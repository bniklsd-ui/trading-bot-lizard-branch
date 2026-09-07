"""Tests for ``phase15_v4/instinct/promotion.py`` (Plan §6 C2 + §1 P10/P12).

Pins the AK7 acceptance criterion (P13): **at n=8 closed trades the harness
correctly refuses to promote** — no instinct, of any status, reaches the
returned list while either gate is closed.
"""

from __future__ import annotations

import sys

import pytest

_REPO_ROOT = "/home/trading-bot/trading-bot"
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from instinct.models import Instinct, InstinctConfig  # noqa: E402
from instinct.promotion import promote_eligible  # noqa: E402


def _instinct(status: str, instinct_id: int = 1) -> Instinct:
    """Build a minimal ``Instinct`` row with the given status."""
    return Instinct(
        trigger="t", domain="entry",
        evidence_trade_ids=(1, 2, 3),
        contradictions_trade_ids=(),
        status=status,
        id=instinct_id,
    )


# ---------------------------------------------------------------------------
# AK7 (P13) — the phase-acceptance test: today (n=8, flag=off) → [].
# ---------------------------------------------------------------------------


def test_promotion_refuses_below_n_min() -> None:
    """AK7 (P13): ``n_closed=8 < instinct_n_min=50`` ⇒ ``[]``, regardless of status."""
    instincts = [
        _instinct("proposed"),
        _instinct("validated"),
        _instinct("refuted"),
        _instinct("promoted"),
    ]
    cfg = InstinctConfig(instinct_n_min=50, enable_instinct_promotion=True)
    assert promote_eligible(instincts, n_closed=8, cfg=cfg) == []


def test_promotion_refuses_when_flag_off() -> None:
    """``enable_instinct_promotion=False`` (P10) ⇒ ``[]``, regardless of n_closed."""
    instincts = [_instinct("validated")]
    cfg = InstinctConfig(instinct_n_min=50, enable_instinct_promotion=False)
    assert promote_eligible(instincts, n_closed=999, cfg=cfg) == []


def test_promotion_refuses_when_both_gates_closed() -> None:
    """Both gates closed (the default state) ⇒ ``[]``."""
    cfg = InstinctConfig()  # defaults: n_min=50, flag=False
    assert promote_eligible([_instinct("validated")], n_closed=8, cfg=cfg) == []


def test_promotion_refuses_on_exact_n_min_boundary() -> None:
    """``n_closed == n_min`` ⇒ eligible (the floor is ``>=``, not ``>``).

    With both gates open and validated rows, the function must return them.
    """
    cfg = InstinctConfig(instinct_n_min=50, enable_instinct_promotion=True)
    instincts = [_instinct("validated", instinct_id=1)]
    out = promote_eligible(instincts, n_closed=50, cfg=cfg)
    assert len(out) == 1
    assert out[0].id == 1


def test_promotion_refuses_one_below_n_min() -> None:
    """``n_closed = n_min - 1`` ⇒ ``[]`` (boundary safety)."""
    cfg = InstinctConfig(instinct_n_min=50, enable_instinct_promotion=True)
    assert promote_eligible([_instinct("validated")], n_closed=49, cfg=cfg) == []


# ---------------------------------------------------------------------------
# Status filtering — only ``validated`` rows are eligible (P10).
# ---------------------------------------------------------------------------


def test_promotion_keeps_proposed_status_when_gates_open() -> None:
    """``proposed`` rows are the validator's job — promoter never advances them."""
    cfg = InstinctConfig(instinct_n_min=50, enable_instinct_promotion=True)
    out = promote_eligible(
        [_instinct("proposed", 1), _instinct("validated", 2)],
        n_closed=100,
        cfg=cfg,
    )
    assert len(out) == 1
    assert out[0].id == 2


