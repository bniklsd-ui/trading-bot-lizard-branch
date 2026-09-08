---
status: plan (ausführungsreif)
purpose: Exec-Plan der Phase-16-F-Subphase — Block J (Live-Reparatur des 2-Wochen-Tests, 3 selbst gemessene Struktur-Defekte) + Block H (Audit-Restbefunde, revidierte Mechanik) + Block G (Tagesroutine) + Block I (Tag-10-Closeout). Direkt an Sonnet 5 übergebbar; Anker verbatim, Entscheidungen gelockt.
read-when: Ausführung der Phase-16-F-Subphase; VOR jedem Edit an autonomy_report.py, archive.py, heartbeat.py oder an einer Header-Card
detail: L2
up: ./CLAUDE.md
down:
  - ./PHASE16_PARTIAL_CLOSEOUT.md                 # 📕 Vorgänger-Snapshot (Blöcke G/H/I), §4-H-Mechanik hier superseded
  - ./PHASE16_AUTONOMY_PREREGISTRATION.md         # 📕 v1, unangetastet — J5 schreibt v2 daneben
  - ./PHASE16_E3_RUNBOOK_v2.md                    # 📕 Operator-Runbook (Restart-Sequenz für J6)
  - ../docs/concepts/phase16_activation_plan.md   # 📕 Vollplan Phase 16 (P1–P17, Blöcke A–E)
  - ./SESSIONS_ARCHIVE.md                         # 📦 Session-Historie (newest-first)
updated: 2026-09-08
---

# Phase 16 F — Exec-Plan (Block J / H / G / I)

> **Planungssession 2026-09-08 (Opus 5, Claude Code).** Jede Zahl unten ist an diesem Tag
> selbst gegen Code, Live-DB (`mode=ro`) und laufende Prozesse gemessen — nicht aus einem
> Vorgänger-Handover übernommen. Was **nicht** gemessen werden konnte, steht vollständig
> in §6 („bei Ausführung verifizieren"). Was dort nicht steht, gilt als geprüft.

## §0 BLUF

- **Der laufende 2-Wochen-Autonomie-Test kann strukturell kein PASS erreichen.** Drei
  Defekte, alle heute gemessen: **K1** zählt jeden Scheduler-Start seit 2026-08-31 (kein
  Fenster-Filter im Code) → 7 statt 1; **K4** ist seit 2026-08-24 an **10 Tagen in Folge**
  `ok=False`, weil `assess_day` die Bar-Dichte gegen ein 24-h-Fenster prüft und die
  Overnight-Lücke (≈930 min) die 5-Minuten-Gap-Schwelle immer reißt; **der LS-Bar-Stream
  schreibt nichts** — 63 942 `sqlite3.ProgrammingError` allein heute, 0 Zeilen
  `bars.source='ls'` seit es die Tabelle gibt.
- **Nikinger-Entscheidung 2026-09-08 (Variante A):** Bot stoppen, alle drei Defekte fixen,
  `run_scheduler.log` truncaten, `PHASE16_AUTONOMY_PREREGISTRATION_v2.md` als datiertes
  supersedendes Dokument schreiben, Uhr auf Tag 1 zurücksetzen. Das ist **Block J** und hat
  Vorrang vor allem anderen.
- **Cross-Phase-Freigabe P12 erteilt** (Nikinger 2026-09-08) für `data_foundation/archive.py`
  + `data_foundation/heartbeat.py`.
- **Lock F3 revidiert** (Nikinger 2026-09-08): kein neues Hook-Skript — Step 4 wandert in
  `scripts/check_doc_rotation.py`.
- **Σ-Regression-Baseline vor dem ersten Fix: 1934 grün** (16 Suites einzeln gemessen
  2026-09-08, Aufschlüsselung §1.1). Mit `meta_m1_harness` 1962.
- Reihenfolge: **Step 0** (Haushalt) → **J** (Live-Reparatur) → **H** (Doku) → **G**
  (Tagesroutine, läuft dann 10 Tage) → **I** (Closeout).

## §1 Selbst gemessene Fakten (2026-09-08)

### 1.1 Σ-Regression-Baseline (vor dem ersten Fix)

Jede Suite einzeln gelaufen (`phase1_broker_wrapper/.venv/bin/python -m pytest <dir>/tests -q
-p no:cacheprovider`), weil `tests.conftest` sonst kollidiert:

| Suite | grün | Suite | grün |
|---|---|---|---|
| phase1_broker_wrapper | 97 | phase10_v3 | 165 |
| phase2_persistence | 82 | phase12_data_foundation | 145 |
| phase3_external_data | 105 | phase13_live_data | 82 |
| phase4_research | 162 | phase14_discovery | 61 |
| phase5_execution | 190 | phase15_v4 | 126 |
| phase6_debate | 76 | phase16_activation | 5 |
| phase7_reward | 169 | root `tests/` | 115 |
| phase8_scheduler | 259 | **Σ ohne M1** | **1934** |
| phase9_universe | 95 | `meta_m1_harness` | 28 (Σ mit M1 = 1962) |

0 Failures, 0 Errors. Deckt sich Zeile für Zeile mit der Tabelle in
`PHASE16_PARTIAL_CLOSEOUT.md` §1.2 — die Behauptung dort ist bestätigt, nicht übernommen.

### 1.2 Live-Stand (2026-09-08, 10:48 CEST)

| Fakt | Wert | Quelle |
|---|---|---|
| Scheduler | PID 281715, hoch seit 2026-09-08 09:30:48 | `ps -eo pid,lstart,cmd` |
| Recorder | PID 268859 (`python -m data_foundation.run`), seit 2026-09-07 22:24:20 | dito |
| Discovery | PID 268871 (`python -m source_registry.run`), seit 2026-09-07 22:24:22 | dito |
| WebUI | PID 268921 (uvicorn `webui.api:app`), seit 2026-09-07 22:24:26 | dito |
| Zombies | 2 × `[python] <defunct>` (PID 281722, 281723), Kinder des Schedulers, seit 09:30:48 | dito — deckt Prereg-Watch-Item **W5** |
| Live-DB-Schema | **v9** (`_schema_version` letzte Zeile = 9) | `data/trading_bot.sqlite`, `mode=ro` |
| `source_spend WHERE kind='rescue'` | **0 Zeilen** | `data/bars.sqlite`, `mode=ro` |
| Trades heute | 0; letzter CLOSED-Trade 2026-08-27 (`trade_outcomes.id=11`) | dito |
| Abstains heute | 14, alle `reason_no_candidates`, Stage `research_empty` | dito |
| Paper-Trades heute | 48 created, 0 resolved (letzte Resolution 2026-08-31T07:05Z) | dito |
| Token heute | 36 126 / 300 000, 15 Calls, `exhausted_at=null` | `data/state/llm_usage.json` |
| `bars` nach Quelle | `capital` 962 · `ig` 2890 · `yf` 37 540 · **`ls` 0** | `data/bars.sqlite`, `mode=ro` |

**Zwei Closeout-Offenposten sind damit erledigt:** Operator-Aktion #7 (Ledger-Restore 250
Punkte) — es gibt keine `kind='rescue'`-Zeile mehr; Phase-16-B1/B2 (Migration 008+009) —
Schema steht auf v9. Beides in §8 als „erledigt" geführt, nicht mehr als Aktion.

### 1.3 Die drei Struktur-Defekte (Block-J-Auslöser)

**J-D1 — LS-Bar-Stream schreibt nichts (Thread-Affinität).**
`phase12_data_foundation/data_foundation/archive.py:77` öffnet die Verbindung mit dem
sqlite3-Default `check_same_thread=True`:

