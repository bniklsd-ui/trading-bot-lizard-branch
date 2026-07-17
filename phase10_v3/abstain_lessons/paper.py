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
    """Debate-abstain trigger (V3-D5: ``REASON_DEBATE_ABSTAIN`` only) -> Both-Sides-Shadow
    (+ optional Council-Paper-Call, §10.3).

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
    ) -> None:
        self.store = store
        self.quote_fetch = quote_fetch
        self.config = config
        self.debate_caller = debate_caller  # None (default) -> Council-Paper-Call never fires
        self.council_daily_cap = council_daily_cap
        self.now_fn = now_fn

    def on_debate_abstain(self, cycle_outcome: Mapping[str, Any], record: AbstainRecord) -> None:
        """Open a Both-Sides-Shadow pair, then (if wired) an optional Council-Pick.
        No-op (silent) unless ``record`` is a real debate-abstain with a known epic —
        the V3-D5 guard doubled here even though the sink already filters on ``reason``
        before calling (§10.4)."""
        if record.reason != AbstainReason.REASON_DEBATE_ABSTAIN or record.epic is None:
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


class PaperTradeTracker:
    """Resolves OPEN paper trades past their time-stop; best-effort, never raises.

    ``bar_fetch`` is duck-typed (``Callable[[str], Sequence[Mapping]]``, one call per
    affected epic per tick) — the wiring layer supplies the real ``get_ohlcv`` call
    (resolution/count decided there, phase-isolation kept: no ``broker_wrapper`` import
    here). ``llm``/``reflect_cap_check`` mirror ``AbstainLessonSink``'s shared-cap reflect
    pattern — one lesson call per **resolved pair**, not per trade.
    """

    def __init__(
        self,
        store: Any,
        bar_fetch: Callable[[str], Sequence[Mapping[str, Any]]],
        llm: Any | None = None,
        reflect_cap_check: Callable[[], bool] | None = None,
        now_fn: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self.store = store
        self.bar_fetch = bar_fetch
        self.llm = llm
        self.reflect_cap_check = reflect_cap_check or (lambda: True)
        self.now_fn = now_fn

    def tick(self, now_utc: str | None = None) -> None:
        """Resolve every OPEN trade whose ``time_stop_utc`` has passed. Idempotent —
        a trade already moved to RESOLVED/EXPIRED_UNRESOLVED by a prior tick is no
        longer in ``open_trades()``, so a repeat tick is a no-op for it."""
        now = now_utc or _utc_iso(self.now_fn())
        due_by_epic: dict[str, list[PaperTrade]] = {}
        for trade in self.store.open_trades():
            if trade.time_stop_utc <= now:
                due_by_epic.setdefault(trade.epic, []).append(trade)

        for epic, trades in due_by_epic.items():
            try:
                bars = self.bar_fetch(epic)
            except Exception as exc:  # noqa: BLE001 — isolate one epic's fetch failure
                logger.critical("PaperTradeTracker bar fetch failed for %s: %s", epic, exc)
                continue
            self._resolve_group(trades, bars, now)

    def _resolve_group(
        self, trades: list[PaperTrade], bars: Sequence[Mapping[str, Any]], now: str
    ) -> None:
        resolved_by_record: dict[str, list[PaperTrade]] = {}
        for trade in trades:
            try:
                outcome = resolve_paper_trade(trade, bars)
                if outcome is None:
                    self.store.mark_expired(trade.paper_id, now)
                    continue
                exit_reason, exit_level = outcome
                pnl_points = _pnl_points(trade, exit_level)
                r_multiple = pnl_points / trade.stop_distance if trade.stop_distance else 0.0
                self.store.mark_resolved(
                    trade.paper_id,
                    exit_reason=exit_reason.value,
                    exit_level=exit_level,
                    pnl_points=pnl_points,
                    r_multiple=r_multiple,
                    resolved_utc=now,
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
