---
status: live
purpose: ACTIVE phase head — V3: Abstain-/No-Trade-Lessons echt auf main + Persistenz-Reform (Regime-Snapshots, Decision-Context) + Paper-Trades; Block A (Steps 0–7) done + Montag-Restart-Beweis erbracht 2026-07-14, Block B (Steps 8–11) gated on WE 2
read-when: working in phase10_v3/ — read this head + its newest Session-stopped block first
detail: L2
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase10_v3_plan.md   # full execution-ready plan (L3, ausführungsreif)
  - ../docs/concepts/PHASE10_V3_KICKOFF_HANDOVER.md   # kickoff handover from M1 into V3 (L3)
  - ../meta_m1_harness/specs/S1.md   # ... S7.md — Abstain-Lessons Bauplan-Specs (L3, zweifach real durchgebaut)
  - ./SESSIONS_ARCHIVE.md   # full session history (L3)
updated: 2026-07-14
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

## Modul-Tree (Block A = ✅ gebaut WE 1 2026-07-11; Block B = geplant WE 2)

```
phase10_v3/
├── CLAUDE.md                                  ← dieser Kopf
├── SESSIONS_ARCHIVE.md                        ← rotierte Session-Blöcke (L3)
├── STEP0_DATA_ANALYSIS_2026-07-10.md          ← Step 2 Output (dated)
├── pyproject.toml · requirements.txt          ← ✅ Paket „abstain_lessons", editable install
├── abstain_lessons/                            ✅ (WE 1) models.py, exceptions.py, classifier.py,
│                                                reflect.py, sink.py, store.py, paper.py
│                                                (Modelle only — Engine ist WE 2), paper_store.py
├── market_context/                             (WE 2) models.py, exceptions.py, regime.py,
│                                                writer.py — noch nicht angelegt
├── scripts/                                    ✅ (WE 1) abstain_report.py
└── tests/                                      ✅ (WE 1) 67 Tests — (WE 2 ergänzt Block B)
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

## Session stopped — 2026-07-11 (WE 1: Block A live on main — Migration 005 + abstain_lessons)

> **Nebenbefund am Sessionstart (nicht Teil dieses Plans):** Phase-8-Scheduler-Kill-Switch
> war bis zu ~63h wirkungslos (uncapped POST_WINDOW-Sleep) — diagnostiziert, gefixt
> (Nikinger-Freigabe), Prozess gestoppt (`kill -9`), dokumentiert in
> `phase8_scheduler/CLAUDE.md` → `## Session stopped — 2026-07-11`. Der Scheduler steht seit
> dieser Session (KILL-Datei, `manual:dashboard`); Restart ist ein bewusster Operator-Schritt.

