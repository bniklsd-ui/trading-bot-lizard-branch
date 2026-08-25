---
status: live
purpose: PHASE-HEAD, Phase 10 (V3) ✅ **abgeschlossen (Closeout 2026-08-25)** und live auf `main`. Council-Paper-Call ✅ gebaut, **default `False`, bis auf weiteres in mind Phase 15** (Nikinger 2026-08-25). **Phase 11 ist seit 2026-08-11 🛑 DEFERRED (Notbremse)** — B1/B2/B4/B5 + H1 + H4-a gebaut, aber WI-2/W2 nach drei Datenwochen unbeantwortet; alle drei Wochen scheiterten an Infrastruktur, nie an der Messung. Gemeinsame Wurzel = das **Datenfundament** (eine Tatsache in drei divergenten Speichern → Fallback deckt 1 von 4 aktiven Epics; dazu: die Mehrquellen-Kette aus Phase 9 Step 6 lief nie, `enable_ig_bars` default `False`). Nichts zurückgerollt. **Einstieg für jede Folge-Session an Phase 10: PHASE10_CLOSEOUT_HANDOVER.md (2026-08-25).** Einstieg für Phase-11-Wiederaufnahme: PHASE11_DEFERRAL_HANDOVER.md.
read-when: working in phase10_v3/ — ZUERST PHASE10_CLOSEOUT_HANDOVER.md, dann dieser Kopf + newest Session-stopped block; für Phase-11-Wiederaufnahme zusätzlich PHASE11_DEFERRAL_HANDOVER.md; vor jedem Scheduler-Neustart zusätzlich ALLOWANCE_INCIDENT_2026-08-08.md
detail: L2
up: ../CLAUDE.md
down:
  - ./PHASE10_CLOSEOUT_HANDOVER.md   # ✅ Closeout-Handover (2026-08-25) — Status, Bilanz, Delta, offene Entscheidungen, Konsistenz-Regeln, Datei-Anker (L3, dated) — ZUERST LESEN
  - ../docs/concepts/phase10_v3_plan.md   # full execution-ready plan (L3, ausführungsreif)
  - ../docs/concepts/PHASE10_V3_KICKOFF_HANDOVER.md   # kickoff handover from M1 into V3 (L3)
  - ../meta_m1_harness/specs/S1.md   # ... S7.md — Abstain-Lessons Bauplan-Specs (L3, zweifach real durchgebaut)
  - ./WEEK1_REVIEW_2026-07-17.md   # Step-8 catch-up review (L3, dated)
  - ./TRADE_DATA_DIAGNOSIS_2026-07-19.md   # pre-V4 Strukturdiagnose W1-W6 + Watch-Items (L3, dated)
  - ./DATA_WEEK_REVIEW_2026-07-25.md   # WI-1..WI-6 Auswertung + 2 Bugfixes + N1/N2 (L3, dated)
  - ./DATA_WEEK_REVIEW_2026-07-31.md   # Datenwoche 2: W1/W5 bestätigt, 3 neue Bugs, Phase-11-Hypothesen H1-H7 (L3, dated)
  - ./DATA_WEEK_REVIEW_2026-08-07.md   # Datenwoche 3 (erste H1-Live-Woche): IG-/prices-Ausfall + Universe-Quarantäne-Kaskade (L3, dated) — §3 Root Cause SUPERSEDED, s. nächste Zeile
  - ./ALLOWANCE_INCIDENT_2026-08-08.md   # korrigiert obige §3.1/§3.2: kein IG-Ausfall, sondern erschöpftes Konto-Kontingent; + Fix + Restart-Gate (L3, dated)
  - ./H4_LESSON_FEEDBACK_SCOPE_2026-08-08.md   # H4-Scoping gegen As-Built: 4 Trades → 4 Lessons → 5.973 Renderings, relevance_score tot (L3, dated)
  - ./PHASE11_DEFERRAL_HANDOVER.md   # 🛑 Notbremse 2026-08-11 — Status, Anforderungen A-G, offene Entscheidungen (L3, dated) — Phase-11-Wiederaufnahme-Handoff
  - ../docs/architecture/data_foundation.svg   # Fehlerbild + Zielbild, 1080x1080 (P11-Deferral-Bild)
  - ../docs/architecture/phase10_v3.svg   # Phase-10-Bild (1080×1080, Closeout) — Block-A/B + Council→P15 + Bilanz
  - ./DATA_SOURCE_STRATEGY_2026-08-11.md   # Entscheidung: Tracker auf ChainedBarProvider (IG→yFinance), NICHT Lightstreamer; IG-Kontingent bestätigt 10.000/Woche (L3, dated)
  - ../ROADMAP.md   # Phase 11 (deferred) + Phase 12 (Datenfundament) + Phase 13 (Live-Datenfundament) + Phase 14 (Discovery) + Phase 15 (V4) sections
  - ./SESSIONS_ARCHIVE.md   # full session history (L3)
