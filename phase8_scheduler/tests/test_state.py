"""Module 4 — ``SchedulerState`` + ``StateStore`` persistence and transitions.

No network, no broker, no LLM: pure dataclass + atomic-file checks against ``tmp_path``,
a ``caplog`` probe of the self-heal WARNING, and a tiny duck-typed fake result for
``record_cycle`` (no ``execution`` import — phase isolation). The trade-status set and the
``profit_loss`` handling pin verified Contract E.
"""

from __future__ import annotations

import dataclasses
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from scheduler import SchedulerState as ExportedSchedulerState
from scheduler import StateStore as ExportedStateStore
from scheduler.state import SchedulerState, StateStore

_BERLIN = ZoneInfo("Europe/Berlin")


@dataclasses.dataclass
class _FakeResult:
    """Duck-typed stand-in for a Phase-5 ``ExecutionResult`` (status + profit_loss)."""

    status: str
    profit_loss: float | None = None


def _store(tmp_path) -> StateStore:
    return StateStore(str(tmp_path / "state" / "scheduler_state.json"))


# --- persistence -----------------------------------------------------------


def test_save_then_load_roundtrips_all_fields(tmp_path) -> None:
    """Every field survives a save → load cycle unchanged."""
    store = _store(tmp_path)
    state = SchedulerState(
        date="2026-06-28",
        trades_today=3,
        realized_pnl_today=-41.16,
        last_research_ts="2026-06-28T09:05:00Z",
        last_reconcile_ts="2026-06-28T09:00:00Z",
        last_shadow_pairs_ts="2026-06-28T09:10:00Z",
        consecutive_failures=1,
        kill_reason="auto:backoff",
        last_no_trade_reason="LLM_ABSTAIN",
        last_no_trade_detail="Weak momentum and a wide spread; skipping.",
    )
    store.save(state)
    assert store.load() == state


def test_load_missing_file_returns_fresh_state(tmp_path) -> None:
    """A never-written store loads a fresh, uninitialised state (no crash)."""
    state = _store(tmp_path).load()
    assert state == SchedulerState()
    assert state.date == ""


def test_load_corrupt_json_self_heals_with_one_warning(
    tmp_path, caplog: pytest.LogCaptureFixture
) -> None:
    """Partial/corrupt JSON → a fresh state plus exactly one WARNING (no raise)."""
    store = _store(tmp_path)
    path = tmp_path / "state" / "scheduler_state.json"
    path.write_text('{"date": "2026-06-28", "trades_today":', encoding="utf-8")  # truncated
    with caplog.at_level(logging.WARNING, logger="scheduler.state"):
        state = store.load()
    assert state == SchedulerState()
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "fresh state" in warnings[0].message


def test_load_tolerates_unknown_and_missing_keys(tmp_path) -> None:
    """Forward/backward-compat: unknown keys are dropped, missing keys default."""
    store = _store(tmp_path)
    path = tmp_path / "state" / "scheduler_state.json"
    path.write_text(
        '{"date": "2026-06-28", "trades_today": 2, "future_field": "ignored"}',
        encoding="utf-8",
    )
    state = store.load()
    assert state.date == "2026-06-28"
    assert state.trades_today == 2
    assert state.realized_pnl_today == 0.0  # missing key → default
    assert not hasattr(state, "future_field")


def test_save_is_atomic_creates_parent_and_leaves_no_tmp(tmp_path) -> None:
    """Parent dir is auto-created; no ``.tmp`` lingers after a successful save."""
    nested = tmp_path / "data" / "state" / "scheduler_state.json"
    store = StateStore(str(nested))
    assert nested.parent.is_dir()  # created in __init__
    store.save(SchedulerState(date="2026-06-28"))
    assert nested.exists()
    assert list(nested.parent.glob("*.tmp")) == []


# --- rollover --------------------------------------------------------------


def test_rollover_new_day_resets_day_scoped_keeps_timestamps(tmp_path) -> None:
    """A new Europe/Berlin day zeroes the day counters but keeps last-action ts."""
    store = _store(tmp_path)
    state = SchedulerState(
        date="2026-06-27",
        trades_today=5,
        realized_pnl_today=-200.0,
        consecutive_failures=2,
        kill_reason="auto:backoff",
        last_no_trade_reason="CAP_BLOCK",
        last_no_trade_detail="some prose from yesterday's abstain",
        last_research_ts="2026-06-27T10:00:00Z",
        last_reconcile_ts="2026-06-27T17:30:00Z",
        last_shadow_pairs_ts="2026-06-27T11:00:00Z",
    )
    now = datetime(2026, 6, 28, 9, 5, tzinfo=_BERLIN)
    out = store.rollover_if_new_day(state, now)

    assert out is state  # mutate-and-return
    assert out.date == "2026-06-28"
    assert out.trades_today == 0
    assert out.realized_pnl_today == 0.0
    assert out.consecutive_failures == 0
    assert out.kill_reason is None
    assert out.last_no_trade_reason is None
    assert out.last_no_trade_detail is None
    # cross-day timestamps are preserved
    assert out.last_research_ts == "2026-06-27T10:00:00Z"
    assert out.last_reconcile_ts == "2026-06-27T17:30:00Z"
    assert out.last_shadow_pairs_ts == "2026-06-27T11:00:00Z"


