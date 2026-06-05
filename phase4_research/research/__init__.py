"""Phase 4 — research package.

The single AI step of the bot (candidate selection) wrapped in deterministic
code-side validation, filtering, and persistence.

Public exports are intentionally **not** declared yet: the orchestrator
(``Research``) and ``ResearchConfig`` are exported here once the orchestrator
exists (Step 7). Until then, import contract types directly from
``research.models``.
"""

from __future__ import annotations
