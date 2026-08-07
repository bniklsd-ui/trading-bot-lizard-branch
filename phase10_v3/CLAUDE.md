---
status: live
purpose: ACTIVE phase head — covers Phase 10 (V3: Abstain-/No-Trade-Lessons + Persistenz-Reform + Paper-Trades, alles live auf main) UND Phase 11 (V3-Fortsetzung: Funnel-/Mess-Fixes aus der Datenwoche-2-Review, claimed 2026-08-01 — ROADMAP's alte "Phase 11 = V4" ist jetzt Phase 12). Fünf Befunde B1-B5: B1/B2/B5/B4(H6) gefixt (07-31/08-01); B3 (Margin-Headroom) design-dokumentiert, eigene Session. H1 (zeitgesteuerte Shadow-Pairs) gebaut + verdrahtet (08-01), erste Live-Woche gefahren (08-03/07) — Funnel weiterhin kollabiert, WI-2/W2 weiterhin unbeantwortet; der Lauf deckte einen IG-`/prices`-Ausfall auf, der 18/22 `instrument_universe`-Epics in Quarantäne schickte. **Nächste Session (Wochenende) startet mit: `/prices`-Health-Check → Universe-Reset-Entscheidung → Tracker-Backoff-Fix, bevor H1 wieder scharf geschaltet wird** — volles Playbook im newest Session-Block. Empfehlung dieser Session: H4 (Lesson-Feedback-Loop) muss nicht mehr auf eine saubere H1-Woche warten (Nikinger-Bestätigung offen).
read-when: working in phase10_v3/ — read this head + its newest Session-stopped block first
detail: L2
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase10_v3_plan.md   # full execution-ready plan (L3, ausführungsreif)
  - ../docs/concepts/PHASE10_V3_KICKOFF_HANDOVER.md   # kickoff handover from M1 into V3 (L3)
  - ../meta_m1_harness/specs/S1.md   # ... S7.md — Abstain-Lessons Bauplan-Specs (L3, zweifach real durchgebaut)
  - ./WEEK1_REVIEW_2026-07-17.md   # Step-8 catch-up review (L3, dated)
  - ./TRADE_DATA_DIAGNOSIS_2026-07-19.md   # pre-V4 Strukturdiagnose W1-W6 + Watch-Items (L3, dated)
  - ./DATA_WEEK_REVIEW_2026-07-25.md   # WI-1..WI-6 Auswertung + 2 Bugfixes + N1/N2 (L3, dated)
  - ./DATA_WEEK_REVIEW_2026-07-31.md   # Datenwoche 2: W1/W5 bestätigt, 3 neue Bugs, Phase-11-Hypothesen H1-H7 (L3, dated)
  - ./DATA_WEEK_REVIEW_2026-08-07.md   # Datenwoche 3 (erste H1-Live-Woche): IG-/prices-Ausfall + Universe-Quarantäne-Kaskade (L3, dated)
  - ../ROADMAP.md   # Phase 11 (this work) + Phase 12 (V4, renumbered 2026-08-01) sections
  - ./SESSIONS_ARCHIVE.md   # full session history (L3)
updated: 2026-08-07
---
# CLAUDE.md — Phase 10 (V3): Abstain-Lessons + Persistenz-Reform + Paper-Trades (`phase10_v3/`)

> Der Bot wird lernfähig aus seinen eigenen Abstains — mit den Daten, die da sind. Kein
> Research-Layer-Umbau, kein Broker-Wrapper-Umbau (spätere Phase). **Quelle der Wahrheit ist
> der Code, nicht dieses Dokument.** Vollständiger Plan: `../docs/concepts/phase10_v3_plan.md`.
> Kickoff-Kontext: `../docs/concepts/PHASE10_V3_KICKOFF_HANDOVER.md`.

## Mission (zuerst lesen)

Drei Blöcke, sequenziert (§1 des Plans):
1. **Step 0 (docs-only, Fr 2026-07-10):** ✅ Phasen-Skeleton + Housekeeping + Datenanalyse +
   Contract-Verifikation.
2. **Block A (Bot-berührend, Wochenende 1, Sa 2026-07-11):** ✅ Abstain-/No-Trade-Lessons echt —
   Migration 005, `AbstainStore`, Classifier, `reflect_abstain`, Sink-Naht am P5-Executor,
   Wiring im P8-Runner. S6 (Prompt-Rückspeisung) bewusst dunkel (default OFF).
3. **Block B (Bot-berührend, Wochenende 2, Sa 2026-07-17):** ✅ Persistenz-Reform
   (`market_regime_snapshots` + `decision_context`, observe-only `regime_tag`, degradiert
   immer auf `quote_only` — kein VETO-Code-Touch) + Paper-Trades (Both-Sides-Shadow-Tracking
   live). **Council-Paper-Call ✅ gebaut** (Folge-Session, selber Tag) — hinter Flag
   `enable_paper_debate` (default `False`), Nikinger flippt wann gewünscht.

Block C (UI) ist **nicht Teil dieses Plans** — geparkt, siehe Plan §13.

## Bauprinzip (Projekt-Kernprinzip, unverändert)

„So wenig AI wie möglich, so viel AI wie nötig." Genau **zwei** AI-Nähte in dieser Phase, beide
best-effort, beide triggern nie eine Order: `reflect_abstain` (Haiku, Tages-Cap) und der
optionale Council-Paper-Call (Flag default AUS, Cap 3/Tag, Output nur in `paper_trades`).
Klassifizierung, Persistenz, Paper-Auflösung, Regime-Features = deterministischer Code. VETOs/
Gates unantastbar, keine AI-Order-Triggerung — siehe Root-`CLAUDE.md` Hard Rules.

## Scope

- **DRIN:** `abstain_lessons/` (Store, Classifier, `reflect_abstain`, Sink, Paper-Modul,
  Report-Script), `market_context/` (Regime-Features, Writer, Decision-Context), Migration
  `005_v3_learning.sql`, additive Nähte an P5-Executor (`abstain_sink`, `context_recorder`) und
  P8-Runner (Config-Keys, Wiring, Tracker-Tick), S6-Flag am P4-Prompt-Builder (default OFF).
- **NICHT DRIN:** Research-Layer-Umbau, Broker-Wrapper-Umbau, `lesson_embeddings`,
  Regime-*Nutzung* (Floor/Directions-Modulation), UI (Block C), S6-Aktivierung (eigener
  Operator-Schritt nach Lesson-Review), M2 (geparkt, kein V3-Blocker).

## Modul-Tree (Block A ✅ WE 1 2026-07-11; Block B ✅ WE 2 2026-07-17; Bug A/B + Council-Paper-Call ✅ Folge-Session 2026-07-17)

```
phase10_v3/
├── CLAUDE.md                                  ← dieser Kopf
├── SESSIONS_ARCHIVE.md                        ← rotierte Session-Blöcke (L3)
├── STEP0_DATA_ANALYSIS_2026-07-10.md          ← Step 2 Output (dated)
├── WEEK1_REVIEW_2026-07-17.md                 ← Step-8-Nachzügler Review (dated)
├── pyproject.toml · requirements.txt          ← ✅ eine Distribution, zwei Pakete
│                                                (abstain_lessons* + market_context*), editable
├── abstain_lessons/                            ✅ models.py, exceptions.py, classifier.py,
│                                                reflect.py, sink.py, store.py,
│                                                paper.py (WE 1 Modelle + WE 2 Engine:
│                                                open_shadow_pair/resolve_paper_trade/
│                                                PaperEngine/PaperTradeTracker + §10.3
│                                                PaperDebateCaller, Folge-Session), paper_store.py
├── market_context/                             ✅ (WE 2) models.py, exceptions.py, regime.py
│                                                (quote_only-Degrade), writer.py
│                                                (MarketContextWriter + ContextRecorder)
├── scripts/                                    ✅ abstain_report.py (+ WE-2 `--paper`-Sektion)
└── tests/                                      ✅ 125 Tests (67 WE 1 + 46 WE 2 + 12 Bug-Fixes/Council)
```

## Arbeitsteilung (nicht verhandelbar)

Bot-berührende Steps **nur am Wochenende** (Markt zu, Bot steht). **Wochentags nur
docs-only/read-only** — read-only auf `data/` (SQLite via `mode=ro`-URI), keine Migration, kein
Scheduler-Restart, keine `live_test.py`. Details + volle Decision-Tabelle (V3-D1…D10):
`../docs/concepts/phase10_v3_plan.md` §0.

## Step 1 — Housekeeping (2026-07-10, Fr)

**Legacy-Grep (Ritual):** `grep -rn -i "turbo\|CALL/PUT\|pre_trade_option_check\|expected hold" --include="*.py" --include="*.md"`
→ **sauber.** Einziger aktiver Treffer ist der bekannte `turbo_candidates.json` (P5-Gate-2-
Contract, "legacy name, do not rename"-annotiert an mehreren Stellen). Alle übrigen Treffer für
`CALL/PUT`/`pre_trade_option_check`/`strike`/`otm` sind Doku-Zeilen, die die historische
Bereinigung *bestätigen* ("kein `option_check`/`CALL`/`PUT` in Phase 5" — negative Assertion,
kein Rest). `expected hold` hat null echte Treffer — nur als Zitat des Grep-Rituals selbst in
anderen Plan-Docs. Nichts zu bereinigen.

**Regression-Baseline (2026-07-10):** volle Suite je Phase separat (`pytest <phase>/tests -v`,
projektübliche Trennung wegen `tests.conftest`-Namenskollision), geteilter Venv
`phase1_broker_wrapper/.venv`. **1162 passed, 0 failed:**

| Phase | Count | vs. Plan-Erwartung |
|---|---|---|
| P1 | 87 | = |
| P2 | 76 | = |
| P3 | 100 | = |
| P4 | **148** | Plan erwartete 141 — **+7, Korrektur** (plausibel: spätere Hotfix-Arbeit an P4-Validator/Prompt nach Plan-Erstellung) |
| P5 | 154 | = |
| P6 | 70 | = |
| P7 | 133 | = |
| P8 | 217 | = |
| P9 | 72 | = |
| meta_m1_harness | 28 | (nicht im Plan-Baseline-Table, informativ) |
| root `tests/` | 77 | = |

**.md↔Code-Verify:** Root-`CLAUDE.md` zeigte M1 korrekt CLOSED, aber Phase 10 noch als
"Geplant, gegatet auf Phase 9" statt aktiv — **gefixt** (Tabellen-Zeile aktualisiert, keine neue
Prosa laut Doku-Hygiene-Regel). `ROADMAP.md`s Phase-10-Statuszeile behauptete noch "keine
Konzept-Session" trotz vorliegendem `phase10_v3_plan.md` — **gefixt** (verweist jetzt auf Plan +
Kickoff-Handover). Meta-Strang-Sektion in `ROADMAP.md` war bereits korrekt (M1 CLOSED). `data/`
während der gesamten Housekeeping-Session unberührt (nur `mode=ro`-Reads für Step 2/3).

