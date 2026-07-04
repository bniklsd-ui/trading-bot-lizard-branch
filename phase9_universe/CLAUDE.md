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

## Session stopped — 2026-07-04 (Handover: BarProvider-Kette verdrahten — nächste Aktion, kein Nikinger-Blocker)

> **Auslöser:** Nikinger-Anweisung nach Abschluss von Step 7a — dieser Block ist
> **kein neuer Baustein**, sondern eine explizite Handover-Notiz, damit die nächste
> Session direkt mit der Step-6-Wiring-Aktivierung starten kann, statt auf den
> Step-7-Diagnose-Lauf zu warten (der bleibt Nikingers Job, ist aber **kein**
> Blocker für diese Aktion — Step 6 und Step 7 sind unabhängig).

### Ausgangslage (Code = Wahrheit, jetzt gegengelesen)
Step 6 baute `ChainedBarProvider`/`IGBarProvider`/`YFinanceBarProvider`
(`phase3_external_data/external_data/providers.py`) + einen additiven
`bar_provider`-Konstruktor-Parameter auf `MarketDataFetcher`
(`phase3_external_data/external_data/fetcher.py`) — **beides fertig, 27 Tests
grün**, aber **bewusst nicht verdrahtet**: beide Composition Roots bauen den
Fetcher weiterhin ohne `bar_provider`:
- `phase4_research/scripts/wiring.py:132` — `market_data = MarketDataFetcher(mapper,
  FileCache(str(_CACHE_DIR)))`
- `phase8_scheduler/scripts/wiring.py:160` — identische Zeile, in `_build_research`

### Nächste Aktion (konkret, für den direkten Einstieg)
1. **Zirkularitäts-Falle beachten:** `YFinanceBarProvider` braucht einen bereits
   gebauten `MarketDataFetcher` als Delegat — der aber selbst der Fetcher ist, der
   den `bar_provider` bekommen soll. Auflösung (im Recap der Vorsession bereits
   durchdacht, s. `## Session stopped` Step 6 oben): **zwei** Fetcher-Instanzen
   bauen — ein „roher" `raw_fetcher = MarketDataFetcher(mapper, cache)` (ohne
   `bar_provider`, rein yFinance) als `YFinanceBarProvider`-Delegat, und der
   „äußere" `market_data = MarketDataFetcher(mapper, cache, bar_provider=chain)`
   (der an `Research`/Consumer geht). Nur `get_bars()` prüft `bar_provider` —
   `get_drift`/`get_history`/`get_momentum`/`get_volume_anomaly` bleiben von der
   äußeren Instanz unberührt (nutzen weiterhin ihre eigene `_get_records`-Logik).
2. In beiden Wiring-Dateien: `chain = ChainedBarProvider([("ig",
   IGBarProvider(broker)), ("yf", YFinanceBarProvider(raw_fetcher))],
   health_sink=...)` bauen — `health_sink` sollte auf `observability.record_event`
   zeigen (P8-Fall; P4 hat keinen Observability-Sink, dort `health_sink=None`).
3. **Vor dem Schreiben:** mit dem Nikinger klären, ob die Aktivierung **jetzt**
   gewünscht ist (ändert den echten Research-Datenpfad — IG-Echtzeit-Bars statt
   reinem yFinance) oder ob sie — wie Step 7s `LiveQuoteCache`-Flag — hinter einem
   Default-aus-Flag bleiben soll, bis ein Live-Lauf sie bestätigt. **Das ist eine
   Nikinger-Entscheidung**, keine rein technische — s. die Reconciliation-Notiz im
   Step-6-Block unten für die Begründung, warum die Vorsession das offen gelassen hat.
4. Nach der Verdrahtung: manuelle End-to-End-Verifikation wie bei Step 5
   (`scripts/wiring.py` wird nicht von pytest importiert) — echte/Fake-Broker
   gegen einen laufenden `get_bars()`-Aufruf, prüfen dass IG-Bars bevorzugt werden
   und der yFinance-Fallback bei simuliertem IG-Ausfall greift.

### Offene Punkte / blockers
- Keine technischen Blocker für diese Aktion. Die einzige offene Frage ist die
  Nikinger-Entscheidung aus Punkt 3 oben (jetzt scharf schalten vs. hinter einem Flag).
