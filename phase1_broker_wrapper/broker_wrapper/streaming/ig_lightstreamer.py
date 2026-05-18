"""IG Lightstreamer client — production streaming target.

STATUS: Skeleton with the protocol structure in place. The Lightstreamer
protocol is HTTP-based: a session is opened, then a long-lived control
stream delivers tick updates. IG documents the items as:

    L1:CS.D.EURUSD.CFD.IP  →  fields: BID, OFFER, HIGH, LOW, ...
    L1:IX.D.DAX.IFM.IP     →  ditto for indices

Authentication uses the same CST and X-SECURITY-TOKEN as REST, plus the
account ID and a lightstreamerEndpoint returned by POST /session.

Why this is a skeleton, not a full implementation:
    Lightstreamer's TLCP protocol is non-trivial (~200-300 lines of
    parsing + reconnect logic) and needs live testing against IG to
    validate. The PollingStreamClient is a functional bridge that
    keeps the bot working today; this file gets fleshed out in a
    dedicated session with a live demo account.

Two implementation paths from here:
    1) Raw TLCP — implement the protocol directly with `requests`
       streaming. Most control. Most code (~300 lines).
    2) `lightstreamer-client` package — minimal Python client by
       Lightstreamer.com. Less code but introduces a dependency.

Recommendation: raw TLCP for the same reasons we chose raw REST.
"""

from __future__ import annotations

import logging
import threading
from typing import Callable

from broker_wrapper.streaming.base import StreamClient, PriceTick, PriceCallback

log = logging.getLogger(__name__)


class IGLightstreamerClient(StreamClient):
    """IG Lightstreamer streaming client. NOT YET IMPLEMENTED.

    Constructor signature is fixed so the factory and bot code can be
    written against it now. Implementation comes after smoke-testing
    the REST path against the demo account.
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
        self._endpoint = lightstreamer_endpoint
        self._running = False
        self._subscriptions: dict[str, PriceCallback] = {}
        self._lock = threading.Lock()
        # TODO: session_id, control_link, subscription_ids, etc.

    def start(self) -> None:
        # TODO: open Lightstreamer session via POST {endpoint}/create_session.txt
        #   with body: LS_user, LS_password (= CST), LS_adapter_set=DEFAULT
        #   parse "OK\nSessionId:...\nControlAddress:..." response,
        #   start the long-lived /bind_session.txt stream reader thread.
        raise NotImplementedError("IGLightstreamerClient is a skeleton — use PollingStreamClient for now")

    def stop(self) -> None:
        # TODO: POST destroy_session.txt + join reader thread.
        self._running = False

    def subscribe(self, epic: str, callback: PriceCallback) -> None:
        # TODO: POST control.txt with LS_op=add, LS_id=N, LS_table=N,
        #   LS_mode=MERGE, LS_data_adapter=DEFAULT,
        #   LS_id=L1:{epic}, LS_schema="BID OFFER UPDATE_TIME"
        with self._lock:
            self._subscriptions[epic] = callback

    def unsubscribe(self, epic: str) -> None:
        # TODO: POST control.txt with LS_op=delete, LS_id=N
        with self._lock:
            self._subscriptions.pop(epic, None)

    @property
    def is_running(self) -> bool:
        return self._running

    # TODO: _reader_loop — parses TLCP frames, dispatches to callbacks.
    # TODO: _parse_update — translate "1,1|BID|ASK|TIME" into PriceTick.
    # TODO: reconnect logic on PROBE failures.
