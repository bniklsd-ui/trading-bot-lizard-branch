"""Module 6 — the auto-confirm gate (``AutoConfirm``): demo-only, fail-closed, **no AI**.

This is the deterministic-code replacement for the Phase-5 *human-confirm* prompt: where
``ig_bot`` asked an operator ``y/N`` before every order, the autonomous daemon asks this
class. It is the single most safety-critical module in Phase 8, so it is pure mechanics —
five hard gates, all of which must pass for an order to be confirmed:

1. **Demo-lock (structural).** ``config.account == "demo"``. Anything else → ``False`` +
   ``logger.critical``. Live auto-confirm is architecturally locked until profit
   validation. **The check is on the *config*, not the order** — verified Contract D: the
   Phase-5 ``OrderPlan`` the executor passes to ``confirm_fn`` carries **no** ``account``
   field, so the demo-lock cannot come from the plan. The wiring enforces demo two ways at
   once: it only ever builds the ``ig_demo`` broker *and* sets ``config.account="demo"``.
2. **Kill-switch off.** ``killswitch.is_set(kill_path)`` is ``False`` (file-existence truth,
   shared with the loop and the Web-UI — Module 5).
3. **Under the trade cap.** ``state.trades_today < config.max_trades_per_day``.
4. **Above the daily-loss breaker.** ``config.daily_loss_cap is not None`` **and** today's
   realized P&L ``> -daily_loss_cap``. ``None`` ⇒ breaker disabled → one loud WARNING at
   construction, no block (you set the cap consciously at wiring).
5. **Budget not exhausted.** ``budget.is_exhausted()`` is ``False``.

Two seams worth pinning (code = source of truth — see the two concept↔code reconciliations
at the bottom of this docstring):

- **The loss-breaker reads today's realized P&L from the DB, not from the state snapshot.**
  Verified Contract E: a ``CLOSED_BY_BROKER`` trade returns ``profit_loss=None`` at cycle
  time (it is only resolved later by the reconcile pass, Module 9), so
  ``SchedulerState.realized_pnl_today`` *lags* the DB for broker-closed trades (see the
  ``state.py`` Module-4 reconciliation, which explicitly flags this). Binding the breaker
  to that snapshot would let a real loss slip past it. So ``AutoConfirm`` takes an injected
  ``realized_pnl_today`` callable — ``(session_date) -> float`` — that the wiring backs with
  the DB. Keeping the query *out* of this module preserves phase isolation (``import
  scheduler.safety`` pulls nothing cross-phase); the wiring's closure runs, against the
  Phase-2 ``Database``::

      SELECT COALESCE(SUM(profit_loss), 0.0)
        FROM trade_outcomes
       WHERE session_date = ? AND profit_loss IS NOT NULL

  (OPEN / CANCELLED rows have ``profit_loss = NULL`` and are naturally excluded; the
  injected callable is given ``state.date`` as the session date.) The DB read is wrapped
  fail-**closed**: if it raises, the breaker blocks the trade (we cannot prove we are under
  the cap → do not open) and logs ``critical``; a later cycle re-evaluates and recovers.

- **``budget`` is a duck-typed Protocol, not the concrete Module-7 class.** Module 7
  (``budget.py``) is built *after* this one in the binding order, so ``AutoConfirm`` depends
  on the :class:`Budget` interface (``is_exhausted() -> bool``), which Module 7's
  ``TokenBudget`` will satisfy. Tests pass a tiny fake. This mirrors how ``state.py`` ducks
  the Phase-5 ``ExecutionResult`` (``CycleResult``) — interface over import.

``AutoConfirm`` is called two ways, both routing through one shared evaluator so they can
never disagree (concept §5):

- :meth:`can_open` — the **pre-cycle** gate the loop calls *before* research, to skip a
  cycle (and its LLM tokens) when a hard condition already blocks. Returns
  ``(ok, reason_or_None)`` so the loop can record ``state.last_no_trade_reason``.
- :meth:`__call__` — the **final** gate the Phase-5 executor invokes as ``confirm_fn(plan)``
  immediately before ``place_order``. It reads state **live** from the store (verified
  Contract A: the executor is built **once** with this as ``confirm_fn`` and the loop calls
  a bare ``run()``, so the gate must not hold a stale snapshot) and returns a bare ``bool``.

Repo conventions apply (``from __future__ import annotations``, type hints + docstrings, one
file = one responsibility, logging to a module logger, never swallow silently). **No AI, no
network, no broker** — pure gating over the config, the kill-file, the injected P&L reader
and the budget.

---

Concept↔code reconciliations (dated 2026-06-28, code = source of truth):

1. **Constructor gains a 5th arg ``realized_pnl_today``.** The concept §5 sketch is
   ``AutoConfirm(config, state_store, kill_path, budget)`` — but its own loss-breaker bullet
   plus verified Contract E require reading realized P&L *from the DB*, which that signature
   has no source for. Adding the injected callable is the minimal, phase-isolated way to
   honour Contract E (rather than importing Phase-2 here or — wrongly — binding the breaker
   to the lagging ``state.realized_pnl_today`` snapshot).

2. **The §5 ``order_ctx.account == "demo"`` double-check is dropped.** Contract D pins that
   the ``OrderPlan`` has no ``account`` field, so the demo-lock is config-only (the wiring's
   ig_demo-broker + ``account="demo"`` is the structural half). ``__call__`` accepts the plan
   but reads nothing from it.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Protocol

from scheduler import killswitch
from scheduler.config import SchedulerConfig
from scheduler.state import SchedulerState, StateStore

logger = logging.getLogger("scheduler.safety")

# Block reasons returned by the gate (None = confirmed). The loop folds the reason into
# ``state.last_no_trade_reason`` (concept §10) for the state file / Web-UI. These are the
# *gate-block* taxonomy; ``research_tick`` owns the separate no-candidate taxonomy
# (EMPTY_UNIVERSE / LLM_ABSTAIN / …).
REASON_NOT_DEMO: str = "NOT_DEMO"          # account != "demo" (structural; logged critical)
REASON_KILL: str = "KILL"                  # kill-switch file present
REASON_CAP: str = "CAP_BLOCK"              # trades_today reached max_trades_per_day
REASON_LOSS: str = "LOSS_BREAKER"          # today's realized P&L at/below -daily_loss_cap
REASON_BUDGET: str = "BUDGET"              # token budget exhausted


# A callable returning today's realized P&L (account currency) for a given Europe/Berlin
# session date — injected by the wiring, DB-backed (see the module docstring SQL). Kept an
# interface, not a Phase-2 import, so this module stays phase-isolated.
RealizedPnLToday = Callable[[str], float]


class Budget(Protocol):
    """The slice of the Module-7 token budget the auto-confirm gate needs.

    Duck-typed on purpose: ``safety.py`` is built before ``budget.py`` in the binding
    order, so it depends on this interface rather than the concrete ``TokenBudget`` (which
    will satisfy it). Tests pass a tiny fake. By contract ``is_exhausted`` returns a bool
    and never raises (the budget gate is fail-soft — see ``exceptions.py``).
    """

    def is_exhausted(self) -> bool:
        """Return whether the daily token budget is spent (``True`` ⇒ block new cycles)."""
        ...


class AutoConfirm:
    """The deterministic auto-confirm gate — the Phase-5 human-confirm's code replacement.

    Confirms an order only when **all five** hard conditions hold (see the module
    docstring). Holds *references* (config, state store, kill path, budget, P&L reader), not
    snapshots, so :meth:`__call__` reads state / caps / kill-switch / budget live at call
    time (verified Contract A).

    Args:
        config: the frozen :class:`~scheduler.config.SchedulerConfig`. The demo-lock reads
            ``config.account``; the caps read ``max_trades_per_day`` / ``daily_loss_cap``.
        state_store: the :class:`~scheduler.state.StateStore`; :meth:`__call__` loads the
            live state from it (the executor passes no state to ``confirm_fn``).
        kill_path: path to the file-based kill-switch (Module 5).
        budget: anything satisfying :class:`Budget` (Module 7's ``TokenBudget`` does).
        realized_pnl_today: ``(session_date) -> float`` returning today's realized P&L in
            account currency (DB-backed at wiring; see the module docstring). Required — the
            loss-breaker cannot read the DB without it.
    """

    def __init__(
        self,
        config: SchedulerConfig,
        state_store: StateStore,
        kill_path: str,
        budget: Budget,
        realized_pnl_today: RealizedPnLToday,
    ) -> None:
        self._config = config
        self._state_store = state_store
        self._kill_path = kill_path
        self._budget = budget
        self._realized_pnl_today = realized_pnl_today

        # One loud WARNING at construction when the loss-breaker is disabled — the safety
        # module loudly owns its own disabled gate (config.py also warns about the *value*;
        # this warns that gate #4 will not block). Concept §5 "eine laute WARNING beim Start".
        if config.daily_loss_cap is None:
            logger.warning(
                "AutoConfirm: daily_loss_cap is None — the daily-loss breaker gate is "
                "DISABLED; trades will NOT be loss-gated. Set daily_loss_cap at wiring."
            )

    # --- the two call surfaces (both route through _evaluate) ----------------

    def can_open(self, state: SchedulerState) -> tuple[bool, str | None]:
        """Pre-cycle gate: may a new trade cycle even be attempted?

        Called by the loop *before* research so a blocked cycle costs no LLM tokens. Returns
        ``(True, None)`` when all five conditions hold, else ``(False, reason)`` with the
        first failing gate's reason (see the ``REASON_*`` constants), which the loop records
        as ``state.last_no_trade_reason``.
        """
        return self._evaluate(state)

    def __call__(self, order_plan: Any) -> bool:
        """Final gate: the executor's ``confirm_fn(plan)`` immediately before ``place_order``.

        Reads the **live** state from the store (Contract A — the executor holds this gate
        from construction and the loop calls a bare ``run()``, so a snapshot would go stale).
        ``order_plan`` is the Phase-5 ``OrderPlan``; per Contract D it carries no ``account``
        and nothing is read from it (the demo-lock is config-only). Returns a bare ``bool``.
        """
        state = self._state_store.load()
        ok, reason = self._evaluate(state)
        if not ok:
            logger.info("auto-confirm declined for order (reason=%s)", reason)
        return ok

    # --- the shared evaluator ------------------------------------------------

    def _evaluate(self, state: SchedulerState) -> tuple[bool, str | None]:
        """Run all five hard gates in fail-closed order; return ``(ok, reason_or_None)``.

        Ordered most-structural first so the reported reason is the most serious one when
        several fail: demo-lock → kill-switch → trade cap → loss breaker → budget.
        """
        # 1) Demo-lock (structural, config-only — Contract D). Anything but demo is a serious
        #    misconfiguration: refuse loudly. Live auto-confirm is architecturally locked.
        if self._config.account != "demo":
            logger.critical(
                "AutoConfirm REFUSED: config.account=%r != 'demo'. Auto-confirm is "
                "demo-only and architecturally locked against live until profit validation.",
                self._config.account,
            )
            return False, REASON_NOT_DEMO

        # 2) Kill-switch (file existence = truth; fail-soft reader never raises).
        if killswitch.is_set(self._kill_path):
            return False, REASON_KILL

        # 3) Trade cap.
        if state.trades_today >= self._config.max_trades_per_day:
            return False, REASON_CAP

        # 4) Daily-loss circuit breaker — reads realized P&L from the DB (Contract E), NOT
        #    state.realized_pnl_today (which lags for broker-closed trades). A None cap means
        #    the breaker is disabled (warned once at construction). The DB read is wrapped
        #    fail-closed: if it raises we cannot prove we are under the cap, so we block.
        cap = self._config.daily_loss_cap
        if cap is not None:
            try:
                pnl_today = self._realized_pnl_today(state.date)
            except Exception:  # pragma: no cover - exercised via a raising fake
                logger.critical(
                    "AutoConfirm: realized-P&L read failed for session_date=%r — blocking "
                    "the trade fail-closed (cannot verify the daily-loss breaker).",
                    state.date,
                    exc_info=True,
                )
                return False, REASON_LOSS
            if pnl_today <= -cap:
                logger.warning(
                    "AutoConfirm: daily-loss breaker tripped — realized P&L %.2f <= -%.2f "
                    "for %s. No new trades until rollover.",
                    pnl_today,
                    cap,
                    state.date,
                )
                return False, REASON_LOSS

        # 5) Token budget (duck-typed; fail-soft by contract).
        if self._budget.is_exhausted():
            return False, REASON_BUDGET

        return True, None
