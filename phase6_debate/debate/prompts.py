"""Module 3 — prompt assembly for the Bull / Bear / Judge debate.

This is the **last code step before the AI requests**: it renders a frozen
:class:`~debate.models.DebateContext` plus the running transcript into the
``(system, user, json_schema)`` triple each agent's turn needs. **No AI touches
this** (root CLAUDE.md "Bauprinzip") — it only *prepares* the requests. Mirrors
the Phase-4 ``research.prompt`` convention (same shape, same Anthropic
Structured-Outputs schema rules).

Two design properties matter here (concept §3, Decision D):

1. **Cache-prefix discipline.** The system block carries the role instructions
   **and** the rendered context — both stable for the whole debate — so Module 4's
   ``cache_control`` marker on the system block reads cache on every later turn.
   Only the **growing transcript** varies, so it lives in the ``user`` part. Keep
   it that way: context in ``system``, transcript in ``user``.
2. **Delay honesty.** The seed fields (``seed_*`` / ``drift_at_pick``) come from
   Phase 4's ~15 min delayed yFinance picture; ``spread_pct`` /
   ``recent_bars_summary`` are IG real-time. The prompts say so explicitly so the
   agents weight them correctly. Every ``None`` renders as an honest "n/a", never
   a faked 0 (single ``_fmt`` choke point).

The prompts are German (concept §3). Direction vocabulary is **BUY / SELL** only —
there is no options terminology anywhere (this is a DAX CFD bot). ``confidence`` is
advisory only (Decision H) and gates nothing; its 0-100 range is communicated in
prose, not enforced in the schema (Structured Outputs rejects numeric bounds).
"""

from __future__ import annotations

import logging
from typing import Any, Mapping

from debate.models import AgentTurn, DebateContext

log = logging.getLogger(__name__)

# How an unavailable (``None``) value is shown — honest, never a "0" fake.
_NA = "n/a"


# --------------------------------------------------------------------------- #
# System prompts (German, role-specific, stable across the whole debate)       #
# --------------------------------------------------------------------------- #

_BULL_SYSTEM = (
    "Du bist der BULL-Analyst in einer kontradiktorischen Trading-Debatte für "
    "einen DAX-Intraday-CFD-Bot. Deine Aufgabe: das stärkste, ehrliche Argument "
    "für eine LONG-Position (Richtung BUY) auf dem genannten Instrument bringen.\n"
    "\n"
    "Regeln:\n"
    "- Richtung ist ausschließlich \"BUY\" oder \"SELL\" (CFD-Bot, keine Optionen).\n"
    "- Argumentiere für BUY, aber bleibe redlich: erfinde keine Zahlen, beziehe "
    "dich nur auf den bereitgestellten Kontext und das bisherige Transkript.\n"
    "- Beachte die Datenherkunft: die Seed-/Drift-Felder aus Phase 4 sind ein "
    "VERZÖGERTES Stimmungsbild (yFinance, ~15 min); Spread und die jüngsten Bars "
    "sind IG-ECHTZEIT. Gewichte Echtzeit höher als verzögerte Stimmung.\n"
    "- Antworte knapp und sachlich im geforderten strukturierten Format "
    "(Feld \"argument\")."
)

_BEAR_SYSTEM = (
    "Du bist der BEAR-Analyst in einer kontradiktorischen Trading-Debatte für "
    "einen DAX-Intraday-CFD-Bot. Deine Aufgabe: das stärkste, ehrliche Argument "
    "für eine SHORT-Position (Richtung SELL) auf dem genannten Instrument bringen.\n"
    "\n"
    "Regeln:\n"
    "- Richtung ist ausschließlich \"BUY\" oder \"SELL\" (CFD-Bot, keine Optionen).\n"
    "- Argumentiere für SELL, aber bleibe redlich: erfinde keine Zahlen, beziehe "
    "dich nur auf den bereitgestellten Kontext und das bisherige Transkript.\n"
    "- Beachte die Datenherkunft: die Seed-/Drift-Felder aus Phase 4 sind ein "
    "VERZÖGERTES Stimmungsbild (yFinance, ~15 min); Spread und die jüngsten Bars "
    "sind IG-ECHTZEIT. Gewichte Echtzeit höher als verzögerte Stimmung.\n"
    "- Antworte knapp und sachlich im geforderten strukturierten Format "
    "(Feld \"argument\")."
)

