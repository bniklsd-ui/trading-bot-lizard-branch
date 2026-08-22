"""``UniverseStore`` — SQLite CRUD for ``instrument_universe`` (migration 004).

Owns its own ``sqlite3`` connection rather than importing
``phase2_persistence.persistence.Database`` (phase isolation — ``import
universe.store`` pulls in no cross-phase module; mirrors how
``phase8_scheduler/scheduler/budget.py`` reads the shared ``llm_usage.json`` log
directly instead of importing a Phase-4 reader). It still points at the same
physical ``data/trading_bot.sqlite`` file that Phase 2's migration runner already
applies migration 004 to — the *table* is shared, the *access code* is not.

``utc_iso_now`` is duplicated (not imported) from Phase 2's ``timeutil.py`` for the
same phase-isolation reason documented there.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from universe.exceptions import UniverseStoreError
from universe.models import DS_OK, STATUS_ACTIVE, UniverseRecord

logger = logging.getLogger("universe.store")

# Registry-truth columns (Decision D5/D7): the only writers are `set_symbol` (Phase 12
# SymbolResolver) and the initial INSERT (`seed_curated`/first `upsert_discovered` for a
# fresh epic). A later `upsert_discovered` call for an *already-known* epic (its ON
# CONFLICT branch) must never clobber these — that would silently un-verify a resolved
# symbol every time discovery re-touches the row.
_PRESERVE_ON_CONFLICT = frozenset(
    {"yf_ticker", "data_source_status", "symbol_source", "symbol_checked_at"}
)


def utc_iso_now() -> str:
    """Current UTC time as an ISO 8601 string with ms precision and Z suffix."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


