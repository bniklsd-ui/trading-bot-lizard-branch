"""Module 6 — ``AutoConfirm``: the five hard gates of the demo-only auto-confirm.

No network, no broker, no LLM: a real :class:`~scheduler.state.StateStore` over ``tmp_path``,
a real file kill-switch, and tiny fakes for the budget (duck-typed :class:`Budget`) and the
DB-backed realized-P&L reader. The critical behaviours are pinned: the structural demo-lock
(config, not the order — Contract D), the loss-breaker reading the injected DB P&L (Contract
E) rather than the lagging state snapshot, fail-closed on a P&L read error, and that
``can_open`` and ``__call__`` route through one evaluator so they never disagree (Contract A:
``__call__`` reads state live from the store).
"""

from __future__ import annotations

import logging

import pytest

from scheduler import AutoConfirm as ExportedAutoConfirm
from scheduler.config import SchedulerConfig
from scheduler.safety import (
    REASON_BUDGET,
    REASON_CAP,
    REASON_KILL,
    REASON_LOSS,
    REASON_NOT_DEMO,
    AutoConfirm,
)
from scheduler.state import SchedulerState, StateStore


class _FakeBudget:
    """Duck-typed :class:`Budget` — a fixed ``is_exhausted`` verdict."""

    def __init__(self, exhausted: bool = False) -> None:
        self._exhausted = exhausted

    def is_exhausted(self) -> bool:
        return self._exhausted


def _make(
    tmp_path,
    *,
    account: str = "demo",
    max_trades: int = 5,
    loss_cap: float | None = 1800.0,
    budget_exhausted: bool = False,
    pnl_today: float = 0.0,
    pnl_raises: bool = False,
    kill: bool = False,
):
    """Build an ``AutoConfirm`` plus its store over ``tmp_path``; returns (gate, store).

    The realized-P&L reader is a closure returning ``pnl_today`` (or raising). The kill path
    is created on disk when ``kill`` is set so ``killswitch.is_set`` reads ``True``.
    """
    config = SchedulerConfig(
        account=account,
        max_trades_per_day=max_trades,
        daily_loss_cap=loss_cap,
        state_path=str(tmp_path / "state" / "scheduler_state.json"),
        kill_path=str(tmp_path / "state" / "KILL"),
    )
    store = StateStore(config.state_path)

    def _pnl(_session_date: str) -> float:
        if pnl_raises:
            raise RuntimeError("db unreachable")
        return pnl_today

    if kill:
        from scheduler import killswitch

        killswitch.set_kill(config.kill_path, "manual:test")

    gate = AutoConfirm(config, store, config.kill_path, _FakeBudget(budget_exhausted), _pnl)
    return gate, store


def _state(**kw) -> SchedulerState:
    """A today-stamped state (rolled-over) so ``state.date`` is a real session date."""
    base = {"date": "2026-06-28", "trades_today": 0}
    base.update(kw)
    return SchedulerState(**base)


# --- happy path ------------------------------------------------------------


def test_all_conditions_ok_confirms(tmp_path) -> None:
    """Demo + kill off + under cap + above breaker + budget ok → confirm."""
    gate, store = _make(tmp_path)
    state = _state()
    assert gate.can_open(state) == (True, None)
    store.save(state)
    assert gate(object()) is True  # __call__ loads the same state from the store


# --- gate 1: demo-lock -----------------------------------------------------


def test_live_account_refused_with_critical(
    tmp_path, caplog: pytest.LogCaptureFixture
) -> None:
    """A non-demo account is refused (config, not order — Contract D) + logs critical."""
    gate, _ = _make(tmp_path, account="live")
    with caplog.at_level(logging.CRITICAL, logger="scheduler.safety"):
        ok, reason = gate.can_open(_state())
    assert (ok, reason) == (False, REASON_NOT_DEMO)
    crit = [r for r in caplog.records if r.levelno == logging.CRITICAL]
    assert len(crit) == 1
    assert "demo-only" in crit[0].message


def test_demo_lock_beats_other_failures(tmp_path) -> None:
    """Demo-lock is checked first: a live account reports NOT_DEMO even if also over cap."""
    gate, _ = _make(tmp_path, account="live", max_trades=1)
    ok, reason = gate.can_open(_state(trades_today=5))
    assert (ok, reason) == (False, REASON_NOT_DEMO)


# --- gate 2: kill-switch ---------------------------------------------------


def test_kill_switch_blocks(tmp_path) -> None:
    """A present KILL file blocks with REASON_KILL."""
    gate, _ = _make(tmp_path, kill=True)
    assert gate.can_open(_state()) == (False, REASON_KILL)


def test_call_reads_kill_switch_live(tmp_path) -> None:
    """__call__ re-reads the kill file each time (Contract A: no stale snapshot)."""
    gate, store = _make(tmp_path)
    store.save(_state())
    assert gate(object()) is True
    from scheduler import killswitch

    killswitch.set_kill(str(tmp_path / "state" / "KILL"), "manual:mid-run")
    assert gate(object()) is False  # picked up live, no rebuild


# --- gate 3: trade cap -----------------------------------------------------


def test_trade_cap_blocks_at_limit(tmp_path) -> None:
    """trades_today == cap blocks (the cap is exclusive: ``< max_trades_per_day``)."""
    gate, _ = _make(tmp_path, max_trades=5)
    assert gate.can_open(_state(trades_today=5)) == (False, REASON_CAP)


