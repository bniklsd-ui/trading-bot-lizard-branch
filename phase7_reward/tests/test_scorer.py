"""Tests for the Phase-7 process-aware scorer (Step 5) — a ★ priority suite.

Pure deterministic math: no network, no LLM, no DB. These pin the **load-bearing**
behaviour of Decision B2/D — that the score is *process-aware*, not outcome-only:
good process beats bad process at an identical outcome, an unlucky loss at a planned
stop is punished less than a sloppy one, the per-trade delta and the score itself
are clamped, and ``loss_asymmetry=1.0`` is symmetric. The exact magnitudes are v1
tunables (Decision D); the asserts target relative/structural properties, not the
specific numbers — except where the arithmetic is the contract (clamps, raw R).
"""

from __future__ import annotations

import pytest

from reward.models import RewardConfig, RewardResult
from reward.scorer import Scorer


def _scorer(**overrides: float) -> Scorer:
    """A Scorer on the §5 defaults, with optional per-test config overrides."""
    return Scorer(RewardConfig(**overrides))


# --------------------------------------------------------------------------- #
# 1. Core Decision-B2 proof: process differentiates at an identical outcome    #
# --------------------------------------------------------------------------- #
def test_good_outcome_clean_process_beats_bad_process() -> None:
    # Same winning R-multiple; only the process differs. A planned exit through a
    # tight spread must out-score a drift exit through a wide spread.
    s = _scorer()
    clean = s.score(
        r_multiple=1.0, status="CLOSED_BY_BROKER", spread_at_entry_pct=0.02,
        debate_confidence=None, score_before=50.0,
    )
    sloppy = s.score(
        r_multiple=1.0, status="TIME_STOP", spread_at_entry_pct=0.20,
        debate_confidence=None, score_before=50.0,
    )
    assert clean.score_after > sloppy.score_after
    assert clean.process_delta > sloppy.process_delta


def test_unlucky_loss_at_planned_stop_punished_less_than_sloppy_loss() -> None:
    # Same losing R-multiple; a loss that hit a planned stop (clean process) should
    # cost *less* score than a sloppy time-stop loss with a wide entry.
    s = _scorer()
    unlucky = s.score(
        r_multiple=-1.0, status="CLOSED_BY_BROKER", spread_at_entry_pct=0.02,
        debate_confidence=None, score_before=50.0,
    )
    sloppy = s.score(
        r_multiple=-1.0, status="TIME_STOP", spread_at_entry_pct=0.20,
        debate_confidence=None, score_before=50.0,
    )
    assert unlucky.score_after > sloppy.score_after


def test_process_delta_moves_score_independent_of_outcome() -> None:
    # At a breakeven outcome (outcome_delta == 0) the process component alone must
    # still move — and differentiate — the score (anti outcome-only).
    s = _scorer()
    clean = s.score(
        r_multiple=0.0, status="CLOSED_BY_BROKER", spread_at_entry_pct=0.02,
        debate_confidence=None, score_before=50.0,
    )
    drift = s.score(
        r_multiple=0.0, status="TIME_STOP", spread_at_entry_pct=0.20,
        debate_confidence=None, score_before=50.0,
    )
    assert clean.outcome_delta == 0.0 and drift.outcome_delta == 0.0
    assert clean.process_delta != 0.0
    assert clean.score_after != drift.score_after


# --------------------------------------------------------------------------- #
# 2. Clamping: per-trade |delta| cap and score bounds                          #
# --------------------------------------------------------------------------- #
def test_clamp_high_caps_delta_and_score() -> None:
    s = _scorer()
    r = s.score(
        r_multiple=100.0, status="CLOSED_BY_BROKER", spread_at_entry_pct=0.01,
        debate_confidence=90.0, score_before=50.0,
    )
    # The applied delta (score not at a bound here) cannot exceed the cap.
    cfg = RewardConfig()
    assert abs(r.score_after - r.score_before) <= cfg.max_delta_per_trade + 1e-9
    assert r.score_after <= cfg.score_max


