"""BrokerAdapter — the unified interface every broker implementation honors.

Every method returns an Envelope. Methods never raise on broker-level
errors (auth, market offline, rate limit) — those become error envelopes.
Only programmer errors (TypeError, ValueError on bad arguments) propagate.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from broker_wrapper.envelope import Envelope
from broker_wrapper.models import Direction, OrderType


class BrokerAdapter(ABC):
    """Abstract interface for all broker integrations."""

    name: str = "abstract"

    # ---------- Session ----------

    @abstractmethod
    def connect(self) -> Envelope:
        """Authenticate and acquire a session. Idempotent."""

    @abstractmethod
    def disconnect(self) -> Envelope:
        """Tear down the session cleanly. Idempotent."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Cheap, non-IO check on session state."""

    # ---------- Market data (read) ----------

    @abstractmethod
    def get_price(self, epic: str) -> Envelope:
        """Latest bid/ask/spread for an epic."""

    @abstractmethod
    def get_ohlcv(
        self, epic: str, resolution: str, count: int
    ) -> Envelope:
        """Most recent `count` OHLCV bars at `resolution`."""

    @abstractmethod
    def get_historical_ohlcv(
        self, epic: str, from_dt: str, to_dt: str, resolution: str
    ) -> Envelope:
        """OHLCV bars between two ISO 8601 timestamps."""

    @abstractmethod
    def get_market_info(self, epic: str) -> Envelope:
        """Static instrument info: lot size, expiry, currency, status."""

    @abstractmethod
    def search_markets(self, query: str) -> Envelope:
        """Search instruments by free-text query."""

    # ---------- Account (read) ----------

    @abstractmethod
    def get_account(self) -> Envelope:
        """Balance, available margin, currency."""

    @abstractmethod
    def get_open_positions(self) -> Envelope:
        """All currently open positions."""

    @abstractmethod
    def get_trade_history(self, days: int = 30) -> Envelope:
        """Closed transactions within the last `days` days."""

    # ---------- Orders (write) ----------

    @abstractmethod
    def open_position(
        self,
        epic: str,
        direction: Direction,
        size: float,
        order_type: OrderType = "MARKET",
        *,
        level: float | None = None,
        stop_level: float | None = None,
        limit_level: float | None = None,
        deal_reference: str | None = None,
        currency: str | None = None,
    ) -> Envelope:
        """Submit an order to open a new position.

        deal_reference is a client-supplied idempotency key. If None,
        the adapter generates one and returns it in the OrderResult.
        """

    @abstractmethod
    def close_position(self, deal_id: str) -> Envelope:
        """Submit a closing order for a position by deal_id."""

    @abstractmethod
    def modify_position(
        self,
        deal_id: str,
        *,
        stop_level: float | None = None,
        limit_level: float | None = None,
    ) -> Envelope:
        """Adjust stop/limit on an open position."""

    @abstractmethod
    def reconcile_positions(
        self, expected_references: list[str] | None = None
    ) -> Envelope:
        """Compare local view to broker truth.

        Called on startup or after a network failure. If
        `expected_references` is given, returns which references the
        broker has and which it does not, so the bot can recover state
        deterministically.
        """
