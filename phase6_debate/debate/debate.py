"""Module 6 — the debate orchestrator (concept §6). **The core of the phase.**

:class:`Debate` composes the individually-built, individually-tested Phase-6
pieces into one ``run(candidate) -> DebateOutcome``:

- ``context_builder.build_debate_context`` — the deterministic, code-only context
  (the AI boundary; the broker is read **here** and nowhere else).
- ``prompts.build_{bull,bear,judge}_prompt`` — the per-turn ``(system, user,
  schema)`` triples (stable cached system prefix, growing transcript in ``user``).
- ``llm_caching.ask_agent`` — the one shared-client request site (the AI).
- ``budget.DebateBudget`` — the hard caps + cumulative metering.

**No new AI logic lives here** — the AI is only the Bull/Bear/Judge requests. The
loop, the deterministic transcript compression, the validation of the model's
output, and the fail-closed handling are all code. The debate **never** references
a VETO/Gate and never hands the broker to a request (Decision J — it *cannot*
bypass a VETO because it cannot reach one). Every error / cap breach / unusable
verdict at any point → **fail-closed ABSTAIN**: never an exception out of ``run``,
never a fabricated direction, never "trade anyway".

All collaborators are injected (DI), and the clock (``now_fn``) is injected too —
the same pattern the Phase-5 ``executor``/``monitor`` use — so the budget's
wall-clock cap is deterministic under test. Phase-isolated: imports only
``debate.*`` + stdlib; the broker and the shared LLM client are duck-typed.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Protocol

from debate.budget import DebateBudget
from debate.context_builder import build_debate_context
from debate.llm_caching import ask_agent
from debate.models import (
    AgentTurn,
    DebateConfig,
    DebateContext,
    DebateError,
    DebateOutcome,
)
from debate.prompts import build_bear_prompt, build_bull_prompt, build_judge_prompt

logger = logging.getLogger(__name__)

# Stable agent ordering for the compressed transcript view.
_AGENT_ORDER = {"BULL": 0, "BEAR": 1, "JUDGE": 2}


class _LLMClientLike(Protocol):
    """The slice of the shared ``research.LLMClient`` the orchestrator drives.

    Duck-typed (never imported) for phase isolation. ``ask_agent`` sets ``model`` /
    ``temperature`` per turn; the orchestrator sets ``max_tokens`` per role (the one
    per-turn knob ``ask_agent`` does not touch). The client must be built with
    ``cache_system=True`` (wiring, Module 8) so the stable system prefix is cached.
    """

    model: str
    temperature: float
    max_tokens: int
    last_usage: dict[str, Any] | None

    def ask_candidate(self, system: str, user: str, json_schema: dict) -> dict: ...


def _as_float(value: Any) -> float:
    """Coerce an advisory value to float, tolerating ``None``/garbage → ``0.0``."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _compress(transcript: list[AgentTurn]) -> list[AgentTurn]:
    """Deterministic, lossy-but-bounded transcript view: latest turn per agent.

    Keeps each side's **current** position (latest Bull / Bear / Judge turn) in
    round order — the concept's "(Bull position, Bear position, Judge interim)"
    compression. Code-only, no extra request (v1). Never mutates the input; the
    **full** transcript is preserved separately for the outcome + audit.
    """
    latest: dict[str, AgentTurn] = {}
    for turn in transcript:
        latest[turn.agent] = turn
    return sorted(latest.values(), key=lambda t: (t.round, _AGENT_ORDER.get(t.agent, 9)))


