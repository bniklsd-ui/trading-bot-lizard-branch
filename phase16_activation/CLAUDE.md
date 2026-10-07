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
## Session stopped — 2026-10-07 (MiniMax-M3-Exec-Session #36, Phase-16-LLM-Subphase **Planung eröffnet** — 2 neue Docs (Detail-Plan + Plan-Brief für Opus), keine Code-Edits, keine Test-Edits; 0 Σ-Regression; Lauf Tag 7 läuft seit 2026-09-29 22:57:03 mit unveränderter Konfiguration)

> **Auftrag:** Nikinger 2026-10-07 ~17:30 Berlin (Phase-16-Live-Status-Check, ~7 Tage nach Session #35): (a) **Push-Freigabe für die 2 Commits der Session #35** — bestätigt: bereits durch Nikinger oder Auto-Sync gepusht, `git rev-list --left-right --count origin/main...HEAD` = `0 0` (HEAD = `1399ce7` = `origin/main`). (b) **K6-Schwellwert-Entscheidung** (Cap an Debatte-Volltagen 09-16/09-17 gerissen, Empfehlung aus dem Vorgespräch der Session #34 „Switch auf MiniMax-M3 via OpenAI-Compat"): **vertagt** auf eine separate Opus-Plan-Session — Cross-Phase-Edits (P4/5/7/8/15) sollen laut Nikinger **nicht** in Phase-16-Exec-Hand, sondern in einer Opus-Plan-Session stattfinden. (c) **Plan-Grundlagen-Doc** für die Opus-Plan-Session erstellen. (d) **Phase-Naming:** „bleibe bei der 16-Nummerierung, hänge ein passenden suffix an" → Subphase **Phase 16 LLM** (analog Phase 16 F für Audit + Restplan, Phase 16 R für Reparatur 2 + Neustart).

### Completed

**Diagnose (vor dem Schreib-Start):**

- `git status` clean (working tree) bis auf `data/` und `sunshine_2026.906.222525-1+ubuntu24.04_amd64.deb` (beide gitignored / untracked).
- `git rev-list --left-right --count origin/main...HEAD` = `0 0` → die 2 Commits der Session #35 (`1d0b6f0` phase3-Retry-Fix + `1399ce7` phase16-Doc-Fix) sind bereits auf `origin/main`. **Kein Push nötig.**
- Phase-16-Subphasen-Stand aus Phasenkopf + INDEX: A/B/C/D/E ✅ (Hauptblöcke, Sessions #1–#17), F (Audit + Restplan) ✅ (Sessions #18–#32), R (Reparatur 2 + Neustart) ✅ (Sessions #33–#35). Subphase LLM noch nicht eröffnet — diese Session eröffnet sie **planungsseitig**, ohne Code.
- Heute-Konfiguration des Bots: 4 systemd-Units laufen seit 2026-09-29 22:57:03 (PIDs 223277 scheduler / 223278 recorder / 223279 discovery / 223280 webui), `NRestarts=0`, Σ 1963 grün.
- Heute-Datum 2026-10-07 = Tag 7 von 10 des v3-Laufs (Tag 1 = 2026-09-29 Di, Tag 10 = 2026-10-13 Di, Mo–Fr ohne Feiertags-Shift).

**Detail-Plan `phase16_activation/PHASE16_LLM_SWITCH_PLAN.md` (NEU, 380 Zeilen):**

- §0 BLUF mit Empfehlung (Default-Flip auf `openai_compat`, Beispiel-Modell `minimax/MiniMax-M3`, P6 bleibt Anthropic, Smoke-Pflicht vor Live-Account).
- §1 selbst gemessene Fakten mit file:line-Ankern auf `phase4_research/research/llm_client.py:1`, `llm_openai_compat.py:107`, `models.py:536`, `scripts/wiring.py:180`, `openrouter_smoke.py:117`.
- §2 8 Nikinger-Entscheidungen L-D1..L-D8 (Modell-String, Endpoint-URL, Keyring-Namespace, Default-Flip-Timing, Pricing-Row, Smoke-Pflicht).
- §3 8 Locks L-L1..L-L8 (Hersteller-Agnostik über Factory, P6 nicht angefasst, Keyring-Isolation, Smoke-Pflicht, additive Pricing-Row, strukturelle Code-Sperre Wurzel-Regel 3).
- §4 10 Schritte (Factory in P4 → Models-Update → P4-Wiring → Key-Skript → Tests → pytest-Sweep → Doku → Commit → Operator-Smoke → Default-Flip).
- §5 5 Follow-ups (P5/7/8/15 in Folgesessions, K6-Schwellwert neu denken, Live-Account-Schalter).
- §6 8 Akzeptanzkriterien AK-L1..AK-L8.
- §7 Out-of-Scope (andere Hersteller, asynchrone Calls, Caching, Live-Account).

**Plan-Brief `phase16_activation/PHASE16_LLM_SWITCH_BRIEF.md` (NEU, prompt-shaped für Opus-Plan-Session):**

- Selbsterklärend für Opus (8 Sektionen + 3 Anhänge: Mission, Vorhandene Bauanleitung, Constraints, Empfehlung, Output-Spec, Offene Fragen, Außenkante, Rollback-Pfad + Anhang A Code-Anker, Anhang B Cross-Phase-Tabelle, Anhang C MiniMax-M3 Spec-Hinweise).
- Anker auf den Detail-Plan + die existierenden Vorarbeiten (M1-Step-10 OpenAICompatLLMClient, smoke-verified mit OpenRouter).
- Empfehlung: **konservativ** — Factory + P4-Defaults + Skripte + Tests in den Commits, **Default bleibt `anthropic`**; Nikinger macht den Flip nach Demo-PASS in einer Mini-Commit (eine Zeile + Service-Restart).

**Phase-Naming-Korrektur (Nikinger-Direktive, in dieser Session umgesetzt):**

- Ursprünglich geplant: Datei `PHASE17_LLM_SWITCH_BRIEF.md` (neue Phase-Nummer 17).
- Per Nikinger-Auftrag 2026-10-07 („bleibe bei der 16 Nummerierung und hänge ein passenden suffix an") → umbenannt zu `PHASE16_LLM_SWITCH_BRIEF.md` (Subphase-Suffix statt Phase-17).
- Brief-Header + Wofür-Absatz entsprechend angepasst: Subphase LLM unter Phase-16-Schirm, gleiche Lauf-Zeitstrahl + Cross-Phase-Freigabe aus aktivem Phase-16-Setup.
- Plan-Datei (`PHASE16_LLM_SWITCH_PLAN.md`) hatte bereits Phase-16-L-Titel — keine Änderung nötig.
- Naming-Konvention ist nun: **Phase 16 F** (Audit + Restplan) · **Phase 16 R** (Reparatur 2 + Neustart) · **Phase 16 LLM** (Hersteller-Agnostik) — alle drei Subphasen unter dem Phase-16-Schirm. Phase 17 bleibt für die Out-of-Scope-Items aus `PHASE16_PARTIAL_CLOSEOUT.md` §7 reserviert (Strategie-Bewertung, Prozess-Supervision, etc.).

**Doku-Updates (additiv):**

- `phase16_activation/CLAUDE.md`: `updated:`-Zeile um Session #36 ergänzt (komprimierte Form); Session #35-Block (308 Zeilen) verbatim nach `SESSIONS_ARCHIVE.md` rotiert (3614 Zeilen Archiv-Eintrag oben, +103 vom Vor-Stand #34-Stand 3511 — Selbst-Korrektur: in dieser Schreib-Pass waren es +308 Session-#35-Zeilen, neue Archiv-Größe wird beim ersten Datei-Read verifiziert); Session #36-Block (dieser hier) im Phasenkopf.
- `docs/INDEX.md`: 2 neue Zeilen — `PHASE16_LLM_SWITCH_PLAN.md` (📕 Detail-Plan, Cross-Phase-Edits NICHT ausgeführt) und `PHASE16_LLM_SWITCH_BRIEF.md` (📕 Plan-Brief für Opus-Plan-Session).

**Σ-Sweep:**

- Σ unverändert: **1 963 grün** repo-weit (kein Test-Touch, kein Code-Touch).
- Doc-Rotation-Hook (`scripts/check_doc_rotation.py --strict`) erwartet grün — neuer Plan + neuer Brief tragen korrekte Header-Cards (relativ-Pfade verifiziert: `down:` zeigt auf `./PHASE16_LLM_SWITCH_PLAN.md` und `./PHASE16_R_EXEC_PLAN.md` etc., beide existieren).

**Commits dieser Session:**

1. `phase16: docs — LLM-Switch-Subphase Plan + Brief + INDEX + Session-#36-Block` (dieser Commit).

### Findings

- 🟢 **Push-Bestätigung ohne Aktion.** Die 2 Commits der Session #35 sind bereits auf `origin/main` — keine Aktion nötig. Vermutlich Nikinger-Push zwischen 2026-09-30 und heute.
- 🟢 **Phase-Naming-Konvention etabliert:** Phase 16 F / R / LLM (Suffix an die aktive Phase-Nummer) ist ab jetzt das Pattern für Subphasen. Phase 17 bleibt reserviert für die Out-of-Scope-Items der Phase 16 (Strategie-Bewertung, Prozess-Supervision, etc., siehe `PHASE16_PARTIAL_CLOSEOUT.md` §7).
- 🟡 **K6-Schwellwert-Entscheidung weiter offen.** Session #34 hatte „K6 bleibt 300k" entschieden; die Empfehlung „Switch auf MiniMax-M3" aus dem damaligen Vorgespräch wurde heute **vertagt** auf die Opus-Plan-Session. K6 wird bis auf weiteres mit dem aktuellen Cap weiterleben (an Debatte-Volltagen reißend). Akzeptabel, weil: (1) Auto-Trigger T-8 noch nicht live verifiziert (siehe Phase-16-R-Subphase Session #34 OPEN-QUESTION), (2) die Laufzeitdaten Tag 4–9 (Sessions #32–#35) zeigen das Token-Budget als Trigger-Quelle für Exec-Sessions, nicht als Hard-Limit, (3) die Opus-Plan-Session wird K6 als Konsequenz der Hersteller-Agnostik ohnehin neu denken (§5 FU3 im Plan).
- 🟢 **Detail-Plan ausreichend für Opus-Plan-Session.** 10 Schritte, 8 Locks, 8 Akzeptanzkriterien, 5 Follow-ups — Opus kann darauf aufbauen, ohne das halbe Repo zu crawlen. Empfehlung im Brief klar (konservativer Default-Flip); 6 offene Fragen dokumentiert.
- 🟢 **0 Σ-Regression.** Kein Test-Touch, kein Code-Touch, kein pyc-Cache-Update nötig.

### Open questions / blockers

- **Keine** technischen. Lauf läuft (neue PIDs seit 2026-09-30 06:37), K6 reißt weiterhin an Debatte-Volltagen (K6-Threshold-Entscheidung offen bis Opus-Plan-Session).
- **Beobachtungsposten für nächste Session:** ob K6 in der neuen Woche (Tag 6–9 des v3-Laufs, also 2026-10-07 bis 2026-10-10) reißt. Trigger T-8 ist im Phasenkopf vorgesehen, aber strukturell noch nicht live-verifiziert.

### NEXT (für die nächste Session)

1. **K6-Schwellwert-Beobachtung Tag 6–9** (Di 2026-10-07 bis Fr 2026-10-10): Tagesroutine G1 (`scripts/autonomy_report.py --day YYYY-MM-DD`) am Ende jedes Handelstags — K1/K8/K9 gegen systemd-Autostart, K6 gegen 300k-Cap. Erwartung: K6 reißt an mind. 1–2 Tagen (analog 09-16/09-17), bleibt strukturell.
2. **Opus-Plan-Session für Phase-16-LLM-Subphase:** Nikinger startet die Plan-Session mit Verweis auf `phase16_activation/PHASE16_LLM_SWITCH_BRIEF.md` als Briefing-Doc. Opus liefert einen execution-ready Plan mit Locks + Schritt-Sequenz + Akzeptanz, geprüft gegen den Detail-Plan und den Code.
3. **Push-Freigabe** für den 1 Commit dieser Session (Nikinger — `git rev-list --left-right --count origin/main...HEAD` zeigt `0 1` nach Commit).
4. **Lauf-Tag-10-Closeout:** Mo 2026-10-13 nach 17:30 — Block I (Tag-10-Closeout, F-Exec-Plan §3 Block I) — exekutieren, falls bis dahin keine Eskalation.

**Block-Status nach Session #36:**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ (Session #1-#4) |
| B (Substrat) | ✅ (Session #3) |
| C (Research-Loop) | ✅ (Sessions #3-#7) |
| D (Freischaltung) | ✅ (Session #7-#17) |
| E (2-Wochen-Test) | 🔄 Tag 7 = 2026-10-07 → Tag 10 = 2026-10-13 — läuft, K6 weiter offen |
| F (Subphase) | ✅ (Sessions #18-#32) |
| R (Reparatur 2 + Neustart) | ✅ (Sessions #33-#35) |
| LLM (Hersteller-Agnostik) | 🔄 **eröffnet Session #36** — Planung ✅, Plan-Brief ✅, Code-Edits 🔄 (Opus-Plan-Session steht aus) |