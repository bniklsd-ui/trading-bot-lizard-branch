"""Tests for ``scripts.wiring._sampler_due`` (Phase 17 B-2).

Pure module-level helper, no keyring / broker / daemon composition. Three contract
cases (per Plan §6 B-2 + §7 AK5):

1. ``_sampler_due`` returns False on a weekend and before ``window_open + 40min``.
2. ``_sampler_due`` returns True mid-window (e.g. 09:50 Berlin on a weekday).
3. ``_sampler_due`` reuses the :class:`~scheduler.clock.Clock` phase classification,
   so a Sunday at 12:00 Berlin returns False even though the time-of-day is inside
   the trading window (the WINDOW classification is weekday-only).

Setup mirrors ``test_wiring_schema_floor.py``: ``scripts/wiring.py`` is not an
installed package, so we add the project dir to ``sys.path`` exactly like
``scripts/live_test.py`` does. This is import-offline-safe because ``scripts.wiring``'s
top-level imports are intra-package ``scheduler.*`` only.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# scripts/ -> phase8_scheduler/ (so ``from scripts.wiring import ...`` resolves)
_PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(_PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(_PROJECT_DIR))

from scripts.wiring import _sampler_due  # noqa: E402
from scheduler.config import SchedulerConfig  # noqa: E402


def _cfg() -> SchedulerConfig:
    """A minimal scheduler config for the gate — uses production defaults
    (``window_open=09:00``, ``window_close=17:30``, tz Europe/Berlin) so the helper
    is exercised in the same shape as the wiring ``scheduler.config`` consumed.
    Only feature flags the gate cares about are overridden; the rest stay default.
    """
    return SchedulerConfig(
        daily_loss_cap=1800.0,    # silence the WARNING in __post_init__
        live_db_path="/tmp/test_sampler_gate_trading_bot.sqlite",
        state_path="/tmp/test_sampler_gate_state.json",
        kill_path="/tmp/test_sampler_gate_KILL",
        command_path="/tmp/test_sampler_gate_CMD",
        observability_path="/tmp/test_sampler_gate_observability.jsonl",
    )


def test_sampler_due_false_on_weekend_and_before_open_plus_40() -> None:
    """Saturday at 12:00 Berlin — weekend, even though inside the trading hours, must
    return False (the Clock classifies non-trading days as IDLE)."""
    cfg = _cfg()
    saturday_noon = datetime(2026, 10, 17, 12, 0, tzinfo=ZoneInfo("Europe/Berlin"))
    assert _sampler_due(saturday_noon, cfg) is False

    # Monday at 09:00 — inside window but only the opening instant, NOT yet +40 min.
    cfg = _cfg()
    monday_open = datetime(2026, 10, 19, 9, 0, tzinfo=ZoneInfo("Europe/Berlin"))
    assert _sampler_due(monday_open, cfg) is False

    # Monday at 09:39 — still under the +40 min threshold.
    cfg = _cfg()
    monday_just_before = datetime(2026, 10, 19, 9, 39, 59, tzinfo=ZoneInfo("Europe/Berlin"))
    assert _sampler_due(monday_just_before, cfg) is False

    # Monday at 17:30 exactly — at the boundary (inclusive window), still >= +40 min.
    # We test the AFTER-CLOSE case explicitly in the next test.


def test_sampler_due_true_mid_window() -> None:
    """Monday at 09:50 Berlin — inside the trading window AND >= +40 min after open."""
    cfg = _cfg()
    monday_late_open = datetime(2026, 10, 19, 9, 50, tzinfo=ZoneInfo("Europe/Berlin"))
    assert _sampler_due(monday_late_open, cfg) is True

    # Mid-session (12:00 Berlin on a weekday).
    cfg = _cfg()
    monday_midday = datetime(2026, 10, 19, 12, 0, tzinfo=ZoneInfo("Europe/Berlin"))
    assert _sampler_due(monday_midday, cfg) is True

    # Right before close (17:29 Berlin on a weekday) — still inside the window.
    cfg = _cfg()
    monday_just_before_close = datetime(2026, 10, 19, 17, 29, 59, tzinfo=ZoneInfo("Europe/Berlin"))
    assert _sampler_due(monday_just_before_close, cfg) is True

    # After close (17:30+30 = 18:00 Berlin on a weekday) — must be False.
    cfg = _cfg()
    monday_after_close = datetime(2026, 10, 19, 18, 0, tzinfo=ZoneInfo("Europe/Berlin"))
    assert _sampler_due(monday_after_close, cfg) is False