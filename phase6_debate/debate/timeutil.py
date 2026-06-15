"""Time helpers — ISO 8601 UTC with millisecond precision and Z suffix.

Duplicated (not imported) from Phase 1/2/3/4 on purpose: even though Phase 6
*does* reuse the Phase-4 LLM stack (the documented Decision-F exception), the
timestamp helper is tiny and phase-local — duplicating it keeps the dependency
surface honest and matches the per-phase convention. The output format is
identical so timestamps are comparable across phases:
``"2026-06-15T09:34:11.123Z"``.

Like Phase 3/4, the clock read goes through a single ``_utcnow()`` indirection so
tests can freeze time by monkeypatching it. This helper sources
``DebateContext.generated_at`` (Module 2) and the debate audit's timestamps.
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
