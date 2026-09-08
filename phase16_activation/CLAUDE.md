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
updated: 2026-09-08 (+ Exec-Session #24: **Pre-Flight + Verify** [read-only V-Checks gegen F-Exec-Plan §6: V-1/V-3/V-7/V-9/V-10 ✅, V-2 ⚠ Session-only-Fixture für J3-Tests, V-8 🟡 Body-Link-Drift `phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md:298` notiert für Nikinger-Entscheidung] + Runbook-v2-§1-§11 gegen Code verifiziert + Block-H-Pattern-Tabelle 1:1 gegen Code abgeglichen [21 Header-Card-Links in 5 Dateien, 1 Body-Link zusätzlich], Session-Start-Reverification 12 Beleg-Checks ✅, Σ **1940 unverändert** [kein Test-Touch, kein Code-Touch, alle 4 Phase-16-J-Defekte-Fixes aus #22 weiterhin grün], 0 Commits pending [Nikinger-Aktionen morgen früh: Pflicht-SQL §1 + Pre-Flight §2.1-§2.6 + Restart §3 mit korrigiertem Caps-Pin-Kommando grep statt /proc/cmdline], J7-Verifikation AK-J1/J2/J3/J4 on demand nach J6 + 30 min, Block H Wochenende 13.-14. Sept. 2026 [Lock F5], Block I Mo 2026-09-21 nach 17:30, V-8-Drift-Entscheidung ausstehend). — Vorheriger Stand: Exec-Session #23 schließt ab: **Doc-Drift-Repair** der drei positiven Drifts zur Code-Wahrheit gefunden [D1 Live-DB Schema v7→v9, D2 Ledger-Restore ausgeführt 0|0 statt 5|250, D3 Push-Freigabe erteilt origin/main = `20a10c1` mit 0 0 ahead/behind], 5 Datierte 🟡-Korrekturhinweise in 5 Dateien, Σ 1940 unverändert, 0 Commits pending; Exec-Session #22 schließt ab: **Phase-16-F-Subphase Block J — die drei Struktur-Defekte des laufenden 2-Wochen-Tests alle drei gefixt**, Σ 1934 → **1940** [+6 neue Tests], 5 Atomic Commits, Nikinger-Sonderauftrag 2026-09-08 „J0 ist deine Aktion" → Bot-Stopp-Reihenfolge; Plan-Session #21: **`PHASE16_F_EXEC_PLAN.md` NEU** [611 LOC, Blöcke J/H/G/I], drei selbst gemessene Struktur-Defekte, Nikinger-Entscheidung Variante A, Σ-Regression-Baseline 1934 vor dem ersten Fix, Lock F3 revidiert)

## Session stopped — 2026-09-08 (MiniMax-M3-Exec-Session #24, Phase-16-F-Subphase **Pre-Flight + Verify** — read-only V-Checks gegen F-Exec-Plan §6 + Runbook-v2-Lesung für morgiges J4+J6+Aktiv-Block; Σ 1940 unverändert, 0 Commits pending, **kein Code-Touch, kein Test-Touch**, 1 Drift-Befund notiert [V-8 Body-Link `phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md:298`] für Nikinger-Entscheidung H-3 vs. Watch-Item-Phase-17)

> **Auftrag:** Nikinger-Chat 2026-09-08 Abend: „ich glaube du kannst über Opencode keinen Advisor Konsultieren (leider). Vorschlag: bereite und verifiziere alles vor, und wenn ich heute noch Zeit habe fange ich heute mit den ersten offenen Items an, die aktuell nicht geblockt sind. Einverstanden?" — Antwort: ja. Heute Abend: (a) Reverifikation Session-#23-Artefakte noch intakt, (b) V-Checks 1-3 + 7-10 aus F-Exec-Plan §6 als read-only Drift-Reparatur-Vorbereitung, (c) Runbook v2 §1-§11 gelesen + gegen Code verifiziert, (d) Block-H-Pattern-Tabelle gegen Code gegengeprüft. KEIN Code-Edit, KEIN Test-Touch. Σ 1940 erwartet (alle J-Block-Fixes aus #22 weiterhin grün).

### Completed

**0. Session-Start-Reverification (15 min, alle 2026-09-08 gemessen):**

| Beleg | Erwartung | Tatsächlich |
|---|---|---|
| Σ 16 Suites einzeln | 1940 | **1940** ✅ (97+82+105+162+190+76+169+259+95+165+149+82+61+126+7+115) |
| `check_doc_rotation.py --strict --quiet` | exit 0 | **exit 0** ✅ |
| `check_doc_rotation.py --strict --phase phase16_activation` | 1 block | **1 block** ✅ |
| `git rev-list --left-right --count origin/main...HEAD` | 0 0 | **0 0** ✅ |
| `git status` | clean (nur data/ untracked) | **clean** ✅ |
| Schema-Version | 9 | **9** ✅ |
| `source_spend WHERE kind='rescue'` | 0\|0 | **0\|0** ✅ |
| `instincts` count | 0 | **0** ✅ |
| `bars WHERE source='ls'` | 0 (wartet auf J6) | **0** ✅ |
| `trade_outcomes WHERE status='OPEN'` | 0 (P7/A6 wartet) | **0** ✅ |
| Bot-Prozesse (Scheduler/Recorder/Discovery/WebUI) | alle tot seit 11:40 | **alle tot** ✅ |
| J-Block-Fixes aus #22 (Commit-Hashes) | 4 commits grün | **4 commits grün** ✅ (Commit-Bodies geprüft via `git show`) |

**1. V-Checks F-Exec-Plan §6 (read-only, ~20 min):**

| V-# | Frage | Befund | Status |
|---|---|---|---|
| **V-1** | Existiert `tests/test_archive.py`? | Ja, 17 Tests, `test_insert_bars_from_other_thread:266` (J1) vorhanden | ✅ |
| **V-2** | Fixture-Aufbau in `test_heartbeat.py`? | `_insert_full_day_yf_bars:86` füllt **24h UTC** (00:00–23:59); J3-Tests brauchen **Session-only**-Fixture (Berlin 07:00–15:30 UTC) — F-Exec-Plan §6 V-2-Hypothese bestätigt, **Implementation-Detail für Block-H-Wochenende oder J3-Block** | 🟡 Hypothese bestätigt, Folge-Aufwand |
| **V-3** | Wer nutzt `BarArchive()`? | 5 Produktiv-Aufrufer: `phase13/scripts/gap_rescue_operator.py:245` + `phase13/scripts/capital_backfill.py:227` + `phase8/scripts/wiring.py:232` + `phase12/data_foundation/run.py:80` + `phase12/scripts/data_health.py:66` (alle Operator-/Recorder-Pfade, alle mit eigener Connection auf die DB; **keiner** im Hot-Path der Lightstreamer-Stream-Thread außer J1-Fix) | ✅ J1-Fix deckt alle Aufrufer ab |
| **V-7** | `_berlin_day`-Inverse vorhanden? | **Ja, obsolet**: `_berlin_day_bounds(day):244` existiert seit #22 J2 Commit `3969f8c` | ✅ Obsolet |
| **V-8** | Body-Links in `PHASE13_BEWEISWOCHE`? | 1 `../../`-Link im **Body** (Z. 298, Markdown-Link) **zusätzlich** zu den 21 `../../` in Header-Cards (Z. 14, 15, 17, 18) — F-Exec-Plan §4 zählt 21, grep findet 22. Body-Link **out-of-scope** per F-Exec-Plan V-8, ABER `sed` würde ihn als Side-Effect mitfixen | 🟡 **Drift, Nikinger-Entscheidung nötig** |
| **V-9** | `PHASE15_HOOK_HARDENING_PLAN.md` nach Pattern-C-Löschung? | Z. 10 löschen (`./PHASE15_A1_A6_STEP_RECORDS.md`) lässt 7 valide down-Einträge übrig; Einrückung bleibt korrekt | ✅ |
| **V-10** | `docs/INDEX.md` Cluster-Phase-16 | Z. 34-50 trägt bereits Prereg v2 + Partial Closeout + F-Exec-Plan + Runbook v2 + phase16_activation_plan; Block-H-Reparaturen brauchen **keine** neuen INDEX-Zeilen | ✅ |

**2. Runbook v2 §1-§11 gelesen + gegen Code verifiziert (für Nikinger morgen früh):**
- §1 Pflicht-Operator-SQL für 3 SUN*-Epics: in Prereg-Block V-5 als **No-Op** markiert (F-Exec-Plan §1.4: alle 5 SUN*-Epics stehen auf `status='verified'`, nicht `active'`) — Nikinger kann den Schritt als 0-Zeilen-Pre-Verify kurz laufen lassen, dann §2-§4 der Reihe nach.
- §2 Pre-Flight 6 Schritte: alle Befehle gegen aktuellen Code geprüft (`_schema_version` Tabelle, `data/bars.sqlite` für `source_spend`, `paper_trades.status` statt `resolved`, `last_verified_at` statt `last_verified_utc`).
- §2.4 Truncate: **3 Wrapper-Logs** + **4 Pre-Wrapper-Logs** = 7 Files insgesamt. Nikinger macht das **vor** J6.
- §3 Restart-Sequenz: `restart-services.sh start` startet 4 Services sequenziell. K7-Caps-Pin-Verify per `grep "starting scheduler daemon" data/state/run_scheduler.log | tail -1` (KORRIGIERT ggü. F-Exec-Plan §1.3: `/proc/<pid>/cmdline` enthält Caps nicht, Log schon).
- §6 Trigger-Bedingungen T-1..T-12: alle klar, V-4 (zweiter `ok=False`-Zweig `heartbeat.py:142` `pairs_resolved==0`) bleibt Verdächtiger falls K4 nach J3 nicht grün wird.
- §7 Watch-Items W1-W6: alle klar, W4 LS-Bars = 0 wird explizit für 09:10 Berlin erwartet (LS-Token-Handshake).

**3. F-Exec-Plan §4 Block H Pattern-Tabelle gegen Code verifiziert:**
- Pattern A (`../../` → `../`): 5 Dateien, **21 Header-Card-Links** (F-Exec-Plan-Zählung). Mein grep findet **22** (21 Header + 1 Body Z. 298 in PHASE13_BEWEISWOCHE).
- Pattern A1 (`../SESSIONS_ARCHIVE.md`): Z. 14 in `PHASE14_F_DOC_ROTATION_HOOK_STEP2_PLAN.md`, **kein sed**, manuell.
- Pattern A2 (`003_` → `008_`): Z. 24 in `phase7_reward/PHASE12_RECONCILIATION_TIMING_PLAN.md`, Migration-Umnummerierung, **kein sed**, manuell.
- Pattern B (`up: ./CLAUDE.md` in `docs/concepts/`): 4 Dateien, alle manuell, **kein sed** (Ziel je Datei verschieden).
- Pattern C (tote Referenz löschen): Z. 10 in `PHASE15_HOOK_HARDENING_PLAN.md`, 1 Zeile weg.
- Pattern D (Prosa-Liste aufspalten): Z. 13 in `PHASE10_CLOSEOUT_HANDOVER.md`, 1 Zeile wird 3 Zeilen.
- Pattern E (falsches Ziel korrigieren): Z. 8 in `docs/concepts/market_snapshot_middleman_konzept.md`, `(1)` im Dateinamen.
- H-4 (Phase-14 Session-7-Block chronologisch): Z. 3205 → vor Z. 2527, byte-identisch verschieben.
- H-2 (INDEX-Scope-Klarstellung): 1 Satz in `docs/DOC_LAYERS_CONVENTION.md:53` ergänzen.
- H-1 (Step 4 im Hook): `check_header_card_links()` in `scripts/check_doc_rotation.py:191` einfügen, 6 neue Tests, Σ 1940 → **1946** nach H-1.

### Findings

🟢 **Session-Start-Reverification perfekt: Σ 1940, alle 12 Beleg-Checks wie erwartet.** Die Session-#23-Arbeit (Doc-Drift-Repair) ist vollständig intakt; kein Code-Touch, kein Test-Touch, alle 4 J-Block-Fixes aus #22 weiterhin grün.

🟢 **5 von 7 V-Checks obsolet oder trivial grün:** V-1 (Test-Suite vorhanden), V-3 (5 Aufrufer, J1 deckt alle), V-7 (Helper existiert seit #22 J2), V-9 (down-Liste valide), V-10 (INDEX-Cluster vollständig). V-2 ist Implementations-Hinweis (Session-only-Fixture für J3-Tests), kein Drift.

🟡 **1 Drift notiert: V-8 Body-Link Z. 298 in `PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md`.** F-Exec-Plan §4 zählt 21 `../../`-Header-Card-Links, mein grep findet 22 (21 Header + 1 Body-Link). F-Exec-Plan V-8 sagt klar: „Step 4 prüft nur Header-Cards; Body-Links sind heute kein Vertrag." — out-of-scope per Plan. **ABER:** das `sed`-Kommando aus Pattern A wirkt **file-global** und würde Z. 298 als Side-Effect mitfixen. Optionen:
  - **A) Sed anwenden wie geplant**, Z. 298 wird Side-Effect-Fix (slight scope expansion 21→22, Link IST kaputt). **Empfehlung.**
  - **B) Sed nur auf Header-Card-Zeilen** anwenden, Z. 298 bleibt broken.
  - **C) Z. 298 als separates Watch-Item Phase-17** markieren, Sed wie geplant mit 21 Fixes.

