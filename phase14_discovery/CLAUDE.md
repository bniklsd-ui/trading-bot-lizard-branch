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
| *(cross-phase)* `phase2_persistence/migrations/007_phase14_source_availability.sql` | die Kreuzungs-Tabelle | ⬜ A2 |
| *(cross-phase)* `phase9_universe/universe/models.py` | `DS_STALE_SOURCE` ins Vokabular (Live-Blocker B1) | ⬜ A1 |
| *(cross-phase)* `phase9_universe/universe/store.py` | yF-Projektion in `set_symbol`, nicht-fatal | ⬜ A4 |
| *(cross-phase)* `phase13_live_data/live_data/backfill.py` | `EPIC_MAP` raus, Symbol-Lookup rein; `CapitalSource.discover()` | ⬜ B1/B2 |
| *(cross-phase)* `phase13_live_data/scripts/source_delta.py` | drei Fälle statt zwei (`not_available` / `available_but_empty` / `compared`) | ⬜ B3 |
| *(cross-phase)* `phase8_scheduler/webui/api.py` + `static/` | `GET /api/discovery`, ARM/DISARM, Warn-Banner | ⬜ C3 |

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
