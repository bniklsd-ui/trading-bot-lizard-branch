"""Tests for ``reward.pnl_resolver`` (concept §6 Step 9) — deterministic, mocked.

The resolver turns a closed trade into ``(close_level, profit_loss, r_multiple)`` by
matching it against ``broker.get_trade_history`` — **heuristically**, because the IG
history record carries **no ``deal_id``** (verified-contract 1.1): ``epic`` is the
instrument *display name* (not the epic code) and ``direction`` is hardcoded ``None``,
so neither can be the match key. The match is therefore size + open-level proximity,
tie-broken by recency. No usable match ⇒ ``PnLUnavailable`` (fail-closed, Decision J;
the level-approx fallback is intentionally dropped in v1 — operator decision — because
a ``ClosedTrade`` has no ``close_level`` to approximate from).
"""

from __future__ import annotations

import pytest

from reward.models import PnLUnavailable, RewardConfig
from reward.pnl_resolver import resolve
from tests.conftest import FakeBroker, make_tx

CFG = RewardConfig()


def test_exact_single_match_returns_levels_and_r_multiple(make_closed, make_opened):
    """One matching history row → (close_level, profit_loss, r = pl / initial_risk)."""
    opened = make_opened(size=1.0, intended_open_level=18000.0, initial_risk=30.0)
    closed = make_closed()
    broker = FakeBroker([make_tx(close_level=18030.0, profit_loss=30.0)])

    close_level, profit_loss, r_multiple = resolve(closed, broker, opened, CFG)

    assert close_level == 18030.0
    assert profit_loss == 30.0
    assert r_multiple == pytest.approx(1.0)  # 30 / 30
    assert broker.history_calls == 1


def test_match_ignores_epic_and_direction(make_closed, make_opened):
    """The matched row need not share epic/direction — proves heuristic, not deal-id."""
    opened = make_opened(epic="IX.D.DAX.IFMM.IP", direction="BUY",
                         size=2.0, intended_open_level=18000.0, initial_risk=60.0)
    closed = make_closed()
    # Wrong-looking epic string + None direction, but the size+level match is ours.
    broker = FakeBroker([
        make_tx(epic="Totally Different Name", direction=None,
                size=2.0, open_level=18000.0, close_level=18060.0, profit_loss=60.0),
    ])

    _, profit_loss, r_multiple = resolve(closed, broker, opened, CFG)

    assert profit_loss == 60.0
    assert r_multiple == pytest.approx(1.0)


def test_disambiguates_by_open_level_proximity(make_closed, make_opened):
    """Two same-size rows → the one nearest ``intended_open_level`` wins."""
    opened = make_opened(size=1.0, intended_open_level=18000.0, initial_risk=30.0)
    closed = make_closed()
    broker = FakeBroker([
        make_tx(open_level=18100.0, close_level=18130.0, profit_loss=30.0),  # not ours
        make_tx(open_level=18000.0, close_level=17985.0, profit_loss=-15.0),  # ours
    ])

    close_level, profit_loss, r_multiple = resolve(closed, broker, opened, CFG)

    assert close_level == 17985.0
    assert profit_loss == -15.0
    assert r_multiple == pytest.approx(-0.5)  # -15 / 30


def test_level_tie_broken_by_recency(make_closed, make_opened):
    """Same size and open level → the most recent close_date wins (the just-closed one)."""
    opened = make_opened(size=1.0, intended_open_level=18000.0, initial_risk=30.0)
    closed = make_closed()
    broker = FakeBroker([
        make_tx(open_level=18000.0, close_level=18010.0, profit_loss=10.0,
                close_date="2026-06-10T12:00:00"),  # older
        make_tx(open_level=18000.0, close_level=18030.0, profit_loss=30.0,
                close_date="2026-06-19T15:30:00"),  # most recent → ours
    ])

    _, profit_loss, _ = resolve(closed, broker, opened, CFG)

    assert profit_loss == 30.0


def test_buy_win_positive_r(make_closed, make_opened):
    """A winning trade → positive R (P&L sign already carried by IG)."""
    opened = make_opened(size=1.0, intended_open_level=18000.0, initial_risk=30.0)
    broker = FakeBroker([make_tx(profit_loss=45.0, close_level=18045.0)])
    _, _, r = resolve(make_closed(), broker, opened, CFG)
    assert r == pytest.approx(1.5)


def test_sell_loss_negative_r(make_closed, make_opened):
    """A losing trade → negative R; no per-direction sign flip is needed."""
    opened = make_opened(direction="SELL", size=1.0, intended_open_level=18000.0,
                         initial_risk=30.0)
    broker = FakeBroker([make_tx(profit_loss=-30.0, close_level=18030.0)])
    _, profit_loss, r = resolve(make_closed(status="TIME_STOP"), broker, opened, CFG)
    assert profit_loss == -30.0
    assert r == pytest.approx(-1.0)


def test_zero_initial_risk_is_defensive_no_raise(make_closed, make_opened):
    """``initial_risk == 0`` → r=0.0 (no ZeroDivision); the match still resolves."""
    opened = make_opened(size=1.0, intended_open_level=18000.0, initial_risk=0.0)
    broker = FakeBroker([make_tx(profit_loss=12.0, close_level=18012.0)])

    close_level, profit_loss, r = resolve(make_closed(), broker, opened, CFG)

    assert close_level == 18012.0
    assert profit_loss == 12.0
    assert r == 0.0


