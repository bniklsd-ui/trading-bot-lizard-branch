# Roadmap

The build order is **strict**. Each phase depends on the previous one being
testable and stable. No skipping ahead.

> Rule: Each phase must be fully testable before the next begins.
> After Phase 1: manual trades work. After Phase 5: first automated trade.
> After Phase 7: bot learns. Everything after that is optimization.

> ⚠ **Doc-reconciliation 2026-06-30:** Eine frühere Drive-Version dieser Datei war
> inkonsistent (Phasen 1/3/4 auf altem „ungetestet/to-be-created"-Stand zurückgefallen,
> obwohl längst ✅ live-verifiziert). Diese Fassung führt die Phasen 1–7 wieder korrekt
> und ergänzt Phase 8 (halber Abschluss) + Phase 9 (9f Instinct-ECC).

---

## Phase 1 — Broker API Wrapper ✅ Abgeschlossen (live-verifiziert, Demo)

**Goal:** A unified Python interface that talks to any supported broker
and emits standard envelopes. Live-tested against IG Demo.

- [x] Concept document
- [x] `broker_wrapper/` module with adapter ABC + IG REST implementation
- [x] Envelope JSON contract
- [x] Credentials via OS keyring
- [x] CLI for standalone testing
- [x] Polling stream client (fallback)
- [x] **Smoke test against live IG Demo account** (PASS inkl. `--order`)
- [x] Lightstreamer streaming client (offizielles SDK, `PRICE`-Feed, CONOK/SUBOK + Live-Ticks 2026-05-21)
- [x] Verify trade-history parsing *(Phase 7 P&L-Resolver: in der Praxis gepivotet — IG-Demo bucht
  History erst nach Settlement, daher ist die **Close-Deal-Confirmation** die primäre lag-freie
  P&L-Quelle; `get_trade_history` bleibt heuristischer Fallback)*

**Done when:** `python scripts/smoke_test.py --order` succeeds end-to-end
against the demo account. ✅ — 2026-05-21. Confirmed epic
`IX.D.DAX.IFMM.IP` (Deutschland 40 Kassa, 1 €/Punkt, EUR, min_deal_size 0.5).

> ⚠ IG Europe GmbH Live-Account noch ausstehend (vor Production-Go-Live kritisch).

**Directory:** [`phase1_broker_wrapper/`](./phase1_broker_wrapper/)
**Concept:** [`docs/concepts/phase1_broker_api_konzept.md`](./docs/concepts/phase1_broker_api_konzept.md)

---

## Phase 2 — Persistenz (SQLite + JSON) ✅ Abgeschlossen (live-verifiziert)

**Goal:** Data layer for the rest of the bot. No business logic, just storage.

- [x] SQLite schema: `trade_lessons`, `trade_outcomes`, `reward_pts`, `ig_config_state`
  (+ V2 `market_regime_snapshots`, `decision_context` as empty placeholders)
- [x] JSON state files: `ig_state.json`, `ig_config.json`, `turbo_candidates.json`
- [x] TTL handling for `turbo_candidates.json` (30 min)
- [x] Migrations / schema versioning (`001_initial.sql`)
- [x] Reader/writer abstractions (`db.py`, `state.py`)

**Done when:** All schemas exist, can read/write/migrate. ✅ 59 unit tests green +
live-verified via `scripts/live_test.py` (durability, TTL, Phase-1 integration) — 2026-05-22.

> Note: Die Prozess-Spalten in `reward_pts` existieren bereits → Phase 7 braucht für
> prozess-bewusstes Scoring **keine** Migration; nur `initial_risk`/`r_multiple`/`account`
> kommen additiv in `002` dazu.

**Directory:** [`phase2_persistence/`](./phase2_persistence/)
**Concept:** [`docs/concepts/phase2_persistence_konzept.md`](./docs/concepts/phase2_persistence_konzept.md)

---

## Phase 3 — External Data (yFinance) ✅ Abgeschlossen (live-verifiziert)

**Goal:** Market data outside the broker (drift, long-term history, brain context). Pure code, no AI.

- [x] yFinance wrapper (rate-limited, cached)
- [x] 30-day price history retrieval
- [x] High/low distance calculation
- [x] Volume anomaly detection (z-score; ETF-Proxy `EXS1.DE`, da `^GDAXI` kein Volume hat)
- [x] Drift calculation (`today_open vs. now %`)
- [x] Momentum (Kontext-Signal) + `get_brain_context` + `TickerMapper` (IG-Epic → yFinance-Symbol)

