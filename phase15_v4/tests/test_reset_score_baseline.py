"""Tests for the Phase-15-B-B6 score-reset operator script.

Plan-Anker: docs/concepts/phase15_v4_plan.md §6 Block B B6 + §7 AK6.

The script ``phase7_reward/scripts/reset_score_baseline.py`` is a **live-DB operator
tool**: ``--dry-run`` is the default, ``--apply`` writes a single conditional
``UPDATE reward_pts SET score_after = 50.0 WHERE id = (SELECT MAX(id) ...)``.
The tests here build a tmp SQLite DB that mirrors the real
``phase2_persistence/migrations/001_initial.sql`` schema for ``reward_pts``,
seed 8 rows so the script can run against it, and check the three behaviours
the plan promises:

1. ``--dry-run`` does not modify the DB.
2. ``--apply`` sets exactly one cell (``score_after`` of the MAX-id row) to 50.0.
3. A second ``--apply`` run is a no-op (idempotency).

Tests run ``op.main([...])`` directly (subprocess not needed — the script's
``main()`` is a clean function), with stdout/stderr captured so the JSON
machine-readable summary can be asserted.
"""

from __future__ import annotations

import io
import json
import sqlite3
import sys
from pathlib import Path

import pytest


_REPO_ROOT = "/home/trading-bot/trading-bot"
_REWARD_PTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS reward_pts (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id              INTEGER NOT NULL,
    outcome_score_delta   REAL NOT NULL DEFAULT 0.0,
    score_after           REAL NOT NULL,
    win_loss              TEXT NOT NULL CHECK(win_loss IN ('WIN','LOSS','BREAKEVEN')),
    pnl_raw               REAL,
    process_score_delta   REAL,
    veto_trigger_count    INTEGER,
    gate_fail_count       INTEGER,
    debate_confidence     REAL,
    spread_at_entry_pct   REAL,
    calculated_at         TEXT NOT NULL
);
"""


def _seed_reward_pts_db(db_path: Path, *, final_score: float = 78.72) -> int:
    """Create the ``reward_pts`` schema and insert 8 rows ending on ``final_score``.

    Mirrors the live ``trade_outcomes.id = 1..8`` shape (8 closed trades at the
    time of Phase-15-B execution, Plan §2.2). The row order imitates the
    inverted-reward window: the score climbs even after losses.

    Returns the ``MAX(id)`` inserted (== 8).
    """
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(_REWARD_PTS_SCHEMA)
        # 8 trades, monotonically growing score that overshoots the neutral
        # baseline 50.0 — this is the exact problem Phase-15-B-B6 fixes.
        deltas = [
            (1, 1,  +1.10, 51.10),
            (2, 2,  -1.20, 49.90),
            (3, 3,  +1.30, 51.20),
            (4, 4,  +1.10, 52.30),
            (5, 5,  +1.10, 53.40),
            (6, 6,  +5.00, 58.40),   # 120x-bug-clamped (Plan §3 B3)
            (7, 7,  +5.00, 63.40),   # 120x-bug-clamped
            (8, 8,  +5.00, final_score),
        ]
        for rid, trade_id, outcome_delta, score_after in deltas:
            conn.execute(
                "INSERT INTO reward_pts "
                "(trade_id, outcome_score_delta, process_score_delta, "
                " score_after, win_loss, calculated_at) "
                "VALUES (?, ?, ?, ?, 'WIN', '2026-08-27T16:00:00Z')",
                (trade_id, outcome_delta, 0.0, score_after),
            )
        conn.commit()
        return 8
    finally:
        conn.close()


def _read_score_after(db_path: Path, row_id: int) -> float:
    """Helper: read ``score_after`` for a given row id from a tmp DB."""
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.execute("SELECT score_after FROM reward_pts WHERE id = ?", (row_id,))
        row = cur.fetchone()
        assert row is not None, f"row id={row_id} not found"
        return float(row[0])
    finally:
        conn.close()


def _import_op():
    """Import the operator module with repo-root on sys.path.

    Mirrors the pattern from phase13_live_data/tests/test_rescue.py:425 — the
    scripts are not under a package, so they need a sys.path tweak to import
    as ``phase7_reward.scripts.reset_score_baseline``.
    """
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)
    from phase7_reward.scripts import reset_score_baseline as op  # noqa: E402
    return op


def _capture_main(op, argv: list[str]) -> tuple[int, dict]:
    """Run ``op.main(argv)`` and capture the JSON-summary on stdout.

    Returns ``(returncode, parsed_json)``. The progress / audit-block output
    that the script writes to stderr is NOT captured here — the assertion
    surface is the machine-readable JSON envelope per Phase-7 operator-script
    convention.
    """
    buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        rc = op.main(argv)
    finally:
        sys.stdout = old_stdout
    payload = buf.getvalue()
    parsed = json.loads(payload) if payload.strip() else {}
    return rc, parsed


@pytest.fixture
def tmp_reward_db(tmp_path: Path) -> Path:
    """Seed a tmp SQLite DB with 8 reward_pts rows; final score = 78.72."""
    db_path = tmp_path / "reward_pts_test.sqlite"
    _seed_reward_pts_db(db_path, final_score=78.72)
    return db_path


def test_dry_run_does_not_modify(tmp_reward_db: Path) -> None:
    """Plan §6 B6 #3 + AK6: ``--dry-run`` (default) writes nothing to the DB."""
    op = _import_op()
    rc, parsed = _capture_main(op, ["--db-path", str(tmp_reward_db)])

    assert rc == 0
    assert parsed["ok"] is True
    assert parsed["mode"] == "dry-run"
    assert parsed["applied"] is False
    assert parsed["latest_id"] == 8
    assert parsed["latest_score_before"] == pytest.approx(78.72)
    assert parsed["latest_score_after"] == pytest.approx(50.0)  # predicted, not written

    # DB-side proof: every score_after row is exactly the seeded value.
    for row_id in range(1, 9):
        # Row 8 (MAX id) is still 78.72, untouched.
        assert _read_score_after(tmp_reward_db, row_id) == pytest.approx(
            _EXPECTED_SCORES[row_id - 1]
        )


