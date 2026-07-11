#!/usr/bin/env python3
"""S7 — deterministic ``abstain_records`` summary report. No network, no AI, no LLM call.

    python phase10_v3/scripts/abstain_report.py --db data/trading_bot.sqlite

Reads directly (read-only intent — no writes anywhere in this script). Output is
plain text on stdout, entirely derived from the DB's current contents.
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def _counts_by_reason(conn: sqlite3.Connection) -> list[tuple[str, int]]:
    rows = conn.execute(
        "SELECT reason, COUNT(*) FROM abstain_records GROUP BY reason ORDER BY reason"
    ).fetchall()
    return [(r[0], r[1]) for r in rows]


def _recent(conn: sqlite3.Connection, limit: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT created_utc, epic, stage, reason, lesson_extracted FROM abstain_records "
        "ORDER BY created_utc DESC LIMIT ?",
        (limit,),
    ).fetchall()


def _lesson_ratio(conn: sqlite3.Connection) -> tuple[int, int]:
    total = conn.execute("SELECT COUNT(*) FROM abstain_records").fetchone()[0]
    with_lesson = conn.execute(
        "SELECT COUNT(*) FROM abstain_records WHERE lesson_extracted = 1"
    ).fetchone()[0]
    return with_lesson, total


def build_report(db_path: str, *, recent_n: int = 10) -> str:
    """Build the full report text (no trailing newline)."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        counts = _counts_by_reason(conn)
        recent = _recent(conn, recent_n)
        with_lesson, total = _lesson_ratio(conn)
    finally:
        conn.close()

    lines = ["=== Abstain-Records Report ===", "", "Counts by reason:"]
    if counts:
        lines.extend(f"  {reason}: {n}" for reason, n in counts)
    else:
        lines.append("  (none)")
    lines.append("")
    lines.append(f"Lesson coverage: {with_lesson}/{total}")
    lines.append("")
    lines.append(f"Last {recent_n} record(s):")
    if recent:
        for row in recent:
            flag = "L" if row["lesson_extracted"] else "-"
            lines.append(
                f"  [{flag}] {row['created_utc']} {row['stage']} {row['reason']} "
                f"{row['epic'] or '-'}"
            )
    else:
        lines.append("  (none)")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic abstain_records summary — no network, no AI."
    )
    parser.add_argument("--db", required=True, type=Path, help="path to the SQLite DB")
    parser.add_argument(
        "--recent", type=int, default=10, help="how many recent records to list (default 10)"
    )
    args = parser.parse_args(argv)
    print(build_report(str(args.db), recent_n=args.recent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
