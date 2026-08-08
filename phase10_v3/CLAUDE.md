---
status: live
purpose: ACTIVE phase head — covers Phase 10 (V3: Abstain-/No-Trade-Lessons + Persistenz-Reform + Paper-Trades, alles live auf main) UND Phase 11 (V3-Fortsetzung: Funnel-/Mess-Fixes aus der Datenwoche-2-Review, claimed 2026-08-01 — ROADMAP's alte "Phase 11 = V4" ist jetzt Phase 12). Fünf Befunde B1-B5: B1/B2/B5/B4(H6) gefixt (07-31/08-01); B3 (Margin-Headroom) design-dokumentiert, eigene Session. H1 (zeitgesteuerte Shadow-Pairs) gebaut (08-01), erste Live-Woche gefahren (08-03/07) — Funnel weiterhin kollabiert, WI-2/W2 unbeantwortet. **Der `/prices`-Live-Check (08-08) korrigierte die Diagnose: kein IG-Ausfall, sondern das erschöpfte Konto-Kontingent für historische Kursdaten, verbraucht vom Paper-Tracker (300 Datenpunkte pro Fetch).** Tracker-Fix (Stale-Expiry + Budget-Breaker + Fetch-Attempt-Cap + `env.error`) gebaut und grün; ebenso der Phase-9-Fix (ein kontoweiter `RATE_LIMIT` demotiert kein Instrument mehr), die B5-Satzgrenzen-Trimmung und **H4-a** (`lesson_max_age_days = 30`). **Universe-Reset und H1-Scharfschaltung bleiben gesperrt, bis ein `remainingAllowance` beobachtet ist** — und H4-as Wirkung ist noch ungemessen.
read-when: working in phase10_v3/ — read this head + its newest Session-stopped block first; vor jedem Scheduler-Neustart zusätzlich ALLOWANCE_INCIDENT_2026-08-08.md
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
  - ./DATA_WEEK_REVIEW_2026-08-07.md   # Datenwoche 3 (erste H1-Live-Woche): IG-/prices-Ausfall + Universe-Quarantäne-Kaskade (L3, dated) — §3 Root Cause SUPERSEDED, s. nächste Zeile
  - ./ALLOWANCE_INCIDENT_2026-08-08.md   # korrigiert obige §3.1/§3.2: kein IG-Ausfall, sondern erschöpftes Konto-Kontingent; + Fix + Restart-Gate (L3, dated)
  - ./H4_LESSON_FEEDBACK_SCOPE_2026-08-08.md   # H4-Scoping gegen As-Built: 4 Trades → 4 Lessons → 5.973 Renderings, relevance_score tot (L3, dated)
  - ../ROADMAP.md   # Phase 11 (this work) + Phase 12 (V4, renumbered 2026-08-01) sections
  - ./SESSIONS_ARCHIVE.md   # full session history (L3)
updated: 2026-08-08
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
└── tests/                                      ✅ 147 Tests (125 bis WE 2/Council, + B4/H6 + H1,
                                                 + 5 Tracker-Guards + 4 Lesson-Salvage 08-08)
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

## Session stopped — 2026-08-08 (Sa — Allowance-Root-Cause + Tracker-Fix; Neustart bleibt gesperrt)

> **BLUF:** Der `/prices`-Health-Check des Nikinger hat die Diagnose der letzten Session
> umgeworfen. **Kein IG-Ausfall — unser eigenes Konto-Kontingent für historische Kursdaten,
> aufgebraucht vom Paper-Tracker.** Der Tracker-Fix ist gebaut und grün; **Universe-Reset und
> H1-Scharfschaltung sind bewusst NICHT erfolgt** — beide hängen an einem beobachteten
> `remainingAllowance`. Volle Forensik: [`ALLOWANCE_INCIDENT_2026-08-08.md`](./ALLOWANCE_INCIDENT_2026-08-08.md).

### Completed

- **Root Cause korrigiert.** Live-Check (Nikinger, 08-08 06:44 UTC) gegen `IX.D.DAX.IFMM.IP`:
  `error.public-api.exceeded-account-historical-data-allowance`. IG rechnet `/prices` in
  **Datenpunkten, nicht Requests** ab — `_PAPER_BAR_COUNT = 300` heißt 300 Punkte **pro
  Fetch**. Aus `paper_trades` rekonstruiert: ≥66 erfolgreiche Fetches ≈ **19.800 Punkte** am
  08-03/08-04, Erschöpfung nach ~einem Tag H1-Vollbetrieb. `DATA_WEEK_REVIEW_2026-08-07.md`
  §3.1/§3.2 hatte Symptom und Mechanismus richtig, die **Ursachenzuschreibung falsch**
  (dated snapshot → nicht editiert, per Konvention superseded).
- **Phase-9-Promotion-Probe als Verursacher ausgeschlossen:** `verify_instrument.py:78-79`
  nutzt `MINUTE_5` × 3 Bars = 3 Punkte/Epic/Runde, 100× billiger als der Tracker. Phase 9 ist
  **Opfer**, nicht Mitverursacher.
- **Zweiter, unabhängiger Befund — eine Datenintegritäts-Falle:** `resolve_paper_trade`
  filtert Bars nur über `timestamp >= created_utc` und prüft den SL-Treffer **bedingungslos
  vor** dem Time-Stop-Ausstieg. Der erste Tick nach einem Neustart hätte einen Teil der **390**
  liegengebliebenen `OPEN`-Zeilen mit **erfundenem** `exit_level`/`pnl_points` als `RESOLVED`
  ins WI-2-Substrat geschrieben — **auch bei gesundem Endpoint, auch ohne
  `--enable-shadow-schedule`** (`_run_paper_tracker` tickt an `enable_paper_trades` allein).
  Das ist der Grund, warum die Branch-Logik der letzten Session („gesund → Reset") nicht
  tragfähig war.
- **Fix gebaut** (2 Dateien, additiv, keine Gate-/VETO-/Order-Pfade):
  - `abstain_lessons/paper.py` — `PaperTradeTracker` bekommt `stale_after_minutes` (Trade
    älter als der Schnitt → `EXPIRED_UNRESOLVED` **ohne Fetch**) und `budget_ok` (**einmal**
    pro Tick geprüft → ein erschöpftes Budget kostet null Calls für den ganzen Tick, nicht
    einen pro Epic; gleiche Callable-Form wie das bestehende `reflect_cap_check`).
    Schnitt ist **Wanduhr**, nicht `bar_count × bar_minutes`, und wird aus
    `exec_cfg.max_hold_minutes + 60` gezogen — eine zweite hartcodierte Kopie dieser Zahl wäre
    die Drift-Klasse von Befund B1.
  - `phase8_scheduler/scripts/wiring.py` — `bar_fetch` trippt bei `RATE_LIMIT` einen
    60-Minuten-Cooldown und unterhalb eines Reserve-Floors (`_PAPER_ALLOWANCE_FLOOR = 2000`,
    **Platzhalter bis ein `totalAllowance` beobachtet ist**, existiert damit die Phase-9-Probe
    weiterläuft); `env.error` wird **nicht mehr verschluckt** (4.232 CRITICAL-Zeilen letzte
    Woche trugen den echten IG-Code nirgends); das `allowance`-Objekt wird einmal pro Prozess
    geloggt (`totalAllowance` = Deckel, `allowanceExpiry` = Reset-Termin — beides kommt gratis
    in jeder erfolgreichen Antwort und wurde bisher weggeworfen).
    `_build_paper_tracker` nimmt dafür `exec_cfg` entgegen (Call-Site mitgezogen).
- **Zur Abnahme-Eigenschaft, ohne Schönfärberei:** die letzte Session forderte „ein
  wiederholter `get_ohlcv`-Fehler muss künftiges Call-Volumen **senken**".
  `stale_after_minutes` **begrenzt** nur (monotones Wachstum → Plateau); erst `budget_ok`
  **senkt** tatsächlich, auf null während des Cooldowns. Zusammen erfüllt.
- **Verifiziert:** `pytest phase10_v3/tests` **141 passed** (138 + 3 neue). `pytest
  phase8_scheduler/tests` **229 passed**. `wiring.py` per `py_compile` (kein pytest-Testfile,
  dokumentierte „operator-run"-Konvention). **Hinweis:** die Zählungen im Modul-Tree oben
  („125 Tests") und in älteren Blöcken („P8 217/222") sind stale — real 141 bzw. 229.
  Gegen die echte DB gerechnet (read-only, Stichtag Mo 08-10 07:05 UTC): **390/390 Rückstands-
  Zeilen fallen unter den Stale-Schnitt → alle expiren beim ersten Tick, 0 Fetches.**
- **H4 gescopet** (Nikinger-Go, docs-only): [`H4_LESSON_FEEDBACK_SCOPE_2026-08-08.md`](./H4_LESSON_FEEDBACK_SCOPE_2026-08-08.md).
  Kernbefund live gemessen: **4 Trades total, alle BUY, alle Verluste** → **4 Lessons** aus
  genau diesen 4 Trades → beide Blöcke (`recent_trades` **und** `Active lessons`) stehen in
  **jedem** Prompt, inzwischen **5.973 Lesson-Renderings**. Und: `relevance_score` existiert
  als Spalte, wird als Konstante 1.0 geschrieben (`reward/recorder.py:394`) und von **keiner**
  Query gelesen — **Kandidat H4-a braucht keine Migration.** Empfehlung: H4-a (Alters-Cap)
  zuerst und allein, H4-b danach entscheiden (wird durch a evtl. gegenstandslos), H4-c erst
  wenn wieder Trades entstehen. Warnung im Doc: ein 30-Tage-Cap entfernt 3 von 4 Lessons, ein
  14-Tage-Cap alle 4 — Verhaltenswechsel für die einzige AI-Entscheidung, Nikinger-Sache.
- **Output-Style** `~/.claude/output-styles/military-brief.md` erstellt (Nikinger-Nebenauftrag,
  außerhalb des Repos, gegen die offizielle Doku verifiziert statt geraten:
  `keep-coding-instructions: true`). BLUF-Format + WHY-Sektion; die Spannung zu ponytail-full
  („drei kurze Zeilen") ist im File **ausgeschrieben** aufgelöst, über ponytails eigene
  Ausnahme für explizit angeforderte Erklärungen. Aktivierung ist ein Nikinger-Schritt
  (`/config` → Output style, wirkt nach `/clear`).

### Nachtrag (gleiche Session) — vier Folge-Fixes gebaut, alle Nikinger-freigegeben

Aus der Liste offener Punkte oben wurden vier abgearbeitet. Alles am Wochenende, Bot steht.

1. **Fetch-Versuche pro Paper-Trade gedeckelt** (`paper.py` + `wiring.py`,
   `_PAPER_MAX_FETCH_ATTEMPTS = 3`). Ein fälliger Trade braucht genau **einen** erfolgreichen
   Fetch — `_resolve_group` terminiert ihn immer, RESOLVED oder EXPIRED. Ein *fehlgeschlagener*
   Fetch ist also der einzige Weg, wie ein Trade einen Tick überlebt. Bisher wurde er jeden
   Zyklus neu geholt, bis `stale_after_minutes` griff: bis zu 60 Versuche bei 5-Minuten-Kadenz.
   Jetzt sind Retries an **fällige Trades** gebunden, nicht an die Ausfalldauer. Zähler
   in-memory (Daemon läuft tagelang; `stale_after_minutes` ist der Backstop über Neustarts —
   eine Spalte wäre eine Migration, um etwas zu begrenzen, das schon begrenzt ist). Wird
   **nicht** belastet, wenn `budget_ok` den Tick abbricht: kein Call, kein Versuch.
2. **Phase-9 `check_ig_side` gefixt** (cross-phase, Nikinger-Go): `verdict` trägt jetzt
   `ig_ohlcv_error_code` — **top-level, bewusst außerhalb von `checks`**, weil sowohl
   `failed_checks` als auch `_ig_side_failed`/`_yf_side_failed` dort nach Boolean-`False`
   scannen. `promotion.py` prüft an **beiden** Call-Sites `_ig_side_indeterminate` vor jedem
   DB-Write: eine unbestimmte Runde schreibt **gar nichts** — nicht den Status, nicht
   `fail_count`, nicht `checks_json`. „Wir haben nichts gelernt" darf nichts ändern, und
   insbesondere `fail_count` **nicht zurücksetzen** (der Spiegelfehler). Verworfen:
   `ig_ohlcv_available: None` — `_ig_side_failed` läse das als Pass, und ein `discovered`
   Kandidat könnte ohne jeden OHLCV-Beweis `VERIFIED` erreichen (Verstoß gegen D6). Eng
   gehalten: ein Epic, dessen Bars aus **eigenem** Grund fehlen, demotet unverändert.
3. **B5-Restfehlerrate geschlossen** (`reflect.py`): zu lange Lessons werden auf den letzten
   **ganzen Satz** unter der Grenze getrimmt statt verworfen. Zwei Qualitätswächter, weil genau
   das die Sorge des Nikinger war: der Schnitt **muss** auf einer Satzgrenze landen (ein
   mitten im Satz gekappter Text kann das Gegenteil des Gemeinten aussagen — „…war nicht
   schlecht" → „…war nicht"), und was übrig bleibt muss substanziell sein (≥150 Zeichen).
   Sonst gilt weiter die alte Ablehnung. Text innerhalb der Grenze kommt **byte-identisch**
   zurück (die 58 von 68 gesunden Fälle sind unberührt, per Test gepinnt).
4. **H4-a gebaut** (`lesson_max_age_days = 30`): rollender Alters-Cap auf die Prompt-Lessons.
   Eigener Knopf, **nicht** `quarantine_before` zweckentfremdet (einmaliger Operator-Reset mit
   festem Datum vs. stehende Policy mit wanderndem). Cutoff wird in **Python** berechnet, nicht
   in SQL: SQLites `datetime('now')` liefert `"YYYY-MM-DD HH:MM:SS"` und vergleicht sich
   **falsch** gegen die `...T...mmmZ`-Timestamps dieses Projekts — eine Falle für stille
   Fehlergebnisse, keine Stilfrage. `None` = altes Verhalten, für ein kontrolliertes A/B.

**Regression, alle Suiten einzeln** (`tests.conftest`-Kollision): P1 87 · P2 **76** · P3 100 ·
P4 155 · P5 173 · P6 76 · P7 138 · P8 229 · P9 **75** · P10 **147** · root **80** = **1336**,
0 failed. `py_compile` clean auf `wiring.py` + `verify_instrument.py`.

**Was H4-a ausdrücklich nicht ist:** es entfernt einen Dämpfer, es fügt kein Signal hinzu.
Liefert der Funnel mit nur noch einer Lesson weiterhin 0 Kandidaten, waren die Lessons nicht
die Ursache — drei Wochen Verdacht sauber ausgeschlossen, was für sich ein Ergebnis ist.
**H4-b (Doppelzählung) bleibt bewusst danach** — der Alters-Cap kann sie gegenstandslos machen,
und zwei Hebel gleichzeitig zu ziehen hat bei H1 schon Messwochen gekostet.

### Next

1. **Nikinger, das Restart-Gate:** denselben Einzeiler **einmal täglich** laufen lassen, bis
   `"ok": true` kommt, dann das `allowance`-Objekt zurückspielen. **Heute (08-08) nicht erneut
   laufen lassen** — bereits ausgeführt, Ergebnis oben; ein zweiter Lauf am selben Tag liefert
   dieselbe Antwort, weil das Kontingent an einer Perioden-Grenze zurückgesetzt wird, nicht
   fortlaufend. Ein abgelehnter Call kostet nichts (403, wird nicht abgerechnet), tägliches
   Prüfen ist also gratis.
   ```bash
   phase1_broker_wrapper/.venv/bin/python -m broker_wrapper.cli \
     --broker ig_demo ohlcv --epic IX.D.DAX.IFMM.IP --resolution MINUTE --count 5
   ```
   `totalAllowance` dimensioniert das Budget, `allowanceExpiry` datiert den Reset.
2. **Erst danach** Universe-Reset der 18 quarantined Epics (Präzedenzfall 2026-07-06). Vorher
   ist er **schädlich**, nicht nur wirkungslos: `fail_count=0` gegen ein noch erschöpftes
   Kontingent quarantäniert alle 22 binnen drei Verify-Runden erneut.
3. **Vor einer echten Messwoche: H1s Grundverbrauch budgetieren.** Die Fixes verhindern
   Eskalation, Datenkorruption und unbegrenzte Retries, senken aber ~33 Fetches × 300
   Punkte/Tag im **Gutfall** nicht. Zwei Hebel:
   (a) `MINUTE_5` × 60 = ⅕ der Kosten, (b) weniger Epics/Paare. **(a) nicht blind schalten** —
   `resolve_paper_trade` löst Same-Bar-SL+TP bedingungslos zu SL auf, gröbere Bars könnten den
   SL-Anteil systematisch aufblähen. Der Offline-Test dazu ist **nicht möglich** (Roh-Bars
   werden nirgends persistiert: nur Auflösungen in `paper_trades`, `data/cache/` sind
   yFinance-**Tages**bars, alle 1.082 `market_regime_snapshots` sind `quote_only` mit
   `atr_points IS NULL`). Ersatz: budgetierter Live-Test nach dem Reset — je ein
   `get_ohlcv(MINUTE,300)` und `get_ohlcv(MINUTE_5,60)` auf demselben Epic, 360 Punkte einmalig.
4. ~~H4-a bauen~~ ✅ **gebaut** (s. Nachtrag Punkt 4, `lesson_max_age_days = 30`). Der
   **Effekt** ist noch nicht gemessen — das braucht eine Woche mit laufendem Daemon, also
   hängt er an Punkt 1–2. Erwartung, gegen die zu prüfen ist: 3 von 4 Lessons fallen raus.
5. **H4-b (Doppelzählung) erst nach dieser Messung entscheiden** — der Alters-Cap kann sie
   gegenstandslos machen (s. Scope-Doc §3/§4).
6. **B3** (Margin-Headroom) unverändert parkiert, eigene Session.
7. **H3/H5/H7** offen, nachrangig zu H4.

### Open questions / blockers

- **`totalAllowance`/`allowanceExpiry` unbekannt** — blockiert 1–3 oben. Der Floor-Wert 2000
  im Code ist ein **deklarierter Platzhalter**, kein gemessener Wert.
- ~~Phase-9 `check_ig_side` liest einen kontoweiten Budget-Ausfall als
  Instrumenten-Untauglichkeit.~~ ✅ **gefixt** (Nachtrag Punkt 2, Nikinger-Go für den
  Cross-Phase-Eingriff). Offline per Test bewiesen, **nicht** live — der Beweis am echten
  Universum kommt erst mit dem nächsten Daemon-Lauf.
- **Mess-Substrat WI-2 — gesichert:** die `paper_id`s der 390 Zeilen sind **vor** dem ersten
  Tick nach `OUTAGE_EXPIRED_PAPER_IDS_2026-08-08.json` geschrieben (read-only erzeugt, kein
  Schema-Zusatz) — danach wären sie nicht mehr von echten Geometrie-Expiries zu trennen. Die
  115 bereits am 08-04 expirierten sind **nicht** enthalten; für die bleibt nur die
  Datumsabgrenzung.
- **`_PAPER_ALLOWANCE_FLOOR = 2000` ist ein Ausfallrisiko, keine bloße Ungenauigkeit:** liegt
  das echte `totalAllowance` bei oder unter 2000, ist `budget_ok()` dauerhaft `False` und der
  Tracker löst **gar nichts** mehr auf — einziges Signal wäre eine CRITICAL-Log-Zeile. Nach
  dem ersten erfolgreichen Fetch das geloggte `allowance`-Objekt prüfen und ggf. senken.
- **W2 (Sub-Noise-Geometrie) weiterhin unbeantwortet** — jetzt zum dritten Mal an einer
  Infrastrukturfrage statt am Funnel gescheitert.
- ~~B5-Restfehlerrate~~ ✅ **gefixt** (Nachtrag Punkt 3, Satzgrenzen-Trimmung mit zwei
  Qualitätswächtern).
- **Neu offen — der Floor und H4-a sind beide ungemessen:** `_PAPER_ALLOWANCE_FLOOR` wartet auf
  ein echtes `totalAllowance`, H4-as Wirkung auf eine Woche mit laufendem Daemon. Beide sind
  gebaut und getestet, aber **offline** — keiner von beiden hat je gegen echte IG-Daten gelaufen.
---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
