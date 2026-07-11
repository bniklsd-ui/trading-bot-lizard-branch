"""Typed exception hierarchy for the abstain-lessons module (S1).

Mirrors the repo's per-phase ``code``-attribute pattern (see e.g.
``phase9_universe/universe/exceptions.py``). Independent of the other phase
hierarchies (phase isolation).
"""

from __future__ import annotations


class AbstainLessonError(Exception):
    """Base class for all abstain-lessons errors."""

    code: str = "ABSTAIN_LESSON_ERROR"


class AbstainStoreError(AbstainLessonError):
    """An ``AbstainStore`` operation failed (persistence)."""

    code = "ABSTAIN_STORE_ERROR"


class PaperTradeError(AbstainLessonError):
    """A ``PaperTradeStore`` operation failed (persistence)."""

    code = "PAPER_TRADE_ERROR"
