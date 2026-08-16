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

## Session stopped — 2026-08-15 (Session 2: Step 3 — Migration 006 + Registry + SymbolResolver)

### Completed

**Migration `006_phase12_data_foundation.sql`** (additiv, Muster 005): `instrument_universe`
+3 Spalten (`data_source_status` DEFAULT `'unverified'`, `symbol_source`,
`symbol_checked_at`), `paper_trades` +1 (`resolution_source`). `phase2_persistence/tests/
test_migrations.py` auf Version 6 gehoben (alle `==5`→`==6`-Stellen), zwei Exact-Equality-
Spaltenmengen erweitert, +1 neuer Test (`test_phase12_data_foundation_columns_present`,
prüft Default-Wert auf einer frisch eingefügten Zeile). `paper_store._CREATE_TABLE`
bekam `resolution_source` **nur im DDL** (kein `_ROW_COLUMNS`/Arity/`from_row`-Touch — das
ist Step 4) — hält `ensure_schema()` und die Migration in derselben Tabellenform.

**Registry-Erweiterung** (`phase9_universe/universe/`): `UniverseRecord` +3 Felder ans Ende
(`data_source_status`, `symbol_source`, `symbol_checked_at`) + Status-Vokabular
(`DS_OK`/`DS_UNVERIFIED`/`DS_NO_SOURCE`/`DS_NO_INTRADAY_SOURCE`/`DS_MISMATCH`,
`SYMBOL_SOURCE_SEED`/`_RESOLVER`/`_OPERATOR`). `UniverseStore.set_symbol` — der **einzige**
`yf_ticker`-Writer (D5) — und `measurable_universe()` (`status='active' AND
data_source_status='ok'`, D7/D19-Gate). `discovery.py` schreibt `yf_ticker` nicht mehr
(`KNOWN_YF_TICKERS` entfernt, Neuanlage immer `yf_ticker=None`); `__init__.py`-Re-Exports
mitgezogen.

**Advisor-gefundener Bug vor Commit, gefixt:** `upsert_discovered`s `ON CONFLICT ... DO
UPDATE SET` baute sich aus *allen* `to_row()`-Spalten — sobald die drei neuen Felder in
`to_row()` standen, wurde eine Re-Discovery eines bereits bekannten Epics zu einem zweiten
`yf_ticker`-Writer, der ein verifiziertes Symbol mit `None`/`'unverified'` überschrieben
hätte. Gefixt am gemeinsamen Punkt: `_PRESERVE_ON_CONFLICT`-Tupel
(`yf_ticker`/`data_source_status`/`symbol_source`/`symbol_checked_at`), aus der
`DO UPDATE SET`-Comprehension gefiltert — beim Insert weiter geschrieben, beim Update nie.
Strukturell (`tests/test_criterion_a.py`) + verhaltensbasiert (`test_store.py::
test_upsert_discovered_preserves_registry_truth_on_conflict`) abgesichert.

**`MarketDataFetcher.get_last_price(symbol)`** (Phase 3, additiv, N2 — Nikinger-
Entscheidung in der Planungssession): symbol-keyed (nicht epic-keyed, für einen im
`TickerMapper` noch unregistrierten Kandidaten), dünner Wrapper um `_get_records(resolution
="5m", period="1d", interval="5m")` — erbt Cache/RateLimiter/Circuit unverändert.
Off-Hours-gated wie jede andere intraday-Methode. Leerer Fetch **raised**
`DataUnavailableError` (konsistent mit `get_drift`/`get_bars`/`get_momentum` — nicht
stillschweigend `None`).

**`data_foundation/symbols.py` — `SymbolResolver`** (D6/D7, N1): `SEED_SYMBOL_CANDIDATES`
(die alten 12 + 4 neue Werktags-Klassen: `^GSPC`/`^NDX`/`^DJI`/`^FTSE`), `candidates_for`,
`is_weekend_instrument` (primär `specialInfo`-Substring, sekundär `openingHours`, Fallback
Name+Epic-Segment — **live bestätigt 2026-08-15**: alle 4 aktiven Wochenend-Epics
(`SUNDAX`/`SUNNAS`/`SUNDOW`/`SUNFUN`) tragen "Wochenend" im Namen, der Fallback allein
deckt heute die reale Produktions-Universe), `price_agreement` ((bid+ask)/2 vs. yF-Last,
2%-Toleranz), `ResolverReport`, `SymbolResolver.resolve_epic`/`resolve_universe`
(fail-soft je Epic).

**N1 — Liveness-Gate (Nikinger-Entscheidung, weicht bewusst vom Plan-Wortlaut ab):** beide
Gates (`is_market_open()` XETRA-Fenster **UND** Frische des yF-Bars, nicht nur D6s
XETRA-Check) — ohne die Frische-Hälfte hätte ein Vergleich außerhalb 15:30-17:30 Berlin
IGs 24h-CFD-Livepreis gegen yFinance' Vortagesschluss für die vier neuen US/UK-Kandidaten
verglichen und wiederholt fälschlich `mismatch` gebucht. Bekannte, dokumentierte Konsequenz:
diese vier Epics verifizieren sich nur im 15:30-17:30-Berlin-Überlappungsfenster — Alarm
dafür ist Step 6 (`data_health.py`/Heartbeat), nicht Step 3.

