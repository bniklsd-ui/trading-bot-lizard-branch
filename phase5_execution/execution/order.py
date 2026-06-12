"""The order-placement layer — write-ahead, confirm, PENDING fail-closed (concept §6).

This is the first module that actually tells the broker to **open** a position, so
it is the highest-risk module in Phase 5. Decision E (concept §0) governs it:

- The bot's own ``deal_reference`` is persisted **write-ahead** (``record_pending``)
  **before** ``open_position`` is ever invoked. If the process dies between "about to
  order" and "broker confirmed", startup reconcile finds the dangling reference.
- A ``PENDING`` confirm-timeout (or an opaque transport error) **never** triggers a
  blind second order. ``place_order`` does a bounded re-check via
  ``reconcile_positions`` and, if still unresolved, leaves the record ``PENDING`` and
  fails closed (``ExecutionAbort``) for the operator — the next ``reconcile_startup``
  resolves it. There is exactly **one** ``open_position`` invocation per ``place_order``.

Three functions:

- :func:`reconcile_startup` — run before every cycle; clean up orphaned references and
  fail closed on an unexpected broker position rather than stacking another order.
- :func:`build_order_plan` — pure: turn a candidate + size + fresh price into an
  :class:`OrderPlan` with absolute, direction-aware ``stop_level`` / ``limit_level`` and
  a fresh write-ahead ``deal_reference``.
- :func:`place_order` — the guarded placement itself.

Phase-isolated: ``execution.*`` + stdlib only. The broker is duck-typed
(``BrokerProtocol``), passed in — never imported. Logging → **stderr** (root config);
stdout is reserved for the executor's machine-readable JSON.

Reconciliation vs concept §6 (code = source of truth, dated §6 annotation): the concept
sketched *"klarer Reject (z.B. nicht-retryable error) → mark_closed; raise"*. Only a
confirmed ``REJECTED`` status definitively means no position → we ``mark_closed``. An
opaque ``not env.ok`` transport error is **ambiguous** (the order may be live), so it is
treated like ``PENDING``: the record stays open and we fail closed — the safest reading of
"never place a blind second order". Also: ``deal_reference`` is capped to IG's 30-char
limit (``bot-`` + 24 hex = 28), matching the adapter's own ``_new_deal_reference``.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable
from uuid import uuid4

from execution.config import ExecutionConfig
from execution.exceptions import ExecutionAbort, ReconcileConflict
from execution.execution_state import ExecutionState
from execution.models import ExecutionResult, OrderPlan

logger = logging.getLogger(__name__)

# Order-confirmation statuses from the broker (``OrderResult.status``,
# normalised by the adapter). ACCEPTED = confirmed open; REJECTED = confirmed no
# position; PENDING = confirm timed out (state unknown); UNKNOWN = unexpected.
_ACCEPTED = "ACCEPTED"
_REJECTED = "REJECTED"
_PENDING = "PENDING"


def reconcile_startup(
    broker: Any, exec_state: ExecutionState, config: ExecutionConfig
) -> None:
    """Reconcile our in-flight references against broker truth, before a cycle.

    Compares ``exec_state.open_references()`` (PENDING/OPEN) to the broker's actual
    positions via ``reconcile_positions``. Resolves orphans and, when configured, fails
    closed on a position the broker has but we do not — rather than stacking another order.

    Outcomes:
      - ``missing`` (we think open, broker has none) → ``exec_state.mark_closed`` (orphan).
      - ``unexpected`` (broker has, we have no record) → ``ReconcileConflict`` when
        ``config.reconcile_unexpected_aborts`` else a WARNING.
      - ``present`` → left as is (genuinely open, the monitor handles it).

    Raises:
        ExecutionAbort: the reconcile envelope is not ``ok`` (broker truth unverifiable).
        ReconcileConflict: an unexpected broker position with abort-on-unexpected on.
    """
    refs = exec_state.open_references()
    if not refs:
        return

    env = broker.reconcile_positions(expected_references=refs)
    if not env.ok:
        raise ExecutionAbort(
            "startup reconcile failed — broker positions could not be verified; "
            "refusing to proceed (fail-closed)"
        )

    data = env.data or {}
    missing = data.get("missing", [])
    unexpected = data.get("unexpected", [])

    for ref in missing:
        logger.info("reconcile: %s missing at broker — marking closed (orphan)", ref)
        exec_state.mark_closed(ref)

    if unexpected:
        if config.reconcile_unexpected_aborts:
            raise ReconcileConflict(
                f"unexpected broker position(s) {unexpected} with no local record — "
                "aborting rather than stacking another order"
            )
        logger.warning(
            "reconcile: unexpected broker position(s) %s with no local record", unexpected
        )


def build_order_plan(
    candidate: dict[str, Any],
    size: float,
    price_env: Any,
    market_info_env: Any,
    config: ExecutionConfig,
) -> OrderPlan:
    """Build the resolved :class:`OrderPlan` from a candidate, size and fresh price.

    Pure (no I/O, no broker). The ``deal_reference`` is a fresh ``bot-<24 hex>`` (≤30
    chars, matching the adapter's own helper / IG's limit). ``stop_level`` /
    ``limit_level`` are **absolute** levels computed direction-aware from the entry-side
    price and the config point distances:

      - BUY  → stop **below** / limit **above** the entry price.
      - SELL → stop **above** / limit **below** the entry price.

    ``currency`` is the instrument's ``market_info`` currency (IG's required
    ``currencyCode`` — a null one is rejected with HTTP 400), falling back to
    ``config.default_currency`` when the env is not ok / lacks a currency.

    Args:
        candidate: the Phase-4 contract dict (``epic`` / ``direction`` consumed here).
        size: the rounded position size from Gate 4 (``sizing.py``).
        price_env: the fresh ``get_price`` envelope (``.data`` has ``bid`` / ``ask``).
        market_info_env: the fresh ``get_market_info`` envelope (``.data`` has
            ``currency``); reused from Gate-4 sizing.
        config: tunables (``stop_distance_points`` / ``limit_distance_points`` /
            ``default_currency``).
    """
    epic = candidate["epic"]
    direction = candidate["direction"]
    data = price_env.data or {}
    currency = (getattr(market_info_env, "data", None) or {}).get(
        "currency"
    ) or config.default_currency

    # Entry-side reference price: cross the spread the way the order will fill.
    if direction == "BUY":
        ref_price = data.get("ask") if data.get("ask") is not None else data.get("bid")
    else:  # SELL
        ref_price = data.get("bid") if data.get("bid") is not None else data.get("ask")
    ref_price = float(ref_price)

    stop_pts = config.stop_distance_points
    limit_pts = config.limit_distance_points
    if direction == "BUY":
        stop_level = ref_price - stop_pts
        limit_level = ref_price + limit_pts
    else:  # SELL
        stop_level = ref_price + stop_pts
        limit_level = ref_price - limit_pts

    return OrderPlan(
        epic=epic,
        direction=direction,
        size=size,
        stop_level=stop_level,
        limit_level=limit_level,
        deal_reference=f"bot-{uuid4().hex[:24]}",
        currency=currency,
    )


def _resolve_pending(
    broker: Any,
    exec_state: ExecutionState,
    plan: OrderPlan,
    config: ExecutionConfig,
    sleep_fn: Callable[[float], None],
) -> ExecutionResult:
    """Bounded re-check of a PENDING/UNKNOWN order — never a second order.

    Re-checks the broker up to ``config.pending_recheck_attempts`` times. If the
    reference turns up present, marks it open and returns OPEN. Otherwise leaves the
    record PENDING (it may be live — startup reconcile resolves it) and fails closed.

    Raises:
        ExecutionAbort: still unresolved after all attempts (fail-closed, operator).
    """
    ref = plan.deal_reference
    for attempt in range(1, config.pending_recheck_attempts + 1):
        env = broker.reconcile_positions(expected_references=[ref])
        if env.ok and ref in (env.data or {}).get("present", []):
            deal_id = _lookup_deal_id(broker, ref)
            exec_state.mark_open(ref, deal_id or "")
            logger.info("order %s resolved present on re-check %d", ref, attempt)
            return ExecutionResult(
                status="OPEN",
                deal_id=deal_id,
                plan=plan,
                detail=f"PENDING resolved present on re-check {attempt}",
            )
        if attempt < config.pending_recheck_attempts:
            sleep_fn(config.pending_recheck_interval_s)

    # Unresolved: do NOT mark_closed (the order may be live) and do NOT re-order.
    logger.error(
        "order %s still unresolved after %d re-checks — leaving PENDING, failing closed",
        ref, config.pending_recheck_attempts,
    )
    raise ExecutionAbort(
        f"order {ref} PENDING/unresolved after {config.pending_recheck_attempts} "
        "re-checks — left PENDING for startup reconcile; no second order placed"
    )


def _lookup_deal_id(broker: Any, deal_reference: str) -> str | None:
    """Best-effort: find the broker ``deal_id`` for one of our references.

    Used after a PENDING order reconciles as present (``reconcile_positions`` returns
    references, not deal_ids). A missing deal_id is not fatal — the reference is the
    idempotency key; the monitor can still operate on it. Fail-closed against a not-``ok``
    listing (returns ``None``, the record stays open).
    """
    env = broker.get_open_positions()
    if not env.ok:
        return None
    for pos in (env.data or {}).get("positions", []):
        if pos.get("deal_reference") == deal_reference:
            return pos.get("deal_id")
    return None


def place_order(
    broker: Any,
    exec_state: ExecutionState,
    plan: OrderPlan,
    config: ExecutionConfig,
    *,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> ExecutionResult:
    """Place ``plan`` with write-ahead idempotency and PENDING fail-closed (Decision E).

    Sequence:
      1. ``exec_state.record_pending(plan)`` — **write-ahead, before any broker order**.
      2. **One** ``open_position`` invocation with our ``deal_reference``.
      3. Branch on the confirmed status:
         - ACCEPTED → ``mark_open`` → ``ExecutionResult(status="OPEN")``.
         - PENDING / UNKNOWN → bounded re-check (no second order); resolved → OPEN, else
           leave PENDING and ``ExecutionAbort``.
         - REJECTED → ``mark_closed`` (broker confirmed no position) → ``ExecutionAbort``.
         - ``not env.ok`` (transport error) → ambiguous → leave PENDING → ``ExecutionAbort``.

    ``sleep_fn`` is injected so tests drive the re-check loop without real waiting.

    Raises:
        ExecutionAbort: unresolved PENDING/transport error, or a confirmed REJECTED order.
    """
    ref = plan.deal_reference

    # 1) WRITE-AHEAD — persisted before the broker ever hears about this order.
    exec_state.record_pending(plan)

    # 2) The single open_position invocation.
    env = broker.open_position(
        plan.epic,
        plan.direction,
        plan.size,
        stop_level=plan.stop_level,
        limit_level=plan.limit_level,
        deal_reference=ref,
        currency=plan.currency,
    )

    # 4) Transport error: ambiguous whether the order landed → fail closed, stay PENDING.
    if not env.ok:
        error = getattr(env, "error", None) or {}
        code = error.get("code", "?")
        # Surface the broker's underlying message too — for a generic BROKER_ERROR the
        # real IG errorCode lives there (e.g. min stop distance / level precision), not
        # in the mapped code. Without it the abort reason is undiagnosable.
        message = error.get("message", "")
        logger.error(
            "open_position transport error for %s (%s: %s) — leaving PENDING, failing closed",
            ref, code, message,
        )
        raise ExecutionAbort(
            f"open_position for {ref} returned a transport error "
            f"({code}: {message}); state unknown — left PENDING for startup "
            "reconcile; no second order placed"
        )

    data = env.data or {}
    status = data.get("status")

    # 3a) Confirmed open.
    if status == _ACCEPTED:
        deal_id = data.get("deal_id")
        exec_state.mark_open(ref, deal_id or "")
        logger.info("order %s ACCEPTED (deal_id=%s)", ref, deal_id)
        return ExecutionResult(
            status="OPEN", deal_id=deal_id, plan=plan, detail="order accepted",
        )

    # 3b) Confirm timed out / unexpected — bounded re-check, never a second order.
    if status == _PENDING or status not in (_ACCEPTED, _REJECTED):
        logger.warning("order %s status %r — entering bounded re-check", ref, status)
        return _resolve_pending(broker, exec_state, plan, config, sleep_fn)

    # 3c) Broker confirmed rejection → no position exists. Surface it.
    exec_state.mark_closed(ref)
    reason = data.get("reason") or "no reason given"
    logger.error("order %s REJECTED by broker: %s", ref, reason)
    raise ExecutionAbort(f"order {ref} REJECTED by broker: {reason}")
