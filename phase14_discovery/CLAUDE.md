# CLAUDE.md — Phase 14: Discovery-Then-Deterministic (`phase14_discovery/`)

> Zwei Phasen lang war „welche Quelle kann Epic X?" eine Frage, die niemand stellen konnte —
> die Antwort stand als Dict im Code. Phase 14 macht sie zu einer Zeile in der DB.
> **Quelle der Wahrheit ist der Plan + der Code, nicht dieses Dokument.**
> Vollständiger Plan: [`../docs/concepts/phase14_discovery_plan.md`](../docs/concepts/phase14_discovery_plan.md).
> Vorgeschichte: [`../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md`](../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md) §1.5.

## Mission (zuerst lesen)

**Was eine Quelle kann, sagt die Quelle — nicht der Konsument.**

1. **Discovery first.** Jede Quelle exponiert ihr Liefer-Spektrum als `SourceProfile`.
2. **Kreuzung second.** `instrument_source_availability` (Migration 007) hält
   IG-Epic × Quelle × Auflösung — inklusive des **quelleneigenen Symbols**.
3. **Determinism last.** Der Konsument liest die Tabelle und wird dadurch *einfacher*.

**Done-Kriterium:** PASS A1–A8 (Plan §7). Die zwei harten davon:
`grep -rn "EPIC_MAP" phase13_live_data/ --include=*.py` ist **leer**, und Discovery gibt
**strukturell** null IG-Punkte aus (Test mit einem Broker, der bei jedem Call wirft).

## Bauprinzip

„So wenig AI wie möglich, so viel AI wie nötig." **Phase 14 fügt NULL neues AI hinzu.**
Quell-Entdeckung, Symbol-Zuordnung, Verfügbarkeits-Bewertung und Scharfschalt-Logik sind
deterministischer Code. Wer hier ein LLM „Quellen bewerten" oder „Symbole raten" lassen
will → **stop**, das ist Code.

## Scope

- **DRIN:** `source_registry/` (Modelle, Store, Quell-Profile, Scharf-Flag, Daemon),
  Migration 007, die Projektions-Naht in `phase9_universe/universe/store.py::set_symbol`,
  der `stale_source`-Vokabular-Fix in `phase9_universe/universe/models.py`, der
  Symbol-Lookup statt `EPIC_MAP` in `phase13_live_data/live_data/backfill.py`, die
  Drei-Fälle-Trennung in `scripts/source_delta.py`, das Scharfschalten in
  `phase8_scheduler/webui/`.
- **DRAUSSEN:** `measurable_universe()` / `data_source_status` umbauen (D3), `prefer` in
  `BarArchive.window` (D7), Dukascopy (D15), `KNOWN_SOURCES` dynamisch (D17), zentrale
  Quell-Verwaltung (Auth/Rate-Limits bleiben je Quelle), `TickerMapper`-Cache,
  Momentum-VETO/Gates/Sizing/P6/P7, `resolve_paper_trade`, die Phase-13-Beweiswoche
  (separater Track, läuft parallel).

## Rahmen

- **Werktags-Arbeit erlaubt, auch bot-berührend.** Vorher den Bot stoppen,
  `ps aux | grep scheduler.run` als Gegenprobe (Parallel-Login-Falle).
- **Live-/Netz-/kostenpflichtige Läufe macht der Nikinger.** Befehl vorbereiten, Kosten
  nennen, vorher fragen. In Phase 14 sind das genau zwei: die Capital.com-`/markets`-Probe
  (B1a, Demo, kostenlos) und die Migration 007 gegen die Produktions-DB (mit Backup).
- **Live-DB nur `mode=ro`.**
- **Cross-Phase-Edits sind für Phase 14 freigegeben** (Nikinger 2026-08-22) für **Phase 2**
  (Migration), **Phase 8** (`webui/`, `run_scheduler.sh`), **Phase 9** (`models.py`,
  `store.py`), **Phase 12** (`budget.py`-Nutzung) und **Phase 13** (`backfill.py`,
  `scripts/`). Ein Touch **außerhalb** dieser Liste ist erneut freigabepflichtig.
- **Ausführungs-Sessions laufen über `claude-minimax`** (Kostengrund, Nikinger 2026-08-18),
  Debugging über `claude`. Ändert **nicht**, welches Modell der Bot selbst ruft.

