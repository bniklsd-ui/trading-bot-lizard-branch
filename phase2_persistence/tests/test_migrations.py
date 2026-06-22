"""Tests for the SQL-file migration runner."""

from __future__ import annotations

import sqlite3

from persistence import migrations
from persistence.db import Database
from persistence.schema import MIGRATIONS_DIR

_EXPECTED_TABLES = {
    "trade_outcomes",
    "reward_pts",
    "trade_lessons",
    "ig_config_state",
    "market_regime_snapshots",
    "decision_context",
}


def _tables(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return {r[0] for r in rows}


def test_get_version_zero_on_empty_db(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "x.sqlite"))
    conn.row_factory = sqlite3.Row
    assert migrations._get_schema_version(conn) == 0


def test_fresh_db_reaches_version_2(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "x.sqlite"))
    conn.row_factory = sqlite3.Row
    version = migrations.run_migrations(conn, MIGRATIONS_DIR)
    assert version == 2  # 001_initial + 002_phase7_reward
    assert migrations._get_schema_version(conn) == 2


def test_all_tables_created(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "x.sqlite"))
    conn.row_factory = sqlite3.Row
    migrations.run_migrations(conn, MIGRATIONS_DIR)
    assert _EXPECTED_TABLES.issubset(_tables(conn))


def test_schema_version_table_created(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "x.sqlite"))
    conn.row_factory = sqlite3.Row
    migrations.run_migrations(conn, MIGRATIONS_DIR)
    assert "_schema_version" in _tables(conn)


def test_indexes_created(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "x.sqlite"))
    conn.row_factory = sqlite3.Row
    migrations.run_migrations(conn, MIGRATIONS_DIR)
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index'"
    ).fetchall()
    names = {r[0] for r in rows}
    assert "idx_trade_outcomes_deal_id" in names
    assert "idx_reward_pts_trade_id" in names


def test_rerun_is_noop(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "x.sqlite"))
    conn.row_factory = sqlite3.Row
    migrations.run_migrations(conn, MIGRATIONS_DIR)
    # Second run must not raise and must not advance the version.
    version = migrations.run_migrations(conn, MIGRATIONS_DIR)
    assert version == 2
    # One version row per applied migration (001 + 002), and no more on rerun.
    count = conn.execute("SELECT COUNT(*) FROM _schema_version").fetchone()[0]
    assert count == 2


def test_find_pending_respects_current(tmp_path):
    pending = migrations._find_pending(MIGRATIONS_DIR, current=0)
    assert [v for v, _ in pending] == [1, 2]
    assert [v for v, _ in migrations._find_pending(MIGRATIONS_DIR, current=1)] == [2]
    assert migrations._find_pending(MIGRATIONS_DIR, current=2) == []


def test_database_run_migrations_seeds_defaults(db):
    config = db.get_all_config()
    assert config["bot_score"] == 50.0
    assert config["risk_level"] == "KONSERVATIV"
    assert config["force_trigger_locked"] is False


def test_database_run_migrations_idempotent(tmp_path):
    path = str(tmp_path / "x.sqlite")
    d = Database(path)
    assert d.run_migrations() == 2
    assert d.run_migrations() == 2  # no error, no change
    d.close()


def test_phase7_columns_present(tmp_path):
    """Migration 002 adds the Phase-7 reward columns to the schema."""
    conn = sqlite3.connect(str(tmp_path / "x.sqlite"))
    conn.row_factory = sqlite3.Row
    migrations.run_migrations(conn, MIGRATIONS_DIR)

    def _columns(table: str) -> set[str]:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return {r["name"] for r in rows}

    assert {"initial_risk", "account"}.issubset(_columns("trade_outcomes"))
    assert "r_multiple" in _columns("reward_pts")
