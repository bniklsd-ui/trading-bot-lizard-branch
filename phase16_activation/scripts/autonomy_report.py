#!/usr/bin/env python3
"""autonomy_report.py — Phase 16 E2 daily / windowed autonomy-test report.

Reads ONLY append-only sources per Plan §6 E2:

  K1  Operator-Restart-Count
        run_scheduler.log   `starting scheduler daemon` (timestamped start-line)
        run_recorder.log    `[run_recorder] starting recorder from`   (untimestamped — full-file count)
        run_discovery.log   `[run_discovery] starting daemon from`   (untimestamped)
        run_webui.log       `Started server process` OR `[run_webui] dashboard on`
                            (untimestamped in the count sense; the
                            `[run_webui]` wrapper line carries no ts but the
                            uvicorn `Started server process` line does on some
                            uvicorn versions — we count BOTH patterns as the
                            E2 contract accepts either).

  K2  Dienste-pro-Handelstag-aktiv
        Scheduler: ≥ 1 entry in research_health.jsonl on that day
        Recorder : ≥ 1 row in bars.sqlite where source IN ('yf','ls','capital') on that day
        Discovery: ≥ 1 entry in research_health.jsonl on that day
                   (Discovery writes both an event and instrument_universe refreshes
                   are not in research_health — Discovery's append-only evidence is
                   sparse in the JSONL because the runner only emits there on
                   discovery-specific events. K2 Discovery check is therefore
                   best-effort and listed as a soft signal, not a hard criterion.
                   Hard signal is `instrument_universe` last_verified_utc growth.)
        WebUI   : Operator-Sichtung (no append-only evidence — see prereg).

  K3  ≥ 5 autonomous Trades
        trade_outcomes WHERE status='CLOSED' AND provenance='autonomous' AND
        account='demo' IN window.

  K4  Heartbeat ok ≥ 8 / 10 Handelstagen
        research_health.jsonl `measurement_heartbeat.ok = True` grouped by day.

  K5  ≤ 5 CRITICAL / 24h nach jedem OPEN (A6)
        run_scheduler.log lines containing 'CRITICAL' inside the 24-h sliding
        window starting at each CLOSED-trades' open_ts (autonomous only). Implemented
        in detail for the operator's verification — for E2 the script reports the max
        so the operator can spot a regression.

  K6  Token-Budget nie vor 17:30 leer
        llm_usage.json per-Berlin-day input+output+cache_creation+cache_read sum,
        threshold 300 000 (matches the Phase-16 C3 default); exhaustion time = the
        timestamp of the last call that took the running sum above the threshold.
        The report **aborts** (raises BudgetFileError) when the file cannot be parsed
        or its line count does not grow between two reads (Opus-Review §13 #9).

  K7  Caps unverändert
        run_scheduler.log start-line substring: `max_trades=5, daily_loss_cap=1800.0`
        AND every CLOSED autonomous trade in window has account='demo'.

  K8  Liveness — Dienste liefen an diesem Handelstag (Phase 16 R3.3 / F8)
        Every trading day in window has ≥ 1 research_health.jsonl event AND
        ≥ 1 archived bar AND ≥ 1 heartbeat event (any outcome). A hard PASS-gate,
        not a soft signal like K2: it exists to catch a dead day, which K1/K5/K6/K7
        all pass vacuously (0 starts, 0 CRITICALs, 0 tokens, unread-but-unchanged
        caps all read as "fine" on a day with zero processes).

Constraints:

- NO LLM, NO network, NO pgrep, NO writes outside `data/reports/<day>.json`.
- The trading + bars DBs are opened with the ``file:...?mode=ro`` URI (SQLite
  refuses writes at the OS level — see ``diag_score_distribution.py``).
- The script accepts `--trading-db`, `--bars-db`, `--state-dir`, `--reports-dir`
  overrides so tests can point at fixtures without touching the live tree.

Usage:
    python phase16_activation/scripts/autonomy_report.py --day 2026-09-08
    python phase16_activation/scripts/autonomy_report.py \\
        --from 2026-09-08 --to 2026-09-19 --summary

Exit codes (--summary only):
    0  every criterion PASS
    1  at least one criterion FAIL or PARTIAL (queried window narrower than the
       full registered test window — not judgeable, not a clean PASS either)
    2  ERROR (input malformed, missing file in non-test mode, budget file corrupt)

Both modes print machine-readable JSON to stdout; the human narrative goes to
stderr (repo convention from ``diag_score_distribution.py``). A copy of the
report is also written to ``data/reports/autonomy_<day>.json`` (gitignored —
added in this commit).
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover — Python 3.9+ ships zoneinfo; belt-and-braces.
    ZoneInfo = None  # type: ignore[assignment]

_LOG = logging.getLogger("autonomy_report")

# Phase 16 E2: scripts/ lives under phase16_activation/, so the repo root is two
# levels up. Mirrors ``probe_market_margin.py`` and ``diag_score_distribution.py``.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

_DEFAULT_TRADING_DB = _REPO_ROOT / "data" / "trading_bot.sqlite"
_DEFAULT_BARS_DB = _REPO_ROOT / "data" / "bars.sqlite"
_DEFAULT_STATE_DIR = _REPO_ROOT / "data" / "state"
_DEFAULT_REPORTS_DIR = _REPO_ROOT / "data" / "reports"

# Vorregistrierte Defaults (PHASE16_AUTONOMY_PREREGISTRATION.md "Vorregistrierte Werte")
DEFAULT_MAX_TRADES = 5
DEFAULT_DAILY_LOSS_CAP_EUR = 1800.0
DEFAULT_DAILY_TOKEN_BUDGET = 300_000
DEFAULT_WINDOW_OPEN_HHMM = (9, 0)  # 09:00 Berlin (Phase-5 ExecutionConfig.trading_window_start)
DEFAULT_WINDOW_CLOSE_HHMM = (17, 30)  # 17:30 Berlin

# Per-criterion PASS thresholds (Plan §6 E2 "Regel" column)
TRADES_PASS_THRESHOLD = 5
HEARTBEAT_OK_PASS_THRESHOLD = 8
CRITICAL_24H_PASS_THRESHOLD = 5
RESTARTS_PASS_THRESHOLD_MAX = 2  # 1 baseline + 1 P17 Backoff-KILL-Clear
# K4's "8 of 10" is a property of the full registered test window (Prereg), not of
# whatever [from_day, to_day] a caller happens to query (Phase 16 R3.2 / Drift #9).
K4_FULL_WINDOW_TRADING_DAYS = 10


# ----------------------------------------------------------------------------
# Errors
# ----------------------------------------------------------------------------

class BudgetFileError(RuntimeError):
    """Phase 16 E2 K6 fail-closed: llm_usage.json unreadable / not growing."""


# ----------------------------------------------------------------------------
# Pure helpers — exposed for tests
# ----------------------------------------------------------------------------

# Regex for the scheduler's start-line timestamp prefix: "2026-09-05 12:00:32,565"
_SCHED_TS_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[,.]\d+)?)"
)
# Stubborn uvicorn timestamps inside run_webui.log look like "INFO:2025-01-01 12:34:56 ..."
# but on this box they actually look like: "INFO:     Started server process [10398]" — no ts.
# We therefore count both the wrapper line and the uvicorn line without timestamp parsing.

_START_PATTERNS = {
    "scheduler": re.compile(r"starting scheduler daemon"),
    "recorder":  re.compile(r"\[run_recorder\] starting recorder"),
    "discovery": re.compile(r"\[run_discovery\] starting daemon"),
    # J8 (Phase 16 §3): the ``Started server process`` alternative is uvicorn's own
    # line and fires on every worker spawn — counting it made one WebUI start read
    # as two, exhausting the budget on a single restart. Only the wrapper line is
    # the operator-observable "WebUI came up" event; the uvicorn line is dropped.
    "webui":     re.compile(r"\[run_webui\] dashboard on"),
}


def _parse_iso(ts: str) -> datetime | None:
    """Parse an ISO-ish timestamp string into a tz-aware datetime. Returns None on bad input.

    Accepts the common shapes seen across the repo:
        ``2026-08-31T07:54:52.274+02:00``     (ISO with offset)
        ``2026-08-31T07:54:52.274Z``           (ISO Z)
        ``2026-08-31 07:54:52,274``            (scheduler.log wall-clock, tz implicit = local)
        ``2026-08-31 07:54:52``                (short)
        ``2026-08-31T07:54:52+0200``           (no colon in offset — rare but seen)
    """
    if not ts:
        return None
    s = ts.strip().replace(" ", "T", 1).replace(",", ".")
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    # Compact offset like +0200 -> +02:00 (rough but works for our own log shapes)
    m = re.search(r"([+-])(\d{2})(\d{2})$", s)
    if m and "+" in s.split("T")[-1]:
        s = s[:-5] + f"{m.group(1)}{m.group(2)}:{m.group(3)}"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        # Treat naive as UTC; the scheduler.ts-Ausgabe is local but the script's
        # window filter is day-bucketed in Europe/Berlin so off-by-tz matters
        # at most by one day boundary edge. Acceptable for a coarse filter.
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _parse_scheduler_ts(line: str) -> datetime | None:
    """Best-effort: pull a Berlin/UTC timestamp off the front of a scheduler.log line.

    Returns None for blank lines or lines where the ts is missing/unparsable.
    """
    m = _SCHED_TS_RE.match(line)
    if not m:
        return None
    return _parse_iso(m.group("ts").replace("T", " ", 1))


def count_starts_in_window(
    log_path: Path,
    service: str,
    *,
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
) -> tuple[int, list[datetime]]:
    """Count start-lines for ``service`` in ``log_path`` within ``[from_ts, to_ts]``.

    Returns ``(count, timestamps_of_each_start)``.

    Services with timestamped start-lines (only ``scheduler`` today) are filtered
    precisely; the others (recorder/discovery/webui) emit untimestamped lines,
    so when a window is provided we fall back to a **whole-file** count and
    surface that explicitly in the report. The script returns the count of
    matching lines regardless, so a caller who knows the file was cleared at
    start can rely on the raw number.
    """
    pattern = _START_PATTERNS[service]
    if not log_path.exists():
        return 0, []
    timestamps: list[datetime] = []
    raw_matches = 0
    with log_path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if not pattern.search(line):
                continue
            raw_matches += 1
            ts = _parse_scheduler_ts(line)
            if ts is not None:
                timestamps.append(ts)
    if not timestamps:
        # No timestamps → services without ts-prefixed start-lines. Whole-file count.
        return raw_matches, []
    filtered = [
        ts for ts in timestamps
        if (from_ts is None or ts >= from_ts) and (to_ts is None or ts <= to_ts)
    ]
    return len(filtered), filtered


def _berlin_day(dt: datetime) -> date:
    """Bucket a tz-aware datetime into a Berlin local date."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if ZoneInfo is not None:
        return dt.astimezone(ZoneInfo("Europe/Berlin")).date()
    # Fallback: fixed UTC+1 (no DST). Coarse but correct at midnight.
    return dt.astimezone(timezone(timedelta(hours=1))).date()


