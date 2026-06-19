"""Lesson extraction — the *only* AI in Phase 7 (concept §6 Step 7, Decision E/F/J).

``Brain.reflect`` turns one closed trade's outcome into **one short, free-text
lesson** via a single Haiku call. That is the entire AI surface of the phase: the
"so wenig AI wie möglich" principle puts everything else (the reward delta, the
confidence math, P&L resolution, persistence, error handling) in deterministic
code. The brain extracts **only language → insight** — it produces **no** number,
**no** score, **no** decision. A reward score is never an LLM output.

## Reuse, not a second AI stack (Decision F)

The brain reuses the Phase-4 ``research.LLMClient`` (the single existing call site
machinery: Structured Outputs → fence-strip fallback → exactly-one transient retry)
through the duck-typed :class:`_LLMClientLike` Protocol — it is **never imported**
here (phase isolation, exactly like the Phase-6 ``debate`` orchestrator's
``_LLMClientLike``). The wiring (Step 13) builds the real client with the
``lesson_*`` knobs from :class:`~reward.models.RewardConfig` and points its token
meter at the shared ``data/state/llm_usage.json``.

**Metering is transitive (documented concept↔code reconciliation, 2026-06-19).** The
concept §6 Step 7 signature was ``Brain(llm_client, token_meter, cfg)``, but
``LLMClient.ask_candidate`` *already* calls ``research.token_meter.record`` internally
and exposes the record on ``client.last_usage``. Passing ``token_meter`` again would
**double-count**. So the brain takes ``Brain(llm_client, cfg)`` and reads back
``last_usage`` for observability — exactly how the Phase-6 ``debate`` reads
``last_usage`` instead of re-metering. ``research.token_meter`` is therefore reused
*through* the client (Decision F satisfied), not a second time.

## Best-effort / fail-closed (Decision E/J)

Lesson extraction is **decoupled from the close critical path**: the reward is
written atomically first (Step 8 recorder), then ``reflect`` runs best-effort. **Any**
failure — a flaky network, a malformed answer, a timeout, anything — yields
``LessonResult(ok=False, error=...)`` and is **never** re-raised. A missing lesson
this cycle is a missing optional learning, not a data-integrity fault, so the brain
logs it at ``warning``; the recorder (Step 8) is where the ``logger.critical`` of
Decision J lives, because that is where the DB *writes* happen.

The "own timeout" of concept §5 (``lesson_timeout_s``) is the client's transport
timeout, configured at construction by the wiring — a timeout surfaces as an
exception, which the best-effort wrapper turns into ``ok=False``.

## Swappable extractor (Decision E)

:class:`LessonExtractor` is the swappable interface (one method, ``reflect``). The
Step-8 recorder types its collaborator against it, so a later batch/scheduler
extractor can be dropped in without touching any reward code. :class:`Brain` is the
v1 single-shot implementation.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol, runtime_checkable

from reward.models import ClosedTrade, LessonResult, RewardConfig, RewardResult

logger = logging.getLogger(__name__)

__all__ = ["Brain", "LessonExtractor"]


class _LLMClientLike(Protocol):
    """The slice of the shared ``research.LLMClient`` the brain drives.

    Duck-typed (never imported) for phase isolation. The wiring (Step 13) builds the
    real client with ``model``/``max_tokens``/``temperature``/``timeout_s`` set from
    the ``lesson_*`` config and a token-meter path; ``last_usage`` carries the meter
    record captured per successful call.
    """

    model: str
    max_tokens: int
    temperature: float
    last_usage: dict[str, Any] | None

    def ask_candidate(self, system: str, user: str, json_schema: dict) -> dict: ...


@runtime_checkable
class LessonExtractor(Protocol):
    """The swappable lesson-extraction interface (Decision E).

    One method. :class:`Brain` is the v1 single-shot implementation; a later
    batch/scheduler extractor satisfies the same Protocol so the Step-8 recorder
    binds to *this*, never to a concrete class.
    """

    def reflect(
        self,
        closed: ClosedTrade,
        outcome: RewardResult,
        market_context: dict[str, Any],
    ) -> LessonResult: ...


def _fmt(value: Any) -> str:
    """Render a value for the prompt, honestly (``None`` → ``"n/a"``, never faked 0).

    The single formatting chokepoint (the Phase-4/6 convention): an absent signal is
    ``"n/a"``, never a fabricated ``0`` that the model would read as real data. Floats
    are rendered with light precision; everything else stringifies.
    """
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def _build_lesson_prompt(
    closed: ClosedTrade,
    outcome: RewardResult,
    market_context: dict[str, Any],
) -> tuple[str, str, dict]:
    """Build the ``(system, user, json_schema)`` triple for one lesson extraction.

    Pure: no AI, no I/O, no clock. The **system** prompt states the role and the
    hard AI boundary (one concise lesson; **no** number/score/risk decision). The
    **user** message carries only the trade facts (win/loss, R-multiple, exit status)
    and the market context, each rendered through :func:`_fmt`. The schema is a single
    required string ``lesson`` (no nullable → no ``anyOf`` needed; the Phase-4 rule
    against type-array unions is moot here).
    """
    system = (
        "Du bist ein nüchterner Reflexions-Assistent für einen DAX-CFD-Trading-Bot. "
        "Deine EINZIGE Aufgabe ist es, aus dem Ergebnis EINES abgeschlossenen Trades "
        "GENAU EINE knappe, umsetzbare Lektion in einem Satz zu extrahieren. "
        "Du triffst KEINE Zahlen-, Score- oder Risiko-Entscheidung und schlägst KEINE "
        "konkrete Positionsgröße vor — du wandelst nur Beobachtung in Erkenntnis um. "
        "Konzentriere dich auf den PROZESS (Entry-Qualität, Exit-Art, Spread), nicht "
        "nur auf Gewinn/Verlust — ein Verlust an einem sauber geplanten Stop ist eine "
        "andere Lektion als ein Verlust durch Drift. Antworte als JSON-Objekt mit dem "
        "einzigen Feld \"lesson\"."
    )

    # R-multiple, win/loss and exit status are the load-bearing facts the test pins.
    user_lines = [
        "Abgeschlossener Trade — extrahiere eine Lektion:",
        "",
        f"- Ergebnis: {_fmt(outcome.win_loss)}",
        f"- R-Multiple (P&L / initiales Risiko): {_fmt(outcome.r_multiple)}",
        f"- Exit-Status: {_fmt(closed.status)} "
        "(CLOSED_BY_BROKER = geplanter SL/TP getroffen; TIME_STOP = Drift, kein Edge realisiert)",
        "",
        "Marktkontext zum Zeitpunkt der Entscheidung:",
    ]
    if market_context:
        for key in market_context:
            user_lines.append(f"- {key}: {_fmt(market_context[key])}")
    else:
        user_lines.append("- (kein Marktkontext verfügbar)")
    user_lines += [
        "",
        "Gib GENAU EINE knappe Lektion zurück (ein Satz), als JSON: {\"lesson\": \"...\"}.",
    ]
    user = "\n".join(user_lines)

    json_schema = {
        "type": "object",
        "properties": {"lesson": {"type": "string"}},
        "required": ["lesson"],
        "additionalProperties": False,
    }
    return system, user, json_schema


class Brain:
    """Extract one free-text lesson per closed trade — best-effort, never raises.

    The v1 :class:`LessonExtractor`: a single Haiku call through the reused
    ``research.LLMClient``. Stateless beyond the injected client + config.
    """

    def __init__(self, llm_client: _LLMClientLike, cfg: RewardConfig) -> None:
        """Bind the (duck-typed) shared LLM client and the reward config.

        Args:
            llm_client: the shared ``research.LLMClient`` (duck-typed; built by the
                Step-13 wiring with the ``lesson_*`` knobs + a token-meter path).
            cfg: the immutable :class:`~reward.models.RewardConfig` (carries the
                ``lesson_*`` defaults; the client is configured from them in wiring).
        """
        self._llm = llm_client
        self.cfg = cfg

    def reflect(
        self,
        closed: ClosedTrade,
        outcome: RewardResult,
        market_context: dict[str, Any],
    ) -> LessonResult:
        """Extract one lesson for a closed trade; **best-effort, never raises**.

        Builds the prompt, makes the single metered call, and returns the model's
        ``lesson`` text verbatim. On **any** failure (transport error, malformed or
        empty answer, timeout, anything) returns ``LessonResult(ok=False, error=...)``
        without re-raising (Decision E/J) — a missing lesson never disturbs the close
        path. ``market_context`` is echoed back unchanged (the recorder persists it as
        ``market_context_json``).

        Args:
            closed: the minimal close fact (carries ``deal_id`` + exit ``status``).
            outcome: the scorer's :class:`~reward.models.RewardResult` (win/loss +
                R-multiple — the factual outcome the prompt reflects on).
            market_context: the conditions dict for the prompt + the lesson row.

        Returns:
            A :class:`~reward.models.LessonResult`: ``ok=True`` with the verbatim
            ``lesson_text`` on success, else ``ok=False`` with ``lesson_text=None`` and
            the captured ``error``.
        """
        try:
            system, user, schema = _build_lesson_prompt(closed, outcome, market_context)
            raw = self._llm.ask_candidate(system, user, schema)
            lesson_text = raw.get("lesson") if isinstance(raw, dict) else None
            if not isinstance(lesson_text, str) or not lesson_text.strip():
                raise ValueError(f"no usable 'lesson' field in model output: {raw!r}")

            # Observability only: the metering itself already happened inside
            # ask_candidate (Decision F — token_meter reused transitively via the
            # client). last_usage carries that record for a reusing caller / logs.
            usage = getattr(self._llm, "last_usage", None)
            logger.info(
                "brain.reflect: lesson extracted (deal_id=%s, usage=%s)",
                closed.deal_id,
                usage,
            )
            return LessonResult(
                lesson_text=lesson_text.strip(),
                market_context=market_context,
                ok=True,
                error=None,
            )
        except Exception as exc:  # noqa: BLE001 — best-effort: never raise (Decision E/J)
            # A failed reflection is a missing *optional* lesson, not a data-integrity
            # fault (no DB write happens here) — hence ``warning``, not the ``critical``
            # of Decision J. The Step-8 recorder owns the critical-on-write logging.
            logger.warning(
                "brain.reflect failed for deal_id=%s (best-effort, no lesson this cycle): %r",
                getattr(closed, "deal_id", "?"),
                exc,
            )
            return LessonResult(
                lesson_text=None,
                market_context=market_context,
                ok=False,
                error=str(exc),
            )
