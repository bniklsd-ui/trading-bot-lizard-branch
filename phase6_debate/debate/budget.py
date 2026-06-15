"""Module 5 — the debate's hard cost caps + cumulative metering (Decision E/J).

Phase 6 is the **most expensive path in the bot**, so cost discipline is a
*structure*, not a convention. :class:`DebateBudget` accumulates the per-turn
usage records the caching seam (Module 4 ``ask_agent``) hands back and enforces
four hard caps — total turns, cumulative input tokens, cumulative output tokens,
and wall-clock time per cycle. The **first** breach raises
:class:`~debate.models.DebateBudgetExceeded`, which the orchestrator (Module 6)
catches and turns into a fail-closed ABSTAIN. A breach never "trades anyway".

The clock is **injected** (``now_fn``, defaulting to ``time.monotonic`` — the same
DI pattern Phase-5 ``executor``/``monitor`` use), so the wall-clock cap is fully
deterministic under test with no real sleeping.

This module is pure code (no AI, no network, no broker). It imports only
``debate.models`` + stdlib — same phase isolation as the other ``debate`` modules;
the documented cross-phase reuse of the Phase-4 LLM stack lives in
``llm_caching``, not here. The usage dict ``register`` consumes is exactly the
``research.token_meter`` record shape (``input_tokens`` / ``output_tokens`` /
``cache_read_input_tokens`` / ``cache_creation_input_tokens`` / ``est_cost_usd`` /
``est_cost_eur``) — or ``{}`` when the shared client captured none.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable

from debate.models import DebateBudgetExceeded, DebateConfig

log = logging.getLogger(__name__)


def _as_int(usage: dict[str, Any], key: str) -> int:
    """Read ``usage[key]`` as a non-negative int, tolerating absent/``None``."""
    return int(usage.get(key, 0) or 0)


def _as_float(usage: dict[str, Any], key: str) -> float:
    """Read ``usage[key]`` as a float, tolerating absent/``None``."""
    return float(usage.get(key, 0.0) or 0.0)


class DebateBudget:
    """Accumulate per-turn usage and fail closed on the first cap breach.

    Usage pattern (Module-6 orchestrator): after every Bull/Bear/Judge turn,
    ``register(usage)`` the record ``ask_agent`` returned, then ``check()`` — the
    first breach raises :class:`DebateBudgetExceeded`. ``summary()`` gives the
    aggregate for ``DebateOutcome.token_summary`` (and, via the audit, Phase 9).

    Boundary semantics: each cap is the **maximum allowed** — ``> cap`` is a
    breach, ``== cap`` is fine. All four caps come from the :class:`DebateConfig`.
    """

    def __init__(
        self,
        config: DebateConfig,
        *,
        now_fn: Callable[[], float] = time.monotonic,
    ) -> None:
        """Start the budget at "now", zeroing every accumulator.

        Args:
            config: the run's :class:`DebateConfig` — supplies the four caps
                (``max_total_calls`` / ``max_cumulative_input_tokens`` /
                ``max_cumulative_output_tokens`` / ``wall_clock_timeout_s``).
            now_fn: injected monotonic clock; defaults to ``time.monotonic``.
                Tests pass a scripted fake so the wall-clock cap is deterministic
                with no real waiting.
        """
        self._config = config
        self._now_fn = now_fn
        self._start = now_fn()

        self._total_calls = 0
        self._input_tokens = 0
        self._output_tokens = 0
        self._cache_read_input_tokens = 0
        self._cache_creation_input_tokens = 0
        self._est_cost_usd = 0.0
        self._est_cost_eur = 0.0

    def register(self, usage: dict[str, Any]) -> None:
        """Fold one turn's usage record into the running totals.

        Counts the turn (one request) and adds its token/cost fields. A missing
        key or an empty ``{}`` (the shared client captured no usage) is tolerated —
        it still counts as a turn but contributes zero tokens/cost.

        Args:
            usage: the ``token_meter`` record dict ``ask_agent`` returned, or ``{}``.
        """
        self._total_calls += 1
        self._input_tokens += _as_int(usage, "input_tokens")
        self._output_tokens += _as_int(usage, "output_tokens")
        self._cache_read_input_tokens += _as_int(usage, "cache_read_input_tokens")
        self._cache_creation_input_tokens += _as_int(usage, "cache_creation_input_tokens")
        self._est_cost_usd += _as_float(usage, "est_cost_usd")
        self._est_cost_eur += _as_float(usage, "est_cost_eur")

    def check(self) -> None:
        """Raise :class:`DebateBudgetExceeded` on the **first** cap breach.

        Checks total turns, cumulative input/output tokens, and elapsed wall-clock
        (against the injected clock). ``> cap`` breaches; ``== cap`` is allowed.
        The orchestrator (Module 6) converts the exception to a fail-closed ABSTAIN.

        Raises:
            DebateBudgetExceeded: a hard cap was exceeded.
        """
        cfg = self._config

        if self._total_calls > cfg.max_total_calls:
            self._breach(
                f"total turns {self._total_calls} > cap {cfg.max_total_calls}"
            )
        if self._input_tokens > cfg.max_cumulative_input_tokens:
            self._breach(
                f"cumulative input tokens {self._input_tokens} "
                f"> cap {cfg.max_cumulative_input_tokens}"
            )
        if self._output_tokens > cfg.max_cumulative_output_tokens:
            self._breach(
                f"cumulative output tokens {self._output_tokens} "
                f"> cap {cfg.max_cumulative_output_tokens}"
            )

        elapsed = self._now_fn() - self._start
        if elapsed > cfg.wall_clock_timeout_s:
            self._breach(
                f"wall-clock {elapsed:.3f}s > cap {cfg.wall_clock_timeout_s}s"
            )

    def summary(self) -> dict[str, Any]:
        """Return the aggregate for ``DebateOutcome.token_summary``.

        The key set is exactly what the Module-7 audit (concept §7) ingests, so the
        Phase-9 ``decision_context`` / ``market_regime_snapshots`` tables take it
        without reshaping. ``total_calls`` is an additive extra (harmless for the
        forward-compatible ingest).
        """
        return {
            "input_tokens": self._input_tokens,
            "output_tokens": self._output_tokens,
            "cache_read_input_tokens": self._cache_read_input_tokens,
            "cache_creation_input_tokens": self._cache_creation_input_tokens,
            "est_cost_usd": round(self._est_cost_usd, 6),
            "est_cost_eur": round(self._est_cost_eur, 6),
            "total_calls": self._total_calls,
        }

    def _breach(self, detail: str) -> None:
        """Log the breach to stderr and raise the fail-closed exception."""
        log.warning("debate budget exceeded: %s", detail)
        raise DebateBudgetExceeded(detail)
