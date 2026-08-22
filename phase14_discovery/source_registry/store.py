"""``SourceAvailabilityStore`` — SQLite CRUD for ``instrument_source_availability``
(Migration 007, Phase 14).

Owns its own ``sqlite3`` connection rather than importing
``phase2_persistence.persistence.Database`` (phase isolation — ``import
source_registry.store`` pulls in no cross-phase module; mirrors how
``phase9_universe/universe/store.py`` and ``phase12_data_foundation/data_foundation/archive.py``
each open their own connection to the shared DB file). It still points at the same
physical ``data/trading_bot.sqlite`` that Phase 2's migration runner already applies
migration 007 to — the *table* is shared, the *access code* is not.

``utc_iso_now`` is duplicated (not imported) from Phase 2's ``timeutil.py`` and
Phase 9's ``universe/store.py`` for the same phase-isolation reason documented there.

The store is intentionally narrow:
- :meth:`upsert` / :meth:`upsert_many` are the only write paths.
- Reads are the four query helpers (:meth:`for_epic`, :meth:`for_source`,
  :meth:`symbol_for`, :meth:`stale_rows`).
- Nothing else. There is no ``delete()`` — a stale row ages out via TTL-driven
  re-discovery, not via manual removal (Plan §8.5: never silently lose a row).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Sequence

from source_registry.models import SourceAvailability


def utc_iso_now() -> str:
    """Current UTC time as an ISO 8601 string with ms precision and Z suffix.

    Mirrors ``phase9_universe/universe/store.py:36`` and Phase 2's
    ``persistence.timeutil.utc_iso_now`` — duplicated for phase isolation (the
    Store must be importable without pulling in Phase 2 / Phase 9).

    Every timestamp this module writes (``upsert`` writes ``last_verified_utc``)
    goes through this function, which is the contract that makes
    :meth:`stale_rows`'s lexicographic comparison a valid chronological
    comparison (lexicographic == chronological when every string is written by
    the same formatter, repo-wide canonical format).
    """
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


def _row_to_availability(row: sqlite3.Row) -> SourceAvailability:
    """Map one ``SELECT * FROM instrument_source_availability`` row to the dataclass."""
    return SourceAvailability(
        epic=row["epic"],
        source=row["source"],
        resolution=row["resolution"],
        source_symbol=row["source_symbol"],
        status=row["status"],
        origin=row["origin"],
        history_min_days=row["history_min_days"],
        latency_min=row["latency_min"],
        last_verified_utc=row["last_verified_utc"],
        notes=row["notes"],
    )


class SourceAvailabilityStore:
    """SQLite-backed CRUD for the ``instrument_source_availability`` table.

    Migration 007 must already have run against ``db_path`` (Phase 2's
    ``Database.run_migrations()`` / ``run_migrations(conn, MIGRATIONS_DIR)`` —
    ``SourceAvailabilityStore`` never runs migrations itself, it only reads/writes
    the table the migration created).
    """

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self) -> None:
        self.conn.close()

    # -- writes -----------------------------------------------------------

    def upsert(self, row: SourceAvailability) -> None:
        """Insert one :class:`SourceAvailability` row, replacing any existing one
        with the same ``(epic, source, resolution)`` PK.

        The PK makes this naturally idempotent for the Discovery daemon — a
        re-run against the same epic touches the same row, no duplicates. Same
        ON CONFLICT shape as ``UniverseStore.upsert_discovered``
        (``phase9_universe/universe/store.py:130-137``).
        """
        self.conn.execute(
            "INSERT INTO instrument_source_availability "
            "(epic, source, resolution, source_symbol, status, origin, "
            "history_min_days, latency_min, last_verified_utc, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(epic, source, resolution) DO UPDATE SET "
            "source_symbol = excluded.source_symbol, "
            "status = excluded.status, "
            "origin = excluded.origin, "
            "history_min_days = excluded.history_min_days, "
            "latency_min = excluded.latency_min, "
            "last_verified_utc = excluded.last_verified_utc, "
            "notes = excluded.notes",
            (
                row.epic, row.source, row.resolution, row.source_symbol,
                row.status, row.origin, row.history_min_days, row.latency_min,
                row.last_verified_utc, row.notes,
            ),
        )
        self.conn.commit()

    def upsert_many(self, rows: Sequence[SourceAvailability]) -> int:
        """Insert / replace many rows in one transaction. Returns the number
        written (== ``len(rows)`` — duplicates on PK are still one row)."""
        count = 0
        for row in rows:
            self.upsert(row)
            count += 1
        return count

    # -- reads ------------------------------------------------------------

    def for_epic(
        self,
        epic: str,
        *,
        resolution: str | None = None,
    ) -> list[SourceAvailability]:
        """All rows for one epic, optionally filtered to one resolution.

        Default ordering: by ``source`` (deterministic across re-reads; no
        semantic ranking — D8 says the table is facts, not preference).
        """
        if resolution is None:
            rows = self.conn.execute(
                "SELECT * FROM instrument_source_availability "
                "WHERE epic = ? ORDER BY source ASC",
                (epic,),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM instrument_source_availability "
                "WHERE epic = ? AND resolution = ? ORDER BY source ASC",
                (epic, resolution),
            ).fetchall()
        return [_row_to_availability(r) for r in rows]

    def for_source(
        self,
        source: str,
        *,
        status: str | None = None,
        resolution: str | None = None,
    ) -> list[SourceAvailability]:
        """All rows for one source, optionally filtered by ``status`` and/or
        ``resolution``.

        Uses the ``idx_isa_source_status`` index when ``status`` is given (the
        Discovery daemon's primary query path: "for the 'capital' source, which
        epics are currently 'ok'?").
        """
        clauses = ["source = ?"]
        params: list[object] = [source]
        if status is not None:
            clauses.append("status = ?")
            params.append(status)
        if resolution is not None:
            clauses.append("resolution = ?")
            params.append(resolution)
        sql = (
            "SELECT * FROM instrument_source_availability "
            f"WHERE {' AND '.join(clauses)} "
            "ORDER BY epic ASC, resolution ASC"
        )
        rows = self.conn.execute(sql, params).fetchall()
        return [_row_to_availability(r) for r in rows]

    def symbol_for(
        self,
        epic: str,
        source: str,
        resolution: str = "1m",
    ) -> str | None:
        """The source's own symbol for ``(epic, source, resolution)``.

        Returns ``None`` (does **not** raise) when no row matches. This is the
        contract ``run_capital_backfill` relies on after Block B2: a missing
        availability row reads as "this source does not serve this epic" — a
        fall-back-to-Path-C decision belongs to the consumer, not the store.

        Replaces ``EPIC_MAP.get(epic)`` in ``live_data/backfill.py:180`` (Phase-14
        B2 acceptance criterion).
        """
        row = self.conn.execute(
            "SELECT source_symbol FROM instrument_source_availability "
            "WHERE epic = ? AND source = ? AND resolution = ?",
            (epic, source, resolution),
        ).fetchone()
        return row["source_symbol"] if row is not None else None

    def stale_rows(
        self,
        *,
        ttl_days: int,
        now_utc: str | None = None,
    ) -> list[SourceAvailability]:
        """Rows whose ``last_verified_utc`` is strictly older than
        ``now_utc - ttl_days`` days.

        Discovery uses this as the work list: only re-verify rows the daemon has
        not touched in the TTL window (Plan D14, default 7 days). A row never
        touched (``last_verified_utc`` set to Migration 007's backfill stamp for
        ``origin='registry'`` rows, or to the first run for ``origin='discovery'``
        rows) is *always* stale — which is the right default for a never-verified
        source.

        Comparison is lexicographic (Plan D14 / §6 A2 implementation hint). This
        is sound because every timestamp in the column comes from the same
        formatter (``utc_iso_now`` above), so lexical order is chronological
        order. If a future writer introduces a different format, this becomes a
        bug — the test (test 9 in §6 A2) is the canary.
        """
        if now_utc is None:
            now_utc = utc_iso_now()
        cutoff_iso = _shift_days(now_utc, -ttl_days)
        rows = self.conn.execute(
            "SELECT * FROM instrument_source_availability "
            "WHERE last_verified_utc < ? "
            "ORDER BY last_verified_utc ASC, epic ASC, source ASC",
            (cutoff_iso,),
        ).fetchall()
        return [_row_to_availability(r) for r in rows]


def _shift_days(iso_str: str, days: int) -> str:
    """Subtract ``days`` from an ISO 8601 UTC string with Z suffix; return
    another ISO 8601 UTC string (lexicographically comparable)."""
    dt = datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    shifted = dt + timedelta(days=days)
    return shifted.strftime("%Y-%m-%dT%H:%M:%S.") + f"{shifted.microsecond // 1000:03d}Z"
