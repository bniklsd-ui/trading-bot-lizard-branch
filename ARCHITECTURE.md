# Architecture

> Visual reference: [`docs/architecture/tradingbot_v2_architecture.svg`](./docs/architecture/tradingbot_v2_architecture.svg)
> The SVG is the canonical, up-to-date system diagram. This document is text-form for grep-ability.

---

## System layers (top-down)

```
┌────────────────────────────────────────────────────────────────────┐
│  COUNCIL SKILL  (Standalone, Browser-based, optional pre-evaluation) │
└────────────────────────────────────────────────────────────────────┘
                              ↓ (verbesserungsvorschlaege)
┌─────────────────────┐  ┌────────────────────┐  ┌─────────────────┐
│  turbo_research.py  │→ │  turbo_candidates  │→ │ ig_bot.py run_  │
│  (LLM + drift + ... │  │  .json (TTL 30min) │  │ cycle() 5 GATES │
└─────────────────────┘  └────────────────────┘  └─────────────────┘
                                                          ↓
                                              ┌────────────────────┐
                                              │ pre_trade_option_  │
                                              │ check() (4 VETOs)  │
                                              └────────────────────┘
                                                          ↓
                                              ┌────────────────────┐
                                              │ BULL / BEAR / JUDGE│
                                              │ (Claude Sonnet, 5R)│
                                              │ + HANDOVER LOGIK ★ │
                                              └────────────────────┘
                                                          ↓ APPROVED
                                              ┌────────────────────┐
                                              │ BROKER & POSITION  │
                                              │ MGT (via wrapper)  │
                                              └────────────────────┘
                                                          ↓ after close
                              ┌───────────────────────────┴───────────────┐
                              ↓                                           ↓
                ┌─────────────────────────┐               ┌─────────────────────────┐
                │ REWARD/PUNISHMENT ▲     │               │ LONGTERM BRAIN          │
                │ (Score-Reform: Prozess) │               │ (reflect, extract lesson)│
                └─────────────────────────┘               └─────────────────────────┘
                              ↓                                           ↓
                              └────────────→ SQLITE V2 ★ ←─────────────────┘
                                            + market_regime_snapshots
                                            + decision_context
                                            + lesson_embeddings (future)
```

---

## Core components

### Broker abstraction (`broker_wrapper/`)
- Unified interface (`BrokerAdapter`) — every broker implements the same methods
- Current adapters: `IGAdapter` (REST), skeleton Lightstreamer streaming client
- Returns standardized `Envelope` JSON for every call
- Credential access via OS keyring only

### 5-Gate Pipeline (`ig_bot.py run_cycle()`)
1. **Gate 1: Time Window** — 09:30 ≤ now ≤ 11:19 CET
2. **Gate 2: Load Candidates** — `turbo_candidates.json` non-empty, TTL valid
3. **Gate 3: Constraints** — Budget ≥5 GBP, max concurrent positions
4. **Gate 4: Broker** — Sizing `min(budget × 0.08, ×3C)`
5. **Gate 5: Direction Fix** — LLM direction = CALL/PUT, confidence ≥55

### Hard VETO Cascade (`pre_trade_option_check()`)
- VETO if spread ≥ 25%
- VETO if price drift ≥ 50% since research
- VETO if 15-min momentum ≥ 0.5% against trade direction
- Spread Guard

### Bull/Bear/Judge Debate
- Three Claude Sonnet instances, 5 rounds
- Adversarial structure: Bull argues for, Bear against, Judge decides
- ★ HANDOVER LOGIK (V2): when context window approaches 60–70% capacity,
  compress positions and start a new session with summary context
- APPROVED output → `size_factor` calculation → BROKER

### Reward/Punishment (V2 Reform ▲)
- WIN: `base + gain × 10 · speed_bonus`
- LOSS: `÷2.5` standard / `÷4.8` quick / `×8max` cap, extra `−3`
- **V2 Reform:** measure process quality (VETO frequency, confidence,
  debate quality, gate path) separately from outcomes
- Anti-emotionality: no score penalty for unavoidable market luck

### Longterm Brain
- `reflect()` / `reflect_with_kl()` after every trade close
- Extracts LESSON → stored in SQLite `trade_lessons`
- 30-day price history (yFinance), high/low distance, volume anomalies
- `longterm_pre_trade_check()`: VETO if expected hold ≥120 days

### Dual State
- **SQLite (persistent):** `trade_lessons`, `trade_outcomes`, `reward_pts`,
  `ig_config_state` + (V2) `market_regime_snapshots`, `decision_context`,
  `lesson_embeddings`
- **JSON (operational, TTL):** `ig_state.json` (account/positions), `ig_config.json`,
  `turbo_candidates.json` (TTL 30min)

### Council Skill (standalone, optional)
- 5 philosopher personas + neutral narrator (Sokrates, Machiavelli, Epiktet,
  Nietzsche, Sun Tzu + Sprecher)
- Adversarial strategy evaluation
- React artifacts: `the_council.jsx`, `council_architecture.jsx`
- Triggered by phrases like "Idee diskutieren", "Rat befragen", "challengen"

---

## Identified risks (from V2 Council analysis)

1. **★ Force Trigger** — human override that bypasses time window. Critical
   on losing days. Recommendation: lock when daily PNL < 0.
2. **Score-as-emotion** — current scoring punishes outcomes (anti-stoic).
   V2 Reform addresses this by measuring process quality.
3. **AI hallucination in interpretation** — even when AI only interprets
   (never fetches data), it can hallucinate. Mitigated structurally by:
   schema validation, code-side sanity checks, VETO cascade running on
   real market data regardless of AI output.

---

## See also

- Build plan: [`ROADMAP.md`](./ROADMAP.md)
- Phase 1 concept: [`docs/concepts/phase1_broker_api_konzept.md`](./docs/concepts/phase1_broker_api_konzept.md)
- Phase 1 implementation: [`phase1_broker_wrapper/`](./phase1_broker_wrapper/)
