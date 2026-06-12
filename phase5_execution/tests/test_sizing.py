"""Step 4 — Gate 4 sizing (``select_risk_pct`` + ``compute_size``).

Pure functions; all mocked, no network, no real broker/credentials. Envelopes are
the duck-typed ``_FakeEnv`` from conftest; the risk level comes from ``FakeDB``.

Sizing model (operator decision 2026-06-12): risk-per-trade ÷ stop-distance —
``size = (balance × risk_pct) / (stop_distance_points × point_value)``, capped by
``(balance × max_leverage) / (price × point_value)``, rounded **down** to 0.1.
With the default ``stop_distance_points=30`` and ``point_value=1`` the size is
independent of the index price; round numbers are chosen so it lands exactly on the
0.1 grid (e.g. balance 1500 × 2% / 30 = 1.0).
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from execution.config import ExecutionConfig
from execution.sizing import compute_size, select_risk_pct
from tests.conftest import FakeDB, _FakeEnv


@pytest.fixture
def config() -> ExecutionConfig:
    return ExecutionConfig()


def _account(available: float) -> _FakeEnv:
    return _FakeEnv(ok=True, data={"available": available, "currency": "EUR"})


def _price(ask: float) -> _FakeEnv:
    return _FakeEnv(ok=True, data={"ask": ask, "bid": ask - 1, "market_status": "TRADEABLE"})


def _market_info(min_deal_size: float) -> _FakeEnv:
    return _FakeEnv(ok=True, data={"min_deal_size": min_deal_size, "currency": "EUR"})


# --- select_risk_pct ------------------------------------------------------


def test_select_risk_pct_conservative(config: ExecutionConfig) -> None:
    db = FakeDB(risk_level="KONSERVATIV")
    assert select_risk_pct(db, config) == config.risk_pct_conservative


def test_select_risk_pct_aggressive(config: ExecutionConfig) -> None:
    db = FakeDB(risk_level="AGGRESSIV")
    assert select_risk_pct(db, config) == config.risk_pct_aggressive


# --- compute_size: risk level drives the size -----------------------------


def test_aggressive_risk_pct_sizes_larger_than_conservative(config: ExecutionConfig) -> None:
    # stop=30, pt=1, price=18000 (cap = 1500×20/18000 = 1.66 -> not binding).
    account, price, info = _account(1500), _price(18_000), _market_info(0.1)

    cons_size, cons_reason = compute_size(
        account, price, info, config.risk_pct_conservative, config
    )
    aggr_size, aggr_reason = compute_size(
        account, price, info, config.risk_pct_aggressive, config
    )

    # cons 2% of 1500 / 30 = 1.0 ; aggr 3% of 1500 / 30 = 1.5
    assert (cons_size, cons_reason) == (1.0, None)
    assert (aggr_size, aggr_reason) == (1.5, None)
    assert aggr_size > cons_size


# --- compute_size: round DOWN to 0.1 --------------------------------------


def test_size_rounds_down_to_tenth(config: ExecutionConfig) -> None:
    # 3% of 1370 / 30 = 1.37 -> rounded DOWN to 0.1 step = 1.3
    size, reason = compute_size(
        _account(1370), _price(18_000), _market_info(0.1), 3.0, config
    )
    assert reason is None
    assert size == 1.3


# --- compute_size: ~€1K budget is tradeable (the rework's regression) -----


def test_thousand_euro_budget_is_tradeable(config: ExecutionConfig) -> None:
    # The exact bug this rework fixes: a real ~€1K account must clear min_deal_size.
    # 2% of 1000 / 30 = 0.66 -> 0.6 >= 0.5 (the old notional model rounded to 0.0).
    size, reason = compute_size(
        _account(1000), _price(18_000), _market_info(0.5), config.risk_pct_conservative, config
    )
    assert reason is None
    assert size == 0.6


# --- compute_size: below min_deal_size is a no-trade ----------------------


def test_size_below_min_deal_size_rejects(config: ExecutionConfig) -> None:
    # 2% of 500 / 30 = 0.333 -> 0.3, below a 0.5 min -> no trade
    size, reason = compute_size(
        _account(500), _price(18_000), _market_info(0.5), config.risk_pct_conservative, config
    )
    assert (size, reason) == (0.0, "below_min_deal_size")


def test_size_no_upward_clamp_when_below_min(config: ExecutionConfig) -> None:
    # Never bump a sub-min size up to min_deal_size — it stays a no-trade.
    # 2% of 1500 / 30 = 1.0 computed but min is 5.0 -> rejected, not clamped to 5.0.
    size, reason = compute_size(
        _account(1500), _price(18_000), _market_info(5.0), config.risk_pct_conservative, config
    )
    assert (size, reason) == (0.0, "below_min_deal_size")


# --- compute_size: leverage / notional cap --------------------------------


def test_leverage_cap_clips_oversized_risk() -> None:
    # A tiny stop distance on a large balance would size huge; the notional cap clips it.
    # raw = 3% of 100_000 / 1 = 3000 ; cap = 100_000 × 20 / 18_000 = 111.11 -> 111.1.
    config = replace(ExecutionConfig(), stop_distance_points=1.0)
    size, reason = compute_size(
        _account(100_000), _price(18_000), _market_info(0.1), config.risk_pct_aggressive, config
    )
    assert reason is None
    assert size == 111.1  # capped, NOT the uncapped 3000


# --- compute_size: available read path & zero balance ---------------------


def test_available_drives_the_size(config: ExecutionConfig) -> None:
    # 2% of 750 / 30 = 0.5 ; 2% of 1500 / 30 = 1.0 (both land on the 0.1 grid)
    small, _ = compute_size(_account(750), _price(18_000), _market_info(0.1), 2.0, config)
    large, _ = compute_size(_account(1500), _price(18_000), _market_info(0.1), 2.0, config)
    assert small == 0.5
    assert large == 1.0


def test_zero_balance_is_no_trade(config: ExecutionConfig) -> None:
    size, reason = compute_size(
        _account(0), _price(18_000), _market_info(0.1), 2.0, config
    )
    assert (size, reason) == (0.0, "below_min_deal_size")


# --- compute_size: fail-safe on a not-ok envelope -------------------------


def test_not_ok_account_env_is_no_trade(config: ExecutionConfig) -> None:
    size, reason = compute_size(
        _FakeEnv(ok=False), _price(1000), _market_info(0.1), 1.0, config
    )
    assert (size, reason) == (0.0, "account_snapshot_unavailable")


def test_not_ok_price_env_is_no_trade(config: ExecutionConfig) -> None:
    size, reason = compute_size(
        _account(100_000), _FakeEnv(ok=False), _market_info(0.1), 1.0, config
    )
    assert (size, reason) == (0.0, "price_snapshot_unavailable")


def test_not_ok_market_info_env_is_no_trade(config: ExecutionConfig) -> None:
    size, reason = compute_size(
        _account(100_000), _price(1000), _FakeEnv(ok=False), 1.0, config
    )
    assert (size, reason) == (0.0, "market_info_snapshot_unavailable")
