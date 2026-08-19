#!/usr/bin/env python3
"""Block B0 — gating live check: does IG deliver CHART:{epic}:1MINUTE on this account?

The Phase-13 plan hinges on S1 = Lightstreamer `CHART:`-kerzen as the **Schwanz**
("now", from the same price series the entry was taken on). The plan is
realistically two-headed (Plan §6 B0 verbatim):

- **YES (CHART delivers):** B1/B2/B3 build the live stream on this signal.
- **NO (`onSubscriptionError` or no updates after a reasonable window):**
  fall back to the existing `PRICE:`-subscription, aggregate ticks into
  1-min-OHLC, write-through with `source='ls'` and a `tick_count` field
  (per-bar tick density is what makes this honest — a single tick in a
  minute is *not* a candle).

Both branches are pre-planned; the probe decides which. The wider question
``setDataAdapter`` ("Pricing" vs other) is **unverified** — IG's docs are
paywalled, and the field list (`UTM`, `CONS_END`, `CONS_TICK_COUNT`,
`BID_*`/`OFR_*`) is from third-party sources (Drittbibliotheken + IG-Labs-Forum).
This probe is the only way to find out on this account.

Usage:
    python phase13_live_data/scripts/probe_chart_stream.py
    python phase13_live_data/scripts/probe_chart_stream.py --epic IX.D.DAX.IFMM.IP
    python phase13_live_data/scripts/probe_chart_stream.py --candles 1 --timeout 30

Exit codes:
    0  YES    — at least one CONS_END==1 candle received (kostenloser Stream)
    1  NO     — connection or subscription error
    2  PARTIAL— connection + subscription OK, but no CONS_END==1 candle in the
                window (most likely: market closed, or CHART not available on
                this account tier)
    3  AUTH   — keyring/broker connect failed (operator should re-seed creds)

Output discipline (repo convention): human narrative -> stderr, machine-
readable JSON -> stdout. Cost: **0** (Lightstreamer-Kontingent, nicht das
10000-Punkte/Woche-IG-REST-Limit).

Live, network, keyring-touching (real IG demo session) — not run in tests,
same "operator-run" convention as ``phase8_scheduler/scripts/wiring.py``.
Nikinger-run per the ``feedback_live_testing`` memory: prepped here, executed
on explicit go-ahead.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_EPIC = "IX.D.DAX.IFMM.IP"
_CHART_FIELDS = (
    "UTM", "CONS_END", "CONS_TICK_COUNT",
    "BID_OPEN", "BID_HIGH", "BID_LOW", "BID_CLOSE",
    "OFR_OPEN", "OFR_HIGH", "OFR_LOW", "OFR_CLOSE",
)


def _eprint(message: str = "") -> None:
    print(message, file=sys.stderr)


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + f"{datetime.now().microsecond // 1000:03d}Z"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--broker", default="ig_demo", help="broker name (default: ig_demo)")
    parser.add_argument("--epic", default=_DEFAULT_EPIC, help=f"epic to probe (default: {_DEFAULT_EPIC})")
    parser.add_argument(
        "--candles", type=int, default=1,
        help="number of CONS_END==1 candles to wait for (default: 1)",
    )
    parser.add_argument(
        "--timeout", type=int, default=30,
        help="seconds to wait before declaring PARTIAL (default: 30)",
    )
    parser.add_argument("--debug", action="store_true", help="full TLCP trace")
    args = parser.parse_args(argv)

    sys.path.insert(0, str(_REPO_ROOT))

    from broker_wrapper import get_broker  # noqa: E402

    _eprint(f"[probe_chart_stream] broker={args.broker!r} epic={args.epic!r} "
            f"target=CHART:{args.epic}:1MINUTE fields={len(_CHART_FIELDS)}")
    broker = get_broker(args.broker)
    connect_env = broker.connect()
    if not connect_env.ok:
        _eprint(f"[probe_chart_stream] broker connect failed: {connect_env.error}")
        print(json.dumps({"ok": False, "epic": args.epic, "error": str(connect_env.error)}))
        return 3

    # We do **not** use the live-tested `IGLightstreamerClient` directly — that
    # class subscribes `PRICE:` (U-line ticks). The CHART subscription is
    # structurally different (server-side aggregated candles, not ticks),
    # so we drive the official `lightstreamer-client-lib` once for this probe
    # only. B1 will refactor `IGLightstreamerClient` to own both subscriptions.
    try:
        from lightstreamer_client_lib.client import LightstreamerClient  # noqa: E402
    except ImportError as exc:  # pragma: no cover — the SDK is a Phase-1 dep
        _eprint(f"[probe_chart_stream] lightstreamer-client-lib missing: {exc}")
        print(json.dumps({"ok": False, "epic": args.epic, "error": "sdk_missing"}))
        return 1

    received: list[dict[str, str]] = []
    completed = threading.Event()
    sub_error: list[str] = []
    lock = threading.Lock()

    def on_item_update(_update: dict) -> None:  # not used
        pass

    def _on_update(field_name: str, field_value: str) -> None:
        # ItemListener callback. The SDK invokes this once per field per update.
        # We accumulate fields until CONS_END==1 ("candle complete"), then
        # snapshot.
        with lock:
            if not received or received[-1].get("UTM") != field_name and field_name == "UTM":
                received.append({"UTM": field_value})
                current = received[-1]
            else:
                current = received[-1]
            current[field_name] = field_value
            if current.get("CONS_END") == "1" and not completed.is_set():
                completed.set()

    item_listener = type(
        "_ItemListener",
        (),
        {
            "onUpdate": lambda self, item, update: _on_update(item, update),
            "onItemName": lambda self, *args, **kwargs: None,
        },
    )()

    sub_listener = type(
        "_SubListener",
        (),
        {
            "onSubscribe": lambda self, *args, **kwargs: None,
            "onSubscription": lambda self, *args, **kwargs: None,
            "onSubscriptionError": lambda self, code, message: (
                sub_error.append(f"{code}: {message}") or completed.set()
            ),
            "onUnsubscription": lambda self, *args, **kwargs: None,
            "onEnd": lambda self, *args, **kwargs: None,
        },
    )()

    cst = connect_env.data.get("cst")
    xst = connect_env.data.get("x_security_token")
    account_id = connect_env.data.get("account_id") or connect_env.data.get("current_account_id")
    ls_url = connect_env.data.get("lightstreamer_endpoint") or "https://apd.marketdatasystems.com"

    client = LightstreamerClient(ls_url, f"DEFAULT_{account_id or 'CLIENT'}")
    client.connectionDetails.setUser(cst)
    client.connectionDetails.setPassword(xst)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    _eprint(f"[probe_chart_stream] connecting to {ls_url} ...")
    client.connect()
    # Register a minimal Subscription on the CHART item, with the full field
    # list. setDataAdapter is the **one** unverified part — we do NOT set it
    # (the SDK default is usually correct; we'll see from the response).
    from lightstreamer_client_lib.subscribe import Subscription  # noqa: E402
    from lightstreamer_client_lib.constants import SubscriptionMode  # noqa: E402

    sub = Subscription(
        SubscriptionMode.MERGE,
        f"CHART:{args.epic}:1MINUTE",
        list(_CHART_FIELDS),
    )
    sub.addListener(item_listener)
    sub.addListener(sub_listener)
    client.subscribe(sub)
    _eprint(f"[probe_chart_stream] subscribed CHART:{args.epic}:1MINUTE, waiting up to {args.timeout}s ...")

    completed.wait(timeout=args.timeout)
    client.disconnect()

    with lock:
        candles_complete = [r for r in received if r.get("CONS_END") == "1"]

    payload = {
        "ok": bool(candles_complete),
        "epic": args.epic,
        "candles_received": len(candles_complete),
        "raw_updates": len(received),
        "sub_error": sub_error[0] if sub_error else None,
        "fields_seen": sorted({k for r in received for k in r}),
    }

    if sub_error:
        _eprint(f"[probe_chart_stream] subscription error: {sub_error[0]}")
        print(json.dumps(payload))
        return 1
    if not candles_complete:
        _eprint(
            f"[probe_chart_stream] no CONS_END==1 candle in {args.timeout}s "
            f"(received {len(received)} raw updates). Likely: market closed, or "
            f"CHART not on this account tier."
        )
        print(json.dumps(payload))
        return 2
    _eprint(f"[probe_chart_stream] YES — received {len(candles_complete)} completed candle(s)")
    for c in candles_complete[:3]:
        _eprint(
            f"  {c.get('UTM')} CONS_END={c.get('CONS_END')} "
            f"tick_count={c.get('CONS_TICK_COUNT')} "
            f"BID_CLOSE={c.get('BID_CLOSE')} OFR_CLOSE={c.get('OFR_CLOSE')}"
        )
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())
