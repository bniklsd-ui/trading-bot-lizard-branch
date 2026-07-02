#!/usr/bin/env python3
"""Archive verification (code-test) trades out of the live DB (v1.6 hotfix, Cause A part 2).

**Why this exists:** the v1.5 Phase-8 hotfix (Step 4 A) tagged verification-trade *lessons*
so they'd be quarantined out of the P4 research prompt, but a live v1.6 run showed the LLM's
abstain reasoning still citing fake "three consecutive losses totaling ~345€" — the three
seeded, forced sub-minute-time-stop demo trades from earlier smoke/live tests
(`trade_outcomes.id` 1-3), read straight off the **separate, unfiltered** `recent_trades`
prompt channel (`db.get_recent_trades`). Two fixes landed together (v1.6, Cause A part 2):

1. Code (`phase2_persistence`/`phase4_research`/`phase7_reward`): `trade_outcomes` gained a
   `provenance` column (migration 003) + a filtered `get_recent_trades_for_prompt` read, mirroring
   the existing lesson filter. New verification trades are auto-excluded from the prompt going
   forward. **This script is not that fix** — it's cleanup for the three trades that predate it.
2. **This script:** a one-time, operator-run archive of those pre-existing verification trades
   (and everything that cascades from them — lessons, rewards, regime snapshots, decision
   context) out of the live DB, for a clean slate before the real autonomous live-proof run.
   The code-side filter (1) already excludes them from the prompt via the `hold_duration_min`
   fallback (they're all untagged/NULL provenance, pre-dating migration 003) — this script is
   pure hygiene, not required for the filter to work.

**Selection (two independent signals, OR'd):** `provenance = 'verification'` (trades opened
since the P5 write-path fix) **or** `hold_duration_min < --hold-threshold-min` (fallback —
catches the pre-migration trades, which predate the tag entirely and are all sub-minute forced
time-stops). `--ids` overrides both with an explicit `trade_outcomes.id` allow-list.

**Safety:** dry-run by default — prints exactly what would be archived + deleted, writes
nothing, deletes nothing. Only `--commit` writes `data/archive/verification_<UTC-stamp>.json`
(every selected `trade_outcomes` row plus its cascaded `trade_lessons`/`reward_pts`/
`market_regime_snapshots`/`decision_context` rows, captured **before** any delete) and then
deletes the selected `trade_outcomes` rows. Deletes are child-table-safe by construction: the
live `Database` opens with `PRAGMA foreign_keys = ON` (`persistence/db.py`), and every child
table's `trade_id` column is declared `... REFERENCES trade_outcomes(id) ON DELETE CASCADE`
(`phase2_persistence/migrations/001_initial.sql`) — deleting the parent row cascades the
children automatically; no separate child-table deletes needed.

Output discipline (repo convention, mirrors `verify_instrument.py`/`resolve_epics.py`): human
narrative -> **stderr**; machine-readable JSON -> **stdout**, always. Exit 0 on every expected
outcome (report tool, not a pass/fail test runner).

Usage:
    python scripts/archive_verification_trades.py                    # dry-run, default selection
    python scripts/archive_verification_trades.py --commit           # actually archive + delete
    python scripts/archive_verification_trades.py --ids 1,2,3 --commit   # explicit trade ids
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

_DEFAULT_HOLD_THRESHOLD_MIN = 2.0  # mirrors ResearchConfig.recent_trades_min_hold_min (v1.6)

# Every table whose rows cascade-delete when their parent trade_outcomes row is deleted
# (all declared "trade_id ... REFERENCES trade_outcomes(id) ON DELETE CASCADE" in
# migrations/001_initial.sql). Collected here as an archive snapshot BEFORE the delete —
# the DB's own FK cascade does the actual child-row removal.
_CHILD_TABLES = ("trade_lessons", "reward_pts", "market_regime_snapshots", "decision_context")


def _eprint(message: str = "") -> None:
    print(message, file=sys.stderr)


def select_verification_trades(
    conn: Any, *, hold_threshold_min: float = _DEFAULT_HOLD_THRESHOLD_MIN, ids: list[int] | None = None
) -> list[dict[str, Any]]:
    """Select ``trade_outcomes`` rows that look like verification/test trades.

    Two independent signals, OR'd (mirrors the read-path prompt filter's precision order):
    a precise ``provenance = 'verification'`` tag (trades opened since migration 003 / the P5
    write-path fix), or the ``hold_duration_min`` fallback (catches trades that predate the
    tag entirely — a forced sub-minute time-stop). ``ids`` bypasses both and selects exactly
    the given ``trade_outcomes.id`` values (operator override, e.g. a known-good demo trade
    that happened to close fast should NOT be swept up by the hold-time heuristic).
    """
    if ids is not None:
        if not ids:
            return []
        placeholders = ",".join("?" * len(ids))
        rows = conn.execute(
            f"SELECT * FROM trade_outcomes WHERE id IN ({placeholders})", ids
        ).fetchall()
        return [dict(r) for r in rows]
    rows = conn.execute(
        "SELECT * FROM trade_outcomes WHERE provenance = 'verification' "
        "OR (hold_duration_min IS NOT NULL AND hold_duration_min < ?)",
        (hold_threshold_min,),
    ).fetchall()
    return [dict(r) for r in rows]


def collect_related(conn: Any, trade_ids: list[int]) -> dict[str, list[dict[str, Any]]]:
    """Pull every child-table row referencing ``trade_ids`` — the archive snapshot's payload.

    Must run **before** :func:`delete_trades` (the delete cascades these away).
    """
    if not trade_ids:
        return {table: [] for table in _CHILD_TABLES}
    placeholders = ",".join("?" * len(trade_ids))
    related: dict[str, list[dict[str, Any]]] = {}
    for table in _CHILD_TABLES:
        rows = conn.execute(
            f"SELECT * FROM {table} WHERE trade_id IN ({placeholders})", trade_ids
        ).fetchall()
        related[table] = [dict(r) for r in rows]
    return related


def delete_trades(conn: Any, trade_ids: list[int]) -> None:
    """Delete the selected ``trade_outcomes`` rows; FK cascade removes the children.

    Caller commits. A no-op for an empty ``trade_ids`` (never reached — ``main`` short-circuits
    on an empty selection before calling this).
    """
    if not trade_ids:
        return
    placeholders = ",".join("?" * len(trade_ids))
    conn.execute(f"DELETE FROM trade_outcomes WHERE id IN ({placeholders})", trade_ids)


def build_archive_payload(
    selected: list[dict[str, Any]], related: dict[str, list[dict[str, Any]]], *, archived_at: str
) -> dict[str, Any]:
    """Assemble the JSON snapshot written to ``data/archive/verification_<ts>.json``."""
    return {
        "archived_at": archived_at,
        "reason": (
            "Phase 8 v1.6 hotfix, Cause A part 2 — quarantine verification/code-test trades "
            "out of the live DB (see scripts/archive_verification_trades.py docstring)."
        ),
        "trade_outcomes": selected,
        **related,
    }


def _format_report(selected: list[dict[str, Any]], related: dict[str, list[dict[str, Any]]]) -> str:
    lines = ["[archive] verification-trade archive (Phase 8 v1.6, Cause A part 2)"]
    if not selected:
        lines.append("  no matching trades — nothing to do.")
        return "\n".join(lines)
    for row in selected:
        lines.append(
            f"  id={row['id']} deal_id={row.get('deal_id')} epic={row.get('epic')} "
            f"hold_min={row.get('hold_duration_min')} provenance={row.get('provenance')!r} "
            f"status={row.get('status')}"
        )
    counts = ", ".join(f"{len(rows)} {table}" for table, rows in related.items() if rows)
    lines.append(f"  cascading: {counts}" if counts else "  cascading: none")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--db-path", default=None,
        help="live DB path (default: <repo_root>/data/trading_bot.sqlite — the real P2 path)",
    )
    parser.add_argument(
        "--hold-threshold-min", type=float, default=_DEFAULT_HOLD_THRESHOLD_MIN,
        help=f"hold-time fallback threshold in minutes (default: {_DEFAULT_HOLD_THRESHOLD_MIN})",
    )
    parser.add_argument(
        "--ids", default=None,
        help="comma-separated trade_outcomes.id list — overrides auto-selection entirely",
    )
    parser.add_argument(
        "--commit", action="store_true",
        help="actually write the archive file + delete the rows; default is dry-run (no writes)",
    )
    parser.add_argument(
        "--archive-dir", default=None,
        help="archive output dir (default: <repo_root>/data/archive)",
    )
    args = parser.parse_args(argv)

    # Lazy cross-phase import (phaseless-script convention, mirrors verify_instrument.py) —
    # `import scripts.archive_verification_trades` (unit tests) needs no DB on the path.
    from persistence.db import Database

    repo_root = Path(__file__).resolve().parent.parent
    db_path = args.db_path or str(repo_root / "data" / "trading_bot.sqlite")
    archive_dir = Path(args.archive_dir) if args.archive_dir else repo_root / "data" / "archive"

    ids = [int(x) for x in args.ids.split(",") if x.strip()] if args.ids else None

    db = Database(db_path)
    try:
        selected = select_verification_trades(
            db.conn, hold_threshold_min=args.hold_threshold_min, ids=ids
        )
        trade_ids = [row["id"] for row in selected]
        related = collect_related(db.conn, trade_ids)

        _eprint(_format_report(selected, related))

        if not selected:
            print(json.dumps({"selected": [], "committed": False, "archive_path": None}, indent=2))
            return 0

        if not args.commit:
            _eprint("[archive] DRY RUN — no changes written. Re-run with --commit to archive + delete.")
            print(
                json.dumps({"selected": trade_ids, "committed": False, "archive_path": None}, indent=2)
            )
            return 0

        archived_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_path = archive_dir / f"verification_{stamp}.json"
        payload = build_archive_payload(selected, related, archived_at=archived_at)
        archive_path.write_text(json.dumps(payload, indent=2, default=str))
        _eprint(f"[archive] wrote {archive_path}")

        delete_trades(db.conn, trade_ids)
        db.conn.commit()
        _eprint(f"[archive] deleted {len(trade_ids)} trade(s) (+ cascaded rows) from the live DB.")

        print(
            json.dumps(
                {"selected": trade_ids, "committed": True, "archive_path": str(archive_path)},
                indent=2,
            )
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
