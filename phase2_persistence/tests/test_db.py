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


def test_insert_trade_persists_provenance(db, base_trade):
    # Migration 003 (Phase 8 v1.6, Cause A part 2): the provenance tag must round-trip.
    db.insert_trade({**base_trade, "provenance": "verification"})
    trade = db.get_trade_by_deal_id("DEAL1")
    assert trade["provenance"] == "verification"


def test_insert_trade_provenance_defaults_to_null(db, base_trade):
    db.insert_trade(base_trade)
    trade = db.get_trade_by_deal_id("DEAL1")
    assert trade["provenance"] is None


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


# -- cascade -----------------------------------------------------------------
# `market_regime_snapshots`/`decision_context` used to cascade from `trade_outcomes`
# too (V2 placeholder era); migration 005 (2026-07-11) DROP+CREATE'd both to an
# epic-scoped V3 schema with no `trade_id` FK — they're no longer children of
# `trade_outcomes` and `Database.insert_regime_snapshot`/`insert_decision_context` were
# removed (see `phase2_persistence/CLAUDE.md`). Their new schema is asserted in
# `test_migrations.py::test_v3_learning_tables_present`.


def test_cascade_delete_removes_children(db, base_trade):
    tid = db.insert_trade(base_trade)
    db.insert_reward(tid, {"score_after": 55.0, "win_loss": "WIN"})
    db.insert_lesson(tid, {"lesson_text": "x"})

    db.conn.execute("DELETE FROM trade_outcomes WHERE id = ?", (tid,))
    db.conn.commit()

    for table in ("reward_pts", "trade_lessons"):
        count = db.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert count == 0, table


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


def test_for_prompt_max_age_days_drops_stale_lessons(db, base_trade):
    """H4-a: four lessons had owned every research prompt for weeks (5.973 renderings,
    the oldest 36 days running). The age cap is relative to now, unlike the fixed-date
    ``quarantine_before`` — hence the computed timestamps here."""
    from datetime import datetime, timedelta, timezone

    def _iso(days_ago: int) -> str:
        ts = datetime.now(timezone.utc) - timedelta(days=days_ago)
        return ts.strftime("%Y-%m-%dT%H:%M:%S.") + f"{ts.microsecond // 1000:03d}Z"

    tid = db.insert_trade(base_trade)
    db.insert_lesson(tid, {"lesson_text": "ancient", "extracted_at": _iso(40)})
    db.insert_lesson(tid, {"lesson_text": "stale", "extracted_at": _iso(31)})
    db.insert_lesson(tid, {"lesson_text": "fresh", "extracted_at": _iso(3)})

    texts = [l["lesson_text"] for l in db.get_recent_lessons_for_prompt(5, max_age_days=30)]
    assert texts == ["fresh"]

    # off by default — the pre-H4-a behaviour stays reachable for a controlled A/B
    assert len(db.get_recent_lessons_for_prompt(5)) == 3


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


# -- trade_outcomes: get_recent_trades_for_prompt (v1.6 Phase-8 hotfix, Cause A part 2) ----

def test_trades_for_prompt_no_filter_equals_get_recent_trades(db, base_trade):
    db.insert_trade(base_trade)
    db.insert_trade({**base_trade, "deal_id": "DEAL2"})
    assert db.get_recent_trades_for_prompt(8) == db.get_recent_trades(8)


def test_trades_for_prompt_excludes_tagged_provenance(db, base_trade):
    db.insert_trade({**base_trade, "deal_id": "VERIF", "provenance": "verification"})
    db.insert_trade({**base_trade, "deal_id": "AUTO", "provenance": "autonomous"})
    db.insert_trade({**base_trade, "deal_id": "UNTAGGED"})  # no provenance → NULL → kept
    ids = [
        t["deal_id"]
        for t in db.get_recent_trades_for_prompt(8, exclude_provenance=("verification",))
    ]
    assert "VERIF" not in ids
    assert "AUTO" in ids and "UNTAGGED" in ids


