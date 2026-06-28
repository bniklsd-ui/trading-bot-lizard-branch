"""Module 9 (concept §6) — ``BackoffTracker``: consecutive-failure tracking + backoff schedule.

A long-running unattended daemon must not hot-loop on a broken dependency (auth / keyring / DB /
network) nor churn forever silently failing. This module is the loop's failure memory: it counts
**consecutive** cycle exceptions, hands the loop an exponentially growing sleep between retries,
and — after ``max_consecutive_failures`` in a row — reports that the loop should trip
(``should_trip``). For a demo data-collector a trip is cheap (restart next day), so the design
tips toward tripping *early* rather than letting a stuck bot run (Decision 9).

**Advisory only.** ``BackoffTracker`` tracks the counter and computes the delay / trip verdict;
it does **not** touch the kill-switch. The runner (Module 10 ``runner.py``) is what calls
``killswitch.set_kill(..., "auto:backoff")`` + ``shutdown()`` when ``should_trip`` is true — the
same single-responsibility split as the killswitch trip-*log* living in the runner, not in
``killswitch.py``.

**No AI, no network, no broker, no I/O** — pure arithmetic over the injected
:class:`~scheduler.config.SchedulerConfig` and the :class:`~scheduler.state.SchedulerState`
counter (whose docstring already declares ``consecutive_failures`` is *owned by this module* —
``record_cycle`` never touches it, and ``rollover_if_new_day`` resets it each Europe/Berlin day).

Repo conventions apply (``from __future__ import annotations``, type hints + docstrings, one file
= one responsibility, logging to a module logger, never swallow silently). ``import
scheduler.backoff`` pulls nothing cross-phase.

---

Concept↔code reconciliations (dated 2026-06-28, code = source of truth):

1. **Advisory, not self-tripping.** Concept §6 says "trip → kill-switch ``auto:backoff`` + clean
   shutdown", but that orchestration is the **runner's** (§10 loop): ``BackoffTracker`` only
   reports ``should_trip``. Keeps single responsibility (mirrors the killswitch trip-log living
   in the runner, not in ``killswitch.py``).

2. **``delay_s`` is total — ``n <= 0 → 0.0``.** The §6 sketch ``min(base·2^(n-1), cap)`` is
   undefined at ``n=0``; the guard makes the method safe to call any time (in practice the loop
   only calls it after ``record_failure``, so ``n >= 1``). The ``cap`` bounds the result, so no
   overflow guard is needed.

3. **Mutate-and-return** (the same object, not a fresh one), consistent with
   ``state.record_cycle`` / ``research_tick.ensure_candidates``; the runner is the single
   persistence owner (its ``finally: state_store.save``).
"""

from __future__ import annotations

import logging

from scheduler.config import SchedulerConfig
from scheduler.state import SchedulerState

logger = logging.getLogger("scheduler.backoff")


class BackoffTracker:
    """Tracks consecutive cycle failures and computes the retry backoff (concept §6).

    Reads three knobs off the config: ``max_consecutive_failures`` (the trip threshold),
    ``backoff_base_s`` and ``backoff_cap_s`` (the exponential schedule). Stateless itself — the
    count lives on the :class:`SchedulerState` it mutates, so a restart resumes from the
    persisted counter.

    Args:
        config: the frozen :class:`~scheduler.config.SchedulerConfig`.
    """

    def __init__(self, config: SchedulerConfig) -> None:
        self._config = config

    def record_success(self, state: SchedulerState) -> SchedulerState:
        """Reset the consecutive-failure counter after a clean cycle. Mutates and returns.

        Touches **only** ``consecutive_failures`` (not ``kill_reason``, the day counters, or
        ``last_no_trade_reason``) — those belong to other modules.
        """
        state.consecutive_failures = 0
        return state

    def record_failure(self, state: SchedulerState) -> SchedulerState:
        """Increment the consecutive-failure counter after a cycle exception. Mutates and returns.

        Touches **only** ``consecutive_failures``. The loop calls this in its ``except`` branch,
        then consults :meth:`should_trip` / :meth:`delay_s`.
        """
        state.consecutive_failures += 1
        logger.warning(
            "cycle failure recorded — consecutive_failures=%d (trip at %d).",
            state.consecutive_failures,
            self._config.max_consecutive_failures,
        )
        return state

    def should_trip(self, state: SchedulerState) -> bool:
        """Return whether the loop should trip the kill-switch and stop.

        ``True`` once ``consecutive_failures >= config.max_consecutive_failures``. The **runner**
        acts on it (``killswitch.set_kill(..., "auto:backoff")`` + clean shutdown); this method
        only reports the verdict.
        """
        return state.consecutive_failures >= self._config.max_consecutive_failures

    def delay_s(self, state: SchedulerState) -> float:
        """Seconds to sleep before the next cycle, given the current failure streak.

        ``min(backoff_base_s * 2**(n-1), backoff_cap_s)`` for ``n = consecutive_failures >= 1``;
        ``0.0`` for ``n <= 0`` (no failures — defensive, the loop calls this only after a
        failure). With the defaults (base 30s, cap 600s): n=1→30, n=2→60, n=3→120, …, capped at
        600. The cap bounds the result.
        """
        n = state.consecutive_failures
        if n <= 0:
            return 0.0
        return min(self._config.backoff_base_s * (2 ** (n - 1)), self._config.backoff_cap_s)
