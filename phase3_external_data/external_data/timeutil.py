"""Time helpers — ISO 8601 UTC with millisecond precision and Z suffix.

Duplicated (not imported) from Phase 2's ``timeutil.py`` on purpose: Phase 3
must run with no dependency on ``persistence`` or ``broker_wrapper`` (phase
isolation). The output format is identical so timestamps are comparable across
phases: ``"2026-05-21T09:34:11.123Z"``.

The single addition over Phase 2 is the :func:`_utcnow` indirection (concept
§6): every other module reads the wall clock through this one function, so
tests can monkeypatch ``timeutil._utcnow`` to drive a deterministic clock
without touching ``datetime`` globally. Modules that need "now" must reference
it module-qualified (``from . import timeutil`` → ``timeutil._utcnow()``) so a
patch is actually seen.
"""

from __future__ import annotations

from datetime import datetime, timezone


def _utcnow() -> datetime:
    """Return the current time as an aware UTC datetime.

    The single clock source for the whole package. Tests monkeypatch **this**
    function (``monkeypatch.setattr(timeutil, "_utcnow", ...)``) to freeze time.
    """
    return datetime.now(timezone.utc)


def iso_from_dt(dt: datetime) -> str:
    """Format an aware datetime as ISO 8601 UTC with ms precision and Z suffix.

    The single canonical formatter (format: ``"2026-05-21T09:34:11.123Z"``).
    The input is converted to UTC first; a naive datetime is treated as UTC.
    Used by :func:`utc_iso_now` and by callers that need to stamp an arbitrary
    instant (e.g. a price-bar timestamp), not just "now".

    Args:
        dt: The datetime to format. Naive values are assumed UTC.

    Returns:
        The ISO 8601 UTC string.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def utc_iso_now() -> str:
    """Current UTC time as an ISO 8601 string with ms precision and Z suffix.

    Reads the clock via :func:`_utcnow`, so it follows any monkeypatched clock
    in tests. Format: ``"2026-05-21T09:34:11.123Z"``.
    """
    return iso_from_dt(_utcnow())


def parse_iso(ts: str) -> datetime:
    """Parse an ISO 8601 UTC string (with optional Z suffix) to an aware datetime.

    Accepts the ``...Z`` form produced by :func:`utc_iso_now` as well as plain
    offset-bearing ISO strings. The result is always timezone-aware (UTC).

    Args:
        ts: An ISO 8601 timestamp string.

    Returns:
        A timezone-aware :class:`datetime` (UTC).
    """
    normalized = ts.replace("Z", "+00:00") if ts.endswith("Z") else ts
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
