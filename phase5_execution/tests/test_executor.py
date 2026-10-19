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

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import pytest

from execution.config import ExecutionConfig
from execution.execution_state import CLOSED, ExecutionState
from execution.executor import Executor, build_opened
from execution.models import ExecutionResult, OrderPlan
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
    abstain_sink: Any | None = None,
    context_recorder: Any | None = None,
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
        abstain_sink=abstain_sink,
        context_recorder=context_recorder,
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
    assert opened.provenance == "autonomous"                # candidate reasoning != seed marker
    assert opened.deal_reference.startswith("bot-")

    closed = sink.closed[0]
    assert closed.status == "CLOSED_BY_BROKER"
    assert closed.deal_id == DEAL_ID
    assert closed.deal_reference == opened.deal_reference   # links back to the open


def test_reward_sink_open_payload_tags_seed_provenance(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """v1.5 (Step 4 A): a manual-seed candidate (``reasoning`` starts with the seed marker)
    → ``opened.provenance == "verification"`` so its lesson is later kept out of the prompt.
    A deterministic string check — no AI; the autonomous case is pinned by the test above."""
    broker = _full_path_broker()
    seed_reasoning = "MANUAL SEED (not a real research pick): injected to exercise the path"
    state = FakeState(
        fresh=True, candidates=[make_candidate(direction="BUY", reasoning=seed_reasoning)]
    )
    sink = _RecordingSink()
    executor, _ = _build(broker, state, exec_state, reward_sink=sink)

    executor.run()

    assert sink.opened[0].provenance == "verification"


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


def test_build_closed_carries_close_confirm_pnl(
    make_order_plan: Callable[..., OrderPlan]
) -> None:
    """build_closed threads the monitor's realised close_level/profit_loss onto the
    ClosedTrade (the Phase-7 lag-free P&L path, 2026-06-23)."""
    from execution.executor import build_closed
    from execution.models import ExecutionResult

    plan = make_order_plan()
    result = ExecutionResult(
        status="TIME_STOP", deal_id="D1", plan=plan, detail="time-stop (max_hold)",
        close_level=24990.0, profit_loss=42.0,
    )
    closed = build_closed(result, now=datetime(2026, 6, 23, 14, 0))

    assert closed.status == "TIME_STOP"
    assert closed.deal_id == "D1"
    assert closed.close_level == 24990.0
    assert closed.profit_loss == 42.0


def test_build_opened_scales_initial_risk_by_point_value(
    make_order_plan: Callable[..., OrderPlan]
) -> None:
    """v1.5 (Issue C): build_opened threads the per-epic point value into initial_risk."""
    plan = make_order_plan(direction="BUY", size=1.0, stop_level=17970.0)
    price_env = _FakeEnv(ok=True, data={"ask": 18000.0, "bid": 17999.0})
    place = ExecutionResult(status="OPEN", deal_id=DEAL_ID, plan=plan, detail=None)
    now = datetime(2026, 7, 1, 10, 0)

    # Default point_value 1.0 → |18000-17970| * 1.0 * 1.0 = 30.0
    opened_default = build_opened(
        {"llm_confidence": 70.0}, plan, place, price_env, None,
        score_at_open=50.0, now=now,
    )
    assert opened_default.initial_risk == 30.0

    # point_value 5.0 → 30 * 1.0 * 5.0 = 150.0 (proves the value threads through)
    opened_pv5 = build_opened(
        {"llm_confidence": 70.0}, plan, place, price_env, None,
        score_at_open=50.0, now=now, point_value=5.0,
    )
    assert opened_pv5.initial_risk == 150.0


def test_build_closed_defaults_none_without_confirm(
    make_order_plan: Callable[..., OrderPlan]
) -> None:
    """A close with no confirm enrichment (e.g. CLOSED_BY_BROKER) → None P&L (history fallback)."""
    from execution.executor import build_closed
    from execution.models import ExecutionResult

    result = ExecutionResult(
        status="CLOSED_BY_BROKER", deal_id="D2", plan=make_order_plan(), detail="SL/TP",
    )
    closed = build_closed(result, now=datetime(2026, 6, 23, 14, 0))

    assert closed.close_level is None
    assert closed.profit_loss is None


# --- 20–25) Phase-10 (V3) abstain-sink seam (Decision J) -------------------
#
# The seam wraps every NO_TRADE return path via the shared ``_no_trade`` helper — never
# the trade path. Like the reward-sink seam, the sink is read duck-typed (a tiny
# recording stand-in), and ``abstain_sink=None`` (the default) must leave every existing
# NO_TRADE/TRADE behaviour bit-identical (proven by the full pre-existing suite staying
# green + the explicit passthrough test below).


class _RecordingAbstainSink:
    """Duck-typed ``AbstainSink`` stand-in — records the ``cycle_outcome`` dicts it sees."""

    def __init__(self, *, raise_on_call: bool = False, record_id: str | None = None) -> None:
        self.calls: list[dict[str, Any]] = []
        self._raise_on_call = raise_on_call
        self._record_id = record_id

    def on_no_trade(self, cycle_outcome: dict[str, Any]) -> str | None:
        self.calls.append(cycle_outcome)
        if self._raise_on_call:
            raise RuntimeError("abstain_sink.on_no_trade boom")
        return self._record_id


def test_abstain_sink_none_is_bit_identical_passthrough(exec_state: ExecutionState) -> None:
    """``abstain_sink=None`` (the default) → a NO_TRADE cycle behaves exactly as before."""
    broker = FakeBroker(account_env=_account(1500.0))
    state = FakeState(fresh=True, candidates=[])  # abstain
    executor, _ = _build(broker, state, exec_state)  # no abstain_sink

    result = executor.run()

    assert result.status == "NO_TRADE"
    assert "load_candidates" in result.detail


def test_abstain_sink_fires_on_gate1_time_window(exec_state: ExecutionState,
                                                   make_candidate: Callable[..., dict[str, Any]]) -> None:
    """Gate 1 fail -> ``failed_gate="G1"``, ``epic=None`` (no candidate loaded yet)."""
    broker = FakeBroker()
    state = FakeState(fresh=True, candidates=[make_candidate()])
    sink = _RecordingAbstainSink()
    executor, _ = _build(broker, state, exec_state, abstain_sink=sink, now_fn=lambda: _at(20, 0))

    executor.run()

    assert len(sink.calls) == 1
    outcome = sink.calls[0]
    assert outcome["outcome"] == "NO_TRADE"
    assert outcome["epic"] is None
    assert outcome["failed_gate"] == "G1"
    assert outcome["research_empty"] is False
    assert outcome["veto"] is None
    assert outcome["debate_decision"] is None
    assert outcome["error"] is None


def test_abstain_sink_fires_on_gate2_no_candidates(exec_state: ExecutionState) -> None:
    """Gate 2 abstain (empty candidates) -> ``research_empty=True``."""
    broker = FakeBroker(account_env=_account(1500.0))
    state = FakeState(fresh=True, candidates=[])
    sink = _RecordingAbstainSink()
    executor, _ = _build(broker, state, exec_state, abstain_sink=sink)

    executor.run()

    assert len(sink.calls) == 1
    assert sink.calls[0]["research_empty"] is True
    assert sink.calls[0]["failed_gate"] is None


def test_abstain_sink_fires_on_veto_momentum(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """A momentum VETO -> ``veto="momentum"``, ``epic`` set (candidate was loaded)."""
    from tests.conftest import make_bars

    broker = FakeBroker(
        account_env=_account(1500.0),
        ohlcv_env=_FakeEnv(ok=True, data={"bars": make_bars([18000.0, 17900.0])}),
    )
    state = FakeState(fresh=True, candidates=[make_candidate(direction="BUY")])
    sink = _RecordingAbstainSink()
    executor, _ = _build(broker, state, exec_state, abstain_sink=sink)

    executor.run()

    assert len(sink.calls) == 1
    outcome = sink.calls[0]
    assert outcome["veto"] == "momentum"
    assert outcome["epic"] == DEFAULT_EPIC
    assert outcome["failed_gate"] is None


def test_abstain_sink_fires_on_debate_abstain(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """A debate ABSTAIN -> ``debate_decision="ABSTAIN"``, ``epic`` set."""
    debate = _DebateRunner(_DebateOutcome("ABSTAIN", None, confidence=0.4))
    broker = FakeBroker(account_env=_account(1500.0))
    state = FakeState(fresh=True, candidates=[make_candidate(direction="BUY")])
    sink = _RecordingAbstainSink()
    executor, _ = _build(broker, state, exec_state, debate_runner=debate, abstain_sink=sink)

    executor.run()

    assert len(sink.calls) == 1
    outcome = sink.calls[0]
    assert outcome["debate_decision"] == "ABSTAIN"
    assert outcome["epic"] == DEFAULT_EPIC


def test_abstain_sink_carries_detail_for_debate_abstain(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """Phase-10 B4-fix (2026-07-31): the Judge's own rationale reaches cycle_outcome["detail"]
    — previously computed for the ExecutionResult but never handed to the classifier, so every
    AbstainRecord.detail landed at "" (see phase10_v3/DATA_WEEK_REVIEW_2026-07-31.md §4 B4)."""
    debate = _DebateRunner(
        _DebateOutcome("ABSTAIN", None, confidence=0.4, rationale="4 consecutive BUY losses")
    )
    broker = FakeBroker(account_env=_account(1500.0))
    state = FakeState(fresh=True, candidates=[make_candidate(direction="BUY")])
    sink = _RecordingAbstainSink()
    executor, _ = _build(broker, state, exec_state, debate_runner=debate, abstain_sink=sink)

    executor.run()

    assert sink.calls[0]["detail"] == "4 consecutive BUY losses"


def test_abstain_sink_carries_detail_for_veto(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """Same B4-fix, VETO path: cycle_outcome["detail"] carries the VETO's own reason text."""
    from tests.conftest import make_bars

    broker = FakeBroker(
        account_env=_account(1500.0),
        ohlcv_env=_FakeEnv(ok=True, data={"bars": make_bars([18000.0, 17900.0])}),
    )
    state = FakeState(fresh=True, candidates=[make_candidate(direction="BUY")])
    sink = _RecordingAbstainSink()
    executor, _ = _build(broker, state, exec_state, abstain_sink=sink)

    executor.run()

    assert sink.calls[0]["detail"]  # non-empty — the VETO's own reason string
    assert sink.calls[0]["detail"] != ""


def test_context_recorder_receives_spread_pct_on_veto_no_trade(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """Phase-10 B4-fix (2026-07-31): a VETO NO_TRADE has a fresh Gate-4 price snapshot in
    scope (fetched just before the VETOs) — spread_pct now reaches decision_context instead
    of always NULL (see phase10_v3/DATA_WEEK_REVIEW_2026-07-31.md §4 B4)."""
    from tests.conftest import make_bars

    broker = FakeBroker(
        account_env=_account(1500.0),
        ohlcv_env=_FakeEnv(ok=True, data={"bars": make_bars([18000.0, 17900.0])}),
    )
    state = FakeState(fresh=True, candidates=[make_candidate(direction="BUY")])
    recorder = _RecordingContextRecorder()
    executor, _ = _build(broker, state, exec_state, context_recorder=recorder)

    executor.run()

    assert recorder.calls[0]["spread_pct"] == pytest.approx(0.03)  # FakeBroker's default price


def test_context_recorder_spread_pct_none_before_gate4(
    exec_state: ExecutionState,
) -> None:
    """A Gate-2 abstain (no candidate) has no price snapshot yet — spread_pct stays None,
    not a fabricated value."""
    broker = FakeBroker(account_env=_account(1500.0))
    state = FakeState(fresh=True, candidates=[])
    recorder = _RecordingContextRecorder()
    executor, _ = _build(broker, state, exec_state, context_recorder=recorder)

    executor.run()

    assert recorder.calls[0]["spread_pct"] is None


def test_context_recorder_receives_spread_pct_on_trade(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """Phase-10 B4-fix: the TRADE path also carries spread_pct (it already had price_env in
    scope, just never passed it to the recorder)."""
    broker = _full_path_broker()
    state = FakeState(fresh=True, candidates=[make_candidate(direction="BUY")])
    recorder = _RecordingContextRecorder()
    executor, _ = _build(broker, state, exec_state, context_recorder=recorder)

    executor.run()

    assert recorder.calls[0]["spread_pct"] == pytest.approx(0.03)


def test_abstain_sink_not_fired_on_trade_path(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """A full open->closed trade path never calls the abstain sink."""
    broker = _full_path_broker()
    state = FakeState(fresh=True, candidates=[make_candidate(direction="BUY")])
    sink = _RecordingAbstainSink()
    executor, _ = _build(broker, state, exec_state, abstain_sink=sink)

    result = executor.run()

    assert result.status == "CLOSED_BY_BROKER"
    assert sink.calls == []


def test_abstain_sink_raising_does_not_crash_cycle(exec_state: ExecutionState) -> None:
    """A throwing ``on_no_trade`` is swallowed -> the cycle still returns NO_TRADE (J)."""
    broker = FakeBroker(account_env=_account(1500.0))
    state = FakeState(fresh=True, candidates=[])
    sink = _RecordingAbstainSink(raise_on_call=True)
    executor, _ = _build(broker, state, exec_state, abstain_sink=sink)

    result = executor.run()

    assert result.status == "NO_TRADE"
    assert len(sink.calls) == 1


# --- 26–31) Phase-10 (V3) Block-B context-recorder seam (Decision J) -------
#
# ``context_recorder=None`` (the default) must leave every existing TRADE/NO_TRADE/ABORT
# behaviour bit-identical (proven by the full pre-existing suite staying green). Unlike
# ``abstain_sink``/``reward_sink``, this seam fires on all three cycle outcomes — including
# the post-debate ABORT path (Nikinger-authorized scope extension, 2026-07-17's Bug B: a
# debate-approved TRADE whose order the broker then rejects).


class _RecordingContextRecorder:
    """Duck-typed ``ContextRecorder`` stand-in — records every ``on_decision`` call."""

    def __init__(self, *, raise_on_call: bool = False) -> None:
        self.calls: list[dict[str, Any]] = []
        self._raise_on_call = raise_on_call

    def on_decision(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)
        if self._raise_on_call:
            raise RuntimeError("context_recorder.on_decision boom")


def test_context_recorder_none_is_bit_identical_passthrough(exec_state: ExecutionState) -> None:
    """``context_recorder=None`` (the default) → a NO_TRADE cycle behaves exactly as before."""
    broker = FakeBroker(account_env=_account(1500.0))
    state = FakeState(fresh=True, candidates=[])
    executor, _ = _build(broker, state, exec_state)  # no context_recorder

    result = executor.run()

    assert result.status == "NO_TRADE"


def test_context_recorder_fires_on_trade_path(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """A full open->closed trade path records exactly one TRADE context, with deal_id."""
    broker = _full_path_broker()
    state = FakeState(fresh=True, candidates=[make_candidate(direction="BUY")])
    recorder = _RecordingContextRecorder()
    executor, _ = _build(broker, state, exec_state, context_recorder=recorder)

    result = executor.run()

    assert result.status == "CLOSED_BY_BROKER"
    assert len(recorder.calls) == 1
    call = recorder.calls[0]
    assert call["outcome"] == "TRADE"
    assert call["epic"] == DEFAULT_EPIC
    assert call["deal_id"] == DEAL_ID
    assert call["abstain_record_id"] is None


def test_context_recorder_fires_on_no_trade_path_with_abstain_record_id(
    exec_state: ExecutionState,
) -> None:
    """A NO_TRADE cycle records outcome=NO_TRADE, linked to the real abstain record_id."""
    broker = FakeBroker(account_env=_account(1500.0))
    state = FakeState(fresh=True, candidates=[])  # Gate 2 abstain (research_empty)
    abstain_sink = _RecordingAbstainSink(record_id="abs-42")
    recorder = _RecordingContextRecorder()
    executor, _ = _build(
        broker, state, exec_state, abstain_sink=abstain_sink, context_recorder=recorder,
    )

    executor.run()

    assert len(recorder.calls) == 1
    call = recorder.calls[0]
    assert call["outcome"] == "NO_TRADE"
    assert call["abstain_record_id"] == "abs-42"
    assert call["deal_id"] is None


def test_context_recorder_fires_on_abort_after_debate_approved_but_broker_rejects(
    exec_state: ExecutionState, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """Bug B (2026-07-15): TRADE debate decision, then broker REJECTED -> ABORT is recorded."""
    broker = FakeBroker(
        account_env=_account(1500.0),
        positions_env=_positions(),  # Gate 3/5 + VETO 4 all clear
        open_env=_FakeEnv(ok=True, data={"status": "REJECTED", "reason": "INSUFFICIENT_FUNDS"}),
    )
    state = FakeState(fresh=True, candidates=[make_candidate(direction="BUY")])
    debate = _DebateRunner(_DebateOutcome("TRADE", "BUY", confidence=57.0))
    recorder = _RecordingContextRecorder()
    executor, _ = _build(
        broker, state, exec_state, debate_runner=debate, context_recorder=recorder,
    )

    result = executor.run()

    assert result.status == "ABORT"
    assert len(recorder.calls) == 1
    call = recorder.calls[0]
    assert call["outcome"] == "ABORT"
    assert call["epic"] == DEFAULT_EPIC
    assert call["deal_id"] is None
    assert call["debate_outcome"] is debate.outcome
    # Bug-B follow-up (2026-07-17): the broker's own reject reason must round-trip
    # into the persisted row — otherwise a future rejection is invisible without
    # stderr access (exactly what made 2026-07-15's incident undiagnosable).
    veto_results = json.loads(call["veto_results_json"])
    assert "INSUFFICIENT_FUNDS" in veto_results["abort_detail"]


def test_context_recorder_not_fired_on_early_session_health_abort(
    exec_state: ExecutionState,
) -> None:
    """The pre-Gate-1 session-health ABORT has no candidate yet -> deliberately unrecorded."""
    broker = FakeBroker(account_env=_FakeEnv(ok=False, data=None))
    state = FakeState(fresh=True, candidates=[])
    recorder = _RecordingContextRecorder()
    executor, _ = _build(broker, state, exec_state, context_recorder=recorder)

    result = executor.run()

    assert result.status == "ABORT"
    assert recorder.calls == []


def test_context_recorder_raising_does_not_crash_cycle(exec_state: ExecutionState) -> None:
    """A throwing ``on_decision`` is swallowed -> the cycle still returns NO_TRADE (J)."""
    broker = FakeBroker(account_env=_account(1500.0))
    state = FakeState(fresh=True, candidates=[])
    recorder = _RecordingContextRecorder(raise_on_call=True)
    executor, _ = _build(broker, state, exec_state, context_recorder=recorder)

    result = executor.run()

    assert result.status == "NO_TRADE"
    assert len(recorder.calls) == 1


# --- 32–35) Phase-17 B-5 monitor re-adoption seam (T8) ----------------------
#
# ``resume_open_position()`` is called by the P8 scheduler runner in the WINDOW phase
# after a restart (the bot was down with an open trade — AEX id 26 ran 6 days without
# ``max_hold`` ever being checked, Phase-17-Block-B). Picker over open references,
# rebuilds an ``OrderPlan`` from the recorded state, hands ``recorded_at`` to
# ``monitor_position`` as ``entry_at`` so an already-elapsed ``max_hold`` closes immediately.
# Never touches the regular run() path — see test_executor.py for the existing 31 tests.


def _seed_open_reference(
    exec_state: ExecutionState,
    *,
    deal_id: str = "DIAAAA-FAKE",
    recorded_at: str = "2026-06-11T09:00:00.000Z",
) -> str:
    """Write a synthetic ``OPEN`` record into ``exec_state`` and return its ``deal_reference``.

    Uses the public :class:`ExecutionState` API (``record_pending`` + ``mark_open``) and then
    pokes ``recorded_at`` to the requested string — same shape the live boot produces
    (``_format_iso(_utcnow())`` always emits the trailing ``Z``).
    """
    plan = OrderPlan(
        epic=DEFAULT_EPIC, direction="BUY", size=1.0,
        stop_level=17970.0, limit_level=18045.0,
        deal_reference=f"bot-{uuid.uuid4().hex}",
        currency="EUR",
    )
    exec_state.record_pending(plan)
    exec_state.mark_open(plan.deal_reference, deal_id)
    # record_pending/_write already produced a recorded_at; overwrite via the public store.
    records = exec_state._read()  # noqa: SLF001 — test-only direct poke
    records[plan.deal_reference]["recorded_at"] = recorded_at
    exec_state._write(records)  # noqa: SLF001
    return plan.deal_reference


def _tz_aware_now() -> Callable[[], datetime]:
    """A tz-aware UTC ``now_fn`` compatible with recorded_at deserialization (the
    executed ``recorded_at`` is tz-aware UTC; subtracting a naive now would TypeError)."""
    return lambda: datetime(2026, 6, 11, 10, 0, tzinfo=timezone.utc)


def test_resume_monitors_present_open_record_from_recorded_at(
    exec_state: ExecutionState,
) -> None:
    """Phase 17 B-5: an OPEN ref whose deal_id the broker still holds is rebuilt into an
    OrderPlan + watched from its recorded open time. A broker-side close → CLOSED_BY_BROKER,
    the write-ahead ref is marked CLOSED, and the Phase-7 close seam receives the result."""
    ref = _seed_open_reference(exec_state)
    broker = FakeBroker(
        positions_sequence=[_positions(_open_position()), _positions()],
    )
    sink = _RecordingSink()
    executor, _ = _build(
        broker, FakeState(fresh=True, candidates=[]), exec_state,
        now_fn=_tz_aware_now(), reward_sink=sink,
    )

    result = executor.resume_open_position()

    assert result is not None
    assert result.status == "CLOSED_BY_BROKER"
    assert result.deal_id == "DIAAAA-FAKE"
    assert exec_state.get(ref)["status"] == CLOSED
    assert exec_state.open_references() == []
    # The Phase-7 close seam fired with the same ClosedTrade snapshot it gets in run().
    assert len(sink.closed) == 1
    assert sink.closed[0].status == "CLOSED_BY_BROKER"
    assert sink.closed[0].deal_id == "DIAAAA-FAKE"


def test_resume_returns_none_when_position_missing_at_broker(
    exec_state: ExecutionState,
) -> None:
    """Phase 17 B-5: an OPEN ref whose deal_id is gone at the broker is left to
    ``reconcile_startup``'s missing-set — ``resume_open_position()`` returns ``None``
    without calling ``close_position`` (the broker closed it, not us)."""
    _seed_open_reference(exec_state)
    broker = FakeBroker(positions_env=_positions())  # no DIAAAA-FAKE in the list
    executor, _ = _build(
        broker, FakeState(fresh=True, candidates=[]), exec_state,
        now_fn=_tz_aware_now(),
    )

    result = executor.resume_open_position()

    assert result is None
    # Nothing was closed by us; broker had already closed it.
    assert broker.close_position_calls == []


def test_resume_skips_pending_without_deal_id(exec_state: ExecutionState) -> None:
    """Phase 17 B-5: a PENDING ref without a deal_id is reconcile_startup's job (orphan
    PENDING). ``resume_open_position()`` skips it — broker is never even queried."""
    plan = OrderPlan(
        epic=DEFAULT_EPIC, direction="BUY", size=1.0,
        stop_level=17970.0, limit_level=18045.0,
        deal_reference=f"bot-{uuid.uuid4().hex}",
        currency="EUR",
    )
    exec_state.record_pending(plan)  # PENDING with deal_id=None
    broker = FakeBroker()
    executor, _ = _build(
        broker, FakeState(fresh=True, candidates=[]), exec_state,
        now_fn=_tz_aware_now(),
    )

    result = executor.resume_open_position()

    assert result is None
    assert broker.get_open_positions_calls == 0  # never queried the broker
    # The PENDING ref is still in the store; reconcile_startup decides what to do with it.
    assert plan.deal_reference in exec_state.open_references()


def test_resume_closes_immediately_when_max_hold_elapsed(
    exec_state: ExecutionState,
) -> None:
    """Phase 17 B-5 (T8): recorded_at + max_hold already elapsed before the first poll ->
    one close_position call, TIME_STOP with ``max_hold`` in detail, the ref is closed."""
    _seed_open_reference(exec_state, recorded_at="2026-06-11T09:00:00.000Z")
    broker = FakeBroker(positions_env=_positions(_open_position()))
    # Now is 14:00 UTC; recorded 09:00 UTC = 5 h ago > 4 h default max_hold.
    now_fn = lambda: datetime(2026, 6, 11, 14, 0, tzinfo=timezone.utc)
    sink = _RecordingSink()
    executor, _ = _build(
        broker, FakeState(fresh=True, candidates=[]), exec_state,
        now_fn=now_fn, reward_sink=sink,
    )

    result = executor.resume_open_position()

    assert result is not None
    assert result.status == "TIME_STOP"
    assert "max_hold" in result.detail
    assert broker.close_position_calls == ["DIAAAA-FAKE"]  # exactly one close attempt
    assert len(sink.closed) == 1 and sink.closed[0].status == "TIME_STOP"
