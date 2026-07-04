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
| `universe/promotion.py` | Statusmaschine + Safety | ⬜ (Step 4) |
| P4/P8-Integration | DB-Universum statt `EXTENDED_UNIVERSE`, Refresh-Naht | ⬜ (Step 5) |
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

## Session stopped — 2026-07-04 (Step 3: `discovery.py` — abgeschlossen)

> **Auslöser:** direkte Fortsetzung nach Step 2, gleiche Session, Auto-Modus.

### Completed
- `universe/discovery.py` (neu): `SEARCH_TERMS` (deutsch+englisch, 18 Begriffe),
  `KNOWN_YF_TICKERS`/`KNOWN_VOLUME_PROXIES` (statische Substring-Tabellen, kein LLM),
  `discover(broker, store, *, search_terms, pace_s=1.0, sleep_fn) -> DiscoveryReport`.
  Ruft je Treffer `get_market_info` (mirrors `scripts/resolve_epics.py`s Kette), filtert
  EUR + `instrument_type` enthält INDICES + `market_status==TRADEABLE` + `min_deal_size>0`
  + Kassa-Präferenz (kleinster `lot_size`, kein „forward" im Namen) bei Mehrfachtreffern
  pro Term. Bereits bekannte Epics (jeder Status) → Skip. Fail-soft je Term (Exception
  oder `search_ok=False` killt nie den restlichen Sweep).
- **14 neue Tests** (`test_discovery.py`): jedes Filterkriterium einzeln, Kassa-Auswahl
  bei 3 Treffern (Forward + zwei Kassa-Größen), Single-Hit-Bypass, Skip bekannter Epics,
  Fail-soft (Exception + `search_ok=False`), Pacing-Beweis (injizierter `sleep_fn`,
  keine echten Sleeps, 2 Calls je Epic: nach `search_markets` + nach `get_market_info`),
  Report-Defaults, **Grep-Assertion** (`import anthropic` verboten im Paket — automatisiert,
  nicht nur manuell geprüft).
- `universe/__init__.py`: `discover`/`DiscoveryReport`/`SEARCH_TERMS`/`KNOWN_YF_TICKERS`/
  `KNOWN_VOLUME_PROXIES` exportiert.

### Verifiziert
- `pytest phase9_universe/tests -v` → **48 passed** (19 store + 15 pricing + 14 discovery).
- Import-Isolation erneut bestätigt (0 cross-phase Leaks); `py_compile` clean.
- Volle Regression unverändert grün: P1 52 · P2 76 · P3 73 · P4 135 · P5 154 · P6 70 ·
  P7 133 · P8 199 · root 64 · **P9 48**.

### Next
- **Step 4 — `promotion.py`:** Statusmaschine (discovered→verified→active,
  Auto-Demotion active→quarantined), Demo-only Safety-Raise, Backoff-Treppe,
  `max_active`-Kappung, kuratierte Bestätigung via `confirm_curated`. **Wichtig:** die
  Verify-Funktionen (`check_ig_side`/`check_yf_side`/`verdict_for`) müssen aus
  `phase8_scheduler/scripts/verify_instrument.py` via
  `importlib.util.spec_from_file_location` importiert werden — **kein Copy-Paste**
  (Plan §7). Vor dem Bau deren exakte Signaturen gegenlesen.

### Offene Punkte / blockers
- Keine technischen.

---

## Session stopped — 2026-07-04 (Step 2: `pricing.py` — abgeschlossen)

> **Auslöser:** direkte Fortsetzung nach Step 1, gleiche Session, Auto-Modus.

### Completed
- `universe/pricing.py` (neu): `resolve_point_value(market_info: dict) -> tuple[float,str]|None`
  (Auflösungsordnung: IG-Rohfelder → Namens-/lot_size-Kreuzcheck → `None`) +
  `confirm_curated(record, market_info) -> bool | None`.
- **15 neue Tests** (`test_pricing.py`), inkl. der im Plan geforderten Akzeptanz-Fixtures
  (STXE `"(2€)"`/lot_size 2.0 → `(2.0, "name_lotsize_agree")`; widersprüchliche Fixture → `None`).
- `universe/__init__.py`: `resolve_point_value`/`confirm_curated` exportiert.

### ⚠ Reconciliation (Code = Wahrheit — vor dem Bau verifiziert, kein P1-Edit nötig)
- **P1s `MarketInfo.to_dict()`** (`phase1_broker_wrapper/broker_wrapper/models.py`) exponiert
  **nur** `epic`/`name`/`instrument_type`/`currency`/`expiry`/`min_deal_size`/`lot_size`/
  `market_status` — **keine** rohen IG-Pip-/Contract-Felder. Der `ig_fields`-Pfad im Resolver
  ist damit **gegen echte P1-Daten aktuell dormant** (feuert nie, bis P1 sie additiv
  durchreicht) — bewusst **trotzdem gebaut + fixture-getestet** (reine Funktion, aktiviert sich
  automatisch ohne Code-Änderung hier, sobald P1 die Felder liefert). **Kein P1-Touch in
  diesem Step** — nicht „extremely necessary" jetzt, da Pfad 2 (Namens-/lot_size-Kreuzcheck)
  bereits jedes aktuell geseedete Instrument mit einem echten Beweis versorgt. Offener Punkt
  für eine spätere Session, falls IG-Pip-Felder wirklich gebraucht werden.
- **`confirm_curated`-Rückgabetyp bewusst `bool | None`** statt des Plan-Wortlauts `bool` —
  der Plan-Fließtext selbst beschreibt drei reale Zustände (bestätigt/widerlegt/nicht auflösbar),
  die ein reiner `bool` nicht ohne Informationsverlust abbilden kann. Dokumentierte, minimale
  Abweichung (Docstring in `pricing.py`).

### Verifiziert
- `pytest phase9_universe/tests -v` → **34 passed** (19 store + 15 pricing).
- Import-Isolation erneut bestätigt (0 cross-phase Leaks); `grep -rn "import anthropic"
  phase9_universe/universe/` → 0 Treffer (Grep-Assertion aus der Test-Konvention erfüllt).
- Volle Regression unverändert grün: P1 52 · P2 76 · P3 73 · P4 135 · P5 154 · P6 70 ·
  P7 133 · P8 199 · root 64 · **P9 34**.

### Next
- **Step 3 — `discovery.py`:** Seed-Suchbegriff-Sweep + IG `search_markets` + Code-Filter.
  Vor dem Bau `scripts/resolve_epics.py` als Referenznutzung + die echte `search_markets`-
  Envelope-Form gegenlesen (Plan §14 Punkt 2 — Feldnamen `instrument_type`/`market_status`
  sind an `search_markets` **bereits** bestätigt snake_case+gemappt, s. `ig_adapter.py:480-493`
  oben in dieser Session gelesen).

### Offene Punkte / blockers
- Keine technischen. Der `ig_fields`-Pfad bleibt dormant bis zu einer möglichen künftigen
  P1-Erweiterung (kein Blocker für Steps 3–5, die den Namens-/lot_size-Pfad nutzen).

---

## Session stopped — 2026-07-04 (Step 1: Migration 004 + `UniverseStore` — abgeschlossen)

> **Auslöser:** Fortsetzung der Phase-9-(V2)-Kickoff-Session (Housekeeping Step 0/0b lief
> bereits vorher, docs-only, auf Branch `phase9-v2-foundation`, committet). Dieser Step
> baut das erste echte Modul: die DB-Persistenz für das autonome Instrumenten-Universum.
> Auto-Modus (Nikinger-Freigabe) — kein Plan-Mode-Zwischenstopp, da der Fable-Plan
> bereits ausführungsreif ist; nur bei einem schweren Problem zurückfragen.

### Completed
- `phase2_persistence/migrations/004_phase9_instrument_universe.sql` (neu): `instrument_universe`-
  Tabelle + `idx_instrument_universe_status`-Index, additiv, dated Header mirrort 002/003.
- `phase2_persistence/tests/test_migrations.py`: Version-3→4-Anpassung an 5 Stellen +
  1 neuer Test (`test_phase9_instrument_universe_table_present`). **P2 75 → 76.**
- `phase9_universe/universe/models.py` (neu): `UniverseRecord` + Status-/Source-/
  Pricing-Source-Konstanten.
- `phase9_universe/universe/exceptions.py` (neu): `UniverseError`-Hierarchie.
- `phase9_universe/universe/store.py` (neu): `UniverseStore` (eigene sqlite3-Connection,
  `seed_curated`/`upsert_discovered`/`get`/`list_by_status`/`set_status`/`set_pricing`/
  `active_universe`).
- `phase9_universe/universe/__init__.py`: Public Exports.
- `phase9_universe/tests/test_store.py` (neu, 19 Tests).
- `phase9_universe/pyproject.toml` + `requirements.txt` + `README.md` (Scaffold).
- `scripts/dev_install.sh`: `phase9_universe` in die editable-install-Kette aufgenommen
  (Position nach P8, rein numerisch — keine echte Abhängigkeit, s. Kommentar im Script).

### Verifiziert (gemockt/offline — kein Netz, kein LLM, kein Broker)
- `pip install -e phase9_universe` grün; `pytest phase9_universe/tests -v` → **19 passed**.
  `pytest phase2_persistence/tests -q` → **76 passed** (75+1).
- **Import-Isolation bewiesen:** `import universe` zieht 33 neue Module beim Laden,
  **keines davon** cross-phase (`broker_wrapper`/`persistence`/`external_data`/`research`/
  `execution`/`reward`/`debate`/`scheduler`/`anthropic`/`requests`/`pandas`/`numpy`/
  `yfinance` — alle abwesend).
- `py_compile` clean auf allen neuen `.py`-Dateien; `bash -n scripts/dev_install.sh` clean.
- **Volle Regression** (alle Phasen separat, bekannte `tests.conftest`-Kollision):
  P1 52 · P2 76 · P3 73 · P4 135 · P5 154 · P6 70 · P7 133 · P8 199 · root 64 · **P9 19** —
  alle grün, nur P2 verändert (erwartungsgemäß, s. o.).

### Next
- **Step 2 — `universe/pricing.py`:** deterministischer `point_value`-Resolver
  (IG-Feld-Auflösung + Namens-/lot_size-Kreuzcheck + `confirm_curated()`). Plan §5
  ([VERIFY]: welche `get_market_info`-Felder P1 heute durchreicht — sehr wahrscheinlich
  nur `currency`/`min_deal_size`/`lot_size`; ggf. additive P1-Feld-Passthrough-Erweiterung
  nötig, Cross-Phase-Edit-Register §11 im Plan).
- Danach Step 3 (`discovery.py`), Step 4 (`promotion.py`), Step 5 (P4/P8-Integration).
- **Commit:** dieser Step ist commit-fertig (Status-Tabelle + dieser Block aktuell,
  „Commit ⇒ Note-Update" erfüllt).

### Offene Punkte / blockers
- Keine technischen. `pricing.py` (Step 2) muss zuerst gegen den echten
  `get_market_info`-Envelope verifizieren, welche IG-Instrumentfelder heute
  durchgereicht werden (Plan §14 Sammelliste Punkt 2) — bevor der Resolver gegen
  Fixtures gebaut wird, die ggf. Felder erfinden, die P1 noch gar nicht liefert.
