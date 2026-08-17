---
status: live
purpose: PHASE-HEAD, Phase 12 (Datenfundament) — Registry + BarService + Bar-Archiv + Recorder + Heartbeat. Steps 4+5+6 committed (49902b6, 473c8e4, 65ebec7). Step 7 (full integration + offline proof) + Step 8's two scripts (probe_allowance.py, reset_universe.py, D18) built Session 4, still UNCOMMITTED. Session 5 (2026-08-17): both real IG allowance bugs fixed. Same-day live run then found Step 8.5 (NEW, blocking Step 9): SymbolResolver built in Step 3, never wired into universe_refresher — measurable_universe() permanently empty. Step 8.5 now IMPLEMENTED + regression-green (P12 117) — still UNCOMMITTED; live proof (scheduler restart inside XETRA hours) is the Nikinger's next step. Steps 9-10 (gated, operator) come after that.
read-when: working in phase12_data_foundation/ — read this head + its newest Session-stopped block first (⚠️ operator landmine there before any bot restart — affects epic_filter, the Recorder, and the divergence sampler, but is deliberately NOT a Step-6 CRITICAL alarm); the full plan (docs/concepts/phase12_data_foundation_plan.md) is the execution contract, read its relevant §6 step block before touching anything
detail: L2
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase12_data_foundation_plan.md   # full execution-ready plan, D1-D20, Steps 0-10 (L3, ausführungsreif)
  - ../phase10_v3/PHASE11_DEFERRAL_HANDOVER.md          # why this track exists (L3, dated)
  - ../docs/architecture/data_foundation.svg            # Fehlerbild + Zielbild
  - ./SESSIONS_ARCHIVE.md                               # rotierte Session-Blöcke (L3)
updated: 2026-08-17
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

## Session stopped — 2026-08-17 (Session 5: Allowance-Bugfix + Step 8.5 SymbolResolver-Wiring)

> **Ausgangslage:** Session 4 endete mit dem exakten, Nikinger-freigegebenen Fix-Plan im
> `CLAUDE.md`-Next-Block (file:line-Anchors für beide Bugs). Diese Session war reine
> Umsetzung des vorgegebenen Plans, keine erneute Diagnose.

### Completed

1. **Bug 1 (root cause, Cross-Phase-Edit Phase 1, Nikinger-freigegeben 2026-08-17):**
   `phase1_broker_wrapper/broker_wrapper/adapters/ig_adapter.py:436` (`get_ohlcv`) UND
   `:466` (`get_historical_ohlcv`): `body.get("allowance", {})` →
   `body.get("metadata", {}).get("allowance", {})` — spiegelt IGs echten,
   Roh-Dump-verifizierten `/prices`-Shape (Session 4).
2. **Der tote Test dafür gefixt:** `phase1_broker_wrapper/tests/test_ig_adapter.py`
   — `test_get_ohlcv_happy_path_envelope_shape` (Zeile ~499) und
   `test_get_historical_ohlcv_happy_path` (Zeile ~525): Mock-Body von top-level
   `"allowance": {...}` auf `"metadata": {"allowance": {...}}}` umgestellt.
3. **Bug 2 (Sekunden→ISO-Konvertierung):**
   - `phase12_data_foundation/data_foundation/service.py`: `BudgetedIGBarProvider`
     bekommt einen `now_fn`-Parameter (Default `_default_now`, gleiche Konvention wie
     `BarService`/`SourceBudget`); `get_bars()` konvertiert `allowanceExpiry`
     (Sekunden-Restwert) via `_iso(now_fn() + timedelta(seconds=int(...)))` vor
     `budget.record_allowance(...)`, `None` bleibt `None`.
   - `phase12_data_foundation/scripts/probe_allowance.py`: gleiche Konvertierung
     (eigene kleine `_iso`-Hilfsfunktion, `datetime.now(timezone.utc)` direkt — das
     Skript hat keinen injizierbaren `now_fn`, Live-Skript, keine Tests dafür nötig).
