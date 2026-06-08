"""Tests for the ``Research`` orchestrator — the full ``run()`` cycle (Step 7).

All mocked, no network, no real LLM: the broker / DB / fetcher / state / LLM are
the ``conftest`` fakes. Concept §7 mandates ≥5 cases; this file covers the full
PASS flow, a valid abstain, a validator REJECT (hallucinated epic), an LLM error,
a session-health fail (no AI call), an empty universe (no AI call), and the soft
drift-coherence warn that must still PASS.

The invariant under test across every branch: **exactly one**
``save_candidates`` call per cycle — the single pick on PASS, ``[]`` otherwise —
and the LLM is asked **only** after the session-health + non-empty-universe gates.
"""

from __future__ import annotations

from typing import Any

import pytest

from research.models import Candidate, LLMResponseError, ResearchConfig
from research.research import Research
from tests.conftest import (
    DEFAULT_EPIC,
    FakeBroker,
    FakeDB,
    FakeFetcher,
    FakeLLM,
    FakeState,
    _make_prompt_dict,
)


def _config(**over: Any) -> ResearchConfig:
    """A config with the default single-epic allow-list unless overridden."""
    return ResearchConfig(**over)


def _research(
    *,
    broker: FakeBroker | None = None,
    db: FakeDB | None = None,
    state: FakeState | None = None,
    fetcher: FakeFetcher | None = None,
    llm: FakeLLM | None = None,
    config: ResearchConfig | None = None,
) -> tuple[Research, FakeState, FakeLLM, FakeBroker]:
    """Build a ``Research`` over fakes, returning the handles a test asserts on."""
    broker = broker if broker is not None else FakeBroker()
    db = db if db is not None else FakeDB(score=55.0)
    state = state if state is not None else FakeState()
    fetcher = (
        fetcher
        if fetcher is not None
        else FakeFetcher(prompt_dict=_make_prompt_dict())
    )
    llm = llm if llm is not None else FakeLLM()
    config = config if config is not None else _config()
    research = Research(broker, db, state, fetcher, llm, config)
    return research, state, llm, broker


def _buy_raw(confidence: float = 72.0) -> dict[str, Any]:
    """A well-formed, in-universe BUY pick."""
    return {
        "abstain": False,
        "epic": DEFAULT_EPIC,
        "direction": "BUY",
        "confidence": confidence,
        "reasoning": "Drift positive, spread tight, score neutral.",
    }


# --------------------------------------------------------------------------- #
# 1. Full PASS flow                                                            #
# --------------------------------------------------------------------------- #


def test_run_pass_saves_single_candidate() -> None:
    """Healthy broker + clean BUY pick → one candidate saved + returned."""
    llm = FakeLLM(raw=_buy_raw())
    research, state, llm, _ = _research(llm=llm)

    result = research.run()

    assert len(result) == 1
    candidate = result[0]
    assert isinstance(candidate, Candidate)
    assert candidate.epic == DEFAULT_EPIC
    assert candidate.direction == "BUY"
    assert candidate.source == "research"
    # spread_pct_at_pick is the FRESH live recheck value (FakeBroker default 0.03).
    assert candidate.spread_pct_at_pick == pytest.approx(0.03)
    # drift_at_pick is the Phase-3 drift passthrough (prompt_dict default 0.42).
    assert candidate.drift_at_pick == pytest.approx(0.42)
    assert candidate.score_at_pick == 55.0
    assert candidate.threshold_applied == 55.0  # score 55 ≥ neutral → default floor
    # Exactly one save, carrying exactly the candidate dict.
    assert state.saved == [[candidate.to_dict()]]
    # The AI was asked exactly once.
    assert len(llm.calls) == 1


# --------------------------------------------------------------------------- #
# 2. Valid abstain                                                            #
# --------------------------------------------------------------------------- #


def test_run_abstain_saves_empty_but_asks_llm() -> None:
    """A valid ``{"abstain": true}`` → empty save, but the LLM *was* called."""
    llm = FakeLLM(raw={"abstain": True, "reasoning": "No clean setup."})
    research, state, llm, _ = _research(llm=llm)

    result = research.run()

    assert result == []
    assert state.saved == [[]]
    assert len(llm.calls) == 1  # abstain is a content answer — LLM was asked