## Der Kontingent-Deckel (dreifach, Plan §4 D6/D13/D14)

Die Frage „wie verhindern wir, dass Discovery das Kontingent sprengt" ist mit drei Lagen
beantwortet, von wichtig nach unterstützend:

1. **Strukturell.** Discovery ruft **nie** `/prices` und **nie** `search_markets`. Die
   IG-Zeile wird aus `instrument_universe` **abgeleitet** — jede Zeile dort *ist* per
   Definition eine IG-Epic. Der Beweis ist ein Test mit einem Broker-Fake, dessen jede
   Methode wirft (Muster L12 / `test_get_window_never_fetches`), **kein** Zählwert.
2. **Zwei Kontingente, nicht eins.** Das 10 000-Punkte-Kontingent (`/prices`, rollierende
   7 Tage) hat Phase 11 gesprengt; das API-Key-Kontingent (~30 req/min, 403
   `exceeded-api-key-allowance`) hat Phase 9 gesprengt (`discovery.py:183-189`, Pacing
   1,0 s → 2,5 s). Discovery berührt **keins von beiden**, weil sie IG gar nicht ruft.
3. **Deckel für alles, was doch fetcht** — heute nur Capital.com (Demo, kostenlos):
   `max_probe_calls_per_source_per_run=8`, TTL `profile_ttl_days=7` gegen
   `last_verified_utc`, und jede Ausgabe gebucht als `spend_kind='discovery'` im
   existierenden `source_spend`-Ledger (Muster `GapRescue`s `'rescue'`). Sichtbar statt
   unsichtbar.

Dazu kommt der Betriebs-Deckel: der Daemon tut **nichts**, solange
`data/state/DISCOVERY_ARMED` fehlt (D10) — die sichere Richtung jeder Mehrdeutigkeit ist
**nicht scharf**. Unscharf kostet null.

## Modul-Tabelle

> Stand: **nichts gebaut.** Diese Tabelle wird in Block D gegen den As-Built-Stand gefüllt
> (Testzahlen aus dem finalen Sweep, nicht geschätzt).

| Datei | Zweck | Status |
|---|---|---|
| `source_registry/models.py` | `SourceAvailability`, `SourceProfile`, `Source`-Protocol, `origin`-Vokabular | ⬜ A2/A3 |
| `source_registry/store.py` | `SourceAvailabilityStore` — der einzige Zugriff auf Migration 007 | ⬜ A2 |
| `source_registry/sources.py` | `IGDerivedSource`, `LSStaticSource`, `RegistryYFSource` — alle drei ohne Netz | ⬜ A3 |
| `source_registry/arm.py` | Scharf-Flag `data/state/DISCOVERY_ARMED` (Muster `killswitch.py`, sichere Richtung umgedreht) | ⬜ C1 |
| `source_registry/run.py` | Der Daemon (Muster `data_foundation/run.py`: PID-File, graceful SIGTERM, `--once`) | ⬜ C2 |
| `scripts/run_discovery.sh` | Start-Wrapper (Muster `run_recorder.sh`) | ⬜ C4 |
| *(cross-phase)* `phase2_persistence/migrations/007_phase14_source_availability.sql` | die Kreuzungs-Tabelle **+ der einmalige yF-Backfill aus `instrument_universe`** (der Grundbestand kommt aus der Migration, nicht aus einem Resolver-Lauf — `resolve_epic` ruft `set_symbol` in sechs von acht Pfaden nicht) | ⬜ A2 |
| *(cross-phase)* `phase9_universe/universe/models.py` | `DS_STALE_SOURCE` ins Vokabular (Live-Blocker B1) | ⬜ A1 |
| *(cross-phase)* `phase9_universe/universe/store.py` | yF-Projektion in `set_symbol`, nicht-fatal | ⬜ A4 |
| *(cross-phase)* `phase13_live_data/live_data/backfill.py` | `EPIC_MAP` raus, Symbol-Lookup rein; `CapitalSource.discover()` | ⬜ B1/B2 |
| *(cross-phase)* `phase13_live_data/scripts/source_delta.py` | drei Fälle statt zwei (`not_available` / `available_but_empty` / `compared`) | ⬜ B3 |
| *(cross-phase)* `phase8_scheduler/webui/api.py` + `static/` | `GET /api/discovery`, ARM/DISARM, Warn-Banner | ⬜ C3 |

