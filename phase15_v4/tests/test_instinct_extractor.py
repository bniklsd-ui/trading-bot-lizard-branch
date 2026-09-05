"""Tests for ``phase15_v4/instinct/extractor.py`` (Plan §6 C2 + §1 P9).

Pins:
- Best-effort contract (Decision E/J-mirror): **never raises** — every failure
  path returns ``InstinctExtractionResult(ok=False, error=...)``.
- Schema-conformant LLM output is parsed verbatim into ``Instinct`` rows.
- Malformed entries (bad domain, bad confidence, non-int list elements, etc.)
  are caught by the try/except and surfaced as ``ok=False``.
- The prompt builder is pure (no I/O, no clock, no LLM).
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from typing import Any

import pytest

_REPO_ROOT = "/home/trading-bot/trading-bot"
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from instinct.extractor import (  # noqa: E402
    InstinctExtractionResult,
    SingleShotInstinctExtractor,
    _build_instinct_prompt,
)


# ---------------------------------------------------------------------------
# Fake LLM client — duck-typed ``_LLMClientLike`` mirror of ``phase7_reward``.
# ---------------------------------------------------------------------------


@dataclass
class _FakeLLM:
    """A controllable stand-in for ``research.LLMClient``.

    Each ``ask_candidate`` call records its arguments on ``self.calls`` and
    returns whatever ``self.response`` / ``self.response_fn`` says. Defaults
    to a valid empty extraction.
    """

    response: Any = field(
        default_factory=lambda: {"instincts": []}
    )
    response_fn: Any = None  # callable(system, user, schema) -> payload
    model: str = "fake-instinct-model"
    max_tokens: int = 800
    temperature: float = 0.2
    last_usage: dict[str, Any] | None = None
    calls: list[tuple[str, str, dict]] = field(default_factory=list)

    def ask_candidate(
        self, system: str, user: str, json_schema: dict,
    ) -> dict:
        self.calls.append((system, user, json_schema))
        if self.response_fn is not None:
            return self.response_fn(system, user, json_schema)
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


# ---------------------------------------------------------------------------
# Prompt builder — pure.
# ---------------------------------------------------------------------------


def test_prompt_builder_is_pure() -> None:
    """``_build_instinct_prompt`` does no I/O, no clock, no LLM — same input,
    same output, every call."""
    lessons = [{"lesson_text": "Tight spread helped"}]
    rewards = [{"win_loss": "WIN", "outcome_score_delta": 1.5}]

    s1, u1, sc1 = _build_instinct_prompt(lessons, rewards)
    s2, u2, sc2 = _build_instinct_prompt(lessons, rewards)
    assert (s1, u1) == (s2, u2)
    assert sc1 == sc2


def test_prompt_builder_schema_pins_domain_enum() -> None:
    """The JSON schema constrains ``domain`` to the four pinned values (matches
    the SQL CHECK constraint)."""
    _, _, schema = _build_instinct_prompt([], [])
    domain_schema = schema["properties"]["instincts"]["items"]["properties"]["domain"]
    # Sorted by JSON-schema tooling or hard-coded — either way it must be a subset.
    assert set(domain_schema["enum"]) == set(["entry", "exit", "sizing", "timing"])


def test_prompt_builder_schema_requires_all_fields() -> None:
    """All schema fields are required — matches Concept §7b exactly."""
    _, _, schema = _build_instinct_prompt([], [])
    item_schema = schema["properties"]["instincts"]["items"]
    assert set(item_schema["required"]) == {
        "trigger", "domain", "confidence",
        "evidence_trade_ids", "contradictions_trade_ids",
    }


def test_prompt_builder_schema_max_5_instincts() -> None:
    """The schema caps one call at 5 instincts — mirrors Phase 7's lesson cap."""
    _, _, schema = _build_instinct_prompt([], [])
    assert schema["properties"]["instincts"]["maxItems"] == 5


def test_prompt_builder_user_carries_lesson_text() -> None:
    """The user prompt includes the lesson text verbatim — the LLM sees the input."""
    _, user, _ = _build_instinct_prompt(
        [{"lesson_text": "Avoid trading on Mondays"}], [],
    )
    assert "Avoid trading on Mondays" in user


