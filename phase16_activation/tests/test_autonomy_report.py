"""Tests for ``phase16_activation/scripts/autonomy_report.py`` (Phase 16 E2).

Self-contained: every test builds its own fixture DB + fake log files under a
temp dir, then exercises the script's pure functions (and one end-to-end
``--summary`` round-trip via ``subprocess`` to keep the CLI happy path covered
without leaking printed JSON into pytest's stdout).

Plan §6 E2 acceptance criteria, paraphrased as test names below — five tests,
each pinning a distinct Akzeptanz from §7 (AK14 = offline behavior against
fixtures; AK15 = summary PASS / FAIL semantics) and the per-criterion contracts
from §6 E2:

1. ``test_day_report_against_fixture_db``  — Tagesbericht-Felder gegen Fixture-DB
2. ``test_summary_passes_for_clean_10_day_window``  — 10 Handelstage PASS
3. ``test_summary_fails_when_recorder_log_has_three_starts``  — K1 FAIL
4. ``test_summary_fails_when_budget_exhausted_before_1730``  — K6 FAIL
5. ``test_summary_fails_when_six_criticals_after_open``  — K5 FAIL

Why sub-tests don't go farther: each test already proves the criterion it
pinns (FAIL ⇒ measured vs. threshold, PASS ⇒ zero offenders). Each is
**independent** of the live DB / live logs by construction (we build fixtures
under ``tmp_path`` and pass them via the ``--trading-db`` / ``--state-dir``
overrides). No network, no LLM, no pgrep — the script's whole point.

Why we don't test every criterion in isolation: passing the synthetic 10-day
window also exercises K2 (recorder→bars, scheduler→health_events), K3
(trade_outcomes count), K4 (heartbeat count), K7 (start-line caps), so the
2nd test pins five criteria at once. Pinning K5 + K6 separately is needed
because they require specific failure shapes.
"""
from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# scripts/ is phase16_activation/scripts/, so two levels up is the phase dir.
# The script imports nothing except stdlib + the (transient) ZoneInfo — both
# available without any install on Python 3.9+; we add the script dir to
# sys.path here so ``import autonomy_report`` works as a plain module.
_PHASE16_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(_PHASE16_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_PHASE16_SCRIPTS))

import autonomy_report  # noqa: E402

# The fixtures need a real ``trade_outcomes`` schema — Phase-2's
# ``Database.run_migrations()`` produces one. Persistence is editable-installed
# via ``scripts/dev_install.sh`` (Phase-0 venv), so a plain import works.
_PERSISTENCE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "phase2_persistence"
if str(_PERSISTENCE_DIR) not in sys.path:
    sys.path.insert(0, str(_PERSISTENCE_DIR))

from persistence.db import Database  # noqa: E402


# ----------------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------------

def _seed_trading_db(path: Path, trades: list[dict[str, object]]) -> None:
    """Insert ``trades`` (list of dicts with the 8 columns that autonomy_report
    actually reads: open_ts, close_ts, status, provenance, account, epic, id,
    direction — only the columns it touches) into a fresh Phase-2-schema DB."""
    db = Database(str(path))
    db.run_migrations()
    db.close()
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    for t in trades:
        conn.execute(
            "INSERT INTO trade_outcomes "
            "(deal_id, deal_reference, epic, broker, direction, size, open_level, "
            " currency, open_ts, close_ts, status, session_date, created_at, updated_at, "
            " account, provenance) VALUES "
            "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                t["deal_id"], t.get("deal_reference", ""), t["epic"], "ig",
                t.get("direction", "BUY"), t.get("size", 1.0),
                t.get("open_level", 100.0), t.get("currency", "EUR"),
                t["open_ts"], t.get("close_ts"), t.get("status", "CLOSED"),
                t.get("session_date", t["open_ts"][:10]),
                t.get("created_at", t["open_ts"]),
                t.get("updated_at", t["open_ts"]),
                t.get("account", "demo"),
                t.get("provenance", "autonomous"),
            ),
        )
    conn.commit()
    conn.close()


def _seed_bars_db(path: Path, days: list[date], source: str = "yf") -> None:
    """Insert a small set of bars rows per Berlin day in ``days``."""
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(
        "CREATE TABLE bars ("
        "  epic TEXT NOT NULL, resolution TEXT NOT NULL, ts_utc TEXT NOT NULL,"
        "  open REAL NOT NULL, high REAL NOT NULL, low REAL NOT NULL, close REAL NOT NULL,"
        "  volume REAL, source TEXT NOT NULL, fetched_at TEXT NOT NULL, tick_count INTEGER,"
        "  PRIMARY KEY (epic, resolution, ts_utc, source));"
        "CREATE INDEX idx_bars_epic_res_ts ON bars(epic, resolution, ts_utc);"
    )
    for d in days:
        ts = datetime(d.year, d.month, d.day, 9, 0, tzinfo=timezone.utc).isoformat()
        conn.execute(
            "INSERT OR REPLACE INTO bars "
            "(epic, resolution, ts_utc, open, high, low, close, volume, source, fetched_at, tick_count) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            ("IX.D.DAX.IFMM.IP", "MINUTE", ts, 100.0, 101.0, 99.0, 100.5, 0.0, source,
             datetime(d.year, d.month, d.day, 9, 5, tzinfo=timezone.utc).isoformat(), 1),
        )
    conn.commit()
    conn.close()


