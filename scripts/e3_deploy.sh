#!/usr/bin/env bash
#
# e3_deploy.sh — Phase-17 E-3 deploy (operator path).
#
# One script for Plan §20 E-3a (steps 1–7) + Plan §22 E-22c (timing). It exists
# because the E-3 sequence has two failure modes that a human at a terminal is
# prone to:
#
#   1. The start lands AFTER 09:00 Berlin. The start-line would then sit on a
#      day that is no longer "the first full trading day after the start"
#      (Prereg BLUF) ⇒ K7-v5 fails BY CONSTRUCTION (fail-closed, no start-line
#      inside the window). The script refuses to start the scheduler in that
#      case instead of burning a window.
#   2. The data repair writes the wrong number of rows (a second run, a changed
#      live DB). The script aborts on a `changes()` mismatch instead of
#      continuing into step 5.
#
# Everything else is Plan §20 E-3a verbatim — the script is a mechanical
# transcription, not a new procedure. The runbook
# (phase17_testbed/PHASE17_E3_RUNBOOK.md) is the readable version.
#
# Usage:
#   bash scripts/e3_deploy.sh              # the deploy (stops services, repairs data, starts the bot)
#   bash scripts/e3_deploy.sh --dry-run    # print every step, touch nothing
#
# Exit codes: 0 deploy finished · 1 aborted (see the log line) · 2 usage error
#
# Environment overrides (all optional — the defaults are the live values):
#   E3_LATEST_START    local HH:MM after which the scheduler is NOT started (default 08:55)
#   E3_REPO_ROOT       repo root (default: the parent of scripts/)
#   E3_DATA_DIR        data directory (default: $E3_REPO_ROOT/data)
#   E3_EXPECT_IG       expected `changes()` of the ig-bar DELETE (default 3770)
#   E3_EXPECT_INSTINCT expected `changes()` of the instinct UPDATE (default 29)
#   E3_SKIP_PREFLIGHT  set to 1 to skip the read-only pre-flight checks
#   E3_START_POLL      tries/2s to wait for the start-line (default 60 = 120 s)
#   E3_PREFLIGHT_WAIT  seconds to wait for the pre-flight outcome (default 15)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${E3_REPO_ROOT:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
DATA_DIR="${E3_DATA_DIR:-${REPO_ROOT}/data}"
STATE_DIR="${DATA_DIR}/state"
LOG_FILE="${STATE_DIR}/e3_deploy.log"
LATEST_START="${E3_LATEST_START:-08:55}"
EXPECT_IG="${E3_EXPECT_IG:-3770}"
EXPECT_INSTINCT="${E3_EXPECT_INSTINCT:-29}"
UNITS=(tradingbot-scheduler.service tradingbot-recorder.service
       tradingbot-discovery.service tradingbot-webui.service)
PY="${REPO_ROOT}/phase1_broker_wrapper/.venv/bin/python"

DRY_RUN=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        -h|--help) sed -n '2,30p' "$0"; exit 0 ;;
        *) echo "unknown arg: ${arg}" >&2; exit 2 ;;
    esac
done

mkdir -p "${STATE_DIR}"

log() { printf '[e3-deploy] %s\n' "$*" | tee -a "${LOG_FILE}" >&2; }
die() { log "ABORT: $*"; exit 1; }

run() {
    log "\$ $*"
    [[ "${DRY_RUN}" == "1" ]] || "$@"
}

now_hm() { TZ=Europe/Berlin date +%H:%M; }

log "=== E-3 deploy gestartet === $(date -Is) (repo=${REPO_ROOT}, dry-run=${DRY_RUN})"
[[ "${DRY_RUN}" == "1" ]] || log "Log-Datei: ${LOG_FILE}"

