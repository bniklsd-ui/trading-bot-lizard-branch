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


def _insert_full_day_yf_bars(archive, epic: str, day: str, *,
                             skip_minutes: set[int] | None = None) -> int:
    """Insert one yF bar per minute over a full UTC day (00:00–23:59). Used by
    assess_day tests that need to pass the A6.2 coverage check. ``skip_minutes``
    simulates gaps (each entry is the minute-of-day to skip, e.g. {720} drops
    the 12:00 bar). Returns the count actually inserted."""
    from datetime import datetime, timedelta, timezone
    day_start = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    bars: list = []
    for m in range(24 * 60):
        if skip_minutes and m in skip_minutes:
            continue
        ts = (day_start + timedelta(minutes=m)).strftime("%Y-%m-%dT%H:%M:00.000Z")
        bars.append(Bar(epic=epic, resolution="1m", ts_utc=ts,
                        open=1, high=1, low=1, close=1, volume=1, source="yf",
                        fetched_at=ts))
    archive.insert_bars(bars)
    return len(bars)


def test_assess_day_healthy(archive, db_path):
    _insert_universe_row(db_path, EPIC)
    n = _insert_full_day_yf_bars(archive, EPIC, DAY)
    _insert_paper_trade(db_path, created_utc=f"{DAY}T09:00:00.000Z", status="RESOLVED",
                         resolved_utc=f"{DAY}T10:00:00.000Z", exit_reason="TP")

    verdict = assess_day(archive, db_path, db_path, DAY, shadow_enabled=True)
    assert isinstance(verdict, HealthVerdict)
    assert verdict.ok is True, f"problems={verdict.problems}"
    assert verdict.bars_today == n
    assert verdict.pairs_resolved == 1
    assert verdict.pairs_typed_expired == 0
    assert verdict.measurable_epics == 1
    assert verdict.worst_coverage == 1.0
    assert verdict.epics_below_threshold == []
    assert verdict.problems == []


def test_assess_day_zero_measurement_with_shadow_enabled(archive, db_path):
    _insert_universe_row(db_path, EPIC)
    _insert_full_day_yf_bars(archive, EPIC, DAY)
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
    next_day = "2026-08-17"
    # 1 bar each on the two days, both yF.
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc=f"{DAY}T09:05:00.000Z",
                              open=1, high=1, low=1, close=1, volume=1, source="yf",
                              fetched_at=f"{DAY}T09:05:01.000Z")])
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc=f"{next_day}T09:05:00.000Z",
                              open=1, high=1, low=1, close=1, volume=1, source="yf",
                              fetched_at=f"{next_day}T09:05:01.000Z")])

    verdict = assess_day(archive, db_path, db_path, DAY, shadow_enabled=False)
    assert verdict.bars_today == 1  # not 2 — the next day's bar must not leak in


def test_assess_day_flags_measurement_arm_off(archive, db_path):
    _insert_universe_row(db_path, EPIC)
    _insert_full_day_yf_bars(archive, EPIC, DAY)
    # shadow_enabled=False: measurement arm off even though bars + epics exist.

    verdict = assess_day(archive, db_path, db_path, DAY, shadow_enabled=False)
    assert verdict.ok is False
    assert any("measurement arm off" in p for p in verdict.problems)


def test_assess_day_typed_expiry_counts_as_measurement(archive, db_path):
    _insert_universe_row(db_path, EPIC)
    _insert_full_day_yf_bars(archive, EPIC, DAY)
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
        # Three 5m bars at 08:50, 08:55, 09:00 with stable close — A6.0's
        # compute_return_divergence needs >= 2 bars per source.
        day = datetime.strptime(self.day, "%Y-%m-%d")
        bars = [
            {"timestamp": day.strftime("%Y/%m/%d") + f" {h:02d}:{m:02d}:00",
             "open": self.close, "high": self.close,
             "low": self.close, "close": self.close, "volume": 1}
            for h, m in [(8, 50), (8, 55), (9, 0)]
        ]
        return SimpleNamespace(ok=True, data={"bars": bars})


