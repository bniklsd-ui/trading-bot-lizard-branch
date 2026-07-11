---
status: closed-phase
purpose: Phase-2 head — SQLite/JSON persistence layer, migrations, whitelist
read-when: working in phase2_persistence/ — read this head + its newest Session-stopped block first
detail: L2
up: ../CLAUDE.md
down:
  - ./README.md
  - ../docs/concepts/phase2_persistence_konzept.md   # full concept/plan snapshot (L3)
updated: 2026-07-06
---
# persistence — Claude Code context

## Project
Phase 2 of a DAX intraday trading bot. This package is the data/persistence layer.
Full design and all decisions: see `../docs/concepts/phase2_persistence_konzept.md`.

**Status:** ✅ live-verified 2026-05-22 (pytest + `scripts/live_test.py`), merged to `main`.

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
- `market_regime_snapshots`/`decision_context`: created empty + `trade_id`-scoped in 001
  (Phase 9 was meant to fill them, never did). **Migration 005 (2026-07-11, Phase 10 V3)
  DROP+CREATE'd both** to an epic-scoped schema with no `trade_id` FK (see the Don't-list
  exception above) — the real writer is `phase10_v3/market_context/writer.py` (WE 2),
  `Database` no longer has `insert_regime_snapshot`/`insert_decision_context`.

> 🔁 **Phase-8 v1.5-hotfix edit (2026-07-01, Issue A — lesson provenance, code = source of truth):**
> new **read-only** method `get_recent_lessons_for_prompt(n=5, *, min_hold_min=None,
> quarantine_before=None, exclude_provenance=())` — a parameterised sibling of `get_recent_lessons`
> (which is **untouched**) that the P4 research prompt uses to drop verification-trade lessons. Filters
> **in the query** (newest N *survivors*): NULL-safe `json_extract(market_context_json, '$.provenance')
> IS NOT <tag>` (precise; needs SQLite JSON1, bundled in 3.11+), a `hold_duration_min` subquery
> (fallback, NULL hold → kept), and an `extracted_at` cutoff (reversible reset). **No schema change, no
> migration.** P2 stays a dumb parameterised store — the excluded values + thresholds are the caller's
> (P4) policy. +5 tests (**62 → 67**). Detail: `docs/concepts/phase8_v1.5_hotfix_plan.md` Step 4.

> 🔁 **Phase-8 v1.6-hotfix edit (2026-07-02, Cause A part 2 — trade-history provenance, code = source
> of truth):** the v1.5 fix above cleaned the *lessons* channel; `build_context` (P4) also reads
> `get_recent_trades` — a **second, separate** channel into the same research prompt — which stayed
> unfiltered. A live v1.6 run showed the LLM's abstain reasoning citing fake "three consecutive
> losses" from three seeded verification trades read straight off `trade_outcomes`. **Fix (new,
> real schema column this time — Nikinger decision, unlike the JSON-blob-only lesson fix):**
> `migrations/003_phase8_trade_provenance.sql` adds `trade_outcomes.provenance TEXT` (fresh DB now
> reaches **version 3**); `_TRADE_COLUMNS += ("provenance",)`; new **read-only** sibling method
> `get_recent_trades_for_prompt(n=8, *, min_hold_min=None, quarantine_before=None,
> exclude_provenance=())` mirrors `get_recent_lessons_for_prompt` exactly, but against the real
> `provenance` column (no `json_extract` needed — it's a column, not a JSON blob field) —
> `get_recent_trades` itself stays untouched for other callers. Three signals, same precision order:
> `provenance IS NOT <tag>` (NULL-safe), `hold_duration_min` fallback (catches trades opened before
> migration 003 — NULL hold i.e. still-open trades are kept, fail-open), `open_ts` quarantine cutoff.
> +8 tests (**67 → 75**: 1 migration-version-3 assertion + 1 column-presence test + 5
> `get_recent_trades_for_prompt` filter cases + 1 provenance round-trip + 1 NULL-default case).
> Detail: `docs/concepts/phase8_v1.6_hotfix_plan.md` §6 + `phase8_scheduler/CLAUDE.md` →
> `## Session stopped — 2026-07-02 (v1.6-Hotfix: Cause A part 2)`.

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
  **One documented exception (migration 005, 2026-07-11, Nikinger-approved):**
  `market_regime_snapshots`/`decision_context` were DROP+CREATE'd, not ALTER'd — both
  were empty `trade_id NOT NULL REFERENCES trade_outcomes(id)` placeholders (001) that
  V3's NO_TRADE-scoped snapshots cannot satisfy (SQLite can't relax a NOT NULL FK via
  `ALTER TABLE` short of a full rebuild, which is DROP+CREATE anyway); verified 0 rows
  in production and no live-path reader/writer (only `tests/test_db.py` +
  `scripts/archive_verification_trades.py` referenced them) before dropping. Treat this
  as the ceiling for when a destructive migration is acceptable here, not a precedent
  for convenience — the default stays additive-only.
- Don't add an LLM call anywhere — Phase 2 is 100% code.
- Don't consider a subtask done until `pytest tests/ -v` is green.

## After every task or subtask
- Add `pytest` tests in `tests/` for every new function (no live calls).
- Update `../docs/concepts/phase2_persistence_konzept.md` if a design decision changed.
- If the session ends mid-task, append a `## Session stopped` block (below).
