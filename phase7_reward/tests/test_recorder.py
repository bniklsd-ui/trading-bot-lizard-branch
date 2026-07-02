"""Tests for ``reward.recorder.RewardSink`` (concept §6 Step 8, Decision A/J).

The recorder is the orchestration: ``on_trade_opened`` persists the decision context
and stashes it; ``on_trade_closed`` resolves P&L, closes the trade, scores it, writes
the reward, and best-effort extracts a lesson. **Every step is fail-closed** (Decision
J): any failure logs ``critical`` and the cycle continues — a reward/lesson failure
**never** raises into the Phase-5 close path. These tests pin that contract with
``FakeDB`` / ``FakeBroker`` / ``FakeBrain`` and the real ``Scorer`` (mocked, no I/O).
"""

from __future__ import annotations

import logging

import pytest

from reward.models import LessonResult, RewardConfig
from reward.recorder import RewardSink
from reward.scorer import Scorer
from tests.conftest import FakeBroker, FakeBrain, FakeDB, make_tx

CFG = RewardConfig()


def _sink(db, *, broker=None, brain=None, confidence_provider=None):
    """Wire a RewardSink with the real Scorer and the given fakes."""
    return RewardSink(
        db=db,
        broker=broker if broker is not None else FakeBroker([make_tx()]),
        scorer=Scorer(CFG),
        brain=brain if brain is not None else FakeBrain(),
        cfg=CFG,
        confidence_provider=confidence_provider,
    )


# --- on_trade_opened ------------------------------------------------------


def test_on_trade_opened_inserts_trade_and_stashes(make_opened):
    db = FakeDB()
    sink = _sink(db)
    opened = make_opened()

    sink.on_trade_opened(opened)

    row = db.get_trade_by_deal_id(opened.deal_id)
    assert row is not None
    assert row["epic"] == opened.epic
    assert row["open_level"] == opened.intended_open_level  # intended_open_level -> open_level
    assert row["initial_risk"] == opened.initial_risk
    assert row["account"] == opened.account
    assert row["status"] == "OPEN"
    # the full open context is stashed for close-time scoring
    assert sink._opened[opened.deal_id] is opened


def test_on_trade_opened_persists_provenance(make_opened):
    """v1.6 (Phase-8 hotfix, Cause A part 2): the same provenance tag that already reaches
    the lesson's market_context_json (see test_on_trade_closed's lesson assertions) must also
    land on the trade_outcomes row itself, so the SEPARATE recent_trades prompt channel
    (P4 context_builder.get_recent_trades_for_prompt) can filter on it too — migration 003.
    """
    db = FakeDB()
    sink = _sink(db)
    opened = make_opened(provenance="verification")

    sink.on_trade_opened(opened)

    row = db.get_trade_by_deal_id(opened.deal_id)
    assert row["provenance"] == "verification"


def test_on_trade_opened_provenance_defaults_to_autonomous(make_opened):
    db = FakeDB()
    sink = _sink(db)
    opened = make_opened()  # no explicit provenance override

    sink.on_trade_opened(opened)

    row = db.get_trade_by_deal_id(opened.deal_id)
    assert row["provenance"] == "autonomous"


def test_on_trade_opened_insert_failure_is_fail_closed(make_opened, caplog):
    db = FakeDB(fail_on={"insert_trade"})
    sink = _sink(db)
    with caplog.at_level(logging.CRITICAL):
        sink.on_trade_opened(make_opened())  # must not raise
    assert any(r.levelno == logging.CRITICAL for r in caplog.records)


# --- on_trade_closed: happy path -----------------------------------------


