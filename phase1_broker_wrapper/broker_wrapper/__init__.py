"""
broker_wrapper — Unified broker abstraction for the trading bot.

Public surface:
    from broker_wrapper import get_broker, Envelope
    from broker_wrapper.exceptions import BrokerError, MarketOfflineError

The wrapper is designed to be used standalone (CLI / JSON pipes / scripts)
and is consumed by upper layers (FastAPI, bot core, backtester) through the
same `BrokerAdapter` interface.
"""

from broker_wrapper.envelope import Envelope, ok_envelope, error_envelope
from broker_wrapper.factory import get_broker
from broker_wrapper.exceptions import (
    BrokerError,
    AuthenticationError,
    CredentialNotFoundError,
    MarketOfflineError,
    RateLimitError,
    InsufficientFundsError,
    OrderRejectedError,
    EpicNotFoundError,
)

__all__ = [
    "Envelope",
    "ok_envelope",
    "error_envelope",
    "get_broker",
    "BrokerError",
    "AuthenticationError",
    "CredentialNotFoundError",
    "MarketOfflineError",
    "RateLimitError",
    "InsufficientFundsError",
    "OrderRejectedError",
    "EpicNotFoundError",
]

__version__ = "0.1.0"
