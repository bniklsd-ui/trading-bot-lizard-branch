"""Module 4 — the scheduler's persisted operational state (``scheduler_state.json``).

The daemon must survive restarts without double-counting trades, double-tripping the
backoff, or forgetting it already paused for the day. This module is that memory: a flat
:class:`SchedulerState` value plus a :class:`StateStore` that persists it atomically and
applies the two deterministic state transitions the loop (Module 11 ``runner.py``) needs:

- **day rollover** — reset the day-scoped counters when the Europe/Berlin date changes;
- **per-cycle bookkeeping** — count a real trade and fold in its immediate P&L.

Concept §3 + Decision 18. **No AI, no network, no broker — pure mechanics + one atomic
JSON file.**

Design points worth pinning (code = source of truth):

1. **Self-heal, never raise (load).** A missing file → a fresh state; corrupt/partial
   JSON → one WARNING + a fresh state. A data-collection daemon must not die because its
   state file got truncated by a hard kill — it re-initialises and carries on (the
   "state self-heal" noted in ``exceptions.py``). Unknown future keys are ignored and
   missing keys defaulted (forward/backward-compatible reconstruction).

2. **Atomic writes.** ``save`` writes a ``.tmp`` sibling then ``os.replace``s it over the
   target, so a crash mid-write never leaves a half-written file (the live file is only
   ever swapped, never appended in place). This re-implements the Phase-2
   ``StateManager._atomic_write`` *pattern* locally — copied, not imported, to keep
   ``scheduler`` phase-isolated (``import scheduler.state`` pulls nothing cross-phase).

3. **``realized_pnl_today`` is a best-effort persisted snapshot, NOT the loss-breaker's
   source of truth.** ``record_cycle`` folds in P&L only when the cycle result carries it
   — which at cycle time is the ``TIME_STOP`` path (verified Contract E:
   ``CLOSED_BY_BROKER`` returns ``profit_loss=None`` and is resolved later by the reconcile
   pass, Module 9). So this field can lag the DB for broker-closed trades. The
   authoritative daily-loss circuit breaker (``safety.py``, Module 5) reads today's
   realized P&L from the **DB** per Contract E; it does *not* depend on this field. Keeping
   the snapshot here (for the UI / persistence / rollover) while leaving the breaker on the
   DB avoids a double-count trap and keeps this module self-contained.

Repo conventions apply (``from __future__ import annotations``, type hints + docstrings,
one file = one responsibility, logging to a module logger, never swallow silently).
"""

from __future__ import annotations

import dataclasses
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

logger = logging.getLogger("scheduler.state")

# Execution statuses that count as a *real* trade for ``trades_today`` (verified
# Contract E — ``execution/models.py`` ``ExecutionResult.status``). NO_TRADE /
# ABORTED_BY_USER / ABORT are not trades and never increment the cap counter.
TRADE_STATUSES: frozenset[str] = frozenset({"OPEN", "CLOSED_BY_BROKER", "TIME_STOP"})


class CycleResult(Protocol):
    """The slice of a Phase-5 ``ExecutionResult`` that ``record_cycle`` reads.

    Duck-typed on purpose: ``scheduler`` does not import ``execution.models`` (phase
    isolation). Any object exposing these two attributes works — the real
    ``ExecutionResult`` does, and tests pass a tiny fake.
    """

    status: str
    profit_loss: float | None


@dataclass
class SchedulerState:
    """The daemon's persisted operational state (concept §3, Decision 18).

    Mutable by design — the loop both reassigns it from the store methods and mutates
    fields in place (e.g. ``state.last_no_trade_reason = reason``).

    Day-scoped (reset on rollover):
        date: the Europe/Berlin day this state describes, ``YYYY-MM-DD``. ``""`` means
            uninitialised (a fresh / missing file); the first ``rollover_if_new_day``
            stamps the real date.
        trades_today: count of real trades opened today (the ``max_trades_per_day`` cap
            counter). Incremented by ``record_cycle`` only for :data:`TRADE_STATUSES`.
        realized_pnl_today: best-effort persisted P&L snapshot for today (see the module
            docstring — NOT the loss-breaker's source of truth).
        consecutive_failures: consecutive cycle-exception count, owned by ``backoff.py``
            (``record_cycle`` never touches it); reset on rollover.
        kill_reason: the last recorded kill reason **for display only** — resetting it on
            rollover does *not* clear the ``KILL`` file (that is ``killswitch.py``'s job;
            a tripped switch still needs manual clearing).
        last_no_trade_reason: the last cycle's ``no_trade_reason`` (set by the loop /
            ``research_tick``), for the UI; reset on rollover.

    Cross-day (kept across rollover — genuine last-action timestamps, not counters):
        last_research_ts: ISO timestamp of the last real research trigger.
        last_reconcile_ts: ISO timestamp of the last reconcile pass.
        last_universe_refresh_ts: ISO timestamp of the last Phase-9 (V2) universe
            discover/promotion refresh (``None`` until the wiring injects a
            ``universe_refresher`` — default behaviour untouched otherwise).
    """

    date: str = ""
    trades_today: int = 0
    realized_pnl_today: float = 0.0
    last_research_ts: str | None = None
    last_reconcile_ts: str | None = None
    last_universe_refresh_ts: str | None = None
    consecutive_failures: int = 0
    kill_reason: str | None = None
    last_no_trade_reason: str | None = None
    last_no_trade_detail: str | None = None  # the LLM's prose abstain reason (display-only); reset on rollover


