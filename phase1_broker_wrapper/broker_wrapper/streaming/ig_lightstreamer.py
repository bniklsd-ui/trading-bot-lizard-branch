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

from broker_wrapper.streaming.base import StreamClient, PriceTick, PriceCallback

log = logging.getLogger(__name__)

_FIELDS = ["BIDPRICE1", "ASKPRICE1", "TIMESTAMP"]


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


class IGLightstreamerClient(StreamClient):
    """IG real-time price feed backed by the official Lightstreamer SDK.

    Constructor signature is fixed; see factory.get_stream() for the canonical
    way to instantiate from a connected IGAdapter.
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
            epics = list(self._subscriptions.keys())
        client.connect()
        for epic in epics:
            self._do_subscribe(epic)

    def stop(self) -> None:
        with self._lock:
            if not self._running:
                return
            client = self._client
            subs = list(self._subs.values())
            self._subs.clear()
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