- Step 7 (Lightstreamer-Diagnose-Lauf + Fix) bleibt **separat** blockiert auf den
  Nikinger und hat keine Abhängigkeit zu dieser Aktion.

---

## Session stopped — 2026-07-04 (Step 7a: Lightstreamer-Diagnose-Harness gebaut — Live-Lauf steht aus)

> **Auslöser:** direkte Fortsetzung nach Step 6. **Nur das Script** — der eigentliche
> diagnostische Wert entsteht erst, wenn der Nikinger es live gegen IG-Demo laufen
> lässt (braucht eine echte Lightstreamer-Session während der Handelszeiten,
> Mo–Fr 08:00–22:30 CET). Step 7b (der Fix) ist **nicht** Teil dieser Session —
> er folgt der Diagnose, nicht ihr voraus.

### Completed
- **`scripts/diag_lightstreamer_multi.py`** (neu, repo-root, phasenlos — mirrort
  `resolve_epics.py`/`verify_instrument.py`s Konvention). Abonniert den aktiven
  Phase-9-Universum-Epic-Satz (Fallback: die kuratierte 4er-Liste, inkl. der
  live-verifizierten DAX-Anchor als Sanity-Kontrolle) in zwei Modi:
  - **M1** — eine `Subscription` pro Epic (das heutige `IGLightstreamerClient`-
    Verhalten, `_do_subscribe` in `ig_lightstreamer.py`).
  - **M2** — eine `Subscription` mit einer Item-Liste
    (`["PRICE:{acct}:{e1}", "PRICE:{acct}:{e2}", ...]`).
  Fängt je Epic/Modus `onSubscription`/`onSubscriptionError`/`onItemUpdate`-Zähler
  + den Client-Status am Ende. **`classify_hypotheses(m1, m2)`** — reine Funktion,
  markiert H1 (Item-String-Problem: gleicher Epic scheitert in beiden Modi), H2
  (Subscription-Limit: nur M1 scheitert), H3 (Modus-abhängig: unterschiedliche
  Fail-Sets), H4 (Instrumentklasse: nie aus diesem Harness allein auflösbar, immer
  `False` — braucht menschlichen Abgleich gegen `instrument_universe.instrument_type`).
