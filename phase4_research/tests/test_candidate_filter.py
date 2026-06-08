"""Tests for ``candidate_filter`` — the real deterministic gate (Step 6).

All mocked, no network, no real LLM. Exercises the two pure helpers
(``confidence_threshold`` / ``resolve_allowed_directions``) and ``apply_filter``
(the gate itself), including the **soft** drift-coherence warn that must pass,
not reject.
"""

from __future__ import annotations

import dataclasses
from typing import Any

import pytest

from research.candidate_filter import (
    apply_filter,
    confidence_threshold,
    resolve_allowed_directions,
)
from research.models import Candidate, ResearchConfig, ResearchContext

DEFAULT_EPIC = "IX.D.DAX.IFMM.IP"


def make_candidate(**overrides: Any) -> Candidate:
    """Build a well-formed BUY candidate; override any field per test."""
    base: dict[str, Any] = {
        "epic": DEFAULT_EPIC,
        "direction": "BUY",
        "llm_confidence": 72.0,
        "reasoning": "Drift positive, spread tight.",
        "spread_pct_at_pick": 0.03,
        "drift_at_pick": 0.42,
        "score_at_pick": 55.0,
        "threshold_applied": 55.0,
        "generated_at": "2026-06-08T09:30:00+00:00",
        "source": "research",
    }
    base.update(overrides)
    return Candidate(**base)


@pytest.fixture
def config() -> ResearchConfig:
    return ResearchConfig()


# --------------------------------------------------------------------------- #
# confidence_threshold                                                         #
# --------------------------------------------------------------------------- #


def test_floor_default_at_or_above_neutral(config: ResearchConfig) -> None:
    """Score >= 50 → the default (looser) floor of 55."""
    assert confidence_threshold(55.0, config) == 55.0
    assert confidence_threshold(50.0, config) == 55.0  # boundary is inclusive of default


def test_floor_strict_below_neutral(config: ResearchConfig) -> None:
    """Score < 50 → the stricter floor of 70."""
    assert confidence_threshold(40.0, config) == 70.0
    assert confidence_threshold(49.999, config) == 70.0


# --------------------------------------------------------------------------- #
# resolve_allowed_directions                                                   #
# --------------------------------------------------------------------------- #


def test_clamp_to_buy_only_below_threshold(config: ResearchConfig) -> None:
    """Clamp on + score below long_bias_below_score → only BUY."""
    assert resolve_allowed_directions(40.0, config) == ("BUY",)


def test_no_clamp_above_threshold(config: ResearchConfig) -> None:
    """Score at/above the clamp threshold → both directions stand."""
    assert resolve_allowed_directions(55.0, config) == ("BUY", "SELL")


def test_clamp_disabled_keeps_both_at_low_score() -> None:
    """Clamp disabled → both directions even at a low score."""
    config = ResearchConfig(enable_long_bias_clamp=False)
    assert resolve_allowed_directions(40.0, config) == ("BUY", "SELL")


# --------------------------------------------------------------------------- #
# apply_filter — hard rules                                                    #
# --------------------------------------------------------------------------- #


def test_clean_buy_passes(
    research_context: ResearchContext, config: ResearchConfig
) -> None:
    """A clean in-universe BUY at neutral score passes with no rule."""
    verdict = apply_filter(make_candidate(), research_context, config)
    assert verdict.ok is True
    assert verdict.rule is None


def test_sell_filtered_when_clamped(
    research_context: ResearchContext, config: ResearchConfig
) -> None:
    """SELL at score < 50 is rejected by the long-bias clamp."""
    ctx = dataclasses.replace(research_context, bot_score=40.0)
    verdict = apply_filter(make_candidate(direction="SELL"), ctx, config)
    assert verdict.ok is False
    assert verdict.rule == "direction_not_allowed"


def test_sell_allowed_at_neutral_score(
    research_context: ResearchContext, config: ResearchConfig
) -> None:
    """SELL passes at neutral score (clamp not engaged); drift not opposed enough."""
    # research_context drift_pct is 0.42 (< 0.5 threshold) → no warn either.
    verdict = apply_filter(make_candidate(direction="SELL"), research_context, config)
    assert verdict.ok is True
    assert verdict.rule is None


def test_spread_too_wide_rejected(
    research_context: ResearchContext, config: ResearchConfig
) -> None:
    """A universe entry whose spread exceeds the bound is rejected."""
    wide = [dict(research_context.tradeable_epics[0], spread_pct=0.9)]
    ctx = dataclasses.replace(research_context, tradeable_epics=wide)
    verdict = apply_filter(make_candidate(), ctx, config)
    assert verdict.ok is False
    assert verdict.rule == "spread_too_wide"


def test_not_tradeable_rejected(
    research_context: ResearchContext, config: ResearchConfig
) -> None:
    """A universe entry no longer TRADEABLE is rejected."""
    closed = [dict(research_context.tradeable_epics[0], market_status="EDITS_ONLY")]
    ctx = dataclasses.replace(research_context, tradeable_epics=closed)
    verdict = apply_filter(make_candidate(), ctx, config)
    assert verdict.ok is False
    assert verdict.rule == "not_tradeable"


def test_epic_not_in_universe_rejected(
    research_context: ResearchContext, config: ResearchConfig
) -> None:
    """A candidate epic absent from the universe is rejected (defense-in-depth)."""
    verdict = apply_filter(make_candidate(epic="XX.D.FOO.IP"), research_context, config)
    assert verdict.ok is False
    assert verdict.rule == "epic_not_in_universe"


# --------------------------------------------------------------------------- #
# apply_filter — soft drift-coherence (warn, never reject)                     #
# --------------------------------------------------------------------------- #


def test_drift_incoherent_sell_warns_but_passes(
    research_context: ResearchContext, config: ResearchConfig
) -> None:
    """SELL against a strongly positive delayed drift → passes WITH a warn rule."""
    brain = dict(research_context.brain_context or {}, drift_pct=1.5)
    ctx = dataclasses.replace(research_context, brain_context=brain)
    verdict = apply_filter(make_candidate(direction="SELL"), ctx, config)
    assert verdict.ok is True  # soft: NOT a reject
    assert verdict.rule == "drift_coherence_warn"
    assert verdict.details["drift_pct"] == 1.5


def test_drift_incoherent_buy_warns_but_passes(
    research_context: ResearchContext, config: ResearchConfig
) -> None:
    """BUY against a strongly negative delayed drift → passes WITH a warn rule."""
    brain = dict(research_context.brain_context or {}, drift_pct=-1.5)
    ctx = dataclasses.replace(research_context, brain_context=brain)
    verdict = apply_filter(make_candidate(direction="BUY"), ctx, config)
    assert verdict.ok is True
    assert verdict.rule == "drift_coherence_warn"


def test_drift_none_no_warn(
    research_context: ResearchContext, config: ResearchConfig
) -> None:
    """Off-hours drift (None) → coherence check skipped, clean pass."""
    brain = dict(research_context.brain_context or {}, drift_pct=None)
    ctx = dataclasses.replace(research_context, brain_context=brain)
    verdict = apply_filter(make_candidate(direction="SELL"), ctx, config)
    assert verdict.ok is True
    assert verdict.rule is None


def test_drift_brain_context_none_no_crash(
    research_context: ResearchContext, config: ResearchConfig
) -> None:
    """A wholly-absent brain context degrades gracefully (clean pass, no warn)."""
    ctx = dataclasses.replace(research_context, brain_context=None)
    verdict = apply_filter(make_candidate(), ctx, config)
    assert verdict.ok is True
    assert verdict.rule is None
