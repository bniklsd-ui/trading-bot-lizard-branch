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
# — SCHEDULER-HOLD (Phase 17 B-0, 2026-10-25): while the marker file
#   data/state/SCHEDULER_HELD exists, the scheduler unit is **not** enabled
#   and the installer says so loudly. Rationale: Phase 17 stops the scheduler
#   on purpose (Plan §6 B-0, Plan T22) until E-3 — only the scheduler holds an
#   IG session. A reboot (VM-host event, Plan T10) or a re-run of this
#   installer would otherwise switch the deliberately stopped scheduler back on
#   and break that decision. The marker is operator-sticky, same pattern as
#   data/state/KILL and data/state/DISCOVERY_ARMED — this script never creates
#   it on its own, it only honours it.
#
# Usage:
#   bash scripts/install_units.sh                 # install + enable (idempotent)
#   bash scripts/install_units.sh --dry-run       # preview only
#   bash scripts/install_units.sh --verify        # only systemd-analyze verify
#   bash scripts/install_units.sh --check         # report-only: installed/enabled per unit
#   bash scripts/install_units.sh --hold          # mark the scheduler as deliberately stopped
#   bash scripts/install_units.sh --release-hold  # remove that marker again (E-3)
#
# Exit codes: 0 ok · 1 verify failed / drift in --check · 2 I/O error

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SRC_DIR="${REPO_ROOT}/phase16_activation/systemd"
DEST_DIR="${HOME}/.config/systemd/user"
UNITS=(tradingbot-scheduler.service tradingbot-recorder.service
       tradingbot-discovery.service tradingbot-webui.service)

# Scheduler hold (Phase 17 B-0). TRADINGBOT_HOLD_FILE exists so the tests can
# point the marker at a tmp path instead of the live data/state directory.
HOLD_FILE="${TRADINGBOT_HOLD_FILE:-${REPO_ROOT}/data/state/SCHEDULER_HELD}"
HELD_UNIT="tradingbot-scheduler.service"

DRY_RUN=0; VERIFY_ONLY=0; CHECK_ONLY=0; HOLD=0; RELEASE_HOLD=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        --verify)  VERIFY_ONLY=1 ;;
        --check)   CHECK_ONLY=1 ;;
        --hold)    HOLD=1 ;;
        --release-hold) RELEASE_HOLD=1 ;;
        -h|--help) sed -n '2,35p' "$0"; exit 0 ;;
        *) echo "unknown arg: $arg" >&2; exit 2 ;;
    esac
done

log() { printf "[install_units] %s\n" "$*" >&2; }

# True while the scheduler-hold marker exists (operator-sticky).
hold_active() { [[ -f "$HOLD_FILE" ]]; }

# ── Hold: create / release the marker ───────────────────────────────────────
# `--hold` marks the scheduler as deliberately stopped (marker + autostart off),
# `--release-hold` removes the marker again. Neither installs anything.
if [[ "$HOLD" == "1" || "$RELEASE_HOLD" == "1" ]]; then
    if [[ "$HOLD" == "1" ]]; then
        if hold_active; then
            log "hold: marker already present: $HOLD_FILE"
        else
            mkdir -p "$(dirname "$HOLD_FILE")"
            printf 'Scheduler-HOLD (Phase 17 B-0) — erstellt %s\n' "$(date -Is)" > "$HOLD_FILE"
            log "hold: marker created: $HOLD_FILE"
        fi
        if [[ -f "${DEST_DIR}/${HELD_UNIT}" ]]; then
            if [[ "$DRY_RUN" == "1" ]]; then
                log "hold: (dry-run) would: systemctl --user disable ${HELD_UNIT}"
            else
                systemctl --user disable "$HELD_UNIT" || true
                log "hold: autostart disabled: ${HELD_UNIT}"
            fi
        else
            log "hold: unit not installed yet — nothing to disable"
        fi
        log "hold: active — the scheduler unit is NOT enabled (no autostart after reboot)"
        exit 0
    fi
    # --release-hold
    if hold_active; then
        if [[ "$DRY_RUN" == "1" ]]; then
            log "hold: (dry-run) would remove $HOLD_FILE"
        else
            rm -f "$HOLD_FILE"
            log "hold: marker removed: $HOLD_FILE"
        fi
    else
        log "hold: no marker present: $HOLD_FILE (nothing to release)"
    fi
    log "hold: released — 'bash scripts/install_units.sh' enables all four units again"
    exit 0
