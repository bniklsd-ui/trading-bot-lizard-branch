"""CRUD tests for the Database layer."""

from __future__ import annotations

import json

import pytest


# -- trade_outcomes ---------------------------------------------------------

def test_insert_trade_returns_id(db, base_trade):
    assert db.insert_trade(base_trade) >= 1


def test_insert_trade_sets_defaults(db, base_trade):
    tid = db.insert_trade(base_trade)
    trade = db.get_trade_by_deal_id("DEAL1")
    assert trade["id"] == tid
    assert trade["status"] == "OPEN"
    assert trade["broker"] == "ig"
    assert trade["created_at"] and trade["updated_at"]


def test_get_trade_by_deal_id_missing_returns_none(db):
    assert db.get_trade_by_deal_id("NOPE") is None


def test_get_open_trades_filters_by_status(db, base_trade):
    db.insert_trade(base_trade)
    db.insert_trade({**base_trade, "deal_id": "DEAL2"})
    db.update_trade_close("DEAL2", {"close_level": 18100.0, "profit_loss": 100.0})
    open_trades = db.get_open_trades()
    assert [t["deal_id"] for t in open_trades] == ["DEAL1"]


def test_update_trade_close_sets_fields(db, base_trade):
    db.insert_trade(base_trade)
    ok = db.update_trade_close(
        "DEAL1",
        {"close_level": 18120.0, "profit_loss": 120.0,
         "close_ts": "2026-05-21T09:30:00.000Z"},
    )
    assert ok is True
    trade = db.get_trade_by_deal_id("DEAL1")
    assert trade["status"] == "CLOSED"
    assert trade["close_level"] == 18120.0
    assert trade["profit_loss"] == 120.0


def test_update_trade_close_computes_hold_duration(db, base_trade):
    db.insert_trade(base_trade)  # open_ts 09:00
    db.update_trade_close("DEAL1", {"close_ts": "2026-05-21T09:30:00.000Z"})
    trade = db.get_trade_by_deal_id("DEAL1")
    assert trade["hold_duration_min"] == pytest.approx(30.0)


def test_update_trade_close_default_close_ts(db, base_trade):
    db.insert_trade(base_trade)
    assert db.update_trade_close("DEAL1", {"profit_loss": 5.0}) is True
    trade = db.get_trade_by_deal_id("DEAL1")
    assert trade["close_ts"] is not None
    assert trade["hold_duration_min"] is not None


def test_update_trade_close_missing_returns_false(db):
    assert db.update_trade_close("NOPE", {"profit_loss": 1.0}) is False


def test_get_recent_trades_ordering_and_limit(db, base_trade):
    for i in range(3):
        db.insert_trade({**base_trade, "deal_id": f"DEAL{i}"})
    recent = db.get_recent_trades(n=2)
    assert [t["deal_id"] for t in recent] == ["DEAL2", "DEAL1"]


def test_gate_path_dict_is_json_serialized(db, base_trade):
    db.insert_trade({**base_trade, "gate_path": {"gate1": True, "gate2": False}})
    trade = db.get_trade_by_deal_id("DEAL1")
    assert json.loads(trade["gate_path"]) == {"gate1": True, "gate2": False}


# -- reward_pts -------------------------------------------------------------

def test_insert_reward_returns_id(db, base_trade):
    tid = db.insert_trade(base_trade)
    rid = db.insert_reward(tid, {"score_after": 55.0, "win_loss": "WIN"})
    assert rid >= 1


def test_get_current_score_default_when_no_rewards(db):
    assert db.get_current_score() == 50.0


def test_get_current_score_returns_latest(db, base_trade):
    tid = db.insert_trade(base_trade)
    db.insert_reward(tid, {"score_after": 55.0, "win_loss": "WIN"})
    db.insert_reward(tid, {"score_after": 47.5, "win_loss": "LOSS"})
    assert db.get_current_score() == 47.5


def test_risk_level_default_konservativ(db):
    assert db.get_risk_level() == "KONSERVATIV"


def test_risk_level_aggressiv_above_threshold(db, base_trade):
    tid = db.insert_trade(base_trade)
    db.insert_reward(tid, {"score_after": 70.0, "win_loss": "WIN"})
    assert db.get_risk_level() == "AGGRESSIV"


