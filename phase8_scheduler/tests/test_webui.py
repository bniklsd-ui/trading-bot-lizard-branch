"""Module 12 (concept §12) — the read-mostly FastAPI dashboard backend.

No network, no broker, no LLM, no real daemon: a temp SQLite seeded with the columns the
endpoints read + a temp ``scheduler_state.json`` + temp KILL / command paths, driven through
FastAPI's ``TestClient``. The behaviours pinned: the ``/api/status`` shape + running-state
derivation (RUNNING/PAUSED/HALTED) from the kill + command files, the read endpoints returning
seeded rows, the file-only control endpoints (kill / clear / command), command validation, the
fail-soft missing-DB path, and — the isolation proof — that the DB connection is read-only (a
write raises ``OperationalError``).
"""

from __future__ import annotations

import dataclasses
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from scheduler import command, killswitch
from scheduler.clock import Phase
from scheduler.config import SchedulerConfig
from scheduler.state import SchedulerState, StateStore
from webui.api import create_app, ro_connect

_PHASES = {p.value for p in Phase}


# --- fixtures --------------------------------------------------------------


def _seed_db(db_path: str) -> None:
    """Create the (subset of the) Phase-2 tables the UI reads + a couple of rows."""
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE trade_outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, deal_id TEXT, epic TEXT, direction TEXT,
            size REAL, open_level REAL, close_level REAL, profit_loss REAL, status TEXT,
            account TEXT, open_ts TEXT, close_ts TEXT, session_date TEXT, research_confidence REAL
        );
        CREATE TABLE reward_pts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, trade_id INTEGER, outcome_score_delta REAL,
            process_score_delta REAL, score_after REAL, win_loss TEXT, pnl_raw REAL,
            r_multiple REAL, debate_confidence REAL, calculated_at TEXT
        );
        CREATE TABLE trade_lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT, trade_id INTEGER, lesson_text TEXT,
            used_in_research INTEGER, extracted_at TEXT, market_context_json TEXT
        );
        """
    )
    conn.execute(
        "INSERT INTO trade_outcomes (deal_id, epic, direction, size, open_level, close_level, "
        "profit_loss, status, account, open_ts, close_ts, session_date) VALUES "
        "('DEAL1','IX.D.DAX.IFMM.IP','SELL',19.6,24771.3,24772.4,-41.16,'CLOSED','demo',"
        "'2026-06-28T10:00:00Z','2026-06-28T10:05:00Z','2026-06-28')"
    )
    conn.execute(
        "INSERT INTO trade_outcomes (deal_id, epic, direction, size, open_level, status, "
        "account, open_ts, session_date) VALUES "
        "('DEAL2','IX.D.DAX.IFMM.IP','BUY',10.0,24800.0,'OPEN','demo','2026-06-28T11:00:00Z','2026-06-28')"
    )
    conn.execute(
        "INSERT INTO reward_pts (trade_id, outcome_score_delta, process_score_delta, score_after, "
        "win_loss, pnl_raw, r_multiple, calculated_at) VALUES "
        "(1,-2.0,-0.5,47.5,'LOSS',-41.16,-1.3,'2026-06-28T10:05:01Z')"
    )
    conn.execute(
        "INSERT INTO trade_lessons "
        "(trade_id, lesson_text, used_in_research, extracted_at, market_context_json) VALUES "
        "(1,'Avoid shorting into a relief rally.',0,'2026-06-28T10:05:02Z',"
        "'{\"provenance\": \"autonomous\"}')"
    )
    # v1.5 (Step 4 addendum): a pre-v1.5 lesson with no market_context_json at all — the
    # provenance column must degrade to NULL / "untagged" in the API/UI, not error.
    conn.execute(
        "INSERT INTO trade_lessons (trade_id, lesson_text, used_in_research, extracted_at) VALUES "
        "(1,'Old lesson written before the provenance tag existed.',0,'2026-05-01T09:00:00Z')"
    )
    conn.commit()
    conn.close()


@pytest.fixture()
def client(tmp_path):
    db_path = str(tmp_path / "trading_bot.sqlite")
    _seed_db(db_path)
    cfg = dataclasses.replace(
        SchedulerConfig(max_trades_per_day=5),
        live_db_path=db_path,
        state_path=str(tmp_path / "scheduler_state.json"),
        kill_path=str(tmp_path / "KILL"),
        command_path=str(tmp_path / "cmd.json"),
    )
    StateStore(cfg.state_path).save(
        SchedulerState(date="2026-06-28", trades_today=1, realized_pnl_today=-41.16)
    )
    return TestClient(create_app(cfg)), cfg


# --- status ----------------------------------------------------------------


def test_status_shape_and_running_state(client) -> None:
    c, _cfg = client
    body = c.get("/api/status").json()
    for key in (
        "phase", "running_state", "trades_today", "max_trades_per_day",
        "realized_pnl_today", "consecutive_failures", "session_date",
    ):
        assert key in body
    assert body["phase"] in _PHASES
    assert body["running_state"] == "RUNNING"     # no kill, no command file
    # v1.7: DB-fed, not the state snapshot — the seeded DB has 2 trade_outcomes rows for
    # 2026-06-28 (DEAL1 CLOSED -41.16, DEAL2 OPEN/NULL), while the snapshot itself says 1 /
    # -41.16 (see test_status_reads_db_not_stale_snapshot below for the divergence proof).
    assert body["trades_today"] == 2
    assert body["realized_pnl_today"] == -41.16   # SUM excludes DEAL2's NULL profit_loss
    assert body["max_trades_per_day"] == 5
    assert body["session_date"] == "2026-06-28"


def test_status_reads_db_not_stale_snapshot(client) -> None:
    """v1.7 regression guard: /api/status must ignore a wrong/stale state-file snapshot.

    Reproduces the 2026-07-02 bug shape — a scheduler_state.json whose counters lag the DB
    (as happens for a CLOSED_BY_BROKER trade before the reconcile pass resolves its P&L) —
    and asserts the endpoint reports the DB's truth, not the snapshot.
    """
    c, cfg = client
    StateStore(cfg.state_path).save(
        SchedulerState(date="2026-06-28", trades_today=99, realized_pnl_today=0.0)
    )
    body = c.get("/api/status").json()
    assert body["trades_today"] == 2          # DB truth, not the stale snapshot's 99
    assert body["realized_pnl_today"] == -41.16  # DB truth, not the stale snapshot's 0.0


def test_status_missing_db_falls_back_to_zero(tmp_path) -> None:
    """v1.7: no DB file yet -> DB-fed status/trades/pnl degrade to 0 / 0.0, never a 500."""
    cfg = dataclasses.replace(
        SchedulerConfig(max_trades_per_day=5),
        live_db_path=str(tmp_path / "nope.sqlite"),
        state_path=str(tmp_path / "scheduler_state.json"),
        kill_path=str(tmp_path / "KILL"),
        command_path=str(tmp_path / "cmd.json"),
    )
    StateStore(cfg.state_path).save(SchedulerState(date="2026-06-28"))
    c = TestClient(create_app(cfg))
    body = c.get("/api/status").json()
    assert body["trades_today"] == 0
    assert body["realized_pnl_today"] == 0.0


def test_kill_flips_status_to_halted(client) -> None:
    c, cfg = client
    r = c.post("/api/kill", json={"reason": "panic"})
    assert r.json()["ok"] is True
    assert killswitch.is_set(cfg.kill_path)             # file written
    body = c.get("/api/status").json()
    assert body["running_state"] == "HALTED"
    assert body["kill_reason"] == "manual:panic"


def test_clear_kill_returns_to_running(client) -> None:
    c, cfg = client
    c.post("/api/kill", json={})
    c.post("/api/clear_kill")
    assert not killswitch.is_set(cfg.kill_path)
    assert c.get("/api/status").json()["running_state"] == "RUNNING"


def test_command_stop_sets_paused(client) -> None:
    c, cfg = client
    r = c.post("/api/command", json={"cmd": "stop"})
    assert r.json() == {"ok": True, "cmd": "stop"}
    assert command.read_command(cfg.command_path) == "stop"   # file written
    assert c.get("/api/status").json()["running_state"] == "PAUSED"


def test_command_start_clears_paused(client) -> None:
    c, _cfg = client
    c.post("/api/command", json={"cmd": "stop"})
    c.post("/api/command", json={"cmd": "start"})
    assert c.get("/api/status").json()["running_state"] == "RUNNING"


def test_command_invalid_is_400(client) -> None:
    c, _cfg = client
    assert c.post("/api/command", json={"cmd": "explode"}).status_code == 400


# --- read endpoints --------------------------------------------------------


def test_trades_returns_seeded_rows(client) -> None:
    c, _cfg = client
    rows = c.get("/api/trades").json()
    assert {r["deal_id"] for r in rows} == {"DEAL1", "DEAL2"}
    closed = next(r for r in rows if r["deal_id"] == "DEAL1")
    assert closed["status"] == "CLOSED" and closed["profit_loss"] == -41.16


def test_score_returns_reward_rows(client) -> None:
    c, _cfg = client
    rows = c.get("/api/score").json()
    assert len(rows) == 1 and rows[0]["score_after"] == 47.5


def test_confidence_shape(client) -> None:
    c, _cfg = client
    body = c.get("/api/confidence").json()
    assert body["state"] in ("OK", "INSUFFICIENT")   # 1 demo trade → INSUFFICIENT
    assert "n" in body and "n_min" in body


def test_lessons_returns_seeded_row(client) -> None:
    c, _cfg = client
    rows = c.get("/api/lessons").json()
    assert len(rows) == 2
    assert "relief rally" in rows[1]["lesson_text"]  # newest-first; older seeded row


def test_lessons_expose_provenance(client) -> None:
    """v1.5 (Step 4 addendum): /api/lessons surfaces provenance (from market_context_json)
    so the dashboard can label verification-trade lessons instead of showing them unmarked;
    a pre-v1.5 row with no market_context_json degrades to a NULL provenance, not an error."""
    c, _cfg = client
    rows = c.get("/api/lessons").json()
    by_text = {r["lesson_text"]: r["provenance"] for r in rows}
    assert by_text["Avoid shorting into a relief rally."] == "autonomous"
    assert by_text["Old lesson written before the provenance tag existed."] is None


def test_last_cycle_shape(client) -> None:
    c, _cfg = client
    body = c.get("/api/last_cycle").json()
    assert "last_no_trade_reason" in body and "trades_today" in body


# --- fail-soft + isolation -------------------------------------------------


def test_missing_db_returns_empty(tmp_path) -> None:
    """A not-yet-created DB → read endpoints return [] (the daemon may not have run init_db)."""
    cfg = dataclasses.replace(
        SchedulerConfig(),
        live_db_path=str(tmp_path / "nope.sqlite"),
        state_path=str(tmp_path / "state.json"),
        kill_path=str(tmp_path / "KILL"),
        command_path=str(tmp_path / "cmd.json"),
    )
    c = TestClient(create_app(cfg))
    assert c.get("/api/trades").json() == []
    assert c.get("/api/score").json() == []
    assert c.get("/api/status").status_code == 200   # status still renders


def test_db_connection_is_read_only(client) -> None:
    """The isolation proof: the UI's connection refuses writes (SQLite ``mode=ro``)."""
    _c, cfg = client
    conn = ro_connect(cfg.live_db_path)
    try:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("INSERT INTO trade_outcomes (deal_id) VALUES ('HACK')")
    finally:
        conn.close()