4. **Kollateralfund beim Testlauf, nicht im Plan genannt, aber derselbe Fehlerklasse:**
   `phase12_data_foundation/tests/test_service.py::test_budgeted_ig_books_spend_and_allowance_on_success`
   mockte `allowanceExpiry` selbst als absolute-ISO-String (die alte, jetzt widerlegte
   Annahme aus `SourceBudget`s Docstring) — mit dem `int(expiry_seconds)`-Cast schlug
   das mit `ValueError` fehl. Fixture auf einen echten Sekunden-Wert (`345_600`)
   umgestellt + `now_fn=lambda: NOW` explizit übergeben, gleiche Korrektur-Logik wie
   Bug 1s Testfix (falsche Annahme, nicht Timing-Zufall).

### Verified

- `pytest phase1_broker_wrapper/tests -q` → **87 passed** (Baseline unverändert).
- `pytest phase12_data_foundation/tests -q` → **116 passed** (Baseline unverändert,
  inkl. des gefixten `test_service.py`-Falls).
- `pytest phase8_scheduler/tests -q` → **237 passed** (Baseline unverändert).
- Volle Regression, alle Phasen + root: P1 87 · P2 77 · P3 104 · P4 155 · P5 173 ·
  P6 76 · P7 138 · P8 237 · P9 80 · P10 159 · P12 116 · meta 28 · root 80 — exakt die
  Session-4-Baseline, keine Regression, keine neuen Tests nötig (reiner Bugfix +
  Testkorrektur, kein neues Verhalten).

### Next

- **Überholt durch die Nachtrag-Sektion unten:** Punkt 4 dieser Liste nannte die
  leere `measurable_universe()` noch als hinzunehmende Operator-Landmine — das ist
  jetzt Step 8.5 (s. Nachtrag), **nicht mehr** nur eine Landmine zum Umschiffen, sondern
  gefixt + regression-grün, aber noch **live unbewiesen**.
- **Nikinger-Job (freigegeben, per `feedback_live_testing`-Memory):**
  1. `probe_allowance.py` erneut laufen lassen — sollte jetzt ein echtes
     `remaining`/`expiry` in `data/bars.sqlite` schreiben (vorher strukturell blind).
  2. Sobald `remaining > 1500` beobachtet: `scripts/reset_universe.py` (keine Argumente
     nötig) — setzt die quarantined Zeilen zurück.
  3. Recorder-Warmlauf (werktags erlaubt, yF-only): `bash phase12_data_foundation/
     scripts/run_recorder.sh`.
  4. Scheduler-Neustart (`run_scheduler.sh`) — **innerhalb der XETRA-Handelszeit**
     (Mo–Fr 09:00–17:30 Berlin), damit der jetzt gewirte `SymbolResolver` seinen
     ersten echten Beweis liefern kann (s. Nachtrag für die Negativ-Kontrollen).
- Steps 9-10 (Beweiswoche, Lightstreamer) — gated auf einen laufenden Scheduler +
  einem bestätigt nicht-leeren `measurable_universe()` + 5 Handelstage, weiterhin
  kein heutiger Schritt.
- **Commit:** dieser Stand (Allowance-Bugfix + Step 8.5 Wiring + alle Session-4-
  Uncommitted-Dateien) ist commit-fertig — Nikinger-Entscheidung, ob jetzt oder nach
  dem ersten echten Live-Neustart.
- Die beiden aus Step 6 bekannten, bewusst offenen Lücken (G-Deckungslücke bei einem
  POST_WINDOW-losen Tag; In-Memory-Sampler-Throttle über Neustarts) bleiben unverändert
  offen — kein Teil dieser Session.

### Open questions / blockers

- Keine. Beide Bugs sind gefixt und über die volle Regression verifiziert; ihr erster
  echter Live-Effekt (ein `probe_allowance.py`-Lauf mit echten, nicht-leeren Werten)
  ist weiterhin unbewiesen bis zum nächsten Nikinger-Lauf — nicht mit "verifiziert"
  verwechseln (gleiche Disziplin wie der 08-11-Notbremse-Befund).

### Nachtrag (gleiche Session) — Live-Lauf gestartet, ein echter Plan↔Code-Drift gefunden: `SymbolResolver` wird nie aufgerufen

