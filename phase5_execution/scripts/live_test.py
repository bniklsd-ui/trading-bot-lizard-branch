#!/usr/bin/env python3
"""Hard-assert live verification for the Phase-5 execution path — the Phase-5 gate.

Runs one **full** execution cycle against IG Demo and asserts the cycle's invariants,
then exits ``0`` (PASS) / ``1`` (FAIL). Unlike ``smoke_test.py`` this **auto-confirms**
(``make_confirm_fn(auto_yes=True)`` — running live_test *is* the consent) and, when the
market is open and a candidate exists, **places a real Demo order** and monitors it to a
close. To keep that open→close quick, it overrides ``max_hold_minutes`` / ``poll_interval_s``
to small values so the time-stop closes the position within ~a minute (a fast, deterministic
open→close), rather than holding for the default 4 h.

A clean ``NO_TRADE`` (a gate/VETO said no) or an abstain (no fresh candidate / market
closed) is **also** a valid exit-0 outcome — the run-logged reason tells which. Only a
fail-closed ``ABORT`` is a failure.

The forced-PENDING / adverse-momentum / declined-confirm proof-tests are covered
deterministically in CI (``test_order.py`` / ``test_executor.py``); this script's
guarantee is that the **same** gate/VETO/order/monitor path runs live end-to-end and only
a clean, contract-shaped result is produced.

Live script: touches the keyring + IG Demo + places a real Demo order, is
non-deterministic, and is deliberately not collected by ``pytest`` / CI. **The operator
runs it.** Prereqs: IG Demo creds (+ ``anthropic_api_key`` if research must run) in the
keyring; ``pip install -e`` the five packages (``scripts/dev_install.sh``).

Output discipline: the PASS/FAIL table + ``RESULT`` line → **stderr**; the single
machine-readable result JSON → **stdout**.

Usage:
    python scripts/live_test.py
    python scripts/live_test.py --epic IX.D.DAX.IFMM.IP --broker ig_demo --verbose
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Make the project dir importable so the (non-installed) `scripts` package resolves.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent  # phase5_execution/
sys.path.insert(0, str(_PROJECT_ROOT))

from execution.config import ExecutionConfig  # noqa: E402
from execution.execution_state import ExecutionState  # noqa: E402
from execution.ig_bot import make_confirm_fn, result_to_dict  # noqa: E402

log = logging.getLogger("phase5.live_test")

# Statuses a healthy cycle may end on (anything but a fail-closed ABORT).
_PLACED_AND_CLOSED = {"CLOSED_BY_BROKER", "TIME_STOP"}
_NO_ORDER = {"NO_TRADE", "ABORTED_BY_USER"}
_OK_STATUSES = _PLACED_AND_CLOSED | _NO_ORDER

# Same data path wiring resolves (scripts/ -> phase5_execution/ -> repo root).
_EXEC_STATE_PATH = _PROJECT_ROOT.parent / "data" / "state" / "execution_state.json"


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epic", default=None, help="research allow-list epic override")
    parser.add_argument("--broker", default="ig_demo", help="broker id (default: ig_demo)")
    parser.add_argument("--verbose", action="store_true", help="DEBUG logging")
    args = parser.parse_args(argv)

    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    # Short hold + fast polling so a placed order self-closes (time-stop) quickly.
    config = ExecutionConfig(max_hold_minutes=1, poll_interval_s=10)
    check = _Check()

    from scripts.wiring import build_executor  # noqa: E402

    _eprint(f"[live] building executor (broker={args.broker}, "
            f"max_hold={config.max_hold_minutes}m, poll={config.poll_interval_s}s)")
    executor = build_executor(
        config,
        confirm_fn=make_confirm_fn(auto_yes=True, dry=False),
        broker_name=args.broker,
        epic_override=args.epic,
    )

    _eprint("[live] --- running full cycle (IG Demo; may place + close a Demo order) ---")
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
            _eprint(f"[live] outcome: ORDER PLACED → {result.status}")
            check("a deal_id was assigned", bool(result.deal_id),
                  f"deal_id={result.deal_id!r}")
            if result.plan is not None:
                rec = ExecutionState(str(_EXEC_STATE_PATH)).get(result.plan.deal_reference)
                check("write-ahead record ended CLOSED",
                      bool(rec) and rec.get("status") == "CLOSED",
                      f"record={rec}")
        else:
            _eprint(f"[live] outcome: {result.status} — clean no-trade "
                    "(gate/VETO said no, or no fresh candidate / market closed). "
                    "A valid exit-0 result; reason in the log above.")

    # Machine-readable: the cycle result (empty object if the run raised).
    print(json.dumps(result_to_dict(result) if run_ok else {}, indent=2))

    passed = check.total - check.failures
    _eprint(f"\nRESULT: {passed}/{check.total} passed")
    return 0 if check.failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
