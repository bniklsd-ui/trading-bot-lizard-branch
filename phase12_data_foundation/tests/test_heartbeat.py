"""Tests for ``data_foundation.heartbeat`` (Plan §6 Step 6). No network."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from data_foundation.archive import BarArchive
from data_foundation.budget import IG_QUOTA_V1, SourceBudget
from data_foundation.heartbeat import DivergenceSampler, HealthVerdict, assess_day
from data_foundation.models import Bar
from data_foundation.service import BudgetedIGBarProvider

_MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "phase2_persistence" / "migrations"
_MIGRATION_004 = _MIGRATIONS_DIR / "004_phase9_instrument_universe.sql"
_MIGRATION_005 = _MIGRATIONS_DIR / "005_v3_learning.sql"
_MIGRATION_006 = _MIGRATIONS_DIR / "006_phase12_data_foundation.sql"

EPIC = "IX.D.DAX.IFMM.IP"
DAY = "2026-08-16"


@pytest.fixture
def archive(tmp_path) -> BarArchive:
    a = BarArchive(tmp_path / "bars.sqlite")
    a.ensure_schema()
    yield a
    a.close()


@pytest.fixture
def db_path(tmp_path) -> str:
    """One physical DB carrying both ``instrument_universe`` and ``paper_trades`` —
    mirrors production, where both tables live in the same ``trading_bot.sqlite``
    (``wiring.py`` passes the same ``_DB_PATH`` to both ``UniverseStore`` and
    ``PaperTradeStore``); ``assess_day`` still takes two path params per the plan's
    signature, callers just happen to pass the same string twice."""
    path = tmp_path / "trading_bot_test.sqlite"
    conn = sqlite3.connect(str(path))
    conn.executescript(_MIGRATION_004.read_text(encoding="utf-8"))
    conn.executescript(_MIGRATION_005.read_text(encoding="utf-8"))
    conn.executescript(_MIGRATION_006.read_text(encoding="utf-8"))
    conn.commit()
    conn.close()
    return str(path)


def _insert_universe_row(db_path: str, epic: str, *, data_source_status: str = "ok",
                          status: str = "active") -> None:
    now = "2026-08-16T09:00:00.000Z"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO instrument_universe (epic, yf_ticker, point_value, min_deal_size, "
        "currency, status, source, checks_json, fail_count, data_degraded, created_at, "
        "updated_at, data_source_status, symbol_source, symbol_checked_at) VALUES "
        "(?, '^GDAXI', 1.0, 0.5, 'EUR', ?, 'curated', '{}', 0, 0, ?, ?, ?, 'resolver', ?)",
        (epic, status, now, now, data_source_status, now),
    )
    conn.commit()
    conn.close()


def _insert_paper_trade(db_path: str, *, created_utc: str, status: str = "OPEN",
                         resolved_utc: str | None = None, exit_reason: str | None = None,
                         epic: str = EPIC) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO paper_trades (paper_id, abstain_record_id, variant, epic, direction, "
        "created_utc, entry_level, stop_distance, time_stop_utc, status, resolved_utc, "
        "exit_reason) VALUES (?, 'ar1', 'shadow_up', ?, 'BUY', ?, 100.0, 10.0, ?, ?, ?, ?)",
        (f"p-{created_utc}-{status}-{exit_reason}", epic, created_utc, created_utc, status,
         resolved_utc, exit_reason),
    )
    conn.commit()
    conn.close()


# -- assess_day -----------------------------------------------------------


def test_assess_day_healthy(archive, db_path):
    _insert_universe_row(db_path, EPIC)
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc=f"{DAY}T09:05:00.000Z",
                              open=1, high=1, low=1, close=1, volume=1, source="yf",
                              fetched_at=f"{DAY}T09:05:01.000Z")])
    _insert_paper_trade(db_path, created_utc=f"{DAY}T09:00:00.000Z", status="RESOLVED",
                         resolved_utc=f"{DAY}T10:00:00.000Z", exit_reason="TP")

    verdict = assess_day(archive, db_path, db_path, DAY, shadow_enabled=True)
    assert isinstance(verdict, HealthVerdict)
    assert verdict.ok is True
    assert verdict.bars_today == 1
    assert verdict.pairs_resolved == 1
    assert verdict.pairs_typed_expired == 0
    assert verdict.measurable_epics == 1
    assert verdict.problems == []


def test_assess_day_zero_measurement_with_shadow_enabled(archive, db_path):
    _insert_universe_row(db_path, EPIC)
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc=f"{DAY}T09:05:00.000Z",
                              open=1, high=1, low=1, close=1, volume=1, source="yf",
                              fetched_at=f"{DAY}T09:05:01.000Z")])
    # nothing resolved or typed-expired today

    verdict = assess_day(archive, db_path, db_path, DAY, shadow_enabled=True)
    assert verdict.ok is False
    assert any("zero resolved/expired" in p for p in verdict.problems)


def test_assess_day_recorder_dead(archive, db_path):
    _insert_universe_row(db_path, EPIC)
    # no bars archived today at all

    verdict = assess_day(archive, db_path, db_path, DAY, shadow_enabled=False)
    assert verdict.ok is False
    assert any("Recorder appears dead" in p for p in verdict.problems)


def test_assess_day_no_measurable_epic_is_ok_with_problem_note(archive, db_path):
    # no universe row inserted at all -> measurable_universe() is empty.
    # shadow_enabled=True + a real resolution isolates this from E8's new
    # "measurement arm off" check (P12.5 plan §2), which would otherwise flip ok on
    # its own and defeat this test's actual point: measurable_epics==0 alone is a
    # note, not a failure.
    _insert_paper_trade(db_path, created_utc=f"{DAY}T09:00:00.000Z", status="RESOLVED",
                         resolved_utc=f"{DAY}T10:00:00.000Z", exit_reason="TP")
    verdict = assess_day(archive, db_path, db_path, DAY, shadow_enabled=True)
    assert verdict.ok is True
    assert verdict.measurable_epics == 0
    assert any("no measurable epic" in p for p in verdict.problems)


def test_assess_day_does_not_leak_bars_from_other_days(archive, db_path):
    """A past day's bars_today must not include bars fetched on a later day (the
    open-ended bars_written_since bug this test guards against, Plan §6 Step 6)."""
    _insert_universe_row(db_path, EPIC)
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc=f"{DAY}T09:05:00.000Z",
                              open=1, high=1, low=1, close=1, volume=1, source="yf",
                              fetched_at=f"{DAY}T09:05:01.000Z")])
    next_day = "2026-08-17"
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc=f"{next_day}T09:05:00.000Z",
                              open=1, high=1, low=1, close=1, volume=1, source="yf",
                              fetched_at=f"{next_day}T09:05:01.000Z")])

    verdict = assess_day(archive, db_path, db_path, DAY, shadow_enabled=False)
    assert verdict.bars_today == 1  # not 2 — the next day's bar must not leak in


def test_assess_day_flags_measurement_arm_off(archive, db_path):
    """E8 (P12.5 plan §2): the exact Tag-1 situation that live-reported ``ok=True`` --
    bars flowing, a measurable epic, but enable_shadow_schedule off means zero shadow
    pairs can ever open. The daemon must not be able to call that a healthy day."""
    _insert_universe_row(db_path, EPIC)
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc=f"{DAY}T09:05:00.000Z",
                              open=1, high=1, low=1, close=1, volume=1, source="yf",
                              fetched_at=f"{DAY}T09:05:01.000Z")])

    verdict = assess_day(archive, db_path, db_path, DAY, shadow_enabled=False)
    assert verdict.ok is False
    assert any("measurement arm off" in p for p in verdict.problems)


def test_assess_day_typed_expiry_counts_as_measurement(archive, db_path):
    _insert_universe_row(db_path, EPIC)
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc=f"{DAY}T09:05:00.000Z",
                              open=1, high=1, low=1, close=1, volume=1, source="yf",
                              fetched_at=f"{DAY}T09:05:01.000Z")])
    _insert_paper_trade(db_path, created_utc=f"{DAY}T09:00:00.000Z", status="RESOLVED",
                         resolved_utc=f"{DAY}T13:00:00.000Z", exit_reason="TIME_STOP")

    verdict = assess_day(archive, db_path, db_path, DAY, shadow_enabled=True)
    assert verdict.ok is True
    assert verdict.pairs_resolved == 0
    assert verdict.pairs_typed_expired == 1


# -- DivergenceSampler ------------------------------------------------------


class _FakeIGBroker:
    """Returns a bar in IG's real raw ``get_ohlcv`` shape (``"yyyy/MM/dd HH:mm:ss"``,
    never ISO) whose ``timestamp`` tracks an injectable "current day" — a fixed
    timestamp here would make every probe query the same archive window regardless
    of which day the test has advanced ``now_fn`` to.

    Wired through the real :class:`BudgetedIGBarProvider` (not a stand-in that hands
    ``DivergenceSampler`` an already-ISO ``ts``) so these tests exercise the actual U1
    fix (``service.py``'s ``normalize_bar_ts`` call) instead of skipping the seam it
    fixes (P12.5 plan §3/U1)."""

    def __init__(self, close: float):
        self.close = close
        self.calls = 0
        self.day = DAY

    def get_ohlcv(self, epic, resolution, count):
        self.calls += 1
        raw_ts = datetime.strptime(self.day, "%Y-%m-%d").strftime("%Y/%m/%d") + " 09:00:00"
        bar = {"timestamp": raw_ts, "open": self.close, "high": self.close,
               "low": self.close, "close": self.close, "volume": 1}
        return SimpleNamespace(ok=True, data={"bars": [bar]})


def _budgeted_ig(tmp_path, close: float) -> tuple[_FakeIGBroker, BudgetedIGBarProvider]:
    broker = _FakeIGBroker(close)
    budget = SourceBudget(tmp_path / "ig_budget.sqlite", IG_QUOTA_V1)
    return broker, BudgetedIGBarProvider(broker, budget, spend_kind="sample")


def test_sampler_throttles_to_once_per_day(archive, tmp_path):
    broker, ig = _budgeted_ig(tmp_path, 100.0)
    now = datetime(2026, 8, 16, 9, 5, tzinfo=timezone.utc)
    sampler = DivergenceSampler(ig, archive, now_fn=lambda: now)
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc=f"{DAY}T09:00:00.000Z",
                              open=100, high=100, low=100, close=100.0, volume=1, source="yf",
                              fetched_at=f"{DAY}T09:00:01.000Z")])

    sampler.sample_epic(EPIC, lambda e: None)
    sampler.sample_epic(EPIC, lambda e: None)
    assert broker.calls == 1  # second call same day is a no-op


def test_sampler_compares_only_yf_bars_not_ig(archive, tmp_path):
    """The regression this exists to catch: an IG bar at the same minute must never be
    picked as the yFinance comparator (it would always agree with itself)."""
    _, ig = _budgeted_ig(tmp_path, 100.0)
    now = datetime(2026, 8, 16, 9, 5, tzinfo=timezone.utc)
    # an IG bar at the exact probed minute, wildly different from the IG probe's own
    # close would still "agree" if picked as the comparator by mistake — plant a yF bar
    # that genuinely diverges to prove the *yf* row (not the ig row) drives the check.
    archive.insert_bars([
        Bar(epic=EPIC, resolution="1m", ts_utc=f"{DAY}T09:00:00.000Z",
            open=100, high=100, low=100, close=100.0, volume=1, source="ig",
            fetched_at=f"{DAY}T09:00:01.000Z"),
        Bar(epic=EPIC, resolution="1m", ts_utc=f"{DAY}T09:00:00.000Z",
            open=90, high=90, low=90, close=90.0, volume=1, source="yf",
            fetched_at=f"{DAY}T09:00:01.000Z"),
    ])
    events = []
    sampler = DivergenceSampler(ig, archive, health_sink=events.append, now_fn=lambda: now)
    sampler.sample_epic(EPIC, lambda e: None)
    assert len(events) == 1  # 100 vs 90 is a real divergence -> the yf bar was used
    assert events[0]["event"] == "quote_divergence"


def test_sampler_no_yf_bar_in_window_is_a_noop(archive, tmp_path):
    _, ig = _budgeted_ig(tmp_path, 100.0)
    now = datetime(2026, 8, 16, 9, 5, tzinfo=timezone.utc)
    events = []
    sampler = DivergenceSampler(ig, archive, health_sink=events.append, now_fn=lambda: now)
    # archive has no bars at all for this window
    sampler.sample_epic(EPIC, lambda e: None)
    assert events == []


def test_sampler_mismatch_fires_after_two_consecutive_divergences_not_one(archive, tmp_path):
    broker, ig = _budgeted_ig(tmp_path, 100.0)
    day1 = datetime(2026, 8, 16, 9, 5, tzinfo=timezone.utc)
    day2 = datetime(2026, 8, 17, 9, 5, tzinfo=timezone.utc)
    marked = []
    sampler = DivergenceSampler(ig, archive, now_fn=lambda: day1)

    broker.day = "2026-08-16"
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc="2026-08-16T09:00:00.000Z",
                              open=90, high=90, low=90, close=90.0, volume=1, source="yf",
                              fetched_at="2026-08-16T09:00:01.000Z")])
    sampler.sample_epic(EPIC, marked.append)
    assert marked == []  # first divergence — not yet a sticky mismatch

    sampler.now_fn = lambda: day2
    broker.day = "2026-08-17"
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc="2026-08-17T09:00:00.000Z",
                              open=90, high=90, low=90, close=90.0, volume=1, source="yf",
                              fetched_at="2026-08-17T09:00:01.000Z")])
    sampler.sample_epic(EPIC, marked.append)
    assert marked == [EPIC]  # second consecutive divergence — now mark mismatch


def test_sampler_agreement_resets_streak(archive, tmp_path):
    broker, ig = _budgeted_ig(tmp_path, 100.0)
    day1 = datetime(2026, 8, 16, 9, 5, tzinfo=timezone.utc)
    day2 = datetime(2026, 8, 17, 9, 5, tzinfo=timezone.utc)
    day3 = datetime(2026, 8, 18, 9, 5, tzinfo=timezone.utc)
    marked = []
    sampler = DivergenceSampler(ig, archive, now_fn=lambda: day1)

    broker.day = "2026-08-16"
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc="2026-08-16T09:00:00.000Z",
                              open=90, high=90, low=90, close=90.0, volume=1, source="yf",
                              fetched_at="2026-08-16T09:00:01.000Z")])
    sampler.sample_epic(EPIC, marked.append)  # divergence 1

    sampler.now_fn = lambda: day2
    broker.day = "2026-08-17"
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc="2026-08-17T09:00:00.000Z",
                              open=100, high=100, low=100, close=100.0, volume=1, source="yf",
                              fetched_at="2026-08-17T09:00:01.000Z")])
    sampler.sample_epic(EPIC, marked.append)  # agreement — resets streak

    sampler.now_fn = lambda: day3
    broker.day = "2026-08-18"
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc="2026-08-18T09:00:00.000Z",
                              open=90, high=90, low=90, close=90.0, volume=1, source="yf",
                              fetched_at="2026-08-18T09:00:01.000Z")])
    sampler.sample_epic(EPIC, marked.append)  # divergence 1 again (not 3rd consecutive)

    assert marked == []


def test_sampler_budget_veto_is_a_noop(archive):
    class _RefusingIG:
        def get_bars(self, epic, *, resolution, count):
            return None

    events = []
    sampler = DivergenceSampler(_RefusingIG(), archive, health_sink=events.append)
    sampler.sample_epic(EPIC, lambda e: None)
    assert events == []
