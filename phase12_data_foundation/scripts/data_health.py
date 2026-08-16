#!/usr/bin/env python3
"""Operator script — today's measurement health + budget status (Plan §6 Step 6).

Read-only, weekday-safe: no migration, no write to any trading-relevant table (only
reads ``bars.sqlite`` and the shared ``trading_bot.sqlite``). Prints
:class:`~data_foundation.heartbeat.HealthVerdict` for ``--day`` (default: **today**,
UTC calendar day), the IG budget's current standing, and the Recorder's
heartbeat-state age; exits ``1`` when the verdict is ``ok=False`` — an operator or
cron job can gate on the exit code without parsing the printed text.

**Default-day caveat:** run before the trading day's POST_WINDOW pass (e.g. a morning
cron), today's own verdict will legitimately show ``ok=False`` — nothing has
happened yet, not a real outage. Pass ``--day`` with yesterday's date (or the last
trading day) for a genuine end-of-day review.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DB_PATH = _REPO_ROOT / "data" / "trading_bot.sqlite"
_DEFAULT_BARS_DB_PATH = _REPO_ROOT / "data" / "bars.sqlite"
_DEFAULT_RECORDER_STATE_PATH = _REPO_ROOT / "data" / "state" / "recorder_state.json"


def _print_recorder_heartbeat_age(state_path: Path, *, now: datetime) -> None:
    if not state_path.exists():
        print(f"Recorder heartbeat: no state file at {state_path} (Recorder never ticked)")
        return
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
        last_ts = payload.get("ts")
        last = datetime.fromisoformat(last_ts.replace("Z", "+00:00")) if last_ts else None
    except (OSError, ValueError, json.JSONDecodeError):
        print(f"Recorder heartbeat: unreadable state file at {state_path}")
        return
    if last is None:
        print(f"Recorder heartbeat: state file at {state_path} has no 'ts'")
        return
    age_min = (now - last).total_seconds() / 60.0
    print(f"Recorder heartbeat: last tick {last_ts} ({age_min:.0f} min ago)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", default=str(_DEFAULT_DB_PATH))
    parser.add_argument("--bars-db", default=str(_DEFAULT_BARS_DB_PATH))
    parser.add_argument("--recorder-state", default=str(_DEFAULT_RECORDER_STATE_PATH))
    parser.add_argument("--day", default=None, help="YYYY-MM-DD (default: today, UTC)")
    parser.add_argument("--shadow-enabled", action="store_true",
                         help="whether Phase-11 (H1) time-scheduled shadow pairs are on")
    args = parser.parse_args(argv)

    from data_foundation.archive import BarArchive
    from data_foundation.budget import IG_QUOTA_V1, SourceBudget
    from data_foundation.heartbeat import assess_day

    now = datetime.now(timezone.utc)
    day = args.day or now.strftime("%Y-%m-%d")

    archive = BarArchive(args.bars_db)
    archive.ensure_schema()
    verdict = assess_day(
        archive, args.db_path, args.db_path, day, shadow_enabled=args.shadow_enabled
    )

    print(f"=== Measurement health — {verdict.day} ===")
    print(f"ok: {verdict.ok}")
    print(f"bars_today: {verdict.bars_today}")
    print(f"pairs_opened: {verdict.pairs_opened}")
    print(f"pairs_resolved: {verdict.pairs_resolved}")
    print(f"pairs_typed_expired: {verdict.pairs_typed_expired}")
    print(f"measurable_epics: {verdict.measurable_epics}")
    for problem in verdict.problems:
        print(f"  problem: {problem}")

    budget = SourceBudget(args.bars_db, IG_QUOTA_V1)
    spent = budget.spent_in_window()
    remaining = budget.remaining_estimate()
    daily_rate = spent / IG_QUOTA_V1.window_days if IG_QUOTA_V1.window_days else 0.0
    exhaustion = budget.predicted_exhaustion_days(daily_rate) if daily_rate > 0 else None
    print("\n=== IG budget ===")
    print(f"spent_in_window: {spent}")
    print(f"remaining_estimate: {remaining}")
    print(f"predicted_exhaustion_days (at the observed avg daily rate): {exhaustion}")

    print("\n=== Recorder ===")
    _print_recorder_heartbeat_age(Path(args.recorder_state), now=now)

    return 0 if verdict.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
