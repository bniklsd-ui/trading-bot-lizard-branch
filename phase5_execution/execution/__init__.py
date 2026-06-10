"""Phase 5 — execution pipeline (``execution`` package).

The first end-to-end *execution* path of the DAX CFD trading bot: Gates 1-5,
the four hard pre-trade VETOs (``pre_trade_check``), order placement with
write-ahead idempotency, position monitoring, and startup reconcile. Manual
trigger, IG **Demo** only, no scheduler (that is Phase 8).

**No AI here.** Every gate, VETO, sizing and order decision is deterministic
code. The only AI in the system stays the single Phase-4 research run, lazily
triggered through Gate 2.

This module deliberately exports nothing yet — the public surface
(``ExecutionConfig``, ``Executor``, the model dataclasses) lands with Step 1.
"""

from __future__ import annotations

__all__: list[str] = []
