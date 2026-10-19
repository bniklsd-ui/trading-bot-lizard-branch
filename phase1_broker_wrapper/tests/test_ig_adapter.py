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


# IG signals allowance exhaustion as 403 (error.public-api.exceeded-*-allowance),
# not 429 — it must take the same retry path, NOT map to AUTH_ERROR
# (live finding 2026-07-06: discovery burst → misleading AUTH_ERROR fail-closed).

_ALLOWANCE_BODY = {"errorCode": "error.public-api.exceeded-api-key-allowance"}


def test_403_allowance_retries_like_429():
    sleeps = []
    a = _adapter_with_sleep(sleeps)
    with patch.object(a._session, "request") as req:
        req.side_effect = [
            _mock_response(status=403, json_body=_ALLOWANCE_BODY),
            _mock_response(status=200, json_body={"snapshot": {
                "bid": 18000.0, "offer": 18001.0, "marketStatus": "TRADEABLE",
                "updateTime": "2026-05-14T12:00:00Z",
            }}),
        ]
        env = a.get_price("IX.D.DAX.IFMM.IP")

    assert env.ok is True
    assert sleeps == [1.0]
    assert req.call_count == 2


def test_403_allowance_exhausts_to_rate_limit_not_auth_error():
    sleeps = []
    a = _adapter_with_sleep(sleeps)
    with patch.object(a._session, "request") as req:
        req.return_value = _mock_response(status=403, json_body=_ALLOWANCE_BODY)
        env = a.get_price("IX.D.DAX.IFMM.IP")

    assert env.ok is False
    assert env.error["code"] == "RATE_LIMIT"  # not AUTH_ERROR — pacing, not credentials
    assert sleeps == [1.0, 2.0]
    assert req.call_count == 3


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
        "margin_factor", "margin_factor_unit",
    }


def test_get_market_info_extracts_margin_factor():
    """Phase 16 D3.1 (L7 / AK11): ``marginFactor`` is parsed to float, ``marginFactorUnit`` is the raw IG unit string.

    Confirms the value-side path (the notional-cap math in sizing lives in Phase 5):
    a 5 %/POINTS body yields ``margin_factor == 5.0`` and ``margin_factor_unit == "PERCENTAGE"``
    in the envelope ``data``; a body with the fields absent yields ``None`` (no crash,
    no fallback to 0.0 — Phase-5 sizing treats ``None`` as "no margin cap, use the
    leverage cap"). Mirrors the probe (2026-09-07, DAX marginFactor=5 PERCENTAGE).
    """
    a = _authed_adapter()
    with patch.object(a._session, "request") as req:
        req.return_value = _mock_response(json_body=_market_info_body(
            marginFactor=5, marginFactorUnit="PERCENTAGE",
        ))
        env = a.get_market_info("IX.D.DAX.IFMM.IP")

    assert env.ok is True
    assert env.data["margin_factor"] == 5.0
    assert env.data["margin_factor_unit"] == "PERCENTAGE"


def test_get_market_info_missing_margin_factor_fields_are_none_not_crash():
    """A body without ``marginFactor`` / ``marginFactorUnit`` (e.g. a future non-CFD instrument)
    yields ``None`` for both — sizing's "fall back to the leverage cap" path is the consumer.
    """
    a = _authed_adapter()
    with patch.object(a._session, "request") as req:
        req.return_value = _mock_response(json_body=_market_info_body())
        env = a.get_market_info("IX.D.FTSE.IFD.IP")

    assert env.ok is True
    assert env.data["margin_factor"] is None
    assert env.data["margin_factor_unit"] is None


# --- Step 3 test backfill (Phase 1 hardening plan §5) ------------------------
# Priority order per the plan: bars/ohlcv (P9 IGBarProvider's regression guard)
# first, then transactions, search/account/positions, open_position lifecycle,
# reconcile, _poll_confirms timeout. Real Envelope data shapes, not just status.

from broker_wrapper.adapters.ig_adapter import _parse_bar, _parse_transaction  # noqa: E402


# -- _parse_bar / get_ohlcv (highest live risk — P9's IGBarProvider depends on this shape) --


