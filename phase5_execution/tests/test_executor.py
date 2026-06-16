"""Step 8 — ``executor.py``: the orchestrator composing the whole cycle.

All mocked, no network, **no real order**. The clock (``now_fn``) / sleep (``sleep_fn``)
are injected so the loop runs deterministically. These tests assert the *composition* —
each gate/VETO/sizing rule is unit-tested in its own module; here we prove the executor
wires them in the right order, short-circuits correctly, and never places an order when a
gate/VETO/confirm says no.

Covers the two Phase-5 proof-tests that live at this layer (concept "Done-Kriterien"):
(b) an adverse-momentum snapshot vetoes before the order; (c) a declined human-confirm
places no order. Proof-test (a) — a forced PENDING → exactly one ``open_position`` +
abort — lives in ``test_order.py``.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import pytest

from execution.config import ExecutionConfig
from execution.execution_state import CLOSED, ExecutionState
from execution.executor import Executor
from execution.models import OrderPlan
from tests.conftest import DEFAULT_EPIC, FakeBroker, FakeDB, FakeState, _FakeEnv

DEAL_ID = "DIAAAA-FAKE"  # the FakeBroker default open_env deal_id


# --- helpers --------------------------------------------------------------


def _at(hour: int, minute: int = 0) -> datetime:
    """A naive 2026-06-11 time-of-day (interpreted in config.tz, like the gates)."""
    return datetime(2026, 6, 11, hour, minute)


def _in_window() -> Callable[[], datetime]:
    """A fixed ``now_fn`` well inside the default 09:00-17:30 window (far from 17:15)."""
    return lambda: _at(10, 0)


def _account(available: float) -> _FakeEnv:
    return _FakeEnv(
        ok=True,
        data={
            "balance": available,
            "available": available,
            "profit_loss": 0.0,
            "currency": "EUR",
        },
    )


def _positions(*positions: dict[str, Any]) -> _FakeEnv:
    return _FakeEnv(ok=True, data={"positions": list(positions)})


def _open_position(direction: str = "BUY") -> dict[str, Any]:
    return {
        "deal_id": DEAL_ID,
        "deal_reference": "bot-x",
        "epic": DEFAULT_EPIC,
        "direction": direction,
        "size": 0.5,
    }


class _Runner:
    """Recording ``research_runner`` — counts invocations (Gate 2's lazy Phase-4 hook)."""

    def __init__(self, result: list[dict[str, Any]] | None = None) -> None:
        self.calls = 0
        self.result = result or []

    def __call__(self) -> list[dict[str, Any]]:
        self.calls += 1
        return self.result


def _yes(_plan: OrderPlan) -> bool:
    return True


def _no(_plan: OrderPlan) -> bool:
    return False


@pytest.fixture
def exec_state(tmp_path: Path) -> ExecutionState:
    return ExecutionState(str(tmp_path / "state" / "execution_state.json"))


def _build(
    broker: FakeBroker,
    state: FakeState,
    exec_state: ExecutionState,
    *,
    confirm_fn: Callable[[OrderPlan], bool] = _yes,
    runner: _Runner | None = None,
    debate_runner: Callable[[dict[str, Any]], Any] | None = None,
    now_fn: Callable[[], datetime] | None = None,
    config: ExecutionConfig | None = None,
    db: FakeDB | None = None,
) -> tuple[Executor, _Runner]:
    runner = runner or _Runner()
    executor = Executor(
        broker,
        db or FakeDB(),
        state,
        exec_state,
        config or ExecutionConfig(),
        runner,
        confirm_fn,
        debate_runner=debate_runner,
        now_fn=now_fn or _in_window(),
        sleep_fn=lambda _s: None,
    )
    return executor, runner


# --- 1) full path: open → monitored → broker SL/TP closes it --------------


def test_full_path_open_then_closed_by_broker(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """Every gate/VETO passes, order ACCEPTED, position present then gone → CLOSED_BY_BROKER."""
    broker = FakeBroker(
        account_env=_account(1500.0),  # 2% / 30pt → 1.0 lot ≥ min 0.5 (risk-per-trade model)
        positions_sequence=[
            _positions(),                  # Gate 3 + Gate 5 (one fetch)
            _positions(),                  # VETO 4 (pre_trade_check)
            _positions(_open_position()),  # monitor poll 1: present
            _positions(),                  # monitor poll 2: gone
        ],
    )
    state = FakeState(fresh=True, candidates=[make_candidate(direction="BUY")])
    executor, runner = _build(broker, state, exec_state)

    result = executor.run()

    assert result.status == "CLOSED_BY_BROKER"
    assert result.deal_id == DEAL_ID
    assert len(broker.open_position_calls) == 1          # exactly one order
    assert runner.calls == 0                             # fresh candidate, no research
    ref = broker.open_position_calls[0]["deal_reference"]
    assert ref.startswith("bot-")
    assert exec_state.get(ref)["status"] == CLOSED       # write-ahead record closed
    assert exec_state.open_references() == []


# --- 2) Gate 1 (window) fail: no research, no order -----------------------


def test_gate1_outside_window_no_research_no_order(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """now outside the trade window → NO_TRADE before Gate 2 (research never invoked)."""
    broker = FakeBroker()
    state = FakeState(fresh=True, candidates=[make_candidate()])
    executor, runner = _build(broker, state, exec_state, now_fn=lambda: _at(20, 0))

    result = executor.run()

    assert result.status == "NO_TRADE"
    assert "time_window" in result.detail
    assert runner.calls == 0
    assert broker.open_position_calls == []
    assert broker.get_open_positions_calls == 0  # Gate 3 never reached


# --- 3) Gate 2 abstain: fresh but empty → no order ------------------------


def test_gate2_abstain_no_order(exec_state: ExecutionState) -> None:
    """Fresh-but-empty candidate store → abstain (NO_TRADE), no order."""
    broker = FakeBroker(account_env=_account(1500.0))
    state = FakeState(fresh=True, candidates=[])  # abstain
    executor, runner = _build(broker, state, exec_state)

    result = executor.run()

    assert result.status == "NO_TRADE"
    assert "load_candidates" in result.detail
    assert runner.calls == 0  # fresh → research not invoked
    assert broker.open_position_calls == []


# --- 4) VETO fail (adverse momentum) → no order [proof-test b] ------------


def test_veto_adverse_momentum_blocks_order(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """Sizing passes, but a sharp drop vetoes a BUY → NO_TRADE, no order placed."""
    from tests.conftest import make_bars

    broker = FakeBroker(
        account_env=_account(1500.0),
        ohlcv_env=_FakeEnv(ok=True, data={"bars": make_bars([18000.0, 17900.0])}),  # -0.56%
    )
    state = FakeState(fresh=True, candidates=[make_candidate(direction="BUY")])
    executor, _ = _build(broker, state, exec_state)

    result = executor.run()

    assert result.status == "NO_TRADE"
    assert "momentum" in result.detail
    assert broker.open_position_calls == []


# --- 5) Gate 4 size below min → no order ----------------------------------


def test_size_below_min_no_order(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """A tiny balance rounds the size below min_deal_size → NO_TRADE, no order."""
    # 2% of 400 / 30 = 0.266 → 0.2 < min_deal_size 0.5 (risk-per-trade model).
    broker = FakeBroker(account_env=_account(400.0))
    state = FakeState(fresh=True, candidates=[make_candidate()])
    executor, _ = _build(broker, state, exec_state)

    result = executor.run()

    assert result.status == "NO_TRADE"
    assert "below_min_deal_size" in result.detail
    assert broker.open_position_calls == []


# --- 6) require_confirm + declined → ABORTED_BY_USER [proof-test c] -------


def test_confirm_declined_places_no_order(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """A declined human-confirm places no order and writes no write-ahead record."""
    broker = FakeBroker(account_env=_account(1500.0))
    state = FakeState(fresh=True, candidates=[make_candidate()])
    executor, _ = _build(broker, state, exec_state, confirm_fn=_no)

    result = executor.run()

    assert result.status == "ABORTED_BY_USER"
    assert result.plan is not None              # the plan was built, just not placed
    assert broker.open_position_calls == []
    assert exec_state.open_references() == []   # no record_pending (place_order never ran)


# --- 7) session-health fail → ABORT ---------------------------------------


def test_session_health_fail_aborts(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """A not-ok account snapshot fails closed (ABORT) before any gate or order."""
    broker = FakeBroker(account_env=_FakeEnv(ok=False, data=None))
    state = FakeState(fresh=True, candidates=[make_candidate()])
    executor, runner = _build(broker, state, exec_state)

    result = executor.run()

    assert result.status == "ABORT"
    assert runner.calls == 0
    assert broker.open_position_calls == []
    assert broker.get_open_positions_calls == 0  # never got past session health


# --- 8) startup reconcile conflict → ABORT --------------------------------


def test_reconcile_conflict_aborts(
    exec_state: ExecutionState,
    make_candidate: Callable[..., dict[str, Any]],
    make_order_plan: Callable[..., OrderPlan],
) -> None:
    """An unexpected broker position at startup reconcile aborts (no stacked order)."""
    # Seed an open reference so reconcile_startup actually queries the broker.
    seeded = make_order_plan()
    exec_state.record_pending(seeded)

    broker = FakeBroker(
        account_env=_account(1500.0),
        reconcile_env=_FakeEnv(
            ok=True,
            data={
                "broker_position_count": 1,
                "broker_deal_ids": ["DIAAAA-OTHER"],
                "present": [],
                "missing": [],
                "unexpected": ["bot-orphan"],  # broker has it, we have no record
            },
        ),
    )
    state = FakeState(fresh=True, candidates=[make_candidate()])
    executor, _ = _build(broker, state, exec_state)

    result = executor.run()

    assert result.status == "ABORT"
    assert broker.open_position_calls == []


# --- 9–12) Phase-6 debate seam (Decision A) -------------------------------
#
# The seam sits between Gate 2 and Gate 3. The outcome is read duck-typed, so the
# tests use a tiny local stand-in (no Phase-6 import — the P5 suite stays isolated).


class _DebateOutcome:
    """Duck-typed stand-in for the Phase-6 ``DebateOutcome`` (the seam reads attrs)."""

    def __init__(self, decision: str, direction: str | None, rationale: str = "") -> None:
        self.decision = decision
        self.direction = direction
        self.rationale = rationale


class _DebateRunner:
    """Recording ``debate_runner`` — captures the candidate it saw, returns a fixed outcome."""

    def __init__(self, outcome: _DebateOutcome) -> None:
        self.outcome = outcome
        self.seen: list[dict[str, Any]] = []

    def __call__(self, candidate: dict[str, Any]) -> _DebateOutcome:
        self.seen.append(candidate)
        return self.outcome


def _full_path_broker() -> FakeBroker:
    """A broker wired for the full open→present→gone path (default rising bars)."""
    return FakeBroker(
        account_env=_account(1500.0),
        positions_sequence=[
            _positions(),                  # Gate 3 + Gate 5
            _positions(),                  # VETO 4
            _positions(_open_position()),  # monitor poll 1: present
            _positions(),                  # monitor poll 2: gone
        ],
    )


def test_debate_flip_reverses_order_direction(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """A BUY seed + TRADE/SELL debate verdict → the placed order is SELL (Decision B flip)."""
    broker = _full_path_broker()
    state = FakeState(fresh=True, candidates=[make_candidate(direction="BUY")])
    debate = _DebateRunner(_DebateOutcome("TRADE", "SELL"))
    executor, _ = _build(broker, state, exec_state, debate_runner=debate)

    result = executor.run()

    assert result.status == "CLOSED_BY_BROKER"
    assert debate.seen and debate.seen[0]["direction"] == "BUY"  # saw the seed
    assert len(broker.open_position_calls) == 1
    assert broker.open_position_calls[0]["direction"] == "SELL"  # flipped reached the order


def test_debate_abstain_blocks_order(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """A debate ABSTAIN → NO_TRADE before Gate 3, no order placed (fail-closed, Decision J)."""
    broker = FakeBroker(account_env=_account(1500.0))
    state = FakeState(fresh=True, candidates=[make_candidate(direction="BUY")])
    debate = _DebateRunner(_DebateOutcome("ABSTAIN", None, rationale="bears won"))
    executor, _ = _build(broker, state, exec_state, debate_runner=debate)

    result = executor.run()

    assert result.status == "NO_TRADE"
    assert "debate" in result.detail and "bears won" in result.detail
    assert broker.open_position_calls == []
    assert broker.get_open_positions_calls == 0  # Gate 3 never reached


def test_debate_trade_same_direction_opens_normally(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """A TRADE verdict keeping the seed direction proceeds exactly like the baseline."""
    broker = _full_path_broker()
    state = FakeState(fresh=True, candidates=[make_candidate(direction="BUY")])
    debate = _DebateRunner(_DebateOutcome("TRADE", "BUY"))
    executor, _ = _build(broker, state, exec_state, debate_runner=debate)

    result = executor.run()

    assert result.status == "CLOSED_BY_BROKER"
    assert len(broker.open_position_calls) == 1
    assert broker.open_position_calls[0]["direction"] == "BUY"


def test_no_debate_runner_is_bit_identical_passthrough(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """``debate_runner=None`` (the default) → the seam is skipped; baseline behaviour."""
    broker = _full_path_broker()
    state = FakeState(fresh=True, candidates=[make_candidate(direction="BUY")])
    executor, _ = _build(broker, state, exec_state)  # no debate_runner

    result = executor.run()

    assert result.status == "CLOSED_BY_BROKER"
    assert broker.open_position_calls[0]["direction"] == "BUY"


def test_debate_runner_raising_fails_closed_no_order(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """A throwing debate_runner never crashes the cycle → NO_TRADE, no order (Decision J defense)."""
    broker = FakeBroker(account_env=_account(1500.0))
    state = FakeState(fresh=True, candidates=[make_candidate(direction="BUY")])

    def boom(_candidate: dict[str, Any]) -> Any:
        raise RuntimeError("debate infra exploded")

    executor, _ = _build(broker, state, exec_state, debate_runner=boom)

    result = executor.run()

    assert result.status == "NO_TRADE"
    assert "debate" in result.detail
    assert broker.open_position_calls == []
    assert broker.get_open_positions_calls == 0  # Gate 3 never reached
