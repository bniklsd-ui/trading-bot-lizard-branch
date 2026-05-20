"""Unit tests for IGLightstreamerClient and related factory/adapter changes.

All HTTP is mocked — no network calls.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest

from broker_wrapper.adapters.ig_adapter import IGAdapter
from broker_wrapper.streaming.ig_lightstreamer import (
    IGLightstreamerClient,
    _ensure_scheme,
    _update_time_to_iso,
)
from broker_wrapper.factory import get_stream


# ---------- helpers ----------------------------------------------------------


def _adapter() -> IGAdapter:
    return IGAdapter(
        username="u", password="p", api_key="k", account_id="ACC1",
        demo=True, request_timeout=1.0, max_retries=0,
    )


def _connected_adapter() -> IGAdapter:
    a = _adapter()
    a._cst = "cst-x"
    a._security_token = "tok-y"
    a._lightstreamer_endpoint = "https://push.example.com"
    a._session_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    return a


def _client(**kwargs) -> IGLightstreamerClient:
    defaults = dict(
        cst="cst-x",
        security_token="tok-y",
        account_id="ACC1",
        lightstreamer_endpoint="https://push.example.com",
    )
    defaults.update(kwargs)
    return IGLightstreamerClient(**defaults)


def _mock_response(status: int = 200, text: str = "", headers: dict | None = None) -> MagicMock:
    m = MagicMock()
    m.status_code = status
    m.text = text
    m.headers = headers or {}
    m.content = text.encode() if text else b""
    m.json.return_value = {}
    m.raise_for_status = MagicMock()
    return m


# ---------- adapter changes --------------------------------------------------


def test_login_captures_lightstreamer_endpoint():
    a = _adapter()
    login_resp = MagicMock()
    login_resp.status_code = 200
    login_resp.content = b"x"
    login_resp.headers = {"CST": "cst-x", "X-SECURITY-TOKEN": "tok-y"}
    login_resp.json.return_value = {
        "currentAccountId": "ACC1",
        "lightstreamerEndpoint": "https://push.example.com",
    }
    with patch.object(a._session, "post", return_value=login_resp):
        a.connect()
    assert a._lightstreamer_endpoint == "https://push.example.com"
    assert a.lightstreamer_endpoint == "https://push.example.com"


def test_lightstreamer_endpoint_property_before_connect():
    a = _adapter()
    assert a.lightstreamer_endpoint == ""


# ---------- client construction ----------------------------------------------


def test_client_init():
    c = _client()
    assert c._cst == "cst-x"
    assert c._security_token == "tok-y"
    assert c._account_id == "ACC1"
    assert c._endpoint == "https://push.example.com"
    assert c._running is False
    assert c._subscriptions == {}
    assert c._session_id is None
    assert c._table_map == {}


# ---------- subscribe / unsubscribe ------------------------------------------


def test_subscribe_unsubscribe_thread_safe():
    c = _client()
    cb = MagicMock()
    # No active session → no control.txt POST.
    c.subscribe("IX.D.DAX.IFMM.IP", cb)
    assert "IX.D.DAX.IFMM.IP" in c._subscriptions
    c.unsubscribe("IX.D.DAX.IFMM.IP")
    assert "IX.D.DAX.IFMM.IP" not in c._subscriptions
    # Idempotent.
    c.unsubscribe("IX.D.DAX.IFMM.IP")


# ---------- _create_ls_session -----------------------------------------------


def test_create_session_parses_ok_response():
    c = _client()
    session_text = (
        "OK\n"
        "SessionId:S-abc123\n"
        "ControlAddress:ctrl.example.com\n"
        "KeepaliveMillis:5000\n"
    )
    with patch.object(c._http, "post", return_value=_mock_response(text=session_text)):
        c._create_ls_session()
    assert c._session_id == "S-abc123"
    assert c._control_address == "https://ctrl.example.com"


def test_create_session_error_raises():
    c = _client()
    with patch.object(c._http, "post", return_value=_mock_response(text="ERROR\nErrorCode:10\n")):
        with pytest.raises(RuntimeError, match="create_session failed"):
            c._create_ls_session()


def test_create_session_missing_fields_raises():
    c = _client()
    # OK but no SessionId line.
    with patch.object(c._http, "post", return_value=_mock_response(text="OK\n")):
        with pytest.raises(RuntimeError, match="missing SessionId"):
            c._create_ls_session()


# ---------- update parsing ---------------------------------------------------


def test_handle_update_dispatches_callback():
    c = _client()
    cb = MagicMock()
    c._table_map["IX.D.DAX.IFMM.IP"] = 1
    c._subscriptions["IX.D.DAX.IFMM.IP"] = cb

    c._handle_update("U,1,1,24615.9|24617.0|08:30:00.000")

    cb.assert_called_once()
    tick = cb.call_args[0][0]
    assert tick.epic == "IX.D.DAX.IFMM.IP"
    assert tick.bid == pytest.approx(24615.9)
    assert tick.ask == pytest.approx(24617.0)
    assert "08:30:00.000" in tick.timestamp


def test_handle_update_field_cache():
    c = _client()
    cb = MagicMock()
    c._table_map["EPIC"] = 1
    c._subscriptions["EPIC"] = cb

    c._handle_update("U,1,1,100.0|101.0|09:00:00.000")
    assert cb.call_count == 1

    # Empty offer and time fields — should reuse cached values.
    c._handle_update("U,1,1,100.5||")
    assert cb.call_count == 2
    tick = cb.call_args[0][0]
    assert tick.bid == pytest.approx(100.5)
    assert tick.ask == pytest.approx(101.0)   # from cache


def test_handle_update_incomplete_before_cache_no_callback():
    c = _client()
    cb = MagicMock()
    c._table_map["EPIC"] = 1
    c._subscriptions["EPIC"] = cb

    # Only bid present, ask empty, cache is cold — no callback yet.
    c._handle_update("U,1,1,100.0||")
    cb.assert_not_called()


# ---------- _handle_line dispatching -----------------------------------------


def test_probe_ignored():
    c = _client()
    cb = MagicMock()
    c._table_map["EPIC"] = 1
    c._subscriptions["EPIC"] = cb
    c._handle_line("PROBE")
    cb.assert_not_called()


def test_subok_stores_field_count():
    c = _client()
    c._handle_line("SUBOK,1,1,3")
    assert c._subok_fields[1] == 3


# ---------- factory ----------------------------------------------------------


def test_get_stream_requires_connected():
    a = _adapter()
    with pytest.raises(RuntimeError, match="connect()"):
        get_stream(a)


def test_get_stream_returns_client():
    a = _connected_adapter()
    client = get_stream(a)
    assert isinstance(client, IGLightstreamerClient)
    assert client._cst == "cst-x"
    assert client._account_id == "ACC1"
    assert client._endpoint == "https://push.example.com"


# ---------- helpers ----------------------------------------------------------


def test_ensure_scheme_adds_https():
    assert _ensure_scheme("ctrl.example.com") == "https://ctrl.example.com"
    assert _ensure_scheme("https://ctrl.example.com") == "https://ctrl.example.com"
    assert _ensure_scheme("https://ctrl.example.com/") == "https://ctrl.example.com"


def test_update_time_to_iso_formats_correctly():
    ts = _update_time_to_iso("08:30:00.000")
    assert ts.endswith("T08:30:00.000Z")
    assert "T" in ts


def test_update_time_to_iso_fallback_on_empty():
    ts = _update_time_to_iso("")
    # Should still be a valid-looking ISO string.
    assert "T" in ts
    assert ts.endswith("Z")
