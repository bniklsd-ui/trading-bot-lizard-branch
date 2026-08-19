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
                    epic, "1m", start, end, sources=("yf",),
                )
            ]
            verdict = assess_window(timestamps, start, end, 1)
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


def compute_return_divergence(ig_bars: list[Any], yf_bars: list[Any]) -> float | None:
    """Phase 13 §6 A6.0: per-bar log return over both series, return the **difference
    of returns**. A constant basis (CFD vs Kassa, Forward vs Index) cancels out; a
    genuine decoupling shows up as a non-zero delta.

    Returns ``None`` if fewer than two bars per series (no return defined) — the
    caller should emit ``divergence_no_comparator`` rather than silently 0.0, which
    is the bug Phase 12.5 had (a stuck "no divergence" answer on one-row windows).
    """
    if len(ig_bars) < 2 or len(yf_bars) < 2:
        return None
    def _returns(bars: list[Any]) -> list[float]:
        out: list[float] = []
        for i in range(1, len(bars)):
            prev, cur = bars[i - 1].close, bars[i].close
            if prev == 0:
                continue
            out.append((cur - prev) / abs(prev))
        return out
    ig_r = _returns(ig_bars)
    yf_r = _returns(yf_bars)
    if not ig_r or not yf_r:
        return None
    n = min(len(ig_r), len(yf_r))
    return abs(sum(ig_r[:n]) - sum(yf_r[:n]))


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
    - **A6.0 rendite** statt Niveau — siehe :func:`compute_return_divergence`.
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
        today = self.now_fn().strftime("%Y-%m-%d")
        if self._last_sample_date.get(epic) == today:
            return
        self._last_sample_date[epic] = today

        ig_bars = self.budgeted_ig.get_bars(epic, resolution="5m", count=3)
        if not ig_bars:
            return  # budget veto or fetch failure — fail-soft, try again tomorrow
        ig_bar = ig_bars[-1]

        # A6.1: Frische-Prüfung. Knopf getrennt von A4 (Plan §6 A6.1: Schreibpfad vs
        # Diagnose). Bei F1 (tote IG-Historie) wäre der Vergleich gegen yF eine
        # Fata Morgana — beide Reihen „stimmen überein", weil die IG-Reihe selbst
        # schon wochenalt ist.
        ig_age_min = (_parse(self.now_fn().isoformat()) - _parse(ig_bar.ts)).total_seconds() / 60.0
        if ig_age_min > self.stale_tolerance_min:
            self._emit({
                "event": "stale_source", "epic": epic, "provider": "ig",
                "bar_ts": ig_bar.ts, "age_min": ig_age_min,
            })
            mark_stale_fn(epic)
            return

        window_start = ig_bar.ts
        window_end = _iso(_parse(ig_bar.ts) + timedelta(minutes=5))
        # A6.1 + L10: sources-filter macht die yF-Quellenrein-Lesung direkt im Store;
        # kein Nachfiltern im Aufrufer mehr nötig.
        archived = self.archive.window(epic, "1m", window_start, window_end, sources=("yf",))
        yf_bars = list(archived)
        if not yf_bars:
            # A6.1: ehrlich — kein Komparator ist ein typisierter Event, kein stiller
            # return. Genau die Stille war F2.
            self._emit({
                "event": "divergence_no_comparator", "epic": epic,
                "ig_bar_ts": ig_bar.ts, "ig_close": ig_bar.close,
            })
            return

        # A6.0: Rendite-Differenz statt Niveau-Differenz. Eine konstante Basis (CFD
        # vs Kassa, Forward vs Index) fällt heraus, eine echte Entkopplung nicht.
        delta = compute_return_divergence(ig_bars, yf_bars)
        if delta is None:
            # Weniger als 2 Bars je Seite — keine Rendite definiert.
            self._emit({
                "event": "divergence_no_comparator", "epic": epic,
                "ig_bar_ts": ig_bar.ts, "reason": "too_few_bars",
            })
            return
        # ``threshold_pct`` ist in **Prozent** (Default 0.5 = 0.5 %), ``delta`` ist die
        # Fraktion der kumulierten Return-Differenz. Vergleich in einer Einheit:
        # delta*100 > threshold_pct ⇔ delta > threshold_pct/100.
        if delta * 100.0 <= self.threshold_pct:
            self._mismatch_streak[epic] = 0
            return
        self._mismatch_streak[epic] = self._mismatch_streak.get(epic, 0) + 1
        self._emit({
            "event": "quote_divergence", "epic": epic, "delta": delta,
            "kind": "return",  # A6.0 marker: this is a return-divergence, not level
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
