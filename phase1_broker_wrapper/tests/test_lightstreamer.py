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
    _CandleListener,
    _PriceListener,
    _utm_to_iso,
    _CHART_FIELDS,
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


def _fake_candle_update(
    utm: str,
    *,
    bid_o: str = "100.0", bid_h: str = "101.0", bid_l: str = "99.5", bid_c: str = "100.5",
    ofr_o: str = "100.2", ofr_h: str = "101.2", ofr_l: str = "99.7", ofr_c: str = "100.7",
    cons_end: str = "0",
    cons_tick_count: str = "5",
) -> MagicMock:
    """Mock SDK ItemUpdate for a CHART candle subscription."""
    values = {
        "UTM": utm, "CONS_END": cons_end, "CONS_TICK_COUNT": cons_tick_count,
        "BID_OPEN": bid_o, "BID_HIGH": bid_h, "BID_LOW": bid_l, "BID_CLOSE": bid_c,
        "OFR_OPEN": ofr_o, "OFR_HIGH": ofr_h, "OFR_LOW": ofr_l, "OFR_CLOSE": ofr_c,
    }
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


# ---------- Phase 13 §6 B1: CHART candle subscription --------------------------


def test_subscribe_candles_uses_chart_item_and_full_field_list():
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
        c.subscribe_candles("IX.D.DAX.IFMM.IP", cb)
    # Item-String exakt, Field-Liste exakt, MERGE-Modus.
    sub_ctor.assert_called_once_with(
        "MERGE",
        ["CHART:ACC1:IX.D.DAX.IFMM.IP:1MINUTE"],
        list(_CHART_FIELDS),
    )
    # CHART subscription does NOT call setDataAdapter (the SDK default
    # is correct; if that ever breaks, the B0 probe fails loud, not
    # silent in production).
    fake_sub.setDataAdapter.assert_not_called()
    fake_sub.addListener.assert_called_once()
    fake_client.subscribe.assert_called_once_with(fake_sub)


def test_subscribe_candles_before_start_defers_until_start():
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
        c.subscribe_candles("IX.D.DAX.IFMM.IP", cb)  # no client yet
        fake_client.subscribe.assert_not_called()
        c.start()                                       # subscribes the backlog
    fake_client.subscribe.assert_called_once_with(fake_sub)


def test_unsubscribe_candles_removes_and_calls_sdk():
    c = _client()
    fake_client = MagicMock()
    with patch(
        "broker_wrapper.streaming.ig_lightstreamer.LightstreamerClient",
        return_value=fake_client,
    ), patch(
        "broker_wrapper.streaming.ig_lightstreamer.Subscription",
        return_value=MagicMock(),
    ):
        c.start()
        c.subscribe_candles("EPIC", lambda c: None)
        c.unsubscribe_candles("EPIC")
    assert "EPIC" not in c._candle_subs
    assert "EPIC" not in c._chart_subs
    fake_client.unsubscribe.assert_called_once()
    # idempotent
    c.unsubscribe_candles("EPIC")


def test_stop_clears_both_price_and_candle_subscriptions():
    c = _client()
    fake_client = MagicMock()
    with patch(
        "broker_wrapper.streaming.ig_lightstreamer.LightstreamerClient",
        return_value=fake_client,
    ), patch(
        "broker_wrapper.streaming.ig_lightstreamer.Subscription",
        return_value=MagicMock(),
    ):
        c.start()
        c.subscribe("EPIC", lambda t: None)
        c.subscribe_candles("EPIC", lambda c: None)
        c.stop()
    # stop() must unsubscribe BOTH the price and candle subs.
    assert fake_client.unsubscribe.call_count == 2
    assert c._subs == {}
    assert c._chart_subs == {}


def test_candle_listener_emits_on_cons_end_1_with_mid_ohlc():
    """CONS_END == "1" fires the callback exactly once, with bid/ofr mid OHLC."""
    cb = MagicMock()
    lis = _CandleListener("IX.D.DAX.IFMM.IP", cb)
    # Partial update #1: no CONS_END yet → no callback.
    lis.onItemUpdate(_fake_candle_update(
        utm="1747737000000", bid_o="100.0", ofr_o="100.2", cons_end="0",
    ))
    cb.assert_not_called()
    # Partial update #2: bid_high + bid_low + ofr_high + ofr_low arrive, still no CONS_END.
    lis.onItemUpdate(_fake_candle_update(
        utm="1747737000000", bid_h="101.0", bid_l="99.5", ofr_h="101.2", ofr_l="99.7", cons_end="0",
    ))
    cb.assert_not_called()
    # Final update: CONS_END == "1" + bid_close + ofr_close → one callback.
    lis.onItemUpdate(_fake_candle_update(
        utm="1747737000000", bid_c="100.5", ofr_c="100.7", cons_end="1",
    ))
    cb.assert_called_once()
    candle = cb.call_args[0][0]
    assert candle.epic == "IX.D.DAX.IFMM.IP"
    assert candle.complete is True
    # Mid: open = (100.0 + 100.2) / 2 = 100.1
    assert candle.open == pytest.approx(100.1)
    assert candle.high == pytest.approx(101.1)   # (101.0 + 101.2)/2
    assert candle.low == pytest.approx(99.6)    # (99.5 + 99.7)/2
    assert candle.close == pytest.approx(100.6)  # (100.5 + 100.7)/2
    assert candle.tick_count == 5
    assert "T" in candle.ts_utc and candle.ts_utc.endswith("Z")


def test_candle_listener_does_not_emit_on_cons_end_0():
    cb = MagicMock()
    lis = _CandleListener("EPIC", cb)
    # Every field delivered, but CONS_END stays 0 → no callback (candle not final).
    lis.onItemUpdate(_fake_candle_update(utm="1747737000000", cons_end="0"))
    lis.onItemUpdate(_fake_candle_update(utm="1747737000000", cons_end="0"))
    cb.assert_not_called()


def test_candle_listener_swallows_missing_or_non_numeric_field():
    """A missing/non-numeric field must not crash the recorder for the rest of
    the day; the listener logs and skips the candle."""
    cb = MagicMock()
    lis = _CandleListener("EPIC", cb)
    # Cons_end=1, but BID_OPEN missing → KeyError caught, no callback.
    lis.onItemUpdate(_fake_candle_update(utm="1747737000000", cons_end="1", bid_o=""))
    cb.assert_not_called()
    # Cons_end=1, but BID_HIGH non-numeric → ValueError caught, no callback.
    lis.onItemUpdate(_fake_candle_update(utm="1747737000000", cons_end="1", bid_h="oops"))
    cb.assert_not_called()


def test_candle_listener_callback_exception_isolated():
    cb = MagicMock(side_effect=RuntimeError("boom"))
    lis = _CandleListener("EPIC", cb)
    # must not raise — exception is logged, the listener survives
    lis.onItemUpdate(_fake_candle_update(utm="1747737000000", cons_end="1"))
    cb.assert_called_once()