# ── Pre-flight (read-only) ────────────────────────────────────────────────────
if [[ "${E3_SKIP_PREFLIGHT:-0}" != "1" ]]; then
    log "--- Pre-flight ---"

    git -C "${REPO_ROOT}" fetch origin main --quiet 2>/dev/null || log "WARN: git fetch fehlgeschlagen (offline?) — Vergleich nutzt den lokalen origin/main-Ref"
    head_sha="$(git -C "${REPO_ROOT}" rev-parse HEAD 2>/dev/null || echo unknown)"
    origin_sha="$(git -C "${REPO_ROOT}" rev-parse origin/main 2>/dev/null || echo unknown)"
    if [[ "${head_sha}" == "unknown" || "${origin_sha}" == "unknown" ]]; then
        log "WARN: HEAD/origin-main nicht lesbar — Drift-Check übersprungen"
    elif [[ "${head_sha}" != "${origin_sha}" ]]; then
        die "HEAD (${head_sha}) != origin/main (${origin_sha}) — der geprüfte Code-Stand ist nicht deployed (AK22 gilt für HEAD; im Fenster ist jeder Commit ein Befund)"
    else
        log "OK: HEAD == origin/main (${head_sha:0:7})"
    fi

    if bash "${REPO_ROOT}/scripts/install_units.sh" --check >/dev/null 2>&1; then
        log "OK: install_units.sh --check exit 0"
    else
        die "install_units.sh --check ist rot — Units/Marker-Drift (Plan §20 E-3e)"
    fi

    if pgrep -f "scheduler.run" >/dev/null 2>&1; then
        die "ein scheduler.run-Prozess läuft bereits — der Bot ist nicht im HOLD (Abbruch, erst prüfen)"
    fi
    log "OK: kein scheduler.run-Prozess"

    "${PY}" - <<'PY' || die "Keyring unvollständig (siehe oben) — der Preflight des Daemons würde fehlschlagen"
import sys
import keyring
need = [("trading-bot-minimax-bot", "api_key"),
        ("tradingbot", "anthropic_api_key"),
        ("tradingbot", "ig_demo_api_key"),
        ("tradingbot", "ig_demo_account_id"),
        ("tradingbot", "ig_demo_username"),
        ("tradingbot", "ig_demo_password")]
missing = []
for svc, user in need:
    try:
        ok = bool(keyring.get_password(svc, user))
    except Exception:
        ok = False
    if not ok:
        missing.append(f"{svc}/{user}")
print("[e3-deploy] Keyring fehlt: " + ", ".join(missing) if missing else "[e3-deploy] OK: Keyring vollstaendig (6 Eintraege)")
sys.exit(1 if missing else 0)
PY
fi

# ── Step 1: Hold freigeben (nur der Marker verschwindet) ──────────────────────
log "--- Schritt 1: Hold freigeben ---"
run bash "${REPO_ROOT}/scripts/install_units.sh" --release-hold

# ── Step 2: vier Dienste stoppen ─────────────────────────────────────────────
log "--- Schritt 2: Dienste stoppen (kann bis 6 min dauern — TimeoutStopSec=360) ---"
run systemctl --user stop "${UNITS[@]}"
run bash -c 'ps aux | grep -E "scheduler.run|data_foundation.run|source_registry.run|uvicorn" | grep -v grep || true'

# ── Step 3: Backups ───────────────────────────────────────────────────────────
log "--- Schritt 3: Backups ---"
STAMP="$(date +%Y%m%d)"
run cp "${DATA_DIR}/bars.sqlite" "${DATA_DIR}/bars.sqlite.bak-${STAMP}-pre-p17-igts"
run cp "${DATA_DIR}/trading_bot.sqlite" "${DATA_DIR}/trading_bot.sqlite.bak-${STAMP}-pre-p17-legacy"

# ── Step 4: Daten reparieren (T14 + T12) ─────────────────────────────────────
log "--- Schritt 4: Daten reparieren (T14 ig-Bars + T12 Instincts) ---"
if [[ "${DRY_RUN}" == "1" ]]; then
    run sqlite3 "${DATA_DIR}/bars.sqlite" "DELETE FROM bars WHERE source='ig'; SELECT changes();"
    run sqlite3 "${DATA_DIR}/trading_bot.sqlite" "UPDATE instincts SET trigger = '[legacy-p16] ' || trigger WHERE evidence_trade_ids_json IS NULL AND trigger NOT LIKE '[legacy-p16]%'; SELECT changes();"
else
    got_ig="$(sqlite3 "${DATA_DIR}/bars.sqlite" "DELETE FROM bars WHERE source='ig'; SELECT changes();")"
    [[ "${got_ig}" == "${EXPECT_IG}" ]] || die "DELETE ig-Bars: changes()=${got_ig}, erwartet ${EXPECT_IG} — Abbruch (kein Schritt 5)"
    log "OK: ig-Bars gelöscht (${got_ig})"
    got_inst="$(sqlite3 "${DATA_DIR}/trading_bot.sqlite" "UPDATE instincts SET trigger = '[legacy-p16] ' || trigger WHERE evidence_trade_ids_json IS NULL AND trigger NOT LIKE '[legacy-p16]%'; SELECT changes();")"
    [[ "${got_inst}" == "${EXPECT_INSTINCT}" ]] || die "UPDATE instincts: changes()=${got_inst}, erwartet ${EXPECT_INSTINCT} — Abbruch (kein Schritt 5)"
    log "OK: Instincts markiert (${got_inst})"
