"""The orchestrator — the whole execution cycle in one place (concept §8).

:class:`Executor` composes the individually-built, individually-tested pieces of
Phase 5 into a single ``run()``: session health → startup reconcile → the four
suitability Gates (1/2/3/5) → Gate 4 sizing → the four fresh-snapshot VETOs →
human-confirm → write-ahead placement → monitoring. It writes **no** new broker,
gate, or VETO logic; every rule already lives in ``gates.py`` / ``sizing.py`` /
``vetos.py`` / ``order.py`` / ``monitor.py``. This is pure composition.

**No AI here.** The only AI in the whole system is the lazy Phase-4
``research_runner`` reached through Gate 2 (``gate_load_candidates``) when no fresh
candidate is stored — injected, so this module never imports Phase 4.

Result vocabulary (documented in :mod:`execution.models`):

- ``CLOSED_BY_BROKER`` / ``TIME_STOP`` — a position was opened and ended (monitor).
- ``OPEN`` — opened, monitor returned it open (only if monitoring is skipped).
- ``NO_TRADE`` — a gate/VETO/abstain said no; clean, exit 0.
- ``ABORTED_BY_USER`` — human-confirm declined; no order placed.
- ``ABORT`` — fail-closed: session health, reconcile, an unresolved ``PENDING``
  order, or a failed time-stop close. ``ig_bot.py`` (Step 9) exits non-zero on this.

Aborts are **returned**, not raised: ``ExecutionAbort`` / ``ReconcileConflict``
(both ``ExecutionError``, neither a subclass of the other) are caught at the run
boundary and surfaced as ``ExecutionResult(status="ABORT", ...)`` so the CLI has a
single result object to serialise. Every gate/VETO/abort reason is logged to
**stderr**; stdout is reserved for that machine-readable JSON (Step 9).

Determinism: ``now_fn`` / ``sleep_fn`` are injected (keyword-only, defaulting to the
real clock / sleep) — the same pattern ``monitor.py`` and ``order.py`` already use,
so tests drive Gate 1, the VETO window check, the PENDING re-check loop, and the
monitor loop with no real time passing. The §8 signature stub did not list them; this
is a code-as-source-of-truth reconciliation (dated §8 annotation).

Phase-isolated: ``execution.*`` + stdlib only; broker / db / state are duck-typed
(passed in, never imported).
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Callable

from execution.config import ExecutionConfig
from execution.exceptions import ExecutionAbort, ReconcileConflict
from execution.execution_state import ExecutionState
from execution.gates import (
    gate_constraints,
    gate_direction_consistency,
    gate_load_candidates,
    gate_time_window,
)
from execution.models import ExecutionResult, OrderPlan
from execution.monitor import monitor_position
from execution.order import build_order_plan, place_order, reconcile_startup
from execution.sizing import compute_size, select_risk_pct
from execution.vetos import pre_trade_check

logger = logging.getLogger(__name__)


class Executor:
    """Run one execution cycle (concept §8). All collaborators are injected (DI)."""

    def __init__(
        self,
        broker: Any,
        db: Any,
        state: Any,
        exec_state: ExecutionState,
        config: ExecutionConfig,
        research_runner: Callable[[], list[dict[str, Any]]],
        confirm_fn: Callable[[OrderPlan], bool],
        *,
        now_fn: Callable[[], datetime] = datetime.now,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        """Wire the cycle's collaborators.

        Args:
            broker: duck-typed broker (the :class:`~execution.protocols.BrokerProtocol`
                surface — session, market probes, OHLCV, order/close/reconcile).
            db: read-only :class:`~execution.protocols.DbProtocol` (risk level / score).
            state: :class:`~execution.protocols.StateProtocol` (candidate JSON store).
            exec_state: the write-ahead idempotency store (Phase 5's own JSON file).
            config: the run's :class:`ExecutionConfig` (all tunables).
            research_runner: lazy Phase-4 runner for Gate 2 (``build_research(cfg).run``);
                injected so Phase 4 stays out of this module.
            confirm_fn: human-confirm predicate (``ig_bot`` stdin prompt; ``--yes`` →
                ``lambda _p: True``; tests: a stub).
            now_fn / sleep_fn: injected clock / sleep for deterministic tests.
        """
        self.broker = broker
        self.db = db
        self.state = state
        self.exec_state = exec_state
        self.config = config
        self.research_runner = research_runner
        self.confirm_fn = confirm_fn
        self.now_fn = now_fn
        self.sleep_fn = sleep_fn

    # -- result helpers -----------------------------------------------------

    @staticmethod
    def _no_trade(rule: str, reason: str) -> ExecutionResult:
        """A clean no-trade outcome (gate/VETO/abstain) — exit 0, no order placed."""
        logger.info("no trade: %s — %s", rule, reason)
        return ExecutionResult(
            status="NO_TRADE", deal_id=None, plan=None, detail=f"{rule}: {reason}"
        )

    @staticmethod
    def _abort(detail: str, *, plan: OrderPlan | None = None,
               deal_id: str | None = None) -> ExecutionResult:
        """A fail-closed abort outcome — the CLI exits non-zero, operator attends."""
        logger.error("abort: %s", detail)
        return ExecutionResult(
            status="ABORT", deal_id=deal_id, plan=plan, detail=detail
        )

    # -- the cycle ----------------------------------------------------------

    def run(self) -> ExecutionResult:
        """Execute one cycle. Returns the outcome; never lets an abort escape.

        See the module docstring for the status vocabulary and the abort-is-returned
        contract. The flow short-circuits at the first gate/VETO that says no.
        """
        # 1) Session health + 2) startup reconcile — both can fail closed.
        try:
            account_env = self._ensure_session()
            reconcile_startup(self.broker, self.exec_state, self.config)
        except (ExecutionAbort, ReconcileConflict) as exc:
            return self._abort(str(exc))

        # 3) Gate 1 — trade window. ``now`` is captured once and reused for the
        # VETO window check (the VETOs' freshness comes from re-fetched broker
        # snapshots, not the wall clock).
        now = self.now_fn()
        g1 = gate_time_window(now, self.config)
        if not g1.ok:
            return self._no_trade(g1.gate, g1.reason)

        # 4) Gate 2 — fresh research candidate (runs research lazily if stale).
        g2, candidate = gate_load_candidates(
            self.state, self.research_runner, self.config
        )
        if not g2.ok or candidate is None:
            return self._no_trade(g2.gate, g2.reason)

        # 5) Gate 3 + Gate 5 — share one fresh open-positions snapshot.
        positions_env = self.broker.get_open_positions()
        g3 = gate_constraints(account_env, positions_env, candidate, self.config)
        if not g3.ok:
            return self._no_trade(g3.gate, g3.reason)
        g5 = gate_direction_consistency(candidate, positions_env)
        if not g5.ok:
            return self._no_trade(g5.gate, g5.reason)

        # 6) Gate 4 — sizing. One fresh price (reused by build_order_plan) + market info.
        epic = candidate["epic"]
        price_env = self.broker.get_price(epic)
        market_info_env = self.broker.get_market_info(epic)
        risk_pct = select_risk_pct(self.db, self.config)
        size, size_reason = compute_size(
            account_env, price_env, market_info_env, risk_pct, self.config
        )
        if size_reason is not None:
            return self._no_trade("sizing", size_reason)

        # 7) The four HARD VETOs on a fresh snapshot, immediately before the order.
        veto = pre_trade_check(self.broker, candidate, now, self.config)
        if not veto.ok:
            return self._no_trade(veto.veto, veto.reason)

        # 8) Build the resolved order plan (reuse the Gate-4 fresh price + market info).
        plan = build_order_plan(candidate, size, price_env, market_info_env, self.config)

        # 9) Human-confirm — the last gate before any broker order (Decision D).
        if self.config.require_confirm and not self.confirm_fn(plan):
            logger.info("human-confirm declined for %s — no order placed", plan.deal_reference)
            return ExecutionResult(
                status="ABORTED_BY_USER",
                deal_id=None,
                plan=plan,
                detail="human-confirm declined",
            )

        # 10) Place (write-ahead, PENDING fail-closed), then monitor if open.
        try:
            place_result = place_order(
                self.broker, self.exec_state, plan, self.config, sleep_fn=self.sleep_fn
            )
            if place_result.status == "OPEN":
                return monitor_position(
                    self.broker,
                    self.exec_state,
                    plan,
                    place_result.deal_id,
                    self.config,
                    now_fn=self.now_fn,
                    sleep_fn=self.sleep_fn,
                )
            return place_result
        except (ExecutionAbort, ReconcileConflict) as exc:
            return self._abort(str(exc), plan=plan)

    # -- internals ----------------------------------------------------------

    def _ensure_session(self) -> Any:
        """Verify the broker session is healthy; return the account envelope.

        Connects if needed (``.ok`` required) and fetches the account (``.ok``
        required). The account envelope is returned so the caller reuses it for
        Gate 3 and sizing — one ``get_account`` per cycle.

        Raises:
            ExecutionAbort: connect failed or the account snapshot is not ``ok``.
        """
        if not self.broker.is_connected():
            connect_env = self.broker.connect()
            if not connect_env.ok:
                error = getattr(connect_env, "error", None) or {}
                raise ExecutionAbort(
                    f"broker connect failed ({error.get('code', '?')}) — cannot proceed"
                )

        account_env = self.broker.get_account()
        if not account_env.ok:
            error = getattr(account_env, "error", None) or {}
            raise ExecutionAbort(
                f"account snapshot unavailable ({error.get('code', '?')}) — "
                "session health unverifiable, failing closed"
            )
        return account_env
