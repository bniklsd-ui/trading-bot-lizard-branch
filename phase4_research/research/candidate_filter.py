"""The real deterministic gate — Phase 4's actual gating lives here.

Concept Decisions 4 + 7: the LLM's self-reported ``confidence`` is epistemically
weak (uncalibrated, systematically overconfident, ECE ~0.1) so it is **not** the
gate — it is stored as advisory data only. The gate is the deterministic logic in
this module, applied to an already-validated :class:`~research.models.Candidate`
(the validator, Step 2, ran first; this is the second, final code-side gate
before persistence).

Three pure functions, no I/O / no clock / no AI:

- :func:`confidence_threshold` — the coarse, **provisional** confidence floor
  (55 normally / 70 when the bot score is below neutral). Not a probability;
  replaced by Phase-7 outcome-anchored confidence.
- :func:`resolve_allowed_directions` — the long-bias clamp (``("BUY",)`` when the
  score is below neutral and the clamp is enabled).
- :func:`apply_filter` — the deterministic end rules a candidate must pass:
  in-universe, spread within bound, market tradeable, direction permitted, plus a
  **soft** drift-coherence sanity check (warn, never hard-reject — Phase-3 data is
  ~15 min delayed).
"""

from __future__ import annotations

import logging
from typing import Any

from research.models import Candidate, FilterVerdict, ResearchConfig, ResearchContext

log = logging.getLogger(__name__)

_TRADEABLE = "TRADEABLE"

# Neutral-score boundary for the confidence floor (concept §6 stub literal).
# Deliberately distinct from ``config.long_bias_below_score`` (the *direction*
# clamp boundary), even though both default to 50.0 — they are separate knobs.
_NEUTRAL_SCORE = 50.0

# Soft drift-coherence threshold (% drift). A pick whose direction opposes a
# drift of larger magnitude than this is *flagged* (warn), never rejected:
# Phase-3 drift is ~15 min delayed, so it is a sentiment signal, not ground
# truth (concept §6 — the bot must not tip into a "never sure" extreme). A
# blunt, deliberately generous constant; not a tuned parameter.
_DRIFT_COHERENCE_PCT = 0.5


def confidence_threshold(bot_score: float, config: ResearchConfig) -> float:
    """Return the coarse confidence floor for the current bot score.

    Below the neutral score → the stricter floor; otherwise the default. This is
    a **provisional, coarse self-report floor** (concept Decision 4), **not** a
    probability and **not** the real gate (:func:`apply_filter` is). Phase 7
    replaces it with outcome-anchored confidence.

    Args:
        bot_score: Current bot score.
        config: Carries ``confidence_floor_default`` (55) and
            ``confidence_floor_low_score`` (70).

    Returns:
        The applicable floor (e.g. 55.0 or 70.0).
    """
    return (
        config.confidence_floor_low_score
        if bot_score < _NEUTRAL_SCORE
        else config.confidence_floor_default
    )


def resolve_allowed_directions(
    bot_score: float, config: ResearchConfig
) -> tuple[str, ...]:
    """Apply the long-bias clamp to the permitted directions.

    When the clamp is enabled and ``bot_score < config.long_bias_below_score``,
    only ``("BUY",)`` is permitted (concept Decision 7 — avoid shorting into a
    weak score). Otherwise the configured ``allowed_directions`` stand. Works
    purely in BUY/SELL vocabulary — no CALL/PUT leftovers.

    Args:
        bot_score: Current bot score.
        config: Carries ``enable_long_bias_clamp``, ``long_bias_below_score`` and
            ``allowed_directions``.

    Returns:
        The effective allowed-direction tuple after the clamp.
    """
    if config.enable_long_bias_clamp and bot_score < config.long_bias_below_score:
        return ("BUY",)
    return config.allowed_directions