def _budgeted_ig(tmp_path, close: float, *, now_fn=None, stale_tolerance_min: int = 120) -> tuple[_FakeIGBroker, BudgetedIGBarProvider]:
    broker = _FakeIGBroker(close)
    budget = SourceBudget(tmp_path / "ig_budget.sqlite", IG_QUOTA_V1)
    # Phase 13 §6 A4: BudgetedIGBarProvider now gates fresh-history-stale. The
    # heartbeat tests bump a fake `now` (2026-08-16) but the broker's `_default_now`
    # is real time; without forwarding `now_fn` here every test would be rejected
    # by the staleness guard with reason="stale_history" — which is the very bug
    # F1 / A4 exist to catch, but only against real data, not against fixed test data.
    # `stale_tolerance_min` lets the A6.1 sampler-stale test raise the A4 ceiling
    # so the sample-side guard can fire without A4 catching the bar first.
    return broker, BudgetedIGBarProvider(
        broker, budget, spend_kind="sample",
        now_fn=now_fn, stale_tolerance_min=stale_tolerance_min,
    )


def test_sampler_throttles_to_once_per_day(archive, tmp_path):
    now = datetime(2026, 8, 16, 9, 5, tzinfo=timezone.utc)
    broker, ig = _budgeted_ig(tmp_path, 100.0, now_fn=lambda: now)
    sampler = DivergenceSampler(ig, archive, now_fn=lambda: now)
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc=f"{DAY}T09:00:00.000Z",
                              open=100, high=100, low=100, close=100.0, volume=1, source="yf",
                              fetched_at=f"{DAY}T09:00:01.000Z")])

    sampler.sample_epic(EPIC, lambda e: None, lambda e: None)
    sampler.sample_epic(EPIC, lambda e: None, lambda e: None)
    assert broker.calls == 1  # second call same day is a no-op


def test_sampler_compares_only_yf_bars_not_ig(archive, tmp_path):
    """The regression this exists to catch: an IG bar at the same minute must never be
    picked as the yFinance comparator (it would always agree with itself).

    Phase 13 §6 A6.1 + L10: the SQL filter ``sources=("yf",)`` excludes IG rows
    structurally — even if a same-minute IG bar exists in the archive, it cannot
    reach the comparison. We prove the yF row drives the check by giving the yF
    bars a different return-trend from the IG bars."""
    now = datetime(2026, 8, 16, 9, 5, tzinfo=timezone.utc)
    broker, ig = _budgeted_ig(tmp_path, 100.0, now_fn=lambda: now)
    broker.close = 100.0  # IG stays flat
    # yF bars in the probe's 5m window (09:00–09:05): rising close.
    archive.insert_bars([
        Bar(epic=EPIC, resolution="1m", ts_utc=f"{DAY}T09:00:00.000Z",
            open=90, high=90, low=90, close=90.0, volume=1, source="yf",
            fetched_at=f"{DAY}T09:00:01.000Z"),
        Bar(epic=EPIC, resolution="1m", ts_utc=f"{DAY}T09:01:00.000Z",
            open=100, high=100, low=100, close=100.0, volume=1, source="yf",
            fetched_at=f"{DAY}T09:01:01.000Z"),
    ])
    events = []
    sampler = DivergenceSampler(ig, archive, health_sink=events.append, now_fn=lambda: now)
    sampler.sample_epic(EPIC, lambda e: None, lambda e: None)
    assert len(events) == 1
    assert events[0]["event"] == "quote_divergence"
    assert events[0].get("kind") == "return"  # A6.0 marker: return-based, not level


def test_sampler_no_yf_bar_emits_typed_no_comparator_event(archive, tmp_path):
    """A6.1: kein yF-Komparator ist ein typisierter Event, nicht Stille. Genau
    die Stille war F2."""
    now = datetime(2026, 8, 16, 9, 5, tzinfo=timezone.utc)
    _, ig = _budgeted_ig(tmp_path, 100.0, now_fn=lambda: now)
    events = []
    sampler = DivergenceSampler(ig, archive, health_sink=events.append, now_fn=lambda: now)
    # archive has no bars at all for this window
    sampler.sample_epic(EPIC, lambda e: None, lambda e: None)
    assert len(events) == 1
    assert events[0]["event"] == "divergence_no_comparator"


