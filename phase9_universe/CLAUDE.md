# CLAUDE.md — Phase 9 (V2): Foundation (`phase9_universe/`)

> Closes the two structural gaps the v1.5→v1.7 hotfix arc kept resurfacing under different
> names: no autonomous epic discovery (universe is a hand-curated tuple) and no hardened
> data-input path (yFinance intermittency tolerated, not fixed). **Quelle der Wahrheit ist der
> Code, nicht dieses Dokument.** Full plan: `../docs/concepts/phase9_v2_foundation_plan(1).md`.
> Context: `../phase8_scheduler/PHASE8_CLOSEOUT_HANDOVER.md` (the reframe proposal this phase
> executes).

## Mission (zuerst lesen)
Zwei Jobs, gleich gewichtet:
1. **V2a — Autonome Epic-Research:** discover → validate → promote als Code-Pipeline. Kein
   manueller Code-Edit mehr, damit ein Instrument ins Live-Universum kommt.
2. **V2b — Daten-Input-Zuverlässigkeit:** Provider-Kette IG-primär + yFinance strukturell
   gehärtet (Backoff/Circuit-Breaker), Lightstreamer in den Research-Kontextpfad verdrahtet.

## Bauprinzip (Projekt-Kernprinzip, unverändert)
„So wenig AI wie möglich, so viel AI wie nötig." **Phase 9 (V2) fügt NULL neues AI hinzu** —
Discovery-/Promotion-Kriterien sind 100 % code-evaluiert (Suchbegriff-Sweep + IG-Feld-Filter +
deterministischer `point_value`-Resolver). Wer hier ein LLM „entscheiden/filtern/mappen" lassen
will → **stop**, das ist Code. `yf_ticker`-Mapping ist eine statische Code-Tabelle, kein
LLM-Vorschlag (das wäre V4).

## Scope
- **DRIN:** `discovery.py` (Seed-Sweep + Code-Filter), `pricing.py` (deterministischer
  `point_value`-Resolver), `promotion.py` (Statusmaschine + Safety + Auto-Demotion), Migration
  004 (`instrument_universe`) + `UniverseStore`, P4-Integration (DB-Universum statt
  `EXTENDED_UNIVERSE`-Tuple), P8-Refresh-Naht, BarProvider-Kette (IG→yFinance) + yFinance-
  Härtung (Backoff/Circuit-Breaker) + Divergenz-Check, Lightstreamer-Multi-Epic-Diagnose →
  Fix → `LiveQuoteCache` in den Research-Kontext.
- **DRAUSSEN (carried to V3/V4):** DB-Reform jenseits Migration 004, No-Trade-Lessons, UI-
  Arbeit (alles V3/Phase 10); Council, Debate-Handover, Reward-Reform, Force-Trigger-Guard,
  Instinct-ECC (V4/Phase 11); eine echte zweite unabhängige Echtzeitquelle (Lock #8 — kein
  neuer bezahlter/gekeyter Provider); Momentum-VETO-Datenquelle (bleibt P1-IG-Bars, unangetastet).

## Build-Reihenfolge (verbindlich, aus dem Plan §1)
Step 0 (Legacy-Grep + Baseline) → Step 0b (Doku-Reconciliation, **dieser Skeleton ist Teil
davon**) → Step 1 (Migration 004 + `UniverseStore`) → Step 2 (`pricing.py`) → Step 3
(`discovery.py`) → Step 4 (`promotion.py`) → Step 5 (P4/P8-Integration) → Step 6 (V2b-i:
BarProvider-Kette) → Step 7 (V2b-ii: Lightstreamer) → Step 8 (Operator-Live-Runs) → Post
(Doku-Sync, SVG, Handover). 1–5 (V2a) vor 6–7 (V2b), weil die Promotion-Pipeline der
Verbraucher der Datenpfad-Verbesserungen ist.

## Statusmaschine (`instrument_universe.status`)

