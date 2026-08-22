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

> Stand: **2026-08-22 — Session 7.** Diese Tabelle wird in Block D gegen den
> As-Built-Stand gefüllt (Testzahlen aus dem finalen Sweep, nicht geschätzt).

| Datei | Zweck | Status |
|---|---|---|
| `source_registry/models.py` | `SourceAvailability`, `SourceProfile`, `Source`-Protocol, `origin`-Vokabular | ✅ A2/A3 (gelockt in Phase-13-Session 4) |
| `source_registry/store.py` | `SourceAvailabilityStore` — der einzige Zugriff auf Migration 007 | ✅ A2 |
| `source_registry/sources.py` | `IGDerivedSource`, `LSStaticSource`, `RegistryYFSource` — alle drei ohne Netz | ✅ A3 |
| `source_registry/arm.py` | Scharf-Flag `data/state/DISCOVERY_ARMED` (Muster `killswitch.py`, sichere Richtung umgedreht) | ⬜ C1 |
| `source_registry/run.py` | Der Daemon (Muster `data_foundation/run.py`: PID-File, graceful SIGTERM, `--once`) | ⬜ C2 |
| `scripts/run_discovery.sh` | Start-Wrapper (Muster `run_recorder.sh`) | ⬜ C4 |
| *(cross-phase)* `phase2_persistence/migrations/007_phase14_source_availability.sql` | die Kreuzungs-Tabelle **+ der einmalige yF-Backfill aus `instrument_universe`** (der Grundbestand kommt aus der Migration, nicht aus einem Resolver-Lauf — `resolve_epic` ruft `set_symbol` in sechs von acht Pfaden nicht) | ✅ A2 |
| *(cross-phase)* `phase9_universe/universe/models.py` | `DS_STALE_SOURCE` ins Vokabular (Live-Blocker B1) | ✅ A1 |
| *(cross-phase)* `phase9_universe/universe/store.py` | yF-Projektion in `set_symbol`, nicht-fatal | ✅ A4 (Session 7) |
| *(cross-phase)* `phase13_live_data/live_data/backfill.py` | `CapitalSource.discover()` (B1b); `EPIC_MAP` raus + Symbol-Lookup rein (B2) | 🔶 B1b gebaut, ⬜ B2 |
| *(cross-phase)* `phase13_live_data/scripts/probe_capital.py` | CFD-Filter-Bug Fix: `"CFD"`-Substring → exakt `"INDICES"`; neuer Helper `_pick_index_match` für Testbarkeit | ✅ Cross-Phase-Hygiene (Session 7) |
| *(cross-phase)* `phase13_live_data/scripts/source_delta.py` | drei Fälle statt zwei (`not_available` / `available_but_empty` / `compared`) | ⬜ B3 |
| *(cross-phase)* `phase8_scheduler/webui/api.py` + `static/` | `GET /api/discovery`, ARM/DISARM, Warn-Banner | ⬜ C3 |

---

## Session stopped — 2026-08-22 (Session 8: Block B2 + Block B3)

> **Auftrag:** Nikinger-Entscheidung 2026-08-22, Session-7-Empfehlung
> gefolgt: B2 + B3 in einer Session, schließt Block B ab. Plus
> Smoketest-Erlaubnis (Phase 5 gegen die neue Phase-13-Bibliothek, nicht
> Phase-14-Stoff). Drei Code-Commits, ein Docs-Commit; 7 neue Tests;
> `grep "EPIC_MAP" --include=*.py` ist leer (Akzeptanz A2).

### Completed

**Commit 1 — `phase14: code+tests -- B2 EPIC_MAP raus, symbol_lookup
Callable rein`** (`bb095df`, 3 files, +163/-46). `CapitalSource` nimmt
jetzt einen `symbol_lookup: Callable[[str], str | None]`-Parameter
(Default `None` = kein Lookup = jedes Epic wird abgelehnt, kein HTTP,
fail-closed). `fetch_window` ruft `self._symbol_lookup(epic)` statt
`EPIC_MAP.get(epic)`. `run_capital_backfill` nimmt einen
`symbol_lookup`-kwarg entgegen und überschreibt den Source-eigenen
Lookup (Script ist Owner der DB-Verbindung, Source ist dummer Adapter).
Warnung umformuliert: kein Dukascopy-Verweis mehr (D15). `_make_source`-
Helper im Test nimmt jetzt einen `symbol_lookup`-Parameter (Default:
DAX→DE40, CAC→FR40, sonst nichts). Lock-in-Test
`test_epic_map_does_not_contain_path_c_territory` umbenannt zu
`test_symbol_lookup_default_omits_path_c_territory` (dieselbe These,
neue Quelle der Wahrheit). Zwei neue Tests:
`test_fetch_window_returns_empty_when_no_lookup_was_supplied` (sichere
Default-Richtung) und
`test_run_capital_backfill_symbol_lookup_kwarg_overrides_source`
(Script-Override-Semantik). `scripts/probe_capital.py`: historischer
"was EPIC_MAP aktuell 'DE40' / 'FR40' nennt"-String zeigt jetzt auf
`instrument_source_availability.source_symbol` (gleiche Identitäts-These
wie für yF; D2).

