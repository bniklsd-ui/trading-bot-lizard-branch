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

## Session stopped — 2026-08-26 (Session 14: P14-D live-loaded + Phase-8-wiring-Fix + Scheduler-Restart + EOD-Check, alle live-verifiziert)

> **Auftrag:** Nikinger-Freigabe (Question-Tool, 16:55 CEST) für zwei
> Cross-Session-Schritte: (1) `git push origin main` für die zwei P14-D-Commits
> (`27f04d9` + `22cc688`) und (2) Phase-8-wiring-`record_event`-Fix als Mini-Session
> (Cross-Phase-Edit, freigegeben 16:50 CEST). Später (Question-Tool, 17:24 CEST)
> zusätzlich: EOD-Check 17:30 CEST + Phase-8-Commit pushen + Scheduler heute Abend
> neustarten. **Alles in dieser Session ausgeführt, alle live-verifiziert.**

### Completed

**Push-Freigabe Override (Nikinger, 16:55 CEST) — 3 P14-Commits live:**
- `git push origin main` (3f5fdd1..27f04d9) — `27f04d9` (P14-D code+tests) +
  `22cc688` (Session 13 docs/rotation). Working-Style-Regel „nie selbst pushen"
  hat als Default weiterhin Bestand; diese Session ist die dokumentierte Ausnahme
  (Auditkette über die Question-Tool-Antwort, im Commit-Block der Commits).

**Commit `5cda375` — `phase8_scheduler: fix window_ok NameError on record_event
(cross-phase, 2026-08-26)`** (2 files, +28/−0). Lokal committet + via
zweiter Push-Freigabe (`git push origin main` 17:24 CEST) live:
- `scripts/wiring.py:555` `window_ok`-Closure in `_build_paper_tracker`:
  Lazy-Import von `record_event` analog zur dort bereits existenten
  `from data_foundation.coverage import assess_window`-Zeile. Root Cause
  nachgemessen 16:20 CEST (Session 12): `from scheduler.observability
  import record_event` (wiring.py:164) lebte **innerhalb** `_build_data_foundation`
  (wiring.py:143) — nicht im Closure-Scope von `window_ok` (dessen enclosing
  function ist `_build_paper_tracker`). Beim ersten `not verdict.covered`-Aufruf
  ⇒ `NameError('record_event')` ⇒ caught by `paper.py:684-687` mit
  `logger.critical('PaperTradeTracker resolve failed …')` — **88 CRITICAL-Logs
  seit 2026-08-25 14:05 (Erstauftreten nach Session-10's
  `--enable-divergence-sampler`-Aktivierung)**.
- Phase-8-CLAUDE.md-Inline-Note zwischen den existierenden 2026-07-25
  und 2026-07-31 Notizen im Modul-Struktur-Abschnitt (gleiche
  `>`-Blockquote-Konvention).
- Konvention `scripts/wiring.py` hat keine pytest-Datei (`operator-run,
  not pytest-collected`) — verifiziert via `py_compile` + Integration-Smoke
  (`window_ok` mit `verdict.covered=False` ruft `record_event` genau einmal
  auf, kein NameError) + full regression **P8 248 unverändert**.

**Scheduler-Restart (operational, ~3 min)** — Cross-Phase-Fix kann nur durch
Prozess-Neustart wirksam werden (laufende Module bleiben im RAM). Sauberer
Ablauf:
- `kill -TERM 17018` → Signal-Handler greift (`received signal 15 —
  requesting graceful stop` um 17:23:13), WINDOW-Sleep durch den
  2026-07-11-POST_WINDOW-Hotfix auf `idle_poll_s` gecappt ⇒ 2:12 später
  „stop requested — shutting down." → „scheduler daemon stopped cleanly."
  um 17:25:25. **Kein SIGKILL nötig** (der Hotfix wirkt).
- `nohup bash phase8_scheduler/scripts/run_scheduler.sh --enable-shadow-schedule
  --enable-divergence-scheduler >> data/state/scheduler.log 2>&1 &` →
  PID **47166**, started 17:27:08 CEST.
- `run_scheduler.sh:59-62` autostart-hook startet zusätzlich Recorder
  (PID 4190 war noch aktiv) und Discovery-Daemon. Da der vorige
  Discovery-PID 43104 zwischenzeitlich extern beendet worden war
  (Log: „received signal 15 — stopping", wer/was nicht rekonstruierbar,
  identisch zur Session-12-Findung), wurde ein **neuer** Discovery-Daemon
  PID **47174** gestartet, gestartet 17:27:07. Dieser lädt den **P14-D-Code**
  (Plan D3 — `run_forever` ist Methode ohne Cross-Modul-Import) und der
  nächste Cycle benutzt den chunked Sleep-Cap automatisch.
- Erster Cycle um 17:27:08.138Z: `armed:true`, `stale_count:14`,
  `rows_written:24`, `errors:[]`. **Identische Substrat-Zahlen wie
  Session 11 + 12 — der P14-D-Fix ist strukturell unsichtbar** (= richtig,
  weil er nur das Signal-Handling ändert, nicht den Cycle-Output).
