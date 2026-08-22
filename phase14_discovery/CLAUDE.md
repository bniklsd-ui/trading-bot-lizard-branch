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
