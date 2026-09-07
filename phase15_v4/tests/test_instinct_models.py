"""Tests for ``phase15_v4/instinct/models.py`` (Plan §6 C2, AK7/AK8).

Pins the immutable invariants of :class:`Instinct` and :class:`InstinctConfig` —
the contract :class:`Database.insert_instinct` (Phase 2, Migration 009) honors.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = "/home/trading-bot/trading-bot"
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from instinct.models import (  # noqa: E402
    DOMAINS,
    INSTINCT_STATUSES,
    Instinct,
    InstinctConfig,
    is_valid_domain,
    is_valid_status,
)


# ---------------------------------------------------------------------------
# Module-level constants — pinned to the SQL CHECK constraints in Migration 009.
# ---------------------------------------------------------------------------


def test_domains_constant_pinned_to_sql_check() -> None:
    """``DOMAINS`` must match the ``CHECK(domain IN (...))`` from Migration 009."""
    assert DOMAINS == ("entry", "exit", "sizing", "timing")


def test_instinct_statuses_constant_pinned_to_sql_check() -> None:
    """``INSTINCT_STATUSES`` must match the ``CHECK(status IN (...))`` from Migration 009."""
    assert INSTINCT_STATUSES == (
        "proposed", "validated", "refuted", "promoted", "archived",
    )


def test_is_valid_domain_accepts_only_the_four() -> None:
    """``is_valid_domain`` returns True only for the four pinned values."""
    for d in DOMAINS:
        assert is_valid_domain(d) is True
    for bad in ("", "ENTRY", "Entry", "trade", None, 1, []):
        assert is_valid_domain(bad) is False


def test_is_valid_status_accepts_only_the_five() -> None:
    """``is_valid_status`` returns True only for the five lifecycle values."""
    for s in INSTINCT_STATUSES:
        assert is_valid_status(s) is True
    for bad in ("", "PROPOSED", "Proposed", "deleted", None, 0, {}):
        assert is_valid_status(bad) is False


# ---------------------------------------------------------------------------
# Instinct — defaults.
# ---------------------------------------------------------------------------


def test_instinct_defaults_match_schema() -> None:
    """Defaults: ``status='proposed'``, empty tuples, ``confidence=None``, ``id=None``."""
    inst = Instinct(trigger="Avoid entries when spread > 0.015 %", domain="entry")
    assert inst.status == "proposed"
    assert inst.confidence is None
    assert inst.evidence_trade_ids == ()
    assert inst.contradictions_trade_ids == ()
    assert inst.created_utc == ""
    assert inst.validated_utc is None
    assert inst.promoted_utc is None
    assert inst.archived_utc is None
    assert inst.id is None


def test_instinct_accepts_all_fields() -> None:
    """Full construction with every field set — matches the DB row shape 1:1."""
    inst = Instinct(
        trigger="Tight-spread entries outperform",
        domain="entry",
        confidence=0.7,
        evidence_trade_ids=(1, 2, 3),
        contradictions_trade_ids=(4,),
        status="validated",
        created_utc="2026-09-05T08:00:00.000Z",
        validated_utc="2026-09-05T09:00:00.000Z",
        promoted_utc=None,
        archived_utc=None,
        id=42,
    )
    assert inst.id == 42
    assert inst.confidence == 0.7
    assert inst.evidence_trade_ids == (1, 2, 3)
    assert inst.contradictions_trade_ids == (4,)
    assert inst.status == "validated"
    assert inst.validated_utc == "2026-09-05T09:00:00.000Z"


# ---------------------------------------------------------------------------
# Instinct — validation paths (must raise before reaching the DB).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_domain", ["", "ENTRY", "trade", "Exit", None, 1])
def test_instinct_rejects_invalid_domain(bad_domain: object) -> None:
    """Invalid ``domain`` raises ``ValueError`` (would be caught by SQL CHECK too)."""
    with pytest.raises(ValueError, match="domain must be one of"):
        Instinct(trigger="t", domain=bad_domain)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "bad_status", ["", "PROPOSED", "deleted", None, 1]
)
def test_instinct_rejects_invalid_status(bad_status: object) -> None:
    """Invalid ``status`` raises ``ValueError`` (would be caught by SQL CHECK too)."""
    with pytest.raises(ValueError, match="status must be one of"):
        Instinct(trigger="t", domain="entry", status=bad_status)  # type: ignore[arg-type]


def test_instinct_default_status_proposed_is_accepted() -> None:
    """``status='proposed'`` (default) is valid — the validator's starting state."""
    Instinct(trigger="t", domain="entry")  # no raise


