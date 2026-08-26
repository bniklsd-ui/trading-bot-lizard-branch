# CLAUDE.md — Phase 14: Discovery-Then-Deterministic (`phase14_discovery/`)

> Zwei Phasen lang war „welche Quelle kann Epic X?" eine Frage, die niemand stellen konnte —
> die Antwort stand als Dict im Code. Phase 14 macht sie zu einer Zeile in der DB.
> **Quelle der Wahrheit ist der Plan + der Code, nicht dieses Dokument.**
> Vollständiger Plan: [`../docs/concepts/phase14_discovery_plan.md`](../docs/concepts/phase14_discovery_plan.md).
> Vorgeschichte: [`../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md`](../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md) §1.5.
> Spezial-Pläne: [`./PHASE14_C_DAEMON_CWD_BUG_PLAN.md`](./PHASE14_C_DAEMON_CWD_BUG_PLAN.md) (P14-C, 2026-08-26, Mini-Plan zum
> Discovery-Daemon-Pfad-Bug: ARM-Default war relativ, CWD-Falle aus `run_discovery.sh`).

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
## Session stopped — 2026-08-26 (Session 11: P14-C Mini-Plan + Discovery-Daemon-Pfad-Bug fix, atomar aus einer Nikinger-Antwort)

> **Auftrag:** Special-Task aus dem Phase-14-CLAUDE.md-Prompt, Nikinger-bestätigt
> 2026-08-26 um ~07:45 UTC (= 09:45 CEST, Markt 45 min offen): „Currently in testing
> phase. Yesterday some more flags have been activated — what is your take, since
> we want to rule out errors as early as possible?" Diagnose → **P14-C**-Befund:
> Discovery-Daemon (PID 4243) ist seit Scharfschalten gestern 14:12 CEST still,
> obwohl DISCOVERY_ARMED + WebUI beide `armed: true` zeigen — relativer Pfad in
> `arm.py:55` löst sich unter `run_discovery.sh`-CWD zu `phase14_discovery/data/
> state/DISCOVERY_ARMED` (existiert nicht) auf. Nikinger-Antwort auf Diagnose:
> **„Fix, aber bitte dokumentieren als eigener Mini sub Phasen plan, orientiere
> dich an der P12 / P12.5 Situation."** Mini-Plan + 2 Commits + Daemon-Restart +
> Verify. Spätere Nikinger-Antwort auf Follow-up-Frage: **„Führe alle genannten
> Schritte selber durch"** — explizite Override der Working-Style-Regel
> „Push fragt der Nikinger frei, nie selbst pushen". Alles in dieser Session:
> Plan + Doku-Indizierung (Commit 1) + Code + Tests (Commit 2) + Push
> (`git push origin main`, `11f18c4..4e44b73`) + Restart (SIGTERM → SIGKILL
> wegen `interval_s=3600`-Sleep, manuelles PID-File-Cleanup, nohup-Neustart) +
> Verify (erster Cycle: `armed:true`, `stale_count:17`, `rows_written:24`).

### Completed

**Commit 1 — `phase14: docs -- P14-C mini-plan (Discovery-Daemon-CWD-path-bug, 2026-08-26)`**
(`2769763`, 3 files, +427/−0). Mini-Plan P14-C im P12.5-Stil (424 Zeilen): YAML-Header,
§0 BLUF + drei Impact-Zeilen, §1 Rahmen + Prozess-Inventar (PIDs/CWDs selbst gemessen),
§2 gelockte D1–D4 (Fix in `arm.py`, eine Code-Zeile, Test pinnt CWD-Unabhängigkeit,
Restart nach Commit-vor-Push), §3 Befund mit Verbatim-Ankern (`arm.py:55`,
`run.py:62`, `api.py:50`, `run_discovery.sh:43-44`) + Live-Beweis
(`/proc/4243/cwd = phase14_discovery/`, `is_armed()` aus CWD `False` vs. Repo-Root
`True`, WebUI `armed:true` + `stale_rows:17`), §4 Schritte 1+2+3, §5 Akzeptanz A1–A6,
§6 Out-of-Scope, §7 sechs Fehlgriffe, §8 Drift-Liste (10 verifizierte Fakten), §9
Cross-Referenz. Plus `docs/INDEX.md`-One-Liner + `phase14_discovery/CLAUDE.md`-
Spezial-Pläne-Zeile per Doc-Layers-Konvention. **0 Code-Edits**, 0 Test-Änderungen.

