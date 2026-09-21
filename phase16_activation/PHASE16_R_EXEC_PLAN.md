---
status: plan (Entwurf — wartet auf Nikinger-Freigabe)
purpose: Exec-Plan der Phase-16-R-Subphase — Reparatur der beiden am 2026-09-21 gefundenen Struktur-Defekte (Drift #12 `record_event`-NameError, Drift #13 Tick-statt-Minuten-Bar), Reparatur der Report-Tool-Drifts #9/#11, Archivierung statt Löschung von 2,37 GB Log + 4,06 Mio Tick-Zeilen, systemd-Autostart für alle vier Dienste, Prereg v3 und Neustart des 10-Handelstage-Laufs ab Tag 1.
read-when: Ausführung der Phase-16-R-Subphase; VOR jedem Edit an wiring.py, stream.py, autonomy_report.py, an den systemd-Units oder an der Vorregistrierung
detail: L2
up: ./CLAUDE.md
down:
  - ./PHASE16_F_EXEC_PLAN.md                      # 📕 Vorgänger-Exec-Plan (Blöcke J/H/G/I), Muster für Aufbau + Akzeptanz
  - ./PHASE16_AUTONOMY_PREREGISTRATION_v2.md      # 📕 v2, unangetastet — R7 schreibt v3 daneben
  - ./PHASE16_E3_RUNBOOK_v3.md                    # 📕 Operator-Runbook (locked) — R5 macht §Restart-Sequenz teilweise obsolet, v4 in R7
  - ../docs/concepts/phase16_activation_plan.md   # 📕 Vollplan Phase 16 (P1–P17, Blöcke A–E)
  - ./SESSIONS_ARCHIVE.md                         # 📦 Session-Historie (newest-first)
updated: 2026-09-21
---

# Phase 16 R — Exec-Plan (Reparatur 2 + Neustart)

> **Planungssession 2026-09-21 (Opus 5, Claude Code), Session #32.** Jede Zahl unten ist an
> diesem Tag selbst gemessen — gegen Code, `data/bars.sqlite` (`mode=ro`), die Logs und `last`.
> Nichts ist aus einem Vorgänger-Handover übernommen. Was nicht gemessen werden konnte, steht
> vollständig in §6.

## §0 BLUF

- **Der zweite 10-Tage-Lauf ist an Tag 9 gestorben** — nicht an einem Absturz, sondern an einem
  Reboot (So 2026-09-20 18:29) ohne Autostart. Montag 2026-09-21 hatte null Zyklen.
- **Zwei Struktur-Defekte, beide seit Phase 13 latent, beide erst durch den J1-Fix erreichbar:**
  **Drift #12** (`wiring.py:1240` ruft `record_event` ohne Import → 4 368 060 Tracebacks, Log
  2,37 GB) und **Drift #13** (`stream.py:38` hängt die Tick-Millisekunde an den Minuten-Bucket →
  jeder Tick wird eine „1-Minuten-Bar": 4 055 221 Zeilen, 973 MB).
- **Zwei Mess-Defekte obendrauf:** **F7** — K6 war an 09-16 und 09-17 gerissen (301 225 / 302 892
  Tokens vor Handelsschluss) und **niemand hat es gesehen**, weil die Tagesroutine seit 09-14 lag.
  **F8** — der Tagesreport meldet an einem Tag mit null Prozessen **K1/K5/K6/K7 grün**; es fehlt
  ein Liveness-Kriterium.
- **Nikinger-Entscheidungen 2026-09-21 (gelockt, §2):** fixen statt weiterlaufen · P13 freigegeben ·
  Autostart bauen · **archivieren statt löschen** · **kein Closeout jetzt**.
- Reihenfolge: **R0** Haushalt → **R1** Drift #12 → **R2** Drift #13 → **R3** Report-Tool →
  **R4** Archivierung → **R5** Autostart → **R6** K6-Analyse → **R7** Prereg v3 + Neustart Tag 1.

## §1 Selbst gemessene Fakten (2026-09-21)

### 1.1 Live-Stand

