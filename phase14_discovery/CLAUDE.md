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
