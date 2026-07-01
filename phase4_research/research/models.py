"""Data contracts for the Phase 4 research layer.

These types are the integration surface for the research pipeline:

- :class:`Candidate` is the **Phase 4 → Phase 5 contract** — exactly the dict
  shape persisted to ``turbo_candidates.json`` via
  ``StateManager.save_candidates([candidate.to_dict()])``. Phase 5's Gate 2 reads
  it back, so the field set is frozen here.
- :class:`ResearchContext` is the deterministic, code-built bundle the prompt
  builder (Step 4) consumes — no AI touches its construction.
- :class:`ValidationResult` is the output of the hallucination-guard validator
  (Step 2).
- :class:`ResearchConfig` carries every tunable, including the token-meter
  pricing (Step 5 consumes it; the fields live here so config is single-sourced).

This module is **types only — no logic, no I/O, no network**. It deliberately
imports nothing from Phase 1/2/3 (phase isolation; cross-phase data crosses as
plain dicts / the Envelope JSON). Repo conventions apply:
``from __future__ import annotations``, type hints + docstrings everywhere.

Direction vocabulary is **BUY / SELL** throughout — exactly what
``ig_adapter.open_position()`` enforces (concept Decision 1). There is no
CALL/PUT anywhere: this is a DAX CFD bot, the options terminology is dead.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions (own typed hierarchy — concept §1, mirrors Phase-1/3 pattern)
# ---------------------------------------------------------------------------


class ResearchError(Exception):
    """Base class for all Phase-4 research errors.

    Carries a ``code`` class attribute so callers can catch the whole family
    with one ``except`` or be specific. Independent of the Phase-1/3
    hierarchies (phase isolation).
    """

    code: str = "RESEARCH_ERROR"


class LLMResponseError(ResearchError):
    """The LLM call failed unrecoverably (after the single permitted retry).

    Raised by the LLM client (Step 5) when, even after one retry on a
    *transient* fault (network / timeout / 5xx / parse- or schema-fail), no
    usable structured response could be obtained. The orchestrator treats this
    as an abstain — it writes ``save_candidates([])`` (no blind trade), never a
    fabricated candidate (concept Decision 8).
    """

    code = "LLM_RESPONSE_ERROR"


class ResearchAbort(ResearchError):
    """A pre-flight session-health check failed; no research is attempted.

    Raised by the orchestrator (Step 7) when broker connectivity / account /
    anchor-epic tradeability is not satisfied. Like every other failure path it
    resolves to ``save_candidates([])`` — a hard ``ValueError`` from
    ``open_position`` downstream is far worse than an honest empty list.
    """

    code = "RESEARCH_ABORT"


# ---------------------------------------------------------------------------
# Candidate — the Phase 4 → Phase 5 contract (frozen field set)
# ---------------------------------------------------------------------------


@dataclass
class Candidate:
    """One research pick, ready to persist as a candidate dict.

    The field set is the **stable contract** consumed by Phase 5 Gate 2. An
    abstain / reject does **not** produce a ``Candidate`` — it produces an empty
    candidate list (``save_candidates([])``); there is no ``abstain`` field on a
    persisted candidate.

    The split is intentional (concept "Der Candidate-Contract"):

    - ``llm_confidence`` is the model's **self-report** — advisory, uncalibrated
      (research shows LLM confidence is systematically overconfident, ECE ~0.1).
      It is stored as raw data, **not** used as the real gate. The real gate is
      the deterministic ``candidate_filter`` (Step 6). Phase 7 will later
      correlate this field against actual outcomes to build outcome-anchored
      confidence — which is exactly why it is preserved verbatim.
    - ``spread_pct_at_pick`` / ``drift_at_pick`` / ``score_at_pick`` are
      **code-captured hard facts** at decision time, kept separate from the
      self-report.

    Attributes:
        epic: IG epic, taken verbatim from the code-provided tradeable universe.
        direction: ``"BUY"`` or ``"SELL"`` — broker vocabulary, flows straight
            into ``open_position`` with no mapping.
        llm_confidence: 0-100 LLM self-report. **Advisory, uncalibrated.**
        reasoning: 2-3 sentence rationale from the LLM.
        spread_pct_at_pick: Live spread % captured by code at validation time
            (fresh ``get_price``), not from the model.
        drift_at_pick: Phase-3 drift context (~15 min delayed); ``None`` when the
            indicator was unavailable (off-hours / no history).
        score_at_pick: Bot score at the decision moment.
        threshold_applied: The confidence floor applied (55 default / 70 when
            ``bot_score < 50``). **Provisional** — a coarse self-report floor,
            replaced by Phase-7 outcome-anchored confidence. Not a probability.
        generated_at: ISO 8601 UTC timestamp.
        source: Provenance tag; always ``"research"`` for this layer.
    """

    epic: str
    direction: str  # "BUY" | "SELL" — enforced downstream by open_position
    llm_confidence: float  # 0-100, LLM self-report — ADVISORY, uncalibrated
    reasoning: str
    spread_pct_at_pick: float
    drift_at_pick: float | None
    score_at_pick: float
    threshold_applied: float
    generated_at: str
    source: str = "research"

    def to_dict(self) -> dict[str, Any]:
        """Serialise to the plain dict persisted via ``save_candidates``.

        Returns a JSON-serialisable dict with exactly the contract keys (no
        extra fields), suitable for ``StateManager.save_candidates([...])``.
        """
        return asdict(self)


# ---------------------------------------------------------------------------
# ResearchContext — deterministic, code-built prompt input
# ---------------------------------------------------------------------------


@dataclass
class ResearchContext:
    """Everything the prompt builder needs, assembled entirely by code.

    Built by ``context_builder.build_context`` (Step 3) from Phase-1 broker
    probes, Phase-2 persistence reads, and the Phase-3 brain context. No AI
    participates in its construction.

    Attributes:
        tradeable_epics: The code-vetted universe. Each item is a dict
            ``{epic, name, spread_pct, market_status, min_deal_size}``. The LLM
            may pick **only** from these epics; an empty list is the abstain
            path (market closed / nothing tradeable).
        recent_trades: Up to 8 recent trades (Phase-2 ``get_recent_trades``).
        recent_lessons: Up to 5 active lessons (Phase-2 ``get_recent_lessons``).
        bot_score: Current bot score (drives the confidence floor + long-bias
            clamp).
        risk_level: Current risk level string (Phase-2 ``get_risk_level``).
        brain_context: The anchor epic's Phase-3 ``to_prompt_dict()`` — the
            **10-key** set incl. ``generated_at`` (Step 0.5). Any indicator value
            may be ``None`` (off-hours / unavailable); rendered honestly, never
            faked to ``0``. ``None`` for the whole dict when the brain context
            could not be built (e.g. unmapped epic degraded).
        anchor_epic: The epic the brain context describes (default-allowlist
            anchor, ``IX.D.DAX.IFMM.IP``).
        brain_contexts: v1.5 (Issue C) — the per-epic delayed snapshots, keyed by
            epic (each value is a ``to_prompt_dict()`` or ``None`` when unavailable
            / unmapped). ``brain_context`` above stays the **anchor** view for
            back-compat; multi-epic consumers (prompt render, drift-coherence) read
            the candidate's own epic from here. Defaults to ``{}`` so callers built
            before v1.5 keep working (they fall back to ``brain_context``).
    """

    tradeable_epics: list[dict[str, Any]]
    recent_trades: list[dict[str, Any]]
    recent_lessons: list[dict[str, Any]]
    bot_score: float
    risk_level: str
    brain_context: dict[str, Any] | None
    anchor_epic: str
    brain_contexts: dict[str, dict[str, Any] | None] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# ValidationResult — output of the hallucination-guard validator (Step 2)
# ---------------------------------------------------------------------------


@dataclass
class ValidationResult:
    """Result of validating a raw LLM pick against the real universe.

    A valid abstain is represented as ``valid=True, candidate=None`` (a
    legitimate "no candidate" answer, not a rejection). A content rejection
    (hallucinated epic, bad direction, sub-floor confidence, live-spread fail)
    is ``valid=False`` with a human-readable ``rejected_reason``.

    Attributes:
        valid: ``True`` for a clean pick **or** a valid abstain; ``False`` for a
            rejection.
        candidate: The built :class:`Candidate` on a clean pick; ``None`` for a
            valid abstain **or** a rejection.
        rejected_reason: Why the pick was rejected; ``None`` when ``valid``.
    """

    valid: bool
    candidate: Candidate | None
    rejected_reason: str | None = None


# ---------------------------------------------------------------------------
# FilterVerdict — output of the deterministic candidate filter (Step 6)
# ---------------------------------------------------------------------------


@dataclass
class FilterVerdict:
    """Result of the deterministic ``candidate_filter`` — the **real** gate.

    Defined **locally** (phase isolation — Phase 4 imports nothing from
    ``broker_wrapper``) but deliberately mirrors the shape of Phase-1's
    ``broker_wrapper.filters.FilterVerdict`` (``ok / rule / reason / details``)
    so the convention reads the same across phases.

    This is where Phase 4 does its real gating (concept Decisions 4 + 7), **not**
    on the LLM's self-reported confidence (which is advisory only). A candidate
    must pass this filter before it is persisted as a pick.

    Soft-warn convention: ``ok=True`` **with** a ``rule`` set means "passed, but
    with a coherence warning" — used for the soft drift-coherence sanity check.
    Phase-3 data is ~15 min delayed, so a direction that looks incoherent with
    delayed drift is flagged, **never** hard-rejected (concept §6: the bot must
    not tip into a "never sure" extreme). A hard fail is ``ok=False`` with the
    failing ``rule``.

    Attributes:
        ok: ``True`` if the candidate passes the gate (possibly with a warn
            ``rule``); ``False`` for a hard rejection.
        rule: The failing rule on a hard reject, **or** a soft-warn marker when
            ``ok=True``; ``None`` for a clean pass.
        reason: Human-readable explanation; ``None`` for a clean pass.
        details: Optional structured context (e.g. the observed ``drift_pct``).
    """

    ok: bool
    rule: str | None = None
    reason: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# InstrumentSpec + load_universe — the typed, validated research universe (v1.5)
# ---------------------------------------------------------------------------
#
# ⚠ This module is otherwise "types only — no logic, no I/O" (see the module
# docstring). ``load_universe`` is a small, pure **validating loader** (its only
# side effect is a stderr ``logger.warning`` on a dropped entry) added in the
# Phase-8 v1.5 hotfix (Issue C — variety). It lives here so the universe type and
# its validation are single-sourced next to ``ResearchConfig`` (which consumes it),
# and so there is no circular import between a separate module and ``ResearchConfig``.


@dataclass(frozen=True)
class InstrumentSpec:
    """One curated tradeable instrument in the research universe (v1.5 Issue C).

    Replaces the bare ``epic_allowlist`` tuple with a typed, validated entry so the
    universe can grow beyond the single DAX epic. This is the **deterministic seam**
    a future P9 research step will extend (validated ``source="research_promoted"``
    entries appended via a deterministic validate→promote path, mirroring the
    Instinct→VETO ECC) — **no AI is wired into universe selection in v1.5**; the
    universe stays code-curated (concept Decision 5, "no ``search_markets`` dragnet").

    Attributes:
        epic: IG epic string (demo-account-specific; resolved once via the operator
            ``scripts/resolve_epics.py`` read-only resolver — never guessed).
        yf_ticker: yFinance symbol for the P3 brain context, or ``None``. Registered
            on the ``TickerMapper`` in wiring. ``None`` → no brain context for this
            epic (reduced-signal, tolerated — concept C3), never a crash.
        volume_proxy: ETF symbol supplying volume for an index that reports none
            (e.g. DAX ``^GDAXI`` → ``EXS1.DE``), or ``None`` (``volume_z_score``
            stays ``None`` — tolerated).
        point_value: Account-currency value of one index point (DAX cash CFD =
            1 €/pt). Used by P5 Gate-4 sizing (``risk / (stop_pts × point_value)``).
            **Provisional for non-DAX until confirmed via ``resolve_epics.py``.**
        min_deal_size: Curated sanity value for the minimum tradeable size. Advisory
            — P5 sizing reads the authoritative ``min_deal_size`` from the broker's
            ``get_market_info`` at runtime; this documents the expected floor.
        currency: Must be ``"EUR"`` (root hard rule — EUR account; concept C2).
        source: Provenance — ``"curated"`` now; ``"research_promoted"`` reserved
            for P9. Documents where an entry came from; no behaviour attached in v1.5.
    """

    epic: str
    yf_ticker: str | None
    volume_proxy: str | None
    point_value: float
    min_deal_size: float
    currency: str = "EUR"
    source: str = "curated"


_REQUIRED_UNIVERSE_CURRENCY = "EUR"

# The default code-curated universe: the single confirmed DAX-CFD epic, matching the
# pre-v1.5 ``epic_allowlist``/``volume_proxy`` defaults exactly (default path
# bit-identical). Siblings (Euro Stoxx 50 / CAC 40 …) are appended in v1.5 Step 2B
# once the operator confirms their epic strings on IG demo.
_DEFAULT_UNIVERSE: tuple[InstrumentSpec, ...] = (
    InstrumentSpec(
        epic="IX.D.DAX.IFMM.IP",
        yf_ticker="^GDAXI",
        volume_proxy="EXS1.DE",
        point_value=1.0,
        min_deal_size=0.5,
        currency="EUR",
        source="curated",
    ),
)

# v1.5 Issue C, Step 2B (2026-07-01) — the confirmed multi-instrument universe. Public
# (unlike ``_DEFAULT_UNIVERSE``) so the wiring layer — the only place cross-phase config
# choices belong — can opt the daemon/live builds into it explicitly. A bare
# ``ResearchConfig()`` still defaults to ``_DEFAULT_UNIVERSE`` (DAX-only, unchanged), so
# no existing caller/test needs to change; only ``scripts/wiring.py`` (P4 + P8) passes
# ``universe=EXTENDED_UNIVERSE`` in.
#
# DAX epic/point_value/min_deal_size/ticker/proxy are the pre-v1.5 values, reused as-is.
# Euro Stoxx 50 (``IX.D.STXE.IFM.IP``) was resolved via the operator's
# ``scripts/resolve_epics.py`` run against IG demo (2026-07-01): currency/min_deal_size/
# market_status=TRADEABLE/ohlcv_available=True are all **live-confirmed**. Two fields are
# NOT independently confirmed, flagged below — re-verify before trusting this instrument
# in a live run:
#   - point_value=2.0 is INFERRED from IG's "(2€)" cash-instrument name, by analogy with
#     the verified DAX pattern (name "(1€)" <-> point_value=1.0, and lot_size==1.0 matches
#     it exactly). Not independently confirmed via a contract-spec page or a manual trade.
#   - yf_ticker="^STOXX50E" / volume_proxy="EXW1.DE" are the well-known public Yahoo
#     Finance / iShares Core EURO STOXX 50 UCITS ETF symbols (by analogy with DAX's
#     ^GDAXI / EXS1.DE), NOT live-verified against yfinance. Operator: verify with
#     `python phase3_external_data/scripts/smoke_test.py --epic IX.D.STXE.IFM.IP
#     --volume-proxy EXW1.DE` before trusting the brain-context signal for this epic.
#
# CAC 40 / AEX / IBEX 35 are deliberately NOT added yet — the 2026-07-01 resolve_epics.py
# run's tail (France 40 onward) shows a rate-limiting cascade (get_market_info failing
# outright for 3/4 CAC hits, ohlcv_available=False for the one that resolved, both
# remaining search terms failing outright) after ~35 unthrottled back-to-back broker
# calls. Confirming CAC 40's `ohlcv_available` matters: VETO 3 fails closed on missing
# bars, so an epic without real-time OHLCV would never clear the momentum VETO and could
# never actually trade — a silent "phantom" instrument. resolve_epics.py now paces itself
# (see its module docstring); re-run it for a clean read before adding these.
EXTENDED_UNIVERSE: tuple[InstrumentSpec, ...] = (
    _DEFAULT_UNIVERSE[0],  # DAX, unchanged
    InstrumentSpec(
        epic="IX.D.STXE.IFM.IP",
        yf_ticker="^STOXX50E",
        volume_proxy="EXW1.DE",
        point_value=2.0,
        min_deal_size=0.5,
        currency="EUR",
        source="curated",
    ),
)


def _validate_spec(spec: InstrumentSpec) -> list[str]:
    """Return a list of problems with ``spec`` (empty list = valid)."""
    problems: list[str] = []
    if not isinstance(spec.epic, str) or not spec.epic.strip():
        problems.append("epic empty")
    if spec.currency != _REQUIRED_UNIVERSE_CURRENCY:
        problems.append(f"currency {spec.currency!r} != {_REQUIRED_UNIVERSE_CURRENCY} (EUR-only)")
    if not (isinstance(spec.point_value, (int, float)) and spec.point_value > 0):
        problems.append(f"point_value {spec.point_value!r} not > 0")
    if not (isinstance(spec.min_deal_size, (int, float)) and spec.min_deal_size > 0):
        problems.append(f"min_deal_size {spec.min_deal_size!r} not > 0")
    return problems


def load_universe(specs: Any) -> tuple[InstrumentSpec, ...]:
    """Validate a sequence of :class:`InstrumentSpec` into the runnable universe.

    Fail-closed per entry: a malformed spec (non-EUR, empty epic, non-positive
    ``point_value``/``min_deal_size``) is **dropped** with a ``logger.warning`` —
    never silently passed, never used. If **every** entry drops (or the input is
    empty) a :class:`ValueError` is raised: an empty universe is a configuration
    error the caller must see, not a silent no-trade forever.

    Args:
        specs: An iterable of :class:`InstrumentSpec`.

    Returns:
        The validated, order-preserving universe tuple (at least one entry).

    Raises:
        ValueError: if no valid instrument remains.
    """
    validated: list[InstrumentSpec] = []
    for spec in specs:
        problems = _validate_spec(spec)
        if problems:
            log.warning(
                "load_universe: dropping malformed InstrumentSpec %r: %s",
                getattr(spec, "epic", "?"),
                "; ".join(problems),
            )
            continue
        validated.append(spec)
    if not validated:
        raise ValueError("load_universe: no valid instruments in the universe (all dropped / empty)")
    return tuple(validated)


def _derive_universe(
    epic_allowlist: tuple[str, ...], volume_proxy: str | None
) -> tuple[InstrumentSpec, ...]:
    """Build a validated universe from the legacy ``epic_allowlist``/``volume_proxy``.

    Backward-compat path for callers that still construct ``ResearchConfig`` with
    ``epic_allowlist=(...)`` (scripts, tests). The known DAX anchor keeps its
    ``^GDAXI`` / ``EXS1.DE`` mapping; any other epic degrades to ``yf_ticker=None``
    (reduced-signal, tolerated) with the configured ``volume_proxy`` applied only to
    the first (anchor) epic — mirroring the pre-v1.5 wiring behaviour exactly.
    """
    specs: list[InstrumentSpec] = []
    for i, epic in enumerate(epic_allowlist):
        if epic == "IX.D.DAX.IFMM.IP":
            specs.append(
                InstrumentSpec(epic, "^GDAXI", volume_proxy, 1.0, 0.5, "EUR", "curated")
            )
        else:
            specs.append(
                InstrumentSpec(
                    epic, None, volume_proxy if i == 0 else None, 1.0, 0.5, "EUR", "curated"
                )
            )
    return load_universe(specs)


# ---------------------------------------------------------------------------
# ResearchConfig — every tunable in one place
# ---------------------------------------------------------------------------

# Per-model Anthropic pricing in USD per **million** tokens, as
# ``(input_per_Mtok, output_per_Mtok)``.
#
# ⚠ PRICING AS OF 2026-06-08 — verify against Anthropic's pricing page before
# trusting any cost figure. These are estimates used only for the token meter's
# advisory cost log (Step 5); they never gate a trade. Update here when pricing
# changes; the meter reads whatever is in the config.
#
# corrected 2026-06-08 (Step 5): Opus 4.8 is $5/$25 per 1M (the recent price
# drop), not the old $15/$75 — fixed below. Sonnet 4.6 ($3/$15) and Haiku 4.5
# ($1/$5) re-verified and unchanged. The default model is claude-sonnet-4-6, so
# this row is only exercised when the config names Opus.
_DEFAULT_PRICING_USD_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-opus-4-8": (5.0, 25.0),
    "claude-haiku-4-5-20251001": (1.0, 5.0),
}


@dataclass
class ResearchConfig:
    """All tunables for the research pipeline (concept §1 + token meter).

    Defaults are the locked Phase-4 decisions. Nothing here is hard-coded into
    logic modules — they all read from a ``ResearchConfig`` instance so a single
    config object configures the whole run (and tests can override freely).

    LLM / decoding:
        model: Anthropic model id. Default ``claude-sonnet-4-6`` (the concept's
            old ``claude-sonnet-4-20250514`` string is stale). Configurable, not
            hard-coded in the client.
        max_tokens / temperature / timeout_s: standard decoding knobs.

    Universe / direction:
        epic_allowlist: Code-curated universe (Decision 5 — no
            ``search_markets`` dragnet). Default is the single confirmed DAX-CFD
            epic; room for 1-2 curated siblings (which then also need a
            ``TickerMapper`` entry — see concept Step 0.5).
        allowed_directions: Default both. Clamped to ``("BUY",)`` by the
            long-bias rule below **only when that clamp is enabled** (v1.5:
            disabled by default — see ``enable_long_bias_clamp``).
        long_bias_below_score / enable_long_bias_clamp: when the clamp is on and
            ``bot_score < long_bias_below_score``, only ``BUY`` is allowed. ⚠
            **v1.5 (2026-07-01): the clamp is OFF by default** (was Decision-7
            ON) for demo data-collection — every observed ``bot_score`` sits
            below 50, so the clamp force-abstained every cycle. With it off, the
            P6 debate + the 4 VETOs do the direction check. Re-baseline (re-enable)
            before any live account.
        max_spread_pct: live-spread rejection threshold (% of ask).
        volume_proxy: ETF symbol supplying volume for ``^GDAXI`` (which reports
            none natively); registered on the fetcher in wiring (Step 8). ``None``
            disables the proxy → ``volume_z_score`` stays ``None``.

    Confidence floor (PROVISIONAL — Decision 4; Phase-7 outcome-anchoring replaces it):
        confidence_floor_below_score: the score boundary below which the stricter
            ``confidence_floor_low_score`` applies (else ``confidence_floor_default``).
            v1.5 made this its **own config field** so the floor boundary is now
            **decoupled** from the direction-clamp boundary (``long_bias_below_score``) —
            previously it was a hardcoded ``candidate_filter._NEUTRAL_SCORE`` literal that
            happened to share 50.0. The two are independent knobs.
        confidence_floor_default / confidence_floor_low_score: the coarse
            self-report floor. ⚠ **v1.5 (2026-07-01): the low-score floor was
            collapsed 70 → 55** (= default) for demo data-collection — a 70 floor
            is unreachable given the observed sub-50 scores. This is **not** a
            probability and **not** the real gate — the deterministic
            ``candidate_filter`` is. Re-baseline before live.

    Token meter (Step 5 consumes these — USD + EUR, per this session's decision):
        pricing_usd_per_mtok: per-model ``(input, output)`` USD per Mtok. See the
            module-level ``_DEFAULT_PRICING_USD_PER_MTOK`` caveat (estimates).
        usd_to_eur: USD→EUR conversion estimate for the EUR cost column.
            Configurable; documented as an estimate, not a live FX rate.
        usage_log_path: where the meter appends usage records. Left ``None`` here
            so no repo path is baked into the dataclass default; wiring (Step 8)
            resolves it to ``<repo_root>/data/state/llm_usage.json``.
    """

    # --- LLM / decoding ---
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 1024
    temperature: float = 0.2
    timeout_s: float = 30.0

    # --- universe / direction ---
    epic_allowlist: tuple[str, ...] = ("IX.D.DAX.IFMM.IP",)
    allowed_directions: tuple[str, ...] = ("BUY", "SELL")
    long_bias_below_score: float = 50.0
    # v1.5 data-collection mode — re-baseline before live. Disabled so a below-neutral
    # SELL can be *generated*; the P6 debate (can flip BUY<->SELL) + the 4 hard VETOs are
    # the real direction check. Was True (Decision 7). See phase8 v1.5 hotfix, Issue B.
    enable_long_bias_clamp: bool = False
    max_spread_pct: float = 0.5
    volume_proxy: str | None = "EXS1.DE"
    # v1.5 (Issue C): the typed, validated universe is the single source of truth.
    # Default ``None`` → derived from ``epic_allowlist``/``volume_proxy`` in
    # ``__post_init__`` (default path bit-identical). Pass a list/tuple of
    # ``InstrumentSpec`` to widen the universe; ``epic_allowlist`` is then re-derived
    # from it so every consumer sees a consistent epic list.
    universe: tuple[InstrumentSpec, ...] | None = None

    # --- confidence floor (provisional — Decision 4; Phase 7 outcome-anchoring replaces it) ---
    confidence_floor_below_score: float = 50.0  # boundary below which the low-score floor applies
    confidence_floor_default: float = 55.0
    # v1.5 data-collection mode — re-baseline before live. Collapsed to the default (was 70.0):
    # every real bot_score has been < 50, so a 70 floor is unreachable and force-abstains. 55
    # keeps a meaningful self-report bar while letting a genuine pick through. See Issue B.
    confidence_floor_low_score: float = 55.0

    # --- token meter (USD + EUR) ---
    pricing_usd_per_mtok: dict[str, tuple[float, float]] = field(
        default_factory=lambda: dict(_DEFAULT_PRICING_USD_PER_MTOK)
    )
    usd_to_eur: float = 0.92
    usage_log_path: str | None = None

    def __post_init__(self) -> None:
        """Reconcile the typed ``universe`` with the derived ``epic_allowlist`` (v1.5).

        Single source of truth = ``universe``. If it was not supplied, derive it from
        the legacy ``epic_allowlist``/``volume_proxy`` (backward compat for callers
        that still construct with ``epic_allowlist=(...)``). If it *was* supplied,
        validate it (``load_universe`` — fail-closed) and re-derive ``epic_allowlist``
        from it so every consumer (``context_builder``, ``research._preflight``,
        wiring) sees a consistent epic list.
        """
        if self.universe is None:
            self.universe = _derive_universe(self.epic_allowlist, self.volume_proxy)
        else:
            self.universe = load_universe(self.universe)
            self.epic_allowlist = tuple(spec.epic for spec in self.universe)
