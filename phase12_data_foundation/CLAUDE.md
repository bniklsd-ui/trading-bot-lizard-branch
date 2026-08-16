---
status: live
purpose: PHASE-HEAD, Phase 12 (Datenfundament) — Registry + BarService + Bar-Archiv + Recorder. Step 4 done+committed (49902b6). Step 5 (Recorder, PID-guarded standalone process) done this session, UNCOMMITTED. Steps 6/7 sind noch Wochenend-Arbeit.
read-when: working in phase12_data_foundation/ — read this head + its newest Session-stopped block first (⚠️ operator landmine there before any bot restart — now affects both the paper tracker AND the Recorder); the full plan (docs/concepts/phase12_data_foundation_plan.md) is the execution contract, read its relevant §6 step block before touching anything
detail: L2
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase12_data_foundation_plan.md   # full execution-ready plan, D1-D20, Steps 0-10 (L3, ausführungsreif)
  - ../phase10_v3/PHASE11_DEFERRAL_HANDOVER.md          # why this track exists (L3, dated)
  - ../docs/architecture/data_foundation.svg            # Fehlerbild + Zielbild
  - ./SESSIONS_ARCHIVE.md                               # rotierte Session-Blöcke (L3)
updated: 2026-08-16
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

## Session stopped — 2026-08-16 (Session 3: Step 4 committed + Step 5 — Recorder, Step 5 UNCOMMITTED)

> **Vorherige Session ging in Context Limit.** Der Handover-Satz beim Sitzungsstart lautete:
> „Acceptance grep confirms: only a docstring comment remains, zero real get_ohlcv calls in
> wiring.py. Task 19 complete." — diese Session hat das As-Built gegen den Plan (§ Step 4,
> `docs/concepts/phase12_data_foundation_plan.md:394-457`) nachverifiziert (voller Regression-
> Lauf + 4 Advisor-Nachprüfungen), **kein neuer Code geschrieben**, nur die Doku nachgezogen.

### Completed (in der Vorgänger-Session gebaut, diese Session verifiziert + dokumentiert)

**`data_foundation/service.py`** (neu, 267 Zeilen): `BudgetedIGBarProvider` (`BarProvider`-
Protocol, gated auf `SourceBudget.can_spend` **vor** dem Broker-Call, bucht nach Erfolg
`record_spend(len(bars))` + `record_allowance(...)` aus `env.data['allowance']`, emittiert
`bar_fetch`-Health-Events) und `BarService` (Archiv-first via `coverage_ratio`/`window`, sonst
`ChainedBarProvider([yf, ig])` + Write-Through mit Provenienz; `get_bars` für die Research-Naht,
`get_window` für den Tracker — bei unvollständiger yF-Deckung ein expliziter IG-Top-up-Zweig,
bewusst außerhalb der Chain-Reihenfolge, weil Korrektheit hier vor Kosten geht).

**Wiring-Rewire** (`phase8_scheduler/scripts/wiring.py`): neu `_build_data_foundation`
(lazy imports, `bars.sqlite`-Pfad); `_build_market_data`s `enable_ig_bars`-Zweig ersetzt durch
`enable_bar_service` (Kette `[("ig", BudgetedIGBarProvider), ("yf", YFinanceBarProvider)]`,
außen `BarService`); `_build_paper_tracker`s `bar_fetch(epic)` ist jetzt ein dünner Closure über
`bar_service.get_window(...)` — die alten Budget-Konstanten `_PAPER_BAR_COUNT`/
`_PAPER_BUDGET_COOLDOWN_MIN`/`_PAPER_ALLOWANCE_FLOOR` sind **entfallen** (bestätigt per Grep,
0 Treffer), `_PAPER_MAX_FETCH_ATTEMPTS` bleibt (Korrektheitsguard, quellenneutral); `budget_ok`
ist jetzt ein dokumentierter No-Op (`lambda: True`, Kommentar erklärt warum — der reale Gate
lebt in `BudgetedIGBarProvider.can_spend`, ein zweiter Tick-Level-Gate wäre redundant).

**`PaperTradeTracker._resolve_group`** (`phase10_v3/abstain_lessons/paper.py:581-627`):
`resolution_source = "+".join(sorted(sources))` über die tatsächlich konsumierten Bars,
gefiltert auf `b["timestamp"] >= trade.created_utc` (spiegelt `resolve_paper_trade`s eigenen
Filter, keine zweite Traversierung mit anderer Semantik) — kein Fallback-Default für Bars ohne
`source`-Key, ein ehrliches `None` statt eines geratenen Werts.

**`PaperEngine.epic_filter`** (D19): Wiring injiziert
`lambda epic: epic in {r.epic for r in store.measurable_universe()}`.

