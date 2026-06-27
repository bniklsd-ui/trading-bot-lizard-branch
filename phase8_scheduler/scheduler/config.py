"""Tunables for the Phase 8 scheduler daemon (``SchedulerConfig``).

Every knob the clock, state store, auto-confirm gate, backoff tracker, token
budget, research tick, reconcile pass and the loop itself read lives here —
nothing is hard-coded into a logic module, so a single frozen config object
parameterises the whole daemon and tests can override freely. This mirrors the
Phase-5 ``ExecutionConfig`` pattern exactly (one immutable config per run).

The defaults are the locked concept §1 values (v1; tuned at real output, not now
— see the ``# v1`` notes), **with two documented concept↔code reconciliations**
(code = source of truth):

- **Trade window = full market ``09:00``–``17:30``** (operator decision 2026-06-28),
  held as ``HH:MM`` strings. The concept §1 draft defaulted to ``09:30``–``11:19``
  and called it "aus P5-Config" — but the real, live-verified Phase-5
  ``ExecutionConfig.trading_window_start`` / ``…_end`` are ``09:00`` / ``17:30``
  (and ``external_data.market_hours.is_market_open`` likewise runs ``09:00–17:30``).
  So the narrow morning window was neither from P5 nor what the executor enforces.
  The operator chose the full market window to maximise trade attempts = more real
  demo data (the phase mission). ``clock.py`` (next module) classifies the WINDOW
  phase against these strings; P5's Gate 1 independently re-checks ``09:00–17:30``.
- **Window held as ``str`` (``"09:00"``), not ``datetime.time``.** The concept §1
  typed the fields ``time``; the build note in ``phase8_scheduler/CLAUDE.md`` says
  "Zeitfenster (reuse P5-Strings)" and the source-of-truth sibling P5 stores the
  window as ``HH:MM`` strings parsed via ``gates._parse_hhmm``. Mirroring that keeps
  a single parsing idiom that ``clock.py`` reuses, instead of introducing a second
  time representation.

Types only / no logic / no I/O beyond a single startup WARNING — repo conventions
apply (``from __future__ import annotations``, type hints + docstrings). This module
imports nothing cross-phase.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("scheduler.config")


@dataclass(frozen=True)
class SchedulerConfig:
    """All Phase-8 scheduler tunables (concept §1). Immutable; pass one per run.

    Time / window (``clock.py`` phase classification + the loop cadence):
        window_open / window_close: the daemon's trade window, ``HH:MM`` strings in
            ``tz``. Defaults ``09:00`` / ``17:30`` mirror the live-verified Phase-5
            ``ExecutionConfig`` window (operator: full market, see the module
            docstring reconciliation). The WINDOW phase is when the loop attempts a
            full research→execute cycle; outside it the loop idles/reconciles.
        tz: IANA zone the ``HH:MM`` window strings are interpreted in (Europe/Berlin,
            DST-aware via stdlib ``zoneinfo`` in ``clock.py`` — Python 3.11+, no dep).
        cycle_interval_min: cadence between trade cycles inside the WINDOW (Decision
            3). With an open position the Phase-5 ``monitor_position`` takes over.
        idle_poll_min: sleep granularity while IDLE / waiting for the next phase.
        pre_open_lead_min: how early before ``window_open`` to warm the IG session /
            token (PRE_OPEN), so the first WINDOW cycle does not pay a cold connect.

    Caps / safety (consumed by ``safety.py`` ``AutoConfirm`` + ``backoff.py``):
        account: the trading account tag. **HARD demo-lock lives in ``safety.py``**,
            not here — a non-``"demo"`` value is *constructable* (separation of
            concerns / testability), but ``AutoConfirm`` refuses to confirm anything
            ``!= "demo"`` (``logger.critical``). Default ``"demo"``.
        max_trades_per_day: per-day trade cap (Decision 6). Operator-confirmed v1 = 5.
        daily_loss_cap: the daily-loss circuit breaker threshold in account currency
            (Decision 10). ``None`` ⇒ **breaker inactive** → ``__post_init__`` emits a
            loud WARNING (you must set it consciously). The operator-confirmed
            production value (~€1800 on the ~30K demo ≈ 3× a trade's ``initial_risk``)
            is passed at the **wiring** step, not baked into the dataclass default, so
            forgetting to set it is loud, not silent. **v1, tune at real output.**
        max_consecutive_failures: consecutive cycle exceptions before the backoff
            tracker trips the kill-switch (``auto:backoff``) and stops cleanly
            (Decision 9). Operator-confirmed v1 = 3 (a transient blip should not kill
            the day; three in a row is structural — auth/keyring/DB).
        backoff_base_s / backoff_cap_s: exponential backoff schedule on cycle
            exceptions — ``min(base · 2^(n-1), cap)``.

    Budget (consumed by ``budget.py``):
        daily_token_budget: per-day LLM token budget over the reused 8-field
            ``token_meter`` / ``llm_usage.json`` (Decision 12). ``None`` ⇒ never
            exhausted; that WARNING lives in ``budget.py`` (§7), not here, to keep
            one warning per responsibility.

    Reconcile (consumed by ``reconcile.py``):
        reconcile_interval_min: cadence of the idempotent ``CLOSED_BY_BROKER`` P&L
            catch-up pass (Decision 11) — also run on startup + shutdown.

    Paths (gitignored ``data/`` tree, the layout Phase-2 ``init_db.py`` provisions):
        live_db_path: the **real** Phase-2 SQLite DB — ``data/trading_bot.sqlite``
            (matches the Phase-7 wiring ``_DB_PATH``; the concept's ``…/trading_bot.db``
            string was stale, reconciled in Phase 7 already).
        state_path: ``scheduler_state.json`` (trade count, loss accumulator, backoff
            counter, kill reason, last research/reconcile ts — Decision 18; atomic
            tmp+rename writes in ``state.py``).
        kill_path: the file-based kill-switch (Decision 8) — existence = truth; read
            by ``safety.py`` / every loop, written by the auto-trip and the UI.
        command_path: ``scheduler_command.json`` — the UI's start/stop control channel
            (Decision 14); the daemon polls it. Generic enough for later P10 actions.
    """

    # --- time / window ---
    # HH:MM strings in `tz`; defaults mirror the live-verified Phase-5 window
    # (operator: full market 09:00–17:30 — see the module docstring reconciliation).
    window_open: str = "09:00"
    window_close: str = "17:30"
    tz: str = "Europe/Berlin"
    cycle_interval_min: int = 5            # v1 (Decision 3, testrun cadence)
    idle_poll_min: int = 5
    pre_open_lead_min: int = 10            # warm the session this early before open

    # --- caps / safety ---
    account: str = "demo"                  # HARD demo-lock is in safety.py, not here
    max_trades_per_day: int = 5            # operator-confirmed v1
    daily_loss_cap: float | None = None    # None ⇒ breaker inactive + loud WARNING
    max_consecutive_failures: int = 3      # operator-confirmed v1
    backoff_base_s: float = 30.0
    backoff_cap_s: float = 600.0

    # --- budget ---
    daily_token_budget: int | None = None  # None ⇒ never exhausted (WARNING in budget.py)

    # --- reconcile ---
    reconcile_interval_min: int = 15

    # --- paths (gitignored data/ tree) ---
    live_db_path: str = "data/trading_bot.sqlite"          # the real P2 DB
    state_path: str = "data/state/scheduler_state.json"
    kill_path: str = "data/state/KILL"
    command_path: str = "data/state/scheduler_command.json"

    def __post_init__(self) -> None:
        """Emit one loud WARNING when the daily-loss breaker is inactive.

        ``daily_loss_cap is None`` means the Decision-10 circuit breaker will not
        block — a deliberate "you must set this consciously" design, surfaced loudly
        rather than silently. Read-only (no attribute mutation), so it is safe on a
        frozen dataclass; it never raises (a missing cap is a configuration choice,
        not a crash).
        """
        if self.daily_loss_cap is None:
            logger.warning(
                "daily_loss_cap is None — the daily-loss circuit breaker is INACTIVE. "
                "Set it consciously at wiring (operator-confirmed v1 ≈ 1800 on the demo)."
            )
