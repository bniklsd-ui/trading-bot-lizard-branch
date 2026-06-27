"""Module 3 — ``Clock`` phase classification + DST-correct ``seconds_until``.

All mocked: ``now`` is passed explicitly (or via a fixed ``now_fn``), ``sleep_fn`` is
a recording no-op, and no test sleeps for real or hits the network. Reference dates
are pinned, real calendar days (verified weekdays / DST transitions):

- 2026-06-29 Mon, 2026-07-03 Fri, 2026-07-04 Sat, 2026-07-05 Sun (a clean week).
- 2026-03-29 Sun = spring-forward (02:00→03:00); the Fri→Mon span around it loses an
  hour (real 62h, not the naive 63h).
- 2026-10-25 Sun = fall-back (03:00→02:00); the Fri→Mon span gains an hour (64h).
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from scheduler import Clock as ExportedClock
from scheduler import Phase as ExportedPhase
from scheduler.clock import Clock, Phase
from scheduler.config import SchedulerConfig

_TZ = ZoneInfo("Europe/Berlin")
_HOUR = 3600.0


def _berlin(y: int, m: int, d: int, hh: int, mm: int) -> datetime:
    return datetime(y, m, d, hh, mm, tzinfo=_TZ)


def _clock(**cfg) -> tuple[Clock, list[float]]:
    """Build a Clock on the given config overrides; return it + a sleep-capture list."""
    sleeps: list[float] = []
    clock = Clock(
        SchedulerConfig(**cfg),
        now_fn=lambda: _berlin(2026, 6, 29, 10, 0),  # unused by classify/seconds_until
        sleep_fn=sleeps.append,
    )
    return clock, sleeps


# --- classify (defaults: window 09:00–17:30, pre-open lead 10 → 08:50) ---------


def test_weekday_before_lead_is_idle() -> None:
    clock, _ = _clock()
    assert clock.classify(_berlin(2026, 6, 29, 8, 0)) is Phase.IDLE


def test_weekday_inside_lead_is_pre_open() -> None:
    clock, _ = _clock()
    # 08:50 is the inclusive start of the warm-up; 08:55 is well inside it.
    assert clock.classify(_berlin(2026, 6, 29, 8, 50)) is Phase.PRE_OPEN
    assert clock.classify(_berlin(2026, 6, 29, 8, 55)) is Phase.PRE_OPEN


def test_weekday_inside_window_is_window() -> None:
    clock, _ = _clock()
    assert clock.classify(_berlin(2026, 6, 29, 12, 0)) is Phase.WINDOW


def test_weekday_after_close_is_post_window() -> None:
    clock, _ = _clock()
    assert clock.classify(_berlin(2026, 6, 29, 17, 31)) is Phase.POST_WINDOW
    assert clock.classify(_berlin(2026, 6, 29, 23, 0)) is Phase.POST_WINDOW


def test_window_boundaries_are_inclusive() -> None:
    clock, _ = _clock()
    assert clock.classify(_berlin(2026, 6, 29, 9, 0)) is Phase.WINDOW   # exact open
    assert clock.classify(_berlin(2026, 6, 29, 17, 30)) is Phase.WINDOW  # exact close


def test_weekend_is_idle_even_inside_window_hours() -> None:
    clock, _ = _clock()
    assert clock.classify(_berlin(2026, 7, 4, 12, 0)) is Phase.IDLE  # Saturday
    assert clock.classify(_berlin(2026, 7, 5, 12, 0)) is Phase.IDLE  # Sunday


# --- seconds_until -------------------------------------------------------------


def test_seconds_until_window_same_day_from_pre_open() -> None:
    clock, _ = _clock()
    secs = clock.seconds_until(Phase.WINDOW, _berlin(2026, 6, 29, 8, 55))
    assert secs == pytest.approx(5 * 60)  # 08:55 → 09:00


def test_seconds_until_window_across_midnight() -> None:
    clock, _ = _clock()
    # Mon 18:00 (POST_WINDOW) → Tue 09:00 = 15h.
    secs = clock.seconds_until(Phase.WINDOW, _berlin(2026, 6, 29, 18, 0))
    assert secs == pytest.approx(15 * _HOUR)


def test_seconds_until_window_skips_the_weekend() -> None:
    clock, _ = _clock()
    # Fri 18:00 → Mon 09:00 = 63h (no DST change this week).
    secs = clock.seconds_until(Phase.WINDOW, _berlin(2026, 7, 3, 18, 0))
    assert secs == pytest.approx(63 * _HOUR)


def test_seconds_until_is_strictly_next_when_now_is_on_the_boundary() -> None:
    clock, _ = _clock()
    # Exactly at Mon 09:00 → next WINDOW is Tue 09:00 (24h), never 0.
    secs = clock.seconds_until(Phase.WINDOW, _berlin(2026, 6, 29, 9, 0))
    assert secs == pytest.approx(24 * _HOUR)


def test_seconds_until_pre_open_from_post_window() -> None:
    clock, _ = _clock()
    # Mon 18:00 → Tue 08:50 (next pre-open) = 14h50m.
    secs = clock.seconds_until(Phase.PRE_OPEN, _berlin(2026, 6, 29, 18, 0))
    assert secs == pytest.approx((14 * 60 + 50) * 60)


def test_seconds_until_idle_is_rejected() -> None:
    clock, _ = _clock()
    with pytest.raises(ValueError):
        clock.seconds_until(Phase.IDLE, _berlin(2026, 6, 29, 18, 0))


def test_seconds_until_is_dst_correct_spring_forward() -> None:
    """Fri 2026-03-27 18:00 → Mon 09:00 spans the spring-forward: real 62h, not 63h."""
    clock, _ = _clock()
    secs = clock.seconds_until(Phase.WINDOW, _berlin(2026, 3, 27, 18, 0))
    assert secs == pytest.approx(62 * _HOUR)
    assert secs != pytest.approx(63 * _HOUR)  # the naive-subtraction trap


def test_seconds_until_is_dst_correct_fall_back() -> None:
    """Fri 2026-10-23 18:00 → Mon 09:00 spans the fall-back: real 64h, not 63h."""
    clock, _ = _clock()
    secs = clock.seconds_until(Phase.WINDOW, _berlin(2026, 10, 23, 18, 0))
    assert secs == pytest.approx(64 * _HOUR)


# --- now / sleep / market_is_open / config-driven window ----------------------


def test_now_returns_injected_instant_tz_aware() -> None:
    clock, _ = _clock()
    now = clock.now()
    assert now == _berlin(2026, 6, 29, 10, 0)
    assert now.tzinfo is not None


def test_sleep_delegates_to_injected_sleep_fn() -> None:
    clock, sleeps = _clock()
    clock.sleep(42.0)
    clock.sleep(7.5)
    assert sleeps == [42.0, 7.5]


def test_market_is_open_delegates_to_phase3_predicate() -> None:
    """``market_is_open`` reuses P3's DST-aware predicate (Decision 2)."""
    clock, _ = _clock()
    assert clock.market_is_open(_berlin(2026, 6, 29, 10, 0)) is True   # Mon in-hours
    assert clock.market_is_open(_berlin(2026, 6, 29, 8, 0)) is False   # Mon pre-open
    assert clock.market_is_open(_berlin(2026, 7, 4, 12, 0)) is False   # Saturday


def test_window_is_config_driven_not_hardcoded() -> None:
    """A custom window reclassifies the same instant — boundaries come from config."""
    clock, _ = _clock(window_open="10:00", window_close="12:00")
    assert clock.classify(_berlin(2026, 6, 29, 9, 30)) is Phase.IDLE     # before 09:50 lead
    assert clock.classify(_berlin(2026, 6, 29, 9, 55)) is Phase.PRE_OPEN  # 09:50–10:00
    assert clock.classify(_berlin(2026, 6, 29, 11, 0)) is Phase.WINDOW
    assert clock.classify(_berlin(2026, 6, 29, 12, 1)) is Phase.POST_WINDOW


# --- package export ------------------------------------------------------------


def test_clock_and_phase_exported_from_package_root() -> None:
    assert ExportedClock is Clock
    assert ExportedPhase is Phase
