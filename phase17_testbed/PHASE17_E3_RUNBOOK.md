---
status: locked (Nikinger-Freigabe T23-Nachtrag am 2026-11-05; locked-nach-Commit — Korrekturen
  nur als neue, datierte, supersedende Datei `PHASE17_E3_RUNBOOK_v2.md` mit Begründung,
  niemals als Edit hier)
purpose: Operator-Runbook für den Phase-17-Deploy (Plan §20 E-3a + §22 E-22c) — Hold-Freigabe,
  T14/T12-Datenreparatur, Unit-Installation, Scheduler-Start am Morgen von D1 (vor 09:00 Berlin)
  und die 8 Day-0-Checks. Alle Anker und Sollwerte am 2026-11-05 live gegen den Code und die
  Live-DBs gemessen (read-only) — null Drift.
read-when: am Deploy-Morgen (D1, 08:00–09:00 Berlin) — Schritt für Schritt; danach beim
  Auswerten des Shakedowns (E-4/E-5) für den Report-Befehl; Audit, was der Operator mechanisch
  tut vs. lassen muss
detail: L3
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase17_testbed_plan.md          # 📕 der Plan (§20 E-3a–f = Sequenz + Sollwerte + Fehlgriffe · §22 = Nachtrag D1/Zeitpunkt)
  - ./PHASE17_SHAKEDOWN_PREREGISTRATION.md            # 📕 die gelockte Vorregistrierung (Kriterien K1–K11, Aktiv-Block, Report-Befehl)
  - ../scripts/install_units.sh                       # 🔧 der Installer (--check · --release-hold)
  - ../scripts/e3_deploy.sh                           # 🔧 das Deploy-Skript (Schritte 1–7 + 2 Guardrails, §9)
  - ./systemd/                                       # 📂 Service- + Timer-Unit für den automatischen Deploy (§9)
  - ../phase16_activation/systemd/                    # 📂 die 4 User-Units (TimeoutStopSec=360)
  - ../phase16_activation/scripts/autonomy_report.py  # 🔧 der Report (v5-Evaluatoren)
updated: 2026-11-06 (Exec-Session #18, Fortsetzung — **der Deploy läuft jetzt automatisch**:
  D1 = **Mo 2026-11-09** (der Freitag 06.11. ist als D1 nicht mehr möglich — 10:07 ist nach 09:00
  ⇒ K7-v5 FAIL by construction), Ablauf via `scripts/e3_deploy.sh` + systemd-Timer
  (`phase17_testbed/systemd/tradingbot-e3-deploy.{service,timer}`, `OnCalendar=2026-11-09 07:30:00
  Europe/Berlin`, `Persistent=true`) → **§9**; alle Datumsangaben auf D1/D2 = 09./10.11. umgestellt)
  | 2026-11-05 (Exec-Session #18 — E-3-Runbook geschrieben: alle §20/§22-Anker live
  nachgemessen; **2 Korrekturen** gegenüber dem Plan: (a) §3-Check #4 liefert **vor** dem DELETE
  2 637 (nicht 3 770 — das ist die DELETE-Zahl), (b) der K1-Log-Truncate aus dem Phase-16-Runbook
  v2 §2.4 ist **obsolet** (die Wrapper-Start-Zeilen tragen inzwischen einen Timestamp-Prefix und
  werden fenstergefiltert) — **nicht** truncaten)
---
# PHASE17_E3_RUNBOOK — Operator-Pfad für den Phase-17-Deploy (E-3)

> **Quelle der Wahrheit:** der Code, dann der Plan (§20 + §22), dann dieses Runbook.
> **Was dieses Runbook ist:** der mechanische Pfad für den Deploy-Morgen. Es ist **kein** neues
> Konzept — §2 ist Plan §20 E-3a Schritt 1–7 **verbatim**, §3 ist Plan §20 E-3c + §22 E-22e,
> ergänzt um die Kommandos, die dort nur beschrieben sind.
> **Was es nicht ist:** kein Eingriff in den Shakedown. Ab Schritt 6 gilt die FAIL-Regel der
> Vorregistrierung: **kein** Hotfix im Fenster, **kein** Lockern eines Kriteriums.

## §0 BLUF

