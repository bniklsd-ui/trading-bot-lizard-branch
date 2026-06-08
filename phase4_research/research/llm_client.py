"""The single AI call site of the whole bot — ``LLMClient.ask_candidate``.

This module is **the only place** that talks to an LLM (root CLAUDE.md
Bauprinzip; concept Decision 3). Everything else in Phase 4 is deterministic
code. The LLM answers exactly one question — "which candidate?" — and its raw
output is then run through the independent validator + deterministic filter
before it can ever influence an order.

## Which way we call the model (billing)

We use the Anthropic **Messages API** only: one ``client.messages.create`` per
research cycle, billed purely per token. We deliberately do **not** use Managed
Agents or any server-side tool (code execution / web search) — those add a
hosted agent loop + per-session container charge on top of tokens. All non-AI
work (context build, validation, filter, persistence) is our own code, so the
only thing that ever bills is this one call's input+output tokens. The token
meter records exactly that.

## Structured Outputs (primary) + manual fallback

Primary path uses Anthropic Structured Outputs via
``output_config={"format": {"type": "json_schema", "schema": <dynamic schema>}}``
— the schema is built per-run by ``prompt.build_prompt`` with the real epic list
as an ``enum``, so the model literally cannot emit an out-of-universe epic at the
decoding layer. (The older top-level ``output_format`` request parameter is
deprecated API-wide; ``output_config.format`` is the canonical form.) If the
structured call fails structurally (HTTP 400), we fall back to a plain call and
fence-strip + ``json.loads`` the text. **The validator runs independently and
always** regardless of which path produced the dict.

## Request-surface note (recent model changes)

Opus 4.7 / 4.8 reject sampling parameters (``temperature`` / ``top_p`` /
``top_k``) and ``budget_tokens`` with HTTP 400. The default model
(``claude-sonnet-4-6``) still accepts ``temperature``. ``_supports_sampling``
omits ``temperature`` for Opus-class models so the client is correct whatever
the config names. Extended thinking is **off** by default (the deterministic
choice — it also preserves the small ``max_tokens`` budget for the answer);
``enable_thinking=True`` sends ``thinking={"type": "adaptive"}``.

## Caching: intentionally not used

The call runs once per ~30-min cycle (longer than the 5-minute cache TTL) and
the system prompt sits below the per-model minimum cacheable prefix, so prompt
caching would only ever pay the write premium for no read. The meter still reads
the cache usage fields (they stay 0).

## Retry (Decision 8) — exactly 1, transient only

The SDK's own auto-retry is disabled (``max_retries=0``) so this client owns the
policy. We retry **once** on a *transient* fault: network / timeout / 5xx / rate
limit / JSON parse failure. We do **not** retry a valid content answer (including
``{"abstain": true}``) or a config-level error (400 bad request / auth). Any
final failure raises :class:`LLMResponseError`, which the orchestrator (Step 7)
turns into ``save_candidates([])`` — never a fabricated candidate.

## Testability

``anthropic`` is imported **lazily, inside ``_raw_call``** — the one mockable
call site (the Phase-3 ``_raw_download`` analogue). Faults are classified **by
class name** (the codebase's phase-isolation pattern, cf. Phase-3
``_is_rate_limit_error`` and the Step-3 ``EpicNotMappedError`` guard), so the
unit run never imports the SDK. Unit tests monkeypatch ``_raw_call`` /
``_build_create_kwargs`` and never touch the network.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from research import token_meter
from research.models import LLMResponseError, ResearchConfig

log = logging.getLogger(__name__)

# Models that reject sampling parameters (temperature/top_p/top_k) and
# budget_tokens with HTTP 400. Matched as substrings of the model id so future
# Opus 4.7+/4.8+ point releases are covered without an exhaustive list.
_NO_SAMPLING_MODEL_MARKERS = ("opus-4-7", "opus-4-8")

# SDK exception class names that count as *transient* (retry once). Matched by
# name so this module never imports ``anthropic`` (phase isolation / SDK-free
# unit run) — the same by-class-name guard Phase 3 uses for rate-limit errors.
_TRANSIENT_EXC_NAMES = frozenset(
    {
        "APIConnectionError",
        "APITimeoutError",
        "RateLimitError",
        "InternalServerError",
        "OverloadedError",
    }
)


def _supports_sampling(model: str) -> bool:
    """Whether ``model`` accepts ``temperature`` & co. (False for Opus 4.7/4.8)."""
    return not any(marker in model for marker in _NO_SAMPLING_MODEL_MARKERS)


def _status_code(exc: BaseException) -> int | None:
    """Best-effort HTTP status of an SDK exception (``status_code`` attr)."""
    code = getattr(exc, "status_code", None)
    return code if isinstance(code, int) else None


def _is_transient(exc: BaseException) -> bool:
    """Classify a fault as transient (network / timeout / 5xx / 429).

    Recognises stdlib ``ConnectionError`` / ``TimeoutError`` (so tests can drive
    the retry path without the SDK), the named SDK transient exceptions, and any
    exception carrying a 429 / ≥500 ``status_code``.
    """
    if isinstance(exc, (ConnectionError, TimeoutError)):
        return True
    if type(exc).__name__ in _TRANSIENT_EXC_NAMES:
        return True
    code = _status_code(exc)
    return code is not None and (code == 429 or code >= 500)


def _is_bad_request(exc: BaseException) -> bool:
    """Classify a fault as a 400 bad request (→ structured-output fallback)."""
    if type(exc).__name__ == "BadRequestError":
        return True
    return _status_code(exc) == 400


def _strip_fences(text: str) -> str:
    """Strip a Markdown ```json … ``` (or bare ``` … ```) fence if present.

    The structured path returns clean JSON; this only matters on the fallback
    path, where a plain completion may wrap the JSON in a code fence.
    """
    s = text.strip()
    if s.startswith("```"):
        first_newline = s.find("\n")
        if first_newline != -1:
            s = s[first_newline + 1 :]
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3]
    return s.strip()


def _extract_text(message: Any) -> str:
    """Concatenate the ``text`` blocks of an Anthropic ``Message``.

    Reads ``message.content`` (a list of blocks); keeps blocks whose ``type`` is
    ``"text"``. Raises ``ValueError`` if no text is present — treated as a parse
    failure by the caller (transient → eligible for the single retry).
    """
    content = getattr(message, "content", None) or []
    parts = [
        getattr(block, "text", "")
        for block in content
        if getattr(block, "type", None) == "text"
    ]
    text = "".join(parts).strip()
    if not text:
        raise ValueError("no text block in LLM response")
    return text


class LLMClient:
    """Thin wrapper around the Anthropic Messages API for the single pick call."""

    def __init__(
        self,
        model: str,
        api_key: str,
        *,
        max_tokens: int,
        temperature: float,
        timeout_s: float,
        token_meter_path: str | None = None,
        config: ResearchConfig | None = None,
        enable_thinking: bool = False,
    ) -> None:
        """Configure the client (no network call here — the SDK is lazy-built).

        Args:
            model: Anthropic model id (e.g. ``claude-sonnet-4-6``).
            api_key: Anthropic API key (resolved from the keyring by wiring in
                Step 8 — never read from a file).
            max_tokens / temperature / timeout_s: decoding + transport knobs.
                ``temperature`` is dropped automatically for models that reject
                it (Opus 4.7/4.8).
            token_meter_path: where the meter appends usage records; ``None``
                disables the file write (the meter still computes the record).
            config: a :class:`ResearchConfig` supplying pricing for the meter;
                defaults to ``ResearchConfig()`` if not given.
            enable_thinking: send adaptive thinking when ``True`` (off by
                default — see module docstring).
        """
        self.model = model
        self._api_key = api_key
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout_s = timeout_s
        self.token_meter_path = token_meter_path
        self.config = config if config is not None else ResearchConfig()
        self.enable_thinking = enable_thinking
        self._client: Any = None  # lazily built inside _raw_call

    # ------------------------------------------------------------------ #
    # Request construction (pure — directly unit-testable, SDK-free)      #
    # ------------------------------------------------------------------ #
    def _build_create_kwargs(
        self, system: str, user: str, *, json_schema: dict | None
    ) -> dict[str, Any]:
        """Build the ``messages.create`` kwargs (no SDK call, no network).

        Sampling params are included only when the model accepts them; thinking
        and the structured-output ``output_config`` are added conditionally.
        Factored out so the request surface (esp. the Opus sampling-param drop)
        can be asserted without touching the SDK.
        """
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        if _supports_sampling(self.model):
            kwargs["temperature"] = self.temperature
        if self.enable_thinking:
            kwargs["thinking"] = {"type": "adaptive"}
        if json_schema is not None:
            kwargs["output_config"] = {
                "format": {"type": "json_schema", "schema": json_schema}
            }
        return kwargs

    # ------------------------------------------------------------------ #
    # The one mockable raw call site (Phase-3 ``_raw_download`` analogue) #
    # ------------------------------------------------------------------ #
    def _raw_call(self, system: str, user: str, *, json_schema: dict | None) -> Any:
        """Issue one Messages API request and return the raw ``Message``.

        This is the **only** method that imports / touches ``anthropic``. Unit
        tests monkeypatch it. When ``json_schema`` is given, the request uses
        Structured Outputs (``output_config.format``); when ``None``, it is a
        plain completion (the fallback path). Raises whatever the SDK raises;
        the caller maps that to the retry policy.
        """
        import anthropic  # lazy: keeps unit tests SDK-free

        if self._client is None:
            # max_retries=0: this client owns the retry policy (Decision 8).
            self._client = anthropic.Anthropic(
                api_key=self._api_key,
                max_retries=0,
                timeout=self.timeout_s,
            )
        kwargs = self._build_create_kwargs(system, user, json_schema=json_schema)
        return self._client.messages.create(**kwargs)

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #
    def ask_candidate(self, system: str, user: str, json_schema: dict) -> dict:
        """Ask the model for one candidate; return the parsed (unvalidated) dict.

        Tries the structured path, then the fence-strip fallback, with exactly
        one retry on a transient fault across the whole attempt. The returned
        dict is **raw model output** — it has *not* been validated; the caller
        must run it through ``validate_candidate`` before trusting it.

        Args:
            system: System prompt (from ``prompt.build_prompt``).
            user: User message (from ``prompt.build_prompt``).
            json_schema: The dynamic Structured-Outputs schema (epic enum =
                real universe).

        Returns:
            The parsed JSON object (e.g. ``{"abstain": True, ...}`` or a pick).

        Raises:
            LLMResponseError: after the single retry is exhausted, or on a
                non-transient fault (bad request / auth).
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
                # Non-transient (bad request after fallback / auth) — no retry.
                raise LLMResponseError(f"LLM call failed: {exc!r}") from exc

        raise LLMResponseError(f"LLM call failed after retry: {last_exc!r}")

    # ------------------------------------------------------------------ #
    # Internals                                                          #
    # ------------------------------------------------------------------ #
    def _attempt(self, system: str, user: str, json_schema: dict) -> dict:
        """One full attempt: structured path, then in-attempt fence-strip fallback.

        A transient transport exception or a JSON parse failure propagates to
        ``ask_candidate`` (which may retry once). A **400 bad request** on the
        *structured* call is treated as "this model/SDK can't honor structured
        outputs" and triggers an in-attempt fallback to a plain call — it does
        **not** consume the retry. Any other exception propagates unchanged.
        """
        try:
            message = self._raw_call(system, user, json_schema=json_schema)
        except Exception as exc:  # noqa: BLE001 - classified by helper
            if _is_bad_request(exc):
                log.info(
                    "structured output rejected (%s) — falling back to plain call", exc
                )
                message = self._raw_call(system, user, json_schema=None)
            else:
                raise

        raw = json.loads(_strip_fences(_extract_text(message)))
        # Best-effort metering — never let a meter problem break the pick.
        try:
            token_meter.record(
                getattr(message, "usage", None),
                self.model,
                self.config,
                self.token_meter_path,
            )
        except Exception as exc:  # pragma: no cover - defensive
            log.warning("token_meter.record failed: %s", exc)
        return raw