# --------------------------------------------------------------------------- #
# 3. Validator REJECT (hallucinated epic)                                     #
# --------------------------------------------------------------------------- #


def test_run_validator_reject_hallucinated_epic_saves_empty() -> None:
    """A pick for an epic outside the universe is rejected → empty save."""
    llm = FakeLLM(
        raw={
            "abstain": False,
            "epic": "IX.D.FTSE.IFMM.IP",  # not in the allow-list universe
            "direction": "BUY",
            "confidence": 90.0,
            "reasoning": "Hallucinated instrument.",
        }
    )
    research, state, llm, _ = _research(llm=llm)

    result = research.run()

    assert result == []
    assert state.saved == [[]]
    assert len(llm.calls) == 1


# --------------------------------------------------------------------------- #
# 4. LLM error                                                                #
# --------------------------------------------------------------------------- #


def test_run_llm_error_saves_empty() -> None:
    """An unrecoverable ``LLMResponseError`` → empty save (no fabricated pick)."""
    llm = FakeLLM(raises=LLMResponseError("boom after retry"))
    research, state, llm, _ = _research(llm=llm)

    result = research.run()

    assert result == []
    assert state.saved == [[]]
    assert len(llm.calls) == 1  # it was attempted, then it raised


# --------------------------------------------------------------------------- #
# 5. Session-health fail → no AI call                                          #
# --------------------------------------------------------------------------- #


def test_run_session_health_fail_skips_llm() -> None:
    """A failed account read aborts before any LLM call → empty save."""
    broker = FakeBroker(account_ok=False)
    research, state, llm, broker = _research(broker=broker)

    result = research.run()

    assert result == []
    assert state.saved == [[]]
    assert llm.calls == []  # ★ the AI is never asked on a pre-flight abort
    assert broker.account_calls == 1


def test_run_connect_failure_skips_llm() -> None:
    """Not connected + a failing reconnect aborts → empty save, no LLM call."""
    broker = FakeBroker(connected=False, connect_ok=False)
    research, state, llm, broker = _research(broker=broker)

    result = research.run()

    assert result == []
    assert state.saved == [[]]
    assert llm.calls == []
    assert broker.connect_calls == 1


# --------------------------------------------------------------------------- #
# 6. Empty universe → no AI call                                              #
# --------------------------------------------------------------------------- #


def test_run_empty_universe_skips_llm() -> None:
    """A non-TRADEABLE probe empties the universe → abstain, no LLM call.

    The anchor pre-flight uses the *price* leg (TRADEABLE here), so we fail the
    *universe* leg via the market-info probe so pre-flight passes but the universe
    is empty (drives the empty-universe branch, not the pre-flight one).
    """
    # Pre-flight anchor price is TRADEABLE, but the EUR/info check drops the epic.
    broker = FakeBroker(currency="USD")
    research, state, llm, _ = _research(broker=broker)

    result = research.run()

    assert result == []
    assert state.saved == [[]]
    assert llm.calls == []  # empty universe → never reach the AI step


# --------------------------------------------------------------------------- #
# 7. Soft drift-coherence warn still PASSES                                    #
# --------------------------------------------------------------------------- #


def test_run_drift_coherence_warn_still_passes() -> None:
    """SELL against a strongly positive (delayed) drift → warn, but still saved.

    Confirms ``apply_filter``'s ``ok=True``-with-``rule`` soft warn is treated as
    a pass by the orchestrator, not a reject (Phase-3 drift is ~15 min delayed).
    """
    fetcher = FakeFetcher(prompt_dict=_make_prompt_dict(drift_pct=2.0))
    llm = FakeLLM(
        raw={
            "abstain": False,
            "epic": DEFAULT_EPIC,
            "direction": "SELL",  # opposes the +2.0% drift → soft warn
            "confidence": 72.0,
            "reasoning": "Fade the extended move.",
        }
    )
    research, state, llm, _ = _research(fetcher=fetcher, llm=llm)

    result = research.run()

    assert len(result) == 1
    assert result[0].direction == "SELL"
    assert result[0].drift_at_pick == pytest.approx(2.0)
    assert state.saved == [[result[0].to_dict()]]
