"""Tests for Module 4 — caching seam + the additive Phase-4 edits (Decision F/G).

Covers both sides of the documented cross-phase reuse:
- the Phase-4 ``LLMClient`` cache marker (``cache_system`` on / off) and the
  ``token_meter`` cache-field record, asserted against the **real** Phase-4 code
  (reached via the editable install) — but **SDK-free** (``_build_create_kwargs``
  is pure; ``estimate_cost``/``record`` are pure);
- the Phase-6 ``ask_agent`` wrapper, with a fake client (no network, no SDK).
"""

from __future__ import annotations

import pytest

from debate.llm_caching import ask_agent
from debate.models import DebateLLMError

from research.llm_client import LLMClient
from research import token_meter
from research.models import ResearchConfig


def _client(model: str = "claude-haiku-4-5-20251001", **kw) -> LLMClient:
    return LLMClient(
        model, "test-key", max_tokens=512, temperature=0.4, timeout_s=30.0, **kw
    )


class _Usage:
    """Duck-typed Anthropic ``usage`` (only the token-count attrs are read)."""

    def __init__(self, **fields: int) -> None:
        for name, value in fields.items():
            setattr(self, name, value)


# --------------------------------------------------------------------------- #
# Phase-4 edit 1: cache_control marker on the system block (cache_system flag) #
# --------------------------------------------------------------------------- #


def test_cache_system_true_marks_system_block() -> None:
    client = _client(cache_system=True)
    kwargs = client._build_create_kwargs(
        "SYSTEXT", "USR", json_schema=None, cache_system=client.cache_system
    )
    system = kwargs["system"]
    assert isinstance(system, list) and len(system) == 1
    assert system[0]["type"] == "text"
    assert system[0]["text"] == "SYSTEXT"
    assert system[0]["cache_control"] == {"type": "ephemeral"}


def test_cache_system_false_is_plain_string_p4_default() -> None:
    client = _client()  # default cache_system=False → Phase-4 behaviour
    assert client.cache_system is False
    kwargs = client._build_create_kwargs("SYSTEXT", "USR", json_schema=None)
    assert kwargs["system"] == "SYSTEXT"  # byte-identical to the pre-cache request


# --------------------------------------------------------------------------- #
# Phase-4 edit 2: token_meter logs the two cache fields (additive, Decision G) #
# --------------------------------------------------------------------------- #


def test_record_includes_cache_fields() -> None:
    usage = _Usage(
        input_tokens=10,
        output_tokens=5,
        cache_read_input_tokens=120,
        cache_creation_input_tokens=30,
    )
    rec = token_meter.record(usage, "claude-sonnet-4-6", ResearchConfig(), None)
    assert rec["cache_read_input_tokens"] == 120
    assert rec["cache_creation_input_tokens"] == 30


def test_record_cache_fields_zero_at_p4_default() -> None:
    usage = _Usage(input_tokens=10, output_tokens=5)  # no cache attrs
    rec = token_meter.record(usage, "claude-sonnet-4-6", ResearchConfig(), None)
    assert rec["cache_read_input_tokens"] == 0
    assert rec["cache_creation_input_tokens"] == 0


def test_estimate_cost_read_and_write_multipliers() -> None:
    usage = _Usage(
        input_tokens=1_000_000,
        output_tokens=0,
        cache_creation_input_tokens=1_000_000,
        cache_read_input_tokens=1_000_000,
    )
    usd, _ = token_meter.estimate_cost(usage, "claude-sonnet-4-6", ResearchConfig())
    # sonnet in-rate 3 USD/Mtok: 3 + 3*1.25 (write) + 3*0.1 (read) = 7.05
    assert round(usd, 4) == 7.05


def test_estimate_cost_unknown_model_zero() -> None:
    usage = _Usage(input_tokens=999, output_tokens=999)
    assert token_meter.estimate_cost(usage, "no-such-model", ResearchConfig()) == (0.0, 0.0)


# --------------------------------------------------------------------------- #
# Phase-6 wrapper: ask_agent                                                   #
# --------------------------------------------------------------------------- #


class _FakeClient:
    """Stand-in for the shared ``research.LLMClient`` (no SDK, no network)."""

    def __init__(self, *, answer: dict | None = None, usage: dict | None = None,
                 raises: Exception | None = None) -> None:
        self.model = ""
        self.temperature = 0.0
        self.last_usage = usage
        self._answer = answer if answer is not None else {"argument": "x"}
        self._raises = raises
        self.calls: list[tuple[str, str, dict, str, float]] = []

    def ask_candidate(self, system: str, user: str, json_schema: dict) -> dict:
        self.calls.append((system, user, json_schema, self.model, self.temperature))
        if self._raises is not None:
            raise self._raises
        return self._answer


def test_ask_agent_applies_model_temperature_and_returns_usage() -> None:
    usage = {"input_tokens": 7, "output_tokens": 3, "cache_read_input_tokens": 50}
    client = _FakeClient(answer={"argument": "long"}, usage=usage)
    answer, out_usage = ask_agent(
        client, "SYS", "USR", {"type": "object"},
        model="claude-haiku-4-5-20251001", temperature=0.4,
    )
    assert answer == {"argument": "long"}
    assert out_usage == usage
    # per-role model/temperature were applied to the shared client for the turn
    assert client.model == "claude-haiku-4-5-20251001"
    assert client.temperature == 0.4
    assert client.calls[0][3] == "claude-haiku-4-5-20251001"  # seen at request time
    assert client.calls[0][4] == 0.4


def test_ask_agent_empty_usage_when_none_captured() -> None:
    client = _FakeClient(usage=None)
    _, out_usage = ask_agent(
        client, "S", "U", {}, model="claude-sonnet-4-6", temperature=0.1
    )
    assert out_usage == {}


def test_ask_agent_failure_is_fail_closed_debate_error() -> None:
    client = _FakeClient(raises=RuntimeError("boom"))
    with pytest.raises(DebateLLMError):
        ask_agent(client, "S", "U", {}, model="m", temperature=0.1)
