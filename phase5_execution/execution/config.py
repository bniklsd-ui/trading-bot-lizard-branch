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
- ``risk_pct_conservative`` / ``risk_pct_aggressive`` are **percent**;
  ``calc_position_size`` consumes a *fraction*, so ``sizing.py`` (Step 4) divides
  these by 100.
"""

from __future__ import annotations

from dataclasses import dataclass


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

    Sizing (Gate 4):
        risk_pct_conservative / risk_pct_aggressive: **percent** of available
            balance to expose, chosen by ``Database.get_risk_level()``
            (KONSERVATIV / AGGRESSIV). ``sizing.py`` passes ``value / 100`` to
            ``calc_position_size`` (which takes a fraction).

    SL / TP (set at entry, broker-side — survives a monitor crash):
        stop_distance_points / limit_distance_points: point offsets from the
            entry price; ``build_order_plan`` (Step 6) turns them into the
            **absolute** ``stop_level`` / ``limit_level`` IG expects. **v1, tune
            at profit** (ATR-based sizing is a documented later swap).

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

    # --- sizing (Gate 4) ---
    risk_pct_conservative: float = 0.5     # percent; sizing.py divides by 100
    risk_pct_aggressive: float = 1.0       # percent; sizing.py divides by 100

    # --- SL / TP ---
    stop_distance_points: float = 30.0     # v1, tune at profit
    limit_distance_points: float = 45.0    # v1 (1.5R), tune at profit

    # --- constraints / safety ---
    max_parallel_positions: int = 1        # v1 default (not in §0 table)
    require_confirm: bool = True
    reconcile_unexpected_aborts: bool = True

    # --- order placement (Step 6 — PENDING fail-closed re-check) ---
    pending_recheck_attempts: int = 3      # v1, tune at profit
    pending_recheck_interval_s: float = 2.0  # v1, tune at profit
