"""Module 1 — ``SchedulerConfig`` defaults, immutability, and the loss-cap WARNING.

No network, no broker, no LLM, no I/O: pure dataclass checks plus a ``caplog`` probe
of the single startup WARNING. The defaults asserted here are the locked concept §1
values, with the two documented reconciliations (full-market ``09:00–17:30`` window
held as ``HH:MM`` strings — see ``scheduler/config.py``).
"""

from __future__ import annotations

import dataclasses
import logging

import pytest

from scheduler import SchedulerConfig as ExportedSchedulerConfig
from scheduler.config import SchedulerConfig


def test_defaults_match_locked_concept_values() -> None:
    """Every default equals the concept §1 / operator-confirmed value."""
    cfg = SchedulerConfig()

    # time / window
    assert cfg.tz == "Europe/Berlin"
    assert cfg.cycle_interval_min == 5
    assert cfg.idle_poll_min == 5
    assert cfg.pre_open_lead_min == 10

    # caps / safety
    assert cfg.account == "demo"
    assert cfg.max_trades_per_day == 5
    assert cfg.daily_loss_cap is None
    assert cfg.max_consecutive_failures == 3
    assert cfg.backoff_base_s == 30.0
    assert cfg.backoff_cap_s == 600.0

    # budget — armed by default (v1 runaway breaker ≈ €0.8/day); None ⇒ explicitly disabled
    assert cfg.daily_token_budget == 200_000

    # reconcile
    assert cfg.reconcile_interval_min == 15

    # universe refresh (Phase 9 / V2)
    assert cfg.universe_refresh_interval_min == 240

    # data path (Phase 9 / V2) — IG bar chain OFF by default (yFinance-only, bit-identical)
    assert cfg.enable_ig_bars is False

    # Phase 10 (V3) abstain-lessons — on by default (classification+persistence),
    # reflect (the one AI call) also on by default, shared daily cap 10
    assert cfg.enable_abstain_lessons is True
    assert cfg.enable_abstain_reflect is True
    assert cfg.reflect_daily_cap == 10

    # Phase 10 (V3) market_context + paper-trades (Block B) — context persistence + Both-
    # Sides-Shadow paper trades on by default; Council-Paper-Call (debate) off (deferred)
    assert cfg.enable_context_persistence is True
    assert cfg.enable_paper_trades is True
    assert cfg.enable_paper_debate is False
    assert cfg.paper_debate_daily_cap == 3

    # paths (gitignored data/ tree)
    assert cfg.live_db_path == "data/trading_bot.sqlite"
    assert cfg.state_path == "data/state/scheduler_state.json"
    assert cfg.kill_path == "data/state/KILL"
    assert cfg.command_path == "data/state/scheduler_command.json"
    # v1.6 (Phase-8 hotfix Step 0, observability)
    assert cfg.observability_path == "data/state/research_health.jsonl"


def test_window_is_full_market_not_the_concept_morning_window() -> None:
    """The reconciliation: full-market 09:00–17:30 (operator), NOT 09:30–11:19.

    The concept §1 draft defaulted to a narrow morning window and mis-labelled it
    "aus P5-Config"; the real P5 window is 09:00–17:30. Pin the corrected default so a
    silent regression back to the concept string is caught.
    """
    cfg = SchedulerConfig()
    assert cfg.window_open == "09:00"
    assert cfg.window_close == "17:30"
    # explicitly not the mis-attributed concept morning window
    assert (cfg.window_open, cfg.window_close) != ("09:30", "11:19")


def test_window_fields_are_hhmm_strings_not_time_objects() -> None:
    """Reconciliation: window held as ``HH:MM`` strings (reuse P5), not ``time``."""
    cfg = SchedulerConfig()
    assert isinstance(cfg.window_open, str)
    assert isinstance(cfg.window_close, str)


def test_is_frozen() -> None:
    """Immutable config — a single instance parameterises the whole daemon."""
    cfg = SchedulerConfig()
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.max_trades_per_day = 99  # type: ignore[misc]


def test_non_demo_account_is_constructable_here() -> None:
    """``config`` does not enforce the demo-lock — ``safety.py`` does (Decision 7).

    Separation of concerns: a ``"live"`` config is *buildable* (so tests and a future
    go-live can exist), but ``AutoConfirm`` refuses it. Constructing it must not raise.
    """
    cfg = SchedulerConfig(account="live")
    assert cfg.account == "live"


def test_none_loss_cap_logs_exactly_one_warning(caplog: pytest.LogCaptureFixture) -> None:
    """``daily_loss_cap=None`` (the default) ⇒ one loud WARNING, no crash."""
    with caplog.at_level(logging.WARNING, logger="scheduler.config"):
        SchedulerConfig()
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "daily_loss_cap" in warnings[0].message
    assert "INACTIVE" in warnings[0].message


def test_set_loss_cap_emits_no_warning(caplog: pytest.LogCaptureFixture) -> None:
    """A consciously-set cap is silent — the warning is only for the inactive case."""
    with caplog.at_level(logging.WARNING, logger="scheduler.config"):
        cfg = SchedulerConfig(daily_loss_cap=1800.0)
    assert cfg.daily_loss_cap == 1800.0
    assert [r for r in caplog.records if r.levelno == logging.WARNING] == []


def test_none_token_budget_is_accepted_without_config_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """``daily_token_budget=None`` is valid here; its WARNING belongs to ``budget.py``.

    Constructing with a set loss cap + ``None`` budget must produce no config-level
    warning (config warns only for the loss cap — one warning per responsibility).
    """
    with caplog.at_level(logging.WARNING, logger="scheduler.config"):
        cfg = SchedulerConfig(daily_loss_cap=1800.0, daily_token_budget=None)
    assert cfg.daily_token_budget is None
    assert [r for r in caplog.records if r.levelno == logging.WARNING] == []


def test_full_override_roundtrips() -> None:
    """All-custom construction reads back unchanged; untouched fields keep defaults."""
    cfg = SchedulerConfig(
        window_open="10:00",
        window_close="12:30",
        tz="Europe/London",
        cycle_interval_min=3,
        idle_poll_min=2,
        pre_open_lead_min=15,
        account="live",
        max_trades_per_day=8,
        daily_loss_cap=500.0,
        max_consecutive_failures=5,
        backoff_base_s=10.0,
        backoff_cap_s=120.0,
        daily_token_budget=1_000_000,
        reconcile_interval_min=30,
        universe_refresh_interval_min=60,
        live_db_path="/tmp/x.sqlite",
        state_path="/tmp/state.json",
        kill_path="/tmp/KILL",
        command_path="/tmp/cmd.json",
        observability_path="/tmp/health.jsonl",
    )
    assert cfg.window_open == "10:00"
    assert cfg.window_close == "12:30"
    assert cfg.tz == "Europe/London"
    assert cfg.cycle_interval_min == 3
    assert cfg.account == "live"
    assert cfg.daily_loss_cap == 500.0
    assert cfg.max_consecutive_failures == 5
    assert cfg.daily_token_budget == 1_000_000
    assert cfg.reconcile_interval_min == 30
    assert cfg.universe_refresh_interval_min == 60
    assert cfg.live_db_path == "/tmp/x.sqlite"
    assert cfg.observability_path == "/tmp/health.jsonl"


def test_exported_from_package_root() -> None:
    """``from scheduler import SchedulerConfig`` is the same object as the submodule's."""
    assert ExportedSchedulerConfig is SchedulerConfig