def test_trades_for_prompt_hold_time_filter(db, base_trade):
    db.insert_trade({**base_trade, "deal_id": "SHORT"})  # open_ts 09:00
    db.update_trade_close("SHORT", {"close_ts": "2026-05-21T09:01:00.000Z"})  # 1 min hold
    db.insert_trade({**base_trade, "deal_id": "LONG"})
    db.update_trade_close("LONG", {"close_ts": "2026-05-21T10:00:00.000Z"})  # 60 min hold
    db.insert_trade({**base_trade, "deal_id": "OPENQ"})  # never closed → NULL hold
    ids = [t["deal_id"] for t in db.get_recent_trades_for_prompt(8, min_hold_min=2.0)]
    assert "SHORT" not in ids
    assert "LONG" in ids
    assert "OPENQ" in ids  # NULL hold → fail-open keep (still-open trade)


def test_trades_for_prompt_quarantine_before(db, base_trade):
    db.insert_trade({**base_trade, "deal_id": "OLD", "open_ts": "2026-05-20T00:00:00.000Z"})
    db.insert_trade({**base_trade, "deal_id": "NEW", "open_ts": "2026-06-30T00:00:00.000Z"})
    ids = [
        t["deal_id"]
        for t in db.get_recent_trades_for_prompt(8, quarantine_before="2026-06-01T00:00:00.000Z")
    ]
    assert "OLD" not in ids
    assert "NEW" in ids


def test_trades_for_prompt_combined_returns_newest_n_survivors(db, base_trade):
    db.insert_trade({**base_trade, "deal_id": "DROP_VERIF", "provenance": "verification"})
    db.insert_trade({**base_trade, "deal_id": "KEEP1", "provenance": "autonomous"})
    db.insert_trade({**base_trade, "deal_id": "DROP_OLD", "open_ts": "2026-01-01T00:00:00.000Z"})
    db.insert_trade({**base_trade, "deal_id": "KEEP2"})  # never closed → NULL hold, not dropped
    db.insert_trade({**base_trade, "deal_id": "KEEP3"})
    got = db.get_recent_trades_for_prompt(
        2,
        min_hold_min=2.0,
        quarantine_before="2026-03-01T00:00:00.000Z",
        exclude_provenance=("verification",),
    )
    # survivors are KEEP1/KEEP2/KEEP3; LIMIT 2 returns the newest two, id DESC.
    assert [t["deal_id"] for t in got] == ["KEEP3", "KEEP2"]


# -- D2.1: get_recent_rewards + count_closed_trades --------------------------
# Phase 16 D2: read methods for the Instinct-Extractor + the
# promote_eligible gate (Plan §6 D2.1).


def test_get_recent_rewards_returns_newest_first(db, base_trade):
    """Phase 16 D2.1: ``get_recent_rewards(n)`` returns the ``n`` newest
    ``reward_pts`` rows, id DESC. Mirrors ``get_recent_lessons``."""
    tid = db.insert_trade(base_trade)
    for score in (40.0, 50.0, 60.0):
        db.insert_reward(tid, {"score_after": score, "win_loss": "BREAKEVEN"})
    got = db.get_recent_rewards(n=2)
    assert len(got) == 2
    # newest first
    assert got[0]["score_after"] == 60.0
    assert got[1]["score_after"] == 50.0


def test_get_recent_rewards_empty_db_returns_empty_list(db):
    """Phase 16 D2.1: no rewards yet ⇒ ``[]``, not None, not a default."""
    assert db.get_recent_rewards(n=20) == []


def test_count_closed_trades_only_counts_status_closed(db, base_trade):
    """Phase 16 D2.1: ``count_closed_trades()`` only counts ``status='CLOSED'``.
    OPEN / CANCELLED don't qualify — only CLOSED trades
    contribute to ``n_closed`` for the ``promote_eligible`` gate."""
    open_trade = {**base_trade, "deal_id": "OPEN1", "status": "OPEN"}
    cancelled = {**base_trade, "deal_id": "CAN1", "status": "CANCELLED"}
    closed = {**base_trade, "deal_id": "C1", "status": "CLOSED"}
    closed2 = {**base_trade, "deal_id": "C2", "status": "CLOSED"}
    for t in (open_trade, cancelled, closed, closed2):
        db.insert_trade(t)
    assert db.count_closed_trades() == 2


def test_count_closed_trades_empty_db_returns_zero(db):
    """Phase 16 D2.1: no trades ⇒ ``0``."""
    assert db.count_closed_trades() == 0
