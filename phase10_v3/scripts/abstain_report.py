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


def _paper_counts_by_variant(conn: sqlite3.Connection) -> list[tuple[str, int]]:
    rows = conn.execute(
        "SELECT variant, COUNT(*) FROM paper_trades GROUP BY variant ORDER BY variant"
    ).fetchall()
    return [(r[0], r[1]) for r in rows]


def _paper_counts_by_exit(conn: sqlite3.Connection) -> list[tuple[str, int]]:
    """Buckets by ``exit_reason`` when resolved, else the raw ``status`` (OPEN/EXPIRED_UNRESOLVED)."""
    rows = conn.execute(
        "SELECT COALESCE(exit_reason, status) AS bucket, COUNT(*) FROM paper_trades "
        "GROUP BY bucket ORDER BY bucket"
    ).fetchall()
    return [(r[0], r[1]) for r in rows]


def _abstain_validation_rate(conn: sqlite3.Connection) -> tuple[int, int]:
    """Among abstain records with BOTH shadow sides RESOLVED: how many had both sides
    lose or break even (``pnl_points <= 0``) — the count where the abstain looked
    correct, over the count of resolved pairs (Both-Sides-Shadow-Tracking, V3-D6)."""
    rows = conn.execute(
        "SELECT abstain_record_id, variant, pnl_points, status FROM paper_trades "
        "WHERE variant IN ('SHADOW_BUY', 'SHADOW_SELL')"
    ).fetchall()
    by_record: dict[str, dict[str, tuple[float | None, str]]] = {}
    for record_id, variant, pnl_points, status in rows:
        by_record.setdefault(record_id, {})[variant] = (pnl_points, status)

    validated = 0
    resolved_pairs = 0
    for sides in by_record.values():
        if "SHADOW_BUY" not in sides or "SHADOW_SELL" not in sides:
            continue
        (buy_pnl, buy_status) = sides["SHADOW_BUY"]
        (sell_pnl, sell_status) = sides["SHADOW_SELL"]
        if buy_status != "RESOLVED" or sell_status != "RESOLVED":
            continue
        resolved_pairs += 1
        if buy_pnl is not None and sell_pnl is not None and buy_pnl <= 0 and sell_pnl <= 0:
            validated += 1
    return validated, resolved_pairs


def build_report(db_path: str, *, recent_n: int = 10, include_paper: bool = False) -> str:
    """Build the full report text (no trailing newline). ``include_paper=False`` (the
    default) keeps the original Block-A abstain-only report bit-identical."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        counts = _counts_by_reason(conn)
        recent = _recent(conn, recent_n)
        with_lesson, total = _lesson_ratio(conn)
        if include_paper:
            paper_by_variant = _paper_counts_by_variant(conn)
            paper_by_exit = _paper_counts_by_exit(conn)
            validated, resolved_pairs = _abstain_validation_rate(conn)
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

    if include_paper:
        lines.append("")
        lines.append("=== Paper-Trades Report ===")
        lines.append("")
        lines.append("Counts by variant:")
        if paper_by_variant:
            lines.extend(f"  {variant}: {n}" for variant, n in paper_by_variant)
        else:
            lines.append("  (none)")
        lines.append("")
        lines.append("Counts by exit (or status if still open):")
        if paper_by_exit:
            lines.extend(f"  {bucket}: {n}" for bucket, n in paper_by_exit)
        else:
            lines.append("  (none)")
        lines.append("")
        lines.append(
            f"Abstain-Validierungsquote: {validated}/{resolved_pairs} resolved pairs "
            "(both shadow sides negative or breakeven)"
        )

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic abstain_records summary — no network, no AI."
    )
    parser.add_argument("--db", required=True, type=Path, help="path to the SQLite DB")
    parser.add_argument(
        "--recent", type=int, default=10, help="how many recent records to list (default 10)"
    )
    parser.add_argument(
        "--paper", action="store_true",
        help="also include the Block-B paper-trades section (counts by variant/exit, "
        "abstain-validation rate)",
    )
    args = parser.parse_args(argv)
    print(build_report(str(args.db), recent_n=args.recent, include_paper=args.paper))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
