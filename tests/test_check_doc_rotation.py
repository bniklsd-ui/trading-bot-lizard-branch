"""Tests for ``scripts/check_doc_rotation.py`` (Mini-Session 16, 2026-08-27).

Loaded via ``importlib`` by file path — root ``scripts/`` is deliberately **not** an
importable package (the phases already collide on a ``scripts.wiring`` module name),
so this phase-less harness is loaded the same way as ``test_verify_instrument.py`` /
``test_resolve_epics.py``.

Tests cover:
- ``count_session_blocks``: the pure counting helper (offline, no I/O).
- ``check_phase``: per-phase file IO with a tmp dir (no fixture needed).
- ``main``: full CLI invocation with a tmp PHASE_DIRS override.
- The end-to-end repo run: every phase head in PHASE_DIRS must be canonical
  (0 or 1 ``## Session stopped`` block — at most one). This catches the
  Session-12 drift pattern (inline-duplicate of session blocks in one head).
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

_SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "check_doc_rotation.py"
_spec = importlib.util.spec_from_file_location("check_doc_rotation", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
check_doc_rotation_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_doc_rotation_mod)

REPO_ROOT = check_doc_rotation_mod.REPO_ROOT


def test_count_session_blocks_empty() -> None:
    """An empty body has zero session blocks."""
    assert check_doc_rotation_mod.count_session_blocks("") == 0


def test_count_session_blocks_no_heading() -> None:
    """A body without any ``## Session stopped`` line is zero."""
    body = "# Title\n\nSome prose.\n\n## Another heading\n\nMore prose.\n"
    assert check_doc_rotation_mod.count_session_blocks(body) == 0


def test_count_session_blocks_one() -> None:
    """A canonical phasenkopf has exactly one."""
    body = (
        "## Module table\n\n"
        "| foo | bar |\n"
        "\n"
        "---\n"
        "\n"
        "## Session stopped — 2026-08-27 (Session N)\n"
        "\n"
        "> body\n"
    )
    assert check_doc_rotation_mod.count_session_blocks(body) == 1


def test_count_session_blocks_two_inline_duplicate() -> None:
    """The Session-12 drift pattern: two ``## Session stopped`` in one file."""
    body = (
        "## Session stopped — 2026-08-26 (Session 13)\n\nbody 13\n\n"
        "## Session stopped — 2026-08-26 (Session 12)\n\nbody 12\n"
    )
    assert check_doc_rotation_mod.count_session_blocks(body) == 2


def test_count_session_blocks_ignores_inline_match() -> None:
    """Only the H2 heading line itself counts; inline matches are ignored.

    The footer pointer paragraph contains ``## Session stopped`` text inside a
    ``>`` blockquote — that's prose, not an H2 heading, and must NOT count.
    """
    body = (
        "## Session stopped — 2026-08-27 (real)\n\nbody\n\n"
        "> **Ältere Session-Blöcke**: ## Session stopped is the convention, see archive.\n"
    )
    assert check_doc_rotation_mod.count_session_blocks(body) == 1


def test_check_phase_no_claude_md(tmp_path: Path) -> None:
    """Missing CLAUDE.md is reported as ``(no CLAUDE.md)`` with count 0."""
    count, label = check_doc_rotation_mod.check_phase(tmp_path / "missing")
    assert count == 0
    assert "no CLAUDE.md" in label


def test_check_phase_zero(tmp_path: Path) -> None:
    """A CLAUDE.md with no session block reports count 0 (canonical for virgin phases)."""
    head = tmp_path / "CLAUDE.md"
    head.write_text("# Phase\n\nSome body without any session heading.\n", encoding="utf-8")
    count, label = check_doc_rotation_mod.check_phase(tmp_path)
    assert count == 0
    assert label == tmp_path.name


def test_check_phase_one(tmp_path: Path) -> None:
    """A canonical phasenkopf with one session block reports count 1."""
    head = tmp_path / "CLAUDE.md"
    head.write_text(
        "## Session stopped — 2026-08-27 (Session 1)\n\nbody\n",
        encoding="utf-8",
    )
    count, _ = check_doc_rotation_mod.check_phase(tmp_path)
    assert count == 1


