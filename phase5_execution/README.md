# Phase 5 — Execution (`phase5_execution/`)

The first end-to-end **execution path** of the DAX CFD trading bot: it turns a
Phase-4 candidate into an actual (IG **Demo**) order, guarded by Gates 1–5, four
hard pre-trade VETOs, write-ahead idempotency, polling-based monitoring, and a
startup reconcile. **Manual trigger only — no scheduler (that is Phase 8).**

> ⚠️ **Status: in progress.** Only the composition-root scaffolding exists so far
> (Step 0 terminology hygiene + Step C editable installs). The gates, VETOs,
> sizing, order, monitor and executor modules are not built yet. See `CLAUDE.md`
> → `## Session stopped` for exactly where things stand and what comes next.

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

## Run (later steps — not built yet)

- `python phase5_execution/ig_bot.py --dry` — run Gates + VETOs, place **no** order.
- `python phase5_execution/scripts/smoke_test.py` — read-only DRY sanity of each verdict.
- `python phase5_execution/scripts/live_test.py` — full open→close vs IG Demo
  (operator-run, not CI). Requires IG Demo creds in the OS keyring.

Logs go to **stderr**; **stdout** carries only the machine-readable result JSON.
