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
updated: 2026-09-22 (+ **R5 + R6 ausgeführt (Opus 5, Session #34)** [4 systemd-User-Units + `scripts/install_units.sh` installiert + enabled (nicht gestartet), Keyring aus Unit-Umgebung per `systemd-run --user` bewiesen, 3 Plan-Drifts korrigiert (graphical-session.target, StartLimit* in [Unit], StandardOutput=append:); R6 Token-Aufschlüsselung gemessen (pro Stage unmöglich — kein `stage`-Feld; Research = 94 % des Caps) + 2 Entscheidungen beim Nikinger; F6 gefixt (atomarer `llm_usage.json`-Write) + phase4-Datum-Drift (Fixture); Σ 1958→1960; R7 blockiert auf K6-/K1-Entscheidung + Reboot-Test]). — Vorheriger Stand: 2026-09-22 (+ **R0-R4 ausgeführt (Sonnet 5, Session #33)** [Drift #12/#13/#11/#9 gefixt + F8 (neues K8-Liveness-Gate) + R4-Archivierung (Log 2,37 GB→44 MB gzip, 4 055 221 `ls`-Bars archiviert + aus Live-DB gelöscht, beide DBs integrity-check ok); Σ 1948→1958; R5-R7 offen, siehe Session-Block]). — Vorheriger Stand: Tag-9-Status-Check 2026-09-21 (Opus 5, Session #32, siehe Archiv), Tag-5-Status-Check 2026-09-15 (Drifts #9/#10/#11, deferred), Exec-Session #31 Wrapper-Skript-Fix Drift #8

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
## Session stopped — 2026-09-22 (Opus-5-Session #34, Phase-16-R-Subphase **R5 gebaut + installiert, R6 gemessen + vorgelegt, F6 gefixt** — 4 Commits (scripts/phase4/phase4/phase16-docs); **R5 Autostart**: 4 getrackte systemd-**User**-Units + `scripts/install_units.sh`, `systemd-analyze --user verify` grün, installiert + `enable`d (**nicht** gestartet), Keyring-Erreichbarkeit aus einer echten Unit-Umgebung per `systemd-run --user` **bewiesen**; **zwei Plan-Drifts korrigiert** (`WantedBy=graphical-session.target` statt `default.target`, `StartLimit*` in `[Unit]` statt `[Service]`) + **eine Plan-Lücke geschlossen** (`StandardOutput=append:` auf `data/state/run_*.log`, sonst wären K1/K5/K8 blind); **R6** Token-Aufschlüsselung gemessen (301 225/302 892 gegen den Plan reconciled) — Aufschlüsselung **pro Stage strukturell unmöglich** (kein `stage`-Feld), pro Modell geliefert; **F6 gefixt** (`token_meter` schreibt atomar); **phase4-Datum-Drift gefixt** (Fixture gegen echte Uhr); Σ **1958 → 1960**, alle 16 Suites grün, 0 Fails; **R7 blockiert auf zwei Nikinger-Entscheidungen** (K6-Schwelle, K1-Semantik unter systemd) + Reboot-Test; Session #33 verbatim nach `SESSIONS_ARCHIVE.md` rotiert [34. Eintrag])

> **Auftrag:** Nikinger-Notiz zum Session-Start (2026-09-22): R5 (Units + Installer + Reboot-Test),
> R6 (K6-Aufschlüsselung + Entscheidung), R4.4-Nachzug, R7 (Prereg v3 + Neustart), plus die Frage,
> ob der `phase4_research`-Datum-Drift eine Session wert ist. Kein Plan-Rewrite — der
> `PHASE16_R_EXEC_PLAN.md` (Session #32) wurde gegen den Code verifiziert; die drei unten
> dokumentierten Abweichungen sind **Korrekturen am Plan gegen gemessene Fakten**, keine
> Neuplanung.

### Completed

**R5 — Autostart (R-L3), gebaut + installiert + enabled, nicht gestartet:**

- 4 getrackte Units in `phase16_activation/systemd/`: `tradingbot-scheduler.service`,
  `-recorder.service`, `-discovery.service`, `-webui.service`.
- `scripts/install_units.sh` (Muster `scripts/install_hooks.sh`): idempotent, `--dry-run`,
  `--verify`; ruft **zuerst** `systemd-analyze --user verify`, kopiert nach
  `~/.config/systemd/user/`, `daemon-reload`, `enable` — **kein `start`** (R7.4, Operator).
- Ausgeführt: verify grün, 4 Units installiert, 4 Symlinks in
  `graphical-session.target.wants/` angelegt, `is-enabled` = `enabled` ×4,
  `is-active` = `inactive` ×4 (**nichts gestartet**).

**Drei Abweichungen vom Plan-Text — alle gegen gemessene Fakten, alle notiert:**

| # | Plan (§3 R5) | Gebaut | Warum |
|---|---|---|---|
| D-R5-a | `WantedBy=default.target`, `After=network-online.target` | `WantedBy=graphical-session.target`, `After=graphical-session.target gnome-keyring-daemon.service`, `PartOf=graphical-session.target` | Die Credentials liegen im Secret Service, und `gnome-keyring-daemon.service` ist ein **User-Unit der graphischen Sitzung**, entsperrt von `gdm-autologin` (PAM-Worker `pam/gdm-autologin` heute gemessen). Am 2026-09-20 wurde `default.target` **18:29:07** aktiv, `graphical-session.target` **18:29:10** — eine `default.target`-Unit startet also ~3 s **vor** dem Keyring, fällt in den fail-closed Credential-Preflight und wäre nach `RestartSec=30` × `StartLimitBurst=3` in 90 s endgültig tot. |
| D-R5-b | `RestartSec=30` + `StartLimitIntervalSec/Burst` im selben Block | `StartLimit*` in `[Unit]` | systemd liest `StartLimitIntervalSec`/`StartLimitBurst` nur in `[Unit]`; in `[Service]` werden sie ignoriert (und `systemd-analyze verify` warnt). Der Flap-Schutz hätte still gefehlt. |
| D-R5-c | (im Plan nicht erwähnt) | `StandardOutput=append:…/data/state/run_<svc>.log` + `StandardError=` dito | `autonomy_report.py` liest K1/K5/K8 **aus diesen Dateien** (`run_scheduler.log` timestamped Start-Zeile, die drei Wrapper-Logs als full-file-count). Ohne `append:` landet alles im Journal und die Messgrundlage des gesamten Vorregistrierungs-Laufs verschwindet. |

**Eine bewusste Konstruktionsentscheidung (dokumentiert, statt still):** `run_scheduler.sh`
startet selbst per `nohup` den Recorder **und** den Discovery-Daemon (Z. 60-66). Vier Units, die
den Wrapper aufrufen, hätten beide doppelt gestartet — und zwar in der **Cgroup der
Scheduler-Unit**, so dass `systemctl stop tradingbot-scheduler` die beiden fremden Units
mitgerissen hätte. Deshalb:

- `-recorder`/`-discovery`/`-webui` rufen **ihren Wrapper** auf (die `exec`en python, bleiben
  also PID 1 der Unit ⇒ `Type=simple` korrekt, V-3 damit verifiziert), und ihre K1-Start-Zeile
  (`[run_recorder] starting recorder from …`) bleibt erhalten.
- **nur** `-scheduler` umgeht den Wrapper: `ExecStart=<venv>/bin/python -m scheduler.run`,
  `WorkingDirectory=…/phase8_scheduler` (genau das `cd` des Wrappers). K1/K5 hängen an der
  Start-Zeile des **Daemons** (`scheduler/run.py:207`, timestamped) — die bleibt unberührt,
  ebenso die Caps `max_trades=5, daily_loss_cap=1800.0` (argparse-Defaults; `restart-services.sh`
  übergibt keine Flags, im Archiv-Log so belegt). Ein Kommentar in der Unit nennt
  `run_scheduler.sh` als gespiegelte Quelle.
- `scripts/restart-services.sh` bleibt **unverändert** (R5.4, manueller Notweg).

**Keyring-Beweis ohne Reboot (der Teil von AK-R6, der vorab entscheidbar ist):**
`systemd-run --user --wait --pipe <venv>/python -c "get_credential('ig_demo_api_key')"` läuft
**als transiente User-Unit** (also mit Unit-Umgebung, nicht mit der Shell-Umgebung) und liefert
`DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus`, `XDG_RUNTIME_DIR=/run/user/1000`,
`ig_demo_api_key: FOUND len 41`, Exit 0. Damit ist bewiesen: eine User-Unit erreicht den
entsperrten Keyring. **Nicht** bewiesen (und nur per Reboot beweisbar): dass die Reihenfolge
beim Boot hält. Das bleibt AK-R6 und Operator-Aktion.

**R6 — K6-Analyse (F7), gemessen:**

- **Reconciliation gegen den Plan exakt:** mit der Budget-Definition aus `scheduler/budget.py`
  (alle vier Token-Felder incl. `cache_*`) und Berliner Tagesgrenze ergibt sich 09-16 =
  **301 225** (Überschreitung 17:22 Berlin), 09-17 = **302 892** (16:45) — identisch zu den
  Plan-Zahlen §1.4.
- **R6.1 ist so nicht erfüllbar:** `llm_usage.json` trägt **kein `stage`-Feld** (Record =
  `ts, model, input_tokens, output_tokens, cache_*, est_cost_*`). Eine Aufschlüsselung nach
  Research/Bull/Bear/Judge/Lesson/Council **existiert in den Daten nicht** und wird hier
  **nicht geraten**. Modell-Ebene ist die Obergrenze: Sonnet = Research + Judge + Council,
  Haiku = Bull + Bear + Lesson/Instinct (`research/models.py`, `debate/models.py:134-135`,
  `reward/models.py:378`).

| Tag (Berlin) | billed | Calls | Sonnet | Haiku | 300k gerissen |
|---|---|---|---|---|---|
| 09-11 | 283 966 | 100 | 95 Calls / 281 777 | 5 / 2 189 | — |
| 09-14 | 287 002 | 100 | 95 / 284 854 | 5 / 2 148 | — |
| 09-15 | 283 122 | 99 | 94 / 280 910 | 5 / 2 212 | — |
| **09-16** | **301 225** | 113 | 100 / 287 770 | 13 / 13 455 | **17:22** |
| **09-17** | **302 892** | 121 | 98 / 277 810 | 23 / 25 082 | **16:45** |
| 09-18 | 277 345 | 100 | 95 / 275 158 | 5 / 2 187 | — |

- **Der Befund in einem Satz:** ~95 Research-Calls/Tag × ~2 950 Token = **94 % des Caps**,
  bevor irgendeine Debatte stattfindet. Research läuft **pro Zyklus unbedingt**
  (`runner.py:393` → `research_tick.ensure_candidates` → `research.run()`, keine
  Frische-/Änderungs-Bedingung), bei `cycle=5min` also ~96 Zyklen/Tag. Die ~17 k Restluft
  reichen für ~6 Haiku-Calls; 09-16 (13) und 09-17 (23) haben genau das überschritten. Ein Tag
  **mit** Debatten reißt K6 strukturell.
- **Kostenlage:** ~1,10 USD/Tag (Sonnet 3/15 USD per Mtok). Der Cap ist eine **Sicherheits-
  bremse, keine Kostengrenze** — Cap-Anhebung ist in Euro billig und in Bedeutung teuer (sie
  wurde in Phase 16 C3 schon einmal 200k → 300k angehoben, `scheduler/config.py:140`, wegen
  genau dieses Symptoms).
- **F6 (Leserace) ist strukturell bestätigt und gefixt** (siehe unten). V-5 damit beantwortet:
  der Writer liegt in **P4** (`research/token_meter.py`), nicht P8 — P4 ist per R-L6/Plan §4
  freigegeben, die engere Plan-Formulierung R6.3 („nur wenn in Phase 16 / P8") ist Plan-Drift,
  keine fehlende Freigabe.

**F6 — `llm_usage.json` wird jetzt atomar geschrieben (P4):**
`token_meter.record` schrieb die ~1 MB große JSON-Array-Datei bei **jedem** Call mit
`open(path, "w")` in-place — ein Leser (WebUI) trifft dabei zwangsläufig irgendwann eine
halb geschriebene Datei, loggt einen Parse-Fehler und zählt „0 tokens today"; d. h. **K6 kann
still 0 messen**. Fix: `tmp` + `os.replace` (Muster `run.py:_write_pid`). +1 Test
(`test_record_writes_atomically`) pinnt, dass das Ziel im Moment des Rename noch das
vollständige alte Array trägt.

**`phase4_research`-Datum-Drift (Nikinger-Frage: eine Session wert?) — nein, 1 Fixture-Zeile:**
`build_context` hat **keinen** `now_fn`-Seam und vergleicht gegen die echte Uhr — das ist
**produktiv richtig**. Falsch war der Test: `test_build_context_window_default_14_days` datierte
seine Fixture-Trades gegen `_FIXED_NOW = 2026-09-05`, also war der „3 Tage alte" Trade am
2026-09-22 real 20 Tage alt und fiel korrekt aus dem 14-Tage-Fenster. Fixture jetzt gegen
`datetime.now(timezone.utc)` + Kommentar warum. Kein Produktionsdefekt, keine eigene Session.

**Σ:** 16 Suites einzeln nachgemessen (Konvention ohne `meta_m1_harness`, das 28 trägt):
97+82+105+**163**+190+76+261+169+95+165+149+85+61+126+15+121 = **1960 passed, 0 failed**
(1958 aus Session #33 **+1** neuer F6-Test **+1** der zuvor rote phase4-Test).

### Findings

🔴 **Der Plan hätte AK-R6 verfehlt.** `WantedBy=default.target` + `After=network-online.target`
(Plan §3 R5.1) ignoriert, dass der Keyring in der graphischen Sitzung hängt. Die 3-Sekunden-
Differenz vom letzten Boot ist der Beleg, nicht eine Vermutung.

🔴 **Ohne `StandardOutput=append:` hätte der Autostart die Messung des Laufs zerstört** — Units
loggen per Default ins Journal, `autonomy_report.py` liest Dateien. Das wäre erst an Tag 1 des
neuen Laufs aufgefallen.

🟡 **`StartLimit*` im falschen Abschnitt** wäre still gescheitert (Flap-Schutz ohne Wirkung).

🟡 **K6 ist unter der heutigen Zyklus-Zahl nicht haltbar** — nicht wegen Ausreißern, sondern
weil Research allein 94 % des Caps verbraucht. Entscheidung Nikinger (unten).

🟡 **systemd invertiert die Bedeutung von K1.** K1 („≤ 2 Starts/Tag", aus Start-Zeilen gezählt)
existiert, um zu beweisen, dass **niemand von Hand** neu gestartet hat. Unter
`Restart=on-failure` schreibt eine gesunde Selbstheilung eine Start-Zeile, **ohne** dass jemand
etwas angefasst hat — ein selbstheilender Tag liest sich dann als K1-FAIL. Der natürliche
Diskriminator ist `systemctl --user show -p NRestarts <unit>` (systemd-eigener Zähler) gegen die
Log-Start-Zeilen. **Das ist eine Vorregistrierungs-Frage und blockiert Prereg v3** — genau wie
die K6-Schwelle.

🟢 **V-3 und V-5 beantwortet** (Type=simple korrekt; Writer in P4). **V-1/V-2** waren in Session
#33 geprüft. **V-6** ist mit dem VACUUM in Session #33 erledigt. **V-7** bleibt offen bis zum
Reboot-Test — `enable` hat die Symlinks angelegt, das Boot-Verhalten ist damit nicht bewiesen.

### Open questions / blockers

**Zwei Nikinger-Entscheidungen blockieren R7** (Prereg v3 darf **nicht** mit einem TBD
geschrieben werden — AK-R8 verlangt sie vollständig und committet **vor** der ersten
Startzeile):

1. **K6-Schwelle / Token-Haushalt.** (a) Cap anheben (z. B. 300k → 400k; ~1,10 USD/Tag heute,
   die zweite Anhebung nach C3) · (b) Call-Zahl senken (Zyklus 5 → 10 min halbiert Research auf
   ~48 Calls ≈ 145k und halbiert die Einstiegs-Chancen; oder Research nur bei geänderter
   Datenlage — **neue Logik, nicht lazy**) · (c) K6-Schwelle in v3 neu setzen bzw. das Kriterium
   auf „kein Zyklus wurde budget-gated" umformulieren statt auf eine absolute Zahl.
2. **K1-Semantik unter systemd** (siehe Finding oben): K1 an `NRestarts` koppeln, oder Schwelle
   anheben, oder K1 explizit als „Operator-Starts" definieren und Auto-Restarts separat zählen.

**Operator-Aktionen (Nikinger):**
- **Reboot-Test (AK-R6)** — der einzige ehrliche Beweis. Erwartung: alle vier Units nach dem
  Boot `active`, ohne Handgriff. Prüfen mit `systemctl --user status 'tradingbot-*'` +
  `bash scripts/restart-services.sh status`. Wenn eine Unit `failed` ist:
  `journalctl --user -u tradingbot-scheduler -b` — der erste Verdächtige ist die
  Keyring-Reihenfolge, **nicht** die Unit-Syntax (die ist verify-geprüft).
- **Push** der 4 Commits dieser Session.
- **Start des neuen Laufs** erst nach R7 (Prereg v3 + Runbook v4 committet).

**R4.4 bleibt offen** — die erste neue `ls`-Bar auf `:00.000Z` ist erst prüfbar, wenn der Bot
wieder schreibt (also nach dem Start).

### NEXT (für die nächste Session)

1. **Antworten des Nikinger zu K6 + K1 einholen** (die zwei Fragen oben) — ohne sie kein
   Prereg v3.
2. **R7.1** `PHASE16_AUTONOMY_PREREGISTRATION_v3.md` schreiben (v2 bleibt byte-identisch):
   K1 (neue Semantik) · K2-K5 unverändert · K4 „≥ 8 von 10 des **vollen** Fensters" (R3.2) ·
   K6 nach Entscheidung · K7 · **K8 Liveness** (R3.3) · W1-W5 + **W6** (`ls`-Bars enden auf
   `:00.000Z`) + **W7** (`run_scheduler.log` < 200 MB); Tag 1 / Tag 10 als Datum eintragen.
3. **R7.2** `PHASE16_E3_RUNBOOK_v4.md`: Restart-Sequenz über `systemctl --user`,
   `restart-services.sh` als Notweg, Tagesroutine G1/G2/G5 mit den korrigierten Kommandos.
4. **R7.3/R7.4** Commit **vor** der ersten Startzeile, dann Start durch den Nikinger +
   Tag-1-Verify (inkl. **R4.4**-Stichprobe und `grep -c NameError run_scheduler.log` = 0 für
   AK-R1).
5. **Block I (Closeout)** bleibt liegen bis der neue 10-Tage-Lauf durch ist (R-L5).

**Block-Status nach Session #34:**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ (Session #1-#4) |
| B (Substrat) | ✅ (Session #3) |
| C (Research-Loop) | ✅ (Sessions #3-#7) |
| D (Freischaltung) | ✅ (Session #7-#17) |
| E (2-Wochen-Test) | 🔴 abgebrochen an Tag 9 — Neu-Vorregistrierung in R7 |
| F (Subphase) | 🔄 — G Tag 1 ✅, H ✅ (#28-#29), Quick ✅ (#30), Mini ✅ (#31), Status-Check ✅ (#32) |
| R (Reparatur 2 + Neustart) | 🔄 — **R0-R4 ✅ (#33), R5 ✅ + R6 ✅ (#34)**; R7 blockiert auf 2 Nikinger-Entscheidungen + Reboot-Test |