def test_parse_bar_mid_of_bid_and_ask():
    bar = _parse_bar({
        "snapshotTime": "2026/07/04 12:00:00",
        "openPrice": {"bid": 18000.0, "ask": 18002.0},
        "highPrice": {"bid": 18010.0, "ask": 18012.0},
        "lowPrice": {"bid": 17990.0, "ask": 17992.0},
        "closePrice": {"bid": 18005.0, "ask": 18007.0},
        "lastTradedVolume": 123,
    })
    assert bar.open == pytest.approx(18001.0)
    assert bar.high == pytest.approx(18011.0)
    assert bar.low == pytest.approx(17991.0)
    assert bar.close == pytest.approx(18006.0)
    assert bar.volume == 123.0


def test_parse_bar_missing_one_side_falls_back_to_other():
    bar = _parse_bar({
        "snapshotTime": "2026/07/04 12:00:00",
        "openPrice": {"bid": 18000.0, "ask": 0},
        "highPrice": {"ask": 18012.0},
        "lowPrice": {},
        "closePrice": None,
        "lastTradedVolume": 0,
    })
    assert bar.open == 18000.0       # bid-only (ask falsy) -> bid
    assert bar.high == 18012.0       # no bid key -> ask
    assert bar.low == 0.0            # empty dict -> 0.0
    assert bar.close == 0.0          # None obj -> 0.0
    assert bar.volume == 0.0


def test_parse_bar_prefers_snapshot_time_utc_over_local_snapshot_time():
    """Phase 17 B-1 (D1): ``snapshotTime`` is the account's LOCAL time (Europe/Berlin,
    +2 h CEST, measured 2026-10-17) and ``normalize_bar_ts`` stored it as UTC — every
    IG REST bar landed in the future (D1: 3730 `source='ig'` rows with `ts_utc` 2 h
    ahead of bar time, divergence sampler 233/233 `no_comparator`, F1 gate blind).

    IG emits both fields. With both present, ``_parse_bar`` must take the UTC ISO
    one verbatim — not the local-time string. If only ``snapshotTime`` is present
    (older IG accounts or older proxies), the local-time string is still used as
    a fallback so existing fixtures stay green.
    """
    # Both fields present: prefer UTC ISO.
    bar = _parse_bar({
        "snapshotTime": "2026/10/19 17:35:00",          # Europe/Berlin local
        "snapshotTimeUTC": "2026-10-19T15:35:00",       # UTC ISO (correct)
        "openPrice": {"bid": 24900.0, "ask": 24901.0},
        "highPrice": {"bid": 24910.0, "ask": 24911.0},
        "lowPrice": {"bid": 24890.0, "ask": 24891.0},
        "closePrice": {"bid": 24905.0, "ask": 24906.0},
        "lastTradedVolume": 1,
    })
    assert bar.timestamp == "2026-10-19T15:35:00"

    # Only ``snapshotTime`` present: existing fallback (local-time string) — must stay green.
    bar_local_only = _parse_bar({
        "snapshotTime": "2026/07/04 12:00:00",
        "openPrice": {"bid": 18000.0, "ask": 18001.0},
        "highPrice": {"bid": 18010.0, "ask": 18011.0},
        "lowPrice": {"bid": 17990.0, "ask": 17991.0},
        "closePrice": {"bid": 18005.0, "ask": 18006.0},
        "lastTradedVolume": 0,
    })
    assert bar_local_only.timestamp == "2026/07/04 12:00:00"

    # Only ``snapshotTimeUTC`` present: that string is used verbatim.
    bar_utc_only = _parse_bar({
        "snapshotTimeUTC": "2026-10-19T15:35:00",
        "openPrice": {"bid": 1.0, "ask": 1.0},
        "highPrice": {"bid": 1.0, "ask": 1.0},
        "lowPrice": {"bid": 1.0, "ask": 1.0},
        "closePrice": {"bid": 1.0, "ask": 1.0},
        "lastTradedVolume": 0,
    })
    assert bar_utc_only.timestamp == "2026-10-19T15:35:00"


