---
status: locked
purpose: Operator-Runbook für Phase-16-Block-E-Schritt E3 — Restart des Schedulers + die
  2-Wochen-Tagesroutine bis Closeout. Committet **vor** dem ersten Service-Start;
  danach nicht geändert (Korrekturen nur als neues, datiertes Supersede-Doc). Aus
  Plan §6 E3 S. 797–808 + Plan §11 Operator-Aktionen #5/#6/#7 + Session-#11-Watch-Items
  (K1-Timestamp-Truncate, Hybrid-Test-Ansatz, Staffelung) zu einem Operator-Pfad
  zusammengezogen.
read-when: am E3-Restart-Tag (Tag 0) und täglich während des 2-Wochen-Fensters;
  Audit, was der Operator mechanisch tut vs. lassen muss
detail: L3
up: ./CLAUDE.md
down:
  - ./PHASE16_AUTONOMY_PREREGISTRATION.md    # 📕 PASS-Kriterien + vorregistrierte Werte (zwingend vorher lesen)
  - ../docs/concepts/phase16_activation_plan.md   # 📕 §6 E3 (Quelle, S. 797–808), §11 #5/#6/#7
  - ./scripts/autonomy_report.py             # 🔧 der tägliche Tages-/Summary-Report (K1–K7)
  - ./SESSIONS_ARCHIVE.md                    # 📦 Session-Historie (E1/E2/E3-Sessions)
updated: 2026-09-07
---

# PHASE16_E3_RUNBOOK — Operator-Pfad für den 2-Wochen-Autonomie-Test

> **Dieses Runbook ist der einzige Pfad, den der Operator mechanisch ab Tag 0 geht.**
> Vorregistrierungs-Disziplin (siehe `PHASE16_AUTONOMY_PREREGISTRATION.md`): ist
> committet **vor** dem ersten Service-Start, und nicht editierbar nach Tag 0. Wenn
> etwas fehlt: neue, datierte, supersedende Datei mit Grund — niem ein Edit hier.
>
> **Was dieses Runbook macht:** macht die Plan-§6-E3-Bash-Stufen (4 Zeilen, 797–808)
> zu einem geschlossenen Pfad Pre-Flight → Restart → Day-0-Checks → Tagesroutine →
> Trigger-Bedingungen. Operator-Lesung ist das einzige, was zählt — die Phasen-Head-
> Empfehlung, die Diagnostik-Datenquellen und die Verzweigung in die Exec-Session
> sind explizit.

---

## 0 · BLUF

`bash scripts/restart-services.sh start` (mit Pre-Flight davor und Day-0-Checks danach)
reicht aus, um den 2-Wochen-Autonomie-Test strukturell zu starten. Täglich
`scripts/autonomy_report.py --day` lesen. Bei Auffälligkeit die in §5 gelisteten
Trigger-Bedingungen prüfen — die Exec-Session kommt nur, wenn ein Trigger greift.

---

## 1 · Pre-Flight (VOR dem ersten `start`)

> Dauer: ≤ 5 min, mechanisch. Wenn etwas nicht hält → **nicht starten**, stattdessen
> Exec-Session rufen (siehe §5 Trigger-Bedingungen).

### 1.1 — Liveness-Check (heute = 4 Dienste tot seit B2-Apply, Plan §6 E3)

```bash
bash scripts/restart-services.sh status
```

Erwartung: **alle 4 tot** (`recorder`, `discovery`, `scheduler`, `webui` jeweils "dead").
Wenn ein Dienst lebt: einzeln stoppen oder einmal `bash scripts/restart-services.sh
restart --dry-run` previewen, dann `restart`. Wenn nach `restart` weiterhin ein
Dienst lebt → Exec-Session, kein Operator-Workaround.

### 1.2 — Schema-Floor 9 verifizieren (AK4)

```bash
sqlite3 data/trading_bot.sqlite "SELECT name FROM sqlite_master WHERE type='table'
  AND name IN ('instincts','_schema_version');"
sqlite3 data/trading_bot.sqlite "PRAGMA user_version;"
```

Erwartung: beide Zeilen antworten (`instincts` existiert, `user_version` = 9).
Wenn `_schema_version`-Tabelle leer oder `user_version != 9` → **nicht starten**;
B2 wurde nicht (oder unvollständig) angewendet; Exec-Session.

