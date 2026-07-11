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
    "instrument_universe",
    "abstain_records",
    "paper_trades",
}


def _tables(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return {r[0] for r in rows}


def test_get_version_zero_on_empty_db(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "x.sqlite"))
    conn.row_factory = sqlite3.Row
    assert migrations._get_schema_version(conn) == 0


def test_fresh_db_reaches_version_5(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "x.sqlite"))
    conn.row_factory = sqlite3.Row
    version = migrations.run_migrations(conn, MIGRATIONS_DIR)
    # 001_initial + 002_phase7_reward + 003_phase8_trade_provenance +
    # 004_phase9_instrument_universe + 005_v3_learning
    assert version == 5
    assert migrations._get_schema_version(conn) == 5


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
    assert version == 5
    # One version row per applied migration (001 + 002 + 003 + 004 + 005), and no more on rerun.
    count = conn.execute("SELECT COUNT(*) FROM _schema_version").fetchone()[0]
    assert count == 5


def test_find_pending_respects_current(tmp_path):
    pending = migrations._find_pending(MIGRATIONS_DIR, current=0)
    assert [v for v, _ in pending] == [1, 2, 3, 4, 5]
    assert [v for v, _ in migrations._find_pending(MIGRATIONS_DIR, current=1)] == [2, 3, 4, 5]
    assert [v for v, _ in migrations._find_pending(MIGRATIONS_DIR, current=2)] == [3, 4, 5]
    assert [v for v, _ in migrations._find_pending(MIGRATIONS_DIR, current=3)] == [4, 5]
    assert [v for v, _ in migrations._find_pending(MIGRATIONS_DIR, current=4)] == [5]
    assert migrations._find_pending(MIGRATIONS_DIR, current=5) == []


def test_database_run_migrations_seeds_defaults(db):
    config = db.get_all_config()
    assert config["bot_score"] == 50.0
    assert config["risk_level"] == "KONSERVATIV"
    assert config["force_trigger_locked"] is False


def test_database_run_migrations_idempotent(tmp_path):
    path = str(tmp_path / "x.sqlite")
    d = Database(path)
    assert d.run_migrations() == 5
    assert d.run_migrations() == 5  # no error, no change
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


def test_phase8_provenance_column_present(tmp_path):
    """Migration 003 (Phase 8 v1.6, Cause A part 2) adds trade_outcomes.provenance."""
    conn = sqlite3.connect(str(tmp_path / "x.sqlite"))
    conn.row_factory = sqlite3.Row
    migrations.run_migrations(conn, MIGRATIONS_DIR)

    def _columns(table: str) -> set[str]:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return {r["name"] for r in rows}

    assert "provenance" in _columns("trade_outcomes")


def test_phase9_instrument_universe_table_present(tmp_path):
    """Migration 004 (Phase 9 V2 foundation) adds the instrument_universe table."""
    conn = sqlite3.connect(str(tmp_path / "x.sqlite"))
    conn.row_factory = sqlite3.Row
    migrations.run_migrations(conn, MIGRATIONS_DIR)

    def _columns(table: str) -> set[str]:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return {r["name"] for r in rows}

    assert "instrument_universe" in _tables(conn)
    assert _columns("instrument_universe") == {
        "epic",
        "name",
        "yf_ticker",
        "volume_proxy",
        "point_value",
        "point_value_source",
        "min_deal_size",
        "currency",
        "status",
        "source",
        "checks_json",
        "fail_count",
        "data_degraded",
        "last_verified_at",
        "created_at",
        "updated_at",
    }
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
    assert "idx_instrument_universe_status" in {r["name"] for r in rows}


def test_v3_learning_tables_present(tmp_path):
    """Migration 005 (Phase 10 V3) adds abstain_records/paper_trades and DROP+CREATEs
    market_regime_snapshots/decision_context to the new epic-scoped (no trade_id) schema."""
    conn = sqlite3.connect(str(tmp_path / "x.sqlite"))
    conn.row_factory = sqlite3.Row
    migrations.run_migrations(conn, MIGRATIONS_DIR)

    def _columns(table: str) -> set[str]:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return {r["name"] for r in rows}

    assert _columns("abstain_records") == {
        "record_id", "created_utc", "epic", "stage", "reason", "detail",
        "context_json", "lesson", "lesson_extracted",
    }
    assert _columns("paper_trades") == {
        "paper_id", "abstain_record_id", "variant", "epic", "direction",
        "created_utc", "entry_level", "stop_distance", "limit_distance",
        "time_stop_utc", "status", "resolved_utc", "exit_reason", "exit_level",
        "pnl_points", "r_multiple", "council_confidence", "lesson",
        "lesson_extracted", "context_json",
    }
    # Epic-scoped V3 schema — no trade_id, the old FK-scoped V2 placeholder is gone.
    assert "trade_id" not in _columns("market_regime_snapshots")
    assert _columns("market_regime_snapshots") == {
        "snapshot_id", "created_utc", "epic", "spread_pct", "atr_points",
        "range_pct", "time_bucket", "regime_tag", "data_source", "degraded",
        "decision_context_id",
    }
    assert "trade_id" not in _columns("decision_context")
    assert _columns("decision_context") == {
        "context_id", "created_utc", "epic", "candidate_json", "bull_summary",
        "bear_summary", "judge_decision", "judge_confidence", "rounds_used",
        "veto_results_json", "gate_results_json", "outcome", "deal_id",
        "abstain_record_id",
    }
    names = {r["name"] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index'"
    ).fetchall()}
    assert {
        "idx_abstain_records_created_utc", "idx_abstain_records_reason",
        "idx_paper_trades_status", "idx_paper_trades_created_utc",
        "idx_decision_context_created_utc", "idx_market_regime_snapshots_created_utc",
    }.issubset(names)
