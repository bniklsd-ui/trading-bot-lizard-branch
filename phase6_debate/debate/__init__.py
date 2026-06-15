"""Phase 6 — debate package (Bull/Bear/Judge adversarial direction decision).

The first multi-agent AI path of the bot — **and the most expensive one**. AI is
used *only* for Bull/Bear arguments + Judge synthesis (final direction +
TRADE/ABSTAIN). Everything else — context assembly, budget/caps, persistence,
fail-closed handling — is deterministic code. The debate never sees the broker or
any VETO/Gate function, so it can't bypass a VETO.

Public exports grow per module (mirrors how the Phase-4 ``research`` package grew
its ``__init__``). Module 1 adds the data contracts; the orchestrator ``Debate``
lands with ``debate.py`` (Module 6) and is exported then. Contract types are also
importable directly from ``debate.models``.

Full design + the 11 locked decisions (A–K):
``../docs/concepts/phase6_debate_concept.md``.
"""

from __future__ import annotations

from debate.models import (
    AgentTurn,
    DebateBudgetExceeded,
    DebateConfig,
    DebateContext,
    DebateError,
    DebateLLMError,
    DebateOutcome,
)

__all__ = [
    "DebateConfig",
    "DebateContext",
    "AgentTurn",
    "DebateOutcome",
    "DebateError",
    "DebateBudgetExceeded",
    "DebateLLMError",
]
