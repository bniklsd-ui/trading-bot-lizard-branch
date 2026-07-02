"""The research orchestrator — wires the deterministic pieces around one AI call.

``Research.run()`` is the whole Phase-4 cycle. It composes the six building
blocks built in Steps 2-6 into a single flow, with the safety discipline that
**every** non-PASS branch (session-health abort, empty universe, LLM error,
validator reject, valid abstain, filter reject) resolves to
``state.save_candidates([])`` — never a fabricated candidate (root CLAUDE.md
rule 3; concept Decision 8). The only AI step is the single ``llm.ask_candidate``
call; its raw output passes the independent validator **and** the deterministic
filter before it can ever be persisted as a pick.

Phase isolation holds here too: this module imports only ``research.*`` + stdlib.
Collaborators (broker / db / state / market_data / llm) are injected and typed via
local ``typing.Protocol``s — no ``broker_wrapper`` / ``persistence`` /
``external_data`` import (consistent with ``validator.py`` and
``context_builder.py``).

Logging goes to **stderr** only. ``run()`` returns the candidate list and does
**not** print to stdout: the machine-readable result JSON is the Step-8 scripts'
job, which keeps ``run()`` free of I/O except through its injected collaborators.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol

from research.candidate_filter import (
    apply_filter,
    confidence_threshold,
    resolve_allowed_directions,
)
from research.context_builder import build_context
from research.models import (
    Candidate,
    LLMResponseError,
    ResearchAbort,
    ResearchConfig,
)
from research.prompt import build_prompt
from research.validator import validate_candidate

log = logging.getLogger(__name__)

_TRADEABLE = "TRADEABLE"


class _BrokerLike(Protocol):
    """Minimal broker surface the orchestrator needs (Envelope-returning).

    Typed as a Protocol so Phase 4 never imports ``broker_wrapper`` (phase
    isolation). The real ``IGAdapter`` and the test ``FakeBroker`` both satisfy
    it. ``get_price`` / ``connect`` / ``get_account`` return Envelope-like
    objects exposing ``.ok`` (bool) and ``.data`` (dict).
    """

    def is_connected(self) -> bool: ...
    def connect(self) -> Any: ...
    def get_account(self) -> Any: ...
    def get_price(self, epic: str) -> Any: ...
    def get_market_info(self, epic: str) -> Any: ...


class _DBLike(Protocol):
    """Phase-2 ``Database`` surface: the recent reads + the one loop-closure write.

    Research is read-mostly, but it makes **one** bookkeeping write —
    ``mark_lesson_used`` — after the LLM has consumed the lessons rendered into the
    prompt (Decision I / Phase-7 Step 11). That closes the learning loop: a lesson
    written by the Phase-7 recorder is pulled into the next research prompt and its
    ``used_in_research`` count / ``last_used_ts`` are updated. It is **not** a
    trade/outcome write and never touches the VETO/safety layer.
    """

    def get_recent_trades(self, n: int = 8) -> list[dict[str, Any]]: ...
    def get_recent_lessons(self, n: int = 5) -> list[dict[str, Any]]: ...
    def get_current_score(self) -> float: ...
    def get_risk_level(self) -> str: ...
    def mark_lesson_used(self, lesson_id: int) -> None: ...


class _StateLike(Protocol):
    """Phase-2 ``StateManager`` surface — the orchestrator only ever writes.

    Every cycle ends in exactly one ``save_candidates`` call: the single pick on
    a clean PASS, or ``[]`` on any abstain / reject / error.
    """

    def save_candidates(self, candidates: list[dict[str, Any]]) -> Any: ...


class _FetcherLike(Protocol):
    """Phase-3 ``MarketDataFetcher`` surface needed by ``build_context``."""

    def get_brain_context(self, epic: str) -> Any: ...


class _LLMLike(Protocol):
    """The single AI call site — ``ask_candidate`` (Step 5 ``LLMClient``)."""

    def ask_candidate(self, system: str, user: str, json_schema: dict) -> dict: ...


class Research:
    """Orchestrates one research cycle: context → prompt → AI → validate → filter.

    Dependency-injected (concept Decision 2): the real Phase-1/2/3 instances and
    the ``LLMClient`` are resolved by ``scripts/wiring.py`` (Step 8); unit tests
    inject the conftest fakes. No collaborator is constructed here.
    """

    def __init__(
        self,
        broker: _BrokerLike,
        db: _DBLike,
        state: _StateLike,
        market_data: _FetcherLike,
        llm: _LLMLike,
        config: ResearchConfig,
    ) -> None:
        """Wire the orchestrator (no network, no work — pure injection).

        Args:
            broker: Phase-1 broker adapter (session-health + universe probe +
                validator live recheck).
            db: Phase-2 ``Database`` for trades / lessons / score / risk level.
            state: Phase-2 ``StateManager`` — the sole persistence sink.
            market_data: Phase-3 ``MarketDataFetcher`` for the anchor brain
                context.
            llm: The ``LLMClient`` (or a fake) — the one ``ask_candidate`` call.
            config: The run config (allow-list, floors, clamp, spread bound).
        """
        self.broker = broker
        self.db = db
        self.state = state
        self.market_data = market_data
        self.llm = llm
        self.config = config
        # Display-only: the LLM's prose reason from the *last* valid abstain (``abstain=true``),
        # captured so a UI can show *why* it skipped. ``None`` after a pick or a pre-LLM abort.
        # Never gates anything and never becomes a candidate (root rule 3). Read by Phase-8.
        self.last_no_pick_reasoning: str | None = None
        # v1.6 (Phase-8 hotfix Step 0, observability). Diagnostic-only, gates nothing (root
        # rule 3); both reset at the top of every run() and read defensively by Phase-8
        # (getattr, so a pre-v1.6 fake without these attrs still satisfies the Protocol):
        # - last_context_health: the per-epic brain-context health from the *last* cycle's
        #   build_context() call (copied from ResearchContext.brain_context_health). Set even
        #   on a pre-LLM abort (context is always built before any abort branch that has one).
        # - last_abort_detail: the exact free-text reason passed to _abstain() on the *last*
        #   cycle, for EVERY non-pick branch (session-health abort / empty universe / LLM error
        #   / validator reject / valid abstain / filter reject) — broader than
        #   last_no_pick_reasoning, which only covers the model's own prose on a valid abstain.
        self.last_context_health: dict[str, dict] = {}
        self.last_abort_detail: str | None = None

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #
    def run(self) -> list[Candidate]:
        """Run one full research cycle.

        Returns the persisted candidates: a one-element list on a clean PASS, or
        an empty list on **any** non-PASS outcome (session-health abort, empty
        universe, LLM error, validator reject, valid abstain, filter reject).
        Whatever the outcome, exactly one ``state.save_candidates`` call is made.

        Returns:
            ``[candidate]`` on PASS, otherwise ``[]``. Reasons are logged to
            stderr; stdout is left untouched (Step-8 scripts own the result JSON).
        """
        # Reset the display-only abstain prose each cycle (a pick / pre-LLM abort leaves it clear).
        self.last_no_pick_reasoning = None
        # v1.6 Step 0: reset the observability attrs each cycle too (see __init__ docstring).
        self.last_context_health = {}
        self.last_abort_detail = None

        # 1. Session-health pre-flight. Any fault → abort, no AI call.
        try:
            self._preflight()
        except ResearchAbort as exc:
            return self._abstain(f"session-health abort: {exc}")

        # 2. Deterministic context (Phase-1 probe / Phase-2 reads / Phase-3 brain).
        context = build_context(self.broker, self.db, self.market_data, self.config)
        # v1.6 Step 0: capture the per-epic health snapshot regardless of what happens next.
        self.last_context_health = context.brain_context_health
        if not context.tradeable_epics:
            return self._abstain("empty universe (nothing tradeable)")

        # 3. Score-derived floor + long-bias clamp (deterministic).
        threshold = confidence_threshold(context.bot_score, self.config)
        allowed = resolve_allowed_directions(context.bot_score, self.config)

        # 4. Code-built prompt (epic enum = real universe).
        system, user, schema = build_prompt(context, threshold, allowed)

        # 5. THE single AI step. Any unrecoverable LLM failure → abstain.
        try:
            raw = self.llm.ask_candidate(system, user, schema)
        except LLMResponseError as exc:
            return self._abstain(f"LLM error: {exc}")

        # 5b. Loop-closure (Decision I / Phase-7 Step 11): the lessons in the prompt
        # the model just answered are now "used in research". Mark them here — after a
        # successful answer, so the pre-LLM aborts above never over-count. Best-effort.
        self._mark_lessons_used(context.recent_lessons)

        # 6. Independent hallucination guard + live-spread recheck.
        # v1.5 (Issue C): drift_at_pick comes from the PICKED epic's snapshot (multi-
        # instrument), falling back to the anchor ``brain_context`` when the per-epic
        # map is empty or the pick has no epic (abstain/malformed raw).
        picked_epic = raw.get("epic")
        brain_for_pick = context.brain_contexts.get(picked_epic) if (
            context.brain_contexts and picked_epic
        ) else None
        if brain_for_pick is None:
            brain_for_pick = context.brain_context
        drift = (brain_for_pick or {}).get("drift_pct")
        vr = validate_candidate(
            raw,
            context.tradeable_epics,
            threshold,
            allowed,
            self.broker,
            self.config.max_spread_pct,
            score_at_pick=context.bot_score,
            drift_at_pick=drift,
        )
        if not vr.valid:
            return self._abstain(f"validator REJECT: {vr.rejected_reason}")
        if vr.candidate is None:
            # Valid abstain (model set ``abstain=true``): keep its prose reason for the UI.
            # Scoped to this branch only — on a REJECT, ``raw["reasoning"]`` is the model's
            # *pick* rationale (it wanted to trade), which would be misleading as a skip reason.
            self.last_no_pick_reasoning = (raw.get("reasoning") or "").strip() or None
            return self._abstain("validator abstain (no pick)")

        # 7. The real deterministic gate (a soft drift warn is ok=True → passes).
        fv = apply_filter(vr.candidate, context, self.config)
        if not fv.ok:
            return self._abstain(f"filter REJECT [{fv.rule}]: {fv.reason}")

        # 8. PASS — persist the single pick and return it.
        candidate = vr.candidate
        self.state.save_candidates([candidate.to_dict()])
        log.info(
            "research PASS: saved 1 candidate %s %s (conf=%s, floor=%s)",
            candidate.direction,
            candidate.epic,
            candidate.llm_confidence,
            candidate.threshold_applied,
        )
        return [candidate]

    # ------------------------------------------------------------------ #
    # Internals                                                          #
    # ------------------------------------------------------------------ #
    def _preflight(self) -> None:
        """Verify broker connectivity / account / anchor tradeability.

        Raises:
            ResearchAbort: if not connected (and ``connect`` fails), the account
                read is not ``ok``, or the anchor epic is not a TRADEABLE quote.
                The caller turns this into ``save_candidates([])`` — far safer
                than letting a later ``open_position`` ``ValueError`` blow up.
        """
        anchor_epic = self.config.epic_allowlist[0]

        if not self.broker.is_connected():
            env = self.broker.connect()
            if not getattr(env, "ok", False):
                raise ResearchAbort("broker connect failed")

        acct = self.broker.get_account()
        if not getattr(acct, "ok", False):
            raise ResearchAbort("get_account not ok")

        price = self.broker.get_price(anchor_epic)
        if not getattr(price, "ok", False):
            raise ResearchAbort(f"anchor get_price not ok for {anchor_epic!r}")
        data = getattr(price, "data", None) or {}
        if data.get("market_status") != _TRADEABLE:
            raise ResearchAbort(
                f"anchor {anchor_epic!r} not TRADEABLE "
                f"(market_status={data.get('market_status')!r})"
            )

    def _mark_lessons_used(self, lessons: list[dict[str, Any]]) -> None:
        """Mark each lesson rendered into the prompt as used (loop-closure, Decision I).

        Best-effort: a missing ``id`` is skipped and a ``mark_lesson_used`` failure is
        logged (warning) and swallowed — this is learning bookkeeping, **not** the trade
        decision, so it must never break the research cycle / no-trade outcome.
        """
        for lesson in lessons:
            lid = lesson.get("id")
            if lid is None:
                continue
            try:
                self.db.mark_lesson_used(lid)
            except Exception as exc:  # noqa: BLE001 - bookkeeping must not break the cycle
                log.warning("mark_lesson_used failed for lesson id=%s: %s", lid, exc)

    def _abstain(self, reason: str) -> list[Candidate]:
        """Persist the empty candidate list and return it (the no-trade path)."""
        log.info("research abstain → save_candidates([]): %s", reason)
        # v1.6 Step 0 (observability): the exact free-text reason, for every non-pick
        # branch — broader than last_no_pick_reasoning (LLM prose, valid-abstain only).
        self.last_abort_detail = reason
        self.state.save_candidates([])
        return []
