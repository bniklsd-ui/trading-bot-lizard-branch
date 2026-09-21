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
updated: 2026-09-21 (+ **Tag-9-Status-Check (Opus 5, no-code-Session #32)** [Block-G-Tagesroutine G1/G2/G5 nach Umzugspause; **Befund: der Lauf steht** — VM-Shutdown So 2026-09-20 12:15 / Boot 18:29, **kein Autostart** (weder systemd noch Cron, 4 manuelle `nohup`-Wrapper) ⇒ Montag 2026-09-21 ist ein komplett ausgefallener Handelstag, AK-G1/K5 gebrochen, 8 gültige Handelstage 09-09…09-18; **2 neue Struktur-Defekte**: Drift #12 `NameError: record_event` (`wiring.py:1240`, latent seit `a58a352`, 4 368 060 Tracebacks, Log 2,37 GB) und Drift #13 `_iso_utc_minute` behält die Tick-Millisekunde (`stream.py:38`) ⇒ 4 055 221 Tick-Zeilen als „1m-Bars", 973 MB, `test_stream.py:255` pinnt den Bug; J1 hält (Bars landen, 0 `ProgrammingError` im laufenden Prozess), K4/yF-Substrat unberührt weil alle Konsumenten `sources=("yf",)` lesen; Σ 1948 unverändert]). — Vorheriger Stand: Tag-5-Status-Check 2026-09-15 (Drifts #9/#10/#11, deferred), Exec-Session #31 Wrapper-Skript-Fix Drift #8

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

### 🟠 F5 — Tagesroutine seit 09-14 nicht gelaufen (Operator-Lücke, kein Code-Defekt)

`data/reports/` enthält 09-08 … 09-13; **09-14 bis 09-21 fehlen** (8 Tage). G1 ist eine
Nikinger-Aktion (Exec-Plan §3 Block G) und wurde während der Umzugsphase nicht ausgeführt.
Der 09-13-Report ist zusätzlich der von **Drift #11** überschriebene (Status-Check 09-15).

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

Der Exec-Plan definiert „Tag 10 = Tag 1 + **9 Handelstage**" (§3 Block I). Tag 1 = 2026-09-09 ⇒
09-10 (2), 09-11 (3), 09-14 (4), 09-15 (5), 09-16 (6), 09-17 (7), 09-18 (8), 09-21 (**9**),
09-22 (**10**). Der Status-Check-Block vom **2026-09-15 ist im Phasenkopf als „Tag 7" geführt** —
das war eine Kalendertag-Zählung; nach Plan-Definition war es **Tag 5**. Der Block-I-Termin
Di 2026-09-22 ist von der Korrektur **nicht** betroffen (er stimmt mit der Handelstag-Zählung).
Korrigiert 2026-09-21 gegen den Plan-Text; der archivierte 09-15-Block bleibt verbatim.

### Kriterien-Stand Tag 9 (2026-09-21)

| K | Stand | Anmerkung |
|---|---|---|
| K1 (Restarts) | — | kein Prozess ⇒ nicht messbar; Drift-#8-Fix weiter **nicht** live verifiziert (Restart nötig) |
| K2 (Auto-Signale) | ❌ | 0 Events heute (Bot aus); zusätzlich Drift #10 (falsche Event-Namen) |
| K3 (≥ 5 CLOSED-Trades) | ❌ | 0 Trades im ganzen Lauf |
| K4 (Heartbeat-Tage) | ❌ | heute kein Heartbeat; Drift #9 (Threshold-Wording) unverändert |
| K5 (keine Hand) | ❌ | gebrochen: der Lauf braucht jetzt einen manuellen Restart |
| K6 (Token-Budget) | — | heute 0 Verbrauch (Bot aus); Messung zusätzlich unsicher (F6) |
| K7 (Caps-Pin) | ✅ | Caps-Zeile korrekt |

---

## Session stopped — 2026-09-21 (Opus-5-Session #32, Phase-16-F-Subphase **Tag-9-Status-Check (Block G, no-code)** — 0 Code-Commits, 1 Doc-Commit (dieser Block + Rotation Session #31); **Lauf steht seit Reboot So 2026-09-20 18:29, Montag 09-21 komplett ausgefallen**; 2 neue Struktur-Defekte gefunden (**Drift #12** `NameError: record_event`, 4,37 Mio Tracebacks, 2,37 GB Log · **Drift #13** `_iso_utc_minute` behält ms ⇒ 4,05 Mio Tick-Zeilen als „1m-Bars", 973 MB, Test pinnt den Bug); J1 hält (Bars landen, 0 `ProgrammingError` im laufenden Prozess); K4/yF-Substrat unberührt und ehrlich; Σ **1948 unverändert** (kein Test-Touch); Session #31 verbatim nach `SESSIONS_ARCHIVE.md` rotiert [32. Eintrag])

> **Auftrag:** Nikinger 2026-09-21 ~19:20 Berlin: „Please do the planned check!" (nach Umzugspause).
> Ausgeführt: Block-G-Tagesroutine G1/G2/G5 + Health-Check, **read-only**. Keine Restarts, keine
> Code-Edits, keine Fixes — beides ist Nikinger-Entscheidung, Drift #13 braucht zusätzlich eine
> P13-Cross-Phase-Freigabe, die nicht vorliegt.

### Completed

1. **G2 Caps-Pin geprüft** — letzte `starting scheduler daemon`-Zeile (Z. 795 707, 2026-09-08 15:27:43)
   trägt `account=demo, max_trades=5, daily_loss_cap=1800.0, cycle=5min`. ✅
2. **G5 geprüft** — Log 2,37 GB (Soll < 50 MB) ❌; `ProgrammingError` 98 820, aber **alle** in
   Zeilen 4 982–795 703 = Vor-J1-Lauf ⇒ im laufenden Prozess 0 ✅. Befund am Prüfverfahren
   dokumentiert (nie rotiertes Log ⇒ `grep -c` mischt zwei Läufe).
3. **G1 nicht ausgeführt** — bewusst: `autonomy_report.py` schreibt unter **Drift #11** in eine
   falsche Datei und würde einen bestehenden Report überschreiben; außerdem gibt es für Tag 9
   keine Daten (kein Prozess). Nachgeholt wird die Lücke 09-14…09-21 erst nach der
   Nikinger-Entscheidung über den Lauf.
4. **Live-Zustand gemessen** — `ps` leer, `last -x reboot` (Shutdown 09-20 12:15 / Boot 18:29),
   kein systemd-Unit, kein Cron, `uptime` 1 d; letzte Aktivität 09-18 17:33.
5. **Zwei Struktur-Defekte root-cause-belegt** — Drift #12 (`wiring.py:1240`, latent seit
   `a58a352`) und Drift #13 (`stream.py:38`, Test `test_stream.py:255` pinnt ihn), beide mit
   Live-Zahlen und Fix-Pfad im Live-Beobachtungs-Block oben.
6. **Blast-Radius von Drift #13 eingegrenzt** — `grep` über alle `archive.window(...)`-Aufrufer:
   `heartbeat.py:175`, `heartbeat.py:338`, `rescue.py:343` lesen `sources=("yf",)`; **kein**
   Produktions-Konsument liest `source='ls'`. K4 bleibt damit gültig gemessen.
7. **Tag-Zählung gegen den Plan korrigiert** (heute = Tag 9, nicht Tag 11; der 09-15-Block war
   Tag 5, nicht Tag 7) — dated note im Beobachtungsblock, Block-I-Termin unverändert.

### Findings

🔴 **Der zweite 10-Tage-Lauf ist nicht mehr PASS-fähig** — nicht an Tag 1 wie am 2026-09-08,
sondern an Tag 9: K5 („ohne Hand") ist gebrochen, sobald jemand neu startet, und AK-G1 verlangt
10 Tagesreports ohne manuellen Restart. Gültig gemessen sind 8 Handelstage (09-09…09-18).

🔴 **Gleiches Muster wie am 2026-09-08, andere Stelle:** die Kriterien meldeten grün, während das
Substrat darunter falsch war. Damals schrieb der LS-Pfad nichts; heute schreibt er 140×
zu viel und das Geschriebene ist keine Minutenkerze. Beide Male hat erst eine Messung am
laufenden System es gezeigt, keine Statusprosa.

🟢 **J1 (der Fix vom 2026-09-08) hält.** 4,05 Mio `ls`-Zeilen, 0 `ProgrammingError` im laufenden
Prozess. Der Thread-Bug ist zu; was ihn verdeckt hat, war ein zweiter Bug dahinter.

🟢 **Der Ausfall ist kein Absturz.** Sauberer Shutdown, sauberer Boot, `consecutive_failures=0`,
`kill_reason=null`. Es fehlt schlicht ein Autostart — vier manuelle `nohup`-Wrapper überleben
keinen Reboot. Das ist die eigentliche Lehre für die Neu-Vorregistrierung.

### Open questions / blockers

- **Entscheidung Nikinger (1):** Lauf als FAIL abschließen + nach Fix neu vorregistrieren (Muster
  2026-09-08, dann `PHASE16_AUTONOMY_PREREGISTRATION_v3.md`), **oder** ungefixt neu starten und
  Tag 9 als Loch dokumentieren.
- **Entscheidung Nikinger (2):** Cross-Phase-Freigabe **P13** (`live_data/stream.py` +
  `phase13_live_data/tests/test_stream.py`) für den Drift-#13-Fix. Ohne sie bleibt der Defekt offen.
- **Entscheidung Nikinger (3):** Autostart (systemd-Unit je Dienst) — heute existiert keiner;
  ohne ihn kostet jeder Reboot den Lauf.
- **Entscheidung Nikinger (4):** Aufräumen von `data/state/run_scheduler.log` (2,37 GB) und der
  4,05 Mio Tick-Zeilen in `data/bars.sqlite` (973 MB) — destruktiv, daher nicht ohne Freigabe.
- **Block I Tag-10-Closeout (Di 2026-09-22)** steht terminlich, hat aber jetzt einen anderen
  Inhalt: kein „10 Tage sauber gelaufen"-Abschluss, sondern ein Closeout mit dokumentiertem
  Abbruch (analog 2026-09-08).
- **Unverändert offen:** Drifts #9/#10/#11 (deferred 2026-09-15), Drift-#8-Fix live nicht
  verifiziert (braucht Restart), Gate P7/A6 (wartet auf ersten OPEN-Trade).

### NEXT (für die nächste Session)

1. **Nikinger-Entscheidungen (1)–(4) oben einholen** — alles Weitere hängt daran.
2. **Bei Freigabe „fixen":** Drift #12 (P8, unblocked, lokaler Import wie `wiring.py:906/1136`,
   + 1 Regressionstest) und Drift #13 (**nur mit P13-Freigabe**: `.000Z` konstant in
   `_iso_utc_minute`, `test_stream.py:255` mit-korrigieren, +1 Test „zwei Ticks derselben Minute
   ⇒ eine Bar mit `tick_count=2`"). Σ-Erwartung 1948 → ~1951.
3. **Danach:** Autostart einrichten, Log rotieren, Lauf neu vorregistrieren, Tag 1 neu takten.
4. **Session #33 = Block I** (Closeout), Inhalt wie unter „Open questions" beschrieben.

**Push-Status:** vor dieser Session 5 Commits pending (Session #31); diese Session fügt 1
Doc-Commit hinzu. Nikinger pusht.

**Block-Status nach Session #32:**

| Block | Status |
|---|---|
| A (Haushalt) | ✅ (Session #1-#4) |
| B (Substrat) | ✅ (Session #3) |
| C (Research-Loop) | ✅ (Sessions #3-#7) |
| D (Freischaltung) | ✅ (Session #7-#17) |
| E (2-Wochen-Test) | 🔴 **abgebrochen an Tag 9** (Reboot 09-20 ohne Autostart) — 8 gültige Handelstage, Entscheidung über Neu-Vorregistrierung offen |
| F (Subphase) | 🔄 — G Tag 1 ✅, H ✅ (#28-#29), Quick ✅ (#30), Mini ✅ (#31), **Status-Check ✅ (#32)**, I (#33) |
