"""Step 9 tests — MarketContextWriter + ContextRecorder."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from market_context.writer import ContextRecorder, MarketContextWriter, _extract_bull_bear


def _writer(tmp_path) -> MarketContextWriter:
    w = MarketContextWriter(tmp_path / "test.sqlite")
    w.ensure_schema()
    return w


class _Turn:
    def __init__(self, agent, text):
        self.agent = agent
        self.text = text


class _DebateOutcome:
    def __init__(self, decision, confidence, rounds_used, transcript):
        self.decision = decision
        self.confidence = confidence
        self.rounds_used = rounds_used
        self.transcript = transcript


def test_extract_bull_bear_takes_the_last_turn_per_agent():
    transcript = (
        _Turn("BULL", "bull round 1"),
        _Turn("BEAR", "bear round 1"),
        _Turn("BULL", "bull round 2 (final)"),
        _Turn("BEAR", "bear round 2 (final)"),
        _Turn("JUDGE", "judge synthesis"),
    )
    bull, bear = _extract_bull_bear(_DebateOutcome("TRADE", 60, 2, transcript))
    assert bull == "bull round 2 (final)"
    assert bear == "bear round 2 (final)"


def test_extract_bull_bear_none_without_debate():
    assert _extract_bull_bear(None) == (None, None)


def test_extract_bull_bear_none_with_empty_transcript():
    assert _extract_bull_bear(_DebateOutcome("ABSTAIN", 0.0, 0, ())) == (None, None)


def test_on_decision_trade_inserts_linked_rows(tmp_path):
    writer = _writer(tmp_path)
    recorder = ContextRecorder(writer)
    outcome = _DebateOutcome("TRADE", 57.0, 1, (_Turn("BULL", "b"), _Turn("BEAR", "r")))
    recorder.on_decision(
        outcome="TRADE",
        epic="IX.D.DAX.IFMM.IP",
        candidate={"epic": "IX.D.DAX.IFMM.IP", "direction": "BUY"},
        spread_pct=0.02,
        now_utc=datetime(2026, 7, 17, 9, 0, tzinfo=timezone.utc),
        debate_outcome=outcome,
        gate_results_json='{"gates": "1,2,3,4,5 pass"}',
        veto_results_json='{"vetos": "pass"}',
        deal_id="DEAL123",
    )
    conn = sqlite3.connect(writer.db_path)
    ctx_rows = conn.execute("SELECT * FROM decision_context").fetchall()
    snap_rows = conn.execute("SELECT * FROM market_regime_snapshots").fetchall()
    assert len(ctx_rows) == 1
    assert len(snap_rows) == 1
    assert ctx_rows[0][11] == "TRADE"  # outcome column
    assert ctx_rows[0][12] == "DEAL123"  # deal_id column
    assert snap_rows[0][10] == ctx_rows[0][0]  # decision_context_id == context_id
    assert snap_rows[0][8] == "quote_only"  # data_source (no bars passed)


def test_on_decision_no_trade_links_abstain_record_id(tmp_path):
    writer = _writer(tmp_path)
    recorder = ContextRecorder(writer)
    recorder.on_decision(
        outcome="NO_TRADE",
        epic=None,
        abstain_record_id="abs-123",
    )
    conn = sqlite3.connect(writer.db_path)
    row = conn.execute("SELECT outcome, abstain_record_id FROM decision_context").fetchone()
    assert row == ("NO_TRADE", "abs-123")


def test_on_decision_abort_records_without_debate_or_deal(tmp_path):
    writer = _writer(tmp_path)
    recorder = ContextRecorder(writer)
    recorder.on_decision(outcome="ABORT", epic="IX.D.DAX.IFMM.IP")
    conn = sqlite3.connect(writer.db_path)
    row = conn.execute("SELECT outcome, deal_id, abstain_record_id FROM decision_context").fetchone()
    assert row == ("ABORT", None, None)


def test_on_decision_never_raises_on_writer_failure():
    class _RaisingWriter:
        def insert_decision_context(self, ctx):
            raise RuntimeError("db down")

        def insert_snapshot(self, snap):
            raise RuntimeError("db down")

    recorder = ContextRecorder(_RaisingWriter())  # type: ignore[arg-type]
    recorder.on_decision(outcome="NO_TRADE", epic=None)  # must not raise
