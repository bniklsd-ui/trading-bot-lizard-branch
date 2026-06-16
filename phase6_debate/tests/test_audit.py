"""Tests for ``debate.audit`` (Module 7) — the forward-compatible JSON audit.

Mocked, no network. The clock is frozen via ``debate.timeutil._utcnow`` so the
record ``ts`` is deterministic; the filesystem stays under ``tmp_path``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from debate import timeutil
from debate.audit import write_debate
from debate.models import AgentTurn, DebateContext, DebateOutcome

FROZEN_TS = "2026-06-16T09:30:00.000Z"


@pytest.fixture(autouse=True)
def _freeze_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Freeze the audit clock so ``ts`` is deterministic across the suite."""
    monkeypatch.setattr(
        timeutil,
        "_utcnow",
        lambda: datetime(2026, 6, 16, 9, 30, 0, 0, tzinfo=timezone.utc),
    )


def _make_outcome(**overrides: object) -> DebateOutcome:
    """A TRADE outcome with a small Bull/Bear/Judge transcript + token summary."""
    usage = {
        "input_tokens": 100,
        "output_tokens": 20,
        "cache_read_input_tokens": 80,
        "cache_creation_input_tokens": 0,
        "est_cost_usd": 0.001,
        "est_cost_eur": 0.0009,
    }
    transcript = (
        AgentTurn(round=1, agent="BULL", model="m-bull", text="long", usage=usage),
        AgentTurn(round=1, agent="BEAR", model="m-bear", text="short", usage=usage),
        AgentTurn(round=1, agent="JUDGE", model="m-judge", text="verdict", usage=usage),
    )
    token_summary = {
        "input_tokens": 300,
        "output_tokens": 60,
        "cache_read_input_tokens": 240,
        "cache_creation_input_tokens": 0,
        "est_cost_usd": 0.003,
        "est_cost_eur": 0.0027,
    }
    kwargs = dict(
        decision="TRADE",
        direction="SELL",
        confidence=71.0,
        rationale="bears won on the fresh spread + downward bars",
        rounds_used=1,
        transcript=transcript,
        token_summary=token_summary,
    )
    kwargs.update(overrides)
    return DebateOutcome(**kwargs)  # type: ignore[arg-type]


def _make_context(**overrides: object) -> DebateContext:
    kwargs = dict(
        epic="IX.D.DAX.IFMM.IP",
        seed_direction="BUY",
        seed_reasoning="seed: bullish breakout",
        seed_confidence=62.0,
        spread_pct=0.03,
        market_status="TRADEABLE",
        recent_bars_summary="18000.0 → 17980.0 (-0.11%)",
        drift_at_pick=0.42,
        score_at_pick=58.0,
        generated_at="2026-06-16T09:00:00.000Z",
    )
    kwargs.update(overrides)
    return DebateContext(**kwargs)  # type: ignore[arg-type]


def test_record_schema_complete_with_p9_mapping_keys() -> None:
    """Every top-level key, the regime_snapshot block, transcript, and token_summary."""
    rec = write_debate(_make_outcome(), _make_context(), None)

    assert rec["ts"] == FROZEN_TS
    assert rec["epic"] == "IX.D.DAX.IFMM.IP"
    assert rec["seed_direction"] == "BUY"
    assert rec["final_decision"] == "TRADE"
    assert rec["final_direction"] == "SELL"  # reversed from the seed — Decision B
    assert rec["confidence"] == 71.0  # advisory only — present but not a gate
    assert rec["rounds_used"] == 1
    assert rec["rationale"]

    regime = rec["regime_snapshot"]  # → P9 market_regime_snapshots
    assert set(regime) == {
        "spread_pct",
        "market_status",
        "drift_at_pick",
        "score_at_pick",
        "recent_bars_summary",
    }
    assert regime["spread_pct"] == 0.03
    assert regime["market_status"] == "TRADEABLE"

    transcript = rec["transcript"]  # → P9 decision_context
    assert isinstance(transcript, list) and len(transcript) == 3
    assert set(transcript[0]) == {"round", "agent", "model", "text", "usage"}
    assert [t["agent"] for t in transcript] == ["BULL", "BEAR", "JUDGE"]

    assert set(rec["token_summary"]) == {
        "input_tokens",
        "output_tokens",
        "cache_read_input_tokens",
        "cache_creation_input_tokens",
        "est_cost_usd",
        "est_cost_eur",
    }


def test_abstain_record_carries_null_direction() -> None:
    """An ABSTAIN outcome serialises ``final_direction: null`` (JSON-clean)."""
    outcome = _make_outcome(decision="ABSTAIN", direction=None, rounds_used=0)
    path = None
    rec = write_debate(outcome, _make_context(), path)
    assert rec["final_decision"] == "ABSTAIN"
    assert rec["final_direction"] is None
    # round-trips through JSON as a literal null
    assert json.loads(json.dumps(rec))["final_direction"] is None


def test_write_is_atomic_and_leaves_no_temp_file(tmp_path: Path) -> None:
    """A write yields a valid JSON array and leaves no leftover temp file."""
    path = tmp_path / "debate_log.json"
    write_debate(_make_outcome(), _make_context(), str(path))

    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, list) and len(data) == 1
    assert data[0]["ts"] == FROZEN_TS
    # os.replace path: no sibling temp artifacts survive.
    leftovers = [p.name for p in tmp_path.iterdir() if p.name != "debate_log.json"]
    assert leftovers == []


def test_missing_file_is_created_with_one_record(tmp_path: Path) -> None:
    """No pre-existing file → the log is created with exactly one record."""
    path = tmp_path / "nested" / "debate_log.json"
    assert not path.exists()
    write_debate(_make_outcome(), _make_context(), str(path))
    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data) == 1 and data[0]["epic"] == "IX.D.DAX.IFMM.IP"


def test_corrupt_file_starts_fresh_with_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A non-JSON file → logged warning + a fresh single-record array, no crash."""
    path = tmp_path / "debate_log.json"
    path.write_text("}{ not json at all", encoding="utf-8")

    with caplog.at_level("WARNING"):
        write_debate(_make_outcome(), _make_context(), str(path))

    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert any("starting fresh" in m for m in caplog.messages)


def test_non_array_file_starts_fresh(tmp_path: Path) -> None:
    """A well-formed-but-non-list JSON file is treated as empty (not appended into)."""
    path = tmp_path / "debate_log.json"
    path.write_text(json.dumps({"unexpected": "object"}), encoding="utf-8")
    write_debate(_make_outcome(), _make_context(), str(path))
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, list) and len(data) == 1


def test_path_none_does_not_write(tmp_path: Path) -> None:
    """``path=None`` returns the record and touches the filesystem not at all."""
    rec = write_debate(_make_outcome(), _make_context(), None)
    assert rec["epic"] == "IX.D.DAX.IFMM.IP"
    assert list(tmp_path.iterdir()) == []  # nothing created anywhere we control


def test_append_preserves_prior_records(tmp_path: Path) -> None:
    """A second write appends; the first record stays intact and ordered first."""
    path = tmp_path / "debate_log.json"
    write_debate(_make_outcome(direction="SELL"), _make_context(), str(path))
    write_debate(_make_outcome(direction="BUY"), _make_context(), str(path))

    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data) == 2
    assert data[0]["final_direction"] == "SELL"
    assert data[1]["final_direction"] == "BUY"
