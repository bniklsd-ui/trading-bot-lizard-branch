"""Step 9 — ``ig_bot.py``: the CLI entry's pure, testable helpers.

No network, no keyring, no wiring import: ``execution.ig_bot``'s wiring import lives
inside ``main`` (lazy), so importing the module here pulls only ``execution.*`` +
stdlib. These tests cover the exit-code mapping, the result serialisation, argparse,
and the human-confirm predicate — the parts that decide behaviour without I/O. The
``main``/``build_executor`` path is the operator's live run (``scripts/live_test.py``).
"""

from __future__ import annotations

import json

import pytest

from execution.ig_bot import (
    exit_code,
    make_confirm_fn,
    parse_args,
    result_to_dict,
)
from execution.models import ExecutionResult, OrderPlan


def _plan() -> OrderPlan:
    return OrderPlan(
        epic="IX.D.DAX.IFMM.IP",
        direction="BUY",
        size=0.5,
        stop_level=17970.0,
        limit_level=18045.0,
        deal_reference="bot-deadbeef",
        currency="EUR",
    )


# --- exit_code ------------------------------------------------------------


@pytest.mark.parametrize(
    "status, expected",
    [
        ("ABORT", 1),
        ("NO_TRADE", 0),
        ("ABORTED_BY_USER", 0),
        ("OPEN", 0),
        ("CLOSED_BY_BROKER", 0),
        ("TIME_STOP", 0),
    ],
)
def test_exit_code_only_abort_is_nonzero(status: str, expected: int) -> None:
    result = ExecutionResult(status=status, deal_id=None, plan=None, detail="x")
    assert exit_code(result) == expected


# --- result_to_dict -------------------------------------------------------


def test_result_to_dict_with_plan_is_json_serialisable() -> None:
    result = ExecutionResult(
        status="CLOSED_BY_BROKER", deal_id="DIAAAA", plan=_plan(), detail="done"
    )
    payload = result_to_dict(result)

    assert payload["status"] == "CLOSED_BY_BROKER"
    assert payload["deal_id"] == "DIAAAA"
    assert payload["plan"]["direction"] == "BUY"
    assert payload["plan"]["deal_reference"] == "bot-deadbeef"
    # The nested plan recursed into a plain dict → round-trips through json.
    assert json.loads(json.dumps(payload))["plan"]["size"] == 0.5


def test_result_to_dict_no_plan_is_none() -> None:
    result = ExecutionResult(status="NO_TRADE", deal_id=None, plan=None, detail="sizing")
    payload = result_to_dict(result)
    assert payload["plan"] is None
    assert json.loads(json.dumps(payload))["status"] == "NO_TRADE"


# --- argparse -------------------------------------------------------------


def test_parse_args_defaults() -> None:
    args = parse_args([])
    assert args.yes is False
    assert args.dry is False
    assert args.epic is None
    assert args.broker == "ig_demo"
    assert args.verbose is False


def test_parse_args_flags() -> None:
    args = parse_args(["--yes", "--dry", "--epic", "IX.D.DAX.IFMM.IP", "--verbose"])
    assert args.yes is True
    assert args.dry is True
    assert args.epic == "IX.D.DAX.IFMM.IP"
    assert args.verbose is True


# --- make_confirm_fn ------------------------------------------------------


def test_confirm_auto_yes_always_true_without_prompting() -> None:
    calls: list[str] = []
    confirm = make_confirm_fn(
        auto_yes=True, dry=False, input_fn=lambda p: calls.append(p) or "n"
    )
    assert confirm(_plan()) is True
    assert calls == []  # --yes never prompts


def test_confirm_dry_returns_false_without_prompting() -> None:
    calls: list[str] = []
    confirm = make_confirm_fn(
        auto_yes=False, dry=True, input_fn=lambda p: calls.append(p) or "y"
    )
    assert confirm(_plan()) is False  # dry never places, even if a 'y' were typed
    assert calls == []


@pytest.mark.parametrize(
    "answer, expected",
    [("y", True), ("Y", True), ("yes", True), ("n", False), ("", False), ("nope", False)],
)
def test_confirm_interactive_stdin(answer: str, expected: bool) -> None:
    confirm = make_confirm_fn(auto_yes=False, dry=False, input_fn=lambda _p: answer)
    assert confirm(_plan()) is expected
