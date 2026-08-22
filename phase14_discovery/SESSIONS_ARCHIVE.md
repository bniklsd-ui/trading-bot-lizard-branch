# SESSIONS_ARCHIVE.md — Phase 14 (Discovery-Then-Deterministic)

Newest-first. Rotation rule (root `CLAUDE.md`, mandatory since 2026-07-06): the phase head
carries exactly one `## Session stopped` block; the previously-newest block moves here
verbatim when a new one is appended.

---
## Session stopped — 2026-08-22 (Session 6: B1a-Operator-Probe gelaufen + Findings dokumentiert)

> **Auftrag:** Nikinger hat die B1a-Probe live ausgeführt (Demo, kostenlos) und
> den vollständigen JSON-Output im Chat gepastet. Anweisung: „alle Dokumente
> Updaten und pushen bitte". Output ist die **beobachtete Antwort-Form**,
> gegen die `CapitalSource.discover()` (B1b) gebaut wird. Snapshot-Datei
> angelegt; Session-Block dokumentiert die 8 wichtigsten Befunde; Push der
> 4 ungepushten Commits liegt beim Operator.

### Completed

**`phase14_discovery/PHASE14_B1A_PROBE_OUTPUT_2026-08-22.md`** (NEU, L3-Snapshot) —
Roh-Output der Operator-Probe + 8 nummerierte Befunde mit Mapping auf B1b.
Header-Karte nach Doku-Konvention (`status: snapshot`, `read-when`,
`up:`/`down:`). Cross-Verweis vom Plan (`docs/concepts/phase14_discovery_plan.md`).

### Die 8 Befunde — was B1a gelehrt hat

| # | Befund | Konsequenz für B1b |
|---|---|---|
| 1 | Response ist `{ "markets": [...] }` — Array, je Eintrag ein Market-Objekt | `discover()` iteriert über `markets`, filtert, emittiert pro Match eine `SourceAvailability` |
| 2 | **`epic`-Feld ist das gesuchte Source-Symbol** (`"DE40"`, `"FR40"`, `"SP35"`) | geht 1:1 in `instrument_source_availability.source_symbol` — exakt dieselbe Identitäts-These wie yF (B2) |
| 3 | `instrumentType` ist **`"INDICES"`** (nicht `"CFD"`, wie der bestehende `live_data/backfill.py:339-366`-Filter annimmt) | B1b filtert auf `"INDICES"`. **Offener Filter-Bug im bestehenden Code** — der Fallback `[m for m in markets if m.get("instrumentName") == index_name]` rettet es heute. B1b macht es richtig; bestehender Code wird in B2 oder als separates Hygiene-Ticket nachgezogen (Nikinger-Entscheidung) |
| 4 | **Spain 35 IST verfügbar** als `epic: "SP35"` (war bisher Path-C-Territorium in Phase 13) | Block B erweitert Coverage. Dukascopy-Fallback für SP35 wird überflüssig |
| 5 | Sucht mit `searchTerm=<instrumentName>` → erster Eintrag mit `instrumentName == searchTerm` + `instrumentType == "INDICES"` ist die kanonische Übersetzung | B1b-Such-Algorithmus: `for epic in input: name = instrument_universe[epic].name; GET /markets?searchTerm=name; first INDICES match → SourceAvailability` |
| 6 | `delayTime: 0` für alle drei → **Echtzeit** | `history_min_days=30, latency_min=0` für die `capital`-Zeilen (NICHT die 15-Min-yF-Heuristik) |
| 7 | Jeder Eintrag hat `instrumentId` (numerisch), `epic` (kurz), `symbol` (lang/kurz), `bid`/`offer` (Live-Preise), `lotSize`, `tickSize`, `pipPosition` | B1b braucht nur `epic` + `instrumentName` + `instrumentType`. Andere Felder sind für Discover irrelevant — kein Schema-Mapping nötig |
| 8 | `marketStatus: "CLOSED"` für alle drei am Wochenende | erwartbar (Markt zu), **kein** B1b-Sonderfall. Discover prüft Verfügbarkeit via Existenz des Eintrags, nicht via `marketStatus` |

### Operator-Setup (verifiziert, 2026-08-22)

- **Auth funktioniert:** `POST /api/v1/session` → HTTP 200, `account_type=CFD`,
  CST + X-SECURITY-TOKEN im Response-Header. **Demo-Keyring `trading-bot-capital`
  ist intakt** (Vorbedingung für B1b gegeben).
- **Drei Suchterme, drei Treffer** — alle im ersten Listeneintrag.
- **Probe-Script** (`probe_capital.py --markets --terms ...`) tat ohne
  Modifikation. Kein Code-Edit in dieser Session.

### Nicht-B1b-Stoff (separate Tasks)

- **B2 (`EPIC_MAP` raus):** Plan §6 B2 wartet auf B1b. Heute gibt
  `SourceAvailabilityStore.symbol_for(epic, 'capital')` für keinen Epic
  einen Wert (Tabelle 007 wurde nur mit yF-Backfill gefüllt). Nach B1b
  liefert sie für DE40/FR40/SP35 die richtigen Kürzel.
- **Offener Filter-Bug im bestehenden Code** (`live_data/backfill.py:339-366`,
  `backfill.py:300-316`): `"CFD" in instrumentType` matched nie — die
  Realität ist `"INDICES"`. Der Fallback `candidates = [m for m in markets
  if m.get("instrumentName") == index_name]` rettet es heute. **Nicht in
  dieser Session gefixt** — bewusst zurückgestellt (Phase-14-Cross-Phase-
  Edit nur für Phase 2/8/9/12/13 freigegeben; eine Edit in `backfill.py`
  ist Phase-13-Territorium und gehört in B2 oder als separates Ticket).
  **Empfehlung:** in B2 mit aufnehmen, weil B2 den `EPIC_MAP`-Hintergrund
  eh anfasst.

### Verified (heute nachgemessen, 2026-08-22)

| Suite | Vor B1a | Nach B1a | Δ |
|---|---:|---:|---:|
| (alle Suiten) | 1634 | 1634 | 0 (B1a war Operator-Run, kein Code-Edit) |

Working tree clean (außer Hygiene-Findling `*.sqlite.bak-*`-Pattern aus Session 4),
`ps aux | grep scheduler.run` leer, kein Live-DB-Write. Cross-Phase-Edits: null
in dieser Session.

### NEXT

- **Operator (Nikinger):** Push-Freigabe für die **4 ungepushten Commits**:
  ```bash
  cd /home/trading-bot/trading-bot
  git push origin main
  ```
  Reihenfolge: `fd9e7f8` (A3-Code, 491 Zeilen), `888ee01` (Session-4-Docs,
  Rotation), `69cfc31` (B1a-Script-Erweiterung, +79 Zeilen),
  `+der B1a-Snapshot + Session-6-Docs aus dieser Session` (nach commit).
