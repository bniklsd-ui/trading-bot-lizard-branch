# CLAUDE.md — Project Instructions

> Read this file before doing anything in this repository.
> It is the single source of truth for project rules, conventions, and current state.

---

## What this project is

A multi-phase, AI-augmented CFD trading bot for the DAX.
Primary broker: IG Markets (EUR account). Multi-broker abstraction in place.

The bot is structured around a **5-Gate Execution Pipeline** with adversarial
AI-driven direction decisions (Bull/Bear/Judge debate) and a deterministic VETO
cascade.

Full architecture: `docs/architecture/tradingbot_v2_architecture.svg`
Build order: `ROADMAP.md`

---

## Core principle (read carefully)

**Bauprinzip:** So wenig AI wie möglich, so viel AI wie nötig.

**Code macht:**
- Alle API-Calls (GET, POST, DELETE)
- Authentication, Session-Handling, Token-Refresh
- Spread / Drift / Momentum / Sizing — alle Berechnungen
- VETO-Checks (alle vier sind Code, nicht AI)
- Gate-Logik (True/False Entscheidungen)
- Persistenz (SQLite Reads/Writes, JSON Reads/Writes)
- TTL-Verwaltung, Retry-Logik, Error-Handling, Normalisierungen

**AI macht NUR:**
- "Welcher Kandidat?" — Research LLM
- Bull/Bear/Judge Debatte (Richtungsentscheidung)
- Lesson-Extraktion nach Trade (Longterm Brain)
- Council-Evaluation (Strategieprüfung)
- **NICHTS sonst**

If you find yourself reaching for an LLM call to do data fetching, formatting,
filtering, validation, or any deterministic logic — STOP. Use code instead.

---

## Hard Rules (no exceptions)

1. **Never put credentials in files.** Not in `.env`, not in JSON, not in YAML,
   not anywhere on disk. Credentials live ONLY in the OS keyring
   (macOS Keychain / Windows Credential Manager / Linux Secret Service).
   Access via `broker_wrapper/credentials.py`.

2. **Never bypass VETOs.** If you find code that skips a VETO check "for testing"
   or "for now" — flag it loudly. VETOs are the difference between a working bot
   and a blown account.

3. **Never let AI output trigger an order directly.** Every AI output
   (Bull/Bear/Judge APPROVED, Research candidate selection) MUST pass through
   code-side validation before any order is placed. Hallucinations are a real
   risk and are mitigated structurally, not by trust.

4. **Never test against real money first.** All new code is exercised against
   the IG Demo account via `scripts/smoke_test.py` before being trusted with the
   live account. No exceptions.

5. **The Force Trigger must respect Daily PNL.** Per the architecture analysis,
   the manual override (`ig_bot_force_trigger`) should be **locked** when daily
   PNL is negative. Human override at moments of emotional vulnerability is the
   biggest identified risk.

6. **Output envelope is canonical.** Every broker adapter method returns an
   `Envelope` JSON object (see `broker_wrapper/envelope.py`). Do not deviate
   from this shape. Tests, CLI, FastAPI, and bot core all depend on it.

---

## Current state

