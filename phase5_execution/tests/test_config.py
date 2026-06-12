"""Step 1 — ``ExecutionConfig`` defaults + immutability.

No network, no broker, no I/O: pure dataclass checks. The defaults asserted here
are the locked concept §0 values (with the two reconciled units: ``max_spread_pct``
and ``risk_pct_*`` are percents).
"""

from __future__ import annotations

import dataclasses

import pytest

from execution.config import ExecutionConfig


def test_defaults_match_locked_concept_values() -> None:
    cfg = ExecutionConfig()

    # time / window
    assert cfg.tz == "Europe/Berlin"
    assert cfg.trading_window_start == "09:00"
    assert cfg.trading_window_end == "17:30"
    assert cfg.square_off_time == "17:15"
    assert cfg.max_hold_minutes == 240
    assert cfg.poll_interval_s == 15

    # VETOs
    assert cfg.max_spread_pct == 0.5            # percent of ask
    assert cfg.momentum_resolution == "MINUTE_5"
    assert cfg.momentum_count == 12
    assert cfg.momentum_veto_threshold_pct == 0.15

    # sizing (risk-per-trade percent — sizing.py divides by 100; reworked 2026-06-12)
    assert cfg.risk_pct_conservative == 2.0
    assert cfg.risk_pct_aggressive == 3.0
    assert cfg.max_leverage == 20.0

    # SL / TP (absolute-level offsets in points)
    assert cfg.stop_distance_points == 30.0
    assert cfg.limit_distance_points == 45.0

    # constraints / safety
    assert cfg.max_parallel_positions == 1
    assert cfg.require_confirm is True
    assert cfg.reconcile_unexpected_aborts is True


def test_momentum_resolution_is_a_valid_ig_resolution() -> None:
    # Guards against a typo that would only blow up live in VETO 3.
    assert ExecutionConfig().momentum_resolution in {
        "MINUTE", "MINUTE_5", "MINUTE_15", "MINUTE_30", "HOUR", "HOUR_4", "DAY",
    }


def test_is_frozen() -> None:
    cfg = ExecutionConfig()
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.require_confirm = False  # type: ignore[misc]


def test_overrides_are_honoured() -> None:
    cfg = ExecutionConfig(require_confirm=False, max_parallel_positions=2,
                          max_spread_pct=0.8)
    assert cfg.require_confirm is False
    assert cfg.max_parallel_positions == 2
    assert cfg.max_spread_pct == 0.8
    # untouched fields keep their defaults
    assert cfg.tz == "Europe/Berlin"
