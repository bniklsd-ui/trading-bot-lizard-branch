"""S3 — ``AbstainStore``, an own-connection SQLite store for :class:`AbstainRecord`.

Mirrors ``phase9_universe/universe/store.py``'s pattern (verified this session): a
phase-isolated store that opens its own ``sqlite3`` connection to the shared
``data/trading_bot.sqlite`` file rather than importing ``persistence.Database`` —
the physical DB is shared, the access code is not. Migration 005 must already have
run against ``db_path`` (Phase 2's ``run_migrations()``); this store never runs
migrations itself, it only reads/writes the ``abstain_records`` table it created.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from abstain_lessons.exceptions import AbstainStoreError
from abstain_lessons.models import AbstainRecord

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS abstain_records (
    record_id           TEXT PRIMARY KEY,
    created_utc          TEXT NOT NULL,
    epic                 TEXT,
    stage                TEXT NOT NULL,
    reason               TEXT NOT NULL,
    detail               TEXT NOT NULL DEFAULT '',
    context_json         TEXT NOT NULL DEFAULT '{}',
    lesson               TEXT,
    lesson_extracted     INTEGER NOT NULL DEFAULT 0
)
"""


class AbstainStore:
    """Own-connection CRUD for the ``abstain_records`` table."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        except sqlite3.Error as exc:
            raise AbstainStoreError(f"cannot open {self.db_path!r}: {exc}") from exc

    def ensure_schema(self) -> None:
        """``CREATE TABLE IF NOT EXISTS`` — convenient for tmp-DB tests; a no-op
        against a DB that already ran migration 005."""
        try:
            self.conn.execute(_CREATE_TABLE)
            self.conn.commit()
        except sqlite3.Error as exc:
            raise AbstainStoreError(f"ensure_schema failed: {exc}") from exc

    def insert(self, record: AbstainRecord) -> None:
        """Idempotent insert — a repeat ``record_id`` is silently ignored."""
        try:
            self.conn.execute(
                "INSERT OR IGNORE INTO abstain_records "
                "(record_id, created_utc, epic, stage, reason, detail, "
                "context_json, lesson, lesson_extracted) VALUES (?,?,?,?,?,?,?,?,?)",
                record.to_row(),
            )
            self.conn.commit()
        except sqlite3.Error as exc:
            raise AbstainStoreError(f"insert failed: {exc}") from exc

    def recent(self, limit: int = 20) -> list[AbstainRecord]:
        """Newest ``limit`` records, newest first."""
        try:
            rows = self.conn.execute(
                "SELECT record_id, created_utc, epic, stage, reason, detail, "
                "context_json, lesson, lesson_extracted FROM abstain_records "
                "ORDER BY created_utc DESC LIMIT ?",
                (limit,),
            ).fetchall()
        except sqlite3.Error as exc:
            raise AbstainStoreError(f"recent failed: {exc}") from exc
        return [AbstainRecord.from_row(row) for row in rows]

    def recent_lessons(self, limit: int = 5) -> list[str]:
        """Lesson strings from the newest records with a set, non-null lesson."""
        try:
            rows = self.conn.execute(
                "SELECT lesson FROM abstain_records "
                "WHERE lesson_extracted = 1 AND lesson IS NOT NULL "
                "ORDER BY created_utc DESC LIMIT ?",
                (limit,),
            ).fetchall()
        except sqlite3.Error as exc:
            raise AbstainStoreError(f"recent_lessons failed: {exc}") from exc
        return [row["lesson"] for row in rows]

    def set_lesson(self, record_id: str, lesson: str) -> None:
        """Set ``lesson`` + ``lesson_extracted=True`` on ``record_id``."""
        try:
            self.conn.execute(
                "UPDATE abstain_records SET lesson = ?, lesson_extracted = 1 "
                "WHERE record_id = ?",
                (lesson, record_id),
            )
            self.conn.commit()
        except sqlite3.Error as exc:
            raise AbstainStoreError(f"set_lesson failed: {exc}") from exc

    def count_lessons_today(self, now_utc: str) -> int:
        """Count of lessons extracted on the UTC calendar day of ``now_utc``
        (an ISO-8601 timestamp — only its date prefix is used, restart-safe since
        it's a DB count, not an in-memory counter)."""
        day_prefix = now_utc[:10]
        try:
            row = self.conn.execute(
                "SELECT COUNT(*) FROM abstain_records "
                "WHERE lesson_extracted = 1 AND created_utc LIKE ?",
                (f"{day_prefix}%",),
            ).fetchone()
        except sqlite3.Error as exc:
            raise AbstainStoreError(f"count_lessons_today failed: {exc}") from exc
        return row[0]

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "AbstainStore":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
