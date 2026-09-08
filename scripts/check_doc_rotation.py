#!/usr/bin/env python3
"""Doc-rotation hygiene check (Mini-Session 16, 2026-08-27).

Verifies the Doc-Layers convention (root ``CLAUDE.md`` §"How to work in this repo",
Rotation rule): each phase head carries **exactly one** ``## Session stopped`` block.
Older session blocks live in the phase's ``SESSIONS_ARCHIVE.md`` (newest-first).

Why this exists (Session-12 finding, restated): the rotation rule is documented but
**not machine-checkable**. Inline-duplicates of session blocks (Session 11 was
inlined below Session 13 at one point) slipped through review because no tool caught
the violation. This script is the structural fix: one ``grep -c`` per phase head,
exit code 0 or 1.

**Read-only — no writes, no git operations.** Pure Markdown count, no network,
no keyring, no shell-out. Safe as a pre-commit hook or operator smoke-check.

Exit codes:
  0 — every phase head carries **at most one** ``## Session stopped`` block
      (0 = no session history, 1 = canonical; 2+ = inline-duplicate drift).
  1 — at least one phase head violates the rule (printed to stdout).
  2 — I/O error (missing phase directory, etc.).

The rule is "at most one", not "exactly one", because a phase that has
never held a session has zero blocks and is canonical (precedent:
``phase2_persistence``, closed Phase 11 before any session was written).
The drift this catches is the Session-12 finding (Session 11 was inlined
below Session 13 → two ``## Session stopped`` blocks in one phasenkopf).

Usage::

    python3 scripts/check_doc_rotation.py                       # Step-1 only (default)
    python3 scripts/check_doc_rotation.py --strict             # Step-1 + Step-2 (P14-F) + Step-3 (P16-F9)
    python3 scripts/check_doc_rotation.py --phase phase14_discovery
    python3 scripts/check_doc_rotation.py --quiet              # suppress OK rows

The ``--strict`` mode runs two additional checks beyond the default
inline-duplicate count (Step 1):

- Step 2 (P14-F): ``check_archive_sequence`` — head's max session number
  must equal archive's max + 1 (Anschluss Phasenkopf→Archiv).
- Step 3 (P16-F9, 2026-09-08): ``check_archive_gaps`` — archive's
  per-heading session numbers must form a contiguous descending range
  from 1 to head_max - 1 (Lückenlosigkeit der Archiv-Nummern). This
  caught F8 (Session #17): two blocks had lost their ``## Session stopped``
  headings in earlier rotations, leaving ``#16, #15, #12, #11, …, #1`` —
  Step 2 still passed because the head's predecessor was correctly set,
  but the gap at #13/#14 was silent. Step 3 makes that drift loud.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Phase directories that own a phase head (CLAUDE.md) under the rotation rule.
# Mirrors the active-closed list in docs/INDEX.md (closed phases kept — they
# also carry session blocks). meta_m1_harness is excluded because its archive
# is a separate `SESSIONS_ARCHIVE.md` and its rotation follows the same rule;
# included here for symmetry.
PHASE_DIRS: tuple[str, ...] = (
    "phase1_broker_wrapper",
    "phase2_persistence",
    "phase3_external_data",
    "phase4_research",
    "phase5_execution",
    "phase6_debate",
    "phase7_reward",
    "phase8_scheduler",
    "phase9_universe",
    "phase10_v3",
    "meta_m1_harness",
    "phase12_data_foundation",
    "phase13_live_data",
    "phase14_discovery",
    "phase15_v4",
    "phase16_activation",
)

SESSION_HEADING = "## Session stopped"

# P15-F plan §2 D2: permissiver gegen MiniMax-Vendor-Prefix und optionales '#'-Zeichen.
# Matcht weiterhin P14-F-Stand („Session N", „Mini-Session N") plus die Phase-15-
# Vokabulare („Exec-Session #N", „MiniMax-M3-Exec-Session #N"). \w+ im Prefix-
# Block matched jeden Vendor-Prefix (MiniMax-M3, MiniMax-4, MiniMax-Opus, …),
# sodass zukünftige Varianten ohne Mini-Plan-Anpassung laufen.
_SESSION_NUM_RE = re.compile(
    r"(?:Mini-|MiniMax-\w+-Exec-|Exec-)?Session\s+#?(\d+)"
)


def _max_session_num(md_text: str) -> int | None:
    """Return the largest ``Session N``-number found in ``## Session stopped``
    heading lines of the Markdown body, or ``None`` if no session heading
    carries one.

    Robust gegen die aktuellen zwei Namensvarianten („Session N", „Mini-Session N")
    via ``(?:Mini-)?Session\\s+(\\d+)``. Eine Phasenkopf-Datei hat per Konvention
    nur einen Block; ``max`` ist trotzdem sicherer als ``first`` (defensive).

    Nur H2-Heading-Zeilen werden gescannt (nicht Body-Prose) — sonst fängt die
    Regex False-Positives wie „Folge-Session 2026-07-17" (Jahr) oder
    „Session 12/13" (Kommentar). Plan §8.5 hatte das False-Positive-Risiko als
    „gering" eingestuft; die Realität (mehrere Phasen mit Body-Erwähnungen)
    macht die Einschränkung auf die Heading-Zeile strukturell nötig.
    """
    nums: list[int] = []
    for line in md_text.splitlines():
        if not line.startswith(SESSION_HEADING):
            continue
        for m in _SESSION_NUM_RE.finditer(line):
            nums.append(int(m.group(1)))
    return max(nums) if nums else None


def check_archive_sequence(phase_dir: Path) -> tuple[str, str] | None:
    """P14-F Step 2: prüfe, dass ``head-N == archive-max-(N-1)``.

    Returns:
        ``None`` wenn OK, sonst ``(phase_name, diagnostic)`` für die FAIL-Zeile.

    Invariante: Wenn ein Phasenkopf genau einen ``Session N``-Block hat, muss das
    Archiv (sofern existent) einen Block mit Session-Number ``N-1`` enthalten,
    oder leer sein wenn ``N == 1`` (erste Session der Phase). Eine Lücke ist
    ein Doc-Rotation-Drift, der in Mini-Session 21 (Commit ``5d587a0``)
    operativ aufgetreten ist.
    """
    head = phase_dir / "CLAUDE.md"
    if not head.exists():
        return None  # kein Phasenkopf → kein Step-2-Check
    head_max = _max_session_num(head.read_text(encoding="utf-8"))
    if head_max is None:
        return None  # keine Sessions im Phasenkopf → nichts zu prüfen

    archive = phase_dir / "SESSIONS_ARCHIVE.md"
    if not archive.exists():
        if head_max == 1:
            return None  # erste Session der Phase, Archiv ist erwartet leer
        return (phase_dir.name,
                f"head has Session {head_max} but no SESSIONS_ARCHIVE.md "
                f"(expected Sessions 1..{head_max - 1})")

    arch_max = _max_session_num(archive.read_text(encoding="utf-8"))
    expected = head_max - 1
    if arch_max is None:
        if head_max == 1:
            return None  # erste Session der Phase, Archiv darf leer sein
        return (phase_dir.name,
                f"head has Session {head_max} but SESSIONS_ARCHIVE.md has "
                f"no parseable session numbers (expected Session {expected})")
    if arch_max != expected:
        return (phase_dir.name,
                f"head has Session {head_max} but archive newest is Session "
                f"{arch_max} (expected {expected}) — sequence gap")
    return None


def _first_session_num_per_heading(md_text: str) -> list[int]:
    """For each ``## Session stopped`` heading line in ``md_text``, return the
    FIRST ``Session #N``-number found on that line.

    Headings without a parseable session number (e.g. the Plan-Session block
    in Phase 16's archive, or pre-numeric-session prose) are skipped — the
    regex needs the literal substring ``Session`` followed by whitespace, then
    an optional ``#`` and digits; ``Plan-Session, Fable 5.1`` does not match
    because the char immediately after ``Session`` is a comma, not whitespace.

    The returned list is in file order (newest-first for archive files
    written by the rotation rule, oldest-first if a future convention
    changes).

    P16-F9 (2026-09-08): the archive-gap check needs each block's PRIMARY
    session number, not the MAX across the line — heading bodies routinely
    reference previous sessions (e.g. the ``#16`` heading also mentions
    ``Session #15``). ``_max_session_num`` was unsuitable because it takes
    the max; the gap check needs the per-block primary number.
    """
    nums: list[int] = []
    for line in md_text.splitlines():
        if not line.startswith(SESSION_HEADING):
            continue
        m = _SESSION_NUM_RE.search(line)
        if m is not None:
            nums.append(int(m.group(1)))
    return nums


def check_archive_gaps(phase_dir: Path) -> tuple[str, str] | None:
    """P16-F9 (2026-09-08): prüfe, dass die Archiv-Nummern lückenlos sind.

    Returns:
        ``None`` wenn OK, sonst ``(phase_name, diagnostic)`` für die FAIL-Zeile.

    Invariante: wenn der Phasenkopf genau einen ``Session N``-Block hat,
    muss das Archiv für jedes ``k in 1..N-1`` genau einen Block mit
    Session-Number ``k`` enthalten. Plan-Session-Blocks ohne Nummer sind
    korrekt ausgenommen (siehe Preamble der Archive-Disziplin).

    Diese Prüfung ist eine Verschärfung von ``check_archive_sequence``
    (P14-F Step 2): jene prüft nur ``arch_max == head_max - 1``, also den
    Anschluss Phasenkopf→Archiv. Ein Archiv mit ``#16, #14, #13, …, #1``
    (Lücke bei #15) bestünde diese Prüfung, ist aber ein Doc-Rotation-Drift.

    Genau das ist in Session #17 (F8) operativ aufgetreten: die Rotationen
    der Sessions #14/#15 haben je die ``## Session stopped``-Überschrift der
    Blöcke #13/#14 verloren — der damalige ``--strict``-Hook hat das nicht
    gemeldet, weil die Prüfung nur den Anschluss, nicht die Lückenlosigkeit
    prüfte.
    """
    head = phase_dir / "CLAUDE.md"
    if not head.exists():
        return None  # kein Phasenkopf → keine Prüfung
    head_max = _max_session_num(head.read_text(encoding="utf-8"))
    if head_max is None:
        return None  # keine numerierten Sessions im Phasenkopf
    if head_max <= 1:
        return None  # head=#1 ⇒ Archiv darf leer sein / fehlen

    archive = phase_dir / "SESSIONS_ARCHIVE.md"
    if not archive.exists():
        # check_archive_sequence behandelt diesen Fall bereits (head>1 ohne
        # Archive = FAIL); hier doppeln wir die Diagnostik nicht.
        return None

    nums = _first_session_num_per_heading(archive.read_text(encoding="utf-8"))
    if not nums:
        # Archiv existiert, aber enthält keinen numerierten Block. head>1
        # ohne numerierte Blöcke = Lücke über alle 1..head_max-1; konsistent
        # mit check_archive_sequence, das den Fall auch behandelt.
        return (phase_dir.name,
                f"head has Session {head_max} but archive has no "
                f"parseable session numbers (expected Sessions 1..{head_max - 1})")

    found = set(nums)
    expected = set(range(1, head_max))
    missing = sorted(expected - found)
    extra = sorted(found - expected)
    # Duplikate: gleiche Nummer in zwei Headings (würde die Lücken-Logik
    # verschleiern, weil set() sie wegdichtet).
    seen: set[int] = set()
    duplicates: list[int] = []
    for n in nums:
        if n in seen and n not in duplicates:
            duplicates.append(n)
        seen.add(n)

    if not missing and not extra and not duplicates:
        return None  # lückenlos

    parts: list[str] = []
    if missing:
        parts.append(f"missing session(s) {missing}")
    if extra:
        parts.append(f"unexpected session(s) {extra}")
    if duplicates:
        parts.append(f"duplicate heading(s) for session(s) {duplicates}")
    return (phase_dir.name,
            f"archive session numbers are not contiguous ({'; '.join(parts)}, "
            f"found first-per-heading: {nums}, expected contiguous range "
            f"1..{head_max - 1})")


def count_session_blocks(md_text: str) -> int:
    """Count ``## Session stopped`` H2 headings in a Markdown body.

    Only the heading line itself counts — leading ``---`` dividers and the
    footer pointer paragraph are ignored. A line counts only if it starts
    with the heading prefix (no leading whitespace, no inline markup that
    would push it past H2).
    """
    return sum(
        1 for line in md_text.splitlines() if line.startswith(SESSION_HEADING)
    )


def check_phase(phase_dir: Path) -> tuple[int, str]:
    """Return (count, label) for one phase head.

    ``count`` is the number of ``## Session stopped`` blocks in the phasenkopf.
    ``label`` is ``"<phase_dir.name> (no CLAUDE.md)"`` when the head is missing.
    """
    head = phase_dir / "CLAUDE.md"
    if not head.exists():
        return 0, f"{phase_dir.name} (no CLAUDE.md)"
    text = head.read_text(encoding="utf-8")
    return count_session_blocks(text), phase_dir.name


def main() -> int:
    """Run the rotation check, return a POSIX exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase",
        action="append",
        default=None,
        help=(
            "Restrict check to these phase directories (relative to repo root). "
            "Repeatable. Default: every phase in PHASE_DIRS."
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-phase output on success; print only failures.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Enable Step-2 archive-sequence check in addition to Step-1 "
            "duplicate-block check (P14-F). Default: Step-1 only — "
            "the pre-commit hook should only be hardened once the new "
            "check has been proved against the current archive state."
        ),
    )
    args = parser.parse_args()
    selected = args.phase if args.phase else list(PHASE_DIRS)

    bad: list[tuple[str, int]] = []
    for name in selected:
        phase_dir = REPO_ROOT / name
        count, label = check_phase(phase_dir)
        if count > 1:
            bad.append((label, count))
            print(
                f"[FAIL] {label}: {count} session blocks "
                "(expected at most 1 — inline-duplicate drift)"
            )
        elif not args.quiet:
            kind = "no session history" if count == 0 else "1 session block"
            print(f"[OK]   {label}: {kind}")
    if bad:
        print(
            f"\n{len(bad)} phase(s) violate the Doc-Layers rotation rule "
            "(at most one '## Session stopped' block per phasenkopf)."
        )
        return 1

    # P14-F Step 2: Archive-Sequenz-Integrität (default off, opt-in via
    # --strict). D5: bewusste Trennung Tool-Bau vs. Tool-Verschärfung —
    # die Folgesession (oder --strict-Flag, falls Beweis-Skript grün)
    # aktiviert das im Pre-Commit-Hook.
    #
    # P16-F9 (2026-09-08): im selben --strict-Lauf zusätzlich prüfen, dass
    # die Archiv-Nummern lückenlos sind. check_archive_sequence prüft nur
    # den Anschluss Phasenkopf→Archiv, nicht die Lückenlosigkeit der
    # Archiv-Nummern selbst (genau diese Lücke hat F8 drei Sessions lang
    # unentdeckt bleiben lassen).
    if getattr(args, "strict", False):
        seq_bad: list[tuple[str, str]] = []
        for name in selected:
            result = check_archive_sequence(REPO_ROOT / name)
            if result is not None:
                seq_bad.append(result)
                label, diagnostic = result
                print(f"[FAIL] {label}: {diagnostic}")
            # P16-F9: Lücken-Check im selben Pass
            gap_result = check_archive_gaps(REPO_ROOT / name)
            if gap_result is not None:
                seq_bad.append(gap_result)
                label, diagnostic = gap_result
                print(f"[FAIL] {label}: {diagnostic}")
        if seq_bad:
            return 1  # keine Inline-Duplicates, aber Sequenz- oder Lücken-FAIL → fail

    if not args.quiet:
        print("\nAll phase heads OK.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except OSError as exc:
        print(f"check_doc_rotation: I/O error: {exc}", file=sys.stderr)
        sys.exit(2)
