#!/usr/bin/env bash
#
# restart-services.sh — operator helper to inspect, stop, (re)start the four
# trading-bot services: Recorder (Phase 12), Discovery daemon (Phase 14),
# Scheduler (Phase 8), WebUI (Phase 8). Auto-start-safe when called without
# subcommand (default = status).
#
# ── Modes ──────────────────────────────────────────────────────────────────
#   status       print which services are alive + which PID files match
#                (default; same as no args)
#   stop         SIGTERM each service; 5 s grace; SIGKILL if still alive
#   start        start each service that isn't alive yet, idempotent
#   restart      stop + start, sequentially
#   --dry-run    print what would be done; do nothing destructive
#
# ── SAFETY (the project culture encoded) ───────────────────────────────────
# - Never SIGKILL until SIGTERM + 5 s grace has failed. KILL is a stop-rail,
#   not a tool.
# - Never touch data/state/KILL (operator's sticky decision).
# - Never touch data/state/DISCOVERY_ARMED (operator+UI workflow, not ours).
# - Never start a daemon if its PID-file says one is alive: the daemon-side
#   guards (data_foundation.run, source_registry.run) refuse to double-start
#   for a reason, and we'd just race them.
# - Never start scheduler and discovery at the same instant — sequential,
#   with a short sleep, to avoid even theoretical parallel-login risk.
# - Pattern-match the executable AND the cwd to this repo, so an unrelated
#   "python -m scheduler.run" on another box / in another repo doesn't get
#   killed by accident. /proc is Linux-only; on macOS this falls back to a
#   pure-pgrep check (less safe, but the script is also Linux-only by use).
# - All log lines to stderr; stdout stays clean for piping `status`.
#
# ── NOT a replacement for the per-service wrappers ─────────────────────────
# The four `run_*.sh` wrappers in phase*/scripts/ are the single-process start
# points and remain canonical for "start one service". This helper is for the
# robot case (reboot, parallel-login cleanup, full restart after a config
# change); reach for the per-service wrappers first.
#
# ── USE ────────────────────────────────────────────────────────────────────
#   bash scripts/restart-services.sh status
#   bash scripts/restart-services.sh restart --dry-run    # preview first
#   bash scripts/restart-services.sh restart
#

set -euo pipefail

# ── Paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
STATE_DIR="${REPO_ROOT}/data/state"

# Restart-hygiene (Phase-14 Session-10 NEXT-Block, shared boilerplate with
# the per-service wrappers): prepend the canonical venv's bin/ to PATH so this
# helper works after a reboot without requiring `source <venv>/bin/activate`.
_VENV_BIN="${REPO_ROOT}/phase1_broker_wrapper/.venv/bin"
if [[ -x "${_VENV_BIN}/python" ]]; then
    export PATH="${_VENV_BIN}:${PATH}"
fi
unset _VENV_BIN

# ── Service registry ──────────────────────────────────────────────────────
# Each entry: cmd-pattern  start-script (relative to REPO_ROOT)
# Order in the table matters: restart() stops them in REVERSE order and
# starts in FORWARD order.
SERVICES=(
    "phase12_data_foundation/scripts/run_recorder.sh"
    "phase14_discovery/scripts/run_discovery.sh"
    "phase8_scheduler/scripts/run_scheduler.sh"
    "phase8_scheduler/scripts/run_webui.sh"
)
# Map each service to its pgrep fingerprint (what it looks like in `ps -ef`).
# These are the same patterns the live daemon-process argv carries.
declare -A PGREP_PATTERN=(
    ["phase12_data_foundation/scripts/run_recorder.sh"]="python -m data_foundation.run"
    ["phase14_discovery/scripts/run_discovery.sh"]="python -m source_registry.run"
    ["phase8_scheduler/scripts/run_scheduler.sh"]="python -m scheduler.run"
    ["phase8_scheduler/scripts/run_webui.sh"]="uvicorn webui.api:app"
)
declare -A PID_FILE=(
    ["phase12_data_foundation/scripts/run_recorder.sh"]="${STATE_DIR}/recorder.pid"
    ["phase14_discovery/scripts/run_discovery.sh"]="${STATE_DIR}/discovery.pid"
    ["phase8_scheduler/scripts/run_scheduler.sh"]=""
    ["phase8_scheduler/scripts/run_webui.sh"]=""
)

# ── Logging ────────────────────────────────────────────────────────────────
log() { printf "[restart-services] %s\n" "$*" >&2; }

# ── Service discovery ─────────────────────────────────────────────────────
#
# Return PIDs of a service that:
#   - match the pgrep fingerprint
#   - have cwd INSIDE REPO_ROOT (Linux /proc; falls back to "skip cwd check"
#     on macOS — the script is Linux-only by use anyway). The wrappers do
#     `cd phase<X>/...` before exec-ing python, so cwd is exactly the phase
#     dir, not the repo root. The check is "cwd starts with $REPO_ROOT/".
#
# Echo one PID per line; empty if none.
list_pids() {
    local pattern="$1"
    local pids
    pids=$(pgrep -f -- "$pattern" || true)
    if [[ -z "$pids" ]]; then
        return 0
    fi
    local pid
    for pid in $pids; do
        if [[ -r "/proc/${pid}/cwd" ]]; then
            local cwd
            cwd=$(readlink "/proc/${pid}/cwd" 2>/dev/null || echo "")
            if [[ "$cwd" == "${REPO_ROOT}" || "$cwd" == "${REPO_ROOT}/"* ]]; then
                echo "$pid"
            fi
        else
            # Non-Linux (macOS, etc.): no /proc, accept the pgrep result as-is.
            echo "$pid"
        fi
    done
}

