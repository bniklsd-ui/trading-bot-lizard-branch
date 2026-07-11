"""Tests for paper.py's data model (PaperTrade/PaperVariant/PaperStatus)."""

from __future__ import annotations

from abstain_lessons.paper import PaperExitReason, PaperStatus, PaperTrade, PaperVariant


def test_new_defaults():
    trade = PaperTrade.new(
        abstain_record_id="abs-1",
        variant=PaperVariant.SHADOW_BUY,
        epic="IX.D.DAX.IFMM.IP",
        direction="BUY",
        entry_level=18000.0,
        stop_distance=30.0,
        limit_distance=45.0,
        time_stop_utc="2026-07-11T13:00:00.000Z",
    )
    assert trade.status is PaperStatus.OPEN
    assert trade.resolved_utc is None
    assert trade.lesson_extracted is False
    assert trade.paper_id


def test_to_row_from_row_roundtrip():
    trade = PaperTrade.new(
        abstain_record_id="abs-1",
        variant=PaperVariant.COUNCIL_PICK,
        epic="IX.D.DAX.IFMM.IP",
        direction="SELL",
        entry_level=18000.0,
        stop_distance=30.0,
        limit_distance=None,
        time_stop_utc="2026-07-11T13:00:00.000Z",
        context_json='{"k": 1}',
    )
    roundtripped = PaperTrade.from_row(trade.to_row())
    assert roundtripped == trade


def test_resolved_trade_roundtrip_with_exit_reason():
    trade = PaperTrade(
        paper_id="p1",
        abstain_record_id="abs-1",
        variant=PaperVariant.SHADOW_SELL,
        epic="IX.D.DAX.IFMM.IP",
        direction="SELL",
        created_utc="2026-07-11T12:00:00.000Z",
        entry_level=18000.0,
        stop_distance=30.0,
        limit_distance=45.0,
        time_stop_utc="2026-07-11T13:00:00.000Z",
        status=PaperStatus.RESOLVED,
        resolved_utc="2026-07-11T12:45:00.000Z",
        exit_reason=PaperExitReason.TP,
        exit_level=17955.0,
        pnl_points=45.0,
        r_multiple=1.5,
    )
    roundtripped = PaperTrade.from_row(trade.to_row())
    assert roundtripped == trade
