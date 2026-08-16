"""S3-analog tests — PaperTradeStore."""

from __future__ import annotations

import pytest

from abstain_lessons.exceptions import PaperTradeError
from abstain_lessons.paper import PaperTrade, PaperVariant
from abstain_lessons.paper_store import PaperTradeStore


@pytest.fixture
def store(tmp_path):
    s = PaperTradeStore(tmp_path / "test.sqlite")
    s.ensure_schema()
    yield s
    s.close()


def _trade(**overrides) -> PaperTrade:
    kwargs = dict(
        abstain_record_id="abs-1",
        variant=PaperVariant.SHADOW_BUY,
        epic="IX.D.DAX.IFMM.IP",
        direction="BUY",
        entry_level=18000.0,
        stop_distance=30.0,
        limit_distance=45.0,
        time_stop_utc="2026-07-11T13:00:00.000Z",
    )
    kwargs.update(overrides)
    return PaperTrade.new(**kwargs)


def test_ensure_schema_creates_table(store):
    store.ensure_schema()
    row = store.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='paper_trades'"
    ).fetchone()
    assert row is not None


def test_insert_idempotent_no_duplicates(store):
    t = _trade()
    store.insert(t)
    store.insert(t)
    assert len(store.open_trades()) == 1


def test_open_trades_only_open_status(store):
    t1 = _trade()
    t2 = _trade(variant=PaperVariant.SHADOW_SELL, direction="SELL")
    store.insert(t1)
    store.insert(t2)
    store.mark_resolved(
        t1.paper_id, exit_reason="TP", exit_level=17955.0, pnl_points=45.0,
        r_multiple=1.5, resolved_utc="2026-07-11T12:45:00.000Z",
    )
    open_trades = store.open_trades()
    assert [t.paper_id for t in open_trades] == [t2.paper_id]


def test_mark_resolved(store):
    t = _trade()
    store.insert(t)
    store.mark_resolved(
        t.paper_id, exit_reason="SL", exit_level=18030.0, pnl_points=-30.0,
        r_multiple=-1.0, resolved_utc="2026-07-11T12:30:00.000Z",
    )
    assert store.open_trades() == []


def test_mark_resolved_writes_resolution_source(store):
    t = _trade()
    store.insert(t)
    store.mark_resolved(
        t.paper_id, exit_reason="SL", exit_level=18030.0, pnl_points=-30.0,
        r_multiple=-1.0, resolved_utc="2026-07-11T12:30:00.000Z", resolution_source="ig+yf",
    )
    row = store.conn.execute(
        "SELECT resolution_source FROM paper_trades WHERE paper_id = ?", (t.paper_id,)
    ).fetchone()
    assert row["resolution_source"] == "ig+yf"


def test_mark_resolved_default_resolution_source_is_none(store):
    t = _trade()
    store.insert(t)
    store.mark_resolved(
        t.paper_id, exit_reason="SL", exit_level=18030.0, pnl_points=-30.0,
        r_multiple=-1.0, resolved_utc="2026-07-11T12:30:00.000Z",
    )
    row = store.conn.execute(
        "SELECT resolution_source FROM paper_trades WHERE paper_id = ?", (t.paper_id,)
    ).fetchone()
    assert row["resolution_source"] is None


def test_mark_expired(store):
    t = _trade()
    store.insert(t)
    store.mark_expired(t.paper_id, "2026-07-11T14:00:00.000Z")
    assert store.open_trades() == []


def test_set_lesson_and_recent_lessons(store):
    t = _trade()
    store.insert(t)
    store.set_lesson(t.paper_id, "shadow lesson")
    assert store.recent_lessons(limit=10) == ["shadow lesson"]


def test_count_today_all_and_by_variant(store):
    t1 = _trade()
    t2 = _trade(variant=PaperVariant.COUNCIL_PICK)
    store.insert(t1)
    store.insert(t2)
    today_prefix = t1.created_utc[:10]
    now = f"{today_prefix}T12:00:00.000Z"
    assert store.count_today(None, now) == 2
    assert store.count_today(PaperVariant.SHADOW_BUY, now) == 1
    assert store.count_today(PaperVariant.COUNCIL_PICK, now) == 1
    assert store.count_today(None, "2099-01-01T00:00:00.000Z") == 0


def test_broken_path_raises_paper_trade_error():
    with pytest.raises(PaperTradeError):
        PaperTradeStore("/nonexistent_dir_xyz/test.sqlite")


def test_count_lessons_today(store):
    t1 = _trade()
    t2 = _trade(variant=PaperVariant.SHADOW_SELL)
    store.insert(t1)
    store.insert(t2)
    today_prefix = t1.created_utc[:10]
    now = f"{today_prefix}T12:00:00.000Z"
    assert store.count_lessons_today(now) == 0
    store.set_lesson(t1.paper_id, "eine Lehre")
    assert store.count_lessons_today(now) == 1
    assert store.count_lessons_today("2099-01-01T00:00:00.000Z") == 0
