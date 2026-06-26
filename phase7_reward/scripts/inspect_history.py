#!/usr/bin/env python3
"""Read-only IG trade-history inspector — diagnose Phase-7 P&L resolution.

Dumps the raw ``broker.get_trade_history(days)`` transactions (especially the real
``size`` field — IG signs it) and the current OPEN ``trade_outcomes`` rows, so the
operator can see (a) whether a just-closed deal has reached IG's transaction ledger
yet (history lag) and (b) whether the resolver's magnitude-based size match lines up
with the live record. **Pure read** — no order, no close, no DB write.

This exists because the first reward live run fail-closed on ``PnLUnavailable``
("no usable history row ... size=19.8"), and the two candidate causes — IG signing the
SELL size negative vs. transaction-ledger lag — can only be told apart by looking at
the live record. ``ig_adapter._parse_transaction`` already coerces ``size`` to a float,
so a signed IG size surfaces here as a **negative float**.

Output discipline: human-readable table → **stderr**; the machine-readable JSON
(transactions + open trades) → **stdout**.

Usage:
    python scripts/inspect_history.py
    python scripts/inspect_history.py --broker ig_demo --days 3
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Make the project dir importable so the (non-installed) `scripts` package resolves.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent  # phase7_reward/
sys.path.insert(0, str(_PROJECT_ROOT))

log = logging.getLogger("phase7.inspect_history")

# Same data path the wiring resolves (scripts/ -> phase7_reward/ -> repo root).
_DB_PATH = _PROJECT_ROOT.parent / "data" / "trading_bot.sqlite"


def _eprint(message: str = "") -> None:
    print(message, file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--broker", default="ig_demo", help="broker id (default: ig_demo)")
    parser.add_argument("--days", type=int, default=1, help="history window in days (default: 1)")
    parser.add_argument("--verbose", action="store_true", help="DEBUG logging")
    args = parser.parse_args(argv)

    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    from broker_wrapper import get_broker

    _eprint(f"[inspect] connecting broker={args.broker} (read-only) …")
    broker = get_broker(args.broker)
    connect_env = broker.connect()
    if not getattr(connect_env, "ok", False):
        _eprint(f"[inspect] broker connect failed: {getattr(connect_env, 'error', None)}")
        return 1

    # --- trade history (the resolver's only broker read) ---------------------
    _eprint(f"[inspect] fetching get_trade_history(days={args.days}) …")
    env = broker.get_trade_history(days=args.days)
    transactions: list[dict[str, Any]] = []
    if not getattr(env, "ok", False):
        _eprint(f"[inspect] get_trade_history NOT ok: {getattr(env, 'error', None)}")
    else:
        transactions = list((getattr(env, "data", None) or {}).get("transactions", []))

    _eprint(f"[inspect] {len(transactions)} transaction(s) in the window:")
    for tx in transactions:
        _eprint(f"  size={tx.get('size')!r:>10}  open={tx.get('open_level')!r:>10}  "
                f"close={tx.get('close_level')!r:>10}  pnl={tx.get('profit_loss')!r:>10}  "
                f"epic={tx.get('epic')!r}  close_date={tx.get('close_date')!r}")
    if any(isinstance(tx.get("size"), (int, float)) and tx["size"] < 0 for tx in transactions):
        _eprint("[inspect] NOTE: at least one transaction `size` is negative — confirms IG "
                "signs the history size; the resolver's magnitude (abs) match handles it.")

    # --- open trades the resolver still owes a close -------------------------
    from persistence import Database

    db = Database(str(_DB_PATH))
    try:
        open_trades = db.get_open_trades()
    finally:
        db.close()

    _eprint(f"[inspect] {len(open_trades)} OPEN trade_outcomes row(s):")
    for row in open_trades:
        _eprint(f"  deal_id={row.get('deal_id')!r}  dir={row.get('direction')!r}  "
                f"size={row.get('size')!r}  open_level={row.get('open_level')!r}  "
                f"initial_risk={row.get('initial_risk')!r}")

    print(json.dumps(
        {"transactions": transactions, "open_trades": open_trades}, indent=2, default=str
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
