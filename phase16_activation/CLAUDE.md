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
updated: 2026-09-08 (+ Exec-Session #25: **Drift #7 Fix — Runbook v3 NEU** [locked-nach-Commit-Disziplin für Operator-Runbook analog v1→v2, jetzt v2→v3; 1 Drift in v2-§2.3-Keyring-Snippet live gefunden 2026-09-08 Abend (`cst`/`demo_token`/`token` existieren NICHT in `broker_wrapper/credentials.py`); Fix: `store_credential.py --status` als kanonischer Check + optionaler 8-Zeichen-Fingerprint mit `IG_DEMO_*`-Namen; v3 NEU 552 LOC +50 vs v2; Live-Bestätigung 2026-09-08 Abend: alle 4 `ig_demo_*` = ✓, alle 4 `ig_*` (Live) = ✗; SESSIONS_ARCHIVE Z. 1378 hatte den Drift bereits 2026-09-07 als nicht-blockierend vermerkt, jetzt endgültig gefixt], Σ **1940 unverändert** [kein Test-Touch, kein Code-Touch, alle 4 J-Block-Fixes aus #22 + 4 Phase-16-J-Defekte-Fixes aus #22 weiterhin grün], 0 Commits pending außer dem hier, Restart-Sequenz entblockiert). — Vorheriger Stand: Exec-Session #24: **Pre-Flight + Verify** [read-only V-Checks gegen F-Exec-Plan §6 + Runbook-v2-§1-§11 gegen Code verifiziert + Block-H-Pattern-Tabelle 1:1 gegen Code abgeglichen, V-7 obsolet, V-8 🟡 Body-Link-Drift notiert für Block H, 12 Beleg-Checks ✅, Σ 1940 unverändert, 0 Commits pending]; Exec-Session #23: **Doc-Drift-Repair** [D1 Schema v7→v9, D2 Ledger-Restore, D3 Push-Freigabe erteilt, 5 datierte 🟡-Korrekturhinweise in 5 Dateien]; Exec-Session #22: **Phase-16-F-Subphase Block J** [drei Struktur-Defekte alle drei gefixt, Σ 1934 → 1940, 5 Atomic Commits, Nikinger-Sonderauftrag „J0 ist deine Aktion"]; Plan-Session #21: **`PHASE16_F_EXEC_PLAN.md` NEU** [611 LOC, Blöcke J/H/G/I, Nikinger-Entscheidung Variante A, Σ-Regression-Baseline 1934, Lock F3 revidiert)

## Session stopped — 2026-09-08 (MiniMax-M3-Exec-Session #25, Phase-16-F-Subphase **Drift #7 Fix — Runbook v3 NEU** — locked-nach-Commit Disziplin für Operator-Runbook analog v1→v2, diesmal v2→v3; 1 Drift live gefunden in v2-§2.3-Keyring-Snippet, gefixt via `store_credential.py --status` als kanonischer Check; Σ 1940 unverändert, 0 Commits pending außer dem hier)

> **Auftrag:** Nikinger-Chat 2026-09-08 (Folgesession #24, gegen 22:00 Berlin): „habe ich ausgeführt, selber Fehler. im Session archive solltest du eine nicht so lange her datierte Notiz finden, die dieses Problem bereits schon mal hatte." — Auf den Drift #7-Hinweis in SESSIONS_ARCHIVE.md Z. 1378 (gefunden in Session-#13-Pre-Flight, damals als nicht-blockierend notiert) hin wurde verifiziert: v2-§2.3-Snippet fragt nach `cst`/`demo_token`/`token` (existieren NICHT in `broker_wrapper/credentials.py`), echte Keyring-Namen sind `ig_*` (Live) und `ig_demo_*` (Demo), Status auslesbar via `store_credential.py --status`. Nikinger bestätigt: alle 4 Demo-Credentials = ✓, alle 4 Live = ✗ (Hard Rule 4: Demo-only, korrekt). Drift-Status: **gefixt in v3 (locked-nach-Commit)**. Restart-Sequenz kann mit korrigiertem Wissen weitergehen.

### Completed

**1. Drift #7 Diagnose (SESSIONS_ARCHIVE Z. 1378 reproduziert):**
- v2-§2.3-Snippet `get_credential('cst')` → `CredentialNotFoundError: 'cst' not found`
- Echte Keyring-Namen: `ig_username`/`ig_password`/`ig_api_key`/`ig_account_id` (Live, sollten alle ✗ sein per Hard Rule 4) + `ig_demo_username`/`ig_demo_password`/`ig_demo_api_key`/`ig_demo_account_id` (Demo, sollten alle ✓ sein)
- Status-Check via `phase1_broker_wrapper/.venv/bin/python phase1_broker_wrapper/scripts/store_credential.py --status`:
  ```
  Credential status (✓ = set, ✗ = not set):
    ✗  ig_username           ✗  ig_password
    ✗  ig_api_key            ✗  ig_account_id
    ✓  ig_demo_username      ✓  ig_demo_password
    ✓  ig_demo_api_key       ✓  ig_demo_account_id
  ```
- Drift war seit Session-#13-Pre-Flight (2026-09-07) als nicht-blockierend notiert (Credentials tatsächlich da, Snippet schlug mit `CredentialNotFoundError: 'cst' not found` fehl — leicht als Snippet-Bug diagnostizierbar). In Session #24 heute Abend live reproduziert beim ersten §2.3-Versuch.

**2. v3 NEU erstellt (locked-nach-Commit, 552 LOC, +50 vs v2):**
- `phase16_activation/PHASE16_E3_RUNBOOK_v3.md` — v2 + Drift-#7-Fix in §2.3 + §11 Diff-Tabelle
- §2.3-Block komplett ersetzt: neuer `store_credential.py --status` als kanonischer Check (zeigt nur ✓/✗, keine Werte) + optionaler 8-Zeichen-Fingerprint mit `IG_DEMO_USERNAME`/`IG_DEMO_PASSWORD`/`IG_DEMO_API_KEY`/`IG_DEMO_ACCOUNT_ID`-Namen (Hard Rule 1: kein Volltext, niemals in Datei/Log)
- §11 Diff-Tabelle um Drift #7 erweitert (v2→v2.1-fix-Zeile)
- YAML-Header aktualisiert: v3, supersedet v2, locked-nach-Commit-Disziplin dokumentiert
- v2-Intro als „Was v2 anders macht als v1 (von v2 geerbt)" in v3-Header eingebettet (vollständige Audit-Kette v1 → v2 → v3 im selben Dokument)

**3. INDEX.md aktualisiert:**
- v2-Zeile: „(supersedet v1, jetzt selbst superseded durch v3)" + historischer Audit-Stand
- v3-Zeile NEU: aktive Quelle der Wahrheit, mit Drift-#7-Historie + Live-Bestätigung 2026-09-08 Abend

**4. Σ-Reverification:** 16 Suites, Σ = **1940** unverändert (kein Test-Touch, kein Code-Touch)
- Hook-Verify: `check_doc_rotation.py --strict --quiet` exit 0, Phase 16 = 1 block

### Findings

🟢 **Drift #7 erfolgreich gefixt.** v2-§2.3-Snippet war der einzige Drift in v2 (sonst 6 Drifts in v1→v2). v3 schließt die Klasse endgültig — der nächste Operator (oder Nikinger selbst beim nächsten Restart nach dem 2-Wochen-Lauf) bekommt den korrekten `store_credential.py --status`-Check als erstes zu sehen.

🟢 **Source-of-truth precedence gewahrt:** Code (Keyring-Namen) → Doku (v3) → Operator (du). Live-Bestätigung 2026-09-08 Abend beweist: alle 4 Demo-Credentials da, alle 4 Live leer (Hard Rule 4 eingehalten).

🟢 **Locked-nach-Commit-Disziplin eingehalten:** v2 zu editieren wäre Verstoß gegen Z. 25-27 der v2-Header-Disziplin. v3 NEU ist die saubere Form (analog v1→v2, dokumentiert im v2-§11 Diff-Tabelle als 6+1 Korrekturen).

🟢 **Restart-Sequenz entblockiert.** Mit dem korrigierten Wissen (Status-Check statt Snippet) kann Nikinger jetzt §2.3 als PASS markieren und mit §2.4-§3 (Truncate + Prereg-Aktiv-Block + Restart) fortfahren.

### Open questions / blockers

- **Keine Session-#25-Blocker.** Drift #7 ist gefixt, v3 ist locked, Status-Check bestätigt alle Demo-Credentials. J4-J6 (Truncate + Prereg + Restart) kann jetzt durchgeführt werden.
- **V-8 Body-Link-Drift (Phase-13-Plan-Beweiswoche Z. 298) bleibt für Block H (Wochenende 13.-14. Sept. 2026) offen** — Nikinger hat sich in Session #24 für Option A entschieden (sed global, Z. 298 als Side-Effect-Fix in H-3-Commit-Body dokumentieren).

### NEXT (für die nächste Session / nach J4-J6 + J7)

**Push-Status (post-push 2026-09-08):** `git rev-list --left-right --count origin/main...HEAD` = `0 0` (vor dieser Session-#25-Commit). Diese Session: 1 Commit pending (v3 + INDEX + Rotation). Nikinger pusht bei nächster Gelegenheit.

**Offene Items für die nächste Session (Exec-Session #26, on demand nach J4-J6 + J7):**

1. **J4 + J6 + Aktiv-Block heute Abend / morgen früh** (verbatim aus v3 §1-§3): Pflicht-SQL §1 (No-Op, 0 SUN*-Epics in active) → §2.1-§2.5 Pre-Flight (5 Schritte, alle gegen aktuellen Code geprüft) → §2.6 Prereg-Aktiv-Block-Eintragung + Commit `phase16: docs -- E1-Aktiv-Block-Eintragung` (Commit-Zeit < erste Start-Zeile, AK13) → §3 Restart mit korrigiertem Caps-Pin-Kommando `grep "starting scheduler daemon" data/state/run_scheduler.log | tail -1`.
2. **J7 Tag-1-Live-Verifikation** (Exec-Session on demand): AK-J1 `bars.source='ls'` > 0 (frühestens 09:10 Berlin morgen) · AK-J2 0 ProgrammingError · AK-J3 K1 = 1 Start/Dienst · AK-J4 `measurement_heartbeat.ok == true` 17:00 Berlin. Bei K4-FAIL: V-4 `heartbeat.py:142` `pairs_resolved==0` prüfen.
3. **G + I**: G1 ab Tag 1 (`autonomy_report.py --day` täglich) · G2 Caps-Pin (grep) · I-2+I-3 Tag-10-Closeout Mo 2026-09-21 nach 17:30.
4. **Block H Wochenende 13.-14. Sept.**: H-3 (Sammel-Reparatur Pattern A-E) Sa 13. · H-4 (Phase-14-Archiv-Move) Sa 13. · H-2 (INDEX-Scope) Sa 13. · H-1 (Hook Step 4) So 14. NACH H-3/H-4 (Lock H2) · H-5 (Verifikation). **Lock F5:** Code-Edits außerhalb Trade-Fenster. **V-8-Drift (PHASE13_BEWEISWOCHE Z. 298):** Sed-Side-Effect-Fix in H-3-Commit-Body dokumentieren (Option A).
5. **Phase-15-Folge-Punkte**: Promotion-Bridge ✅ · Ledger-Restore ✅ · Migration 008+009 ✅ · Gate P7/A6 ⏳.
6. **Push-Freigabe-Stand:** 2 Commits pending nach dieser Session (#24 + #25). Nikinger pusht.

**Block-Status nach Session #25:**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ (Session #1-#4) |
| B (Substrat) | ✅ (Session #3) |
| C (Research-Loop) | ✅ (Sessions #3-#7) |
| D (Freischaltung) | ✅ (Session #7-#17) |
| E (2-Wochen-Test) | 🔄 — J-Block ✅ (#22), Doc-Drift-Repair ✅ (#23), Pre-Flight-Verify ✅ (#24), **Drift-#7-Fix-v3 ✅ (#25)**, J4+J6+J7 (Nikinger jetzt) |
| F (Subphase) | 🔄 — G/H/I (laufend nach J6) |
