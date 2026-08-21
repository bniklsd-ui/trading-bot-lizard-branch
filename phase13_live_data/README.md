# phase13_live_data — Live-Datenfundament

Phase 13 fixes the failure mode Phase 12.5 died on: the consumption path fetches its own
data. It splits acquisition from consumption for good — a consumer that needs data it
doesn't have gets a typed status, never a purchase.

Full execution-ready plan (locked decisions L1–L17, Blocks A/B/C, acceptance criteria):
[`docs/concepts/phase13_live_data_plan.md`](../docs/concepts/phase13_live_data_plan.md).
Phase head / session log: [`CLAUDE.md`](./CLAUDE.md).

## Package: `live_data`

| Module | Responsibility | Status |
|---|---|---|
| `stream.py` | `LSBarRecorder` (CHART-Pfad, dormant seit B0=NO 2026-08-19) + `TickAggregator` + `TickAggregatorRecorder` (S1-Primärpfad: PRICE-Tick-Aggregation → 1-min OHLC → `BarArchive`) | ✅ Block B2 + B0.5, 21 Tests |
| `backfill.py` | `CapitalSource` (S3 PARTIAL — Capital.com für DE40/FR40) + `run_capital_backfill()` (vier quellenunabhängige Regeln aus Plan §6 C1.0) | ✅ Session 12 Step 1, 11 Tests. SP35/AEX/MIB bleiben Path-C-Territorium (Dukascopy, deferred). |
| `rescue.py` | `GapRescue` (S4, budgeted IG range rescue, default OFF) | ✅ Block C2, 11 Tests |

**Bauprinzip:** zero new AI. Gap detection, coverage assessment, source selection, bar
aggregation and freshness checks are deterministic code — see root `CLAUDE.md`.

Cross-phase pieces this phase edits live in `phase12_data_foundation/data_foundation/`
(`coverage.py`, `archive.py`, `service.py`), `phase10_v3/abstain_lessons/paper.py`,
`phase1_broker_wrapper/broker_wrapper/streaming/` and `phase8_scheduler/` — see the phase
head's Modul-Tabelle for the full cross-phase list.