### 1.3 — Keyring erreichbar (Desktop-Session eingeloggt)

```bash
phase1_broker_wrapper/.venv/bin/python -c "
from broker_wrapper.credentials import get_credential
print('cst:', (get_credential('cst') or '')[:8] + '...')
print('token:', (get_credential('demo_token') or get_credential('token') or '')[:8] + '...')
"
```

Erwartung: beide Zeilen drucken je ≥ 8 Zeichen. Wenn eine Zeile `CredentialNotFoundError`
wirft oder leer bleibt → Desktop-Session war / ist nicht eingeloggt; **Login wiederholen**,
dann erneut prüfen. Wenn nach Relogin immer noch leer → Exec-Session (Keyring kaputt).

> **Hard Rule 1 (root-CLAUDE.md):** Credentials werden **nie** in Dateien geschrieben,
> **nie** ins `.env`, **nie** ins Log. Die `print()` oben gibt nur die ersten 8 Zeichen
> aus — das ist ein Fingerprint, kein Volltext.

### 1.4 — K1-Log-Truncate (Session-#11-Watch-Item)

Die Wrapper-Zeilen `[run_X] starting …` haben **keinen** Timestamp-Prefix und werden
vom `autonomy_report.py` als **full-file-count** ausgewertet — d. h. jede vor-E3-
geschriebene Start-Zeile zählt mit und macht Kriterium 1 sofort FAIL. Einmalig truncaten:

```bash
truncate -s 0 data/state/run_recorder.log \
          data/state/run_discovery.log \
          data/state/run_webui.log
```

`run_scheduler.log` **nicht** truncaten — die `scheduler.run`-Python-Logger-Zeilen
(`starting scheduler daemon (account=…, max_trades=…, daily_loss_cap=…, cycle=…min).`)
haben Timestamp-Prefix (default `basicConfig`-Format `asctime levelname name: message`),
`autonomy_report.py` filtert dort präzise.

> **Implikation:** ab Tag 0 hat jeder der 3 getruncten Logs **genau eine** Start-Zeile
> (vom E3-Start). Bei einem späteren P17-erlaubten Backoff-KILL-Clear ⇒ exakt 2 Zeilen
> (PASS, einmalig erlaubt). Bei einem späteren Reboot ⇒ 2+ Zeilen (FAIL Kriterium 1,
> Plan §1 P17 / Prereg §Erlaubte Operator-Ereignisse a).

### 1.5 — Datenbank-Health (vorhanden, nicht gelockt)

```bash
sqlite3 data/bars.sqlite "SELECT count(*), source FROM bars GROUP BY source;" 2>&1 | head -10
sqlite3 data/trading_bot.sqlite "SELECT count(*) FROM trade_outcomes;" 2>&1
```

Erwartung: Bars nach `source` gruppiert (heute `yf`/`ls`/`capital`, ≥ 1 Zeile je
etablierter Quelle). Wenn `database is locked` → vorigen Reader (`mode=ro`-WebUI
zuletzt) lebt noch, kurz warten oder `restart-services.sh status` prüfen.

### 1.6 — Akten-Vermerk im Preregistrierungs-Doc (AK13)

Im `PHASE16_AUTONOMY_PREREGISTRATION.md`-Aktiv-Block das Feld **Start (E3-Restart-
Zeitstempel)** mit dem genauen Zeitpunkt eintragen, **bevor** die erste Start-Zeile
im Log landet. Das ist eine **Eintragung**, kein Edit (im Prereg-Doc explizit
dokumentiert). Format: Berlin, ISO 8601, Sekunden-genau. **Anschließend** Commit
`phase16: docs -- E1-Aktiv-Block-Eintragung` mit dem Zeitstempel.

---

## 2 · Restart-Sequenz (verbatim aus Plan §6 E3)

