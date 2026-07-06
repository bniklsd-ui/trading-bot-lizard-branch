---
status: live
purpose: ACTIVE phase head — V2 Foundation: autonomous epic research (universe pkg) + data-input reliability; Steps 2–8 open
read-when: working in phase9_universe/ — read this head + its newest Session-stopped block first
detail: L2
up: ../CLAUDE.md
down:
  - ./SESSIONS_ARCHIVE.md      # full session history (L3)
  - ./README.md
  - ../docs/concepts/phase9_v2_foundation_plan(1).md   # full concept/plan snapshot (L3)
updated: 2026-07-06
---
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

## Modul-Struktur (`universe` Paket) — Status pro Step
| Datei | Zweck | Status |
|---|---|---|
| `pyproject.toml` · `requirements.txt` · `README.md` · `CLAUDE.md` | Scaffold + Packaging (Step 0b/1) | ✅ |
| `phase2_persistence/migrations/004_phase9_instrument_universe.sql` | `instrument_universe`-Tabelle + Status-Index | ✅ (Step 1, P2-Berührung sanktioniert) |
| `universe/models.py` | `UniverseRecord` (frozen, `to_row`/`from_row`/`to_instrument_spec`) + Status-/Source-/Pricing-Source-Konstanten | ✅ (Step 1) |
| `universe/exceptions.py` | `UniverseError` → `UniverseSafetyError`/`UniverseStoreError` | ✅ (Step 1) |
| `universe/store.py` | `UniverseStore` — eigene sqlite3-Connection (kein `persistence.Database`-Import, Phasen-Isolation) | ✅ (Step 1, 19 Tests) |
| `universe/pricing.py` | Deterministischer `point_value`-Resolver (`resolve_point_value`/`confirm_curated`) | ✅ (Step 2, 15 Tests) |
| `universe/discovery.py` | Seed-Sweep + Code-Filter (`discover`/`DiscoveryReport`) | ✅ (Step 3, 14 Tests) |
| `universe/promotion.py` | Statusmaschine + Safety (`run_promotion_cycle`/`PromotionReport`) | ✅ (Step 4, 14 Tests) |
| P4/P8-Integration | DB-Universum statt `EXTENDED_UNIVERSE`, Refresh-Naht | ✅ (Step 5) |
| BarProvider-Kette (Step 6) gebaut | `external_data/providers.py` + Circuit + Divergenz | ✅ (Step 6) |
| BarProvider-Kette **verdrahtet** (P4+P8 wiring) | `_build_market_data` hinter `enable_ig_bars`-Flag (Default **aus**) | ✅ (Wiring 2026-07-04) |
| Step 7a — LS-Multi-Epic-Diagnose (Live-Lauf) | `scripts/diag_lightstreamer_multi.py` gegen die kuratierten 4 Epics | ✅ Live gelaufen 2026-07-06 → **NEGATIVE result**: kein Multi-Epic-Bug (alle 4 subscriben in M1+M2, H1–H4 alle False). Details: `phase1_broker_wrapper/lightstreamer_integration_notes.md` |
| Step 7b — LS-Fix + `LiveQuoteCache` | Fix folgt aus 7a | ⏸ Kein Fix-Target — 7a fand keinen Bug. Unblocked-aber-leer; nur re-run bei ~10+ aktiven Epics (H2-Limit ungeprüft bei 4) |
| `scripts/dev_install.sh` | `phase9_universe` in die editable-install-Kette aufgenommen | ✅ |

## Step 1 — Ergebnisse (2026-07-04)
- **Migration 004** additiv, folgt exakt dem 002/003-Muster (dated Header-Kommentar,
  `ALTER`/`CREATE TABLE IF NOT EXISTS`, kein bestehendes Objekt berührt). Frische DB
  erreicht jetzt Version 4. **P2-Tests aktualisiert** (die einzige sanktionierte
  P2-Berührung dieses Steps, mirror wie 002/003 es taten): `_EXPECTED_TABLES` +
  `instrument_universe`, `test_fresh_db_reaches_version_3` → `_version_4`,
  `test_rerun_is_noop`/`test_find_pending_respects_current`/
  `test_database_run_migrations_idempotent` auf 4 gehoben, **+1 neuer Test**
  (`test_phase9_instrument_universe_table_present`, prüft Spalten + Index) → **P2 75 → 76**.
