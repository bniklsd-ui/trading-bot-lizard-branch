"""Paper-trade model + deterministic engine (V3-D6/D7).

Block A (WE 1) built the model only. Block B (WE 2, this addition) adds the
"deterministischer Kern" (plan §10.1/§10.2): ``open_shadow_pair``/``resolve_paper_trade``
(pure functions) and ``PaperEngine``/``PaperTradeTracker`` (the stateful wiring around
them). No AI in this module — the one AI call (lesson reflect for a resolved pair) reuses
``reflect.build_paper_lesson_prompt``/``validate_abstain_lesson`` via an injected,
duck-typed LLM (mirrors ``AbstainLessonSink``'s pattern), never triggers an order, and
stays outside the deterministic core itself.

Council-Paper-Call (§10.3, built the following weekend session, 2026-07-17): a second,
optional AI call, still best-effort and still never triggering an order — only ever
producing a ``paper_trades`` row. ``PaperDebateCaller`` is the smallest additive reuse of
the P6 debate machinery: a single forced-pick LLM request (not the full multi-round
Bull/Bear/Judge orchestrator — ``PaperEngine`` has no broker access to build a
``DebateContext``, and the plan calls for the smallest additive form). It takes an
injected ``prompt_builder`` callable (the real one lives in
``debate.prompts.build_paper_pick_prompt``) so this module still imports nothing from
``debate`` — the P8 wiring layer is the only place that crosses the phase boundary,
mirroring how ``debate_runner`` is duck-typed into ``phase5_execution``.
"""

from __future__ import annotations

import dataclasses
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Mapping, Sequence
from uuid import uuid4

from abstain_lessons.models import AbstainReason, AbstainRecord
from abstain_lessons.reflect import build_paper_lesson_prompt, validate_abstain_lesson

logger = logging.getLogger("abstain_lessons.paper")