Nach dem Bugfix hat der Nikinger den vollen Stack live gestartet: `init_db.py` (Schema
war bei v5 hängengeblieben, Migration 006 fehlte real — nachgeholt, additiv, 22 Zeilen
unangetastet), `probe_allowance.py`, `reset_universe.py` (18 Epics zurückgesetzt),
Recorder (crashte initial genau an der fehlenden Migration 006, nach dem `init_db.py`-
Nachholen sauber neu gestartet, pid 33151), Scheduler mit `--enable-divergence-sampler`
(pid 33397). Alles läuft, kein KILL, `consecutive_failures=0`, `bars.sqlite` wächst
bereits (116 Zeilen/22 Epics über `BarService`-Write-Through) — **Steps 4-7 sind end-to-
end bewiesen live**, nicht nur offline.

**Aber:** `measurable_universe()` liefert weiterhin 0 (`status='active' AND
data_source_status='ok'`) — alle 22 Zeilen stehen unverändert auf `'unverified'`, auch
nach mehreren `universe_refresher`-Durchläufen (`last_universe_refresh_ts` bewegt sich,
`status` wandert discovered→verified→active, `data_source_status` nie). **Root Cause
(Grep, kein Rätsel):** `SymbolResolver` (Step 3, committed `c198ca5`) wird **an keiner
einzigen Laufzeit-Stelle instanziiert** — `grep -rn "SymbolResolver(" phase8_scheduler
phase9_universe phase12_data_foundation --include="*.py"` (Tests ausgenommen) liefert
null Treffer. `universe_refresher` (`wiring.py:855-912`) ruft `seed_curated` →
`discover` → `run_promotion_cycle` → (falls aktiv) den Divergenz-Sampler — nie den
Resolver. D6 sagt explizit „läuft wiederkehrend (im `universe_refresher`-Pass)"; Plan
§6 Step 8 Bullet 6 listet „Resolver vergibt `data_source_status`" als **erwartete
Beobachtung**, nicht als manuellen Schritt. Kein späterer Step (9/10) verdrahtet das
nach — es ist schlicht nie gebaut worden, obwohl der Plan es für Steps 3-7 vorsah.

**Folge:** ohne diesen Fix bleibt `measurable_universe()` für immer leer, der Recorder
schreibt für immer 0 Bars/Epics, Paper/Shadow-Messung startet nie — die Beweiswoche
(Step 9) kann im aktuellen Zustand **nicht bestehen**. Der laufende Live-Test ist davon
nicht bedroht (läuft harmlos weiter, produziert echte Archiv-Daten), aber er wird sich
**nicht selbst heilen**, egal wie lange er läuft. Exakt dasselbe Fehlerbild wie
`enable_ig_bars` (`PHASE11_DEFERRAL_HANDOVER.md`) — gebaut, nie scharfgeschaltet.

**Advisor-bestätigt (2026-08-17):** die zwei von `SymbolResolver.__init__` benötigten
Callables sind an der `universe_refresher`-Stelle bereits vorhanden, kein neues
Plumbing nötig — `broker` (closure-Variable, `broker.get_price(epic).data` liefert
`{bid, ask}`) und `research.market_data` (bereits verdrahteter `MarketDataFetcher`,
`.get_last_price(symbol) -> tuple[float, str] | None` — exakt die von `SymbolResolver`
erwartete Signatur, `phase3_external_data/external_data/fetcher.py:464`, Commit
`066949f` wurde genau dafür gebaut). Der Fix ist damit ein additiver ~5-10-Zeilen-Call
in `universe_refresher`, kein Redesign — aber ein Cross-Phase-Edit an einer
Bot-berührenden Datei, während der Bot live läuft, und eine **neue** Entdeckung ohne
vorab abgestimmten Fix-Plan (anders als der Allowance-Bugfix oben). Root-`CLAUDE.md`
+ Phase-12-`Rahmen` legen sowas auf Wochenende/Nikinger-Freigabe.

**Nikinger-Entscheidung (gleiche Session):** sofort wiring, aber über eine eigene
Plan-Mode-Session (nicht spontan inline) — als neuer **Step 8.5** im Plan-Dokument
festgehalten (`docs/concepts/phase12_data_foundation_plan.md`, zwischen Step 8 und
Step 9, explizit **blockierend für Step 9**). Plan-Session ist der nächste Schritt.