**Done when:** Given any DAX-related ticker, can return drift, history, and anomaly flags reliably.
✅ 70 unit tests green + live-verified (`RESULT: 6/6 passed` gegen reales `^GDAXI`) — 2026-06-02.

> ⚠ **Phase-5/7-Flag:** `get_momentum()` ist ~15 min verzögert — ein **Kontext-Signal**, KEIN
> harter Momentum-VETO (der sitzt in Phase 5 an IG-Echtzeit-Bars `get_ohlcv`).

**Directory:** [`phase3_external_data/`](./phase3_external_data/)
**Concept:** [`docs/concepts/phase3_external_data_konzept.md`](./docs/concepts/phase3_external_data_konzept.md)

---

## Phase 4 — research.py + LLM Kandidaten ✅ Abgeschlossen (live-getestet)

> Legacy-Benennung: das Modul hieß im Konzept-Erbe `turbo_research.py`; es heißt jetzt
> `research.py` (Klasse `Research`). Output-Datei `turbo_candidates.json` behält ihren
> **Legacy-Namen** (Phase-2/Phase-5-Gate-2-Contract). DAX-**CFDs**, keine Optionen/Turbos.

**Goal:** LLM picks one candidate per session based on code-prepared data. AI's first appearance.

- [x] Session health check
- [x] LLM pick underlyings (drift, last 8 trades, brain lessons, score)
- [x] Probe epics by allowlist (uses broker_wrapper)
- [x] Candidate filter (CFD-Filter: Spread, Drift-Eignung, Score-Coupling; confidence-Floor)
- [x] Save to `turbo_candidates.json`
- [x] Code-side validation of LLM output (`validator.py` = Halluzinations-Guard)

**Done when:** Running `research.py` produces a valid `turbo_candidates.json`. ✅ 88 unit tests
green + live-getestet (`RESULT: 3/3 passed`, IG Demo + realer LLM-Call) — 2026-06-09.

> ⚠ Live-getestet ≠ profit-validiert. Pipeline-**Logik** läuft korrekt end-to-end; keine echten
> Trades platziert/ausgewertet.
> ℹ **v1.5-Relevanz:** `epic_allowlist` (Default 1 Epic) + der Sub-50-Doppel-Clamp
> (long-bias + Confidence-Floor) sind die Hauptursachen für den Near-Constant-Abstain →
> siehe `phase8_scheduler/PHASE8_V1.5_HOTFIX_HANDOVER.md`.

**Directory:** [`phase4_research/`](./phase4_research/)
**Concept:** [`docs/concepts/phase4_research_plan_konzept.md`](./docs/concepts/phase4_research_plan_konzept.md)

---

## Phase 5 — ig_bot.py Gates 1–5 + pre_trade ✅ Abgeschlossen (live-verifiziert)

**Goal:** First end-to-end execution path. Manual trigger only, no scheduler yet.

- [x] Gate 1: Time Window check (09:30–11:19 CET)
- [x] Gate 2: Load Candidates (lazy-calls Phase 4 if missing)
- [x] Gate 3: Constraints (budget, concurrent positions)
- [x] Gate 4: Broker sizing (**risk-per-trade ÷ stop-distance**)
- [x] Gate 5: Direction Consistency (`gate_direction_consistency` — pass-through, no FLIP)
- [x] `pre_trade_check()` — 4 VETOs (status/window, spread, momentum via `get_ohlcv` IG-Echtzeit, position conflict)
- [x] Place order via broker_wrapper (write-ahead `deal_reference`, PENDING fail-closed)
- [x] Monitor position (polling, time-stop close) + Close + Startup reconcile

**Done when:** Manually triggering `ig_bot.py` against IG Demo opens and closes a trade through all
gates. ✅ live-verified (`live_test.py`: echte SELL-Order → time-stop-close, `RESULT: 4/4 passed`)
— 2026-06-12. ⚠ Live-verified ≠ profit-validated (edge ist Phase 7 + Live-Betrieb).

> ℹ Test-Count nach P6+P7: **146** grüne P5-Unit-Tests (P7-Abschluss 2026-06-26:
> P1 52 · P2 62 · P4 94 · P5 146 · P6 70 · P7 128). **Die 4 VETOs (`execution/vetos.py`) sind
> unantastbar — kein v1.5-Knob darf sie berühren.**

**Directory:** [`phase5_execution/`](./phase5_execution/)
**Concept:** [`docs/concepts/phase5_concept.md`](./docs/concepts/phase5_concept.md)

---

## Phase 6 — Bull/Bear/Judge Debate ✅ Abgeschlossen (live-verifiziert)

