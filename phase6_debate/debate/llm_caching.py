"""Module 4 — the cached single request point for one debate turn.

Phase 6 is the **most expensive path in the bot**, so cost correctness counts as
much as function. This module is the thin Phase-6 seam over the **shared** Phase-4
``research.LLMClient`` (the documented Decision-F cross-phase reuse — there is no
second LLM request site, no premature ``llm_common`` extraction). It does **not**
re-implement the request; it configures the one shared client for a role's turn
and hands back the parsed answer plus the per-turn usage record the budget meter
(Module 5) aggregates.

The two enabling edits live in the Phase-4 code (additive, Decision F/G; Phase-4
default behaviour is unchanged because both default off):

- ``research.llm_client.LLMClient(cache_system=...)`` + ``_build_create_kwargs``
  set a ``cache_control: {"type":"ephemeral"}`` marker on the stable system block
  (the role instructions + frozen context — see ``prompts.py``), so every later
  turn of a role reads that prefix from cache instead of re-billing it.
- ``research.token_meter.record`` now also logs ``cache_read_input_tokens`` /
  ``cache_creation_input_tokens`` so the cache work is **visible** (otherwise the
  most expensive optimisation of the phase would be invisible). ``LLMClient``
  captures that record on ``last_usage`` per request.

This module holds **no AI logic** — the AI is the model; here we only marshal the
request and read back the usage. Imports only ``debate.models`` + stdlib; the
shared client is duck-typed via a ``Protocol`` (no ``anthropic`` import — the
client lazy-imports the SDK itself, only on a real request).
"""

from __future__ import annotations

import logging
from typing import Any, Protocol

from debate.models import DebateLLMError

log = logging.getLogger(__name__)


class _LLMClientLike(Protocol):
    """The slice of ``research.LLMClient`` a debate turn needs.

    Duck-typed so the unit tests can supply a fake and this module never imports
    ``anthropic`` / ``research`` directly. The shared client must already be
    constructed with ``cache_system=True`` (done by wiring, Module 8).
    """

    model: str
    temperature: float
    last_usage: dict[str, Any] | None

    def ask_candidate(self, system: str, user: str, json_schema: dict) -> dict: ...


def ask_agent(
    client: _LLMClientLike,
    system: str,
    user: str,
    json_schema: dict[str, Any],
    *,
    model: str,
    temperature: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run one Bull/Bear/Judge turn on the shared client; return (answer, usage).

    The debate uses **one** shared client for all three roles (max cache reuse,
    one SDK connection); the per-role ``model`` and ``temperature`` are applied
    here for this turn. Caching is governed by the client's ``cache_system`` flag
    (set ``True`` at construction), not per request — so the stable system+context
    prefix is the cached part.

    Args:
        client: the shared ``research.LLMClient`` (built with ``cache_system=True``).
        system: the stable role+context system block (from ``prompts``).
        user: the growing transcript message (from ``prompts``).
        json_schema: the role's Structured-Outputs schema (from ``prompts``).
        model: the model id for this role (e.g. Haiku for Bull/Bear, Sonnet Judge).
        temperature: the decoding temperature for this role.

    Returns:
        ``(answer, usage)`` — the parsed (unvalidated) model dict, and the token
        meter record for this turn (``input_tokens`` / ``output_tokens`` /
        ``cache_read_input_tokens`` / ``cache_creation_input_tokens`` / costs) for
        the budget meter. ``usage`` is ``{}`` if the client captured none.

    Raises:
        DebateLLMError: the shared client failed unrecoverably (after its own
            single transient retry). The orchestrator converts this to a
            fail-closed ABSTAIN — never a fabricated turn (Decision J).
    """
    client.model = model
    client.temperature = temperature
    try:
        answer = client.ask_candidate(system, user, json_schema)
    except Exception as exc:  # noqa: BLE001 — any client failure → fail-closed
        log.warning("ask_agent: shared client failed for model %s: %s", model, exc)
        raise DebateLLMError(f"agent request failed ({model}): {exc!r}") from exc

    usage = client.last_usage or {}
    return answer, usage
