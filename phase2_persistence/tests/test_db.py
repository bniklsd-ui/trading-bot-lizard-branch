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


def test_insert_trade_persists_initial_risk_and_account(db, base_trade):
    # Migration 002 + whitelist: the Phase-7 reward keys must round-trip.
    db.insert_trade({**base_trade, "initial_risk": 30.0, "account": "demo"})
    trade = db.get_trade_by_deal_id("DEAL1")
    assert trade["initial_risk"] == 30.0
    assert trade["account"] == "demo"


# -- reward_pts -------------------------------------------------------------

def test_insert_reward_returns_id(db, base_trade):
    tid = db.insert_trade(base_trade)
    rid = db.insert_reward(tid, {"score_after": 55.0, "win_loss": "WIN"})
    assert rid >= 1


def test_insert_reward_persists_r_multiple(db, base_trade):
    # Migration 002 + whitelist: the Phase-7 r_multiple must round-trip.
    tid = db.insert_trade(base_trade)
    db.insert_reward(tid, {"score_after": 55.0, "win_loss": "WIN", "r_multiple": 2.5})
    row = db.conn.execute(
        "SELECT r_multiple FROM reward_pts WHERE trade_id = ?", (tid,)
    ).fetchone()
    assert row["r_multiple"] == 2.5


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


# -- trade_lessons: get_recent_lessons_for_prompt (v1.5 Phase-8 hotfix Step 4 A) ----

def test_for_prompt_no_filter_equals_get_recent_lessons(db, base_trade):
    tid = db.insert_trade(base_trade)
    db.insert_lesson(tid, {"lesson_text": "a"})
    db.insert_lesson(tid, {"lesson_text": "b"})
    assert db.get_recent_lessons_for_prompt(5) == db.get_recent_lessons(5)


def test_for_prompt_excludes_tagged_provenance(db, base_trade):
    tid = db.insert_trade(base_trade)
    db.insert_lesson(tid, {"lesson_text": "verif", "market_context_json": {"provenance": "verification"}})
    db.insert_lesson(tid, {"lesson_text": "auto", "market_context_json": {"provenance": "autonomous"}})
    db.insert_lesson(tid, {"lesson_text": "untagged"})  # no market_context_json → NULL tag → kept
    texts = [
        l["lesson_text"]
        for l in db.get_recent_lessons_for_prompt(5, exclude_provenance=("verification",))
    ]
    assert "verif" not in texts
    assert "auto" in texts and "untagged" in texts


def test_for_prompt_hold_time_filter(db, base_trade):
    short = db.insert_trade({**base_trade, "deal_id": "SHORT"})  # open_ts 09:00
    db.update_trade_close("SHORT", {"close_ts": "2026-05-21T09:01:00.000Z"})  # 1 min hold
    db.insert_lesson(short, {"lesson_text": "short-hold"})
    long_ = db.insert_trade({**base_trade, "deal_id": "LONG"})
    db.update_trade_close("LONG", {"close_ts": "2026-05-21T10:00:00.000Z"})  # 60 min hold
    db.insert_lesson(long_, {"lesson_text": "long-hold"})
    openq = db.insert_trade({**base_trade, "deal_id": "OPENQ"})  # never closed → NULL hold
    db.insert_lesson(openq, {"lesson_text": "open-hold"})
    texts = [l["lesson_text"] for l in db.get_recent_lessons_for_prompt(5, min_hold_min=2.0)]
    assert "short-hold" not in texts
    assert "long-hold" in texts
    assert "open-hold" in texts  # NULL hold → fail-open keep


def test_for_prompt_quarantine_before(db, base_trade):
    tid = db.insert_trade(base_trade)
    db.insert_lesson(tid, {"lesson_text": "old", "extracted_at": "2026-05-20T00:00:00.000Z"})
    db.insert_lesson(tid, {"lesson_text": "new", "extracted_at": "2026-06-30T00:00:00.000Z"})
    texts = [
        l["lesson_text"]
        for l in db.get_recent_lessons_for_prompt(5, quarantine_before="2026-06-01T00:00:00.000Z")
    ]
    assert "old" not in texts
    assert "new" in texts


def test_for_prompt_combined_returns_newest_n_survivors(db, base_trade):
    tid = db.insert_trade(base_trade)  # never closed → NULL hold (not dropped by hold rule)
    db.insert_lesson(tid, {"lesson_text": "drop-verif", "market_context_json": {"provenance": "verification"}})
    db.insert_lesson(tid, {"lesson_text": "keep1", "market_context_json": {"provenance": "autonomous"}})
    db.insert_lesson(tid, {"lesson_text": "drop-old", "extracted_at": "2026-01-01T00:00:00.000Z"})
    db.insert_lesson(tid, {"lesson_text": "keep2"})
    db.insert_lesson(tid, {"lesson_text": "keep3"})
    got = db.get_recent_lessons_for_prompt(
        2,
        min_hold_min=2.0,
        quarantine_before="2026-03-01T00:00:00.000Z",
        exclude_provenance=("verification",),
    )
    # survivors are keep1/keep2/keep3; LIMIT 2 returns the newest two, id DESC.
    assert [l["lesson_text"] for l in got] == ["keep3", "keep2"]
