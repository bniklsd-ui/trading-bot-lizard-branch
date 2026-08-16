"""S3-analog — ``PaperTradeStore``, an own-connection SQLite store for :class:`PaperTrade`.

Same pattern as :class:`~abstain_lessons.store.AbstainStore` (own connection, no
``persistence.Database`` import). Migration 005 must already have run against
``db_path``. The engine that actually opens/resolves paper trades is WE 2
(``paper.py``'s "deterministischer Kern" + ``PaperEngine``) — this store only
persists whatever it's handed.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from abstain_lessons.exceptions import PaperTradeError
from abstain_lessons.paper import PaperTrade, PaperVariant

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS paper_trades (
    paper_id            TEXT PRIMARY KEY,
    abstain_record_id   TEXT NOT NULL,
    variant             TEXT NOT NULL,
    epic                TEXT NOT NULL,
    direction           TEXT NOT NULL,
    created_utc         TEXT NOT NULL,
    entry_level         REAL NOT NULL,
    stop_distance       REAL NOT NULL,
    limit_distance      REAL,
    time_stop_utc       TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'OPEN',
    resolved_utc        TEXT,
    exit_reason         TEXT,
    exit_level          REAL,
    pnl_points           REAL,
    r_multiple          REAL,
    council_confidence  INTEGER,
    lesson              TEXT,
    lesson_extracted    INTEGER NOT NULL DEFAULT 0,
    context_json        TEXT NOT NULL DEFAULT '{}',
    resolution_source   TEXT
)
"""

_ROW_COLUMNS = (
    "paper_id, abstain_record_id, variant, epic, direction, created_utc, "
    "entry_level, stop_distance, limit_distance, time_stop_utc, status, "
    "resolved_utc, exit_reason, exit_level, pnl_points, r_multiple, "
    "council_confidence, lesson, lesson_extracted, context_json, resolution_source"
)


