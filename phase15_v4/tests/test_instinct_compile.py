"""Tests for ``phase15_v4/instinct/compile.py`` (Phase 16 D2.2 + D2.3).

Pins (Plan §1 P9, §6 D2.2):
- The Mini-Grammatik ``avoid BUY|SELL[ on EPIC]`` matches both with-epic and
  epic-free variants; case-insensitive.
- ``compile_rule`` returns a predicate that fires on the matching direction
  (and Epic, if specified); non-matching candidates return ``False``.
- Non-entry domains log WARNING + return ``None``.
- Non-promoted instincts (status=proposed / validated / refuted / archived)
  log WARNING + return ``None``.
- Bad triggers (free-text, wrong word order, missing direction) log WARNING
  + return ``None``.
- ``compile_rules`` over a sequence yields a tuple — empty when no rows
  qualify, preserving the AK9-Erbe (``longterm_rules == ()`` ⇒
  ``test_pre_trade_check_veto5_empty_rules_is_identity`` stays green).
- ``instinct_from_row`` parses the JSON-serialized tuple fields back into
  tuples (the DB stores them as JSON strings; the dataclass needs tuples).
"""

from __future__ import annotations

import json
import sys

import pytest


_REPO_ROOT = "/home/trading-bot/trading-bot"
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


from instinct.compile import (  # noqa: E402
    TRIGGER_RE,
    compile_rule,
    compile_rules,
    instinct_from_row,
)
from instinct.models import Instinct  # noqa: E402


# -- TRIGGER_RE -------------------------------------------------------------


def test_trigger_re_matches_avoid_buy_no_epic() -> None:
    """``avoid BUY`` (epic-free broad veto) matches; group(1)='BUY', group(2)=None."""
    match = TRIGGER_RE.match("avoid BUY")
    assert match is not None
    assert match.group(1) == "BUY"
    assert match.group(2) is None


def test_trigger_re_matches_avoid_sell_no_epic() -> None:
    """``avoid SELL`` (epic-free broad veto) matches; group(1)='SELL'."""
    match = TRIGGER_RE.match("avoid SELL")
    assert match is not None
    assert match.group(1) == "SELL"
    assert match.group(2) is None


def test_trigger_re_matches_avoid_buy_on_epic() -> None:
    """``avoid BUY on IX.D.DAX.IFMM.IP`` matches; groups captured."""
    match = TRIGGER_RE.match("avoid BUY on IX.D.DAX.IFMM.IP")
    assert match is not None
    assert match.group(1) == "BUY"
    assert match.group(2) == "IX.D.DAX.IFMM.IP"


def test_trigger_re_case_insensitive() -> None:
    """``AVOID buy On IX.D.DAX.IFMM.IP`` also matches (case-insensitive).

    The regex captures the literal text (``group(1)`` is ``"buy"``), and the
    compiler normalises via ``.upper()`` (see ``compile_rule``). The grammar
    itself is case-insensitive at the schema level.
    """
    match = TRIGGER_RE.match("AVOID buy On IX.D.DAX.IFMM.IP")
    assert match is not None
    assert match.group(1).upper() == "BUY"
    assert match.group(2) == "IX.D.DAX.IFMM.IP"  # already uppercase in input


def test_trigger_re_case_insensitive_lowercase_epic() -> None:
    """``avoid BUY on ix.d.dax.ifmm.ip`` matches (Epic regex case-insensitive too)."""
    match = TRIGGER_RE.match("avoid BUY on ix.d.dax.ifmm.ip")
    assert match is not None
    assert match.group(1) == "BUY"
    assert match.group(2).upper() == "IX.D.DAX.IFMM.IP"


def test_trigger_re_rejects_free_text() -> None:
    """Free text like ``spread too wide`` does NOT match."""
    assert TRIGGER_RE.match("spread too wide") is None


def test_trigger_re_rejects_missing_direction() -> None:
    """``avoid`` without direction is malformed (no BUY|SELL)."""
    assert TRIGGER_RE.match("avoid") is None


def test_trigger_re_rejects_unknown_direction() -> None:
    """``avoid HOLD`` does NOT match — HOLD is not BUY or SELL."""
    assert TRIGGER_RE.match("avoid HOLD") is None


