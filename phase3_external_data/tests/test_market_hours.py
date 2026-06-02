"""Tests for ``external_data.market_hours.is_market_open`` (concept §15).

No network. Times are passed as explicit timezone-aware UTC datetimes so the
DST-aware Europe/Berlin conversion is exercised directly; the ``now=None``
default path is covered via the ``frozen_clock`` fixture.

DST reference for 2026: Europe/Berlin is on CEST (UTC+2) from 2026-03-29 to
2026-10-25, otherwise CET (UTC+1).
"""

from __future__ import annotations

from datetime import datetime, timezone

from external_data import market_hours


def _utc(year, month, day, hour, minute=0) -> datetime:
    """Build a timezone-aware UTC datetime."""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def test_weekday_inside_window_is_open():
    # Monday 2026-05-25, 09:00 UTC = 11:00 Berlin (CEST) — mid-session.
    assert market_hours.is_market_open(_utc(2026, 5, 25, 9, 0)) is True


def test_saturday_is_closed():
    # Saturday 2026-05-30, 10:00 UTC = 12:00 Berlin — weekend.
    assert market_hours.is_market_open(_utc(2026, 5, 30, 10, 0)) is False


def test_sunday_is_closed():
    # Sunday 2026-05-31, 10:00 UTC = 12:00 Berlin — weekend.
    assert market_hours.is_market_open(_utc(2026, 5, 31, 10, 0)) is False


def test_before_open_is_closed():
    # Monday 2026-05-25, 06:30 UTC = 08:30 Berlin (CEST) — before 09:00.
    assert market_hours.is_market_open(_utc(2026, 5, 25, 6, 30)) is False


def test_after_close_is_closed():
    # Monday 2026-05-25, 16:00 UTC = 18:00 Berlin (CEST) — after 17:30.
    assert market_hours.is_market_open(_utc(2026, 5, 25, 16, 0)) is False


def test_dst_awareness_same_utc_differs_by_season():
    # Identical 07:30 UTC on a Monday resolves to different Berlin local times:
    #   summer (CEST, UTC+2) → 09:30 Berlin → open
    #   winter (CET,  UTC+1) → 08:30 Berlin → closed
    summer = market_hours.is_market_open(_utc(2026, 5, 25, 7, 30))   # Monday
    winter = market_hours.is_market_open(_utc(2026, 1, 5, 7, 30))    # Monday
    assert summer is True
    assert winter is False


def test_inclusive_boundaries():
    # 09:00 and 17:30 Berlin (CEST) are inclusive endpoints of the window.
    assert market_hours.is_market_open(_utc(2026, 5, 25, 7, 0)) is True    # 09:00 Berlin
    assert market_hours.is_market_open(_utc(2026, 5, 25, 15, 30)) is True  # 17:30 Berlin


def test_default_now_uses_clock(frozen_clock):
    # frozen_clock defaults to Mon 2026-05-25 09:00 UTC (11:00 Berlin) → open.
    assert market_hours.is_market_open() is True
    # Re-freeze to a weekend instant → closed via the same clock indirection.
    frozen_clock(_utc(2026, 5, 30, 10, 0))
    assert market_hours.is_market_open() is False


def test_naive_datetime_treated_as_utc():
    # A naive datetime is treated as UTC: Monday 09:00 UTC → 11:00 Berlin → open.
    naive = datetime(2026, 5, 25, 9, 0)
    assert market_hours.is_market_open(naive) is True
