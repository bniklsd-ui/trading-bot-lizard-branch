---
status: snapshot (aktive Vorregistrierung — supersedet v1)
purpose: Aktive, korrigierte Vorregistrierung des 2-Wochen-Autonomie-Tests. v1 verbatim
  übernommen **plus** ein "Warum v2"-Block, der die drei J-Block-Struktur-Defekte und
  ihre Fixes dokumentiert. Aktiv-Block (Start-/Endzeitstempel) wird vom Operator am
  E3-Restart-Tag ausgefüllt, **bevor** die erste Start-Zeile im Log landet.
read-when: Block-E-Ausführung (E2–E4); Audit, ob die Kriterien vor oder nach dem
  Lauf festgelegt wurden — v2 ist die aktive Vorregistrierung, v1 ist byte-identisch
  eingefroren (siehe Warnung dort)
detail: L3
up: ./CLAUDE.md
down:
  - ./PHASE16_AUTONOMY_PREREGISTRATION.md  # v1 — byte-identisch eingefroren, durch v2 supersedet
  - ./PHASE16_F_EXEC_PLAN.md                # Plan-Session 2026-09-08 (Opus 5), §1.3 die drei Befunde
  - ../docs/concepts/phase16_activation_plan.md   # 📕 §6 Block E Steps E1–E4 (Quelle), §7 AK13+AK15, §11 Operator-Aktionen
  - ../phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md    # 📕 Vorgänger (E1–E3 bleiben in Phase 16 zu schließen)
  - ./SESSIONS_ARCHIVE.md                         # 📦 Session-Block-Historie
updated: 2026-09-08
---

# PHASE16_AUTONOMY_PREREGISTRATION v2

