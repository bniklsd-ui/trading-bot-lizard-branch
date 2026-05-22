"""Phase 2 — persistence layer.

Two stores, one principle: dumb, fast, reliable. Stores and returns; never judges.

- :class:`Database` — SQLite for historical trade data (outcomes, rewards,
  lessons) and the operational key-value config table.
- :class:`StateManager` — JSON files for short-lived operational state
  (account snapshot, bot config, research candidates) with TTL handling.
"""

from __future__ import annotations

from persistence.db import Database
from persistence.state import StateManager

__all__ = ["Database", "StateManager"]