# --- token meter -----------------------------------------------------------


def _utc_z(local_dt: datetime) -> str:
    """A noon-local datetime → the UTC ``...Z`` string ``token_meter`` writes."""
    noon = local_dt.replace(hour=12, minute=0, second=0, microsecond=0)
    return noon.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _write_usage_log(cfg) -> None:
    """Two records today + one yesterday (Berlin) at the wiring's ``llm_usage.json`` path."""
    tz = ZoneInfo(cfg.tz)
    today = datetime.now(tz)
    yest = today - timedelta(days=1)
    records = [
        {"ts": _utc_z(today), "model": "claude-sonnet-4-6", "input_tokens": 1000,
         "output_tokens": 200, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
         "est_cost_usd": 0.006, "est_cost_eur": 0.0055},
        {"ts": _utc_z(today), "model": "claude-haiku-4-5-20251001", "input_tokens": 500,
         "output_tokens": 100, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
         "est_cost_usd": 0.001, "est_cost_eur": 0.0009},
        {"ts": _utc_z(yest), "model": "claude-sonnet-4-6", "input_tokens": 9999,
         "output_tokens": 9999, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
         "est_cost_usd": 9.9, "est_cost_eur": 9.9},
    ]
    (Path(cfg.state_path).parent / "llm_usage.json").write_text(
        json.dumps(records), encoding="utf-8"
    )