def test_get_ohlcv_happy_path_envelope_shape():
    """The exact shape P9's IGBarProvider (external_data/providers.py) relies on."""
    a = _authed_adapter()
    with patch.object(a._session, "request") as req:
        req.return_value = _mock_response(json_body={
            "prices": [{
                "snapshotTime": "2026/07/04 12:00:00",
                "openPrice": {"bid": 18000.0, "ask": 18002.0},
                "highPrice": {"bid": 18010.0, "ask": 18012.0},
                "lowPrice": {"bid": 17990.0, "ask": 17992.0},
                "closePrice": {"bid": 18005.0, "ask": 18007.0},
                "lastTradedVolume": 42,
            }],
            "metadata": {"allowance": {"remainingAllowance": 9999}},
        })
        env = a.get_ohlcv("IX.D.DAX.IFMM.IP", "MINUTE_5", 1)

    assert env.ok is True
    assert env.data["allowance"] == {"remainingAllowance": 9999}
    bars = env.data["bars"]
    assert len(bars) == 1
    b = bars[0]
    assert set(b.keys()) == {"timestamp", "open", "high", "low", "close", "volume"}
    assert b["close"] == pytest.approx(18006.0)
    assert b["volume"] == 42.0


def test_get_historical_ohlcv_happy_path():
    a = _authed_adapter()
    with patch.object(a._session, "request") as req:
        req.return_value = _mock_response(json_body={
            "prices": [{
                "snapshotTime": "2026/07/01 09:00:00",
                "openPrice": {"bid": 100.0, "ask": 100.0},
                "highPrice": {"bid": 101.0, "ask": 101.0},
                "lowPrice": {"bid": 99.0, "ask": 99.0},
                "closePrice": {"bid": 100.5, "ask": 100.5},
                "lastTradedVolume": 5,
            }],
            "metadata": {"allowance": {}},
        })
        env = a.get_historical_ohlcv(
            "IX.D.DAX.IFMM.IP", "2026-07-01T00:00:00", "2026-07-02T00:00:00", "DAY",
        )

    assert env.ok is True
    assert len(env.data["bars"]) == 1
    assert env.data["bars"][0]["close"] == 100.5


def test_get_historical_ohlcv_rejects_invalid_resolution():
    a = _adapter()
    with pytest.raises(ValueError):
        a.get_historical_ohlcv("X", "2026-01-01", "2026-01-02", "BOGUS")


# -- get_trade_history / _parse_transaction (signed size, currency stripping) --


def test_parse_transaction_signed_size_and_currency_stripping():
    tx = _parse_transaction({
        "reference": "T1", "instrumentName": "Germany 40",
        "size": "-1.0", "openLevel": "18000.0", "closeLevel": "18010.0",
        "profitAndLoss": "E12.34", "currency": "EUR",
        "openDateUtc": "2026-07-01T09:00:00", "dateUtc": "2026-07-01T10:00:00",
        "transactionType": "WITH",
    })
    assert tx.size == -1.0
    assert tx.profit_loss == pytest.approx(12.34)
    assert tx.currency == "EUR"
    assert tx.transaction_type == "WITH"


def test_parse_transaction_missing_fields_are_none_not_crash():
    tx = _parse_transaction({"reference": "T2"})
    assert tx.size is None
    assert tx.open_level is None
    assert tx.profit_loss is None


def test_get_trade_history_happy_path():
    a = _authed_adapter()
    with patch.object(a._session, "request") as req:
        req.return_value = _mock_response(json_body={
            "transactions": [{
                "reference": "T1", "instrumentName": "Germany 40",
                "size": "-1.0", "openLevel": "18000.0", "closeLevel": "18010.0",
                "profitAndLoss": "E12.34", "currency": "EUR",
                "openDateUtc": "2026-07-01T09:00:00", "dateUtc": "2026-07-01T10:00:00",
                "transactionType": "WITH",
            }],
        })
        env = a.get_trade_history(days=1)

    assert env.ok is True
    assert len(env.data["transactions"]) == 1
    assert env.data["transactions"][0]["profit_loss"] == pytest.approx(12.34)


def test_get_trade_history_rejects_invalid_days():
    a = _adapter()
    with pytest.raises(ValueError):
        a.get_trade_history(days=0)
    with pytest.raises(ValueError):
        a.get_trade_history(days=366)