# ── Status ─────────────────────────────────────────────────────────────────
cmd_status() {
    local any=0
    printf "[restart-services] repo=%s\n" "$REPO_ROOT" >&2
    for svc in "${SERVICES[@]}"; do
        local pattern="${PGREP_PATTERN[$svc]}"
        local pids
        pids=$(list_pids "$pattern")
        if [[ -n "$pids" ]]; then
            printf "[restart-services]   ALIVE  %-50s pids=%s\n" "$svc" "$(echo $pids | tr '\n' ' ')" >&2
            any=1
        else
            printf "[restart-services]   dead   %-50s\n" "$svc" >&2
        fi
    done
    # Surface the operator-sticky files we never touch.
    [[ -f "${STATE_DIR}/KILL" ]] && printf "[restart-services]   NOTE   KILL file present (operator-controlled, untouched): %s\n" "${STATE_DIR}/KILL" >&2
    [[ -f "${STATE_DIR}/DISCOVERY_ARMED" ]] && printf "[restart-services]   NOTE   DISCOVERY_ARMED present (operator+UI-controlled, untouched)\n" >&2
    return $((1 - any))   # 0 if any alive, 1 if all dead
}

# ── Stop ───────────────────────────────────────────────────────────────────
# Stop a single service: TERM, wait 5 s, KILL if still alive.
# Honors --dry-run. Never modifies operator-controlled files.
stop_one() {
    local svc="$1"
    local pattern="${PGREP_PATTERN[$svc]}"
    local pidfile="${PID_FILE[$svc]}"
    local pids
    pids=$(list_pids "$pattern")
    if [[ -z "$pids" ]]; then
        log "stop: $svc already down"
        return 0
    fi
    for pid in $pids; do
        if [[ "${DRY_RUN:-0}" == "1" ]]; then
            log "stop: (dry-run) would TERM pid=$pid for $svc"
            continue
        fi
        log "stop: TERM pid=$pid ($svc)"
        kill -TERM "$pid" 2>/dev/null || log "stop: pid=$pid already gone"
    done
    # Wait up to 5 s for graceful exit.
    local waited=0
    while (( waited < 5 )); do
        local still
        still=$(list_pids "$pattern")
        if [[ -z "$still" ]]; then
            log "stop: $svc down (graceful)"
            return 0
        fi
        sleep 1
        waited=$((waited + 1))
    done
    # Fallback to KILL.
    for pid in $pids; do
        if kill -0 "$pid" 2>/dev/null; then
            if [[ "${DRY_RUN:-0}" == "1" ]]; then
                log "stop: (dry-run) would KILL pid=$pid for $svc (TERM did not stop in 5 s)"
            else
                log "stop: KILL pid=$pid ($svc) — TERM did not stop in 5 s"
                kill -KILL "$pid" 2>/dev/null || true
            fi
        fi
    done
}

# ── Start ──────────────────────────────────────────────────────────────────
# Start a single service via its canonical wrapper, nohup so it survives
# our shell exit. Skips if a process is already alive (prevents races).
start_one() {
    local svc="$1"
    local pattern="${PGREP_PATTERN[$svc]}"
    local script="${REPO_ROOT}/${svc}"
    if [[ ! -x "$script" ]]; then
        log "start: wrapper not executable: $script — skipping"
        return 0
    fi
    local pids
    pids=$(list_pids "$pattern")
    if [[ -n "$pids" ]]; then
        log "start: $svc already alive (pids=$(echo $pids | tr '\n' ' ')) — skipping (refuse double-start)"
        return 0
    fi
    if [[ "${DRY_RUN:-0}" == "1" ]]; then
        log "start: (dry-run) would nohup $script"
        return 0
    fi
    log "start: nohup $script"
    # log redirected to data/state/<svc>.log; stderr also captured.
    local svcname
    svcname=$(basename "$svc" .sh)
    nohup "$script" >>"${STATE_DIR}/${svcname}.log" 2>&1 &
    disown || true
    sleep 2   # let the daemon's own PID-file + preflight settle before the next one
}

# ── Top-level modes ────────────────────────────────────────────────────────
cmd_stop() {
    log "stop: starting (reverse-start order)"
    local i
    for (( i=${#SERVICES[@]} - 1; i>=0; i-- )); do
        stop_one "${SERVICES[$i]}"
    done
    log "stop: done"
}

cmd_start() {
    log "start: starting (forward order, sequential)"
    for svc in "${SERVICES[@]}"; do
        start_one "$svc"
    done
    log "start: done"
}

cmd_restart() {
    cmd_stop
    cmd_start
}

# ── CLI parsing ────────────────────────────────────────────────────────────
DRY_RUN=0
SUBCMD="status"
SUBCMD_ARGS=()
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        status|stop|start|restart) SUBCMD="$arg" ;;
        -h|--help)
            sed -n '2,40p' "$0"
            exit 0
            ;;
        *)
            echo "unknown arg: $arg" >&2
            exit 2
            ;;
    esac
done

# ── Entry ──────────────────────────────────────────────────────────────────
case "$SUBCMD" in
    status)  cmd_status ;;
    stop)    cmd_stop ;;
    start)   cmd_start ;;
    restart) cmd_restart ;;
    *) echo "internal error: unknown subcmd $SUBCMD" >&2; exit 1 ;;
esac