---

## Session stopped — 2026-08-22 (Session 3: Block A2 — Migration 007 + SourceAvailabilityStore)

> **Auftrag:** Nikinger-Bestätigung „gehe nach Plan vor" → Block A2.
> Plan §6 A2 hat vier Edits: Migration 007, `models.py`, `store.py`, 12 Tests
> + Versions-Anpassung im P2-Migration-Test. **Ein Commit**, **null
> Aufrufer verdrahtet** (A2 ist Fundament, A3/A4 ziehen nach).

### Completed

**`phase2_persistence/migrations/007_phase14_source_availability.sql`** (NEU,
additive only) — legt `instrument_source_availability` an (10 Spalten, PK
`(epic, source, resolution)`) **plus** den yF-Backfill als `INSERT … SELECT`
aus `instrument_universe` in derselben Datei. Backfill ist nicht in einem
Resolver-Lauf, weil `SymbolResolver.resolve_epic` `set_symbol` in 6 von 8
Pfaden NICHT ruft (`symbols.py:194-199, 207-210, 213-214, 219-220, 222-223,
229-230`) — die 3 `SUN*`-Epics stehen bereits auf `no_intraday_source` und
bekämen sonst nie eine Projektionszeile. Der Backfill kauft zusätzlich den
Identitätsbeweis (B2: `source_symbol = yf_ticker`) VOR der ersten Zeile
neuem Code; Test 11 prüft das gegen die heutigen 22 Zeilen Substrat.
Kein `FOREIGN KEY` auf `epic` — bewusst (Auditkette: 001–006 haben keinen
FK, `UniverseStore` öffnet ohne `PRAGMA foreign_keys = ON`, ein
nicht-erzwungener FK ist Doku die sich als Constraint verkleidet).

**`phase14_discovery/source_registry/models.py`** (NEU) — Dataclasses +
Konstanten + Protocol, Phase-Isolation per Duplikation (Muster
`UniverseStore`/`Budget`/`BarArchive`): `KNOWN_AVAILABILITY_STATUSES`
dupliziert `KNOWN_DATA_SOURCE_STATUSES` aus Phase-12 (D18 — identischer
Vokabular, Drift wäre der nächste Bug); `REGISTRY_SOURCES` spiegelt die
4 heute existenten Quellen (`ig`/`yf`/`ls`/`capital`); `KNOWN_ORIGINS`
(discovery/registry/derived/operator); `KNOWN_RESOLUTIONS` (1m/5m/1h/1d).
`SourceAvailability(frozen=True)` mit `__post_init__`-Validierung an allen
drei Vokabularen; `SourceProfile(frozen=True)` mit `rows`/`probe_calls_used`/
`errors`; `Source` Protocol mit `name()`/`discover(epics, *, max_probe_calls)`.

**`phase14_discovery/source_registry/store.py`** (NEU) —
`SourceAvailabilityStore` mit eigener `sqlite3`-Connection
(Phase-Isolation), 8 Methoden exakt nach Plan §5.3: `upsert`,
`upsert_many`, `for_epic`, `for_source`, `symbol_for`, `stale_rows`,
`close`. `upsert` ist `INSERT … ON CONFLICT(epic, source, resolution) DO
UPDATE` (Muster `UniverseStore.upsert_discovered`).
`symbol_for` gibt `None` statt zu raisen — Block-B2-Vertrag: „kein
Eintrag" liest sich als „diese Quelle kann das nicht", Fall-Back ist
Sache des Konsumenten (nicht des Stores). `stale_rows` nutzt
lexikografischen Vergleich über `last_verified_utc < cutoff_iso` — nur
sicher weil jeder Timestamp aus derselben `utc_iso_now`-Formatter kommt
(Test 13 pinnt den Format-Vertrag).

**`phase14_discovery/tests/test_store.py`** (NEU) — 13 Tests (12 aus Plan +
1 Format-Contract-Pin). Test 11 ist der harte Beweis: das heutige
22-Zeilen-Substrat wird in eine Fixture-DB gesetzt (5 active+ok, 3
active+no_intraday_source, 14 verified+unverified), Migration 007 wird
**danach** angewendet, und `for_source('yf', status='ok')` muss **genau**
die 5 Epics aus Plan §2.2 liefern — die Identitäts-These hält **bevor**
irgendwelcher neuer Code sie brechen könnte. Test 10 pinnen D17: die
Tabelle gattet einen Source außerhalb von `KNOWN_SOURCES` NICHT (eine
Zeile mit `source='dukas_copy'` wird geschrieben + gelesen; der
Archiv-Schreibpfad ist der Gatekeeper, nicht die Tabelle).