```
                 ┌─────────────┐
   discover()    │             │
  ──────────────▶│ discovered  │
                 │             │
                 └──────┬──────┘
                        │ verify PASS + point_value resolved
                        ▼
                 ┌─────────────┐
                 │  verified   │
                 └──────┬──────┘
                        │ auto-activate (len(active) < max_active)
                        ▼
        IG-fail×N  ┌─────────────┐  IG-fail×3 (demote_after_fails)
      ┌────────────│   active    │────────────────┐
      │            └─────────────┘                │
      │  yF-fail → data_degraded=1 (never demotes) ▼
      │                                     ┌──────────────┐
      └────────────backoff, re-verify──────▶│ quarantined  │
                                             └──────────────┘

  retired = manual/future (not reachable in v1 promotion cycle)
```

PASS + point_value ungelöst → bleibt `discovered` (kein Fortschritt, kein Fehler). IG-seitiger
Health-Fail demotiert (nach `demote_after_fails`); yFinance-seitiger Fail setzt nur
`data_degraded=1` (reduced-signal toleriert, degradiert nie zu einem Aktivierungs-Hindernis —
Konzept C3, gleiche Disziplin wie P3s Brain-Context-Degradierung).

## Test-/Wiring-Konventionen (gespiegelt an P4/P7/P8)
- `from __future__ import annotations`, Type-Hints + Docstrings, eine Datei = eine
  Verantwortung, eigene typisierte Exceptions (`UniverseError` → `UniverseSafetyError`/
  `UniverseStoreError`), nie still schlucken.
- **Phasen-Isolation:** `import universe.*` zieht **keine** cross-phase Module beim Laden
  (broker_wrapper/persistence/external_data/research/execution/reward/debate/anthropic nur
  lazy in Funktionskörpern, nie am Modul-Top — Muster aus P7/P8 `scripts/wiring.py`).
- **Kein Copy-Paste der P8-Verify-Funktionen.** `promotion.py` importiert
  `check_ig_side`/`check_yf_side`/`verdict_for` aus `phase8_scheduler/scripts/verify_instrument.py`
  via `importlib.util.spec_from_file_location` (die dokumentierte, duck-typed v3-Naht) — eine
  Wahrheit für „ist dieses Instrument nutzbar".
- **Demo-only, fail-closed, hart.** `run_promotion_cycle(..., is_demo: bool, ...)` wirft
  `UniverseSafetyError`, wenn `is_demo=False` — kein Ausnahmepfad, keine „für jetzt"-Bypässe.
- `pytest phase9_universe/tests -q`, in-memory SQLite (`:memory:` + Migrations-SQL direkt) für
  `test_store.py`; reine Fixture-Dicts (kein Netz) für `test_pricing.py`/`test_discovery.py`;
  Fake-Broker/-Fetcher/-Store für `test_promotion.py`. Grep-Assertion in mindestens einem Test:
  `import anthropic` verboten irgendwo im Paket.
- **Reuse, nicht Reimplementierung:** `EXTENDED_UNIVERSE` (P4 `research/models.py`) wird zum
  einmaligen `UniverseStore.seed_curated()`-Input (`source="curated"`), nicht dupliziert.
- Logging → stderr, stdout nur bei CLI-Scripts JSON. Atomic commits. Kein Subtask „done" ohne
  grünes `pytest` (gemockt/offline — Live-Läufe sind Operator-Sache, s. `feedback_live_testing`
  memory).

## Cross-Phase-Edit-Register (aus dem Plan §11 — hier nur der Pointer, Details im Plan)
P1 (`get_market_info`-Feld-Passthrough, Lightstreamer-Fix, `quote_cache.py`), P2 (Migration
004), P3 (`providers.py`, `fetcher.py`-Härtung), P4 (`models.py`/`context_builder.py`
Live-Quote-Enrichment, `enable_live_quotes` default aus), P8 (`runner.py`
`universe_refresher`-Naht default `None`, `observability.py` neue Event-Typen), Wiring
(`scripts/wiring.py` — zentraler Cross-Phase-Konfig-Ort). **Nicht angefasst:** P5
(Gates/VETOs/Sizing), P6 (Debatte), P7 (Reward). Null LLM-Änderungen.

---

## Session stopped — (leer, noch kein Modul-Step gestartet)

Dieser Block wird beim Abschluss des ersten echten Moduls (Step 1 — Migration 004 +
`UniverseStore`) erstmals befüllt.