def test_apply_sets_only_latest_row(tmp_reward_db: Path) -> None:
    """Plan §6 B6 #4 + AK6: ``--apply`` updates exactly one cell to 50.0."""
    op = _import_op()
    rc, parsed = _capture_main(op, ["--db-path", str(tmp_reward_db), "--apply"])

    assert rc == 0
    assert parsed["ok"] is True
    assert parsed["mode"] == "apply"
    assert parsed["applied"] is True
    assert parsed["latest_id"] == 8
    assert parsed["latest_score_before"] == pytest.approx(78.72)
    assert parsed["latest_score_after"] == pytest.approx(50.0)

    # Rows 1..7 are untouched; row 8 is 50.0.
    for row_id in range(1, 8):
        assert _read_score_after(tmp_reward_db, row_id) == pytest.approx(
            _EXPECTED_SCORES[row_id - 1]
        )
    assert _read_score_after(tmp_reward_db, 8) == pytest.approx(50.0)


def test_apply_is_idempotent(tmp_reward_db: Path) -> None:
    """Plan §6 B6 #6: a second ``--apply`` run is a no-op (already at 50.0)."""
    op = _import_op()

    # First apply
    rc1, parsed1 = _capture_main(
        op, ["--db-path", str(tmp_reward_db), "--apply"]
    )
    assert rc1 == 0
    assert parsed1["applied"] is True
    assert parsed1["latest_score_after"] == pytest.approx(50.0)

    # Second apply — nothing should change.
    rc2, parsed2 = _capture_main(
        op, ["--db-path", str(tmp_reward_db), "--apply"]
    )
    assert rc2 == 0
    assert parsed2["applied"] is True  # Operation completed; rowcount was 0.
    assert parsed2["latest_score_before"] == pytest.approx(50.0)
    assert parsed2["latest_score_after"] == pytest.approx(50.0)

    # DB-side proof: row 8 still at 50.0; rows 1..7 unchanged.
    for row_id in range(1, 8):
        assert _read_score_after(tmp_reward_db, row_id) == pytest.approx(
            _EXPECTED_SCORES[row_id - 1]
        )
    assert _read_score_after(tmp_reward_db, 8) == pytest.approx(50.0)


def test_dry_run_after_apply_is_safe(tmp_reward_db: Path) -> None:
    """AK6 mixed-mode: dry-run after apply does nothing (already-reset row)."""
    op = _import_op()

    # First, apply.
    rc1, _ = _capture_main(op, ["--db-path", str(tmp_reward_db), "--apply"])
    assert rc1 == 0

    # Then dry-run — script must NOT touch the (already 50.0) row.
    rc2, parsed2 = _capture_main(op, ["--db-path", str(tmp_reward_db)])
    assert rc2 == 0
    assert parsed2["mode"] == "dry-run"
    assert parsed2["applied"] is False
    assert parsed2["latest_score_before"] == pytest.approx(50.0)
    assert _read_score_after(tmp_reward_db, 8) == pytest.approx(50.0)


# --- helpers --------------------------------------------------------------- #

_EXPECTED_SCORES = [51.10, 49.90, 51.20, 52.30, 53.40, 58.40, 63.40, 78.72]