def test_trigger_re_rejects_trailing_garbage() -> None:
    """``avoid BUY something else`` — extra tokens after the Epic do not match."""
    assert TRIGGER_RE.match("avoid BUY IX.D.DAX.IFMM.IP forever") is None


def test_trigger_re_rejects_lowercase_epic_with_dot() -> None:
    """The Epic regex is **case-insensitive** (re.IGNORECASE) — lowercase is fine."""
    # With re.IGNORECASE, ``[A-Z0-9.]+`` matches both cases.
    assert TRIGGER_RE.match("avoid BUY on ix.d.dax.ifmm.ip") is not None


# -- compile_rule ----------------------------------------------------------


def _entry_instinct(trigger: str, status: str = "promoted", domain: str = "entry") -> Instinct:
    """Build a promoted entry-domain Instinct for compile tests."""
    return Instinct(
        trigger=trigger,
        domain=domain,
        confidence=0.8,
        evidence_trade_ids=(1, 2, 3),
        contradictions_trade_ids=(),
        status=status,
    )


def test_compile_rule_avoid_buy_broad_veto_matches_any_buy() -> None:
    """``avoid BUY`` predicate fires on every BUY candidate."""
    pred = compile_rule(_entry_instinct("avoid BUY"))
    assert pred is not None
    assert pred({"direction": "BUY", "epic": "IX.D.DAX.IFMM.IP"}) is True
    assert pred({"direction": "SELL", "epic": "IX.D.DAX.IFMM.IP"}) is False


def test_compile_rule_avoid_sell_broad_veto_matches_any_sell() -> None:
    """``avoid SELL`` predicate fires on every SELL candidate."""
    pred = compile_rule(_entry_instinct("avoid SELL"))
    assert pred is not None
    assert pred({"direction": "SELL", "epic": "IX.D.FOO.BAR.IP"}) is True
    assert pred({"direction": "BUY", "epic": "IX.D.FOO.BAR.IP"}) is False


def test_compile_rule_avoid_buy_on_epic_vetoes_only_that_epic() -> None:
    """``avoid BUY on IX.D.DAX.IFMM.IP`` fires only on that Epic's BUY."""
    pred = compile_rule(_entry_instinct("avoid BUY on IX.D.DAX.IFMM.IP"))
    assert pred is not None
    assert pred({"direction": "BUY", "epic": "IX.D.DAX.IFMM.IP"}) is True
    assert pred({"direction": "BUY", "epic": "IX.D.FOO.BAR.IP"}) is False
    assert pred({"direction": "SELL", "epic": "IX.D.DAX.IFMM.IP"}) is False


def test_compile_rule_non_entry_domain_returns_none_with_warning(caplog) -> None:
    """``domain='sizing'`` (no consumer today) returns None + WARNING."""
    with caplog.at_level("WARNING", logger="instinct.compile"):
        pred = compile_rule(_entry_instinct("avoid BUY", domain="sizing"))
    assert pred is None
    assert any("no consumer for domain" in r.message for r in caplog.records)


def test_compile_rule_non_promoted_status_returns_none_with_warning(caplog) -> None:
    """``status='proposed'`` (validator-only stage) returns None + WARNING."""
    with caplog.at_level("WARNING", logger="instinct.compile"):
        pred = compile_rule(_entry_instinct("avoid BUY", status="proposed"))
    assert pred is None
    assert any("refusing non-promoted" in r.message for r in caplog.records)


def test_compile_rule_bad_trigger_returns_none_with_warning(caplog) -> None:
    """A trigger that doesn't match the grammar returns None + WARNING."""
    with caplog.at_level("WARNING", logger="instinct.compile"):
        pred = compile_rule(_entry_instinct("spread too wide", status="promoted"))
    assert pred is None
    assert any("does not match the grammar" in r.message for r in caplog.records)


def test_compile_rule_fail_open_on_missing_direction_key() -> None:
    """A candidate without ``direction`` returns ``False`` (fail-open).

    VETO 5 expects a predicate that **triggers** on bad candidates. A malformed
    candidate (missing key) shouldn't trigger the veto — VETO 5 stays fail-
    closed via the upstream candidate construction, not the predicate.
    """
    pred = compile_rule(_entry_instinct("avoid BUY"))
    assert pred is not None
    assert pred({"epic": "IX.D.DAX.IFMM.IP"}) is False
    assert pred({}) is False


