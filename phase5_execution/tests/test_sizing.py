"""Step 4 — Gate 4 sizing (``select_risk_pct`` + ``compute_size``).

Pure functions; all mocked, no network, no real broker/credentials. Envelopes are
the duck-typed ``_FakeEnv`` from conftest; the risk level comes from ``FakeDB``.

Sizing model (operator decision 2026-06-12): risk-per-trade ÷ stop-distance —
``size = (balance × risk_pct) / (stop_distance_points × point_value)``, capped by
``(balance × max_leverage) / (price × point_value)``, rounded **down** to 0.1.
With the default ``stop_distance_points=30`` and ``point_value=1`` the size is
independent of the index price; round numbers are chosen so it lands exactly on the
0.1 grid (e.g. balance 1500 × 2% / 30 = 1.0).
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from execution.config import ExecutionConfig
from execution.sizing import compute_size, select_risk_pct
from tests.conftest import FakeDB, _FakeEnv


@pytest.fixture
def config() -> ExecutionConfig:
    return ExecutionConfig()


def _account(available: float) -> _FakeEnv:
    return _FakeEnv(ok=True, data={"available": available, "currency": "EUR"})


def _price(ask: float) -> _FakeEnv:
    return _FakeEnv(ok=True, data={"ask": ask, "bid": ask - 1, "market_status": "TRADEABLE"})


def _market_info(min_deal_size: float) -> _FakeEnv:
    return _FakeEnv(ok=True, data={"min_deal_size": min_deal_size, "currency": "EUR"})


# --- select_risk_pct ------------------------------------------------------


def test_select_risk_pct_conservative(config: ExecutionConfig) -> None:
    db = FakeDB(risk_level="KONSERVATIV")
    assert select_risk_pct(db, config) == config.risk_pct_conservative


def test_select_risk_pct_aggressive(config: ExecutionConfig) -> None:
    db = FakeDB(risk_level="AGGRESSIV")
    assert select_risk_pct(db, config) == config.risk_pct_aggressive


# --- compute_size: risk level drives the size -----------------------------


def test_aggressive_risk_pct_sizes_larger_than_conservative(config: ExecutionConfig) -> None:
    # stop=30, pt=1, price=18000 (cap = 1500×20/18000 = 1.66 -> not binding).
    account, price, info = _account(1500), _price(18_000), _market_info(0.1)

    cons_size, cons_reason = compute_size(
        account, price, info, config.risk_pct_conservative, config
    )
    aggr_size, aggr_reason = compute_size(
        account, price, info, config.risk_pct_aggressive, config
    )

    # cons 2% of 1500 / 30 = 1.0 ; aggr 3% of 1500 / 30 = 1.5
    assert (cons_size, cons_reason) == (1.0, None)
    assert (aggr_size, aggr_reason) == (1.5, None)
    assert aggr_size > cons_size


# --- compute_size: round DOWN to 0.1 --------------------------------------


def test_size_rounds_down_to_tenth(config: ExecutionConfig) -> None:
    # 3% of 1370 / 30 = 1.37 -> rounded DOWN to 0.1 step = 1.3
    size, reason = compute_size(
        _account(1370), _price(18_000), _market_info(0.1), 3.0, config
    )
    assert reason is None
    assert size == 1.3


# --- compute_size: ~€1K budget is tradeable (the rework's regression) -----


def test_thousand_euro_budget_is_tradeable(config: ExecutionConfig) -> None:
    # The exact bug this rework fixes: a real ~€1K account must clear min_deal_size.
    # 2% of 1000 / 30 = 0.66 -> 0.6 >= 0.5 (the old notional model rounded to 0.0).
    size, reason = compute_size(
        _account(1000), _price(18_000), _market_info(0.5), config.risk_pct_conservative, config
    )
    assert reason is None
    assert size == 0.6


# --- compute_size: below min_deal_size is a no-trade ----------------------


def test_size_below_min_deal_size_rejects(config: ExecutionConfig) -> None:
    # 2% of 500 / 30 = 0.333 -> 0.3, below a 0.5 min -> no trade
    size, reason = compute_size(
        _account(500), _price(18_000), _market_info(0.5), config.risk_pct_conservative, config
    )
    assert (size, reason) == (0.0, "below_min_deal_size")


def test_size_no_upward_clamp_when_below_min(config: ExecutionConfig) -> None:
    # Never bump a sub-min size up to min_deal_size — it stays a no-trade.
    # 2% of 1500 / 30 = 1.0 computed but min is 5.0 -> rejected, not clamped to 5.0.
    size, reason = compute_size(
        _account(1500), _price(18_000), _market_info(5.0), config.risk_pct_conservative, config
    )
    assert (size, reason) == (0.0, "below_min_deal_size")


# --- compute_size: leverage / notional cap --------------------------------


def test_leverage_cap_clips_oversized_risk() -> None:
    # A tiny stop distance on a large balance would size huge; the notional cap clips it.
    # raw = 3% of 100_000 / 1 = 3000 ; cap = 100_000 × 20 / 18_000 = 111.11 -> 111.1.
    config = replace(ExecutionConfig(), stop_distance_points=1.0)
    size, reason = compute_size(
        _account(100_000), _price(18_000), _market_info(0.1), config.risk_pct_aggressive, config
    )
    assert reason is None
    assert size == 111.1  # capped, NOT the uncapped 3000


# --- compute_size: v1.5 per-epic point value ------------------------------


def test_point_value_scales_size_down() -> None:
    # A €5/pt instrument risks 5× as much per lot, so the same risk budget buys 1/5
    # the size: 2% of 1500 / (30 × 5) = 0.2 (vs 1.0 at point_value 1.0).
    epic = "IX.D.STXE.IFMM.IP"
    config = replace(ExecutionConfig(), point_values={epic: 5.0})
    size, reason = compute_size(
        _account(1500), _price(18_000), _market_info(0.1),
        config.risk_pct_conservative, config, epic=epic,
    )
    assert reason is None
    assert size == 0.2


def test_point_value_default_one_when_epic_unmapped(config: ExecutionConfig) -> None:
    # An epic absent from point_values falls back to 1.0 → identical to the DAX path.
    size, reason = compute_size(
        _account(1500), _price(18_000), _market_info(0.1),
        config.risk_pct_conservative, config, epic="UNMAPPED.EPIC",
    )
    assert (size, reason) == (1.0, None)


def test_point_value_from_market_info_echo_when_epic_arg_omitted() -> None:
    # Back-compat: no epic arg → resolved from the market_info envelope's echoed epic.
    epic = "IX.D.CAC.IFMM.IP"
    config = replace(ExecutionConfig(), point_values={epic: 10.0})
    info = _FakeEnv(ok=True, data={"min_deal_size": 0.1, "currency": "EUR", "epic": epic})
    size, reason = compute_size(
        _account(1500), _price(18_000), info, config.risk_pct_conservative, config
    )
    # 2% of 1500 / (30 × 10) = 0.1
    assert (size, reason) == (0.1, None)


def test_point_value_still_fails_closed_below_min() -> None:
    # A high point value can push the size below min_deal_size → still a no-trade.
    epic = "IX.D.STXE.IFMM.IP"
    config = replace(ExecutionConfig(), point_values={epic: 10.0})
    size, reason = compute_size(
        _account(1000), _price(18_000), _market_info(0.5),
        config.risk_pct_conservative, config, epic=epic,
    )
    # 2% of 1000 / (30 × 10) = 0.066 -> 0.0, below the 0.5 min.
    assert (size, reason) == (0.0, "below_min_deal_size")


def test_point_value_unmapped_epic_fails_closed_when_map_populated() -> None:
    # Phase-10 B1(b)-fix (2026-07-31): once point_values is wired at all (non-empty),
    # an epic absent from it is a real data gap, not a safe 1.0 default — no trade.
    # This is the guard that would have caught the AEX 40x-oversizing incident.
    config = replace(ExecutionConfig(), point_values={"IX.D.STXE.IFMM.IP": 5.0})
    size, reason = compute_size(
        _account(1500), _price(18_000), _market_info(0.1),
        config.risk_pct_conservative, config, epic="IX.D.AEX.IFM.IP",
    )
    assert (size, reason) == (0.0, "point_value_unmapped")


# --- compute_size: available read path & zero balance ---------------------


def test_available_drives_the_size(config: ExecutionConfig) -> None:
    # 2% of 750 / 30 = 0.5 ; 2% of 1500 / 30 = 1.0 (both land on the 0.1 grid)
    small, _ = compute_size(_account(750), _price(18_000), _market_info(0.1), 2.0, config)
    large, _ = compute_size(_account(1500), _price(18_000), _market_info(0.1), 2.0, config)
    assert small == 0.5
    assert large == 1.0


def test_zero_balance_is_no_trade(config: ExecutionConfig) -> None:
    size, reason = compute_size(
        _account(0), _price(18_000), _market_info(0.1), 2.0, config
    )
    assert (size, reason) == (0.0, "below_min_deal_size")


# --- compute_size: fail-safe on a not-ok envelope -------------------------


def test_not_ok_account_env_is_no_trade(config: ExecutionConfig) -> None:
    size, reason = compute_size(
        _FakeEnv(ok=False), _price(1000), _market_info(0.1), 1.0, config
    )
    assert (size, reason) == (0.0, "account_snapshot_unavailable")


def test_not_ok_price_env_is_no_trade(config: ExecutionConfig) -> None:
    size, reason = compute_size(
        _account(100_000), _FakeEnv(ok=False), _market_info(0.1), 1.0, config
    )
    assert (size, reason) == (0.0, "price_snapshot_unavailable")


def test_not_ok_market_info_env_is_no_trade(config: ExecutionConfig) -> None:
    size, reason = compute_size(
        _account(100_000), _price(1000), _FakeEnv(ok=False), 1.0, config
    )
    assert (size, reason) == (0.0, "market_info_snapshot_unavailable")


# --- compute_size: Phase 16 D3.2 margin-based cap (L7 / AK11) ---------------


def _market_info_with_margin(
    *,
    min_deal_size: float = 0.1,
    margin_factor: float | None = None,
    margin_factor_unit: str | None = None,
) -> _FakeEnv:
    """Build a market_info envelope that optionally carries the margin fields.

    Field names mirror the Phase-1 ``MarketInfo.to_dict()`` shape (snake_case)
    — see ``ig_adapter.py:get_market_info`` (Phase 16 D3.1).
    """
    data: dict[str, Any] = {"min_deal_size": min_deal_size, "currency": "EUR"}
    if margin_factor is not None:
        data["margin_factor"] = margin_factor
    if margin_factor_unit is not None:
        data["margin_factor_unit"] = margin_factor_unit
    return _FakeEnv(ok=True, data=data)


def test_size_from_risk_margin_factor_uses_margin_cap(config: ExecutionConfig) -> None:
    """Phase 16 D3.2 (Plan §7 AK11): the Datenwoche-Grenzfall ``available=27_100, ask=24_500,
    pv=1.0, mf=5.0`` ⇒ ``leverage_cap ≈ 22.12`` and ``margin_cap ≈ 21.0`` ⇒ **size = 21.0**.

    Reproduces the empirical 2026-07-20 finding: 22.1 was REJECTED by IG, 22.0 accepted.
    With the 5 % margin-headroom (``config.margin_headroom = 0.95``, D3.2 default),
    the margin cap takes over the leverage cap and yields exactly the IG-friendly size.
    Risk-budget 3 % (aggressive) chosen so the margin cap actually binds — with the
    conservative 2 % the risk-budget (raw ≈ 18.07) undercuts both caps and the margin
    cap is never exercised (which is fine, but doesn't *demonstrate* D3.2).
    """
    info = _market_info_with_margin(
        margin_factor=5.0, margin_factor_unit="PERCENTAGE",
    )
    size, reason = compute_size(
        _account(27_100), _price(24_500), info,
        config.risk_pct_aggressive, config,
    )
    assert reason is None
    # raw = 3% of 27_100 / 30 = 27.10
    # leverage_cap = 27_100 × 20 / (24_500 × 1) = 22.12
    # margin_cap  = 27_100 × 0.95 / (24_500 × 1 × 5/100) = 25_745 / 1_225 = 21.02
    # min(27.10, 22.12, 21.02) = 21.02 -> rounded down to 0.1 = 21.0
    assert size == 21.0


def test_size_from_risk_without_margin_factor_is_bit_identical(config: ExecutionConfig) -> None:
    """``margin_factor is None`` (the legacy / pre-D3.2 path) ⇒ the leverage cap is the only cap.

    The plan verification: ``mf=None`` ⇒ **bit-identisch zu heute** (Plan §7 AK11 +
    §6 D3.2).
    """
    # Same account / price / risk inputs as the margin-factor test, but WITHOUT
    # the margin_factor fields in the market_info envelope.
    size, reason = compute_size(
        _account(27_100), _price(24_500), _market_info(0.1),
        config.risk_pct_aggressive, config,
    )
    assert reason is None
    # raw = 27.10, leverage_cap = 22.12 — same arithmetic as with a margin cap, minus
    # the margin constraint. Rounded down = 22.1.
    assert size == 22.1


def test_size_from_risk_margin_factor_zero_does_not_apply_cap(config: ExecutionConfig) -> None:
    """A 0-valued ``margin_factor`` falls back to the leverage cap (the ``> 0`` guard)."""
    info = _market_info_with_margin(
        margin_factor=0.0, margin_factor_unit="PERCENTAGE",
    )
    size, reason = compute_size(
        _account(27_100), _price(24_500), info,
        config.risk_pct_aggressive, config,
    )
    assert reason is None
    assert size == 22.1  # same as the no-margin path


def test_compute_size_logs_warning_on_unexpected_margin_factor_unit(
    config: ExecutionConfig, caplog
) -> None:
    """A non-PERCENTAGE unit (legacy ``POINTS``, hypothetical ``BANDS`` …) is ignored with a
    WARNING — the size falls back to the leverage cap, not fail-closed.

    Plan §6 D3.2: "nur wenn margin_factor_unit == 'PERCENTAGE', sonst None + einmaliges
    WARNING". A missing factor must not silently deny trades (P10 fallback behaviour).
    """
    info = _market_info_with_margin(
        margin_factor=5.0, margin_factor_unit="POINTS",
    )
    with caplog.at_level("WARNING", logger="execution.sizing"):
        size, reason = compute_size(
            _account(27_100), _price(24_500), info,
            config.risk_pct_aggressive, config,
        )
    assert reason is None
    # Same as the no-margin path: 27_100 × 20 / 24_500 = 22.12 -> 22.1.
    assert size == 22.1
    # WARNING surfaced, mentioning the unexpected unit so an operator grepping for it
    # can correlate it with the IG response (and decide whether to extend D3.2).
    assert any(
        "POINTS" in rec.getMessage() and "leverage cap" in rec.getMessage()
        for rec in caplog.records
    ), [rec.getMessage() for rec in caplog.records]


def test_compute_size_reads_margin_factor_from_market_info_unit_percentage(
    config: ExecutionConfig,
) -> None:
    """The Phase-3.1 → Phase-3.2 wiring works end-to-end: the market_info envelope's
    margin fields reach ``compute_size`` and the resulting size matches the
    helper-level ``_size_from_risk(margin_factor_pct=...)`` path.
    """
    info = _market_info_with_margin(
        margin_factor=10.0, margin_factor_unit="PERCENTAGE",
    )
    # IBEX-style 10 % margin: margin_cap = 27_100 × 0.95 / (24_500 × 1 × 0.10)
    #                        = 25_745 / 2_450 = 10.51 -> 10.5 (rounded down to 0.1)
    size, reason = compute_size(
        _account(27_100), _price(24_500), info,
        config.risk_pct_aggressive, config,
    )
    assert reason is None
    assert size == 10.5
