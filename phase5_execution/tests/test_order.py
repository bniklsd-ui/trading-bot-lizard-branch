"""Step 6 — ``order.py``: write-ahead place, PENDING fail-closed, startup reconcile.

All mocked, no network, **no real order**. The single hardest invariant (Decision E):
exactly **one** ``open_position`` invocation per ``place_order`` and never a blind second
order on a PENDING / transport-error outcome.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pytest

from execution.config import ExecutionConfig
from execution.exceptions import ExecutionAbort, ReconcileConflict
from execution.execution_state import CLOSED, OPEN, PENDING, ExecutionState
from execution.models import OrderPlan
from execution.order import build_order_plan, place_order, reconcile_startup
from tests.conftest import DEFAULT_EPIC, FakeBroker, _FakeEnv


@pytest.fixture
def config() -> ExecutionConfig:
    """Default config but with a fast re-check loop (still mocked sleep)."""
    return ExecutionConfig(pending_recheck_attempts=3, pending_recheck_interval_s=0.0)


@pytest.fixture
def exec_state(tmp_path: Path) -> ExecutionState:
    return ExecutionState(str(tmp_path / "state" / "execution_state.json"))


def _no_sleep(_seconds: float) -> None:
    """Injected ``sleep_fn`` — never actually wait in tests."""
    return None


# --- build_order_plan -----------------------------------------------------


def test_build_order_plan_buy_levels_and_reference(
    make_candidate: Callable[..., dict[str, Any]],
) -> None:
    config = ExecutionConfig()
    candidate = make_candidate(direction="BUY")
    price_env = _FakeEnv(ok=True, data={"bid": 17999.0, "ask": 18000.0})

    plan = build_order_plan(candidate, size=0.5, price_env=price_env, config=config)

    # BUY fills at ask; stop below, limit above.
    assert plan.direction == "BUY"
    assert plan.stop_level == 18000.0 - config.stop_distance_points
    assert plan.limit_level == 18000.0 + config.limit_distance_points
    assert plan.stop_level < 18000.0 < plan.limit_level
    assert plan.deal_reference.startswith("bot-")
    assert len(plan.deal_reference) <= 30  # IG dealReference limit


def test_build_order_plan_sell_levels_inverted(
    make_candidate: Callable[..., dict[str, Any]],
) -> None:
    config = ExecutionConfig()
    candidate = make_candidate(direction="SELL")
    price_env = _FakeEnv(ok=True, data={"bid": 17999.0, "ask": 18000.0})

    plan = build_order_plan(candidate, size=0.5, price_env=price_env, config=config)

    # SELL fills at bid; stop above, limit below.
    assert plan.stop_level == 17999.0 + config.stop_distance_points
    assert plan.limit_level == 17999.0 - config.limit_distance_points
    assert plan.limit_level < 17999.0 < plan.stop_level


def test_build_order_plan_reference_is_unique(
    make_candidate: Callable[..., dict[str, Any]],
) -> None:
    config = ExecutionConfig()
    price_env = _FakeEnv(ok=True, data={"bid": 17999.0, "ask": 18000.0})
    plan_a = build_order_plan(make_candidate(), 0.5, price_env, config)
    plan_b = build_order_plan(make_candidate(), 0.5, price_env, config)
    assert plan_a.deal_reference != plan_b.deal_reference


# --- place_order: write-ahead + ACCEPTED ----------------------------------


def test_place_order_writes_ahead_before_open_position(
    exec_state: ExecutionState, order_plan: OrderPlan, config: ExecutionConfig
) -> None:
    """The PENDING record exists by the time open_position is invoked (write-ahead)."""
    recorded_at_call: list[bool] = []

    class _AssertingBroker(FakeBroker):
        def open_position(self, *args: Any, **kwargs: Any) -> _FakeEnv:
            # When the broker is invoked, the write-ahead record must already exist.
            record = exec_state.get(order_plan.deal_reference)
            recorded_at_call.append(record is not None and record["status"] == PENDING)
            return super().open_position(*args, **kwargs)

    broker = _AssertingBroker()
    place_order(broker, exec_state, order_plan, config, sleep_fn=_no_sleep)

    assert recorded_at_call == [True]


def test_place_order_accepted_marks_open(
    exec_state: ExecutionState, order_plan: OrderPlan, config: ExecutionConfig
) -> None:
    broker = FakeBroker()  # default open_env = ACCEPTED, deal_id DIAAAA-FAKE
    result = place_order(broker, exec_state, order_plan, config, sleep_fn=_no_sleep)

    assert result.status == "OPEN"
    assert result.deal_id == "DIAAAA-FAKE"
    assert len(broker.open_position_calls) == 1
    record = exec_state.get(order_plan.deal_reference)
    assert record is not None
    assert record["status"] == OPEN
    assert record["deal_id"] == "DIAAAA-FAKE"
    # open_position received our absolute levels + write-ahead reference.
    placed = broker.open_position_calls[0]
    assert placed["deal_reference"] == order_plan.deal_reference
    assert placed["stop_level"] == order_plan.stop_level
    assert placed["limit_level"] == order_plan.limit_level


# --- place_order: PENDING fail-closed -------------------------------------


def _pending_open_env() -> _FakeEnv:
    return _FakeEnv(
        ok=True,
        data={
            "deal_reference": None,
            "deal_id": None,
            "status": "PENDING",
            "epic": DEFAULT_EPIC,
            "direction": "BUY",
            "size": 0.5,
            "level": None,
            "reason": "confirm timeout — reconcile later",
            "timestamp": "2026-06-11T09:05:01Z",
        },
    )


def test_place_order_pending_then_present_marks_open(
    exec_state: ExecutionState, order_plan: OrderPlan, config: ExecutionConfig
) -> None:
    """PENDING confirm but the order is actually live → re-check resolves it to OPEN."""
    ref = order_plan.deal_reference
    broker = FakeBroker(
        open_env=_pending_open_env(),
        reconcile_env=_FakeEnv(
            ok=True,
            data={"present": [ref], "missing": [], "unexpected": []},
        ),
        positions_env=_FakeEnv(
            ok=True,
            data={"positions": [{"deal_reference": ref, "deal_id": "DIAAAA-LIVE"}]},
        ),
    )

    result = place_order(broker, exec_state, order_plan, config, sleep_fn=_no_sleep)

    assert result.status == "OPEN"
    assert result.deal_id == "DIAAAA-LIVE"
    assert len(broker.open_position_calls) == 1  # never a second order
    assert exec_state.get(ref)["status"] == OPEN


def test_place_order_pending_unresolved_aborts_and_stays_pending(
    exec_state: ExecutionState, order_plan: OrderPlan, config: ExecutionConfig
) -> None:
    """PENDING stays unresolved → ExecutionAbort, record stays PENDING, ONE order."""
    ref = order_plan.deal_reference
    broker = FakeBroker(open_env=_pending_open_env())  # reconcile default: present empty

    with pytest.raises(ExecutionAbort):
        place_order(broker, exec_state, order_plan, config, sleep_fn=_no_sleep)

    assert len(broker.open_position_calls) == 1  # the core invariant
    # Re-checked the configured number of times, never re-ordered.
    assert len(broker.reconcile_calls) == config.pending_recheck_attempts
    record = exec_state.get(ref)
    assert record["status"] == PENDING  # NOT closed — may be live; reconcile next run
    assert ref in exec_state.open_references()


def test_place_order_unknown_status_uses_recheck(
    exec_state: ExecutionState, order_plan: OrderPlan, config: ExecutionConfig
) -> None:
    """An UNKNOWN status is treated like PENDING (bounded re-check, fail-closed)."""
    env = _pending_open_env()
    env.data["status"] = "UNKNOWN"
    broker = FakeBroker(open_env=env)

    with pytest.raises(ExecutionAbort):
        place_order(broker, exec_state, order_plan, config, sleep_fn=_no_sleep)
    assert len(broker.open_position_calls) == 1
    assert exec_state.get(order_plan.deal_reference)["status"] == PENDING


# --- place_order: transport error + REJECTED ------------------------------


def test_place_order_transport_error_aborts_stays_pending(
    exec_state: ExecutionState, order_plan: OrderPlan, config: ExecutionConfig
) -> None:
    """``not env.ok`` is ambiguous → fail closed, leave PENDING, no second order."""
    ref = order_plan.deal_reference
    broker = FakeBroker(
        open_env=_FakeEnv(ok=False, data={"deal_reference": ref})
    )
    broker.open_env.error = {"code": "TIMEOUT", "message": "x", "retryable": True}

    with pytest.raises(ExecutionAbort):
        place_order(broker, exec_state, order_plan, config, sleep_fn=_no_sleep)

    assert len(broker.open_position_calls) == 1
    record = exec_state.get(ref)
    assert record["status"] == PENDING  # never mark a possibly-live order closed
    assert ref in exec_state.open_references()


def test_place_order_rejected_marks_closed_and_aborts(
    exec_state: ExecutionState, order_plan: OrderPlan, config: ExecutionConfig
) -> None:
    """A confirmed REJECTED → broker says no position → mark_closed + surface."""
    ref = order_plan.deal_reference
    env = _pending_open_env()
    env.data["status"] = "REJECTED"
    env.data["reason"] = "INSUFFICIENT_FUNDS"
    broker = FakeBroker(open_env=env)

    with pytest.raises(ExecutionAbort):
        place_order(broker, exec_state, order_plan, config, sleep_fn=_no_sleep)

    assert len(broker.open_position_calls) == 1
    assert exec_state.get(ref)["status"] == CLOSED
    assert ref not in exec_state.open_references()


# --- reconcile_startup ----------------------------------------------------


def test_reconcile_startup_empty_refs_skips_broker(
    exec_state: ExecutionState, config: ExecutionConfig
) -> None:
    broker = FakeBroker()
    reconcile_startup(broker, exec_state, config)  # no open refs → no broker request
    assert broker.reconcile_calls == []


def test_reconcile_startup_missing_marks_closed(
    exec_state: ExecutionState, order_plan: OrderPlan, config: ExecutionConfig
) -> None:
    """We think a ref is open; broker has no record → orphan resolved (mark_closed)."""
    ref = order_plan.deal_reference
    exec_state.record_pending(order_plan)  # now open_references() == [ref]
    broker = FakeBroker(
        reconcile_env=_FakeEnv(
            ok=True, data={"present": [], "missing": [ref], "unexpected": []}
        )
    )

    reconcile_startup(broker, exec_state, config)

    assert broker.reconcile_calls == [[ref]]
    assert exec_state.get(ref)["status"] == CLOSED


def test_reconcile_startup_unexpected_aborts_when_configured(
    exec_state: ExecutionState, order_plan: OrderPlan
) -> None:
    """An unexpected broker position → ReconcileConflict (don't stack another order)."""
    exec_state.record_pending(order_plan)
    broker = FakeBroker(
        reconcile_env=_FakeEnv(
            ok=True,
            data={"present": [], "missing": [], "unexpected": ["bot-someoneelse"]},
        )
    )
    config = ExecutionConfig(reconcile_unexpected_aborts=True)

    with pytest.raises(ReconcileConflict):
        reconcile_startup(broker, exec_state, config)


def test_reconcile_startup_unexpected_warns_when_disabled(
    exec_state: ExecutionState, order_plan: OrderPlan
) -> None:
    """With abort-on-unexpected off, an unexpected position logs but does not raise."""
    exec_state.record_pending(order_plan)
    broker = FakeBroker(
        reconcile_env=_FakeEnv(
            ok=True,
            data={"present": [], "missing": [], "unexpected": ["bot-someoneelse"]},
        )
    )
    config = ExecutionConfig(reconcile_unexpected_aborts=False)

    reconcile_startup(broker, exec_state, config)  # no raise
    # Our own record is untouched (still open).
    assert order_plan.deal_reference in exec_state.open_references()


def test_reconcile_startup_not_ok_aborts(
    exec_state: ExecutionState, order_plan: OrderPlan, config: ExecutionConfig
) -> None:
    """A not-ok reconcile envelope → ExecutionAbort (broker truth unverifiable)."""
    exec_state.record_pending(order_plan)
    broker = FakeBroker(reconcile_env=_FakeEnv(ok=False, data=None))

    with pytest.raises(ExecutionAbort):
        reconcile_startup(broker, exec_state, config)
