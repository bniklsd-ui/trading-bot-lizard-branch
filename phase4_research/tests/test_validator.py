"""Tests for the hallucination guard — the most important suite in Phase 4.

All mocked, no network, no real LLM. The broker recheck uses ``FakeBroker``
(``conftest.py``). Concept §2 mandates ≥12 cases; this file covers all of them
plus the Phase-4-gate "proof test" (an adversarial pick is caught before it can
become a candidate).

Default direction set is both BUY/SELL; the long-bias clamp itself is tested in
Step 6 (``candidate_filter``) — here we pass ``allowed_directions`` explicitly.
"""

from __future__ import annotations

from typing import Any

import pytest

from research import timeutil
from research.models import Candidate
from research.validator import validate_candidate
from tests.conftest import DEFAULT_EPIC, FakeBroker

BOTH = ("BUY", "SELL")
THRESHOLD = 55.0
MAX_SPREAD = 0.5

# Candidate keys the persisted contract must carry (Step-1 frozen set).
_CONTRACT_KEYS = {
    "epic", "direction", "llm_confidence", "reasoning", "spread_pct_at_pick",
    "drift_at_pick", "score_at_pick", "threshold_applied", "generated_at", "source",
}


def _validate(raw: dict[str, Any], broker: FakeBroker, universe, **over) -> Any:
    """Call ``validate_candidate`` with sensible Step-2 defaults."""
    kwargs = dict(
        threshold=THRESHOLD,
        allowed_directions=BOTH,
        max_spread_pct=MAX_SPREAD,
        score_at_pick=55.0,
        drift_at_pick=None,
    )
    kwargs.update(over)
    return validate_candidate(raw, universe, broker=broker, **kwargs)


# --- rejections -------------------------------------------------------------


def test_invented_epic_rejected(broker, universe, good_raw):
    good_raw["epic"] = "XX.D.FAKE.IP"
    vr = _validate(good_raw, broker, universe)
    assert not vr.valid and vr.candidate is None
    assert "universe" in vr.rejected_reason


def test_call_direction_rejected(broker, universe, good_raw):
    # Old options leftover — must never survive (Decision 1).
    good_raw["direction"] = "CALL"
    vr = _validate(good_raw, broker, universe)
    assert not vr.valid and vr.candidate is None
    assert "direction" in vr.rejected_reason


def test_direction_outside_clamp_rejected(broker, universe, good_raw):
    # SELL is well-formed but excluded when the clamp leaves only BUY.
    good_raw["direction"] = "SELL"
    vr = _validate(good_raw, broker, universe, allowed_directions=("BUY",))
    assert not vr.valid and vr.candidate is None


def test_confidence_below_threshold_rejected(broker, universe, good_raw):
    good_raw["confidence"] = 54.9
    vr = _validate(good_raw, broker, universe)
    assert not vr.valid
    assert "below floor" in vr.rejected_reason


def test_confidence_above_100_rejected(broker, universe, good_raw):
    good_raw["confidence"] = 142
    vr = _validate(good_raw, broker, universe)
    assert not vr.valid and "range" in vr.rejected_reason


def test_confidence_non_numeric_rejected(broker, universe, good_raw):
    good_raw["confidence"] = "very high"
    vr = _validate(good_raw, broker, universe)
    assert not vr.valid and "numeric" in vr.rejected_reason


def test_confidence_bool_rejected(broker, universe, good_raw):
    # bool is a subclass of int — must not slip through as 0/1.
    good_raw["confidence"] = True
    vr = _validate(good_raw, broker, universe)
    assert not vr.valid and "numeric" in vr.rejected_reason


def test_wide_live_spread_rejected(universe, good_raw):
    broker = FakeBroker(spread_pct=0.9)  # > MAX_SPREAD 0.5
    vr = _validate(good_raw, broker, universe)
    assert not vr.valid and "spread" in vr.rejected_reason


def test_non_tradeable_status_rejected(universe, good_raw):
    broker = FakeBroker(market_status="CLOSED")
    vr = _validate(good_raw, broker, universe)
    assert not vr.valid and "TRADEABLE" in vr.rejected_reason


def test_get_price_not_ok_rejected(universe, good_raw):
    broker = FakeBroker(ok=False)
    vr = _validate(good_raw, broker, universe)
    assert not vr.valid and "not ok" in vr.rejected_reason


@pytest.mark.parametrize("missing", ["epic", "direction", "confidence"])
def test_missing_required_field_rejected(broker, universe, good_raw, missing):
    good_raw[missing] = None
    vr = _validate(good_raw, broker, universe)
    assert not vr.valid and missing in vr.rejected_reason


# --- valid abstain ----------------------------------------------------------


def test_abstain_is_valid_no_candidate(broker, universe):
    raw = {"abstain": True, "reasoning": "Nothing tradeable; sit out."}
    vr = _validate(raw, broker, universe)
    assert vr.valid and vr.candidate is None and vr.rejected_reason is None
    assert broker.calls == []  # no live recheck on abstain


# --- passes -----------------------------------------------------------------


def test_confidence_equal_threshold_passes(broker, universe, good_raw):
    good_raw["confidence"] = THRESHOLD  # boundary: >= floor passes
    vr = _validate(good_raw, broker, universe)
    assert vr.valid and isinstance(vr.candidate, Candidate)


def test_well_formed_buy_passes_full_contract(broker, universe, good_raw):
    vr = _validate(good_raw, broker, universe, drift_at_pick=0.12, score_at_pick=61.0)
    assert vr.valid
    c = vr.candidate
    assert isinstance(c, Candidate)
    assert c.epic == DEFAULT_EPIC and c.direction == "BUY"
    assert c.llm_confidence == 72.0 and c.source == "research"
    # spread_pct_at_pick comes from the FRESH recheck (0.03), not the raw pick.
    assert c.spread_pct_at_pick == 0.03
    assert c.drift_at_pick == 0.12 and c.score_at_pick == 61.0
    assert c.threshold_applied == THRESHOLD
    # generated_at is a real, parseable ISO timestamp.
    assert timeutil.parse_iso(c.generated_at).tzinfo is not None
    # full frozen contract round-trips.
    assert set(c.to_dict()) == _CONTRACT_KEYS
    assert broker.calls == [DEFAULT_EPIC]  # exactly one live recheck


def test_well_formed_sell_passes(broker, universe, good_raw):
    good_raw["direction"] = "SELL"
    vr = _validate(good_raw, broker, universe)
    assert vr.valid and vr.candidate is not None and vr.candidate.direction == "SELL"


# --- Phase-4 gate proof test ------------------------------------------------


def test_proof_adversarial_pick_caught(broker, universe):
    """Invented epic + inflated confidence + old CALL → never a candidate."""
    raw = {
        "abstain": False,
        "epic": "ZZ.D.MOON.IP",       # hallucinated
        "direction": "CALL",           # dead options vocabulary
        "confidence": 99,              # overconfident
        "reasoning": "Trust me.",
    }
    vr = _validate(raw, broker, universe)
    assert not vr.valid and vr.candidate is None
    # earliest guard (epic membership) fires before direction/confidence.
    assert "universe" in vr.rejected_reason
    assert broker.calls == []  # rejected before any live trade-path call
