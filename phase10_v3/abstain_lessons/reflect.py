"""S4 — the single AI seam in this module: an optional LLM lesson-extraction call.

Mirrors the P7 ``reward/brain.py`` reflect pattern (best-effort, default off, never
raises to the caller). ``AbstainLLM`` is a thin ``Protocol`` — the real adapter
(wrapping ``research.llm_client.LLMClient``) is built in P8 wiring, not here, to keep
this module free of any cross-phase import (phase isolation, no network in tests).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Protocol

from abstain_lessons.exceptions import AbstainLessonError
from abstain_lessons.models import AbstainRecord

if TYPE_CHECKING:
    from abstain_lessons.paper import PaperTrade

logger = logging.getLogger("abstain_lessons.reflect")

# Phase-10 B5-fix (2026-07-31): both prompts below now state this limit explicitly
# (they used to only say "max two sentences", drifting from what validate_abstain_lesson
# actually enforces — 6 Haiku calls paid for, 4 rejected as too long on 2026-07-27).
_MAX_LESSON_CHARS = 300


class AbstainLLM(Protocol):
    """Duck-typed LLM boundary — a single free-text completion call."""

    def complete(self, prompt: str, timeout_s: float) -> str: ...


def build_abstain_prompt(record: AbstainRecord) -> str:
    """Deterministic prompt: asks for exactly one lesson, max two sentences, German."""
    return (
        "Ein Trading-Bot-Zyklus endete ohne Trade (NO_TRADE).\n"
        f"Stufe: {record.stage.value}\n"
        f"Grund: {record.reason.value}\n"
        f"Detail: {record.detail or '(keine weiteren Details)'}\n\n"
        "Formuliere GENAU EINE Lehre aus diesem Abstain, in maximal zwei Sätzen "
        f"und maximal {_MAX_LESSON_CHARS} Zeichen, auf Deutsch. Antworte nur mit "
        "der Lehre, ohne Einleitung."
    )


def build_paper_lesson_prompt(trade: "PaperTrade", sibling: "PaperTrade | None") -> str:
    """Deterministic prompt for a resolved paper trade — includes both shadow sides
    when available (``sibling`` is the opposite-direction shadow of the same
    abstain, WE 2's Both-Sides-Shadow-Tracking). Asks for one lesson, German."""
    lines = [
        "Ein simulierter (nie ausgeführter) Paper-Trade wurde aufgelöst.",
        f"Variante: {trade.variant.value}",
        f"Epic: {trade.epic}",
        f"Richtung: {trade.direction}",
        f"Ausstiegsgrund: {trade.exit_reason.value if trade.exit_reason else 'unbekannt'}",
        f"PnL (Punkte): {trade.pnl_points}",
        f"R-Multiple: {trade.r_multiple}",
    ]
    if sibling is not None:
        lines.append(
            f"Gegenseite ({sibling.direction}): Ausstiegsgrund="
            f"{sibling.exit_reason.value if sibling.exit_reason else 'unbekannt'}, "
            f"PnL (Punkte)={sibling.pnl_points}, R-Multiple={sibling.r_multiple}"
        )
    lines.append(
        "\nFormuliere GENAU EINE Lehre aus diesem simulierten Ergebnis, in maximal "
        f"zwei Sätzen und maximal {_MAX_LESSON_CHARS} Zeichen, auf Deutsch. "
        "Antworte nur mit der Lehre, ohne Einleitung."
    )
    return "\n".join(lines)


# An over-long lesson is only salvaged if trimming to whole sentences leaves at least
# this much text. Below it we are no longer shortening a lesson, we are inventing a
# different (shorter, possibly meaning-inverted) one — better to keep none.
_MIN_SALVAGED_LESSON_CHARS = 150

_SENTENCE_ENDINGS = (". ", "! ", "? ")


def _trim_to_sentence(text: str, limit: int) -> str | None:
    """Longest prefix of ``text`` that ends on a sentence boundary within ``limit``.

    ``None`` when no boundary exists in range — the caller must then reject rather than
    cut mid-sentence. A lesson truncated mid-clause can read as the opposite of what the
    model meant ("BUY nach Drift war nicht schlecht" → "BUY nach Drift war nicht"), and a
    silently inverted lesson is worse in the prompt than a missing one.

    **Known limitation, stated rather than papered over:** this keeps the *head* of the
    text, so a lesson whose actionable part is trailing loses it and still reads as a
    grammatical sentence. That shape is real — all four lessons on record put the
    conclusion last ("…, was auf sauberes Risikomanagement hindeutet — überprüfe …"). It
    is not measurable here: the 10 over-long texts from the 08-03/07 week were never
    stored, only their rejection was. Whoever reviews the first trimmed lessons should
    check specifically for a missing conclusion. Salvage still beats the current zero;
    the claim is "better than nothing", not "quality preserved".
    """
    window = text[: limit + 1]
    cut = max((window.rfind(end) for end in _SENTENCE_ENDINGS), default=-1)
    if cut == -1:
        # A single sentence ending exactly at the limit has no trailing space to find.
        if len(text) > limit and text[limit - 1] in ".!?":
            return text[:limit].strip()
        return None
    return text[: cut + 1].strip()


def validate_abstain_lesson(text: str) -> str:
    """Strip + validate a lesson string: non-empty, <=300 chars, single-line.

    Over-long text is **salvaged, not rejected** (B5 residual, 2026-08-08): the 300-char
    limit is stated in the prompt, but the model still overshot on 10 of 68 attempts in
    the 08-03/07 week (321-382 chars), and each of those produced **no lesson at all**.
    Trimming to the last whole sentence under the limit recovers a coherent lesson where
    the alternative is silence — strictly better, as long as the trim never manufactures
    a meaning the model did not write. Two guards enforce that: the cut must land on a
    sentence boundary, and what survives must still be substantial
    (``_MIN_SALVAGED_LESSON_CHARS``). Failing either, the old rejection stands.

    Text already within the limit is returned byte-identical — the 58 of 68 that were
    fine are untouched by this path.

    Raises:
        AbstainLessonError: the text is empty, spans multiple lines, or is too long and
            cannot be trimmed to a whole sentence with enough substance left.
    """
    stripped = text.strip()
    if not stripped:
        raise AbstainLessonError("lesson text is empty")
    if "\n" in stripped:
        raise AbstainLessonError("lesson text must be a single line")
    if len(stripped) > _MAX_LESSON_CHARS:
        salvaged = _trim_to_sentence(stripped, _MAX_LESSON_CHARS)
        if salvaged is None or len(salvaged) < _MIN_SALVAGED_LESSON_CHARS:
            raise AbstainLessonError(
                f"lesson text too long ({len(stripped)} > {_MAX_LESSON_CHARS} chars) "
                "and not trimmable to a whole sentence"
            )
        logger.warning(
            "lesson text trimmed from %d to %d chars at a sentence boundary",
            len(stripped), len(salvaged),
        )
        return salvaged
    return stripped


def reflect_abstain(
    record: AbstainRecord, llm: AbstainLLM | None = None, timeout_s: float = 20.0
) -> str | None:
    """Best-effort lesson extraction. ``llm=None`` -> ``None`` immediately (no call).

    Any failure (LLM exception, validation failure, timeout) is logged ``critical``
    and returns ``None`` — this function never raises to its caller.
    """
    if llm is None:
        return None
    try:
        raw = llm.complete(build_abstain_prompt(record), timeout_s)
        return validate_abstain_lesson(raw)
    except Exception as exc:  # noqa: BLE001 — best-effort, must never crash the cycle
        logger.critical("reflect_abstain failed for %s: %s", record.record_id, exc)
        return None
