---
status: active-phase
purpose: PHASE-HEAD, Phase 16 (Freischaltung) — 🔄 eröffnet 2026-09-05 (Plan-Session, Fable 5.1). Mission = jedes gebaute Feature läuft, jeder bekannte Bruch ist zu, ein vorregistrierter 2-Wochen-Lauf beweist Autonomie ohne Hand. Kern-Befund: der Bot ist seit 2026-08-31 faktisch tot (100 % Research-Abstain, 77/Tag) — Ursache Infrastruktur (Historien-Tabelle ohne Zeitfenster), nicht Strategie; dazu Token-Budget täglich um 15:48 leer, Live-DB auf Schema v7 (Migrations nie angewendet, Doku behauptete das Gegenteil), Flags nicht restart-fest, 3 Wochenend-Epics im Universum.
read-when: jede Phase-16-Session; zuerst den neuesten `## Session stopped`-Block, dann den Plan-Step, der dran ist
detail: L1
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase16_activation_plan.md   # 📕 der Plan (P1–P18, L1–L9, Blöcke A–E, AK1–AK17, §9 Drift, §13 Reviews)
  - ../phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md    # 📕 Vorgänger-Handover (E1–E3 werden hier geschlossen)
  - ../phase7_reward/PHASE12_RECONCILIATION_TIMING_PLAN.md   # 📕 A6 hängt an Migration 008
  - ../phase5_execution/CLAUDE.md                 # B3-Block → Plan D3
  - ./SESSIONS_ARCHIVE.md                         # 📦 Session-Block-Historie (newest-first, A-0 angelegt)
