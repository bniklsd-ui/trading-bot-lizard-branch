#!/usr/bin/env python3
"""Live validation for IGLightstreamerClient against IG demo.

Proves that the Lightstreamer streaming connection delivers PriceTick callbacks
end-to-end via the official Lightstreamer SDK. Tracks three connection milestones
independently so a partial failure (e.g. market closed) is clearly distinguished
from a real one.

Usage:
    python scripts/test_lightstreamer.py
    python scripts/test_lightstreamer.py --epic IX.D.DAX.IFMM.IP --ticks 3 --timeout 30
    python scripts/test_lightstreamer.py --debug          # full TLCP trace

Exit codes:
    0  PASS    — required number of ticks received
    1  FAIL    — auth/connection error, or no CONOK within timeout
    2  PARTIAL — CONOK + SUBOK confirmed but no ticks (market likely closed)

Milestones tracked:
    CONOK   — LS session accepted by server (auth OK, stream open)
    SUBOK   — subscription confirmed (epic valid, server will send updates)
    tick    — first PriceTick callback fired (market is live and sending data)

Market hours for DAX: Mon–Fri 08:00–22:30 CET. Outside those hours you will
typically see CONOK + SUBOK but no U-line ticks (exit code 2, not 1).
"""

from __future__ import annotations

import argparse
import logging
import sys
import threading
import time

sys.path.insert(0, ".")

from broker_wrapper import get_broker
from broker_wrapper.exceptions import CredentialNotFoundError


# ---------- milestone capture ------------------------------------------------

class _MilestoneHandler(logging.Handler):
    """Intercepts INFO log records from ig_lightstreamer to track CONOK/SUBOK."""

    def __init__(self) -> None:
        super().__init__()
        self.conok = threading.Event()
        self.subok = threading.Event()

    def emit(self, record: logging.LogRecord) -> None:
        msg = record.getMessage()
        if "CONOK" in msg:
            self.conok.set()
        if "SUBOK" in msg:
            self.subok.set()


