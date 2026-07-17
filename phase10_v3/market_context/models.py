"""Block B (Step 9) — core data models for the two persistence-reform tables.

Fields mirror ``phase2_persistence/migrations/005_v3_learning.sql``'s
``market_regime_snapshots`` / ``decision_context`` columns exactly. Pure data — no
persistence, no feature-extraction logic, no AI.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence
from uuid import uuid4


def _utc_iso_now() -> str:
    """Current UTC time as an ISO 8601 string with ms precision and Z suffix."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


@dataclass(frozen=True)
class RegimeSnapshot:
    """One deterministic market-regime feature snapshot (observe-only, V3-D4)."""

    snapshot_id: str
    created_utc: str
    epic: str | None
    spread_pct: float | None
    atr_points: float | None
    range_pct: float | None
    time_bucket: str | None
    regime_tag: str | None
    data_source: str  # "ig_bars" | "yfinance" | "quote_only"
    degraded: bool = False
    decision_context_id: str | None = None

    @classmethod
    def new(
        cls,
        *,
        epic: str | None,
        spread_pct: float | None,
        atr_points: float | None,
        range_pct: float | None,
        time_bucket: str | None,
        regime_tag: str | None,
        data_source: str,
        degraded: bool = False,
    ) -> "RegimeSnapshot":
        """Build a fresh snapshot — generates ``snapshot_id``/``created_utc``."""
        return cls(
            snapshot_id=str(uuid4()),
            created_utc=_utc_iso_now(),
            epic=epic,
            spread_pct=spread_pct,
            atr_points=atr_points,
            range_pct=range_pct,
            time_bucket=time_bucket,
            regime_tag=regime_tag,
            data_source=data_source,
            degraded=degraded,
        )

    def to_row(self) -> tuple:
        """Serialize to a plain tuple — column order the SQL schema mirrors exactly."""
        return (
            self.snapshot_id,
            self.created_utc,
            self.epic,
            self.spread_pct,
            self.atr_points,
            self.range_pct,
            self.time_bucket,
            self.regime_tag,
            self.data_source,
            int(self.degraded),
            self.decision_context_id,
        )

    @classmethod
    def from_row(cls, row: Sequence) -> "RegimeSnapshot":
        """Inverse of :meth:`to_row` — accepts a tuple or a ``sqlite3.Row``."""
        return cls(
            snapshot_id=row[0],
            created_utc=row[1],
            epic=row[2],
            spread_pct=row[3],
            atr_points=row[4],
            range_pct=row[5],
            time_bucket=row[6],
            regime_tag=row[7],
            data_source=row[8],
            degraded=bool(row[9]),
            decision_context_id=row[10],
        )


@dataclass(frozen=True)
class DecisionContext:
    """One cycle's decision digest — TRADE, NO_TRADE, or ABORT (Bug-B extension)."""

    context_id: str
    created_utc: str
    epic: str | None
    candidate_json: str | None
    bull_summary: str | None
    bear_summary: str | None
    judge_decision: str | None
    judge_confidence: int | None
    rounds_used: int | None
    veto_results_json: str | None
    gate_results_json: str | None
    outcome: str  # "TRADE" | "NO_TRADE" | "ABORT"
    deal_id: str | None = None
    abstain_record_id: str | None = None

    @classmethod
    def new(
        cls,
        *,
        epic: str | None,
        candidate_json: str | None,
        bull_summary: str | None,
        bear_summary: str | None,
        judge_decision: str | None,
        judge_confidence: int | None,
        rounds_used: int | None,
        veto_results_json: str | None,
        gate_results_json: str | None,
        outcome: str,
        deal_id: str | None = None,
        abstain_record_id: str | None = None,
    ) -> "DecisionContext":
        """Build a fresh context row — generates ``context_id``/``created_utc``."""
        return cls(
            context_id=str(uuid4()),
            created_utc=_utc_iso_now(),
            epic=epic,
            candidate_json=candidate_json,
            bull_summary=bull_summary,
            bear_summary=bear_summary,
            judge_decision=judge_decision,
            judge_confidence=judge_confidence,
            rounds_used=rounds_used,
            veto_results_json=veto_results_json,
            gate_results_json=gate_results_json,
            outcome=outcome,
            deal_id=deal_id,
            abstain_record_id=abstain_record_id,
        )

    def to_row(self) -> tuple:
        """Serialize to a plain tuple — column order the SQL schema mirrors exactly."""
        return (
            self.context_id,
            self.created_utc,
            self.epic,
            self.candidate_json,
            self.bull_summary,
            self.bear_summary,
            self.judge_decision,
            self.judge_confidence,
            self.rounds_used,
            self.veto_results_json,
            self.gate_results_json,
            self.outcome,
            self.deal_id,
            self.abstain_record_id,
        )

    @classmethod
    def from_row(cls, row: Sequence) -> "DecisionContext":
        """Inverse of :meth:`to_row` — accepts a tuple or a ``sqlite3.Row``."""
        return cls(
            context_id=row[0],
            created_utc=row[1],
            epic=row[2],
            candidate_json=row[3],
            bull_summary=row[4],
            bear_summary=row[5],
            judge_decision=row[6],
            judge_confidence=row[7],
            rounds_used=row[8],
            veto_results_json=row[9],
            gate_results_json=row[10],
            outcome=row[11],
            deal_id=row[12],
            abstain_record_id=row[13],
        )
