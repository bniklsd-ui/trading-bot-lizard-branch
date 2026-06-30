# Architecture

> Visual reference: [`docs/architecture/tradingbot_v2_architecture.svg`](./docs/architecture/tradingbot_v2_architecture.svg)
> The SVG is the canonical, up-to-date system diagram. This document is text-form for grep-ability.
>
> **As-built reconciliation (2026-06-30, v1.5 hotfix housekeeping Step 0b):** this document had
> drifted to a pre-Phase-5 vocabulary (options terminology, a single `pre_trade_option_check()`,
> no Phase 7/8). Brought to as-built against the live code (P1–P8, code = source of truth). See
> `phase8_scheduler/PHASE8_V1.5_HOTFIX_HANDOVER.md` for the current open work (Phase 8 abstains
> almost every cycle — the v1.5 hotfix is in progress).

---

## System layers (top-down)

```
┌────────────────────────────────────────────────────────────────────┐
│  COUNCIL SKILL  (Standalone, Browser-based, optional pre-evaluation) │
└────────────────────────────────────────────────────────────────────┘
                              ↓ (verbesserungsvorschlaege)
┌─────────────────────┐  ┌────────────────────┐  ┌─────────────────┐
│  research.py (P4)   │→ │  turbo_candidates  │→ │ ig_bot.py run_  │
│  (LLM + P1/P2/P3    │  │  .json (TTL 30min, │  │ cycle() GATES   │
│  context assembly)  │  │  frozen legacy name)│  │ 1–5 (P5)        │
└─────────────────────┘  └────────────────────┘  └─────────────────┘
                                                          ↓
                                              ┌────────────────────┐
                                              │ pre_trade_check()  │
                                              │ (4 HARD VETOs, P5) │
                                              └────────────────────┘
                                                          ↓
                                              ┌────────────────────┐
                                              │ BULL / BEAR / JUDGE│
                                              │ DEBATE (P6, Claude │
                                              │ Sonnet, fail-closed│
                                              │ ABSTAIN on doubt)  │
                                              └────────────────────┘
                                                          ↓ TRADE
                                              ┌────────────────────┐
                                              │ BROKER & POSITION  │
                                              │ MGT (via wrapper)  │
                                              └────────────────────┘
                                                          ↓ after close
                              ┌───────────────────────────┴───────────────┐
                              ↓                                           ↓
                ┌─────────────────────────┐               ┌─────────────────────────┐
                │ REWARD SCORE (P7)       │               │ LONGTERM BRAIN (P7)     │
                │ process-aware Δ, never  │               │ reflect() — one Haiku   │
                │ gates anything          │               │ call, extract a lesson  │
                └─────────────────────────┘               └─────────────────────────┘
                              ↓                                           ↓
                              └────────────→ SQLITE (P2) ←────────────────┘
                                            trade_outcomes / reward_pts /
                                            trade_lessons (V2: market_regime_
                                            snapshots / decision_context /
                                            lesson_embeddings — future, P9)

┌────────────────────────────────────────────────────────────────────┐
│  SCHEDULER (P8) — unsupervised daemon driving the cycle above on a  │
│  market-hours loop: auto-confirm, file kill-switch, daily-loss      │
│  breaker, token budget, idempotent reconcile, read-mostly web UI.   │
│  🟡 code-complete + merged, autonomous net-new trade NOT yet proven │
│  live (the bot abstains almost every cycle — v1.5 hotfix in flight) │
└────────────────────────────────────────────────────────────────────┘
```

---

## Core components

### Broker abstraction (`broker_wrapper/`)
- Unified interface (`BrokerAdapter`) — every broker implements the same methods
- Current adapters: `IGAdapter` (REST), skeleton Lightstreamer streaming client
- Returns standardized `Envelope` JSON for every call
- Credential access via OS keyring only

