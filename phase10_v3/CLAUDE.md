---
status: live
purpose: ACTIVE phase head — V3: Abstain-/No-Trade-Lessons + Persistenz-Reform + Paper-Trades, alles live auf main; zwei Datenwochen gefahren (07-20/24 + 07-27/31). Woche 2 ausgewertet 2026-07-31: Funnel kollabiert (366 Zyklen → 1 Kandidat → 0 Trades), WI-1/WI-5 beantwortet (W1+W5 bestätigt), WI-2 zum zweiten Mal tot; drei neue Bugs seit Rollout (B1 point_value-Drift = 40x-Oversizing auf AEX, B2 Reward-Score steigt nach jedem Verlust, B5 Paper-Lesson-Prompt) + zwei strukturelle Lücken (Margin-Headroom, leeres Mess-Substrat); Phase-11-Scope-Vorschlag mit 7 Hypothesen liegt vor (H2→H1→H6), Entscheidung beim Nikinger
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
  - ./SESSIONS_ARCHIVE.md   # full session history (L3)
updated: 2026-07-31
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

## Session stopped — 2026-07-31 (Fr — zweite Datenwoche ausgewertet, read-only; 3 neue Bugs + Phase-11-Scope)

> Special-Task-Session (Nikinger): „Datenwoche ist rum — sag direkt, wenn etwas schiefgelaufen
> ist; wenn genug Daten da sind, tiefe Analyse + Hypothesen für Phase 11." Kein Code-Touch,
> DB nur `mode=ro` (Wochentags-Regel). Advisor vor dem Report konsultiert — sein
> Diskriminator-Query (Regime-Snapshots auf dem Happy Path) hat B4 von „leer weil Funnel leer"
> auf „teils Design, teils Verdrahtungslücke" präzisiert; seine Warnung zu B2 (Ein-Zeichen-Fix
> repariert den Loop nicht) ist im Report als eigene Rechnung belegt.

### Completed
- **`DATA_WEEK_REVIEW_2026-07-31.md`** (neu, 📕 dated, in `docs/INDEX.md`) — vollständige
  Auswertung. Kernzahlen der Woche: **366 Research-Zyklen, 1 Kandidat, 1 Debatte, 0 Trades,
  0 neue Paper-Trades**, 364 Abstain-Records zu 100 % `REASON_NO_CANDIDATES`. Mechanik
  einwandfrei (0 `consecutive_failures`, kein Kill, 10/10 Tage stabil) — der Funnel selbst
  ist der Ausfall.
- **WI-1 + WI-5 sind beantwortet, W1 + W5 bestätigt.** Es gab rote Tage (3 von 4 auswertbaren
  DAX-Sessions negativ). Am 07-30, bei breiter europäischer Schwäche, erzeugte Research
  **einen BUY** auf dem einzigen Instrument mit positivem Drift und schrieb die Begründung
  selbst hin: *„a SELL on DAX/CAC/IBEX [is] tempting, **but** recent trade history shows 4
  consecutive BUY losses on DAX — avoiding that instrument."* Die Verluste dämpfen die
  **Instrumentenwahl**, nicht die Richtungswahl. Stand kumulativ: 30 Debatten, 29 BUY-Seeds
  vs. 1 SELL, **nie ein Richtungs-Flip**, 8× TRADE (alle BUY).
- **WI-2 zum zweiten Mal tot** — diesmal ohne Bug: der Shadow-Pair-Trigger ist
  `REASON_DEBATE_ABSTAIN`, und die eine Debatte der Woche sagte TRADE. WI-3 bestätigt (10/10
  Tage an der 200k-Kappe, Research endet 15:2x). WI-6 ohne neue Evidenz.
- **Drei neue harte Bugs, alle seit Rollout falsch, alle exakt nachgerechnet** (Details +
  Fix-Ausdrücke im Review-Doc §4):
  1. **B1 `point_value`-Drift** (`phase8_scheduler/scripts/wiring.py:616`): `point_values`
     kommt aus der statischen 4-Epic-`EXTENDED_UNIVERSE`, Research handelt aber die
     8-Epic-DB-Universe → AEX mit 1,0 statt **40,0 €/Punkt** → **40× Oversizing**
     (Size 26,8 = 1,18 Mio € Nominale, Risiko am Stop **120 % des Kontos**). Erklärt **alle
     drei** AEX-Rejects (07-15/07-20/07-30) und löst damit den als „unrettbar verloren"
     abgelegten Bug-B-Vorfall vom 07-15. **50 % aller 8 TRADE-Entscheidungen der Historie sind
     an Sizing-Config gestorben, nicht am Markt.**
  2. **B2 Reward-Score-Inversion** (`phase7_reward/reward/scorer.py:115`): `debate_confidence`
     wird als [0,1] behandelt, geliefert wird 0–100 → `process_delta` +92,25 statt ~+3 →
     per-Trade-Delta clamped **immer** auf +5 → Score **55→60→65→70 über vier Totalverluste**
     → `get_risk_level()` = AGGRESSIV → `risk_pct` 3 % statt 2 %. Die Unit-Tests kodieren die
     falsche Skala (`debate_confidence=0.9`), deshalb unsichtbar. ⚠ **Der Skalen-Fix allein
     repariert es nicht** (bliebe +1,2/Verlust, weil ein SL-Treffer den `clean_exit_bonus`
     kassiert) — das ist eine Phase-11-Designfrage.
  3. **B5 Paper-Lesson-Prompt** (`abstain_lessons/reflect.py:62-65` vs. `:78`): Prompt sagt
     „max. zwei Sätze", Validator erzwingt ≤300 Zeichen, die Grenze steht nicht im Prompt →
     am 07-27 6 Reflect-Calls bezahlt, 2 Lessons persistiert.
