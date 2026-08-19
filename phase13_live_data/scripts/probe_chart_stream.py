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
# Phase 13 §6 B0: 11 fields. CHART field list is **unverified** (IG docs
# paywalled, sources are Drittbibliotheken + IG-Labs-Forum). B0 is the
# verification — fields that come back are the real ones.
_CHART_FIELDS = (
    "UTM", "CONS_END", "CONS_TICK_COUNT",
    "BID_OPEN", "BID_HIGH", "BID_LOW", "BID_CLOSE",
    "OFR_OPEN", "OFR_HIGH", "OFR_LOW", "OFR_CLOSE",
)


def _eprint(message: str = "") -> None:
    print(message, file=sys.stderr)


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

    # The actual import path is ``lightstreamer.client`` (the pip package
    # name is ``lightstreamer-client-lib``; the top-level module is
    # ``lightstreamer``, and the client SDK lives in ``lightstreamer.client``).
    # Phase 1's ``phase1_broker_wrapper/broker_wrapper/streaming/ig_lightstreamer.py``
    # imports the same way and is **live-verified**.
    try:
        from lightstreamer.client import (  # noqa: E402
            ClientListener,
            LightstreamerClient,
            Subscription,
            SubscriptionListener,
        )
    except ImportError as exc:  # pragma: no cover — the SDK is a Phase-1 dep
        _eprint(f"[probe_chart_stream] lightstreamer SDK import failed: {exc}")
        print(json.dumps({"ok": False, "epic": args.epic, "error": "sdk_import_failed"}))
        return 1

    cst = connect_env.data.get("cst")
    xst = connect_env.data.get("x_security_token")
    account_id = connect_env.data.get("account_id") or connect_env.data.get("current_account_id")
    ls_url = connect_env.data.get("lightstreamer_endpoint") or "https://apd.marketdatasystems.com"

    # The SDK callback model: ``SubscriptionListener`` is the **single**
    # listener interface for both subscription events (``onSubscription``,
    # ``onSubscriptionError``) and item updates (``onItemUpdate``). One
    # listener class per subscription, with both methods.
    completed = threading.Event()
    sub_error: list[str] = []
    completed_candles: list[dict[str, str]] = []
    state_lock = threading.Lock()

    class _ChartSubListener(SubscriptionListener):
        """Aggregates field updates into one candle per CONS_END==1.

        The SDK delivers partial field dicts per update (LS is a stream,
        not a request/response). We accumulate across updates until
        ``CONS_END == "1"`` arrives, then snapshot one candle.
        """

        def onSubscription(self) -> None:
            _eprint("[probe_chart_stream] SUBOK: candle subscription confirmed")

        def onSubscriptionError(self, code, message) -> None:
            sub_error.append(f"{code}: {message}")
            _eprint(f"[probe_chart_stream] subscription error: {code} {message}")
            completed.set()

        def onItemUpdate(self, update) -> None:
            utm = update.getValue("UTM") or ""
            if not utm:
                return
            with state_lock:
                # Find or create the current-minute bucket by UTM.
                if completed_candles and completed_candles[-1]["UTM"] == utm:
                    bucket = completed_candles[-1]
                else:
                    # New minute — flush the previous if it had CONS_END==1
                    # (in case we never got a second update), then start a new one.
                    bucket = {"UTM": utm}
                    completed_candles.append(bucket)
                for f in _CHART_FIELDS:
                    v = update.getValue(f)
                    if v is not None:
                        bucket[f] = v
                if bucket.get("CONS_END") == "1" and not completed.is_set():
                    completed.set()

    class _ClientL(ClientListener):
        def onStatusChange(self, status: str) -> None:
            _eprint(f"[probe_chart_stream] status: {status}")

        def onServerError(self, code, message) -> None:
            _eprint(f"[probe_chart_stream] server error: {code} {message}")

    _eprint(f"[probe_chart_stream] connecting to {ls_url} as account={account_id!r} ...")
    client = LightstreamerClient(ls_url, "DEFAULT")
    client.connectionDetails.setUser(account_id or "")
    client.connectionDetails.setPassword(f"CST-{cst}|XST-{xst}" if cst and xst else "")
    client.addListener(_ClientL())

    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)

    sub = Subscription("MERGE", [f"CHART:{account_id}:{args.epic}:1MINUTE"], list(_CHART_FIELDS))
    sub.addListener(_ChartSubListener())
    client.connect()
    client.subscribe(sub)
    _eprint(f"[probe_chart_stream] subscribed CHART:{args.epic}:1MINUTE, waiting up to {args.timeout}s ...")

    completed.wait(timeout=args.timeout)
    try:
        client.unsubscribe(sub)
    except Exception:  # noqa: BLE001
        pass
    client.disconnect()

    with state_lock:
        candles_complete = [c for c in completed_candles if c.get("CONS_END") == "1"]

    fields_seen: set[str] = set()
    for c in completed_candles:
        fields_seen.update(k for k in c if k != "UTM")

    payload = {
        "ok": bool(candles_complete),
        "epic": args.epic,
        "candles_received": len(candles_complete),
        "raw_updates": len(completed_candles),
        "sub_error": sub_error[0] if sub_error else None,
        "fields_seen": sorted(fields_seen),
    }

    if sub_error:
        _eprint(f"[probe_chart_stream] subscription error: {sub_error[0]}")
        print(json.dumps(payload))
        return 1
    if not candles_complete:
        _eprint(
            f"[probe_chart_stream] no CONS_END==1 candle in {args.timeout}s "
            f"(received {len(completed_candles)} raw updates). Likely: market closed, or "
            f"CHART not on this account tier. fields_seen={fields_seen}"
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