def test_not_ok_envelope_raises_pnl_unavailable(make_closed, make_opened):
    """A not-ok history envelope ⇒ PnLUnavailable (never guess)."""
    broker = FakeBroker(ok=False)
    with pytest.raises(PnLUnavailable):
        resolve(make_closed(), broker, make_opened(), CFG)


def test_no_matching_row_raises_pnl_unavailable(make_closed, make_opened):
    """No size-matching row (IG lag) ⇒ PnLUnavailable → idempotent retry later."""
    opened = make_opened(size=1.0, intended_open_level=18000.0, initial_risk=30.0)
    broker = FakeBroker([make_tx(size=5.0)])  # different size → not a candidate
    with pytest.raises(PnLUnavailable):
        resolve(make_closed(), broker, opened, CFG)


def test_empty_history_raises_pnl_unavailable(make_closed, make_opened):
    """No transactions at all ⇒ PnLUnavailable."""
    broker = FakeBroker([])
    with pytest.raises(PnLUnavailable):
        resolve(make_closed(), broker, make_opened(), CFG)


def test_unusable_match_missing_pnl_raises(make_closed, make_opened):
    """A size+level match with no usable profit_loss is not a match ⇒ PnLUnavailable."""
    opened = make_opened(size=1.0, intended_open_level=18000.0, initial_risk=30.0)
    broker = FakeBroker([make_tx(profit_loss=None, close_level=None)])
    with pytest.raises(PnLUnavailable):
        resolve(make_closed(), broker, opened, CFG)


def test_raises_pnl_unavailable_carries_code(make_closed, make_opened):
    """The exception is the typed P7 one (catchable by the recorder via its code)."""
    broker = FakeBroker([])
    try:
        resolve(make_closed(), broker, make_opened(), CFG)
    except PnLUnavailable as exc:
        assert exc.code == "PNL_UNAVAILABLE"
    else:  # pragma: no cover - the call above must raise
        pytest.fail("expected PnLUnavailable")


def test_close_confirm_profit_is_used_directly_no_broker_call(make_closed, make_opened):
    """A ClosedTrade carrying realised profit_loss resolves lag-free — no history call
    (the IG-demo transaction ledger only books after settlement, 2026-06-23)."""
    opened = make_opened(size=19.6, intended_open_level=24968.9, initial_risk=588.0)
    closed = make_closed(status="TIME_STOP", close_level=24990.0, profit_loss=42.0)
    broker = FakeBroker([])  # empty history would raise PnLUnavailable if reached

    close_level, profit_loss, r = resolve(closed, broker, opened, CFG)

    assert close_level == 24990.0
    assert profit_loss == pytest.approx(42.0)
    assert r == pytest.approx(42.0 / 588.0)
    assert broker.history_calls == 0


def test_close_level_without_profit_computes_from_levels_buy(make_closed, make_opened):
    """close_level present, no profit → P&L = (close-open)·size·point_value (+ for BUY)."""
    opened = make_opened(direction="BUY", size=2.0, intended_open_level=24000.0, initial_risk=60.0)
    closed = make_closed(close_level=24015.0, profit_loss=None)
    broker = FakeBroker([])

    close_level, profit_loss, r = resolve(closed, broker, opened, CFG)

    assert close_level == 24015.0
    assert profit_loss == pytest.approx((24015.0 - 24000.0) * 2.0 * CFG.point_value)  # +30
    assert r == pytest.approx(0.5)
    assert broker.history_calls == 0


def test_close_level_without_profit_sell_direction_sign(make_closed, make_opened):
    """SELL gains as price falls → the sign comes from direction, not the level delta."""
    opened = make_opened(direction="SELL", size=1.0, intended_open_level=24000.0, initial_risk=30.0)
    closed = make_closed(close_level=23970.0, profit_loss=None)

    _, profit_loss, r = resolve(closed, FakeBroker([]), opened, CFG)

    assert profit_loss == pytest.approx(30.0)  # (24000-23970)*1*1
    assert r == pytest.approx(1.0)


def test_signed_history_size_matches_by_magnitude(make_closed, make_opened):
    """IG signs the history ``size`` (``-19.8`` for a SELL); the magnitude match still
    finds it. A signed compare silently rejected every SELL forever (live-debug
    2026-06-23, deal DIAAAAXTGBTEYAC). ``OpenedTrade.size`` stays unsigned."""
    opened = make_opened(direction="SELL", size=19.8, intended_open_level=24874.9,
                         initial_risk=594.0)
    broker = FakeBroker([
        make_tx(size=-19.8, open_level=24874.9, close_level=24904.9, profit_loss=-99.0),
    ])

    close_level, profit_loss, r = resolve(make_closed(status="TIME_STOP"), broker, opened, CFG)

    assert close_level == 24904.9
    assert profit_loss == -99.0  # sign carried by IG's profit_loss, not by size
    assert r == pytest.approx(-99.0 / 594.0)
