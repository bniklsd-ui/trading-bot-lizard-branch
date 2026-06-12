# Roadmap

The build order is **strict**. Each phase depends on the previous one being
testable and stable. No skipping ahead.

> Rule: Each phase must be fully testable before the next begins.
> After Phase 1: manual trades work. After Phase 5: first automated trade.
> After Phase 7: bot learns. Everything after that is optimization.

---

## Phase 1 — Broker API Wrapper *(Code vorhanden, ungetestet)*

**Goal:** A unified Python interface that talks to any supported broker
and emits standard envelopes. Live-tested against IG Demo.

- [x] Concept document
- [x] `broker_wrapper/` module with adapter ABC + IG REST implementation
- [x] Envelope JSON contract
- [x] Credentials via OS keyring
- [x] CLI for standalone testing
- [x] Polling stream client (fallback)
- [ ] **Smoke test against live IG Demo account** ← next concrete step
- [ ] Fix any IG-specific quirks found in smoke test
- [ ] Verify trade-history parsing against known closed deal
- [ ] Finish Lightstreamer streaming client *(optional, can wait)*

**Done when:** `python scripts/smoke_test.py --order` succeeds end-to-end
against the demo account.

**Directory:** [`phase1_broker_wrapper/`](./phase1_broker_wrapper/)
**Concept:** [`docs/concepts/phase1_broker_api_konzept.md`](./docs/concepts/phase1_broker_api_konzept.md)

---

## Phase 2 — Persistenz (SQLite + JSON)

**Goal:** Data layer for the rest of the bot. No business logic, just storage.

- [x] SQLite schema: `trade_lessons`, `trade_outcomes`, `reward_pts`, `ig_config_state`
      (+ V2 `market_regime_snapshots`, `decision_context` as empty placeholders)
- [x] JSON state files: `ig_state.json`, `ig_config.json`, `turbo_candidates.json`
- [x] TTL handling for `turbo_candidates.json` (30 min)
- [x] Migrations / schema versioning
- [x] Reader/writer abstractions (`db.py`, `state.py`)

**Done when:** All schemas exist, can read/write/migrate. Unit tests cover
each table's CRUD operations. ✅ 59 unit tests green + live-verified via
`scripts/live_test.py` (durability, TTL, Phase-1 integration) — 2026-05-22.

**Directory:** [`phase2_persistence/`](./phase2_persistence/)
**Concept:** [`docs/concepts/phase2_persistence_konzept.md`](./docs/concepts/phase2_persistence_konzept.md)

---

## Phase 3 — External Data (yFinance)

**Goal:** Market data outside the broker (for drift calculation, long-term
history, brain context). Pure code, no AI.

- [ ] yFinance wrapper (rate-limited, cached)
- [ ] 30-day price history retrieval
- [ ] High/low distance calculation
- [ ] Volume anomaly detection (≥10% vol max)
- [ ] Drift calculation (`today_open vs. now %`)

**Done when:** Given any DAX-related ticker, can return drift, history, and
anomaly flags reliably.

**Directory:** `phase3_external_data/` *(to be created)*

---

## Phase 4 — research.py + LLM Kandidaten

> Legacy-Benennung: das Modul hieß im Konzept-Erbe `turbo_research.py`; es heißt
> jetzt `research.py` (Klasse `Research`). Die Output-Datei `turbo_candidates.json`
> behält ihren **Legacy-Namen** (Phase-2/Phase-5-Gate-2-Contract). Es geht um
> DAX-**CFDs**, keine Optionen/Turbos — kein CALL/PUT/Strike/OTM.

**Goal:** The research phase. LLM picks one candidate per session based on
code-prepared data. AI's first appearance in the pipeline.

- [ ] Session health check
- [ ] LLM pick underlyings (with drift, last 8 trades, brain lessons, score)
- [ ] Probe epics by range (uses broker_wrapper)
- [ ] Candidate filter (CFD-Filter: Spread, Drift-Eignung, Score-Coupling; confidence-Floor)
- [ ] Save to `turbo_candidates.json`
- [ ] Code-side validation of LLM output (epic exists, spread tradeable)

**Done when:** Running `research.py` produces a valid `turbo_candidates.json`
that passes downstream consumption.

**Directory:** `phase4_research/` *(to be created)*

---

## Phase 5 — ig_bot.py Gates 1–5 + pre_trade

