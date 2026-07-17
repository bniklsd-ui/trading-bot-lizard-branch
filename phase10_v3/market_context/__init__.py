"""Phase 10 (V3) Block B — market_regime_snapshots + decision_context.

Own-connection SQLite writer for the two persistence-reform tables (migration 005,
already on ``main`` since Block A). Deterministic feature extraction only — no AI,
``regime_tag`` is observe-only and gates nothing (V3-D4).
"""

from __future__ import annotations

from market_context.exceptions import MarketContextError
from market_context.models import DecisionContext, RegimeSnapshot
from market_context.regime import classify_regime_tag, compute_regime_features
from market_context.writer import ContextRecorder, MarketContextWriter

__all__ = [
    "MarketContextError",
    "RegimeSnapshot",
    "DecisionContext",
    "compute_regime_features",
    "classify_regime_tag",
    "MarketContextWriter",
    "ContextRecorder",
]
