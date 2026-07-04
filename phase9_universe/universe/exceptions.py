"""Typed exception hierarchy for Phase 9 (V2 — Foundation).

Mirrors the Phase-4/5/6/7/8 ``code``-attribute pattern so callers can catch the
whole family with one ``except`` or be specific. Independent of the other phase
hierarchies (phase isolation).
"""

from __future__ import annotations


class UniverseError(Exception):
    """Base class for all Phase-9 universe errors."""

    code: str = "UNIVERSE_ERROR"


class UniverseSafetyError(UniverseError):
    """A safety invariant was violated — e.g. promotion attempted on a non-demo account.

    Raised, never silently guarded: promotion running against a live account would be
    exactly the kind of "temporary bypass" the project's hard rules forbid. There is
    no fallback path here (Decision D6) — fail loud, fail closed.
    """

    code = "UNIVERSE_SAFETY"


class UniverseStoreError(UniverseError):
    """A ``UniverseStore`` operation failed (e.g. an unknown status value)."""

    code = "UNIVERSE_STORE_ERROR"