_JUDGE_SYSTEM = (
    "Du bist der RICHTER (Judge) in einer kontradiktorischen Trading-Debatte für "
    "einen DAX-Intraday-CFD-Bot. Du argumentierst nicht selbst — du wägst die "
    "Bull- und Bear-Argumente gegen den Kontext ab und entscheidest.\n"
    "\n"
    "Du bist die echte Richtungsquelle: Deine finale Richtung darf vom Phase-4-Seed "
    "abweichen (Gegenrichtung BUY↔SELL ist erlaubt, wenn die Argumente sie "
    "rechtfertigen). Der Seed ist nur ein Vorschlag.\n"
    "\n"
    "Regeln:\n"
    "- Richtung ist ausschließlich \"BUY\" oder \"SELL\" (CFD-Bot, keine Optionen).\n"
    "- Im Zweifel ABSTAIN. Eine ausgelassene Sitzung ist billig; ein schlechter "
    "Trade nicht.\n"
    "- Datenherkunft beachten: Seed/Drift aus Phase 4 sind ~15 min VERZÖGERT; "
    "Spread und jüngste Bars sind IG-ECHTZEIT.\n"
    "- Antworte strukturiert: \"decision\" (TRADE oder ABSTAIN), \"direction\" "
    "(BUY/SELL bei TRADE, null bei ABSTAIN), \"confidence\" (0-100, reine "
    "Selbsteinschätzung — sie steuert NICHTS und ist nur advisory), \"rationale\" "
    "(deine Begründung) und \"conclude\" (true, wenn die Debatte entschieden ist "
    "und keine weitere Runde nötig ist; sonst false)."
)


# --------------------------------------------------------------------------- #
# Rendering helpers (mirror the Phase-4 ``_fmt`` / ``_render_*`` choke points) #
# --------------------------------------------------------------------------- #


def _fmt(value: Any, *, suffix: str = "") -> str:
    """Render a value honestly: ``None`` → "n/a"; numbers keep their value.

    ``suffix`` (e.g. ``"%"``) is appended only to a present value, never to the
    ``None`` marker — the single choke point guaranteeing an unavailable field is
    shown as unavailable, not as ``0`` (identical to Phase-4 ``prompt._fmt``).
    """
    if value is None:
        return _NA
    if isinstance(value, float):
        return f"{value:.2f}{suffix}"
    return f"{value}{suffix}"


def _render_context(context: DebateContext) -> str:
    """Render the read-only context block — stable for the whole debate.

    Lives in the **system** message so it forms the cacheable prefix (Decision D).
    Splits the data honestly into a DELAYED Phase-4 sentiment part and an
    IG-REAL-TIME part so the agents weight them correctly.
    """
    lines = [
        "Kontext (read-only, von Code zusammengestellt):",
        f"- Instrument (epic): {context.epic}",
        "",
        "Phase-4-Seed — VERZÖGERTES Stimmungsbild (yFinance, ~15 min Verzögerung; "
        "nur Vorschlag, advisory):",
        f"- Seed-Richtung (Vorschlag): {context.seed_direction}",
        f"- Seed-Confidence (advisory, steuert nichts): "
        f"{_fmt(context.seed_confidence)}",
        f"- Seed-Begründung: {context.seed_reasoning}",
        f"- Drift bei der Auswahl: {_fmt(context.drift_at_pick, suffix='%')}",
        f"- Bot-Score bei der Auswahl: {_fmt(context.score_at_pick)}",
        "",
        "Live-Marktbild — IG-ECHTZEIT (höher gewichten):",
        f"- Spread: {_fmt(context.spread_pct, suffix='%')}",
        f"- Marktstatus: {context.market_status}",
        f"- Jüngste Bars: {context.recent_bars_summary}",
        f"- Kontext erstellt um: {context.generated_at}",
    ]
    return "\n".join(lines)


