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
        "Formuliere GENAU EINE Lehre aus diesem Abstain, in maximal zwei Sätzen, "
        "auf Deutsch. Antworte nur mit der Lehre, ohne Einleitung."
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
        "zwei Sätzen, auf Deutsch. Antworte nur mit der Lehre, ohne Einleitung."
    )
    return "\n".join(lines)


def validate_abstain_lesson(text: str) -> str:
    """Strip + validate a lesson string: non-empty, <=300 chars, single-line.

    Raises:
        AbstainLessonError: the text is empty, too long, or spans multiple lines.
    """
    stripped = text.strip()
    if not stripped:
        raise AbstainLessonError("lesson text is empty")
    if len(stripped) > _MAX_LESSON_CHARS:
        raise AbstainLessonError(
            f"lesson text too long ({len(stripped)} > {_MAX_LESSON_CHARS} chars)"
        )
    if "\n" in stripped:
        raise AbstainLessonError("lesson text must be a single line")
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
