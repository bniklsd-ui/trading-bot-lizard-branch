"""Tests for the cold OpenAI-compatible fallback client (M1 Step 10).

All mocked: ``requests.post`` is monkeypatched with a fake response, ``keyring``
is monkeypatched to avoid touching the real OS keyring — no network, no real
credentials, matching the repo convention (mocked HTTP, no live calls in unit
tests).
"""

from __future__ import annotations

import json

import keyring
import pytest
import requests

from research.llm_openai_compat import OpenAICompatLLMClient
from research.models import LLMResponseError

SCHEMA = {"type": "object", "properties": {"abstain": {"type": "boolean"}}}


class _FakeResponse:
    """Minimal stand-in for ``requests.Response`` — only what the client reads."""

    def __init__(self, status_code: int = 200, json_body: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._json_body = json_body
        self.text = text or (json.dumps(json_body) if json_body is not None else "")

    def json(self) -> dict:
        if self._json_body is None:
            raise json.JSONDecodeError("no body", "", 0)
        return self._json_body


def _happy_body(content: dict, prompt_tokens: int = 10, completion_tokens: int = 5) -> dict:
    return {
        "choices": [{"message": {"content": json.dumps(content)}}],
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
    }


def _client(monkeypatch, **kw) -> OpenAICompatLLMClient:
    monkeypatch.setattr(keyring, "get_password", lambda service, username: "test-key")
    return OpenAICompatLLMClient(model="test-model", **kw)


def _fake_post(calls: list, responses: list):
    """Returns a ``requests.post`` stand-in that pops one response per call and
    records the call for assertion (e.g. retry-count checks)."""

    def _post(url, *, headers, json, timeout):  # noqa: A002 - matches requests.post's kwarg name
        calls.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        response = responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    return _post


def test_happy_path_returns_dict_and_maps_usage(monkeypatch) -> None:
    good = {"abstain": False, "epic": "IX.D.DAX.IFMM.IP", "direction": "BUY", "confidence": 72.0}
    calls: list = []
    monkeypatch.setattr(
        requests, "post", _fake_post(calls, [_FakeResponse(200, _happy_body(good, 123, 45))])
    )
    client = _client(monkeypatch)

    result = client.ask_candidate("sys", "usr", SCHEMA)

    assert result == good
    assert len(calls) == 1
    # response_format + the schema baked into the system prompt (no decode-time
    # enforcement exists for OpenAI-compat — see module docstring).
    assert calls[0]["json"]["response_format"] == {"type": "json_object"}
    assert "abstain" in calls[0]["json"]["messages"][0]["content"]
    # Usage mapped onto the Anthropic-shaped attribute names token_meter expects.
    assert client.last_usage is not None
    assert client.last_usage["input_tokens"] == 123
    assert client.last_usage["output_tokens"] == 45
    assert client.last_usage["cache_read_input_tokens"] == 0
    assert client.last_usage["cache_creation_input_tokens"] == 0


def test_malformed_json_retries_once_then_raises(monkeypatch) -> None:
    calls: list = []
    body = {"choices": [{"message": {"content": "not json at all"}}], "usage": {}}
    monkeypatch.setattr(requests, "post", _fake_post(calls, [_FakeResponse(200, body)] * 2))
    client = _client(monkeypatch)

    with pytest.raises(LLMResponseError):
        client.ask_candidate("sys", "usr", SCHEMA)

    assert len(calls) == 2  # one retry, per Decision 8


def test_rate_limit_429_retries_once_then_raises(monkeypatch) -> None:
    calls: list = []
    monkeypatch.setattr(
        requests, "post", _fake_post(calls, [_FakeResponse(429, text="rate limited")] * 2)
    )
    client = _client(monkeypatch)

    with pytest.raises(LLMResponseError):
        client.ask_candidate("sys", "usr", SCHEMA)

    assert len(calls) == 2  # 429 is transient — retried once, not raised immediately


def test_timeout_retries_once_then_raises(monkeypatch) -> None:
    calls: list = []
    monkeypatch.setattr(
        requests,
        "post",
        _fake_post(calls, [requests.exceptions.Timeout("slow"), requests.exceptions.Timeout("slow")]),
    )
    client = _client(monkeypatch)

    with pytest.raises(LLMResponseError):
        client.ask_candidate("sys", "usr", SCHEMA)

    assert len(calls) == 2


def test_bad_request_400_raises_immediately_no_retry(monkeypatch) -> None:
    calls: list = []
    monkeypatch.setattr(
        requests, "post", _fake_post(calls, [_FakeResponse(400, text="bad request")])
    )
    client = _client(monkeypatch)

    with pytest.raises(LLMResponseError):
        client.ask_candidate("sys", "usr", SCHEMA)

    assert len(calls) == 1  # config-level error — no retry wasted


def test_missing_key_raises_clean_typed_error_no_network_call(monkeypatch) -> None:
    calls: list = []
    monkeypatch.setattr(requests, "post", _fake_post(calls, []))
    monkeypatch.setattr(keyring, "get_password", lambda service, username: None)
    client = OpenAICompatLLMClient(model="test-model")

    with pytest.raises(LLMResponseError):
        client.ask_candidate("sys", "usr", SCHEMA)

    assert len(calls) == 0  # never even reached the network


def test_default_api_key_service_is_openrouter_not_the_live_bot_service(monkeypatch) -> None:
    seen: dict = {}
    client = OpenAICompatLLMClient(model="test-model")  # default api_key_service
    monkeypatch.setattr(
        keyring,
        "get_password",
        lambda service, username: seen.setdefault("call", (service, username)) or "k",
    )
    client._get_api_key()

    assert seen["call"] == ("openrouter", "api_key")  # never "tradingbot" (the live bot's service)
