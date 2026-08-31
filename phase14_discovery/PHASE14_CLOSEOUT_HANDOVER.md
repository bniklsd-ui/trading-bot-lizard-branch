---
status: snapshot
purpose: Phase-14-Closeout-Handover (2026-08-31) — Phase 14 (Discovery-Then-Deterministic) ✅ **abgeschlossen**. Code-complete (Blöcke 0/A/B/C/D, Akzeptanz A1–A8 alle grün seit Session 9) + D5-Handover komplett freigegeben (Mini-Session 24, Pfad-C-Entscheidung) + P14-F Doc-Rotation-Hook `--strict` als Default (Mini-Session 24) + 4 Mini-Pläne P14-C/D/E/F abgeschlossen. Read-only-Inventur, jeder Datenpunkt selbst nachgemessen.
read-when: vor jedem Plan, der Phase 14 wieder aufnimmt; vor jedem Re-Read der D5-Handover-Begründung; vor jeder Frage „ist Phase 14 eigentlich fertig?"; vor jedem Code-Edit an `source_registry/`, `phase2_persistence/migrations/007_*`, `phase9_universe/universe/{models,store}.py`, `phase13_live_data/live_data/backfill.py`, `phase13_live_data/scripts/probe_capital.py`, `phase13_live_data/scripts/source_delta.py`, `phase8_scheduler/webui/`, oder `phase8_scheduler/scripts/run_scheduler.sh`
detail: L3
up: ./CLAUDE.md
down:
  - ./PHASE14_B1A_PROBE_OUTPUT_2026-08-22.md        # 📕 B1a Probe-Snapshot (Capital.com `/markets`-Rohdaten, 8 nummerierte Befunde)
  - ./PHASE14_C_DAEMON_CWD_BUG_PLAN.md              # 📕 P14-C Mini-Plan (Discovery-Daemon-CWD-Path-Bug, 2026-08-26)
  - ./PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md           # 📕 P14-D Mini-Plan (Discovery-Daemon-Signal-Response-Bug, 2026-08-26 + §10 Korrekturnotiz 2026-08-31)
  - ./PHASE14_E_RECORDER_LOOP_PLAN.md               # 📕 P14-E Mini-Plan (Recorder-Sleep-Cap-Bug + Restart-Loop-Hunt, 2026-08-28 + §2 D3-Korrekturnotiz)
  - ./PHASE14_F_DOC_ROTATION_HOOK_STEP2_PLAN.md     # 📕 P14-F Mini-Plan (Doc-Rotation-Hook Schritt 2, 2026-08-31)
  - ../docs/concepts/phase14_discovery_plan.md       # 📕 Mutterplan, gelockte D1–D20 (unangetastet)
  - ../docs/concepts/phase14_discovery_concept.md    # 📕 Phase-14-Concept (drei Bausteine, sieben offene Fragen — vom Plan Q1–Q7 beantwortet)
  - ../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md # 📕 Pattern-Vorbild Phase-13-Closeout + D5-freigebende Beweiswoche
  - ../phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md # 📕 Beweiswoche-Befund (B1/B2/B3) + §8 Pfad-C-Nachtrag
  - ../phase12_data_foundation/PHASE12_CLOSEOUT_HANDOVER.md # 📕 Pattern-Vorbild-Alt (Phase-12-Closeout)
  - ../docs/architecture/phase13_live_data.svg      # 📕 Schwester-Phase-Bild (nicht Phase-14-spezifisch)
  - ./SESSIONS_ARCHIVE.md                           # 📦 rotierte Session-Blöcke (L3)
updated: 2026-08-31
---
# Phase 14 (Discovery-Then-Deterministic) — Closeout-Handover (2026-08-31)

> **Autor:** Claude Code, Read-only-Analyse 2026-08-31, **kein** Produktionscode-Edit
> in dieser Session. **Adressat:** die nächste Session an Phase 14 (Folge-Arbeit) oder
> an Phase 15 (V4). **Quelle aller Zahlen:** eigene read-only-Abfragen gegen die
> SQLite-DBs, Git-Historie, Tests, und Cross-Phase-File-Inventur — **nichts** aus
> Vordokumenten übernommen, was sich selbst hat prüfen lassen.

---

## §0 BLUF

Phase 14 ist **abgeschlossen**. Code-complete (Blöcke 0/A/B/C/D, Akzeptanz A1–A8 alle
grün seit Session 9) + D5-Handover komplett freigegeben (Mini-Session 24, Pfad-C-
Entscheidung 2026-08-31) + 4 Mini-Pläne P14-C/D/E/F abgeschlossen. **54 Phase-14-
Commits auf `origin/main`, 61 Phase-14-Tests grün (heute gemessen), 38 Zeilen in
`instrument_source_availability`, Σ 1703 grün repo-weit, `main` = `origin/main`.**

**Drei Sätze, die die Phase tragen:**

1. **Discovery first.** Jede Quelle exponiert ihr Liefer-Spektrum als `SourceProfile`
   (strukturell ohne Netz — Broker-Fake wirft auf jeder Methode, Test grün).
2. **Kreuzung second.** `instrument_source_availability` (Migration 007) hält
   `IG-Epic × Quelle × Auflösung × source_symbol × status × origin × last_verified_utc`
   — inklusive des quelleneigenen Symbols.
3. **Determinism last.** Konsumenten lesen die Tabelle, nicht den Code. Hinzufügen
   einer Quelle ist eine Konfigurationszeile, kein Code-Deploy.

**5-Zeilen-Bilanz (heute 2026-08-31, selbst nachgemessen):**

