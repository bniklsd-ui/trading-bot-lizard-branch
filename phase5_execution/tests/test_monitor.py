"""Step 7 — ``monitor.py``: polling loop, time-stop, broker-side close detection.

All mocked, no network, **no real order**. The clock (``now_fn``) and sleep (``sleep_fn``)
are injected so the loop runs deterministically with no real waiting; the loop terminates
because the controlled clock reaches the square-off cutoff / max-hold.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable

import pytest

from execution.config import ExecutionConfig
from execution.exceptions import ExecutionAbort
from execution.execution_state import CLOSED, ExecutionState
from execution.models import OrderPlan
from execution.monitor import monitor_position
from tests.conftest import DEFAULT_EPIC, FakeBroker, _FakeEnv

DEAL_ID = "DIAAAA-LIVE"


# --- helpers --------------------------------------------------------------


class _Clock:
    """Deterministic ``now_fn`` — yields successive datetimes; the last repeats."""

    def __init__(self, *times: datetime) -> None:
        self._times = list(times)

    def __call__(self) -> datetime:
        if len(self._times) > 1:
            return self._times.pop(0)
        return self._times[0]


def _at(hour: int, minute: int = 0) -> datetime:
    """A naive 2026-06-11 time-of-day (interpreted in config.tz, like the gates)."""
    return datetime(2026, 6, 11, hour, minute)


def _present_env() -> _FakeEnv:
    return _FakeEnv(
        ok=True,
        data={
            "positions": [
                {
                    "deal_id": DEAL_ID,
                    "deal_reference": "bot-x",
                    "epic": DEFAULT_EPIC,
                    "direction": "BUY",
                    "size": 0.5,
                }
            ]
        },
    )


def _gone_env() -> _FakeEnv:
    return _FakeEnv(ok=True, data={"positions": []})


@pytest.fixture
def exec_state(tmp_path: Path) -> ExecutionState:
    return ExecutionState(str(tmp_path / "state" / "execution_state.json"))


@pytest.fixture
def open_plan(
    make_order_plan: Callable[..., OrderPlan], exec_state: ExecutionState
) -> OrderPlan:
    """A plan that is already recorded OPEN in the store (post-place_order state)."""
    plan = make_order_plan()
    exec_state.record_pending(plan)
    exec_state.mark_open(plan.deal_reference, DEAL_ID)
    return plan


# --- broker-side close (SL/TP filled) -------------------------------------


def test_position_gone_is_closed_by_broker(
    exec_state: ExecutionState, open_plan: OrderPlan
) -> None:
    """Present on poll 1, gone on poll 2 → CLOSED_BY_BROKER, no close_position."""
    broker = FakeBroker(positions_sequence=[_present_env(), _gone_env()])
    sleep_calls: list[float] = []
    config = ExecutionConfig()

    result = monitor_position(
        broker, exec_state, open_plan, DEAL_ID, config,
        now_fn=_Clock(_at(10, 0)),  # always inside window, far from square-off
        sleep_fn=sleep_calls.append,
    )

    assert result.status == "CLOSED_BY_BROKER"
    assert result.deal_id == DEAL_ID
    assert broker.close_position_calls == []  # the broker closed it, not us
    assert exec_state.get(open_plan.deal_reference)["status"] == CLOSED
    assert sleep_calls == [config.poll_interval_s]  # one poll gap, no real sleep


# --- time-stop: square-off ------------------------------------------------


def test_square_off_triggers_time_stop_close(
    exec_state: ExecutionState, open_plan: OrderPlan
) -> None:
    """now past square_off_time, position still open → close_position → TIME_STOP."""
    broker = FakeBroker(positions_env=_present_env())
    config = ExecutionConfig()  # square_off 17:15

    result = monitor_position(
        broker, exec_state, open_plan, DEAL_ID, config,
        now_fn=_Clock(_at(10, 0), _at(17, 20)),  # entry early, first poll past cutoff
        sleep_fn=lambda _s: None,
    )

    assert result.status == "TIME_STOP"
    assert "square_off" in result.detail
    assert broker.close_position_calls == [DEAL_ID]
    assert exec_state.get(open_plan.deal_reference)["status"] == CLOSED


# --- time-stop: max hold --------------------------------------------------


def test_max_hold_triggers_time_stop_close(
    exec_state: ExecutionState, open_plan: OrderPlan
) -> None:
    """Held >= max_hold_minutes while still inside window → TIME_STOP (max_hold)."""
    broker = FakeBroker(positions_env=_present_env())
    config = ExecutionConfig()  # max_hold 240 min = 4 h

    result = monitor_position(
        broker, exec_state, open_plan, DEAL_ID, config,
        now_fn=_Clock(_at(10, 0), _at(14, 0)),  # 4 h later, still before 17:15
        sleep_fn=lambda _s: None,
    )

    assert result.status == "TIME_STOP"
    assert "max_hold" in result.detail
    assert broker.close_position_calls == [DEAL_ID]


# --- time-stop close failure ----------------------------------------------


def test_close_failure_at_time_stop_aborts(
    exec_state: ExecutionState, open_plan: OrderPlan
) -> None:
    """close_position not-ok at the time-stop → ExecutionAbort (operator)."""
    broker = FakeBroker(
        positions_env=_present_env(),
        close_env=_FakeEnv(ok=False, data=None),
    )
    broker.close_env.error = {"code": "SERVER_ERROR", "message": "x", "retryable": True}

    with pytest.raises(ExecutionAbort):
        monitor_position(
            broker, exec_state, open_plan, DEAL_ID, ExecutionConfig(),
            now_fn=_Clock(_at(10, 0), _at(17, 20)),
            sleep_fn=lambda _s: None,
        )

    assert broker.close_position_calls == [DEAL_ID]  # attempted exactly once


# --- polling cadence / termination ----------------------------------------


def test_polls_with_sleep_until_position_gone(
    exec_state: ExecutionState, open_plan: OrderPlan
) -> None:
    """Several polls with a sleep between each; terminates when the position is gone."""
    broker = FakeBroker(
        positions_sequence=[_present_env(), _present_env(), _gone_env()]
    )
    sleep_calls: list[float] = []
    config = ExecutionConfig()

    result = monitor_position(
        broker, exec_state, open_plan, DEAL_ID, config,
        now_fn=_Clock(_at(10, 0)),
        sleep_fn=sleep_calls.append,
    )

    assert result.status == "CLOSED_BY_BROKER"
    assert broker.get_open_positions_calls == 3
    assert sleep_calls == [config.poll_interval_s, config.poll_interval_s]


# --- uncertain read does not infer a close --------------------------------


def test_not_ok_read_does_not_infer_close(
    exec_state: ExecutionState, open_plan: OrderPlan
) -> None:
    """A failed open-positions read must NOT be treated as a close; time-stop ends it."""
    broker = FakeBroker(positions_sequence=[_FakeEnv(ok=False, data=None)])

    result = monitor_position(
        broker, exec_state, open_plan, DEAL_ID, ExecutionConfig(),
        # before cutoff, then past it: first poll can't read, second hits square-off
        now_fn=_Clock(_at(17, 0), _at(17, 0), _at(17, 20)),
        sleep_fn=lambda _s: None,
    )

    # Not CLOSED_BY_BROKER (we never inferred a close from the failed read).
    assert result.status == "TIME_STOP"
    assert broker.close_position_calls == [DEAL_ID]