```bash
bash scripts/restart-services.sh start

# 30 s warten, dann verifizieren
sleep 30
cat /proc/$(pgrep -f "python -m scheduler.run")/cmdline | tr '\0' ' '
#   erwartet: keine --enable-* oder --no-* Flags (D1 hat Defaults geflippt,
#   die Flags existieren nicht mehr — volles Profil = leeres argv nach dem Modul)

grep "starting scheduler daemon" data/state/run_scheduler.log | tail -1
#   erwartet: genau 1 Zeile mit timestamp-Prefix und der Caps-Zeile
#   "starting scheduler daemon (account=demo, max_trades=5, daily_loss_cap=1800.0, cycle=5min)."
#   Das ist die K7-Pin-Zeile (Prereg Kriterium 7, verbatim).
```

> **Reihenfolge** (`restart-services.sh` startet in dieser Order, sequenziell mit
> 2 s Settle-Sleep): Recorder → Discovery → Scheduler → WebUI. Erst Scheduler hat
> den Keyring-Preflight; wenn der Preflight failt ⇒ WebUI startet trotzdem (liest
> nur DB, kein Broker), aber Scheduler ist tot ⇒ **kein** Trading, nur Beobachtung.

---

## 3 · Day-0-Checks Timeline

> Zeitfenster relativ zum E3-Start (`tail -1` oben = t0). Die Checks sind Beobachtungen
> — kein Operator-Eingriff außer im Trigger-Fall (§5). Anomalien notieren (Zeitstempel
> + Befund); Exec-Session in der Folgesession fragen.

### t0 + 5 min — Liveness-Smoke

```bash
bash scripts/restart-services.sh status
# alle 4 alive
pgrep -af "python -m scheduler.run"
pgrep -af "python -m data_foundation.run"
pgrep -af "python -m source_registry.run"
pgrep -af "uvicorn webui.api:app"
```

Erwartung: 4 PIDs, alle in dieser Repo-CWD. Wenn ein Prozess fehlt → siehe §5 T-1.

### t0 + 30 min — Substrat-Inbetriebnahme

```bash
sqlite3 data/bars.sqlite "SELECT count(*), source FROM bars
  WHERE ts_utc >= datetime('now', '-30 minutes') GROUP BY source;"
sqlite3 data/trading_bot.sqlite "SELECT count(*) FROM trade_outcomes
  WHERE status IN ('OPEN','PENDING') AND open_ts >= datetime('now', '-30 minutes');"
sqlite3 data/trading_bot.sqlite "SELECT count(*) FROM paper_trades
  WHERE created_utc >= datetime('now', '-30 minutes');"
sqlite3 data/trading_bot.sqlite "SELECT count(*) FROM source_spend
  WHERE kind='sample' AND ts_utc >= datetime('now', '-30 minutes');"
sqlite3 data/trading_bot.sqlite "SELECT count(*) FROM instrument_universe
  WHERE active=1 AND epic LIKE 'IX.D.SUN%';"
```

Erwartung:
- Bars ≥ 1 in mindestens `yf` oder `ls` (Datenfundament lebt). `source='ls'` = 0 ist
  **erwartet** in den ersten 30 min (LS-Token-Handshake bis zum ersten Tick); Watch-Item W4.
- `trade_outcomes` mit OPEN/PENDING kann 0 sein — die Research-Loop startet erst
  nach `last_research_ts` ≥ `09:00` Berlin (ExecutionConfig-Fenster, Plan §6 C).
- `paper_trades` ≥ 1 (Phase-10 Council-Paper-Call läuft wenn `enable_paper_debate=True`).
- `source_spend kind='sample'` ≥ 1 (Phase-13-Divergenz-Sampler läuft wenn
  `enable_divergence_sampler=True`).
- `IX.D.SUN*` in `active` = 0 (B3 Wochenend-Demotion, endgültig in code).

Wenn eines schlägt fehl → §5 T-2 / T-3 / T-4.

### t0 + 4 h — Heartbeat & Preflight

```bash
grep '"measurement_heartbeat"' data/state/research_heartbeat.jsonl 2>/dev/null | tail -5
# oder (je nach Pfad):
grep '"measurement_heartbeat"' data/state/research_health.jsonl 2>/dev/null | tail -5
grep "PreflightError\|preflight failed" data/state/run_scheduler.log
```

Erwartung: ≥ 1 Heartbeat mit `"ok": true`. Kein PreflightError. Wenn Heartbeat `false`
oder PreflightError → §5 T-5.