**Goal:** Replace the simple direction decision with an adversarial early-stop debate.

> **AI boundary:** AI is used **only** for Bull/Bear arguments + Judge synthesis. Context assembly,
> budget/caps, persistence, fail-closed handling are deterministic code. The debate **never** sees
> the broker or any VETO/Gate function.

- [x] Bull/Bear = **Haiku 4.5** (`claude-haiku-4-5-20251001`), Judge = **Sonnet 4.6** (`claude-sonnet-4-6`), config-overridable
- [x] Early-stop (`max_rounds=5`) + hard caps (calls / cumulative tokens / wall-clock) → any breach → **ABSTAIN**
- [x] Judge is the **direction source** — may flip the Phase-4 seed BUY↔SELL; `decision ∈ {TRADE, ABSTAIN}`; `confidence` advisory, gates nothing
- [x] Caching + extended 8-field token-meter
- [x] Forward-compatible JSON audit `debate_log.json`
- [x] Seam: `debate_runner` injected **between Gate 2 and Gate 3**; default passthrough keeps Phase 5 AI-free

**Done when:** Debate runs reliably; every error/cap-breach → fail-closed ABSTAIN → NO_TRADE.
✅ Done + live-verified 2026-06-16 (`main = 49cda8a`; one Demo cycle: 3 real calls → ABSTAIN → NO_TRADE).
⚠ Live-verified ≠ profit-validated.

> **Caching-Realität:** Haiku cacht erst ab 4096-Token-Präfix → Bull/Bear (~850–1040 Tokens) cachen
> nie; nur der Judge schreibt Cache; Cache-Reads nur bei `rounds_used >= 2`.
> ℹ **v1.5-Relevanz:** Die Debatte ist der **bereits gebaute Differentiator** — sie kann die
> Richtung flippen, läuft aber nur auf einem *erzeugten* Kandidaten. Loosening des P4-Gates lässt
> die Debatte die nuancierte Arbeit tun (v1.5 Block B).

**Directory:** [`phase6_debate/`](./phase6_debate/)
**Concept:** [`docs/concepts/phase6_debate_concept.md`](./docs/concepts/phase6_debate_concept.md)

---

## Phase 7 — Reward/Brain ✅ Abgeschlossen + live-verifiziert (2026-06-26, gepusht)

> **Scope-Lock (lean model):** Phase 7 = **Reward-Score** (`reward_pts`, prozess-bewusst) +
> **free-text Lessons** (`trade_lessons`) + **observe-only outcome-anchored Confidence**.
> **Keine VETO-Berührung.** Die volle **Instinct→VETO-Promotion (ECC)** ist **Phase 9f**, gegatet
> auf reale Outcomes.

**Goal:** Der Feedback-Loop schließt — aus realen Trade-Ergebnissen werden Score + Lessons, die in
spätere Research-Zyklen zurückfließen.

- [x] `RewardSink` write-seam (`on_trade_opened`/`on_trade_closed`), default `None` → Phase 5 bit-identisch
- [x] Prozess-bewusster Reward-Score (`reward_pts`: outcome + process Δ, clamped [0,100], per-trade `|Δ|` capped) → `score_after`
- [x] Score → risk_level unverändert (binäres `get_risk_level`, Schwelle 50)
- [x] Outcome-anchored Confidence `f(Wilson-LB(win_rate), expectancy_R, SQN, N)`, `N_min=10` → INSUFFICIENT; **observe-only, gatet nichts**
- [x] `reflect()` nach jedem Close — ein Haiku-Call, best-effort, vom Close-Critical-Path entkoppelt → `trade_lessons`
- [x] Lessons-Loop-Closure: Research-Prompt injiziert `get_recent_lessons`; `mark_lesson_used`
- [x] **P&L-Pivot:** realisierter P&L + `close_level` reisen **lag-frei aus der Close-Confirmation** mit; `get_trade_history` nur Fallback. Migration `002` = `initial_risk`/`r_multiple`/`account`
- [x] Synthetik/Echt-Trennung (harte DB-Pfad-Grenze + `SyntheticSafetyError`); `include_demo_in_edge=True` (Bootstrap, vor Go-Live re-baselinen)

**Done when:** `pytest phase7_reward/tests/` grün. ✅ **128 P7-Unit-Tests**; Regression
**P1 52 · P2 62 · P4 94 · P5 146 · P6 70** grün; `live_test.py` **5/5** gegen IG Demo. ⚠
live-verifiziert ≠ profit-validiert (erst **ein** Trade; Edge-Metrik läuft bei `score=50`/`INSUFFICIENT`).

