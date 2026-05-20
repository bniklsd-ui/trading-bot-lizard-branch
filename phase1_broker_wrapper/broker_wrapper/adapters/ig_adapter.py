"""IGAdapter — IG Markets REST API implementation.

Targets the EUR-denominated IG Markets Deutschland account, trading
DAX CFDs as the primary product. Pure REST (no third-party trading-ig
dependency) so all error paths are visible and controllable.

Session model:
    POST /session returns CST and X-SECURITY-TOKEN in response HEADERS.
    Both are required on subsequent calls. Session validity ~6h.
    On 401, the adapter attempts one re-login then surfaces the error.

Order model:
    POST /positions/otc returns only a dealReference. The actual deal
    status (ACCEPTED / REJECTED) requires GET /confirms/{dealReference}.
    open_position() polls confirms with a short timeout so callers get
    a final OrderResult in one call.

This implementation is structurally complete but has NOT been integration-
tested against a live IG account in this session. Verify each endpoint
in IG's REST API Companion against your account permissions before
running with real money. The smoke_test.py script is the canonical way
to validate end-to-end.
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from broker_wrapper.adapters.base import BrokerAdapter
from broker_wrapper.envelope import Envelope, LatencyTimer, ok_envelope, error_envelope
from broker_wrapper.exceptions import (
    AuthenticationError,
    BrokerError,
    EpicNotFoundError,
    InsufficientFundsError,
    MarketOfflineError,
    NetworkError,
    OrderRejectedError,
    ProtocolError,
    RateLimitError,
)
from broker_wrapper.filters import calc_spread_pct
from broker_wrapper.models import (
    Account,
    Direction,
    MarketInfo,
    OHLCBar,
    OrderResult,
    OrderType,
    Position,
    Price,
    Transaction,
)

log = logging.getLogger(__name__)


# ---- API constants ------------------------------------------------------

LIVE_BASE_URL = "https://api.ig.com/gateway/deal"
DEMO_BASE_URL = "https://demo-api.ig.com/gateway/deal"

# Map IG market status strings → our normalized MarketStatus literal.
_STATUS_MAP = {
    "TRADEABLE": "TRADEABLE",
    "CLOSED": "CLOSED",
    "EDIT": "EDITS_ONLY",
    "EDITS_ONLY": "EDITS_ONLY",
    "AUCTION": "AUCTION",
    "AUCTION_NO_EDIT": "AUCTION",
    "ON_AUCTION": "AUCTION",
    "ON_AUCTION_NO_EDITS": "AUCTION",
    "OFFLINE": "OFFLINE",
    "SUSPENDED": "OFFLINE",
}

VALID_RESOLUTIONS = {
    "SECOND", "MINUTE", "MINUTE_2", "MINUTE_3", "MINUTE_5",
    "MINUTE_10", "MINUTE_15", "MINUTE_30",
    "HOUR", "HOUR_2", "HOUR_3", "HOUR_4",
    "DAY", "WEEK", "MONTH",
}

# Default polling for /confirms after an order submission.
CONFIRM_POLL_INTERVAL_S = 0.25
CONFIRM_TIMEOUT_S = 5.0


class IGAdapter(BrokerAdapter):
    """IG Markets REST adapter.

    Args:
        username, password, api_key, account_id: credentials.
        demo: if True, use the demo endpoint.
        request_timeout: per-request HTTP timeout in seconds.
        max_retries: number of retries on transient network errors.
    """

    name = "ig"

    def __init__(
        self,
        *,
        username: str,
        password: str,
        api_key: str,
        account_id: str,
        demo: bool = False,
        request_timeout: float = 10.0,
        max_retries: int = 2,
    ) -> None:
        if not all([username, password, api_key, account_id]):
            raise ValueError("IGAdapter requires username, password, api_key, account_id")

        self._username = username
        self._password = password
        self._api_key = api_key
        self._account_id = account_id
        self._base_url = DEMO_BASE_URL if demo else LIVE_BASE_URL
        self._timeout = request_timeout
        self._max_retries = max_retries

        self._session = requests.Session()
        self._cst: str | None = None
        self._security_token: str | None = None
        self._session_expires_at: datetime | None = None
        self._lightstreamer_endpoint: str = ""

    # ---------- Session ----------

    def connect(self) -> Envelope:
        with LatencyTimer() as t:
            try:
                self._login()
            except BrokerError as e:
                return error_envelope(
                    broker=self.name, method="connect",
                    code=e.code, message=str(e),
                    retryable=e.retryable, latency_ms=t.ms,
                )
        return ok_envelope(
            broker=self.name, method="connect",
            data={
                "account_id": self._account_id,
                "expires_at": self._session_expires_at.isoformat()
                if self._session_expires_at else None,
            },
            latency_ms=t.ms,
        )

    def disconnect(self) -> Envelope:
        with LatencyTimer() as t:
            if not self.is_connected():
                return ok_envelope(
                    broker=self.name, method="disconnect",
                    data={"already_disconnected": True},
                    latency_ms=t.ms,
                )
            try:
                self._request("DELETE", "/session", version="1", auth=True)
            except BrokerError:
                # Best-effort. Even if logout fails, clear local state.
                pass
            self._cst = None
            self._security_token = None
            self._session_expires_at = None
        return ok_envelope(
            broker=self.name, method="disconnect",
            data={"disconnected": True}, latency_ms=t.ms,
        )

    def is_connected(self) -> bool:
        if not (self._cst and self._security_token):
            return False
        if self._session_expires_at and datetime.now(timezone.utc) >= self._session_expires_at:
            return False
        return True

    @property
    def lightstreamer_endpoint(self) -> str:
        """Lightstreamer push endpoint from POST /session. Empty string before login."""
        return self._lightstreamer_endpoint

    def _login(self) -> None:
        """Acquire CST + X-SECURITY-TOKEN via POST /session (v2)."""
        url = f"{self._base_url}/session"
        headers = self._base_headers(version="2", auth=False)
        body = {"identifier": self._username, "password": self._password}

        try:
            resp = self._session.post(url, json=body, headers=headers,
                                      timeout=self._timeout)
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"login transport error: {e}", retryable=True) from e

        if resp.status_code == 401 or resp.status_code == 403:
            raise AuthenticationError(f"login rejected: {resp.status_code} {resp.text[:200]}")
        if resp.status_code != 200:
            raise ProtocolError(
                f"unexpected login status {resp.status_code}: {resp.text[:200]}"
            )

        cst = resp.headers.get("CST")
        token = resp.headers.get("X-SECURITY-TOKEN")
        if not cst or not token:
            raise ProtocolError("login response missing CST/X-SECURITY-TOKEN headers")

        self._cst = cst
        self._security_token = token
        # IG sessions are nominally valid 6h; refresh a bit early.
        self._session_expires_at = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)

        # Switch to the configured account if not already current.
        body_meta = resp.json() if resp.content else {}
        self._lightstreamer_endpoint = body_meta.get("lightstreamerEndpoint", "")
        current = body_meta.get("currentAccountId")
        if current and current != self._account_id:
            self._switch_account(self._account_id)

    def _switch_account(self, account_id: str) -> None:
        """PUT /session with body {accountId, defaultAccount} (v1)."""
        try:
            self._request(
                "PUT", "/session", version="1", auth=True,
                json_body={"accountId": account_id, "defaultAccount": True},
            )
        except BrokerError as e:
            log.warning("account switch to %s failed: %s", account_id, e)

    # ---------- HTTP plumbing ----------

    def _base_headers(self, *, version: str, auth: bool) -> dict[str, str]:
        headers = {
            "X-IG-API-KEY": self._api_key,
            "Accept": "application/json; charset=UTF-8",
            "Content-Type": "application/json; charset=UTF-8",
            "Version": version,
        }
        if auth:
            if not (self._cst and self._security_token):
                raise AuthenticationError("not connected — call connect() first")
            headers["CST"] = self._cst
            headers["X-SECURITY-TOKEN"] = self._security_token
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        version: str,
        auth: bool,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
        attempt: int = 1,
    ) -> dict[str, Any]:
        """Execute an HTTP request and return parsed JSON.

        Maps HTTP error codes onto BrokerError subclasses. Performs one
        re-login on 401 and limited retries on network errors.
        """
        url = f"{self._base_url}{path}"
        headers = self._base_headers(version=version, auth=auth)
        if extra_headers:
            headers.update(extra_headers)

        try:
            resp = self._session.request(
                method, url, params=params, json=json_body,
                headers=headers, timeout=self._timeout,
            )
        except requests.exceptions.Timeout as e:
            if attempt <= self._max_retries:
                time.sleep(0.5 * attempt)
                return self._request(
                    method, path, version=version, auth=auth,
                    params=params, json_body=json_body,
                    extra_headers=extra_headers, attempt=attempt + 1,
                )
            raise NetworkError(f"timeout after {self._max_retries} retries: {e}",
                               retryable=True) from e
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"transport error: {e}", retryable=True) from e

        # --- Status code dispatch ---
        if resp.status_code in (200, 201, 204):
            if not resp.content:
                return {}
            try:
                return resp.json()
            except ValueError as e:
                raise ProtocolError(f"non-JSON response: {resp.text[:200]}") from e

        # 401 → token expired. Try one re-login then retry once.
        if resp.status_code == 401 and auth and attempt == 1:
            log.info("401 — re-logging in and retrying")
            try:
                self._login()
            except BrokerError:
                raise AuthenticationError("re-login failed after 401")
            return self._request(
                method, path, version=version, auth=auth,
                params=params, json_body=json_body,
                extra_headers=extra_headers, attempt=attempt + 1,
            )

        if resp.status_code == 403:
            raise AuthenticationError(f"403 forbidden: {resp.text[:200]}")
        if resp.status_code == 404:
            raise EpicNotFoundError(f"404 not found: {path}")
        if resp.status_code == 405:
            # IG returns 405 when a market is offline. Map accordingly.
            raise MarketOfflineError(f"405 market offline: {path}")
        if resp.status_code == 429:
            raise RateLimitError(f"429 rate limited: {resp.text[:200]}", retryable=True)
        if 500 <= resp.status_code < 600:
            if attempt <= self._max_retries:
                time.sleep(0.5 * attempt)
                return self._request(
                    method, path, version=version, auth=auth,
                    params=params, json_body=json_body,
                    extra_headers=extra_headers, attempt=attempt + 1,
                )
            raise BrokerError(
                f"5xx broker error after {self._max_retries} retries: "
                f"{resp.status_code} {resp.text[:200]}",
                retryable=True,
            )

        # Other 4xx — parse error code from body if present.
        body = {}
        try:
            body = resp.json()
        except ValueError:
            pass
        error_code = body.get("errorCode", "") if isinstance(body, dict) else ""
        msg = f"{resp.status_code} {error_code or resp.text[:200]}"

        if "insufficient" in error_code.lower() or "margin" in error_code.lower():
            raise InsufficientFundsError(msg)
        if "rejected" in error_code.lower():
            raise OrderRejectedError(msg)
        raise BrokerError(msg)

    # ---------- Market data ----------

    def get_price(self, epic: str) -> Envelope:
        with LatencyTimer() as t:
            try:
                body = self._request(
                    "GET", f"/markets/{epic}", version="3", auth=True,
                )
                snap = body.get("snapshot") or {}
                bid = float(snap.get("bid", 0) or 0)
                ask = float(snap.get("offer", 0) or 0)
                status_raw = snap.get("marketStatus", "UNKNOWN")
                price = Price(
                    epic=epic,
                    bid=bid,
                    ask=ask,
                    spread=ask - bid,
                    spread_pct=calc_spread_pct(bid, ask),
                    market_status=_STATUS_MAP.get(status_raw, "UNKNOWN"),  # type: ignore[arg-type]
                    timestamp=snap.get("updateTime") or _utc_now_iso(),
                )
                return ok_envelope(
                    broker=self.name, method="get_price",
                    data=price.to_dict(), latency_ms=t.ms,
                )
            except BrokerError as e:
                return error_envelope(
                    broker=self.name, method="get_price",
                    code=e.code, message=str(e),
                    retryable=e.retryable, latency_ms=t.ms,
                )

    def get_ohlcv(self, epic: str, resolution: str, count: int) -> Envelope:
        if resolution not in VALID_RESOLUTIONS:
            raise ValueError(f"resolution must be one of {VALID_RESOLUTIONS}")
        if count <= 0 or count > 1000:
            raise ValueError("count must be in (0, 1000]")
        with LatencyTimer() as t:
            try:
                body = self._request(
                    "GET", f"/prices/{epic}",
                    version="3", auth=True,
                    params={"resolution": resolution, "max": count, "pageSize": count},
                )
                bars = [_parse_bar(p) for p in body.get("prices", [])]
                allowance = body.get("allowance", {})
                return ok_envelope(
                    broker=self.name, method="get_ohlcv",
                    data={"bars": [b.__dict__ for b in bars], "allowance": allowance},
                    latency_ms=t.ms,
                )
            except BrokerError as e:
                return error_envelope(
                    broker=self.name, method="get_ohlcv",
                    code=e.code, message=str(e),
                    retryable=e.retryable, latency_ms=t.ms,
                )

    def get_historical_ohlcv(
        self, epic: str, from_dt: str, to_dt: str, resolution: str,
    ) -> Envelope:
        if resolution not in VALID_RESOLUTIONS:
            raise ValueError(f"resolution must be one of {VALID_RESOLUTIONS}")
        with LatencyTimer() as t:
            try:
                body = self._request(
                    "GET", f"/prices/{epic}",
                    version="3", auth=True,
                    params={
                        "resolution": resolution,
                        "from": from_dt, "to": to_dt,
                        "pageSize": 1000,
                    },
                )
                bars = [_parse_bar(p) for p in body.get("prices", [])]
                allowance = body.get("allowance", {})
                return ok_envelope(
                    broker=self.name, method="get_historical_ohlcv",
                    data={"bars": [b.__dict__ for b in bars], "allowance": allowance},
                    latency_ms=t.ms,
                )
            except BrokerError as e:
                return error_envelope(
                    broker=self.name, method="get_historical_ohlcv",
                    code=e.code, message=str(e),
                    retryable=e.retryable, latency_ms=t.ms,
                )

    def get_market_info(self, epic: str) -> Envelope:
        with LatencyTimer() as t:
            try:
                body = self._request(
                    "GET", f"/markets/{epic}", version="3", auth=True,
                )
                instr = body.get("instrument", {}) or {}
                rules = body.get("dealingRules", {}) or {}
                snap = body.get("snapshot", {}) or {}
                min_size_rule = (rules.get("minDealSize") or {})
                info = MarketInfo(
                    epic=epic,
                    name=instr.get("name", ""),
                    instrument_type=instr.get("type", ""),
                    currency=_extract_currency(instr),
                    expiry=instr.get("expiry") if instr.get("expiry") != "-" else None,
                    min_deal_size=float(min_size_rule.get("value", 0) or 0),
                    lot_size=float(instr.get("lotSize", 1) or 1),
                    market_status=_STATUS_MAP.get(
                        snap.get("marketStatus", "UNKNOWN"), "UNKNOWN"
                    ),  # type: ignore[arg-type]
                )
                return ok_envelope(
                    broker=self.name, method="get_market_info",
                    data=info.to_dict(), latency_ms=t.ms,
                )
            except BrokerError as e:
                return error_envelope(
                    broker=self.name, method="get_market_info",
                    code=e.code, message=str(e),
                    retryable=e.retryable, latency_ms=t.ms,
                )

    def search_markets(self, query: str) -> Envelope:
        with LatencyTimer() as t:
            try:
                body = self._request(
                    "GET", "/markets", version="1", auth=True,
                    params={"searchTerm": query},
                )
                results = [
                    {
                        "epic": m.get("epic"),
                        "name": m.get("instrumentName"),
                        "type": m.get("instrumentType"),
                        "expiry": m.get("expiry"),
                        "market_status": _STATUS_MAP.get(
                            m.get("marketStatus", "UNKNOWN"), "UNKNOWN"
                        ),
                        "bid": m.get("bid"),
                        "ask": m.get("offer"),
                    }
                    for m in body.get("markets", [])
                ]
                return ok_envelope(
                    broker=self.name, method="search_markets",
                    data={"query": query, "results": results},
                    latency_ms=t.ms,
                )
            except BrokerError as e:
                return error_envelope(
                    broker=self.name, method="search_markets",
                    code=e.code, message=str(e),
                    retryable=e.retryable, latency_ms=t.ms,
                )

    # ---------- Account ----------

    def get_account(self) -> Envelope:
        with LatencyTimer() as t:
            try:
                body = self._request("GET", "/accounts", version="1", auth=True)
                accounts = body.get("accounts", [])
                target = next(
                    (a for a in accounts if a.get("accountId") == self._account_id),
                    accounts[0] if accounts else None,
                )
                if not target:
                    raise ProtocolError("no accounts returned")
                bal = target.get("balance", {}) or {}
                acc = Account(
                    account_id=target.get("accountId", self._account_id),
                    balance=float(bal.get("balance", 0) or 0),
                    available=float(bal.get("available", 0) or 0),
                    profit_loss=float(bal.get("profitLoss", 0) or 0),
                    currency=target.get("currency", ""),
                )
                return ok_envelope(
                    broker=self.name, method="get_account",
                    data=acc.to_dict(), latency_ms=t.ms,
                )
            except BrokerError as e:
                return error_envelope(
                    broker=self.name, method="get_account",
                    code=e.code, message=str(e),
                    retryable=e.retryable, latency_ms=t.ms,
                )

    def get_open_positions(self) -> Envelope:
        with LatencyTimer() as t:
            try:
                body = self._request("GET", "/positions", version="2", auth=True)
                positions = [_parse_position(p) for p in body.get("positions", [])]
                return ok_envelope(
                    broker=self.name, method="get_open_positions",
                    data={"positions": [p.to_dict() for p in positions]},
                    latency_ms=t.ms,
                )
            except BrokerError as e:
                return error_envelope(
                    broker=self.name, method="get_open_positions",
                    code=e.code, message=str(e),
                    retryable=e.retryable, latency_ms=t.ms,
                )

    def get_trade_history(self, days: int = 30) -> Envelope:
        if days <= 0 or days > 365:
            raise ValueError("days must be in (0, 365]")
        with LatencyTimer() as t:
            try:
                to_dt = datetime.now(timezone.utc)
                from_dt = to_dt - timedelta(days=days)
                body = self._request(
                    "GET", "/history/transactions", version="2", auth=True,
                    params={
                        "type": "ALL_DEAL",
                        "from": from_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                        "to": to_dt.strftime("%Y-%m-%dT%H:%M:%S"),
                    },
                )
                txs = [_parse_transaction(tx) for tx in body.get("transactions", [])]
                return ok_envelope(
                    broker=self.name, method="get_trade_history",
                    data={"transactions": [tx.__dict__ for tx in txs]},
                    latency_ms=t.ms,
                )
            except BrokerError as e:
                return error_envelope(
                    broker=self.name, method="get_trade_history",
                    code=e.code, message=str(e),
                    retryable=e.retryable, latency_ms=t.ms,
                )

    # ---------- Orders ----------

    def open_position(
        self,
        epic: str,
        direction: Direction,
        size: float,
        order_type: OrderType = "MARKET",
        *,
        level: float | None = None,
        stop_level: float | None = None,
        limit_level: float | None = None,
        deal_reference: str | None = None,
        currency: str | None = None,
    ) -> Envelope:
        if direction not in ("BUY", "SELL"):
            raise ValueError("direction must be BUY or SELL")
        if order_type not in ("MARKET", "LIMIT", "STOP"):
            raise ValueError("order_type must be MARKET, LIMIT, or STOP")
        if size <= 0:
            raise ValueError("size must be positive")
        if order_type in ("LIMIT", "STOP") and level is None:
            raise ValueError(f"{order_type} order requires `level`")

        # Generate idempotency key if caller didn't supply one.
        ref = deal_reference or _new_deal_reference()

        body: dict[str, Any] = {
            "epic": epic,
            "expiry": "-",            # CFD: no expiry
            "direction": direction,
            "size": size,
            "orderType": order_type,
            "guaranteedStop": False,
            "forceOpen": True,
            "dealReference": ref,
        }
        if currency:
            body["currencyCode"] = currency
        if order_type in ("LIMIT", "STOP"):
            body["level"] = level
        if stop_level is not None:
            body["stopLevel"] = stop_level
        if limit_level is not None:
            body["limitLevel"] = limit_level

        with LatencyTimer() as t:
            try:
                self._request(
                    "POST", "/positions/otc",
                    version="2", auth=True, json_body=body,
                )
                # Submission accepted at API layer; poll confirms for outcome.
                confirm = self._poll_confirms(ref)
                result = OrderResult(
                    deal_reference=ref,
                    deal_id=confirm.get("dealId"),
                    status=_normalize_deal_status(confirm.get("dealStatus", "UNKNOWN")),
                    epic=epic,
                    direction=direction,
                    size=size,
                    level=float(confirm["level"]) if confirm.get("level") is not None else None,
                    reason=confirm.get("reason"),
                    timestamp=_utc_now_iso(),
                )
                return ok_envelope(
                    broker=self.name, method="open_position",
                    data=result.to_dict(), latency_ms=t.ms,
                )
            except BrokerError as e:
                # Surface the reference so caller can reconcile later.
                return error_envelope(
                    broker=self.name, method="open_position",
                    code=e.code, message=str(e),
                    retryable=e.retryable, latency_ms=t.ms,
                    data={"deal_reference": ref},
                )

    def close_position(self, deal_id: str) -> Envelope:
        with LatencyTimer() as t:
            try:
                # Need direction + size to close: look up the open position.
                positions_env = self.get_open_positions()
                if not positions_env.ok:
                    raise BrokerError("could not list positions to close")
                target = None
                for p in positions_env.data.get("positions", []):
                    if p.get("deal_id") == deal_id:
                        target = p
                        break
                if target is None:
                    raise BrokerError(f"deal_id {deal_id} not in open positions")

                # Closing direction is the opposite.
                close_direction = "SELL" if target["direction"] == "BUY" else "BUY"

                body = {
                    "dealId": deal_id,
                    "direction": close_direction,
                    "size": target["size"],
                    "orderType": "MARKET",
                }
                # IG uses POST with _method: DELETE header for close.
                self._request(
                    "POST", "/positions/otc", version="1", auth=True,
                    json_body=body,
                    extra_headers={"_method": "DELETE"},
                )
                return ok_envelope(
                    broker=self.name, method="close_position",
                    data={"deal_id": deal_id, "status": "submitted"},
                    latency_ms=t.ms,
                )
            except BrokerError as e:
                return error_envelope(
                    broker=self.name, method="close_position",
                    code=e.code, message=str(e),
                    retryable=e.retryable, latency_ms=t.ms,
                )

    def modify_position(
        self,
        deal_id: str,
        *,
        stop_level: float | None = None,
        limit_level: float | None = None,
    ) -> Envelope:
        if stop_level is None and limit_level is None:
            raise ValueError("must supply stop_level or limit_level (or both)")
        body: dict[str, Any] = {}
        if stop_level is not None:
            body["stopLevel"] = stop_level
        if limit_level is not None:
            body["limitLevel"] = limit_level

        with LatencyTimer() as t:
            try:
                self._request(
                    "PUT", f"/positions/otc/{deal_id}",
                    version="2", auth=True, json_body=body,
                )
                return ok_envelope(
                    broker=self.name, method="modify_position",
                    data={"deal_id": deal_id, "stop_level": stop_level,
                          "limit_level": limit_level},
                    latency_ms=t.ms,
                )
            except BrokerError as e:
                return error_envelope(
                    broker=self.name, method="modify_position",
                    code=e.code, message=str(e),
                    retryable=e.retryable, latency_ms=t.ms,
                )

    def reconcile_positions(
        self, expected_references: list[str] | None = None,
    ) -> Envelope:
        """Pull broker truth and compare to expected references.

        The bot calls this on startup or after a network glitch to figure
        out which orders made it through and which did not.
        """
        with LatencyTimer() as t:
            try:
                positions_env = self.get_open_positions()
                if not positions_env.ok:
                    return error_envelope(
                        broker=self.name, method="reconcile_positions",
                        code=positions_env.error["code"],
                        message=positions_env.error["message"],
                        retryable=positions_env.error["retryable"],
                        latency_ms=t.ms,
                    )
                broker_refs = {
                    p.get("deal_reference") for p in positions_env.data["positions"]
                    if p.get("deal_reference")
                }
                broker_ids = [p.get("deal_id") for p in positions_env.data["positions"]]
                payload: dict[str, Any] = {
                    "broker_position_count": len(broker_ids),
                    "broker_deal_ids": broker_ids,
                }
                if expected_references is not None:
                    expected = set(expected_references)
                    payload["present"] = sorted(expected & broker_refs)
                    payload["missing"] = sorted(expected - broker_refs)
                    payload["unexpected"] = sorted(broker_refs - expected)
                return ok_envelope(
                    broker=self.name, method="reconcile_positions",
                    data=payload, latency_ms=t.ms,
                )
            except BrokerError as e:
                return error_envelope(
                    broker=self.name, method="reconcile_positions",
                    code=e.code, message=str(e),
                    retryable=e.retryable, latency_ms=t.ms,
                )

    # ---------- internals ----------

    def _poll_confirms(self, deal_reference: str) -> dict[str, Any]:
        """Poll GET /confirms/{ref} until dealStatus is final or timeout."""
        deadline = time.monotonic() + CONFIRM_TIMEOUT_S
        last_body: dict[str, Any] = {}
        while time.monotonic() < deadline:
            try:
                body = self._request(
                    "GET", f"/confirms/{deal_reference}",
                    version="1", auth=True,
                )
                last_body = body
                status = body.get("dealStatus")
                if status in ("ACCEPTED", "REJECTED"):
                    return body
            except EpicNotFoundError:
                # Confirm not yet available; retry.
                pass
            time.sleep(CONFIRM_POLL_INTERVAL_S)
        # Timed out — return whatever we last saw.
        last_body.setdefault("dealStatus", "PENDING")
        last_body.setdefault("reason", "confirm timeout — reconcile later")
        return last_body


# ---- Module-private helpers --------------------------------------------

def _new_deal_reference() -> str:
    """IG accepts up to 30 chars, alphanum + hyphen. UUID4 hex fits."""
    return f"bot-{uuid.uuid4().hex[:24]}"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
        f"{datetime.now(timezone.utc).microsecond // 1000:03d}Z"


def _parse_bar(p: dict[str, Any]) -> OHLCBar:
    """IG returns OHLC as nested {bid, ask} per field; use mid."""
    def mid(obj: dict[str, Any] | None) -> float:
        if not obj:
            return 0.0
        bid = float(obj.get("bid", 0) or 0)
        ask = float(obj.get("ask", 0) or 0)
        return (bid + ask) / 2 if (bid and ask) else (bid or ask)

    return OHLCBar(
        timestamp=p.get("snapshotTime") or p.get("snapshotTimeUTC", ""),
        open=mid(p.get("openPrice")),
        high=mid(p.get("highPrice")),
        low=mid(p.get("lowPrice")),
        close=mid(p.get("closePrice")),
        volume=float(p.get("lastTradedVolume", 0) or 0),
    )


def _parse_position(item: dict[str, Any]) -> Position:
    pos = item.get("position", {}) or {}
    market = item.get("market", {}) or {}
    direction = pos.get("direction", "BUY")
    return Position(
        deal_id=pos.get("dealId", ""),
        deal_reference=pos.get("dealReference"),
        epic=market.get("epic", ""),
        direction=direction,  # type: ignore[arg-type]
        size=float(pos.get("size", 0) or 0),
        open_level=float(pos.get("level", 0) or 0),
        current_level=None,  # caller can fetch separately if needed
        profit_loss=None,
        currency=pos.get("currency", ""),
        created_at=pos.get("createdDateUTC") or pos.get("createdDate", ""),
        stop_level=pos.get("stopLevel"),
        limit_level=pos.get("limitLevel"),
    )


def _parse_transaction(tx: dict[str, Any]) -> Transaction:
    return Transaction(
        transaction_id=tx.get("reference", ""),
        epic=tx.get("instrumentName"),
        direction=None,
        size=_safe_float(tx.get("size")),
        open_level=_safe_float(tx.get("openLevel")),
        close_level=_safe_float(tx.get("closeLevel")),
        profit_loss=_safe_float(_strip_currency(tx.get("profitAndLoss"))),
        currency=tx.get("currency"),
        open_date=tx.get("openDateUtc") or tx.get("openDate"),
        close_date=tx.get("dateUtc") or tx.get("date"),
        transaction_type=tx.get("transactionType", ""),
    )


def _safe_float(v: Any) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _strip_currency(v: Any) -> Any:
    """IG returns P&L like 'E12.34' — strip the leading currency letter."""
    if isinstance(v, str) and v and v[0].isalpha():
        return v[1:]
    return v


def _extract_currency(instr: dict[str, Any]) -> str:
    """IG instrument.currencies is a list; pick the default or first."""
    currencies = instr.get("currencies", [])
    if not currencies:
        return ""
    default = next((c for c in currencies if c.get("isDefault")), currencies[0])
    return default.get("code", "")


def _normalize_deal_status(s: str) -> str:
    return s if s in ("ACCEPTED", "REJECTED", "PENDING") else "UNKNOWN"
