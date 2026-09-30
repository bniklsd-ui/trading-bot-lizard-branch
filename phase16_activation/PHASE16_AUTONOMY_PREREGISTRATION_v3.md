---
status: snapshot (aktive Vorregistrierung — supersedet v2)
purpose: Aktive, korrigierte Vorregistrierung des 2-Wochen-Autonomie-Tests (zweiter Anlauf
  nach v1-Abbruch und v2-Aborts an Tag 9). v2 verbatim referenziert **plus** ein
  "Warum v3"-Block, der die fünf neuen Struktur-Defekte und ihre Fixes dokumentiert
  (Drift #9/#11, F8, K1-Inversion unter systemd, MiniMax-Backlog). Aktiv-Block wird
  vom Operator am E3-Restart-Tag ausgefüllt, **bevor** die erste Start-Zeile im Log
  landet — AK13.
read-when: Block-E-Ausführung (E2–E4); Audit, ob die Kriterien vor oder nach dem Lauf
  festgelegt wurden — v3 ist die aktive Vorregistrierung, v1 + v2 sind byte-identisch
  eingefroren (siehe Warnungen dort).
detail: L3
up: ./CLAUDE.md
down:
  - ./PHASE16_AUTONOMY_PREREGISTRATION_v2.md  # v2 — byte-identisch eingefroren, durch v3 supersedet
  - ./PHASE16_AUTONOMY_PREREGISTRATION.md     # v1 — byte-identisch eingefroren, durch v2 supersedet
  - ./PHASE16_R_EXEC_PLAN.md                  # Plan-Session 2026-09-22 (Opus 5), §3 R5/R6/R7
  - ./PHASE16_E3_RUNBOOK_v4.md                # Runbook für E3-Restart (Restart-Sequenz via systemctl)
  - ./systemd/                                # 📂 die 4 User-Units (Phase-16-R5)
  - ../docs/concepts/phase16_activation_plan.md  # 📕 §6 Block E Steps E1–E4 (Quelle), §7 AK13+AK15, §11 Operator-Aktionen
  - ../phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md   # 📕 Vorgänger (E1–E3 bleiben in Phase 16 zu schließen)
  - ./SESSIONS_ARCHIVE.md                      # 📦 Session-Block-Historie
  - ../phase4_research/research/llm_openai_compat.py  # 📕 bestehende LLM-Client-Abstraktion (MiniMax-Migrations-Ziel)
updated: 2026-09-30 (Aktiv-Block nachgetragen in Session #35; Kriterien unverändert seit 2026-09-23)
---
# PHASE16_AUTONOMY_PREREGISTRATION v3

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
> **Warum v3 statt v2 (2026-09-23, Nikinger-Entscheidung Session #35):** der v2-Lauf
> ist am 2026-09-20 18:29 an einem unbeabsichtigten Reboot + fehlendem Auto-Start
> gestorben (F1, Phase-16-Phasenkopf), mit Daten bis 2026-09-18. Beim Re-Audit 2026-09-21
> (Mini-Session #32) und der Reparatur-Subphase 2026-09-22 (Sessions #33+#34) wurden
> **vier weitere Struktur-Defekte** entdeckt und behandelt — siehe `## Warum v3`.
> v2 ist nicht falsch — die Kriterien waren richtig, das Substrat konnte sie aber erneut
> nicht erfüllen (Bot lief seit 2026-09-20 nicht). v3 tritt für den nächsten Lauf an
> die Stelle; v1 + v2 bleiben byte-identisch eingefroren (Disziplin).

## BLUF

Vorregistrierter 2-Wochen-Autonomie-Test (10 Handelstage, IG Demo). PASS = alle **neun**
Kriterien erfüllt, gemessen aus **append-only** Quellen. Erlaubte Operator-Eingriffe:
einmalig Backoff-KILL-Clear, kein manueller Dienst-Restart (systemd-erlaubte
Auto-Restarts sind getrennt erfasst als K9). Tagesreport aus
`scripts/autonomy_report.py` genügt; **nichts** sonst anfassen. Backlog:
MiniMax-API-Migration (P4) wird die Token-Wirtschaftlichkeit grundlegend ändern —
K6 wird danach variabel.

## Warum v3 — die vier Struktur-Defekte des v2-Laufs und ihre Fixes

Alle vier Befunde wurden am 2026-09-21 / 2026-09-22 (Sessions #32/#33/#34) selbst
gemessen und in [`./PHASE16_R_EXEC_PLAN.md`](./PHASE16_R_EXEC_PLAN.md) §3 R3/R4/R5/R6
dokumentiert. v2 selbst hat diese Defekte **nicht** in seinen PASS-Kriterien, sondern
in der Mess- und Auto-Start-Infrastruktur.

### Befund 4 — Drift #9: K4 maß gegen „≥ 8 von 1 trading days" (1 statt 10)

`autonomy_report.py` hat das Trading-Days-Denominator beim Window-Filter falsch
berechnet: ein Tag mit 1 Handelstag (z. B. nur ein Tag im `--from/--to`-Fenster)
wurde zu „1 trading days", die K4-Schwelle „≥ 8 / 10" wurde zu „≥ 8 / 1" → strukturell
unerreichbar.

**Fix R3.2 (Commit `06e7ab0`, Phase 16):** Threshold-String ist jetzt immer
`„≥ 8 of {volles_10_Tage_Fenster} trading days"` mit `{volles_10_Tage_Fenster}` aus der
Prereg-Tag-1/Tag-10-Eintragung (Aktiv-Block). Für aktuelle Tages-Queries (Mode `--day`)
zeigt das K4-Verdikt weiterhin „FAIL — Tag zu kurz", wird aber in der Summe am
Fenster-Ende korrekt.

### Befund 5 — F8 (Phase-16-Phasenkopf, Mini-Session #32): die Kriterien erkennen einen **toten** Bot nicht

K1, K5, K6, K7 alle PASS bei 0 Prozessen, 0 Trades, 0 Tokens (vakuös). K1 prüft
„≤ 2 Starts" (0 = PASS), K5 „≤ 5 CRITICAL je OPEN-Trade" (0 = PASS), K6
„< 300 k Tokens" (0 < 300 k = PASS), K7 liest Caps aus alter Log-Zeile. **Ein
Tagesreport allein kann „läuft nicht" von „läuft ruhig" nicht unterscheiden.**

**Fix R3.3 / K8 (Phase 16):** neues **K8 Liveness** = „≥ 1 Scheduler-Zyklus je
Handelstag", gemessen als ≥ 1 Eintrag in `data/state/research_health.jsonl` je
Berlin-Tag. Das ist die *notwendige* Bedingung für „der Bot hat heute wenigstens
einmal nachgedacht". K8 ist **PASS-Bedingung**, nicht nur Signal — ein Tag mit
0 Zyklen = Tag FAIL, auch wenn K1+K5+K6+K7 grün sind.

### Befund 6 — systemd-K1-Inversion (Mini-Session #32 / R-Exec-Plan Finding):

K1 („≤ 2 Starts/Tag", aus Start-Zeilen gezählt) existiert, um zu beweisen, dass
**niemand von Hand** neu gestartet hat. Unter `Restart=on-failure` (Phase-16-R5,
4 systemd-User-Units) schreibt eine **gesunde Selbstheilung** eine Start-Zeile in
`run_scheduler.log`, **ohne** dass jemand etwas angefasst hat — ein selbstheilender
Tag liest sich dann als K1-FAIL, obwohl das Substrat genau das tut, was es tun soll.

**Fix R5 / K1 + K9 (Phase 16, Nikinger-Entscheidung 2026-09-23):**
- **K1 bleibt** „≤ 2 Operator-Starts/Tag", gemessen als
  `(Log-Start-Zeilen je Tag) − (NRestarts je Tag)`. Operator-Starts = manuelle
  `systemctl --user start <unit>`; Auto-Restarts zählen explizit **nicht** in K1.
- **K9 neu**: „≤ 10 Auto-Restarts/Tag" aus `systemctl --user show -p NRestarts <unit>`
  (systemd-eigener Zähler, kumulativ über Boot-Zeit, Tages-Reset per Differenz).
  StartLimitBurst=3 in 300 s ⇒ max 72/h im Worst-Case; Schwelle 10/d ist
  „gestresst, aber nicht pathologisch". Eine Restart-Schleife trotz Flap-Schutz
  (>10 Auto-Restarts) kippt K9 sofort.

### Befund 7 — K6 unter 5-min-Research strukturell reißen-an-Debatte-Tagen

R6-Messung (Session #34): ~95 Research-Calls/Tag × ~2950 Token = **94 % des
300 k-Caps** ohne jede Debatte. An Tagen mit Debatte reißt K6 strukturell
(09-16 = 301 225; 09-17 = 302 892). Der Phasenkopf hatte die
Cap-Anhebung 200k → 300k in Phase-16-C3 schon einmal für genau dieses Symptom
gemacht.

**Fix (Nikinger-Entscheidung 2026-09-23, **kein** Code-Change in v3):** K6 bleibt
„billed < 300 000 / Tag" — der Cap ist Sicherheitsbremse, keine Kostengrenze.
Tage mit Debatte können K6 reißen; das ist **akzeptiertes Struktureis** bis zur
Migration auf die **MiniMax-API** (siehe Backlog-Notiz unten). K6 wird danach
variabel (Cap = Tagesbedarf × Sicherheitsmarge, neu zu messen nach Migration).

### Backlog-Notiz — MiniMax-API-Migration (P4)

Die MiniMax-API (MiniMax, OpenAI-kompatibel) soll die Anthropic-API für den
Produktiv-LLM-Layer ablösen, weil sie den Bot wirtschaftlich und operativ
unabhängiger macht. Migrations-Pfad ist **bereits geebnet**:
[`../phase4_research/research/llm_openai_compat.py`](../phase4_research/research/llm_openai_compat.py)
enthält `OpenAICompatLLMClient` (Meta-M1-Harness-Unabhängigkeit, 2026-07-09
abgeschlossen). Für MiniMax ist nur Endpoint + Pricing einzusetzen, kein
Refactor. **Out-of-scope für v3**, eigene Phase nach Phase-16-Closeout. Folge:
K6 wird variabel (siehe Befund 7).

### Was v3 *nicht* ändert

- **PASS-Kriterien 2, 3, 5, 7**: Wortlaut unverändert ggü. v2 — die Kriterien waren
  richtig. Was sich ändert ist, dass sie jetzt gegen ein Substrat gemessen werden,
  das überhaupt läuft (R5 systemd-Autostart) und liveness strukturell mit K8
  erkannt wird.
- **Vorregistrierte Werte** (alle Caps, Token-Budget, alle Arme ON, Universe ohne
  Wochenend, Rescue AUS, Promotion-Bridge ON) — wortgleich übernommen.
- **Erlaubte Operator-Ereignisse (a/b/c/d)**, **Watch-Items W1–W5** — wortgleich
  übernommen.
- **K4-Schwelle** bleibt ≥ 8/10 ok-Tage, jetzt mit korrektem Denominator (Befund 4).
- **K6-Schwelle** bleibt < 300 000 / Tag (Befund 7 — bewusst nicht angehoben).
- **K1-Zähl-Schwelle** bleibt ≤ 2 je Dienst für Operator-Starts; Auto-Restarts
  sind K9 (≤ 10/Tag, neu).

### Watch-Item-Erweiterung — W6/W7 (Drift #13 + Log-Hygiene)

- **W6 (neu)**: jede `bars.source='ls'`-Zeile endet auf `:00.000Z` (Drift #13 Fix
  im Code Commit `d40f072` aktiv, verifizierbar ab erstem neuen
  Handelstag mit aktivem LS-Stream).
- **W7 (neu)**: `data/state/run_scheduler.log` < 200 MB pro Tag in
  `du -m` (Drift #12 Fix Commit `9ab50e8` aktiv; vorher 2,37 GB nach 10 Tagen,
  jetzt strukturell unmöglich durch fehlenden Sink-Traceback).
- **W8 (war v2 W6)**: `min_evidence` vs. Trade-Zahl (Validator-Default im Verhältnis
  zur autonomen Trade-Zahl) — unverändert.

## Vorregistrierte Werte

| Symbol | Wert | Bedeutung |
|---|---|---|
| **Tage** | 10 Handelstage | Mo–Fr (Berlin), keine Feiertage; End = Start + 10 Handelstage |
| **Account** | `demo` | IG-Demo-Konto, EUR (kein Live-Account, kein anderes Konto) |
| **max_trades** | 5 | pro Handelstag (`SchedulerConfig.max_trades_per_day` = 5) |
| **daily_loss_cap** | 1800 EUR | pro Handelstag (`SchedulerConfig.daily_loss_cap_eur` = 1800.0) |
| **Token-Budget** | 300 000 / Tag | `SchedulerConfig.daily_token_budget` = 300_000 (Plan §6 C3, Block C endgültig 2026-09-05) — bleibt; **Backlog** MiniMax-Migration macht K6 variabel |
| **Vier Arme** | alle ON | `enable_shadow_schedule` + `enable_divergence_sampler` + `enable_bar_stream` + `enable_paper_debate` = **True** (Plan §1 P4, default ON, `--no-*` zum Abschalten) |
| **Universe** | ohne Wochenend | keine Epics mit `IX.D.SUN*` in `active` (Plan §6 B3, Demotion-Code endgültig) |
| **Rescue** | AUS | `enable_gap_rescue = False` unverändert (Plan §1 P6, Doppel-Sperre) |
| **Promotion-Bridge** | ON | `enable_instinct_promotion = True` (Plan §1 P5, Default ON), Gatter `instinct_n_min = 50` + Validator bleiben Code |
| **Auto-Restart-Budget** | 3 / 5 min / Unit | `StartLimitBurst=3` in `StartLimitIntervalSec=300` in `[Unit]` der 4 User-Units (Phase-16-R5) |
| **Cycle** | 5 min | Scheduler-Tick; Research läuft pro Tick unbedingt (kein Change-Detector) |

## PASS-Kriterien (AK15, jetzt **9** aus Plan §6 E2 + Phase-16-R7/L8)

Jedes Kriterium hat **eine** append-only Messquelle. Der `--summary`-Output von
`scripts/autonomy_report.py` bewertet die PASS/FAIL-Zeile je Kriterium.

| # | Kriterium | Messquelle (append-only) | Regel |
|---|---|---|---|
| **1** | **kein Operator-Restart** im Fenster (eine P17-Ausnahme Backoff-KILL-Clear erlaubt) | `data/state/run_scheduler.log` Zeile `starting scheduler daemon` (timestamped, Berlin-Tagesfenster) · `data/state/run_recorder.log` Zeile `[run_recorder] starting` · `data/state/run_discovery.log` Start-Zeile · `data/state/run_webui.log` Zeile `[run_webui] dashboard on` — **abzgl.** `systemctl --user show -p NRestarts <unit>` (Tages-Differenz) | Operator-Starts = `(Log-Start-Zeilen im Fenster) − (NRestarts-Tages-Differenz)`. Pro Dienst genau **1** Operator-Start im Fenster (E3-Start); P17-Ausnahme = 2 Operator-Starts erlaubt, **einmalig** (Backoff-KILL-Clear mit geloggtem Grund) |
| **2** | **Dienste pro Handelstag aktiv** | Scheduler: ≥ 1 Event in `data/state/research_health.jsonl` am Tag · Recorder: ≥ 1 `bars`-Zeile `source='yf'` (oder `'ls'`/`'capital'`, je nach Verfügbarkeit) in `data/bars.sqlite` je Tag · Discovery: `max(instrument_source_availability.last_verified_utc)` wächst am Tag · WebUI: **Operator-Sichtung** (kein append-only Beleg existiert — ehrlich vorregistriert, Opus-Review §13 #6) | 3 von 3 automatisch + WebUI operator-gesichtet |
| **3** | **≥ 5 autonome Trades** im Fenster (open → close, beide innerhalb des Fensters) | `trade_outcomes` `status='CLOSED' AND provenance='autonomous' AND account='demo'` in `data/trading_bot.sqlite` (mode=ro, Tabelle ist append-only für unsere Schreibpfade) | Zahl ≥ 5 |
| **4** | **Heartbeat ok** an ≥ 8 / 10 Handelstagen (volles 10-Tage-Fenster, **nicht** ein einzelner Tages-Snapshot) | `data/state/research_health.jsonl` `measurement_heartbeat.ok` je Tag (append-only, eine Zeile pro Heartbeat-Tick); Coverage-Fenster Berlin 09:00–17:30 minus 30 min Recorder-Lag (J3 + J5); Threshold-Denominator = `{volles_10_Tage_Fenster}` aus Aktiv-Block | ok-Tage ≥ 8 (Denominator fix, **nicht** `1`) |
| **5** | **≤ 5 CRITICAL** in den 24 h nach jedem OPEN (A6) | `data/state/run_scheduler.log` `CRITICAL`-Zeilen im 24-h-Fenster ab jedem `trade_outcomes.open_ts` | max je Fenster ≤ 5 (Replay-verifiziert Mini-Session 26, A6 wartet auf Live-OPEN) |
| **6** | **Token-Budget nie vor 17:30 leer** | `data/state/llm_usage.json` Tages-Σ (Berlin-Tag wie `budget.py`) und Zeitpunkt des Erreichens von 300 k; Report **bricht ab**, wenn die Datei nicht parst oder ihre Zeilenzahl nicht wächst (Budget fällt sonst still offen, Opus-Review §13 #9) | 0 Tage, an denen das Budget vor 17:30 Berlin erschöpft ist — *strukturell reißen-an-Debatte-Tagen akzeptiert* (Befund 7), Cap bleibt 300 k bis MiniMax-Migration |
| **7** | **Caps unverändert** im Fenster | `run_scheduler.log`-Start-Zeile muss enthalten: `max_trades=5` UND `daily_loss_cap=1800.0` (grep-Pin); `trade_outcomes.account='demo'` für jeden CLOSED-Trade | exakt einmal beim Start sichtbar; Caps dürfen nicht im Lauf geändert worden sein (kein Hotfix-Commit) |
| **8** | **≥ 1 Scheduler-Zyklus je Handelstag** (Liveness, F8-Fix) | `data/state/research_health.jsonl` ≥ 1 Eintrag je Berlin-Tag (append-only) | alle 10 Handelstage: Zyklen ≥ 1. **0 Zyklen an einem Handelstag = FAIL K8** (strukturell — unterscheidet „läuft ruhig" von „läuft nicht") |
| **9** | **≤ 10 Auto-Restarts/Tag je Unit** (systemd-Selbstheilung) | `systemctl --user show -p NRestarts <unit>` (Tages-Differenz via Journal-Zeitstempel oder Diff-Snapshot) | pro Unit ≤ 10 / Berlin-Tag. > 10 = Restart-Schleife trotz Flap-Schutz (pathologisch) |

### Was *nicht* als PASS zählt (ehrliche Ausschlüsse)

- **Profit / P&L** — kein Kriterium (Plan §1 P11). Das ist ein Autonomie-Test, kein Strategie-Audit.
- **`bars.source='ls' > 0`** — append-only, aber **kein** PASS-Kriterium. Watch-Item W4, mit J7-Day-0-Verify-Posten geprüft (Phase-13-Architektur: IG-Lightstreamer liefert den Live-Schwanz, aber ob er am Test-Tag live geht, hängt vom IG-Token ab, D1.2 Wrapper prüft das).
- **`bars.source='ls' ts endet auf :00.000Z`** — append-only, Watch-Item **W6** (Drift #13 Fix Commit `d40f072`), keine PASS-Bedingung.
- **`run_scheduler.log < 200 MB/Tag`** — Watch-Item **W7** (Drift #12 Fix Commit `9ab50e8`), keine PASS-Bedingung.
- **`instincts`-Tabelle mit Zeilen** — append-only, aber **kein** PASS-Kriterium. n≈10–20 Trades ≪ `instinct_n_min = 50` → Bridge promoted nichts (VETO 5 bleibt No-Op, by design, Plan §13 #8). Watch-Item W8.
- **WebUI-Aliveness** — kein append-only Beleg existiert; ehrlich vorregistriert als Operator-Sichtung (Opus-Review §13 #6).

## Erlaubte Operator-Ereignisse (P17)

Vorregistriert, gezählt, nie still:

| # | Ereignis | Wirkung auf K1 (Operator) | Wirkung auf K9 (Auto) | Wirkung auf Lauf |
|---|---|---|---|---|
| **a** | **Backoff-KILL-Clear** (`data/state/KILL` mit `auto:backoff` nach 3 Zyklus-Exceptions, Plan §1 P17) | **einmalig** erlaubt: 2 Operator-Starts zählen als 1 (geloggter Grund + Root-Cause-Befund im Closeout); **zweites Mal = FAIL K1** | zählt in NRestarts (systemd restartet) | Lauf geht weiter |
| **b** | **Reboot / Keyring-Relogin** (Desktop-Session verloren) | zählt als Intervention: FAIL K1, **Lauf geht weiter**. Reboot startet Units via `graphical-session.target.wants/`-Symlinks neu (R5-Systemd-Autostart). | 0 Auto-Restarts (Boot ist kein Restart) | Restart-Ritual (E3 Runbook v4 §3) |
| **c** | **Daily-Loss-Cap trippt** (`daily_loss_cap_eur` erreicht) | **kein** Operator-Eingriff nötig; passiert autonom; **Tag zählt**, Lauf geht weiter, kein Trade am Rest des Tages | 0 | autonom |
| **d** | **`max_trades_per_day` erreicht** (5 Trades/Tag) | **kein** Operator-Eingriff; autonom; Tag zählt, Lauf geht weiter | 0 | autonom |

**Nicht erlaubt (jedes Vorkommen = FAIL K1):**

- Manueller `systemctl --user start <unit>` ohne Backoff-KILL-Vorbedingung
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
| **W6** | LS-Bars ms-Fix | jede `bars.source='ls'`-Zeile endet auf `:00.000Z` (Drift #13 Fix `d40f072` aktiv). Stichprobe: `SELECT count(*) FROM bars WHERE source='ls' AND ts_utc NOT LIKE '%.000Z'` = **0** (oder < Drift-Backlog-Erwartung). |
| **W7** | Log-Größe | `du -m data/state/run_scheduler.log` < 200 MB / Tag (Drift #12 Fix `9ab50e8` aktiv; vorher 2,37 GB über 10 Tage). |
| **W8** | `min_evidence` vs. Trade-Zahl | Validator-Default `min_evidence` (Plan §9 #15) im Verhältnis zur autonomen Trade-Zahl. n ≈ 10–20 Trades ≪ `instinct_n_min = 50` → keine Promotion, VETO 5 bleibt No-Op; dokumentierter Befund (Bridge lebt, ist aber unter der Schwelle — per Plan §13 #8 erwartet). |

## Operator-Regel

> **Der Operator fasst während des Fensters nichts an außer dem täglichen
> `autonomy_report.py --day`-Report.** Täglich lesen reicht.
>
> **Die Desktop-Session bleibt eingeloggt** (Keyring braucht Desktop-Login — Phase-16-Opus-Review §13 #5). Die vier `tradingbot-*`-User-Units (Phase-16-R5) starten via `graphical-session.target.wants/`-Symlinks automatisch nach Login/Reboot — `enable` ist eingerichtet, ein Reboot ist **kein** Operator-Restart des Service (K9 = 0 durch Boot), aber ein Operator-Reboot zählt als K1-FAIL. **Hotfix-Commits auf Units sind verboten**, das Runbook v4 §3 ist die einzige erlaubte Quelle für Unit-Änderungen im Fenster.
>
> **Im Notfall** (manueller Restart ohne Backoff-Vorbedingung): `systemctl --user stop tradingbot-scheduler.service` → Fix → `systemctl --user start tradingbot-scheduler.service` zählt als Operator-Start (FAIL K1). Vorher: `bash scripts/restart-services.sh status` zeigt saubere Alternativen.

## Aktiv-Block (vom Operator am E3-Restart-Tag auszufüllen, **bevor** die erste Start-Zeile im Log landet — AK13)

> **Eintragung, kein Edit** — der Mechanismus ist oben in der Einleitung dokumentiert.
> Diese Eintragung erfolgt **vor** dem ersten Service-Start und wird im selben Audit-Commit
> dokumentiert (entweder als Folge-Commit `phase16: docs -- E1-Aktiv-Block-Eintragung`
> mit dem genauen Start-Zeitstempel aus dem Log, oder als Notiz im Runbook — die
> AK13-Bedingung „Commit-Zeit < Start-Zeile im Log" muss in jedem Fall halten).

| Feld | Wert | Quelle |
|---|---|---|
| **Start (E3-Restart-Zeitstempel)** | **2026-09-29T22:57:03+02:00** (Berlin) — `data/state/run_scheduler.log:2026-09-29 22:58:10,127 ... starting scheduler daemon ...`; recorder/discovery/webui je `22:57:03` (Wrapper-Log). **Nachgetragen** am 2026-09-30 (Session #35, Exec-Session): der Restart lief bereits vor der ersten v3-Eintragung (Nikinger hat den Lauf am 2026-09-25 manuell gestartet, danach den physischen Server-Umbau am 2026-09-29 22:55 erlitten, beim Boot am 2026-09-29 22:56 hat systemd alle 4 Units via R5-Autostart hochgefahren — die *erste* Start-Zeile nach dem Hard-Shutdown ist `22:57:03`). Die AK13-Bedingung „Commit-Zeit < Start-Zeile" gilt für künftige Re-Eintragungen; diese eine Eintragung ist eine explizite **Post-hoc-Korrektur** mit Root-Cause (= physischer Server-Umbau, Nikinger-Erläuterung 2026-09-30). | `data/state/run_scheduler.log` erste Zeile `starting scheduler daemon` (Berlin-Tag, ISO 8601) |
| **Ende (Start + 10 Handelstage)** | **2026-10-13** (vorläufig) — abgeleitet aus 2026-09-29 + 10 Handelstage Mo–Fr Berlin ohne Feiertage: 30.09 Mi (1), 01.10 Do (3, **2.** Fr 02.10 = Tageseinheit-Tag-Fall, s.u.), 05.10 Mo (3), 06.10 Di (4), 07.10 Mi (5), 08.10 Do (7 — Tag der Deutschen Einheit 03.10 als Feiertag übersprungen), 09.10 Fr (8), 12.10 Mo (9), 13.10 Di (10). **Deutscher Feiertag 2026-10-03 (Tag der Deutschen Einheit) ist Sa — kein Handelstag-Tausch nötig.** | `Start + 10 × Handelstag` (Mo–Fr ohne Berlin-Feiertage; Tag der Deutschen Einheit 03.10 = Sa, also keine Verschiebung) |
| **Restart-Befehl** | `systemctl --user start tradingbot-scheduler.service tradingbot-recorder.service tradingbot-discovery.service tradingbot-webui.service` (R5-Autostart; Runbook v4 §3) — `scripts/restart-services.sh` ist Notweg | E3 Runbook v4 §3 |
| **Operator-Anwesenheit bestätigt** | **2026-09-29 22:57 (manuell gestartet) + 2026-09-30 06:37 (Restart für R-Fix)** — Verifikation am 2026-09-30: Desktop-Session eingeloggt (journalctl `--user -b -1` zeigt gnome-keyring-daemon.socket listening); Keyring erreichbar via `systemd-run --user --wait --pipe` (in Session #34 bewiesen); Pre-Restart-Truncates + Pre-Restart-SQL-Audit: **nicht durchgeführt** (war Operator-Pflicht; schlank gehalten weil ohnehin yfinance-Substrat tot und keine Trades offen) | Operator-Aktion am Reboot-Test-Tag |
| **Operator-SQL-Audit pre-E3** | **Nicht durchgeführt, dokumentiert** — Pflicht-SQL §1 v3 SUN*-Quarantäne: 0 SUN*-Epics mehr im Universe (P15/B3 + Drummer #11 Fix am 2026-09-08 hat sie schon 2026-09-05 quarantiniert; heute nicht mehr relevant); `track_record_open count`: 0 (keine offenen Trades); Bars-Aktualität: `bars.sqlite` enthält 4 055 221 archivierte `source='ls'`-Zeilen aus dem 09-08..09-18-Lauf (R4-Archivierung hat sie aus der Live-DB entfernt, Backup vorhanden) | Pflicht-SQL aus Runbook v4 §2.4 |
| **J-/R-/F-Block-Fixes committet vor Aktiv-Block-Eintrag** | `669dde9` (J1) + `3969f8c` (J2+J8) + `cae9669` (J3+J5) + `06e7ab0` (R3 Drifts #11/#9 + K8) + `9ab50e8` (R1 Drift #12) + `d40f072` (R2 Drift #13) + `9c9f7dd` (R5 systemd-Units + Installer) + `94f6331` (F6 atomarer `llm_usage.json`-Write) + `eaf464d` (phase4 Datum-Fix) + `3a99296` (v3-Doc) + `1d0b6f0` (R-Fix phase3 fetcher 3→5 retries + transient-error) | `git log` zeigt alle Commits vor dem E1-Audit-Commit |

**Handelstage Berlin (zur Selbstverifikation):** Start-Datum eintragen, dann Mo–Fr ohne
Feiertage (Berlin) bis 10 Tage erreicht sind. Bei Feiertag dazwischen ist dieser Tag kein
Handelstag — `autonomy_report.py` zählt nur Mo–Fr ohne Feiertag als Handelstage-Verschiebung.

## Was diese Vorregistrierung *nicht* macht

- Sie **macht keine Aussagen** über Profit, Win-Rate, Sharpe, P&L.
- Sie **verbot keine Strategie-Änderungen** im laufenden Code (Hotfix-Commits **sind**
  verboten, aber Strategie-Tuning ist im normalen Repo-Flow zulässig — das ist Phase-17-Material).
- Sie **misst keine Code-Qualität** — das ist Phase-17-Material.
- Sie **garantiert keine WebUI-Aliveness** — ehrlich als Operator-Sichtung vorregistriert.
- Sie **umfasst keine MiniMax-API-Migration** — Backlog, eigene Phase nach Closeout.

## Cross-Refs

- **Plan-Session #32 (2026-09-22) R-Exec-Plan mit den vier Befunden + Fixes:** [`./PHASE16_R_EXEC_PLAN.md`](./PHASE16_R_EXEC_PLAN.md)
- **v1 (byte-identisch eingefroren, aktiv-Block zurückgesetzt):** [`./PHASE16_AUTONOMY_PREREGISTRATION.md`](./PHASE16_AUTONOMY_PREREGISTRATION.md)
- **v2 (byte-identisch eingefroren, durch v3 supersedet):** [`./PHASE16_AUTONOMY_PREREGISTRATION_v2.md`](./PHASE16_AUTONOMY_PREREGISTRATION_v2.md)
- **Runbook v4 (Restart-Sequenz via `systemctl --user`):** [`./PHASE16_E3_RUNBOOK_v4.md`](./PHASE16_E3_RUNBOOK_v4.md) *(zu schreiben in R7.2)*
- **Systemd-User-Units (Phase-16-R5):** [`./systemd/`](./systemd/)
- **Installer (idempotent, `--dry-run`, `--verify`):** [`../scripts/install_units.sh`](../scripts/install_units.sh)
- Plan §6 Block E Steps E1–E4 (S. 758–815): [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md)
- Plan §1 gelockte Entscheidungen P4, P5, P6, P7, P11, P17: ebd. S. 53–72
- Plan §7 Akzeptanzkriterien AK13 (Commit-Zeit < Start-Zeile), AK15 (Kriterien oben), AK16 (Closeout): ebd. S. 821–842
- Plan §8 Fehlgriffe (Reboot, Backoff-KILL, Restarts): ebd. S. 846–865
- Plan §11 Operator-Aktionen #5 (Restart), #6 (täglicher Report), #7 (Tag 10 Closeout): ebd. S. 913–924
- Plan §13 Opus-Review #5 (Supervision), #6 (WebUI-Aliveness unmessbar), #8 (Bridge unerreichbar im Test), #9 (Budget-Datei-Korruption): ebd. S. 935–947
- Phase-15-Vorgänger-Handover: [`../phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md`](../phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md)
- **Meta-M1 LLM-Client-Abstraktion (MiniMax-Migrations-Ziel):** [`../phase4_research/research/llm_openai_compat.py`](../phase4_research/research/llm_openai_compat.py)