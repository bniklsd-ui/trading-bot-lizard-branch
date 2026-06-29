"""Module 11 — ``scheduler/run.py`` offline helpers (argparse + config building).

No wiring import, no keyring, no network: ``scheduler.run`` keeps its cross-phase ``scripts.wiring``
import lazy inside ``main`` (the ig_bot.py pattern), so these unit tests exercise only the pure
front-end — the parser defaults/overrides, the demo-locked config builder, and ``--help`` exiting 0.
"""

from __future__ import annotations

import pytest

from scheduler.config import SchedulerConfig
from scheduler.run import build_arg_parser, config_from_args, parse_args


def test_defaults() -> None:
    args = parse_args([])
    assert args.daily_loss_cap == 1800.0
    assert args.no_loss_cap is False
    assert args.daily_token_budget == 200_000   # armed by default (runaway breaker ≈ €0.8/day)
    assert args.no_token_budget is False
    assert args.max_trades == 5
    assert args.cycle_interval_min == 5
    assert args.max_consecutive_failures == 3
    assert args.verbose is False


def test_overrides() -> None:
    args = parse_args(
        [
            "--daily-loss-cap", "500",
            "--daily-token-budget", "100000",
            "--max-trades", "2",
            "--cycle-interval-min", "1",
            "--max-consecutive-failures", "5",
            "--verbose",
        ]
    )
    assert args.daily_loss_cap == 500.0
    assert args.daily_token_budget == 100000
    assert args.max_trades == 2
    assert args.cycle_interval_min == 1
    assert args.max_consecutive_failures == 5
    assert args.verbose is True


def test_config_from_args_is_demo_locked_with_caps() -> None:
    cfg = config_from_args(parse_args([]))
    assert isinstance(cfg, SchedulerConfig)
    assert cfg.account == "demo"                 # hard demo-lock, regardless of args
    assert cfg.daily_loss_cap == 1800.0
    assert cfg.daily_token_budget == 200_000     # armed by default
    assert cfg.max_trades_per_day == 5
    assert cfg.cycle_interval_min == 5
    assert cfg.max_consecutive_failures == 3


def test_config_from_args_threads_overrides() -> None:
    cfg = config_from_args(
        parse_args(["--daily-loss-cap", "750", "--max-trades", "3", "--cycle-interval-min", "2"])
    )
    assert cfg.daily_loss_cap == 750.0
    assert cfg.max_trades_per_day == 3
    assert cfg.cycle_interval_min == 2
    assert cfg.account == "demo"


def test_no_loss_cap_disables_breaker() -> None:
    cfg = config_from_args(parse_args(["--no-loss-cap"]))
    assert cfg.daily_loss_cap is None            # breaker disabled (loud WARNING at construction)


def test_no_token_budget_disables_breaker() -> None:
    cfg = config_from_args(parse_args(["--no-token-budget"]))
    assert cfg.daily_token_budget is None        # token budget disabled (loud WARNING in budget.py)


def test_help_exits_zero() -> None:
    with pytest.raises(SystemExit) as exc:
        build_arg_parser().parse_args(["--help"])
    assert exc.value.code == 0
