#!/usr/bin/env python3
"""Phase 13 §6 C3 — source-delta diagnostic.

For every resolved ``paper_trades`` row in the requested window, re-resolve
the trade **per source** (yf only, then ls only) and report how often
the two sources disagree. The point is **P6 of the Block-A PASS criteria**
(Plan §7): a measurable, ongoing difference between sources is the
sentinel that something is wrong with one of them — a tick aggregator
silently dropping volume, a stale bar somehow surviving, a future-
timestamped candle.

Read-only. Operates in two modes:

- ``--day YYYY-MM-DD`` (default: today UTC): single-day report
- ``--days N`` (mutually exclusive with --day): last N days

Exit codes:
    0  OK         — the report was written, divergence rate computed
    1  READ ERROR — DB could not be opened or columns missing (the daemon
                     would not start under the same conditions, so this is
                     a loud Operator signal)
    0  DIVERGENCE — divergence rate is high but the report is still
                     written; the operator reads the JSON and decides
                     what to do. **No exit-code distinction by divergence**:
                     a high divergence rate is data, not an error.

Output discipline (repo convention): human narrative -> stderr, machine-
readable JSON -> stdout. ``--quiet`` silences the human part.
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


def _eprint(message: str = "") -> None:
    print(message, file=sys.stderr)


def _resolve_per_source(
    trade: dict, bars: list,
) -> tuple[str | None, float | None]:
    """Re-resolve one trade against one source's bars.

    Returns ``(exit_reason_str, pnl_points)`` — same shape as
    :func:`resolve_paper_trade` writes into ``paper_trades``. ``None``
    values mean the source had no bars (the source-delta report
    counts these rows as **not comparable**, not as agreement).
    """
    from abstain_lessons.paper import resolve_paper_trade, PaperExitReason
    if not bars:
        return None, None
    out = resolve_paper_trade(_trade_proxy(trade), bars)
    if out is None:
        return None, None
    exit_reason, exit_level = out
    pnl = _pnl_points(trade, exit_level)
    return exit_reason.value if isinstance(exit_reason, PaperExitReason) else str(exit_reason), pnl


def _trade_proxy(trade: dict) -> Any:
    """Build a PaperTrade-like object from a row dict. We don't use
    ``PaperTrade.from_row`` because we want to skip the row-parsing
    boilerplate (the script reads raw SQL); a tiny duck-typed proxy is
    enough for ``resolve_paper_trade`` (it only reads attributes).
    """
    from types import SimpleNamespace
    return SimpleNamespace(
        epic=trade["epic"],
        direction=trade["direction"],
        entry_level=trade["entry_level"],
        stop_distance=trade["stop_distance"],
        limit_distance=trade["limit_distance"],
        time_stop_utc=trade["time_stop_utc"],
        created_utc=trade["created_utc"],
    )


def _pnl_points(trade: dict, exit_level: float) -> float:
    sign = 1.0 if trade["direction"] == "BUY" else -1.0
    return sign * (exit_level - trade["entry_level"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--db", default=str(_DEFAULT_DB_PATH),
                        help=f"paper_trades SQLite path (default: {_DEFAULT_DB_PATH})")
    parser.add_argument("--bars-db", default=str(_DEFAULT_BARS_DB_PATH),
                        help=f"BarArchive SQLite path (default: {_DEFAULT_BARS_DB_PATH})")
    parser.add_argument("--day", help="single UTC day in YYYY-MM-DD (default: today)")
    parser.add_argument("--days", type=int, help="last N days (overrides --day)")
    parser.add_argument("--quiet", action="store_true", help="silence human narrative")
    args = parser.parse_args(argv)

    if args.day and args.days:
        _eprint("source_delta: --day and --days are mutually exclusive")
        return 1

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if args.days is not None:
        end_day = today
        start_day = (datetime.now(timezone.utc) - timedelta(days=args.days - 1)).strftime("%Y-%m-%d")
    elif args.day:
        start_day = end_day = args.day
    else:
        start_day = end_day = today

    start_iso = f"{start_day}T00:00:00.000Z"
    end_iso = f"{end_day}T23:59:59.999Z"

    # Phase 13 §6 C3: read-only against both DBs (mode=ro). A
    # READ ERROR (db not found, columns missing) → exit 1.
    try:
        conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    except sqlite3.OperationalError as exc:
        _eprint(f"source_delta: cannot open {args.db}: {exc}")
        return 1

    try:
        trades = _load_resolved_trades(conn, start_iso, end_iso)
    except sqlite3.OperationalError as exc:
        _eprint(f"source_delta: query failed: {exc}")
        conn.close()
        return 1
    conn.close()

    if not trades:
        _eprint(f"source_delta: no resolved trades in [{start_day}, {end_day}]")
        print(json.dumps({
            "ok": True, "start_day": start_day, "end_day": end_day,
            "trades_total": 0, "trades_agree": 0, "trades_diverge": 0,
            "trades_incomparable": 0, "divergence_rate": None, "rows": [],
        }))
        return 0

    # Open the bars DB once for the whole window. The trade fetches
    # a small (max_hold + 60 min) sub-window per row; one connection
    # is plenty fast.
    bars_conn = sqlite3.connect(f"file:{args.bars_db}?mode=ro", uri=True)
    try:
        rows = []
        n_agree = n_diverge = n_incomparable = 0
        for t in trades:
            window_start = t["created_utc"]
            window_end = _add_minutes(window_start, t.get("max_hold_min", 240) + 60)
            yf_bars = _fetch_bars(bars_conn, t["epic"], window_start, window_end, "yf")
            ls_bars = _fetch_bars(bars_conn, t["epic"], window_start, window_end, "ls")
            yf_reason, yf_pnl = _resolve_per_source(t, yf_bars)
            ls_reason, ls_pnl = _resolve_per_source(t, ls_bars)
            if yf_reason is None or ls_reason is None:
                n_incomparable += 1
                continue
            if yf_reason == ls_reason and (yf_pnl is None or ls_pnl is None or abs((yf_pnl or 0) - (ls_pnl or 0)) < 1e-9):
                n_agree += 1
                row_kind = "agree"
            else:
                n_diverge += 1
                row_kind = "diverge"
            rows.append({
                "paper_id": t["paper_id"],
                "epic": t["epic"],
                "created_utc": t["created_utc"],
                "yf": {"exit_reason": yf_reason, "pnl_points": yf_pnl, "n_bars": len(yf_bars)},
                "ls": {"exit_reason": ls_reason, "pnl_points": ls_pnl, "n_bars": len(ls_bars)},
                "kind": row_kind,
            })
    finally:
        bars_conn.close()

    n_total = n_agree + n_diverge + n_incomparable
    comparable = n_agree + n_diverge
    divergence_rate = (n_diverge / comparable) if comparable else None
    payload = {
        "ok": True,
        "start_day": start_day,
        "end_day": end_day,
        "trades_total": n_total,
        "trades_agree": n_agree,
        "trades_diverge": n_diverge,
        "trades_incomparable": n_incomparable,
        "divergence_rate": divergence_rate,
        "rows": rows,
    }
    if not args.quiet:
        _eprint(
            f"source_delta: {start_day}..{end_day} total={n_total} "
            f"agree={n_agree} diverge={n_diverge} incomparable={n_incomparable} "
            f"rate={divergence_rate:.2%}" if divergence_rate is not None else
            f"source_delta: {start_day}..{end_day} no trades to compare"
        )
    print(json.dumps(payload))
    return 0


def _load_resolved_trades(conn: sqlite3.Connection, start_iso: str, end_iso: str) -> list[dict]:
    """Read all resolved trades in [start_iso, end_iso] with a flat
    dict shape (no PaperTrade-construction here)."""
    cur = conn.execute(
        "SELECT paper_id, abstain_record_id, variant, epic, direction, "
        "created_utc, entry_level, stop_distance, limit_distance, time_stop_utc, "
        "exit_reason, exit_level, pnl_points "
        "FROM paper_trades "
        "WHERE status = 'RESOLVED' AND resolved_utc >= ? AND resolved_utc < ?",
        (start_iso, end_iso),
    )
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    return [dict(zip(cols, r)) for r in rows]


def _fetch_bars(
    conn: sqlite3.Connection, epic: str, start_iso: str, end_iso: str, source: str
) -> list[dict]:
    """One source's worth of bars for ``[start_iso, end_iso)``."""
    rows = conn.execute(
        "SELECT ts_utc, open, high, low, close, volume, tick_count "
        "FROM bars WHERE epic = ? AND resolution = '1m' "
        "AND source = ? AND ts_utc >= ? AND ts_utc < ? "
        "ORDER BY ts_utc ASC",
        (epic, source, start_iso, end_iso),
    ).fetchall()
    return [
        {
            "timestamp": r[0], "open": r[1], "high": r[2], "low": r[3],
            "close": r[4], "volume": r[5], "tick_count": r[6],
        }
        for r in rows
    ]


def _add_minutes(ts: str, minutes: int) -> str:
    try:
        normalized = ts.replace("Z", "+00:00") if ts.endswith("Z") else ts
        dt = datetime.fromisoformat(normalized) + timedelta(minutes=minutes)
        return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"
    except (ValueError, TypeError):
        return ts


if __name__ == "__main__":
    from typing import Any  # noqa: E402
    sys.exit(main())
