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
  Instinct-ECC (V4/Phase 12, umnummeriert 2026-08-01, war vorher "Phase 11"); eine echte zweite unabhängige Echtzeitquelle (Lock #8 — kein
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

## Session stopped — 2026-07-06 (Doc-Layers-Restrukturierung + Auth-Debugging + IG-Allowance-Fixes — erster Step-8-naher Live-Lauf gesund)

> **Auslöser:** Nikinger-Session (Montag): (a) Doc-Layers-Plan ausführen (Session-Budget
> reichte doch), (b) das Auth-Problem vom Wochenende diagnostizieren, (c) die daraus
> gefundenen Fixes einbauen. Fable-Session, Auto-Modus.

### Completed
- **Doc-Layers-Konvention repo-weit eingeführt** (Commits `d3421de`…`c9922e6`): per-Phase
  `SESSIONS_ARCHIVE.md` (verbatim rotiert, cmp-verifiziert), L1-Header-Cards auf allen
  lebenden Docs, `docs/INDEX.md` (L0), `docs/DOC_LAYERS_CONVENTION.md` (generisch),
  Rotationsregel + `## Working style` in Root-`CLAUDE.md`. Phase-Heads: P8 211→21KB.
- **Auth-Diagnose (zweistufig):** (1) `error.security.invalid-details` war ein
  **Passwort-Tippfehler im Keyring** (nicht der neue API-Key, nicht die
  Parallel-Login-Falle — die heilt sich selbst). (2) Der Folgefehler im Daemon
  (`get_account AUTH_ERROR` im ersten Zyklus, Zyklus 2 gesund) war **IGs
  Request-Allowance**: der Discovery-Sweep mit `pace_s=1.0` (~60 req/min) riss die
  ~30/min-Demo-Allowance; IG antwortet **403** `exceeded-api-key-allowance`, das der
  Adapter blind auf `AUTH_ERROR` mappte.
- **Fix 1 (`universe/discovery.py` + `promotion.py`, Commit `b72ad53`):** `pace_s`
  Default 1.0 → **2.5s** (~24 req/min). Live bestätigt: Discovery braucht jetzt ~4min
  (14:48→14:52), Zyklus 1 direkt gesund, kein AUTH_ERROR mehr.
- **Fix 2 (`broker_wrapper/adapters/ig_adapter.py`, Commit `142771b`, cross-phase
  Nikinger-approved):** 403 mit `exceeded-*-allowance`-Body nimmt jetzt den
  429-Retry-Pfad und erschöpft zu `RATE_LIMIT` statt irreführendem `AUTH_ERROR`;
  plain 403 bleibt `AUTH_ERROR`. +2 Tests (P1 85→**87**).
- **Fix 3 (`phase8_scheduler/scripts/smoke_test.py`, Commit `d9ae9a2`):** der
  Offline-Smoke-Test war seit `032dd1c` (2026-06-29) latent kaputt — dict-Fake statt
  Envelope-Shape (`'dict' object has no attribute 'ok'`) + `ensure_candidates`-Fake
  ohne `ResearchResult` (v1.6-Observability-Drift). Beide Fakes auf die realen Shapes
  gezogen → **3/3 Szenarien PASS**.

### Verifiziert
- Volle per-Phase-Regression grün: P1 **87** (+2) · P2 76 · P3 100 · P4 141 · P5 154 ·
  P6 70 · P7 133 · P8 217 · P9 69 · root 77. P8-Offline-Smoke 3/3.
- **Live (Nikinger-run):** P1-Smoke-Test PASS (voller REST-Zyklus); Scheduler-Daemon
  startet, Discovery paced sauber, Research-Zyklus gesund (LLM-Abstain on merit —
  legitimes No-Pick, kein Fehler).

### Nachtrag (gleiche Session, ~16:00) — der Curated-Fallback persistierte → C3-Bug gefunden + gefixt
- **Befund (DB-Forensik `instrument_universe`):** Discovery fand 14 Instrumente, aber
  **alle 14 quarantined** — zwei Gruppen: (1) 7 Rows mit vergifteten Check-Ergebnissen
  aus dem 14:19-Allowance-Sturm (selbst DAX mit `currency_eur: false`), (2) 7 Rows aus
  dem gesunden 14:48-Lauf mit **IG-Checks alle grün, aber yf-Checks false** → FAIL.
- **Konzept-Verstoß (C3):** `promotion.py` Step 1 quarantinierte auf das rohe
  `verdict_for`-FAIL (inkl. yf-Seite) — Step 3 tolerierte yf-Fails korrekt als
  `data_degraded`. Dazu Todesspirale: `2**fail_count`-Backoff + wiederholte yf-Flakes
  = Universum stundenlang eingefroren.
- **Fix A (`universe/promotion.py`):** Step 1 quarantiniert nur noch bei
  `_ig_side_failed`; yf-only-Fail → verified/active mit `data_degraded=1` (C3-konform,
  spiegelt Step 3). **+2 Tests → P9 71.**
- **Fix B (`phase8_scheduler/scripts/wiring.py`):** `store.seed_curated(EXTENDED_UNIVERSE)`
  hatte **null Caller** — jetzt idempotent im `universe_refresher` vor `discover()`
  (offline gegen frische Migrations-DB verifiziert: 4 seeded/active, Re-Seed 0).
- **DB-Reset (Nikinger-approved, Daemon gestoppt):** die 12 noch quarantined Rows →
  `status='discovered', fail_count=0, last_verified_at=NULL`. Stand danach: **2 active
  (DAX + CAC, `point_value_source='ig_fields'` — Pricing-Pfad 1 lebt, dank
  P1-Pip-Feld-Passthrough!) + 12 discovered.**

### Nachtrag 2 (2026-07-07) — erster Live-Tag ausgewertet
- Ergebnisse + offene Beweispunkte + Watch-Items (u. a. `fail_count`-Reset-Lücke):
  **[PHASE9_V2_LIVE_RESULTS_HANDOVER.md](./PHASE9_V2_LIVE_RESULTS_HANDOVER.md)** (📕).
  Kurzfassung: Pipeline bewiesen (8 active/7 verified/0 quarantined, alles `ig_fields`),
  erster CAC-Pick+Debatte, 0 Trades bisher, Lauf läuft weiter (~2–3 Tage Baseline).

### Nachtrag 3 (2026-07-07 ~11:31) — Neustart-Beweis erbracht ✅
- **Beweispunkt 1 geschlossen:** Neustart 11:26 → `context built: 8 tradeable epic(s),
  brain=8/8 present` — die V2a-Kette discover→activate→**research-nutzt-es** ist damit
  end-to-end live bewiesen (Nikinger-Lauf).
- **403-Allowance-Fix live bestätigt:** erster Zyklus nach Start abortet weiterhin
  fail-closed (Startup-Refresher verbraucht Allowance), aber jetzt ehrlich als
  `RATE_LIMIT` klassifiziert statt irreführend `AUTH_ERROR` — selbstheilend ab Zyklus 2.
- **`fail_count`-Reset-Lücke gefixt** (Watch-Item aus dem Handover): Step-1-Verify-PASS
  resettet jetzt den ererbten Zähler (beide IG-grüne Pfade), +1 Test → **P9 72**. Live-DAX
  (fail_count=3) heilt ohne DB-Eingriff über den bestehenden Step-3-Recovery-Reset.
- Doku-Frische-Sweep: README (Zeile 9 + Fußnote ⁶), ROADMAP-P9-Status, Root-CLAUDE-Tabelle,
  phase9-README-Modultabelle — alle trugen noch „Build nicht gestartet"-Stände.

### Next
- ~~Nächster Daemon-Start = der V2a-End-to-End-Beweis~~ ✅ **erbracht 2026-07-07 11:31**
  (s. Nachtrag 3). Verbleibende Beweispunkte des Baseline-Laufs: **ein echter Trade
  unter dem V2-Universum** + Variety-These mit 8 Epics (Abstain-Quote beobachten).
- Unverändert offen: `--enable-ig-bars`-Beobachtungslauf (`bar_fetch`-Events),
  Step 7b nur bei ~10+ aktiven Epics re-runnen, Divergenz-Check-Verdrahtung nach den
  Live-Läufen, Step 8 (mehrtägiger Autonomie-Lauf).

### Offene Punkte / blockers
- Keine technischen. Beobachtung: zwei LLM-Abstains in Folge (14:25, 14:53) — on merit,
  aber im Auge behalten (v1.5-Variety-Thema), sobald das DB-Universum >4 Epics aktiviert.
- yFinance fiel im 14:48-Lauf für **alle** Ticker aus (auch ^GSPC/^DJI) — mit Fix A
  nicht mehr fatal, aber ein Auge auf Yahoo-Rate-Limiting der VM halten (V2b-Thema).

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
