"""Step 4 — Gate 4 sizing (``select_risk_pct`` + ``compute_size``).

Pure functions; all mocked, no network, no real broker/credentials. Envelopes are
the duck-typed ``_FakeEnv`` from conftest; the risk level comes from ``FakeDB``.

Round numbers are chosen so the size arithmetic is exact: with ``ask=1000`` and a
1.0% fraction, ``available × 0.01 / 1000`` gives a clean 0.1-step size.
"""

from __future__ import annotations

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
    account, price, info = _account(100_000), _price(1000), _market_info(0.1)

    cons_size, cons_reason = compute_size(
        account, price, info, config.risk_pct_conservative, config
    )
    aggr_size, aggr_reason = compute_size(
        account, price, info, config.risk_pct_aggressive, config
    )

    # 0.5% of 100k / 1000 = 0.5 ; 1.0% of 100k / 1000 = 1.0
    assert (cons_size, cons_reason) == (0.5, None)
    assert (aggr_size, aggr_reason) == (1.0, None)
    assert aggr_size > cons_size


# --- compute_size: round DOWN to 0.1 --------------------------------------


def test_size_rounds_down_to_tenth(config: ExecutionConfig) -> None:
    # 1.0% of 137_000 / 1000 = 1.37 -> rounded DOWN to 0.1 step = 1.3
    size, reason = compute_size(
        _account(137_000), _price(1000), _market_info(0.1), 1.0, config
    )
    assert reason is None
    assert size == 1.3


# --- compute_size: below min_deal_size is a no-trade ----------------------


def test_size_below_min_deal_size_rejects(config: ExecutionConfig) -> None:
    # 1.0% of 200_000 / 18_000 = 0.111 -> 0.1, below a 0.5 min -> no trade
    size, reason = compute_size(
        _account(200_000), _price(18_000), _market_info(0.5), 1.0, config
    )
    assert (size, reason) == (0.0, "below_min_deal_size")


def test_size_no_upward_clamp_when_below_min(config: ExecutionConfig) -> None:
    # Never bump a sub-min size up to min_deal_size — it stays a no-trade.
    size, reason = compute_size(
        _account(100_000), _price(1000), _market_info(5.0), 1.0, config
    )
    # 1.0 computed but min is 5.0 -> rejected, not clamped to 5.0
    assert (size, reason) == (0.0, "below_min_deal_size")


# --- compute_size: available read path & zero balance ---------------------


def test_available_drives_the_size(config: ExecutionConfig) -> None:
    # 1.0% of 50k / 1000 = 0.5 ; 1.0% of 150k / 1000 = 1.5 (both land on the 0.1 grid)
    small, _ = compute_size(_account(50_000), _price(1000), _market_info(0.1), 1.0, config)
    large, _ = compute_size(_account(150_000), _price(1000), _market_info(0.1), 1.0, config)
    assert small == 0.5
    assert large == 1.5


def test_zero_balance_is_no_trade(config: ExecutionConfig) -> None:
    size, reason = compute_size(
        _account(0), _price(1000), _market_info(0.1), 1.0, config
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
