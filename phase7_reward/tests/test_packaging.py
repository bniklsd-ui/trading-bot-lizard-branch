"""Packaging smoke test (Step 2/3) — proves the editable install resolves.

Asserts that the ``reward`` package imports **via the editable install**, i.e.
without any ``sys.path`` manipulation — the Phase-7 Step-C "Done when" criterion
(``bash scripts/dev_install.sh`` then ``pytest phase7_reward/tests -v`` green).

As each reward module lands, its own test file carries the real coverage; this
one stays as the standing proof that the package is installed and importable. No
network, no real LLM.
"""

from __future__ import annotations


def test_reward_package_imports_via_editable_install() -> None:
    """`import reward` resolves through the installed package (no sys.path hack)."""
    import reward

    # Since Step 3 the package re-exports its data contracts; assert one is
    # reachable off the top-level package (proves the editable install + the
    # __init__ re-export both work).
    assert hasattr(reward, "__all__")
    assert "RewardConfig" in reward.__all__
    assert reward.RewardConfig().n_min == 10
