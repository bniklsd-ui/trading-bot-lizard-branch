"""Tests for ``scripts/diag_score_distribution.py`` (v1.5 hotfix, Step 1).

Loaded via ``importlib`` by file path rather than a package import — root ``scripts/`` is
deliberately **not** an importable package (the phases already collide on a ``scripts.wiring``
module name; adding ``scripts/__init__.py`` here would risk the same collision for a script
that is explicitly phase-less per the v1.5 hotfix plan's cross-phase-edit register).

Two layers: pure ``compute_distribution`` unit tests (no I/O) and ``tmp_path``-backed SQLite
integration tests driving ``main()`` end to end. No network, no real DB — a temp on-disk
SQLite file is local disk I/O, consistent with the repo's existing test discipline.

Run standalone: ``pytest tests -q`` (a new, separate suite — like every phase's own suite).
"""

from __future__ import annotations

import importlib.util
import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

_SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "diag_score_distribution.py"
_spec = importlib.util.spec_from_file_location("diag_score_distribution", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
diag = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(diag)


# --- Layer 1: pure compute_distribution --------------------------------------------------


def test_empty_list_is_insufficient() -> None:
    dist = diag.compute_distribution([])
    assert dist["n"] == 0
    assert dist["insufficient"] is True
    assert dist["small_sample"] is False
    assert dist["current_score"] == 50.0
    assert dist["stats"] == {"min": None, "max": None, "median": None, "mean": None, "p25": None, "p75": None}
    assert dist["thresholds"]["below_50"] == {"count": 0, "pct": None}
    assert dist["thresholds"]["below_35"] == {"count": 0, "pct": None}


def test_single_point() -> None:
    dist = diag.compute_distribution([42.0])
    assert dist["n"] == 1
    assert dist["insufficient"] is False
    assert dist["small_sample"] is True
    assert dist["current_score"] == 42.0
    assert dist["stats"]["min"] == dist["stats"]["max"] == dist["stats"]["median"] == 42.0
    assert dist["stats"]["p25"] is None
    assert dist["stats"]["p75"] is None


def test_current_score_is_chronologically_last_not_min_or_max() -> None:
    # Scores must be passed in id-ASC (chronological) order — current is the *last* one,
    # proving the function doesn't silently sort.
    dist = diag.compute_distribution([50.0, 45.0, 40.0])
    assert dist["current_score"] == 40.0
    assert dist["stats"]["min"] == 40.0
    assert dist["stats"]["max"] == 50.0


def test_boundary_exactly_50_excluded_from_below_50() -> None:
    dist = diag.compute_distribution([50.0, 49.9, 60.0])
    assert dist["thresholds"]["below_50"]["count"] == 1  # only 49.9
    assert dist["thresholds"]["below_50"]["pct"] == pytest.approx(1 / 3)


def test_boundary_exactly_35_excluded_from_below_35() -> None:
    dist = diag.compute_distribution([35.0, 34.9, 40.0])
    assert dist["thresholds"]["below_35"]["count"] == 1  # only 34.9


def test_median_odd_count() -> None:
    dist = diag.compute_distribution([10.0, 90.0, 50.0])
    assert dist["stats"]["median"] == 50.0


def test_median_even_count_averages_middle_two() -> None:
    dist = diag.compute_distribution([10.0, 20.0, 30.0, 40.0])
    assert dist["stats"]["median"] == 25.0


def test_ties_are_stable() -> None:
    dist = diag.compute_distribution([50.0, 50.0, 50.0])
    assert dist["stats"]["median"] == 50.0
    assert dist["stats"]["p25"] == 50.0
    assert dist["stats"]["p75"] == 50.0


def test_p25_p75_stay_within_min_max() -> None:
    scores = [10.0, 20.0, 30.0, 40.0, 50.0]
    dist = diag.compute_distribution(scores)
    assert dist["stats"]["min"] <= dist["stats"]["p25"] <= dist["stats"]["median"]
    assert dist["stats"]["median"] <= dist["stats"]["p75"] <= dist["stats"]["max"]


def test_all_above_50_counts_zero_below() -> None:
    dist = diag.compute_distribution([60.0, 70.0, 80.0])
    assert dist["thresholds"]["below_50"]["count"] == 0
    assert dist["thresholds"]["below_50"]["pct"] == 0.0


def test_all_below_50_counts_all() -> None:
    dist = diag.compute_distribution([10.0, 20.0, 30.0])
    assert dist["thresholds"]["below_50"]["count"] == 3
    assert dist["thresholds"]["below_50"]["pct"] == 1.0


def test_small_sample_flag_boundary() -> None:
    nine = diag.compute_distribution([50.0] * 9)
    ten = diag.compute_distribution([50.0] * 10)
    assert nine["small_sample"] is True
    assert ten["small_sample"] is False


def test_negative_scores_do_not_crash() -> None:
    # Real score_after is clamped to [0,100] by the Scorer (P7 Decision D) so this never
    # occurs in live data — this only proves the pure function is robust regardless.
    dist = diag.compute_distribution([-5.0, 10.0])
    assert dist["n"] == 2
    assert dist["stats"]["min"] == -5.0


# --- Layer 2: tmp_path SQLite integration via main() --------------------------------------


def _make_db(path: Path, *, with_tables: bool = True) -> None:
    conn = sqlite3.connect(str(path))
    try:
        if with_tables:
            conn.execute("CREATE TABLE trade_outcomes (id INTEGER PRIMARY KEY AUTOINCREMENT, account TEXT)")
            conn.execute(
                "CREATE TABLE reward_pts ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "trade_id INTEGER NOT NULL REFERENCES trade_outcomes(id), "
                "score_after REAL NOT NULL, "
                "calculated_at TEXT NOT NULL)"
            )
        else:
            conn.execute("CREATE TABLE unrelated (id INTEGER PRIMARY KEY)")
        conn.commit()
    finally:
        conn.close()


def _insert_row(path: Path, *, score: float, calculated_at: str, account: str | None) -> None:
    conn = sqlite3.connect(str(path))
    try:
        cur = conn.execute("INSERT INTO trade_outcomes (account) VALUES (?)", (account,))
        trade_id = cur.lastrowid
        conn.execute(
            "INSERT INTO reward_pts (trade_id, score_after, calculated_at) VALUES (?, ?, ?)",
            (trade_id, score, calculated_at),
        )
        conn.commit()
    finally:
        conn.close()


def _run_main(argv: list[str], capsys: Any) -> tuple[int, dict[str, Any], str]:
    exit_code = diag.main(argv)
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    return exit_code, payload, captured.err


def test_populated_db_reports_full_stats(tmp_path: Path, capsys: Any) -> None:
    db = tmp_path / "test.sqlite"
    _make_db(db)
    _insert_row(db, score=60.0, calculated_at="2026-06-01T00:00:00Z", account="demo")
    _insert_row(db, score=40.0, calculated_at="2026-06-02T00:00:00Z", account="live")
    _insert_row(db, score=45.0, calculated_at="2026-06-03T00:00:00Z", account=None)

    exit_code, payload, err = _run_main(["--db-path", str(db)], capsys)

    assert exit_code == 0
    assert payload["n"] == 3
    assert payload["insufficient"] is False
    assert payload["current_score"] == 45.0  # last inserted, id-ASC order
    assert payload["accounts"] == {"demo": 1, "live": 1, "unknown": 1}
    assert payload["date_range"] == {"earliest": "2026-06-01T00:00:00Z", "latest": "2026-06-03T00:00:00Z"}
    assert "[diag]" in err


def test_empty_table_is_insufficient(tmp_path: Path, capsys: Any) -> None:
    db = tmp_path / "test.sqlite"
    _make_db(db)

    exit_code, payload, _ = _run_main(["--db-path", str(db)], capsys)

    assert exit_code == 0
    assert payload["insufficient"] is True
    assert payload["reason"] == "no reward_pts rows"


def test_missing_db_file_is_insufficient(tmp_path: Path, capsys: Any) -> None:
    db = tmp_path / "does_not_exist.sqlite"

    exit_code, payload, _ = _run_main(["--db-path", str(db)], capsys)

    assert exit_code == 0
    assert payload["insufficient"] is True
    assert payload["reason"] == "database not found"


def test_missing_table_is_insufficient(tmp_path: Path, capsys: Any) -> None:
    db = tmp_path / "test.sqlite"
    _make_db(db, with_tables=False)

    exit_code, payload, _ = _run_main(["--db-path", str(db)], capsys)

    assert exit_code == 0
    assert payload["insufficient"] is True
    assert payload["reason"] == "reward_pts table missing"


def test_connection_is_read_only(tmp_path: Path) -> None:
    db = tmp_path / "test.sqlite"
    _make_db(db)

    conn = diag._ro_connect(str(db))
    try:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute("INSERT INTO trade_outcomes (account) VALUES ('demo')")
    finally:
        conn.close()


def test_null_account_buckets_as_unknown(tmp_path: Path, capsys: Any) -> None:
    db = tmp_path / "test.sqlite"
    _make_db(db)
    _insert_row(db, score=50.0, calculated_at="2026-06-01T00:00:00Z", account=None)

    _, payload, _ = _run_main(["--db-path", str(db)], capsys)

    assert payload["accounts"] == {"unknown": 1}


def test_stdout_is_valid_json_stderr_has_narrative(tmp_path: Path, capsys: Any) -> None:
    db = tmp_path / "test.sqlite"
    _make_db(db)
    _insert_row(db, score=55.0, calculated_at="2026-06-01T00:00:00Z", account="demo")

    exit_code, payload, err = _run_main(["--db-path", str(db)], capsys)

    assert exit_code == 0
    assert isinstance(payload, dict)
    assert "current_score" in payload
    assert err.strip() != ""
