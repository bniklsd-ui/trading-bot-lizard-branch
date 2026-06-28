"""Offline smoke test for the Phase-8 loop — a simulated day with fakes, no network (concept §11).

Unlike the Phase-5/6/7 smoke tests (which dry-run the *real* stack), the scheduler's value is the
**loop mechanics** — market-hours phase transitions, the trade cap, the kill-switch — so this drives
a real :class:`~scheduler.runner.SchedulerRunner` over a **fake clock** + **fake** broker / research
/ executor / reconciler, with a no-op sleep and a ``max_iterations`` bound. It places **no order**,
touches **no keyring** and makes **no network call**; it just shows the loop behaving. Fast, manual.

Run: ``python phase8_scheduler/scripts/smoke_test.py``  → prints a narrative to stderr, exit 0 = ok.
"""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# scripts/ -> phase8_scheduler/ (so `import scheduler.*` resolves when run directly)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scheduler import killswitch  # noqa: E402
from scheduler.backoff import BackoffTracker  # noqa: E402
from scheduler.clock import Clock  # noqa: E402
from scheduler.config import SchedulerConfig  # noqa: E402
from scheduler.runner import SchedulerRunner  # noqa: E402
from scheduler.state import StateStore  # noqa: E402

_BERLIN = ZoneInfo("Europe/Berlin")
# 2026-06-29 is a Monday (trading day). 07:00 → IDLE (pre warm-up), 08:55 → PRE_OPEN,
# 10:00 → WINDOW, 18:00 → POST_WINDOW.
_DAY = [
    datetime(2026, 6, 29, 7, 0, tzinfo=_BERLIN),
    datetime(2026, 6, 29, 8, 55, tzinfo=_BERLIN),
    datetime(2026, 6, 29, 10, 0, tzinfo=_BERLIN),
    datetime(2026, 6, 29, 18, 0, tzinfo=_BERLIN),
]
_WINDOW = datetime(2026, 6, 29, 10, 0, tzinfo=_BERLIN)


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


class _SteppingNow:
    def __init__(self, times: list[datetime]) -> None:
        self._times, self.i = times, 0

    def __call__(self) -> datetime:
        t = self._times[min(self.i, len(self._times) - 1)]
        self.i += 1
        return t


class _Result:
    def __init__(self, status: str, profit_loss: float | None = None) -> None:
        self.status, self.profit_loss = status, profit_loss


class _Broker:
    def __init__(self) -> None:
        self.connected = False

    def is_connected(self) -> bool:
        return self.connected

    def connect(self) -> dict:
        self.connected = True
        return {"ok": True}

    def disconnect(self) -> dict:
        self.connected = False
        return {"ok": True}


class _Executor:
    def __init__(self) -> None:
        self.runs = 0

    def run(self) -> _Result:
        self.runs += 1
        _log("    · executor.run() → OPEN (fake demo trade)")
        return _Result("OPEN")


class _ResearchTick:
    def ensure_candidates(self, state) -> None:
        _log("    · research_tick → fresh candidate written (fake)")


class _Reconciler:
    def tick(self, state) -> None:
        _log("    · reconcile tick")


class _AutoConfirm:
    def __init__(self, ok: bool = True, reason: str | None = None) -> None:
        self.ok, self.reason = ok, reason

    def can_open(self, state):
        return self.ok, self.reason


def _runner(tmp: str, *, times, auto_confirm, executor, max_iterations) -> tuple[SchedulerRunner, StateStore, SchedulerConfig]:
    cfg = SchedulerConfig(
        state_path=str(Path(tmp) / "scheduler_state.json"),
        kill_path=str(Path(tmp) / "KILL"),
    )
    clock = Clock(cfg, now_fn=_SteppingNow(times), sleep_fn=lambda _s: None)
    store = StateStore(cfg.state_path)
    runner = SchedulerRunner(
        clock=clock,
        state_store=store,
        config=cfg,
        auto_confirm=auto_confirm,
        backoff=BackoffTracker(cfg),
        research_tick=_ResearchTick(),
        reconciler=_Reconciler(),
        executor=executor,
        broker=_Broker(),
        preflight_fn=lambda: None,
        max_iterations=max_iterations,
    )
    return runner, store, cfg


def main() -> int:
    _log("=== Phase-8 scheduler smoke test (offline, fakes, no network) ===\n")

    with tempfile.TemporaryDirectory() as tmp:
        _log("[1] A simulated trading day: IDLE → PRE_OPEN → WINDOW → POST_WINDOW")
        ex = _Executor()
        runner, store, _ = _runner(tmp, times=_DAY, auto_confirm=_AutoConfirm(ok=True), executor=ex, max_iterations=4)
        runner.run()
        st = store.load()
        _log(f"  → trades_today={st.trades_today}, executor runs={ex.runs} (one WINDOW cycle)\n")
        assert ex.runs == 1 and st.trades_today == 1

    with tempfile.TemporaryDirectory() as tmp:
        _log("[2] WINDOW with the trade cap reached → no research, no order")
        ex = _Executor()
        runner, store, _ = _runner(
            tmp, times=[_WINDOW], auto_confirm=_AutoConfirm(ok=False, reason="CAP_BLOCK"),
            executor=ex, max_iterations=1,
        )
        runner.run()
        st = store.load()
        _log(f"  → executor runs={ex.runs}, last_no_trade_reason={st.last_no_trade_reason!r}\n")
        assert ex.runs == 0 and st.last_no_trade_reason == "CAP_BLOCK"

    with tempfile.TemporaryDirectory() as tmp:
        _log("[3] Kill-switch set before a WINDOW cycle → loop stops, shutdown runs")
        ex = _Executor()
        runner, store, cfg = _runner(tmp, times=[_WINDOW], auto_confirm=_AutoConfirm(ok=True), executor=ex, max_iterations=5)
        killswitch.set_kill(cfg.kill_path, "manual:smoke")
        runner.run()
        st = store.load()
        _log(f"  → executor runs={ex.runs}, kill_reason={st.kill_reason!r}\n")
        assert ex.runs == 0 and st.kill_reason == "manual:smoke"

    _log("RESULT: 3/3 scenarios behaved as expected (offline). exit 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