| Feld | Wert |
|---|---|
| **D1 (Tag 1)** | **Mo 2026-11-09** — der Deploy-Tag. Der Scheduler startet **vor 09:00 Berlin** (Plan §22 E-22a: AK22 R2 (a)). |
| **D2 (Tag 2)** | **Di 2026-11-10** (der nächste Handelstag). Fenster = `[2026-11-09, 2026-11-10]`. |
| **Fenster-Ende** | 2026-11-10, 17:30 Berlin — **vor** der MiniMax-Abo-Frist 2026-11-15 (Plan §16, §22 E-22b). |
| **Dauer** | 07:30–09:00 (Deploy-Skript, 7 Schritte nach Plan §20 E-3a) + 8 Day-0-Checks bis ~13:00. |
| **Was entsteht** | Der Scheduler läuft zum ersten Mal seit dem HOLD (2026-10-25) — mit `llm_profile=research_m3` (C-8 Flip 1) und 3 770 gelöschten Alt-IG-Bars (T14). |
| **Das Risiko des Tages** | Der **IG-Allowance**-Status: die letzte Beobachtung trägt `expiry = 2026-10-26` (**9 Tage in der Vergangenheit**). Check #7 entscheidet, ob der Bot mit Allowance läuft. Ohne Allowance ⇒ kein Comparator ⇒ K11 nicht erfüllbar ⇒ **E-3-Befund** (Plan §20 E-3e), *kein* Shakedown-Befund. |
| **Das Risiko des Starts** | Die Start-Zeile steht **vor** dem Preflight (`run.py:203-219`): ein Preflight-Fehler ⇒ Zeile + Exit 2 ⇒ `Restart=on-failure` alle 30 s ⇒ nach 3 Versuchen `failed` ⇒ **K1/K9 FAIL**. Deshalb Check #1 **sofort** nach dem Start. |
| **Nicht tun** | Kein `truncate` der Wrapper-Logs (Phase-16-Runbook v2 §2.4 ist obsolet — §6). Kein Handeln, kein Force-Trigger, keine Cap-Änderung, kein Hotfix-Commit im Fenster. |

## §1 Vorbedingungen (bis 08:00 Berlin, D1) — 6 Checks

Alle Erwartungen sind **am 2026-11-05 live gemessen** (read-only, keine Änderung).

| # | Check | Kommando | Erwartung (gemessen 2026-11-05) |
|---|---|---|---|
| 1 | **HEAD == origin/main** | `git -C /home/trading-bot/trading-bot status -sb && git -C /home/trading-bot/trading-bot log --oneline -1` | `## main...origin/main` (kein `ahead`/`behind`), HEAD `b372649` |

> **Achtung bei `git add -A`:** `data/` ist **nicht** ignoriert — nur einzelne Runtime-Pfade sind es.
> Am 2026-11-05 untracked: `data/state/DISCOVERY_ARMED` und
> `data/trading_bot.sqlite.pre-apply-2026-09-03` (Altlasten) — **nicht** mit committen. Die beiden
> Backups aus §2-Schritt 3 sind durch `*.sqlite.bak-*` ignoriert ✓.
| 2 | **Hold aktiv + Units sauber** | `bash /home/trading-bot/trading-bot/scripts/install_units.sh --check; echo "exit=$?"` | `exit=0` · alle 4 Units `installed=current` · Scheduler `enabled=disabled expected=disabled` · `hold ACTIVE` |
| 3 | **Kein Scheduler-Prozess** | `ps aux \| grep "scheduler.run" \| grep -v grep` | **leer** |
| 4 | **Keyring vollständig** (nur Anwesenheit, keine Werte) | siehe Kommando unten | `trading-bot-minimax-bot/api_key` ✓ · `tradingbot/anthropic_api_key` ✓ · `tradingbot/ig_demo_api_key` ✓ · `ig_demo_account_id` ✓ · `ig_demo_username` ✓ · `ig_demo_password` ✓ |
| 5 | **LLM-Profil startklar** | siehe Kommando unten | `research_m3` → Rolle `research` = **MiniMax-M3** (openai_compat, `https://api.minimax.io/v1`, `max_completion_tokens`), alle anderen Rollen = Anthropic · `check_llm_profile` grün · Preiszeile `MiniMax-M3 = (0.0, 0.0)` |
| 6 | **Sollwerte der Daten-Schritte** | siehe Kommando unten | `ig`-Bars = **3 770** · `instincts` = **29** (29 ohne Evidenz, 0 mit Präfix) · `trade_outcomes` OPEN = **0** · Allowance: letzte Zeile 2026-10-19, 9 923 übrig, expiry 2026-10-26 (**vergangen**) |

