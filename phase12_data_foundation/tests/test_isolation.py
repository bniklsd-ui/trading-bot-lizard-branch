"""Structural confirmation of D3 (phase isolation): no ``data_foundation`` module
imports another phase's package at module top-level. Mirrors
``phase10_v3/tests/test_separation_guarantees.py``'s AST-based approach (a static
check, no need to actually import broker/execution modules)."""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PKG_DIR = _REPO_ROOT / "phase12_data_foundation" / "data_foundation"

_OTHER_PHASE_PACKAGES = {
    "broker_wrapper", "persistence", "external_data", "research",
    "execution", "debate", "reward", "scheduler", "universe", "abstain_lessons",
    "market_context",
}


def _top_level_imported_names(path: Path) -> set[str]:
    """Names imported at module top-level (not inside a function/method body) —
    imports inside ``def``/``async def`` bodies are the sanctioned lazy-import
    escape hatch (D3) and are deliberately excluded here."""
    tree = ast.parse(path.read_text(), filename=str(path))
    names: set[str] = set()
    for node in tree.body:  # only module-level statements, not nested function bodies
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module.split(".")[0])
    return names


def test_no_module_top_level_cross_phase_import():
    offending: dict[str, set[str]] = {}
    for py_file in _PKG_DIR.rglob("*.py"):
        names = _top_level_imported_names(py_file)
        hit = names & _OTHER_PHASE_PACKAGES
        if hit:
            offending[str(py_file.relative_to(_REPO_ROOT))] = hit
    assert offending == {}, f"module-top-level cross-phase imports found: {offending}"
