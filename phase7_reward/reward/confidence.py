"""Outcome-anchored confidence math for Phase 7 (concept §6 Step 4, Decision C).

**Pure, deterministic, no I/O** — no network, no LLM, no broker, no DB. This is
the single most test-critical module in the phase (★), and it is *not* AI: the
"AI as little as possible" principle puts every number here in plain code.

The product is a :class:`~reward.models.ConfidenceReport`. Its ``confidence_value``
is **observe-only and gates nothing** in v1 (Decision C): it does not gate an
order and does not modulate ``risk_pct``. Below ``cfg.n_min`` trades the picture
is ``INSUFFICIENT`` and ``confidence_value`` is ``None`` (flows into nothing) —
the deliberate guard against the naive small-N collapse (1 win out of 1 is *not*
100 % confidence). The named sub-metrics (raw rate, Wilson lower bound,
expectancy-R, SQN) are always populated when computable; they are the real
logging quantities.

Conventions: stdlib ``math`` / ``statistics`` only — no third-party numeric dep
is needed for these closed-form estimators.
"""

from __future__ import annotations

import math
import statistics

from reward.models import ConfidenceReport, RewardConfig

__all__ = [
    "wilson_lower_bound",
    "expectancy_r",
    "system_quality_number",
    "compute_confidence",
]


def wilson_lower_bound(successes: int, n: int, z: float = 1.96) -> float | None:
    """Wilson score interval lower bound for a binomial proportion.

    A conservative, small-N-stable estimator of the win rate. Unlike the naive
    ``successes / n``, it does **not** collapse to 1.0 on a lucky 1-of-1 (it
    returns ≈ 0.21 at z=1.96) — exactly the behaviour Decision C relies on to
    avoid over-trusting a tiny sample. For zero wins the lower bound is 0.0 by
    construction (you have no evidence the true rate is above zero), which is the
    correct conservative floor, not a degenerate collapse.

    Args:
        successes: number of wins (``0 <= successes <= n``).
        n: number of trials.
        z: standard-normal quantile (1.96 ≈ 95 % two-sided → a one-sided lower
            bound at ~97.5 %).

    Returns:
        The lower bound in ``[0, 1]``, or ``None`` when ``n == 0`` (undefined).
    """
    if n <= 0:
        return None
    p_hat = successes / n
    z2 = z * z
    denominator = 1.0 + z2 / n
    center = p_hat + z2 / (2.0 * n)
    margin = z * math.sqrt((p_hat * (1.0 - p_hat) + z2 / (4.0 * n)) / n)
    return (center - margin) / denominator


def expectancy_r(r_multiples: list[float]) -> float | None:
    """Mean R-multiple (realised P&L per trade expressed in units of risk-taken).

    Args:
        r_multiples: per-trade R-multiples (P&L / initial risk).

    Returns:
        The arithmetic mean, or ``None`` for an empty list.
    """
    if not r_multiples:
        return None
    return statistics.fmean(r_multiples)


def system_quality_number(r_multiples: list[float]) -> float | None:
    """Van Tharp's System Quality Number: ``sqrt(N) * mean(R) / stdev(R)``.

    A side-metric only (Decision C); reported for logging, never gating. Van
    Tharp considers ``N > 30`` necessary for significance, so a value at small N
    is informational. Uses the **sample** standard deviation (ddof=1).

    Args:
        r_multiples: per-trade R-multiples.

    Returns:
        The SQN, or ``None`` when undefined — ``N < 2`` (no sample stdev) or
        zero variance (would divide by zero).
    """
    n = len(r_multiples)
    if n < 2:
        return None
    stdev = statistics.stdev(r_multiples)
    if stdev == 0.0:
        return None
    return math.sqrt(n) * statistics.fmean(r_multiples) / stdev


def _combine_confidence(
    wilson_lb: float, exp_r: float | None, cfg: RewardConfig
) -> float:
    """The v1 confidence combiner → a value on the ``[0, 100]`` score scale.

    Observe-only, so the exact shape is **not** load-bearing (Decision C); it is
    kept simple, monotonic in both inputs, and bounded. Two normalised, equally
    weighted components:

    - ``win_component = wilson_lb`` (already in ``[0, 1]``) — the conservative
      win-rate floor.
    - ``edge_component`` maps expectancy-R onto ``[0, 1]`` linearly: neutral 0.5
      at 0R, → 1 at ``+r_clip``, → 0 at ``-r_clip`` (``r_clip`` reused from the
      scoring config; a missing expectancy is treated as neutral 0R).

    ``confidence_value = 100 * (0.5 * win_component + 0.5 * edge_component)``,
    clamped to ``[0, 100]``.
    """
    edge_raw = 0.0 if exp_r is None else exp_r
    if cfg.r_clip > 0:
        edge_component = 0.5 + edge_raw / (2.0 * cfg.r_clip)
    else:
        edge_component = 0.5
    edge_component = min(1.0, max(0.0, edge_component))
    value = 100.0 * (0.5 * wilson_lb + 0.5 * edge_component)
    return min(100.0, max(0.0, value))


def compute_confidence(
    r_multiples: list[float], wins: int, n: int, cfg: RewardConfig
) -> ConfidenceReport:
    """Assemble the outcome-anchored confidence picture (Decision C).

    The caller owns edge-set selection (e.g. whether ``account='demo'`` trades
    count via ``include_demo_in_edge``) and passes the resulting ``r_multiples``,
    ``wins`` and ``n`` — this function does **not** re-derive ``n`` from the list
    length.

    Gating: ``n < cfg.n_min`` → ``state="INSUFFICIENT"`` and
    ``confidence_value=None`` (flows into nothing — the small-N guard). Otherwise
    ``state="OK"`` with a bounded ``confidence_value``. The sub-metrics
    (``win_rate_raw``, ``win_rate_wilson_lb``, ``expectancy_r``, ``sqn``) are
    populated whenever computable, **independent** of the gate.

    Args:
        r_multiples: per-trade R-multiples over the edge set.
        wins: number of winning trades in that set.
        n: number of trades in that set.
        cfg: the reward config (``n_min``, ``wilson_z``, ``r_clip``).

    Returns:
        A frozen :class:`~reward.models.ConfidenceReport`.
    """
    win_rate_raw = wins / n if n > 0 else None
    win_rate_wilson_lb = wilson_lower_bound(wins, n, cfg.wilson_z)
    exp_r = expectancy_r(r_multiples)
    sqn = system_quality_number(r_multiples)

    if n < cfg.n_min:
        return ConfidenceReport(
            state="INSUFFICIENT",
            n=n,
            win_rate_raw=win_rate_raw,
            win_rate_wilson_lb=win_rate_wilson_lb,
            expectancy_r=exp_r,
            sqn=sqn,
            confidence_value=None,
        )

    # OK branch: n >= n_min >= 1 guarantees a Wilson bound (n > 0).
    confidence_value = _combine_confidence(win_rate_wilson_lb or 0.0, exp_r, cfg)
    return ConfidenceReport(
        state="OK",
        n=n,
        win_rate_raw=win_rate_raw,
        win_rate_wilson_lb=win_rate_wilson_lb,
        expectancy_r=exp_r,
        sqn=sqn,
        confidence_value=confidence_value,
    )
