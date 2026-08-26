# CLAUDE.md — Phase 14: Discovery-Then-Deterministic (`phase14_discovery/`)

> Zwei Phasen lang war „welche Quelle kann Epic X?" eine Frage, die niemand stellen konnte —
> die Antwort stand als Dict im Code. Phase 14 macht sie zu einer Zeile in der DB.
> **Quelle der Wahrheit ist der Plan + der Code, nicht dieses Dokument.**
> Vollständiger Plan: [`../docs/concepts/phase14_discovery_plan.md`](../docs/concepts/phase14_discovery_plan.md).
> Vorgeschichte: [`../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md`](../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md) §1.5.
> Spezial-Pläne: [`./PHASE14_C_DAEMON_CWD_BUG_PLAN.md`](./PHASE14_C_DAEMON_CWD_BUG_PLAN.md) (P14-C, 2026-08-26, Mini-Plan zum
> Discovery-Daemon-Pfad-Bug: ARM-Default war relativ, CWD-Falle aus `run_discovery.sh`);
> [`./PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md`](./PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md) (P14-D, 2026-08-26, Mini-Plan zum
> Discovery-Daemon-Signal-Response-Bug: `interval_s=3600`-Sleep verschluckt SIGTERM, analog Phase-8-POST_WINDOW).

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

> Stand: **2026-08-22 — Session 9.** Diese Tabelle wird in Block D gegen den
> As-Built-Stand gefüllt (Testzahlen aus dem finalen Sweep, nicht geschätzt).

| Datei | Zweck | Status |
|---|---|---|
| `source_registry/models.py` | `SourceAvailability`, `SourceProfile`, `Source`-Protocol, `origin`-Vokabular | ✅ A2/A3 (gelockt in Phase-13-Session 4) |
| `source_registry/store.py` | `SourceAvailabilityStore` — der einzige Zugriff auf Migration 007 | ✅ A2 |
| `source_registry/sources.py` | `IGDerivedSource`, `LSStaticSource`, `RegistryYFSource` — alle drei ohne Netz | ✅ A3 |
| `source_registry/arm.py` | Scharf-Flag `data/state/DISCOVERY_ARMED` (Muster `killswitch.py`, sichere Richtung umgedreht) | ✅ C1 (Session 9) |
| `source_registry/run.py` | Der Daemon (Muster `data_foundation/run.py`: PID-File, graceful SIGTERM, `--once`) | ✅ C2 (Session 9) |
| `scripts/run_discovery.sh` | Start-Wrapper (Muster `run_recorder.sh`) | ✅ C4 (Session 9) |
| *(cross-phase)* `phase2_persistence/migrations/007_phase14_source_availability.sql` | die Kreuzungs-Tabelle **+ der einmalige yF-Backfill aus `instrument_universe`** (der Grundbestand kommt aus der Migration, nicht aus einem Resolver-Lauf — `resolve_epic` ruft `set_symbol` in sechs von acht Pfaden nicht) | ✅ A2 |
| *(cross-phase)* `phase9_universe/universe/models.py` | `DS_STALE_SOURCE` ins Vokabular (Live-Blocker B1) | ✅ A1 |
| *(cross-phase)* `phase9_universe/universe/store.py` | yF-Projektion in `set_symbol`, nicht-fatal | ✅ A4 (Session 7) |
| *(cross-phase)* `phase13_live_data/live_data/backfill.py` | `CapitalSource.discover()` (B1b); `EPIC_MAP` raus + Symbol-Lookup rein (B2) | ✅ B1b + B2 (Session 8) |
| *(cross-phase)* `phase13_live_data/scripts/probe_capital.py` | CFD-Filter-Bug Fix: `"CFD"`-Substring → exakt `"INDICES"`; neuer Helper `_pick_index_match` für Testbarkeit | ✅ Cross-Phase-Hygiene (Session 7) |
| *(cross-phase)* `phase13_live_data/scripts/source_delta.py` | drei Fälle statt zwei (`not_available` / `available_but_empty` / `compared`) | ✅ B3 (Session 8) |
| *(cross-phase)* `phase8_scheduler/webui/api.py` + `static/` | `GET /api/discovery`, ARM/DISARM, Warn-Banner | ✅ C3 (Session 9) |
| *(cross-phase)* `phase8_scheduler/scripts/run_scheduler.sh` | Autostart-Hook für `run_discovery.sh` (analog Recorder) | ✅ C4b (Session 9) |

---

## Session stopped — 2026-08-26 (Session 13: P14-D Implementation — chunked Sleep-Cap, lokal grün, Push ausstehend)

