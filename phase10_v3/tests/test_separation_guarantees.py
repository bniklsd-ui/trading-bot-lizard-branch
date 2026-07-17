"""Step 10 §10.4 — Trennungs-Garantien (tests, not prose).

Paper-trades are a hard-separated shadow system: never joined with real trade
outcomes/reward math, never able to reach the broker/order path. These are
structural guarantees, checked here rather than asserted in a docstring.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]

_ORDER_PATH_SYMBOLS = {"place_order", "open_position", "close_position", "modify_position"}


def _imported_names(path: Path) -> set[str]:
    """All names a module imports (``import x`` and ``from x import y``), via ``ast`` —
    a static check, no need to actually import the (phase-isolated, broker-free) module."""
    tree = ast.parse(path.read_text(), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.update(alias.name for alias in node.names)
            if node.module:
                names.add(node.module)
    return names


def test_paper_module_imports_no_broker_order_path():
    """Neither ``paper.py`` nor ``paper_store.py`` imports ``place_order`` or any
    broker open/close/modify-position symbol — structurally unable to touch an order."""
    for rel in ("abstain_lessons/paper.py", "abstain_lessons/paper_store.py"):
        names = _imported_names(_REPO_ROOT / "phase10_v3" / rel)
        assert not (names & _ORDER_PATH_SYMBOLS), f"{rel} imports an order-path symbol: {names}"
        assert not any("broker_wrapper" in n or "execution.order" in n for n in names), (
            f"{rel} imports a broker/order module: {names}"
        )


def test_paper_module_imports_no_execution_package():
    """Neither paper module imports ``execution`` at all (config is duck-typed, plan §10.1) —
    the deterministic core never even sees an ``ExecutionConfig`` class, only its shape."""
    for rel in ("abstain_lessons/paper.py", "abstain_lessons/paper_store.py"):
        names = _imported_names(_REPO_ROOT / "phase10_v3" / rel)
        assert not any(n == "execution" or n.startswith("execution.") for n in names), (
            f"{rel} imports the execution package: {names}"
        )


def test_reward_and_confidence_modules_never_import_paper_or_context_packages():
    """Structural confirmation that Phase 7's reward/confidence math is untouched: no
    ``phase7_reward`` source file imports ``abstain_lessons`` or ``market_context`` (the
    two Phase-10 Block-B packages). Combined with Phase 7's own unchanged (133-test)
    suite staying green, this is the "Confidence-N/Score reads are identical with or
    without paper_trades" guarantee — there is no code path in P7 that could read the
    new table. (A raw text search for "market_context" would false-positive: P7's own
    ``market_context: dict`` parameter/``market_context_json`` column predate this
    package and are unrelated — hence the AST import check, not a substring search.)"""
    reward_pkg = _REPO_ROOT / "phase7_reward" / "reward"
    offending: list[str] = []
    for py_file in reward_pkg.rglob("*.py"):
        names = _imported_names(py_file)
        if any(n == "abstain_lessons" or n.startswith("abstain_lessons.") for n in names) or any(
            n == "market_context" or n.startswith("market_context.") for n in names
        ):
            offending.append(str(py_file.relative_to(_REPO_ROOT)))
    assert offending == [], f"reward/ imports Phase-10 paper/context packages: {offending}"