def test_full_open_close_writes_all_three_tables(make_opened, make_closed):
    db = FakeDB()
    sink = _sink(db)
    opened = make_opened()  # size 1.0 @ 18000, initial_risk 30 -> matches make_tx (+30 -> r=1.0)
    sink.on_trade_opened(opened)

    sink.on_trade_closed(make_closed(status="CLOSED_BY_BROKER"))

    # 1) trade closed
    assert len(db.closes) == 1
    _, close_data = db.closes[0]
    assert close_data["close_level"] == 18030.0
    assert close_data["profit_loss"] == 30.0
    assert close_data["status"] == "CLOSED"
    # 2) reward written, mapped onto the P2 column names
    assert len(db.rewards) == 1
    trade_id, reward = db.rewards[0]
    assert trade_id == db.get_trade_by_deal_id(opened.deal_id)["id"]
    assert reward["win_loss"] == "WIN"
    assert reward["pnl_raw"] == 30.0
    assert reward["r_multiple"] == pytest.approx(1.0)
    assert reward["spread_at_entry_pct"] == opened.spread_at_entry_pct
    assert reward["debate_confidence"] == opened.debate_confidence
    # outcome/process deltas mapped from the RewardResult component names
    expected = Scorer(CFG).score(
        r_multiple=1.0, status="CLOSED_BY_BROKER",
        spread_at_entry_pct=opened.spread_at_entry_pct,
        debate_confidence=opened.debate_confidence, score_before=50.0,
    )
    assert reward["outcome_score_delta"] == pytest.approx(expected.outcome_delta)
    assert reward["process_score_delta"] == pytest.approx(expected.process_delta)
    assert reward["score_after"] == pytest.approx(expected.score_after)
    # 3) lesson written
    assert len(db.lessons) == 1
    _, lesson = db.lessons[0]
    assert lesson["lesson_text"]


def test_market_context_handed_to_brain_carries_outcome(make_opened, make_closed):
    db = FakeDB()
    brain = FakeBrain()
    sink = _sink(db, brain=brain)
    sink.on_trade_opened(make_opened())
    sink.on_trade_closed(make_closed(status="TIME_STOP"))

    assert len(brain.calls) == 1
    _, outcome, market_context = brain.calls[0]
    assert market_context["status"] == "TIME_STOP"
    assert market_context["r_multiple"] == pytest.approx(outcome.r_multiple)
    assert market_context["direction"] == "BUY"


def test_market_context_carries_provenance_from_opened(make_opened, make_closed):
    """v1.5 (Step 4 A): the stashed OpenedTrade.provenance is written into the lesson's
    market_context (→ market_context_json), so the research prompt can later exclude it."""
    db = FakeDB()
    brain = FakeBrain()
    sink = _sink(db, brain=brain)
    sink.on_trade_opened(make_opened(provenance="verification"))
    sink.on_trade_closed(make_closed(status="TIME_STOP"))

    _, _, market_context = brain.calls[-1]
    assert market_context["provenance"] == "verification"
    # and it lands in the persisted lesson row's context blob (FakeDB stores (trade_id, dict))
    _, lesson_row = db.lessons[-1]
    assert lesson_row["market_context_json"]["provenance"] == "verification"


def test_market_context_provenance_unknown_on_cold_reconcile(make_opened):
    """Cold reconcile after a restart (no stash, opened is None) → provenance 'unknown'
    (kept by the read-path tag clause, then caught by its hold-time/date fallbacks)."""
    db = FakeDB()
    _sink(db).on_trade_opened(make_opened())  # opened by a now-gone sink instance

    brain = FakeBrain()
    closer = _sink(db, broker=FakeBroker([make_tx()]), brain=brain)
    closer.reconcile_open_trades()

    _, _, market_context = brain.calls[-1]
    assert market_context["provenance"] == "unknown"


def test_score_advances_current_score(make_opened, make_closed):
    db = FakeDB()
    sink = _sink(db)
    sink.on_trade_opened(make_opened())
    sink.on_trade_closed(make_closed())
    assert db.get_current_score() > 50.0  # a +1R clean win lifts the score


# --- on_trade_closed: fail-closed paths ----------------------------------


def test_pnl_unavailable_logs_critical_no_reward_trade_stays_open(make_opened, make_closed, caplog):
    db = FakeDB()
    broker = FakeBroker([])  # empty history -> resolver raises PnLUnavailable
    sink = _sink(db, broker=broker)
    opened = make_opened()
    sink.on_trade_opened(opened)

    with caplog.at_level(logging.CRITICAL):
        sink.on_trade_closed(make_closed())  # must not raise

    assert any(r.levelno == logging.CRITICAL for r in caplog.records)
    assert db.rewards == []
    assert db.closes == []  # update_trade_close not reached -> trade stays OPEN, retry-able
    assert db.get_trade_by_deal_id(opened.deal_id)["status"] == "OPEN"


