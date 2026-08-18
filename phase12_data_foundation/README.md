# phase12_data_foundation — Datenfundament

Phase 12 rebuilds the data layer three data weeks (Phase 11) kept dying on: the same
instrument fact lived in three divergent stores, the multi-source `ChainedBarProvider`
chain built in Phase 9 never ran (`enable_ig_bars` default `False`), and a whole day of
zero measurement went unnoticed until Friday.

Full execution-ready plan (locked decisions D1–D20, Steps 0–10, acceptance criteria):
[`docs/concepts/phase12_data_foundation_plan.md`](../docs/concepts/phase12_data_foundation_plan.md).
Phase head / session log: [`CLAUDE.md`](./CLAUDE.md).

## Package: `data_foundation`

| Module | Responsibility |
|---|---|
| `models.py` | `Bar` dataclass, source/status constants, `normalize_bar_ts` |
| `exceptions.py` | `DataFoundationError` hierarchy (`ArchiveError`, `BudgetError`, `ResolverError`) |
| `archive.py` | `BarArchive` — own-connection SQLite (`data/bars.sqlite`), write-through, source-preference reads |
| `budget.py` | `SourceBudget` — persistent IG-points spend ledger + `can_spend` prediction |
| `symbols.py` | *(Step 3)* seed candidates + `SymbolResolver` — derived, code-verified symbol mapping |
| `service.py` | *(Step 4)* `BarService` — the one bar path for all consumers (Research + Paper Tracker) |
| `recorder.py` | *(Step 5)* `Recorder` — yFinance-only continuous poll loop, fail-soft per epic, own process |
| `run.py` | *(Step 5)* `python -m data_foundation.run` — PID-guarded entrypoint, SIGTERM/SIGINT → graceful stop |
| `scripts/run_recorder.sh` | *(Step 5)* operator launcher (standalone, or auto-started from `run_scheduler.sh`) |
| `heartbeat.py` | *(Step 6)* `assess_day` (daily `HealthVerdict`, same-day alarm) + `DivergenceSampler` (IG-vs-yFinance cross-check, D12) |
| `coverage.py` | `WindowCoverage` + `assess_window` — fensterweite Abdeckungsprüfung (Phase 13 §6 A1, rein, kein I/O) |
| `scripts/data_health.py` | *(Step 6)* operator script — prints the day's `HealthVerdict` + budget standing + Recorder heartbeat age, exits 1 on `ok=False` |

**Bauprinzip:** zero new AI. `SymbolResolver` (Step 3) is a deterministic price-comparison
check against IG snapshots, not an LLM guess — see root `CLAUDE.md`.

## Commands

```bash
source phase1_broker_wrapper/.venv/bin/activate   # shared venv (repo convention)
bash scripts/dev_install.sh                        # editable-installs data_foundation too
pytest phase12_data_foundation/tests -v
```
