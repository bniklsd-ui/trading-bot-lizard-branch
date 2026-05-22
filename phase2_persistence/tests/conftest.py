"""Shared fixtures. All tests use temp-file SQLite / temp dirs — no network."""

from __future__ import annotations

import pytest

from persistence.db import Database
from persistence.state import StateManager


@pytest.fixture
def db(tmp_path):
    """A migrated, seeded Database on a temp-file SQLite path."""
    d = Database(str(tmp_path / "test.sqlite"))
    d.run_migrations()
    yield d
    d.close()


@pytest.fixture
def sm(tmp_path):
    """A StateManager rooted at a temp state directory."""
    return StateManager(str(tmp_path / "state"))


@pytest.fixture
def base_trade():
    """A minimal valid trade dict for insert_trade."""
    return {
        "deal_id": "DEAL1",
        "epic": "IX.D.DAX.IFMM.IP",
        "direction": "BUY",
        "size": 1.0,
        "open_level": 18000.0,
        "currency": "EUR",
        "open_ts": "2026-05-21T09:00:00.000Z",
        "session_date": "2026-05-21",
    }