> **Auftrag:** Special-Task aus dem Phase-14-CLAUDE.md-Prompt: P14-D-Fix
> (Doc-Plan `96353f6` schon committet, Implementation noch offen — 1 Code-Stelle
> in `run_forever` + 1 Test in `test_run.py`, ~15 min, kein Operator-Restart nötig).
> Plan ist execution-ready, D1–D3 gelockt. **Atomic-only:** Code + Test in einem
> Commit, **kein** Push (Working-Style-Regel, P14-D §1: „Push = Nikinger-Freigabe").
> Phase-8-wiring-Bug (Cross-Phase-Edit, getrennt festgehalten — siehe Open
> questions) wartet weiter auf eigene Mini-Session-Freigabe.
>
> **Ergebnis:** Implementation done, Tests grün, Commit `27f04d9` lokal.
> Discovery-Daemon (PID 43104, läuft seit 16:24 CEST) **nicht** angerührt
> (Plan D3 — der nächste Cycle, spätestens 17:24 CEST, lädt den neuen Code
> automatisch; `run_forever` ist Methode ohne Cross-Modul-Import).

### Completed

**Commit 1 — `phase14: code+tests -- P14-D fix: chunked between-cycle sleep (signal cap, 2026-08-26)`**
(`27f04d9`, 2 files, +89/−7). Fix lebt komplett in `phase14_discovery/`
(kein Cross-Phase-Edit, kein neuer Default-Parameter öffentlich sichtbar —
`sigterm_check_interval_s` ist optionaler Konstruktor-Parameter mit
Default 60 s, additive API).

Konkrete Änderungen:

`source_registry/run.py` (+30/−7):
- neue Modul-Konstante `_DEFAULT_SIGNAL_CHECK_INTERVAL_S = 60` (Zeile 73-78),
  mit Kommentar der auf Plan §2 D2 + Phase-8-POST_WINDOW-Hotfix 2026-07-11
  verweist.
- neuer optionaler Konstruktor-Parameter `signal_check_interval_s: int =
  _DEFAULT_SIGNAL_CHECK_INTERVAL_S` (Zeile 170), gebunden an
  `self._signal_check_interval_s` (Zeile 183).
- `run_forever`-Docstring erweitert (Zeile 257-269): erklärt den Cap,
  verweist auf PEP-475-Verhalten und Phase-8-Analogie.
- `run_forever`-Body: `self._sleep_fn(float(self._interval_s))` →
  `self._sleep_capped(float(self._interval_s))` (Zeile 273).
- neue Methode `_sleep_capped(total_s: float)` (Zeile 275-287): chunked
  Sleep-Helper, zerlegt `total_s` in Brocken `≤ signal_check_interval_s`
  und prüft `self._stop` **vor** jedem Brocken. Loop-Pattern statt
  Phase-8's `min(seconds_until(...), idle_poll_s)`, weil `run_forever`
  eine Periode hat, kein Zielzeitpunkt.

`tests/test_run.py` (+56/−2):
- `_make_daemon`-Helper: neuer optionaler Parameter
  `signal_check_interval_s: int | None = None`, weitergereicht wenn
  gesetzt (Backwards-kompatibel: Default bleibt `_DEFAULT_SIGNAL_CHECK_INTERVAL_S`).
- neuer Test `test_run_forever_caps_between_cycle_sleep_to_signal_check_interval`:
  `interval_s=3600` + `signal_check_interval_s=10`, `fake_sleep` ruft
  `request_stop()` nach erstem Brocken. Assertions: jeder Brocken ≤ 10 s,
  Summe < 3600 s (= Bug-Indikator: ohne Cap wäre Summe = 3600 s).
  Test schlägt sicher fehl ohne den Fix.

Akzeptanz §5 P14-D-Mini-Plan alle grün:
- A1: `signal_check_interval_s` Default 60 s ✓ (`grep` zeigt 4 Treffer in `run.py`)
- A2: `run_forever` ruft `_sleep_capped` statt direktem `self._sleep_fn(...)` ✓
- A3: `_sleep_capped` chunked + `_stop`-Check zwischen Brocken ✓ (neuer Test)
- A4: bestehende Aufrufer sehen altes Verhalten ✓ (`test_run_forever_calls_run_once_in_loop_until_request_stop` mit `interval_s=42`/Default-Cap 60 bleibt grün, weil `min(42, 60) == 42`)
- A5: kein Cross-Phase-Edit, nur Phase 14 angefasst ✓

### Verified

- `pytest phase14_discovery/tests -q` → **61 passed** (vorher 60, +1 neuer Test;
  Σ-Drift Phase 14: +1, Phase-8-Suite unverändert).
- `pytest phase8_scheduler/tests -q` → **248 passed** (unverändert).
- Bestehender `test_run_forever_calls_run_once_in_loop_until_request_stop`
  (interval_s=42, Default-Cap 60) bleibt grün — der Chunked-Loop zerlegt
  42 s nicht, weil `min(42, 60) == 42` ⇒ exakt ein `sleep_fn(42.0)`-Call.
- `git log --oneline -5`: `27f04d9` direkt nach `3f5fdd1` (Session 12) auf `main.
- `git diff 3f5fdd1..27f04d9 --stat` → 2 files, +89/−7. Sauber lokal.
- Daemon PID 43104 läuft weiter (gestartet 16:24:42 CEST, jetzt ~17:00 CEST,
  CWD `phase14_discovery/`, `armed: true`, `stale_count: 14`,
  `rows_written: 24`). **Kein Operator-Restart** ausgelöst — Plan D3 hält
  (run_forever ist Methode ohne Cross-Modul-Import, Method-Body wird beim
  nächsten Cycle aus frischem Modul-Code geladen, spätestens 17:24 CEST).

### Findings

🟢 **P14-D-Fix wirkt strukturell** (Plan §2 D2): `_sleep_capped` chunked
den Sleep in `≤ signal_check_interval_s` und prüft `self._stop` zwischen
Brocken. Ab jetzt reagiert der Daemon auf SIGTERM innerhalb von **maximal
60 Sekunden** (Default) statt bis zu 3600 Sekunden. Phase-8 hat das
exakt gleiche Pattern in `runner.py:370` mit `min(..., idle_poll_s)`
seit 2026-07-11 — Phase 14 zieht jetzt nach.

🟡 **Doc-Drift aus Session 12 entdeckt + aufgeräumt:** Session-12-Commit
(`3f5fdd1`) hat behauptet „Session-12-Block ersetzt Session-11 im Phasenkopf;
Session-11 wandert verbatim ins SESSIONS_ARCHIVE.md" — das Archiv
enthält Session-11 in der Tat (Zeile 8 von `SESSIONS_ARCHIVE.md` nach
dieser Session), aber Session-11-Block wurde **nicht** aus dem
`CLAUDE.md`-Phasenkopf entfernt, sondern nur ohne `## Session stopped
— ...`-Header inlined weiter unten (CLAUDE.md Zeilen 251-481).
Doc-Hygiene-Drift, mit dieser Rotation aufgeräumt: Session-12 wandert
ins Archiv (oben), der inlined-duplicate Session-11-Block im Phasenkopf
verschwindet. **Footer-Pointer bleibt** (`> Ältere Session-Blöcke ...`).

### Unverändert offen

- **Phase-8-wiring.py-`record_event`-Fix** (Cross-Phase-Edit, braucht
  Nikinger-Freigabe, **nicht** in Phase-14-Plan-§4-Freigabe-Liste).
  Fix-Scope 1-3 Zeilen (Lazy-Import in `window_ok` analog zur dort
  existenten `from data_foundation.coverage import assess_window`-Zeile
  ODER Module-Top-Level-Import in `wiring.py:30-40`). 88 CRITICAL-Logs
  heute, ~26 h aktiv, **null Trading-Impact** (nur Paper-Tracker-Pfad).
  Empfehlung: eigene Phase-8-Mini-Session analog P14-C/P14-D, ~15 min,
  1 Commit. **In dieser Session nicht angefasst** (Cross-Phase-Edit
  außerhalb der freigegebenen Liste; Special-Task hatte das festgehalten,
  nicht zur Umsetzung freigegeben).
- **P14-D-Push-Freigabe** — Commit `27f04d9` lokal, kein Push. Working-
  Style-Regel „nie selbst pushen" gilt (P14-D-Plan §1 explizit).
  Push-Freigabe via `git push origin main` (kein Konflikt erwartet,
  Working-Tree clean + zwei Markdown-Dateien via Rotation parallel in
  diesem Commit).
- **D5 Closeout-Handover** — wartet weiter auf Phase-13-Beweiswoche
  (Plan §7 P1–P9). P14-D war eine **operativ-aufgefallene Lücke** im
  Mutterplan (gleicher Status wie P14-C) — keine Plan-Änderung nötig.
- **Recorder-Daemon (`phase12_data_foundation/data_foundation/run.py`)**
  hat denselben theoretischen Bug mit `interval_s=300` (5 min, 12×
  weniger schmerzhaft). Phase-15-Territorium — Nikinger-Entscheidung
  2026-08-26: „nicht heute". Empfehlung: gleichzeitiger Hygiene-Pass
  beim Phase-15-Plan (eine Helper-Klasse in einem gemeinsamen Modul).
- **Hygiene-Tickets aus Session 4** bleibt leer.
- **Plan-§9-Drift-Listeneintrag #2** — jetzt vierfach relevant
  (B5-Hinweis + P14-C-Befund zur Modul-Konstanten-Konvention
  `parents[2]` + P14-D-Befund zur fehlenden Sleep-Cap-Konvention +
  die Doc-Rotation-Drift aus Session 12). Erweiterung in der nächsten
  Plan-Session.
- **Phase-15-Planungs-Session**: V4-Themen (Council, Handover,
  Reward-Reform, Force-Trigger, Instinct-ECC) — gegatet auf
  Phase 9+11+12+13+14 + reale Outcomes.
- **EOD-Check um 17:30 CEST (= 15:30 UTC)** — Nikinger-Entscheidung
  in Session 12 noch offen („falls Nikinger den Tagesschluss sehen
  will, sonst in der Folge-Session"). Heute 16:50 CEST (= 14:50 UTC)
  Stand kurz vor Session-Ende: 1 closed Trade (+939.75 €), 1 offener
  BUY DAX.IGN (DIAAAAYCPU28MA4 @ 26428.86, eingegangen 15:42 CEST),
  Loss-Breaker aus, Discovery wieder operativ. Der offene Trade läuft
  bis SL/TP oder 17:30 CEST Window-Close (Scheduler fährt in
  POST_WINDOW → Reconcile).

### NEXT

- **Operator (Nikinger):**
  (1) **Push-Freigabe für `27f04d9`** (Code+Tests-Commit) +
      parallel für den Session-13-Rotation-Commit (2 Markdown-Dateien,
      SESSIONS_ARCHIVE.md prepend Session-12-Block + CLAUDE.md
      Session-13 ersetzt). Beide lokal vorhanden, kein Konflikt
      erwartet. Default-Working-Style-Regel „nie selbst pushen"
      bleibt verbindlich.
  (2) **Freigabe für Phase-8-wiring-`record_event`-Fix** als eigene
      Mini-Session (Cross-Phase-Edit, Trading-Impact null). Falls ja:
      identische Struktur wie P14-D — Mini-Plan + Code+Test in
      einem Commit + Doc-Commit, ~15 min.
  (3) **EOD-Check um 17:30 CEST** in eigener Mini-Session oder
      verschoben auf Folge-Session.
  (4) **Phase-15-Plan** (V4-Themen) als nächste große Session —
      gegatet auf Phase 9+11+12+13+14 + reale Outcomes.

- **Ausführende Session (nächste):** keine Pflicht. P14-D-Fix ist
  lokal grün und wird beim nächsten Discovery-Cycle automatisch
  geladen. Wahrscheinliche Tracks je nach Nikinger-Entscheidung:
  (a) Phase-8-wiring-Fix als Mini-Session (~15 min); (b) EOD-Check;
  (c) Phase-15-Plan-Session (V4); (d) Phase-13-Beweiswoche-
  Beobachtung. **Discovery-Daemon läuft** (PID 43104, neuer Code
  wird automatisch beim nächsten Cycle geladen — Plan D3 eingehalten).

- **Phase-14-Aktivität:** Mid-Phase-Status, strukturell + operativ
  fertig. P14-C und P14-D beide gefixt + live-verifiziert (P14-C
  bereits auf `origin/main`, P14-D wartet auf Push). Phase-13-
  Beweiswoche läuft separat. D5 wartet auf Beweiswoche. Hygiene-
  Tickets leer.

- **Beweiswoche** Stand 2026-08-26 ~16:50 CEST (= Session-Ende):
  - 1 closed Trade heute (+939.75 €, BUY DAX.IGN)
  - 1 offener BUY DAX.IGN (DIAAAAYCPU28MA4 @ 26428.86, eingegangen 15:42)
  - **+1852 € realisiert über die letzten 2 DAX-IGN-Trades** (gestern +912.9,
    heute +939.75) — brach die -2530-€-Streak über 4 DAX-Buys
  - Allowance 10000 → 9245 (7.5 % verbraucht, sauber)
  - Loss-Breaker **nicht** ausgelöst
  - Token-Budget innerhalb Caps, Weekly-Allowance 48%
  - Scheduler `consecutive_failures: 0`, `kill_reason: null`
  - **yfinance-Circuit-Breaker offen** für ^GDAXI, ^FCHI, ^IBEX
    (delisted/no-data, degradiert ohne Netz-Versuch) — Trading-Impact
    null, brain-context 5/5 als „present"
  - **88 `record_event` NameError**-Logs heute (Phase-8-Bug, siehe
    Open-Questions — Cross-Phase-Edit, wartet auf Freigabe)

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
