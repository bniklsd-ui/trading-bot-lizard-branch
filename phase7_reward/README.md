# Phase 7 — Reward/Brain (`phase7_reward/`)

The phase where the bot **starts learning**. After every closed trade it (1) scores
the outcome **process-aware** (an `reward_pts` delta combining a braked outcome
component with a real process-signal component), (2) extracts a short free-text
**lesson** (`trade_lessons`) via one Haiku call, and (3) reports an **outcome-anchored
confidence** `f(Wilson-LB(win_rate), expectancy_R, N)` — **observe-only**, gating
nothing in v1. Those lessons feed back into the next Phase-4 research call (the
research prompt already injects `get_recent_lessons`). **Demo only, manual trigger —
no scheduler (that is Phase 8).**

> ✅ **Status: live-verified (2026-06-26).** Reward math (confidence + process-aware
> scorer), synthetic/live separation, lesson AI (`Brain.reflect`), P&L resolution,
> recorder orchestration, the `reward_sink` executor seam, loop-closure
> (`mark_lesson_used`), migration 002, and the wiring + operator scripts are all built
> (**128 P7 unit tests**; regression P1 52 · P2 62 · P4 94 · P5 146 · P6 70 green).
> `scripts/live_test.py` ran **5/5** against IG Demo: a SELL was placed → time-stop
> close → `trade_outcomes` CLOSED + `reward_pts` + `trade_lessons` written, with P&L
> resolved **lag-free from the close deal confirmation** (live-debug 13b/13c — IG demo
> books `get_trade_history` only after settlement, so the close confirm is the intraday
> P&L source). ⚠ **live-verified ≠ profit-validated** (only one trade; edge is later
> live running). See `CLAUDE.md` → the latest `## Session stopped` block.

**AI boundary.** AI is used **only** for the lesson-extraction `reflect()` (one
Haiku call, best-effort, decoupled from the close critical path). Everything else —
the score delta (outcome + process), the confidence math (Wilson lower bound,
expectancy-R, SQN, N_min gating), P&L resolution, persistence, and fail-closed error
handling — is deterministic code. The score's `confidence` is **observe-only and
gates nothing**; it does not modulate `risk_pct` in v1. **No VETO touch** — the full
Instinct→VETO promotion ("ECC") is deferred to Phase 9 / concept §7b. Full design +
the locked decisions A–J:
[`../docs/concepts/phase7_reward_concept.md`](../docs/concepts/phase7_reward_concept.md).

**Reuse, not reinvent (Decision F/G).** The single LLM call site is **reused** from
Phase 4 (`research.LLMClient` / `research.token_meter`), and persistence is the
Phase-2 `Database` CRUD (`insert_trade` / `update_trade_close` / `insert_reward` /
`insert_lesson`) — no second metering system, no new DB layer. The write path is an
optional, duck-typed `reward_sink` injected into the Phase-5 `Executor` (default
`None` → Phase 5 stays **bit-identical**), mirroring the Phase-6 `debate_runner` seam.

## Package layout

The importable package is **`reward`** (nested as `phase7_reward/reward/`), mirroring
the repo convention (`phase4_research/research/`, `phase5_execution/execution/`,
`phase6_debate/debate/`). Cross-phase collaborators (broker, the Phase-4 LLM stack,
the Phase-2 `Database`) are reached only through their contracts, wired in
`scripts/wiring.py` (a later step).

## Setup (editable installs — the composition root)

From the repo root, into your active venv:

```bash
bash scripts/dev_install.sh         # pip install -e P1..P7 in dependency order
pytest phase7_reward/tests -v       # (tests land with the reward-logic steps)
```

This is the same composition root used by Phase 5/6; it now installs Phase 7 after
Phase 4/5/6 (Phase 7 reuses Phase 4's LLM stack and Phase 2's `Database`).

## Run (operator gate — Demo only, manual trigger)

```bash
python phase2_persistence/scripts/init_db.py            # applies migration 002 (reward columns)
python phase5_execution/scripts/seed_candidate.py --direction SELL   # in window, with the move; TTL 30 min
python phase7_reward/scripts/smoke_test.py              # one real Haiku reflect(), DRY (no DB write)
python phase7_reward/scripts/live_test.py               # full open→close→reward→lesson vs IG Demo
```

`live_test.py` drives a full cycle against IG Demo and, when an order placed+closed,
hard-asserts a CLOSED `trade_outcomes` row + a `reward_pts` row for the deal (the
`trade_lessons` row is best-effort — the only AI — and reported, not gated). A clean
`NO_TRADE`/abstain is a valid exit-0. ⚠ **code-complete ≠ live-verified ≠
profit-validated.**

`scripts/backfill_synthetic.py` populates a **separate** synthetic DB for the
confidence math — it calls `guard_synthetic_path` first and refuses (exit 2) to write
to the live DB. Logs go to **stderr**; **stdout** carries only machine-readable JSON.
