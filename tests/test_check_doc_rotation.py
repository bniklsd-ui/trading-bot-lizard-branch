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


# ---------------------------------------------------------------------------
# P14-F Step 2 — archive-sequence integrity (Mini-Session 22, 2026-08-31).
#
# The pre-existing tests above cover Step-1 (inline-duplicate count). The
# tests below cover Step-2 (head-N == archive-max-(N-1)). Acceptance A1-A6
# from PHASE14_F_DOC_ROTATION_HOOK_STEP2_PLAN.md §5.
# ---------------------------------------------------------------------------


def test_archive_sequence_ok_for_continuous_block(tmp_path: Path) -> None:
    """A1: head=Session N, archive-newest=Session (N-1) → OK.

    Reproduziert den heutigen korrekten Zustand für Mini-Session 21.
    """
    (tmp_path / "CLAUDE.md").write_text(
        "## Session stopped — 2026-08-31 (Mini-Session 21 ...)\n",
        encoding="utf-8",
    )
    (tmp_path / "SESSIONS_ARCHIVE.md").write_text(
        "## Session stopped — 2026-08-28 (Session 20 ...)\n"
        "## Session stopped — 2026-08-28 (Session 19 ...)\n",
        encoding="utf-8",
    )
    assert check_doc_rotation_mod.check_archive_sequence(tmp_path) is None


def test_archive_sequence_drift_when_archive_skips_a_session(tmp_path: Path) -> None:
    """A2: head=Session 21, archive-newest=Session 19 → ❌ DRIFT.

    Genau der Fall, den Mini-Session-21 manuell korrigiert hat: Session 20
    wurde beim Hinzufügen von Session 21 nicht ins Archiv rotiert.
    """
    (tmp_path / "CLAUDE.md").write_text(
        "## Session stopped — 2026-08-31 (Mini-Session 21 ...)\n",
        encoding="utf-8",
    )
    (tmp_path / "SESSIONS_ARCHIVE.md").write_text(
        "## Session stopped — 2026-08-28 (Session 19 ...)\n",
        encoding="utf-8",
    )
    result = check_doc_rotation_mod.check_archive_sequence(tmp_path)
    assert result is not None
    label, diagnostic = result
    assert "Session 21" in diagnostic
    assert "Session 19" in diagnostic
    assert "expected 20" in diagnostic


def test_archive_sequence_drift_when_archive_missing(tmp_path: Path) -> None:
    """A3: head=Session 5, no archive → ❌ DRIFT (Sessions 1..4 verloren)."""
    (tmp_path / "CLAUDE.md").write_text(
        "## Session stopped — 2026-08-31 (Session 5 ...)\n",
        encoding="utf-8",
    )
    result = check_doc_rotation_mod.check_archive_sequence(tmp_path)
    assert result is not None
    label, diagnostic = result
    assert "Session 5" in diagnostic
    assert "SESSIONS_ARCHIVE.md" in diagnostic


def test_archive_sequence_ok_for_first_ever_session(tmp_path: Path) -> None:
    """A4: head=Session 1, archive absent oder leer → OK.

    Erste Session einer Phase, Archiv darf leer sein / fehlen.
    """
    (tmp_path / "CLAUDE.md").write_text(
        "## Session stopped — 2026-08-31 (Mini-Session 1 ...)\n",
        encoding="utf-8",
    )
    # Kein SESSIONS_ARCHIVE.md angelegt
    assert check_doc_rotation_mod.check_archive_sequence(tmp_path) is None

    # Auch mit leerem Archiv OK
    (tmp_path / "SESSIONS_ARCHIVE.md").write_text("# noch leer\n", encoding="utf-8")
    assert check_doc_rotation_mod.check_archive_sequence(tmp_path) is None


def test_archive_sequence_skips_phases_with_no_session_block(tmp_path: Path) -> None:
    """A5: Phasenkopf ohne Session-Block → OK (kein Check noetig)."""
    (tmp_path / "CLAUDE.md").write_text(
        "# Phase ohne Sessions\n\nKein Block, nichts zu pruefen.\n",
        encoding="utf-8",
    )
    assert check_doc_rotation_mod.check_archive_sequence(tmp_path) is None