```
        self.conn = sqlite3.connect(self.db_path)
```

`phase13_live_data/live_data/stream.py:498` (`_write_candle`) ruft `insert_bars` aus dem
Lightstreamer-Listener-Thread. Jede geschlossene Kerze endet in
`sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same
thread`. Gemessen: **63 942** Vorkommen in `data/state/run_scheduler.log`, erstes um
2026-09-08 09:35:25,745 (= 4½ min nach Restart #4, dem ersten Lauf mit `enable_bar_stream`
default ON). `bars.source='ls'` hat **nie** eine Zeile bekommen.
Nebenwirkung: das Log wächst dadurch um ≈25 MB/h (43 MB heute, `df` zeigt 17 GB frei).

**J-D2 — K1 misst ohne Fenster.**
`phase16_activation/scripts/autonomy_report.py:542` deklariert
`def evaluate_k1(state_dir, *, from_ts=None, to_ts=None)`. **Beide** Aufrufer übergeben
nichts:

```
    report.criteria["1"] = evaluate_k1(state_dir)
```
— `:870` in `_build_day_report`, `:919` in `_build_summary_report`. `count_starts_in_window`
(`:189`) filtert nur, wenn `from_ts`/`to_ts` gesetzt sind; sonst zählt es die ganze Datei.
`run_scheduler.log` beginnt am 2026-08-31 07:54:52 und trägt 7 Start-Zeilen — **heute** gibt
es genau eine (`grep "starting scheduler daemon" | grep 2026-09-08` → 1 Treffer, 09:30:49).
Gemessen mit `--summary --from 2026-09-08 --to 2026-09-08`: `scheduler.starts = 7` → K1 FAIL,
und zwar für jeden Tag des Laufs.
Zweitbefund derselben Funktion: `_START_PATTERNS["webui"]` (`:143`) matcht **zwei** Muster
(`[run_webui] dashboard on` **und** `Started server process`), zählt einen WebUI-Start also
doppelt → 2 von 2 erlaubten Starts sind nach einem einzigen Start verbraucht.

**J-D3 — K4 ist per Konstruktion unerreichbar.**
`phase12_data_foundation/data_foundation/heartbeat.py:73` holt das Fenster aus
`_day_bounds_iso` (`:36-40`) — das ist **00:00 → 24:00 UTC**. Die Coverage-Schleife
(`:118-125`) prüft darin die yF-1-Minuten-Bars:

```
            if verdict.largest_gap_min > 5:  # MAX_WINDOW_GAP_MIN — same threshold as A1
```
Ein normaler Handelstag liefert ≈8,5 h Bars in einem 24-h-Fenster; die Nacht ist eine
zusammenhängende Lücke von ≈930 min ≫ 5 min → `epics_below_threshold` ist immer nicht-leer
→ `ok = False` (`:151`). Gemessen über alle `measurement_heartbeat`-Events in
`data/state/research_health.jsonl`: **2026-08-24 bis 2026-09-04 durchgehend `ok=False`**,
`worst_coverage` konstant 0,32–0,34 (= 510 min / 1440 min). Der einzige `ok=True` stammt vom
2026-08-17, als `worst_coverage=0` und noch kein Epic messbar war.
**Wichtig:** `worst_coverage` ist reine Telemetrie — es gattert nichts. Wer `MIN_WINDOW_RATIO`
anfasst, ändert nichts. Der Schalter ist `largest_gap_min`.
**Zweiter, unabhängiger `ok=False`-Pfad** in derselben Funktion (`:142-145`):
`if shadow_enabled and pairs_resolved == 0 and pairs_typed_expired == 0`. Heute: 48 Paper-
Trades created, 0 resolved. Ob dieser Zweig zusätzlich feuert, entscheidet sich erst im
POST_WINDOW nach 17:30 — steht in §6 als V-4.

### 1.4 Korrekturen an `PHASE16_PARTIAL_CLOSEOUT.md` (📕, wird **nicht** editiert)

Der Partial Closeout ist ein datierter Snapshot. Diese Zeilen sind gegen den Code/Live-Stand
falsch; die Korrektur lebt hier, das Original bleibt als Audit-Stand stehen.

| Closeout | Behauptung | Befund 2026-09-08 |
|---|---|---|
| §1.3 | „`run_scheduler.log` endet mit `INFO scheduler.run: starting scheduler daemon …` **ohne Traceback**" | Falsch. Endet mit `sqlite3.ProgrammingError` (J-D1), 63 942 Vorkommen. |
| §1.3 | „K7-Caps-Pin … **verbatim in Startzeile**" | Richtig — aber **in der Log-Startzeile**, nicht in `/proc/<pid>/cmdline`. `cat /proc/281715/cmdline` liefert nur `python -m scheduler.run`. Das G2-Kommando im Closeout kann so nie funktionieren; korrigiert in G2 unten. |
| §4 H-3 Pattern B | „`sed 's\|^\./CLAUDE\.md\|../CLAUDE.md\|g'`" | Erzeugt `docs/CLAUDE.md` — **existiert nicht**. Ziel ist pro Datei verschieden, Tabelle in H-3. |
| §2.1 | „15× Pattern A, 4 Dateien" | 21 `../../`-Links in **5** Dateien; `phase14_discovery/PHASE14_B1A_PROBE_OUTPUT_2026-08-22.md` (2 Links) fehlt in der Closeout-Liste. |
| §2.1 | 29 Befunde gesamt | Eigener Scan: 28 fehlende Ziele + 1 Prosa-Liste = 29 echte Befunde + 1 bewusster Nicht-Pfad (`docs/INDEX.md:7 down: every project doc (that is the point)`) — der darf **nicht** anschlagen. |
| §6 Aktion #7 | Ledger-Restore 250 Punkte „Status bisher unklar" | Erledigt: 0 Zeilen `kind='rescue'`. |
| §6 Aktion #8 | Backup-SQL für 3 SUN*-Epics „Status prüfen" | Das Runbook-v2-SQL (`WHERE … AND status='active'`) war ein **No-Op**: alle 5 SUN*-Epics stehen auf `status='verified'`, keiner auf `active`. Prereg-Bedingung („keine `IX.D.SUN*` in `active`") ist damit erfüllt — aber zufällig. 3 SUN*-Epics haben heute trotzdem je 5 IG-Punkte gezogen (`source_spend`, `kind='research'`, 07:34 UTC). Watch-Item, kein Blocker. |

## §2 Gelockte Entscheidungen

