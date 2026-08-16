---
status: live
purpose: PHASE-HEAD, Phase 12 (Datenfundament) — Registry + BarService + Bar-Archiv + Recorder + Heartbeat. Steps 4+5 committed (49902b6, 473c8e4). Step 6 (measurement heartbeat + divergence sampler, enable_divergence_sampler default OFF) done this session, UNCOMMITTED. Step 7 (full integration + offline proof) is next.
read-when: working in phase12_data_foundation/ — read this head + its newest Session-stopped block first (⚠️ operator landmine there before any bot restart — affects epic_filter, the Recorder, and the divergence sampler, but is deliberately NOT a Step-6 CRITICAL alarm); the full plan (docs/concepts/phase12_data_foundation_plan.md) is the execution contract, read its relevant §6 step block before touching anything
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

## Session stopped — 2026-08-16 (Session 3: Steps 4+5 committed, Step 6 — Heartbeat + Divergence Sampler, UNCOMMITTED)

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

**Korrektur (diese Session, vor Step 6):** die vorherige Fassung dieses Blocks behauptete
„Step 6s Heartbeat ist der geplante Alarm dafür" für die leere `measurable_universe()`.
**Falsch, gegen den Plan-Text korrigiert:** `assess_day` behandelt `measurable_epics == 0`
als reine Problem-Notiz mit `ok=True`, nicht als Alarm (s. Step-6-Abschnitt unten,
`test_assess_day_no_measurable_epic_is_ok_with_problem_note`). Die Operator-Voraussetzung
(Resolver vor Neustart laufen lassen) bleibt unverändert die eigentliche Abhilfe.

**Step 4 committed** (Commit `49902b6`), **Step 5 committed** (Commit `473c8e4`).

## Step 6 — Divergenz-Sampler + Mess-Heartbeat (derselbe Tag, Wochenende, D12/§7 G)

`data_foundation/heartbeat.py`: `HealthVerdict` + `assess_day(archive, paper_db_path,
universe_db_path, day_utc, *, shadow_enabled)` — `ok=False` auf genau zwei Bedingungen
(`measurable_epics > 0 AND bars_today == 0` [Recorder tot] oder `shadow_enabled AND
pairs_resolved == 0 AND pairs_typed_expired == 0` [Null-Messtag]); `measurable_epics == 0`
liefert nur eine Problem-Notiz, kein `ok=False` (Bootstrap-Zustand, kein Infra-Fehler).
`pairs_resolved` zählt SL/TP-Auflösungen, `pairs_typed_expired` Time-Stop-Auflösungen —
`EXPIRED_UNRESOLVED` (Datenfehler) zählt in keinem der beiden.

`DivergenceSampler` (D12): einmal/Epic/Tag ein budgetiertes IG-`5m×3`-Sample
(`BudgetedIGBarProvider(spend_kind="sample")`) vs. die archivierten yF-Bars desselben
Fensters (nie ein frischer yF-Fetch); zweite Folge-Divergenz ⇒ `mark_mismatch_fn(epic)`
(Wiring löst das über `UniverseStore.set_symbol(..., status=DS_MISMATCH)` auf, inkl.
`logger.warning`, weil das ein Einbahn-Türverhalten ist — die Epic verschwindet sofort aus
`measurable_universe()`, nichts verifiziert sie automatisch zurück).

**Wiring** (`phase8_scheduler/scripts/wiring.py`): `daily_health_check`-Closure (neu,
`SchedulerConfig.enable_measurement_heartbeat` default **True** — rein lesend, kostet
nichts) — ruft `assess_day` mit dem aktuellen UTC-Kalendertag, schreibt
`measurement_heartbeat`-Event, `logger.critical` bei `ok=False`. `divergence_sampler`
reitet im **bestehenden** `universe_refresher`-Pass mit (keine neue Runner-Naht) —
`SchedulerConfig.enable_divergence_sampler` default **False** (echter neuer IG-Spend,
~120 Punkte/Woche bei ~8 `'ok'`-Epics — innerhalb des Plan-Budgets, aber ein neuer Posten;
gleiche Disziplin wie `enable_shadow_schedule`/`enable_paper_debate`: der Nikinger
scharfschaltet bewusst, kein stiller Default-ON unter einem Step-6-Commit).

