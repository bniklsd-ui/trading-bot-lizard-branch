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


# --- close_position confirm-enrichment (Phase-7 lag-free P&L, 2026-06-23) ----


def _authed_adapter():
    a = _adapter()
    a._cst = "x"; a._security_token = "y"
    from datetime import datetime, timezone, timedelta
    a._session_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    return a


def _positions_body(deal_id="D1", direction="BUY", size=19.6, level=24968.9):
    return {"positions": [{
        "position": {"dealId": deal_id, "direction": direction, "size": size, "level": level},
        "market": {"epic": "IX.D.DAX.IFMM.IP"},
    }]}


def test_close_position_enriches_with_confirm_level_and_profit():
    """The close polls /confirms and surfaces the realised close level + P&L."""
    a = _authed_adapter()
    with patch.object(a._session, "request") as req:
        req.side_effect = [
            _mock_response(json_body=_positions_body(deal_id="D1", direction="BUY")),
            _mock_response(json_body={"dealReference": "close-ref-1"}),
            _mock_response(json_body={
                "dealStatus": "ACCEPTED", "level": 24990.0,
                "profit": 42.0, "profitCurrency": "EUR", "dealId": "D1",
            }),
        ]
        env = a.close_position("D1")

    assert env.ok is True
    assert env.data["deal_id"] == "D1"
    assert env.data["close_level"] == 24990.0
    assert env.data["profit_loss"] == pytest.approx(42.0)
    assert env.data["profit_currency"] == "EUR"
    assert env.data["close_deal_reference"] == "close-ref-1"


def test_close_position_confirm_without_profit_sets_level_only():
    """A confirm with a level but no profit → close_level set, profit_loss None."""
    a = _authed_adapter()
    with patch.object(a._session, "request") as req:
        req.side_effect = [
            _mock_response(json_body=_positions_body()),
            _mock_response(json_body={"dealReference": "close-ref-2"}),
            _mock_response(json_body={"dealStatus": "ACCEPTED", "level": 24990.0}),
        ]
        env = a.close_position("D1")

    assert env.ok is True
    assert env.data["close_level"] == 24990.0
    assert env.data["profit_loss"] is None


def test_close_position_confirm_failure_is_best_effort():
    """A failing confirm lookup must NOT turn an accepted close into an error."""
    a = _authed_adapter()
    with patch.object(a._session, "request") as req:
        req.side_effect = [
            _mock_response(json_body=_positions_body()),
            _mock_response(json_body={"dealReference": "close-ref-3"}),
            _mock_response(status=500, json_body={"errorCode": "server.error"}),
        ]
        env = a.close_position("D1")

    assert env.ok is True  # the close itself succeeded
    assert env.data["close_level"] is None
    assert env.data["profit_loss"] is None
    assert env.data["close_deal_reference"] == "close-ref-3"


def test_disconnect_idempotent_when_not_connected():
    a = _adapter()
    env = a.disconnect()
    assert env.ok is True
    assert env.data["already_disconnected"] is True


# --- 429 retry/backoff in _request (Phase 1 hardening, Step 1) ---------------


def _adapter_with_sleep(sleeps, **kwargs):
    a = IGAdapter(
        username="u", password="p", api_key="k", account_id="A1",
        demo=True, request_timeout=1.0, max_retries=0,
        sleep_fn=lambda s: sleeps.append(s),
        **kwargs,
    )
    a._cst = "x"; a._security_token = "y"
    from datetime import datetime, timezone, timedelta
    a._session_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    return a


def test_429_succeeds_after_one_retry():
    sleeps = []
    a = _adapter_with_sleep(sleeps)
    with patch.object(a._session, "request") as req:
        req.side_effect = [
            _mock_response(status=429, json_body={"errorCode": "rate-limit"}),
            _mock_response(status=200, json_body={"snapshot": {
                "bid": 18000.0, "offer": 18001.0, "marketStatus": "TRADEABLE",
                "updateTime": "2026-05-14T12:00:00Z",
            }}),
        ]
        env = a.get_price("IX.D.DAX.IFMM.IP")

    assert env.ok is True
    assert sleeps == [1.0]
    assert req.call_count == 2


def test_429_exhausts_retries_and_raises_rate_limit_error():
    sleeps = []
    a = _adapter_with_sleep(sleeps)
    with patch.object(a._session, "request") as req:
        req.return_value = _mock_response(status=429, json_body={"errorCode": "rate-limit"})
        env = a.get_price("IX.D.DAX.IFMM.IP")

    assert env.ok is False
    assert env.error["code"] == "RATE_LIMIT"
    assert sleeps == [1.0, 2.0]
    assert req.call_count == 3  # initial + 2 retries (retry_429_attempts default = 2)


