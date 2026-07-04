-- Phase 9 (V2 — Foundation) — the autonomous instrument universe (version 4)
-- Additive only. Adds one new table, `instrument_universe`, and its status index.
--
-- WHY (docs/concepts/phase9_v2_foundation_plan(1).md §4 Step 1):
-- Phase 4's `EXTENDED_UNIVERSE` (`phase4_research/research/models.py`) is a hand-curated
-- Python tuple — every new instrument needed a manual code edit + P3 ticker-map entry +
-- Sizing sanity check (the v1.5 hotfix arc). This migration gives the Phase 9 discover→
-- verify→promote pipeline (`phase9_universe/universe/`) a persistent home so that path can
-- run without a code edit per instrument. `EXTENDED_UNIVERSE` becomes a one-time seed
-- (`source='curated'`) into this table, not a runtime source of truth going forward.
--
-- `point_value`/`point_value_source` are nullable by design: activation requires a
-- deterministically resolved point_value (Decision D6) — a NULL here means "not yet
-- provable", not "zero". `checks_json` holds the last verify-instrument verdict (JSON) so
-- an operator/UI can see *why* a row is in its current status without re-running a probe.
-- `fail_count`/`data_degraded` are separate signals on purpose: IG-side failures count
-- toward demotion (`fail_count`), yFinance-side degradation never does (`data_degraded`,
-- Konzept C3 — reduced-signal is tolerated, not demotion-worthy).
--
-- Status values (`status`): 'discovered' | 'verified' | 'active' | 'quarantined' | 'retired'.
-- `source` values: 'curated' | 'research_promoted'.
--
-- No existing table touched. No AI in this layer (Bauprinzip) — this is pure storage for a
-- 100%-code discovery/promotion pipeline.

CREATE TABLE IF NOT EXISTS instrument_universe (
    epic                TEXT PRIMARY KEY,
    name                TEXT,
    yf_ticker           TEXT,
    volume_proxy        TEXT,
    point_value         REAL,            -- NULL until deterministically resolved (D6)
    point_value_source  TEXT,            -- 'ig_fields' | 'name_lotsize_agree' | 'curated_confirmed' | NULL
    min_deal_size       REAL,
    currency            TEXT NOT NULL,
    status              TEXT NOT NULL,   -- 'discovered'|'verified'|'active'|'quarantined'|'retired'
    source              TEXT NOT NULL,   -- 'curated'|'research_promoted'
    checks_json         TEXT,            -- last verify-instrument verdict (JSON)
    fail_count          INTEGER NOT NULL DEFAULT 0,
    data_degraded       INTEGER NOT NULL DEFAULT 0,  -- yF-side degraded, NEVER demotion-triggering
    last_verified_at    TEXT,
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_instrument_universe_status ON instrument_universe(status);
