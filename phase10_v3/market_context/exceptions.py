"""Typed exception hierarchy for the market_context module (Block B, Step 9).

Mirrors ``abstain_lessons/exceptions.py``'s per-phase ``code``-attribute pattern.
Independent of the other phase hierarchies (phase isolation).
"""

from __future__ import annotations


class MarketContextError(Exception):
    """A ``MarketContextWriter`` operation failed (persistence)."""

    code: str = "MARKET_CONTEXT_ERROR"
