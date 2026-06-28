"""Module 10 (concept §9) — ``Reconciler``: the idempotent reconcile pass.

The daemon's data-recovery pass, run on startup, periodically, and at shutdown (the *scheduling*
is the runner's job, §10). Its mission-critical half: when a trade closes but its P&L could not be
resolved in-cycle — IG books transaction history only *after settlement* (the verified intraday
lag), so a ``CLOSED_BY_BROKER`` close legitimately leaves the ``trade_outcomes`` row **OPEN** with
no reward/lesson — a later pass retries that row once IG history catches up. That is the only way
the demo outcome data the whole phase exists to collect actually lands. Secondarily it cleans
orphaned PENDING references between windows.

**No AI, no reimplementation** — pure composition of two already-built, already-tested pieces
(verified Contract F: *"reconcile.py ist Komposition dieser beiden, keine Reimplementierung"*):

- **orphan PENDING** — the Phase-5 ``execution/order.py`` ``reconcile_startup`` (compares our
  in-flight references to broker truth; marks orphans closed, conflicts loud). It already runs
  inside *every* ``executor.run()``, so the scheduler pass only adds *between-window* coverage.
- **CLOSED_BY_BROKER P&L catch-up** — the Phase-7 ``RewardSink.reconcile_open_trades(None)``
  (re-runs the guarded close for every still-OPEN row: history-resolve → ``update_trade_close`` +
  ``insert_reward``, idempotent via the OPEN/CLOSED status, never raises).

**Both collaborators are injected, not imported** — this is what preserves the scheduler's
verified import-isolation (``import scheduler.reconcile`` pulls nothing cross-phase). ``reward_sink``
is duck-typed (:class:`_RewardSinkLike`); the orphan-PENDING pass is a **zero-arg
``pending_reconcile_fn`` closure** the wiring (Module 11) binds over the shared
broker/exec_state/``ExecutionConfig`` at the composition root, where cross-phase imports are
allowed. This mirrors the established scheduler pattern (``safety.Budget`` / ``state.CycleResult``
/ ``research_tick._ResearchLike``).

Fail-closed throughout: each half is individually guarded so a failure logs ``critical`` and the
pass continues — the tick **never raises into the loop** (concept §9 / ``exceptions.py``: the loop
treats a reconcile failure like any cycle error, it does not crash the daemon).

Repo conventions apply (``from __future__ import annotations``, type hints + docstrings, one file =
one responsibility, logging to a module logger, never swallow silently).

---

Concept↔code reconciliations (dated 2026-06-28, code = source of truth):

1. **Ctor ``Reconciler(reward_sink, pending_reconcile_fn, *, now_fn)``** vs the §9 sketch
   ``(broker, db, reward_sink, state_store)``: ``broker`` + the Phase-5 ``reconcile_startup`` are
   folded into the injected ``pending_reconcile_fn`` closure (import-isolation); ``db`` is dropped
   (``reward_sink`` owns it — ``reconcile_open_trades`` is self-contained); ``state_store`` is
   dropped (this module mutates ``state.last_reconcile_ts`` and the **runner** persists, consistent
   with ``research_tick`` / ``record_cycle`` / ``backoff``); ``now_fn`` is added (determinism /
   timestamp source).

2. **Composition, not reimplementation** (Contract F): ``reconcile_open_trades`` already does the
   history-resolve → ``update_trade_close`` + ``insert_reward``, idempotent. This module does **not**
   re-implement the §9 "step 2" SQL — it calls the tested Phase-7 method.

3. **The orphan-PENDING half is partly redundant** with the executor's own per-cycle
   ``reconcile_startup``; the scheduler pass adds the between-window coverage and pairs it with the
   P&L catch-up the executor does not do.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Protocol

from scheduler.state import SchedulerState

logger = logging.getLogger("scheduler.reconcile")


@dataclass(frozen=True)
class ReconcileReport:
    """The outcome of one reconcile tick (for the runner + tests).

    Attributes:
        pending_ok: ``True`` if the orphan-PENDING pass completed without a conflict/error.
        resolved_deal_ids: deals that reached a non-OPEN status on this pass (P&L caught up).
        n_resolved: ``len(resolved_deal_ids)`` — convenience for logging.
    """

    pending_ok: bool
    resolved_deal_ids: list[str]
    n_resolved: int


class _RewardSinkLike(Protocol):
    """The slice of the Phase-7 ``RewardSink`` the reconcile pass needs (duck-typed)."""

    def reconcile_open_trades(self, deal_ids: list[str] | None = None) -> list[str]: ...


class Reconciler:
    """Runs the idempotent reconcile pass: orphan-PENDING cleanup + P&L catch-up (concept §9).

    Args:
        reward_sink: anything satisfying :class:`_RewardSinkLike` (the Phase-7 ``RewardSink`` does);
            its ``reconcile_open_trades`` is the CLOSED_BY_BROKER P&L catch-up.
        pending_reconcile_fn: a zero-arg callable that runs the orphan-PENDING reconcile (the wiring
            binds Phase-5 ``reconcile_startup`` over the shared broker/exec_state/config). May raise
            (``ReconcileConflict`` / ``ExecutionAbort``); :meth:`tick` catches it.
        now_fn: returns the current (ideally tz-aware) time used to stamp ``last_reconcile_ts``.
            Defaults to UTC now; the runner injects ``clock.now``.
    """

    def __init__(
        self,
        reward_sink: _RewardSinkLike,
        pending_reconcile_fn: Callable[[], None],
        *,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        self._reward_sink = reward_sink
        self._pending_reconcile_fn = pending_reconcile_fn
        self._now_fn = now_fn or (lambda: datetime.now(timezone.utc))

    def tick(self, state: SchedulerState) -> ReconcileReport:
        """Run one reconcile pass and record it onto ``state``. Never raises (fail-closed).

        Runs both halves independently (a failure in one does not skip the other), stamps
        ``state.last_reconcile_ts``, and returns a :class:`ReconcileReport`. The runner persists
        the state afterwards.
        """
        # 1) Orphan-PENDING pass (the P5 reconcile_startup, injected). It raises on an
        #    unexpected/unverifiable broker position; we contain that — the P&L catch-up below is
        #    the important half and must still run.
        pending_ok = True
        try:
            self._pending_reconcile_fn()
        except Exception:  # noqa: BLE001 - ReconcileConflict/ExecutionAbort/anything; never crash the loop
            logger.critical(
                "reconcile: orphan-PENDING pass failed — continuing to the P&L catch-up.",
                exc_info=True,
            )
            pending_ok = False

        # 2) CLOSED_BY_BROKER P&L catch-up (the P7 reconcile_open_trades; None = all OPEN rows).
        #    The real method is total (never raises, returns []), but it is duck-typed → guard it.
        try:
            resolved = self._reward_sink.reconcile_open_trades()
        except Exception:  # noqa: BLE001 - defensive: the protocol is duck-typed
            logger.critical(
                "reconcile: P&L catch-up (reconcile_open_trades) raised — none resolved this pass.",
                exc_info=True,
            )
            resolved = []

        # 3) Stamp the pass (it ran, whatever the two halves did).
        state.last_reconcile_ts = self._now_fn().isoformat()

        if resolved:
            logger.info("reconcile: resolved %d open trade(s): %s", len(resolved), resolved)
        return ReconcileReport(
            pending_ok=pending_ok,
            resolved_deal_ids=list(resolved),
            n_resolved=len(resolved),
        )