**Advisor-Review (2. Runde, vor Abnahme) fand 2 echte Bugs, beide gefixt:**
1. Die Mismatch-Eskalation gatete auf `data_source_status == DS_UNVERIFIED` — Migration 006
   setzt aber **jede** Zeile initial auf `'unverified'`, also wäre die erste Preis-
   Abweichung eines **frischen** Epics sofort zu `mismatch` eskaliert (bewiesen gegen die
   echte DB: alle 22 Produktionszeilen starten `'unverified'`). Gefixt: die Eskalation
   gated jetzt auf `rec.yf_ticker == candidate` ("wurde dieser Kandidat schon in einem
   früheren Pass gebucht") statt auf den Status allein — ein frischer Epic bekommt immer
   einen kostenlosen ersten `unverified`-Pass; ein bestehendes `mismatch` bleibt jetzt auch
   sticky (flatterte vorher zurück zu `unverified`).
2. `is_weekend_instrument(rec.name, None)` — der `epic`-Parameter fehlte im Aufruf, die
   SUN-Segment-Fallback-Hälfte war unerreichbar. Signatur um `epic: str | None = None`
   erweitert, `resolve_epic` reicht `rec.epic` durch; per Live-Query gegen die echte DB
   bestätigt, dass der Namens-Fallback die heutige Produktions-Universe bereits allein
   deckt (s.o.), der Epic-Fallback ist Defense-in-Depth für zukünftige Namen ohne
   "Wochenend"-Substring.
3. `resolve_universe` fing nur `ResolverError` — ein `store.set_symbol`-Fehler (z. B. Zeile
   während des Laufs verschwunden) hätte den ganzen Pass abgebrochen. Auf `Exception`
   verbreitert; `resolve_epic`s Docstring korrigiert (raised `ResolverError` nur bei
   unparsebarem Timestamp, kein "never raises" mehr).

Alle drei Funde durch neue/erweiterte Tests abgesichert (s. Verified).

**Doku-Korrekturen (Code = Source of Truth):** `phase9_universe/CLAUDE.md`s Bauprinzip-Zeile
("statische Code-Tabelle") war seit diesem Step falsch — datierte Korrekturnotiz ergänzt.
`phase3_external_data/CLAUDE.md` bekam den vierten `🔁`-Edit-Eintrag für `get_last_price`.

### Verified

- **`pytest phase12_data_foundation/tests -v` → 64 passed** (war 28 vor diesem Step: +5
  set_symbol/measurable_universe/conflict-preserve-Tests wanderten nach P9, +31 `test_
  symbols.py`, +3 `test_criterion_a.py`, +5 Advisor-Nachschärfung).
- Volle per-Phase-Regression: P1 87 · P2 77 (+1) · P3 104 (+4) · P4 155 · P5 173 · P6 76 ·
  P7 138 · P8 229 · P9 80 (+5) · P10 147 · P12 64 (+36 ggü. 28) · root 80 · meta 28 —
  Summe ohne P12 **1374** (Baseline **1364** + die 10 erwarteten neuen Tests in P2/P3/P9,
  keine Regression sonst).
- **Migrations-Trockenlauf gegen eine Scratchpad-Kopie der echten `data/trading_bot.
  sqlite`** (Original nie geöffnet): Version 5→6, 22 `instrument_universe`-Zeilen + 615
  `paper_trades`-Zeilen zahlenmäßig unverändert (additiv bewiesen, nicht nur behauptet),
  alle 22 landen auf `data_source_status='unverified'` (bestätigt die im Plan
  dokumentierte Konsequenz: `measurable_universe()` startet leer), Re-Lauf idempotent
  (Version bleibt 6, keine zweite `_schema_version`-Zeile).
- **Live-Query gegen die echte DB** (read-only, `mode=ro`): die vier aktiven Wochenend-
  Epics bestätigt (`IX.D.SUNDAX.IGN.IP`/`IX.D.SUNNAS.IAE.IP`/`IX.D.SUNDOW.IAE.IP`/
  `IX.D.SUNFUN.IFE.IP`, alle `name` enthält "Wochenend") — trägt Step-3-Doku direkt gegen
  Produktionsdaten, nicht nur gegen Fixtures.

### Next

- **Step 4** (Wochenende, Cross-Phase): `BarService` + Tracker-/Research-Rewire in
  `phase8_scheduler/scripts/wiring.py`, `SchedulerConfig.enable_bar_service` (löst
  `enable_ig_bars` ab, D17). `BudgetedIGBarProvider`, `_resolve_group`s
  `resolution_source`-Durchreichung, `PaperEngine.epic_filter` (D19).
- Step 5 (Recorder, Paket-Code werktags baubar; `run_scheduler.sh`-Edit Wochenende), Steps
  6/7 (Wochenende), Steps 8-10 (gated, Operator).

### Open questions / blockers

- Keine technischen. Die im Plan dokumentierte Konsequenz (leere `measurable_universe()`
  bis der Resolver + der `universe_refresher` mehrfach gelaufen sind) ist jetzt gegen die
  echte DB bestätigt, nicht nur eine Annahme — 22/22 Zeilen starten `unverified`. Step 6
  muss das als Alarmbedingung in `data_health.py`/`measurement_heartbeat` fangen, nicht
  erst am Freitag der Beweiswoche auffallen.
- Die vier neuen US/UK-Kandidaten (`^GSPC`/`^NDX`/`^DJI`/`^FTSE`) verifizieren sich nur im
  15:30-17:30-Berlin-Fenster (N1-Konsequenz) — erwartungsgemäß, dokumentiert, kein Bug.
---

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
