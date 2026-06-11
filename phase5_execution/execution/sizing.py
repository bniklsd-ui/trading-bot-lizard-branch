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

The notional→size arithmetic **mirrors** the verified Phase-1
``broker_wrapper.filters.calc_position_size`` (``notional = balance × risk_pct``;
round **down** to the 0.1 IG CFD step; ``0.0`` on non-positive balance/price). It
is re-implemented locally rather than imported, holding the same strict
phase-isolation the gates and ``execution_state`` modules keep (cross-phase imports
live only in the lazy wiring layer). If the Phase-1 formula ever changes, this
helper must track it — see the dated concept §4 annotation.
"""

from __future__ import annotations

from typing import Any

from execution.config import ExecutionConfig

def _round_down_size(
    *, available_balance: float, risk_pct: float, price: float, point_value: float = 1.0
) -> float:
    """Size so exposure ≈ ``available_balance × risk_pct``, rounded down to 0.1.

    Local mirror of Phase-1 ``filters.calc_position_size`` — kept byte-for-byte on
    the arithmetic (``int(raw * 10) / 10.0``) so the two never diverge. ``risk_pct``
    is a **fraction** here, ``notional = size × price × point_value``. Returns
    ``0.0`` on non-positive balance or price (fail-safe), never a negative size.
    """
    if available_balance <= 0 or price <= 0:
        return 0.0
    target_notional = available_balance * risk_pct
    raw_size = target_notional / (price * point_value)
    # Round DOWN to the 0.1 IG CFD step so we never exceed the risk budget.
    return max(0.0, int(raw_size * 10) / 10.0)


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
    ``_round_down_size`` expects (config ``risk_pct`` is a percent, the Phase-1
    helper takes a fraction — concept §0 annotation).

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

    # Config risk_pct is a PERCENT (0.5 → 0.5%); the helper takes a fraction.
    size = _round_down_size(
        available_balance=available, risk_pct=risk_pct / 100, price=ask, point_value=1.0
    )

    if size < min_deal_size:
        return 0.0, "below_min_deal_size"

    return size, None