### Completed
- **Migration `005_v3_learning.sql`** (`phase2_persistence/migrations/`): `abstain_records` +
  `paper_trades` (additiv), **DROP+CREATE** von `market_regime_snapshots`/`decision_context`
  (Nikinger-Freigabe via AskUserQuestion — FK-inkompatibel, 0 Zeilen, keine Live-Referenz;
  dokumentierte Ausnahme von Phase 2s "additive only"-Regel, s.
  `phase2_persistence/CLAUDE.md` Don't-Liste). **Backup vor Migration:**
  `data/trading_bot.sqlite.2026-07-11.bak` (gitignored, `*.bak`-Pattern). Live angewandt via
  `phase2_persistence/scripts/init_db.py` → Schema-Version 5, verifiziert (3 Bestands-Trades
  unberührt, alle 4 neuen Tabellen leer + korrektes Schema).
- **Konsequenz-Fixes derselben Migration** (root-cause, nicht nur Symptom): `Database.
  insert_regime_snapshot`/`insert_decision_context` (trade_id-basiert, jetzt schema-inkompatibel)
  entfernt aus `phase2_persistence/persistence/db.py`; `scripts/archive_verification_trades.py`s
  `_CHILD_TABLES` von den beiden Tabellen bereinigt (hätten sonst auf eine nicht mehr existierende
  `trade_id`-Spalte gequeryt); betroffene Tests in `phase2_persistence/tests/test_db.py`,
  `test_migrations.py` (Version 4→5, neuer `test_v3_learning_tables_present`),
  `tests/test_archive_verification_trades.py` aktualisiert.
- **`phase10_v3/abstain_lessons/`** (neues Paket, `pyproject.toml` + editable install, in
  `scripts/dev_install.sh` aufgenommen): `models.py`/`exceptions.py` (S1: `AbstainStage` 5
  Werte, `AbstainReason` 12 Werte, `AbstainRecord` frozen), `classifier.py` (S2:
  `classify_abstain`, Prioritätsordnung exakt wie gespecct), `reflect.py` (S4: `AbstainLLM`
  Protocol, `reflect_abstain` best-effort/nie werfend, `build_paper_lesson_prompt` für WE 2),
  `store.py` (S3: `AbstainStore`, UniverseStore-Own-Connection-Muster), `paper.py` (nur
  Modelle — `PaperTrade`/`PaperVariant`/`PaperStatus`/`PaperExitReason`; die "deterministischer
  Kern"-Engine ist WE 2), `paper_store.py` (`PaperTradeStore`, analog `AbstainStore`),
  `sink.py` (S5: `AbstainLessonSink`, `paper_engine=None` bis WE 2).
- **P5-Executor-Naht** (`phase5_execution/execution/executor.py` + `protocols.py`): neuer
  keyword-only `abstain_sink=None`; `_no_trade` von `@staticmethod` zu Instanzmethode mit
  Cycle-Outcome-Keywords, neuer `_notify_no_trade`-Helper (Muster wie `_notify_opened`,
  Decision J). Alle 8 NO_TRADE-Rückgabepfade übergeben jetzt ihre bekannten Felder
  (Gate-ID-Mapping `time_window→G1, load_candidates→G2(→research_empty statt failed_gate),
  constraints→G3, sizing→G4, direction_consistency→G5`; Veto-IDs matchten bereits 1:1).
  **Default `None` ⇒ bit-identisch bewiesen** (154→154 Bestandstests unverändert grün,
  **+7 neue Naht-Tests → P5 154→161**).
- **P8-Wiring** (`scheduler/config.py`, `scripts/wiring.py`): `enable_abstain_lessons=True`,
  `enable_abstain_reflect=True`, `reflect_daily_cap=10` (V3-D8: **an by default**, anders als
  z. B. `enable_ig_bars` — bewusst, s. Plan). `_build_abstain_sink` (AbstainStore + optionaler
  `_AbstainLLMAdapter` über die wiederverwendete P4-`LLMClient`/Haiku, `RewardConfig.lesson_*`-
  Knobs) + `_observed_abstain_sink`-Wrapper (`abstain_recorded`-Event via
  `observability.record_event`, generischer Call wie im Anker-Annex vorgesehen). In die
  Executor-Konstruktion verdrahtet. **P8 217 Tests unverändert grün** (Config-Defaults
  erweitert, kein neuer Test nötig).
- **S7** `phase10_v3/scripts/abstain_report.py`: deterministisches `--db`-CLI (Counts je
  Reason, letzte N Records, Lesson-Quote), Golden-Output-Test, manuell gegen die echte
  (aktuell leere) Live-DB smoke-verifiziert.
- **S6 dunkel** (`phase4_research/research/prompt.py`): `build_prompt` bekam
  `include_abstain_lessons`/`abstain_lessons`/`include_paper_lessons`/`paper_lessons`
  (alle default aus/`None`) — **pure Funktion bleibt pure** (Lessons werden als
  vorgefertigte String-Listen übergeben, kein eigener DB-Zugriff in `prompt.py`, anders
  als der Plan-Wortlaut "AbstainStore.recent_lessons als Prompt-Block" wörtlich nahelegt —
  bewusste Abweichung, um die dokumentierte "Pure function — no I/O"-Invariante des
  Moduls nicht zu brechen; der Aufrufer holt die Lessons). Default aus ⇒ **P4 148→148
  Bestandstests unverändert grün, +7 neue Flag-Tests → P4 148→155**. **Aktivierung bleibt
  ausdrücklich außerhalb V3** (V3-D3) — niemand im Repo setzt die Flags aktuell `True`.

### Verifiziert
- Volle Cross-Phase-Regression (jede Phase separat, `tests.conftest`-Kollision):
  P1 87 · P2 **75** (−1: 2 alte Regime/Context-Tests entfernt, 1 neuer Migrations-Test) ·
  P3 100 · P4 **155** (+7) · P5 **161** (+7) · P6 70 · P7 133 · P8 217 · P9 72 ·
  **P10 67 (neu)** · meta_m1_harness 28 · root 77. `py_compile` clean auf allen
  berührten Dateien (inkl. `scripts/wiring.py`, laut Konvention nicht pytest-importiert).
- Live-Migration gegen die echte `data/trading_bot.sqlite` angewandt + verifiziert
  (s. o.) — nicht nur gegen `tmp_path`.
- `phase2_persistence/CLAUDE.md` + `phase8_scheduler/CLAUDE.md`(Nebenbefund) dokumentiert
  Doku-Drift-Fixes im selben Commit-Satz (Doku-Hygiene-Regel).

### Next
- **Operator (Nikinger), Montag:** Scheduler-Restart ist ein bewusster Schritt (KILL-Datei
  erst löschen). Montag-Restart-Beweis (Plan §7.3 Akzeptanzkriterium): erste echte
  `abstain_records`-Zeilen + `abstain_recorded`-Events im Health-Log — wortgleich hier
  protokollieren, sobald der Nikinger den Restart macht.
- **Woche 2 (wochentags, docs-only):** Review-Note nach den ersten realen
  `abstain_records`-Zeilen (Plan §8) — insbesondere `REASON_DEBATE_ABSTAIN`-Reflect-Cap-
  Verteilung gegen die 94/6-Analyse aus Step 2 prüfen.
- **WE 2 (18.–19.07.):** Block B — `market_context/` Paket (Modelle, `regime.py`,
  `writer.py`, `context_recorder`-Naht am P5-Executor) + Paper-Pipeline (die
  "deterministischer Kern"-Engine für `paper.py`, `PaperEngine`, Both-Sides-Shadow +
  optionaler Council-Paper-Call). Plan §9–§11.

### Open questions / blockers
- Keine technischen. Eine Beobachtung für die Woche-2-Review: der `_no_trade`-Seam übergibt
  `research_empty=True` für JEDE Gate-2-Fehlschlag (nicht nur `research_empty` im engeren
  Sinn) — das war bereits die S2-Contract-Absicht (G2 → `REASON_NO_CANDIDATES`), aber am
  echten Datenbild (94 % der Abstains sind genau dieser Pfad) lohnt ein Blick, ob die
  12-Reason-Taxonomie an dieser Stelle granular genug bleibt.

### Nachtrag (2026-07-14, Di) — Montag-Restart-Beweis erbracht ✅

Scheduler seit Mo 2026-07-13 durchgehend gelaufen (PID 129102, KILL-Datei vom Nikinger vor
dem Restart gelöscht), `scheduler_state.json` zeigt `consecutive_failures: 0`, `kill_reason:
null` — sauberer, unbeaufsichtigter Lauf. Read-only via `mode=ro`-URI gegen die Live-DB
geprüft (Plan §7.3 Akzeptanzkriterium):

**`abstain_records`** (66 Zeilen, 2026-07-13T07:05:42.541Z … 2026-07-13T14:47:42.545Z, alle
`epic: null`/`stage: research_empty`/`reason: reason_no_candidates`/`lesson_extracted: 0`).
Erste 3 Zeilen wortgleich:
```
{'record_id': 'fc38dd85-a8f3-47a8-a722-8f4d71ac4748', 'created_utc': '2026-07-13T07:05:42.541Z', 'epic': None, 'stage': 'research_empty', 'reason': 'reason_no_candidates', 'lesson_extracted': 0}
{'record_id': 'ae4615b6-a371-4908-96ce-f38cef069aff', 'created_utc': '2026-07-13T07:10:52.196Z', 'epic': None, 'stage': 'research_empty', 'reason': 'reason_no_candidates', 'lesson_extracted': 0}
{'record_id': '7165c61a-a1b1-4fa9-b07e-800536eb881b', 'created_utc': '2026-07-13T07:15:59.476Z', 'epic': None, 'stage': 'research_empty', 'reason': 'reason_no_candidates', 'lesson_extracted': 0}
```

**`research_health.jsonl`** — 66 `abstain_recorded`-Events, 1:1 deckungsgleich mit den
DB-Zeilen (gleiche Reason/Stage/Epic, unabhängiger zweiter Kanal). Letzte 3 wortgleich:
```
{"event": "abstain_recorded", "reason": "reason_no_candidates", "stage": "research_empty", "epic": null, "ts": "2026-07-13T14:37:20.513400+02:00"}
{"event": "abstain_recorded", "reason": "reason_no_candidates", "stage": "research_empty", "epic": null, "ts": "2026-07-13T14:42:31.614240+02:00"}
{"event": "abstain_recorded", "reason": "reason_no_candidates", "stage": "research_empty", "epic": null, "ts": "2026-07-13T14:47:42.546626+02:00"}
```

**Einordnung:** 66/66 sind `REASON_NO_CANDIDATES` (Research-Stufe) — deckt sich exakt mit der
Step-2-Baseline (94.3 % dieses Pfads über 8 Tage). `lesson_extracted` 0/66 ist **erwartetes
Verhalten**, kein Fehler: `reflect_stages` defaultet auf `{AbstainStage.DEBATE}` (V3-D8) —
Research-Stufe-Abstains reflektieren bewusst nie. Noch kein einziger `REASON_DEBATE_ABSTAIN`
in diesem Fenster beobachtet → der Reflect-Pfad selbst ist am echten Live-Lauf noch
unbewiesen (Beobachtungspunkt für die Woche-2-Review, s. o.). **WE-1-Akzeptanzkriterium
(Plan §7.3) damit vollständig erfüllt** — Block A ist nicht nur code-complete, sondern
live am echten unbeaufsichtigten Bot bewiesen.

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