`SchedulerRunner`: neuer `daily_health_check`-Konstruktor-Param (Default `None`,
bit-identisch), im POST_WINDOW-Zweig **nach** dem Force-Reconcile aufgerufen
(`_maybe_run_daily_health_check`, `_due_after`-Throttle 20h/`health_check_interval_min`).
`SchedulerState.last_health_check_ts` neu (cross-day, wie `last_shadow_pairs_ts`).

`phase12_data_foundation/scripts/data_health.py` (Operator, read-only, werktags erlaubt):
druckt `HealthVerdict` + Budget-Stand (`spent_in_window`/`remaining_estimate`/
`predicted_exhaustion_days`) + Recorder-Heartbeat-Alter; Exit 1 bei `ok=False`.

**Advisor-Review fand 2 echte Bugs vor Abnahme, beide gefixt:**
1. `BarArchive.bars_written_since(ts_utc)` hatte **keine** obere Grenze — eine Abfrage für
   einen **vergangenen** Tag hätte alles seit diesem Tagesanfang bis jetzt gezählt, nicht
   nur den einen Tag. Ein toter Tag hätte sich als "gesund" gemeldet — genau die Frage, die
   Requirement G stellt. Gefixt: additiver `end_utc: str | None = None`-Parameter
   (`None` = alte Semantik, offen-endig); `assess_day` reicht jetzt beide Grenzen aus
   `_day_bounds_iso` durch. Test beweist den Unterschied
   (`test_bars_written_since_respects_end_bound`,
   `test_assess_day_does_not_leak_bars_from_other_days`).
2. `BudgetedIGBarProvider._emit`s Event trug kein `spend_kind` — ein Sampler-Fetch und ein
   Research-Fetch waren im Observability-Log ununterscheidbar; Requirement C
   ("auch leere Tage zählen als Beweis der Ausführung via Sampler-Log") wäre am geloggten
   Event nicht nachweisbar gewesen (der Beweis existiert zwar über `source_spend`-Zeilen
   mit `kind='sample'`, aber ein Reviewer, der das JSONL liest, hätte nichts gefunden).
   Gefixt am gemeinsamen Punkt (`service.py`, beide Verbraucher — `BarService` und
   `DivergenceSampler` — profitieren): Event trägt jetzt `spend_kind`.

### Verified

- `pytest phase12_data_foundation/tests -v` → **109 passed** (war 96, +13: 11
  `test_heartbeat.py` + 2 Archiv-Regressionstests).
- `pytest phase8_scheduler/tests -v` → **235 passed** (war 229 nach Step 4, +6:
  Config-Assertions + 6 neue `test_daily_health_check_*`-Tests in `test_runner.py`,
  minus die bereits gezählten Step-4-Deltas).
- Volle Regression, alle 12 Phasen + root: P1 87 · P2 77 · P3 104 · P4 155 · P5 173 ·
  P6 76 · P7 138 · P8 235 · P9 80 · P10 159 · P12 109 · meta 28 · root 80.
- `py_compile` clean (`heartbeat.py`, `archive.py`, `service.py`, `data_health.py`,
  `wiring.py`, `runner.py`, `state.py`, `config.py`); Offline-Smoke 3/3 PASS.
- `data_health.py` end-to-end offline gegen eine synthetische Migrations-DB gelaufen
  (kein Netz, keine echte `data/`-Berührung): druckt Verdict + Budget + Recorder-Alter,
  exit 0 bei leerem/gesundem Synthetik-Zustand.
- `grep -rn "import broker_wrapper\|from broker_wrapper"
  phase12_data_foundation/data_foundation/` → 0 Treffer; `test_isolation.py`s AST-Grep
  deckt `heartbeat.py` automatisch mit ab (das lazy `scheduler.observability`-Import in
  `DivergenceSampler.sample_epic` ist function-body-scoped, nicht module-top-level).