def test_clamp_score_floor_and_ceiling_hold() -> None:
    s = _scorer()
    floored = s.score(
        r_multiple=-100.0, status="TIME_STOP", spread_at_entry_pct=0.50,
        debate_confidence=0.0, score_before=2.0,
    )
    capped = s.score(
        r_multiple=100.0, status="CLOSED_BY_BROKER", spread_at_entry_pct=0.01,
        debate_confidence=100.0, score_before=99.0,
    )
    assert floored.score_after >= 0.0          # never negative
    assert capped.score_after <= 100.0         # never above 100


def test_per_trade_delta_cap_independent_of_score_bounds() -> None:
    # Away from the [0,100] bounds, the magnitude moved is exactly the capped delta.
    cfg = RewardConfig()
    s = Scorer(cfg)
    r = s.score(
        r_multiple=50.0, status="CLOSED_BY_BROKER", spread_at_entry_pct=0.01,
        debate_confidence=None, score_before=50.0,
    )
    assert r.score_after - r.score_before == pytest.approx(cfg.max_delta_per_trade)


# --------------------------------------------------------------------------- #
# 3. Outcome component: symmetry, asymmetry, R-clip                            #
# --------------------------------------------------------------------------- #
def test_symmetric_outcome_when_loss_asymmetry_is_one() -> None:
    s = _scorer()  # loss_asymmetry default 1.0
    win = s.score(
        r_multiple=2.0, status="CLOSED_BY_BROKER", spread_at_entry_pct=0.02,
        debate_confidence=None, score_before=50.0,
    )
    loss = s.score(
        r_multiple=-2.0, status="CLOSED_BY_BROKER", spread_at_entry_pct=0.02,
        debate_confidence=None, score_before=50.0,
    )
    assert win.outcome_delta == pytest.approx(-loss.outcome_delta)


def test_loss_asymmetry_makes_losses_bite_harder() -> None:
    s = _scorer(loss_asymmetry=2.0)
    win = s.score(
        r_multiple=2.0, status="CLOSED_BY_BROKER", spread_at_entry_pct=0.02,
        debate_confidence=None, score_before=50.0,
    )
    loss = s.score(
        r_multiple=-2.0, status="CLOSED_BY_BROKER", spread_at_entry_pct=0.02,
        debate_confidence=None, score_before=50.0,
    )
    assert abs(loss.outcome_delta) > abs(win.outcome_delta)
    assert abs(loss.outcome_delta) == pytest.approx(2.0 * abs(win.outcome_delta))


def test_r_multiple_is_clipped_for_scoring() -> None:
    # Beyond r_clip the outcome component saturates: r=10 scores like r=r_clip.
    cfg = RewardConfig()
    s = Scorer(cfg)
    at_clip = s.score(
        r_multiple=cfg.r_clip, status="CLOSED_BY_BROKER", spread_at_entry_pct=0.02,
        debate_confidence=None, score_before=50.0,
    )
    beyond = s.score(
        r_multiple=10.0 * cfg.r_clip, status="CLOSED_BY_BROKER",
        spread_at_entry_pct=0.02, debate_confidence=None, score_before=50.0,
    )
    assert at_clip.outcome_delta == pytest.approx(beyond.outcome_delta)
    assert at_clip.outcome_delta == pytest.approx(cfg.outcome_weight * cfg.r_clip)


# --------------------------------------------------------------------------- #
# 4. win_loss classification                                                   #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "r_multiple, expected",
    [(1.5, "WIN"), (-1.5, "LOSS"), (0.0, "BREAKEVEN")],
)
def test_win_loss_classification(r_multiple: float, expected: str) -> None:
    s = _scorer()
    r = s.score(
        r_multiple=r_multiple, status="CLOSED_BY_BROKER", spread_at_entry_pct=0.02,
        debate_confidence=None, score_before=50.0,
    )
    assert r.win_loss == expected


# --------------------------------------------------------------------------- #
# 5. Individual process signals: exit status, entry spread                     #
# --------------------------------------------------------------------------- #
def test_clean_exit_vs_time_stop_differ_by_expected_amount() -> None:
    # The exit signal flips sign between the two statuses: the process_delta gap is
    # exactly 2 * process_weight * clean_exit_bonus (entry/debate held equal).
    cfg = RewardConfig()
    s = Scorer(cfg)
    broker = s.score(
        r_multiple=0.0, status="CLOSED_BY_BROKER", spread_at_entry_pct=0.20,
        debate_confidence=None, score_before=50.0,
    )
    time_stop = s.score(
        r_multiple=0.0, status="TIME_STOP", spread_at_entry_pct=0.20,
        debate_confidence=None, score_before=50.0,
    )
    gap = broker.process_delta - time_stop.process_delta
    assert gap == pytest.approx(2.0 * cfg.process_weight * cfg.clean_exit_bonus)


