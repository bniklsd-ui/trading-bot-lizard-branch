# Phase 6 — Bull/Bear/Judge Debate (`phase6_debate/`)

The first **multi-agent AI path** of the DAX CFD trading bot — **and the most
expensive path in the system**. It replaces the simple direction decision with an
adversarial, early-stopping debate: a **Bull** argues LONG (BUY), a **Bear** argues
SHORT (SELL), and a **Judge** synthesises the exchange into a final direction +
`TRADE`/`ABSTAIN`. The Judge's direction is the *real* source and **may flip** the
Phase-4 seed (BUY↔SELL). **Demo only, manual trigger — no scheduler (that is Phase 8).**

> 🚧 **Status: scaffold + packaging (Step C) — 2026-06-12.** Concept is locked
> (11 decisions A–K). The phase home, `CLAUDE.md` knowledge base and editable
> install exist; module implementation (models → context → prompts → caching →
> budget → debate → audit → scripts → executor seam) is the work ahead. See
> `CLAUDE.md` → the latest `## Session stopped` block for the exact current state.

**AI boundary.** AI is used **only** for Bull/Bear arguments + Judge synthesis.
Context assembly, budget/caps, persistence, and fail-closed handling are all
deterministic code. The debate **never** sees the broker or any VETO/Gate function,
so it cannot bypass a VETO — every error / cap-breach / context failure →
**ABSTAIN → NO_TRADE**, never "trade anyway". The Judge's self-reported `confidence`
is **advisory and gates nothing** (logged for Phase-7 outcome-anchoring only). Full
design + the 11 locked decisions:
[`../docs/concepts/phase6_debate_concept.md`](../docs/concepts/phase6_debate_concept.md).

**Cost discipline is first-class.** Caching (stable system+context prefix) +
token-metering (incl. cache-read/write fields) + hard caps on calls, cumulative
tokens and wall-clock make the expense provable and bounded. The single LLM call
site is **reused** from Phase 4 (`research.LLMClient` / `research.token_meter`) — the
documented cross-phase exception (Decision F).

## Package layout

The importable package is **`debate`** (nested as `phase6_debate/debate/`),
mirroring the repo convention (`phase4_research/research/`,
`phase5_execution/execution/`). Cross-phase collaborators (broker, the Phase-4 LLM
stack) are reached only through their contracts, wired in `scripts/wiring.py`.

## Setup (editable installs — the composition root)

From the repo root, into your active venv:

```bash
bash scripts/dev_install.sh         # pip install -e P1..P6 in dependency order
pytest phase6_debate/tests -v       # green => `import debate` resolves without sys.path hacks
```

This is the same composition root used by Phase 5; it now installs Phase 6 after
Phase 4 (which Phase 6 imports for the shared LLM stack).

## Run

The smoke / live scripts (`scripts/smoke_test.py`, `scripts/live_test.py`) land
with the later build steps. The live test (operator-run, **Demo only**) drives the
debate inside the full Phase-5 executor against IG Demo and proves caching works
(cache-reads > 0 in `usage_report`).

Logs go to **stderr**; **stdout** carries only machine-readable JSON.
