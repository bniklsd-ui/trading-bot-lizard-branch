#!/usr/bin/env python3
"""Operator tool — reset the latest ``reward_pts.score_after`` to the neutral baseline.

Phase 15 / Block B / Step B6 (Plan §6): the live ``reward_pts.score_after`` has drifted
upward through the inverted-reward window (Plan §3 B1, P15-D3 SVG column ③). After
B1 + B2 (process_weight 1.5 → 0.5) the math is honest again, but the historical
score is the sum of the broken deltas. This script sets the **latest** score back
to the neutral baseline ``50.0`` (== ``_DEFAULT_SCORE`` in P2 ``db.py:50``), which
is what the bot's sizing layer (``Database.get_risk_level``) treats as the
KONSERVATIV/AGGRESSIV boundary.

**Hard safety:** ``--dry-run`` is the default. The script writes nothing to the
live DB without an explicit ``--apply`` flag. The Nikinger runs ``--apply`` after
the dry-run output has been audited (Plan §11 #3).

**Idempotency:** the operation is a single conditional UPDATE on the MAX(id)
row. Running it twice with ``--apply`` is a no-op the second time — the latest
row is already 50.0, the WHERE clause matches zero rows.

**What it does NOT touch:**
- ``trade_outcomes`` rows (untouched — the trades themselves are historical truth).
- ``reward_pts`` rows other than the latest one.
- The ``calculated_at`` timestamp of the modified row — UPDATE only changes
  ``score_after``, leaving the audit trail of when the score was originally
  calculated intact.

Output discipline (matches Phase-7 operator-script convention):
- progress + before/after table + audit block → **stderr**
- single machine-readable summary JSON → **stdout**

Exit codes: ``0`` on success (dry-run reports what would happen, ``--apply``
writes), ``1`` on missing DB / no reward_pts rows, ``2`` on SQL error.

Usage::

    # Inspect (default — dry-run)
    python scripts/reset_score_baseline.py

    # Inspect against a custom DB path
    python scripts/reset_score_baseline.py --db-path /tmp/test.sqlite

    # Apply the reset (writes to the live DB — Nikinger action)
    python scripts/reset_score_baseline.py --apply
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

# Repo-root relative default — the real path comes from the Phase-7
# RewardConfig.live_db_path (= "data/trading_bot.sqlite"). We mirror it here
# to avoid an import dependency on Phase-7's reward package; the script must
# run even when reward imports fail (e.g. partial checkout).
_DEFAULT_LIVE_DB = "data/trading_bot.sqlite"
_NEUTRAL_SCORE = 50.0

_SELECT_COLUMNS = (
    "id",
    "trade_id",
    "outcome_score_delta",
    "process_score_delta",
    "score_after",
)

_UPDATE_SQL = (
    "UPDATE reward_pts "
    "SET score_after = ? "
    "WHERE id = (SELECT id FROM reward_pts ORDER BY id DESC LIMIT 1)"
)


def _connect(db_path: Path) -> sqlite3.Connection:
    """Open the DB with row-factory + FK + print SQL errors to stderr."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _read_all_reward_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Return every ``reward_pts`` row, newest first.

    The plan §6 B6 says "alle 8 Zeilen" — the table is expected to hold 8 rows
    (one per closed trade at the time of Phase-15-B execution, Plan §2.2). If it
    holds more, we show all of them; if fewer, we show what we have.
    """
    cur = conn.execute(
        "SELECT id, trade_id, outcome_score_delta, process_score_delta, score_after "
        "FROM reward_pts ORDER BY id ASC"
    )
    return list(cur.fetchall())


def _print_table(rows: list[sqlite3.Row], *, title: str) -> None:
    """Print a fixed-width table to stderr (progress channel)."""
    print(f"\n=== {title} ({len(rows)} rows) ===", file=sys.stderr)
    if not rows:
        print("  (no rows)", file=sys.stderr)
        return
    header = f"{'id':>4}  {'trade_id':>9}  {'outcome_delta':>13}  {'process_delta':>13}  {'score_after':>11}"
    print(header, file=sys.stderr)
    print("-" * len(header), file=sys.stderr)
    for row in rows:
        print(
            f"{row['id']:>4}  "
            f"{row['trade_id']:>9}  "
            f"{row['outcome_score_delta']:>+13.3f}  "
            f"{row['process_score_delta']:>+13.3f}  "
            f"{row['score_after']:>11.3f}",
            file=sys.stderr,
        )


def _build_audit_block(
    *,
    db_path: Path,
    mode: str,
    latest_id: int | None,
    latest_score_before: float | None,
    latest_score_after: float | None,
    applied: bool,
) -> str:
    """Build the paste-into-CLAUDE.md audit block (Plan §6 B6 #5).

    The block is human-readable Markdown with the same vocabulary the
    existing session blocks use (e.g. ``phase15_v4/CLAUDE.md``).
    """
    score_before_str = f"{latest_score_before:.2f}" if latest_score_before is not None else "n/a"
    score_after_str = f"{latest_score_after:.2f}" if latest_score_after is not None else "n/a"
    latest_id_str = str(latest_id) if latest_id is not None else "n/a"
    return (
        "## Score-Reset Audit Block (Phase 15 / Block B / Step B6)\n"
        "\n"
        f"- db_path: `{db_path}`\n"
        f"- mode: `{mode}`\n"
        f"- applied: `{applied}`\n"
        f"- latest reward_pts id: `{latest_id_str}`\n"
        f"- latest score_after (before): `{score_before_str}`\n"
        f"- latest score_after (after):  `{score_after_str}`\n"
        f"- neutral baseline: `{_NEUTRAL_SCORE}` (== `Database._DEFAULT_SCORE`)\n"
        "- AK6 evidence: score-reset script exists; --dry-run output is below; --apply was\n"
        "  executed under explicit Nikinger-Freigabe (Plan §11 #3).\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reset the latest reward_pts.score_after to 50.0 (dry-run by default).",
    )
    parser.add_argument(
        "--db-path",
        default=_DEFAULT_LIVE_DB,
        help=f"Path to the SQLite DB (default: {_DEFAULT_LIVE_DB!r}).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually write the UPDATE. Default: dry-run (no writes).",
    )
    args = parser.parse_args(argv)

    db_path = Path(args.db_path).resolve()
    mode = "apply" if args.apply else "dry-run"
    print(f"[reset_score_baseline] mode={mode}  db_path={db_path}", file=sys.stderr)

    if not db_path.exists():
        print(f"[reset_score_baseline] ERROR: db not found at {db_path}", file=sys.stderr)
        return 1

    try:
        conn = _connect(db_path)
    except sqlite3.Error as exc:
        print(f"[reset_score_baseline] ERROR: cannot open db: {exc}", file=sys.stderr)
        return 2

    try:
        before_rows = _read_all_reward_rows(conn)
        _print_table(before_rows, title="reward_pts BEFORE")
        if not before_rows:
            print(
                "[reset_score_baseline] ERROR: reward_pts has no rows — nothing to reset",
                file=sys.stderr,
            )
            return 1

        latest_row = before_rows[-1]
        latest_id = int(latest_row["id"])
        latest_score_before = float(latest_row["score_after"])

        applied = False
        latest_score_after: float | None = None

        if args.apply:
            if abs(latest_score_before - _NEUTRAL_SCORE) < 1e-9:
                print(
                    f"[reset_score_baseline] --apply: latest row id={latest_id} "
                    f"already at {_NEUTRAL_SCORE}; no-op",
                    file=sys.stderr,
                )
                latest_score_after = latest_score_before
                applied = True  # Operation completed; nothing changed (idempotent).
            else:
                cur = conn.execute(_UPDATE_SQL, (_NEUTRAL_SCORE,))
                conn.commit()
                if cur.rowcount != 1:
                    print(
                        f"[reset_score_baseline] ERROR: UPDATE affected "
                        f"{cur.rowcount} rows, expected 1",
                        file=sys.stderr,
                    )
                    return 2
                applied = True
                latest_score_after = _NEUTRAL_SCORE
                print(
                    f"[reset_score_baseline] --apply: row id={latest_id} "
                    f"score_after {latest_score_before:.2f} -> {_NEUTRAL_SCORE:.2f}",
                    file=sys.stderr,
                )
        else:
            # dry-run: don't write, just predict
            print(
                f"[reset_score_baseline] dry-run: would UPDATE row id={latest_id} "
                f"score_after {latest_score_before:.2f} -> {_NEUTRAL_SCORE:.2f} "
                f"(no write performed)",
                file=sys.stderr,
            )
            latest_score_after = (
                _NEUTRAL_SCORE
                if abs(latest_score_before - _NEUTRAL_SCORE) > 1e-9
                else latest_score_before
            )

        after_rows = _read_all_reward_rows(conn)
        _print_table(after_rows, title="reward_pts AFTER")

        audit = _build_audit_block(
            db_path=db_path,
            mode=mode,
            latest_id=latest_id,
            latest_score_before=latest_score_before,
            latest_score_after=latest_score_after,
            applied=applied,
        )
        print("\n--- AUDIT BLOCK (paste into phase15_v4/CLAUDE.md) ---", file=sys.stderr)
        print(audit, file=sys.stderr)
        print("--- END AUDIT BLOCK ---\n", file=sys.stderr)

        summary = {
            "ok": True,
            "db_path": str(db_path),
            "mode": mode,
            "applied": applied,
            "latest_id": latest_id,
            "latest_score_before": latest_score_before,
            "latest_score_after": latest_score_after,
            "neutral_score": _NEUTRAL_SCORE,
            "row_count": len(after_rows),
        }
        print(json.dumps(summary, ensure_ascii=False))
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
