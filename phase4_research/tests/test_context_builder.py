"""Tests for ``context_builder.build_context`` — the deterministic input side.

All mocked, no network, no cross-phase imports: the broker, DB, and fetcher are
the ``conftest`` fakes. Concept §3 mandates ≥6 cases; this file covers the full
context, empty P2 reads, honest ``None`` pass-through (incl. ``volume_z_score`` and
all-intraday-off-hours), epics dropping out of the universe, an empty universe, the
``EpicNotMappedError`` degrade-to-``None`` guard, and the non-ok-envelope skip.
"""

from __future__ import annotations

from typing import Any

import pytest

from research.context_builder import build_context
from research.models import ResearchConfig, ResearchContext
from tests.conftest import (
    DEFAULT_EPIC,
    EpicNotMappedError,
    FakeBroker,
    FakeDB,
    FakeFetcher,
    _make_prompt_dict,
)


def _config(**over: Any) -> ResearchConfig:
    """A config with the default single-epic allow-list unless overridden."""
    return ResearchConfig(**over)


def test_full_context(broker: FakeBroker, db: FakeDB, fetcher: FakeFetcher) -> None:
    """Happy path: one tradeable epic, P2 reads, full 10-key brain context."""
    ctx = build_context(broker, db, fetcher, _config())

    assert isinstance(ctx, ResearchContext)
    assert ctx.anchor_epic == DEFAULT_EPIC
    # universe
    assert len(ctx.tradeable_epics) == 1
    epic = ctx.tradeable_epics[0]
    assert epic == {
        "epic": DEFAULT_EPIC,
        "name": "Germany 40 Cash (1 EUR)",
        "spread_pct": 0.03,
        "market_status": "TRADEABLE",
        "min_deal_size": 0.5,
    }
    # P2 reads + the 8/5 limits actually requested
    assert len(ctx.recent_trades) == 2
    assert len(ctx.recent_lessons) == 1
    assert ctx.bot_score == 55.0
    assert ctx.risk_level == "AGGRESSIV"
    assert db.trade_n == [8]
    assert db.lesson_n == [5]
    # P3 brain context — all 10 keys present
    assert ctx.brain_context is not None
    assert set(ctx.brain_context) == {
        "ticker", "drift_pct", "momentum_15m_pct", "momentum_is_realtime",
        "volume_z_score", "volume_available", "distance_to_high_pct",
        "distance_to_low_pct", "range_30d", "generated_at",
    }


def test_empty_trades_and_lessons(broker: FakeBroker, fetcher: FakeFetcher) -> None:
    """No trades / no lessons → empty lists tolerated, build still succeeds."""
    db = FakeDB(trades=[], lessons=[], score=50.0, risk_level="KONSERVATIV")
    ctx = build_context(broker, db, fetcher, _config())

    assert ctx.recent_trades == []
    assert ctx.recent_lessons == []
    assert ctx.bot_score == 50.0
    assert ctx.risk_level == "KONSERVATIV"


def test_volume_z_score_none_passed_through(broker: FakeBroker, db: FakeDB) -> None:
    """A ``None`` volume z-score is preserved honestly — never faked to 0."""
    pd = _make_prompt_dict(volume_z_score=None, volume_available=False)
    ctx = build_context(broker, db, FakeFetcher(prompt_dict=pd), _config())

    assert ctx.brain_context is not None
    assert ctx.brain_context["volume_z_score"] is None
    assert ctx.brain_context["volume_available"] is False


def test_all_intraday_none_offhours(broker: FakeBroker, db: FakeDB) -> None:
    """Off-hours: every intraday field is ``None`` → dict with ``None``s, no crash."""
    pd = _make_prompt_dict(
        drift_pct=None,
        momentum_15m_pct=None,
        volume_z_score=None,
        distance_to_high_pct=None,
        distance_to_low_pct=None,
        range_30d=None,
    )
    ctx = build_context(broker, db, FakeFetcher(prompt_dict=pd), _config())

    assert ctx.brain_context is not None
    for key in (
        "drift_pct", "momentum_15m_pct", "volume_z_score",
        "distance_to_high_pct", "distance_to_low_pct", "range_30d",
    ):
        assert ctx.brain_context[key] is None
    # delay-honesty flag is always present and False
    assert ctx.brain_context["momentum_is_realtime"] is False


