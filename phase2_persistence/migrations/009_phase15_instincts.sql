-- Phase 15 Block C — `instincts` table (version 9, 2026-09-03)
-- Additive only. Layer for the Instinct-ECC (Plan §6 Block C).
--
-- Schema wörtlich nach `docs/concepts/phase7_reward_concept.md §7b` (Phase 7
-- deferred this to a later step — that step is now Phase 15, Plan §6 Block C):
--
--   trigger / domain ∈ {entry, exit, sizing, timing} /
--   confidence / evidence_trade_ids[] / contradictions_trade_ids[]
--
-- Lifecycle status (Plan §6 C1 + §1 P10 — Promotion per Default AUS, gated auf
-- n_closed ≥ instinct_n_min):
--
--   proposed → validated → promoted (deterministischer Code, VETO-Eintritt)
--                     ↘ refuted (Code-Beweis: contradictions überwiegen evidence)
--                promoted → archived (Pruning durch Validator / Operator)
--
-- `evidence_trade_ids_json` und `contradictions_trade_ids_json` sind
-- JSON-Listen von `trade_outcomes.id`-Werten. Bewusst **kein** FK-Constraint:
-- Instincts sind ein **Aggregation-Layer**, keine Punkt-Referenz — eine FK
-- würde Promotion/Archive-Logik mit ON-DELETE-CASCADE verkoppeln, was die
-- Promotion-Gates (`instinct_n_min`, `enable_instinct_promotion`) aushebelt.
-- Der Validator-Pfad (Phase 15 C2) joint manuell gegen `trade_outcomes`.
--
-- `validated_utc` / `promoted_utc` / `archived_utc` sind nullable und werden
-- jeweils nur beim Status-Übergang gesetzt (siehe `update_instinct_status` in
-- `phase2_persistence/persistence/db.py`). `proposed` und `refuted` haben
-- kein dediziertes Timestamp — `created_utc` (für `proposed`) und die letzte
-- Status-Update-Zeit (per Code, nicht in der Tabelle) reichen.
--
-- `confidence` ist `REAL` und initial NULL — der Extractor (Phase 15 C2) füllt
-- ihn; NULL bedeutet „noch nicht bewertet" und wird vom Validator als
-- „unpromotable" behandelt.
--
-- Migration-Runner (`phase2_persistence/persistence/migrations.py`) macht
-- idempotent: `_schema_version`-Guard, `_find_pending` scannt nach
-- `^\d+_.*\.sql$`. Fresh-DB erreicht nach dieser Migration `version = 9`.

CREATE TABLE IF NOT EXISTS instincts (
    id                              INTEGER PRIMARY KEY AUTOINCREMENT,
    trigger                         TEXT NOT NULL,
    domain                          TEXT NOT NULL
                                    CHECK(domain IN ('entry','exit','sizing','timing')),
    confidence                      REAL,
    evidence_trade_ids_json         TEXT,
    contradictions_trade_ids_json   TEXT,
    status                          TEXT NOT NULL DEFAULT 'proposed'
                                    CHECK(status IN ('proposed','validated','refuted','promoted','archived')),
    created_utc                     TEXT NOT NULL,
    validated_utc                   TEXT,
    promoted_utc                    TEXT,
    archived_utc                    TEXT
);

CREATE INDEX IF NOT EXISTS idx_instincts_status ON instincts(status);
CREATE INDEX IF NOT EXISTS idx_instincts_domain ON instincts(domain);
CREATE INDEX IF NOT EXISTS idx_instincts_created_utc ON instincts(created_utc);
