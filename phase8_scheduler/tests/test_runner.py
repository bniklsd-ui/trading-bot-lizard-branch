"""Module 10 (concept §10) — ``SchedulerRunner``: the loop / daemon orchestrator.

Fully deterministic: time and sleep come from a **real** :class:`~scheduler.clock.Clock` driven by
a stepping ``now_fn`` (one fixed instant per loop iteration — the runner calls ``clock.now()`` once
per iteration because every collaborator here is a fake that does not call it) and a recording
no-op ``sleep_fn``; the loop is bounded by ``max_iterations``. No network, no real sleep, no LLM.

The behaviours pinned: per-phase work (PRE_OPEN / WINDOW / POST_WINDOW / IDLE), Contract A (a
**bare** ``executor.run()``), the pre-cycle cap gate, kill-switch stop + shutdown, the backoff trip
(real :class:`~scheduler.backoff.BackoffTracker`), transient-failure recovery, the fail-closed
``preflight``, the reconcile throttle, and the package export.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from scheduler import SchedulerRunner as ExportedSchedulerRunner
from scheduler import killswitch
from scheduler.backoff import BackoffTracker
from scheduler.clock import Clock, Phase
from scheduler.config import SchedulerConfig
from scheduler.exceptions import PreflightError
from scheduler.runner import SchedulerRunner
from scheduler.safety import AutoConfirm
from scheduler.state import SchedulerState, StateStore

BERLIN = ZoneInfo("Europe/Berlin")


def _dt(year: int, month: int, day: int, hour: int, minute: int) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=BERLIN)


# Fixture instants (verified by ``test_fixture_times_classify_as_expected`` below):
#   2026-06-29 is a Monday (trading day), 2026-06-27 a Saturday (weekend).
_EARLY_T = _dt(2026, 6, 29, 7, 0)        # trading day, before the warm-up → IDLE
_PRE_OPEN_T = _dt(2026, 6, 29, 8, 55)    # inside the 08:50–09:00 warm-up
_WINDOW_T = _dt(2026, 6, 29, 10, 0)      # inside 09:00–17:30
_POST_WINDOW_T = _dt(2026, 6, 29, 18, 0)  # after close
_WEEKEND_T = _dt(2026, 6, 27, 12, 0)     # Saturday → IDLE


# --- fakes -----------------------------------------------------------------


class _SteppingNow:
    """A ``now_fn`` returning ``times[i]`` on the i-th call, clamping at the last entry."""

    def __init__(self, times: list[datetime]) -> None:
        self._times = times
        self.calls = 0

    def __call__(self) -> datetime:
        t = self._times[min(self.calls, len(self._times) - 1)]
        self.calls += 1
        return t


class _RecordingSleep:
    """A ``sleep_fn`` that records every requested duration without sleeping."""

    def __init__(self) -> None:
        self.sleeps: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.sleeps.append(seconds)


class _Result:
    """A tiny ``ExecutionResult`` stand-in (the ``state.CycleResult`` duck-type)."""

    def __init__(self, status: str, profit_loss: float | None = None) -> None:
        self.status = status
        self.profit_loss = profit_loss


class _FakeBroker:
    """Duck-typed Phase-1 broker: records connect/disconnect; returns an Envelope-like mapping."""

    def __init__(self, *, connected: bool = False, connect_ok: bool = True) -> None:
        self._connected = connected
        self._connect_ok = connect_ok
        self.connect_calls = 0
        self.disconnect_calls = 0

    def is_connected(self) -> bool:
        return self._connected

    def connect(self) -> dict:
        self.connect_calls += 1
        self._connected = self._connect_ok
        return {"ok": self._connect_ok, "error": None if self._connect_ok else "boom"}

    def disconnect(self) -> dict:
        self.disconnect_calls += 1
        self._connected = False
        return {"ok": True}


class _FakeExecutor:
    """Duck-typed Phase-5 executor: bare ``run()``; optionally raises on given (1-indexed) calls."""

    def __init__(self, *, result: _Result | None = None, raise_on: set[int] | None = None) -> None:
        self._result = result if result is not None else _Result("NO_TRADE")
        self._raise_on = raise_on or set()
        self.run_calls = 0

    def run(self) -> _Result:
        self.run_calls += 1
        if self.run_calls in self._raise_on:
            raise RuntimeError(f"executor boom on call {self.run_calls}")
        return self._result


class _FakeResearchTick:
    def __init__(self) -> None:
        self.calls = 0

    def ensure_candidates(self, state: SchedulerState):
        self.calls += 1
        return None


class _FakeReconciler:
    """Counts ``tick`` calls. Does NOT stamp ``last_reconcile_ts`` → throttle stays off in loop
    tests (the throttle is exercised directly in ``test_reconcile_throttle``)."""

    def __init__(self) -> None:
        self.tick_calls = 0

    def tick(self, state: SchedulerState):
        self.tick_calls += 1
        return None


class _FakeAutoConfirm:
    def __init__(self, *, ok: bool = True, reason: str | None = None) -> None:
        self._ok = ok
        self._reason = reason
        self.calls = 0

    def can_open(self, state: SchedulerState) -> tuple[bool, str | None]:
        self.calls += 1
        return self._ok, self._reason


class _FakeBackoff:
    def __init__(self) -> None:
        self.successes = 0
        self.failures = 0

    def record_success(self, state: SchedulerState) -> SchedulerState:
        self.successes += 1
        state.consecutive_failures = 0
        return state

    def record_failure(self, state: SchedulerState) -> SchedulerState:
        self.failures += 1
        state.consecutive_failures += 1
        return state

    def should_trip(self, state: SchedulerState) -> bool:
        return False

    def delay_s(self, state: SchedulerState) -> float:
        return 1.0


class _FakeBudget:
    def __init__(self, exhausted: bool = False) -> None:
        self._exhausted = exhausted

    def is_exhausted(self) -> bool:
        return self._exhausted


# --- builders --------------------------------------------------------------


def _config(tmp_path, **over) -> SchedulerConfig:
    base = dict(
        state_path=str(tmp_path / "scheduler_state.json"),
        kill_path=str(tmp_path / "KILL"),
        command_path=str(tmp_path / "cmd.json"),
        live_db_path=str(tmp_path / "db.sqlite"),
    )
    base.update(over)
    return SchedulerConfig(**base)


def _make_runner(
    tmp_path,
    *,
    times: list[datetime],
    config: SchedulerConfig | None = None,
    auto_confirm=None,
    backoff=None,
    research_tick=None,
    reconciler=None,
    executor=None,
    broker=None,
    preflight_fn=None,
    max_iterations: int | None = 1,
):
    cfg = config or _config(tmp_path)
    sleep = _RecordingSleep()
    clock = Clock(cfg, now_fn=_SteppingNow(times), sleep_fn=sleep)
    store = StateStore(cfg.state_path)
    runner = SchedulerRunner(
        clock=clock,
        state_store=store,
        config=cfg,
        auto_confirm=auto_confirm or _FakeAutoConfirm(),
        backoff=backoff or _FakeBackoff(),
        research_tick=research_tick or _FakeResearchTick(),
        reconciler=reconciler or _FakeReconciler(),
        executor=executor or _FakeExecutor(),
        broker=broker or _FakeBroker(),
        preflight_fn=preflight_fn or (lambda: None),
        max_iterations=max_iterations,
    )
    return runner, sleep, store, cfg


# --- fixture-time sanity ---------------------------------------------------


def test_fixture_times_classify_as_expected(tmp_path) -> None:
    """Guard the date arithmetic the rest of the file relies on."""
    clock = Clock(_config(tmp_path))
    assert clock.classify(_PRE_OPEN_T) is Phase.PRE_OPEN
    assert clock.classify(_WINDOW_T) is Phase.WINDOW
    assert clock.classify(_POST_WINDOW_T) is Phase.POST_WINDOW
    assert clock.classify(_WEEKEND_T) is Phase.IDLE


# --- WINDOW happy path -----------------------------------------------------


def test_window_happy_path_runs_research_then_bare_execute(tmp_path) -> None:
    """can_open ok → research, then a BARE executor.run() (Contract A); OPEN bumps trades_today."""
    rt = _FakeResearchTick()
    ex = _FakeExecutor(result=_Result("OPEN"))
    runner, sleep, store, cfg = _make_runner(
        tmp_path, times=[_WINDOW_T], research_tick=rt, executor=ex, max_iterations=1
    )

    runner.run()

    assert rt.calls == 1
    assert ex.run_calls == 1
    assert store.load().trades_today == 1                 # OPEN is a real trade (Contract E)
    assert cfg.cycle_interval_min * 60 in sleep.sleeps    # WINDOW sleeps one cycle interval


def test_no_trade_status_does_not_count_against_the_cap(tmp_path) -> None:
    """A NO_TRADE cycle still calls research + execute, but does not increment trades_today."""
    ex = _FakeExecutor(result=_Result("NO_TRADE"))
    runner, _sleep, store, _cfg = _make_runner(
        tmp_path, times=[_WINDOW_T], executor=ex, max_iterations=1
    )

    runner.run()

    assert ex.run_calls == 1
    assert store.load().trades_today == 0


# --- pre-cycle cap gate (real AutoConfirm) ---------------------------------


def test_cap_block_skips_research_and_execute(tmp_path) -> None:
    """A real AutoConfirm at the trade cap → no research, no execute, reason recorded."""
    cfg = _config(tmp_path, max_trades_per_day=0)  # cap reached at 0 trades
    real_ac = AutoConfirm(cfg, StateStore(cfg.state_path), cfg.kill_path, _FakeBudget(False), lambda d: 0.0)
    rt = _FakeResearchTick()
    ex = _FakeExecutor()
    runner, _sleep, store, _cfg = _make_runner(
        tmp_path, times=[_WINDOW_T], config=cfg, auto_confirm=real_ac,
        research_tick=rt, executor=ex, max_iterations=1,
    )

    runner.run()

    assert rt.calls == 0
    assert ex.run_calls == 0
    assert store.load().last_no_trade_reason == "CAP_BLOCK"


# --- PRE_OPEN / POST_WINDOW / IDLE ----------------------------------------


def test_pre_open_warms_and_reconciles_then_sleeps_until_window(tmp_path) -> None:
    rec = _FakeReconciler()
    ex = _FakeExecutor()
    broker = _FakeBroker()
    runner, sleep, _store, cfg = _make_runner(
        tmp_path, times=[_PRE_OPEN_T], reconciler=rec, executor=ex, broker=broker, max_iterations=1
    )

    runner.run()

    assert ex.run_calls == 0
    assert rec.tick_calls >= 1                 # startup + PRE_OPEN reconcile
    assert broker.connect_calls == 1           # preflight connected; warm-ups are no-ops after
    # Sleeps until WINDOW, capped by idle poll: 08:55 → 09:00 is 5 min == idle_poll default.
    assert min(300.0, cfg.idle_poll_min * 60) in sleep.sleeps


def test_post_window_forces_reconcile_and_sleeps_to_next_pre_open(tmp_path) -> None:
    rec = _FakeReconciler()
    ex = _FakeExecutor()
    runner, sleep, _store, _cfg = _make_runner(
        tmp_path, times=[_POST_WINDOW_T], reconciler=rec, executor=ex, max_iterations=1
    )

    runner.run()

    assert ex.run_calls == 0
    assert rec.tick_calls >= 1
    assert sleep.sleeps and sleep.sleeps[-1] > 0  # long sleep to the next pre-open


def test_idle_only_sleeps_no_work(tmp_path) -> None:
    rec = _FakeReconciler()
    rt = _FakeResearchTick()
    ex = _FakeExecutor()
    runner, sleep, _store, cfg = _make_runner(
        tmp_path, times=[_WEEKEND_T], reconciler=rec, research_tick=rt, executor=ex, max_iterations=1
    )

    runner.run()

    assert ex.run_calls == 0
    assert rt.calls == 0
    # The only loop sleep is the idle poll (startup/shutdown do not sleep).
    assert sleep.sleeps == [cfg.idle_poll_min * 60]
    # Startup + shutdown still reconcile (forced), but the IDLE iteration does not add one.
    assert rec.tick_calls == 2


# --- full simulated day ----------------------------------------------------


def test_full_simulated_day(tmp_path) -> None:
    """IDLE → PRE_OPEN → WINDOW → POST_WINDOW across one trading day (no rollover)."""
    rec = _FakeReconciler()
    rt = _FakeResearchTick()
    ex = _FakeExecutor(result=_Result("OPEN"))
    runner, sleep, store, _cfg = _make_runner(
        tmp_path,
        times=[_EARLY_T, _PRE_OPEN_T, _WINDOW_T, _POST_WINDOW_T],
        reconciler=rec, research_tick=rt, executor=ex, max_iterations=4,
    )

    runner.run()

    assert ex.run_calls == 1                 # only the WINDOW iteration trades
    assert rt.calls == 1
    assert store.load().trades_today == 1
    # reconcile: startup + PRE_OPEN + WINDOW + POST_WINDOW(forced) + shutdown = 5 (IDLE adds none).
    assert rec.tick_calls == 5
    assert len(sleep.sleeps) == 4            # one sleep per iteration


# --- kill-switch -----------------------------------------------------------


def test_kill_switch_stops_loop_and_runs_shutdown(tmp_path) -> None:
    cfg = _config(tmp_path)
    killswitch.set_kill(cfg.kill_path, "manual:test")
    ex = _FakeExecutor()
    broker = _FakeBroker()
    runner, _sleep, store, _cfg = _make_runner(
        tmp_path, times=[_WINDOW_T], config=cfg, executor=ex, broker=broker, max_iterations=5
    )

    with caplog_at(logging.CRITICAL):
        runner.run()

    assert ex.run_calls == 0                  # never traded
    assert store.load().kill_reason == "manual:test"
    assert broker.disconnect_calls == 1       # shutdown ran


# --- backoff trip (real BackoffTracker) ------------------------------------


def test_backoff_trip_sets_kill_and_stops(tmp_path) -> None:
    """Three consecutive executor exceptions → real backoff trips → KILL set 'auto:backoff'."""
    cfg = _config(tmp_path, max_consecutive_failures=3)
    ex = _FakeExecutor(raise_on={1, 2, 3})
    runner, _sleep, store, _cfg = _make_runner(
        tmp_path, times=[_WINDOW_T], config=cfg, backoff=BackoffTracker(cfg),
        executor=ex, max_iterations=10,
    )

    with caplog_at(logging.CRITICAL):
        runner.run()

    assert ex.run_calls == 3                   # tripped on the 3rd, no 4th attempt
    assert killswitch.is_set(cfg.kill_path)
    assert killswitch.read_reason(cfg.kill_path) == "auto:backoff"
    assert store.load().kill_reason == "auto:backoff"


def test_transient_failure_backs_off_then_recovers(tmp_path) -> None:
    """One executor exception (below the trip threshold) → backoff delay sleep, loop continues."""
    cfg = _config(tmp_path, max_consecutive_failures=3)
    ex = _FakeExecutor(result=_Result("NO_TRADE"), raise_on={1})
    runner, sleep, store, _cfg = _make_runner(
        tmp_path, times=[_WINDOW_T], config=cfg, backoff=BackoffTracker(cfg),
        executor=ex, max_iterations=2,
    )

    with caplog_at(logging.CRITICAL):
        runner.run()

    assert ex.run_calls == 2                    # failed once, then succeeded
    assert cfg.backoff_base_s in sleep.sleeps   # the n=1 backoff delay (30s default)
    assert not killswitch.is_set(cfg.kill_path)
    assert store.load().consecutive_failures == 0  # reset after the clean second cycle


# --- preflight -------------------------------------------------------------


def test_preflight_fn_failure_raises_and_never_loops(tmp_path) -> None:
    def boom() -> None:
        raise RuntimeError("keyring unreachable")

    ex = _FakeExecutor()
    runner, _sleep, _store, _cfg = _make_runner(
        tmp_path, times=[_WINDOW_T], executor=ex, preflight_fn=boom, max_iterations=1
    )

    with pytest.raises(PreflightError):
        runner.run()
    assert ex.run_calls == 0


def test_preflight_broker_connect_failure_raises(tmp_path) -> None:
    ex = _FakeExecutor()
    runner, _sleep, _store, _cfg = _make_runner(
        tmp_path, times=[_WINDOW_T], executor=ex, broker=_FakeBroker(connect_ok=False),
        max_iterations=1,
    )

    with pytest.raises(PreflightError):
        runner.run()
    assert ex.run_calls == 0


def test_preflight_pass_enters_loop(tmp_path) -> None:
    ex = _FakeExecutor(result=_Result("OPEN"))
    runner, _sleep, _store, _cfg = _make_runner(
        tmp_path, times=[_WINDOW_T], executor=ex, max_iterations=1
    )
    runner.run()  # must not raise
    assert ex.run_calls == 1


# --- reconcile throttle ----------------------------------------------------


def test_reconcile_throttle(tmp_path) -> None:
    """A recent ``last_reconcile_ts`` suppresses an unforced reconcile; ``force`` always runs."""
    rec = _FakeReconciler()
    runner, _sleep, _store, cfg = _make_runner(
        tmp_path, times=[_WINDOW_T], reconciler=rec, max_iterations=1
    )
    now = _WINDOW_T
    state = SchedulerState(date="2026-06-29")

    # 5 minutes ago, interval default 15 min → NOT due → no tick.
    state.last_reconcile_ts = (now - timedelta(minutes=5)).isoformat()
    runner._maybe_reconcile(state, now)
    assert rec.tick_calls == 0

    # force bypasses the throttle.
    runner._maybe_reconcile(state, now, force=True)
    assert rec.tick_calls == 1

    # 20 minutes ago → due → ticks.
    state.last_reconcile_ts = (now - timedelta(minutes=20)).isoformat()
    runner._maybe_reconcile(state, now)
    assert rec.tick_calls == 2

    # No prior reconcile → due.
    state.last_reconcile_ts = None
    runner._maybe_reconcile(state, now)
    assert rec.tick_calls == 3


# --- package export --------------------------------------------------------


def test_exported_from_package_root() -> None:
    assert ExportedSchedulerRunner is SchedulerRunner


# --- helper ----------------------------------------------------------------


class caplog_at:
    """Context manager silencing expected CRITICAL logs (the loop logs them by design)."""

    def __init__(self, level: int) -> None:
        self._level = level
        self._logger = logging.getLogger("scheduler.runner")
        self._prev = self._logger.level

    def __enter__(self):
        self._logger.setLevel(self._level + 10)  # suppress at/below the expected level in test output
        return self

    def __exit__(self, *exc) -> None:
        self._logger.setLevel(self._prev)