class Debate:
    """Run one Bull/Bear/Judge debate; always return a ``DebateOutcome`` (§6)."""

    def __init__(
        self,
        broker: Any,
        llm_client: _LLMClientLike,
        config: DebateConfig,
        *,
        audit: Callable[[DebateOutcome, DebateContext], None] | None = None,
        now_fn: Callable[[], float] = time.monotonic,
    ) -> None:
        """Wire the debate's collaborators.

        Args:
            broker: the read-only broker, read **once** by ``build_debate_context``
                (never handed to a request — Decision J).
            llm_client: the shared ``research.LLMClient`` (duck-typed; built with
                ``cache_system=True``).
            config: the run's :class:`DebateConfig` (models, caps, temperatures,
                compression trigger).
            audit: optional sink ``(outcome, ctx) -> None`` (DI). Module 7's
                ``write_debate`` is adapted to this shape by the Module-8 wiring;
                tests pass a recorder. ``None`` → no audit.
            now_fn: injected monotonic clock for the budget's wall-clock cap.
        """
        self._broker = broker
        self._llm = llm_client
        self._config = config
        self._audit = audit
        self._now_fn = now_fn

    # -- public ------------------------------------------------------------- #

    def run(self, candidate: dict[str, Any]) -> DebateOutcome:
        """Run the debate for one Phase-4 candidate; never raise.

        Builds the context, runs the rounds, and returns the Judge's verdict — or a
        fail-closed ABSTAIN on **any** error / cap breach / unusable verdict
        (Decision J). Writes the audit exactly once (if injected and the context was
        built) before returning.
        """
        cfg = self._config
        ctx: DebateContext | None = None
        budget = DebateBudget(cfg, now_fn=self._now_fn)
        full_transcript: list[AgentTurn] = []

        try:
            ctx = build_debate_context(candidate, self._broker, cfg)
            outcome = self._debate(ctx, budget, full_transcript)
        except DebateError as exc:
            # context fault, agent request failure, or a hard cap breach — all
            # fail-closed to ABSTAIN (Decision J). The reason is logged + carried.
            logger.warning("debate fail-closed (%s): %s", type(exc).__name__, exc)
            outcome = self._abstain(str(exc), full_transcript, budget)
        except Exception as exc:  # noqa: BLE001 — defensive: never raise out (Decision J)
            logger.error("debate fail-closed (unexpected): %r", exc)
            outcome = self._abstain(f"unexpected error: {exc!r}", full_transcript, budget)

        if self._audit is not None and ctx is not None:
            try:
                self._audit(outcome, ctx)
            except Exception as exc:  # noqa: BLE001 — audit must never break the result
                logger.warning("debate audit write failed (ignored): %r", exc)
        return outcome

    # -- internals ---------------------------------------------------------- #

    def _debate(
        self,
        ctx: DebateContext,
        budget: DebateBudget,
        full_transcript: list[AgentTurn],
    ) -> DebateOutcome:
        """Run the round loop (Bull → Bear → Judge), early-stop, then the verdict.

        Appends every turn to ``full_transcript`` in place so the fail-closed path
        in ``run`` can carry the partial transcript. Raises only the typed
        :class:`DebateError` family (from ``ask_agent`` / ``budget.check``), which
        ``run`` converts to ABSTAIN.
        """
        cfg = self._config
        threshold = cfg.compression_trigger_pct * cfg.max_cumulative_input_tokens
        compressed = False
        last_judge: dict[str, Any] | None = None

        roles = (
            ("BULL", build_bull_prompt, cfg.model_bull, cfg.temperature_bull,
             cfg.max_tokens_agent, "argument"),
            ("BEAR", build_bear_prompt, cfg.model_bear, cfg.temperature_bear,
             cfg.max_tokens_agent, "argument"),
            ("JUDGE", build_judge_prompt, cfg.model_judge, cfg.temperature_judge,
             cfg.max_tokens_judge, "rationale"),
        )

        for rnd in range(1, cfg.max_rounds + 1):
            for agent, builder, model, temperature, max_tokens, text_key in roles:
                # Deterministic compression latch: once cumulative input tokens
                # cross the trigger, render prompts from the compressed view.
                if not compressed and budget.summary()["input_tokens"] > threshold:
                    compressed = True
                    logger.info("debate transcript compression triggered (round %d)", rnd)
                prompt_view = _compress(full_transcript) if compressed else full_transcript

                turn, answer = self._turn(
                    agent, builder, model, temperature, max_tokens, ctx, prompt_view,
                    rnd, text_key,
                )
                full_transcript.append(turn)
                budget.register(turn.usage)
                budget.check()  # raises DebateBudgetExceeded on the first breach
                if agent == "JUDGE":
                    last_judge = answer

            if cfg.early_stop and last_judge is not None and last_judge.get("conclude") is True:
                break

        return self._verdict(last_judge, full_transcript, budget)

    def _turn(
        self,
        agent: str,
        builder: Callable[[DebateContext, list[AgentTurn]], tuple[str, str, dict]],
        model: str,
        temperature: float,
        max_tokens: int,
        ctx: DebateContext,
        prompt_view: list[AgentTurn],
        rnd: int,
        text_key: str,
    ) -> tuple[AgentTurn, dict[str, Any]]:
        """Run one agent turn via the shared client; return the turn + raw answer.

        Applies the per-role ``max_tokens`` to the shared client (``ask_agent``
        applies model + temperature), then records the turn. Raises
        :class:`~debate.models.DebateLLMError` on an unrecoverable request failure
        (via ``ask_agent``) — ``run`` turns that into ABSTAIN.
        """
        system, user, schema = builder(ctx, prompt_view)
        self._llm.max_tokens = max_tokens
        answer, usage = ask_agent(
            self._llm, system, user, schema, model=model, temperature=temperature
        )
        text = answer.get(text_key)
        turn = AgentTurn(
            round=rnd, agent=agent, model=model, text=str(text or ""), usage=usage
        )
        return turn, answer

    def _verdict(
        self,
        last_judge: dict[str, Any] | None,
        full_transcript: list[AgentTurn],
        budget: DebateBudget,
    ) -> DebateOutcome:
        """Turn the final Judge answer into a validated :class:`DebateOutcome`.

        Code-side validation of the AI output (Hard Rule 3): an unusable
        ``decision`` or a ``TRADE`` without a usable ``BUY``/``SELL`` direction →
        fail-closed ABSTAIN. ``confidence`` is advisory only (Decision H) — it is
        carried for Phase-7 outcome-anchoring but gates nothing here.
        """
        if last_judge is None:
            return self._abstain("no judge verdict produced", full_transcript, budget)

        decision = last_judge.get("decision")
        if decision not in ("TRADE", "ABSTAIN"):
            return self._abstain(
                f"judge returned invalid decision {decision!r}", full_transcript, budget
            )

        if decision == "ABSTAIN":
            direction: str | None = None
        else:
            direction = last_judge.get("direction")
            if direction not in ("BUY", "SELL"):
                return self._abstain(
                    f"judge TRADE without a usable direction ({direction!r})",
                    full_transcript,
                    budget,
                )

        return DebateOutcome(
            decision=decision,
            direction=direction,
            confidence=_as_float(last_judge.get("confidence")),  # advisory only
            rationale=str(last_judge.get("rationale") or ""),
            rounds_used=full_transcript[-1].round if full_transcript else 0,
            transcript=tuple(full_transcript),
            token_summary=budget.summary(),
        )

    def _abstain(
        self,
        reason: str,
        full_transcript: list[AgentTurn],
        budget: DebateBudget,
    ) -> DebateOutcome:
        """Build the fail-closed ABSTAIN outcome (no direction, reason carried)."""
        return DebateOutcome(
            decision="ABSTAIN",
            direction=None,
            confidence=0.0,
            rationale=reason,
            rounds_used=full_transcript[-1].round if full_transcript else 0,
            transcript=tuple(full_transcript),
            token_summary=budget.summary(),
        )