def _render_transcript(transcript: list[AgentTurn]) -> str:
    """Serialise the debate so far, in order, into the (growing) user message."""
    if not transcript:
        return "Bisheriges Transkript: noch keine Argumente (erste Runde)."
    rows = ["Bisheriges Transkript (älteste zuerst):"]
    for turn in transcript:
        rows.append(f"Runde {turn.round} · {turn.agent}: {turn.text}")
    return "\n".join(rows)


# --------------------------------------------------------------------------- #
# Schemas (fresh dicts per request — no shared mutable; Anthropic-safe shape)  #
# --------------------------------------------------------------------------- #


def _arg_schema() -> dict[str, Any]:
    """Minimal Bull/Bear Structured-Outputs schema: one ``argument`` string.

    The arguers only produce an argument — the Judge decides direction and
    TRADE/ABSTAIN (so wenig AI-Struktur wie möglich).
    """
    return {
        "type": "object",
        "properties": {"argument": {"type": "string"}},
        "required": ["argument"],
        "additionalProperties": False,
    }


def _judge_schema() -> dict[str, Any]:
    """Judge Structured-Outputs schema (concept §3).

    Nullable ``direction`` / ``confidence`` use ``anyOf`` with a ``{"type":
    "null"}`` branch — **not** a type-array union (Anthropic Structured Outputs
    400s on ``{"type": ["string", "null"]}``; see Phase-4 ``prompt._build_schema``).
    ``confidence`` carries **no** ``minimum``/``maximum`` (Structured Outputs
    rejects numeric bounds); the 0-100 range is stated in the prompt prose, and
    ``confidence`` is advisory-only (Decision H) — it gates nothing regardless.
    ``direction`` is ``null`` on ABSTAIN.
    """
    return {
        "type": "object",
        "properties": {
            "decision": {"type": "string", "enum": ["TRADE", "ABSTAIN"]},
            "direction": {
                "anyOf": [
                    {"type": "string", "enum": ["BUY", "SELL"]},
                    {"type": "null"},
                ]
            },
            "confidence": {"anyOf": [{"type": "number"}, {"type": "null"}]},
            "rationale": {"type": "string"},
            "conclude": {"type": "boolean"},
        },
        "required": ["decision", "direction", "confidence", "rationale", "conclude"],
        "additionalProperties": False,
    }


# --------------------------------------------------------------------------- #
# Public builders                                                              #
# --------------------------------------------------------------------------- #


def _build_arg_prompt(
    role_system: str, context: DebateContext, transcript: list[AgentTurn], directive: str
) -> tuple[str, str, dict[str, Any]]:
    """Shared assembly for the two arguers (Bull/Bear differ only in role text)."""
    system = role_system + "\n\n" + _render_context(context)
    user = _render_transcript(transcript) + "\n\n" + directive
    return system, user, _arg_schema()


def build_bull_prompt(
    context: DebateContext, transcript: list[AgentTurn]
) -> tuple[str, str, dict[str, Any]]:
    """Assemble the ``(system, user, json_schema)`` triple for a Bull turn."""
    return _build_arg_prompt(
        _BULL_SYSTEM,
        context,
        transcript,
        "Du bist jetzt am Zug. Bringe dein stärkstes Argument für BUY im "
        "geforderten Schema (Feld \"argument\").",
    )


