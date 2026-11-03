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


def test_length_truncation_raises_without_retry(monkeypatch) -> None:
    """Phase 17 B-4 (T20): finish_reason=length + unparseable JSON is non-transient.

    Same retry semantics as the Anthropic client's stop_reason=max_tokens path —
    a retry at the same ``max_tokens`` truncates again identically. Exactly one
    network call. ``last_finish_reason`` is surfaced for downstream readers.
    """
    body = {
        "choices": [
            {
                "message": {"content": "not json at all"},
                "finish_reason": "length",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }
    calls: list = []
    monkeypatch.setattr(
        requests, "post", _fake_post(calls, [_FakeResponse(200, body)])
    )
    client = _client(monkeypatch)

    with pytest.raises(LLMResponseError, match="finish_reason=length"):
        client.ask_candidate("sys", "usr", SCHEMA)

    assert len(calls) == 1  # no retry on truncation + parse failure
    assert client.last_finish_reason == "length"


def test_meters_even_when_parse_fails(monkeypatch, tmp_path) -> None:
    """Phase 17 B-4 (T20): meter runs BEFORE the parse — K6 sees every billed response.

    Two retried attempts both fail to parse (no finish_reason hint, transient
    per Decision 8). The meter records two responses regardless of the parse
    failures — pre-B-4 this would have logged 0 and silently under-counted K6.
    """
    body = {"choices": [{"message": {"content": "not json at all"}}], "usage": {}}
    calls: list = []
    monkeypatch.setattr(requests, "post", _fake_post(calls, [_FakeResponse(200, body)] * 2))
    log_path = tmp_path / "llm_usage.json"
    client = _client(monkeypatch, token_meter_path=str(log_path))

    with pytest.raises(LLMResponseError):
        client.ask_candidate("sys", "usr", SCHEMA)

    records = json.loads(log_path.read_text())
    assert len(records) == 2  # one per failed attempt, NOT 0 (pre-B-4 bug)


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


def test_bad_request_400_retries_once_without_response_format_then_raises(monkeypatch) -> None:
    """Phase 17 C-3 (a): a 400 on a request that carried ``response_format`` is
    retried **once without that field** — same fallback as the Anthropic client
    (``llm_client._attempt``). The retry does not consume the transient retry:
    a *second* 400 is a config-level error and raises immediately.

    (Renamed from ``test_bad_request_400_raises_immediately_no_retry`` — that
    expectation became wrong with C-3; Plan §15.4 C-3 Nr. 6.)
    """
    calls: list = []
    monkeypatch.setattr(
        requests,
        "post",
        _fake_post(calls, [_FakeResponse(400, text="bad request")] * 2),
    )
    client = _client(monkeypatch)

    with pytest.raises(LLMResponseError):
        client.ask_candidate("sys", "usr", SCHEMA)

    assert len(calls) == 2  # the response_format fallback — not the transient retry
    assert "response_format" in calls[0]["json"]
    assert "response_format" not in calls[1]["json"]


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


# --------------------------------------------------------------------------- #
# Phase 17 C-3 — reasoning blocks, the 400 fallback and the provider quirks.
# --------------------------------------------------------------------------- #


def test_400_with_response_format_retries_once_without_it(monkeypatch) -> None:
    """C-3 (a): the endpoint rejects ``response_format`` — the request goes out a
    second time without that field and the answer is parsed normally.

    The retry is **inside** one attempt (it does not consume the transient
    retry): the second call succeeds, so the caller gets its dict after exactly
    two HTTP requests.
    """
    good = {"abstain": False, "epic": "IX.D.DAX.IFMM.IP", "direction": "BUY", "confidence": 72.0}
    calls: list = []
    monkeypatch.setattr(
        requests,
        "post",
        _fake_post(calls, [_FakeResponse(400, text="unsupported parameter"), _FakeResponse(200, _happy_body(good))]),
    )
    client = _client(monkeypatch)

    result = client.ask_candidate("sys", "usr", SCHEMA)

    assert result == good
    assert len(calls) == 2
    assert "response_format" in calls[0]["json"]
    assert "response_format" not in calls[1]["json"]


def test_think_block_is_stripped_before_json_parse(monkeypatch) -> None:
    """C-3 (b): reasoning models (GLM/DeepSeek/Qwen) put their reasoning into a
    ``<think>…</think>`` block before the JSON. The block is not JSON — it must be
    gone before parsing, otherwise every GLM answer would fail to parse."""
    good = {"abstain": False, "epic": "IX.D.DAX.IFMM.IP", "direction": "BUY", "confidence": 72.0}
    body = {
        "choices": [
            {
                "message": {
                    "content": "<think>let me weigh the spread and the momentum…</think>\n"
                    + json.dumps(good)
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }
    calls: list = []
    monkeypatch.setattr(requests, "post", _fake_post(calls, [_FakeResponse(200, body)]))
    client = _client(monkeypatch)

    result = client.ask_candidate("sys", "usr", SCHEMA)

    assert result == good
    assert len(calls) == 1
    assert "<think>" in client.last_raw_text  # the raw text still shows it


def test_unterminated_think_raises_without_retry(monkeypatch) -> None:
    """C-3 (b): an **unterminated** think block means the reply was cut off — a
    hard, non-retryable error (the same prompt at the same token limit truncates
    again). Exactly one HTTP call."""
    body = {
        "choices": [
            {"message": {"content": "<think>still thinking about the spread"}, "finish_reason": "length"}
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }
    calls: list = []
    monkeypatch.setattr(requests, "post", _fake_post(calls, [_FakeResponse(200, body)]))
    client = _client(monkeypatch)

    with pytest.raises(LLMResponseError, match="unterminated <think> block"):
        client.ask_candidate("sys", "usr", SCHEMA)

    assert len(calls) == 1  # no retry — a retry truncates again


def test_custom_api_key_username_is_used(monkeypatch) -> None:
    """C-3: the keyring **username** is a constructor argument, not a hard-coded
    ``"api_key"`` — every provider gets its own namespace (service + username)."""
    seen: dict = {}

    def _fake_get_password(service: str, username: str) -> str:
        seen["call"] = (service, username)
        return "k"

    monkeypatch.setattr(keyring, "get_password", _fake_get_password)
    client = OpenAICompatLLMClient(
        model="test-model", api_key_service="trading-bot-zai-bot", api_key_username="api_key"
    )

    assert client._get_api_key() == "k"
    assert seen["call"] == ("trading-bot-zai-bot", "api_key")


# --------------------------------------------------------------------------- #
# §15 T27/T28 — the three provider quirks.
# --------------------------------------------------------------------------- #


def test_default_quirks_payload_is_unchanged(monkeypatch) -> None:
    """T28: the defaults reproduce the pre-§15 payload **byte for byte** — same
    keys, same order. Any change here is a silent behaviour change for every
    provider that does not need a quirk."""
    calls: list = []
    monkeypatch.setattr(
        requests,
        "post",
        _fake_post(calls, [_FakeResponse(200, _happy_body({"abstain": True}))]),
    )
    client = _client(monkeypatch)

    client.ask_candidate("sys", "usr", SCHEMA)

    assert list(calls[0]["json"]) == [
        "model",
        "messages",
        "max_tokens",
        "temperature",
        "response_format",
    ]


def test_max_completion_tokens_field_replaces_max_tokens(monkeypatch) -> None:
    """The OpenAI GPT-5 line wants ``max_completion_tokens`` — the quirk swaps the
    payload key (and removes ``max_tokens``)."""
    calls: list = []
    monkeypatch.setattr(
        requests,
        "post",
        _fake_post(calls, [_FakeResponse(200, _happy_body({"abstain": True}))]),
    )
    client = _client(monkeypatch, max_tokens_field="max_completion_tokens")

    client.ask_candidate("sys", "usr", SCHEMA)

    payload = calls[0]["json"]
    assert payload["max_completion_tokens"] == 1024
    assert "max_tokens" not in payload


def test_send_temperature_false_omits_temperature(monkeypatch) -> None:
    """Some reasoning models reject ``temperature`` outright — the quirk omits
    the field instead of sending it."""
    calls: list = []
    monkeypatch.setattr(
        requests,
        "post",
        _fake_post(calls, [_FakeResponse(200, _happy_body({"abstain": True}))]),
    )
    client = _client(monkeypatch, send_temperature=False)

    client.ask_candidate("sys", "usr", SCHEMA)

    assert "temperature" not in calls[0]["json"]


def test_extra_body_is_merged_into_payload(monkeypatch) -> None:
    """Non-standard body fields (DeepSeek/GLM ``thinking``, Qwen
    ``enable_thinking``) ride along in ``extra_body``."""
    calls: list = []
    monkeypatch.setattr(
        requests,
        "post",
        _fake_post(calls, [_FakeResponse(200, _happy_body({"abstain": True}))]),
    )
    client = _client(monkeypatch, extra_body={"thinking": {"type": "disabled"}})

    client.ask_candidate("sys", "usr", SCHEMA)

    assert calls[0]["json"]["thinking"] == {"type": "disabled"}


def test_invalid_quirks_raise_value_error_at_construction(monkeypatch) -> None:
    """The constructor is the one choke point the bot (``_build_llm``) and the
    smoke script share — a broken provider entry fails here, not on the first
    live call. ``extra_body`` may not set a client-owned key (T28)."""
    monkeypatch.setattr(keyring, "get_password", lambda service, username: "test-key")

    with pytest.raises(ValueError, match="max_tokens_field"):
        OpenAICompatLLMClient(model="test-model", max_tokens_field="max_output_tokens")

    with pytest.raises(ValueError, match="extra_body must not set client-owned keys"):
        OpenAICompatLLMClient(model="test-model", extra_body={"stream": True})
