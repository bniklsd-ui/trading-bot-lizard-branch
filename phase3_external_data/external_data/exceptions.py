"""Custom exception hierarchy for the external-data layer.

Mirrors the Phase-1 ``BrokerError`` pattern: a base class with a ``code``
class attribute and a ``retryable`` flag, so callers can catch the whole
family with one ``except`` clause or be more specific when needed.

Phase 3 stays isolated from Phase 1, so this hierarchy is **independent** —
we deliberately do not import Phase 1's ``RateLimitError``. The two
``RateLimitError`` names live in different modules; callers wanting both
can alias on import.
"""

from __future__ import annotations


class ExternalDataError(Exception):
    """Base class for all external-data errors."""

    code: str = "EXTERNAL_DATA_ERROR"
    retryable: bool = False

    def __init__(self, message: str, *, retryable: bool | None = None) -> None:
        super().__init__(message)
        if retryable is not None:
            self.retryable = retryable


class EpicNotMappedError(ExternalDataError):
    """No yFinance symbol is registered for the given IG epic.

    Treated as a programmer error: the fetcher does **not** catch this, it
    propagates so the missing mapping gets fixed in ``TickerMapper``.
    """

    code = "EPIC_NOT_MAPPED"
    retryable = False


class DataUnavailableError(ExternalDataError):
    """yFinance returned no usable data (empty / too-short DataFrame).

    Raised after the fetcher's retry budget is exhausted. Typical causes:
    market holiday, off-hours intraday request, transient upstream hiccup.
    Retryable later (different time / different symbol).
    """

    code = "DATA_UNAVAILABLE"
    retryable = True


class RateLimitError(ExternalDataError):
    """yFinance rate-limited us (HTTP 429 / ``YFRateLimitError``).

    Raised after the fetcher's retry budget is exhausted. The fetcher
    translates ``yfinance.exceptions.YFRateLimitError`` into this type so
    callers do not need to import yFinance internals.
    """

    code = "RATE_LIMIT"
    retryable = True


class CircuitOpenError(ExternalDataError):
    """The per-ticker circuit breaker is open — no network call was even attempted.

    Phase 9 (V2) Step 6: the structural answer to a ticker that fails
    persistently (the ``^FCHI``/``^IBEX`` intermittency this arc kept
    resurfacing) — after ``open_after`` consecutive failures the fetcher stops
    hammering that symbol for ``cooldown_s``, degrading immediately instead of
    spending another retry budget on a symbol that is currently unhealthy.
    Same ``ExternalDataError`` family as :class:`DataUnavailableError`, so every
    existing ``except ExternalDataError`` caller (``get_brain_context``'s
    ``field_errors``) degrades gracefully with zero changes.
    """

    code = "CIRCUIT_OPEN"
    retryable = True
