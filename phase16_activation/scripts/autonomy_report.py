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

Phase 17 E-1 (Prereg v5) adds three criteria and tightens three. The default
preregistration stays ``v4`` — the v4 verdicts are byte-compatible; everything
below is reachable only via ``--prereg v5``:

  K2-v5  Dienste-pro-Handelstag-aktiv — **every** trading day needs scheduler
        health, recorder bars AND a Discovery cycle. The v4 Discovery signal was
        a proxy (it counted the scheduler's own JSONL events); v5 reads the
        Discovery daemon's append-only cycle line (Phase-17 B-10).
  K5-v5  same rule as v4, but ``measured.per_trade[]`` additionally carries
        ``by_logger`` (CRITICAL count per logger) and ``deal_related`` (the A6
        source definition — the CRITICALs that name that trade's deal_id).
  K6-v5  like v4, but the models in ``budget_exempt_models`` (Abo/M plan, T7) are
        measured, not capped: they land in ``exempt_tokens`` / ``exempt_calls``
        and are skipped in the ``exhausted_at`` sum — the same exemption the
        budget gate applies (Phase-17 D-1), so report and budget agree.
  K7-v5  caps like v4 AND every ``starting scheduler daemon`` line inside the
        window carries ``llm_profile=<expected>`` (the Phase-17 C-4 start line).
  K9     operator restart jobs per Berlin day ≤ 10 (journal export; NA without
        a journal file).
  K10    instinct-bridge health: 0 CRITICAL ``instinct.bridge`` lines, 0
        ``extractor returned ok=False`` lines, and every instinct created in the
        window carries evidence trade ids (NA without a CLOSE in the window).
  K11    every trading day has ≥ 1 divergence event (``divergence_ok`` or
        ``quote_divergence``) in ``research_health.jsonl``.

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
import dataclasses
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
# Phase 17 E-1 (K9): operator/auto restart jobs per Berlin day (journal export).
RESTART_JOBS_PER_DAY_MAX = 10
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

# Phase 17 E-1: the scheduler start-line carries the LLM routing profile
# (``phase8_scheduler/scheduler/run.py:206`` — "starting scheduler daemon
# (account=…, max_trades=…, daily_loss_cap=…, cycle=…min, llm_profile=…)").
_START_LINE_RE = re.compile(r"starting scheduler daemon \((?P<inner>[^)]*)\)")
_MAX_TRADES_RE = re.compile(r"max_trades=(?P<v>\d+)")
_DAILY_LOSS_CAP_RE = re.compile(r"daily_loss_cap=(?P<v>[\d.]+)")
_LLM_PROFILE_RE = re.compile(r"llm_profile=(?P<v>[^,)\s]+)")

# Phase 17 E-1: the logger name inside a CRITICAL line. The scheduler's log format
# is ``%(asctime)s %(levelname)s %(name)s: %(message)s`` → "CRITICAL instinct.bridge: …".
# A message that merely *contains* the word CRITICAL ("CRITICAL: heartbeat not ok")
# does not match — the regex requires a space + a name + a colon.
_CRITICAL_LOGGER_RE = re.compile(r"CRITICAL (?P<logger>\S+):")

# Phase 17 E-1 (B-10): the Discovery daemon's append-only cycle line —
# ``phase14_discovery/source_registry/run.py:211/225/272`` logs
# "discovery cycle %s: armed=…" with the UTC timestamp inside the text.
_DISCOVERY_CYCLE_RE = re.compile(r"discovery cycle (?P<ts>\d{4}-\d{2}-\d{2}T[\d:.]+Z):")

# Phase 17 E-1 (K9): the journal line of an operator/auto restart job. The exact
# live text is still unverified (Plan §9 #8) — the first real occurrence has to be
# checked against this pattern.
_RESTART_JOB_RE = re.compile(r"Scheduled restart job")
# journalctl -o short-iso → "2026-11-04T12:00:00+0100 host unit[pid]: message".
_JOURNAL_TS_RE = re.compile(
    r"^\s*(?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?)"
)

# Phase 17 E-1 (K10): the instinct-bridge failure texts
# (``phase15_v4/instinct/bridge.py:125/146/230/244``).
_BRIDGE_CRITICAL_RE = re.compile(r"CRITICAL instinct\.bridge")
_EXTRACTOR_NOT_OK_RE = re.compile(r"extractor returned ok=False")

# Phase 17 E-1 (K11): the divergence events — ``divergence_ok`` comes from the
# Phase-12 heartbeat sampler, ``quote_divergence`` from the Phase-8 observability
# module; both are written into ``research_health.jsonl`` with a ``ts``.
_DIVERGENCE_EVENTS = ("divergence_ok", "quote_divergence")


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
    exempt_models: tuple[str, ...] = (),
) -> dict[date, dict[str, Any]]:
    """Aggregate llm_usage.json per Berlin day.

    Returns ``{day: {"tokens": total, "calls": n, "exempt_tokens": total,
    "exempt_calls": n, "exhausted_at": iso|None}}``.

    Counts ``input_tokens + output_tokens + cache_creation_input_tokens +
    cache_read_input_tokens`` if those keys exist (a Phase-4 change added the
    cache fields; budget.py treats them as full-weight per Opus-Review §13 #3).

    Phase 17 E-1 (D-1-Fortsetzung): records whose ``model`` is in
    ``exempt_models`` do **not** count against the budget — they are the Abo/M
    plan (T7), "measured, not capped". They are summed separately into
    ``exempt_tokens`` / ``exempt_calls`` and are **skipped in the
    ``exhausted_at`` cumulative sum**, exactly like ``scheduler/budget.py``
    skips them (Phase-17 D-1). Without that skip the report would declare the
    budget exhausted while the budget gate still has headroom — the report and
    the gate must agree.

    ``exempt_models=()`` ⇒ v4 behaviour, verdict-identical (the two new keys are
    structurally always present, with value 0).
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
        rec = per_day.setdefault(
            day,
            {
                "tokens": 0,
                "calls": 0,
                "exempt_tokens": 0,
                "exempt_calls": 0,
                "exhausted_at": None,
            },
        )
        if entry.get("model") in exempt_models:
            rec["exempt_tokens"] += tokens
            rec["exempt_calls"] += 1
            continue
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
            if entry.get("model") in exempt_models:
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
    by_logger: bool = False,
) -> list[dict[str, Any]]:
    """For every CLOSED+autonomous trade whose ``open_ts`` Berlin-day is in window,
    count ``CRITICAL`` lines in ``scheduler_log`` whose timestamp is within
    ``max_hours`` after the trade's ``open_ts``. Returns the list of per-trade
    counts (sorted by open_ts). Empty list when there are no trades.

    Phase 17 E-1 (``by_logger=True``): each per-trade dict additionally carries
    ``by_logger`` (the CRITICAL count per logger name — the log format is
    ``%(asctime)s %(levelname)s %(name)s: %(message)s``) and ``deal_related``
    (the A6 source definition: the CRITICALs inside the window that name this
    trade's ``deal_id``). Both are **reported only** — the K5 verdict stays the
    v4 rule (all CRITICALs ≤ 5 per 24 h after each OPEN).

    ``by_logger=False`` (default) ⇒ the payload is byte-identical to v4.
    """
    if not (scheduler_log.exists()) or not trading_db.exists():
        return []
    sql = (
        "SELECT id, open_ts, close_ts, epic FROM trade_outcomes "
        "WHERE status='CLOSED' AND provenance='autonomous' AND account='demo'"
    )
    if by_logger:
        sql = (
            "SELECT id, open_ts, close_ts, epic, deal_id FROM trade_outcomes "
            "WHERE status='CLOSED' AND provenance='autonomous' AND account='demo'"
        )
    out: list[dict[str, Any]] = []
    with _ro_connect(trading_db) as conn:
        trades = [dict(r) for r in conn.execute(sql).fetchall()]
    if not trades:
        return out
    # Load all CRITICAL lines into memory (cheap: ~120 KB/day × ~10 days).
    critical_ts: list[datetime] = []
    critical_extra: list[tuple[datetime, str | None, str]] = []
    if scheduler_log.exists():
        with scheduler_log.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if "CRITICAL" not in line:
                    continue
                ts = _parse_scheduler_ts(line)
                if ts is not None:
                    critical_ts.append(ts)
                    if by_logger:
                        m = _CRITICAL_LOGGER_RE.search(line)
                        critical_extra.append((ts, m.group("logger") if m else None, line))
    critical_ts.sort()
    if by_logger:
        critical_extra.sort(key=lambda item: item[0])
    for trade in trades:
        open_dt = _parse_iso(trade["open_ts"])
        if open_dt is None:
            continue
        if not (from_day <= _berlin_day(open_dt) <= to_day):
            continue
        horizon = open_dt + timedelta(hours=max_hours)
        n = sum(1 for ct in critical_ts if open_dt <= ct <= horizon)
        entry: dict[str, Any] = {
            "trade_id": trade["id"],
            "epic": trade["epic"],
            "open_ts": trade["open_ts"],
            "close_ts": trade["close_ts"],
            "critical_count_24h": n,
        }
        if by_logger:
            deal_id = trade.get("deal_id")
            per_logger: dict[str, int] = {}
            deal_related = 0
            for ct, logger, line in critical_extra:
                if not (open_dt <= ct <= horizon):
                    continue
                key = logger or "unknown"
                per_logger[key] = per_logger.get(key, 0) + 1
                if deal_id and deal_id in line:
                    deal_related += 1
            entry["by_logger"] = per_logger
            entry["deal_related"] = deal_related
            entry["deal_id"] = deal_id
        out.append(entry)
    return out


def _parse_start_line_inner(inner: str) -> dict[str, Any]:
    """Parse the inner part of a ``starting scheduler daemon (...)`` line.

    Returns ``{"max_trades": int|None, "daily_loss_cap_eur": float|None,
    "llm_profile": str|None, "raw_inner": str}``. The three values are read
    independently — a line that carries only some of them still yields the
    others as ``None`` (the caps check then fails closed).
    """
    mt = _MAX_TRADES_RE.search(inner)
    cap = _DAILY_LOSS_CAP_RE.search(inner)
    prof = _LLM_PROFILE_RE.search(inner)
    return {
        "max_trades": int(mt.group("v")) if mt else None,
        "daily_loss_cap_eur": float(cap.group("v")) if cap else None,
        "llm_profile": prof.group("v") if prof else None,
        "raw_inner": inner,
    }


def extract_caps_from_scheduler_log(scheduler_log: Path) -> dict[str, Any]:
    """Pin ``max_trades`` and ``daily_loss_cap`` from the most recent
    ``starting scheduler daemon`` start-line. Returns an empty dict if no
    start-line is found."""
    out: dict[str, Any] = {}
    if not scheduler_log.exists():
        return out
    last: dict[str, Any] | None = None
    with scheduler_log.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = _START_LINE_RE.search(line)
            if not m:
                continue
            parsed = _parse_start_line_inner(m.group("inner"))
            last = {
                "max_trades": parsed["max_trades"],
                "daily_loss_cap_eur": parsed["daily_loss_cap_eur"],
                "raw_inner": parsed["raw_inner"],
            }
    if last is not None:
        out.update(last)
    return out


def start_lines_in_window(
    scheduler_log: Path,
    from_day: date,
    to_day: date,
) -> list[dict[str, Any]]:
    """Return every ``starting scheduler daemon`` line whose timestamp falls into
    the Berlin-day window ``[from_day, to_day]``.

    Each entry: ``{"ts": iso, "max_trades": int|None,
    "daily_loss_cap_eur": float|None, "llm_profile": str|None,
    "raw_inner": str}``. Lines without a parsable timestamp are skipped — they
    cannot be attributed to a day (the window filter needs a timestamp).
    """
    out: list[dict[str, Any]] = []
    if not scheduler_log.exists():
        return out
    with scheduler_log.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = _START_LINE_RE.search(line)
            if not m:
                continue
            ts = _parse_scheduler_ts(line)
            if ts is None:
                continue
            day = _berlin_day(ts)
            if not (from_day <= day <= to_day):
                continue
            parsed = _parse_start_line_inner(m.group("inner"))
            out.append({"ts": ts.isoformat(), **parsed})
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
# Phase 17 E-1 — Prereg v5 evaluators
# ----------------------------------------------------------------------------

def count_discovery_cycles_per_day(log: Path) -> dict[date, int]:
    """Return ``{Berlin day: number of Discovery cycles}``.

    The Discovery daemon writes one append-only line per cycle
    (``phase14_discovery/source_registry/run.py:211/225/272`` — Phase-17 B-10):
    ``discovery cycle 2026-11-04T12:34:56.789Z: armed=True stale=0 rows_written=0
    errors=0``. The UTC timestamp is *inside the text* (the daemon's basicConfig
    logs without asctime), so the regex reads it from there and buckets it into
    the Berlin day.

    A missing file yields ``{}`` — the daemon may simply not have run yet.
    """
    out: dict[date, int] = {}
    if not log.exists():
        return out
    with log.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = _DISCOVERY_CYCLE_RE.search(line)
            if not m:
                continue
            dt = _parse_iso(m.group("ts"))
            if dt is None:
                continue
            day = _berlin_day(dt)
            out[day] = out.get(day, 0) + 1
    return out


def evaluate_k2_v5(
    state_dir: Path,
    bars_db: Path,
    from_day: date,
    to_day: date,
    *,
    health_events_per_day: dict[date, int] | None = None,
    bars_per_day_evidence: dict[date, int] | None = None,
    discovery_cycles_per_day: dict[date, int] | None = None,
) -> CriterionResult:
    """K2-v5 — every trading day needs all three automatic service signals.

    v4's Discovery signal was a **proxy**: it counted the scheduler's own
    ``research_health.jsonl`` events, so a dead Discovery daemon still read as
    "Discovery present" (``autonomy_report.py:660`` in the v4 source). v5 reads
    the Discovery daemon's own append-only cycle line (Phase-17 B-10) — that is
    the evidence of the *Discovery* arm, not of the Scheduler arm.

    Rules per trading day (Mo–Fr in the window):
      * Scheduler — ≥ 1 ``research_health.jsonl`` event,
      * Recorder — ≥ 1 archived bar,
      * Discovery — ≥ 1 discovery cycle.

    PASS requires **every** trading day to have all three. A window without any
    trading day is ``NA`` (nothing to judge) — never a vacuous PASS.
    """
    health_path = state_dir / "research_health.jsonl"
    trading_days = list(_iter_trading_days(from_day, to_day))
    if not trading_days:
        return CriterionResult(
            criterion="2",
            verdict="NA",
            measured={"trading_days_considered": 0},
            threshold="every trading day has ≥1 scheduler event AND ≥1 bar AND ≥1 discovery cycle",
            note="window contains no trading day (Mo–Fr) — nothing to judge",
        )
    if discovery_cycles_per_day is None:
        discovery_cycles_per_day = count_discovery_cycles_per_day(
            state_dir / "run_discovery.log"
        )
    per_day: dict[str, dict[str, Any]] = {}
    live_days = 0
    for d in trading_days:
        events = (
            health_events_per_day.get(d, 0) if health_events_per_day is not None
            else _count_health_events_for(health_path, d)
        )
        bars = (
            bars_per_day_evidence.get(d, 0) if bars_per_day_evidence is not None
            else bars_per_day(bars_db, d)
        )
        cycles = discovery_cycles_per_day.get(d, 0)
        day_ok = events >= 1 and bars >= 1 and cycles >= 1
        if day_ok:
            live_days += 1
        per_day[d.isoformat()] = {
            "scheduler_health_events": events,
            "recorder_bars_per_day": bars,
            "discovery_cycles": cycles,
            "ok": day_ok,
        }
    verdict = "PASS" if live_days == len(trading_days) else "FAIL"
    return CriterionResult(
        criterion="2",
        verdict=verdict,
        measured={
            "live_days": live_days,
            "trading_days_considered": len(trading_days),
            "per_day": per_day,
            "webui": "operator-gesichtet",
        },
        threshold=(
            "every trading day has ≥1 scheduler event AND ≥1 bar AND ≥1 discovery cycle "
            "+ WebUI operator-gesichtet"
        ),
        note="" if verdict == "PASS" else (
            f"{live_days}/{len(trading_days)} trading days carry all three automatic signals"
        ),
    )


def evaluate_k6_v5(
    usage_json: Path,
    from_day: date,
    to_day: date,
    *,
    threshold: int = DEFAULT_DAILY_TOKEN_BUDGET,
    window_close_hhmm: tuple[int, int] = DEFAULT_WINDOW_CLOSE_HHMM,
    exempt_models: tuple[str, ...] = (),
    per_day: dict[date, dict[str, Any]] | None = None,
) -> CriterionResult:
    """K6-v5 — the budget of the **non-exempt** models is never empty before 17:30.

    Same rule as v4, but the models in ``exempt_models`` (the Abo/M plan, T7) are
    measured and reported (``exempt_tokens_per_day`` / ``exempt_calls_per_day``)
    without counting against the cap — exactly like ``scheduler/budget.py``
    (Phase-17 D-1). Those numbers are the measurement D-2 needs to decide the
    K6 unit.
    """
    if per_day is None:
        try:
            per_day = llm_usage_per_day(
                usage_json, threshold=threshold, exempt_models=exempt_models
            )
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
            "exempt_tokens_per_day": {
                d.isoformat(): int(rec.get("exempt_tokens", 0)) for d, rec in sorted(in_window.items())
            },
            "exempt_calls_per_day": {
                d.isoformat(): int(rec.get("exempt_calls", 0)) for d, rec in sorted(in_window.items())
            },
            "exempt_models": list(exempt_models),
        },
        threshold=f"< {threshold} tokens before {hh:02d}:{mm:02d} Berlin (exempt models uncapped)",
    )


def evaluate_k7_v5(
    trading_db: Path,
    scheduler_log: Path,
    from_day: date,
    to_day: date,
    *,
    expected_max_trades: int = DEFAULT_MAX_TRADES,
    expected_daily_loss_cap: float = DEFAULT_DAILY_LOSS_CAP_EUR,
    pinned_caps: dict[str, Any] | None = None,
    expected_llm_profile: str | None = None,
) -> CriterionResult:
    """K7-v5 — caps unchanged **and** the LLM routing profile pinned per start-line.

    Two independent requirements:

    1. The caps rule of v4 (the most recent start-line carries
       ``max_trades=5, daily_loss_cap=1800.0``) plus every CLOSED autonomous
       trade in the window is a demo trade.
    2. Every ``starting scheduler daemon`` line **inside the window** carries
       ``llm_profile=<expected_llm_profile>`` (Phase-17 C-4 wrote the profile
       into the start line). ``expected_llm_profile=None`` ⇒ requirement 2 is
       not checked (v4 rule only).

    Requirement 2 is **fail-closed**: with no start-line inside the window the
    profile cannot be confirmed ⇒ FAIL (not a vacuous PASS). That is the F8
    lesson — a criterion must not pass on a day without a single process.
    """
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
    lines = start_lines_in_window(scheduler_log, from_day, to_day)
    if expected_llm_profile is None:
        profile_ok = True
        profile_measured: dict[str, Any] = {
            "checked": False,
            "expected": None,
            "start_lines_in_window": len(lines),
        }
    else:
        observed = [ln["llm_profile"] for ln in lines]
        mismatched = [p for p in observed if p != expected_llm_profile]
        profile_ok = bool(lines) and not mismatched
        profile_measured = {
            "checked": True,
            "expected": expected_llm_profile,
            "start_lines_in_window": len(lines),
            "observed_profiles": sorted({p for p in observed if p is not None}),
            "mismatched_profiles": mismatched,
        }
    verdict = "PASS" if caps_match and demo_count >= 0 and profile_ok else "FAIL"
    note = ""
    if expected_llm_profile is not None and not lines:
        note = (
            "no 'starting scheduler daemon' line inside the window — the llm_profile "
            "pin cannot be confirmed (fail-closed)"
        )
    elif expected_llm_profile is not None and not profile_ok:
        note = f"llm_profile pin {expected_llm_profile!r} violated by a start-line in the window"
    return CriterionResult(
        criterion="7",
        verdict=verdict,
        measured={
            "start_line_caps": caps,
            "expected_max_trades": expected_max_trades,
            "expected_daily_loss_cap_eur": expected_daily_loss_cap,
            "closed_autonomous_trades_in_window": demo_count,
            "llm_profile": profile_measured,
        },
        threshold=(
            f"max_trades={expected_max_trades}, daily_loss_cap_eur={expected_daily_loss_cap} "
            "immutable in window"
            + (
                f" AND llm_profile={expected_llm_profile} on every start-line in window"
                if expected_llm_profile is not None else ""
            )
        ),
        note=note,
    )


def evaluate_k9(
    journal_file: Path | None,
    from_day: date,
    to_day: date,
    *,
    max_per_day: int = RESTART_JOBS_PER_DAY_MAX,
) -> CriterionResult:
    """K9 — operator restart jobs per Berlin day ≤ ``max_per_day``.

    Source: the journal export the operator produces in E-4
    (``journalctl -o short-iso``). A restart job is a line carrying
    ``Scheduled restart job``. Without a journal file the criterion is ``NA``
    (not measurable) — it never blocks a run that simply has no export.

    Fail-closed on unattributable lines: a restart-job line whose timestamp
    cannot be parsed cannot be assigned to a day, so the per-day bound cannot be
    proven ⇒ FAIL (with the count in ``measured``).
    """
    if journal_file is None:
        return CriterionResult(
            criterion="9",
            verdict="NA",
            measured={"journal_file": None},
            threshold=f"≤ {max_per_day} restart jobs per Berlin day",
            note="no journal file supplied (--journal-file) — not measurable",
        )
    if not journal_file.exists():
        return CriterionResult(
            criterion="9",
            verdict="NA",
            measured={"journal_file": str(journal_file), "exists": False},
            threshold=f"≤ {max_per_day} restart jobs per Berlin day",
            note="journal file not found — not measurable",
        )
    per_day: dict[date, int] = {}
    unattributed = 0
    total = 0
    with journal_file.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if not _RESTART_JOB_RE.search(line):
                continue
            total += 1
            m = _JOURNAL_TS_RE.match(line)
            dt = _parse_iso(m.group("ts")) if m else None
            if dt is None:
                unattributed += 1
                continue
            day = _berlin_day(dt)
            per_day[day] = per_day.get(day, 0) + 1
    in_window = {d: n for d, n in per_day.items() if from_day <= d <= to_day}
    offenders = {d.isoformat(): n for d, n in sorted(in_window.items()) if n > max_per_day}
    verdict = "FAIL" if (offenders or unattributed) else "PASS"
    note = ""
    if unattributed:
        note = (
            f"{unattributed} restart-job line(s) without a parsable timestamp — "
            "the per-day bound cannot be proven (fail-closed)"
        )
    return CriterionResult(
        criterion="9",
        verdict=verdict,
        measured={
            "journal_file": str(journal_file),
            "restart_jobs_total": total,
            "per_day": {d.isoformat(): n for d, n in sorted(in_window.items())},
            "offenders": offenders,
            "unattributed_lines": unattributed,
        },
        threshold=f"≤ {max_per_day} restart jobs per Berlin day",
        note=note,
    )


def evaluate_k10(
    trading_db: Path,
    scheduler_log: Path,
    from_day: date,
    to_day: date,
) -> CriterionResult:
    """K10 — the instinct bridge is healthy for the trades closed in the window.

    Three requirements (the bridge is the Phase-15 promotion path — a silent
    failure there means the bot learns nothing):

    1. No ``CRITICAL instinct.bridge`` line inside the window
       (``phase15_v4/instinct/bridge.py:125/164/230/244``).
    2. No ``extractor returned ok=False`` line inside the window
       (``bridge.py:146`` — an INFO line, matched by text).
    3. Every ``instincts`` row **created** inside the window carries
       ``evidence_trade_ids_json`` (an instinct without evidence is a
       hallucinated rule — the live DB shows 29 such legacy rows).

    No CLOSE in the window ⇒ ``NA`` (nothing to judge). The trade population is
    the report's standard one: CLOSED + autonomous + demo.
    """
    closes = 0
    if trading_db.exists():
        sql = (
            "SELECT COUNT(*) AS n FROM trade_outcomes "
            "WHERE status='CLOSED' AND provenance='autonomous' AND account='demo' "
            "AND date(close_ts) BETWEEN ? AND ?"
        )
        try:
            with _ro_connect(trading_db) as conn:
                row = conn.execute(sql, (from_day.isoformat(), to_day.isoformat())).fetchone()
                closes = int(row["n"]) if row else 0
        except sqlite3.OperationalError:
            closes = -1
    if closes <= 0:
        return CriterionResult(
            criterion="10",
            verdict="NA",
            measured={"closed_autonomous_trades_in_window": max(closes, 0)},
            threshold="0 CRITICAL instinct.bridge + 0 extractor ok=False + every new instinct has evidence",
            note="no CLOSE in the window — not measurable",
        )
    bridge_criticals = 0
    extractor_failures = 0
    if scheduler_log.exists():
        with scheduler_log.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                ts = _parse_scheduler_ts(line)
                if ts is None:
                    continue
                # The scheduler log carries local wall-clock timestamps; the report
                # buckets them into Berlin days (like K2/K8/K11) instead of mixing
                # the naive-as-UTC parse with a UTC window bound.
                if not (from_day <= _berlin_day(ts) <= to_day):
                    continue
                if _BRIDGE_CRITICAL_RE.search(line):
                    bridge_criticals += 1
                if _EXTRACTOR_NOT_OK_RE.search(line):
                    extractor_failures += 1
    instincts_total = 0
    instincts_without_evidence = 0
    if trading_db.exists():
        try:
            with _ro_connect(trading_db) as conn:
                rows = conn.execute(
                    "SELECT created_utc, evidence_trade_ids_json FROM instincts"
                ).fetchall()
        except sqlite3.OperationalError:
            rows = []
        for row in rows:
            dt = _parse_iso(row["created_utc"]) if row["created_utc"] else None
            if dt is None:
                continue
            day = _berlin_day(dt)
            if not (from_day <= day <= to_day):
                continue
            instincts_total += 1
            if row["evidence_trade_ids_json"] is None:
                instincts_without_evidence += 1
    verdict = (
        "PASS"
        if bridge_criticals == 0 and extractor_failures == 0 and instincts_without_evidence == 0
        else "FAIL"
    )
    return CriterionResult(
        criterion="10",
        verdict=verdict,
        measured={
            "closed_autonomous_trades_in_window": closes,
            "bridge_critical_lines": bridge_criticals,
            "extractor_ok_false_lines": extractor_failures,
            "instincts_created_in_window": instincts_total,
            "instincts_without_evidence": instincts_without_evidence,
        },
        threshold=(
            "0 CRITICAL instinct.bridge + 0 'extractor returned ok=False' + "
            "every instinct created in the window carries evidence_trade_ids_json"
        ),
    )


def evaluate_k11(
    health_jsonl: Path,
    from_day: date,
    to_day: date,
) -> CriterionResult:
    """K11 — every trading day carries ≥ 1 divergence event.

    The Phase-12 heartbeat sampler emits ``divergence_ok`` (the two sources
    agree) and the Phase-8 observability module emits ``quote_divergence`` (they
    disagree) — both into ``research_health.jsonl`` with a ``ts``. Before Phase-17
    B-2 the sampler never compared anything (233 of 233 events were
    ``divergence_no_comparator``), so this criterion is the proof that the
    comparison arm is alive.

    A window without any trading day is ``NA`` (nothing to judge).
    """
    trading_days = list(_iter_trading_days(from_day, to_day))
    if not trading_days:
        return CriterionResult(
            criterion="11",
            verdict="NA",
            measured={"trading_days_considered": 0},
            threshold="every trading day has ≥1 divergence event (divergence_ok or quote_divergence)",
            note="window contains no trading day (Mo–Fr) — nothing to judge",
        )
    per_day: dict[date, int] = {}
    if health_jsonl.exists():
        with health_jsonl.open("r", encoding="utf-8", errors="replace") as fh:
            for ln in fh:
                try:
                    ev = json.loads(ln)
                except json.JSONDecodeError:
                    continue
                if ev.get("event") not in _DIVERGENCE_EVENTS:
                    continue
                ts = ev.get("ts")
                if not ts:
                    continue
                dt = _parse_iso(ts)
                if dt is None:
                    continue
                day = _berlin_day(dt)
                per_day[day] = per_day.get(day, 0) + 1
    in_window = {d: per_day.get(d, 0) for d in trading_days}
    missing = [d.isoformat() for d, n in in_window.items() if n < 1]
    verdict = "FAIL" if missing else "PASS"
    return CriterionResult(
        criterion="11",
        verdict=verdict,
        measured={
            "trading_days_considered": len(trading_days),
            "per_day": {d.isoformat(): n for d, n in in_window.items()},
            "days_without_event": missing,
        },
        threshold="every trading day has ≥1 divergence event (divergence_ok or quote_divergence)",
        note="" if verdict == "PASS" else f"{len(missing)} trading day(s) without a divergence event",
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
    prereg: str = "v4",
    journal_file: Path | None = None,
    expect_llm_profile: str | None = None,
    exempt_models: tuple[str, ...] = (),
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
    if prereg == "v5":
        report.criteria["2"] = evaluate_k2_v5(state_dir, bars_db, day, day)
    else:
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
            trading_db, state_dir / "run_scheduler.log", day, day,
            by_logger=(prereg == "v5"),
        ),
    )
    try:
        per_day_budget = llm_usage_per_day(
            state_dir / "llm_usage.json",
            threshold=threshold,
            exempt_models=exempt_models if prereg == "v5" else (),
        )
    except BudgetFileError as exc:
        per_day_budget = None
        report.warnings.append(f"llm_usage.json unreadable: {exc}")
    if prereg == "v5":
        report.criteria["6"] = evaluate_k6_v5(
            state_dir / "llm_usage.json",
            from_day=day,
            to_day=day,
            threshold=threshold,
            exempt_models=exempt_models,
            per_day=per_day_budget,
        )
    else:
        report.criteria["6"] = evaluate_k6(
            state_dir / "llm_usage.json",
            from_day=day,
            to_day=day,
            threshold=threshold,
            per_day=per_day_budget,
        )
    if prereg == "v5":
        report.criteria["7"] = evaluate_k7_v5(
            trading_db, state_dir / "run_scheduler.log", day, day,
            expected_max_trades=expected_max_trades,
            expected_daily_loss_cap=expected_daily_loss_cap,
            expected_llm_profile=expect_llm_profile,
        )
    else:
        report.criteria["7"] = evaluate_k7(
            trading_db, state_dir / "run_scheduler.log", day, day,
            expected_max_trades=expected_max_trades,
            expected_daily_loss_cap=expected_daily_loss_cap,
        )
    report.criteria["8"] = evaluate_k8(state_dir, bars_db, day, day)
    if prereg == "v5":
        report.criteria["9"] = evaluate_k9(journal_file, day, day)
        report.criteria["10"] = evaluate_k10(
            trading_db, state_dir / "run_scheduler.log", day, day
        )
        report.criteria["11"] = evaluate_k11(
            state_dir / "research_health.jsonl", day, day
        )
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
    prereg: str = "v4",
    journal_file: Path | None = None,
    expect_llm_profile: str | None = None,
    exempt_models: tuple[str, ...] = (),
) -> SummaryReport:
    report = SummaryReport(from_day=from_day, to_day=to_day)
    report.n_trading_days = sum(1 for _ in _iter_trading_days(from_day, to_day))
    # Summary covers the full Berlin range [from_day 00:00, to_day 24:00).
    # _berlin_day_bounds(to_day)[1] is Berlin-00:00 of the next day (end-exclusive).
    from_ts, _ = _berlin_day_bounds(from_day)
    _, to_ts = _berlin_day_bounds(to_day)
    report.criteria["1"] = evaluate_k1(state_dir, from_ts=from_ts, to_ts=to_ts)
    if prereg == "v5":
        report.criteria["2"] = evaluate_k2_v5(state_dir, bars_db, from_day, to_day)
    else:
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
            trading_db, state_dir / "run_scheduler.log", from_day, to_day,
            by_logger=(prereg == "v5"),
        ),
    )
    try:
        per_day_budget = llm_usage_per_day(
            state_dir / "llm_usage.json",
            threshold=threshold,
            exempt_models=exempt_models if prereg == "v5" else (),
        )
    except BudgetFileError as exc:
        per_day_budget = None
        report.warnings.append(f"llm_usage.json unreadable: {exc}")
    if prereg == "v5":
        report.criteria["6"] = evaluate_k6_v5(
            state_dir / "llm_usage.json",
            from_day=from_day,
            to_day=to_day,
            threshold=threshold,
            exempt_models=exempt_models,
            per_day=per_day_budget,
        )
    else:
        report.criteria["6"] = evaluate_k6(
            state_dir / "llm_usage.json",
            from_day=from_day,
            to_day=to_day,
            threshold=threshold,
            per_day=per_day_budget,
        )
    if prereg == "v5":
        report.criteria["7"] = evaluate_k7_v5(
            trading_db, state_dir / "run_scheduler.log", from_day, to_day,
            expected_max_trades=expected_max_trades,
            expected_daily_loss_cap=expected_daily_loss_cap,
            expected_llm_profile=expect_llm_profile,
        )
    else:
        report.criteria["7"] = evaluate_k7(
            trading_db, state_dir / "run_scheduler.log", from_day, to_day,
            expected_max_trades=expected_max_trades,
            expected_daily_loss_cap=expected_daily_loss_cap,
        )
    report.criteria["8"] = evaluate_k8(state_dir, bars_db, from_day, to_day)
    if prereg == "v5":
        report.criteria["9"] = evaluate_k9(journal_file, from_day, to_day)
        report.criteria["10"] = evaluate_k10(
            trading_db, state_dir / "run_scheduler.log", from_day, to_day
        )
        report.criteria["11"] = evaluate_k11(
            state_dir / "research_health.jsonl", from_day, to_day
        )
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


def _resolve_exempt_models(explicit: list[str] | None) -> tuple[str, ...]:
    """Resolve the K6-v5 token-exemption list.

    Precedence: an explicit ``--exempt-model`` **wins**. A preregistered
    measurement has to pin the value — it must not silently follow a code
    default that can change without notice (the Abo deadline 2026-11-15 is
    exactly such a change). The code default is only the fallback.

    Fallback: ``SchedulerConfig().budget_exempt_models`` — the same data the
    budget gate reads (Phase-17 D-1). The import is **lazy** and **fail-soft**:
    the script runs standalone and must not die because the ``scheduler``
    package is not importable; in that case the list is empty and one WARNING
    goes to stderr (the human narrative channel).
    """
    if explicit:
        return tuple(dict.fromkeys(explicit))
    try:
        scheduler_dir = str(_REPO_ROOT / "phase8_scheduler")
        if scheduler_dir not in sys.path:
            sys.path.insert(0, scheduler_dir)
        from scheduler.config import SchedulerConfig
    except ImportError as exc:
        _LOG.warning(
            "scheduler.config not importable (%s) — K6-v5 measures without token "
            "exemptions; pin the list with --exempt-model",
            exc,
        )
        return ()
    try:
        # Read the *declared default* instead of constructing the config: the
        # constructor logs an unrelated warning about daily_loss_cap=None, and
        # the exemption list is a code default with no CLI override.
        defaults = {
            f.name: f.default
            for f in dataclasses.fields(SchedulerConfig)
        }
    except Exception as exc:  # noqa: BLE001 — fail-soft, the report must run
        _LOG.warning("SchedulerConfig defaults unreadable (%s) — no token exemptions", exc)
        return ()
    exempt = defaults.get("budget_exempt_models") or ()
    return tuple(exempt)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Phase 16 E2 autonomy-report (read-only, append-only sources).",
    )
    p.add_argument("--day", type=_parse_day, help="Single-day report (Berlin day, ISO date)")
    p.add_argument("--from", dest="from_day", type=_parse_day, help="Window start (ISO date)")
    p.add_argument("--to", dest="to_day", type=_parse_day, help="Window end (ISO date)")
    p.add_argument(
        "--summary",
        action="store_true",
        help="Evaluate PASS criteria (v4: 8, v5: 11) (--from/--to required)",
    )
    p.add_argument(
        "--prereg",
        choices=("v4", "v5"),
        default="v4",
        help="Preregistration version: v4 (default, verdict-identical) or v5 (Phase 17)",
    )
    p.add_argument(
        "--journal-file",
        type=Path,
        default=None,
        help="Operator journal export (K9); without it K9 is NA",
    )
    p.add_argument(
        "--expect-llm-profile",
        default=None,
        help="Expected llm_profile on every scheduler start-line in the window (K7-v5)",
    )
    p.add_argument(
        "--exempt-model",
        action="append",
        default=None,
        help="Model whose tokens are exempt from the K6 cap (repeatable); wins over the code default",
    )
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
    exempt_models = _resolve_exempt_models(args.exempt_model)
    common = dict(
        state_dir=args.state_dir,
        bars_db=args.bars_db,
        trading_db=args.trading_db,
        threshold=args.budget_tokens,
        expected_max_trades=args.cap_max_trades,
        expected_daily_loss_cap=args.cap_daily_loss_cap,
        prereg=args.prereg,
        journal_file=args.journal_file,
        expect_llm_profile=args.expect_llm_profile,
        exempt_models=exempt_models,
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
