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
