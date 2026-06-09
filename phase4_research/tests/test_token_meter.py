"""Tests for the token / cost meter (Step 5) — pure, no network, no real usage.

The ``usage`` object is duck-typed, so these tests use a tiny local
:class:`_Usage` stand-in rather than importing the Anthropic SDK.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from research import timeutil, token_meter
from research.models import ResearchConfig


@dataclass
class _Usage:
    """Duck-typed stand-in for an Anthropic ``usage`` object."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int | None = None
    cache_read_input_tokens: int | None = None


def test_estimate_cost_known_model_usd_and_eur() -> None:
    config = ResearchConfig(usd_to_eur=0.9)
    # Sonnet 4.6 pricing: (3.0 in, 15.0 out) USD/Mtok.
    usage = _Usage(input_tokens=1_000_000, output_tokens=1_000_000)

    usd, eur = token_meter.estimate_cost(usage, "claude-sonnet-4-6", config)

    assert usd == 18.0  # 1M*3 + 1M*15 = 18 USD
    assert eur == 18.0 * 0.9


def test_estimate_cost_counts_cache_fields() -> None:
    config = ResearchConfig()
    # input billed full, cache_read at 0.1x, cache_write at 1.25x of the in-rate.
    usage = _Usage(
        input_tokens=1_000_000,
        output_tokens=0,
        cache_creation_input_tokens=1_000_000,
        cache_read_input_tokens=1_000_000,
    )
    usd, _ = token_meter.estimate_cost(usage, "claude-sonnet-4-6", config)
    # 3 + (3*1.25) + (3*0.1) = 3 + 3.75 + 0.3 = 7.05
    assert round(usd, 4) == 7.05


def test_estimate_cost_unknown_model_is_zero() -> None:
    config = ResearchConfig()
    usage = _Usage(input_tokens=999, output_tokens=999)

    usd, eur = token_meter.estimate_cost(usage, "no-such-model", config)

    assert (usd, eur) == (0.0, 0.0)


def test_record_returns_frozen_shape_without_path() -> None:
    config = ResearchConfig()
    usage = _Usage(input_tokens=100, output_tokens=50)

    rec = token_meter.record(usage, "claude-sonnet-4-6", config, path=None)

    assert set(rec) == {
        "ts",
        "model",
        "input_tokens",
        "output_tokens",
        "est_cost_usd",
        "est_cost_eur",
    }
    assert rec["model"] == "claude-sonnet-4-6"
    assert rec["input_tokens"] == 100
    assert rec["output_tokens"] == 50


def test_record_appends_to_json_array(tmp_path, monkeypatch) -> None:
    log_path = tmp_path / "llm_usage.json"
    config = ResearchConfig()

    # Freeze the clock so ``ts`` is deterministic.
    from datetime import datetime, timezone

    frozen = datetime(2026, 6, 8, 9, 30, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(timeutil, "_utcnow", lambda: frozen)

    token_meter.record(_Usage(input_tokens=10, output_tokens=5),
                       "claude-sonnet-4-6", config, path=str(log_path))
    token_meter.record(_Usage(input_tokens=20, output_tokens=8),
                       "claude-haiku-4-5-20251001", config, path=str(log_path))

    data = json.loads(log_path.read_text())
    assert isinstance(data, list) and len(data) == 2
    assert data[0]["ts"] == "2026-06-08T09:30:00.000Z"
    assert data[0]["model"] == "claude-sonnet-4-6"
    assert data[1]["model"] == "claude-haiku-4-5-20251001"
    assert data[1]["input_tokens"] == 20


def test_record_tolerates_corrupt_existing_log(tmp_path) -> None:
    log_path = tmp_path / "llm_usage.json"
    log_path.write_text("{ not valid json")
    config = ResearchConfig()

    token_meter.record(_Usage(input_tokens=1, output_tokens=1),
                       "claude-sonnet-4-6", config, path=str(log_path))

    data = json.loads(log_path.read_text())
    assert isinstance(data, list) and len(data) == 1
