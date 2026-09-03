"""Tests for the Phase-7 data contracts (Step 3).

Types only — these assert the frozen field set, the §5 ``RewardConfig`` defaults,
the exception hierarchy + codes, and the advisory/observe-only role of confidence.
No network, no real LLM, no logic exercised (there is none in ``models.py``).
"""

from __future__ import annotations

import dataclasses

import pytest

from reward.models import (
    ClosedTrade,
    ConfidenceReport,
    LessonResult,
    OpenedTrade,
    PnLUnavailable,
    RewardConfig,
    RewardError,
    RewardResult,
)


# --------------------------------------------------------------------------- #
# helpers                                                                      #
# --------------------------------------------------------------------------- #
def _opened(**over: object) -> OpenedTrade:
    base = dict(
        deal_reference="bot-deadbeef",
        deal_id="DIAAAAXQ6CSGTA5",
        epic="IX.D.DAX.IFMM.IP",
        direction="BUY",
        size=0.5,
        intended_open_level=18000.0,
        stop_level=17970.0,
        limit_level=18045.0,
        currency="EUR",
        initial_risk=15.0,
        research_confidence=70.0,
        debate_confidence=66.0,
        gate_path={"gate_1": "pass", "gate_2": "pass"},
        spread_at_entry_pct=0.02,
        score_at_open=50.0,
        session_date="2026-06-18",
        open_ts="2026-06-18T08:00:00.000Z",
        account="demo",
    )
    base.update(over)
    return OpenedTrade(**base)  # type: ignore[arg-type]


def _closed(**over: object) -> ClosedTrade:
    base = dict(
        deal_reference="bot-deadbeef",
        deal_id="DIAAAAXQ6CSGTA5",
        status="CLOSED_BY_BROKER",
        closed_at="2026-06-18T08:05:00.000Z",
    )
    base.update(over)
    return ClosedTrade(**base)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# 1. RewardConfig defaults match the locked §5 table                          #
# --------------------------------------------------------------------------- #
def test_reward_config_defaults_match_concept_section_5() -> None:
    cfg = RewardConfig()
    # confidence (Decision C)
    assert cfg.n_min == 10
    assert cfg.wilson_z == 1.96
    assert cfg.point_value == 1.0
    # scoring bounds & shape (Decision B2/D)
    assert cfg.score_min == 0.0
    assert cfg.score_max == 100.0
    assert cfg.max_delta_per_trade == 5.0
    assert cfg.outcome_weight == 2.0
    assert cfg.r_clip == 3.0
    assert cfg.process_weight == 0.5  # korrigiert 2026-09-03 (Phase-15-B-B2): war 1.5, gesenkt für Invariante P1/P2 (Plan §6 Block B)
    assert cfg.loss_asymmetry == 1.0
    assert cfg.tight_spread_pct == 0.05
    assert cfg.clean_exit_bonus == 1.0
    # lesson extraction (Decision E)
    assert cfg.lesson_model == "claude-haiku-4-5-20251001"
    assert cfg.lesson_max_tokens == 400
    assert cfg.lesson_temperature == 0.3
    assert cfg.lesson_timeout_s == 20.0
    # bootstrap / data separation (Decision H)
    assert cfg.include_demo_in_edge is True
    assert cfg.synthetic_db_path == "data/synthetic_reward.db"


def test_reward_config_live_db_path_is_the_real_p2_sqlite_path() -> None:
    # Verified-contract 1.7: the real Phase-2 DB is data/trading_bot.sqlite, NOT
    # the concept §5 string data/trading_bot.db. Code = source of truth.
    assert RewardConfig().live_db_path == "data/trading_bot.sqlite"


def test_reward_config_is_frozen() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        RewardConfig().n_min = 5  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# 2. OpenedTrade — construct/read-back, optional debate_confidence, frozen     #
# --------------------------------------------------------------------------- #
def test_opened_trade_constructs_and_reads_back() -> None:
    o = _opened()
    assert o.direction == "BUY"
    assert o.account == "demo"
    assert o.deal_reference.startswith("bot-")
    assert o.gate_path["gate_1"] == "pass"
    assert o.debate_confidence == 66.0


def test_opened_trade_allows_none_debate_confidence() -> None:
    # debate_confidence is None when no debate ran (verified-contract 1.3).
    assert _opened(debate_confidence=None).debate_confidence is None


