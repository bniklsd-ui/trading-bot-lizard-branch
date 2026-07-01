#!/usr/bin/env python3
"""Read-only ``bot_score`` distribution diagnostic (v1.5 hotfix, Step 1).

Reports the distribution of ``reward_pts.score_after`` (the "bot_score" that gates the
Phase-4 long-bias clamp / confidence floor, ``candidate_filter.py``) over the full trade
history in the live DB. Pure read — **no writes, no pipeline change**. This exists so the
operator can hand real numbers to the Step-3 floor-tuning decision in the v1.5 hotfix
(``docs/concepts/phase8_v1.5_hotfix_plan.md``) instead of guessing a replacement value.

Deliberately phase-less: this script is not owned by any phase package (the hotfix plan's
own cross-phase-edit register lists it with no phase). It has **zero** cross-phase Python
imports — stdlib only (``sqlite3``/``statistics``/``argparse``/``json``) — so it can never
entangle with the phase-import-isolation discipline the rest of the repo maintains.

DB access mirrors ``phase8_scheduler/webui/api.py``'s ``ro_connect()``: opened via the
``file:...?mode=ro`` URI, so a write is refused by SQLite itself (OS-level guarantee, not
just discipline). Duplicated rather than imported — ``webui``/``scripts`` are excluded from
the installed packages, and reusing ``persistence.Database`` was considered and rejected
(it opens read-write and has no full-series getter — see the v1.5 Step-1 plan for the full
weighing).

Output discipline (repo convention, mirrors ``phase7_reward/scripts/inspect_history.py``):
human-readable narrative -> **stderr**; the machine-readable JSON payload -> **stdout**,
always, no flag needed. Exit 0 in every expected case, including all "insufficient history"
paths (this is a report tool, not a pass/fail test) — a genuinely unexpected error is not
swallowed.

Usage:
    python scripts/diag_score_distribution.py
    python scripts/diag_score_distribution.py --db-path /path/to/other.sqlite
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any

# scripts/ -> repo root (mirrors the phase scripts' <phase>/scripts/ -> repo-root convention,
# one level shallower since this script has no phase directory above it).
_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DB_PATH = _REPO_ROOT / "data" / "trading_bot.sqlite"

# The real system default `get_current_score()` returns when reward_pts is empty
# (persistence/db.py `_DEFAULT_SCORE`). Mirrored here, not imported (stdlib-only script).
_DEFAULT_CURRENT_SCORE = 50.0

# Echoes reward.confidence's n_min=10 concept (Wilson-LB stability floor) as an informal,
# local literal -- NOT an import, to keep this script dependency-free and phase-less.
_SMALL_SAMPLE_N = 10

# The two thresholds the v1.5 hotfix cares about: the long-bias clamp fires below 50
# (ResearchConfig.long_bias_below_score), and Option B4 considers a "strongly biased"
# regime below 35. Both boundaries are exclusive (strict `<`), matching candidate_filter.py.
_LONG_BIAS_THRESHOLD = 50.0
_STRONG_BIAS_THRESHOLD = 35.0

_QUERY = """
    SELECT r.score_after AS score_after, r.calculated_at AS calculated_at, t.account AS account
    FROM reward_pts r
    LEFT JOIN trade_outcomes t ON t.id = r.trade_id
    ORDER BY r.id ASC
