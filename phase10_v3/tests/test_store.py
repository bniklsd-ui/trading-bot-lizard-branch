"""S3 tests — AbstainStore."""

from __future__ import annotations

import sqlite3

import pytest

from abstain_lessons.exceptions import AbstainStoreError
from abstain_lessons.models import AbstainReason, AbstainRecord, AbstainStage
from abstain_lessons.store import AbstainStore


@pytest.fixture
def store(tmp_path):
    s = AbstainStore(tmp_path / "test.sqlite")
    s.ensure_schema()
    yield s
    s.close()


def _record(**overrides) -> AbstainRecord:
    kwargs = dict(
        epic="IX.D.DAX.IFMM.IP",
        stage=AbstainStage.GATE,
        reason=AbstainReason.REASON_GATE_TIME_WINDOW,
    )
    kwargs.update(overrides)
    return AbstainRecord.new(**kwargs)


def test_ensure_schema_creates_table(store):
    # ensure_schema() already ran in the fixture — a second call must not raise.
    store.ensure_schema()
    row = store.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='abstain_records'"
    ).fetchone()
    assert row is not None


def test_insert_and_recent_newest_first(store):
    r1 = _record()
    r2 = AbstainRecord(
        record_id="later",
        created_utc="2099-01-01T00:00:00.000Z",
        epic="IX.D.DAX.IFMM.IP",
        stage=AbstainStage.VETO,
        reason=AbstainReason.REASON_VETO_SPREAD,
    )
    store.insert(r1)
    store.insert(r2)
    recent = store.recent(limit=10)
    assert [r.record_id for r in recent] == [r2.record_id, r1.record_id]


def test_insert_idempotent_no_duplicates(store):
    r = _record()
    store.insert(r)
    store.insert(r)  # same record_id — must not raise, must not duplicate
    assert len(store.recent(limit=10)) == 1


def test_set_lesson_and_recent_lessons_filter(store):
    r1 = _record()
    r2 = _record()
    store.insert(r1)
    store.insert(r2)
    store.set_lesson(r1.record_id, "lesson one")
    lessons = store.recent_lessons(limit=10)
    assert lessons == ["lesson one"]


def test_count_lessons_today(store):
    r = _record()
    store.insert(r)
    store.set_lesson(r.record_id, "a lesson")
    today_prefix = r.created_utc[:10]
    assert store.count_lessons_today(f"{today_prefix}T12:00:00.000Z") == 1
    assert store.count_lessons_today("2099-01-01T00:00:00.000Z") == 0


def test_broken_path_raises_abstain_store_error():
    with pytest.raises(AbstainStoreError):
        AbstainStore("/nonexistent_dir_xyz/test.sqlite")


def test_context_manager_calls_close(tmp_path):
    with AbstainStore(tmp_path / "test.sqlite") as s:
        s.ensure_schema()
        conn = s.conn
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")
