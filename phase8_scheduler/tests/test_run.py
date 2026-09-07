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
    assert args.daily_token_budget == 300_000   # armed by default (runaway breaker ≈ €1.2/day, Phase 16 C3 was 200k)
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
    assert cfg.daily_token_budget == 300_000     # armed by default (Phase 16 C3)
    assert cfg.max_trades_per_day == 5
    assert cfg.cycle_interval_min == 5
    assert cfg.max_consecutive_failures == 3
    assert cfg.enable_bar_service is True        # BarService ON by default (D17)


def test_no_bar_service_flag_threads_through() -> None:
    assert config_from_args(parse_args([])).enable_bar_service is True
    assert config_from_args(parse_args(["--no-bar-service"])).enable_bar_service is False


def test_no_paper_debate_flag_threads_through() -> None:
    """Phase 16 D1: arm default ON, --no-paper-debate disables (Plan §6 D1)."""
    assert config_from_args(parse_args([])).enable_paper_debate is True
    assert (
        config_from_args(parse_args(["--no-paper-debate"])).enable_paper_debate is False
    )


def test_no_shadow_schedule_flag_threads_through() -> None:
    """Phase 16 D1: arm default ON, --no-shadow-schedule disables."""
    assert config_from_args(parse_args([])).enable_shadow_schedule is True
    assert (
        config_from_args(parse_args(["--no-shadow-schedule"])).enable_shadow_schedule
        is False
    )


def test_no_divergence_sampler_flag_threads_through() -> None:
    """Phase 16 D1: arm default ON, --no-divergence-sampler disables."""
    assert config_from_args(parse_args([])).enable_divergence_sampler is True
    assert (
        config_from_args(parse_args(["--no-divergence-sampler"])).enable_divergence_sampler
        is False
    )


def test_no_bar_stream_flag_threads_through() -> None:
    """Phase 16 D1: arm default ON, --no-bar-stream disables (Plan §6 D1)."""
    assert config_from_args(parse_args([])).enable_bar_stream is True
    assert (
        config_from_args(parse_args(["--no-bar-stream"])).enable_bar_stream
        is False
    )


def test_default_profile_is_fully_armed() -> None:
    """Phase 16 D1 / AK5: ``SchedulerConfig()`` and ``config_from_args(parse_args([]))``
    both default all four arms to True (Plan §1 P4 + §6 D1). Operator flips
    individual arms via ``--no-*``. ``--help`` no longer lists any ``--enable-*``.
    """
    cfg_default = SchedulerConfig()
    cfg_from_args = config_from_args(parse_args([]))
    for arm in (
        "enable_paper_debate",
        "enable_shadow_schedule",
        "enable_divergence_sampler",
        "enable_bar_stream",
    ):
        assert getattr(cfg_default, arm) is True, f"{arm} default is False"
        assert getattr(cfg_from_args, arm) is True, f"{arm} from CLI default is False"
    # Already-ON arms stay ON.
    assert cfg_default.enable_paper_trades is True
    assert cfg_default.enable_measurement_heartbeat is True
    assert cfg_default.enable_bar_service is True
    # ``--help`` output must not contain any ``--enable-*`` arm flag.
    parser = build_arg_parser()
    for stale in ("--enable-paper-debate", "--enable-shadow-schedule",
                  "--enable-divergence-sampler", "--enable-bar-stream"):
        assert not any(stale in action.option_strings for action in parser._actions), (
            f"argparser still lists stale {stale}"
        )


def test_no_measurement_heartbeat_flag_threads_through() -> None:
    assert config_from_args(parse_args([])).enable_measurement_heartbeat is True
    assert (
        config_from_args(parse_args(["--no-measurement-heartbeat"])).enable_measurement_heartbeat
        is False
    )


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