### 5-Gate Pipeline (`execution/gates.py` + `execution/sizing.py`, `ig_bot.py` orchestrator)
1. **Gate 1: Time Window** — `09:00`–`17:30` (`config.tz`, full market window)
2. **Gate 2: Load Candidates** — fresh `turbo_candidates.json` (frozen legacy filename, TTL
   30 min); runs research if stale/empty
3. **Gate 3: Constraints** — budget available, room under `max_parallel_positions`
4. **Gate 4: Sizing** (`sizing.py`) — **risk-per-trade ÷ stop-distance** (not notional ÷ price;
   v1-tunable `risk_pct`)
5. **Gate 5: Direction Consistency** (ex-"Direction Fix") — direction is **BUY/SELL** (no
   CALL/PUT — this is a CFD bot, not an options bot), no open opposite position on the epic

### Hard VETO Cascade (`execution/vetos.py` → `pre_trade_check()`, 4 VETOs, fresh snapshot)
- **VETO 1** `veto_status_and_window` — market TRADEABLE + inside the trade window (fail-closed
  on a bad price snapshot)
- **VETO 2** `veto_spread` — fresh `spread_pct` within `max_spread_pct` (re-checked at order
  time, not the Phase-4 research-time spread)
- **VETO 3** `veto_momentum` — adverse-momentum guard from **IG real-time bars** (`get_ohlcv`,
  P1) — **not** the ~15-min-delayed yFinance P3 signal; a BUY into a sharp drop or SELL into a
  sharp rally is vetoed
- **VETO 4** `veto_position_conflict` — no open opposite position on the same epic, under
  `max_parallel_positions`

### Bull/Bear/Judge Debate (Phase 6)
- Three Claude Sonnet/Haiku calls per cycle: Bull argues for, Bear against, Judge synthesizes
- The Judge emits the **final direction** — may flip BUY↔SELL from the Phase-4 research pick
- Any error or budget/cap breach → **fail-closed ABSTAIN → NO_TRADE**, never "trade anyway"
- `confidence` is **advisory only** — it gates nothing; the deterministic gates/VETOs above are
  the real check
- Cross-phase reuse of the Phase-4 `LLMClient`/token-meter — no second metering system

### Reward Score + Longterm Brain (Phase 7 — process-aware, replaces the legacy V2 reform sketch)
- **`reward_pts`** — a process-aware score delta per closed trade: a damped *outcome* component
  (clipped R-multiple, asymmetric on losses) **plus** an independent *process* component (clean
  exit vs. time-stop, tight-spread bonus, a weak additive debate signal) — never a multiplier on
  outcome
- **`trade_lessons`** — `reflect()`, one best-effort Haiku call per closed trade, extracts a
  free-text lesson (language only — no number/score/decision); failures never break the close path
- **Confidence** (Wilson lower-bound / expectancy-R / N-min) is **observe-only** — it does not
  gate `risk_pct` or anything else in v1. Promotion to an actual VETO ("Instinct→VETO ECC") is
  deferred to **Phase 9f**, gated on real outcomes
- **No VETO touch.** Reward/lessons sit entirely downstream of order execution

### Scheduler (Phase 8 — 🟡 code-complete + merged, unproven live)
- Long-running daemon (injectable `now_fn`/`sleep_fn`) drives the cycle above unsupervised on a
  market-hours loop, with no new AI — pure mechanics around the existing P4 research / P6 debate
  / P7 reward calls
- Safety: `AutoConfirm` (demo-only, fail-closed `confirm_fn` replacement), a file kill-switch,
  consecutive-failure backoff, a daily-loss breaker, a daily token budget, idempotent reconcile
- Read-mostly web UI (FastAPI, DB opened `mode=ro`) for status/control — control is file-writes
  only, so a UI crash can never touch trading
- **Status:** the bot currently **abstains almost every cycle** (single-instrument universe +
  an over-conservative confidence clamp below score 50) — no net-new autonomous trade has been
  observed open→close in one clean run yet. The **v1.5 hotfix** (universe variety, clamp/floor
  decoupling, lesson provenance) is the active track; see
  `phase8_scheduler/PHASE8_V1.5_HOTFIX_HANDOVER.md`

