"""CLI entry / composition root for the Phase-5 execution cycle (concept §9).

``ig_bot.py`` is the operator-facing front door: it parses flags, builds the real
:class:`~execution.executor.Executor` via :func:`scripts.wiring.build_executor`,
runs one cycle, prints the machine-readable result to **stdout** and a human summary
to **stderr**, and maps the outcome to an exit code (non-zero **only** on a
fail-closed ``ABORT``).

Run it as ``python -m execution.ig_bot`` or ``python phase5_execution/execution/
ig_bot.py``. The wiring import is **lazy inside** :func:`main` (with a one-line
``sys.path`` insert of the project dir so the non-installed ``scripts`` package
resolves), so ``--help`` and the unit tests touch neither the keyring nor the
network. The ``execution`` runtime package itself stays ``sys.path``-free (editable
installs); this entry script is the single, deliberate exception — the Phase-4
precedent.

Output discipline (project rule): logs + the human summary → **stderr**; the result
JSON → **stdout** (so a caller can pipe it). Demo only, manual trigger; no scheduler
(that is Phase 8).

The pure helpers (:func:`exit_code`, :func:`result_to_dict`, :func:`parse_args`,
:func:`make_confirm_fn`) carry no I/O and are unit-tested directly in
``tests/test_ig_bot.py`` — ``main`` itself is exercised by the operator's live run.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import sys
from pathlib import Path
from typing import Any, Callable

from execution.config import ExecutionConfig
from execution.models import ExecutionResult, OrderPlan

logger = logging.getLogger("phase5.ig_bot")

# Statuses that mean "the cycle ended cleanly" — exit 0. Only a fail-closed ABORT
# (session health, reconcile conflict, unresolved PENDING, failed time-stop close)
# is a non-zero exit; a no-trade / a declined confirm are *not* failures.
_ABORT_STATUS = "ABORT"


def exit_code(result: ExecutionResult) -> int:
    """Map a cycle result to a process exit code: ``1`` on ABORT, else ``0``.

    ``NO_TRADE`` (a gate/VETO/abstain said no) and ``ABORTED_BY_USER`` (confirm
    declined / dry run) are clean outcomes → ``0``. Only ``ABORT`` is non-zero.
    """
    return 1 if result.status == _ABORT_STATUS else 0


def result_to_dict(result: ExecutionResult) -> dict[str, Any]:
    """Serialise an :class:`ExecutionResult` (with its nested plan) to a plain dict.

    ``dataclasses.asdict`` recurses into the frozen :class:`OrderPlan`, so the output
    is directly JSON-serialisable; ``plan`` is ``None`` when no order was built.
    """
    return dataclasses.asdict(result)


def make_confirm_fn(
    *,
    auto_yes: bool,
    dry: bool,
    input_fn: Callable[[str], str] = input,
    log: logging.Logger | None = None,
) -> Callable[[OrderPlan], bool]:
    """Build the human-confirm predicate the executor consults before placing.

    Three modes (precedence ``auto_yes`` > ``dry`` > interactive):

    - ``auto_yes`` (``--yes``): always ``True`` — for later automation / the live test.
    - ``dry`` (``--dry``): log the would-be :class:`OrderPlan` and return ``False``,
      so the full gate/sizing/VETO pipeline runs and the plan is built, but **no**
      ``open_position`` is ever invoked (the executor's confirm gate stops there).
    - interactive (default): a stdin ``y/N`` prompt via ``input_fn`` (injected so
      tests drive it); only an explicit ``y`` / ``yes`` confirms.
    """
    log = log or logger

    def _confirm(plan: OrderPlan) -> bool:
        if auto_yes:
            return True
        summary = (
            f"{plan.direction} {plan.size} {plan.epic} "
            f"stop={plan.stop_level} limit={plan.limit_level} ref={plan.deal_reference}"
        )
        if dry:
            log.info("[dry] would place: %s — no order placed (dry run)", summary)
            return False
        answer = input_fn(f"Place order: {summary} ? [y/N] ").strip().lower()
        return answer in ("y", "yes")

    return _confirm


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the ``ig_bot`` argument parser (concept §9 flags)."""
    parser = argparse.ArgumentParser(
        prog="ig_bot",
        description="Phase-5 execution cycle: gates -> VETOs -> confirm -> order -> "
        "monitor (DAX CFD, IG Demo, manual trigger).",
    )
    parser.add_argument(
        "--yes", action="store_true",
        help="skip the human-confirm prompt (auto-confirm the order). Use deliberately.",
    )
    parser.add_argument(
        "--dry", action="store_true",
        help="run all gates + VETOs and build the plan, but place no order.",
    )
    parser.add_argument(
        "--epic", default=None,
        help="optional research allow-list epic override (when research must run).",
    )
    parser.add_argument(
        "--broker", default="ig_demo",
        help="broker id to build (default: ig_demo). Phase 5 is Demo only.",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="DEBUG-level logging on stderr.",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse ``argv`` (or ``sys.argv``) into the ``ig_bot`` namespace."""
    return build_arg_parser().parse_args(argv)


def _summarize(result: ExecutionResult, *, dry: bool) -> str:
    """A one-line human summary of the outcome (for stderr)."""
    if result.status == _ABORT_STATUS:
        return f"ABORT (exit 1) — {result.detail}"
    if result.status == "NO_TRADE":
        return f"NO_TRADE — {result.detail}"
    if result.status == "ABORTED_BY_USER":
        if dry:
            return "DRY RUN — gates + VETOs passed, plan built, no order placed."
        return "ABORTED_BY_USER — confirm declined, no order placed."
    return f"{result.status} — deal_id={result.deal_id} ({result.detail})"


def main(argv: list[str] | None = None) -> int:
    """Run one execution cycle and return the process exit code.

    Builds the real executor via the (lazily imported) wiring, runs it, emits the
    result JSON to stdout + a summary to stderr, and returns :func:`exit_code`.
    """
    args = parse_args(argv)
    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    config = ExecutionConfig()
    confirm_fn = make_confirm_fn(auto_yes=args.yes, dry=args.dry)

    # Lazy: keep the keyring + sibling packages out of --help and the unit tests.
    # The project dir holds the (non-installed) `scripts` package with the wiring.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scripts.wiring import build_executor  # noqa: E402

    logger.info(
        "building executor (broker=%s, dry=%s, auto_yes=%s)", args.broker, args.dry, args.yes
    )
    executor = build_executor(
        config, confirm_fn=confirm_fn, broker_name=args.broker, epic_override=args.epic
    )

    result = executor.run()

    # stdout = the machine-readable result; stderr = the human summary.
    print(json.dumps(result_to_dict(result), indent=2))
    logger.info("%s", _summarize(result, dry=args.dry))
    return exit_code(result)


if __name__ == "__main__":
    raise SystemExit(main())
