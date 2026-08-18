---
status: archive
purpose: Verbatim session-history archive rotated out of `CLAUDE.md`
read-when: auditing how a past Phase-12 decision came about — never needed at session start
detail: L3
up: ./CLAUDE.md
updated: 2026-08-17
---

# phase12_data_foundation — Session Archive

> The blocks below were moved here **verbatim, unedited** from `CLAUDE.md` per the Doc-Layers
> rotation rule ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)). Source order
> preserved (newest-first). The newest `## Session stopped` block always stays in the source file;
> at each session end, the previously-newest block rotates here.

## Session stopped — 2026-08-17 (Session 7: P12.5 Steps 1–3 — U1/U3/Entscheidung B + U2/U5, pausiert nach Nikinger-Auftrag)

> **Auftrag:** `PHASE12_5_MEASUREMENT_ARM_PLAN.md` ausführen (execution-ready, E1–E9
> gelockt). Umfang dieser Session: Steps 1–3 (Housekeeping, phasen-interne Fixes, die zwei
> freigabepflichtigen Cross-Phase-Fixes). Steps 4–7 (Neustart, falsifizierbarer Nachweis,
> Beweiswoche, Handover) sind Nikinger-/Operator-Arbeit und **nicht** Teil dieser Session —
> Nikinger-Auftrag nach Step-3-Freigabe war explizit „vollständigen Step 3, danach
> pausieren".

### Completed

