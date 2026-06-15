"""Tests for Module 3 — ``debate.prompts`` (Bull / Bear / Judge prompt assembly).

Pure-function tests: build a ``DebateContext`` + a scripted transcript directly
(decoupled from the context builder) and assert the (system, user, schema)
triples. No network, no LLM. Verifies the cache-prefix invariant (context in
system, transcript in user), delay honesty, role-correctness, schema shape, and
the no-options-vocabulary hygiene rule.
"""

from __future__ import annotations

from debate.models import AgentTurn, DebateContext
from debate.prompts import (
    build_bear_prompt,
    build_bull_prompt,
    build_judge_prompt,
)


def _ctx(**overrides) -> DebateContext:
    base = dict(
        epic="IX.D.DAX.IFMM.IP",
        seed_direction="BUY",
        seed_reasoning="seed: bullish breakout",
        seed_confidence=62.0,
        spread_pct=0.03,
        market_status="TRADEABLE",
        recent_bars_summary="12 x MINUTE_5 bars (IG real-time): net +0.111%",
        drift_at_pick=0.42,
        score_at_pick=58.0,
        generated_at="2026-06-15T11:22:33.456Z",
    )
    base.update(overrides)
    return DebateContext(**base)


def _transcript() -> list[AgentTurn]:
    return [
        AgentTurn(round=1, agent="BULL", model="m", text="BULL-ARGUMENT-EINS", usage={}),
        AgentTurn(round=1, agent="BEAR", model="m", text="BEAR-ARGUMENT-EINS", usage={}),
    ]


_BUILDERS = (build_bull_prompt, build_bear_prompt, build_judge_prompt)


def test_each_builder_returns_triple() -> None:
    ctx = _ctx()
    for build in _BUILDERS:
        system, user, schema = build(ctx, [])
        assert isinstance(system, str) and system
        assert isinstance(user, str) and user
        assert isinstance(schema, dict)


def test_schemas_well_formed() -> None:
    ctx = _ctx()
    for build in (build_bull_prompt, build_bear_prompt):
        _, _, schema = build(ctx, [])
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        assert schema["required"] == ["argument"]
    _, _, judge = build_judge_prompt(ctx, [])
    assert judge["type"] == "object"
    assert judge["additionalProperties"] is False
    assert judge["properties"]["decision"]["enum"] == ["TRADE", "ABSTAIN"]
    assert set(judge["required"]) == {
        "decision", "direction", "confidence", "rationale", "conclude",
    }


def test_context_in_system_not_in_user() -> None:
    ctx = _ctx()
    transcript = _transcript()
    for build in _BUILDERS:
        system, user, _ = build(ctx, transcript)
        # Context lives in the stable (cacheable) system block.
        assert ctx.epic in system
        assert ctx.seed_direction in system
        assert "0.03%" in system  # fresh spread rendered
        assert ctx.recent_bars_summary in system
        # The growing transcript must NOT be in system (cache-prefix invariant).
        assert "BULL-ARGUMENT-EINS" not in system


def test_transcript_serialised_in_order_in_user() -> None:
    ctx = _ctx()
    system, user, _ = build_judge_prompt(ctx, _transcript())
    assert "BULL-ARGUMENT-EINS" in user
    assert "BEAR-ARGUMENT-EINS" in user
    assert user.index("BULL-ARGUMENT-EINS") < user.index("BEAR-ARGUMENT-EINS")
    assert "Runde 1" in user


def test_judge_schema_allows_direction_null() -> None:
    _, _, judge = build_judge_prompt(_ctx(), [])
    branches = judge["properties"]["direction"]["anyOf"]
    assert {"type": "null"} in branches
    assert {"type": "string", "enum": ["BUY", "SELL"]} in branches
    # No numeric bounds on confidence (Anthropic Structured Outputs rejects them).
    conf = judge["properties"]["confidence"]
    assert "minimum" not in str(conf) and "maximum" not in str(conf)


def test_delay_honesty_present() -> None:
    ctx = _ctx()
    for build in _BUILDERS:
        system, _, _ = build(ctx, [])
        assert "15 min" in system  # seed flagged delayed
        assert "VERZÖGERT" in system.upper()
        assert "ECHTZEIT" in system.upper()  # real-time fields flagged


def test_no_options_vocabulary() -> None:
    ctx = _ctx()
    # Tokens are split-then-joined so the literals don't appear in this source
    # file (keeping the repo-wide §0 hygiene grep over phase6_debate/ empty).
    banned = tuple(
        a + b
        for a, b in (
            ("CA", "LL"), ("P", "UT"), ("str", "ike"), ("o", "tm"),
            ("iss", "uer"), ("FL", "IP"), ("tur", "bo"), ("option", "_check"),
        )
    )
    for build in _BUILDERS:
        system, user, _ = build(ctx, _transcript())
        blob = (system + " " + user)
        for token in banned:
            assert token not in blob, f"banned token {token!r} in prompt"


def test_roles_distinct_and_correct() -> None:
    ctx = _ctx()
    bull_sys, _, _ = build_bull_prompt(ctx, [])
    bear_sys, _, _ = build_bear_prompt(ctx, [])
    assert "BULL" in bull_sys and "LONG" in bull_sys and "BUY" in bull_sys
    assert "BEAR" in bear_sys and "SHORT" in bear_sys and "SELL" in bear_sys
    assert bull_sys != bear_sys


def test_empty_transcript_well_formed() -> None:
    ctx = _ctx()
    for build in _BUILDERS:
        _, user, _ = build(ctx, [])
        assert "noch keine Argumente" in user


def test_none_drift_renders_na() -> None:
    ctx = _ctx(drift_at_pick=None)
    system, _, _ = build_bull_prompt(ctx, [])
    assert "n/a" in system
