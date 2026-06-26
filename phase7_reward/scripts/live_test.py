#!/usr/bin/env python3
"""Hard-assert live verification for the Phase-7 reward loop — the Phase-7 gate.

Runs one **full** Phase-5 execution cycle **with the reward sink injected** at the
place/monitor seam, against IG Demo, and asserts the cycle's invariants, then exits
``0`` (PASS) / ``1`` (FAIL). It auto-confirms (running live_test *is* the consent)
and, when a fresh candidate exists and all gates/VETOs pass, **places a real Demo
order** and monitors it to a close (``max_hold_minutes`` / ``poll_interval_s``
overridden small so the time-stop closes within ~a minute).

**When an order placed and closed**, the reward proofs are asserted against the real
``data/trading_bot.sqlite``: a ``trade_outcomes`` row for the deal exists and is
``CLOSED``, and a ``reward_pts`` row was written for it (the deterministic learning
writes — Decision B/D). The ``trade_lessons`` row is **best-effort** (the only AI;
a flaky Haiku call may skip it without breaking the close — Decision E/J), so it is
reported informationally, not hard-gated. A clean ``NO_TRADE``/abstain (a gate/VETO
said no, or no fresh candidate / market closed) is **also** a valid exit-0 outcome —
the reward proofs are then skipped. Only a fail-closed ``ABORT`` is a failure.

Seed a candidate first (30-min TTL), in the trade window, with the current move::

    python phase5_execution/scripts/seed_candidate.py --direction SELL

And ensure the DB schema is current (migration 002 adds the reward columns)::

    python phase2_persistence/scripts/init_db.py

Live script: keyring + IG Demo + a real Demo order + a real Anthropic request (the
lesson); non-deterministic; deliberately not collected by ``pytest`` / CI. **The
operator runs it.** Prereqs: IG Demo creds + ``anthropic_api_key`` in the keyring;
``bash scripts/dev_install.sh``.

Output discipline: the PASS/FAIL table + ``RESULT`` line → **stderr**; the single
machine-readable result JSON → **stdout**.

Usage:
    python scripts/live_test.py
    python scripts/live_test.py --broker ig_demo --verbose
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

# Make the project dir importable so the (non-installed) `scripts` package resolves.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent  # phase7_reward/
sys.path.insert(0, str(_PROJECT_ROOT))

from execution.config import ExecutionConfig  # noqa: E402
from execution.ig_bot import make_confirm_fn, result_to_dict  # noqa: E402

log = logging.getLogger("phase7.live_test")

_PLACED_AND_CLOSED = {"CLOSED_BY_BROKER", "TIME_STOP"}
_NO_ORDER = {"NO_TRADE", "ABORTED_BY_USER"}
_OK_STATUSES = _PLACED_AND_CLOSED | _NO_ORDER

# Same data path the wiring resolves (scripts/ -> phase7_reward/ -> repo root).
_DB_PATH = _PROJECT_ROOT.parent / "data" / "trading_bot.sqlite"


def _eprint(message: str = "") -> None:
    print(message, file=sys.stderr)


class _Check:
    """Tiny PASS/FAIL recorder so the script reads like a checklist."""

    def __init__(self) -> None:
        self.failures = 0
        self.total = 0

    def __call__(self, label: str, condition: bool, detail: str = "") -> bool:
        self.total += 1
        ok = bool(condition)
        if not ok:
            self.failures += 1
        mark = "✓" if ok else "✗"
        suffix = f" — {detail}" if detail else ""
        _eprint(f"  {mark} {label}{suffix}")
        return ok


def _count(db: Any, sql: str, params: tuple) -> int:
    """Run a ``SELECT COUNT(*)`` against the live DB (advisory read)."""
    return int(db.conn.execute(sql, params).fetchone()[0])


def _reconcile_until_closed(
    db: Any, sink: Any, deal_id: str, *, attempts: int, wait_s: float
) -> None:
    """Drive the idempotent reconcile retry until the trade closes (or attempts run out).

    IG's transaction history can lag a just-closed deal by seconds–minutes, so the
    in-cycle ``on_trade_closed`` may have fail-closed on ``PnLUnavailable`` and left the
    trade OPEN (by design — retry-able via ``deal_id``). This exercises that documented
    "later pass": wait for history to catch up, then call
    ``RewardSink.reconcile_open_trades([deal_id])``, which is idempotent (the OPEN/CLOSED
    status guard never double-scores). No-op if the in-cycle close already resolved.
    """
    for i in range(1, attempts + 1):
        row = db.get_trade_by_deal_id(deal_id)
        if row is None or row.get("status") != "OPEN":
            return  # resolved in-cycle (or row gone) — nothing to reconcile
        if sink is None:
            _eprint("[live] executor has no reward sink — cannot reconcile")
            return
        _eprint(f"[live] trade still OPEN (IG history lag?) — waiting {wait_s:g}s then "
                f"reconcile attempt {i}/{attempts} …")
        time.sleep(wait_s)
        resolved = sink.reconcile_open_trades([deal_id])
        if deal_id in resolved:
            _eprint(f"[live] reconcile resolved deal_id={deal_id} on attempt {i}.")
            return
    _eprint(f"[live] deal_id={deal_id} still unresolved after {attempts} reconcile "
            "attempt(s) — IG history may still be lagging; the reward asserts below will "
            "fail. Re-run, or reconcile again later.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--broker", default="ig_demo", help="broker id (default: ig_demo)")
    parser.add_argument("--verbose", action="store_true", help="DEBUG logging")
    parser.add_argument("--reconcile-attempts", type=int, default=3,
                        help="reconcile retries if IG history lags the close (default: 3)")
    parser.add_argument("--reconcile-wait", type=float, default=20.0,
                        help="seconds to wait before each reconcile attempt (default: 20)")
    args = parser.parse_args(argv)

    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    # Short hold + fast polling so a placed order self-closes (time-stop) quickly.
    config = ExecutionConfig(max_hold_minutes=1, poll_interval_s=10)
    check = _Check()

    from scripts.wiring import build_executor

    _eprint(f"[live] building executor + reward sink (broker={args.broker}, "
            f"max_hold={config.max_hold_minutes}m, poll={config.poll_interval_s}s)")
    executor = build_executor(
        config,
        confirm_fn=make_confirm_fn(auto_yes=True, dry=False),
        broker_name=args.broker,
    )

    _eprint("[live] --- running full cycle with reward sink (IG Demo; may place + close) ---")
    result: Any = None
    try:
        result = executor.run()
        run_ok = True
    except Exception as exc:  # noqa: BLE001 — the gate must report, not crash
        run_ok = False
        log.exception("executor.run raised")
        _eprint(f"[live] run() raised: {type(exc).__name__}: {exc}")

    check("executor.run() completed without raising", run_ok)

    if run_ok:
        check("status is a clean, known outcome (not ABORT)",
              result.status in _OK_STATUSES,
              f"status={result.status} detail={result.detail!r}")

        if result.status in _PLACED_AND_CLOSED:
            _eprint(f"[live] outcome: ORDER PLACED → {result.status} — asserting reward writes.")
            check("a deal_id was assigned", bool(result.deal_id),
                  f"deal_id={result.deal_id!r}")

            # Read back the durable reward writes from the live DB.
            from persistence import Database

            db = Database(str(_DB_PATH))
            try:
                # If the in-cycle resolve fail-closed on IG history lag, the trade is
                # still OPEN — drive the documented idempotent retry before asserting.
                if result.deal_id:
                    _reconcile_until_closed(
                        db, executor.reward_sink, result.deal_id,
                        attempts=args.reconcile_attempts, wait_s=args.reconcile_wait,
                    )
                trade = db.get_trade_by_deal_id(result.deal_id) if result.deal_id else None
                check("trade_outcomes row exists and is CLOSED",
                      bool(trade) and trade.get("status") == "CLOSED",
                      f"row={trade}")
                if trade:
                    trade_id = trade["id"]
                    n_reward = _count(
                        db, "SELECT COUNT(*) FROM reward_pts WHERE trade_id = ?", (trade_id,)
                    )
                    check("a reward_pts row was written for the trade",
                          n_reward >= 1, f"reward_pts rows={n_reward}")
                    # Lesson is best-effort (the only AI) — reported, not hard-gated.
                    n_lesson = _count(
                        db, "SELECT COUNT(*) FROM trade_lessons WHERE trade_id = ?", (trade_id,)
                    )
                    if n_lesson >= 1:
                        _eprint(f"[live] trade_lessons row written (best-effort lesson ok): "
                                f"{n_lesson}")
                    else:
                        _eprint("[live] no trade_lessons row this cycle — the lesson is "
                                "best-effort (Decision E/J); a flaky Haiku call skips it "
                                "without breaking the close. Re-run to retry the lesson.")
            finally:
                db.close()
        else:
            _eprint(f"[live] outcome: {result.status} — clean no-trade "
                    "(gate/VETO said no, or no fresh candidate / market closed). "
                    "A valid exit-0 result; reward proofs skipped. Seed a candidate in "
                    "the window and re-run to exercise the reward loop.")

    # Machine-readable: the cycle result (empty object if the run raised).
    print(json.dumps(result_to_dict(result) if run_ok else {}, indent=2))

    passed = check.total - check.failures
    _eprint(f"\nRESULT: {passed}/{check.total} passed")
    return 0 if check.failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
