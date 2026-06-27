"""Module 3 — the scheduler clock: wall-clock time → daemon phase.

The loop (Module 11 ``runner.py``) does not read the clock directly; it asks the
:class:`Clock` *which phase are we in?* and *how long until the next one?*, then
warms the session / runs a cycle / reconciles / sleeps accordingly. Time is fully
**injectable** (``now_fn`` / ``sleep_fn``) so the whole daemon is deterministically
testable — tests drive ``now_fn`` and pass a no-op ``sleep_fn``; nothing here ever
calls the real clock-of-the-wall or sleeps for real, and there is no network.

The four phases (concept §2):

- ``PRE_OPEN``  — a trading day, inside the ``pre_open_lead_min`` warm-up window just
  before ``window_open``: the loop warms the IG session + token so the first WINDOW
  cycle does not pay a cold connect.
- ``WINDOW``    — a trading day, inside ``[window_open, window_close]`` (inclusive):
  the loop attempts a full research → execute cycle.
- ``POST_WINDOW`` — a trading day, after ``window_close`` (before midnight): a final
  reconcile pass, then sleep until the next pre-open.
- ``IDLE``      — a non-trading day (weekend), or a trading day before the warm-up
  window starts: just sleep.

Two design points worth pinning (code = source of truth):

1. **The WINDOW boundary is config-driven**, parsed from the ``HH:MM`` strings
   ``config.window_open`` / ``config.window_close`` via a local ``_parse_hhmm``
   (mirroring P5 ``gates._parse_hhmm`` — copied, not imported, to keep this module
   phase-isolated). The defaults are the live-verified full-market window
   ``09:00``–``17:30`` (Module-1 reconciliation), but a test may override them.
2. **The trading-day check is a weekday test** (Mon–Fri). v1 has **no holiday
   calendar** — the same deliberate simplification P3 ``market_hours`` makes; a
   holiday looks like a trading day here, and falls into the broker / VETO
   fail-closed paths downstream (the daemon attempts a cycle, the market-status VETO
   refuses it). The live, DST-aware P3 predicate is still reused — lazily — via
   :meth:`Clock.market_is_open` (Decision 2: do not reimplement market hours), so the
   hot classification logic stays stdlib-only and import-light while the runtime
   "is the market actually open?" guard delegates to P3.

All datetime arithmetic is **DST-safe**: boundaries are constructed as tz-aware
datetimes in ``config.tz`` and subtracted — never naive ``timedelta(hours=…)`` hacks
(concept requirement). Repo conventions apply (``from __future__ import
annotations``, type hints + docstrings). Imports nothing cross-phase at module scope.
"""

from __future__ import annotations

import time as _time
from datetime import date, datetime, time, timedelta, timezone
from enum import Enum
from typing import Callable

from zoneinfo import ZoneInfo

from .config import SchedulerConfig


class Phase(Enum):
    """The daemon's coarse time-of-day phase (concept §2)."""

    PRE_OPEN = "PRE_OPEN"
    WINDOW = "WINDOW"
    POST_WINDOW = "POST_WINDOW"
    IDLE = "IDLE"


def _parse_hhmm(value: str) -> time:
    """Parse an ``"HH:MM"`` window string into a :class:`datetime.time`.

    Mirrors P5 ``gates._parse_hhmm`` — copied rather than imported so ``scheduler``
    does not depend on the ``execution`` package for a one-line parse (phase
    isolation; the window is held as ``HH:MM`` strings per the Module-1 config
    reconciliation).
    """
    hour, minute = (int(part) for part in value.split(":", 1))
    return time(hour=hour, minute=minute)


