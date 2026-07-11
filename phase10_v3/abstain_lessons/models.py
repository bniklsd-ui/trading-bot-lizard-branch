"""S1 — core data models + the abstain-reason taxonomy.

Foundation for the classifier (S2), store (S3), and reflect (S4) modules. Pure
data — no persistence, no classification logic, no AI.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Sequence
from uuid import uuid4


def _utc_iso_now() -> str:
    """Current UTC time as an ISO 8601 string with ms precision and Z suffix."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


class AbstainStage(str, Enum):
    """Which stage of the execution cycle produced a NO_TRADE outcome."""

    RESEARCH_EMPTY = "research_empty"
    GATE = "gate"
    VETO = "veto"
    DEBATE = "debate"
    ERROR = "error"


class AbstainReason(str, Enum):
    """The 12 reasons a cycle can end in NO_TRADE (S2's classification output)."""

    REASON_NO_CANDIDATES = "reason_no_candidates"
    REASON_GATE_TIME_WINDOW = "reason_gate_time_window"
    REASON_GATE_CONSTRAINTS = "reason_gate_constraints"
    REASON_GATE_SIZING = "reason_gate_sizing"
    REASON_GATE_DIRECTION = "reason_gate_direction"
    REASON_VETO_SPREAD = "reason_veto_spread"
    REASON_VETO_MOMENTUM = "reason_veto_momentum"
    REASON_VETO_STATUS_WINDOW = "reason_veto_status_window"
    REASON_VETO_POSITION_CONFLICT = "reason_veto_position_conflict"
    REASON_DEBATE_ABSTAIN = "reason_debate_abstain"
    REASON_ERROR_FAILCLOSED = "reason_error_failclosed"
    REASON_UNCLASSIFIED = "reason_unclassified"


@dataclass(frozen=True)
class AbstainRecord:
    """One classified NO_TRADE cycle. Frozen — mutate via a new instance only."""

    record_id: str
    created_utc: str
    epic: str | None
    stage: AbstainStage
    reason: AbstainReason
    detail: str = ""
    context_json: str = "{}"
    lesson: str | None = None
    lesson_extracted: bool = False

    @classmethod
    def new(
        cls,
        *,
        epic: str | None,
        stage: AbstainStage,
        reason: AbstainReason,
        detail: str = "",
        context_json: str = "{}",
    ) -> "AbstainRecord":
        """Build a fresh record — generates ``record_id``/``created_utc``."""
        return cls(
            record_id=str(uuid4()),
            created_utc=_utc_iso_now(),
            epic=epic,
            stage=stage,
            reason=reason,
            detail=detail,
            context_json=context_json,
        )

    def to_row(self) -> tuple:
        """Serialize to a plain tuple — column order the SQL schema mirrors exactly."""
        return (
            self.record_id,
            self.created_utc,
            self.epic,
            self.stage.value,
            self.reason.value,
            self.detail,
            self.context_json,
            self.lesson,
            int(self.lesson_extracted),
        )

    @classmethod
    def from_row(cls, row: Sequence) -> "AbstainRecord":
        """Inverse of :meth:`to_row` — accepts a tuple or a ``sqlite3.Row``."""
        return cls(
            record_id=row[0],
            created_utc=row[1],
            epic=row[2],
            stage=AbstainStage(row[3]),
            reason=AbstainReason(row[4]),
            detail=row[5],
            context_json=row[6],
            lesson=row[7],
            lesson_extracted=bool(row[8]),
        )
