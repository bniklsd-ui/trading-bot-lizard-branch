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

    The record shape is frozen (CLAUDE.md "Token / cost meter"):
    ``{ts, model, input_tokens, output_tokens, est_cost_usd, est_cost_eur}``.

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
        "est_cost_usd": round(usd, 6),
        "est_cost_eur": round(eur, 6),
    }
    if path is None:
        return rec

    try:
        records = _load_log(path)
        records.append(rec)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(records, fh, indent=2)
            fh.write("\n")
    except OSError as exc:
        log.warning("token_meter: could not append usage to %s (%s)", path, exc)
    return rec