def build_bear_prompt(
    context: DebateContext, transcript: list[AgentTurn]
) -> tuple[str, str, dict[str, Any]]:
    """Assemble the ``(system, user, json_schema)`` triple for a Bear turn."""
    return _build_arg_prompt(
        _BEAR_SYSTEM,
        context,
        transcript,
        "Du bist jetzt am Zug. Bringe dein stärkstes Argument für SELL im "
        "geforderten Schema (Feld \"argument\").",
    )


def build_judge_prompt(
    context: DebateContext, transcript: list[AgentTurn]
) -> tuple[str, str, dict[str, Any]]:
    """Assemble the ``(system, user, json_schema)`` triple for a Judge turn."""
    system = _JUDGE_SYSTEM + "\n\n" + _render_context(context)
    user = (
        _render_transcript(transcript)
        + "\n\n"
        + "Du bist jetzt am Zug. Wäge die Argumente ab und antworte im "
        "geforderten Schema (decision, direction, confidence, rationale, conclude)."
    )
    return system, user, _judge_schema()


# --------------------------------------------------------------------------- #
# Council-Paper-Call (Phase-10 V3, §10.3) — additive sibling, zero diff above  #
# --------------------------------------------------------------------------- #
#
# A single-shot forced-pick variant of the Judge, used only by
# ``abstain_lessons.paper.PaperDebateCaller`` (never on the live order path — that
# caller has no broker access to build a full ``DebateContext``/run Bull-Bear
# rounds; it is triggered post-hoc from an already-recorded debate-abstain). The
# live ``build_judge_prompt``/``_judge_schema`` above are untouched.

_PAPER_PICK_SYSTEM = (
    "Du bist der RICHTER (Judge) in einer Trading-Entscheidung für einen "
    "DAX/Index-Intraday-CFD-Bot.\n"
    "\n"
    "PAPER-MODUS: kein echtes Geld, keine echte Order — dies ist ein rein "
    "virtueller Test. ABSTAIN ist nicht verfügbar: wähle BUY oder SELL und "
    "begründe deine Wahl in einem Satz.\n"
    "\n"
    "Regeln:\n"
    "- Richtung ist ausschließlich \"BUY\" oder \"SELL\" (CFD-Bot, keine Optionen).\n"
    "- \"confidence\" (0-100, reine Selbsteinschätzung — steuert nichts, rein "
    "advisory).\n"
    "- \"rationale\": genau ein Satz."
)


def _paper_pick_schema() -> dict[str, Any]:
    """Forced-pick Structured-Outputs schema — no ABSTAIN branch (contrast
    :func:`_judge_schema`, which keeps it): ``direction`` is required, not
    nullable."""
    return {
        "type": "object",
        "properties": {
            "direction": {"type": "string", "enum": ["BUY", "SELL"]},
            "confidence": {"anyOf": [{"type": "number"}, {"type": "null"}]},
            "rationale": {"type": "string"},
        },
        "required": ["direction", "confidence", "rationale"],
        "additionalProperties": False,
    }


def build_paper_pick_prompt(digest: Mapping[str, Any]) -> tuple[str, str, dict[str, Any]]:
    """Single-shot forced-pick prompt for the Council-Paper-Call (plan §10.3).

    Takes a thin ``candidate_digest`` (``epic`` + a fresh ``bid``/``ask`` — not a
    full :class:`~debate.models.DebateContext`: ``PaperEngine`` has no broker
    context-builder access, only the one quote it's already sanctioned to fetch
    for the shadow pair) instead of a full debate round. No transcript — one shot.
    """
    lines = ["Kontext (read-only):", f"- Instrument (epic): {digest.get('epic')}"]
    bid, ask = digest.get("bid"), digest.get("ask")
    if bid is not None or ask is not None:
        lines.append(f"- Aktueller Kurs: bid={_fmt(bid)} ask={_fmt(ask)}")
    system = _PAPER_PICK_SYSTEM + "\n\n" + "\n".join(lines)
    user = (
        "Triff jetzt deine Wahl im geforderten Schema (direction, confidence, "
        "rationale)."
    )
    return system, user, _paper_pick_schema()