| Zeile | Stand 2026-08-31 |
|---|---|
| **fertig gestellt** | Blöcke 0 (Konzept + Plan), A (Registry + Migration 007 + Stores + Quell-Profile), B (`EPIC_MAP` raus + Symbol-Lookup in Phase-13-Backfill + CFD-Filter-Bug-Fix + Drei-Fälle-`source_delta`), C (Discovery-Daemon + ARM-Flag + WebUI + Scheduler-Hook), D (Doku-Updates + Σ-Sweep + Modul-Tabelle); P14-C (Daemon-CWD-Bug, 2026-08-26), P14-D (Daemon-Signal-Cap, 2026-08-26 + §10 Korrekturnotiz 2026-08-31), P14-E (Recorder-Sleep-Cap + Restart-Loop-Hunt, 2026-08-28), P14-F (Doc-Rotation-Hook `--strict`, 2026-08-31); D5-Handover komplett freigegeben (Mini-Session 24). |
| **getestet** | **61 Phase-14-Unit-Tests grün** (heute 2026-08-31 gemessen; Σ = 13 + 9 + 21 + 18; **unverändert** seit Mini-Session 21 — P14-F brachte Tests in `tests/test_check_doc_rotation.py` = 21 Tests, lebt aber im root-`tests/`-Verzeichnis, nicht in `phase14_discovery/tests/`). Σ **1703 grün** repo-weit (war 1698 in Session 9; **+5** durch Mini-Sessions 22+24: P14-F Step-2 Tests + 7 root tests; Phase-14-interne Suite unverändert). |
| **live validiert** | Block A Strukturell (`test_get_window_never_fetches` Pattern, IG-Provider wirft auf jeder Methode, Test grün). Block B1a (`probe_capital.py`-Probe gegen Capital.com Demo, 2026-08-22). Block B0 Pfad A Probe (`scripts/probe_chart_stream.py`, 2026-08-19 — NO für CHART-Pfad). Block C Live (Daemon-PID 10741 → SIGTERM-CAP-Verify ≤ 60 s, Mini-Session 21, 2026-08-31). Block C WebUI (`GET /api/discovery` + ARM/DISARM-Endpoint, fail-soft ohne Tabelle 007 getestet). |
| **gepusht und committet** | `main` synchron mit `origin/main`. **54** `phase14:`-Commits auf origin (war 18 in Session 9; **+36** durch Mini-Sessions 21–24: Block-D Schließung `362f4b9` + `b16aea8` + `5d587a0`, P14-F Sub-Plan + Doku-Indizierung `76a56f5` + `8db5a1c`, Pfad-C-Entscheidung + D5-Hook-Verschärfung `9600d79` + `c4f7d9c`, Phase-13-Beweiswoche-Befund-Indizierung, Phase-13-Closeout `0ff55d2`, Phase-7-Plan-File-Track `2923096`, Phase-7-CLAUDE.md-Mini-Session-26⅔ `2e1cc13` + `bec6b87`). 0 unpushed lokal. |
| **nicht erreicht / offen geblieben** | (a) **P15-V4-Plan-Session** — Material jetzt vollständig (Pfad A, Pfad B aufgehoben solange C, Quellen-Vertrauens-Modell, Council-Paper-Call, Reward-Reform, Force-Trigger, Instinct-ECC). (b) **Dukascopy-ToS** — Phase-14 macht daraus eine Quell-Registry-Zeile, kein Backfill-Code (L15). (c) **Auto-Gap-Fill-Scheduler** (Cron-Logik, tägliche Lücken ≥ 60 min schließen) — bewusst nicht implementiert (Plan §10 Out-of-Scope). (d) **Phase-13-closeout.svg / Phase-14-closeout.svg** — beide bewusst aufgeschoben, Empfehlung: gemeinsam mit Phase-15 als `phase13_14_15.svg`-Gesamtbild. |

---

## §1 Architektur-Bild (in einer Zeile)

```
┌────────────────────────────────────────────────────────────────────────┐
│ Konsument (Research / PaperTracker / DivergenceSampler / WebUI)        │
│ liest NUR die Tabelle ↓                                                 │
└────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌────────────────────────────────────────────────────────────────────────┐
│ instrument_source_availability  (Migration 007, 38 Zeilen, 3 Quellen)  │
│   ig: 8  ls: 8  yf: 22                                                 │
│   Spalten: epic, source, resolution, source_symbol, status, origin,    │
│            last_verified_utc                                           │
└────────────────────────────────────────────────────────────────────────┘
            ↑ befüllt von                                       ↑
┌────────────────────────────┐         ┌──────────────────────────────┐
│ SourceProfile (Registry)   │         │ Discovery-Daemon             │
│ IGDerivedSource (kein Netz)│         │ arm.py → data/state/         │
│ LSStaticSource (kein Netz) │         │   DISCOVERY_ARMED            │
│ RegistryYFSource (kein Netz)         │ run.py mit signal_check_     │
│ SourceAvailabilityStore   │         │   interval_s (P14-D-Fix)     │
└────────────────────────────┘         └──────────────────────────────┘
```

Discovery ruft **nie** `/prices` und **nie** `search_markets`. Die IG-Zeile wird aus
`instrument_universe` **abgeleitet** — jede Zeile dort *ist* per Definition eine
IG-Epic. Beweis: Broker-Fake wirft auf jeder Methode (`test_sources.py` Test 2, das
A1-Akzeptanzkriterium).

---

## §2 Locks (D1–D20, „don't re-litigate")

Vollständige Liste aus [`../docs/concepts/phase14_discovery_plan.md`](../docs/concepts/phase14_discovery_plan.md)
§1; je Zeile mit Begründung verlinkt auf den Plan-Snapshot. Hier nur die kompakten
Locks, die in Folge-Sessions am ehesten re-litigiert werden:

