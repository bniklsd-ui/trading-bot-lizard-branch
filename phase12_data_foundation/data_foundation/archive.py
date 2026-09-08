"""``BarArchive`` — own-connection SQLite store for ``data/bars.sqlite`` (D4).

Every bar ever fetched from any source (IG, yFinance, later Lightstreamer) lands
here, write-through, with provenance (``source``) — so measurements become
replayable and offline-auditable (§0 BLUF, D9). A separate physical file from
``data/trading_bot.sqlite``: write load is isolated from the Phase-2 DB's
locking, and archive maintenance never touches trading data (D4).

Owns its own ``sqlite3`` connection rather than importing
``phase2_persistence.persistence.Database`` — same phase-isolation reason
``phase9_universe.universe.store.UniverseStore`` documents for itself (D3).
"""

from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from data_foundation.exceptions import ArchiveError
from data_foundation.models import KNOWN_SOURCES, Bar

_CREATE_BARS = """
CREATE TABLE IF NOT EXISTS bars (
    epic        TEXT NOT NULL,
    resolution  TEXT NOT NULL,
    ts_utc      TEXT NOT NULL,
    open REAL NOT NULL, high REAL NOT NULL, low REAL NOT NULL, close REAL NOT NULL,
    volume      REAL,
    source      TEXT NOT NULL,
    fetched_at  TEXT NOT NULL,
    tick_count  INTEGER,
    PRIMARY KEY (epic, resolution, ts_utc, source)
)
"""
_CREATE_BARS_INDEX = (
    "CREATE INDEX IF NOT EXISTS idx_bars_epic_res_ts ON bars(epic, resolution, ts_utc)"
)
# source_spend / allowance_observations live in the same physical file (§4.1) so
# a single BarArchive.ensure_schema() call provisions the whole bars.sqlite —
# SourceBudget (Step 2) opens its own connection to the same file and re-issues
# the same idempotent DDL, so either class can be instantiated first in tests.
_CREATE_SOURCE_SPEND = """
CREATE TABLE IF NOT EXISTS source_spend (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    ts_utc TEXT NOT NULL,
    points INTEGER NOT NULL,
    kind   TEXT NOT NULL
)
"""
_CREATE_ALLOWANCE_OBSERVATIONS = """
CREATE TABLE IF NOT EXISTS allowance_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observed_at TEXT NOT NULL,
    total INTEGER, remaining INTEGER, expiry TEXT
)
"""

# Phase-3-side resolution names -> seconds (naive granularity, no trading-session
# awareness — used only by coverage_ratio's expected-bar-count estimate, §6 Step 1).
_RESOLUTION_SECONDS: dict[str, int] = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "1h": 3600,
    "1d": 86400,
}


