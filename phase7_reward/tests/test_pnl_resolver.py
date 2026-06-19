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
