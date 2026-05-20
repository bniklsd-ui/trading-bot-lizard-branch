"""IG Lightstreamer client — production streaming via TLCP over HTTP.

IG uses Lightstreamer's Text-based Client Protocol (TLCP-2.1.0). A session
is established with POST create_session.txt, subscriptions are registered
with POST control.txt, and updates arrive as a long-lived chunked response
from POST bind_session.txt.

Authentication:
    LS_user     = account_id
    LS_password = "CST-{cst}|XST-{security_token}"

Update format: U,{table},{item},{f0}|{f1}|{f2}
    Empty field = unchanged from last update (MERGE mode).
    Schema used here: BID OFFER UPDATE_TIME (indices 0, 1, 2).

Reconnect: on any connection error the reader thread creates a new LS
session and re-registers all active subscriptions automatically.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Callable

import requests

from broker_wrapper.streaming.base import StreamClient, PriceTick, PriceCallback

log = logging.getLogger(__name__)


def _ensure_scheme(address: str) -> str:
    """Prepend https:// if address is a bare hostname."""
    if address.startswith(("http://", "https://")):
        return address.rstrip("/")
    return "https://" + address.rstrip("/")


def _update_time_to_iso(time_str: str) -> str:
    """Convert IG UPDATE_TIME (HH:MM:SS.sss) to ISO 8601 UTC string."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if time_str and len(time_str) >= 8:
        return f"{today}T{time_str}Z"
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


class IGLightstreamerClient(StreamClient):
    """IG Lightstreamer streaming client — raw TLCP over requests.

    Constructor signature is fixed; see factory.get_stream() for the
    canonical way to instantiate from a connected IGAdapter.
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
        self._stop_event = threading.Event()
        self._reader_thread: threading.Thread | None = None
        self._response: requests.Response | None = None

        self._subscriptions: dict[str, PriceCallback] = {}

        # Per-session state (reset on every reconnect in _create_ls_session).
        self._session_id: str | None = None
        self._control_address: str | None = None   # normalized with https://
        self._table_counter: int = 0
        self._table_map: dict[str, int] = {}            # epic → LS table number
        self._field_cache: dict[int, dict[int, str]] = {}  # table → {idx: last_val}
        self._subok_fields: dict[int, int] = {}         # table → field count

        self._http = requests.Session()

    # ---------- StreamClient interface ----------

    def start(self) -> None:
        with self._lock:
            if self._running:
                return
            self._running = True
            self._stop_event.clear()
        try:
            self._create_ls_session()
            self._resubscribe_all()
        except Exception:
            log.exception("Lightstreamer session creation failed")
            with self._lock:
                self._running = False
            return
        self._reader_thread = threading.Thread(
            target=self._reader_loop, daemon=True, name="ls-reader"
        )
        self._reader_thread.start()

    def stop(self) -> None:
        with self._lock:
            if not self._running:
                return
            self._running = False
        self._stop_event.set()
        # Interrupt iter_lines() in the reader thread by closing the response.
        with self._lock:
            resp = self._response
        if resp is not None:
            try:
                resp.close()
            except Exception:
                pass
        if self._reader_thread:
            self._reader_thread.join(timeout=5.0)
            self._reader_thread = None

    def subscribe(self, epic: str, callback: PriceCallback) -> None:
        with self._lock:
            self._subscriptions[epic] = callback
            session_id = self._session_id
            control = self._control_address
        if session_id and control:
            self._send_subscribe(epic, session_id, control)

    def unsubscribe(self, epic: str) -> None:
        with self._lock:
            self._subscriptions.pop(epic, None)
            self._table_map.pop(epic, None)

    @property
    def is_running(self) -> bool:
        return self._running

    # ---------- TLCP session management ----------

    def _create_ls_session(self) -> None:
        """POST create_session.txt and parse SessionId + ControlAddress."""
        url = self._endpoint + "/lightstreamer/create_session.txt"
        resp = self._http.post(url, data={
            "LS_protocol": "TLCP-2.1.0",
            "LS_adapter_set": "DEFAULT",
            "LS_user": self._account_id,
            "LS_password": f"CST-{self._cst}|XST-{self._security_token}",
        }, timeout=10.0)
        resp.raise_for_status()
        lines = resp.text.splitlines()
        if not lines or lines[0].strip() != "OK":
            raise RuntimeError(f"Lightstreamer create_session failed: {resp.text[:200]}")
        session_id = None
        control_address = None
        for line in lines[1:]:
            if line.startswith("SessionId:"):
                session_id = line.split(":", 1)[1].strip()
            elif line.startswith("ControlAddress:"):
                control_address = _ensure_scheme(line.split(":", 1)[1].strip())
        if not session_id or not control_address:
            raise RuntimeError(
                f"Lightstreamer missing SessionId/ControlAddress: {resp.text[:200]}"
            )
        with self._lock:
            self._session_id = session_id
            self._control_address = control_address
            self._field_cache.clear()
            self._subok_fields.clear()
            self._table_counter = 0
            self._table_map.clear()
        log.info("Lightstreamer session created: %s", session_id)

    def _resubscribe_all(self) -> None:
        """Re-register all known subscriptions after a (re)connect."""
        with self._lock:
            epics = list(self._subscriptions.keys())
            session_id = self._session_id
            control = self._control_address
        for epic in epics:
            self._send_subscribe(epic, session_id, control)

    def _send_subscribe(self, epic: str, session_id: str, control_address: str) -> None:
        """POST control.txt to add one subscription. Assigns a new table ID."""
        with self._lock:
            if epic in self._table_map:
                return
            self._table_counter += 1
            table_id = self._table_counter
            self._table_map[epic] = table_id
        url = control_address + "/lightstreamer/control.txt"
        try:
            resp = self._http.post(url, data={
                "LS_session": session_id,
                "LS_op": "add",
                "LS_table": str(table_id),
                "LS_id": f"L1:{epic}",
                "LS_schema": "BID OFFER UPDATE_TIME",
                "LS_mode": "MERGE",
                "LS_data_adapter": "DEFAULT",
            }, timeout=10.0)
            resp.raise_for_status()
            log.debug("Subscribed %s as table %d", epic, table_id)
        except Exception:
            log.exception("control.txt subscribe failed for %s", epic)
            with self._lock:
                self._table_map.pop(epic, None)

    # ---------- Reader thread ----------

    def _reader_loop(self) -> None:
        """Daemon thread: bind, read, reconnect on error."""
        while not self._stop_event.is_set():
            try:
                self._bind_and_read()
            except Exception:
                log.exception("Lightstreamer reader error; will reconnect")
            if self._stop_event.is_set():
                break
            try:
                self._create_ls_session()
                self._resubscribe_all()
            except Exception:
                log.exception("Lightstreamer reconnect failed; retrying in 5s")
                self._stop_event.wait(5.0)
        with self._lock:
            self._running = False

    def _bind_and_read(self) -> None:
        """POST bind_session.txt and iterate TLCP lines until stop or error."""
        with self._lock:
            session_id = self._session_id
        resp = self._http.post(
            self._endpoint + "/lightstreamer/bind_session.txt",
            data={"LS_session": session_id},
            stream=True,
            timeout=30.0,
        )
        resp.raise_for_status()
        with self._lock:
            self._response = resp
        try:
            for raw_line in resp.iter_lines(decode_unicode=True):
                if self._stop_event.is_set():
                    break
                if raw_line:
                    self._handle_line(raw_line)
        finally:
            with self._lock:
                self._response = None
            resp.close()

    # ---------- TLCP frame handling ----------

    def _handle_line(self, line: str) -> None:
        if line.startswith("SUBOK"):
            parts = line.split(",")
            if len(parts) >= 4:
                try:
                    with self._lock:
                        self._subok_fields[int(parts[1])] = int(parts[3])
                except ValueError:
                    pass
            return
        if line.startswith("U,"):
            self._handle_update(line)
        # PROBE, CONOK, EOS, END, CLIENTIP, SERVNAME: silently ignored

    def _handle_update(self, line: str) -> None:
        """Parse U,{table},{item},{fields} and dispatch to callback.

        Never holds _lock while calling the callback.
        """
        parts = line.split(",", 3)
        if len(parts) < 4:
            return
        try:
            table_id = int(parts[1])
            raw_fields = parts[3].split("|")
        except ValueError:
            log.warning("malformed update: %s", line)
            return

        # Merge into field cache (empty string = field unchanged in MERGE mode).
        with self._lock:
            cache = self._field_cache.setdefault(table_id, {})
            for idx, val in enumerate(raw_fields):
                if val != "":
                    cache[idx] = val
            bid_str  = cache.get(0, "")
            ask_str  = cache.get(1, "")
            time_str = cache.get(2, "")
            epic = next(
                (e for e, tid in self._table_map.items() if tid == table_id), None
            )
            callback = self._subscriptions.get(epic) if epic else None

        if not epic or not callback or not bid_str or not ask_str:
            return
        try:
            bid, ask = float(bid_str), float(ask_str)
        except ValueError:
            log.warning("non-numeric price in update: %s", line)
            return

        tick = PriceTick(
            epic=epic, bid=bid, ask=ask,
            timestamp=_update_time_to_iso(time_str),
        )
        try:
            callback(tick)
        except Exception:
            log.exception("callback raised for epic %s", epic)
