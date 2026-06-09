"""Tests for the single LLM call site — ``LLMClient.ask_candidate`` (Step 5).

All mocked: ``LLMClient._raw_call`` is replaced by a :class:`FakeRawCall`, so no
network and **no ``anthropic`` import** in the unit run (faults are classified by
class name). The structured-output request surface is asserted via the pure
``_build_create_kwargs`` helper.
"""

from __future__ import annotations

import json

import pytest

from research.llm_client import (
    LLMClient,
    _extract_json_object,
    _strip_fences,
    _supports_sampling,
)
from research.models import LLMResponseError, ResearchConfig

from tests.conftest import (
    AuthenticationError,
    BadRequestError,
    FakeRawCall,
    _FakeUsage,
    make_message,
    make_text_message,
)

SCHEMA = {"type": "object", "properties": {"abstain": {"type": "boolean"}}}


def _client(model: str = "claude-sonnet-4-6", **kw) -> LLMClient:
    return LLMClient(
        model=model,
        api_key="test-key",
        max_tokens=1024,
        temperature=0.2,
        timeout_s=30.0,
        **kw,
    )


def test_structured_happy_path_returns_dict(good_raw) -> None:
    client = _client()
    fake = FakeRawCall([make_message(good_raw)])
    client._raw_call = fake  # type: ignore[method-assign]

    result = client.ask_candidate("sys", "usr", SCHEMA)

    assert result == good_raw
    # Exactly one call, on the structured path (json_schema passed through).
    assert len(fake.calls) == 1
    assert fake.calls[0]["json_schema"] is SCHEMA


def test_fallback_on_bad_request_fence_strips_plain_json(good_raw) -> None:
    client = _client()
    fake = FakeRawCall([
        BadRequestError("output_config not supported"),  # structured call 400s
        make_message(good_raw, fenced=True),             # plain call, fenced JSON
    ])
    client._raw_call = fake  # type: ignore[method-assign]

    result = client.ask_candidate("sys", "usr", SCHEMA)

    assert result == good_raw
    # Two raw calls within ONE attempt: structured (schema set) then plain (None).
    assert len(fake.calls) == 2
    assert fake.calls[0]["json_schema"] is SCHEMA
    assert fake.calls[1]["json_schema"] is None


def test_malformed_json_retries_once_then_raises() -> None:
    client = _client()
    fake = FakeRawCall([
        make_text_message("not json at all"),
        make_text_message("still not json"),
    ])
    client._raw_call = fake  # type: ignore[method-assign]

    with pytest.raises(LLMResponseError):
        client.ask_candidate("sys", "usr", SCHEMA)

    # One retry → exactly two attempts (two raw calls).
    assert len(fake.calls) == 2


def test_transient_error_retries_then_succeeds(good_raw) -> None:
    client = _client()
    fake = FakeRawCall([
        ConnectionError("connection reset"),  # transient → retry
        make_message(good_raw),               # second attempt succeeds
    ])
    client._raw_call = fake  # type: ignore[method-assign]

    result = client.ask_candidate("sys", "usr", SCHEMA)

    assert result == good_raw
    assert len(fake.calls) == 2


def test_valid_abstain_is_not_retried() -> None:
    client = _client()
    abstain = {"abstain": True, "reasoning": "nothing tradeable"}
    fake = FakeRawCall([make_message(abstain)])
    client._raw_call = fake  # type: ignore[method-assign]

    result = client.ask_candidate("sys", "usr", SCHEMA)

    assert result == abstain
    # A content answer is not a transport fault → no retry.
    assert len(fake.calls) == 1


def test_auth_error_raises_without_retry() -> None:
    client = _client()
    fake = FakeRawCall([AuthenticationError("invalid api key")])
    client._raw_call = fake  # type: ignore[method-assign]

    with pytest.raises(LLMResponseError):
        client.ask_candidate("sys", "usr", SCHEMA)

    # Non-transient, non-bad-request → fail fast, single call.
    assert len(fake.calls) == 1