| Sache | Messung |
|---|---|
| Prozesse | `ps aux \| grep -E "scheduler\|recorder\|discovery\|webui"` = **0** |
| Boot | `last -x`: Shutdown So 2026-09-20 12:15, Boot 18:29; `uptime` 1 d |
| Autostart | **keiner** — kein systemd-Unit für den Bot, `crontab -l` leer; die vier Dienste sind manuelle `nohup`-Wrapper |
| letzte Aktivität | `research_health.jsonl` 2026-09-18T17:33; letzte `ls`-Bar 2026-09-18T21:00 |
| `run_scheduler.log` | **2 373 056 215 B** (2,37 GB), 35 748 963 Zeilen |
| `data/bars.sqlite` | **973 115 392 B**; `ls` 4 055 221 · `yf` 71 346 · `ig` 3 215 · `capital` 962 |
| Disk `/` | 40 G, 25 G belegt (65 %), **14 G frei** |
| Schema | Live-DB v9 (unverändert seit 2026-09-05) |
| Git | `origin/main` = `ca4e6ea` beim Session-Start; Session #32 legt 5 Doc-Commits obendrauf |

### 1.2 Drift #12 — `NameError: record_event`

- `phase8_scheduler/scripts/wiring.py:1240` (in `_build_recorder`, genestet in `build_scheduler`,
  Z. 808): `health_sink=lambda ev: record_event(config.observability_path, ev)`.
- `record_event` ist in `wiring.py` **nirgends auf Modul-Ebene** importiert. Alle anderen
  Aufrufer importieren lokal: Z. 230, 653, 756, 791, **906** (`as _sampler_record_event`),
  **1136** (`as _health_record_event`).
- Alter: Phase-13-Commit `a58a352` („Step B3 — Scheduler-Lebenszyklus + Token-Rotation").
- Zählung: **4 368 060** Tracebacks im aktuellen Log.
- **Die Bar geht nicht verloren:** `stream.py:497` `insert_bars([bar])` läuft **vor** dem Sink
  (Z. 498–509). Der generische `except Exception` (Z. 515) fängt den Sink-Fehler und loggt ihn als
  `"TickAggregatorRecorder: insert_bars failed for …"` — **die Meldung ist falsch**.

### 1.3 Drift #13 — jeder Tick wird eine Bar

```python
# phase13_live_data/live_data/stream.py:38-44
truncated = dt.replace(second=0, microsecond=0)
ms = dt.microsecond // 1000
return truncated.strftime("%Y-%m-%dT%H:%M:00.") + f"{ms:03d}Z"
```

- Die Millisekunde des Ticks landet wieder im „Minuten"-Bucket ⇒ `TickAggregator.on_tick`
  (Z. 263) sieht bei fast jedem Tick einen Rollover ⇒ eine Bar **pro Tick**.
- Live: `IX.D.DAX.IFMM.IP`, 09-18, 07:00–15:30 UTC ⇒ **76 901 Zeilen auf 510 distinkte Minuten**
  (~140/min), alle `tick_count=1`, `open==high==low==close`.
- PK `(epic, resolution, ts_utc, source)` kollidiert wegen der ms nie ⇒ keine DB-seitige Dedup.
- **Der Test pinnt den Bug:** `phase13_live_data/tests/test_stream.py:255-257`
  `test_iso_utc_minute_truncates_to_minute` erwartet `"2026-08-19T09:00:00.123Z"`.
- **Blast-Radius heute = 0 Konsumenten:** `heartbeat.py:175`, `heartbeat.py:338`, `rescue.py:343`
  lesen alle `sources=("yf",)`. Kein Produktionspfad liest `source='ls'`. K4 bleibt gültig.

### 1.4 Mess-Defekte

- **F7 / K6:** 09-16 → 301 225 Tokens, `exhausted_at` 15:22:04 UTC, 113 Calls · 09-17 → 302 892
  Tokens, 14:45:36 UTC, 121 Calls. Schwelle: `< 300 000` vor 17:30 Berlin. Trigger T-8 nie gezogen.
- **F8:** `autonomy_2026-09-21.json` (null Prozesse) meldet **K1 ✅ K5 ✅ K6 ✅ K7 ✅**, nur K2/K4 ❌.
- **Drift #9** (K4-Threshold-String gegen Sub-Window) und **Drift #11** (Report-Dateiname aus
  `args.day or args.from_day`, `autonomy_report.py:992`) sind **Fenster-Query-Artefakte**;
  `--day` ist davon nicht betroffen (heute verifiziert, 6 Reports ohne Overwrite geschrieben).
