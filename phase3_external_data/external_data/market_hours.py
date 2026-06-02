"""XETRA market-hours check for the external-data layer.

A single predicate, :func:`is_market_open`, used by the fetcher's off-hours
guard (concept §11 step 2): intraday methods return ``None`` outside trading
hours rather than serving stale cache as fresh.

Times are evaluated in ``Europe/Berlin`` and are **DST-aware** (concept
correction §1.5): XETRA runs on CEST in summer and CET in winter, so we resolve
the local time via :class:`zoneinfo.ZoneInfo` rather than a fixed UTC offset.
"""

from __future__ import annotations

from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo

from . import timeutil

_TZ = ZoneInfo("Europe/Berlin")
_OPEN = time(9, 0)
_CLOSE = time(17, 30)


def is_market_open(now: datetime | None = None) -> bool:
    """Return whether ``now`` is within XETRA trading hours.

    Trading window: Monday–Friday, 09:00–17:30 ``Europe/Berlin`` (boundaries
    inclusive), DST-aware. ``now`` is expected to be a timezone-aware UTC
    datetime; a naive value is treated as UTC defensively.

    Holidays are **not** modelled by a calendar in v1 — that is a deliberate
    simplification. yFinance returns empty DataFrames on holidays, so those
    fall into the fetcher's ``DataUnavailableError`` path instead. A future
    phase may add ``exchange_calendars`` / ``pandas_market_calendars`` here.

    Args:
        now: The instant to test. ``None`` → the current time via
            :func:`timeutil._utcnow` (monkeypatchable in tests).

    Returns:
        ``True`` if the German cash market is open at ``now``.
    """
    if now is None:
        now = timeutil._utcnow()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    local = now.astimezone(_TZ)
    if local.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        return False
    return _OPEN <= local.time() <= _CLOSE
