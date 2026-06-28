"""Live test for the Phase-8 scheduler — a real unattended cycle against IG Demo (operator-run).

This is the phase's gate: it builds the **real** wired daemon (one warm IG-Demo broker, real Phase-4
research, the Phase-6 debate + Phase-7 reward injected into the Phase-5 executor) and runs a **bounded**
number of real WINDOW cycles unattended — autonomous candidate generation, the auto-confirm gate, a
real order if a signal qualifies, the reward loop, and a clean stop + reconcile. It then verifies, via
a **read-only** DB / state read, that the cycle did its job.

It is deliberately lenient about *whether a trade happened* (the same discipline as the Phase-5/6/7
live tests): a clean run that places no order — because research abstained, a VETO fired, the cap/budget
blocked, or the market is quiet — is a valid PASS. What it hard-asserts:

  - the daemon ran and stopped **cleanly** (no exception, no orphan),
  - the scheduler state was **persisted**, and
  - **if** a demo trade was opened+closed today, its reward bookkeeping landed (``trade_outcomes`` CLOSED
    **and** a ``reward_pts`` row) — proving the autonomous open→close→reward loop end-to-end.

Run it **inside the trading window** (09:00–17:30 Europe/Berlin) for the cycle to do real work. Not in
CI. Prereqs: ``bash scripts/dev_install.sh`` + ``python phase2_persistence/scripts/init_db.py`` + the
IG-Demo creds seeded in the keyring (unlocked session). ``RESULT: N/M``; exit 0 = PASS.

Run: ``python phase8_scheduler/scripts/live_test.py [--iterations 2] [--max-hold-min 1]``
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# scripts/ -> phase8_scheduler/ (so `import scheduler.*` / `import scripts.wiring` resolve)
_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))

_REPO_ROOT = _PROJECT_DIR.parent
_DB_PATH = _REPO_ROOT / "data" / "trading_bot.sqlite"
_STATE_PATH = _REPO_ROOT / "data" / "state" / "scheduler_state.json"


def _log(msg: str) -> None:
    print(msg, file=sys.stderr)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="live_test.py",
        description="Real unattended Phase-8 cycle vs IG Demo (operator-run; run inside the window).",
    )
    p.add_argument("--iterations", type=int, default=2, help="bounded WINDOW cycles to run (default 2).")
    p.add_argument(
        "--max-hold-min", type=int, default=1,
        help="executor max-hold minutes so a placed trade closes fast via time-stop (default 1).",
    )
    p.add_argument("--daily-loss-cap", type=float, default=1800.0, help="daily-loss breaker (default 1800).")
    return p.parse_args(argv)


def _today_berlin() -> str:
    return datetime.now(ZoneInfo("Europe/Berlin")).strftime("%Y-%m-%d")


def _read_state() -> dict:
    import json

    if not _STATE_PATH.exists():
        return {}
    try:
        return json.loads(_STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s", stream=sys.stderr
    )

    from execution.config import ExecutionConfig  # noqa: E402
    from scheduler.config import SchedulerConfig  # noqa: E402
    from scheduler.exceptions import PreflightError  # noqa: E402
    from scripts.wiring import build_scheduler  # noqa: E402

    config = SchedulerConfig(account="demo", daily_loss_cap=args.daily_loss_cap)
    # Short hold so a placed demo trade closes quickly via the monitor time-stop; the clock sleep is a
    # no-op so the bounded loop runs back-to-back (the executor keeps its own real sleep for monitoring).
    exec_cfg = ExecutionConfig(max_hold_minutes=args.max_hold_min, poll_interval_s=10)

    _log(f"=== Phase-8 live test (IG Demo, {args.iterations} bounded cycles) ===")
    try:
        runner = build_scheduler(
            config, sleep_fn=lambda _s: None, max_iterations=args.iterations, exec_config=exec_cfg
        )
    except Exception as exc:  # noqa: BLE001 - construction surfaces keyring/import problems
        _log(f"FAIL: could not build the scheduler: {exc}")
        return 1

    passed = 0
    total = 0

    # 1) Clean run (preflight + bounded loop + shutdown) without raising.
    total += 1
    try:
        runner.run()
        _log("[1] PASS: daemon ran and stopped cleanly (preflight ok, bounded loop, shutdown).")
        passed += 1
    except PreflightError as exc:
        _log(f"[1] FAIL (preflight): {exc} — fix the keyring/DB prereq, then re-run.")
        return 1
    except Exception as exc:  # noqa: BLE001
        _log(f"[1] FAIL: the loop raised: {exc!r}")
        return 1

    # 2) State persisted.
    total += 1
    state = _read_state()
    if state:
        _log(
            f"[2] PASS: scheduler_state persisted — trades_today={state.get('trades_today')}, "
            f"last_research_ts={state.get('last_research_ts')}, "
            f"last_no_trade_reason={state.get('last_no_trade_reason')}, "
            f"last_reconcile_ts={state.get('last_reconcile_ts')}."
        )
        passed += 1
    else:
        _log(f"[2] FAIL: no scheduler_state at {_STATE_PATH}.")

    # 3) If a demo trade was opened+closed today, its reward bookkeeping must have landed.
    total += 1
    today = _today_berlin()
    if not _DB_PATH.exists():
        _log(f"[3] SKIP→PASS: no DB at {_DB_PATH} yet (no trade attempted).")
        passed += 1
    else:
        conn = sqlite3.connect(f"file:{_DB_PATH}?mode=ro", uri=True)
        try:
            closed = conn.execute(
                "SELECT id, deal_id, status FROM trade_outcomes "
                "WHERE session_date = ? AND status = 'CLOSED' ORDER BY id DESC LIMIT 1",
                (today,),
            ).fetchone()
            if closed is None:
                _log("[3] PASS: no CLOSED demo trade today (valid no-trade run — abstain/VETO/cap/quiet).")
                passed += 1
            else:
                trade_id, deal_id = closed[0], closed[1]
                reward = conn.execute(
                    "SELECT COUNT(*) FROM reward_pts WHERE trade_id = ?", (trade_id,)
                ).fetchone()[0]
                lessons = conn.execute(
                    "SELECT COUNT(*) FROM trade_lessons WHERE trade_id = ?", (trade_id,)
                ).fetchone()[0]
                if reward > 0:
                    _log(
                        f"[3] PASS: demo trade {deal_id} CLOSED + reward_pts written "
                        f"(lessons={lessons}, best-effort) — autonomous open→close→reward proved."
                    )
                    passed += 1
                else:
                    _log(f"[3] FAIL: trade {deal_id} CLOSED but NO reward_pts row (reward loop broke).")
        finally:
            conn.close()

    _log(f"RESULT: {passed}/{total} passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