| # | Was gelockt ist | Warum |
|---|---|---|
| **D1** | Quell-Profile sind der erste Schritt. Ohne Profil keine Tabelle. | Plan-Snapshot §2 + Q1. |
| **D2** | `instrument_source_availability` ist die einzige Kreuzungs-Wahrheit. | Plan-Snapshot §2 + Q2. |
| **D3** | Discovery ruft nie `/prices`, nie `search_markets`. IG-Zeile aus `instrument_universe`-Ableitung. | A1-Akzeptanz + Test 2 in `test_sources.py`. |
| **D4** | Konsumenten lesen die Tabelle, nicht den Code. | D1+D2-Konsequenz. |
| **D5** | Cross-Phase-Edits brauchen eine eigene Nikinger-Freigabe; die freigegebene Liste (Phase 2/8/9/12/13; Phase 7 ab 2026-08-31 via Mini-Session 26) gilt weiter. | Plan-Snapshot §4. |
| **D6** | `profile_ttl_days=7` + `max_probe_calls_per_source_per_run=8` + jede Probe als `spend_kind='discovery'` im `source_spend`-Ledger. | Kontingent-Deckel, Plan-Snapshot §4. |
| **D7** | `BarArchive.window` bekommt `prefer`-Filter (was die Tabelle heute ist). | L10 erweitert. |
| **D8** | `EPIC_MAP` ist weg. Symbol-Lookup gegen `instrument_source_availability.source_symbol`. | A2-Akzeptanz (`grep EPIC_MAP phase13_live_data/ --include=*.py` leer). |
| **D9** | `stale_source`-Vokabular im DS-Layer. | Live-Blocker B1 (Phase-9-Regression), Mini-Session 21. |
| **D10** | Daemon tut nichts ohne `data/state/DISCOVERY_ARMED`. Sichere Richtung: **unscharf**. | Block C, Session 9. |
| **D11** | ARM-Flag hat absoluten Pfad (`parents[2]`-Muster). | P14-C, 2026-08-26. |
| **D12** | Daemon-Sleep zwischen Cycles ist `signal_check_interval_s`-gecapped (Default 60 s). | P14-D, 2026-08-26. |
| **D13** | Recorder-Sleep zwischen Cycles ist `signal_check_interval_s`-gecapped (Cross-Phase-Phase-12). | P14-E, 2026-08-28. |
| **D14** | `stale_source`-Status triggert `DS_STALE_SOURCE` im DS-Layer, nicht einen Throw. | A1-Akzeptanz. |
| **D15** | Dukascopy ist Mock-only (Tabelle kennt die Zeile, `fetch` wirft `NotImplementedError`). | E3-Entscheidung, Plan-Snapshot §5. |
| **D16** | Auto-Gap-Fill-Scheduler ist Phase-15-Territorium (Cron-Logik, tägliche Lücken ≥ 60 min). | Plan-Snapshot §10 Out-of-Scope. |
| **D17** | `KNOWN_SOURCES` bleibt statisch im Code (nicht dynamisch aus DB). | Plan-Snapshot §10 Out-of-Scope. |
| **D18** | `TickerMapper`-Cache ist Phase-9-Territorium (Cross-Phase-Touch braucht eigene Freigabe). | Plan-Snapshot §10 Out-of-Scope. |
| **D19** | IG-Default AUS als Live-Quelle (Phase-13-L18, Pfad-C-Entscheidung). | Mini-Session 24, Phase-13-Findings §8.1. |
| **D20** | Phase-14 ist die **Brücke** zwischen Datenfundament (Phase 13) und AI-Sophistication (Phase 15). V4 setzt voraus, dass die Daten-Infrastruktur konfigurierbar ist. | Plan-Snapshot §1. |

---

## §3 Akzeptanz A1–A8 (alle grün seit Session 9, 2026-08-22)

| # | Kriterium | Beleg | Stand |
|---|---|---|---|
| **A1** | Discovery gibt strukturell 0 IG-Punkte aus | `test_sources.py::test_2` (Broker-Fake wirft auf jeder Methode); `grep -rn EPIC_MAP phase13_live_data/ --include=*.py` ist leer | ✅ seit Session 9 |
| **A2** | `grep EPIC_MAP phase13_live_data/*.py` ist leer | Phase-13-Backfill nutzt Symbol-Lookup | ✅ seit Session 9 |
| **A3** | `measurable_universe()`-Identität (vor/nach Phase-14-Tabelle) | +6 Tests in `phase9_universe/tests/test_store.py` | ✅ seit Session 9 |
| **A4** | yF-Projektion in `set_symbol` (nicht-fatal) | +6 Tests in `phase9_universe/tests/test_store.py` | ✅ seit Session 9 |
| **A5** | Daemon unscharf = nichts | `test_run.py` (Daemon-Pattern: 18 Tests) | ✅ seit Session 9 |
| **A6** | UI warnt + scharf per Datei | `phase8_scheduler/webui/api.py` (`GET /api/discovery` + ARM/DISARM, +4 Tests in `phase8_scheduler/tests/test_webui.py`) | ✅ seit Session 9 |
| **A7** | `source_delta.py` Drei-Fälle-Trennung (`not_available` / `available_but_empty` / `compared`) | +4 Tests in `phase13_live_data/tests/test_source_delta.py` | ✅ seit Session 9 |
| **A8** | Σ-Sweep 1659→1698 (heute 1703; +5 durch P14-F + Phase-7-Backoff) | Σ-Sweep Stand 2026-08-31 | ✅ seit Session 9 |

**Akzeptanz-Status 2026-08-31:** alle 8 grün. **Block-D ✅** (Mini-Sessions 21+22+23+24):
- Mini-Session 21: P14-D §10 Korrekturnotiz + Modul-Tabelle + P14-E Test-Fix + Doc-Rotation Session 20 → Archiv.
- Mini-Session 22: P14-F Sub-Plan (Doc-Rotation-Hook Schritt 2: `check_archive_sequence` + `--strict`-Flag + 7 Tests A1–A6 + Tracked-Installer `scripts/install_hooks.sh` + `dev_install.sh`-Anbindung).
- Mini-Session 23: Phase-13-Beweiswoche-Befund-Indizierung in Phasenkopf + INDEX.
- Mini-Session 24: P14-F D5-Ausnahme (Hook-Verschärfung auf `--strict`-Default nach D5-Beweis).

---

## §4 As-Built-Zahlen (heute 2026-08-31, read-only)

### §4.1 Modul-Inventar (Phase-14)