def test_risk_level_konservativ_below_threshold(db, base_trade):
    tid = db.insert_trade(base_trade)
    db.insert_reward(tid, {"score_after": 30.0, "win_loss": "LOSS"})
    assert db.get_risk_level() == "KONSERVATIV"


def test_risk_level_at_threshold_is_konservativ(db, base_trade):
    tid = db.insert_trade(base_trade)
    db.insert_reward(tid, {"score_after": 50.0, "win_loss": "BREAKEVEN"})
    assert db.get_risk_level() == "KONSERVATIV"


# -- trade_lessons ----------------------------------------------------------

def test_insert_and_get_recent_lessons(db, base_trade):
    tid = db.insert_trade(base_trade)
    db.insert_lesson(tid, {"lesson_text": "Avoid wide spreads at open."})
    db.insert_lesson(tid, {"lesson_text": "Trend days reward patience."})
    lessons = db.get_recent_lessons(n=5)
    assert lessons[0]["lesson_text"] == "Trend days reward patience."
    assert len(lessons) == 2


def test_market_context_dict_is_json_serialized(db, base_trade):
    tid = db.insert_trade(base_trade)
    db.insert_lesson(tid, {"lesson_text": "x", "market_context_json": {"vix": 18}})
    lesson = db.get_recent_lessons()[0]
    assert json.loads(lesson["market_context_json"]) == {"vix": 18}


def test_mark_lesson_used_increments_and_stamps(db, base_trade):
    tid = db.insert_trade(base_trade)
    lid = db.insert_lesson(tid, {"lesson_text": "x"})
    db.mark_lesson_used(lid)
    db.mark_lesson_used(lid)
    lesson = db.get_recent_lessons()[0]
    assert lesson["used_in_research"] == 2
    assert lesson["last_used_ts"] is not None


# -- ig_config_state --------------------------------------------------------

@pytest.mark.parametrize("value", [42.5, "AGGRESSIV", True, False, {"a": 1}, [1, 2, 3]])
def test_config_roundtrip_various_types(db, value):
    db.set_config("k", value)
    assert db.get_config("k") == value


def test_get_config_missing_returns_none(db):
    assert db.get_config("does_not_exist") is None


def test_set_config_upserts(db):
    db.set_config("k", 1)
    db.set_config("k", 2, note="updated")
    assert db.get_config("k") == 2


def test_get_all_config_includes_seeds(db):
    config = db.get_all_config()
    assert {"bot_score", "risk_level", "daily_pnl_today",
            "session_date", "force_trigger_locked"}.issubset(config)


# -- cascade + V2 -----------------------------------------------------------

def test_cascade_delete_removes_children(db, base_trade):
    tid = db.insert_trade(base_trade)
    db.insert_reward(tid, {"score_after": 55.0, "win_loss": "WIN"})
    db.insert_lesson(tid, {"lesson_text": "x"})
    db.insert_regime_snapshot(tid, {"spread_pct": 0.4})
    db.insert_decision_context(tid, {"judge_confidence": 0.8})

    db.conn.execute("DELETE FROM trade_outcomes WHERE id = ?", (tid,))
    db.conn.commit()

    for table in ("reward_pts", "trade_lessons",
                  "market_regime_snapshots", "decision_context"):
        count = db.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert count == 0, table


def test_insert_regime_snapshot(db, base_trade):
    tid = db.insert_trade(base_trade)
    sid = db.insert_regime_snapshot(tid, {"volatility_pct": 1.2, "spread_pct": 0.4})
    assert sid >= 1
    row = db.conn.execute(
        "SELECT * FROM market_regime_snapshots WHERE id = ?", (sid,)
    ).fetchone()
    assert row["snapshot_ts"] is not None


def test_insert_decision_context_serializes_json(db, base_trade):
    tid = db.insert_trade(base_trade)
    cid = db.insert_decision_context(
        tid, {"judge_confidence": 0.7, "veto_factors_json": {"spread": "ok"}}
    )
    row = db.conn.execute(
        "SELECT * FROM decision_context WHERE id = ?", (cid,)
    ).fetchone()
    assert json.loads(row["veto_factors_json"]) == {"spread": "ok"}
