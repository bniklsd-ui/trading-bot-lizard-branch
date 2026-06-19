"""Tests for the Phase-7 synthetic/live data separation (Step 6, Decision H).

Pure deterministic code: no network, no LLM, no real DB. The headline is the
**path guard** — the phase-gate proof (concept §7 (c)) that a synthetic write can
never hit the live database path. The rest pins the generator's reproducibility/labels
and the ``include_demo_in_edge`` + synthetic-exclusion rule that feeds the edge metric.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from reward.confidence import compute_confidence
from reward.models import RewardConfig, RewardError, SyntheticSafetyError
from reward.synthetic import (
    SyntheticTrade,
    SyntheticTradeGenerator,
    guard_synthetic_path,
    select_edge_set,
)


def _cfg(**overrides: object) -> RewardConfig:
    return RewardConfig(**overrides)


# --------------------------------------------------------------------------- #
# 1. Generator — reproducibility and labels                                    #
# --------------------------------------------------------------------------- #
def test_generator_is_deterministic_for_a_fixed_seed() -> None:
    a = SyntheticTradeGenerator(seed=42).generate(50, win_rate=0.6)
    b = SyntheticTradeGenerator(seed=42).generate(50, win_rate=0.6)
    assert [t.r_multiple for t in a] == [t.r_multiple for t in b]


def test_generator_differs_across_seeds() -> None:
    a = SyntheticTradeGenerator(seed=1).generate(50, win_rate=0.6)
    b = SyntheticTradeGenerator(seed=2).generate(50, win_rate=0.6)
    assert [t.r_multiple for t in a] != [t.r_multiple for t in b]


def test_generator_respects_win_rate_and_labels_consistently() -> None:
    trades = SyntheticTradeGenerator(seed=7).generate(200, win_rate=0.7)
    wins = sum(1 for t in trades if t.r_multiple > 0)
    assert wins / len(trades) == pytest.approx(0.7, abs=0.1)
    # Every trade is tagged synthetic, and win_loss matches the R-multiple's sign.
    for t in trades:
        assert t.synthetic is True
        if t.r_multiple > 0:
            assert t.win_loss == "WIN"
        elif t.r_multiple < 0:
            assert t.win_loss == "LOSS"
        else:
            assert t.win_loss == "BREAKEVEN"


def test_generate_rejects_bad_inputs() -> None:
    gen = SyntheticTradeGenerator(seed=0)
    with pytest.raises(ValueError):
        gen.generate(-1, win_rate=0.5)
    with pytest.raises(ValueError):
        gen.generate(10, win_rate=1.5)


# --------------------------------------------------------------------------- #
# 2. edge_inputs feeds the confidence math end to end                          #
# --------------------------------------------------------------------------- #
def test_edge_inputs_drive_compute_confidence() -> None:
    cfg = _cfg()
    gen = SyntheticTradeGenerator(seed=3)

    enough = gen.generate(cfg.n_min, win_rate=0.6)
    r_multiples, wins, n = SyntheticTradeGenerator.edge_inputs(enough)
    assert n == cfg.n_min and wins == sum(1 for r in r_multiples if r > 0)
    report = compute_confidence(r_multiples, wins, n, cfg)
    assert report.state == "OK"
    assert report.confidence_value is not None

    too_few = gen.generate(cfg.n_min - 1, win_rate=0.6)
    r2, w2, n2 = SyntheticTradeGenerator.edge_inputs(too_few)
    insufficient = compute_confidence(r2, w2, n2, cfg)
    assert insufficient.state == "INSUFFICIENT"
    assert insufficient.confidence_value is None


# --------------------------------------------------------------------------- #
# 3. guard_synthetic_path — THE boundary (phase-gate proof (c))                #
# --------------------------------------------------------------------------- #
def test_guard_raises_on_the_live_db_path(tmp_path: Path) -> None:
    live = tmp_path / "live.sqlite"
    cfg = _cfg(live_db_path=str(live), synthetic_db_path=str(tmp_path / "syn.db"))
    with pytest.raises(SyntheticSafetyError) as exc:
        guard_synthetic_path(cfg.live_db_path, cfg)
    # It is a RewardError subclass carrying a distinct code.
    assert isinstance(exc.value, RewardError)
    assert exc.value.code == "SYNTHETIC_SAFETY"


def test_guard_catches_relative_vs_absolute_aliasing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The live path spelled relatively must still be caught (paths are resolved).
    monkeypatch.chdir(tmp_path)
    cfg = _cfg(live_db_path="data/trading_bot.sqlite")
    aliases = ["data/trading_bot.sqlite", "./data/trading_bot.sqlite",
               str(tmp_path / "data" / "trading_bot.sqlite"),
               "data/../data/trading_bot.sqlite"]
    for alias in aliases:
        with pytest.raises(SyntheticSafetyError):
            guard_synthetic_path(alias, cfg)


def test_guard_returns_resolved_path_when_distinct(tmp_path: Path) -> None:
    live = tmp_path / "live.sqlite"
    syn = tmp_path / "syn.db"
    cfg = _cfg(live_db_path=str(live), synthetic_db_path=str(syn))
    out = guard_synthetic_path(cfg.synthetic_db_path, cfg)
    assert out == str(syn.resolve())


# --------------------------------------------------------------------------- #
# 4. select_edge_set — synthetic exclusion + include_demo_in_edge rule         #
# --------------------------------------------------------------------------- #
def test_select_edge_excludes_synthetic_regardless_of_flag() -> None:
    records = [
        SyntheticTrade(r_multiple=2.0, win_loss="WIN"),          # synthetic=True
        {"r_multiple": 1.0, "account": "live", "synthetic": False},
        {"r_multiple": -1.0, "account": "demo", "synthetic": True},  # synthetic
    ]
    for flag in (True, False):
        r_multiples, wins, n = select_edge_set(records, _cfg(include_demo_in_edge=flag))
        assert n == 1 and r_multiples == [1.0] and wins == 1  # only the live row


def test_select_edge_demo_inclusion_toggles_with_flag() -> None:
    records = [
        {"r_multiple": 1.0, "account": "live", "synthetic": False},
        {"r_multiple": 2.0, "account": "demo", "synthetic": False},
    ]
    incl = select_edge_set(records, _cfg(include_demo_in_edge=True))
    excl = select_edge_set(records, _cfg(include_demo_in_edge=False))
    assert incl == ([1.0, 2.0], 2, 2)   # demo counted
    assert excl == ([1.0], 1, 1)        # demo dropped, live always kept


def test_select_edge_wins_and_n_counting() -> None:
    records = [
        {"r_multiple": 3.0, "account": "live", "synthetic": False},   # win
        {"r_multiple": 0.0, "account": "live", "synthetic": False},   # breakeven, not a win
        {"r_multiple": -2.0, "account": "live", "synthetic": False},  # loss
        {"r_multiple": 9.9, "account": "demo", "synthetic": False},   # dropped when flag off
    ]
    r_multiples, wins, n = select_edge_set(records, _cfg(include_demo_in_edge=False))
    assert n == 3
    assert wins == 1            # only the +3.0; breakeven excluded
    assert r_multiples == [3.0, 0.0, -2.0]
