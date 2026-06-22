-- Phase 7 — reward-layer columns (version 2)
-- Additive only. Adds the three columns the reward layer already writes but the
-- v1 schema lacks: initial_risk + account on trade_outcomes (Decision G + the
-- 2026-06-18 operator decision to persist the demo/live tag) and r_multiple on
-- reward_pts. The reward whitelists in persistence/db.py are extended in the same
-- change so insert_trade/insert_reward stop silently dropping these keys.
--
-- NOTE: SQLite `ALTER TABLE ... ADD COLUMN` is NOT self-`IF NOT EXISTS`. Unlike
-- the `CREATE TABLE IF NOT EXISTS` statements in 001, these ALTERs are not
-- individually re-runnable. Idempotency is provided by the runner's
-- `_schema_version` guard (persistence/migrations.py): version 2 is applied
-- exactly once. Re-running run_migrations after this is a no-op.

ALTER TABLE trade_outcomes ADD COLUMN initial_risk REAL;   -- |entry - stop| * size * point_value
ALTER TABLE trade_outcomes ADD COLUMN account      TEXT;   -- 'demo' | 'live' (edge-metric filter)
ALTER TABLE reward_pts     ADD COLUMN r_multiple   REAL;   -- profit_loss / initial_risk
