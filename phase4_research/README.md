# Phase 4 — Research (LLM candidate selection)

> **Status:** ✅ Code-complete + live-**tested** (2026-06-09). 88 mocked unit tests
> green (no network); `scripts/live_test.py` → `RESULT: 3/3 passed` against IG Demo +
> a real LLM call. Build order and all locked decisions:
> `../docs/concepts/phase4_research_plan_konzept.md`.
>
> ⚠ **Live-tested, not profit-validated.** The pipeline is proven to run *correctly*
> end-to-end — correct context, a contract-valid pick **or** a clean abstain, and a
> safe no-trade on every failure path (last confirmed: a markets-closed abstain at
> 07:18, `exit 0`). Whether the bot makes **profitable** trades is **unknown**: no
> real trades have been placed or evaluated. That's correct at this stage — execution
> is Phase 5, and edge/profitability is a much later concern (Phase 7
> outcome-anchoring + live running). Green means "the logic works," **not** "the bot
> is profitable."

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
is auditable after the fact. `scripts/usage_report.py` totals it by model/day.

## Layout

```
research/
  models.py          # ✅ contracts: Candidate, ResearchContext, ResearchConfig, ValidationResult, exceptions
  validator.py       # ✅ hallucination guard (the safety core)
  context_builder.py # ✅ deterministic context from P1/P2/P3
  prompt.py          # ✅ (system, user, json_schema) builder — anyOf nullable enums
  llm_client.py      # ✅ Anthropic wrapper (Structured Outputs + fallback + 1 retry) + token meter
  candidate_filter.py# ✅ the real deterministic gate
  research.py        # ✅ orchestrator run()
  credentials.py     # ✅ keyring shim (documented phase-isolation exception, Decision 6)
scripts/             # ✅ wiring / smoke_test / live_test + usage_report
tests/               # ✅ mocked, no network — 88 green (validator 18 ≥12)
```

## Commands (CI / local — no network)

```bash
pytest tests/ -v                       # 88 mocked tests, no network (from this directory)
```

## Run (live — operator only, real network)

The two live scripts talk to **IG Demo** and the **real Anthropic API**; they are
run by the operator, never in CI. Prereqs:

```bash
pip install -r requirements.txt        # installs `anthropic` into the venv
# seed the LLM key into the OS keyring (reuses Phase-1's keyring, SERVICE "tradingbot"):
python ../phase1_broker_wrapper/scripts/store_credential.py anthropic_api_key
# IG Demo creds must already be seeded (Phase-1 store_credential.py).
```

```bash
python scripts/smoke_test.py           # DRY sanity: prints context + cycle outcome, saves nothing
python scripts/live_test.py            # hard-asserted gate: writes turbo_candidates.json or a clean abstain
```

**Output discipline:** machine-readable JSON (the would-be / persisted candidate
list) → **stdout**; all human-facing logs + the `RESULT:` line → **stderr**.
Market-closed (or a cautious model) → a clean abstain (empty list), still `exit 0`.
