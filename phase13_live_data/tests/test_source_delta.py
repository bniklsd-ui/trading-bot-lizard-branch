"""Phase 13 §6 C3 — tests for ``scripts.source_delta``.

All read-only against a tmp_path SQLite pair (paper_trades + bars).
No network, no LLM, no Phase-3 fetcher.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

import pytest

# Add the scripts/ dir to sys.path so we can import the module by name.
_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_SCRIPTS))

import source_delta as sd  # noqa: E402

# Migration paths: the test sets up paper_trades + instrument_universe
# the same way Phase 10's tests do (Migrations 004/005/006). Phase-14
# B3 adds migration 007 so the script's per-epic availability query
# has a real table to read from.
_P2_MIGRATIONS = Path(__file__).resolve().parents[2] / "phase2_persistence" / "migrations"
_MIG_004 = _P2_MIGRATIONS / "004_phase9_instrument_universe.sql"
_MIG_005 = _P2_MIGRATIONS / "005_v3_learning.sql"
_MIG_006 = _P2_MIGRATIONS / "006_phase12_data_foundation.sql"
_MIG_007 = _P2_MIGRATIONS / "007_phase14_source_availability.sql"


def _bootstrap_db(db_path: Path) -> None:
    """Bootstraps all migrations 004–007. Phase-14 B3 needs 007 for
    ``instrument_source_availability`` to exist in the fixture DB."""
    conn = sqlite3.connect(str(db_path))
    try:
        for mig in (_MIG_004, _MIG_005, _MIG_006, _MIG_007):
            conn.executescript(mig.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()


# ---------- helpers ----------------------------------------------------------


def _insert_paper_trade(
    db_path: Path, *, paper_id: str, epic: str = "IX.D.DAX.IFMM.IP",
    direction: str = "BUY", entry_level: float = 18000.0,
    stop_distance: float = 30.0, limit_distance: float = 45.0,
    created_utc: str = "2026-08-19T09:00:00.000Z",
    time_stop_utc: str = "2026-08-19T13:00:00.000Z",
    exit_reason: str = "SL", exit_level: float = 17970.0,
    pnl_points: float = -30.0, resolved_utc: str = "2026-08-19T09:10:00.000Z",
) -> None:
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "INSERT INTO paper_trades (paper_id, abstain_record_id, variant, epic, direction, "
            "created_utc, entry_level, stop_distance, limit_distance, time_stop_utc, status, "
            "resolved_utc, exit_reason, exit_level, pnl_points) "
            "VALUES (?, 'ar1', 'shadow_up', ?, ?, ?, ?, ?, ?, ?, 'RESOLVED', ?, ?, ?, ?)",
            (paper_id, epic, direction, created_utc, entry_level, stop_distance,
             limit_distance, time_stop_utc, resolved_utc, exit_reason, exit_level, pnl_points),
        )
        conn.commit()
    finally:
        conn.close()


def _insert_yf_bar(bars_path: Path, *, epic: str, ts: str, close: float = 100.0,
                  open_: float = 100.0, high: float = 100.0, low: float = 100.0,
                  volume: float = 1.0) -> None:
    conn = sqlite3.connect(str(bars_path))
    try:
        conn.execute(
            "INSERT INTO bars (epic, resolution, ts_utc, open, high, low, close, volume, "
            "source, fetched_at) "
            "VALUES (?, '1m', ?, ?, ?, ?, ?, ?, 'yf', ?)",
            (epic, ts, open_, high, low, close, volume, ts),
        )
        conn.commit()
    finally:
        conn.close()


def _insert_ls_bar(bars_path: Path, *, epic: str, ts: str, close: float = 100.0,
                   tick_count: int | None = 5) -> None:
    conn = sqlite3.connect(str(bars_path))
    try:
        conn.execute(
            "INSERT INTO bars (epic, resolution, ts_utc, open, high, low, close, volume, "
            "source, fetched_at, tick_count) "
            "VALUES (?, '1m', ?, ?, ?, ?, ?, NULL, 'ls', ?, ?)",
            (epic, ts, close, close, close, close, ts, tick_count),
        )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def dbs(tmp_path: Path):
    db_path = tmp_path / "trading_bot.sqlite"
    bars_path = tmp_path / "bars.sqlite"
    _bootstrap_db(db_path)
    # Phase 14 B3: bootstrap migration 007 too so availability rows are
    # writable (the default test setup registers yf+ls as ``ok`` for
    # IX.D.DAX.IFMM.IP — the historical hardcoded-source pair). Tests
    # that need different availability override via the helpers below.
    _P2_MIG_007 = _P2_MIGRATIONS / "007_phase14_source_availability.sql"
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(_P2_MIG_007.read_text(encoding="utf-8"))
        # Seed the historical hardcoded pair (yf, ls) as ``ok``.
        conn.execute(
            "INSERT INTO instrument_source_availability "
            "(epic, source, resolution, source_symbol, status, origin, "
            " history_min_days, latency_min, last_verified_utc, notes) "
            "VALUES (?, 'yf', '1m', '^GDAXI', 'ok', 'registry', 30, 15, "
            "        '2026-08-19T08:00:00.000Z', 'fixture')",
            ("IX.D.DAX.IFMM.IP",),
        )
        conn.execute(
            "INSERT INTO instrument_source_availability "
            "(epic, source, resolution, source_symbol, status, origin, "
            " history_min_days, latency_min, last_verified_utc, notes) "
            "VALUES (?, 'ls', '1m', NULL, 'ok', 'derived', 1, 0, "
            "        '2026-08-19T08:00:00.000Z', 'fixture')",
            ("IX.D.DAX.IFMM.IP",),
        )
        conn.commit()
    finally:
        conn.close()
    # Bootstrap the bars archive (its own DDL is in BarArchive.ensure_schema)
    from data_foundation.archive import BarArchive
    BarArchive(bars_path).ensure_schema()
    return db_path, bars_path


def _set_availability(db_path: Path, *, epic: str, sources: list[str]) -> None:
    """Replace the availability rows for one epic with the given
    ``sources`` list (status='ok', resolution='1m'). Used by Phase-14
    B3 tests to drive the three-case rule deterministically."""
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "DELETE FROM instrument_source_availability WHERE epic = ?",
            (epic,),
        )
        for src in sources:
            conn.execute(
                "INSERT INTO instrument_source_availability "
                "(epic, source, resolution, source_symbol, status, origin, "
                " history_min_days, latency_min, last_verified_utc, notes) "
                "VALUES (?, ?, '1m', NULL, 'ok', 'registry', 30, 0, "
                "        '2026-08-19T08:00:00.000Z', 'fixture')",
                (epic, src),
            )
        conn.commit()
    finally:
        conn.close()


def _run(args: list[str], db_path: Path, bars_path: Path) -> tuple[int, dict]:
    """Invoke ``source_delta.main`` with the given args. Returns (exit, payload)."""
    full_args = [
        "--db", str(db_path),
        "--bars-db", str(bars_path),
        "--quiet",
    ] + args
    # Capture stdout (the script prints JSON to stdout, narrative to stderr).
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = sd.main(full_args)
    payload = json.loads(buf.getvalue() or "{}")
    return rc, payload


# ---------- tests ----------------------------------------------------------


def test_agreement_yf_and_ls_resolve_to_same_outcome(dbs):
    db_path, bars_path = dbs
    # Trade at entry=100, SL=95, TP=110 — yF and LS both fire SL at 09:10.
    _insert_paper_trade(db_path, paper_id="p-agree", entry_level=100.0,
                        stop_distance=5.0, limit_distance=10.0,
                        exit_reason="SL", exit_level=95.0, pnl_points=-5.0)
    for m in range(10):
        _insert_yf_bar(bars_path, epic="IX.D.DAX.IFMM.IP",
                       ts=f"2026-08-19T09:{m:02d}:00.000Z",
                       close=100.0, open_=100.0, high=100.0, low=100.0)
    # 09:10: low=94 → SL fires.
    _insert_yf_bar(bars_path, epic="IX.D.DAX.IFMM.IP",
                   ts="2026-08-19T09:10:00.000Z",
                   close=96.0, open_=100.0, high=100.0, low=94.0)
    # LS: same shape, same SL.
    for m in range(10):
        _insert_ls_bar(bars_path, epic="IX.D.DAX.IFMM.IP",
                       ts=f"2026-08-19T09:{m:02d}:00.000Z", close=100.0)
    _insert_ls_bar(bars_path, epic="IX.D.DAX.IFMM.IP",
                   ts="2026-08-19T09:10:00.000Z", close=96.0)
    # The default _insert_ls_bar helper sets high=close=96 and low=96;
    # for the LS-SL to actually fire we need low=94 too. The cleanest
    # way is an UPDATE post-insert.
    conn = sqlite3.connect(str(bars_path))
    try:
        conn.execute(
            "UPDATE bars SET low=94.0 WHERE epic=? AND ts_utc=? AND source='ls'",
            ("IX.D.DAX.IFMM.IP", "2026-08-19T09:10:00.000Z"),
        )
        conn.commit()
    finally:
        conn.close()
    rc, payload = _run(["--day", "2026-08-19"], db_path, bars_path)
    assert rc == 0
    assert payload["trades_total"] == 1
    assert payload["trades_agree"] == 1
    assert payload["trades_diverge"] == 0
    assert payload["divergence_rate"] == 0.0
    row = payload["rows"][0]
    # Phase-14 B3: kind='compared' + comparison='agree' (the
    # three-case rule puts this in the "compared" bucket with an
    # agree/diverge sub-state — see source_delta._resolve_one_trade).
    assert row["kind"] == "compared"
    assert row["comparison"] == "agree"
    assert row["sources"]["yf"]["exit_reason"] == "SL"
    assert row["sources"]["ls"]["exit_reason"] == "SL"


def test_divergence_yf_sl_ls_tp(dbs):
    """The two sources see different SL/TP outcomes for the same trade.
    yF: 09:10 low=94 → SL (BUY at 100, SL=95). LS: 09:10 high=111 → TP (TP=110)."""
    db_path, bars_path = dbs
    _insert_paper_trade(db_path, paper_id="p-diverge", entry_level=100.0,
                        stop_distance=5.0, limit_distance=10.0,
                        exit_reason="SL", exit_level=95.0, pnl_points=-5.0)
    # yF bars: stable until 09:10, low=94 (SL).
    for m in range(10):
        _insert_yf_bar(bars_path, epic="IX.D.DAX.IFMM.IP",
                       ts=f"2026-08-19T09:{m:02d}:00.000Z", close=100.0)
    _insert_yf_bar(bars_path, epic="IX.D.DAX.IFMM.IP",
                   ts="2026-08-19T09:10:00.000Z",
                   close=100.0, open_=100.0, high=100.0, low=94.0)
    # LS bars: stable until 09:10, high=111 (TP).
    for m in range(10):
        _insert_ls_bar(bars_path, epic="IX.D.DAX.IFMM.IP",
                       ts=f"2026-08-19T09:{m:02d}:00.000Z", close=100.0)
    _insert_ls_bar(bars_path, epic="IX.D.DAX.IFMM.IP",
                   ts="2026-08-19T09:10:00.000Z", close=100.0)
    # Update the LS bar to have high=111 — but our insert_ls_bar helper
    # sets high=close. We insert with close=100 then update below.
    conn = sqlite3.connect(str(bars_path))
    try:
        conn.execute(
            "UPDATE bars SET high=111.0, low=100.0 WHERE epic=? AND ts_utc=? AND source='ls'",
            ("IX.D.DAX.IFMM.IP", "2026-08-19T09:10:00.000Z"),
        )
        conn.commit()
    finally:
        conn.close()
    rc, payload = _run(["--day", "2026-08-19"], db_path, bars_path)
    assert rc == 0
    assert payload["trades_diverge"] == 1
    assert payload["divergence_rate"] == 1.0
    row = payload["rows"][0]
    assert row["kind"] == "compared"
    assert row["comparison"] == "diverge"
    assert row["sources"]["yf"]["exit_reason"] == "SL"
    assert row["sources"]["ls"]["exit_reason"] == "TP"


def test_available_but_empty_when_one_source_has_no_bars(dbs):
    """Phase-14 B3: a trade where one registered source has bars and
    the other doesn't is reported as ``kind='available_but_empty'``
    (Beschaffungslücke on at least one registered source). This is
    NOT the old ``incomparable`` bucket — the new three-case rule
    splits "registered but no bars" from "not registered at all".
    """
    db_path, bars_path = dbs
    # entry=100 with stop=95 / tp=110; flat bars at 100 → no exit fires,
    # exit_reason stays None on yF (the only source with bars).
    _insert_paper_trade(db_path, paper_id="p-incomp", entry_level=100.0,
                        stop_distance=5.0, limit_distance=10.0,
                        exit_reason="SL", exit_level=95.0, pnl_points=-5.0)
    for m in range(10):
        _insert_yf_bar(bars_path, epic="IX.D.DAX.IFMM.IP",
                       ts=f"2026-08-19T09:{m:02d}:00.000Z",
                       close=100.0, open_=100.0, high=100.0, low=100.0)
    # No LS bars at all — LS is registered (fixture) but delivered nothing.
    rc, payload = _run(["--day", "2026-08-19"], db_path, bars_path)
    assert rc == 0
    assert payload["trades_total"] == 1
    assert payload["trades_available_but_empty"] == 1
    assert payload["trades_agree"] == 0
    assert payload["trades_diverge"] == 0
    assert payload["divergence_rate"] is None  # no comparison happened
    row = payload["rows"][0]
    assert row["kind"] == "available_but_empty"
    assert row["comparison"] is None
    # yF: bars present, but no SL/TP hit at entry=100 with the flat bars.
    assert row["sources"]["yf"]["n_bars"] == 10
    assert row["sources"]["yf"]["exit_reason"] is None
    # LS: zero bars.
    assert row["sources"]["ls"]["n_bars"] == 0
    assert row["sources"]["ls"]["exit_reason"] is None


# ---------- Phase-14 B3: three-case rule (new tests) -----------------------


def test_not_available_when_no_sources_registered_for_epic(dbs):
    """An epic with **no** ``status='ok'`` rows in
    ``instrument_source_availability`` reports the trade as
    ``not_available``. This is the "war prinzipiell nicht abrufbar"
    case — distinct from "registered but no bars" (which would be
    ``available_but_empty``)."""
    db_path, bars_path = dbs
    # Strip the fixture-seeded availability rows for DAX so it has no
    # registered source at all. Bars still exist (legacy Phase-13
    # behaviour) but they don't count without a registered source.
    _set_availability(db_path, epic="IX.D.DAX.IFMM.IP", sources=[])
    _insert_paper_trade(db_path, paper_id="p-noavail", entry_level=100.0,
                        stop_distance=5.0, limit_distance=10.0,
                        exit_reason="SL", exit_level=95.0, pnl_points=-5.0)
    for m in range(10):
        _insert_yf_bar(bars_path, epic="IX.D.DAX.IFMM.IP",
                       ts=f"2026-08-19T09:{m:02d}:00.000Z", close=100.0)
    rc, payload = _run(["--day", "2026-08-19"], db_path, bars_path)
    assert rc == 0
    assert payload["trades_total"] == 1
    assert payload["trades_not_available"] == 1
    assert payload["trades_agree"] == 0
    assert payload["trades_diverge"] == 0
    assert payload["trades_available_but_empty"] == 0
    assert payload["divergence_rate"] is None
    row = payload["rows"][0]
    assert row["kind"] == "not_available"
    assert row["comparison"] is None
    # The per-source dict is empty — no source was registered.
    assert row["sources"] == {}


def test_available_but_empty_when_all_registered_sources_have_no_bars(dbs):
    """Both yF and LS are registered (``status='ok'``) for the epic,
    but no bars landed for either source inside the trade window.
    Result: ``kind='available_but_empty'`` (Beschaffungslücke on
    both registered sources) — still distinct from ``not_available``."""
    db_path, bars_path = dbs
    # Fixture already seeds yf+ls as ok for DAX — keep that.
    _insert_paper_trade(db_path, paper_id="p-empty", entry_level=100.0,
                        stop_distance=5.0, limit_distance=10.0,
                        exit_reason="SL", exit_level=95.0, pnl_points=-5.0)
    # No bars at all (neither yF nor LS).
    rc, payload = _run(["--day", "2026-08-19"], db_path, bars_path)
    assert rc == 0
    assert payload["trades_total"] == 1
    assert payload["trades_available_but_empty"] == 1
    assert payload["trades_not_available"] == 0
    assert payload["trades_agree"] == 0
    assert payload["trades_diverge"] == 0
    row = payload["rows"][0]
    assert row["kind"] == "available_but_empty"
    assert row["comparison"] is None
    assert row["sources"]["yf"]["n_bars"] == 0
    assert row["sources"]["yf"]["exit_reason"] is None
    assert row["sources"]["ls"]["n_bars"] == 0


def test_fail_soft_when_availability_table_missing(dbs, tmp_path):
    """An older ``trading_bot.sqlite`` without Migration 007 must
    NOT crash the report. Every trade is reported as
    ``not_available`` (no source is registered), ``divergence_rate=None``,
    exit 0. The script is read-only and silent-failure-by-default."""
    db_path, bars_path = dbs
    # Boot a SECOND trading_bot.sqlite WITHOUT migration 007 (only 004–006).
    other_db = tmp_path / "trading_bot_no_007.sqlite"
    conn = sqlite3.connect(str(other_db))
    try:
        for mig in (_MIG_004, _MIG_005, _MIG_006):
            conn.executescript(mig.read_text(encoding="utf-8"))
        # Insert one paper trade (so the script has something to chew on).
        conn.execute(
            "INSERT INTO paper_trades (paper_id, abstain_record_id, variant, "
            " epic, direction, created_utc, entry_level, stop_distance, "
            " limit_distance, time_stop_utc, status, resolved_utc, "
            " exit_reason, exit_level, pnl_points) "
            "VALUES ('p-failsoft', 'ar1', 'shadow_up', 'IX.D.DAX.IFMM.IP', "
            "        'BUY', '2026-08-19T09:00:00.000Z', 100.0, 5.0, 10.0, "
            "        '2026-08-19T13:00:00.000Z', 'RESOLVED', "
            "        '2026-08-19T09:10:00.000Z', 'SL', 95.0, -5.0)",
        )
        conn.commit()
    finally:
        conn.close()

    rc, payload = _run(["--day", "2026-08-19"], other_db, bars_path)
    assert rc == 0, f"expected exit 0 (fail-soft); got {rc}"
    assert payload["trades_total"] == 1
    assert payload["trades_not_available"] == 1
    assert payload["trades_agree"] == 0
    assert payload["trades_diverge"] == 0
    assert payload["trades_available_but_empty"] == 0
    assert payload["divergence_rate"] is None
    row = payload["rows"][0]
    assert row["kind"] == "not_available"
    assert row["sources"] == {}


def test_db_read_error_returns_exit_1(dbs, tmp_path):
    """A missing DB → exit 1 (READ ERROR). The script must not silently
    emit a zero-row payload."""
    db_path, _ = dbs
    missing = tmp_path / "no_such.sqlite"
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = sd.main([
            "--db", str(missing),
            "--bars-db", str(missing),
            "--quiet", "--day", "2026-08-19",
        ])
    assert rc == 1


def test_no_trades_in_window_returns_zero_row_payload(dbs):
    """An empty window (no resolved trades) is **not** an error — the
    script writes a zero-row payload and exits 0. The operator
    reading the JSON sees ``trades_total: 0`` and knows the day was
    empty (or out of range)."""
    db_path, bars_path = dbs
    rc, payload = _run(["--day", "2026-08-19"], db_path, bars_path)
    assert rc == 0
    assert payload["trades_total"] == 0
    assert payload["rows"] == []
    assert payload["divergence_rate"] is None


def test_multiple_days_window(dbs):
    """``--days N`` covers the trailing N UTC days inclusive. Trades
    on different days count separately."""
    db_path, bars_path = dbs
    # Use today-relative dates so the test stays inside the
    # ``--days 2`` window (= [today-1, today]) regardless of when it's run.
    today = datetime.now(timezone.utc).date()
    d1 = (today - timedelta(days=1)).isoformat()  # yesterday
    d2 = today.isoformat()                       # today
    _insert_paper_trade(db_path, paper_id="p-d1",
                        created_utc=f"{d1}T09:00:00.000Z",
                        time_stop_utc=f"{d1}T13:00:00.000Z",
                        resolved_utc=f"{d1}T09:10:00.000Z")
    _insert_paper_trade(db_path, paper_id="p-d2",
                        created_utc=f"{d2}T09:00:00.000Z",
                        time_stop_utc=f"{d2}T13:00:00.000Z",
                        resolved_utc=f"{d2}T09:10:00.000Z")
    rc, payload = _run(["--days", "2"], db_path, bars_path)
    assert rc == 0
    assert payload["trades_total"] == 2


def test_day_and_days_are_mutually_exclusive(dbs):
    db_path, bars_path = dbs
    rc = sd.main([
        "--db", str(db_path), "--bars-db", str(bars_path),
        "--quiet", "--day", "2026-08-19", "--days", "2",
    ])
    assert rc == 1
