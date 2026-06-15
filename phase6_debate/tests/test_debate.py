"""Tests for Module 6 — ``debate/debate.py`` (the orchestrator, the phase core).

All mocked: a scripted ``FakeLLM`` (no SDK / no network / no real LLM) and the
configurable ``FakeBroker``, with time injected so nothing waits. Covers the §6
contract: round order, seed-confirm vs flip, early-stop, max-rounds exhaustion,
fail-closed on cap breach / request failure / context fault, deterministic
compression, the advisory-only ``confidence`` (Decision H), audit-once, and the
code-side validation of the AI output (Hard Rule 3).
"""

from __future__ import annotations

from typing import Any

from debate.debate import Debate
from debate.models import DebateConfig, DebateContext, DebateOutcome

from tests.conftest import FakeBroker, FakeLLM, _FakeEnv


# --------------------------------------------------------------------------- #
# scripted-answer helpers                                                      #
# --------------------------------------------------------------------------- #


def _arg(text: str = "argument") -> dict[str, Any]:
    return {"argument": text}


def _judge(
    *,
    decision: str = "TRADE",
    direction: str | None = "BUY",
    confidence: float | None = 70.0,
    rationale: str = "judge synthesis",
    conclude: bool = True,
) -> dict[str, Any]:
    return {
        "decision": decision,
        "direction": direction,
        "confidence": confidence,
        "rationale": rationale,
        "conclude": conclude,
    }


def _round(bull: str, bear: str, judge: dict[str, Any]) -> list[dict[str, Any]]:
    """One round's three scripted answers, in turn order."""
    return [_arg(bull), _arg(bear), judge]


def _build(broker: FakeBroker, llm: FakeLLM, config: DebateConfig | None = None,
           audit: Any = None) -> Debate:
    return Debate(broker, llm, config or DebateConfig(), audit=audit)


# --------------------------------------------------------------------------- #
# round order + the two direction outcomes                                     #
# --------------------------------------------------------------------------- #


def test_bull_bear_judge_order_and_per_role_models_and_tokens(broker, candidate) -> None:
    cfg = DebateConfig()
    llm = FakeLLM(_round("bull", "bear", _judge(conclude=True)))
    outcome = _build(broker, llm, cfg).run(candidate)

    assert outcome.decision == "TRADE"
    # one round, in Bull → Bear → Judge order, with the per-role model + max_tokens
    models = [t[0] for t in llm.turns]
    max_toks = [t[2] for t in llm.turns]
    assert models == [cfg.model_bull, cfg.model_bear, cfg.model_judge]
    assert max_toks == [cfg.max_tokens_agent, cfg.max_tokens_agent, cfg.max_tokens_judge]


def test_judge_confirms_seed_direction(broker, make_candidate) -> None:
    cand = make_candidate(direction="BUY")
    llm = FakeLLM(_round("b", "b", _judge(decision="TRADE", direction="BUY")))
    outcome = _build(broker, llm).run(cand)
    assert outcome.decision == "TRADE"
    assert outcome.direction == "BUY"


def test_judge_flips_seed_direction(broker, make_candidate) -> None:
    cand = make_candidate(direction="BUY")  # seed BUY ...
    llm = FakeLLM(_round("b", "b", _judge(decision="TRADE", direction="SELL")))
    outcome = _build(broker, llm).run(cand)
    assert outcome.decision == "TRADE"
    assert outcome.direction == "SELL"  # ... Judge reversed it (Decision B)


# --------------------------------------------------------------------------- #
# rounds: early-stop + exhaustion                                              #
# --------------------------------------------------------------------------- #


def test_early_stop_on_conclude_true(broker, candidate) -> None:
    # round 1 Judge says conclude=False, round 2 conclude=True → stop after round 2
    answers = (
        _round("b1", "b1", _judge(conclude=False))
        + _round("b2", "b2", _judge(conclude=True))
        + _round("b3", "b3", _judge(conclude=True))  # never reached
    )
    llm = FakeLLM(answers)
    outcome = _build(broker, llm).run(candidate)
    assert outcome.rounds_used == 2
    assert len(llm.turns) == 6  # no round-3 requests
    assert len(outcome.transcript) == 6


def test_max_rounds_exhausted_uses_last_judge(broker, candidate) -> None:
    cfg = DebateConfig(max_rounds=2)  # no consensus → run both rounds
    answers = (
        _round("b1", "b1", _judge(decision="TRADE", direction="SELL", conclude=False))
        + _round("b2", "b2", _judge(decision="TRADE", direction="SELL", conclude=False))
    )
    llm = FakeLLM(answers)
    outcome = _build(broker, llm, cfg).run(candidate)
    assert outcome.rounds_used == 2
    assert outcome.decision == "TRADE" and outcome.direction == "SELL"
    assert len(llm.turns) == 6


# --------------------------------------------------------------------------- #
# fail-closed paths (Decision J) — every one → ABSTAIN, no exception out       #
# --------------------------------------------------------------------------- #