class PaperTradeStore:
    """Own-connection CRUD for the ``paper_trades`` table."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        except sqlite3.Error as exc:
            raise PaperTradeError(f"cannot open {self.db_path!r}: {exc}") from exc

    def ensure_schema(self) -> None:
        """``CREATE TABLE IF NOT EXISTS`` — convenient for tmp-DB tests; a no-op
        against a DB that already ran migration 005."""
        try:
            self.conn.execute(_CREATE_TABLE)
            self.conn.commit()
        except sqlite3.Error as exc:
            raise PaperTradeError(f"ensure_schema failed: {exc}") from exc

    def insert(self, trade: PaperTrade) -> None:
        """Idempotent insert — a repeat ``paper_id`` is silently ignored."""
        try:
            self.conn.execute(
                f"INSERT OR IGNORE INTO paper_trades ({_ROW_COLUMNS}) "
                f"VALUES ({', '.join('?' * 21)})",
                trade.to_row(),
            )
            self.conn.commit()
        except sqlite3.Error as exc:
            raise PaperTradeError(f"insert failed: {exc}") from exc

    def open_trades(self) -> list[PaperTrade]:
        """All ``OPEN`` trades, oldest first (the WE-2 tracker resolves them in order)."""
        try:
            rows = self.conn.execute(
                f"SELECT {_ROW_COLUMNS} FROM paper_trades "
                "WHERE status = 'OPEN' ORDER BY created_utc ASC"
            ).fetchall()
        except sqlite3.Error as exc:
            raise PaperTradeError(f"open_trades failed: {exc}") from exc
        return [PaperTrade.from_row(row) for row in rows]

    def mark_resolved(
        self,
        paper_id: str,
        *,
        exit_reason: str,
        exit_level: float,
        pnl_points: float,
        r_multiple: float,
        resolved_utc: str,
        resolution_source: str | None = None,
    ) -> None:
        """Move ``paper_id`` from OPEN to RESOLVED with its exit details.

        ``resolution_source`` (Phase 12 D11) records which bar source(s) actually
        resolved this trade (``'yf'``/``'ig'``/``'ig+yf'``) — ``None`` when the caller
        genuinely doesn't know (e.g. a legacy caller predating this column).
        """
        try:
            self.conn.execute(
                "UPDATE paper_trades SET status = 'RESOLVED', exit_reason = ?, "
                "exit_level = ?, pnl_points = ?, r_multiple = ?, resolved_utc = ?, "
                "resolution_source = ? WHERE paper_id = ?",
                (exit_reason, exit_level, pnl_points, r_multiple, resolved_utc, resolution_source, paper_id),
            )
            self.conn.commit()
        except sqlite3.Error as exc:
            raise PaperTradeError(f"mark_resolved failed: {exc}") from exc

    def mark_expired(self, paper_id: str, resolved_utc: str) -> None:
        """Move ``paper_id`` from OPEN to EXPIRED_UNRESOLVED (no first-touch found)."""
        try:
            self.conn.execute(
                "UPDATE paper_trades SET status = 'EXPIRED_UNRESOLVED', "
                "resolved_utc = ? WHERE paper_id = ?",
                (resolved_utc, paper_id),
            )
            self.conn.commit()
        except sqlite3.Error as exc:
            raise PaperTradeError(f"mark_expired failed: {exc}") from exc

    def set_lesson(self, paper_id: str, lesson: str) -> None:
        """Set ``lesson`` + ``lesson_extracted=True`` on ``paper_id``."""
        try:
            self.conn.execute(
                "UPDATE paper_trades SET lesson = ?, lesson_extracted = 1 "
                "WHERE paper_id = ?",
                (lesson, paper_id),
            )
            self.conn.commit()
        except sqlite3.Error as exc:
            raise PaperTradeError(f"set_lesson failed: {exc}") from exc

    def count_today(self, variant: PaperVariant | None, now_utc: str) -> int:
        """Count of trades created on the UTC calendar day of ``now_utc``, optionally
        filtered to one ``variant`` (the Council-Paper-Call daily cap, V3-D6)."""
        day_prefix = now_utc[:10]
        try:
            if variant is None:
                row = self.conn.execute(
                    "SELECT COUNT(*) FROM paper_trades WHERE created_utc LIKE ?",
                    (f"{day_prefix}%",),
                ).fetchone()
            else:
                row = self.conn.execute(
                    "SELECT COUNT(*) FROM paper_trades "
                    "WHERE created_utc LIKE ? AND variant = ?",
                    (f"{day_prefix}%", variant.value),
                ).fetchone()
        except sqlite3.Error as exc:
            raise PaperTradeError(f"count_today failed: {exc}") from exc
        return row[0]

    def count_lessons_today(self, now_utc: str) -> int:
        """Count of lessons extracted on the UTC calendar day of ``now_utc`` — mirrors
        ``AbstainStore.count_lessons_today``; the two combine into the shared daily
        reflect cap (``AbstainLessonSink``, V3-D8)."""
        day_prefix = now_utc[:10]
        try:
            row = self.conn.execute(
                "SELECT COUNT(*) FROM paper_trades "
                "WHERE lesson_extracted = 1 AND created_utc LIKE ?",
                (f"{day_prefix}%",),
            ).fetchone()
        except sqlite3.Error as exc:
            raise PaperTradeError(f"count_lessons_today failed: {exc}") from exc
        return row[0]

    def recent_lessons(self, limit: int = 5) -> list[str]:
        """Lesson strings from the newest resolved trades with a set, non-null lesson."""
        try:
            rows = self.conn.execute(
                "SELECT lesson FROM paper_trades "
                "WHERE lesson_extracted = 1 AND lesson IS NOT NULL "
                "ORDER BY created_utc DESC LIMIT ?",
                (limit,),
            ).fetchall()
        except sqlite3.Error as exc:
            raise PaperTradeError(f"recent_lessons failed: {exc}") from exc
        return [row["lesson"] for row in rows]

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "PaperTradeStore":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
