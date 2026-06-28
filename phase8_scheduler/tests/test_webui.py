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
import sqlite3

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
            used_in_research INTEGER, extracted_at TEXT
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
        "INSERT INTO trade_lessons (trade_id, lesson_text, used_in_research, extracted_at) VALUES "
        "(1,'Avoid shorting into a relief rally.',0,'2026-06-28T10:05:02Z')"
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
    assert body["trades_today"] == 1
    assert body["max_trades_per_day"] == 5
    assert body["session_date"] == "2026-06-28"


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
    assert len(rows) == 1
    assert "relief rally" in rows[0]["lesson_text"]


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