def test_sampler_mismatch_fires_after_two_consecutive_divergences_not_one(archive, tmp_path):
    day1 = datetime(2026, 8, 16, 9, 5, tzinfo=timezone.utc)
    day2 = datetime(2026, 8, 17, 9, 5, tzinfo=timezone.utc)
    broker, ig = _budgeted_ig(tmp_path, 100.0, now_fn=lambda: day1)
    marked = []
    sampler = DivergenceSampler(ig, archive, now_fn=lambda: day1)

    broker.day = "2026-08-16"
    broker.close = 100.0
    # yF bars in the same 5m window the probe targets (09:00–09:05).
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc="2026-08-16T09:00:00.000Z",
                              open=90, high=90, low=90, close=90.0, volume=1, source="yf",
                              fetched_at="2026-08-16T09:00:01.000Z")])
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc="2026-08-16T09:01:00.000Z",
                              open=100, high=100, low=100, close=100.0, volume=1, source="yf",
                              fetched_at="2026-08-16T09:01:01.000Z")])
    sampler.sample_epic(EPIC, marked.append, lambda e: None)
    assert marked == []  # first divergence — not yet a sticky mismatch

    sampler.now_fn = lambda: day2
    broker.day = "2026-08-17"
    broker.close = 100.0
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc="2026-08-17T09:00:00.000Z",
                              open=90, high=90, low=90, close=90.0, volume=1, source="yf",
                              fetched_at="2026-08-17T09:00:01.000Z")])
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc="2026-08-17T09:01:00.000Z",
                              open=100, high=100, low=100, close=100.0, volume=1, source="yf",
                              fetched_at="2026-08-17T09:01:01.000Z")])
    sampler.sample_epic(EPIC, marked.append, lambda e: None)
    assert marked == [EPIC]  # second consecutive divergence — now mark mismatch


def test_sampler_agreement_resets_streak(archive, tmp_path):
    day1 = datetime(2026, 8, 16, 9, 5, tzinfo=timezone.utc)
    day2 = datetime(2026, 8, 17, 9, 5, tzinfo=timezone.utc)
    day3 = datetime(2026, 8, 18, 9, 5, tzinfo=timezone.utc)
    broker, ig = _budgeted_ig(tmp_path, 100.0, now_fn=lambda: day1)
    marked = []
    sampler = DivergenceSampler(ig, archive, now_fn=lambda: day1)

    broker.day = "2026-08-16"
    broker.close = 100.0
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc="2026-08-16T09:00:00.000Z",
                              open=90, high=90, low=90, close=90.0, volume=1, source="yf",
                              fetched_at="2026-08-16T09:00:01.000Z")])
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc="2026-08-16T09:01:00.000Z",
                              open=100, high=100, low=100, close=100.0, volume=1, source="yf",
                              fetched_at="2026-08-16T09:01:01.000Z")])
    sampler.sample_epic(EPIC, marked.append, lambda e: None)  # divergence 1

    sampler.now_fn = lambda: day2
    broker.day = "2026-08-17"
    broker.close = 100.0
    # Agreement: yF stable, IG stable -> no divergence, streak resets.
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc="2026-08-17T09:00:00.000Z",
                              open=100, high=100, low=100, close=100.0, volume=1, source="yf",
                              fetched_at="2026-08-17T09:00:01.000Z")])
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc="2026-08-17T09:01:00.000Z",
                              open=100, high=100, low=100, close=100.0, volume=1, source="yf",
                              fetched_at="2026-08-17T09:01:01.000Z")])
    sampler.sample_epic(EPIC, marked.append, lambda e: None)  # agreement — resets streak

    sampler.now_fn = lambda: day3
    broker.day = "2026-08-18"
    broker.close = 100.0
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc="2026-08-18T09:00:00.000Z",
                              open=90, high=90, low=90, close=90.0, volume=1, source="yf",
                              fetched_at="2026-08-18T09:00:01.000Z")])
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc="2026-08-18T09:01:00.000Z",
                              open=100, high=100, low=100, close=100.0, volume=1, source="yf",
                              fetched_at="2026-08-18T09:01:01.000Z")])
    sampler.sample_epic(EPIC, marked.append, lambda e: None)  # divergence 1 again (not 3rd consecutive)

    assert marked == []


