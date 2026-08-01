"""S2 — deterministic classifier: raw cycle-outcome dict -> :class:`AbstainRecord`.

Pure function, no LLM, never raises — an unclassifiable input lands fail-closed in
``REASON_UNCLASSIFIED``. The input contract (``cycle_outcome``) is deliberately
spec-fixed (S2), independent of the real executor's field names — the translation
from real gate/veto identifiers (``"time_window"``, ``"spread"``, …) into this
contract's shape happens at the Phase-5 seam (``executor.py``), not here.
"""

from __future__ import annotations

from typing import Any, Mapping

from abstain_lessons.models import AbstainReason, AbstainRecord, AbstainStage

_GATE_REASONS: dict[str, AbstainReason] = {
    "G1": AbstainReason.REASON_GATE_TIME_WINDOW,
    "G2": AbstainReason.REASON_NO_CANDIDATES,
    "G3": AbstainReason.REASON_GATE_CONSTRAINTS,
    "G4": AbstainReason.REASON_GATE_SIZING,
    "G5": AbstainReason.REASON_GATE_DIRECTION,
}

_VETO_REASONS: dict[str, AbstainReason] = {
    "spread": AbstainReason.REASON_VETO_SPREAD,
    "momentum": AbstainReason.REASON_VETO_MOMENTUM,
    "status_window": AbstainReason.REASON_VETO_STATUS_WINDOW,
    "position_conflict": AbstainReason.REASON_VETO_POSITION_CONFLICT,
}


def _reason_from_gate(gate_id: str) -> AbstainReason:
    """Map a ``"G1".."G5"`` gate id to its reason; unknown ids -> UNCLASSIFIED."""
    return _GATE_REASONS.get(gate_id, AbstainReason.REASON_UNCLASSIFIED)


def _reason_from_veto(veto_id: str) -> AbstainReason:
    """Map a veto id to its reason; unknown ids -> UNCLASSIFIED."""
    return _VETO_REASONS.get(veto_id, AbstainReason.REASON_UNCLASSIFIED)


def classify_abstain(cycle_outcome: Mapping[str, Any]) -> AbstainRecord:
    """Classify one NO_TRADE cycle outcome. Never raises.

    Priority order (fixed, S2): ``error`` -> ``research_empty`` -> ``failed_gate`` ->
    ``debate_decision`` -> ``veto`` -> ``REASON_UNCLASSIFIED``. An unmapped
    ``failed_gate``/``veto`` id, or an empty/unrecognized input, falls through to
    ``REASON_UNCLASSIFIED`` (fail-closed, not raised).

    ``detail`` (Phase-10 B4-fix, 2026-07-31): the executor's ``reason`` string — a
    gate/VETO message, or the debate stage's own Judge rationale — is threaded
    through onto every branch. Previously never read here, so every
    ``AbstainRecord.detail`` landed at the model default ``""``
    (phase10_v3/DATA_WEEK_REVIEW_2026-07-31.md §4 B4).
    """
    epic = cycle_outcome.get("epic")
    detail = str(cycle_outcome.get("detail") or "")

    if cycle_outcome.get("error"):
        return AbstainRecord.new(
            epic=epic, stage=AbstainStage.ERROR, reason=AbstainReason.REASON_ERROR_FAILCLOSED,
            detail=detail,
        )
    if cycle_outcome.get("research_empty") is True:
        return AbstainRecord.new(
            epic=epic, stage=AbstainStage.RESEARCH_EMPTY,
            reason=AbstainReason.REASON_NO_CANDIDATES, detail=detail,
        )
    failed_gate = cycle_outcome.get("failed_gate")
    if failed_gate:
        return AbstainRecord.new(
            epic=epic, stage=AbstainStage.GATE, reason=_reason_from_gate(failed_gate),
            detail=detail,
        )
    if cycle_outcome.get("debate_decision") == "ABSTAIN":
        return AbstainRecord.new(
            epic=epic, stage=AbstainStage.DEBATE, reason=AbstainReason.REASON_DEBATE_ABSTAIN,
            detail=detail,
        )
    veto = cycle_outcome.get("veto")
    if veto:
        return AbstainRecord.new(
            epic=epic, stage=AbstainStage.VETO, reason=_reason_from_veto(veto), detail=detail,
        )
    # No signal matched (or an empty mapping) — fail-closed, never raise.
    return AbstainRecord.new(
        epic=epic, stage=AbstainStage.ERROR, reason=AbstainReason.REASON_UNCLASSIFIED,
        detail=detail,
    )
