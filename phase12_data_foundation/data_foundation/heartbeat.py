"""Step 6 — the Mess-Heartbeat (same-day measurement-outage alarm, D12/§7 Requirement G)
and the Divergenz-Sampler (D12).

Both are deterministic, code-only (Bauprinzip: null new AI) — a same-day CRITICAL when a
scheduled measurement day produced nothing, and a daily cross-check between IG's
real-time close and the archived yFinance close so a silent quote drift gets a typed
registry status (``DS_MISMATCH``) instead of quietly poisoning every downstream
comparison.
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from zoneinfo import ZoneInfo

logger = logging.getLogger("data_foundation.heartbeat")


@dataclass(frozen=True)
class HealthVerdict:
    day: str
    bars_today: int
    pairs_opened: int
    pairs_resolved: int
    pairs_typed_expired: int
    measurable_epics: int
    worst_coverage: float
    epics_below_threshold: list[str]
    ok: bool
    problems: list[str]


def _day_bounds_iso(day_utc: str) -> tuple[str, str]:
    start = f"{day_utc}T00:00:00.000Z"
    end_date = datetime.strptime(day_utc, "%Y-%m-%d") + timedelta(days=1)
    end = end_date.strftime("%Y-%m-%dT00:00:00.000Z")
    return start, end


# Recorder lag tolerance: how many minutes we shrink the right edge of the coverage
# window. Measured 18 min on 2026-09-08 08:48 UTC (last yF bar 18 min behind wall-clock).
# ``assess_window`` counts the gap between the last bar and ``end_dt`` as part of the
# window, so without this trim a perfectly healthy session with a lagging recorder
# reads as "5-min gap exceeded" right at the edge. 30 min is a deliberate safety
# margin (18 min measured + 12 min slack) — the only knob to turn if the Recorder's
# fetch cadence ever widens is **this constant**, NOT the 5-min ``largest_gap_min``
# threshold (Phase 13 F3's "kein Loch mitten im Fenster" — still the right contract).
RECORDER_LAG_TOLERANCE_MIN = 30

# Coverage window — the Berlin trading session. Mirrors ``SchedulerConfig.window_open``
# (``"09:00"``) and ``window_close`` (``"17:30"``) in ``phase8_scheduler/scheduler/config.py``.
# Held as constants here rather than imported because Phase 12 does not import from
# Phase 8; if these ever diverge, the heartbeat's coverage window must move with the
# scheduler's trade window — that's an intentional single-knob check, not a bug.
_SESSION_OPEN_BERLIN = (9, 0)
_SESSION_CLOSE_BERLIN = (17, 30)
_SESSION_TZ = ZoneInfo("Europe/Berlin")


def _session_bounds_iso(day_utc: str) -> tuple[str, str]:
    """Berlin trading-session bounds for ``day_utc`` as UTC ISO strings.

    Phase 16 §3 J3 + J5: replaces the 00:00–24:00 UTC window for the **coverage**
    check (the bars-today and paper-trade counters still use ``_day_bounds_iso`` —
    those are wall-clock-aligned daily aggregates, not in-session coverage).

    ``end_dt`` is shifted **earlier** by :data:`RECORDER_LAG_TOLERANCE_MIN` so the
    trailing gap a lagging Recorder always produces doesn't get counted as a real
    gap. The shift happens in UTC after the Berlin-to-UTC conversion so DST is
    handled correctly (``zoneinfo`` carries it).
    """
    day = datetime.strptime(day_utc, "%Y-%m-%d").date()
    start_local = datetime(day.year, day.month, day.day, _SESSION_OPEN_BERLIN[0],
                            _SESSION_OPEN_BERLIN[1], tzinfo=_SESSION_TZ)
    end_local = datetime(day.year, day.month, day.day, _SESSION_CLOSE_BERLIN[0],
                          _SESSION_CLOSE_BERLIN[1], tzinfo=_SESSION_TZ)
    start_utc = start_local.astimezone(timezone.utc)
    end_utc = (end_local - timedelta(minutes=RECORDER_LAG_TOLERANCE_MIN)).astimezone(timezone.utc)
    return (
        start_utc.strftime("%Y-%m-%dT%H:%M:%S.") + f"{start_utc.microsecond // 1000:03d}Z",
        end_utc.strftime("%Y-%m-%dT%H:%M:%S.") + f"{end_utc.microsecond // 1000:03d}Z",
    )


def assess_day(
    archive: Any,
    paper_db_path: str,
    universe_db_path: str,
    day_utc: str,
    *,
    shadow_enabled: bool,
) -> HealthVerdict:
    """Same-day verdict for ``day_utc`` (``YYYY-MM-DD``, the daemon's local trading day).

    ``pairs_resolved`` counts shadow pairs that resolved on a real SL/TP touch;
    ``pairs_typed_expired`` counts ones that resolved via the time-stop
    (``PaperExitReason.TIME_STOP``) — both are typed outcomes. ``EXPIRED_UNRESOLVED``
    rows (a bar-data failure, not a trading outcome) count in neither, on purpose: they
    are a data-quality problem the Recorder/archive side should surface, not a "the
    measurement ran" signal.

    ``ok=False`` on exactly three conditions (P12.5 plan §2/E8 added the third):
    ``measurable_epics > 0`` and zero bars were archived today (the Recorder appears
    dead); shadow pairs are enabled and neither a real resolution nor a typed expiry
    happened all day (a zero-measurement day); or shadow pairs are *not* enabled at
    all — the measurement arm is off, so the day measures nothing regardless of what
    else ran (Phase-12 §7 "Kern" cannot pass, and the daemon cannot lie about this:
    ``shadow_enabled`` is read straight from ``config.enable_shadow_schedule``).
    ``measurable_epics == 0`` on its own only adds a problem note — it is the known
    bootstrap/operator-prerequisite state (Step 3's ``SymbolResolver`` hasn't run
    yet), not an infrastructure failure to page on.
    """
    from universe.store import UniverseStore

    start, end = _day_bounds_iso(day_utc)
    # Phase 16 §3 J3: coverage on the trading session (Berlin 09:00–17:30 minus the
    # Recorder's lag tolerance), not 00:00–24:00. The overnight gap otherwise reißt
    # the 5-min ``largest_gap_min`` threshold on every single trading day, making
    # K4 structurally unreachable since 2026-08-24 (10 consecutive ``ok=False``
    # measurements). The bars-today + paper-trade counters stay wall-clock-aligned
    # because they're daily aggregates, not coverage measures.
    cov_start, cov_end = _session_bounds_iso(day_utc)
    bars_today = archive.bars_written_since(start, end)

    conn = sqlite3.connect(paper_db_path)
    try:
        pairs_opened = conn.execute(
            "SELECT COUNT(*) FROM paper_trades WHERE created_utc >= ? AND created_utc < ?",
            (start, end),
        ).fetchone()[0]
        pairs_resolved = conn.execute(
            "SELECT COUNT(*) FROM paper_trades WHERE status = 'RESOLVED' "
            "AND exit_reason IN ('SL', 'TP') AND resolved_utc >= ? AND resolved_utc < ?",
            (start, end),
        ).fetchone()[0]
        pairs_typed_expired = conn.execute(
            "SELECT COUNT(*) FROM paper_trades WHERE status = 'RESOLVED' "
            "AND exit_reason = 'TIME_STOP' AND resolved_utc >= ? AND resolved_utc < ?",
            (start, end),
        ).fetchone()[0]
    finally:
        conn.close()

    store = UniverseStore(universe_db_path)
    try:
        measurable_epics_records = store.measurable_universe()
        measurable_epics = len(measurable_epics_records)
    finally:
        store.close()

    # Phase 13 §6 A6.2: coverage statt Bar-Zählung. F3 hat gezeigt, dass 496 yF-Bars
    # pro Epic ≠ "Fenster ist dicht" — eine Mitten-Lücke kann das Mess-Substrat
    # unbrauchbar machen, ohne dass die Zählung das anzeigt. assess_window über das
    # Tages-Fenster ist die einzige preiswerte Operation, die beides misst (Dichte
    # und größte zusammenhängende Lücke).
    #
    # Phase 16 §3 J3: window = ``_session_bounds_iso`` (Berlin 09:00–17:30 minus
    # Recorder lag), not ``_day_bounds_iso`` (00:00–24:00). The overnight gap
    # otherwise reißt the 5-min ``largest_gap_min`` threshold on every trading day.
    from data_foundation.coverage import MIN_WINDOW_RATIO, assess_window

    worst_coverage = 1.0
    epics_below_threshold: list[str] = []
    if measurable_epics > 0:
        for epic_record in measurable_epics_records:
            epic = epic_record.get("epic") if isinstance(epic_record, dict) else getattr(epic_record, "epic", None)
            if not epic:
                continue
            timestamps = [
                b.ts_utc for b in archive.window(
                    epic, "1m", cov_start, cov_end, sources=("yf",),
                )
            ]
            verdict = assess_window(timestamps, cov_start, cov_end, 1)
            if verdict.ratio < worst_coverage:
                worst_coverage = verdict.ratio
            if verdict.largest_gap_min > 5:  # MAX_WINDOW_GAP_MIN — same threshold as A1
                epics_below_threshold.append(epic)

    problems: list[str] = []
    ok = True
    if measurable_epics == 0:
        problems.append(
            "no measurable epic — SymbolResolver has not verified any instrument yet "
            "(expected until the resolver runs, not itself an alarm)"
        )
    if measurable_epics > 0 and bars_today == 0:
        problems.append("zero bars archived today despite measurable epics (Recorder appears dead)")
        ok = False
    if not shadow_enabled:
        problems.append(
            "measurement arm off: enable_shadow_schedule is False — no shadow pairs can be "
            "opened, so this day measures nothing (Phase-12 §7 Kern cannot pass)"
        )
        ok = False
    if shadow_enabled and pairs_resolved == 0 and pairs_typed_expired == 0:
        problems.append("shadow pairs enabled but zero resolved/expired paper trades today")
        ok = False
    if epics_below_threshold:
        problems.append(
            f"{len(epics_below_threshold)} measurable epic(s) below the coverage threshold "
            f"({MIN_WINDOW_RATIO:.0%} density or 5-min gap): {epics_below_threshold}"
        )
        ok = False

    return HealthVerdict(
        day=day_utc,
        bars_today=bars_today,
        pairs_opened=pairs_opened,
        pairs_resolved=pairs_resolved,
        pairs_typed_expired=pairs_typed_expired,
        measurable_epics=measurable_epics,
        worst_coverage=worst_coverage,
        epics_below_threshold=epics_below_threshold,
        ok=ok,
        problems=problems,
    )


def _default_now() -> datetime:
    return datetime.now(timezone.utc)


# Phase 17 B-2 (2026-10-17): yF 1m bars reach the archive 15.6–20.3 min after their timestamp
# (p10/max, measured 2026-10-16); the comparator window must end this long before "now".
COMPARATOR_LAG_MIN: int = 25
IG_SAMPLE_COUNT: int = 8        # 8 × 5m = 40 min → always ≥ 1 complete bar older than the lag
MIN_YF_BARS: int = 4            # ≥ 4 of the 5 one-minute bars, or the window is not comparable


def window_return_divergence(ig_bar: Any, yf_bars: list[Any]) -> float | None:
    """|return(IG 5m bar) − return(yF 1m bars over the SAME five minutes)| (Phase 17 B-2).

    return = (last close − first open) / first open; a constant CFD-vs-cash basis cancels.
    ``None`` when a side has no usable open. Replaces ``compute_return_divergence``, which
    summed two 5-minute IG returns against two 1-minute yF returns (different horizons).
    """
    if not yf_bars or not ig_bar.open or not yf_bars[0].open:
        return None
    ig_r = (ig_bar.close - ig_bar.open) / abs(ig_bar.open)
    yf_r = (yf_bars[-1].close - yf_bars[0].open) / abs(yf_bars[0].open)
    return abs(ig_r - yf_r)


@dataclass
class DivergenceSampler:
    """Once-per-epic-per-day IG-vs-yFinance cross-check (D12).

    ``budgeted_ig`` is a ``BudgetedIGBarProvider(spend_kind="sample")`` — the sample
    itself is budget-gated exactly like every other IG call (D10), so a busy day can't
    let this silently exhaust the allowance. ``archive`` is read for the yFinance
    comparator over the *same window* as the IG probe — never a fresh yFinance fetch
    (D12: "verglichen gegen die Archiv-yF-Bars desselben Fensters"), so a day the
    Recorder didn't cover simply produces no comparison, not a stale/wrong one.

    Per-epic throttle and mismatch-streak state are held in memory (``dict``s) — reset
    on daemon restart, acceptable for a once-daily sample (Plan §6 Step 6, no test
    requires persistence across restarts).

    Phase 13 §6 A6:
    - **A6.0 rendite** statt Niveau — siehe :func:`window_return_divergence`.
    - **A6.1 stale** — wenn der IG-Bar schon älter als ``stale_tolerance_min`` ist,
      wird ``mark_stale_fn(epic)`` gerufen statt eines Vergleichs. Knopf getrennt
      von A4 (Schreibpfad vs Diagnose).
    - **A6.1 quellenrein** — die yF-Seite kommt aus ``sources=("yf",)`` (L10), nicht
      aus einer Nachfilterung im Aufrufer.
    - **A6.1 ehrlich** — kein yF-Komparator ⇒ typisierter Event statt Stille.
    """

    budgeted_ig: Any
    archive: Any
    threshold_pct: float = 0.5
    health_sink: Callable[[dict], None] | None = None
    now_fn: Callable[[], datetime] = _default_now
    stale_tolerance_min: int = 120
    _last_sample_date: dict[str, str] = field(default_factory=dict)
    _mismatch_streak: dict[str, int] = field(default_factory=dict)

    def _emit(self, event: dict[str, Any]) -> None:
        if self.health_sink is None:
            return
        try:
            self.health_sink(event)
        except Exception:  # noqa: BLE001 — a health sink must never break the sample
            pass

    def sample_epic(
        self, epic: str,
        mark_mismatch_fn: Callable[[str], Any],
        mark_stale_fn: Callable[[str], Any],
    ) -> None:
        """Sample ``epic`` at most once per calendar day. Two callbacks now:

        * ``mark_mismatch_fn(epic)`` — after the **second** consecutive divergence.
        * ``mark_stale_fn(epic)`` — when the IG bar is already older than
          ``stale_tolerance_min``. Sets ``data_source_status=DS_STALE_SOURCE`` (the
          caller maps the call to the registry).

        Both are single-arg rather than calling the registry directly — same shape
        as the original callback, just one extra parameter."""
        # (a) Throttle prüfen, aber noch nicht setzen — eine „no_comparator"-Wartezeit
        # darf das Tageskontingent NICHT verbrauchen, sonst trifft der Sampler den
        # yF-Lag an Tagen ohne ein einziges vollständiges IG-Fenster und liefert für
        # den Rest des Tages keine echten Vergleiche mehr (Plan §6 B-2).
        today = self.now_fn().strftime("%Y-%m-%d")
        if self._last_sample_date.get(epic) == today:
            return

        # (b) IG-Bars laden. Leer = Budget-Veto oder Fetch-Fehler: fail-soft, KEIN
        # Throttle, morgen wieder versuchen.
        ig_bars = self.budgeted_ig.get_bars(epic, resolution="5m", count=IG_SAMPLE_COUNT)
        if not ig_bars:
            return

        # (c) Frische-Check auf dem neuesten IG-Bar (A6.1). Bei stale: Event +
        # mark_stale_fn + Throttle setzen + return. Hier setzen wir den Throttle
        # mit, weil der Fehler echt ist (kein Komparator-Problem).
        ig_bar_latest = ig_bars[-1]
        ig_age_min = (_parse(self.now_fn().isoformat()) - _parse(ig_bar_latest.ts)).total_seconds() / 60.0
        if ig_age_min > self.stale_tolerance_min:
            self._last_sample_date[epic] = today
            self._emit({
                "event": "stale_source", "epic": epic, "provider": "ig",
                "bar_ts": ig_bar_latest.ts, "age_min": ig_age_min,
            })
            mark_stale_fn(epic)
            return

        # (d) Comparator-Lag-Filter. Wir suchen den letzten IG-5m-Bar, dessen
        # 5-Minuten-Fenster **vollständig** älter als now-COMPARATOR_LAG_MIN ist —
        # erst dieser Bar ist ein ehrlicher Vergleichspunkt, weil yF-Bars desselben
        # Fensters mit Sicherheit im Archiv liegen (Lag gemessen 15,6–20,3 min).
        cutoff = _parse(self.now_fn().isoformat()) - timedelta(minutes=COMPARATOR_LAG_MIN)
        complete = [b for b in ig_bars if _parse(b.ts) + timedelta(minutes=5) <= cutoff]
        if not complete:
            # Kein einziger IG-5m-Bar ist alt genug — wir warten, bis die Recorder-
            # Lag-Toleranz überschritten ist. KEIN Throttle: morgen / nächste Stunde
            # wieder versuchen.
            self._emit({
                "event": "divergence_no_comparator", "epic": epic,
                "reason": "no_complete_bar",
            })
            return

        # (e) yF-Bars im **gleichen** 5-Minuten-Fenster (L10: sources=("yf",) macht
        # die Quellenrein-Lesung direkt im Store). Zu wenig yF-Bars ⇒ ehrlich
        # typisierter Event, KEIN Throttle.
        ig_bar = complete[-1]
        window_start = ig_bar.ts
        window_end = _iso(_parse(ig_bar.ts) + timedelta(minutes=5))
        yf_bars = list(self.archive.window(epic, "1m", window_start, window_end, sources=("yf",)))
        if len(yf_bars) < MIN_YF_BARS:
            self._emit({
                "event": "no_comparator", "epic": epic,
                "ig_bar_ts": ig_bar.ts, "reason": "partial_yf_window",
                "n_yf": len(yf_bars),
            })
            return

        # (f) Rendite-Vergleich (window_return_divergence: IG-5m gegen yF-1m im
        # SELBEN Fenster — verschiedene Horizonte sind weg). None = keine offene
        # Bar auf einer Seite, kein sinnvoller Vergleich.
        delta = window_return_divergence(ig_bar, yf_bars)
        if delta is None:
            self._emit({
                "event": "no_comparator", "epic": epic,
                "ig_bar_ts": ig_bar.ts, "reason": "zero_open",
            })
            return

        # (g) **Erst jetzt** Throttle setzen — wir haben einen echten Vergleich
        # gefahren. Agreement / Divergence wie bisher; bei Agreement gibt es das
        # neue ``divergence_ok``-Event, das dem Shakedown-Kriterium K11
        # („jeder Handelstag ≥ 1 Event divergence_ok oder quote_divergence") als
        # Wahrheits-Quelle dient.
        self._last_sample_date[epic] = today
        if delta * 100.0 <= self.threshold_pct:
            self._mismatch_streak[epic] = 0
            self._emit({
                "event": "divergence_ok", "epic": epic,
                "delta": delta, "ig_bar_ts": ig_bar.ts, "n_yf": len(yf_bars),
            })
            return
        self._mismatch_streak[epic] = self._mismatch_streak.get(epic, 0) + 1
        self._emit({
            "event": "quote_divergence", "epic": epic, "delta": delta,
            "kind": "return",  # A6.0 marker: this is a return-divergence, not level
            "ig_bar_ts": ig_bar.ts, "n_yf": len(yf_bars),
        })
        if self._mismatch_streak[epic] >= 2:
            mark_mismatch_fn(epic)


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def _parse(ts: str) -> datetime:
    normalized = ts.replace("Z", "+00:00") if ts.endswith("Z") else ts
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
