"""Packaging smoke test (Step C) — proves the editable install resolves.

This is the only test that exists at the scaffold stage. It asserts that the
``debate`` package imports **via the editable install**, i.e. without any
``sys.path`` manipulation — exactly the Phase-6 Step-C "Done when" criterion
(``bash scripts/dev_install.sh`` then ``pytest phase6_debate/tests -v`` green).

Real module tests (models / context_builder / prompts / llm_caching / budget /
debate / audit) replace this file's role as each module lands; this one stays as
the standing proof that the package is installed and importable. No network, no
real LLM.
"""

from __future__ import annotations


def test_debate_package_imports_via_editable_install() -> None:
    """`import debate` resolves through the installed package (no sys.path hack)."""
    import debate

    # Since Module 1 the package re-exports its data contracts; assert one is
    # reachable off the top-level package (proves the editable install + the
    # __init__ re-export both work).
    assert hasattr(debate, "__all__")
    assert "DebateConfig" in debate.__all__
    assert debate.DebateConfig().max_rounds == 5