# ---------- main -------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(
        description="Lightstreamer live validation against IG demo."
    )
    p.add_argument(
        "--epic", default="IX.D.DAX.IFMM.IP",
        help="IG epic to subscribe to (default: IX.D.DAX.IFMM.IP)",
    )
    p.add_argument(
        "--ticks", type=int, default=3,
        help="number of PriceTick callbacks to wait for (default: 3)",
    )
    p.add_argument(
        "--timeout", type=int, default=30,
        help="seconds to wait for ticks before declaring FAIL/PARTIAL (default: 30)",
    )
    p.add_argument(
        "--debug", action="store_true",
        help="enable DEBUG logging — prints every TLCP line received",
    )
    args = p.parse_args()

    # Configure logging before anything else.
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )

    # Capture CONOK/SUBOK milestones from the streaming client's log output.
    milestones = _MilestoneHandler()
    milestones.setLevel(logging.INFO)
    logging.getLogger("broker_wrapper.streaming.ig_lightstreamer").addHandler(milestones)

    print(
        f"Lightstreamer live test  epic={args.epic}  "
        f"want={args.ticks} ticks  timeout={args.timeout}s"
    )

    # --- connect via REST ---
    try:
        broker = get_broker("ig_demo")
    except CredentialNotFoundError as e:
        print(f"\n[ERR] credentials: {e}")
        return 1

    print("\n[1] connect (REST)")
    env = broker.connect()
    if not env.ok:
        print(f"  [ERR] {env.error['code']}: {env.error['message']}")
        return 1
    print(f"  [OK ] account={env.data['account_id']}")

    ls_endpoint = broker.lightstreamer_endpoint  # type: ignore[attr-defined]
    print(f"  [OK ] lightstreamer_endpoint={ls_endpoint!r}")

    if not ls_endpoint:
        print(
            "\n  [ERR] No lightstreamerEndpoint returned by POST /session.\n"
            "  Check ig_adapter.py → _login() → body_meta.get('lightstreamerEndpoint')"
        )
        broker.disconnect()
        return 1

    # --- create stream client ---
    print("\n[2] create IGLightstreamerClient")
    try:
        from broker_wrapper.factory import get_stream  # type: ignore[attr-defined]
        stream = get_stream(broker)
    except Exception as e:
        print(f"  [ERR] get_stream() failed: {e}")
        broker.disconnect()
        return 1
    print("  [OK ] stream client created")

    # --- subscribe ---
    received_ticks: list = []
    first_tick_event = threading.Event()

    def on_tick(tick) -> None:
        received_ticks.append(tick)
        elapsed = time.monotonic() - start_t
        print(
            f"  [TICK #{len(received_ticks):02d}] "
            f"bid={tick.bid:.1f}  ask={tick.ask:.1f}  "
            f"ts={tick.timestamp}  (+{elapsed:.1f}s)"
        )
        if not first_tick_event.is_set():
            first_tick_event.set()

    print(f"\n[3] subscribe to {args.epic}")
    stream.subscribe(args.epic, on_tick)

    # --- start stream ---
    print(f"\n[4] start stream (waiting up to {args.timeout}s for {args.ticks} ticks)")
    print("    Milestones: CONOK=session active  SUBOK=subscription confirmed  tick=data flowing")
    start_t = time.monotonic()

    try:
        stream.start()
    except Exception as e:
        print(f"\n  [ERR] stream.start() raised: {e}")
        broker.disconnect()
        return 1

    # Wait for CONOK (session must be established within 15s)
    conok_timeout = min(15, args.timeout)
    conok_ok = milestones.conok.wait(timeout=conok_timeout)
    if conok_ok:
        print(f"  [CONOK ] session established  (+{time.monotonic()-start_t:.1f}s)")
    else:
        elapsed = time.monotonic() - start_t
        print(f"\n  [ERR] no CONOK within {conok_timeout}s — session creation failed")
        print(
            "  Debug hints:"
            "\n  - Run with --debug to see full TLCP trace"
            "\n  - Check that lightstreamer_endpoint is correct (printed above)"
            "\n  - Verify IG demo credentials are valid (run smoke_test.py first)"
        )
        stream.stop()
        broker.disconnect()
        return 1

    # Wait for SUBOK (subscription confirmed within 10s of CONOK)
    subok_ok = milestones.subok.wait(timeout=10)
    if subok_ok:
        print(f"  [SUBOK ] subscription confirmed  (+{time.monotonic()-start_t:.1f}s)")
    else:
        print(f"  [WARN ] no SUBOK yet — subscription may still be pending")

    # Wait for ticks up to the user's timeout
    remaining = args.timeout - (time.monotonic() - start_t)
    if remaining > 0:
        done = threading.Event()
        def _watch() -> None:
            while len(received_ticks) < args.ticks and not done.wait(0.1):
                pass
            done.set()
        watcher = threading.Thread(target=_watch, daemon=True)
        watcher.start()
        # Wait for enough ticks or timeout
        deadline = start_t + args.timeout
        while len(received_ticks) < args.ticks and time.monotonic() < deadline:
            time.sleep(0.05)
        done.set()

    elapsed_total = time.monotonic() - start_t

    # --- stop & disconnect ---
    print(f"\n[5] stop stream + disconnect")
    stream.stop()
    broker.disconnect()
    print(f"  [OK ] stopped  (total elapsed: {elapsed_total:.1f}s)")

    # --- verdict ---
    print()
    if len(received_ticks) >= args.ticks:
        print(
            f"result: PASS  "
            f"({len(received_ticks)} ticks in {elapsed_total:.1f}s)"
        )
        return 0

    if milestones.conok.is_set() and milestones.subok.is_set():
        print(
            f"result: PARTIAL  "
            f"(CONOK+SUBOK confirmed, {len(received_ticks)}/{args.ticks} ticks in {elapsed_total:.1f}s)"
        )
        print(
            "\n  DAX trades Mon–Fri 08:00–22:30 CET. Outside those hours the server\n"
            "  accepts the subscription but sends no U-line tick data. PARTIAL is a\n"
            "  PASS for the connection layer — run again during market hours for ticks."
        )
        return 2

    print(
        f"result: FAIL  "
        f"(CONOK={milestones.conok.is_set()}  "
        f"SUBOK={milestones.subok.is_set()}  "
        f"ticks={len(received_ticks)}/{args.ticks})"
    )
    if not milestones.conok.is_set():
        print(
            "\n  No CONOK received — the LS session was not established. Run with\n"
            "  --debug to see the raw TLCP exchange. Possible causes:\n"
            "  - Wrong lightstreamer_endpoint URL format\n"
            "  - IG session tokens expired (reconnect via smoke_test.py)\n"
            "  - Network / firewall issue reaching the streaming server"
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