# -- search_markets happy path -------------------------------------------------


def test_search_markets_happy_path_maps_fields():
    a = _authed_adapter()
    with patch.object(a._session, "request") as req:
        req.return_value = _mock_response(json_body={
            "markets": [{
                "epic": "IX.D.DAX.IFMM.IP", "instrumentName": "Germany 40",
                "instrumentType": "INDICES", "expiry": "-",
                "marketStatus": "TRADEABLE", "bid": 18000.0, "offer": 18002.0,
            }],
        })
        env = a.search_markets("Germany 40")

    assert env.ok is True
    assert env.data["query"] == "Germany 40"
    r = env.data["results"][0]
    assert r["epic"] == "IX.D.DAX.IFMM.IP"
    assert r["type"] == "INDICES"
    assert r["market_status"] == "TRADEABLE"
    assert r["bid"] == 18000.0
    assert r["ask"] == 18002.0


# -- get_account happy path + fallback ----------------------------------------


def test_get_account_matches_configured_account_id():
    a = _authed_adapter()
    with patch.object(a._session, "request") as req:
        req.return_value = _mock_response(json_body={
            "accounts": [
                {"accountId": "OTHER", "balance": {"balance": 1.0, "available": 1.0,
                                                    "profitLoss": 0.0}, "currency": "EUR"},
                {"accountId": "A1", "balance": {"balance": 1000.0, "available": 900.0,
                                                 "profitLoss": 50.0}, "currency": "EUR"},
            ],
        })
        env = a.get_account()

    assert env.ok is True
    assert env.data["account_id"] == "A1"
    assert env.data["balance"] == 1000.0
    assert env.data["available"] == 900.0
    assert env.data["profit_loss"] == 50.0


def test_get_account_falls_back_to_first_when_no_id_match():
    a = _authed_adapter()
    with patch.object(a._session, "request") as req:
        req.return_value = _mock_response(json_body={
            "accounts": [
                {"accountId": "OTHER", "balance": {"balance": 1.0, "available": 1.0,
                                                    "profitLoss": 0.0}, "currency": "EUR"},
            ],
        })
        env = a.get_account()

    assert env.ok is True
    assert env.data["account_id"] == "OTHER"


def test_get_account_no_accounts_returns_protocol_error():
    a = _authed_adapter()
    with patch.object(a._session, "request") as req:
        req.return_value = _mock_response(json_body={"accounts": []})
        env = a.get_account()

    assert env.ok is False
    assert env.error["code"] == "PROTOCOL_ERROR"


# -- get_open_positions / _parse_position -------------------------------------


def test_get_open_positions_happy_path():
    a = _authed_adapter()
    with patch.object(a._session, "request") as req:
        req.return_value = _mock_response(json_body=_positions_body(
            deal_id="D9", direction="SELL", size=2.0, level=18000.0,
        ))
        env = a.get_open_positions()

    assert env.ok is True
    p = env.data["positions"][0]
    assert p["deal_id"] == "D9"
    assert p["direction"] == "SELL"
    assert p["size"] == 2.0
    assert p["open_level"] == 18000.0


def test_parse_position_missing_optional_fields():
    from broker_wrapper.adapters.ig_adapter import _parse_position
    pos = _parse_position({"position": {"dealId": "D1"}, "market": {}})
    assert pos.deal_id == "D1"
    assert pos.epic == ""
    assert pos.direction == "BUY"  # IG default when absent
    assert pos.stop_level is None
    assert pos.limit_level is None


# -- open_position lifecycle (submit -> poll confirms) ------------------------


def test_open_position_accepted_happy_path():
    a = _authed_adapter()
    with patch.object(a._session, "request") as req:
        req.side_effect = [
            _mock_response(json_body={"dealReference": "bot-1"}),  # POST /positions/otc
            _mock_response(json_body={  # GET /confirms/{ref}
                "dealStatus": "ACCEPTED", "dealId": "D1", "level": 18000.0,
            }),
        ]
        env = a.open_position("IX.D.DAX.IFMM.IP", "BUY", 1.0)

    assert env.ok is True
    assert env.data["status"] == "ACCEPTED"
    assert env.data["deal_id"] == "D1"
    assert env.data["level"] == 18000.0
    assert env.data["deal_reference"].startswith("bot-")


