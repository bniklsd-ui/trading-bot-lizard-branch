"""Tradeable filters — deterministic rules engine.

This is the "Ist dieser Kandidat tradeable?" check, moved out of the AI
bucket and into deterministic Code as agreed. Pure functions, no I/O.

Rules are configurable thresholds so the bot core / Council can tune them
without touching adapter code. Returns a structured verdict with the
specific rule that failed, so logs and Brain lessons are actionable.

Usage:
    from broker_wrapper.filters import is_tradeable, FilterConfig
    verdict = is_tradeable(price, market_info, FilterConfig())
    if not verdict.ok:
        log.info("skip %s: %s", epic, verdict.reason)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from broker_wrapper.models import Price, MarketInfo


@dataclass
class FilterConfig:
    max_spread_pct: float = 0.5          # reject if spread > 0.5%
    min_market_status: tuple[str, ...] = ("TRADEABLE",)
    require_currency: str | None = "EUR"  # None = don't enforce
    max_min_deal_size: float | None = None  # None = don't enforce


@dataclass
class FilterVerdict:
    ok: bool
    rule: str | None         # the rule that failed, if any
    reason: str | None       # human-readable explanation
    details: dict[str, Any] = field(default_factory=dict)


def is_tradeable(
    price: Price,
    market_info: MarketInfo,
    config: FilterConfig | None = None,
) -> FilterVerdict:
    """Pure function. Returns ok=True only if all rules pass."""
    cfg = config or FilterConfig()

    if price.market_status not in cfg.min_market_status:
        return FilterVerdict(
            ok=False,
            rule="MARKET_STATUS",
            reason=f"market_status={price.market_status}, "
                   f"required one of {cfg.min_market_status}",
            details={"status": price.market_status},
        )

    if price.spread_pct > cfg.max_spread_pct:
        return FilterVerdict(
            ok=False,
            rule="SPREAD_TOO_WIDE",
            reason=f"spread_pct={price.spread_pct:.3f}%, "
                   f"max={cfg.max_spread_pct}%",
            details={
                "spread_pct": price.spread_pct,
                "bid": price.bid,
                "ask": price.ask,
            },
        )

    if cfg.require_currency and market_info.currency != cfg.require_currency:
        return FilterVerdict(
            ok=False,
            rule="WRONG_CURRENCY",
            reason=f"currency={market_info.currency}, "
                   f"required={cfg.require_currency}",
            details={"currency": market_info.currency},
        )

    if (cfg.max_min_deal_size is not None
            and market_info.min_deal_size > cfg.max_min_deal_size):
        return FilterVerdict(
            ok=False,
            rule="MIN_SIZE_TOO_LARGE",
            reason=f"min_deal_size={market_info.min_deal_size}, "
                   f"max_min_deal_size={cfg.max_min_deal_size}",
            details={"min_deal_size": market_info.min_deal_size},
        )

    return FilterVerdict(ok=True, rule=None, reason=None, details={})


def calc_spread_pct(bid: float, ask: float) -> float:
    """(ask - bid) / ask * 100, guarded against div-by-zero."""
    if ask <= 0:
        return float("inf")
    return (ask - bid) / ask * 100.0


def calc_position_size(
    *,
    available_balance: float,
    risk_pct: float,
    price: float,
    point_value: float = 1.0,
    cap: float | None = None,
) -> float:
    """Compute size such that exposure ≈ balance × risk_pct.

    For a CFD where 1 unit of size = `point_value` currency per point:
        notional = size × price × point_value
    We want notional ≈ available_balance × risk_pct.

    Returns size rounded down to 1 decimal (IG CFD step).
    """
    if available_balance <= 0 or price <= 0:
        return 0.0
    target_notional = available_balance * risk_pct
    raw_size = target_notional / (price * point_value)
    if cap is not None:
        raw_size = min(raw_size, cap)
    # Round DOWN to 0.1 step so we never exceed the risk budget.
    return max(0.0, int(raw_size * 10) / 10.0)
