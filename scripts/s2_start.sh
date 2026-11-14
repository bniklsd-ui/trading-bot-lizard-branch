#!/usr/bin/env bash
#
# s2_start.sh — Phase-17 -S2 start (Plan §26 F-26f + phase17_testbed/PHASE17_SHAKEDOWN_PREREGISTRATION_S2.md).
#
# Run by tradingbot-s2-start.timer on Mon 2026-11-16 07:30 Berlin. It does the
# prereg's "Start am D1-Morgen" block (release hold → install units → start the
# scheduler) plus the two things a person at 07:30 would have to remember:
#
#   1. Guard: start ONLY on D1 and before 08:55 Berlin. A later start (e.g. a
#      Persistent= catch-up after the VM was down) would not make D1 a full
#      trading day — the registered window would be void (prereg BLUF, K7-v5).
#      The script then refuses (exit 1) and the start becomes a Nikinger decision.
#   2. The Aktiv-Block is entered before 09:00 (S1 finding N1): start line, HEAD,
#      open positions — from append-only sources, committed locally as a doc
#      commit (allowed in the window). Fail-soft: the bot never depends on it.
#
# Only the scheduler is started — recorder, discovery and webui keep running
# (F-26f: K1 counts their starts). Pattern: scripts/e3_deploy.sh (E-3).
#
# Usage:
#   bash scripts/s2_start.sh            # the start
#   bash scripts/s2_start.sh --dry-run  # print every step, touch nothing
#
# Exit codes: 0 started · 1 refused/aborted (see the log) · 2 usage error
#
# Environment overrides (defaults are the live values):
#   S2_DAY             the only Berlin day a start may happen (default 2026-11-16)
#   S2_LATEST_START    Berlin HH:MM from which nothing is started (default 08:55)
#   S2_REPO_ROOT       repo root (default: the parent of scripts/)
#   S2_DATA_DIR        data directory (default: $S2_REPO_ROOT/data)
#   S2_SKIP_PREFLIGHT  1 = skip the read-only pre-flight (tests)
#   S2_SKIP_AKTIV      1 = do not write the Aktiv-Block
#   S2_START_POLL      tries/2 s to wait for the start line (default 60 = 120 s)
#   S2_PREFLIGHT_WAIT  seconds to wait for the daemon's preflight (default 15)

# No `set -e`: E-3 died in step 7 on `set -e` + an empty grep (finding N3) —
# every step here checks its own exit status and says why it stops.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${S2_REPO_ROOT:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
DATA_DIR="${S2_DATA_DIR:-${REPO_ROOT}/data}"
STATE_DIR="${DATA_DIR}/state"
LOG_FILE="${STATE_DIR}/s2_start.log"
SCHED_LOG="${STATE_DIR}/run_scheduler.log"
PREREG="${REPO_ROOT}/phase17_testbed/PHASE17_SHAKEDOWN_PREREGISTRATION_S2.md"
DAY="${S2_DAY:-2026-11-16}"
LATEST_START="${S2_LATEST_START:-08:55}"
PROFILE="all_m3"
UNIT="tradingbot-scheduler.service"
ALL_UNITS=(tradingbot-scheduler.service tradingbot-recorder.service
           tradingbot-discovery.service tradingbot-webui.service)
PY="${REPO_ROOT}/phase1_broker_wrapper/.venv/bin/python"

DRY_RUN=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        -h|--help) sed -n '2,34p' "$0"; exit 0 ;;
        *) echo "unknown arg: ${arg}" >&2; exit 2 ;;
    esac
done

mkdir -p "${STATE_DIR}"
log() { printf '[s2-start] %s\n' "$*" | tee -a "${LOG_FILE}" >&2; }
die() { log "ABORT: $*"; exit 1; }
run() { log "\$ $*"; [[ "${DRY_RUN}" == "1" ]] || "$@"; }

log "=== -S2 start === $(date -Is) (repo=${REPO_ROOT}, dry-run=${DRY_RUN})"

