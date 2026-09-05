"""Tests for ``phase15_v4/instinct/validator.py`` (Plan §6 C2 + §1 P11 / AK8).

Pins the deterministic validation contract — same input → same output — and
the AK8 invariant: ``validator.py`` does **not** import any LLM-related module.
The grep-style guard test is the regression that would have caught an accidental
LLM-call introduction.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path
from typing import Any

import pytest

_REPO_ROOT = "/home/trading-bot/trading-bot"
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from instinct.models import Instinct  # noqa: E402
from instinct.validator import (  # noqa: E402
    MIN_EVIDENCE,
    InstinctValidation,
    InstinctValidator,
)


# ---------------------------------------------------------------------------
# AK8: the validator module does NOT import anything LLM-shaped.
# ---------------------------------------------------------------------------


_LLM_MODULE_FRAGMENTS = (
    "llm_client",
    "brain",
    "ask_candidate",
    "research.LLMClient",
    "openai",
    "anthropic",
)


def test_validator_has_no_llm_import() -> None:
    """AK8 (Plan §7): the validator module must not import LLM-shaped modules.

    Inspects both the source file and the live module namespace. The
    ``inspect`` check guards against ``from research import llm_client``
    or any other indirect path; the source-text check guards against
    `import` statements that resolve at runtime to a private symbol.
    """
    import instinct.validator as validator_mod

    # 1) Module namespace — none of the loaded attributes point at an LLM-shaped symbol.
    for attr_name in dir(validator_mod):
        if attr_name.startswith("_"):
            continue
        attr = getattr(validator_mod, attr_name)
        mod = getattr(attr, "__module__", "") or ""
        for fragment in _LLM_MODULE_FRAGMENTS:
            assert fragment not in mod, (
                f"validator.{attr_name} comes from {mod!r} — looks LLM-shaped "
                f"(fragment {fragment!r})"
            )

    # 2) Source-text check — no import line targets an LLM module.
    src_path = Path(validator_mod.__file__)
    source = src_path.read_text(encoding="utf-8")
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            for fragment in _LLM_MODULE_FRAGMENTS:
                assert fragment not in stripped, (
                    f"validator.py imports an LLM-shaped module: {stripped!r}"
                )


def test_validator_module_only_imports_stdlib_and_models() -> None:
    """Defence-in-depth: the validator's import surface is stdlib + the
    package's own models module — nothing else."""
    import ast

    import instinct.validator as validator_mod
    tree = ast.parse(
        Path(validator_mod.__file__).read_text(encoding="utf-8")
    )
    allowed_top_level = {"dataclasses", "typing", "logging"}
    for node in ast.walk(tree):
        # ``from __future__ import ...`` is a special statement, not a real
        # module import — skip it.
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            continue
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                assert root in allowed_top_level or root == "instinct", (
                    f"validator.py imports {alias.name!r} — "
                    f"only stdlib + instinct.* allowed"
                )
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = (node.module or "").split(".")[0]
            assert root in allowed_top_level or root == "instinct", (
                f"validator.py imports from {node.module!r} — "
                f"only stdlib + instinct.* allowed"
            )


# ---------------------------------------------------------------------------
# Decision rule — evidence / contradiction counting.
# ---------------------------------------------------------------------------


def _trades(*ids: int) -> list[dict[str, Any]]:
    """Build a list of minimal trade rows with just ``id`` set."""
    return [{"id": i} for i in ids]


def test_validator_validates_when_evidence_beats_contradictions() -> None:
    """``evidence > contradictions`` **and** ``evidence >= MIN_EVIDENCE`` ⇒ ``validated``."""
    instinct = Instinct(
        trigger="Tight-spread entries win",
        domain="entry",
        evidence_trade_ids=(1, 2, 3),
        contradictions_trade_ids=(4,),
    )
    val = InstinctValidator().validate(instinct, _trades(1, 2, 3, 4))
    assert val.decision == "validated"
    assert val.evidence_count == 3
    assert val.contradiction_count == 1


def test_validator_refutes_when_contradictions_ge_evidence() -> None:
    """``contradictions >= evidence`` (and contradictions > 0) ⇒ ``refuted``."""
    instinct = Instinct(
        trigger="Mondays are bad",
        domain="timing",
        evidence_trade_ids=(1,),
        contradictions_trade_ids=(2, 3, 4),
    )
    val = InstinctValidator().validate(instinct, _trades(1, 2, 3, 4))
    assert val.decision == "refuted"
    assert val.contradiction_count == 3


def test_validator_refutes_when_contradictions_equal_evidence() -> None:
    """Tie (evidence == contradictions > 0) ⇒ ``refuted`` — no signal either way."""
    instinct = Instinct(
        trigger="Tie scenario",
        domain="entry",
        evidence_trade_ids=(1, 2),
        contradictions_trade_ids=(3, 4),
    )
    val = InstinctValidator().validate(instinct, _trades(1, 2, 3, 4))
    assert val.decision == "refuted"


def test_validator_stays_proposed_below_min_evidence() -> None:
    """``evidence < MIN_EVIDENCE`` (default 3) ⇒ ``proposed`` (insufficient signal)."""
    instinct = Instinct(
        trigger="Too few supporting trades",
        domain="entry",
        evidence_trade_ids=(1, 2),  # only 2 < MIN_EVIDENCE=3
        contradictions_trade_ids=(),
    )
    val = InstinctValidator().validate(instinct, _trades(1, 2))
    assert val.decision == "proposed"
    assert "insufficient signal" in val.reason


