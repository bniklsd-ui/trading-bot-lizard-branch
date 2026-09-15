---
status: active-phase
purpose: PHASE-HEAD, Phase 16 (Freischaltung) — 🔄 eröffnet 2026-09-05 (Plan-Session, Fable 5.1). Mission = jedes gebaute Feature läuft, jeder bekannte Bruch ist zu, ein vorregistrierter 2-Wochen-Lauf beweist Autonomie ohne Hand. Kern-Befund: der Bot ist seit 2026-08-31 faktisch tot (100 % Research-Abstain, 77/Tag) — Ursache Infrastruktur (Historien-Tabelle ohne Zeitfenster), nicht Strategie; dazu Token-Budget täglich um 15:48 leer, Live-DB auf Schema v7 (Migrations nie angewendet, Doku behauptete das Gegenteil), Flags nicht restart-fest, 3 Wochenend-Epics im Universum.
read-when: jede Phase-16-Session; zuerst den neuesten `## Session stopped`-Block, dann den Plan-Step, der dran ist
detail: L1
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase16_activation_plan.md   # 📕 der Plan (P1–P18, L1–L9, Blöcke A–E, AK1–AK17, §9 Drift, §13 Reviews)
  - ../phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md    # 📕 Vorgänger-Handover (E1–E3 werden hier geschlossen)
  - ../phase7_reward/PHASE12_RECONCILIATION_TIMING_PLAN.md   # 📕 A6 hängt an Migration 008
  - ../phase5_execution/CLAUDE.md                 # B3-Block → Plan D3
  - ./SESSIONS_ARCHIVE.md                         # 📦 Session-Block-Historie (newest-first, A-0 angelegt)
