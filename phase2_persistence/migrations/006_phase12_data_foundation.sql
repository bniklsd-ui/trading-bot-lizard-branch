-- Phase 12 (Datenfundament) — Registry-Erweiterung + Mess-Provenienz (version 6)
-- Additive only. Answers Decision D5/D7 (docs/concepts/phase12_data_foundation_plan.md §4.2):
-- `instrument_universe` becomes the one source of truth for instrument facts — symbol
-- mapping is derived + code-verified (SymbolResolver) instead of declared across three
-- divergent tables, and "no source" becomes a typed, loud state instead of a silent NULL.
--
-- `data_source_status` starts 'unverified' on every row (existing and new) — correct:
-- nothing is verified until the resolver has run against it at least once. Measurement
-- (paper/shadow) is gated on 'ok' via `UniverseStore.measurable_universe()`.
--
-- `resolution_source` on `paper_trades` records provenance per resolved trade ('yf'|'ig'|
-- 'ig+yf'|'ls'); existing rows keep NULL (honest: provenance unknown for pre-Phase-12
-- trades). Consumer is Step 4 (BarService/tracker rewire) — landing the column here keeps
-- the migration additive-only and the schema self-consistent one step ahead of its writer.
ALTER TABLE instrument_universe ADD COLUMN data_source_status TEXT NOT NULL DEFAULT 'unverified';
ALTER TABLE instrument_universe ADD COLUMN symbol_source TEXT;       -- 'seed'|'resolver'|'operator'|NULL
ALTER TABLE instrument_universe ADD COLUMN symbol_checked_at TEXT;
ALTER TABLE paper_trades ADD COLUMN resolution_source TEXT;          -- 'yf'|'ig'|'ig+yf'|'ls'|NULL(legacy)
