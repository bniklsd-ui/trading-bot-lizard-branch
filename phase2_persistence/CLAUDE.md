# persistence — Claude Code context

## Project
Phase 2 of a DAX intraday trading bot. This package is the data/persistence layer.
Full design and all decisions: see `../docs/concepts/phase2_persistence_konzept.md`.

## Stack
- Python 3.11+ · `sqlite3` + `json` (stdlib) — **no runtime dependencies**
- `pytest` for tests (mocked/local only, no network)

## Commands
```bash
pip install -r requirements.txt        # only pytest (dev)
pytest tests/ -v                       # 59 unit tests, no network
python scripts/init_db.py              # create data/ dirs, migrate, seed (idempotent)
```
Run pytest from this directory (`phase2_persistence/`) — `tests/__init__.py` plus
the package layout put `persistence` on the path the same way Phase 1 does.

## Architecture
Two stores. **100% deterministic code — no LLM calls anywhere in Phase 2.**
- `Database` (`persistence/db.py`) — typed `sqlite3` CRUD for all 6 tables.
  `row_factory = sqlite3.Row`, `PRAGMA foreign_keys = ON` (cascade deletes).
- `StateManager` (`persistence/state.py`) — JSON read/write + TTL; atomic writes
  (temp file + `os.replace`).
- `migrations.py` — self-written SQL-file runner; version tracked in
  `_schema_version`; idempotent. DDL lives **only** in `migrations/*.sql`.
- `schema.py` — thin: just the `_schema_version` DDL + migrations dir path.
- `defaults.py` — seed rows for `ig_config_state` (`INSERT OR IGNORE`).
- `timeutil.py` — `utc_iso_now()` / `parse_iso()`, duplicated from Phase 1 (no
  cross-phase import — phase isolation).

## Runtime data location
- DB: `<repo_root>/data/trading_bot.sqlite`
- JSON state: `<repo_root>/data/state/{ig_state,ig_config,turbo_candidates}.json`
- Both gitignored; created by `init_db.py`; paths configurable via its flags.

## Key design decisions
- `get_current_score()` reads the latest `reward_pts.score_after`; **default 50.0**
  when no rewards exist yet.
- `get_risk_level()`: `> 50 → "AGGRESSIV"`, else `"KONSERVATIV"`. The neutral
  start score (50) maps to KONSERVATIV, matching the seeded `risk_level` default.
- `ig_config_state` (mutable DB key-value) ≠ `ig_config.json` (static config file).
- V2 tables (`market_regime_snapshots`, `decision_context`) are created empty;
  Phase 9 fills them.

## Conventions
- All timestamps ISO 8601 UTC, ms precision, `Z` suffix.
- All money REAL + explicit `currency` column.
- Inserts use per-table column whitelists + parameterized values (no string-built
  column names from caller input).
- Tests use temp-file SQLite / temp dirs — no network, no real credentials.

## Don't
- Don't import `broker_wrapper` here — Phase 2 receives plain dicts only.
- Don't put DDL in `schema.py` or `db.py` — migrations own the schema.
- Don't write destructive migrations — additive only (`ADD COLUMN` / new tables).
- Don't add an LLM call anywhere — Phase 2 is 100% code.
- Don't consider a subtask done until `pytest tests/ -v` is green.

## After every task or subtask
- Add `pytest` tests in `tests/` for every new function (no live calls).
- Update `../docs/concepts/phase2_persistence_konzept.md` if a design decision changed.
- If the session ends mid-task, append a `## Session stopped` block (below).
