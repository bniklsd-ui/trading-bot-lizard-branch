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
``Brain``/``LessonExtractor`` (Step 7), ``resolve`` (Step 9) and ``RewardSink``
(Step 8) land here. Contract types are also importable directly from ``reward.models``.

Full design + the locked decisions A–J:
``../docs/concepts/phase7_reward_concept.md``.
"""

from __future__ import annotations

from reward.brain import Brain, LessonExtractor
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
    SyntheticSafetyError,
)
from reward.pnl_resolver import resolve
from reward.recorder import RewardSink
from reward.scorer import Scorer
from reward.synthetic import (
    SyntheticTrade,
    SyntheticTradeGenerator,
    guard_synthetic_path,
    select_edge_set,
)

__all__ = [
    "RewardConfig",
    "OpenedTrade",
    "ClosedTrade",
    "ConfidenceReport",
    "RewardResult",
    "LessonResult",
    "RewardError",
    "PnLUnavailable",
    "SyntheticSafetyError",
    "compute_confidence",
    "Scorer",
    "resolve",
    "RewardSink",
    "Brain",
    "LessonExtractor",
    "SyntheticTrade",
    "SyntheticTradeGenerator",
    "guard_synthetic_path",
    "select_edge_set",
]