def test_sampler_stale_ig_emits_event_and_marks_stale(archive, tmp_path):
    """A6.1: F1 — IG liefert eine Bar, die älter als stale_tolerance_min ist. Der
    Sampler ruft mark_stale_fn + emittiert ein stale_source-Event, statt einen
    Vergleich zu fälschen, der gegen die tote Historie „stimmen würde"."""
    from data_foundation.models import DS_STALE_SOURCE
    # Broker produces bars at 2026-08-16T09:00:00; the provider's now_fn is 3 days
    # later — exactly the F1 situation (Plan §4 F1, IX.D.IBEX.FWM2.IP).
    broker_now = datetime(2026, 8, 16, 9, 5, tzinfo=timezone.utc)
    fresh_now = datetime(2026, 8, 19, 9, 5, tzinfo=timezone.utc)
    broker, ig = _budgeted_ig(
        tmp_path, 100.0, now_fn=lambda: fresh_now,
        stale_tolerance_min=7 * 24 * 60,  # A4 ceiling way up: let the bar through
    )
    events, marked_stale = [], []
    sampler = DivergenceSampler(
        ig, archive, health_sink=events.append,
        now_fn=lambda: fresh_now, stale_tolerance_min=120,
    )
    sampler.sample_epic(EPIC, lambda e: None, marked_stale.append)
    assert len(events) == 1
    assert events[0]["event"] == "stale_source"
    assert events[0]["provider"] == "ig"
    assert marked_stale == [EPIC]  # caller would set data_source_status=DS_STALE_SOURCE
    assert DS_STALE_SOURCE == "stale_source"  # symbol available for A6 callers


def test_sampler_budget_veto_is_a_noop(archive):
    class _RefusingIG:
        def get_bars(self, epic, *, resolution, count):
            return None

    events = []
    sampler = DivergenceSampler(_RefusingIG(), archive, health_sink=events.append)
    sampler.sample_epic(EPIC, lambda e: None, lambda e: None)
    assert events == []


# -- Phase 16 §3 J3: coverage on the Berlin trading session ----------------------------


def _insert_session_yf_bars(archive, epic: str, day: str) -> int:
    """Insert one yF bar per minute from Berlin 09:00 to Berlin 17:30 of ``day``
    (= UTC 07:00 to 15:30, CEST summer-time). Mirrors the production Recorder
    output: dense during the session, nothing overnight. Used by the J3 session-
    window tests below."""
    from datetime import datetime, timedelta, timezone
    from zoneinfo import ZoneInfo
    tz_berlin = ZoneInfo("Europe/Berlin")
    start_local = datetime.strptime(day, "%Y-%m-%d").replace(hour=9, minute=0, tzinfo=tz_berlin)
    end_local = start_local + timedelta(hours=8, minutes=30)  # 09:00 → 17:30 Berlin
    start_utc = start_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)
    bars: list = []
    cur = start_utc
    while cur < end_utc:
        ts = cur.strftime("%Y-%m-%dT%H:%M:00.000Z")
        bars.append(Bar(epic=epic, resolution="1m", ts_utc=ts,
                        open=1, high=1, low=1, close=1, volume=1, source="yf",
                        fetched_at=ts))
        cur += timedelta(minutes=1)
    archive.insert_bars(bars)
    return len(bars)


def test_assess_day_ok_with_session_only_bars(archive, db_path):
    """Phase 16 §3 J3 regression pin: bars *only* during the trading session (no
    overnight bars, no gap inside) ⇒ coverage window = session window ⇒
    ``worst_coverage ≈ 1.0`` ⇒ no ``epics_below_threshold`` ⇒ K4 can be PASS.

    Pre-J3 the coverage window was 00:00–24:00, so a session-only fixture
    (510 of 1440 minutes present) read ``worst_coverage = 0.35`` and tripped
    the gap threshold via the overnight hole — K4 unreachable every day.
    """
    _insert_universe_row(db_path, EPIC)
    _insert_session_yf_bars(archive, EPIC, DAY)
    _insert_paper_trade(db_path, created_utc=f"{DAY}T09:00:00.000Z", status="RESOLVED",
                         resolved_utc=f"{DAY}T10:00:00.000Z", exit_reason="TP")

    verdict = assess_day(archive, db_path, db_path, DAY, shadow_enabled=True)
    assert verdict.ok is True, f"problems={verdict.problems}"
    assert verdict.epics_below_threshold == []
    # 8.5h session window minus 30min lag tolerance = 8h exactly = 480 minutes,
    # all present (510 minutes inserted - some past the lag-trimmed end).
    assert verdict.worst_coverage == pytest.approx(1.0, abs=0.01), (
        f"session-only bars must read as full coverage; got worst_coverage={verdict.worst_coverage}"
    )


