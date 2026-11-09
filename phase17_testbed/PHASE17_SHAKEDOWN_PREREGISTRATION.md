---
status: locked (Nikinger-Freigabe T23 am 2026-11-04; committet vor dem Fenster, danach nicht geändert — nur der Aktiv-Block wird am E-3-Tag eingetragen)
purpose: Vorregistrierung des 2-Tage-Prüfstand-Fensters nach dem E-3-Deploy — prüft, ob die Phase-17-Fixes live tragen (K1/K2/K5/K6/K7/K8/K9/K10/K11; K3/K4 nur berichtet)
read-when: E-3 (Deploy) und E-4 (Shakedown) — die Kriterien werden danach NICHT editiert, nur der Aktiv-Block wird am Start-Tag eingetragen; E-5 (Auswertung)
detail: L3
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase17_testbed_plan.md                       # 📕 Plan (§6 E-2, §19 = Entwurf dieser Datei, §7 AK19/AK20)
  - ../phase16_activation/scripts/autonomy_report.py              # 🔧 Report: v5-Evaluatoren + CLI-Flags
  - ../phase16_activation/PHASE16_AUTONOMY_PREREGISTRATION_v4.md   # 📕 Format-Vorbild (Aktiv-Block am Restart-Tag)
updated: 2026-11-04 (Exec-Session #16 — Entwurf aus Plan §19 E-2b; alle Anker am 2026-11-04 gegen den Code re-verifiziert, null Drift; **Nikinger-Freigabe (T23)** am 2026-11-04 ⇒ `status: locked`; **Token-Ausnahme auf die ganze MiniMax-Familie erweitert** — Plan-Änderung, siehe Notiz unten)
---
# PHASE17 SHAKEDOWN-PREREGISTRATION (S1) — 2-Tage-Prüfstand-Fenster

> **Disziplin (T23, wie Prereg v3):** dieses Dokument wird **vor** dem Fenster committet und
> danach **nicht** geändert. Korrekturen sind nur als **neue**, datierte, supersedende
> Vorregistrierung (`-S2`) mit Begründung möglich — niemals als Edit an dieser Datei. Das gilt
> für jeden Wert in *Vorregistrierte Werte* und *Kriterien*. Der **Aktiv-Block** ganz unten ist
> die einzige Ausnahme: er wird vom Operator **am E-3-Tag** eingetragen (das ist eine
> *Eintragung*, kein *Edit* — der Startzeitpunkt, nicht die Kriterien).
>
> **Warum:** ein nach dem Lauf geschriebenes Kriterium beweist nichts (Phase 16 P11; M1
> Vorregistrierungs-Disziplin). Alle Messquellen sind **append-only** (`run_*.log`,
> `research_health.jsonl`, `llm_usage.json`, `trade_outcomes`, `bars`, Journal-Export).

## BLUF

- **Fenster:** Tag 1 = der erste volle Handelstag **nach** dem E-3-Start, Tag 2 = der nächste
  Handelstag. Der Start-Zeitstempel ist die `starting scheduler daemon`-Zeile aus E-3
  (im Aktiv-Block eingetragen). Die konkreten Daten **D1/D2** stehen erst nach E-3 fest.
- **Zweck:** **kein** weiterer Autonomie-Test, sondern ein **2-Tage-Prüfstand-Fenster**: es
  prüft, ob die Phase-17-Fixes **live tragen** — B-1…B-10 (Mess- und Geldpfad), C-1…C-8 (LLM
  pro Rolle austauschbar, Flip 1 `research_m3`), D-1 (Token-Budget-Ausnahme) und E-1
  (Report v5) — **inklusive** der drei neuen Kriterien K9/K10/K11, die es vorher gar nicht gab.
- **PASS = alle berichtenden Kriterien PASS** (K1, K2, K5, K6, K7, K8, K9, K10, K11).
  **K3/K4 werden nur berichtet** (Rohzahl) — sie sind 10-Tage-Kriterien und werden hier
  **nicht** bewertet.
- **Profit ist kein Kriterium** (Phase-16-v3-Disziplin: „ehrliche Ausschlüsse"). Ebenso wenig
  Strategie-Qualität, Code-Qualität oder WebUI-Aliveness (die WebUI wird nur *gesichtet*).
- **Code-Stand:** HEAD beim E-3-Start — im Aktiv-Block eingetragen. Der Scheduler steht seit
  2026-10-25 im **HOLD** (systemd `disabled` + Marker `data/state/SCHEDULER_HELD`); **E-3**
  löst ihn. Bis dahin läuft der Bot nicht — die Daten unter dem Fenster sind also **keine**
  Phase-17-Live-Belege, sie sind es erst ab E-3.
- **Stand des Vorregistrierungs-Commits:** siehe *Vorregistriert* im Aktiv-Block.

## Vorregistrierte Werte (gepinnt)

Alle Werte **am 2026-11-04 gegen den Code geprüft** (nicht aus dem Plan abgeschrieben) — der
Code ist die Quelle der Wahrheit.

| Wert | Wert | Beleg (live geprüft 2026-11-04) |
|---|---|---|
| `account` | `demo` | `phase8_scheduler/scheduler/run.py:156` — **hart** gesetzt (`account="demo"`), nicht per Flag; die Wiring lehnt alles andere ab |
| `max_trades` | `5` | `run.py:72-74` (`--max-trades`, `default=5`); die Unit übergibt **keine** Flags (`phase16_activation/systemd/tradingbot-scheduler.service:25` = `python -m scheduler.run`) |
| `daily_loss_cap` | `1800.0` | `run.py:47-49` (`--daily-loss-cap`, `default=1800.0`) |
| `cycle` | `5min` | `run.py:78-80` (`--cycle-interval-min`, `default=5`) |
| `llm_profile` | `research_m3` | `phase8_scheduler/scheduler/config.py:149` — **Code-Default** (T17), seit C-8 (Flip 1): nur *Research* → MiniMax-M3, alle anderen Rollen Anthropic |
| `daily_token_budget` | `300 000` | `run.py:60-62` (`--daily-token-budget`, `default=300_000`) — gilt **nur** für Nicht-Ausnahme-Modelle |
| Token-Ausnahme | **alle MiniMax-Modelle** (C-7-Familie): `MiniMax-M3` (aktiv) + `MiniMax-M3.1-Flash` (Reserve) | `config.py:154` (`budget_exempt_models = ("MiniMax-M3", "MiniMax-M3.1-Flash")`) — D-1/T7: „measured, not capped" (Abo/M-Plan, Grenzkosten 0). 🟡 **Abweichung vom Plan-§19-Entwurf** (der nur `MiniMax-M3` pinnte) — Nikinger-Entscheidung 2026-11-04, siehe Notiz unten |

**Unverändert (aus Phase 16 übernommen, nicht verändert):** Demo-only · `RescueConfig.enable_gap_rescue=False`
· Promotion-Bridge AN · `max_parallel_positions` 1 · Cycle 5 min. **Keine Force-Trigger-Arbeit** (Hard Rule 5).

### 🟡 Änderung gegenüber dem Plan-Entwurf §19 (Nikinger, 2026-11-04)

Der Plan-§19-Entwurf pinnte die Token-Ausnahme auf **eine** Modell-ID (`MiniMax-M3`). Der
Nikinger hat am 2026-11-04 entschieden: **alle MiniMax-Modelle** ausnehmen, umgesetzt als
**Familien-Aufzählung** (`("MiniMax-M3", "MiniMax-M3.1-Flash")`) — das Matching im Code ist
überall ein Exakt-Match (`budget.py`, `webui/api.py`, `autonomy_report.py`,
`llm_profiles.py:377`), eine Prefix-Regel wäre ein Cross-Phase-Edit über P16 hinaus gewesen.
Ein **künftiges** MiniMax-Modell braucht einen neuen Eintrag in `config.py`; `check_llm_profile`
verweigert dann den Start und **nennt** die fehlende ID (kein stiller Drift). Der Code-Default
und die `--exempt-model`-Liste im Report-Befehl sind damit deckungsgleich.

**Voraussetzung für einen späteren Modellwechsel (M3 → M3.1-Flash, Entscheidung in E-5):**
`MiniMax-M3.1-Flash` hat **noch keine Preiszeile** in `phase4_research/research/models.py`
(nur `MiniMax-M3` hat eine) ⇒ `check_llm_profile` würde den Start verweigern
(„model has no price line"). Der Preis ist (0.0, 0.0) (Abo). **Bis dahin bleibt M3 aktiv.**

## Kriterien

Alle Regeln sind die **Code-Regeln** des Reports (`phase16_activation/scripts/autonomy_report.py`,
`--prereg v5`). Die Spalte *Quelle* nennt den Evaluator — die Quelle der Wahrheit ist der Code,
nicht diese Tabelle.

| K | Regel | Quelle im Code |
|---|---|---|
| K1 | Start-Zeilen je **Dienst** (scheduler, recorder, discovery, webui) ≤ **2** im Fenster — 1 regulärer Start + 1 erlaubtes Ereignis | `evaluate_k1` (`:770`), `RESTARTS_PASS_THRESHOLD_MAX = 2` (`:150`) |
| K2 | **v5-Regel:** je Handelstag (Mo–Fr) **≥ 1** Scheduler-Health-Event **und** **≥ 1** Recorder-Bar **und** **≥ 1** Discovery-Zyklus. Fenster ohne Handelstag ⇒ `NA` | `evaluate_k2_v5` (`:1175`), `count_discovery_cycles_per_day` (`:1147`) |
| K5 | v3-Regel: **alle** CRITICALs ≤ **5** je 24-h-Fenster nach jedem OPEN (Maximum über die Trades des Fensters). **0 Trades ⇒ PASS (vakuös)** — die Liveness tragen K2-v5 und K8 | `evaluate_k5` (`:947`), `CRITICAL_24H_PASS_THRESHOLD = 5` (`:149`) |
| K6 | **v5-Regel:** das Budget der **Nicht-Ausnahme**-Modelle wird **nie** vor **17:30** Berlin erschöpft (Cap 300 000). Ausnahme-Modelle werden gemessen, aber nicht gezählt | `evaluate_k6_v5` (`:1256`), `DEFAULT_DAILY_TOKEN_BUDGET = 300_000` (`:142`), `DEFAULT_WINDOW_CLOSE_HHMM = (17, 30)` (`:144`) |
| K7 | **v5-Regel:** Caps unverändert (`max_trades=5`, `daily_loss_cap=1800.0`) **und** jede CLOSED autonome Trade ist eine Demo-Trade **und** **jede** Start-Zeile im Fenster trägt `llm_profile=research_m3`. **Ohne** Start-Zeile im Fenster ⇒ **FAIL** (fail-closed, nicht vakuum-PASS) | `evaluate_k7_v5` (`:1327`) |
| K8 | v3-Regel (Liveness): je Handelstag **≥ 1** Scheduler-Zyklus **und** **≥ 1** Bar **und** **≥ 1** Heartbeat | `evaluate_k8` (`:1079`) |
| K9 | **v5-Regel:** Restart-Jobs je **Berlin-Tag** ≤ **10** (Journal-Export). Ohne Journal-Datei ⇒ `NA`; Zeilen ohne parsbaren Zeitstempel ⇒ **FAIL** (fail-closed) | `evaluate_k9` (`:1424`), `RESTART_JOBS_PER_DAY_MAX = 10` (`:152`) |
| K10 | **v5-Regel:** 0 CRITICAL `instinct.bridge` **und** 0 `extractor returned ok=False` im Fenster **und** jede im Fenster angelegte `instincts`-Zeile trägt `evidence_trade_ids_json`. 0 CLOSE im Fenster ⇒ `NA` | `evaluate_k10` (`:1497`) |
| K11 | **v5-Regel:** je Handelstag **≥ 1** Divergenz-Event (`divergence_ok` oder `quote_divergence`). Fenster ohne Handelstag ⇒ `NA` | `evaluate_k11` (`:1599`) |

**Nur berichtet (kein PASS/FAIL):** **K3** (≥ 5 CLOSED-Trades — 10-Tage-Kriterium) · **K4**
(Heartbeat-Tage — 10-Tage-Kriterium).

**Hinweis zu K10:** die 29 Alt-Instincts (T12) werden in E-3 mit dem Präfix `[legacy-p16] `
gekennzeichnet. K10 zählt nur Zeilen, die **im Fenster angelegt** wurden — der Altbestand ist
davon nicht betroffen.

## Erlaubte Operator-Ereignisse (gezählt, nie still)

- **(a) Re-Adoption-Probe — einmal, nur wenn beim Start eine Position offen ist:**
  `systemctl --user restart tradingbot-scheduler.service`.
  **Erwartet:** ≤ 2 Zyklen später `resume: re-adopting open position …` im Scheduler-Log und
  danach ein regulärer Close mit geschlossener `trade_outcomes`-Zeile (B-5/T8: die Re-Adoption
  ist genau das „+1" in K1).
- **(b) Tagesexport Journal (E-4)** — der Export selbst ist **kein** Ereignis.
- **Ein VM-Host-Reboot = K1 FAIL** mit der Ursache „VM-Host" (T10: Reboots sind
  Operator-/VM-Host-Ereignisse). Kein Neustart aus anderen Gründen im Fenster.
- **Alles andere ist ein Befund**, kein erlaubtes Ereignis: Hotfix-Commits, Konfig-Änderungen,
  manuelles Schließen/Öffnen von Positionen, Änderungen an Caps oder Profil.

## FAIL-Regel

Befund → Fix-Step **innerhalb Phase 17** → **neue** Shakedown-Vorregistrierung `-S2` (mit
Begründung) → neuer Lauf. **Kein** Kriterium wird gelockert (T3/T23). Ein FAIL im Fenster wird
**nicht** durch einen Edit dieser Datei geheilt — die Kriterien bleiben, bis eine neue
Vorregistrierung sie ersetzt.

## §F2 Flip-2-Tag (bedingt — nur bei Nikinger-Go in E-5)

- **1 Handelstag** mit `llm_profile=all_m3` (alle Rollen auf MiniMax-M3).
- **Dieselben Kriterien**, K7 gegen `all_m3` (der Profil-Pin wird umgestellt).
- **Abbruch + Revert** nach C-8 (eine Zeile zurück auf `research_m3`).
- **Start** = die erste Start-Zeile **nach** dem Flip-2-Commit.
- Dieser Abschnitt wird **jetzt mit vorregistriert**, sonst wäre der Flip-2-Tag ein Lauf ohne
  vorab festgelegte Kriterien (T5/T23). Er ist **kein** Teil des S1-Fensters.

## Report-Befehl (Operator, nach Tag 2)

**Schritt 1 — Journal-Export (E-4), einmal nach Tag 2:**

```bash
cd /home/trading-bot/trading-bot
journalctl --user -u tradingbot-scheduler.service -u tradingbot-recorder.service \
  -u tradingbot-discovery.service -u tradingbot-webui.service \
  --since "<D1> 00:00" --until "<D2+1> 00:00" -o short-iso --no-pager \
  > data/reports/journal_<D1>_to_<D2>.txt
```

**Schritt 2 — Report:**

```bash
phase1_broker_wrapper/.venv/bin/python phase16_activation/scripts/autonomy_report.py \
  --prereg v5 --from <D1> --to <D2> --summary \
  --journal-file data/reports/journal_<D1>_to_<D2>.txt \
  --expect-llm-profile research_m3 \
  --exempt-model MiniMax-M3 \
  --exempt-model MiniMax-M3.1-Flash \
  --reports-dir data/reports
```

`--exempt-model` ist **repeatable** und wird **mit** der ganzen MiniMax-Familie übergeben: der
Wert wird damit gepinnt und folgt **nicht** dem Code-Default (Plan §18 E-1d). `--expect-llm-profile
research_m3` ist der K7-Profil-Pin. **Exit-Code:** 0 = PASS · 1 = FAIL · 2 = PARTIAL/ERROR.

## Aktiv-Block (vom Operator am **E-3-Tag** einzutragen — *Eintragung*, kein Edit)

> Der Zeitpunkt des E-3-Starts, die beiden Handelstage (D1/D2), der HEAD-Commit und der
> Positionsstand beim Start stehen **erst nach dem Deploy** fest. Der Operator trägt sie hier
> ein, **bevor** der erste Shakedown-Zyklus läuft (Mechanik wie Prereg v3 — AK13).

| Feld | Wert | Quelle |
|---|---|---|
| **Start (E-3-Start-Zeitstempel)** | **2026-11-09 07:30:23,789 Europe/Berlin** — `starting scheduler daemon (account=demo, max_trades=5, daily_loss_cap=1800.0, cycle=5min, llm_profile=research_m3).` (automatischer Deploy, systemd-Timer 07:30) | `data/state/run_scheduler.log`, erste Zeile `starting scheduler daemon (account=…, max_trades=…, daily_loss_cap=…, cycle=…min, llm_profile=research_m3)` |
| **D1 (Tag 1)** | **Mo 2026-11-09** (Start vor 09:00 ⇒ erster voller Handelstag nach dem Start; Plan §22 / AK22 R2 a) | Berlin-Kalender, Mo–Fr |
| **D2 (Tag 2)** | **Di 2026-11-10** | Berlin-Kalender, Mo–Fr |
| **HEAD-Commit beim Start** | **`28ecf2b`** (= `origin/main`; Runbook erwartete `b372649` — Bot-Code seit `b372649` unverändert, Differenz nur Deploy-Skript/Units/Tests/Doku, siehe `docs/concepts/eurofleet_stand_2026-11-08.md` §6) | `git log -1` |
| **Offene Position bei Start** | **0** (`execution_state.json`: 0 OPEN/PENDING · `trade_outcomes`: 0 OPEN) | `data/state/execution_state.json` (OPEN/PENDING) + `trade_outcomes` (OPEN) |
| **Erlaubte Re-Adoption-Probe** | **nicht anwendbar** (keine offene Position beim Start) | (a) in *Erlaubte Operator-Ereignisse* |
| **Vorregistriert** | Exec-Session #16 (2026-11-04) — **Freigabe: Nikinger (T23), 2026-11-04**; Commit `32835dd` (Vorregistrierung), `fa02a6a` (Familien-Ausnahme) | `git log` |

> **Eintragung nachträglich** am 2026-11-09 ~17:55 (Review-Session #17, Claude Code, Nikinger-Auftrag) — nicht vor dem ersten Zyklus,
> weil `scripts/e3_deploy.sh` nach Schritt 6 in Schritt 7 abbrach (`set -e` + leerer `grep` in Z. 183, Bot lief weiter;
> `docs/concepts/eurofleet_stand_2026-11-08.md` §8). Alle Werte stammen aus append-only Quellen und sind vom Zeitpunkt der
> Eintragung unabhängig. **Day-0-Checks 8/8 grün:** #1 0 `preflight failed` · #2 Start-Zeile mit `llm_profile=research_m3` ·
> #3 erster `MiniMax-M3`-Record 2026-11-09T08:14:56Z · #4 40 `ig`-Bars, 0 mit `ts_utc > fetched_at` · #5 `discovery cycle`-Zeilen
> vorhanden · #6 14 NO_TRADE-`decision_context`-Zeilen seit Start, 0 ohne `abstain_record_id` · #7 neue Allowance
> 2026-11-09T12:08Z, 9 632 übrig, expiry 2026-11-16 · #8 alle vier Units `active`.

## Was diese Vorregistrierung **nicht** prüft

- **Kein** Profit, keine Win-Rate, kein Sharpe, kein P&L — der Bot hat in Phase 16 Σ −654,72 EUR
  bei 9 Gewinnern aus 17 Trades geliefert; das ist **kein** Befund dieses Fensters.
- **Keine** Aussage über Strategie- oder Code-Qualität (Phase-17-Material).
- **Keine** WebUI-Aliveness (nur Sichtung durch den Operator, wie in K2 vermerkt).
- **Keine** Änderung der Hard Rules (Demo-only, VETOs, Force-Trigger bei negativem Tages-PNL).
