"""Step 2 — ``ExecutionState`` write-ahead idempotency store.

All mocked, no network, no real order. Uses ``tmp_path`` (pytest built-in) for
the JSON file and the ``make_order_plan`` / ``order_plan`` fixtures from conftest.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest

from execution.exceptions import ExecutionError
from execution.execution_state import CLOSED, OPEN, PENDING, ExecutionState
from execution.models import OrderPlan


@pytest.fixture
def state_path(tmp_path: Path) -> Path:
    """A nested path so __init__'s parent-dir creation is exercised too."""
    return tmp_path / "state" / "execution_state.json"


def test_record_pending_persists_before_order(
    state_path: Path, order_plan: OrderPlan
) -> None:
    state = ExecutionState(str(state_path))
    state.record_pending(order_plan)

    # The file exists *before* any order would be placed (write-ahead).
    assert state_path.exists()
    record = state.get(order_plan.deal_reference)
    assert record is not None
    assert record["status"] == PENDING
    assert record["deal_id"] is None
    assert record["epic"] == order_plan.epic
    assert record["direction"] == order_plan.direction
    assert record["size"] == order_plan.size
    assert record["stop_level"] == order_plan.stop_level
    assert record["limit_level"] == order_plan.limit_level


def test_mark_open_sets_status_and_deal_id(
    state_path: Path, order_plan: OrderPlan
) -> None:
    state = ExecutionState(str(state_path))
    state.record_pending(order_plan)
    state.mark_open(order_plan.deal_reference, "DIAAA123")

    record = state.get(order_plan.deal_reference)
    assert record is not None
    assert record["status"] == OPEN
    assert record["deal_id"] == "DIAAA123"


def test_mark_closed_drops_from_open_references(
    state_path: Path, order_plan: OrderPlan
) -> None:
    state = ExecutionState(str(state_path))
    state.record_pending(order_plan)
    state.mark_open(order_plan.deal_reference, "DIAAA123")
    assert order_plan.deal_reference in state.open_references()

    state.mark_closed(order_plan.deal_reference)
    record = state.get(order_plan.deal_reference)
    assert record is not None and record["status"] == CLOSED
    assert order_plan.deal_reference not in state.open_references()


def test_open_references_lists_pending_and_open_not_closed(
    state_path: Path, make_order_plan: Callable[..., OrderPlan]
) -> None:
    state = ExecutionState(str(state_path))
    pending = make_order_plan()
    opened = make_order_plan()
    closed = make_order_plan()

    state.record_pending(pending)            # stays PENDING
    state.record_pending(opened)
    state.mark_open(opened.deal_reference, "DI-OPEN")
    state.record_pending(closed)
    state.mark_open(closed.deal_reference, "DI-CLOSED")
    state.mark_closed(closed.deal_reference)

    refs = set(state.open_references())
    assert refs == {pending.deal_reference, opened.deal_reference}


def test_corrupt_file_raises(state_path: Path, order_plan: OrderPlan) -> None:
    state = ExecutionState(str(state_path))
    state.record_pending(order_plan)
    state_path.write_text("{ this is not json", encoding="utf-8")

    # Every read path surfaces the corruption rather than silently resetting.
    with pytest.raises(ExecutionError):
        state.get(order_plan.deal_reference)
    with pytest.raises(ExecutionError):
        state.open_references()
    with pytest.raises(ExecutionError):
        state.record_pending(order_plan)


def test_atomic_write_leaves_no_temp_and_survives_restart(
    state_path: Path, order_plan: OrderPlan
) -> None:
    ExecutionState(str(state_path)).record_pending(order_plan)

    # No leftover .tmp from the atomic write.
    tmp = state_path.with_suffix(state_path.suffix + ".tmp")
    assert not tmp.exists()
    assert list(state_path.parent.glob("*.tmp")) == []

    # A fresh instance on the same path reads the prior record back
    # (durability across a process restart).
    reloaded = ExecutionState(str(state_path))
    record = reloaded.get(order_plan.deal_reference)
    assert record is not None and record["status"] == PENDING


def test_mark_open_unknown_ref_raises(state_path: Path) -> None:
    state = ExecutionState(str(state_path))
    with pytest.raises(ExecutionError):
        state.mark_open("bot-does-not-exist", "DIAAA")


def test_mark_closed_unknown_ref_raises(state_path: Path) -> None:
    state = ExecutionState(str(state_path))
    with pytest.raises(ExecutionError):
        state.mark_closed("bot-does-not-exist")


def test_get_unknown_returns_none_known_returns_copy(
    state_path: Path, order_plan: OrderPlan
) -> None:
    state = ExecutionState(str(state_path))
    assert state.get("bot-missing") is None

    state.record_pending(order_plan)
    record = state.get(order_plan.deal_reference)
    assert record is not None
    # Mutating the returned dict must not corrupt the stored state (it's a copy).
    record["status"] = "TAMPERED"
    assert state.get(order_plan.deal_reference)["status"] == PENDING


def test_missing_file_reads_empty(state_path: Path) -> None:
    state = ExecutionState(str(state_path))
    assert state.open_references() == []
    assert state.get("bot-anything") is None
    assert not state_path.exists()  # reads don't create the file