def _utc_iso(dt: datetime) -> str:
    """``dt`` as an ISO 8601 string with ms precision and Z suffix."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def _utc_iso_now() -> str:
    """Current UTC time as an ISO 8601 string with ms precision and Z suffix."""
    return _utc_iso(datetime.now(timezone.utc))


def _parse_utc(ts: str) -> datetime:
    """Inverse of :func:`_utc_iso` — every timestamp this module compares is written by
    it, so the format is fixed and no tolerant parser is warranted."""
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)


class PaperVariant(str, Enum):
    """Which paper-trade mechanism produced this row (V3-D6)."""

    SHADOW_BUY = "SHADOW_BUY"
    SHADOW_SELL = "SHADOW_SELL"
    COUNCIL_PICK = "COUNCIL_PICK"


class PaperStatus(str, Enum):
    """Lifecycle of a paper trade."""

    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    EXPIRED_UNRESOLVED = "EXPIRED_UNRESOLVED"


class PaperExitReason(str, Enum):
    """Why a paper trade resolved (WE 2 engine sets this)."""

    SL = "SL"
    TP = "TP"
    TIME_STOP = "TIME_STOP"


# Phase 13 §6 A7.5 (Tracker-Stale-Mini-Step, Session 9): how old a bar may be
# before we treat the *entire* window as stale. Default 120 min = same floor as
# A4 (Provider) and A6.1 (Sampler), but **deliberately a separate constant**:
# A4 protects the *write path* (nichts Totes ins Archiv), A6.1 the *diagnostic*
# (wann ist eine Quelle als tot zu melden), this one the *tracker entry*
# (soll ein Trade überhaupt aufgelöst werden, wenn jede Bar stale ist). Whoever
# loosens one should not silently loosen the others.
_TRACKER_STALE_TOLERANCE_MIN = 120


@dataclass(frozen=True)
class PaperTrade:
    """One virtual (never-ordered) trade — Both-Sides-Shadow or Council-Paper-Call."""

    paper_id: str
    abstain_record_id: str
    variant: PaperVariant
    epic: str
    direction: str  # "BUY" | "SELL"
    created_utc: str
    entry_level: float
    stop_distance: float
    limit_distance: float | None
    time_stop_utc: str
    status: PaperStatus = PaperStatus.OPEN
    resolved_utc: str | None = None
    exit_reason: PaperExitReason | None = None
    exit_level: float | None = None
    pnl_points: float | None = None
    r_multiple: float | None = None
    council_confidence: int | None = None
    lesson: str | None = None
    lesson_extracted: bool = False
    context_json: str = "{}"
    resolution_source: str | None = None  # 'yf'|'ig'|'ig+yf'|'ls'|None (Phase 12 Step 4/D11)

    @classmethod
    def new(
        cls,
        *,
        abstain_record_id: str,
        variant: PaperVariant,
        epic: str,
        direction: str,
        entry_level: float,
        stop_distance: float,
        limit_distance: float | None,
        time_stop_utc: str,
        context_json: str = "{}",
    ) -> "PaperTrade":
        """Build a fresh OPEN paper trade — generates ``paper_id``/``created_utc``."""
        return cls(
            paper_id=str(uuid4()),
            abstain_record_id=abstain_record_id,
            variant=variant,
            epic=epic,
            direction=direction,
            created_utc=_utc_iso_now(),
            entry_level=entry_level,
            stop_distance=stop_distance,
            limit_distance=limit_distance,
            time_stop_utc=time_stop_utc,
            context_json=context_json,
        )

    def to_row(self) -> tuple:
        """Serialize to a plain tuple — column order the SQL schema mirrors exactly."""
        return (
            self.paper_id,
            self.abstain_record_id,
            self.variant.value,
            self.epic,
            self.direction,
            self.created_utc,
            self.entry_level,
            self.stop_distance,
            self.limit_distance,
            self.time_stop_utc,
            self.status.value,
            self.resolved_utc,
            self.exit_reason.value if self.exit_reason is not None else None,
            self.exit_level,
            self.pnl_points,
            self.r_multiple,
            self.council_confidence,
            self.lesson,
            int(self.lesson_extracted),
            self.context_json,
            self.resolution_source,
        )

    @classmethod
    def from_row(cls, row: Sequence) -> "PaperTrade":
        """Inverse of :meth:`to_row` — accepts a tuple or a ``sqlite3.Row``."""
        return cls(
            paper_id=row[0],
            abstain_record_id=row[1],
            variant=PaperVariant(row[2]),
            epic=row[3],
            direction=row[4],
            created_utc=row[5],
            entry_level=row[6],
            stop_distance=row[7],
            limit_distance=row[8],
            time_stop_utc=row[9],
            status=PaperStatus(row[10]),
            resolved_utc=row[11],
            exit_reason=PaperExitReason(row[12]) if row[12] is not None else None,
            exit_level=row[13],
            pnl_points=row[14],
            r_multiple=row[15],
            council_confidence=row[16],
            lesson=row[17],
            lesson_extracted=bool(row[18]),
            context_json=row[19],
            # len() guard: a pre-Phase-12 20-column row (legacy _ROW_COLUMNS shape) has no
            # index 20 at all — read back as None (honest: provenance genuinely unknown for
            # trades resolved before this column existed), never an IndexError.
            resolution_source=row[20] if len(row) > 20 else None,
        )


# --- deterministic core (Step 10 / Block B) -------------------------------


def open_shadow_pair(
    abstain_record_id: str,
    epic: str,
    quote: Mapping[str, float],
    config: Any,
    now_utc: datetime,
) -> list[PaperTrade]:
    """Both-Sides-Shadow-Tracking (V3-D6): SHADOW_BUY from ``quote["ask"]``, SHADOW_SELL
    from ``quote["bid"]``. Pure — no I/O, no randomness beyond ``PaperTrade.new``'s uuid4.

    ``config`` is duck-typed (an ``ExecutionConfig``-shaped object: ``.stop_distance_points``,
    ``.limit_distance_points``, ``.max_hold_minutes``) — the **same fixed v1 constants** the
    real order path sizes against (verified this session: Gate-4 sizing reads these directly,
    not a per-trade computed value), so no ``execution`` import is needed here.
    """
    time_stop_utc = _utc_iso(now_utc + timedelta(minutes=config.max_hold_minutes))
    return [
        PaperTrade.new(
            abstain_record_id=abstain_record_id,
            variant=PaperVariant.SHADOW_BUY,
            epic=epic,
            direction="BUY",
            entry_level=quote["ask"],
            stop_distance=config.stop_distance_points,
            limit_distance=config.limit_distance_points,
            time_stop_utc=time_stop_utc,
        ),
        PaperTrade.new(
            abstain_record_id=abstain_record_id,
            variant=PaperVariant.SHADOW_SELL,
            epic=epic,
            direction="SELL",
            entry_level=quote["bid"],
            stop_distance=config.stop_distance_points,
            limit_distance=config.limit_distance_points,
            time_stop_utc=time_stop_utc,
        ),
    ]


def resolve_paper_trade(
    trade: PaperTrade, bars: Sequence[Mapping[str, Any]]
) -> tuple[PaperExitReason, float] | None:
    """First-touch SL/TP resolution, bars chronologically from ``trade.created_utc``.

    Pure. ``None`` means "cannot resolve yet" (bars don't reach the time-stop) — the
    caller marks ``EXPIRED_UNRESOLVED``, this function never guesses. Same-bar SL+TP touch
    ⇒ conservative SL (checked first, unconditionally). Bar timestamps are compared as
    ISO-8601 strings (lexical == chronological order — the same convention
    ``pnl_resolver._normalise_ts`` relies on); real IG bar-timestamp format compatibility
    is a live-test concern, not verifiable from this deterministic unit.
    """
    relevant = [b for b in bars if b.get("timestamp", "") >= trade.created_utc]
    if not relevant:
        return None

    sign = 1.0 if trade.direction == "BUY" else -1.0
    sl_level = trade.entry_level - sign * trade.stop_distance
    tp_level = (
        trade.entry_level + sign * trade.limit_distance
        if trade.limit_distance is not None
        else None
    )

    last_close_at_or_before_stop: float | None = None
    for bar in relevant:
        ts = bar.get("timestamp", "")
        high, low, close = bar["high"], bar["low"], bar["close"]
        sl_touched = (low <= sl_level) if trade.direction == "BUY" else (high >= sl_level)
        if sl_touched:
            return PaperExitReason.SL, sl_level
        tp_touched = tp_level is not None and (
            (high >= tp_level) if trade.direction == "BUY" else (low <= tp_level)
        )
        if tp_touched:
            return PaperExitReason.TP, tp_level
        if ts <= trade.time_stop_utc:
            last_close_at_or_before_stop = close
        if ts >= trade.time_stop_utc:
            if last_close_at_or_before_stop is not None:
                return PaperExitReason.TIME_STOP, last_close_at_or_before_stop
            return None
    return None  # ran out of bars before reaching the time-stop -> insufficient


def _pnl_points(trade: PaperTrade, exit_level: float) -> float:
    sign = 1.0 if trade.direction == "BUY" else -1.0
    return (exit_level - trade.entry_level) * sign


class PaperDebateCaller:
    """Council-Paper-Call (§10.3): one forced-pick LLM request, never triggers an order.

    Best-effort, never raises (Decision J). ``llm`` is the duck-typed shared
    ``research.LLMClient`` (``.ask_candidate(system, user, schema) -> dict``, the exact
    surface ``phase6_debate.debate.Debate`` already drives). ``prompt_builder`` is
    injected (``debate.prompts.build_paper_pick_prompt`` in real wiring) so this module
    stays free of any ``debate`` import — phase isolation, same convention as
    ``debate_runner`` in ``phase5_execution``.
    """

    def __init__(
        self,
        llm: Any,
        prompt_builder: Callable[[Mapping[str, Any]], tuple[str, str, dict[str, Any]]],
    ) -> None:
        self.llm = llm
        self.prompt_builder = prompt_builder

    def request_pick(self, candidate_digest: Mapping[str, Any]) -> tuple[str, int] | None:
        """Force a BUY/SELL pick. ``None`` (silent, no ``COUNCIL_PICK`` row) on any
        failure or unusable output — direction must be BUY/SELL, confidence an int in
        ``[0, 100]`` (plan §10.3's code-side validation)."""
        try:
            system, user, schema = self.prompt_builder(candidate_digest)
            answer = self.llm.ask_candidate(system, user, schema)
        except Exception as exc:  # noqa: BLE001 — best-effort, never raises (J)
            logger.critical("PaperDebateCaller.request_pick failed: %s", exc)
            return None
        direction = answer.get("direction")
        if direction not in ("BUY", "SELL"):
            return None
        try:
            confidence = int(answer.get("confidence"))
        except (TypeError, ValueError):
            return None
        if not (0 <= confidence <= 100):
            return None
        return direction, confidence


class PaperEngine:
    """Two entry points, both -> Both-Sides-Shadow: the event-triggered
    ``on_debate_abstain`` (V3-D5: ``REASON_DEBATE_ABSTAIN`` only, + optional
    Council-Paper-Call, §10.3) and the time-scheduled ``open_scheduled_pairs`` (Phase 11
    H1, decoupled from the research/debate funnel entirely).

    Best-effort, never raises (Decision J, mirrors ``AbstainLessonSink``). ``quote_fetch``
    is duck-typed (``Callable[[str], Mapping[str, float]]``, one fresh call per trigger —
    the plan's own sanctioned exception to the "no extra IG calls" rule, §10.2: frequency
    is bounded by debate-abstains/day and a stale entry would corrupt every R-multiple).
    The same quote also feeds the optional Council-Paper-Call (no second IG call).
    """

    def __init__(
        self,
        store: Any,
        quote_fetch: Callable[[str], Mapping[str, float]],
        config: Any,
        debate_caller: "PaperDebateCaller | None" = None,
        council_daily_cap: int = 3,
        now_fn: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        epic_filter: Callable[[str], bool] | None = None,
    ) -> None:
        self.store = store
        self.quote_fetch = quote_fetch
        self.config = config
        self.debate_caller = debate_caller  # None (default) -> Council-Paper-Call never fires
        self.council_daily_cap = council_daily_cap
        self.now_fn = now_fn
        # None (default) -> bit-identical (every epic passes). Phase 12 D7/D19: the
        # wiring injects a measurable_universe() ('active' + data_source_status='ok')
        # check so paper trades only open for epics with a verified data source.
        self.epic_filter = epic_filter

    def on_debate_abstain(self, cycle_outcome: Mapping[str, Any], record: AbstainRecord) -> None:
        """Open a Both-Sides-Shadow pair, then (if wired) an optional Council-Pick.
        No-op (silent) unless ``record`` is a real debate-abstain with a known epic —
        the V3-D5 guard doubled here even though the sink already filters on ``reason``
        before calling (§10.4). Also no-op (silent) if ``epic_filter`` rejects the epic
        (D19) — same shape as the reason/epic-None guard, not a separate error path."""
        if record.reason != AbstainReason.REASON_DEBATE_ABSTAIN or record.epic is None:
            return
        if self.epic_filter is not None and not self.epic_filter(record.epic):
            return
        try:
            quote = self.quote_fetch(record.epic)
            pair = open_shadow_pair(record.record_id, record.epic, quote, self.config, self.now_fn())
            for trade in pair:
                self.store.insert(trade)
            self._maybe_council_pick(record, quote)
        except Exception as exc:  # noqa: BLE001 — best-effort, must never crash the cycle
            logger.critical("PaperEngine.on_debate_abstain failed: %s", exc)

    def _maybe_council_pick(self, record: AbstainRecord, quote: Mapping[str, float]) -> None:
        """§10.3: no-op unless a ``debate_caller`` is wired (default off) and the daily
        cap isn't reached yet. A raising ``request_pick`` is already guarded by the
        caller's try/except (``on_debate_abstain``) — nothing here escalates it."""
        if self.debate_caller is None:
            return
        now = self.now_fn()
        now_iso = _utc_iso(now)
        if self.store.count_today(PaperVariant.COUNCIL_PICK, now_iso) >= self.council_daily_cap:
            return
        pick = self.debate_caller.request_pick(
            {"epic": record.epic, "bid": quote.get("bid"), "ask": quote.get("ask")}
        )
        if pick is None:
            return
        direction, confidence = pick
        entry_level = quote["ask"] if direction == "BUY" else quote["bid"]
        time_stop_utc = _utc_iso(now + timedelta(minutes=self.config.max_hold_minutes))
        trade = PaperTrade.new(
            abstain_record_id=record.record_id,
            variant=PaperVariant.COUNCIL_PICK,
            epic=record.epic,
            direction=direction,
            entry_level=entry_level,
            stop_distance=self.config.stop_distance_points,
            limit_distance=self.config.limit_distance_points,
            time_stop_utc=time_stop_utc,
        )
        self.store.insert(dataclasses.replace(trade, council_confidence=confidence))

    def count_lessons_today(self, now_utc: str) -> int:
        """Delegates to the store — used by ``AbstainLessonSink``'s shared reflect cap."""
        return self.store.count_lessons_today(now_utc)

    def open_scheduled_pairs(
        self, epics: Sequence[str], deadline: datetime | None = None
    ) -> None:
        """Phase 11 (H1): open a Both-Sides-Shadow pair per epic on a timer, fully
        decoupled from ``REASON_DEBATE_ABSTAIN`` (two data-weeks of measurement died on
        that coupling — see ``phase10_v3/DATA_WEEK_REVIEW_2026-07-31.md`` §5 H1).

        ``deadline`` (optional, tz-aware — the wiring passes today's daemon
        ``window_close``): if this tick's prospective time-stop (``now +
        config.max_hold_minutes``) would land after it, the **whole tick** is skipped
        (same ``now``/``max_hold_minutes`` for every epic, so either all of them would
        overrun or none would). Without this guard, a pair opened late in the window
        sits unresolved overnight (``PaperTradeTracker`` only ticks during WINDOW) and
        a next-morning gap bar can then register as a "touch" in ``resolve_paper_trade``
        hours after the intended hold ended — a fabricated fill, not a real one. Kept
        as a same-day guard here rather than changing ``resolve_paper_trade`` itself
        (shared with the debate-triggered path — a behaviour change there is its own,
        separately-flagged decision, not folded in silently).

        One shared ``now`` for the whole tick (every epic's pair gets the same
        creation/time-stop timestamp). Each epic is isolated in its own try/except —
        one epic's quote-fetch failure must not skip the rest (mirrors
        ``PaperTradeTracker.tick``'s per-epic ``bar_fetch`` isolation). Uses a synthetic
        ``sched:<uuid>`` ``abstain_record_id`` (no real ``AbstainRecord`` exists for a
        timer tick; the column has no FK, schema-verified) — the ``sched:`` prefix keeps
        these trivially distinguishable from debate-triggered pairs (bare UUIDs) in
        analysis. Deliberately no Council-Paper-Call here — that call is conceptually
        tied to an actual debate-abstain, not a bare timer tick.
        """
        now = self.now_fn()
        if deadline is not None:
            prospective_stop = now + timedelta(minutes=self.config.max_hold_minutes)
            if prospective_stop > deadline:
                return
        for epic in epics:
            if self.epic_filter is not None and not self.epic_filter(epic):
                continue
            try:
                quote = self.quote_fetch(epic)
                pair = open_shadow_pair(f"sched:{uuid4()}", epic, quote, self.config, now)
                for trade in pair:
                    self.store.insert(trade)
            except Exception as exc:  # noqa: BLE001 — isolate one epic's failure (J)
                logger.critical("PaperEngine.open_scheduled_pairs failed for %s: %s", epic, exc)


class PaperTradeTracker:
    """Resolves OPEN paper trades past their time-stop; best-effort, never raises.

    ``bar_fetch`` is duck-typed (``Callable[[str], Sequence[Mapping]]``, one call per
    affected epic per tick) — the wiring layer supplies the real ``get_ohlcv`` call
    (resolution/count decided there, phase-isolation kept: no ``broker_wrapper`` import
    here). ``llm``/``reflect_cap_check`` mirror ``AbstainLessonSink``'s shared-cap reflect
    pattern — one lesson call per **resolved pair**, not per trade. ``budget_ok`` is the
    same shape as ``reflect_cap_check`` deliberately (see ``tick``).
    """

    def __init__(
        self,
        store: Any,
        bar_fetch: Callable[[str], Sequence[Mapping[str, Any]]],
        llm: Any | None = None,
        reflect_cap_check: Callable[[], bool] | None = None,
        now_fn: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        stale_after_minutes: int | None = None,
        budget_ok: Callable[[], bool] | None = None,
        max_fetch_attempts: int | None = None,
        window_ok: Callable[[str, Sequence[Mapping[str, Any]], str, str], bool] | None = None,
    ) -> None:
        self.store = store
        self.bar_fetch = bar_fetch
        self.llm = llm
        self.reflect_cap_check = reflect_cap_check or (lambda: True)
        self.now_fn = now_fn
        self.stale_after_minutes = stale_after_minutes
        self.budget_ok = budget_ok or (lambda: True)
        self.max_fetch_attempts = max_fetch_attempts
        # Phase 13 §6 A3: window_ok is the guard that sits **before** resolve_paper_trade.
        # Default None = bit-identical to the pre-A3 behaviour (the wiring layer supplies
        # the real closure in production; tests can inject any predicate). Argument order
        # is locked: (epic, bars, created_utc, time_stop_utc).
        self.window_ok = window_ok
        # In-memory on purpose: the daemon runs for days at a time, so this is durable
        # enough for its job, and `stale_after_minutes` is the backstop across a restart.
        # A column would cost a migration to bound something already bounded.
        self._fetch_attempts: dict[str, int] = {}

    def tick(self, now_utc: str | None = None) -> None:
        """Resolve every OPEN trade whose ``time_stop_utc`` has passed. Idempotent —
        a trade already moved to RESOLVED/EXPIRED_UNRESOLVED by a prior tick is no
        longer in ``open_trades()``, so a repeat tick is a no-op for it.

        Two guards, both added 2026-08-08 after the first H1 live week exhausted IG's
        account historical-data allowance (`DATA_WEEK_REVIEW_2026-08-07.md` +
        its addendum):

        * ``budget_ok`` — checked **once**, before any fetch, so a tripped budget costs
          zero calls for the whole tick rather than one per epic. Same callable shape as
          ``reflect_cap_check`` on purpose: the wiring layer owns the policy, this module
          stays deterministic and broker-agnostic.
        * ``stale_after_minutes`` — a trade older than this is expired **without** a
          fetch. This is a correctness guard first and a budget guard second:
          ``resolve_paper_trade`` filters bars by ``timestamp >= created_utc`` only, and
          checks the SL touch unconditionally *before* the time-stop bail-out. A
          days-old trade therefore matches against unrelated fresh bars and resolves
          with a fabricated exit — silently poisoning the very substrate WI-2 reads.
          The cut is **wall-clock**, not ``bar_count × bar_minutes``: IG returns the last
          N *existing* bars, which reach back across the overnight gap. Same hazard
          ``PaperEngine.open_scheduled_pairs``' deadline guard already exists to prevent.
        """
        if not self.budget_ok():
            logger.warning("PaperTradeTracker tick skipped: fetch budget exhausted")
            return

        now = now_utc or _utc_iso(self.now_fn())
        stale_before = (
            _utc_iso(_parse_utc(now) - timedelta(minutes=self.stale_after_minutes))
            if self.stale_after_minutes is not None
            else None
        )

        due_by_epic: dict[str, list[PaperTrade]] = {}
        stale = 0
        for trade in self.store.open_trades():
            if trade.time_stop_utc > now:
                continue
            if stale_before is not None and trade.created_utc < stale_before:
                self.store.mark_expired(trade.paper_id, now)
                stale += 1
                continue
            due_by_epic.setdefault(trade.epic, []).append(trade)
        if stale:
            logger.warning(
                "PaperTradeTracker expired %d unresolvable trade(s) older than %s "
                "(no bar fetch attempted)", stale, stale_before
            )

        for epic, trades in due_by_epic.items():
            try:
                bars = self.bar_fetch(epic)
            except Exception as exc:  # noqa: BLE001 — isolate one epic's fetch failure
                logger.critical("PaperTradeTracker bar fetch failed for %s: %s", epic, exc)
                self._charge_failed_attempt(trades, now)
                continue
            self._resolve_group(trades, bars, now)

    def _charge_failed_attempt(self, trades: list[PaperTrade], now: str) -> None:
        """Count one failed resolution attempt against each trade in the group; expire
        at the cap.

        "Failed" covers two cases (P12.5 plan §3/U2, corrected 2026-08-17 — the previous
        docstring here claimed a successful `_resolve_group` always terminates a trade,
        which was never true): a raised fetch error (`bar_fetch` itself raising) **or**
        a fetch that came back without enough bars for `resolve_paper_trade` to decide an
        outcome (`outcome is None`). Both mean "not enough data yet, try again next
        tick" — capping them caps the retries either way.

        Without this, a due trade is re-fetched every cycle until `stale_after_minutes`
        expires it — up to 60 attempts at a 5-minute cadence, all of them against an
        endpoint that just refused the previous one. The cap makes the worst case a
        function of how many trades are due, not of how long the failure lasts.

        Deliberately **not** charged when `budget_ok` stands the tick down: no call was
        made, so no attempt was spent.
        """
        if self.max_fetch_attempts is None:
            return
        for trade in trades:
            attempts = self._fetch_attempts.get(trade.paper_id, 0) + 1
            if attempts >= self.max_fetch_attempts:
                self.store.mark_expired(trade.paper_id, now)
                self._fetch_attempts.pop(trade.paper_id, None)
                logger.warning(
                    "PaperTradeTracker gave up on %s after %d failed fetches",
                    trade.paper_id, attempts,
                )
            else:
                self._fetch_attempts[trade.paper_id] = attempts

    def _resolve_group(
        self, trades: list[PaperTrade], bars: Sequence[Mapping[str, Any]], now: str
    ) -> None:
        resolved_by_record: dict[str, list[PaperTrade]] = {}
        for trade in trades:
            try:
                # Phase 13 §6 A3 + A7.5 (Tracker-Stale-Mini-Step): window_ok-guard
                # sits **before** resolve_paper_trade. A gap *in the middle* of the trade
                # window would otherwise produce a fabricated TIME_STOP exit (P12.5 §4
                # F3): resolve_paper_trade filters bars by `timestamp >= created_utc`
                # and checks the SL touch unconditionally before the time-stop bail-out,
                # so a missing SL-touch bar runs the loop through to the first bar
                # `>= time_stop_utc` and returns TIME_STOP -- indistinguishable from a
                # clean outcome. The guard routes the trade through the existing U2 retry
                # cap (counts as a failed attempt) so it gets another chance on the next
                # tick with more bars in the archive, instead of writing a fabricated
                # resolution.
                #
                # Tracker-Stale check sits *before* window_ok (cheaper, catches a
                # strictly larger case: even a perfectly-covered window is useless if
                # every bar is hours old). Knopf getrennt von A4 (Provider) und A6.1
                # (Sampler) — Schreibpfad / Diagnose / Tracker-Eintritt sind drei
                # unabhängige Stale-Hooks, die nicht dieselbe Konstante teilen müssen.
                newest_ts = ""
                for b in bars:
                    ts = b.get("timestamp", "") or ""
                    if ts > newest_ts:
                        newest_ts = ts
                if newest_ts:
                    newest_age_min = (_parse_utc(now) - _parse_utc(newest_ts)).total_seconds() / 60.0
                    if newest_age_min > _TRACKER_STALE_TOLERANCE_MIN:
                        self._charge_failed_attempt([trade], now)
                        continue
                if self.window_ok is not None and not self.window_ok(
                    trade.epic, bars, trade.created_utc, trade.time_stop_utc
                ):
                    self._charge_failed_attempt([trade], now)
                    continue
                outcome = resolve_paper_trade(trade, bars)
                if outcome is None:
                    # Both of resolve_paper_trade's None-returns mean "not enough bar data yet",
                    # never "no outcome" -- so this is a failed resolution attempt, subject to
                    # the same cap as a raised fetch error, not an immediate write-off
                    # (P12.5 plan §3/U2).
                    self._charge_failed_attempt([trade], now)
                    continue
                exit_reason, exit_level = outcome
                pnl_points = _pnl_points(trade, exit_level)
                r_multiple = pnl_points / trade.stop_distance if trade.stop_distance else 0.0
                # Mirrors resolve_paper_trade's own `timestamp >= trade.created_utc` filter
                # (paper.py — the pure function itself stays untouched, this is a thin
                # wrapper around the same filter, not a second traversal with different
                # semantics) to report which source(s) the bars that actually resolved this
                # trade came from (Phase 12 D11). Deliberately no fallback default (e.g.
                # "yf") for a bar without a `source` key — an honest None ("we don't know
                # the provenance") is auditable; a guessed value would corrupt the SL/TP-
                # by-source breakdown the Phase-12 proof week (Plan §7, Requirement E) reads.
                relevant = [b for b in bars if b.get("timestamp", "") >= trade.created_utc]
                sources = {s for b in relevant if (s := b.get("source"))}
                resolution_source = "+".join(sorted(sources)) if sources else None
                self.store.mark_resolved(
                    trade.paper_id,
                    exit_reason=exit_reason.value,
                    exit_level=exit_level,
                    pnl_points=pnl_points,
                    r_multiple=r_multiple,
                    resolved_utc=now,
                    resolution_source=resolution_source,
                )
                # in-memory copy carrying the resolution (mark_resolved only updates the
                # DB row; `trade` itself is frozen) -- build_paper_lesson_prompt reads
                # exit_reason/pnl_points/r_multiple off the object, not the DB.
                resolved = dataclasses.replace(
                    trade,
                    status=PaperStatus.RESOLVED,
                    resolved_utc=now,
                    exit_reason=exit_reason,
                    exit_level=exit_level,
                    pnl_points=pnl_points,
                    r_multiple=r_multiple,
                    resolution_source=resolution_source,
                )
                resolved_by_record.setdefault(trade.abstain_record_id, []).append(resolved)
            except Exception as exc:  # noqa: BLE001 — isolate one trade's failure (J)
                logger.critical(
                    "PaperTradeTracker resolve failed for %s: %s", trade.paper_id, exc
                )

        if self.llm is None:
            return
        for record_id, pair in resolved_by_record.items():
            if not self.reflect_cap_check():
                continue
            try:
                sibling = pair[1] if len(pair) > 1 else None
                prompt = build_paper_lesson_prompt(pair[0], sibling)
                lesson = validate_abstain_lesson(self.llm.complete(prompt, 20.0))
                for trade in pair:
                    self.store.set_lesson(trade.paper_id, lesson)
            except Exception as exc:  # noqa: BLE001 — best-effort, must never crash the tick
                logger.critical(
                    "PaperTradeTracker reflect failed for record %s: %s", record_id, exc
                )
