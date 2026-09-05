"""Step 5 — the 5 hard VETOs + ``pre_trade_check`` orchestrator (Phase 15 C3 added VETO 5).

All mocked, no network, no real order/credentials. Envelopes are the duck-typed
``_FakeEnv``; VETO 3 reads bars from a ``FakeBroker`` (``make_bars`` builds the
``get_ohlcv`` bar dicts). ``now`` is a fixed in-window timestamp.

**VETO 5** (``longterm_pre_trade_check``) takes the already-built candidate dict
plus ``config.longterm_rules`` (a tuple of ``Callable[[dict], bool]``). Empty tuple
by default ⇒ inactive ⇒ bit-identical to pre-C3 (Phase 15 AK9). The rule predicates
travel through ``ExecutionConfig`` — Phase 5 never imports ``phase15_v4``.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from execution.config import ExecutionConfig
from execution.vetos import (
    longterm_pre_trade_check,
    pre_trade_check,
    veto_momentum,
    veto_position_conflict,
    veto_spread,
    veto_status_and_window,
)
from typing import Any, Callable

from tests.conftest import DEFAULT_EPIC, FakeBroker, _FakeEnv, make_bars


@pytest.fixture
def config() -> ExecutionConfig:
    return ExecutionConfig()


# A weekday 09:05 Europe/Berlin — comfortably inside the 09:00-17:30 window.
NOW_IN_WINDOW = datetime(2026, 6, 11, 9, 5, tzinfo=ZoneInfo("Europe/Berlin"))
NOW_OUT_OF_WINDOW = datetime(2026, 6, 11, 8, 0, tzinfo=ZoneInfo("Europe/Berlin"))


def _price(*, status: str = "TRADEABLE", spread_pct: float = 0.03, ok: bool = True) -> _FakeEnv:
    return _FakeEnv(
        ok=ok,
        data={"ask": 18000.0, "bid": 17999.0, "spread_pct": spread_pct, "market_status": status},
    )


def _positions(positions: list[dict] | None = None, *, ok: bool = True) -> _FakeEnv:
    return _FakeEnv(ok=ok, data={"positions": positions or []})


# --- VETO 1: status & window ----------------------------------------------


def test_veto_status_window_passes(config: ExecutionConfig) -> None:
    v = veto_status_and_window(_price(), NOW_IN_WINDOW, config)
    assert v.ok


def test_veto_status_window_vetoes_non_tradeable(config: ExecutionConfig) -> None:
    v = veto_status_and_window(_price(status="EDITS_ONLY"), NOW_IN_WINDOW, config)
    assert not v.ok and v.veto == "status_window"


def test_veto_status_window_vetoes_outside_window(config: ExecutionConfig) -> None:
    v = veto_status_and_window(_price(), NOW_OUT_OF_WINDOW, config)
    assert not v.ok and "window" in v.reason


def test_veto_status_window_vetoes_not_ok_env(config: ExecutionConfig) -> None:
    v = veto_status_and_window(_FakeEnv(ok=False), NOW_IN_WINDOW, config)
    assert not v.ok and v.reason == "price snapshot unavailable"


# --- VETO 2: spread --------------------------------------------------------


def test_veto_spread_passes_within_max(config: ExecutionConfig) -> None:
    v = veto_spread(_price(spread_pct=0.5), config)  # exactly at max → pass
    assert v.ok


def test_veto_spread_vetoes_above_max(config: ExecutionConfig) -> None:
    v = veto_spread(_price(spread_pct=0.6), config)
    assert not v.ok and v.veto == "spread"


def test_veto_spread_vetoes_not_ok_env(config: ExecutionConfig) -> None:
    v = veto_spread(_FakeEnv(ok=False), config)
    assert not v.ok


# --- VETO 3: momentum (get_ohlcv) -----------------------------------------


def test_veto_momentum_vetoes_buy_into_drop(config: ExecutionConfig) -> None:
    # 18000 -> 17950 = -0.278% <= -0.15% threshold
    broker = FakeBroker(ohlcv_env=_FakeEnv(ok=True, data={"bars": make_bars([18000.0, 17950.0])}))
    v = veto_momentum(broker, DEFAULT_EPIC, "BUY", config)
    assert not v.ok and v.veto == "momentum"


def test_veto_momentum_vetoes_sell_into_rally(config: ExecutionConfig) -> None:
    # 18000 -> 18050 = +0.278% >= +0.15% threshold
    broker = FakeBroker(ohlcv_env=_FakeEnv(ok=True, data={"bars": make_bars([18000.0, 18050.0])}))
    v = veto_momentum(broker, DEFAULT_EPIC, "SELL", config)
    assert not v.ok and v.veto == "momentum"


def test_veto_momentum_passes_within_threshold(config: ExecutionConfig) -> None:
    # 18000 -> 18010 = +0.056%, below 0.15% — a BUY is fine (not into a drop)
    broker = FakeBroker(ohlcv_env=_FakeEnv(ok=True, data={"bars": make_bars([18000.0, 18010.0])}))
    v = veto_momentum(broker, DEFAULT_EPIC, "BUY", config)
    assert v.ok


def test_veto_momentum_buy_passes_on_rally(config: ExecutionConfig) -> None:
    # A strong rally does NOT veto a BUY (momentum aligned) — only adverse moves veto.
    broker = FakeBroker(ohlcv_env=_FakeEnv(ok=True, data={"bars": make_bars([18000.0, 18100.0])}))
    v = veto_momentum(broker, DEFAULT_EPIC, "BUY", config)
    assert v.ok


def test_veto_momentum_vetoes_too_few_bars(config: ExecutionConfig) -> None:
    broker = FakeBroker(ohlcv_env=_FakeEnv(ok=True, data={"bars": make_bars([18000.0])}))
    v = veto_momentum(broker, DEFAULT_EPIC, "BUY", config)
    assert not v.ok and "too few bars" in v.reason


def test_veto_momentum_vetoes_not_ok_env(config: ExecutionConfig) -> None:
    broker = FakeBroker(ohlcv_env=_FakeEnv(ok=False))
    v = veto_momentum(broker, DEFAULT_EPIC, "BUY", config)
    assert not v.ok and v.reason == "ohlcv snapshot unavailable"


def test_veto_momentum_vetoes_on_raise(config: ExecutionConfig) -> None:
    broker = FakeBroker(ohlcv_raises=True)
    v = veto_momentum(broker, DEFAULT_EPIC, "BUY", config)
    assert not v.ok and "raised" in v.reason


# --- VETO 4: position conflict --------------------------------------------


def test_veto_position_conflict_vetoes_opposite(
    config: ExecutionConfig, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    candidate = make_candidate(direction="BUY", epic=DEFAULT_EPIC)
    env = _positions([{"epic": DEFAULT_EPIC, "direction": "SELL"}])
    v = veto_position_conflict(env, candidate, config)
    assert not v.ok and v.veto == "position_conflict"


def test_veto_position_conflict_vetoes_at_max_parallel(
    config: ExecutionConfig, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    # max_parallel_positions default 1; one same-direction position fills the cap.
    candidate = make_candidate(direction="BUY", epic=DEFAULT_EPIC)
    env = _positions([{"epic": DEFAULT_EPIC, "direction": "BUY"}])
    v = veto_position_conflict(env, candidate, config)
    assert not v.ok and "max_parallel_positions" in v.reason


def test_veto_position_conflict_passes_when_clear(
    config: ExecutionConfig, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    candidate = make_candidate(direction="BUY", epic=DEFAULT_EPIC)
    v = veto_position_conflict(_positions([]), candidate, config)
    assert v.ok


def test_veto_position_conflict_vetoes_not_ok_env(
    config: ExecutionConfig, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    candidate = make_candidate()
    v = veto_position_conflict(_FakeEnv(ok=False), candidate, config)
    assert not v.ok


# --- pre_trade_check orchestrator -----------------------------------------


def test_pre_trade_check_all_pass(
    config: ExecutionConfig, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    # Default FakeBroker: TRADEABLE, tight spread, flat bars, no positions.
    broker = FakeBroker()
    candidate = make_candidate(direction="BUY", epic=DEFAULT_EPIC)
    v = pre_trade_check(broker, candidate, NOW_IN_WINDOW, config)
    assert v.ok
    # all four fresh snapshots were taken
    assert broker.get_price_calls == [DEFAULT_EPIC]
    assert len(broker.get_ohlcv_calls) == 1
    assert broker.get_open_positions_calls == 1


def test_pre_trade_check_aborts_on_first_fail_before_ohlcv(
    config: ExecutionConfig, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    # A status veto must short-circuit — get_ohlcv / get_open_positions never touched.
    broker = FakeBroker(price_env=_price(status="CLOSED"))
    candidate = make_candidate(direction="BUY", epic=DEFAULT_EPIC)
    v = pre_trade_check(broker, candidate, NOW_IN_WINDOW, config)
    assert not v.ok and v.veto == "status_window"
    assert broker.get_ohlcv_calls == []
    assert broker.get_open_positions_calls == 0


# --- VETO 5 — longterm_pre_trade_check (Phase 15 Block C Step C3) ----------- #


def test_longterm_pre_trade_check_empty_rules_passes() -> None:
    """Empty rules tuple ⇒ ``ok=True`` (Plan §6 C3 default path, AK9 bit-identical)."""
    v = longterm_pre_trade_check({"epic": "X", "direction": "BUY"}, ())
    assert v.ok is True
    assert v.veto == "longterm"
    assert v.reason == ""


def test_longterm_pre_trade_check_all_rules_pass() -> None:
    """All rules return True ⇒ ``ok=True`` (no short-circuit on success path)."""
    candidate = {"epic": "X", "direction": "BUY"}
    calls: list[dict] = []

    def rule_a(c: dict) -> bool:
        calls.append(c)
        return True

    def rule_b(c: dict) -> bool:
        calls.append(c)
        return True

    v = longterm_pre_trade_check(candidate, (rule_a, rule_b))
    assert v.ok is True
    assert v.veto == "longterm"
    assert v.reason == ""
    # Both rules ran, in order, on the same candidate.
    assert len(calls) == 2
    assert calls[0] is candidate
    assert calls[1] is candidate


def test_longterm_pre_trade_check_first_false_vetoes() -> None:
    """First rule that returns False short-circuits with a precise reason."""
    calls: list[str] = []

    def rule_a(c: dict) -> bool:
        calls.append("a")
        return True

    def rule_b(c: dict) -> bool:
        calls.append("b")
        return False

    def rule_c(c: dict) -> bool:
        calls.append("c")
        return True

    v = longterm_pre_trade_check({}, (rule_a, rule_b, rule_c))
    assert v.ok is False
    assert v.veto == "longterm"
    assert "rule[1]" in v.reason
    # rule_b vetoed ⇒ rule_c never runs (short-circuit).
    assert calls == ["a", "b"]


def test_longterm_pre_trade_check_raising_rule_vetoes() -> None:
    """A rule that raises is **fail-closed**: ok=False with the exception captured."""
    calls: list[str] = []

    def rule_a(c: dict) -> bool:
        calls.append("a")
        return True

    def rule_b(c: dict) -> bool:
        calls.append("b")
        raise RuntimeError("rule-b broken")

    def rule_c(c: dict) -> bool:
        calls.append("c")
        return True

    v = longterm_pre_trade_check({}, (rule_a, rule_b, rule_c))
    assert v.ok is False
    assert v.veto == "longterm"
    assert "rule[1]" in v.reason
    assert "rule-b broken" in v.reason
    # rule_c never runs (short-circuit, same discipline as a returning-False rule).
    assert calls == ["a", "b"]


def test_longterm_pre_trade_check_does_not_mutate_candidate() -> None:
    """The candidate dict is passed read-only — predicates must not mutate it.

    The function does not pass a defensive copy (it's the same object every time);
    the test just confirms no implicit mutation happens inside VETO 5 itself.
    """
    candidate = {"epic": "X", "direction": "BUY", "tags": []}
    snapshot = dict(candidate)
    longterm_pre_trade_check(candidate, (lambda _c: True,))
    assert candidate == snapshot


# --- pre_trade_check + VETO 5 integration (Phase 15 AK9) ------------------ #


def test_pre_trade_check_veto5_empty_rules_is_identity(
    config: ExecutionConfig, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """AK9 (Plan §7): ``pre_trade_check`` with empty ``longterm_rules`` is bit-
    identical to pre-C3 behaviour — passes when the other 4 VETOs pass."""
    broker = FakeBroker()
    candidate = make_candidate(direction="BUY", epic=DEFAULT_EPIC)
    v = pre_trade_check(broker, candidate, NOW_IN_WINDOW, config)
    assert v.ok is True
    # All 4 fresh snapshots still taken (VETO 5 needs nothing extra — no broker, no clock).
    assert broker.get_price_calls == [DEFAULT_EPIC]
    assert len(broker.get_ohlcv_calls) == 1
    assert broker.get_open_positions_calls == 1


def test_pre_trade_check_veto5_short_circuits_after_veto4(
    config: ExecutionConfig, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """VETO 4 fail ⇒ VETO 5 never runs (short-circuit ordering preserved)."""
    broker = FakeBroker(
        positions_env=_FakeEnv(
            ok=True,
            data={"positions": [{"epic": DEFAULT_EPIC, "direction": "SELL"}]},
        )
    )
    candidate = make_candidate(direction="BUY", epic=DEFAULT_EPIC)

    # A rule that would veto if reached — but VETO 4 short-circuits first.
    rule_calls: list[dict] = []

    def rule(c: dict) -> bool:
        rule_calls.append(c)
        return False

    config_longterm = ExecutionConfig(longterm_rules=(rule,))
    v = pre_trade_check(broker, candidate, NOW_IN_WINDOW, config_longterm)
    assert v.ok is False
    assert v.veto == "position_conflict"
    # VETO 5 must NOT have been evaluated.
    assert rule_calls == []


def test_pre_trade_check_veto5_vetoes_when_rule_returns_false(
    config: ExecutionConfig, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """All other 4 VETOs pass + VETO 5 rule returns False ⇒ ``veto="longterm"``,
    short-circuits the pre_trade_check before the final ok=True return."""
    broker = FakeBroker()
    candidate = make_candidate(direction="BUY", epic=DEFAULT_EPIC)

    def always_veto(_c: dict) -> bool:
        return False

    config_with_rule = ExecutionConfig(longterm_rules=(always_veto,))
    v = pre_trade_check(broker, candidate, NOW_IN_WINDOW, config_with_rule)
    assert v.ok is False
    assert v.veto == "longterm"
    assert "rule[0]" in v.reason


def test_pre_trade_check_veto5_passes_when_all_rules_pass(
    config: ExecutionConfig, make_candidate: Callable[..., dict[str, Any]]
) -> None:
    """All 4 VETOs pass + all 5 VETO-5 rules pass ⇒ ``ok=True`` (the pre-C3
    success path, with the new layer active)."""
    broker = FakeBroker()
    candidate = make_candidate(direction="BUY", epic=DEFAULT_EPIC)

    def rule_a(_c: dict) -> bool:
        return True

    def rule_b(_c: dict) -> bool:
        return True

    config_with_rules = ExecutionConfig(longterm_rules=(rule_a, rule_b))
    v = pre_trade_check(broker, candidate, NOW_IN_WINDOW, config_with_rules)
    assert v.ok is True
    assert v.veto == "pre_trade_check"


# --- ExecutionConfig.longterm_rules default invariants -------------------- #


def test_longterm_rules_default_is_empty_tuple_not_list() -> None:
    """Mutable-default trap guard (Plan §8): default must be ``tuple``, not ``list``
    — a shared mutable default would let one instance's rules leak into another."""
    cfg = ExecutionConfig()
    assert cfg.longterm_rules == ()
    assert isinstance(cfg.longterm_rules, tuple)


def test_longterm_rules_is_frozen_via_config() -> None:
    """``ExecutionConfig`` is ``frozen=True`` → ``longterm_rules`` is immutable
    at the config level; replacing it requires a new config instance."""
    cfg = ExecutionConfig()
    with pytest.raises(Exception):  # FrozenInstanceError
        cfg.longterm_rules = (lambda _c: True,)  # type: ignore[misc]


def test_longterm_rules_supports_arbitrary_callables() -> None:
    """Type is ``tuple[Any, ...]`` — any callable signature is accepted. The
    discipline (single-arg predicate returning bool) is the wiring's
    responsibility, not the config's."""
    cfg = ExecutionConfig(longterm_rules=(lambda _c: True, lambda _c: False))
    assert len(cfg.longterm_rules) == 2
    assert all(callable(r) for r in cfg.longterm_rules)
