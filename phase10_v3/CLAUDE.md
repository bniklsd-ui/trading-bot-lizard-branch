---
status: live
purpose: ACTIVE phase head — V3: Abstain-/No-Trade-Lessons echt auf main + Persistenz-Reform (Regime-Snapshots, Decision-Context) + Paper-Trades; Steps 0–3 (docs-only) done, Steps 4–11 gated on weekend windows
read-when: working in phase10_v3/ — read this head + its newest Session-stopped block first
detail: L2
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase10_v3_plan.md   # full execution-ready plan (L3, ausführungsreif)
  - ../docs/concepts/PHASE10_V3_KICKOFF_HANDOVER.md   # kickoff handover from M1 into V3 (L3)
  - ../meta_m1_harness/specs/S1.md   # ... S7.md — Abstain-Lessons Bauplan-Specs (L3, zweifach real durchgebaut)
updated: 2026-07-10
---
# CLAUDE.md — Phase 10 (V3): Abstain-Lessons + Persistenz-Reform + Paper-Trades (`phase10_v3/`)

> Der Bot wird lernfähig aus seinen eigenen Abstains — mit den Daten, die da sind. Kein
> Research-Layer-Umbau, kein Broker-Wrapper-Umbau (spätere Phase). **Quelle der Wahrheit ist
> der Code, nicht dieses Dokument.** Vollständiger Plan: `../docs/concepts/phase10_v3_plan.md`.
> Kickoff-Kontext: `../docs/concepts/PHASE10_V3_KICKOFF_HANDOVER.md`.

## Mission (zuerst lesen)

Drei Blöcke, sequenziert (§1 des Plans):
1. **Step 0 (docs-only, Fr):** Phasen-Skeleton + Housekeeping + Datenanalyse +
   Contract-Verifikation — **dieser Commit-Satz**.
2. **Block A (Bot-berührend, Wochenende 1):** Abstain-/No-Trade-Lessons echt — Migration 005,
   `AbstainStore`, Classifier, `reflect_abstain`, Sink-Naht am P5-Executor, Wiring im P8-Runner.
3. **Block B (Bot-berührend, Wochenende 2):** Persistenz-Reform (`market_regime_snapshots` +
   `decision_context`, observe-only `regime_tag`) + Paper-Trades (Both-Sides-Shadow-Tracking,
   optionaler Council-Paper-Call hinter Flag).

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

## Modul-Tree (geplant — Verzeichnisse entstehen erst mit Block A/B, WE 1/2)

```
phase10_v3/
├── CLAUDE.md                                  ← dieser Kopf
├── STEP0_DATA_ANALYSIS_2026-07-10.md          ← Step 2 Output (dated)
├── abstain_lessons/                            (WE 1) models.py, exceptions.py, classifier.py,
│                                                reflect.py, sink.py, store.py, paper.py,
│                                                paper_store.py
├── market_context/                             (WE 2) models.py, exceptions.py, regime.py,
│                                                writer.py
├── scripts/                                    (WE 1) abstain_report.py
└── tests/                                      (WE 1/2)
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

## Session stopped — 2026-07-10 (Steps 0–3 komplett, docs-only/read-only)

### Completed
- `phase10_v3/CLAUDE.md`: Phasen-Skeleton, Housekeeping-Ergebnisse (Legacy-Grep clean,
  Baseline 1162 grün mit P4-Korrektur 141→148), vollständiger Verified-anchors-Annex
  (9 Punkte, s. o.).
- `docs/INDEX.md`: Phase 10 als aktive Sektion eingetragen, Phase 9 zur "Prior phase"
  umgehängt, alle 4 neuen/verifizierten Docs indiziert.
- Root `CLAUDE.md` + `ROADMAP.md`: Current-state-Tabellenzeile bzw. Phase-10-Statuszeile
  von stale ("Geplant"/"keine Konzept-Session") auf real (🔄 aktiv, Kickoff 2026-07-10)
  korrigiert — Tabellen-Edit only, keine neue Root-Prosa (Doku-Hygiene-Regel).
- `phase10_v3/STEP0_DATA_ANALYSIS_2026-07-10.md`: V2-Baseline (2 reale Trades, beide vor
  07-06, beide Verlust-Stopouts), Abstain-Ist-Analyse (97.6 % Zyklen-Abstain-Quote, davon
  94.3 % Research-Stufe `REASON_NO_CANDIDATES` — Gate-/VETO-/Error-Reasons real **nie**
  aufgetreten in 8 Tagen), Gap-Check (Feld-Mapping S2-Contract + Block-B) inkl. zweier
  echter Lücken: Session-Health-`ABORT`-Zyklen (11×) fallen außerhalb des geplanten
  NO_TRADE-only-Sink-Scopes; `CAC`/`IBEX` laufen 84–97 % der Zeit `degraded` (fehlend
  `volume`) — bestätigt den Bedarf für `data_source`/`degraded` in
  `market_regime_snapshots` konkret statt nur theoretisch.
- 3 Commits: Step 0 (`dce5002`), Step 1 (`76992a0`), Step 2 (`95690b0`); Step 3 (dieser
  Annex + dieser Session-Block) folgt als 4. Commit direkt im Anschluss.
- `data/` während der gesamten Session ausschließlich `mode=ro` gelesen — verifiziert,
  keine Schreibzugriffe.

### Next
- **WE 1 (11.–12.07.):** Migration `005_v3_learning.sql` (Backup-Protokoll zuerst!) +
  `AbstainStore`/`PaperTradeStore` (Plan §6) — dabei die oben dokumentierte
  DROP+CREATE-Empfehlung für `market_regime_snapshots`/`decision_context` final
  entscheiden (Nikinger). Danach S1/S2/S4-Module (Plan §7.1), dann Sink-Naht +
  P8-Wiring + S7-Report + S6-dunkel (Plan §7.2), dann WE1-Regression + Montag-
  Restart-Beweis (Plan §7.3).
- Vor WE 1 starten: kurz `docs/concepts/phase10_v3_plan.md` §6 erneut lesen (Migration-
  Schema-Details), Operator-Checkliste dort beachten (Scheduler-Stop bestätigen, Backup
  vor Migration).
- Woche 2 (wochentags, docs-only): Review-Note nach den ersten realen
  `abstain_records`-Zeilen (Plan §8) — insbesondere prüfen, ob `REASON_DEBATE_ABSTAIN`
  je einen Reflect-Cap-Slot bekommt, gegeben die 94/6-Verteilung aus der heutigen
  Analyse.

### Open questions / blockers
- Keine Blocker für WE 1. Eine Entscheidung liegt an: DROP+CREATE vs. anderer Ansatz für
  die beiden inkompatiblen Placeholder-Tabellen (Empfehlung: DROP+CREATE, s. Anker-Annex
  Punkt 3) — bindend erst am Migrations-Commit, nicht heute.
