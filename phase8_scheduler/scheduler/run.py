"""Entry point for the autonomous scheduler daemon — ``python -m scheduler.run``.

The thin operator front-end: parse the consciously-set caps (daily-loss cap, token budget, trade
cap, cycle cadence) into a :class:`~scheduler.config.SchedulerConfig`, build the fully wired
:class:`~scheduler.runner.SchedulerRunner` via the (lazily imported) composition root, install
graceful SIGTERM/SIGINT handlers, and run the loop until it stops (kill-switch, backoff trip, a
signal, or — never in production — ``max_iterations``).

This module lives **inside** the ``scheduler`` package (not ``scripts/``) so the documented
``python -m scheduler.run`` entry resolves — the ``scripts/`` dir is excluded from the installed
package (``pyproject`` ``include=["scheduler*"]``). Exactly the Phase-5 ``execution/ig_bot.py``
pattern: the cross-phase ``scripts.wiring`` import is **lazy inside** :func:`main` (with a one-line
``sys.path`` insert of the project dir), so module-level imports stay stdlib + ``scheduler.*`` and
``python -m scheduler.run --help`` / the unit tests touch neither the keyring nor the network.

Graceful stop: the signal handler calls ``runner.request_stop()`` (a non-sticky in-memory flag) —
**not** the kill-switch file, so a SIGTERM does not persist a halt that would block the next restart.
The loop stops at the next iteration boundary and runs ``shutdown()`` (final reconcile + disconnect).

Logging goes to **stderr** (repo convention; stdout carries no machine output here). Repo
conventions apply (``from __future__ import annotations``, type hints + docstrings).
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
from pathlib import Path

from scheduler.config import SchedulerConfig

logger = logging.getLogger("scheduler.run")


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the daemon's consciously-set caps (concept §1 / Decisions 6/9/10/12)."""
    parser = argparse.ArgumentParser(
        prog="python -m scheduler.run",
        description=(
            "Run the autonomous DAX demo-trading scheduler daemon (demo-only, fail-closed). "
            "Caps are v1 values, tuned at real output."
        ),
    )
    parser.add_argument(
        "--daily-loss-cap",
        type=float,
        default=1800.0,
        help="daily realized-loss circuit breaker in account currency "
        "(operator-confirmed v1 ~1800 on the ~30K demo; pass a negative/0 to keep it but small). "
        "Use --no-loss-cap to disable (NOT recommended).",
    )
    parser.add_argument(
        "--no-loss-cap",
        action="store_true",
        help="disable the daily-loss breaker (sets daily_loss_cap=None — a loud WARNING). Discouraged.",
    )
    parser.add_argument(
        "--daily-token-budget",
        type=int,
        default=200_000,
        help="daily LLM token budget over the shared meter (default 200000 ≈ €0.8/day runaway breaker). "
        "Use --no-token-budget to disable (NOT recommended).",
    )
    parser.add_argument(
        "--no-token-budget",
        action="store_true",
        help="disable the token budget (sets daily_token_budget=None — a loud WARNING). Discouraged.",
    )
    parser.add_argument(
        "--max-trades",
        type=int,
        default=5,
        help="max real trades opened per Europe/Berlin day (default 5, operator-confirmed v1).",
    )
    parser.add_argument(
        "--cycle-interval-min",
        type=int,
        default=5,
        help="minutes between trade cycles inside the trading window (default 5).",
    )
    parser.add_argument(
        "--max-consecutive-failures",
        type=int,
        default=3,
        help="consecutive cycle exceptions before the backoff trips the kill-switch (default 3).",
    )
    parser.add_argument("--verbose", action="store_true", help="DEBUG logging to stderr.")
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse ``argv`` (or ``sys.argv``) into a namespace."""
    return build_arg_parser().parse_args(argv)


def config_from_args(args: argparse.Namespace) -> SchedulerConfig:
    """Build the demo-locked :class:`SchedulerConfig` from parsed CLI args.

    ``account`` is hard-set to ``"demo"`` here (the wiring re-checks it and refuses anything else —
    the structural demo-lock). ``--no-loss-cap`` sets ``daily_loss_cap=None`` and ``--no-token-budget``
    sets ``daily_token_budget=None`` (each a loud WARNING). Path fields keep their defaults; the wiring
    rewrites them to the absolute data tree.
    """
    return SchedulerConfig(
        account="demo",
        daily_loss_cap=None if args.no_loss_cap else args.daily_loss_cap,
        daily_token_budget=None if args.no_token_budget else args.daily_token_budget,
        max_trades_per_day=args.max_trades,
        cycle_interval_min=args.cycle_interval_min,
        max_consecutive_failures=args.max_consecutive_failures,
    )


def _install_signal_handlers(runner: object) -> None:
    """Wire SIGTERM/SIGINT to a graceful, non-sticky stop (``runner.request_stop()``)."""

    def _handle(signum: int, _frame: object) -> None:
        logger.warning("received signal %s — requesting graceful stop.", signum)
        runner.request_stop()  # type: ignore[attr-defined]

    signal.signal(signal.SIGTERM, _handle)
    signal.signal(signal.SIGINT, _handle)


def main(argv: list[str] | None = None) -> int:
    """Build the wired scheduler and run it. Returns a process exit code (0 = clean stop).

    Parses args, constructs the demo-locked config, then lazily imports the composition root (so
    ``--help`` and the unit tests stay offline) and runs. A ``PreflightError`` from the runner is a
    clean, expected fail-closed exit (e.g. the keyring is unreachable) → logged, exit code 2.
    """
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    config = config_from_args(args)

    # Lazy cross-phase import (keeps module load + --help + tests offline). Mirrors ig_bot.py.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scheduler.exceptions import PreflightError
    from scripts.wiring import build_scheduler  # noqa: E402

    runner = build_scheduler(config)
    _install_signal_handlers(runner)

    logger.info(
        "starting scheduler daemon (account=%s, max_trades=%d, daily_loss_cap=%s, cycle=%dmin).",
        config.account,
        config.max_trades_per_day,
        config.daily_loss_cap,
        config.cycle_interval_min,
    )
    try:
        runner.run()
    except PreflightError as exc:
        logger.critical("preflight failed — not trading: %s", exc)
        return 2
    logger.info("scheduler daemon stopped cleanly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
