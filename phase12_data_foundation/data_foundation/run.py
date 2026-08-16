"""``python -m data_foundation.run`` — standalone entrypoint for the Recorder (D14).

PID-file-guarded (``data/state/recorder.pid``) so it's double-start-safe whether
launched by hand or from ``phase8_scheduler/scripts/run_scheduler.sh``: if the file
names a still-living process, this exits 0 immediately with a message instead of
running a second Recorder against the same archive. ``SIGTERM``/``SIGINT`` both map to
:meth:`Recorder.request_stop` — a graceful stop, not a hard kill mid-write.
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger("data_foundation.run")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_PID_PATH = _REPO_ROOT / "data" / "state" / "recorder.pid"
_DEFAULT_STATE_PATH = _REPO_ROOT / "data" / "state" / "recorder_state.json"
_DEFAULT_UNIVERSE_DB_PATH = _REPO_ROOT / "data" / "trading_bot.sqlite"
_DEFAULT_BARS_DB_PATH = _REPO_ROOT / "data" / "bars.sqlite"
_DEFAULT_CACHE_DIR = _REPO_ROOT / "data" / "cache"


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


def _build_recorder(
    *,
    universe_db_path: str,
    bars_db_path: str,
    cache_dir: str,
    state_path: str,
    interval_s: int,
) -> Any:
    """Lazy-wire the real Recorder — yFinance + the archive, no broker import ever.

    A bare ``TickerMapper()`` only knows its ~7 static entries (P3's own smoke-test
    shape) — it never learns a registry-resolved ``yf_ticker`` (D5/D6, Phase-12 Step
    3) on its own. Mirrors the scheduler's own wiring
    (``phase8_scheduler/scripts/wiring.py::_build_market_data``, ``mapper.register``):
    ``epics_fn`` registers each measurable epic's ``yf_ticker`` onto the shared mapper
    every call, so an epic the resolver verifies mid-run becomes fetchable on the very
    next tick without a Recorder restart.
    """
    from data_foundation.archive import BarArchive
    from data_foundation.recorder import Recorder
    from external_data.cache import FileCache
    from external_data.fetcher import MarketDataFetcher
    from external_data.ticker_map import TickerMapper

    archive = BarArchive(bars_db_path)
    archive.ensure_schema()
    mapper = TickerMapper()
    fetcher = MarketDataFetcher(mapper, FileCache(cache_dir))

    def epics_fn() -> list[str]:
        from universe.store import UniverseStore

        store = UniverseStore(universe_db_path)
        try:
            records = store.measurable_universe()
        finally:
            store.close()
        epics = []
        for rec in records:
            if not rec.yf_ticker:
                continue
            mapper.register(rec.epic, rec.yf_ticker)
            epics.append(rec.epic)
        return epics

    return Recorder(
        archive,
        fetcher.get_bars,
        epics_fn,
        interval_s=interval_s,
        state_path=state_path,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase-12 Recorder — yFinance-only bar-archive writer (D14/D15)."
    )
    parser.add_argument("--pid-file", default=str(_DEFAULT_PID_PATH))
    parser.add_argument("--state-path", default=str(_DEFAULT_STATE_PATH))
    parser.add_argument("--universe-db", default=str(_DEFAULT_UNIVERSE_DB_PATH))
    parser.add_argument("--bars-db", default=str(_DEFAULT_BARS_DB_PATH))
    parser.add_argument("--cache-dir", default=str(_DEFAULT_CACHE_DIR))
    parser.add_argument("--interval-s", type=int, default=300)
    args = parser.parse_args(argv)

    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    pid_path = Path(args.pid_file)
    if _already_running(pid_path):
        print(f"Recorder already running (pid file {pid_path}) — exiting.", file=sys.stderr)
        return 0

    _write_pid(pid_path)
    recorder = _build_recorder(
        universe_db_path=args.universe_db,
        bars_db_path=args.bars_db,
        cache_dir=args.cache_dir,
        state_path=args.state_path,
        interval_s=args.interval_s,
    )

    def _handle_signal(signum: int, frame: Any) -> None:
        logger.info("Recorder received signal %s — stopping.", signum)
        recorder.request_stop()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    try:
        recorder.run_forever()
    finally:
        try:
            pid_path.unlink()
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