**`SchedulerConfig`**: `enable_ig_bars` → `enable_bar_service: bool = True` (D17,
Docstring erklärt die Ablösung); `scheduler/run.py` bekam `--no-bar-service`-Flag nachgezogen.

### Verified (diese Session, gegen den Plan-Text Zeile für Zeile)

- **Volle Regression, alle 12 Phasen + root, 0 Failures:** P1 87 · P2 77 · P3 104 · P4 155 ·
  P5 173 · P6 76 · P7 138 · **P8 229** (unverändert trotz 3 geänderter Dateien — plausibel,
  keine Netto-Testzahl-Änderung) · P9 80 · **P10 159** (+12 ggü. 147) · **P12 80** (+16 ggü. 64)
  · meta 28 · root 80.
- Offline-Smoke (`phase8_scheduler/scripts/smoke_test.py`) 3/3 PASS.
- **Akzeptanz-Grep, repo-weit (nicht nur `wiring.py` wie der Handover-Satz nahelegte):**
  `grep -rn "get_ohlcv"` außerhalb `wiring.py`s Docstring-Kommentar trifft ausschließlich
  `broker_wrapper`s eigene Definition, den Momentum-VETO-Pfad (`phase5_execution/execution/
  vetos.py`), `verify_instrument`/`resolve_epics`-Skripte, Phase-4/6/9-eigene (unabhängige)
  Nähte und `data_foundation/service.py` selbst (`BudgetedIGBarProvider`) — keine vierte
  IG-Bar-Direktleitung übersehen. `grep -rn "enable_ig_bars"` zeigt nur noch `phase4_research`s
  **eigenes**, unabhängiges Flag (sein eigenständiges `scripts/wiring.py`, nicht Teil des
  Scheduler-Laufpfads — außerhalb Step-4-Scope) + einen Wiring-Kommentar, der die Ablösung
  erklärt.
- `resolution_source` per Lesen von `paper.py:581-627` bestätigt korrekt gefiltert (nicht aus
  allen zurückgegebenen Bars, nur aus den tatsächlich für die Auflösung relevanten).
- `BudgetedIGBarProvider.get_bars` gelesen: bucht `record_spend`/`record_allowance` nur nach
  erfolgreichem Fetch, verweigert vor jedem Broker-Call bei `can_spend()==False` (kein toter
  Breaker).
- `test_config.py:49` trägt eine echte Assertion (`cfg.enable_bar_service is True`), keine
  stumme Umbenennung.

**Kleiner, außerhalb-Scope-Fund (nicht angefasst):** `phase4_research/research/models.py:623`
kommentiert noch „the daemon's own SchedulerConfig.enable_ig_bars" — dieses Feld existiert seit
diesem Step nicht mehr (jetzt `enable_bar_service`). Reiner Kommentar in einem Phase-4-File,
außerhalb des Step-4-Dateiumfangs (`phase4_research/`-Edits nur bei zwingendem Grund laut
Root-`CLAUDE.md`-Scope-Regel) — für den Nikinger notiert, nicht selbst gefixt.

**Step 4 committed** (Commit `49902b6`, `phase12: BarService + tracker/research rewire (Step 4)`).

## Step 5 — Recorder (derselbe Tag, Wochenende, D14/D15)

`data_foundation/recorder.py` (`Recorder`, `RecorderReport`) — yFinance-only Poll-Loop,
fail-soft je Epic, Dedup über den Archiv-PK (kein eigener Dedup-Code nötig,
`insert_bars` macht das schon), atomarer Heartbeat-State (`.tmp`+`os.replace`, P8-Muster
kopiert nicht importiert), `recorder_heartbeat`-Health-Event. `data_foundation/run.py`
(`python -m data_foundation.run`) — PID-File-Guard (`_pid_alive`/`_already_running`/
`_write_pid`, doppelstart-sicher, live gegen einen echten `os.getpid()` verifiziert),
SIGTERM/SIGINT → `request_stop()`. `phase12_data_foundation/scripts/run_recorder.sh`
(neu, Paket-Code) + Edit an `phase8_scheduler/scripts/run_scheduler.sh` (D14, Cross-Phase
— `nohup … &` vor dem `exec`, PID-Guard lebt im Recorder-Skript).