def test_untradeable_epic_drops_out(db: FakeDB, fetcher: FakeFetcher) -> None:
    """A non-TRADEABLE market status drops the epic from the universe."""
    broker = FakeBroker(market_status="CLOSED")
    ctx = build_context(broker, db, fetcher, _config())
    assert ctx.tradeable_epics == []


def test_wide_spread_drops_out(db: FakeDB, fetcher: FakeFetcher) -> None:
    """A spread above the configured cap drops the epic from the universe."""
    broker = FakeBroker(spread_pct=0.9)
    ctx = build_context(broker, db, fetcher, _config(max_spread_pct=0.5))
    assert ctx.tradeable_epics == []


def test_non_eur_currency_drops_out(db: FakeDB, fetcher: FakeFetcher) -> None:
    """A non-EUR instrument is rejected (EUR-account hard rule)."""
    broker = FakeBroker(currency="USD")
    ctx = build_context(broker, db, fetcher, _config())
    assert ctx.tradeable_epics == []


def test_empty_universe_when_price_not_ok(db: FakeDB, fetcher: FakeFetcher) -> None:
    """``get_price`` ok=False → epic skipped → empty universe (abstain path)."""
    broker = FakeBroker(ok=False)
    ctx = build_context(broker, db, fetcher, _config())
    assert ctx.tradeable_epics == []
    # bot_score / risk_level still flow through regardless of the empty universe
    assert ctx.bot_score == 55.0
    assert ctx.risk_level == "AGGRESSIV"


def test_market_info_not_ok_skips_epic(db: FakeDB, fetcher: FakeFetcher) -> None:
    """``get_market_info`` ok=False → epic skipped even with a healthy price."""
    broker = FakeBroker(info_ok=False)
    ctx = build_context(broker, db, fetcher, _config())
    assert ctx.tradeable_epics == []


def test_epic_not_mapped_degrades_brain_context(broker: FakeBroker, db: FakeDB) -> None:
    """``EpicNotMappedError`` from the fetcher → ``brain_context is None``, no crash."""
    fetcher = FakeFetcher(raises=EpicNotMappedError("no mapping for epic"))
    ctx = build_context(broker, db, fetcher, _config())

    assert ctx.brain_context is None
    # the rest of the context is unaffected
    assert len(ctx.tradeable_epics) == 1
    assert ctx.bot_score == 55.0


def test_brain_context_none_degrades(broker: FakeBroker, db: FakeDB) -> None:
    """A defensive ``None`` return from ``get_brain_context`` degrades cleanly."""
    fetcher = FakeFetcher(returns_none=True)
    ctx = build_context(broker, db, fetcher, _config())
    assert ctx.brain_context is None


def test_unexpected_exception_propagates(broker: FakeBroker, db: FakeDB) -> None:
    """A non-guard exception from the fetcher re-raises (never swallowed)."""
    fetcher = FakeFetcher(raises=RuntimeError("boom"))
    with pytest.raises(RuntimeError, match="boom"):
        build_context(broker, db, fetcher, _config())


def test_multi_epic_allowlist_partial_tradeable(db: FakeDB, fetcher: FakeFetcher) -> None:
    """With two epics, only those passing the probe land in the universe.

    The default ``FakeBroker`` answers every epic identically, so a two-epic
    allow-list yields two tradeable entries with the anchor first.
    """
    broker = FakeBroker()
    sibling = "IX.D.DAX.DAILY.IP"
    ctx = build_context(broker, db, fetcher, _config(epic_allowlist=(DEFAULT_EPIC, sibling)))

    assert [e["epic"] for e in ctx.tradeable_epics] == [DEFAULT_EPIC, sibling]
    assert ctx.anchor_epic == DEFAULT_EPIC
