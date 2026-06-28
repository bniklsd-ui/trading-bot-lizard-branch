"""Module 9 (concept §6) — ``BackoffTracker``: consecutive-failure tracking + backoff schedule.

No network, no broker, no LLM, no real sleep: pure arithmetic over a config + a state counter.
The behaviours pinned: failure/success counter transitions (mutate-and-return), the trip
threshold (boundary-inclusive), the exponential ``delay_s`` schedule + its cap, the ``n<=0``
guard, and that only ``consecutive_failures`` is touched (other state fields are off-limits).
"""

from __future__ import annotations

from scheduler import BackoffTracker as ExportedBackoffTracker
from scheduler.backoff import BackoffTracker
from scheduler.config import SchedulerConfig
from scheduler.state import SchedulerState


def _config(**kw) -> SchedulerConfig:
    """A config with the loss-cap set (silences the unrelated config WARNING) + overrides."""
    base = {"daily_loss_cap": 1800.0, "max_consecutive_failures": 3}
    base.update(kw)
    return SchedulerConfig(**base)


# --- counter transitions ---------------------------------------------------


def test_record_failure_increments_same_object() -> None:
    """record_failure bumps consecutive_failures by one and returns the same object."""
    tracker = BackoffTracker(_config())
    state = SchedulerState(consecutive_failures=0)
    returned = tracker.record_failure(state)
    assert returned is state
    assert state.consecutive_failures == 1
    tracker.record_failure(state)
    assert state.consecutive_failures == 2


def test_record_success_resets() -> None:
    """record_success zeroes the counter (and returns the same object)."""
    tracker = BackoffTracker(_config())
    state = SchedulerState(consecutive_failures=4)
    returned = tracker.record_success(state)
    assert returned is state
    assert state.consecutive_failures == 0


# --- should_trip -----------------------------------------------------------


def test_should_trip_false_below_threshold() -> None:
    """Two failures with max=3 → not yet tripping."""
    tracker = BackoffTracker(_config(max_consecutive_failures=3))
    assert tracker.should_trip(SchedulerState(consecutive_failures=2)) is False


def test_should_trip_true_at_threshold() -> None:
    """Boundary: consecutive_failures == max trips (condition is ``>=``)."""
    tracker = BackoffTracker(_config(max_consecutive_failures=3))
    assert tracker.should_trip(SchedulerState(consecutive_failures=3)) is True
    assert tracker.should_trip(SchedulerState(consecutive_failures=4)) is True


# --- delay_s ---------------------------------------------------------------


def test_delay_grows_exponentially() -> None:
    """n=1→base, n=2→2·base, n=3→4·base (cap high enough not to clip)."""
    tracker = BackoffTracker(_config(backoff_base_s=30.0, backoff_cap_s=10_000.0))
    assert tracker.delay_s(SchedulerState(consecutive_failures=1)) == 30.0
    assert tracker.delay_s(SchedulerState(consecutive_failures=2)) == 60.0
    assert tracker.delay_s(SchedulerState(consecutive_failures=3)) == 120.0


def test_delay_respects_cap() -> None:
    """A small cap clamps a large streak's delay."""
    tracker = BackoffTracker(_config(backoff_base_s=30.0, backoff_cap_s=100.0))
    # n=10 would be 30·2^9 = 15360 without the cap
    assert tracker.delay_s(SchedulerState(consecutive_failures=10)) == 100.0


def test_delay_zero_when_no_failures_then_base_after_one() -> None:
    """n<=0 → 0.0 (defensive); after one failure the delay is base again (post-reset path)."""
    tracker = BackoffTracker(_config(backoff_base_s=30.0, backoff_cap_s=600.0))
    state = SchedulerState(consecutive_failures=0)
    assert tracker.delay_s(state) == 0.0
    tracker.record_failure(state)
    assert tracker.delay_s(state) == 30.0


# --- field isolation -------------------------------------------------------


def test_only_consecutive_failures_is_touched() -> None:
    """record_failure / record_success leave every other state field untouched."""
    tracker = BackoffTracker(_config())
    state = SchedulerState(
        date="2026-06-28",
        trades_today=2,
        realized_pnl_today=-50.0,
        last_research_ts="2026-06-28T09:05:00+00:00",
        last_reconcile_ts="2026-06-28T09:00:00+00:00",
        kill_reason="manual:test",
        last_no_trade_reason="LLM_ABSTAIN",
        consecutive_failures=1,
    )
    tracker.record_failure(state)
    tracker.record_success(state)
    assert state.date == "2026-06-28"
    assert state.trades_today == 2
    assert state.realized_pnl_today == -50.0
    assert state.last_research_ts == "2026-06-28T09:05:00+00:00"
    assert state.last_reconcile_ts == "2026-06-28T09:00:00+00:00"
    assert state.kill_reason == "manual:test"
    assert state.last_no_trade_reason == "LLM_ABSTAIN"
    assert state.consecutive_failures == 0  # the only field that changed


# --- plumbing --------------------------------------------------------------


def test_exported_from_package_root() -> None:
    """``from scheduler import BackoffTracker`` is the submodule class."""
    assert ExportedBackoffTracker is BackoffTracker
