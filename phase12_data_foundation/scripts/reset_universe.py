#!/usr/bin/env python3
"""Operator script — reset the quarantined universe (Plan §6 Step 8 bullet 4, D18).

Sets every ``quarantined`` ``instrument_universe`` row back to
``status='discovered', fail_count=0, last_verified_at=NULL`` (precedent: the manual
2026-07-06 DB reset, ``phase9_universe/CLAUDE.md`` "Session stopped — 2026-07-06"). A
reset against a still-exhausted IG allowance would quarantine everything again within a
few verify rounds — not just ineffective but actively harmful (repeated 403s, more
allowance burned). D18's gate: refuse unless ``data/bars.sqlite``'s ``allowance_observations``
table has a row **younger than 24h** with ``remaining > reserve_points`` — written by
``probe_allowance.py``, which must therefore run first.

Live, writes the real trading DB — not run in tests (same "operator-run" convention as
``wiring.py``). Weekend-only per the plan's bot-touching rule (Root ``CLAUDE.md`` §1: bot
stopped, market closed). Nikinger-run per ``feedback_live_testing``.

Output discipline: human narrative -> stderr, machine-readable JSON -> stdout. Exit 0 on a
successful reset (including "nothing to reset" — zero quarantined rows is not a failure),
exit 1 when the D18 gate refuses.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DB_PATH = _REPO_ROOT / "data" / "trading_bot.sqlite"
_DEFAULT_BARS_DB_PATH = _REPO_ROOT / "data" / "bars.sqlite"
_FRESHNESS_HOURS = 24


def _eprint(message: str = "") -> None:
    print(message, file=sys.stderr)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def _parse(ts_utc: str) -> datetime:
    normalized = ts_utc.replace("Z", "+00:00") if ts_utc.endswith("Z") else ts_utc
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _check_restart_gate(bars_db_path: str, reserve_points: int, *, now: datetime) -> tuple[bool, str]:
    """D18: a fresh (< 24h) observation with ``remaining > reserve_points``. Returns
    ``(allowed, reason)`` — never raises on a missing table (a bars.sqlite that never
    saw a probe is the same "not allowed" case as a stale/exhausted one)."""
    conn = sqlite3.connect(bars_db_path)
    try:
        row = conn.execute(
            "SELECT observed_at, remaining FROM allowance_observations "
            "WHERE remaining IS NOT NULL ORDER BY observed_at DESC LIMIT 1"
        ).fetchone()
    except sqlite3.OperationalError:
        return False, "no allowance_observations table yet — run probe_allowance.py first"
    finally:
        conn.close()

    if row is None:
        return False, "no allowance observation on record — run probe_allowance.py first"
    observed_at, remaining = row
    age = now - _parse(observed_at)
    if age > timedelta(hours=_FRESHNESS_HOURS):
        return False, f"latest observation is {age} old (> {_FRESHNESS_HOURS}h) — run probe_allowance.py again"
    if remaining <= reserve_points:
        return False, f"latest observation remaining={remaining} <= reserve={reserve_points} — allowance still exhausted"
    return True, f"observed {observed_at}: remaining={remaining} > reserve={reserve_points}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db-path", default=str(_DEFAULT_DB_PATH), help="instrument_universe SQLite path")
    parser.add_argument("--bars-db", default=str(_DEFAULT_BARS_DB_PATH), help="allowance_observations SQLite path")
    parser.add_argument(
        "--reserve-points", type=int, default=1_500,
        help="D10 reserve floor (default: 1500, matches SourceBudget's default)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="bypass the D18 restart gate (NOT recommended — only for a documented, "
             "deliberate manual override; the gate exists because a premature reset "
             "re-quarantines everything within a few verify rounds)",
    )
    args = parser.parse_args(argv)

    now = datetime.now(timezone.utc)
    allowed, reason = _check_restart_gate(args.bars_db, args.reserve_points, now=now)
    _eprint(f"[reset_universe] D18 gate: {reason}")
    if not allowed and not args.force:
        print(json.dumps({"ok": False, "reset": 0, "gate_reason": reason}))
        return 1
    if not allowed and args.force:
        _eprint("[reset_universe] --force set: bypassing the gate despite the reason above.")

    from universe.models import STATUS_DISCOVERED, STATUS_QUARANTINED

    conn = sqlite3.connect(args.db_path)
    try:
        epics = [r[0] for r in conn.execute(
            "SELECT epic FROM instrument_universe WHERE status = ?", (STATUS_QUARANTINED,)
        ).fetchall()]
        conn.execute(
            "UPDATE instrument_universe SET status = ?, fail_count = 0, "
            "last_verified_at = NULL, updated_at = ? WHERE status = ?",
            (STATUS_DISCOVERED, _iso(now), STATUS_QUARANTINED),
        )
        conn.commit()
    finally:
        conn.close()

    _eprint(f"[reset_universe] reset {len(epics)} quarantined epic(s) to 'discovered': {epics}")
    print(json.dumps({"ok": True, "reset": len(epics), "epics": epics, "gate_reason": reason}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
