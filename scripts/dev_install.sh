#!/usr/bin/env bash
#
# dev_install.sh — composition root (concept §"Step C", Phase 5 + Phase 6 + Phase 7 + Phase 8 + Phase 9 + Phase 10 + Phase 12 + Phase 13 + Phase 14).
#
# Editable-install every phase package in dependency order (P1 -> P2 -> P3 -> P4
# -> P5 -> P6 -> P7 -> P8 -> P9 -> P10 -> P12 -> P13 -> P14 -> P15) into the *currently active* virtualenv, so that
#   import broker_wrapper / persistence / external_data / research / execution / debate / reward / scheduler / universe / abstain_lessons / data_foundation / live_data / source_registry / instinct
# all resolve at runtime WITHOUT any sys.path manipulation, and `pytest`
# collects cleanly. Run once per fresh venv. (P6 + P7 import `research`, so they
# are installed after P4; P7 also reuses the Phase-2 `persistence` Database. P8
# composes the whole P1–P7 stack, so it is installed after P7. P9 (`universe`)
# owns its own sqlite3 connection at runtime — no cross-phase import at load
# time — so its position in this list is purely by phase number, not a real
# dependency order. P10 (`abstain_lessons`) is the same: own-connection store,
# no cross-phase import at load time. P12 (`data_foundation`) is the same again:
# own-connection `bars.sqlite` (D4), no cross-phase import at load time — Steps
# 3/4/6/7 wire it INTO P8/P9/P10 via their own lazy imports, not the reverse.
# P13 (`live_data`) is the same again: no cross-phase import at load time, wires
# INTO P1/P8/P10/P12 via lazy imports as each block lands. P14
# (`source_registry`) is the same again: own-connection `trading_bot.sqlite`
# (D3-Muster von UniverseStore/BarArchive), no cross-phase import at load
# time, wires INTO P9/P13 via its own lazy imports as each block lands. P15
# (`instinct`, Phase-15-V4 Instinct-ECC package) is the same again: standalone
# `instinct/` package with no cross-phase import at load time (pure stdlib +
# internal `from instinct.xxx import`), wires INTO P8 (`scripts/wiring.py:383`
# imports `from instinct import InstinctBridge, InstinctConfig, InstinctValidator,
# SingleShotInstinctExtractor`) via Phase-16 Block-D Step-D2.6 lazy import —
# the wiring import is what crashed the scheduler pre-Phase-16 (ModuleNotFoundError
# No module named 'instinct', Session #13 2026-09-07 22:01), because P15 had no
# `pyproject.toml`/`setup.cfg` and was therefore not editable-installed.)
#
# Usage:
#   source <your-venv>/bin/activate
#   bash scripts/dev_install.sh
#   pytest phase5_execution/tests -v       # green => Step C proven (P5)
#   pytest phase6_debate/tests -v          # green => Step C proven (P6)
#   pytest phase7_reward/tests -v          # green => Step C proven (P7)
#   pytest phase8_scheduler/tests -v       # green => Step C proven (P8)
#   pytest phase9_universe/tests -v        # green => Step C proven (P9)
#   pytest phase10_v3/tests -v             # green => Step C proven (P10)
#   pytest phase12_data_foundation/tests -v # green => Step C proven (P12)
#   pytest phase13_live_data/tests -v      # green => Step C proven (P13)
#
# Editable installs change only *packaging*, not code dependencies: each phase
# still imports its siblings only through their defined contracts (cross-phase
# imports stay lazy / Protocol-typed in the wiring layer).

set -euo pipefail

# Restart-hygiene (Phase-14 Session-9 NEXT-Block): prepend the canonical
# venv's `bin/` to PATH so this script works after a reboot without requiring
# `source <venv>/bin/activate`. The venv lives under phase1_broker_wrapper/.venv
# (see the comment header above) and is where the editable installs below land.
# Prepending is non-destructive — an already-active venv stays first.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
_VENV_BIN="${ROOT}/phase1_broker_wrapper/.venv/bin"
if [[ -x "${_VENV_BIN}/python" ]]; then
    export PATH="${_VENV_BIN}:${PATH}"
fi
unset _VENV_BIN

PY="${PYTHON:-python}"

echo "dev_install: using interpreter -> $("$PY" -c 'import sys; print(sys.executable)')"

# Build backend (setuptools>=68 / wheel) must be present for the editable installs.
"$PY" -m pip install --upgrade setuptools wheel

for pkg in \
    phase1_broker_wrapper \
    phase2_persistence \
    phase3_external_data \
    phase4_research \
    phase5_execution \
    phase6_debate \
    phase7_reward \
    phase8_scheduler \
    phase9_universe \
    phase10_v3 \
    phase12_data_foundation \
    phase13_live_data \
    phase14_discovery \
    phase15_v4
do
    echo "dev_install: pip install -e $pkg"
    "$PY" -m pip install -e "$ROOT/$pkg"
done

# P14-F Mini-Plan §4 Schritt 3: install the doc-rotation pre-commit hook
# (tracked installer — .git/hooks/pre-commit is untracked by git, so this
# is the only way it survives a fresh clone). Idempotent: re-running this
# script does not overwrite a hand-edited hook (install_hooks.sh fails
# loudly on body-mismatch instead).
bash "${ROOT}/scripts/install_hooks.sh" || true

echo "dev_install: all fourteen packages installed editable. Run: pytest phase15_v4/tests -v"
