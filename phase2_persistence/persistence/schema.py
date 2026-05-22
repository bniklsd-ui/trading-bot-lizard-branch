"""Schema-tracking constants.

The table DDL lives in ``migrations/*.sql`` (single source of truth, applied by
:mod:`persistence.migrations`). This module holds only what the migration runner
itself needs: the version-tracking table DDL and the migrations directory path.
"""

from __future__ import annotations

from pathlib import Path


# Directory containing the numbered ``NNN_*.sql`` migration files.
MIGRATIONS_DIR: Path = Path(__file__).resolve().parent.parent / "migrations"


# Tracks the highest applied migration version. Created before any migration runs.
SCHEMA_VERSION_TABLE = """
CREATE TABLE IF NOT EXISTS _schema_version (
    version INTEGER NOT NULL
);
"""
