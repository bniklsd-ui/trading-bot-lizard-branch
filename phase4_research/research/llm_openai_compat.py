"""OpenAI-compatible client — wired via ``phase8_scheduler/scheduler/llm_profiles.py``.

Since Phase 17 this client is **live**: the scheduler's routing table
(``scheduler/llm_profiles.py``) maps a role to a provider, and every
non-Anthropic provider is served by this class (T25: exactly two client classes —
``LLMClient`` for Anthropic-native, this one for everything else). The single
construction site is ``phase8_scheduler/scripts/wiring.py::_build_llm``; the
provider's endpoint, keyring namespace and request quirks come from its
:class:`~scheduler.llm_profiles.ProviderSpec` via ``client_kwargs(spec)``.

The operator smoke (``scripts/openrouter_smoke.py``) uses **the same**
construction (``--provider <name>``), so a smoke proves the very payload the bot
would send.

## Interface parity

Mirrors :class:`~research.llm_client.LLMClient`'s public surface exactly where it
matters to a caller: ``ask_candidate(system, user, json_schema) -> dict`` (the
``_LLMLike`` Protocol ``research.py`` actually depends on), ``.model``, and
``.last_usage`` (a Phase-6-debate-style reader). Retry policy mirrors Decision 8
(``llm_client`` module docstring) exactly: **exactly one retry**, only on a
*transient* fault (network / timeout / 5xx / 429 / JSON parse failure); a
config-level error (4xx auth/bad-request, missing key) raises immediately, no
retry wasted.

## Provider quirks (Phase 17 §15 T27/T28)

Three documented differences between OpenAI-compatible endpoints are **fields on
the client**, not branches in the code:

* ``max_tokens_field`` — ``"max_tokens"`` (default) or ``"max_completion_tokens"``
  (the OpenAI GPT-5 line),
* ``send_temperature`` — some reasoning models reject the field outright,
* ``extra_body`` — non-standard body fields (e.g. ``{"thinking": {...}}``).

The defaults reproduce the pre-§15 payload **byte for byte**. ``extra_body`` is
merged **first** (client-owned keys always win) and may not contain a
client-owned key — that is rejected right here, in the constructor, because the
constructor is the one choke point the bot (``_build_llm``) and the smoke script
share.

## Structured Outputs — no equivalent, so it's a prompt instruction instead

OpenAI-compatible APIs have no ``output_config.format`` / decoding-layer schema
enforcement equivalent to Anthropic Structured Outputs. This adapter requests
``response_format={"type": "json_object"}`` (loose JSON-mode) and additionally
serialises ``json_schema`` into the system prompt as an explicit instruction —
weaker than decode-time enforcement, so the fence-strip / prose-recovery parse
path (reused from ``llm_client``, same tiny pure helpers) matters more here, not
less. If an endpoint rejects ``response_format`` with HTTP 400, the request is
sent **once more without that field** (same fallback as
``LLMClient._attempt:388-398``) — it does not consume the transient retry.

Reasoning models (GLM, DeepSeek, Qwen 3.5+) may emit a ``<think>…</think>``
block before the JSON. The block is stripped before parsing; an **unterminated**
block is a hard, non-retryable error (the same prompt at the same token limit
would truncate again).

``enable_thinking`` / ``cache_system`` are accepted-but-ignored kwargs purely so
a caller that constructs with the full ``LLMClient`` kwarg set (e.g. Phase 6's
debate) doesn't need a conditional — no OpenAI-compat equivalent exists for
either, so they are documented no-ops, never silently doing something different
than the name implies.
"""

from __future__ import annotations

import json
import logging
import re
from types import SimpleNamespace
from typing import Any, Mapping

import keyring
import requests

from research import token_meter
from research.llm_client import _extract_json_object, _strip_fences
from research.models import LLMResponseError, ResearchConfig

log = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
_KEYRING_USERNAME = "api_key"

#: Payload keys the client owns — ``extra_body`` may not set any of them (§15 T28).
_RESERVED_PAYLOAD_KEYS = frozenset(
    {
        "model",
        "messages",
        "max_tokens",
        "max_completion_tokens",
        "temperature",
        "response_format",
        "stream",
    }
)

#: The token-limit field names a client may send (§15 T27).
_MAX_TOKENS_FIELDS = ("max_tokens", "max_completion_tokens")

_THINK_BLOCK_RE = re.compile(r"(?s)<think>.*?</think>")


