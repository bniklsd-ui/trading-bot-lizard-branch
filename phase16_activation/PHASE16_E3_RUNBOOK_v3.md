---
status: locked
purpose: Operator-Runbook v3 für Phase-16-Block-E-Schritt E3 — supersedet v2
  (PHASE16_E3_RUNBOOK_v2.md, 2026-09-07) durch 1 Drift-Korrektur (Drift #7: §2.3
  Keyring-Check-Snippet verwendet falsche Credential-Namen `cst`/`demo_token`/
  `token`; echt sind `ig_*` und `ig_demo_*` per `store_credential.py --status`).
  v2 bleibt als historischer Stand im Repo (Audit-Trail), wird nicht mehr gelesen.
  v3 ist die einzige Quelle der Wahrheit für den Operator-Pfad.
read-when: am E3-Restart-Tag (Tag 0) und täglich während des 2-Wochen-Fensters;
  Audit, was der Operator mechanisch tut vs. lassen muss
detail: L3
up: ./CLAUDE.md
down:
  - ./PHASE16_E3_RUNBOOK.md                          # 📕 v1 (superseded by v2→v3, Audit-Trail)
  - ./PHASE16_E3_RUNBOOK_v2.md                       # 📕 v2 (superseded by v3, Audit-Trail)
  - ./PHASE16_AUTONOMY_PREREGISTRATION.md            # 📕 PASS-Kriterien + vorregistrierte Werte (zwingend vorher lesen)
  - ../docs/concepts/phase16_activation_plan.md      # 📕 §6 E3 (Quelle, S. 797–808), §11 #5/#6/#7
  - ./scripts/autonomy_report.py                     # 🔧 der tägliche Tages-/Summary-Report (K1–K7)
  - ./SESSIONS_ARCHIVE.md                            # 📦 Session-Historie (E1/E2/E3-Sessions)
  - ./PHASE16_E3_RUNBOOK_v3.md                       # 📕 DIESE DATEI (locked, v3 ab 2026-09-08)
updated: 2026-09-08
---

# PHASE16_E3_RUNBOOK v3 — Operator-Pfad für den 2-Wochen-Autonomie-Test

