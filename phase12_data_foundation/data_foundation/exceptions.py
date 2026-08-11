"""Typed exception hierarchy for Phase 12 (Datenfundament).

Mirrors the `code`-attribute pattern used across the other phases (Phase 4/5/6/7/8/9)
so callers can catch the whole family with one `except` or be specific. Independent
of the other phase hierarchies (phase isolation, D3).
"""

from __future__ import annotations


class DataFoundationError(Exception):
    """Base class for all Phase-12 data-foundation errors."""

    code: str = "DATA_FOUNDATION_ERROR"
    retryable: bool = False


class ArchiveError(DataFoundationError):
    """A ``BarArchive`` operation failed (e.g. an unknown source string)."""

    code = "ARCHIVE_ERROR"


class BudgetError(DataFoundationError):
    """A ``SourceBudget`` operation failed (e.g. an unknown quota source)."""

    code = "BUDGET_ERROR"


class ResolverError(DataFoundationError):
    """A ``SymbolResolver`` operation failed in a way that isn't the normal
    fail-soft-per-epic path (Step 3) — reserved for programmer-error cases."""

    code = "RESOLVER_ERROR"