def test_prompt_builder_system_draws_ai_boundary() -> None:
    """The system prompt forbids scoring / deciding / promoting / validating —
    the four anti-patterns the validator + promoter are responsible for."""
    system, _, _ = _build_instinct_prompt([], [])
    for forbidden_phrase in (
        "KEINE Score-",
        "Risiko- oder Positions-Entscheidung",
        "Du promotest NICHTS",
        "Du validierst NICHTS",
    ):
        assert forbidden_phrase in system


# ---------------------------------------------------------------------------
# Single-shot extractor — happy path.
# ---------------------------------------------------------------------------


def test_extractor_returns_empty_list_on_valid_empty_payload() -> None:
    """Valid payload with ``instincts: []`` returns ``ok=True``, no rows."""
    ext = SingleShotInstinctExtractor(_FakeLLM())
    out = ext.extract([], [])
    assert isinstance(out, InstinctExtractionResult)
    assert out.ok is True
    assert out.instincts == []
    assert out.error is None


def test_extractor_parses_one_instinct() -> None:
    """A well-formed payload returns one ``Instinct`` with the expected fields."""
    payload = {
        "instincts": [
            {
                "trigger": "Tight-spread entries beat wide-spread ones",
                "domain": "entry",
                "confidence": 0.7,
                "evidence_trade_ids": [1, 2, 3],
                "contradictions_trade_ids": [],
            }
        ]
    }
    ext = SingleShotInstinctExtractor(_FakeLLM(response=payload))
    out = ext.extract([], [])
    assert out.ok is True
    assert len(out.instincts) == 1
    i = out.instincts[0]
    assert i.trigger == "Tight-spread entries beat wide-spread ones"
    assert i.domain == "entry"
    assert i.confidence == 0.7
    assert i.evidence_trade_ids == (1, 2, 3)
    assert i.contradictions_trade_ids == ()


def test_extractor_accepts_confidence_null() -> None:
    """``confidence=None`` is valid — the validator treats it as unpromotable."""
    payload = {
        "instincts": [
            {
                "trigger": "t", "domain": "exit",
                "confidence": None,
                "evidence_trade_ids": [], "contradictions_trade_ids": [],
            }
        ]
    }
    ext = SingleShotInstinctExtractor(_FakeLLM(response=payload))
    out = ext.extract([], [])
    assert out.ok is True
    assert out.instincts[0].confidence is None


def test_extractor_accepts_string_payload_via_json_decode() -> None:
    """The fence-strip fallback path: payload delivered as a JSON-encoded string."""
    payload_dict = {
        "instincts": [
            {
                "trigger": "t", "domain": "timing",
                "confidence": 0.5,
                "evidence_trade_ids": [7], "contradictions_trade_ids": [],
            }
        ]
    }
    ext = SingleShotInstinctExtractor(
        _FakeLLM(response=json.dumps(payload_dict))
    )
    out = ext.extract([], [])
    assert out.ok is True
    assert out.instincts[0].domain == "timing"
    assert out.instincts[0].evidence_trade_ids == (7,)


def test_extractor_strips_whitespace_around_trigger() -> None:
    """Leading/trailing whitespace around the trigger is stripped."""
    payload = {
        "instincts": [
            {
                "trigger": "  trimmed trigger  ", "domain": "entry",
                "confidence": None,
                "evidence_trade_ids": [], "contradictions_trade_ids": [],
            }
        ]
    }
    ext = SingleShotInstinctExtractor(_FakeLLM(response=payload))
    out = ext.extract([], [])
    assert out.ok is True
    assert out.instincts[0].trigger == "trimmed trigger"


# ---------------------------------------------------------------------------
# Single-shot extractor — best-effort: every failure yields ``ok=False``,
# never raises (Decision E/J-mirror).
# ---------------------------------------------------------------------------


def test_extractor_never_raises_on_llm_runtime_error() -> None:
    """LLM raises ``RuntimeError`` → ``ok=False``, error captured, no re-raise."""
    ext = SingleShotInstinctExtractor(
        _FakeLLM(response=RuntimeError("network down"))
    )
    out = ext.extract([], [])
    assert out.ok is False
    assert out.instincts == []
    assert "network down" in (out.error or "")


def test_extractor_never_raises_on_invalid_json_string() -> None:
    """LLM returns a malformed JSON string → ``ok=False``, no re-raise."""
    ext = SingleShotInstinctExtractor(_FakeLLM(response="not json"))
    out = ext.extract([], [])
    assert out.ok is False
    assert out.error is not None