**Kommando 4 (Keyring-Anwesenheit, gibt keine Werte aus):**

```bash
cd /home/trading-bot/trading-bot && phase1_broker_wrapper/.venv/bin/python - <<'PY'
import keyring
for svc, user in [("trading-bot-minimax-bot", "api_key"),
                   ("tradingbot", "anthropic_api_key"),
                   ("tradingbot", "ig_demo_api_key"),
                   ("tradingbot", "ig_demo_account_id"),
                   ("tradingbot", "ig_demo_username"),
                   ("tradingbot", "ig_demo_password")]:
    try:
        v = keyring.get_password(svc, user)
    except Exception:
        v = None
    print(f"{'OK  ' if v else 'FEHLT'} {svc}/{user}")
PY
```

**Kommando 5 (Profil-Check, offline, kein Netz):**

```bash
cd /home/trading-bot/trading-bot/phase8_scheduler && /home/trading-bot/trading-bot/phase1_broker_wrapper/.venv/bin/python - <<'PY'
import sys
sys.path[:0] = ["/home/trading-bot/trading-bot/phase8_scheduler",
                "/home/trading-bot/trading-bot/phase4_research",
                "/home/trading-bot/trading-bot/phase6_debate",
                "/home/trading-bot/trading-bot/phase7_reward"]
from scheduler.config import SchedulerConfig
from scheduler.llm_profiles import check_llm_profile, LLM_ROLES, PROVIDERS, role_spec
from research.models import ResearchConfig
from debate.models import DebateConfig
from reward.models import RewardConfig
c = SchedulerConfig(); r, d, w = ResearchConfig(), DebateConfig(), RewardConfig()
check_llm_profile(c.llm_profile, pricing=r.pricing_usd_per_mtok,
                  default_models={"research": r.model, "debate": d.model_judge,
                                  "paper_debate": d.model_judge, "lesson": w.lesson_model,
                                  "instinct": w.lesson_model, "reflect": w.lesson_model},
                  exempt_models=c.budget_exempt_models)
print("Profil:", c.llm_profile, "| Ausnahme:", c.budget_exempt_models)
for role in LLM_ROLES:
    s = role_spec(c.llm_profile, role)
    print(f"  {role:13s} -> {s.provider:10s} {s.model or '(Phase-Default)'}")
PY
```

**Kommando 6 (Sollwerte, read-only):**

```bash
cd /home/trading-bot/trading-bot
sqlite3 "file:data/bars.sqlite?mode=ro" "SELECT COUNT(*) FROM bars WHERE source='ig';"
sqlite3 "file:data/trading_bot.sqlite?mode=ro" \
  "SELECT COUNT(*) FROM instincts WHERE evidence_trade_ids_json IS NULL;
   SELECT COUNT(*) FROM instincts WHERE trigger LIKE '[legacy-p16]%';
   SELECT COUNT(*) FROM trade_outcomes WHERE status='OPEN';"
sqlite3 "file:data/bars.sqlite?mode=ro" \
  "SELECT observed_at, remaining, expiry FROM allowance_observations ORDER BY id DESC LIMIT 1;"
```

## §2 Ablauf 07:30–09:00 (Plan §20 E-3a Schritt 1–7, verbatim)

> **Reihenfolge ist Pflicht.** Der Recorder hält `bars.sqlite` → Schritt 2 **vor** Schritt 4,
> sonst `database is locked`. Die Backups (Schritt 3) liegen **vor** dem DELETE (Schritt 4).
> Schritt 1 (Hold-Freigabe) liegt **vor** Schritt 5 (Installer) — sonst bleibt der Scheduler
> `disabled` und startet nach dem Reboot nicht (Plan §20 E-3e, letzte Zeile).