🟢 **Runbook v2 §1-§11 ist Operator-SOT für morgen.** Pflicht-SQL-Schritt ist Prereg-Block V-5 zufolge **No-Op** (5 SUN*-Epics auf `status='verified'`, nicht `active'`) — Nikinger kann §1 als 0-Zeilen-Pre-Verify kurz laufen lassen, dann §2-§4.

🟢 **F-Exec-Plan §4 Block H Pattern-Tabelle stimmt 1:1 gegen Code.** 5 Dateien, 21 Header-Card-Links, 2 manuelle Ausnahmen (A1, A2), 4 Pattern-B-Dateien, 1 Pattern-C, 1 Pattern-D, 1 Pattern-E. H-4 Phase-14-Session-7-Move Z. 3205 → vor Z. 2527 (178 Zeilen byte-identisch). H-2 INDEX-Scope 1 Satz. H-1 Hook Step 4 = 1 Funktion + 6 Tests, Σ +6 → 1946.

🟢 **Vorbereitung vollständig.** Heute Abend keine Operator-Aktion erforderlich (Bot ist seit 11:40 down, morgen früh J4+J6+Aktiv-Block durch Nikinger). J7-Verifikationen hängen am ersten POST_WINDOW nach J6. Block H Wochenende 13.-14. Sept. 2026. Block I Mo 2026-09-21 nach 17:30.