# ── Guard: D1 and before LATEST_START (Berlin) ───────────────────────────────
today="$(TZ=Europe/Berlin date +%F)"
hm="$(TZ=Europe/Berlin date +%H:%M)"
if [[ "${today}" != "${DAY}" || ! "${hm}" < "${LATEST_START}" ]]; then
    msg="it is ${today} ${hm} Berlin — the start is only allowed on ${DAY} before ${LATEST_START} (D1 must be a full trading day: prereg BLUF / K7-v5). NOT started — a later start is a Nikinger decision."
    [[ "${DRY_RUN}" == "1" ]] && log "WARN (dry-run): ${msg}" || die "${msg}"
else
    log "OK: ${today} ${hm} Berlin < ${LATEST_START}"
fi

# ── Pre-flight (read-only) ────────────────────────────────────────────────────
if [[ "${S2_SKIP_PREFLIGHT:-0}" != "1" ]]; then
    git -C "${REPO_ROOT}" fetch origin main --quiet 2>/dev/null || log "WARN: git fetch failed (offline?) — comparing against the local origin/main ref"
    head_sha="$(git -C "${REPO_ROOT}" rev-parse HEAD 2>/dev/null || echo unknown)"
    origin_sha="$(git -C "${REPO_ROOT}" rev-parse origin/main 2>/dev/null || echo unknown)"
    [[ "${head_sha}" == "${origin_sha}" && "${head_sha}" != "unknown" ]] \
        || die "HEAD (${head_sha}) != origin/main (${origin_sha}) — only the reviewed, pushed state may start (T23)"
    log "OK: HEAD == origin/main (${head_sha:0:7})"

    bash "${REPO_ROOT}/scripts/install_units.sh" --check >/dev/null 2>&1 \
        || die "install_units.sh --check is red — unit/marker drift, check by hand"
    log "OK: install_units.sh --check exit 0"

    pgrep -f "scheduler.run" >/dev/null 2>&1 && die "a scheduler.run process is already running — not in HOLD, check by hand"
    log "OK: no scheduler.run process"

    "${PY}" - <<'PY' || die "keyring incomplete — the daemon's preflight would fail and loop (K1/K9)"
import sys
import keyring
need = [("trading-bot-minimax-bot", "api_key"), ("tradingbot", "anthropic_api_key"),
        ("tradingbot", "ig_demo_api_key"), ("tradingbot", "ig_demo_account_id"),
        ("tradingbot", "ig_demo_username"), ("tradingbot", "ig_demo_password")]
missing = [f"{s}/{u}" for s, u in need if not keyring.get_password(s, u)]
print("[s2-start] keyring missing: " + ", ".join(missing) if missing else "[s2-start] OK: keyring complete (6 entries)")
sys.exit(1 if missing else 0)
PY
fi

# ── Start: release hold → install → start (prereg "Start am D1-Morgen") ──────
before_lines="$( { wc -l < "${SCHED_LOG}"; } 2>/dev/null || echo 0)"
run bash "${REPO_ROOT}/scripts/install_units.sh" --release-hold || die "release-hold failed"
run bash "${REPO_ROOT}/scripts/install_units.sh" || die "install_units.sh failed"
run systemctl --user start "${UNIT}" || die "systemctl start ${UNIT} failed"

if [[ "${DRY_RUN}" == "1" ]]; then
    log "=== dry-run done === $(date -Is) — nothing was changed"
    exit 0
fi

# ── Day-0 checks that exist right after the start ───────────────────────────
start_line=""
for _ in $(seq 1 "${S2_START_POLL:-60}"); do
    start_line="$(tail -n +$((before_lines + 1)) "${SCHED_LOG}" 2>/dev/null | grep "starting scheduler daemon" | tail -1 || true)"
    [[ -n "${start_line}" ]] && break
    sleep 2
done
[[ -n "${start_line}" ]] || die "no 'starting scheduler daemon' line after the start — the daemon did not come up"
log "start line: ${start_line}"
[[ "${start_line}" == *"llm_profile=${PROFILE}"* ]] \
    || die "start line without llm_profile=${PROFILE} ⇒ K7 FAIL — the bot runs, check by hand"