**Active phase:** Phase 8 — Scheduler (`phase8_scheduler/`, Paket `scheduler`): 🟡 **code-complete +
gemerged nach `main` (2026-06-30); v1.5-Hotfix gemerged (2026-07-02)** — mechanisch bewiesen,
**autonomer Trade noch NICHT live-bewiesen** (ehrlich geflaggt gemerged, um den Build weiterzutragen).
**⚠ v1.5-Stand (ehrlich, 2026-07-02):** die drei Code-Fixes A/B/C sind fertig + mockgrün (P1 52 · P2 67 ·
P3 72 · P4 122 · P5 154 · P6 70 · P7 131 · P8 182), aber der erste **Live-Lauf** deckte einen
**yFinance-Blocker** auf — CAC 40 (`^FCHI`) und IBEX 35 (`^IBEX`), die im Step-2-Variety-Track **nie
live-verifizierten** Ticker, liefern keine Kursdaten (*„possibly delisted"*) → deren P3-Brain-Context
degradiert zu `None` (2 von 4 Instrumenten reduced-signal; **kein** Hard-Crash — Fallback auf letzten
Daily-Close, **kein VETO betroffen** — Momentum-VETO nutzt IG-Echtzeit-Bars, **nicht** der
v1.5-Provenance-Code). Der **net-new autonome open→close** bleibt unbewiesen; es fehlt zudem **echtes
Logging**. **Nächster Track = v1.6** (erst Observability, dann `^FCHI`/`^IBEX` verifizieren/fixen oder
droppen, dann der Live-Beweis), Handover: `phase8_scheduler/PHASE8_V1.6_HANDOVER.md` (v1.5-Kontext:
`PHASE8_V1.5_HOTFIX_HANDOVER.md`). **Initial-Plan (das „Was", 2026-07-02, bewusst in Claude Code
statt Web-Chat erstellt — Begründung dort §0a):** `docs/concepts/phase8_v1.6_hotfix_plan.md`; die
„Wie"-Session baut daraus den Ausführungsplan.
(gestartet 2026-06-27). **Mission (zuerst lesen):** Phase 8 heißt „Scheduler", aber das Ziel ist
**autonome, unbeaufsichtigte Erzeugung echter Demo-Trades** — alles danach (Confidence aus
`INSUFFICIENT`, P9-Instinct-Promotion) ist auf reale Outcomes gegatet. Der harte Pfad ist die
**autonome Kandidaten-Generierung** (echtes P4-Research, **nie** der manuelle Seed), nicht „ein
Cron-Job bauen". **Phase 8 fügt KEINE neue AI hinzu** (reine Mechanik; AI bleibt P4-Pick/P6-Debatte/
P7-Lesson). Langlaufender Daemon (injizierbares `now_fn`/`sleep_fn`), Auto-Confirm (demo-only,
fail-closed), Datei-Kill-Switch, Tages-Loss-Breaker, Token-Budget, idempotenter Reconcile-Pass,
zuletzt eine read-mostly Web-UI. **Build-Reihenfolge:** Cleanup → Verify → autonome Candidates →
Auto-Confirm/Safety → Reconcile → Loop/Daemon → **zuletzt** UI; unter Druck fällt die UI weg, **nie**
die Safety. Konzept: `docs/concepts/phase8_scheduler_concept.md` (20 gelockte Entscheidungen +
Modul-Plan). **Stand (2026-06-29): Module 1–12 gebaut + grün; erster Operator-`live_test`-Lauf grün (3/3) —
aber NUR teilweise live-bewiesen, KEIN ✅-Flip.** **Bewiesen:** Daemon-Lifecycle (Preflight→bounded Loop→sauberer
Shutdown), State-Persistenz, autonomes echtes P4-Research (Sonnet) mit korrektem Fail-Safe-ABSTAIN (KONSERVATIV,
Score 45.83<50 → Floor 70 by-design, kein Bug), **Reconcile+Reward-Loop auf 2 realen früheren Demo-Trades**
(open→close→reward→lesson auf echten Outcomes). **NOCH NICHT bewiesen** (braucht einen Mehr-Zyklen-/Mehr-Tage-Lauf
in einem nicht-konservativen Fenster): ein netto-neuer autonomer Trade in **einem** sauberen Lauf geöffnet+geschlossen;
die Safety-Breaker, die **tatsächlich auslösen**; Mehr-Zyklen-Verhalten; Edge/Profit (nie im Scope). **Fix 2026-06-29:**
das Token-Budget war diesen Lauf deaktiviert (`daily_token_budget=None`) → Default jetzt by-default scharf
(`200_000` ≈ €0.8/Tag Runaway-Breaker) + Flags (`--no-token-budget`/`--token-budget`); **173 P8-Tests**. Erst nach
den bewiesenen Punkten Doku-Flip auf ✅ + Merge. Modul 12 = `webui/`
(FastAPI read-mostly, DB `mode=ro` + Kill/Command-Dateien, Dark-Neumorphism-Dashboard) + reale
Start/Stop-Pause (neues `scheduler/command.py` + additiver Runner-Command-Poll, konzept §12 „Daemon
pollt"; `stop`=weiche Pause, KILL=harter Stop). **173 P8-Tests** (171 + 1 Envelope-Regression +
1 `--no-token-budget`). Initial-Steps (Step 0 Legacy-grep = sauber/No-Op, Step 0b
Doku-Reconciliation, Step 1 Contract-Verify, Step 2 Scaffold) **erledigt**. Gebaut + getestet (gemockt/
offline, kein Netz/LLM): `config` · `exceptions` · `clock` · `state` · `killswitch` · `safety`
(AutoConfirm) · `backoff` · `budget` · `research_tick` · `reconcile` · **`runner`** (die Loop —
Preflight/run/Shutdown/`request_stop`, Contract A bare `executor.run()`, injizierte `now_fn`/`sleep_fn`
+ `max_iterations`) · **Modul 11 = Composition Root:** `scripts/wiring.py` `build_scheduler()` (EIN
geteilter warmer `ig_demo`-Broker treibt echtes P4-Research, P6-Debatte **und** P7-Reward beide in EINEN
P5-Executor; 3 Closures `realized_pnl_today`/`pending_reconcile_fn`/`preflight_fn`; harter Demo-Lock) +
`scheduler/run.py` (`python -m scheduler.run`, SIGTERM→`request_stop`) + `run_scheduler.sh` + offline
`smoke_test.py` (3/3) + operator `live_test.py`. **173 P8-Tests** (Regression unberührt: P1 52 · P2 62 ·
P4 94 · P5 146 · P6 70 · P7 128). Jedes Scheduler-Modul + `scripts.wiring`/`scheduler.run` ist
import-isoliert (zieht NONE cross-phase beim Laden — Cross-Phase lazy in den Funktionen).
**Step-1-Befunde (Code = Wahrheit, ⚠ weichen vom Handover ab — voll in `phase8_scheduler/CLAUDE.md`
→ `## Verifizierte Contracts`):** (A) `confirm_fn` ist ein **Konstruktor**-Arg, **nicht** `run()`-Arg
→ `run()` arglos, Executor **einmal** mit `AutoConfirm` gebaut; (B) `candidates_are_fresh()` ist
**False für `[]`** ⇒ **No-op-`research_runner` injizieren** (echtes Research vorher in
`research_tick`); (C) Seed-Marker englisch `"MANUAL SEED (not a real research pick)"`; (D)
`OrderPlan` trägt **kein `account`** → Demo-Lock strukturell im Wiring (`config.account="demo"`, nur
`ig_demo`-Broker); (E) `realized_pnl_today` für den Loss-Breaker aus der **DB** (CLOSED_BY_BROKER
trägt keine sofortige P&L). Reuse: `reconcile_startup` (P5) + `reward_sink.reconcile_open_trades()`
(P7 13b) decken den Reconcile-Pass ab. **Alle fünf Befunde sind in Modul 11 (`scripts/wiring.py`)
verdrahtet** (No-op-`research_runner`, Demo-Lock, DB-`realized_pnl_today`-Closure, geteilter Broker).
**Modul 12 ✅ (2026-06-28): `webui/`** (FastAPI read-mostly, DB `mode=ro` + `scheduler_state.json` +
Kill/Command-Dateien; Dark-Neumorphism-Dashboard GitHub-Dark/Monospace/Polling 7 s, kein Build-Step;
Control **nur** Datei-Writes → UI-Crash kann Trading nie berühren, Decision 14) **+ reale Start/Stop-
Pause** (neues `scheduler/command.py` + additiver Runner-Command-Poll, konzept §12 „Daemon pollt":
`stop`=weiche reversible Pause, KILL=harter Stop; keine Command-Datei ⇒ Loop bit-identisch).
`fastapi`+`uvicorn` die einzigen neuen Runtime-Deps (nur UI). **Nächstes: Operator-Re-Run** von
`live_test.py` in einem **nicht-konservativen** Fenster (Score ≥ 50 → Floor 55) gegen IG-Demo
(+ `run_webui.sh`), um einen **netto-neuen autonomen open→close in einem sauberen Lauf** zu fangen +
die Safety-Breaker auslösen zu sehen (die WARNING „token budget is DISABLED" muss weg sein); **erst
danach** Doku-Flip auf ✅ + Merge. Detail-Analyse + proven/unproven: `phase8_scheduler/CLAUDE.md`
→ `## Session stopped — 2026-06-29`. **Update (2026-06-30):** weil der „echte" autonome Trade nie/spät
kommt (der Bot **abstained** quasi immer), ist die Diagnose + ein v1.5-Hotfix-Vorschlag in
`phase8_scheduler/PHASE8_V1.5_HOTFIX_HANDOVER.md` (für eine Claude-Web-Planungssession) festgehalten —
drei Ursachen: **(C, Hauptblocker)** 1-Instrument-Universe (`research/models.py:320`), **(B)** Doppel-Clamp
unter Score 50 (BUY-only + Floor 55→70, `candidate_filter.py:47-66,70+`), **(A)** Verifikations-Trade-Lessons
im P4-Prompt (`context_builder.py:184`). **Empfehlung: Phase 8 mit ehrlichen Flags nach `main` mergen**
(verified = Mechanik/State/Reconcile+Reward; NOT verified = netto-neuer autonomer open→close + auslösende
Safety-Breaker), **v1.5 auf frischem Branch**. Voller Befund: `phase8_scheduler/CLAUDE.md` →
`## Session stopped — 2026-06-30`.

**Phase 7** bleibt ✅ **live-verifiziert (2026-06-26) + gemerged nach `main`** — der Reward-Loop läuft
end-to-end live (place → monitor → lag-freie Close-Confirm-P&L → score → reward → lesson); ⚠
**live-verifiziert ≠ profit-validiert** (ein Trade beweist den Pfad, nicht die Edge). Detail im
**Phase-7-status**-Block unten. Phase 6 (Bull/Bear/Judge-Debatte) bleibt ✅ Code-complete +
live-verifiziert, **gemerged + gepusht nach `main`** (`49cda8a`, 2026-06-16); Phase 5 (ig_bot Gates
1–5 + 4 VETOs + place/monitor/close) bleibt ✅ abgeschlossen + live-verifiziert (Order-/Monitor-Pfad).

**Phase 7 status:** ✅ **live-verifiziert (2026-06-26) + gemerged nach `main`** — Reward-Mathe Confidence+Scorer + Synthetik/Echt-Trennung + Lesson-AI + pnl_resolver + Recorder-Orchestrierung + Executor-Seam + Loop-Closure + Migration 002 + Wiring/Operator-Scripts + signed-size-Fix + reconcile/retry + **lag-freie Close-Confirm-P&L (cross-phase P1+P5+P7)**. `live_test.py` 5/5 (SELL → Time-Stop → Confirm-P&L `-41.16` → CLOSED + `reward_pts` + `trade_lessons`); **128 P7-Tests** (Regression P1 52 · P2 62 · P4 94 · P5 146 · P6 70). ⚠ **live-verifiziert ≠ profit-validiert** (2026-06-26)
- **Live-verifiziert ✅ (2026-06-26):** `live_test.py` → **5/5**. SELL `DIAAAAXUYTL77A3` (size 19.6, open 24771.3) → Time-Stop-Close → **Close-Confirm** lieferte close 24772.4 + `profit_loss=-41.16` → in-cycle resolve gelang (Branch 1: IG liefert `profit`; die Differenz zur Level-Rechnung = der Spread) → `trade_outcomes` CLOSED + `reward_pts` + echte Haiku-`trade_lessons`. Der ganze Loop ist damit end-to-end live bewiesen. Doku-Flip + Merge nach `main` in diesem Commit.
- **Step 13c ✅ (2026-06-23) — lag-freie P&L aus dem Close-Confirm (cross-phase, user-authorized "specific yes").**
  `inspect_history.py` bewies: **IG-Demo bucht `get_trade_history` erst nach Settlement** (intraday 0 Zeilen) →
  die History ist intraday als P&L-Quelle unbrauchbar. Fix: `close_position` (P1) pollt jetzt den Close-Confirm
  (`close_level`+`profit`), `monitor_position`→`ExecutionResult` (P5, nur TIME_STOP) reicht sie durch, und der
  `pnl_resolver` (P7) **bevorzugt** sie vor der History (die bleibt Fallback für CLOSED_BY_BROKER/Confirm-Timeout).
  Alle Edits **additiv** (Defaults ⇒ P1/P5 bit-identisch); dated Notes in **jeder** berührten `.md`. Regression:
  **P1 52 · P2 62 · P4 94 · P5 146 · P6 70 · P7 128.**
- **Step 13b ✅ (2026-06-23) — Reward-Live-Debug nach dem ersten `live_test`-Lauf (`RESULT 3/5`).** Einzige
  Ursache: `pnl_resolver` warf `PnLUnavailable` (kein Size-Match für die SELL size 19.8). Fix deckt **beide**
  konsistenten Ursachen: (1) **magnituden-basierter Size-Match** (`abs(abs(tx_size)−abs(size))`) — IG signt
  das History-`size` negativ für SELL → ein exakter Vergleich verwarf jeden SELL für immer (Fix **defensiv
  im P7-Resolver**, P1-Sign-Normalisierung bewusst zurückgestellt); (2) **`RewardSink.reconcile_open_trades`**
  = idempotenter Retry für noch-OPEN-Trades bei IG-History-Lag, von `live_test.py` nach kurzem Warten
  getrieben. **+ read-only `scripts/inspect_history.py`** (History-Dump zum Bestätigen der Ursache). **+6
  P7-Tests (118→124)**, Regression unberührt (**P2 62 · P4 94 · P5 142 · P6 70**). **Keine** Cross-Phase-Edit.
- **Step 13 ✅ (2026-06-23):** Wiring + Credentials-Shim + Operator-Scripts — **schließt den Phase-7-Build**.
  `reward/credentials.py` (verbatim P4/P6-Shim → `get_credential("anthropic_api_key")`), `scripts/wiring.py`
  (`build_reward_sink`/`build_brain`/`build_executor`, **spiegelt P6**: Executor direkt aus dem installierten
  `execution`-Paket, **einen** Broker geteilt, `reward_sink=` injiziert, `research_runner=_no_research` —
  **keine** P5-`ig_bot.py`-Edit, Phasen-Isolation), `scripts/smoke_test.py` (1× echter Haiku-`reflect`, DRY),
  `scripts/live_test.py` (voller open→close→reward→lesson gegen IG-Demo; harte Proofs `trade_outcomes`(CLOSED)+
  `reward_pts`, Lesson best-effort/Info), `scripts/backfill_synthetic.py` [→ Opus] (**guard-first** — `guard_
  synthetic_path` vor jedem DB-Open → exit 2 wenn Ziel == live, nie auto-live). Reward-Live-Pfad **debatte-frei**
  (einzige AI = die Lesson-Haiku). **Keine neuen Unit-Tests** (Scripts+Shim operator-run, nicht collected —
  konsistent P4/P5/P6; Synthetik-Kern in Steps 4/6 gedeckt). Verifiziert: alle 5 `py_compile`, offline-Imports
  (`reward.credentials`/`scripts.wiring`), `--help` exit 0, **`backfill_synthetic` end-to-end gegen Temp-DB**
  (12+12 Zeilen, Migration-002-Spalten befüllt, exit 0) + **Guard-Refusal exit 2**. Regression unberührt:
  **P7 118 · P2 62 · P4 94 · P5 142 · P6 70**.
- **Step 12 ✅ (2026-06-22):** Migration `002` + minimale P2-Berührung (Decision G) — **zweite, vom
  Konzept sanktionierte P2-Berührung** (nach Step 11s P4-Touch). `phase2_persistence/migrations/
  002_phase7_reward.sql` (additiv, version 2): `ADD COLUMN trade_outcomes.initial_risk REAL` +
  `trade_outcomes.account TEXT` + `reward_pts.r_multiple REAL`. `persistence/db.py`:
  `_TRADE_COLUMNS += ("initial_risk", "account")` + `_REWARD_COLUMNS += ("r_multiple",)` (Whitelist —
  **keine** Logik-Änderung). Damit landen die von `Scorer`/`RewardSink`/`build_opened` **bereits
  geschriebenen** Felder gegen die echte DB statt still verworfen zu werden. **Reconciliation (Code=SoT):**
  die Datei liegt in `phase2_persistence/migrations/` (was der Runner als einziges Dir scannt:
  `db.py:75`/`schema.py:14`), **nicht** im Konzept-§4-Pfad `phase7_reward/migrations/`; frische DB =
  Version 2 → vier versions-asserting P2-Tests v1→v2 nachgezogen + 1 Spalten-Beweis + 2 Round-Trip-Beweise
  → **P2 59 → 62**. Regression unberührt: P7 118 · P4 94 · P5 142 · P6 70.
- **Step 11 ✅ (2026-06-22):** Loop-Closure (Decision I) — `mark_lesson_used` in P4-`research/research.py`
  verdrahtet (vom P7-Konzept §6 Step 11 verlangte P4-Berührung). Die „read→prompt"-Hälfte war schon da
  (Contract 1.5: `build_context` zieht `get_recent_lessons(5)`, `prompt._render_lessons` rendert);
  Step 11 ergänzt die „mark used"-Hälfte: best-effort `_mark_lessons_used(context.recent_lessons)` **nach**
  erfolgreichem `ask_candidate` (vor der Validierung → Pre-LLM-Abbrüche over-counten nicht). Fehlende `id`
  skip; werfendes `mark_lesson_used` → `warning` + weiter. **Erster DB-Write aus P4-Research** (benigner
  `used_in_research`-Increment, kein Trade/Outcome-Write). **+6 Tests → P4 88 → 94**; P7 118 · P5 142 ·
  P6 70 · P2 59 unberührt.
- **Step 10 ✅ (2026-06-22):** Executor-Naht (Decision A) verdrahtet — **erste P5-Berührung**.
  `execution/protocols.py` bekam ein duck-typed `RewardSink`-Protocol; `execution/executor.py` einen
  additiven **keyword-only** `reward_sink: Any | None = None` (default `None` ⇒ **P5 bit-identisch +
  AI-frei**, spiegelt `debate_runner`). `on_trade_opened` nach `place_result.status == "OPEN"` (vor
  `monitor_position`), `on_trade_closed` nach dem Monitor-Return (nur `CLOSED_BY_BROKER`/`TIME_STOP`) —
  **beide guarded** (`logger.critical`, kein Re-raise, Decision J). `build_opened`/`build_closed`
  übersetzen Executor-Locals in die P7-Contracts; `intended_open_level` aus `price_env` rekonstruiert
  (Contract 1.2: `place_order` droppt den Fill-`level`); **lazy** `reward.models`-Import → P5-Modul-Imports
  bleiben `execution.* + stdlib`. **3 Reconciliations:** lazy Import; `point_value=1.0`/`account="demo"`
  v1-Konstanten (durabler Tag = Wiring/Step 13); Seam-Tests in `phase5_execution/tests/test_executor.py`
  (wo Executor+Fakes leben), **nicht** `phase7_reward/tests/test_executor_seam.py`. **+7 Seam-Tests →
  P5 135 → 142; P7 118 · P4 88 · P6 70 unberührt.**
- **Scope-Lock (schlankes Modell, Konzept Rev. 2026-06-16-b):** Phase 7 = **Reward-Score**
  (`reward_pts`, prozess-bewusst ab Tag 1) + **Freitext-Lessons** (`trade_lessons`) +
  **observe-only outcome-anchored Confidence**. **Keine VETO-Berührung.** Die volle
  Instinct→VETO-Promotion („ECC") ist ein **separater, späterer Step** (Phase 9f / Konzept §7b),
  gated auf reale Outcomes — Promotion auf null validierten Outcomes würde Risiko zurück in die
  Safety-Schicht importieren.
- **AI-Grenze (Kernprinzip):** AI macht in P7 **nur** die Lesson-Extraktion (`reflect()`, ein
  Haiku-Call, best-effort). Scoring, Confidence-Mathe (Wilson-LB/Expectancy-R/N_min), Persistenz,
  P&L-Auflösung, Fehlerbehandlung sind **deterministischer Code**. `confidence` ist **observe-only
  und gatet NICHTS** (Decision C) — moduliert in v1 auch **nicht** `risk_pct`.
- **Naht:** optionaler, duck-typed `reward_sink` (Protocol) im `Executor`, default `None` →
  **P5 bit-identisch** (spiegelt das `debate_runner`-Muster). Zwei Methoden: `on_trade_opened`
  (Decision-Kontext) + `on_trade_closed` (Outcome+Reward+Lesson). Alle P7-Writes **best-effort,
  fail-closed** — werfen nie in den P5-Close-Pfad (Decision J: Fehler → `logger.critical`).
- **Reuse (Decision F):** `research.LLMClient` + `research.token_meter` (8-Feld, cache-aware) +
  `credentials`-Shim wiederverwendet — kein zweites Mess-/Client-System. DB-Writes über die
  bestehende **P2-CRUD** (`insert_trade`/`update_trade_close`/`insert_reward`/`insert_lesson`).
- **Stand (Step 1, dieser Step):** Step 0 (Turbo-grep) = **dokumentierter No-Op** (nur frozen
  `turbo_candidates.json`); Step 0b (Doku-Reconciliation) = ROADMAP-Phase-7 auf das schlanke Modell
  geflippt + `longterm_pre_trade_check() VETO` nach **Phase 9f** verschoben (kein Instinct→VETO-
  Framing mehr in der Doku); Step 1 (Verify-against-code) = 7 Verträge gegen Live-Code gepinnt →
  in `phase7_reward/CLAUDE.md` unter `## Verifizierte Contracts`; Step 2 = Paket-Scaffold
  (`phase7_reward/`, pkg `reward`).
- **Step 3 ✅ (2026-06-18):** `reward/models.py` — frozen Datentypen (`OpenedTrade`/`ClosedTrade`/
  `ConfidenceReport`/`RewardResult`/`LessonResult`) + `RewardConfig` (§5-Defaults; `live_db_path`
  auf den **echten** P2-Pfad `data/trading_bot.sqlite` korrigiert) + Exceptions; **21 Tests grün**.
  Noch reine Typen — Confidence/Scorer/Brain-Logik kommt in Steps 4–13.
- **Step 4 ✅ (2026-06-18):** `reward/confidence.py` — reine, deterministische Mathe (★):
  `wilson_lower_bound` (klein-N-stabil, 1/1 ≈ 0.21 statt 1.0), `expectancy_r`, `system_quality_number`,
  `compute_confidence` (**N < `n_min=10` → `INSUFFICIENT`, `confidence_value=None`**, gatet nichts —
  Decision C). Sub-Metriken immer befüllt, wenn berechenbar. **+30 Tests** (51 gesamt).
- **Step 5 ✅ (2026-06-18):** `reward/scorer.py` — prozess-bewusstes Reward-Delta (★, Decision B2/D):
  `Scorer.score()` = gebremste **Outcome**-Komponente (`outcome_weight · clip(R, ±r_clip)`, `loss_asymmetry`
  auf Verlusten) **+** **Prozess**-Komponente **unabhängig** vom Outcome (Clean-Exit vs. Time-Stop,
  Tight-Spread-Bonus, schwaches additives Debate-Signal — **kein** Multiplikator), `total` auf
  `±max_delta_per_trade` und `score_after` auf `[0,100]` geclampt. **+18 Tests** (69 gesamt). Reuse-Hinweis:
  Magnituden sind v1/tunbar (Decision D); Tests pinnen *relative* Eigenschaften. **Sibling-Suiten grün +
  unberührt** (P2 59 · P4 88 · P5 135 · P6 70).
- **Step 6 ✅ (2026-06-19):** `reward/synthetic.py` — pure Library für die harte Synthetik/Echt-Trennung
  (Decision H): `SyntheticTradeGenerator` (seed-reproduzierbare R-Multiple-Verteilungen),
  `guard_synthetic_path()` (wirft `SyntheticSafetyError`, wenn ein Synthetik-Write den `live_db_path`
  treffen würde — realpath-Vergleich; **Grenze = der DB-Pfad**), `select_edge_set()` (`include_demo_in_edge`
  + Synthetik-Ausschluss → `(r_multiples, wins, n)` für `compute_confidence`). **Kein DB-Write** — der
  Schreiber ist Step 13 (`backfill_synthetic.py`), der den Guard konsumiert. **+11 Tests** (80 gesamt),
  inkl. §7(c)-Beweis „Synthetik-Write trifft Live-Pfad nie". Sibling-Suiten grün (P2 59 · P4 88 · P5 135 · P6 70).
- **Step 7 ✅ (2026-06-19):** `reward/brain.py` — **das einzige AI-Modul der Phase** (Decision E). `Brain(llm_client,
  cfg).reflect(closed, outcome, market_context) -> LessonResult` = **EIN** Haiku-Call über den wiederverwendeten
  `research.LLMClient` (duck-typed, Phasen-Isolation), extrahiert **nur Sprache → eine knappe Lektion** (AI-Grenze:
  keine Zahl/Score/Entscheidung). **Best-effort/fail-closed (J):** jede Exception → `LessonResult(ok=False)`, kein
  Re-raise. `LessonExtractor`-Protocol = swappbare Schnittstelle (Batch/Scheduler später). **3 dokumentierte
  Konzept↔Code-Reconciliations:** Signatur `Brain(llm_client, cfg)` statt `…, token_meter, …` (token_meter
  **transitiv** über `ask_candidate`/`client.last_usage` reused — Doppel-Metering vermieden, spiegelt P6);
  Brain-eigener Fehlschlag = `warning` (das `critical` aus J gehört in den Recorder/Step 8); `reward/credentials.py`
  → Step 13. **+12 Tests** (92 gesamt). Sibling-Suiten grün + unberührt (P2 59 · P4 88 · P5 135 · P6 70).
- **Step 9 ✅ (2026-06-19, vor Step 8 gebaut — löst die „linked steps"-Notiz auf):** `reward/pnl_resolver.py` —
  `resolve(closed, broker, opened, cfg) -> (close_level, profit_loss, r_multiple)`, **deterministisch, kein AI**.
  **Heuristischer** History-Match, weil der IG-Record **kein `deal_id`** trägt (Contract 1.1; `epic`=instrumentName,
  `direction`=None) → harter size-Filter + open-level-Nähe + Recency-Tie-Break. Vorzeichen gratis (IG-`profit_loss`
  trägt es). **Fallback = `PnLUnavailable` werfen** (Operator-Entscheidung), **nicht** aus Levels approximieren
  (`ClosedTrade` hat kein `close_level` → würde Zahl erfinden) → idempotenter Retry via `deal_id`. **+12 Tests** (104 gesamt).
- **Step 8 ✅ (2026-06-19):** `reward/recorder.py` — `RewardSink` (Naht-Impl für Step 10). `on_trade_opened`
  (insert + **In-Memory-Stash**) / `on_trade_closed` (Guard→resolve→close→score→reward→best-effort-Lesson),
  **jeder Schritt fail-closed `critical` (J), idempotent via OPEN/CLOSED-Status.** 3 Reconciliations: Stash
  zwingend (`spread`/`debate_confidence` nicht in `trade_outcomes`); `confidence_provider` optional/keyword-only/
  observe-only; `resolve` vor `update_trade_close` (PnLUnavailable lässt Trade OPEN/retry-bar). **+14 Tests** (118 gesamt).
  Sibling-Suiten grün + unberührt (P2 59 · P4 88 · P5 135 · P6 70). **Erste P5-Berührung erst in Step 10.**
- Konzept: `docs/concepts/phase7_reward_concept.md` (voller Claude-Code-Plan, Step 0–13).

**Phase 6 status:** ✅ Code-complete + live-**verifiziert** (Debatte-Pfad), **noch nicht
profit-validiert** (2026-06-16)
- ⚠ **Live-verifiziert ≠ profit-validiert** (gleiche Disziplin wie Phase 4/5): der Live-Lauf
  (`phase6_debate/scripts/live_test.py` gegen IG Demo) bewies den **ganzen** Pfad end-to-end —
  `build_executor` → injizierter `debate_runner` → **3 echte** Bull/Bear/Judge-Calls →
  fail-closed **ABSTAIN** → `NO_TRADE` → `debate_log.json` angehängt (Modul-7-Audit auch live).
  **Unbekannt** bleibt die Profitabilität: nur **ein** Zyklus, ein ABSTAIN, **keine** echte
  Order durch die Debatte (der Order-/Monitor-Pfad selbst ist in Phase 5 bereits live bewiesen).
  Edge/Outcome-Anchoring ist Phase 7.
- **Cache-Assertion-Reconciliation (Code = Source of Truth):** Der erste Live-Lauf war
  `RESULT 3/4` — einziger Fail = die `cache_reads > 0`-Assertion in `live_test.py`, ein
  **bestätigtes False-Negative**. Haiku 4.5 cacht erst ab 4096-Token-Präfix → Bull/Bear (~850–
  1040 Input-Tokens) cachen **nie**; nur der Judge (Sonnet, 2048-Floor) **schreibt** Cache. Ein
  Cache-**Read** braucht denselben Präfix ≥2× → entsteht nur in **Mehr-Runden**-Debatten; ein
  1-Runden-Early-Stop liest nichts neu. **Fix (dieser Step):** `cache_creation > 0` **immer**
  fordern (beweist den `cache_control`-Marker), `cache_read > 0` **nur bei `rounds_used >= 2`** —
  sonst false-FAILt ein sauberer 1-Runden-ABSTAIN. Caching-ROI/Modell-Split ist P7-Tuning.
- **Deferred (P5-Scope, bewusst nicht in diesem Step):** ein `--reasoning`-Override für
  `seed_candidate.py`, um die Debatte zu einem TRADE statt ABSTAIN zu treiben. Grund: (a) ob
  Trades *profitabel* sind, ist **nicht** Scope dieses Tests, und (b) die Logik, *ob* ein Trade
  ausführbar ist, ist bereits live-bewiesen (Phase-5-Order-/Monitor-Pfad).
- **Erster Mehr-Agenten-AI-Pfad + teuerster Pfad im System** → Kostenkorrektheit (Caching +
  Metering + Caps) wiegt so schwer wie Funktionsumfang.
- **AI-Grenze (Kernprinzip):** AI macht **nur** Bull/Bear-Argumente + Judge-Synthese. Kontextaufbau,
  Budget/Caps, Persistenz, Fehlerbehandlung sind deterministischer Code. Die Debatte bekommt
  **niemals** den Broker oder eine VETO-/Gate-Funktion — sie *kann* keinen VETO umgehen, weil sie
  ihn nicht referenziert.
- **Richtungsquelle:** Der Judge emittiert die finale `direction`, die vom P4-Seed **abweichen darf**
  (Flip BUY↔SELL, Decision B). Judge-`decision ∈ {TRADE, ABSTAIN}` qualitativ; `confidence` ist
  **advisory und gatet NICHTS** (Decision H). Jeder Fehler/Cap-Breach → fail-closed **ABSTAIN →
  NO_TRADE**, nie „trotzdem traden" (Decision J).
- **Naht:** `debate_runner` zwischen Gate 2 und Gate 3 in `executor.run()`; **Default-Passthrough
  hält Phase 5 AI-frei** (Step 9). Neues Paket `phase6_debate/` (gespiegelt an `phase4_research/`);
  Cross-Phase-Reuse von `research.LLMClient`/`token_meter`/Pricing ist die **dokumentierte Ausnahme**
  (Decision F). DB bleibt read-only (P7) → nur `data/state/debate_log.json` (gitignored, P9-kompatibel).

**Phase 5 status:** ✅ Code-complete + live-**verifiziert** (Order-/Monitor-Pfad), **noch
nicht profit-validiert** (2026-06-12)
- ⚠ **Live-verifiziert ≠ profit-validiert** (gleiche Disziplin wie Phase 4): der Pfad
  *platziert und schließt korrekt* — `phase5_execution/scripts/live_test.py` (SELL-Seed,
  im Fenster) platzierte eine **echte** IG-Demo-Order (ACCEPTED, `deal_id=DIAAAAXQ6CSGTA5`)
  und schloss sie per Time-Stop → `RESULT: 4/4 passed`. Damit ist der ganze Pfad end-to-end
  live bewiesen (Gates → Sizing → 4 VETOs → place → monitor → close), **nicht** nur in CI.
  **Unbekannt** bleibt die Profitabilität (nur **ein** Trade, kein Edge gemessen) —
  Outcome-Anchoring ist Phase 7 + Live-Betrieb.
- **KEINE AI in Phase 5** (Kernprinzip): Gates, VETOs, Sizing, Order, Monitoring, Reconcile
  sind deterministischer Code. Die einzige AI bleibt der eine Phase-4-Research-Call (lazy
  über Gate 2). VETOs sind HART (kein Trade); Datenfehler/zu wenige Bars → fail-closed.
- 130 Unit-Tests grün (gemockt, kein Netzwerk, keine echte Order; `pytest phase5_execution/
  tests`). Bestehende Suites unberührt (P1 49 · P2 59 · P3 70 · P4 88).
- Code in `phase5_execution/execution/` (Paket `execution`, editable-install Composition Root —
  kein `sys.path`-Hack) · Konzept in `docs/concepts/phase5_concept.md` · CLI `python -m
  execution.ig_bot` · Operator-Live-Gate via `scripts/seed_candidate.py` → `smoke_test.py` →
  `live_test.py` (Demo only, manueller Trigger, **kein** Scheduler = Phase 8).
- Erkenntnisse (Code = Source of Truth, Konzept §4/§6 annotiert): (1) Position-Sizing auf
  **Risk-per-Trade ÷ Stop-Distanz** umgestellt (statt notional ÷ Preis) → ein ~€1 K-Budget
  liefert eine handelbare Size ≥ `min_deal_size`. (2) IG verlangt am `POST /positions/otc`
  ein nicht-null **`currencyCode`** → `OrderPlan` trägt jetzt `currency` (aus `get_market_info`,
  Fallback `EUR`). v1-Tuning-Parameter (`risk_pct` 2.0/3.0, `stop=30`/`limit=45`,
  `momentum_threshold=0.15`, `max_leverage=20`) bleiben am Profit zu tunen (Phase 7).

**Phase 4 status:** ✅ Code-complete + live-**getestet** (Pipeline-Logik), **noch
nicht profit-validiert** (2026-06-09)
- ⚠ **Live-getestet ≠ profit-validiert:** Die Pipeline läuft nachweislich korrekt
  end-to-end (IG Demo + echter LLM-Call) — korrekter Kontext, contract-valider Pick
  **oder** sauberer Abstain, sicherer No-Trade auf **jedem** Fehlerpfad (zuletzt
  bestätigt: Markt-geschlossen-Abstain um 07:18, `exit 0`). **Unbekannt** bleibt, ob
  der Bot *profitable* Trades macht — es wurden **keine echten Trades platziert oder
  ausgewertet**. Das ist hier bewusst so: Ausführung = Phase 5, Edge/Profitabilität =
  viel später (Phase 7 Outcome-Anchoring + Live-Betrieb). Grünes Licht heißt „die
  Logik funktioniert", **nicht** „der Bot ist profitabel".
- 88 Unit-Tests grün (gemockt, `_raw_call` der einzige mockbare LLM-Punkt — kein
  Netzwerk, kein `anthropic`-Import im Unit-Run; `test_validator.py` 18 ≥ 12) +
  live-getestet via `phase4_research/scripts/live_test.py` → `RESULT: 3/3 passed`
  gegen IG Demo + realen LLM-Call (run() ohne Exception, 1-Save-Invariante,
  Abstain → leere Liste). `smoke_test.py` als DRY-Sanity vorgeschaltet.
- **Einziger AI-Schritt** = `llm_client.ask_candidate` ("welcher Kandidat?"). Alles
  andere ist Code: Context-Assembly (P1/P2/P3), Validator (Halluzinations-Guard),
  `candidate_filter` (das reale Gate), Persistenz, Retry. LLM-Output erreicht **nie**
  `open_position` ohne Validator + Filter; LLM-`confidence` ist Rohdatum, **nicht** das
  Gate (Phase 7 ankert es an Outcomes).
- Code in `phase4_research/` (importiert nichts aus Phase 1/2/3 zur Laufzeit — nur
  via `scripts/wiring.py`-Bootstrap; Phasen-Isolation) · Konzept in
  `docs/concepts/phase4_research_plan_konzept.md` · Candidate-Persistenz in
  gitignored Root-`data/state/turbo_candidates.json` (Legacy-Name, TTL 30 min);
  Token-/Kosten-Log in `data/state/llm_usage.json` (gitignored).
- Erkenntnis (Code = Source of Truth, Konzept §4 annotiert): **Anthropic Structured
  Outputs lehnen JSON-Schema-Type-Arrays ab** (`{"type": ["string","null"]}` → HTTP
  400) — der Code nutzt `anyOf` für nullable Enums; numerische Constraints
  (`minimum`/`maximum`) sind ebenfalls nicht unterstützt → der `confidence`-Bereich
  wird vom Validator durchgesetzt. Baseline-Tag vor dem Fix: `phase4-pre-schema-fix`.

**Phase 3 status:** ✅ Abgeschlossen + live-verifiziert (2026-06-02)
- 70 Unit-Tests grün (gemockt, `_raw_download` monkeypatched — kein Netzwerk) +
  live-verifiziert via `phase3_external_data/scripts/live_test.py --clear-cache`
  → `RESULT: 6/6 passed` gegen reales yFinance `^GDAXI` (Konnektivität, Daily-
  Indikatoren, Markt-Regime-Verzweigung, Cache-Hit, Rate-Limiter-Abstand,
  `get_brain_context`-Toleranz). ETF-Volume-Proxy-Pfad via `--volume-proxy EXS1.DE`
  bestätigt (`volume_available=True`, `volume_source=EXS1.DE`, `today_volume>0`).
- 100 % Code, **kein LLM-Call** (Bauprinzip). yFinance liefert Rohwerte, Code rechnet
  Drift/Momentum/Volume-z/HighLow. Einziger Netzwerk-Punkt: `fetcher._raw_download`.
- Code in `phase3_external_data/` (importiert nichts aus Phase 1/2 — Phasen-Isolation)
  · Plan/Konzept in `docs/concepts/phase3_external_data_konzept.md`
- Runtime-Cache in gitignored Root-`data/cache/*.json` (TTL: 1d bis Mitternacht
  Europe/Berlin · 5m 120 s · 30m 300 s)
- ⚠ **Phase-5-Flag:** `get_momentum()` ist ~15 min verzögert (yFinance Delayed Quote) —
  ein **Kontext-Signal**, KEIN harter Momentum-VETO. Der VETO gehört in Phase 5 an
  Phase-1/IG-Echtzeit-Bars (siehe `phase3_external_data/CLAUDE.md` + Konzept §13).
- Erkenntnisse (Code = Source of Truth, Konzept entsprechend annotiert): `get_bars`
  ist `list[PriceBar] | None` (Off-Hours-Disziplin, §11); der Live-Rate-Limiter-Check
  provisioniert sich einen frischen Temp-Cache statt `--clear-cache` zu brauchen (§17.2)

**Phase 2 status:** ✅ Abgeschlossen + live-verifiziert (2026-05-22)
- 59 Unit-Tests grün (gemockt) + live-verifiziert via `phase2_persistence/scripts/live_test.py`
  (Durability über Prozess-Neustart, Candidates-TTL-Selbstlöschung, Phase-1→Phase-2
  Integration gegen IG Demo)
- Code in `phase2_persistence/` · Konzept in `docs/concepts/phase2_persistence_konzept.md`
- Runtime-Daten in gitignored Root-`data/` (`trading_bot.sqlite` + `state/*.json`),
  angelegt via `scripts/init_db.py`
- Erkenntnis (Code = Source of Truth): `get_open_positions().data` ist ein Dict
  `{"positions": [...]}`, keine blanke Liste — Konzept-Beispiel entsprechend korrigiert

**Phase 1 status:** ✅ Abgeschlossen
- Live-verifiziert gegen IG Demo · smoke_test PASS inkl. `--order`
- Confirmed epic: `IX.D.DAX.IFMM.IP` — Deutschland 40-Kassa (1 €/Punkt), EUR, min_deal_size: 0.5
- Code in `phase1_broker_wrapper/` · Konzept in `docs/concepts/phase1_broker_api_konzept.md`
- Lightstreamer client live-getestet gegen IG Demo (offizielles `lightstreamer-client-lib`
  SDK, `PRICE`-Feed) — CONOK/SUBOK + Live-Ticks bestätigt am 2026-05-21; Polling-Client
  bleibt als Fallback → Notes: `phase1_broker_wrapper/lightstreamer_integration_notes.md`
- IG Europe GmbH Live-Account noch ausstehend (vor Production-Go-Live kritisch)

---

## File organization (where things go)

```
~/trading-bot/                              ← root
├── README.md                               ← human-facing overview
├── CLAUDE.md                               ← this file
├── ARCHITECTURE.md                         ← architecture summary + links
├── ROADMAP.md                              ← Phase 1–9 plan
├── .gitignore
│
├── docs/
│   ├── concepts/                           ← Phase-N concept docs
│   │   ├── phase1_broker_api_konzept.md
│   │   ├── phase2_persistence_konzept.md
│   │   └── phase3_external_data_konzept.md
│   ├── architecture/
│   │   ├── tradingbot_v2_architecture.svg
│   │   └── tradingbot_v2_architecture.pdf
│   └── sessions/                           ← (optional) chat session summaries
│
├── data/                                   ← runtime SQLite + JSON state (gitignored)
├── phase1_broker_wrapper/                  ← Phase 1 code ✅
├── phase2_persistence/                     ← Phase 2 code ✅
├── phase3_external_data/                   ← Phase 3 code ✅
└── ...
```

**Rule:** Each phase is a self-contained directory with its own `README.md`,
`requirements.txt`, and optionally its own `CLAUDE.md`. Cross-phase imports
happen only via well-defined contracts (e.g. Envelope JSON for broker_wrapper).

---

## Conventions

**Python:**
- Type hints everywhere (`from __future__ import annotations`)
- Docstrings on every public function/class (purpose, args, raises)
- `pytest` for tests, mock HTTP — no network calls in unit tests
- `requests` for HTTP, NOT `urllib` or `httpx` (consistency)
- One file = one responsibility (do not bloat modules)

**Errors:**
- Custom typed exception hierarchy in `exceptions.py`
- Never swallow exceptions silently — log + raise or log + return error envelope
- HTTP errors map to envelope error codes (see existing IGAdapter for pattern)

**Logging:**
- Use the standard `logging` module
- Logs go to stderr, never stdout (stdout is reserved for envelope JSON)
- DEBUG for internals, INFO for milestones, WARNING/ERROR for problems

**Git:**
- Atomic commits — one logical change per commit
- Commit message format: `<scope>: <imperative>` e.g. `broker_wrapper: fix epic search timeout`
- Never commit credentials. Never commit `.venv/`. Never commit `__pycache__/`.

---

## How to work in this repo

**Starting a session:**

1. Confirm which phase is active (check "Current state" above)
2. Read the relevant phase README (e.g. `phase1_broker_wrapper/README.md`)
3. Check `git status` and `git log -5` to understand recent work
4. Run existing tests before making changes (`pytest tests/ -v`)
5. If a `## Session stopped` block exists in the active phase's `CLAUDE.md` or
   relevant notes file — read it first. It records exactly where the previous
   session ended and what comes next.

**During a session:**

- After every subtask: run `pytest tests/ -v` before moving on.
  A subtask is not done until its tests are green.
- Write tests in the phase's `tests/` directory for every new function
  (mocked HTTP, no live network calls in unit tests).
- If any architectural decision changes, update the relevant concept doc in
  `docs/concepts/` immediately — not at the end of the session.

**Ending a session (mandatory):**

Before closing, append a `## Session stopped` block to the active phase's
`CLAUDE.md` (or the task's notes file if one exists, e.g.
`lightstreamer_integration_notes.md`). This is the handover to the next session.
Without it, context is lost and the next session starts cold.

```markdown
## Session stopped — <YYYY-MM-DD>

### Completed
- `<file>`: <what was done>

### Next
- <exact next step, specific enough to start without re-reading everything>

### Open questions / blockers
- <anything unresolved>
```

Replace or update this block at the start of each new session once read.

**When in doubt about scope or AI vs. code: default to code.**
The "AI as little as possible" principle resolves most ambiguity.

---

## Phase transitions

A phase is considered "done" when:
- All planned components exist
- Smoke test passes against the relevant environment (demo or local)
- Phase README documents what was built, known limitations, and integration points
- The next phase's concept document is ready in `docs/concepts/`

Phase transitions happen in the **Claude browser interface** (Konzept-Session),
not in Claude Code. Claude Code implements; Claude (browser) plans.

---

## Anti-patterns to flag

If you see any of these, stop and discuss with the human:

- LLM call inside a Gate, VETO, or sizing calculation
- Credentials in any file other than the keyring
- An AI output triggering an order without code-side validation
- A "temporary" hardcoded value that bypasses a check
- A test that hits the live (non-demo) IG account
- Force Trigger usage without checking Daily PNL
- Any direct broker call outside `broker_wrapper/` (always go through the wrapper)
- A subtask marked done without passing `pytest tests/ -v`
- A session ending without a `## Session stopped` block written