- **Drift #10 teil-entwarnt:** K2 meldet an 09-14…09-18 **PASS**; der 09-15-FAIL war eine
  Fenster-Query.
- **F6 (inferiert, nicht am Writer verifiziert):** `run_webui.log` zeigt 5 JSON-Parse-Fehler auf
  `llm_usage.json` mit Folge „counting 0 today"; die Datei parst im Ruhezustand sauber (4 039
  Einträge). Verdacht: Leser trifft unvollständigen Schreibvorgang ⇒ K6 kann still 0 zählen.

### 1.5 Autostart — was auf dieser Maschine schon existiert

`~/.config/systemd/user/` trägt **`claude-rc.service`**, **`opencode.service`**, `sunshine.service`;
`loginctl show-user trading-bot` meldet **`Linger=yes`** (User-Units starten ohne Login beim Boot).
Muster (opencode): `After=network.target` · `Restart=on-failure` · `RestartSec=5` ·
`WantedBy=default.target`. **Genau dieses Muster wird für den Bot wiederverwendet** — keine
Erfindung, keine root-Units.

## §2 Gelockte Entscheidungen (Nikinger 2026-09-21)

| # | Entscheidung |
|---|---|
| **R-L1** | **Fixen, dann 10 Tage neu starten.** Kein Weiterlaufen auf dem kaputten Substrat; Uhr auf Tag 1. |
| **R-L2** | **Cross-Phase-Freigabe P13 erteilt** (`live_data/stream.py` + `phase13_live_data/tests/`). Ein **eigener Teilplan nach den 10 Tagen** bleibt vorbehalten. |
| **R-L3** | **Autostart bauen** — „Claude und OpenCode sind auch schon autostart, warum der trading bot nicht auch". |
| **R-L4** | **Archivieren statt löschen** — Log und Tick-Zeilen werden verschoben, nicht gelöscht. „Groß, aber Speicherplatz ist billig." |
| **R-L5** | **Kein Closeout jetzt.** Block I bleibt liegen, bis der neue Lauf durch ist. |
| **R-L6** | Bestehende Freigaben gelten weiter: P1/2/3/4/5/7/8/9/15 (Plan §4) + P12 + P14 (Session #31) + **P13 neu**. |

## §3 Schritt-Sequenz

### R0 — Haushalt (vor allem anderen)

**R0.1** Σ-Baseline: **am 2026-09-21 gemessen = 1948** (16 Suites einzeln, nicht übernommen —
97+82+105+161+190+76+169+259+95+165+149+82+61+126+10+121). Vor dem ersten Fix **einmal
nachmessen**, falls zwischen Plan und Ausführung Commits dazukommen.
**R0.2** `git status` sauber (außer `data/` + `sunshine*.deb`), Session-#32-Commits gepusht.
**R0.3** Backup der Live-DBs **vor** R4: `cp data/bars.sqlite data/bars.sqlite.bak-20260921-pre-archive`
(973 MB, 14 G frei). `data/trading_bot.sqlite` wird in dieser Subphase **nicht** angefasst.

### R1 — Drift #12 (P8, freigegeben)

**R1.1** In `wiring.py` einen **modul-ebenen Builder** einführen (macht den Defekt testbar):
```python
def _ls_health_sink(observability_path: str) -> Callable[[dict[str, Any]], None]:
    """Health-Sink für den LS-Tick-Recorder. Eigener Builder, damit der Import
    (der in wiring.py per Konvention lokal passiert) testbar an einer Stelle steht."""
    from scheduler.observability import record_event
    def _sink(event: dict[str, Any]) -> None:
        record_event(observability_path, event)
    return _sink
```
**R1.2** Z. 1240 auf `health_sink=_ls_health_sink(config.observability_path)` umstellen.
**R1.3** Test `phase8_scheduler/tests/test_wiring_ls_health_sink.py` im Muster von
`test_wiring_reward_sink.py`: Sink bauen, ein Event durchschicken, prüfen dass die Zeile in einer
`tmp_path`-Datei landet — und dass **kein** `NameError` fliegt.

**Warum nicht einfach den Import oben in die Funktion ziehen?** Weil der Defekt dann wieder in
einer genesteten Closure säße, die kein Test erreicht (`_build_recorder` liegt in
`build_scheduler`, Z. 808, das ohne Broker/DB nicht aufrufbar ist). Der Builder ist die kleinste
Änderung, die den Fehler **strukturell** testbar macht — dieselbe Lehre wie
`test_wiring_reward_sink.py` (dessen Datei-Docstring genau diesen Fehlermodus beschreibt).

### R2 — Drift #13 (P13, neu freigegeben)

**R2.1** `stream.py:38-44` `_iso_utc_minute`: Millisekunde **konstant** `.000Z`.
**R2.2** `test_stream.py:255-257` mit-korrigieren (der Test pinnt heute den Bug) — Erwartung
`"2026-08-19T09:00:00.000Z"`, Docstring-Zeile „warum" dazu.
**R2.3** Neuer Test: zwei Ticks in **derselben** Minute ⇒ **eine** Bar mit `tick_count=2`,
`open`/`close` = erster/letzter Tick (der Regressionspin für den Rollover).
**R2.4** Neuer Test: Tick in Minute N+1 schließt Minute N ⇒ genau **eine** Bar mit `ts_utc`
auf `:00.000Z`.
**R2.5** `stream.py:514-520` (der `except Exception`-Zweig in `_write_candle`): Log-Text trennen —
Archiv-Fehler bleibt „insert_bars failed", Sink-Fehler wird eigener `logger.error`
(„health sink failed … — bar was written"). Test: Sink wirft ⇒ Bar ist trotzdem im Archiv **und**
die Log-Meldung nennt den Sink.

**Warum R2.5 mit in denselben Block?** Weil genau diese falsche Meldung Drift #12 zehn Tage lang
als Archiv-Problem getarnt hat. Der Fix ohne die Meldung wäre die Reparatur des Symptoms ohne die
Reparatur der Diagnose.

### R3 — Report-Tool (Phase-16-eigener Code)

**R3.1 Drift #11:** Dateiname aus dem **tatsächlichen Fenster** — `--day X` → `autonomy_X.json`
(unverändert), `--from X --to Y` → `autonomy_X_to_Y.json`. Kein Overwrite eines Tagesreports mehr.
**R3.2 Drift #9:** K4-Threshold-String und -Verdikt **immer gegen das volle Test-Fenster**
(`≥ 8 of 10`), nie gegen ein Sub-Window; bei Teil-Fenstern Verdikt `PARTIAL` statt `FAIL`.
**R3.3 F8 — Liveness:** neues Kriterium **K8 „Dienste liefen an diesem Handelstag"** (≥ 1
Scheduler-Zyklus **und** ≥ 1 Bar **und** ≥ 1 Heartbeat am Tag). Es ist ein **PASS-Kriterium** der
Neu-Vorregistrierung (R7), nicht nur Telemetrie.
**R3.4** Tests je Punkt in `phase16_activation/tests/test_autonomy_report.py` (+3 … +5).

> **Achtung Prereg-Disziplin (Plan §6 E2):** R3.2 und R3.3 ändern die Mess-Semantik. Sie sind
> deshalb **Teil von Prereg v3** (R7) und gelten erst für den neuen Lauf — nicht rückwirkend für
> die 8 gemessenen Tage.

### R4 — Archivierung (R-L4: verschieben, nicht löschen)

**R4.1** Log: `gzip -c data/state/run_scheduler.log > data/archive/run_scheduler.log.2026-09-21.pre-drift12-fix.gz`,
danach `: > data/state/run_scheduler.log` (truncate, kein Löschen). Erwartung: die Tracebacks sind
hochgradig repetitiv, der gzip liegt bei wenigen Prozent von 2,37 GB — **gemessen wird es, nicht
geschätzt**; wenn der gzip < 50 MB bleibt, wandert er zusätzlich als Beleg in den Session-Block.
**R4.2** Tick-Zeilen: neue Datei `data/archive/bars_ls_tickagg_2026-09-21.sqlite`,
`ATTACH` + `INSERT INTO archive.bars SELECT * FROM main.bars WHERE source='ls'`, Count-Abgleich
(**4 055 221**, exakt), erst **danach** `DELETE FROM bars WHERE source='ls'` + `VACUUM`.
**R4.3** Beleg im Session-Block: Zeilenzahl vorher/nachher je Quelle, Dateigrößen, `PRAGMA
integrity_check` auf beiden DBs.
**R4.4** Nach R2: die erste neue `ls`-Bar muss auf `:00.000Z` enden — Stichprobe in den
Session-Block.

> **Reihenfolge ist Pflicht:** R4 läuft **nach** R1/R2 und **vor** R7 (Neustart). Sonst schreibt
> der alte Code während der Archivierung weiter Tick-Zeilen in die Tabelle, die gerade kopiert wird.

### R5 — Autostart (R-L3)

**R5.1** Vier **getrackte** Unit-Dateien in `phase16_activation/systemd/`:
`tradingbot-scheduler.service`, `-recorder.service`, `-discovery.service`, `-webui.service`.
Jede nach dem **vorhandenen** Muster (`~/.config/systemd/user/opencode.service`):
```ini
[Unit]
Description=Trading-Bot Scheduler (Phase 8)
After=network-online.target
[Service]
WorkingDirectory=/home/trading-bot/trading-bot
ExecStart=/home/trading-bot/trading-bot/phase8_scheduler/scripts/run_scheduler.sh
Restart=on-failure
RestartSec=30
SuccessExitStatus=143
[Install]
WantedBy=default.target
```
**R5.2** Installer `scripts/install_units.sh` (Muster: `scripts/install_hooks.sh`, getrackt,
idempotent): kopiert die vier Units nach `~/.config/systemd/user/`, `systemctl --user
daemon-reload`, `enable` (kein `start` — der Start gehört zu R7).
**R5.3** Die Wrapper laufen im Vordergrund (`restart-services.sh` backgroundet sie selbst mit
`nohup … &`) ⇒ `Type=simple` ist korrekt, kein `forking`. **Bei Ausführung verifizieren (V-3).**
**R5.4** `scripts/restart-services.sh` bleibt **unverändert** (manueller Pfad, Doppelstart-Schutz
per `pgrep`). In `PHASE16_E3_RUNBOOK_v4.md` (R7) wird dokumentiert: **systemctl ist ab jetzt der
Normalweg**, `restart-services.sh` der manuelle Notweg.
**R5.5** `RestartSec=30` + `StartLimitIntervalSec=300` / `StartLimitBurst=3`, damit ein flappender
Dienst K1 (`≤ 2 Starts/Tag`) nicht sprengt, sondern stehen bleibt und auffällt.

> **Warum User-Units und nicht root?** Weil `Linger=yes` bereits gesetzt ist und Claude/OpenCode
> genau so laufen — gleiche Rechte, gleicher Keyring-Zugang (die Credentials liegen im
> Secret Service des Users; eine root-Unit käme nicht an sie heran).

### R6 — K6-Analyse (F7)

**R6.1** Aus `data/state/llm_usage.json` je Tag aufschlüsseln: Tokens pro Stage
(Research / Bull / Bear / Judge / Lesson / Council) und pro Modell.
**R6.2** Befund + **drei Optionen** in den Session-Block: (a) Cap anheben, (b) Call-Zahl senken
(113–121/Tag), (c) K6-Schwelle in v3 neu setzen. **Entscheidung trifft der Nikinger** — sie ist
Teil der Vorregistrierung, nicht des Codes.
**R6.3** F6 (`llm_usage.json`-Leserace) dabei mitprüfen: schreibt der Writer atomar
(`tmp` + `os.replace`) oder in-place? Wenn in-place: kleiner Fix im selben Muster wie
`_write_pid` (`run.py:49-53`). **Nur wenn der Writer in Phase 16 / P8 liegt.**

### R7 — Prereg v3 + Neustart

**R7.1** `PHASE16_AUTONOMY_PREREGISTRATION_v3.md` **neu** (v2 bleibt byte-identisch, wie v1 es
vorschreibt): Tag 1 = erster voller Handelstag nach dem Neustart, Tag 10 = Tag 1 + 9 Handelstage,
beide Daten **eingetragen**; K1–K7 unverändert übernommen **plus K8 (Liveness, R3.3)**;
K4-Semantik „≥ 8 von 10 **des vollen Fensters**" (R3.2); K6-Schwelle gemäß R6-Entscheidung;
Watch-Items W1–W5 + neu **W6 „`ls`-Bars enden auf `:00.000Z`"** und **W7 „`run_scheduler.log`
< 200 MB"**.
**R7.2** `PHASE16_E3_RUNBOOK_v4.md` neu (v3 ist locked): Restart-Sequenz über `systemctl --user`,
Tagesroutine G1/G2/G5 mit den korrigierten Kommandos (G5 mit Fenster ab letzter Startzeile).
**R7.3** Commit **vor** der ersten Startzeile des neuen Laufs (Muster AK-J5: `git log` vs.
Log-Zeitstempel).
**R7.4** Start durch den **Nikinger** (Operator-Aktion): `systemctl --user start tradingbot-*`,
danach Tag-1-Verify wie Session #27.
**R7.5** Phasenkopf + Memory aktualisieren; **kein Closeout** (R-L5).

## §4 Testliste (neu)

| Datei | Test | Deckt |
|---|---|---|
| `phase8_scheduler/tests/test_wiring_ls_health_sink.py` | `test_ls_health_sink_records_event` | R1 / Drift #12 |
| `phase8_scheduler/tests/test_wiring_ls_health_sink.py` | `test_ls_health_sink_does_not_raise_nameerror` | R1 (Regressionspin) |
| `phase13_live_data/tests/test_stream.py` | `test_iso_utc_minute_truncates_to_minute` (**korrigiert**) | R2.2 |
| `phase13_live_data/tests/test_stream.py` | `test_two_ticks_same_minute_yield_one_bar` | R2.3 |
| `phase13_live_data/tests/test_stream.py` | `test_minute_rollover_emits_bar_on_minute_boundary` | R2.4 |
| `phase13_live_data/tests/test_stream.py` | `test_health_sink_failure_keeps_bar_and_logs_sink` | R2.5 |
| `phase16_activation/tests/test_autonomy_report.py` | `test_window_report_filename_uses_window` | R3.1 / Drift #11 |
| `phase16_activation/tests/test_autonomy_report.py` | `test_k4_threshold_is_full_window` | R3.2 / Drift #9 |
| `phase16_activation/tests/test_autonomy_report.py` | `test_k4_partial_window_is_partial_not_fail` | R3.2 |
| `phase16_activation/tests/test_autonomy_report.py` | `test_k8_liveness_fails_on_dead_day` | R3.3 / F8 |
| `phase16_activation/tests/test_autonomy_report.py` | `test_k8_liveness_passes_on_live_day` | R3.3 |

**Σ-Erwartung:** 1948 (gemessen 2026-09-21) **+11** ⇒ **1959**.

## §5 Akzeptanzkriterien

| AK | Kriterium | Beleg |
|---|---|---|
| **AK-R1** | 0 `NameError` im neuen `run_scheduler.log` nach 1 Handelstag | `grep -c` |
| **AK-R2** | Jede neue `bars.source='ls'`-Zeile endet auf `:00.000Z`; ≤ 1 Zeile je (Epic, Minute) | SQL, `mode=ro` |
| **AK-R3** | `tick_count > 1` kommt in den neuen `ls`-Bars vor (Beweis, dass aggregiert wird) | SQL |
| **AK-R4** | Archiv-DB trägt exakt 4 055 221 Zeilen, Live-DB `source='ls'` = 0 vor dem Neustart | SQL beide Seiten |
| **AK-R5** | gzip des alten Logs existiert, Live-Log truncated (< 1 MB beim Start) | `ls -la` |
| **AK-R6** | Nach einem echten Reboot laufen alle vier Dienste ohne Handgriff | `systemctl --user status` + `ps` |
| **AK-R7** | K8 meldet an einem Tag ohne Zyklen FAIL | Report eines toten Tages (Regression) |
| **AK-R8** | Prereg v3 committet **vor** der ersten Startzeile des neuen Laufs | `git log` vs. Log-Zeitstempel |
| **AK-Σ** | Σ = Baseline + 11, alle Suites grün | Suite-Sweep |

## §6 Bei Ausführung verifizieren

| # | Punkt | Warum offen |
|---|---|---|
| **V-1** | Ob `TickAggregator` außer `on_tick` noch einen Pfad hat, der `_iso_utc_minute` mit anderer Erwartung nutzt (`close_minute` nimmt den String als Argument). | Nur die beiden Aufrufer gegrept, `close_minute`-Aufrufer im Produktionscode nicht vollständig zurückverfolgt. |
| **V-2** | Ob außer `test_stream.py:255` noch ein Test die ms-Form erwartet. | `grep "00\.[0-9]\{3\}Z"` lief nur über `phase13_live_data/tests/`. |
| **V-3** | Ob die vier Wrapper wirklich im Vordergrund bleiben (`Type=simple`) — `run_webui.sh` startet `uvicorn`, `run_scheduler.sh` ein `python -m`. | Aus `restart-services.sh` geschlossen (`nohup … &`), nicht je Wrapper gelesen. |
| **V-4** | Ob `_build_recorder` außer dem Health-Sink weitere freie Namen nutzt, die nur durch Zufall gebunden sind. | Nur die Lambda gelesen, nicht die ganze Closure. |
| **V-5** | Ob der `llm_usage.json`-Writer in P8 liegt (dann F6-Fix in-scope) oder in P4/P6 (dann eigene Freigabe). | Writer nicht lokalisiert. |
| **V-6** | Ob `VACUUM` auf der 973-MB-DB genug temporären Platz hat (braucht ~Dateigröße). | 14 G frei gemessen, VACUUM nicht ausgeführt. |
| **V-7** | Ob `enable` allein reicht oder `systemctl --user enable --now` gebraucht wird, damit `Linger` greift. | `Linger=yes` gemessen, Boot-Verhalten nicht getestet. |

## §7 Fehlgriffe (Symptom → erster Verdächtiger)

| Symptom | Erster Verdächtiger |
|---|---|
| Nach R2 weiterhin ms in `ts_utc` | ein zweiter Formatter — `_serialize` gibt `buf.minute_start_utc` **durch**, der Wert entsteht allein in `_iso_utc_minute` |
| `ls`-Bars fehlen nach dem Neustart ganz | nicht R2, sondern der LS-Subscribe-Pfad (`CHART:` ist auf diesem Account NO, L6-Fallback muss greifen) |
| Units starten beim Boot nicht | `Linger` ok, aber `WantedBy=default.target` fehlt oder `daemon-reload` vergessen |
| K1 meldet plötzlich > 2 Starts | `Restart=on-failure` flappt — `StartLimitBurst` prüfen, **nicht** K1 anpassen |
| VACUUM bricht ab | Platz (V-6) oder ein offener Reader — alle Dienste müssen zu diesem Zeitpunkt stehen |

## §8 Operator-Aktionen (Nikinger, nicht Exec-Session)

1. **Push** der Session-#32-Commits (5) und der R-Commits.
2. **Reboot-Test** nach R5 (AK-R6) — der einzige ehrliche Beweis für den Autostart.
3. **Start des neuen Laufs** (R7.4) und Tag-1-Verify.
4. **K6-Entscheidung** (R6.2).
5. **Tagesroutine G1/G2/G5** ab Tag 1 — die F7-Lehre: der Befund lag 5 Tage ungelesen in den Rohdaten.

## §9 Out-of-Scope (bleibt liegen)

- **Block I / Closeout** — R-L5, kommt nach dem neuen Lauf.
- **Phase-17-Material:** Strategie-Befund K3 (0 Trades), Universums-Konsolidierung W2,
  Zombie-Reaping W5, IG-Punkte für verified SUN*-Epics (V-5 aus dem F-Plan).
- **Promotion-Bridge / Gate P7-A6** — unverändert delegiert.
- **Der nach den 10 Tagen vorbehaltene P13-Teilplan** (R-L2).

## §10 Commit-Konvention

`<scope>: <imperative>` je logischer Änderung, eine Phase je Commit:
`phase8: code -- …` · `phase13: code|tests -- …` · `phase16: code|tests|docs -- …` ·
`scripts: …` für den Unit-Installer. Kein Sammel-Commit über Phasengrenzen.
