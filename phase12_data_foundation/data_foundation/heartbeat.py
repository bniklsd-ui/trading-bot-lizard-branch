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

    ``ok=False`` on exactly two conditions (Plan §6 Step 6): ``measurable_epics > 0``
    and zero bars were archived today (the Recorder appears dead), or shadow pairs are
    enabled and neither a real resolution nor a typed expiry happened all day (a
    zero-measurement day). ``measurable_epics == 0`` on its own only adds a problem
    note — it is the known bootstrap/operator-prerequisite state (Step 3's
    ``SymbolResolver`` hasn't run yet), not an infrastructure failure to page on.
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
        measurable_epics = len(store.measurable_universe())
    finally:
        store.close()

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
    if shadow_enabled and pairs_resolved == 0 and pairs_typed_expired == 0:
        problems.append("shadow pairs enabled but zero resolved/expired paper trades today")
        ok = False

    return HealthVerdict(
        day=day_utc,
        bars_today=bars_today,
        pairs_opened=pairs_opened,
        pairs_resolved=pairs_resolved,
        pairs_typed_expired=pairs_typed_expired,
        measurable_epics=measurable_epics,
        ok=ok,
        problems=problems,
    )


def _default_now() -> datetime:
    return datetime.now(timezone.utc)


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
    """

    budgeted_ig: Any
    archive: Any
    threshold_pct: float = 0.5
    health_sink: Callable[[dict], None] | None = None
    now_fn: Callable[[], datetime] = _default_now
    _last_sample_date: dict[str, str] = field(default_factory=dict)
    _mismatch_streak: dict[str, int] = field(default_factory=dict)

    def _emit(self, event: dict[str, Any]) -> None:
        if self.health_sink is None:
            return
        try:
            self.health_sink(event)
        except Exception:  # noqa: BLE001 — a health sink must never break the sample
            pass

    def sample_epic(self, epic: str, mark_mismatch_fn: Callable[[str], Any]) -> None:
        """Sample ``epic`` at most once per calendar day; ``mark_mismatch_fn(epic)`` is
        called after the **second** consecutive divergence, not the first (Plan §6 Step
        6 test bullet). Deliberately a single-arg callback rather than calling
        ``UniverseStore.set_symbol`` directly — that call needs the record's existing
        ``yf_ticker``/``symbol_source`` (a read-then-write the caller already has to do
        for its own registry access), not something this sampler should know about."""
        today = self.now_fn().strftime("%Y-%m-%d")
        if self._last_sample_date.get(epic) == today:
            return
        self._last_sample_date[epic] = today

        ig_bars = self.budgeted_ig.get_bars(epic, resolution="5m", count=3)
        if not ig_bars:
            return  # budget veto or fetch failure — fail-soft, try again tomorrow
        ig_bar = ig_bars[-1]

        window_start = ig_bar.ts
        window_end = _iso(_parse(ig_bar.ts) + timedelta(minutes=5))
        archived = self.archive.window(epic, "1m", window_start, window_end, prefer=("yf",))
        # `window`'s `prefer` only *ranks* sources when several cover the same minute —
        # it does not exclude an IG-sourced row from the result. Filtering explicitly is
        # the only way to guarantee an IG-vs-IG comparison never happens (it would
        # always agree, silently defeating this whole check).
        yf_bars = [b for b in archived if b.source == "yf"]
        if not yf_bars:
            return  # Recorder hasn't covered this window yet — nothing to compare

        from scheduler.observability import check_divergence

        event = check_divergence(epic, ig_bar.close, yf_bars[-1].close, threshold_pct=self.threshold_pct)
        if event is None:
            self._mismatch_streak[epic] = 0
            return
        self._mismatch_streak[epic] = self._mismatch_streak.get(epic, 0) + 1
        self._emit(event)
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