- **`UniverseStore` öffnet seine eigene `sqlite3`-Connection** (kein
  `persistence.Database`-Import) — bewusste Abweichung vom P7-Muster
  ("bestehende P2-CRUD wiederverwendet"), aber konsistent mit P8s `budget.py`
  (liest `llm_usage.json` direkt statt einen P4-Reader zu importieren): die
  physische DB-Datei ist geteilt, der Zugriffscode nicht. `import universe.*`
  zieht **NONE** cross-phase (verifiziert: 33 neue Module beim Import, keiner
  davon `broker_wrapper`/`persistence`/`external_data`/`research`/`execution`/
  `reward`/`debate`/`scheduler`/`anthropic`/`requests`/`pandas`/`numpy`/`yfinance`).
- **`seed_curated()`:** nur die DAX-Epic (`IX.D.DAX.IFMM.IP`, live-bestätigt) bekommt
  `point_value_source="curated_confirmed"` beim Seed; alle anderen (STXE/CAC/IBEX,
  bislang nur inferiert) seeden mit `point_value_source=NULL` → müssen den
  Step-2-Resolver durchlaufen, um bestätigt zu werden (D6/carried-over point_value
  stirbt hier strukturell, nicht per Behauptung). `INSERT OR IGNORE` auf dem PK
  (`epic`) macht das Seeden idempotent — ein Re-Seed überschreibt nie bereits
  vorhandene Zeilen (weder Operator- noch Pipeline-getriebene).
- **19 Tests** (`test_store.py`): Migrations-Tabellen-Beweis, Record-Roundtrip
  (inkl. leerer `checks`-Dict → `NULL`, nicht `"{}"`), invalid-Status/-Source →
  `ValueError`, Seed-Idempotenz + 4-Instrumente-Fall, Upsert+Get+Conflict-Overwrite,
  Status-Roundtrip + fail_count-Inkrement (unabhängig vom `set_pricing`-Pfad),
  fehlende Epic → `UniverseStoreError` (beide Setter), Status-Filter (single/multi/
  leer), `active_universe()`-Determinismus (created_at, dann epic als Tie-Break).
- **Regression:** volle Suite neu gelaufen, alles grün + unverändert außer P2 (75→76
  wie oben erklärt): P1 52 · P3 73 · P4 135 · P5 154 · P6 70 · P7 133 · P8 199 ·
  root 64 · **P9 19 (neu)**. `py_compile` clean auf allen neuen Dateien.

## Cross-Phase-Edit-Register (aus dem Plan §11 — hier nur der Pointer, Details im Plan)
P1 (`get_market_info`-Feld-Passthrough, Lightstreamer-Fix, `quote_cache.py`), P2 (Migration
004), P3 (`providers.py`, `fetcher.py`-Härtung), P4 (`models.py`/`context_builder.py`
Live-Quote-Enrichment, `enable_live_quotes` default aus), P8 (`runner.py`
`universe_refresher`-Naht default `None`, `observability.py` neue Event-Typen), Wiring
(`scripts/wiring.py` — zentraler Cross-Phase-Konfig-Ort). **Nicht angefasst:** P5
(Gates/VETOs/Sizing), P6 (Debatte), P7 (Reward). Null LLM-Änderungen.

---

## Session stopped — 2026-07-04 (Wochenend-Session: Review-Polish-Fixes + Phase-1-Hardening-Plan geschrieben)

> **Auslöser:** Nikinger-Auftrag (Wochenende, keine Live-Tests möglich): (a) die drei
> kosmetischen Punkte aus der Review-Session umsetzen, (b) die am schwächsten
> geschriebene Phase scannen und einen Verbesserungsplan **nur schreiben** — Umsetzung
> später durch Sonnet, NACH den Live-Tests, als Teil von V2. Auto-Modus (Tests frei),
> für (b) ausdrücklich keine Code-Änderungen.

### Completed (a) — die drei Review-Polish-Fixes (klein, additiv, alle getestet)
- **`universe/pricing.py`:** Pfad 2 (name/lot_size) trägt jetzt denselben `> 0`-Guard
  wie Pfad 1 — ein hypothetisches „(0€)"/lot_size 0 kann nicht mehr zu
  `point_value=0` auflösen (würde P5-Sizing nullen). **+1 Test** (`test_pricing.py`).