def test_reward_insert_failure_logs_critical_trade_still_closed(make_opened, make_closed, caplog):
    db = FakeDB(fail_on={"insert_reward"})
    sink = _sink(db)
    opened = make_opened()
    sink.on_trade_opened(opened)

    with caplog.at_level(logging.CRITICAL):
        sink.on_trade_closed(make_closed())  # must not raise

    assert any(r.levelno == logging.CRITICAL for r in caplog.records)
    assert db.rewards == []
    # the trade is still correctly closed at the DB (update_trade_close ran first)
    assert db.get_trade_by_deal_id(opened.deal_id)["status"] == "CLOSED"


def test_lesson_failure_leaves_reward_intact(make_opened, make_closed):
    db = FakeDB()
    brain = FakeBrain(raises_exc=RuntimeError("LLM down"))
    sink = _sink(db, brain=brain)
    sink.on_trade_opened(make_opened())

    sink.on_trade_closed(make_closed())  # must not raise

    assert len(db.rewards) == 1  # reward survives a brain failure
    assert db.lessons == []


def test_lesson_not_ok_is_not_written(make_opened, make_closed):
    db = FakeDB()
    brain = FakeBrain(LessonResult(lesson_text=None, market_context={}, ok=False, error="boom"))
    sink = _sink(db, brain=brain)
    sink.on_trade_opened(make_opened())
    sink.on_trade_closed(make_closed())
    assert len(db.rewards) == 1
    assert db.lessons == []  # ok=False -> no lesson row


def test_close_unknown_deal_logs_critical_no_crash(make_closed, caplog):
    db = FakeDB()  # no open record inserted
    sink = _sink(db)
    with caplog.at_level(logging.CRITICAL):
        sink.on_trade_closed(make_closed())  # must not raise
    assert any(r.levelno == logging.CRITICAL for r in caplog.records)
    assert db.rewards == []
    assert db.closes == []


# --- idempotency ----------------------------------------------------------


def test_double_close_does_not_double_score(make_opened, make_closed):
    db = FakeDB()
    sink = _sink(db)
    sink.on_trade_opened(make_opened())

    sink.on_trade_closed(make_closed())
    score_after_first = db.get_current_score()
    sink.on_trade_closed(make_closed())  # second call for the same deal_id

    assert len(db.rewards) == 1  # not doubled
    assert db.get_current_score() == score_after_first


# --- restart / no-stash fallback -----------------------------------------


def test_close_without_stash_reconstructs_from_db_row(make_opened, make_closed):
    """A fresh sink (no in-memory stash, e.g. after a restart) still resolves+scores
    from the persisted trade row."""
    db = FakeDB()
    opener = _sink(db)
    opener.on_trade_opened(make_opened())

    # a *different* sink instance closes it — its _opened stash is empty
    closer = _sink(db)
    closer.on_trade_closed(make_closed())

    assert len(db.rewards) == 1
    assert db.get_trade_by_deal_id(make_opened().deal_id)["status"] == "CLOSED"


# --- confidence_provider (observe-only, forward-compat) -------------------


def test_confidence_provider_invoked_best_effort(make_opened, make_closed):
    calls = []
    sink = _sink(FakeDB(), confidence_provider=lambda: calls.append(1))
    sink.on_trade_opened(make_opened())
    sink.on_trade_closed(make_closed())
    assert calls == [1]


def test_raising_confidence_provider_does_not_break_close(make_opened, make_closed):
    def boom():
        raise RuntimeError("confidence query failed")

    db = FakeDB()
    sink = _sink(db, confidence_provider=boom)
    sink.on_trade_opened(make_opened())
    sink.on_trade_closed(make_closed())  # must not raise
    assert len(db.rewards) == 1  # the reward still got written


# --- close-confirm P&L (lag-free; preferred over transaction history) ----------


def test_close_confirm_pnl_resolves_without_history(make_opened, make_closed):
    """A close carrying realised P&L writes reward_pts without touching get_trade_history."""
    db = FakeDB()
    broker = FakeBroker([])  # empty history would fail-close if the resolver reached it
    sink = _sink(db, broker=broker)
    opened = make_opened(size=19.6, intended_open_level=24968.9, initial_risk=588.0)
    sink.on_trade_opened(opened)

    sink.on_trade_closed(make_closed(status="TIME_STOP", close_level=24990.0, profit_loss=42.0))

    assert broker.history_calls == 0
    assert len(db.closes) == 1
    assert len(db.rewards) == 1
    _, reward = db.rewards[0]
    assert reward["pnl_raw"] == pytest.approx(42.0)


