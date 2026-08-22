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