def test_sampling_param_dropped_for_opus_kept_for_sonnet() -> None:
    sonnet = _client("claude-sonnet-4-6")
    opus = _client("claude-opus-4-8")

    sonnet_kwargs = sonnet._build_create_kwargs("s", "u", json_schema=SCHEMA)
    opus_kwargs = opus._build_create_kwargs("s", "u", json_schema=SCHEMA)

    # Billing/request-surface change: Opus 4.8 rejects temperature → dropped.
    assert sonnet_kwargs["temperature"] == 0.2
    assert "temperature" not in opus_kwargs
    assert _supports_sampling("claude-sonnet-4-6")
    assert not _supports_sampling("claude-opus-4-8")
    # Structured outputs use output_config.format (not the deprecated output_format).
    assert opus_kwargs["output_config"]["format"]["type"] == "json_schema"
    assert opus_kwargs["output_config"]["format"]["schema"] is SCHEMA
    # Thinking is off by default.
    assert "thinking" not in sonnet_kwargs


def test_thinking_kwarg_added_when_enabled() -> None:
    client = _client(enable_thinking=True)
    kwargs = client._build_create_kwargs("s", "u", json_schema=None)
    assert kwargs["thinking"] == {"type": "adaptive"}
    assert "output_config" not in kwargs  # plain (fallback) path omits it


def test_successful_call_records_usage_to_log(tmp_path, good_raw) -> None:
    log_path = tmp_path / "llm_usage.json"
    client = _client(token_meter_path=str(log_path), config=ResearchConfig())
    fake = FakeRawCall([make_message(good_raw, usage=_FakeUsage(input_tokens=100,
                                                                output_tokens=50))])
    client._raw_call = fake  # type: ignore[method-assign]

    client.ask_candidate("sys", "usr", SCHEMA)

    records = json.loads(log_path.read_text())
    assert len(records) == 1
    assert records[0]["model"] == "claude-sonnet-4-6"
    assert records[0]["input_tokens"] == 100
    assert records[0]["output_tokens"] == 50


def test_strip_fences_handles_plain_and_fenced() -> None:
    assert _strip_fences('{"a": 1}') == '{"a": 1}'
    assert _strip_fences('```json\n{"a": 1}\n```') == '{"a": 1}'
    assert _strip_fences('```\n{"a": 1}\n```') == '{"a": 1}'


def test_extract_json_object_recovers_first_balanced_object() -> None:
    # Prose before and after a balanced object → just the object.
    assert _extract_json_object('Here is my pick: {"epic": "X"} hope that helps') == (
        '{"epic": "X"}'
    )
    # Braces inside string literals must not miscount the depth.
    assert _extract_json_object('{"reasoning": "a } b { c"}') == (
        '{"reasoning": "a } b { c"}'
    )
    # Nested objects are balanced through the matching close brace.
    assert _extract_json_object('x {"a": {"b": 1}} y') == '{"a": {"b": 1}}'
    # No object present → None.
    assert _extract_json_object("no json here at all") is None


def test_fallback_recovers_prose_wrapped_json() -> None:
    """Structured 400 → plain fallback returns JSON wrapped in prose → recovered."""
    client = _client()
    pick = {"abstain": False, "epic": "IX.D.DAX.IFMM.IP", "direction": "BUY",
            "confidence": 60, "reasoning": "ok"}
    prose = "Based on the data, here is my pick: " + json.dumps(pick)
    fake = FakeRawCall([
        BadRequestError("output_config not supported"),  # structured call 400s
        make_text_message(prose),                        # plain call, prose-wrapped
    ])
    client._raw_call = fake  # type: ignore[method-assign]

    result = client.ask_candidate("sys", "usr", SCHEMA)

    assert result == pick
    # One attempt: structured (schema) then plain (None) — recovered, no retry.
    assert len(fake.calls) == 2
    assert fake.calls[1]["json_schema"] is None


def test_fallback_pure_prose_still_raises_after_retry() -> None:
    """Fallback with no JSON object at all → parse failure → single retry → raise."""
    client = _client()
    fake = FakeRawCall([
        BadRequestError("output_config not supported"),  # attempt 1: structured 400
        make_text_message("I cannot pick anything right now."),  # attempt 1: plain prose
        BadRequestError("output_config not supported"),  # attempt 2 (retry): 400
        make_text_message("Still no structured answer."),        # attempt 2: plain prose
    ])
    client._raw_call = fake  # type: ignore[method-assign]

    with pytest.raises(LLMResponseError):
        client.ask_candidate("sys", "usr", SCHEMA)

    # Two attempts, each = structured(400) + plain → four raw calls. Safe abstain.
    assert len(fake.calls) == 4
