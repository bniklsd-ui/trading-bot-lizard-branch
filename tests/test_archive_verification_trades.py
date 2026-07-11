"""Tests for ``scripts/archive_verification_trades.py`` (v1.6 hotfix, Cause A part 2).

Loaded via ``importlib`` by file path — root ``scripts/`` is deliberately **not** an
importable package (the phases already collide on a ``scripts.wiring`` module name), so this
phase-less script is loaded the same way as ``test_verify_instrument.py`` /
``test_resolve_epics.py``.

All local / offline: a real temp-file SQLite DB via the editable-installed ``persistence``
package (no network, no keyring, no live DB touched). Exercises the pure selection/collection/
delete helpers directly, plus ``main()`` end-to-end for the dry-run and ``--commit`` paths.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from persistence.db import Database

_SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "archive_verification_trades.py"
)
_spec = importlib.util.spec_from_file_location("archive_verification_trades", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
archive_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(archive_mod)


@pytest.fixture
def db(tmp_path):
    """A migrated, seeded Database on a temp-file SQLite path (mirrors phase2's fixture)."""
    d = Database(str(tmp_path / "test.sqlite"))
    d.run_migrations()
    yield d
    d.close()


def _insert(db: Database, **overrides) -> int:
    base = {
        "deal_id": overrides.pop("deal_id", "DEAL1"),
        "epic": "IX.D.DAX.IFMM.IP",
        "direction": "BUY",
        "size": 1.0,
        "open_level": 18000.0,
        "currency": "EUR",
        "open_ts": "2026-05-21T09:00:00.000Z",
        "session_date": "2026-05-21",
        **overrides,
    }
    return db.insert_trade(base)


# -- select_verification_trades ---------------------------------------------------------------

def test_select_by_provenance_tag(db):
    _insert(db, deal_id="VERIF", provenance="verification")
    _insert(db, deal_id="AUTO", provenance="autonomous")
    selected = archive_mod.select_verification_trades(db.conn)
    assert [r["deal_id"] for r in selected] == ["VERIF"]


def test_select_by_hold_time_fallback(db):
    tid_short = _insert(db, deal_id="SHORT")
    db.update_trade_close("SHORT", {"close_ts": "2026-05-21T09:01:00.000Z"})  # 1 min
    _insert(db, deal_id="LONG")
    db.update_trade_close("LONG", {"close_ts": "2026-05-21T10:00:00.000Z"})  # 60 min
    _insert(db, deal_id="OPENQ")  # never closed -> NULL hold, never swept up

    selected = archive_mod.select_verification_trades(db.conn, hold_threshold_min=2.0)

    ids = [r["deal_id"] for r in selected]
    assert ids == ["SHORT"]
    assert tid_short  # sanity: insert succeeded


def test_select_union_of_both_signals_no_duplicates(db):
    _insert(db, deal_id="TAGGED", provenance="verification")
    _insert(db, deal_id="SHORT_HOLD")
    db.update_trade_close("SHORT_HOLD", {"close_ts": "2026-05-21T09:01:00.000Z"})
    _insert(db, deal_id="BOTH", provenance="verification")
    db.update_trade_close("BOTH", {"close_ts": "2026-05-21T09:01:00.000Z"})
    _insert(db, deal_id="REAL")
    db.update_trade_close("REAL", {"close_ts": "2026-05-21T11:00:00.000Z"})  # 120 min, real

    selected = archive_mod.select_verification_trades(db.conn, hold_threshold_min=2.0)

    ids = {r["deal_id"] for r in selected}
    assert ids == {"TAGGED", "SHORT_HOLD", "BOTH"}


def test_select_ids_override_bypasses_heuristics(db):
    tid = _insert(db, deal_id="REAL_BUT_NAMED")  # would NOT match either heuristic
    db.update_trade_close("REAL_BUT_NAMED", {"close_ts": "2026-05-21T11:00:00.000Z"})
    _insert(db, deal_id="VERIF")  # would match, but not requested via --ids

    selected = archive_mod.select_verification_trades(db.conn, ids=[tid])

    assert [r["deal_id"] for r in selected] == ["REAL_BUT_NAMED"]


def test_select_ids_empty_list_selects_nothing(db):
    _insert(db, deal_id="VERIF", provenance="verification")
    assert archive_mod.select_verification_trades(db.conn, ids=[]) == []


def test_select_nothing_matches_returns_empty(db):
    _insert(db, deal_id="REAL")
    db.update_trade_close("REAL", {"close_ts": "2026-05-21T11:00:00.000Z"})
    assert archive_mod.select_verification_trades(db.conn) == []


# -- collect_related / delete_trades (FK-cascade contract) -------------------------------------

def test_collect_related_pulls_lessons_and_rewards(db):
    tid = _insert(db, deal_id="VERIF", provenance="verification")
    db.insert_lesson(tid, {"lesson_text": "a test-harness artifact"})
    db.insert_reward(tid, {"score_after": 50.0, "win_loss": "LOSS"})

    related = archive_mod.collect_related(db.conn, [tid])

    assert len(related["trade_lessons"]) == 1
    assert len(related["reward_pts"]) == 1


def test_collect_related_empty_ids_returns_empty_shape(db):
    related = archive_mod.collect_related(db.conn, [])
    assert related == {t: [] for t in archive_mod._CHILD_TABLES}


def test_delete_trades_cascades_children(db):
    tid = _insert(db, deal_id="VERIF", provenance="verification")
    db.insert_lesson(tid, {"lesson_text": "cascade me"})
    db.insert_reward(tid, {"score_after": 50.0, "win_loss": "LOSS"})

    archive_mod.delete_trades(db.conn, [tid])
    db.conn.commit()

    assert db.get_trade_by_deal_id("VERIF") is None
    assert db.conn.execute("SELECT COUNT(*) FROM trade_lessons WHERE trade_id = ?", (tid,)).fetchone()[0] == 0
    assert db.conn.execute("SELECT COUNT(*) FROM reward_pts WHERE trade_id = ?", (tid,)).fetchone()[0] == 0


def test_delete_trades_leaves_other_rows_untouched(db):
    tid_verif = _insert(db, deal_id="VERIF", provenance="verification")
    _insert(db, deal_id="REAL")

    archive_mod.delete_trades(db.conn, [tid_verif])
    db.conn.commit()

    assert db.get_trade_by_deal_id("VERIF") is None
    assert db.get_trade_by_deal_id("REAL") is not None


# -- main(): dry-run vs --commit -----------------------------------------------------------------

def test_main_dry_run_writes_nothing_and_leaves_db_untouched(tmp_path, capsys):
    db_path = tmp_path / "live.sqlite"
    d = Database(str(db_path))
    d.run_migrations()
    _insert(d, deal_id="VERIF", provenance="verification")
    d.close()

    archive_dir = tmp_path / "archive"
    rc = archive_mod.main(["--db-path", str(db_path), "--archive-dir", str(archive_dir)])
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out["committed"] is False
    assert out["archive_path"] is None
    assert out["selected"] == [1]
    assert not archive_dir.exists()  # no directory even created — true dry-run

    # DB is untouched: the trade is still there.
    d2 = Database(str(db_path))
    assert d2.get_trade_by_deal_id("VERIF") is not None
    d2.close()


def test_main_no_matches_dry_run_exits_clean(tmp_path, capsys):
    db_path = tmp_path / "live.sqlite"
    d = Database(str(db_path))
    d.run_migrations()
    _insert(d, deal_id="REAL")
    d.close()

    rc = archive_mod.main(["--db-path", str(db_path)])
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out == {"selected": [], "committed": False, "archive_path": None}


def test_main_commit_writes_archive_and_deletes(tmp_path, capsys):
    db_path = tmp_path / "live.sqlite"
    d = Database(str(db_path))
    d.run_migrations()
    tid = _insert(d, deal_id="VERIF", provenance="verification")
    d.insert_lesson(tid, {"lesson_text": "test-harness artifact"})
    _insert(d, deal_id="REAL")
    d.close()

    archive_dir = tmp_path / "archive"
    rc = archive_mod.main(
        ["--db-path", str(db_path), "--archive-dir", str(archive_dir), "--commit"]
    )
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out["committed"] is True
    assert out["selected"] == [tid]
    archive_path = Path(out["archive_path"])
    assert archive_path.exists()

    payload = json.loads(archive_path.read_text())
    assert payload["trade_outcomes"][0]["deal_id"] == "VERIF"
    assert payload["trade_lessons"][0]["lesson_text"] == "test-harness artifact"
    assert "reason" in payload and "archived_at" in payload

    # DB reflects the deletion; the real trade survives.
    d2 = Database(str(db_path))
    assert d2.get_trade_by_deal_id("VERIF") is None
    assert d2.get_trade_by_deal_id("REAL") is not None
    d2.close()


def test_main_ids_override(tmp_path, capsys):
    db_path = tmp_path / "live.sqlite"
    d = Database(str(db_path))
    d.run_migrations()
    tid_named = _insert(d, deal_id="NAMED_REAL")  # would not match heuristics
    _insert(d, deal_id="WOULD_MATCH", provenance="verification")  # not requested
    d.close()

    rc = archive_mod.main(
        ["--db-path", str(db_path), "--ids", str(tid_named), "--commit",
         "--archive-dir", str(tmp_path / "archive")]
    )
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out["selected"] == [tid_named]

    d2 = Database(str(db_path))
    assert d2.get_trade_by_deal_id("NAMED_REAL") is None  # archived (explicit override)
    assert d2.get_trade_by_deal_id("WOULD_MATCH") is not None  # left alone
    d2.close()