- **`scheduler/observability.py`:** `record_event` stempelt jetzt ein **tz-aware**
  `datetime.now().astimezone()` statt naiv — keine gemischten Zeitformate mehr im
  selben JSONL wie `record_cycle`s tz-aware `clock.now()`. **+1 Test** → **P8 217**.
- **`universe/promotion.py`:** Step 3 (Health-Recheck) überspringt Epics, die in
  **diesem** Zyklus aktiviert wurden (Step-1-Verify liegt Sekunden zurück — der
  zweite `verify_instrument`-Call war reiner Doppel-Traffic). Ab dem Folgezyklus
  normale Recheck-Teilnahme. **+1 Test** (beweist: 1 `get_ohlcv`-Call im
  Aktivierungszyklus, 1 im Folgezyklus) → **P9 69**.

### Completed (b) — Scan + Plan (NUR Plan, kein Code — Nikinger-Vorgabe)
- **Scan aller 9 Phasen** (Zeilen, Testdichte, Debt-Marker, qualitative Reads):
  **Phase 1 (`broker_wrapper`) ist der klare Schwächste** — Testdichte 2.3
  Tests/100 Zeilen (nächster: 4.7), größte Einzeldatei (`ig_adapter.py` 930 Zeilen),
  und zwei live-gebissene strukturelle Löcher: 429 → sofortiger Raise ohne Retry
  (verursachte den v1.5-CAC/AEX/IBEX-Ausfall; **fünf** Call-Sites reimplementieren
  deshalb Pacing) und der fehlende `valueOfOnePip`/`contractSize`-Passthrough in
  `get_market_info` (hält P9s Pricing-Pfad 1 dauerhaft dormant). Dazu ungetestete
  Envelope-Shapes genau in der bewiesenen Live-Bug-Klasse („Fake ≠ echte Shape",
  s. der 2026-06-29-`env.get`-Bug).
- **Plan geschrieben:** [`docs/concepts/phase1_hardening_plan.md`](../docs/concepts/phase1_hardening_plan.md)
  — §0 Scan-Evidenz · §2 Step 0 Baseline + P1-CLAUDE.md-Skeleton · §3 Step 1
  429-Retry/Backoff zentral in `_request` (injizierbares `sleep_fn`, Opt-out,
  Call-Site-Pacing bleibt als belt-and-braces) · §4 Step 2 MarketInfo-Feld-
  Passthrough (aktiviert P9-Pricing Pfad 1 ohne P9-Änderung) · §5 Step 3
  Test-Backfill nach Live-Risiko (Parser + Envelope-Shapes zuerst, ~52 → ~80+ Tests)
  · §6 Cross-Phase-Register · **bewusst verworfen:** `ig_adapter.py`-Split (Risiko >
  Ästhetik) und alles Lightstreamer (gehört zu Step 7b, keine Doppelung).
- **Ausführung gelockt:** durch Sonnet (medium, Auto-Modus), erst NACH den
  Phase-9-Live-Tests, als Teil des V2-Bogens.

### Verifiziert (gemockt/offline)
- Volle per-Phase-Regression grün: P1 52 · P2 76 · P3 100 · P4 141 · P5 154 ·
  P6 70 · P7 133 · **P8 217 (+1)** · **P9 69 (+2)** · root 77.

### Next
- **Nikinger (Montag/Handelszeiten):** die zwei Live-Läufe aus dem Wiring-Handover
  unten — (1) `--enable-ig-bars`-Lauf + `bar_fetch`-Events beobachten, (2) Step 7a
  `python scripts/diag_lightstreamer_multi.py`. Danach: 7b, Step 8, und (separat,
  Sonnet) der Phase-1-Hardening-Plan.
- **Commit:** dieser Stand (3 Fixes + 3 Tests + Plan-Datei + dieser Block) ist
  commit-fertig, wartet auf Nikinger-Trigger.

### Offene Punkte / blockers
- Keine technischen. Der Divergenz-Check (gebaut, kein Consumer) bleibt der einzige
  unverdrahtete Step-6-Baustein — bewusst offen bis nach den Live-Läufen.

---


> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
