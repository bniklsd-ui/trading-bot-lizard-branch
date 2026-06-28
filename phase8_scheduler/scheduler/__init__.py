"""Phase 8 — scheduler package (autonomous unattended demo trading).

"Scheduler" is only the name: the goal is **autonomous, unattended generation of
real demo trades**, because everything after Phase 8 (confidence out of
``INSUFFICIENT``, Phase-9 instinct-promotion) is gated on *real outcomes*. The hard
path is **autonomous candidate generation** via real Phase-4 research — never the
manual ``seed_candidate.py``.

**Phase 8 adds NO new AI.** A scheduler is pure mechanics: a long-running daemon
with market-hours phases (injectable ``now_fn`` / ``sleep_fn``), a deterministic
auto-confirm gate (demo-only, fail-closed), a file-based kill-switch, a daily-loss
circuit breaker, a token budget, and an idempotent reconcile pass. AI stays exactly
where it was — the Phase-4 pick, the Phase-6 debate, the Phase-7 lesson — all reused
unchanged. The scheduler never sees a Gate/VETO/order path; it drives the Phase-5
``Executor`` and records via the Phase-7 ``RewardSink`` through their seams.

Public exports grow per module (mirrors how the Phase-4 ``research`` / Phase-6
``debate`` / Phase-7 ``reward`` packages grew their ``__init__``). The build order
is binding: Cleanup -> Verify -> autonomous candidates -> Auto-Confirm/Safety ->
Reconcile -> Loop/Daemon -> (last) Web-UI.

Full design + the 20 locked decisions: ``../docs/concepts/phase8_scheduler_concept.md``.
"""

from __future__ import annotations

from .clock import Clock, Phase
from .config import SchedulerConfig
from .exceptions import PreflightError, SchedulerError
from .state import SchedulerState, StateStore

__all__ = [
    "SchedulerConfig",
    "SchedulerError",
    "PreflightError",
    "Clock",
    "Phase",
    "SchedulerState",
    "StateStore",
]
