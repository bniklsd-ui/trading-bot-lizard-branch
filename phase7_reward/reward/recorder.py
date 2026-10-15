"""The reward orchestration — ``RewardSink`` (concept §6 Step 8, Decision A/J).

This is the seam implementation the Phase-5 executor calls (Step 10): two passive,
duck-typed callbacks that turn a trade's open→close lifecycle into the Phase-2
``trade_outcomes`` / ``reward_pts`` / ``trade_lessons`` rows. It owns no broker write
path and references no Gate/VETO — it **cannot** bypass a VETO because it names none.

**Fail-closed, always (Decision J).** Every persistence step is individually wrapped:
a failure logs ``critical`` (the learning bookkeeping deliberately stands out from
``error``) and the cycle continues — a reward/lesson failure is *never* raised into
the close path. The trade is already closed at the broker; reward + lesson are
bookkeeping/learning, not a safety layer. An outer guard makes both callbacks total
(they never raise), mirroring how the seam itself wraps them.

**The in-memory stash (build reconciliation).** ``trade_outcomes`` has no columns for
``spread_at_entry_pct`` / ``debate_confidence`` (they live on ``reward_pts``, written
only at close), so the full process context cannot round-trip through the DB. The sink
therefore stashes the :class:`~reward.models.OpenedTrade` in ``self._opened[deal_id]``
at open and reads it back at close (same sink instance within one executor cycle). The
persisted row (``get_trade_by_deal_id``) is the durable anchor — it supplies the
``trade_id`` PK and the OPEN/CLOSED status for idempotency, and a minimal resolve
context when the stash is cold (e.g. after a restart).

**``on_trade_closed`` order (retry-friendly).** Idempotency guard → ``resolve`` (raises
:class:`~reward.models.PnLUnavailable` **before** the close write, so an unresolved P&L
leaves the trade OPEN and retry-able) → ``update_trade_close`` → score → ``insert_reward``
→ best-effort ``reflect`` + ``insert_lesson``. Idempotency is the OPEN/CLOSED status
(Decision J sanctions "Guard via status OR existing reward"): a second close for an
already-CLOSED deal is skipped, so the score is never doubled.

**The "later pass" — ``reconcile_open_trades`` (live-debug 2026-06-23).** IG's
transaction history can lag a just-closed deal by seconds–minutes, so the in-cycle
``resolve`` can legitimately raise ``PnLUnavailable`` and leave the trade OPEN. The
design promises an idempotent retry "via ``deal_id`` on a later pass"; that pass is
:meth:`reconcile_open_trades`, which re-runs the close for every still-OPEN row (reusing
the exact retained ``ClosedTrade`` within one process, or reconstructing a minimal one
from the persisted row after a restart). It re-uses the same OPEN/CLOSED status guard,
so it never double-scores. The operator ``live_test`` (and a future Phase-8 scheduler)
calls it after a short wait; the in-cycle close stays the fast path.

Reconciliations vs concept §8 (code = source of truth): ``confidence_provider`` is an
**optional, keyword-only** forward-compat hook (it is observe-only — there is no
confidence DB column, so it is invoked + logged, never written, never gates); and
``cfg`` precedes it in the signature. ``veto_trigger_count`` / ``gate_fail_count`` are
left NULL in v1 (not load-bearing for the score).
-- Vermerk 2026-09-03 (Phase 15 Block B Step B5, MiniMax-M3-Exec-Session #7):
Strukturell immer 0 / NULL, weil ein ``reward_pts``-Row per Definition nur
geschrieben wird, NACHDEM ein Trade alle Gates und VETOs passiert hat
(sonst waere er nie geoeffnet worden, siehe Phase-5 ``executor.py`` +
``vetos.py``). Empirischer Beleg (Plan §3 / Phase-15-B-B5, Stand 2026-08-31):
0 von 1902 ``abstain_records`` mit ``stage='veto'`` oder ``stage='gate'`` —
die VETO-/Gate-Information fuer abgelehnte Zyklen lebt in
``decision_context`` (``005_v3_learning.sql:78-92``), nicht in ``reward_pts``.
Die zwei Spalten bleiben im Schema (Migration 002) und koennen befuellt
werden, sobald jemand einen Reward-Score auf eine abgelehnte Candidate-
Zeile zurueckschreiben will — bis dahin ist NULL die korrekte Aussage. No
code change.
``initial_risk`` / ``account`` / ``r_multiple`` are written but only persist once
migration 002 (Step 12) adds the columns — the P2 ``_insert`` whitelist silently
drops them until then.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from reward import pnl_resolver
from reward.models import ClosedTrade, OpenedTrade, RewardConfig

logger = logging.getLogger(__name__)


# P12-Reconcile-Timing (Mini-Session 26, 2026-08-31,
# PHASE12_RECONCILIATION_TIMING_PLAN.md): exponential backoff for unresolved
# trade P&L retries. D1: 15 min -> 30 min -> 1 h -> 4 h -> 24 h cap. D4: WARNING
# (not CRITICAL) after 24 h without resolution (persistent-fail alarm).
_RETRY_BACKOFF_STEPS_S: tuple[int, ...] = (
    15 * 60, 30 * 60, 60 * 60, 4 * 60 * 60, 24 * 60 * 60,
)
_PERSISTENT_FAIL_HOURS = 24


def _parse_iso_safe(s: str | None) -> datetime | None:
    """Parse ISO-8601 string to tz-aware UTC datetime, or None on failure.

    Tolerates the two timestamp shapes the codebase uses: ``...Z`` (UTC suffix,
    SQLite-stored format) and ``+02:00`` (offset suffix, IG-style history rows).
    Returns None for None, '', or any unparseable input — never raises.
    """
    if not s:
        return None
    try:
        normalized = s.replace("Z", "+00:00") if s.endswith("Z") else s
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _next_retry_in_s(
    last_attempt_iso: str | None,
    open_ts_iso: str | None = None,
    now_utc: datetime | None = None,
) -> int:
    """Return seconds until next retry is allowed (D1).

    ``0`` means 'proceed immediately' (no prior attempt, or the interval has passed).
    The retry interval is the largest D1 step that does not exceed the trade's age
    (``now - open_ts``), floored at the first step (15 min) — so a fresh trade is
    retried every 15 min, a 3 h old one hourly, a 30 h old one daily.

    Corrected 2026-10-15 (Phase 16 Session #37): the original walked the ladder
    against ``elapsed since the last attempt`` alone, which always ran to the top —
    every retry waited the full 24 h (measured: all 8 broker-closed v3-run trades
    booked after 24.06–27.22 h). Anchored on ``open_ts`` instead of an attempt
    counter so no schema migration is needed (the plan sketch already passed
    ``open_ts_iso`` and never used it).

    ponytail: age-anchored, not attempt-anchored — a stop-out after the 4 h step
    (~max_hold) waits up to 4 h for its next retry. Upgrade path: anchor on the
    in-memory ``_pending_close[...].closed_at`` (NOT the cold-reconstructed one:
    its ``closed_at`` is ``updated_at``, which every stamp bumps).
    """
    last = _parse_iso_safe(last_attempt_iso)
    if last is None:
        return 0
    now = now_utc if now_utc is not None else datetime.now(timezone.utc)
    opened = _parse_iso_safe(open_ts_iso)
    age = (now - opened).total_seconds() if opened is not None else 0.0
    interval = _RETRY_BACKOFF_STEPS_S[0]
    for step in _RETRY_BACKOFF_STEPS_S:
        if step <= age:
            interval = step
    return max(0, int(interval - (now - last).total_seconds()))


def _hours_open(open_ts_iso: str | None, now_utc: datetime | None = None) -> float | None:
    """Return hours since ``open_ts``, or None if unparseable."""
    opened = _parse_iso_safe(open_ts_iso)
    if opened is None:
        return None
    now = now_utc if now_utc is not None else datetime.now(timezone.utc)
    return (now - opened).total_seconds() / 3600.0

# Process-signal defaults used only when the open context is cold (no stash, e.g. a
# restart): a spread that earns no clean-entry bonus, and no debate signal. The durable
# signals (R-multiple, exit status) still score normally from the resolved P&L + close.
_NO_STASH_SPREAD = 1.0  # 100% — never <= tight_spread_pct
# Code-side default lesson relevance (the Brain produces no number — AI boundary). Not
# load-bearing in v1; the Phase-9 instinct layer is where relevance gets earned.
_DEFAULT_RELEVANCE = 1.0


@dataclass(frozen=True)
class _OpenCtx:
    """Minimal duck-typed open context the resolver needs (``.size`` / levels / risk /
    ``.direction`` for the level-based P&L branch / ``.open_ts`` for the Bug-A
    plausibility guard, Phase-10 V3)."""

    size: float
    intended_open_level: float
    initial_risk: float
    direction: str | None = None
    open_ts: str | None = None


class RewardSink:
    """Orchestrates open/close persistence + scoring + lesson extraction (Decision A/J).

    Satisfies the ``RewardSink`` protocol that Step 10 adds to ``execution/protocols.py``.
    All collaborators are duck-typed and injected; nothing here is AI except the
    delegated ``brain.reflect`` (best-effort).
    """

    def __init__(
        self,
        *,
        db: Any,
        broker: Any,
        scorer: Any,
        brain: Any,
        cfg: RewardConfig,
        confidence_provider: Callable[[], Any] | None = None,
        instinct_hook: Callable[[int], None] | None = None,
    ) -> None:
        """Bind the collaborators.

        Args:
            db: the Phase-2 ``Database`` (CRUD only).
            broker: a read-only broker (``get_trade_history`` only — never order/close).
            scorer: a :class:`~reward.scorer.Scorer`.
            brain: a lesson extractor (``reflect`` — the only AI; best-effort).
            cfg: the reward config.
            confidence_provider: optional observe-only hook invoked best-effort after a
                close; its result is logged, never written, never gates (Decision C).
            instinct_hook: Phase 16 D2: optional callable invoked best-effort after a
                close with the persisted ``trade_outcomes.id`` (int). Wires the
                Promotion-Bridge (Phase 15 C2): extract → validate → promote. Never
                raises — failures log CRITICAL and are swallowed (mirrors
                ``confidence_provider`` discipline, Decision C). Default ``None`` =
                P5 bit-identical + Phase 7 bit-identical + Phase 15 bit-identical.
        """
        self.db = db
        self.broker = broker
        self.scorer = scorer
        self.brain = brain
        self.cfg = cfg
        self.confidence_provider = confidence_provider
        self.instinct_hook = instinct_hook
        self._opened: dict[str, OpenedTrade] = {}
        # Retain the exact ClosedTrade per deal so a later reconcile (after IG history
        # lag clears) retries the *same* close — with its true exit status — not a
        # reconstructed guess. Dropped once the trade reaches CLOSED.
        self._pending_close: dict[str, ClosedTrade] = {}

    # -- open ---------------------------------------------------------------

    def on_trade_opened(self, opened: OpenedTrade) -> None:
        """Persist the decision context and stash it for close-time scoring.

        Best-effort: an insert failure logs ``critical`` and does not raise (Decision J).
        The stash is set regardless so a later close still has the process context.
        """
        self._opened[opened.deal_id] = opened
        try:
            self.db.insert_trade(self._open_record(opened))
        except Exception as exc:  # noqa: BLE001 - fail-closed (J)
            logger.critical(
                "reward: insert_trade failed for deal_id=%s: %s", opened.deal_id, exc
            )

    @staticmethod
    def _open_record(opened: OpenedTrade) -> dict[str, Any]:
        """Map an ``OpenedTrade`` onto a ``trade_outcomes`` insert record.

        ``intended_open_level`` → ``open_level`` (NOT NULL in P2). ``initial_risk`` /
        ``account`` persist only after migration 002 (whitelist drops them until then);
        ``provenance`` only after migration 003 (Phase 8 v1.6, Cause A part 2, same rule).
        """
        return {
            "deal_id": opened.deal_id,
            "deal_reference": opened.deal_reference,
            "epic": opened.epic,
            "direction": opened.direction,
            "size": opened.size,
            "open_level": opened.intended_open_level,
            "currency": opened.currency,
            "open_ts": opened.open_ts,
            "research_confidence": opened.research_confidence,
            "gate_path": opened.gate_path,
            "session_date": opened.session_date,
            "initial_risk": opened.initial_risk,  # migration 002 (Step 12)
            "account": opened.account,  # migration 002 (Step 12)
            # v1.6 (Phase-8 hotfix, Cause A part 2, 2026-07-02): stamp the same tag that
            # already reaches the lesson's market_context_json (see _extract_lesson below)
            # onto the trade row itself, so the SEPARATE recent_trades prompt channel
            # (context_builder.get_recent_trades_for_prompt) can filter on it too.
            "provenance": opened.provenance,  # migration 003 (Phase 8 v1.6)
        }

    # -- close --------------------------------------------------------------

    def on_trade_closed(self, closed: ClosedTrade) -> None:
        """Resolve P&L, close, score, reward, and best-effort extract a lesson.

        Total (never raises — Decision J). See the module docstring for the step order
        and the idempotency contract.
        """
        # Retain for an idempotent later retry (reconcile_open_trades) if the in-cycle
        # resolve can't reach the broker history yet (IG lag). Dropped once CLOSED.
        self._pending_close[closed.deal_id] = closed
        try:
            self._on_trade_closed(closed)
        except Exception as exc:  # noqa: BLE001 - the sink must never kill the cycle (J)
            logger.critical(
                "reward: on_trade_closed crashed for deal_id=%s: %s", closed.deal_id, exc
            )

    def reconcile_open_trades(self, deal_ids: list[str] | None = None) -> list[str]:
        """Re-attempt the close for still-OPEN trades (the idempotent "later pass").

        The in-cycle ``on_trade_closed`` can leave a trade OPEN when ``resolve`` raises
        ``PnLUnavailable`` (IG history lag). This re-runs the close for each OPEN row —
        reusing the exact retained :class:`~reward.models.ClosedTrade` when this same
        sink instance saw the close (the common case: live_test / a long-running
        scheduler), or reconstructing a minimal one from the persisted row when the
        in-memory state is cold (after a restart). It delegates to the guarded
        ``on_trade_closed``, so the OPEN/CLOSED status guard makes it **idempotent** —
        a now-resolvable trade closes + scores exactly once; a second pass is a no-op.

        Best-effort/total: a listing failure logs ``critical`` and returns (never raises,
        Decision J).

        Args:
            deal_ids: if given, only reconcile these deals (e.g. live_test targets just
                the trade it placed, leaving unrelated stale rows untouched); otherwise
                reconcile every OPEN row.

        Returns:
            The deal_ids that reached a non-OPEN status on this pass.
        """
        try:
            rows = self.db.get_open_trades()
        except Exception as exc:  # noqa: BLE001 - never raise into the caller (J)
            logger.critical("reward: reconcile could not list open trades: %s", exc)
            return []

        resolved: list[str] = []
        for row in rows:
            deal_id = row.get("deal_id")
            if not deal_id or (deal_ids is not None and deal_id not in deal_ids):
                continue
            closed = self._pending_close.get(deal_id) or self._reconstruct_closed(row)
            self.on_trade_closed(closed)  # guarded + idempotent via status
            after = self.db.get_trade_by_deal_id(deal_id)
            if after is not None and after.get("status") not in (None, "OPEN"):
                resolved.append(deal_id)
        return resolved

    @staticmethod
    def _reconstruct_closed(row: dict[str, Any]) -> ClosedTrade:
        """Rebuild a minimal ``ClosedTrade`` from a persisted OPEN row (cold reconcile).

        Used only when no in-memory pending close exists (e.g. a restart). The exit
        *type* is not persisted, so default to the conservative ``"TIME_STOP"`` (the
        drift exit earns no clean-exit process bonus); the durable signals (R-multiple,
        the resolved close fact) still score normally from ``get_trade_history``.
        """
        return ClosedTrade(
            deal_reference=row.get("deal_reference") or "",
            deal_id=row.get("deal_id"),
            status="TIME_STOP",
            closed_at=row.get("updated_at") or datetime.now(timezone.utc).isoformat(),
        )

    def _on_trade_closed(self, closed: ClosedTrade) -> None:
        deal_id = closed.deal_id

        # (0) idempotency + trade_id lookup off the durable row.
        row = self.db.get_trade_by_deal_id(deal_id)
        if row is None:
            logger.critical(
                "reward: no open record for deal_id=%s — cannot record close", deal_id
            )
            return
        status = row.get("status")
        if status not in (None, "OPEN"):
            logger.debug("reward: deal_id=%s already processed (status=%s) — skip", deal_id, status)
            self._pending_close.pop(deal_id, None)
            return
        trade_id = row.get("id")
        opened = self._opened.get(deal_id)

        # P12-Reconcile-Timing (Mini-Session 26, D5): backoff-skip if a recent attempt
        # happened within the age-dependent interval. NULL last_attempt_iso => proceed
        # immediately (first attempt). Caps at 24 h (D1).
        last_attempt_iso = row.get("last_resolve_attempt_utc")
        retry_in_s = _next_retry_in_s(last_attempt_iso, row.get("open_ts"))
        if retry_in_s > 0:
            logger.debug(
                "reward: deal_id=%s backoff-skip (retry in %ds)", deal_id, retry_in_s
            )
            return

        # (1) resolve P&L BEFORE closing, so PnLUnavailable leaves the trade OPEN.
        ctx = opened if opened is not None else _OpenCtx(
            size=float(row.get("size") or 0.0),
            intended_open_level=float(row.get("open_level") or 0.0),
            initial_risk=float(row.get("initial_risk") or 0.0),
            direction=row.get("direction"),
            open_ts=row.get("open_ts"),
        )
        try:
            close_level, profit_loss, r_multiple = pnl_resolver.resolve(
                closed, self.broker, ctx, self.cfg
            )
        except Exception as exc:  # noqa: BLE001 - includes PnLUnavailable
            # P12-Reconcile-Timing (D5): pre-claim AFTER resolve() failed (so a
            # successful resolve does not stamp the slot). persistent-fail (D4):
            # WARNING instead of CRITICAL after 24 h without resolution.
            try:
                self.db.update_trade_resolve_attempt(
                    deal_id, datetime.now(timezone.utc).isoformat()
                )
            except Exception as claim_exc:  # noqa: BLE001 - claim failure is best-effort
                logger.debug(
                    "reward: deal_id=%s pre-claim failed: %s", deal_id, claim_exc
                )
            open_ts_iso = row.get("open_ts")
            hours = _hours_open(open_ts_iso)
            if hours is not None and hours > _PERSISTENT_FAIL_HOURS:
                logger.warning(
                    "reward: P&L unresolved for deal_id=%s (%.1fh open): %s — "
                    "persistent fail, investigate",
                    deal_id, hours, exc,
                )
            else:
                logger.critical(
                    "reward: P&L unresolved for deal_id=%s: %s — trade stays OPEN, retry later",
                    deal_id, exc,
                )
            return

        # (2) close the trade row (close fact).
        try:
            self.db.update_trade_close(
                deal_id,
                {
                    "close_level": close_level,
                    "profit_loss": profit_loss,
                    "close_ts": closed.closed_at,
                    "status": "CLOSED",
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.critical(
                "reward: update_trade_close failed for deal_id=%s: %s — abort scoring",
                deal_id, exc,
            )
            return

        # The close fact is durable now → no resolve-retry is owed for this deal.
        self._pending_close.pop(deal_id, None)

        # (3)+(4) score and write the reward.
        spread = opened.spread_at_entry_pct if opened is not None else _NO_STASH_SPREAD
        debate_conf = opened.debate_confidence if opened is not None else None
        reward = None
        try:
            score_before = self.db.get_current_score()
            reward = self.scorer.score(
                r_multiple=r_multiple,
                status=closed.status,
                spread_at_entry_pct=spread,
                debate_confidence=debate_conf,
                score_before=score_before,
            )
            self.db.insert_reward(trade_id, self._reward_record(reward, profit_loss, spread, debate_conf))
        except Exception as exc:  # noqa: BLE001
            logger.critical(
                "reward: scoring/insert_reward failed for deal_id=%s: %s "
                "(trade stays CLOSED; reward bookkeeping lost — manual retry)",
                deal_id, exc,
            )

        # (5) best-effort lesson (the only AI; decoupled from the close-critical path).
        if reward is not None:
            self._extract_lesson(closed, reward, row, opened, trade_id, spread)

        # observe-only confidence (forward-compat; never gates — Decision C).
        self._observe_confidence(deal_id)

        # Phase 16 D2: best-effort instinct extraction (Phase-15 Promotion-Bridge).
        # Never raises — the close path stays safe (mirrors ``confidence_provider``).
        # Trade stays CLOSED; instinct bookkeeping is a learning signal, not safety.
        if self.instinct_hook is not None and trade_id is not None:
            try:
                self.instinct_hook(int(trade_id))
            except Exception as exc:  # noqa: BLE001
                logger.critical(
                    "reward: instinct_hook raised for deal_id=%s: %s",
                    deal_id, exc,
                )

    @staticmethod
    def _reward_record(
        reward: Any, profit_loss: float, spread: float, debate_conf: float | None
    ) -> dict[str, Any]:
        """Map a ``RewardResult`` onto a ``reward_pts`` insert record.

        ``outcome_delta`` / ``process_delta`` → ``outcome_score_delta`` /
        ``process_score_delta``. ``r_multiple`` persists only after migration 002.
        """
        return {
            "outcome_score_delta": reward.outcome_delta,
            "process_score_delta": reward.process_delta,
            "score_after": reward.score_after,
            "win_loss": reward.win_loss,
            "pnl_raw": profit_loss,
            "r_multiple": reward.r_multiple,  # migration 002 (Step 12)
            "debate_confidence": debate_conf,
            "spread_at_entry_pct": spread,
        }

    def _extract_lesson(
        self,
        closed: ClosedTrade,
        reward: Any,
        row: dict[str, Any],
        opened: OpenedTrade | None,
        trade_id: int,
        spread: float,
    ) -> None:
        """Run the best-effort Haiku ``reflect`` and persist the lesson if any (E/J)."""
        # v1.5 (Phase-8 hotfix Step 4 A, 2026-07-01): stamp the trade's provenance into the
        # lesson's market_context so the P4 research prompt can exclude verification-trade
        # lessons (which describe the test harness, not a market decision). It rides inside
        # the existing free-form ``market_context_json`` blob → **no schema change**. The tag
        # comes from the stashed ``OpenedTrade.provenance`` (set at open by the executor seam
        # from the candidate's seed marker). On a cold reconcile after a restart the stash is
        # gone (``opened is None``) → ``"unknown"``: kept by the read-path tag clause, then
        # caught by its hold-time/date fallbacks. Provenance is display/prompt-only — it never
        # feeds the reward/score math below (root rule 3).
        market_context = {
            "epic": opened.epic if opened is not None else row.get("epic"),
            "direction": opened.direction if opened is not None else row.get("direction"),
            "status": closed.status,
            "spread_at_entry_pct": spread,
            "r_multiple": reward.r_multiple,
            "win_loss": reward.win_loss,
            "session_date": opened.session_date if opened is not None else row.get("session_date"),
            "provenance": opened.provenance if opened is not None else "unknown",
        }
        try:
            lesson = self.brain.reflect(closed, reward, market_context)
        except Exception as exc:  # noqa: BLE001 - the real Brain never raises; guard anyway
            logger.critical("reward: brain.reflect raised for deal_id=%s: %s", closed.deal_id, exc)
            return
        if not getattr(lesson, "ok", False) or not getattr(lesson, "lesson_text", None):
            logger.debug("reward: no lesson for deal_id=%s (%s)", closed.deal_id, getattr(lesson, "error", None))
            return
        try:
            self.db.insert_lesson(
                trade_id,
                {
                    "lesson_text": lesson.lesson_text,
                    "market_context_json": lesson.market_context,
                    "relevance_score": _DEFAULT_RELEVANCE,
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.critical("reward: insert_lesson failed for deal_id=%s: %s", closed.deal_id, exc)

    def _observe_confidence(self, deal_id: str) -> None:
        """Invoke the optional observe-only confidence hook (best-effort; never gates)."""
        if self.confidence_provider is None:
            return
        try:
            report = self.confidence_provider()
            logger.info("reward: confidence (observe-only) after deal_id=%s: %s", deal_id, report)
        except Exception as exc:  # noqa: BLE001
            logger.critical("reward: confidence_provider raised for deal_id=%s: %s", deal_id, exc)
