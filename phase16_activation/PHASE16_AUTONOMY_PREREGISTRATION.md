---
status: locked
purpose: Vorregistrierung des 2-Wochen-Autonomie-Tests (P11, Block E1). PASS-Kriterien,
  Konfiguration, Operator-Ereignisse, Watch-Items — **vor** dem E3-Restart committet
  und danach nicht geändert. Aktiv-Block (Start-/Endzeitstempel) wird vom Operator
  am E3-Restart-Tag ausgefüllt, **bevor** die erste Start-Zeile im Log landet.
read-when: Block-E-Ausführung (E2–E4); Audit, ob die Kriterien vor oder nach dem
  Lauf festgelegt wurden
detail: L3
up: ./CLAUDE.md
down:
  - ../docs/concepts/phase16_activation_plan.md   # 📕 §6 Block E Steps E1–E4 (Quelle), §7 AK13+AK15, §11 Operator-Aktionen
  - ../phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md    # 📕 Vorgänger (E1–E3 bleiben in Phase 16 zu schließen)
  - ./SESSIONS_ARCHIVE.md                         # 📦 Session-Block-Historie
updated: 2026-09-07
---

# PHASE16_AUTONOMY_PREREGISTRATION

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

## BLUF

Vorregistrierter 2-Wochen-Autonomie-Test (10 Handelstage, IG Demo). PASS = alle sieben
Kriterien erfüllt, gemessen aus **append-only** Quellen. Erlaubte Operator-Eingriffe:
einmalig Backoff-KILL-Clear, kein Reboot. Tagesreport aus `scripts/autonomy_report.py`
genügt; **nichts** sonst anfassen.

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
| **1** | **kein Operator-Restart** im Fenster (eine P17-Ausnahme Backoff-KILL-Clear erlaubt) | `data/state/run_scheduler.log` Zeile `starting scheduler daemon` · `data/state/run_recorder.log` Zeile `[run_recorder] starting` · `data/state/run_discovery.log` Start-Zeile · `data/state/run_webui.log` Zeile `Started server process` | pro Dienst genau **1** Start-Zeile im Fenster (die vom E3-Start); P17-Ausnahme = 2 Start-Zeilen je Dienst erlaubt, **einmalig** (Backoff-KILL-Clear mit geloggtem Grund, Plan §1 P17) |
| **2** | **Dienste pro Handelstag aktiv** | Scheduler: ≥ 1 Event in `data/state/research_health.jsonl` am Tag · Recorder: ≥ 1 `bars`-Zeile `source='yf'` (oder `'ls'`/`'capital'`, je nach Verfügbarkeit) in `data/bars.sqlite` je Tag · Discovery: `max(instrument_source_availability.last_verified_utc)` wächst am Tag · WebUI: **Operator-Sichtung** (kein append-only Beleg existiert — ehrlich vorregistriert, Opus-Review §13 #6) | 3 von 3 automatisch + WebUI operator-gesichtet |
| **3** | **≥ 5 autonome Trades** im Fenster (open → close, beide innerhalb des Fensters) | `trade_outcomes` `status='CLOSED' AND provenance='autonomous' AND account='demo'` in `data/trading_bot.sqlite` (mode=ro, Tabelle ist append-only für unsere Schreibpfade) | Zahl ≥ 5 |
| **4** | **Heartbeat ok** an ≥ 8 / 10 Handelstagen | `data/state/research_health.jsonl` `measurement_heartbeat.ok` je Tag (append-only, eine Zeile pro Heartbeat-Tick) | ok-Tage ≥ 8 |
| **5** | **≤ 5 CRITICAL** in den 24 h nach jedem OPEN (A6) | `data/state/run_scheduler.log` `CRITICAL`-Zeilen im 24-h-Fenster ab jedem `trade_outcomes.open_ts` | max je Fenster ≤ 5 (Replay-verifiziert Mini-Session 26, A6 wartet auf Live-OPEN) |
| **6** | **Token-Budget nie vor 17:30 leer** | `data/state/llm_usage.json` Tages-Σ (Berlin-Tag wie `budget.py`) und Zeitpunkt des Erreichens von 300 k; Report **bricht ab**, wenn die Datei nicht parst oder ihre Zeilenzahl nicht wächst (Budget fällt sonst still offen, Opus-Review §13 #9) | 0 Tage, an denen das Budget vor 17:30 Berlin erschöpft ist |
| **7** | **Caps unverändert** im Fenster | `run_scheduler.log`-Start-Zeile muss enthalten: `max_trades=5` UND `daily_loss_cap=1800.0` (grep-Pin); `trade_outcomes.account='demo'` für jeden CLOSED-Trade | exakt einmal beim Start sichtbar; Caps dürfen nicht im Lauf geändert worden sein (kein Hotfix-Commit) |

### Was *nicht* als PASS zählt (ehrliche Ausschlüsse)

- **Profit / P&L** — kein Kriterium (Plan §1 P11). Das ist ein Autonomie-Test, kein Strategie-Audit.
- **`bars.source='ls' > 0`** — append-only, aber **kein** PASS-Kriterium. Das ist Watch-Item, nicht Akzeptanz (Phase-13-Architektur: IG-Lightstreamer liefert den Live-Schwanz, aber ob er am Test-Tag live geht, hängt vom IG-Token ab, D1.2 Wrapper prüft das).
- **`instincts`-Tabelle mit Zeilen** — append-only, aber **kein** PASS-Kriterium. n≈10–20 Trades ≪ `instinct_n_min = 50` → Bridge promoted nichts (VETO 5 bleibt No-Op, by design, Plan §13 #8). Watch-Item.
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
| **W4** | LS-Bars | `bars.source='ls'` wächst ab Tag 1 (D1.2 Wrapper aktiv). Wenn 0 nach 24 h → Befund (D1.2 nicht verdrahtet oder Broker-Token-Problem), nicht PASS-Verletzung. |
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
| **Start (E3-Restart-Zeitstempel)** | `2026-09-07T21:58:27+02:00` | `data/state/run_scheduler.log` erste Zeile `starting scheduler daemon` (Berlin-Tag, ISO 8601); Commit-Zeit dieses Audit-Commits, Restart erfolgt unmittelbar danach durch Operator |
| **Ende (Start + 10 Handelstage)** | `2026-09-21` | `Start + 10 × Handelstag` (Mo–Fr, Berlin, keine Feiertage; Liste unten) |
| **Restart-Befehl** | `bash scripts/restart-services.sh start` | E3 Runbook v2 §3 (verbatim aus Plan §6 E3 S. 799-808) |
| **Operator-Anwesenheit bestätigt** | ✓ | Desktop-Session eingeloggt, Keyring erreichbar (Truncate der 7 Wrapper/Pre-Wrapper-Logs + Pflicht-SQL §1 v2 bereits durchgeführt) |
| **Operator-SQL-Audit pre-E3** | 3 Epics → `quarantined` um `2026-09-07T21:58:27+02:00` (`IX.D.SUNDAX.IGN.IP`, `IX.D.SUNDOW.IAE.IP`, `IX.D.SUNNAS.IAE.IP`, alle `checks_json.reason='weekend_market_pre_B3_cleanup'`) | Session #13 Pflicht-SQL §1 v2 (analog B2 Operator-Aktion Session #3); B3-Code-Commit `d82922e` Session #3 2026-09-05 wirkt forward-only, die 3 Epics waren 2026-09-04 vor B3 promoted |

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

- Plan §6 Block E Steps E1–E4 (S. 758–815): [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md)
- Plan §1 gelockte Entscheidungen P4, P5, P6, P7, P11, P17: ebd. S. 53–72
- Plan §7 Akzeptanzkriterien AK13 (Commit-Zeit < Start-Zeile), AK15 (7 Kriterien oben), AK16 (Closeout): ebd. S. 821–842
- Plan §8 Fehlgriffe (Reboot, Backoff-KILL, Restarts): ebd. S. 846–865
- Plan §11 Operator-Aktionen #5 (Restart), #6 (täglicher Report), #7 (Tag 10 Closeout): ebd. S. 913–924
- Plan §13 Opus-Review #5 (Supervision), #6 (WebUI-Aliveness unmessbar), #8 (Bridge unerreichbar im Test), #9 (Budget-Datei-Korruption): ebd. S. 935–947
- Phase-15-Vorgänger-Handover: [`../phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md`](../phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md)