## Verified anchors (2026-07-10)

Contract-Verifikation der Specs S1–S7 + Block-B-Anker gegen As-Built (Plan §5). Diese
Liste ist ab WE 1 die bindende Anker-Liste — Ersatz für die `[VERIFY]`-Marker im
Web-Chat-Plan, wo unten aufgelöst.

**1. P5-Executor** (`phase5_execution/execution/executor.py`):
- Alle NO_TRADE-Rückgabepfade: Gate 1 (:167-168), Gate 2 (:174-175), Debatte-Fehler
  fail-closed (:186-191), Debatte-ABSTAIN (:192-195), Gate 3 (:202-204), Gate 5
  (:205-207), Gate-4-Sizing (:213-218), VETO (:220-223). Helper `_no_trade` (:130-136).
  **Separat, kein NO_TRADE:** Session-Health/Reconcile-Fail-Closed (:159-160) und
  Order-Platzierung/Reconcile-Fehler (:238-262) geben `ABORT` zurück, nicht `NO_TRADE` —
  der Plan verdrahtet `abstain_sink` nur an NO_TRADE-Pfaden; ABORT-Zyklen bleiben
  bewusst außerhalb (bestätigt real relevant: 11 Session-Health-Aborts in der
  Step-2-Analyse, s. o.).
