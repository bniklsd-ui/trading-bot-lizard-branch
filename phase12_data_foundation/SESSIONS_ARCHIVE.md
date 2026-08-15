---
status: archive
purpose: Verbatim session-history archive rotated out of `CLAUDE.md`
read-when: auditing how a past Phase-12 decision came about — never needed at session start
detail: L3
up: ./CLAUDE.md
updated: 2026-08-15
---

# phase12_data_foundation — Session Archive

> The blocks below were moved here **verbatim, unedited** from `CLAUDE.md` per the Doc-Layers
> rotation rule ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)). Source order
> preserved (newest-first). The newest `## Session stopped` block always stays in the source file;
> at each session end, the previously-newest block rotates here.

## Session stopped — 2026-08-11 (Session 1: Anker-Verifikation + Steps 0/1/2)

### Completed

**Step 0a — Live-Check (Nikinger-Job, ausgeführt):**
`get_market_info` projiziert die IG-Antwort auf eine feste `MarketInfo`-Shape ohne
`openingHours`/Margin-Felder (`ig_adapter.py:479-513`) — der geplante CLI-Weg hätte beide
Step-0a-Fragen nicht beantwortet. Nikinger-Entscheidung: Roh-Dump-Skript statt CLI
(`GET /markets/{epic}` v3 direkt über `broker._request`). Ergebnis (3 Epics, alle
`marketStatus` != CLOSED da Dienstagnachmittag; SUNDAX zeigte `EDITS_ONLY`, nicht
`CLOSED` — Vokabular-Fund für §9-Drift):

- `IX.D.DAX.IFMM.IP` (gemappt, `^GDAXI`) und `IX.D.SPTRD.IAE.IP` (ungemappt, US 500):
  **`instrument.openingHours: null`** für beide — normale Werktags-Instrumente tragen keine
  `marketTimes`.
- `IX.D.SUNDAX.IGN.IP` (aktiv, SUN): **`instrument.openingHours: {"marketTimes": [{"openTime":
  "07:00", "closeTime": "21:40"}]}`** — populated, plus (stärkeres Signal) ein wörtlicher
  Satz in `instrument.specialInfo`: *"The weekend instruments prices are determined by IG
  based on various factors."* → **`specialInfo`-Substring-Match ist ein zuverlässigerer
  Wochenend-Detektor als `openingHours != null` allein** (ein echtes restricted-hours-
  Werktagsinstrument könnte theoretisch auch `marketTimes` tragen, ohne Wochenend zu sein).
  **Empfehlung für Step 3 `symbols.py::is_weekend_instrument`:** primär auf
  `specialInfo`-Substring ("weekend instrument"), `openingHours != null` als Sekundärsignal,
  Namens-/Epic-Heuristik (`"wochenend"`/`"weekend"`/`SUN`-Segment) bleibt der dokumentierte
  Fallback, wenn `specialInfo` fehlt oder leer ist.
- **B3-Margin (gebündelt, alle 3 Epics):** `instrument.marginDepositBands` (gestaffelt nach
  Positionswert: `min`/`max`/`margin`(%)/`currency`, z. B. DAX 0-350€ → 5%, >2800€ → 15%),
  `instrument.marginFactor` (5, alle drei Epics gleich) + `marginFactorUnit`
  (`"PERCENTAGE"`). Vollständig genug für die eigene B3-Session (Plan §10 — nicht hier
  umgesetzt, nur gescoutet).
- Rohdaten: `dump_market_raw_result.json` (Scratchpad, nicht im Repo — Wegwerf-Diagnose).

