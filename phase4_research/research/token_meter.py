"""Token / cost meter — advisory usage logging for the single LLM call.

This is a **user addition** to Phase 4 (concept §"Token-Zähler"): after every
successful Anthropic response, the meter reads the response ``usage`` (token
counts + cache fields), prices it from :class:`research.models.ResearchConfig`
(per-model USD/Mtok + a USD→EUR estimate), and **appends** one record to
``data/state/llm_usage.json``.

It is **purely advisory**: the cost figures never gate a trade and a meter
failure must never break a research pick. Pricing is an estimate — the source
of truth is Anthropic's pricing page (see the caveat on
``ResearchConfig.pricing_usd_per_mtok``).

**Billing note (Bauprinzip in billing form):** Phase 4 calls only the Anthropic
**Messages API** — one ``POST /v1/messages`` per research cycle, billed purely
per token. We deliberately use neither Managed Agents nor server-side tools
(code execution / web search), which would add a hosted agent loop + per-session
container charge *on top of* tokens. So the only thing that ever bills is the
single classification call's input+output tokens — exactly what this meter
records. ``cache_creation_input_tokens`` / ``cache_read_input_tokens`` are read
for correctness but stay ``0`` (we do not cache — see ``llm_client`` for why).

Phase isolation: imports only ``research.models`` + ``research.timeutil`` +
stdlib. No ``anthropic`` / ``broker_wrapper`` / ``external_data`` /
``persistence`` import — the ``usage`` object is duck-typed (it only needs the
four token-count attributes).
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from research import timeutil
from research.models import ResearchConfig

log = logging.getLogger(__name__)

# Cost multipliers for cached tokens (Anthropic prompt-caching economics).
# Cache **reads** bill ~0.1× the base input rate; cache **writes** ~1.25×.
# These terms are included for correctness even though Phase 4 never caches
# (the call is too infrequent and the prompt too short — see ``llm_client``),
# so in practice both cache fields are 0 and these multipliers are inert.
_CACHE_WRITE_MULT = 1.25
_CACHE_READ_MULT = 0.1


def _usage_int(usage: Any, name: str) -> int:
    """Read an integer token field off a duck-typed ``usage`` object.

    Anthropic's ``usage`` exposes ``input_tokens`` / ``output_tokens`` always,
    and ``cache_creation_input_tokens`` / ``cache_read_input_tokens`` which may
    be ``None`` when caching is not in play. Missing or ``None`` → ``0``.
    """
    value = getattr(usage, name, None)
    return int(value) if value is not None else 0


def estimate_cost(
    usage: Any, model: str, config: ResearchConfig
) -> tuple[float, float]:
    """Estimate the USD and EUR cost of one response from its ``usage``.

    Args:
        usage: Anthropic ``usage`` object (or any object exposing
            ``input_tokens`` / ``output_tokens`` and, optionally,
            ``cache_creation_input_tokens`` / ``cache_read_input_tokens``).
        model: The model id the call used — selects the pricing row.
        config: Carries ``pricing_usd_per_mtok`` (per-model ``(in, out)`` USD per
            million tokens) and ``usd_to_eur``.

    Returns:
        ``(usd, eur)``. An **unknown model** (no pricing row) yields
        ``(0.0, 0.0)`` plus a stderr warning — an advisory log must never crash
        the pick just because pricing wasn't configured for a model.
    """
    pricing = config.pricing_usd_per_mtok.get(model)
    if pricing is None:
        log.warning("token_meter: no pricing for model %r — cost logged as 0", model)
        return (0.0, 0.0)

    in_per_mtok, out_per_mtok = pricing
    input_tokens = _usage_int(usage, "input_tokens")
    output_tokens = _usage_int(usage, "output_tokens")
    cache_write = _usage_int(usage, "cache_creation_input_tokens")
    cache_read = _usage_int(usage, "cache_read_input_tokens")

    usd = (
        input_tokens * in_per_mtok
        + cache_write * in_per_mtok * _CACHE_WRITE_MULT
        + cache_read * in_per_mtok * _CACHE_READ_MULT
        + output_tokens * out_per_mtok
    ) / 1_000_000.0
    eur = usd * config.usd_to_eur
    return (usd, eur)


def _load_log(path: str) -> list[dict[str, Any]]:
    """Load the existing usage-log array, tolerating absence / corruption.

    A missing file → empty list (first write). A corrupt / non-list file is
    logged and treated as empty rather than raising — the advisory log is not
    worth aborting a pick over.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("token_meter: could not read %s (%s) — starting fresh", path, exc)
        return []
    if not isinstance(data, list):
        log.warning("token_meter: %s is not a JSON array — starting fresh", path)
        return []
    return data


def record(
    usage: Any,
    model: str,
    config: ResearchConfig,
    path: str | None,
) -> dict[str, Any]:
    """Build a usage record and append it to the usage log.

    The record shape (CLAUDE.md "Token / cost meter") is:
    ``{ts, model, input_tokens, output_tokens, cache_read_input_tokens,
    cache_creation_input_tokens, est_cost_usd, est_cost_eur}``.

    The two ``cache_*`` fields were added **additively** for Phase 6 (Decision G):
    Phase 6 caches the stable debate prefix, so making the cache token counts
    visible in the log is what lets ``usage_report`` show a cache-hit ratio. They
    stay ``0`` for Phase 4 (which does not cache) — the older six-field consumers
    are unaffected (purely additive; old keys unchanged).

    Args:
        usage: The response ``usage`` object (duck-typed).
        model: Model id used for the call (also the pricing key).
        config: Pricing + FX source.
        path: Destination JSON file. ``None`` → **do not write** (still returns
            the record) — wiring (Step 8) resolves the real
            ``data/state/llm_usage.json`` path; unit tests pass a ``tmp_path`` or
            ``None`` to stay filesystem-free.

    Returns:
        The record dict (JSON-serialisable). Writing is best-effort: an I/O
        error is logged to stderr and swallowed — metering must never break a
        pick.
    """
    usd, eur = estimate_cost(usage, model, config)
    rec: dict[str, Any] = {
        "ts": timeutil.utc_iso_now(),
        "model": model,
        "input_tokens": _usage_int(usage, "input_tokens"),
        "output_tokens": _usage_int(usage, "output_tokens"),
        "cache_read_input_tokens": _usage_int(usage, "cache_read_input_tokens"),
        "cache_creation_input_tokens": _usage_int(usage, "cache_creation_input_tokens"),
        "est_cost_usd": round(usd, 6),
        "est_cost_eur": round(eur, 6),
    }
    if path is None:
        return rec

    try:
        records = _load_log(path)
        records.append(rec)
        # Phase 16 R6.3 / F6 (2026-09-22): write atomically (tmp + os.replace)
        # instead of truncating the real file in place. The log is a single
        # ~1 MB JSON array that is rewritten on EVERY call, so an in-place
        # ``open(path, "w")`` leaves a window in which a concurrent reader sees
        # a half-written array. That window was hit live: the WebUI logged 5
        # JSON-parse errors on llm_usage.json and then counted "0 tokens
        # today" — i.e. the token-budget gate (K6) can silently read 0.
        # ``os.replace`` is atomic within a filesystem, so a reader sees either
        # the old or the new array, never a truncated one. Same pattern as
        # ``scheduler/run.py`` ``_write_pid``.
        tmp_path = f"{path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(records, fh, indent=2)
            fh.write("\n")
        os.replace(tmp_path, path)
    except OSError as exc:
        log.warning("token_meter: could not append usage to %s (%s)", path, exc)
    return rec