class BarArchive:
    """SQLite-backed write-through bar archive (D4/D9, §4.1 schema)."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        # J1 (Phase 16 §3): the connection is shared by multiple threads
        # (Recorder writes yF bars from the yF-thread, the Lightstreamer-Listener-
        # Thread writes ``source='ls'`` bars from ``stream.py:498``). ``check_same_thread=False``
        # permits the cross-thread use; the ``threading.Lock`` below serializes every
        # DB-touching method so concurrent writers don't corrupt the cursor. See the
        # ``commit``-message body and ``PHASE16_F_EXEC_PLAN.md`` §3 J1 for the live
        # evidence (63 942 ``ProgrammingError`` on 2026-09-08 alone; ``bars.source='ls'`` = 0
        # since the table existed).
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()

    def close(self) -> None:
        # NOTE: ``close()`` invalidates ``self.conn`` for every other thread holding the lock.
        # Today this is only called at shutdown (Recorder + Scheduler tear-down), so no other
        # writer races the close. If a future caller adds an in-flight ``close()``, it must
        # join all writer threads first — the lock alone doesn't protect against the
        # post-close use-after-free on a different thread.
        with self._lock:
            self.conn.close()

    def ensure_schema(self) -> None:
        """Create all three ``bars.sqlite`` tables if they don't exist yet (idempotent)."""
        with self._lock:
            self.conn.execute(_CREATE_BARS)
            self.conn.execute(_CREATE_BARS_INDEX)
            self.conn.execute(_CREATE_SOURCE_SPEND)
            self.conn.execute(_CREATE_ALLOWANCE_OBSERVATIONS)
            # Phase 13 §6 A5: idempotent column add for tick_count. A naked ALTER
            # would raise on the second run; the PRAGMA check makes it a no-op.
            cols = {r[1] for r in self.conn.execute("PRAGMA table_info(bars)").fetchall()}
            if "tick_count" not in cols:
                self.conn.execute("ALTER TABLE bars ADD COLUMN tick_count INTEGER")
            self.conn.commit()

    # -- writes -----------------------------------------------------------

    def insert_bars(self, bars: Sequence[Bar]) -> int:
        """Write-through insert, deduped on the ``(epic, resolution, ts_utc, source)``
        primary key (``INSERT OR IGNORE`` — a re-fetched identical bar is a no-op).

        Args:
            bars: bars to persist (``ts_utc``/``fetched_at`` already normalized).

        Returns:
            The number of genuinely new rows written (not re-inserted duplicates).

        Raises:
            ArchiveError: any bar carries an unknown ``source`` string. Validated
                up front (before any row is written) so a bad bar mid-batch can't
                leave an open, uncommitted transaction holding earlier inserts —
                the whole call is atomic: all bars land, or none do.
        """
        for bar in bars:
            if bar.source not in KNOWN_SOURCES:
                raise ArchiveError(
                    f"unknown bar source {bar.source!r} (known: {sorted(KNOWN_SOURCES)})"
                )
        new_count = 0
        with self._lock:
            for bar in bars:
                cur = self.conn.execute(
                    "INSERT OR IGNORE INTO bars "
                    "(epic, resolution, ts_utc, open, high, low, close, volume, source, fetched_at, tick_count) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        bar.epic, bar.resolution, bar.ts_utc,
                        bar.open, bar.high, bar.low, bar.close, bar.volume,
                        bar.source, bar.fetched_at, bar.tick_count,
                    ),
                )
                new_count += cur.rowcount
            self.conn.commit()
        return new_count

    # -- reads --------------------------------------------------------------

    def window(
        self,
        epic: str,
        resolution: str,
        start_utc: str,
        end_utc: str,
        *,
        prefer: tuple[str, ...] = ("ig", "capital", "ls", "yf"),
        sources: tuple[str, ...] | None = None,
    ) -> list[Bar]:
        """Return one ``Bar`` per distinct ``ts_utc`` in ``[start_utc, end_utc)``
        (start inclusive, end exclusive — avoids double-counting at adjacent-window
        boundaries).

        When multiple sources cover the same minute, the first source in ``prefer``
        wins (default: IG real-time beats a Lightstreamer mitschrieb beats yFinance).

        ``sources`` (Phase 13 §6 A5, L10): when set, the SQL ``WHERE`` is filtered
        to that source *before* the ``prefer`` ranking — so a quellenrein (single-
        source) read is possible without callers having to re-filter the result.
        Sample use: ``archive.window(epic, "1m", start, end, sources=("yf",))``
        feeds the source-delta report + the (repaired) divergence sampler without
        leakage from IG rows.
        """
        if sources is not None:
            placeholders = ",".join("?" for _ in sources)
            with self._lock:
                rows = self.conn.execute(
                    f"SELECT * FROM bars WHERE epic = ? AND resolution = ? "
                    f"AND ts_utc >= ? AND ts_utc < ? AND source IN ({placeholders}) "
                    f"ORDER BY ts_utc ASC",
                    (epic, resolution, start_utc, end_utc, *sources),
                ).fetchall()
        else:
            with self._lock:
                rows = self.conn.execute(
                    "SELECT * FROM bars WHERE epic = ? AND resolution = ? "
                    "AND ts_utc >= ? AND ts_utc < ? ORDER BY ts_utc ASC",
                    (epic, resolution, start_utc, end_utc),
                ).fetchall()
        by_ts: dict[str, sqlite3.Row] = {}
        rank = {src: i for i, src in enumerate(prefer)}
        default_rank = len(prefer)
        for row in rows:
            existing = by_ts.get(row["ts_utc"])
            if existing is None or rank.get(row["source"], default_rank) < rank.get(
                existing["source"], default_rank
            ):
                by_ts[row["ts_utc"]] = row
        return [
            Bar(
                epic=row["epic"], resolution=row["resolution"], ts_utc=row["ts_utc"],
                open=row["open"], high=row["high"], low=row["low"], close=row["close"],
                volume=row["volume"], source=row["source"], fetched_at=row["fetched_at"],
                tick_count=row["tick_count"] if "tick_count" in row.keys() else None,
            )
            for row in sorted(by_ts.values(), key=lambda r: r["ts_utc"])
        ]

    def coverage_ratio(self, epic: str, resolution: str, start_utc: str, end_utc: str) -> float:
        """Distinct present bar-minutes / naively-expected bar count in the window.

        Naive: assumes continuous trading with no session gaps (documented
        limitation, §6 Step 1) — a genuinely closed market reads as "missing
        coverage", which is fine for its only consumer (the Recorder heartbeat,
        Step 6) since a closed market also produces zero real bars either way.

        No ``with self._lock`` here: ``self.window()`` already holds it, and
        the math below is pure-Python on the returned list — no shared state
        that another thread could race on.
        """
        present = len(self.window(epic, resolution, start_utc, end_utc))
        step = _RESOLUTION_SECONDS.get(resolution)
        if not step:
            raise ArchiveError(f"unknown resolution {resolution!r}")
        start_dt = _parse(start_utc)
        end_dt = _parse(end_utc)
        expected = max(0, int((end_dt - start_dt).total_seconds() // step))
        if expected == 0:
            return 0.0
        return min(1.0, present / expected)

    def latest_ts(self, epic: str, resolution: str) -> str | None:
        with self._lock:
            row = self.conn.execute(
                "SELECT MAX(ts_utc) AS latest FROM bars WHERE epic = ? AND resolution = ?",
                (epic, resolution),
            ).fetchone()
        return row["latest"] if row and row["latest"] is not None else None

    def bars_written_since(self, ts_utc: str, end_utc: str | None = None) -> int:
        """Count of distinct ``(epic, resolution, ts_utc)`` bars first observed in
        ``[ts_utc, end_utc)`` (by ``fetched_at``; ``end_utc=None`` ⇒ open-ended, "since
        forever after") — the Mess-Heartbeat's (Step 6) per-day activity counter.
        Distinct on purpose: the PK also includes ``source``, so a minute covered by
        both IG and yFinance must count once, not twice, in a health report.

        ``end_utc`` matters for ``assess_day``: without it, a query for a **past**
        day (``ts_utc`` = that day's start) would count every bar fetched from then
        until now, not just that day's — reporting a dead day as healthy.
        """
        if end_utc is None:
            with self._lock:
                row = self.conn.execute(
                    "SELECT COUNT(DISTINCT epic || '|' || resolution || '|' || ts_utc) AS n "
                    "FROM bars WHERE fetched_at >= ?",
                    (ts_utc,),
                ).fetchone()
        else:
            with self._lock:
                row = self.conn.execute(
                    "SELECT COUNT(DISTINCT epic || '|' || resolution || '|' || ts_utc) AS n "
                    "FROM bars WHERE fetched_at >= ? AND fetched_at < ?",
                    (ts_utc, end_utc),
                ).fetchone()
        return int(row["n"]) if row else 0


def _parse(ts_utc: str) -> datetime:
    normalized = ts_utc.replace("Z", "+00:00") if ts_utc.endswith("Z") else ts_utc
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