- `reward_sink`: keyword-only Konstruktor-Param, `Any | None = None` (:80, :106-113,
  :124); Protocol in `phase5_execution/execution/protocols.py:101-119`
  (`on_trade_opened`/`on_trade_closed`). Aufruf best-effort, try/except →
  `logger.critical`, wirft nie (:283-291, :302-305). **`abstain_sink=None` sollte
  exakt dasselbe Muster spiegeln.**
- `debate_runner`: keyword-only Konstruktor-Param, `Callable[[dict], Any] | None = None`
  (:79, :97-104), duck-typed (kein `Protocol`), gelesen als `.decision`/`.direction`/
  `.rationale` (:192,194,196). Reale Shape: `DebateOutcome`
  (`phase6_debate/debate/models.py:249-277`) — `decision: str`, `direction: str | None`,
  `confidence: float`, `rationale: str`, `rounds_used: int`. **Kein Bull/Bear-Summary-Feld
  auf `DebateOutcome` selbst** — siehe Punkt 5.
- Objekte im Scope je NO_TRADE-Punkt: `candidate` ab Gate 2 vorhanden, `price_env` erst
  ab Gate 4 (fehlt bei Gates 1/2/Debatte/3/5 — reale Lücke, in Step-2(c) dokumentiert).
  `cycle_outcome`-Assembly braucht **keine neue Plumbing** für das, was S2 fordert — nur
  lokale lose Objekte in ein Dict verpacken.

