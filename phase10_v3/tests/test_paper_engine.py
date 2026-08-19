"""Step 10 tests — open_shadow_pair / resolve_paper_trade / PaperEngine / PaperTradeTracker."""

from __future__ import annotations

import dataclasses
from datetime import datetime, timezone

import pytest

from abstain_lessons.models import AbstainReason, AbstainRecord, AbstainStage
from abstain_lessons.paper import (
    PaperDebateCaller,
    PaperEngine,
    PaperExitReason,
    PaperTrade,
    PaperTradeTracker,
    PaperVariant,
    open_shadow_pair,
    resolve_paper_trade,
)
from abstain_lessons.paper_store import PaperTradeStore


class _Config:
    stop_distance_points = 30.0
    limit_distance_points = 45.0
    max_hold_minutes = 240


def _bar(ts, o, h, l, c):
    return {"timestamp": ts, "open": o, "high": h, "low": l, "close": c}


# --- open_shadow_pair -------------------------------------------------------


def test_open_shadow_pair_builds_both_sides():
    now = datetime(2026, 7, 17, 9, 0, tzinfo=timezone.utc)
    pair = open_shadow_pair("abs-1", "IX.D.DAX.IFMM.IP", {"bid": 17999.0, "ask": 18000.0}, _Config(), now)
    assert len(pair) == 2
    buy, sell = pair
    assert buy.variant is PaperVariant.SHADOW_BUY and buy.direction == "BUY" and buy.entry_level == 18000.0
    assert sell.variant is PaperVariant.SHADOW_SELL and sell.direction == "SELL" and sell.entry_level == 17999.0
    assert buy.stop_distance == 30.0 and buy.limit_distance == 45.0
    assert buy.time_stop_utc == sell.time_stop_utc == "2026-07-17T13:00:00.000Z"
    assert buy.abstain_record_id == sell.abstain_record_id == "abs-1"


# --- resolve_paper_trade -----------------------------------------------------


def _open_trade(direction="BUY", entry=18000.0, stop=30.0, limit=45.0, created="2026-07-17T09:00:00.000Z",
                 time_stop="2026-07-17T13:00:00.000Z"):
    return PaperTrade(
        paper_id="p1", abstain_record_id="abs-1", variant=PaperVariant.SHADOW_BUY,
        epic="X", direction=direction, created_utc=created, entry_level=entry,
        stop_distance=stop, limit_distance=limit, time_stop_utc=time_stop,
    )


def test_resolve_sl_first_buy():
    trade = _open_trade("BUY", entry=18000.0, stop=30.0, limit=45.0)
    bars = [_bar("2026-07-17T09:05:00.000Z", 18000, 18010, 17960, 17965)]  # low <= 17970 (SL)
    reason, level = resolve_paper_trade(trade, bars)
    assert reason is PaperExitReason.SL
    assert level == 17970.0


def test_resolve_tp_first_buy():
    trade = _open_trade("BUY", entry=18000.0, stop=30.0, limit=45.0)
    bars = [_bar("2026-07-17T09:05:00.000Z", 18000, 18050, 17990, 18040)]  # high >= 18045 (TP)
    reason, level = resolve_paper_trade(trade, bars)
    assert reason is PaperExitReason.TP
    assert level == 18045.0


def test_resolve_same_bar_sl_and_tp_is_conservative_sl():
    trade = _open_trade("BUY", entry=18000.0, stop=30.0, limit=45.0)
    # single bar touches both SL (17970) and TP (18045)
    bars = [_bar("2026-07-17T09:05:00.000Z", 18000, 18050, 17960, 18000)]
    reason, _ = resolve_paper_trade(trade, bars)
    assert reason is PaperExitReason.SL


def test_resolve_sell_direction_sign():
    trade = _open_trade("SELL", entry=18000.0, stop=30.0, limit=45.0)
    # SELL SL = entry + stop = 18030; touched when high >= 18030
    bars = [_bar("2026-07-17T09:05:00.000Z", 18000, 18040, 17990, 18010)]
    reason, level = resolve_paper_trade(trade, bars)
    assert reason is PaperExitReason.SL
    assert level == 18030.0


def test_resolve_time_stop_no_touch():
    trade = _open_trade("BUY", entry=18000.0, stop=30.0, limit=45.0,
                         time_stop="2026-07-17T10:00:00.000Z")
    bars = [
        _bar("2026-07-17T09:30:00.000Z", 18000, 18010, 17990, 18005),
        _bar("2026-07-17T10:00:00.000Z", 18005, 18008, 17998, 18002),  # at time-stop, no touch
    ]
    reason, level = resolve_paper_trade(trade, bars)
    assert reason is PaperExitReason.TIME_STOP
    assert level == 18002.0


def test_resolve_none_when_bars_dont_reach_time_stop():
    trade = _open_trade("BUY", entry=18000.0, stop=30.0, limit=45.0,
                         time_stop="2026-07-17T12:00:00.000Z")
    bars = [_bar("2026-07-17T09:05:00.000Z", 18000, 18010, 17990, 18005)]  # far short of time-stop
    assert resolve_paper_trade(trade, bars) is None


def test_resolve_none_with_no_bars():
    trade = _open_trade()
    assert resolve_paper_trade(trade, []) is None


def test_resolve_ignores_bars_before_created_utc():
    trade = _open_trade("BUY", entry=18000.0, stop=30.0, limit=45.0, created="2026-07-17T09:00:00.000Z")
    bars = [
        _bar("2026-07-17T08:00:00.000Z", 18000, 18100, 17000, 17500),  # before created_utc -> ignored
    ]
    assert resolve_paper_trade(trade, bars) is None


# --- PaperEngine --------------------------------------------------------------


def _record(reason=AbstainReason.REASON_DEBATE_ABSTAIN, epic="IX.D.DAX.IFMM.IP") -> AbstainRecord:
    return AbstainRecord.new(epic=epic, stage=AbstainStage.DEBATE, reason=reason)


