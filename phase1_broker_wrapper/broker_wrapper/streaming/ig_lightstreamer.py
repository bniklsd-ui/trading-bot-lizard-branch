"""IG Lightstreamer client — production streaming via the official Lightstreamer SDK.

Wraps `lightstreamer-client-lib` (`from lightstreamer.client import ...`). The SDK
negotiates the transport (WebSocket with HTTP fallback), the TLCP protocol version,
reconnection, LOOP rebind, MERGE-mode field caching and keepalive internally — so this
module is a thin adapter from the SDK's listener callbacks to our `PriceTick` contract.

History: a hand-rolled raw-TLCP-over-HTTP implementation lived here through v9. IG's
server rejected its `create_session.txt` with an opaque HTTP 400 regardless of protocol
version, so it was replaced by the official SDK (see lightstreamer_integration_notes.md,
v10). The legacy `MARKET:`/`L1:` feed was decommissioned by IG on 8 May 2026; the
replacement is `PRICE:{account_id}:{epic}` via the `Pricing` data adapter.

Authentication (IG-specific):
    LS_user     = account_id (e.g. "Z6BEGX")
    LS_password = "CST-{cst}|XST-{security_token}"

Subscription:
    item   = PRICE:{account_id}:{epic}
    fields = BIDPRICE1 ASKPRICE1 TIMESTAMP   (TIMESTAMP = Unix ms)
    mode   = MERGE   ·   data adapter = Pricing
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone

from lightstreamer.client import (
    ClientListener,
    LightstreamerClient,
    Subscription,
    SubscriptionListener,
)

from broker_wrapper.streaming.base import (
    CandleCallback,
    ChartCandle,
    PriceCallback,
    PriceTick,
    StreamClient,
)

log = logging.getLogger(__name__)

_FIELDS = ["BIDPRICE1", "ASKPRICE1", "TIMESTAMP"]

# Phase 13 §6 B1: CHART:{epic}:{scale} server-side aggregated candles. Field
# list is **unverified** (IG docs paywalled; sources are Drittbibliotheken +
# IG-Labs-Forum posts) — the B0 probe is the only way to know on this account.
# What we know: UTM is Unix-ms (candle OPEN time, not close); CONS_END==1
# marks the candle as final; CONS_TICK_COUNT is the per-bar tick density
# (a candle with 1 tick is a dressed-up tick, not an OHLC).
_CHART_FIELDS = [
    "UTM", "CONS_END", "CONS_TICK_COUNT",
    "BID_OPEN", "BID_HIGH", "BID_LOW", "BID_CLOSE",
    "OFR_OPEN", "OFR_HIGH", "OFR_LOW", "OFR_CLOSE",
]


def _utm_to_iso(utm: str) -> str:
    """Convert an IG Unix-ms timestamp string to an ISO 8601 UTC string."""
    try:
        ts = datetime.fromtimestamp(int(utm) / 1000.0, tz=timezone.utc)
        ms = ts.microsecond // 1000
        return ts.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ms:03d}Z"
    except (ValueError, TypeError, OSError):
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


class _ClientListener(ClientListener):
    """Logs SDK connection-status transitions (CONOK milestone on connect)."""

    def onStatusChange(self, status: str) -> None:
        if status.startswith("CONNECTED:"):
            # "CONOK" keeps scripts/test_lightstreamer.py's milestone scraper working.
            log.info("Lightstreamer CONOK: connected (%s)", status)
        else:
            log.debug("Lightstreamer status: %s", status)

    def onServerError(self, code, message) -> None:
        log.error("Lightstreamer server error %s: %s", code, message)


class _PriceListener(SubscriptionListener):
    """Maps SDK item updates for one epic onto a PriceTick callback."""

    def __init__(self, epic: str, callback: PriceCallback) -> None:
        self._epic = epic
        self._callback = callback

    def onSubscription(self) -> None:
        # "SUBOK" keeps scripts/test_lightstreamer.py's milestone scraper working.
        log.info("Lightstreamer SUBOK: subscription confirmed for %s", self._epic)

    def onSubscriptionError(self, code, message) -> None:
        log.error("Lightstreamer subscription error for %s — %s: %s",
                  self._epic, code, message)

    def onItemUpdate(self, update) -> None:
        bid_str = update.getValue("BIDPRICE1")
        ask_str = update.getValue("ASKPRICE1")
        if not bid_str or not ask_str:
            return
        try:
            bid, ask = float(bid_str), float(ask_str)
        except (ValueError, TypeError):
            log.warning("non-numeric price for %s: bid=%r ask=%r",
                        self._epic, bid_str, ask_str)
            return
        tick = PriceTick(
            epic=self._epic, bid=bid, ask=ask,
            timestamp=_utm_to_iso(update.getValue("TIMESTAMP") or ""),
        )
        try:
            self._callback(tick)
        except Exception:
            log.exception("callback raised for epic %s", self._epic)


class _CandleListener(SubscriptionListener):
    """Maps SDK item updates for one CHART-candle subscription onto a ChartCandle.

    Phase 13 §6 B1: a single SDK update delivers a **partial** field dict for
    the candle (LS is a stream, not a request/response). We accumulate fields
    across updates until ``CONS_END == "1"`` arrives, then emit exactly one
    ``ChartCandle`` with ``complete=True``.

    Mid-Rechnung (L7): OHLC values are bid/ofr **mid** = (BID + OFR) / 2 per
    field. The archive already stores IG-REST bars in mid (L7-Verweis) — a
    LS-bar in bid neben einer REST-bar in mid wäre eine stille
    Preisreihen-Mischung.

    Fail-soft: a missing/non-numeric field logs and skips the candle
    (one missing field at 09:00 must not crash the recorder for the rest of
    the day). The recorder is responsible for the decision; this listener
    only **refuses to write garbage**.
    """

    def __init__(self, epic: str, callback: CandleCallback) -> None:
        self._epic = epic
        self._callback = callback
        # Current candle accumulator (keyed by UTM == open-time).
        self._current_utm: str | None = None
        self._current_fields: dict[str, str] = {}

    def onSubscription(self) -> None:
        log.info("Lightstreamer SUBOK: candle subscription confirmed for %s", self._epic)

    def onSubscriptionError(self, code, message) -> None:
        log.error("Lightstreamer candle subscription error for %s — %s: %s",
                  self._epic, code, message)

    def onItemUpdate(self, update) -> None:
        utm = update.getValue("UTM") or ""
        if not utm:
            log.debug("ignoring candle update for %s without UTM", self._epic)
            return
        # If this update starts a new candle, flush the previous one if it
        # was complete (a missed CONS_END==1 in the previous minute is
        # unrecoverable — we drop the incomplete one rather than emit a
        # half-formed candle; the recorder stays correct).
        if self._current_utm and utm != self._current_utm:
            self._current_fields.clear()
            self._current_utm = None
        self._current_utm = utm
        # Accumulate the fields this update brought.
        for f in _CHART_FIELDS:
            v = update.getValue(f)
            if v is not None:
                self._current_fields[f] = v
        # CONS_END==1 is the server's "this minute is final" signal.
        if self._current_fields.get("CONS_END") == "1":
            self._emit_if_complete()

    def _emit_if_complete(self) -> None:
        fields = self._current_fields
        try:
            bid_o = float(fields["BID_OPEN"])
            bid_h = float(fields["BID_HIGH"])
            bid_l = float(fields["BID_LOW"])
            bid_c = float(fields["BID_CLOSE"])
            ofr_o = float(fields["OFR_OPEN"])
            ofr_h = float(fields["OFR_HIGH"])
            ofr_l = float(fields["OFR_LOW"])
            ofr_c = float(fields["OFR_CLOSE"])
        except (KeyError, ValueError, TypeError) as exc:
            log.warning("incomplete candle for %s at %s: %s",
                        self._epic, self._current_utm, exc)
            return
        candle = ChartCandle(
            epic=self._epic,
            ts_utc=_utm_to_iso(self._current_utm),
            open=(bid_o + ofr_o) / 2.0,
            high=(bid_h + ofr_h) / 2.0,
            low=(bid_l + ofr_l) / 2.0,
            close=(bid_c + ofr_c) / 2.0,
            tick_count=int(fields["CONS_TICK_COUNT"]) if fields.get("CONS_TICK_COUNT") else None,
            complete=True,
        )
        try:
            self._callback(candle)
        except Exception:
            log.exception("candle callback raised for %s", self._epic)
        # Reset so a re-issued CONS_END==1 (network glitch) doesn't double-emit.
        self._current_fields.clear()
        self._current_utm = None


class IGLightstreamerClient(StreamClient):
    """IG real-time price feed backed by the official Lightstreamer SDK.

    Constructor signature is fixed; see factory.get_stream() for the canonical
    way to instantiate from a connected IGAdapter.

    Phase 13 §6 B1: in addition to the live-tested PRICE-tick subscription,
    this class now owns a parallel CHART-candle subscription. Both share
    one SDK connection, one threading lock, one lifecycle. Candle
    subscription is IG-specific (not in the StreamClient ABC) — duck-typed
    by consumers that need it (``subscribe_candles``).
    """

    def __init__(
        self,
        *,
        cst: str,
        security_token: str,
        account_id: str,
        lightstreamer_endpoint: str,
    ) -> None:
        self._cst = cst
        self._security_token = security_token
        self._account_id = account_id
        self._endpoint = lightstreamer_endpoint.rstrip("/")

        self._lock = threading.Lock()
        self._running = False
        self._client: LightstreamerClient | None = None
        self._subscriptions: dict[str, PriceCallback] = {}
        self._subs: dict[str, Subscription] = {}
        # Phase 13 §6 B1: parallel candle-subscription bookkeeping. Same
        # epic can have a price-tick sub and a candle sub at the same time.
        self._candle_subs: dict[str, CandleCallback] = {}
        self._chart_subs: dict[str, Subscription] = {}

    # ---------- StreamClient interface ----------

    def start(self) -> None:
        with self._lock:
            if self._running:
                return
            client = LightstreamerClient(self._endpoint, "DEFAULT")
            client.connectionDetails.setUser(self._account_id)
            client.connectionDetails.setPassword(
                f"CST-{self._cst}|XST-{self._security_token}"
            )
            client.addListener(_ClientListener())
            self._client = client
            self._running = True
            price_epics = list(self._subscriptions.keys())
            chart_epics = list(self._candle_subs.keys())
        client.connect()
        for epic in price_epics:
            self._do_subscribe(epic)
        for epic in chart_epics:
            self._do_subscribe_chart(epic)

    def stop(self) -> None:
        with self._lock:
            if not self._running:
                return
            client = self._client
            subs = list(self._subs.values()) + list(self._chart_subs.values())
            self._subs.clear()
            self._chart_subs.clear()
            self._running = False
            self._client = None
        if client is not None:
            for sub in subs:
                try:
                    client.unsubscribe(sub)
                except Exception:
                    log.debug("unsubscribe during stop failed", exc_info=True)
            client.disconnect()

    def subscribe(self, epic: str, callback: PriceCallback) -> None:
        with self._lock:
            self._subscriptions[epic] = callback
            active = self._running and self._client is not None
        if active:
            self._do_subscribe(epic)

    def unsubscribe(self, epic: str) -> None:
        with self._lock:
            self._subscriptions.pop(epic, None)
            client = self._client
            sub = self._subs.pop(epic, None)
        if client is not None and sub is not None:
            try:
                client.unsubscribe(sub)
            except Exception:
                log.debug("unsubscribe for %s failed", epic, exc_info=True)

    @property
    def is_running(self) -> bool:
        return self._running

    # ---------- candle (Phase 13 §6 B1) ----------

    def subscribe_candles(
        self, epic: str, callback: CandleCallback, *, scale: str = "1MINUTE"
    ) -> None:
        """Register a callback for 1-min CHART candles. The callback fires
        exactly once per completed candle (CONS_END==1).

        ``scale`` is the IG candle scale (``"1MINUTE"`` / ``"5MINUTE"`` /
        ``"30MINUTE"`` / ``"1HOUR"`` / etc.). Phase 13 only uses ``"1MINUTE"``;
        the parameter is here so B2 (the recorder) can switch to
        ``"5MINUTE"`` for the divergence sampler without touching this class.
        """
        with self._lock:
            self._candle_subs[epic] = callback
            active = self._running and self._client is not None
        if active:
            self._do_subscribe_chart(epic, scale=scale)

    def unsubscribe_candles(self, epic: str) -> None:
        with self._lock:
            self._candle_subs.pop(epic, None)
            client = self._client
            sub = self._chart_subs.pop(epic, None)
        if client is not None and sub is not None:
            try:
                client.unsubscribe(sub)
            except Exception:
                log.debug("unsubscribe_candles for %s failed", epic, exc_info=True)

    # ---------- internals ----------

    def _do_subscribe(self, epic: str) -> None:
        """Register one PRICE subscription with the SDK. Idempotent per epic."""
        with self._lock:
            if epic in self._subs:
                return
            client = self._client
            callback = self._subscriptions.get(epic)
            if client is None or callback is None:
                return
            sub = Subscription("MERGE", [f"PRICE:{self._account_id}:{epic}"], _FIELDS)
            sub.setDataAdapter("Pricing")
            sub.addListener(_PriceListener(epic, callback))
            self._subs[epic] = sub
        client.subscribe(sub)

    def _do_subscribe_chart(self, epic: str, *, scale: str = "1MINUTE") -> None:
        """Register one CHART subscription with the SDK. Idempotent per epic.

        Note: we do **not** call ``setDataAdapter`` here — the SDK's default
        is correct for CHART (verified in the B0 probe; if a future IG
        change breaks this, the failure is loud in the probe, not silent
        in production)."""
        with self._lock:
            if epic in self._chart_subs:
                return
            client = self._client
            callback = self._candle_subs.get(epic)
            if client is None or callback is None:
                return
            sub = Subscription("MERGE", [f"CHART:{self._account_id}:{epic}:{scale}"], _CHART_FIELDS)
            sub.addListener(_CandleListener(epic, callback))
            self._chart_subs[epic] = sub
        client.subscribe(sub)
