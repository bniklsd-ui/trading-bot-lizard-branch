"""Phase 16 D2.4 — Promotion-Bridge.

Glues the four Phase-15 Instinct-ECC pieces together:

    SingleShotInstinctExtractor (LLM, best-effort) → DB.insert_instinct(proposed)
        → InstinctValidator (deterministic, code-only) → DB.update_instinct_status
        → promote_eligible (P10/P12 gate) → DB.update_instinct_status(promoted)
        → compile_rules → loaded into ``ExecutionConfig.longterm_rules`` for VETO 5.

The bridge is invoked from the **close-seam** of ``RewardSink`` (Phase 7) via
the new keyword-only ``instinct_hook`` (D2.5). It is **best-effort, never
raises** — a bridge failure is logged ``critical`` (mirrors
``confidence_provider`` discipline, Decision C) and the trade remains CLOSED.
Instincts are bookkeeping, not safety (Hard Rule 3 — root ``CLAUDE.md``).

Lifecycle (Plan §6 D2.4):

- :meth:`InstinctBridge.after_trade_closed(trade_id)` — single-shot on each
  CLOSE; takes the lessons + rewards snapshot from the DB, asks the extractor,
  inserts proposed rows, validates each, updates status. Wrapped in a single
  try/except — never propagates to the trade path.
- :meth:`InstinctBridge.promote()` — called once at scheduler start; iterates
  ``status='validated'`` rows, applies ``promote_eligible``, sets
  ``status='promoted'``. Returns the new promoted instinct ids (caller logs
  them). **T18 (Phase 17):** a promotion takes effect from the next restart —
  the executor reads ``exec_cfg`` once at construction, so a promotion run
  from ``after_trade_closed`` only shows up in ``longterm_rules`` after the
  next ``run_scheduler``-Start.
- :meth:`InstinctBridge.load_rules()` — returns the ``compile_rules`` tuple
  for ``ExecutionConfig.longterm_rules``. Empty tuple when no rows are
  promoted (AK9-Erbe — VETO 5 stays an identity function).

Why all three calls live on one object: a builder that returns ``(reward_sink,
bridge)`` (Phase 8 wiring, Plan §6 D2.6) wires the bridge into the sink in a
single transaction; the scheduler's start path loads ``longterm_rules`` from
the bridge once, and the close-path runs ``after_trade_closed`` + ``promote``
+ ``load_rules`` updates each cycle.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from instinct.compile import compile_rules, instinct_from_row
from instinct.models import Instinct, InstinctConfig
from instinct.promotion import promote_eligible
from instinct.validator import InstinctValidator


logger = logging.getLogger(__name__)


class InstinctBridge:
    """The Promotion-Bridge between extractor + validator + DB + VETO 5.

    Phase 16 D2.4 / Plan §6 D2.4. All public methods are **best-effort**:
    a raise is logged as ``critical`` and swallowed. The bridge owns no
    lifecycle state beyond what it caches on construction (the
    ``extractor`` / ``validator`` / ``db`` references).
    """

    def __init__(
        self,
        db: Any,
        extractor: Any,
        validator: InstinctValidator,
        cfg: InstinctConfig,
        *,
        lessons_n: int = 20,
        rewards_n: int = 20,
        trades_n: int = 500,
    ) -> None:
        """Bind the four collaborators.

        Args:
            db: the Phase-2 ``Database`` (must expose ``get_recent_lessons(n)``,
                ``get_recent_rewards(n)``, ``count_closed_trades()``,
                ``insert_instinct(...)``, ``list_instincts(status=...)``,
                ``update_instinct_status(id, status)``).
            extractor: an :class:`instinct.extractor.InstinctExtractor`
                (LLM-backed, best-effort, never raises). Duck-typed here so the
                bridge module never imports the LLM (Phase-Isolation, mirror
                Phase 7 ``Brain`` Decision F).
            validator: an :class:`instinct.validator.InstinctValidator`
                (deterministic, code-only; ``NoOpValidator`` acceptable in
                tests).
            cfg: the :class:`InstinctConfig` (gates ``enable_instinct_promotion``
                and ``instinct_n_min`` via ``promote_eligible``).
            lessons_n: how many recent lessons to feed the extractor (default
                20, Plan §6 D2.4). ``None`` for "no limit".
            rewards_n: how many recent reward rows to feed the extractor
                (default 20).
            trades_n: how many closed trades the validator should consider for
                evidence/contradiction counting. The validator receives them
                via ``self.db.get_recent_trades(n=trades_n)`` on every
                ``after_trade_closed`` call and counts which of the instinct's
                ``evidence_trade_ids`` / ``contradictions_trade_ids`` resolve to
                real ``trade_outcomes.id`` rows in that window. Default ``500``
                (Plan §6 B-3, D3 Nahtfehler 1 — previously reserved / never
                read, the validator silently fell back to ``[]``).
        """
        self.db = db
        self.extractor = extractor
        self.validator = validator
        self.cfg = cfg
        self.lessons_n = lessons_n
        self.rewards_n = rewards_n
        self.trades_n = trades_n

    # -- close seam --------------------------------------------------------

    def after_trade_closed(self, trade_id: int) -> None:
        """Best-effort instinct extraction on each CLOSE.

        Called from ``RewardSink._on_trade_closed`` via the new
        ``instinct_hook`` keyword. The single ``try/except`` here protects the
        trade path (mirrors Phase 7 ``_observe_confidence``, Decision C):
        bridge failure ⇒ ``logger.critical`` + swallowed.
        """
        try:
            self._extract_and_validate(trade_id)
        except Exception as exc:  # noqa: BLE001 - best-effort, never raises
            logger.critical(
                "instinct.bridge: after_trade_closed failed for trade_id=%s: %s",
                trade_id, exc,
            )

    def _extract_and_validate(self, trade_id: int) -> None:
        """The actual extract → insert(proposed) → validate → update_status path.

        Public method :meth:`after_trade_closed` wraps this in try/except so
        failures never propagate. This private method may raise freely —
        callers that bypass ``after_trade_closed`` must handle their own
        exceptions (used by the test suite to assert failure paths).
        """
        lessons = self.db.get_recent_lessons(n=self.lessons_n)
        rewards = self.db.get_recent_rewards(n=self.rewards_n)
        # Phase 17 B-3 (D3 Nahtfehler 1): pass the trades to the validator so it
        # can count evidence vs. contradictions against real ``trade_outcomes``
        # rows. ``trades_n`` is no longer reserved — it's the validator's view.
        trades = self.db.get_recent_trades(n=self.trades_n)
        result = self.extractor.extract(lessons=lessons, rewards=rewards)
        if not getattr(result, "ok", False):
            logger.info(
                "instinct.bridge: extractor returned ok=False for trade_id=%s: %s",
                trade_id, getattr(result, "error", None),
            )
            return

        for instinct in getattr(result, "instincts", []) or []:
            try:
                row = self._instinct_to_row(instinct)
                row_id = self.db.insert_instinct(row)
                # Validator: deterministic, code-only (no LLM, Hard Rule 3).
                # Phase 17 B-3 (D3 Nahtfehler 2): ``InstinctValidation`` is the
                # frozen dataclass with ``.decision`` (not the old test-only
                # ``._D.value`` shim). Reading ``.value`` here would silently
                # fall back to ``str(decision)`` and break every per-instinct
                # update once the validator struct shape changes.
                decision = self.validator.validate(instinct, trades)
                self.db.update_instinct_status(int(row_id), decision.decision)
            except Exception as exc:  # noqa: BLE001 - per-instinct resilience
                logger.critical(
                    "instinct.bridge: per-instinct failure for trade_id=%s: %s",
                    trade_id, exc,
                )

    @staticmethod
    def _instinct_to_row(instinct: Instinct) -> dict:
        """Convert an :class:`Instinct` to a DB-insert row dict.

        Maps the dataclass onto the :data:`phase2_persistence.persistence.db
        ._INSTINCT_COLUMNS` whitelist (10 columns: ``trigger`` /
        ``domain`` / ``confidence`` / ``evidence_trade_ids_json`` /
        ``contradictions_trade_ids_json`` / ``status`` / ``created_utc`` /
        ``validated_utc`` / ``promoted_utc`` / ``archived_utc``). The two
        ``*_trade_ids`` list fields use the ``_json``-suffixed column names —
        :meth:`phase2_persistence.persistence.db.Database.insert_instinct`
        auto-serialises them via its ``json_fields=`` whitelist.

        Phase 17 B-3 (D3 Nahtfehler 3): keys previously lacked ``_json`` and
        were silently dropped by the column whitelist, leaving the columns
        ``NULL`` on every insert (29/29 rows in the live DB pre-fix).
        """
        return {
            "trigger": instinct.trigger,
            "domain": instinct.domain,
            "confidence": instinct.confidence,
            "evidence_trade_ids_json": list(instinct.evidence_trade_ids),
            "contradictions_trade_ids_json": list(instinct.contradictions_trade_ids),
            "status": instinct.status,
        }

    # -- promote / load ---------------------------------------------------

    def promote(self) -> list[int]:
        """Promote validated rows whose evidence gate is open.

        Called **once at scheduler start** (Plan §6 B-3 / T18): iterating
        ``status='validated'`` rows, asks ``promote_eligible`` (P10/P12 gate)
        which combines ``enable_instinct_promotion`` + ``n_closed >=
        instinct_n_min``, and sets ``status='promoted'`` on the winners.

        **T18:** a promotion takes effect from the next restart — the
        executor reads ``exec_cfg`` once at construction, so even though the
        close-seam re-calls ``promote()`` every cycle, the resulting
        ``longterm_rules`` are not picked up until the next scheduler start.

        Returns the list of newly promoted instinct ids (caller may log them).
        Empty list when the gate stays closed (today: every cycle until
        ``n_closed >= 50``).
        """
        if not self.cfg.enable_instinct_promotion:
            return []
        try:
            rows = self.db.list_instincts(status="validated")
            n_closed = self.db.count_closed_trades()
            # ``promote_eligible`` accepts Instinct objects, not raw dicts —
            # convert via the same helper the compile path uses.
            validated_instincts = [instinct_from_row(row) for row in rows]
            winners = promote_eligible(validated_instincts, n_closed=n_closed, cfg=self.cfg)
            for winner in winners:
                row_id = int(winner.id or 0)
                if row_id <= 0:
                    continue
                self.db.update_instinct_status(row_id, "promoted")
            return [w.id for w in winners if w.id is not None and int(w.id) > 0]
        except Exception as exc:  # noqa: BLE001 - never raises from a bridge call
            logger.critical("instinct.bridge: promote() failed: %s", exc)
            return []

    def load_rules(self) -> tuple[Callable[[dict], bool], ...]:
        """Compile all currently ``promoted`` instincts into a tuple of predicates.

        Returns an empty tuple when no rows are promoted (AK9-Erbe:
        ``longterm_rules == ()`` ⇒ ``test_pre_trade_check_veto5_empty_rules_is_identity``
        stays green). Never raises — failures are logged and yield ``()``.
        """
        try:
            rows = self.db.list_instincts(status="promoted")
            return compile_rules(rows)
        except Exception as exc:  # noqa: BLE001
            logger.critical("instinct.bridge: load_rules() failed: %s", exc)
            return ()