| ID | Entscheidung | Begründung (warum sie nicht wieder aufgemacht wird) |
|---|---|---|
| **J1** | Der laufende Test wird **abgebrochen**, nicht zu Ende gelaufen. | Drei von sieben Kriterien sind heute schon unerreichbar (§1.3). Neun weitere Tage produzieren einen vorhersagbaren FAIL-Report und kosten neun Tage. Nikinger 2026-09-08, Variante A. |
| **J2** | Der Thread-Fix sitzt in `BarArchive.__init__` (**ein** Punkt), nicht in `insert_bars`. | Alle 14 `self.conn`-Stellen (§3 J1) sind betroffen, nicht nur der Insert. Ein Guard nur um `insert_bars` lässt `window()`/`latest_ts()` denselben Fehler aus einem anderen Thread werfen — und der liest sich dann wie ein **neuer** Bug. Root Cause statt Symptom. |
| **J3** | `check_same_thread=False` **plus** `threading.Lock` um jede Nutzung. | `check_same_thread=False` allein erlaubt zwei Threads gleichzeitig auf einem Cursor — das tauscht `ProgrammingError` gegen sporadische Korruption. Der Lock ist 3 Zeilen und macht die Klasse threadsicher, nicht nur thread-tolerant. |
| **J4** | K1-Fix = Fenster an `evaluate_k1` durchreichen (2 Zeilen), **nicht** Schwelle anheben. | Die Prereg formuliert das Kriterium bereits als „≤ 2 starts per service **in window**". Der Code implementiert das Fenster nicht. Wir reparieren das Instrument auf den vorregistrierten Wortlaut — die Schwelle bleibt unangetastet. |
| **J5** | K4-Fix = Coverage-Fenster auf die Handelssitzung (Berlin 09:00–17:30 via `zoneinfo`) **minus einer Recorder-Lag-Toleranz am rechten Rand**; Gap-Schwelle bleibt 5 min. | Die 5-Minuten-Schwelle ist die inhaltlich richtige Aussage („keine Lücke mitten im Fenster", Phase-13 F3). Falsch ist das Fenster, nicht die Schwelle. **Die Lag-Toleranz ist nicht optional:** `assess_window` (`coverage.py:94-105`, Kommentar „Ränder zählen mit") zählt die Lücke zwischen der letzten Bar und `end_dt` ausdrücklich mit. Der yF-Recorder hinkt nach — heute 2026-09-08 um 08:48 UTC war die jüngste Bar `08:30:00Z`, **18 min** Rückstand. Ein Fenster, das exakt auf 15:30 UTC endet, und ein Heartbeat, der um 15:30 UTC feuert, erzeugen garantiert eine Schwanz-Lücke > 5 min — dieselbe `ok=False`-Zeile, nur mit neuer Ursache. `zoneinfo` statt fester UTC-Offsets, weil der Lauf über den DST-Wechsel (2026-10-25) hinausreichen kann. |
| **J6** | Prereg-Korrektur als **neue Datei** `PHASE16_AUTONOMY_PREREGISTRATION_v2.md`; v1 bleibt Byte-identisch. | Die v1 schreibt sich das selbst vor („Korrekturen sind nur als neues, datiertes, supersedendes Dokument … möglich — nie als Edit an dieser Datei", Z. 20-23). Gleiche 📕-Disziplin wie beim Partial Closeout. |
| **J7** | `data/state/run_scheduler.log` wird **vor** dem Restart geleert (Backup-Kopie mit Datum daneben). | K1 zählt Start-Zeilen aus dieser Datei; ohne Truncate schleppt der neue Lauf die 7 Alt-Starts mit. Backup, weil das Log der einzige Beleg für die 63 942 J-D1-Fehler ist. |
| **J8** | Der WebUI-Doppelzähl-Bug (`_START_PATTERNS["webui"]`) wird **mitgefixt**. | Ein Start = zwei Treffer heißt: der erste erlaubte Restart reißt die Schwelle. Der Fix ist ein Muster-String und gehört in denselben Commit wie J4, sonst misst K1 weiter falsch. |
| **H1** | **F3 revidiert** — Header-Card-Link-Check wird **Step 4** in `scripts/check_doc_rotation.py`, kein neues Skript. | Nikinger 2026-09-08. Der Pre-Commit-Hook ruft bereits `--strict` auf; ein zweites Skript bräuchte eigene Tests, eine `install_hooks.sh`-Änderung und eine Hook-Neuinstallation — für dieselbe Prüfung. Docstring wird auf „Doc-Layers-Hygiene (Rotation + Header-Card-Links)" erweitert. |
| **H2** | Reihenfolge: **erst** Reparatur-Commit (H-3/H-4), **dann** Step-4-Commit. | Step 4 läuft ab Merge im `--strict`-Pfad des Pre-Commit-Hooks. Käme er zuerst, wäre jeder folgende Commit blockiert. Der „exit 1 vor / exit 0 nach"-Beweis wandert in den Commit-Body + einen Regressionstest. |
| **H3** | Pattern C = **Reference entfernen** (`phase15_v4/PHASE15_HOOK_HARDENING_PLAN.md:10`). | Nikinger 2026-09-08. Der Kommentar in derselben Zeile sagt es selbst: „(im Phasenkopf Sektionen, nicht diese Datei)". Eine Datei zu erfinden, um einen Link zu retten, ist die falsche Richtung. |
| **H4** | `docs/concepts/phase9_v2_foundation_plan(1).md` wird **nicht umbenannt**; der Link zeigt auf den echten Namen inkl. `(1)`. | Die Klammern stehen in ROADMAP, README, ARCHITECTURE, INDEX und zwei Phasen-Docs — ein Rename ist 10 Dateien für null Funktionsgewinn. Phase-17-Kandidat. |
| **F1** | Phase-16-F bleibt Subphase (kein Phase 17). | Unverändert aus `PHASE16_PARTIAL_CLOSEOUT.md` §3 F1, Nikinger-Auftrag 2026-09-08. |

## §3 Schritt-Sequenz

### Step 0 — Haushalt (vor allem anderen, ~10 min)

**0.1 Legacy-Namen-Ritual.** `grep -rn -i "turbo\|CALL/PUT\|pre_trade_option_check" --include="*.py" --include="*.md" .` (ohne `.agents/`, `.git/`, `*_ARCHIVE.md`).
**Ergebnis dieser Plan-Session (2026-09-08): No-Op.** 4 Treffer, alle bewusst eingefroren und
als solche dokumentiert — `ARCHITECTURE.md:76,134,212` (`turbo_candidates.json`, „frozen
legacy filename") und `README.md:28` („`turbo_*` = legacy"). Kein Python-Treffer. Die
Exec-Session wiederholt den Grep und protokolliert das Ergebnis im Session-Block, auch wenn
es wieder No-Op ist.

**0.2 Σ-Baseline.** Bereits genommen (§1.1, 1934). Die Exec-Session **wiederholt sie nicht**
— sie vergleicht am Ende jedes Blocks gegen 1934.

**0.3 Bot-Zustand feststellen.** `ps -eo pid,lstart,cmd | grep -E "scheduler.run|data_foundation.run|source_registry.run|uvicorn"`.
Die vier PIDs aus §1.2 notieren. **Parallel-Login-Falle:** ab hier läuft kein zweiter
IG-Prozess; jede Live-Berührung passiert seriell.

### Block J — Live-Reparatur (Vorrang, ein zusammenhängender Block außerhalb 09:00–17:30)

> **Wann:** Nach 17:30 Berlin oder vor 09:00. Der Restart (J6) soll morgens vor 09:00
> passieren, damit Tag 1 des neuen Laufs ein voller Handelstag ist.

**J0 — Bot stoppen (Operator-Aktion, Nikinger).**
Reihenfolge Scheduler → Recorder → Discovery → WebUI, `SIGTERM`, dann `ps` als Gegenprobe.
Der Kill-Pfad steht in `PHASE16_E3_RUNBOOK_v2.md` §3. **Gegenprobe:**
`ps aux | grep -E "scheduler.run|data_foundation.run|source_registry.run" | grep -v grep`
muss leer sein, bevor J1 editiert wird.

**J1 — `BarArchive` threadsicher machen** (Phase 12, Freigabe 2026-09-08).
Datei `phase12_data_foundation/data_foundation/archive.py`.

- Anker A (Z. 16), verbatim: `import sqlite3` → darunter `import threading` ergänzen
  (alphabetisch nach `sqlite3`: `import sqlite3` / `import threading`).
- Anker B (Z. 77-78), verbatim:
  ```
          self.conn = sqlite3.connect(self.db_path)
          self.conn.row_factory = sqlite3.Row
  ```
  → wird zu `sqlite3.connect(self.db_path, check_same_thread=False)` plus
  `self._lock = threading.Lock()` in derselben `__init__`.
- Anker C — **alle** Methoden, die `self.conn` benutzen, bekommen `with self._lock:` um ihren
  DB-Zugriff. Vollständige Liste der Methoden (Zeilen heutiger Stand, `grep -n "    def " archive.py`):
  `close` (80) · `ensure_schema` (83) · `insert_bars` (98) · `window` (137) ·
  `coverage_ratio` (194) · `latest_ts` (213) · `bars_written_since` (220).
  Die `self.conn`-Stellen darin: 77, 78, 81, 85-88, 91, 93, 94, 121, 132, 163, 170, 214,
  232, 238.
- **Kein** Verhaltenswechsel sonst: kein WAL, kein Timeout, keine Retry-Schleife. Der Lock
  serialisiert Schreiber im selben Prozess; `SourceBudget` mit eigener Verbindung auf
  dieselbe Datei bleibt wie bisher (Kommentar Z. 42).
- **Ordering-Annahme, die der Lock nicht abdeckt:** `close()` nimmt zwar den Lock, macht die
  Verbindung danach aber für jeden anderen Thread ungültig. Das ist heute unkritisch, weil
  Recorder und Scheduler nur beim Shutdown schließen. Wer später ein `close()` mitten im
  Lauf einbaut, braucht mehr als diesen Lock — Kommentar an `close()` schreiben, damit die
  Annahme sichtbar bleibt.
- Tests: `phase12_data_foundation/tests/test_archive.py` um **1** Test erweitern —
  `test_insert_bars_from_other_thread` (Bar aus einem `threading.Thread` schreiben, im
  Haupt-Thread über `window()` wieder lesen). Das ist der kleinste Check, der bricht, wenn
  jemand `check_same_thread` zurückdreht.
- Commit: `phase16+phase12: fix -- BarArchive threadsicher (check_same_thread=False + Lock), LS-Bar-Stream schrieb seit 2026-09-08 09:35 keine einzige Kerze (63942 ProgrammingError)`

**J2 — K1 misst im Fenster** (Phase 16, eigen).
Datei `phase16_activation/scripts/autonomy_report.py`.

- Anker A (Z. 870, in `_build_day_report`) und Anker B (Z. 919, in `_build_summary_report`),
  beide verbatim identisch:
  ```
      report.criteria["1"] = evaluate_k1(state_dir)
  ```
  → Fenster übergeben. Für den Tagesreport: Berlin-Tagesgrenzen von `day`. Für den Summary:
  Berlin-00:00 des `from_day` bis Berlin-24:00 des `to_day`. `_berlin_day` (Z. 230) ist die
  vorhandene Richtung; die Umkehrung (Tag → tz-aware Grenzen) ist neu und gehört als kleiner
  Helper direkt daneben.
- Anker C (Z. 143), verbatim:
  ```
      "webui":     re.compile(r"\[run_webui\] dashboard on|Started server process"),
  ```
  → nur noch `\[run_webui\] dashboard on` (J8). Das zweite Muster stammt von uvicorn selbst
  und feuert bei jedem Worker-Start.
- Tests: `phase16_activation/tests/test_autonomy_report.py` um **2** Tests erweitern —
  `test_k1_ignores_starts_before_window` (Log mit 3 Alt-Starts + 1 Start im Fenster ⇒ PASS)
  und `test_k1_webui_single_start_counts_once` (Log mit `dashboard on` **und**
  `Started server process` ⇒ 1).
- Commit: `phase16: fix -- K1 misst im Fenster (evaluate_k1 bekommt from_ts/to_ts) + WebUI-Start zaehlt einmal; zaehlte bisher alle 7 Scheduler-Starts seit 2026-08-31`

**J3 — Heartbeat-Coverage auf die Handelssitzung** (Phase 12, Freigabe 2026-09-08).
Datei `phase12_data_foundation/data_foundation/heartbeat.py`.

- Anker (Z. 73), verbatim:
  ```
      start, end = _day_bounds_iso(day_utc)
  ```
  bleibt für `bars_today` und die Paper-Trade-Zählungen (Z. 74, 78, 83, 88 — Tagesgrenzen
  sind dort richtig). **Neu** daneben: ein zweites Paar `cov_start, cov_end` für die
  Coverage-Schleife.
- Anker (Z. 118), verbatim:
  ```
                    epic, "1m", start, end, sources=("yf",),
  ```
  → `cov_start, cov_end`. Ebenso der `assess_window`-Aufruf zwei Zeilen darunter (Z. 121:
  `verdict = assess_window(timestamps, start, end, 1)`).
- Neuer Helper neben `_day_bounds_iso` (Z. 36):
  `_session_bounds_iso(day_utc) -> tuple[str, str]` — Berlin 09:00 und 17:30 des Tages via
  `zoneinfo.ZoneInfo("Europe/Berlin")`, konvertiert nach UTC, im selben
  `%Y-%m-%dT%H:%M:%S.000Z`-Format. **Das Ende bekommt die Lag-Toleranz abgezogen** (Lock J5):
  Modulkonstante `RECORDER_LAG_TOLERANCE_MIN = 30` mit Kommentar, der den gemessenen Wert
  nennt (18 min am 2026-09-08) und den Upgrade-Pfad: wenn der Recorder-Takt je enger wird,
  ist das die einzige Stellschraube — nicht die Gap-Schwelle. `import` von `zoneinfo` oben ergänzen (Z. 11-17 Block).
  Die Zeiten 09:00/17:30 spiegeln `phase8_scheduler/scheduler/config.py:124-125`
  (`window_open` / `window_close`) — **als Konstante gespiegelt, nicht importiert**: Phase 12
  importiert nicht aus Phase 8. Ein Kommentar nennt die Quelle.
- Tests: `phase12_data_foundation/tests/test_heartbeat.py` um **2** Tests erweitern —
  `test_assess_day_ok_with_session_only_bars` (Bars nur 07:00–15:30 UTC ⇒ `ok=True`, der
  Fall der heute fälschlich FAILt) und `test_assess_day_flags_gap_inside_session`
  (20-Minuten-Loch um 10:00 UTC ⇒ `ok=False`). Prüfen, ob die bestehende
  `bars`-Fixture (`skip_minutes`, Z. ~88) den Tag noch abdeckt — sie füllt heute 24 h.
- **AK-J4 hängt an zwei Zweigen, nicht an einem.** J3 räumt nur den Gap-Zweig (`:146-151`)
  ab. Der zweite `ok=False`-Pfad (`:142-145`, `shadow_enabled and pairs_resolved == 0 and
  pairs_typed_expired == 0`) bleibt unangetastet und kann K4 allein rot halten — heute
  48 Paper-Trades created, 0 resolved, letzte Resolution 2026-08-31 (V-4). Ein `ok=false`
  nach J3 ist deshalb **kein** Beleg, dass der Fenster-Fix versagt hat: erst `worst_coverage`
  im Event anschauen (nahe 1,0 ⇒ J3 hat gewirkt), dann den Resolver.
- Commit: `phase16+phase12: fix -- Heartbeat-Coverage misst die Handelssitzung statt 00-24h; Overnight-Luecke riss die 5-Min-Gap-Schwelle, ok=False an 10 Tagen in Folge`

**J4 — Log-Hygiene (Operator-Aktion, Nikinger).**
```
cp data/state/run_scheduler.log data/state/run_scheduler.log.2026-09-08.pre-J-truncate
: > data/state/run_scheduler.log
```
Ebenso `run_recorder.log`, `run_discovery.log`, `run_webui.log` (die drei stehen heute schon
auf 1/1/2 Treffer, aber der neue Lauf soll bei 0 anfangen). Das Backup ist der Beleg für
J-D1 und gehört **nicht** ins Git (`data/` ist gitignored).

**J5 — Prereg v2 schreiben** (docs).
Neue Datei `phase16_activation/PHASE16_AUTONOMY_PREREGISTRATION_v2.md`, Header-Card mit
`status: snapshot`, `up: ./CLAUDE.md`. Inhalt: v1 verbatim übernommen **plus** ein
`## Warum v2` mit den drei Befunden aus §1.3, den drei Fixes und dem neuen Aktiv-Block
(Start-Zeitstempel wird vom Operator **vor** der ersten Start-Zeile eingetragen).
v1 bleibt Byte-identisch — nur `docs/INDEX.md` bekommt bei v1 den Zusatz „⚠ superseded durch
v2" analog zum `PHASE16_E3_RUNBOOK.md`-Muster (INDEX Z. 40).
`docs/INDEX.md` bekommt im selben Commit die v2-Zeile.

**J6 — Restart (Operator-Aktion, Nikinger).**
`PHASE16_E3_RUNBOOK_v2.md` §3 verbatim. Danach die Startzeile prüfen:
```
grep "starting scheduler daemon" data/state/run_scheduler.log
```
muss **genau eine** Zeile liefern und `account=demo, max_trades=5, daily_loss_cap=1800.0,
cycle=5min` enthalten.

**J7 — Day-0-Verify (Exec-Session).**
> **Timing:** die vier unteren Zeilen laufen ~15 min nach J6. Die **LS-Bars-Zeile nicht** —
> der Tick-Aggregator schreibt erst bei Kerzen-Rollover unter fließenden Marktdaten. Am
> 2026-09-08 kam das erste `Lightstreamer SUBOK` um 09:35:25, die ersten Kerzen danach. Bei
> einem Restart um 08:45 ist `count = 0` um 09:00 **korrekt** und kein Beleg gegen J1. Die
> Zeile frühestens **10 min nach Markt-Öffnung** (09:10 Berlin) prüfen.
| Check | Kommando | Erwartung |
|---|---|---|
| LS-Bars fließen (**ab 09:10 Berlin**, s. Timing-Hinweis) | `sqlite3 "file:data/bars.sqlite?mode=ro" "select count(*) from bars where source='ls'"` | **> 0** (der eigentliche Beweis für J1) |
| Keine Tracebacks | `grep -c ProgrammingError data/state/run_scheduler.log` | 0 |
| K1 | `autonomy_report.py --day <heute> --reports-dir /tmp/verify` | `criteria.1.verdict == PASS`, `scheduler.starts == 1` |
| Log-Wachstum | `du -m data/state/run_scheduler.log` | < 5 MB nach 1 h |
| K4 | nach dem ersten POST_WINDOW: `grep measurement_heartbeat data/state/research_health.jsonl \| tail -1` | `"ok": true` |

**Akzeptanz J:** J-D1/J-D2/J-D3 alle drei durch J7 widerlegt · Σ = 1934 + 6 neue Tests =
**1940** · v2-Prereg + INDEX-Zeile committet · genau eine Start-Zeile je Dienst im Log.

### Block H — Audit-Restbefunde (docs + Hook, außerhalb 09:00–17:30)

> Diese Mechanik **supersedet** `PHASE16_PARTIAL_CLOSEOUT.md` §4 Block H. Der Closeout bleibt
> als 📕-Snapshot stehen; die Gründe für die Abweichung stehen in §1.4.

**H-3 — Sammel-Reparatur (zuerst, siehe Lock H2).** 29 Befunde, je mit Datei:Zeile und
verbatim-Anker. Zeilennummern Stand 2026-09-08.

*Pattern A — `../../` → `../` (21 Links, 5 Dateien).* Mechanisch per
`sed -i 's|\.\./\.\./|../|g' <datei>` — **mit zwei Ausnahmen**, die per Hand nachgezogen
werden (siehe unten).

| Datei | Zeilen | Anker (erste Zeile verbatim) |
|---|---|---|
| `phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md` | 14, 15, 17, 18 | `  - ../../docs/concepts/phase13_live_data_plan.md  # 📕 Mutterplan, unangetastet` |
| `phase14_discovery/PHASE14_B1A_PROBE_OUTPUT_2026-08-22.md` | 6, 8 | `up: ../../docs/concepts/phase14_discovery_plan.md` |
| `phase14_discovery/PHASE14_F_DOC_ROTATION_HOOK_STEP2_PLAN.md` | 12, 13, 15, 16 | `  - ../../scripts/check_doc_rotation.py                            # das Tool, das erweitert wird (existiert seit Session 16, 2026-08-27)` |
| `phase15_v4/PHASE15_HOOK_HARDENING_PLAN.md` | 11, 12, 13, 14 | `  - ../../scripts/check_doc_rotation.py                            # das Tool, das erweitert wird (P14-F-Stand)` |
| `phase7_reward/PHASE12_RECONCILIATION_TIMING_PLAN.md` | 18–24 | `  - ../../phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md # Vor-Findings (Phase-13-Beweiswoche-Auswertung 2026-08-31)` |

**Ausnahme A1** — `phase14_discovery/PHASE14_F_DOC_ROTATION_HOOK_STEP2_PLAN.md:14`, verbatim:
`  - ../SESSIONS_ARCHIVE.md                                         # die Archive-Datei, deren Integrität jetzt zusätzlich geprüft wird`
→ muss `./SESSIONS_ARCHIVE.md` werden (die Datei liegt **im selben** Phasenordner). Das `sed`
fasst diese Zeile nicht an, sie ist trotzdem kaputt.

**Ausnahme A2** — `phase7_reward/PHASE12_RECONCILIATION_TIMING_PLAN.md:24`, verbatim:
`  - ../../phase2_persistence/migrations/003_phase12_reconcile_backoff.sql # 📕 NEU — die Backoff-Spalte (D2)`
→ nach dem `sed` immer noch tot: die Migration heißt heute
`008_phase12_reconcile_backoff.sql` (umnummeriert, `ls phase2_persistence/migrations/`
bestätigt 001–009). Also `../phase2_persistence/migrations/008_phase12_reconcile_backoff.sql`.

*Pattern B — `up: ./CLAUDE.md` in `docs/concepts/` (4 Dateien).* **Kein `sed`** — `../CLAUDE.md`
zeigt auf `docs/CLAUDE.md`, das es nicht gibt. Ziel je Datei, Muster aus den intakten
Nachbarn (`phase14_discovery_plan.md:up: ../../phase14_discovery/CLAUDE.md`,
`phase15_v4_plan.md:up: ../../CLAUDE.md`):

| Datei:Zeile | Anker verbatim | Neu |
|---|---|---|
| `docs/concepts/phase10_v3_plan.md:6` | `up: ./CLAUDE.md` | `up: ../../phase10_v3/CLAUDE.md` |
| `docs/concepts/PHASE10_V3_KICKOFF_HANDOVER.md:8` | `up: ./CLAUDE.md` | `up: ../../phase10_v3/CLAUDE.md` |
| `docs/concepts/meta_m1_harness_plan.md:6` | `up: ./CLAUDE.md` | `up: ../../meta_m1_harness/CLAUDE.md` |
| `docs/concepts/PHASE10_META_KICKOFF_HANDOVER.md:6` | `up: ./CLAUDE.md` | `up: ../../CLAUDE.md` (Meta-Kickoff nach Phase 9 — kein Phasenordner ist der richtige Elternteil, der Root-Phasenkopf schon) |

*Pattern C — tote Referenz (1).* `phase15_v4/PHASE15_HOOK_HARDENING_PLAN.md:10`, verbatim:
`  - ./PHASE15_A1_A6_STEP_RECORDS.md                                # 📕 A-1..A-6 Detail-Protokolle (im Phasenkopf Sektionen, nicht diese Datei)`
→ **Zeile löschen** (Lock H3).

*Pattern D — Prosa-Liste (1).* `phase10_v3/PHASE10_CLOSEOUT_HANDOVER.md:13`, verbatim:
`  - ./DATA_WEEK_REVIEW_2026-07-25.md / -07-31.md / -08-07.md   # 📕 die drei Datenwochen (V3-Folgephase Inhalte)`
→ drei Zeilen, je ein Pfad. Alle drei Dateien existieren (geprüft).

*Pattern E — falsches Ziel (1).* `docs/concepts/market_snapshot_middleman_konzept.md:8`, verbatim:
`  - ./phase9_v2_foundation_plan.md          # V2b-Kette + Divergenz-Check (der Ist-Zustand)`
→ `./phase9_v2_foundation_plan(1).md` (Lock H4 — der echte Dateiname trägt die Klammern).

> Das im Closeout §2.1 genannte „Pattern E, 8× Mischformen" existiert nicht als eigene
> Kategorie — der eigene Scan (Skript-Spec in H-5) findet 29 Befunde, restlos in A–E oben
> abgedeckt. Wer im Hook-Output mehr sieht, hat einen neuen Befund und keine Mischform.

**1 Sammel-Commit:** `phase16: docs -- Sammel-Reparatur 29 Header-Card-Link-Drifts (Pattern A-E aus Audit-Session #19; 2 Ausnahmen die kein sed faengt: ../SESSIONS_ARCHIVE.md und 003->008 Migration-Umnummerierung)`

**H-4 — Phase-14-Archiv-Reihenfolge.**
`phase14_discovery/SESSIONS_ARCHIVE.md`: der Session-7-Block steht am Dateiende statt
chronologisch. Anker (Z. 3205), verbatim:
`## Session stopped — 2026-08-22 (Session 7: CFD-Filter-Fix + Block B1b + Block A4)`
Zielposition: **vor** Z. 2527, verbatim:
`## Session stopped — 2026-08-22 (Session 6: B1a-Operator-Probe gelaufen + Findings dokumentiert)`
Zu verschieben: Z. **3204** (der `---`-Separator direkt über der Heading) bis **3382**
(Dateiende). Inhalt bleibt Byte-identisch; nur die Position ändert sich. Nach dem Move prüfen,
dass Session 1 (Z. 3102) sauber mit `---` abschließt und dass
`grep -c "^## Session stopped" phase14_discovery/SESSIONS_ARCHIVE.md` weiterhin **23** liefert.
Commit: `phase14: docs -- Session-7-Block chronologisch einsortiert (stand am Dateiende, Phase-16-F Block H-4)`

**H-2 — INDEX-Scope-Klarstellung.**
`docs/DOC_LAYERS_CONVENTION.md`, Anker (Z. 53), verbatim:
`Maintenance rule: **new .md file ⇒ its index line lands in the same commit.**`
→ ein Satz darunter: Skill-Internals (`.agents/skills/`) und Harness-Specs
(`meta_m1_harness/specs/`) sind Tooling-Metadaten und werden nicht in `docs/INDEX.md`
gelistet; die Regel gilt für `phase*/`, `docs/` und Root-`.md`.
Commit: `phase16: docs -- DOC_LAYERS_CONVENTION.md: INDEX-Scope-Klarstellung (Skill-Internals + Harness-Specs sind Tooling-Metadata)`

**H-1 — Step 4 im Hook** (nach H-3/H-4, Lock H2).
Datei `scripts/check_doc_rotation.py`.

- Neue Funktion `check_header_card_links(md_path) -> list[tuple[str, str]]` neben
  `check_archive_gaps` (Z. 191). Spec — genau die Regeln, mit denen die 29 Befunde oben
  reproduziert wurden:
  1. Header-Card = der YAML-Block, wenn die Datei mit `---\n` beginnt, bis zum nächsten `\n---\n`.
  2. Ziele: die `up:`-Zeile (einzeiliger Wert) und jeder `  - `-Eintrag unter `down:`.
  3. Pro Wert: alles ab dem ersten `#` abschneiden (Kommentar), dann `**` und Backticks
     entfernen. **`_` bleibt** — Unterstriche sind Teil der Dateinamen.
  4. Werte, die mit `http` beginnen: überspringen.
  5. Enthält der Wert Whitespace, wird jedes Token geprüft, das `/` enthält **oder** auf
     `.md`/`.py`/`.sql`/`.svg` endet. Ein Wert ohne solches Token ist Prosa und wird
     übersprungen — das ist die Regel, die `docs/INDEX.md:7 down: every project doc (that is
     the point)` in Ruhe lässt.
  6. Ziel relativ zum **Verzeichnis der Datei** auflösen, `Path.exists()`.
- Scope: alle `*.md` unter dem Repo-Root außer `.git/`, `.venv/`, `node_modules/`,
  `.agents/`, `__pycache__/`. (Zur Einordnung: 92 Dateien tragen heute eine Header-Card.)
- Verdrahtung in `main()`: Anker (Z. 351-364), verbatim beginnend mit
  `    if getattr(args, "strict", False):` — Step 4 läuft im selben `--strict`-Block wie
  Step 2/3, sammelt in dieselbe `seq_bad`-Liste und teilt den `return 1`.
- Modul-Docstring (Z. 1) und `--strict`-Hilfetext (Z. 309-316) auf vier Steps erweitern.
- `.git/hooks/pre-commit` und die `CANONICAL_BODY` in `scripts/install_hooks.sh` weichen
  heute schon voneinander ab (installierte Version sagt „Two steps", die kanonische kennt
  Step 3 — Verhalten identisch, beide rufen `--strict --quiet`). Beim Step-4-Kommentar beide
  auf denselben Stand bringen und `bash scripts/install_hooks.sh` einmal laufen lassen,
  sonst meldet der Installer beim nächsten Mal einen Diff.
- Tests in `tests/test_check_doc_rotation.py` (bestehende Datei, 750 Z.), **6** neue:
  `test_header_card_up_link_ok` · `test_header_card_down_links_with_inline_comment` ·
  `test_header_card_strip_markdown_preserves_underscores` ·
  `test_header_card_prose_down_entry_is_ignored` (Regressions-Pin für `docs/INDEX.md`) ·
  `test_header_card_double_dotdot_is_flagged` (Pin für die 21 Pattern-A-Bugs) ·
  `test_header_card_repo_is_clean` (läuft gegen das echte Repo — schlägt fehl, sobald jemand
  eine kaputte Karte einführt).
- Commit: `phase16: code+tests -- check_doc_rotation.py Step 4: Header-Card-Link-Check (F3 revidiert, kein zweites Skript; 29 Befunde vor H-3 / 0 danach), root 115 -> 121`

**H-5 — Verifikation.**
```
python3 scripts/check_doc_rotation.py --strict --quiet ; echo "exit=$?"     # 0
```
Beweis-Protokoll für den Commit-Body: auf `git stash`-Stand vor H-3 muss derselbe Aufruf
exit 1 mit 29 gelisteten Befunden liefern.
Σ nach Block H: 1940 + 6 = **1946**.

**Akzeptanz H:** H-3 + H-4 + H-2 + H-1 committet · Hook exit 0 · Σ 1946 · `git grep -n "\.\./\.\./" -- "*/*.md"`
liefert in Header-Cards keine Treffer mehr.

### Block G — Tagesroutine (10 Handelstage ab J6)

**G1** (Nikinger, täglich): `python3 phase16_activation/scripts/autonomy_report.py --day YYYY-MM-DD`
→ schreibt `data/reports/autonomy_<day>.json`.
> **Hinweis:** die heute dort liegende `autonomy_2026-09-08.json` hat mtime 2026-09-07 18:08
> — sie ist **vor** Restart #4 entstanden und beschreibt einen anderen Lauf. Bei J4 mit
> wegräumen.

**G2** (Nikinger, täglich): Caps-Pin prüfen. **Korrigiertes Kommando** (das aus dem Partial
Closeout liest `/proc/<pid>/cmdline` und findet dort nur `python -m scheduler.run`, weil die
Caps aus der Config kommen, nicht aus argv):
```
grep "starting scheduler daemon" data/state/run_scheduler.log | tail -1
```
muss `account=demo, max_trades=5, daily_loss_cap=1800.0, cycle=5min` enthalten — dieselbe
Zeile, die `extract_caps_from_scheduler_log` (`autonomy_report.py:437`) für K7 parst.

**G3** (Exec, on demand): K1-FAIL im Tagesreport ⇒ Root-Cause im Session-Block, Muster wie
§1.3.
**G4** (Exec, on demand): K5-FAIL ⇒ Tracing per `phase16_activation_plan.md` §8.
**G5** (Exec, täglich, neu): `grep -c ProgrammingError data/state/run_scheduler.log` muss 0
bleiben und `du -m data/state/run_scheduler.log` unter 50 MB. Beides ist der Frühwarnung für
einen Rückfall von J1.

**Akzeptanz G:** 10 Tagesreports ohne manuellen Restart · `daily_loss_cap=1800` nie gerissen ·
Caps-Pin jeden Tag korrekt · kein `ProgrammingError`.

### Block I — Tag-10-Closeout

> **Datum verschiebt sich mit J6.** Tag 1 = erster voller Handelstag nach dem Restart;
> Tag 10 = Tag 1 + 9 Handelstage. Das exakte Datum trägt die Exec-Session in Prereg v2 ein.

**I-1** `autonomy_report.py --from <Tag1> --to <Tag10> --summary`.
**I-1a — Eskalationszweig K3 (vorab entschieden, damit niemand neu planen muss).** K3
verlangt ≥ 5 autonome CLOSED-Trades. Am 2026-09-08 gab es 0 Trades bei 14
`reason_no_candidates`-Abstains — und die Abstain-Begründungen sind **inhaltlich** (Drift,
Momentum, Volumen-z-Score), nicht die strukturelle Leer-Historie von vor Phase 16. Wenn K3
am Tag 10 FAILt, ist das ein **Strategie**-Befund (Prereg-Watch-Items W1/W2), den
`PHASE16_PARTIAL_CLOSEOUT.md` §7 explizit an Phase 17 delegiert. Der Closeout dokumentiert
das dann als „Infrastruktur bewiesen, Strategie offen" und verlängert den Lauf **nicht** von
sich aus — das ist eine Nikinger-Entscheidung.
**I-2** `phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md` NEU, Struktur wie
`phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md`; Blöcke A–F + J.
**I-3** `docs/architecture/phase16_activation.svg` NEU (1080×1080, 5 Panels wie Phase 13/14/15).
**I-4** Status-Pflege: root `CLAUDE.md` (Phase-16-Zeile), `ROADMAP.md`, `README.md`,
`docs/INDEX.md` (+ Closeout + SVG + dieser Plan + Prereg v2).
**I-5** Session-Rotation nach `phase16_activation/SESSIONS_ARCHIVE.md`.

**Akzeptanz I:** I-1..I-5 ✅, Phase 16 in allen vier Statusdokumenten geschlossen.

## §4 Testliste (neu, gesamt +12 → Σ 1946)

| Datei | Test | Deckt |
|---|---|---|
| `phase12_data_foundation/tests/test_archive.py` | `test_insert_bars_from_other_thread` | J1 / J-D1 |
| `phase16_activation/tests/test_autonomy_report.py` | `test_k1_ignores_starts_before_window` | J2 / J-D2 |
| `phase16_activation/tests/test_autonomy_report.py` | `test_k1_webui_single_start_counts_once` | J8 |
| `phase12_data_foundation/tests/test_heartbeat.py` | `test_assess_day_ok_with_session_only_bars` | J3 / J-D3 |
| `phase12_data_foundation/tests/test_heartbeat.py` | `test_assess_day_flags_gap_inside_session` | J3 (Gegenprobe) |
| `phase12_data_foundation/tests/test_heartbeat.py` | `test_assess_day_tolerates_lagging_recorder_tail` | J5-Lag-Toleranz (Bars enden 20 min vor Sitzungsschluss ⇒ `ok=True`) |
| `tests/test_check_doc_rotation.py` | 6 Tests, Liste in H-1 | Step 4 |

## §5 Akzeptanzkriterien

| AK | Kriterium | Beleg |
|---|---|---|
| **AK-J1** | `bars.source='ls'` > 0 nach dem ersten Handelstag | SQL, `mode=ro` |
| **AK-J2** | 0 `ProgrammingError` im neuen `run_scheduler.log` | `grep -c` |
| **AK-J3** | K1 = 1 Start je Dienst im Tagesreport | `autonomy_<day>.json` |
| **AK-J4** | `measurement_heartbeat.ok == true` am ersten POST_WINDOW | `research_health.jsonl` |
| **AK-J5** | Prereg v2 committet **vor** der ersten Start-Zeile des neuen Laufs | `git log` vs. Log-Zeitstempel |
| **AK-H1** | `check_doc_rotation.py --strict --quiet` exit 0 mit Step 4 aktiv | Konsole |
| **AK-H2** | Beweis 29 → 0 im Commit-Body dokumentiert | Commit-Message |
| **AK-G1** | 10 Tagesreports, kein manueller Restart | `data/reports/` |
| **AK-I1** | Closeout-Handover + SVG + 4 Statusdokumente aktualisiert | Dateien |
| **AK-Σ** | Σ = 1946 am Ende (1934 + 12) | Suite-Sweep |

## §6 Bei Ausführung verifizieren (vollständig — was hier nicht steht, ist geprüft)

| # | Punkt | Warum offen |
|---|---|---|
| **V-1** | Ob `phase12_data_foundation/tests/test_archive.py` existiert und wie die Bar-Fixture heißt. | Ich habe die Datei nicht geöffnet, nur die 145 grünen Phase-12-Tests gezählt. |
| **V-2** | Der genaue Aufbau der `bars`-Fixture in `test_heartbeat.py` (Z. ~88, `skip_minutes`) — sie füllt heute vermutlich 24 h und muss für J3 auf Sitzungszeiten. | Nur die Zeilennummer gegrept, den Fixture-Body nicht gelesen. |
| **V-11** | Ob `RECORDER_LAG_TOLERANCE_MIN = 30` reicht. Gemessen wurde **ein** Wert (18 min am 2026-09-08, 08:48 UTC). Der Recorder-Takt selbst wurde nicht gelesen. | Ein Tag ist keine Stichprobe. Wenn K4 mit `worst_coverage` nahe 1,0 rot bleibt, ist das die erste Stellschraube (§7). |
| **V-3** | Ob `BarArchive` außer Recorder/Scheduler noch andere Prozesse hat, die von der `check_same_thread`-Änderung berührt werden. | `grep -rn "BarArchive("` nicht gelaufen. |
| **V-4** | Ob der **zweite** `ok=False`-Zweig (`pairs_resolved == 0 and pairs_typed_expired == 0`, `heartbeat.py:142`) zusätzlich feuert. Heute 48 Paper-Trades created, 0 resolved, letzte Resolution 2026-08-31. Entscheidet sich erst im ersten POST_WINDOW nach J6. | Der Resolver läuft nur nach 17:30. **Wenn J3 allein K4 nicht grün macht, ist das der erste Verdächtige — nicht der Fenster-Fix.** |
| **V-5** | Ob die 3 SUN*-Epics weiter IG-Punkte ziehen (heute 15 Punkte, `kind='research'`). Status `verified`, nicht `active` — Prereg formal erfüllt. | Der Pfad, der für `verified`-Epics fetcht, ist nicht zurückverfolgt. Watch-Item, kein J-Blocker. |
| **V-6** | Ob die 2 Zombie-Prozesse nach J6 wiederkommen (Prereg-Watch-Item W5). | Ursache nicht untersucht. |
| **V-7** | Ob `_berlin_day` (`autonomy_report.py:230`) eine Umkehrfunktion hat oder J2 einen neuen Helper braucht. | Nur die Vorwärtsrichtung gelesen. |
| **V-8** | Ob nach dem Pattern-A-`sed` in `PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md` auch die Body-Links (z. B. Z. 298) mitgehen sollen — die Header-Card ist Pflicht, der Body nicht. | Step 4 prüft nur Header-Cards; Body-Links sind heute kein Vertrag. |
| **V-9** | Ob `phase15_v4/PHASE15_HOOK_HARDENING_PLAN.md` nach dem Löschen von Z. 10 noch eine gültige `down:`-Liste hat (Einrückung). | Nur die Zeile gelesen, nicht die Blockgrenzen. |
| **V-10** | Der exakte `docs/INDEX.md`-Einfügepunkt für Prereg v2 + diesen Plan (Cluster Z. 34-42). | Der Cluster ist gelesen, die genaue Sortierregel innerhalb nicht. |

## §7 Fehlgriffe (Symptom → erster Verdächtiger)

| Symptom nach dem Fix | Sieht aus wie | Erster Verdächtiger |
|---|---|---|
| `ProgrammingError` weg, aber `bars.source='ls'` bleibt 0 | „LS liefert keine Ticks" | Nicht J1. `stream.py:498` fängt `ArchiveError` — schau, ob `_write_candle` jetzt still in einen anderen `except`-Zweig läuft, und ob die LS-Subscription überhaupt `SUBOK` meldet (`grep "Lightstreamer SUBOK"`). |
| `database is locked` statt `ProgrammingError` | „Der Lock hilft nicht" | `SourceBudget` mit **eigener** Verbindung auf dieselbe Datei (`archive.py:42`). Der Lock schützt nur `BarArchive`. Kein WAL nachrüsten, ohne das zu messen. |
| K4 bleibt `ok=False` nach J3, `worst_coverage` aber nahe 1,0 | „Fenster-Fix wirkt nicht" | Der **Schwanz**. `assess_window` (`coverage.py:94-105`) zählt die Lücke zwischen letzter Bar und `end_dt` mit; der yF-Recorder hinkt ~18 min nach. Wenn `RECORDER_LAG_TOLERANCE_MIN` zu klein ist, tauscht J3 nur eine 930-Minuten-Lücke gegen eine 20-Minuten-Lücke. Erst die Toleranz prüfen, dann alles andere. |
| `bars.source='ls'` = 0 kurz nach dem Restart | „J1 hat nicht gewirkt" | Die Uhr. Erste Kerze kommt erst nach `SUBOK` **und** dem ersten Minuten-Rollover unter fließenden Kursen — vor 09:10 Berlin ist 0 der erwartete Wert. |
| K4 bleibt `ok=False` nach J3 | „Fenster-Fix wirkt nicht" | **V-4**: der zweite Zweig (`pairs_resolved == 0`). `worst_coverage` im Event anschauen — steht es jetzt nahe 1,0, hat J3 gewirkt und der Fehler kommt woanders her. |
| K1 zeigt weiter 7 | „Fenster kommt nicht an" | Zwei Aufrufer, nicht einer — Z. 870 **und** Z. 919. Einen davon zu vergessen fällt erst im Summary auf. |
| Hook schlägt nach H-1 auf einer intakten Datei an | „Neuer Bug im Step 4" | Die Markdown-Strip-Regel. `_` darf **nicht** entfernt werden (Dateinamen wie `PHASE10_CLOSEOUT_HANDOVER.md`), `**` und Backticks schon. Das ist Regel 3 der H-1-Spec und der Grund für `test_header_card_strip_markdown_preserves_underscores`. |
| Nach H-3 meldet der Hook mehr als 0 | „`sed` war unvollständig" | Die zwei Ausnahmen A1 (`../SESSIONS_ARCHIVE.md`) und A2 (`003_` → `008_`). Kein `sed` fasst die an. |
| Commit wird vom Pre-Commit-Hook blockiert | „Rotation kaputt" | Reihenfolge (Lock H2): Step 4 darf erst **nach** der Reparatur eingecheckt werden. |

## §8 Operator-Aktionen (Nikinger, nicht Exec-Session)

| # | Wann | Was | Kosten |
|---|---|---|---|
| 1 | vor J1 | Bot stoppen (J0), `ps` als Gegenprobe | ~2 min |
| 2 | nach J3 | Logs sichern + truncaten (J4) | ~1 min |
| 3 | morgens vor 09:00 | Restart nach Runbook v2 §3 (J6) | ~5 min |
| 4 | täglich, 10 Tage | `autonomy_report.py --day` (G1) + Caps-Pin (G2, **korrigiertes** Kommando) | ~1 min/Tag |
| 5 | nach Block J / Block H | Push-Freigabe | — |
| 6 | Tag 10 nach 17:30 | `--from/--to --summary` (I-1) | ~5 sec |
| ~~7~~ | — | ~~Ledger-Restore 250 Punkte~~ | **erledigt** — 0 Zeilen `kind='rescue'` (2026-09-08 gemessen) |
| ~~8~~ | — | ~~Migration 008+009 auf Live-DB~~ | **erledigt** — `_schema_version` = 9 (2026-09-08 gemessen) |

## §9 Out-of-Scope (Phase-17-Material)

Unverändert die 7 Punkte aus `PHASE16_PARTIAL_CLOSEOUT.md` §7, plus:

- **Rename `phase9_v2_foundation_plan(1).md`** → 10 Fundstellen, kein Funktionsgewinn (Lock H4).
- **Zombie-Reaping im Scheduler** (2 `<defunct>`-Kinder pro Lauf, Prereg-W5).
- **IG-Punkte für `verified`-Epics** (V-5) — 15 Punkte/Tag an SUN*-Epics, die nie gehandelt werden.
- **`run_scheduler.log`-Rotation** — 43 MB in 8 Tagen ohne Bug; `critical_count_after_opens`
  (`autonomy_report.py:385`) liest die Datei bei jedem Report zeilenweise und trägt einen
  Kommentar „cheap: ~120 KB/day", der nicht mehr stimmt.

## §10 Commit-Konvention

`<scope>: <typ> -- <imperativ>`; Scope `phase16` oder `phase16+phase12` / `phase14` bei
Cross-Phase-Touch. Ein logischer Schritt = ein Commit; Ausnahme ist der H-3-Sammel-Commit
(Lock F4 aus dem Partial Closeout, hier übernommen). Cross-Phase-Freigaben, die dieser Plan
nutzt: P1/2/3/4/5/7/8/9/15 (Phase-16-Plan §4) **+ P12** (Nikinger 2026-09-08, Block J)
**+ P14** (Block H-4, Archiv-Move) **+ P15** (Block H-3, Pattern C) **+ P7/P13** (Block H-3,
Pattern A).
