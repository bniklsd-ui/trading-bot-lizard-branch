---
status: live
purpose: PHASE-HEAD, Phase 12 (Datenfundament) — Registry + BarService + Bar-Archiv + Recorder. Step 3 done this session (Migration 006, Registry-Erweiterung, SymbolResolver). Steps 4/6/7 sind noch Wochenend-Arbeit.
read-when: working in phase12_data_foundation/ — read this head + its newest Session-stopped block first; the full plan (docs/concepts/phase12_data_foundation_plan.md) is the execution contract, read its relevant §6 step block before touching anything
detail: L2
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase12_data_foundation_plan.md   # full execution-ready plan, D1-D20, Steps 0-10 (L3, ausführungsreif)
  - ../phase10_v3/PHASE11_DEFERRAL_HANDOVER.md          # why this track exists (L3, dated)
  - ../docs/architecture/data_foundation.svg            # Fehlerbild + Zielbild
  - ./SESSIONS_ARCHIVE.md                               # rotierte Session-Blöcke (L3)
updated: 2026-08-15
---
# CLAUDE.md — Phase 12: Datenfundament (`phase12_data_foundation/`)

> Three data weeks (Phase 11) died on infrastructure, never on measurement. Root cause: one
> instrument fact lived in three divergent stores, the Phase-9 multi-source bar chain
> (`ChainedBarProvider`) was built and never switched on (`enable_ig_bars` default `False`).
> **Source of truth is the plan doc + the code, not this file.** Full plan:
> `../docs/concepts/phase12_data_foundation_plan.md`.

## Mission (zuerst lesen)
Ein neues Fundament, sequenziell (Überweg C, D1, Nikinger-Entscheidung 2026-08-11):
1. **Instrument-Registry** wird die eine Wahrheit für Instrument-Fakten; Symbol-Mapping
   abgeleitet + code-verifiziert statt deklariert.
2. **BarService** wird der eine Bar-Pfad für alle Konsumenten (Research + Paper Tracker).
3. **Bar-Archiv** (`data/bars.sqlite`) — jede gefetchte Bar wird persistiert, quellenagnostisch.
4. **Recorder** — eigener yF-only-Prozess, schreibt kontinuierlich, unabhängig vom Bot-Zustand.
5. **Mess-Heartbeat** — ein Ausfalltag fällt am selben Tag auf.
6. **Lightstreamer-Mitschrieb** (Step 10) — gated auf die bestandene Beweiswoche.

**Done-Kriterium der Phase:** eine echte Beweis-Messwoche läuft durch, ohne dass Infrastruktur
die Messung tötet (Plan §7). Die WI-2-Auswertung selbst bleibt Phase-11-Wiederaufnahme.

## Bauprinzip
„So wenig AI wie möglich, so viel AI wie nötig." **Phase 12 fügt NULL neues AI hinzu** (Plan
§1) — Symbol-Verifikation ist ein deterministischer Preisvergleich (IG-Snapshot vs. yF-Last),
kein LLM-Aufruf. Wer hier ein LLM „mappen/prüfen/schätzen" lassen will → stop, das ist Code.

## Scope
- **DRIN:** `data_foundation/` Paket (Archiv, Budget, Resolver, BarService, Recorder,
  Heartbeat), Migration 006 (Registry-Erweiterung + `paper_trades.resolution_source`), die
  Rewiring-Punkte in `phase8_scheduler/scripts/wiring.py` (Steps 3/4/6/7, Wochenend-Arbeit).
- **DRAUSSEN:** WI-2/W2-Auswertung + jede weitere H-Serie (Phase-11-Wiederaufnahme nach PASS),
  Research-Funnel-Fix, B3-Margin-Headroom-Umsetzung (nur Feld-Scouting hier, s. Session-Block),
  Council-Paper-Call, UI, Live-Konto, Lightstreamer für Live-Quotes (Step 10 hier ist reiner
  Archiv-Mitschrieb, anderer Zweck). Momentum-VETO bleibt unangetastet (D16) — sourct immer
  direkt aus P1-IG-Echtzeit-Bars, nie aus BarService/Archiv/yF.

## Rahmen (Plan §1, verbindlich)
Bot-berührende Steps nur am Wochenende (Bot steht, Markt zu). Werktags: docs-only /
`data_foundation/`-Paket-Code selbst (eigene Dateien, eigene Tests, kein bestehender
Phasen-Code, nichts in `data/` geschrieben). Live-/Netz-/Kosten-Tests macht der Nikinger.

## Modul-Tabelle
Siehe [`README.md`](./README.md).

---

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

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
