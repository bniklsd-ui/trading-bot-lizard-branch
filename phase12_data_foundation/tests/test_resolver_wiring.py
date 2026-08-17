"""Structural guard for D6 / Plan §6 Step 8.5: ``universe_refresher`` in
``phase8_scheduler/scripts/wiring.py`` must actually call ``SymbolResolver``.

``SymbolResolver`` was built and fully unit-tested in Step 3 (commit ``c198ca5``) but
never called from anywhere at runtime until Step 8.5 — a "built, never wired" gap none
of Steps 4-7's own acceptance greps caught, because none of them grepped for a resolver
*caller*. AST-based (mirrors ``test_isolation.py``'s approach) rather than a bare
file-wide grep, and scoped to ``universe_refresher``'s own body (nested ``def``s
excluded, same reasoning as ``test_isolation.py:27``) — a future refactor that buries
the call inside an inner helper nobody calls must still fail this test, not just one
that deletes the call outright."""

from __future__ import annotations

import ast
from pathlib import Path

_WIRING_PATH = (
    Path(__file__).resolve().parents[2]
    / "phase8_scheduler" / "scripts" / "wiring.py"
)

_FUNC_DEF_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef)


def _statements_excluding_nested_defs(func: ast.FunctionDef) -> list[ast.AST]:
    """Flatten ``func.body`` into nodes, pruning any subtree rooted at a nested
    ``def`` before it is walked."""
    collected: list[ast.AST] = []
    stack = list(func.body)
    while stack:
        node = stack.pop()
        collected.append(node)
        if isinstance(node, _FUNC_DEF_TYPES):
            continue  # prune: do not descend into a nested function's own body
        stack.extend(ast.iter_child_nodes(node))
    return collected


def test_universe_refresher_calls_symbol_resolver():
    tree = ast.parse(_WIRING_PATH.read_text(), filename=str(_WIRING_PATH))
    matches = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "universe_refresher"
    ]
    assert len(matches) == 1, (
        f"expected exactly one universe_refresher() in {_WIRING_PATH}, found {len(matches)}"
    )
    universe_refresher = matches[0]

    calls_symbol_resolver = any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id == "SymbolResolver"
        for node in _statements_excluding_nested_defs(universe_refresher)
    )
    assert calls_symbol_resolver, (
        "universe_refresher()'s own body (excluding any nested def) no longer calls "
        "SymbolResolver() — measurable_universe() will stay permanently empty "
        "(D6 / Plan §6 Step 8.5)"
    )