fi

# ── Step 5: Units installieren + aktivieren ──────────────────────────────────
log "--- Schritt 5: Units installieren + aktivieren ---"
run bash "${REPO_ROOT}/scripts/install_units.sh"
run systemctl --user daemon-reload

# ── Step 6: starten — mit dem 09:00-Guard ─────────────────────────────────────
log "--- Schritt 6: Dienste starten ---"
hm="$(now_hm)"
if [[ "${hm}" > "${LATEST_START}" ]]; then
    if [[ "${DRY_RUN}" == "1" ]]; then
        log "WARN (dry-run): Uhrzeit ${hm} > ${LATEST_START} — im echten Lauf wuerde der Start hier abbrechen"
    else
        die "Uhrzeit ${hm} > ${LATEST_START} — der Scheduler wird NICHT gestartet (Start-Zeile waere nicht im Fenster ⇒ K7-v5 FAIL by construction). Bitte einen frueheren Termin waehlen (D1-Definition, Prereg BLUF)."
    fi
fi
[[ "${hm}" < "${LATEST_START}" ]] && log "OK: Uhrzeit ${hm} < ${LATEST_START} (die Start-Zeile liegt im Fenster [D1, D2])"
SCHED_LOG="${STATE_DIR}/run_scheduler.log"
before_lines="$(wc -l < "${SCHED_LOG}" 2>/dev/null || echo 0)"
run systemctl --user start "${UNITS[@]}"

# ── Step 7: Startzeile + die vier sofortigen Day-0-Checks ────────────────────
if [[ "${DRY_RUN}" == "1" ]]; then
    log "--- Schritt 7: Startzeile (dry-run — es läuft nichts, es wird nichts geprüft) ---"
    log "=== E-3 dry-run beendet === $(date -Is) — es wurde NICHTS verändert"
    exit 0
fi
log "--- Schritt 7: Startzeile ---"
new_line=""
for _ in $(seq 1 "${E3_START_POLL:-60}"); do
    if [[ -f "${SCHED_LOG}" ]]; then
        new_line="$(tail -n +$((before_lines + 1)) "${SCHED_LOG}" 2>/dev/null | grep "starting scheduler daemon" | tail -1)"
        if [[ -n "${new_line}" ]]; then break; fi
    fi
    sleep 2
done
[[ -n "${new_line}" ]] || die "keine 'starting scheduler daemon'-Zeile nach $(( ${E3_START_POLL:-60} * 2 )) s — der Daemon ist nicht gestartet"
log "Startzeile: ${new_line}"
case "${new_line}" in
    *"llm_profile=research_m3"*) log "OK: Check #2 — llm_profile=research_m3 in der Startzeile" ;;
    *) die "Check #2 rot: die Startzeile traegt kein llm_profile=research_m3 ⇒ K7 FAIL (Flip 1 nicht aktiv)" ;;
esac

wait_s="${E3_PREFLIGHT_WAIT:-15}"
log "warte ${wait_s} s (Preflight-Ausgang abwarten) ..."
[[ "${wait_s}" == "0" ]] || sleep "${wait_s}"
pf="$(tail -n +$((before_lines + 1)) "${SCHED_LOG}" | grep -c "preflight failed" || true)"
if [[ "${pf}" == "0" ]]; then
    log "OK: Check #1 — kein 'preflight failed'"
else
    log "FEHLER: Check #1 — ${pf} Preflight-Fehler nach der Startzeile (Daemon laeuft nicht; Restart-Schleife)"
fi

cyc="$(grep -c "discovery cycle" "${STATE_DIR}/run_discovery.log" 2>/dev/null || echo 0)"
log "Check #5 — 'discovery cycle'-Zeilen in run_discovery.log: ${cyc} (>= 1 erwartet; der Discovery-Daemon ruft run_once() sofort beim Start)"

act="$(systemctl --user is-active "${UNITS[@]}" 2>/dev/null | tr '\n' ' ')"
log "Check #8 — is-active: ${act} (4x 'active' erwartet)"

log "=== E-3 deploy beendet === $(date -Is)"
log "Noetig bis 09:00 (erster WINDOW-Zyklus): Checks #3 (Research-Call auf MiniMax-M3), #4 (IG-Bar-Zeitstempel), #6 (abstain_record_id), #7 (IG-Allowance) — die Kommandos stehen im Runbook §3."
log "Aktiv-Block der Vorregistrierung eintragen (Runbook §4): Start-Zeitstempel · D1 · D2 · HEAD · offene Position."
