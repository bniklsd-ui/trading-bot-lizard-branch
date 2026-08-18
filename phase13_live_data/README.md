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
| `stream.py` | `LSBarRecorder` (S1, write-through IG Lightstreamer candles) + `TickAggregator` (L6 fallback) | ⬜ Block B2 |
| `backfill.py` | `ExternalBackfill` (S3, independent third source) | ⬜ Block C1 |
| `rescue.py` | `GapRescue` (S4, budgeted IG range rescue, default OFF) | ⬜ Block C2 |

**Bauprinzip:** zero new AI. Gap detection, coverage assessment, source selection, bar
aggregation and freshness checks are deterministic code — see root `CLAUDE.md`.

Cross-phase pieces this phase edits live in `phase12_data_foundation/data_foundation/`
(`coverage.py`, `archive.py`, `service.py`), `phase10_v3/abstain_lessons/paper.py`,
`phase1_broker_wrapper/broker_wrapper/streaming/` and `phase8_scheduler/` — see the phase
head's Modul-Tabelle for the full cross-phase list.