**Step 0b — Plan-Korrektur + Housekeeping:**
- Drift in `docs/concepts/phase12_data_foundation_plan.md` gegen Code (Stand `c5d7ef1`)
  korrigiert: CLI-Subcommand `market-info`→`get-market-info`; `verify_instrument.py`-Pfad
  `phase9_universe/scripts/`→`scripts/` (Repo-Root); `run_scheduler.sh`-Anker (33 Zeilen,
  kein `$REPO_ROOT`, `PROJECT_DIR`-Var). §9.3 IG-Bar-Timestamp bestätigt **nicht** ISO
  (`snapshotTime`/`snapshotTimeUTC`, IG-eigenes Format) — `normalize_bar_ts` (Step 1) deckt
  das ab. Alle übrigen §9-Anker gegen Code verifiziert, kein weiterer Drift gefunden.
- **Nummerierung final** (D2, Nikinger-Entscheidung 2026-08-11): Phase 12 = Datenfundament,
  altes „V4" → Phase 13. Nachgezogen in Root-`CLAUDE.md`, `ROADMAP.md`, `README.md`,
  `ARCHITECTURE.md`, `docs/INDEX.md` (die fünf gemäß Plan) plus zwei kleine Streufunde
  (`phase9_universe/CLAUDE.md:45`, `phase10_v3/CLAUDE.md:21`) — dieselbe Nummer, gleiche
  Korrektur, nicht extra erwähnenswert als eigener Fund.
  `docs/INDEX.md`-Zeile für den Plan ergänzt (selber Commit).
- Legacy-Grep-Ritual (`turbo|CALL/PUT|pre_trade_option_check|expected hold`) sauber — alle
  171 Treffer sind dokumentierte Prosa/der eingefrorene `turbo_candidates.json`-Dateiname,
  kein aktiver Options-Rest (deckt sich mit dem zuletzt dokumentierten Ritual-Ergebnis in
  `phase10_v3/CLAUDE.md`).
- Regression-Baseline (per-Phase, vor jedem Edit): P1 87 · P2 76 · P3 100 · P4 155 · P5 173 ·
  P6 76 · P7 138 · P8 229 · P9 75 · P10 147 · root 80 · meta_m1_harness 28 = **1364 grün**,
  keine Regression durch Steps 0c/1/2 (kein Bestandscode angefasst).

**Step 0c — Skeleton:** `phase12_data_foundation/` angelegt (`data_foundation/` Paket,
`pyproject.toml`, `requirements.txt` (nur `pytest`), `README.md`, dieses `CLAUDE.md`,
`tests/`, `scripts/`), Eintrag in `scripts/dev_install.sh` (elftes Paket).

**Step 1 — `BarArchive`:** `data_foundation/models.py` (`Bar`, Source-/Status-Konstanten,
`normalize_bar_ts` — deckt IG `yyyy/MM/dd HH:mm:ss`, ISO `...Z`, yF-Form), `exceptions.py`
(`DataFoundationError`-Hierarchie), `archive.py` (`BarArchive`: `ensure_schema`,
`insert_bars` mit Dedup, `window` mit Quellen-Präferenz, `coverage_ratio`, `latest_ts`,
`bars_written_since`, `close`). Eigene SQLite `data/bars.sqlite` (D4), kein
`persistence`-Import.

**Step 2 — `SourceBudget`:** `data_foundation/budget.py` (`QuotaModel`, `IG_QUOTA_V1` =
10 000 Pkt/7 Tage — Platzhalter bis §9.5/§9.11 live bestätigt, `SourceBudget` mit
`record_spend`/`record_allowance`/`can_spend`/`remaining_estimate`/
`predicted_exhaustion_days`, Persistenz über `bars.sqlite`). 08-03-Regressionstest gebaut:
33×300-Punkte-Sequenz zeigt `can_spend(300) == False` **vor** dem erschöpfenden Call.

### Verified
- `pytest phase12_data_foundation/tests -v` → **28 passed** (15 Archive + 12 Budget + 1
  Isolations-AST-Test; Plan schätzte ~19, Mehrbedarf kam aus den `normalize_bar_ts`-Formvarianten
  + den drei Advisor-Regressionstests, s. u.).