# Field names allowed when reconstructing from disk — computed once. Used to filter a
# loaded dict so unknown (future-schema) keys are ignored and missing keys default.
_FIELD_NAMES: frozenset[str] = frozenset(f.name for f in dataclasses.fields(SchedulerState))


class StateStore:
    """Persists :class:`SchedulerState` atomically and applies its day transitions.

    Args:
        state_path: path to ``scheduler_state.json`` (the gitignored ``data/state`` tree).
            The parent directory is created on construction if needed.
    """

    def __init__(self, state_path: str) -> None:
        self._path = Path(state_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    # --- persistence -------------------------------------------------------

    def load(self) -> SchedulerState:
        """Return the persisted state, self-healing on any failure (never raises).

        Missing file → a fresh ``SchedulerState`` (``date=""``). Corrupt / partial JSON,
        or any read error → one WARNING + a fresh state. Unknown keys are dropped and
        missing keys defaulted, so an older or newer on-disk schema still loads.
        """
        if not self._path.exists():
            return SchedulerState()
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("scheduler_state.json is not a JSON object")
            known = {k: v for k, v in data.items() if k in _FIELD_NAMES}
            return SchedulerState(**known)
        except (OSError, ValueError, json.JSONDecodeError, TypeError) as exc:
            logger.warning(
                "scheduler_state at %s unreadable (%s) — starting from a fresh state.",
                self._path,
                exc,
            )
            return SchedulerState()

    def save(self, state: SchedulerState) -> None:
        """Atomically write ``state`` to disk (``.tmp`` then ``os.replace``).

        The live file is only ever swapped in one atomic step, so a crash mid-write
        cannot leave it half-written (the Phase-2 ``_atomic_write`` pattern, copied).
        """
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(dataclasses.asdict(state), indent=2), encoding="utf-8"
        )
        os.replace(tmp, self._path)

    # --- transitions -------------------------------------------------------

    def rollover_if_new_day(
        self, state: SchedulerState, now: datetime
    ) -> SchedulerState:
        """Reset day-scoped fields if ``now`` is a new Europe/Berlin day; else no-op.

        ``now`` must be a tz-aware datetime in the daemon zone (the clock guarantees
        this — ``Clock.now()`` returns ``config.tz``); the local date string is taken
        directly from it (no tz logic here keeps the module stdlib-only). On a date
        change: ``trades_today``, ``realized_pnl_today`` and ``consecutive_failures`` go
        to zero, ``kill_reason`` and ``last_no_trade_reason`` to ``None``, and ``date``
        becomes today. ``last_research_ts`` / ``last_reconcile_ts`` are kept (genuine
        last-action timestamps, not day counters). Idempotent: a same-day call changes
        nothing. Mutates and returns the same object.

        Note: this resets the **state** ``kill_reason`` field only — it does not delete
        the ``KILL`` file (``killswitch.py`` owns that; a tripped switch needs manual
        clearing).
        """
        today = now.strftime("%Y-%m-%d")
        if state.date == today:
            return state
        state.date = today
        state.trades_today = 0
        state.realized_pnl_today = 0.0
        state.consecutive_failures = 0
        state.kill_reason = None
        state.last_no_trade_reason = None
        state.last_no_trade_detail = None
        return state

    def record_cycle(
        self, state: SchedulerState, result: CycleResult
    ) -> SchedulerState:
        """Fold one execution-cycle outcome into the day's bookkeeping.

        Increments ``trades_today`` iff ``result.status`` is a real trade
        (:data:`TRADE_STATUSES`, Contract E) — NO_TRADE / ABORT / ABORTED_BY_USER do not
        count. Adds ``result.profit_loss`` to ``realized_pnl_today`` when present
        (best-effort snapshot; only the TIME_STOP path carries it at cycle time — see the
        module docstring). Does not touch ``consecutive_failures`` (``backoff.py``),
        ``last_no_trade_reason`` (the loop / ``research_tick``), or the ts fields. Mutates
        and returns the same object.
        """
        if result.status in TRADE_STATUSES:
            state.trades_today += 1
        if result.profit_loss is not None:
            state.realized_pnl_today += result.profit_loss
        return state
