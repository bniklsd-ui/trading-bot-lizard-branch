"""S2 tests — classify_abstain, table-driven."""

from __future__ import annotations

import pytest

from abstain_lessons.classifier import classify_abstain
from abstain_lessons.models import AbstainReason, AbstainStage

_ALL_REASONS_CASES = [
    ({"error": "boom"}, AbstainReason.REASON_ERROR_FAILCLOSED, AbstainStage.ERROR),
    ({"research_empty": True}, AbstainReason.REASON_NO_CANDIDATES, AbstainStage.RESEARCH_EMPTY),
    ({"failed_gate": "G1"}, AbstainReason.REASON_GATE_TIME_WINDOW, AbstainStage.GATE),
    ({"failed_gate": "G2"}, AbstainReason.REASON_NO_CANDIDATES, AbstainStage.GATE),
    ({"failed_gate": "G3"}, AbstainReason.REASON_GATE_CONSTRAINTS, AbstainStage.GATE),
    ({"failed_gate": "G4"}, AbstainReason.REASON_GATE_SIZING, AbstainStage.GATE),
    ({"failed_gate": "G5"}, AbstainReason.REASON_GATE_DIRECTION, AbstainStage.GATE),
    ({"debate_decision": "ABSTAIN"}, AbstainReason.REASON_DEBATE_ABSTAIN, AbstainStage.DEBATE),
    ({"veto": "spread"}, AbstainReason.REASON_VETO_SPREAD, AbstainStage.VETO),
    ({"veto": "momentum"}, AbstainReason.REASON_VETO_MOMENTUM, AbstainStage.VETO),
    ({"veto": "status_window"}, AbstainReason.REASON_VETO_STATUS_WINDOW, AbstainStage.VETO),
    ({"veto": "position_conflict"}, AbstainReason.REASON_VETO_POSITION_CONFLICT, AbstainStage.VETO),
]


@pytest.mark.parametrize("cycle_outcome, expected_reason, expected_stage", _ALL_REASONS_CASES)
def test_classify_abstain_reasons(cycle_outcome, expected_reason, expected_stage):
    record = classify_abstain(cycle_outcome)
    assert record.reason is expected_reason
    assert record.stage is expected_stage


def test_all_12_reasons_reachable():
    reached = {reason for _, reason, _ in _ALL_REASONS_CASES}
    reached.add(classify_abstain({}).reason)  # REASON_UNCLASSIFIED
    assert reached == set(AbstainReason)


def test_priority_error_beats_veto():
    record = classify_abstain({"error": "boom", "veto": "spread"})
    assert record.reason is AbstainReason.REASON_ERROR_FAILCLOSED


def test_priority_research_empty_beats_failed_gate():
    record = classify_abstain({"research_empty": True, "failed_gate": "G1"})
    assert record.reason is AbstainReason.REASON_NO_CANDIDATES


def test_priority_failed_gate_beats_debate():
    record = classify_abstain({"failed_gate": "G3", "debate_decision": "ABSTAIN"})
    assert record.reason is AbstainReason.REASON_GATE_CONSTRAINTS


def test_priority_debate_beats_veto():
    record = classify_abstain({"debate_decision": "ABSTAIN", "veto": "spread"})
    assert record.reason is AbstainReason.REASON_DEBATE_ABSTAIN


def test_unknown_gate_id_is_unclassified():
    record = classify_abstain({"failed_gate": "G99"})
    assert record.reason is AbstainReason.REASON_UNCLASSIFIED


def test_unknown_veto_id_is_unclassified():
    record = classify_abstain({"veto": "unknown_veto"})
    assert record.reason is AbstainReason.REASON_UNCLASSIFIED


def test_empty_mapping_is_unclassified_never_raises():
    record = classify_abstain({})
    assert record.reason is AbstainReason.REASON_UNCLASSIFIED


def test_epic_passed_through():
    record = classify_abstain({"epic": "IX.D.DAX.IFMM.IP", "veto": "spread"})
    assert record.epic == "IX.D.DAX.IFMM.IP"


def test_epic_none_when_absent():
    record = classify_abstain({"veto": "spread"})
    assert record.epic is None