def test_under_trade_cap_passes(tmp_path) -> None:
    """One below the cap still confirms."""
    gate, _ = _make(tmp_path, max_trades=5)
    assert gate.can_open(_state(trades_today=4)) == (True, None)


# --- gate 4: daily-loss breaker (from the DB, Contract E) ------------------


def test_loss_breaker_blocks_when_pnl_below_cap(tmp_path) -> None:
    """Realized P&L worse than -cap blocks with REASON_LOSS (read from the injected DB)."""
    gate, _ = _make(tmp_path, loss_cap=1800.0, pnl_today=-1850.0)
    assert gate.can_open(_state()) == (False, REASON_LOSS)


def test_loss_breaker_blocks_exactly_at_cap(tmp_path) -> None:
    """Boundary: P&L == -cap blocks (condition is ``pnl > -cap``)."""
    gate, _ = _make(tmp_path, loss_cap=1800.0, pnl_today=-1800.0)
    assert gate.can_open(_state()) == (False, REASON_LOSS)


def test_loss_breaker_allows_just_within_cap(tmp_path) -> None:
    """Boundary: P&L just better than -cap is allowed."""
    gate, _ = _make(tmp_path, loss_cap=1800.0, pnl_today=-1799.99)
    assert gate.can_open(_state()) == (True, None)


def test_loss_breaker_uses_state_date_as_session(tmp_path) -> None:
    """The breaker queries the P&L reader with ``state.date`` (the session date)."""
    seen: list[str] = []

    config = SchedulerConfig(
        daily_loss_cap=1800.0,
        state_path=str(tmp_path / "s.json"),
        kill_path=str(tmp_path / "KILL"),
    )
    store = StateStore(config.state_path)

    def _pnl(session_date: str) -> float:
        seen.append(session_date)
        return 0.0

    gate = AutoConfirm(config, store, config.kill_path, _FakeBudget(), _pnl)
    gate.can_open(_state(date="2026-07-01"))
    assert seen == ["2026-07-01"]


def test_loss_breaker_read_error_fails_closed(
    tmp_path, caplog: pytest.LogCaptureFixture
) -> None:
    """A raising P&L read blocks fail-closed (cannot verify the cap) + logs critical."""
    gate, _ = _make(tmp_path, loss_cap=1800.0, pnl_raises=True)
    with caplog.at_level(logging.CRITICAL, logger="scheduler.safety"):
        ok, reason = gate.can_open(_state())
    assert (ok, reason) == (False, REASON_LOSS)
    assert any(r.levelno == logging.CRITICAL for r in caplog.records)


def test_loss_cap_none_warns_once_and_does_not_block(
    tmp_path, caplog: pytest.LogCaptureFixture
) -> None:
    """``daily_loss_cap=None`` → one construction WARNING, breaker disabled (no block).

    ``config.py`` also warns about the *value* being None (a separate responsibility); here
    we assert ``safety.py`` owns exactly one warning about *its gate* being disabled.
    """
    with caplog.at_level(logging.WARNING, logger="scheduler.safety"):
        gate, _ = _make(tmp_path, loss_cap=None, pnl_today=-9_999_999.0)
    warnings = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING and r.name == "scheduler.safety"
    ]
    assert len(warnings) == 1
    assert "DISABLED" in warnings[0].message
    # even a catastrophic P&L does not block when the breaker is off
    assert gate.can_open(_state()) == (True, None)


def test_loss_cap_none_never_calls_pnl_reader(tmp_path) -> None:
    """With the breaker off the P&L reader is never invoked (short-circuit)."""
    called = False

    config = SchedulerConfig(
        daily_loss_cap=None,
        state_path=str(tmp_path / "s.json"),
        kill_path=str(tmp_path / "KILL"),
    )
    store = StateStore(config.state_path)

    def _pnl(_session_date: str) -> float:
        nonlocal called
        called = True
        return 0.0

    gate = AutoConfirm(config, store, config.kill_path, _FakeBudget(), _pnl)
    gate.can_open(_state())
    assert called is False


# --- gate 5: budget --------------------------------------------------------


def test_budget_exhausted_blocks(tmp_path) -> None:
    """An exhausted token budget blocks with REASON_BUDGET."""
    gate, _ = _make(tmp_path, budget_exhausted=True)
    assert gate.can_open(_state()) == (False, REASON_BUDGET)


# --- consistency + plumbing ------------------------------------------------


def test_can_open_and_call_agree(tmp_path) -> None:
    """For the same stored state, ``can_open`` and ``__call__`` give the same verdict."""
    # blocked-by-cap case
    gate, store = _make(tmp_path, max_trades=2)
    state = _state(trades_today=2)
    store.save(state)
    ok, _ = gate.can_open(state)
    assert ok is False
    assert gate(object()) is False

    # passing case (fresh store, under cap)
    gate2, store2 = _make(tmp_path, max_trades=5)
    passing = _state(trades_today=1)
    store2.save(passing)
    assert gate2.can_open(passing)[0] is True
    assert gate2(object()) is True


def test_call_ignores_order_plan_fields(tmp_path) -> None:
    """``__call__`` reads nothing off the plan (Contract D: OrderPlan has no account)."""
    gate, store = _make(tmp_path)
    store.save(_state())

    class _Plan:
        account = "live"  # must be ignored — the demo-lock is config-only

    assert gate(_Plan()) is True


def test_exported_from_package_root() -> None:
    """``from scheduler import AutoConfirm`` is the submodule class."""
    assert ExportedAutoConfirm is AutoConfirm