### t0 + 24 h (= Tag 1) — Tagesabschluss

```bash
phase1_broker_wrapper/.venv/bin/python phase16_activation/scripts/autonomy_report.py \
  --day "$(date -d 'yesterday' +%F)"
# Exit 0 = PASS, 1 = FAIL (mind. ein Kriterium schlug fehl), 2 = ERROR (Quelldatei
# fehlt/korrupt). Output ist data/reports/autonomy_<day>.json (gitignored).
```

Erwartung Tag 1: **K1–K6 grün, K7 grün**. Falls etwas rot:
- K1 rot → Reboot / Restart ohne Backoff ⇒ FAIL Kriterium 1 (P17), Tag läuft weiter.
- K2 rot → WebUI-Down oder Datenfundament-Down ⇒ §5 T-6 / T-7.
- K3 rot → keine autonomen Trades. **OK** am Tag 1 (Watch-Item, n=1 Trade ist
  empirisch selten am ersten Tag — der Effekt kumuliert).
- K4 rot → Heartbeat inkonsistent. Wenn an ≥ 2 Tagen → §5 T-5.
- K5 rot → Backoff oder Margen-Reject-Häufung. Exec-Session für A6-Live-Verify.
- K6 rot → Token-Budget vor 17:30 erschöpft. **FAIL** (Plan §6 E2 K6, hard fail-closed).
- K7 rot → Caps-String-Pin verletzt; Exec-Session, sonst Drift unentdeckt.

---

## 4 · Tagesroutine (Tag 1 … Tag 10)

> Aufwand pro Tag: ≤ 1 min. Operator liest, fasst nichts an.

**Täglich, am Ende des Handelstages (≥ 17:30 Berlin):**

```bash
phase1_broker_wrapper/.venv/bin/python phase16_activation/scripts/autonomy_report.py \
  --day "$(date +%F)"
```

Output auf stderr zusammenfassen (eine Zeile pro Kriterium), JSON in
`data/reports/autonomy_<day>.json` ist der Audit-Trail. Bei `--summary --from
<start> --to <end>` werden die 7 Kriterien über das Fenster aggregiert (für Tag-10-
Closeout, einmalig).

**Was der Operator NICHT tut:**

- Keine manuellen Restarts (Backoff-KILL-Clear zählt als einzige Ausnahme; §Prereg b).
- Kein Trade-Eingriff (Force-Trigger; §Prereg Hard Rule 5, daily_loss_cap = 1800 ⇒
  PNL < 0 sperrt den Force-Trigger strukturell).
- Kein Hotfix-Commit auf Caps/Arms (`max_trades`, `daily_loss_cap`,
  `enable_*`-Defaults).
- Keine DB-Repair außerhalb dieses Runbooks.
- Kein Browser-Refresh auf das WebUI für „mehr Daten" — Polling ist 7 s, der
  Server ist read-only.

**Was der Operator TÄGLICH prüft (zwei Werte, eine Minute):**

1. `--day`-Exit-Code: `0` weiter, `1` Kriterium verletzt → §5 Trigger-Liste gehen,
   `2` Quelldatei korrupt → Exec-Session.
2. JSON-File existiert (`ls -l data/reports/autonomy_<day>.json`) — wenn 0 Bytes
   oder fehlt → Exec-Session (Script hat geschrieben aber nichts gedruckt = Bug).

---

## 5 · Trigger-Bedingungen (wann Exec-Session rufen)

> Die Exec-Session kommt **nur**, wenn ein Trigger greift. „Täglich lesen reicht"
> (Prereg Operator-Regel) heißt auch: nicht bei jeder `--day`-FAIL-Zeile sofort
> rufen — erst die Zuordnung in dieser Tabelle prüfen.