fi

# systemd-analyze verify is the honest check for a unit file: it parses the
# same way systemd does and complains about misplaced keys (e.g. StartLimit*
# in [Service] instead of [Unit]).
log "verify: systemd-analyze --user verify"
if systemd-analyze --user verify "${SRC_DIR}"/tradingbot-*.service; then
    log "verify: ok"
    VERIFY_OK=1
else
    log "verify FAILED"
    VERIFY_OK=0
    if [[ "$CHECK_ONLY" != "1" ]]; then
        log "verify FAILED — not installing"
        exit 1
    fi
fi

# ── --check: report only, never change anything ─────────────────────────────
# Expected state per unit: unit file installed and identical to the tracked
# source, and enabled — EXCEPT the held scheduler, which must be installed
# and *disabled* (autostart off, Phase 17 B-0). Exit 1 on any drift.
if [[ "$CHECK_ONLY" == "1" ]]; then
    drift=0
    for unit in "${UNITS[@]}"; do
        src="${SRC_DIR}/${unit}"; dest="${DEST_DIR}/${unit}"
        state_installed="missing"; state_enabled="unknown"
        if [[ -f "$dest" ]]; then
            if cmp -s "$src" "$dest"; then state_installed="current"; else state_installed="differs"; fi
        fi
        # `is-enabled` prints the state on stdout but exits non-zero for
        # "disabled" (1) / "not-found" (4) — keep the printed word, not the code.
        state_enabled="$(systemctl --user is-enabled "$unit" 2>/dev/null || true)"
        state_enabled="${state_enabled:-not-found}"
        expect_enabled="enabled"
        if [[ "$unit" == "$HELD_UNIT" ]] && hold_active; then
            expect_enabled="disabled"
        fi
        status="ok"
        if [[ "$state_installed" != "current" ]]; then
            status="DRIFT"; drift=1
        elif [[ "$state_enabled" != "$expect_enabled" ]]; then
            status="DRIFT"; drift=1
        fi
        log "check: ${unit} installed=${state_installed} enabled=${state_enabled} expected=${expect_enabled} → ${status}"
    done
    if hold_active; then
        log "check: hold ACTIVE ($HOLD_FILE) — ${HELD_UNIT} stays disabled on purpose (Phase 17 B-0)"
    else
        log "check: hold inactive (no $HOLD_FILE)"
    fi
    [[ "$VERIFY_OK" == "1" ]] || drift=1
    if [[ "$drift" == "0" ]]; then
        log "check: all four units match the expected state"
        exit 0
    fi
    log "check: DRIFT detected (see above) — 'bash scripts/install_units.sh' fixes it"
    exit 1
fi

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

# Units to enable — the held scheduler is skipped (Phase 17 B-0).
UNITS_TO_ENABLE=()
for unit in "${UNITS[@]}"; do
    if [[ "$unit" == "$HELD_UNIT" ]] && hold_active; then
        log "HOLD: ${HELD_UNIT} is deliberately stopped (marker: $HOLD_FILE) — NOT enabling (no autostart after reboot)"
        continue
    fi
    UNITS_TO_ENABLE+=("$unit")
done

if [[ "$DRY_RUN" == "1" ]]; then
    if ((${#UNITS_TO_ENABLE[@]} > 0)); then
        log "(dry-run) would: systemctl --user daemon-reload && enable ${UNITS_TO_ENABLE[*]}"
    else
        log "(dry-run) would: systemctl --user daemon-reload (no unit to enable)"
    fi
    exit 0
fi

systemctl --user daemon-reload
if ((${#UNITS_TO_ENABLE[@]} > 0)); then
    systemctl --user enable "${UNITS_TO_ENABLE[@]}"
    log "enabled: ${UNITS_TO_ENABLE[*]} (NOT started — start is the operator's step, R7.4)"
fi
if hold_active; then
    log "HOLD active ($HOLD_FILE): ${HELD_UNIT} stays disabled. Release before E-3:"
    log "HOLD active: bash scripts/install_units.sh --release-hold"
fi
log "check: systemctl --user list-dependencies graphical-session.target | grep tradingbot"