class _RecordingStore:
    def __init__(self, council_count_today=0):
        self.inserted = []
        self._council_count_today = council_count_today

    def insert(self, trade):
        self.inserted.append(trade)

    def count_lessons_today(self, now_utc):
        return 0

    def count_today(self, variant, now_utc):
        return self._council_count_today


def test_paper_engine_opens_shadow_pair_on_debate_abstain():
    store = _RecordingStore()
    engine = PaperEngine(store, lambda epic: {"bid": 17999.0, "ask": 18000.0}, _Config(),
                         now_fn=lambda: datetime(2026, 7, 17, 9, 0, tzinfo=timezone.utc))
    record = _record()
    engine.on_debate_abstain({"outcome": "NO_TRADE"}, record)
    assert len(store.inserted) == 2
    assert {t.variant for t in store.inserted} == {PaperVariant.SHADOW_BUY, PaperVariant.SHADOW_SELL}
    assert all(t.abstain_record_id == record.record_id for t in store.inserted)


def test_paper_engine_ignores_non_debate_abstain_reason():
    store = _RecordingStore()
    engine = PaperEngine(store, lambda epic: {"bid": 1, "ask": 2}, _Config())
    engine.on_debate_abstain({}, _record(reason=AbstainReason.REASON_VETO_SPREAD))
    assert store.inserted == []


def test_paper_engine_ignores_record_without_epic():
    store = _RecordingStore()
    engine = PaperEngine(store, lambda epic: {"bid": 1, "ask": 2}, _Config())
    engine.on_debate_abstain({}, _record(epic=None))
    assert store.inserted == []


def test_paper_engine_never_raises_on_quote_fetch_failure():
    store = _RecordingStore()

    def _raising_fetch(epic):
        raise RuntimeError("boom")

    engine = PaperEngine(store, _raising_fetch, _Config())
    engine.on_debate_abstain({}, _record())  # must not raise
    assert store.inserted == []


def test_paper_engine_count_lessons_today_delegates_to_store():
    store = _RecordingStore()
    engine = PaperEngine(store, lambda epic: {}, _Config())
    assert engine.count_lessons_today("2026-07-17T00:00:00.000Z") == 0


# --- open_scheduled_pairs (Phase 11 H1) ---------------------------------------


def test_open_scheduled_pairs_opens_pair_per_epic():
    store = _RecordingStore()
    engine = PaperEngine(
        store, lambda epic: {"bid": 17999.0, "ask": 18000.0}, _Config(),
        now_fn=lambda: datetime(2026, 8, 1, 9, 0, tzinfo=timezone.utc),
    )
    engine.open_scheduled_pairs(["EPIC.A", "EPIC.B"])

    assert len(store.inserted) == 4
    by_epic = {}
    for t in store.inserted:
        by_epic.setdefault(t.epic, []).append(t)
    assert set(by_epic) == {"EPIC.A", "EPIC.B"}
    for epic, trades in by_epic.items():
        assert {t.variant for t in trades} == {PaperVariant.SHADOW_BUY, PaperVariant.SHADOW_SELL}
        assert all(t.abstain_record_id.startswith("sched:") for t in trades)
    # each epic's pair gets its own synthetic id, not shared across epics
    assert by_epic["EPIC.A"][0].abstain_record_id != by_epic["EPIC.B"][0].abstain_record_id


def test_epic_filter_blocks_on_debate_abstain_for_non_matching_epic():
    store = _RecordingStore()
    engine = PaperEngine(
        store, lambda epic: {"bid": 1.0, "ask": 2.0}, _Config(),
        epic_filter=lambda epic: epic == "ALLOWED",
    )
    engine.on_debate_abstain({}, _record(epic="BLOCKED"))
    assert store.inserted == []


def test_epic_filter_allows_matching_epic_on_debate_abstain():
    store = _RecordingStore()
    engine = PaperEngine(
        store, lambda epic: {"bid": 1.0, "ask": 2.0}, _Config(),
        epic_filter=lambda epic: epic == "ALLOWED",
    )
    engine.on_debate_abstain({}, _record(epic="ALLOWED"))
    assert len(store.inserted) == 2


def test_epic_filter_filters_open_scheduled_pairs_epic_list():
    store = _RecordingStore()
    engine = PaperEngine(
        store, lambda epic: {"bid": 1.0, "ask": 2.0}, _Config(),
        epic_filter=lambda epic: epic == "EPIC.A",
    )
    engine.open_scheduled_pairs(["EPIC.A", "EPIC.B"])
    epics = {t.epic for t in store.inserted}
    assert epics == {"EPIC.A"}


def test_epic_filter_none_default_is_bit_identical():
    store = _RecordingStore()
    engine = PaperEngine(store, lambda epic: {"bid": 1.0, "ask": 2.0}, _Config())
    engine.open_scheduled_pairs(["EPIC.A", "EPIC.B"])
    assert {t.epic for t in store.inserted} == {"EPIC.A", "EPIC.B"}


def test_open_scheduled_pairs_isolates_per_epic_failure():
    store = _RecordingStore()

    def _quote_fetch(epic):
        if epic == "BAD":
            raise RuntimeError("boom")
        return {"bid": 1.0, "ask": 2.0}

    engine = PaperEngine(store, _quote_fetch, _Config())
    engine.open_scheduled_pairs(["BAD", "GOOD"])  # must not raise

    assert len(store.inserted) == 2
    assert all(t.epic == "GOOD" for t in store.inserted)


def test_open_scheduled_pairs_empty_epics_is_noop():
    store = _RecordingStore()
    engine = PaperEngine(store, lambda epic: {"bid": 1.0, "ask": 2.0}, _Config())
    engine.open_scheduled_pairs([])
    assert store.inserted == []


def test_open_scheduled_pairs_skips_whole_tick_when_deadline_would_be_exceeded():
    store = _RecordingStore()
    engine = PaperEngine(
        store, lambda epic: {"bid": 1.0, "ask": 2.0}, _Config(),
        now_fn=lambda: datetime(2026, 8, 1, 14, 0, tzinfo=timezone.utc),
    )
    # _Config().max_hold_minutes == 240 -> prospective stop 18:00, past a 17:30 deadline.
    deadline = datetime(2026, 8, 1, 17, 30, tzinfo=timezone.utc)
    engine.open_scheduled_pairs(["EPIC.A", "EPIC.B"], deadline=deadline)
    assert store.inserted == []


