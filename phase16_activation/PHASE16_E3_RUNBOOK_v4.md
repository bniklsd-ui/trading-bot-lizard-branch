---
status: locked
purpose: Operator-Runbook v4 für Phase-16-Block-E-Schritt E3 — supersedet v3
  (PHASE16_E3_RUNBOOK_v3.md, 2026-09-08) durch Phase-16-R5-Autostart
  (4 systemd-User-Units + Installer) + K1/K9-Split (Prereg v3) + W6/W7
  (Drift #13-Fix + Log-Hygiene). v3 bleibt als historischer Stand im Repo
  (Audit-Trail), wird nicht mehr gelesen. v4 ist die einzige Quelle der
  Wahrheit für den Operator-Pfad.
read-when: am E3-Restart-Tag (Tag 0), am Reboot-Test-Tag (AK-R6), und täglich
  während des 2-Wochen-Fensters; Audit, was der Operator mechanisch tut vs.
  lassen muss
detail: L3
up: ./CLAUDE.md
down:
  - ./PHASE16_E3_RUNBOOK.md                          # 📕 v1 (superseded durch v2→v3→v4, Audit-Trail)
  - ./PHASE16_E3_RUNBOOK_v2.md                       # 📕 v2 (superseded durch v3→v4, Audit-Trail)
  - ./PHASE16_E3_RUNBOOK_v3.md                       # 📕 v3 (superseded durch v4, Audit-Trail)
  - ./PHASE16_AUTONOMY_PREREGISTRATION_v3.md         # 📕 aktive Vorregistrierung (PASS-Kriterien + vorregistrierte Werte — zwingend vorher lesen)
  - ../docs/concepts/phase16_activation_plan.md      # 📕 §6 E3 (Quelle, S. 797–808), §11 #5/#6/#7
  - ./scripts/autonomy_report.py                     # 🔧 der tägliche Tages-/Summary-Report (K1–K9)
  - ./systemd/                                       # 📂 die 4 User-Units (Phase-16-R5)
  - ../scripts/install_units.sh                      # 🔧 idempotenter Installer (`--dry-run`, `--verify`)
  - ./SESSIONS_ARCHIVE.md                            # 📦 Session-Historie (E1/E2/E3-Sessions)
  - ./PHASE16_E3_RUNBOOK_v4.md                       # 📕 DIESE DATEI (locked, v4 ab 2026-09-23)
updated: 2026-09-30 (3 Header-Card-Pfade korrigiert in Session #35: `./phase16_activation/systemd/` → `./systemd/` und `./scripts/install_units.sh` → `../scripts/install_units.sh`; locked-Inhalt unverändert)
---
# PHASE16_E3_RUNBOOK v4 — Operator-Pfad für den 2-Wochen-Autonomie-Test

> **v4 supersedet v3** (`PHASE16_E3_RUNBOOK_v3.md`). v3 bleibt im Repo als historischer
> Audit-Stand; **nicht** mehr lesen für den E3-Start. v4 ist die einzige Quelle der
> Wahrheit für den Operator-Pfad. v4 ist locked-nach-Commit (Prereg-Disziplin analog
> v1, v2, v3 und `PHASE16_AUTONOMY_PREREGISTRATION_v3.md`): Korrekturen sind nur als
> `PHASE16_E3_RUNBOOK_v5.md` mit Datum und Grund möglich — niemals ein Edit hier.
>
> **Was v4 anders macht als v3 (5 Korrekturen, alle Phase-16-R5/R6 + Prereg v3):**
> 1. **§0 BLUF + §3 Restart-Sequenz** neu: **systemd-User-Units** sind der primäre
>    Pfad (`systemctl --user start tradingbot-*`), `scripts/restart-services.sh`
>    ist nur noch der **manuelle Notweg**. Begründung: nach dem 2026-09-20-Reboot
>    war der Bot 12 Tage aus, weil kein Autostart existierte (F1, Phase-16-Phasenkopf);
>    4 Units + Installer (Phase-16-R5, Commits `9c9f7dd` + `94f6331` + `eaf464d`)
>    beheben das strukturell.
> 2. **§2.3 Keyring-Check erweitert:** `store_credential.py --status` (aus v3,
>    unverändert) **plus** Beweis, dass die Credentials auch aus einer echten
>    systemd-Unit-Umgebung erreichbar sind (transienter Unit-Test via
>    `systemd-run --user --wait --pipe`). Hintergrund: am 2026-09-20-Boot
>    unlockte `gkr-pam` den Keyring nicht (`gkr-pam: couldn't unlock the login
>    keyring`, Journalctl-Log), so dass eine User-Unit, die **vor** dem Login
>    gestartet wäre, in den fail-closed Credential-Preflight gelaufen wäre.
>    v4 verifiziert die Unit-Umgebung aktiv.
> 3. **§4 Day-0 t0+5 min** verwendet `systemctl --user status 'tradingbot-*'`
>    statt `pgrep` — Operator sieht auf einen Blick `active`/`failed`/`inactive`.
> 4. **§5 Tagesroutine** referenziert K1 + K9 aus Prereg v3 (K1 = Operator-Starts,
>    K9 = Auto-Restarts aus `NRestarts`). Implementation in `autonomy_report.py`
>    folgt in R7.3; bis dahin manuelle Sichtprüfung der `--day`-JSON-Outputs.
> 5. **§7 Watch-Items W6/W7 neu** (LS-Bars auf `:00.000Z` + Log-Größe <200 MB/Tag);
>    altes v3-W6 (min_evidence) wandert auf v4-W8. W6/W7-Repräsentation in
>    `autonomy_report.py` optional, R7.3 fügt sie hinzu.
>
> **Was v3 anders macht als v2 (1 Korrektur, Drift #7 aus Session #24):**
> *(verbatim aus v3-Einleitung, hier referenziert; v3 bleibt byte-identisch im Repo)*
> 1. §2.3 Keyring-Check: `cst`/`demo_token`/`token` (existieren nicht in
>    `broker_wrapper/credentials.py`) → `store_credential.py --status` als kanonischer
>    Check + optionaler 8-Zeichen-Fingerprint mit `IG_DEMO_*`-Namen.
>
> **Was v2 anders macht als v1 (6 Korrekturen aus Session-#13-Pre-Flight):**
> *(verbatim aus v3-Einleitung, hier referenziert; v2 bleibt byte-identisch im Repo)*
> §1.2 Schema-Floor (`_schema_version` ≠ `PRAGMA user_version`) · §1.4 Truncate um
> 4 Pre-Wrapper-Logs · §1.5/§3.0/§5 Spalten (`status` statt `active=1`, `last_verified_at`
> statt `last_verified_utc`) · §3.0 `source_spend` in `data/bars.sqlite` · §3.0
> `paper_trades` mit `status`/`created_utc` · §1 Pflicht-Operator-SQL für 3 SUN*-Epics.

---

## 0 · BLUF

**Reboot-Test (AK-R6)** ist jetzt Teil des E3-Pfads — der Bot muss nach einem
Reboot **ohne Handgriff** wieder laufen. Pre-Flight + Restart-Sequenz sind
zwei getrennte Schritte: Pre-Flight verifiziert das Substrat, Restart startet
die 4 systemd-User-Units. Nach dem ersten Run **bleibt** die Maschine eingeloggt
(systemd-Autostart greift beim nächsten Reboot automatisch). Täglich
`scripts/autonomy_report.py --day` lesen. Bei Auffälligkeit die in §6 gelisteten
Trigger-Bedingungen prüfen — die Exec-Session kommt nur, wenn ein Trigger greift.

**Reihenfolge (Operator-Pfad in dieser Reihenfolge ausführen, kein Schritt überspringen):**

1. **§1 Pflicht-Operator-SQL** (3 SUN*-Epics → `quarantined`, pre-E3-Blocker aus B3
   forward-only Lücke) — *unverändert ggü. v3.*
2. **§2 Pre-Flight** (6 Schritte + Reboot-Test-Beweis, ≤ 10 min) — Status-Checks +
   Keyring + Truncate + DB-Health.
3. **§2.7 Prereg-Aktiv-Block-Eintragung** + Folge-Commit `phase16: docs -- E1-Aktiv-Block-Eintragung`.
4. **§3 Restart-Sequenz** (`systemctl --user start tradingbot-*` als Primärpfad;
   `restart-services.sh start` als Notweg) + K7-Caps-Pin-Verify.
5. **§4 Day-0-Checks Timeline** (5min / 30min / 4h / 24h).
6. **§5 Tagesroutine** (täglich `--day`, jetzt K1+K9 beobachten).
7. **§8 Tag 10 Closeout** (`--summary` + Exec-Session für Handover/SVG).

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
> **Audit-Trail:** dieser SQL-Schritt wird im `PHASE16_AUTONOMY_PREREGISTRATION_v3.md`-
> Aktiv-Block unter „Operator-Aktionen vor E3-Start" eingetragen (analog zu B2
> Schema-Apply, Session #3).

```bash
# Pre-Verify (erwartet: 3 Zeilen, falls nicht schon früher geräumt)
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

> Dauer: ≤ 10 min, mechanisch. Wenn etwas nicht hält → **nicht starten**, stattdessen
> Exec-Session rufen (siehe §6 Trigger-Bedingungen). Reboot-Test (§2.8) ist neu in v4
> und **vor** dem ersten Restart auszuführen — er beweist, dass die systemd-Units
> nach einem Reboot automatisch starten.

### 2.1 — Liveness-Check (heute = 4 Dienste tot seit Boot 2026-09-20)

```bash
systemctl --user status 'tradingbot-*' --no-pager 2>&1 | head -20
```

Erwartung: alle 4 Units `inactive (dead)`. `enabled` muss stehen — wenn ein Dienst
`disabled` zeigt → §2.8 Reboot-Test kann nicht greifen, Installer erneut laufen
(`bash scripts/install_units.sh --verify`). Wenn ein Dienst `failed` zeigt → Exec-Session.

> **Hintergrund:** im v3-Runbook war `bash scripts/restart-services.sh status` der
> Liveness-Check. v4 nutzt `systemctl`, weil die 4 Units die kanonische
> Service-Identität sind (Phase-16-R5); `restart-services.sh` startet ohne
> systemd-Eintrag (= keine Flap-Protection, keine Logs nach `data/state/run_*.log`,
> keine NRestarts-Messung für K9).

### 2.2 — Schema-Floor 9 verifizieren (unverändert ggü. v3)

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

### 2.3 — Keyring erreichbar (Demo-Credentials gesetzt + Unit-Umgebung)

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

```bash
# 3) NEU in v4: Beweis, dass Credentials aus einer echten systemd-Unit-Umgebung
#    erreichbar sind. Hintergrund: am 2026-09-20-Boot unlockte gkr-pam den Keyring
#    NICHT (Journal: "couldn't unlock the login keyring"), so dass eine User-Unit,
#    die VOR dem graphischen Login gestartet wäre, in den fail-closed Credential-
#    Preflight gelaufen wäre. v4 beweist die Unit-Umgebung jetzt vor dem Restart.
phase1_broker_wrapper/.venv/bin/python -c "
import subprocess
r = subprocess.run(
    ['systemd-run', '--user', '--wait', '--pipe',
     '/home/trading-bot/trading-bot/phase1_broker_wrapper/.venv/bin/python',
     '-c', 'from broker_wrapper.credentials import get_credential; v=get_credential(\"ig_demo_api_key\"); print(\"ig_demo_api_key:\", \"FOUND\" if v else \"EMPTY\", \"len\", len(v) if v else 0)'],
    capture_output=True, text=True, timeout=20)
print('exit', r.returncode)
print('stdout:', r.stdout.strip())
print('stderr:', r.stderr.strip()[:500])
"
```

Erwartung: Exit 0, stdout `ig_demo_api_key: FOUND len 41` (oder ähnliche Länge ≥ 20).
Exit ≠ 0 oder `EMPTY` → Exec-Session; Keyring ist in der Unit-Umgebung **nicht**
greifbar, Restart wird fehlschlagen.

> **Hard Rule 1 (root-CLAUDE.md):** Credentials werden **nie** in Dateien geschrieben,
> **nie** ins `.env`, **nie** ins Log. `store_credential.py` liest Werte via `getpass`
> (kein Echo, keine Shell-History); `get_credential` und `--status` geben nie Werte aus.
> Die 8-Zeichen-Fingerprints im optionalen Check sind eindeutig kein Volltext.

### 2.4 — K1-Log-Truncate (unverändert ggü. v3)

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
> (FAIL Kriterium 1, Plan §1 Prereg §Erlaubte Operator-Ereignisse b).

### 2.5 — Datenbank-Health (unverändert ggü. v3)

```bash
sqlite3 data/bars.sqlite "SELECT count(*), source FROM bars GROUP BY source;" 2>&1 | head -10
sqlite3 data/bars.sqlite "SELECT count(*), kind FROM source_spend GROUP BY kind;" 2>&1
sqlite3 data/trading_bot.sqlite "SELECT count(*), status FROM paper_trades GROUP BY status;" 2>&1
sqlite3 data/trading_bot.sqlite "SELECT count(*) FROM trade_outcomes WHERE account='demo';" 2>&1
sqlite3 data/trading_bot.sqlite "SELECT count(*) FROM instrument_universe WHERE status='active' AND epic LIKE 'IX.D.SUN%';" 2>&1
```

> **v1-Drift-Korrekturungen (unverändert ggü. v3):**
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

Wenn eines schlägt fehl → §6 T-2 / T-3 / T-4.

### 2.6 — Akten-Vermerk im Preregistrierungs-Doc (AK13) — neu: v3 statt v2

Im `PHASE16_AUTONOMY_PREREGISTRATION_v3.md`-Aktiv-Block das Feld **Start (E3-Restart-
Zeitstempel)** mit dem genauen Zeitpunkt eintragen, **bevor** die erste Start-Zeile
im Log landet. Das ist eine **Eintragung**, kein Edit (im Prereg-Doc explizit
dokumentiert). Format: Berlin, ISO 8601, Sekunden-genau. **Anschließend** Commit
`phase16: docs -- E1-Aktiv-Block-Eintragung` mit dem Zeitstempel.

Zusätzlich eintragen: **Operator-SQL-Audit** für die 3 SUN*-Epics
(Epic-Liste + ts_utc der Ausführung) + **Operator-Systemd-Audit** (4 Units
`is-enabled = enabled`).

### 2.7 — systemd-Unit-Status-Pin (NEU in v4)

```bash
systemctl --user list-unit-files 'tradingbot-*'
```

Erwartung: 4 Zeilen mit `STATE = enabled`. Wenn ein Dienst `disabled` zeigt →
`bash scripts/install_units.sh` (ohne `--dry-run`) erneut laufen — der Installer
ist idempotent. Wenn `static` → Exec-Session (Unit-Datei kaputt).

### 2.8 — Reboot-Test (NEU in v4, AK-R6)

> **Hintergrund:** am 2026-09-20-Boot startete der Bot **nicht** automatisch (F1).
> Es gab **keinen** Autostart (kein systemd-Unit, kein Cron, kein Skript). Die 4
> Units aus R5 wurden erst **nach** diesem Boot installiert (2026-09-22 19:22),
> so dass sie beim 09-20-Boot strukturell nicht greifen konnten. **Erst der nächste
> Reboot ist der erste ehrliche Test.** v4 macht den Test explizit vor dem Restart.
>
> **Risiko:** am 2026-09-20-Boot unlockte `gkr-pam` den Keyring nicht
> (`couldn't unlock the login keyring`). Eine User-Unit, die **vor** dem
> `graphical-session.target` startet, würde in den fail-closed Credential-Preflight
> laufen, 3× in 90 s restart-en, in `StartLimitBurst=3` enden und in 90 s endgültig
> tot sein. v4 verifiziert die Reihenfolge (Units wollen `graphical-session.target`,
> nicht `default.target`, siehe `phase16_activation/systemd/tradingbot-scheduler.service`
> Kommentarblock) UND beweist die Keyring-Erreichbarkeit in §2.3.3.
>
> **Operator-Pfad:** Reboot durchführen, **vor** dem ersten Restart. Erwartung:
> nach dem Boot sind alle 4 Units `active (running)`, ohne Handgriff.

```bash
# 1) Reboot (sauber, geplant)
sudo shutdown -r now "Phase-16-AK-R6-Reboot-Test"
# oder über die UI, falls kein sudo verfügbar

# 2) Nach dem Login (manuelle Anmeldung) — Desktop-Session muss wieder aktiv sein
loginctl show-session self -p State
# erwartet: State=active

# 3) Status nach 60 s Settle-Zeit (grafischer Login + Keyring-Unlock brauchen ~10-30 s)
sleep 60
systemctl --user status 'tradingbot-*' --no-pager 2>&1 | head -40
# Erwartung: alle 4 Units "active (running)" oder "active (running) since ..."

# 4) Verify Caps (K7-Pin)
grep "starting scheduler daemon" data/state/run_scheduler.log | tail -1
# Erwartet: enthält max_trades=5, daily_loss_cap=1800.0, cycle=5min, account=demo

# 5) Verify, dass KEINE Tracebacks im Log sind (Drift #12 Test)
grep -c "NameError\|Traceback" data/state/run_scheduler.log
# Erwartet: 0 (frischer Log nach Boot)
```

Erwartung Schritt 3: **alle 4 Units `active (running)`**. Wenn ein Dienst `failed`:
`journalctl --user -u tradingbot-<svc> -b --no-pager -n 50` — der erste Verdächtige
ist die **Keyring-Reihenfolge** (`gkr-pam`-Unlock), nicht die Unit-Syntax (die ist
verify-geprüft vom Installer). Wenn alle 4 Units `inactive`: Exec-Session (Autostart
greift nicht, Installer-Problem oder Unit-Datei falsch verlinkt).

> **Wichtig:** der Reboot-Test ist die einzige ehrliche Validierung des Auto-Starts.
> Wenn er hier bereits scheitert, ist der geplante 10-Tage-Lauf strukturell
> unfähig zum PASS (F1 wiederholt sich beim nächsten ungeplanten Reboot).

---

## 3 · Restart-Sequenz (Primärpfad: systemd; Notweg: Wrapper-Skript)

> **v4-Änderung:** Primärpfad ist jetzt `systemctl --user`, weil die 4 Units die
> kanonische Service-Identität sind (Logs nach `data/state/run_*.log`,
> Flap-Protection, NRestarts für K9). `scripts/restart-services.sh` bleibt
> **ausschließlich** als manueller Notweg im Runbook, wenn systemd aus irgendeinem
> Grund nicht greift (z. B. `graphical-session.target` ist nie aktiv geworden).

### 3.1 — Primärpfad (systemd)

```bash
# 1) Daemon-Reload, falls Unit-Datei editiert wurde (in v4-Fenster: unüblich,
#    Hotfix-Commits auf Units sind verboten — Prereg §"Nicht erlaubt")
systemctl --user daemon-reload

# 2) Alle 4 Units starten
systemctl --user start \
  tradingbot-scheduler.service \
  tradingbot-recorder.service \
  tradingbot-discovery.service \
  tradingbot-webui.service

# 3) 30 s Settle, dann verifizieren
sleep 30
systemctl --user is-active \
  tradingbot-scheduler.service \
  tradingbot-recorder.service \
  tradingbot-discovery.service \
  tradingbot-webui.service
# erwartet: 4 × "active"

# 4) Caps-Pin (K7) verifizieren
grep "starting scheduler daemon" data/state/run_scheduler.log | tail -1
# erwartet: "starting scheduler daemon (account=demo, max_trades=5,
#            daily_loss_cap=1800.0, cycle=5min)."
#             ^^^                  ^^^                  ^^^             ^^^^
#             K7 #1                K7 #2                K7 #3           K7 #4
```

> **Reihenfolge** ist absichtlich so: Scheduler zuletzt, weil er die Credentials
> aus dem Keyring lädt (Credential-Preflight); Recorder/Discovery/WebUI laufen
> ohne Keyring. Wenn Scheduler in den fail-closed Credential-Preflight läuft,
> ist das **Schlüssel-Beleg**, dass die Reihenfolge von `graphical-session.target`
> nicht gehalten hat — **nicht** die Unit-Syntax (die ist verify-geprüft vom
> Installer). Bei `inactive`: `journalctl --user -u tradingbot-scheduler -b
> --no-pager -n 50`.

### 3.2 — Notweg (Wrapper-Skript — nur wenn §3.1 scheitert)

```bash
bash scripts/restart-services.sh start
sleep 30
bash scripts/restart-services.sh status
# erwartet: alle 4 alive (PID in der Status-Ausgabe)
```

> **Achtung:** der Wrapper-Pfad umgeht **alle** systemd-Vorteile — keine
> Flap-Protection, keine Logs nach `data/state/run_*.log` (Logs gehen nach
> `data/state/run_<wrapper>.log` ohne systemd-Standard-Append), keine
> NRestarts-Messung für K9. **Wenn §3.2 nötig ist:** Exec-Session danach
> (Reboot-Test muss wiederholt werden, sonst gilt Autostart als nicht bewiesen).

### 3.3 — K1/K9-Tagesbasis (NEU in v4, ab R7.3 implementiert)

```bash
# K1 (Operator-Starts/Tag) — bis R7.3: manuelle Sichtprüfung der Log-Start-Zeilen
grep "starting scheduler daemon\|starting recorder\|[run_discovery] starting\|[run_webui] dashboard on" \
  data/state/run_*.log | awk '{print $1, $2}' | sort -u

# K9 (Auto-Restarts/Tag) — bis R7.3: manuelles systemd-Show
systemctl --user show -p NRestarts \
  tradingbot-scheduler.service \
  tradingbot-recorder.service \
  tradingbot-discovery.service \
  tradingbot-webui.service
```

Erwartung Tag 1: K1 = 1 Start je Dienst (E3-Start); K9 = 0 (kein Auto-Restart seit Boot).
K9 > 0 am Tag 1 → §6 T-13 (Auto-Restart-Schleife).

---

## 4 · Day-0-Checks Timeline

> Zeitfenster relativ zum E3-Start (`tail -1` in §3 = t0). Die Checks sind Beobachtungen
> — kein Operator-Eingriff außer im Trigger-Fall (§6). Anomalien notieren (Zeitstempel
> + Befund); Exec-Session in der Folgesession fragen.

### t0 + 5 min — Liveness-Smoke

```bash
systemctl --user status 'tradingbot-*' --no-pager 2>&1 | head -40
# Erwartung: alle 4 "active (running)"
```

Wenn ein Dienst `failed` oder `inactive` → §6 T-1 / T-13. Der `pgrep`-Pfad aus v3
ist obsolet — `systemctl` ist die kanonische Sicht.

### t0 + 30 min — Substrat-Inbetriebnahme (Spalten-Drift korrigiert, unverändert ggü. v3)

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

Wenn eines schlägt fehl → §6 T-2 / T-3 / T-4.

### t0 + 4 h — Heartbeat & Preflight (unverändert ggü. v3)

```bash
grep '"measurement_heartbeat"' data/state/research_health.jsonl 2>/dev/null | tail -5
grep "PreflightError\|preflight failed" data/state/run_scheduler.log
```

> **v1-Korrektur:** Heartbeat liegt in `data/state/research_health.jsonl` (nicht
> `data/state/research_heartbeat.jsonl`, das es nicht gibt).

Erwartung: ≥ 1 Heartbeat mit `"ok": true`. Kein PreflightError. Wenn Heartbeat `false`
oder PreflightError → §6 T-5.

### t0 + 24 h (= Tag 1) — Tagesabschluss

```bash
phase1_broker_wrapper/.venv/bin/python phase16_activation/scripts/autonomy_report.py \
  --day "$(date -d 'yesterday' +%F)"
# Exit 0 = PASS, 1 = FAIL (mind. ein Kriterium schlug fehl), 2 = ERROR (Quelldatei
# fehlt/korrupt). Output ist data/reports/autonomy_<day>.json (gitignored).
```

Erwartung Tag 1: **K1–K9 grün** (K3 = FAIL erwartet am Tag 1). Falls etwas rot:
- K1 rot → Reboot / Restart ohne Backoff ⇒ FAIL Kriterium 1 (P17), Tag läuft weiter.
- K2 rot → WebUI-Down oder Datenfundament-Down ⇒ §6 T-6 / T-7.
- K3 rot → keine autonomen Trades. **OK** am Tag 1 (Watch-Item, n=1 Trade ist
  empirisch selten am ersten Tag — der Effekt kumuliert).
- K4 rot → Heartbeat inkonsistent. Wenn an ≥ 2 Tagen → §6 T-5.
- K5 rot → Backoff oder Margen-Reject-Häufung. Exec-Session für A6-Live-Verify.
- K6 rot → Token-Budget vor 17:30 erschöpft. **FAIL** (Plan §6 E2 K6, hard fail-closed).
  *Hinweis 2026-09-23:* an Debatte-Tagen strukturell erwartbar (Prereg v3 Befund 7);
  Exec-Session prüft, ob Budget-Gate scharf gefeuert hat.
- K7 rot → Caps-String-Pin verletzt; Exec-Session, sonst Drift unentdeckt.
- K8 rot → 0 Scheduler-Zyklen am Tag. Strukturell FAIL, unterscheidet „läuft ruhig"
  von „läuft nicht" (F8-Fix). Siehe §6 T-14.
- K9 rot → > 10 Auto-Restarts/Tag je Unit = pathologisch. Siehe §6 T-13.

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
<start> --to <end>` werden die 9 Kriterien über das Fenster aggregiert (für Tag-10-
Closeout, einmalig).

**Was der Operator NICHT tut:**

- Keine manuellen Restarts (`systemctl --user start tradingbot-<svc>` ohne Backoff-
  KILL-Vorbedingung; `bash scripts/restart-services.sh start` als No-Op auf bereits
  laufende Dienste).
- Kein Trade-Eingriff (Force-Trigger; §Prereg Hard Rule 5, daily_loss_cap = 1800 ⇒
  PNL < 0 sperrt den Force-Trigger strukturell).
- Kein Hotfix-Commit auf Caps/Arms (`max_trades`, `daily_loss_cap`,
  `enable_*`-Defaults) oder Units.
- Keine DB-Repair außerhalb dieses Runbooks.
- Kein Browser-Refresh auf das WebUI für „mehr Daten" — Polling ist 7 s, der
  Server ist read-only.

**Was der Operator TÄGLICH prüft (zwei Werte, eine Minute):**

1. `--day`-Exit-Code: `0` weiter, `1` Kriterium verletzt → §6 Trigger-Liste gehen,
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
| **T-1** Dienst tot nach Restart | `systemctl --user status 'tradingbot-*'` zeigt einen Dienst `failed` oder `inactive` UND Start-Zeile fehlt im Log | Exec-Session, **nicht** manuell restarten (das ist FAIL Kriterium 1) |
| **T-2** Schema-Floor verletzt | `count(*) FROM _schema_version` ≠ 9, oder `_schema_version` weg | Exec-Session (B2 nochmal nötig) |
| **T-3** Wochenend-Epic zurück in active | `instrument_universe WHERE status='active' AND epic LIKE 'IX.D.SUN%'` > 0 | Exec-Session (B3-Regression oder Pflicht-SQL §1 wurde vergessen) |
| **T-4** `bars.source='ls'` bleibt 0 nach 24 h | t0+24 h Substrat-Smoke: keine `ls`-Bars | Exec-Session, D1.2-Wrapper prüfen |
| **T-5** Heartbeat `false` an ≥ 2 Tagen | K4 FAIL ≥ 2× im `--summary`-Output | Exec-Session |
| **T-6** WebUI nicht erreichbar (localhost:8000) | `curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/` ≠ 200, nach 1 min | Exec-Session (K2 WebUI-Operator-Sichtung kann nicht erfüllt werden, Prereg §K2 ehrlich) |
| **T-7** `KILL`-Datei ohne Auto-Backoff | `cat data/state/KILL` zeigt `reason != "auto:backoff"` (z. B. `manual:*`) | **Nicht anfassen**, Exec-Session (Operator-Eingriff wäre FAIL Kriterium 1) |
| **T-8** Token-Budget vor 17:30 erschöpft | K6 FAIL im `--day`-Report | Exec-Session (Plan §6 E2 K6 fail-closed, hard; heute strukturell möglich, Prereg v3 Befund 7) |
| **T-9** Margen-Reject-Häufung | `grep "INSUFFICIENT_FUNDS" data/state/run_scheduler.log` > 2 pro Tag | Exec-Session, D3-Margin-Headroom prüfen (Watch-Item Plan §13 #8) |
| **T-10** Reboot / Auto-Reboot getriggert | `last reboot` zeigt heutigen Eintrag; oder systemd hat Units auto-gestartet (= K9-Tages-Differenz > 0) | Exec-Session, FAIL Kriterium 1 (Prereg §Erlaubte b); K9 wird separat gezählt |
| **T-11** Desktop-Session verloren | `loginctl show-session` zeigt keinen aktiven User-Login | **Nicht** neu einloggen ohne Exec-Session-Rücksprache (Keyring-Relogin = FAIL Kriterium 1); stattdessen Exec-Session |
| **T-12** Trade mit nicht-Demo-Account | `SELECT DISTINCT account FROM trade_outcomes` ≠ `'demo'` | **Sofort** Exec-Session (Hard Rule 4: Live-Account verboten); Bot stoppen via `kill -TERM $(pgrep -f scheduler.run)` als Notbremse (oder `systemctl --user stop tradingbot-scheduler.service`) |
| **T-13** Auto-Restart-Schleife | K9 > 10/Tag je Unit, oder `journalctl --user -u tradingbot-<svc> -b` zeigt `Start request repeated too quickly` | Exec-Session, Restart-Logik prüfen (Flap-Schutz, Credential-Preflight) |
| **T-14** K8 Liveness-FAIL | K8 FAIL (`research_health.jsonl` 0 Einträge an einem Handelstag) | Exec-Session: Scheduler läuft nicht, oder Process-Hang. Strukturell FAIL (F8) — unterscheidet „läuft ruhig" von „läuft nicht" |

---

## 7 · Watch-Items (nicht PASS, aber zu beobachten)

> Aus `PHASE16_AUTONOMY_PREREGISTRATION_v3.md §Watch-Items`. Werden **nicht** im
> `--day`-Report als PASS-Kriterium ausgewertet; W6/W7 sind beobachtbar (R7.3-Code
> noch pending), W1–W5 + W8 nur durch Operator-Sichtprüfung. Operator beobachten,
> Exec-Session fragen wenn unerwartet.

| Watch | Was zu beobachten | Schwelle |
|---|---|---|
| **W1** BUY-Bias | Alle autonomen Trades sind BUY | Empirisch 8/8 BUY in Phase-9-Live, Plan §2.4. SELL = Befund, nicht PASS-Verletzung. |
| **W2** DAX-Only | Aktive Epics außer Wochenend: DAX-dominant | Phase-9-Live-Substrat. Nach B3 + Universe-Refresh: DAX-dominant mit MIB/FTSE/STXE/DOW/SPTRD als Sekundär-Slots (Session #30 Update). Schwelle: DAX-Anteil < 50 % der aktiven Epics = Befund (= strukturelle Drift weg von der DAX-Heimat). Pflegschaft mit Phase-17. |
| **W3** 09:05-Breaker | `circuit open`-Zeilen 09:05–09:20 an Tag 1 | = 0 (Plan §7 AK17 + C5). Wenn doch → Befund, C5-Semantik greift nicht. |
| **W4** LS-Bars | `bars.source='ls'` wächst ab Tag 1 | D1.2 Wrapper aktiv. Wenn 0 nach 24 h → T-4. |
| **W5** Zombie-Zahl | `[python] <defunct>` Prozesse | ≤ 2 (Plan §2.3). Wenn > 5 → Befund (P14-D Sleep-Cap greift nicht). |
| **W6** LS-Bars ms-Fix (NEU in v4) | jede `bars.source='ls'`-Zeile endet auf `:00.000Z` | Drift #13 Fix `d40f072` aktiv. Stichprobe: `SELECT count(*) FROM bars WHERE source='ls' AND ts_utc NOT LIKE '%.000Z'` = **0** (oder < Drift-Backlog-Erwartung). Bis R7.3: manuelle Sichtprüfung des ersten 100-Zeilen-Samples. |
| **W7** Log-Größe (NEU in v4) | `du -m data/state/run_scheduler.log` < 200 MB/Tag | Drift #12 Fix `9ab50e8` aktiv (vorher 2,37 GB über 10 Tage). Bis R7.3: täglicher `du`-Smoke. |
| **W8** `min_evidence` vs. Trade-Zahl (war v3-W6) | Validator-Default `min_evidence` / `instinct_n_min` vs. autonome Trade-Zahl | n ≈ 10–20 ≪ 50 → keine Promotion, VETO 5 No-Op by design (Plan §13 #8). |

---

## 8 · Tag 10 — Closeout

```bash
# 1) Summary über das gesamte Fenster (10 Handelstage Berlin)
phase1_broker_wrapper/.venv/bin/python phase16_activation/scripts/autonomy_report.py \
  --from "$(date -d '<Tag 0 Datum>' +%F)" --to "$(date +%F)" --summary

# 2) Erwartung: overall_verdict == "PASS" (alle 9 Kriterien über das Fenster)

# 3) Wenn PASS: Exec-Session rufen für Closeout-Handover
#    (phase16_activation/PHASE16_CLOSEOUT_Handover.md +
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
- **Keine Code-Änderungen.** Hotfix-Commits auf Caps/Arms/Units sind in Prereg §"Nicht
  erlaubt" explizit FAIL Kriterium 1. Cross-Phase-Bugfixes in der 2-Wochen-Phase
  sind Phase-17-Material, nicht Phase-16.
- **Keine Prozess-Supervision.** Auto-Restart nach Reboot ist jetzt **in-scope**
  (Phase-16-R5 systemd-Autostart), aber **nicht** Auto-Restart nach Operator-Befehl
  (= FAIL Kriterium 1). Die Desktop-Session manuell eingeloggt zu lassen ist die
  Vorregistrierungs-Disziplin (Keyring-Bedarf).
- **Keine Fehlgriff-Diagnose.** Die §8-Fehlgriffe-Tabelle im Plan (z. B. „Heartbeat
  nach D1 weiter CRITICAL 'measurement arm off'") gehört in die Exec-Session; der
  Operator liest Symptom → Trigger, nicht Symptom → Root Cause.
- **Keine v1/v2/v3-Referenz.** v1/v2/v3 sind superseded. Wenn v1/v2/v3-Verweise im
  Code/anderen Docs auftauchen, sind sie historisch — v4 ist die Quelle der Wahrheit.

---

## 10 · Cross-Refs

- Vorregistrierung v3 (PASS-Kriterien, Operator-Ereignisse, Watch-Items): [`./PHASE16_AUTONOMY_PREREGISTRATION_v3.md`](./PHASE16_AUTONOMY_PREREGISTRATION_v3.md)
- v3 (superseded, Audit-Trail): [`./PHASE16_E3_RUNBOOK_v3.md`](./PHASE16_E3_RUNBOOK_v3.md)
- v2 (superseded, Audit-Trail): [`./PHASE16_E3_RUNBOOK_v2.md`](./PHASE16_E3_RUNBOOK_v2.md)
- v1 (superseded, Audit-Trail): [`./PHASE16_E3_RUNBOOK.md`](./PHASE16_E3_RUNBOOK.md)
- Plan §6 Block E Steps E1–E4: [`../docs/concepts/phase16_activation_plan.md`](../docs/concepts/phase16_activation_plan.md) S. 758–815
- Plan §6 E3 (Quelle dieses Runbooks, Bash-Stufen 797–808): ebd.
- Plan §7 Akzeptanz AK4/AK5/AK5b/AK9/AK11/AK12/AK13/AK14/AK15/AK16/AK17: ebd. S. 821–842
- Plan §8 Fehlgriffe-Symptom-Tabelle: ebd. S. 846–865 (Exec-Session-Pfad)
- Plan §10 Out-of-Scope: ebd. S. 895–910 (Strategy-Bewertung, Auto-Restart, etc.)
- Plan §11 Operator-Aktionen #5 (Restart), #6 (täglicher Report), #7 (Tag 10 Closeout): ebd. S. 913–924
- Plan §13 Opus-Review #5 (Supervision), #6 (WebUI-Aliveness unmessbar), #8 (Bridge unerreichbar), #9 (Budget-Datei-Korruption): ebd. S. 935–947
- **Phase-16-R5 systemd-User-Units + Installer:** [`./systemd/`](./systemd/) + [`../scripts/install_units.sh`](../scripts/install_units.sh) (idempotent, `--dry-run`, `--verify`)
- **Restart-Pfad-Notweg:** [`../scripts/restart-services.sh`](../scripts/restart-services.sh) (4-Services, sequenziell, kein systemd-Standard)
- Tages-/Summary-Report: [`./scripts/autonomy_report.py`](./scripts/autonomy_report.py) + [`./tests/test_autonomy_report.py`](./tests/test_autonomy_report.py) (5+ AK-Tests, Suite-Zeit ≤ 2 s)
- Phase-15-Vorgänger (E1–E3 dort offen → hier geschlossen): [`../phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md`](../phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md)
- **Phase-16-R-Exec-Plan (R5/R6/R7 Quelle):** [`./PHASE16_R_EXEC_PLAN.md`](./PHASE16_R_EXEC_PLAN.md)

---

## 11 · Diff v3 → v4 (für Audit-Trail)

| Stelle | v3 | v4 | Grund |
|---|---|---|---|
| §0 BLUF + Reihenfolge | Pre-Flight → Restart | Reboot-Test (§2.8) **vor** Restart, systemd-Primärpfad | Phase-16-R5: systemd-Autostart ist die Kern-Antwort auf F1 (Bot aus seit 2026-09-20-Boot); Reboot-Test beweist, dass die 4 Units nach einem Reboot **ohne Handgriff** wieder laufen, bevor der 10-Tage-Lauf sich darauf verlässt |
| §2.1 Liveness-Check | `bash scripts/restart-services.sh status` | `systemctl --user status 'tradingbot-*'` | kanonische Service-Sicht; pgrep/PID-Pfad ist Wrapper-Opazität, nicht Service-Identität |
| §2.3 Keyring-Check | `store_credential.py --status` + optionaler Fingerprint | + **transienter Unit-Test** via `systemd-run --user --wait --pipe` | 2026-09-20-Boot-Log: `gkr-pam: couldn't unlock the login keyring` — Keyring kann in der User-Shell erreichbar sein, aber in der Unit-Umgebung (vor graphischem Login) leer sein. v4 beweist die Unit-Umgebung **vor** dem Restart, nicht erst beim ersten Reboot |
| §2.7 systemd-Unit-Status-Pin | nicht vorhanden | `systemctl --user list-unit-files 'tradingbot-*'` (4 × `enabled` erwartet) | Installer (Phase-16-R5) ist idempotent, aber wenn ein Symlink manuell gelöscht wurde, schlägt der Reboot-Test ohne Vorwarnung fehl; v4 pinnt das vor dem Restart |
| §2.8 Reboot-Test | nicht vorhanden | **AK-R6-Reboot + Verifikation** in 5 Schritten | ohne diesen Test ist der geplante 10-Tage-Lauf strukturell unfähig zum PASS (F1 wiederholt sich beim nächsten ungeplanten Reboot) |
| §3 Restart-Sequenz | `bash scripts/restart-services.sh start` | Primärpfad `systemctl --user start tradingbot-*`, Wrapper nur als §3.2-Notweg | systemd bringt StandardOutput-Append nach `data/state/run_*.log` (sonst K1/K5/K8 blind), Restart=on-failure mit StartLimit-Schutz, NRestarts-Messung für K9 |
| §3.3 K1/K9-Tagesbasis | nicht dokumentiert | manuelle Sichtprüfung bis R7.3 implementiert | K1 + K9 sind neu in Prereg v3 (Phase-16-R5 + R7); bis autonomy_report.py-Code-Change (R7.3) ist die Messung manuell |
| §4 Day-0 t0+5 min | `pgrep -af "python -m ..."` × 4 | `systemctl --user status 'tradingbot-*'` | analog §2.1 — kanonische Sicht, ein Befehl statt vier |
| §4 t0+24 h Tag-1-Erwartung | K1–K7 grün | K1–K9 grün, **K8 Liveness explizit** (F8-Fix) | Prereg v3 fügt K8 (Liveness) und K9 (Auto-Restarts) hinzu; K6-FAIL-Hinweis ergänzt (strukturelles Reiß-en-an-Debatte-Tagen, Befund 7) |
| §5 Tagesroutine | `--day` Exit-Code + JSON-Existenz | gleich, plus K9-Stichprobe wenn `--day` Exit ≠ 0 | K9 ist jetzt eine eigene Fehlerklasse (Restart-Schleife) |
| §6 Trigger T-1 | `restart-services.sh status` zeigt Dienst "dead" | `systemctl` zeigt Dienst `failed`/`inactive` | analog §2.1 — Wrapper-Pfad ist seit R5 nicht mehr kanonisch |
| §6 Trigger T-10 | Reboot / Auto-Reboot | zusätzlich: K9-Tages-Differenz > 0 = Auto-Restart-Count | K9 ist jetzt das Maß für Auto-Restarts, nicht die binäre Beobachtung „Reboot hat stattgefunden" |
| §6 Trigger T-13 (NEU) | nicht vorhanden | Auto-Restart-Schleife (K9 > 10 oder `Start request repeated too quickly`) | K9-Schwelle 10; Flap-Schutz sollte das verhindern, aber Restarts nach kurzer Laufzeit (z. B. Credential-Preflight-Bug) können ihn umgehen |
| §6 Trigger T-14 (NEU) | nicht vorhanden | K8 Liveness-FAIL | F8-Fix: 0 Scheduler-Zyklen an einem Handelstag = strukturell FAIL (unterscheidet „läuft ruhig" von „läuft nicht") |
| §7 Watch-Items W6/W7/W8 | W6 = min_evidence | **W6 neu**: ls-Bars auf `:00.000Z` (Drift #13) · **W7 neu**: Log-Größe < 200 MB/Tag (Drift #12) · altes W6 → W8 | Drifts #12 + #13 sind im Code gefixt (`9ab50e8` + `d40f072`); v4 macht sie als Watch beobachtbar |
| §9 Was-nicht | „Keine Prozess-Supervision. Auto-Restart nach Reboot, systemd-Unit, Keyring-Auto-Unlock sind **bewusst out-of-scope**" | „Auto-Restart nach Reboot ist jetzt **in-scope** (Phase-16-R5 systemd-Autostart); aber **nicht** Auto-Restart nach Operator-Befehl (= FAIL Kriterium 1). Die Desktop-Session manuell eingeloggt zu lassen ist die Vorregistrierungs-Disziplin (Keyring-Bedarf)" | Phase-16-R5 hat den Status gewechselt: Autostart ist jetzt in-scope, die Disziplin „eingeloggt lassen" bleibt aus Keyring-Gründen |
| §10 Cross-Refs | ohne Sys-Standartanbieter | + [`./systemd/`](./systemd/) + [`../scripts/install_units.sh`](../scripts/install_units.sh) + [`./PHASE16_R_EXEC_PLAN.md`](./PHASE16_R_EXEC_PLAN.md) | R5-Quellen + Plan-Quelle jetzt explizit verlinkt |
| §11 Diff-Tabelle | v1→v2-Diff | v3→v4-Diff (Tabelle hier) + v1→v2/v2→v3-Verweis in der Einleitung | kumulative Drift-Verfolgung; v3 bleibt byte-identisch im Repo für Audit-Trail |