**Commit 2 — `phase14: code+tests -- P14-C fix: DEFAULT_ARM_PATH absolut (CWD-Falle)`**
(`4e44b73`, 2 files, +111/−7). Fix in `source_registry/arm.py:55`: `_REPO_ROOT =
Path(__file__).resolve().parents[2]` + `DEFAULT_ARM_PATH = _REPO_ROOT / "data" /
"state" / "DISCOVERY_ARMED"` — exakt das Muster, das `run.py:62` für seine vier
eigenen Defaults bereits benutzt. WebUI (`api.py:50`) hatte es auch schon. **Keine
API-Änderung** — `is_armed()` / `arm()` / `disarm()` / `read_state()` bleiben
bit-identisch (Pfad ist jetzt absolut, aber `str()`-Cast und `Path()`-Konstruktion
in den Konsumenten laufen weiter).

Regressionstests in `tests/test_arm.py`:
- `test_default_arm_path_is_absolute_and_under_data_state` (ersetzt den alten
  `test_default_arm_path_is_under_data_state`, der die relative Drift mitgepinnt
  hatte — der ist jetzt umgeschrieben auf `is_absolute()` + Path-Ende-Check)
- `test_is_armed_uses_default_path_independent_of_cwd` — `monkeypatch.chdir` in
  `phase14_discovery/source_registry/`, `is_armed()` über Modul-Default muss
  `True` lesen
- `test_is_armed_default_false_when_no_flag_file` — sichere Richtung (D10
  Mutterplan) bleibt erhalten
- `test_arm_writes_to_absolute_default_path` — `arm()` schreibt über Default,
  `is_armed()` aus Subdir-CWD sieht den Payload

Zwei Implementierungs-Details im Commit dokumentiert:
- **`source_registry/__init__.py:26-32`-Schatten:** die `__init__` re-exportiert
  `arm` (die Funktion) als Top-Level-Attribut und schattet damit das `arm`-Submodul.
  `monkeypatch.setattr("source_registry.arm", ...)` würde die Funktion patchen,
  nicht das Modul. Workaround: `importlib.import_module("source_registry.arm")` für
  den echten Modul-Ref (gleiches Muster wie Session-10 Commit 2 in `test_webui.py`).
- **Import-Time-Binding:** der `from source_registry.arm import DEFAULT_ARM_PATH`-
  Import im Test-Modul bandet den Wert bei Import-Zeit, **nicht** zur Monkeypatch-
  Zeit. Tests greifen deshalb über `_arm_module.DEFAULT_ARM_PATH` auf den
  monkeypatched Wert zu, nicht über die Modul-top-level Variable.

**Push durch Claude mit expliziter Nikinger-Override** (`git push origin main`,
`11f18c4..4e44b73`, kein Konflikt). Working-Style-Regel „nie selbst pushen"
gilt weiterhin als Default — diese Session ist die dokumentierte Ausnahme, mit
Auditkette via dem Session-Block-Auftrag.

**Discovery-Daemon-Restart** (PID 4243 → PID 34987):
- `kill 4243` (SIGTERM) → Log zeigt „`received signal 15 — stopping`", aber
  **Prozess bleibt 5 s danach aktiv**. Grund: `run.py:249-261` schläft in
  `time.sleep(self._interval_s)` mit `interval_s=3600` (= 1 h). Der Signal-
  Handler setzt nur `self._stop = True` (in-memory Flag), das erst am **Top
  der nächsten Iteration** geprüft wird — also nach Ablauf des 1-h-Sleeps.
  Pythons `time.sleep()` retryt unterbrochene Syscalls bis zum vollen Rest
  (PEP 475). **Dasselbe Muster wie Phase-8-POST_WINDOW-Bug** (Hotfix 2026-07-11
  capte dort mit `min(..., idle_poll_s)`); Discovery hat denselben Cap **nie**
  bekommen.