def test_tight_entry_spread_earns_a_process_bonus() -> None:
    cfg = RewardConfig()
    s = Scorer(cfg)
    tight = s.score(
        r_multiple=0.0, status="CLOSED_BY_BROKER",
        spread_at_entry_pct=cfg.tight_spread_pct, debate_confidence=None,
        score_before=50.0,
    )
    wide = s.score(
        r_multiple=0.0, status="CLOSED_BY_BROKER",
        spread_at_entry_pct=cfg.tight_spread_pct + 0.05, debate_confidence=None,
        score_before=50.0,
    )
    gap = tight.process_delta - wide.process_delta
    assert gap == pytest.approx(cfg.process_weight * cfg.clean_exit_bonus)


# --------------------------------------------------------------------------- #
# 6. debate_confidence: a weak, additive signal — never a multiplier           #
# --------------------------------------------------------------------------- #
def test_debate_confidence_is_weak_and_not_a_multiplier() -> None:
    cfg = RewardConfig()
    s = Scorer(cfg)
    none = s.score(
        r_multiple=1.0, status="CLOSED_BY_BROKER", spread_at_entry_pct=0.02,
        debate_confidence=None, score_before=50.0,
    )
    high = s.score(
        r_multiple=1.0, status="CLOSED_BY_BROKER", spread_at_entry_pct=0.02,
        debate_confidence=90.0, score_before=50.0,
    )
    # Not a multiplier: the outcome component is untouched by debate confidence.
    assert high.outcome_delta == pytest.approx(none.outcome_delta)
    # Weak: the process shift stays within ±0.5 of a unit signal (× process_weight).
    shift = abs(high.process_delta - none.process_delta)
    assert shift <= 0.5 * cfg.process_weight + 1e-9


def test_debate_confidence_extremes_are_centred_at_half() -> None:
    # debate_confidence is 0-100 (DebateOutcome.confidence scale, Phase-10 B2-fix):
    # 100 nudges up, 0 nudges down, by symmetric amounts around the 50 (centred) baseline.
    s = _scorer()
    base = s.score(
        r_multiple=1.0, status="CLOSED_BY_BROKER", spread_at_entry_pct=0.02,
        debate_confidence=50.0, score_before=50.0,
    )
    up = s.score(
        r_multiple=1.0, status="CLOSED_BY_BROKER", spread_at_entry_pct=0.02,
        debate_confidence=100.0, score_before=50.0,
    )
    down = s.score(
        r_multiple=1.0, status="CLOSED_BY_BROKER", spread_at_entry_pct=0.02,
        debate_confidence=0.0, score_before=50.0,
    )
    assert up.process_delta > base.process_delta > down.process_delta
    assert (up.process_delta - base.process_delta) == pytest.approx(
        base.process_delta - down.process_delta
    )


def test_debate_confidence_scale_is_0_to_100_not_a_fraction() -> None:
    # Phase-10 B2-fix regression pin (2026-07-31): the live bug fed the real 0-100
    # DebateOutcome.confidence straight into a formula written for [0, 1], turning a
    # confidence of 60 into a process_delta of +59.5 (clamped to +5.0 total, on EVERY
    # trade regardless of outcome — a total_delta hardcoded well below the cap proves
    # the scale bug is fixed). Trade shape mirrors the review's Trade-7 regression:
    # a near-total loss with debate_confidence=60.0 must NOT clamp to the cap.
    cfg = RewardConfig()
    s = Scorer(cfg)
    r = s.score(
        r_multiple=-0.975, status="CLOSED_BY_BROKER", spread_at_entry_pct=0.02,
        debate_confidence=60.0, score_before=65.0,
    )
    applied_delta = r.score_after - r.score_before
    assert applied_delta < cfg.max_delta_per_trade - 1.0  # not clamped to the cap
    assert r.score_after < 68.0  # a near-total loss must not push the score up ~5