```bash
cd /home/trading-bot/trading-bot

# 1) Hold freigeben — NUR der Marker verschwindet, es wird NICHTS installiert
bash scripts/install_units.sh --release-hold

# 2) Vier Dienste stoppen (der Recorder hält sonst die bars.sqlite → "database is locked")
systemctl --user stop tradingbot-scheduler.service tradingbot-recorder.service \
                      tradingbot-discovery.service tradingbot-webui.service
ps aux | grep -E "scheduler.run|data_foundation.run|source_registry.run|uvicorn" | grep -v grep   # muss leer sein

# 3) Backups
cp data/bars.sqlite        data/bars.sqlite.bak-$(date +%Y%m%d)-pre-p17-igts
cp data/trading_bot.sqlite data/trading_bot.sqlite.bak-$(date +%Y%m%d)-pre-p17-legacy

# 4) Daten reparieren (T14 + T12) — Sollwerte siehe §1-Check 6
sqlite3 data/bars.sqlite "DELETE FROM bars WHERE source='ig'; SELECT changes();"          # erwartet 3 770
sqlite3 data/trading_bot.sqlite "UPDATE instincts SET trigger = '[legacy-p16] ' || trigger WHERE evidence_trade_ids_json IS NULL AND trigger NOT LIKE '[legacy-p16]%'; SELECT changes();"   # erwartet 29

# 5) Units installieren + aktivieren (B-9: TimeoutStopSec=360) — der Start bleibt Operator-Schritt
bash scripts/install_units.sh && systemctl --user daemon-reload

# 6) Alle vier Dienste starten
systemctl --user start tradingbot-scheduler.service tradingbot-recorder.service \
                      tradingbot-discovery.service tradingbot-webui.service
sleep 30 && systemctl --user is-active tradingbot-scheduler.service tradingbot-recorder.service \
                      tradingbot-discovery.service tradingbot-webui.service

# 7) Startzeile
grep "starting scheduler daemon" data/state/run_scheduler.log | tail -1
```

**Erwartungen je Schritt (live gemessen 2026-11-05):**

| Schritt | Erwartung |
|---|---|
| 1 | `[install_units] hold: marker removed: …/data/state/SCHEDULER_HELD` · `hold: released — 'bash scripts/install_units.sh' enables all four units again` |
| 2 | Alle 4 Units `inactive`; `ps`-Gegenprobe **leer**. ⏱ Der Stop kann **bis zu 6 Minuten** dauern (`TimeoutStopSec=360`, B-9): der SIGTERM wird erst nach dem Zyklus-Sleep (≤ 300 s) gewürdigt — **normal, kein Fehler**. |
| 3 | Zwei neue Dateien (79 MB + 7,3 MB), keine Namenskollision (Suffix `20261106`). |
| 4 | `changes()` = **3 770** und **29**. Beide Befehle laufen im **Read-write-Modus** (Journal-Modus `delete` — live gemessen, keine `-wal`/`-journal`-Dateien offen; das Rollback-Journal wird nach dem Commit wieder entfernt). Die `changes()`-Zahl **muss** **3 770** bzw. **29** sein — eine andere Zahl ⇒ **Abbruch**, nicht weiter deployen. |
| 5 | `installed:`/`up-to-date:` je Unit, danach `enabled: tradingbot-scheduler.service tradingbot-recorder.service tradingbot-discovery.service tradingbot-webui.service`. **Wichtig:** der Scheduler ist jetzt **enabled** (Autostart nach Reboot — das ist die E-3-Freigabe des HOLDs). |
| 6 | 4× `active`. ⚠ `is-active` beweist nur, dass der **Prozess** läuft — die Start-Zeile steht **vor** dem Preflight (`run.py:203-219`): ein Preflight-Fehler ⇒ Zeile + Exit 2 ⇒ Restart-Schleife. **Check #1 entscheidet**, nicht #3. Der Discovery-Daemon schreibt **sofort** seine erste `discovery cycle`-Zeile (er ruft `run_once()` direkt beim Start). |
| 7 | `starting scheduler daemon (account=demo, max_trades=5, daily_loss_cap=1800.0, cycle=5min, llm_profile=research_m3).` — **mit** `llm_profile=research_m3`. Die alte Zeile (2026-10-17, ohne Profil) steht darunter; sie liegt **außerhalb** des Fensters. |

**Zeit-Tipp (Plan §22 E-22c):** Schritt 6+7 **vor 09:00** mit ≥ 15 min Puffer (Deploy-Start 07:30 ⇒ Startzeile ~07:45). Startet der
Scheduler erst nach 09:00, liegt die Start-Zeile **vor** dem Fenster ⇒ K7-v5 **FAIL by
construction** (kein `starting scheduler daemon` in `[D1, D2]`) ⇒ FAIL-Regel, neuer Lauf.