def _find_universe_entry(
    epic: str, tradeable_epics: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Return the universe dict for ``epic``, or ``None`` if it is absent."""
    for entry in tradeable_epics:
        if entry.get("epic") == epic:
            return entry
    return None


def _fail(rule: str, reason: str, **details: Any) -> FilterVerdict:
    """Build a hard-reject verdict and log it to stderr (never swallow)."""
    log.info("candidate_filter REJECT [%s]: %s", rule, reason)
    return FilterVerdict(ok=False, rule=rule, reason=reason, details=details)


def apply_filter(
    candidate: Candidate, context: ResearchContext, config: ResearchConfig
) -> FilterVerdict:
    """Run the deterministic end rules against an already-validated candidate.

    Runs **after** the validator (Step 2) and is the final code-side gate before
    a candidate is persisted as a pick. The checks (in order; first hard fail
    short-circuits):

    1. **In universe** — ``candidate.epic`` must be present in
       ``context.tradeable_epics``. Defense-in-depth: the validator already
       checked membership, but the filter never trusts an upstream check.
    2. **Spread** — the universe entry's ``spread_pct`` must be
       ``<= config.max_spread_pct``.
    3. **Tradeable** — the universe entry's ``market_status`` must be
       ``"TRADEABLE"``.
    4. **Direction** — ``candidate.direction`` must be in the clamped allowed set
       (:func:`resolve_allowed_directions` on ``context.bot_score``).
    5. **Soft drift-coherence** — if ``brain_context["drift_pct"]`` is available
       and the direction opposes a drift of magnitude beyond
       ``_DRIFT_COHERENCE_PCT``, return a **passing** verdict carrying a
       ``drift_coherence_warn`` rule (Phase-3 drift is delayed → warn, never
       reject).

    Args:
        candidate: The validated candidate to gate.
        context: The deterministic research context (universe, score, brain).
        config: Tunables (spread bound, clamp, floors).

    Returns:
        A :class:`FilterVerdict`. ``ok=False`` with the failing ``rule`` on a hard
        reject; ``ok=True`` (optionally with a ``drift_coherence_warn`` rule) on a
        pass.
    """
    # 1. In universe (defense-in-depth — never trust the upstream validator).
    entry = _find_universe_entry(candidate.epic, context.tradeable_epics)
    if entry is None:
        return _fail(
            "epic_not_in_universe",
            f"epic {candidate.epic!r} not in tradeable universe",
        )

    # 2. Spread within bound (confirms the already-vetted universe entry).
    spread_pct = entry.get("spread_pct")
    if spread_pct is None or spread_pct > config.max_spread_pct:
        return _fail(
            "spread_too_wide",
            f"spread {spread_pct}% > max {config.max_spread_pct}% for {candidate.epic!r}",
            spread_pct=spread_pct,
        )

    # 3. Market tradeable.
    market_status = entry.get("market_status")
    if market_status != _TRADEABLE:
        return _fail(
            "not_tradeable",
            f"market_status {market_status!r} != TRADEABLE for {candidate.epic!r}",
            market_status=market_status,
        )

    # 4. Direction in the clamped allowed set.
    allowed = resolve_allowed_directions(context.bot_score, config)
    if candidate.direction not in allowed:
        return _fail(
            "direction_not_allowed",
            f"direction {candidate.direction!r} not in allowed {allowed!r} "
            f"(score {context.bot_score})",
            direction=candidate.direction,
            allowed=allowed,
        )

    # 5. Soft drift-coherence sanity — warn, NEVER hard-reject (delayed data).
    brain = context.brain_context or {}
    drift_pct = brain.get("drift_pct")
    if drift_pct is not None:
        incoherent = (
            candidate.direction == "SELL" and drift_pct > _DRIFT_COHERENCE_PCT
        ) or (
            candidate.direction == "BUY" and drift_pct < -_DRIFT_COHERENCE_PCT
        )
        if incoherent:
            reason = (
                f"{candidate.direction} vs delayed drift {drift_pct}% "
                f"(|drift| > {_DRIFT_COHERENCE_PCT}%) — soft warn, not a reject"
            )
            log.info("candidate_filter WARN [drift_coherence_warn]: %s", reason)
            return FilterVerdict(
                ok=True,
                rule="drift_coherence_warn",
                reason=reason,
                details={"drift_pct": drift_pct},
            )

    log.info("candidate_filter PASS: %s %s", candidate.direction, candidate.epic)
    return FilterVerdict(ok=True)
