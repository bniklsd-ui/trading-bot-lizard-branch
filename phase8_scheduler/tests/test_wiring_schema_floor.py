"""Tests for ``scripts.wiring.assert_schema_floor`` (Phase 16 B1).

The function is a pure module-level helper (extracted from the original ``preflight_fn``
closure specifically so it can be tested without touching the keyring, the broker, or the
full daemon composition). Three contract cases (per Plan §6 B1 + §7 AK4):

1. ``v9`` (current target) → returns the version, no raise.
2. ``v7`` (the live-DB state at 2026-09-05, migrations 008+009 not applied) → raises
   ``RuntimeError`` with the ``init_db.py`` operator-actionable instruction in the text.
3. Empty ``_schema_version`` (a brand-new DB with no migrations applied) → raises.

Setup: ``scripts/wiring.py`` is not an installed package (it lives under ``phase8_scheduler/
scripts/`` alongside ``scheduler/``), so we add the project dir to ``sys.path`` here, exactly
the way ``phase8_scheduler/scripts/live_test.py`` does it. This is import-offline-safe because
``scripts.wiring``'s only top-level imports are intra-package ``scheduler.*`` modules — every
cross-phase import (persistence, broker_wrapper, etc.) is lazy inside function bodies.

No network, no keyring, no LLM, no real ``data/`` writes. Pure SQLite in-memory.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

# scripts/ -> phase8_scheduler/ (so ``from scripts.wiring import ...`` resolves)
_PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(_PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(_PROJECT_DIR))

from scripts.wiring import REQUIRED_SCHEMA_VERSION, assert_schema_floor  # noqa: E402


def _conn_at_version(version: int | None) -> sqlite3.Connection:
    """Open an in-memory DB with a ``_schema_version`` table seeded at ``version``.

    ``None`` = empty table (no rows at all), mirroring a fresh DB with no migrations applied.
    """
    conn = sqlite3.connect(":memory:")
    conn.executescript("CREATE TABLE _schema_version (version INTEGER NOT NULL);")
    if version is not None:
        conn.execute("INSERT INTO _schema_version (version) VALUES (?);", (int(version),))
        conn.commit()
    return conn


def test_required_schema_version_is_nine() -> None:
    """The constant is locked at 9 — migrations 008 + 009 are the live floor.

    If a future migration lands that the daemon depends on, this test should be updated
    **and** ``REQUIRED_SCHEMA_VERSION`` bumped in the same commit.
    """
    assert REQUIRED_SCHEMA_VERSION == 9


def test_v9_passes_and_returns_version() -> None:
    conn = _conn_at_version(9)
    try:
        version = assert_schema_floor(conn)
    finally:
        conn.close()
    assert version == 9


def test_v7_raises_with_init_db_instruction() -> None:
    """v7 is the live-DB state at 2026-09-05 — the floor must trip loudly."""
    conn = _conn_at_version(7)
    try:
        try:
            assert_schema_floor(conn)
        except RuntimeError as exc:
            text = str(exc)
        else:
            raise AssertionError("assert_schema_floor(v7) did not raise")
    finally:
        conn.close()
    # Operator-actionable instruction (matches Plan §6 B1 verbatim).
    assert "init_db.py" in text, text
    assert "--db-path" in text, text
    assert "version 7" in text and "required 9" in text, text


def test_empty_schema_version_table_raises() -> None:
    """A fresh DB with no migrations applied at all → same fail-closed behaviour."""
    conn = _conn_at_version(None)
    try:
        try:
            assert_schema_floor(conn)
        except RuntimeError as exc:
            text = str(exc)
        else:
            raise AssertionError("assert_schema_floor(empty) did not raise")
    finally:
        conn.close()
    assert "init_db.py" in text, text
    assert "version 0" in text and "required 9" in text, text


def test_below_required_raises_for_every_lower_version() -> None:
    """Belt-and-braces: every version < REQUIRED_SCHEMA_VERSION must trip the floor."""
    for version in (0, 1, 2, 3, 4, 5, 6, 7, 8):
        conn = _conn_at_version(version)
        try:
            try:
                assert_schema_floor(conn, required=9)
            except RuntimeError as exc:
                assert f"version {version}" in str(exc), str(exc)
                assert "required 9" in str(exc), str(exc)
            else:
                raise AssertionError(f"version {version} did not raise")
        finally:
            conn.close()
