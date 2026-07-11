"""S1 tests — models.py (AbstainStage/AbstainReason/AbstainRecord)."""

from __future__ import annotations

import re
from dataclasses import FrozenInstanceError

import pytest

from abstain_lessons.models import AbstainReason, AbstainRecord, AbstainStage

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")


def test_construction_with_all_fields():
    record = AbstainRecord(
        record_id="r1",
        created_utc="2026-07-11T09:00:00.000Z",
        epic="IX.D.DAX.IFMM.IP",
        stage=AbstainStage.GATE,
        reason=AbstainReason.REASON_GATE_TIME_WINDOW,
        detail="outside window",
        context_json='{"k": 1}',
        lesson="a lesson",
        lesson_extracted=True,
    )
    assert record.record_id == "r1"
    assert record.epic == "IX.D.DAX.IFMM.IP"
    assert record.stage is AbstainStage.GATE
    assert record.reason is AbstainReason.REASON_GATE_TIME_WINDOW
    assert record.lesson == "a lesson"
    assert record.lesson_extracted is True


def test_frozen_mutation_raises():
    record = AbstainRecord.new(
        epic=None, stage=AbstainStage.ERROR, reason=AbstainReason.REASON_ERROR_FAILCLOSED
    )
    with pytest.raises(FrozenInstanceError):
        record.lesson = "not allowed"  # type: ignore[misc]


def test_abstain_reason_has_exactly_12_values():
    assert len(list(AbstainReason)) == 12


def test_new_defaults_and_plausible_generated_fields():
    record = AbstainRecord.new(
        epic="IX.D.DAX.IFMM.IP",
        stage=AbstainStage.DEBATE,
        reason=AbstainReason.REASON_DEBATE_ABSTAIN,
    )
    assert record.lesson is None
    assert record.lesson_extracted is False
    assert _UUID_RE.match(record.record_id)
    assert _ISO_RE.match(record.created_utc)


def test_to_row_from_row_roundtrip():
    record = AbstainRecord.new(
        epic="IX.D.DAX.IFMM.IP",
        stage=AbstainStage.VETO,
        reason=AbstainReason.REASON_VETO_SPREAD,
        detail="spread too wide",
        context_json='{"spread_pct": 1.2}',
    )
    roundtripped = AbstainRecord.from_row(record.to_row())
    assert roundtripped == record
