---
status: draft (Review-Session #22, 2026-11-14) — wird nach dem G1-Smoke-PASS und der Nikinger-Freigabe (T23) auf `locked` gesetzt und vor dem Fenster committet; danach nur noch der Aktiv-Block (Eintragung am D1-Morgen)
purpose: Vorregistrierung des 2-Tage-Prüfstand-Fensters -S2 (Mo 2026-11-16 / Di 2026-11-17) — supersedes S1 nach dem S1-FAIL an K6; prüft die Konfiguration des 10-Tage-Laufs (`all_m3`) mit K1/K2/K5/K6/K7/K8/K9/K10/K11 + neu K12; K3/K4 + Judge-Quote + MiniMax-Last + Offline-Review nur berichtet
read-when: D1-Morgen (Start + Aktiv-Block), Mi 2026-11-18 (Export + Report + Auswertung) — die Kriterien werden danach NICHT editiert
detail: L3
up: ../CLAUDE.md
down:
  - ./PHASE17_SHAKEDOWN_PREREGISTRATION.md                       # 📕 S1 (superseded durch diese Datei, Begründung unten)
  - ../docs/concepts/phase17_testbed_plan.md                     # 📕 Plan §25 (S1 FAIL) · §26 F-26g (Inhalt dieser Datei) · §26.2 (Generalprobe + G1/G2)
  - ../phase16_activation/scripts/autonomy_report.py            # 🔧 Report: v5-Evaluatoren inkl. K12 + CLI-Flags
updated: 2026-11-14 (Review-Session #22 — Entwurf aus Plan §26 F-26g + den Generalprobe-Fixes G1/G2/G2b (§26.2); alle Anker am 2026-11-14 gegen den Code gemessen)
---
# PHASE17 SHAKEDOWN-PREREGISTRATION (-S2) — 2-Tage-Prüfstand-Fenster

> **Disziplin (T23, wie S1):** dieses Dokument wird **vor** dem Fenster committet und danach
> **nicht** geändert. Korrekturen nur als **neue**, datierte, supersedende Vorregistrierung
> (`-S3`) mit Begründung. Einzige Ausnahme: der **Aktiv-Block** ganz unten wird am D1-Morgen
> **eingetragen** (Startzeitpunkt, HEAD, Positionsstand — nicht die Kriterien).
>
> **Warum:** ein nach dem Lauf geschriebenes Kriterium beweist nichts. Alle Messquellen sind
> **append-only** (`run_*.log`, `research_health.jsonl`, `llm_usage.json`, `llm_io.jsonl`,
> `trade_outcomes`, `bars`, Journal-Export).

## Supersedes S1 — Begründung

- **S1 (Mo 2026-11-09 / Di 2026-11-10) = FAIL an K6** (Plan §25): unter Flip 1 (`research_m3`) lief
  die Debatte weiter auf Anthropic; D2 erschöpfte das 300-k-Cap um 17:19:13 (302 186 Tokens).
  Alle anderen bewertenden Kriterien PASS.
- **Fix (Nikinger 2026-11-11, Plan §26):** Flip 2 `llm_profile = "all_m3"` (alle Rollen MiniMax-M3,
  `54a45d9`) + Eingabe-Rekorder `data/state/llm_io.jsonl` (`7f8bd83`) + Kriterium **K12
  „LLM-Verfügbarkeit"** im Report (`6e8ec57`).
- **Generalprobe Fr 2026-11-13** (unregistriert, `all_m3`, Plan §26.2): K12 trocken PASS, aber
  **G1** — die Instinct-Extraktion lief auf M3 in 4 von 5 Calls in `finish_reason=length` (K10 wäre
  an jedem CLOSE-Tag FAIL) — und **G2** — 2 von 24 Debatten rissen das 120-s-Wanduhr-Cap.
  **Fixes (Nikinger 2026-11-14):** G1 = Instinct-Rolle unter `all_m3` 32 768 Tokens / 480 s ·
  G2 = Debatten-Wanduhr 240 s + G2b = Debatten-Output-Cap 24 000 für Profile, die die Debatte
  verlagern. **G1-Smoke PASS** (2026-11-14 12:29, Bot-Verdrahtung): 5 Instincts, `finish_reason=stop`,
  7 798 Output-Tokens, 49,2 s — dieselbe Eingabe, die am Fr bei 8 192 abgeschnitten wurde. Kein Kriterium geändert
  (F-26e: „Befunde der Generalprobe dürfen nur Code-Fixes auslösen").

## BLUF

- **Fenster:** **D1 = Mo 2026-11-16**, **D2 = Di 2026-11-17**. Scheduler-Start am D1-Morgen
  **vor 09:00 Berlin** (07:30–08:55): die `starting scheduler daemon`-Zeile liegt damit **im**
  Fenster (K7-v5) und K1 zählt genau den einen regulären Start.
- **Zweck:** prüfen, ob die Konfiguration des 10-Tage-Laufs (`all_m3`) zwei Handelstage **ohne
  Eingriff** trägt — inklusive des neuen K12 (das unter `all_m3` leere K6 ersetzt).
- **PASS = alle bewertenden Kriterien PASS** (K1, K2, K5, K6, K7, K8, K9, K10, K11, K12).
  **K3/K4 nur berichtet** (10-Tage-Kriterien).
- **Profit ist kein Kriterium.** Ebenso wenig Strategie-, Code- oder Modellqualität (die
  Modellqualität wird im Offline-Review nur **berichtet**).
- **Code-Stand:** HEAD beim Start — im Aktiv-Block eingetragen. Der Scheduler steht seit
  Sa 2026-11-14 09:06 im **HOLD** (`data/state/SCHEDULER_HELD`, Unit `disabled`); der Start löst ihn.

## Vorregistrierte Werte (gepinnt)

Alle Werte **am 2026-11-14 gegen den Code geprüft** (nicht aus dem Plan abgeschrieben).

| Wert | Wert | Beleg (live geprüft 2026-11-14) |
|---|---|---|
| `account` | `demo` | `phase8_scheduler/scheduler/run.py:156` — hart gesetzt, kein Flag |
| `max_trades` | `5` | `run.py:72-74` (`default=5`); die Unit übergibt **keine** Flags (`phase16_activation/systemd/tradingbot-scheduler.service:25` = `python -m scheduler.run`) |
| `daily_loss_cap` | `1800.0` | `run.py:47-49` (`default=1800.0`) |
| `cycle` | `5min` | `run.py:78-80` (`default=5`) |
| `llm_profile` | **`all_m3`** | `phase8_scheduler/scheduler/config.py:155` — Code-Default seit F-3 (`54a45d9`): **alle sechs Rollen** (research · debate · lesson · instinct · reflect · paper_debate) → MiniMax-M3 |
| Rollen-Limits unter `all_m3` | research/debate/lesson/reflect/paper_debate: `max_tokens=8192`, Timeout 90 s · **instinct: `max_tokens=32768`, Timeout 480 s** (G1) | `phase8_scheduler/scheduler/llm_profiles.py:200` (`_M3`) · `:208` (`_M3_INSTINCT`) · `:213` (`all_m3`) |
| Debatten-Caps | **Wanduhr 240 s** (G2) · **Output kumuliert 24 000** (G2b) · Input kumuliert 120 000 · Calls 18 · Runden 5 | `phase8_scheduler/scripts/wiring.py:543-544` (`_debate_config`) · Phase-6-Defaults `phase6_debate/debate/models.py:139-144` |
| `daily_token_budget` | `300 000` | `run.py:60-62` (`default=300_000`) — bindet unter `all_m3` **kein** aktives Modell |
| Token-Ausnahme | `MiniMax-M3` + `MiniMax-M3.1-Flash` | `config.py:166` (`budget_exempt_models`) |
| Eingabe-Rekorder | an (Research- + Debatten-Client) → `data/state/llm_io.jsonl` | `wiring.py` `_record_llm_io` (F-2, `7f8bd83`) |

**Unverändert aus S1:** Demo-only · `RescueConfig.enable_gap_rescue=False` · Promotion-Bridge AN ·
`max_parallel_positions` 1 · keine Force-Trigger-Arbeit (Hard Rule 5).

## Kriterien

Alle Regeln sind die **Code-Regeln** des Reports (`phase16_activation/scripts/autonomy_report.py`,
`--prereg v5`). Quelle der Wahrheit ist der Code, nicht diese Tabelle.

| K | Regel | Quelle im Code |
|---|---|---|
| K1 | Start-Zeilen je Dienst (scheduler, recorder, discovery, webui) ≤ **2** im Fenster — 1 regulärer Start (Scheduler) + 1 erlaubtes Ereignis | `evaluate_k1` (`:819`), `RESTARTS_PASS_THRESHOLD_MAX = 2` (`:161`) |
| K2 | je Handelstag ≥ 1 Scheduler-Health-Event **und** ≥ 1 Recorder-Bar **und** ≥ 1 Discovery-Zyklus | `evaluate_k2_v5` (`:1224`), `count_discovery_cycles_per_day` (`:1196`) |
| K5 | **alle** CRITICALs ≤ **5** je 24-h-Fenster nach jedem OPEN (0 Trades ⇒ PASS, vakuös — Liveness tragen K2/K8) | `evaluate_k5` (`:996`), `CRITICAL_24H_PASS_THRESHOLD = 5` (`:160`) |
| K6 | Budget der **Nicht-Ausnahme**-Modelle nie vor 17:30 Berlin erschöpft (Cap 300 000). **Unter `all_m3` nicht verletzbar** — offen so geführt; das Verfügbarkeitssignal trägt K12 | `evaluate_k6_v5` (`:1305`), `DEFAULT_DAILY_TOKEN_BUDGET` (`:153`), `DEFAULT_WINDOW_CLOSE_HHMM` (`:155`) |
| K7 | Caps unverändert (`max_trades=5`, `daily_loss_cap=1800.0`) **und** jede CLOSED autonome Trade ist Demo **und** **jede** Start-Zeile im Fenster trägt **`llm_profile=all_m3`**. Ohne Start-Zeile im Fenster ⇒ **FAIL** | `evaluate_k7_v5` (`:1376`) |
| K8 | je Handelstag ≥ 1 Scheduler-Zyklus **und** ≥ 1 Bar **und** ≥ 1 Heartbeat | `evaluate_k8` (`:1128`) |
| K9 | Restart-Jobs je Berlin-Tag ≤ **10** (Journal-Export); ohne Journal-Datei ⇒ `NA`; Zeilen ohne Zeitstempel ⇒ FAIL | `evaluate_k9` (`:1473`), `RESTART_JOBS_PER_DAY_MAX = 10` (`:163`) |
| K10 | 0 CRITICAL `instinct.bridge` **und** 0 `extractor returned ok=False` **und** jede im Fenster angelegte `instincts`-Zeile trägt Evidenz; 0 CLOSE ⇒ `NA` | `evaluate_k10` (`:1546`) |
| K11 | je Handelstag ≥ 1 Divergenz-Event (`divergence_ok` / `quote_divergence`) | `evaluate_k11` (`:1648`) |
| **K12** *(neu)* | je Handelstag: (a) ≥ 1 Research-ok-Ereignis · (b) keine Serie ≥ **3** aufeinanderfolgender LLM-Ausfälle (Research `LLM_UNAVAILABLE` + Debatte `DebateLLMError`/`DebateBudgetExceeded`/`unexpected`, Log-Reihenfolge) · (c) LLM-Ausfälle ≤ **10 %** der LLM-Ereignisse · (d) mit `--expect-no-capped-calls`: **0** Nicht-Ausnahme-Calls im Fenster (jeder `claude-*`-Record = Rollen-Leck). `debate fail-closed (DebateError)` = Datenpfad: gezählt, kein Ausfall | `evaluate_k12` (`:1730`), `_k12_event_kind` (`:1707`), Schwellen `:266-267` |

**Nur berichtet (kein PASS/FAIL):**
- **K3** (CLOSED-Trades) · **K4** (Heartbeat-Tage) — 10-Tage-Kriterien.
- **Judge-Freigabequote je Tag** (Vergleich: S1 unter Sonnet 5/16 · 2/70 · 5/17; Generalprobe unter M3 5/22).
- **MiniMax-Calls und -Tokens je Tag** (aus K6 `exempt_calls_per_day` / `exempt_tokens_per_day`).
- **Abbrüche je Tag:** `DebateError` (Datenpfad) · `DebateBudgetExceeded` (Wanduhr/Token, in K12 `debate_failed`).
- **Instinct-Calls je Tag:** Anzahl, max. Output-Tokens (Abstand zum 32 768-Limit aus G1; Smoke-Referenz 7 798, Fr 8 026 / 4 × ≥ 8 192), Dauer. Ein `finish_reason=length` unter 32 768 wäre eine stille Kappung durch MiniMax.
- **Offline-Review** in Claude Code (Opus, Pro-Plan, manuell — **kein** API-Call des Bots): Stichprobe =
  alle Debatten mit `TRADE` + jede fünfte übrige in Dateireihenfolge aus `data/state/debate_log.json`,
  Eingaben aus `data/state/llm_io.jsonl`; berichtet werden Übereinstimmung Reviewer/Judge und Fälle
  „Daten falsch gelesen".

**Hinweis zu K10:** die 29 Alt-Instincts (`[legacy-p16] `) und die 5 Instincts der Generalprobe
liegen vor dem Fenster — K10 zählt nur Zeilen, die **im Fenster** angelegt wurden.

## Erlaubte Operator-Ereignisse (gezählt, nie still)

- **(a) Re-Adoption-Probe** — einmal, nur wenn beim Start eine Position offen ist:
  `systemctl --user restart tradingbot-scheduler.service`; erwartet ≤ 2 Zyklen später
  `resume: re-adopting open position …` und danach ein regulärer Close.
- **(b) Journal-Export** nach D2 — der Export selbst ist kein Ereignis.
- **Doku-Commits im Fenster sind erlaubt** (S1-Befund N2). **Code- und Konfig-Commits nicht.**
- **Ein VM-Reboot = K1 FAIL** (Ursache benannt). Kein Neustart einer `tradingbot-*`-Unit aus anderen Gründen.
- **Befund, kein erlaubtes Ereignis:** eine Ausführer-Sitzung auf dem MiniMax-Key im Fenster
  (Mo 07:30 bis Di 18:00) · Hotfix-Commits · Konfig-Änderungen · manuelles Schließen/Öffnen von
  Positionen · Änderungen an Caps oder Profil.

## FAIL-Regel

Unverändert: Befund → Fix-Step **innerhalb Phase 17** → neue Vorregistrierung `-S3` (mit
Begründung) → neuer Lauf. **Kein** Kriterium wird gelockert (T3/T23). Bei FAIL an **K12** oder
**K10** ist der kleinste Fix der Revert von F-3 (eine Zeile, `all_m3` → `research_m3`) — dann
gilt wieder das K6-Risiko aus S1.

**§F2 (Flip-2-Tag) entfällt** — in `-S2` aufgegangen.

## Report-Befehl (Operator, Mi 2026-11-18)

**Schritt 1 — Journal-Export:**

```bash
cd /home/trading-bot/trading-bot
journalctl --user -u tradingbot-scheduler.service -u tradingbot-recorder.service \
  -u tradingbot-discovery.service -u tradingbot-webui.service \
  --since "2026-11-16 00:00" --until "2026-11-18 00:00" -o short-iso --no-pager \
  > data/reports/journal_2026-11-16_to_2026-11-17.txt
```

**Schritt 2 — Report:**

```bash
phase1_broker_wrapper/.venv/bin/python phase16_activation/scripts/autonomy_report.py \
  --prereg v5 --from 2026-11-16 --to 2026-11-17 --summary \
  --journal-file data/reports/journal_2026-11-16_to_2026-11-17.txt \
  --expect-llm-profile all_m3 --expect-no-capped-calls \
  --exempt-model MiniMax-M3 \
  --exempt-model MiniMax-M3.1-Flash \
  --reports-dir data/reports
```

**Exit-Code:** 0 = PASS · 1 = FAIL · 2 = ERROR. Der Payload trägt `"reported_only": ["3", "4"]`.

## Start am D1-Morgen (Operator, Mo 2026-11-16, 07:30–08:55)

```bash
cd /home/trading-bot/trading-bot
bash scripts/install_units.sh --release-hold
bash scripts/install_units.sh
systemctl --user start tradingbot-scheduler.service
```

**Day-0-Checks (Plan F-26f, im Fenster):** Start-Zeile mit `llm_profile=all_m3` · 0 `preflight failed`
seit dem Start · erster Datensatz in `data/state/llm_io.jsonl` nach 09:00 · 0 `claude-*`-Records seit
dem Start in `data/state/llm_usage.json` · vier Units `active`.

## Aktiv-Block (vom Operator am D1-Morgen **vor 09:00** einzutragen — *Eintragung*, kein Edit)

| Feld | Wert | Quelle |
|---|---|---|
| **Start** | *(einzutragen)* | `data/state/run_scheduler.log`, Zeile `starting scheduler daemon (…, llm_profile=all_m3)` |
| **D1 / D2** | Mo 2026-11-16 / Di 2026-11-17 | Berlin-Kalender |
| **HEAD-Commit beim Start** | *(einzutragen)* | `git log -1` |
| **Offene Position bei Start** | *(einzutragen)* | `execution_state.json` + `trade_outcomes` (OPEN) |
| **Re-Adoption-Probe** | *(einzutragen: anwendbar ja/nein)* | (a) oben |
| **Vorregistriert** | Review-Session #22 (2026-11-14) — **Freigabe: Nikinger (T23), *(Datum)***; Commits: *(einzutragen)* | `git log` |

## Was diese Vorregistrierung **nicht** prüft

- **Kein** Profit, keine Win-Rate, kein P&L.
- **Keine** Bewertung der Modellqualität (nur berichtet: Judge-Quote, Offline-Review).
- **Keine** WebUI-Aliveness (nur Sichtung).
- **Keine** Änderung der Hard Rules (Demo-only, VETOs, Force-Trigger bei negativem Tages-PNL).