- **Ausführende Session (nächste):** Plan §6 **Block A4** (yF-Projektion
  in `UniverseStore.set_symbol`) **ODER** Block B1b (`CapitalSource.discover()`
  gegen die beobachtete Form, Snapshot als Quell-der-Wahrheit). Beide sind
  jetzt baubar; meine Empfehlung **B1b zuerst** weil:
  1. Der Snapshot ist die genaueste Spec — direkt in Code umsetzbar.
  2. Block B2 wartet auf B1b.
  3. A4 ist orthogonal und kann danach kommen.
  Sag, welche Reihenfolge.
- **Unverändert offen:** A4 (yF-Projektion), B2 (`EPIC_MAP` raus), B3
  (`source_delta.py` drei Fälle), C (Daemon), D (Closeout). Plus die zwei
  Optional-Hygiene-Tickets aus Session 4 (`.gitignore`-Pattern, `ROADMAP.md:427`).

---
## Session stopped — 2026-08-22 (Session 5: B1a — probe_capital.py erweitert + Operator-Probe startklar)

> **Auftrag:** Nikinger-Frage „was sagt der Plan zu B1a-vs-A4?" → Plan schweigt
> explizit zu dieser Frage (D20 lockt nur A→B; §6 B1 + §9.3 lockt nur B1a→B1b,
> kein Cross-Block-Constraint). Nikinger folgt meiner Empfehlung Option C:
> B1a-Code jetzt, A4 in der Folge-Session, B1b sobald Operator-Output vorliegt.
> B1a-Build: 5-Minuten-Job (`probe_capital.py` um `--markets`-Modus erweitern).

### Completed

**`phase13_live_data/scripts/probe_capital.py`** — zwei neue Flags, +79 Zeilen:

| Flag | Wirkung |
|---|---|
| `--markets` (bool) | B1a-Modus: nach Auth pro Term ein GET `/api/v1/markets?searchTerm=…`, **roh** ausgegeben (keine Filterung, kein Prices-Probe) |
| `--terms` (str) | Suchterme für `--markets` (Default fällt auf `--indices` zurück → backward-compat mit den existierenden Defaults `Germany 40,France 40,Spain 35`) |