**Commit 2 — `phase14: code+tests -- B2 script builds symbol_lookup
from SourceAvailabilityStore`** (`6e8148e`, 2 files, +145/-9).
`scripts/capital_backfill.py`: neue `_build_symbol_lookup()`-Helper
schließt die DB an `SourceAvailabilityStore` und gibt einen
Closure-Lookup + die Store-Instanz zurück. Fail-soft: ohne Migration
007 liefert der Lookup `None` für jedes Epic → der Backfill wird zu
einem No-Op statt zu werfen. WARNING-Log wenn keine Capital-Zeile in
der Tabelle steht (Operator-Hinweis: Discovery hat noch nie gelaufen).
Zwei neue Tests: Migration-007-missing (null-lookup, kein Crash) +
SourceAvailabilityStore-Aufruf-Pfad (mocked store, prüft
`symbol_for(epic, 'capital', '1m')` als Schlüsselparameter).

**Commit 3 — `phase14: code+tests -- B3 source_delta.py drei Fälle`
(`ac54825`, 2 files, +373/-53)**. Plan §6 B3:
`scripts/source_delta.py` liest die Quellenliste aus
`instrument_source_availability` (statt hartkodiert yf+ls) und
unterscheidet drei Fälle pro Trade:
- `not_available`: kein `status='ok'` für diese Epic (prinzipiell
  nicht abrufbar — Beispiel: SP35 vor dem ersten Discovery-Lauf).
- `available_but_empty`: Quellen registriert, aber keine Bars im
  Fenster (Beschaffungslücke).
- `compared`: ≥ 2 Quellen vergleichbar → `comparison` ist `agree` oder
  `diverge`.
Fail-Soft bei fehlender Migration 007 (`_load_available_sources` fängt
`OperationalError` → leerer Dict → jede Trade ist `not_available`, Exit
0, `divergence_rate=None`). Report-Header trägt jetzt
`trades_not_available` und `trades_available_but_empty` zusätzlich zu
den alten `trades_agree`/`trades_diverge`-Counters. Drei neue Tests
+ drei bestehende umgeschrieben (`row["kind"]`-Werte sind jetzt
`compared`+`comparison` statt direkt `agree`/`diverge`;
`test_missing_source_counted_as_incomparable` →
`test_available_but_empty_when_one_source_has_no_bars`).

**Smoke-Test** (`phase5_execution/scripts/smoke_test.py --broker
ig_demo`) — einmal gelaufen auf Nikinger-Erlaubnis (nicht Phase-14-
Stoff). Ergebnis sauber: `NO_TRADE -- time_window: 19:01 outside trade
window 09:00-17:30 Europe/Berlin` (heute Samstag 19:01, kein Trade-
Fenster; Phase 5 baut den Cycle sauber auf, alle Gates + VETOs laufen,
OrderDecliner blockt, kein Live-Touch). Beweis: die Phase-13-Bibliothek
ist unter dem Phase-5-Bot konsumierbar — kein Import- oder Wiring-Bruch
aus B2/B3.

### Verified

- Regression-Sweep aller 14 Suiten + root `tests/` (Stand nach den drei
  Commits, ohne Docs-Edits):
  | Suite | Vor Session 8 | Nach | Δ |
  |---|---:|---:|---:|
  | phase1_broker_wrapper | 95 | 95 | 0 |
  | phase2_persistence | 77 | 77 | 0 |
  | phase3_external_data | 104 | 104 | 0 |
  | phase4_research | 155 | 155 | 0 |
  | phase5_execution | 173 | 173 | 0 |
  | phase6_debate | 76 | 76 | 0 |
  | phase7_reward | 138 | 138 | 0 |
  | phase8_scheduler | 244 | 244 | 0 |
  | phase9_universe | 87 | 87 | 0 |
  | phase10_v3 | 165 | 165 | 0 |
  | phase12_data_foundation | 143 | 143 | 0 |
  | phase13_live_data | 67 | 74 | **+7 (B2: 4, B3: 3)** |
  | phase14_discovery | 22 | 22 | 0 |
  | meta_m1_harness | 28 | 28 | 0 |
  | root `tests/` | 80 | 80 | 0 |
  | **Σ** | **1652** | **1659** | **+7** |
  *(Cross-check: B2=3+1=4, B3=3 — 7 neue Tests, keine Lücke.)*
