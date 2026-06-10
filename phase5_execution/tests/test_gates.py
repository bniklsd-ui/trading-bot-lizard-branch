"""Step 3 — Gate 1/2/3/5 (suitability gates).

Pure functions; all mocked, no network. Envelopes are the duck-typed ``_FakeEnv``
from conftest; Gate 2 uses ``FakeState`` + an injected ``research_runner`` stub.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

import pytest

from execution.config import ExecutionConfig
from execution.gates import (
    gate_constraints,
    gate_direction_consistency,
    gate_load_candidates,
    gate_time_window,
)
from tests.conftest import DEFAULT_EPIC, FakeState, _FakeEnv


@pytest.fixture
def config() -> ExecutionConfig:
    return ExecutionConfig()


# --- Gate 1: time window --------------------------------------------------


def test_gate1_inside_window(config: ExecutionConfig) -> None:
    # 10:00 Europe/Berlin, expressed as a UTC-aware datetime (08:00Z in summer).
    now = datetime(2026, 6, 10, 8, 0, tzinfo=timezone.utc)
    verdict = gate_time_window(now, config)
    assert verdict.ok is True
    assert verdict.gate == "time_window"


def test_gate1_before_window_rejects_with_tz_conversion(config: ExecutionConfig) -> None:
    # 06:00 UTC = 08:00 Berlin (summer), before the 09:00 open.
    now = datetime(2026, 6, 10, 6, 0, tzinfo=timezone.utc)
    verdict = gate_time_window(now, config)
    assert verdict.ok is False
    assert "outside trade window" in verdict.reason


def test_gate1_after_window_rejects(config: ExecutionConfig) -> None:
    # 18:00 Berlin (16:00Z summer) is past the 17:30 close.
    now = datetime(2026, 6, 10, 16, 0, tzinfo=timezone.utc)
    assert gate_time_window(now, config).ok is False


def test_gate1_honours_custom_window() -> None:
    cfg = ExecutionConfig(trading_window_start="10:00", trading_window_end="11:00")
    now = datetime(2026, 6, 10, 8, 30, tzinfo=timezone.utc)  # 10:30 Berlin
    assert gate_time_window(now, cfg).ok is True
    early = datetime(2026, 6, 10, 7, 0, tzinfo=timezone.utc)  # 09:00 Berlin
    assert gate_time_window(early, cfg).ok is False


# --- Gate 2: load candidates ----------------------------------------------


def _never_runs() -> list[dict[str, Any]]:
    raise AssertionError("research_runner must not be called when candidates are fresh")


def test_gate2_fresh_returns_first_candidate_without_running(
    config: ExecutionConfig, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    first = make_candidate(direction="BUY")
    state = FakeState(fresh=True, candidates=[first, make_candidate(direction="SELL")])

    verdict, candidate = gate_load_candidates(state, _never_runs, config)

    assert verdict.ok is True
    assert candidate is first  # the FIRST candidate is chosen
    assert state.load_calls == 1


def test_gate2_stale_runs_research_then_reloads(
    config: ExecutionConfig, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    pick = make_candidate()
    state = FakeState(fresh=False, candidates=[])
    ran: list[bool] = []

    def runner() -> list[dict[str, Any]]:
        ran.append(True)
        state.candidates = [pick]  # research persists; Gate 2 reloads from state
        return [pick]

    verdict, candidate = gate_load_candidates(state, runner, config)

    assert ran == [True]
    assert verdict.ok is True
    assert candidate == pick


def test_gate2_empty_is_abstain(config: ExecutionConfig) -> None:
    state = FakeState(fresh=False, candidates=[])
    verdict, candidate = gate_load_candidates(state, lambda: [], config)
    assert verdict.ok is False
    assert candidate is None
    assert verdict.gate == "load_candidates"


# --- Gate 3: constraints --------------------------------------------------


def test_gate3_budget_and_room_pass(
    config: ExecutionConfig, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    account = _FakeEnv(ok=True, data={"available": 5000.0})
    positions = _FakeEnv(ok=True, data={"positions": []})
    verdict = gate_constraints(account, positions, make_candidate(), config)
    assert verdict.ok is True


def test_gate3_no_budget_rejects(
    config: ExecutionConfig, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    account = _FakeEnv(ok=True, data={"available": 0.0})
    positions = _FakeEnv(ok=True, data={"positions": []})
    verdict = gate_constraints(account, positions, make_candidate(), config)
    assert verdict.ok is False
    assert "budget" in verdict.reason


def test_gate3_at_max_parallel_rejects(
    config: ExecutionConfig, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    account = _FakeEnv(ok=True, data={"available": 5000.0})
    # default max_parallel_positions == 1 → one open position is already the cap
    positions = _FakeEnv(ok=True, data={"positions": [{"epic": "X", "direction": "BUY"}]})
    verdict = gate_constraints(account, positions, make_candidate(), config)
    assert verdict.ok is False
    assert "max_parallel_positions" in verdict.reason


def test_gate3_env_not_ok_rejects(
    config: ExecutionConfig, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    bad_account = _FakeEnv(ok=False, data=None)
    positions = _FakeEnv(ok=True, data={"positions": []})
    assert gate_constraints(bad_account, positions, make_candidate(), config).ok is False

    account = _FakeEnv(ok=True, data={"available": 5000.0})
    bad_positions = _FakeEnv(ok=False, data=None)
    assert gate_constraints(account, bad_positions, make_candidate(), config).ok is False


# --- Gate 5: direction consistency ----------------------------------------


def test_gate5_invalid_direction_rejects(
    make_candidate: Callable[..., dict[str, Any]]
) -> None:
    positions = _FakeEnv(ok=True, data={"positions": []})
    verdict = gate_direction_consistency(make_candidate(direction="CALL"), positions)
    assert verdict.ok is False
    assert "invalid direction" in verdict.reason


def test_gate5_opposite_position_same_epic_rejects(
    make_candidate: Callable[..., dict[str, Any]]
) -> None:
    positions = _FakeEnv(
        ok=True, data={"positions": [{"epic": DEFAULT_EPIC, "direction": "SELL"}]}
    )
    verdict = gate_direction_consistency(make_candidate(direction="BUY"), positions)
    assert verdict.ok is False
    assert "conflicts" in verdict.reason


def test_gate5_same_direction_or_other_epic_passes(
    make_candidate: Callable[..., dict[str, Any]]
) -> None:
    # same direction on same epic → not blocked here (parallel count is Gate 3/VETO 4)
    same_dir = _FakeEnv(
        ok=True, data={"positions": [{"epic": DEFAULT_EPIC, "direction": "BUY"}]}
    )
    assert gate_direction_consistency(make_candidate(direction="BUY"), same_dir).ok is True

    # opposite direction but a *different* epic → no conflict
    other_epic = _FakeEnv(
        ok=True, data={"positions": [{"epic": "OTHER.EPIC", "direction": "SELL"}]}
    )
    assert gate_direction_consistency(make_candidate(direction="BUY"), other_epic).ok is True


def test_gate5_env_not_ok_rejects(make_candidate: Callable[..., dict[str, Any]]) -> None:
    bad = _FakeEnv(ok=False, data=None)
    assert gate_direction_consistency(make_candidate(direction="BUY"), bad).ok is False
