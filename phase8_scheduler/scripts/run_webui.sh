#!/usr/bin/env bash
# Launch the Phase-8 read-mostly Web-UI dashboard (Module 12).
#
# ── what it is ───────────────────────────────────────────────────────────────────────────────────
# A localhost FastAPI dashboard that OBSERVES the autonomous demo trader (status, score, confidence,
# trades, lessons, last cycle) and CONTROLS it only by writing the files the daemon already polls —
# the kill-switch (`data/state/KILL`) and the start/stop command file (`data/state/scheduler_command.json`).
# It opens the DB READ-ONLY and never imports the executor/broker/runner: a UI crash can't touch trading
# (concept Decision 14). Built last; the first thing dropped under pressure — never the safety.
#
# ── isolation / safety ───────────────────────────────────────────────────────────────────────────
# Binds 127.0.0.1 only (no auth in v1 — localhost-only by design; light auth is a later carry-over).
# Run it on the same box as the daemon so it reads/writes the same `data/` tree. It does NOT need the
# keyring (it never talks to the broker), unlike `run_scheduler.sh`.
#
# ── usage ────────────────────────────────────────────────────────────────────────────────────────
#   bash phase8_scheduler/scripts/run_webui.sh [--port 8000]
# Then open http://127.0.0.1:8000  (the daemon need not be running — empty cards render fine).
#
# Prereqs (operator, once): `bash scripts/dev_install.sh` (editable installs P1–P8) and
# `pip install fastapi uvicorn` (already in phase8_scheduler/requirements.txt).

set -euo pipefail

# Restart-hygiene (Phase-14 Session-9 NEXT-Block): prepend the canonical
# venv's `bin/` to PATH so this wrapper works after a reboot without requiring
# `source <venv>/bin/activate`. This is the exact fix for `exec: uvicorn: not
# found` after a fresh boot — `uvicorn` lives in phase1_broker_wrapper/.venv/bin
# (installed alongside FastAPI in phase8_scheduler/requirements.txt). Prepending
# is non-destructive — an already-active venv stays first.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
_VENV_BIN="${REPO_ROOT}/phase1_broker_wrapper/.venv/bin"
if [[ -x "${_VENV_BIN}/python" ]]; then
    export PATH="${_VENV_BIN}:${PATH}"
fi
unset _VENV_BIN

PORT=8000
if [[ "${1:-}" == "--port" && -n "${2:-}" ]]; then PORT="$2"; fi

# phase8_scheduler/ (this script lives in phase8_scheduler/scripts/). `webui` is NOT installed as a
# package (pyproject includes only `scheduler*`), so run uvicorn with this dir on the import path.
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
export PYTHONPATH="${PROJECT_DIR}${PYTHONPATH:+:$PYTHONPATH}"

printf '%s [run_webui] dashboard on http://127.0.0.1:%s (read-only DB, localhost-only)...\n' \
    "$(date '+%Y-%m-%d %H:%M:%S')" "${PORT}" >&2
# Phase 16 A-4 (2026-09-05, L8): --no-access-log kills the 16 MB/day uvicorn access log;
# application logs on stderr stay. Restart der WebUI (Block D) wirkt.
exec uvicorn webui.api:app --host 127.0.0.1 --port "${PORT}" --no-access-log