### Open questions / blockers

- **V-8 Body-Link-Drift (Phase-13-Plan-Beweiswoche Z. 298)**: Nikinger-Entscheidung Option A/B/C oben. **Empfehlung: A** (Sed wie geplant, Side-Effect-Fix in Commit-Body dokumentieren).
- **Keine Session-#24-Blocker für morgen.** Runbook v2 ist Operator-SOT; alle 7 Truncate-Files in §2.4; K7-Caps-Pin-Kommando korrigiert (grep statt /proc/cmdline); J4-Logs-Backup ist .gitignore-d.
- **V-4 (zweiter `ok=False`-Zweig `heartbeat.py:142` `pairs_resolved==0`)** bleibt Watch-Item für die erste POST_WINDOW nach J6; falls K4 nach J3 nicht grün wird, ist `pairs_resolved == 0` der erste Verdächtige (F-Exec-Plan §7 Fehlgriff-Tabelle).

### NEXT (für die nächste Session / morgen früh nach J4+J6)

**Push-Status (post-push 2026-09-08 Abend):** `git rev-list --left-right --count origin/main...HEAD` = `0 0`, working tree clean. Session-#24 Doc-Rotation wird committet, Nikinger pusht bei nächster Gelegenheit.

**Offene Items für die nächste Session (Exec-Session #25, morgen nach J6):**

1. **Nikinger-Aktionen morgen früh** (in dieser Reihenfolge, verbatim aus `PHASE16_E3_RUNBOOK_v2.md`): Pflicht-SQL §1 (3 SUN*-Epics) → §2.1 Liveness → §2.2 Schema-Floor 9 → §2.3 Keyring → §2.4 K1-Log-Truncate (3+4=7 Files) → §2.5 DB-Health (5 SQL-Smokes) → §2.6 Prereg-Aktiv-Block-Eintragung + Commit `phase16: docs -- E1-Aktiv-Block-Eintragung` (Commit-Zeit < erste Start-Zeile, AK13) → §3 Restart + K7-Caps-Pin-Verify per `grep` (korrigiert).
2. **Tag-1-Live-Verifikation (Exec-Session #25, J7)**: AK-J1 `bars.source='ls'` > 0 (frühestens 09:10 Berlin) · AK-J2 0 ProgrammingError · AK-J3 K1 = 1 Start/Dienst · AK-J4 `measurement_heartbeat.ok == true` (17:00 Berlin = 17:30 minus 30-min-Lag). Bei K4-FAIL: V-4 `heartbeat.py:142` `pairs_resolved==0` prüfen.
3. **G + I**: G1 ab Tag 1 (`autonomy_report.py --day` täglich) · G2 Caps-Pin (grep) · G3/G4/G5 on demand · I-2+I-3 Tag-10-Closeout Mo 2026-09-21 nach 17:30.
4. **Block H Wochenende 13.-14. Sept.**: H-3 (Sammel-Reparatur Pattern A-E) Sa 13. · H-4 (Phase-14-Archiv-Move) Sa 13. · H-2 (INDEX-Scope) Sa 13. · H-1 (Hook Step 4) So 14. NACH H-3/H-4 (Lock H2) · H-5 (Verifikation). **Lock F5:** Code-Edits außerhalb Trade-Fenster. **V-8-Drift (PHASE13_BEWEISWOCHE Z. 298):** Sed-Side-Effect-Fix in H-3-Commit-Body dokumentieren (Option A).
5. **Phase-15-Folge-Punkte**: Promotion-Bridge ✅ · Ledger-Restore ✅ · Migration 008+009 ✅ · Gate P7/A6 ⏳.
6. **Push-Freigabe-Stand:** 0 Commits pending nach dieser Session-#24-Rotation; Nikinger pusht.

**Block-Status nach Session #24:**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ (Session #1-#4) |
| B (Substrat) | ✅ (Session #3) |
| C (Research-Loop) | ✅ (Sessions #3-#7) |
| D (Freischaltung) | ✅ (Session #7-#17) |
| E (2-Wochen-Test) | 🔄 — J-Block ✅ (#22), Doc-Drift-Repair ✅ (#23), Pre-Flight-Verify ✅ (#24), J4+J6 (Nikinger morgen früh), J7 (#25 on demand) |
| F (Subphase) | 🔄 — G/H/I (laufend nach J6) |
