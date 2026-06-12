# Phase 5 — Execution (`phase5_execution/`)

The first end-to-end **execution path** of the DAX CFD trading bot: it turns a
Phase-4 candidate into an actual (IG **Demo**) order, guarded by Gates 1–5, four
hard pre-trade VETOs, write-ahead idempotency, polling-based monitoring, and a
startup reconcile. **Manual trigger only — no scheduler (that is Phase 8).**

> ✅ **Status: code-complete + live-verified (Demo) — 2026-06-12.** 130 mocked
> unit tests green; `scripts/live_test.py` placed a real IG-Demo order
> (ACCEPTED) and closed it via time-stop → `RESULT: 4/4 passed`. The full path
> is proven end-to-end (Gates → sizing → 4 VETOs → place → monitor → close), not
> just in CI. See `CLAUDE.md` → the latest `## Session stopped` block for the
> exact final state.
>
> ⚠️ **Live-verified ≠ profit-validated.** "Live-verified" means the path
> *places and closes correctly*; it does **not** mean the bot is profitable —
> only one trade has been run and no edge has been measured. Profitability is
> anchored to outcomes in Phase 7 + live running, not here. `risk_pct` 2.0/3.0,
> `stop=30`/`limit=45`, `momentum_threshold=0.15`, `max_leverage=20` are all
> **v1** (to be tuned on profit, later).

**No AI here.** Gates, VETOs, sizing, order, monitoring and reconcile are all
deterministic code. The only AI in the system stays the single Phase-4 research
call, lazily triggered through Gate 2. Full design + the 8 locked decisions:
[`../docs/concepts/phase5_concept.md`](../docs/concepts/phase5_concept.md).

## Package layout

The importable package is **`execution`** (nested as `phase5_execution/execution/`),
mirroring the repo convention (`phase4_research/research/` etc.). Cross-phase
collaborators (broker / persistence / research) are reached only through their
contracts, wired in `scripts/wiring.py`.

## Setup (editable installs — the composition root)

From the repo root, into your active venv:

```bash
bash scripts/dev_install.sh        # pip install -e P1..P5 in dependency order
pytest phase5_execution/tests -v   # green => packages resolve without sys.path hacks
```

This replaces the older `sys.path` bootstrap: after it, `import broker_wrapper`,
`persistence`, `external_data`, `research` and `execution` all resolve directly.

## Run

All commands below run from `phase5_execution/`. **Demo only.** Prereqs: IG Demo
creds in the OS keyring (Phase-1 `scripts/store_credential.py`) and the editable
installs above.

```bash
# CLI entry — one execution cycle (gates -> VETOs -> confirm -> order -> monitor):
python -m execution.ig_bot --dry     # gates + VETOs + build plan, place NO order
python -m execution.ig_bot           # live cycle, stdin y/N confirm before the order
python -m execution.ig_bot --yes     # auto-confirm (skip the prompt) — deliberate
#   --epic <EPIC>  research allow-list override (only when research must run)
```

### Operator live-gate (reproduce the 4/4 pass)

Run inside the **09:00–17:30 Europe/Berlin** trade window, in this order:

```bash
# 1. Seed ONE fresh candidate (TTL 30 min — seed immediately before the run).
#    Pick the direction that matches the current get_ohlcv net-return so VETO 3
#    (momentum) passes: on a downward drift, seed SELL.
python scripts/seed_candidate.py --direction SELL

# 2. DRY sanity (places no order) — eyeball where the cycle stops:
python scripts/smoke_test.py

# 3. Hard-asserted live gate: real open -> time-stop close vs IG Demo.
#    exit 0 = PASS (a clean NO_TRADE / market-closed abstain is also exit 0;
#    only a fail-closed ABORT is a failure).
python scripts/live_test.py
```

The seed self-expires after 30 minutes: if it is stale when `live_test.py` runs,
Gate 2 treats candidates as not fresh and invokes the real Phase-4 research hook
(a non-deterministic LLM request that may abstain) instead — so re-seed **right
before** the live run.

Logs go to **stderr**; **stdout** carries only the machine-readable result JSON.