def _strip_think(text: str) -> str:
    """Remove complete ``<think>…</think>`` blocks from a reasoning model's reply.

    Reasoning models (GLM, DeepSeek, Qwen) put their reasoning into a ``<think>``
    block before the JSON answer. The block is *not* part of the JSON, so it must
    go before parsing. An **unterminated** block (the model was cut off) leaves
    the marker in the text — the caller turns that into a hard error instead of
    parsing garbage.

    Args:
        text: the raw assistant text.

    Returns:
        The text without complete think blocks, stripped.
    """
    return _THINK_BLOCK_RE.sub("", text).strip()


def _is_transient(exc: BaseException) -> bool:
    """Classify a fault as transient (network / timeout / 5xx / 429).

    Mirrors ``llm_client._is_transient`` exactly (same retry semantics,
    Decision 8) but classifies off ``requests`` exception types + a
    ``status_code`` attribute instead of Anthropic SDK exception class names —
    there is no SDK here, only ``requests`` + plain HTTP status codes.
    """
    if isinstance(exc, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
        return True
    code = getattr(exc, "status_code", None)
    return isinstance(code, int) and (code == 429 or code >= 500)


class _HTTPStatusFault(Exception):
    """A non-2xx HTTP response, carrying its status code for classification."""

    def __init__(self, status_code: int, body: str) -> None:
        super().__init__(f"HTTP {status_code}: {body[:300]}")
        self.status_code = status_code


class OpenAICompatLLMClient:
    """OpenAI-compatible chat-completions client (OpenRouter by default).

    Cold fallback for :class:`research.llm_client.LLMClient` — see the module
    docstring for the switch instructions and interface-parity notes.
    """

    def __init__(
        self,
        model: str,
        *,
        base_url: str = _DEFAULT_BASE_URL,
        api_key_service: str = "openrouter",
        api_key_username: str = _KEYRING_USERNAME,
        timeout_s: float = 60.0,
        max_tokens: int = 1024,
        temperature: float = 0.2,
        token_meter_path: str | None = None,
        config: ResearchConfig | None = None,
        enable_thinking: bool = False,  # no-op — see module docstring
        cache_system: bool = False,  # no-op — see module docstring
        max_tokens_field: str = "max_tokens",
        send_temperature: bool = True,
        extra_body: Mapping[str, Any] | None = None,
    ) -> None:
        """Configure the client (no network call here, no keyring read here).

        Args:
            model: the provider's model id (e.g. ``"MiniMax-M3"``).
            base_url: API base; ``/chat/completions`` is appended.
            api_key_service: OS keyring **service** name the API key is stored
                under. Default ``"openrouter"`` — a dedicated namespace, never
                the live bot's ``tradingbot`` service (same isolation pattern as
                the M1 bake-off key). The bot's own providers use their own
                namespaces (``trading-bot-zai-bot``, ``trading-bot-minimax-bot``,
                …) — see ``scheduler/llm_profiles.py``.
            api_key_username: OS keyring **username** under that service.
            timeout_s / max_tokens / temperature: transport + decoding knobs.
            token_meter_path: forwarded to ``token_meter.record`` — ``None``
                disables the file write (the meter still computes the record).
            config: pricing source for the meter; defaults to
                ``ResearchConfig()``. An unrecognised model id in
                ``config.pricing_usd_per_mtok`` logs cost as 0.0 (the meter's own
                documented graceful-unknown-model behaviour) — never a crash.
            enable_thinking / cache_system: accepted, always ignored — no
                OpenAI-compat equivalent (see module docstring).
            max_tokens_field: which payload key carries the token limit —
                ``"max_tokens"`` (default) or ``"max_completion_tokens"``.
            send_temperature: whether the payload may carry ``temperature``.
            extra_body: non-standard body fields merged into the payload (e.g.
                ``{"thinking": {"type": "disabled"}}``).

        Raises:
            ValueError: ``max_tokens_field`` is unknown, or ``extra_body`` tries
                to set a client-owned key (§15 T28) — the constructor is the one
                choke point the bot and the smoke script share, so a broken
                provider entry fails here and not on the first live call.
        """
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key_service = api_key_service
        self.api_key_username = api_key_username
        self.timeout_s = timeout_s
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.token_meter_path = token_meter_path
        self.config = config if config is not None else ResearchConfig()
        # §15 T27/T28: provider quirks, validated here — the one choke point the bot and the smoke share.
        if max_tokens_field not in _MAX_TOKENS_FIELDS:
            raise ValueError(
                f"max_tokens_field must be max_tokens|max_completion_tokens, got {max_tokens_field!r}"
            )
        reserved = set(extra_body or {}) & _RESERVED_PAYLOAD_KEYS
        if reserved:
            raise ValueError(f"extra_body must not set client-owned keys: {sorted(reserved)}")
        self.max_tokens_field = max_tokens_field
        self.send_temperature = send_temperature
        self.extra_body: dict[str, Any] = dict(extra_body or {})
        # Captured per successful call, mirroring LLMClient.last_usage — lets a
        # reusing caller read per-turn token usage without changing ask_candidate.
        self.last_usage: dict[str, Any] | None = None
        # OpenAI-compat truncation signal — "stop" (complete) or "length" (truncated
        # at max_tokens). Surfaced per call so the parse-failure branch can decide
        # whether a retry would just truncate again (Phase 17 B-4, T20).
        self.last_finish_reason: str | None = None
        # The raw assistant text of the last reply — the operator smoke prints the
        # first 400 characters of it (``--show-raw``) so a failed parse can be
        # judged by eye (Phase 17 C-6).
        self.last_raw_text: str = ""
        self._api_key: str | None = None  # lazily fetched from the keyring, cached

    # ------------------------------------------------------------------ #
    # Credentials (self-contained: wiring.py needs no new import for this) #
    # ------------------------------------------------------------------ #
    def _get_api_key(self) -> str:
        """Fetch+cache the API key from the OS keyring. Never a file, never env."""
        if self._api_key is not None:
            return self._api_key
        value = keyring.get_password(self.api_key_service, self.api_key_username)
        if not value:
            raise LLMResponseError(
                f"no API key in the OS keyring (service={self.api_key_service!r}, "
                f"username={self.api_key_username!r}) — seed it via "
                "keyring.set_password(...) or scripts/openrouter_smoke.py --store-key"
            )
        self._api_key = value
        return value

    # ------------------------------------------------------------------ #
    # The one mockable raw call site (llm_client._raw_call analogue)      #
    # ------------------------------------------------------------------ #
    def _raw_call(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST one chat-completion request; return the parsed JSON body.

        Raises ``_HTTPStatusFault`` (carrying ``.status_code``) on a non-2xx
        response, or a ``requests`` transport exception — both classified by
        ``_is_transient`` in ``ask_candidate``'s retry loop. A malformed JSON
        body raises ``ValueError``/``json.JSONDecodeError`` — the same parse-
        failure family ``ask_candidate`` retries once (Decision 8).
        """
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self._get_api_key()}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.timeout_s,
        )
        if response.status_code >= 400:
            raise _HTTPStatusFault(response.status_code, response.text)
        return response.json()

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #
    def ask_candidate(self, system: str, user: str, json_schema: dict) -> dict:
        """Ask the model for one candidate; return the parsed (unvalidated) dict.

        Same contract as ``LLMClient.ask_candidate`` (the ``_LLMLike`` Protocol
        ``research.py`` depends on) — the caller must still run the result
        through ``validate_candidate`` before trusting it; this client performs
        no validation itself.

        Raises:
            LLMResponseError: after the single retry is exhausted, on a
                non-transient fault (bad request / auth), or when the API key
                is missing from the keyring.
        """
        last_exc: Exception | None = None
        for attempt in (1, 2):  # exactly one retry → at most two attempts
            try:
                return self._attempt(system, user, json_schema)
            except (ValueError, json.JSONDecodeError) as exc:  # parse failure
                last_exc = exc
                log.warning("ask_candidate parse failure (attempt %d): %s", attempt, exc)
            except Exception as exc:  # noqa: BLE001 - classified below
                if _is_transient(exc):
                    last_exc = exc
                    log.warning(
                        "ask_candidate transient fault (attempt %d): %s", attempt, exc
                    )
                    continue
                raise LLMResponseError(
                    f"OpenAI-compat call failed (base_url={self.base_url}): {exc!r}"
                ) from exc

        raise LLMResponseError(
            f"OpenAI-compat call failed (base_url={self.base_url}) after retry: {last_exc!r}"
        )

    # ------------------------------------------------------------------ #
    # Internals                                                          #
    # ------------------------------------------------------------------ #
    def _attempt(self, system: str, user: str, json_schema: dict) -> dict:
        """One full attempt: build the request, parse the response, meter usage.

        Since Phase 17 B-4 (T20): metering runs **before** parsing so a response
        that fails to parse is still billed toward K6; truncation (``finish_reason ==
        "length"``) on top of a parse failure is surfaced as a non-transient
        :class:`LLMResponseError` — the retry path cannot fix a token-budget-cutoff.

        Two provider-specific guards live here (Plan §6 C-3):
        * an HTTP 400 on a request that carried ``response_format`` is retried
          **once without that field** (same fallback as ``LLMClient._attempt``) —
          it does not consume the transient retry;
        * a reasoning model's ``<think>…</think>`` block is stripped before
          parsing; an unterminated block is a hard error (no retry).
        """
        schema_instruction = (
            "Respond with a single JSON object matching exactly this JSON Schema "
            f"— no prose, no markdown fence:\n{json.dumps(json_schema)}"
        )
        payload: dict[str, Any] = {
            **self.extra_body,  # first: client-owned keys below always win (T28; reserved keys rejected in __init__)
            "model": self.model,
            "messages": [
                {"role": "system", "content": f"{system}\n\n{schema_instruction}"},
                {"role": "user", "content": user},
            ],
            self.max_tokens_field: self.max_tokens,
        }
        if self.send_temperature:
            payload["temperature"] = self.temperature
        payload["response_format"] = {"type": "json_object"}
        try:
            body = self._raw_call(payload)
        except _HTTPStatusFault as exc:
            # C-3 (a): the endpoint cannot honour response_format — send the request
            # once more without that field. Not a transient fault, so it does not
            # consume the single retry. The FIRST error text is logged, otherwise
            # the operator only sees the second (Plan §15.6).
            if exc.status_code == 400 and "response_format" in payload:
                log.info(
                    "HTTP 400 with response_format — retrying once without it; first fault: %s",
                    exc,
                )
                payload = {k: v for k, v in payload.items() if k != "response_format"}
                body = self._raw_call(payload)
            else:
                raise
        choice = body["choices"][0]
        # Truncation surfaced here so the parse-failure branch below can short-circuit
        # to a non-transient LLMResponseError (Phase 17 B-4, T20).
        self.last_finish_reason: str | None = choice.get("finish_reason")

        # Meter first: a response that fails to parse was still billed (Phase 17 B-4).
        usage = body.get("usage") or {}
        # OpenAI-compat field names (prompt_tokens/completion_tokens) mapped onto
        # the Anthropic-shaped attribute names token_meter.record duck-types on;
        # cache fields are always 0 — no cache_control equivalent (module docstring).
        usage_ns = SimpleNamespace(
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            cache_creation_input_tokens=0,
            cache_read_input_tokens=0,
        )
        try:
            self.last_usage = token_meter.record(
                usage_ns, self.model, self.config, self.token_meter_path
            )
        except Exception as exc:  # pragma: no cover - defensive, mirrors llm_client
            log.warning("token_meter.record failed: %s", exc)

        raw_text = choice["message"].get("content") or ""
        self.last_raw_text = raw_text
        # Reasoning models (GLM/DeepSeek/Qwen) put their reasoning into a <think>
        # block — it is not JSON and must go before parsing (C-3 (b)).
        text = _strip_think(raw_text)
        if "<think>" in text:
            # Unterminated block ⇒ the reply was cut off. Non-retryable: the same
            # prompt at the same token limit truncates again.
            raise LLMResponseError(
                f"unterminated <think> block (finish_reason={self.last_finish_reason}, "
                f"max_tokens={self.max_tokens}, model={self.model})"
            )
        text = _strip_fences(text)
        try:
            raw = json.loads(text)
        except json.JSONDecodeError:
            # Truncation + unparseable JSON → non-transient LLMResponseError, no retry
            # (T20). The same prompt at the same ``max_tokens`` will truncate again.
            if self.last_finish_reason == "length":
                raise LLMResponseError(
                    f"LLM output truncated (finish_reason=length, "
                    f"max_tokens={self.max_tokens}, model={self.model})"
                ) from None
            # No decode-time schema constraint here (see module docstring), so a
            # prose-wrapped reply is the *expected* case to recover from, not an
            # edge case — same recovery ``llm_client``'s schema-free fallback uses.
            snippet = _extract_json_object(text)
            if snippet is None:
                raise
            raw = json.loads(snippet)
        return raw
