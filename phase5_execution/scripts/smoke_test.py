#!/usr/bin/env python3
"""Quick **DRY** smoke run of the Phase-5 execution cycle (concept §10).

Runs one real cycle against IG Demo — session health, startup reconcile, all gates,
sizing, the four fresh VETOs, and (if everything passes) builds the ``OrderPlan`` —
but **places no order**: the human-confirm gate is wired to a dry decliner
(``make_confirm_fn(dry=True)``), so ``open_position`` is never invoked. Use it to
eyeball where a cycle stops (a gate/VETO reason, or the would-be order) before doing
anything live. It *prints*; it does not hard-assert — the hard-asserted gate is
``live_test.py``.

Output discipline (project rule, same as Phase 3/4): human-readable progress + the
per-step reasons (the executor's stderr log at INFO) → **stderr**; the single
machine-readable result JSON → **stdout**.

Live script: touches the keyring + IG Demo, is non-deterministic, and is deliberately
not collected by ``pytest`` / CI. Prereqs: IG Demo creds in the keyring (Phase-1
``scripts/store_credential.py``); ``anthropic`` only if a research run is triggered.

Usage:
    python scripts/smoke_test.py
    python scripts/smoke_test.py --epic IX.D.DAX.IFMM.IP --broker ig_demo --verbose
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Make the project dir importable so the (non-installed) `scripts` package resolves.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent  # phase5_execution/
sys.path.insert(0, str(_PROJECT_ROOT))

from execution.config import ExecutionConfig  # noqa: E402
from execution.ig_bot import make_confirm_fn, result_to_dict  # noqa: E402

log = logging.getLogger("phase5.smoke_test")


def _eprint(message: str = "") -> None:
    """Human-readable progress → stderr (stdout is reserved for the JSON)."""
    print(message, file=sys.stderr)


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

    config = ExecutionConfig()

    from scripts.wiring import build_executor  # noqa: E402

    _eprint("[smoke] building executor (DRY — confirm declines, no order placed) ...")
    executor = build_executor(
        config,
        confirm_fn=make_confirm_fn(auto_yes=False, dry=True, log=log),
        broker_name=args.broker,
        epic_override=args.epic,
    )

    _eprint("[smoke] --- running cycle (gates + sizing + VETOs, no order) ---")
    result = executor.run()

    _eprint(f"[smoke] outcome: {result.status} — {result.detail}")
    if result.plan is not None:
        p = result.plan
        _eprint(
            f"[smoke] would-be order: {p.direction} {p.size} {p.epic} "
            f"stop={p.stop_level} limit={p.limit_level} ref={p.deal_reference}"
        )

    # Machine-readable: the cycle result (a DRY run never persists an order).
    print(json.dumps(result_to_dict(result), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
