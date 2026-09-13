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
updated: 2026-09-13 (+ Exec-Session #31: **Mini-Session „Wrapper-Skript-Fix Drift #8 Root Cause"** [4 Commits `5cd9168` + `cc73462` + `774a3e1` + `9c323e3`; 3 Wrapper-Skript-Edits (phase8_scheduler/scripts/run_webui.sh + phase12_data_foundation/scripts/run_recorder.sh + phase14_discovery/scripts/run_discovery.sh) mit `date '+%Y-%m-%d %H:%M:%S'`-Prefix; 3 neue Test-K1-Pin-Tests (in-window / out-of-window / mixed); Σ 1945 → **1948** exakt am F-Exec-Plan-Akzeptanz-Muster; v3-§11-Drift-#8-Fix-Marker **nicht** in v3 (Locked-Regel) — Drift-#8-Fix stattdessen im Phasenkopf dokumentiert; `bash -n` für jeden Wrapper exit 0; `pytest phase16_activation/tests/test_autonomy_report.py` 10/10 grün; `check_doc_rotation.py --strict --quiet` exit 0]). — Vorheriger Stand: Exec-Session #30: **Quick-Session: 3 nicht-zeit-blockierte Items abgehakt**

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
