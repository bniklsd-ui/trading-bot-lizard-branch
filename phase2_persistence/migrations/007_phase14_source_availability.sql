-- Phase 14 (Discovery-Then-Deterministic) — `instrument_source_availability` (version 7)
-- Additive only. The cross-product IG-Epic × Source × Resolution — answers Phase-14
-- Plan D1/D2/D8 (`docs/concepts/phase14_discovery_plan.md`):
--
-- D2 — `source_symbol TEXT`: the Concept-Schema-Skizze (§2.2) had no column for the
-- source's own symbol, which meant the table could NOT replace `EPIC_MAP` and the Phase
-- Done-Kriterium was structurally unreachable. `source_symbol` carries the Capital.com
-- Kürzel ("DE40"), yFinance-Symbol ("^GDAXI"), or NULL when the source uses the IG
-- epic itself (derived 'ig' rows — D6). `instrument_universe.yf_ticker` becomes exactly
-- `source_symbol WHERE source='yf'`.
--
-- D8 — the table is a *Fakten* table (what can who), NOT a *Präferenz* table (which
-- source first). Ranking stays the consumer's job.
--
-- D17 — the table does NOT enforce `KNOWN_SOURCES` membership. A source that exists
-- here but not in `KNOWN_SOURCES` may be DISCOVERED, but it must NEVER be written into
-- the bar archive (`BarArchive.insert_bars` is the gatekeeper — `KNOWN_SOURCES` stays
-- the gate, per Phase-12 D4). Discovery of new sources = DB-row + (later) an
-- `KNOWN_SOURCES` edit; never DB-row alone.
--
-- D18 — `status` vocabulary is identical to `KNOWN_DATA_SOURCE_STATUSES`
-- (Phase-12 D7): 'ok' | 'unverified' | 'no_source' | 'no_intraday_source' |
-- 'mismatch' | 'stale_source'. Same words, same meanings. The yF projection (A4) is
-- a copy, not a translation — no mapping table between two vocabularies, no drift.
--
-- No FOREIGN KEY on `epic` — deliberate. Audit this against `phase2_persistence/migrations/001..006`
-- and `phase9_universe/universe/store.py:53` before changing: 0 FKs in 001..006,
-- `UniverseStore` opens without `PRAGMA foreign_keys = ON`. An unenforced FK is
-- documentation that pretends to be a constraint. Additionally correct in intent:
-- an availability row for an epic that gets retired later is *history*, not corruption.
--
-- `origin` vocabulary ('discovery'|'registry'|'derived'|'operator') is module-side in
-- `source_registry/models.py`. SQLite does not enforce it; `SourceAvailabilityStore.upsert`
-- is the gatekeeper on writes (D6: 'ig' is always 'derived'; A4: 'yf' is always 'registry').
--
-- BACKFILL rationale (Block-C-Re-Plan §2 nennt genau diesen Schritt): the
-- `instrument_universe` row IS, per definition, an IG epic — so the IG projection
-- needs no migration; the yF projection DOES, because the only writer of `yf_ticker`
-- (`UniverseStore.set_symbol`) is reached by `SymbolResolver.resolve_epic` in 6 of 8
-- branches (`symbols.py:194-199, 207-210, 213-214, 219-220, 222-223, 229-230`), and
-- the three `SUN*` epics stand on their Zielstatus today (Plan §2.2 — Plan-14 §5.1).
-- Without this migration they would NEVER get a projection row, regardless of how
-- often the resolver runs. INSERT … SELECT carries `yf_ticker` 1:1 into the new
-- table for every existing row, `origin='registry'`. This same SELECT is the proof
-- (test 11 in §6 A2): the five `(yf,'ok')` rows land atomically with the migration,
-- before any new code can introduce drift.
CREATE TABLE IF NOT EXISTS instrument_source_availability (
    epic              TEXT NOT NULL,
    source            TEXT NOT NULL,   -- 'ig'|'yf'|'ls'|'capital'|… (D17: table gattet NICHT, Archiv-Schreibpfad gattet)
    resolution        TEXT NOT NULL,   -- '1m'|'5m'|'1h'|'1d'
    source_symbol     TEXT,            -- D2: 'DE40' | '^GDAXI' | NULL (Quelle nutzt die Epic selbst)
    status            TEXT NOT NULL,   -- D18: identisch zu KNOWN_DATA_SOURCE_STATUSES
    origin            TEXT NOT NULL,   -- 'discovery'|'registry'|'derived'|'operator'
    history_min_days  INTEGER,
    latency_min       INTEGER,
    last_verified_utc TEXT NOT NULL,
    notes             TEXT,
    PRIMARY KEY (epic, source, resolution)
);

CREATE INDEX IF NOT EXISTS idx_isa_source_status
    ON instrument_source_availability(source, status);

-- Backfill: one row per existing `instrument_universe` row, source='yf',
-- `status` taken 1:1 from `data_source_status` (the two vocabularies are identical —
-- D18), `origin='registry'` (D4: the registry row is the source of truth; this is
-- a projection, not a separate writer), `last_verified_utc` falls back to
-- `symbol_checked_at` → `updated_at` (the resolver-set timestamp, or the row's last
-- touch). `source_symbol = yf_ticker` (the 1:1 identity D2 promises).
INSERT OR IGNORE INTO instrument_source_availability
    (epic, source, resolution, source_symbol, status, origin, last_verified_utc, notes)
SELECT epic, 'yf', '1m', yf_ticker, data_source_status, 'registry',
       COALESCE(symbol_checked_at, updated_at),
       'backfilled from instrument_universe by migration 007'
FROM instrument_universe;