- **Zwei strukturelle Lücken (B3/B4, brauchen Designentscheidung, kein Quickfix):**
  Leverage-Cap ohne Margin-Headroom (Nominale konstruktionsbedingt auf `available × 20`
  gepinnt; 22,1 rejected / 22,0 accepted am selben Vormittag) und das **leere Mess-Substrat**
  (alle 1.036 `abstain_records` mit `detail=''`/`context_json='{}'`; alle 722
  `market_regime_snapshots` `quote_only`/NULL — Bars sind dokumentierte Degradation,
  `spread_pct` dagegen eine echte Verdrahtungslücke an den drei `_notify_context`-Call-Sites).
- **Korrektur am 07-27-Block:** der Bug-2-Fix vom 07-25 **ist** live bewiesen — am 07-27 liefen
  6 Haiku-Calls über denselben gefixten `_AbstainLLMAdapter._SCHEMA` (Abstain-Sink *und*
  Paper-Pfad teilen ihn), 2 Lessons persistiert, kein HTTP 400. Der 07-27-Block sagte „kein
  Call wurde versucht" — das galt nur für den Debatte-Abstain-Pfad, nicht für den Adapter.
- **Der Kern-Befund** (Review §3): eine geschlossene Rückkopplung — 4 SL-Verluste → 4 Lessons
  („prüfe die Entry-Qualität", **4.529× in den Prompt gerendert**) + dieselben 4 Verluste als
  zweiter Kanal via `recent_trades` → Modell abstaint 365/366 und begründet es wörtlich damit
  → keine Trades → keine neuen Outcomes → die 4 alten Lessons bleiben. Ein **absorbierender
  Zustand**, aus dem sich der Loop nicht selbst befreien kann.
- Session-Block 2026-07-27 verbatim nach `SESSIONS_ARCHIVE.md` rotiert.

### Next
- **Nikinger, Entscheidung:** Phase-11-Scope. Vorschlag im Review §5, Reihenfolge
  **H2 → H1 → H6**, danach mit echten Daten H7/H4/H3/H5:
  - **H2** Sizing-Wahrheitskette (B1-Fix + fail-closed statt still 1,0 + Margin-Headroom) —
    klein, sicherheitskritisch, **vor** jedem Live-Gedanken.
  - **H1** *(größter Hebel)* Messung vom Funnel entkoppeln: Shadow-Pairs **zeitgesteuert**
    statt an `REASON_DEBATE_ABSTAIN` gekoppelt. 8 Epics × alle 30 min ≈ **130 Paare/Tag**,
    risikofrei, null LLM-Kosten, beantwortet **WI-2 an einem Tag**. Nutzt `PaperEngine` +
    `PaperTradeTracker` unverändert; neu ist nur ein Scheduler-Tick (Muster:
    `universe_refresher` + `_due_after()`).
  - **H6** Mess-Substrat füllen (`last_no_pick_reasoning` in die ohnehin geschriebene
    `abstain_records`-Zeile; `spread_pct` durchreichen) — klein, ~70 Begründungen/Tag statt 1.
- **B1/B2/B5 sind fixbar, ohne den Phase-11-Scope abzuwarten** (klein, additiv, in bereits von
  V3 berührtem Code). Bei B2 **zwingend** die Testskala in `test_scorer.py` mitziehen, sonst
  bleibt der Fix ungeprüft. Alles am Wochenende bei gestopptem Bot.
- **⚠ S6 bleibt AUS.** Die 5 vorhandenen Paper-Lessons sind tautologisch, auf beiden Seiten
  desselben Paares wortgleich und aus Backfill-Artefakten abgeleitet.

### Open questions / blockers
- **W2 (Sub-Noise-Geometrie) ist weiterhin unbeantwortet** und ist die Wurzel: solange nicht
  klar ist, ob 30/45 Punkte auf DAX überhaupt gewinnbar sind, ist jede Arbeit an der
  Richtungslogik verfrüht. H1 liefert die Antwort in Tagen.
- Der Scheduler-Daemon lief bei Analyse-Ende (Fr 21:26 lokal) nicht mehr (letzter Reconcile
  21:22, kein Prozess). Freitagabend unauffällig — falls das nicht der Nikinger war, startet
  er Montag aber auch nicht von selbst.
- N1 (`INSUFFICIENT_FUNDS`) ist **kein** Beobachtungspunkt mehr, sondern durch B1/B3
  vollständig erklärt.

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