def test_token_usage_counts_today_only(client) -> None:
    c, cfg = client
    _write_usage_log(cfg)
    body = c.get("/api/token_usage").json()
    assert body["consumed_tokens"] == 1800          # (1000+200)+(500+100); yesterday excluded
    assert body["calls_today"] == 2
    assert abs(body["cost_eur_today"] - 0.0064) < 1e-9
    assert body["budget"] == 200_000                # the armed default
    assert body["percent"] == 0.9                   # 100*1800/200000


def test_token_usage_missing_log_is_zeros(client) -> None:
    c, _cfg = client                                # fixture writes no llm_usage.json
    body = c.get("/api/token_usage").json()
    assert body["consumed_tokens"] == 0
    assert body["calls_today"] == 0
    assert body["percent"] == 0.0
    assert body["budget"] == 200_000


def test_token_usage_budget_disabled_percent_none(tmp_path) -> None:
    cfg = dataclasses.replace(
        SchedulerConfig(daily_token_budget=None),
        live_db_path=str(tmp_path / "trading_bot.sqlite"),
        state_path=str(tmp_path / "scheduler_state.json"),
        kill_path=str(tmp_path / "KILL"),
        command_path=str(tmp_path / "cmd.json"),
    )
    body = TestClient(create_app(cfg)).get("/api/token_usage").json()
    assert body["budget"] is None
    assert body["percent"] is None                  # no budget ⇒ no percent


