"""Tests for Module 2 — ``context_builder.build_debate_context``.

Deterministic, mocked (the ``FakeBroker`` from conftest), no network, no LLM.
Asserts the AI boundary: code reads exactly one fresh snapshot, folds it with the
candidate seed, and fails closed (``DebateError``) on any bad data — never builds
a context the agents could trade on unsafely.
"""

from __future__ import annotations

from typing import Any, Callable

import pytest

from debate import context_builder
from debate.context_builder import build_debate_context
from debate.models import DebateConfig, DebateContext, DebateError

from .conftest import DEFAULT_EPIC, FakeBroker, _FakeEnv, make_bars


CONFIG = DebateConfig()


def test_full_context_assembled(candidate: dict[str, Any], broker: FakeBroker) -> None:
    ctx = build_debate_context(candidate, broker, CONFIG)
    assert isinstance(ctx, DebateContext)
    assert ctx.epic == DEFAULT_EPIC
    assert ctx.seed_direction == "BUY"
    assert ctx.seed_reasoning == candidate["reasoning"]
    assert ctx.seed_confidence == 62.0
    assert ctx.market_status == "TRADEABLE"
    assert ctx.score_at_pick == 58.0
    # bars summary reflects the real-time closes (18000 -> 18020)
    assert "IG real-time" in ctx.recent_bars_summary
    assert "net +0.111%" in ctx.recent_bars_summary
    assert ctx.generated_at.endswith("Z")


def test_fresh_spread_overrides_pick(
    make_candidate: Callable[..., dict[str, Any]]
) -> None:
    cand = make_candidate(spread_pct_at_pick=0.05)
    fresh = _FakeEnv(
        ok=True,
        data={
            "bid": 17999.0,
            "ask": 18000.0,
            "spread": 1.0,
            "spread_pct": 0.09,  # fresh, different from the pick
            "market_status": "TRADEABLE",
            "timestamp": "2026-06-15T09:05:00Z",
        },
    )
    ctx = build_debate_context(cand, FakeBroker(price_env=fresh), CONFIG)
    assert ctx.spread_pct == 0.09  # fresh value, NOT the 0.05 from the pick


def test_drift_none_does_not_crash(
    make_candidate: Callable[..., dict[str, Any]], broker: FakeBroker
) -> None:
    cand = make_candidate(drift_at_pick=None)
    ctx = build_debate_context(cand, broker, CONFIG)
    assert ctx.drift_at_pick is None


def test_ohlcv_raised_fault_fails_closed(candidate: dict[str, Any]) -> None:
    broker = FakeBroker(ohlcv_raises=True)
    with pytest.raises(DebateError):
        build_debate_context(candidate, broker, CONFIG)


def test_ohlcv_not_ok_fails_closed(candidate: dict[str, Any]) -> None:
    broker = FakeBroker(ohlcv_env=_FakeEnv(ok=False, data=None))
    with pytest.raises(DebateError):
        build_debate_context(candidate, broker, CONFIG)


def test_too_few_bars_fails_closed(candidate: dict[str, Any]) -> None:
    broker = FakeBroker(ohlcv_env=_FakeEnv(ok=True, data={"bars": make_bars([18000.0])}))
    with pytest.raises(DebateError):
        build_debate_context(candidate, broker, CONFIG)


def test_zero_close_fails_closed(candidate: dict[str, Any]) -> None:
    broker = FakeBroker(ohlcv_env=_FakeEnv(ok=True, data={"bars": make_bars([0.0, 18000.0])}))
    with pytest.raises(DebateError):
        build_debate_context(candidate, broker, CONFIG)


def test_non_tradeable_market_fails_closed(candidate: dict[str, Any]) -> None:
    closed = _FakeEnv(
        ok=True,
        data={"spread_pct": 0.03, "market_status": "CLOSED", "ask": 1.0, "bid": 1.0},
    )
    with pytest.raises(DebateError):
        build_debate_context(candidate, FakeBroker(price_env=closed), CONFIG)


def test_price_not_ok_fails_closed(candidate: dict[str, Any]) -> None:
    broker = FakeBroker(price_env=_FakeEnv(ok=False, data=None))
    with pytest.raises(DebateError):
        build_debate_context(candidate, broker, CONFIG)


def test_market_info_not_ok_fails_closed(candidate: dict[str, Any]) -> None:
    broker = FakeBroker(market_info_env=_FakeEnv(ok=False, data=None))
    with pytest.raises(DebateError):
        build_debate_context(candidate, broker, CONFIG)


def test_each_probe_read_exactly_once(
    candidate: dict[str, Any], broker: FakeBroker
) -> None:
    build_debate_context(candidate, broker, CONFIG)
    assert broker.get_price_calls == [DEFAULT_EPIC]
    assert broker.get_ohlcv_calls == [(DEFAULT_EPIC, CONFIG.bars_resolution, CONFIG.bars_count)]
    assert broker.get_market_info_calls == [DEFAULT_EPIC]


def test_generated_at_frozen_via_utcnow(
    candidate: dict[str, Any], broker: FakeBroker, monkeypatch: pytest.MonkeyPatch
) -> None:
    from datetime import datetime, timezone

    frozen = datetime(2026, 6, 15, 11, 22, 33, 456000, tzinfo=timezone.utc)
    monkeypatch.setattr(context_builder, "utc_iso_now", lambda: "2026-06-15T11:22:33.456Z")
    ctx = build_debate_context(candidate, broker, CONFIG)
    assert ctx.generated_at == "2026-06-15T11:22:33.456Z"
    assert frozen.year == 2026  # sanity: the freeze instant is well-formed
