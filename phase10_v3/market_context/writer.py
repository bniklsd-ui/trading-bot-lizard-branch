"""Block B (Step 9) — ``MarketContextWriter`` + the ``ContextRecorder`` executor seam.

Own-connection SQLite store (same pattern as ``abstain_lessons/store.py`` /
``phase9_universe/universe/store.py``). Migration 005 must already have created both
tables (Block A, ``main``); ``ensure_schema`` is a convenience for tmp-DB tests.
"""

from __future__ import annotations

import dataclasses
import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from market_context.exceptions import MarketContextError
from market_context.models import DecisionContext, RegimeSnapshot
from market_context.regime import compute_regime_features

logger = logging.getLogger("market_context.writer")

_CREATE_DECISION_CONTEXT = """
CREATE TABLE IF NOT EXISTS decision_context (
    context_id          TEXT PRIMARY KEY,
    created_utc         TEXT NOT NULL,
    epic                TEXT,
    candidate_json      TEXT,
    bull_summary        TEXT,
    bear_summary        TEXT,
    judge_decision      TEXT,
    judge_confidence    INTEGER,
    rounds_used         INTEGER,
    veto_results_json   TEXT,
    gate_results_json   TEXT,
    outcome             TEXT,
    deal_id             TEXT,
    abstain_record_id   TEXT
)
"""

_CREATE_MARKET_REGIME_SNAPSHOTS = """
CREATE TABLE IF NOT EXISTS market_regime_snapshots (
    snapshot_id           TEXT PRIMARY KEY,
    created_utc            TEXT NOT NULL,
    epic                   TEXT,
    spread_pct             REAL,
    atr_points              REAL,
    range_pct               REAL,
    time_bucket             TEXT,
    regime_tag              TEXT,
    data_source             TEXT,
    degraded                INTEGER DEFAULT 0,
    decision_context_id     TEXT
)
"""


class MarketContextWriter:
    """Own-connection CRUD for ``decision_context`` + ``market_regime_snapshots``."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        except sqlite3.Error as exc:
            raise MarketContextError(f"cannot open {self.db_path!r}: {exc}") from exc

    def ensure_schema(self) -> None:
        """``CREATE TABLE IF NOT EXISTS`` — convenient for tmp-DB tests; a no-op
        against a DB that already ran migration 005."""
        try:
            self.conn.execute(_CREATE_DECISION_CONTEXT)
            self.conn.execute(_CREATE_MARKET_REGIME_SNAPSHOTS)
            self.conn.commit()
        except sqlite3.Error as exc:
            raise MarketContextError(f"ensure_schema failed: {exc}") from exc

    def insert_decision_context(self, ctx: DecisionContext) -> None:
        try:
            self.conn.execute(
                "INSERT OR IGNORE INTO decision_context "
                "(context_id, created_utc, epic, candidate_json, bull_summary, "
                "bear_summary, judge_decision, judge_confidence, rounds_used, "
                "veto_results_json, gate_results_json, outcome, deal_id, "
                "abstain_record_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ctx.to_row(),
            )
            self.conn.commit()
        except sqlite3.Error as exc:
            raise MarketContextError(f"insert_decision_context failed: {exc}") from exc

    def insert_snapshot(self, snap: RegimeSnapshot) -> None:
        try:
            self.conn.execute(
                "INSERT OR IGNORE INTO market_regime_snapshots "
                "(snapshot_id, created_utc, epic, spread_pct, atr_points, range_pct, "
                "time_bucket, regime_tag, data_source, degraded, decision_context_id) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                snap.to_row(),
            )
            self.conn.commit()
        except sqlite3.Error as exc:
            raise MarketContextError(f"insert_snapshot failed: {exc}") from exc

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "MarketContextWriter":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


def _extract_bull_bear(debate_outcome: Any) -> tuple[str | None, str | None]:
    """Last ``BULL``/``BEAR`` turn's text from ``debate_outcome.transcript`` — the fully
    refined argument after however many rounds ran. ``(None, None)`` if no debate ran or
    the transcript is empty (duck-typed, no ``phase6_debate`` import)."""
    transcript = getattr(debate_outcome, "transcript", None)
    if not transcript:
        return None, None
    bull = next((t.text for t in reversed(transcript) if t.agent == "BULL"), None)
    bear = next((t.text for t in reversed(transcript) if t.agent == "BEAR"), None)
    return bull, bear


class ContextRecorder:
    """The Phase-5 executor seam (Decision A pattern): ``on_decision(...)``, never raises.

    Builds both rows (regime snapshot degraded to quote-only when no ``bars`` are in
    scope — verified this session that VETO 3's momentum bars never leave ``vetos.py``),
    links ``market_regime_snapshots.decision_context_id``, inserts both. ``outcome`` is
    ``"TRADE" | "NO_TRADE" | "ABORT"`` — the ABORT case is a Block-B scope extension
    (Nikinger's call, Bug B this session) beyond the original plan's TRADE/NO_TRADE-only
    scope.
    """

    def __init__(self, writer: MarketContextWriter) -> None:
        self.writer = writer

    def on_decision(
        self,
        *,
        outcome: str,
        epic: str | None,
        candidate: Mapping[str, Any] | None = None,
        spread_pct: float | None = None,
        bars: Sequence[Mapping] | None = None,
        now_utc: datetime | None = None,
        debate_outcome: Any = None,
        gate_results_json: str | None = None,
        veto_results_json: str | None = None,
        deal_id: str | None = None,
        abstain_record_id: str | None = None,
    ) -> None:
        try:
            now = now_utc or datetime.now(timezone.utc)
            bull_summary, bear_summary = _extract_bull_bear(debate_outcome)
            ctx = DecisionContext.new(
                epic=epic,
                candidate_json=json.dumps(candidate) if candidate is not None else None,
                bull_summary=bull_summary,
                bear_summary=bear_summary,
                judge_decision=getattr(debate_outcome, "decision", None),
                judge_confidence=(
                    int(debate_outcome.confidence)
                    if getattr(debate_outcome, "confidence", None) is not None
                    else None
                ),
                rounds_used=getattr(debate_outcome, "rounds_used", None),
                veto_results_json=veto_results_json,
                gate_results_json=gate_results_json,
                outcome=outcome,
                deal_id=deal_id,
                abstain_record_id=abstain_record_id,
            )
            self.writer.insert_decision_context(ctx)

            snapshot = compute_regime_features(bars, spread_pct, now, epic=epic)
            snapshot = dataclasses.replace(snapshot, decision_context_id=ctx.context_id)
            self.writer.insert_snapshot(snapshot)
        except Exception as exc:  # noqa: BLE001 — the recorder must never kill the cycle
            logger.critical("ContextRecorder.on_decision failed: %s", exc)
