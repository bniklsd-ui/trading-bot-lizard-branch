"""Instinct extraction — the *second* AI surface in Phase 15.

Mirrors ``phase7_reward/reward/brain.py`` (Decision F-pattern): the extractor
turns a batch of free-text lessons + reward outcomes into structured
:class:`Instinct` rows via a single LLM call. The call is **best-effort,
never raises** (P9): any failure yields ``InstinctExtractionResult(ok=False,
error=...)`` without re-raising — a flaky LLM never disturbs the close path
or the validator (which runs in a separate, deterministic code step).

## Reuse, not a second AI stack

The extractor reuses the Phase-4 ``research.LLMClient`` (Phase 7's
``_LLMClientLike`` is the duck-typed slice; this module defines its own
identical Protocol to keep phase isolation). The wiring (a later Phase-15
step) builds the real client with the ``instinct_*`` knobs and points its
token meter at the shared ``data/state/llm_usage.json``.

## Swappable extractor (mirror Decision E)

:class:`InstinctExtractor` is the v1 single-shot implementation; a later
batch/scheduler extractor satisfies the same Protocol so the validator
binds to *this*, never to a concrete class.

## What it does NOT do

The extractor extracts **language → structure**. It does **not** validate
(no evidence count, no contradiction count), it does **not** promote
(gated by :func:`instinct.promotion.promote_eligible`), and it does **not**
score (no number, no decision). Validator + promoter are deterministic
code — see ``validator.py`` and ``promotion.py``.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Protocol, runtime_checkable

from instinct.models import (
    DOMAINS,
    Instinct,
    is_valid_domain,
)

logger = logging.getLogger(__name__)

__all__ = ["InstinctExtractor", "InstinctExtractionResult"]


class _LLMClientLike(Protocol):
    """The slice of the shared ``research.LLMClient`` the extractor drives.

    Duck-typed (never imported) for phase isolation — exact mirror of
    ``phase7_reward/reward/brain.py:_LLMClientLike``. The wiring (a later
    Phase-15 step) builds the real client with ``model``/``max_tokens``/
    ``temperature``/``timeout_s`` set from the ``instinct_*`` config;
    ``last_usage`` carries the meter record captured per successful call.
    """

    model: str
    max_tokens: int
    temperature: float
    last_usage: dict[str, Any] | None

    def ask_candidate(self, system: str, user: str, json_schema: dict) -> dict: ...


@runtime_checkable
class InstinctExtractor(Protocol):
    """The swappable instinct-extraction interface.

    One method. A later batch/scheduler extractor satisfies the same
    Protocol so the validator binds to *this*, never to a concrete class.
    """

    def extract(
        self,
        lessons: list[dict[str, Any]],
        rewards: list[dict[str, Any]],
    ) -> "InstinctExtractionResult": ...


# ---------------------------------------------------------------------------
# Result type — mirrors LessonResult's shape (ok=True/False + payload + error).
# ---------------------------------------------------------------------------


class InstinctExtractionResult:
    """Outcome of one instinct-extraction call (best-effort, Decision E/J-style).

    Attributes:
        ok: whether extraction succeeded.
        instincts: parsed ``Instinct`` rows on success, else ``[]``.
        error: failure reason when ``ok`` is False, else ``None``.
    """

    __slots__ = ("ok", "instincts", "error")

    def __init__(
        self,
        ok: bool,
        instincts: list[Instinct],
        error: str | None,
    ) -> None:
        self.ok = ok
        self.instincts = instincts
        self.error = error

    def __repr__(self) -> str:
        if self.ok:
            return f"InstinctExtractionResult(ok=True, n={len(self.instincts)})"
        return f"InstinctExtractionResult(ok=False, error={self.error!r})"


# ---------------------------------------------------------------------------
# Prompt builder — pure, no AI, no I/O, no clock (mirror brain._build_lesson_prompt).
# ---------------------------------------------------------------------------


def _render_lessons(lessons: list[dict[str, Any]]) -> str:
    """Render lesson rows for the prompt; ``None`` / missing fields become ``"n/a"``."""
    if not lessons:
        return "(keine Lektionen vorhanden)"
    lines: list[str] = []
    for idx, lesson in enumerate(lessons, start=1):
        text = lesson.get("lesson_text") or "n/a"
        lines.append(f"{idx}. {text}")
    return "\n".join(lines)


def _render_rewards(rewards: list[dict[str, Any]]) -> str:
    """Render reward rows for the prompt; honest ``n/a`` for missing fields."""
    if not rewards:
        return "(keine Reward-Zeilen vorhanden)"
    lines: list[str] = []
    for idx, row in enumerate(rewards, start=1):
        win_loss = row.get("win_loss") or "n/a"
        outcome_delta = row.get("outcome_score_delta")
        process_delta = row.get("process_score_delta")
        score_after = row.get("score_after")
        lines.append(
            f"{idx}. result={win_loss} outcome_delta={outcome_delta!r} "
            f"process_delta={process_delta!r} score_after={score_after!r}"
        )
    return "\n".join(lines)


def _build_instinct_prompt(
    lessons: list[dict[str, Any]],
    rewards: list[dict[str, Any]],
) -> tuple[str, str, dict]:
    """Build the ``(system, user, json_schema)`` triple for one extraction call.

    The schema asks for **at most 5** structured instincts, each carrying
    exactly the schema fields from Concept §7b. ``domain`` is constrained
    to the four valid values; ``evidence_trade_ids`` / ``contradictions_trade_ids``
    are integer arrays (the validator counts them deterministically — see
    ``validator.py``).

    The system prompt draws the AI boundary sharply: extract **structure from
    language**, do not score, do not decide, do not promote. Validation and
    promotion are explicit code-side responsibilities.
    """
    domain_list = ", ".join(DOMAINS)
    system = (
        "Du bist ein nüchterner Aggregations-Assistent für einen DAX-CFD-Trading-Bot. "
        "Deine EINZIGE Aufgabe ist es, aus Freitext-Lektionen und Reward-Zeilen "
        "strukturierte Instinkt-Regeln zu extrahieren. Du triffst KEINE Score-, "
        "Risiko- oder Positions-Entscheidung. Du promotest NICHTS. Du validierst "
        "NICHTS (Evidence vs. Contradiction zählt der Code). Antworte als JSON-Objekt "
        "mit dem Feld \"instincts\" (Liste, max. 5 Einträge). Jeder Eintrag hat die "
        f"Felder trigger (string), domain (eines von: {domain_list}), "
        "confidence (0.0–1.0 oder null), evidence_trade_ids (Liste int), "
        "contradictions_trade_ids (Liste int). "
        "**``trigger`` MUSS die Form ``avoid BUY`` / ``avoid SELL`` / "
        "``avoid BUY on <EPIC>`` / ``avoid SELL on <EPIC>`` haben "
        "(EPIC = uppercase letters + digits + dots, z.B. ``IX.D.DAX.IFMM.IP``). "
        "Alles, was nicht in dieses Mini-Grammatik-Schema passt, wird vom Compiler "
        "verworfen (WARNING, kein Veto).** "
        "KEINE weiteren Felder."
    )

    user_lines = [
        "Extrahiere strukturierte Instinkt-Regeln aus folgenden Beobachtungen.",
        "",
        "Lektionen (Freitext):",
        _render_lessons(lessons),
        "",
        "Reward-Zeilen (Ergebnis-Signale):",
        _render_rewards(rewards),
        "",
        "Gib GENAU die JSON-Struktur zurück: {\"instincts\": [ ... ]}.",
    ]
    user = "\n".join(user_lines)

    json_schema = {
        "type": "object",
        "properties": {
            "instincts": {
                "type": "array",
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "properties": {
                        # Phase 16 D2.3: enforce the Mini-Grammatik at schema level
                        # (Plan §1 P9). The pattern is the **same** regex the
                        # compiler (compile.py:TRIGGER_RE) uses, so a trigger that
                        # passes the schema is guaranteed to compile to a predicate;
                        # a trigger that fails is structurally invalid for VETO 5.
                        "trigger": {
                            "type": "string",
                            "pattern": r"^\s*avoid\s+(BUY|SELL)(?:\s+on\s+[A-Z0-9.]+)?\s*$",
                        },
                        "domain": {
                            "type": "string",
                            "enum": list(DOMAINS),
                        },
                        "confidence": {
                            "anyOf": [
                                {"type": "number", "minimum": 0.0, "maximum": 1.0},
                                {"type": "null"},
                            ],
                        },
                        "evidence_trade_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                        },
                        "contradictions_trade_ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                        },
                    },
                    "required": [
                        "trigger", "domain", "confidence",
                        "evidence_trade_ids", "contradictions_trade_ids",
                    ],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["instincts"],
        "additionalProperties": False,
    }
    return system, user, json_schema


# ---------------------------------------------------------------------------
# Single-shot extractor — mirror Brain (P9).
# ---------------------------------------------------------------------------


class SingleShotInstinctExtractor:
    """v1 single-shot instinct extractor — best-effort, never raises.

    Stateless beyond the injected client + config. Mirrors
    ``phase7_reward/reward/brain.Brain``: one LLM call per ``extract``,
    structured output parsed verbatim into :class:`Instinct` rows.
    """

    def __init__(self, llm_client: _LLMClientLike) -> None:
        """Bind the duck-typed shared LLM client (Phase-4 / Phase-7 mirror)."""
        self._llm = llm_client

    def extract(
        self,
        lessons: list[dict[str, Any]],
        rewards: list[dict[str, Any]],
    ) -> InstinctExtractionResult:
        """Extract zero or more instincts — best-effort, never raises.

        Builds the prompt, makes one metered call, parses the structured
        output into :class:`Instinct` rows. On **any** failure (transport,
        timeout, malformed output, invalid domain, unparseable JSON) returns
        ``InstinctExtractionResult(ok=False, error=...)`` without re-raising.
        """
        try:
            system, user, schema = _build_instinct_prompt(lessons, rewards)
            raw = self._llm.ask_candidate(system, user, schema)
            payload = _parse_payload(raw)
            instincts = _coerce_instincts(payload)
            usage = getattr(self._llm, "last_usage", None)
            logger.info(
                "instinct.extract: %d instincts (usage=%s)",
                len(instincts),
                usage,
            )
            return InstinctExtractionResult(
                ok=True, instincts=instincts, error=None,
            )
        except Exception as exc:  # noqa: BLE001 — best-effort: never raise
            logger.warning(
                "instinct.extract failed (best-effort, no instincts this cycle): %r",
                exc,
            )
            return InstinctExtractionResult(
                ok=False, instincts=[], error=str(exc),
            )


# ---------------------------------------------------------------------------
# Internal parsing helpers — pure, no I/O, raised exceptions are caught by
# the wrapper above. Kept module-private.
# ---------------------------------------------------------------------------


def _parse_payload(raw: Any) -> dict[str, Any]:
    """Pull the ``{"instincts": [...]}`` payload out of the LLM response.

    The shared ``research.LLMClient`` returns a dict (Structured Outputs path)
    or a JSON-encoded string (fence-strip fallback path). Both are accepted;
    anything else raises ``ValueError``.
    """
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        return json.loads(raw)
    raise ValueError(f"unsupported LLM payload type: {type(raw).__name__}")


def _coerce_instincts(payload: dict[str, Any]) -> list[Instinct]:
    """Turn the parsed ``{"instincts": [...]}`` into ``Instinct`` rows.

    Each entry is validated against the schema (trigger, domain, confidence,
    evidence/contradictions). Malformed entries raise ``ValueError`` — caught
    by the caller's try/except so a single bad row fails the whole batch
    rather than silently dropping.
    """
    raw_list = payload.get("instincts")
    if not isinstance(raw_list, list):
        raise ValueError(
            f"payload must contain an 'instincts' list, got {type(raw_list).__name__}"
        )
    out: list[Instinct] = []
    for entry in raw_list:
        if not isinstance(entry, dict):
            raise ValueError(f"instinct entry must be a dict, got {type(entry).__name__}")
        trigger = entry.get("trigger")
        domain = entry.get("domain")
        confidence = entry.get("confidence")
        evidence = entry.get("evidence_trade_ids", [])
        contradictions = entry.get("contradictions_trade_ids", [])

        if not isinstance(trigger, str) or not trigger.strip():
            raise ValueError(f"instinct.trigger missing/empty: {entry!r}")
        if not is_valid_domain(domain):
            raise ValueError(
                f"instinct.domain invalid (got {domain!r}, must be one of {DOMAINS})"
            )
        if not isinstance(evidence, list) or not all(
            isinstance(x, int) for x in evidence
        ):
            raise ValueError(
                f"instinct.evidence_trade_ids must be a list[int], got {evidence!r}"
            )
        if not isinstance(contradictions, list) or not all(
            isinstance(x, int) for x in contradictions
        ):
            raise ValueError(
                f"instinct.contradictions_trade_ids must be a list[int], "
                f"got {contradictions!r}"
            )
        if confidence is not None and not (
            isinstance(confidence, (int, float)) and 0.0 <= float(confidence) <= 1.0
        ):
            raise ValueError(
                f"instinct.confidence must be in [0.0, 1.0] or null, got {confidence!r}"
            )

        out.append(
            Instinct(
                trigger=trigger.strip(),
                domain=domain,
                confidence=(float(confidence) if confidence is not None else None),
                evidence_trade_ids=tuple(int(x) for x in evidence),
                contradictions_trade_ids=tuple(int(x) for x in contradictions),
            )
        )
    return out
