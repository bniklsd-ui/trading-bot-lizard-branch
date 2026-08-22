# phase14_discovery — Discovery-Then-Deterministic

Phase 14 turns "which source can serve epic X?" from a hardcoded dict in the
code into a row in the database. Each source exposes its own delivery spectrum
as a `SourceProfile`; the cross-product IG-Epic × Source × Resolution lives
in `instrument_source_availability` (Migration 007); consumers read the table
instead of the code — and `EPIC_MAP` disappears.

Mission (one line): **was eine Quelle kann, sagt die Quelle — nicht der
Konsument.**

Full execution-ready plan (locked decisions **D1–D20**, Block 0/A/B/C/D step
sequence with verbatim anchors, acceptance **A1–A8**, complete drift list):
[`docs/concepts/phase14_discovery_plan.md`](../docs/concepts/phase14_discovery_plan.md).
Phase head / session log: [`CLAUDE.md`](./CLAUDE.md).

## Package: `source_registry`

> **Block 0.4 (2026-08-22): Skeleton.** No functional code yet. This table is
> filled in Block D against the as-built stand (test counts from the final
> sweep, not estimates).

| Module | Responsibility | Status |
|---|---|---|
| `models.py` | `SourceAvailability` + `SourceProfile` dataclasses + `Source` Protocol + `origin`-Vokabular | ⬜ Block A2/A3 |
| `store.py` | `SourceAvailabilityStore` — der einzige Zugriff auf Migration 007 (eigene `sqlite3`-Connection, Phasen-Isolation) | ⬜ Block A2 |
| `sources.py` | `IGDerivedSource` (D6: jede Epic ⇒ abgeleitete Zeile, **null IG-Punkte**), `LSStaticSource`, `RegistryYFSource` — alle drei ohne Netz | ⬜ Block A3 |
| `arm.py` | Scharf-Flag `data/state/DISCOVERY_ARMED` (Muster `killswitch.py`, sichere Richtung umgedreht: fail-soft + `False` als Default) | ⬜ Block C1 |
| `run.py` | Daemon (Muster `data_foundation/run.py`: PID-File, `SIGTERM`/`SIGINT` → graceful, `--once`) | ⬜ Block C2 |
| `scripts/run_discovery.sh` | Start-Wrapper (Muster `run_recorder.sh`) | ⬜ Block C4 |

**Bauprinzip:** zero new AI. Source discovery, symbol mapping, availability
evaluation, scharfschalt logic — deterministic code, see root `CLAUDE.md`.
Whoever reaches for an LLM call here → **stop**, that is code.

**Dreifacher Kontingent-Deckel** (siehe Phasenkopf §Rahmen):
1. **strukturell** — Discovery ruft nie `/prices`, nie `search_markets` (D6);
   IG-Zeile wird abgeleitet, testbar mit einem Broker-Fake, dessen jede
   Methode wirft.
2. **zwei getrennte Kontingente** — 10 000-Punkte-Wochenfenster (`/prices`) und
   API-Key-Allowance (30 req/min) werden beide nicht berührt, weil IG gar nicht
   gerufen wird.
3. **Ledger-`spend_kind='discovery'`** — jeder Fetch, der doch Netz kostet (heute
   nur Capital.com), wird im existierenden `source_spend`-Ledger gebucht.

Cross-phase pieces this phase edits live in
`phase2_persistence/migrations/` (Migration 007),
`phase9_universe/universe/{models,store}.py` (`DS_STALE_SOURCE` + yF-Projektion),
`phase13_live_data/live_data/backfill.py` (`EPIC_MAP` raus, Symbol-Lookup rein) +
`phase13_live_data/scripts/` (`capital_backfill.py` `--universe-db`, drei-Fälle-
`source_delta.py`) and `phase8_scheduler/webui/` (ARM-Endpoints + Warn-Banner).
See the phase head's Modul-Tabelle for the full cross-phase list.
