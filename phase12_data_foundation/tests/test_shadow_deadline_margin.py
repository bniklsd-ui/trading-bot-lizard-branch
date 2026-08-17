"""Structural guard for P12.5 plan §3/U5: ``shadow_pair_scheduler`` in
``phase8_scheduler/scripts/wiring.py`` must pass a deadline with margin, not raw
``window_close`` -- ``wiring.py`` has no dedicated pytest suite of its own (documented
"operator-run, not pytest-collected" convention), so a file-wide grep would not catch a
moved/dead ``deadline`` line, the same gap that let Step 8.5's ``universe_refresher``
finding through (``test_resolver_wiring.py``, same AST-scoping approach)."""

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


def test_shadow_deadline_has_margin():
    tree = ast.parse(_WIRING_PATH.read_text(), filename=str(_WIRING_PATH))
    matches = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "shadow_pair_scheduler"
    ]
    assert len(matches) == 1, (
        f"expected exactly one shadow_pair_scheduler() in {_WIRING_PATH}, found {len(matches)}"
    )
    shadow_pair_scheduler = matches[0]

    deadline_has_margin = any(
        isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "deadline" for t in node.targets)
        and isinstance(node.value, ast.BinOp) and isinstance(node.value.op, ast.Sub)
        for node in _statements_excluding_nested_defs(shadow_pair_scheduler)
    )
    assert deadline_has_margin, (
        "shadow_pair_scheduler()'s deadline assignment no longer subtracts a margin -- "
        "window_close itself leaves the day's last shadow-pair cohort zero tracker "
        "ticks (P12.5 plan §3/U5)"
    )
