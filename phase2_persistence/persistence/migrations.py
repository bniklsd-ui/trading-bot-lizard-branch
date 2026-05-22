"""SQL-file migration runner — no Alembic, no ORM.

Migration files live in ``migrations/`` as ``NNN_description.sql`` where ``NNN``
is a zero-padded integer version. The current applied version is tracked in the
``_schema_version`` table. ``run_migrations`` applies every file newer than the
current version, each inside its own transaction, in ascending order.

The runner is idempotent: a second call with no new files is a no-op.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from persistence.schema import SCHEMA_VERSION_TABLE

_MIGRATION_RE = re.compile(r"^(\d+)_.*\.sql$")


def _ensure_version_table(conn: sqlite3.Connection) -> None:
    """Create the ``_schema_version`` table if it does not exist yet."""
    conn.executescript(SCHEMA_VERSION_TABLE)
    conn.commit()


def _get_schema_version(conn: sqlite3.Connection) -> int:
    """Return the highest applied migration version (0 if none applied)."""
    _ensure_version_table(conn)
    row = conn.execute("SELECT MAX(version) AS v FROM _schema_version").fetchone()
    value = row["v"] if isinstance(row, sqlite3.Row) else row[0]
    return int(value) if value is not None else 0


def _set_schema_version(conn: sqlite3.Connection, version: int) -> None:
    """Record ``version`` as applied."""
    conn.execute("INSERT INTO _schema_version (version) VALUES (?)", (version,))


def _find_pending(migrations_dir: Path, current: int) -> list[tuple[int, Path]]:
    """Return ``(version, path)`` pairs newer than ``current``, sorted ascending."""
    pending: list[tuple[int, Path]] = []
    for path in migrations_dir.glob("*.sql"):
        match = _MIGRATION_RE.match(path.name)
        if not match:
            continue
        version = int(match.group(1))
        if version > current:
            pending.append((version, path))
    return sorted(pending, key=lambda pair: pair[0])


def _apply(conn: sqlite3.Connection, path: Path, version: int) -> None:
    """Apply a single migration file, then bump the version.

    ``executescript`` implicitly commits the DDL. The version row is then
    inserted and committed. Because all migration DDL is ``IF NOT EXISTS``
    (idempotent), a crash between the two steps is safe to recover from by
    simply re-running the migration.
    """
    sql = path.read_text(encoding="utf-8")
    try:
        conn.executescript(sql)
        _set_schema_version(conn, version)
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def run_migrations(conn: sqlite3.Connection, migrations_dir: Path | str) -> int:
    """Apply all pending migrations. Returns the resulting schema version.

    Idempotent — calling again with no new files does nothing and returns the
    unchanged current version.
    """
    migrations_dir = Path(migrations_dir)
    current = _get_schema_version(conn)
    for version, path in _find_pending(migrations_dir, current):
        _apply(conn, path, version)
        current = version
    return current
