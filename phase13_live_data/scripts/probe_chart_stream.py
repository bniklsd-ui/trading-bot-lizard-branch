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

The probe reuses **Phase 1's live-verified** ``IGLightstreamerClient`` (the
PRICE-tick subscription) for the **connect** step (the LS-URL / CST / XST /
account_id all come from the same warm session), and adds a **parallel**
CHART-candle subscription on the same SDK connection. One LS session,
two subscriptions — exactly the architecture B1 commits.

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

    # Phase 1's live-verified broker + LS-client factory. The factory
    # already handles the connect + warm-session flow; we then add a
    # parallel CHART subscription on the same SDK client.
    from broker_wrapper import get_broker  # noqa: E402
    from broker_wrapper.factory import get_stream  # noqa: E402

    _eprint(f"[probe_chart_stream] broker={args.broker!r} epic={args.epic!r} "
            f"target=CHART:{args.epic}:1MINUTE fields={len(_CHART_FIELDS)}")
    broker = get_broker(args.broker)
    connect_env = broker.connect()
    if not connect_env.ok:
        _eprint(f"[probe_chart_stream] broker connect failed: {connect_env.error}")
        print(json.dumps({"ok": False, "epic": args.epic, "error": str(connect_env.error)}))
        return 3

    # Phase 1's ``get_stream`` returns an ``IGLightstreamerClient`` already
    # configured with the same CST/XST/account/endpoint the broker used.
    # The CLIENT instance is what we hook our parallel CHART subscription
    # onto — same SDK connection, same auth, **no double login**.
    try:
        ls_client = get_stream(broker)
    except Exception as exc:  # noqa: BLE001
        _eprint(f"[probe_chart_stream] get_stream failed: {exc}")
        print(json.dumps({"ok": False, "epic": args.epic, "error": "ls_client_build_failed"}))
        return 1

    # Phase 1's IGLightstreamerClient is the live-verified path; its
    # internals already start the SDK connection in ``start()``. We
    # **add** a CHART-candle subscription to the running client (B1-style:
    # same connection, parallel subscription).
    try:
        from lightstreamer.client import Subscription, SubscriptionListener  # noqa: E402
    except ImportError as exc:  # pragma: no cover — Phase-1 dep
        _eprint(f"[probe_chart_stream] lightstreamer SDK import failed: {exc}")
        print(json.dumps({"ok": False, "epic": args.epic, "error": "sdk_import_failed"}))
        return 1

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
                if completed_candles and completed_candles[-1]["UTM"] == utm:
                    bucket = completed_candles[-1]
                else:
                    bucket = {"UTM": utm}
                    completed_candles.append(bucket)
                for f in _CHART_FIELDS:
                    v = update.getValue(f)
                    if v is not None:
                        bucket[f] = v
                if bucket.get("CONS_END") == "1" and not completed.is_set():
                    completed.set()

    ls_client.start()
    account_id = broker._account_id  # same value IGLightstreamerClient used

    sub = Subscription("MERGE", [f"CHART:{account_id}:{args.epic}:1MINUTE"], list(_CHART_FIELDS))
    sub.addListener(_ChartSubListener())
    # B1 is the clean way to add candles; here we drive the SDK directly
    # because the IGLightstreamerClient doesn't expose ``subscribe_candles``
    # in *all* versions of the file (B1 was committed in this Phase).
    # The IGLightstreamerClient carries the same SDK client instance as the
    # PRICE subscription, so we reach in to attach the CHART subscription.
    _ls_sdk_client = ls_client._client  # noqa: SLF001 — same SDK instance
    _ls_sdk_client.subscribe(sub)
    _eprint(f"[probe_chart_stream] subscribed CHART:{args.epic}:1MINUTE, waiting up to {args.timeout}s ...")

    completed.wait(timeout=args.timeout)
    try:
        _ls_sdk_client.unsubscribe(sub)
    except Exception:  # noqa: BLE001
        pass
    ls_client.stop()

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
