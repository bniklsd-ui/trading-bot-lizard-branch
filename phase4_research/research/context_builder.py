"""Context assembly — the deterministic input side of the research pipeline.

``build_context`` gathers everything the prompt builder (Step 4) needs into a
single :class:`~research.models.ResearchContext`, drawing from the three upstream
phases:

- **Phase 1** broker probes — for each allow-listed epic, a fresh ``get_price`` +
  ``get_market_info``, kept only if the live quote is tradeable (TRADEABLE,
  spread within the configured cap, EUR).
- **Phase 2** persistence reads — recent trades, active lessons, bot score, risk
  level.
- **Phase 3** brain context — the anchor epic's delayed market snapshot
  (``to_prompt_dict()``), tolerated honestly with its ``None`` fields.

**This is 100% code — no AI touches it** (root CLAUDE.md "Bauprinzip"). The single
AI step is the LLM call in Step 5; here we only assemble its input.

Phase isolation is preserved exactly as the validator established it: collaborators
are typed via local :class:`typing.Protocol` surfaces, so this module imports
**nothing** from ``broker_wrapper`` / ``persistence`` / ``external_data``. The
Phase-3 ``EpicNotMappedError`` guard matches by **class name** (the codebase's
isolation-preserving pattern, mirroring Phase-3's name-matching of
``YFRateLimitError``) rather than importing the exception.

Concept reference: ``docs/concepts/phase4_research_plan_konzept.md`` §3. The
tradeability check is the §3-sanctioned "check ``spread_pct``/``market_status``
directly off ``env.data``" option (not a ``Price``/``MarketInfo`` reconstruction +
``is_tradeable`` call) — consistent with the validator's inline recheck and the
no-``broker_wrapper``-import isolation stance.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol

from research.models import ResearchConfig, ResearchContext

log = logging.getLogger(__name__)

_TRADEABLE = "TRADEABLE"
# The EUR-account hard rule (root CLAUDE.md) + FilterConfig.require_currency
# default. The allow-list is code-curated DAX-CFD epics, all EUR; this is a cheap
# defensive sanity check, not a discovery filter.
_REQUIRED_CURRENCY = "EUR"


class _BrokerLike(Protocol):
    """Minimal broker surface the universe probe needs (Envelope-returning).

    Typed as a Protocol so Phase 4 does not import ``broker_wrapper`` (phase
    isolation). The real ``IGAdapter`` and the test ``FakeBroker`` both satisfy
    it. Each method returns an Envelope-like object exposing ``.ok`` (bool) and
    ``.data`` (dict).
    """

    def get_price(self, epic: str) -> Any: ...

    def get_market_info(self, epic: str) -> Any: ...


class _DBLike(Protocol):
    """Minimal Phase-2 ``Database`` surface for the research context reads."""

    def get_recent_trades(self, n: int = ...) -> list[dict[str, Any]]: ...

    def get_recent_lessons(self, n: int = ...) -> list[dict[str, Any]]: ...

    # v1.5 (Phase-8 hotfix Step 4 A): provenance-/quality-filtered lesson selection for the
    # prompt (keeps verification-trade lessons out). Kept separate from ``get_recent_lessons``.
    def get_recent_lessons_for_prompt(
        self,
        n: int = ...,
        *,
        min_hold_min: float | None = ...,
        quarantine_before: str | None = ...,
        exclude_provenance: tuple[str, ...] = ...,
    ) -> list[dict[str, Any]]: ...

    def get_current_score(self) -> float: ...

    def get_risk_level(self) -> str: ...


class _FetcherLike(Protocol):
    """Minimal Phase-3 ``MarketDataFetcher`` surface for the brain context.

    ``get_brain_context`` returns an object exposing ``to_prompt_dict()`` (or
    ``None``), and propagates an ``EpicNotMappedError`` for an unmapped epic —
    caught here by class name, not by import.
    """

    def get_brain_context(self, epic: str) -> Any: ...


def _probe_epic(broker: _BrokerLike, epic: str, max_spread_pct: float) -> dict[str, Any] | None:
    """Probe one epic; return its universe dict if tradeable, else ``None``.

    Always checks ``env.ok`` before touching ``env.data``. A non-ok envelope,
    a closed/untradeable market, a spread above the cap, a non-EUR currency, or a
    missing field all mean "leave this epic out" — logged to stderr, never raised.
    """
    price_env = broker.get_price(epic)
    if not getattr(price_env, "ok", False):
        log.info("context: get_price not ok for %s — skipping", epic)
        return None
    info_env = broker.get_market_info(epic)
    if not getattr(info_env, "ok", False):
        log.info("context: get_market_info not ok for %s — skipping", epic)
        return None

    price = getattr(price_env, "data", None) or {}
    info = getattr(info_env, "data", None) or {}

    spread_pct = price.get("spread_pct")
    market_status = price.get("market_status")
    currency = info.get("currency")
    if spread_pct is None or market_status is None:
        log.info("context: live price missing spread_pct/market_status for %s — skipping", epic)
        return None

    if market_status != _TRADEABLE:
        log.info("context: %s not TRADEABLE (status=%s) — skipping", epic, market_status)
        return None
    if spread_pct > max_spread_pct:
        log.info("context: %s spread %.3f%% > max %s%% — skipping", epic, spread_pct, max_spread_pct)
        return None
    if currency != _REQUIRED_CURRENCY:
        log.info("context: %s currency %r != %s — skipping", epic, currency, _REQUIRED_CURRENCY)
        return None

    return {
        "epic": epic,
        "name": info.get("name"),
        "spread_pct": spread_pct,
        "market_status": market_status,
        "min_deal_size": info.get("min_deal_size"),
    }


def _safe_brain_context(
    market_data: _FetcherLike, anchor_epic: str
) -> tuple[dict[str, Any] | None, dict[str, str]]:
    """Fetch one epic's Phase-3 prompt dict, degrading to ``None`` safely.

    Guards the documented Phase-3 failure mode: ``get_brain_context`` propagates
    an ``EpicNotMappedError`` for an unmapped epic. That is caught **by class
    name** (phase isolation — no ``external_data`` import) and degraded to
    ``None`` with a warning; any other exception re-raises (never swallow
    silently). For a mapped epic the call practically never returns ``None``, but
    the defensive ``is None`` check is kept anyway.

    Returns:
        A ``(prompt_dict, field_errors)`` pair. v1.6 (Phase-8 hotfix Step 0,
        observability): ``field_errors`` mirrors the Phase-3
        ``BrainContext.field_errors`` (label → exception text for a degraded
        sub-indicator), read via ``getattr`` since ``get_brain_context``'s return
        is duck-typed ``Any`` here (phase isolation) — a fake without the
        attribute (pre-v1.6 test doubles) degrades to ``{}``, never crashes.
        ``({}, {})``-shaped on either guard branch (unmapped epic / ``None``
        context) since there is nothing to report per-field in those cases.
    """
    try:
        bc = market_data.get_brain_context(anchor_epic)
    except Exception as exc:  # noqa: BLE001 — re-raised unless it's the known guard case
        if type(exc).__name__ != "EpicNotMappedError":
            raise
        log.warning("context: brain context unavailable for %s (unmapped epic: %s)", anchor_epic, exc)
        return None, {}
    if bc is None:
        log.warning("context: brain context is None for %s — degrading", anchor_epic)
        return None, {}
    field_errors = dict(getattr(bc, "field_errors", None) or {})
    return bc.to_prompt_dict(), field_errors


def _brain_health(prompt_dict: dict[str, Any] | None, field_errors: dict[str, str]) -> dict[str, Any]:
    """Derive a v1.6 (Step 0) diagnostic health summary from one epic's snapshot.

    Purely a function of the already-honest ``None``-gaps in ``to_prompt_dict()``
    (no new Phase-3 data needed for the "which field" half) plus the exception text
    Phase-3 now captures (the "why" half). Never gates anything — diagnostic-only.
    """
    if prompt_dict is None:
        return {"status": "unavailable"}
    missing: list[str] = []
    if prompt_dict.get("drift_pct") is None:
        missing.append("drift")
    if prompt_dict.get("momentum_15m_pct") is None:
        missing.append("momentum")
    if prompt_dict.get("volume_z_score") is None:
        missing.append("volume")
    if prompt_dict.get("distance_to_high_pct") is None or prompt_dict.get("distance_to_low_pct") is None:
        missing.append("high_low")
    if prompt_dict.get("range_30d") is None:
        missing.append("history")
    return {
        "status": "degraded" if missing else "full",
        "missing": missing,
        "errors": dict(field_errors),
    }


def build_context(
    broker: _BrokerLike,
    db: _DBLike,
    market_data: _FetcherLike,
    config: ResearchConfig,
) -> ResearchContext:
    """Assemble the deterministic research context from P1/P2/P3.

    Args:
        broker: Phase-1 broker adapter (Envelope-returning) for the universe probe.
        db: Phase-2 ``Database`` for trades / lessons / score / risk level.
        market_data: Phase-3 ``MarketDataFetcher`` for the anchor brain context.
        config: The run config — drives ``epic_allowlist`` and ``max_spread_pct``.

    Returns:
        A :class:`ResearchContext`. ``tradeable_epics`` may be empty (market
        closed / nothing tradeable) — a valid result the orchestrator (Step 7)
        treats as the abstain path, not an error. Every indicator value in
        ``brain_context`` is passed through verbatim (``None`` stays ``None`` —
        never faked to ``0``); ``brain_context`` itself is ``None`` when the
        anchor epic's snapshot could not be built.
    """
    anchor_epic = config.epic_allowlist[0]

    tradeable_epics: list[dict[str, Any]] = []
    for epic in config.epic_allowlist:
        probed = _probe_epic(broker, epic, config.max_spread_pct)
        if probed is not None:
            tradeable_epics.append(probed)

    recent_trades = db.get_recent_trades(8)
    # v1.5 (Phase-8 hotfix Step 4 A): filter verification-trade lessons out of the prompt.
    # Precise provenance tag (written since v1.5) + hold-time fallback (catches pre-tag
    # polluted lessons) + optional reversible date quarantine — all driven by config, applied
    # in the query so we still get the newest 5 *surviving* lessons. Only the prompt is
    # cleaned; the reward/score math never reads these (root rule 3).
    recent_lessons = db.get_recent_lessons_for_prompt(
        5,
        min_hold_min=config.lesson_min_hold_min,
        quarantine_before=config.lesson_quarantine_before,
        exclude_provenance=config.lesson_exclude_provenance,
    )
    bot_score = db.get_current_score()
    risk_level = db.get_risk_level()

    # v1.5 (Issue C): fetch a delayed brain snapshot for EACH tradeable epic (plus the
    # anchor, so ``brain_context`` stays populated even when the anchor is untradeable
    # this cycle). Order-preserving, de-duplicated. Each fetch degrades to ``None`` on
    # its own (unmapped epic / off-hours) — one epic's missing data never blocks another
    # (concept C3 reduced-signal, tolerated).
    epics_needing_brain = list(
        dict.fromkeys([e["epic"] for e in tradeable_epics] + [anchor_epic])
    )
    brain_contexts: dict[str, dict[str, Any] | None] = {}
    # v1.6 (Phase-8 hotfix Step 0, observability): a per-epic diagnostic summary
    # assembled alongside brain_contexts, from the same fetch — no extra Phase-3
    # calls. Display/diagnostic-only (root rule 3: gates nothing).
    brain_context_health: dict[str, dict[str, Any]] = {}
    for epic in epics_needing_brain:
        prompt_dict, field_errors = _safe_brain_context(market_data, epic)
        brain_contexts[epic] = prompt_dict
        brain_context_health[epic] = _brain_health(prompt_dict, field_errors)
    brain_context = brain_contexts.get(anchor_epic)

    n_present = sum(1 for v in brain_contexts.values() if v is not None)
    log.info(
        "context built: %d tradeable epic(s), score=%s, risk=%s, brain=%d/%d present",
        len(tradeable_epics),
        bot_score,
        risk_level,
        n_present,
        len(brain_contexts),
    )

    return ResearchContext(
        tradeable_epics=tradeable_epics,
        recent_trades=recent_trades,
        recent_lessons=recent_lessons,
        bot_score=bot_score,
        risk_level=risk_level,
        brain_context=brain_context,
        anchor_epic=anchor_epic,
        brain_contexts=brain_contexts,
        brain_context_health=brain_context_health,
    )
