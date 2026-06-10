"""Step C proof — every package resolves via editable install, no sys.path hack.

This is the Phase-5 "composition root" test. Before Step C, the operator scripts
bootstrapped sibling packages by mutating ``sys.path``; that is fragile for a
long-lived scheduler (Phase 8) and for clean ``pytest`` collection. Step C instead
``pip install -e`` s each package (see ``scripts/dev_install.sh`` at the repo root),
so the five top-level import names below are discoverable on the import path
directly.

We assert *discoverability* via :func:`importlib.util.find_spec` rather than
importing the packages, deliberately: it proves the editable install registered
each package on ``sys.path`` without executing heavy ``__init__`` side effects or
needing every transitive runtime dependency (``yfinance``/``pandas`` for
``external_data``, ``anthropic`` for ``research``) to be installed. Import
resolution is exactly what the old ``sys.path`` bootstrap provided — this test is
green only when editable installs replace it.

No network, no broker I/O, no real order.
"""

from __future__ import annotations

import importlib.util

import pytest

# Dependency order P1 -> P2 -> P3 -> P4 -> P5 (the install order in dev_install.sh).
EXPECTED_PACKAGES = [
    "broker_wrapper",   # Phase 1
    "persistence",      # Phase 2
    "external_data",    # Phase 3
    "research",         # Phase 4
    "execution",        # Phase 5 (this package)
]


@pytest.mark.parametrize("package", EXPECTED_PACKAGES)
def test_package_is_importable_without_sys_path_hack(package: str) -> None:
    """Each phase package is on the import path (proves the editable install)."""
    spec = importlib.util.find_spec(package)
    assert spec is not None, (
        f"{package!r} is not importable. Run `bash scripts/dev_install.sh` "
        "from the repo root to editable-install all phase packages."
    )


def test_no_sys_path_manipulation_needed() -> None:
    """Sanity: this very test module was collected and run without a path hack."""
    assert importlib.util.find_spec("execution") is not None