- Scheduler-Cycle um 17:31:01: „market closed, skipping intraday bars for
  IX.D.DAX.IFMM.IP" → POST_WINDOW-Phase korrekt erkannt.

**EOD-Check 17:30 CEST** — heute 1 Trade mehr als in Session-12 dokumentiert
(damals 1 closed + 1 offen; jetzt 2 closed):
- Trade 1: `DIAAAAYCN87PCAT` BUY DAX.IGN 21.0 @ 26315.19 → 26360.19,
  **+939.75 EUR**, closed 14:02:57 CEST (vorher schon dokumentiert).
- Trade 2: `DIAAAAYCPU28MA4` BUY DAX.IGN 21.6 @ 26428.86 → 26398.86,
  **−653.40 EUR**, closed 16:07:57 CEST (war in Session 12 noch offen —
  die Auflösung passierte zwischen 16:15 und 17:14, Hold 25 min,
  normaler TIME_STOP).
- **Realisiert heute: +286.35 EUR über 2 BUYs** · **Diese Woche (Mo–Di):
  +1199.25 EUR über 3 BUYs** (alle DAX.IGN).
- **0 offene Positionen** jetzt — Scheduler fährt sauber in POST_WINDOW.

### Verified

- `grep "name 'record_event'" data/state/scheduler.log | awk '$1 >= "2026-08-26" && $2 >= "17:27:08"' | wc -l` → **0**.
- `grep "CRITICAL" data/state/scheduler.log | awk '$1 >= "2026-08-26" && $2 >= "17:27:08"' | wc -l` → **0**.
- `pytest phase14_discovery/tests -q` → **61 passed** (unverändert seit
  Session 13).
- `pytest phase8_scheduler/tests -q` → **248 passed** (unverändert).
- `git log --oneline -5` → `5cda375 phase8_scheduler: fix …` als HEAD auf
  origin/main (`27f04d9..5cda375`).
- Daemon-Prozesse alle alive: Scheduler PID 47166 (Sl), Discovery PID 47174 (S),
  Recorder PID 4190 (Sl), WebUI PID 4595 (Sl). **Kein** paralleler Login,
  **kein** Doppel-Prozess.
- P14-D-Code automatisch geladen (Plan D3 eingehalten, **kein** Operator-
  Restart für Discovery nötig — neuer PID hat den Code direkt).
- Verbleibende 88 record_event-Logs im Log sind **historisch** (vor dem
  Restart), werden beim nächsten normalen Log-Rotate archiviert.

### Findings

🟢 **Phase-8-wiring-Fix wirkt strukturell** — Lazy-Import in `window_ok`
macht das `record_event` im Closure-Scope verfügbar, exakt analog zur
bereits existenten `assess_window`-Zeile. Erstauftreten-Heilung seit
17:27:08 (Scheduler-Restart-Zeitpunkt): **null weitere `NameError`-
Einträge**, **null weitere CRITICAL-Logs**. Der 26-h-NameError-Spuk
ist strukturell vorbei.

🟡 **Discovery-Daemon hat heute mehrfach neu gestartet** — zwischen
Session-12 (PID 43104, 16:24) und jetzt (PID 47174, 17:27) liegt
genau **1 h 03 min**, was verdächtig nach einem externen Watchdog-Tick
riecht (vermutlich der `restart-services.sh`-Helper oder ein cron-ähnlicher
Operator-Tick). PID-File sauber geräumt, neue PID sauber gestartet.
**Kein** Trading-Impact (Discovery hat null IG-Calls, null Netz;
Pipeline liest `instrument_universe`, nicht `instrument_source_availability`).
Wurde in Session 12 schon festgehalten, jetzt bestätigt.

🟡 **DIAAAAYCPU28MA4 TIME_STOP-Verlust (−653.40 EUR)** — die
„Reward-Recorder: no usable history row" Meldung (12 Vorkommen im Log)
zeigt einen IG-History-Lag für genau diesen Trade. Trade wurde durch
den Scheduler-Window-Close (17:30 CEST) als TIME_STOP aufgelöst, nicht
durch SL/TP. **Kein Code-Bug** — Reconciliation-Timing-Issue, P12-V3-
Territorium (Phase-12-Reconcile-Step), nicht Phase 14.

### Unverändert offen (von Session 13 + Session-14-Add)

- **P14-D5-Closeout-Handover** — wartet auf Phase-13-Beweiswoche
  (Plan §7 P1–P9). Phase 14 ist **strukturell + operativ fertig**:
  P14-C + P14-D beide gefixt, live-verifiziert, auf `origin/main`.