# --- last-cycle reasoning detail -------------------------------------------


def test_last_cycle_surfaces_pick_and_debate(client) -> None:
    c, cfg = client
    state_dir = Path(cfg.state_path).parent
    (state_dir / "turbo_candidates.json").write_text(
        json.dumps([{
            "epic": "IX.D.DAX.IFMM.IP", "direction": "BUY", "llm_confidence": 72.0,
            "reasoning": "Momentum and a tight spread favor a long.", "score_at_pick": 55.0,
            "threshold_applied": 55.0, "generated_at": "2026-06-28T09:30:00Z", "source": "research",
        }]), encoding="utf-8",
    )
    (state_dir / "debate_log.json").write_text(
        json.dumps([{
            "ts": "2026-06-28T09:31:00Z", "epic": "IX.D.DAX.IFMM.IP", "seed_direction": "BUY",
            "final_decision": "TRADE", "final_direction": "BUY", "confidence": 67.0,
            "rounds_used": 1, "rationale": "The bull case is stronger.",
            "regime_snapshot": {"spread_pct": 0.01},
            "transcript": [
                {"round": 1, "agent": "BULL", "model": "claude-haiku-4-5-20251001",
                 "text": "Up we go.", "usage": {"input_tokens": 1}},
                {"round": 1, "agent": "BEAR", "model": "claude-haiku-4-5-20251001",
                 "text": "Be careful.", "usage": {"input_tokens": 1}},
                {"round": 1, "agent": "JUDGE", "model": "claude-sonnet-4-6",
                 "text": "Trade BUY.", "usage": {"input_tokens": 1}},
            ],
        }]), encoding="utf-8",
    )
    body = c.get("/api/last_cycle").json()
    assert body["research_pick"]["reasoning"].startswith("Momentum")
    assert body["research_pick"]["llm_confidence"] == 72.0
    assert body["debate"]["final_decision"] == "TRADE"
    assert [t["agent"] for t in body["debate"]["transcript"]] == ["BULL", "BEAR", "JUDGE"]
    assert "usage" not in body["debate"]["transcript"][0]   # payload kept lean
    assert "last_no_trade_reason" in body and "session_date" in body  # existing fields preserved