def test_open_scheduled_pairs_proceeds_when_within_deadline():
    store = _RecordingStore()
    engine = PaperEngine(
        store, lambda epic: {"bid": 1.0, "ask": 2.0}, _Config(),
        now_fn=lambda: datetime(2026, 8, 1, 13, 0, tzinfo=timezone.utc),
    )
    # prospective stop 17:00, at/before the deadline -> proceeds.
    deadline = datetime(2026, 8, 1, 17, 30, tzinfo=timezone.utc)
    engine.open_scheduled_pairs(["EPIC.A"], deadline=deadline)
    assert len(store.inserted) == 2


def test_open_scheduled_pairs_no_deadline_is_unrestricted():
    """Default (``deadline=None``) stays exactly the earlier behaviour."""
    store = _RecordingStore()
    engine = PaperEngine(store, lambda epic: {"bid": 1.0, "ask": 2.0}, _Config())
    engine.open_scheduled_pairs(["EPIC.A"])
    assert len(store.inserted) == 2


# --- PaperDebateCaller (§10.3) --------------------------------------------------


class _StubLLMClient:
    def __init__(self, answer=None, raises=False):
        self._answer = answer
        self._raises = raises
        self.calls = 0

    def ask_candidate(self, system, user, schema):
        self.calls += 1
        if self._raises:
            raise RuntimeError("boom")
        return self._answer


def _stub_prompt_builder(digest):
    return "system", "user", {"type": "object"}


def test_request_pick_valid_returns_direction_and_confidence():
    llm = _StubLLMClient({"direction": "BUY", "confidence": 70, "rationale": "x"})
    caller = PaperDebateCaller(llm, _stub_prompt_builder)
    assert caller.request_pick({"epic": "X"}) == ("BUY", 70)


def test_request_pick_invalid_direction_returns_none():
    llm = _StubLLMClient({"direction": "HOLD", "confidence": 50, "rationale": "x"})
    caller = PaperDebateCaller(llm, _stub_prompt_builder)
    assert caller.request_pick({"epic": "X"}) is None


def test_request_pick_confidence_out_of_range_returns_none():
    llm = _StubLLMClient({"direction": "SELL", "confidence": 150, "rationale": "x"})
    caller = PaperDebateCaller(llm, _stub_prompt_builder)
    assert caller.request_pick({"epic": "X"}) is None


def test_request_pick_unparseable_confidence_returns_none():
    llm = _StubLLMClient({"direction": "SELL", "confidence": None, "rationale": "x"})
    caller = PaperDebateCaller(llm, _stub_prompt_builder)
    assert caller.request_pick({"epic": "X"}) is None


def test_request_pick_llm_exception_returns_none_never_raises():
    llm = _StubLLMClient(raises=True)
    caller = PaperDebateCaller(llm, _stub_prompt_builder)
    assert caller.request_pick({"epic": "X"}) is None  # must not raise


# --- PaperEngine + Council-Paper-Call integration -------------------------------


class _StubDebateCaller:
    def __init__(self, pick):
        self._pick = pick
        self.calls = 0

    def request_pick(self, candidate_digest):
        self.calls += 1
        return self._pick


def test_paper_engine_council_pick_adds_third_row_when_wired():
    store = _RecordingStore()
    caller = _StubDebateCaller(("BUY", 70))
    engine = PaperEngine(
        store, lambda epic: {"bid": 17999.0, "ask": 18000.0}, _Config(),
        debate_caller=caller, now_fn=lambda: datetime(2026, 7, 17, 9, 0, tzinfo=timezone.utc),
    )
    engine.on_debate_abstain({}, _record())

    assert caller.calls == 1
    assert len(store.inserted) == 3
    picks = [t for t in store.inserted if t.variant is PaperVariant.COUNCIL_PICK]
    assert len(picks) == 1
    assert picks[0].direction == "BUY"
    assert picks[0].entry_level == 18000.0  # ask, matching a BUY shadow entry
    assert picks[0].council_confidence == 70


def test_paper_engine_council_pick_sell_uses_bid():
    store = _RecordingStore()
    caller = _StubDebateCaller(("SELL", 55))
    engine = PaperEngine(
        store, lambda epic: {"bid": 17999.0, "ask": 18000.0}, _Config(), debate_caller=caller,
    )
    engine.on_debate_abstain({}, _record())
    pick = next(t for t in store.inserted if t.variant is PaperVariant.COUNCIL_PICK)
    assert pick.entry_level == 17999.0  # bid, matching a SELL shadow entry


def test_paper_engine_no_council_pick_when_debate_caller_none():
    """Default (``debate_caller=None``) stays bit-identical to Block B — only the
    shadow pair is inserted."""
    store = _RecordingStore()
    engine = PaperEngine(store, lambda epic: {"bid": 17999.0, "ask": 18000.0}, _Config())
    engine.on_debate_abstain({}, _record())
    assert len(store.inserted) == 2
    assert all(t.variant is not PaperVariant.COUNCIL_PICK for t in store.inserted)


def test_paper_engine_council_pick_skipped_when_request_pick_returns_none():
    store = _RecordingStore()
    caller = _StubDebateCaller(None)
    engine = PaperEngine(store, lambda epic: {"bid": 1.0, "ask": 2.0}, _Config(), debate_caller=caller)
    engine.on_debate_abstain({}, _record())
    assert len(store.inserted) == 2


def test_paper_engine_council_pick_respects_daily_cap():
    store = _RecordingStore(council_count_today=3)  # already at the default cap
    caller = _StubDebateCaller(("BUY", 70))
    engine = PaperEngine(store, lambda epic: {"bid": 1.0, "ask": 2.0}, _Config(), debate_caller=caller)
    engine.on_debate_abstain({}, _record())
    assert caller.calls == 0  # cap short-circuits before the LLM call
    assert len(store.inserted) == 2


