"""Module 8 — ``ResearchTick``: the autonomous candidate generator.

No network, no LLM, no real Phase-4: a ``FakeResearch`` stands in for the real orchestrator,
configurable to return a pick / abstain / raise, exposing a ``FakeStateManager`` ``.state`` that
records ``save_candidates`` so the fail-closed clear can be asserted. The behaviours pinned: the
PASS / abstain / exception classification, the two v1 reason buckets (Reconciliation H), the
fail-closed candidate clear on exception, ``last_research_ts`` always stamped (injected
``now_fn``), and the safety guarantee that a real pick never carries the manual-seed marker.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import pytest

from scheduler import ResearchResult as ExportedResearchResult
from scheduler import ResearchTick as ExportedResearchTick
from scheduler.research_tick import (
    REASON_LLM_ABSTAIN,
    REASON_PREFLIGHT,
    ResearchResult,
    ResearchTick,
)
from scheduler.state import SchedulerState

# The literal marker the operator seed tool writes (phase5_execution/scripts/seed_candidate.py).
# An autonomous Phase-4 pick must NEVER contain it (Step 1.1 / concept §8).
_SEED_MARKER = "MANUAL SEED"


class _FakeStateManager:
    """Stand-in for the Phase-2 ``StateManager`` — records ``save_candidates`` calls."""

    def __init__(self) -> None:
        self.saved: list[list] = []

    def save_candidates(self, candidates: list) -> None:
        self.saved.append(list(candidates))


class _FakeResearch:
    """Duck-typed Phase-4 ``Research``: returns a configured result or raises.

    Args:
        result: the list ``run()`` returns (a pick list or ``[]``).
        raises: if set, ``run()`` raises this exception instead of returning.
        save_raises: if True, ``state.save_candidates`` raises (for the cleanup-also-fails path).
    """

    def __init__(
        self,
        *,
        result: list | None = None,
        raises: Exception | None = None,
        save_raises: bool = False,
    ) -> None:
        self._result = result if result is not None else []
        self._raises = raises
        self.state = _FakeStateManager()
        self.run_calls = 0
        if save_raises:
            def _boom(_c: list) -> None:
                raise RuntimeError("disk full")

            self.state.save_candidates = _boom  # type: ignore[method-assign]

    def run(self) -> list:
        self.run_calls += 1
        if self._raises is not None:
            raise self._raises
        return self._result


def _real_pick() -> dict:
    """A realistic Phase-4 candidate dict (frozen 10-field contract) — NOT a manual seed."""
    return {
        "epic": "IX.D.DAX.IFMM.IP",
        "direction": "SELL",
        "llm_confidence": 68.0,
        "reasoning": "DAX printing lower highs on the 5m with weak breadth; favour shorts.",
        "spread_pct_at_pick": 0.03,
        "drift_at_pick": -0.2,
        "score_at_pick": 50.0,
        "threshold_applied": 55.0,
        "generated_at": "2026-06-28T09:05:00.000Z",
        "source": "research",
    }


def _fixed_now():
    """An injectable tz-aware ``now_fn`` returning a fixed instant."""
    return lambda: datetime(2026, 6, 28, 9, 5, tzinfo=timezone.utc)


def _state() -> SchedulerState:
    return SchedulerState(date="2026-06-28")


# --- PASS ------------------------------------------------------------------


def test_pass_writes_pick_and_clears_reason() -> None:
    """A real pick → picked=True, n=1, reason cleared, run() called once, ts stamped."""
    research = _FakeResearch(result=[_real_pick()])
    tick = ResearchTick(research, now_fn=_fixed_now())
    state = _state()
    state.last_no_trade_reason = "STALE"  # a prior cycle's reason must be cleared on PASS

    result = tick.ensure_candidates(state)

    assert result == ResearchResult(picked=True, n=1, reason=None)
    assert state.last_no_trade_reason is None
    assert state.last_research_ts == "2026-06-28T09:05:00+00:00"
    assert research.run_calls == 1


# --- abstain ---------------------------------------------------------------


def test_abstain_sets_llm_abstain_reason() -> None:
    """An empty list → picked=False, reason=LLM_ABSTAIN (the v1 umbrella, Reconciliation H)."""
    research = _FakeResearch(result=[])
    tick = ResearchTick(research, now_fn=_fixed_now())
    state = _state()

    result = tick.ensure_candidates(state)

    assert result == ResearchResult(picked=False, n=0, reason=REASON_LLM_ABSTAIN)
    assert state.last_no_trade_reason == REASON_LLM_ABSTAIN
    assert research.run_calls == 1


# --- exception (fail-closed) ----------------------------------------------


def test_exception_fails_closed_with_preflight_reason(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """run() raising → reason=PREFLIGHT_FAIL, one critical, candidate file cleared, no re-raise."""
    research = _FakeResearch(raises=RuntimeError("broker down"))
    tick = ResearchTick(research, now_fn=_fixed_now())
    state = _state()

    with caplog.at_level(logging.CRITICAL, logger="scheduler.research_tick"):
        result = tick.ensure_candidates(state)  # must NOT raise

    assert result == ResearchResult(picked=False, n=0, reason=REASON_PREFLIGHT)
    assert state.last_no_trade_reason == REASON_PREFLIGHT
    # fail-closed clear: a fresh empty list was written so nothing stale is tradeable
    assert research.state.saved == [[]]
    crit = [r for r in caplog.records if r.levelno == logging.CRITICAL]
    assert len(crit) == 1
    # ts is still stamped even though research failed
    assert state.last_research_ts == "2026-06-28T09:05:00+00:00"


def test_exception_cleanup_failure_is_swallowed(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """If the fail-closed clear ALSO raises, it is logged and swallowed (never raises out)."""
    research = _FakeResearch(raises=RuntimeError("broker down"), save_raises=True)
    tick = ResearchTick(research, now_fn=_fixed_now())
    state = _state()

    with caplog.at_level(logging.CRITICAL, logger="scheduler.research_tick"):
        result = tick.ensure_candidates(state)  # still must not raise

    assert result.reason == REASON_PREFLIGHT
    # two criticals: the research failure + the cleanup failure
    crit = [r for r in caplog.records if r.levelno == logging.CRITICAL]
    assert len(crit) == 2


# --- the safety guarantee --------------------------------------------------


def test_no_manual_seed_marker() -> None:
    """A real (autonomous) pick never carries the seed_candidate.py manual marker.

    This is the structural guarantee that autonomous candidates are tradeable rather than
    judge-forced ABSTAINs (Step 1.1 / concept §8): the marker only comes from the operator
    seed tool, never from ``Research.run()``.
    """
    pick = _real_pick()
    research = _FakeResearch(result=[pick])
    tick = ResearchTick(research, now_fn=_fixed_now())
    state = _state()

    result = tick.ensure_candidates(state)

    assert result.picked is True
    # the candidate surfaced on PASS carries no manual-seed marker anywhere in its reasoning
    assert _SEED_MARKER not in pick["reasoning"]
    assert all(_SEED_MARKER not in str(v) for v in pick.values())


# --- timestamp on every outcome -------------------------------------------


@pytest.mark.parametrize(
    "research",
    [
        _FakeResearch(result=[_real_pick()]),
        _FakeResearch(result=[]),
        _FakeResearch(raises=RuntimeError("x")),
    ],
    ids=["pass", "abstain", "exception"],
)
def test_last_research_ts_stamped_on_every_outcome(research: _FakeResearch) -> None:
    """``last_research_ts`` is set on PASS, abstain, and exception alike (the attempt happened)."""
    tick = ResearchTick(research, now_fn=_fixed_now())
    state = _state()
    assert state.last_research_ts is None

    tick.ensure_candidates(state)

    assert state.last_research_ts == "2026-06-28T09:05:00+00:00"


def test_default_now_fn_is_tz_aware() -> None:
    """Without an injected ``now_fn`` the timestamp is still produced (tz-aware UTC default)."""
    tick = ResearchTick(_FakeResearch(result=[]))
    state = _state()
    tick.ensure_candidates(state)
    assert state.last_research_ts is not None
    # parseable ISO with an offset (tz-aware), not a naive stamp
    parsed = datetime.fromisoformat(state.last_research_ts)
    assert parsed.tzinfo is not None


# --- plumbing --------------------------------------------------------------


def test_exported_from_package_root() -> None:
    """``from scheduler import ResearchTick, ResearchResult`` are the submodule objects."""
    assert ExportedResearchTick is ResearchTick
    assert ExportedResearchResult is ResearchResult