def test_last_cycle_absent_artifacts_are_null(client) -> None:
    c, _cfg = client                                # fixture writes neither file
    body = c.get("/api/last_cycle").json()
    assert body["research_pick"] is None
    assert body["debate"] is None
    assert body["last_no_trade_detail"] is None     # no abstain prose in the seeded state
    assert body["trades_today"] == 1                # existing cycle field still present


def test_last_cycle_exposes_abstain_detail(client) -> None:
    c, cfg = client
    StateStore(cfg.state_path).save(
        SchedulerState(date="2026-06-28", last_no_trade_reason="LLM_ABSTAIN",
                       last_no_trade_detail="Weak momentum and a wide spread; skipping.")
    )
    body = c.get("/api/last_cycle").json()
    assert body["last_no_trade_reason"] == "LLM_ABSTAIN"
    assert body["last_no_trade_detail"] == "Weak momentum and a wide spread; skipping."


# --- discovery (Phase 14 §5.5 / §6 C3) -------------------------------------


def test_discovery_unarmed_reports_false(client) -> None:
    """The flag file is absent on a fresh checkout — ``armed`` reads False."""
    c, _cfg = client
    body = c.get("/api/discovery").json()
    assert body["armed"] is False
    assert body["armed_by"] is None
    assert body["armed_ts"] is None
    assert body["last_run_utc"] is None


def test_discovery_arm_creates_flag_and_subsequent_get_reports_true(client) -> None:
    """POST /api/discovery/arm writes the flag file; a follow-up GET sees armed=true."""
    from source_registry.arm import DEFAULT_ARM_PATH
    c, _cfg = client
    r = c.post("/api/discovery/arm")
    assert r.status_code == 200
    assert r.json() == {"ok": True, "armed": True}
    # The flag file lives at the Phase-14 DEFAULT_ARM_PATH — same path the daemon reads.
    assert DEFAULT_ARM_PATH.exists()
    body = c.get("/api/discovery").json()
    assert body["armed"] is True
    assert body["armed_by"] == "dashboard"


def test_discovery_disarm_removes_flag(client) -> None:
    """POST /api/discovery/disarm deletes the flag file (no-op if absent)."""
    from source_registry.arm import DEFAULT_ARM_PATH
    c, _cfg = client
    c.post("/api/discovery/arm")             # arm first
    assert DEFAULT_ARM_PATH.exists()
    r = c.post("/api/discovery/disarm")
    assert r.status_code == 200
    assert r.json() == {"ok": True, "armed": False}
    assert not DEFAULT_ARM_PATH.exists()
    # GET now reports unarmed again.
    assert c.get("/api/discovery").json()["armed"] is False


def test_discovery_endpoint_fails_soft_without_migration_007(client) -> None:
    """Migration 007 is not applied in this fixture (the seeded DB has no
    ``instrument_source_availability`` table) — the endpoint must return ``None`` counts,
    not 500. This is the Plan §6 C3 acceptance for the fail-soft direction.
    """
    c, _cfg = client
    body = c.get("/api/discovery").json()
    # Fail-soft contract: rows_total / rows_by_source / stale_rows are None
    # when the availability table isn't there yet.
    assert body["rows_total"] is None
    assert body["rows_by_source"] is None
    assert body["stale_rows"] is None
    # And the arm-flag is still reported correctly (independent of DB).
    assert body["armed"] is False
