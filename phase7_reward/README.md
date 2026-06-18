# Phase 7 — Reward/Brain (`phase7_reward/`)

The phase where the bot **starts learning**. After every closed trade it (1) scores
the outcome **process-aware** (an `reward_pts` delta combining a braked outcome
component with a real process-signal component), (2) extracts a short free-text
**lesson** (`trade_lessons`) via one Haiku call, and (3) reports an **outcome-anchored
confidence** `f(Wilson-LB(win_rate), expectancy_R, N)` — **observe-only**, gating
nothing in v1. Those lessons feed back into the next Phase-4 research call (the
research prompt already injects `get_recent_lessons`). **Demo only, manual trigger —
no scheduler (that is Phase 8).**

> 🚧 **Status: pre-steps in progress (Step 1) — 2026-06-18.** This session does the
> housekeeping/verification + package scaffold only (Step 0 turbo No-Op, Step 0b doc
> reconciliation, Step 1 verify-against-code, Step 2 scaffold). **No reward logic yet**
> — Steps 3–13 (models → confidence → scorer → synthetic → brain → recorder →
> pnl_resolver → executor seam → loop-closure → migration → wiring) are later TDD
> sessions. See `CLAUDE.md` → `## Verifizierte Contracts` and the latest
> `## Session stopped` block for the exact current state.

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

## Run

The smoke / live scripts (`scripts/smoke_test.py`, `scripts/live_test.py`) land with
the later build steps. The live test (operator-run, **Demo only**) will drive a full
open→close→reward→lesson cycle against IG Demo and assert a `trade_outcomes` +
`reward_pts` + `trade_lessons` row was written. ⚠ **live-verified ≠ profit-validated.**

Logs go to **stderr**; **stdout** carries only machine-readable JSON.
