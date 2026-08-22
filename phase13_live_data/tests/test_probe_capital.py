"""Phase 13 / Phase 14 — tests for ``scripts/probe_capital._pick_index_match``.

Pure-function tests, no network, no keyring, no ``main()``. The helper
lives at module scope (not inside ``main()``) so it can be unit-tested
without mocking ``argparse`` / keyring / ``requests``.

History: the previous in-script filter
``"CFD" in (m.get("instrumentType") or "").upper()`` was a no-op against
the real REST response (Capital.com's index CFDs carry
``instrumentType == "INDICES"``, captured in the B1a probe snapshot
2026-08-22). The fallback path carried the day. This file pins the
fixed exact-equality match — and the name-only fallback that protects
us against a future type rename — so we can never silently lose the
match again.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "phase13_live_data" / "scripts"))

from probe_capital import _pick_index_match  # noqa: E402


# ---------- fixtures --------------------------------------------------------


def _market(
    *,
    name: str,
    type_: str,
    epic: str = "EPIC",
) -> dict:
    """One minimal market-shape — only the fields the helper reads."""
    return {
        "instrumentName": name,
        "instrumentType": type_,
        "epic": epic,
    }


# ---------- happy path: INDICES wins ---------------------------------------


def test_pick_index_match_picks_indices_over_other_types():
    """When an INDICES entry exists for ``index_name``, it wins — even if
    a SHARES/COMMODITIES sibling also carries the exact name (B1a probe
    shows search returns a heterogeneous first page)."""
    markets = [
        _market(name="Gold", type_="COMMODITIES", epic="GOLD"),
        _market(name="Germany 40", type_="SHARES", epic="DUMMY_SHARES"),
        _market(name="Germany 40", type_="INDICES", epic="DE40"),
    ]
    match = _pick_index_match(markets, "Germany 40")
    assert match is not None
    assert match["epic"] == "DE40"
    assert match["instrumentType"] == "INDICES"


def test_pick_index_match_uppercases_type_for_comparison():
    """Real-world ``instrumentType`` is mixed-case; the comparison must
    normalise to upper so ``Indices`` / ``indices`` / ``INDICES`` all hit."""
    markets = [
        _market(name="France 40", type_="Indices", epic="FR40"),
    ]
    match = _pick_index_match(markets, "France 40")
    assert match is not None
    assert match["epic"] == "FR40"


# ---------- fallback: no INDICES entry, but exact name exists --------------


def test_pick_index_match_falls_back_to_any_exact_name_match():
    """If only SHARES / COMMODITIES carries the exact name, we still
    surface it. The probe must not lose the index just because Capital.com
    renames its type column — that's a forward-compatible signal of
    'something with that name exists, look at it'."""
    markets = [
        _market(name="Gold", type_="COMMODITIES", epic="GOLD"),
        _market(name="Spain 35", type_="SHARES", epic="SP35-SHARES"),
    ]
    match = _pick_index_match(markets, "Spain 35")
    assert match is not None
    assert match["epic"] == "SP35-SHARES"


# ---------- no match at all -------------------------------------------------


def test_pick_index_match_returns_none_when_no_exact_name():
    """No entry whose ``instrumentName`` equals ``index_name`` ⇒ ``None``.
    The script emits ``error='no_exact_name_match'`` in that case."""
    markets = [
        _market(name="Gold", type_="COMMODITIES", epic="GOLD"),
        _market(name="US Wall Street 30", type_="INDICES", epic="US30"),
    ]
    assert _pick_index_match(markets, "Spain 35") is None


# ---------- robustness ------------------------------------------------------


def test_pick_index_match_tolerates_missing_type_field():
    """A market with no ``instrumentType`` field (or ``None``) must not
    raise. Missing-type markets fall through to the name-only fallback."""
    markets = [
        {"instrumentName": "Germany 40", "epic": "DE40"},  # no type
        _market(name="Gold", type_="COMMODITIES", epic="GOLD"),
    ]
    match = _pick_index_match(markets, "Germany 40")
    assert match is not None
    assert match["epic"] == "DE40"


def test_pick_index_match_empty_markets_returns_none():
    """Empty market list — the helper must not crash."""
    assert _pick_index_match([], "anything") is None
