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
from datetime import datetime, timedelta, timezone

import pytest

from reward.models import LessonResult, RewardConfig
from reward.recorder import RewardSink
from reward.scorer import Scorer
from tests.conftest import FakeBroker, FakeBrain, FakeDB, make_tx


def _now_iso() -> str:
    """ISO-8601 UTC timestamp with Z (not +00:00) — P12-Reconcile-Timing helper."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

CFG = RewardConfig()


def _sink(db, *, broker=None, brain=None, confidence_provider=None, instinct_hook=None):
    """Wire a RewardSink with the real Scorer and the given fakes."""
    return RewardSink(
        db=db,
        broker=broker if broker is not None else FakeBroker([make_tx()]),
        scorer=Scorer(CFG),
        brain=brain if brain is not None else FakeBrain(),
        cfg=CFG,
        confidence_provider=confidence_provider,
        instinct_hook=instinct_hook,
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
    # P12-Reconcile-Timing (Mini-Session 26): override open_ts to "now" so the test
    # exercises the fresh-trade CRITICAL path (D4 persistent-fail WARNING kicks in
    # only after >24 h). Real fresh trades are <1 min old.
    from datetime import datetime, timezone
    fresh_open_ts = _now_iso()
    opened = make_opened(open_ts=fresh_open_ts)
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


# --- instinct_hook (Phase 16 D2.5) ----------------------------------------


def test_instinct_hook_called_after_close_with_trade_id(make_opened, make_closed):
    """Phase 16 D2.5: ``instinct_hook(trade_id)`` fires after a successful close,
    with the persisted ``trade_outcomes.id`` int.
    """
    db = FakeDB()
    seen: list[int] = []
    sink = _sink(db, instinct_hook=seen.append)
    sink.on_trade_opened(make_opened())
    sink.on_trade_closed(make_closed())
    assert len(seen) == 1
    assert isinstance(seen[0], int)
    assert seen[0] > 0


def test_raising_instinct_hook_does_not_break_close(make_opened, make_closed):
    """Phase 16 D2.5: a raising instinct_hook must not propagate (best-effort).

    Mirrors the ``confidence_provider`` discipline (Decision C). Trade stays
    CLOSED, reward remains written, no exception escapes.
    """
    def boom(_trade_id: int) -> None:
        raise RuntimeError("bridge blew up")

    db = FakeDB()
    sink = _sink(db, instinct_hook=boom)
    sink.on_trade_opened(make_opened())
    sink.on_trade_closed(make_closed())  # must not raise
    assert len(db.rewards) == 1  # the reward still got written


def test_default_instinct_hook_is_none_and_safe(make_opened, make_closed):
    """Phase 16 D2.5: no instinct_hook wired ⇒ bit-identical to pre-D2.5 behaviour."""
    db = FakeDB()
    sink = _sink(db)  # no instinct_hook passed
    sink.on_trade_opened(make_opened())
    sink.on_trade_closed(make_closed())  # must not raise
    assert len(db.rewards) == 1


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

    # P12-Reconcile-Timing (Mini-Session 26): backoff window is elapsed in production
    # (next scheduler cycle is 5 min after the first attempt; backoff is 15 min so
    # 5 min is still within — the tests simulate that the reconcile *cycle* runs
    # later, e.g. after 20 min). Backdate the last_resolve_attempt_utc so the
    # backoff-skip is bypassed.
    db._trades[opened.deal_id]["last_resolve_attempt_utc"] = "2026-01-01T00:00:00.000Z"

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

    # P12-Reconcile-Timing: backoff bypass (see test_reconcile_resolves_after_history_catches_up).
    # There is only one row in this test.
    for row in db._trades.values():
        row["last_resolve_attempt_utc"] = "2026-01-01T00:00:00.000Z"
        break

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

    # P12-Reconcile-Timing: backoff bypass
    for row in db._trades.values():
        row["last_resolve_attempt_utc"] = "2026-01-01T00:00:00.000Z"

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


# --- P12-Reconcile-Timing (Mini-Session 26, 2026-08-31) --------------------


def test_backoff_skip_within_window(make_opened, make_closed, caplog):
    """A3: backoff-skip wenn last_resolve_attempt_utc innerhalb der naechsten Stufe liegt."""
    from datetime import datetime, timezone, timedelta
    db = FakeDB()
    broker = FakeBroker([])  # empty history -> in-cycle fail
    sink = _sink(db, broker=broker)
    opened = make_opened(open_ts=_now_iso())
    sink.on_trade_opened(opened)

    # In-cycle fail (stamps last_resolve_attempt_utc)
    sink.on_trade_closed(make_closed())
    assert db.get_trade_by_deal_id(opened.deal_id)["last_resolve_attempt_utc"] is not None

    # Manuelle Aufzeichnung der Aufrufe VOR dem zweiten Close
    calls_before = list(db.calls)

    # Zweiter close-Call innerhalb des 15-min-Fensters: Backoff-Skip
    with caplog.at_level(logging.DEBUG):
        sink.on_trade_closed(make_closed())

    # Kein update_trade_resolve_attempt-Call (pre-claim nicht ausgeloest)
    new_calls = [c for c in db.calls if c not in calls_before]
    assert "update_trade_resolve_attempt" not in new_calls
    # Debug-Log wurde emittiert
    assert any(r.levelno == logging.DEBUG and "backoff-skip" in r.getMessage() for r in caplog.records)


def test_persistent_fail_warning(make_opened, make_closed, caplog):
    """A4: WARNING statt CRITICAL wenn open_ts > 24 h zurueckliegt."""
    from datetime import datetime, timezone, timedelta
    db = FakeDB()
    broker = FakeBroker([])
    sink = _sink(db, broker=broker)
    # open_ts > 24 h zurueck
    old_open_ts = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat().replace("+00:00", "Z")
    opened = make_opened(open_ts=old_open_ts)
    sink.on_trade_opened(opened)

    with caplog.at_level(logging.WARNING):
        sink.on_trade_closed(make_closed())

    # WARNING emittiert (persistent-fail)
    warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert any("persistent fail" in r.getMessage() for r in warning_records)
    # Keine CRITICAL in diesem Pfad
    assert not any(r.levelno == logging.CRITICAL
                   for r in caplog.records)


def test_preclaim_idempotent_concurrent(make_opened, make_closed):
    """A5: zwei aufeinanderfolgende _on_trade_closed-Calls in der Backoff-Window
    lassen nur einen den resolve() ausfuehren."""
    db = FakeDB()
    broker = FakeBroker([])  # immer PnLUnavailable
    sink = _sink(db, broker=broker)
    opened = make_opened(open_ts=_now_iso())
    sink.on_trade_opened(opened)

    # Erster close: pre-claim + CRITICAL
    sink.on_trade_closed(make_closed())
    calls_after_first = list(db.calls)

    # Zweiter close innerhalb Backoff-Window: Backoff-Skip, kein pre-claim
    sink.on_trade_closed(make_closed())
    new_calls = [c for c in db.calls if c not in calls_after_first]

    # Nur update_trade_resolve_attempt-Count: genau 1 (nur der erste)
    preclaim_calls = [c for c in new_calls if c == "update_trade_resolve_attempt"]
    assert len(preclaim_calls) == 0  # zweiter wurde ueberhaupt nicht aufgerufen (backoff-skip)


def test_backoff_replay_reduces_critical_count(make_opened, make_closed, caplog):
    """A2: replay-test — 17 historische CRITICALs aus 2026-08-25/26/27 haetten
    mit Backoff nur 4-5 produziert (einer pro Stufe)."""
    from datetime import datetime, timezone, timedelta
    db = FakeDB()
    broker = FakeBroker([])  # immer PnLUnavailable
    sink = _sink(db, broker=broker)

    # Simuliere 4 Deals (genau die aus dem historischen Log: 17 CRITICALs ueber
    # 4 deals = 2-7 retries pro deal). Mit Backoff: ein attempt pro Stufe = 5.
    deal_ids = ["DIAAAAYCHTSTGA3", "DIAAAAYCN87PCAT", "DIAAAAYCPU28MA4", "DIAAAAYCT67N8AU"]
    fresh_open_ts = _now_iso()
    for did in deal_ids:
        sink.on_trade_opened(make_opened(deal_id=did, open_ts=fresh_open_ts))

    # 17 close-Calls (genau die Anzahl aus scheduler.log)
    caplog.clear()
    with caplog.at_level(logging.CRITICAL):
        for i in range(17):
            sink.on_trade_closed(make_closed(deal_id=deal_ids[i % 4]))
            # Native backoff (no override needed; per-deal_id last_resolve_attempt_utc
            # grows monotonically and gates the 15-min first-step).

    # Die ersten 4 Aufrufe (einer pro deal_id) loesen pre-claim + CRITICAL aus
    # (frisch, kein prior attempt). Alle weiteren 13 fallen in den Backoff-Skip.
    critical_count = sum(1 for r in caplog.records if r.levelno == logging.CRITICAL)
    assert critical_count == 4  # genau die 4 deal-ids, jeweils 1 CRITICAL beim ersten Attempt


def test_backoff_interval_follows_trade_age_not_ladder_top():
    """Phase 16 #37 (2026-10-15): the retry interval is the largest D1 step <= the
    trade's age. The pre-fix code waited the full 24 h after *every* failed attempt."""
    from datetime import datetime, timezone, timedelta
    from reward.recorder import _next_retry_in_s

    now = datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc)

    def iso(**kw):
        return (now - timedelta(**kw)).isoformat()

    # 3 h old trade, last attempt 61 min ago -> 1 h step passed -> retry now.
    assert _next_retry_in_s(iso(minutes=61), iso(hours=3), now) == 0
    # 3 h old trade, last attempt 20 min ago -> wait the remaining 40 min.
    assert _next_retry_in_s(iso(minutes=20), iso(hours=3), now) == 40 * 60
    # Fresh trade (10 min old) -> 15 min floor.
    assert _next_retry_in_s(iso(minutes=5), iso(minutes=10), now) == 10 * 60
    # 5 h old trade -> 4 h step.
    assert _next_retry_in_s(iso(hours=1), iso(hours=5), now) == 3 * 3600
    # 30 h old trade, last attempt 5 h ago -> 24 h cap, 19 h left.
    assert _next_retry_in_s(iso(hours=5), iso(hours=30), now) == 19 * 3600
    # No prior attempt -> proceed; unparseable open_ts -> 15 min floor.
    assert _next_retry_in_s(None, iso(hours=3), now) == 0
    assert _next_retry_in_s(iso(minutes=16), "garbage", now) == 0