updated: 2026-08-25
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
   live). **Council-Paper-Call ✅ gebaut** (Folge-Session, selber Tag) — **default `False`,
   bis auf weiteres in mind Phase 15** (Nikinger 2026-08-25). Die P10-Implementation bleibt
   als Eingangs-Schnittstelle-Vorschlag im Code; P15 subsumiert sie.

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

## Modul-Tree (Block A ✅ WE 1 2026-07-11; Block B ✅ WE 2 2026-07-17; Bug A/B + Council-Paper-Call ✅ Folge-Session 2026-07-17; Closeout 2026-08-25)

```
phase10_v3/
├── CLAUDE.md                                  ← dieser Kopf (✅ Closeout 2026-08-25)
├── PHASE10_CLOSEOUT_HANDOVER.md               ← ✅ 2026-08-25 — Phase-10-Abschluss + Council→P15
├── SESSIONS_ARCHIVE.md                        ← rotierte Session-Blöcke (L3)
├── STEP0_DATA_ANALYSIS_2026-07-10.md          ← Step 2 Output (dated)
├── WEEK1_REVIEW_2026-07-17.md                 ← Step-8-Nachzügler Review (dated)
├── TRADE_DATA_DIAGNOSIS_2026-07-19.md         ← pre-V4 Strukturdiagnose W1–W6 (dated)
├── DATA_WEEK_REVIEW_2026-07-25.md            ← WI-1..WI-6 + 2 Bugfixes + N1/N2 (dated)
├── DATA_WEEK_REVIEW_2026-07-31.md            ← W2: 3 neue Bugs, Phase-11-H1..H7 (dated)
├── DATA_WEEK_REVIEW_2026-08-07.md            ← W3: Allowance-Incident (SUPERSEDED §3; s. u.)
├── ALLOWANCE_INCIDENT_2026-08-08.md          ← §3-Korrektur + Fix + Restart-Gate (dated)
├── H4_LESSON_FEEDBACK_SCOPE_2026-08-08.md    ← H4-Scoping: relevance_score tot (dated)
├── PHASE11_DEFERRAL_HANDOVER.md               ← 🛑 Notbremse 2026-08-11, P11-Wiederaufnahme
├── DATA_SOURCE_STRATEGY_2026-08-11.md         ← ChainedBarProvider statt Lightstreamer (dated)
├── pyproject.toml · requirements.txt          ← ✅ eine Distribution, zwei Pakete
│                                                (abstain_lessons* + market_context*), editable
├── abstain_lessons/                            ✅ models.py, exceptions.py, classifier.py,
│                                                reflect.py, sink.py, store.py,
│                                                paper.py (WE 1 Modelle + WE 2 Engine:
│                                                open_shadow_pair/resolve_paper_trade/
│                                                PaperEngine/PaperTradeTracker + §10.3
│                                                PaperDebateCaller, Folge-Session — Council
│                                                default OFF, deferred → P15), paper_store.py
├── market_context/                             ✅ (WE 2) models.py, exceptions.py, regime.py
│                                                (quote_only-Degrade), writer.py
│                                                (MarketContextWriter + ContextRecorder)
├── scripts/                                    ✅ abstain_report.py (+ WE-2 `--paper`-Sektion)
└── tests/                                      ✅ **165** Tests (frisch gemessen 2026-08-25;
                                                 Stand der Head-Doku 147 war stale — Korrektur
                                                 147 → 165 ist Teil des Closeout-Commits.
                                                 Zusammensetzung: 125 bis WE 2/Council
                                                 + B4/H6 + H1 + 5 Tracker-Guards
                                                 + 4 Lesson-Salvage 08-08
                                                 + 14 nachgelagerte Bugfix-Targets
                                                 = 165 grün)
```

**Bugfix-Block (zusammengefasst für die Audit-Kette):**
- 2026-07-25 — zwei stille 100%-Failure-Bugs: `wiring.py:616` `MINUTE_1` → `MINUTE` (422
  Tracker-Failures über 5 Tage 0/15 resolved); `_AbstainLLMAdapter._SCHEMA`
  `additionalProperties: False` (sonst kein Structured-Output — 0 Lessons seit 2026-07-15)
- 2026-07-31 — **B1 point_value-Drift** (40×-Oversizing für AEX; erklärt 3 historische
  Rejects 07-15/20/30): `wiring.py` `point_values` aus `_build_universe_from_db()` statt
  statischem `research.EXTENDED_UNIVERSE`; `compute_size` now fail-closed bei unmapptem Epic
