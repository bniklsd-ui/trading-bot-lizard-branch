"""Gate 4 — position sizing (concept §4 / Decision F).

Turns the score-coupled risk level into a concrete, IG-valid position size:

- **:func:`select_risk_pct`** reads ``Database.get_risk_level()`` (KONSERVATIV /
  AGGRESSIV) and picks the matching config percent.
- **:func:`compute_size`** sizes the order from the live account/price snapshot and
  rejects (no trade) when the rounded size falls below the instrument's
  ``min_deal_size`` — **no upward clamp**, so the risk budget is never exceeded.

Pure, testable functions: the orchestrator (Step 8) fetches the broker envelopes
once and passes them in; nothing here does I/O or calls AI. Phase-isolated —
stdlib + ``execution`` types only, **no** sibling-package imports.

**Sizing model — risk-per-trade ÷ stop-distance (operator decision 2026-06-12).**
The size is the position whose worst-case loss at the stop ≈ the risk budget::

    risk_amount = available_balance × risk_pct          # money at risk if stopped
    raw_size    = risk_amount / (stop_distance_points × point_value)

so ``size`` scales with the **SL distance**, not the index price. This deliberately
**diverges** from the Phase-1 ``broker_wrapper.filters.calc_position_size`` notional
÷ price model that this helper used to mirror: that model needed a ~€1.8M balance to
reach size 0.5 on DAX ~18000, so a real ~€1K-budget account never produced a
tradeable size (live-confirmed ``below_min_deal_size`` on 2026-06-11). The mirror is
now **intentionally broken** — do not "fix" it back to the Phase-1 formula; see the
dated concept §4 annotation. A notional/leverage **cap** (``max_leverage``) keeps the
otherwise price-unbounded risk model from requesting more margin than the account can
hold. Round **down** to the 0.1 IG CFD step; ``0.0`` on any non-positive input.
"""

from __future__ import annotations

from typing import Any

from execution.config import ExecutionConfig

def _size_from_risk(
    *,
    available_balance: float,
    risk_pct: float,
    stop_distance_points: float,
    price: float,
    max_leverage: float,
    point_value: float = 1.0,
) -> float:
    """Risk-per-trade size, leverage-capped, rounded **down** to the 0.1 IG step.

    ``risk_pct`` is a **fraction** here (``compute_size`` passes ``config %`` ÷ 100).
    The size is the position whose loss at the stop ≈ ``available_balance × risk_pct``::

        raw_size = (available_balance × risk_pct) / (stop_distance_points × point_value)

    A notional ceiling ``cap_size = (available_balance × max_leverage) / (price ×
    point_value)`` guards against the risk model requesting more margin than the
    account can hold (it only bites pathological cases — e.g. a tiny stop distance on
    a large balance — never normal ~€1K sizing). Returns ``0.0`` on any non-positive
    balance, stop distance or price (fail-safe), never a negative size.
    """
    if available_balance <= 0 or stop_distance_points <= 0 or price <= 0:
        return 0.0
    risk_amount = available_balance * risk_pct
    raw_size = risk_amount / (stop_distance_points * point_value)
    # Notional/leverage safety cap — never request more margin than the account holds.
    cap_size = (available_balance * max_leverage) / (price * point_value)
    sized = min(raw_size, cap_size)
    # Round DOWN to the 0.1 IG CFD step so we never exceed the risk budget.
    return max(0.0, int(sized * 10) / 10.0)


def select_risk_pct(db: Any, config: ExecutionConfig) -> float:
    """Pick the risk percent from the score-coupled risk level (Decision F).

    ``Database.get_risk_level()`` returns ``"AGGRESSIV"`` (score above neutral) or
    ``"KONSERVATIV"``; we map those to ``risk_pct_aggressive`` /
    ``risk_pct_conservative``. The value is a **percent** (e.g. ``0.5``) — the
    caller divides by 100 before sizing.
    """
    return (
        config.risk_pct_aggressive
        if db.get_risk_level() == "AGGRESSIV"
        else config.risk_pct_conservative
    )


def compute_size(
    account_env: Any,
    price_env: Any,
    market_info_env: Any,
    risk_pct: float,
    config: ExecutionConfig,
) -> tuple[float, str | None]:
    """Gate 4: size the order, or reject (no trade) below ``min_deal_size``.

    Returns ``(size, reason)``: ``reason`` is ``None`` on success, otherwise a
    no-trade code (the executor logs it to stderr). ``risk_pct`` is the **percent**
    from :func:`select_risk_pct`; it is divided by 100 to the fraction
    :func:`_size_from_risk` expects (config ``risk_pct`` is a percent — concept §0
    annotation). The risk-per-trade model reads ``config.stop_distance_points`` (the
    SL offset the size is sized against) and ``config.max_leverage`` (the notional
    safety cap); the live ``ask`` feeds only the cap, not the risk arithmetic.

    Fail-safe: any envelope that is not ``ok`` is a no-trade (we cannot verify the
    size). A rounded size below the instrument's ``min_deal_size`` is a no-trade
    too — we never clamp upward.
    """
    if not account_env.ok:
        return 0.0, "account_snapshot_unavailable"
    if not price_env.ok:
        return 0.0, "price_snapshot_unavailable"
    if not market_info_env.ok:
        return 0.0, "market_info_snapshot_unavailable"

    available = float((account_env.data or {}).get("available", 0) or 0)
    ask = float((price_env.data or {}).get("ask", 0) or 0)
    min_deal_size = float((market_info_env.data or {}).get("min_deal_size", 0) or 0)

    # Config risk_pct is a PERCENT (2.0 → 2.0%); the helper takes a fraction.
    size = _size_from_risk(
        available_balance=available,
        risk_pct=risk_pct / 100,
        stop_distance_points=config.stop_distance_points,
        price=ask,
        max_leverage=config.max_leverage,
        point_value=1.0,
    )

    if size < min_deal_size:
        return 0.0, "below_min_deal_size"

    return size, None