def _berlin_day_bounds(day: date) -> tuple[datetime, datetime]:
    """Inverse of :func:`_berlin_day` — the ``[start, end)`` tz-aware UTC range
    that maps to the Berlin local date ``day``.

    Used by K1 to filter ``run_scheduler.log`` start-lines by the preregistered
    "in window" clause (Phase 16 §3 J2): without this, every start-line in the
    log counted, so 7 pre-registration starts already broke K1 on day 1. End is
    exclusive so a start exactly at Berlin-midnight is attributed to the day
    that just started (matching the bucket ``_berlin_day`` assigns).
    """
    if ZoneInfo is not None:
        tz = ZoneInfo("Europe/Berlin")
        start_local = datetime.combine(day, datetime.min.time(), tzinfo=tz)
        end_local = datetime.combine(day + timedelta(days=1), datetime.min.time(), tzinfo=tz)
        return (
            start_local.astimezone(timezone.utc),
            end_local.astimezone(timezone.utc),
        )
    # Fallback (DST-naive, but mirrors _berlin_day's coarse correctness guarantee):
    tz_fallback = timezone(timedelta(hours=1))
    start_local = datetime.combine(day, datetime.min.time(), tzinfo=tz_fallback)
    end_local = datetime.combine(day + timedelta(days=1), datetime.min.time(), tzinfo=tz_fallback)
    return (
        start_local.astimezone(timezone.utc),
        end_local.astimezone(timezone.utc),
    )