def test_open_position_rejected_surfaces_reason():
    a = _authed_adapter()
    with patch.object(a._session, "request") as req:
        req.side_effect = [
            _mock_response(json_body={"dealReference": "bot-2"}),
            _mock_response(json_body={
                "dealStatus": "REJECTED", "reason": "INSUFFICIENT_FUNDS",
            }),
        ]
        env = a.open_position("IX.D.DAX.IFMM.IP", "SELL", 1.0)

    assert env.ok is True  # submission itself succeeded; REJECTED is a valid outcome
    assert env.data["status"] == "REJECTED"
    assert env.data["reason"] == "INSUFFICIENT_FUNDS"
    assert env.data["level"] is None


# -- reconcile_positions --------------------------------------------------------


def test_reconcile_positions_present_missing_unexpected():
    a = _authed_adapter()
    with patch.object(a._session, "request") as req:
        req.return_value = _mock_response(json_body={
            "positions": [
                {"position": {"dealId": "D1", "dealReference": "ref-1", "direction": "BUY",
                              "size": 1.0, "level": 18000.0}, "market": {"epic": "E1"}},
                {"position": {"dealId": "D2", "dealReference": "ref-unexpected",
                              "direction": "BUY", "size": 1.0, "level": 18000.0},
                 "market": {"epic": "E1"}},
            ],
        })
        env = a.reconcile_positions(expected_references=["ref-1", "ref-missing"])

    assert env.ok is True
    assert env.data["present"] == ["ref-1"]
    assert env.data["missing"] == ["ref-missing"]
    assert env.data["unexpected"] == ["ref-unexpected"]
    assert env.data["broker_position_count"] == 2


def test_reconcile_positions_without_expected_references_omits_diff_keys():
    a = _authed_adapter()
    with patch.object(a._session, "request") as req:
        req.return_value = _mock_response(json_body={"positions": []})
        env = a.reconcile_positions()

    assert env.ok is True
    assert env.data["broker_position_count"] == 0
    assert "present" not in env.data


# -- _poll_confirms timeout path (no real sleeping — time module mocked) ------


def test_poll_confirms_timeout_returns_pending():
    a = _authed_adapter()
    fake_time = {"t": 0.0}
    with patch("broker_wrapper.adapters.ig_adapter.time.monotonic",
               side_effect=lambda: fake_time["t"]), \
         patch("broker_wrapper.adapters.ig_adapter.time.sleep",
               side_effect=lambda s: fake_time.__setitem__("t", fake_time["t"] + s)), \
         patch.object(a._session, "request") as req:
        req.return_value = _mock_response(json_body={"dealStatus": "PENDING"})
        body = a._poll_confirms("bot-timeout")

    assert body["dealStatus"] == "PENDING"
    assert body["reason"] == "confirm timeout — reconcile later"


# -- _base_headers / _request 403 (Step 3, remaining plan §5 point 5) ---------


def test_base_headers_unauthenticated_no_session_tokens():
    a = _adapter()
    headers = a._base_headers(version="2", auth=False)
    assert headers["Version"] == "2"
    assert "CST" not in headers
    assert "X-SECURITY-TOKEN" not in headers


def test_base_headers_authenticated_includes_session_tokens():
    a = _authed_adapter()
    headers = a._base_headers(version="3", auth=True)
    assert headers["Version"] == "3"
    assert headers["CST"] == "x"
    assert headers["X-SECURITY-TOKEN"] == "y"


def test_base_headers_auth_without_session_raises():
    a = _adapter()
    with pytest.raises(AuthenticationError):
        a._base_headers(version="2", auth=True)


def test_request_403_maps_to_authentication_error():
    a = _authed_adapter()
    with patch.object(a._session, "request") as req:
        req.return_value = _mock_response(status=403, json_body={"errorCode": "forbidden"})
        env = a.get_price("IX.D.DAX.IFMM.IP")

    assert env.ok is False
    assert env.error["code"] == "AUTH_ERROR"
