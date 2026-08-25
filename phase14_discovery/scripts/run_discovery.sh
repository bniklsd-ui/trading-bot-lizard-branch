#!/usr/bin/env bash
# Launch the Phase-14 Discovery daemon — the file-flag-gated source-availability re-verifier.
#
# Like the Phase-12 Recorder (``run_recorder.sh``), this script is a thin wrapper that
# ``exec``s into the daemon entrypoint. The wrapper exists so ``run_scheduler.sh`` can
# autostart the daemon via ``nohup`` (one line, no inline Python). Logs go to stderr
# by default; ``run_scheduler.sh`` redirects them to ``data/state/discovery.log`` when
# autostarting.
#
# ── safety: fail-safe unarmed ────────────────────────────────────────────────────────
# The daemon is **always safe to start**: its first action every cycle is
# ``source_registry.arm.is_armed()`` (Plan D10). Absent flag file → the daemon sleeps,
# does **zero** network calls, **zero** DB writes, and logs only a debug tick. The only
# documented way to enable Discovery is the Web-UI's ARM DISCOVERY button (which writes
# ``data/state/DISCOVERY_ARMED``); an operator may also ``touch`` it by hand. The point
# of the safe-default-False flag is that *autostarting* the daemon is **unbedenklich**
# — it costs nothing while unarmed.
#
# ── usage ────────────────────────────────────────────────────────────────────────────
#   bash phase14_discovery/scripts/run_discovery.sh [--interval-s 3600 --once ...]
# All flags are forwarded to ``python -m source_registry.run`` (see its --help). The
# most useful operator-mode flag is ``--once``: runs a single cycle (arming honoured,
# state file written) and exits — no PID file, no infinite loop.
#
# Prereq (operator, once): ``bash scripts/dev_install.sh`` (editable installs incl. P14).

set -euo pipefail

# Restart-hygiene (Phase-14 Session-9 NEXT-Block): prepend the canonical
# venv's `bin/` to PATH so this wrapper works after a reboot without requiring
# `source <venv>/bin/activate`. The venv lives under phase1_broker_wrapper/.venv
# (where `scripts/dev_install.sh` puts every phase's editable install) and is
# the only place that has the `python` module this wrapper `exec`s. Prepending
# is non-destructive — an already-active venv stays first.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
_VENV_BIN="${REPO_ROOT}/phase1_broker_wrapper/.venv/bin"
if [[ -x "${_VENV_BIN}/python" ]]; then
    export PATH="${_VENV_BIN}:${PATH}"
fi
unset _VENV_BIN

# phase14_discovery/ (this script lives in phase14_discovery/scripts/)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "[run_discovery] starting daemon from ${PROJECT_DIR} (unarmed ⇒ noop)..." >&2
exec python -m source_registry.run "$@"