def test_paper_engine_council_pick_custom_cap():
    store = _RecordingStore(council_count_today=1)
    caller = _StubDebateCaller(("BUY", 70))
    engine = PaperEngine(
        store, lambda epic: {"bid": 1.0, "ask": 2.0}, _Config(),
        debate_caller=caller, council_daily_cap=1,
    )
    engine.on_debate_abstain({}, _record())
    assert caller.calls == 0
    assert len(store.inserted) == 2


def test_paper_engine_council_pick_raising_never_crashes_cycle():
    store = _RecordingStore()

    class _RaisingCaller:
        def request_pick(self, candidate_digest):
            raise RuntimeError("boom")

    engine = PaperEngine(
        store, lambda epic: {"bid": 1.0, "ask": 2.0}, _Config(), debate_caller=_RaisingCaller(),
    )
    engine.on_debate_abstain({}, _record())  # must not raise
    # The shadow pair already committed before the council-pick step raised — the
    # outer guard swallows the exception but doesn't roll back prior inserts.
    assert len(store.inserted) == 2
    assert all(t.variant is not PaperVariant.COUNCIL_PICK for t in store.inserted)


# --- PaperTradeTracker ---------------------------------------------------------


@pytest.fixture
def paper_store(tmp_path):
    s = PaperTradeStore(tmp_path / "test.sqlite")
    s.ensure_schema()
    yield s
    s.close()


def test_tracker_resolves_due_trade_and_marks_resolved(paper_store):
    trade = PaperTrade.new(
        abstain_record_id="abs-1", variant=PaperVariant.SHADOW_BUY, epic="X",
        direction="BUY", entry_level=18000.0, stop_distance=30.0, limit_distance=45.0,
        time_stop_utc="2026-07-17T10:00:00.000Z",
    )
    # force created_utc into the past so it's due
    trade = dataclasses.replace(trade, created_utc="2026-07-17T09:00:00.000Z")
    paper_store.insert(trade)

    bars = [_bar("2026-07-17T09:05:00.000Z", 18000, 18050, 17990, 18040)]  # TP touch
    tracker = PaperTradeTracker(paper_store, bar_fetch=lambda epic: bars)
    tracker.tick(now_utc="2026-07-17T10:05:00.000Z")

    assert paper_store.open_trades() == []
    row = paper_store.conn.execute(
        "SELECT status, exit_reason FROM paper_trades WHERE paper_id = ?", (trade.paper_id,)
    ).fetchone()
    assert row[0] == "RESOLVED"
    assert row[1] == "TP"


def test_tracker_resolution_source_single_source(paper_store):
    """Phase 12 D11: resolution_source records which bar source(s) resolved the trade."""
    trade = PaperTrade.new(
        abstain_record_id="abs-1", variant=PaperVariant.SHADOW_BUY, epic="X",
        direction="BUY", entry_level=18000.0, stop_distance=30.0, limit_distance=45.0,
        time_stop_utc="2026-07-17T10:00:00.000Z",
    )
    trade = dataclasses.replace(trade, created_utc="2026-07-17T09:00:00.000Z")
    paper_store.insert(trade)
    bar = {**_bar("2026-07-17T09:05:00.000Z", 18000, 18050, 17990, 18040), "source": "yf"}
    tracker = PaperTradeTracker(paper_store, bar_fetch=lambda epic: [bar])
    tracker.tick(now_utc="2026-07-17T10:05:00.000Z")

    row = paper_store.conn.execute(
        "SELECT resolution_source FROM paper_trades WHERE paper_id = ?", (trade.paper_id,)
    ).fetchone()
    assert row[0] == "yf"


def test_tracker_resolution_source_mixed_sources_sorted_and_joined(paper_store):
    trade = PaperTrade.new(
        abstain_record_id="abs-1", variant=PaperVariant.SHADOW_BUY, epic="X",
        direction="BUY", entry_level=18000.0, stop_distance=30.0, limit_distance=45.0,
        time_stop_utc="2026-07-17T10:00:00.000Z",
    )
    trade = dataclasses.replace(trade, created_utc="2026-07-17T09:00:00.000Z")
    paper_store.insert(trade)
    bars = [
        {**_bar("2026-07-17T09:01:00.000Z", 18000, 18010, 17995, 18005), "source": "ig"},
        {**_bar("2026-07-17T09:05:00.000Z", 18000, 18050, 17990, 18040), "source": "yf"},  # TP touch
    ]
    tracker = PaperTradeTracker(paper_store, bar_fetch=lambda epic: bars)
    tracker.tick(now_utc="2026-07-17T10:05:00.000Z")

    row = paper_store.conn.execute(
        "SELECT resolution_source FROM paper_trades WHERE paper_id = ?", (trade.paper_id,)
    ).fetchone()
    assert row[0] == "ig+yf"  # sorted, +-joined


def test_tracker_resolution_source_none_when_bars_have_no_source_key(paper_store):
    trade = PaperTrade.new(
        abstain_record_id="abs-1", variant=PaperVariant.SHADOW_BUY, epic="X",
        direction="BUY", entry_level=18000.0, stop_distance=30.0, limit_distance=45.0,
        time_stop_utc="2026-07-17T10:00:00.000Z",
    )
    trade = dataclasses.replace(trade, created_utc="2026-07-17T09:00:00.000Z")
    paper_store.insert(trade)
    bars = [_bar("2026-07-17T09:05:00.000Z", 18000, 18050, 17990, 18040)]  # no "source" key
    tracker = PaperTradeTracker(paper_store, bar_fetch=lambda epic: bars)
    tracker.tick(now_utc="2026-07-17T10:05:00.000Z")

    row = paper_store.conn.execute(
        "SELECT resolution_source FROM paper_trades WHERE paper_id = ?", (trade.paper_id,)
    ).fetchone()
    assert row[0] is None  # honest — never guessed