**Advisor-Review fand 1 echten Bug vor Abnahme, gefixt:** `_build_recorder`s
`MarketDataFetcher(TickerMapper(), ...)` nutzte eine **bare** `TickerMapper()` — die kennt
nur ihre ~7 statischen `_MAP`-Einträge (P3s eigene Smoke-Test-Form), nie einen
Registry-aufgelösten `yf_ticker` (D5/D6, Step 3). Jeder von `measurable_universe()`
gelieferte Epic außerhalb der 7 Defaults hätte `EpicNotMappedError` geworfen, still von
`tick()`s fail-soft-Guard geschluckt — Archiv bleibt leer, Heartbeat schreibt trotzdem
„gesund". Exakt Phase 11s Fehlerklasse (ein dritter Speicher, der die Registry
überschattet), reintroduziert in der Phase, die sie beheben soll. Gefixt am gemeinsamen
Punkt: `epics_fn` registriert jetzt `rec.yf_ticker` auf den geteilten Mapper bei jedem
Aufruf (spiegelt `phase8_scheduler/scripts/wiring.py`s `mapper.register`-Muster), bevor es
den Epic zurückgibt — ein Epic ohne `yf_ticker` wird übersprungen (defensiv, sollte durch
`measurable_universe()`s Gate nie vorkommen). Kein dedizierter Test nötig (Fake-`epics_fn`
in den bestehenden Recorder-Tests umgeht die reale Mapper-Frage strukturell — dieselbe
"operator-run, nicht pytest-erfasst"-Konvention wie `wiring.py` selbst).

### Verified

- `pytest phase12_data_foundation/tests -v` → **96 passed** (war 80, +16: ~10
  `test_recorder.py` + 6 `test_run.py`).
- Volle Regression unverändert grün, alle 12 Phasen + root: P1 87 · P2 77 · P3 104 ·
  P4 155 · P5 173 · P6 76 · P7 138 · P8 229 · P9 80 · P10 159 · P12 96 · meta 28 · root 80.
- `py_compile` clean (`recorder.py`, `run.py`); `bash -n` clean (beide `.sh`).
- **PID-Guard live gegen einen echten Prozess getestet** (nicht nur gemockt): ein
  `--pid-file` mit der eigenen PID der laufenden Shell → zweiter Start meldet „already
  running", **exit 0**, kein zweiter Recorder gestartet.
- `grep -rn "import broker_wrapper\|from broker_wrapper"
  phase12_data_foundation/data_foundation/` → 0 Treffer (D14). `test_isolation.py`s
  AST-Grep deckt beide neuen Dateien automatisch mit ab (paketweit, kein Zusatztest nötig).
- `scripts/dev_install.sh` hat `phase12_data_foundation` bereits in der editable-Install-
  Kette (Zeile 55) — `run_recorder.sh`s Prereq-Zeile ist wahr, nicht nur behauptet.
- `run_scheduler.sh`-Edit nur `bash -n`-geprüft (Syntax), **nicht live ausgeführt** — ein
  echter Start würde die reale `data/`-DB berühren + einen echten yFinance-Netzwerkruf
  machen, beides Nikinger-Job laut `feedback_live_testing`-Memory. `data/state/` existiert
  bereits (Redirect-Ziel sicher).

### Next

- **⚠️ Operator-Landmine vor jedem Neustart (jetzt auf zwei Konsumenten erweitert):**
  alle 22 Produktionszeilen stehen laut Step 3 auf `data_source_status='unverified'` →
  `measurable_universe()` ist **leer** → sowohl `epic_filter` (Paper-Tracker öffnet keine
  Paare) **als auch der neue Recorder** (tickt endlos mit `epics: 0, bars_written: 0`,
  Heartbeat schreibt trotzdem "erfolgreich") sind betroffen. Beide Symptome sehen wie
  gesunder Leerlauf aus, nicht wie ein Fehler — Step 6s Heartbeat ist der geplante Alarm
  dafür und ist **noch nicht gebaut**. Bis dahin: Resolver von Hand laufen lassen und
  `measurable_universe()` vor einem Neustart prüfen.
- **Erster echter Start ist Nikinger-Job:** `bash phase12_data_foundation/scripts/
  run_recorder.sh` standalone (Archiv-Warmlauf) oder automatisch über den nächsten
  `run_scheduler.sh`-Start — beides live/netzwerkberührend, hier nicht ausgeführt.
- Steps 6/7 (Wochenende), Steps 8-10 (gated, Operator).
- Uncommitted: Step-5-Dateien (s. `git status`) — Commit ist Nikinger-Entscheidung.

### Open questions / blockers

- Keine technischen (Advisor-Review dieser Session: 4 Step-4-Nachprüfungen + 1
  Step-5-Fund, alle sauber/gefixt).
- Operator-Landmine oben ist die einzige reale Konsequenz, die vor dem nächsten
  Bot-Neustart aktiv gemanagt werden muss — jetzt mit zwei betroffenen Konsumenten.
---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
