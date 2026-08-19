"""Phase 13 §6 C3 — tests for ``scripts.source_delta``.

All read-only against a tmp_path SQLite pair (paper_trades + bars).
No network, no LLM, no Phase-3 fetcher.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timezone

import pytest

# Add the scripts/ dir to sys.path so we can import the module by name.
_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_SCRIPTS))

import source_delta as sd  # noqa: E402

# Migration paths: the test sets up paper_trades + instrument_universe
# the same way Phase 10's tests do (Migrations 004/005/006).
_P2_MIGRATIONS = Path(__file__).resolve().parents[2] / "phase2_persistence" / "migrations"
_MIG_004 = _P2_MIGRATIONS / "004_phase9_instrument_universe.sql"
_MIG_005 = _P2_MIGRATIONS / "005_v3_learning.sql"
_MIG_006 = _P2_MIGRATIONS / "006_phase12_data_foundation.sql"


# ---------- helpers ----------------------------------------------------------


def _bootstrap_db(db_path: Path) -> None:
    conn = sqlite3.connect(str(db_path))
    try:
        for mig in (_MIG_004, _MIG_005, _MIG_006):
            conn.executescript(mig.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()


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
    # Bootstrap the bars archive (its own DDL is in BarArchive.ensure_schema)
    from data_foundation.archive import BarArchive
    BarArchive(bars_path).ensure_schema()
    return db_path, bars_path


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
    assert row["kind"] == "agree"
    assert row["yf"]["exit_reason"] == "SL"
    assert row["ls"]["exit_reason"] == "SL"


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
    assert row["kind"] == "diverge"
    assert row["yf"]["exit_reason"] == "SL"
    assert row["ls"]["exit_reason"] == "TP"


def test_missing_source_counted_as_incomparable(dbs):
    """A trade with yF bars but NO ls bars (or vice versa) is reported
    as ``trades_incomparable`` — not as agreement. The signal must
    not be misread."""
    db_path, bars_path = dbs
    _insert_paper_trade(db_path, paper_id="p-incomp")
    for m in range(10):
        _insert_yf_bar(bars_path, epic="IX.D.DAX.IFMM.IP",
                       ts=f"2026-08-19T09:{m:02d}:00.000Z", close=100.0)
    # No LS bars at all.
    rc, payload = _run(["--day", "2026-08-19"], db_path, bars_path)
    assert rc == 0
    assert payload["trades_total"] == 1
    assert payload["trades_incomparable"] == 1
    assert payload["trades_agree"] == 0
    assert payload["trades_diverge"] == 0
    assert payload["divergence_rate"] is None  # division by zero → None


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
    # Trade on 2026-08-18
    _insert_paper_trade(db_path, paper_id="p-d1",
                        created_utc="2026-08-18T09:00:00.000Z",
                        time_stop_utc="2026-08-18T13:00:00.000Z",
                        resolved_utc="2026-08-18T09:10:00.000Z")
    # Trade on 2026-08-19
    _insert_paper_trade(db_path, paper_id="p-d2",
                        created_utc="2026-08-19T09:00:00.000Z",
                        time_stop_utc="2026-08-19T13:00:00.000Z",
                        resolved_utc="2026-08-19T09:10:00.000Z")
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