def test_429_retry_opt_out_raises_immediately():
    sleeps = []
    a = _adapter_with_sleep(sleeps, retry_429_attempts=0)
    with patch.object(a._session, "request") as req:
        req.return_value = _mock_response(status=429, json_body={"errorCode": "rate-limit"})
        env = a.get_price("IX.D.DAX.IFMM.IP")

    assert env.ok is False
    assert env.error["code"] == "RATE_LIMIT"
    assert sleeps == []
    assert req.call_count == 1


def test_no_sleep_on_200():
    sleeps = []
    a = _adapter_with_sleep(sleeps)
    with patch.object(a._session, "request") as req:
        req.return_value = _mock_response(status=200, json_body={"snapshot": {
            "bid": 18000.0, "offer": 18001.0, "marketStatus": "TRADEABLE",
            "updateTime": "2026-05-14T12:00:00Z",
        }})
        env = a.get_price("IX.D.DAX.IFMM.IP")

    assert env.ok is True
    assert sleeps == []


def test_401_relogin_path_unchanged_by_429_retry_addition():
    """Regression guard: the 401 re-login retry (previously untested) still works
    alongside the new retry_429_count plumbing threaded through every recursive call."""
    a = _authed_adapter()
    with patch.object(a._session, "request") as req, \
         patch.object(a._session, "post") as post:
        req.side_effect = [
            _mock_response(status=401, json_body={"errorCode": "expired"}),
            _mock_response(status=200, json_body={"snapshot": {
                "bid": 18000.0, "offer": 18001.0, "marketStatus": "TRADEABLE",
                "updateTime": "2026-05-14T12:00:00Z",
            }}),
        ]
        post.return_value = _mock_response(
            status=200,
            headers={"CST": "cst-2", "X-SECURITY-TOKEN": "tok-2"},
            json_body={"currentAccountId": "A1"},
        )
        env = a.get_price("IX.D.DAX.IFMM.IP")

    assert env.ok is True
    assert a._cst == "cst-2"
    assert req.call_count == 2


# --- get_market_info pip/contract field passthrough (Phase 1 hardening, Step 2) ----


def _market_info_body(**instr_extra):
    return {
        "instrument": {
            "name": "France 40", "type": "INDICES", "currencies": [{"code": "EUR"}],
            "expiry": "-", "lotSize": 1.0,
            **instr_extra,
        },
        "dealingRules": {"minDealSize": {"value": 0.5}},
        "snapshot": {"marketStatus": "TRADEABLE"},
    }


def test_get_market_info_passes_through_pip_fields():
    a = _authed_adapter()
    with patch.object(a._session, "request") as req:
        req.return_value = _mock_response(json_body=_market_info_body(
            valueOfOnePip="1", onePipMeans="1 index point", contractSize="1",
        ))
        env = a.get_market_info("IX.D.FTSE.IFD.IP")

    assert env.ok is True
    assert env.data["value_of_one_pip"] == "1"
    assert env.data["one_pip_means"] == "1 index point"
    assert env.data["contract_size"] == "1"


def test_get_market_info_missing_pip_fields_are_none_not_crash():
    a = _authed_adapter()
    with patch.object(a._session, "request") as req:
        req.return_value = _mock_response(json_body=_market_info_body())
        env = a.get_market_info("IX.D.FTSE.IFD.IP")

    assert env.ok is True
    assert env.data["value_of_one_pip"] is None
    assert env.data["one_pip_means"] is None
    assert env.data["contract_size"] is None


def test_get_market_info_existing_fields_byte_identical():
    a = _authed_adapter()
    with patch.object(a._session, "request") as req:
        req.return_value = _mock_response(json_body=_market_info_body())
        env = a.get_market_info("IX.D.FTSE.IFD.IP")

    assert env.ok is True
    assert env.data["name"] == "France 40"
    assert env.data["instrument_type"] == "INDICES"
    assert env.data["currency"] == "EUR"
    assert env.data["expiry"] is None
    assert env.data["min_deal_size"] == 0.5
    assert env.data["lot_size"] == 1.0
    assert env.data["market_status"] == "TRADEABLE"


def test_get_market_info_to_dict_roundtrip_keys():
    a = _authed_adapter()
    with patch.object(a._session, "request") as req:
        req.return_value = _mock_response(json_body=_market_info_body(
            valueOfOnePip="1", contractSize="1",
        ))
        env = a.get_market_info("IX.D.FTSE.IFD.IP")

    assert set(env.data.keys()) == {
        "epic", "name", "instrument_type", "currency", "expiry",
        "min_deal_size", "lot_size", "market_status",
        "value_of_one_pip", "one_pip_means", "contract_size",
    }
