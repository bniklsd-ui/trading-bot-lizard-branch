"""Hallucination guard — the safety core of Phase 4.

``validate_candidate`` is the structural mitigation for the hard rule "an AI
output must never trigger an order without code-side validation" (root CLAUDE.md
rule 3; concept Decision 3). It runs **independently and always**, even when
Structured Outputs already constrained the LLM response — it is defense-in-depth
plus the one check a JSON schema cannot do: a **fresh live-spread/tradeability
recheck** against the broker at validation time.

It is a pure function (no I/O except the single ``broker.get_price`` recheck) and
returns a :class:`ValidationResult`:

- a **valid abstain** (``valid=True, candidate=None``) — a legitimate "no pick";
- a **rejection** (``valid=False, candidate=None, rejected_reason=...``) — a
  hallucinated epic, a disallowed direction, sub-floor/garbage confidence, or a
  failed live recheck;
- a **clean pass** (``valid=True, candidate=<Candidate>``) — a fully-formed
  :class:`Candidate` ready for the deterministic filter (Step 6) and persistence.

The confidence floor here is a **coarse** check (concept Decision 4): LLM
self-reported confidence is uncalibrated, so it is *not* the real gate — the
deterministic ``candidate_filter`` is. The floor only screens out obviously
under-confident or malformed values.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol

from research.models import Candidate, ValidationResult
from research import timeutil

log = logging.getLogger(__name__)

# Required keys on a non-abstain raw LLM pick. The LLM output key is
# ``confidence``; it maps to the ``Candidate`` field ``llm_confidence``.
_REQUIRED_FIELDS = ("epic", "direction", "confidence")

_TRADEABLE = "TRADEABLE"


class _BrokerLike(Protocol):
    """Minimal broker surface the validator needs for the live recheck.

    Typed as a Protocol so Phase 4 does not import ``broker_wrapper`` (phase
    isolation). The real :class:`IGAdapter` and the test ``FakeBroker`` both
    satisfy it. ``get_price`` returns an Envelope-like object exposing ``.ok``
    (bool) and ``.data`` (dict with ``spread_pct`` + ``market_status``).
    """

    def get_price(self, epic: str) -> Any: ...


def _reject(reason: str) -> ValidationResult:
    """Build a rejection result and log the reason to stderr (never swallow)."""
    log.info("validator REJECT: %s", reason)
    return ValidationResult(valid=False, candidate=None, rejected_reason=reason)


def validate_candidate(
    raw: dict[str, Any],
    epic_universe: list[dict[str, Any]],
    threshold: float,
    allowed_directions: tuple[str, ...],
    broker: _BrokerLike,
    max_spread_pct: float,
    *,
    score_at_pick: float,
    drift_at_pick: float | None,
) -> ValidationResult:
    """Validate a raw LLM pick against the real universe and a live recheck.

    Args:
        raw: Parsed LLM output (Structured-Output dict or fence-stripped JSON).
            Recognised keys: ``abstain`` (bool), ``epic``, ``direction``,
            ``confidence`` (0-100), ``reasoning``.
        epic_universe: Code-provided real epics, each a dict with at least
            ``epic``. Membership in this set is the anti-hallucination gate.
        threshold: Score-dependent confidence floor (coarse; not a probability).
        allowed_directions: Permitted directions after the long-bias clamp
            (e.g. ``("BUY", "SELL")`` or ``("BUY",)``).
        broker: Broker for the fresh live-spread/tradeability recheck.
        max_spread_pct: Reject if the fresh spread exceeds this (% of ask).
        score_at_pick: Bot score at decision time — **passthrough** to the
            persisted candidate (concept §0 contract), not a validation input.
            Supplied by the orchestrator from ``context.bot_score``.
        drift_at_pick: Phase-3 drift (~15 min delayed) at decision time, or
            ``None`` — **passthrough** to the persisted candidate, not a
            validation input.

    Returns:
        A :class:`ValidationResult`. See the module docstring for the three
        outcomes. The keyword-only ``score_at_pick`` / ``drift_at_pick`` are a
        deliberate extension of the concept §2 6-arg signature so this function
        can populate the full frozen ``Candidate`` contract (annotated in the
        concept doc, dated 2026-06-05).
    """
    # 1. Valid abstain — a legitimate "no candidate" answer, not a rejection.
    if raw.get("abstain") is True:
        log.info("validator: abstain (no pick)")
        return ValidationResult(valid=True, candidate=None)

    # 2. Required fields present and non-None.
    for key in _REQUIRED_FIELDS:
        if raw.get(key) is None:
            return _reject(f"missing required field: {key!r}")

    epic = raw["epic"]
    direction = raw["direction"]
    confidence = raw["confidence"]

    # 3. ★ Epic must be in the code-provided universe (anti-hallucination core).
    if epic not in {e["epic"] for e in epic_universe}:
        return _reject(f"epic not in universe (hallucination): {epic!r}")

    # 4. Direction must be in the (already clamped) allowed set — catches old
    #    CALL/PUT leftovers and long-bias-clamp violations.
    if direction not in allowed_directions:
        return _reject(
            f"direction {direction!r} not in allowed {allowed_directions!r}"
        )

    # 5. Confidence numeric, in [0, 100], and at/above the coarse floor.
    #    ``bool`` is a subclass of ``int`` — exclude it explicitly.
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        return _reject(f"confidence not numeric: {confidence!r}")
    if not (0 <= confidence <= 100):
        return _reject(f"confidence out of range [0,100]: {confidence}")
    if confidence < threshold:
        return _reject(f"confidence {confidence} below floor {threshold}")

    # 6. ★ Fresh live-spread / tradeability recheck — the check the schema can't do.
    env = broker.get_price(epic)
    if not getattr(env, "ok", False):
        return _reject(f"live get_price not ok for {epic!r}")
    data = getattr(env, "data", None) or {}
    spread_pct = data.get("spread_pct")
    market_status = data.get("market_status")
    if spread_pct is None or market_status is None:
        return _reject(f"live price missing spread_pct/market_status for {epic!r}")
    if spread_pct > max_spread_pct:
        return _reject(
            f"live spread {spread_pct}% > max {max_spread_pct}% for {epic!r}"
        )
    if market_status != _TRADEABLE:
        return _reject(f"market_status {market_status!r} != TRADEABLE for {epic!r}")

    # 7. PASS — build the full Candidate. spread_pct_at_pick is the FRESH value.
    candidate = Candidate(
        epic=epic,
        direction=direction,
        llm_confidence=float(confidence),
        reasoning=raw.get("reasoning", ""),
        spread_pct_at_pick=float(spread_pct),
        drift_at_pick=drift_at_pick,
        score_at_pick=score_at_pick,
        threshold_applied=threshold,
        generated_at=timeutil.utc_iso_now(),
        source="research",
    )
    log.info("validator PASS: %s %s (conf=%s)", direction, epic, confidence)
    return ValidationResult(valid=True, candidate=candidate)