> ℹ **v1.5-Relevanz:** Die bisherigen Lessons stammen aus **Verifikations-Trades** und fließen
> ungefiltert in den Research-Prompt → v1.5 Block A (Lesson-Provenance-Quarantäne).

**Directory:** `phase7_reward/` *(package `reward`)*
**Concept:** [`docs/concepts/phase7_reward_concept.md`](./docs/concepts/phase7_reward_concept.md) · **Kickoff:** [`PHASE7_KICKOFF_HANDOVER.md`](./PHASE7_KICKOFF_HANDOVER.md)

---

## Phase 8 — Scheduler 🟡 code-complete + merged; v1.5-Hotfix merged 2026-07-02 — autonomer Trade NOCH NICHT live-bewiesen (→ v1.6)

> **Mission (zuerst lesen):** „Scheduler" ist nur der Name — das Ziel ist **autonome,
> unbeaufsichtigte Erzeugung realer Demo-Trades**, weil alles nach P8 (Confidence aus
> `INSUFFICIENT`, P9-Instinct-Promotion) auf **reale Outcomes** gegatet ist. Der harte Pfad ist
> **autonome Kandidaten-Generierung** via echtes Phase-4-Research (nie der manuelle Seed).
> **Kein neues AI** — ein Scheduler ist reine Mechanik; AI bleibt bei P4-Pick / P6-Debatte /
> P7-Lesson. Build-Reihenfolge bindend: **Cleanup → Verify → autonome Kandidaten →
> Auto-Confirm/Safety → Reconcile → Loop/Daemon → (zuletzt) Web-UI**; unter Druck fällt die UI,
> nie die Safety.

**Goal:** Ein langlaufender Daemon, der aufwacht, recherchiert, im Fenster tradet, reconcilet und
schläft — und so die ersten realen Outcome-Daten sammelt.

- [x] Pre-Steps: Step 0 (Legacy-grep — clean), Step 0b (Docs), Step 1 (Contract-Verify), Step 2 (Scaffold `phase8_scheduler/`, pkg `scheduler`)
- [x] `clock.py` — Marktzeiten-Phasen (reuse `is_market_open` + Gate-1-Fenster), injizierbares `now_fn`/`sleep_fn`
- [x] `state.py` — `scheduler_state.json` (Trade-Count, Tages-Loss, Backoff, Kill-Reason), Europe/Berlin-Rollover
- [x] `safety.py` — Auto-Confirm `confirm_fn` (demo-only fail-closed + Caps + Loss-Breaker + Budget)
- [x] `killswitch.py` — file-based KILL (UI-unabhängig); `command.py` — UI-/P10-Command-Pfad; `backoff.py` — Consecutive-Failure-Trip; `budget.py` — Token-Budget (default scharf, 200k ≈ €0.8/Tag)
- [x] `research_tick.py` — autonome Kandidaten (echtes P4-Research, nie der Seed; `no_trade_reason`-Skelett)
- [x] `reconcile.py` — idempotenter `CLOSED_BY_BROKER`-P&L-Catch-up
- [x] `runner.py` — die Loop/Daemon + fail-closed Keyring-Preflight + graceful shutdown
- [x] `scripts/` — wiring (voller P1–P7-Stack), `run.py` entry, `run_scheduler.sh`, smoke_test, live_test
- [x] Web-UI (`webui/`, FastAPI read-mostly + statisches Dashboard) — **zuletzt gebaut**

**Status (ehrlich):** Alle 12 Module gebaut, **181 Unit-Tests grün**, gemergt nach `main`
(2026-06-30). ✅ **Bewiesen** (Operator-Run 2026-06-29 + Mocks): Daemon-Lifecycle (preflight →
bounded loop → clean shutdown), State-Persistenz, autonomes **echtes** P4-Research mit korrektem
Fail-Safe-Abstain, reconcile+reward auf **2 realen Demo-Trades**, scharfes Token-Budget,
read-only Web-UI. ⚠ **NICHT bewiesen** (mit ehrlichem Flag gemergt): ein **net-new autonomer
Trade** open *und* close in einem sauberen Lauf; **real auslösende** Safety-Breaker; Multi-Day;
Edge/Profitabilität (nie im Scope).