**2. P8-Wiring** (`phase8_scheduler/scripts/wiring.py`, `scheduler/runner.py`,
`scheduler/config.py`, `scheduler/observability.py`):
- Executor-Bau + Seam-Injektion: `build_scheduler()`, `_make_debate_runner`
  (wiring.py:224-265), `_build_reward_sink` (wiring.py:268-291), injiziert in
  `Executor(...)` (wiring.py:394-405).
- Config-Key-Muster: `SchedulerConfig` (`scheduler/config.py:42-157`), ein Feld pro
  Tunable mit Default (z. B. `enable_ig_bars: bool = False`, :150).
- Tracker-Tick-Naht: WINDOW-Phase-Branch `_run_phase()` (runner.py:342-366), nach
  `record_cycle`. Muster wie bestehender `universe_refresher` (optionaler Callable,
  Default `None`, runner.py:211, :447-475) — `_due_after()`-Helper (:430-445)
  wiederverwendbar für Throttling.
- Observability: generischer `record_event(path, event: dict)` (observability.py:99-115)
  — **das** ist der richtige Aufruf für `abstain_recorded`/`context_recorded`/
  `paper_*`-Events, nicht der feste `record_cycle`-Schema-Call. Bereits so genutzt in
  wiring.py:154-159. Log-Pfad: `SchedulerConfig.observability_path` (:157).

**3. P2-Migrationen** (`phase2_persistence/`):
- Migrationsverzeichnis `phase2_persistence/migrations/`, Konvention `NNN_description.sql`
  (`persistence/migrations.py:19`). Vorhanden: 001–004. **Nächste Nummer bestätigt: 005.**
- Runner: `run_migrations()` (migrations.py:72-83), Version-Tracking über
  `_schema_version`-Tabelle, `conn.executescript` je Migration in eigener Transaktion
  (:54-69) — additiv/idempotent by convention.
- `db.py`-„Whitelist" ist eine **Spalten-Whitelist pro Tabelle** (`_TRADE_COLUMNS` etc.,
  db.py:26-53), **keine** Connection-/Tabellen-Zugriffssperre — bestätigt, dass eigene
  `sqlite3.connect(...)`-Stores (wie geplant für `AbstainStore`/`PaperTradeStore`) nichts
  umgehen müssen, weil es keine solche Sperre gibt.
- `UniverseStore` (`phase9_universe/universe/store.py:1-13,42-45`) bestätigt exakt als
  Präzedenzfall: eigene `sqlite3.connect`, kein Import von `persistence.Database`, läuft
  Migrationen nie selbst.
