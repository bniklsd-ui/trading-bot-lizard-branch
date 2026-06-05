"""Prompt assembly — turns a ``ResearchContext`` into the LLM call's inputs.

``build_prompt`` is the last **code** step before the single AI call: it renders a
:class:`~research.models.ResearchContext` (Step 3) into the three pieces the LLM
client (Step 5) needs — ``(system, user, json_schema)``. **No AI touches this** (root
CLAUDE.md "Bauprinzip"); it only *prepares* the one AI call.

Two safety-relevant properties live here (concept §4):

1. **Delay honesty.** Phase-3 market data is ~15 min delayed (yFinance). The system
   prompt says so explicitly — it is a sentiment picture, **not** a real-time signal —
   and every indicator value is rendered verbatim: a ``None`` shows as an explicit
   "n/a", **never** faked to ``0``. The model is told to abstain when in doubt.
2. **Decoding-layer anti-hallucination.** The ``json_schema`` constrains ``epic`` to a
   **dynamic enum of exactly the real universe** (plus ``null``) and ``direction`` to the
   **already-clamped** allowed set (plus ``null``). This makes an out-of-universe epic or
   a clamp-violating direction impossible to *decode* — on top of the validator's
   independent, always-on guard (defense in depth).

Direction vocabulary is **BUY / SELL** only; there is no CALL/PUT anywhere.
"""

from __future__ import annotations

import logging
from typing import Any

from research.models import ResearchContext

log = logging.getLogger(__name__)

# How an unavailable (``None``) value is shown — honest, never a "0" fake.
_NA = "n/a"

_SYSTEM_PROMPT = (
    "You are the research analyst for a DAX intraday CFD trading bot. Your single "
    "job: from the list of tradeable instruments provided in the user message, pick "
    "AT MOST ONE to trade this session — or abstain.\n"
    "\n"
    "Hard rules:\n"
    "- Choose an instrument ONLY from the provided list. Never invent an epic.\n"
    "- direction is \"BUY\" or \"SELL\" only (this is a CFD bot — there are no "
    "options, no CALL/PUT).\n"
    "- The market data shown is ~15 minutes DELAYED. Treat it as a sentiment picture, "
    "NOT a real-time entry signal. Real-time checks happen later in code.\n"
    "- When in doubt, ABSTAIN. A skipped session is cheap; a bad trade is not.\n"
    "- Your confidence is a self-report and is advisory only — a deterministic filter "
    "and a live recheck run after you. Be honest, not persuasive.\n"
    "\n"
    "Respond in the required structured format: set abstain=true with reasoning to skip, "
    "or abstain=false with epic, direction, confidence (0-100) and reasoning to pick."
)


def _fmt(value: Any, *, suffix: str = "") -> str:
    """Render a value honestly: ``None`` → "n/a"; numbers keep their value.

    ``suffix`` (e.g. ``"%"``) is appended only to a present value, never to the
    ``None`` marker. This is the single choke point guaranteeing an unavailable
    indicator is shown as unavailable, not as ``0``.
    """
    if value is None:
        return _NA
    if isinstance(value, float):
        return f"{value:.2f}{suffix}"
    return f"{value}{suffix}"


def _render_market_state(brain_context: dict[str, Any] | None) -> str:
    """Render the delayed Phase-3 snapshot, or an explicit 'unavailable' note."""
    if brain_context is None:
        return "Market snapshot: unavailable (no delayed data for the anchor instrument)."

    bc = brain_context
    range_30d = bc.get("range_30d")
    if range_30d is None:
        range_txt = _NA
    else:
        range_txt = f"{_fmt(range_30d.get('low'))} – {_fmt(range_30d.get('high'))}"

    lines = [
        "Market snapshot (delayed ~15 min — sentiment, not real-time):",
        f"- ticker: {bc.get('ticker', _NA)}",
        f"- drift: {_fmt(bc.get('drift_pct'), suffix='%')}",
        f"- momentum 15m: {_fmt(bc.get('momentum_15m_pct'), suffix='%')} "
        f"(realtime={bc.get('momentum_is_realtime')})",
        f"- volume z-score: {_fmt(bc.get('volume_z_score'))} "
        f"(available={bc.get('volume_available')})",
        f"- distance to 30d high: {_fmt(bc.get('distance_to_high_pct'), suffix='%')}",
        f"- distance to 30d low: {_fmt(bc.get('distance_to_low_pct'), suffix='%')}",
        f"- 30d range: {range_txt}",
        f"- snapshot taken: {bc.get('generated_at', _NA)}",
    ]
    return "\n".join(lines)