def test_tick_charges_attempt_instead_of_expiring_on_empty_bars(paper_store):
    """P12.5 plan §3/U2: resolve_paper_trade returning None means "not enough bar data
    yet", not "no outcome" — a single empty-bars tick must charge the retry cap, not
    write the trade off immediately (this test replaces the old
    test_tracker_marks_expired_when_unresolvable, which asserted the pre-fix bug)."""
    trade = PaperTrade.new(
        abstain_record_id="abs-1", variant=PaperVariant.SHADOW_BUY, epic="X",
        direction="BUY", entry_level=18000.0, stop_distance=30.0, limit_distance=45.0,
        time_stop_utc="2026-07-17T10:00:00.000Z",
    )
    trade = dataclasses.replace(trade, created_utc="2026-07-17T09:00:00.000Z")
    paper_store.insert(trade)

    tracker = PaperTradeTracker(
        paper_store, bar_fetch=lambda epic: [], max_fetch_attempts=12  # no bars at all
    )
    tracker.tick(now_utc="2026-07-17T10:05:00.000Z")

    assert len(paper_store.open_trades()) == 1  # still OPEN, not written off
    assert tracker._fetch_attempts[trade.paper_id] == 1


def test_tick_expires_after_the_attempt_cap(paper_store):
    """The cap behavior itself is unchanged (P12.5 plan §3/U2) -- only the trigger
    (empty bars, not just a raised exception) is new."""
    trade = PaperTrade.new(
        abstain_record_id="abs-1", variant=PaperVariant.SHADOW_BUY, epic="X",
        direction="BUY", entry_level=18000.0, stop_distance=30.0, limit_distance=45.0,
        time_stop_utc="2026-07-17T10:00:00.000Z",
    )
    trade = dataclasses.replace(trade, created_utc="2026-07-17T09:00:00.000Z")
    paper_store.insert(trade)

    tracker = PaperTradeTracker(
        paper_store, bar_fetch=lambda epic: [], max_fetch_attempts=12
    )
    for _ in range(12):
        tracker.tick(now_utc="2026-07-17T10:05:00.000Z")

    row = paper_store.conn.execute(
        "SELECT status FROM paper_trades WHERE paper_id = ?", (trade.paper_id,)
    ).fetchone()
    assert row[0] == "EXPIRED_UNRESOLVED"


# --- Phase 13 §6 A3: window_ok-guard (F3: fabricated TIME_STOP) ----------------


def test_window_ok_none_default_is_bit_identical(paper_store):
    """Regression: pre-A3 callers (no `window_ok` kwarg) behave exactly as before.

    Same setup as `test_tracker_resolves_due_trade_and_marks_resolved` — proves the
    new parameter doesn't change a single line of the resolution path when no guard
    is supplied."""
    trade = PaperTrade.new(
        abstain_record_id="abs-1", variant=PaperVariant.SHADOW_BUY, epic="X",
        direction="BUY", entry_level=18000.0, stop_distance=30.0, limit_distance=45.0,
        time_stop_utc="2026-07-17T10:00:00.000Z",
    )
    trade = dataclasses.replace(trade, created_utc="2026-07-17T09:00:00.000Z")
    paper_store.insert(trade)

    bars = [_bar("2026-07-17T09:05:00.000Z", 18000, 18050, 17990, 18040)]  # TP touch
    tracker = PaperTradeTracker(paper_store, bar_fetch=lambda epic: bars)  # no window_ok
    tracker.tick(now_utc="2026-07-17T10:05:00.000Z")

    row = paper_store.conn.execute(
        "SELECT status, exit_reason FROM paper_trades WHERE paper_id = ?", (trade.paper_id,)
    ).fetchone()
    assert row[0] == "RESOLVED"
    assert row[1] == "TP"


def test_window_ok_false_charges_attempt_and_does_not_call_resolve(paper_store):
    """A guard that says "no" must (a) charge the retry cap, (b) leave the trade
    OPEN, and (c) never invoke resolve_paper_trade — proven by the exit_reason
    column staying NULL (resolve_paper_trade is the only writer of that field)."""
    trade = PaperTrade.new(
        abstain_record_id="abs-1", variant=PaperVariant.SHADOW_BUY, epic="X",
        direction="BUY", entry_level=18000.0, stop_distance=30.0, limit_distance=45.0,
        time_stop_utc="2026-07-17T10:00:00.000Z",
    )
    trade = dataclasses.replace(trade, created_utc="2026-07-17T09:00:00.000Z")
    paper_store.insert(trade)

    bars = [_bar("2026-07-17T09:05:00.000Z", 18000, 18050, 17990, 18040)]  # would be TP
    guard_calls: list[tuple[str, str, str]] = []

    def window_ok(epic, bars_arg, created_utc, time_stop_utc):
        guard_calls.append((epic, created_utc, time_stop_utc))
        return False

    tracker = PaperTradeTracker(
        paper_store, bar_fetch=lambda epic: bars, window_ok=window_ok, max_fetch_attempts=12,
    )
    tracker.tick(now_utc="2026-07-17T10:05:00.000Z")

    assert guard_calls == [(trade.epic, trade.created_utc, trade.time_stop_utc)]
    assert tracker._fetch_attempts[trade.paper_id] == 1
    row = paper_store.conn.execute(
        "SELECT status, exit_reason FROM paper_trades WHERE paper_id = ?", (trade.paper_id,)
    ).fetchone()
    assert row[0] == "OPEN"           # still OPEN, not written off
    assert row[1] is None              # resolve_paper_trade was never called


def test_window_ok_false_eventually_expires_at_cap(paper_store):
    """Same cap behavior as the empty-bars case (U2): a permanently uncovered window
    expires after `max_fetch_attempts` ticks, never producing a fabricated resolution."""
    trade = PaperTrade.new(
        abstain_record_id="abs-1", variant=PaperVariant.SHADOW_BUY, epic="X",
        direction="BUY", entry_level=18000.0, stop_distance=30.0, limit_distance=45.0,
        time_stop_utc="2026-07-17T10:00:00.000Z",
    )
    trade = dataclasses.replace(trade, created_utc="2026-07-17T09:00:00.000Z")
    paper_store.insert(trade)

    tracker = PaperTradeTracker(
        paper_store,
        bar_fetch=lambda epic: [],
        window_ok=lambda epic, bars, c, t: False,
        max_fetch_attempts=12,
    )
    for _ in range(12):
        tracker.tick(now_utc="2026-07-17T10:05:00.000Z")

    row = paper_store.conn.execute(
        "SELECT status, exit_reason FROM paper_trades WHERE paper_id = ?", (trade.paper_id,)
    ).fetchone()
    assert row[0] == "EXPIRED_UNRESOLVED"
    assert row[1] is None              # never produced a TIME_STOP


