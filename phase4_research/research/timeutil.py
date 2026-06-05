"""Time helpers — ISO 8601 UTC with millisecond precision and Z suffix.

Duplicated (not imported) from Phase 1/2/3 on purpose: Phase 4 must run with no
dependency on ``broker_wrapper`` / ``persistence`` / ``external_data`` (phase
isolation). The output format is identical so timestamps are comparable across
phases: ``"2026-06-05T09:34:11.123Z"``.

Like Phase 3 (and unlike Phase 2), the clock read goes through a single
``_utcnow()`` indirection so tests can freeze time by monkeypatching it. This
helper sources ``Candidate.generated_at`` (Step 2) and will source the token
meter's ``ts`` (Step 5).
"""

from __future__ import annotations

from datetime import datetime, timezone


def _utcnow() -> datetime:
    """The single clock read. Monkeypatch this in tests to freeze time."""
    return datetime.now(timezone.utc)


def utc_iso_now() -> str:
    """Current UTC time as an ISO 8601 string with ms precision and Z suffix."""
    now = _utcnow()
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


def parse_iso(ts: str) -> datetime:
    """Parse an ISO 8601 UTC string (with optional Z suffix) to an aware datetime.

    Accepts the ``...Z`` form produced by :func:`utc_iso_now` as well as plain
    offset-bearing ISO strings. The result is always timezone-aware (UTC).
    """
    normalized = ts.replace("Z", "+00:00") if ts.endswith("Z") else ts
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
