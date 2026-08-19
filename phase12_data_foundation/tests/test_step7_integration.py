"""Step 7 — the synthetic-day offline proof (Plan §6 Step 7, acceptance bullet 2).

Composes the pieces Steps 1-6 built and tested in isolation (BarArchive, BarService,
PaperTradeTracker, assess_day) into one scenario: a Recorder-fake has already written
yFinance bars to the archive, two Both-Sides-Shadow paper trades are due, the tracker
resolves them *exclusively* from the archive (a chain provider that raises proves no
network/chain call happens), the resolved rows carry ``resolution_source == 'yf'``, and
``assess_day`` reports the day healthy. No network, no LLM.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from abstain_lessons.paper import PaperExitReason, PaperStatus, PaperTrade, PaperVariant
from abstain_lessons.paper_store import PaperTradeStore
from data_foundation.archive import BarArchive
from data_foundation.budget import IG_QUOTA_V1, SourceBudget
from data_foundation.heartbeat import assess_day
from data_foundation.models import Bar
from data_foundation.service import BarService

_MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "phase2_persistence" / "migrations"
_MIGRATION_004 = _MIGRATIONS_DIR / "004_phase9_instrument_universe.sql"
_MIGRATION_005 = _MIGRATIONS_DIR / "005_v3_learning.sql"
_MIGRATION_006 = _MIGRATIONS_DIR / "006_phase12_data_foundation.sql"

EPIC = "IX.D.DAX.IFMM.IP"
DAY = "2026-08-16"
CREATED_UTC = f"{DAY}T09:00:00.000Z"
TIME_STOP_UTC = f"{DAY}T10:00:00.000Z"


class _RaisingProvider:
    """A BarProvider that must never be called — proves archive-first, zero chain calls."""

    def get_bars(self, epic, *, resolution, count):
        raise AssertionError("chain provider called — archive coverage should have been enough")


@pytest.fixture
def archive(tmp_path) -> BarArchive:
    a = BarArchive(tmp_path / "bars.sqlite")
    a.ensure_schema()
    # Phase 13 §6 A6.2: assess_day now checks coverage (MIN_WINDOW_RATIO=0.9) per
    # measurable epic over the full day. This test isn't about coverage — it's about
    # the resolution flow — so we insert a dense baseline of 1-min bars covering
    # the day, then override the SL/TP bar at 09:10 with the low that triggers
    # both legs. INSERT OR IGNORE keeps the FIRST insertion at a given (ts, source)
    # — the special bars must be inserted *before* the loop's generic ones, or
    # the loop's 09:10 (low=100) wins and the SL trigger never fires.
    from datetime import datetime, timedelta, timezone
    day_start = datetime.strptime(DAY, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    bars = [
        # 09:05: the entry bar (BUY trigger condition met later)
        Bar(epic=EPIC, resolution="1m", ts_utc=f"{DAY}T09:05:00.000Z",
            open=100, high=101, low=99, close=100, volume=10,
            source="yf", fetched_at=f"{DAY}T09:05:01.000Z"),
        # 09:10: SL for BUY (low <= 90.5) and TP for SELL (low <= 80) in one bar.
        Bar(epic=EPIC, resolution="1m", ts_utc=f"{DAY}T09:10:00.000Z",
            open=100, high=101, low=79, close=80, volume=10,
            source="yf", fetched_at=f"{DAY}T09:10:01.000Z"),
    ]
    bars.extend(
        Bar(epic=EPIC, resolution="1m",
            ts_utc=(day_start + timedelta(minutes=m)).strftime("%Y-%m-%dT%H:%M:00.000Z"),
            open=100, high=100, low=100, close=100, volume=10,
            source="yf", fetched_at=f"{DAY}T08:55:01.000Z")
        for m in range(24 * 60)
        if m not in (65, 70)  # 65=09:05, 70=09:10 — keep the special bars
    )
    a.insert_bars(bars)
    yield a
    a.close()


@pytest.fixture
def db_path(tmp_path) -> str:
    """One physical DB carrying both ``instrument_universe`` and ``paper_trades``,
    mirroring production (``wiring.py`` passes the same path to both stores)."""
    path = tmp_path / "trading_bot_test.sqlite"
    conn = sqlite3.connect(str(path))
    conn.executescript(_MIGRATION_004.read_text(encoding="utf-8"))
    conn.executescript(_MIGRATION_005.read_text(encoding="utf-8"))
    conn.executescript(_MIGRATION_006.read_text(encoding="utf-8"))
    conn.commit()
    conn.close()
    now = f"{DAY}T08:00:00.000Z"
    conn = sqlite3.connect(str(path))
    conn.execute(
        "INSERT INTO instrument_universe (epic, yf_ticker, point_value, min_deal_size, "
        "currency, status, source, checks_json, fail_count, data_degraded, created_at, "
        "updated_at, data_source_status, symbol_source, symbol_checked_at) VALUES "
        "(?, '^GDAXI', 1.0, 0.5, 'EUR', 'active', 'curated', '{}', 0, 0, ?, ?, 'ok', "
        "'resolver', ?)",
        (EPIC, now, now, now),
    )
    conn.commit()
    conn.close()
    return str(path)


def _shadow_pair() -> list[PaperTrade]:
    """Both-Sides-Shadow, entry levels chosen so 09:10's bar SL/TPs the BUY/SELL leg."""
    return [
        PaperTrade(
            paper_id="p-buy", abstain_record_id="sched:test", variant=PaperVariant.SHADOW_BUY,
            epic=EPIC, direction="BUY", created_utc=CREATED_UTC, entry_level=100.5,
            stop_distance=10.0, limit_distance=20.0, time_stop_utc=TIME_STOP_UTC,
            status=PaperStatus.OPEN,
        ),
        PaperTrade(
            paper_id="p-sell", abstain_record_id="sched:test", variant=PaperVariant.SHADOW_SELL,
            epic=EPIC, direction="SELL", created_utc=CREATED_UTC, entry_level=100.0,
            stop_distance=10.0, limit_distance=20.0, time_stop_utc=TIME_STOP_UTC,
            status=PaperStatus.OPEN,
        ),
    ]


