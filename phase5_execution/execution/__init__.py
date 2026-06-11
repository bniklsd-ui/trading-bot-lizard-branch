"""Phase 5 — execution pipeline (``execution`` package).

The first end-to-end *execution* path of the DAX CFD trading bot: Gates 1-5,
the four hard pre-trade VETOs (``pre_trade_check``), order placement with
write-ahead idempotency, position monitoring, and startup reconcile. Manual
trigger, IG **Demo** only, no scheduler (that is Phase 8).

**No AI here.** Every gate, VETO, sizing and order decision is deterministic
code. The only AI in the system stays the single Phase-4 research run, lazily
triggered through Gate 2.

Public surface: the orchestrator ``Executor``, the ``ExecutionConfig`` tunable
bundle, the result/plan dataclasses, and the write-ahead ``ExecutionState`` store.
The gate/VETO/order/monitor functions remain importable from their own submodules
(``execution.gates`` / ``execution.vetos`` / ``execution.order`` / ``execution.monitor``).
"""

from __future__ import annotations

from execution.config import ExecutionConfig
from execution.execution_state import ExecutionState
from execution.executor import Executor
from execution.models import ExecutionResult, GateVerdict, OrderPlan, VetoVerdict

__all__ = [
    "Executor",
    "ExecutionConfig",
    "ExecutionState",
    "ExecutionResult",
    "OrderPlan",
    "GateVerdict",
    "VetoVerdict",
]