class UniverseStore:
    """SQLite-backed CRUD for the ``instrument_universe`` table.

    Migration 004 must already have run against ``db_path`` (Phase 2's
    ``Database.run_migrations()`` / ``run_migrations(conn, MIGRATIONS_DIR)`` —
    ``UniverseStore`` never runs migrations itself, it only reads/writes the table
    the migration created).
    """

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self) -> None:
        self.conn.close()

    # -- seeding --------------------------------------------------------

    def seed_curated(self, specs: Iterable[object]) -> int:
        """Idempotent one-time seed from the Phase-4 curated universe (Decision D5).

        ``specs`` are ``InstrumentSpec``-shaped objects (duck-typed: ``epic``,
        ``yf_ticker``, ``volume_proxy``, ``point_value``, ``min_deal_size``,
        ``currency``). Every seeded row gets ``status=STATUS_ACTIVE`` (they are
        already live-verified curated instruments, not fresh discoveries) and
        ``source="curated"``. Only the DAX epic (``IX.D.DAX.IFMM.IP``, the one
        live-confirmed contract) gets ``point_value_source="curated_confirmed"``;
        every other epic seeds with ``point_value_source=NULL`` so it must pass
        through the Step-2 resolver (``pricing.confirm_curated``) for confirmation
        — carried-over inferred point_values (STXE/CAC/IBEX) get a real code proof
        instead of staying "curated and never independently confirmed".

        ``INSERT OR IGNORE`` on the primary key (``epic``): re-seeding an already
        -known epic is a no-op, never overwrites operator/pipeline-driven state.
        Returns the number of rows actually inserted.
        """
        now = utc_iso_now()
        inserted = 0
        for spec in specs:
            epic = spec.epic
            point_value_source = (
                "curated_confirmed" if epic == "IX.D.DAX.IFMM.IP" else None
            )
            record = UniverseRecord(
                epic=epic,
                name=None,
                yf_ticker=spec.yf_ticker,
                volume_proxy=spec.volume_proxy,
                point_value=spec.point_value,
                point_value_source=point_value_source,
                min_deal_size=spec.min_deal_size,
                currency=spec.currency,
                status=STATUS_ACTIVE,
                source="curated",
                checks={},
                fail_count=0,
                data_degraded=False,
                last_verified_at=None,
                created_at=now,
                updated_at=now,
            )
            row = record.to_row()
            cols = list(row.keys())
            placeholders = ", ".join("?" for _ in cols)
            cur = self.conn.execute(
                f"INSERT OR IGNORE INTO instrument_universe ({', '.join(cols)}) "
                f"VALUES ({placeholders})",
                [row[c] for c in cols],
            )
            if cur.rowcount:
                inserted += 1
        self.conn.commit()
        return inserted

    # -- CRUD -------------------------------------------------------------

    def upsert_discovered(self, rec: UniverseRecord) -> None:
        """Insert a record wholesale, keyed on ``epic``.

        On conflict (an already-known epic re-discovered), registry-truth columns
        (:data:`_PRESERVE_ON_CONFLICT`) are left untouched — a re-discovery carries no
        symbol-verification signal, so it must not reset one (D5).
        """
        row = rec.to_row()
        cols = list(row.keys())
        placeholders = ", ".join("?" for _ in cols)
        update_cols = [c for c in cols if c != "epic" and c not in _PRESERVE_ON_CONFLICT]
        self.conn.execute(
            f"INSERT INTO instrument_universe ({', '.join(cols)}) "
            f"VALUES ({placeholders}) "
            f"ON CONFLICT(epic) DO UPDATE SET "
            + ", ".join(f"{c} = excluded.{c}" for c in update_cols),
            [row[c] for c in cols],
        )
        self.conn.commit()

    def get(self, epic: str) -> UniverseRecord | None:
        row = self.conn.execute(
            "SELECT * FROM instrument_universe WHERE epic = ?", (epic,)
        ).fetchone()
        return UniverseRecord.from_row(dict(row)) if row is not None else None

    def list_by_status(self, *statuses: str) -> list[UniverseRecord]:
        if not statuses:
            return []
        placeholders = ", ".join("?" for _ in statuses)
        rows = self.conn.execute(
            f"SELECT * FROM instrument_universe WHERE status IN ({placeholders}) "
            f"ORDER BY created_at ASC, epic ASC",
            statuses,
        ).fetchall()
        return [UniverseRecord.from_row(dict(r)) for r in rows]

    def set_status(
        self,
        epic: str,
        status: str,
        *,
        checks: dict | None = None,
        fail_increment: bool = False,
        reset_fail_count: bool = False,
        data_degraded: bool | None = None,
    ) -> None:
        """Update status (+ optionally checks/fail_count/data_degraded) for ``epic``.

        ``fail_increment`` and ``reset_fail_count`` are mutually exclusive knobs on
        the same counter (IG-side health tracking, Konzept C3): a health-recheck
        failure increments it toward demotion, a clean recheck resets it to 0.
        ``data_degraded`` is an independent yFinance-side signal — it never affects
        ``fail_count``/demotion (Decision: reduced-signal is tolerated, not
        demotion-worthy). Leaving both at their defaults changes neither field
        (additive, bit-identical to the pre-Step-4 behaviour for existing callers).
        """
        existing = self.get(epic)
        if existing is None:
            raise UniverseStoreError(f"no instrument_universe row for epic={epic!r}")
        now = utc_iso_now()
        if reset_fail_count:
            fail_count = 0
        elif fail_increment:
            fail_count = existing.fail_count + 1
        else:
            fail_count = existing.fail_count
        degraded = int(data_degraded) if data_degraded is not None else (1 if existing.data_degraded else 0)
        checks_json = (
            json.dumps(checks) if checks is not None else existing.to_row()["checks_json"]
        )
        self.conn.execute(
            "UPDATE instrument_universe SET status = ?, checks_json = ?, "
            "fail_count = ?, data_degraded = ?, last_verified_at = ?, updated_at = ? "
            "WHERE epic = ?",
            (status, checks_json, fail_count, degraded, now, now, epic),
        )
        self.conn.commit()

    def set_pricing(self, epic: str, point_value: float, source: str) -> None:
        existing = self.get(epic)
        if existing is None:
            raise UniverseStoreError(f"no instrument_universe row for epic={epic!r}")
        now = utc_iso_now()
        self.conn.execute(
            "UPDATE instrument_universe SET point_value = ?, point_value_source = ?, "
            "updated_at = ? WHERE epic = ?",
            (point_value, source, now, epic),
        )
        self.conn.commit()

    def active_universe(self) -> list[UniverseRecord]:
        """Only ``STATUS_ACTIVE`` rows, deterministic order (``created_at``, ``epic``)."""
        return self.list_by_status(STATUS_ACTIVE)

    def set_symbol(
        self,
        epic: str,
        yf_ticker: str | None,
        *,
        symbol_source: str | None,
        status: str,
    ) -> None:
        """The one writer of ``yf_ticker`` (Decision D5) — the ``SymbolResolver`` (Phase 12).

        Sets all four registry-truth columns (``yf_ticker``, ``data_source_status``,
        ``symbol_source``, ``symbol_checked_at``) atomically, plus ``updated_at``.
        ``symbol_source=None`` is valid — it is the correct value for a status with no
        symbol at all (``no_source``/``no_intraday_source``).

        Phase 14 A4: after the registry write commits, also projects the yF truth
        into ``instrument_source_availability`` (Migration 007) as a single row
        ``(epic, 'yf', '1m')``. The projection runs in its own try/except — a
        projection failure must NOT take down the registry write (Plan D5 /
        §8.2: silent measurement loss). If the projection table is missing (an
        older DB without Migration 007) ``sqlite3.OperationalError`` is caught
        and the registry write still stands.
        """
        existing = self.get(epic)
        if existing is None:
            raise UniverseStoreError(f"no instrument_universe row for epic={epic!r}")
        now = utc_iso_now()
        self.conn.execute(
            "UPDATE instrument_universe SET yf_ticker = ?, data_source_status = ?, "
            "symbol_source = ?, symbol_checked_at = ?, updated_at = ? WHERE epic = ?",
            (yf_ticker, status, symbol_source, now, now, epic),
        )
        self.conn.commit()

        # Phase 14 D4/D5: project yF truth into the cross-product table. The
        # registry stays the single writer; this is a named read-model
        # (``origin='registry'``) that the measurement gate NEVER reads.
        # Fail-soft — a projection error must not take down the registry
        # write, or an epic silently drops out of measurable universe (§8.2).
        try:
            self._project_availability(epic, yf_ticker, status, now)
        except Exception:  # noqa: BLE001 — D5: never let the projection kill the registry
            logger.warning(
                "source-availability projection failed for %s (registry write stands)",
                epic, exc_info=True,
            )

    def measurable_universe(self) -> list[UniverseRecord]:
        """``active`` rows with a verified data source (Decision D7) — the gate for
        paper/shadow measurement (`PaperEngine.epic_filter`, D19)."""
        rows = self.conn.execute(
            "SELECT * FROM instrument_universe WHERE status = ? AND data_source_status = ? "
            "ORDER BY created_at ASC, epic ASC",
            (STATUS_ACTIVE, DS_OK),
        ).fetchall()
        return [UniverseRecord.from_row(dict(r)) for r in rows]

    # -- phase 14 a4: yF projection into instrument_source_availability --------

    def _project_availability(
        self,
        epic: str,
        yf_ticker: str | None,
        status: str,
        now: str,
    ) -> None:
        """Phase-14 A4 — project the yF registry truth into
        ``instrument_source_availability`` (Migration 007).

        Writes exactly one row at PK ``(epic, source, resolution) ==
        (epic, 'yf', '1m')``. The same ``INSERT … ON CONFLICT DO UPDATE``
        shape as :meth:`source_registry.store.SourceAvailabilityStore.upsert`
        — both writers must produce byte-identical rows for the same input
        (doppelschreiber-gleichheit — Plan §6 A4 mitigation 3 / test 6).

        ``source_symbol = yf_ticker`` carries the 1:1 identity the D2
        promise makes (``instrument_universe.yf_ticker`` is exactly
        ``source_symbol WHERE source='yf'``). ``status`` is copied
        verbatim from the registry row (D18: same vocabulary as
        ``data_source_status``). ``origin = 'registry'`` per Plan D4.
        ``history_min_days`` and ``latency_min`` are NULL — these are
        discovery-time facts (Plan §5.1), not registry time. ``notes``
        is NULL — the migration-backfill note belongs to backfilled
        rows, not live registry writes.

        No cross-phase import (Plan §6 A4 "Schreib-Mechanik gelockt").
        No DDL — the table is owned by Migration 007; if it is missing,
        ``self.conn.execute`` raises ``sqlite3.OperationalError`` and the
        caller (``set_symbol``) catches + logs + returns (D5 fail-soft).
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
                epic, "yf", "1m", yf_ticker, status, "registry",
                None, None, now, None,
            ),
        )
        self.conn.commit()
