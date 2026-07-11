"""Paper-trade data model (V3-D6/D7) — WE 1 scope is the model only.

The schema lands now (Migration 005) so ``paper_store.py`` has something typed to
store; the resolution engine (Both-Sides-Shadow-Tracking, bar-based SL/TP/time-stop
resolution, the optional Council-Paper-Call) is explicitly **WE 2** work (plan §10.1
"Modelle + deterministischer Kern" — the "deterministischer Kern" half is not built
here). No AI, no order call, not even demo — this module is data-only.
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