**Goal:** First end-to-end execution path. Manual trigger only, no scheduler yet.

- [x] Gate 1: Time Window check
- [x] Gate 2: Load Candidates (calls Phase 4 if missing)
- [x] Gate 3: Constraints (budget, concurrent positions)
- [x] Gate 4: Broker sizing (risk-per-trade ÷ stop-distance)
- [x] Gate 5: Direction Consistency (`gate_direction_consistency` — pass-through check, no FLIP)
- [x] `pre_trade_check()` — 4 VETOs (status/window, spread, momentum via `get_ohlcv`, position conflict)
- [x] Place order via broker_wrapper (write-ahead `deal_reference`, PENDING fail-closed)
- [x] Monitor position (polling, time-stop close)
- [x] Close position
- [x] Startup reconcile (orphan PENDING → mark_closed)

**Done when:** Manually triggering `ig_bot.py` against IG Demo opens and
closes a trade through all gates successfully. ✅ 130 unit tests green +
live-verified via `phase5_execution/scripts/live_test.py` (real SELL order
open → time-stop-close, IG Demo, `RESULT: 4/4 passed`) — 2026-06-12.
⚠ Live-verified ≠ profit-validated (edge is Phase 7 + live running).

**Directory:** [`phase5_execution/`](./phase5_execution/)
**Concept:** [`docs/concepts/phase5_concept.md`](./docs/concepts/phase5_concept.md)

---

## Phase 6 — Bull/Bear/Judge Debate

**Goal:** Replace simple direction decision with adversarial 5-round debate.

- [ ] Bull agent (Claude Sonnet)
- [ ] Bear agent (Claude Sonnet)
- [ ] Judge agent (Claude Sonnet)
- [ ] 5-round orchestration
- [ ] VETOs on debate output (trade factor, close factor, time-to-target)
- [ ] FLIP-logic
- [ ] APPROVED → `size_factor`
- [ ] **Hand off to Code-side validation before order**

**Done when:** Debate runs reliably and APPROVED outputs pass code-side
sanity checks. Integration test in Demo: full debate → order → close.

**Directory:** `phase6_debate/` *(to be created)*

---

## Phase 7 — Reward/Punishment + Brain

**Goal:** The bot starts learning. Score updates, lessons extracted, fed back.

- [ ] `record_outcome()` — WIN/LOSS scoring rules
- [ ] Score → risk_level mapping (0–50 KONSERVATIV, 50–100 AGGRESSIV)
- [ ] `reflect()` / `reflect_with_kl()` after every close
- [ ] Lesson extraction → SQLite `trade_lessons`
- [ ] `longterm_pre_trade_check()` VETO
- [ ] Brain context injected into next Phase 4 research call

**Done when:** After 5 demo trades, score updates correctly, lessons are
stored, next research call uses them.

**Directory:** `phase7_brain/` *(to be created)*

---

## Phase 8 — Scheduler

**Goal:** Make it autonomous. Wake up, run, sleep, on a schedule.

- [ ] 09:20 Session Track trigger
- [ ] 09:25 Research trigger
- [ ] 09:30–11:19 Trading window (Gate 1 enforced)
- [ ] 11:30 hard stop
- [ ] Token refresh / session keepalive
- [ ] Graceful shutdown

**Done when:** Bot runs unattended for a full session, performs research,
trades within window, stops cleanly.

**Directory:** `phase8_scheduler/` *(to be created)*

---

## Phase 9 — V2 Erweiterungen

**Goal:** Implement the V2 improvements identified in the Council analysis.

### 9a — Council Skill Integration
- [ ] Integrate `verbesserungsvorschlaege` as structured input to pipeline
- [ ] Trigger detection for ad-hoc strategy evaluation

### 9b — Handover-Logik (Bull/Bear/Judge)
- [ ] Context-window monitoring during debate
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

**Done when:** All V2 changes operational, bot demonstrates improved learning
signal (process-score divergence from outcome-score on bad-market days).

**Directory:** `phase9_v2/` *(to be created)*

---

## Cross-cutting concerns (always)

- **Smoke tests** before any production change
- **No credentials in files** — keyring only
- **No AI for code-doable work** — every reach for AI must be justified
- **Atomic git commits** with clear messages
- **Phase isolation** — cross-phase imports only through defined contracts