def test_synthetic_day_resolves_exclusively_from_archive_and_reports_healthy(archive, db_path):
    budget = SourceBudget(archive.db_path, IG_QUOTA_V1)
    chain = [("yf", _RaisingProvider()), ("ig", _RaisingProvider())]
    bar_service = BarService(archive, chain, budget)

    store = PaperTradeStore(db_path)
    for trade in _shadow_pair():
        store.insert(trade)

    def bar_fetch(epic: str):
        return bar_service.get_window(
            epic, "1m", CREATED_UTC, f"{DAY}T10:05:00.000Z"
        )

    from abstain_lessons.paper import PaperTradeTracker

    tracker = PaperTradeTracker(store, bar_fetch=bar_fetch)
    tracker.tick(now_utc=f"{DAY}T10:01:00.000Z")

    resolved = {t.paper_id: t for t in [
        PaperTrade.from_row(row) for row in store.conn.execute(
            "SELECT paper_id, abstain_record_id, variant, epic, direction, created_utc, "
            "entry_level, stop_distance, limit_distance, time_stop_utc, status, "
            "resolved_utc, exit_reason, exit_level, pnl_points, r_multiple, "
            "council_confidence, lesson, lesson_extracted, context_json, resolution_source "
            "FROM paper_trades"
        ).fetchall()
    ]}
    assert resolved["p-buy"].status == PaperStatus.RESOLVED
    assert resolved["p-buy"].exit_reason == PaperExitReason.SL
    assert resolved["p-buy"].resolution_source == "yf"
    assert resolved["p-sell"].status == PaperStatus.RESOLVED
    assert resolved["p-sell"].exit_reason == PaperExitReason.TP
    assert resolved["p-sell"].resolution_source == "yf"

    verdict = assess_day(archive, db_path, db_path, DAY, shadow_enabled=True)
    assert verdict.ok is True
    assert verdict.measurable_epics == 1
    assert verdict.pairs_opened == 2
    assert verdict.pairs_resolved == 2
    assert verdict.problems == []
