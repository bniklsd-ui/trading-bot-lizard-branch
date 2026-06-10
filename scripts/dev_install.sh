#!/usr/bin/env bash
#
# dev_install.sh — Phase-5 composition root (concept §"Step C").
#
# Editable-install every phase package in dependency order (P1 -> P2 -> P3 -> P4
# -> P5) into the *currently active* virtualenv, so that
#   import broker_wrapper / persistence / external_data / research / execution
# all resolve at runtime WITHOUT any sys.path manipulation, and `pytest`
# collects cleanly. Run once per fresh venv.
#
# Usage:
#   source <your-venv>/bin/activate
#   bash scripts/dev_install.sh
#   pytest phase5_execution/tests -v       # green => Step C proven
#
# Editable installs change only *packaging*, not code dependencies: each phase
# still imports its siblings only through their defined contracts (cross-phase
# imports stay lazy / Protocol-typed in the wiring layer).

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${PYTHON:-python}"

echo "dev_install: using interpreter -> $("$PY" -c 'import sys; print(sys.executable)')"

# Build backend (setuptools>=68 / wheel) must be present for the editable installs.
"$PY" -m pip install --upgrade setuptools wheel

for pkg in \
    phase1_broker_wrapper \
    phase2_persistence \
    phase3_external_data \
    phase4_research \
    phase5_execution
do
    echo "dev_install: pip install -e $pkg"
    "$PY" -m pip install -e "$ROOT/$pkg"
done

echo "dev_install: all five packages installed editable. Run: pytest phase5_execution/tests -v"
