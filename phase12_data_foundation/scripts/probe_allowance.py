#!/usr/bin/env python3
"""Operator script — the daily IG historical-data-allowance probe (Plan §6 Step 8 bullet 1,
D18). Wraps the known CLI one-liner (``phase10_v3/ALLOWANCE_INCIDENT_2026-08-08.md`` §6) as
a repeatable, budget-booking check: one ``get_ohlcv(epic, "MINUTE", 5)`` call (5 IG points),
books the spend and the returned ``allowance`` object into ``data/bars.sqlite`` via
``SourceBudget`` — the ledger ``reset_universe.py``'s restart gate (D18) reads to decide
whether it's safe to reset the quarantined universe.

Live, network, keyring-touching (real IG demo session) — not run in tests, same
"operator-run" convention as ``phase8_scheduler/scripts/wiring.py``. Nikinger-run per
the ``feedback_live_testing`` memory: prepped here, executed on explicit go-ahead.

Output discipline (repo convention): human narrative -> stderr, machine-readable JSON ->
stdout. Exit 0 on a successful probe (even one that reveals an exhausted allowance —
that's a successful *observation*), exit 1 only when the call itself failed (network/auth/
still-exhausted-403), so a daily cron/loop can tell "learned something" from "learn nothing,
retry tomorrow" (Plan §6 Step 8 bullet 1: "bis 'ok': true kommt").
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_BARS_DB_PATH = _REPO_ROOT / "data" / "bars.sqlite"
_DEFAULT_EPIC = "IX.D.DAX.IFMM.IP"
_PROBE_RESOLUTION = "MINUTE"
_PROBE_COUNT = 5


def _eprint(message: str = "") -> None:
    print(message, file=sys.stderr)


def _iso(dt: datetime) -> str:
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--broker", default="ig_demo", help="broker name (default: ig_demo — demo only)")
    parser.add_argument("--epic", default=_DEFAULT_EPIC, help=f"epic to probe (default: {_DEFAULT_EPIC})")
    parser.add_argument(
        "--bars-db", default=str(_DEFAULT_BARS_DB_PATH),
        help=f"BarArchive/SourceBudget SQLite path (default: {_DEFAULT_BARS_DB_PATH})",
    )
    args = parser.parse_args(argv)

    # Lazy imports: `import scripts.probe_allowance` (if ever unit-tested) needs no
    # broker/keyring/network — only main() touches them.
    from broker_wrapper import get_broker
    from data_foundation.budget import IG_QUOTA_V1, SourceBudget

    broker = get_broker(args.broker)
    connect_env = broker.connect()
    if not connect_env.ok:
        _eprint(f"[probe_allowance] broker connect failed for {args.broker!r}: {connect_env.error}")
        print(json.dumps({"ok": False, "epic": args.epic, "error": connect_env.error}, default=str))
        return 1

    _eprint(f"[probe_allowance] {args.broker} get_ohlcv({args.epic!r}, {_PROBE_RESOLUTION!r}, {_PROBE_COUNT}) — 5 points")
    env = broker.get_ohlcv(args.epic, _PROBE_RESOLUTION, _PROBE_COUNT)

    budget = SourceBudget(args.bars_db, IG_QUOTA_V1)
    try:
        if not env.ok:
            _eprint(f"[probe_allowance] FAILED: {env.error}")
            print(json.dumps({"ok": False, "epic": args.epic, "error": env.error}, default=str))
            return 1

        allowance = (env.data or {}).get("allowance") or {}
        budget.record_spend(_PROBE_COUNT, "probe")
        expiry_seconds = allowance.get("allowanceExpiry")
        expiry_iso = (
            _iso(datetime.now(timezone.utc) + timedelta(seconds=int(expiry_seconds)))
            if expiry_seconds is not None else None
        )
        budget.record_allowance(
            allowance.get("totalAllowance"),
            allowance.get("remainingAllowance"),
            expiry_iso,
        )
        _eprint(f"[probe_allowance] ok — allowance={allowance}")
        _eprint(
            "[probe_allowance] next: if remainingAllowance > reserve_points, "
            "reset_universe.py will now proceed (D18)."
        )
        print(json.dumps({"ok": True, "epic": args.epic, "allowance": allowance}))
        return 0
    finally:
        budget.close()


if __name__ == "__main__":
    sys.exit(main())
