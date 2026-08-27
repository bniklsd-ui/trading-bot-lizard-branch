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

## Session stopped — 2026-08-27 (Session 18: Operator-Folge-Session — Recorder + Discovery-Daemon-Restart + Restart-Loop-Rätsel, 0 Code-Edits, 2 Live-Operator-Aktionen)

> **Auftrag:** Nikinger-Chat (2026-08-27, ~17:50 CEST) auf den Kurz-Stand-Bericht:
> „Recorder + Discovery-Daemon-Restart-Klärung (5 Min, Nikinger-Entscheidung bitte).
> Option A, gerne du wenn du kannst." Mini-Session-Scope: **Restart-Klärung** +
> **Stale-PID-Cleanup** + **Restart-Loop-Diagnose**. **Kein Code-Edit** (Operativ,
> dokumentationsdominierte Diagnose).

### Completed

**1. Stale-PID-Befund:** `data/state/{recorder,discovery}.pid` zeigten auf noch lebende
Prozesse (4190 / 47174). Beide Daemons waren **nie tot** — `kill -0` hatte recht, nur
`ps aux | grep` hatte sie (Filter-/Container-PS-View) nicht gezeigt. **Annahme „Prozess
tot" anhand fehlendem `ps`-Match ist nicht zulässig.**

**2. Restart-Aktion A (Operator, Nikinger-Override):**

