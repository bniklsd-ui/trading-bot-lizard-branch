"""Phase 15 — Block C Instinct-ECC package (Plan §6 C2).

Aggregates free-text lessons + reward outcomes into **structured Instincts**, validates
them deterministically, and gates promotion to VETO 5 (Plan §6 C3) behind
``n_closed >= InstinctConfig.instinct_n_min`` AND ``InstinctConfig.enable_instinct_promotion``
(P10/P12). The four sub-modules split the responsibility cleanly:

- :mod:`instinct.models`     — ``Instinct`` + ``InstinctConfig`` (frozen dataclasses)
- :mod:`instinct.extractor`  — LLM call (best-effort, never raises; mirrors ``Brain.reflect``)
- :mod:`instinct.validator`  — deterministic code-only check (NO LLM; Plan §1 P11)
- :mod:`instinct.promotion`  — ``promote_eligible`` gate (P10/P12)

Schema (table ``instincts``) is wörtlich nach ``docs/concepts/phase7_reward_concept.md §7b``:
``trigger`` / ``domain`` ∈ {entry,exit,sizing,timing} / ``confidence`` /
``evidence_trade_ids[]`` / ``contradictions_trade_ids[]``. Lifecycle status
(``proposed`` / ``validated`` / ``refuted`` / ``promoted`` / ``archived``) is the C1
addition (Plan §6 C1, Migration 009).

Phase isolation (Decision F-pattern, mirror Phase 7 ``Brain``): the extractor uses a
duck-typed ``_LLMClientLike`` Protocol — **never** imports ``research.LLMClient``.
The wiring in Phase 15 (later step) builds the real client; tests use a fake.
"""

from instinct.bridge import InstinctBridge
from instinct.compile import (
    TRIGGER_RE,
    compile_rule,
    compile_rules,
    instinct_from_row,
)
from instinct.extractor import (
    InstinctExtractor,
    InstinctExtractionResult,
    SingleShotInstinctExtractor,
)
from instinct.models import (
    DOMAINS,
    INSTINCT_STATUSES,
    Instinct,
    InstinctConfig,
    is_valid_domain,
    is_valid_status,
)
from instinct.promotion import promote_eligible
from instinct.validator import (
    InstinctValidation,
    InstinctValidator,
)

__all__ = [
    "DOMAINS",
    "INSTINCT_STATUSES",
    "Instinct",
    "InstinctBridge",
    "InstinctConfig",
    "InstinctExtractionResult",
    "InstinctExtractor",
    "InstinctExtractionResult",
    "InstinctValidation",
    "InstinctValidator",
    "SingleShotInstinctExtractor",
    "TRIGGER_RE",
    "compile_rule",
    "compile_rules",
    "instinct_from_row",
    "is_valid_domain",
    "is_valid_status",
    "promote_eligible",
]