### Dual State
- **SQLite (persistent):** `trade_lessons`, `trade_outcomes`, `reward_pts`,
  `ig_config_state` + (future, P9) `market_regime_snapshots`, `decision_context`,
  `lesson_embeddings`
- **JSON (operational, TTL):** `ig_state.json` (account/positions, fresh <60s),
  `ig_config.json` (static bot config), `turbo_candidates.json` (frozen legacy name, TTL
  30 min) + later-phase runtime files (all gitignored): `llm_usage.json` (P4 token meter),
  `execution_state.json` (P5 write-ahead idempotency), `debate_log.json` (P6 audit),
  `scheduler_state.json`/`scheduler_command.json`/`KILL` (P8 daemon state + control)

### Council Skill (standalone, optional)
- 5 philosopher personas + neutral narrator (Sokrates, Machiavelli, Epiktet,
  Nietzsche, Sun Tzu + Sprecher)
- Adversarial strategy evaluation
- React artifacts: `the_council.jsx`, `council_architecture.jsx`
- Triggered by phrases like "Idee diskutieren", "Rat befragen", "challengen"

---

## Identified risks (from V2 Council analysis)

1. **★ Force Trigger** — human override that bypasses time window. Critical
   on losing days. Recommendation: lock when daily PNL < 0 (root `CLAUDE.md`
   Hard Rule 5). The P2 schema already carries a `force_trigger_locked` flag
   (`persistence/defaults.py`), but no Force Trigger feature exists yet to
   enforce it against — tracked for whenever manual override is built (P9+).
2. **Score-as-emotion** — addressed by Phase 7: `reward_pts` measures process
   quality (clean exit vs. time-stop, spread tightness, debate signal)
   independently from the outcome component, instead of punishing unlucky
   but well-executed trades. Live-verified 2026-06-26.
3. **AI hallucination in interpretation** — even when AI only interprets
   (never fetches data), it can hallucinate. Mitigated structurally by:
   schema validation, code-side sanity checks, VETO cascade running on
   real market data regardless of AI output.

---

## See also

- Build plan: [`ROADMAP.md`](./ROADMAP.md)

Per-phase concept + implementation:

- Phase 1 — [`docs/concepts/phase1_broker_api_konzept.md`](./docs/concepts/phase1_broker_api_konzept.md) · [`phase1_broker_wrapper/`](./phase1_broker_wrapper/)
- Phase 2 — [`docs/concepts/phase2_persistence_konzept.md`](./docs/concepts/phase2_persistence_konzept.md) · [`phase2_persistence/`](./phase2_persistence/)
- Phase 3 — [`docs/concepts/phase3_external_data_konzept.md`](./docs/concepts/phase3_external_data_konzept.md) · [`phase3_external_data/`](./phase3_external_data/)
- Phase 4 — [`docs/concepts/phase4_research_plan_konzept.md`](./docs/concepts/phase4_research_plan_konzept.md) · [`phase4_research/`](./phase4_research/)
- Phase 5 — [`docs/concepts/phase5_concept.md`](./docs/concepts/phase5_concept.md) · [`phase5_execution/`](./phase5_execution/)
- Phase 6 — [`docs/concepts/phase6_debate_concept.md`](./docs/concepts/phase6_debate_concept.md) · [`phase6_debate/`](./phase6_debate/)
- Phase 7 — [`docs/concepts/phase7_reward_concept.md`](./docs/concepts/phase7_reward_concept.md) · [`phase7_reward/`](./phase7_reward/)
- Phase 8 — [`docs/concepts/phase8_scheduler_concept.md`](./docs/concepts/phase8_scheduler_concept.md) · [`phase8_scheduler/`](./phase8_scheduler/) · hotfix in flight: [`phase8_scheduler/PHASE8_V1.5_HOTFIX_HANDOVER.md`](./phase8_scheduler/PHASE8_V1.5_HOTFIX_HANDOVER.md)