| Kategorie | Anzahl | Bemerkung |
|---|---:|---|
| Source-Files (`source_registry/*.py`) | **5** | `__init__.py`, `models.py`, `store.py`, `sources.py`, `arm.py`, `run.py` |
| Skript-Files (`scripts/run_discovery.sh`) | **1** | Bash-Wrapper, kein Python-Test |
| Test-Files (`tests/*.py`) | **5** | `__init__.py`, `test_store.py` (13 T), `test_sources.py` (9 T), `test_arm.py` (21 T), `test_run.py` (18 T) |
| Phase-14-Tests grün | **61** | **unverändert** seit Mini-Session 21 (13+9+21+18=61) |
| Σ repo-weit grün | **1703** | war 1698 in Session 9; +5 (root tests/ +7 [P14-F Step-2], −2 Phase-13-Test-Korrektur) |

### §4.2 `instrument_source_availability` (heute, read-only gegen `data/trading_bot.sqlite`)

```
Total: 38 Zeilen
ig: 8 Zeilen
ls: 8 Zeilen
yf: 22 Zeilen
```

**Anmerkung:** die 8 IG-Zeilen sind alle aus `instrument_universe` abgeleitet
(Origin='derived'). Sie zeigen **nicht** „IG liefert heute Bars" — sie zeigen
„Discovery hat diese IG-Epic bestätigt" (= semantisch korrekt unter Pfad C,
Phase-13-L18 + L19). Die yF-Zeilen (22) sind die echten Backfill-Reproduktionen
aus der Migration; ls-Zeilen (8) sind statisch aus `KNOWN_SOURCES`.

### §4.3 Phase-14-Commits auf `origin/main` (54 total)

Erste Commits (Phase-14-Open, 2026-08-22): Block 0/A Setup, Migration 007, Stores.
Letzte Commits (heute 2026-08-31): Phase-13-Closeout-Folgewirkung (Status-Pflege),
Doc-Rotation Session-22→Archiv, Phase-7-Plan-File-Track, Phase-7-CLAUDE.md-26⅔.
**Pattern:** kontinuierlicher Strom von Mini-Session-Doku-Commits, kein großer
Block-Commit nach Session 9.

### §4.4 Live-Verify-Eintrag (unverändert seit Block C Re-Plan 2026-08-22)

```
CAP-Verify live (Mini-Session 21, PID 10741 → Exit in 46 s, ≤ 60 s CAP).
```

### §4.5 Cross-Phase-Phase-14-Effects (Tests beigetragen zur Eigentümer-Phase)

| Eigentümer-Phase | +Tests durch Phase-14 | Heute | Δ |
|---|---:|---:|---:|
| Phase 2 (Persistence) | 2 (Migration-007-Tests in `test_store.py`) | 77 | 0 |
| Phase 8 (Scheduler) | 4 (WebUI ARM/DISARM in `test_webui.py`) | 248 | 0 |
| Phase 9 (Universe) | 7 (DS_STALE_SOURCE + yF-Projektion in `test_store.py`) | 87 | 0 |
| Phase 13 (Live-Daten) | 8 (B1b/B2/B3 in `test_backfill.py`/`test_source_delta.py`/`test_probe_capital.py`) | 74 | 0 |

**Σ-Tests beigetragen:** 21, verteilt auf 4 Cross-Phase-Suites. Alle bleiben bei
ihren Eigentümer-Phasen gemessen, nicht in Phase-14.

---

## §5 Was bewiesen ist vs. was nicht (Test vs. Live vs. Produktion)

| Artefakt | Beweis-Art | Beleg |
|---|---|---|
| **D3 + A1: Discovery gibt 0 IG-Punkte aus** | **Strukturell, Test** | `phase14_discovery/tests/test_sources.py` Test 2 (Broker-Fake, wirft auf jeder Methode). |
| **A2: EPIC_MAP ist weg** | **Strukturell, Grep** | `grep -rn "EPIC_MAP" phase13_live_data/ --include=*.py` ist leer (Akzeptanz A2). |
| **A3: measurable_universe()-Identität** | **Test, Bit-Identität** | +6 Tests in `phase9_universe/tests/test_store.py` (Bit-Identität mit `SourceAvailabilityStore.upsert`). |
| **A5: Daemon unscharf = nichts** | **Test, Pattern** | `phase14_discovery/tests/test_run.py` (18 Tests, P14-D CAP-Test inkludiert). |
| **A6: WebUI ARM/DISARM + Warn-Banner** | **Test, fail-soft** | +4 Tests in `phase8_scheduler/tests/test_webui.py` (inkl. fail-soft ohne Tabelle 007). |
| **A7: source_delta.py Drei-Fälle** | **Test, Coverage** | +4 Tests in `phase13_live_data/tests/test_source_delta.py` (`not_available`/`available_but_empty`/`compared`). |
| **A8: Σ-Sweep 1703 grün** | **Test, gemessen** | Heute 2026-08-31, alle 13 Phasen + root tests/ = 1703 passed, 0 fails. |
| **P14-C: ARM-Flag absoluter Pfad** | **Test, CWD-Unabhängigkeit** | Regressionstest in `phase14_discovery/tests/test_arm.py`. |
| **P14-D: Daemon-Signal-Cap** | **Test, Stop-Latenz** | CAP-Test in `phase14_discovery/tests/test_run.py`; Live-Verify PID 10741 → Exit in 46 s. |
| **P14-E: Recorder-Sleep-Cap** | **Test, Cross-Phase-Phase-12** | +2 Tests in Phase-12-Test-Suite (analog P14-D). |
| **P14-F: Doc-Rotation-Hook `--strict`** | **Test, 7 neue Tests A1–A6** | `tests/test_check_doc_rotation.py` (21 Tests, lebt im root `tests/`). |
| **`stale_source`-Vokabular (Phase-9-Phase-14-Schnittstelle)** | **Test, +1 Regression** | `phase9_universe/universe/models.py::DS_STALE_SOURCE`. |
| **B1a Probe: Capital.com liefert** | **Live, 2026-08-22** | `phase14_discovery/PHASE14_B1A_PROBE_OUTPUT_2026-08-22.md` (8 nummerierte Befunde). |
| **D5-Handover komplett freigegeben** | **Live + Architektur** | Mini-Session 24, Pfad-C-Entscheidung (Phase-13-Findings §8.1); Phase-13-CLOSE-OUT Handover `0ff55d2` bestätigt. |
| **P14-F `--strict`-Hook-Default** | **Live**, alle 14 Phasenarchive Step-2-konform | Mini-Session 24, Commit `c4f7d9c`. |

