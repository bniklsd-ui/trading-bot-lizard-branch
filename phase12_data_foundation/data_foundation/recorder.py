"""``Recorder`` — a standalone, yFinance-only process that keeps ``bars.sqlite`` warm
independent of the bot's own state (D14/D15).

**No IG session, ever** (D14): two concurrent IG REST logins clobber each other's
tokens (the parallel-login trap, ``reference_ig_parallel_login_trap`` memory). All
IG-side traffic (divergence samples, probes, the tracker's IG top-up) stays inside the
scheduler process, which holds the one warm session. The Recorder only ever calls a
Phase-3 ``fetcher.get_bars`` closure (yFinance) — never ``broker_wrapper``.

Runs standalone (``python -m data_foundation.run``, warms the archive ahead of a bot
restart) and automatically alongside the scheduler (``run_scheduler.sh``, D14 — "damit
es weniger schnell vergessen wird").
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from data_foundation.models import SOURCE_YF, Bar, normalize_bar_ts

logger = logging.getLogger("data_foundation.recorder")


@dataclass
class RecorderReport:
    epics: int
    bars_written: int
    skipped_off_hours: bool
    errors: list[str] = field(default_factory=list)


def _default_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def _default_market_open() -> bool:
    from external_data.market_hours import is_market_open

    return is_market_open()


# P14-E plan §2 D2: cap the between-cycle sleep so SIGTERM is honored within at most
# this many seconds (analog to P14-D for the Discovery daemon, and to Phase-8's
# POST_WINDOW idle_poll_s hotfix 2026-07-11). Default 60s ≪ interval_s=300 default,
# so a stop is responsive without hammering the loop. Testable via the same
# _sleep_fn injection as the cycle sleep itself.
_DEFAULT_SIGNAL_CHECK_INTERVAL_S = 60


class Recorder:
    """Polls ``epics_fn()``'s epics for fresh bars and write-throughs them (D15).

    ``get_bars`` is a Phase-3 ``fetcher.get_bars``-shaped closure
    (``get_bars(epic, resolution=..., count=...) -> list[PriceBar] | None``) — the
    caller builds and injects it (lazily, so this module never imports
    ``external_data`` at module top, mirroring the rest of the package's phase
    isolation). ``epics_fn`` likewise stays a plain closure so ownership of its
    (read-mostly) DB connection is the caller's, not this class's.
    """

    def __init__(
        self,
        archive: Any,
        get_bars: Callable[..., Any],
        epics_fn: Callable[[], list[str]],
        *,
        resolution: str = "1m",
        count: int = 30,
        interval_s: int = 300,
        signal_check_interval_s: int = _DEFAULT_SIGNAL_CHECK_INTERVAL_S,
        state_path: str = "data/state/recorder_state.json",
        health_sink: Callable[[dict], None] | None = None,
        market_open_fn: Callable[[], bool] = _default_market_open,
        now_fn: Callable[[], datetime] = _default_now,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        self._archive = archive
        self._get_bars = get_bars
        self._epics_fn = epics_fn
        self._resolution = resolution
        self._count = count
        self._interval_s = interval_s
        self._signal_check_interval_s = signal_check_interval_s
        self._state_path = Path(state_path)
        self._health_sink = health_sink
        self._market_open_fn = market_open_fn
        self._now_fn = now_fn
        self._sleep_fn = sleep_fn
        self._stop_requested = False

    def _emit(self, event: dict[str, Any]) -> None:
        if self._health_sink is None:
            return
        try:
            self._health_sink(event)
        except Exception:  # noqa: BLE001 — a health sink must never break the tick
            pass

    def tick(self) -> RecorderReport:
        """One poll cycle: fail-soft per epic, never raises.

        Off-hours (``market_open_fn() is False``) is a no-op report — no fetch
        attempted for any epic (yFinance intraday would return empty anyway, this
        just skips the wasted call). Overlap across ticks is deduped for free by
        the archive's own primary key (``INSERT OR IGNORE``, no logic needed here).
        """
        epics = list(self._epics_fn())
        now = self._now_fn()

        if not self._market_open_fn():
            report = RecorderReport(epics=len(epics), bars_written=0, skipped_off_hours=True)
            self._finish(report, now)
            return report

        bars_written = 0
        errors: list[str] = []
        for epic in epics:
            try:
                bars = self._get_bars(epic, resolution=self._resolution, count=self._count)
            except Exception as exc:  # noqa: BLE001 — one epic's failure must not stop the tick
                errors.append(f"{epic}: {exc}")
                continue
            if not bars:
                continue
            fetched_at = _iso(now)
            archive_bars = [
                Bar(
                    epic=epic, resolution=self._resolution, ts_utc=normalize_bar_ts(b.ts),
                    open=b.open, high=b.high, low=b.low, close=b.close, volume=b.volume,
                    source=SOURCE_YF, fetched_at=fetched_at,
                )
                for b in bars
            ]
            try:
                bars_written += self._archive.insert_bars(archive_bars)
            except Exception as exc:  # noqa: BLE001 — same fail-soft discipline
                errors.append(f"{epic}: archive write failed: {exc}")

        report = RecorderReport(
            epics=len(epics), bars_written=bars_written, skipped_off_hours=False, errors=errors
        )
        self._finish(report, now)
        return report

    def _finish(self, report: RecorderReport, now: datetime) -> None:
        self._write_state(report, now)
        self._emit({
            "event": "recorder_heartbeat",
            "epics": report.epics,
            "bars_written": report.bars_written,
            "skipped_off_hours": report.skipped_off_hours,
            "errors": len(report.errors),
        })

    def _write_state(self, report: RecorderReport, now: datetime) -> None:
        """Atomically write the heartbeat state (``.tmp`` + ``os.replace`` — the P8
        ``StateStore.save`` pattern, copied not imported, D3 phase-isolation)."""
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "ts": _iso(now),
            "epics": report.epics,
            "bars_written": report.bars_written,
            "skipped_off_hours": report.skipped_off_hours,
            "errors": report.errors,
        }
        tmp = self._state_path.with_suffix(self._state_path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, self._state_path)

    def run_forever(self) -> None:
        """Tick, then sleep ``interval_s``, until :meth:`request_stop`.

        A tick that raises is logged and swallowed (``tick()`` itself is already
        fail-soft per epic; this is only a backstop against a bug in the loop
        plumbing itself) — the loop must survive one bad iteration, exactly like
        every other P8 daemon loop in this repo.

        The between-cycle sleep is **capped** at ``signal_check_interval_s``
        (P14-E plan D2, analog to Phase-8 POST_WINDOW hotfix 2026-07-11 and to
        P14-D for the Discovery daemon): without the cap, ``time.sleep(interval_s)``
        blocks SIGTERM for up to ``interval_s`` seconds (Python PEP 475 retries
        interrupted syscalls; the ``self._stop_requested`` flag is only checked
        at the top of each iteration). With the cap, a Ctrl+C / SIGTERM during
        sleep is honored within at most ``signal_check_interval_s`` seconds.
        """
        while not self._stop_requested:
            try:
                self.tick()
            except Exception:  # noqa: BLE001 — the loop must outlive one bad tick
                logger.exception("Recorder tick failed")
            if self._stop_requested:
                break
            self._sleep_capped(float(self._interval_s))

    def _sleep_capped(self, total_s: float) -> None:
        """Sleep ``total_s`` in chunks of at most ``signal_check_interval_s``.

        Each chunk re-checks ``self._stop_requested`` so a SIGTERM /
        :meth:`request_stop` during sleep short-circuits the loop within at most
        one chunk. Mirrors the POST_WINDOW fix pattern: ``min(seconds_until(...),
        idle_poll_s)`` (Phase 8, 2026-07-11). P14-D applies the same shape to the
        Discovery daemon; Phase 15 will consolidate the two into a shared helper
        module.
        """
        remaining = max(0.0, float(total_s))
        chunk = min(remaining, float(self._signal_check_interval_s))
        while remaining > 0.0 and not self._stop_requested:
            sleep_for = min(chunk, remaining)
            self._sleep_fn(sleep_for)
            remaining -= sleep_for

    def request_stop(self) -> None:
        self._stop_requested = True
