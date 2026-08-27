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

    python3 scripts/check_doc_rotation.py                  # all phases
    python3 scripts/check_doc_rotation.py --phase phase14_discovery
    python3 scripts/check_doc_rotation.py --quiet          # suppress OK rows
"""

from __future__ import annotations

import argparse
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
)

SESSION_HEADING = "## Session stopped"


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
    if not args.quiet:
        print("\nAll phase heads OK.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except OSError as exc:
        print(f"check_doc_rotation: I/O error: {exc}", file=sys.stderr)
        sys.exit(2)
