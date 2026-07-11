-- Phase 10 (V3) — Abstain-Lessons + Persistenz-Reform + Paper-Trades (version 5)
-- Adds `abstain_records` + `paper_trades` (new). DROP+CREATEs `market_regime_snapshots`
-- and `decision_context` (schema change — see WHY below; this is the one deliberate
-- exception to this package's "additive only" migration rule, Nikinger-approved
-- 2026-07-11, documented in `phase2_persistence/CLAUDE.md`'s Don't-list).
--
-- WHY the DROP+CREATE (docs/concepts/phase10_v3_plan.md §6.3 + phase10_v3/CLAUDE.md
-- "Verified anchors" #3):
-- `market_regime_snapshots`/`decision_context` were created empty in 001_initial.sql,
-- scoped to `trade_id INTEGER NOT NULL REFERENCES trade_outcomes(id)`. V3 needs a
-- snapshot/context row for EVERY NO_TRADE cycle (abstains, gate/VETO fails) — the vast
-- majority of cycles never produce a `trade_outcomes` row, so the NOT NULL FK is
-- structurally incompatible. SQLite cannot drop/relax a column's NOT NULL/FK via
-- `ALTER TABLE` without a full table rebuild (i.e. this is DROP+CREATE either way).
-- Verified before this migration: 0 rows in production in either table; the only
-- references anywhere in the repo are `tests/test_db.py` and
-- `scripts/archive_verification_trades.py` (no live production path writes to them).
-- No data loss. New schema is epic-scoped (`snapshot_id`/`context_id` TEXT PK, no
-- `trade_id` requirement), links `market_regime_snapshots.decision_context_id` to
-- `decision_context.context_id` (nullable), and `decision_context.deal_id`/
-- `abstain_record_id` (both nullable) record whichever outcome actually happened.
--
-- Table 1: abstain_records — one row per NO_TRADE cycle classification (S1 spec,
-- phase10_v3/abstain_lessons/models.py AbstainRecord). Columns match
-- AbstainRecord.to_row() order exactly.
CREATE TABLE IF NOT EXISTS abstain_records (
    record_id           TEXT PRIMARY KEY,
    created_utc         TEXT NOT NULL,
    epic                TEXT,                          -- NULL before Gate 2 (no candidate yet)
    stage               TEXT NOT NULL,                  -- research_empty|gate|veto|debate|error
    reason              TEXT NOT NULL,                  -- one of 12 AbstainReason values
    detail              TEXT NOT NULL DEFAULT '',
    context_json        TEXT NOT NULL DEFAULT '{}',
    lesson              TEXT,                            -- NULL until reflect_abstain succeeds
    lesson_extracted    INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_abstain_records_created_utc ON abstain_records(created_utc);
CREATE INDEX IF NOT EXISTS idx_abstain_records_reason ON abstain_records(reason);

-- Table 2: paper_trades — Both-Sides-Shadow-Tracking + optional Council-Paper-Call
-- (V3-D6/D7). Schema lands now (WE 1); the engine that writes rows is WE 2 — the table
-- exists ahead of its writer so Migration 005 stays the single V3 schema migration
-- (V3-D9: "eine Migration mit allen neuen Tabellen"). Hard separation from real trading:
-- never joined with `trade_outcomes`/`reward_pts`, never counted in Confidence-N.
CREATE TABLE IF NOT EXISTS paper_trades (
    paper_id            TEXT PRIMARY KEY,
    abstain_record_id   TEXT NOT NULL,
    variant             TEXT NOT NULL,                  -- SHADOW_BUY|SHADOW_SELL|COUNCIL_PICK
    epic                TEXT NOT NULL,
    direction           TEXT NOT NULL,                  -- BUY|SELL
    created_utc         TEXT NOT NULL,
    entry_level         REAL NOT NULL,
    stop_distance       REAL NOT NULL,
    limit_distance      REAL,
    time_stop_utc       TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'OPEN',   -- OPEN|RESOLVED|EXPIRED_UNRESOLVED
    resolved_utc        TEXT,
    exit_reason         TEXT,                            -- SL|TP|TIME_STOP
    exit_level          REAL,
    pnl_points           REAL,
    r_multiple          REAL,
    council_confidence  INTEGER,
    lesson              TEXT,
    lesson_extracted    INTEGER NOT NULL DEFAULT 0,
    context_json        TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_paper_trades_status ON paper_trades(status);
CREATE INDEX IF NOT EXISTS idx_paper_trades_created_utc ON paper_trades(created_utc);

-- Table 3/4: market_regime_snapshots + decision_context — DROP the FK-scoped v1
-- placeholders (see WHY above), CREATE the epic-scoped v3 versions. `decision_context`
-- first (market_regime_snapshots.decision_context_id references it).
DROP TABLE IF EXISTS market_regime_snapshots;
DROP TABLE IF EXISTS decision_context;

CREATE TABLE IF NOT EXISTS decision_context (
    context_id          TEXT PRIMARY KEY,
    created_utc         TEXT NOT NULL,
    epic                TEXT,
    candidate_json       TEXT,
    bull_summary        TEXT,                            -- extracted from DebateOutcome.transcript
    bear_summary        TEXT,
    judge_decision       TEXT,                            -- TRADE|ABSTAIN
    judge_confidence     INTEGER,
    rounds_used          INTEGER,
    veto_results_json    TEXT,
    gate_results_json    TEXT,
    outcome              TEXT,                            -- TRADE|NO_TRADE
    deal_id              TEXT,                            -- set only when outcome=TRADE
    abstain_record_id    TEXT                             -- set only when outcome=NO_TRADE
);

CREATE INDEX IF NOT EXISTS idx_decision_context_created_utc ON decision_context(created_utc);

CREATE TABLE IF NOT EXISTS market_regime_snapshots (
    snapshot_id           TEXT PRIMARY KEY,
    created_utc           TEXT NOT NULL,
    epic                  TEXT,
    spread_pct            REAL,
    atr_points            REAL,                          -- NULL if bars unavailable
    range_pct             REAL,                          -- NULL if bars unavailable
    time_bucket           TEXT,                           -- OPEN|MORNING|LUNCH|AFTERNOON|CLOSE
    regime_tag            TEXT,                           -- observe-only (V3-D4), NULL if unclassified
    data_source           TEXT,                           -- ig_bars|yfinance|quote_only
    degraded              INTEGER DEFAULT 0,
    decision_context_id   TEXT                            -- nullable link to decision_context
);

CREATE INDEX IF NOT EXISTS idx_market_regime_snapshots_created_utc ON market_regime_snapshots(created_utc);