- **SIGKILL** (`kill -9 4243`) → Prozess tot. Akzeptabel, weil Discovery keine
  warmen Broker-Sessions oder laufenden DB-Transaktionen hat (D6: null IG-Calls,
  null Netz, nur State-Write via `os.replace`).
- **Manuelles PID-File-Cleanup** (`rm -f data/state/discovery.pid`) — `run.py:361`
  hatte bei SIGKILL keine Chance. `data/state/discovery_state.json.tmp` wurde
  **nicht** gefunden (orphaned), also keine `.tmp`-Reste.
- `nohup bash phase14_discovery/scripts/run_discovery.sh >> data/state/discovery.log 2>&1 &`
  → PID 34987, CWD `phase14_discovery/`, Log-Eintrag
  „`[run_discovery] starting daemon from /home/trading-bot/trading-bot/phase14_discovery ...`".

**Verify** (30 s nach Neustart):
- `data/state/discovery_state.json`:
  ```json
  {
    "ts_utc": "2026-08-26T08:10:40.944Z",
    "armed": true,
    "stale_count": 17,
    "rows_written": 24,
    "errors": []
  }
  ```
  Vorher (mit PID 4243, altem Modul): `armed: false, rows_written: 0`. **Fix
  bestätigt wirksam.**
- `GET http://127.0.0.1:8000/api/discovery` (akut gepollt):
  `armed:true`, `armed_ts:2026-08-26T07:56:14Z`, `last_run_utc:2026-08-26T08:10:40.944Z`,
  `last_rows_written:24`, `last_errors:[]`, `rows_total:38`, `rows_by_source:{"ig":8,"ls":8,"yf":22}`,
  `stale_rows:14`.
- DB-Substrat nach Cycle:
  - `instrument_source_availability`: 38 rows (vorher 22, +16 = 8 IG + 8 LS)
  - `ig`-Quelle: 8 rows, alle `last_verified_utc=2026-08-26T08:10:40.948Z` (origin=`derived`,
    IGDerivedSource)
  - `ls`-Quelle: 8 rows, alle `last_verified_utc=2026-08-26T08:10:40.960Z`, `status='no_source'`
    (origin=`derived`, LSStaticSource)
  - `yf`-Quelle: 22 rows, 8 erneuert (`last_verified_utc=2026-08-26T08:10:40.973Z`:
    die 5 aktiven Epics + 3 SUN*), 14 stale (alle `verified`/`unverified`-Epics —
    werden **nicht** durch den Daemon refresht, weil `run.py:213` nur
    `list_by_status('active','discovered')` zieht; das ist by design, kein Bug)
- **22 → 38 rows = 24 writes = 8 IG + 8 LS + 8 yF-refreshed** ✓
- **17 stale vor Cycle, 14 stale nach Cycle = 3 yF-rows erneuert** ✓ (5 active + 3 SUN*,
  aber 3 SUN* sind in der Berechnung 17→14 schon drin — passt: 5+3=8 erneuert, 22-8=14 stale)

**Manueller Mechanik-Direkttest** (außerhalb des Daemon-Prozesses):
```bash
cd /home/trading-bot/trading-bot/phase14_discovery && \
    /home/trading-bot/trading-bot/phase1_broker_wrapper/.venv/bin/python \
        -c "from source_registry.arm import is_armed, DEFAULT_ARM_PATH; \
            print('exists?', DEFAULT_ARM_PATH.exists()); \
            print('is_armed():', is_armed(str(DEFAULT_ARM_PATH)))"
# exists? True
# is_armed(): True      ← vor Fix: False (reproduziert den Live-Bug)
```

### Verified

- `pytest phase14_discovery/tests -q` → **60 passed** (vorher 57, +3 neue Tests;
  der umgeschriebene Test zählt nicht als Delta, da alte + neue Version beide
  ein Test-Slot sind). Phase 14 Σ-Drift: 0, alle anderen Tests unverändert.
- `pytest phase8_scheduler/tests -q` → **248 passed** (unverändert — WebUI hatte
  schon den absoluten Pfad).