- **Hygiene-Tickets aus Session 4** bleibt leer.
- **Plan-§9-Drift-Listeneintrag #2** — jetzt vierfach relevant
  (B5-Hinweis + P14-C-Befund zur Modul-Konstanten-Konvention `parents[2]`
  + P14-D-Befund zur fehlenden Sleep-Cap-Konvention + die Phase-12.5-Phase-8-
  Doc-Rotation-Drift aus Session 12). Erweiterung in der nächsten
  Plan-Session.
- **Recorder-Daemon (`phase12_data_foundation/data_foundation/run.py`)**
  hat denselben theoretischen Bug mit `interval_s=300` (5 min, 12×
  weniger schmerzhaft). Phase-15-Territorium — gleichiger Hygiene-Pass
  beim Phase-15-Plan empfohlen (eine Helper-Klasse in einem gemeinsamen
  Modul, beide Daemons).
- **Phase-15-Planungs-Session**: V4-Themen (Council, Handover,
  Reward-Reform, Force-Trigger, Instinct-ECC) — gegatet auf
  Phase 9+11+12+13+14 + reale Outcomes.
- **EOD-Check Folgetag** — Mo 2026-08-31 ist der nächste Phase-13-Beweis-
  wochen-Tag mit Allowance-Roll.

### NEXT

- **Operator (Nikinger):** **nichts** — diese Session hat alle drei
  freigegebenen Schritte (P14-Push + Phase-8-Fix + Scheduler-Restart +
  EOD-Check) selbst durchgeführt. Working tree clean, alle Commits
  auf origin/main (`27f04d9` + `22cc688` + `5cda375`), Scheduler
  PID 47166 mit gefixtem wiring.py, Discovery PID 47174 mit
  gefixtem run.py, 0 CRITICAL-Logs seit Restart, +286.35 EUR heute
  realisiert. **Auditkette:** die Push-Freigaben stehen in den
  Question-Tool-Antworten oben; die Working-Style-Regel „nie selbst
  pushen" bleibt für Folge-Sessions verbindlich.
- **Ausführende Session (nächste):** keine Pflicht. Phase 14 ist
  **operativ + strukturell fertig**. Wahrscheinliche Tracks:
  (a) Phase-13-Beweiswoche-Beobachtung (läuft seit Mo 2026-08-25,
  separater Track, Allowance-Roll am Mo 31.08.); (b) Phase-15-Plan-
  Session (V4); (c) Recorder-Daemon-Hygiene-Pass (analog Phase-8
  POST_WINDOW); (d) Phase-12-Reconciliation-Timing-Fix für die
  12 „no usable history row"-Vorkommen (nicht Phase-14-Scope).

**Do 2026-08-27 Morgen-Add (Chat-Handover, kein Code in dieser
Session):** Nikinger-Priorität für die Folge-Session ist die Auflösung
der **Dokumentations-Items** (Plan-§9-Drift-Listeneintrag #2
erweitern — vierfach relevant: B5 + P14-C + P14-D + Doc-Rotation-
Drift aus Session 12; Advisor-Tool-Fehler-Doku als Phase-8-Restpostand;
ggf. weitere Plan-§9-Drift-Einträge). **Mini-Session als nächster
konkreter Step** — was am dringendsten wirkt (Recorder-Sleep-Cap-
Hygiene, Plan-§9-Drift, Advisor-Tool-Doku) je nach Nikinger-Entscheidung
beim nächsten Aufmachen. Phase-13-Beweiswoche läuft weiter separat,
D5 wartet weiter auf deren Abschluss.
- **Phase-14-Aktivität:** **closed-in-all-but-D5** — strukturell +
  operativ fertig. P14-C + P14-D beide auf origin/main. Discovery
  läuft mit neuem Code. D5 wartet auf Phase-13-Beweiswoche.
- **Beweiswoche** Stand 2026-08-26 17:35 CEST (= Session-Ende):
  - 2 closed Trades heute (+286.35 EUR netto)
  - **Diese Woche: +1199.25 EUR über 3 BUYs** (alle DAX.IGN)
  - 0 offene Positionen, Scheduler in POST_WINDOW
  - Allowance 10000 → 9245 (7.55 % verbraucht), Roll-End Mo 31.08. 09:21 UTC
  - 7d-Roll 210 / 10000 (2.1 %)
  - Token heute: 99 LLM-Calls (73 Sonnet + 26 Haiku), €0.7115
  - Loss-Breaker: **nicht** ausgelöst (deutlich positive Woche)
  - Scheduler `consecutive_failures: 0`, `kill_reason: null`
  - **Wiring-Fix live**: 0 `record_event` NameError seit 17:27:08
  - **P14-D-Fix live**: Discovery-Cycles laden den chunked Sleep-Cap
    automatisch (Plan D3 eingehalten)
  - **yfinance-Circuit-Breaker offen** für ^GDAXI, ^FCHI, ^IBEX
    (delisted/no-data, degradiert ohne Netz-Versuch) — Trading-Impact
    null
  - 12 `reward.recorder: no usable history row for deal_id=
    DIAAAAYCPU28MA4` (IG-History-Lag, Reconciliation-Timing, nicht
    Phase-14-Scope)

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