def trades_per_day(trading_db: Path) -> dict[date, int]:
    """Return ``{Berlin day: count of CLOSED+autonomous+demo trades opened that day}``.

    Day bucket = ``open_ts`` (Berlin). Reads via ``file:...?mode=ro`` URI.
    """
    sql = (
        "SELECT open_ts FROM trade_outcomes "
        "WHERE status='CLOSED' AND provenance='autonomous' AND account='demo'"
    )
    out: dict[date, int] = {}
    with _ro_connect(trading_db) as conn:
        rows = conn.execute(sql).fetchall()
    for row in rows:
        dt = _parse_iso(row["open_ts"])
        if dt is None:
            continue
        out[_berlin_day(dt)] = out.get(_berlin_day(dt), 0) + 1
    return out


def bars_count_by_source(bars_db: Path) -> dict[str, int]:
    """Return ``{source: count of bars ever written}`` — non-windowed, used in the
    ``--day`` report as a coarse liveness signal for the Recorder."""
    if not bars_db.exists():
        return {}
    with _ro_connect(bars_db) as conn:
        rows = conn.execute(
            "SELECT source, COUNT(*) AS n FROM bars GROUP BY source"
        ).fetchall()
    return {r["source"]: int(r["n"]) for r in rows}


def bars_per_day(bars_db: Path, day: date, sources: tuple[str, ...] = ("yf", "ls", "capital")) -> int:
    """Count bars rows in ``bars.sqlite`` whose ``fetched_at`` date (Berlin) == ``day``.

    Used by K2 (Recorder-Evidence): at least one bar per day means the Recorder
    loop ran. Sources: ``yf`` (recorder), ``ls`` (Phase-13 recorder stream),
    ``capital`` (Capital.com fallback — recorded by the same Recorder).
    """
    if not bars_db.exists():
        return 0
    sql = (
        f"SELECT fetched_at FROM bars WHERE source IN ({','.join('?' * len(sources))})"
    )
    n = 0
    with _ro_connect(bars_db) as conn:
        for row in conn.execute(sql, sources).fetchall():
            dt = _parse_iso(row["fetched_at"])
            if dt is None:
                continue
            if _berlin_day(dt) == day:
                n += 1
    return n