**`phase2_persistence/tests/test_migrations.py`** (Anpassung, keine Test-
Anzahl-Änderung) — Versions-Nummern 6 → 7 in vier Tests
(`test_fresh_db_reaches_version_6` → `_version_7`, `test_rerun_is_noop`
count 6 → 7, `test_find_pending_respects_current` Liste 1..6 → 1..7,
`test_database_run_migrations_idempotent` 6 → 7);
`_EXPECTED_TABLES` um `'instrument_source_availability'` ergänzt.

### Verified (heute nachgemessen, 2026-08-22)

| Suite | Vor A2 | Nach A2 | Δ |
|---|---:|---:|---:|
| phase2_persistence | 77 | 77 | 0 (Versions-Nummern im Test-Body) |
| phase14_discovery | 0 | 13 | +13 (12 aus Plan + 1 Format-Contract) |
| **Summe (Regression)** | **1612** | **1625** | **+13** |

Working tree clean (nach jedem Commit), `ps aux | grep scheduler.run`
leer, kein Live-DB-Write, keine Cross-Phase-Edits außerhalb der
freigegebenen Liste (Phase 2/8/9/12/13 — alle im Scope). A2 hat null
externe Aufrufer von `source_registry` (verifiziert per `grep -rn
source_registry`): die einzigen Treffer sind die Paket-Definition
selbst und der editable-install-Marker in `.venv`. Fundament steht
isoliert.

### Cross-Phase-Anmerkungen für die nächsten Schritte

- **A4 (yF-Projektion in `UniverseStore.set_symbol`)** muss denselben
  INSERT-ON-CONFLICT-Pfad benutzen wie `SourceAvailabilityStore.upsert`,
  und die Spaltenliste steht an zwei Stellen (Migration 007 vs.
  `store.py:_project_availability`). Plan §6 A4 sagt: **rohes SQL über
  `self.conn`**, kein `source_registry`-Import in `phase9_universe` —
  Paket-Zyklus vermeiden. Der Doppelschreiber-Gleichheitstest (Plan §6 A4,
  Test 6) fängt Drift ab, sobald A4 baut.
- **`symbol_for` ist genau die Methode, die `run_capital_backfill` nach
  Block B2 ruft** statt `EPIC_MAP.get(epic)` — heute gibt sie
  `None` für alle Epics, weil die `capital`-Zeilen erst nach B1b/B2
  geschrieben werden (B1a-Sonden-Output fehlt noch — Operator-Run
  steht aus, Plan §9.3).

### Next

- **Operator (Nikinger):** Push-Freigabe für den A2-Commit (`4ef7535`).
- **Ausführende Session (nächste):** Plan §6 **Block A3** — drei
  Quell-Profile: `IGDerivedSource` (D6, **null Netz**, jede
  `instrument_universe`-Epic ⇒ abgeleitete Zeile), `LSStaticSource`
  (`bars.source='ls'` = 0 heute → `no_source`), `RegistryYFSource`
  (Projektion aus `UniverseRecord`-Shape, `origin='registry'`).
  Der **strukturelle Kostentest** (Test 2 aus A3): ein Broker-Fake,
  dessen jede Methode `AssertionError` wirft — `IGDerivedSource.discover()`
  läuft trotzdem durch, `probe_calls_used == 0`. Das ist die A3-Akzeptanz
  für D6.
- **Unverändert offen:** Capital.com `/markets`-Probe (B1a, Operator,
  Demo, kostenlos). Ohne den Output wird B1b nicht gebaut — die
  `capital`-Zeile kommt dann als `origin='operator'` über ein Seed-Script.
- **Unverändert offen:** Backup von `data/trading_bot.sqlite` vor
  Produktions-Anwendung von Migration 007 (Plan §9.13).
- **Optional (Nikinger-Entscheidung):** `ROADMAP.md:427` Korrektur-Eintrag
  (zweiter Roll-over, datiert 2026-08-22 — s. Session-2-Finding).
