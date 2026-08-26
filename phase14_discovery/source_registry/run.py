"""``python -m source_registry.run`` — Phase-14 Discovery daemon (Plan §6 C2).

PID-file-guarded (``data/state/discovery.pid`` by default), so it's double-start-safe
whether launched by hand or from ``scripts/run_discovery.sh`` (C4): if the file names a
still-living process, this exits 0 immediately with a message instead of running a
second Discovery against the same DB. ``SIGTERM``/``SIGINT`` both map to
:meth:`DiscoveryDaemon.request_stop` — a graceful stop, not a hard kill mid-write
(mirrors ``phase12_data_foundation/data_foundation/run.py``).

The loop is the *safe-default-False* design (D10) the Plan calls out: the very first
action every cycle is :func:`source_registry.arm.is_armed` — if the flag file is
absent, empty, broken, or carries any value other than a literal JSON ``True``, the
daemon **does nothing** (no DB read, no network, no log beyond a single debug tick).
This is the structural answer to "how do we prevent Discovery from running
unattended"? The flag file is the gate; the UI's ARM button is the only documented
way to set it (operators may also ``touch`` it by hand, the file is readable).

A second gate sits below that: the daemon only does real work when the
``instrument_source_availability`` table carries rows whose
``last_verified_utc`` is older than ``profile_ttl_days`` (Plan D14, default 7 days).
A fresh table ⇒ sleep. No stale rows ⇒ no ``discover()`` calls. The point is to
make "no work to do" the cheap, common path, not the exception.

When there IS work, every configured :class:`~source_registry.models.Source` is asked
in turn — ``IGDerivedSource``, ``LSStaticSource``, ``RegistryYFSource`` are net-free
by construction (they emit zero ``probe_calls_used``); Capital.com is the only
Source that may book against the existing ``source_spend`` ledger under
``spend_kind='discovery'``. A raising source is captured into ``SourceProfile.errors``
and does **not** kill the cycle (Plan §8.5: "one bad row must not kill the whole
Discovery cycle").

State is written to ``data/state/discovery_state.json`` (atomic ``.tmp`` + ``os.replace``)
on every cycle — the file is the only way an operator can read "what did the last
cycle do?" without grepping logs. The format mirrors ``recorder_state.json`` (the
Daemon-Health-Format from Phase 12 ``data_health.py:36-44``), so a future
``/api/discovery`` reader doesn't need a parser per consumer.

Stdlib-only + Phase-12 ``SourceBudget`` (lazy) + Phase-9 ``UniverseStore`` (lazy).
Repo conventions: ``from __future__ import annotations``, type hints + docstrings,
no network in tests, one module = one responsibility.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

from source_registry.arm import DEFAULT_ARM_PATH, is_armed
from source_registry.models import Source

logger = logging.getLogger("source_registry.run")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_PID_PATH = _REPO_ROOT / "data" / "state" / "discovery.pid"
_DEFAULT_STATE_PATH = _REPO_ROOT / "data" / "state" / "discovery_state.json"
_DEFAULT_UNIVERSE_DB_PATH = _REPO_ROOT / "data" / "trading_bot.sqlite"
_DEFAULT_BARS_DB_PATH = _REPO_ROOT / "data" / "bars.sqlite"
# Plan §4 D13/D14: 8 Probe-Calls max pro Run, 7-Tage-TTL als Stale-Schwelle.
_DEFAULT_MAX_PROBE_CALLS_PER_RUN = 8
_DEFAULT_PROFILE_TTL_DAYS = 7
# P14-D plan §2 D2: cap the between-cycle sleep so SIGTERM is honored within
# at most this many seconds (analog to Phase-8 idle_poll_s, 2026-07-11 hotfix).
# Default 60s ≪ interval_s=3600 default, so a stop is responsive without
# hammering the loop. Testable via the same _sleep_fn injection as the cycle
# sleep itself.
_DEFAULT_SIGNAL_CHECK_INTERVAL_S = 60


# ---------------------------------------------------------------------------
# PID-file helpers (verbatim pattern from data_foundation/run.py:39-53).
# ---------------------------------------------------------------------------


def _pid_alive(pid: int) -> bool:
    """Whether a process with this PID exists (signal 0 — no actual kill)."""
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _already_running(pid_path: Path) -> bool:
    if not pid_path.exists():
        return False
    try:
        pid = int(pid_path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return False
    return _pid_alive(pid)


def _write_pid(pid_path: Path) -> None:
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = pid_path.with_suffix(pid_path.suffix + ".tmp")
    tmp.write_text(str(os.getpid()), encoding="utf-8")
    os.replace(tmp, pid_path)


def _clear_pid(pid_path: Path) -> None:
    try:
        pid_path.unlink()
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Cycle result + state-file writer.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CycleResult:
    """The outcome of one Discovery cycle — written verbatim into the state file.

    Field set is the smallest subset that lets the operator see "what happened"
    without grepping logs: when, armed-or-not, how many stale rows drove the cycle,
    how many rows were written back, how many errors (per source) were tolerated.
    """

    ts_utc: str
    armed: bool
    stale_count: int
    rows_written: int
    errors: tuple[str, ...] = field(default_factory=tuple)


def _write_state(state_path: Path, result: CycleResult) -> None:
    """Atomic JSON write of one ``CycleResult`` (matches recorder_state.json shape)."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ts_utc": result.ts_utc,
        "armed": result.armed,
        "stale_count": result.stale_count,
        "rows_written": result.rows_written,
        "errors": list(result.errors),
    }
    tmp = state_path.with_suffix(state_path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(tmp, state_path)


# ---------------------------------------------------------------------------
# The daemon — testable without CLI / signals / PID.
# ---------------------------------------------------------------------------


class DiscoveryDaemon:
    """The Discovery cycle. One instance per process; not thread-safe (one loop, one state)."""

    def __init__(
        self,
        *,
        sources: Sequence[Source],
        universe_store: Any,             # duck-typed: needs .list_by_status(...)
        availability_store: Any,          # duck-typed: needs .stale_rows/.upsert_many
        budget: Any | None = None,       # duck-typed: needs .record_spend(points, kind)
        arm_path: str = str(DEFAULT_ARM_PATH),
        state_path: str = str(_DEFAULT_STATE_PATH),
        interval_s: int = 3600,
        signal_check_interval_s: int = _DEFAULT_SIGNAL_CHECK_INTERVAL_S,
        max_probe_calls_per_run: int = _DEFAULT_MAX_PROBE_CALLS_PER_RUN,
        profile_ttl_days: int = _DEFAULT_PROFILE_TTL_DAYS,
        now_fn: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        self._sources = tuple(sources)
        self._universe_store = universe_store
        self._availability_store = availability_store
        self._budget = budget
        self._arm_path = arm_path
        self._state_path = Path(state_path)
        self._interval_s = interval_s
        self._signal_check_interval_s = signal_check_interval_s
        self._max_probe_calls = max_probe_calls_per_run
        self._profile_ttl_days = profile_ttl_days
        self._now_fn = now_fn
        self._sleep_fn = sleep_fn
        self._stop = False

    def request_stop(self) -> None:
        """Signal handler / CLI hook — ask the loop to exit at the next iteration boundary."""
        self._stop = True

    def run_once(self) -> CycleResult:
        """One cycle: arm-check → stale-check → per-source discover → write state.

        Fail-soft by design: a raising ``discover`` lands in ``errors``, never bubbles
        out of this method. The operator's last-cycle view (state file) is therefore
        always written, even on partial failure.
        """
        ts_utc = _iso(self._now_fn())
        armed = is_armed(self._arm_path)

        if not armed:
            result = CycleResult(ts_utc=ts_utc, armed=False, stale_count=0, rows_written=0)
            _write_state(self._state_path, result)
            logger.debug("discovery cycle skipped: not armed")
            return result

        stale = self._availability_store.stale_rows(ttl_days=self._profile_ttl_days)
        if not stale:
            result = CycleResult(ts_utc=ts_utc, armed=True, stale_count=0, rows_written=0)
            _write_state(self._state_path, result)
            logger.debug("discovery cycle skipped: nothing stale (ttl=%d days)", self._profile_ttl_days)
            return result

        # Plan §6 C2 step 3: pull the epic list from the universe (active + discovered).
        # ``stale`` rows are *availability* rows — they tell us "what needs re-checking";
        # the actual epic list comes from the universe so we don't accidentally target
        # epics the universe has already retired.
        universe_records = self._universe_store.list_by_status("active", "discovered")
        epics = [rec.epic for rec in universe_records]

        rows_written = 0
        errors: list[str] = []
        total_probe_calls = 0

        for source in self._sources:
            try:
                profile = source.discover(epics, max_probe_calls=self._max_probe_calls)
            except Exception as exc:  # noqa: BLE001 — Plan §8.5: never let one bad source kill the cycle
                errors.append(f"{source.name()}: discover raised: {exc}")
                continue
            errors.extend(f"{source.name()}: {err}" for err in profile.errors)
            total_probe_calls += profile.probe_calls_used
            try:
                rows_written += self._availability_store.upsert_many(profile.rows)
            except Exception as exc:  # noqa: BLE001 — fail-soft: DB-Wackler killt nicht den Cycle
                errors.append(f"{source.name()}: upsert_many raised: {exc}")

        if total_probe_calls > 0 and self._budget is not None:
            try:
                self._budget.record_spend(total_probe_calls, kind="discovery")
            except Exception as exc:  # noqa: BLE001 — ledger-Wackler blockt nicht die Discovery selbst
                errors.append(f"budget.record_spend raised: {exc}")

        result = CycleResult(
            ts_utc=ts_utc,
            armed=True,
            stale_count=len(stale),
            rows_written=rows_written,
            errors=tuple(errors),
        )
        _write_state(self._state_path, result)
        return result

    def run_forever(self) -> None:
        """Loop ``run_once`` until :meth:`request_stop` is called.

        The between-cycle sleep is **capped** at ``signal_check_interval_s``
        (D2, analog Phase-8 POST_WINDOW hotfix 2026-07-11) — without the cap,
        ``time.sleep(interval_s)`` blocks SIGTERM for up to ``interval_s``
        seconds (Python PEP 475 retries interrupted syscalls until they
        complete; the ``self._stop`` flag is only checked at the top of each
        iteration). With the cap, a Ctrl+C / SIGTERM during sleep is honored
        within at most ``signal_check_interval_s`` seconds — same guarantee
        as ``phase8_scheduler.scheduler.runner``'s POST_WINDOW cap.
        """
        while not self._stop:
            self.run_once()
            if self._stop:
                break
            self._sleep_capped(float(self._interval_s))

    def _sleep_capped(self, total_s: float) -> None:
        """Sleep ``total_s`` in chunks of at most ``signal_check_interval_s``.

        Each chunk re-checks ``self._stop`` so a SIGTERM / request_stop()
        during sleep short-circuits the loop within at most one chunk.
        Mirrors the POST_WINDOW fix pattern: ``min(seconds_until(...), idle_poll_s)``
        — but here we loop because the total is bounded, not a target time.
        """
        chunk_s = min(total_s, float(self._signal_check_interval_s))
        elapsed = 0.0
        while elapsed < total_s and not self._stop:
            remaining = total_s - elapsed
            self._sleep_fn(min(remaining, chunk_s))
            elapsed += chunk_s


# ---------------------------------------------------------------------------
# CLI / PID / signal wiring (mirrors data_foundation/run.py:110-156).
# ---------------------------------------------------------------------------


def _build_default_sources(universe_store: Any) -> tuple[Source, ...]:
    """The three net-free Phase-14 sources in canonical order.

    Order matters for the cycle-result ``errors`` field (read top-to-bottom by the
    operator); IG-derived first because it's the cheapest, LS second (static),
    yF-third (DB projection). Capital.com lives in Phase-13 ``backfill.py`` per the
    freigegebene Cross-Phase-Liste 2026-08-22 and is **not** part of the default
    source set here — adding it would import Phase-13 modules and pull the daemon
    onto a network path. Future Block D can compose a richer default.
    """
    from source_registry.sources import (
        IGDerivedSource,
        LSStaticSource,
        RegistryYFSource,
    )

    return (
        IGDerivedSource(),
        LSStaticSource(),
        RegistryYFSource(universe_store),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase-14 Discovery daemon — re-verifies source availability on a TTL."
    )
    parser.add_argument("--pid-file", default=str(_DEFAULT_PID_PATH))
    parser.add_argument("--state-path", default=str(_DEFAULT_STATE_PATH))
    parser.add_argument("--universe-db", default=str(_DEFAULT_UNIVERSE_DB_PATH))
    parser.add_argument("--bars-db", default=str(_DEFAULT_BARS_DB_PATH))
    parser.add_argument("--arm-file", default=str(DEFAULT_ARM_PATH))
    parser.add_argument("--interval-s", type=int, default=3600)
    parser.add_argument("--max-probe-calls-per-run", type=int,
                        default=_DEFAULT_MAX_PROBE_CALLS_PER_RUN)
    parser.add_argument("--profile-ttl-days", type=int, default=_DEFAULT_PROFILE_TTL_DAYS)
    parser.add_argument("--once", action="store_true",
                        help="run a single cycle and exit (operator mode).")
    args = parser.parse_args(argv)

    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    pid_path = Path(args.pid_file)
    if _already_running(pid_path):
        print(f"Discovery daemon already running (pid file {pid_path}) — exiting.",
              file=sys.stderr)
        return 0

    _write_pid(pid_path)

    # Lazy cross-phase imports: Phase-9 UniverseStore (DB owner), Phase-14 own
    # SourceAvailabilityStore, Phase-12 SourceBudget (only when --bars-db is set
    # AND a future source actually books spend — default sources never do).
    from universe.store import UniverseStore
    from source_registry.store import SourceAvailabilityStore
    from data_foundation.budget import SourceBudget, IG_QUOTA_V1

    universe_store = UniverseStore(args.universe_db)
    availability_store = SourceAvailabilityStore(args.universe_db)
    try:
        budget = SourceBudget(args.bars_db, IG_QUOTA_V1)
    except Exception as exc:  # noqa: BLE001 — budget is best-effort; default sources never book
        logger.warning("SourceBudget unavailable (%s) — discovery will run without ledger.", exc)
        budget = None

    sources = _build_default_sources(universe_store)

    daemon = DiscoveryDaemon(
        sources=sources,
        universe_store=universe_store,
        availability_store=availability_store,
        budget=budget,
        arm_path=args.arm_file,
        state_path=args.state_path,
        interval_s=args.interval_s,
        max_probe_calls_per_run=args.max_probe_calls_per_run,
        profile_ttl_days=args.profile_ttl_days,
    )

    def _handle_signal(signum: int, frame: Any) -> None:
        logger.info("Discovery daemon received signal %s — stopping.", signum)
        daemon.request_stop()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    try:
        if args.once:
            daemon.run_once()
        else:
            daemon.run_forever()
    finally:
        _clear_pid(pid_path)
        try:
            universe_store.close()
        except Exception:  # noqa: BLE001
            pass
        try:
            availability_store.close()
        except Exception:  # noqa: BLE001
            pass
        if budget is not None:
            try:
                budget.close()
            except Exception:  # noqa: BLE001
                pass

    return 0


def _iso(dt: datetime) -> str:
    """UTC ISO-8601 with millisecond precision and explicit ``Z`` suffix — the
    format ``SourceAvailabilityStore.stale_rows`` expects for lexicographic
    comparison (the canary test in §6 A2 guards against drift here)."""
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


if __name__ == "__main__":
    raise SystemExit(main())
