"""Tests for the Phase-7 confidence math (Step 4) — the ★ priority suite.

Pure deterministic math: no network, no LLM, no DB. These pin the closed-form
estimators against known values and, more importantly, the **load-bearing**
behaviour Decision C relies on: the small-N guard (``INSUFFICIENT`` →
``confidence_value=None``) and the anti-collapse property of the Wilson lower
bound (a lucky 1-of-1 is *not* 100 % confidence).
"""

from __future__ import annotations

import statistics

import pytest

from reward.confidence import (
    compute_confidence,
    expectancy_r,
    system_quality_number,
    wilson_lower_bound,
)
from reward.models import ConfidenceReport, RewardConfig


# --------------------------------------------------------------------------- #
# 1. wilson_lower_bound — known values, anti-collapse, monotonicity, n==0      #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "successes, n, expected",
    [
        (7, 10, 0.39677),   # textbook Wilson LB at z=1.96
        (6, 10, 0.31268),
        (10, 10, 0.72254),  # 10/10 is NOT 1.0
        (0, 10, 0.0),       # zero wins → conservative 0.0 floor
    ],
)
def test_wilson_known_values(successes: int, n: int, expected: float) -> None:
    lb = wilson_lower_bound(successes, n)
    assert lb == pytest.approx(expected, abs=1e-4)


def test_wilson_n_zero_returns_none() -> None:
    # Undefined for an empty sample.
    assert wilson_lower_bound(0, 0) is None


def test_wilson_one_of_one_does_not_collapse_to_one() -> None:
    # The whole point of using Wilson over the naive rate (Decision C): a single
    # lucky win is ~0.21, not 1.0.
    lb = wilson_lower_bound(1, 1)
    assert lb == pytest.approx(0.20654, abs=1e-4)
    assert lb < 0.5


@pytest.mark.parametrize("n", [1, 10, 50])
def test_wilson_zero_successes_is_conservative_zero(n: int) -> None:
    # No wins → the lower bound is 0.0 for any n (correct, not a degenerate case).
    assert wilson_lower_bound(0, n) == pytest.approx(0.0, abs=1e-12)


def test_wilson_monotonic_in_successes_at_fixed_n() -> None:
    # More wins → a higher lower bound at fixed N.
    lbs = [wilson_lower_bound(k, 10) for k in (4, 5, 6, 7)]
    assert all(a is not None and b is not None and a < b for a, b in zip(lbs, lbs[1:]))


@pytest.mark.parametrize("successes, n", [(7, 10), (3, 10), (1, 4), (9, 10)])
def test_wilson_lb_never_exceeds_raw_rate(successes: int, n: int) -> None:
    # A *lower* bound is always ≤ the point estimate.
    lb = wilson_lower_bound(successes, n)
    assert lb is not None and lb <= successes / n


# --------------------------------------------------------------------------- #
# 2. expectancy_r — mean, empty, mixed signs                                   #
# --------------------------------------------------------------------------- #
def test_expectancy_is_the_mean_r() -> None:
    assert expectancy_r([2.0, -1.0, 0.5]) == pytest.approx(0.5)


def test_expectancy_empty_returns_none() -> None:
    assert expectancy_r([]) is None


def test_expectancy_handles_net_negative() -> None:
    assert expectancy_r([-1.0, -1.0, -1.0, 2.0]) == pytest.approx(-0.25)


# --------------------------------------------------------------------------- #
# 3. system_quality_number — known value, N<2, zero variance                   #
# --------------------------------------------------------------------------- #
def test_sqn_known_value() -> None:
    r = [2.0, -1.0, 2.0, -1.0, 2.0]
    # sqrt(5) * mean / sample-stdev ; mean=0.8, stdev(ddof=1)=sqrt(2.7)
    expected = (5 ** 0.5) * 0.8 / statistics.stdev(r)
    assert system_quality_number(r) == pytest.approx(expected, rel=1e-9)
    assert system_quality_number(r) == pytest.approx(1.08866, abs=1e-4)


