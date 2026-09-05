"""Phase 13 §6 C2 — S4 GapRescue (Default AUS).

Rettungs-Stufe für **gealterte Restlücken** im Archiv: das S1-Signal (LS)
und S2 (yFinance) liefern beide nicht, der Trade-Window ist lückenhaft,
und der Lücken-Anteil ist alt genug, dass weder S1 noch S2 ihn in
absehbarer Zeit nachträglich abdecken werden.

Mechanik: geht am Chain-Provider vorbei **direkt** an
:meth:`BrokerAdapter.get_historical_ohlcv` (Bereichs-API mit ``from``/``to``,
nicht das count-basierte ``get_ohlcv``) — der Plan §6 C2 stellt fest, dass
die Chain den count-Pfad nicht bietet. Schreibt mit ``source='ig'`` ins
Archiv (das ist eine echte IG-Bereichs-API-Antwort, **kein** Selbstbetrug),
**gedrosselt** auf einen Call pro Epic pro Tag, und prüft die frische der
Antwort am Kaufort (L8-Stale-Assertion, wiederverwendet aus A4).

**Default AUS** (Plan §6 C2: „Erst nach S1/S2/S3 kalibrieren"). Operator
muss ``enable_gap_rescue=True`` explizit setzen — sonst ist die ganze
Klasse nicht im Wiring. Das ist die gleiche Disziplin wie
``enable_shadow_schedule`` / ``enable_bar_stream``.

Buchung: ``spend_kind='rescue'`` ist der eigene Ledger-Eintrag (Plan §6
C2: „eigener ``spend_kind='rescue'`` — der Ledger wird eindeutig"). Der
geteilte Provider taggte Tracker-Top-ups fälschlich als ``research``,
die Kostenexplosion war im Ledger nicht auffindbar. Diese Stufe macht
es **auffindbar**.

Dataclass ``RescueReport`` ist der Vertrag nach außen (Operator-Script
in einer späteren Session liest sie aus); ``rescue_epic`` gibt **immer**
eine Report-Instanz zurück, auch bei Skip-Pfaden — kein ``None``, das
der Aufrufer erst entpacken müsste.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

logger = logging.getLogger("live_data.rescue")

NowFn = Callable[[], datetime]


@dataclass(frozen=True)
class RescueConfig:
    """Phase 15 §6 D3 — Operator-facing config for Pfad A (S4 GapRescue).

    ``enable_gap_rescue`` is the **master switch** for the S4 operator
    tool (`phase13_live_data/scripts/gap_rescue_operator.py`). Default
    **AUS** (Plan §6 D3, analog ``enable_shadow_schedule`` /
    ``enable_divergence_sampler`` / ``enable_paper_debate``).

    The Operator-Tool requires **both** ``enable_gap_rescue=True``
    **and** ``--apply`` to actually write to the archive — die
    Doppel-Sperre aus dem Plan (S. 689) verhindert, dass eine einzige
    Bedingung versehentlich scharf schaltet.

    **Kein** Feld in ``SchedulerConfig`` (Plan §4: Phase 8 ist NICHT
    cross-phase-freigegeben für Phase 15), **kein** Wiring im Daemon
    — Pfad A ist bewusst ein **Operator-Tool**, kein Scheduler-Feature
    (Plan §6 D3: „Pfad A ist ein Operator-Tool, kein Daemon-Feature.
    P13-Findings §8.2 sagt wörtlich ‚GapRescue-Skript als Operator-Tool
    mit Schedule'.").

    Attributes:
        enable_gap_rescue: master switch (default ``False``).
        epics: explicit epic list. Empty tuple means: Operator-Tool
            resolves via ``UniverseStore.measurable_universe()``
            (analog ``scripts/capital_backfill.py --auto``). Frozen
            tuple to keep the dataclass truly hashable.
        max_points_per_run: Punkte-Deckel pro Lauf (Plan §6 D3
            + §9.2: 560 stammt aus P13-Findings §8.2, **nicht
            nachgerechnet** — vor dem Scharfschalten gegen
            ``source_spend`` verifizieren, Plan §9.2).
    """

    enable_gap_rescue: bool = False
    epics: tuple[str, ...] = field(default_factory=tuple)
    max_points_per_run: int = 560


@dataclass
class RescueReport:
    """Outcome of one :meth:`GapRescue.rescue_epic` call.

    ``points_spent`` is the **booked** spend (Plan §6 C2: spend is
    recorded **before** the bars are written, IG has already billed
    the call). ``bars_written`` may be **less** than the IG response
    count if the Stale-Assertion rejects some — those are still
    budgeted.
    """

    epic: str
    gaps_found: int
    bars_written: int
    points_spent: int
    skipped_reason: str | None = None


def _parse_iso(ts: str) -> datetime:
    if not ts:
        return datetime.now(timezone.utc)
    try:
        normalized = ts.replace("Z", "+00:00") if ts.endswith("Z") else ts
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return datetime.now(timezone.utc)


def _age_minutes(ts: str, now: datetime) -> float:
    return (now - _parse_iso(ts)).total_seconds() / 60.0


def _add_minute_iso(ts: str) -> str:
    try:
        dt = _parse_iso(ts)
        return (dt + timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:00.000Z")
    except Exception:  # noqa: BLE001
        return ts


def _to_minute_iso(ts: str) -> str:
    """Truncate an ISO timestamp to its minute (bar-open time)."""
    try:
        dt = _parse_iso(ts)
        dt = dt.replace(second=0, microsecond=0)
        return dt.strftime("%Y-%m-%dT%H:%M:00.000Z")
    except Exception:  # noqa: BLE001
        return ts


class GapRescue:
    """S4 — gealterte Restlücken über die IG-Bereichs-API, gedrosselt
    und frische-geprüft.

    Constructor parameters are the operator's tuning surface. Defaults
    match Plan §5.6; the L8 Stale-Assertion default is 120 min (A4
    identisch, weil es dasselbe Risiko ist — „IG antwortet ok, aber
    liefert alte Bars"). Constructor takes ``broker`` (Phase-1
    ``BrokerAdapter``), ``budget`` (``SourceBudget``) and ``archive``
    (the gap-finder). It does **not** own the bars-to-write conversion
    — it calls ``archive.insert_bars`` directly (the contract:
    ``Bar`` with ``source='ig'``).
    """

    def __init__(
        self,
        broker: Any,
        budget: Any,
        archive: Any,
        *,
        max_calls_per_epic_per_day: int = 1,
        min_gap_age_min: int = 60,
        max_points_per_call: int = 60,
        stale_tolerance_min: int = 120,
        now_fn: NowFn | None = None,
    ) -> None:
        self._broker = broker
        self._budget = budget
        self._archive = archive
        self._max_calls_per_epic_per_day = max_calls_per_epic_per_day
        self._min_gap_age_min = min_gap_age_min
        self._max_points_per_call = max_points_per_call
        # Phase 13 §6 A4 / L8: die Frische-Assertion aus A4 lebt hier
        # wiederverwendet — eine IG-Bereichs-Antwort mit ``ok=True``
        # und ``ts``-vor-zwei-Tagen ist nicht „historische Daten", sie
        # ist „tote Historie" (F1). Knopf getrennt von A4 und A6.1
        # (Schreibpfad / Diagnose / Rettung — drei Stale-Hooks, drei
        # unabhängige Konstanten).
        self._stale_tolerance_min = stale_tolerance_min
        self._now_fn = now_fn or (lambda: datetime.now(timezone.utc))
        # Per-Epic-Per-Tag throttle state (in-memory, daemon reset clears
        # it; Plan §6 C2.3: Drossel nach dem ``_last_sample_date``-Muster).
        self._last_rescue_date: dict[str, str] = {}

    def rescue_epic(
        self, epic: str, day_start_utc: str, day_end_utc: str
    ) -> RescueReport:
        """Attempt one S4 rescue for ``epic`` over ``[day_start_utc, day_end_utc)``.

        Returns a :class:`RescueReport` **always** (even on skip paths) —
        no ``None``, no exceptions. The caller decides what to do with
        the report (operator-script aggregates; in-line wiring logs).
        """
        today = self._now_fn().strftime("%Y-%m-%d")
        if self._last_rescue_date.get(epic) == today:
            return RescueReport(epic=epic, gaps_found=0, bars_written=0,
                               points_spent=0, skipped_reason="throttled_today")
        # Find the oldest gap. If the gap is too fresh (younger than
        # ``min_gap_age_min``), S1/S2 may still cover it — wait.
        try:
            gap = self._find_oldest_gap(epic, day_start_utc, day_end_utc)
        except Exception:  # noqa: BLE001 — rescue is best-effort
            logger.exception("rescue_epic: gap scan failed for %s", epic)
            return RescueReport(epic=epic, gaps_found=0, bars_written=0,
                               points_spent=0, skipped_reason="scan_error")
        if gap is None:
            return RescueReport(epic=epic, gaps_found=0, bars_written=0,
                               points_spent=0, skipped_reason="no_gap")
        gap_start, gap_end = gap
        if _age_minutes(gap_end, self._now_fn()) < self._min_gap_age_min:
            return RescueReport(epic=epic, gaps_found=1, bars_written=0,
                               points_spent=0, skipped_reason="gap_too_fresh")
        # Approximate gap size in minutes → points (1 bar/minute for
        # ``MINUTE`` resolution, capped at ``max_points_per_call``). The
        # ``from``/``to`` API is range-based, not count-based, so we
        # ask IG for the actual span and let the API cap server-side.
        minutes = max(1, int((_parse_iso(gap_end) - _parse_iso(gap_start)).total_seconds() / 60.0))
        points = min(minutes, self._max_points_per_call)
        if not self._budget.can_spend(points):
            return RescueReport(epic=epic, gaps_found=1, bars_written=0,
                               points_spent=0, skipped_reason="budget")
        env = self._call_history(epic, gap_start, gap_end)
        # Phase 15 Block-D-Folgefix Schritt 2 (2026-09-03): Spend-Booking-
        # Logik korrigiert (Audit-Trail §Bug 3, Z. 1106-1126 + Z. 1219-1240).
        # Der vorherige Pfad buchte `record_spend` VOR dem `env.ok`-Check —
        # korrekt für IG-Antworten egal welchen Inhalts (leer, stale, partial:
        # Call hat stattgefunden, IG hat abgerechnet), aber FALSCH für
        # Exception-Fälle (z.B. TypeError aus Step 1): Call hat IG nie erreicht,
        # wir buchen trotzdem. Heute live geschehen: 250 Punkte für 5 Calls,
        # die IG nie gesehen hat.
        #
        # Fix: `record_spend` läuft **nach** dem `env.ok`-Check. Bei `not_ok`
        # (Exception + nicht-OK-Antwort) wird KEIN Spend gebucht. Bei
        # erfolgreicher IG-Antwort mit stale/empty Daten bleibt der Spend
        # weiterhin gebucht (L8-Logik aus A4 — IG hat den Call gesehen).
        #
        # `_last_rescue_date[epic] = today` muss **vor** dem Call passieren,
        # sonst blockiert eine Exception die Throttle für denselben Tag.
        self._last_rescue_date[epic] = today
        if not getattr(env, "ok", False):
            # Call hat IG nie erreicht (Exception) oder hat nicht_ok geantwortet
            # → KEIN Spend, kein Throttle-Reset nötig (oben bereits gesetzt).
            return RescueReport(epic=epic, gaps_found=1, bars_written=0,
                               points_spent=0, skipped_reason="not_ok")
        self._budget.record_spend(points, "rescue")
        raw_bars = (getattr(env, "data", None) or {}).get("bars") or []
        if not raw_bars:
            return RescueReport(epic=epic, gaps_found=1, bars_written=0,
                               points_spent=points, skipped_reason="empty")
        # L8 Stale-Assertion: reject the response if the **newest** bar
        # is older than the tolerance. IG may have a 32-day-stale row
        # in a freshly-issued envelope (F1) — defence in depth on top
        # of A4.
        newest_ts = max(
            (b.get("timestamp", "") for b in raw_bars if isinstance(b, dict)),
            default="",
        )
        if newest_ts and _age_minutes(newest_ts, self._now_fn()) > self._stale_tolerance_min:
            logger.warning(
                "GapRescue: stale response for %s, newest=%s, age=%.0fmin (tolerance %d) — "
                "spend already booked (%d pts), no write", epic, newest_ts,
                _age_minutes(newest_ts, self._now_fn()), self._stale_tolerance_min, points,
            )
            return RescueReport(epic=epic, gaps_found=1, bars_written=0,
                               points_spent=points, skipped_reason="stale_history")
        # Convert + write. The archive expects ``Bar`` with source='ig'.
        bars_written = self._write_bars(epic, raw_bars)
        return RescueReport(
            epic=epic, gaps_found=1, bars_written=bars_written,
            points_spent=points, skipped_reason=None,
        )

    # -- internals ---------------------------------------------------------

    def _call_history(self, epic: str, start_utc: str, end_utc: str) -> Any:
        """
        The actual broker call. Range-basiert: ``get_historical_ohlcv`` ist die
        Bereichs-API mit ``from``/``to`` (nicht count-basiert wie ``get_ohlcv``),
        siehe Plan §6 C2 + rescue.py Module-Docstring Z. 9-11 + ig_adapter.py:449.

        Phase 15 Block-D-Folgefix (2026-09-03, Audit-Trail): der frühere Aufruf
        ``method(epic, "MINUTE", count, from_dt=start_utc, to_dt=end_utc)``
        verletzt den ABC-Vertrag (``(epic, from_dt, to_dt, resolution)``) — IG
        antwortete mit ``TypeError: got multiple values for argument 'from_dt'``.
        Fix: 4 positionelle Args in der Vertrag-Reihenfolge, kein ``count``.
        """
        method = getattr(self._broker, "get_historical_ohlcv", None)
        if method is None:
            return _Env(False, "broker has no get_historical_ohlcv")
        try:
            return method(epic, start_utc, end_utc, "MINUTE")
        except Exception:  # noqa: BLE001
            logger.exception("get_historical_ohlcv raised for %s", epic)
            return _Env(False, "exception")

    def _write_bars(self, epic: str, raw_bars: list[dict]) -> int:
        """Convert raw IG dicts to ``Bar`` and write through. Returns the
        count actually written (excludes duplicates already in the
        archive — INSERT OR IGNORE on the PK).
        """
        from data_foundation.models import Bar, normalize_bar_ts

        now_iso = self._now_fn().strftime("%Y-%m-%dT%H:%M:%S.000Z")
        bars = []
        for b in raw_bars:
            if not isinstance(b, dict):
                continue
            try:
                bars.append(Bar(
                    epic=epic,
                    resolution="1m",
                    ts_utc=normalize_bar_ts(b.get("timestamp", "")),
                    open=float(b.get("open", 0.0)),
                    high=float(b.get("high", 0.0)),
                    low=float(b.get("low", 0.0)),
                    close=float(b.get("close", 0.0)),
                    volume=float(b.get("volume", 0.0)) if b.get("volume") not in (None, "") else None,
                    source="ig",
                    fetched_at=now_iso,
                ))
            except (KeyError, ValueError, TypeError) as exc:
                logger.debug("skipping malformed rescue bar for %s: %s", epic, exc)
                continue
        if not bars:
            return 0
        try:
            return self._archive.insert_bars(bars)
        except Exception:  # noqa: BLE001 — rescue is best-effort
            logger.exception("rescue archive.insert_bars failed for %s", epic)
            return 0

    def _find_oldest_gap(
        self, epic: str, day_start_utc: str, day_end_utc: str
    ) -> tuple[str, str] | None:
        """Walk the archive's yF rows for ``[day_start, day_end)`` and
        return the **oldest** contiguous gap. ``None`` if the day is
        dense enough to skip.

        Two-pass detection: (1) gaps between consecutive yF bars, (2) a
        tail gap from the last yF bar to ``day_end_utc``. The leading
        gap (``day_start_utc`` → first yF bar) is *not* a rescue target —
        the S1 stream will fill it if it ever arrives (and S1 starts
        fresh on each daemon run anyway).
        """
        if self._archive is None:
            return None
        bars = sorted(
            self._archive.window(epic, "1m", day_start_utc, day_end_utc, sources=("yf",)),
            key=lambda b: b.ts_utc,
        )
        if not bars:
            return day_start_utc, day_end_utc
        # Pass 1: gaps between consecutive yF bars.
        prev = day_start_utc
        for b in bars:
            if b.ts_utc > _add_minute_iso(prev):
                return prev, b.ts_utc
            prev = b.ts_utc
        # Pass 2: tail gap (last yF bar → day_end_utc). This is the
        # case the recorder-stopped-mid-day scenario produces: bars
        # up to 14:00, then silence. Without this pass the rescue
        # would never fire. The window is [start, end) (end exclusive),
        # so the last "filled" minute is one minute **before** end — a
        # tail gap is therefore defined as ``last_ts + 1 min < end``
        # (i.e. at least one full minute of silence).
        last_ts = bars[-1].ts_utc
        if _add_minute_iso(last_ts) < day_end_utc:
            return last_ts, day_end_utc
        return None


@dataclass
class _Env:
    ok: bool
    error: str | None = None
    data: dict | None = None