# --- reconcile_open_trades (the idempotent "later pass" for IG history lag) ----


def test_reconcile_resolves_after_history_catches_up(make_opened, make_closed):
    """In-cycle resolve fail-closed (empty history) → trade stays OPEN; the reconcile
    pass (history now populated) closes + scores it."""
    db = FakeDB()
    broker = FakeBroker(responses=[[], [make_tx()]])  # empty in-cycle, match on reconcile
    sink = _sink(db, broker=broker)
    opened = make_opened()
    sink.on_trade_opened(opened)

    sink.on_trade_closed(make_closed())  # in-cycle: PnLUnavailable → stays OPEN
    assert db.closes == []
    assert db.get_trade_by_deal_id(opened.deal_id)["status"] == "OPEN"

    resolved = sink.reconcile_open_trades([opened.deal_id])

    assert resolved == [opened.deal_id]
    assert db.get_trade_by_deal_id(opened.deal_id)["status"] == "CLOSED"
    assert len(db.rewards) == 1


def test_reconcile_reuses_retained_closed_trade_status(make_opened, make_closed):
    """The retained (exact) ClosedTrade — with its true CLOSED_BY_BROKER exit status —
    is reused on reconcile, not a TIME_STOP reconstruction."""
    db = FakeDB()
    brain = FakeBrain()
    broker = FakeBroker(responses=[[], [make_tx()]])
    sink = _sink(db, broker=broker, brain=brain)
    sink.on_trade_opened(make_opened())
    sink.on_trade_closed(make_closed(status="CLOSED_BY_BROKER"))  # in-cycle fails

    sink.reconcile_open_trades()

    assert brain.calls  # reflect ran on the reconcile pass
    _, _, market_context = brain.calls[-1]
    assert market_context["status"] == "CLOSED_BY_BROKER"


def test_reconcile_is_idempotent(make_opened, make_closed):
    """A second reconcile after the trade is CLOSED is a no-op (no double score)."""
    db = FakeDB()
    broker = FakeBroker(responses=[[], [make_tx()]])
    sink = _sink(db, broker=broker)
    sink.on_trade_opened(make_opened())
    sink.on_trade_closed(make_closed())

    sink.reconcile_open_trades()
    assert len(db.rewards) == 1
    score_after_first = db.get_current_score()

    second = sink.reconcile_open_trades()  # nothing OPEN left
    assert second == []
    assert len(db.rewards) == 1  # not doubled
    assert db.get_current_score() == score_after_first


def test_reconcile_cold_reconstructs_from_row(make_opened):
    """A fresh sink (restart: no stash, no pending close) reconstructs a minimal
    ClosedTrade from the persisted row — defaulting the exit type to TIME_STOP."""
    db = FakeDB()
    _sink(db).on_trade_opened(make_opened())  # opened by a now-gone sink instance

    brain = FakeBrain()
    closer = _sink(db, broker=FakeBroker([make_tx()]), brain=brain)
    resolved = closer.reconcile_open_trades()

    assert resolved == [make_opened().deal_id]
    assert db.get_trade_by_deal_id(make_opened().deal_id)["status"] == "CLOSED"
    assert len(db.rewards) == 1
    _, _, market_context = brain.calls[-1]
    assert market_context["status"] == "TIME_STOP"  # conservative cold default


def test_reconcile_scoped_to_deal_ids_leaves_others_open(make_opened):
    """Passing deal_ids confines the reconcile (live_test targets only its own deal)."""
    db = FakeDB()
    sink = _sink(db, broker=FakeBroker([make_tx()]))
    sink.on_trade_opened(make_opened(deal_id="DEAL-A", deal_reference="ref-a"))
    sink.on_trade_opened(make_opened(deal_id="DEAL-B", deal_reference="ref-b"))

    resolved = sink.reconcile_open_trades(["DEAL-A"])

    assert resolved == ["DEAL-A"]
    assert db.get_trade_by_deal_id("DEAL-A")["status"] == "CLOSED"
    assert db.get_trade_by_deal_id("DEAL-B")["status"] == "OPEN"