- **`tests/test_diag_lightstreamer_multi.py`** (root, importlib-Pattern wie
  `test_resolve_epics.py`) — **13 Tests**: `EpicOutcome`/`ModeReport`-Dataclasses,
  alle vier Hypothesen-Kombinationen von `classify_hypotheses` (inkl. „identische
  Fails in beiden Modi ⇒ H3 False"), `run_mode` gegen eine Fake-SDK-Client/
  -Subscription (M1 = N Subscriptions, M2 = 1 Subscription mit Item-Liste, invalider
  Modus wirft, Pacing via injiziertem `sleep_fn`), `--help` exit 0. **Nur die reine
  Logik ist getestet** — das eigentliche Subscribe-und-auf-SDK-Callbacks-warten ist
  Live-only (kein sinnvolles Fake für Lightstreamers async Callback-Threading-
  Modell), konsistent mit `scripts/test_lightstreamer.py`, das aus demselben Grund
  ebenfalls keine pytest-Tests hat.

### ⚠ Bekannte Einschränkung (im Code dokumentiert, ehrlich)
M2s Listener-Registrierung (`sub.addListener(...)` einmal je Epic auf **derselben**
Subscription) kann `onItemUpdate` nicht zuverlässig einem einzelnen Epic zuordnen,
falls die SDK-Version die Item-Position nicht im Callback trägt — das Script
dokumentiert das an Ort und Stelle. Für die Diagnose ist das unkritisch: die
harten Signale (`onSubscriptionError` pro Epic, `client.getStatus()`) sind
Modus-übergreifend eindeutig; nur die feingranulare Update-Zählung in M2 ist mit
Vorbehalt zu lesen.

### Verifiziert
- `pytest tests/test_diag_lightstreamer_multi.py -v` → **13 passed**. `python
  scripts/diag_lightstreamer_multi.py --help` → exit 0, kein Netz-/Keyring-Import
  (`main()`s Broker-/SDK-Imports bleiben lazy). `pytest tests -q` (root) → **77
  passed** (64 + 13). Volle Regression unverändert: P1 52 · P2 76 · P3 100 ·
  P4 141 · P5 154 · P6 70 · P7 133 · P8 215 · P9 67.
- **Ein Python-Fallstrick gefunden + gefixt:** `dataclass`-Decorators in einem via
  `importlib.util.module_from_spec` geladenen Modul crashen, wenn das Modul nicht
  vorher in `sys.modules` registriert wird (`dataclasses`-Internals lesen
  `sys.modules[cls.__module__]` nach) — `resolve_epics.py`/`verify_instrument.py`
  hatten dieses Problem nie, weil sie keine `@dataclass`-Klassen auf Modul-Ebene
  definieren. Fix im Testfile: `sys.modules[_spec.name] = diag` **vor**
  `_spec.loader.exec_module(diag)`.

### Next
- **Der Nikinger:** `python scripts/diag_lightstreamer_multi.py` während der
  Handelszeiten laufen lassen (optional `--settle-s 15` bei wenig Ticks, `--epic`
  wiederholbar für einen anderen Epic-Satz). Ergebnis-JSON als neue datierte
  Sektion in `phase1_broker_wrapper/lightstreamer_integration_notes.md`
  dokumentieren (bestehende Konvention der Datei).
- **Danach (Step 7b, separate Session):** der Fix in
  `phase1_broker_wrapper/broker_wrapper/streaming/ig_lightstreamer.py` folgt aus
  der Diagnose — Plan §10 nennt als wahrscheinlichste Form „Subscribe-Strategie
  auf eine Subscription je Epic normieren + Epic-String-Validierung vor Subscribe
  + `onSubscriptionError`-Handler mit per-Epic-Fehlerdurchreichung statt
  Silent-Fail", aber das ist eine Vermutung, keine Vorwegnahme der echten Ursache.
  Danach `LiveQuoteCache` + P4-Kontext-Enrichment (Flag default aus).
- Step 8 (Operator-Live-Runs: Autonomie-Beweis + Breaker-Fire) folgt nach 7b.

### Offene Punkte / blockers
- **Blockiert auf den Nikinger:** der eigentliche Diagnose-Lauf. Ohne ihn bleibt
  H1–H4 unentschieden — das Script kann nicht mehr tun, als bereitzustehen.

---

## Session stopped — 2026-07-04 (Step 6: V2b-i BarProvider-Kette + Circuit-Breaker + Divergenz-Check — abgeschlossen)

> **Auslöser:** direkte Fortsetzung nach Step 5, gleiche Session, Auto-Modus. Erster
> V2b-Step (Daten-Input-Zuverlässigkeit) — alles in P3 (`external_data`) + P8
> (`observability.py`), additiv, Default-Pfad bit-identisch.

### Reconciliation (Code = Wahrheit — vor dem Bau verifiziert)
- **Backoff existierte bereits.** Der Plan verlangte einen `_with_backoff`-Helper um
  die rohen yfinance-Calls — `fetcher.py` hat das **schon**: `_fetch_with_retry`
  (exponentiell 1s→2s→4s, ≤3 Versuche, unterscheidet Rate-Limit vs. leer/kurz).
  Keine Duplikation gebaut, nur der **Circuit-Breaker** (der echte Lückenschluss)
  kam neu dazu.

### Completed
- **`external_data/exceptions.py`:** neue `CircuitOpenError(ExternalDataError)` —
  gleiche Familie wie `DataUnavailableError`/`RateLimitError`, degradiert also
  automatisch überall dort, wo schon `except ExternalDataError` steht
  (`get_brain_context`'s `field_errors`), ohne einen einzigen Call-Site anzufassen.
- **`fetcher.py`:** neue `_TickerCircuit`-Klasse (per-Symbol, `open_after=4`,
  `cooldown_s=900`, injizierbarer `now_fn` — kein echtes Sleep in Tests). In
  `_get_records` verdrahtet: offen → sofortiger `CircuitOpenError` **ohne**
  Netz-Versuch; Erfolg → Reset; `DataUnavailableError`/`RateLimitError` → Failure
  gezählt. **On-by-Default** (mirrort das `RateLimiter`-Default-Muster — ein
  gesundes Symbol trippt ihn nie, kein bestehender Test simuliert 4 konsekutive
  Fails). **+9 Tests** (`test_circuit.py`).
- **`fetcher.py` (additiv):** neuer Konstruktor-Parameter `bar_provider: Any | None
  = None`. `get_bars()` delegiert an ihn, wenn gesetzt (Off-Hours-Guard bleibt
  **im Fetcher**, nicht dupliziert pro Provider); Default `None` → exakt der
  ursprüngliche yFinance-Pfad, **Reihenfolge unverändert** (erst `epic_to_yf`,
  dann Off-Hours-Check — bit-identisch für jeden bestehenden Aufrufer).
- **`external_data/providers.py`** (neu): `BarProvider`-Protocol,
  `IGBarProvider` (mapped IG-`get_ohlcv`-Envelopes → `PriceBar`, Resolution-Map
  `5m→MINUTE_5` etc., nie ein Crash — jeder Fehlerpfad → `None`), `YFinanceBarProvider`
  (delegiert an einen injizierten Fetcher, kein Re-Implement), `ChainedBarProvider`
  (erster Non-`None` gewinnt, `health_sink`-Events `{"event":"bar_fetch","provider":
  ...,"epic":...,"ok":bool}`, fail-soft bei Provider- **und** Sink-Exceptions).
  **+18 Tests** (`test_providers.py`).
- **`phase8_scheduler/scheduler/observability.py`:** neue generische
  `record_event(path, event)` (Geschwister zu `record_cycle`s festem Schema — für
  `bar_fetch`/`circuit_open`/`quote_divergence`/`universe_*`, teilt sich denselben
  Log via einem extrahierten `_append`-Helper) + `compute_divergence_pct`/
  `check_divergence` (reine Funktionen, `> 0.5% Default-Schwelle` → ein
  `quote_divergence`-Event, sonst `None` — gated nichts, root rule 3). **+10 Tests**.

### ⚠ Bewusst NICHT in dieser Session: Wiring-Aktivierung
Die Kette (`ChainedBarProvider`) ist **gebaut + vollständig getestet**, aber
**noch nicht** in `phase4_research/scripts/wiring.py` / `phase8_scheduler/scripts/
wiring.py` verdrahtet (der Live-Daemon nutzt weiterhin ausschließlich den
yFinance-Pfad für `get_bars`). Begründung: das Umschalten des tatsächlichen
Research-Datenpfads (IG-Echtzeit-Bars statt yFinance) ist eine Live-Verhalten-
Entscheidung mit realer Trading-Relevanz — dieselbe Vorsicht, die der Plan selbst
für Step 7s `LiveQuoteCache`-Flag vorschreibt ("default aus, Wiring schaltet erst
nach 7a/7b-PASS an"). Aktivierung bleibt ein bewusster, separater Schritt (Nikinger-
Entscheidung), sobald gewünscht — der Fetcher-Konstruktor nimmt `bar_provider`
bereits entgegen, es fehlt nur der Wiring-Aufruf, der ihn tatsächlich baut+übergibt.

### Verifiziert
- `pytest phase3_external_data/tests -q` → **100 passed** (73 + 27: 9 circuit +
  18 providers). `pytest phase8_scheduler/tests -q` → **215 passed** (205 + 10).
- Import-Isolation: `import external_data` zieht weiterhin **NONE** cross-phase
  (broker_wrapper/persistence/universe/research/execution/reward/debate/scheduler/
  anthropic — alle abwesend, `providers.py`s `IGBarProvider`/`ChainedBarProvider`
  sind rein duck-typed, kein `broker_wrapper`-Import nötig).
- Volle Regression: P1 52 · P2 76 · **P3 100 (+27)** · P4 141 · P5 154 · P6 70 ·
  P7 133 · **P8 215 (+10)** · root 64 · P9 67. `py_compile` clean auf allen
  berührten Dateien.

### Next
- **Step 7 — V2b-ii: Lightstreamer Multi-Epic (Diagnose → Fix → LiveQuoteCache).**
  7a (Diagnose-Harness `scripts/diag_lightstreamer_multi.py`) ist ein **Operator-
  Live-Lauf** — kann nicht von Claude Code allein abgeschlossen werden (braucht
  echte IG-Demo-Verbindung während der Handelszeiten). 7b (Fix + `LiveQuoteCache`)
  folgt erst **nach** 7a-PASS.
- Danach Step 8 (Operator-Live-Runs: Autonomie-Beweis + Breaker-Fire).

### Offene Punkte / blockers
- **Step 7a braucht den Nikinger** (Live-Lauf gegen IG-Demo während Handelszeiten
  Mo–Fr 08:00–22:30 CET). Bis dahin kann der 7a-Diagnose-Harness selbst gebaut
  werden (reines Script, kein Fix), aber nicht ausgeführt/ausgewertet.
- Die Wiring-Aktivierung von Step 6 (s. o.) bleibt eine offene Nikinger-Entscheidung.

---

## Session stopped — 2026-07-04 (Step 5: P4/P8-Integration — abgeschlossen)

> **Auslöser:** direkte Fortsetzung nach Step 4, gleiche Session, Auto-Modus. Der erste
> Step, der **außerhalb** von `phase9_universe/` schreibt (P4 `research/models.py` +
> `scripts/wiring.py`, P8 `scheduler/{config,state,runner}.py` + `scripts/wiring.py`) —
> alles additiv, Default-Pfad bit-identisch, per Plan §11 Cross-Phase-Edit-Register
> sanktioniert.

### Completed
- **P4 `research/models.py`:** neue `universe_from_records(records, *,
  fallback=EXTENDED_UNIVERSE) -> tuple[InstrumentSpec, ...]` — baut+validiert eine
  Instrument-Universe-Tupel aus `InstrumentSpec`-förmigen Plain-Dicts (z. B.
  `UniverseRecord.to_instrument_spec()`), fällt bei leerem Input auf
  `EXTENDED_UNIVERSE` zurück (`logger.warning`, nie still, nie Crash). **Phase 4
  importiert weiterhin nichts aus `universe`** — die Dict-Grenze wahrt die
  Phasen-Isolation. Exportiert aus `research.__init__`. **+6 Tests**
  (`test_universe.py`) → **P4 135 → 141**.
- **P4 `scripts/wiring.py`:** neue `build_universe_from_db(db_path=None) ->
  tuple[InstrumentSpec, ...]` — öffnet einen `universe.UniverseStore` (lazy Import),
  liest `active_universe()`, mappt via `universe_from_records`; Fallback bei
  Unreachable/Empty auf `EXTENDED_UNIVERSE` (fail-soft, `logger.warning`).
  `build_research()`s Default nutzt jetzt diese Funktion statt hartkodiertem
  `EXTENDED_UNIVERSE` — ein unbeautes/unreachable Phase-9-Checkout verhält sich
  **bit-identisch** zum Vor-Phase-9-Stand.
- **P8 `scheduler/config.py`/`state.py`/`runner.py`:** `universe_refresh_interval_min`
  (Default 240), `last_universe_refresh_ts` (Cross-Day-Feld), optionaler
  `universe_refresher`-Konstruktor-Parameter am `SchedulerRunner` (Default `None` =
  heutiges Verhalten). Aufgerufen einmalig in `preflight()` + danach throttled in der
  WINDOW-Phase (nie im Research-Tick selbst) via einem aus `_due()` extrahierten
  generischen `_due_after()`. Fail-soft (Exception → `logger.critical`, nie ein
  Cycle-Crash/Backoff-Trip). **+6 Tests** → **P8 199 → 205.** Details im
  `phase8_scheduler/CLAUDE.md`-Session-Block von heute.
- **P8 `scripts/wiring.py`:** `_build_universe_from_db()` (dupliziert aus P4s
  Funktion — die `scripts.wiring`-Namenskollision über Phasen verbietet den Import),
  `_build_research()` nutzt sie statt hartkodiertem `EXTENDED_UNIVERSE`. Neue
  `universe_refresher`-Closure in `build_scheduler()` (Discover + `run_promotion_cycle`
  über den geteilten Broker + `research.market_data`), an `SchedulerRunner`
  durchgereicht.

### ⚠ Reconciliation (Code = Wahrheit)
- Da `scripts/wiring.py` laut etablierter Repo-Konvention **nicht** von pytest
  importiert wird (würde Keyring/Netzwerk-Imports ziehen), sind
  `build_universe_from_db`/`_build_universe_from_db`/die `universe_refresher`-Closure
  **nicht unit-getestet** — konsistent mit jeder anderen Funktion in diesen Dateien.
  Stattdessen: **manuelle End-to-End-Verifikation** dieser Session (echte Migration-
  004-DB, 1 geseedeter DAX-Record → `build_universe_from_db` liefert `[DAX]`; leere/
  fehlende DB → korrekter Fallback auf `EXTENDED_UNIVERSE`, kein Crash, korrekt
  geloggte Warnung) — die pure Logik dahinter (`universe_from_records`) trägt die
  volle Testabdeckung.

### Verifiziert
- `pytest phase9_universe/tests -q` → **67 passed** (unverändert — Step 5 fügt der
  `universe`-Package selbst keine neuen Dateien hinzu, nur Konsumenten in P4/P8).
- Volle Regression: P1 52 · P2 76 · P3 73 · **P4 141 (+6)** · P5 154 · P6 70 · P7 133 ·
  **P8 205 (+6)** · root 64 · P9 67. Import-Isolation aller vier `universe`-Module
  weiterhin bestätigt (0 cross-phase Leaks, unverändert seit Step 4).
- `py_compile` clean auf allen berührten Dateien in P4/P8/P9.

### Next
- **Step 6 — V2b-i: BarProvider-Kette + yFinance-Härtung + Divergenz-Check** (P3
  `external_data/providers.py` neu, `fetcher.py` additiv: Backoff + Circuit-Breaker).
  Vor dem Bau: P3s Off-Hours-Check-Ort + exakte yfinance-Call-Sites in `fetcher.py`
  gegenlesen (Plan §14 Punkt 3).
- Danach Step 7 (V2b-ii: Lightstreamer-Multi-Epic-Diagnose → Fix → `LiveQuoteCache`),
  Step 8 (Operator-Live-Runs).

### Offene Punkte / blockers
- Keine technischen. Die vier Kernmodule + die P4/P8-Integration sind fertig — die
  Discover→Verify→Promote-Pipeline ist jetzt vollständig **end-to-end verdrahtet**
  (wenn auch mangels Operator-Live-Lauf noch nicht live bewiesen). V2b (Steps 6–7)
  ist der einzige verbleibende Baustein vor den Operator-Live-Runs.

---

## Session stopped — 2026-07-04 (Step 4: `promotion.py` — abgeschlossen)

> **Auslöser:** direkte Fortsetzung nach Step 3, gleiche Session, Auto-Modus.

### ⚠ Reconciliation (Code = Wahrheit, vor dem Bau verifiziert)
- **Der Plan zitiert `phase8_scheduler/scripts/verify_instrument.py` — das Skript liegt
  tatsächlich phasenlos im Repo-Root: `scripts/verify_instrument.py`.** Signaturen
  (`check_ig_side(broker, epic, *, sleep_fn, pace_s)`, `check_yf_side(fetcher, epic, *,
  volume_proxy=None)`, `verdict_for(epic, ig_checks, yf_checks)`, plus eine bereits
  komponierte `verify_instrument(broker, fetcher, epic, *, volume_proxy=None, sleep_fn,
  pace_s) -> dict`) stimmen exakt mit der Plan-Beschreibung überein — nur der Ordner war
  falsch zitiert. `promotion.py` importiert die **komponierte** `verify_instrument(...)`
  (spart die einzelne `check_ig_side`+`check_yf_side`+`verdict_for`-Orchestrierung) via
  `importlib.util.spec_from_file_location`, exakt das in `tests/test_resolve_epics.py`
  etablierte Muster.

### Completed
- `universe/promotion.py` (neu): `run_promotion_cycle(broker, fetcher, store, *,
  is_demo, max_active=8, demote_after_fails=3, pace_s=1.0, sleep_fn, health_sink=None,
  now_fn) -> PromotionReport`. Safety-Raise zuerst (`is_demo=False` → `UniverseSafetyError`,
  hart, kein Bypass). Drei Schritte: (1) `discovered`/`quarantined`-Kandidaten mit
  Backoff-Treppe (`2**fail_count` Stunden gegen `last_verified_at`) verifizieren + Pricing
  auflösen — PASS+Pricing → `verified`+`set_pricing`; PASS ohne Pricing → bleibt
  `discovered`; FAIL → `quarantined`+`fail_count++`. (2) alle `verified` → `active` bis
  `max_active`. (3) Health-Recheck aller `active`: IG-seitiger Fail → `fail_count++` →
  `demote_after_fails` erreicht → `quarantined`; **Erfolg → `fail_count` auf 0
  zurückgesetzt** (Konzept C3, IG-spezifischer Zähler); yFinance-seitiger Fail →
  **ausschließlich** `data_degraded=True`, **nie** eine Demotion — unabhängig vom IG-Status
  gesetzt/gelöscht. Kuratierte Bestätigung (`point_value_source IS NULL` + IG-Seite
  gesund) via `confirm_curated`: `True` → `set_pricing` mit dem aufgelösten Source-Tag;
  `False` → Quarantäne + `logger.warning` (ein widerlegter kuratierter Wert ist
  gefährlicher als ein fehlender); `None` → keine Änderung.
- **`universe/store.py` erweitert (additiv):** `set_status()` bekam zwei neue
  keyword-only Parameter, `reset_fail_count: bool = False` (Alternative zu
  `fail_increment`, beide betreffen denselben Zähler) und `data_degraded: bool | None
  = None` (unabhängiges Feld — betroffen war vorher **gar nicht** in `set_status`
  schreibbar, ein echter Gap gegenüber Migration 004s Spalte). **Default-Verhalten
  bit-identisch** für alle bestehenden Aufrufer (Steps 1–3 berühren `data_degraded`/
  `reset_fail_count` nirgends).
- **14 neue Tests** (`test_promotion.py`): Safety-Raise, Happy-Path
  discovered→verified→active, PASS-ohne-Pricing bleibt liegen, Verify-Fail→Quarantäne,
  `max_active`-Kappung, Demotion nach 3 IG-Fails (Zyklus-für-Zyklus), yF-Fail demotiert
  nie + setzt `data_degraded` (+ ein Recovery-Test, der es wieder löscht), Backoff-Treppe
  (blockiert + erlaubt nach Ablauf), nie-verifiziert = sofort eligible, kuratierte
  Bestätigung + Widerspruchs-Quarantäne, `health_sink`-Events, Report-Defaults. **+6 neue
  Tests** in `test_store.py` für die zwei neuen `set_status`-Kwargs (Reset, Set/Clear,
  Default-Kwargs-No-Op).
- `universe/__init__.py`: `run_promotion_cycle`/`PromotionReport` exportiert.

### Verifiziert
- `pytest phase9_universe/tests -v` → **67 passed** (19+6 store + 15 pricing + 14
  discovery + 14 promotion — die 6 store-Zusatztests kamen in diesem Step dazu, s. o.).
- Import-Isolation erneut bestätigt (0 cross-phase Leaks) — der dynamische
  `verify_instrument.py`-Load bleibt lazy in `_load_verify_instrument()`, nie am
  Modul-Top von `promotion.py`. Kein `import anthropic` irgendwo im Paket.
- Volle Regression unverändert grün: P1 52 · P2 76 · P3 73 · P4 135 · P5 154 · P6 70 ·
  P7 133 · P8 199 · root 64 · **P9 67**.

### Next
- **Step 5 — P4/P8-Integration:** `build_universe_from_db(store) -> tuple[InstrumentSpec,
  ...]` in `scripts/wiring.py` (P4), optionale `universe_refresher`-Naht in
  `phase8_scheduler/scheduler/runner.py` (P8, Default `None` = heutiges Verhalten
  bit-identisch). **Cross-Phase-Edits — vor dem Bau** die exakten Stellen gegenlesen, an
  denen P4/P8-Wiring heute `EXTENDED_UNIVERSE`/`TickerMapper` verdrahten (Plan §14 Punkt 4
  + 5).

### Offene Punkte / blockers
- Keine technischen. Alle vier universe-Kernmodule (models/store/pricing/discovery/
  promotion) sind jetzt fertig — Step 5 ist der erste Schritt, der **außerhalb** von
  `phase9_universe/` schreibt (P4 `scripts/wiring.py`, P8 `scheduler/runner.py`).

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
