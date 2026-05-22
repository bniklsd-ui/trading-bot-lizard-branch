"""Seed values for the ``ig_config_state`` key-value table.

Inserted at DB init with ``INSERT OR IGNORE`` — existing values are never
overwritten. These are the operational defaults the bot starts from before any
trade has run. (Static config such as the trading window lives in the
``ig_config.json`` file, handled by :class:`persistence.state.StateManager`,
not here.)
"""

from __future__ import annotations

from datetime import datetime, timezone


def default_config_state() -> list[tuple[str, object, str]]:
    """Return seed ``(key, value, note)`` rows for ``ig_config_state``.

    ``value`` is a native Python object; the DB layer JSON-serializes it on write.
    ``session_date`` is stamped with the current UTC date at seed time.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return [
        ("bot_score", 50.0, "Accumulated reward score; 50 = neutral start"),
        ("risk_level", "KONSERVATIV", "Derived from bot_score (<50 KONSERVATIV)"),
        ("daily_pnl_today", 0.0, "Realized PNL for the current session date"),
        ("session_date", today, "Trading session date (YYYY-MM-DD)"),
        ("force_trigger_locked", False, "Manual override lock (locked when daily PNL < 0)"),
    ]