## §3 Day-0-Checks (8 Stück — Plan §20 E-3c + §22 E-22e)

> **Ein rotes Ergebnis ist ein Befund im Fenster** (kein Puffertag mehr, §22 E-22a): Wortlaut +
> Rohwert in den Phasenkopf, dann FAIL-Regel (`-S2` + neuer Lauf). **Kein** Hotfix im Fenster.

| Plan-# | Wann | Check | Kommando | Erwartung |
|---|---|---|---|---|
| **#1** | sofort nach dem Start | **Kein Preflight-Fehler** | `tail -n +$(grep -n "starting scheduler daemon" data/state/run_scheduler.log \| tail -1 \| cut -d: -f1) data/state/run_scheduler.log \| grep -c "preflight failed"` | **0**. Ein Treffer ⇒ der Daemon läuft **nicht** (Exit 2, `Restart=on-failure` alle 30 s, nach 3 Versuchen `failed`). |
| **#2** | sofort | **Start-Zeile mit Profil** | `grep "starting scheduler daemon" data/state/run_scheduler.log \| tail -1` | enthält `llm_profile=research_m3` (sonst ist C-8 Flip 1 nicht aktiv ⇒ K7 FAIL). |
| **#8** | sofort | **Alle 4 Units aktiv** (AK22 H4, neu in §22) | `systemctl --user is-active tradingbot-scheduler.service tradingbot-recorder.service tradingbot-discovery.service tradingbot-webui.service` | 4× `active`. ⚠ `is-active` beweist nur, dass der **Prozess** läuft — die Start-Zeile steht **vor** dem Preflight (`run.py:203-219`): ein Preflight-Fehler ⇒ Zeile + Exit 2 ⇒ Restart-Schleife. **#1 entscheidet**, nicht #8. |
| **#5** | sofort | **Discovery-Beleg** (B-10) | `grep -c "discovery cycle" data/state/run_discovery.log` | **≥ 1** (war **0** — der Daemon lief seit 2026-11-01 mit dem Pre-B-10-Code ⇒ der Neustart in Schritt 6 ist Pflicht, sonst K2 dauerhaft FAIL). |
| **#3** | ab 09:00 (1. WINDOW-Zyklus) | **Erster Research-Call auf MiniMax** | `python3 -c "import json;r=json.load(open('data/state/llm_usage.json'));print(r[-1]['ts'], r[-1]['model'])"` | `model` = **MiniMax-M3**. (Vorher: 5 559 Records, letzter vom 2026-10-19 mit `claude-sonnet-4-6` — der Flip war bis E-3 inert.) |
| **#6** | ab 09:00 | **Abstain-Naht geschlossen** (B-7) | `sqlite3 "file:data/trading_bot.sqlite?mode=ro" "SELECT COUNT(*) FROM decision_context WHERE created_utc >= '2026-11-09' AND abstain_record_id IS NULL;"` | **0**. (Historisch: 3 679 NULL-Zeilen, alle vor dem 2026-10-19.) |
| **#4** | ab 09:00 | **Neue IG-Bars mit korrektem Zeitstempel** (T14) | `sqlite3 "file:data/bars.sqlite?mode=ro" "SELECT COUNT(*) FROM bars WHERE source='ig' AND ts_utc > fetched_at;"` | **0**. ⚠ **Korrektur zum Plan** (§7): die Abfrage liefert **vor** dem DELETE **2 637** (nicht 3 770 — das ist die Zahl der gelöschten Zeilen). Der Null-Wert beweist, dass der DELETE gewirkt hat **und** dass neue IG-Bars echtes UTC tragen (B-1-Fix, `ig_adapter.py:909`: `snapshotTimeUTC` vor `snapshotTime`). |
| **#7** | ab 09:00 | **IG-Allowance erneuert** | `sqlite3 "file:data/bars.sqlite?mode=ro" "SELECT observed_at, remaining, expiry FROM allowance_observations ORDER BY id DESC LIMIT 3;"` | eine **neue** Zeile mit `remaining > 0`. ⚠ Vor dem Deploy: letzte Zeile 2026-10-19, 9 923 übrig, **expiry 2026-10-26 = vergangen**. Bleibt es bei der alten Zeile ⇒ **E-3-Befund**: der Bot darf nicht ohne Allowances laufen (Plan §20 E-3e). |

