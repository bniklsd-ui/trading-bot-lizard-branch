---
status: live
purpose: ACTIVE phase head — V3: Abstain-/No-Trade-Lessons echt auf main + Persistenz-Reform (Regime-Snapshots, Decision-Context) + Paper-Trades; Block A ✅ (Montag-Restart-Beweis 2026-07-14) + Block B ✅ (market_context + Paper-Pipeline live auf main 2026-07-17); Council-Paper-Call (§10.3) ✅ gebaut, aus (enable_paper_debate=False) 2026-07-17; Bug A (pnl_resolver) + Bug B (abort_detail) beide gefixt 2026-07-17
read-when: working in phase10_v3/ — read this head + its newest Session-stopped block first
detail: L2
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase10_v3_plan.md   # full execution-ready plan (L3, ausführungsreif)
  - ../docs/concepts/PHASE10_V3_KICKOFF_HANDOVER.md   # kickoff handover from M1 into V3 (L3)
  - ../meta_m1_harness/specs/S1.md   # ... S7.md — Abstain-Lessons Bauplan-Specs (L3, zweifach real durchgebaut)
  - ./WEEK1_REVIEW_2026-07-17.md   # Step-8 catch-up review (L3, dated)
  - ./SESSIONS_ARCHIVE.md   # full session history (L3)
updated: 2026-07-17
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

## Session stopped — 2026-07-17 (WE 2 follow-up: Bug A + Bug B fixed, Council-Paper-Call built)

