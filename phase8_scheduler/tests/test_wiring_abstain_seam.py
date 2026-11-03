"""Phase 17 B-7 (D7) — the abstain seam: ``record_id`` pass-through + classification order.

Two seams are pinned here, both in ``phase8_scheduler/scripts/wiring.py``:

1. **``_observed_abstain_sink`` swallowed the sink's return value.** The wrapper's
   ``on_no_trade`` was typed ``-> None`` and dropped ``inner.on_no_trade(...)`` on the
   floor. The Phase-5 executor reads that return value as ``record_id`` and links it
   into ``decision_context.abstain_record_id`` (``execution/executor.py``) — so the
   link was NULL on **3 669 of 3 669** NO_TRADE rows (measured 2026-10-17, Plan §3 D7).
2. **The wrapper order made the observability event classify the *un-enriched*
   outcome.** ``observed(enrich(sink))`` meant the ``abstain_recorded`` event saw the
   raw cycle outcome while only the persistence saw the enriched one. Phase 17 flips
   it to ``enrich(observed(sink))`` so the enrichment (and, from C-5 on, the
   ``llm_unavailable`` flag) reaches the classification in time.

Both are pure wiring — no broker, no network, no LLM. The sink, the research object
and the classifier are fakes/spies; only the real ``scheduler.observability`` writer
(the JSONL append) and the real ``abstain_lessons`` module are used.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

# scripts/ -> phase8_scheduler/ (so ``from scripts.wiring import ...`` resolves)
_PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(_PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(_PROJECT_DIR))

from scripts.wiring import _enrich_abstain_detail, _observed_abstain_sink  # noqa: E402


class _FakeSink:
    """Minimal :class:`AbstainSink` stand-in — records what it got, returns a record id."""

    def __init__(self, record_id: str | None = "abs-1") -> None:
        self.record_id = record_id
        self.calls: list[dict[str, Any]] = []

    def on_no_trade(self, cycle_outcome: Any) -> str | None:
        self.calls.append(dict(cycle_outcome))
        return self.record_id


class _FakeResearch:
    """The Phase-4 ``Research`` stand-in — only ``last_no_pick_reasoning`` is read."""

    def __init__(self, reasoning: str | None) -> None:
        self.last_no_pick_reasoning = reasoning


def _read_events(path: Path) -> list[dict[str, Any]]:
    """Parse the observability JSONL written by ``scheduler.observability.record_event``."""
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_observed_sink_returns_inner_record_id(tmp_path: Path) -> None:
    """Phase 17 B-7 (D7): the observability wrapper hands the sink's ``record_id``
    back to its caller.

    Pre-B-7 the wrapper was typed ``-> None`` and dropped the value — so the
    executor's ``decision_context.abstain_record_id`` link stayed NULL on every
    NO_TRADE cycle. The wrapper must return exactly what ``inner`` returned
    (``None`` stays ``None`` — the sink may legitimately have nothing to record).
    """
    obs_path = tmp_path / "research_health.jsonl"

    sink = _FakeSink(record_id="abs-42")
    observed = _observed_abstain_sink(sink, str(obs_path))

    returned = observed.on_no_trade(
        {"outcome": "NO_TRADE", "epic": "IX.D.DAX.IFMM.IP", "research_empty": True}
    )

    assert returned == "abs-42", "the sink's record_id must survive the wrapper"
    assert len(sink.calls) == 1, "the inner sink is still called exactly once"

    events = _read_events(obs_path)
    assert len(events) == 1
    assert events[0]["event"] == "abstain_recorded"
    assert events[0]["epic"] == "IX.D.DAX.IFMM.IP"


def test_enriched_outer_wrapper_feeds_observed_classification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Phase 17 B-7 (D7): the enrichment runs **before** the event classifies.

    The composition is ``enrich(observed(sink))`` (the order ``build_scheduler``
    builds since B-7). The classifier therefore sees the *enriched* cycle outcome —
    the research model's own abstain prose instead of Gate 2's generic string.
    Pre-B-7 the order was ``observed(enrich(sink))`` and the classifier saw the
    generic string while only the persistence saw the enriched one.

    The classifier is spied (monkeypatched **before** the wrapper is built — the
    module attribute is imported into the wrapper's closure at construction time),
    so the assertion is on the *input* the classifier receives, not on a side effect.
    """
    import abstain_lessons.classifier as classifier_module

    seen: list[dict[str, Any]] = []
    real_classify = classifier_module.classify_abstain

    def _spy(cycle_outcome: Any) -> Any:
        seen.append(dict(cycle_outcome))
        return real_classify(cycle_outcome)

    monkeypatch.setattr(classifier_module, "classify_abstain", _spy)

    obs_path = tmp_path / "research_health.jsonl"
    sink = _FakeSink(record_id="abs-7")
    research = _FakeResearch(reasoning="Kein Kandidat: DAX im Spread zu weit.")

    # The composition root's order (build_scheduler, Phase 17 B-7).
    chain = _enrich_abstain_detail(
        _observed_abstain_sink(sink, str(obs_path)),
        research,
    )

    returned = chain.on_no_trade(
        {
            "outcome": "NO_TRADE",
            "epic": "IX.D.DAX.IFMM.IP",
            "research_empty": True,
            "detail": "no fresh candidate (research abstained or empty)",
        }
    )

    assert returned == "abs-7", "the record_id must survive the whole chain"
    assert len(seen) == 1, "the classifier is called exactly once per cycle"
    assert seen[0]["detail"] == "Kein Kandidat: DAX im Spread zu weit.", (
        "the classifier must see the ENRICHED detail — pre-B-7 it saw Gate 2's "
        "generic string"
    )
    # The persistence keeps the enriched outcome too (it always did).
    assert sink.calls[0]["detail"] == "Kein Kandidat: DAX im Spread zu weit."