def _render_trades(trades: list[dict[str, Any]]) -> str:
    """Render up to the last trades as a compact table (defensive ``.get()``)."""
    if not trades:
        return "Recent trades: none on record."
    rows = ["Recent trades (newest first):", "date | direction | epic | pnl | status"]
    for t in trades:
        date = t.get("session_date") or t.get("close_ts") or t.get("open_ts") or _NA
        rows.append(
            f"{date} | {t.get('direction', _NA)} | {t.get('epic', _NA)} | "
            f"{_fmt(t.get('profit_loss'))} | {t.get('status', _NA)}"
        )
    return "\n".join(rows)


def _render_lessons(lessons: list[dict[str, Any]]) -> str:
    """Render active lessons as ``lesson_text`` bullet lines."""
    if not lessons:
        return "Active lessons: none on record."
    rows = ["Active lessons:"]
    for lesson in lessons:
        rows.append(f"- {lesson.get('lesson_text', _NA)}")
    return "\n".join(rows)


def _render_universe(tradeable_epics: list[dict[str, Any]]) -> str:
    """Render the code-vetted tradeable instruments as a table."""
    if not tradeable_epics:
        return "Tradeable instruments: none right now (market closed / nothing tradeable)."
    rows = ["Tradeable instruments (pick at most one):", "epic | name | spread% | min_size"]
    for e in tradeable_epics:
        rows.append(
            f"{e.get('epic', _NA)} | {e.get('name', _NA)} | "
            f"{_fmt(e.get('spread_pct'), suffix='%')} | {_fmt(e.get('min_deal_size'))}"
        )
    return "\n".join(rows)


def _build_schema(
    epics: list[str], allowed_directions: tuple[str, ...]
) -> dict[str, Any]:
    """Build the Structured-Outputs JSON schema with dynamic epic/direction enums.

    ``epic`` is constrained to exactly the real universe (plus ``null``); an empty
    universe yields ``[None]`` (valid — the orchestrator abstains before calling
    the LLM, but the schema must never be malformed). ``direction`` reflects the
    already-applied long-bias clamp (BUY-only → ``["BUY", None]``).
    """
    return {
        "type": "object",
        "properties": {
            "abstain": {"type": "boolean"},
            "epic": {"type": ["string", "null"], "enum": [*epics, None]},
            "direction": {
                "type": ["string", "null"],
                "enum": [*allowed_directions, None],
            },
            "confidence": {
                "type": ["number", "null"],
                "minimum": 0,
                "maximum": 100,
            },
            "reasoning": {"type": "string"},
        },
        "required": ["abstain", "reasoning"],
        "additionalProperties": False,
    }


def build_prompt(
    context: ResearchContext,
    threshold: float,
    allowed_directions: tuple[str, ...],
) -> tuple[str, str, dict[str, Any]]:
    """Assemble the ``(system, user, json_schema)`` triple for the LLM call.

    Pure function — no I/O, no AI, no clock. ``threshold`` and
    ``allowed_directions`` arrive **already** resolved by ``candidate_filter``
    (Step 6): the confidence floor and the long-bias clamp are decided upstream;
    here they are only rendered (user message) and enforced on the decoding layer
    (schema ``direction`` enum).

    Args:
        context: The deterministic, code-built research context (Step 3).
        threshold: The required confidence floor to communicate to the model
            (advisory — the real gate is the deterministic filter).
        allowed_directions: The permitted directions after the clamp; reflected in
            both the user message and the schema ``direction`` enum.

    Returns:
        ``(system, user, json_schema)``: the static system prompt, the
        code-rendered user message, and the Structured-Outputs schema whose
        ``epic`` enum is exactly ``context.tradeable_epics`` (plus ``null``).
    """
    epics = [e["epic"] for e in context.tradeable_epics]

    directions_txt = " / ".join(allowed_directions) if allowed_directions else "none"
    decision_block = (
        "Decision context:\n"
        f"- bot score: {_fmt(context.bot_score)}\n"
        f"- risk level: {context.risk_level}\n"
        f"- required confidence floor: {_fmt(threshold)} "
        "(advisory self-report floor, not a probability)\n"
        f"- permitted directions: {directions_txt}"
    )

    user = "\n\n".join(
        [
            _render_market_state(context.brain_context),
            _render_trades(context.recent_trades),
            _render_lessons(context.recent_lessons),
            decision_block,
            _render_universe(context.tradeable_epics),
            "Answer format: respond with abstain, epic, direction, confidence, "
            "reasoning per the structured schema. epic must come from the list above; "
            f"direction must be one of [{directions_txt}].",
        ]
    )

    schema = _build_schema(epics, allowed_directions)

    log.info(
        "prompt built: %d epic(s) in schema enum, directions=%s, floor=%s",
        len(epics),
        allowed_directions,
        threshold,
    )
    return _SYSTEM_PROMPT, user, schema
