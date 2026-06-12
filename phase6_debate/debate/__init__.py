"""Phase 6 — debate package (Bull/Bear/Judge adversarial direction decision).

The first multi-agent AI path of the bot — **and the most expensive one**. AI is
used *only* for Bull/Bear arguments + Judge synthesis (final direction +
TRADE/ABSTAIN). Everything else — context assembly, budget/caps, persistence,
fail-closed handling — is deterministic code. The debate never sees the broker or
any VETO/Gate function, so it can't bypass a VETO.

Public exports (later steps): the orchestrator ``Debate`` plus ``DebateConfig`` /
``DebateOutcome``. They land with ``models.py`` (Module 1) and ``debate.py``
(Module 6); this scaffold deliberately exports **nothing yet** (same precedent as
the Phase-4 ``research`` package at its Step-1 scaffold). Contract types stay
importable directly from ``debate.models`` once they exist.

Full design + the 11 locked decisions (A–K):
``../docs/concepts/phase6_debate_concept.md``.
"""

from __future__ import annotations

__all__: list[str] = []
