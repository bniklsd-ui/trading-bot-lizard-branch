#!/usr/bin/env bash
# Launch the Phase-8 autonomous scheduler daemon (demo-only).
#
# ── WHY THIS SCRIPT EXISTS (concept Q3 — the deployment top-risk) ───────────────────────────────
# The daemon reads the IG-Demo credentials from the OS keyring (gnome-keyring / Secret-Service via
# D-Bus). That requires an UNLOCKED, interactive login session with a live session bus. Start this
# from a logged-in desktop terminal (or a `tmux`/`screen` inside one) — NOT from a bare cron entry,
# a detached systemd system service, or an SSH session without a session bus, or the keyring will be
# unreachable. The runner's fail-closed preflight (`get_credential` + DB check) catches that loudly
# and refuses to trade rather than running blind — but the right fix is to start it where the keyring
# lives.
#
# ── known issue: background / headless ──────────────────────────────────────────────────────────
# Running fully head-less (no session bus) will fail the keyring preflight by design. v1 recommendation:
# run inside a persistent unlocked user session (e.g. `tmux` under the logged-in user, or
# `systemd --user` with `loginctl enable-linger` + PAM keyring auto-unlock). Full systemd hardening is
# a Phase-9 / ops carry-over, deliberately out of Phase-8 scope.
#
# ── usage ───────────────────────────────────────────────────────────────────────────────────────
#   bash phase8_scheduler/scripts/run_scheduler.sh [--daily-loss-cap 1800 --max-trades 5 ...]
# All flags are forwarded to `python -m scheduler.run` (see its --help). Logs go to stderr.
#
# Prereqs (operator, once): `bash scripts/dev_install.sh` (editable installs P1–P8) and
# `python phase2_persistence/scripts/init_db.py` (applies migration 002).

set -euo pipefail

# phase8_scheduler/ (this script lives in phase8_scheduler/scripts/)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "[run_scheduler] starting daemon from ${PROJECT_DIR} (keyring must be unlocked)..." >&2
exec python -m scheduler.run "$@"