def test_promotion_keeps_refuted_status_when_gates_open() -> None:
    """``refuted`` rows never promote — they are structurally blocked."""
    cfg = InstinctConfig(instinct_n_min=50, enable_instinct_promotion=True)
    out = promote_eligible(
        [_instinct("refuted", 1), _instinct("validated", 2)],
        n_closed=100,
        cfg=cfg,
    )
    assert len(out) == 1
    assert out[0].id == 2


def test_promotion_keeps_promoted_status_when_gates_open() -> None:
    """``promoted`` rows are already at the VETO layer — not re-promotable."""
    cfg = InstinctConfig(instinct_n_min=50, enable_instinct_promotion=True)
    out = promote_eligible(
        [_instinct("promoted", 1), _instinct("validated", 2)],
        n_closed=100,
        cfg=cfg,
    )
    assert len(out) == 1
    assert out[0].id == 2


def test_promotion_returns_all_validated_when_gates_open() -> None:
    """Multiple ``validated`` rows + gates open ⇒ all returned."""
    cfg = InstinctConfig(instinct_n_min=50, enable_instinct_promotion=True)
    rows = [
        _instinct("validated", 1),
        _instinct("validated", 2),
        _instinct("validated", 3),
    ]
    out = promote_eligible(rows, n_closed=200, cfg=cfg)
    assert [r.id for r in out] == [1, 2, 3]


# ---------------------------------------------------------------------------
# Edge cases.
# ---------------------------------------------------------------------------


def test_promotion_empty_input_returns_empty() -> None:
    """Gates open + empty input ⇒ empty result."""
    cfg = InstinctConfig(instinct_n_min=50, enable_instinct_promotion=True)
    assert promote_eligible([], n_closed=100, cfg=cfg) == []


def test_promotion_does_not_mutate_input() -> None:
    """The input iterable is not consumed twice — passes through a list copy."""
    cfg = InstinctConfig(instinct_n_min=50, enable_instinct_promotion=True)
    rows = [
        _instinct("validated", 1),
        _instinct("refuted", 2),
        _instinct("proposed", 3),
    ]
    out1 = promote_eligible(rows, n_closed=100, cfg=cfg)
    out2 = promote_eligible(rows, n_closed=100, cfg=cfg)
    assert [r.id for r in out1] == [r.id for r in out2] == [1]


def test_promotion_accepts_a_generator_input() -> None:
    """Generators work — the function materialises the iterable internally."""
    cfg = InstinctConfig(instinct_n_min=50, enable_instinct_promotion=True)

    def gen():
        yield _instinct("validated", 1)
        yield _instinct("refuted", 2)
        yield _instinct("validated", 3)

    out = promote_eligible(gen(), n_closed=100, cfg=cfg)
    assert [r.id for r in out] == [1, 3]


def test_promotion_returns_a_list_not_a_generator() -> None:
    """The return type is a concrete ``list`` — callers may index / len it."""
    cfg = InstinctConfig(instinct_n_min=50, enable_instinct_promotion=True)
    out = promote_eligible(
        [_instinct("validated", 1)], n_closed=100, cfg=cfg,
    )
    assert isinstance(out, list)
    assert len(out) == 1
    assert out[0] is not None


# ---------------------------------------------------------------------------
# Sanity — the default Config = the today's live-substrate state.
# ---------------------------------------------------------------------------


def test_promotion_today_state_is_closed() -> None:
    """Sanity probe: the default config + the actual n_closed=8 ⇒ the harness
    returns ``[]`` — the gating the Instinct-ECC harness was built to do.

    This test is redundant with ``test_promotion_refuses_below_n_min`` above
    but it makes the today-state property readable in isolation.
    Phase 16 D1: ``enable_instinct_promotion`` default is now True (Plan §1 P5);
    n_min=50 still gates at n_closed=8 ⇒ no promotion."""
    cfg = InstinctConfig()  # defaults: n_min=50, flag=True (Phase 16 D1)
    assert cfg.instinct_n_min == 50
    assert cfg.enable_instinct_promotion is True
    rows = [_instinct("validated") for _ in range(5)]
    assert promote_eligible(rows, n_closed=8, cfg=cfg) == []