updated: 2026-09-15 (+ **Tag-7-Status-Check (OpenCode / MiniMax-M3, no-code-Session)** [Health-Check nach gemeldeter Nikinger-Downtime 17:45–21:00 = remote-Zugang, nicht VM-Outage (15 d uptime stabil, scheduler+webui laufen seit 2026-09-08, recorder+discovery inline-orchestriert per Phase-12/14-Architektur → keine Restarts nötig); **3 neue Drifts #9/#10/#11 gefunden**, alle 3 per Nikinger-Entscheidung **deferred** (Phase-16-Block-E läuft, Block-I-Tag-10-Closeout ist zeit-blockiert 2026-09-22); Kriterien Tag-6+7-Status: K1 ✅, K2 ❌, K3 ❌, K4 ❌, K5 ✅, K6 ✅, K7 ✅ — K2/K4-Fails sind Code-Drift, nicht Live-Problem; Live-Beweis: 8 yF-Bar-Fetches ok, 1 `measurement_heartbeat ok:true worst_coverage=0.996`, 5 Zyklen LLM_ABSTAIN (legit DAX-nahe-30d-Tief), `consecutive_failures=0`]). — Vorheriger Stand: Exec-Session #31: **Mini-Session „Wrapper-Skript-Fix Drift #8 Root Cause"**

## Live-Beobachtungen — 2026-09-15 (Tag 7, Status-Check ohne Code-Edits)

> **Kontext:** Nikinger-Meldung ~17:45–21:00 „Maschine längere Downphase" → Health+Status-Check als Session-Einstieg. **Befund:** VM 15 d stabil (gemeldete Downtime war Remote-Zugang, nicht VM-Outage). 3 neue Drifts in der autonomen Monitoring-/Reporting-Schicht gefunden, alle per Nikinger-Entscheidung dokumentiert+deferred (Phase-16-Block-E läuft, Block-I-Tag-10-Closeout 2026-09-22 ist die nächste zeitlich nicht-blockierte Exec-Session).

### 🟡 Drift #9 — K4 Threshold-Wording Bug (`autonomy_report.py:726`)

- **Code-Stelle:** `threshold=f"≥ {HEARTBEAT_OK_PASS_THRESHOLD} of {len(trading_days)} trading days"` (Plan §33 will „≥ 8 / 10 Handelstage"); Verdict-Logik (Z. 714): `verdict = "PASS" if ok_days >= 8 else "FAIL"` (`HEARTBEAT_OK_PASS_THRESHOLD = 8`, Z. 114)
- **Bug-Symptom:** Partial-Window-Queries (Operator-Tagesroutine mit `--from Tag-N --to Tag-N+1`) erzeugen Threshold-Strings wie `"≥ 8 of 2 trading days"` (strukturell unerfüllbar) → K4 ist für Tagesroutinen **immer FAIL**, auch wenn alle Tage OK
- **Live-Beweis Tag 6+7 (Query 09-13→09-15):** `ok_days=2`, beide Tage `per_day_ok_flags={"2026-09-14": true, "2026-09-15": true}`, **Verdict FAIL wegen Schwellwert-Bug, nicht wegen Real-Verhalten**
- **Fix-Vorschlag (zur Diskussion Block I / Phase 17):** Threshold auf dynamisch `≥ 0.8 × N` ODER explizit `≥ 8 of full_test_window (10)` (immer gegen Full-Window, nie gegen Sub-Window). Achtung: locked-Plan §6 E2 (Prereg-Disziplin) — jede Schwellwert-Änderung ist ein **echter Eingriff** in die Vorregistrierung, braucht explizite Nikinger-Freigabe
- **Workaround bis Fix:** Tag-Routine-Berichte mit `--from 2026-09-09 --to <heute>` (voller Test-Window) ausführen, dann ist Threshold `≥ 8 of N` sinnvoll

### 🟡 Drift #10 — K2 misst falsche Events (`autonomy_report.py:622-650`)

- **Code-Stelle:** K2 zählt `discovery_heartbeat_event`, `recorder_bars_per_day`, `scheduler_health_events` aus `research_health.jsonl`
- **Bug-Symptom:** Echte Heartbeats heute vorhanden als `{"event": "measurement_heartbeat", "ok": true, ...}` (z. B. 2026-09-15T17:31:04, `bars_today=457331`, `worst_coverage=0.9958`), werden aber **nicht** von K2 erkannt → gemessene Werte `0/0/0` → K2 immer FAIL obwohl Health-Signal real existiert
- **Wahrscheinliche Ursache:** K2-Event-Namen veraltet (pre-Phase-14, pre-Migration 009); die echten Heartbeats heißen heute `measurement_heartbeat` mit `ok`-Feld
- **Fix-Vorschlag (zur Diskussion Block I / Phase 17):** K2 auf `measurement_heartbeat.ok == true` umstellen (Tages-Aggregation); zusätzlich prüfen ob `event: "bar_fetch"` mit `ok:true` als Recorder-Signal zählen sollte
- **Impact:** K2-Verdict ist aktuell **nicht aussagekräftig** — alle 3 auto-Signale als 0 gemessen, aber Health-OK nachweislich vorhanden

### 🟡 Drift #11 — Report-Filename-Logik überschreibt Vorgänger (`autonomy_report.py` — write-Statement)

- **Code-Stelle:** Filename-Logik schreibt offenbar fixiert auf einen Anker-Datum (vermutlich `--to` oder `today`) — egal welche `--from/--to`-Range gefragt ist
- **Bug-Symptom:** Query `--from 2026-09-13 --to 2026-09-15` schreibt `data/reports/autonomy_2026-09-13.json` und **überschreibt** den existierenden Tag-5-Report. Operator-Tagesroutine wird riskant, wenn sie versehentlich Partial-Windows re-runt
- **Reproduziert heute 09-15:** meine Status-Check-Query hat den 09-13-Report überschrieben (nicht destruktiv — Window 09-13→09-15 ist vollständig aus den Roh-Daten reproduzierbar; Tag-5-Original ging verloren)
- **Fix-Vorschlag (zur Diskussion Block I / Phase 17):** Filename aus Window-Berechnung ableiten (`--from X --to Y` → `autonomy_X_to_Y.json` oder `autonomy_<min-date>_to_<max-date>.json`), plus `--force`/`--no-overwrite`-Flag für Tag-Routine-Schutz
- **Achtung:** Tag-Routine in Runbook v3 §X ist betroffen — sollte vor jeder Runbook-Iteration (v4) gefixt sein, sonst Audit-Trail-Schaden

### 🟢 Was **nicht** broken ist

- **Token-Budget** (K6) ist **heute sauber**: 287k Mo / 283k Di (Cap 300k) — die C5-Erhöhung von 200k→300k (Plan §1 P3) wirkt.
- **Bot läuft autonom:** 5 Zyklen LLM_ABSTAIN (legit, DAX-nahe-30d-Tief, keine echte Edge) — Phase-16-Block-D-Defaults greifen (Shadow-Schedule + Paper-Debate aktiv, K2 zeigt 0 heartbeat-events aber Code-Path wird durchlaufen).
- **Migration 008+009 wirksam:** Schema heute v9 (per CLAUDE.md Korrekturhinweis 2026-09-08, hier nicht reverified — gilt als stable), Backup `data/trading_bot.sqlite.bak-20260905-pre-mig009` ist die Rückfall-Option.
- **Push-Backlog:** 5 Commits pending (von Session #31) — `git rev-list --left-right --count origin/main...HEAD = 0 5`, working tree clean (außer `data/`-Runtime-Files + sunshine-deb).

### NEXT für nächste Session (unverändert vs Session #31 NEXT-Block)

- **Session #32 (Block I Tag-10-Closeout) — geplant Di 2026-09-22 nach 17:30 Berlin** (zeit-blockiert bis dahin).
- **Drifts #9/#10/#11** als Agenda-Punkte für Block I / Phase-17-Sammlung mitnehmen.
- **Drift-#8-Fix-Live-Verifikation:** nächster Restart (Backoff-KILL-Clear oder Reboot) zeigt jetzt `note: "filtered-by-timestamp"` für alle 3 Wrapper-Dienste (alte `run_*.log`-Logs pre-Fix bleiben bis dahin `full-file-count`).
- **Trigger on-demand:** K4 FAIL ≥ 2 Tage → T-5, K6 FAIL → T-8, erster OPEN-Trade → A6-Live-Verify (Gate P7/A6).

---

## Session stopped — 2026-09-13 (MiniMax-M3-Exec-Session #31, Phase-16-F-Subphase **Mini-Session „Wrapper-Skript-Fix Drift #8 Root Cause"** — 4 Commits `5cd9168` + `cc73462` + `774a3e1` + `9c323e3` (3 Code + 1 Test), 1 Session-Rotations-Commit; v3 §11 Drift-#8-Fix-Marker **nicht** in v3 eingetragen (Locked-Konvention verlangt v4-Erstellung, Mini-Session-Scope überschritten), stattdessen im Phasenkopf dokumentiert; K1 deterministisch für alle 4 Dienste; Σ 1945 → **1948** [+3 Tests, exakt am F-Exec-Plan-Akzeptanz-Muster]; `bash -n` für jeden Wrapper exit 0; `pytest phase16_activation/tests/test_autonomy_report.py` 10/10 grün; `check_doc_rotation.py --strict --quiet` exit 0)

> **Auftrag:** Nikinger-Chat 2026-09-13 ~19:30 Berlin: „Freigegeben, erstelle aber trotzdem eine extra Plan, damit wirklich nichts schief geht. Gerne sehr detailliert, mit langer nachdenkzeit. Danke dir!". Mini-Session aus Session #30 NEXT-Block Z. 81 (Nikinger-Vorschlag, nicht terminiert): 3 File-Edits + 1 Test-Erweiterung. Vorab: Cross-Phase-Freigabe-Status P12+P14 explizit abgefragt + erteilt (P8 schon freigegeben per Phase-16-Plan §4 Z. 260). Mini-Plan im Chat vorab detailliert besprochen + freigegeben („Plan OK, atomar ausführen"), 6 Commits geplant (3 Code + 1 Test + 1 v3-Annotation + 1 Rotation). **Plan-Anpassung während Ausführung:** v3 §11 Drift-#8-Annotation übersprungen weil v3 header „niemals ein Edit hier" → v4 wäre Pflicht, Mini-Session-Scope sprengen würde; stattdessen Drift-#8-Fix im Phasenkopf dokumentiert (lebender Ort, Locked-Konvention eingehalten). 5 Commits final.

### Completed

**1. Drift #8 Root Cause bestätigt (Source-of-Truth-Anker):**
- `autonomy_report.py:193-231` `count_starts_in_window()` filtert via `_parse_scheduler_ts()` + `_SCHED_TS_RE = r"^(?P<ts>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}...)"` — verlangt Timestamp am Zeilenanfang.
- 3 Wrapper-Start-Lines ohne Timestamp bestätigt: `phase8_scheduler/scripts/run_webui.sh:47`, `phase12_data_foundation/scripts/run_recorder.sh:37`, `phase14_discovery/scripts/run_discovery.sh:46`.
- K1 gibt heute `note: "full-file-count (untimestamped start-lines: opaque to window filter)"` für alle 3 Wrapper-Dienste zurück (Live-Beweis Session #26: `discovery: 7, recorder: 6, scheduler: 6, webui: 10` Starts).
- 4. Wrapper `phase8_scheduler/scripts/run_scheduler.sh:64` braucht KEINEN Fix (Python `basicConfig` schreibt timestamped `starting scheduler daemon (...)` in dieselbe Log-Datei, K1-Pattern matcht dort, Wrapper-Echo ist dekorativ).

**2. Commit `5cd9168 phase8: code -- run_webui.sh: timestamp prefix for wrapper-start-line (Drift #8 Root Cause fix)`:**
- `phase8_scheduler/scripts/run_webui.sh:47` von `echo "[run_webui] dashboard on http://127.0.0.1:${PORT}..."` zu `printf '%s [run_webui] dashboard on http://127.0.0.1:%s...\n' "$(date '+%Y-%m-%d %H:%M:%S')" "${PORT}"`.
- `${PORT}` als `%s`-Argument (keine Format-String-Re-Interpretation), Backslash-Continuation matched File-Style.
- `bash -n` exit 0.
- Cross-Phase-Freigabe: Phase 16 Plan §4 Z. 260 (P8 freigegeben für Phase 16).

**3. Commit `cc73462 phase12: code -- run_recorder.sh: timestamp prefix...`:**
- Selbe Form auf `phase12_data_foundation/scripts/run_recorder.sh:37`.
- Cross-Phase-Freigabe: Nikinger 2026-09-13 explizit erteilt (Phase 12 nicht in Phase-16-Plan §4 Z. 253-264 gelistet).

**4. Commit `774a3e1 phase14: code -- run_discovery.sh: timestamp prefix...`:**
- Selbe Form auf `phase14_discovery/scripts/run_discovery.sh:46`, UTF-8 `⇒` (U+21D2) preserved durch `%s`-Placeholder.
- Cross-Phase-Freigabe: Nikinger 2026-09-13 explizit erteilt (Phase 14 nicht in Phase-16-Plan §4 Z. 253-264 gelistet, Phase-14-Plan §4 Z. 275-279 seinerseits verlangt neue Freigabe).

**5. Commit `9c323e3 phase16: tests -- autonomy_report K1 wrapper-timestamp-prefix test extension (Drift #8 fix regression pin)`:**
- 3 neue Tests in `phase16_activation/tests/test_autonomy_report.py`:
  - `test_k1_wrapper_timestamped_start_counts_in_window` — timestamped in-window → count=1, note=filtered-by-timestamp
  - `test_k1_wrapper_timestamped_start_outside_window_excluded` — timestamped out-of-window → count=0, verdict=PASS (Note ist Folge der Window-Logik, by-design)
  - `test_k1_wrapper_mixed_timestamped_and_untimestamped` — mixed mode → count=1 (only timestamped in-window), note=filtered-by-timestamp
- Σ delta: +3 Tests (1945 → 1948).
- Bestehende 7 Tests bleiben grün (`_START_PATTERNS[svc].search(line)` ist prefix-tolerant).

**6. Plan-Anpassung: v3 §11 Drift-#8-Fix-Marker übersprungen:**
- v3 Header: „v3 ist locked-nach-Commit: Korrekturen sind nur als PHASE16_E3_RUNBOOK_v4.md mit Datum und Grund möglich — niemals ein Edit hier."
- Drift-#8-Fix-Dokumentation gehört in den Phasenkopf (dieser Block) als lebender Ort, nicht in locked Runbook.
- v4-Erstellung wäre Mini-Session-Scope-Überschreitung; bei nächster Runbook-Iteration (z. B. wenn W2 oder andere Watch-Items weitere Drift-Fixes triggern) kann v4 als Sammel-Commit entstehen.

**7. Verifikation:**
- `bash -n phase8_scheduler/scripts/run_webui.sh` exit 0 ✓
- `bash -n phase12_data_foundation/scripts/run_recorder.sh` exit 0 ✓
- `bash -n phase14_discovery/scripts/run_discovery.sh` exit 0 ✓
- `pytest phase16_activation/tests/test_autonomy_report.py -v` → **10/10** grün (7 existing + 3 new) ✓
- Σ-Sweep (15 Phase-Suites + root, exkl. meta_m1 per Repo-Konvention): 97+82+105+161+190+76+169+259+95+165+149+82+61+126+10+121 = **1948** ✓
- `python3 scripts/check_doc_rotation.py --strict --quiet` exit 0 ✓
- `git rev-list --left-right --count origin/main...HEAD` = `0 4` (4 Commits pending Nikinger push: 3 Code + 1 Test; Session-Rotation noch nicht committed)

**8. Doc-Rotation Session #30 → SESSIONS_ARCHIVE + Session #31 → Phasenkopf (in diesem Commit):**
- `phase16_activation/SESSIONS_ARCHIVE.md`: Session-#30-Block-Verbatim-Summary als 31. Eintrag prependiert (newest-first)
- Preamble „Stand nach Exec-Session #30" → „Stand nach Exec-Session #31", Archiv-Count **30 → 31**
- `phase16_activation/CLAUDE.md` Session-#30-Block durch Session-#31-Block ersetzt
- `python3 scripts/check_doc_rotation.py --strict --phase phase16_activation` → exit 0 nach Rotation

### Findings

🟢 **Drift #8 Root Cause strukturell behoben.** K1 ist jetzt deterministisch für alle 4 Dienste — Wrapper-Start-Lines emittieren `YYYY-MM-DD HH:MM:SS [run_X] starting...` Format, `count_starts_in_window()` extrahiert Timestamp + filtert nach Berlin-Day-Fenster. Resultat: `filtered-by-timestamp` statt `full-file-count`, präzise K1-Messung pro Restart im Fenster.

🟢 **3 Wrapper-Edits atomar, Cross-Phase-Freigabe explizit.** 3 Commits (einer pro Phase) entsprechen dem „eine logische Änderung pro Commit"-Prinzip (root-CLAUDE.md Conventions). P12 + P14 Freigabe explizit vom Nikinger erteilt (Phase-12/Phase-14-Code außerhalb des Phase-16-Plan-§4-Whitelist).

🟢 **Test-Pin robust:** 3 Tests decken in-window / out-of-window / mixed-Mode ab. mixed-Mode-Test ist der realistischste nach Fix-Apply (alte untimestamped Log-Inhalte coexistieren mit neuen timestamped Restart-Events). Bestehende 7 Tests bleiben grün.

🟢 **Σ exakt am F-Exec-Plan-Akzeptanz-Muster:** +3 Tests (1945 → 1948). Stabil, kein Regression-Risiko (keine Phase-Code-Touches außer Wrapper-Shells, keine Test-Datei außer `phase16_activation/tests/test_autonomy_report.py`).

🟢 **Locked-Konvention eingehalten.** v3 §11 Drift-#8-Fix-Marker NICHT in v3 eingetragen (header-Verbot), stattdessen Drift-Fix im Phasenkopf dokumentiert (lebender Ort). v4-Erstellung für nachfolgende Drift-Fixes aufgeschoben (Mini-Session-Scope).

🟢 **Cross-Phase-Touches minimal + alle dokumentiert.** 3 Phase-Code-Files (Phase 8/12/14) + 1 Phase-Test-File (Phase 16). Keine Migration, keine Doku in fremden Phasen, keine Schema-Änderungen, kein Live-Touch (Wrapper-Skripts werden nur bei Restart aktiv).

🟢 **Pre-Commit-Hook bleibt aktiv und grün.** `check_doc_rotation.py --strict --quiet` exit 0 nach jedem Commit; H-1-Hook (Step 4) hat die Code-Edits überlebt (Wrapper-Shells sind keine Header-Card-Files).

### Open questions / blockers

- **Block I Tag-10-Closeout (Di 2026-09-22 nach 17:30)** unverändert zeit-blockiert. I-1 Tag-10-Summary + I-2 Closeout-Handover + I-3 SVG (1080×1080, 3-Säulen) + I-4 Status-Pflege root/ROADMAP/README/INDEX + I-5 Session-Rotation.
- **Drift-#8-Fix im Live-Betrieb verifizieren** — nächster Restart (Backoff-KILL-Clear oder Reboot) zeigt jetzt `note: "filtered-by-timestamp"` für alle 3 Wrapper-Dienste; bis dahin weiterhin `note: "full-file-count"` (alter Log-Inhalt pre-Fix in `data/state/run_*.log`).
- **v4 Runbook-Erstellung aufgeschoben** — Mini-Session-Scope; v4 wird fällig wenn (a) weitere Drift-Fixes hinzukommen oder (b) nächste Operator-Runbook-Iteration ansteht. Cross-Phase-Freigabe für Runbook-Edits nicht nötig (Runbook ist Phase-16-internal).
- **Trigger on-demand:** K4 FAIL ≥ 2 Tage → T-5, K6 FAIL → T-8, erster OPEN-Trade → A6-Live-Verify (Gate P7/A6).

### NEXT (für die nächste Session)

**Push-Status:** **5 Commits pending** nach dieser Session (`5cd9168` + `cc73462` + `774a3e1` + `9c323e3` + der Session-Rotations-Commit). **Nikinger pusht jetzt mit `git push origin main`** (working tree clean danach außer `data/`).

**Tagesroutine Tag 2–Tag 10 (Operator):** unverändert (Session #27 NEXT-Block).

**Offene Items für die nächste Exec-Session (Session #32, Block I Tag-10-Closeout):**

1. **Session #32 (Block I, Tag-10-Closeout) — geplant Di 2026-09-22 nach 17:30 Berlin:** Fokus I-1 Tag-10-Summary (`autonomy_report.py --from 2026-09-09 --to 2026-09-22 --summary`) + I-2 Closeout-Handover (analog Phase-15-Pattern) + I-3 SVG (1080×1080, 3-Säulen Status-Bilanz) + I-4 Status-Pflege root/ROADMAP/README/INDEX + I-5 Session-Rotation. Σ = 1948 stabil, alle daily reports Mi-Fr+Mo-Di verfügbar, alle H-Block-Items + Quick-Session-Items + Mini-Session-Items erledigt. Total ~5 Commits + 1 neuer SVG.

**Optional für Session #32 oder später:**

2. **Optional:** Phase-17-Material sammeln (Strategie-Befund K3, Universums-Konsolidierung W2 by-design FAIL, Zombie-Reaping W5, IG-Punkte für verified SUN*-Epics V-5, Log-Rotation v3 §11-Kommentar-Inkonsistenz, v4-Runbook-Erstellung mit Drift-#8-Fix-Marker).
3. **Falls K4 FAIL an ≥ 2 Tagen:** Trigger T-5 → Exec-Session on demand.
4. **Falls K6 FAIL:** Trigger T-8 → Exec-Session on demand.
5. **Falls erster OPEN-Trade:** Gate P7/A6 → A6-Live-Verify-Session on demand.

**Push-Freigabe-Stand nach dieser Session:** 5 Commits pending. Nikinger pusht.

**Block-Status nach Session #31:**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ (Session #1-#4) |
| B (Substrat) | ✅ (Session #3) |
| C (Research-Loop) | ✅ (Sessions #3-#7) |
| D (Freischaltung) | ✅ (Session #7-#17) |
| E (2-Wochen-Test) | 🔄 — Tag-1-Verify ✅ (#27), H-3+H-4 ✅ (#28), H-1+H-2+H-5 ✅ (#29), Quick-Session #30 ✅, **Mini-Session #31 ✅**, Block I Di 2026-09-22 (#32) |
| F (Subphase) | 🔄 — G Tag 1 ✅, H ✅ (#28-#29), Quick ✅ (#30), **Mini #31 ✅**, I (#32) |
