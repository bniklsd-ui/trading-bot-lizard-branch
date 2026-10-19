"""Cold, dormant fallback LLM client — OpenAI-compatible API (OpenRouter default).

**Not wired into any live path.** M1 Step 10 (P4/P6 cold fallback): a tested,
provider-agnostic drop-in for :class:`research.llm_client.LLMClient`, kept
additive so a real Anthropic outage has a working alternative — see
``meta_m1_harness/CLAUDE.md`` for why this exists. Nothing in ``scripts/wiring.py``
or ``research.py`` imports this module; it is exercised only by its own tests and
the operator-run smoke script (``scripts/openrouter_smoke.py``).

## Interface parity

Mirrors :class:`~research.llm_client.LLMClient`'s public surface exactly where it
matters to a caller: ``ask_candidate(system, user, json_schema) -> dict`` (the
``_LLMLike`` Protocol ``research.py`` actually depends on), ``.model``, and
``.last_usage`` (a Phase-6-debate-style reader). Retry policy mirrors Decision 8
(``llm_client`` module docstring) exactly: **exactly one retry**, only on a
*transient* fault (network / timeout / 5xx / 429 / JSON parse failure); a
config-level error (4xx auth/bad-request, missing key) raises immediately, no
retry wasted.

## Switch instructions (the only wiring change this would ever need)

``scripts/wiring.py``'s ``build_research()`` currently constructs::

    llm = LLMClient(
        model=config.model,
        api_key=get_credential("anthropic_api_key"),
        max_tokens=config.max_tokens,
        temperature=config.temperature,
        timeout_s=config.timeout_s,
        token_meter_path=str(_USAGE_LOG),
        config=config,
    )

To fall back to this adapter, that one call site becomes::

    llm = OpenAICompatLLMClient(
        model="<an OpenRouter model id — pick from the current catalog>",
        max_tokens=config.max_tokens,
        temperature=config.temperature,
        token_meter_path=str(_USAGE_LOG),
        config=config,
    )

No other line in ``wiring.py`` or ``research.py`` changes — credentials are
resolved internally from a **separate** keyring service (``openrouter`` by
default, never the live bot's ``tradingbot`` service), matching the isolation
pattern the M1 bake-off key already established.

## Structured Outputs — no equivalent, so it's a prompt instruction instead

OpenAI-compatible APIs have no ``output_config.format`` / decoding-layer schema
enforcement equivalent to Anthropic Structured Outputs. This adapter requests
``response_format={"type": "json_object"}`` (loose JSON-mode) and additionally
serialises ``json_schema`` into the system prompt as an explicit instruction —
weaker than decode-time enforcement, so the fence-strip / prose-recovery parse
path (reused from ``llm_client``, same tiny pure helpers) matters more here, not
less. ``enable_thinking`` / ``cache_system`` are accepted-but-ignored kwargs
purely so a caller that constructs with the full ``LLMClient`` kwarg set (e.g.
Phase 6's debate) doesn't need a conditional — no OpenAI-compat equivalent
exists for either, so they are documented no-ops, never silently doing
something different than the name implies.
"""

from __future__ import annotations

import json
import logging
from types import SimpleNamespace
from typing import Any

import keyring
import requests

from research import token_meter
from research.llm_client import _extract_json_object, _strip_fences
from research.models import LLMResponseError, ResearchConfig

log = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
_KEYRING_USERNAME = "api_key"


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
        timeout_s: float = 60.0,
        max_tokens: int = 1024,
        temperature: float = 0.2,
        token_meter_path: str | None = None,
        config: ResearchConfig | None = None,
        enable_thinking: bool = False,  # no-op — see module docstring
        cache_system: bool = False,  # no-op — see module docstring
    ) -> None:
        """Configure the client (no network call here, no keyring read here).

        Args:
            model: OpenRouter (or any OpenAI-compatible provider) model id.
            base_url: API base; ``/chat/completions`` is appended.
            api_key_service: OS keyring **service** name the API key is stored
                under (**username** is always fixed as ``"api_key"``). Default
                ``"openrouter"`` — a dedicated namespace, never the live bot's
                ``tradingbot`` service (same isolation pattern as the M1
                bake-off key). Seed it once via
                ``keyring.set_password("openrouter", "api_key", "<key>")``, e.g.
                through ``scripts/openrouter_smoke.py --store-key``.
            timeout_s / max_tokens / temperature: transport + decoding knobs.
            token_meter_path: forwarded to ``token_meter.record`` — ``None``
                disables the file write (the meter still computes the record).
            config: pricing source for the meter; defaults to
                ``ResearchConfig()``. An unrecognised OpenRouter model id in
                ``config.pricing_usd_per_mtok`` logs cost as 0.0 (the meter's own
                documented graceful-unknown-model behaviour) — never a crash.
            enable_thinking / cache_system: accepted, always ignored — no
                OpenAI-compat equivalent (see module docstring).
        """
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key_service = api_key_service
        self.timeout_s = timeout_s
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.token_meter_path = token_meter_path
        self.config = config if config is not None else ResearchConfig()
        # Captured per successful call, mirroring LLMClient.last_usage — lets a
        # reusing caller read per-turn token usage without changing ask_candidate.
        self.last_usage: dict[str, Any] | None = None
        # OpenAI-compat truncation signal — "stop" (complete) or "length" (truncated
        # at max_tokens). Surfaced per call so the parse-failure branch can decide
        # whether a retry would just truncate again (Phase 17 B-4, T20).
        self.last_finish_reason: str | None = None
        self._api_key: str | None = None  # lazily fetched from the keyring, cached

    # ------------------------------------------------------------------ #
    # Credentials (self-contained: wiring.py needs no new import for this) #
    # ------------------------------------------------------------------ #
    def _get_api_key(self) -> str:
        """Fetch+cache the API key from the OS keyring. Never a file, never env."""
        if self._api_key is not None:
            return self._api_key
        value = keyring.get_password(self.api_key_service, _KEYRING_USERNAME)
        if not value:
            raise LLMResponseError(
                f"no API key in the OS keyring (service={self.api_key_service!r}, "
                f"username={_KEYRING_USERNAME!r}) — seed it via "
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
                raise LLMResponseError(f"OpenRouter call failed: {exc!r}") from exc

        raise LLMResponseError(f"OpenRouter call failed after retry: {last_exc!r}")

    # ------------------------------------------------------------------ #
    # Internals                                                          #
    # ------------------------------------------------------------------ #
    def _attempt(self, system: str, user: str, json_schema: dict) -> dict:
        """One full attempt: build the request, parse the response, meter usage.

        Since Phase 17 B-4 (T20): metering runs **before** parsing so a response
        that fails to parse is still billed toward K6; truncation (``finish_reason ==
        "length"``) on top of a parse failure is surfaced as a non-transient
        :class:`LLMResponseError` — the retry path cannot fix a token-budget-cutoff.
        """
        schema_instruction = (
            "Respond with a single JSON object matching exactly this JSON Schema "
            f"— no prose, no markdown fence:\n{json.dumps(json_schema)}"
        )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": f"{system}\n\n{schema_instruction}"},
                {"role": "user", "content": user},
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "response_format": {"type": "json_object"},
        }
        body = self._raw_call(payload)
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

        text = _strip_fences(choice["message"]["content"])
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