- **⚠ Real gefundene Abweichung von der Plan-Annahme:** `market_regime_snapshots` und
  `decision_context` existieren bereits (`001_initial.sql:110-154`), aber **`trade_id`-FK-
  scoped** (Kind-Tabelle von `trade_outcomes`, `trade_id INTEGER NOT NULL REFERENCES
  trade_outcomes(id)`), nicht UUID-/`epic`-scoped wie V3 braucht (V3 muss auch NO_TRADE-
  Zyklen abdecken, die keine `trade_outcomes`-Zeile haben). Geschrieben heute nur über
  `Database.insert_regime_snapshot`/`insert_decision_context` (db.py:398-413) — **aktuell
  in keinem Produktionspfad aufgerufen**, nur in `tests/test_db.py` +
  `scripts/archive_verification_trades.py` referenziert, und (neu bestätigt, Step 2) mit
  **0 Zeilen** in der Live-DB. Additive `ALTER TABLE` ist strukturell nicht möglich
  (FK-Constraint kann nicht nachträglich entfernt werden). **Empfehlung für Step 4 (WE 1,
  nicht heute):** DROP+CREATE in Migration 005 mit Begründung im Migrations-Kommentar —
  die 2 Referenzen sind Test-/Script-Code, keine Live-Trading-Daten, kein
  Datenverlust-Risiko. Bindet die Nikinger-Entscheidung an den tatsächlichen
  Migrations-Commit (WE 1), nicht an dieses Dokument.

**4. P6-Debatte** (`phase6_debate/debate/models.py`, `debate.py`, `prompts.py`):
- `DebateOutcome` (models.py:248-279): `decision`, `direction`, `confidence`,
  `rationale`, `rounds_used`, **plus `transcript: tuple[AgentTurn, ...]`** — Bull/Bear-Text
  liegt vollständig vor (`AgentTurn` = `{round, agent, model, text, usage}`,
  models.py:223-240), nicht nur die finale Entscheidung. `decision_context.bull_summary`/
  `bear_summary` müssen aus `transcript` extrahiert werden (kein Direkt-Feld).
- Paper-Modus ist **mehr Aufwand als "Flag umlegen"**: Judge-Schema hardcodet
  `decision.enum=["TRADE","ABSTAIN"]` in `prompts.py:178-205` — ein Forced-Pick-Modus
  braucht einen eigenen Prompt/Schema-Builder + entweder eine `Debate`-Subclass oder ein
  additives Sibling-Modul, keinen Konstruktor-Flag. Niedriges Risiko fürs Gesamtprojekt:
  Plan-§14-Drop-Order stuft den Council-Paper-Call ohnehin zuerst weg, falls Zeit knapp
  wird.

**5. P4-Prompt-Builder** (`phase4_research/research/prompt.py`,
`research/context_builder.py`): Lessons-Block existiert bereits
(`_render_lessons`, prompt.py:135-142, immer gerendert, aktuell **nicht flag-gated** —
leere Liste rendert "none on record"). Speisequelle: `db.get_recent_lessons_for_prompt`
(context_builder.py:262-267). **Korrektur zur Plan-Prosa:** dieses Muster lebt in Phase 4
(Lesen) + Phase 2 (DB), nicht in Phase 7 — Phase 7s `brain.reflect()` schreibt Lessons
nur, rendert nichts.

**6. P7-Reflect-Muster** (`phase7_reward/reward/brain.py:187-249`): `Brain.reflect()`
nutzt einen duck-typed `_LLMClientLike`-Protocol (:63-77, `.ask_candidate(...)`), ganzer
Body in try/except (:213-249), gibt bei Fehler ein **typisiertes** `LessonResult(ok=False,
error=...)` zurück, keinen blanken `None`. **Nuance für Step 5:** S4-Spec will
`reflect_abstain(...) -> str | None` — der P7-Precedent nutzt ein typisiertes Result statt
bare-`None`; beide sind valide, S4 bleibt bei `str | None` (Spec-Text), nur vermerkt.

**7. P1 `get_ohlcv`** (`ig_adapter.py:423-441`, Basisklasse
`broker_wrapper/adapters/base.py:43-46`): `get_ohlcv(epic, resolution, count) -> Envelope`,
`resolution` muss in `VALID_RESOLUTIONS` sein, `count` in `(0, 1000]`. Der
403/Allowance-Vorfall vom 2026-07-06 ist **inline in `_request` dokumentiert**
(ig_adapter.py:330-360), nicht in den Lightstreamer-Notes wie der Plan vermutete — IG
signalisiert Allowance-Erschöpfung als HTTP 403 mit `exceeded-*-allowance`-Body, jetzt
korrekt auf denselben 429-Backoff-Pfad geroutet statt fälschlich `AuthenticationError`.