- `rm -f data/state/{recorder,discovery}.pid` (PIDs reuse-gefährdet → Double-Start-Guard
  würde sonst fälschlich „already running" sagen).
- `nohup bash phase12_data_foundation/scripts/run_recorder.sh >> data/state/recorder.log 2>&1 &`
- `nohup bash phase14_discovery/scripts/run_discovery.sh >> data/state/discovery.log 2>&1 &`
- **Ergebnis:** NEW recorder (PID 87276) lief, NEW discovery (PID 87271) wurde durch
  externen SIGTERM gekillt (Quelle nicht identifiziert — kein cron/systemd/supervisor,
  keine Watchdog-Datei, kein offener `bash`-Loop gefunden; vermutlich historischer
  Loop aus früherer Session, heute irrelevant).
- **Aufräumen:** OLD recorder (PID 4190, doppelt vorhanden) per `kill -9 4190` entfernt;
  SIGTERM allein reichte nicht (siehe 🟡 Finding unten).
- **OLD discovery (PID 47174)** läuft weiter, schreibt State — P14-D-Fix funktioniert.

**3. Warte-Probe + Fehlddiagnose:** 10 Min gewartet, dann **Recorder als „wieder tot"
fehldiagnostiziert**, weil „received signal 15 — stopping" mehrfach im Log stand. **Falsch:**
Der Signal-Handler ruft `recorder.request_stop()`, aber der Loop ignoriert ihn wegen
des Sleep-Cap-Bugs (siehe 🟡). Der Recorder **schläft weiter**, ignoriert die nächsten
SIGTERMs, und tickt nach Ablauf des Sleeps normal weiter.

**4. Restart-Aktion A' (Reue, sauber):** PID-File weg, neuer Recorder (90518) gestartet,
nach 5 Min verifiziert → **alive, State geschrieben um 19:00:03** (`bars_written:0,
skipped_off_hours:true, errors:[]` — normaler Off-Hours-Stand).

### Verified

- **Live-Prozesse (21:00 CEST):** Scheduler 47166 (1d 3h) + Discovery 47174 (1d 3h) +
  Recorder **90518** (5 Min, frisch, schreibt State).
- **Heartbeat** CRITICAL noch von 17:33 — **vor** dem Recorder-Restart. Nächster
  Health-Check wird sich mit aktivem Recorder erholen.
- **Allowance** 9245/10000 (7,55 %, Roll-End Mo 31.08.) — unverändert.
- **CRITICAL-Logs seit P14-Wiring-Fix:** **0** (alt-bekannte `reward.recorder: no usable
  history row`-CRITICALs laufen weiter, **nicht** Phase-14-Scope).
- **Phase-14-Doku:** keine Code-Edits. Working tree clean. Kein Push nötig (reine
  Operator-Aktion + Diagnose).

### Findings

🟢 **„alive in ps ≠ funktioniert"** UND **„weg aus ps ≠ tot"** — beide Diagnose-Fehler
in dieser Session selbst aufgetreten. Beim nächsten Mal: **State-File-Timestamp + letzte
Log-Zeile + `kill -0` gegen die PID im PID-File** (nicht gegen eine Vermutung) sind
die einzige belastbare Aussage über „lebt der Daemon". Lesson gehört in die nächste
„Werkstatt-Session" als harte Regel.

🟢 **Discovery-Daemon ist robuster als angenommen:** trotz vieler SIGTERMs überlebt er
dank des P14-D-Fix (`run.py:70-83`, `signal_check_interval_s` als Sleep-Cap). PID 47174
seit 1d 3h stabil — gutes Zeichen für Phase 15 (Recorder bekommt denselben Fix).

🟡 **Recorder-Sleep-Cap-Bug bestätigt im Live-Betrieb** (`recorder.py:189`):
```python
self._sleep_fn(self._interval_s)
```
Genau wie P14-D bei Discovery, **ungefixt**. Signal-Handler setzt `_stop_requested = True`,
aber `time.sleep()` schluckt `EINTR` intern und schläft die volle `interval_s` (Default
300 s = 5 Min). Exit erst nach Sleep-Ablauf. **Live-Konsequenz:** SIGTERMs **töten den
Recorder nicht** — sie sind harmlos. Aber `kill -9` wäre für sauberen Restart nötig,
falls der Daemon tatsächlich mal weg soll. Bereits korrekt dokumentiert als Phase-15-
Territorium (Session-17-NEXT-Block). **Verschärfung:** die Fix-Notwendigkeit ist nicht
mehr „theoretisch", sondern **im Live-Betrieb bestätigt** — Phase-15-Helper-Klasse
`interruptible_sleep(interval, stop_requested_fn)` und beide Daemons umstellen.

🟡 **„Restart-Loop-Quelle" nicht identifiziert** — kein cron/systemd/supervisor/watchdog,
keine offene `bash`-Loop-Spur in `ps`. Discovery-Log zeigt wiederholte „starting daemon"-
und „received signal 15"-Einträge; Recorder-Log dasselbe. **Hypothese:** ein
historischer `while true; do bash run_X.sh; sleep N; done` aus einer früheren Session,
der als disowned nohup-Kind im Hintergrund läuft und nicht in `grep` auftaucht.
**Aktueller Effekt: null** — die Daemons laufen (Recorder wegen Sleep-Cap-Bug,
Discovery wegen P14-D-Fix). **Empfehlung für morgen:** nach Login einmal
`pgrep -af "while.*run_"2>/dev/null` o.ä. und verdächtige nohup-Bäume abschießen.

🟡 **`scripts/restart-services.sh`** wurde gefunden (Operator-Helper für, mit eigenem
5-s-Grace + SIGKILL-Fallback). Hätte den Recorder vermutlich mit SIGKILL weggekriegt —
aber bewusst **nicht** benutzt, weil es auch Scheduler und WebUI restarten würde, und
Scheduler sollte nicht gestört werden. Für die **nächste** Restart-Situation lohnt sich
ein Blick darauf (korrekte Reihenfolge, sauberer Cleanup).

###### Unverändert offen (von Session 17)

- **Phase-14 D5 Closeout-Handover** — wartet auf Phase-13-Beweiswoche.
- **Phase-15-Plan-Session** (V4: Council / Handover / Reward-Reform / Force-Trigger /
  Instinct-ECC) — gegatet auf Outcomes aus Phase 9+11+12+13+14.
- **Hook-Installer (tracked)** — Skript gebaut, Operator-seitige Installation fertig,
  die **tracked**-Variante (Option 1/3) bleibt offen.
- **Phase-12-Reconciliation-Timing-Fix** — `reward.recorder: no usable history row`-
  Vorkommen laufen weiter (nicht Phase-14-Scope).
- **Phase-11-Wiederaufnahme** (WI-2/W2) — Datenfundament-Abhängigkeit.

###### NEXT (für die nächste Session / morgen)

**Nikinger-Anweisung zum Session-Ende (2026-08-27, 21:05 CEST):**
> „morgen sollen alle offenen items angegriffen werden, da die beweiswoche aus endet.
> Der Übersicht halber wird Phase 15 evtl items weiter fortführen."

**Konkrete Empfehlung für die morgige Session** (sortiert nach Aufwand × Impact, kann
der Nikinger nach Belieben umstellen):

1. **Phase-13-Beweiswoche-Abschluss** (separater Track, ggf. erste Auswertung):
   - Status der Datenwoche(n) erheben (`phase13_live_data/scripts/source_delta.py`-
     Report der letzten Tage).
   - Wenn PASS ⇒ Phase-14-D5-Closeout-Handover schreiben.
   - Wenn FAIL ⇒ nicht-triviale Befunde dokumentieren + ggf. Phase-14-Code-Fixes.
2. **Recorder-Sleep-Cap-Bug fixen** (Phase-12-Code, ~1-2h): `recorder.py:189` auf
   chunked Sleep umstellen (P14-D-Muster), Regressionstest, Commit. **Empfehlung: jetzt
   machen** — der Fix ist klein, gut getestet (P14-D-Vorbild), und räumt ein
   dokumentiertes Phase-14-Finding ab.
3. **Hook-Installer (tracked, Option 1)** (~1h): `scripts/install_hooks.sh` schreiben,
   der `.git/hooks/pre-commit` aus `scripts/hooks/pre-commit` installiert (tracked im
   ). Niedrige Hürde, hoher Impact für neue Klone.
4. **Phase-12-Reconciliation-Timing-Fix** (~2-3h, Phase-12-Code): die anhaltenden
   `reward.recorder: no usable history row`-CRITICALs angehen. Eigener
   Mini-Session-Track, nicht Phase-14-Scope.
5. **Phase-15-Plan-Session** (großer Block, V4): wenn die Beweiswoche genug Outcomes
   für die V4-Gegenargumente liefert, **jetzt** starten — Council / Handover /
   Reward-Reform / Force-Trigger / Instinct-ECC. Sonst weiter deferred.

**Bot-Stand für die nächste Session:**
- 3 Live-Prozesse (Scheduler 47166, Discovery 47174, Recorder 90518).
- **Wichtig:** der Bot wurde in dieser Session **nicht** gestoppt — Scheduler läuft seit
  1d 3h **ohne** Unterbrechung. Wenn morgen Code-Edits am Scheduler nötig sind: vorher
  Nikinger-Entscheidung, dann `ps aux | grep scheduler.run` als Gegenprobe.
- **Nicht angerührt:** Migration 007 ist **noch nicht** angewendet (`instrument_source_availability`
  existiert nicht in `data/trading_bot.sqlite`). Phase-14 D2-Akzeptanz (z. B. Test 11
  des Plans) ist **nicht** grün — sie wird im Phase-15-H-Setup vermut relevant, sobald
  die Beweiswoche-Entscheidung steht.

**Hinweise für die morgige Session:**

- **Cold-Reader-Hinweis:** Phase 14 ist **closed-in-all-but-D5**. Phase-13-Beweiswoche
  läuft seit Mo 2026-08-25. Hook-Hygiene ist dreifach geschützt (Konvention + Skript +
  Pre-Commit-Hook).
- **Erste Aktion morgens:** `ps -o pid,etime,cmd -p 47166,47174,90518` — sind die drei
  Daemons noch alive? `cat data/state/{recorder,discovery,scheduler}_state.json` —
  schreiben sie noch? Wenn ja: normal starten mit Item 1. Wenn nein: kurze
  Re-Investigation (PIDs reuse, Zombie, etc.) wie in dieser Session.
- **Arbeitsmodell:** Ausführungs-Sessions laufen weiter über `claude-minimax` (Kostengrund,
  Nikinger 2026-08-18). Debugging über `claude`. Kein Live-/Netz-/kostenpflichtiger Lauf
  ohne Nikinger-Freigabe.

- **Σ-Sweep** Stand 2026-08-27 ~21:05 CEST:
  - P14 61, P13 74, P12 143, P9 87, P8 248 — Σ 613 für diese 5 Phasen
    (Σ 1698 wie in den Closeout-Handovern = alle 13 Phasen + meta)
  - Σ Root-Tests **94** (unverändert zu Session 17)
  - Allowance: **9245/10000** (7,55 % verbraucht, Roll-End Mo **31.08.**)
  - Verbleibende CRITICAL-Logs seit P14-Wiring-Fix: **0**
  - Scheduler **PID 47166** (Sl, 1d 3h, `--enable-divergence-sampler)
  - Discovery **PID 47174** (S, 1d 3h, ARMED, schreibt State)
  - Recorder **PID 90518** (Sl, 5 Min, neu gestartet, schreibt State —
    `bars_written:0, skipped_off_hours:true`, normaler Off-Hours-Stand)
  - **`.git/hooks/pre-commit`:** installiert, grün gegen Live-Repo.

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).