**Plan-Mode-Session (Fortsetzung):** execution-ready Plan gespeichert unter
`/home/trading-bot/.claude/plans/cheeky-floating-hopcroft.md` (Repo-extern,
`~/.claude/plans/`) — Change an `phase8_scheduler/scripts/wiring.py` innerhalb
`universe_refresher()`, zwischen `run_promotion_cycle(...)` und dem
`divergence_sampler`-Block. Session endete ohne Umsetzung.

**✅ Umsetzungs-Session (2026-08-17, Fortsetzung):** eigene Plan-Mode-Session gegen den
aktuellen Code re-verifiziert (alle Anker exakt bestätigt — `universe_refresher` weiterhin
`wiring.py:855-912`, `SymbolResolver.__init__`-Kwargs alle mit Defaults, `get_price(epic)
.data`→`{bid,ask}`, `get_last_price`→`fetcher.py:464`); finaler Plan
`/home/trading-bot/.claude/plans/peaceful-juggling-lemon.md` (supersedet
`cheeky-floating-hopcroft.md`), Nikinger-freigegeben, **implementiert**:
- `wiring.py`: `SymbolResolver(...).resolve_universe()`-Call zwischen
  `run_promotion_cycle` und dem Sampler-Block (Zeile ~893) + `logger.info` mit den
  vollen `ResolverReport`-Zählern (macht den künftigen Live-Beweis falsifizierbar,
  nicht nur "es lief").
- **Zwei Korrekturen ggü. der ursprünglichen Planpass-Fassung**, beide vor Umsetzung
  verifiziert: (1) ein Test ist doch nötig — der Plan-Doc-Eintrag für Step 8.5 verlangt
  ihn explizit, die "`wiring.py` hat keine Testsuite"-Konvention verbietet nur
  *Laufzeit*-Imports (`test_run.py:3`), keinen statischen Check; neue
  `phase12_data_foundation/tests/test_resolver_wiring.py` (AST-Guard, Vorbild
  `test_isolation.py`) prüft, dass `universe_refresher`s Funktionskörper einen
  `SymbolResolver(`-Call enthält. (2) Namenskorrektur: die throttelnde Methode heißt
  `_maybe_refresh_universe`, nicht `_maybe_run_universe_refresher`.
- Status-Konstanten gegengecheckt: `_STATUS_ACTIVE`/`_STATUS_DISCOVERED` = `"active"`/
  `"discovered"`, identisch zu `universe/models.py` — kein Drift.
- **Verifiziert:** `py_compile` clean; volle Regression unverändert außer P12:
  P1 87 · P2 77 · P3 104 · P4 155 · P5 173 · P6 76 · P7 138 · P8 237 · P9 80 · P10 159 ·
  **P12 117** (116+1) · meta 28 · root 80. Acceptance-Grep `SymbolResolver(` zeigt eine
  echte Call-Stelle (Zeile 893).
- **Live-Beweis bleibt Nikinger-Job** (`feedback_live_testing`) — der laufende
  Scheduler (pid 33397) braucht einen Neustart, ein Datei-Edit wirkt nicht auf einen
  bereits laufenden Prozess. **Zeitfenster beachten:** der Resolver bucht eine
  Beobachtung nur bei offenem Markt (XETRA Mo–Fr 09:00–17:30 Berlin) UND einem
  yFinance-Balken jünger als 30 Min — ein Neustart außerhalb dieses Fensters lässt alle
  22 Epics bei `unverified`, ununterscheidbar vom unreparierten Bug. Europäische Epics
  sollten sofort auflösen; US-Epics erst nach ~15:30 Berlin (US-Handelsüberlappung).
  Negativ-Kontrollen (unterscheidbar über die neue `logger.info`-Zeile): `checked=22,
  ok=0` ohne Writes = Markt zu/inconclusive; `checked=0` oder keine Log-Zeile = weiterhin
  kaputt. Danach `measurable_universe()` + nächster Recorder-Tick (`epics > 0`) prüfen.
- **Commit:** dieser Stand (Wiring + Test + Doku, plus alle vorherigen Session-4/5-
  Uncommitted-Dateien) ist commit-fertig — weiterhin Nikinger-Entscheidung, ob jetzt
  oder nach dem ersten echten Live-Neustart.

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