> Die **Nummern sind die Plan-Nummern** (Plan §20 E-3c + §22 E-22e) — die Reihenfolge hier ist nach
> **Verfügbarkeit** sortiert (Plan §22 E-22e), nicht nach Nummer.

**Ab 13:00 (kein Day-0-Check, Tag-1-Evidenz):** der erste echte Divergenz-Vergleich (K11).
Der Sampler läuft im Universe-Refresh-Slot (`universe_refresh_interval_min = 240`) **und** nur im
WINDOW und ≥ 40 min nach Öffnung ⇒ der erste Vergleich fällt frühestens auf den Refresh um 13:00.
K11 zählt **nur** `divergence_ok` / `quote_divergence` — die typisierten Warte-Events
(`no_comparator` mit reason `partial_yf_window`/`zero_open`/`no_complete_bar`) sind **kein**
K11-Beleg, sondern die ehrliche „noch nicht vergleichbar"-Meldung.

## §4 Aktiv-Block eintragen (Plan §22 E-22c, direkt nach Schritt 7)

Die Vorregistrierung (`PHASE17_SHAKEDOWN_PREREGISTRATION.md`, `status: locked`) bekommt **am
E-3-Tag** genau eine **Eintragung** (kein Edit der Kriterien): Start-Zeitstempel · D1 · D2 ·
HEAD-Commit · offene Position · Re-Adoption-Probe.

