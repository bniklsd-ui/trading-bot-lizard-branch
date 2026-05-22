# persistence — Phase 2

The data layer for the trading bot. **100% deterministic code — no LLM calls.**
It stores and returns; it does not judge, score, or filter. Two stores, two
lifetimes:

- **SQLite** (`Database`) — persistent, historical: trade outcomes, rewards,
  lessons, operational config, and empty V2 audit tables (Phase 9 fills them).
- **JSON state** (`StateManager`) — short-lived operational state with TTL:
  account snapshot, static bot config, research candidates.

> Rule of thumb: *"What did the bot do last month?"* → SQLite.
> *"What is the bot doing right now?"* → JSON state.

## What it is, what it isn't

**Is:** schema + migrations, typed CRUD wrappers, TTL/freshness logic, seed
defaults, a one-time init script.

**Isn't:** business logic, scoring, filtering, AI, backtesting infrastructure
(Phase 3/4), or a write-path for live Lightstreamer ticks.

## Install

```bash
pip install -r requirements.txt   # only pytest (dev); sqlite3 + json are stdlib
```

## Initialize

```bash
python scripts/init_db.py
# or with custom locations:
python scripts/init_db.py --db-path /custom/trading_bot.sqlite --state-dir /custom/state
```

Creates `<repo_root>/data/trading_bot.sqlite` + `<repo_root>/data/state/`, applies
migrations, and seeds default config rows. **Idempotent** — safe to re-run. The
`data/` directory is gitignored (runtime artifacts, never committed).

## Layout

```
phase2_persistence/
├── persistence/
│   ├── __init__.py        exports Database, StateManager
│   ├── timeutil.py        ISO 8601 UTC helpers (utc_iso_now, parse_iso)
│   ├── schema.py          _schema_version DDL + migrations dir path
│   ├── defaults.py        seed rows for ig_config_state
│   ├── migrations.py      SQL-file migration runner (version-tracked, idempotent)
│   ├── db.py              Database — sqlite3 CRUD for all tables
│   └── state.py           StateManager — JSON read/write + TTL
├── migrations/
│   └── 001_initial.sql    all 6 tables + indexes (single source of DDL)
├── scripts/
│   └── init_db.py         one-time init (create dirs, migrate, seed)
└── tests/                 test_migrations.py · test_db.py · test_state.py
```

## SQLite tables

| Table | Filled by | Purpose |
|---|---|---|
| `trade_outcomes` | Phase 5+ | every open/closed trade |
| `reward_pts` | Phase 7 | per-trade score delta + accumulated score |
| `trade_lessons` | Phase 7 | extracted lessons (Longterm Brain) |
| `ig_config_state` | Phase 2+ | operational key-value state (seeded) |
| `market_regime_snapshots` | Phase 9 (V2) | market context per trade *(empty)* |
| `decision_context` | Phase 9 (V2) | Bull/Bear/Judge + VETO audit *(empty)* |

`ig_config_state` (mutable runtime state in the DB) is distinct from the
`ig_config.json` file (static config handled by `StateManager`).

## JSON state files

| File | TTL | Notes |
|---|---|---|
| `ig_state.json` | "fresh" if < 60s old | account + open positions snapshot |
| `ig_config.json` | none | static config; `load_bot_config()` raises if missing |
| `turbo_candidates.json` | 30 min | self-clears on expiry or when empty |

## Programmatic usage

```python
from persistence import Database, StateManager

db = Database("data/trading_bot.sqlite")
db.run_migrations()                       # idempotent: migrate + seed

trade_id = db.insert_trade({              # accepts Envelope.data / model.to_dict()
    "deal_id": "DIAAA", "epic": "IX.D.DAX.IFMM.IP", "direction": "BUY",
    "size": 1.0, "open_level": 18000.0, "currency": "EUR",
    "open_ts": "2026-05-22T09:00:00.000Z", "session_date": "2026-05-22",
})
db.update_trade_close("DIAAA", {"close_level": 18090.0, "profit_loss": 90.0})
db.insert_reward(trade_id, {"score_after": 58.0, "win_loss": "WIN"})
db.get_current_score()                    # 58.0
db.get_risk_level()                       # "AGGRESSIV"

sm = StateManager("data/state")
sm.save_candidates([{"epic": "IX.D.DAX.IFMM.IP", "direction": "CALL", "confidence": 72}])
sm.load_candidates()                      # [] if expired/empty/missing
```

## Integration contract (phase isolation)

Phase 2 **never imports `broker_wrapper`**. Callers pass plain dicts — typically
`Envelope.data` or `model.to_dict()` from Phase 1. This keeps the layer runnable
offline (tests, analysis, future backtesting) with no broker connection.

## Running tests

```bash
pytest tests/ -v   # 59 tests: migrations(9) · db(31) · state(19) — no network, temp SQLite/dirs
```

## Conventions

- All timestamps: ISO 8601 UTC, ms precision, `Z` suffix.
- All money: REAL + explicit `currency` column.
- Migrations are additive only (`ALTER TABLE ADD COLUMN` / new tables) — never
  destructive. New version → new `migrations/NNN_*.sql` file.
- A subtask isn't done until `pytest tests/ -v` is green.