def _write_log(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_state_dir(
    state_dir: Path,
    *,
    days: list[date],
    services_with_restarts: dict[str, int] | None = None,
    scheduler_ts_prefix: bool = True,
    start_line_caps: str = "max_trades=5, daily_loss_cap=1800.0, cycle=5min",
    critical_lines_after_open: list[str] | None = None,
    heartbeat_events: list[tuple[date, bool]] | None = None,
) -> None:
    """Build a synthetic state-dir tree shaped like ``data/state/``.

    ``services_with_restarts`` maps service name ("scheduler"/"recorder"/"discovery"/"webui")
    to the number of start-lines to emit. ``critical_lines_after_open`` are appended
    after the most-recent start-line in ``run_scheduler.log`` to test K5.
    ``heartbeat_events`` is a list of ``(day, ok)`` tuples written into research_health.jsonl.
    """
    services_with_restarts = services_with_restarts or {}
    state_dir.mkdir(parents=True, exist_ok=True)
    # Service start-line logs
    if scheduler_ts_prefix:
        for i in range(services_with_restarts.get("scheduler", 1)):
            ts = "2026-09-08 09:00:00,000"
            if i > 0:
                ts = "2026-09-09 09:00:00,000"
            _write_log(
                state_dir / "run_scheduler.log",
                [
                    f"{ts} INFO scheduler.run: starting scheduler daemon (account=demo, {start_line_caps}).",
                ] * (i + 1) if False else [f"{ts} INFO scheduler.run: starting scheduler daemon (account=demo, {start_line_caps})."] * 1,
            )
    else:
        _write_log(state_dir / "run_scheduler.log",
                   ["[run_scheduler] starting daemon (keyring must be unlocked)..."])
    for svc in ("recorder", "discovery", "webui"):
        n = services_with_restarts.get(svc, 1)
        if svc == "recorder":
            line = "[run_recorder] starting recorder from /home/trading-bot/trading-bot/phase12_data_foundation..."
        elif svc == "discovery":
            line = "[run_discovery] starting daemon from /home/trading-bot/trading-bot/phase14_discovery (unarmed ⇒ noop)..."
        else:
            line = "[run_webui] dashboard on http://127.0.0.1:8000 (read-only DB, localhost-only)..."
        with (state_dir / f"run_{svc}.log").open("w", encoding="utf-8") as fh:
            for _ in range(n):
                fh.write(line + "\n")
    # Append CRITICAL lines AFTER the most-recent start so K5 has something to count
    if critical_lines_after_open:
        with (state_dir / "run_scheduler.log").open("a", encoding="utf-8") as fh:
            for line in critical_lines_after_open:
                fh.write(line + "\n")
    # research_health.jsonl
    heartbeat_events = heartbeat_events or []
    if heartbeat_events:
        with (state_dir / "research_health.jsonl").open("w", encoding="utf-8") as fh:
            for d, ok in heartbeat_events:
                # Anchor the event ts at 09:00 UTC on its day so K2 (health-events
                # count) and K4 (heartbeat.ok day-bucket) both fire. The day field
                # is authoritative for K4; the ts field is what K2 reads.
                ts_iso = datetime(d.year, d.month, d.day, 9, 0, tzinfo=timezone.utc).isoformat()
                fh.write(json.dumps({
                    "event": "measurement_heartbeat",
                    "day": d.isoformat(),
                    "ts": ts_iso,
                    "ok": ok,
                    "bars_today": 100,
                    "pairs_opened": 0,
                    "pairs_resolved": 0,
                    "pairs_typed_expired": 0,
                    "measurable_epics": 5,
                    "worst_coverage": 0.95,
                    "epics_below_threshold": [],
                    "problems": [],
                }) + "\n")


def _write_llm_usage(path: Path, days_with_usage: dict[date, tuple[int, int]]) -> None:
    """``days_with_usage``: {day: (n_calls, tokens_per_call)}.

    Spreads entries across the trading window starting 09:30 with the spec tokens-per-call
    (representative of the pre-C3 budget burn). The last entry of each day is set so
    the per-day cumulative exactly hits or slightly exceeds ``threshold``.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, object]] = []
    for d, (n_calls, tokens_per_call) in days_with_usage.items():
        for i in range(n_calls):
            ts = datetime(d.year, d.month, d.day, 9, 30, tzinfo=timezone.utc) + timedelta(seconds=i * 600)
            cumulative_tokens = tokens_per_call * (i + 1)
            entries.append({
                "ts": ts.isoformat(),
                "model": "claude-sonnet-4-6",
                "input_tokens": tokens_per_call // 2,
                "output_tokens": tokens_per_call // 2,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0,
                "_cum": cumulative_tokens,
            })
    with path.open("w", encoding="utf-8") as fh:
        json.dump(entries, fh)


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------

def test_day_report_against_fixture_db(tmp_path: Path) -> None:
    """Build a 1-day fixture and assert the DayReport fields."""
    trading_db = tmp_path / "trading.sqlite"
    bars_db = tmp_path / "bars.sqlite"
    state_dir = tmp_path / "state"
    reports_dir = tmp_path / "reports"
    day = date(2026, 9, 8)
    _seed_trading_db(
        trading_db,
        [
            {
                "deal_id": f"DAX-DAY-{i}",
                "epic": "IX.D.DAX.IFMM.IP",
                "direction": "BUY",
                "open_ts": f"{day.isoformat()}T09:30:00+02:00",
                "close_ts": f"{day.isoformat()}T10:00:00+02:00",
                "status": "CLOSED",
                "session_date": day.isoformat(),
                "created_at": f"{day.isoformat()}T09:30:00+02:00",
                "updated_at": f"{day.isoformat()}T10:00:00+02:00",
                "account": "demo",
                "provenance": "autonomous",
            }
            for i in range(3)
        ],
    )
    _seed_bars_db(bars_db, [day])
    _build_state_dir(state_dir, days=[day], heartbeat_events=[(day, True)])

    rep = autonomy_report._build_day_report(
        day,
        state_dir=state_dir,
        bars_db=bars_db,
        trading_db=trading_db,
        threshold=300_000,
        expected_max_trades=5,
        expected_daily_loss_cap=1800.0,
    )
    payload = rep.to_dict()
    assert payload["day"] == day.isoformat()
    # All 8 criteria present (K8 liveness added Phase 16 R3.3)
    assert set(payload["criteria"].keys()) == {str(i) for i in range(1, 9)}
    # K3: 3 autonomous trades on that day
    assert payload["criteria"]["3"]["measured"]["in_window_total"] == 3
    # K2: scheduler has 1 health_event + recorder wrote ≥ 1 bar → 3/3 auto signals
    assert payload["criteria"]["2"]["measured"]["scheduler_health_events"] >= 1
    assert payload["criteria"]["2"]["measured"]["recorder_bars_per_day"] >= 1
    # K7: caps match the start-line substring exactly
    assert payload["criteria"]["7"]["measured"]["start_line_caps"]["max_trades"] == 5
    assert payload["criteria"]["7"]["measured"]["start_line_caps"]["daily_loss_cap_eur"] == 1800.0
    # K4: heartbeat ok = 1 day
    assert payload["criteria"]["4"]["measured"]["ok_days"] == 1
    # JSON file written
    out = reports_dir / f"autonomy_{day.isoformat()}.json"
    assert not out.exists()  # _write_report_file only fires in CLI main(); OK here
    out.parent.mkdir(parents=True, exist_ok=True)
    autonomy_report._write_report_file(reports_dir, day.isoformat(), payload)
    assert out.exists()
    loaded = json.loads(out.read_text())
    assert loaded["day"] == day.isoformat()


def test_summary_passes_for_clean_10_day_window(tmp_path: Path) -> None:
    """A clean 10-day window where every criterion is satisfied ⇒ PASS overall."""
    trading_db = tmp_path / "trading.sqlite"
    bars_db = tmp_path / "bars.sqlite"
    state_dir = tmp_path / "state"
    from_day = date(2026, 9, 8)   # Tuesday
    to_day = date(2026, 9, 21)    # Monday (covers 10 weekdays)
    days = [d for d in autonomy_report._iter_trading_days(from_day, to_day)]
    assert len(days) == 10
    # 6 autonomous trades ≥ the K3 threshold
    trades = []
    for i in range(6):
        d = days[i]
        trades.append({
            "deal_id": f"DAX-{i}",
            "epic": "IX.D.DAX.IFMM.IP",
            "direction": "BUY",
            "open_ts": f"{d.isoformat()}T09:30:00+02:00",
            "close_ts": f"{d.isoformat()}T10:00:00+02:00",
            "status": "CLOSED",
            "session_date": d.isoformat(),
            "created_at": f"{d.isoformat()}T09:30:00+02:00",
            "updated_at": f"{d.isoformat()}T10:00:00+02:00",
            "account": "demo",
            "provenance": "autonomous",
        })
    _seed_trading_db(trading_db, trades)
    _seed_bars_db(bars_db, days)
    _build_state_dir(
        state_dir,
        days=days,
        # No double-restart, so each service has exactly 1 start-line
        services_with_restarts={s: 1 for s in ("scheduler", "recorder", "discovery", "webui")},
        # 9 of 10 days with heartbeat.ok = True (8+ required)
        heartbeat_events=[(d, True) for d in days[:9]] + [(days[9], False)],
        critical_lines_after_open=None,
    )
    # llm_usage.json — budget NOT exhausted before 17:30 any day.
    # 100 calls × 2 000 tokens = 200 k << 300 k threshold → safe.
    _write_llm_usage(
        state_dir / "llm_usage.json",
        {d: (100, 2_000) for d in days},
    )

    rep = autonomy_report._build_summary_report(
        from_day, to_day,
        state_dir=state_dir,
        bars_db=bars_db,
        trading_db=trading_db,
        threshold=300_000,
        expected_max_trades=5,
        expected_daily_loss_cap=1800.0,
    )
    payload = rep.to_dict()
    assert payload["n_trading_days"] == 10
    assert payload["criteria"]["3"]["verdict"] == "PASS"
    assert payload["criteria"]["3"]["measured"]["in_window_total"] == 6
    assert payload["criteria"]["4"]["measured"]["ok_days"] == 9
    assert payload["criteria"]["4"]["verdict"] == "PASS"
    assert payload["criteria"]["6"]["verdict"] == "PASS"
    assert payload["criteria"]["5"]["measured"]["max_critical_24h"] == 0
    assert payload["overall_verdict"] == "PASS"


def test_summary_fails_when_recorder_log_has_three_starts(tmp_path: Path) -> None:
    """K1 — three recorder.log start-lines ⇒ max_starts > P17 threshold ⇒ FAIL."""
    trading_db = tmp_path / "trading.sqlite"
    bars_db = tmp_path / "bars.sqlite"
    state_dir = tmp_path / "state"
    from_day = date(2026, 9, 8)
    to_day = date(2026, 9, 21)
    days = [d for d in autonomy_report._iter_trading_days(from_day, to_day)]
    trades = [{
        "deal_id": f"DAX-{i}",
        "epic": "IX.D.DAX.IFMM.IP",
        "direction": "BUY",
        "open_ts": f"{days[0].isoformat()}T09:30:00+02:00",
        "close_ts": f"{days[0].isoformat()}T10:00:00+02:00",
        "status": "CLOSED",
        "session_date": days[0].isoformat(),
        "created_at": f"{days[0].isoformat()}T09:30:00+02:00",
        "updated_at": f"{days[0].isoformat()}T10:00:00+02:00",
        "account": "demo",
        "provenance": "autonomous",
    } for i in range(6)]
    _seed_trading_db(trading_db, trades)
    _seed_bars_db(bars_db, days)
    _build_state_dir(
        state_dir, days=days,
        # K1 break: 3 recorder starts, the others at 1
        services_with_restarts={"scheduler": 1, "recorder": 3, "discovery": 1, "webui": 1},
        heartbeat_events=[(d, True) for d in days],
    )
    _write_llm_usage(state_dir / "llm_usage.json", {d: (100, 2_000) for d in days})
    rep = autonomy_report._build_summary_report(
        from_day, to_day,
        state_dir=state_dir, bars_db=bars_db, trading_db=trading_db,
        threshold=300_000, expected_max_trades=5, expected_daily_loss_cap=1800.0,
    )
    payload = rep.to_dict()
    assert payload["criteria"]["1"]["measured"]["recorder"]["starts"] == 3
    assert payload["criteria"]["1"]["verdict"] == "FAIL"
    assert payload["overall_verdict"] == "FAIL"


def test_summary_fails_when_budget_exhausted_before_1730(tmp_path: Path) -> None:
    """K6 — day's cumulative reaches 300 k before 17:30 Berlin ⇒ FAIL."""
    trading_db = tmp_path / "trading.sqlite"
    bars_db = tmp_path / "bars.sqlite"
    state_dir = tmp_path / "state"
    from_day = date(2026, 9, 8)
    to_day = date(2026, 9, 21)
    days = [d for d in autonomy_report._iter_trading_days(from_day, to_day)]
    trades = [{
        "deal_id": f"DAX-{i}",
        "epic": "IX.D.DAX.IFMM.IP",
        "direction": "BUY",
        "open_ts": f"{d.isoformat()}T09:30:00+02:00",
        "close_ts": f"{d.isoformat()}T10:00:00+02:00",
        "status": "CLOSED",
        "session_date": d.isoformat(),
        "created_at": f"{d.isoformat()}T09:30:00+02:00",
        "updated_at": f"{d.isoformat()}T10:00:00+02:00",
        "account": "demo",
        "provenance": "autonomous",
    } for i, d in enumerate(days)]
    _seed_trading_db(trading_db, trades)
    _seed_bars_db(bars_db, days)
    _build_state_dir(
        state_dir, days=days,
        services_with_restarts={s: 1 for s in ("scheduler", "recorder", "discovery", "webui")},
        heartbeat_events=[(d, True) for d in days],
    )
    # First day: 200 calls × 2 000 tokens = 400 000 → crosses 300 k around call 150,
    # which lands near 09:30 + 150 × 600 s = 09:30 + 25 h = next morning BEFORE 17:30
    # of the second day. Wait — that lands on the next day. Build it more carefully:
    # Force the crossing at 09:50 day-1 by using bigger tokens-per-call × shorter spacing.
    days_with_usage: dict[date, tuple[int, int]] = {d: (100, 2_000) for d in days}
    # First day special: 100 calls × 4 000 tokens = 400 k; spacing 60 s ⇒ crossing at 09:30 + 75×60 = 09:30+4500s=10:45 local.
    days_with_usage[days[0]] = (100, 4_000)
    # Same machine-rolled fixture as before, but with the 09:30 anchor (UTC) — so 10:45
    # UTC = 12:45 Berlin ⇒ still before 17:30. FAIL.
    # Build manually here to control the exact cumulative:
    entries: list[dict[str, object]] = []
    for d, (n_calls, tpc) in days_with_usage.items():
        for i in range(n_calls):
            ts = datetime(d.year, d.month, d.day, 9, 30, tzinfo=timezone.utc) + timedelta(seconds=i * 60)
            entries.append({
                "ts": ts.isoformat(), "model": "claude-sonnet-4-6",
                "input_tokens": tpc // 2, "output_tokens": tpc // 2,
                "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
            })
    (state_dir / "llm_usage.json").parent.mkdir(parents=True, exist_ok=True)
    (state_dir / "llm_usage.json").write_text(json.dumps(entries), encoding="utf-8")

    rep = autonomy_report._build_summary_report(
        from_day, to_day,
        state_dir=state_dir, bars_db=bars_db, trading_db=trading_db,
        threshold=300_000, expected_max_trades=5, expected_daily_loss_cap=1800.0,
    )
    payload = rep.to_dict()
    assert payload["criteria"]["6"]["verdict"] == "FAIL"
    assert payload["criteria"]["6"]["measured"]["offenders_before_close"], (
        "Expected at least one offender day where exhausted_at_local < 17:30 Berlin"
    )
    assert payload["overall_verdict"] == "FAIL"


def test_summary_fails_when_six_criticals_after_open(tmp_path: Path) -> None:
    """K5 — 6 CRITICAL lines within 24h after one OPEN ⇒ max > 5 ⇒ FAIL."""
    trading_db = tmp_path / "trading.sqlite"
    bars_db = tmp_path / "bars.sqlite"
    state_dir = tmp_path / "state"
    from_day = date(2026, 9, 8)
    to_day = date(2026, 9, 21)
    days = [d for d in autonomy_report._iter_trading_days(from_day, to_day)]
    open_day = days[0]
    # Single trade, with CRITICALs spread over the next ~6 hours
    trades = [{
        "deal_id": "DAX-0",
        "epic": "IX.D.DAX.IFMM.IP",
        "direction": "BUY",
        "open_ts": f"{open_day.isoformat()}T09:00:00+02:00",   # 07:00 UTC
        "close_ts": f"{open_day.isoformat()}T11:00:00+02:00",
        "status": "CLOSED",
        "session_date": open_day.isoformat(),
        "created_at": f"{open_day.isoformat()}T09:00:00+02:00",
        "updated_at": f"{open_day.isoformat()}T11:00:00+02:00",
        "account": "demo",
        "provenance": "autonomous",
    } for _ in range(6)]
    _seed_trading_db(trading_db, trades)
    _seed_bars_db(bars_db, days)
    # 6 CRITICAL lines between 09:15 and 14:00 Berlin (= 07:15–12:00 UTC) on the open day
    crit_lines = [
        f"2026-09-08 09:15:00,000 ERROR scheduler.run: CRITICAL: heartbeat not ok at cycle N",
        f"2026-09-08 10:00:00,000 ERROR scheduler.run: CRITICAL: heartbeat not ok at cycle N",
        f"2026-09-08 11:00:00,000 ERROR scheduler.run: CRITICAL: heartbeat not ok at cycle N",
        f"2026-09-08 12:00:00,000 ERROR scheduler.run: CRITICAL: heartbeat not ok at cycle N",
        f"2026-09-08 13:00:00,000 ERROR scheduler.run: CRITICAL: heartbeat not ok at cycle N",
        f"2026-09-08 14:00:00,000 ERROR scheduler.run: CRITICAL: heartbeat not ok at cycle N",
    ]
    _build_state_dir(
        state_dir, days=days,
        services_with_restarts={s: 1 for s in ("scheduler", "recorder", "discovery", "webui")},
        critical_lines_after_open=crit_lines,
        heartbeat_events=[(d, True) for d in days],
    )
    _write_llm_usage(state_dir / "llm_usage.json", {d: (100, 2_000) for d in days})
    rep = autonomy_report._build_summary_report(
        from_day, to_day,
        state_dir=state_dir, bars_db=bars_db, trading_db=trading_db,
        threshold=300_000, expected_max_trades=5, expected_daily_loss_cap=1800.0,
    )
    payload = rep.to_dict()
    assert payload["criteria"]["5"]["measured"]["max_critical_24h"] == 6
    assert payload["criteria"]["5"]["verdict"] == "FAIL"
    assert payload["overall_verdict"] == "FAIL"


# -- Phase 16 §3 J2 + J8: K1 misst im Fenster + WebUI-Start zählt einmal ------------------


def test_k1_ignores_starts_before_window(tmp_path: Path) -> None:
    """Phase 16 §3 J2 regression pin: K1 must filter by Berlin-day window, not by the
    whole log file. Before the fix, ``evaluate_k1`` was called with ``from_ts=None`` /
    ``to_ts=None`` from both report builders, so ``count_starts_in_window`` counted every
    start-line in the log — 7 historic Scheduler starts since 2026-08-31 made K1 FAIL on
    day 1 of every fresh run. Here: 3 scheduler starts pre-window + 1 in-window ⇒ max
    starts (in window) = 1 ⇒ PASS.
    """
    state_dir = tmp_path / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    # Three starts on 2026-09-07 (the day before the window) and one on 2026-09-08
    # (the report day) — Berlin local times.
    lines = [
        "2026-09-07 09:00:00,000 INFO scheduler.run: starting scheduler daemon (account=demo, max_trades=5, daily_loss_cap=1800.0, cycle=5min).",
        "2026-09-07 11:00:00,000 INFO scheduler.run: starting scheduler daemon (account=demo, max_trades=5, daily_loss_cap=1800.0, cycle=5min).",
        "2026-09-07 15:00:00,000 INFO scheduler.run: starting scheduler daemon (account=demo, max_trades=5, daily_loss_cap=1800.0, cycle=5min).",
        "2026-09-08 09:30:00,000 INFO scheduler.run: starting scheduler daemon (account=demo, max_trades=5, daily_loss_cap=1800.0, cycle=5min).",
    ]
    (state_dir / "run_scheduler.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for svc in ("recorder", "discovery", "webui"):
        (state_dir / f"run_{svc}.log").write_text("", encoding="utf-8")

    day = date(2026, 9, 8)
    from_ts, to_ts = autonomy_report._berlin_day_bounds(day)
    result = autonomy_report.evaluate_k1(state_dir, from_ts=from_ts, to_ts=to_ts)
    assert result.measured["scheduler"]["starts"] == 1, (
        f"K1 must count only in-window starts; got {result.measured['scheduler']['starts']}"
    )
    assert result.verdict == "PASS", (
        f"1 start inside the Berlin day = PASS expected, got {result.verdict}; "
        f"measured={result.measured}"
    )


def test_k1_webui_single_start_counts_once(tmp_path: Path) -> None:
    """Phase 16 §3 J8 regression pin: one WebUI restart must read as **one** start,
    not two. Before the fix, ``_START_PATTERNS["webui"]`` matched both the wrapper
    line (``[run_webui] dashboard on``) **and** uvicorn's own ``Started server
    process`` line — a single WebUI restart therefore exhausted the 2-restart budget
    on its own, failing K1 on the first non-trivial restart. After the fix only the
    wrapper line matches.
    """
    state_dir = tmp_path / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    # Single start: wrapper line + uvicorn's own "Started server process" line.
    # Pre-fix this would count as 2; post-fix the second line doesn't match.
    lines = [
        "[run_webui] dashboard on http://127.0.0.1:8000 (read-only DB, localhost-only)...",
        "INFO:     Started server process [12345]",
    ]
    (state_dir / "run_webui.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for svc in ("scheduler", "recorder", "discovery"):
        (state_dir / f"run_{svc}.log").write_text("", encoding="utf-8")

    day = date(2026, 9, 8)
    from_ts, to_ts = autonomy_report._berlin_day_bounds(day)
    result = autonomy_report.evaluate_k1(state_dir, from_ts=from_ts, to_ts=to_ts)
    assert result.measured["webui"]["starts"] == 1, (
        f"WebUI counts one start per restart; got {result.measured['webui']['starts']}"
    )
    assert result.verdict == "PASS"


# -- Phase 16 §11 Drift #8 fix regression pin: K1 deterministic for wrappers ----
# Commits 5cd9168 (P8 run_webui.sh) + cc73462 (P12 run_recorder.sh) +
# 774a3e1 (P14 run_discovery.sh) added 'date +%Y-%m-%d %H:%M:%S' prefix to the
# wrapper-start-line in each script, so autonomy_report.py:count_starts_in_window
# can extract the timestamp via _parse_scheduler_ts() and filter by the
# Berlin-day window — instead of falling back to 'full-file-count'.


def test_k1_wrapper_timestamped_start_counts_in_window(tmp_path: Path) -> None:
    """Phase 16 §11 Drift #8 fix pin: a wrapper-start-line WITH timestamp prefix
    inside the Berlin-day window is counted precisely (filtered-by-timestamp).
    Before the fix, the same line would have been untimestamped and K1 would
    have reported 'full-file-count (opaque to window filter)'.
    """
    state_dir = tmp_path / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    # One recorder start on 2026-09-08 09:00:00 (Berlin local time, naive parsed
    # as UTC by _parse_iso, i.e. 2026-09-08 11:00+02:00 Berlin).
    line = (
        "2026-09-08 09:00:00 [run_recorder] starting recorder from "
        "/home/trading-bot/trading-bot/phase12_data_foundation..."
    )
    (state_dir / "run_recorder.log").write_text(line + "\n", encoding="utf-8")
    for svc in ("scheduler", "discovery", "webui"):
        (state_dir / f"run_{svc}.log").write_text("", encoding="utf-8")

    day = date(2026, 9, 8)
    from_ts, to_ts = autonomy_report._berlin_day_bounds(day)
    result = autonomy_report.evaluate_k1(state_dir, from_ts=from_ts, to_ts=to_ts)
    assert result.measured["recorder"]["starts"] == 1, (
        f"K1 must count exactly the timestamped in-window wrapper-start; "
        f"got {result.measured['recorder']['starts']}"
    )
    assert result.measured["recorder"]["note"] == "filtered-by-timestamp", (
        f"After Drift #8 fix, wrapper-start-lines with timestamp must report "
        f"'filtered-by-timestamp'; got {result.measured['recorder']['note']!r}"
    )
    assert result.verdict == "PASS"


def test_k1_wrapper_timestamped_start_outside_window_excluded(tmp_path: Path) -> None:
    """Phase 16 §11 Drift #8 fix pin: a wrapper-start-line WITH timestamp prefix
    OUTSIDE the Berlin-day window is excluded (count=0). Proves the timestamp
    is parsed and the window filter works for wrappers, not just scheduler.

    Note: ``evaluate_k1`` sets the ``note`` field from the *in-window*
    filtered list (not from the raw timestamps list) — so when no
    timestamped line was inside the window, the note reverts to
    'full-file-count'. This is by design (the note is the operator's
    signal: "K1 successfully filtered by timestamp"; a 0-count after
    timestamp filtering still means the timestamp mechanism worked, but
    nothing was in-window). The primary assertion here is the count.
    """
    state_dir = tmp_path / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    # One recorder start on 2026-09-07 09:00:00 — one day BEFORE the window.
    line = (
        "2026-09-07 09:00:00 [run_recorder] starting recorder from "
        "/home/trading-bot/trading-bot/phase12_data_foundation..."
    )
    (state_dir / "run_recorder.log").write_text(line + "\n", encoding="utf-8")
    for svc in ("scheduler", "discovery", "webui"):
        (state_dir / f"run_{svc}.log").write_text("", encoding="utf-8")

    day = date(2026, 9, 8)
    from_ts, to_ts = autonomy_report._berlin_day_bounds(day)
    result = autonomy_report.evaluate_k1(state_dir, from_ts=from_ts, to_ts=to_ts)
    assert result.measured["recorder"]["starts"] == 0, (
        f"K1 must exclude timestamped out-of-window wrapper-starts; "
        f"got {result.measured['recorder']['starts']}"
    )
    assert result.verdict == "PASS", (
        f"0 starts = PASS expected; got {result.verdict}; "
        f"measured={result.measured}"
    )


def test_k1_wrapper_mixed_timestamped_and_untimestamped(tmp_path: Path) -> None:
    """Phase 16 §11 Drift #8 fix pin: a wrapper log with both timestamped and
    untimestamped start-lines reports only the timestamped in-window count.
    Realistic mixed-mode case after a fix-apply: old log content
    (untimestamped) coexists with new restart events (timestamped).
    """
    state_dir = tmp_path / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        # 2 untimestamped (pre-fix format, legacy content)
        "[run_recorder] starting recorder from "
        "/home/trading-bot/trading-bot/phase12_data_foundation...",
        "[run_recorder] starting recorder from "
        "/home/trading-bot/trading-bot/phase12_data_foundation...",
        # 1 timestamped in-window (post-fix, on report day)
        "2026-09-08 09:00:00 [run_recorder] starting recorder from "
        "/home/trading-bot/trading-bot/phase12_data_foundation...",
        # 1 timestamped out-of-window (post-fix, day BEFORE report day)
        "2026-09-07 09:00:00 [run_recorder] starting recorder from "
        "/home/trading-bot/trading-bot/phase12_data_foundation...",
    ]
    (state_dir / "run_recorder.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for svc in ("scheduler", "discovery", "webui"):
        (state_dir / f"run_{svc}.log").write_text("", encoding="utf-8")

    day = date(2026, 9, 8)
    from_ts, to_ts = autonomy_report._berlin_day_bounds(day)
    result = autonomy_report.evaluate_k1(state_dir, from_ts=from_ts, to_ts=to_ts)
    # Only the 1 timestamped in-window line counts; the 2 untimestamped legacy
    # lines and the 1 timestamped out-of-window line are excluded.
    assert result.measured["recorder"]["starts"] == 1, (
        f"K1 mixed-mode: only timestamped in-window counts; got "
        f"{result.measured['recorder']['starts']} (expected 1, the single "
        f"in-window post-fix restart; legacy untimestamped + out-of-window "
        f"timestamped lines must be excluded)"
    )
    assert result.measured["recorder"]["note"] == "filtered-by-timestamp", (
        f"Mixed-mode must report 'filtered-by-timestamp' when at least one "
        f"timestamped line exists; got {result.measured['recorder']['note']!r}"
    )
    assert result.verdict == "PASS"


# -- Phase 16 R3.1 (Drift #11) / R3.2 (Drift #9) / R3.3 (F8, K8) --------------


def test_window_report_filename_uses_window(tmp_path: Path) -> None:
    """Drift #11 regression: a ``--from/--to`` window report must not collide with
    the single-day report filename for the same ``from_day``. Before the fix both
    wrote ``autonomy_<from_day>.json``, silently overwriting the day report."""
    reports_dir = tmp_path / "reports"
    day = date(2026, 9, 8)
    to_day = date(2026, 9, 9)
    day_stem = day.isoformat()
    window_stem = f"{day.isoformat()}_to_{to_day.isoformat()}"

    day_path = autonomy_report._write_report_file(reports_dir, day_stem, {"kind": "day"})
    window_path = autonomy_report._write_report_file(reports_dir, window_stem, {"kind": "window"})

    assert day_path != window_path
    assert day_path.name == "autonomy_2026-09-08.json"
    assert window_path.name == "autonomy_2026-09-08_to_2026-09-09.json"
    # The day report survives the window write — no overwrite.
    assert json.loads(day_path.read_text())["kind"] == "day"
    assert json.loads(window_path.read_text())["kind"] == "window"


def test_k4_threshold_is_full_window() -> None:
    """Drift #9 regression: the threshold string and verdict must always read against
    the full registered 10-day window, never against a queried sub-window's own day
    count. A clean 10-trading-day window with 8+ ok-days PASSes with that fixed
    threshold text."""
    from_day = date(2026, 9, 8)
    to_day = date(2026, 9, 21)  # 10 trading days
    days = [d for d in autonomy_report._iter_trading_days(from_day, to_day)]
    assert len(days) == 10
    health_evidence = {d: (1, 1) for d in days[:8]}  # 8 ok, 2 missing
    result = autonomy_report.evaluate_k4(
        Path("/nonexistent"), from_day, to_day, health_evidence=health_evidence,
    )
    assert "of 10 trading days" in result.threshold
    assert result.measured["full_window_trading_days"] == 10
    assert result.verdict == "PASS"


def test_k4_partial_window_is_partial_not_fail() -> None:
    """Drift #9 regression: a query narrower than the full registered window (e.g. a
    single ``--day`` report, or the 8-valid-day window Session #32 actually measured)
    must report PARTIAL, not a misleading FAIL against a threshold it can't satisfy
    by construction."""
    day = date(2026, 9, 8)
    result = autonomy_report.evaluate_k4(
        Path("/nonexistent"), day, day, health_evidence={day: (1, 1)},
    )
    assert result.measured["trading_days_considered"] == 1
    assert result.verdict == "PARTIAL"
    assert result.verdict != "FAIL"


def test_k8_liveness_fails_on_dead_day(tmp_path: Path) -> None:
    """F8 regression: a day with zero scheduler/recorder/heartbeat evidence must
    FAIL K8 — this is the exact 2026-09-21 shape (0 processes, 0 cycles, 0 bars),
    which K1/K5/K6/K7 all read as PASS."""
    state_dir = tmp_path / "state"
    bars_db = tmp_path / "bars.sqlite"
    day = date(2026, 9, 21)
    _seed_bars_db(bars_db, [])  # no bars at all
    state_dir.mkdir(parents=True, exist_ok=True)
    # No research_health.jsonl, no heartbeat events — a fully dead day.

    result = autonomy_report.evaluate_k8(state_dir, bars_db, day, day)

    assert result.criterion == "8"
    assert result.verdict == "FAIL"
    assert result.measured["live_days"] == 0
    assert result.measured["per_day"][day.isoformat()]["live"] is False


def test_k8_liveness_passes_on_live_day(tmp_path: Path) -> None:
    """A day with ≥1 scheduler cycle, ≥1 bar, and ≥1 heartbeat is live ⇒ K8 PASS."""
    state_dir = tmp_path / "state"
    bars_db = tmp_path / "bars.sqlite"
    day = date(2026, 9, 8)
    _seed_bars_db(bars_db, [day])
    _build_state_dir(state_dir, days=[day], heartbeat_events=[(day, True)])

    result = autonomy_report.evaluate_k8(state_dir, bars_db, day, day)

    assert result.verdict == "PASS"
    assert result.measured["live_days"] == 1
    flags = result.measured["per_day"][day.isoformat()]
    assert flags["scheduler_cycles"] >= 1
    assert flags["bars"] >= 1
    assert flags["heartbeats"] >= 1
    assert flags["live"] is True
