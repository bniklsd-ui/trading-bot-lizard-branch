#!/usr/bin/env bash
#
# install_units.sh — tracked installer for the four systemd **user** units that
# autostart the trading bot (Phase 16 R5). Pattern: scripts/install_hooks.sh.
#
# — Copies phase16_activation/systemd/tradingbot-*.service into
#   ~/.config/systemd/user/, runs `systemctl --user daemon-reload`, then
#   `enable` (NOT start — the start of a preregistered run is an operator
#   action, R7.4).
# — Idempotent: identical content → no copy, still enables.
# — User units, never root: the credentials live in the user's Secret Service
#   (gnome-keyring); a system unit could not reach them. `Linger=yes` is
#   already set for this user, so the units come up at boot without a login.
# — Units are WantedBy=graphical-session.target (not default.target): the
#   keyring is unlocked by the gdm-autologin session, so the session is the
#   real dependency.
#
# Usage:
#   bash scripts/install_units.sh              # install + enable (idempotent)
#   bash scripts/install_units.sh --dry-run    # preview only
#   bash scripts/install_units.sh --verify     # only systemd-analyze verify
#
# Exit codes: 0 ok · 1 verify failed · 2 I/O error

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SRC_DIR="${REPO_ROOT}/phase16_activation/systemd"
DEST_DIR="${HOME}/.config/systemd/user"
UNITS=(tradingbot-scheduler.service tradingbot-recorder.service
       tradingbot-discovery.service tradingbot-webui.service)

DRY_RUN=0; VERIFY_ONLY=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        --verify)  VERIFY_ONLY=1 ;;
        -h|--help) sed -n '2,25p' "$0"; exit 0 ;;
        *) echo "unknown arg: $arg" >&2; exit 2 ;;
    esac
done

log() { printf "[install_units] %s\n" "$*" >&2; }

# systemd-analyze verify is the honest check for a unit file: it parses the
# same way systemd does and complains about misplaced keys (e.g. StartLimit*
# in [Service] instead of [Unit]).
log "verify: systemd-analyze --user verify"
if ! systemd-analyze --user verify "${SRC_DIR}"/tradingbot-*.service; then
    log "verify FAILED — not installing"
    exit 1
fi
log "verify: ok"
[[ "$VERIFY_ONLY" == "1" ]] && exit 0

mkdir -p "$DEST_DIR"
for unit in "${UNITS[@]}"; do
    src="${SRC_DIR}/${unit}"; dest="${DEST_DIR}/${unit}"
    if [[ ! -f "$src" ]]; then log "missing source unit: $src"; exit 2; fi
    if [[ -f "$dest" ]] && cmp -s "$src" "$dest"; then
        log "up-to-date: $unit"
        continue
    fi
    if [[ "$DRY_RUN" == "1" ]]; then log "(dry-run) would copy $unit"; continue; fi
    cp "$src" "$dest"
    log "installed: $unit"
done

if [[ "$DRY_RUN" == "1" ]]; then
    log "(dry-run) would: systemctl --user daemon-reload && enable ${UNITS[*]}"
    exit 0
fi

systemctl --user daemon-reload
systemctl --user enable "${UNITS[@]}"
log "enabled (NOT started — start is the operator's step, R7.4)"
log "check: systemctl --user list-dependencies graphical-session.target | grep tradingbot"