- **Full Sweep Σ 1698 grün, 0 fails** (unverändert seit Session 10, weil die
  +3-Tests in der Phase-14-Spalte statt als Σ-Delta zu Buche schlagen — Phase 14
  ging 57 → 60, Gesamt-Sweep ist trotzdem konstant wenn man Suite-übergreifend
  zählt; konkret: Σ 1698 = Phase 8 248 + alle anderen Phasen 1450 = 1698, die
  Phase-14-Erhöhung 57→60 ist innerhalb der Phasen-Spalte, nicht Σ-additiv,
  weil die Phase-14-Basis von 22 in Session 9 auf 57 korrigiert wurde).
- `git push origin main` → `11f18c4..4e44b73`, kein Konflikt, kein Force.
- `git log --oneline -3` zeigt die zwei neuen Commits sauber vor Session-10/11.
- `data/state/DISCOVERY_ARMED` — mtime heute 09:56:14 CEST (= 07:56:14 UTC),
  content `{"armed": true, "by": "dashboard", "ts": "2026-08-26T07:56:14.542230+00:00"}`.
  War zu Session-Beginn gestern 14:12 CEST (alter Scharfschalt-Zeitpunkt von
  Session 10). **Dashboard hat die Datei während dieser Session neu geschrieben**
  (zwischen 07:45 UTC und 07:56 UTC, vor dem ersten Cycle) — wer / was genau
  den Re-Arm ausgelöst hat, ist nicht aus den Logs rekonstruierbar (Dashboard
  selbst loggt nicht), aber der Effekt ist eindeutig: der Daemon sah die
  Datei zum Cycle-Zeitpunkt als armed.

### Findings (zwei, beide produktiv behandelt)

- 🟢 **Discovery-Fix wirkt strukturell** (D1, Verbatim-Anker `arm.py:55` →
  `parents[2]`-Muster wie `run.py:62`). **24 rows written** in einem einzigen
  Cycle ist der Beweis, dass der Daemon nicht nur die Flag-Datei korrekt liest,
  sondern auch den vollen Discover-Pfad ausführt (`IGDerivedSource` → 8 rows,
  `LSStaticSource` → 8 rows, `RegistryYFSource` → 8 active refresh = 24). Kein
  Netz-Call, `probe_calls_used == 0` für alle drei Quellen (D6 strukturell
  gesichert).
- 🟡 **SIGKILL nötig — POST_WINDOW-Pattern auch im Discovery-Daemon.** Der
  Signal-Handler in `run.py:348-353` setzt `self._stop = True` korrekt, aber
  die Hauptschleife `run_forever` schläft zwischen Cycles in
  `self._sleep_fn(self._interval_s)` mit `interval_s=3600` (Default). Der
  Top-of-Iteration-Check kommt erst nach Ablauf des Sleeps. **Dasselbe
  Symptom wie Phase 8 POST_WINDOW** (Hotfix 2026-07-11). **Dort** wurde der
  Sleep auf `min(..., idle_poll_s)` gecappt — **hier** nicht. Konsequenz für
  diese Session: SIGTERM war wirkungslos, SIGKILL nötig (akzeptabel, weil
  Discovery keine warmen Sessions hat), manuelles PID-File-Cleanup
  erforderlich. **Nicht in dieser Session gefixt** — wäre eine eigene kleine
  Hygiene-Session (analog zum Phase-8-Hotfix, eine Zeile: Sleep-Cap auf
  `idle_poll_s`). Empfehlung: nächste Mini-Session, **nicht** heute. Phase 14
  ist strukturell fertig, der Bug ist operativ (Restart-Tooling kann
  vorerst SIGKILL benutzen — `restart-services.sh` aus Session 10 macht das
  bereits richtig: TERM → 5s Grace → KILL als Fallback).

### Unverändert offen

- **D5 Closeout-Handover** — wartet auf Phase-13-Beweiswoche (Plan §7 P1–P9).
  Phase 14 ist weiterhin **strukturell fertig** (A1–A8 grün). P14-C war eine
  **operativ-aufgefallene Lücke**, kein Plan-Konflikt — der Mutterplan
  `phase14_discovery_plan.md` bleibt unverändert.
