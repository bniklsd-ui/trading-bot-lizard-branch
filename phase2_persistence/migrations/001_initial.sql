-- Phase 2 — initial schema (version 1)
-- All six tables + indexes. V2 tables (market_regime_snapshots, decision_context)
-- are created empty here; Phase 9 fills them. Idempotent: every CREATE uses
-- IF NOT EXISTS so re-applying is harmless.

-- ----------------------------------------------------------------------------
-- Table 1: trade_outcomes — every completed (or open) trade.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trade_outcomes (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Broker identifiers
    deal_id          TEXT NOT NULL,
    deal_reference   TEXT,                             -- client-supplied idempotency key
    epic             TEXT NOT NULL,
    broker           TEXT NOT NULL DEFAULT 'ig',

    -- Trade parameters
    direction        TEXT NOT NULL CHECK(direction IN ('BUY','SELL')),
    size             REAL NOT NULL CHECK(size > 0),
    open_level       REAL NOT NULL,
    close_level      REAL,                             -- NULL while open
    currency         TEXT NOT NULL,

    -- Timestamps
    open_ts          TEXT NOT NULL,                    -- ISO 8601 UTC
    close_ts         TEXT,                             -- NULL while open
    hold_duration_min REAL,                            -- computed at close

    -- Outcome
    profit_loss      REAL,                             -- in `currency`
    status           TEXT NOT NULL CHECK(status IN ('OPEN','CLOSED','CANCELLED')),

    -- Context (filled by Phase 4+)
    research_confidence REAL,                          -- LLM confidence score (0-100)
    gate_path        TEXT,                             -- JSON: gates passed/blocked
    session_date     TEXT NOT NULL,                    -- "2026-05-21" for daily aggregation

    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_trade_outcomes_deal_id ON trade_outcomes(deal_id);
CREATE INDEX IF NOT EXISTS idx_trade_outcomes_session_date ON trade_outcomes(session_date);
CREATE INDEX IF NOT EXISTS idx_trade_outcomes_epic ON trade_outcomes(epic);
CREATE INDEX IF NOT EXISTS idx_trade_outcomes_status ON trade_outcomes(status);

-- ----------------------------------------------------------------------------
-- Table 2: reward_pts — score delta per trade (Phase 7 writes; Phase 2 creates).
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reward_pts (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id              INTEGER NOT NULL REFERENCES trade_outcomes(id) ON DELETE CASCADE,

    -- Outcome-based scoring (current system)
    outcome_score_delta   REAL NOT NULL DEFAULT 0.0,
    score_after           REAL NOT NULL,               -- accumulated score after this trade
    win_loss              TEXT NOT NULL CHECK(win_loss IN ('WIN','LOSS','BREAKEVEN')),
    pnl_raw               REAL,                        -- copied from trade_outcomes for fast access

    -- V2 reform: process-quality score (Phase 9 fills; Phase 2 creates)
    process_score_delta   REAL,                        -- NULL until Phase 9 active
    veto_trigger_count    INTEGER,                     -- how many VETOs fired
    gate_fail_count       INTEGER,                     -- how many gates blocked
    debate_confidence     REAL,                        -- Judge confidence from Bull/Bear
    spread_at_entry_pct   REAL,                        -- spread at entry time

    calculated_at         TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reward_pts_trade_id ON reward_pts(trade_id);

-- ----------------------------------------------------------------------------
-- Table 3: trade_lessons — lessons extracted by Phase 7 (Longterm Brain).
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trade_lessons (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id             INTEGER NOT NULL REFERENCES trade_outcomes(id) ON DELETE CASCADE,

    -- Lesson content
    lesson_text          TEXT NOT NULL,                -- LLM-extracted learning
    market_context_json  TEXT,                         -- JSON: market conditions at trade time

    -- Quality indicators
    relevance_score      REAL,                         -- 0.0-1.0, initially NULL
    used_in_research     INTEGER NOT NULL DEFAULT 0,   -- count: times used as context
    last_used_ts         TEXT,

    -- V2: embedding (Phase 9)
    embedding_json       TEXT,                         -- NULL until vector store active
    embedding_model      TEXT,                         -- model version for invalidation

    extracted_at         TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_trade_lessons_trade_id ON trade_lessons(trade_id);
CREATE INDEX IF NOT EXISTS idx_trade_lessons_relevance ON trade_lessons(relevance_score);

-- ----------------------------------------------------------------------------
-- Table 4: ig_config_state — operational key-value state across sessions.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ig_config_state (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,              -- always JSON-serialized
    updated_at TEXT NOT NULL,
    note       TEXT                        -- optional description
);

-- ----------------------------------------------------------------------------
-- Table 5: market_regime_snapshots (V2 — Phase 9). Created empty.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS market_regime_snapshots (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id         INTEGER NOT NULL REFERENCES trade_outcomes(id) ON DELETE CASCADE,

    -- Market context
    volatility_pct   REAL,                -- implied or historical volatility
    spread_pct       REAL,                -- spread at snapshot time
    drift_pct        REAL,                -- open-to-now drift% from Phase 1 filter
    volume_z_score   REAL,                -- volume anomaly (standard deviations)
    time_of_day_h    REAL,                -- decimal hours (09.5 = 09:30)
    market_status    TEXT,                -- TRADEABLE / AUCTION etc.

    snapshot_ts      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_market_regime_trade_id ON market_regime_snapshots(trade_id);

-- ----------------------------------------------------------------------------
-- Table 6: decision_context (V2 — Phase 9). Full AI decision context per trade.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS decision_context (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id            INTEGER NOT NULL REFERENCES trade_outcomes(id) ON DELETE CASCADE,

    -- Bull/Bear/Judge
    bull_summary        TEXT,
    bear_summary        TEXT,
    judge_reasoning     TEXT,
    debate_rounds       INTEGER,          -- number of debate rounds (1-5)
    judge_confidence    REAL,             -- 0.0-1.0

    -- VETO details
    veto_factors_json   TEXT,             -- JSON: which VETOs triggered/passed
    pre_trade_checks_json TEXT,           -- JSON: all pre_trade_option_check() values

    -- Council (optional, Phase 9)
    council_verdict     TEXT,             -- SOLIDE / FRAGWUERDIG / KRITISCH
    council_summary     TEXT,

    stored_at           TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_decision_context_trade_id ON decision_context(trade_id);
