#!/usr/bin/env bash
# Launch the Phase-12 Recorder — a standalone, yFinance-only bar-archive writer (D14).
#
# No IG session, ever: the Recorder never imports broker_wrapper (grep-tested, D14) —
# all IG traffic stays in the scheduler process, which holds the one warm session
# (parallel logins clobber each other's tokens). Double-start-safe: the PID-file guard
# lives in `python -m data_foundation.run` itself (data/state/recorder.pid) — a second
# invocation while one is already alive exits 0 immediately instead of racing it.
#
# ── usage ───────────────────────────────────────────────────────────────────────────
#   bash phase12_data_foundation/scripts/run_recorder.sh [--interval-s 300 ...]
# All flags are forwarded to `python -m data_foundation.run` (see its --help). Logs go
# to stderr. Runnable standalone (archive warm-up ahead of a bot restart) or launched
# automatically from `phase8_scheduler/scripts/run_scheduler.sh`.
#
# Prereq (operator, once): `bash scripts/dev_install.sh` (editable installs, incl. P12).

set -euo pipefail

# phase12_data_foundation/ (this script lives in phase12_data_foundation/scripts/)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "[run_recorder] starting recorder from ${PROJECT_DIR}..." >&2
exec python -m data_foundation.run "$@"
