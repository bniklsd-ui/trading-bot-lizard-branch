"""Step 1 — model dataclasses + exception hierarchy.

Pure construction / immutability / subclassing checks. No I/O.
"""

from __future__ import annotations

import dataclasses

import pytest

from execution.exceptions import (
    ExecutionAbort,
    ExecutionError,
    GateRejected,
    ReconcileConflict,
    VetoRejected,
)
from execution.models import ExecutionResult, GateVerdict, OrderPlan, VetoVerdict


# --- models ---------------------------------------------------------------


def test_order_plan_constructs_and_reads_back() -> None:
    plan = OrderPlan(
        epic="IX.D.DAX.IFMM.IP",
        direction="BUY",
        size=0.5,
        stop_level=17970.0,
        limit_level=18045.0,
        deal_reference="bot-deadbeef",
        currency="EUR",
    )
    assert plan.direction == "BUY"
    assert plan.size == 0.5
    assert plan.stop_level == 17970.0
    assert plan.limit_level == 18045.0
    assert plan.deal_reference.startswith("bot-")
    assert plan.currency == "EUR"


def test_order_plan_is_frozen() -> None:
    plan = OrderPlan("E", "SELL", 0.5, 1.0, 2.0, "bot-x", "EUR")
    with pytest.raises(dataclasses.FrozenInstanceError):
        plan.size = 1.0  # type: ignore[misc]


def test_gate_and_veto_verdicts() -> None:
    g = GateVerdict(ok=True, gate="time_window", reason="")
    v = VetoVerdict(ok=False, veto="momentum", reason="BUY into a sharp drop")
    assert g.ok is True and g.gate == "time_window"
    assert v.ok is False and v.veto == "momentum" and "drop" in v.reason


@pytest.mark.parametrize("verdict", [
    GateVerdict(ok=True, gate="g", reason=""),
    VetoVerdict(ok=True, veto="v", reason=""),
])
def test_verdicts_are_frozen(verdict: object) -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        verdict.ok = False  # type: ignore[attr-defined, misc]


def test_execution_result_open_shape() -> None:
    plan = OrderPlan("E", "BUY", 0.5, 1.0, 2.0, "bot-y", "EUR")
    res = ExecutionResult(status="OPEN", deal_id="DIAAA", plan=plan, detail="opened")
    assert res.status == "OPEN"
    assert res.deal_id == "DIAAA"
    assert res.plan is plan


def test_execution_result_no_trade_shape() -> None:
    # The no-trade / abstain outcome: no deal, no plan, still a valid result.
    res = ExecutionResult(status="NO_TRADE", deal_id=None, plan=None,
                          detail="gate_2 abstain")
    assert res.deal_id is None
    assert res.plan is None
    assert res.status == "NO_TRADE"


def test_execution_result_is_frozen() -> None:
    res = ExecutionResult(status="NO_TRADE", deal_id=None, plan=None, detail="")
    with pytest.raises(dataclasses.FrozenInstanceError):
        res.status = "OPEN"  # type: ignore[misc]


# --- exceptions -----------------------------------------------------------


@pytest.mark.parametrize("exc_cls", [
    GateRejected, VetoRejected, ExecutionAbort, ReconcileConflict,
])
def test_exceptions_subclass_base(exc_cls: type[ExecutionError]) -> None:
    assert issubclass(exc_cls, ExecutionError)
    # raisable + catchable as the base family
    with pytest.raises(ExecutionError):
        raise exc_cls("boom")


def test_exception_codes_are_distinct() -> None:
    codes = {
        ExecutionError.code, GateRejected.code, VetoRejected.code,
        ExecutionAbort.code, ReconcileConflict.code,
    }
    assert len(codes) == 5