log "OK: llm_profile=${PROFILE}"

[[ "${S2_PREFLIGHT_WAIT:-15}" == "0" ]] || sleep "${S2_PREFLIGHT_WAIT:-15}"
pf="$(tail -n +$((before_lines + 1)) "${SCHED_LOG}" | grep -c "preflight failed" || true)"
[[ "${pf}" == "0" ]] && log "OK: no 'preflight failed'" || log "ERROR: ${pf}x 'preflight failed' after the start (restart loop)"
log "is-active: $(systemctl --user is-active "${ALL_UNITS[@]}" 2>/dev/null | tr '\n' ' ')(4x active expected)"

# ── Aktiv-Block (before 09:00, S1 finding N1) — fail-soft ────────────────────
start_ts="${start_line:0:23}"
head_short="$(git -C "${REPO_ROOT}" rev-parse --short HEAD 2>/dev/null || echo unknown)"
open_db="$(sqlite3 "file:${DATA_DIR}/trading_bot.sqlite?mode=ro" "SELECT count(*) FROM trade_outcomes WHERE status='OPEN'" 2>/dev/null || echo "?")"
open_es="$("${PY}" -c "import json,sys; r=json.load(open(sys.argv[1])).get('records',{}); print(sum(1 for v in r.values() if v.get('status') in ('OPEN','PENDING')))" "${STATE_DIR}/execution_state.json" 2>/dev/null || echo "?")"
log "aktiv-block: start=${start_ts} head=${head_short} open(trade_outcomes)=${open_db} open/pending(execution_state)=${open_es}"
if [[ "${S2_SKIP_AKTIV:-0}" == "1" ]]; then
    log "aktiv-block: skipped (S2_SKIP_AKTIV=1) — enter it by hand from the line above"
else
    if "${PY}" - "${PREREG}" "${start_ts}" "${start_line#* INFO scheduler.run: }" "${head_short}" "${open_db}" "${open_es}" <<'PY'
import sys
from pathlib import Path
path, ts, line, head, open_db, open_es = sys.argv[1:]
p = Path(path)
s = p.read_text(encoding="utf-8")
probe = "nicht anwendbar (keine offene Position beim Start)" if (open_db, open_es) == ("0", "0") else "**anwendbar** — offene Position beim Start, Prereg (a) prüfen"
rows = {
    "| **Start** | *(einzutragen)* |": f"| **Start** | **{ts} Europe/Berlin** — `{line}` (automatischer Start, `tradingbot-s2-start.timer`) |",
    "| **HEAD-Commit beim Start** | *(einzutragen)* |": f"| **HEAD-Commit beim Start** | **`{head}`** (== origin/main, im Pre-flight geprüft) |",
    "| **Offene Position bei Start** | *(einzutragen)* |": f"| **Offene Position bei Start** | **{open_db}** (`trade_outcomes` OPEN) · **{open_es}** (`execution_state.json` OPEN/PENDING) |",
    "| **Re-Adoption-Probe** | *(einzutragen: anwendbar ja/nein)* |": f"| **Re-Adoption-Probe** | {probe} |",
}
for old, new in rows.items():
    if s.count(old) != 1:
        sys.exit(f"aktiv-block placeholder not found exactly once: {old}")
for old, new in rows.items():
    s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
PY
    then
        git -C "${REPO_ROOT}" commit -q -m "phase17: docs -- -S2 Aktiv-Block eingetragen (automatischer Start ${start_ts})" \
            -- "${PREREG}" 2>&1 | tee -a "${LOG_FILE}" >&2 \
            && log "aktiv-block: entered + committed locally ($(git -C "${REPO_ROOT}" rev-parse --short HEAD 2>/dev/null))" \
            || log "WARN: aktiv-block written but NOT committed — commit by hand"
    else
        log "WARN: aktiv-block NOT written — enter it by hand from the line above"
    fi
fi

log "=== -S2 start done === $(date -Is) — before 09:00 the bot only warms up; the first LLM record lands in llm_io.jsonl after 09:00"