@pytest.mark.parametrize("r", [[], [1.5]])
def test_sqn_needs_at_least_two_points(r: list[float]) -> None:
    assert system_quality_number(r) is None


def test_sqn_zero_variance_returns_none() -> None:
    # No dispersion → division by zero avoided.
    assert system_quality_number([1.0, 1.0, 1.0]) is None


# --------------------------------------------------------------------------- #
# 4. compute_confidence — the N_min gate (load-bearing, Decision C)            #
# --------------------------------------------------------------------------- #
def test_compute_confidence_insufficient_below_n_min() -> None:
    cfg = RewardConfig()  # n_min == 10
    rep = compute_confidence([1.0] * 9, wins=6, n=9, cfg=cfg)
    assert isinstance(rep, ConfidenceReport)
    assert rep.state == "INSUFFICIENT"
    assert rep.confidence_value is None
    assert rep.n == 9


def test_compute_confidence_ok_at_n_min() -> None:
    cfg = RewardConfig()
    r = [1.0, -1.0, 1.5, -1.0, 2.0, -1.0, 1.0, 0.5, -1.0, 1.2]
    rep = compute_confidence(r, wins=6, n=10, cfg=cfg)
    assert rep.state == "OK"
    assert rep.confidence_value is not None
    assert 0.0 <= rep.confidence_value <= 100.0


def test_compute_confidence_submetrics_populated_even_when_insufficient() -> None:
    # The named sub-metrics are the real logging quantities — always filled when
    # computable, independent of the gate (concept §6 Step 4: "IMMER befüllt").
    cfg = RewardConfig()
    rep = compute_confidence([1.0, -1.0, 2.0], wins=2, n=3, cfg=cfg)
    assert rep.state == "INSUFFICIENT"
    assert rep.confidence_value is None
    assert rep.win_rate_raw == pytest.approx(2 / 3)
    assert rep.win_rate_wilson_lb is not None
    assert rep.expectancy_r == pytest.approx(2 / 3)
    assert rep.sqn is not None


def test_compute_confidence_antipattern_one_win_is_not_full_confidence() -> None:
    # The proof test for Decision C: naive win-rate 1/1 = 100 % is NOT the
    # confidence. N < n_min → INSUFFICIENT, confidence_value=None.
    cfg = RewardConfig()
    rep = compute_confidence([2.0], wins=1, n=1, cfg=cfg)
    assert rep.win_rate_raw == 1.0          # the naive rate IS 100 %...
    assert rep.state == "INSUFFICIENT"      # ...but it does not become confidence
    assert rep.confidence_value is None


def test_compute_confidence_respects_custom_n_min() -> None:
    # n_min is config-tunable: at n_min=5, exactly 5 trades is OK.
    cfg = RewardConfig(n_min=5)
    rep = compute_confidence([1.0, -1.0, 1.0, -1.0, 1.0], wins=3, n=5, cfg=cfg)
    assert rep.state == "OK"
    assert rep.confidence_value is not None


@pytest.mark.parametrize(
    "r, wins, n",
    [
        ([1.0] * 12, 12, 12),                 # all wins
        ([-1.0] * 12, 0, 12),                 # all losses
        ([2.0, -1.0] * 6, 6, 12),             # mixed
    ],
)
def test_compute_confidence_value_within_bounds(
    r: list[float], wins: int, n: int
) -> None:
    rep = compute_confidence(r, wins=wins, n=n, cfg=RewardConfig())
    assert rep.state == "OK"
    assert rep.confidence_value is not None
    assert 0.0 <= rep.confidence_value <= 100.0


def test_compute_confidence_monotonic_in_wins() -> None:
    # With expectancy held neutral (0R mean), more wins → higher confidence,
    # driven by the rising Wilson lower bound.
    cfg = RewardConfig()
    r = [1.0, -1.0] * 10  # mean 0 → neutral edge component, 20 trades
    low = compute_confidence(r, wins=8, n=20, cfg=cfg)
    high = compute_confidence(r, wins=14, n=20, cfg=cfg)
    assert low.confidence_value is not None and high.confidence_value is not None
    assert high.confidence_value > low.confidence_value
