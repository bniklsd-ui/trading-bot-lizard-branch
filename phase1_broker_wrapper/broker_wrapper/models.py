"""Normalized data models — the cross-broker vocabulary.

Every adapter converts its broker-specific payloads into these dataclasses.
Upper layers (bot, FastAPI, backtester) only ever see these shapes.

All amounts are floats with the broker-reported precision. Currency is
explicit on Account / Position so the caller never has to guess.
Timestamps are ISO 8601 UTC strings.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal, Any


Direction = Literal["BUY", "SELL"]
OrderType = Literal["MARKET", "LIMIT", "STOP"]
MarketStatus = Literal[
    "TRADEABLE", "CLOSED", "OFFLINE", "EDITS_ONLY", "AUCTION", "UNKNOWN"
]
DealStatus = Literal["ACCEPTED", "REJECTED", "PENDING", "UNKNOWN"]


@dataclass
class Price:
    epic: str
    bid: float
    ask: float
    spread: float            # absolute (ask - bid)
    spread_pct: float        # (ask - bid) / ask * 100
    market_status: MarketStatus
    timestamp: str           # ISO 8601 UTC

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OHLCBar:
    timestamp: str           # ISO 8601 UTC, bar open time
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class MarketInfo:
    epic: str
    name: str
    instrument_type: str     # "CFD", "FUTURE", "OPTION", etc.
    currency: str            # ISO 4217
    expiry: str | None       # ISO date if applicable, else None
    min_deal_size: float
    lot_size: float          # value per point/pip in the instrument's currency
    market_status: MarketStatus
    # Additive (2026-07-04, Phase 1 hardening Step 2): IG's raw pip/contract fields,
    # passed through as-is (strings, as IG returns them). None if IG omits them.
    # Parsing them into a resolved point_value is Phase 9's job (pricing.py).
    value_of_one_pip: str | None = None
    one_pip_means: str | None = None
    contract_size: str | None = None
    # Additive (2026-09-05, Phase 16 D3.1, L7 / AK11): IG's per-instrument margin
    # requirement (``instrument.marginFactor`` / ``marginFactorUnit``), used by
    # Phase-5 sizing as a margin-based notional cap. ``margin_factor`` is a float
    # (e.g. ``5.0`` for 5 % on DAX); ``margin_factor_unit`` is the IG-reported unit
    # string ("PERCENTAGE" is the one the sizing code can consume, anything else
    # triggers a one-shot WARNING + fall back to the leverage cap). ``None`` if IG
    # omits either field — consumer MUST handle the absence (legacy behaviour,
    # no margin cap). See `probe_market_margin.py` for the empirical confirmation
    # across DAX/IBEX/AEX (2026-09-07).
    margin_factor: float | None = None
    margin_factor_unit: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Account:
    account_id: str
    balance: float
    available: float         # what can be used for new positions
    profit_loss: float
    currency: str            # ISO 4217

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Position:
    deal_id: str
    deal_reference: str | None
    epic: str
    direction: Direction
    size: float
    open_level: float
    current_level: float | None
    profit_loss: float | None
    currency: str
    created_at: str          # ISO 8601 UTC
    stop_level: float | None = None
    limit_level: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OrderResult:
    """Result of an order submission and its confirmation.

    deal_reference is a client-supplied idempotency key. If the network
    drops mid-call, the bot can reconcile using this reference.
    """
    deal_reference: str
    deal_id: str | None
    status: DealStatus
    epic: str
    direction: Direction | None
    size: float
    level: float | None      # actual fill level if accepted
    reason: str | None        # rejection reason if any
    timestamp: str            # ISO 8601 UTC

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Transaction:
    """Single row of trade history."""
    transaction_id: str
    epic: str | None
    direction: Direction | None
    size: float | None
    open_level: float | None
    close_level: float | None
    profit_loss: float | None
    currency: str | None
    open_date: str | None
    close_date: str | None
    transaction_type: str    # broker-specific, normalized as best-effort
