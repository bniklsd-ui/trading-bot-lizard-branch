"""Data contracts for the Phase 7 reward/brain pipeline (concept §6 Step 3).

Frozen dataclasses, types only — **no logic, no I/O, no AI**. These are the
integration surface between the reward modules (confidence / scorer / pnl_resolver
/ brain / recorder) and the Phase-5 executor seam:

- :class:`OpenedTrade` — the decision-context snapshot captured when a position
  opens (``reward_sink.on_trade_opened``); it is what gets persisted into the
  Phase-2 ``trade_outcomes`` row.
- :class:`ClosedTrade` — the minimal close fact (``reward_sink.on_trade_closed``);
  the realised P&L + levels are resolved later via ``get_trade_history``.
- :class:`ConfidenceReport` — the output of the deterministic confidence math
  (Decision C); ``confidence_value`` is **observe-only and gates nothing**.
- :class:`RewardResult` — the score delta the scorer produces (Decision B/D).
- :class:`LessonResult` — the outcome of the best-effort Haiku ``reflect()``
  (Decision E); ``ok=False`` carries the error, never raised into the close path.
- :class:`RewardConfig` — every tunable in one immutable place (concept §5).

Direction vocabulary is **BUY / SELL** only. ``account`` is **"demo" / "live"**.
No options terminology anywhere: this is a DAX CFD bot.

Pricing is **not** duplicated here (Decision F): the lesson model's USD pricing
lives in the reused ``research.ResearchConfig``; this config only names the model
(``lesson_model``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ---------------------------------------------------------------------------
# Exceptions (own typed hierarchy — mirrors the Phase-5/6 ``code``-attr pattern)
# ---------------------------------------------------------------------------


class RewardError(Exception):
    """Base class for all Phase-7 reward errors.

    Carries a ``code`` class attribute so callers can catch the whole family with
    one ``except`` or be specific. Independent of the Phase-1/3/4/5/6 hierarchies
    (phase isolation). Every Phase-7 write is best-effort/fail-closed (Decision J):
    a reward/lesson failure is logged ``critical`` and **never** raised into the
    Phase-5 close path — these are bookkeeping/learning, not a safety layer.
    """

    code: str = "REWARD_ERROR"


class PnLUnavailable(RewardError):
    """The realised P&L / close level could not be resolved for a closed trade.

    Raised inside ``pnl_resolver`` when ``get_trade_history`` has no usable match
    for a deal **and** the level-based fallback cannot be computed. The recorder
    treats it fail-closed (Decision J): log ``critical``, leave the trade closed at
    the broker, retry idempotently via ``deal_id`` later — never guess a P&L.
    """

    code = "PNL_UNAVAILABLE"


class SyntheticSafetyError(RewardError):
    """A synthetic write was about to target the **live** database (Decision H).

    Raised by ``synthetic.guard_synthetic_path`` (Step 6) when a synthetic-data
    write path resolves to the same file as ``RewardConfig.live_db_path``. The hard
    location split ("Grenze = der DB-Pfad") is the boundary: synthetic data lives in
    ``synthetic_db_path`` and **never** in the live store, so it can never enter the
    live edge metric. Unlike the bookkeeping errors above this is a **safety guard**
    — it is raised eagerly (before any DB is opened), not swallowed.

    ⚠ Step-6 addition: the concept §6 Step 3 exception list named only ``RewardError``
    /``PnLUnavailable``; this guard exception was added when ``synthetic.py`` landed.
    """

    code = "SYNTHETIC_SAFETY"


# ---------------------------------------------------------------------------
# OpenedTrade — decision context captured at open (-> trade_outcomes row)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OpenedTrade:
    """The decision context known the moment a position opens (Decision A).

    Captured by ``reward_sink.on_trade_opened`` immediately after ``place_order``
    confirms ``OPEN`` and **before** monitoring. It is the source for the Phase-2
    ``trade_outcomes`` insert (``insert_trade``). The broker is **never** handed to
    the reward layer for writing — this is a passive snapshot.

    Note on ``intended_open_level`` (verified-contract 1.2): ``place_order`` does
    **not** propagate the actual fill ``level`` (it is dropped from the
    ``ExecutionResult``), and ``trade_outcomes.open_level`` is NOT NULL. The seam
    (Step 10) therefore reconstructs the intended entry from the executor's fresh
    ``price_env`` (BUY→ask / SELL→bid) — or equivalently from
    ``stop_level ± stop_distance_points`` — and stores it here.

    Attributes:
        deal_reference: the bot's write-ahead idempotency key (``bot-<hex>``).
        deal_id: the broker deal id (from the ``OPEN`` confirm).
        epic: IG epic from the candidate.
        direction: ``"BUY"`` | ``"SELL"`` — the resolved direction (post-debate).
        size: the rounded position size that was placed.
        intended_open_level: the intended entry price (see the note above).
        stop_level: absolute stop level on the order.
        limit_level: absolute limit level on the order.
        currency: IG ``currencyCode`` (e.g. ``"EUR"``).
        initial_risk: the trade's risk in account currency, computed by the caller
            as ``abs(intended_open_level - stop_level) * size * point_value`` (this
            field only **carries** the value — "types only"; the arithmetic lives
            at the Step-10 seam where the inputs are known).
        research_confidence: the Phase-4 candidate self-report (advisory).
        debate_confidence: the Phase-6 Judge confidence captured **in-memory** at
            open time (advisory; ``None`` when no debate ran — verified-contract 1.3).
        gate_path: which gates passed/blocked this cycle (persisted as JSON).
        spread_at_entry_pct: the fresh spread % at entry (a process signal, B2).
        score_at_open: the bot score at the moment of opening.
        session_date: ``"YYYY-MM-DD"`` for daily aggregation (NOT NULL in P2).
        open_ts: ISO 8601 UTC open timestamp.
        account: ``"demo"`` | ``"live"`` — the data-source tag (Decision H); needed
            so ``include_demo_in_edge`` can filter the edge metric. Persisted in the
            ``account`` column added by migration 002 (operator decision 2026-06-18).
        provenance: ``"autonomous"`` | ``"verification"`` (v1.5 Phase-8 hotfix Step 4 A,
            2026-07-01). **Why:** the P4 research prompt is fed recent ``trade_lessons``;
            lessons distilled from **code-verification trades** (seeded, sub-minute forced
            time-stops — see ``seed_candidate.py``) describe the test harness, not a market
            decision, and pollute the single AI decision's input. The literal seed marker
            ``"MANUAL SEED (not a real research pick)"`` is otherwise **never persisted**
            (``build_opened`` stores only ``llm_confidence``; ``trade_outcomes`` has no
            reasoning column) and a schema migration is out of scope for the hotfix — so the
            executor seam derives this tag from the candidate ``reasoning`` and the recorder
            writes it into the existing ``trade_lessons.market_context_json`` blob (no schema
            change). The read-path filter (``db.get_recent_lessons_for_prompt``) then keeps
            ``"verification"`` lessons out of the prompt. **Display/prompt-provenance only —
            it gates nothing and never feeds the reward/score math** (root rule 3). Defaults
            to ``"autonomous"`` so every existing construction stays valid (additive).
    """

    deal_reference: str
    deal_id: str
    epic: str
    direction: str  # "BUY" | "SELL"
    size: float
    intended_open_level: float
    stop_level: float
    limit_level: float
    currency: str
    initial_risk: float
    research_confidence: float
    debate_confidence: float | None
    gate_path: dict[str, Any]
    spread_at_entry_pct: float
    score_at_open: float
    session_date: str
    open_ts: str
    account: str  # "demo" | "live"
    # v1.5 (Phase-8 hotfix Step 4 A): lesson-prompt provenance; default keeps existing
    # constructions valid + must stay the trailing field (only trailing fields may default).
    provenance: str = "autonomous"  # "autonomous" | "verification"


# ---------------------------------------------------------------------------
# ClosedTrade — the minimal close fact (-> P&L resolved later)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ClosedTrade:
    """The minimal fact that a monitored position has ended (Decision A).

    For a bot-issued ``TIME_STOP`` close, the realised close level + P&L ride along
    from the close deal confirmation (P5 ``monitor_position`` → ``ExecutionResult``,
    2026-06-23) — this is the **lag-free** P&L source the resolver prefers, because IG
    demo only books ``get_trade_history`` after settlement (unusable intraday). They are
    ``None`` on a broker-side ``CLOSED_BY_BROKER`` close (no bot close confirm) and on a
    cold reconcile; ``pnl_resolver`` then falls back to the heuristic
    ``get_trade_history`` match (verified-contract 1.1, no ``deal_id``).

    Attributes:
        deal_reference: the bot's idempotency key (links back to the OpenedTrade).
        deal_id: the broker deal id.
        status: ``"CLOSED_BY_BROKER"`` (broker SL/TP filled) or ``"TIME_STOP"``
            (monitor squared off / max-hold) — the exit-quality process signal (B2).
        closed_at: ISO 8601 UTC close timestamp.
        close_level: realised close fill from the close confirm, or ``None``.
        profit_loss: realised P&L from the close confirm, or ``None``.
    """

    deal_reference: str
    deal_id: str
    status: str  # "CLOSED_BY_BROKER" | "TIME_STOP"
    closed_at: str
    close_level: float | None = None
    profit_loss: float | None = None


# ---------------------------------------------------------------------------
# ConfidenceReport — output of the deterministic confidence math (Decision C)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConfidenceReport:
    """The outcome-anchored confidence picture (Decision C — **observe-only**).

    Produced by ``confidence.compute_confidence`` (Step 4). ``confidence_value`` is
    advisory and **gates nothing** in v1 — it does not gate an order and does not
    modulate ``risk_pct``. The named sub-metrics are the real logging quantities.

    ``state == "INSUFFICIENT"`` when ``n < n_min`` (default 10): then
    ``confidence_value`` is ``None`` (flows into nothing). The optional sub-metrics
    are also ``None`` on degenerate inputs (e.g. ``n == 0`` → no Wilson bound,
    ``n < 2`` / zero-variance → no SQN); Step 4 fills them for the OK case.

    Attributes:
        state: ``"OK"`` | ``"INSUFFICIENT"``.
        n: number of trades the metric is computed over.
        win_rate_raw: naive wins/n (advisory; **not** the confidence).
        win_rate_wilson_lb: Wilson score lower bound (the conservative estimator).
        expectancy_r: mean R-multiple (P&L / initial risk).
        sqn: System Quality Number (Van Tharp side-metric); ``None`` when undefined.
        confidence_value: the bounded v1 combiner; ``None`` when INSUFFICIENT.
    """

    state: str  # "OK" | "INSUFFICIENT"
    n: int
    win_rate_raw: float | None
    win_rate_wilson_lb: float | None
    expectancy_r: float | None
    sqn: float | None
    confidence_value: float | None


# ---------------------------------------------------------------------------
# RewardResult — the score delta the scorer produces (Decision B/D)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RewardResult:
    """The process-aware reward delta for one closed trade (Decision B2/D).

    Produced by ``scorer.score`` (Step 5). The total applied delta is
    ``outcome_delta + process_delta`` (clamped to ``±max_delta_per_trade``);
    ``score_after`` is ``score_before`` plus that, clamped to
    ``[score_min, score_max]`` (the DB does **not** clamp — verified-contract 1.7).

    Attributes:
        outcome_delta: the braked outcome component (∝ clipped R-multiple).
        process_delta: the process-quality component, **independent** of the
            outcome (clean SL/TP exit vs time-stop drift, tight vs wide entry spread).
        score_before: the score read before this trade (``get_current_score``).
        score_after: the clamped resulting score (what gets written).
        win_loss: ``"WIN"`` | ``"LOSS"`` | ``"BREAKEVEN"`` from the R-multiple.
        r_multiple: realised P&L over initial risk (clipped for scoring, raw here).
    """

    outcome_delta: float
    process_delta: float
    score_before: float
    score_after: float
    win_loss: str  # "WIN" | "LOSS" | "BREAKEVEN"
    r_multiple: float


# ---------------------------------------------------------------------------
# LessonResult — outcome of the best-effort Haiku reflect() (Decision E/J)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LessonResult:
    """The result of the best-effort lesson extraction (Decision E — the only AI).

    Produced by ``brain.reflect`` (Step 7): one Haiku call, own timeout. It is
    **best-effort** (Decision J) — any failure yields ``ok=False`` with the error
    captured here and **no re-raise**, so a flaky LLM never disturbs the close path.

    Attributes:
        lesson_text: the extracted learning, or ``None`` on failure.
        market_context: the market conditions dict passed to the prompt (also
            persisted as ``market_context_json`` on the lesson row).
        ok: whether extraction succeeded.
        error: the failure reason when ``ok`` is False, else ``None``.
    """

    lesson_text: str | None
    market_context: dict[str, Any]
    ok: bool
    error: str | None


# ---------------------------------------------------------------------------
# RewardConfig — every tunable in one place (concept §5 defaults)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RewardConfig:
    """All tunables for the reward/brain pipeline (concept §5). Immutable; v1 defaults.

    These are v1 values to be tuned on **real profit/cost** later, **not** now.
    Logic modules read everything from a ``RewardConfig`` instance (tests override
    freely by constructing a new one). Pricing is deliberately absent (Decision F):
    the lesson model's USD pricing lives in the reused ``research.ResearchConfig``.

    Confidence (Decision C):
        n_min: below this N the confidence is INSUFFICIENT (flows into nothing).
        wilson_z: z for the Wilson lower bound (1.96 = 95%).
        point_value: € per point for the R-multiple (DAX CFD = 1.0).

    Scoring bounds & shape (Decision B2/D):
        score_min / score_max: clamp bounds for ``score_after`` ([0, 100]).
        max_delta_per_trade: hard cap on ``|outcome_delta + process_delta|``.
        outcome_weight: scale of the outcome component (× clipped R).
        r_clip: clip the R-multiple to ``±r_clip`` before scoring (tail guard).
        process_weight: scale of the process component.
        loss_asymmetry: ``>1`` makes losses move the score more; default symmetric.
        tight_spread_pct: entry spread ≤ this → a clean-entry process plus.
        clean_exit_bonus: planned SL/TP exit (``CLOSED_BY_BROKER``) vs drift
            (``TIME_STOP``) process signal.

    Lesson extraction (Decision E):
        lesson_model: the Haiku model id (priced in ``ResearchConfig``).
        lesson_max_tokens / lesson_temperature / lesson_timeout_s: one short,
            low-temperature lesson with its own timeout (never hard-blocks close).

    Bootstrap / data separation (Decision H):
        include_demo_in_edge: count ``account='demo'`` trades in the edge metric
            (``True`` for the bootstrap phase, so confidence can leave INSUFFICIENT;
            demo confidence is **not** live-edge-validated — re-baseline at go-live).
        live_db_path / synthetic_db_path: the hard location split — every synthetic
            writer targets ``synthetic_db_path`` (never the live path); demo/live
            trades go to ``live_db_path``.

    ⚠ ``live_db_path`` default reconciliation (verified-contract 1.7, 2026-06-18):
    the real Phase-2 database is ``data/trading_bot.sqlite`` (P2 ``CLAUDE.md`` /
    ``scripts/init_db.py``), **not** the concept §5 string ``data/trading_bot.db``.
    Code = source of truth → this default uses the real ``.sqlite`` path; concept §5
    is annotated with the dated note.
    """

    # --- confidence (Decision C) ---
    n_min: int = 10
    wilson_z: float = 1.96
    point_value: float = 1.0

    # --- scoring bounds & shape (Decision B2/D) ---
    score_min: float = 0.0
    score_max: float = 100.0
    max_delta_per_trade: float = 5.0
    outcome_weight: float = 2.0
    r_clip: float = 3.0
    process_weight: float = 0.5
    # ponytail (Phase 15 Block B Step B2, 2026-09-03, MiniMax-M3-Exec-Session #7):
    # gesenkt von 1.5 → 0.5. Arithmetik der Invariante P1/P2:
    #   max|process| = process_weight × (1 + 1 + 0.5) = 0.5 × 2.5 = 1.25
    #   |outcome bei R = −1| = outcome_weight × 1.0 × loss_asymmetry = 2.0
    # 1.25 < 2.0 ⇒ ein voller Stop-Out kann den Score nicht mehr netto heben.
    # Belegt durch den RED→GREEN-Test `test_a_full_stop_loss_never_raises_the_score`
    # (Phase-15-B-B1 / AK5): vor B2 6/24 Fälle rot, nach B2 0/24.
    loss_asymmetry: float = 1.0
    # ponytail (Phase 15 Block B Step B4, 2026-09-03, MiniMax-M3-Exec-Session #7):
    # sichtbarer Knopf — Wert bewusst unverändert (Plan §6 B4: P3).
    # Gemessene Verteilung (Plan §3 B2, Stand 2026-08-31): n=13 Trades+S Snapshots,
    # Median spread_at_entry_pct = 0.00456, Max = 0.0248. Der Schwellwert 0.05
    # liegt ~11× über dem Median ⇒ der Clean-Entry-Bonus feuert in 7/8 Trades
    # (fast immer) und ist damit faktisch eine Konstante, kein Signal.
    # Bedingung fürs Nachziehen: n ≥ 50 Spread-Beobachtungen (sonst overfitten
    # auf n=13). Bis dahin: Bonus bleibt als „Planmäßigkeit dokumentiert" stehen.
    tight_spread_pct: float = 0.05
    clean_exit_bonus: float = 1.0

    # --- lesson extraction (Decision E) ---
    lesson_model: str = "claude-haiku-4-5-20251001"
    lesson_max_tokens: int = 400
    lesson_temperature: float = 0.3
    lesson_timeout_s: float = 20.0

    # --- bootstrap / data separation (Decision H) ---
    include_demo_in_edge: bool = True
    live_db_path: str = "data/trading_bot.sqlite"  # real P2 path (see docstring ⚠)
    synthetic_db_path: str = "data/synthetic_reward.db"
