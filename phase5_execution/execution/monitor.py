"""The position-monitoring layer — polling loop + time-stop + close (concept §7).

Once :func:`order.place_order` has an **open** position, this module watches it and
ends it one of two ways (Decision H — polling, no Lightstreamer; that is Phase 8):

- **broker-side SL/TP filled** — the ``stop_level`` / ``limit_level`` set at entry
  (Step 6) fired and the position vanished from ``get_open_positions``. We just record
  it (``CLOSED_BY_BROKER``); we never placed that close, the broker did.
- **time-stop** — the square-off cutoff (``square_off_time``) or the max hold
  (``max_hold_minutes``) is reached → we ``close_position`` and record ``TIME_STOP``.

The entry SL/TP live broker-side, so they survive a monitor crash — this loop is the
*time-stop* and the *bookkeeping*, not the only safety net. ``now_fn`` / ``sleep_fn`` are
injected so tests drive the loop deterministically with no real waiting. The loop always
terminates: the time-stop fires as the wall clock advances.

Phase-isolated: ``execution.*`` + stdlib only; the broker is duck-typed (passed in, never
imported). Logging → **stderr**; stdout is the executor's JSON. Reuses
``gates._parse_hhmm`` + the ``gate_time_window`` tz idiom for the square-off cutoff so the
HH:MM/tz logic lives in one place.

Edge note (v1): if the position vanishes *between* the open-positions check and a
time-stop ``close_position``, that close errors (the deal_id is gone) → ``ExecutionAbort``.
Per concept §7 we keep abort-on-close-error for v1 (safe — no double action; the operator
reconciles) rather than parsing the error to tell "already gone" from a real failure.
"""

from __future__ import annotations

import logging
import time as _time
from datetime import datetime, timedelta
from typing import Any, Callable
from zoneinfo import ZoneInfo

from execution.config import ExecutionConfig
from execution.exceptions import ExecutionAbort
from execution.execution_state import ExecutionState
from execution.gates import _parse_hhmm
from execution.models import ExecutionResult, OrderPlan

logger = logging.getLogger(__name__)


def _is_after_square_off(now: datetime, config: ExecutionConfig) -> bool:
    """Is ``now`` (interpreted in ``config.tz``) at/after the square-off cutoff?

    Mirrors the ``gates.gate_time_window`` tz idiom: a tz-aware ``now`` is converted to
    ``config.tz``; a naive ``now`` is assumed already in-zone. Reuses
    ``gates._parse_hhmm`` for the ``HH:MM`` cutoff.
    """
    zone = ZoneInfo(config.tz)
    local = now.astimezone(zone) if now.tzinfo is not None else now
    return local.time() >= _parse_hhmm(config.square_off_time)


def _position_present(positions_env: Any, deal_id: str) -> bool:
    """True if ``deal_id`` is among the broker's open positions in ``positions_env``."""
    positions = (positions_env.data or {}).get("positions", [])
    return any(pos.get("deal_id") == deal_id for pos in positions)


def monitor_position(
    broker: Any,
    exec_state: ExecutionState,
    plan: OrderPlan,
    deal_id: str,
    config: ExecutionConfig,
    *,
    now_fn: Callable[[], datetime] = datetime.now,
    sleep_fn: Callable[[float], None] = _time.sleep,
) -> ExecutionResult:
    """Poll an open position until it closes (broker SL/TP) or the time-stop fires.

    Args:
        broker: duck-typed broker (``get_open_positions`` / ``close_position``).
        exec_state: the write-ahead store; the reference is marked closed on exit.
        plan: the placed :class:`OrderPlan` (carries ``deal_reference`` + ``epic``).
        deal_id: the broker deal id of the open position to watch.
        config: tunables (``poll_interval_s`` / ``square_off_time`` / ``max_hold_minutes``).
        now_fn / sleep_fn: injected clock / sleep — tests drive the loop with no real wait.

    Returns:
        ``ExecutionResult`` with status ``CLOSED_BY_BROKER`` or ``TIME_STOP``.

    Raises:
        ExecutionAbort: a ``close_position`` at the time-stop failed (operator attention).
    """
    ref = plan.deal_reference
    entry = now_fn()
    max_hold = timedelta(minutes=config.max_hold_minutes)
    logger.info("monitoring %s (deal_id=%s) from %s", ref, deal_id, entry.isoformat())

    while True:
        now = now_fn()

        # 1) Has the broker already closed it (SL/TP filled → position gone)?
        positions_env = broker.get_open_positions()
        if positions_env.ok:
            if not _position_present(positions_env, deal_id):
                exec_state.mark_closed(ref)
                logger.info("%s gone from broker — closed by broker SL/TP", ref)
                return ExecutionResult(
                    status="CLOSED_BY_BROKER",
                    deal_id=deal_id,
                    plan=plan,
                    detail="position no longer open at broker (SL/TP filled)",
                )
        else:
            # Uncertain read: do NOT infer a close. Keep polling; the time-stop still
            # guarantees the loop terminates.
            logger.warning(
                "%s: open-positions read failed — not inferring close, will retry", ref
            )

        # 2) Time-stop: square-off cutoff or max hold reached.
        after_square_off = _is_after_square_off(now, config)
        held_too_long = (now - entry) >= max_hold
        if after_square_off or held_too_long:
            trigger = "square_off" if after_square_off else "max_hold"
            close_env = broker.close_position(deal_id)
            if not close_env.ok:
                error = getattr(close_env, "error", None) or {}
                logger.error(
                    "%s: close_position failed at time-stop (%s): %s",
                    ref, trigger, error.get("code", "?"),
                )
                raise ExecutionAbort(
                    f"close_position for {ref} (deal_id={deal_id}) failed at time-stop "
                    f"({trigger}): {error.get('code', '?')} — operator must reconcile"
                )
            exec_state.mark_closed(ref)
            logger.info("%s closed by time-stop (%s)", ref, trigger)
            return ExecutionResult(
                status="TIME_STOP",
                deal_id=deal_id,
                plan=plan,
                detail=f"time-stop ({trigger})",
            )

        sleep_fn(config.poll_interval_s)