def test_window_ok_mitten_loch_blocks_fabricated_time_stop(paper_store):
    """F3 — the test that catches the Phase 12.5 failure mode.

    The bar set: two minutes of bars from 09:00 → 09:01, then a 20-minute gap, then
    bars from 09:22 → 10:00 covering the time-stop. From `resolve_paper_trade`'s
    perspective this is a *complete* window (SL never touches, first bar `>= time_stop`
    exists at 10:00) — so without the guard it would happily resolve as a fabricated
    TIME_STOP. With the guard, `assess_window` sees the 20-minute gap and returns
    covered=False with reason='gap' — the trade stays OPEN, counted as a failed
    attempt, with no fabricated exit_reason written.

    This is the most important test of Block A: it fails red on the pre-A3 code path
    and green on the A3 path."""
    trade = PaperTrade.new(
        abstain_record_id="abs-1", variant=PaperVariant.SHADOW_BUY, epic="IX.D.DAX.IFMM.IP",
        direction="BUY", entry_level=18000.0, stop_distance=30.0, limit_distance=45.0,
        time_stop_utc="2026-07-17T10:00:00.000Z",
    )
    trade = dataclasses.replace(trade, created_utc="2026-07-17T09:00:00.000Z")
    paper_store.insert(trade)

    # Window 09:00 → 10:00, 20-minute gap from 09:02 → 09:22 in the middle.
    # SL would be at 17970.0 (entry 18000 - stop 30) — never touched in the bars below.
    bars = (
        [_bar(f"2026-07-17T09:0{i}:00.000Z", 18000, 18001, 17995, 18000) for i in range(2)]
        + [_bar(f"2026-07-17T09:2{j}:00.000Z", 18000, 18001, 17995, 18000) for j in range(2, 10)]
        + [_bar("2026-07-17T09:30:00.000Z", 18000, 18001, 17995, 18000),
           _bar("2026-07-17T09:45:00.000Z", 18000, 18001, 17995, 18000),
           _bar("2026-07-17T10:00:00.000Z", 18000, 18001, 17995, 18000)]
    )

    # Sanity: without the guard, this set fabricates a TIME_STOP.
    pre_tracker = PaperTradeTracker(
        paper_store, bar_fetch=lambda epic: bars, max_fetch_attempts=12,
    )
    pre_tracker.tick(now_utc="2026-07-17T10:05:00.000Z")
    pre_row = paper_store.conn.execute(
        "SELECT status, exit_reason FROM paper_trades WHERE paper_id = ?", (trade.paper_id,)
    ).fetchone()
    assert pre_row[0] == "RESOLVED" and pre_row[1] == "TIME_STOP", \
        "precondition: pre-A3 code WOULD fabricate a TIME_STOP here"

    # Restart with a fresh trade + the real `window_ok` closure (via assess_window).
    from data_foundation.coverage import assess_window

    paper_store.conn.execute("DELETE FROM paper_trades WHERE paper_id = ?", (trade.paper_id,))
    paper_store.conn.commit()
    paper_store.insert(trade)

    def window_ok(epic, bars_arg, created_utc, time_stop_utc):
        verdict = assess_window(
            [b.get("timestamp", "") for b in bars_arg],
            created_utc, time_stop_utc, 1,
        )
        return verdict.covered

    guarded_tracker = PaperTradeTracker(
        paper_store, bar_fetch=lambda epic: bars, window_ok=window_ok, max_fetch_attempts=12,
    )
    guarded_tracker.tick(now_utc="2026-07-17T10:05:00.000Z")

    guarded_row = paper_store.conn.execute(
        "SELECT status, exit_reason FROM paper_trades WHERE paper_id = ?", (trade.paper_id,)
    ).fetchone()
    assert guarded_row[0] == "OPEN", "guarded: gap in the middle blocks fabricated TIME_STOP"
    assert guarded_row[1] is None
    assert guarded_tracker._fetch_attempts[trade.paper_id] == 1


# --- Phase 13 §6 A7.5: Tracker-Stale-Mini-Step ------------------------------


def test_tracker_stale_charges_attempt_and_does_not_call_resolve(paper_store):
    """A7.5: if the newest bar in the trade window is older than
    _TRACKER_STALE_TOLERANCE_MIN, the tracker treats the whole window as stale
    and charges a failed attempt — instead of resolving on a perfectly-shaped
    but uniformly-outdated bar set. Sits **before** ``window_ok`` (cheaper,
    catches a strictly larger case)."""
    trade = PaperTrade.new(
        abstain_record_id="abs-1", variant=PaperVariant.SHADOW_BUY, epic="X",
        direction="BUY", entry_level=18000.0, stop_distance=30.0, limit_distance=45.0,
        time_stop_utc="2026-07-17T10:00:00.000Z",
    )
    trade = dataclasses.replace(trade, created_utc="2026-07-17T09:00:00.000Z")
    paper_store.insert(trade)

    # All bars are 3 hours old relative to `now` — well past the 120-min
    # tracker-stale tolerance, even though the window itself is perfectly
    # dense (no gap, no coverage shortfall).
    now = "2026-07-17T13:00:00.000Z"
    bars = [
        _bar(f"2026-07-17T09:0{m}:00.000Z", 18000, 18001, 17995, 18000) for m in range(10)
    ]
    tracker = PaperTradeTracker(paper_store, bar_fetch=lambda epic: bars, max_fetch_attempts=12)
    tracker.tick(now_utc=now)

    row = paper_store.conn.execute(
        "SELECT status, exit_reason FROM paper_trades WHERE paper_id = ?", (trade.paper_id,)
    ).fetchone()
    assert row[0] == "OPEN", "stale-only window must not resolve"
    assert row[1] is None, "resolve_paper_trade was not called (no exit_reason written)"
    assert tracker._fetch_attempts[trade.paper_id] == 1