- Comparator-Regression bewiesen: `test_sampler_compares_only_yf_bars_not_ig` pflanzt
  eine IG- **und** eine yF-Bar an derselben Minute und beweist, dass nur die yF-Zeile den
  Vergleich treibt (`window()`s `prefer` rankt nur, schließt eine IG-Zeile nicht aus —
  ohne den expliziten `source == "yf"`-Filter hätte der Sampler IG gegen sich selbst
  verglichen, dauerhaft grün, genau die Klasse toter Check, die diese Phase verhindern soll).

### Next

- **⚠️ Operator-Landmine vor jedem Neustart (drei Konsumenten, unverändert der Kernpunkt):**
  alle 22 Produktionszeilen stehen laut Step 3 auf `data_source_status='unverified'` →
  `measurable_universe()` ist **leer** → `epic_filter` (Paper-Tracker), der Recorder
  **und** der Divergenz-Sampler (sobald scharfgeschaltet) sehen alle keine Epics. Der
  Heartbeat markiert das als Problem-Notiz, **nicht** als `ok=False` — bewusst (s.
  Korrektur oben), also **kein** automatischer CRITICAL-Alarm dafür. Bis dahin: Resolver
  von Hand laufen lassen und `measurable_universe()` vor einem Neustart prüfen.
- **Bekannte Deckungslücke in G (dokumentiert, nicht gebaut):** der 20h-POST_WINDOW-
  Throttle bedeutet — ein Tag, dessen POST_WINDOW nie läuft (Crash, harter Stop vor
  Handelsschluss), erzeugt **keinen** Heartbeat überhaupt, nicht einmal einen `ok=False`.
  "5/5 Handelstage mit Heartbeat" (Requirement G) ist dadurch nicht strukturell garantiert,
  nur der übliche Fall. Kein Fix in dieser Session — Nikinger-Entscheidung, ob das eine
  eigene Absicherung braucht (z. B. ein "Heartbeat fehlt komplett"-Check von außen).
- **In-Memory-Sampler-Throttle:** `DivergenceSampler`s Once-per-Day-Zähler lebt nur im
  Prozess — jeder Neustart sampled jede Epic erneut am selben Tag (3 Punkte × N Epics pro
  Neustart). Bei häufigen Neustarts an einem Tag frisst das den Wochen-Budget-Puffer
  schneller als geplant; im Auge behalten, kein Bug.
- `enable_divergence_sampler` steht **default False** — Nikinger-Entscheidung, wann
  scharfgeschaltet wird (kostet echten IG-Spend, s. o.).
- **Erster echter Start ist Nikinger-Job:** `bash phase12_data_foundation/scripts/
  run_recorder.sh` standalone oder automatisch über den nächsten `run_scheduler.sh`-Start,
  plus `python phase12_data_foundation/scripts/data_health.py` als täglicher Check —
  alles live/netzwerkberührend, hier nicht ausgeführt.
- Step 7 (Gesamtintegration + Offline-Beweiskette, Wochenende), Steps 8-10 (gated, Operator).
- Uncommitted: Step-6-Dateien (s. `git status`) — Commit ist Nikinger-Entscheidung.

### Open questions / blockers

- Keine technischen (Advisor-Review dieser Session: 4 Step-4-Nachprüfungen + 1
  Step-5-Fund + 2 Step-6-Funde, alle sauber/gefixt).
- Zwei bewusst offene, dokumentierte Lücken (s. Next): die G-Deckungslücke bei einem
  POST_WINDOW-losen Tag, und der In-Memory-Sampler-Throttle über Neustarts hinweg.
- Operator-Landmine (leere `measurable_universe()`) bleibt die einzige Konsequenz, die vor
  dem nächsten Bot-Neustart aktiv gemanagt werden muss — jetzt mit drei betroffenen
  Konsumenten, aber ohne automatischen Alarm dafür (bewusst, s. Korrektur oben).
---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