class Clock:
    """Maps wall-clock time to the daemon phase, with injectable now / sleep.

    Args:
        config: the frozen :class:`SchedulerConfig` (supplies the window strings,
            ``tz`` and ``pre_open_lead_min``).
        now_fn: returns the current instant. Default ``datetime.now`` in
            ``config.tz`` (tz-aware). Tests inject a fake returning fixed datetimes.
        sleep_fn: blocks for N seconds. Default ``time.sleep``. Tests inject a
            recording no-op so the loop never sleeps for real.
    """

    def __init__(
        self,
        config: SchedulerConfig,
        *,
        now_fn: Callable[[], datetime] | None = None,
        sleep_fn: Callable[[float], None] | None = None,
    ) -> None:
        self._config = config
        self._tz = ZoneInfo(config.tz)
        self._now_fn: Callable[[], datetime] = (
            now_fn if now_fn is not None else (lambda: datetime.now(self._tz))
        )
        self._sleep_fn: Callable[[float], None] = (
            sleep_fn if sleep_fn is not None else _time.sleep
        )
        self._window_open = _parse_hhmm(config.window_open)
        self._window_close = _parse_hhmm(config.window_close)

    # --- time access -------------------------------------------------------

    def now(self) -> datetime:
        """The current instant as a tz-aware datetime in ``config.tz``."""
        return self._to_zone(self._now_fn())

    def sleep(self, seconds: float) -> None:
        """Block for ``seconds`` by delegating to the injected ``sleep_fn``."""
        self._sleep_fn(seconds)

    # --- classification ----------------------------------------------------

    def classify(self, now: datetime) -> Phase:
        """Classify ``now`` (interpreted in ``config.tz``) into a :class:`Phase`.

        Weekend (or any non-weekday) → ``IDLE``. On a trading day the time-of-day is
        compared against the config window: inside ``[open, close]`` → ``WINDOW``;
        inside the ``pre_open_lead_min`` warm-up before open → ``PRE_OPEN``; after
        close → ``POST_WINDOW``; before the warm-up window → ``IDLE``.
        """
        local = self._to_zone(now)
        if not self._is_trading_day(local):
            return Phase.IDLE

        t = local.time()
        if self._window_open <= t <= self._window_close:
            return Phase.WINDOW
        if self._pre_open_time() <= t < self._window_open:
            return Phase.PRE_OPEN
        if t > self._window_close:
            return Phase.POST_WINDOW
        return Phase.IDLE

    def seconds_until(self, target: Phase, now: datetime) -> float:
        """Seconds from ``now`` until the next *start* of ``target`` on a trading day.

        Used by the loop (concept §10): ``seconds_until(WINDOW)`` from PRE_OPEN, and
        ``seconds_until(PRE_OPEN)`` from POST_WINDOW. The boundary is the strictly
        next future occurrence — if ``now`` is exactly at the boundary, the *next*
        day's boundary is returned, never ``0`` (so a PRE_OPEN-driven sleep cannot
        busy-loop).

        Walks forward day-by-day (≤8 days, enough to clear a weekend), skipping
        non-trading days, and builds each candidate as a tz-aware datetime in
        ``config.tz``. The elapsed seconds are computed from the **UTC** instants:
        subtracting two datetimes that share the same ``ZoneInfo`` would do naive
        wall-clock subtraction (a 63h answer for a span that spans a spring-forward
        is really 62h), so both sides are converted to UTC first — DST-correct, no
        naive ``timedelta(hours=…)`` hack (concept requirement).

        ``IDLE`` has no single start time (it occurs both early-morning and on
        weekends) and is not a sleep target — requesting it raises ``ValueError``.
        """
        local = self._to_zone(now)
        boundary = self._boundary_time(target)
        for offset in range(0, 9):
            day = (local + timedelta(days=offset)).date()
            candidate = datetime.combine(day, boundary, tzinfo=self._tz)
            if self._is_weekday(day) and candidate > local:
                return (
                    candidate.astimezone(timezone.utc) - local.astimezone(timezone.utc)
                ).total_seconds()
        # Unreachable for a sane config (a trading day always lies within 8 days).
        raise ValueError(f"no {target.name} boundary within 8 days of {local!r}")

    def market_is_open(self, now: datetime) -> bool:
        """Whether the market is actually open at ``now`` — reuses the P3 predicate.

        Delegates to ``external_data.market_hours.is_market_open`` (Decision 2: do
        not reimplement market hours). Imported lazily so the hot classification path
        and ``import scheduler.clock`` stay stdlib-only / import-light; the runtime
        guard that calls this runs in the daemon where P3 (and pandas) is loaded
        anyway. ``now`` is passed tz-aware so the P3-side ``astimezone`` is exact.
        """
        from external_data.market_hours import is_market_open

        return is_market_open(self._to_zone(now))

    # --- internals ---------------------------------------------------------

    def _to_zone(self, dt: datetime) -> datetime:
        """Return ``dt`` as a tz-aware datetime in ``config.tz``.

        Aware input is converted with ``astimezone``; a naive input is assumed to
        already be in ``config.tz`` (the P5 ``gate_time_window`` convention) and is
        tagged with the zone so downstream arithmetic is well-defined.
        """
        if dt.tzinfo is not None:
            return dt.astimezone(self._tz)
        return dt.replace(tzinfo=self._tz)

    @staticmethod
    def _is_weekday(d: date) -> bool:
        """Mon–Fri. v1 trading-day proxy — no holiday calendar (see module docstring)."""
        return d.weekday() < 5

    def _is_trading_day(self, local: datetime) -> bool:
        return self._is_weekday(local.date())

    def _pre_open_time(self) -> time:
        """``window_open`` minus ``pre_open_lead_min`` as a time-of-day.

        Computed on a reference date then projected back to a ``time``; assumes the
        lead does not cross midnight (true for any realistic open such as 09:00).
        """
        ref = datetime.combine(date(2000, 1, 1), self._window_open)
        return (ref - timedelta(minutes=self._config.pre_open_lead_min)).time()

    def _boundary_time(self, target: Phase) -> time:
        """The time-of-day at which ``target`` begins on a trading day."""
        if target is Phase.WINDOW:
            return self._window_open
        if target is Phase.PRE_OPEN:
            return self._pre_open_time()
        if target is Phase.POST_WINDOW:
            return self._window_close
        raise ValueError(f"{target.name} has no single start time")
