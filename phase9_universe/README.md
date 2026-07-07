---
status: live
purpose: What phase9_universe built — components, limitations, integration points
read-when: needing this phase's public surface without its full head
detail: L2
up: ./CLAUDE.md
updated: 2026-07-07
---
# Phase 9 (V2 — Foundation) — `phase9_universe/`

Autonomous instrument discovery → verify → promote pipeline (package `universe`), plus
a hardened data-input path (BarProvider chain, behind the default-off `enable_ig_bars`
flag). Replaces the hand-curated `EXTENDED_UNIVERSE` tuple in
`phase4_research/research/models.py` with a DB-backed, code-evaluated pipeline —
no new AI anywhere in this layer.

Full plan: [`../docs/concepts/phase9_v2_foundation_plan(1).md`](../docs/concepts/phase9_v2_foundation_plan(1).md)
Session state / conventions: [`CLAUDE.md`](./CLAUDE.md)
Live-run day-1 results (2026-07-07): [`PHASE9_V2_LIVE_RESULTS_HANDOVER.md`](./PHASE9_V2_LIVE_RESULTS_HANDOVER.md)

## Status (2026-07-07)

| Module | Purpose | Status |
|---|---|---|
| Migration 004 (`phase2_persistence/migrations/`) | `instrument_universe` table | ✅ |
| `universe/models.py` | Types only — status constants, `UniverseRecord` | ✅ |
| `universe/exceptions.py` | Typed exception hierarchy | ✅ |
| `universe/store.py` | `UniverseStore` — SQLite CRUD | ✅ (19 tests) |
| `universe/pricing.py` | Deterministic `point_value` resolver | ✅ (16 tests) |
| `universe/discovery.py` | Seed-sweep + code filter | ✅ (14 tests) |
| `universe/promotion.py` | Status machine + safety (C3-konform seit 2026-07-06) | ✅ (16 tests) |
| P4/P8 integration + `universe_refresher` + `seed_curated` wiring | DB universe feeds research; refresher in preflight + 240min throttle | ✅ (live seit 2026-07-06) |
| BarProvider chain (`enable_ig_bars`, default off) | IG-primary bars + circuit breaker + divergence check | ✅ gebaut — Beobachtungslauf offen |

Live proven (day 1 of the baseline run): 8 active / 7 verified / 0 quarantined, all
`point_value` via `ig_fields`; first DB-universe pick (CAC). Open proof points + watch
items: see the handover above.

## Running tests

```bash
source phase1_broker_wrapper/.venv/bin/activate   # shared venv, see repo root memory
pytest phase9_universe/tests -q
```