- Import-Isolationstest (AST, `phase10_v3/tests/test_separation_guarantees.py`-Muster): kein
  `data_foundation`-Modul importiert eine andere Phase auf Modul-Top-Level.
- Volle per-Phase-Regression erneut gelaufen nach Steps 0c/1/2: **identisch** zur Baseline
  oben (P1 87 · P2 76 · P3 100 · P4 155 · P5 173 · P6 76 · P7 138 · P8 229 · P9 75 · P10 147 ·
  root 80 · meta 28 = 1364) — keine Regression, kein Bestandscode angefasst. `py_compile`
  clean.

### Next
- **Step 3** (Wochenende, Cross-Phase): Migration 006 + Registry-Erweiterung (`UniverseStore.
  set_symbol`/`measurable_universe`) + `data_foundation/symbols.py` (`SymbolResolver`) —
  **Step-0a-Ergebnis oben konsumieren:** `is_weekend_instrument` primär auf
  `specialInfo`-Substring bauen, nicht nur auf die Namens-/Epic-Heuristik.
- **Step 4** (Wochenende): `BarService` + Tracker-/Research-Rewire in
  `phase8_scheduler/scripts/wiring.py`, `SchedulerConfig.enable_bar_service` (löst
  `enable_ig_bars` ab, D17).
- Step 5 (Recorder, Paket-Code werktags baubar; `run_scheduler.sh`-Edit Wochenende), Steps
  6/7 (Wochenende), Steps 8-10 (gated, Operator).

### Open questions / blockers
- Keine technischen. B3-Margin-Umsetzung (eigene Session, Plan §10) hat jetzt genug
  Feld-Scouting (s. Step-0a-Ergebnis oben), um ohne weiteren Live-Call gestartet zu werden.
- **`marketStatus: "EDITS_ONLY"`-Fund (SUNDAX, Step-0a-Rohdump):** `_STATUS_MAP`
  (`ig_adapter.py:70-81`) kennt den Wert real (`"EDIT"`/`"EDITS_ONLY"` → `"EDITS_ONLY"`,
  fällt **nicht** auf `"UNKNOWN"` zurück) — relevant für Step 3s Markt-offen-Pfad: ein
  SUNDAX-Snapshot außerhalb des Wochenend-Handelsfensters liefert einen echten,
  unterscheidbaren Status, keinen Blindfleck.
- **Advisor-Review dieser Session (2026-08-11) fand 3 echte Bugs vor Commit, alle gefixt:**
  `SourceBudget.window_start()` crashte bei einem nicht-ISO-`expiry`-String (§9.5 unconfirmed
  shape) statt fail-soft in "keine Beobachtung" zu fallen — gefixt (`try/except ValueError`).
  `BarArchive.insert_bars` validierte Quellen erst mitten in der Insert-Schleife (ein
  Batch-Fehler hätte einen offenen Transaktions-Rest hinterlassen) — gefixt (Vollvalidierung
  vor dem ersten Insert). `bars_written_since` zählte `COUNT(*)` statt distinct
  `(epic,resolution,ts_utc)` (eine Minute mit IG+yF hätte doppelt gezählt im
  Heartbeat-„Bars heute") — gefixt (`COUNT(DISTINCT ...)`). Alle drei durch neue/erweiterte
  Tests abgesichert, Suite läuft weiterhin komplett grün (s. u.).
- **Dem Nikinger zu melden (nicht in dieser Session gefixt, außerhalb Scope):** die
  Phasen-Tabelle in Root-`README.md` (Zeilen ~26-34) ist seit ~2026-07-03 unabhängig von
  dieser Renumerierung stale — sie hat **keine Zeile für Phase 10 oder das alte Phase 11**
  (springt von 9 direkt zu der jetzt korrigierten V4-Zeile). Nur die eine Zeile wurde in
  dieser Session korrigiert (D2); eine vollständige Tabellen-Überholung war nicht Teil des
  Auftrags — Entscheidung beim Nikinger, ob das nachgezogen wird.