**8. Sizing/Time-Stop** (`phase5_execution/execution/sizing.py:86`,
`execution/config.py:102,127-128`): `compute_size(account_env, price_env,
market_info_env, risk_pct, config, *, epic=None)` liest `stop_distance_points`/
`limit_distance_points` aus `ExecutionConfig` (deterministisch, kein Live-Vol-Signal).
Time-Stop-Dauer-Key: `max_hold_minutes` (Default 240), konsumiert in `monitor.py:91`.

**9. Test-Baseline-Korrektur:** siehe Step-1-Abschnitt oben (1162 grün, P4 141→148).

## Session stopped — 2026-08-07 (Fr — erste H1-Live-Woche ausgewertet, read-only)

> Read-only Datenwoche-Review, angestoßen durch den Nikinger ("week is over now. wanna have a
> look? the bots paused, everything should be safe"). Kein Code berührt, keine Migration, kein
> Scheduler-Neustart — nur `mode=ro`-DB-Reads + Log-Lesen, exakt wie die beiden Vorwochen-
> Reviews. Vollständige Auswertung: `phase10_v3/DATA_WEEK_REVIEW_2026-08-07.md`.

### Completed
- Verifiziert: Scheduler lief die ganze Woche durchgehend (ein Start 2026-08-01 12:18 lokal,
  kein Neustart, kein Crash), sauberer Stop kurz vor dieser Session (kein `KILL`-File, letzter
  Reconcile 23:13 lokal). **Kein Order-Risiko** — 0 echte Trades, `trade_outcomes` unverändert
  seit 07-20.
- **Funnel weiterhin vollständig kollabiert:** 360 `abstain_records`, 100 % `REASON_NO_CANDIDATES`,
  5/5 Tage — unverändert gegenüber den beiden Vorwochen, nichts Neues.
- **H1 produzierte wie geplant** (600 Shadow-Pairs geöffnet, 0 `open_scheduled_pairs failed`)
  — aber deckte dabei einen **IG-`/prices`-Endpoint-Ausfall** auf, der ab 08-04 einsetzte und
  bis zum letzten Verify-Versuch heute (08-07 15:14 lokal) anhält. Erst als Chat-Erstauswertung
  falsch gelesen (52 SL / 43 TP als "Trefferquote"), dann per Advisor-Pass korrigiert: die
  SL/TP-Verteilung eines Both-Sides-Paars ist mechanisch gekoppelt, keine Edge-Aussage — s.
  Review §2 für die korrigierte Lesart.
- **Root Cause identifiziert:** nicht der 30-Minuten-`shadow_schedule_interval_min` (öffnet nur
  neue Paare), sondern die vorbestehende **5-Minuten-`_run_paper_tracker()`-Kadenz** (Block B,
  seit 07-17, vor H1 mit fast nichts zu tun) — ein wachsender Rückstand fälliger `OPEN`-Trades
  erzeugt monoton eskalierende `get_ohlcv`-Fehlversuche (218→516→786→1148→1564 CRITICAL-
  Zeilen/Tag, Σ 4232). **Korrektur der eigenen Empfehlung aus der letzten Session:** dort stand
  "der Intervall-Regler ist die Stellschraube, falls die Allowance zu heiß läuft" — falsch für
  dieses Ausfallmuster, der Intervall-Regler wirkt auf einen anderen Mechanismus.
  `instrument_universe.checks_json` liefert einen sauberen endpoint-spezifischen Beleg
  (`get_market_info`-Checks grün, `ig_ohlcv_available: false`, gleiche Verify-Runde).
- **Kaskaden-Schaden gefunden:** dieselbe `check_ig_side`-Probe läuft unabhängig von H1 auch in
  der Phase-9-Promotion-Pipeline — 18 von 22 `instrument_universe`-Epics sind jetzt
  `quarantined`, **inklusive des seit Wochen live-verifizierten Kerns** (DAX/CAC/IBEX/AEX/STXE,
  `point_value_source='ig_fields'`). Die verbleibenden 4 aktiven Epics stehen bei
  `fail_count=2` gegen `demote_after_fails=3` — eine Verify-Runde vom vollständigen Leerlauf
  entfernt. Das ist der wichtigste Befund der Woche, nicht die Shadow-Pair-Zahlen selbst.
- **WI-2/W2 bleibt unbeantwortet** — 0 `TIME_STOP` unter den 95 resolved Pairs ist ein Artefakt
  des Ausfalls (keine Bars bis `time_stop_utc`), keine Antwort auf die Geometrie-Frage.
- Zwei Nebenbefunde protokolliert, nicht gefixt: B5-Restfehlerrate (10/68 Reflect-Versuche
  überschreiten weiterhin die 300-Zeichen-Grenze trotz des 07-31-Fixes), `env.error` wird in
  `wiring.py::_build_paper_tracker`s `bar_fetch` verschluckt — die gesamte Diagnose dieser
  Woche lief über `instrument_universe.checks_json`, nicht über die 4232 CRITICAL-Zeilen selbst,
  die den echten IG-Fehlercode nirgends trugen.
- `phase10_v3/DATA_WEEK_REVIEW_2026-08-07.md` geschrieben + in `docs/INDEX.md` registriert.
  Vorheriger Session-Block (2026-08-01, H1 built) verbatim nach `SESSIONS_ARCHIVE.md` rotiert.

### Nachtrag (gleiche Session, Chat-Follow-up) — Strategie-Priorisierung für die
### Wochenend-Session morgen

Der Nikinger fragte nach einer Gesamteinordnung über alle drei Datenwochen + diesen Vorfall
hinweg. Ein Advisor-Pass vor der Antwort korrigierte drei Punkte an der Erstfassung — die
Korrekturen sind unten bereits eingearbeitet, nicht separat vermerkt:

1. **Das Universum ist eingefroren, nicht am Verfallen.** Die Promotion-Pipeline läuft nur,
   wenn der Daemon läuft — solange der Bot pausiert ist, tickt keine Uhr gegen die 4
   verbleibenden aktiven Epics. Das Risiko ist **nicht** „jeder Tag, der vergeht", sondern **der
   nächste Daemon-Start mit einem noch toten Endpoint**. Das nimmt den falschen Zeitdruck fürs
   Wochenende raus — der Health-Check vor dem Neustart ist der eigentliche Gate, keine Uhr.
2. **Der Tracker-Fix braucht eine benannte Eigenschaft, keine bloße Form.** „Kadenz
   entkoppeln/drosseln" beschreibt eine Form, keine Anforderung. Die tatsächlich nötige
   Eigenschaft: **ein wiederholter `get_ohlcv`-Fehler muss künftiges Call-Volumen SENKEN, nicht
   erhöhen.** Heute ist es umgekehrt — ein Fehler lässt den Trade `OPEN`, `OPEN`-Trades
   akkumulieren, der nächste Tick hat mehr Epics zum erneuten Scheitern. Ein reines
   Intervall-Verlängern verlangsamt nur dieselbe Divergenz, kehrt sie nicht um. Der Mechanismus
   (Backoff, Circuit-Breaker, Retry-Cap pro Trade) ist der Wochenend-Session überlassen — aber
   er muss zusätzlich die **bestehenden 328 Rückstands-Zeilen** behandeln, nicht nur neuen
   Rückstand verhindern.
3. **`env.error` nicht verschlucken** bleibt ein kleiner, kostenloser Mitnahme-Fix im selben
   File (`wiring.py::_build_paper_tracker`s `bar_fetch`).
4. **Korrektur der eigenen Zuschreibung:** H1 hat den Ausfall nicht *verursacht* — es hat das
   Call-Volumen erhöht, das eine bereits vorhandene Phase-9-Lücke (`check_ig_side`s
   Demote-bei-IG-Fail-Pfad) freigelegt hat. Dieser Pfad hätte bei jedem sustained
   `/prices`-Ausfall demotiert, unabhängig von H1 (steht bereits so in
   `DATA_WEEK_REVIEW_2026-08-07.md` — hier nur nochmal explizit festgehalten, damit die
   Zuschreibung im Kopf konsistent bleibt).
5. **Die H3/H4/H5/H7-Sequenzierung neu bewertet, mit einer Empfehlung, nicht nur einer Frage:**
   die bisherige Reihenfolge gatete H4 (Lesson-Feedback-Loop) auf eine „saubere H1-Woche". Das
   Gate ist jetzt **dreimal an drei unabhängigen Gründen gescheitert** (Tracker-Bug Woche 1,
   Funnel-Kollaps Woche 2, IG-Ausfall Woche 3) — das ist selbst Evidenz, dass das Gate
   unzuverlässig ist, nicht dass eine saubere Woche kurz bevorsteht. H4s eigene Evidenzbasis
   hängt nicht von WI-2 ab: W5 ist bereits bestätigt, 4.529 Lesson-Renderings, explizites Zitieren
   in jeder bisher eingefangenen Begründung, jetzt drei Wochen in Folge dasselbe Abstain-Muster.
   **Empfehlung: H4 muss nicht auf H1 warten** — Scoping kann parallel zum Infra-Fix laufen,
   braucht keinen laufenden Daemon. Ehrliches Gegenargument aus H7s eigener Logik: nicht an der
   Richtungslogik drehen, bevor die Geometrie bekannt ist. Aber H4 ist keine Richtungslogik —
   es entfernt einen Dämpfer, der die **Sample-Erzeugung selbst** unterdrückt, eine andere
   Kategorie als das, was H7 meinte. Die ursprüngliche Reihenfolge hat das vermutlich vermengt.
   **Das ist eine Empfehlung, keine getroffene Entscheidung** — der Nikinger kann sie morgen
   bestätigen oder überstimmen, ohne dass vorher etwas umgeschrieben werden muss.

### Next (morgige Wochenend-Session startet hier)

1. **Nikinger, vor allem anderen:** ein einzelner `get_ohlcv`-Live-Call gegen z. B.
   `IX.D.DAX.IFMM.IP`, um `/prices` zu bestätigen. Kein Zeitdruck (s. Punkt 1 oben) — aber
   nichts danach ist sicher zu sequenzieren, ohne das zu wissen.
2. **Branch auf das Ergebnis:**
   - Gesund → DB-Reset der 18 quarantined Epics (Präzedenzfall 2026-07-06).
   - Weiterhin tot → **keinen Neustart**, auch nicht ohne `--enable-shadow-schedule` — der
     nächste Punkt (Fix) kommt zuerst so oder so.
3. **Bevor irgendein Neustart mit dem Flag passiert:** der Tracker-Fix nach der oben benannten
   Eigenschaft (Punkt 2 im Nachtrag) + der `env.error`-Mitnahme-Fix, im selben File.
4. **Erst danach H1 wieder scharf schalten** für eine echte Datenwoche.
5. **H4 (Lesson-Feedback-Loop) parallel scopen** — unabhängig von 1–4, kein laufender Daemon
   nötig, s. Empfehlung Punkt 5 oben. Startpunkt: `DATA_WEEK_REVIEW_2026-07-31.md` §5 H4 (die
   drei konkreten Kandidaten: Relevanz-Decay, Doppelzählungs-Ende, Lesson-Skopierung).
6. **B3 (Margin-Headroom) bleibt unverändert parkiert**, unabhängig von alldem — eigene Session,
   startet mit dem live `/markets/{epic}`-Check (`phase5_execution/CLAUDE.md`).
7. **H3/H5/H7** bleiben offen, jetzt nachrangig zu H4 statt gleichrangig gegatet.

### Open questions / blockers
- **Root Cause des IG-`/prices`-Ausfalls selbst** (Wochenkontingent erschöpft vs. etwas
  anderes) — nicht aus dem Repo feststellbar, braucht den Live-Check aus Next #1.
- **W2 (Sub-Noise-Geometrie) weiterhin unbeantwortet** — unverändert der Wurzel-Punkt, jetzt
  zum dritten Mal an einer externen Störung statt am Funnel selbst gescheitert.
- **H4-vor-H1-Empfehlung ist unbestätigt** — s. Nachtrag Punkt 5, wartet auf Nikinger-Go/No-Go.

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