- 2026-08-08 — Allowance-Incident-Fix (Stale-Expiry + Budget-Breaker + Fetch-Cap),
  B5 Lesson-Salvage (Satzgrenzen-Trim, keine Verwerfung), H4-a Alters-Cap

**Phase-15-Erbschaften (Council/Handover/Reward-Reform/Force-Trigger/Instinct-ECC):**
die P10-Paper-Council-Implementation (Phase 14 wurde nie gebraucht) bleibt im Code als
ein **Eingangs-Schnittstelle-Vorschlag** für P15. Vor jedem Council-Touch im
Phase-14-Konsumentenpfad: `enable_paper_debate` bleibt default `False`, Nikinger
genehmigt jeden Flip explizit.

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

## Session stopped — 2026-08-25 (Mo — Phase-10-Closeout, Council→P15, Σ 1698)

> **BLUF:** Phase 10 ist **✅ abgeschlossen** (Closeout 2026-08-25). Council-Paper-Call ist
> **bis auf weiteres in mind Phase 15 verschoben** (Nikinger 2026-08-25). Vollständiger
> Handover — **das erste Dokument jeder Folge-Session an Phase 10**:
> [`PHASE10_CLOSEOUT_HANDOVER.md`](./PHASE10_CLOSEOUT_HANDOVER.md). Read-only-Analyse,
> kein Produktionscode-Edit; eine eigenständige, dokumentationsdominierte Atom-Einheit.

### Completed

- **As-Built-Inventur** (Read-only): jede Zahl selbst nachgemessen — Phase-10-Tests
  **165 grün**, Σ-Sweep **1698 grün / 0 fails**, **`main` = `origin/main` = `03a0919`**,
  25 `phase10_v3:`-Commits auf `origin/main`, 0 unpushed lokal. Keine Zahl aus
  Vordokumenten übernommen, was sich selbst prüfen ließ.
- **`PHASE10_CLOSEOUT_HANDOVER.md`** geschrieben (L3-Snapshot) — 5-Zeilen-Bilanz
  (fertig / getestet / live-validiert / gepusht / nicht-erreicht), Architektur-Bild
  in einer Zeile, §3 Delta seit `PHASE11_DEFERRAL_HANDOVER.md`, §4 vier offene
  Entscheidungen mit Optionen + Empfehlungen + Konsequenzen, §5 Datei-Anker,
  §6 fünf Konsistenz-Regeln (nicht antasten ohne Not), §7 fünf Don't-Anweisungen.
  Nach Handover-Vertrag: keine Implementierungsdetails wiederholt, Code bleibt
  Wahrheit.
- **`docs/architecture/phase10_v3.svg`** (1080×1080) — fünf-Panel-Layout: Block A
  (Abstain-Lessons, NO_TRADE-Pfade 1-7) + Block B (Persistenz-Reform +
  Paper-Pipeline, market_context + paper_trades) + Council-Paper-Call (default
  `False`, **→ Phase 15** als gestrichelter Parked-Pfad mit klarer
  Eingangs-Schnittstellen-Definition) + Status-Bilanz (was geleistet, was offen,
  Phase-11-Inhalte explizit ausgenommen) + Bugfix-Block + Konsistenz-Regeln.
  Style-konsistent mit `data_foundation.svg` / `phase13_live_data.svg` /
  `phase12_5_failure.svg`.
- **Status pflegepropagiert in diesem einen Commit**: Root-`CLAUDE.md`
  (Phase-10-Row: `🔄 aktiv` → `✅ abgeschlossen` + Closeout-Link +
  Council→P15-Markierung + Test-Zahl 165 + Commit-Count 25 + Synchron-Hinweis
  auf `origin/main`); `ROADMAP.md` (Phase-10-Header gleicher Status-Flip +
  Closeout-Verweis + `📕 Closeout 2026-08-25`-Absatz); `docs/INDEX.md`
  (`Active phases`-Header → ohne P10 + neuer `Closed phases`-Header mit P10;
  zwei neue INDEX-Zeilen — Closeout-Handover-Linie + SVG-Linie; phase10_v3-
  Linienreflex: Council→P15, Closeout-Link); Phasenkopf selbst (`up`/`down`/
  `purpose`/`updated` YAML, Mission-B-Block, Modul-Tree um SVG + Closeout-
  Handover + Bugfix-Block erweitert).
- **Drei Drift-Korrekturen an Doku** (Code = source of truth):
  1. **Modul-Tabelle `tests/` 147 → 165 Tests** (Head war stale; reale
     Zusammensetzung: 125 bis WE 2/Council + B4/H6 + H1 + 5 Tracker-Guards
     + 4 Lesson-Salvage 08-08 + 14 nachgelagerte Bugfix-Targets = 165).
     Korrektur im selben Commit, gegen den `pytest phase10_v3/tests -q`.
  2. **Council-Call-Status**: „✅ gebaut, default OFF, Nikinger flippt
     wann gewünscht" → „✅ gebaut, default `False`, **bis auf weiteres in
     mind Phase 15**". Header, Mission-Block-B, Modul-Tree und
     Phase-15-Erbschaften-Block alle gleichlautend.
  3. **Header `## Session stopped — 2026-08-11` (Notbremse)** bleibt
     **unverändert in der Geschichte** — siehe SESSIONS_ARCHIVE.md, rotiert
     verbatim (Auditkette).