updated: 2026-10-07 (+ **LLM-Subphase Planung eröffnet (MiniMax-M3, Session #36)** [Phase-16-LLM-Subphase: Detail-Plan + Plan-Brief für Opus-Plan-Session NEU (2 Files, 525 LOC zusammen), Cross-Phase-Edits NICHT ausgeführt (Nikinger-Auftrag: in Opus' Hand); Phase-Naming: Phase 16 F / R / LLM als Subphasen unter Phase-16-Schirm (Suffix statt neue Phase-Nummer, analog F-Subphase Session #18–#32 + R-Subphase Session #33–#35); K6-Schwellwert-Entscheidung weiter offen (vertagt auf Opus-Plan-Session); Σ 1963 unverändert, 0 Commits code+test, 1 Doc-Commit dieser Session; Push der 2 Session-#35-Commits bereits erfolgt (`git rev-list --left-right --count origin/main...HEAD` = `0 0`); Session #35-Block (308 Zeilen) verbatim nach `SESSIONS_ARCHIVE.md` rotiert (3805 → 3908 Zeilen, +103); Session #36-Block (84 Zeilen) im Phasenkopf]). — Vorheriger Stand: 2026-09-30 (+ **R-Fix + Doc-Fix ausgeführt (MiniMax M3, Session #35)** [phase3 fetcher `_MAX_RETRIES` 3→5 + `_TRANSIENT_EXC_NAMES` für curl_cffi RequestsError/ConnectionError/Timeout/ChunkedEncodingError, Kommentar Phase-16 R-Fix mit Root-Cause-Datum 2026-09-29 22:55 physischer Server-Umbau; pyc-Cache gelöscht + `systemctl --user restart` aller 4 Units (neue PIDs 223277/223278/223279/223280); v3-Aktiv-Block nachträglich ausgefüllt mit echtem Start-Zeitstempel `2026-09-29T22:57:03+02:00` + Post-hoc-Dokumentation (kein AK13-Verstoß für künftige Re-Eintragungen); v3+v4 Header-Card-Pfade korrigiert (`./phase16_activation/systemd/` → `./systemd/`, `./scripts/install_units.sh` → `../scripts/install_units.sh`); INDEX-Zeilen für v3/v4 ergänzt; Σ 1960→1963 (+3 phase3-Tests); neuer Lauf Tag 1 = 2026-09-29, Tag 10 = 2026-10-13]). — Vorheriger Stand: 2026-09-22 (+ **R5 + R6 ausgeführt (Opus 5, Session #34)** [4 systemd-User-Units + `scripts/install_units.sh` installiert + enabled (nicht gestartet), Keyring aus Unit-Umgebung per `systemd-run --user` bewiesen, 3 Plan-Drifts korrigiert (graphical-session.target, StartLimit* in [Unit], StandardOutput=append:); R6 Token-Aufschlüsselung gemessen (pro Stage unmöglich — kein `stage`-Feld; Research = 94 % des Caps) + 2 Entscheidungen beim Nikinger; F6 gefixt (atomarer `llm_usage.json`-Write) + phase4-Datum-Drift (Fixture); Σ 1958→1960; R7 blockiert auf K6-/K1-Entscheidung + Reboot-Test]). — Vorheriger Stand: 2026-09-22 (+ **R0-R4 ausgeführt (Sonnet 5, Session #33)** [Drift #12/#13/#11/#9 gefixt + F8 (neues K8-Liveness-Gate) + R4-Archivierung (Log 2,37 GB→44 MB gzip, 4 055 221 `ls`-Bars archiviert + aus Live-DB gelöscht, beide DBs integrity-check ok); Σ 1948→1958; R5-R7 offen, siehe Session-Block]). — Vorheriger Stand: Tag-9-Status-Check 2026-09-21 (Opus 5, Session #32, siehe Archiv), Tag-5-Status-Check 2026-09-15 (Drifts #9/#10/#11, deferred), Exec-Session #31 Wrapper-Skript-Fix Drift #8

## Live-Beobachtungen — 2026-09-21 (Tag 9, Status-Check ohne Code-Edits)

> **Kontext:** Nikinger-Auftrag 2026-09-21 ~19:20 Berlin: „mach den geplanten Check" (Block-G-
> Tagesroutine G1/G2/G5 vor dem für Di 2026-09-22 terminierten Block-I-Closeout).
> **Befund: der Lauf steht seit dem Reboot am So 2026-09-20 18:29 — Montag 2026-09-21 ist ein
> vollständig ausgefallener Handelstag.** Dazu zwei neue Struktur-Defekte im LS-Pfad (#12, #13),
> beide seit Phase 13 latent, beide erst durch den J1-Fix (2026-09-08) live geworden.
> Alles unten ist heute selbst gemessen; keine Code-Edits, keine Restarts (Operator-Aktion).

### 🔴 F1 — Kein Dienst läuft; kein Autostart existiert

- `ps aux | grep -E "scheduler|recorder|discovery|webui"` → **0 Treffer**.
- `last -x reboot shutdown`: sauberes `shutdown` So **2026-09-20 12:15**, Boot **18:29**;
  `uptime` = 1 d 52 min. Die VM läuft, der Bot nicht.
- **Kein systemd-Unit, kein Cron-Eintrag** (`systemctl list-units | grep -iE "trading|schedul"` leer,
  `systemctl --user` leer, `crontab -l` = „no crontab"). Die vier Dienste sind manuelle
  `nohup`-Wrapper (`data/state/run_*.log`) → ein Reboot beendet den Lauf **stillschweigend**.
- Letzte echte Aktivität: `research_health.jsonl` 2026-09-18T17:33, letzte `ls`-Bar
  2026-09-18T21:00, `scheduler_state.json` `date=2026-09-20` (So, kein Handel).
- **Konsequenz:** AK-G1 („10 Tagesreports, kein manueller Restart") ist für diesen Lauf
  **nicht mehr erreichbar** — Tag 9 hat null Zyklen. Gültige Handelstage: 09-09 … 09-18 = 8.

### 🔴 Drift #12 — `NameError: record_event` bei **jedem** LS-Bar-Write (`wiring.py:1240`)

- **Code-Stelle:** `phase8_scheduler/scripts/wiring.py:1240`
  `health_sink=lambda ev: record_event(config.observability_path, ev)` — `record_event` ist in
  `wiring.py` **nirgends auf Modul-Ebene importiert**. Jeder andere Aufrufer importiert lokal in
  der Funktion (Z. 230, 653, 756, 791, 906, 1136); die Lambda bei 1240 tut das nicht → beim
  Aufruf `NameError`.
- **Alter:** seit Phase-13-Commit `a58a352` („Step B3 — Scheduler-Lebenszyklus + Token-Rotation")
  latent. Vorher unerreichbar, weil der Write-Pfad am `check_same_thread`-Bug (J-D1) scheiterte;
  seit dem J1-Fix wird die Zeile erreicht.
- **Live-Zählung:** **4 368 060** Tracebacks in `data/state/run_scheduler.log`.
- **Wichtig — J1 bleibt gültig:** `stream.py:497` schreibt **vor** dem Sink
  (`self._archive.insert_bars([bar])`, dann `self._health_sink(...)`). Die Bar landet; verloren
  geht nur das `ls_tickagg_candle_written`-Health-Event. Die Log-Zeile
  „TickAggregatorRecorder: insert_bars failed for …" ist **falsch formuliert** — der generische
  `except Exception` (stream.py:515) fängt den Sink-Fehler und meldet ihn als Insert-Fehler.
- **Fix-Pfad (unblocked):** lokalen Import wie in Z. 906/1136 (`from scheduler.observability import
  record_event as _ls_record_event`) in `_build_recorder` ziehen. P8 ist per Plan §4 Z. 260 für
  Phase 16 freigegeben.

### 🔴 Drift #13 — `_iso_utc_minute` behält die Millisekunde → jeder Tick wird eine „1-Minuten-Bar" (`stream.py:38`)

- **Code-Stelle:** `phase13_live_data/live_data/stream.py:38-44`
  ```python
  truncated = dt.replace(second=0, microsecond=0)
  ms = dt.microsecond // 1000
  return truncated.strftime("%Y-%m-%dT%H:%M:00.") + f"{ms:03d}Z"
  ```
  Die Sekunde wird abgeschnitten, die **Millisekunde des Ticks wieder angehängt**. Ein Tick um
  09:30:17.154 ergibt `minute_start = 2026-09-18T09:30:00.154Z`.
- **Folge:** `TickAggregator.on_tick` (Z. 263) vergleicht `self._current.minute_start_utc !=
  minute_start` — der Vergleich ist bei fast jedem Tick wahr → **Rollover pro Tick**. Die
  Minuten-Aggregation findet nie statt.
- **Live-Beleg (`data/bars.sqlite`, `mode=ro`):** `source='ls'` = **4 055 221 Zeilen**
  (2026-09-08 … 09-18), Datei **973 MB**. Für `IX.D.DAX.IFMM.IP` am 09-18 zwischen 07:00–15:30 UTC:
  **76 901 Zeilen auf 510 distinkte Minuten** (~140 Zeilen/Minute), jede mit `tick_count=1` und
  `open == high == low == close`. Der PK `(epic, resolution, ts_utc, source)` kollidiert wegen der
  ms nie, also dedupliziert auch die DB nicht.
- **Test pinnt den Bug:** `phase13_live_data/tests/test_stream.py:255-257`
  `test_iso_utc_minute_truncates_to_minute` behauptet
  `assert _iso_utc_minute(dt) == "2026-08-19T09:00:00.123Z"` — der Name sagt „truncates", die
  Assertion friert die Millisekunde ein. Alle übrigen Bar-Tests im Repo nutzen `.000Z`.
- **Schadensumfang heute begrenzt:** **kein** Produktions-Konsument liest `source='ls'`.
  `heartbeat.assess_day` (`heartbeat.py:175`), `heartbeat` A6.1 (Z. 338) und `rescue.py:343` lesen
  alle `sources=("yf",)`. → **K4 / `worst_coverage` ist auf yF gemessen und bleibt ehrlich**
  (09-18: `ok:true`, `worst_coverage=0.9958`). Der Defekt ist heute Schreib-Müll + ein unbrauchbares
  Substrat für genau den Zweck, für den Phase 13 es gebaut hat (Live-Schwanz aus derselben
  Preisreihe wie der Einstieg).
- **Fix-Pfad (blockiert):** `stream.py` ist **Phase 13**. P13 steht **nicht** auf der
  Phase-16-Cross-Phase-Liste (P1/2/3/4/5/7/8/9/15 + P12/P14 per Session #31) und der Phase-13-
  Phasenkopf verlangt für jede Touch eine eigene Nikinger-Freigabe. → **Freigabe anfragen**, nicht
  annehmen. Der Fix selbst ist eine Zeile (`.000Z` konstant) + die Korrektur des Tests, der ihn pinnt.

### 🟠 F4 — G5-Schwellwert gerissen; der G5-Befehl selbst meldet falsch

| G5-Prüfung | Soll | Ist |
|---|---|---|
| `du -m data/state/run_scheduler.log` | < 50 MB | **2 262 MB** (2,37 GB, 35 748 963 Zeilen) |
| `grep -c ProgrammingError …` | 0 | **98 820** |
| Disk `/` | — | 65 % belegt, 14 G frei (noch unkritisch) |

- Die 2,37 GB sind **vollständig** Drift #12: eine Traceback-Gruppe je Bar-Write, Größenordnung 4 Mio.
- **Die 98 820 `ProgrammingError` sind alle vor-J1:** Zeilen **4 982 – 795 703**, die letzte
  4 Zeilen **vor** der aktuellen Startzeile 795 707 (`2026-09-08 15:27:43 starting scheduler daemon`).
  Im laufenden Prozess: **0**. AK-J2 ist inhaltlich erfüllt.
- **Befund am Prüfverfahren:** `grep -c` über die nie rotierte Datei mischt den Vor-Fix-Lauf
  (Start 09-08 09:30, Zeile 4 963) in die Tagesmessung → **struktureller Falsch-Alarm**. G5 braucht
  ein Fenster (ab letzter „starting scheduler daemon"-Zeile) oder eine Log-Rotation beim Restart.

### 🟠 F5 — Tagesroutine war seit 09-14 nicht gelaufen (Operator-Lücke) — heute nachgeholt

`data/reports/` enthielt 09-08 … 09-13; G1 ist eine Nikinger-Aktion (Exec-Plan §3 Block G) und
blieb während der Umzugsphase liegen. **Heute nachgeholt: 09-14, 09-15, 09-16, 09-17, 09-18, 09-21**
(`--day`, kein Overwrite — siehe Session-Block Punkt 3). Der 09-13-Report bleibt der von
**Drift #11** überschriebene (Status-Check 09-15) und wurde nicht angefasst.

**Ergebnis der Nachholung (Verdikt je Tag):**

| Tag | K1 | K2 | K3 | K4 | K5 | K6 | K7 |
|---|---|---|---|---|---|---|---|
| 09-14 (Mo, Tag 4) | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ |
| 09-15 (Di, Tag 5) | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ |
| 09-16 (Mi, Tag 6) | ✅ | ✅ | ❌ | ❌ | ✅ | **❌** | ✅ |
| 09-17 (Do, Tag 7) | ✅ | ✅ | ❌ | ❌ | ✅ | **❌** | ✅ |
| 09-18 (Fr, Tag 8) | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ |
| 09-21 (Mo, Tag 9 — Bot aus) | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |

### 🔴 F7 — K6 an zwei Tagen gerissen; der Trigger T-8 wurde nie gezogen

- **09-16:** 301 225 Tokens, `exhausted_at 15:22:04 UTC`, 113 Calls — Cap 300 000 **vor** 17:30 Berlin.
- **09-17:** 302 892 Tokens, `exhausted_at 14:45:36 UTC`, 121 Calls.
- Beides ist ein **PASS-Kriterium** der Vorregistrierung (K6 „< 300 000 Tokens vor Handelsschluss").
  Der Phasenkopf hält seit Session #31 den Trigger fest: „**K6 FAIL → T-8 → Exec-Session on demand**".
  Er wurde nicht gezogen, weil die Tagesroutine (G1) nicht lief — der Befund lag 5 Tage unbemerkt
  in den Rohdaten. **Das ist der Preis der G1-Lücke, nicht ein neuer Code-Defekt.**
- Die C5-Erhöhung 200k → 300k (Plan §1 P3) reicht also an Volltagen **nicht** — 113–121 Calls
  reichen aus, um das Budget vor Handelsschluss zu leeren.

### 🟢 Korrektur zu Drift #10 (K2) — Teil-Entwarnung

Drift #10 (2026-09-15) behauptet „K2 misst falsche Events → K2 immer FAIL". **Widerlegt für
Tages-Queries:** an 09-14 … 09-18 meldet K2 **PASS**. Der FAIL am 09-15 stammt aus einer
Fenster-Query (`--from/--to`), gehört damit in dieselbe Familie wie Drift #9 und #11
(**Partial-Window-Artefakte**), nicht in die Klasse „falsche Event-Namen". Die Drift-#10-Notiz
bleibt im Archiv verbatim stehen; gültig ist diese Korrektur.

### 🔴 F8 — Die Kriterien erkennen einen **toten** Bot nicht

Der Report für 09-21 (null Prozesse, null Zyklen, null Bars) meldet **K1 ✅, K5 ✅, K6 ✅, K7 ✅** —
nur K2 und K4 kippen. K1 prüft „≤ 2 Starts" (0 Starts = PASS), K5 „≤ 5 CRITICAL je OPEN-Trade"
(0 Trades = PASS), K6 „< 300 000 Tokens" (0 Tokens = PASS), K7 liest die Caps aus einer alten
Logzeile. **Ein Tagesreport allein kann „läuft nicht" nicht von „läuft ruhig" unterscheiden.**
Für die Neu-Vorregistrierung ist das der wichtigste Einzelbefund: es fehlt ein Liveness-Kriterium
(z. B. „≥ 1 Scheduler-Zyklus je Handelstag" als **PASS-Bedingung**, nicht nur als K2-Teilsignal).

### 🟡 F6 — `llm_usage.json` wird beim Lesen zerrissen (inferiert, nicht am Writer verifiziert)

`run_webui.log` endet auf 5 verschiedene Parse-Fehler („Expecting ',' delimiter: line 5593 …")
mit der Folge „**counting 0 today**". Die Datei selbst parst im Ruhezustand sauber (4 039 Einträge,
1,0 MB). Muster = Leser trifft einen unvollständigen Schreibvorgang. **Konsequenz für die
Messung:** K6 (Token-Budget) kann still 0 zählen und damit grün melden, ohne etwas gemessen zu
haben. Den Writer habe ich nicht gelesen — als Verdacht geführt, kein Blocker.

### 🟢 Was heute **nicht** kaputt ist

- **G2 Caps-Pin korrekt:** letzte `starting scheduler daemon`-Zeile trägt
  `account=demo, max_trades=5, daily_loss_cap=1800.0, cycle=5min` (K7-Quelle, `autonomy_report.py:437`).
- **J1 hält:** 4,05 Mio `source='ls'`-Zeilen seit 09-08 — der `check_same_thread`-Fix wirkt,
  der Thread-Fehler ist im laufenden Prozess nicht mehr aufgetreten.
- **Substrat yF:** `measurement_heartbeat` 09-18 `ok:true`, `worst_coverage=0.9958`,
  `bars_today=417 150`, `epics_below_threshold=[]`, `pairs_opened=144 / resolved=105`.
- **Kein Kill, keine Fehlerkette:** `consecutive_failures=0`, `kill_reason=null`,
  `trades_today=0`, `realized_pnl_today=0.0`.
- **Disk:** 14 GB frei trotz 2,37 GB Log + 973 MB `bars.sqlite`.

### 📐 Korrektur: Tag-Zählung (dated note, Code-vs-Doku-Regel)

Maßgeblich ist die **Vorregistrierung**, nicht eine Herleitung: `PHASE16_AUTONOMY_PREREGISTRATION_v2.md`
Z. 207 trägt „Tag 1 = Mi **2026-09-09**, Tag 10 = Di **2026-09-22**" (10 Handelstage Mo–Fr, Feiertag-
Check dokumentiert). Daraus: 09-10 (2), 09-11 (3), 09-14 (4), 09-15 (5), 09-16 (6), 09-17 (7),
09-18 (8), 09-21 (**9**), 09-22 (**10**). Der Status-Check-Block vom **2026-09-15 ist im Phasenkopf
als „Tag 7" geführt** — das war eine Kalendertag-Zählung; registriert war es **Tag 5**. Der
Block-I-Termin Di 2026-09-22 ist von der Korrektur **nicht** betroffen. Korrigiert 2026-09-21 gegen
Prereg v2 (locked, nicht editiert); der archivierte 09-15-Block bleibt verbatim.

### Kriterien-Stand Tag 9 (2026-09-21) — gemessen, `data/reports/autonomy_2026-09-21.json`

| K | Report | Ehrliche Lesart |
|---|---|---|
| K1 (Restarts) | ✅ | 0 Starts im Fenster = PASS; der Drift-#8-Fix ist weiterhin **nicht** live verifiziert (braucht einen Restart). Note weiterhin `full-file-count` für die 3 Wrapper (alte Logs pre-Fix). |
| K2 (Auto-Signale) | ❌ | `discovery_heartbeat_event 0 / recorder_bars_per_day 0 / scheduler_health_events 0` — korrekt: es lief nichts. |
| K3 (≥ 5 CLOSED-Trades) | ❌ | 0 Trades im ganzen Lauf. |
| K4 (Heartbeat-Tage) | ❌ | `ok_days 0`; Threshold-String „≥ 8 of 1 trading days" = **Drift #9** unverändert. |
| K5 (keine Hand) | ✅ | misst CRITICALs nach OPEN-Trades; bei 0 Trades strukturell PASS. **Inhaltlich gebrochen**, sobald jemand manuell neu startet (AK-G1). |
| K6 (Token-Budget) | ✅ | 0 Tokens verbraucht (Bot aus). An 09-16/09-17 dagegen **FAIL** (F7). Messung zusätzlich unsicher (F6). |
| K7 (Caps-Pin) | ✅ | Caps-Zeile korrekt (`account=demo, max_trades=5, daily_loss_cap=1800.0, cycle=5min`). |

**Lies das zusammen mit F8:** vier grüne Haken an einem Tag, an dem der Bot nicht lief.

### 🟢 Restart-Pfad geprüft (kein Blocker)

`data/state/recorder.pid` (310266) und `discovery.pid` (310279) stammen vom 2026-09-08 und zeigen
auf tote PIDs. Beide Guards prüfen **Liveness**, nicht Existenz (`run.py:39-46` `os.kill(pid, 0)`;
`restart-services.sh` nutzt `pgrep -f` + `/proc/<pid>/cwd`) → heute verifiziert: `kill -0` schlägt
für beide fehl, ein Restart würde sauber durchstarten. **Restrisiko** nach einem Reboot: PID-Reuse —
wenn ein fremder Prozess dieselbe PID bekommt, verweigert der Daemon den Start mit
„already running". Heute nicht der Fall.

---
## Session stopped — 2026-10-14 (Opus-5.5-Session #37, Status-Check nach ~1 Woche Abwesenheit des Nikingers — read-only Diagnose + 3 Doc-Nachträge, keine Code-/Test-Edits, Σ 1963 unverändert (nicht neu gemessen); Session #36 verbatim nach `SESSIONS_ARCHIVE.md` rotiert)

> **Auftrag:** Nikinger 2026-10-14 ~18:50 Berlin: kurzer BLUF zum Stand, Empfehlung für den nächsten Schritt, Notes aus einem anderen Projekt sichten.

### Completed

- **v3-Lauf (Tag 1 = 2026-09-29, Tag 10 = 2026-10-13) gemessen:** 13 Trades, 12 CLOSED (5 Gewinner, Σ −2 499,15 EUR, `trade_outcomes` `session_date>='2026-09-29'`) + 1 OPEN (id 26, s. u.). Letzte Trades 2026-10-08. Alle 4 systemd-Units laufen; **Autostart live bewiesen** — Reboot 2026-10-12 21:09, Units ohne Hand-Restart hoch (pid-Files 21:09–21:10). Schema v9.
- **AEX-Trade id 26 (`DIAAAAYMDDNBRAQ`, BUY 0.6, offen seit 2026-10-08 15:42) — Root Cause:** Monitor startete 15:43, Scheduler wurde am selben Tag neu gestartet (systemd 16:59, Daemon-Log 22:26, Ursache des Stopps unbekannt — Journal abgeschnitten), danach überwacht **niemand** die Position (`reconcile_startup` lässt `present` stehen, `phase5_execution/execution/order.py:68`). Time-Stop (`max_hold_minutes=240`) nie angewendet; `max_parallel_positions=1` blockierte 09.–14.10. jeden neuen Trade (`abstain_records` `reason_gate_constraints`). IG-Screenshot des Nikingers: Long-Zinsen 12./13./14.10. → Position real offen, +261,60 EUR laufend. **Nikinger hat sie am 2026-10-14 ~19:00 manuell geschlossen.**
- **Bot-Reaktion auf den manuellen Close:** 19:02:24 `reconcile: bot-e6e7… missing at broker — marking closed (orphan)` ✅ (execution_state ohne OPEN/PENDING). 19:12:25 Reward-Recorder: `no usable history row … IG lag — retry later` → `trade_outcomes` id 26 steht **noch OPEN ohne P&L** (bekanntes IG-Demo-Settlement-Lag, s. Phase 7).
- **Fleet-Note (`eurofyx-fleet` S6, 2026-10-11, uncommitted §8 in `PHASE16_LLM_SWITCH_PLAN.md`) gegen Log nachgemessen:** `credit balance is too low` 338× **nur** am 2026-10-09; seit 10-12 Anthropic durchgehend `200`. Dated 🟡-Nachtrag an §8 angehängt.
- **`PHASE16_PARTIAL_CLOSEOUT.md` §7:** +2 Phase-17-Kandidaten (Nikinger: Restart-Plan „für die nächste Phase"): Monitor-Re-Adoption nach Restart; `InstinctValidator.validate()`-Signatur-Bruch live (CRITICAL für trade_id 12–19).
- 🔴 **Backoff-Defekt (2026-10-15 gemessen, nicht behoben):** `_next_retry_in_s` (`phase7_reward/reward/recorder.py:105-120`, Commit `cdf49db`) misst jede Stufe ab **demselben** letzten Versuch und gibt erst bei `elapsed ≥ 24 h` frei → effektives Retry-Intervall **immer 24 h**, nicht die geplante Leiter 15 min → 30 min → 1 h → 4 h → 24 h (`phase7_reward/PHASE12_RECONCILIATION_TIMING_PLAN.md` D1, Idempotenz-Satz „Trades, die IG nach 5 h postet, werden beim ersten Backoff-Slot nach Settlement erkannt"). Beleg: alle 8 broker-geschlossenen Trades des v3-Laufs gebucht nach 24,06–27,22 h (id 15: 70 h über das Wochenende); die 4 TIME_STOP-Trades lag-frei (0 h, Close-Confirm-Pfad). **Folge:** der Daily-Loss-Breaker liest `SUM(profit_loss) … WHERE profit_loss IS NOT NULL` (`phase8_scheduler/scheduler/safety.py:24-36`, `wiring.py:1009`) und ist für Stop-outs am selben Tag **blind** (z. B. 2026-10-08: −790 + −550 erst am 10-09 gebucht, AEX-Einstieg 15:42 sah 0 statt −1 341). Gleiches gilt für den Daily-PNL-Lock (Hard Rule 5). Fix-Ort: Phase 7 (gemeinsame Stelle), cross-phase → Nikinger-Freigabe.
- ✅ **Backoff-Defekt gefixt (2026-10-15, Opus 5.5)** — ausdrückliche Nikinger-Ausnahme von der Analyse/Fix-Trennung („kleiner Fix, mit detaillierter Doku"), Cross-Phase P7 freigegeben. `_next_retry_in_s(last_attempt_iso, open_ts_iso, now_utc)`: Intervall = größte D1-Stufe ≤ Trade-Alter, Boden 15 min. +1 Sequenz-Test (schlägt gegen alten Code fehl: alter Code wartete bei „letzter Versuch vor 61 min" noch 2,98 h, bei „vor 5 h" noch 19 h). P7 170 grün, P8 261 grün. Endpoint `/history/transactions` (`ig_adapter.py:613`) → keine `/prices`-Allowance. Advisor konsultiert ([VERIFY]-Mismatch Plan↔Code). **Nicht** behoben: Breaker bleibt bis zur ersten erfolgreichen Auflösung blind (jetzt ≤ ~1 h im Hold-Fenster statt 24 h; echte IG-Settle-Zeit noch unbekannt, der gemessene 24,06-h-Wert war der Backoff-Boden). Null-Blindheit bräuchte einen Breaker, der ungelöste broker-geschlossene Zeilen mit `−initial_risk` zählt → **Nikinger 2026-10-15: Phase-17-Kandidat** (in `PHASE16_PARTIAL_CLOSEOUT.md` §7 eingetragen). **Scheduler-Restart 2026-10-15 07:42:26** (Nikinger-Go; OPEN/PENDING leer, `recorder`-pyc gelöscht, neue MainPID 670575, Startzeile sauber) → Fix live. id 26 bleibt unberührt (letzter Versuch 14.10. 19:12 CEST in der DB, Alter > 24 h → 24-h-Stufe → nächster Versuch ~15.10. 19:12).
- Weitere Log-Befunde (nicht behoben): 1× transienter Reconcile-`ExecutionAbort` 2026-10-14 16:52 (fail-closed korrekt, kein Dauer-Defekt); 16× `PaperEngine … get_price not ok`; yFinance `^IBEX possibly delisted`-Lärm (Hauptteil der 2 857 ERROR-Zeilen).

### Next
- ✅ **id 26 gebucht 2026-10-15 19:15:22** (`reconcile: resolved 1 open trade(s)`, Lesson extrahiert): `CLOSED`, `close_level` 1136,2, `profit_loss` **+266,40 EUR** (IG-Deal-P&L; Long-Zinsen ~−20,73 EUR laufen separat über die IG-Transaktionen und sind darin nicht enthalten). v3-Lauf final: **13 CLOSED, 6 Gewinner, Σ −2 232,75 EUR**. Kleiner Datenbefund: `close_ts` = Zeitstempel des letzten Fehlversuchs (2026-10-14 17:12:25Z), nicht der echte Close (~17:00Z) — Cold-Reconstruct nimmt `updated_at` als `closed_at` (`recorder.py` `_reconstruct_closed`); `hold_duration_min` entsprechend leicht zu lang. Closeout-Notiz, kein Fix.
- Brückenfenster Tag 1 (Stand 19:17): 0 Trades, 86× `reason_no_candidates`, 0× `reason_gate_constraints` (Q2 bisher ok), 0× `credit balance` (Q3 ok).
- Ab 2026-10-15 sollte wieder gehandelt werden (Slot frei) — erste Zeile in `trade_outcomes` mit `session_date='2026-10-15'` oder `reason_gate_constraints` = 0 ist der Beleg.
- **2-Tage-Brückenfenster läuft** (Nikinger 2026-10-15): Do 10-15 09:00 → Fr 10-16 17:30, vorregistriert in `PHASE16_AUTONOMY_PREREGISTRATION_v4.md` (Commit `90b75b1`, 07:48:36 < Start). Nach Fensterende: `autonomy_report.py --from 2026-10-15 --to 2026-10-16 --summary` (Operator) + Q1–Q4 auswerten → Eingang für v3-Closeout + Plan am Wochenende 17./18.10. `eurofyx-fleet` liest im selben Zeitraum (FYI, rein lesend = kein Operator-Ereignis).
- **Brückenfenster Tag 2 — erster Live-Test Q1 (2026-10-16):** id 27 `DIAAAAYN53SMVAS` DAX BUY 16.7 @ 25 556,3, open 09:55:50, **broker-geschlossen 10:05:56** (`closed by broker SL/TP`, Limit getroffen: close 25 601,3, **+738,98 EUR**). Auflösungsversuche: 10:05:57 ✗ · 10:48:25 ✗ · **12:00:22 ✓** (`reconcile: resolved` 12:00:53, Lesson extrahiert). **Buchungsverzug 1 h 54 min** (alt: ~24 h) → Q1 **nicht FAIL** (Schwelle > 4 h), aber **Erwartung ≤ 1 h 15 min verfehlt**. **IG-Demo-Settlement-Zeit erstmals eingegrenzt: zwischen 42 min und 1 h 54 min nach Close.** Ursache der Lücke (Code-Analyse, keine Änderung): Intervall wächst mit dem Trade-**Alter** (Step bei 30 min Alter → 30 min, ab 60 min → 1 h), plus Reconcile-Takt `reconcile_interval_min = 15` (`phase8_scheduler/scheduler/config.py:143`) → reale Abstände 42 min / 72 min. Breaker war für diesen Trade 1 h 54 min blind (W10; unkritisch, Gewinn). Upgrade-Pfad aus dem `ponytail:`-Kommentar (Anker `_pending_close[...].closed_at` statt `open_ts`) hätte nach dem 10:48-Fehlversuch (42 min nach Close → 30-min-Step) ~11:20 erneut versucht; ob IG da schon gesettelt hatte, ist **unbekannt** — Bewertung für die Closeout-/Plan-Session.
- **Brückenfenster-Ergebnis (v4, 2026-10-15/16) — Report `data/reports/autonomy_2026-10-15_to_2026-10-16.json`** (lokal, `--summary`, Nikinger-Go, gelaufen 2026-10-16 17:31). Script-Gesamtverdikt `FAIL` — **nach v4-Regeln** (K3/K4 nur berichtet) bleibt **ein** echtes FAIL: **K6**.

  | K | Script | v4-Bewertung | Messwert |
  |---|---|---|---|
  | 1 | PASS | PASS | scheduler 1 Start (= Restart 10-15 07:42:26, vor Fensterbeginn), recorder/discovery 0 |
  | 2 | PASS | PASS | 3/3 Auto-Signale; WebUI nicht gesichtet (Operator-Pflicht offen) |
  | 3 | FAIL | berichtet | 2 CLOSED (beide 10-16) |
  | 4 | PARTIAL | berichtet | 1/2: 10-15 ok, **10-16 nicht ok** (`DAX.IFMM` + `DAX.IGN` unter 90 %-Dichte/5-min-Gap, CRITICAL 17:30:56) |
  | 5 | PASS | PASS | id 27: **5** CRITICAL in 24 h (= Grenze), id 28: 3 |
  | 6 | FAIL | **FAIL** | Token-Budget leer **10-15 16:45** (303 910) und **10-16 15:35** (301 031) — Research danach aus; bekanntes K6-Thema (LLM-Subphase) |
  | 7 | PASS | PASS | Start-Zeile `max_trades=5, daily_loss_cap=1800.0` |
  | 8 | PASS | PASS | beide Tage live (Zyklen, Bars, Heartbeat) |
  | 9 | — | **nicht vom Script gemessen** | `NRestarts=0` für alle 4 Units (manuell, 10-16 ~17:35) → PASS. Drift: Script bewertet 8 Kriterien, v3 vorregistriert 9 |

  **Q1** 2 Samples: id 27 1 h 54 min ✗ Erwartung (nicht FAIL), id 28 **1 h 06 min ✓** · **Q2** 0× `reason_gate_constraints` ✓ · **Q3** 0× `credit balance` ✓ · **Q4** 0 Restarts bei offener Position ✓ · **W1** 2/2 BUY DAX · **W9** `InstinctValidator`-CRITICAL 0× — **aber** Extractor scheitert jetzt 3/3 vorher (`extractor returned ok=False … JSONDecodeError … Unterminated string`, trade_id 26/27/28 — LLM-JSON abgeschnitten, Verdacht `max_tokens`, nicht verifiziert) → Bridge weiter tot, Defekt wandert eine Stufe nach vorn · **W10** Breaker-Blindzeit = Q1-Verzüge. **P&L Fenster:** 2 Trades, 2 Gewinner (beide Limit +45 Pkt), **+1 593,71 EUR** (kein Kriterium).
- **Run-10-Closeout** (Auswertung v3 gegen Prereg-AK, Ursachen der 0-Trade-Tage trennen: 10-09 LLM-Guthaben, 10-12..14 blockierter Slot, sonst echte Abstains) — wartet auf Nikinger-Go.
- Commit der 3 Doc-Änderungen + dieser Rotation wartet auf Nikinger-Go.

### Open questions / blockers
- K6-Schwelle + LLM-Switch weiter offen (Session #36 → Opus-Plan-Session).
- Fleet-Vorschlag `LLM_UNAVAILABLE` als eigener Abstain-Grund + laute Meldung — offen, nicht entschieden.
- Ursache des Scheduler-Stopps 2026-10-08 zwischen 15:43 und 16:59 unbekannt.