def test_instinct_rejects_empty_trigger() -> None:
    """Empty or whitespace-only trigger raises — the SQL column is NOT NULL but
    we also reject empty strings here (a useful early signal)."""
    for bad in ("", "   ", "\n\t  "):
        with pytest.raises(ValueError, match="trigger must be a non-empty string"):
            Instinct(trigger=bad, domain="entry")


@pytest.mark.parametrize("bad_conf", [-0.1, -1.0, 1.1, 2.0])
def test_instinct_rejects_confidence_outside_unit_interval(bad_conf: float) -> None:
    """Confidence must be in [0.0, 1.0] or None — anything else is rejected."""
    with pytest.raises(ValueError, match="confidence must be in"):
        Instinct(trigger="t", domain="entry", confidence=bad_conf)


@pytest.mark.parametrize("good_conf", [0.0, 0.5, 1.0, None])
def test_instinct_accepts_confidence_in_unit_interval(good_conf: object) -> None:
    """Confidence in [0.0, 1.0] (and None) is accepted."""
    Instinct(trigger="t", domain="entry", confidence=good_conf)  # type: ignore[arg-type]


def test_instinct_is_frozen() -> None:
    """Frozen dataclass discipline — assignment after construction raises."""
    inst = Instinct(trigger="t", domain="entry")
    with pytest.raises(Exception):  # FrozenInstanceError is a subclass of AttributeError
        inst.trigger = "new"  # type: ignore[misc]


def test_instinct_evidence_is_tuple_not_list() -> None:
    """``evidence_trade_ids`` and ``contradictions_trade_ids`` are tuples — frozen
    dataclass discipline (avoids the mutable-default trap)."""
    inst = Instinct(
        trigger="t", domain="entry",
        evidence_trade_ids=[1, 2],  # type: ignore[arg-type]
        contradictions_trade_ids=[3],  # type: ignore[arg-type]
    )
    assert isinstance(inst.evidence_trade_ids, tuple)
    assert isinstance(inst.contradictions_trade_ids, tuple)


# ---------------------------------------------------------------------------
# InstinctConfig — promotion gates.
# ---------------------------------------------------------------------------


def test_instinct_config_defaults() -> None:
    """Defaults: ``instinct_n_min=50``, ``enable_instinct_promotion=True``
    (Phase 16 D1: ON by default, Plan §1 P5 supersedes Phase-15-P10)."""
    cfg = InstinctConfig()
    assert cfg.instinct_n_min == 50
    assert cfg.enable_instinct_promotion is True


def test_instinct_config_rejects_non_positive_n_min() -> None:
    """``instinct_n_min <= 0`` would make the promotion gate trivial — rejected."""
    for bad in (0, -1, -50):
        with pytest.raises(ValueError, match="instinct_n_min must be > 0"):
            InstinctConfig(instinct_n_min=bad)


def test_instinct_config_is_frozen() -> None:
    """Frozen dataclass discipline — assignment raises."""
    cfg = InstinctConfig()
    with pytest.raises(Exception):
        cfg.instinct_n_min = 100  # type: ignore[misc]


def test_instinct_config_from_dict_uses_defaults_when_keys_missing() -> None:
    """``from_dict`` is defensive: missing keys fall back to the dataclass defaults.
    Phase 16 D1: default for ``enable_instinct_promotion`` is now ``True``."""
    cfg = InstinctConfig.from_dict({})
    assert cfg.instinct_n_min == 50
    assert cfg.enable_instinct_promotion is True


def test_instinct_config_from_dict_reads_provided_keys() -> None:
    """``from_dict`` honours explicit values."""
    cfg = InstinctConfig.from_dict(
        {"instinct_n_min": 25, "enable_instinct_promotion": True}
    )
    assert cfg.instinct_n_min == 25
    assert cfg.enable_instinct_promotion is True


def test_instinct_config_from_dict_coerces_types() -> None:
    """``from_dict`` coerces to ``int`` / ``bool`` defensively (config-row safety)."""
    cfg = InstinctConfig.from_dict(
        # YAML/JSON would deliver these as strings if unparsed.
        {"instinct_n_min": "30", "enable_instinct_promotion": "true"}
    )
    assert cfg.instinct_n_min == 30
    assert cfg.enable_instinct_promotion is True
