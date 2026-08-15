"""Abnahme Kriterium A (Decision D5, Plan §6 Step 3/7): ``yf_ticker`` has exactly one
writer (``UniverseStore.set_symbol``) plus the initial-insert path (``seed_curated`` /
a fresh-epic ``upsert_discovered``) — a re-discovery of an already-known epic must never
reset a resolved symbol. Repo-wide static checks; the behavioral half (the actual
conflict-preserve guarantee) lives in ``phase9_universe/tests/test_store.py::
test_upsert_discovered_preserves_registry_truth_on_conflict`` — this file only proves
"a writer" is precisely and narrowly defined."""

from __future__ import annotations

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]

# Files allowed to literally assign/construct a non-None yf_ticker value from a lookup
# table. seed_curated's UniverseRecord(...) construction reads spec.yf_ticker off an
# already-curated InstrumentSpec (Phase 4's data), not a fresh guess — sanctioned initial
# insert, same as the plan's "seed_curated" exception.
_ALLOWED_LOOKUP_FILES = {
    "phase9_universe/universe/store.py",
}


def test_known_yf_tickers_only_survives_as_seed_symbol_candidates():
    """``KNOWN_YF_TICKERS`` (the old declared table) must not exist anywhere — its
    replacement is ``data_foundation.symbols.SEED_SYMBOL_CANDIDATES``, a *candidate*
    list the resolver still has to verify, never a trusted mapping."""
    hits = []
    for py_file in _REPO_ROOT.rglob("*.py"):
        if "/.venv/" in str(py_file) or "/__pycache__/" in str(py_file):
            continue
        if py_file.name == "test_criterion_a.py":
            continue  # this file names the retired symbol on purpose, in its own docstring
        if "KNOWN_YF_TICKERS" in py_file.read_text(encoding="utf-8", errors="ignore"):
            hits.append(str(py_file.relative_to(_REPO_ROOT)))
    assert hits == []


def test_discovery_never_looks_up_yf_ticker():
    """``discovery.py`` must construct every fresh ``UniverseRecord`` with
    ``yf_ticker=None`` — the SymbolResolver derives it later, not discovery."""
    path = _REPO_ROOT / "phase9_universe" / "universe" / "discovery.py"
    text = path.read_text(encoding="utf-8")
    assert "yf_ticker=None" in text
    assert not re.search(r"yf_ticker\s*=\s*_lookup", text)


def test_upsert_discovered_excludes_registry_truth_from_conflict_update():
    """The structural half of the D5 guarantee: ``upsert_discovered``'s ``ON CONFLICT
    ... DO UPDATE SET`` must not include ``yf_ticker`` or the three Phase-12 registry
    columns — otherwise a re-discovery would silently reset a verified symbol every
    time it re-touches an already-known epic (the exact bug class D5 exists to close).
    """
    path = _REPO_ROOT / "phase9_universe" / "universe" / "store.py"
    text = path.read_text(encoding="utf-8")
    assert "_PRESERVE_ON_CONFLICT" in text
    preserve_match = re.search(r"_PRESERVE_ON_CONFLICT\s*=\s*frozenset\(\s*\{([^}]*)\}", text)
    assert preserve_match is not None
    preserved = {c.strip().strip('"') for c in preserve_match.group(1).split(",") if c.strip()}
    assert preserved == {"yf_ticker", "data_source_status", "symbol_source", "symbol_checked_at"}
    assert "update_cols" in text and "_PRESERVE_ON_CONFLICT" in text