> **Dieses Dokument ist committet bevor der 2-Wochen-Test startet und wird danach nicht
> geändert.** Korrekturen sind nur als neues, datiertes, supersedendes Dokument mit
> angegebenem Grund möglich — nie als Edit an dieser Datei. Das gilt für jeden Wert in
> `## Vorregistrierte Werte` und `## PASS-Kriterien` unten. Der Aktiv-Block ganz unten
> ist die einzige Ausnahme: er wird vom Operator **am Tag des E3-Restarts** ausgefüllt
> (vor der ersten Start-Zeile im Log, AK13), das ist eine **Eintragung**, kein
> **Edit** — der Mechanismus ist hier explizit dokumentiert und zählt als „Eintragung
> des Startzeitpunkts", nicht als „Änderung der Kriterien".
>
> **Warum diese Disziplin:** ein nach dem Lauf geschriebenes Kriterium beweist nichts
> (M1-Vorregistrierungs-Disziplin, Plan §1 P11; Opus-Review §13: `*_state.json` werden
> in-place überschrieben und taugen nicht als Beleg). Die `*_state.json`-Quellen sind
> deshalb für E2 explizit ausgeschlossen, die AK15-Messquellen sind ausschließlich
> **append-only**.
>
> **Warum v2 statt v1 (2026-09-08, Plan-Session #21):** beim Audit des ersten Laufs
> (Start-Zeitstempel 2026-09-07 21:58:27, v1-Aktiv-Block) wurden **drei selbst
> gemessene Struktur-Defekte** entdeckt, die den v1-Lauf strukturell unfähig zum PASS
> machten. v1 ist nicht falsch — die Kriterien sind korrekt — aber das Substrat konnte
> sie nicht erfüllen. v2 tritt für den nächsten Lauf an die Stelle; v1 bleibt
> byte-identisch eingefroren (Disziplin). Details in `## Warum v2` unten.

## BLUF

Vorregistrierter 2-Wochen-Autonomie-Test (10 Handelstage, IG Demo). PASS = alle sieben
Kriterien erfüllt, gemessen aus **append-only** Quellen. Erlaubte Operator-Eingriffe:
einmalig Backoff-KILL-Clear, kein Reboot. Tagesreport aus `scripts/autonomy_report.py`
genügt; **nichts** sonst anfassen.

## Warum v2 — die drei Struktur-Defekte des v1-Laufs und ihre Fixes

Alle drei Befunde wurden am 2026-09-08 (Plan-Session #21) selbst gemessen und in
[`./PHASE16_F_EXEC_PLAN.md`](./PHASE16_F_EXEC_PLAN.md) §1.3 dokumentiert.

### Befund 1 — J-D1: LS-Bar-Stream schrieb seit 2026-09-08 09:35 keine einzige Kerze

`phase12_data_foundation/data_foundation/archive.py:77` öffnete die SQLite-Verbindung
mit dem Default `check_same_thread=True`. `phase13_live_data/live_data/stream.py:498`
(`_write_candle`) schreibt aus dem Lightstreamer-Listener-Thread → jede geschlossene
Kerze endete in `sqlite3.ProgrammingError: SQLite objects created in a thread can only
be used in that same thread`. Gemessen: **63 942** Vorkommen allein am 2026-09-08,
erstes um 09:35:25,745. `bars.source='ls'` = **0** seit die Tabelle existiert.

**Fix J1 (Commit `669dde9`, Cross-Phase P12):** `BarArchive.__init__` öffnet die
Verbindung jetzt mit `check_same_thread=False`, jede DB-Methode serialisiert über
`threading.Lock`. Test `test_insert_bars_from_other_thread` pinnt das Verhalten —
bricht, sobald jemand `check_same_thread` zurückdreht.

### Befund 2 — J-D2 + J-D8: K1 zählte alle 7 historischen Starts statt 1; WebUI-Doppelzählung

`phase16_activation/scripts/autonomy_report.py:870` und `:919` riefen
`evaluate_k1(state_dir)` ohne Fensterargumente auf; `count_starts_in_window`
filterte nur, wenn `from_ts`/`to_ts` gesetzt waren → **7** Scheduler-Starts seit
2026-08-31 wurden für jeden Tagesbericht mitgezählt. Zusätzlich matchte
`_START_PATTERNS["webui"]` (Z. 143) zwei Muster (`[run_webui] dashboard on`
**und** uvicorn-eigenes `Started server process`) → jeder WebUI-Start zählte doppelt
und verbrauchte das 2-Restart-Budget mit einem einzigen Neustart.

**Fix J2 + J8 (Commit `3969f8c`):** beide Aufrufer übergeben jetzt
`from_ts`/`to_ts` aus neuem Helper `_berlin_day_bounds(day)` (Inverse zu
`_berlin_day`, end-exclusive). `_START_PATTERNS["webui"]` matcht nur noch das
Wrapper-Pattern. Tests `test_k1_ignores_starts_before_window` und
`test_k1_webui_single_start_counts_once` pinnen beide Fixes.

### Befund 3 — J-D3: K4 war per Konstruktion unerreichbar

`phase12_data_foundation/data_foundation/heartbeat.py:73` holte das Coverage-Fenster
aus `_day_bounds_iso` — das ist **00:00 → 24:00 UTC**. Die Coverage-Schleife prüfte
darin die yF-1-Minuten-Bars; ein normaler Handelstag liefert ≈8,5 h Bars in 24 h,
die Nacht ist eine zusammenhängende Lücke von ≈930 min ≫ 5 min → `largest_gap_min >
5` immer erfüllt → `ok=False` durchgehend seit 2026-08-24 (10 Tage in Folge).

**Fix J3 + J5 (Commit `cae9669`, Cross-Phase P12):** Coverage-Fenster ist jetzt
ein zweites Paar `cov_start, cov_end` aus neuem Helper `_session_bounds_iso(day_utc)`
(Berlin 09:00–17:30 via `zoneinfo.ZoneInfo("Europe/Berlin")`, end-shifted um
`RECORDER_LAG_TOLERANCE_MIN = 30` für den gemessenen 18-min-Recorder-Rückstand).
Die 5-Min-Gap-Schwelle bleibt unverändert (Phase-13 F3 „kein Loch mitten im Fenster").
Tests `test_assess_day_ok_with_session_only_bars`,
`test_assess_day_flags_gap_inside_session` und
`test_assess_day_tolerates_lagging_recorder_tail` pinnen das neue Fenster + die
Lag-Toleranz.

### Was v2 *nicht* ändert

- **PASS-Kriterien 1–7**: Wortlaut unverändert ggü. v1 — die Kriterien waren
  richtig, das Substrat war kaputt. Was sich ändert ist, dass die Kriterien jetzt
  erreichbar sind (K1 misst im Fenster, K4 misst die Session).
- **Erlaubte Operator-Ereignisse (a/b/c/d)**, **Watch-Items W1–W6**,
  **Vorregistrierte Werte** (alle Caps, Token-Budget, alle Arme ON, Universe ohne
  Wochenend, Rescue AUS, Promotion-Bridge ON) — wortgleich übernommen.
- **K1-Zähl-Schwelle** bleibt ≤ 2 je Dienst (1 baseline + 1 P17-Ausnahme).
- **K4-Schwelle** bleibt ≥ 8/10 ok-Tage.

### Watch-Item W4 (LS-Bars) — jetzt Akzeptanz, nicht mehr nur Watch

Mit J1 gefixt ist `bars.source='ls'` > 0 nach dem ersten Handelstag **append-only
belegbar** (`sqlite3 "file:data/bars.sqlite?mode=ro" "select count(*) from bars where
source='ls'"`). Das war v1-Watch-Item; v2 macht es nicht zum harten PASS-Kriterium
(K1–K7 sind unverändert), aber der Day-0-Verify-Posten in `PHASE16_E3_RUNBOOK_v2.md`
prüft es explizit als J7-Tabellen-Zeile „LS-Bars fließen" → **> 0 um 09:10 Berlin**.

## Vorregistrierte Werte

| Symbol | Wert | Bedeutung |
|---|---|---|
| **Tage** | 10 Handelstage | Mo–Fr (Berlin), keine Feiertage; End = Start + 10 Handelstage |
| **Account** | `demo` | IG-Demo-Konto, EUR (kein Live-Account, kein anderes Konto) |
| **max_trades** | 5 | pro Handelstag (`SchedulerConfig.max_trades_per_day` = 5) |
| **daily_loss_cap** | 1800 EUR | pro Handelstag (`SchedulerConfig.daily_loss_cap_eur` = 1800.0) |
| **Token-Budget** | 300 000 / Tag | `SchedulerConfig.daily_token_budget` = 300_000 (Plan §6 C3, Block C endgültig 2026-09-05) |
| **Vier Arme** | alle ON | `enable_shadow_schedule` + `enable_divergence_sampler` + `enable_bar_stream` + `enable_paper_debate` = **True** (Plan §1 P4, default ON, `--no-*` zum Abschalten) |
| **Universe** | ohne Wochenend | keine Epics mit `IX.D.SUN*` in `active` (Plan §6 B3, Demotion-Code endgültig) |
| **Rescue** | AUS | `enable_gap_rescue = False` unverändert (Plan §1 P6, Doppel-Sperre) |
| **Promotion-Bridge** | ON | `enable_instinct_promotion = True` (Plan §1 P5, Default ON), Gatter `instinct_n_min = 50` + Validator bleiben Code |

## PASS-Kriterien (AK15, alle 7 aus Plan §6 E2)

Jedes Kriterium hat **eine** append-only Messquelle. Der `--summary`-Output von
`scripts/autonomy_report.py` bewertet die PASS/FAIL-Zeile je Kriterium.

| # | Kriterium | Messquelle (append-only) | Regel |
|---|---|---|---|
| **1** | **kein Operator-Restart** im Fenster (eine P17-Ausnahme Backoff-KILL-Clear erlaubt) | `data/state/run_scheduler.log` Zeile `starting scheduler daemon` (timestamped, im **Berlin-Tagesfenster** gefiltert, J2) · `data/state/run_recorder.log` Zeile `[run_recorder] starting` · `data/state/run_discovery.log` Start-Zeile · `data/state/run_webui.log` Zeile `[run_webui] dashboard on` (J8: nur Wrapper-Pattern, kein uvicorn-Duplikat) | pro Dienst genau **1** Start-Zeile im Fenster (die vom E3-Start); P17-Ausnahme = 2 Start-Zeilen je Dienst erlaubt, **einmalig** (Backoff-KILL-Clear mit geloggtem Grund, Plan §1 P17) |
| **2** | **Dienste pro Handelstag aktiv** | Scheduler: ≥ 1 Event in `data/state/research_health.jsonl` am Tag · Recorder: ≥ 1 `bars`-Zeile `source='yf'` (oder `'ls'`/`'capital'`, je nach Verfügbarkeit) in `data/bars.sqlite` je Tag · Discovery: `max(instrument_source_availability.last_verified_utc)` wächst am Tag · WebUI: **Operator-Sichtung** (kein append-only Beleg existiert — ehrlich vorregistriert, Opus-Review §13 #6) | 3 von 3 automatisch + WebUI operator-gesichtet |
| **3** | **≥ 5 autonome Trades** im Fenster (open → close, beide innerhalb des Fensters) | `trade_outcomes` `status='CLOSED' AND provenance='autonomous' AND account='demo'` in `data/trading_bot.sqlite` (mode=ro, Tabelle ist append-only für unsere Schreibpfade) | Zahl ≥ 5 |
| **4** | **Heartbeat ok** an ≥ 8 / 10 Handelstagen | `data/state/research_health.jsonl` `measurement_heartbeat.ok` je Tag (append-only, eine Zeile pro Heartbeat-Tick); Coverage-Fenster Berlin 09:00–17:30 minus 30 min Recorder-Lag (J3 + J5) | ok-Tage ≥ 8 |
| **5** | **≤ 5 CRITICAL** in den 24 h nach jedem OPEN (A6) | `data/state/run_scheduler.log` `CRITICAL`-Zeilen im 24-h-Fenster ab jedem `trade_outcomes.open_ts` | max je Fenster ≤ 5 (Replay-verifiziert Mini-Session 26, A6 wartet auf Live-OPEN) |
| **6** | **Token-Budget nie vor 17:30 leer** | `data/state/llm_usage.json` Tages-Σ (Berlin-Tag wie `budget.py`) und Zeitpunkt des Erreichens von 300 k; Report **bricht ab**, wenn die Datei nicht parst oder ihre Zeilenzahl nicht wächst (Budget fällt sonst still offen, Opus-Review §13 #9) | 0 Tage, an denen das Budget vor 17:30 Berlin erschöpft ist |
| **7** | **Caps unverändert** im Fenster | `run_scheduler.log`-Start-Zeile muss enthalten: `max_trades=5` UND `daily_loss_cap=1800.0` (grep-Pin); `trade_outcomes.account='demo'` für jeden CLOSED-Trade | exakt einmal beim Start sichtbar; Caps dürfen nicht im Lauf geändert worden sein (kein Hotfix-Commit) |

### Was *nicht* als PASS zählt (ehrliche Ausschlüsse)

- **Profit / P&L** — kein Kriterium (Plan §1 P11). Das ist ein Autonomie-Test, kein Strategie-Audit.
- **`bars.source='ls' > 0`** — append-only, aber **kein** PASS-Kriterium. Watch-Item W4, mit J7-Day-0-Verify-Posten geprüft (Phase-13-Architektur: IG-Lightstreamer liefert den Live-Schwanz, aber ob er am Test-Tag live geht, hängt vom IG-Token ab, D1.2 Wrapper prüft das).
- **`instincts`-Tabelle mit Zeilen** — append-only, aber **kein** PASS-Kriterium. n≈10–20 Trades ≪ `instinct_n_min = 50` → Bridge promoted nichts (VETO 5 bleibt No-Op, by design, Plan §13 #8). Watch-Item W6.
- **WebUI-Aliveness** — kein append-only Beleg existiert; ehrlich vorregistriert als Operator-Sichtung (Opus-Review §13 #6).

## Erlaubte Operator-Ereignisse (P17)

Vorregistriert, gezählt, nie still:

| # | Ereignis | Wirkung auf PASS Kriterium 1 | Wirkung auf Lauf |
|---|---|---|---|
| **a** | **Backoff-KILL-Clear** (`data/state/KILL` mit `auto:backoff` nach 3 Zyklus-Exceptions, Plan §1 P17) | **einmalig** erlaubt: 2 Start-Zeilen je Dienst zählen als 1 (geloggter Grund + Root-Cause-Befund im Closeout); **zweites Mal = FAIL Kriterium 1** | Lauf geht weiter |
| **b** | **Reboot / Keyring-Relogin** (Desktop-Session verloren) | zählt als Intervention: FAIL Kriterium 1, **Lauf geht weiter** | Restart-Ritual (E3 Runbook) |
| **c** | **Daily-Loss-Cap trippt** (`daily_loss_cap_eur` erreicht) | **kein** Operator-Eingriff nötig; passiert autonom; **Tag zählt**, Lauf geht weiter, kein Trade am Rest des Tages | autonom |
| **d** | **`max_trades_per_day` erreicht** (5 Trades/Tag) | **kein** Operator-Eingriff; autonom; Tag zählt, Lauf geht weiter | autonom |

**Nicht erlaubt (jedes Vorkommen = FAIL Kriterium 1):**

- Manueller Restart eines Dienstes ohne Backoff-KILL-Vorbedingung
- Manueller Trade-Eingriff (Force-Trigger `ig_bot_force_trigger` aus dem Force-Trigger-Arm; Plan §1 P5 + root-CLAUDE Hard Rule 5 „Force-Trigger respektiert Daily PNL" — heute wegen daily_loss_cap=1800 ist ein Force-Trigger ohnehin gelockt, wenn PNL < 0; bei PNL ≥ 0 wäre der Operator-Eingriff eine FAIL-Verletzung)
- Hotfix-Commit auf Caps oder Arms während des Fensters
- DB-Repair außerhalb des E3-Runbooks

## Watch-Items (nicht PASS, aber zu beobachten)

| Watch | Was zu beobachten | Erwartung / Schwelle |
|---|---|---|
| **W1** | BUY-Bias | Alle autonomen Trades sind BUY (empirisch Phase-9-Live 8/8 BUY DAX, Plan §2.4 Live-DB). Wenn ein SELL-Trade auftaucht → Befund, nicht PASS-Verletzung. |
| **W2** | DAX-Only | Alle aktiven Epics außer Wochenend sind DAX (Phase-9-Live). Andere aktive Epics (FTSE, DOW, SPTRD, IBEX, AEX, MIB, STXE) wären Befund — sie sollen nach B3 + Universe-Refresh laufen, sind aber im aktiven Substrat unterrepräsentiert. |
| **W3** | 09:05-Breaker | `circuit open`-Zeilen im Zeitfenster 09:05–09:20 an Tag 1 = 0 (Plan §7 AK17 + C5). Wenn es doch auftritt → Befund (C5-Semantik greift nicht wie geplant), nicht PASS-Verletzung. |
| **W4** | LS-Bars | `bars.source='ls'` wächst ab Tag 1 (D1.2 Wrapper aktiv + J1 Thread-Fix). Wenn 0 nach 24 h → Befund (D1.2 nicht verdrahtet oder Broker-Token-Problem), nicht PASS-Verletzung. J7-Tagesposten prüft das. |
| **W5** | Zombie-Zahl | `[python] <defunct>` Prozesse. Erwartung ≤ 2 (Plan §2.3). Wenn > 5 über mehrere Tage → Befund (P14-D Sleep-Cap greift nicht). |
| **W6** | `min_evidence` vs. Trade-Zahl | Validator-Default `min_evidence` (Plan §9 #15) im Verhältnis zur autonomen Trade-Zahl. n ≈ 10–20 Trades ≪ `instinct_n_min = 50` → keine Promotion, VETO 5 bleibt No-Op; dokumentierter Befund (Bridge lebt, ist aber unter der Schwelle — per Plan §13 #8 erwartet). |

## Operator-Regel

> **Der Operator fasst während des Fensters nichts an außer dem täglichen
> `autonomy_report.py --day`-Report.** Täglich lesen reicht.
>
> **Die Desktop-Session bleibt eingeloggt** (Keyring braucht Desktop-Login — Phase-16-Opus-Review §13 #5; kein systemd-Unit, kein Cron, kein Auto-Reboot, `Automatic-Reboot` auskommentiert). Ein versehentlicher Reboot = Operator-Intervention (FAIL Kriterium 1), Lauf geht weiter.

## Aktiv-Block (vom Operator am E3-Restart-Tag auszufüllen, **bevor** die erste Start-Zeile im Log landet — AK13)

> **Eintragung, kein Edit** — der Mechanismus ist oben in der Einleitung dokumentiert.
> Diese Eintragung erfolgt **vor** dem ersten Service-Start und wird im selben Audit-Commit
> dokumentiert (entweder als Folge-Commit `phase16: docs -- E1-Aktiv-Block-Eintragung`
> mit dem genauen Start-Zeitstempel aus dem Log, oder als Notiz im Runbook — die
> AK13-Bedingung „Commit-Zeit < Start-Zeile im Log" muss in jedem Fall halten).

| Feld | Wert | Quelle |
|---|---|---|
| **Start (E3-Restart-Zeitstempel)** | _vom Operator zu füllen — der neue Lauf startet nach den J-Block-Fixes_ | `data/state/run_scheduler.log` erste Zeile `starting scheduler daemon` (Berlin-Tag, ISO 8601); Commit-Zeit des `phase16: docs -- E1-Aktiv-Block-Eintragung`-Audit-Commits, Restart erfolgt unmittelbar danach durch Operator |
| **Ende (Start + 10 Handelstage)** | _aus Start oben ableiten, Mo–Fr Berlin, keine Feiertage_ | `Start + 10 × Handelstag` |
| **Restart-Befehl** | `bash scripts/restart-services.sh start` | E3 Runbook v2 §3 (verbatim aus Plan §6 E3 S. 799-808) |
| **Operator-Anwesenheit bestätigt** | _vom Operator abzuhaken_ | Desktop-Session eingeloggt, Keyring erreichbar (Truncate der 7 Wrapper/Pre-Wrapper-Logs + Pflicht-SQL §1 v2 bereits durchgeführt) |
| **Operator-SQL-Audit pre-E3** | _vom Operator zu füllen — Epics + ts_utc der Ausführung_ | Pflicht-SQL §1 v2 aus Runbook; die 3 SUN*-Epics stehen aktuell auf `status='verified'` (2026-09-08 gemessen), Pflicht-SQL ist damit formal No-Op, Watch-Item V-5 |
| **J-Block-Fixes committet vor Aktiv-Block-Eintrag** | `669dde9` (J1) + `3969f8c` (J2 + J8) + `cae9669` (J3 + J5 Lag-Toleranz) + dieser Commit (v2) | `git log` zeigt alle vier Commits vor dem E1-Audit-Commit |

**Handelstage Berlin (zur Selbstverifikation):** Start-Datum eintragen, dann Mo–Fr ohne
Feiertage (Berlin) bis 10 Tage erreicht sind. Bei Feiertag dazwischen ist dieser Tag kein
Handelstag — `autonomy_report.py` zählt nur Mo–Fr ohne Feiertag als Handelstage-Verschiebung.

## Was diese Vorregistrierung *nicht* macht

- Sie **macht keine Aussagen** über Profit, Win-Rate, Sharpe, P&L.
- Sie **verbietet keine Strategie-Änderungen** im laufenden Code (Hotfix-Commits **sind**
  verboten, aber Strategie-Tuning ist im normalen Repo-Flow zulässig — das ist Phase-17-Material).
- Sie **misst keine Code-Qualität** — das ist Phase-17-Material.
- Sie **garantiert keine WebUI-Aliveness** — ehrlich als Operator-Sichtung vorregistriert.

## Cross-Refs

- **Plan-Session #21 (2026-09-08) Exec-Plan mit den drei Befunden + Fixes:** [`./PHASE16_F_EXEC_PLAN.md`](./PHASE16_F_EXEC_PLAN.md)
- **v1 (byte-identisch eingefroren, aktiv-Block zurückgesetzt):** [`./PHASE16_AUTONOMY_PREREGISTRATION.md`](./PHASE16_AUTONOMY_PREREGISTRATION.md)
- Plan §6 Block E Steps E1–E4 (S. 758–815): [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md)
- Plan §1 gelockte Entscheidungen P4, P5, P6, P7, P11, P17: ebd. S. 53–72
- Plan §7 Akzeptanzkriterien AK13 (Commit-Zeit < Start-Zeile), AK15 (7 Kriterien oben), AK16 (Closeout): ebd. S. 821–842
- Plan §8 Fehlgriffe (Reboot, Backoff-KILL, Restarts): ebd. S. 846–865
- Plan §11 Operator-Aktionen #5 (Restart), #6 (täglicher Report), #7 (Tag 10 Closeout): ebd. S. 913–924
- Plan §13 Opus-Review #5 (Supervision), #6 (WebUI-Aliveness unmessbar), #8 (Bridge unerreichbar im Test), #9 (Budget-Datei-Korruption): ebd. S. 935–947
- Phase-15-Vorgänger-Handover: [`../phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md`](../phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md)
