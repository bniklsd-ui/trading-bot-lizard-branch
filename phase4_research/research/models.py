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

from dataclasses import asdict, dataclass, field
from typing import Any


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
    """

    tradeable_epics: list[dict[str, Any]]
    recent_trades: list[dict[str, Any]]
    recent_lessons: list[dict[str, Any]]
    bot_score: float
    risk_level: str
    brain_context: dict[str, Any] | None
    anchor_epic: str


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
            long-bias rule below.
        long_bias_below_score / enable_long_bias_clamp: when the clamp is on and
            ``bot_score < long_bias_below_score``, only ``BUY`` is allowed.
        max_spread_pct: live-spread rejection threshold (% of ask).
        volume_proxy: ETF symbol supplying volume for ``^GDAXI`` (which reports
            none natively); registered on the fetcher in wiring (Step 8). ``None``
            disables the proxy → ``volume_z_score`` stays ``None``.

    Confidence floor (PROVISIONAL — Decision 4):
        confidence_floor_default / confidence_floor_low_score: the coarse
            self-report floor (55 normally, 70 when ``bot_score < 50``). This is
            **not** a probability and **not** the real gate — the deterministic
            ``candidate_filter`` is. Replaced by Phase-7 outcome-anchored
            confidence; kept deliberately blunt here.

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
    enable_long_bias_clamp: bool = True
    max_spread_pct: float = 0.5
    volume_proxy: str | None = "EXS1.DE"

    # --- confidence floor (provisional — Decision 4) ---
    confidence_floor_default: float = 55.0
    confidence_floor_low_score: float = 70.0

    # --- token meter (USD + EUR) ---
    pricing_usd_per_mtok: dict[str, tuple[float, float]] = field(
        default_factory=lambda: dict(_DEFAULT_PRICING_USD_PER_MTOK)
    )
    usd_to_eur: float = 0.92
    usage_log_path: str | None = None