- `grep -rn "EPIC_MAP" phase13_live_data/ --include=*.py` → **leer**
  (Exit 1, kein Treffer). Akzeptanzkriterium B2 / A2 grün.
- Working tree clean vor Commit-Kette (außer `data/`-Ordner, gitignored),
  keine Cross-Phase-Edits außerhalb der freigegebenen Phase-13-Liste
  (`backfill.py` ist Phase-13-Territorium per Freigabe 2026-08-22,
  `scripts/probe_capital.py` ist Phase-13-Territorium).
- `git log --oneline -4` zeigt die drei B2/B3-Commits + der folgende
  Docs-Commit: saubere Kette, ein Commit pro Schritt.

### Findings (drei)

- **`EPIC_MAP` lebt weiter in Kommentaren — Akzeptanz sagt nein.** Der
  String tauchte in 8 Code-/Test-Kommentaren + einem JSON-String im
  `probe_capital.py`-Payload auf, alle als historische Erklärungen.
  Akzeptanzkriterium B2 / A2 ist explizit *"`grep … --include=*.py`
  ist leer"* — nicht *"`EPIC_MAP` existiert nicht als Variable"*.
  Habe alle 8 Vorkommen aus den `.py`-Dateien entfernt. Die Geschichte
  lebt jetzt im Plan (`docs/concepts/phase14_discovery_plan.md` §6 B2)
  und in den Session-Blocks (1–7); Code beschreibt den Ist-Stand.
- **`run_capital_backfill` Override-Semantik.** Habe den `symbol_lookup`-
  kwarg als **Override** (nicht "setze nur wenn None") implementiert:
  der Caller (Script) ist Owner der DB-Verbindung, der Source ist
  dummer Adapter. Der `test_run_capital_backfill_symbol_lookup_kwarg_overrides_source`
  pinnt diese Semantik. Alternative wäre gewesen "setze nur wenn source
  noch default" — die hätte einen Sentinel gebraucht und mehr Edge-
  Cases. Override ist die ehrliche Richtung.
- **`source_delta.py` Migration-007-fail-soft.** `_load_available_sources`
  fängt `OperationalError` und gibt `{}` zurück → das Hauptprogramm
  behandelt jede Epic als "kein `status='ok'`" → `not_available` für
  jede Trade. Test `test_fail_soft_when_availability_table_missing`
  pinnt das mit einer zweiten DB (nur 004–006, ohne 007). Exit 0,
  Report-Header voll, divergence_rate = None. Das ist das gleiche
  Pattern wie `_build_symbol_lookup` im Script — Phase-13-Code wird
  nicht zum Pfad, an dem Migration 007 durchgesetzt wird.

### Unverändert offen

- **Block C** (Daemon + Web-UI-Scharfschalten) — C1 (`arm.py`),
  C2 (`run.py`), C3 (Web-UI-Endpoints + Banner), C4 (`run_discovery.sh`).
  Empfehlung: nächste Session.
- **Block D** (Closeout) — kommt am Ende der Phase, sobald A1–A8 grün
  sind (A1 ✅, A2 ✅, A3 ✅, A4 ✅, B1b ✅, B2 ✅, B3 ✅, C1–C4 ⬜).
- **Hygiene-Tickets** aus Session 4: `*.sqlite.bak-*` in `.gitignore`,
  `ROADMAP.md:427` Aktualisierung — bewusst zurückgestellt.
- **Plan-§9-Drift-Listeneintrag #2 erweitern** in der nächsten Plan-
  Session (Editor-Notiz für Phase-15-Planung oder eine Phase-14-
  Closeout-Session). Die jetzige Session bestätigt ihn (alle Anker
  waren korrekt), aber der Eintrag könnte den
  `scripts/probe_capital.py:385`-Befund prominenter machen.

### NEXT

- **Operator (Nikinger):** Push-Freigabe für die 3 Commits
  (`bb095df`, `6e8148e`, `ac54825`) + diesen Docs-Commit. Stand jetzt:
  3 Commits vor `origin/main`.
- **Ausführende Session (nächste):** **Block C** — Daemon
  (`source_registry/run.py`, Muster `data_foundation/run.py`) +
  Web-UI-Scharfschalten (`webui/api.py` + `static/index.html` +
  `static/app.js`). C1 zuerst (kleines Modul, kein Netz, fail-soft
  per D10), C2/C3 danach, C4 zuletzt (run_discovery.sh-Wrapper).
- **Beweiswoche läuft separat weiter** (Phase 13 Plan §7 P1–P9). B2/B3
  berühren die laufende Beweiswoche nicht (kein Konsumentenpfad
  schreibt in `instrument_source_availability` während der Beweiswoche;
  die einzigen Schreiber sind A4-Projektion — wartet auf den ersten
  Resolver-Tick — und C2-Daemon — wartet auf ARM).
