"""Unit tests for IGAdapter — uses requests mocks, no network."""

from unittest.mock import MagicMock, patch

import pytest

from broker_wrapper.adapters.ig_adapter import IGAdapter
from broker_wrapper.exceptions import (
    AuthenticationError, EpicNotFoundError, MarketOfflineError, RateLimitError,
)


def _adapter():
    return IGAdapter(
        username="u", password="p", api_key="k", account_id="A1",
        demo=True, request_timeout=1.0, max_retries=0,
    )


def _mock_response(status=200, json_body=None, headers=None, content=True):
    m = MagicMock()
    m.status_code = status
    m.content = b"x" if content else b""
    m.headers = headers or {}
    m.json.return_value = json_body if json_body is not None else {}
    m.text = str(json_body or "")
    return m


def test_initial_state_disconnected():
    a = _adapter()
    assert a.is_connected() is False


def test_login_success_sets_session_tokens():
    a = _adapter()
    with patch.object(a._session, "post") as post:
        post.return_value = _mock_response(
            status=200,
            headers={"CST": "cst-x", "X-SECURITY-TOKEN": "tok-y"},
            json_body={"currentAccountId": "A1"},
        )
        env = a.connect()
    assert env.ok is True
    assert a.is_connected() is True
    assert a._cst == "cst-x"
    assert a._security_token == "tok-y"


def test_login_401_returns_error_envelope():
    a = _adapter()
    with patch.object(a._session, "post") as post:
        post.return_value = _mock_response(status=401)
        env = a.connect()
    assert env.ok is False
    assert env.error["code"] == "AUTH_ERROR"
    assert a.is_connected() is False


def test_login_missing_headers_returns_error():
    a = _adapter()
    with patch.object(a._session, "post") as post:
        post.return_value = _mock_response(status=200, headers={})
        env = a.connect()
    assert env.ok is False
    assert env.error["code"] == "PROTOCOL_ERROR"


def test_get_price_maps_status_and_computes_spread():
    a = _adapter()
    a._cst = "x"; a._security_token = "y"
    from datetime import datetime, timezone, timedelta
    a._session_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    with patch.object(a._session, "request") as req:
        req.return_value = _mock_response(
            status=200,
            json_body={
                "snapshot": {
                    "bid": 18000.0, "offer": 18001.0,
                    "marketStatus": "TRADEABLE",
                    "updateTime": "2026-05-14T12:00:00Z",
                }
            },
        )
        env = a.get_price("IX.D.DAX.IFM.IP")

    assert env.ok is True
    assert env.data["bid"] == 18000.0
    assert env.data["ask"] == 18001.0
    assert env.data["spread"] == pytest.approx(1.0)
    assert env.data["market_status"] == "TRADEABLE"


def test_get_price_405_returns_market_offline_envelope():
    a = _adapter()
    a._cst = "x"; a._security_token = "y"
    from datetime import datetime, timezone, timedelta
    a._session_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    with patch.object(a._session, "request") as req:
        req.return_value = _mock_response(status=405, json_body={"errorCode": "MARKET_CLOSED"})
        env = a.get_price("IX.D.DAX.IFM.IP")

    assert env.ok is False
    assert env.error["code"] == "MARKET_OFFLINE"
    assert env.error["retryable"] is True


def test_get_price_404_maps_to_epic_not_found():
    a = _adapter()
    a._cst = "x"; a._security_token = "y"
    from datetime import datetime, timezone, timedelta
    a._session_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    with patch.object(a._session, "request") as req:
        req.return_value = _mock_response(status=404, json_body={})
        env = a.get_price("UNKNOWN")

    assert env.ok is False
    assert env.error["code"] == "EPIC_NOT_FOUND"


def test_get_ohlcv_rejects_invalid_resolution():
    a = _adapter()
    with pytest.raises(ValueError):
        a.get_ohlcv("X", "BOGUS", 10)


def test_get_ohlcv_rejects_invalid_count():
    a = _adapter()
    with pytest.raises(ValueError):
        a.get_ohlcv("X", "MINUTE", 0)
    with pytest.raises(ValueError):
        a.get_ohlcv("X", "MINUTE", 9999)


def test_open_position_validation():
    a = _adapter()
    with pytest.raises(ValueError):
        a.open_position("X", "FOO", 1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        a.open_position("X", "BUY", 0)
    with pytest.raises(ValueError):
        a.open_position("X", "BUY", 1.0, "LIMIT")  # missing level


def test_modify_position_requires_at_least_one_level():
    a = _adapter()
    with pytest.raises(ValueError):
        a.modify_position("ABC")


def test_disconnect_idempotent_when_not_connected():
    a = _adapter()
    env = a.disconnect()
    assert env.ok is True
    assert env.data["already_disconnected"] is True
