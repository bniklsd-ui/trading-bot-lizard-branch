"""Tests for the tradeable filter rules engine."""

import math

import pytest

from broker_wrapper.filters import (
    is_tradeable, FilterConfig, calc_spread_pct, calc_position_size,
)
from broker_wrapper.models import Price, MarketInfo


def _price(*, status="TRADEABLE", bid=100.0, ask=100.1):
    return Price(
        epic="X", bid=bid, ask=ask,
        spread=ask - bid, spread_pct=(ask - bid) / ask * 100,
        market_status=status, timestamp="2026-05-14T12:00:00Z",
    )


def _info(*, currency="EUR", min_size=1.0, status="TRADEABLE"):
    return MarketInfo(
        epic="X", name="DAX CFD", instrument_type="CFD",
        currency=currency, expiry=None,
        min_deal_size=min_size, lot_size=1.0,
        market_status=status,
    )


def test_passes_default_config():
    v = is_tradeable(_price(), _info())
    assert v.ok is True


def test_rejects_closed_market():
    v = is_tradeable(_price(status="CLOSED"), _info())
    assert not v.ok
    assert v.rule == "MARKET_STATUS"


def test_rejects_wide_spread():
    v = is_tradeable(_price(bid=100.0, ask=110.0), _info())
    assert not v.ok
    assert v.rule == "SPREAD_TOO_WIDE"


def test_rejects_wrong_currency():
    v = is_tradeable(_price(), _info(currency="GBP"))
    assert not v.ok
    assert v.rule == "WRONG_CURRENCY"


def test_currency_check_can_be_disabled():
    cfg = FilterConfig(require_currency=None)
    v = is_tradeable(_price(), _info(currency="GBP"), cfg)
    assert v.ok


def test_rejects_too_large_min_size():
    cfg = FilterConfig(max_min_deal_size=0.5)
    v = is_tradeable(_price(), _info(min_size=1.0), cfg)
    assert not v.ok
    assert v.rule == "MIN_SIZE_TOO_LARGE"


def test_calc_spread_pct_normal():
    assert calc_spread_pct(100.0, 100.5) == pytest.approx(0.4975, rel=1e-3)


def test_calc_spread_pct_zero_ask_returns_inf():
    assert math.isinf(calc_spread_pct(0.0, 0.0))


def test_calc_position_size_basic():
    # 1000 EUR balance × 0.08 risk = 80 EUR notional
    # at price 100 with 1 €/point → size 0.8 → rounded down to 0.8
    size = calc_position_size(
        available_balance=1000, risk_pct=0.08, price=100, point_value=1,
    )
    assert size == 0.8


def test_calc_position_size_respects_cap():
    size = calc_position_size(
        available_balance=10000, risk_pct=0.5, price=10, point_value=1, cap=1.0,
    )
    assert size == 1.0


def test_calc_position_size_zero_balance():
    assert calc_position_size(
        available_balance=0, risk_pct=0.1, price=100,
    ) == 0.0


def test_calc_position_size_rounds_down():
    # Raw size 0.87 → must round DOWN to 0.8 to stay inside budget.
    size = calc_position_size(
        available_balance=1000, risk_pct=0.087, price=100, point_value=1,
    )
    assert size == 0.8