def test_rollover_same_day_is_noop(tmp_path) -> None:
    """Same Europe/Berlin day → nothing changes (counters preserved)."""
    store = _store(tmp_path)
    state = SchedulerState(date="2026-06-28", trades_today=4, realized_pnl_today=-50.0)
    now = datetime(2026, 6, 28, 16, 0, tzinfo=_BERLIN)
    out = store.rollover_if_new_day(state, now)
    assert out.trades_today == 4
    assert out.realized_pnl_today == -50.0
    assert out.date == "2026-06-28"


def test_rollover_is_idempotent_across_two_calls(tmp_path) -> None:
    """Calling rollover twice on the same new day resets once, then no-ops."""
    store = _store(tmp_path)
    state = SchedulerState(date="2026-06-27", trades_today=3)
    now = datetime(2026, 6, 28, 9, 5, tzinfo=_BERLIN)
    store.rollover_if_new_day(state, now)
    state.trades_today = 2  # simulate a trade after the first rollover
    store.rollover_if_new_day(state, now)  # second call, same day
    assert state.date == "2026-06-28"
    assert state.trades_today == 2  # NOT reset again


def test_rollover_initialises_fresh_state(tmp_path) -> None:
    """An uninitialised (``date=""``) state gets stamped with today on first rollover."""
    store = _store(tmp_path)
    state = SchedulerState()
    now = datetime(2026, 6, 28, 9, 5, tzinfo=_BERLIN)
    store.rollover_if_new_day(state, now)
    assert state.date == "2026-06-28"


# --- record_cycle ----------------------------------------------------------


@pytest.mark.parametrize("status", ["OPEN", "CLOSED_BY_BROKER", "TIME_STOP"])
def test_record_cycle_counts_real_trade_statuses(tmp_path, status: str) -> None:
    """Each real-trade status (Contract E) increments ``trades_today`` by one."""
    store = _store(tmp_path)
    state = SchedulerState(date="2026-06-28", trades_today=1)
    store.record_cycle(state, _FakeResult(status=status))
    assert state.trades_today == 2


@pytest.mark.parametrize("status", ["NO_TRADE", "ABORTED_BY_USER", "ABORT"])
def test_record_cycle_ignores_non_trade_statuses(tmp_path, status: str) -> None:
    """Non-trade outcomes never touch the cap counter."""
    store = _store(tmp_path)
    state = SchedulerState(date="2026-06-28", trades_today=1)
    store.record_cycle(state, _FakeResult(status=status))
    assert state.trades_today == 1


def test_record_cycle_accumulates_pnl_when_present(tmp_path) -> None:
    """A TIME_STOP result with P&L folds into the snapshot; None (broker-close) is skipped."""
    store = _store(tmp_path)
    state = SchedulerState(date="2026-06-28")
    store.record_cycle(state, _FakeResult(status="TIME_STOP", profit_loss=-41.16))
    assert state.realized_pnl_today == pytest.approx(-41.16)
    # CLOSED_BY_BROKER carries no P&L at cycle time (Contract E) → snapshot unchanged
    store.record_cycle(state, _FakeResult(status="CLOSED_BY_BROKER", profit_loss=None))
    assert state.realized_pnl_today == pytest.approx(-41.16)
    assert state.trades_today == 2  # both counted as trades


def test_record_cycle_does_not_touch_failures_or_reason(tmp_path) -> None:
    """Single responsibility: backoff + no_trade_reason fields are not record_cycle's."""
    store = _store(tmp_path)
    state = SchedulerState(
        date="2026-06-28", consecutive_failures=2, last_no_trade_reason="CAP_BLOCK"
    )
    store.record_cycle(state, _FakeResult(status="OPEN"))
    assert state.consecutive_failures == 2
    assert state.last_no_trade_reason == "CAP_BLOCK"


# --- exports ---------------------------------------------------------------


def test_exported_from_package_root() -> None:
    """``from scheduler import SchedulerState, StateStore`` are the submodule objects."""
    assert ExportedSchedulerState is SchedulerState
    assert ExportedStateStore is StateStore
