"""Tests for Module 5 — ``debate/budget.py`` (hard caps + cumulative metering).

The budget is the **cost-discipline structure** of the phase (Decision E/J): every
cap breach raises :class:`DebateBudgetExceeded`, which the orchestrator (Module 6)
converts to a fail-closed ABSTAIN — a breach never trades "regardless".

All tests are pure: time is **injected** via ``now_fn`` (a scripted fake clock),
so the wall-clock cap is deterministic with **no real sleeping**, and ``register``
takes the same usage dict ``ask_agent`` returns (the ``token_meter`` record shape).
"""

from __future__ import annotations

import pytest

from debate.budget import DebateBudget
from debate.models import DebateBudgetExceeded, DebateConfig


class _FakeClock:
    """A scripted monotonic clock: returns successive values from a list.

    The last value is held once the script is exhausted, so a budget that calls
    ``now_fn`` more often than scripted does not crash (it just sees "no further
    time passed"). Used to make the wall-clock cap deterministic.
    """

    def __init__(self, *values: float) -> None:
        self._values = list(values) or [0.0]
        self._i = 0

    def __call__(self) -> float:
        value = self._values[min(self._i, len(self._values) - 1)]
        self._i += 1
        return value


def _usage(
    input_tokens: int = 0,
    output_tokens: int = 0,
    *,
    cache_read: int = 0,
    cache_write: int = 0,
    usd: float = 0.0,
    eur: float = 0.0,
) -> dict:
    """A ``token_meter``-shaped usage record (the ``ask_agent`` return dict)."""
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_input_tokens": cache_read,
        "cache_creation_input_tokens": cache_write,
        "est_cost_usd": usd,
        "est_cost_eur": eur,
    }


# --------------------------------------------------------------------------- #
# Under caps → never raises                                                    #
# --------------------------------------------------------------------------- #


def test_under_all_caps_no_raise() -> None:
    cfg = DebateConfig()  # 18 calls / 120k in / 12k out / 120s
    clock = _FakeClock(0.0, 1.0, 2.0, 3.0)
    budget = DebateBudget(cfg, now_fn=clock)
    for _ in range(3):
        budget.register(_usage(1_000, 100))
        budget.check()  # well under every cap → no raise


def test_check_before_any_turn_no_raise() -> None:
    budget = DebateBudget(DebateConfig(), now_fn=_FakeClock(0.0, 0.0))
    budget.check()  # zero usage, no time passed


# --------------------------------------------------------------------------- #
# Each cap fires individually                                                  #
# --------------------------------------------------------------------------- #


def test_calls_cap_breach() -> None:
    cfg = DebateConfig(max_total_calls=2)
    budget = DebateBudget(cfg, now_fn=_FakeClock(0.0))
    budget.register(_usage(1, 1))
    budget.register(_usage(1, 1))
    budget.check()  # exactly at cap → ok
    budget.register(_usage(1, 1))  # 3rd call → over cap
    with pytest.raises(DebateBudgetExceeded):
        budget.check()


def test_input_tokens_cap_breach() -> None:
    cfg = DebateConfig(max_cumulative_input_tokens=1_000)
    budget = DebateBudget(cfg, now_fn=_FakeClock(0.0))
    budget.register(_usage(1_001, 0))
    with pytest.raises(DebateBudgetExceeded):
        budget.check()


def test_output_tokens_cap_breach() -> None:
    cfg = DebateConfig(max_cumulative_output_tokens=500)
    budget = DebateBudget(cfg, now_fn=_FakeClock(0.0))
    budget.register(_usage(0, 501))
    with pytest.raises(DebateBudgetExceeded):
        budget.check()


def test_wall_clock_cap_breach_deterministic() -> None:
    cfg = DebateConfig(wall_clock_timeout_s=10.0)
    # start at t=0, then check sees t=11 → elapsed 11 > 10 → breach (no sleeping)
    budget = DebateBudget(cfg, now_fn=_FakeClock(0.0, 11.0))
    budget.register(_usage(1, 1))
    with pytest.raises(DebateBudgetExceeded):
        budget.check()


def test_wall_clock_exactly_at_cap_no_raise() -> None:
    cfg = DebateConfig(wall_clock_timeout_s=10.0)
    budget = DebateBudget(cfg, now_fn=_FakeClock(0.0, 10.0))  # elapsed == cap
    budget.register(_usage(1, 1))
    budget.check()  # boundary: at cap is allowed, only > cap breaches


# --------------------------------------------------------------------------- #
# Cumulative aggregation / summary                                             #
# --------------------------------------------------------------------------- #


def test_summary_aggregates_tokens_cache_and_cost() -> None:
    budget = DebateBudget(DebateConfig(), now_fn=_FakeClock(0.0))
    budget.register(_usage(100, 10, cache_read=40, cache_write=5, usd=0.01, eur=0.0092))
    budget.register(_usage(200, 20, cache_read=60, cache_write=0, usd=0.02, eur=0.0184))
    summary = budget.summary()
    assert summary["input_tokens"] == 300
    assert summary["output_tokens"] == 30
    assert summary["cache_read_input_tokens"] == 100
    assert summary["cache_creation_input_tokens"] == 5
    assert round(summary["est_cost_usd"], 6) == 0.03
    assert round(summary["est_cost_eur"], 6) == 0.0276
    assert summary["total_calls"] == 2


def test_summary_keys_match_audit_token_summary_schema() -> None:
    # The summary IS DebateOutcome.token_summary → the audit (Module 7, concept §7)
    # ingests it without reshaping. Pin the forward-compatible key set.
    summary = DebateBudget(DebateConfig(), now_fn=_FakeClock(0.0)).summary()
    for key in (
        "input_tokens",
        "output_tokens",
        "cache_read_input_tokens",
        "cache_creation_input_tokens",
        "est_cost_usd",
        "est_cost_eur",
    ):
        assert key in summary


def test_register_tolerates_empty_usage() -> None:
    # ask_agent returns {} when the client captured no usage record → must not crash.
    budget = DebateBudget(DebateConfig(), now_fn=_FakeClock(0.0))
    budget.register({})
    budget.check()
    summary = budget.summary()
    assert summary["total_calls"] == 1
    assert summary["input_tokens"] == 0
    assert summary["est_cost_usd"] == 0.0
