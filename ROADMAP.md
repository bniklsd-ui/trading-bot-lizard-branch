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

**Goal:** Replace the simple direction decision with an adversarial early-stop
debate. First multi-agent AI path **and** the most expensive path in the system —
cost discipline (caching + metering + caps) matters as much as functionality.

> **AI boundary:** AI is used **only** for Bull/Bear arguments + Judge synthesis.
> Context assembly, budget/caps, persistence, and fail-closed handling are all
> deterministic code. The debate **never** sees the broker or any VETO/Gate
> function — it can't bypass a VETO because it never references one.

- [x] Bull agent — **Haiku 4.5** (`claude-haiku-4-5-20251001`), config-overridable (Decision C)
- [x] Bear agent — **Haiku 4.5**, config-overridable (Decision C)
- [x] Judge agent — **Sonnet 4.6**, config-overridable (Decision C)
- [x] Early-stop orchestration (`max_rounds=5`) + hard caps on calls / cumulative
      tokens / wall-clock; any cap breach → **ABSTAIN** (Decisions E/J)
- [x] Judge is the **direction source** — emits final `direction` that **may flip**
      the Phase-4 seed BUY↔SELL (Decision B); Bull/Bear only argue
- [x] Judge emits qualitative `decision ∈ {TRADE, ABSTAIN}`; `confidence` is
      **advisory and gates nothing** (Decision H)
- [x] Caching + extended token-meter (cache-read/write fields) so the cost
      optimization is provable; `usage_report` shows cache-hit ratio (Decisions D/G)
- [x] Forward-compatible JSON audit `debate_log.json` (no SQLite — DB read-only
      until Phase 7; schema maps to P9 tables, Decision I)
- [x] Seam: `debate_runner` injected **between Gate 2 and Gate 3** in
      `executor.run()`; **default passthrough keeps Phase 5 AI-free**; Gates /
      VETOs / sizing run unchanged on the (possibly flipped) direction (Decision A)

**Done when:** Debate runs reliably; every error / cap-breach → fail-closed
ABSTAIN → NO_TRADE (never "trade anyway"). Integration test in Demo: full debate →
TRADE→order→close **or** ABSTAIN→NO_TRADE, `debate_log.json` written, cache **creation**
> 0 (cache *reads* only on multi-round debates — Haiku's 4096-token floor + 1-round
early-stop mean a single-round ABSTAIN reads no prefix; gated on `rounds_used >= 2`).
✅ **Done + live-verified 2026-06-16** (one Demo cycle: 3 real calls → ABSTAIN → NO_TRADE
→ `debate_log.json`; live-verified ≠ profit-validated — edge is Phase 7).

**Directory:** [`phase6_debate/`](./phase6_debate/)
**Concept:** [`docs/concepts/phase6_debate_concept.md`](./docs/concepts/phase6_debate_concept.md)

---

## Phase 7 — Reward/Brain (Score + Lessons + observe-only Confidence)

> **Scope-lock (lean model):** Phase 7 = **Reward-Score** (`reward_pts`,
> process-aware from day one) + **free-text Lessons** (`trade_lessons`) +
> **observe-only outcome-anchored Confidence**. **No VETO touch.** The full
> Instinct→VETO promotion ("ECC") is a separate, later step (Phase 9f / concept
> §7b), gated on real outcomes — promoting rules on zero validated outcomes
> would import risk back into the safety layer.

**Goal:** The bot starts learning. Score updates, lessons extracted, fed back
into the next research call.

- [x] `RewardSink` write-seam (`on_trade_opened` / `on_trade_closed`), default
      `None` → Phase 5 bit-identical (Decision A)
- [x] Process-aware reward scoring (`reward_pts`: outcome + process delta,
      clamped to [0,100], per-trade `|delta|` capped) → `score_after` (Decision B/D)
- [x] Score → risk_level mapping unchanged (binary `get_risk_level`, threshold 50)
- [x] Outcome-anchored Confidence `f(Wilson-LB(win_rate), expectancy_R, N)`,
      N_min=10 → INSUFFICIENT; **observe-only — gates nothing** (Decision C)
- [x] `reflect()` after every close — Haiku lesson extraction → `trade_lessons`,
      best-effort, decoupled from the close critical path (Decision E)
- [x] Lessons fed back: the research prompt already injects `get_recent_lessons`;
      close the loop by writing lessons + `mark_lesson_used` (Decision I)

**Done when:** After 5 demo trades, score updates correctly, lessons are
stored, and the next research call uses them. ✅ **live-verified (2026-06-26)** —
`live_test.py` → **5/5** against IG Demo: SELL placed → time-stop close →
`trade_outcomes` CLOSED + `reward_pts` + `trade_lessons` written, with P&L
resolved **lag-free from the close confirmation** (Steps 0–13 + live-debug
13b/13c; 128 P7 unit tests). ⚠ live-verified ≠ profit-validated (edge is later
live running).

**Directory:** `phase7_reward/` *(package `reward`)*
**Concept:** [`docs/concepts/phase7_reward_concept.md`](./docs/concepts/phase7_reward_concept.md)

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

### 9f — Instinct-Promotion (ECC) + Longterm VETO *(moved from Phase 7)*
- [ ] AI extracts structured instincts (trigger / domain / confidence /
      evidence_trade_ids) from Phase-7 `trade_lessons` + `reward_pts`
- [ ] Code **validates** instincts against real outcomes; proven ones are
      **promoted to deterministic rules** (`longterm_pre_trade_check()` VETO),
      with prune→archive of refuted ones
- [ ] Hard guardrail: a promotion to the VETO layer happens **only** via a
      deterministic / human-gated step — a promoted rule becomes deterministic
      code; the AI never sits inside VETO evaluation. Gated on real outcomes
      (≫ `n_min`). See concept §7b — Phase 7 only builds the substrate
      (`trade_lessons` + `reward_pts`), not the instinct system itself.

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