- **Keine Cross-Phase-Produktionscode-Edits** in dieser Session. Phase-10-
  Closeout ist eine **eigenständige dokumentationsdominierte Atom-Einheit**
  (so wie `PHASE11_DEFERRAL_HANDOVER.md` 2026-08-11 auch docs-only war).
  Bot läuft unverändert weiter (vier Daemons alive), die drei Patch-Hygiene-
  Änderungen aus Phase-14-Session-10 vom Vortag (PATH-Prepend in 5
  Start-Wrappern + Phase-8-C3-Test-Hermetization + restart-services.sh
  Helper) sind seit gestern live auf `origin/main`.

### Findings (eines, ehrlich)

- 🟡 **Pre-existing Test-Failures im Nachbar-Repo:** 4 Phase-14
  `test_webui.py`-Tests (`test_discovery_unarmed_*`) bleiben in Phase-14-
  Statistik rot — bereits im Phase-14-Session-10-Hygiene-Block (Nikinger-
  Antwort auf den „was ist das Problem bei Phase 8"-Ping) durch Commit
  `0a55818` gelöst → Phase-8-Sweep wieder **248 grün**. **In dieser
  Phase-10-Closeout-Session NICHT weiter angetastet** — gehört zu Phase 8,
  nicht Phase 10. Sweep-Stand für Phase 10 selbst = **165 grün, 0 fails**.

### Unverändert offen

- **Phase 11 (V3-Fortsetzung)** bleibt 🛑 DEFERRED — drei Datenwochen
  unbeantwortet, gehören in den Datenfundament-Track (Phase 12/13/14). Die
  Übergabe-Anforderungen **A–G** im [`PHASE11_DEFERRAL_HANDOVER.md`](./PHASE11_DEFERRAL_HANDOVER.md)
  bleiben der Einstieg für jede Wiederaufnahme; die Phase-10-Closeout ändert daran
  nichts.
- **WI-2/W2 / H3 / H5 / H7 / B3 / M2 / S6 / Block C (UI)** — alles in den
  Phase-11-/Phase-12-/Phase-13-/Phase-15-Tracks dokumentiert. Nicht in
  Phase-10-Scope, auch nicht durch den Closeout erledigt.
- **Bug B5 + H4-a Wirkung** — H4-a wird beim nächsten echten Scheduler-
  Restart (Phase-13-Beweiswoche läuft seit Mo 2026-08-25) erstmals live zu
  beobachten sein; Lessons-Alter-Cap rollt erst ab **2026-08-20**, also kann
  der Effekt erst danach im Lauf sichtbar werden.

### Next

- **Operator (Nikinger):** **Push-Freigabe** für den Phase-10-Closeout-Commit.
  Diff ist dokumentationsdominiert: ein .md-File neu (`PHASE10_CLOSEOUT_HANDOVER.md`)
  + ein .svg-File neu (`docs/architecture/phase10_v3.svg`) + Phasenkopf-Updates +
  Root-CLAUDE.md-Row + ROADMAP-Sektion + INDEX.md-Einträge. **Sweep** Σ 1698 grün,
  kein Bot-Touch, kein Cross-Phase-Produktionscode-Edit.
- **Phase 10 ist abgeschlossen und wird nicht wieder aktiv**. Jeder Touch am
  Produktionscode (`abstain_lessons/`, `market_context/`, `scripts/abstain_report.py`,
  Cross-Phase-Nähte in P5/P8/P9) braucht eine **neue Cross-Phase-Freigabe** des
  Nikinger — die Phase-14-Freigabe-Liste deckt Phase 10 nicht ab.
- **Phase 15 Plan-Session (V4)** — bleibt long-horizon, gegatet auf Outcomes aus
  Phase 9+11+12+13+14. Die Council-Eingangs-Schnittstelle aus Phase 10 ist im
  Closeout §6.3 dokumentiert; P15-Plan-Session entscheidet, ob das als
  Startpunkt übernommen oder durch eine eigene V4-Implementation ersetzt wird.
- **Phase 11 Wiederaufnahme** — strukturell blockiert auf Datenfundament-Track
  (Phase 12/13/14). Beweiswoche läuft seit Mo 2026-08-25, **nicht** vor deren
  Abschluss WI-2/W2 beantwortbar.

---


> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