def test_validator_stays_proposed_when_no_ids_resolve() -> None:
    """An instinct whose IDs don't match any real trade ⇒ ``proposed``
    (counts are zero — below the min-evidence floor)."""
    instinct = Instinct(
        trigger="Phantom IDs",
        domain="entry",
        evidence_trade_ids=(99, 100, 101),
        contradictions_trade_ids=(200,),
    )
    val = InstinctValidator().validate(instinct, _trades(1, 2, 3))
    assert val.decision == "proposed"
    assert val.evidence_count == 0
    assert val.contradiction_count == 0


def test_validator_ignores_ids_not_in_trades() -> None:
    """IDs in the instinct that don't resolve to real trades are silently
    dropped — they are not phantom-counted as evidence or contradiction."""
    instinct = Instinct(
        trigger="Mostly real IDs",
        domain="entry",
        evidence_trade_ids=(1, 2, 99, 100),  # 2 real, 2 phantom
        contradictions_trade_ids=(3,),  # 1 real
    )
    val = InstinctValidator().validate(instinct, _trades(1, 2, 3))
    assert val.evidence_count == 2
    assert val.contradiction_count == 1
    # 2 evidence > 1 contradiction and 2 >= MIN_EVIDENCE=3 is False → proposed
    assert val.decision == "proposed"


def test_validator_ignores_malformed_trade_rows() -> None:
    """Trade rows without ``id`` (or with a non-int ``id``) are skipped
    defensively — never crashes the validator."""
    instinct = Instinct(
        trigger="Survives malformed trades",
        domain="entry",
        evidence_trade_ids=(1, 2, 3),
        contradictions_trade_ids=(),
    )
    messy_trades: list[dict[str, Any]] = [
        {"id": 1},
        {"id": 2},
        {"id": 3},
        {"id": "not-an-int"},  # bad
        {},  # no id
        {"other": "field"},  # no id
    ]
    val = InstinctValidator().validate(instinct, messy_trades)
    assert val.evidence_count == 3
    assert val.decision == "validated"


def test_validator_min_evidence_is_configurable() -> None:
    """``min_evidence=2`` flips the 2-evidence decision from ``proposed`` to ``validated``."""
    instinct = Instinct(
        trigger="Lowered threshold",
        domain="entry",
        evidence_trade_ids=(1, 2),
        contradictions_trade_ids=(),
    )
    # Default floor (3) → proposed
    default_val = InstinctValidator().validate(instinct, _trades(1, 2))
    assert default_val.decision == "proposed"
    # Lowered floor (2) → validated
    lowered_val = InstinctValidator(min_evidence=2).validate(instinct, _trades(1, 2))
    assert lowered_val.decision == "validated"


def test_validator_rejects_non_positive_min_evidence() -> None:
    """``min_evidence <= 0`` would make the floor trivial — rejected at construction."""
    for bad in (0, -1, -100):
        with pytest.raises(ValueError, match="min_evidence must be > 0"):
            InstinctValidator(min_evidence=bad)


# ---------------------------------------------------------------------------
# Determinism — same input, same output, every call.
# ---------------------------------------------------------------------------


def test_validator_is_deterministic() -> None:
    """Pure function: re-running on the same instinct + trades produces the
    same verdict (the property the regression tests pin)."""
    instinct = Instinct(
        trigger="Determinism",
        domain="exit",
        evidence_trade_ids=(1, 2, 3),
        contradictions_trade_ids=(4,),
    )
    trades = _trades(1, 2, 3, 4)
    v1 = InstinctValidator().validate(instinct, trades)
    v2 = InstinctValidator().validate(instinct, trades)
    v3 = InstinctValidator().validate(instinct, trades)
    assert (v1.decision, v1.evidence_count, v1.contradiction_count) == (
        v2.decision, v2.evidence_count, v2.contradiction_count,
    )
    assert (v2.decision, v2.evidence_count, v2.contradiction_count) == (
        v3.decision, v3.evidence_count, v3.contradiction_count,
    )


def test_validator_accepts_a_generator_of_trades() -> None:
    """``trades`` is typed ``Iterable`` — a generator works too (the function
    iterates exactly once into a set)."""
    instinct = Instinct(
        trigger="Generator accepted",
        domain="entry",
        evidence_trade_ids=(1, 2, 3),
        contradictions_trade_ids=(4,),
    )

    def gen():
        yield {"id": 1}
        yield {"id": 2}
        yield {"id": 3}
        yield {"id": 4}

    val = InstinctValidator().validate(instinct, gen())
    assert val.decision == "validated"


# ---------------------------------------------------------------------------
# InstinctValidation — invariant guards.
# ---------------------------------------------------------------------------


def test_instinct_validation_rejects_bad_decision() -> None:
    """``decision`` must be one of ``validated`` / ``refuted`` / ``proposed``."""
    with pytest.raises(ValueError, match="decision must be one of"):
        InstinctValidation(
            decision="yes",  # type: ignore[arg-type]
            evidence_count=0,
            contradiction_count=0,
            reason="",
        )


def test_instinct_validation_rejects_negative_counts() -> None:
    """Counts are non-negative by construction."""
    with pytest.raises(ValueError, match="counts must be non-negative"):
        InstinctValidation(
            decision="validated",
            evidence_count=-1,
            contradiction_count=0,
            reason="",
        )


def test_min_evidence_default_is_three() -> None:
    """``MIN_EVIDENCE`` module constant is 3 — the conservative starting floor."""
    assert MIN_EVIDENCE == 3