Existierender Prices-Probe-Flow **unverändert** — Auth-Pfad ist geteilt (CST +
X-SECURITY-TOKEN einmal holen, dann Verzweigung). Die Pre-Session-Antwort vom
2026-08-22 („`--markets --terms Germany 40,France 40,Spain 35` ⇒ unrecognized
arguments") ist damit behoben: das Argument existiert jetzt.

Output-Format pro Term im `--markets`-Modus:

```json
{
  "term": "Germany 40",
  "http_status": 200,
  "url": "https://demo-api-capital.backend-capital.com/api/v1/markets?searchTerm=Germany+40",
  "content_type": "application/json",
  "raw_text_snippet": "..." (erste 500 Zeichen),
  "raw_body": { ... die tatsächliche API-Antwort ... }
}
```

Dazu `purpose` + `next_step_hint` als Hilfetext für den Operator — erklärt, **was**
in `raw_body` zu suchen ist (Feldnamen für Source-Symbol, das aktuell `DE40`/`FR40`
in `EPIC_MAP` heißt, und alles was zur IG-Epic zurückmappt).

### Operator-Befehl (Demo, kostenlos, am Wochenende möglich)

```bash
phase1_broker_wrapper/.venv/bin/python phase13_live_data/scripts/probe_capital.py \
    --markets --terms "Germany 40,France 40,Spain 35"
```

Output (JSON auf stdout, stderr = narrative) im nächsten Chat pasten. Ich
baue danach `CapitalSource.discover()` (B1b) gegen die beobachtete Form.

### Verified (heute nachgemessen, 2026-08-22)

| Suite | Vor B1a | Nach B1a | Δ |
|---|---:|---:|---:|
| phase13_live_data | 53 | 53 | 0 (B1a ist Script-Erweiterung, keine Test-Änderung) |
| **Summe (Regression)** | **1634** | **1634** | **0** |

Working tree clean (außer dem Hygiene-Findling aus Session 4), `ps aux | grep
scheduler.run` leer, kein Live-DB-Write. Cross-Phase-Edit: ein gezielter Patch
in `phase13_live_data/scripts/probe_capital.py` (Phase 13 ist freigegeben für
Phase-14-Cross-Phase-Edits, Nikinger 2026-08-22). Kein Build, kein
Commit-Push für die anderen Session-5-Edits — das wäre Session-Arbeit.

### Cross-Phase-Anmerkungen für die nächsten Schritte

- **A4 folgt nach dem Operator-Output** (oder parallel, falls du die Probe
  erst am Wochenende machst). A4 braucht **keinen** B1a-Output — die
  yF-Projektion in `set_symbol` ist orthogonal zur Capital.com-Discovery-Form.
- **Falls die Probe einen überraschenden Status liefert** (z.B. 403 oder ein
  Swagger-Drift): Block B fällt auf `origin='operator'` zurück (Plan §6 B1
  „Kein Raten"-Klausel: 2 Paare DE40+FR40 als Seed-Script), Block B2
  (`EPIC_MAP` raus) bleibt machbar. Kein B-Block bricht.
- **B1b + die +4 B1b-Tests** kommen in der Folge-Session nach der Probe.

### Next

- **Operator (Nikinger):** Probe-Run oben ausführen, Output im nächsten Chat
  pasten. Push-Freigabe für 3 Commits (`fd9e7f8` A3-Code, `888ee01`
  Session-4-Docs, `69cfc31` B1a). 3 Commits vor `origin/main`.
- **Ausführende Session (nächste):** Plan §6 **Block A4** — yF-Projektion in
  `UniverseStore.set_symbol`. Sechs Tests gegen die Doppelschreiber-These
  (Plan §6 A4 Test 6). Falls B1a-Output schon da: **danach** B1b
  (`CapitalSource.discover()` gegen beobachtete Form).
- **Unverändert offen:**
  - Operator-Run der B1a-Probe (das hier, am Wochenende möglich).
  - Optional: `.gitignore`-Pattern für `*.sqlite.bak-*` (1 Zeile, s. Session-4).
  - Optional: `ROADMAP.md:427` Korrektur-Eintrag (zweiter Roll-over).

---

## Session stopped — 2026-08-22 (Session 4: Block A3 — Quell-Profile IG/LS/yF)

> **Auftrag:** Nikinger-Anweisung „Arbeite die nächsten Schritte nach Plan ab"
> — Plan-konform weiter mit Block A3 (nach A1 + A2 grün). B1a Capital.com-`/markets`-
> Probe war als Option B angeboten („ich baue den Script-Erweiterung jetzt"), Nikinger
> hat nicht geantwortet → Default Plan-konform: A3 zuerst, B1a kommt später wenn die
> Probe sowieso laufen muss (vor B1b).

### Completed

**`phase14_discovery/source_registry/sources.py`** (NEU) — drei Source-Profile,
keine einzige macht einen Netz-Call:

| Klasse | Eingabe | Status | Origin | Netz |
|---|---|---|---|---|
| `IGDerivedSource` | `Iterable[str]` von IG-Epics | `ok` | `derived` | **nein** — D6 |
| `LSStaticSource` | `Iterable[str]` von IG-Epics | `no_source` (heute; `bars.source='ls'=0`) | `derived` | **nein** — statisch |
| `RegistryYFSource` | `Iterable[str]` + Duck-Store mit `.get(epic)` | 1:1 `data_source_status`-Spiegelung | `registry` | **nein** — D4 |

`max_probe_calls` wird respektiert, **nie** ausgeschöpft — alle drei liefern
`probe_calls_used == 0`, der Daemon bucht nichts in `source_spend` (D13). History/
Latency-Konstanten sind Modul-Level: IG 30d/0min (echtzeit, vollständige Broker-
Historie), yF 7d/15min (Phase-12-Beobachtung), LS 0d/0min (irrelevant solange
`no_source`). `RegistryYFSource` packt store-seitige Fehler ins `errors`-Tupel
(fail-soft per Plan §8.5).

**`phase14_discovery/tests/test_sources.py`** (NEU, 9 Tests = 8 aus Plan + 1
Grep-Komplement zu Test 2):

| Test | Was |
|---|---|
| 1 | `IGDerivedSource` — eine Zeile pro Epic, status='ok', origin='derived', source_symbol=None |
| 2 | **D6-Structural-Cost-Test**: `_ExplodingBroker` (jeder Methoden-Aufruf → AssertionError) als Sentinel, discover() läuft durch, `probe_calls_used == 0` |
| 3 | Grep-Komplement: `import broker_wrapper` / `from broker_wrapper` muss 0 Treffer in `source_registry/` liefern |
| 4 | `RegistryYFSource` mit `_ThrowingStore` (AssertionError auf `.get()`) → SourceProfile mit `errors`, kein Raise |
| 5 | `RegistryYFSource` spiegelt `data_source_status='ok'` 1:1 nach `status='ok'` (D18/A4-Identität) |
| 6 | `RegistryYFSource` spiegelt `no_intraday_source` 1:1, **kein Downgrade** auf `no_source` |
| 7 | `RegistryYFSource` setzt `origin='registry'` auf jeder Zeile |
| 8 | `LSStaticSource` liefert `no_source` für jede Epic |
| 9 | Fail-soft Pattern generisch: `_BrokenStore` (RuntimeError statt AssertionError) → errors-Tupel statt Raise |

Test 2 + Test 3 sind die **D6-Akzeptanz**: strukturelle Zusicherung, dass
`IGDerivedSource` nie `/prices` oder `search_markets` ruft. Test 2 fängt jeden
Aufruf ab, Test 3 pinnt die Modul-Struktur (kein `broker_wrapper`-Import darf
jemals unter `source_registry/` landen).

### Operator-Schritte dieser Session (Nikinger-Ausführung)

- **Push durch** (`6ca9ed4..360683f`): 2 Commits von Session 3, kein Konflikt.
- **Backup der Produktions-DB** angelegt:
  `data/trading_bot.sqlite.bak-20260822-131529` (1 892 352 Bytes, identisch
  zur Live-DB). Vor Produktions-Migration 007 anwendbar — A4 (yF-Projektion)
  muss vorher live sein, sonst liefert die Tabelle nach 007 zwar die historische
  Wahrheit, aber keine Fortschreibung.
- **B1a Capital.com-`/markets`-Probe:** nicht ausgeführt — Block-B-Arbeit, der
  `--markets`-Modus in `probe_capital.py` muss zuerst gebaut werden (Plan §6 B1a).
  Anwendbar sobald B1a-Code steht; bis dahin A3/A4 plan-konform.
- **Hygiene-Findling (außerhalb des Phase-14-Scope, NICHT in dieser Session
  behoben):** `data/trading_bot.sqlite.bak-20260822-131529` zeigt sich als
  untracked, weil `.gitignore:90` `*.sqlite` matcht — `*.sqlite.bak-…` aber
  nicht. Der 2026-07-11-Backup zeigt das gleiche Symptom (auch untracked). Fix
  wäre eine 1-Zeilen-Pattern-Erweiterung (`*.sqlite*` oder explizit
  `*.bak`), bewusst NICHT in dieser Session — Cross-Phase-Edits außerhalb der
  freigegebenen Liste (Phase 2/8/9/12/13) sind erneut freigabepflichtig.

### Verified (heute nachgemessen, 2026-08-22)

| Suite | Vor A3 | Nach A3 | Δ |
|---|---:|---:|---:|
| phase14_discovery | 13 | 22 | 22 (8 aus Plan + 1 Grep-Komplement) |
| **Summe (Regression)** | **1625** | **1634** | **+9** |

Working tree clean (außer dem Hygiene-Findling oben), `ps aux | grep scheduler.run`
leer, kein Live-DB-Write. Cross-Phase-Edits: null (A3 ist vollständig innerhalb
des `phase14_discovery/source_registry/`-Pakets).

### Cross-Phase-Anmerkungen für A4

- **A4 muss rohes SQL über `self.conn` benutzen** (Plan §6 A4) — kein
  `source_registry`-Import in `phase9_universe`. Heute ist die Spaltenliste
  an zwei Stellen: Migration 007 (`phase2_persistence/migrations/007_…sql:13-22`)
  und `SourceAvailabilityStore.upsert`
  (`phase14_discovery/source_registry/store.py`). Beide müssen exakt dieselbe
  Spaltenliste + dieselbe ON-CONFLICT-Klausel verwenden. Der Doppelschreiber-
  Gleichheitstest (Plan §6 A4 Test 6) fängt Drift ab.
- **`source_symbol ≡ yf_ticker WHERE source='yf'`** (B2-Identität): A4 schreibt
  `source_symbol = yf_ticker`, exakt wie Migration-007-Backfill und
  `RegistryYFSource.discover()`. Drei Stellen, dieselbe Spalte.

### Next

- **Operator (Nikinger):** Push-Freigabe für den A3-Commit (`fd9e7f8`).
  Mit Session 4 dann insgesamt 3 Commits in dieser Woche: A2-Code,
  A3-Code, Session-4-Docs.
- **Ausführende Session (nächste):** Plan §6 **Block A4** — yF-Projektion in
  `UniverseStore.set_symbol`. Sechs Tests gegen die heutige Doppelschreiber-
  These: dieselbe Zeile, einmal über `set_symbol`, einmal über
  `SourceAvailabilityStore.upsert` (Plan §6 A4 Test 6).
- **Unverändert offen:** B1a Capital.com-`/markets`-Probe (Plan §9.3).
  Empfehlung: **vor** A4 bauen, weil A4 der letzte Block-A-Step ist und ab dann
  der Discovery-Daemon (Block C) die nächste sinnvolle Arbeit wäre — und der
  Daemon braucht für `capital`-Zeilen die Probe. Sonst gibt es nur IG/LS/yF
  im Daemon-Output, kein Capital.com.
- **Optional (Nikinger-Entscheidung, unabhängig):**
  - `.gitignore`-Pattern für `*.sqlite.bak-*` (1 Zeile, s. Hygiene-Findling).
  - `ROADMAP.md:427` Korrektur-Eintrag (zweiter Roll-over, s. Session-2-Finding).

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

---

## Session stopped — 2026-08-22 (Session 2: Block 0 + A1 — Skeleton + stale_source-Fix)

> **Auftrag:** Nikinger-Auftrag aus der Stand-up-Notiz: Einstieg Block 0.0
> (Sweep gegen die 1608 reproduzieren), dann 0.2 → 0.3 → 0.4, **erst danach
> A1** (der `stale_source`-Fix). Bis A1 grün ist: `enable_divergence_sampler`
> bleibt aus. Vier Commits, atomar je Schritt.

### Completed

**Block 0.0 (Baseline)** — Regression-Sweep reproduziert exakt die 1608 aus
Plan §2.1 (kein Test verschwunden, keine Drift): P1 95 · P2 77 · P3 104 · P4 155
· P5 173 · P6 76 · P7 138 · P8 244 (+1 W) · P9 80 · P10 165 · P12 143 · P13 50 ·
M1 28 · root 80. Working tree clean, `ps aux | grep scheduler.run` leer (kein
Bot-Prozess). **Block 0.0 Akzeptanz erfüllt.**

**Block 0.1 — skip, dokumentiert:** Turbo-/Legacy-Grep-Ritual ist No-Op
(siehe Plan §2.3). Die ausführende Session hat das Ritual **nicht wiederholt**
und verweist stattdessen auf den Session-1-Block.

**Block 0.2 (Doc-Commit `999464a`)** — Nummerierungs-Rollover V4: Phase 14
→ Phase 15, Phase 14 = Discovery-Then-Deterministic. Verbatim-String-Anker:

| Datei | Änderung |
|---|---|
| `ROADMAP.md:625/629/634/638/643` | `### 14a/b/c/d/e` → `### 15a/b/c/d/e` (vormals-Liste erweitert) |
| `README.md:126` | `Phase 14 (V4)` → `Phase 15 (V4)` (mit dritter Umnummerierung 2026-08-22) + Phase-14-Discovery-Eintrag in der dazwischenliegenden-Phasen-Liste |
| `phase10_v3/CLAUDE.md:21` | `down:`-Link-Liste um Phase 14 (Discovery) + Phase 15 (V4) erweitert |
| `ARCHITECTURE.md:60` | alte `V4 moves to Phase 14`-Zeile stehen lassen + datierte Korrekturzeile darunter (Auditkette) |
| `ARCHITECTURE.md:171/230` | `Phase 14e/d (V4)` → `Phase 15e/d (V4)` |
| `ARCHITECTURE.md:261` | Phase 14 (V4) durch zwei Zeilen ersetzt (Phase 14 Discovery mit Plan-Link + Phase 15 V4 deferred) |
| `phase13_live_data/CLAUDE.md` (E6 closeout) | drei Block-C-Modulzeilen `final (Block C geschlossen 2026-08-22)`; Testzahl 39 → 50; „1508 passed" → „1608 passed" mit Summenkorrektur-Fußnote |

**Akzeptanz §6 0.2 erfüllt:** `grep -rn "Phase 14 (V4)" --include=*.md .` liefert
nur noch Treffer in `docs/concepts/phase14_discovery_plan.md` (Plan-Snapshot,
📕, nicht editierbar). 1 Doc-Commit, +35/-22 Zeilen über 5 Dateien.

**Block 0.3 (Fix-Commit `4681d68`)** — drei Phase-13-Script-Bugs (B3/B4/B5)
in einem Commit + drei neuen Tests:

- **B3** `scripts/capital_backfill.py`: eigenes `--universe-db`-Argument mit
  Default `data/trading_bot.sqlite` (Muster `data_foundation/run.py:114-116`).
  `_resolve_epics(args)` → `args.universe_db` (war `args.db`, was per Default
  auf `bars.sqlite` zeigte, wo `instrument_universe` nicht existiert).
- **B4** derselben Datei: `results: dict[str, int] = {}` **vor** dem `try`
  gebunden. Vorher: NameError im except-Handler verschluckte die echte
  Fehlermeldung. Nachher: `partial_results` immer vorhanden, leer im Fehlerfall.
- **B5** `live_data/backfill.py:414-416`: `written += archive.insert_bars(...)`
  statt `written += 1`. Docstring auf „genuinely new rows written" präzisiert
  (`archive.insert_bars` gibt `cur.rowcount` über `INSERT OR IGNORE` zurück;
  Duplikate zählen nicht).

**Bonus-Hygiene-Fix (notwendig, um B5 wirksam zu testen):**
`test_run_capital_backfill_writes_to_archive` nutzte einen hardcoded
`/tmp/test_capital_backfill_e2e/`-Pfad mit Restbars vom 21.08. — der alte
`written += 1` verbarg das (zeigte 2 obwohl 0 neue Rows), B5 macht das sichtbar
(zeigt jetzt ehrlich 0). Umgestellt auf `tmp_path`-Fixture: per-Test frische
DB. Auch der `unmapped`-Test analog. `/tmp/test_capital_backfill_{e2e,unmapped}/`
aufgeräumt.

**Drei neue Tests** (`phase13_live_data/tests/test_capital_backfill_script.py`):
1. `_resolve_epics(--auto)` öffnet Universe-DB-Pfad, nicht Bars-DB-Pfad
   (`monkeypatch` auf `universe.UniverseStore` — Paket-Binding, nicht Submodul).
2. `run_capital_backfill` mit pre-populated Bar (gleicher PK wie die API-Antwort)
   → `results[epic] == 0`, nicht `1` (B5-Beweis).
3. `main()`'s top-level except emittiert JSON mit `partial_results: {}`,
   kein NameError (B4-Beweis).

**Akzeptanz §6 0.3 erfüllt:** `phase13_live_data/tests` 50 + 3 = **53 grün**;
Regression-Sweep 1608 + 3 = **1611**.

**Block 0.4 (Scaffold-Commit `97ffdc2`)** — Phasen-Gerüst, kein funktionaler
Code:

```
phase14_discovery/
├── CLAUDE.md            ← existiert (Plan-Commit), nicht neu angelegt
├── README.md            ← NEU: public surface, Modul-Tabelle als Skeleton
├── pyproject.toml       ← NEU: name='source_registry', editable-install-fähig
├── requirements.txt     ← NEU: nur pytest
├── source_registry/__init__.py   ← NEU, leer
└── tests/__init__.py             ← NEU, leer
```

`scripts/dev_install.sh`: `phase14_discovery` in den editable-install-Loop
aufgenommen, „all twelve packages" → „all thirteen packages", P14 in die
Header-Komposition aufgenommen. `docs/INDEX.md`: README.md-One-Liner im
selben Commit (Doku-Hygiene-Konvention); Active-Phases-Header von „Bau nicht
begonnen" auf „Skeleton + Block 0 in main, funktionaler Bau ab A1"
korrigiert.

**Akzeptanz §6 0.4 erfüllt:** `python -c 'import source_registry'` läuft
(`pip install -e phase14_discovery` erfolgreich); `pytest
phase14_discovery/tests -q`: 0 Tests, kein Fehler; `docs/INDEX.md` kennt jede
neue Datei.

**Block A1 (Fix-Commit `11f5267`)** — Live-Blocker-Fix B1 (`stale_source`
Vokabular-Lücke). Zwei Zeilen in `phase9_universe/universe/models.py`:

```python
DS_STALE_SOURCE = "stale_source"   # Phase 13 §6 A4 (F1)
```

plus `DS_STALE_SOURCE` ins `_VALID_DATA_SOURCE_STATUSES`-Set. Vor dem Fix
warf `UniverseRecord.__post_init__` `ValueError: invalid data_source_status:
'stale_source'` beim LESEN, sobald `set_symbol(..., status='stale_source')`
geschrieben hatte → `active_universe()` stirbt → `wiring.py:131` crashed beim
Daemon-Start. **Zündet genau dann, wenn die Beweiswoche
`enable_divergence_sampler=True` setzt.** Heute unscharf (Default False),
deshalb bisher nicht live gefeuert.

**Test** (`phase9_universe/tests/test_store.py`, +1):
`test_active_universe_survives_stale_source_marker` seedet einen active Epic,
setzt ihn auf stale_source, ruft `active_universe()` (OHNE den Fix: ValueError
via `from_row`). Beweist zusätzlich, dass `measurable_universe()` die stale-
Zeile weiterhin ausschließt (DS_OK-Filter bleibt) — kein Leak in die Messung.

**Falsifikation verifiziert:** vor dem Fix wirft der Test `ImportError`
(`cannot import name DS_STALE_SOURCE`); nach dem Fix grün.

**Akzeptanz §6 A1 erfüllt:** `pytest phase9_universe/tests -q` 80 + 1 = **81
grün**; Gesamt-Baseline 1608 + 4 (A1 + 0.3) = **1612**.

### Verified (heute nachgemessen, 2026-08-22)

| Suite | Vorher | Nachher | Δ |
|---|---:|---:|---:|
| phase13_live_data | 50 | 53 | +3 (B3/B4/B5) |
| phase9_universe | 80 | 81 | +1 (A1) |
| phase14_discovery | n/a | 0 | Skeleton |
| **Summe (Regression)** | **1608** | **1612** | **+4** |

Working tree clean (nach jedem Commit), `ps aux | grep scheduler.run` leer
(Parallel-Login-Falle kontinuierlich). Keine Cross-Phase-Edits außerhalb der
am 2026-08-22 freigegebenen Liste (Phase 2/8/9/12/13). Keine Live-Läufe,
kein Live-DB-Write (alle Tests gegen tmp_path).

### Finding (außerhalb des Locked-Scope §6 0.2, NICHT in dieser Session behoben)

`ROADMAP.md:427` trägt einen dated-2026-08-18 Korrektur-Eintrag („V4 rutscht
auf Phase 14. Jede ‚Phase 13 (V4)'-Nennung in älteren Zeilen meint jetzt
Phase 14"). Durch den zweiten Roll-over (2026-08-22: V4 → 15) ist diese Zeile
jetzt **erneut stale**. Der Plan §6 0.2 pinnt die zu ändernden Stellen
explizit auf die fünf `### 14a…14e`-Sub-Bullets; diese Zeile ist nicht in
der Liste. Empfehlung an Nikinger: ein zweiter datierter
Korrektur-Eintrag darunter (gleiche Auditketten-Logik wie
`ARCHITECTURE.md:60`). Habe es bewusst nicht still erweitert — „Locked
decisions stay locked" (Root-`CLAUDE.md` Working Style).

### Next

- **Operator (Nikinger):** Push-Freigabe für die **vier Commits** (`999464a`,
  `4681d68`, `97ffdc2`, `11f5267`). 4 Commits vor `origin/main`.
- **Ausführende Session (nächste):** Plan §6 **Block A2** — Migration 007 +
  `SourceAvailabilityStore` + `SourceProfile`/`SourceAvailability`-Dataclasses
  + Tests gegen das heutige `instrument_universe`-Substrat (5+3+14 Zeilen aus
  §2.2). **A2 ist die Voraussetzung für alles weitere** — ohne die Tabelle
  gibt es nichts zu projizieren (A4) und nichts umzustellen (B).
- **Operator (Nikinger, vor Block B1b):** Capital.com `/markets`-Probe
  (B1a). Befehl + Output vorbereiten, Demo-Konto (kostenlos). Ohne den
  Output wird `discover()` **nicht** gebaut (Plan §9.3) — Fallback ist
  `origin='operator'` mit den zwei bekannten Paaren, Block B erfüllt trotzdem.
- **Operator (Nikinger, vor Produktions-Migration 007):** Backup von
  `data/trading_bot.sqlite` (additiv, aber reale Trade-Historie).
  Plan §9.13.
- **Optionaler Hygiene-Commit (Nikinger-Diskussion):** `ROADMAP.md:427`
  Korrektur-Eintrag (s. o.).
- **Beweiswoche läuft parallel** (Phase 13, P1–P9). Mit A1 grün kann
  `enable_divergence_sampler=True` jetzt scharf geschaltet werden, ohne
  den Daemon-Start zu sprengen (B1-Lücke geschlossen).

---

## Session stopped — 2026-08-22 (Session 1: Planungssession)

> **Auftrag:** den execution-ready Plan für Phase 14 schreiben. Read-only am
> Produktionscode — **kein** Produktionscode-Edit in dieser Session.

### Completed

**`docs/concepts/phase14_discovery_plan.md`** (NEU) — gelockte Entscheidungen **D1–D20**
mit Begründung je Zeile, Contracts (§5), Schritt-Sequenz **Block 0/A/B/C/D** mit
Verbatim-Ankern und Zeilennummern, Testliste je Schritt, Akzeptanz **A1–A8** (§7),
Fehlgriff-Tabelle (§8, sechs Einträge), vollständige Drift-Liste (§9, 13 Einträge),
Out-of-Scope (§10).

**Dieses Dokument** (`phase14_discovery/CLAUDE.md`, NEU) — Phasenkopf + Session-Block 1.

**Nachtrag im selben Commit-Strang (Advisor-Review):** der Grundbestand der yF-Projektion
kommt aus **Migration 007 selbst** (vier Zeilen `INSERT … SELECT`), nicht aus einem
Resolver-Lauf — `SymbolResolver.resolve_epic` ruft `set_symbol` in sechs von acht Pfaden
**nicht** (`symbols.py:194-199, 207-210, 213-214, 219-220, 222-223, 229-230`), und die drei
`SUN*`-Epics stehen bereits auf ihrem Zielstatus ⇒ sie bekämen sonst nie eine Zeile. Der
Backfill kauft zusätzlich den Identitätsbeweis **vor** der ersten Zeile neuem Code. Ebenfalls
nachgezogen: die Schreib-Mechanik der Projektion ist auf **rohes SQL über `self.conn`**
gelockt (kein `source_registry`-Import in `phase9_universe` — Paket-Zyklus in der falschen
Richtung, plus zweite Verbindung auf dieselbe DB), abgesichert durch einen
Doppelschreiber-Gleichheitstest.

**Nikinger-Entscheidungen dieser Session (2026-08-22):**
- Discovery läuft **autonom als eigener Daemon** (nicht im `universe_refresher`-Slot),
  mit eigenem Operator-Script, und die **UI warnt, bis ein Button scharfschaltet**.
- Code-Ort: **`phase14_discovery/`, Paket `source_registry`** (nicht `discovery` —
  Kollision mit `universe.discovery`).
- **Dukascopy raus aus Phase 14, aber nicht ganz raus** — die Beweiswoche zeigt, was von
  einer Fremdquelle gebraucht wird und ob Dukascopy das richtige Werkzeug ist.
- Der `stale_source`-Fix kommt **in Phase 14, nach den initial steps** — „sonst womöglich
  auf falsches Fundament bauen".
- Cross-Phase-Freigabe erteilt für Phase 2 / 8 / 9 / 12 / 13.

### Verified (selbst gemessen, 2026-08-22)

- **Regression-Baseline VOR dem ersten Fix: 1608 passed**, 14 Suiten, je Phase separat.
  Vollständige Tabelle im Plan §2.1. Working tree clean, `ps aux | grep scheduler.run` leer.
- **Migration 007 ist frei** — `_schema_version` = 6.
- **`instrument_universe`: 22 Zeilen** — 5 `active`+`ok`, 3 `active`+`no_intraday_source`,
  14 `verified`+`unverified`. Namentlich im Plan §2.2 (das ist das Akzeptanz-Substrat für A4).
- **`data/bars.sqlite`: 14 846 Bars** — yf 11 654 · ig 2 230 · capital 962 · **ls 0**.
- **Turbo-/Legacy-Grep-Ritual ausgeführt: No-Op.** 3 Treffer, alle „strike" im
  `fail_count`-Sinn (identisch zu 2026-06-27 / 07-10 / 08-18); `turbo_candidates` = 19,
  eingefrorener P5-Contract-Name, **nicht umbenennen**. Plan §2.3 — die ausführende
  Session wiederholt das Ritual **nicht**.
- **Kein `FOREIGN KEY` in `migrations/001…006`** (6× gezählt), und `UniverseStore` öffnet
  ohne `PRAGMA foreign_keys = ON` → Tabelle 007 bekommt bewusst keinen FK (Plan §5.1).

### Befunde (B1–B6, alle neu — keiner steht in einem Vordokument)

- **B1 🔴 Live-Blocker, empirisch reproduziert:** `DS_STALE_SOURCE = "stale_source"`
  (Phase 13 A4) fehlt in `_VALID_DATA_SOURCE_STATUSES`
  (`phase9_universe/universe/models.py:61-63`). `set_symbol` schreibt es per rohem SQL
  durch; jeder spätere `UniverseRecord.from_row` wirft
  `ValueError: invalid data_source_status: 'stale_source'`. Damit stirbt
  `active_universe()` → `wiring.py:131` beim nächsten Start. **Zündet genau dann, wenn die
  Beweiswoche `enable_divergence_sampler=True` setzt** — was P9 verlangt. Heute unscharf
  (Default `False`). Fix = 2 Zeilen + 1 Test, Plan §6/A1.
- **B2:** die Concept-Schema-Skizze (§2.2) hat **keine** Spalte für das quelleneigene
  Symbol und kann `EPIC_MAP` deshalb nicht ersetzen — ihr eigenes Done-Kriterium wäre
  unerreichbar. **Korrektur (2026-08-22): `source_symbol TEXT`.** Damit ist
  `instrument_universe.yf_ticker` exakt `source_symbol WHERE source='yf'`.
- **B3:** `capital_backfill.py --auto` ist strukturell kaputt — `UniverseStore(args.db)`
  mit `args.db` = `data/bars.sqlite`, wo `instrument_universe` nicht existiert. Seit
  Session 12 nie erfolgreich gelaufen (der Live-Lauf 2026-08-22 nutzte `--epics`).
- **B4:** `capital_backfill.py:187-191` — `NameError` im `except`-Handler (`results` erst
  in Zeile 186 gebunden), verschluckt die eigentliche Fehlermeldung.
- **B5:** `backfill.py:414-416` verwirft den Rückgabewert von `insert_bars` und zählt
  Versuche statt Schreibvorgänge. **Konsequenz für die Beweislage:** „962 bars written"
  (Closeout-Handover §2.4) heißt korrekt „962 Insert-Versuche". Die Zahl stimmt mit der
  Archiv-Zählung überein — aber **nur weil es ein Erstlauf war**; die Übereinstimmung ist
  kein Beweis, dass der Zähler richtig ist.
- **B6:** die „1508 passed" in diesem Repo (`phase13_live_data/CLAUDE.md:169`) ist ein
  **Additionsfehler** — die Einzelzahlen derselben Tabelle ergeben 1608, und mein Sweep
  reproduziert jede Einzelzahl. Keine Drift, keine fehlenden Tests.

### Drift, die ich in Vordokumenten korrigiert habe

- `EPIC_MAP` steht in `backfill.py` **85-88**, nicht in `67-72`
  (`PHASE13_CLOSEOUT_HANDOVER.md` §1.5 und `phase13_c_block_c_replan.md` §1.1 sind stale).
  Der Plan arbeitet deshalb durchgehend mit Verbatim-Strings, nicht mit Handover-Zahlen.

### Next

- **Operator (Nikinger):** Push-Freigabe für den Plan-Commit.
- **Ausführende Session:** Plan §6 **Block 0.0** — Sweep gegen die 1608 aus §2.1
  reproduzieren, dann 0.2 (Nummerierungs-Nachlese, ein Doc-Commit), dann 0.3 (die drei
  Script-Bugs), dann 0.4 (Gerüst). **Erst danach A1** (der `stale_source`-Fix).
- **Vor Block B1b:** die Capital.com-`/markets`-Probe muss gelaufen sein (B1a,
  Operator, Demo, kostenlos). Ohne den Output wird `discover()` **nicht** gebaut, sondern
  auf `origin='operator'` ausgewichen — die Antwort-Form dieser API ist nie inspiziert
  worden (Plan §9.3).
- **Vor der Produktions-Migration 007:** Backup von `data/trading_bot.sqlite` (additiv,
  aber die DB trägt reale Trade-Historie). Plan §9.13.
- **Beweiswoche läuft parallel** (Phase 13, P1–P9) und wird von Phase 14 **nicht**
  blockiert — mit **einer** Ausnahme: wer `enable_divergence_sampler` anschaltet, bevor
  A1 gelaufen ist, zündet B1.

---
## Session stopped — 2026-08-22 (Session 7: CFD-Filter-Fix + Block B1b + Block A4)

> **Auftrag:** Option 1+ kombiniert (Nikinger-Entscheidung) — CFD-Fix, B1b, A4
> in getrennten Commits. Drei Commits, 16 neue Tests grün; keine Cross-Phase-
> Edit außerhalb der freigegebenen Liste (Phase 2/8/9/12/13).

### Completed

**Commit 1 — `phase13: probe -- fix CFD-substring filter to exact INDICES
match`** (`4195033`, 2 files, +154/-12). `scripts/probe_capital.py:382-388`
Filter `"CFD" in instrumentType` war ein No-Op gegen die Realität
(`instrumentType == "INDICES"` — Phase-14 B1a Befund 3). Helper
`_pick_index_match` als modul-level Pure-Funktion extrahiert (gleiche
Disziplin wie `CapitalSource._pick_markets_match` in Session 8) — exakt-
`"INDICES"` Match mit Name-only-Fallback für forward-compat (zukünftige
Type-Renames verlieren den Probe nicht).
+6 Tests in `phase13_live_data/tests/test_probe_capital.py` (NEU): INDICES-
wins, type-case, fallback, no-match → None, missing-type-field, empty-list.

**Commit 2 — `phase14: code+tests -- B1b CapitalSource.discover() against
B1a snapshot`** (`3434fe7`, 2 files, +572/-1). `CapitalSource.discover`
implementiert genau gegen den B1a-Snapshot:
- Signatur `discover(epics, *, max_probe_calls=8) -> SourceProfile` —
  identisch zum Protocol in `source_registry.models:192`.
- Interner statischer Name-Lookup `_DISPLAY_NAME_BY_EPIC` (3 Paare aus B1a
  Befund 5); Spanien 35 ist **drin** (`SP35`) — Dukascopy-Fallback wird
  überflüssig für IBEX.
- Filter exakt `instrumentName == name` UND `instrumentType == "INDICES"`
  (B1a Befund 3); Strict — kein Fallback auf non-INDICES (Discover
  schreibt in die `instrument_source_availability` Tabelle, da ist
  `status='ok'` ein bindender Vertrag).
- Fail-soft (Plan §8.5): network / parse / non-200 → `errors`-Tuple;
  iteriert weiter. Auth-POST zählt nicht gegen `max_probe_calls`.
+8 Tests in `phase13_live_data/tests/test_capital_discover.py` (NEU):
Happy DE40, unknown epic ohne HTTP, search-hit-mit-non-INDICES-Result →
no_source, `max_probe_calls=0` → keine GETs, `max_probe_calls=1` → nur
erste Epic, `requests.ConnectionError` → error, non-200 → error, B1a 3-Paar
round-trip.

**Commit 3 — `phase14: code+tests -- A4 yF-Projektion in
UniverseStore.set_symbol`** (`ee48cd2`, 2 files, +326/-0). `set_symbol`
schreibt nach dem Registry-UPDATE in try/except-Block die yF-Zeile in
`instrument_source_availability` (Migration 007). Schreib-Mechanik gelockt
(Plan §6 A4): rohes SQL gegen `self.conn`, **kein** Cross-Phase-Import von
`source_registry.models` (Phase 9 ist sealed, Phase 14 hängt davon ab —
Importer würde in die falsche Richtung laufen). INSERT … ON CONFLICT …
DO UPDATE — gleiche Shape wie `SourceAvailabilityStore.upsert`.
Doppelschreiber-Gleichheit wird zur Laufzeit zugesichert (Test 6),
nicht zur Compile-Zeit. Fail-soft gemäß D5: fehlt die Tabelle, geht der
Registry-Write durch, der Projektions-Fehler landet im Log.
+6 Tests in `phase9_universe/tests/test_store.py`: round-trip (status='ok'),
overwrite on second call, source_symbol=None, **D5-Beweis mit fehlendem
Migration 007** (Fixture `store` ohne 007; `set_symbol` raises nicht),
measurable_universe byte-equal vor/nach, doppelschreiber-gleichheit mit
beiden `utc_iso_now` auf fixed clock gepatcht.

### Verified

- Regression-Sweep aller 14 Suiten + root `tests/` (Stand nach den drei
  Commits, ohne Docs-Edits):
  | Suite | Vor Session 7 | Nach | Δ |
  |---|---:|---:|---:|
  | phase1_broker_wrapper | 95 | 95 | 0 |
  | phase2_persistence | 77 | 77 | 0 |
  | phase3_external_data | 104 | 104 | 0 |
  | phase4_research | 155 | 155 | 0 |
  | phase5_execution | 173 | 173 | 0 |
  | phase6_debate | 76 | 76 | 0 |
  | phase7_reward | 138 | 138 | 0 |
  | phase8_scheduler | 244 | 244 | 0 |
  | phase9_universe | 81 | 87 | +6 (A4) |
  | phase10_v3 | 165 | 165 | 0 |
  | phase12_data_foundation | 143 | 143 | 0 |
  | phase13_live_data | 59 | 67 | +8 (CFD-Fix: 0; B1b: 8) |
  | phase14_discovery | 22 | 22 | 0 |
  | meta_m1_harness | 28 | 28 | 0 |
  | root `tests/` | 80 | 80 | 0 |
  | **Σ** | **1638** | **1652** | **+14** |
  *(Cross-check: 6 A4 + 8 B1b = 14 neue Tests, keine Lücke.)*
- Working tree clean (außer `data/`-Ordner, der ist gitignored), keine
  Cross-Phase-Edits außerhalb der freigegebenen Phase-13-Liste,
  `git log --oneline -4` zeigt eine saubere Commit-Kette.

### Findings (drei, davon einer war neu)

- **CFD-Filter-Bug-Lage korrigiert:** Plan §6 0.3, Session-6-Doc, der
  Phase-13-Closeout-Handover und die ROOT-CLAUDE-MD zitierten alle
  `live_data/backfill.py:339-366` (oder `:300-316`) als Bug-Stelle. **Falsch.**
  Der `"CFD" in instrumentType`-Substring lebt in `scripts/probe_capital.py:385`.
  `_extract_ohlc` in `backfill.py` filtert nicht nach Typ — sucht nur
  OHLC-Feldnamen. Plan-Drift-Listeneintrag #2 ("Zeilennummern
  verschieben sich") hat sich hier bestätigt; die Korrektur wandert
  in die Plan-§9-Drift-Liste der nächsten Plan-Session.
- **`CapitalSource._pick_markets_match` ist strict-by-design:**
  `scripts/probe_capital._pick_index_match` hat einen Fallback auf
  exakten Namen ohne Typ-Check (für Forward-Kompat im Operator-Tooling).
  `_pick_markets_match` hat **keinen** Fallback — Discover schreibt
  in die Cross-Product-Tabelle, wo `status='ok'` bedeutet "diese
  Quelle liefert CFD-Index-Bars". SHARES/COMMODITIES sind die falsche
  Antwort, kein Notbehelf. Begründung im Helper-Docstring.
- **`import logging` war `phase9_universe/universe/store.py` fremd** bis
  A4 (verifiziert im Plan-Drift-Item #12). `logger = logging.getLogger
  ("universe.store")` ergänzt; nur für den Projektions-Warning-Pfad —
  andere Methoden ändern ihr Verhalten nicht.

### Unverändert offen

- **B2** (`EPIC_MAP` raus, `SourceAvailabilityStore.symbol_for` rein)
  — wartet auf die jetzt baubare B1b-Availability. Empfehlung: nächste
  Session.
- **B3** (`source_delta.py` drei Fälle) — orthogonal, danach.
- **Block C** (Daemon + Web-UI-Scharfschalten) — C1/C2/C3/C4 jeweils
  eigener Commit.
- **Block D** (Closeout) — kommt am Ende der Phase, sobald A1–A8 grün
  sind (A1–A4, B1b, B2, B3, C1–C4).
- **Hygiene-Tickets** aus Session 4: `*.sqlite.bak-*` in `.gitignore`,
  `ROADMAP.md:427` Aktualisierung — bewusst zurückgestellt.
- **Plan-§9-Drift-Listeneintrag #2 erweitern** in der nächsten Plan-
  Session (Editor-Notiz für Phase-15-Planung oder eine Phase-14-
  Closeout-Session).

### NEXT

- **Operator (Nikinger):** Push-Freigabe für die 3 Commits (`4195033`,
  `3434fe7`, `ee48cd2`) + diesen Docs-Commit. Stand jetzt: 3 Commits
  vor `origin/main`.
- **Ausführende Session (nächste):** **B2** (`EPIC_MAP` raus,
  `SourceAvailabilityStore.symbol_for` rein) — jetzt baubar, weil
  B1b die `capital`-Availability liefern kann. Plus B3
  (`source_delta.py` drei Fälle). Block C danach.
- **Beweiswoche läuft separat weiter** (Phase 13 Plan §7 P1–P9). Die
  hier committeten Schreib-Pfade sind alle nicht im Konsumentenpfad
  (D6-Muster), berühren die laufende Beweiswoche nicht.

### Completed

**`phase14_discovery/PHASE14_B1A_PROBE_OUTPUT_2026-08-22.md`** (NEU, L3-Snapshot) —
Roh-Output der Operator-Probe + 8 nummerierte Befunde mit Mapping auf B1b.
Header-Karte nach Doku-Konvention (`status: snapshot`, `read-when`,
`up:`/`down:`). Cross-Verweis vom Plan (`docs/concepts/phase14_discovery_plan.md`).

### Die 8 Befunde — was B1a gelehrt hat

| # | Befund | Konsequenz für B1b |
|---|---|---|
| 1 | Response ist `{ "markets": [...] }` — Array, je Eintrag ein Market-Objekt | `discover()` iteriert über `markets`, filtert, emittiert eine `SourceAvailability` pro Match |
| 2 | **`epic`-Feld ist das gesuchte Source-Symbol** (`"DE40"`, `"FR40"`, `"SP35"`) | geht 1:1 in `instrument_source_availability.source_symbol` — exakt dieselbe Identitäts-These wie yF (B2) |
| 3 | `instrumentType` ist **`"INDICES"`** (nicht `"CFD"`, wie der bestehende `live_data/backfill.py:339-366`-Filter annimmt) | B1b filtert auf `"INDICES"`. **Offener Filter-Bug im bestehenden Code** — der Fallback `[m for m in markets if m.get("instrumentName") == index_name]` rettet es heute. B1b macht es richtig; bestehender Code wird in B2 oder als separates Hygiene-Ticket nachgezogen (Nikinger-Entscheidung) |
| 4 | **Spain 35 IST verfügbar** als `epic: "SP35"` (war bisher Path-C-Territorium in Phase 13) | Block B erweitert Coverage. Dukascopy-Fallback für SP35 wird überflüssig |
| 5 | Sucht mit `searchTerm=<instrumentName>` → erster Eintrag mit `instrumentName == searchTerm` + `instrumentType == "INDICES"` ist die kanonische Übersetzung | B1b-Such-Algorithmus: `for epic in input: name = instrument_universe[epic].name; GET /markets?searchTerm=name; first INDICES match → SourceAvailability` |
| 6 | `delayTime: 0` für alle drei → **Echtzeit** | `history_min_days=30, latency_min=0` für die `capital`-Zeilen (NICHT die 15-Min-yF-Heuristik) |
| 7 | Jeder Eintrag hat `instrumentId` (numerisch), `epic` (kurz), `symbol` (lang/kurz), `bid`/`offer` (Live-Preise), `lotSize`, `tickSize`, `pipPosition` | B1b braucht nur `epic` + `instrumentName` + `instrumentType`. Andere Felder sind für Discover irrelevant — kein Schema-Mapping nötig |
| 8 | `marketStatus: "CLOSED"` für alle drei am Wochenende | erwartbar (Markt zu), **kein** B1b-Sonderfall. Discover prüft Verfügbarkeit via Existenz des Eintrags, nicht via `marketStatus` |

### Operator-Setup (verifiziert, 2026-08-22)

- **Auth funktioniert:** `POST /api/v1/session` → HTTP 200, `account_type=CFD`,
  CST + X-SECURITY-TOKEN im Response-Header. **Demo-Keyring `trading-bot-capital`
  ist intakt** (Vorbedingung für B1b gegeben).
- **Drei Suchterme, drei Treffer** — alle im ersten Listeneintrag.
- **Probe-Script** (`probe_capital.py --markets --terms ...`) tat ohne
  Modifikation. Kein Code-Edit in dieser Session.

### Nicht-B1b-Stoff (separate Tasks)

- **B2 (`EPIC_MAP` raus):** Plan §6 B2 wartet auf B1b. Heute gibt
  `SourceAvailabilityStore.symbol_for(epic, 'capital')` für keinen Epic
  einen Wert (Tabelle 0027 wurde nur mit yF-Backfill gefüllt). Nach B1b
  liefert sie für DE40/FR40/SP35 die richtigen Kürzel.
- **Offener Filter-Bug im bestehenden Code** (`live_data/backfill.py:339-366`,
  `backfill.py:300-316`): `"CFD" in instrumentType` matched nie — die
  Realität ist `"INDICES"`. Der Fallback `candidates = [m for m in markets
  if m.get("instrumentName") == index_name]` rettet es heute. **Nicht in
  dieser Session gefixt** — bewusst zurückgestellt (Phase-14-Cross-Phase-
  Edit nur für Phase 2/8/9/12/13 freigegeben; eine Edit in `backfill.py`
  ist Phase-13-Territorium und gehört in B2 oder als separates Ticket).
  **Empfehlung:** in B2 mit aufnehmen, weil B2 den `EPIC_MAP`-Hintergrund
  eh anfasst.
