"""Data contracts for the Phase 6 Bull/Bear/Judge debate.

These types are the integration surface for the debate pipeline:

- :class:`DebateConfig` carries every tunable (the locked §0 defaults). Nothing
  here is the *cost* source: per Decision F, pricing + the USD→EUR rate live in
  the shared ``research.ResearchConfig`` (reused, not duplicated). This config
  holds only the debate-specific knobs.
- :class:`DebateContext` is the deterministic, **read-only** bundle the agents
  see — built entirely by code (Module 2, ``context_builder``) from the Phase-4
  candidate + exactly one fresh broker snapshot. No AI touches its construction.
- :class:`AgentTurn` is one Bull/Bear/Judge turn (text + token usage), collected
  into the debate transcript.
- :class:`DebateOutcome` is the orchestrator's verdict (Module 6) and the
  **Phase 6 → Phase 5 seam contract**: ``decision`` (TRADE/ABSTAIN) + the final
  ``direction`` (which may reverse the seed). ``confidence`` is **advisory only —
  it gates nothing** (Decision H).

This module is **types only — no logic, no I/O, no network, no AI**. It imports
nothing from ``anthropic`` / ``broker_wrapper`` / ``research`` (phase isolation;
the documented cross-phase reuse of the Phase-4 LLM stack is wired later, in the
caching/budget modules, not in the types). Repo conventions apply:
``from __future__ import annotations``, type hints + docstrings everywhere.

Direction vocabulary is **BUY / SELL** only — exactly what ``open_position()``
enforces. No options terminology anywhere: this is a DAX CFD bot.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Exceptions (own typed hierarchy — concept §1, mirrors the Phase-4 pattern)
# ---------------------------------------------------------------------------


class DebateError(Exception):
    """Base class for all Phase-6 debate errors.

    Carries a ``code`` class attribute so callers can catch the whole family with
    one ``except`` or be specific. Independent of the Phase-1/3/4 hierarchies
    (phase isolation). Every subclass is converted to a **fail-closed ABSTAIN** by
    the orchestrator (Module 6) — it is never raised out of ``Debate.run`` and
    never results in "trade anyway" (Decision J).
    """

    code: str = "DEBATE_ERROR"


class DebateBudgetExceeded(DebateError):
    """A hard cap was breached mid-debate (calls / tokens / wall-clock).

    Raised by the budget meter (Module 5) on the **first** breach of
    ``max_total_calls`` / ``max_cumulative_input_tokens`` /
    ``max_cumulative_output_tokens`` / ``wall_clock_timeout_s``. The orchestrator
    catches it and returns an ABSTAIN outcome (cost discipline is structural — a
    breach never trades "regardless"; Decision E/J).
    """

    code = "DEBATE_BUDGET_EXCEEDED"


class DebateLLMError(DebateError):
    """An agent turn failed unrecoverably (after the shared client's retry).

    Raised when the reused ``research.LLMClient`` cannot produce a usable response
    for a Bull/Bear/Judge turn even after its single transient retry. Like every
    other failure path it resolves to an ABSTAIN outcome — never a fabricated
    direction (Decision J).
    """

    code = "DEBATE_LLM_ERROR"


# ---------------------------------------------------------------------------
# DebateConfig — every debate tunable in one place (concept §0 defaults table)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DebateConfig:
    """All tunables for the debate (concept §0). Immutable; v1 defaults.

    These defaults are the locked Phase-6 decisions, to be tuned on real
    profit/cost later (Phase 7), **not** now. Logic modules read everything from a
    ``DebateConfig`` instance (tests override freely by constructing a new one).

    **Pricing is deliberately absent** (Decision F): the per-model USD pricing and
    the USD→EUR rate are reused from the shared ``research.ResearchConfig`` that
    configures the Phase-4 ``LLMClient`` / ``token_meter`` — there is no second
    pricing source of truth here.

    Models (Decision C — all overridable):
        model_bull / model_bear: the adversarial arguers. Default Haiku 4.5
            (cheap, the bulk of the requests). Raise to Sonnet per role if Haiku
            argues too weakly in operation.
        model_judge: the synthesiser. Default Sonnet 4.6 (synthesis quality).

    Rounds & caps (Decision E/J — every breach → fail-closed ABSTAIN):
        max_rounds: 1 round = Bull + Bear + Judge-interim. Early-stop may end sooner.
        early_stop: let the Judge conclude on consensus before ``max_rounds``.
        max_total_calls / max_cumulative_input_tokens /
            max_cumulative_output_tokens / wall_clock_timeout_s: hard caps; the
            first breach raises :class:`DebateBudgetExceeded`.

    Caching & compression (Decision D/G):
        cache_system: cache the stable system+context prefix (the expensive
            optimization; the meter must log cache fields or it is invisible).
        compression_trigger_pct: compress the transcript at ~this fraction of the
            token budget (deterministic, code-side in v1 — no extra LLM request).

    Broker snapshot (Module 2 ``context_builder``):
        bars_resolution / bars_count: the IG real-time ``get_ohlcv`` window that
            feeds ``recent_bars_summary`` in the ``DebateContext``. Reused from the
            locked Phase-5 momentum defaults (same bars, same instrument).

    Decoding:
        temperature_bull / temperature_bear: slight divergence wanted (0.4).
        temperature_judge: synthesis should be consistent (0.1).
        max_tokens_agent / max_tokens_judge: per-turn output budgets.

    Audit / self-documentation:
        debate_log_path: gitignored JSON audit (Decision I). DB stays read-only.
        confidence_gates_nothing: **a self-documenting constant, not behaviour**
            (Decision H). The Judge's ``confidence`` is advisory; only the
            qualitative ``decision`` (TRADE/ABSTAIN) decides. A numeric confidence
            threshold is the calibration anti-pattern this flag exists to forbid.
    """

    # --- models (Decision C) ---
    model_bull: str = "claude-haiku-4-5-20251001"
    model_bear: str = "claude-haiku-4-5-20251001"
    model_judge: str = "claude-sonnet-4-6"

    # --- rounds & hard caps (Decision E/J) ---
    max_rounds: int = 5
    early_stop: bool = True
    max_total_calls: int = 18
    max_cumulative_input_tokens: int = 120_000
    max_cumulative_output_tokens: int = 12_000
    wall_clock_timeout_s: float = 120.0

    # --- caching & compression (Decision D/G) ---
    cache_system: bool = True
    compression_trigger_pct: float = 0.65

    # --- fresh broker snapshot (Module 2 context_builder) ---
    # Resolution/count for the IG real-time bars that feed ``recent_bars_summary``.
    # Reused verbatim from the locked Phase-5 momentum defaults
    # (``ExecutionConfig.momentum_resolution`` / ``momentum_count``) — same bars,
    # same instrument — not a new invented value. v1, tune at profit (Phase 7).
    bars_resolution: str = "MINUTE_5"
    bars_count: int = 12  # ≈ 1 h of MINUTE_5 bars

    # --- decoding ---
    temperature_bull: float = 0.4
    temperature_bear: float = 0.4
    temperature_judge: float = 0.1
    max_tokens_agent: int = 512
    max_tokens_judge: int = 768

    # --- audit / self-documentation ---
    debate_log_path: str = "data/state/debate_log.json"
    confidence_gates_nothing: bool = True  # Decision H — label only, no behaviour


# ---------------------------------------------------------------------------
# DebateContext — deterministic, code-built, read-only (the AI boundary)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DebateContext:
    """The single read-only bundle the agents argue over — built by code.

    Assembled by ``context_builder.build_debate_context`` (Module 2) from the
    Phase-4 candidate (the *seed*) plus exactly **one** fresh broker snapshot
    (``get_price`` + ``get_ohlcv`` + ``get_market_info``). The broker is read here,
    in code; the LLM agents never receive it (Decision J — structural fail-safe).

    The seed fields carry the Phase-4 proposal; the agents may argue *against* it
    and the Judge may reverse the direction (Decision B). Honesty note for the
    prompts (Module 3): ``drift_at_pick`` / ``seed_*`` are a **delayed** sentiment
    picture (Phase-4 used yFinance, ~15 min lag); ``spread_pct`` and
    ``recent_bars_summary`` are **IG real-time**.

    Attributes:
        epic: IG epic from the candidate (verbatim).
        seed_direction: the Phase-4 candidate direction (the "proposal"), BUY/SELL.
        seed_reasoning: ``candidate["reasoning"]``.
        seed_confidence: ``candidate["llm_confidence"]`` — advisory.
        spread_pct: **fresh** live spread % from ``get_price`` (supersedes the
            candidate's ``spread_pct_at_pick``).
        market_status: fresh market status string (e.g. ``"TRADEABLE"``).
        recent_bars_summary: compact text from ``get_ohlcv`` (IG real-time, e.g.
            MINUTE_5) — the agents' real-time price picture.
        drift_at_pick: Phase-4 drift context (~15 min delayed); ``None`` if the
            indicator was unavailable.
        score_at_pick: bot score captured at the Phase-4 pick.
        generated_at: ISO 8601 UTC timestamp of this context build.
    """

    epic: str
    seed_direction: str  # "BUY" | "SELL"
    seed_reasoning: str
    seed_confidence: float  # advisory
    spread_pct: float  # FRESH from get_price
    market_status: str
    recent_bars_summary: str  # from get_ohlcv (IG real-time)
    drift_at_pick: float | None
    score_at_pick: float
    generated_at: str


# ---------------------------------------------------------------------------
# AgentTurn — one Bull/Bear/Judge turn in the transcript
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AgentTurn:
    """A single agent turn: who spoke, what they said, and what it cost.

    Attributes:
        round: 1-based debate round.
        agent: ``"BULL"`` | ``"BEAR"`` | ``"JUDGE"``.
        model: the Anthropic model id used for this turn.
        text: the agent's argument / synthesis text.
        usage: token usage dict for this turn (input/output + cache fields + est
            cost) — the raw record the budget meter aggregates (Module 5).
    """

    round: int
    agent: str  # "BULL" | "BEAR" | "JUDGE"
    model: str
    text: str
    usage: dict[str, Any]


# ---------------------------------------------------------------------------
# DebateOutcome — the orchestrator verdict + Phase 6 → Phase 5 seam contract
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DebateOutcome:
    """The debate's final verdict, consumed at the Gate-2↔Gate-3 seam.

    ``decision`` is the only gating field: ``"ABSTAIN"`` → Phase 5 returns
    ``NO_TRADE``; ``"TRADE"`` → the candidate is enriched in-memory with
    ``direction`` (possibly reversed) and execution continues unchanged. Every
    error / cap-breach inside the debate produces ``decision="ABSTAIN"`` —
    fail-closed, never an exception out of ``run`` (Decision J).

    ``confidence`` is **ADVISORY and gates nothing** (Decision H): it is logged for
    Phase-7 outcome-anchoring, never compared to a threshold. Wiring a numeric
    confidence gate here is the calibration anti-pattern the design forbids.

    Attributes:
        decision: ``"TRADE"`` | ``"ABSTAIN"``.
        direction: ``"BUY"`` | ``"SELL"`` on TRADE; ``None`` on ABSTAIN.
        confidence: 0-100 Judge self-report — **advisory only**.
        rationale: the Judge's final reasoning (or the fail-closed reason).
        rounds_used: how many rounds ran (0 for the Phase-5 default passthrough).
        transcript: the full Bull/Bear/Judge turn sequence (immutable).
        token_summary: aggregate token/cost dict for the whole debate
            (input/output/cache_read/cache_write/est_cost_*).
    """

    decision: str  # "TRADE" | "ABSTAIN"
    direction: str | None  # "BUY" | "SELL" | None
    confidence: float  # ADVISORY ONLY — gates nothing (Decision H)
    rationale: str
    rounds_used: int
    transcript: tuple[AgentTurn, ...] = ()
    token_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain JSON-ready dict (used by the Module-7 audit).

        ``dataclasses.asdict`` recurses into the :class:`AgentTurn` transcript
        (which it keeps as a tuple); we normalise that to a **list** of plain
        dicts so the audit record (Module 7) is a clean JSON array. Mirrors
        ``research.models.Candidate.to_dict``.
        """
        d = asdict(self)
        d["transcript"] = list(d["transcript"])
        return d
