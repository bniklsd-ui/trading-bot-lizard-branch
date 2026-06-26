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
left NULL in v1 (not load-bearing for the score). ``initial_risk`` / ``account`` /
``r_multiple`` are written but only persist once migration 002 (Step 12) adds the
columns — the P2 ``_insert`` whitelist silently drops them until then.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from reward import pnl_resolver
from reward.models import ClosedTrade, OpenedTrade, RewardConfig

logger = logging.getLogger(__name__)

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
    ``.direction`` for the level-based P&L branch)."""

    size: float
    intended_open_level: float
    initial_risk: float
    direction: str | None = None


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
        """
        self.db = db
        self.broker = broker
        self.scorer = scorer
        self.brain = brain
        self.cfg = cfg
        self.confidence_provider = confidence_provider
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
        ``account`` persist only after migration 002 (whitelist drops them until then).
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

        # (1) resolve P&L BEFORE closing, so PnLUnavailable leaves the trade OPEN.
        ctx = opened if opened is not None else _OpenCtx(
            size=float(row.get("size") or 0.0),
            intended_open_level=float(row.get("open_level") or 0.0),
            initial_risk=float(row.get("initial_risk") or 0.0),
            direction=row.get("direction"),
        )
        try:
            close_level, profit_loss, r_multiple = pnl_resolver.resolve(
                closed, self.broker, ctx, self.cfg
            )
        except Exception as exc:  # noqa: BLE001 - includes PnLUnavailable
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
        market_context = {
            "epic": opened.epic if opened is not None else row.get("epic"),
            "direction": opened.direction if opened is not None else row.get("direction"),
            "status": closed.status,
            "spread_at_entry_pct": spread,
            "r_multiple": reward.r_multiple,
            "win_loss": reward.win_loss,
            "session_date": opened.session_date if opened is not None else row.get("session_date"),
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