def test_main_zero_is_ok(tmp_path: Path, monkeypatch) -> None:
    """A phasenkopf with 0 session blocks passes (precedent: phase2_persistence)."""
    head = tmp_path / "CLAUDE.md"
    head.write_text("# Virgin phase\n", encoding="utf-8")
    monkeypatch.setattr(
        check_doc_rotation_mod,
        "PHASE_DIRS",
        ("zero_phase",),
    )
    monkeypatch.setattr(check_doc_rotation_mod, "REPO_ROOT", tmp_path.parent)
    monkeypatch.setattr(sys, "argv", ["check_doc_rotation"])
    # Build the expected phase dir layout: tmp_path.parent / "zero_phase".
    (tmp_path.parent / "zero_phase").mkdir(exist_ok=True)
    (tmp_path.parent / "zero_phase" / "CLAUDE.md").write_text(
        "# Virgin phase\n", encoding="utf-8"
    )
    rc = check_doc_rotation_mod.main()
    assert rc == 0


def test_main_one_is_ok(tmp_path: Path, monkeypatch) -> None:
    """A canonical phasenkopf with 1 session block passes."""
    (tmp_path.parent / "one_phase").mkdir(exist_ok=True)
    (tmp_path.parent / "one_phase" / "CLAUDE.md").write_text(
        "## Session stopped — 2026-08-27 (Session N)\n\nbody\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        check_doc_rotation_mod,
        "PHASE_DIRS",
        ("one_phase",),
    )
    monkeypatch.setattr(check_doc_rotation_mod, "REPO_ROOT", tmp_path.parent)
    monkeypatch.setattr(sys, "argv", ["check_doc_rotation"])
    rc = check_doc_rotation_mod.main()
    assert rc == 0


def test_main_two_is_fail(tmp_path: Path, monkeypatch) -> None:
    """The Session-12 drift pattern (inline-duplicate) is caught as exit code 1."""
    (tmp_path.parent / "two_phase").mkdir(exist_ok=True)
    (tmp_path.parent / "two_phase" / "CLAUDE.md").write_text(
        "## Session stopped — 2026-08-26 (Session 13)\n\n"
        "## Session stopped — 2026-08-26 (Session 12)\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        check_doc_rotation_mod,
        "PHASE_DIRS",
        ("two_phase",),
    )
    monkeypatch.setattr(check_doc_rotation_mod, "REPO_ROOT", tmp_path.parent)
    monkeypatch.setattr(sys, "argv", ["check_doc_rotation"])
    rc = check_doc_rotation_mod.main()
    assert rc == 1


def test_main_quiet_suppresses_ok_lines(tmp_path: Path, monkeypatch, capsys) -> None:
    """``--quiet`` suppresses OK rows; failures still print."""
    (tmp_path.parent / "ok_phase").mkdir(exist_ok=True)
    (tmp_path.parent / "ok_phase" / "CLAUDE.md").write_text(
        "## Session stopped — 2026-08-27 (Session N)\n", encoding="utf-8"
    )
    (tmp_path.parent / "fail_phase").mkdir(exist_ok=True)
    (tmp_path.parent / "fail_phase" / "CLAUDE.md").write_text(
        "## Session stopped — 2026-08-26 (Session 13)\n"
        "## Session stopped — 2026-08-26 (Session 12)\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        check_doc_rotation_mod,
        "PHASE_DIRS",
        ("ok_phase", "fail_phase"),
    )
    monkeypatch.setattr(check_doc_rotation_mod, "REPO_ROOT", tmp_path.parent)
    monkeypatch.setattr(sys, "argv", ["check_doc_rotation", "--quiet"])
    rc = check_doc_rotation_mod.main()
    out = capsys.readouterr().out
    assert rc == 1
    assert "[OK]" not in out
    assert "fail_phase" in out


def test_repo_end_to_end_all_canonical(monkeypatch) -> None:
    """Every phase head in PHASE_DIRS is canonical (at most one session block).

    This is the structural Session-12 finding made machine-checkable: any
    future drift (inline-duplicate in a phasenkopf) trips this test before
    it can be committed.
    """
    monkeypatch.setattr(sys, "argv", ["check_doc_rotation", "--quiet"])
    rc = check_doc_rotation_mod.main()
    assert rc == 0, (
        "Doc-rotation drift detected — a phase head has >1 '## Session stopped' "
        "block (Session-12 pattern). Run scripts/check_doc_rotation.py to see "
        "which phase; the previous block must move to SESSIONS_ARCHIVE.md."
    )


def test_repo_end_to_end_cli_invocation() -> None:
    """End-to-end CLI: invoking the script as a subprocess exits 0 against
    the live repo (every phase head is canonical right now)."""
    result = subprocess.run(
        [sys.executable, str(_SCRIPT_PATH), "--quiet"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"check_doc_rotation.py --quiet exited {result.returncode}:\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
