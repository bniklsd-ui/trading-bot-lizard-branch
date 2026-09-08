---
status: partial
purpose: Partial Closeout + Mini-Plan für die 2-Wochen-Test-Periode (Phase-16-F-Subphase, 2026-09-08) — strukturiert Audit-Restbefunde (29+1+1) + laufenden 2-Wochen-Test (E4) + Tag-10-Closeout in 3 Blöcken G/H/I
read-when: jede Phase-16-Session ab jetzt bis Tag-10-Closeout (Mo 2026-09-21)
detail: L3
up: ../CLAUDE.md
down:
  - ./PHASE16_AUTONOMY_PREREGISTRATION.md    # 📕 PASS-Kriterien + erlaubte Operator-Ereignisse
  - ./PHASE16_E3_RUNBOOK_v2.md              # 📕 Operator-Runbook
  - ./SESSIONS_ARCHIVE.md                   # 📦 Session-Historie (newest-first)
  - ../docs/concepts/phase16_activation_plan.md  # 📕 Vollplan
updated: 2026-09-08
---

# Phase 16 — Partial Closeout + Restplan (F-Subphase)

> Partial Closeout der Phase 16 zur **Halbzeit des 2-Wochen-Autonomie-Tests** (Tag 1 von 10 = Di 2026-09-08). Nach abgeschlossenen Blöcken A–E + F9-Mechanik + Audit-Session #19 jetzt **drei** offene Stränge, die in diesem Mini-Plan strukturiert sind.

## §0 BLUF

- **Status:** alle Blöcke A–E code-complete + E3 Restart #4 läuft seit 2026-09-08 09:30:49 (PID 281715, keine Tracebacks im Log).
- **Σ 1934 grün** (Phase-16-Endstand, +10 F9-Tests vs. Σ-Baseline 1924).
- **Audit-Session #19** hat 31 Restbefunde aufgedeckt + 2 davon (Phase 14 [9, 10] + Phase 15 [1]) bereits repariert (`ce74ee1` + `23bbd14`).
- **3 Stränge offen, hier als F-Subphase strukturiert:** **G** Audit-Restbefunde-Reparatur (29 + 1 + 1 Items), **H** 2-Wochen-Test-Tagesroutine-Begleitung (E4 läuft, 9 Tage verbleibend bis Mo 2026-09-21), **I** Tag-10-Closeout.
- **Phase 17 explizit ausgeschlossen** — alle offenen Items laufen als **Phase-16-F-Subphase** (keine neue Phase-Nummer, gemäß Nikinger-Auftrag 2026-09-08).

## §1 Status-Quintessenz

### 1.1 Phase-16 Block-Tabelle (vollständig)

