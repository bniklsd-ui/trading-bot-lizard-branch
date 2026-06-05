# Phase 4 — Research (LLM candidate selection)

> **Status:** 🚧 In progress — **Step 1 done** (scaffold + `models.py`).
> Build order and all locked decisions: `../docs/concepts/phase4_research_plan_konzept.md`.

## What this is

The **one** AI step in the bot: a research LLM picks **≤ 1** DAX-CFD instrument
from a **code-curated** universe, and that pick is then run through
deterministic code-side guards before it can ever become a tradeable candidate.

```
code builds context  →  LLM picks (the only AI step)  →  code validates  →
code filters (the real gate)  →  code persists  →  Phase 5
```

**Bauprinzip — so wenig AI wie möglich:** everything except the single
`ask_candidate` call is plain code. The LLM never triggers an order directly;
its output must pass the validator (hallucination guard) and the deterministic
`candidate_filter` (the real gate). LLM self-reported confidence is stored as
raw data but is **not** the gate (it is uncalibrated; Phase 7 will anchor it to
outcomes).

## Output

A pick is persisted as a `Candidate` dict in `turbo_candidates.json` (legacy
name — content is DAX-CFD candidates, **no** turbos/options; Phase-2/Phase-5
contract). Abstain or reject → **empty list** (`save_candidates([])`), never a
fabricated trade.

`direction` is **`BUY` / `SELL`** only — exactly what `open_position()` enforces.
There is no `CALL`/`PUT` anywhere.

## Token / cost meter

Every real LLM call's token usage (input/output, incl. cache fields) is logged
to `data/state/llm_usage.json` with **both** `est_cost_usd` (Anthropic's billing
unit) and `est_cost_eur` (via a configurable rate in `ResearchConfig`), so spend
is auditable after the fact. A `scripts/usage_report.py` summary readout totals
it by model/day. *(Built in Step 5 — not present yet.)*

## Layout

```
research/
  models.py          # ✅ contracts: Candidate, ResearchContext, ResearchConfig, ValidationResult, exceptions
  validator.py       # ☐ hallucination guard (Step 2 — the safety core)
  context_builder.py # ☐ deterministic context from P1/P2/P3 (Step 3)
  prompt.py          # ☐ (system, user, json_schema) builder (Step 4)
  llm_client.py      # ☐ Anthropic wrapper + token meter (Step 5)
  candidate_filter.py# ☐ the real deterministic gate (Step 6)
  research.py        # ☐ orchestrator run() (Step 7)
scripts/             # ☐ wiring / smoke_test / live_test (Step 8)
tests/               # mocked, no network — tests begin at Step 2 (validator ≥12)
```

## Commands

```bash
pip install -r requirements.txt        # only needed for the live scripts
pytest tests/ -v                       # mocked, no network (from this directory)
```

Live scripts (`smoke_test.py`, `live_test.py`) arrive in Step 8 and are run by
the operator (Niklas), never in CI.
