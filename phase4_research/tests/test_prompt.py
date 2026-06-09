"""Tests for ``prompt.build_prompt`` — deterministic prompt assembly.

All pure, no network, no AI. Concept §4 mandates ≥5 cases; this file covers the
3-tuple shape + system constraints, the universe embedded in both the user table and
the dynamic schema enum, honest ``None`` rendering (off-hours + whole-snapshot-None),
the schema shape, the direction clamp, trade/lesson rendering, the floor/score block,
and the empty-universe edge.
"""

from __future__ import annotations

from typing import Any

from research.models import ResearchContext
from research.prompt import build_prompt
from tests.conftest import DEFAULT_EPIC, _make_prompt_dict

BOTH = ("BUY", "SELL")
THRESHOLD = 55.0


def _empty_context() -> ResearchContext:
    """A context with an empty universe and empty P2/P3 (abstain-path shape)."""
    return ResearchContext(
        tradeable_epics=[],
        recent_trades=[],
        recent_lessons=[],
        bot_score=42.0,
        risk_level="KONSERVATIV",
        brain_context=None,
        anchor_epic=DEFAULT_EPIC,
    )


def test_returns_triple_with_system_constraints(research_context: ResearchContext) -> None:
    """Returns (system, user, schema); system carries the key constraints."""
    system, user, schema = build_prompt(research_context, THRESHOLD, BOTH)

    assert isinstance(system, str) and isinstance(user, str) and isinstance(schema, dict)
    low = system.lower()
    assert "dax" in low and "cfd" in low
    assert "only from the provided list" in low or "only from the list" in low
    assert "15 min" in low or "delayed" in low
    assert "abstain" in low
    # BUY/SELL vocabulary is the sanctioned set (the prompt also explicitly forbids
    # CALL/PUT, so we assert the positive vocabulary rather than CALL/PUT absence).
    assert '"buy"' in low and '"sell"' in low


def test_universe_in_user_and_schema_enum(research_context: ResearchContext) -> None:
    """Universe epics appear in the user table AND exactly in the schema enum."""
    _, user, schema = build_prompt(research_context, THRESHOLD, BOTH)

    assert DEFAULT_EPIC in user
    assert "Germany 40 Cash" in user  # the name column
    # Nullable enum via anyOf (string-branch + null-branch) — NOT a type-array union.
    epic_schema = schema["properties"]["epic"]
    assert epic_schema["anyOf"][0]["enum"] == [DEFAULT_EPIC]
    assert {"type": "null"} in epic_schema["anyOf"]


def test_none_market_values_rendered_honestly(research_context: ResearchContext) -> None:
    """Off-hours None indicators render as 'n/a' — never faked to 0."""
    research_context.brain_context = _make_prompt_dict(
        drift_pct=None,
        momentum_15m_pct=None,
        volume_z_score=None,
        distance_to_high_pct=None,
        distance_to_low_pct=None,
        range_30d=None,
    )
    _, user, _ = build_prompt(research_context, THRESHOLD, BOTH)

    assert "n/a" in user
    # the drift line must show n/a, not a fabricated 0
    drift_line = next(ln for ln in user.splitlines() if ln.startswith("- drift:"))
    assert drift_line == "- drift: n/a"


def test_whole_snapshot_none(research_context: ResearchContext) -> None:
    """A fully-missing brain context yields an explicit 'unavailable', no crash."""
    research_context.brain_context = None
    _, user, _ = build_prompt(research_context, THRESHOLD, BOTH)
    assert "unavailable" in user.lower()


def test_schema_shape(research_context: ResearchContext) -> None:
    """Schema required / additionalProperties / confidence shape are exact."""
    _, _, schema = build_prompt(research_context, THRESHOLD, BOTH)

    assert schema["required"] == ["abstain", "reasoning"]
    assert schema["additionalProperties"] is False
    # confidence is a nullable number via anyOf. Numeric bounds (minimum/maximum)
    # are deliberately ABSENT — Structured Outputs rejects them; the [0,100] range
    # is enforced independently by validator.py.
    conf = schema["properties"]["confidence"]
    assert {branch["type"] for branch in conf["anyOf"]} == {"number", "null"}
    assert "minimum" not in conf and "maximum" not in conf
    assert schema["properties"]["abstain"]["type"] == "boolean"


def test_direction_clamp_reflected(research_context: ResearchContext) -> None:
    """BUY-only clamp → schema direction enum ['BUY', None] and BUY-only instructions.

    Asserts on the schema enum and the *instruction* blocks (permitted directions /
    answer format), not on whole-user 'SELL' absence — the trade-history table may
    legitimately contain a past SELL.
    """
    _, user, schema = build_prompt(research_context, THRESHOLD, ("BUY",))

    assert schema["properties"]["direction"]["anyOf"][0]["enum"] == ["BUY"]
    assert {"type": "null"} in schema["properties"]["direction"]["anyOf"]
    assert "permitted directions: BUY" in user
    assert "direction must be one of [BUY]." in user


def test_trades_and_lessons_rendered(research_context: ResearchContext) -> None:
    """Trade rows (direction/epic/pnl) and lesson text are present."""
    _, user, _ = build_prompt(research_context, THRESHOLD, BOTH)

    assert "Recent trades" in user
    assert "BUY" in user and "12.50" in user  # pnl formatted
    assert "Trend day; held to target." in user


def test_empty_trades_and_lessons_graceful() -> None:
    """Empty P2 reads render 'none' lines, no crash."""
    _, user, _ = build_prompt(_empty_context(), THRESHOLD, BOTH)
    assert "Recent trades: none" in user
    assert "Active lessons: none" in user


def test_floor_and_score_in_user(research_context: ResearchContext) -> None:
    """The required floor and bot score/risk level appear in the user message."""
    _, user, _ = build_prompt(research_context, 70.0, BOTH)
    assert "70.00" in user  # the floor
    assert "55.00" in user  # bot score
    assert "AGGRESSIV" in user


def test_empty_universe_edge() -> None:
    """Empty universe → schema epic enum [None], no instruments table, no crash."""
    _, user, schema = build_prompt(_empty_context(), THRESHOLD, BOTH)
    # Empty universe → empty string-branch enum (still well-formed; never sent to
    # the API — the orchestrator abstains before the LLM call on an empty universe).
    assert schema["properties"]["epic"]["anyOf"][0]["enum"] == []
    assert {"type": "null"} in schema["properties"]["epic"]["anyOf"]
    assert "none right now" in user.lower()
