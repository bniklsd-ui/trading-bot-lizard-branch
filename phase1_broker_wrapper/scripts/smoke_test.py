#!/usr/bin/env python3
"""End-to-end smoke test against the IG demo account.

This is the canonical "does the wrapper actually work?" check. Run it
after storing demo credentials in the keyring. It exercises every
read endpoint and (with --order) submits a tiny test order on the
demo account.

Usage:
    python scripts/smoke_test.py                   # read-only checks
    python scripts/smoke_test.py --order           # also place a demo order
    python scripts/smoke_test.py --epic IX.D.DAX.IFM.IP

Output is human-readable summary. Failures exit non-zero.
"""

from __future__ import annotations

import argparse
import json
import sys

sys.path.insert(0, ".")

from broker_wrapper import get_broker  # noqa: E402
from broker_wrapper.envelope import Envelope  # noqa: E402


def _show(env: Envelope, *, max_data_len: int = 400) -> bool:
    status = "OK " if env.ok else "ERR"
    print(f"  [{status}] {env.method} ({env.latency_ms}ms)")
    if env.ok:
        data_str = json.dumps(env.data, default=str)
        if len(data_str) > max_data_len:
            data_str = data_str[:max_data_len] + " …(truncated)"
        print(f"    data: {data_str}")
    else:
        print(f"    error: {env.error}")
    return env.ok


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--broker", default="ig_demo")
    p.add_argument("--epic", default=None,
                   help="epic to use for price/info checks (default: discover via search)")
    p.add_argument("--order", action="store_true",
                   help="also submit a tiny demo BUY order, then close it")
    p.add_argument("--size", type=float, default=0.5,
                   help="size for the test order (only used with --order)")
    args = p.parse_args()

    print(f"Smoke test: broker={args.broker}")
    broker = get_broker(args.broker)

    all_ok = True

    print("\n[1] connect")
    all_ok &= _show(broker.connect())

    print("\n[2] get_account")
    all_ok &= _show(broker.get_account())

    print("\n[3] search 'DAX'")
    s_env = broker.search_markets("DAX")
    all_ok &= _show(s_env, max_data_len=600)

    # Pick an epic to test against.
    epic = args.epic
    if not epic and s_env.ok:
        for r in s_env.data.get("results", []):
            if (
                r.get("epic")
                and r.get("type") == "INDICES"
                and r.get("market_status") == "TRADEABLE"
            ):
                epic = r["epic"]
                break
    if not epic:
        print("\n[!] no epic available — skipping price/info checks")
        print("\n[4] disconnect")
        all_ok &= _show(broker.disconnect())
        return 0 if all_ok else 1

    print(f"\n[4] get_market_info ({epic})")
    all_ok &= _show(broker.get_market_info(epic))

    print(f"\n[5] get_price ({epic})")
    all_ok &= _show(broker.get_price(epic))

    print(f"\n[6] get_ohlcv ({epic}, MINUTE_5, count=5)")
    all_ok &= _show(broker.get_ohlcv(epic, "MINUTE_5", 5))

    print("\n[7] get_open_positions")
    all_ok &= _show(broker.get_open_positions())

    print("\n[8] reconcile_positions (empty expected set)")
    all_ok &= _show(broker.reconcile_positions([]))

    if args.order:
        print(f"\n[9] open_position {epic} BUY size={args.size} (DEMO)")
        open_env = broker.open_position(
            epic, "BUY", args.size, "MARKET", currency="EUR",
        )
        all_ok &= _show(open_env)
        if open_env.ok and open_env.data.get("deal_id") and open_env.data.get("status") == "ACCEPTED":
            deal_id = open_env.data["deal_id"]
            print(f"\n[10] close_position {deal_id}")
            all_ok &= _show(broker.close_position(deal_id))

    print("\n[final] disconnect")
    all_ok &= _show(broker.disconnect())

    print("\nresult:", "PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