def test_assess_day_flags_gap_inside_session(archive, db_path):
    """Phase 16 §3 J3 Gegenprobe: a real 20-min gap **inside** the session must
    still read as ``epics_below_threshold`` — the window moved from 00–24h to
    09–17:30, but the "no 5-min gap inside the window" contract (Phase-13 F3) is
    unchanged. A gap at 10:00–10:20 Berlin (= 08:00–08:20 UTC) is 20 min > 5 min.
    """
    _insert_universe_row(db_path, EPIC)
    # Insert session bars except skip 08:00–08:19 UTC (= 10:00–10:19 Berlin).
    from datetime import datetime, timedelta, timezone
    from zoneinfo import ZoneInfo
    tz_berlin = ZoneInfo("Europe/Berlin")
    start_local = datetime.strptime(DAY, "%Y-%m-%d").replace(hour=9, minute=0, tzinfo=tz_berlin)
    start_utc = start_local.astimezone(timezone.utc)
    bars: list = []
    cur = start_utc
    skipped_start = datetime.strptime(DAY, "%Y-%m-%d").replace(hour=8, minute=0, tzinfo=timezone.utc)
    skipped_end = skipped_start + timedelta(minutes=20)
    while cur < start_utc + timedelta(hours=8, minutes=30):
        if skipped_start <= cur < skipped_end:
            cur += timedelta(minutes=1)
            continue
        ts = cur.strftime("%Y-%m-%dT%H:%M:00.000Z")
        bars.append(Bar(epic=EPIC, resolution="1m", ts_utc=ts,
                        open=1, high=1, low=1, close=1, volume=1, source="yf",
                        fetched_at=ts))
        cur += timedelta(minutes=1)
    archive.insert_bars(bars)
    _insert_paper_trade(db_path, created_utc=f"{DAY}T09:00:00.000Z", status="RESOLVED",
                         resolved_utc=f"{DAY}T10:00:00.000Z", exit_reason="TP")

    verdict = assess_day(archive, db_path, db_path, DAY, shadow_enabled=True)
    assert verdict.ok is False, (
        "a 20-min gap inside the session must trip epics_below_threshold; "
        f"verdict={verdict}"
    )
    assert EPIC in verdict.epics_below_threshold
    assert any("below the coverage threshold" in p for p in verdict.problems)


def test_assess_day_tolerates_lagging_recorder_tail(archive, db_path):
    """Phase 16 §3 J5 regression pin: a Recorder that lags the session by < 30 min
    must NOT read as a coverage gap. The Recorder measured ~18 min behind wall-
    clock on 2026-09-08 08:48 UTC (last yF bar 08:30 UTC, wall clock 08:48 UTC)
    — without the lag trim the trailing 18-min hole would falsely trip
    ``largest_gap_min > 5`` exactly at session close.

    The trim is :data:`RECORDER_LAG_TOLERANCE_MIN` = 30 min, so we deliberately
    cut the last 20 minutes of bars (well inside the 30-min slack) and assert
    PASS. Without the trim the verdict would still be FAIL — that's the
    regression we're guarding.
    """
    _insert_universe_row(db_path, EPIC)
    # Session bars from Berlin 09:00 to Berlin 17:10 (= UTC 07:00 to 15:10)
    # — 20 minutes short of session close 17:30 (= UTC 15:30), still well
    # inside the 30-min lag tolerance.
    from datetime import datetime, timedelta, timezone
    from zoneinfo import ZoneInfo
    tz_berlin = ZoneInfo("Europe/Berlin")
    start_local = datetime.strptime(DAY, "%Y-%m-%d").replace(hour=9, minute=0, tzinfo=tz_berlin)
    end_local = start_local + timedelta(hours=8, minutes=10)  # 09:00 → 17:10 Berlin
    start_utc = start_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)
    bars: list = []
    cur = start_utc
    while cur < end_utc:
        ts = cur.strftime("%Y-%m-%dT%H:%M:00.000Z")
        bars.append(Bar(epic=EPIC, resolution="1m", ts_utc=ts,
                        open=1, high=1, low=1, close=1, volume=1, source="yf",
                        fetched_at=ts))
        cur += timedelta(minutes=1)
    archive.insert_bars(bars)
    _insert_paper_trade(db_path, created_utc=f"{DAY}T09:00:00.000Z", status="RESOLVED",
                         resolved_utc=f"{DAY}T10:00:00.000Z", exit_reason="TP")

    verdict = assess_day(archive, db_path, db_path, DAY, shadow_enabled=True)
    assert verdict.ok is True, (
        f"lagging Recorder tail within tolerance must not fail K4; problems={verdict.problems}"
    )
    assert verdict.epics_below_threshold == []
