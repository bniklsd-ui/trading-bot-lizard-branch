"""Typed exception hierarchy for the Phase 5 execution pipeline.

Mirrors the Phase-1/3/4 pattern: one base (:class:`ExecutionError`) carrying a
``code`` class attribute, plus specific subclasses so callers can catch the whole
family or be precise. Independent of the sibling phases' hierarchies (phase
isolation). Exceptions are never swallowed silently — log + raise, or surface as
a result.

The orchestration contract (concept §8):

- ``GateRejected`` / ``VetoRejected`` are *informational* — a gate or VETO said
  "no trade". The executor turns these into a clean ``ExecutionResult`` with
  ``status="NO_TRADE"`` and exit 0; they are **not** failures.
- ``ExecutionAbort`` is **fail-closed**: something is unsafe to continue (session
  health, an unresolved ``PENDING`` order, a ``close_position`` failure). The
  operator must look; ``ig_bot.py`` exits non-zero.
- ``ReconcileConflict`` is the startup-reconcile flavour of an abort — broker
  truth disagrees with our record in a way we will not auto-resolve.
"""

from __future__ import annotations


class ExecutionError(Exception):
    """Base class for all Phase-5 execution errors."""

    code: str = "EXECUTION_ERROR"


class GateRejected(ExecutionError):
    """A Gate (1/2/3/5) declined the trade — a no-trade decision, not a fault."""

    code = "GATE_REJECTED"


class VetoRejected(ExecutionError):
    """A pre-trade VETO fired on the fresh snapshot — no-trade, not a fault."""

    code = "VETO_REJECTED"


class ExecutionAbort(ExecutionError):
    """Fail-closed abort: unsafe to continue, operator attention required.

    Raised for session-health failure, an unresolved ``PENDING`` order (never a
    blind second ``open_position``), or a failed ``close_position`` during
    monitoring. Distinct from a gate/VETO no-trade — this is an *error* path.
    """

    code = "EXECUTION_ABORT"


class ReconcileConflict(ExecutionError):
    """Startup reconcile found broker state we will not auto-resolve.

    E.g. an *unexpected* open position (broker has it, we have no record) while
    ``reconcile_unexpected_aborts`` is on — abort rather than stack another order.
    """

    code = "RECONCILE_CONFLICT"