def test_archive_sequence_handles_mini_session_naming(tmp_path: Path) -> None:
    """A1/A4-Edge: 'Mini-Session 21' und 'Session 20' werden korrekt extrahiert.

    Bonus: Body-Prose wie 'Folge-Session 2026-XX-XX' darf KEIN falsches Maximum
    erzeugen (sonst würden alle Phasen mit Datums-Erwähnungen fälschlich als
    Session 2026+ detected). Regex ist deshalb auf ``## Session stopped``-
    Heading-Zeilen eingeschränkt (siehe Kommentar in ``_max_session_num``).
    """
    (tmp_path / "CLAUDE.md").write_text(
        "## Session stopped — 2026-08-31 (Mini-Session 21 ...)\n",
        encoding="utf-8",
    )
    # Body-Prose mit Datum darf das Maximum NICHT verändern.
    (tmp_path / "SESSIONS_ARCHIVE.md").write_text(
        "Frühere Folge-Session 2026-07-17 war eröffnet; später dann:\n\n"
        "## Session stopped — 2026-08-28 (Session 20 ...)\n",
        encoding="utf-8",
    )
    assert check_doc_rotation_mod.check_archive_sequence(tmp_path) is None


def test_strict_flag_added_and_default_off() -> None:
    """A6: ``--strict``-Flag wird geparst; ohne Flag laeuft nur Step-1.

    Subprozess-Aufruf (kein Mock) — verifiziert die Mechanik ``--strict``
    schaltet Step 2 + Step 3 ein. Scope auf ``phase16_activation``
    (post-F8-Stand: alle 17 Headings lückenlos 1..16 + Plan-Session-Block),
    NICHT auf das ganze Repo (Phase 14 hat fehlende Sessions [9, 10], Phase 15
    fehlt Session #1 — diese Lücken werden in der Folgesession repariert;
    siehe Session-#18-Doc-Drift-Audit-Auftrag aus Phase-16-Phasenkopf).
    """
    # Ohne --strict: nur Step-1 (Inline-Duplicate-Count), exit 0 erwartet.
    result = subprocess.run(
        [sys.executable, str(_SCRIPT_PATH), "--quiet", "--phase", "phase16_activation"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0  # Step-1 gruen, Step-2 nicht aktiv

    # Mit --strict: Step-2 (Sequenz) + Step-3 (Lücken) aktiv. Phase 16 ist
    # post-F8 lückenlos, also exit 0 erwartet.
    result_strict = subprocess.run(
        [sys.executable, str(_SCRIPT_PATH), "--strict", "--quiet",
         "--phase", "phase16_activation"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result_strict.returncode == 0, (
        f"check_doc_rotation.py --strict --phase phase16_activation failed:\n"
        f"stdout={result_strict.stdout!r}\nstderr={result_strict.stderr!r}"
    )
    assert "sequence gap" not in result_strict.stdout.lower()
    assert "not contiguous" not in result_strict.stdout.lower()


# ---------------------------------------------------------------------------
# P15-F Step 2 — Doc-Rotation-Hook für Phase 15 nachgeschärft (2026-08-31).
#
# Phase-15-Vokabular ist „MiniMax-M3-Exec-Session #N" statt „Session N" /
# „Mini-Session N". Die P14-F-Regex wurde permissiver gemacht
# (``(?:Mini-|MiniMax-\w+-Exec-|Exec-)?Session\s+#?(\d+)``), und PHASE_DIRS
# wurde um „phase15_v4" erweitert. Die Tests unten verifizieren die neuen
# Heading-Formen + den Probe-Aufruf gegen die echte Phase-15-Struktur.
# Mini-Plan: phase15_v4/PHASE15_HOOK_HARDENING_PLAN.md §5 Akzeptanz A3–A6.
# ---------------------------------------------------------------------------


def test_archive_sequence_handles_exec_session_with_hash(tmp_path: Path) -> None:
    """P15-F A3: head=MiniMax-M3-Exec-Session #3, archive=#2 → OK (Phase 15 Block A).

    Reproduziert den aktuellen Phase-15-Stand (MiniMax-M3-Exec-Session #3 im
    Phasenkopf, #2 + #1 im Archiv, Plan-Session mit Opus 5 wird ignoriert).
    """
    (tmp_path / "CLAUDE.md").write_text(
        "## Session stopped — 2026-08-31 (MiniMax-M3-Exec-Session #3, ...)\n",
        encoding="utf-8",
    )
    (tmp_path / "SESSIONS_ARCHIVE.md").write_text(
        "## Session stopped — 2026-08-31 (MiniMax-M3-Exec-Session #2, ...)\n"
        "## Session stopped — 2026-08-31 (MiniMax-M3-Exec-Session, ...)\n"
        "## Session stopped — 2026-08-31 (Plan-Session, Opus 5)\n",
        encoding="utf-8",
    )
    assert check_doc_rotation_mod.check_archive_sequence(tmp_path) is None


def test_archive_sequence_drift_when_phase15_skips_a_session(tmp_path: Path) -> None:
    """P15-F A4: head=#3, archive-newest=#1 (überspringt #2) → ❌ DRIFT.

    Genau das Muster, das P14-F für Mini-Session 21 gefangen hat (Session 20
    wurde nicht ins Archiv rotiert) — jetzt für die Phase-15-Sequenz getestet.
    """
    (tmp_path / "CLAUDE.md").write_text(
        "## Session stopped — 2026-08-31 (MiniMax-M3-Exec-Session #3, ...)\n",
        encoding="utf-8",
    )
    (tmp_path / "SESSIONS_ARCHIVE.md").write_text(
        "## Session stopped — 2026-08-31 (MiniMax-M3-Exec-Session #1, ...)\n",
        encoding="utf-8",
    )
    result = check_doc_rotation_mod.check_archive_sequence(tmp_path)
    assert result is not None
    label, diagnostic = result
    # Die Diagnostik muss klar machen: head=3, archive-newest=1, expected=2.
    assert "expected 2" in diagnostic
    assert "Session 1" in diagnostic


def test_archive_sequence_ignores_plan_session_without_number(tmp_path: Path) -> None:
    """P15-F A5: archive enthält „Plan-Session, Opus 5" (kein \\d+) → ignoriert.

    Pre-Phase-Session-Blocks sollen nicht in die Sequenz-Invariante einbezogen
    werden. Ohne diese Asymmetrie würde archive_max=5 sein, was head=3 vs.
    expected=2 fälschlich als DRIFT melden würde.
    """
    (tmp_path / "CLAUDE.md").write_text(
        "## Session stopped — 2026-08-31 (MiniMax-M3-Exec-Session #3, ...)\n",
        encoding="utf-8",
    )
    (tmp_path / "SESSIONS_ARCHIVE.md").write_text(
        "## Session stopped — 2026-08-31 (Plan-Session, Opus 5)\n"
        "## Session stopped — 2026-08-31 (MiniMax-M3-Exec-Session #2, ...)\n",
        encoding="utf-8",
    )
    assert check_doc_rotation_mod.check_archive_sequence(tmp_path) is None


def test_strict_check_passes_for_phase15_v4_against_real_repo() -> None:
    """P15-F A6 + P16-F9: Echtes Phase-15-Repo ist nach F8-B-Reparatur Step-3-konform.

    Reparatur-Historie (Phase 16 Session #19 = Doc-Drift-Audit):
    - 2026-09-08 F9-Audit-Fund: ``phase15_v4/SESSIONS_ARCHIVE.md`` hatte
      Headings #2..#12 + Plan-Session-Block, aber das Heading für Session #1
      fehlte (MiniMax-M3-Exec-Session ohne Nummer — Pre-#1 hatte nie eine
      `#1`-Nummer, war von Anfang an ein F8-A-Versäumnis bei der ersten
      Erstellung des Archivs)
    - Reparatur: `#1` zur Heading-Zeile hinzugefügt (1-Zeichen-Edit, kein
      Inhalt geändert, kein Plan-Session-Block berührt). Jetzt exit 0.

    Der Test dokumentiert den Erfolg der Reparatur — der Hook bleibt
    *laut* bei zukünftigen Lücken (gleiche Mechanik wie Phase 16 / Phase 14).
    """
    result = subprocess.run(
        [sys.executable, str(_SCRIPT_PATH), "--strict", "--phase", "phase15_v4"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"erwartet exit 0 (Phase 15 F8-B-repariert post Audit), "
        f"got {result.returncode}: stdout={result.stdout!r}"
    )
    assert "phase15_v4" in result.stdout
    assert "not contiguous" not in result.stdout.lower()


# ---------------------------------------------------------------------------
# P16-F9 (2026-09-08) — archive-gap check (Lücken-Check).
#
# Session #17 (F8) hat zwei verlorene ``## Session stopped``-Überschriften in
# den Archiv-Blöcken #13/#14 gefunden — der damalige ``--strict``-Hook
# (P14-F Step 2) hat das nicht gemeldet, weil er nur den Anschluss
# Phasenkopf→Archiv prüfte, nicht die Lückenlosigkeit der Archiv-Nummern
# selbst. F9 fügt eine zweite Prüfung im selben ``--strict``-Pass hinzu.
#
# Akzeptanz (aus Phase-16-Phasenkopf Session-#17 Next-Block):
# - Grün gegen das heutige, reparierte Phase-16-Archiv.
# - Rot gegen den Stand vor der F8-Reparatur.
# - Plan-Session-Blöcke ohne Nummer korrekt ausgenommen.
# - Head = Session #1 → kein Check (Archiv darf leer sein).
# ---------------------------------------------------------------------------


def test_first_session_num_per_heading_picks_primary_not_max() -> None:
    """Heading-Bodies erwähnen vorherige Sessions; die Funktion nimmt das ERSTE
    Match pro Heading-Zeile (= primäre Session des Blocks), nicht das MAX.

    Reproduziert die Phase-16-#16-Heading: ``MiniMax-M3-Exec-Session #16, …,
    Session #15`` → muss 16 liefern, nicht 15. Ohne diese Disziplin würde der
    Gap-Check fälschlich Lücken bei #16 (statt #13/#14) melden.
    """
    archive = (
        "# SESSIONS_ARCHIVE\n\n"
        "## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #16, ..., "
        "Session #15])\n\n"
        "## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #15, ..., "
        "Session #14])\n\n"
        "## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #14, ..., "
        "Session #13])\n\n"
    )
    nums = check_doc_rotation_mod._first_session_num_per_heading(archive)
    assert nums == [16, 15, 14], (
        f"expected primary session numbers [16, 15, 14] (first-per-heading), "
        f"got {nums}"
    )


def test_first_session_num_per_heading_skips_plan_session_block() -> None:
    """Plan-Session-Block (Heading ohne Nummer) wird korrekt ausgenommen.

    ``Plan-Session, Fable 5.1`` matcht die Regex NICHT, weil nach
    ``Session`` ein Komma statt Whitespace+``#``+Digits kommt.
    """
    archive = (
        "## Session stopped — 2026-09-05 (Plan-Session, Fable 5.1 — Phase 16 eröffnet)\n"
        "## Session stopped — 2026-09-05 (MiniMax-M3-Exec-Session #1, ...)\n"
    )
    nums = check_doc_rotation_mod._first_session_num_per_heading(archive)
    assert nums == [1], (
        f"expected [1] (Plan-Session block skipped), got {nums}"
    )


def test_archive_gaps_ok_for_complete_archive(tmp_path: Path) -> None:
    """Head=#N, Archive mit lückenlosen Nummern 1..N-1 → OK.

    Reproduziert das aktuelle Phase-16-Stand post-F8 (head=#17, archive mit
    1..16 + Plan-Session-Block).
    """
    (tmp_path / "CLAUDE.md").write_text(
        "## Session stopped — 2026-09-08 (MiniMax-M3-Exec-Session #17, ...)\n",
        encoding="utf-8",
    )
    archive_lines = ["# SESSIONS_ARCHIVE\n\n"]
    archive_lines.append(
        "## Session stopped — 2026-09-05 (Plan-Session, Fable 5.1)\n\n"
    )
    for n in range(16, 0, -1):
        archive_lines.append(
            f"## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #{n}, "
            f"..., Session #{n - 1}])\n\n"
        )
    (tmp_path / "SESSIONS_ARCHIVE.md").write_text(
        "".join(archive_lines), encoding="utf-8"
    )
    assert check_doc_rotation_mod.check_archive_gaps(tmp_path) is None


def test_archive_gaps_fail_for_pre_f8_state(tmp_path: Path) -> None:
    """Head=#17, Archive mit Lücke bei #13/#14 (pre-F8-Stand) → ❌ DRIFT.

    Genau der Befund aus F8: die Rotationen der Sessions #14/#15 haben je die
    ``## Session stopped``-Überschrift der Blöcke #13/#14 verloren — die
    Archive-Datei trug weiterhin die BODYs, aber die H2-Headings fehlten,
    sodass die Session-Nummern 13 und 14 nicht mehr zählbar waren. ``_max``
    lieferte weiterhin 16 (Kopf #17 → Erwartung 16 = OK); die Lücke war
    silent. Der neue Check muss sie laut machen.
    """
    (tmp_path / "CLAUDE.md").write_text(
        "## Session stopped — 2026-09-08 (MiniMax-M3-Exec-Session #17, ...)\n",
        encoding="utf-8",
    )
    # Archive mit Lücke: #16, #15, dann Body ohne Heading für #14 und #13,
    # dann wieder #12, #11, …, #1.
    archive_lines = ["# SESSIONS_ARCHIVE\n\n"]
    archive_lines.append(
        "## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #16, ...)\n\n"
    )
    archive_lines.append(
        "## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #15, ...)\n\n"
    )
    # Hier fehlen die ## Session stopped-Headings für #14 und #13 (pre-F8).
    archive_lines.append(
        "> **Auftrag:** Nikinger-Chat 2026-09-07 (Session #14-Inhalt, "
        "Überschrift ging bei der Rotation verloren)\n\n"
    )
    archive_lines.append(
        "> **Auftrag:** Nikinger-Chat 2026-09-07 (Session #13-Inhalt, "
        "Überschrift ging bei der Rotation verloren)\n\n"
    )
    for n in range(12, 0, -1):
        archive_lines.append(
            f"## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #{n}, ...)\n\n"
        )
    (tmp_path / "SESSIONS_ARCHIVE.md").write_text(
        "".join(archive_lines), encoding="utf-8"
    )
    result = check_doc_rotation_mod.check_archive_gaps(tmp_path)
    assert result is not None, "expected FAIL for archive with gap at #13/#14"
    label, diagnostic = result
    assert "missing session(s) [13, 14]" in diagnostic, (
        f"expected missing [13, 14] in diagnostic, got: {diagnostic!r}"
    )


def test_archive_gaps_fail_for_archive_with_extra_session(tmp_path: Path) -> None:
    """Head=#5, Archive enthält zusätzlich #6 (out-of-range) → ❌ DRIFT.

    Defensiv: nicht nur Lücken, auch unerwartete Nummern werden gemeldet
    (z. B. wenn eine Rotation die falsche Datei erwischt hat).
    """
    (tmp_path / "CLAUDE.md").write_text(
        "## Session stopped — 2026-09-08 (MiniMax-M3-Exec-Session #5, ...)\n",
        encoding="utf-8",
    )
    (tmp_path / "SESSIONS_ARCHIVE.md").write_text(
        "## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #6, ...)\n"
        "## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #4, ...)\n"
        "## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #3, ...)\n"
        "## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #2, ...)\n"
        "## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #1, ...)\n",
        encoding="utf-8",
    )
    result = check_doc_rotation_mod.check_archive_gaps(tmp_path)
    assert result is not None
    _, diagnostic = result
    assert "unexpected session(s) [6]" in diagnostic, (
        f"expected unexpected [6] in diagnostic, got: {diagnostic!r}"
    )


def test_archive_gaps_fail_for_duplicate_heading(tmp_path: Path) -> None:
    """Archive mit zwei Headings für dieselbe Session-Nummer → ❌ DRIFT.

    Ohne Duplikat-Check würde ``set()`` den Bug wegdichten: zwei Headings
    für #3 + Heading für #4 = ``{3, 4}``, contiguous → OK. Aber genau das
    verschleiert den Drift (eine Session wäre doppelt rotiert).
    """
    (tmp_path / "CLAUDE.md").write_text(
        "## Session stopped — 2026-09-08 (MiniMax-M3-Exec-Session #5, ...)\n",
        encoding="utf-8",
    )
    (tmp_path / "SESSIONS_ARCHIVE.md").write_text(
        "## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #4, ...)\n"
        "## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #3, ...)\n"
        "## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #3, ...)\n"
        "## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #2, ...)\n"
        "## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #1, ...)\n",
        encoding="utf-8",
    )
    result = check_doc_rotation_mod.check_archive_gaps(tmp_path)
    assert result is not None
    _, diagnostic = result
    assert "duplicate heading(s) for session(s) [3]" in diagnostic


def test_archive_gaps_skip_phases_with_first_ever_session(tmp_path: Path) -> None:
    """Head=#1, Archive beliebig/leer → kein Check (erste Session der Phase)."""
    (tmp_path / "CLAUDE.md").write_text(
        "## Session stopped — 2026-09-08 (MiniMax-M3-Exec-Session #1, ...)\n",
        encoding="utf-8",
    )
    # Kein Archiv
    assert check_doc_rotation_mod.check_archive_gaps(tmp_path) is None
    # Auch leeres Archiv
    (tmp_path / "SESSIONS_ARCHIVE.md").write_text(
        "# Plan-Session-Block (kein Heading)\n", encoding="utf-8"
    )
    assert check_doc_rotation_mod.check_archive_gaps(tmp_path) is None


def test_archive_gaps_fail_for_archive_with_no_numeric_headings(tmp_path: Path) -> None:
    """Head=#5, Archive existiert, aber enthält keinen numerierten Block
    (z. B. nur einen Plan-Session-Block ohne Nummer) → ❌ DRIFT.

    Sonderfall, weil ``check_archive_sequence`` denselben Befund mit
    anderer Diagnostik meldet; wir prüfen die Lücken-Check-Variante.
    """
    (tmp_path / "CLAUDE.md").write_text(
        "## Session stopped — 2026-09-08 (MiniMax-M3-Exec-Session #5, ...)\n",
        encoding="utf-8",
    )
    (tmp_path / "SESSIONS_ARCHIVE.md").write_text(
        "## Session stopped — 2026-09-05 (Plan-Session, Fable 5.1)\n",
        encoding="utf-8",
    )
    result = check_doc_rotation_mod.check_archive_gaps(tmp_path)
    assert result is not None
    _, diagnostic = result
    assert "no parseable session numbers" in diagnostic


def test_strict_check_passes_for_phase16_activation_against_real_repo() -> None:
    """P16-F9: Echte Phase-16-Struktur post-F8 ist F9-konform.

    Subprozess-Aufruf gegen ``phase16_activation/CLAUDE.md`` +
    ``phase16_activation/SESSIONS_ARCHIVE.md`` (reparierter Stand).
    Wenn dieser Test grün ist, deckt der Hook die F8-Klasse ab.
    """
    result = subprocess.run(
        [sys.executable, str(_SCRIPT_PATH), "--strict", "--phase", "phase16_activation"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"check_doc_rotation.py --strict --phase phase16_activation failed:\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert "not contiguous" not in result.stdout.lower(), (
        f"unexpected Lücken-FAIL in repaired Phase-16 archive: {result.stdout!r}"
    )


def test_strict_check_fails_for_simulated_pre_f8_phase16_archive(
    tmp_path: Path, monkeypatch
) -> None:
    """P16-F9: Simulierter pre-F8-Phase-16-Stand erzeugt exit 1.

    Verifiziert, dass der neue Check gegen den Stand VOR der F8-Reparatur
    rot wäre — sonst prüft er nicht, was er prüfen soll (Selbsttest-Forderung
    aus dem Phasenkopf Session-#17 Next-Block).
    """
    # Layout: phase16_activation/CLAUDE.md + SESSIONS_ARCHIVE.md
    phase_dir = tmp_path / "phase16_activation"
    phase_dir.mkdir()
    (phase_dir / "CLAUDE.md").write_text(
        "## Session stopped — 2026-09-08 (MiniMax-M3-Exec-Session #17, ...)\n",
        encoding="utf-8",
    )
    # Pre-F8: Headings für #16, #15, #12..#1, Plan-Session ohne Nummer
    archive_lines = ["# SESSIONS_ARCHIVE\n\n"]
    archive_lines.append(
        "## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #16, ...)\n\n"
    )
    archive_lines.append(
        "## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #15, ...)\n\n"
    )
    # Hier fehlen die Headings für #14 und #13 (pre-F8-Drift)
    archive_lines.append(
        "> **Auftrag:** Body von Session #14 ohne Heading\n\n"
        "> **Auftrag:** Body von Session #13 ohne Heading\n\n"
    )
    for n in range(12, 0, -1):
        archive_lines.append(
            f"## Session stopped — 2026-09-07 (MiniMax-M3-Exec-Session #{n}, ...)\n\n"
        )
    archive_lines.append(
        "## Session stopped — 2026-09-05 (Plan-Session, Fable 5.1)\n"
    )
    (phase_dir / "SESSIONS_ARCHIVE.md").write_text(
        "".join(archive_lines), encoding="utf-8"
    )

    # Hauptskript gegen das tmp-Layout laufen lassen
    monkeypatch.setattr(check_doc_rotation_mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        check_doc_rotation_mod, "PHASE_DIRS", ("phase16_activation",)
    )
    monkeypatch.setattr(
        sys, "argv", ["check_doc_rotation", "--strict", "--quiet"]
    )
    rc = check_doc_rotation_mod.main()
    assert rc == 1, (
        f"expected exit 1 for pre-F8 simulated archive (gap at #13/#14), got {rc}"
    )


# ---------------------------------------------------------------------------
# P16-H-1 (2026-09-13) — Header-Card-Link-Check (Step 4 im `--strict`-Pfad).
#
# Audit-Session #19 hat 29 Header-Card-Link-Drifts aufgedeckt (Patterns A-E),
# gestreut über 12 Dateien in 6 Phasen + docs/concepts/. H-3 hat sie gestern
# (Session #28, Commit `fa51084`) repariert. H-1 fügt die maschinelle Prüfung
# hinzu, damit zukünftige Drifts beim ersten Commit gefangen werden, nicht
# erst in einer Folgesession.
#
# Akzeptanz (F-Exec-Plan §3 H-1):
# - A1 `test_header_card_up_link_ok` — `up:` zeigt auf existierende Datei → OK
# - A2 `test_header_card_down_links_with_inline_comment` — Inline-`#`-Kommentare
#       werden korrekt abgeschnitten
# - A3 `test_header_card_strip_markdown_preserves_underscores` — ``**`` und
#       Backticks weg, Underscores bleiben (PHASE10_CLOSEOUT_HANDOVER.md
#       wäre sonst kaputtgemacht worden)
# - A4 `test_header_card_prose_down_entry_is_ignored` — Regressions-Pin
#       für ``docs/INDEX.md:7 down: every project doc (that is the point)``
# - A5 `test_header_card_double_dotdot_is_flagged` — Pin für die 21
#       Pattern-A-Bugs aus H-3 (Link zeigt auf nicht-existierendes Ziel)
# - A6 `test_header_card_repo_is_clean` — End-to-End gegen das echte Repo,
#       schlägt fehl, sobald jemand eine kaputte Karte einführt
# ---------------------------------------------------------------------------


def test_header_card_up_link_ok(tmp_path: Path) -> None:
    """A1: `up: <existing-path>` → keine Befunde."""
    (tmp_path / "CLAUDE.md").write_text(
        "---\nstatus: live\npurpose: probe\nread-when: a\ndetail: L2\n"
        "up: ./CLAUDE.md\ndown:\n  - ./README.md\n"
        "updated: 2026-09-13\n---\n# Body\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("hi\n", encoding="utf-8")
    failures = check_doc_rotation_mod.check_header_card_links(tmp_path / "CLAUDE.md")
    assert failures == [], (
        f"expected no failures for self-referential up + existing README, "
        f"got: {failures}"
    )


def test_header_card_down_links_with_inline_comment(tmp_path: Path) -> None:
    """A2: `  - <path>  # Kommentar` — Kommentar wird vor der Pfad-Auflösung
    abgeschnitten, Pfad wird korrekt aufgelöst.

    Reproduziert den Normalfall der H-3-Reparatur-Phase: jeder
    `down:`-Eintrag trägt einen Inline-Kommentar (z. B. `# 📕 Vorgänger-Closeout`).
    Ohne Strip würde der Pfad den Kommentar enthalten und nicht auflösen.
    """
    (tmp_path / "CLAUDE.md").write_text(
        "---\nstatus: snapshot\npurpose: probe\nread-when: a\ndetail: L3\n"
        "up: ./CLAUDE.md\ndown:\n"
        "  - ./PHASE12_5_CLOSEOUT_HANDOVER.md   # 📕 Vorgänger\n"
        "  - ./phase14_discovery_concept.md    # 📕 Concept-Skizze\n"
        "updated: 2026-09-13\n---\n# Body\n",
        encoding="utf-8",
    )
    (tmp_path / "PHASE12_5_CLOSEOUT_HANDOVER.md").write_text("x", encoding="utf-8")
    (tmp_path / "phase14_discovery_concept.md").write_text("x", encoding="utf-8")
    failures = check_doc_rotation_mod.check_header_card_links(tmp_path / "CLAUDE.md")
    assert failures == [], (
        f"expected comments stripped + paths resolved, got: {failures}"
    )


def test_header_card_strip_markdown_preserves_underscores(tmp_path: Path) -> None:
    """A3: ``**``-Bold und Backticks werden entfernt, Underscores bleiben.

    Lock-Schritt 3 der H-1 Spec (F-Exec-Plan §3 H-1): ``_`` darf NICHT
    entfernt werden — Dateinamen wie ``PHASE10_CLOSEOUT_HANDOVER.md``
    tragen Underscores. Würde der Strip sie mit entfernen, wäre der
    Pfad falsch und der Hook FAILt auf einer intakten Datei. Regression-Pin.
    """
    (tmp_path / "CLAUDE.md").write_text(
        "---\nstatus: snapshot\npurpose: probe\nread-when: a\ndetail: L3\n"
        "up: ./CLAUDE.md\ndown:\n"
        "  - **`PHASE10_CLOSEOUT_HANDOVER.md`**   # 📕 Closeout, **bold** muss weg\n"
        "updated: 2026-09-13\n---\n# Body\n",
        encoding="utf-8",
    )
    (tmp_path / "PHASE10_CLOSEOUT_HANDOVER.md").write_text("x", encoding="utf-8")
    failures = check_doc_rotation_mod.check_header_card_links(tmp_path / "CLAUDE.md")
    assert failures == [], (
        f"expected underscores preserved + ** / backticks stripped, "
        f"got: {failures}"
    )


def test_header_card_prose_down_entry_is_ignored(tmp_path: Path) -> None:
    """A4: Prosa-Down-Eintrag ohne Slash und ohne .md/.py/.sql/.svg-Endung
    wird ignoriert (Lock-Schritt 5).

    Regression-Pin für ``docs/INDEX.md:7 down: every project doc (that is
    the point)`` — der Satz hat weder ``/`` noch eine Datei-Endung, ist
    also Prosa und wird zu Recht übersprungen. Würde der Check ihn als
    Link werten, würde er global FAILen und der Hook wäre unbenutzbar.
    """
    # up zeigt auf existierende Datei (damit der Test sich auf die Prosa-
    # Erkennung im `down:` konzentriert; der up:-Fehler wäre sonst Lärm).
    (tmp_path / "INDEX.md").write_text(
        "---\nstatus: live\npurpose: probe\nread-when: a\ndetail: L0\n"
        "up: ./INDEX.md\ndown: every project doc (that is the point)\n"
        "updated: 2026-09-13\n---\n# Body\n",
        encoding="utf-8",
    )
    failures = check_doc_rotation_mod.check_header_card_links(tmp_path / "INDEX.md")
    assert failures == [], (
        f"prosa-style 'down: every project doc (...)' must NOT be flagged, "
        f"got: {failures}"
    )


def test_header_card_double_dotdot_is_flagged(tmp_path: Path) -> None:
    """A5: `up: ../../<existing-dir>/X.md` aus einem `phase*/`-File ist ein
    kaputter Pfad (zeigt auf Repo-Root/<dir>/X.md statt auf phase*/<dir>/X.md
    — exakt die 21 Pattern-A-Befunde aus H-3).

    Reproduziert den Drift der in Session #28 (H-3, Commit `fa51084`)
    repariert wurde: die Files lagen in `phase*/` (nicht in `phase*/<dir>/`),
    also war `../` richtig, nicht `../../`.
    """
    phase_dir = tmp_path / "phase13_live_data"
    phase_dir.mkdir()
    # `../../phase12_data_foundation/...` aus phase13_live_data/foo.md
    # → tmp_path/phase12_data_foundation/... (existiert NICHT)
    (phase_dir / "PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md").write_text(
        "---\nstatus: snapshot\npurpose: probe\nread-when: a\ndetail: L3\n"
        "up: ../../phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md\n"
        "down:\n"
        "  - ../../phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md"
        "   # 📕 der falsche Pfad\n"
        "updated: 2026-09-13\n---\n# Body\n",
        encoding="utf-8",
    )
    failures = check_doc_rotation_mod.check_header_card_links(
        phase_dir / "PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md"
    )
    assert len(failures) == 2, (
        f"expected 2 failures (up + down both wrong), got: {failures}"
    )
    # Diagnostik muss Datei + Zeile nennen (Pin für lesbare Fehlermeldung)
    for diagnostic, _value in failures:
        assert "PHASE13_BEWEISWOCHE" in diagnostic, (
            f"diagnostic must name the offending file, got: {diagnostic!r}"
        )
        assert "does not exist" in diagnostic


def test_header_card_repo_is_clean() -> None:
    """A6: End-to-End gegen das echte Repo — alle 92 Header-Cards sind clean.

    Wenn dieser Test grün ist, fängt der Hook die nächste Drift der
    Audit-Session-#19-Klasse (Patterns A-E) ab dem ersten Commit ab.
    Body-Links sind out-of-scope per F-Exec-Plan §1.4 V-8 — der Test
    prüft nur Header-Cards, nicht Markdown-Link-Syntax im Fließtext.
    """
    bad: list[tuple[str, str]] = []
    for md_path in check_doc_rotation_mod._discover_step4_md_files(REPO_ROOT):
        failures = check_doc_rotation_mod.check_header_card_links(md_path)
        for diagnostic, _value in failures:
            bad.append((str(md_path.relative_to(REPO_ROOT)), diagnostic))
    assert not bad, (
        f"Header-Card-Link-Drift im Repo (Step 4 FAILt): {bad[:10]}... "
        f"({len(bad)} Befunde). Reparatur analog H-3-Patterns A-E aus "
        f"F-Exec-Plan §3."
    )