| Feld | einzutragen |
|---|---|
| Start (E-3-Start-Zeitstempel) | der Zeitstempel der **neuen** `starting scheduler daemon`-Zeile (Spalte „Zeitstempel der Start-Zeile", §2 Schritt 7) |
| D1 | `2026-11-09` (Mo) |
| D2 | `2026-11-10` (Di) |
| HEAD-Commit beim Start | `git rev-parse --short HEAD` (erwartet `b372649`) |
| Offene Position bei Start | `0` — gemessen: `trade_outcomes` OPEN = 0, `execution_state.json` = 38 Records, alle CLOSED ⇒ die Re-Adoption-Probe (Prereg „Erlaubte Ereignisse" (a)) ist **nicht anwendbar** |
| Erlaubte Re-Adoption-Probe | „nicht anwendbar" |

## §5 Danach (E-4 → E-5) — bis der Report läuft

- **D1 (Mo 09.11.) und D2 (Di 10.11.)**: der Bot läuft, **kein Eingriff** außer den erlaubten
  Ereignissen (Prereg: Journal-Export, einmalige Re-Adoption-Probe — nicht anwendbar, VM-Host-Reboot
  = K1 FAIL mit Ursache „VM-Host").
- **Nach Tag 2** — Journal-Export (E-4), einmal:

```bash
cd /home/trading-bot/trading-bot
journalctl --user -u tradingbot-scheduler.service -u tradingbot-recorder.service \
  -u tradingbot-discovery.service -u tradingbot-webui.service \
  --since "2026-11-09 00:00" --until "2026-11-11 00:00" -o short-iso --no-pager \
  > data/reports/journal_2026-11-09_to_2026-11-10.txt
```

- **Dann** der Report, **wörtlich** aus der Vorregistrierung:

```bash
phase1_broker_wrapper/.venv/bin/python phase16_activation/scripts/autonomy_report.py \
  --prereg v5 --from 2026-11-09 --to 2026-11-10 --summary \
  --journal-file data/reports/journal_2026-11-09_to_2026-11-10.txt \
  --expect-llm-profile research_m3 \
  --exempt-model MiniMax-M3 \
  --exempt-model MiniMax-M3.1-Flash \
  --reports-dir data/reports
```

**Exit-Code:** 0 = PASS · 1 = FAIL · 2 = PARTIAL/ERROR. Der Payload trägt `"reported_only":
["3", "4"]` (K3/K4 werden berichtet, nicht bewertet — AK22 R1).

## §6 Fehlgriffe (Plan §20 E-3e + die zwei Korrekturen aus §7)

| Symptom | Ursache | Hand |
|---|---|---|
| `sqlite3: database is locked` beim DELETE | Recorder/Scheduler halten `bars.sqlite` | **erst** alle vier Dienste stoppen (Schritt 2), dann löschen; Backups **vor** dem DELETE |
| K2-v5 FAIL „discovery 0" | Discovery-Daemon lief mit dem **Pre-B-10-Code** (live: 0 Zeilen, Dienst gestartet 2026-11-01) | Neustart in Schritt 6 — der Beleg kommt erst mit dem neuen Code |
| **K11 FAIL „kein Divergenz-Event"** | Der Sampler lief noch nie vergleichbar (vorher 233/233 `divergence_no_comparator`) oder der erste Vergleich fällt erst auf 13:00 oder die yF-Archiv-Lag (p90 19,6 min) ist noch nicht abgefüllt | **erst die `reason` im Event lesen** (`no_complete_bar` / `partial_yf_window` / `zero_open`), dann die Pass-Zeiten (240 min + 40-min-Gate) |
| **IG-Allowance 0 / keine neue Zeile** | Die letzte Beobachtung trägt `expiry = 2026-10-26` — **vergangen**; die Erneuerung ist unbestätigt | Check #8. Ohne IG-Bars ⇒ kein Comparator ⇒ K11 nicht erfüllbar ⇒ **E-3-Befund** (kein Shakedown-Befund) — der Bot darf nicht ohne Allowances laufen |
| Der Scheduler startet nicht: `ValueError … not budget-exempt` / `… no price line` | `check_llm_profile` prüft **Preiszeile** + **Ausnahmenliste** | Modell-ID an **allen drei** Stellen prüfen: `llm_profiles._M3.model` · P4-Preiszeile (`research/models.py`) · `SchedulerConfig.budget_exempt_models` (`config.py:160`, jetzt die **Familie**) |
| Der Stopp hängt 6 Minuten | `TimeoutStopSec=360` (B-9) — der SIGTERM wird erst nach dem Zyklus-Sleep (≤ 300 s) gewürdigt | **normal**, kein Fehler |
| Der Report sagt K6 FAIL, der Bot blockte nicht | Report ohne `--prereg v5` (v4 zählt alle Tokens) oder `--exempt-model` vergessen | Der Befehl in §5 übergibt **beide** MiniMax-IDs (`--exempt-model` ist repeatable) |
| `install_units.sh --check` exit 1 nach dem Deploy | Erwartung ist nach dem Hold-Release **`enabled`** für alle vier Units | Der Marker muss **vor** dem Install weg (Schritt 1 vor Schritt 5) |
| **K1 FAIL „too many starts"** (≥ 3 je Dienst) | Der Service ist mehrfach gestartet (Restart-Schleife) oder die VM ist gebootet | Nicht durch Log-Edit heilen — der Befund zählt. Nur der **eine** reguläre Start (Schritt 6) darf im Fenster stehen. |
| ⚠ **„K1-Log-Truncate" aus dem Phase-16-Runbook v2 §2.4** | **obsolet** — die Wrapper-Start-Zeilen tragen inzwischen einen Timestamp-Prefix (`2026-11-01 00:21:58 [run_recorder] starting recorder …`) und werden vom Report **fenstergefiltert** (live geprüft: 2 Starts am 2026-11-01, 0 im Fenster 11-06…11-09) | **NICHT truncaten.** Ein Truncate würde Beweismaterial löschen, ohne den K1-Zähler zu verbessern. |

## §7 Was dieses Runbook gegen den Plan korrigiert (beide am 2026-11-05 live gemessen)

| # | Fundstelle | Plan-Angabe | Gemessen | Konsequenz |
|---|---|---|---|---|
| 1 | §20 E-3c, Check #4 | „vor dem Löschen liefert er exakt **3 770**" | die Abfrage `ts_utc > fetched_at` liefert **2 637** (3 770 ist die Zahl der `source='ig'`-Zeilen = die DELETE-Zahl) | Der **Sollwert des Checks bleibt 0** (nach dem DELETE). Nur die Beweis-Zahl im Plan war falsch — der Check selbst ist unverändert gültig. Alle 3 770 Zeilen tragen den +2-h-Versatz (B-1/T14) ⇒ der DELETE ist vollständig. |
| 2 | Phase-16-Runbook v2 §2.4 | „K1-Log-Truncate der 3 untimestamped Wrapper-Logs" | die Wrapper-Logs sind **timestamped** ⇒ der Report filtert sie fenstergenau | **kein** Truncate. Sonst Beweisverlust ohne Nutzen. |

Beide Korrekturen sind **Dokumentation**, kein Code — die Deploy-Sequenz und die Kriterien bleiben
unverändert.

## §8 Was dieses Runbook **nicht** macht

- Kein Profit-, P&L- oder Strategie-Urteil (Phase-16-v3-Disziplin: „ehrliche Ausschlüsse").
- Keine Aussage über Code- oder Strategie-Qualität.
- Keine WebUI-Aliveness-Bewertung (die WebUI wird nur *gesichtet*).
- Keine Änderung der Hard Rules (Demo-only, VETOs, Force-Trigger bei negativem Tages-PNL).
- Kein Fix im Fenster: ein roter Day-0-Check ⇒ Befund dokumentieren ⇒ FAIL-Regel
  (`-S2` + neuer Lauf), **nicht** patchen.

## §9 Der Deploy läuft **automatisch** — Mo 2026-11-09, 07:30 (systemd-Timer)

Der Nikinger hat den Deploy **nicht** selbst gestartet (Freitag 06.11. 10:07 — nach 09:00,
ein Start heute wäre K7 FAIL by construction). Stattdessen läuft er als **systemd-Timer**:

| Baustein | Ort | Aufgabe |
|---|---|---|
| Deploy-Skript | `scripts/e3_deploy.sh` | die Sequenz §2 Schritt 1–7 **verbatim** + 2 Guardrails (09:00-Guard, `changes()`-Guard) + die 4 sofortigen Day-0-Checks |
| Service-Unit | `phase17_testbed/systemd/tradingbot-e3-deploy.service` | `Type=oneshot`, führt das Skript aus, Log nach Journal |
| Timer-Unit | `phase17_testbed/systemd/tradingbot-e3-deploy.timer` | `OnCalendar=2026-11-09 07:30:00 Europe/Berlin`, `Persistent=true` (ein Reboot vor 07:30 verschiebt den Deploy **nicht**, er wird nachgeholt) |
| Test | `tests/test_e3_deploy.py` | 6 Tests (root): Schritt-Reihenfolge · dry-run ändert nichts · 09:00-Guard bricht **vor** dem Start ab · `changes()`-Mismatch bricht **vor** Schritt 5 ab · Plan-Werte im Skript gepinnt |

**Status (2026-11-06):** Timer **installiert und aktiviert** —
`systemctl --user list-timers` zeigt `Mon 2026-11-09 07:30:00 CET → tradingbot-e3-deploy.service`.
Der Pfad ist am 2026-11-06 mit einem **Self-Test** (derselbe Service, aber `--dry-run`) end-to-end
geprüft: DBUS-Zugriff, `sqlite3`, Keyring-Anwesenheit und `git` funktionieren **innerhalb** eines
User-Service ✓.

**Die zwei Guardrails (der Grund für das Skript):**

1. **09:00-Guard** — ist die Uhrzeit beim Start später als 08:55, startet das Skript den
   Scheduler **nicht** und bricht ab. Grund: die Start-Zeile muss im Fenster `[D1, D2]` liegen,
   und D1 muss ein *voller* Handelstag **nach** dem Start sein (Prereg BLUF) ⇒ ein Start nach
   09:00 würde das Fenster verbrennen (K7-v5 FAIL by construction).
2. **`changes()`-Guard** — die Reparatur muss **3 770** ig-Zeilen und **29** Instincts treffen.
   Eine andere Zahl (zweiter Lauf, geänderte Live-DB) ⇒ Abbruch **vor** Schritt 5.

**Logs:**
- Journal: `journalctl --user -u tradingbot-e3-deploy.service`
- Datei: `data/state/e3_deploy.log` (append-only, gitignoriert)

**Falls der Timer nicht feuert** (z. B. Rechner war aus, aber `Persistent=true` fängt das ab):

```bash
cd /home/trading-bot/trading-bot
systemctl --user start tradingbot-e3-deploy.service      # manuell jetzt
# oder: das Skript direkt (ohne Timer)
bash scripts/e3_deploy.sh
```

**Timer abschalten** (wenn der Deploy doch nicht laufen soll):

```bash
systemctl --user disable --now tradingbot-e3-deploy.timer
```

**Nur ansehen, ohne zu deployen:**

```bash
bash scripts/e3_deploy.sh --dry-run      # druckt jeden Schritt, ändert NICHTS
```
