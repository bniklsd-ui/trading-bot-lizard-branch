"""Tunables for the Phase 5 execution pipeline (``ExecutionConfig``).

Every knob the gates, VETOs, sizing, order, monitor and reconcile modules read
lives here — nothing is hard-coded into a logic module, so a single frozen
config object parameterises the whole run and tests can override freely. The
defaults are the locked concept §0 decisions (v1 values; they are tuned at real
profit, not now — see the ``# v1`` notes).

Types only / no logic / no I/O — repo conventions apply
(``from __future__ import annotations``, type hints + docstrings). This module
imports nothing cross-phase.

Two unit reconciliations vs. the concept's first draft (code = source of truth,
verified against ``ig_adapter.py`` / ``filters.py``):

- ``max_spread_pct`` is a **percent of ask** (``Price.spread_pct`` =
  ``(ask-bid)/ask*100``), not points — the "~1.8 pts" guess was wrong. Default
  ``0.5`` mirrors Phase-4 ``ResearchConfig.max_spread_pct``.
- ``risk_pct_conservative`` / ``risk_pct_aggressive`` are **percent**; the risk
  sizer consumes a *fraction*, so ``sizing.py`` divides these by 100. As of
  2026-06-12 these are **risk-per-trade** percents (loss at the stop), not notional
  percents — the model was switched off notional ÷ price (see ``sizing.py``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ExecutionConfig:
    """All Phase-5 tunables (concept §0). Immutable; pass one instance per run.

    Time / window (Gate 1 + monitor time-stop):
        tz: IANA zone the ``HH:MM`` window/square-off strings are interpreted in
            (parsed via stdlib ``zoneinfo.ZoneInfo`` — Python 3.11+, no dep).
        trading_window_start / trading_window_end: Gate 1 trade window, ``HH:MM``.
        square_off_time: monitor force-close cutoff, ``HH:MM``.
        max_hold_minutes: monitor time-stop — max time a position is held.
        poll_interval_s: monitor polling cadence.

    VETOs (fresh snapshot immediately before the order):
        max_spread_pct: VETO 2 — reject when live ``price.spread_pct`` exceeds
            this (**percent of ask**).
        momentum_resolution / momentum_count: VETO 3 — the ``get_ohlcv`` bars
            (IG real-time) the momentum check reads (``MINUTE_5`` × 12 ≈ 1 h).
        momentum_veto_threshold_pct: VETO 3 — adverse net-return that vetoes the
            trade (BUY into a sharp drop / SELL into a sharp rally). **v1, tune at
            profit** — a blunt guard, not a hidden confidence system.

    Sizing (Gate 4 — risk-per-trade ÷ stop-distance, operator decision 2026-06-12):
        risk_pct_conservative / risk_pct_aggressive: **percent** of available
            balance put **at risk per trade** (worst-case loss if the stop is hit),
            chosen by ``Database.get_risk_level()`` (KONSERVATIV / AGGRESSIV).
            ``sizing.py`` passes ``value / 100`` (a fraction) into the risk-sizer;
            ``size = risk_amount / (stop_distance_points × point_value)``. Defaults
            2.0 / 3.0 give a tradeable ≥ ``min_deal_size`` 0.5 lot at the real ~€1K
            budget (the old 0.5 / 1.0 notional defaults rounded to 0.0 — see
            ``sizing.py`` for the model switch). **v1, tune at profit.**
        max_leverage: notional safety cap — the order's notional may not exceed
            ``available_balance × max_leverage`` (``sizing.py`` clips the risk size
            to this). Default 20.0 = the ESMA retail major-index ceiling (5% margin),
            so it only guards pathological oversizing, never normal ~€1K sizing.
            **v1, tune at profit.**

    SL / TP (set at entry, broker-side — survives a monitor crash):
        stop_distance_points / limit_distance_points: point offsets from the
            entry price; ``build_order_plan`` (Step 6) turns them into the
            **absolute** ``stop_level`` / ``limit_level`` IG expects. **v1, tune
            at profit** (ATR-based sizing is a documented later swap).

    Order currency:
        default_currency: IG's ``open_position`` requires a non-null ``currencyCode``
            (HTTP 400 otherwise). ``build_order_plan`` resolves the currency from the
            instrument's ``market_info``; this is the fallback when that is absent
            (the account + DAX cash CFD are EUR).

    Constraints / safety:
        max_parallel_positions: Gate 3 + VETO 4 cap on concurrent open positions.
            Not in the concept §0 table; default 1 (DAX intraday, single position)
            — a v1 default, flagged in the concept annotation.
        require_confirm: human-confirm gate before ``open_position`` (Decision D);
            default ON. ``ig_bot.py --yes`` overrides for later automation.
        reconcile_unexpected_aborts: on startup reconcile, an *unexpected* broker
            position (we have no record of it) aborts fail-closed when True
            (Decision E) rather than stacking another order.

    Order placement (``order.py``, Step 6 — Decision E idempotency):
        pending_recheck_attempts: when ``open_position`` returns ``PENDING`` (confirm
            timeout), how many times ``place_order`` re-checks the broker via
            ``reconcile_positions`` before failing closed. It **never** retries the
            order itself — a blind second order is the risk this guards against.
        pending_recheck_interval_s: pause between those re-checks (injected
            ``sleep_fn`` in tests, so no real wait). Both **v1, tune at profit**.
    """

    # --- time / window ---
    tz: str = "Europe/Berlin"
    trading_window_start: str = "09:00"
    trading_window_end: str = "17:30"
    square_off_time: str = "17:15"
    max_hold_minutes: int = 240
    poll_interval_s: int = 15

    # --- VETOs ---
    max_spread_pct: float = 0.5            # percent of ask (VETO 2)
    momentum_resolution: str = "MINUTE_5"  # VETO 3 — IG real-time bars
    momentum_count: int = 12               # ≈ 1 h of MINUTE_5 bars
    momentum_veto_threshold_pct: float = 0.15  # v1, tune at profit
    # Phase 15 Block C Step C3 (VETO 5 — long-term promoted instincts, AK9):
    # tuple of deterministic, promoted instinct predicates (``Callable[[dict], bool]``)
    # evaluated by ``longterm_pre_trade_check`` after VETO 4. Empty tuple (default)
    # ⇒ VETO 5 inactive ⇒ bit-identical to pre-C3 behaviour (Plan §6 C3). A promoted
    # instinct never reaches VETO 5 until ``n_closed >= InstinctConfig.instinct_n_min``
    # AND ``enable_instinct_promotion is True`` (Phase 15 P10/P12 + promote_eligible
    # gate). ``tuple`` (not ``list``) so the default is immutable and shared safely
    # across instances — mutable-default trap guard (Plan §8 second suspect).
    longterm_rules: tuple[Any, ...] = ()

    # --- sizing (Gate 4) ---
    risk_pct_conservative: float = 2.0     # percent; sizing.py divides by 100
    risk_pct_aggressive: float = 3.0       # percent; sizing.py divides by 100
    max_leverage: float = 20.0             # notional cap = balance × this (ESMA ceiling)
    # Phase 16 D3.2 (L7 / AK11): fraction of available balance the margin cap may use.
    # ``sizing.compute_size`` reads ``market_info.margin_factor`` (when ``margin_factor_unit
    # == "PERCENTAGE"``) and computes ``margin_cap = (available_balance * margin_headroom)
    # / (price * point_value * margin_factor / 100)``; the leverage cap above is the
    # fallback when IG has no per-instrument margin factor. The 0.95 below (vs. a full
    # 1.0) is the deliberate **5 % buffer** against IG's per-band staggering — empirical
    # observation from the 2026-09-07 ``probe_market_margin.py`` run shows IG steps the
    # factor up at named notional bands (e.g. DAX 5 % until 2800 EUR trade notional, then
    # 15 %). 0.95 absorbs most of those band jumps at the cost of a tiny size reduction.
    margin_headroom: float = 0.95
    # v1.5 (Issue C — multi-instrument sizing): per-epic account-currency value of ONE
    # index point, used by Gate-4 sizing (``risk / (stop_pts × point_value)``) and the
    # reconstructed ``initial_risk``. Default ``{}`` → every epic falls back to 1.0
    # (DAX cash CFD = 1 €/pt) → the DAX/default path is bit-identical — this empty-map
    # default is only hit by callers that don't wire the map at all (most unit tests).
    # ⚠ Phase-10 B1-fix (2026-07-31): once this map IS populated (the real wiring case,
    # ``phase8_scheduler/scripts/wiring.py``), an epic missing from it is no longer a
    # silent 1.0 — ``sizing.compute_size`` fails closed (no trade) instead. This is what
    # a stale-comment version of this note failed to prevent: a static, incomplete
    # source for this map caused a real 40x oversizing on AEX (see
    # ``phase10_v3/DATA_WEEK_REVIEW_2026-07-31.md`` §4 B1) — a doc note alone doesn't
    # stop that, a structural guard does. Keep this map consistent with the research-side
    # ``InstrumentSpec.point_value`` (the two are separate SoTs because the frozen
    # Candidate/turbo_candidates.json contract carries no point value and IG's
    # ``get_market_info`` does not expose one).
    point_values: dict[str, float] = field(default_factory=dict)

    # --- SL / TP ---
    stop_distance_points: float = 30.0     # v1, tune at profit
    limit_distance_points: float = 45.0    # v1 (1.5R), tune at profit

    # --- order currency ---
    # IG's open_position requires a non-null currencyCode (HTTP 400 otherwise).
    # build_order_plan resolves it from the instrument's market_info; this is the
    # fallback used only when market_info lacks a currency (EUR account/instrument).
    default_currency: str = "EUR"

    # --- constraints / safety ---
    max_parallel_positions: int = 1        # v1 default (not in §0 table)
    require_confirm: bool = True
    reconcile_unexpected_aborts: bool = True

    # --- order placement (Step 6 — PENDING fail-closed re-check) ---
    pending_recheck_attempts: int = 3      # v1, tune at profit
    pending_recheck_interval_s: float = 2.0  # v1, tune at profit

    def point_value_for(self, epic: str | None) -> float:
        """Account-currency value of one index point for ``epic`` (v1.5).

        Returns ``point_values[epic]`` when present, else ``1.0`` (DAX cash CFD =
        1 €/pt). ``None`` epic → ``1.0`` too. This 1.0 fallback is only the *safe*
        default when ``point_values`` is empty (the map is unwired); once the map is
        populated, ``sizing.compute_size`` never reaches this fallback for an
        unmapped epic — it fails closed first (Phase-10 B1-fix). This is the P5
        sizing authority for the point value; see the ``point_values`` field note
        on why it is a separate SoT from the research ``InstrumentSpec.point_value``.
        """
        if epic is None:
            return 1.0
        return self.point_values.get(epic, 1.0)
