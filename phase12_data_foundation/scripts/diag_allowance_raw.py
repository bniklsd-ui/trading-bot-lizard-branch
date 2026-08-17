#!/usr/bin/env python3
"""Diagnostic (one-off) — dump IG's raw ``/prices`` response body, unparsed.

``probe_allowance.py``'s live run (2026-08-17, market open) came back with
``allowance={}`` despite ``ALLOWANCE_INCIDENT_2026-08-08.md``'s (untested) assumption that
IG includes an ``allowance`` object in every successful ``/prices`` response. This bypasses
``IGAdapter.get_ohlcv``'s parsing (``body.get("allowance", {})``, Step 3 confirmed that part
correct) and prints the **exact** top-level keys and the full raw body IG actually sent —
so we see whether ``allowance`` is missing entirely, nested somewhere else, or named
differently for this account tier, instead of guessing again.

Same precedent as Step 0a (``phase12_data_foundation/CLAUDE.md`` Session-Block 2026-08-11):
a raw dump against ``broker._request()`` when a parsed-envelope assumption needed
live-checking. Live, network, keyring — Nikinger-run.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_EPIC = "IX.D.DAX.IFMM.IP"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--broker", default="ig_demo")
    parser.add_argument("--epic", default=_DEFAULT_EPIC)
    parser.add_argument("--resolution", default="MINUTE")
    parser.add_argument("--count", type=int, default=5)
    args = parser.parse_args(argv)

    from broker_wrapper import get_broker

    broker = get_broker(args.broker)
    connect_env = broker.connect()
    if not connect_env.ok:
        print(f"connect failed: {connect_env.error}", file=sys.stderr)
        return 1

    body = broker._request(  # noqa: SLF001 — deliberate raw-dump diagnostic, not production code
        "GET", f"/prices/{args.epic}", version="3", auth=True,
        params={"resolution": args.resolution, "max": args.count, "pageSize": args.count},
    )
    print(f"top-level keys: {sorted(body.keys())}", file=sys.stderr)
    print(json.dumps(body, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
