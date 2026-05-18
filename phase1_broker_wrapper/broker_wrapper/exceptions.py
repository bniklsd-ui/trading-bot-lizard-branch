"""Custom exception hierarchy for the broker wrapper.

All wrapper-level errors derive from BrokerError so callers can catch
the whole family with one except clause, or be more specific when needed.
"""


class BrokerError(Exception):
    """Base class for all broker wrapper errors."""

    code: str = "BROKER_ERROR"
    retryable: bool = False

    def __init__(self, message: str, *, retryable: bool | None = None) -> None:
        super().__init__(message)
        if retryable is not None:
            self.retryable = retryable


class AuthenticationError(BrokerError):
    """Login failed, token rejected, credentials invalid."""

    code = "AUTH_ERROR"
    retryable = False


class CredentialNotFoundError(BrokerError):
    """Credential is not present in the OS keyring."""

    code = "CREDENTIAL_NOT_FOUND"
    retryable = False


class MarketOfflineError(BrokerError):
    """Market is closed, off-hours, or the broker is not quoting."""

    code = "MARKET_OFFLINE"
    retryable = True  # try again later


class RateLimitError(BrokerError):
    """Broker rate-limited us. Caller should back off."""

    code = "RATE_LIMIT"
    retryable = True


class InsufficientFundsError(BrokerError):
    """Account has insufficient margin / balance for the operation."""

    code = "INSUFFICIENT_FUNDS"
    retryable = False


class OrderRejectedError(BrokerError):
    """Order was accepted at the API level but rejected at the venue."""

    code = "ORDER_REJECTED"
    retryable = False


class EpicNotFoundError(BrokerError):
    """The instrument identifier is unknown to the broker."""

    code = "EPIC_NOT_FOUND"
    retryable = False


class NetworkError(BrokerError):
    """Transport-level failure (timeout, DNS, connection refused)."""

    code = "NETWORK_ERROR"
    retryable = True


class ProtocolError(BrokerError):
    """Broker returned a malformed or unexpected payload."""

    code = "PROTOCOL_ERROR"
    retryable = False
