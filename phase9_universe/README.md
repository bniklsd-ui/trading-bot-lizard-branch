# Phase 9 (V2 — Foundation) — `phase9_universe/`

Autonomous instrument discovery → verify → promote pipeline (package `universe`), plus
(later steps) a hardened data-input path. Replaces the hand-curated `EXTENDED_UNIVERSE`
tuple in `phase4_research/research/models.py` with a DB-backed, code-evaluated pipeline —
no new AI anywhere in this layer.

Full plan: [`../docs/concepts/phase9_v2_foundation_plan(1).md`](../docs/concepts/phase9_v2_foundation_plan(1).md)
Session state / conventions: [`CLAUDE.md`](./CLAUDE.md)

## Status

| Module | Purpose | Status |
|---|---|---|
| Migration 004 (`phase2_persistence/migrations/`) | `instrument_universe` table | ✅ |
| `universe/models.py` | Types only — status constants, `UniverseRecord` | 🔄 |
| `universe/exceptions.py` | Typed exception hierarchy | 🔄 |
| `universe/store.py` | `UniverseStore` — SQLite CRUD | 🔄 |
| `universe/pricing.py` | Deterministic `point_value` resolver | ⬜ |
| `universe/discovery.py` | Seed-sweep + code filter | ⬜ |
| `universe/promotion.py` | Status machine + safety | ⬜ |

## Running tests

```bash
source phase1_broker_wrapper/.venv/bin/activate   # shared venv, see repo root memory
pytest phase9_universe/tests -q
```
