"""Step 5 — the 4 hard VETOs + ``pre_trade_check`` orchestrator.

All mocked, no network, no real order/credentials. Envelopes are the duck-typed
``_FakeEnv``; VETO 3 reads bars from a ``FakeBroker`` (``make_bars`` builds the
``get_ohlcv`` bar dicts). ``now`` is a fixed in-window timestamp.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from execution.config import ExecutionConfig
from execution.vetos import (
    pre_trade_check,
    veto_momentum,
    veto_position_conflict,
    veto_spread,
    veto_status_and_window,
)
from typing import Any, Callable

from tests.conftest import DEFAULT_EPIC, FakeBroker, _FakeEnv, make_bars


@pytest.fixture
def config() -> ExecutionConfig:
    return ExecutionConfig()


# A weekday 09:05 Europe/Berlin — comfortably inside the 09:00-17:30 window.
NOW_IN_WINDOW = datetime(2026, 6, 11, 9, 5, tzinfo=ZoneInfo("Europe/Berlin"))
NOW_OUT_OF_WINDOW = datetime(2026, 6, 11, 8, 0, tzinfo=ZoneInfo("Europe/Berlin"))


def _price(*, status: str = "TRADEABLE", spread_pct: float = 0.03, ok: bool = True) -> _FakeEnv:
    return _FakeEnv(
        ok=ok,
        data={"ask": 18000.0, "bid": 17999.0, "spread_pct": spread_pct, "market_status": status},
    )


def _positions(positions: list[dict] | None = None, *, ok: bool = True) -> _FakeEnv:
    return _FakeEnv(ok=ok, data={"positions": positions or []})


# --- VETO 1: status & window ----------------------------------------------


def test_veto_status_window_passes(config: ExecutionConfig) -> None:
    v = veto_status_and_window(_price(), NOW_IN_WINDOW, config)
    assert v.ok


def test_veto_status_window_vetoes_non_tradeable(config: ExecutionConfig) -> None:
    v = veto_status_and_window(_price(status="EDITS_ONLY"), NOW_IN_WINDOW, config)
    assert not v.ok and v.veto == "status_window"


def test_veto_status_window_vetoes_outside_window(config: ExecutionConfig) -> None:
    v = veto_status_and_window(_price(), NOW_OUT_OF_WINDOW, config)
    assert not v.ok and "window" in v.reason


def test_veto_status_window_vetoes_not_ok_env(config: ExecutionConfig) -> None:
    v = veto_status_and_window(_FakeEnv(ok=False), NOW_IN_WINDOW, config)
    assert not v.ok and v.reason == "price snapshot unavailable"


# --- VETO 2: spread --------------------------------------------------------


def test_veto_spread_passes_within_max(config: ExecutionConfig) -> None:
    v = veto_spread(_price(spread_pct=0.5), config)  # exactly at max → pass
    assert v.ok


def test_veto_spread_vetoes_above_max(config: ExecutionConfig) -> None:
    v = veto_spread(_price(spread_pct=0.6), config)
    assert not v.ok and v.veto == "spread"


def test_veto_spread_vetoes_not_ok_env(config: ExecutionConfig) -> None:
    v = veto_spread(_FakeEnv(ok=False), config)
    assert not v.ok


# --- VETO 3: momentum (get_ohlcv) -----------------------------------------


def test_veto_momentum_vetoes_buy_into_drop(config: ExecutionConfig) -> None:
    # 18000 -> 17950 = -0.278% <= -0.15% threshold
    broker = FakeBroker(ohlcv_env=_FakeEnv(ok=True, data={"bars": make_bars([18000.0, 17950.0])}))
    v = veto_momentum(broker, DEFAULT_EPIC, "BUY", config)
    assert not v.ok and v.veto == "momentum"


def test_veto_momentum_vetoes_sell_into_rally(config: ExecutionConfig) -> None:
    # 18000 -> 18050 = +0.278% >= +0.15% threshold
    broker = FakeBroker(ohlcv_env=_FakeEnv(ok=True, data={"bars": make_bars([18000.0, 18050.0])}))
    v = veto_momentum(broker, DEFAULT_EPIC, "SELL", config)
    assert not v.ok and v.veto == "momentum"


def test_veto_momentum_passes_within_threshold(config: ExecutionConfig) -> None:
    # 18000 -> 18010 = +0.056%, below 0.15% — a BUY is fine (not into a drop)
    broker = FakeBroker(ohlcv_env=_FakeEnv(ok=True, data={"bars": make_bars([18000.0, 18010.0])}))
    v = veto_momentum(broker, DEFAULT_EPIC, "BUY", config)
    assert v.ok


def test_veto_momentum_buy_passes_on_rally(config: ExecutionConfig) -> None:
    # A strong rally does NOT veto a BUY (momentum aligned) — only adverse moves veto.
    broker = FakeBroker(ohlcv_env=_FakeEnv(ok=True, data={"bars": make_bars([18000.0, 18100.0])}))
    v = veto_momentum(broker, DEFAULT_EPIC, "BUY", config)
    assert v.ok


def test_veto_momentum_vetoes_too_few_bars(config: ExecutionConfig) -> None:
    broker = FakeBroker(ohlcv_env=_FakeEnv(ok=True, data={"bars": make_bars([18000.0])}))
    v = veto_momentum(broker, DEFAULT_EPIC, "BUY", config)
    assert not v.ok and "too few bars" in v.reason


def test_veto_momentum_vetoes_not_ok_env(config: ExecutionConfig) -> None:
    broker = FakeBroker(ohlcv_env=_FakeEnv(ok=False))
    v = veto_momentum(broker, DEFAULT_EPIC, "BUY", config)
    assert not v.ok and v.reason == "ohlcv snapshot unavailable"


def test_veto_momentum_vetoes_on_raise(config: ExecutionConfig) -> None:
    broker = FakeBroker(ohlcv_raises=True)
    v = veto_momentum(broker, DEFAULT_EPIC, "BUY", config)
    assert not v.ok and "raised" in v.reason


# --- VETO 4: position conflict --------------------------------------------


def test_veto_position_conflict_vetoes_opposite(
    config: ExecutionConfig, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    candidate = make_candidate(direction="BUY", epic=DEFAULT_EPIC)
    env = _positions([{"epic": DEFAULT_EPIC, "direction": "SELL"}])
    v = veto_position_conflict(env, candidate, config)
    assert not v.ok and v.veto == "position_conflict"


def test_veto_position_conflict_vetoes_at_max_parallel(
    config: ExecutionConfig, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    # max_parallel_positions default 1; one same-direction position fills the cap.
    candidate = make_candidate(direction="BUY", epic=DEFAULT_EPIC)
    env = _positions([{"epic": DEFAULT_EPIC, "direction": "BUY"}])
    v = veto_position_conflict(env, candidate, config)
    assert not v.ok and "max_parallel_positions" in v.reason


def test_veto_position_conflict_passes_when_clear(
    config: ExecutionConfig, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    candidate = make_candidate(direction="BUY", epic=DEFAULT_EPIC)
    v = veto_position_conflict(_positions([]), candidate, config)
    assert v.ok


def test_veto_position_conflict_vetoes_not_ok_env(
    config: ExecutionConfig, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    candidate = make_candidate()
    v = veto_position_conflict(_FakeEnv(ok=False), candidate, config)
    assert not v.ok


# --- pre_trade_check orchestrator -----------------------------------------


def test_pre_trade_check_all_pass(
    config: ExecutionConfig, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    # Default FakeBroker: TRADEABLE, tight spread, flat bars, no positions.
    broker = FakeBroker()
    candidate = make_candidate(direction="BUY", epic=DEFAULT_EPIC)
    v = pre_trade_check(broker, candidate, NOW_IN_WINDOW, config)
    assert v.ok
    # all four fresh snapshots were taken
    assert broker.get_price_calls == [DEFAULT_EPIC]
    assert len(broker.get_ohlcv_calls) == 1
    assert broker.get_open_positions_calls == 1


def test_pre_trade_check_aborts_on_first_fail_before_ohlcv(
    config: ExecutionConfig, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    # A status veto must short-circuit — get_ohlcv / get_open_positions never touched.
    broker = FakeBroker(price_env=_price(status="CLOSED"))
    candidate = make_candidate(direction="BUY", epic=DEFAULT_EPIC)
    v = pre_trade_check(broker, candidate, NOW_IN_WINDOW, config)
    assert not v.ok and v.veto == "status_window"
    assert broker.get_ohlcv_calls == []
    assert broker.get_open_positions_calls == 0
