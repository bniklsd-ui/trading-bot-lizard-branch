"""Tests for ``scripts/reset_universe.py``'s D18 restart gate (``_check_restart_gate``).

Loaded via ``importlib.util`` (precedent: ``scripts/verify_instrument.py``,
``phase9_universe/CLAUDE.md``) — the script lives outside any installed package, same
"operator-run, not normally imported" convention as the rest of this phase's scripts. Only
the pure gate function is exercised here; the network/DB-writing ``main()`` is Nikinger-run.
"""

from __future__ import annotations

import importlib.util
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "reset_universe.py"
_spec = importlib.util.spec_from_file_location("reset_universe", _SCRIPT_PATH)
reset_universe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(reset_universe)  # type: ignore[union-attr]

NOW = datetime(2026, 8, 16, 12, 0, 0, tzinfo=timezone.utc)


def _bars_db(tmp_path, *, observed_at: str | None = None, remaining: int | None = None) -> str:
    path = tmp_path / "bars.sqlite"
    conn = sqlite3.connect(str(path))
    conn.execute(
        "CREATE TABLE allowance_observations (id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "observed_at TEXT NOT NULL, total INTEGER, remaining INTEGER, expiry TEXT)"
    )
    if observed_at is not None:
        conn.execute(
            "INSERT INTO allowance_observations (observed_at, total, remaining, expiry) "
            "VALUES (?, ?, ?, ?)",
            (observed_at, 10_000, remaining, None),
        )
    conn.commit()
    conn.close()
    return str(path)


def test_gate_refuses_when_no_table(tmp_path):
    path = str(tmp_path / "empty_bars.sqlite")
    sqlite3.connect(path).close()  # file exists but no table at all
    allowed, reason = reset_universe._check_restart_gate(path, 1_500, now=NOW)
    assert allowed is False
    assert "probe_allowance" in reason


def test_gate_refuses_when_no_observation(tmp_path):
    path = _bars_db(tmp_path)
    allowed, reason = reset_universe._check_restart_gate(path, 1_500, now=NOW)
    assert allowed is False
    assert "no allowance observation" in reason


def test_gate_refuses_when_stale(tmp_path):
    stale = reset_universe._iso(NOW - timedelta(hours=25))
    path = _bars_db(tmp_path, observed_at=stale, remaining=5_000)
    allowed, reason = reset_universe._check_restart_gate(path, 1_500, now=NOW)
    assert allowed is False
    assert "old" in reason


def test_gate_refuses_when_remaining_at_or_below_reserve(tmp_path):
    fresh = reset_universe._iso(NOW - timedelta(hours=1))
    path = _bars_db(tmp_path, observed_at=fresh, remaining=1_500)
    allowed, reason = reset_universe._check_restart_gate(path, 1_500, now=NOW)
    assert allowed is False
    assert "exhausted" in reason


def test_gate_allows_when_fresh_and_above_reserve(tmp_path):
    fresh = reset_universe._iso(NOW - timedelta(hours=1))
    path = _bars_db(tmp_path, observed_at=fresh, remaining=5_000)
    allowed, reason = reset_universe._check_restart_gate(path, 1_500, now=NOW)
    assert allowed is True
    assert "remaining=5000" in reason


def test_gate_boundary_exactly_24h_is_still_fresh(tmp_path):
    boundary = reset_universe._iso(NOW - timedelta(hours=24))
    path = _bars_db(tmp_path, observed_at=boundary, remaining=5_000)
    allowed, _ = reset_universe._check_restart_gate(path, 1_500, now=NOW)
    assert allowed is True