# --------------------------------------------------------------------------- #
# 7. Result plumbing: raw R, score_before passthrough, exact arithmetic        #
# --------------------------------------------------------------------------- #
def test_result_carries_raw_unclipped_r_multiple() -> None:
    s = _scorer()
    r = s.score(
        r_multiple=10.0, status="CLOSED_BY_BROKER", spread_at_entry_pct=0.02,
        debate_confidence=None, score_before=50.0,
    )
    assert isinstance(r, RewardResult)
    assert r.r_multiple == 10.0  # raw input, even though scoring clipped it


def test_score_before_passthrough_and_exact_after() -> None:
    # A no-clamp case: verify the full arithmetic end to end.
    cfg = RewardConfig()
    s = Scorer(cfg)
    r = s.score(
        r_multiple=0.5, status="CLOSED_BY_BROKER", spread_at_entry_pct=0.02,
        debate_confidence=None, score_before=40.0,
    )
    expected_outcome = cfg.outcome_weight * 0.5            # 1.0
    expected_process = cfg.process_weight * (cfg.clean_exit_bonus + cfg.clean_exit_bonus)  # 3.0
    expected_total = expected_outcome + expected_process   # 4.0 (< cap 5.0)
    assert r.score_before == 40.0
    assert r.outcome_delta == pytest.approx(expected_outcome)
    assert r.process_delta == pytest.approx(expected_process)
    assert r.score_after == pytest.approx(40.0 + expected_total)


# --------------------------------------------------------------------------- #
# 8. Phase-15 Block B — Invariante P1: ein Verlust darf den Score niemals heben
# --------------------------------------------------------------------------- #
# Phase 15 / Block B / Step B1 — die Invariante als Test VOR dem Fix (Plan §6
# Block B B1; AK5). Belegt den Plan-Befund §3 B1 (Reward-Loop belohnt Verluste):
# bei ``r_multiple = -1.0`` muss ``score_after < score_before`` gelten für JEDE
# Kombination der drei Prozess-Signale. Vor B2 (``process_weight: 1.5 → 0.5``)
# ist dieser Test **ROT** (6/24 Fälle verletzen die Invariante — gemessen
# 2026-09-02, MiniMax-M3-Exec-Session #7); nach B2 GRÜN (0/24).
#
# ``score_before = 50.0`` ist absichtlich **nicht** am Floor (Plan §8: ein
# tiefer ``score_before`` würde den Floor-Clamp auf 0.0 triggern und das
# Vorzeichen der Verletzung verschleiern — der Test wäre dann fälschlich
# grün). 50.0 liegt mitten im [0, 100]-Clamp-Bereich und lässt die Verletzung
# ungefiltert durchschlagen.
#
# Parametrisierung folgt Plan §6 Block B B1 verbatim: 3 × 2 × 4 = 24 Fälle.
@pytest.mark.parametrize(
    "status",
    ["CLOSED_BY_BROKER", "TIME_STOP", "OTHER"],
)
@pytest.mark.parametrize(
    "spread_label,spread_at_entry_pct",
    [("tight", 0.02), ("wide", 0.20)],
)
@pytest.mark.parametrize(
    "debate_confidence",
    [None, 0, 50, 100],
)
def test_a_full_stop_loss_never_raises_the_score(
    status: str,
    spread_label: str,
    spread_at_entry_pct: float,
    debate_confidence: int | None,
) -> None:
    s = _scorer()
    r = s.score(
        r_multiple=-1.0,
        status=status,
        spread_at_entry_pct=spread_at_entry_pct,
        debate_confidence=debate_confidence,
        score_before=50.0,
    )
    assert r.score_after < r.score_before, (
        f"Invariante P1 verletzt: r_multiple=-1.0 hebt den Score "
        f"({r.score_before} → {r.score_after}). "
        f"status={status}, spread={spread_label} ({spread_at_entry_pct}), "
        f"debate_confidence={debate_confidence}. "
        f"outcome_delta={r.outcome_delta:+.3f}, process_delta={r.process_delta:+.3f}."
    )