---

## §6 Delta seit Mini-Session 22 (Phase-14 NEXT-Block-Stand)

Letzter Phase-14-Session-Block: `phase14_discovery/CLAUDE.md` Z. 143 (Mini-Session 22,
P14-F Doc-Rotation-Hook Schritt 2, 2026-08-31). Was sich seitdem geändert hat:

### §6.1 Phase-13-Closeout entsperrt Phase-14-Closeout (Commit `0ff55d2`, 2026-08-31)

Die Phase-14-D5-Handover-Blockade war strukturell an die Phase-13-Beweiswoche +
Pfad-C-Entscheidung gekoppelt (Phasenkopf Z. 244: „Phase-14 D5 Closeout-Handover —
wartet auf Phase-13-Beweiswoche"). Mit Phase-13-CLOSE-OUT am 2026-08-31
(Session 18) ist diese Blockade aufgehoben: Beweiswoche gelaufen, Pfad C entschieden,
Befund-Inversion dokumentiert.

### §6.2 P14-F Doc-Rotation-Hook Schritt 2 (Mini-Sessions 22+24, 2026-08-31)

- 4 Commits (`94e0c35`, `d32e93a`, `8fe439c`, `8db5a1c`): Tool-Erweiterung +
  7 Tests + Tracked-Installer + dev_install.sh-Anbindung.
- 1 Commit (`c4f7d9c`): Hook-Verschärfung auf `--strict`-Default nach D5-Beweis.
- Repo-weit heute: alle 14 Phasenarchive Step-2-konform (D5-Beweis erbracht in
  Mini-Sessions 22+23).

### §6.3 Phase-7-Plan-File-Tracking nachgeholt (Commits `2923096` + `2e1cc13` + `bec6b87`)

Die `phase7_reward/PHASE12_RECONCILIATION_TIMING_PLAN.md` war seit Mini-Session 26
working-tree-Leftover. Session 18 hat das nachgeholt + in Phase-7-CLAUDE.md als
Mini-Session 26⅔ dokumentiert. **Kein** Phase-14-Code-Touch.

### §6.4 Cross-Phase-Test-Bilanz (unverändert seit Mini-Session 21)

Phase 14 hat 21 Cross-Phase-Tests beigetragen, alle bei den Eigentümer-Phasen (P2/P8/P9/P13)
gemessen. Σ-Sweep 1703 grün, kein Cross-Phase-Code-Edit in dieser Session.

### §6.5 Self-Messung, nicht aus Vordokumenten

- `find phase14_discovery/source_registry -name "*.py"` (non-`__pycache__`): **6** Source-Files
- `find phase14_discovery/tests -name "*.py"`: **5** Test-Files (inkl. `__init__.py`)
- `pytest phase14_discovery/tests -q` (heute): **61 passed**
- `git log --grep='^phase14:'` lokal: **54** (identisch mit origin), 0 unpushed
- `git log origin/main --grep='^phase14:'`: **54**
- `SELECT COUNT(*) FROM instrument_source_availability`: **38** Zeilen (8 ig + 8 ls + 22 yf)
- Σ-Sweep (alle 13 Phasen + root tests/): **1703 grün, 0 fails**

---

## §7 Offene Entscheidungen (mit Empfehlung — Status 2026-08-31)

| # | Entscheidung | Optionen | Empfehlung | Stand 2026-08-31 |
|---|---|---|---|---|
| **D5-H.** | Phase-14-Final-Closeout — jetzt oder später | (a) jetzt nach Phase-13-CLOSE-OUT; (b) warten auf Phase-15-Plan-Session | **(a) jetzt** | **erledigt durch diese Closeout-Session** (Pattern Phase-12/13, ~1h) |
| **D5-H.-A** | IG-Default (Pfad A/B/C) | (a) Pfad A — Operator-S4-Aktivierung; (b) Pfad B — Schema-Reinterpretation; (c) Pfad C — Default AUS | **(c) Pfad C** | **erledigt** (Mini-Session 24, L19 + Phase-13-L18); Pfad A als P15-V4-Kandidat, Pfad B aufgehoben solange C |
| **D5-H.-B** | Quellen-Vertrauens-Modell-Framing | (a) Aktualitäts-Modell; (b) Verfügbarkeits-Modell | **(b) Verfügbarkeits-Modell** | **offen für P15-V4-Plan-Session** (V4 entscheidet `last_verified_utc`-Semantik) |
| **D5-H.-C** | Auto-Gap-Fill-Scheduler | (a) Phase-14; (b) Phase-15 (Cron-Logik); (c) eigener Track | **(b) Phase-15** | **offen für P15** (D16, Plan §10 Out-of-Scope) |
| **D5-H.-D** | Dukascopy-Code in Phase-14 | (a) Ja; (b) Nein; (c) Mock-only | **(c) Mock-only** | **erledigt** (D15, E3) |
| **D5-H.-E** | Profil-Cache-TTL | (a) täglich; (b) wöchentlich; (c) on-demand | **(b) wöchentlich** | **erledigt** (`profile_ttl_days=7`, D6) |

---

## §8 Datei-Anker

**Zuerst lesen:**
- [`./CLAUDE.md`](./CLAUDE.md) — Phasenkopf + neuester Session-Block (Session 23 nach dieser Closeout)
- [`../docs/concepts/phase14_discovery_plan.md`](../docs/concepts/phase14_discovery_plan.md) — der frozen Plan (📕, „never edit"); D1–D20 (alle gelockt), §11 Korrekturnotizen
- [`../docs/concepts/phase14_discovery_concept.md`](../docs/concepts/phase14_discovery_concept.md) — Concept-Skizze (vom Plan Q1–Q7 beantwortet)
- [`../docs/architecture/phase13_live_data.svg`](../docs/architecture/phase13_live_data.svg) — Schwester-Phase-Bild (nicht Phase-14-spezifisch)

**Mini-Pläne (P14-C, P14-D, P14-E, P14-F):**
- [`./PHASE14_C_DAEMON_CWD_BUG_PLAN.md`](./PHASE14_C_DAEMON_CWD_BUG_PLAN.md) — P14-C, Discovery-Daemon-CWD-Path-Bug, 2026-08-26
- [`./PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md`](./PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md) — P14-D, Discovery-Daemon-Signal-Response-Bug, 2026-08-26 + §10 Korrekturnotiz 2026-08-31
- [`./PHASE14_E_RECORDER_LOOP_PLAN.md`](./PHASE14_E_RECORDER_LOOP_PLAN.md) — P14-E, Recorder-Sleep-Cap-Bug + Restart-Loop-Hunt, 2026-08-28 + §2 D3-Korrekturnotiz
- [`./PHASE14_F_DOC_ROTATION_HOOK_STEP2_PLAN.md`](./PHASE14_F_DOC_ROTATION_HOOK_STEP2_PLAN.md) — P14-F, Doc-Rotation-Hook Schritt 2, 2026-08-31
- [`./PHASE14_B1A_PROBE_OUTPUT_2026-08-22.md`](./PHASE14_B1A_PROBE_OUTPUT_2026-08-22.md) — B1a Probe-Snapshot (Capital.com `/markets`-Rohdaten)

**Die strukturelle Antwort, die Phase 14 abgelöst hat:**
- [`../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md`](../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md) — Pattern-Vorbild Phase-13-Closeout, D5-freigebende Beweiswoche + Pfad-C-Entscheidung
- [`../phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md`](../phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md) — Beweiswoche-Befund (B1/B2/B3) + §8 Pfad-C-Nachtrag
- [`../phase12_data_foundation/PHASE12_CLOSEOUT_HANDOVER.md`](../phase12_data_foundation/PHASE12_CLOSEOUT_HANDOVER.md) — Pattern-Vorbild-Alt (Phase-12-Closeout)

**Die Cross-Phase-Nähte, die Phase 14 dem Restprojekt gegeben hat (Code ist Wahrheit — hier nur Wegweiser):**
- `phase14_discovery/source_registry/`: `models.py` (`SourceAvailability`/`SourceProfile`/`origin`-Vokabular), `store.py` (`SourceAvailabilityStore`, einziger Zugriff auf Migration 007), `sources.py` (drei Quell-Profile strukturell ohne Netz), `arm.py` (Scharf-Flag mit absoluten Pfaden, D11), `run.py` (Daemon mit `signal_check_interval_s`-Cap, D12)
- `phase2_persistence/migrations/007_phase14_source_availability.sql` — Migration 007 (Kreuzungs-Tabelle + einmaliger yF-Backfill aus `instrument_universe`)
- `phase9_universe/universe/models.py` — `DS_STALE_SOURCE` ins Vokabular (D9, Live-Blocker B1)
- `phase9_universe/universe/store.py` — yF-Projektion in `set_symbol`, nicht-fatal (D2 + A4)
- `phase13_live_data/live_data/backfill.py` — `CapitalSource.discover()` (B1b); `EPIC_MAP` raus + Symbol-Lookup rein (D8 + A2)
- `phase13_live_data/scripts/probe_capital.py` — CFD-Filter-Bug Fix (`"CFD"`-Substring → exakt `"INDICES"`)
- `phase13_live_data/scripts/source_delta.py` — drei Fälle statt zwei (`not_available` / `available_but_empty` / `compared`, A7)
- `phase8_scheduler/webui/api.py` + `static/` — `GET /api/discovery` + ARM/DISARM-Endpoint + Warn-Banner (A6)
- `phase8_scheduler/scripts/run_scheduler.sh` — Autostart-Hook für `run_discovery.sh` (Block C4b)
- `scripts/run_discovery.sh` — Bash-Wrapper für den Daemon
- `scripts/check_doc_rotation.py` — Doc-Rotation-Hook Schritt 1 + 2 (P14-F; `--strict`-Default nach D5-Beweis, Mini-Session 24)
- `scripts/install_hooks.sh` — Tracked-Installer für den Pre-Commit-Hook (P14-F)
- `scripts/dev_install.sh` — `install_hooks.sh`-Anbindung am Ende der 13 `pip install -e`-Schritte (P14-F)
- Cross-Phase-Phase-12: `phase12_data_foundation/data_foundation/recorder.py` — Recorder-Sleep-Cap (P14-E)
- Cross-Phase-Phase-7: `phase7_reward/PHASE12_RECONCILIATION_TIMING_PLAN.md` endlich tracked (Mini-Session 26⅔, Commit `2923096`)

**Historie, nur bei Bedarf:** `phase12_data_foundation/PHASE12_5_FAILURE_HANDOVER.md`
(Sofort-Befund), `phase10_v3/PHASE11_DEFERRAL_HANDOVER.md` (warum dieser Track
entstanden ist), `./SESSIONS_ARCHIVE.md`.

---

## §9 Konsistenz-Regeln, die Phase-14-Code aufstellt (nicht antasten, ohne Not)

1. **NULL neues AI in Phase 14.** Quell-Entdeckung, Symbol-Zuordnung, Verfügbarkeits-
   Bewertung und Scharfschalt-Logik sind deterministischer Code. Phase 14 fügt keine
   AI-Naht hinzu. Wer das anfasst, bricht den Plan-§1-Vertrag.

2. **Eine Wahrheit pro Quelle-Epic-Kreuzung** (D2). `instrument_source_availability`
   ist die einzige Quelle für „welche Quelle kann welche Epic?". **Drei Speicher
   wären eine Regression.**

3. **Discovery ruft nie `/prices`, nie `search_markets`** (D3). IG-Zeile aus
   `instrument_universe`-Ableitung. Beweis: `test_sources.py` Test 2 (Broker-Fake
   wirft auf jeder Methode). Wer eine `if`-Verzweigung einbaut, die IG-REST ruft,
   **sprengt den A1-Akzeptanz-Test**.

4. **`EPIC_MAP` ist weg** (D8 + A2). Symbol-Lookup gegen `instrument_source_availability.source_symbol`.
   `grep -rn "EPIC_MAP" phase13_live_data/ --include=*.py` ist leer. Wer das Dict
   wieder einführt, **rollt den Backfill-Bug wieder rein**.

5. **`stale_source`-Vokabular im DS-Layer** (D9 + D14). Trigger nicht throw, sondern
   Status. Wer einen Throw einführt, **rollt den Live-Blocker B1 wieder rein**.

6. **ARM-Flag hat absoluten Pfad** (D11, P14-C). CWD-Unabhängigkeit per
   `parents[2]`-Muster. Wer einen relativen Pfad einbaut, **bricht P14-C-Akzeptanz A1–A6**.

7. **Daemon-Sleep zwischen Cycles ist `signal_check_interval_s`-gecapped** (D12, P14-D).
   Default 60 s. Strukturell analog zum Phase-8-POST_WINDOW-Bug. Live-Verify: PID
   10741 → Exit in 46 s (≤ 60 s CAP). Wer den Cap entfernt, **bricht die Operator-Restart-Pfad-Sicherheit**.

8. **Recorder-Sleep zwischen Cycles ist `signal_check_interval_s`-gecapped** (D13, P14-E).
   Cross-Phase-Phase-12. Wer den Cap entfernt, **bricht die Recorder-Restart-Pfad-Sicherheit**
   (15-h-Datenverlust-Vorfall aus Session 19).

9. **Ressourcen sind modelliert** (D6). `profile_ttl_days=7` +
   `max_probe_calls_per_source_per_run=8` + jede Probe als `spend_kind='discovery'`
   im `source_spend`-Ledger. Wer den Deckel entfernt, **sprengt das 10 000/Woche-
   IG-Kontingent** (P12.5-Lektion).

10. **IG-Default AUS als Live-Quelle** (D19, Phase-13-L18). IG ist nur als S4-
    GapRescue-Pfad designed (operator-getriggert, budget-bound). Wer IG als
    kontinuierliche Live-Quelle einbaut, **rollt den P12.5-Fail wieder rein**.

11. **Dukascopy ist Mock-only** (D15, E3-Entscheidung). Tabelle kennt die Zeile,
    `fetch` wirft `NotImplementedError`. Wer echten Dukascopy-Code einbaut, ohne
    P15-Freigabe, bricht den ToS-Vertrag.

12. **Doc-Rotation-Hook `--strict` als Default** (P14-F, Mini-Session 24). Nach
    D5-Beweis. Wer ihn auf non-strict zurückdreht, **re-litigiert einen Drift, den
    die Repo-weit-Konformität bereits gelöst hat**.

13. **Momentum-VETO bleibt unangetastet** (Phase-13-L13). Sourct direkt aus P1-IG-
    Echtzeit-Bars, nie aus `BarService`/`bar_archive`/yF/`instrument_source_availability`.
    Wer das umstellt, bricht den D16-Vertrag (Phase-13).

---

## §10 Was die nächste Session **nicht** tun soll

- **Keine** Re-Aktivierung der Pfad-A-IG-Live-Quelle ohne P15-V4-Freigabe. D19
  (Phase-13-L18) bleibt gelockt; wer IG als kontinuierliche Live-Quelle braucht,
  holt eine eigene P15-V4-Freigabe.

- **Keine** Code-Edits an `source_registry/`, die eine der 13 Konsistenz-Regeln
  aus §9 verletzen. Besonders: keine direkten IG-Fetches im Discovery; keine
  `EPIC_MAP`-Wieder-Einführung; keine Schema-Reinterpretation (Pfad B) solange
  Pfad C gilt; keine Modifikation am `signal_check_interval_s`-Cap (D12/D13).

- **Keine** Schema-Migrationen, die `instrument_source_availability` umstrukturieren
  (Pfad B) solange Pfad C gilt. Pfad B ist in Phase-13-Findings §8.2 als P15-V4-
  Kandidat aufgehoben — V4 entscheidet, nicht Phase-14.

- **Keine** Code-Edits an Cross-Phase-Files außerhalb der freigegebenen Liste
  (Phase 2, Phase 7 ab 2026-08-31, Phase 8, Phase 9, Phase 12, Phase 13). Wer
  Phase 14 auf eine andere Cross-Phase-Liste erweitern will, holt eine eigene
  Nikinger-Freigabe.

- **Kein** Doc-Rotation-Hook-Reflex (P14-F) auf non-`--strict` zurückdrehen.
  Wer das tut, **re-litigiert einen Drift, den die Repo-weit-Konformität gelöst hat**.

- **Kein** Scheduler-/Daemon-/Recorder-Restart für Messzwecke. Phase 14 ist
  abgeschlossen; was die Daemons noch bewegt, ist Lifecycle, nicht Phase-14-Validation.

- **Keine** Duplikation von Phase-14-Wissen an einer anderen Stelle: das
  Closeout-Handover hier, der Phasenkopf dort, die fünf Mini-Pläne als
  Mini-Plan-Snapshots, das B1a-Probe-Snapshot, die vier Schwester-Phase-Closeouts
  (Phase 8/10/12/13) als Pattern-Vorbilder — sieben Quellen, sieben Rollen, keine
  neuen Achten. Wer ein neues Doku-File zu Phase 14 anlegt, soll vorher prüfen,
  ob eine der sieben Rollen es trägt.

- **Kein** Phase-14-SVG (analog zu Phase-12-`phase12_closeout.svg`). Phase-14 hat
  ein Architektur-Bild in §1 (ASCII), aber kein separates SVG. Empfehlung:
  Phase-15-Plan-Session zeichnet ein gemeinsames `phase13_14_15.svg`-Gesamtbild.

- **Kein** Auto-Gap-Fill-Scheduler in Phase 14 (D16, Plan §10). Wer das baut,
  ohne P15-Freigabe, bricht die Out-of-Scope-Konvention.

---

## §11 Was diese Session gemacht hat — und was nicht

**Diese Session (2026-08-31, ~13:00–14:00 UTC, Session 23 auf Phase 14, diesmal
Read-only + Closeout-Propagation):**
- As-Built gegen Code, Tests, Git-Historie, `data/trading_bot.sqlite` (mode=ro)
  selbst nachgemessen.
- Phase-14-Status ehrlich: **Code-complete + Akzeptanz A1–A8 alle grün seit
  Session 9 + D5-Handover komplett freigegeben + 4 Mini-Pläne abgeschlossen**.
  Phase 14 ist abgeschlossen.
- 20 Locks (D1–D20) sauber differenziert: D1–D18 aus dem Mutterplan, D19 (IG-
  Default-AUS, Phase-13-L18) als Cross-Phase-Erweiterung, D20 (Phase 14 als
  Brücke zur Phase 15) als Mission-Lock.
- A1–A8-Akzeptanz-Status explizit dokumentiert; jeder mit Beleg (Test-/Live-
  Verweis).
- 13 Konsistenz-Regeln gelockt (zwei mehr als Phase-13 hat: §9.6 ARM-Pfad absolut,
  §9.12 Doc-Rotation-Hook-`--strict`).
- Status pflegepropagiert in diesem einen Commit: Root-`CLAUDE.md` (Phase-14-Row:
  `🔄 Blöcke 0+A+B+C code-complete → ✅ abgeschlossen (Closeout 2026-08-31,
  Session 23)`, Closeout-Handover-Link, D5-Handover-Vermerk); `ROADMAP.md`
  (Phase-14-Header gleicher Status-Flip + D5-Handover-Vermerk + 4-Mini-Pläne-
  Vermerk); `docs/INDEX.md` (`Phase 14` von Active → Closed, neue Closeout-
  Handover-Linie); Phasenkopf selbst (Header-Status-Flip, YAML-Card-Update,
  Session-22 → Archiv, Session-23 → Phasenkopf).
- Drei Drift-Korrekturen an Doku (Code = source of truth):
  1. **Mini-Session-22-NEXT-Block Item 2 (Doku-Updates synchronisieren)** war als
     „Mini-Hygiene" aufgeschoben und ist jetzt **im selben Closeout-Commit
     mit-propagiert**.
  2. **Phase-14-Phasenkopf-Status-Text** war schon richtig („architektonisch +
     operativ komplett freigegeben"), aber das **Status-Emoji** war noch `🔄`
     statt `✅` — Status-Flip im selben Commit.
  3. **`origin/main`-HEAD-Drift:** vor dieser Session war unklar, wann der
     Phase-14-D5-Handover formell aufgehoben wird; nach dem Phase-13-CLOSE-OUT
     (heute Morgen, Commit `0ff55d2`) ist die Voraussetzung erfüllt — Closeout
     heute schließt die Schleife.
- **Keine Cross-Phase-Produktionscode-Edits** in dieser Session. Phase-14-CLOSE-OUT
  ist eine **eigenständige dokumentationsdominierte Atom-Einheit** (analog zu
  Phase-12/13-Closeouts). Bot läuft unverändert weiter.

**Was diese Session bewusst NICHT gemacht hat:**
- **Eigene SVG-Illustration** (`docs/architecture/phase14_closeout.svg`) — Phase-12
  hatte eine (1080×1080, drei-Panel-Layout). Phase-13 hat **keine Fehlerbild-SVG**
  und empfiehlt ein gemeinsames `phase13_14_15.svg` mit Phase-15. Phase-14 folgt
  dieser Empfehlung: **kein Solo-SVG**, gemeinsam mit Phase-15 wenn überhaupt.
- **P15-Plan-Session** — Material jetzt vollständig (Phase-13-Findings + §8 +
  Pfad-C + 4 Mini-Pläne-Outputs), bleibt long-horizon, gegatet auf Outcomes aus
  Phase 9+11+12+13+14. Wer das startet, hat das vollständige Bild.
- **Phase-12-Reconciliation-Timing-Fix** — out of scope (Phase-12-Code). Pre-Test
  grün (4 von 4 Backoff-Tests A2–A5), A6 wartet auf nächsten OPEN-Trade.
- **Hook-`-strict`-Default-Verschärfung als Installer-Argument** (P14-F D5) —
  bereits live seit Mini-Session 24 (Commit `c4f7d9c`).

**Push-Freigabe:** dieser Closeout-Commit ist der einzige Commit dieser Session;
enthält **kein** Cross-Phase-Produktionscode-Edit. Sweep Σ 1703 grün, kein Bot-Touch.

---

> **Autor dieses Files:** Claude Code, Read-only-Session 2026-08-31, Session 23
> auf Phase 14. Cross-Phase-Liste (Plan §4 D5 + Session-9-NEXT +
> Phase-14-Nikinger-Sign-off 2026-08-22 + Mini-Sessions 21/22/23/24) abgearbeitet:
> Phase-14-Files editiert (1 NEU + 4 Updates, alle Doku), Cross-Phase-Files
> (`source_registry/`, `data_foundation/`, `live_data/`, `phase9_universe/`) **nicht**
> angefasst — die sind die strukturelle Antwort und bleiben autonom.
> **Phase-14-CLOSE-OUT-Handover ist eine eigenständige dokumentationsdominierte
> Atom-Einheit** — keine Cross-Phase-Produktionscode-Edits am Phase-14-Code in
> dieser Session.