> **v3 supersedet v2** (`PHASE16_E3_RUNBOOK_v2.md`). v2 bleibt im Repo als historischer
> Audit-Stand; **nicht** mehr lesen für den E3-Start. v3 ist die einzige Quelle der
> Wahrheit für den Operator-Pfad. v3 ist locked-nach-Commit (Prereg-Disziplin analog
> v1, v2 und PHASE16_AUTONOMY_PREREGISTRATION.md): Korrekturen sind nur als
> `PHASE16_E3_RUNBOOK_v4.md` mit Datum und Grund möglich — niemals ein Edit hier.
>
> **Was v3 anders macht als v2 (1 Korrektur, Drift #7 aus Session #24):**
> 1. **§2.3 Keyring-Check** korrigiert: `cst`/`demo_token`/`token` (existieren nicht in
>    `broker_wrapper/credentials.py`) → `store_credential.py --status` als kanonischer
>    Check + optionaler 8-Zeichen-Fingerprint mit `IG_DEMO_*`-Namen. Drift war seit
>    Session-#13-Pre-Flight (SESSIONS_ARCHIVE Z. 1378) als nicht-blockierend notiert
>    (Demo-Credentials tatsächlich da, Snippet schlug mit `CredentialNotFoundError: 'cst'`
>    fehl, leicht als Snippet-Bug diagnostizierbar); in Session #24 (2026-09-08 Abend) live
>    reproduziert. v3-Patch schließt die Klasse endgültig.
>
> **Warum diese Disziplin:** die Pre-Flight-Checks haben gezeigt, dass das v2-Snippet
> die falschen Credential-Namen verwendete. Code ist source of truth (root-CLAUDE.md
> Working-Style-Regel). v2 zu editieren wäre Locked-nach-Commit-Verstoß; ein neues
> supersedendes v3 ist die saubere Form. v1 zu editieren wäre analog Locked-nach-Commit-
> Verstoß (v1 → v2 enthielt bereits 6 Schema-/SQL-Drifts in derselben Disziplin).
>
> **Was v2 anders macht als v1 (6 Korrekturen aus Session-#13-Pre-Flight):**
> 1. **§1.2 Schema-Floor-Check** korrigiert: `PRAGMA user_version` ist **nicht** die
>    Schema-Version (gibt 0 zurück). Phase-2 trackt via `_schema_version`-Tabelle
>    (9 Zeilen = v9 wirksam).
> 2. **§1.4 Truncate** erweitert: 4 zusätzliche Pre-Wrapper-Logs (`scheduler.log`,
>    `webui.log`, `recorder.log`, `discovery.log`) — irrelevant für K1 (kein
>    run-Wrapper-Prefix), aber kosmetisch (verhindert dass Pre-Wrapper-Restarts in
>    den Logs weiterleben).
> 3. **§1.5 / §3.0 / §5 T-3 Spalten-Drift**: `instrument_universe.active=1` →
>    `instrument_universe.status='active'`, `last_verified_utc` → `last_verified_at`.
> 4. **§3.0 `source_spend`-DB-Pfad**: lebt in `data/bars.sqlite`, **nicht** in
>    `data/trading_bot.sqlite` (Runbook v1 hatte es implizit in trading_bot).
> 5. **§3.0 `paper_trades`**: Spalte heißt `status` (nicht `resolved`), die
>    Beobachtung ist `paper_trades WHERE status='OPEN' AND created_utc >= ...` (oder
>    RESOLVED-Zähler separat).
> 6. **§3.0 Pflicht-Pre-E3-Operator-SQL** für 3 SUN*-Epics neu aufgenommen:
>    `UPDATE instrument_universe SET status='quarantined' WHERE epic LIKE 'IX.D.SUN%'
>    AND status='active';` (3 Zeilen: SUNDAX.IGN, SUNDOW, SUNNAS; alle aus
>    2026-09-04-Promotions, vor B3-Implementation B3-Commit `d82922e` Session #3
>    2026-09-05; B3 wirkt forward-only, deshalb diese Pre-E3-Reinigung).

>
> **Was v2 anders macht als v1 (6 Korrekturen aus Session-#13-Pre-Flight, von v2 geerbt):**
> *(verbatim aus v2, hier eingebettet damit v3 die komplette Audit-Kette trägt)*
>
> **Warum diese Disziplin:** die Pre-Flight-Checks (§1.1) haben gezeigt, dass die
> Live-DB anders aussieht als v1 annahm. Code ist source of truth (Root-CLAUDE.md
> Working-Style-Regel). v1 zu editieren wäre Locked-nach-Commit-Verstoß; ein neues
> supersedendes v2 ist die saubere Form.

---

## 0 · BLUF

`bash scripts/restart-services.sh start` (mit Pre-Flight davor, Pflicht-Operator-SQL
für 3 SUN*-Epics, und Day-0-Checks danach) reicht aus, um den 2-Wochen-Autonomie-
Test strukturell zu starten. Täglich `scripts/autonomy_report.py --day` lesen. Bei
Auffälligkeit die in §5 gelisteten Trigger-Bedingungen prüfen — die Exec-Session
kommt nur, wenn ein Trigger greift.

**Reihenfolge (Operator-Pfad in dieser Reihenfolge ausführen, kein Schritt überspringen):**

1. **Pflicht-Operator-SQL** (Abschnitt 1.0) — 3 SUN*-Epics → `quarantined` (3 Zeilen,
   pre-E3-Blocker aus B3 forward-only Lücke).
2. **§1 Pre-Flight** (6 Schritte, ≤ 5 min) — Status-Checks + Truncate + DB-Health.
3. **§1.6 Prereg-Aktiv-Block-Eintragung** + Folge-Commit `phase16: docs -- E1-Aktiv-Block-Eintragung`.
4. **§2 Restart-Sequenz** (`restart-services.sh start` + K7-Caps-Pin-Verify).
5. **§3 Day-0-Checks Timeline** (5min / 30min / 4h / 24h).
6. **§4 Tagesroutine** (täglich `--day`).
7. **§7 Tag 10 Closeout** (`--summary` + Exec-Session für Handover/SVG).

---

## 1 · Pflicht-Operator-SQL (VOR dem ersten `start` — Pre-E3-Blocker)

> **Hintergrund:** Block B Step B3 (Phase-16-Session #3, 2026-09-05, Code-Commit
> `d82922e phase16+phase9: code -- Block B Step B3`) hat `is_weekend_market()` +
> Discovery-Filter + Promotion-Step-3-demote eingebaut — aber **forward-only**. Drei
> SUN*-Epics wurden am 2026-09-04 promoted (`status='active'`), bevor B3 aktiv war.
> Diese müssen pre-E3 manuell demotet werden, sonst verletzt der Test bereits vor
> Tag 1 die AK9-Bedingung „kein `IX.D.SUN*` in `active`" (Prereg §Vorregistrierte
> Werte / Plan §7).
>
> **Audit-Trail:** dieser SQL-Schritt wird im `PHASE16_AUTONOMY_PREREGISTRATION.md`-
> Aktiv-Block unter „Operator-Aktionen vor E3-Start" eingetragen (analog zu B2
> Schema-Apply, Session #3).

```bash
# Pre-Verify (erwartet: 3 Zeilen)
sqlite3 data/trading_bot.sqlite "SELECT epic, status, last_verified_at \
  FROM instrument_universe \
  WHERE epic LIKE 'IX.D.SUN%' AND status='active';"

# Pflicht-SQL (3 Zeilen: SUNDAX.IGN, SUNDOW, SUNNAS)
sqlite3 data/trading_bot.sqlite "UPDATE instrument_universe \
  SET status='quarantined', checks_json=json_set( \
    COALESCE(checks_json,'{}'), '\$.reason', 'weekend_market_pre_B3_cleanup' ) \
  WHERE epic LIKE 'IX.D.SUN%' AND status='active';"

# Post-Verify (erwartet: 0 Zeilen)
sqlite3 data/trading_bot.sqlite "SELECT count(*) FROM instrument_universe \
  WHERE epic LIKE 'IX.D.SUN%' AND status='active';"
```

`json_set` setzt einen Audit-Trail-Eintrag ins `checks_json`-Feld (kein FK, kein
Schema-Touch, kein Commit nötig — die Datenbank ist gitignored). Falls
`json_set`-Update wegen NULL `checks_json` fehlschlägt, einfach ohne das json_set
ausführen — die reine Status-Änderung zählt für die AK9-Erfüllung.

**Was diese 3 Epics danach machen:** sie bleiben `quarantined`. Phase-9-Discovery
wird sie bei zukünftigen Sweeps **nicht** erneut promoten (`is_weekend_market`
filtert sie im `_passes_code_filter` raus, Code-Commit `d82922e` Z. 102-104 +
Z. 87 `WEEKEND_NAME_MARKERS = ("wochenend", "weekend")`). Sie sind strukturell
aus dem aktiven Universum entfernt, ohne dass ein Operator-Workaround nötig wäre.

---

## 2 · Pre-Flight (VOR dem ersten `start`, NACH Pflicht-SQL)

> Dauer: ≤ 5 min, mechanisch. Wenn etwas nicht hält → **nicht starten**, stattdessen
> Exec-Session rufen (siehe §5 Trigger-Bedingungen).

### 2.1 — Liveness-Check (heute = 4 Dienste tot seit B2-Apply, Plan §6 E3)

```bash
bash scripts/restart-services.sh status
```

Erwartung: **alle 4 tot** (`recorder`, `discovery`, `scheduler`, `webui` jeweils "dead").
Wenn ein Dienst lebt: einzeln stoppen oder einmal `bash scripts/restart-services.sh
restart --dry-run` previewen, dann `restart`. Wenn nach `restart` weiterhin ein
Dienst lebt → Exec-Session, kein Operator-Workaround.

### 2.2 — Schema-Floor 9 verifizieren (korrigiert ggü. v1)

> **v1-Drift:** `PRAGMA user_version` ist **nicht** die Schema-Version (gibt 0
> zurück, da SQLite-PRAGMA nicht das ist, was Phase-2-Persistenz für Schema-Tracking
> nutzt). Phase-2 trackt via eigene `_schema_version`-Tabelle.

```bash
sqlite3 data/trading_bot.sqlite "SELECT name FROM sqlite_master WHERE type='table'
  AND name IN ('instincts','_schema_version');"
sqlite3 data/trading_bot.sqlite "SELECT count(*) FROM _schema_version;"
```

Erwartung: beide Zeilen antworten (`instincts` existiert, `_schema_version` hat **9 Zeilen**).
Wenn `_schema_version`-Tabelle leer oder count ≠ 9 → **nicht starten**; B2 wurde
nicht (oder unvollständig) angewendet; Exec-Session.

### 2.3 — Keyring erreichbar (Demo-Credentials gesetzt)

```bash
# 1) Status (zeigt nur ✓/✗, niemals Werte)
phase1_broker_wrapper/.venv/bin/python phase1_broker_wrapper/scripts/store_credential.py --status
```

Erwartung: **alle 4 `ig_demo_*` = ✓**, alle 4 `ig_*` (Live-Account) = **✗** (per Hard
Rule 4, Demo-only — der Bot darf den Live-Account nie sehen). Wenn ein Demo-Key ✗
zeigt → `python phase1_broker_wrapper/scripts/store_credential.py ig_demo_<fehlend>`
ausführen, Wert via `getpass` interaktiv eingeben (Hard Rule 1: niemals in Datei/Chat/Log).
Wenn ein Live-Key ✓ zeigt → **sofort stoppen**, Exec-Session (Hard Rule 4 verletzt).

```bash
# 2) Optional: 8-Zeichen-Fingerprint pro Demo-Key (beweist dass Werte nicht leer sind)
phase1_broker_wrapper/.venv/bin/python -c "
from broker_wrapper.credentials import get_credential
for n in ['IG_DEMO_USERNAME', 'IG_DEMO_PASSWORD', 'IG_DEMO_API_KEY', 'IG_DEMO_ACCOUNT_ID']:
    v = get_credential(n)
    print(f'{n}: {(v[:8] + chr(46)*3) if v else chr(40)+chr(101)+chr(109)+chr(112)+chr(116)+chr(121)+chr(41)}')
"
```

Erwartung: 4 Zeilen mit je 8-Zeichen-Fingerprint + `...`. Wenn eine Zeile `(empty)` zeigt →
Desktop-Session war / ist nicht eingeloggt; **Login wiederholen**, dann erneut prüfen.
Wenn nach Relogin immer noch leer → Exec-Session (Keyring kaputt).

> **Drift-Historie:** das **v2-§2.3-Snippet** fragte nach `cst` und `demo_token`/`token` —
> diese Namen existieren **nicht** in `broker_wrapper/credentials.py`. Echte Keyring-Namen
> sind `ig_username`/`ig_password`/`ig_api_key`/`ig_account_id` (Live) und
> `ig_demo_username`/`ig_demo_password`/`ig_demo_api_key`/`ig_demo_account_id` (Demo).
> Der Drift wurde zuerst in Session-#13-Pre-Flight gefunden (SESSIONS_ARCHIVE Z. 1378
> „Drift #7"), damals als **nicht-blockierend** notiert (Demo-Credentials tatsächlich da,
> Snippet schlug nur mit `CredentialNotFoundError: 'cst' not found` fehl, war leicht als
> „Snippet fragt falschen Namen" diagnostizierbar). In Session #24 (2026-09-08 Abend) live
> reproduziert: `CredentialNotFoundError: 'cst' not found` beim ersten §2.3-Versuch →
> `store_credential.py --status` zeigt alle 4 `ig_demo_*` = ✓. **v3 fixt Drift #7:**
> `store_credential.py --status` als kanonischer Check, alter Fingerprint-Snippet korrigiert
> auf die echten `IG_DEMO_*`-Namen, Drift #7 in §11 Diff-Tabelle aufgenommen.
>
> **Hard Rule 1 (root-CLAUDE.md):** Credentials werden **nie** in Dateien geschrieben,
> **nie** ins `.env`, **nie** ins Log. `store_credential.py` liest Werte via `getpass`
> (kein Echo, keine Shell-History); `get_credential` und `--status` geben nie Werte aus.
> Die 8-Zeichen-Fingerprints im optionalen Check sind eindeutig kein Volltext.

### 2.4 — K1-Log-Truncate (korrigiert ggü. v1)

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

> **Erweitert ggü. v1:** zusätzlich die 4 Pre-Wrapper-Logs truncaten — irrelevant
> für K1 (kein `run_`-Wrapper-Prefix), aber kosmetisch (verhindert dass
> Pre-Wrapper-Restarts in den Logs weiterleben und der Operator später verwirrt ist):
>
> ```bash
> truncate -s 0 data/state/scheduler.log \
>           data/state/webui.log \
>           data/state/recorder.log \
>           data/state/discovery.log
> ```

> **Implikation:** ab Tag 0 hat jeder der 3 getruncten Wrapper-Logs **genau eine**
> Start-Zeile (vom E3-Start). Bei einem späteren P17-erlaubten Backoff-KILL-Clear ⇒
> exakt 2 Zeilen (PASS, einmalig erlaubt). Bei einem späteren Reboot ⇒ 2+ Zeilen
> (FAIL Kriterium 1, Plan §1 P17 / Prereg §Erlaubte Operator-Ereignisse a).

### 2.5 — Datenbank-Health (korrigiert ggü. v1)

```bash
sqlite3 data/bars.sqlite "SELECT count(*), source FROM bars GROUP BY source;" 2>&1 | head -10
sqlite3 data/bars.sqlite "SELECT count(*), kind FROM source_spend GROUP BY kind;" 2>&1
sqlite3 data/trading_bot.sqlite "SELECT count(*), status FROM paper_trades GROUP BY status;" 2>&1
sqlite3 data/trading_bot.sqlite "SELECT count(*) FROM trade_outcomes WHERE account='demo';" 2>&1
sqlite3 data/trading_bot.sqlite "SELECT count(*) FROM instrument_universe WHERE status='active' AND epic LIKE 'IX.D.SUN%';" 2>&1
```

> **v1-Drift-Korrekturen:**
> - `source_spend` ist in `data/bars.sqlite` (nicht `data/trading_bot.sqlite`).
> - `paper_trades`-Spalte heißt `status` (nicht `resolved`), Werte OPEN/RESOLVED/EXPIRED_UNRESOLVED.
> - `instrument_universe`-Spalte heißt `status` (nicht `active=1`).

Erwartung:
- Bars nach `source` gruppiert (heute `yf`/`ig`/`capital`, ≥ 1 Zeile je etablierter
  Quelle). `source='ls'` = 0 ist **erwartet** in den ersten 30 min (LS-Token-
  Handshake bis zum ersten Tick); Watch-Item W4.
- `source_spend` zeigt die 3 erlaubten Kinds (`probe`/`research`/`sample`).
- `paper_trades`-Verteilung plausibel (Status-Mix aus früheren Läufen).
- `trade_outcomes WHERE account='demo'` ≥ 1 (alle historischen 8 sind demo).
- **`instrument_universe WHERE status='active' AND epic LIKE 'IX.D.SUN%'` = 0**
  (Pflicht-SQL §1 muss vorher gelaufen sein — sonst FAIL).

Wenn eines schlägt fehl → §5 T-2 / T-3 / T-4.

### 2.6 — Akten-Vermerk im Preregistrierungs-Doc (AK13)

Im `PHASE16_AUTONOMY_PREREGISTRATION.md`-Aktiv-Block das Feld **Start (E3-Restart-
Zeitstempel)** mit dem genauen Zeitpunkt eintragen, **bevor** die erste Start-Zeile
im Log landet. Das ist eine **Eintragung**, kein Edit (im Prereg-Doc explizit
dokumentiert). Format: Berlin, ISO 8601, Sekunden-genau. **Anschließend** Commit
`phase16: docs -- E1-Aktiv-Block-Eintragung` mit dem Zeitstempel.

Zusätzlich eintragen (neu in v2): **Operator-SQL-Audit** für die 3 SUN*-Epics
(Epic-Liste + ts_utc der Ausführung).

---

## 3 · Restart-Sequenz (verbatim aus Plan §6 E3)

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

## 4 · Day-0-Checks Timeline (korrigiert ggü. v1)

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

### t0 + 30 min — Substrat-Inbetriebnahme (Spalten-Drift korrigiert)

```bash
sqlite3 data/bars.sqlite "SELECT count(*), source FROM bars
  WHERE ts_utc >= datetime('now', '-30 minutes') GROUP BY source;"
sqlite3 data/bars.sqlite "SELECT count(*) FROM source_spend
  WHERE ts_utc >= datetime('now', '-30 minutes');"
sqlite3 data/trading_bot.sqlite "SELECT count(*) FROM trade_outcomes
  WHERE status IN ('OPEN','PENDING') AND open_ts >= datetime('now', '-30 minutes');"
sqlite3 data/trading_bot.sqlite "SELECT count(*) FROM paper_trades
  WHERE created_utc >= datetime('now', '-30 minutes');"
sqlite3 data/trading_bot.sqlite "SELECT count(*) FROM instrument_universe
  WHERE status='active' AND epic LIKE 'IX.D.SUN%';"
sqlite3 data/trading_bot.sqlite "SELECT max(last_verified_at) FROM instrument_universe;"
```

> **v1-Drift-Korrekturen:** Spalte `status` (statt `active=1`); `paper_trades`-
> Filter auf `created_utc` (kein `resolved`-Feld); `source_spend` in `data/bars.sqlite`
> mit `ts_utc` (Spalte heißt `ts_utc`, nicht `created_at`); `last_verified_at`
> (nicht `last_verified_utc`); SUN*-Check muss 0 sein (Pflicht-SQL §1).

Erwartung:
- Bars ≥ 1 in mindestens `yf` oder `ls` (Datenfundament lebt). `source='ls'` = 0 ist
  **erwartet** in den ersten 30 min (LS-Token-Handshake bis zum ersten Tick); Watch-Item W4.
- `source_spend` ≥ 1 (kind='sample' wenn Divergenz-Sampler läuft, oder kind='research'
  wenn Research getickt hat).
- `trade_outcomes` mit OPEN/PENDING kann 0 sein — die Research-Loop startet erst
  nach `last_research_ts` ≥ `09:00` Berlin (ExecutionConfig-Fenster, Plan §6 C).
- `paper_trades` ≥ 1 (Phase-10 Council-Paper-Call läuft wenn `enable_paper_debate=True`).
- `IX.D.SUN*` in `status='active'` = 0 (Pflicht-SQL §1 muss vorher gelaufen sein).
- `max(last_verified_at)` ist ein recent Timestamp (≤ 30 min alt) — Discovery hat
  refresht.

Wenn eines schlägt fehl → §5 T-2 / T-3 / T-4.

### t0 + 4 h — Heartbeat & Preflight

```bash
grep '"measurement_heartbeat"' data/state/research_health.jsonl 2>/dev/null | tail -5
grep "PreflightError\|preflight failed" data/state/run_scheduler.log
```

> **v1-Korrektur:** Heartbeat liegt in `data/state/research_health.jsonl` (nicht
> `data/state/research_heartbeat.jsonl`, das es nicht gibt).

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

## 5 · Tagesroutine (Tag 1 … Tag 10)

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

## 6 · Trigger-Bedingungen (wann Exec-Session rufen)

> Die Exec-Session kommt **nur**, wenn ein Trigger greift. „Täglich lesen reicht"
> (Prereg Operator-Regel) heißt auch: nicht bei jeder `--day`-FAIL-Zeile sofort
> rufen — erst die Zuordnung in dieser Tabelle prüfen.

| Trigger | Beobachtung | Aktion |
|---|---|---|
| **T-1** Dienst tot nach Restart | `restart-services.sh status` zeigt einen Dienst "dead" UND Start-Zeile fehlt im Log | Exec-Session, **nicht** manuell restarten (das ist FAIL Kriterium 1) |
| **T-2** Schema-Floor verletzt | `count(*) FROM _schema_version` ≠ 9, oder `_schema_version` weg | Exec-Session (B2 nochmal nötig) |
| **T-3** Wochenend-Epic zurück in active | `instrument_universe WHERE status='active' AND epic LIKE 'IX.D.SUN%'` > 0 | Exec-Session (B3-Regression oder Pflicht-SQL §1 wurde vergessen) |
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

## 7 · Watch-Items (nicht PASS, aber zu beobachten)

> Aus `PHASE16_AUTONOMY_PREREGISTRATION.md §Watch-Items`. Werden **nicht** im
> `--day`-Report ausgewertet (kein append-only Pin für W1/W2/W3/W5); W4 + W6 sind
> beobachtbar, aber kein PASS-Kriterium. Operator beobachten, Exec-Session fragen
> wenn unerwartet.

| Watch | Beobachtung | Schwelle |
|---|---|---|
| **W1** BUY-Bias | Alle autonomen Trades sind BUY | Empirisch 8/8 BUY in Phase-9-Live, Plan §2.4. SELL = Befund, nicht PASS-Verletzung. |
| **W2** DAX-Only | Aktive Epics außer Wochenend: alle DAX | Phase-9-Live-Substrat. Andere aktive Epics (FTSE, DOW, SPTRD, IBEX, AEX, MIB, STXE) = Befund nach B3 + Universe-Refresh. **W2-Definition-Update 2026-09-13 (Phase-16 Session #30):** nach B3-Block (Phase 16) + Universe-Refresh ist die Live-Substrat-Erwartung nicht mehr „alle DAX", sondern „DAX-dominant mit MIB/FTSE/STXE/DOW/SPTRD als Sekundär-Slots". Beobachtungs-Schwelle: DAX-Anteil < 50 % der aktiven Epics = Befund (= strukturelle Drift weg von der DAX-Heimat). Heute gemessen 2026-09-13: 8 active, davon 1 DAX (`IX.D.DAX.IFM.IP`) + 1 DAX-IGN + MIB + FTSE + DOW + SPTRD + 2 Wochenend-SUNDAX-IGN (zurück in active per heute Datenabgleich — AK9 prereg-formal noch offen) ⇒ **DAX-Anteil 25 % (2/8) — W2 FAIL**. **Aber:** AK9 prereg-formal noch offen (B3 forward-only hat 3 SUNDAX/SUNDOW/SUNNAS pre-promoted gelassen, Pflicht-SQL §1 ist Operator-Pflicht bis zum ersten Restart), und die Sekundär-Slots sind Phase-14-Discovery-Ausgabe (soll so sein). **Operative Lesart 2026-09-13:** W2 ist heute FAIL by design (B3 + Phase-14-Discovery-Output zusammen) und kein Strategy-Befund — Pflegschaft mit Phase-17 (Universums-Konsolidierung). |
| **W3** 09:05-Breaker | `circuit open`-Zeilen 09:05–09:20 an Tag 1 | = 0 (Plan §7 AK17 + C5). Wenn doch → Befund, C5-Semantik greift nicht. |
| **W4** LS-Bars | `bars.source='ls'` wächst ab Tag 1 | D1.2 Wrapper aktiv. Wenn 0 nach 24 h → T-4. |
| **W5** Zombie-Zahl | `[python] <defunct>` Prozesse | ≤ 2 (Plan §2.3). Wenn > 5 → Befund (P14-D Sleep-Cap greift nicht). |
| **W6** `min_evidence` vs. Trade-Zahl | Validator-Default `min_evidence` / `instinct_n_min` vs. autonome Trade-Zahl | n ≈ 10–20 ≪ 50 → keine Promotion, VETO 5 No-Op by design (Plan §13 #8). |

---

## 8 · Tag 10 — Closeout

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

## 9 · Was dieses Runbook *nicht* macht

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
- **Keine v1-Referenz.** v1 ist superseded. Wenn v1-Verweise im Code/anderen Docs
  auftauchen, sind sie historisch — v2 ist die Quelle der Wahrheit.

---

## 10 · Cross-Refs

- Vorregistrierung (PASS-Kriterien, Werte, Operator-Ereignisse, Watch-Items): [`./PHASE16_AUTONOMY_PREREGISTRATION.md`](./PHASE16_AUTONOMY_PREREGISTRATION.md)
- v1 (superseded, Audit-Trail): [`./PHASE16_E3_RUNBOOK.md`](./PHASE16_E3_RUNBOOK.md)
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

---

## 11 · Diff v1 → v2 (für Audit-Trail)

| Stelle | v1 | v2 | Grund |
|---|---|---|---|
| §1.2 Schema-Check | `PRAGMA user_version` | `SELECT count(*) FROM _schema_version` | v1-SQL gibt 0 zurück (PRAGMA ≠ Phase-2-Schema-Tracking); v2 verifiziert die echte 9-Zeilen-Tabelle |
| §1.4 Truncate | 3 Wrapper-Logs | 3 Wrapper-Logs + 4 Pre-Wrapper-Logs | v1 hatte kosmetische Lücke; v2 truncatet zusätzlich `scheduler.log`/`webui.log`/`recorder.log`/`discovery.log` (Pre-Wrapper-Stände) |
| §1.5 / §3.0 / §5 T-3 Spalte `active` | `WHERE active=1` | `WHERE status='active'` | v1 falsche Spalte (Tabelle hat kein `active`-Feld, sondern `status`) |
| §1.5 / §3.0 / §5 T-3 Spalte `last_verified` | `last_verified_utc` | `last_verified_at` | v1 falsche Spalte (DB hat `last_verified_at`) |
| §3.0 `source_spend`-DB | implizit `data/trading_bot.sqlite` | explizit `data/bars.sqlite` | v1 falsche DB (Phase-12 trackt `source_spend` in `bars.sqlite`) |
| §3.0 `paper_trades`-Filter | "neue Zeilen" (kein Spalten-Filter) | `WHERE created_utc >= ...` + Status-Mix | v1 hatte keinen konkreten Filter; v2 spezifiziert auf `created_utc` und zeigt Status-Mix-Hinweis |
| §1 (NEU) | — | **Pflicht-Operator-SQL** für 3 SUN*-Epics | v2 fügt pre-E3-Blocker-Fix hinzu (B3 forward-only Lücke: 3 Epics vom 2026-09-04 pre-B3-promoted → manuell `quarantined`) |
| Reihenfolge | §1 → §2 → §3 → §4 | §1 (Pflicht-SQL) → §2 (Pre-Flight) → §3 (Restart) → §4 (Day-0) → §5 (Tagesroutine) → §6 (Trigger) → §7 (Watch) → §8 (Closeout) | v2 nummeriert Sektionen 0-11 (war 0-9), Pflicht-SQL als eigene Sektion §1 |
| §2.3 Keyring-Check-Snippet | `cst` + `demo_token`/`token` | `store_credential.py --status` + optionaler Fingerprint mit `IG_DEMO_USERNAME`/`IG_DEMO_PASSWORD`/`IG_DEMO_API_KEY`/`IG_DEMO_ACCOUNT_ID` | **Drift #7** aus Session-#13-Pre-Flight (SESSIONS_ARCHIVE Z. 1378, damals als nicht-blockierend notiert); live reproduziert 2026-09-08 Session #24 (`CredentialNotFoundError: 'cst' not found`); echte Keyring-Namen in `broker_wrapper/credentials.py` sind `ig_*` (Live) und `ig_demo_*` (Demo), keine `cst`/`demo_token`/`token` Aliase. v3-Patch: kanonischer Check via `store_credential.py --status`, alter Snippet durch korrigierten Fingerprint ersetzt, Drift-Historie in §2.3-Body dokumentiert. |
| K1-Counting `full-file-count`-Note | nicht dokumentiert (implizit „alle Zeilen, weil kein Filter") | explizite Drift-Erklärung + W2-Definition-Update | **Drift #8** aus Session #26 (SESSIONS_ARCHIVE Session #26 NEXT-Block) und Session #28-#29: `autonomy_report.py` K1 zählt Wrapper-Start-Lines (`[run_recorder] starting` / `[run_discovery] starting` / `[run_webui] dashboard on`) als **full-file-count**, weil die Wrapper-Logs (`run_recorder.log` / `run_discovery.log` / `run_webui.log`) **untimestamped** starten — `restart-services.sh` ruft die Wrapper ohne `date`-Prefix auf, der Wrapper selbst schreibt beim Start eine Zeile ohne `[YYYY-MM-DD HH:MM:SS,mmm]`. `count_starts_in_window` (autonomy_report.py:189) filtert nur Zeilen MIT Timestamp (`from_ts`/`to_ts`), also matchen die Wrapper-Start-Lines nie → werden als **ganze-Datei-Count** gemeldet (`note: "full-file-count (untimestamped start-lines: opaque to window filter)"`). **Live-Beweis Session #26 Tag-1-Verify:** K1 meldete `discovery: 7, recorder: 6, scheduler: 6, webui: 10` Starts — alle außer scheduler waren Wrapper-full-file-counts. **Akzeptanz**: K1 ist für Scheduler deterministisch korrekt (Python-Logger mit Timestamp-Prefix per `basicConfig`-default), für Wrapper-Dienste **by-design opak**. Phase-16-F Exec-Plan F-Exec-Plan §7 Fehlgriffe empfiehlt: bei K1 FAIL die `note`-Felder anschauen — `filtered-by-timestamp` = echter Restart im Fenster, `full-file-count` = Wrapper-Opazität (kein K1-FAIL-Grund). **Fix-Pfad (out-of-scope heute):** Wrapper-Skripte könnten `date '+%Y-%m-%d %H:%M:%S'` als Prefix vor jeden Start-Print schreiben; Code-Change in `scripts/run_recorder.sh` / `run_discovery.sh` / `run_webui.sh` (=3 File-Edits), H-1-Tests beweisen bereits dass die Wrapper-Logik sonst korrekt ist (`grep -c ProgrammingError data/state/run_scheduler.log` muss 0 bleiben). Heute dokumentiert; Tag-10-Closeout (Session #30 Block I) kann den Fix optional mitnehmen. |