1. **Step 1 (Housekeeping, No-Op):** Legacy-Grep sauber (nur der bekannte, frozen
   `turbo_candidates.json`-Rest). Fünf Statusdokumente (Root-`CLAUDE.md`, `ROADMAP.md`,
   `docs/INDEX.md`, dieser Kopf, `README.md`) gegen Code geprüft — **keine Abweichung**,
   alle sagen korrekt „Steps 0–8.5 fertig, Step 9 nicht begonnen". Regression-Baseline
   aller Phasen gemessen (s. u.) — deckt sich exakt mit dem Plan-§8.2-Erwartungswert.
   Kein Commit für diesen Step (reiner No-Op-Befund, keine Datei geändert — „less is
   sometimes more").
2. **Step 2 (`data_foundation/`, phasen-intern, Commit `83d5ef3`):**
   - **U1** (`service.py:119`): `BudgetedIGBarProvider.get_bars` normalisiert jetzt IGs
     Roh-Timestamp über `normalize_bar_ts`, fängt `ArchiveError` in ein
     `bad_timestamp`-`bar_fetch`-Event statt es hochzuwerfen zu lassen (E1/E2). Heilt
     `DivergenceSampler`s lexikalischen Timestamp-Vergleich mit, weil `service.py` die
     einzige Stelle ist, an der IGs Rohformat einläuft — **end-to-end bewiesen**, nicht
     nur behauptet: `test_heartbeat.py`s IG-Fake läuft jetzt durch den echten
     `BudgetedIGBarProvider` mit einem Rohformat-Broker statt eines Stand-ins, der die
     Normalisierung übersprang.
   - **U3** (`service.py:207`): `_MIN_WINDOW_COVERAGE = 0.5`-Schwelle neben dem
     bestehenden `_covers_tail`-Check — ein kurzes-aber-tail-deckendes Archiv
     kurzschließt nicht mehr. `:217` (IG-Top-up) unangetastet (E4).
   - **Entscheidung B** (`heartbeat.py`): `assess_day` flaggt `shadow_enabled=False`
     jetzt unbedingt als Problem + `ok=False` — genau die Tag-1-Situation, die live
     `ok=True` meldete.
   - Ein bestehender `assess_day`-Test (`test_assess_day_no_measurable_epic_is_ok_with_problem_note`)
     musste umgebaut werden (mit `shadow_enabled=True` + einem realen Resolve isoliert),
     sonst hätte E8 seine eigentliche Aussage (measurable_epics==0 allein ist nur eine
     Notiz) überdeckt — kommentiert im Testfile.
   - `phase12_data_foundation` Tests: **117 → 122** (5 neu: 2 Provider, 2 `get_window`,
     1 `assess_day`).
3. **Step 3 (Cross-Phase, Nikinger-Freigabe per AskUserQuestion: „Vollständigen step 3,
   danach pausieren", Commit `ff5741c`):**
   - **U2** (`phase10_v3/abstain_lessons/paper.py:588`): `resolve_paper_trade`s
     `outcome is None` bedeutet an **beiden** Return-Stellen „noch nicht genug Bardaten",
     nie „kein Ergebnis" — `_resolve_group` belastet jetzt den Retry-Cap statt beim ersten
     Miss sofort abzuschreiben. Docstring-Korrektur (E6) an zwei Stellen:
     `_charge_failed_attempt` (paper.py) und der zugehörige Kommentar in `wiring.py:468-480`
     (behauptete fälschlich, der Fall sei bereits abgedeckt).
   - Ein bestehender Test (`test_tracker_marks_expired_when_unresolvable`) kodierte exakt
     den Vorher-Bug (sofortiges Expiry bei leeren Bars) — ersetzt durch
     `test_tick_charges_attempt_instead_of_expiring_on_empty_bars` (bleibt OPEN, Attempt-
     Zähler 1) + `test_tick_expires_after_the_attempt_cap` (12 leere Ticks ⇒ expiriert
     trotzdem, Cap-Verhalten unverändert). Den Plan-Vorschlag für einen dritten
     (Healthy-Path-Regressions-)Test bewusst ausgelassen — deckt sich mit dem bereits
     bestehenden `test_tracker_resolves_due_trade_and_marks_resolved`.
     `phase10_v3`: **159 → 160**.
   - **U5** (`phase8_scheduler/scripts/wiring.py:805`): `shadow_pair_scheduler`s
     `deadline` zieht jetzt zwei Zyklus-Intervalle von `window_close` ab —
     `window_close` selbst ließ der letzten Tages-Kohorte (13:30-Öffnung) null
     Tracker-Ticks (Tracker läuft nur in WINDOW, die Kohorte wird fällig genau beim
     Phasenwechsel zu POST_WINDOW). **Pflicht-Gegenprobe durchgeführt** (§8.3):
     `window_close="17:30"` + `cycle_interval_min=5` ⇒ Deadline landet exakt auf **17:20**.
     `wiring.py` hat keine eigene pytest-Suite (dokumentierte Konvention) — verifiziert
     via `py_compile` (sauber) + neuer AST-Guard
     (`phase12_data_foundation/tests/test_shadow_deadline_margin.py`, spiegelt
     `test_resolver_wiring.py`). `phase12_data_foundation`: **122 → 123**.
   - Volle Cross-Phase-Regression nach Step 3 grün und **unverändert** außerhalb der
     beiden berührten Phasen: P1 87 · P2 77 · P3 104 · P4 155 · P5 173 · P6 76 · P7 138 ·
     P8 237 · P9 80 · meta 28 · root 80 — deckt sich exakt mit Plan-§8.2.
4. **Bot unangetastet.** Scheduler (`pid 35195`) und Recorder (`pid 33151`) liefen zu
   Beginn dieser Session unverändert seit dem Pre-Proof-Handover — kein Stop/Restart,
   keine Live-/Netz-Aktion (Plan §1, unverändert Nikinger-Job).

### Verified

- `pytest phase12_data_foundation/tests -q` → **123 passed**.
- `pytest phase10_v3/tests -q` → **160 passed**.
- Volle Phasen-Regression (s. o.) — jede Zahl deckt sich mit dem Plan-§8.2-Erwartungswert,
  außer den beiden bewusst geänderten Phasen.
- U5-Deadline-Rechnung von Hand nachgerechnet: `17:30 - 2×5min = 17:20` ✓.

### Next

- **Step 4 (Nikinger, live):** laufenden Scheduler **erst stoppen**
  (`ps aux | grep scheduler.run` als Gegenprobe — Parallel-Login-Falle), dann
  `bash phase8_scheduler/scripts/run_scheduler.sh --enable-divergence-sampler --enable-shadow-schedule`.
- **Step 5 (am Starttag, nicht am Freitag):** der vierteilige falsifizierbare Nachweis
  (echte argv · Config-Default zurückgelesen · eine Zeile Live-Paper-Trades ·
  zweiteiliger Alarm-Positivtest d-i/d-ii) — Plan §4 Step 5, wörtlich befolgen, nicht
  paraphrasieren.
- **Step 6:** Beweiswoche als reiner Watch-Auftrag (5 Handelstage), Freitags-Review gegen
  Plan §7 A–G + Kern.
- **Step 7:** Handover ⇒ Phase 12 zu, inkl. Doku-Sync (Root-`CLAUDE.md`, `ROADMAP.md`,
  `docs/INDEX.md`, `README.md`, Memory-Updates).
- Diese Session hat **nicht** committet in Richtung `origin/main` gepusht — lokal auf
  `main`, zwei Commits (`83d5ef3`, `ff5741c`) über dem zuletzt gepushten Stand
  (`cc3770e`). Push ist wie gehabt eine bewusste, separate Freigabe.

### Open questions / blockers

- Keine technischen Blocker für Step 4 — beide Cross-Phase-Fixes sind committed + grün.
- Step 4 selbst ist der Blocker für alles Weitere: ohne den Neustart mit beiden Flags
  misst nichts.

---

## Session stopped — 2026-08-17 (Session 6: Tag-1-Live-Auswertung + Pre-Proof-Handover)

> **Auftrag:** Auswertung des ersten vollen Handelstags mit dem kompletten Stack, Antwort
> auf die offenen Fragen aus Session 5, Vorschlag für die Zeit nach Steps 9/10 — und der
> Handover. **Kein Bot-berührender Code angefasst** (Werktag, Bot läuft): read-only DB
> (`mode=ro`), Doku, `.gitignore`. Alle Zahlen unten selbst erhoben, keine aus früheren
> Blöcken übernommen.
>
> **Vollständiges Ergebnis: [`PHASE12_PREPROOF_HANDOVER.md`](./PHASE12_PREPROOF_HANDOVER.md)**
> — dieser Block ist die Kurzfassung, nicht die Quelle.

### Completed

1. **Tag-1-Live-Auswertung** (Recorder `pid 33151` seit 09:56 CEST, Scheduler `pid 35195`
   seit 12:09 CEST mit `--enable-divergence-sampler`). Ergebnis: die Kette
   Resolver → Registry → `measurable_universe()` → Recorder/BarService → `bars.sqlite`
   läuft end-to-end **live**, ohne Operator-Eingriff (Details: Handover §2).
2. **`PHASE12_PREPROOF_HANDOVER.md`** (neu) — Status, Tag-1-Ergebnisse, die drei Befunde
   vor Step 9, Delta gegen `PHASE11_DEFERRAL_HANDOVER.md` (A–G), Entscheidungen A–D,
   Vorschlag für nach Steps 9/10.
3. **`../docs/architecture/phase12_preproof.svg`** (neu, 1080×1080) — was steht, was fehlt,
   warum der Alarm es nicht merkt.
4. **Statuspflege** im selben Commit: Root-`CLAUDE.md`, `ROADMAP.md`, `docs/INDEX.md`,
   dieser Phasenkopf, Rotation des Session-5-Blocks nach `SESSIONS_ARCHIVE.md`.
5. **`.gitignore`**: `data/state/recorder.pid` + `data/state/recorder_state.json` ergänzt
   (Phase-12-Laufzeitdateien, waren als einzige Dateien unter `data/` nicht ignoriert —
   ein `git add -A` hätte Laufzeitstand committet; gleiche Einzelpfad-Konvention wie
   `llm_usage.json`/`execution_state.json`).
6. **Doku-Korrektur gegen Code** (Code gewinnt, datiert vermerkt): Phasenkopf und
   `docs/INDEX.md` behaupteten „Steps 7/8/8.5 uncommitted" — `47d89b0` (+ `37f2f0a`) haben
   sie gelandet. Korrigiert.

### Verified

- **Registry:** 22 Zeilen → 5 `active`/`ok`, 3 `active`/`no_intraday_source` (SUN*), 13
  `verified`/`unverified`, 1 `quarantined`. `measurable_universe()` erstmals **nicht leer**
  ⇒ **Step 8.5 ist live bewiesen**, nicht nur regression-grün.
- **Resolver-Timing:** Pass 1 `10:14:38Z` (Startup-erzwungen — `runner.py:285` ruft
  `_run_universe_refresher()` im Preflight, **vor** der 240-Min-Drossel; korrigiert die
  Session-5-Operator-Notiz, die einen unklaren Wartezeitraum nahelegte), Pass 2 `12:19Z`.
- **Recorder:** erster 1m-Write `10:16:32Z` = **114 s** nach dem ersten Resolver-Write;
  62 Fetch-Batches im 5-Min-Takt, `errors: []`.
- **Archiv:** 1891 Bars, **alle heute** geschrieben.
- **Allowance-Bugfix aus Session 5 wirkt live:** 28 echte `allowance_observations`
  (`total=10000`, `remaining=9724`, `expiry=2026-08-23T20:53Z`), Verbrauch 136 Punkte —
  damit ist die letzte offene Frage aus Session 5 („erster echter Live-Effekt") **geschlossen**.
- **Step-6-Operator-Pfad erstmals real gelaufen:** `data_health.py --day 2026-08-17` →
  `ok: True`, Exit `0`.
- `pytest phase12_data_foundation/tests -q` → **117 passed** (heute nachgelaufen).

### Befunde (Details + Belege: Handover §3)

- 🔴 **Blockierend:** `enable_shadow_schedule` ist Default `False` und im laufenden Prozess
  nicht gesetzt ⇒ **0 Paper-Zeilen heute** (letzte überhaupt 2026-08-07). Der
  abstain-getriebene Pfad kann das nicht auffangen (`open_shadow_pair` braucht ein Epic;
  1465 von 1476 `abstain_records` haben `epic IS NULL`) ⇒ der H1-Timer ist der **einzige**
  lebende Messarm. Plan §7 „Kern" ⇒ **Step 9 kann so nicht bestehen.**
- 🟠 `assess_day`s Bedingung (b) hängt selbst an `shadow_enabled` ⇒ ein Nulltag meldet
  `ok=True`. Requirement G ist im Ist-Zustand blind für genau den laufenden Ausfall —
  heute live vorgeführt.
- 🟡 3 der 8 Aktiv-Plätze halten SUN*-Epics (`max_active=8`, `promotion.py` kennt
  `data_source_status` nicht) ⇒ messbarer Pool auf 5 gedeckelt.
- 🟡 **Nur Befund, fremder Scope:** `reason_no_candidates` vermischt „keine Daten" mit
  „LLM enthält sich bewusst" (der feinere Name `REASON_LLM_ABSTAIN` existiert bereits
  scheduler-seitig); `market_regime_snapshots` ist zu 100 % (1162/1162) degradiert leer.
- 🔴 **Nachtrag gleiche Session — Ultrareview, vier Befunde, alle gegen den Code
  nachverifiziert, keiner gefixt** (Analyse/Fix-Trennung, Werktag, Bot läuft). Details +
  Fix-Orte: Handover §3.0. Kurz:
  **U1** `DivergenceSampler` crasht an IGs `yyyy/MM/dd HH:mm:ss` (`heartbeat.py:175` parst
  mit `fromisoformat`, `service.py:119` normalisiert nicht) — Drossel wird vor dem Crash
  gesetzt, die Ausnahme killt die Epic-Schleife ⇒ **Kriterium C tot**. **Live belegt:**
  je Pass genau ein Epic, jeweils das nächste (`research_health.jsonl`) — meine frühere
  Aussage „Sampler läuft" war damit falsch und ist im Handover korrigiert.
  **U2** Retry-Cap des Paper-Trackers wirkungslos, weil `get_window` nie wirft
  (`wiring.py:514-517`, Kommentar `:477-480` behauptet das Gegenteil).
  **U3** `_covers_tail` prüft nur das Fensterende, nie den Anfang (`service.py:254-261`).
  **U4** Scheduler-`TickerMapper` wird nur beim Start befüllt (`wiring.py:175-180`) —
  reine Kostenfrage, heilt beim Neustart.
  ⇒ **Entscheidung A im Handover ist korrigiert:** erst U1–U3 fixen, dann Neustart,
  dann Step 9. „Nur ein Flag" reicht nicht mehr.

### Next

- **Nikinger-Entscheidungen A–D** (Handover §5). **A ist blockierend für Step 9:**
  laufenden Scheduler **erst stoppen** (Parallel-Login-Falle — sonst zwei IG-Sessions),
  `ps aux | grep scheduler.run` als Gegenprobe, dann
  `bash phase8_scheduler/scripts/run_scheduler.sh --enable-divergence-sampler --enable-shadow-schedule`
  — danach binnen ~30 Min neue `SHADOW_BUY`/`SHADOW_SELL`-Zeilen erwarten.
- Danach erst Step 9 (Beweiswoche, 5 Handelstage, täglich `data_health.py`), dann Step 10.
- Vorschlag für nach 9/10: Funnel-Reason-Split → Promotion lernt `data_source_status` →
  Phase-11/WI-2-Wiederaufnahme (Handover §6). Nummerierung entscheidet der Nikinger.
- Die zwei bekannten Step-6-Lücken (G-Deckung an einem POST_WINDOW-losen Tag;
  In-Memory-Sampler-Throttle über Neustarts) bleiben unverändert offen.
- ⚠️ **Rahmen-Änderung (Nikinger, 2026-08-17):** die Wochenend-Regel ist aufgehoben —
  gearbeitet wird ab jetzt **direkt unter der Woche**, auch bot-berührend, weil der Bot
  ohne U1–U3 nicht gescheit läuft. Für die Planungssession verbindlich; s. `## Rahmen`
  oben und Handover §1a.
- **Gepusht:** dieser Stand ist auf `origin/main` (Nikinger-Freigabe 2026-08-17).

### Open questions / blockers

- **Blocker für Step 9: Entscheidung A** (U1–U3 fixen + Messarm einschalten). Ohne sie
  misst die Beweiswoche nichts und läuft in einen garantierten FAIL.
- Entscheidung D (Push) ist **erledigt** — der Nikinger hat freigegeben, `main` ist
  gepusht.

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

## Session stopped — 2026-08-16 (Session 4: Step 7 — Gesamtintegration + Offline-Beweiskette)

> **Ausgangslage (Advisor-bestätigt, kein Re-Plan nötig):** der Großteil von Step 7 war
> bereits in Steps 4/6 gebaut — `_build_data_foundation` (einmal, verifiziert), BarService in
> Research+Tracker, `epic_filter`, `daily_health_check`-Closure inkl. echter
> `SchedulerRunner(...)`-Kwarg-Übergabe. Diese Session war daher **Verifikation + zwei echte
> Lücken schließen**, kein Neubau.

### Completed

1. **CLI-Lücke geschlossen** (Advisor-Fund, Plan §9.9): `enable_divergence_sampler` (D12) und
   `enable_measurement_heartbeat` (D13) hatten seit Step 6 **keinen** CLI-Arm in
   `scheduler/run.py` — nur `--no-bar-service` (Step 4) existierte. „Der Nikinger
   scharfschaltet bewusst" war damit ohne Code-Edit operativ unmöglich, exakt die
   `enable_ig_bars`-Fehlerklasse (gebaut, nie erreichbar), die diese Phase beheben soll.
   Gefixt: `--enable-divergence-sampler` (store_true, Default OFF, spiegelt
   `--enable-shadow-schedule`s Muster) + `--no-measurement-heartbeat` (store_true, Default
   Heartbeat AN, spiegelt `--no-bar-service`s Muster) in `phase8_scheduler/scheduler/run.py`,
   beide in `config_from_args` verdrahtet. +2 Tests in `test_run.py`
   (`test_enable_divergence_sampler_flag_threads_through`,
   `test_no_measurement_heartbeat_flag_threads_through`).
2. **Synthetischer Tag — der geplante Step-7-Beweis** (Plan §6 Step 7, Akzeptanz-Bullet 2):
   neu `phase12_data_foundation/tests/test_step7_integration.py`. Komponiert, was Steps 1-6
   isoliert getestet hatten, zum ersten Mal zusammen: `BarArchive` mit vorab geschriebenen
   yF-Bars (simuliert den Recorder), `BarService` mit einer **`_RaisingProvider`**-Chain (wirft
   bei jedem Aufruf — beweist "zero chain calls", nicht nur "keiner beobachtet"), zwei direkt
   konstruierte Both-Sides-Shadow-`PaperTrade`s (BUY/SELL, `PaperTrade.new()`s echte
   Wanduhr-`created_utc` umgangen — gleiche Konvention wie `test_paper.py`s eigene
   Direkt-Konstruktion), `PaperTradeTracker.tick()` mit `bar_fetch = bar_service.get_window`,
   dann `assess_day` auf derselben synthetischen DB. Beweist: beide Trades lösen exakt aus dem
   Archiv auf (SL/TP, kein Chain-Call), `resolution_source == 'yf'` in beiden Zeilen,
   `assess_day` meldet `ok=True`, `measurable_epics=1`, `pairs_opened=2`, `pairs_resolved=2`,
   `problems=[]`. **Bewusst positiv assertiert** (Advisor-Warnung ernst genommen: ein
   sorglos leerer Zustand hätte `ok=True` auch **ohne** echte Messung geliefert, weil
   `measurable_epics==0` nur eine Problem-Notiz ist, kein Alarm — dieser Test seedet die
   Universe-Zeile explizit auf `data_source_status='ok'`, sonst wäre er ein toter Check).
3. **Doku-Drift gefixt** (Session-Start): `CLAUDE.md`s Header behauptete „Step 6 done this
   session, UNCOMMITTED" — `git log`/`git status` zeigten Step 6 bereits als Commit `65ebec7`,
   Baum sauber. Reine Faktenkorrektur, kein Code betroffen.

### Verified

- `pytest phase12_data_foundation/tests -v` → **110 passed** (war 109, +1: der neue
  Integrationstest).
- `pytest phase8_scheduler/tests -v` → **237 passed** (war 235, +2: die neuen CLI-Flag-Tests).
- Volle Regression, alle 12 Phasen + root: P1 87 · P2 77 · P3 104 · P4 155 · P5 173 · P6 76 ·
  P7 138 · **P8 237** · P9 80 · P10 159 · **P12 110** · meta 28 · root 80.
- Offline-Smoke (`phase8_scheduler/scripts/smoke_test.py`) 3/3 PASS.
- **Akzeptanz-Greps (Plan §6 Step 7, „kein vierter Patch"):**
  `grep -rn "KNOWN_YF_TICKERS" --include="*.py"` → nur noch der `test_criterion_a.py`-Grep-Test
  selbst (kein Deklarations-Fund mehr). `grep -rn "enable_ig_bars" --include="*.py"` → nur
  `phase4_research`s eigenes, unabhängiges Flag (außerhalb Scheduler-Laufpfad,
  außerhalb Phase-12-Scope) + erklärende Kommentare — keine vierte IG-Bar-Direktleitung.
- **`_build_data_foundation` genau einmal aufgerufen** (`wiring.py:744`) — kein zweiter
  `bars.sqlite`-Connection-Aufbau, kein Locking-Risiko (Plan §8).
- **`daily_health_check` wirklich an `SchedulerRunner(...)` übergeben** (`wiring.py:976`,
  nicht nur die Closure darüber definiert) — bestätigt gegen genau die Advisor-Sorge, dass ein
  definierter-aber-nie-durchgereichter Callable dieselbe Fehlerklasse wie `enable_ig_bars`
  reproduziert hätte.

### Nachtrag (gleiche Session) — Step 8: die zwei fehlenden D18-Skripte gebaut

Der Nikinger fragte nach den heute (Wochenende, Markt zu) ausführbaren Schritten. Plan
§6 Step 8 referenziert zwei Skripte, die in Steps 1-7 nie gebaut wurden:
`scripts/probe_allowance.py` und `scripts/reset_universe.py` (beide nur in D18/§6 als
Namen genannt, nie als Datei angelegt — ein echter Plan↔Code-Drift, jetzt geschlossen).

- **`phase12_data_foundation/scripts/probe_allowance.py`** (neu): wrappt den bekannten
  CLI-Einzeiler (`ALLOWANCE_INCIDENT_2026-08-08.md` §6, `get_ohlcv(epic, "MINUTE", 5)`,
  5 Punkte) und bucht Erfolg via `SourceBudget.record_spend(5, "probe")` +
  `record_allowance(...)` in `data/bars.sqlite` — genau die Beobachtung, die
  `reset_universe.py`s D18-Gate liest. Live/Netz/Keyring — nicht diese Session ausgeführt.
- **`phase12_data_foundation/scripts/reset_universe.py`** (neu): `_check_restart_gate`
  (pure Funktion) verweigert den Reset ohne eine **frische** (< 24h) `allowance_observations`-
  Zeile mit `remaining > reserve_points` (D18) — liest `data/bars.sqlite` direkt (kein
  `SourceBudget`-Objekt nötig, reiner Lesezugriff). Bei Freigabe: setzt alle `quarantined`-
  Zeilen in `instrument_universe` auf `status='discovered', fail_count=0,
  last_verified_at=NULL` (Präzedenzfall 2026-07-06, damals manuelles SQL — jetzt ein
  wiederholbares Skript). `--force` als dokumentierter, absichtlicher Overrde (nicht
  Default). Live, schreibt die echte Trading-DB — nicht diese Session ausgeführt.
- **Test:** `phase12_data_foundation/tests/test_reset_universe.py` (neu, 6 Tests, via
  `importlib.util` geladen — gleiche Konvention wie `verify_instrument.py`, das Skript
  liegt außerhalb des installierten Pakets) — deckt alle vier Gate-Zweige (keine Tabelle,
  keine Beobachtung, zu alt, `remaining <= reserve`) + den Erfolgsfall + die
  24h-Grenze exakt. Nur `_check_restart_gate` getestet (pure), nicht `main()`
  (Netz/DB-Writes — Nikinger-Job).
- **Verifiziert:** `pytest phase12_data_foundation/tests -v` → **116 passed** (war 110,
  +6). `--help` beider Skripte lädt sauber (kein versehentlicher Netz-Import am Modul-Top).
  Gate live gegen eine leere synthetische `bars.sqlite` durchexerziert (kein
  echtes Repo-`data/` berührt): verweigert korrekt, exit 1, JSON auf stdout.

### Next

- **SOFORT-NÄCHSTER SCHRITT (freigegeben, Nikinger 2026-08-17, kein Re-Ask nötig):** die
  zwei Allowance-Bugs fixen, **bevor** irgendein weiterer `probe_allowance.py`-Lauf Sinn
  ergibt — der Probe bleibt sonst strukturell blind (`allowance={}` egal wie oft man
  läuft). Exakter Fix-Plan, keine erneute Diagnose nötig:
  1. `phase1_broker_wrapper/broker_wrapper/adapters/ig_adapter.py:436` UND `:466`:
     `allowance = body.get("allowance", {})` → `allowance = body.get("metadata", {}).get("allowance", {})`.
  2. `phase1_broker_wrapper/tests/test_ig_adapter.py:499` (und der `{}`-Fall um Zeile 525):
     Mock-Body auf die echte `{"metadata": {"allowance": {...}}}`-Verschachtelung umstellen —
     sonst bleibt der Test grün gegen die falsche Annahme (toter Check).
  3. `phase12_data_foundation/data_foundation/service.py`s `BudgetedIGBarProvider.get_bars()`
     UND `phase12_data_foundation/scripts/probe_allowance.py`: `allowanceExpiry` ist
     Sekunden-Restwert, nicht absolutes ISO — vor `record_allowance(...)` konvertieren:
     `expiry_iso = _iso(now_fn() + timedelta(seconds=int(allowanceExpiry)))` (nur wenn
     `allowanceExpiry is not None`, sonst `None` durchreichen wie bisher).
  4. Volle Regression (mind. P1 + P12 + P8, dann alle Phasen) + `pytest -v` grün.
  5. **Dann erst** `probe_allowance.py` erneut (Nikinger-Lauf) — sollte jetzt ein echtes
     `remaining`/`expiry` in `data/bars.sqlite` schreiben.
- **Danach, heute noch möglich (Nikinger, per `feedback_live_testing`-Memory):**
  1. `probe_allowance.py` (s. o., jetzt mit echten Daten).
  2. Sobald `remaining > 1500` beobachtet: `... scripts/reset_universe.py`
     (kein Argument nötig — Defaults zeigen auf `data/trading_bot.sqlite`/`data/bars.sqlite`)
     — setzt die quarantined Zeilen zurück.
  3. Recorder-Warmlauf (werktags erlaubt, yF-only):
     `bash phase12_data_foundation/scripts/run_recorder.sh`.
  4. **Erst danach**, falls gewünscht: Scheduler-Neustart (`run_scheduler.sh`) — beachtet
     die Operator-Landmine unten.
- Steps 9-10 (Beweiswoche, Lightstreamer) — gated auf einen laufenden Scheduler + 5
  Handelstage, kein heutiger Schritt.
- **Erster echter Start ist weiterhin Nikinger-Job**, unverändert seit Step 6: Recorder
  standalone oder über `run_scheduler.sh`, `data_health.py` als täglicher Check — vor jedem
  Neustart die Operator-Landmine (leere `measurable_universe()` bis der Resolver lief)
  beachten.
- Uncommitted: diese Session (`run.py`, `test_run.py`, `test_step7_integration.py`,
  `probe_allowance.py`, `reset_universe.py`, `test_reset_universe.py`,
  `diag_allowance_raw.py`, `CLAUDE.md`, `SESSIONS_ARCHIVE.md`, s. `git status`) — Commit
  ist Nikinger-Entscheidung (frühestens nach dem Allowance-Bugfix oben, sonst commitet man
  ein bekannt-blindes `probe_allowance.py` mit).
- Die beiden aus Step 6 bekannten, bewusst offenen Lücken (G-Deckungslücke bei einem
  POST_WINDOW-losen Tag; In-Memory-Sampler-Throttle über Neustarts) bleiben unverändert offen
  — kein Teil dieser Session.

### Open questions / blockers

- Keine technischen. Step 7s Plan-Akzeptanz ist vollständig erfüllt (Smoke 3/3,
  synthetischer Tag, volle Regression, Akzeptanz-Greps). Die zwei D18-Skripte sind
  offline verifiziert, aber **ihr erster echter Lauf ist unbewiesen** — nicht mit
  "verifiziert" verwechseln (gleiche Disziplin wie der 08-11-Notbremse-Befund).
- **Echter Bug, live gefunden + gefixt (Nikinger-Lauf, 2026-08-16):** `probe_allowance.py`
  rief `get_ohlcv` ohne vorheriges `broker.connect()` — `AUTH_ERROR "not connected"`.
  Gefixt nach `verify_instrument.py`s Muster (`connect()` vor dem ersten Call, Fail-Fast
  bei `connect_env.ok is False`), kein `disconnect()` (In-Memory-Session heilt sich laut
  `reference_ig_parallel_login_trap`-Memory selbst, gleiche Konvention wie das Vorbild).
- **Empirische Frage aufgelöst — zwei echte Bugs gefunden (Nikinger-Lauf 2026-08-17,
  Dienstag, Markt offen 09:13):** der 08-16-Sonntags-Befund („`allowance={}`, evtl.
  Markt-zu") ist **falsifiziert** — derselbe Probe mit offenem Markt lieferte immer noch
  `allowance={}`. Root-Cause per Roh-Dump ermittelt: `phase12_data_foundation/scripts/
  diag_allowance_raw.py` (neu, gebaut + verifiziert diese Session) ruft `broker._request()`
  direkt auf und zeigt IGs **echten** `/prices`-Response-Shape:
  ```json
  {"prices": [...], "instrumentType": "INDICES",
   "metadata": {"allowance": {"remainingAllowance": 9985, "totalAllowance": 10000,
                               "allowanceExpiry": 567432},
                "size": 5, "pageData": {...}}}
  ```
  **Bug 1 (root cause des leeren `allowance`):** `phase1_broker_wrapper/broker_wrapper/
  adapters/ig_adapter.py` liest in `get_ohlcv` (Zeile 436) UND `get_historical_ohlcv`
  (Zeile 466) `allowance = body.get("allowance", {})` — IG verschachtelt es aber unter
  `metadata.allowance`, nicht top-level. Fix: `body.get("metadata", {}).get("allowance", {})`
  an beiden Stellen. **Der P1-Test dafür ist selbst ein toter Check:**
  `phase1_broker_wrapper/tests/test_ig_adapter.py:499` mockt den Response-Body mit
  `allowance` **top-level** (spiegelt exakt die falsche Code-Annahme, nicht IGs echten
  Shape) — muss beim Fix auf die `metadata`-Verschachtelung umgestellt werden, sonst bleibt
  der Test grün und blind.
  **Bug 2 (gefunden beim Lesen der echten Werte, nicht nur der Struktur):**
  `allowanceExpiry: 567432` ist ein **Sekunden-Restwert** (≈6,57 Tage — passt zu einem
  gerade zurückgesetzten 10.000-Punkte/7-Tage-Fenster), **kein** absoluter ISO-Zeitstempel.
  `SourceBudget.record_allowance`s Docstring (`budget.py:81-87`) hat genau diesen Fall
  bereits vorausgesehen: „the caller converts it to an absolute instant before calling this
  method" — aber weder `BudgetedIGBarProvider.get_bars()` (`service.py`, bereits **committed**
  in Step 4, `49902b6`) noch `probe_allowance.py` (diese Session) tun das; beide reichen
  `allowance.get("allowanceExpiry")` unkonvertiert durch.
  **Tragweite:** Bug 1 bedeutet, dass das gesamte D10-Budget-System (Steps 2+4, bereits
  committed) seit seinem Bau **nie echte Allowance-Daten empfangen hat** — nur gegen Fakes
  getestet, die dieselbe falsche Top-Level-Annahme teilen (`test_service.py`s `_FakeBroker`
  baut `data={"allowance": ...}` direkt auf Envelope-Ebene, das bleibt nach dem Fix korrekt,
  da der Envelope-Vertrag `data["allowance"]` sich nicht ändert — nur `ig_adapter.py`s
  Befüllung dieses Feldes). **Kein Schaden am D18-Gate:** `SourceBudget`/
  `_check_restart_gate` filtern beide auf `remaining IS NOT NULL` — die leere Beobachtung
  wurde korrekt ignoriert, nie als `remaining=0` fehlinterpretiert; das Gate blieb sicher
  verweigert (fail-closed), konnte aber strukturell nie grün werden, bis jetzt.
  **Nikinger-Entscheidung (2026-08-17):** beide Bugs fixen, **aber nicht in dieser Session**
  (Context knapp) — Bug 1 ist ein Cross-Phase-Edit (Phase 1, bereits ✅ live-verifiziert)
  und fällt unter die Wochenend-Regel, aber der Nikinger hat es für **sofort im
  nächsten Zug freigegeben** ("wofür warten wir sonst, der Bot kann eh nicht laufen") —
  keine weitere Rückfrage nötig, direkt umsetzen.

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
- **Step 6 committed** (Commit `65ebec7`, `phase12: measurement heartbeat + divergence sampler (Step 6)`); `git status` clean.

### Open questions / blockers

- Keine technischen (Advisor-Review dieser Session: 4 Step-4-Nachprüfungen + 1
  Step-5-Fund + 2 Step-6-Funde, alle sauber/gefixt).
- Zwei bewusst offene, dokumentierte Lücken (s. Next): die G-Deckungslücke bei einem
  POST_WINDOW-losen Tag, und der In-Memory-Sampler-Throttle über Neustarts hinweg.
- Operator-Landmine (leere `measurable_universe()`) bleibt die einzige Konsequenz, die vor
  dem nächsten Bot-Neustart aktiv gemanagt werden muss — jetzt mit drei betroffenen
  Konsumenten, aber ohne automatischen Alarm dafür (bewusst, s. Korrektur oben).

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