def test_budget_breach_mid_debate_abstains(broker, candidate) -> None:
    cfg = DebateConfig(max_total_calls=4)  # 5th turn breaches
    answers = _round("b", "b", _judge(conclude=False)) + _round("b", "b", _judge())
    llm = FakeLLM(answers)
    outcome = _build(broker, llm, cfg).run(candidate)
    assert outcome.decision == "ABSTAIN"
    assert outcome.direction is None
    assert len(llm.turns) == 5  # breached on the 5th request, then failed closed


def test_llm_error_abstains(broker, candidate) -> None:
    llm = FakeLLM(_round("b", "b", _judge()), raises_on=0)  # Bull request fails
    outcome = _build(broker, llm).run(candidate)
    assert outcome.decision == "ABSTAIN"
    assert outcome.direction is None
    assert outcome.transcript == ()  # the failed turn was never recorded


def test_context_fault_abstains_with_zero_requests(make_candidate) -> None:
    broker = FakeBroker(price_env=_FakeEnv(ok=False))  # context build fails
    llm = FakeLLM(_round("b", "b", _judge()))
    outcome = _build(broker, llm).run(make_candidate())
    assert outcome.decision == "ABSTAIN"
    assert len(llm.turns) == 0  # not a single agent request was made
    assert outcome.transcript == ()


# --------------------------------------------------------------------------- #
# deterministic transcript compression                                         #
# --------------------------------------------------------------------------- #


def test_compression_triggers_but_full_transcript_preserved(broker, candidate) -> None:
    # 0.5 * 1000 = 500 token trigger; 100/turn → crosses before turn 7 (round 3 Bull).
    cfg = DebateConfig(
        max_rounds=3,
        compression_trigger_pct=0.5,
        max_cumulative_input_tokens=1_000,
        max_cumulative_output_tokens=1_000_000,
        max_total_calls=100,
        wall_clock_timeout_s=1e9,
    )
    answers = (
        _round("BULL-R1", "BEAR-R1", _judge(rationale="JUDGE-R1", conclude=False))
        + _round("BULL-R2", "BEAR-R2", _judge(rationale="JUDGE-R2", conclude=False))
        + _round("BULL-R3", "BEAR-R3", _judge(rationale="JUDGE-R3", conclude=False))
    )
    llm = FakeLLM(answers)
    outcome = _build(broker, llm, cfg).run(candidate)

    # the round-3 Bull request (index 6) saw the COMPRESSED view: round-1 turns gone,
    # round-2 (latest-per-agent) kept.
    user_r3_bull = llm.seen_users[6]
    assert "BULL-R1" not in user_r3_bull
    assert "BULL-R2" in user_r3_bull
    # but the full transcript in the outcome keeps every turn (Decision I)
    assert len(outcome.transcript) == 9
    assert any(t.text == "BULL-R1" for t in outcome.transcript)


# --------------------------------------------------------------------------- #
# confidence is advisory only (Decision H)                                     #
# --------------------------------------------------------------------------- #


def test_low_confidence_still_trades(broker, candidate) -> None:
    llm = FakeLLM(_round("b", "b", _judge(decision="TRADE", direction="BUY", confidence=1.0)))
    outcome = _build(broker, llm).run(candidate)
    assert outcome.decision == "TRADE"  # low confidence does NOT block a TRADE
    assert outcome.confidence == 1.0


def test_high_confidence_abstain_has_no_direction(broker, candidate) -> None:
    llm = FakeLLM(_round("b", "b", _judge(decision="ABSTAIN", direction="BUY", confidence=99.0)))
    outcome = _build(broker, llm).run(candidate)
    assert outcome.decision == "ABSTAIN"  # high confidence does NOT force a trade
    assert outcome.direction is None  # ABSTAIN → direction dropped regardless


# --------------------------------------------------------------------------- #
# AI-output validation (Hard Rule 3) + audit + transcript shape                #
# --------------------------------------------------------------------------- #


def test_trade_without_usable_direction_fails_closed(broker, candidate) -> None:
    llm = FakeLLM(_round("b", "b", _judge(decision="TRADE", direction=None)))
    outcome = _build(broker, llm).run(candidate)
    assert outcome.decision == "ABSTAIN"  # a TRADE with no direction is unusable
    assert outcome.direction is None


def test_audit_written_exactly_once(broker, candidate) -> None:
    recorded: list[tuple[DebateOutcome, DebateContext]] = []
    llm = FakeLLM(_round("b", "b", _judge()))
    outcome = _build(broker, llm, audit=lambda o, c: recorded.append((o, c))).run(candidate)
    assert len(recorded) == 1
    assert recorded[0][0] is outcome
    assert isinstance(recorded[0][1], DebateContext)


def test_transcript_is_complete_and_immutable(broker, candidate) -> None:
    llm = FakeLLM(_round("bull text", "bear text", _judge(rationale="verdict")))
    outcome = _build(broker, llm).run(candidate)
    assert isinstance(outcome.transcript, tuple)  # immutable
    assert [t.agent for t in outcome.transcript] == ["BULL", "BEAR", "JUDGE"]
    assert outcome.transcript[0].text == "bull text"
    assert outcome.transcript[2].text == "verdict"  # judge text = rationale
    assert outcome.token_summary["total_calls"] == 3