def test_tracker_ignores_not_yet_due_trades(paper_store):
    trade = PaperTrade.new(
        abstain_record_id="abs-1", variant=PaperVariant.SHADOW_BUY, epic="X",
        direction="BUY", entry_level=18000.0, stop_distance=30.0, limit_distance=45.0,
        time_stop_utc="2099-01-01T00:00:00.000Z",  # far future
    )
    paper_store.insert(trade)

    calls = []
    tracker = PaperTradeTracker(paper_store, bar_fetch=lambda epic: calls.append(epic) or [])
    tracker.tick(now_utc="2026-07-17T10:05:00.000Z")

    assert calls == []
    assert len(paper_store.open_trades()) == 1


def test_tracker_is_idempotent_on_double_tick(paper_store):
    trade = PaperTrade.new(
        abstain_record_id="abs-1", variant=PaperVariant.SHADOW_BUY, epic="X",
        direction="BUY", entry_level=18000.0, stop_distance=30.0, limit_distance=45.0,
        time_stop_utc="2026-07-17T10:00:00.000Z",
    )
    trade = dataclasses.replace(trade, created_utc="2026-07-17T09:00:00.000Z")
    paper_store.insert(trade)

    bars = [_bar("2026-07-17T09:05:00.000Z", 18000, 18050, 17990, 18040)]
    calls = []
    tracker = PaperTradeTracker(paper_store, bar_fetch=lambda epic: calls.append(epic) or bars)
    tracker.tick(now_utc="2026-07-17T10:05:00.000Z")
    tracker.tick(now_utc="2026-07-17T10:10:00.000Z")

    assert len(calls) == 1  # second tick found no OPEN trades left for this epic


def test_tracker_reflects_once_per_resolved_pair(paper_store):
    now_stop = "2026-07-17T10:00:00.000Z"
    buy = PaperTrade.new(
        abstain_record_id="abs-1", variant=PaperVariant.SHADOW_BUY, epic="X",
        direction="BUY", entry_level=18000.0, stop_distance=30.0, limit_distance=45.0,
        time_stop_utc=now_stop,
    )
    sell = PaperTrade.new(
        abstain_record_id="abs-1", variant=PaperVariant.SHADOW_SELL, epic="X",
        direction="SELL", entry_level=17999.0, stop_distance=30.0, limit_distance=45.0,
        time_stop_utc=now_stop,
    )
    buy = dataclasses.replace(buy, created_utc="2026-07-17T09:00:00.000Z")
    sell = dataclasses.replace(sell, created_utc="2026-07-17T09:00:00.000Z")
    paper_store.insert(buy)
    paper_store.insert(sell)

    # BUY SL=17970 (low touch), SELL SL=18029 (high touch) -- one bar hits both, neither TP
    bars = [_bar("2026-07-17T09:05:00.000Z", 18000, 18030, 17960, 18000)]

    class _StubLLM:
        def __init__(self):
            self.calls = 0

        def complete(self, prompt, timeout_s):
            self.calls += 1
            return "Beide Seiten verloren -> Abstain war richtig."

    llm = _StubLLM()
    tracker = PaperTradeTracker(paper_store, bar_fetch=lambda epic: bars, llm=llm)
    tracker.tick(now_utc="2026-07-17T10:05:00.000Z")

    assert llm.calls == 1  # one call for the pair, not two
    lessons = paper_store.recent_lessons(limit=5)
    assert lessons == [
        "Beide Seiten verloren -> Abstain war richtig.",
        "Beide Seiten verloren -> Abstain war richtig.",
    ]


def test_tracker_respects_reflect_cap(paper_store):
    trade = PaperTrade.new(
        abstain_record_id="abs-1", variant=PaperVariant.SHADOW_BUY, epic="X",
        direction="BUY", entry_level=18000.0, stop_distance=30.0, limit_distance=45.0,
        time_stop_utc="2026-07-17T10:00:00.000Z",
    )
    trade = dataclasses.replace(trade, created_utc="2026-07-17T09:00:00.000Z")
    paper_store.insert(trade)
    bars = [_bar("2026-07-17T09:05:00.000Z", 18000, 18010, 17960, 17965)]  # SL

    class _StubLLM:
        def __init__(self):
            self.calls = 0

        def complete(self, prompt, timeout_s):
            self.calls += 1
            return "lesson"

    llm = _StubLLM()
    tracker = PaperTradeTracker(
        paper_store, bar_fetch=lambda epic: bars, llm=llm, reflect_cap_check=lambda: False,
    )
    tracker.tick(now_utc="2026-07-17T10:05:00.000Z")

    assert llm.calls == 0
    assert paper_store.recent_lessons(limit=5) == []


def test_tracker_bar_fetch_failure_isolated_per_epic(paper_store):
    trade = PaperTrade.new(
        abstain_record_id="abs-1", variant=PaperVariant.SHADOW_BUY, epic="X",
        direction="BUY", entry_level=18000.0, stop_distance=30.0, limit_distance=45.0,
        time_stop_utc="2026-07-17T10:00:00.000Z",
    )
    trade = dataclasses.replace(trade, created_utc="2026-07-17T09:00:00.000Z")
    paper_store.insert(trade)

    def _raising_fetch(epic):
        raise RuntimeError("get_ohlcv boom")

    tracker = PaperTradeTracker(paper_store, bar_fetch=_raising_fetch)
    tracker.tick(now_utc="2026-07-17T10:05:00.000Z")  # must not raise

    assert len(paper_store.open_trades()) == 1  # left OPEN, untouched


# --- 2026-08-08: staleness + budget guards (DATA_WEEK_REVIEW_2026-08-07 addendum) -----