| Trigger | Beobachtung | Aktion |
|---|---|---|
| **T-1** Dienst tot nach Restart | `restart-services.sh status` zeigt einen Dienst "dead" UND Start-Zeile fehlt im Log | Exec-Session, **nicht** manuell restarten (das ist FAIL Kriterium 1) |
| **T-2** Schema-Floor verletzt | `user_version != 9` zur Tag-1-Stunde, oder `_schema_version` weg | Exec-Session (B2 nochmal nötig) |
| **T-3** Wochenend-Epic zurück in active | `instrument_universe WHERE active=1 AND epic LIKE 'IX.D.SUN%'` > 0 | Exec-Session (B3-Regression) |
| **T-4** `bars.source='ls'` bleibt 0 nach 24 h | t0+24 h Substrat-Smoke: keine `ls`-Bars | Exec-Session, D1.2-Wrapper prüfen |
| **T-5** Heartbeat `false` an ≥ 2 Tagen | K4 FAIL ≥ 2× im `--summary`-Output | Exec-Session |
| **T-6** WebUI nicht erreichbar (localhost:8000) | `curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/` ≠ 200, nach 1 min | Exec-Session (K2 WebUI-Operator-Sichtung kann nicht erfüllt werden, Prereg §K2 ehrlich) |
| **T-7** `KILL`-Datei ohne Auto-Backoff | `cat data/state/KILL` zeigt `reason != "auto:backoff"` (z. B. `manual:*`) | **Nicht anfassen**, Exec-Session (Operator-Eingriff wäre FAIL Kriterium 1) |
| **T-8** Token-Budget vor 17:30 erschöpft | K6 FAIL im `--day`-Report | Exec-Session (Plan §6 E2 K6 fail-closed, hard) |
| **T-9** Margen-Reject-Häufung | `grep "INSUFFICIENT_FUNDS" data/state/run_scheduler.log` > 2 pro Tag | Exec-Session, D3-Margin-Headroom prüfen (Watch-Item Plan §13 #8) |
| **T-10** Reboot / Auto-Reboot getriggert | `last reboot` zeigt heutigen Eintrag; `Automatic-Reboot` aktiv | Exec-Session, FAIL Kriterium 1 (Prereg §Erlaubte b) |
| **T-11** Desktop-Session verloren | `loginctl show-session` zeigt keinen aktiven User-Login | **Nicht** neu einloggen ohne Exec-Session-Rücksprache (Keyring-Relogin = FAIL Kriterium 1); stattdessen Exec-Session |
| **T-12** Trade mit nicht-Demo-Account | `SELECT DISTINCT account FROM trade_outcomes` ≠ `'demo'` | **Sofort** Exec-Session (Hard Rule 4: Live-Account verboten); Bot stoppen via `kill -TERM $(pgrep -f scheduler.run)` als Notbremse |

---

## 6 · Watch-Items (nicht PASS, aber zu beobachten)

> Aus `PHASE16_AUTONOMY_PREREGISTRATION.md §Watch-Items`. Werden **nicht** im
> `--day`-Report ausgewertet (kein append-only Pin für W1/W2/W3/W5); W4 + W6 sind
> beobachtbar, aber kein PASS-Kriterium. Operator beobachten, Exec-Session fragen
> wenn unerwartet.

| Watch | Beobachtung | Schwelle |
|---|---|---|
| **W1** BUY-Bias | Alle autonomen Trades sind BUY | Empirisch 8/8 BUY in Phase-9-Live, Plan §2.4. SELL = Befund, nicht PASS-Verletzung. |
| **W2** DAX-Only | Aktive Epics außer Wochenend: alle DAX | Phase-9-Live-Substrat. Andere aktive Epics (FTSE, DOW, SPTRD, IBEX, AEX, MIB, STXE) = Befund nach B3 + Universe-Refresh. |
| **W3** 09:05-Breaker | `circuit open`-Zeilen 09:05–09:20 an Tag 1 | = 0 (Plan §7 AK17 + C5). Wenn doch → Befund, C5-Semantik greift nicht. |
| **W4** LS-Bars | `bars.source='ls'` wächst ab Tag 1 | D1.2 Wrapper aktiv. Wenn 0 nach 24 h → T-4. |
| **W5** Zombie-Zahl | `[python] <defunct>` Prozesse | ≤ 2 (Plan §2.3). Wenn > 5 → Befund (P14-D Sleep-Cap greift nicht). |
| **W6** `min_evidence` vs. Trade-Zahl | Validator-Default `min_evidence` / `instinct_n_min` vs. autonome Trade-Zahl | n ≈ 10–20 ≪ 50 → keine Promotion, VETO 5 No-Op by design (Plan §13 #8). |

---

## 7 · Tag 10 — Closeout

```bash
# 1) Summary über das gesamte Fenster (10 Handelstage Berlin)
phase1_broker_wrapper/.venv/bin/python phase16_activation/scripts/autonomy_report.py \
  --from "$(date -d '<Tag 0 Datum>' +%F)" --to "$(date +%F)" --summary

# 2) Erwartung: overall_verdict == "PASS" (alle 7 Kriterien über das Fenster)

# 3) Wenn PASS: Exec-Session rufen für Closeout-Handover
#    (phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md +
#     docs/architecture/phase16_activation.svg 1080×1080 +
#     Status-Pflege root-CLAUDE/ROADMAP/README/INDEX +
#     Session-Rotation)
```

Wenn `overall_verdict != "PASS"` → Exec-Session für Fehl-Analyse (welches Kriterium,
welche Tage, welcher Grund). Kein Operator-Workaround, kein „nur noch 3 Tage"-
Denken: das 2-Wochen-Fenster ist die Akzeptanz, ein FAIL ist ein FAIL.

---

## 8 · Was dieses Runbook *nicht* macht

- **Keine Strategie-Bewertung.** Profit, Win-Rate, Sharpe, P&L sind explizit aus
  Prereg §"Was nicht als PASS zählt" ausgeschlossen. Das ist ein Autonomie-Test.
- **Keine Code-Änderungen.** Hotfix-Commits auf Caps/Arms sind in Prereg §"Nicht
  erlaubt" explizit FAIL Kriterium 1. Cross-Phase-Bugfixes in der 2-Wochen-Phase
  sind Phase-17-Material, nicht Phase-16.
- **Keine Prozess-Supervision.** Auto-Restart nach Reboot, systemd-Unit, Keyring-
  Auto-Unlock sind **bewusst out-of-scope** (Plan §10 / Opus-Review §13 #5). Die
  Desktop-Session manuell eingeloggt zu lassen ist die Vorregistrierungs-Disziplin.
- **Keine Fehlgriff-Diagnose.** Die §8-Fehlgriffe-Tabelle im Plan (z. B. „Heartbeat
  nach D1 weiter CRITICAL 'measurement arm off'") gehört in die Exec-Session; der
  Operator liest Symptom → Trigger, nicht Symptom → Root Cause.

---

## 9 · Cross-Refs

- Vorregistrierung (PASS-Kriterien, Werte, Operator-Ereignisse, Watch-Items): [`./PHASE16_AUTONOMY_PREREGISTRATION.md`](./PHASE16_AUTONOMY_PREREGISTRATION.md)
- Plan §6 Block E Steps E1–E4: [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) S. 758–815
- Plan §6 E3 (Quelle dieses Runbooks, Bash-Stufen 797–808): ebd.
- Plan §7 Akzeptanz AK4/AK5/AK5b/AK9/AK11/AK12/AK13/AK14/AK15/AK16/AK17: ebd. S. 821–842
- Plan §8 Fehlgriffe-Symptom-Tabelle: ebd. S. 846–865 (Exec-Session-Pfad)
- Plan §10 Out-of-Scope: ebd. S. 895–910 (Strategy-Bewertung, Auto-Restart, etc.)
- Plan §11 Operator-Aktionen #5 (Restart), #6 (täglicher Report), #7 (Tag 10 Closeout): ebd. S. 913–924
- Plan §13 Opus-Review #5 (Supervision), #6 (WebUI-Aliveness unmessbar), #8 (Bridge unerreichbar), #9 (Budget-Datei-Korruption): ebd. S. 935–947
- `restart-services.sh`: [`../scripts/restart-services.sh`](../scripts/restart-services.sh) (4-Services, sequenziell, Sicherheits-Kultur)
- Tages-/Summary-Report: [`./scripts/autonomy_report.py`](./scripts/autonomy_report.py) + [`./tests/test_autonomy_report.py`](./tests/test_autonomy_report.py) (5 AK-Tests, 1,39 s)
- Phase-15-Vorgänger (E1–E3 dort offen → hier geschlossen): [`../phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md`](../phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md)