**Why the gap + nächster Track:** der Bot **abstaint** fast jeden Zyklus (Single-Instrument-Universum
+ Sub-50-Doppel-Clamp). Track = **v1.5-Hotfix** (Varietät C + Clamp/Floor B + echte Lessons A) —
siehe [`phase8_scheduler/PHASE8_V1.5_HOTFIX_HANDOVER.md`](./phase8_scheduler/PHASE8_V1.5_HOTFIX_HANDOVER.md)
(+ Planner-Companion `PHASE8_V1.5_KICKOFF_HANDOVER.md`). Das ursprüngliche „Done when" (live net-new
autonomer open→close + demonstrierbarer Breaker-Trip) ist **in v1.5 übernommen**, hier nicht behauptet.

> **⚠ v1.5-Stand (gemergt 2026-07-02, ehrlich):** die drei Code-Fixes A/B/C sind fertig + mockgrün
> (P1 52 · P2 67 · P3 72 · P4 122 · P5 154 · P6 70 · P7 131 · P8 182). Aber der erste **Live-Lauf**
> (2026-07-02) deckte einen **yFinance-Blocker** auf: CAC 40 (`^FCHI`) und IBEX 35 (`^IBEX`) — die im
> Step-2-Variety-Track **nie live-verifizierten** Ticker — liefern keine Kursdaten (*„possibly
> delisted; no price data"*) → deren P3-Brain-Context degradiert zu `None` (2 von 4 Instrumenten
> reduced-signal). **Kein Hard-Crash** (Fallback auf letzten Daily-Close), **kein VETO betroffen**
> (Momentum-VETO nutzt IG-Echtzeit-Bars, nicht yFinance), **nicht** der v1.5-Provenance-Code. Der
> **net-new autonome open→close** bleibt damit **unbewiesen**. Es fehlt außerdem **echtes Logging**.
> → Nächster Track = **v1.6** (erst Observability, dann `^FCHI`/`^IBEX` verifizieren/fixen **oder**
> droppen, dann der Live-Beweis): siehe
> [`phase8_scheduler/PHASE8_V1.6_HANDOVER.md`](./phase8_scheduler/PHASE8_V1.6_HANDOVER.md).

**Directory:** [`phase8_scheduler/`](./phase8_scheduler/) *(pkg `scheduler` + `webui`)*
**Concept:** [`docs/concepts/phase8_scheduler_concept.md`](./docs/concepts/phase8_scheduler_concept.md)

---

## Phase 9 — V2 Erweiterungen

**Goal:** Implement the V2 improvements identified in the Council analysis.

### 9a — Council Skill Integration
- [ ] Integrate `verbesserungsvorschlaege` as structured input to pipeline
- [ ] Trigger detection for ad-hoc strategy evaluation

### 9b — Handover-Logik (Bull/Bear/Judge)
- [ ] Context-window monitoring during debate (~60–70 %)
- [ ] Compression of Bull/Bear/Judge state into summary
- [ ] New session continuation

### 9c — SQLite V2 Extensions
- [ ] `+ market_regime_snapshots` (volatility, spread, time per trade)
- [ ] `+ decision_context` (Bull/Bear args, VETO factors, confidence curve)
- [ ] `+ lesson_embeddings` (vector store, semantic similarity) — optional/later

### 9d — Reward/Punishment Reform
- [ ] `+ process_quality_score` (VETOs, confidence, debate quality, gate path)
- [ ] Anti-emotionality: separate process score from outcome score

### 9e — Force Trigger Safeguard
- [ ] Lock force trigger when daily PNL < 0

### 9f — Instinct-Promotion (ECC) + Longterm VETO *(aus Phase 7 hierher verschoben)*
- [ ] AI extrahiert strukturierte Instincts (`trigger` / `domain` / `confidence` / `evidence_trade_ids`) aus P7 `trade_lessons` + `reward_pts`
- [ ] Code **validiert** Instincts gegen reale Outcomes; bewährte werden zu **deterministischen Regeln promotet** (`longterm_pre_trade_check()` VETO), mit Prune→Archiv der widerlegten
- [ ] **Harte Leitplanke:** Promotion in die VETO-Schicht **nur** über einen deterministischen / menschlich gegateten Schritt — eine promotete Regel wird deterministischer Code, die AI sitzt nie in der VETO-Auswertung. Gegatet auf reale Outcomes (≫ `n_min`)

**Done when:** All V2 changes operational, bot demonstrates improved learning signal (process-score
divergence from outcome-score on bad-market days).

**Directory:** `phase9_v2/` *(to be created)*

---

## Cross-cutting concerns (always)

- **Smoke tests** before any production change
- **No credentials in files** — keyring only
- **No AI for code-doable work** — every reach for AI must be justified
- **Atomic git commits** with clear messages; **Commit ⇒ Note-Update**
- **Phase isolation** — cross-phase imports only through defined contracts / Protocols
