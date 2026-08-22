# SESSIONS_ARCHIVE.md — Phase 14 (Discovery-Then-Deterministic)

Newest-first. Rotation rule (root `CLAUDE.md`, mandatory since 2026-07-06): the phase head
carries exactly one `## Session stopped` block; the previously-newest block moves here
verbatim when a new one is appended.

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
