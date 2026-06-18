"""Phase 7 — reward package (process-aware score + lessons + observe-only confidence).

The phase where the bot starts *learning*. AI is used **only** for the
lesson-extraction ``reflect()`` (one Haiku call, best-effort). Everything else —
the reward score delta (outcome + process), the confidence math (Wilson lower
bound, expectancy-R, SQN, N_min gating), P&L resolution, persistence, and
fail-closed error handling — is deterministic code. The score's ``confidence`` is
**observe-only and gates nothing**; there is **no VETO touch** (the full
Instinct→VETO promotion is deferred to Phase 9 / concept §7b).

Public exports grow per module (mirrors how the Phase-4 ``research`` and Phase-6
``debate`` packages grew their ``__init__``). Step 3 adds the data contracts +
config + exceptions; ``compute_confidence`` (Step 4), ``Scorer`` (Step 5),
``Brain`` (Step 7) and ``RewardSink`` (Step 10) land later. Contract types are
also importable directly from ``reward.models``.

Full design + the locked decisions A–J:
``../docs/concepts/phase7_reward_concept.md``.
"""

from __future__ import annotations

from reward.confidence import compute_confidence
from reward.models import (
    ClosedTrade,
    ConfidenceReport,
    LessonResult,
    OpenedTrade,
    PnLUnavailable,
    RewardConfig,
    RewardError,
    RewardResult,
)
from reward.scorer import Scorer

__all__ = [
    "RewardConfig",
    "OpenedTrade",
    "ClosedTrade",
    "ConfidenceReport",
    "RewardResult",
    "LessonResult",
    "RewardError",
    "PnLUnavailable",
    "compute_confidence",
    "Scorer",
]
