"""Tests for the Phase-6 data contracts (Module 1).

Types only — these assert the frozen field set, the §0 config defaults, the
exception hierarchy, and the advisory-only role of ``confidence``. No network, no
real LLM, no logic exercised (there is none in ``models.py``).
"""

from __future__ import annotations

import dataclasses
import json

import pytest

from debate.models import (
    AgentTurn,
    DebateBudgetExceeded,
    DebateConfig,
    DebateContext,
    DebateError,
    DebateLLMError,
    DebateOutcome,
)


# --------------------------------------------------------------------------- #
# 1. DebateConfig defaults match the locked §0 table                          #
# --------------------------------------------------------------------------- #
def test_config_defaults_match_concept_section_0() -> None:
    cfg = DebateConfig()
    # models (Decision C)
    assert cfg.model_bull == "claude-haiku-4-5-20251001"
    assert cfg.model_bear == "claude-haiku-4-5-20251001"
    assert cfg.model_judge == "claude-sonnet-4-6"
    # rounds & hard caps (Decision E/J)
    assert cfg.max_rounds == 5
    assert cfg.early_stop is True
    assert cfg.max_total_calls == 18
    assert cfg.max_cumulative_input_tokens == 120_000
    assert cfg.max_cumulative_output_tokens == 12_000
    assert cfg.wall_clock_timeout_s == 120.0
    # caching & compression (Decision D/G)
    assert cfg.cache_system is True
    assert cfg.compression_trigger_pct == 0.65
    # decoding
    assert cfg.temperature_bull == 0.4
    assert cfg.temperature_bear == 0.4
    assert cfg.temperature_judge == 0.1
    assert cfg.max_tokens_agent == 512
    assert cfg.max_tokens_judge == 768
    # audit
    assert cfg.debate_log_path == "data/state/debate_log.json"


# --------------------------------------------------------------------------- #
# 2. Decision H — the self-documenting "confidence gates nothing" constant      #
# --------------------------------------------------------------------------- #
def test_confidence_gates_nothing_constant_present_and_true() -> None:
    # A label, not behaviour: its presence documents that the Judge's confidence
    # is advisory only. No code branch is allowed to gate on confidence.
    assert DebateConfig().confidence_gates_nothing is True


# --------------------------------------------------------------------------- #
# 3. Contract types are immutable (frozen)                                     #
# --------------------------------------------------------------------------- #
def test_contract_types_are_frozen() -> None:
    turn = AgentTurn(round=1, agent="BULL", model="m", text="t", usage={})
    ctx = _sample_context()
    outcome = _sample_outcome(transcript=(turn,))
    for obj, attr, val in (
        (DebateConfig(), "max_rounds", 99),
        (ctx, "epic", "X"),
        (turn, "agent", "BEAR"),
        (outcome, "decision", "ABSTAIN"),
    ):
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(obj, attr, val)


# --------------------------------------------------------------------------- #
# 4. DebateOutcome.to_dict round-trips (incl. nested transcript) and is JSON   #
# --------------------------------------------------------------------------- #
def test_outcome_to_dict_serialises_nested_transcript() -> None:
    turn = AgentTurn(
        round=1, agent="JUDGE", model="claude-sonnet-4-6", text="synth",
        usage={"input_tokens": 10, "output_tokens": 5},
    )
    outcome = _sample_outcome(transcript=(turn,), token_summary={"input_tokens": 10})
    d = outcome.to_dict()
    # transcript becomes a list of plain dicts
    assert isinstance(d["transcript"], list)
    assert d["transcript"][0]["agent"] == "JUDGE"
    assert d["transcript"][0]["usage"]["input_tokens"] == 10
    # whole thing is JSON-serialisable (the audit writes it to debate_log.json)
    assert json.loads(json.dumps(d))["decision"] == "TRADE"


# --------------------------------------------------------------------------- #
# 5. Exception hierarchy + codes                                              #
# --------------------------------------------------------------------------- #
def test_exception_hierarchy_and_codes() -> None:
    assert issubclass(DebateBudgetExceeded, DebateError)
    assert issubclass(DebateLLMError, DebateError)
    assert DebateError.code == "DEBATE_ERROR"
    assert DebateBudgetExceeded.code == "DEBATE_BUDGET_EXCEEDED"
    assert DebateLLMError.code == "DEBATE_LLM_ERROR"
    # both are catchable as the base family (fail-closed handling in Module 6)
    for exc_cls in (DebateBudgetExceeded, DebateLLMError):
        with pytest.raises(DebateError):
            raise exc_cls("boom")


# --------------------------------------------------------------------------- #
# 6. confidence is data, not a gate: an ABSTAIN still carries a confidence      #
# --------------------------------------------------------------------------- #
def test_abstain_outcome_has_none_direction_but_keeps_confidence() -> None:
    outcome = DebateOutcome(
        decision="ABSTAIN", direction=None, confidence=72.0,
        rationale="fail-closed", rounds_used=2,
    )
    assert outcome.direction is None
    # confidence is preserved as advisory data even on ABSTAIN (Decision H / P7)
    assert outcome.confidence == 72.0


# --------------------------------------------------------------------------- #
# helpers                                                                      #
# --------------------------------------------------------------------------- #
def _sample_context() -> DebateContext:
    return DebateContext(
        epic="IX.D.DAX.IFMM.IP", seed_direction="BUY", seed_reasoning="r",
        seed_confidence=70.0, spread_pct=0.02, market_status="TRADEABLE",
        recent_bars_summary="…", drift_at_pick=None, score_at_pick=55.0,
        generated_at="2026-06-15T08:00:00Z",
    )


def _sample_outcome(
    *, transcript: tuple[AgentTurn, ...] = (), token_summary: dict | None = None,
) -> DebateOutcome:
    return DebateOutcome(
        decision="TRADE", direction="BUY", confidence=66.0, rationale="ok",
        rounds_used=len(transcript), transcript=transcript,
        token_summary=token_summary or {},
    )
