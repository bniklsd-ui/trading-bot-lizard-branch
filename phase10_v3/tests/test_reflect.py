"""S4 tests — reflect.py. Mock LLM only, no network."""

from __future__ import annotations

import logging

from abstain_lessons.models import AbstainReason, AbstainRecord, AbstainStage
from abstain_lessons.reflect import reflect_abstain, validate_abstain_lesson
from abstain_lessons.exceptions import AbstainLessonError

import pytest


def _record() -> AbstainRecord:
    return AbstainRecord.new(
        epic="IX.D.DAX.IFMM.IP",
        stage=AbstainStage.DEBATE,
        reason=AbstainReason.REASON_DEBATE_ABSTAIN,
        detail="judge said no",
    )


class _StubLLM:
    def __init__(self, response=None, exc=None):
        self._response = response
        self._exc = exc
        self.calls: list[tuple[str, float]] = []

    def complete(self, prompt: str, timeout_s: float) -> str:
        self.calls.append((prompt, timeout_s))
        if self._exc is not None:
            raise self._exc
        return self._response


def test_llm_none_returns_none_no_call():
    assert reflect_abstain(_record(), llm=None) is None


def test_happy_path_returns_validated_text():
    llm = _StubLLM(response="Halte Abstand bei niedrigem Momentum.")
    result = reflect_abstain(_record(), llm=llm)
    assert result == "Halte Abstand bei niedrigem Momentum."


def test_validator_reject_too_long_returns_none(caplog):
    llm = _StubLLM(response="x" * 301)
    with caplog.at_level(logging.CRITICAL):
        result = reflect_abstain(_record(), llm=llm)
    assert result is None
    assert any("reflect_abstain failed" in r.message for r in caplog.records)


def test_validator_reject_empty_returns_none(caplog):
    llm = _StubLLM(response="   ")
    with caplog.at_level(logging.CRITICAL):
        result = reflect_abstain(_record(), llm=llm)
    assert result is None
    assert any("reflect_abstain failed" in r.message for r in caplog.records)


def test_llm_exception_returns_none_never_raises(caplog):
    llm = _StubLLM(exc=RuntimeError("timeout"))
    with caplog.at_level(logging.CRITICAL):
        result = reflect_abstain(_record(), llm=llm)
    assert result is None
    assert any("reflect_abstain failed" in r.message for r in caplog.records)


def test_timeout_s_passed_through_unchanged():
    llm = _StubLLM(response="ok")
    reflect_abstain(_record(), llm=llm, timeout_s=7.5)
    assert llm.calls[0][1] == 7.5


def test_validate_abstain_lesson_strips_and_accepts():
    assert validate_abstain_lesson("  a lesson  ") == "a lesson"


def test_validate_abstain_lesson_rejects_multiline():
    with pytest.raises(AbstainLessonError):
        validate_abstain_lesson("line one\nline two")


def test_validate_abstain_lesson_rejects_301_chars():
    with pytest.raises(AbstainLessonError):
        validate_abstain_lesson("x" * 301)


def test_validate_abstain_lesson_accepts_exactly_300_chars():
    assert validate_abstain_lesson("x" * 300) == "x" * 300