def test_extractor_never_raises_on_missing_instincts_key() -> None:
    """LLM returns a dict without ``instincts`` → ``ok=False``, no re-raise."""
    ext = SingleShotInstinctExtractor(_FakeLLM(response={"other": []}))
    out = ext.extract([], [])
    assert out.ok is False


def test_extractor_never_raises_on_invalid_domain() -> None:
    """LLM returns an instinct with a bad domain → ``ok=False``, no re-raise."""
    payload = {
        "instincts": [
            {
                "trigger": "t", "domain": "trade",  # invalid
                "confidence": 0.5,
                "evidence_trade_ids": [], "contradictions_trade_ids": [],
            }
        ]
    }
    ext = SingleShotInstinctExtractor(_FakeLLM(response=payload))
    out = ext.extract([], [])
    assert out.ok is False
    assert "domain" in (out.error or "").lower()


def test_extractor_never_raises_on_non_int_evidence() -> None:
    """LLM returns a non-int in ``evidence_trade_ids`` → ``ok=False``, no re-raise."""
    payload = {
        "instincts": [
            {
                "trigger": "t", "domain": "entry",
                "confidence": 0.5,
                "evidence_trade_ids": ["one", "two"],  # invalid
                "contradictions_trade_ids": [],
            }
        ]
    }
    ext = SingleShotInstinctExtractor(_FakeLLM(response=payload))
    out = ext.extract([], [])
    assert out.ok is False


def test_extractor_never_raises_on_confidence_out_of_range() -> None:
    """LLM returns ``confidence=2.0`` → ``ok=False``, no re-raise (validator
    path doesn't see this row at all)."""
    payload = {
        "instincts": [
            {
                "trigger": "t", "domain": "entry",
                "confidence": 2.0,
                "evidence_trade_ids": [], "contradictions_trade_ids": [],
            }
        ]
    }
    ext = SingleShotInstinctExtractor(_FakeLLM(response=payload))
    out = ext.extract([], [])
    assert out.ok is False


def test_extractor_never_raises_on_empty_trigger() -> None:
    """LLM returns an empty trigger → ``ok=False``, no re-raise."""
    payload = {
        "instincts": [
            {
                "trigger": "", "domain": "entry",
                "confidence": None,
                "evidence_trade_ids": [], "contradictions_trade_ids": [],
            }
        ]
    }
    ext = SingleShotInstinctExtractor(_FakeLLM(response=payload))
    out = ext.extract([], [])
    assert out.ok is False


def test_extractor_never_raises_on_unsupported_payload_type() -> None:
    """LLM returns neither a dict nor a string → ``ok=False``, no re-raise."""
    ext = SingleShotInstinctExtractor(_FakeLLM(response=12345))
    out = ext.extract([], [])
    assert out.ok is False


# ---------------------------------------------------------------------------
# Single-shot extractor — observability / wiring surface.
# ---------------------------------------------------------------------------


def test_extractor_passes_lessons_and_rewards_to_llm() -> None:
    """The lessons + rewards the caller passed in reach the LLM via the user prompt."""
    fake = _FakeLLM(response={"instincts": []})
    ext = SingleShotInstinctExtractor(fake)
    lessons = [{"lesson_text": "Lesson-A"}]
    rewards = [{"win_loss": "WIN", "outcome_score_delta": 1.0}]
    ext.extract(lessons, rewards)
    assert len(fake.calls) == 1
    _sys, user, _schema = fake.calls[0]
    assert "Lesson-A" in user
    assert "WIN" in user


def test_extractor_does_not_call_llm_on_empty_input_but_still_returns_ok() -> None:
    """Empty lessons + empty rewards → empty result, but the LLM **is** still
    called once (one extraction cycle per invocation — mirrors ``Brain.reflect``)."""
    fake = _FakeLLM(response={"instincts": []})
    out = SingleShotInstinctExtractor(fake).extract([], [])
    assert out.ok is True
    assert len(fake.calls) == 1


def test_extractor_result_repr_includes_n_or_error() -> None:
    """``__repr__`` is operator-friendly — counts rows on success, shows error on failure."""
    ok = InstinctExtractionResult(ok=True, instincts=[], error=None)
    assert "n=0" in repr(ok)
    bad = InstinctExtractionResult(ok=False, instincts=[], error="boom")
    assert "boom" in repr(bad)