"""


def _eprint(message: str = "") -> None:
    print(message, file=sys.stderr)


def _ro_connect(db_path: str) -> sqlite3.Connection:
    """Open the DB **read-only** (``mode=ro``) — a write attempt raises ``OperationalError``.

    Mirrors ``phase8_scheduler/webui/api.py:ro_connect`` (the repo's established isolation
    pattern for read-only diagnostics). Rows come back as ``sqlite3.Row`` (dict-like).
    """
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _load_score_rows(db_path: str) -> tuple[list[sqlite3.Row], str | None]:
    """Load the full ``reward_pts`` series (oldest -> newest), fail-soft.

    Returns ``(rows, reason)``. ``reason`` is ``None`` on success (rows may still be empty
    if the table genuinely has no data yet — see the ``"no reward_pts rows"`` case);
    otherwise it names *why* nothing came back, so the operator isn't left guessing between
    "wrong path" and "DB not initialized yet".
    """
    if not Path(db_path).exists():
        return [], "database not found"

    conn = _ro_connect(db_path)
    try:
        rows = conn.execute(_QUERY).fetchall()
    except sqlite3.OperationalError:
        return [], "reward_pts table missing"
    finally:
        conn.close()

    if not rows:
        return [], "no reward_pts rows"
    return list(rows), None


def compute_distribution(scores: list[float]) -> dict[str, Any]:
    """Pure stats over an **ordered (chronological, ascending)** score series.

    No I/O — fully unit-testable in isolation. ``current`` is the *last* element (matches
    ``get_current_score()``'s "most recent" semantics), not the max — callers must pass the
    series in ``id ASC`` order, not sorted by value.
    """
    n = len(scores)
    if n == 0:
        return {
            "n": 0,
            "insufficient": True,
            "small_sample": False,
            "current_score": _DEFAULT_CURRENT_SCORE,
            "stats": {"min": None, "max": None, "median": None, "mean": None, "p25": None, "p75": None},
            "thresholds": {
                "below_50": {"count": 0, "pct": None},
                "below_35": {"count": 0, "pct": None},
            },
        }

    if n >= 2:
        p25, _p50, p75 = statistics.quantiles(scores, n=4, method="inclusive")
    else:
        p25 = p75 = None

    below_50 = sum(1 for s in scores if s < _LONG_BIAS_THRESHOLD)
    below_35 = sum(1 for s in scores if s < _STRONG_BIAS_THRESHOLD)

    return {
        "n": n,
        "insufficient": False,
        "small_sample": n < _SMALL_SAMPLE_N,
        "current_score": scores[-1],
        "stats": {
            "min": min(scores),
            "max": max(scores),
            "median": statistics.median(scores),
            "mean": statistics.fmean(scores),
            "p25": p25,
            "p75": p75,
        },
        "thresholds": {
            "below_50": {"count": below_50, "pct": below_50 / n},
            "below_35": {"count": below_35, "pct": below_35 / n},
        },
    }


def _bucket_accounts(rows: list[sqlite3.Row]) -> dict[str, int]:
    """Tally ``account`` across rows, folding NULL (pre-migration-002 rows) into ``"unknown"``."""
    counter: Counter[str] = Counter(row["account"] or "unknown" for row in rows)
    return dict(counter)


def _date_range(rows: list[sqlite3.Row]) -> dict[str, str | None]:
    """Earliest/latest ``calculated_at`` from the already ``id ASC``-ordered rows."""
    if not rows:
        return {"earliest": None, "latest": None}
    return {"earliest": rows[0]["calculated_at"], "latest": rows[-1]["calculated_at"]}


def build_report(db_path: str, rows: list[sqlite3.Row], reason: str | None) -> dict[str, Any]:
    """Assemble the stable JSON payload (same shape whether data is present or not)."""
    scores = [float(row["score_after"]) for row in rows]
    dist = compute_distribution(scores)
    return {
        "db_path": db_path,
        "reason": reason,
        "accounts": _bucket_accounts(rows),
        "date_range": _date_range(rows),
        **dist,
    }


def _format_report(payload: dict[str, Any]) -> str:
    """Human-readable narrative for stderr."""
    lines = [f"[diag] DB: {payload['db_path']}"]
    if payload["insufficient"]:
        lines.append(f"[diag] insufficient history ({payload['reason']}) — nothing to measure yet.")
        lines.append(f"[diag] current_score would default to {payload['current_score']} (system default).")
        return "\n".join(lines)

    n = payload["n"]
    stats = payload["stats"]
    thr = payload["thresholds"]
    lines.append(f"[diag] n={n}" + ("  (small sample, n<{})".format(_SMALL_SAMPLE_N) if payload["small_sample"] else ""))
    lines.append(f"[diag] current_score = {payload['current_score']:.2f}")
    lines.append(
        f"[diag] min={stats['min']:.2f}  p25={_fmt(stats['p25'])}  median={stats['median']:.2f}  "
        f"p75={_fmt(stats['p75'])}  max={stats['max']:.2f}  mean={stats['mean']:.2f}"
    )
    lines.append(
        f"[diag] below 50: {thr['below_50']['count']}/{n} ({thr['below_50']['pct'] * 100:.1f}%)  "
        f"below 35: {thr['below_35']['count']}/{n} ({thr['below_35']['pct'] * 100:.1f}%)"
    )
    lines.append(f"[diag] accounts: {payload['accounts']}")
    lines.append(f"[diag] date range: {payload['date_range']['earliest']} .. {payload['date_range']['latest']}")
    return "\n".join(lines)


def _fmt(value: float | None) -> str:
    return f"{value:.2f}" if value is not None else "n/a"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db-path",
        default=str(_DEFAULT_DB_PATH),
        help=f"path to the SQLite DB (default: {_DEFAULT_DB_PATH})",
    )
    args = parser.parse_args(argv)

    rows, reason = _load_score_rows(args.db_path)
    payload = build_report(args.db_path, rows, reason)

    _eprint(_format_report(payload))
    print(json.dumps(payload, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
