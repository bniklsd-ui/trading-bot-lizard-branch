"""S5 — the sink: classify -> persist -> optionally reflect -> optionally paper-trigger.

Connects S1-S4 into one best-effort pipeline step, wired into the Phase-5 executor at
the ``_no_trade`` seam (every NO_TRADE path). Never raises to the caller — a failure
anywhere in the pipeline is logged ``critical`` and swallowed (mirrors the existing
``reward_sink`` guard pattern in ``phase5_execution/execution/executor.py``).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Mapping, Protocol

from abstain_lessons.classifier import classify_abstain
from abstain_lessons.models import AbstainReason, AbstainStage
from abstain_lessons.reflect import AbstainLLM, reflect_abstain
from abstain_lessons.store import AbstainStore

if TYPE_CHECKING:
    # WE 2 (plan §10.2) — duck-typed here (Protocol below), never imported at runtime.
    from typing import Protocol as _Protocol

    class PaperEngine(_Protocol):
        def on_debate_abstain(self, cycle_outcome: Mapping[str, Any], record: Any) -> None: ...
        def count_lessons_today(self, now_utc: str) -> int: ...

logger = logging.getLogger("abstain_lessons.sink")


class AbstainSink(Protocol):
    """The seam the executor calls on every NO_TRADE path.

    Returns the persisted ``record_id`` on success (Phase-10 Block-B needs it to link
    ``decision_context.abstain_record_id``) or ``None`` if classification/persistence
    failed — never raises.
    """

    def on_no_trade(self, cycle_outcome: Mapping[str, Any]) -> str | None: ...


class AbstainLessonSink:
    """Classify -> persist -> (capped, stage-filtered) reflect -> (WE 2) paper-trigger."""

    def __init__(
        self,
        store: AbstainStore,
        llm: AbstainLLM | None = None,
        paper_engine: "PaperEngine | None" = None,
        reflect_stages: frozenset[AbstainStage] = frozenset({AbstainStage.DEBATE}),
        reflect_daily_cap: int = 10,
    ) -> None:
        self.store = store
        self.llm = llm
        self.paper_engine = paper_engine
        self.reflect_stages = reflect_stages
        self.reflect_daily_cap = reflect_daily_cap

    def on_no_trade(self, cycle_outcome: Mapping[str, Any]) -> str | None:
        """Best-effort pipeline step. Never raises. Returns the persisted ``record_id``
        (``None`` on failure) — Block-B's ``context_recorder`` links it into
        ``decision_context.abstain_record_id``."""
        try:
            record = classify_abstain(cycle_outcome)
            self.store.insert(record)

            if record.stage in self.reflect_stages:
                paper_lessons_today = 0
                if self.paper_engine is not None and hasattr(
                    self.paper_engine, "count_lessons_today"
                ):
                    paper_lessons_today = self.paper_engine.count_lessons_today(
                        record.created_utc
                    )
                lessons_today = (
                    self.store.count_lessons_today(record.created_utc) + paper_lessons_today
                )
                if lessons_today < self.reflect_daily_cap:
                    lesson = reflect_abstain(record, self.llm)
                    if lesson is not None:
                        self.store.set_lesson(record.record_id, lesson)

            if (
                record.reason == AbstainReason.REASON_DEBATE_ABSTAIN
                and self.paper_engine is not None
            ):
                self.paper_engine.on_debate_abstain(cycle_outcome, record)
            return record.record_id
        except Exception as exc:  # noqa: BLE001 — the sink must never kill the cycle
            logger.critical("AbstainLessonSink.on_no_trade failed: %s", exc)
            return None