| Block | Inhalt | Status |
|---|---|---|
| A | Haushalt (Step-0-Ritual, Σ-Baseline, Code↔.md-Sweep, WebUI-Log, Push) | ✅ endgültig (Sessions #1–#3) |
| B | Substrat (Schema-Floor + Operator-Apply + Ledger-Restore + Wochenend-Filter + Demotion) | ✅ endgültig (Session #3) |
| C | Research-Loop (Historien-Fenster 14d + Budget 300k + Breaker-Semantik P3 + Prompt-Satz) | ✅ endgültig (Sessions #4–#5) |
| D | Freischaltung (Defaults ON + Bar-Stream-Token-Wrapper + Promotion-Bridge + Compiler + Margin-Headroom) | ✅ endgültig (Sessions #7–#10) |
| E | 2-Wochen-Autonomie-Test (E1 Prereg + E2 Report + E3 Runbook v2 + Pre-Steps + Hotfixes + F9) | 🟡 **Restart #4 läuft** (E4 Tagesroutine), Tag 1–10 |
| **F** | **Audit + Restplan** (F9-Mechanik + Audit-Session #19 + Partial Closeout dieser) | 🟡 **diese Session** |

### 1.2 Σ-Endstand (2026-09-08 re-measured)

- **1934 grün** (Phase-16, ohne `meta_m1_harness/28` Tests → 1962 mit).
- P1 97 · P2 82 · P3 105 · P4 162 · P5 190 · P6 76 · P7 169 · P8 259 · P9 95 · P10 165 · P12 145 · P13 82 · P14 61 · P15 126 · P16 5 · root 115.
- `python3 scripts/check_doc_rotation.py --strict --quiet` exit **0** (Repo-weit F9-konform).
- **Konvention:** `meta_m1_harness/` (28 Tests) zählt **nicht** mit → Σ ohne M1 = 1934, mit M1 = 1962. (Session-#17-F7 hat das protokolliert; Session #19 hat es erneut verifiziert.)

### 1.3 Live-Stand (Stand Session #19/20, 2026-09-08 ~22:00)

- **Scheduler:** PID 281715, K7-Caps-Pin `account=demo, max_trades=5, daily_loss_cap=1800.0, cycle=5min` verbatim in Startzeile.
- **Recorder:** PID 268859 · **Discovery:** 268871 · **WebUI:** 268921 (alle 4 durchgehend seit Restart #4).
- **Tag 1 von 10** (Di 2026-09-08) → **Tag 10 = Mo 2026-09-21**.
- 0 OPEN-Trades, 0 autonome Trades seit Restart #4 (Tag-1-Beobachtung: Research + Discovery laufen normal, Research-Abstain-Quote weiter hoch — entspricht L1-Architektur, nicht neuer Bruch).
- `data/state/run_scheduler.log` endet mit `INFO scheduler.run: starting scheduler daemon ...` ohne Traceback.

### 1.4 Audit-Recap (Session #19, 6 Checks)

| # | Check | Result | Aktion in dieser Subphase |
|---|---|---|---|
| 1 | Push-Baseline (F6) | ✅ PASS (keine stale Claims in aktiven Phasenköpfen) | keine |
| 2 | Σ-Konsistenz (F7) | ✅ PASS (Σ 1934 gemessen vs. Behauptungen) | keine |
| 3 | Archiv-Integrität (F8) | 🟢 2 echte Befunde | ✅ **repariert** (`ce74ee1` + `23bbd14`) — Phase 14 [9, 10] + Phase 15 [1] |
| 4 | Ein Block/Phasenkopf | ✅ PASS (16 Phasen, phase2 = 0 = kanonisch) | keine |
| 5 | INDEX-Vollständigkeit | 🟡 Scope-Drift (224 Skill-Internals fehlen in INDEX) | **H-2** Klarstellung in DOC_LAYERS_CONVENTION.md |
| 6 | Header-Card-Links | 🟡 29 echte fehlende Links | **H-1** + **H-3** (neuer Hook + Sammel-Reparatur) |

## §2 Audit-Befunde im Detail (Input für Block H)

### 2.1 29 Header-Card-Link-Drifts (kategorisiert)

1. **15x Pattern A** `../../` statt `../` — Files in `phase*/`, nicht in `phase*/<dir>/`:
   - `phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md` (4 Links)
   - `phase14_discovery/PHASE14_F_DOC_ROTATION_HOOK_STEP2_PLAN.md` (4 Links)
   - `phase15_v4/PHASE15_HOOK_HARDENING_PLAN.md` (4 Links)
   - `phase7_reward/PHASE12_RECONCILIATION_TIMING_PLAN.md` (7 Links)
   - **Mechanischer Fix:** `sed 's|\.\./\.\./|\.\./|g'` pro File.

2. **4x Pattern B** `./` statt `../` — Files in `docs/concepts/`:
   - `PHASE10_META_KICKOFF_HANDOVER.md`, `phase10_v3_plan.md`, `meta_m1_harness_plan.md`, `PHASE10_V3_KICKOFF_HANDOVER.md`
   - **Mechanischer Fix:** `sed 's|^\.\/CLAUDE\.md|..\/CLAUDE.md|g'` (Up-Heading-Zeile).

3. **1x Pattern C** — fehlende Datei: `phase15_v4/PHASE15_A1_A6_STEP_RECORDS.md` im Plan referenziert, nie erstellt.
   - **Entscheidung (Nikinger):** erstellen (5-Zeilen-Summary der Phase-15-A-1..A-6-Step-Records + Commit-Verweise) **ODER** Reference aus Plan entfernen.

4. **1x Pattern D** Prose-List: `phase10_v3/PHASE10_CLOSEOUT_HANDOVER.md` → `./DATA_WEEK_REVIEW_2026-07-25.md / -07-31.md / -08-07.md`
   - **Mechanischer Fix:** in 3 separate Markdown-Lines aufspalten.

5. **8x Pattern E** Mischformen (Bold-Marker + Pfade + Kommentare) — manuell zu prüfen, F9-Hook-Beweis gibt die genaue Liste.

### 2.2 1 INDEX-Scope-Drift

- 224 `.md`-Dateien sind nicht in `docs/INDEX.md` erwähnt.
- Verteilung: 220+ Skill-Internals (`.agents/skills/`) + 6 Harness-Specs (`meta_m1_harness/specs/`).
- INDEX.md-Regel („new `.md` ⇒ add one line") wurde für Skill-Internals nie angewendet — Konventionsdrift.
- **Fix:** 1-Satz-Klarstellung in `DOC_LAYERS_CONVENTION.md` (sieH-2).

### 2.3 1 Phase-14-Archive-File-Order-Bug

- Session-7-Block steht am Ende des Phase-14-Archivs (Z. 3205), sollte chronologisch zwischen Session-8 (Z. 2364) und Session-6 stehen.
- F9 erkennt das nicht (F9 prüft nur Contiguity-Set, nicht Reihenfolge).
- **Fix:** Session-7-Block mit `---`-Separator umschlossen an die richtige Stelle verschieben (sieH-4).

## §3 Gelockte Entscheidungen (Phase-16-F-Subphase)

| ID | Entscheidung | Begründung |
|---|---|---|
| **F1** | Phase-16-F ist eine **Subphase** von Phase 16 (kein Phase-17, keine neue Nummer) | Nikinger-Auftrag 2026-09-08: „Keine Phase 17, weitere Phase 16 Subphase". Phase 16 ist als großes Ganzes bereits geplant (Plan §1 P1), die Restarbeit passt in F. |
| **F2** | F9-Mechanik (`scripts/check_doc_rotation.py` + `_first_session_num_per_heading` + `check_archive_gaps`) bleibt das zentrale Tool für Archiv-Integrität | F9 deckt Archiv-Integrität ab (alle restlichen Befunde sind Pre-Existing-Drifts aus dem Doku-Strang, nicht aus der Code-Basis); F9-Step-3 ist Teil von `--strict` (Nikinger-Auftrag 2026-09-08) |
| **F3** | Neuer Hook `scripts/check_header_card_links.py` (Block H-1) wird **vor** der Sammel-Reparatur gebaut — analog Session #18-F9-Strategie | Hook erkennt zukünftige Header-Card-Drifts; mit dem Hook-Beweis (exit 1 vor Reparatur → exit 0 nach Reparatur) wird die Sammel-Reparatur testbar |
| **F4** | Sammel-Reparatur-Commit für alle 29 + 1 + 1 Header-Card/INDEX/Order-Drifts — **nicht** 31 Einzelcommits | Die Reparaturen sind mechanisch (Pattern A-E), eine Plan-Session hat sie als Einheit begründet; 31 Mini-Commits produzieren nur Lärm im Log. Pattern einmalig im Sammel-Commit-Body dokumentiert. |
| **F5** | Phase-16-F-Tagesroutine (Block G) hat **Vorrang** vor Code-Edits (Block H) | Block E (2-Wochen-Test) ist das laufende Hauptexperiment. Code-Edits in Block H nur **außerhalb** der Trade-Fenster (Mo–Fr 09:00–17:30 Berlin): Fr-Abend 17:30+, Wochenende Sa/So, Mo-Fr-Morgen vor 09:00. |
| **F6** | Audit-Restbefunde-Reparatur ist **read-only** für aktive Phasen (Phase 16) — pre-existing-Drifts für abgeschlossene Phasen (Phase 14 Archive-Order-Bug) | Phase-16-Block-E läuft, keine Drift darf den 2-Wochen-Test beeinflussen. Phase-14 ist abgeschlossen, H-4-Fix ist mechanisch (Block-Verschiebung, kein Inhalt-Edit). |
| **F7** | Tag-10-Closeout (Block I) läuft Mo-Abend 2026-09-21 oder Di-Morgen 2026-09-22 | Mo 2026-09-21 ist der letzte Handelstag. Trade-Fenster bis 17:30, danach Operator-Aktion `autonomy_report.py --summary`. Closeout-Handover + SVG + Status-Pflege am Mo-Abend oder Di-Morgen (außerhalb des Fensters). |
| **F8** | Phase-15-`requires-python`-Align (`>=3.12` vs `>=3.11`) bleibt **offen** (Phase-17-Kandidat) | Drift aus Session #14 zwischen Plan-Literal und 13-Package-Konsens — Nikinger-Entscheidung; aktuell funktional egal (.venv ist 3.12). Nicht-blockierend für E4. |

## §4 Schritt-Sequenz (Mini-Plan für die 2-Wochen-Test-Periode)

> **Reihenfolge:** zuerst Block H (Audit-Restbefunde-Strukturierung, **parallel** zu Block G aber **außerhalb** der Trade-Fenster), dann Block G laufend (E4-Tagesroutine), dann Block I (Tag-10-Closeout).
>
> **Trade-Fenster Mo–Fr 09:00–17:30 (Berlin) = E4-only.** Code-Edits nur außerhalb.

### Block G — 2-Wochen-Test-Tagesroutine-Begleitung (laufend, 9 Tage)

**G1** (laufend, Nikinger-Aktion): `python3 phase16_activation/scripts/autonomy_report.py --day YYYY-MM-DD` einmal pro Handelstag (Mi 2026-09-09 bis Mo 2026-09-21, 9 Tage).

**G2** (laufend, Nikinger-Aktion): Tägliche K7-Caps-Pin-Verifikation via `cat /proc/$(pgrep -f scheduler.run)/cmdline | tr '\0' ' '` (muss verbatim `account=demo, max_trades=5, daily_loss_cap=1800.0, cycle=5min` enthalten).

**G3** (laufend, Exec-Session on demand): Bei jedem Tag-Report FAIL in Kriterium 1 (Operator-Restart) → Root-Cause in nächstem Session-Block dokumentieren (Opus-#17-F8-Muster: Befund-Beschreibung + Diff + Lessons).

**G4** (laufend, Exec-Session on demand): Bei jedem Tag-Report FAIL in K5 (≤ 5 CRITICALs in 24h nach OPEN) → Root-Cause-Tracing (Phase-16-Plan §8 Symptom→Verdächtiger-Tabelle, K7 = CRITICAL).

**Akzeptanz G:** 9 weitere Tag-Reports ohne manuellen Restart (`autonomy_<day>.json` in `data/reports/`), `daily_loss_cap=1800` nie gerissen, K7-Caps-Pin jeden Tag in `/proc/<pid>/cmdline` korrekt.

### Block H — Audit-Restbefunde-Reparatur (1 Plan-Session + 1 Sammel-Commit, **außerhalb** Trade-Fenster)

> **Wann:** Fr-Abend 2026-09-12 (nach 17:30) oder Sa/So 2026-09-13/14 (ganzer Tag). Empfehlung: Wochenende 13.–14. Sept., 1 zusammenhängender Block, keine Markt-Unterbrechung.

**H-1** — `scripts/check_header_card_links.py` NEU (analog F9):

- `_first_link_per_heading`-Helper extrahiert `up:`-Targets (single-line) und `down:`-Liste (multi-line mit `- <path>`).
- Markdown-Format strippen: `**` (bold) und `` ` `` (inline code), aber NICHT `_` (Underscore ist Teil von Filenames wie `PHASE10_CLOSEOUT_HANDOVER.md`).
- `check_header_card_links(scope)` prüft alle Header-Card-Links gegen Filesystem.
- In `main()` als **Step 4** im `--strict`-Modus verdrahtet (analog F9 als Step 3).
- Tests in `tests/test_check_header_card_links.py` NEU (~8 Tests, analog F9-Tests):
  - `test_extract_up_link_simple`
  - `test_extract_up_link_with_inline_code`
  - `test_extract_down_links_multi_line_with_comments`
  - `test_strip_markdown_preserves_underscores` (Regression-Pin: F8-False-Positive verhindern)
  - `test_header_card_links_ok_for_known_good_file` (z. B. `phase16_activation/CLAUDE.md`)
  - `test_header_card_links_fail_for_double_dotdot_path` (Regression-Pin für die 15 Phase-13/14/15-Bugs)
  - `test_header_card_links_fail_for_relative_path_in_docs_concepts` (Regression-Pin für die 4 docs/concepts-Bugs)
  - `test_header_card_links_fail_for_missing_referenced_file` (Regression-Pin für `PHASE15_A1_A6_STEP_RECORDS.md`)
- `--strict`-Default **nach** Hook-Beweis (analog F9: erst Phase #18 hat F9 gebaut, Phase #19 hat F9 mit Reparaturen bewiesen, Phase #20 hat F9 als Default installiert).
- **2 Atomic Commits:** `phase16: code+tests -- F10 Hook check_header_card_links.py (analog F9, 8 neue Tests root 115 → 123, Pre-H-3-Befunde-Beweis 29 missing)` + ggf. `phase16: docs -- install_hooks.sh Header Four-Steps → Five-Steps (Step 4 hinzugefügt)`.

**H-2** — `docs/DOC_LAYERS_CONVENTION.md` — 1-Satz-Klarstellung:

- Neuer Eintrag im L0/L1/L2/L3-Abschnitt: _"Skill-Internals in `.agents/skills/` und Harness-Specs in `meta_m1_harness/specs/` sind Tooling-Metadaten, **nicht** Projekt-Doku, und werden daher **nicht** in `docs/INDEX.md` gelistet. Die INDEX-Regel „jede `.md` hat eine INDEX-Zeile" gilt für `phase*/` + `docs/` + root-`.md`-Dateien."_
- 1 Commit (`phase16: docs -- DOC_LAYERS_CONVENTION.md: INDEX-Scope-Klarstellung (Skill-Internals sind Tooling-Metadata)`).

**H-3** — Sammel-Reparatur der 29 Header-Card-Link-Drifts + 1 fehlende Datei:

- Pattern A (15x): `sed 's|\.\./\.\./|\.\./|g'` pro File — mechanisch via Bash.
- Pattern B (4x): `sed 's|^\.\/CLAUDE\.md|..\/CLAUDE.md|g'` pro File in `docs/concepts/`.
- Pattern C (1x, Nikinger-Entscheidung): `phase15_v4/PHASE15_A1_A6_STEP_RECORDS.md` entweder **erstellen** (5-Zeilen-Summary mit Commit-Verweisen auf die A-1..A-6-Step-Commits) ODER Reference aus `PHASE15_HOOK_HARDENING_PLAN.md` entfernen.
- Pattern D (1x): Prose-List aufspalten in 3 separate Markdown-Lines.
- Pattern E (8x): manuell, basierend auf H-1-Hook-Output (genau-Liste).
- **1 Sammel-Commit** `phase16: docs -- Sammel-Reparatur der 29 Header-Card-Link-Drifts aus Audit-Session #19 (Pattern A-E, F10-Hook-Beweis Regression-Pin)`.

**H-4** — Phase-14-Archive-File-Order-Fix:

- Session-7-Block (Z. 3205) mit `---`-Separator umschlossen, an die richtige Stelle zwischen Session-8 (Z. 2364) und Session-6 (Z. ~2400) verschieben.
- Block-Inhalt unverändert (Pre-Existing-Drift, mechanischer Move).
- 1 Commit `phase14: docs -- Session-7-Block von File-Ende an chronologisch korrekte Stelle verschoben (Phase-16-F-Subphase Block H-4)`.

**H-5** — Verifikation:

- `python3 scripts/check_doc_rotation.py --strict --quiet` exit **0** (F9 weiterhin clean).
- `python3 scripts/check_header_card_links.py --strict --quiet` exit **0** (H-1-Hook neu, jetzt clean nach H-3).
- `pytest tests/ -q -p no:cacheprovider` pro Phase — Σ unverändert (H-3 + H-4 docs-only, H-1 Hook + Tests +8-10 in root tests).
- **Hook-Beweis (Session #19-F8-Muster):** H-1-Hook exit 1 vor H-3 auf einem Pre-H-3-Snapshot zeigt die 29 Befunde, exit 0 nach H-3 auf demselben Stand zeigt 0. (Analog F8-Beweis aus Session #18: 2 echte F8-Befunde wurden sichtbar, dann repariert.)

**Akzeptanz H:** H-1-Hook shipped + Tests grün + alle H-2/H-3/H-4/H-5 erfüllt = 1 neuer Hook + 1 Convention-Klarstellung + 29 + 1 Sammel-Reparaturen + 1 Archive-Order-Fix + Verifikation.

### Block I — Tag-10-Closeout (Mo 2026-09-21 nach 17:30, oder Di 2026-09-22 morgens)

> **Wann:** Mo 2026-09-21 nach 17:30 (Trade-Fenster-Ende + Operator-Aktion). Di 2026-09-22 vor 09:00 (vor Trade-Fenster-Start) als Alternative.

**I-1** — `python3 phase16_activation/scripts/autonomy_report.py --from 2026-09-08 --to 2026-09-21 --summary`

- Bei `overall_verdict == "PASS"`: Block I-2 bis I-5.
- Bei `overall_verdict == "FAIL"`: Root-Cause-Tracing (Phase-16-Plan §8) → Fix-Plan → ggf. Lauf-Verlängerung (Nikinger-Entscheidung, E4-Plan §11 Trigger T-12 „Sofort-Stop" greift nur bei nicht-Demo-Trade).

**I-2** — `phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md` NEU:

- Pattern analog zu `phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md` (763 LOC-Vorbild) + `phase14_discovery/PHASE14_CLOSEOUT_HANDOVER.md` + `phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md` + `phase12_data_foundation/PHASE12_CLOSEOUT_HANDOVER.md`.
- §0 BLUF + 5-Zeilen-Bilanz (fertig/getestet/live-validiert/gepusht/nicht-erreicht) — alle 6 Blöcke A-F ✅.
- §1 Architektur-Bild: `docs/architecture/phase16_activation.svg` 1080×1080 (Block I-3).
- §2 Locks P1-P18 (aus Phase-16-Plan, alle erfüllt).
- §3 A1-A17-Akzeptanz (alle ✅, inkl. AK15 7-Kriterien):
  - A1 Σ ≥ 1843 ✅ (1934)
  - A2 K1 ein Start-Zeile pro Dienst ✅
  - A3 K2 ≥ 1 Event/Tag (Scheduler + Recorder + Discovery) ✅
  - A4 K3 ≥ 5 autonome open→→close Trades (Watch: Tag1 hat 0 OPEN, ggf. E4-Lauf-Verlängerung falls am Tag 10 < 5 Trades)
  - A5 K4 Heartbeat ok ≥ 8/10 Tagen
  - A6 K5 ≤ 5 CRITICALs/24h nach OPEN (jedes OPEN-Trade einzeln)
  - A7 K6 Token-Budget nie vor 17:30 leer (Σ < 300 000)
  - A8 K7 Caps unverändert (Demo, `max_trades=5`, `daily_loss_cap=1800`)
- §4 As-Built-Zahlen heute (Σ 1934, 4 Daemons + 1 WebUI laufend, 0 OPEN-Trades etc.).
- §5 Test vs. Live vs. Produktion (Demo-Account vollständig, Live-Account ausstehend per Hard Rule 4).
- §6 Delta seit Session #19 (Audit-Session #19 + F-Subphase-Eröffnung + H/I-Reparaturen).
- §7 Offene Entscheidungen E1-E9 (Promotion-Bridge ✅ done in D2, Ledger-Restore 250 Punkte [Nikinger-Action-Status], A6 Live-Verify [wartet auf nächsten OPEN], Live-DB Migration 008+009 [Nikinger-Action on Demand]).
- §8 Datei-Anker (mit Partial-Closeout-Verweis).
- §9 Konsistenz-Regeln (mit F1-F8 + F-Subphase-Philosophie „kein Phase-17, weitere Subphase").
- §10 Don'ts.
- §11 Was diese Session gemacht hat.

**I-3** — `docs/architecture/phase16_activation.svg` NEU (1080×1080):

- 5-Panel-Layout (analog Phase-13/14/15-Closeout-SVGs):
  - ① Fehlerbild: 100 % Research-Abstain seit 2026-08-31 (L1, vor Phase 16).
  - ② Zielbild: 2-Wochen-Test läuft mit allen 4 Armen ON (Shadow-Schedule + Divergence-Sampler + Bar-Stream + Paper-Debate).
  - ③ Block-Tabelle A-F (alle ✅ — 5 Sessions + 1 Subphase, 6 Blöcke).
  - ④ Status-Panel 3-spaltig (fertig/getestet + live-validiert + gepusht/nicht-gepusht + nicht-ererreicht/offen).
  - ⑤ Was-das-Bild-trägt-Callout (3 Elemente: F9-Mechanik catches-the-class + Audit-Read-only-Reparaturen + 2-Wochen-Test-bestanden).

**I-4** — Status-Pflege root + ROADMAP + README + INDEX:

- `CLAUDE.md`: Phase-16-Row in Status-Tabelle → `✅ **abgeschlossen (Closeout 2026-09-21, Tag-10)**` mit Verweis auf Closeout-Handover + Partial Closeout.
- `ROADMAP.md`: Phase-16-Abschnitt → `✅ abgeschlossen 2026-09-21, Tag 10 = Mo 2026-09-21, alle 6 Blöcke A-F, Σ 1934+` + Block-Häkchen-Update + Plan-Verweis auf Partial-Closeout.
- `docs/INDEX.md`: Phase-16-Cluster +2 Zeilen (CLOSE-OUT + Bild).
- `README.md`: Phase-16-Status-Update falls dort erwähnt.

**I-5** — Session-Rotation (Standard-Pattern): Session #20 → Archiv, Session #21 (Closeout) im Phasenkopf. 1 Commit.

**Akzeptanz I:** Alle I-1..I-5 ✅, Phase 16 closed in `CLAUDE.md` + `ROADMAP.md` + `README.md` + `INDEX.md` + Status-Archiv-Tabelle.

## §5 Akzeptanzkriterien (alle Blöcke G + H + I)

| AK | Kriterium | Beleg |
|---|---|---|
| **AK-F1** | Phase-16-F-Subphase existiert (Partial Closeout + Mini-Plan) | dieses Dokument + Phasenkopf-Updated-Stamp |
| **AK-F2** | Audit-Restbefunde strukturiert (29 + 1 + 1) | §2 Recap + §4-H-Block |
| **AK-F3** | Block G läuft 9 Tage ohne manuellen Restart | 9 `--day`-Reports in `data/reports/autonomy_<day>.json` |
| **AK-F4** | H-1-Hook shipped + Tests grün | `scripts/check_header_card_links.py` + `pytest tests/test_check_header_card_links.py -q` exit 0 |
| **AK-F5** | H-2 Convention-Klarstellung + H-3 Sammel-Reparatur + H-4 Order-Fix durch | 4 Commits + H-1-Hook exit 0 nach H-3 |
| **AK-F6** | I-1 Summary PASS | `overall_verdict == "PASS"` |
| **AK-F7** | I-2 Closeout-Handover + I-3 SVG + I-4 Status-Pflege + I-5 Rotation | neue Dateien + Updated-Stamps in root/ROADMAP/README/INDEX |

## §6 Operator-Aktionen (Nikinger, nicht Exec-Session)

| # | Wann | Was | Kosten |
|---|---|---|---|
| 1 | täglich bis Tag 10 | `python3 phase16_activation/scripts/autonomy_report.py --day YYYY-MM-DD` | ~30 sec/Tag |
| 2 | täglich | K7-Caps-Pin-Verify via `cat /proc/$(pgrep -f scheduler.run)/cmdline | tr '\0' ' '` | ~10 sec/Tag |
| 3 | Sa/So 2026-09-13/14 (oder Fr-Abend 2026-09-12) | Push der Block-H-Commits (H-1-Hook + H-2 Convention + H-3 Sammel + H-4 Order + ggf. Install-Hook) | — |
| 4 | Mo 2026-09-21 nach 17:30 | `python3 phase16_activation/scripts/autonomy_report.py --from 2026-09-08 --to 2026-09-21 --summary` | ~5 sec |
| 5 | nach I-1 PASS | Push der Block-I-Commits (Closeout-Handover + SVG + Status-Pflege) | — |
| 6 | bei FAIL (I-1 != PASS) | Root-Cause + Fix-Plan + ggf. Lauf-Verlängerung-Entscheidung | — |
| 7 | einmalig (Phase-15-CLOSOUT-Delegat E3) | Ledger-Restore 250 Punkte (war Phase-15-Offene-Entscheidung, Status bisher unklar) | ~5 min |
| 8 | einmalig (Phase-16-Plan §3 L3) | Backup-Operator-SQL für 3 SUN*-Epics pre-Tag-1 (war E1-Aktiv-Block, Status prüfen) | ~1 min |

## §7 Out-of-Scope (für Phase-17 delegiert)

- **Strategie-Bewertung** (BUY-Bias, DAX-Only, R:R 1.5, 2 W : 6 L) → Watch-Items W1–W6 der Prereg, **nicht** Phase-16-Scope (Phase-16-Plan §1 P3: „Phase 16 stopft Infrastruktur").
- **Prozess-Supervision** (systemd-User-Unit + Auto-Restart + Keyring ohne Login) → reale Lücke, Phase-17-Kandidat (Opus-Review §13 #5).
- **Smoke-Test-Pattern auf Geschwister-`_build_*`** (`_build_paper_tracker`, `_build_paper_engine`, `_build_context_recorder`, `_build_data_foundation`, `_build_research`, `_build_universe_from_db`, `_build_abstain_sink`) → Phase-17-Kandidat (Watch-Item aus Session #18-F9).
- **Phase-15-Wiring-Doku** (3 Konstruktor-Signaturen `InstinctBridge`, `SingleShotInstinctExtractor`, `InstinctValidator` prominent im Phase-15-Repo) → Phase-17-Kandidat (Watch-Item).
- **Phase-15 `requires-python`-Align** (`>=3.12` vs `>=3.11`, F8-Lock) → F8 §F8, Nikinger-Entscheidung.
- **Force-Trigger-Implementierung** → existiert nicht; Hard Rule 5 bleibt Vorschrift.
- **Live-Account** → Hard Rule 4, Demo bleibt.
- **Phase-9 `is_weekend_market`** → bereits in B3 (Session #3) implementiert, ✅ erledigt.

## §8 Drift-Liste (bekannte Items, in dieser Subphase NICHT behoben)

| # | Drift | Status | Begründung / Delegation |
|---|---|---|---|
| **D-F1** | Phase-15 `requires-python='>=3.12'` vs `'>=3.11'` | offen, Mini-Change | F8 §F8, Nikinger-Entscheidung. Aktuell funktional egal (.venv ist 3.12). |
| **D-F2** | 1 fehlende Datei `phase15_v4/PHASE15_A1_A6_STEP_RECORDS.md` | offen, Nikinger-Entscheidung | Hängt von H-3-Pattern-C-Entscheidung ab (erstellen oder Reference raus). |
| **D-F3** | Plan-Session-Block-Heading ohne Modell | offen | Convention-Drift (Session #1 in Phase-15 hatte nie `#1`, wurde in Session #19 repariert). Phase-17-Plan-Session Klarstellung. |
| **D-F4** | Stale-Push-Status-Behauptungen in archivierten Phase-Blöcken (Phase 15 Z. 753, 882, etc.) | offen | Historische Audit-Stände (📦 Pattern), kein aktiver Vertrag. Stale-Push-Status-Mechanik Phase-17-Kandidat. |
| **D-F5** | 224 Skill-Internals in `docs/INDEX.md` fehlend | offen | Scope-Drift (H-2-Klarstellung), mechanisch behoben. |
| **D-F6** | Phase-14-Archive-File-Order-Bug (Session 7 am Ende) | offen (H-4-Fix) | Pre-Existing-Drift, in dieser Subphase behoben. |
| **D-F7** | Plan-Block-C noch nicht repariert (`market_snapshot_middleman_konzept.md` → falsche `phase9_v2_foundation_plan.md`) | offen | H-3-Pattern-B (Konzepte-Doc-Family), wird mit dem Pattern-B-Sammel-Reparatur mitbehoben. |
| **D-F8** | 31 vs. 29 Diskrepanz | beantwortet | Die 29 Header-Card-Link-Befunde sind die dokumentierten; weitere Funde (z. B. D-F7) können im H-1-Hook-Beweis als „> 29" gemeldet werden — Sammel-Commit-Body dokumentiert die Gesamt-Zahl. |

## §9 Was diese Session (Phase-16-F-Subphase-Eröffnung) gemacht hat

- **`PHASE16_PARTIAL_CLOSEOUT.md` NEU** (~13 KB): Partial Closeout der Phase 16 zur 2-Wochen-Test-Halbzeit + Mini-Plan für die 3 verbleibenden Stränge.
- **3 Blöcke strukturiert:** G (laufende E4-Begleitung, 9 Tage) + H (Audit-Restbefunde-Reparatur, Wochenende 13.–14. Sept.) + I (Tag-10-Closeout, Mo 2026-09-21 nach 17:30).
- **8 gelockte Entscheidungen** (F1-F8) mit Begründung je Zeile.
- **8 Akzeptanzkriterien** (AK-F1 bis AK-F7) mit Beleg-Quelle.
- **8 Operator-Aktionen** (Nikinger) tabelliert mit Kosten.
- **7 Out-of-Scope-Items** für Phase-17 explizit delegiert.
- **8 Drift-Items** dokumentiert (5 offen + 1 in dieser Subphase behoben + 2 Sammel-Reparatur-geplant).

## §10 Cross-Phase-Touch-Disziplin

- **Block H berührt 6 Phasen** (Phase 7, 10, 13, 14, 15 + root docs/concepts/) — alle im Phase-16-Plan §4 als Cross-Phase-freigegeben gelistet + Nikinger-Auftrag 2026-09-08.
- **Block I berührt root + docs/architecture + ROADMAP + README + INDEX + phase16_activation/CLAUDE.md + SESSIONS_ARCHIVE.md** — alle Phase-16-eigene Status-Pflege.
- **Hard Rule 3 unangetastet:** alle Reparaturen in Block H + I sind docs-only (Markdown-Inhalt + 1 kleiner Hook in `scripts/`, kein AI/VETO/Order-Pfad).

## §11 Σ-Impact

- **Aktuell:** Σ 1934 unverändert.
- **Block H:** H-1-Hook + Tests ~+8-10 in root → Σ 1934 → **~1944**.
- **Block I:** docs-only (kein Σ-Impact).
- **Phase 16 Closed-Σ:** ~1944 (final).

---

> **Nächste Sch:**:** (Nikinger, nach Push) F1. `git push origin main` für diesen `PHASE16_PARTIAL_CLOSEOUT.md`-Commit. F2. E4-Tagesroutine startet Tag 2 (Mi 2026-09-09) via `autonomy_report.py --day`. F3. Block H am Wochenende 13.–14. Sept. F4. Block I Mo 2026-09-21 nach 17:30. F5. Bei Tag-10-PASS → `PHASE16_CLOSEOUT_HANDOVER.md` + SVG + Status-Pflege.