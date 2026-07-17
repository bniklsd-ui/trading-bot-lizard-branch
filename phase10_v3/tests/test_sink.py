"""S5 tests — AbstainLessonSink."""

from __future__ import annotations

from abstain_lessons.models import AbstainStage
from abstain_lessons.sink import AbstainLessonSink
from abstain_lessons.store import AbstainStore


class _StubLLM:
    def __init__(self, response="a lesson"):
        self._response = response
        self.calls = 0

    def complete(self, prompt: str, timeout_s: float) -> str:
        self.calls += 1
        return self._response


class _RaisingStore:
    def insert(self, record):
        raise RuntimeError("db is down")


def _store(tmp_path) -> AbstainStore:
    s = AbstainStore(tmp_path / "test.sqlite")
    s.ensure_schema()
    return s


def test_on_no_trade_classifies_and_persists(tmp_path):
    store = _store(tmp_path)
    sink = AbstainLessonSink(store)
    sink.on_no_trade({"veto": "spread", "epic": "IX.D.DAX.IFMM.IP"})
    recent = store.recent(limit=10)
    assert len(recent) == 1
    assert recent[0].stage is AbstainStage.VETO


def test_on_no_trade_returns_the_persisted_record_id(tmp_path):
    """Block-B's context_recorder needs the real record_id to link decision_context."""
    store = _store(tmp_path)
    sink = AbstainLessonSink(store)
    record_id = sink.on_no_trade({"veto": "spread"})
    assert record_id is not None
    assert store.recent(limit=10)[0].record_id == record_id


def test_on_no_trade_returns_none_on_failure():
    sink = AbstainLessonSink(_RaisingStore())  # type: ignore[arg-type]
    assert sink.on_no_trade({"veto": "spread"}) is None


def test_reflect_runs_for_matching_stage_with_llm(tmp_path):
    store = _store(tmp_path)
    llm = _StubLLM(response="Warte auf klareres Momentum.")
    sink = AbstainLessonSink(store, llm=llm)
    sink.on_no_trade({"debate_decision": "ABSTAIN"})
    recent = store.recent(limit=10)
    assert recent[0].lesson == "Warte auf klareres Momentum."
    assert llm.calls == 1


def test_reflect_skipped_for_non_matching_stage(tmp_path):
    store = _store(tmp_path)
    llm = _StubLLM()
    sink = AbstainLessonSink(store, llm=llm)  # default reflect_stages = {DEBATE}
    sink.on_no_trade({"veto": "spread"})
    assert llm.calls == 0
    assert store.recent(limit=10)[0].lesson is None


def test_reflect_skipped_when_llm_none(tmp_path):
    store = _store(tmp_path)
    sink = AbstainLessonSink(store, llm=None)
    sink.on_no_trade({"debate_decision": "ABSTAIN"})
    assert store.recent(limit=10)[0].lesson is None


def test_reflect_daily_cap_enforced(tmp_path):
    store = _store(tmp_path)
    llm = _StubLLM()
    sink = AbstainLessonSink(store, llm=llm, reflect_daily_cap=1)
    sink.on_no_trade({"debate_decision": "ABSTAIN"})
    sink.on_no_trade({"debate_decision": "ABSTAIN"})
    assert llm.calls == 1  # second call is over the cap


def test_sink_exception_never_reaches_caller():
    sink = AbstainLessonSink(_RaisingStore())  # type: ignore[arg-type]
    sink.on_no_trade({"veto": "spread"})  # must not raise


def test_no_paper_trigger_when_paper_engine_none(tmp_path):
    store = _store(tmp_path)
    sink = AbstainLessonSink(store, paper_engine=None)
    sink.on_no_trade({"debate_decision": "ABSTAIN"})  # must not raise, no paper call


def test_paper_trigger_called_on_debate_abstain(tmp_path):
    store = _store(tmp_path)

    class _FakePaperEngine:
        def __init__(self):
            self.calls = []

        def on_debate_abstain(self, cycle_outcome, record):
            self.calls.append((cycle_outcome, record))

        def count_lessons_today(self, now_utc):
            return 0

    paper_engine = _FakePaperEngine()
    sink = AbstainLessonSink(store, paper_engine=paper_engine)
    sink.on_no_trade({"debate_decision": "ABSTAIN"})
    assert len(paper_engine.calls) == 1


def test_no_paper_trigger_for_non_debate_reason(tmp_path):
    store = _store(tmp_path)

    class _FakePaperEngine:
        def __init__(self):
            self.calls = []

        def on_debate_abstain(self, cycle_outcome, record):
            self.calls.append((cycle_outcome, record))

        def count_lessons_today(self, now_utc):
            return 0

    paper_engine = _FakePaperEngine()
    sink = AbstainLessonSink(store, paper_engine=paper_engine)
    sink.on_no_trade({"veto": "spread"})
    assert paper_engine.calls == []
