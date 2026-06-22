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
    reward_sink: Any | None = None,
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
        reward_sink=reward_sink,
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

    def __init__(
        self,
        decision: str,
        direction: str | None,
        rationale: str = "",
        confidence: float | None = None,
    ) -> None:
        self.decision = decision
        self.direction = direction
        self.rationale = rationale
        self.confidence = confidence


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


# --- 13–19) Phase-7 reward-sink seam (Decision A) -------------------------
#
# The seam wraps the place→monitor block: on_trade_opened fires after the position is
# confirmed OPEN (before monitoring) and on_trade_closed after a real close. Like the
# debate seam, the sink is read duck-typed, so the tests use a tiny recording stand-in —
# but here the executor *builds* the payload, so these assert the built OpenedTrade /
# ClosedTrade snapshots (the real ``reward.models`` contracts, via the lazy import).
#
# Placement reconciliation (code = source of truth): concept §4 listed these in
# ``phase7_reward/tests/test_executor_seam.py``, but the Executor + its fakes live here and
# the structurally identical debate-seam tests are right above — cross-test-package fake
# reuse is infeasible, so the seam is tested where it lives (mirroring the debate precedent).


class _RecordingSink:
    """Duck-typed ``RewardSink`` stand-in — records the payloads it is handed.

    ``raise_on_open`` / ``raise_on_close`` make the respective callback throw, to prove
    the executor guards it (a raising sink never crashes the cycle — Decision J).
    """

    def __init__(self, *, raise_on_open: bool = False, raise_on_close: bool = False) -> None:
        self.opened: list[Any] = []
        self.closed: list[Any] = []
        self._raise_on_open = raise_on_open
        self._raise_on_close = raise_on_close

    def on_trade_opened(self, opened: Any) -> None:
        self.opened.append(opened)
        if self._raise_on_open:
            raise RuntimeError("sink on_trade_opened boom")

    def on_trade_closed(self, closed: Any) -> None:
        self.closed.append(closed)
        if self._raise_on_close:
            raise RuntimeError("sink on_trade_closed boom")


def test_reward_sink_none_is_bit_identical_passthrough(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """``reward_sink=None`` (the default) → the seam is skipped; baseline behaviour."""
    broker = _full_path_broker()
    state = FakeState(fresh=True, candidates=[make_candidate(direction="BUY")])
    executor, _ = _build(broker, state, exec_state)  # no reward_sink

    result = executor.run()

    assert result.status == "CLOSED_BY_BROKER"
    assert len(broker.open_position_calls) == 1


def test_reward_sink_fires_both_callbacks_with_built_snapshots(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """Full BUY path → on_trade_opened once + on_trade_closed once, with correct payloads."""
    broker = _full_path_broker()
    state = FakeState(fresh=True, candidates=[make_candidate(direction="BUY")])
    sink = _RecordingSink()
    executor, _ = _build(broker, state, exec_state, reward_sink=sink)

    result = executor.run()

    assert result.status == "CLOSED_BY_BROKER"
    assert len(sink.opened) == 1 and len(sink.closed) == 1

    opened = sink.opened[0]
    assert opened.deal_id == DEAL_ID
    assert opened.direction == "BUY"
    assert opened.intended_open_level == 18000.0            # BUY → ask (price_env default)
    assert opened.stop_level == 17970.0                     # ask - 30 (build_order_plan)
    assert opened.size == 1.0                               # 2% of 1500 / 30pt
    assert opened.initial_risk == 30.0                      # |18000-17970| * 1.0 * 1.0
    assert opened.spread_at_entry_pct == 0.03
    assert opened.research_confidence == 70.0               # candidate llm_confidence
    assert opened.debate_confidence is None                 # no debate ran
    assert opened.score_at_open == 50.0                     # FakeDB default
    assert opened.account == "demo"
    assert opened.deal_reference.startswith("bot-")

    closed = sink.closed[0]
    assert closed.status == "CLOSED_BY_BROKER"
    assert closed.deal_id == DEAL_ID
    assert closed.deal_reference == opened.deal_reference   # links back to the open


def test_reward_sink_open_payload_reflects_debate_flip(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """A BUY seed flipped to SELL by the debate → opened payload is SELL, entry = bid."""
    broker = _full_path_broker()
    state = FakeState(fresh=True, candidates=[make_candidate(direction="BUY")])
    debate = _DebateRunner(_DebateOutcome("TRADE", "SELL", confidence=0.82))
    sink = _RecordingSink()
    executor, _ = _build(broker, state, exec_state, debate_runner=debate, reward_sink=sink)

    result = executor.run()

    assert result.status == "CLOSED_BY_BROKER"
    opened = sink.opened[0]
    assert opened.direction == "SELL"
    assert opened.intended_open_level == 17999.0            # SELL → bid (price_env default)
    assert opened.debate_confidence == 0.82                 # captured from the in-memory outcome


def test_reward_sink_close_payload_on_time_stop(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """A time-stop close also fires on_trade_closed, carrying status TIME_STOP."""
    broker = FakeBroker(
        account_env=_account(1500.0),
        positions_sequence=[
            _positions(),                  # Gate 3 + Gate 5
            _positions(),                  # VETO 4
            _positions(_open_position()),  # monitor poll 1: still present → time-stop fires
        ],
    )
    state = FakeState(fresh=True, candidates=[make_candidate(direction="BUY")])
    sink = _RecordingSink()
    executor, _ = _build(
        broker, state, exec_state, reward_sink=sink,
        config=ExecutionConfig(max_hold_minutes=0),  # held_too_long immediately
    )

    result = executor.run()

    assert result.status == "TIME_STOP"
    assert len(sink.opened) == 1 and len(sink.closed) == 1
    assert sink.closed[0].status == "TIME_STOP"
    assert broker.close_position_calls == [DEAL_ID]


def test_reward_sink_not_fired_when_no_order(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """A NO_TRADE path (abstain) places no order → neither callback fires."""
    broker = FakeBroker(account_env=_account(1500.0))
    state = FakeState(fresh=True, candidates=[])  # abstain
    sink = _RecordingSink()
    executor, _ = _build(broker, state, exec_state, reward_sink=sink)

    result = executor.run()

    assert result.status == "NO_TRADE"
    assert sink.opened == [] and sink.closed == []


def test_reward_sink_open_raising_does_not_crash_cycle(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """A throwing on_trade_opened is swallowed → the cycle still completes (Decision J)."""
    broker = _full_path_broker()
    state = FakeState(fresh=True, candidates=[make_candidate(direction="BUY")])
    sink = _RecordingSink(raise_on_open=True)
    executor, _ = _build(broker, state, exec_state, reward_sink=sink)

    result = executor.run()

    assert result.status == "CLOSED_BY_BROKER"   # cycle unaffected
    assert len(broker.open_position_calls) == 1
    assert len(sink.closed) == 1                  # close seam still fires


def test_reward_sink_close_raising_does_not_crash_cycle(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """A throwing on_trade_closed is swallowed → the cycle still returns its result (J)."""
    broker = _full_path_broker()
    state = FakeState(fresh=True, candidates=[make_candidate(direction="BUY")])
    sink = _RecordingSink(raise_on_close=True)
    executor, _ = _build(broker, state, exec_state, reward_sink=sink)

    result = executor.run()

    assert result.status == "CLOSED_BY_BROKER"
    assert len(sink.opened) == 1 and len(sink.closed) == 1