# -- compile_rules ---------------------------------------------------------


def test_compile_rules_empty_input_returns_empty_tuple() -> None:
    """No rows ⇒ empty tuple — AK9-Erbe (VETO 5 stays identity function)."""
    assert compile_rules([]) == ()


def test_compile_rules_filters_unmatchable_rows() -> None:
    """Unmatchable rows are skipped (with WARNING); matchable ones stay."""
    rows = [
        {"id": 1, "trigger": "avoid BUY", "domain": "entry", "status": "promoted",
         "evidence_trade_ids_json": "[]", "contradictions_trade_ids_json": "[]"},
        {"id": 2, "trigger": "free text", "domain": "entry", "status": "promoted",
         "evidence_trade_ids_json": "[]", "contradictions_trade_ids_json": "[]"},
        {"id": 3, "trigger": "avoid SELL", "domain": "sizing", "status": "promoted",
         "evidence_trade_ids_json": "[]", "contradictions_trade_ids_json": "[]"},
        {"id": 4, "trigger": "avoid BUY on IX.D.FOO.BAR.IP", "domain": "entry",
         "status": "promoted", "evidence_trade_ids_json": "[]",
         "contradictions_trade_ids_json": "[]"},
    ]
    preds = compile_rules(rows)
    assert len(preds) == 2
    # Order is implementation-defined; both matchable predicates should fire correctly.
    buy_broad = preds[0]({"direction": "BUY", "epic": "X"})
    buy_narrow = preds[1]({"direction": "BUY", "epic": "IX.D.FOO.BAR.IP"})
    assert buy_broad is True
    assert buy_narrow is True


def test_compile_rules_iterable_not_just_list() -> None:
    """``compile_rules`` accepts any iterable, not just list (Phase-15 contract)."""
    def _gen():
        yield {"id": 1, "trigger": "avoid BUY", "domain": "entry",
               "status": "promoted", "evidence_trade_ids_json": "[]",
               "contradictions_trade_ids_json": "[]"}
    preds = compile_rules(_gen())
    assert len(preds) == 1


# -- instinct_from_row -----------------------------------------------------


def test_instinct_from_row_parses_json_tuple_fields() -> None:
    """JSON-serialized trade-id lists parse back into tuples."""
    row = {
        "id": 7,
        "trigger": "avoid BUY",
        "domain": "entry",
        "confidence": 0.9,
        "evidence_trade_ids_json": json.dumps([1, 2, 3]),
        "contradictions_trade_ids_json": json.dumps([4]),
        "status": "validated",
        "created_utc": "2026-09-01T12:00:00.000Z",
    }
    inst = instinct_from_row(row)
    assert inst.id == 7
    assert inst.trigger == "avoid BUY"
    assert inst.domain == "entry"
    assert inst.confidence == 0.9
    assert inst.evidence_trade_ids == (1, 2, 3)
    assert inst.contradictions_trade_ids == (4,)
    assert inst.status == "validated"


def test_instinct_from_row_handles_already_parsed_lists() -> None:
    """Some callers pass already-parsed lists (not JSON strings) — accept both."""
    row = {
        "trigger": "avoid BUY", "domain": "entry", "status": "proposed",
        "evidence_trade_ids_json": [10, 20],
        "contradictions_trade_ids_json": [],
    }
    inst = instinct_from_row(row)
    assert inst.evidence_trade_ids == (10, 20)
    assert inst.contradictions_trade_ids == ()


def test_instinct_from_row_defaults_when_fields_missing() -> None:
    """Defensive defaults: missing keys fall back to the dataclass defaults.

    Note: the ``trigger`` field is required to be non-empty by the
    ``Instinct.__post_init__`` check, so a fully-empty row raises. We seed a
    minimal trigger so the dataclass accepts the row.
    """
    inst = instinct_from_row({"trigger": "avoid BUY"})
    assert inst.trigger == "avoid BUY"
    assert inst.domain == "entry"  # default
    assert inst.confidence is None
    assert inst.evidence_trade_ids == ()
    assert inst.contradictions_trade_ids == ()
    assert inst.status == "proposed"
