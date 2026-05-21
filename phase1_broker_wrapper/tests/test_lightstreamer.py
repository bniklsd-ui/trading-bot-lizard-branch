"""Unit tests for IGLightstreamerClient (SDK-backed) and factory/adapter changes.

The Lightstreamer SDK is mocked — no network calls, no real connection.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest

from broker_wrapper.adapters.ig_adapter import IGAdapter
from broker_wrapper.streaming.ig_lightstreamer import (
    IGLightstreamerClient,
    _PriceListener,
    _utm_to_iso,
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


def _fake_update(bid="24615.9", ask="24617.0", ts="1747737000000") -> MagicMock:
    """Mock SDK ItemUpdate whose getValue() returns the given field values."""
    values = {"BIDPRICE1": bid, "ASKPRICE1": ask, "TIMESTAMP": ts}
    u = MagicMock()
    u.getValue.side_effect = lambda field: values.get(field)
    return u


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
    assert c._subs == {}


# ---------- start / stop -----------------------------------------------------


def test_start_connects_with_ig_credentials():
    c = _client()
    fake_client = MagicMock()
    with patch(
        "broker_wrapper.streaming.ig_lightstreamer.LightstreamerClient",
        return_value=fake_client,
    ) as ls_ctor:
        c.start()
    ls_ctor.assert_called_once_with("https://push.example.com", "DEFAULT")
    fake_client.connectionDetails.setUser.assert_called_once_with("ACC1")
    fake_client.connectionDetails.setPassword.assert_called_once_with(
        "CST-cst-x|XST-tok-y"
    )
    fake_client.connect.assert_called_once()
    assert c.is_running is True


def test_start_is_idempotent():
    c = _client()
    with patch(
        "broker_wrapper.streaming.ig_lightstreamer.LightstreamerClient",
        return_value=MagicMock(),
    ) as ls_ctor:
        c.start()
        c.start()
    ls_ctor.assert_called_once()


def test_stop_disconnects():
    c = _client()
    fake_client = MagicMock()
    with patch(
        "broker_wrapper.streaming.ig_lightstreamer.LightstreamerClient",
        return_value=fake_client,
    ):
        c.start()
        c.stop()
    fake_client.disconnect.assert_called_once()
    assert c.is_running is False


# ---------- subscribe / unsubscribe ------------------------------------------


def test_subscribe_creates_price_subscription():
    c = _client()
    fake_client = MagicMock()
    fake_sub = MagicMock()
    cb = MagicMock()
    with patch(
        "broker_wrapper.streaming.ig_lightstreamer.LightstreamerClient",
        return_value=fake_client,
    ), patch(
        "broker_wrapper.streaming.ig_lightstreamer.Subscription",
        return_value=fake_sub,
    ) as sub_ctor:
        c.start()
        c.subscribe("IX.D.DAX.IFMM.IP", cb)
    sub_ctor.assert_called_once_with(
        "MERGE", ["PRICE:ACC1:IX.D.DAX.IFMM.IP"],
        ["BIDPRICE1", "ASKPRICE1", "TIMESTAMP"],
    )
    fake_sub.setDataAdapter.assert_called_once_with("Pricing")
    fake_sub.addListener.assert_called_once()
    fake_client.subscribe.assert_called_once_with(fake_sub)


def test_subscribe_before_start_defers_until_start():
    c = _client()
    fake_client = MagicMock()
    fake_sub = MagicMock()
    cb = MagicMock()
    with patch(
        "broker_wrapper.streaming.ig_lightstreamer.LightstreamerClient",
        return_value=fake_client,
    ), patch(
        "broker_wrapper.streaming.ig_lightstreamer.Subscription",
        return_value=fake_sub,
    ):
        c.subscribe("IX.D.DAX.IFMM.IP", cb)   # no client yet → deferred
        fake_client.subscribe.assert_not_called()
        c.start()                              # start() subscribes the backlog
    fake_client.subscribe.assert_called_once_with(fake_sub)


def test_unsubscribe_removes_and_calls_sdk():
    c = _client()
    fake_client = MagicMock()
    cb = MagicMock()
    with patch(
        "broker_wrapper.streaming.ig_lightstreamer.LightstreamerClient",
        return_value=fake_client,
    ), patch(
        "broker_wrapper.streaming.ig_lightstreamer.Subscription",
        return_value=MagicMock(),
    ):
        c.start()
        c.subscribe("EPIC", cb)
        c.unsubscribe("EPIC")
    assert "EPIC" not in c._subscriptions
    assert "EPIC" not in c._subs
    fake_client.unsubscribe.assert_called_once()
    # idempotent
    c.unsubscribe("EPIC")


# ---------- _PriceListener ---------------------------------------------------


def test_price_listener_dispatches_tick():
    cb = MagicMock()
    lis = _PriceListener("IX.D.DAX.IFMM.IP", cb)
    lis.onItemUpdate(_fake_update(bid="24615.9", ask="24617.0", ts="1747737000000"))
    cb.assert_called_once()
    tick = cb.call_args[0][0]
    assert tick.epic == "IX.D.DAX.IFMM.IP"
    assert tick.bid == pytest.approx(24615.9)
    assert tick.ask == pytest.approx(24617.0)
    assert "T" in tick.timestamp and tick.timestamp.endswith("Z")


def test_price_listener_skips_incomplete_update():
    cb = MagicMock()
    lis = _PriceListener("EPIC", cb)
    lis.onItemUpdate(_fake_update(bid="100.0", ask=None, ts="1747737000000"))
    cb.assert_not_called()


def test_price_listener_swallows_non_numeric():
    cb = MagicMock()
    lis = _PriceListener("EPIC", cb)
    lis.onItemUpdate(_fake_update(bid="n/a", ask="101.0"))
    cb.assert_not_called()


def test_price_listener_callback_exception_isolated():
    cb = MagicMock(side_effect=RuntimeError("boom"))
    lis = _PriceListener("EPIC", cb)
    # must not raise
    lis.onItemUpdate(_fake_update())
    cb.assert_called_once()


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


def test_utm_to_iso_formats_correctly():
    ts = _utm_to_iso("1747737000000")
    assert "T" in ts
    assert ts.endswith("Z")
    assert len(ts) == len("2025-01-01T00:00:00.000Z")


def test_utm_to_iso_fallback_on_empty():
    ts = _utm_to_iso("")
    assert "T" in ts
    assert ts.endswith("Z")


def test_utm_to_iso_fallback_on_invalid():
    ts = _utm_to_iso("not-a-number")
    assert "T" in ts
    assert ts.endswith("Z")
