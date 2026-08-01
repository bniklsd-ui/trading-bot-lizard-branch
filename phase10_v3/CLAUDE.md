---
status: live
purpose: ACTIVE phase head — covers Phase 10 (V3: Abstain-/No-Trade-Lessons + Persistenz-Reform + Paper-Trades, alles live auf main) UND Phase 11 (V3-Fortsetzung: Funnel-/Mess-Fixes aus der Datenwoche-2-Review, claimed 2026-08-01 — ROADMAP's alte "Phase 11 = V4" ist jetzt Phase 12). Zwei Datenwochen gefahren (07-20/24 + 07-27/31), Woche 2 zeigte Funnel-Kollaps (366 Zyklen → 1 Kandidat → 0 Trades). Fünf Befunde B1-B5: B1/B2/B5/B4(H6) gefixt (07-31/08-01); B3 (Margin-Headroom) design-dokumentiert, bewusst auf eine eigene größere Session verschoben. H1 (zeitgesteuerte Shadow-Pairs) ist gebaut + verdrahtet (2026-08-01, default AUS — enable_shadow_schedule), wartet auf einen Nikinger-Live-Lauf; H3/H4/H5/H7 offen, gegatet auf H1s echte Daten.
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
  - ../ROADMAP.md   # Phase 11 (this work) + Phase 12 (V4, renumbered 2026-08-01) sections
  - ./SESSIONS_ARCHIVE.md   # full session history (L3)
updated: 2026-08-01
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

## Session stopped — 2026-08-01 (H1 built: time-scheduled shadow pairs, default OFF)

> Building session on the same working thread as the earlier 2026-08-01 (Phase 11 claim +
> B4/H6 + B3-deferred) session — that block rotated verbatim to `SESSIONS_ARCHIVE.md`. Per the
> Nikinger's confirmed ordering, H1 (time-scheduled shadow pairs) was the next content step: it
> decouples paper-trade measurement from the collapsed research funnel entirely and answers W2,
> the root open question everything else is gated on. Planned in Claude-Code plan mode first
> (anchors verified against live code before writing any line), approved, then built atomically.

### Completed
- **`PaperEngine.open_scheduled_pairs(epics, deadline=None)`** (`phase10_v3/abstain_lessons/
  paper.py`) — a new, lean entry point alongside the existing event-triggered
  `on_debate_abstain`: one shared `now` per tick, opens a Both-Sides-Shadow pair per epic via
  the existing (unmodified) `open_shadow_pair`, each epic isolated in its own try/except
  (mirrors `PaperTradeTracker.tick`'s per-epic isolation) so one epic's quote-fetch failure
  never blocks the rest. Synthetic `abstain_record_id = f"sched:{uuid4()}"` (schema-verified:
  the column has no FK) — the `sched:` prefix keeps these trivially distinguishable from
  debate-triggered pairs (bare UUIDs) in later analysis, per the review's own recommendation.
  Deliberately **no** Council-Paper-Call from this path — that call is conceptually tied to an
  actual debate-abstain, not a bare timer tick. +6 tests in `phase10_v3/tests/test_paper_engine.py`.
- **`deadline` guard, added after an Advisor pass caught a real correctness gap in the first
  cut:** `PaperTradeTracker` only ticks during the WINDOW phase, so a pair opened late enough
  that `now + max_hold_minutes` lands after `window_close` would sit unresolved overnight; worse,
  `resolve_paper_trade` checks SL/TP touch on **every** bar with no cut-off at `time_stop_utc`,
  so a next-morning gap bar can register as a "touch" hours after the intended hold ended — a
  fabricated fill, not a real one. Fixed by skipping the **whole tick** (same `now`/
  `max_hold_minutes` for every epic, so either all would overrun the deadline or none would)
  when the prospective time-stop would exceed a passed-in `deadline`. `wiring.py`'s
  `shadow_pair_scheduler()` computes that deadline as today's `config.window_close` in the
  daemon's tz and passes it through — `resolve_paper_trade` itself is **untouched** (it's shared
  with the debate-triggered path; a behaviour change there is its own decision, not folded in
  here). +3 more tests in `test_paper_engine.py` (skips whole tick past deadline / proceeds
  within it / `deadline=None` stays unrestricted).
- **Scheduler wiring** — the exact structural precedent as the Phase-9 `universe_refresher`
  (injected closure + fail-soft fire-and-forget wrapper + throttled caller via the shared
  `_due_after` helper), with one deliberate difference: **no preflight firing** (a timer tick
  needs no daemon-start warm-up, unlike a universe refresh):
  - `phase8_scheduler/scheduler/config.py`: `enable_shadow_schedule: bool = False`,
    `shadow_schedule_interval_min: int = 30`. **Corrected sizing (post deadline-guard, do not
    use the review's ~130-136 figure):** with `window_close=17:30` and `max_hold_minutes=240`,
    the last productive tick is 13:30, so at the 8-epic active universe this is **10 ticks ×
    8 epics ≈ 80 pairs/day**, not 130 — the guard trades some volume for a same-day-clean
    sample. Still answers WI-2 in ~1-2 sessions instead of two dead weeks. Two tuning levers if
    more volume is wanted: shrink `shadow_schedule_interval_min` (20 min → ~14 productive ticks
    ≈ 112 pairs/day) or shorten the scheduled pairs' own hold (would need a separate
    `max_hold_minutes` for this path — not built, `open_scheduled_pairs` reuses the shared
    `ExecutionConfig.max_hold_minutes` today). No new CLI flag on the interval (mirrors
    `universe_refresh_interval_min`/`reflect_daily_cap` — config-only default).
  - `phase8_scheduler/scheduler/state.py`: `last_shadow_pairs_ts: str | None = None` — cross-day,
    kept across `rollover_if_new_day` (same category as `last_universe_refresh_ts`).
  - `phase8_scheduler/scheduler/runner.py`: `shadow_pair_scheduler` ctor param,
    `_run_shadow_pair_scheduler()` (fail-soft) + `_maybe_run_shadow_pairs()` (throttled), called
    from the WINDOW phase right after `_maybe_refresh_universe` — independent of the auto-confirm
    gate, since paper trades never touch real trade caps.
  - `phase8_scheduler/scripts/wiring.py`: a `shadow_pair_scheduler()` closure inside
    `build_scheduler()`, gated on `enable_paper_trades AND enable_shadow_schedule` both true,
    queries `UniverseStore.active_universe()` (identical pattern the `universe_refresher` closure
    already uses) for the active epic list, computes today's `window_close` deadline, and calls
    `paper_engine.open_scheduled_pairs(epics, deadline=deadline)`. No dedicated test file for
    `wiring.py` (documented "operator-run, not pytest-collected" convention) — verified via
    `py_compile`.
  - **`phase8_scheduler/scheduler/run.py`: `--enable-shadow-schedule` CLI flag** (mirrors
    `--enable-ig-bars`/`--enable-paper-debate` exactly — `store_true`, threaded into
    `config_from_args`). Caught by the same Advisor pass: without this, `enable_shadow_schedule`
    had no path to `True` via the documented `python -m scheduler.run` entry at all.
  - +9 tests in `phase8_scheduler/tests/test_runner.py` (none/runs-once/throttled/re-fires-after-
    interval/not-in-non-WINDOW-phases/fail-soft, mirroring the `universe_refresher` test block),
    +2 default assertions in `test_config.py`, +2 field roundtrip assertions in `test_state.py`,
    +1 CLI-flag-threads-through test in `test_run.py`.
- **Ships default OFF** (`enable_shadow_schedule=False`) — bit-identical to today's behaviour
  until the Nikinger consciously arms it (mirrors `enable_paper_debate`'s discipline), given the
  real IG-allowance cost. No live/network run this session (repo convention: live runs are the
  Nikinger's job) — that's the natural next step once armed.
- Full cross-phase regression before AND after all edits, everything green: **P1 87 · P2 75 ·
  P3 100 · P4 155 · P5 173 · P6 76 · P7 138 · P8 229 (was 222, +7) · P9 72 · P10 138 (was 132,
  +6) · meta_m1_harness 28 · root 77.**
- Earlier 2026-08-01 session-block (Phase-11-claim + B4/H6 + B3-deferred) verbatim nach
  `SESSIONS_ARCHIVE.md` rotiert.

### Next
- **Operator (Nikinger):** flip `--enable-shadow-schedule` on a live demo run once ready (paper
  trades already default on), and watch the IG-allowance budget — the interval is the tuning
  knob if it's too hot. This is what actually answers W2 (do the paper pairs' SL/TP/time-stop
  resolution rates look like the review's W2 hypothesis predicts). **Open verification item for
  that live run:** confirm whether IG's `get_ohlcv(epic, "MINUTE", 300)` returns only
  trading-hours bars or includes out-of-hours — this determines how much slack the deadline
  guard actually needs; not verifiable from the repo, only from a live call.
- **B3 (its own session, whenever the Nikinger picks it up):** start with the live `/markets/
  {epic}` inspection — see `phase5_execution/CLAUDE.md`'s B3 block for the exact plan.
- **`resolve_paper_trade`'s no-cutoff-at-`time_stop_utc` behaviour** (flagged, not fixed — see
  the deadline-guard note above): if a future session wants belt-and-braces protection on the
  debate-triggered path too (not just H1's scheduled pairs), that means changing shared Block-B
  code — a decision for the Nikinger, not a silent fold-in.
- **H3/H4/H5/H7** remain fully open, data-gated on H1's live results per the review's own
  ordering — read the resolved scheduled pairs before touching any of them.
- Scheduler daemon still not started — unchanged, an operator decision outside this session.

### Open questions / blockers
- **W2 (Sub-Noise geometry) still unanswered** — the whole point of shipping H1 is to answer it;
  needs a live run with the flag armed, not more code.
- None new from this session's own work (all edits additive, full regression green) beyond the
  two items above, both already actioned (deadline guard + CLI flag) or explicitly deferred.

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