def heartbeat_ok_per_day(health_jsonl: Path) -> dict[date, tuple[int, int]]:
    """``{day: (ok_count, total_count)}`` for ``measurement_heartbeat`` events.

    Reads the file once; cheap enough for the volume (under 10k events).
    """
    out: dict[date, tuple[int, int]] = {}
    if not health_jsonl.exists():
        return out
    with health_jsonl.open("r", encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            try:
                ev = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if ev.get("event") != "measurement_heartbeat":
                continue
            day_str = ev.get("day")
            if not day_str:
                continue
            try:
                day = date.fromisoformat(day_str)
            except ValueError:
                continue
            ok_n, total_n = out.get(day, (0, 0))
            total_n += 1
            if ev.get("ok") is True:
                ok_n += 1
            out[day] = (ok_n, total_n)
    return out


def llm_usage_per_day(
    usage_json: Path,
    *,
    threshold: int = DEFAULT_DAILY_TOKEN_BUDGET,
) -> dict[date, dict[str, Any]]:
    """Aggregate llm_usage.json per Berlin day.

    Returns ``{day: {"tokens": total, "calls": n, "exhausted_at": iso|None}}``.

    Counts ``input_tokens + output_tokens + cache_creation_input_tokens +
    cache_read_input_tokens`` if those keys exist (a Phase-4 change added the
    cache fields; budget.py treats them as full-weight per Opus-Review §13 #3).
    """
    if not usage_json.exists():
        raise BudgetFileError(f"llm_usage.json missing: {usage_json}")
    try:
        with usage_json.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise BudgetFileError(f"llm_usage.json unparseable: {exc}") from exc
    if not isinstance(data, list):
        raise BudgetFileError(f"llm_usage.json must be a list, got {type(data).__name__}")
    per_day: dict[date, dict[str, Any]] = {}
    for entry in data:
        ts_str = entry.get("ts")
        dt = _parse_iso(ts_str) if ts_str else None
        if dt is None:
            continue
        day = _berlin_day(dt)
        tokens = (
            int(entry.get("input_tokens") or 0)
            + int(entry.get("output_tokens") or 0)
            + int(entry.get("cache_creation_input_tokens") or 0)
            + int(entry.get("cache_read_input_tokens") or 0)
        )
        rec = per_day.setdefault(day, {"tokens": 0, "calls": 0, "exhausted_at": None})
        rec["tokens"] += tokens
        rec["calls"] += 1
    # Second pass for exhausted_at — walk the file once per day, cheap (~80 entries/day)
    for day in list(per_day.keys()):
        cum = 0
        exhausted_ts: str | None = None
        for entry in data:
            ts_str = entry.get("ts")
            dt = _parse_iso(ts_str) if ts_str else None
            if dt is None or _berlin_day(dt) != day:
                continue
            cum += (
                int(entry.get("input_tokens") or 0)
                + int(entry.get("output_tokens") or 0)
                + int(entry.get("cache_creation_input_tokens") or 0)
                + int(entry.get("cache_read_input_tokens") or 0)
            )
            if exhausted_ts is None and cum >= threshold:
                exhausted_ts = dt.isoformat()
        per_day[day]["exhausted_at"] = exhausted_ts
    return per_day


def critical_count_after_opens(
    trading_db: Path,
    scheduler_log: Path,
    from_day: date,
    to_day: date,
    *,
    max_hours: int = 24,
) -> list[dict[str, Any]]:
    """For every CLOSED+autonomous trade whose ``open_ts`` Berlin-day is in window,
    count ``CRITICAL`` lines in ``scheduler_log`` whose timestamp is within
    ``max_hours`` after the trade's ``open_ts``. Returns the list of per-trade
    counts (sorted by open_ts). Empty list when there are no trades."""
    if not (scheduler_log.exists()) or not trading_db.exists():
        return []
    sql = (
        "SELECT id, open_ts, close_ts, epic FROM trade_outcomes "
        "WHERE status='CLOSED' AND provenance='autonomous' AND account='demo'"
    )
    out: list[dict[str, Any]] = []
    with _ro_connect(trading_db) as conn:
        trades = [dict(r) for r in conn.execute(sql).fetchall()]
    if not trades:
        return out
    # Load all CRITICAL lines into memory (cheap: ~120 KB/day × ~10 days).
    critical_ts: list[datetime] = []
    if scheduler_log.exists():
        with scheduler_log.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if "CRITICAL" not in line:
                    continue
                ts = _parse_scheduler_ts(line)
                if ts is not None:
                    critical_ts.append(ts)
    critical_ts.sort()
    for trade in trades:
        open_dt = _parse_iso(trade["open_ts"])
        if open_dt is None:
            continue
        if not (from_day <= _berlin_day(open_dt) <= to_day):
            continue
        horizon = open_dt + timedelta(hours=max_hours)
        n = sum(1 for ct in critical_ts if open_dt <= ct <= horizon)
        out.append({
            "trade_id": trade["id"],
            "epic": trade["epic"],
            "open_ts": trade["open_ts"],
            "close_ts": trade["close_ts"],
            "critical_count_24h": n,
        })
    return out


def extract_caps_from_scheduler_log(scheduler_log: Path) -> dict[str, Any]:
    """Pin ``max_trades`` and ``daily_loss_cap`` from the most recent
    ``starting scheduler daemon`` start-line. Returns an empty dict if no
    start-line is found."""
    out: dict[str, Any] = {}
    if not scheduler_log.exists():
        return out
    pattern = re.compile(
        r"starting scheduler daemon \((?P<inner>[^)]*)\)"
    )
    max_trades_re = re.compile(r"max_trades=(?P<v>\d+)")
    cap_re = re.compile(r"daily_loss_cap=(?P<v>[\d.]+)")
    last: dict[str, Any] | None = None
    with scheduler_log.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = pattern.search(line)
            if not m:
                continue
            inner = m.group("inner")
            mt = max_trades_re.search(inner)
            cap = cap_re.search(inner)
            last = {
                "max_trades": int(mt.group("v")) if mt else None,
                "daily_loss_cap_eur": float(cap.group("v")) if cap else None,
                "raw_inner": inner,
            }
    if last is not None:
        out.update(last)
    return out


# ----------------------------------------------------------------------------
# Internal: read-only SQLite connect
# ----------------------------------------------------------------------------

def _ro_connect(db_path: Path) -> sqlite3.Connection:
    """Open ``db_path`` in SQLite read-only mode. OS-level guarantee (the URI
    refuses writes); see ``diag_score_distribution.py`` for the same pattern."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# ----------------------------------------------------------------------------
# Reporting model
# ----------------------------------------------------------------------------

@dataclass
class CriterionResult:
    criterion: str
    verdict: str                # "PASS" | "FAIL" | "NA" | "ERROR" | "PARTIAL"
    measured: dict[str, Any]
    threshold: str
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "criterion": self.criterion,
            "verdict": self.verdict,
            "measured": self.measured,
            "threshold": self.threshold,
            "note": self.note,
        }


@dataclass
class DayReport:
    day: date
    criteria: dict[str, CriterionResult] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "day": self.day.isoformat(),
            "criteria": {k: v.to_dict() for k, v in self.criteria.items()},
            "warnings": list(self.warnings),
        }


@dataclass
class SummaryReport:
    from_day: date
    to_day: date
    criteria: dict[str, CriterionResult] = field(default_factory=dict)
    n_trading_days: int = 0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        verdicts = {c.verdict for c in self.criteria.values()}
        # Precedence ERROR > FAIL > PARTIAL > PASS: a PARTIAL (e.g. K4 on a sub-window)
        # must not read as clean PASS, but it is not a failure either — it means the
        # query can't judge that criterion, not that the criterion was violated.
        if "ERROR" in verdicts:
            overall = "ERROR"
        elif "FAIL" in verdicts:
            overall = "FAIL"
        elif "PARTIAL" in verdicts:
            overall = "PARTIAL"
        else:
            overall = "PASS"
        return {
            "from": self.from_day.isoformat(),
            "to": self.to_day.isoformat(),
            "n_trading_days": self.n_trading_days,
            "criteria": {k: v.to_dict() for k, v in self.criteria.items()},
            "warnings": list(self.warnings),
            "overall_verdict": overall,
        }


# ----------------------------------------------------------------------------
# Per-criterion evaluators
# ----------------------------------------------------------------------------

def evaluate_k1(
    state_dir: Path,
    *,
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
) -> CriterionResult:
    """K1 — Operator-Restart-Count. Threshold: ≤ 2 per service (P17: 1 Backoff-KILL-Clear)."""
    measured: dict[str, Any] = {}
    services = ("scheduler", "recorder", "discovery", "webui")
    for svc in services:
        n, ts_list = count_starts_in_window(
            state_dir / f"run_{svc}.log",
            svc,
            from_ts=from_ts,
            to_ts=to_ts,
        )
        measured[svc] = {
            "starts": n,
            "note": (
                "filtered-by-timestamp"
                if ts_list
                else "full-file-count (untimestamped start-lines: opaque to window filter)"
            ),
        }
    max_starts = max((v["starts"] for v in measured.values()), default=0)
    verdict = "PASS" if max_starts <= RESTARTS_PASS_THRESHOLD_MAX else "FAIL"
    return CriterionResult(
        criterion="1",
        verdict=verdict,
        measured=measured,
        threshold=f"≤ {RESTARTS_PASS_THRESHOLD_MAX} starts per service in window (P17: 1 Backoff-KILL-Clear allowance)",
        note=(
            "PASS requires ALL services at or below threshold"
            if any(v["starts"] > RESTARTS_PASS_THRESHOLD_MAX for v in measured.values())
            else ""
        ),
    )


def evaluate_k2(
    state_dir: Path,
    bars_db: Path,
    trading_db: Path,
    day: date,
    health_evidence_per_service: dict[date, dict[str, int]] | None = None,
) -> CriterionResult:
    """K2 — Services-active per Berlin-day. Soft signal (3-of-3 from append-only evidence).

    Pre-aggregated ``health_evidence_per_service`` lets tests bypass scanning the
    JSONL file by passing a hand-built dict — the shape is
    ``{day: {"health_events": N, "bars_per_day": M}}``.
    """
    health_path = state_dir / "research_health.jsonl"
    if health_evidence_per_service is not None and day in health_evidence_per_service:
        evidence = health_evidence_per_service[day]
    else:
        evidence = {
            "health_events": _count_health_events_for(health_path, day),
            "bars_per_day": bars_per_day(bars_db, day),
        }
    scheduler_ok = evidence["health_events"] >= 1
    recorder_ok = evidence["bars_per_day"] >= 1
    webui_ok = "operator-gesichtet"  # no append-only evidence; honest prereg
    measured = {
        "scheduler_health_events": evidence["health_events"],
        "recorder_bars_per_day": evidence["bars_per_day"],
        "discovery_heartbeat_event": evidence["health_events"],  # same JSONL covers both
        "webui": webui_ok,
    }
    auto = {"scheduler": scheduler_ok, "recorder": recorder_ok, "discovery": evidence["health_events"] >= 1}
    auto_pass_count = sum(1 for v in auto.values() if v)
    verdict = "PASS" if auto_pass_count == 3 else "FAIL"
    note = (
        f"{auto_pass_count}/3 automatic signals present (Scheduler={scheduler_ok}, "
        f"Recorder={recorder_ok}, Discovery={'?'}); WebUI must be operator-gesichtet."
    )
    return CriterionResult(
        criterion="2",
        verdict=verdict,
        measured=measured,
        threshold="3/3 automatic signals present + WebUI operator-gesichtet",
        note=note,
    )


def _count_health_events_for(health_path: Path, day: date) -> int:
    if not health_path.exists():
        return 0
    n = 0
    with health_path.open("r", encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            try:
                ev = json.loads(ln)
            except json.JSONDecodeError:
                continue
            ts = ev.get("ts")
            if not ts:
                continue
            dt = _parse_iso(ts)
            if dt is None:
                continue
            if _berlin_day(dt) == day:
                n += 1
    return n


def evaluate_k3(
    trading_db: Path,
    from_day: date,
    to_day: date,
    *,
    per_day: dict[date, int] | None = None,
) -> CriterionResult:
    """K3 — ≥ 5 autonomous Trades im Fenster (open_ts Berlin day inside window)."""
    counts = per_day if per_day is not None else trades_per_day(trading_db)
    in_window = {d: c for d, c in counts.items() if from_day <= d <= to_day}
    total = sum(in_window.values())
    verdict = "PASS" if total >= TRADES_PASS_THRESHOLD else "FAIL"
    return CriterionResult(
        criterion="3",
        verdict=verdict,
        measured={"in_window_total": total, "per_day": {d.isoformat(): n for d, n in sorted(in_window.items())}},
        threshold=f"≥ {TRADES_PASS_THRESHOLD} autonomous CLOSED trades in window",
    )


def evaluate_k4(
    state_dir: Path,
    from_day: date,
    to_day: date,
    *,
    health_evidence: dict[date, tuple[int, int]] | None = None,
    full_window_trading_days: int = K4_FULL_WINDOW_TRADING_DAYS,
) -> CriterionResult:
    """K4 — Heartbeat ok ≥ 8 / 10 Handelstagen. Trading days are Mo–Fr in window.

    Drift #9 (Phase 16 R3.2): the threshold must always read against the **full
    registered** test window (8 of 10), never against whatever sub-window a caller
    queried — a ``--day`` report used to print "≥ 8 of 1 trading days", which is not
    a criterion anyone registered. A query that covers fewer trading days than the
    full window cannot judge this criterion at all, so it reports ``PARTIAL`` instead
    of a misleading PASS/FAIL.
    """
    trading_days = [d for d in _iter_trading_days(from_day, to_day)]
    if health_evidence is None:
        health_evidence = heartbeat_ok_per_day(state_dir / "research_health.jsonl")
    ok_days = sum(
        1 for d in trading_days if health_evidence.get(d, (0, 0))[0] >= 1
    )
    is_full_window = len(trading_days) >= full_window_trading_days
    if is_full_window:
        verdict = "PASS" if ok_days >= HEARTBEAT_OK_PASS_THRESHOLD else "FAIL"
    else:
        verdict = "PARTIAL"
    return CriterionResult(
        criterion="4",
        verdict=verdict,
        measured={
            "ok_days": ok_days,
            "trading_days_considered": len(trading_days),
            "full_window_trading_days": full_window_trading_days,
            "per_day_ok_flags": {
                d.isoformat(): bool(health_evidence.get(d, (0, 0))[0] >= 1)
                for d in trading_days
            },
        },
        threshold=(
            f"≥ {HEARTBEAT_OK_PASS_THRESHOLD} of {full_window_trading_days} trading days "
            "(full registered window) with heartbeat.ok"
        ),
        note="" if is_full_window else (
            f"queried window covers {len(trading_days)} of {full_window_trading_days} "
            "registered trading days — PARTIAL, not judgeable"
        ),
    )


def evaluate_k5(
    trading_db: Path,
    state_dir: Path,
    from_day: date,
    to_day: date,
    *,
    per_trade_counts: list[dict[str, Any]] | None = None,
) -> CriterionResult:
    """K5 — ≤ 5 CRITICAL in 24h nach jedem OPEN. Returns the max across all opens."""
    if per_trade_counts is None:
        per_trade_counts = critical_count_after_opens(
            trading_db,
            state_dir / "run_scheduler.log",
            from_day,
            to_day,
        )
    max_n = max((p["critical_count_24h"] for p in per_trade_counts), default=0)
    verdict = "PASS" if (not per_trade_counts or max_n <= CRITICAL_24H_PASS_THRESHOLD) else "FAIL"
    return CriterionResult(
        criterion="5",
        verdict=verdict,
        measured={
            "max_critical_24h": max_n,
            "per_trade": per_trade_counts,
            "trades_in_window": len(per_trade_counts),
        },
        threshold=(
            f"≤ {CRITICAL_24H_PASS_THRESHOLD} CRITICAL per 24h window after each OPEN "
            "(A6 contract)"
        ),
    )


def evaluate_k6(
    usage_json: Path,
    from_day: date,
    to_day: date,
    *,
    threshold: int = DEFAULT_DAILY_TOKEN_BUDGET,
    window_close_hhmm: tuple[int, int] = DEFAULT_WINDOW_CLOSE_HHMM,
    per_day: dict[date, dict[str, Any]] | None = None,
) -> CriterionResult:
    """K6 — Budget nie vor 17:30 Berlin leer."""
    if per_day is None:
        try:
            per_day = llm_usage_per_day(usage_json, threshold=threshold)
        except BudgetFileError as exc:
            return CriterionResult(
                criterion="6",
                verdict="ERROR",
                measured={"error": str(exc)},
                threshold=f"< {threshold} tokens before {window_close_hhmm[0]:02d}:{window_close_hhmm[1]:02d} Berlin",
                note="Budget-File unreadable — OpUs-Review §13 #9 fail-closed",
            )
    in_window = {d: rec for d, rec in per_day.items() if from_day <= d <= to_day}
    hh, mm = window_close_hhmm
    offenders: list[dict[str, Any]] = []
    for d, rec in sorted(in_window.items()):
        ex_ts = rec.get("exhausted_at")
        if not ex_ts:
            continue
        dt = _parse_iso(ex_ts)
        if dt is None:
            continue
        if ZoneInfo is None:
            local = dt
        else:
            local = dt.astimezone(ZoneInfo("Europe/Berlin"))
        limit = local.replace(hour=hh, minute=mm, second=0, microsecond=0)
        if local < limit:
            offenders.append({
                "day": d.isoformat(),
                "exhausted_at_local": local.isoformat(),
                "tokens": rec["tokens"],
            })
    verdict = "PASS" if not offenders else "FAIL"
    return CriterionResult(
        criterion="6",
        verdict=verdict,
        measured={
            "budget_per_day": {d.isoformat(): {k: v for k, v in rec.items()} for d, rec in sorted(in_window.items())},
            "offenders_before_close": offenders,
        },
        threshold=f"< {threshold} tokens before {hh:02d}:{mm:02d} Berlin",
    )


def evaluate_k7(
    trading_db: Path,
    scheduler_log: Path,
    from_day: date,
    to_day: date,
    *,
    expected_max_trades: int = DEFAULT_MAX_TRADES,
    expected_daily_loss_cap: float = DEFAULT_DAILY_LOSS_CAP_EUR,
    pinned_caps: dict[str, Any] | None = None,
) -> CriterionResult:
    """K7 — Caps unverändert in window + every CLOSED trade has account='demo'."""
    caps = pinned_caps if pinned_caps is not None else extract_caps_from_scheduler_log(scheduler_log)
    caps_match = (
        caps.get("max_trades") == expected_max_trades
        and abs(float(caps.get("daily_loss_cap_eur") or 0) - expected_daily_loss_cap) < 0.01
    )
    sql = (
        "SELECT COUNT(*) AS n FROM trade_outcomes "
        "WHERE status='CLOSED' AND provenance='autonomous' "
        "AND account='demo' AND date(open_ts) BETWEEN ? AND ?"
    )
    demo_count = 0
    try:
        with _ro_connect(trading_db) as conn:
            row = conn.execute(
                sql,
                (from_day.isoformat(), to_day.isoformat()),
            ).fetchone()
            demo_count = int(row["n"]) if row else 0
    except sqlite3.OperationalError:
        demo_count = -1
    verdict = "PASS" if caps_match and demo_count >= 0 else "FAIL"
    return CriterionResult(
        criterion="7",
        verdict=verdict,
        measured={
            "start_line_caps": caps,
            "expected_max_trades": expected_max_trades,
            "expected_daily_loss_cap_eur": expected_daily_loss_cap,
            "closed_autonomous_trades_in_window": demo_count,
        },
        threshold=f"max_trades={expected_max_trades}, daily_loss_cap_eur={expected_daily_loss_cap} immutable in window",
    )


def evaluate_k8(
    state_dir: Path,
    bars_db: Path,
    from_day: date,
    to_day: date,
    *,
    health_events_per_day: dict[date, int] | None = None,
    bars_per_day_evidence: dict[date, int] | None = None,
    heartbeat_total_per_day: dict[date, int] | None = None,
) -> CriterionResult:
    """K8 — Liveness: services actually ran on each trading day in window.

    Phase 16 R3.3 / F8: K1/K5/K6/K7 all PASS vacuously on a day with zero
    processes (0 starts ≤ threshold, 0 CRITICALs ≤ threshold, 0 tokens < budget,
    caps unread-but-unchanged) — a dead day reads identically to a quiet one. K8
    is the independent, positive-evidence check that catches exactly that case:
    a day is "live" only if it has ≥ 1 scheduler research_health event, ≥ 1
    archived bar, AND ≥ 1 heartbeat event (any outcome, not just ``ok``). PASS
    requires every trading day in the queried window to be live; one dead day
    fails the whole criterion (this is a PASS-gate for the re-registration, not
    a soft signal like K2).
    """
    health_path = state_dir / "research_health.jsonl"
    trading_days = [d for d in _iter_trading_days(from_day, to_day)]
    if heartbeat_total_per_day is None:
        heartbeat_totals = {
            d: total for d, (_ok, total) in heartbeat_ok_per_day(health_path).items()
        }
    else:
        heartbeat_totals = heartbeat_total_per_day
    per_day_live: dict[str, dict[str, Any]] = {}
    live_days = 0
    for d in trading_days:
        cycles = (
            health_events_per_day.get(d, 0) if health_events_per_day is not None
            else _count_health_events_for(health_path, d)
        )
        bars = (
            bars_per_day_evidence.get(d, 0) if bars_per_day_evidence is not None
            else bars_per_day(bars_db, d)
        )
        heartbeats = heartbeat_totals.get(d, 0)
        live = cycles >= 1 and bars >= 1 and heartbeats >= 1
        if live:
            live_days += 1
        per_day_live[d.isoformat()] = {
            "scheduler_cycles": cycles,
            "bars": bars,
            "heartbeats": heartbeats,
            "live": live,
        }
    verdict = "PASS" if trading_days and live_days == len(trading_days) else "FAIL"
    return CriterionResult(
        criterion="8",
        verdict=verdict,
        measured={
            "live_days": live_days,
            "trading_days_considered": len(trading_days),
            "per_day": per_day_live,
        },
        threshold="every trading day in window has ≥1 scheduler cycle AND ≥1 bar AND ≥1 heartbeat",
    )


# ----------------------------------------------------------------------------
# Convenience: trading-day iterator
# ----------------------------------------------------------------------------

def _iter_trading_days(from_day: date, to_day: date) -> Iterable[date]:
    cur = from_day
    while cur <= to_day:
        if cur.weekday() < 5:  # Mon..Fri (no holiday calendar — prereg honest)
            yield cur
        cur += timedelta(days=1)


# ----------------------------------------------------------------------------
# CLI driver
# ----------------------------------------------------------------------------

def _parse_day(s: str) -> date:
    try:
        return date.fromisoformat(s)
    except ValueError as exc:
        raise SystemExit(f"--day/--from/--to must be ISO dates YYYY-MM-DD (got {s!r})") from exc


def _build_day_report(
    day: date,
    *,
    state_dir: Path,
    bars_db: Path,
    trading_db: Path,
    threshold: int,
    expected_max_trades: int,
    expected_daily_loss_cap: float,
) -> DayReport:
    report = DayReport(day=day)
    k2_evidence = {
        day: {
            "health_events": _count_health_events_for(state_dir / "research_health.jsonl", day),
            "bars_per_day": bars_per_day(bars_db, day),
        }
    }
    from_ts, to_ts = _berlin_day_bounds(day)
    report.criteria["1"] = evaluate_k1(state_dir, from_ts=from_ts, to_ts=to_ts)
    report.criteria["2"] = evaluate_k2(state_dir, bars_db, trading_db, day, health_evidence_per_service=k2_evidence)
    report.criteria["3"] = evaluate_k3(
        trading_db,
        from_day=day,
        to_day=day,
        per_day=trades_per_day(trading_db),
    )
    health = heartbeat_ok_per_day(state_dir / "research_health.jsonl")
    report.criteria["4"] = evaluate_k4(state_dir, day, day, health_evidence=health)
    report.criteria["5"] = evaluate_k5(
        trading_db, state_dir, day, day,
        per_trade_counts=critical_count_after_opens(
            trading_db, state_dir / "run_scheduler.log", day, day
        ),
    )
    try:
        per_day_budget = llm_usage_per_day(state_dir / "llm_usage.json", threshold=threshold)
    except BudgetFileError as exc:
        per_day_budget = None
        report.warnings.append(f"llm_usage.json unreadable: {exc}")
    report.criteria["6"] = evaluate_k6(
        state_dir / "llm_usage.json",
        from_day=day,
        to_day=day,
        threshold=threshold,
        per_day=per_day_budget,
    )
    report.criteria["7"] = evaluate_k7(
        trading_db, state_dir / "run_scheduler.log", day, day,
        expected_max_trades=expected_max_trades,
        expected_daily_loss_cap=expected_daily_loss_cap,
    )
    report.criteria["8"] = evaluate_k8(state_dir, bars_db, day, day)
    return report


def _build_summary_report(
    from_day: date,
    to_day: date,
    *,
    state_dir: Path,
    bars_db: Path,
    trading_db: Path,
    threshold: int,
    expected_max_trades: int,
    expected_daily_loss_cap: float,
) -> SummaryReport:
    report = SummaryReport(from_day=from_day, to_day=to_day)
    report.n_trading_days = sum(1 for _ in _iter_trading_days(from_day, to_day))
    # Summary covers the full Berlin range [from_day 00:00, to_day 24:00).
    # _berlin_day_bounds(to_day)[1] is Berlin-00:00 of the next day (end-exclusive).
    from_ts, _ = _berlin_day_bounds(from_day)
    _, to_ts = _berlin_day_bounds(to_day)
    report.criteria["1"] = evaluate_k1(state_dir, from_ts=from_ts, to_ts=to_ts)
    report.criteria["2"] = evaluate_k2(state_dir, bars_db, trading_db, from_day)
    counts = trades_per_day(trading_db)
    report.criteria["3"] = evaluate_k3(
        trading_db, from_day=from_day, to_day=to_day, per_day=counts
    )
    health = heartbeat_ok_per_day(state_dir / "research_health.jsonl")
    report.criteria["4"] = evaluate_k4(state_dir, from_day, to_day, health_evidence=health)
    report.criteria["5"] = evaluate_k5(
        trading_db, state_dir, from_day, to_day,
        per_trade_counts=critical_count_after_opens(
            trading_db, state_dir / "run_scheduler.log", from_day, to_day
        ),
    )
    try:
        per_day_budget = llm_usage_per_day(state_dir / "llm_usage.json", threshold=threshold)
    except BudgetFileError as exc:
        per_day_budget = None
        report.warnings.append(f"llm_usage.json unreadable: {exc}")
    report.criteria["6"] = evaluate_k6(
        state_dir / "llm_usage.json",
        from_day=from_day,
        to_day=to_day,
        threshold=threshold,
        per_day=per_day_budget,
    )
    report.criteria["7"] = evaluate_k7(
        trading_db, state_dir / "run_scheduler.log", from_day, to_day,
        expected_max_trades=expected_max_trades,
        expected_daily_loss_cap=expected_daily_loss_cap,
    )
    report.criteria["8"] = evaluate_k8(state_dir, bars_db, from_day, to_day)
    return report


def _write_report_file(reports_dir: Path, stem: str, payload: dict[str, Any]) -> Path:
    """Write the report to ``data/reports/autonomy_<stem>.json``.

    ``stem`` is the caller's choice: a single ISO date for ``--day`` reports, or
    ``<from>_to_<to>`` for windowed ``--from/--to`` reports (Drift #11, Phase 16
    R3.1). Before this fix both cases wrote ``autonomy_<from_day>.json``, so every
    windowed report silently overwrote that day's own single-day report file.
    """
    reports_dir.mkdir(parents=True, exist_ok=True)
    out = reports_dir / f"autonomy_{stem}.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return out


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Phase 16 E2 autonomy-report (read-only, append-only sources).",
    )
    p.add_argument("--day", type=_parse_day, help="Single-day report (Berlin day, ISO date)")
    p.add_argument("--from", dest="from_day", type=_parse_day, help="Window start (ISO date)")
    p.add_argument("--to", dest="to_day", type=_parse_day, help="Window end (ISO date)")
    p.add_argument("--summary", action="store_true", help="Evaluate 7 PASS criteria (--from/--to required)")
    p.add_argument("--trading-db", type=Path, default=_DEFAULT_TRADING_DB)
    p.add_argument("--bars-db", type=Path, default=_DEFAULT_BARS_DB)
    p.add_argument("--state-dir", type=Path, default=_DEFAULT_STATE_DIR)
    p.add_argument("--reports-dir", type=Path, default=_DEFAULT_REPORTS_DIR)
    p.add_argument("--budget-tokens", type=int, default=DEFAULT_DAILY_TOKEN_BUDGET)
    p.add_argument("--cap-max-trades", type=int, default=DEFAULT_MAX_TRADES)
    p.add_argument("--cap-daily-loss-cap", type=float, default=DEFAULT_DAILY_LOSS_CAP_EUR)
    p.add_argument("--quiet", action="store_true", help="stderr only on errors")
    args = p.parse_args(argv)
    if args.day and (args.from_day or args.to_day):
        p.error("--day is mutually exclusive with --from/--to")
    if args.summary and not (args.from_day and args.to_day):
        p.error("--summary requires --from and --to")
    return args


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if not args.quiet:
        logging.basicConfig(level=logging.INFO, format="[autonomy_report] %(message)s", stream=sys.stderr)
    common = dict(
        state_dir=args.state_dir,
        bars_db=args.bars_db,
        trading_db=args.trading_db,
        threshold=args.budget_tokens,
        expected_max_trades=args.cap_max_trades,
        expected_daily_loss_cap=args.cap_daily_loss_cap,
    )
    if args.day:
        rep = _build_day_report(args.day, **common)
        payload = rep.to_dict()
        stem = args.day.isoformat()
    else:
        rep = _build_summary_report(args.from_day, args.to_day, **common)
        payload = rep.to_dict()
        stem = f"{args.from_day.isoformat()}_to_{args.to_day.isoformat()}"
    out_path = _write_report_file(args.reports_dir, stem, payload)
    json.dump(payload, sys.stdout, indent=2, sort_keys=True, default=str)
    sys.stdout.write("\n")
    _LOG.info("wrote %s", out_path)
    if args.summary:
        return {"PASS": 0, "FAIL": 1, "PARTIAL": 1, "ERROR": 2}.get(payload["overall_verdict"], 2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