def test_opened_trade_provenance_defaults_autonomous() -> None:
    # v1.5 (Step 4 A): the field is additive with a default so every existing construction
    # (which omits it) stays valid; the executor seam sets "verification" only for seeds.
    assert _opened().provenance == "autonomous"
    assert _opened(provenance="verification").provenance == "verification"


def test_opened_trade_initial_risk_matches_documented_formula() -> None:
    # The field only CARRIES the value; the formula is documented for the caller
    # (Step 10). Pin the relationship so the contract is unambiguous:
    #   initial_risk = abs(intended_open_level - stop_level) * size * point_value
    o = _opened(intended_open_level=18000.0, stop_level=17970.0, size=0.5)
    assert o.initial_risk == 15.0  # abs(18000-17970) * 0.5 * 1.0


def test_opened_trade_is_frozen() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        _opened().size = 1.0  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# 3. ClosedTrade — status vocabulary + frozen                                 #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("status", ["CLOSED_BY_BROKER", "TIME_STOP"])
def test_closed_trade_status_vocabulary(status: str) -> None:
    assert _closed(status=status).status == status


def test_closed_trade_is_frozen() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        _closed().status = "TIME_STOP"  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# 4. ConfidenceReport — OK vs INSUFFICIENT; observe-only None on INSUFFICIENT  #
# --------------------------------------------------------------------------- #
def test_confidence_report_ok_shape() -> None:
    r = ConfidenceReport(
        state="OK", n=12, win_rate_raw=0.58, win_rate_wilson_lb=0.33,
        expectancy_r=0.4, sqn=1.1, confidence_value=41.0,
    )
    assert r.state == "OK"
    assert r.confidence_value == 41.0


def test_confidence_report_insufficient_has_none_confidence() -> None:
    # N < n_min → INSUFFICIENT, confidence_value flows into nothing (Decision C).
    r = ConfidenceReport(
        state="INSUFFICIENT", n=9, win_rate_raw=1.0, win_rate_wilson_lb=None,
        expectancy_r=None, sqn=None, confidence_value=None,
    )
    assert r.state == "INSUFFICIENT"
    assert r.confidence_value is None


def test_confidence_report_is_frozen() -> None:
    r = ConfidenceReport(
        state="OK", n=10, win_rate_raw=0.5, win_rate_wilson_lb=0.2,
        expectancy_r=0.1, sqn=None, confidence_value=30.0,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.confidence_value = 99.0  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# 5. RewardResult — win_loss vocabulary + frozen                              #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("win_loss", ["WIN", "LOSS", "BREAKEVEN"])
def test_reward_result_win_loss_vocabulary(win_loss: str) -> None:
    res = RewardResult(
        outcome_delta=2.0, process_delta=0.5, score_before=50.0,
        score_after=52.5, win_loss=win_loss, r_multiple=1.0,
    )
    assert res.win_loss == win_loss
    assert res.score_after == 52.5


def test_reward_result_is_frozen() -> None:
    res = RewardResult(
        outcome_delta=0.0, process_delta=0.0, score_before=50.0,
        score_after=50.0, win_loss="BREAKEVEN", r_multiple=0.0,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        res.score_after = 60.0  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# 6. LessonResult — ok/error shapes (best-effort, never raises)               #
# --------------------------------------------------------------------------- #
def test_lesson_result_ok_carries_text_no_error() -> None:
    lr = LessonResult(
        lesson_text="Avoid BUY into a falling tape.", market_context={"drift": -0.2},
        ok=True, error=None,
    )
    assert lr.ok is True
    assert lr.lesson_text and lr.error is None


def test_lesson_result_failure_carries_error_no_text() -> None:
    # Decision E/J: a failed reflect() yields ok=False, never a raise.
    lr = LessonResult(lesson_text=None, market_context={}, ok=False, error="timeout")
    assert lr.ok is False
    assert lr.lesson_text is None
    assert lr.error == "timeout"


# --------------------------------------------------------------------------- #
# 7. Exception hierarchy + codes                                              #
# --------------------------------------------------------------------------- #
def test_exception_hierarchy_and_codes() -> None:
    assert issubclass(PnLUnavailable, RewardError)
    assert RewardError.code == "REWARD_ERROR"
    assert PnLUnavailable.code == "PNL_UNAVAILABLE"
    assert RewardError.code != PnLUnavailable.code
    # PnLUnavailable is catchable as the base family (fail-closed handling, J).
    with pytest.raises(RewardError):
        raise PnLUnavailable("no history match")
