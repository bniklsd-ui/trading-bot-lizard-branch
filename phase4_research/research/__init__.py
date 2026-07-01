"""Phase 4 — research package.

The single AI step of the bot (candidate selection) wrapped in deterministic
code-side validation, filtering, and persistence.

Public exports (Step 7): the orchestrator ``Research`` and the ``ResearchConfig``
tunable bundle, plus the v1.5 typed universe (``InstrumentSpec`` / ``load_universe`` /
``EXTENDED_UNIVERSE`` — the confirmed multi-instrument universe wiring opts into).
Other contract types (``Candidate``, ``ResearchContext``, ``ValidationResult``,
``FilterVerdict``, the exceptions) remain importable directly from ``research.models``.
"""

from __future__ import annotations

from research.models import EXTENDED_UNIVERSE, InstrumentSpec, ResearchConfig, load_universe
from research.research import Research

__all__ = ["Research", "ResearchConfig", "InstrumentSpec", "load_universe", "EXTENDED_UNIVERSE"]