> Same-day follow-up to the Block-B session above (now rotated to `SESSIONS_ARCHIVE.md`).
> Nikinger's special task: "this session is only actually solving these bugs + papertrade
> council logic." All three delivered. Advisor consulted twice (once before implementation —
> caught a real timezone defect in the planned Bug-A fix before it shipped; the Council-
> Paper-Call reuse-shape question was also resolved there, since the plan's own `[VERIFY aus
> §5.5]` pointer turned out to reference a section that doesn't exist in the plan doc).

### Completed

**Bug A — FIXED** (`phase7_reward/reward/pnl_resolver.py`, cross-phase, dated 🔁-note in
`phase7_reward/CLAUDE.md`): `resolve()` branch 3 now rejects any `get_trade_history`
candidate whose `close_date` predates the trade's own `open_ts` (new `_parse_instant`
helper — tz-aware, compares in UTC, conservative/no-reject on parse failure).
**Advisor-caught defect avoided:** a naive string compare across `open_ts` (local offset,
e.g. `+02:00`) and IG's `close_date` (UTC) would have rejected legitimate same-day matches
too. `_OpenCtx` (`recorder.py`'s cold-reconcile path) gained `open_ts`. +4 tests, **P7 133 →
137**, including a golden replay of the row-6 incident and a dedicated tz-correctness case.
**Not done:** correcting the already-persisted bad row (`id=6`) — needs a live
`get_trade_history` read (deal `DIAAAAXZEYXT8BC` should be settled by now) + a manual DB
`UPDATE`, both left to the Nikinger (network + live-DB write are operator actions per
project convention).

**Bug B — root cause confirmed correct, visibility gap closed, root reason unrecoverable**
(`phase5_execution/execution/executor.py`, dated 🔁-note in `phase5_execution/CLAUDE.md`):
the 2026-07-15 AEX order was a genuine broker `REJECTED` → `ExecutionAbort` — correct
fail-closed behavior, not a gate/VETO/order-path bug. But `_abort()`'s `_notify_context`
call hardcoded `veto_results_json={"vetos": "pass"}`, dropping the actual `detail` (IG's
reject reason) — so even with last session's ABORT-visibility fix, a future rejection would
still need stderr access to know why. Fixed: `detail` now folds into
`{"vetos": "pass", "abort_detail": detail}` (no schema change). **The original 2026-07-15
reason itself is confirmed unrecoverably lost** — checked `logs/` (only covers 2026-07-16+,
daemon restarted since) and `journalctl` (nothing bot-related for that window). **Flagged
to the Nikinger, unconfirmed:** the rejected instrument was AEX, not DAX — the fixed
`stop_distance_points`/`limit_distance_points` (30/45) apply to every epic, and the existing
v1.5-hotfix note already flags non-DAX `point_values` as provisional; the same DAX-
calibration risk plausibly extends to stop/limit distances tripping an IG minimum-distance
rule on the ~1000-level AEX index. Unconfirmed — watch for it on the next rejection, now
self-diagnosing from the DB.

**Council-Paper-Call (§10.3) — built, off by default** (`enable_paper_debate` stays `False`,
matches the plan's Drop-Order + the Nikinger's build-then-flip pattern for every other V3
flag):
- `phase6_debate/debate/prompts.py` (dated 🔁-note in `phase6_debate/CLAUDE.md`): additive
  sibling to the live Judge — `build_paper_pick_prompt(digest)` + `_paper_pick_schema()` +
  `_PAPER_PICK_SYSTEM` (forced BUY/SELL, no ABSTAIN branch, one-sentence rationale). Zero
  diff to `build_judge_prompt`/the live Bull/Bear/Judge orchestrator. **P6 70 → 76** (+6).
- `phase10_v3/abstain_lessons/paper.py`: `PaperDebateCaller` (`request_pick(digest) ->
  tuple[str,int]|None`, injected `llm` + `prompt_builder` — no `debate` import, phase
  isolation preserved by construction, verified again by `test_separation_guarantees.py`).
  `PaperEngine` gained `council_daily_cap` (default 3) and `_maybe_council_pick`: after the
  shadow pair, checks `store.count_today(COUNCIL_PICK, ...)` against the cap, calls
  `debate_caller.request_pick({"epic","bid","ask"})` (same quote already fetched for the
  shadow pair — no second IG call), inserts a `COUNCIL_PICK` `PaperTrade` with
  `council_confidence` set on a valid pick. Digest is deliberately thin (epic + one quote)
  — `PaperEngine.on_debate_abstain` only ever receives a sparse `cycle_outcome`
  (confirmed: `AbstainRecord.detail`/`.context_json` are never actually populated by
  `classify_abstain` today — a separate, pre-existing gap, out of this session's scope, not
  touched). **P10 113 → 125** (+12: `PaperDebateCaller` validation + `PaperEngine`
  integration).
- `phase8_scheduler/scripts/wiring.py`: `_build_paper_engine` now builds a
  `PaperDebateCaller` when `config.enable_paper_debate` (lazy import, mirrors the existing
  `enable_abstain_reflect` LLM-construction pattern exactly — same `get_credential`/
  `LLMClient`/`ResearchConfig`). Model = `DebateConfig().model_judge` (Sonnet, matching the
  real Judge — deliberately not the cheap Haiku reflect model; the cap keeps cost trivial
  regardless). `py_compile` clean; not pytest-collected (scripts convention).

### Verifiziert
- Volle Cross-Phase-Regression: P1 87 · P2 75 · P3 100 · P4 155 · P5 **167** (unverändert —
  Bug-B-Fix erweiterte einen Bestandstest statt einen neuen anzulegen) · P6 **76** (+6) ·
  P7 **137** (+4) · P8 221 (unverändert) · P9 72 · P10 **125** (+12) · meta_m1_harness 28 ·
  root 77.
- Kein Live-/Netz-/Smoke-Test diese Session (kein neuer Broker-/Order-Pfad berührt) —
  Live-Verifikation (inkl. `enable_paper_debate`-Flip, wenn gewünscht) bleibt Operator-Aufgabe.

### Next
- **Operator (Nikinger):**
  1. Row-`id=6`-Korrektur (Bug A): optional, network + live-DB write, s. o. — nur falls die
     historische Zeile es wert ist, korrigiert zu werden.
  2. AEX-Stop-Distanz-Hypothese (Bug B): unbestätigt, beobachten bei der nächsten
     ABORT-Zeile (jetzt self-diagnosing via `decision_context.veto_results_json`).
  3. `enable_paper_debate=True` flippen, wann gewünscht — Council-Paper-Call ist gebaut +
     getestet, aber bewusst noch nicht live.
  4. Montag-Restart-Beweis Runde 2 (aus der Vorsession, weiterhin offen): erste echte
     `market_regime_snapshots`/`decision_context`/`paper_trades`-Zeilen protokollieren.
- **Reflect-Pfad-Watch-Item** (aus dem Week-1-Review, weiterhin offen): warum
  `lesson_extracted=0` bei allen realen `REASON_DEBATE_ABSTAIN`-Records — unverändert aus der
  Vorsession, nicht Teil dieser Session's Scope.

### Open questions / blockers
- Keine technischen. Volle Regression grün, keine VETO-/Gate-/Order-Pfad-Änderung diese
  Session (Bug-B-Fix ist rein additiv an einer bereits Nikinger-autorisierten Beobachtungs-
  Naht, kein neuer Order-Pfad-Touch).

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
