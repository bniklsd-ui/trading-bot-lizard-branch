"""Module 8 — ``ResearchTick``: autonomous candidate generation (the phase's hard path).

Phase 8's mission is the **unattended generation of real demo trades**, and the one thing
that makes that possible is this module: every in-window cycle, the loop (Module 10
``runner.py``) calls :meth:`ResearchTick.ensure_candidates` to trigger the **real** Phase-4
``Research.run()``, which writes a fresh ``turbo_candidates.json`` the Phase-5 executor then
reads at Gate 2. It is the deliberate opposite of ``seed_candidate.py``: that operator tool
stamps a manual candidate whose ``reasoning`` carries the marker
``"MANUAL SEED (not a real research pick)"`` (``phase5_execution/scripts/seed_candidate.py``),
which the Phase-6 judge treats as un-tradeable → forced ABSTAIN. An autonomous candidate must
**never** carry that marker (``test_no_manual_seed_marker``). Without this module the scheduler
runs forever and collects **zero** outcome data.

**No new AI here.** The only AI is the single Phase-4 ``ask_candidate`` call *inside*
``Research.run()`` — reused unchanged. This module is pure mechanics around it: trigger,
classify the outcome, record a minimal ``no_trade_reason``, fail-closed on any error.

Two seams worth pinning (code = source of truth — see the reconciliations at the bottom):

- **``Research.run()`` returns only ``list[Candidate]`` — never a reason.** It collapses every
  non-PASS branch (session-health abort, empty universe, LLM error, validator reject, valid
  abstain, filter reject) to ``[]`` and only ``log.info``'s the granular cause to stderr
  (``phase4_research/research/research.py``). It also calls ``state.save_candidates(...)``
  exactly once per cycle internally (the pick, or ``[]`` on abstain). So from the return value
  this module can distinguish only three outcomes — **pick** / **abstain (`[]`)** /
  **exception** — and the concept §8 five-code taxonomy collapses to the v1 buckets
  :data:`REASON_PREFLIGHT` (exception) and :data:`REASON_LLM_ABSTAIN` (empty list). The finer
  three are declared for forward-compatibility but only set once Phase-4 surfaces a reason,
  which is Phase 9 (RESEARCH_V3) — Decision 5's "minimal now, full model = P9". This matches
  what ``safety.py`` already documents (it owns the *separate* gate-block taxonomy, this owns
  the no-candidate taxonomy).

- **Gate-2 freshness is *not* this module's job.** ``candidates_are_fresh()`` returns ``False``
  for an empty list (``persistence/state.py``), so a *bare* abstain would let Gate 2 re-call
  research and pay a second LLM bill. The fix lives in the wiring (Module 11): the executor is
  built with a **no-op** ``research_runner`` (verified Contract B), so the only real research
  is the one this module runs *before* ``executor.run()``. ``ResearchTick`` therefore just runs
  the real ``Research`` and never touches the executor seam.

Repo conventions apply (``from __future__ import annotations``, type hints + docstrings, one
file = one responsibility, logging to a module logger on stderr, never swallow silently). **No
network, no broker, no second LLM site.** The collaborator is duck-typed via a local
``typing.Protocol`` so ``import scheduler.research_tick`` pulls nothing cross-phase (the proven
package isolation; mirrors ``research.py``'s own Protocol approach and ``safety.py``/
``budget.py``).

---

Concept↔code reconciliations (dated 2026-06-28, code = source of truth):

H. **The five-code taxonomy collapses to two v1 buckets.** ``Research.run()`` returns only the
   candidate list (no reason), so v1 sets ``PREFLIGHT_FAIL`` (the run raised) or ``LLM_ABSTAIN``
   (the run returned ``[]``, the umbrella for every abstain sub-cause). ``EMPTY_UNIVERSE`` /
   ``VALIDATOR_REJECT`` / ``FILTER_FAIL`` are declared but reserved for P9, when Phase-4 returns
   a reason. Honest and consistent with Decision 5.

C. **Constructor reconciliation.** The concept §8 sketch is ``ResearchTick(research,
   state_store)`` — but this module only *mutates* the passed-in :class:`SchedulerState`
   (``last_research_ts`` / ``last_no_trade_reason``), the same mutate-and-return pattern
   ``state.record_cycle`` and ``backoff`` use; the **runner** is the single persistence owner
   (its ``finally: state_store.save(state)``, concept §10 loop). So ``state_store`` is dropped
   as an unused dependency. A keyword-only ``now_fn`` is added instead (the project's
   injectable-clock determinism rule; the sketch under-specified the timestamp source). The
   fail-closed clear on exception reuses the already-injected ``research.state`` (the Phase-2
   ``StateManager``), so no extra dependency is needed.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Protocol

from scheduler.state import SchedulerState

logger = logging.getLogger("scheduler.research_tick")

# No-candidate reason taxonomy (concept §8 / Decision 5). The loop folds the chosen reason into
# ``state.last_no_trade_reason`` for the state file / Web-UI. This is the *no-candidate*
# taxonomy; ``safety.py`` owns the separate *gate-block* taxonomy (CAP_BLOCK / KILL / ...).
#
# v1 populates only the two the return contract lets us tell apart (Reconciliation H):
REASON_LLM_ABSTAIN: str = "LLM_ABSTAIN"        # research.run() returned [] (umbrella for all v1 abstains)
REASON_PREFLIGHT: str = "PREFLIGHT_FAIL"       # research.run() raised → fail-closed
# declared for forward-compatibility / Phase 9 (RESEARCH_V3), NOT set in v1:
REASON_EMPTY_UNIVERSE: str = "EMPTY_UNIVERSE"
REASON_VALIDATOR_REJECT: str = "VALIDATOR_REJECT"
REASON_FILTER_FAIL: str = "FILTER_FAIL"


@dataclass(frozen=True)
class ResearchResult:
    """The outcome of one research tick (for the runner + tests).

    Attributes:
        picked: ``True`` iff a real candidate was written this tick (a tradeable pick).
        n: number of candidates written (0 or 1 — Phase-4 persists at most one pick).
        reason: the ``no_trade_reason`` when ``picked`` is ``False`` (one of the ``REASON_*``
            constants), else ``None``.
    """

    picked: bool
    n: int
    reason: str | None


class _ResearchLike(Protocol):
    """The slice of the Phase-4 ``Research`` orchestrator this module drives.

    Duck-typed on purpose so ``scheduler`` does not import the ``research`` package (phase
    isolation). The real ``research.research.Research`` satisfies it (it exposes ``.state`` —
    the Phase-2 ``StateManager`` — and ``run() -> list[Candidate]``); tests pass a tiny fake.
    """

    state: Any  # the Phase-2 StateManager (used only for the fail-closed clear on exception)

    def run(self) -> list: ...


class ResearchTick:
    """Triggers the real Phase-4 research once per cycle and classifies the outcome.

    Holds a reference to the injected ``Research`` (and a ``now_fn`` for the timestamp); it
    mutates the :class:`SchedulerState` passed to :meth:`ensure_candidates` and returns a
    :class:`ResearchResult`. It never persists the state itself — the runner owns that
    (Reconciliation C).

    Args:
        research: the real Phase-4 ``Research`` instance (built by the wiring, Module 11,
            sharing the warm broker/db/state — Contract G). Anything satisfying
            :class:`_ResearchLike` works.
        now_fn: returns the current (ideally tz-aware) time used to stamp
            ``last_research_ts``. Defaults to UTC now; the runner injects ``clock.now`` so the
            timestamp carries the daemon zone.
    """

    def __init__(
        self,
        research: _ResearchLike,
        *,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        self._research = research
        self._now_fn = now_fn or (lambda: datetime.now(timezone.utc))

    def ensure_candidates(self, state: SchedulerState) -> ResearchResult:
        """Run the real Phase-4 research and record the outcome onto ``state``.

        Always stamps ``state.last_research_ts`` (the attempt happened, whatever its result).
        Then:

        - **pick** — ``run()`` returned a non-empty list → clears ``last_no_trade_reason`` and
          returns ``ResearchResult(picked=True, n, reason=None)``. Phase-4 already wrote the
          fresh candidate file; the executor will trade it.
        - **abstain** — ``run()`` returned ``[]`` → sets ``last_no_trade_reason`` to
          :data:`REASON_LLM_ABSTAIN` and returns ``ResearchResult(False, 0, LLM_ABSTAIN)``.
          Phase-4 already wrote a fresh ``[]``.
        - **exception** — ``run()`` raised → logs ``critical`` (never re-raises; the
          data-collection loop must survive a bad research cycle), **defensively** clears the
          candidate file via the injected ``research.state`` so a stale prior pick cannot be
          traded by the executor's no-op runner, sets ``last_no_trade_reason`` to
          :data:`REASON_PREFLIGHT`, and returns ``ResearchResult(False, 0, PREFLIGHT_FAIL)``.

        Mutates and is the source of ``state.last_research_ts`` / ``last_no_trade_reason``; the
        runner persists the state afterwards.
        """
        state.last_research_ts = self._now_fn().isoformat()

        try:
            candidates = self._research.run()
        except Exception:  # noqa: BLE001 - fail-closed: a bad research cycle must not kill the loop
            logger.critical(
                "research tick failed — no candidate this cycle (fail-closed).",
                exc_info=True,
            )
            self._clear_candidates_fail_closed()
            state.last_no_trade_reason = REASON_PREFLIGHT
            return ResearchResult(picked=False, n=0, reason=REASON_PREFLIGHT)

        if candidates:
            state.last_no_trade_reason = None
            logger.info("research tick: %d candidate(s) written (PASS).", len(candidates))
            return ResearchResult(picked=True, n=len(candidates), reason=None)

        state.last_no_trade_reason = REASON_LLM_ABSTAIN
        logger.info("research tick: abstain (no candidate, reason=%s).", REASON_LLM_ABSTAIN)
        return ResearchResult(picked=False, n=0, reason=REASON_LLM_ABSTAIN)

    # --- internals ---------------------------------------------------------

    def _clear_candidates_fail_closed(self) -> None:
        """Best-effort: write a fresh empty candidate list so nothing stale gets traded.

        On a research exception the previous ``turbo_candidates.json`` is untouched and could
        still be within its 30-min TTL — the executor's no-op runner would then trade a stale
        pick. Writing ``[]`` (mirroring Phase-4's own abstain path) closes that hole. Itself
        guarded: a failure here is logged and swallowed (cleanup must not raise).
        """
        try:
            self._research.state.save_candidates([])
        except Exception:  # noqa: BLE001 - cleanup is best-effort; never raise out of fail-closed
            logger.critical(
                "research tick: fail-closed candidate clear also failed — a stale candidate "
                "may remain; the auto-confirm caps remain the backstop.",
                exc_info=True,
            )
