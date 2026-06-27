# phase8_scheduler — Scheduler (autonomous unattended demo trading)

Phase 8 of the DAX intraday CFD trading bot. Importable package: **`scheduler`**.
Entry point: `python -m scheduler.run`.

> **Status:** 🔄 in progress (since 2026-06-27). Initial steps (cleanup / doc
> reconciliation / contract-verify / scaffold) underway. See `CLAUDE.md` →
> `## Session stopped` for the current step.

## What this is

"Scheduler" is only the name. The **mission** is autonomous, unattended generation
of **real demo trades** — the data supply that Phase 9 (confidence out of
`INSUFFICIENT`, instinct-promotion) is gated on. The hard part is **autonomous
candidate generation** via real Phase-4 research (never the manual seed); without it
the scheduler gathers zero data.

**Phase 8 adds no new AI** — it is deterministic mechanics: a long-running daemon
with market-hours phases, a demo-only fail-closed auto-confirm, a file-based
kill-switch, a daily-loss circuit breaker, a token budget, and an idempotent
reconcile pass. AI stays at the reused P4 pick / P6 debate / P7 lesson.

## Build order (binding)

Cleanup → Verify → autonomous candidates → Auto-Confirm/Safety → Reconcile →
Loop/Daemon → **(last)** Web-UI. Under time/token pressure the UI drops, never the
safety.

## Run (operator)

```bash
bash scripts/dev_install.sh                  # editable-install P1..P8 (repo root)
python phase2_persistence/scripts/init_db.py # ensure DB + migrations
# inside an unlocked session (keyring reachable), within the trade window:
bash phase8_scheduler/scripts/run_scheduler.sh
```

- Tests: `pytest phase8_scheduler/tests -v` (mocked — no network, no real LLM, no
  real sleep).
- Live verification (`scripts/live_test.py`, IG Demo) is the **operator's** job.

Concept: [`../docs/concepts/phase8_scheduler_concept.md`](../docs/concepts/phase8_scheduler_concept.md)
Project rules + verified contracts: [`CLAUDE.md`](./CLAUDE.md)