def _stale_trade(epic="X"):
    """A trade created two days before the tick — resolve_paper_trade would happily
    match it against unrelated fresh bars, because it filters on `>= created_utc` only."""
    trade = PaperTrade.new(
        abstain_record_id="abs-1", variant=PaperVariant.SHADOW_BUY, epic=epic,
        direction="BUY", entry_level=18000.0, stop_distance=30.0, limit_distance=45.0,
        time_stop_utc="2026-07-15T14:00:00.000Z",
    )
    return dataclasses.replace(trade, created_utc="2026-07-15T10:00:00.000Z")


def test_tracker_expires_stale_trade_without_fetching(paper_store):
    paper_store.insert(_stale_trade())

    calls = []
    # bars that WOULD produce a (fabricated) SL touch if they were ever consulted
    bars = [_bar("2026-07-17T09:05:00.000Z", 18000, 18010, 17900, 17950)]
    tracker = PaperTradeTracker(
        paper_store,
        bar_fetch=lambda epic: calls.append(epic) or bars,
        stale_after_minutes=300,
    )
    tracker.tick(now_utc="2026-07-17T10:05:00.000Z")

    assert calls == []  # the whole point: zero API cost for an unresolvable trade
    row = paper_store.conn.execute("SELECT status, exit_reason FROM paper_trades").fetchone()
    assert row[0] == "EXPIRED_UNRESOLVED"
    assert row[1] is None  # never fabricated an exit


def test_tracker_still_resolves_fresh_trade_with_staleness_enabled(paper_store):
    trade = PaperTrade.new(
        abstain_record_id="abs-1", variant=PaperVariant.SHADOW_BUY, epic="X",
        direction="BUY", entry_level=18000.0, stop_distance=30.0, limit_distance=45.0,
        time_stop_utc="2026-07-17T10:00:00.000Z",
    )
    trade = dataclasses.replace(trade, created_utc="2026-07-17T09:00:00.000Z")
    paper_store.insert(trade)

    bars = [_bar("2026-07-17T09:05:00.000Z", 18000, 18050, 17990, 18040)]  # TP touch
    tracker = PaperTradeTracker(
        paper_store, bar_fetch=lambda epic: bars, stale_after_minutes=300
    )
    tracker.tick(now_utc="2026-07-17T10:05:00.000Z")

    row = paper_store.conn.execute("SELECT status, exit_reason FROM paper_trades").fetchone()
    assert (row[0], row[1]) == ("RESOLVED", "TP")


def test_tracker_skips_whole_tick_when_budget_exhausted(paper_store):
    trade = PaperTrade.new(
        abstain_record_id="abs-1", variant=PaperVariant.SHADOW_BUY, epic="X",
        direction="BUY", entry_level=18000.0, stop_distance=30.0, limit_distance=45.0,
        time_stop_utc="2026-07-17T10:00:00.000Z",
    )
    trade = dataclasses.replace(trade, created_utc="2026-07-17T09:00:00.000Z")
    paper_store.insert(trade)

    calls = []
    tracker = PaperTradeTracker(
        paper_store,
        bar_fetch=lambda epic: calls.append(epic) or [],
        budget_ok=lambda: False,
    )
    tracker.tick(now_utc="2026-07-17T10:05:00.000Z")

    assert calls == []
    # left OPEN, not expired: a budget stand-down must not destroy a still-resolvable
    # trade the way the staleness cut deliberately does.
    assert len(paper_store.open_trades()) == 1


def test_tracker_gives_up_on_a_trade_after_max_fetch_attempts(paper_store):
    """A due trade must not be re-fetched forever: one successful fetch always
    terminates it, so a bounded number of *failed* fetches bounds the retries."""
    trade = PaperTrade.new(
        abstain_record_id="abs-1", variant=PaperVariant.SHADOW_BUY, epic="X",
        direction="BUY", entry_level=18000.0, stop_distance=30.0, limit_distance=45.0,
        time_stop_utc="2026-07-17T10:00:00.000Z",
    )
    trade = dataclasses.replace(trade, created_utc="2026-07-17T09:00:00.000Z")
    paper_store.insert(trade)

    calls = []

    def _raising_fetch(epic):
        calls.append(epic)
        raise RuntimeError("get_ohlcv not ok")

    tracker = PaperTradeTracker(
        paper_store, bar_fetch=_raising_fetch, max_fetch_attempts=3
    )
    for _ in range(10):  # ten ticks, but only three may reach the broker
        tracker.tick(now_utc="2026-07-17T10:05:00.000Z")

    assert len(calls) == 3
    row = paper_store.conn.execute("SELECT status FROM paper_trades").fetchone()
    assert row[0] == "EXPIRED_UNRESOLVED"


def test_budget_standdown_does_not_consume_fetch_attempts(paper_store):
    """No call was made, so no attempt was spent — otherwise a long outage would burn
    every trade's budget without ever asking the broker."""
    trade = PaperTrade.new(
        abstain_record_id="abs-1", variant=PaperVariant.SHADOW_BUY, epic="X",
        direction="BUY", entry_level=18000.0, stop_distance=30.0, limit_distance=45.0,
        time_stop_utc="2026-07-17T10:00:00.000Z",
    )
    trade = dataclasses.replace(trade, created_utc="2026-07-17T09:00:00.000Z")
    paper_store.insert(trade)

    allowed = False
    bars = [_bar("2026-07-17T09:05:00.000Z", 18000, 18050, 17990, 18040)]  # TP touch
    tracker = PaperTradeTracker(
        paper_store, bar_fetch=lambda epic: bars,
        budget_ok=lambda: allowed, max_fetch_attempts=3,
    )
    for _ in range(5):
        tracker.tick(now_utc="2026-07-17T10:05:00.000Z")
    assert len(paper_store.open_trades()) == 1  # survived the stand-down intact

    allowed = True
    tracker.tick(now_utc="2026-07-17T10:05:00.000Z")
    row = paper_store.conn.execute("SELECT status, exit_reason FROM paper_trades").fetchone()
    assert (row[0], row[1]) == ("RESOLVED", "TP")