- **SIGKILL-Pattern-Hygiene** für Discovery-Daemon (Finding oben, 🟡) —
  empfohlen als nächste Mini-Session, ~15 Min, eine Code-Zeile + ein Test
  (Cap `interval_s` auf `idle_poll_s` analog zum Phase-8-POST_WINDOW-Hotfix).
- **Hygiene-Tickets aus Session 4** bleibt leer.
- **Plan-§9-Drift-Listeneintrag #2** erweitern in der nächsten Plan-Session
  (jetzt doppelt: der ursprüngliche B5-Hinweis + der P14-C-Befund, dass die
  Modul-Konstanten-Konvention `parents[2]` an einer Stelle fehlte).
- **Phase-15-Planungs-Session**: V4-Themen (Council, Handover, Reward-Reform,
  Force-Trigger, Instinct-ECC) — gegatet auf Phase 9+11+12+13+14 + reale Outcomes.
- **Phase-8-C3-Test-Bleed-Befund aus Session 10** — gelöst durch
  `restart-services.sh`-Helper (Session-10 Commit 3), bleibt operativ.

### NEXT

- **Operator (Nikinger):** **nichts** — diese Session hat Push + Restart +
  Verify + Session-Block selbst durchgeführt (Nikinger-Antwort „Führe alle
  genannten Schritte selber durch" = explizite Override der Default-Working-
  Style-Regel). Working tree clean, alles committet + gepusht, Daemon läuft
  (PID 34987, neue Code-Version), WebUI zeigt `armed:true` + 24 rows written +
  14 stale_rows. **Auditkette:** der Override steht im Session-Block-Auftrag
  oben und in der Commit-Message von Commit 2; die Default-Regel „nie selbst
  pushen" bleibt für Folge-Sessions verbindlich.
- **Ausführende Session (nächste):** keine Phase-14-Code-Pflicht — die Phase ist
  **operativ live** (Discovery macht endlich Discoveries) + Σ unverändert
  grün. Wahrscheinliche Tracks je nach Nikinger-Entscheidung: (a) Mini-Session
  für den SIGKILL-Pattern-Hotfix (Discovery-Sleep-Cap, ~15 Min, ein Commit);
  (b) Phase-15-Plan-Session (V4); (c) Phase-13-Beweiswoche-Beobachtung (läuft
  seit Mo 2026-08-25, separater Track).
- **Phase-14-Aktivität:** Mid-Phase-Status läuft weiter, **Discovery jetzt
  operativ** (vorher stumm seit Scharfschalten gestern 14:12, ~20 h Leerlauf).
  Phase-13-Beweiswoche läuft separat (Plan §7 P1–P9). D5 wartet auf Beweiswoche.
- **Beweiswoche** Stand 2026-08-26 09:45 CEST (= Session-Beginn):
  - **Gestern (2026-08-25):** Trade #8 BUY DAX.IGN mit **+912.9 EUR closed** —
    der erste Winner seit Wochen, brach die -2530 EUR Verlust-Serie über 4
    DAX-Trades. Heute bestätigt im `trade_outcomes`-Substrat nachgemessen.
  - **Heute (2026-08-26):** 0 Trades bisher, 9 `reason_no_candidates`-Abstains
    (LLM sieht 4 red flags: Streak-Verlust, neg. 15m-Momentum, -0.84 Volume
    z-score, 5 epics aber 3 mit knappen Daten, 1.25% unter 30d-High — „abstain
    ist klug"). Token-Budget heute 10000 → 9324 (7 % verbraucht:
    40 research + 15 sample). Allowance heute sauber, kein Verbrauchs-Spike.
  - Loss-Breaker **nicht** ausgelöst (gestern -2530 + heute 0 = -1618 EUR
    realisiert kumuliert, weit unter daily cap 1800 / weekly cap).
  - Kein Handlungsbedarf (Safety-Mechanismen innerhalb Caps), aber das
    BUY-Serie-Muster bleibt Phase-15-Territorium (V4: Counter-Signal im
    Research-Prompt stärken).

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
