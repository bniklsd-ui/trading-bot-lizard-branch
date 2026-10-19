---
status: snapshot
purpose: Execution-ready Plan für Phase 17 (Prüfstand — keine neuen Features; jeder vorhandene Arm liefert nachweisbar, jeder Mess-/Geldpfad-Defekt ist zu, das LLM ist austauschbar, Report + Vorregistrierung v5 bilden das Fundament für die ausgiebigen Tests), geschrieben 2026-10-17 in der Plan-Session gegen Code, Live-DB (mode=ro), Logs und Journal; direkt an Sonnet 5 übergebbar
read-when: vor jedem Phase-17-Schritt; danach nur noch als Snapshot beim Auditieren
detail: L3
up: ../../CLAUDE.md
down:
  - ../../phase17_testbed/CLAUDE.md                          # Phasenkopf — trägt den Plan-Session-Block; Step A-0 rotiert ihn
  - ../../phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md    # 📕 Vorgänger-Handover (§4 PASS-Blocker, §5 E1–E8 — hier entschieden)
  - ../../phase16_activation/PHASE16_LLM_SWITCH_PLAN.md      # 📕 ungebauter LLM-Plan (hier abgelöst, §1 T4/T16)
  - ../../phase16_activation/PHASE16_AUTONOMY_PREREGISTRATION_v3.md  # 📕 Kriterien K1–K9 (Basis für v5)
  - ../../phase16_activation/scripts/autonomy_report.py      # Report-Skript (Block E erweitert es in place)
updated: 2026-10-19 (§15 Nachtrag — Provider-Plastizität: 9 Provider-Einträge als Daten, 3 Quirks, T25–T30, zwei Live-Stufen; ändert C-1/C-3/C-4/C-6/C-7 in place) | 2026-10-18 (§14 Nachtrag — Executor GLM in OpenCode, Bot-Provider z.ai Pay-per-use) | 2026-10-17
---

# Phase 17 — Prüfstand: Execution-ready Plan (2026-10-17)

> ⚠ **Nachtrag 2026-10-18 (§14, Nikinger): §14 hat Vorrang.** Der Executor ist ein offener Test mit GLM in OpenCode und Review-Gate vor E-3. Bot-Provider ist die z.ai-API mit Pay-per-use statt MiniMax M3. §14 überschreibt T4–T7, T22 und alle MiniMax-Stellen in C/D/E — **zuerst §14 lesen.**

> ⚠ **Nachtrag 2026-10-19 (§15, Nikinger): Provider-Plastizität** ändert C-1/C-3/C-4/C-6/C-7 in place (Reihenfolge §14 → §15 → §6). Vor Block C **§15 lesen.**

> **Adressat:** die ausführende Session (**Sonnet 5 in Claude Code**, Nikinger-Auftrag 2026-10-17).
> Nichts hier muss neu hergeleitet werden. Jede Zahl in §2/§3 ist in der Plan-Session selbst gegen
> Code, Live-DB (`mode=ro`), Logs oder `journalctl` gemessen — mit Datum und Zeilennummer.
> Was **nicht** prüfbar war, steht vollständig in **§9**; was dort nicht steht, gilt als geprüft.
> Zeilennummern = Stand HEAD `e19c178` (2026-10-17). **Der Verbatim-String ist der Anker, die Zahl
> die Abkürzung** — Steps verschieben einander die Zeilen.

---

## §0 BLUF

**Mission in einem Satz:** Phase 17 macht den Bot zum Prüfstand — jeder vorhandene Arm liefert
nachweisbar, was er liefern soll, jeder bekannte Mess- und Geldpfad-Defekt ist zu, das LLM ist pro
Rolle austauschbar (Research zuerst auf MiniMax M3), und ein erweitertes Report-Skript plus
Vorregistrierung v5 bilden das Fundament für die anschließenden ausgiebigen Tests.

**Rahmen (Nikinger 2026-10-17):** *„keine besondere Feature-Session — bildet eher das Fundament für
ausgiebige Tests. LLM-Austausch wäre aber trotzdem sehr wichtig"* und *„kein zusätzlicher Umfang,
eher extrem tiefe Optimierung von dem, was schon da ist."* Phase 17 baut deshalb **nichts Neues**,
sondern repariert und härtet Vorhandenes.

**Warum jetzt:** Die Plan-Session hat zusätzlich zu den vier PASS-Blockern aus Phase 16 drei
**stille Totalausfälle** gemessen. Grüne Tests haben jeden davon verdeckt:

| Neu gemessen | Beleg (2026-10-17) |
|---|---|
| Alle IG-REST-Bars sind **+2 h in die Zukunft** gestempelt (Ortszeit als UTC) | 3 730 Zeilen; Bars, abgerufen 07:07:12Z, tragen `ts_utc` bis 09:05Z; Preis-Match IG „09:00Z" = LS 07:04Z exakt |
| Der Divergenz-Sampler hat **noch nie** verglichen | 233 von 233 Events `divergence_no_comparator` seit 08-25 |
| `decision_context.abstain_record_id` ist **immer leer** | 3 643 von 3 643 NO_TRADE-Zeilen NULL |

**Fünf Blöcke, in dieser Reihenfolge:**

| Block | Inhalt | Bot |
|---|---|---|
| **A** | Haushalt: Step-0-Ritual, Baseline Σ **1964**, Code↔.md-Sweep, Push | läuft |
| **B** | Mess- und Geldpfad-Defekte: IG-Zeitstempel, Sampler, Bridge, Abschneiden sichtbar, Monitor-Re-Adoption, Breaker-Blindfenster, Abstain-Naht, Paper-Logstufen, Stop-Timeout, Discovery-Beleg | **Scheduler gestoppt ab B-0** |
| **C** | LLM-Austausch: Rollen-Profile, OpenAI-Compat-Härtung, eine Bau-Funktion für alle 7 Clients, `LLM_UNAVAILABLE`, Key + Smoke → **Flip 1** (Research → M3) | gestoppt |
| **D** | Token-Budget: MiniMax-M3-Calls budgetfrei, Anthropic bleibt bei 300 k; messen, dann entscheiden | gestoppt |
| **E** | Test-Fundament: Report v5, Shakedown-Vorregistrierung, Deploy, **2-Tage-Shakedown**, Prereg v5, Closeout | **Restart in E-3** |

**Phase-Abnahme (Nikinger 2026-10-17, F2):** Prereg v5 ist committet **und** der Shakedown war
sauber (AK19 + AK20). Der vorregistrierte 10-Tage-Lauf ist selbst die ausgiebige Testreihe danach.

**Ehrliche Grenzen:** keine Strategie- oder Edge-Bewertung. Phase-16-Trades id 12–28: Σ −654,72 EUR,
9 Gewinner bei 17 Trades (Handover §2). Profit ist **kein** Kriterium. Ob M3 als Research-Modell
*gut* entscheidet, misst erst die Testreihe; Phase 17 stellt nur sicher, *dass* es messbar wird.

---

## §1 Gelockte Entscheidungen (Nikinger 2026-10-17, Runden 1+2 — je Zeile mit Begründung)

| ID | Entscheidung | Begründung (warum niemand sie gutgemeint aufmacht) |
|---|---|---|
| **T1** | Phase 17 „**Prüfstand**", Verzeichnis `phase17_testbed/`, Commit-Scope `phase17:` (E1 = a) | Nikinger F1. Die Phase-16-Subphasen F/R/LLM hätten den Schirm weiter verwässert (Handover E1); der Name beschreibt den Zweck: Fundament für Tests |
| **T2** | **Kein zusätzlicher Umfang.** WebUI-Layout-Wunsch und alle „Weiteren Kandidaten" (Backoff-Anker `closed_at`, `close_ts`-Cold-Reconstruct, Smoke-Muster, `requires-python`) bleiben draußen | Nikinger F2: „extrem tiefe Optimierung von dem, was schon da ist". Jeder Step hier repariert einen gemessenen Defekt eines existierenden Arms |
| **T3** | Blöcke A → B → C → D → E. Abnahme = Prereg v5 committet + 2-Tage-Shakedown PASS | Nikinger F2 „passt so". Erst reparieren, dann messen — ein Lauf auf defekter Messung beweist nichts (drei Phase-16-Läufe scheiterten genau daran) |
| **T4** | LLM-Ziel = **MiniMax M3** über den **OpenAI-kompatiblen** Endpoint mit dem vorhandenen, getesteten `OpenAICompatLLMClient` | Nikinger F3. Der Client ist seit M1 Step 10 gebaut und smoke-verifiziert (gegen OpenRouter). Der Anthropic-kompatible `/anthropic`-Shim hat laut Memory sporadische Tool-Fehler, und `output_config.format` wäre dort ungeprüft |
| **T5** | **Flip 1** = nur Rolle `research` auf M3 (eigener Commit **nach** dem Demo-Smoke). **Flip 2** = alle Rollen (`all_m3`), gegated: nur mit Nikinger-Go nach dem Shakedown-Report; dann ein 1-Tage-Shakedown auf `all_m3` vor Prereg v5. Ohne Go pinnt Prereg v5 `research_m3`, und Flip 2 wandert in die Testreihe | Nikinger F4 „b) erst, dann später alle". Research ist der größte Token-Block (10-15: 86 Sonnet-Calls = 301 087 Tokens). Ein Profil ist **eine** Variable — Mischstände machen spätere Modellvergleiche unlesbar |
| **T6** | Bot-Key in **eigenem** Keyring-Namespace `trading-bot-minimax-bot`, Username `api_key`. Das Seed-Skript ist das um `--service/--username` erweiterte `scripts/store_minimax_key.py` (keine Skript-Kopie) | Nikinger F5. Der Dev-Harness-Key (`trading-bot-minimax`/`minimax_api_key`) bleibt unberührt (Isolationsmuster M1). Das Abo-Kontingent deckt API-Nutzung; 100–150 Calls/Tag sind laut Nikinger „quasi unsichtbar" |
| **T7** | **MiniMax-M3-Calls zählen nicht gegen das Tages-Token-Budget** (`budget_exempt_models`). Anthropic-Calls bleiben bei 300 000 gedeckelt. Die K6-Einheit für Prereg v5 entscheidet der Nikinger **nach** dem Shakedown (D-2) | Nikinger F6: „für alle MiniMax-M3-Calls unlimited, danach messen und Entscheidung". Der Token-Cap ist modellblind (`budget.py` `_TOKEN_FIELDS`), ein billigeres Modell senkt allein nichts an K6 (§3 D10) |
| **T8** | **Monitor-Re-Adoption:** Nach einem Restart übernimmt der Runner im WINDOW eine bei IG offene Position (Einstieg = `execution_state.recorded_at`, Währung = `default_currency`). Research pausiert bis zum Close. Sind `max_hold` oder `square_off` schon überschritten, folgt ein **sofortiger Close**. Nie in IDLE/PRE_OPEN/POST_WINDOW | Nikinger F7 „ja passt". Hard Rule 2: der Orphan AEX id 26 lief 6 Tage ohne Time-Stop. Ein Close bei geschlossenem Markt würde scheitern, deshalb nur WINDOW |
| **T9** | **Breaker Worst-Case:** `realized_pnl_today` = gebuchte P&L **plus** `−initial_risk` für jede heutige `status='OPEN'`-Zeile. Fehlt `initial_risk` bei einer OPEN-Zeile → die Closure wirft → `AutoConfirm` blockt (fail-closed) | Nikinger F8 „ja passt". Das Blindfenster dauert bis zum IG-Settlement (1 h 06 bis 1 h 54 gemessen). Dieselbe Annahme trägt Hard Rule 5 |
| **T10** | `TimeoutStopSec=360` in der Scheduler-Unit. Reboots sind **Operator-/VM-Host-Ereignisse** (Nikinger: „von mir, ausgelöst durch VM-Host") und zählen in Vorregistrierungen als solche | F9 + F12. Heute endet jeder Stopp nach 90 s in SIGKILL (09-23, 09-30, 10-11), weil der Zyklus-Schlaf 300 s dauert, also läuft kein `shutdown()`-Reconcile. Ein unterbrechbarer Schlaf wäre ein Runner-Umbau, die Unit-Zeile reicht |
| **T11** | E4 (a) **Quellen beheben, Kriterium nicht lockern** (Paper-Fehler externer Abhängigkeiten: CRITICAL → WARNING). E5 (a) Bridge bleibt an. E6 (a) **Gate P7/A6 gilt als erfüllt**, der Status-Text wird angepasst. E7 (a) **`LLM_UNAVAILABLE`** wird eine eigene Abstain-Klasse, laut ab 3 Ticks in Folge | Nikinger F10 „deine Empfehlung, solange das dann endlich funktioniert". K5 bleibt „alle CRITICALs" — wir senken das Rauschen an der Quelle |
| **T12** | Die 29 Alt-Instincts **bleiben stehen** und werden **gekennzeichnet**: Operator-SQL setzt das Präfix `[legacy-p16] ` vor `trigger` (E-3) | Nikinger F11. Keine Migration nötig, in jedem SELECT sichtbar, reversibel (`substr`). Funktional sind sie ohnehin inert: `proposed`, Evidence NULL, nie kompiliert |
| **T13** | Cross-Phase-Freigabe (Code): **P1, P4, P5, P8, P10, P12, P14, P15, P16**. **P2 nur in Tests** (echte `Database` im Bridge-Contract-Test). **Kein Code in P6, P7, P13** — die Debatte wechselt per Config-Override in der P8-Wiring | Nikinger F12 „alle freigegeben" + F13/F14 „ja". Jede Änderung außerhalb dieser Liste → stoppen und fragen |
| **T14** | IG-Zeitstempel: `_parse_bar` liest **`snapshotTimeUTC` zuerst** (P1, eine Zeile). Vorher ein Operator-Probe (1 Datenpunkt) als Beleg für das Feld. Fehlt es → Fallback B-1b: zonenrichtige Europe/Berlin→UTC-Umrechnung in `normalize_bar_ts` (P12). Danach **alle `source='ig'`-Zeilen löschen** (Backup, Recorder gestoppt) | Nikinger F13. DST-Wechsel am 2026-10-25 — eine feste −2-h-Verschiebung wäre ab dann falsch. Löschen statt Verschieben: kein PK-Kollisionsrisiko, yF + LS decken dieselben Minuten |
| **T15** | Divergenz-Sampler reparieren: Vergleich auf einem **abgeschlossenen** IG-5m-Bar, der ≥ 25 min alt ist, gegen yF-1m-Bars **desselben** 5-min-Fensters (≥ 4 von 5). Tagesthrottle nur **nach** einem echten Vergleich. Explizites `divergence_ok`-Event. Sampling nur im WINDOW und ab Öffnung + 40 min | Nikinger F14. yF-Archiv-Lag p50 17,6 / p90 19,6 / max 20,3 min (gemessen 10-16). Die alte Rechnung verglich zwei 5-min-Renditen mit zwei 1-min-Renditen — repariert man nur den Zeitstempel, würden **falsche** `mismatch`-Marken Epics endgültig aus `measurable_universe()` werfen |
| **T16** | Das LLM-Routing lebt in **P8**: neues Modul `scheduler/llm_profiles.py` plus **eine** Bau-Funktion `_build_llm` in `scripts/wiring.py`. Keine Factory in P4 | Die Composition Root ist P8. Alle 6 heutigen Client-Konstruktionen plus der neue Extractor-Client stehen dort (`wiring.py:313,344,390,470,527,685`). Die `scripts/wiring.py` von P4/P5/P6/P7 sind Operator-Skripte und bleiben Anthropic |
| **T17** | Profile sind **Code-Defaults** (`SchedulerConfig.llm_profile`), kein CLI-Flag. Rollback = Flip-Commit revertieren + Restart | systemd-`ExecStart` übergibt keine Flags (`tradingbot-scheduler.service:25`), nur ein Code-Default ist restart-fest (Memory „Flags prüfen, bevor ‚ist live'") |
| **T18** | `InstinctBridge.promote()` bleibt **nur beim Start**. Die Doku (bridge.py:22-25, :177; wiring.py:945-947) wird an den Code angepasst, kein Promote nach jedem Close | `exec_cfg.longterm_rules` wird nur bei der Konstruktion gelesen. Ein Status `promoted` in der DB ohne geladene Regel wäre ein Mess-Widerspruch |
| **T19** | Der Instinct-Extractor bekommt einen **eigenen** Client: `max_tokens=2048`, `timeout_s=60` als Wiring-Konstanten | Er teilt sich heute den Haiku-Client mit `Brain` (`lesson_max_tokens=400`, `wiring.py:389-400`) und bricht seit 10-15 bei Zeichen 962–988 ab. `InstinctConfig` bleibt unverändert (Docstring „zwei Felder") |
| **T20** | Abschneiden (`stop_reason=="max_tokens"` / `finish_reason=="length"` bei gescheitertem Parse) wird ein **expliziter, nicht-transienter** `LLMResponseError` ohne Retry. Der Token-Meter läuft **vor** dem Parse | Decision 8 (P4) wiederholt nur transiente Fehler; ein gleicher Prompt am gleichen Limit bricht wieder ab. Heute werden gescheiterte Parses nicht gemetert, K6 zählt also zu wenig (`llm_client.py:400-423`) |
| **T21** | Report v5 = **in-place-Erweiterung** von `phase16_activation/scripts/autonomy_report.py` hinter `--prereg v5`. Default `v4` bleibt verdikt-identisch | v3/v4-Berichte müssen reproduzierbar bleiben (Handover §2). Eine Kopie mit 1 165 Zeilen wäre eine zweite Wahrheit |
| **T22** | Exec-Modell **Sonnet 5 (Claude Code)**. Der Scheduler bleibt von **B-0 bis E-3** gestoppt, die anderen drei Dienste laufen weiter. Empfehlung: Exec am Wochenende | Nur der Scheduler hält eine IG-Session (Recorder: nur yF, `recorder.py:8`; Discovery: netzfrei, `run.py:296-316`; WebUI: kein IG). Parallel-Login-Falle (Memory) |
| **T23** | P11 gilt weiter: Kriterien werden **vor** dem Lauf committet und danach nicht geändert. Der Nikinger gibt jede Vorregistrierung beim Commit frei | Ein nachträglich geschriebenes Kriterium beweist nichts (Phase 16 P11) |
| **T24** | Unverändert: demo-only, `RescueConfig.enable_gap_rescue=False`, keine Force-Trigger-Arbeit, 📕-Docs nur per angehängtem datiertem Vermerk | Hard Rules 2–5, Phase-16-Handover §7 |

---

## §2 Selbst gemessene Fakten (2026-10-17, Plan-Session)

### 2.1 Σ-Baseline — **1964 grün** (Kommandoform verifiziert, heute gelaufen)

```bash
cd /home/trading-bot/trading-bot
PY=/home/trading-bot/trading-bot/phase1_broker_wrapper/.venv/bin/python
for d in phase1_broker_wrapper phase2_persistence phase3_external_data phase4_research \
         phase5_execution phase6_debate phase7_reward phase8_scheduler phase9_universe phase10_v3 \
         phase12_data_foundation phase13_live_data phase14_discovery phase15_v4 phase16_activation; do
  echo "$d | $(cd $d && $PY -m pytest tests/ -q -p no:cacheprovider 2>&1 | tail -1)"
done
echo "root | $($PY -m pytest tests/ -q -p no:cacheprovider 2>&1 | tail -1)"
echo "meta | $(cd meta_m1_harness && $PY -m pytest tests/ -q -p no:cacheprovider 2>&1 | tail -1)"   # nicht in Σ
```

| Suite | grün | | Suite | grün |
|---|---:|---|---|---:|
| P1 broker_wrapper | 97 | | P9 universe | 95 |
| P2 persistence | 82 (≈ 58 s) | | P10 v3 | 165 |
| P3 external_data | 108 | | P12 data_foundation | 149 |
| P4 research | 163 | | P13 live_data | 85 |
| P5 execution | 190 | | P14 discovery | 61 |
| P6 debate | 76 | | P15 v4 | 126 |
| P7 reward | 170 | | P16 activation | 15 |
| P8 scheduler | 261 (1 Warning, alt) | | root `tests/` | 121 |
| **Σ (16 Suites)** | **1964** | | meta_m1 (nicht in Σ) | 28 |

Jede Suite **getrennt** laufen lassen (geteilter `tests.conftest`-Name kollidiert).

### 2.2 Git, Prozesse, Units

| Größe | Wert |
|---|---|
| HEAD | `e19c178`, **1 Commit ahead** von `origin/main` (Phase-16-Closeout, nicht gepusht) |
| untracked | `data/` (gitignored-Inhalte) · `sunshine_2026.906.222525-1+ubuntu24.04_amd64.deb` (10,8 MB, Repo-Root) |
| Units | 4 × `active`. Scheduler `ActiveEnterTimestamp` 2026-10-17 10:32:13, `NRestarts=0` |
| Boots | 10-08 16:38→16:59 · 10-11 15:40→15:43 · 10-12 21:08 · 10-17 00:00→00:10 · 10-17 10:29 (`journalctl --user --list-boots`) |
| Stop-Timeouts | `tradingbot-scheduler.service: Main process exited, code=killed, status=9/KILL` + `Failed with result 'timeout'`: 09-23 11:02, 09-30 06:37, 10-11 15:40 |
| Journal | persistent (`/var/log/journal` existiert). Breite `grep`-Abfragen dauern > 120 s, mit Unit-Filter + `--since/--until` schnell |
| Starts je Boot | nach den Boots 10-17 00:10 und 10:29 folgte ~2–3 min später je ein `Stopped`/`Started`-Paar (00:12:54, 10:32:13) → **2 Start-Zeilen je Boot**. Die Ursache ist **nicht** geprüft; die Units sind `PartOf=graphical-session.target` (Unit-Datei). Für Prereg-K1 relevant, ein Reboot ist ohnehin ein Operator-Ereignis (T10) |
| Disk | 14 GB frei. `bars.sqlite` 67 MB, `trading_bot.sqlite` 7,6 MB |

### 2.3 Live-DB `data/trading_bot.sqlite` (mode=ro)

| Größe | Wert |
|---|---|
| `_schema_version` | 9 |
| `trade_outcomes` | 25 Zeilen, alle `CLOSED`, max id 28, **0 OPEN**, `initial_risk IS NULL` = **0** |
| `instincts` | 29, alle `proposed`; `evidence_trade_ids_json IS NULL` = **29/29**; `confidence IS NULL` = 16 |
| `trade_lessons` | 23 — Trades **24 und 25 ohne Lesson** (Close am 10-08, Extraktion am 10-09 im Guthaben-Ausfall) |
| `execution_state.json` | 36 Records, **alle CLOSED** (keine offene Position → B-5 adoptiert beim ersten Start nichts) |
| `decision_context` | 3 669 Zeilen. `abstain_record_id IS NULL` = **3 669/3 669**. Zeilen/Tag 10-12…10-16 = 49/57/79/86/51 (der Rest der 102 Zyklen war budget-blockiert) |
| `market_regime_snapshots` | 3 669 Zeilen, `atr_points`/`range_pct`/`regime_tag` NULL 3 669/3 669 — **so entworfen** („degradiert immer auf `quote_only`", `phase10_v3/CLAUDE.md:42-44`), kein Defekt |
| `abstain_records` seit 10-01 | 772, `context_json='{}'` 772/772 (nie befüllt, kein Konsument) |

Abstains je Tag (Ausschnitt): 10-12 debate 29 · gate 6 · research_empty 14 / 10-13 19 · 10 · 28 / 10-15 0 · 0 · 86.
Die `gate`-Zeilen am 10-12/13 (6 + 10) sind Debatten-**TRADE**-Entscheidungen, die der AEX-Orphan (G3) blockierte.

### 2.4 `data/bars.sqlite` (mode=ro)

| Quelle | Zeilen | Zeitraum |
|---|---:|---|
| `yf` | 130 809 | 08-17 → 10-16 |
| `ls` | 149 250 | 09-25 → 10-16 (R4-Archivierung entfernte die älteren 4,05 Mio) |
| `ig` | **3 730** (1m 2 083 aus August · 5m 1 647) | 07-17 → 10-16, **alle +2 h verschoben** |
| `capital` | 962 | nur 08-21 (Operator-Probe Phase 13) |

- **IG-Beweis:** die MIB-5m-Bars, abgerufen 07:07:12Z, haben `ts_utc` 08:45–09:05Z. Der Bar „09:00Z" hat Close **49 663,2**. Der LS-1m-Bar um **07:04Z** hat ebenfalls **49 663,2**, der um 09:04Z dagegen 49 798,2.
- **yF-Archiv-Lag** (`fetched_at − ts_utc`, 1m, 10-16 07–15Z, n = 3 824): p10 15,6 · p50 17,6 · p90 19,6 · max **20,3 min**.
- **IG-Spend** `source_spend` 10-12…10-16: `research` 8 Zeilen/40 Pkt je Tag, `sample` 8–16/24–48. Dazu 10-16 22:17Z und 10-17 08:36Z (nachts bzw. Samstag, nach den Reboots).
- **IG-Allowance** (letzte Zeile): 10 000 gesamt, **8 195** übrig, Ablauf 2026-10-19T07:04Z.

### 2.5 `llm_usage.json` und Budget

| Tag | Calls | Tokens | davon Sonnet | Haiku-Calls | € |
|---|---:|---:|---:|---:|---:|
| 10-12 | 149 | 301 561 | 214 293 | 68 | 1,02 |
| 10-13 | 142 | 300 399 | 227 616 | 58 | 1,03 |
| 10-14 | 103 | 302 539 | 286 030 | 16 | 1,07 |
| 10-15 | 92 | 303 910 | 301 087 | 6 | 1,09 |
| 10-16 | 138 | 301 031 | 228 900 | 60 | 1,01 |

- Research-Call ≈ **3 501 Tokens** (10-15: 301 087 / 86).
- Ein voller Tag hat 102 Zyklen à 5 min, das sind ≈ 357 k Tokens > Cap 300 k. **K6 ist im 5-min-Takt mit keinem Modell erfüllbar**, solange der Cap Tokens zählt.
- Die Kosten liegen bei ≈ **1,0 €/Tag**, Geld ist also nicht das Problem.

### 2.6 `research_health.jsonl` — Event-Typen (gesamt)

`ls_tickagg_candle_written` 149 258 · `abstain_recorded` 3 961 · `context_recorded` 3 669 · `bar_fetch` 1 974 · `window_uncovered` 670 · **`divergence_no_comparator` 233** · `measurement_heartbeat` 36 · `quote_divergence` **0** · `stale_source` **0**.

Heartbeat 10-07…10-15 alle `ok`, 10-16 `not ok` (2 DAX-Epics unter der Coverage-Schwelle) → 1 CRITICAL.

### 2.7 Step-0-Erwartung (Turbo / EPIC_MAP)

- `grep -rni turbo --include=*.py --include=*.sql --include=*.sh . --exclude-dir=.venv`: **20 Zeilen in 13 Dateien**. Alle sind der eingefrorene Legacy-Name `turbo_candidates.json`; die einzige andere Zeile ist der Schutzkommentar `phase2_persistence/persistence/state.py:27` („Do NOT rename").
- `grep -rn EPIC_MAP --include=*.py`: **3** Phase-14-Doku-Kommentare (`test_store.py:239`, `models.py:121`, `store.py:194`).
- Erwartung: **No-Op, 7. Mal.**

### 2.8 Funktions-Inventar — liefert jeder vorhandene Arm? (Live-Daten 10-12…10-16)

| Arm (Flag-Default) | Beleg | Status |
|---|---|---|
| Research (P4) | Picks + Abstains täglich, 14–86 `research_empty`/Tag | ✅ (gebremst durch K6-Cap) |
| Debatte (P6) | 4–29 Debatten-Abstains/Tag, 2 Trades 10-16 | ✅ |
| Reward/Lessons (P7) | 25 `reward_pts`, 23 Lessons | ✅ (2 Lücken: Ausfall 10-09, kein Nachholen — §10) |
| **Promotion-Bridge** (P15, `enable_instinct_promotion=True`) | 29 × `proposed`, Evidence 29/29 NULL; 10-05…10-07 `validate() missing 'trades'`; seit 10-15 Extractor-Abbruch | ❌ **tot** (§3 D3) |
| VETO 5 | `longterm_rules == ()` | inert (so gewollt, n = 25 < 50) |
| Abstain-Lessons + Reflect (P10) | Lessons nur für Debatten-Abstains (`reflect_stages={DEBATE}`), Cap 10 | ✅ (so gewollt) |
| Paper/Shadow (P10) | 137–179 Paare/Tag; seit 10-09 ≥ 95 % `RESOLVED` | ✅ |
| Council-Paper-Call | 3 `COUNCIL_PICK`/Tag | ✅ |
| Context-Persistenz (P10) | 1 Zeile je Entscheidung | ⚠ Verknüpfung `abstain_record_id` tot (§3 D7) |
| Bar-Stream LS (P13) | ≈ 10,5 k Kerzen/Tag | ✅ |
| Recorder yF (P12) | ≈ 4 k Bars/Tag | ✅ |
| **Divergenz-Sampler** (P12, `enable_divergence_sampler=True`) | 233/233 `no_comparator`, kostet 24 Pkt/Tag + je Neustart | ❌ **tot** (§3 D2) |
| Measurement-Heartbeat (P12) | 1/Tag, meist `ok` | ✅ |
| Discovery (P14, ARMED) | `discovery_state.json` 24 Zeilen/Pass, aber **kein** append-only Beleg | ⚠ (§3 D12) |
| Universe-Refresh (P9) | `bar_fetch` 09/13/17 Uhr | ✅ |
| Token-Budget (P8) | erschöpft an jedem Volltag | ✅ technisch / ❌ K6 (§3 D10) |
| Loss-Breaker (P8) | blind bis zum IG-Settlement | ⚠ (§3 D6) |
| Margin-Cap (P5 D3) | nur Live-Probe 09-07 | ⚠ ungeprüft, kein Phase-17-Ziel (§10) |

### 2.9 Doku-Drift (gegen Code/Git, 2026-10-17)

| Datei:Zeile | Behauptung | Wahrheit |
|---|---|---|
| `README.md:40` | Phase 16 „🔄 in execution seit 2026-09-05 — Block A läuft (A-0..A-2 ✅)" | abgeschlossen mit Teilbilanz 2026-10-16 |
| `ARCHITECTURE.md:260-266` | Phase 9 „in Arbeit", 10 „geplant, no concept doc yet", 12 „🆕 geöffnet", 15 „deferred, no concept doc yet"; Phase 16 fehlt | 10/12–16 abgeschlossen, Konzept-Docs existieren |
| `ROADMAP.md` | 41 827 B, Status 📗 | L2-Grenze 40 KB überschritten |
| root `CLAUDE.md` | 36 806 B; INDEX nennt „20KB" | Banner seit 2026-08-31 angewachsen |
| `docs/INDEX.md:33` | „Active phases (16 — Freischaltung 🔄 eröffnet …)" | Phase 16 geschlossen |
| root `CLAUDE.md:204` | Phase 9 „🔄 in Arbeit (Stand 2026-07-07)" | Code produktiv seit 07-06, nie formal geschlossen (Nikinger-Sache, §10) |
| `phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md:105` | „Unbekannt geblieben: die Ursache des Scheduler-Stopps am 10-08 … des Starts am 10-11 19:02" | VM-Reboots (Journal §2.2; Nikinger 2026-10-17) |
| `phase15_v4/instinct/bridge.py:22-25,177` + `wiring.py:945` | `promote()` läuft „at scheduler start **and** after each close" | nur beim Start (`after_trade_closed` ruft `promote()` nicht) |
| `phase4_research/research/llm_openai_compat.py:3` | „**Not wired into any live path.**" | wird mit C-4 verdrahtet |
| `wiring.py:752-753` | „locked `AbstainSink.on_no_trade(cycle_outcome) -> None` contract" | die Sink gibt `record_id` zurück (`sink.py:58,87`) |
| `phase14_discovery/scripts/run_discovery.sh:46` | druckt immer „(unarmed ⇒ noop)" | der Daemon ist seit 08-26 ARMED |
| `phase16_activation/scripts/autonomy_report.py:1064` | Summary-K2 „über das Fenster" | wertet **nur `from_day`** aus |

---

## §3 Befunde D1–D13 (alle selbst verifiziert 2026-10-17)

### D1 — IG-REST-Bars tragen Ortszeit als UTC (🔴, P1/P12)

- `phase1_broker_wrapper/broker_wrapper/adapters/ig_adapter.py:909` → `timestamp=p.get("snapshotTime") or p.get("snapshotTimeUTC", ""),`. `snapshotTime` ist die Ortszeit des Kontos.
- `phase12_data_foundation/data_foundation/models.py:61-71` `_iso_from_dt` behandelt naive Zeiten als UTC (eigener Kommentar: „never been live-verified against a real DST boundary").
- Beweis: §2.4. Folgen:
  - (a) Der Sampler sucht 2 h in der Zukunft (D2).
  - (b) Das F1-Stale-Gate `service.py:150` (`_age_minutes(newest, now) > 120`) war blind, weil die Alter negativ waren.
  - (c) `archive.window(prefer=("ig","capital","ls","yf"))` (`archive.py:162`) bevorzugt IG-Bars am falschen Ort.
- **Nicht** betroffen: Handels-Gates. Die Momentum-VETO liest nur Closes (`vetos.py:126-145`), die Debatte zeigt keine Zeitstempel, der Paper-Tracker liest 1m-Fenster (IG schreibt seit August nur 5m).

### D2 — Divergenz-Sampler hat nie verglichen (🔴, P12/P8)

`heartbeat.py:297-371`. Drei Ursachen hintereinander:
1. D1: das Vergleichsfenster liegt 2 h in der Zukunft.
2. Er nimmt `ig_bars[-1]` (`:319`), den **laufenden** Bar. Das yF-Archiv hängt 15–20 min hinterher.
3. Er läuft beim ersten Refresh nach Öffnung (09:04–09:09); der Throttle wird **vor** dem Vergleich gesetzt (`:314`), es gibt also keinen zweiten Versuch am Tag.

Zusätzlich vergleicht `compute_return_divergence` (`:228-251`) Summen aus 5-min- und 1-min-Renditen. Das sind verschiedene Horizonte, also entstünden nach einem reinen Zeitstempel-Fix **falsche** `quote_divergence`-Events. Nach 2 davon folgt `mark_mismatch`, eine Einbahnstraße (`wiring.py:1103-1120`).

Kosten heute: 24 IG-Pkt/Tag plus je Neustart, auch nachts und am Wochenende. Grund: der Preflight-Refresher (`runner.py` `preflight()` → `_run_universe_refresher()`) läuft ohne Phasen-Check.

### D3 — Promotion-Bridge: drei Nahtfehler + Abbruch + Doku (🔴, P15/P8)

1. `bridge.py:146` `decision = self.validator.validate(instinct)` — `validator.py:97-101` verlangt `validate(self, instinct, trades)` → `TypeError` je Instinct (Log 10-05…10-07).
2. `bridge.py:147` `new_status = decision.value if hasattr(decision, "value") else str(decision)`. `InstinctValidation` hat `.decision` (`validator.py:72`), nicht `.value`. `str(...)` liefert den Dataclass-Repr, `update_instinct_status` wirft dann `ValueError` (`db.py:500-503`).
3. `bridge.py:163-170` schreibt die Keys `"evidence_trade_ids"`/`"contradictions_trade_ids"`. Die Whitelist `_INSTINCT_COLUMNS` (`db.py:54-58`) kennt nur `…_json` → **still verworfen** (29/29 NULL live).
4. Der Test-Fake `tests/test_instinct_bridge.py:121-133` hat `validate(self, instinct)` und liefert `.value`, deshalb blieb die Naht grün.
5. Extractor-Abbruch seit 10-15 (char 962–988, `JSONDecodeError`): geteilter Haiku-Client mit `lesson_max_tokens=400` (`reward/models.py:379`, `wiring.py:389-400`). Der Zusammenhang ist **inferiert** — B-4 macht ihn sichtbar.
6. Doku-Drift „promote nach jedem Close" (§2.9).

### D4 — Abschneiden unsichtbar, Fehl-Parses ungezählt (🟠, P4)

- `llm_client.py:378-423`: kein Blick auf `message.stop_reason`. `token_meter.record` läuft erst **nach** erfolgreichem `json.loads` (`:411-422`).
- `llm_openai_compat.py:242-287` dito, mit `finish_reason`. Außerdem fehlt dort ein Fallback, falls ein Endpoint `response_format` mit HTTP 400 ablehnt (anders als `LLMClient._attempt:388-398`).
- Der Keyring-Username ist fest `"api_key"` (`:82`, `:170`).

### D5 — Monitor-Orphan nach Restart (🔴, P5/P8)

- `order.py:68` lässt `present` stehen („the monitor handles it"). Der Monitor läuft aber nur **innerhalb** von `Executor.run()` direkt nach `place_order` (`executor.py:350-372`).
- Nach einem Restart startet ihn niemand. `max_hold` (240) und `square_off` (17:15) greifen nie (AEX id 26: 10-08 15:42 → 10-14 17:12).
- **Nebeneffekt:** Research und Debatte laufen **vor** Gate 3 (`runner.py:386-405`, `executor.py:299-302`). Jeder blockierte Zyklus bezahlt also LLM-Calls (10-12/13: 149/142 Calls).
- `monitor_position` setzt `entry = now_fn()` (`monitor.py:90`) und kennt keinen echten Einstieg.

### D6 — Breaker-Blindfenster (🟠, P8, Hard Rule 5)

`wiring.py:1009-1016` summiert `profit_loss IS NOT NULL`. Ein vom Broker geschlossener Trade ist bis zum Settlement `status='OPEN'` mit `profit_loss` NULL → unsichtbar.
`AutoConfirm` behandelt eine **werfende** Closure fail-closed (`safety.py` Modul-Docstring, Absatz „The DB read is wrapped fail-closed").

### D7 — Abstain-Naht verwirft `record_id` (🟠, P8)

- `wiring.py:758-760` `class _Observed: def on_no_trade(self, cycle_outcome: Any) -> None: inner.on_no_trade(cycle_outcome)` — der Rückgabewert geht verloren.
- Der Executor reicht ihn als `abstain_record_id` an den Context-Recorder (`executor.py:186-201`) → 3 669/3 669 NULL.
- Reihenfolge `wiring.py:993-995`: `_observed_abstain_sink(_enrich_abstain_detail(…))` → das Observability-Event klassifiziert den **un**angereicherten Zyklus.

### D8 — Paper-CRITICAL-Rauschen (🟡, P10)

- `paper.py:321` (Council-LLM), `:386` (`on_debate_abstain`, `get_price`), `:465` (`open_scheduled_pairs`, `get_price`), `:701` (Reflect-LLM) loggen `critical` für Ausfälle **externer** Abhängigkeiten.
- 10-09: 72× `:701` (Guthaben-Ausfall). `:563`/`:685` sind lokale Fehler (Bug-Indikatoren, z. B. NameError 08-26) und bleiben CRITICAL.

### D9 — LLM-Ausfall ununterscheidbar (🟠, P4/P8/P10)

- `research.py:198-201` fängt `LLMResponseError` → `_abstain("LLM error: …")`. `research_tick.py:219` setzt pauschal `LLM_ABSTAIN`.
- Der P10-Klassifizierer kennt nur `REASON_NO_CANDIDATES` (`classifier.py:64-68`).
- `AbstainReason` hat 12 Werte; der Test `test_models.py:47` pinnt `== 12`.

### D10 — K6 zählt Tokens, modellblind (🟠, P8/P16)

- `budget.py:177-183` summiert alle Records des Tages. Die WebUI-Karte zählt **eigenständig** dasselbe (`webui/api.py:289-296`). Der Report hat seine eigene Summe (`autonomy_report.py:369-425`).
- Drei Stellen müssen dieselbe Ausnahme kennen.

### D11 — Report-Drifts (🟡, P16)

- K9 fehlt.
- K2-Discovery ist ein Proxy auf Scheduler-Events (`autonomy_report.py:660,663`); die WebUI ist eine Konstante (`:656`); der Summary-K2 prüft nur `from_day` (`:1064`).
- K5 ohne Aufschlüsselung nach Logger.
- K7 kennt kein LLM-Profil.

### D12 — Discovery ohne append-only Beleg (🟡, P14)

- `source_registry/run.py:194-255` schreibt nur `discovery_state.json` (in place) und loggt `debug`.
- Das Log-Format ist `basicConfig` ohne Zeitstempel (`:336`) — eine Zeile muss den Zeitstempel selbst tragen.
- `run_discovery.sh:46` druckt statisch „(unarmed ⇒ noop)".

### D13 — Stop-Timeout → SIGKILL (🟠, P16-Unit)

- `tradingbot-scheduler.service` hat kein `TimeoutStopSec` (Default 90 s). `request_stop()` wirkt erst nach dem laufenden `clock.sleep` (≤ 300 s, `runner.py` `request_stop`-Docstring „v1 latency").
- Belege: §2.2.

---

## §4 Cross-Phase-Touches (T13) — wer fasst was an

| Phase | Dateien | Steps |
|---|---|---|
| P1 | `broker_wrapper/adapters/ig_adapter.py`, `tests/test_ig_adapter.py` | B-1 |
| P2 | nur Import in Tests (`persistence.Database`) | B-3, B-6 |
| P4 | `research/llm_client.py`, `research/llm_openai_compat.py`, `research/models.py`, `research/research.py`, `scripts/openrouter_smoke.py`, Tests | B-4, C-3, C-5, C-6 |
| P5 | `execution/monitor.py`, `execution/executor.py`, Tests | B-5 |
| P8 | `scheduler/llm_profiles.py` (NEU), `scheduler/config.py`, `scheduler/budget.py`, `scheduler/research_tick.py`, `scheduler/runner.py`, `scheduler/run.py`, `scripts/wiring.py`, `webui/api.py`, Tests | B-2, B-3, B-5, B-6, B-7, C-1, C-2, C-4, C-5, D-1 |
| P10 | `abstain_lessons/paper.py`, `abstain_lessons/models.py`, `abstain_lessons/classifier.py`, Tests | B-8, C-5 |
| P12 | `data_foundation/heartbeat.py` (+ ggf. `models.py` B-1b), Tests | B-1b, B-2 |
| P14 | `source_registry/run.py`, `scripts/run_discovery.sh`, Tests | B-10 |
| P15 | `instinct/bridge.py`, `tests/test_instinct_bridge.py` | B-3 |
| P16 | `systemd/tradingbot-scheduler.service`, `scripts/autonomy_report.py`, `tests/test_autonomy_report.py`, `PHASE16_CLOSEOUT_HANDOVER.md` (nur angehängter Vermerk) | A-3, B-9, E-1 |
| root | `scripts/check_doc_rotation.py`, `scripts/store_minimax_key.py`, `tests/`, Docs | A-0, A-3, C-6 |

---

## §5 Contracts (verifiziert 2026-10-17)

| Naht | Vertrag |
|---|---|
| LLM-Client (beide) | `ask_candidate(system, user, json_schema) -> dict`; Attribute `.model`, `.max_tokens`, `.temperature`, `.last_usage` (`llm_client.py:246-258`, `llm_openai_compat.py:150-161`) |
| Debatte | `llm_caching.ask_agent` überschreibt **je Rolle** `client.model`, `client.temperature` (`:90-91`), `debate.py:229` setzt `self._llm.max_tokens`. Rollenmodelle stehen in `DebateConfig` (frozen dataclass, `model_bull/bear = claude-haiku-4-5-20251001`, `model_judge = claude-sonnet-4-6`, `max_tokens_agent=512`, `max_tokens_judge=768`, `models.py:134-163`) |
| Brain / Extractor / PaperDebateCaller / `_AbstainLLMAdapter` | rufen nur `ask_candidate`, keine Modell-Mutation (`brain.py:215`, `extractor.py:283`, `paper.py:320`, `wiring.py:437-439`) |
| Meter | `token_meter.record(usage, model, config, path) -> dict` (`token_meter.py:120`); unbekanntes Modell → Kosten 0 + WARNING (`:79-82`) |
| Budget | `TokenBudget.consumed_today()` / `is_exhausted()` (`budget.py:168-195`), fail-open bei unlesbarem Log |
| Executor | `run()`: `reconcile_startup` → G1 → G2 → Debatte → G3/G5 → G4 → VETOs → confirm → `place_order` → `monitor_position` → `_notify_closed` (`executor.py:229-377`) |
| ExecutionState-Record | `{deal_reference, epic, direction, size, stop_level, limit_level, status, deal_id, recorded_at, updated_at}`, ISO `…mmmZ` (`execution_state.py:118-131`) |
| `OrderPlan` | `epic, direction, size, stop_level, limit_level, deal_reference, currency` (`models.py:44-50`) |
| `build_closed` | liest `result.plan.deal_reference`, `deal_id`, `status`, `close_level`, `profit_loss` (`executor.py:623-640`) |
| RewardSink kalt | `on_trade_closed` rekonstruiert den Open-Kontext aus der DB-Zeile (`recorder.py:318-338`, `_OpenCtx` `:371-377`) |
| Validator | `InstinctValidator.validate(instinct, trades: Iterable[dict]) -> InstinctValidation(decision, evidence_count, contradiction_count, reason)`; zählt nur IDs, die in `trades` als `row["id"]` vorkommen (`validator.py:97-170`) |
| DB-Instincts | `insert_instinct(dict)` whitelistet `_INSTINCT_COLUMNS`, serialisiert `…_json`-Listen; `update_instinct_status(id, status)` wirft bei unbekanntem Status (`db.py:442-517`) |
| DB-Trades | `get_recent_trades(n)` = `SELECT * … ORDER BY id DESC LIMIT n` (`db.py:228-233`); `insert_trade` Pflichtfelder siehe `001_initial.sql` |
| Archiv | `BarArchive.window(epic, res, start, end, *, prefer=("ig","capital","ls","yf"), sources=None)` (`archive.py:155-180`), `[start, end)` |
| IG-Bars aus `BudgetedIGBarProvider` | `PriceBar(ts, open, high, low, close, volume)` mit `ts = normalize_bar_ts(b["timestamp"])` (`service.py:130-140`) |
| Research-Tick | `ensure_candidates(state) -> ResearchResult(picked, n, reason, context_health, abort_detail)`, Reasons `research_tick.py:84-89` |
| Abstain | `AbstainLessonSink.on_no_trade(outcome) -> str \| None` (`sink.py:58-90`); Klassifizierer-Priorität error → research_empty → failed_gate → debate (`classifier.py:45-84`) |
| Start-Zeile | `run.py:206-212`; der Report parst `starting scheduler daemon \((?P<inner>[^)]*)\)` und darin einzelne Keys (`autonomy_report.py:487-509`) |
| Units | werden **kopiert**, nicht verlinkt (`scripts/install_units.sh`: `systemd-analyze --user verify`, dann Kopie nach `~/.config/systemd/user/`) |

---

## §6 Schritt-Sequenz

> Konvention: pro Step **Ziel → Anker (verbatim, Zeile e19c178) → Edit → Tests → Akzeptanz**.
> Jeder Step = ein atomarer Commit (`phase17+phaseN: …`). Nach jedem Step die betroffene(n) Suite(s)
> grün, nach jedem Block der volle Sweep §2.1. Test-Zahlen „+n" sind die Mindestzahl neuer Tests.

### Block A — Haushalt (Bot läuft, nur Docs)

#### A-0 — Phasenkopf lesen, Session rotieren, Hook-Liste

1. `phase17_testbed/CLAUDE.md` lesen. Den Plan-Session-Block **wortgleich** nach `phase17_testbed/SESSIONS_ARCHIVE.md` (NEU, Header-Card wie `phase16_activation/SESSIONS_ARCHIVE.md`) verschieben und den eigenen Block „Session #1" anlegen. Danach `./SESSIONS_ARCHIVE.md` in die `down:`-Liste des Phasenkopfs aufnehmen; vorher würde Hook-Step 4 an einem toten Link scheitern.
2. `scripts/check_doc_rotation.py:88` Anker `    "phase16_activation",` → darunter neue Zeile `    "phase17_testbed",`.
3. `docs/INDEX.md`: Zeile für `phase17_testbed/SESSIONS_ARCHIVE.md`.
- **Tests:** `python3 scripts/check_doc_rotation.py --strict --phase phase17_testbed` exit 0; root-Suite grün (`tests/test_check_doc_rotation.py:193` prüft jeden Phasenkopf in `PHASE_DIRS`).
- **Kein** `tests/`- oder `scripts/`-Verzeichnis in `phase17_testbed/` anlegen: Phase 17 hat keinen eigenen Code, und Σ bleibt bei 16 Suites.

#### A-1 — Step-0-Ritual (auch als No-Op protokollieren)

```bash
grep -rni "turbo" --include="*.py" --include="*.sql" --include="*.sh" . --exclude-dir=.venv | grep -v "/.venv/"
grep -rn "EPIC_MAP" --include="*.py" . --exclude-dir=.venv | grep -v "/.venv/"
```
- Erwartung §2.7 (20/13 + 3).
- Ergebnis als Tabelle in den Phasenkopf.
- Ein Treffer, der **nicht** `turbo_candidates.json`, `state.py:27` oder Phase-14-Doku ist → stoppen, melden, **nicht** umbenennen.

#### A-2 — Regression-Baseline VOR dem ersten Fix

- Sweep §2.1, **Erwartung Σ 1964** (+ meta 28).
- Eine Abweichung ist ein Befund von *vor* Phase 17: dokumentieren, nicht reparieren.

#### A-3 — Code↔.md-Sweep (Drift §2.9)

| Datei | Anker (verbatim) | Edit |
|---|---|---|
| `README.md:40` | `\| 16    \| Freischaltung (alle Löcher zu, alle Arme scharf, 2-Wochen-Autonomie-Test) \| 🔄 **in execution seit 2026-09-05** — Plan execution-ready; Block A läuft (A-0..A-2 ✅) \|` | Status → `✅ **abgeschlossen mit Teilbilanz (Closeout 2026-10-16)**`; darunter neue Zeile `\| 17    \| Prüfstand (Mess-/Geldpfad-Defekte zu, LLM austauschbar, Report + Prereg v5) \| 🔄 **in execution seit <Datum>** \|` |
| `ARCHITECTURE.md:260-266` | die sieben Zeilen `- Phase 9 (V2 — Foundation, in Arbeit) — …` bis `- Phase 15 (V4 — Sophisticated/Optional, deferred) — no concept doc yet` | Statuswörter gegen root-`CLAUDE.md`-Tabelle angleichen (10/12/13/14/15/16 ✅ mit Konzept-Link `docs/concepts/phase10_v3_plan…`/`phase15_v4_plan.md`/`phase16_activation_plan.md` — Dateinamen per `ls docs/concepts/` prüfen); neue Zeilen Phase 16 + 17; Header-Card `updated:` |
| `ROADMAP.md` | Abschnitte von `## Phase 9 — V2: Foundation (Autonome Epic-Research + Daten-Input-Zuverlässigkeit)` (Z. 58) bis vor `## Phase 15 — V4: …` (Z. 435) | **wortgleich** ans Ende von `ROADMAP_ARCHIVE.md` verschieben (Archiv-Card: `purpose` „Phasen 1–14", `updated`, Intro-Satz um „+ Phasen 9–14 rotiert <Datum>, Phase 17 A-3" ergänzen); in `ROADMAP.md` die Summary-Tabelle um 6 Einzeiler (9–14, Status wie in der root-Tabelle: 9 🔄 formal offen, 11 🛑 deferred) erweitern, Überschrift `## Phasen 1–14 → [ROADMAP_ARCHIVE.md](./ROADMAP_ARCHIVE.md) (archiviert; 9 formal offen, 11 deferred)` — **nicht** „Abgeschlossene Phasen": den Phase-9-Closeout entscheidet der Nikinger (§10), **neuer Abschnitt `## Phase 17 — Prüfstand`** (Goal = §0-Mission, Blöcke A–E als Checkboxen, Done-When = AK19+AK20, Directory). **AK: `ROADMAP.md` < 40 000 B** |
| root `CLAUDE.md` | Banner-Blöcke Z. 104–113 (`> **🔄 2026-09-05 — Phase 16 (Freischaltung) ERÖFFNET …`), 115–133 (`> **✅ 2026-09-05 — Phase 15 (V4) ABGESCHLOSSEN …`), 135–163 (`> 🟡 **Korrekturhinweis 2026-09-08 …`), 175–192 (`> ✅ **2026-08-31 — Phase 13 + Phase 14 ABGESCHLOSSEN …`) | **wortgleich** in einen neuen datierten Abschnitt am Ende von `docs/sessions/root_claude_md_phase_status_archive.md` verschieben; Tabellenzeilen 12–16 auf je **eine** Zeile kürzen (Status + Link Phasenkopf/Handover) — der alte Zeilentext geht wortgleich in denselben Archiv-Abschnitt. Zeile 9: datierter Vermerk „🟡 *2026-10-xx: Status-Prosa veraltet — Phase-9-Code produktiv seit 2026-07-06, formaler Closeout nie geschrieben (Nikinger-Entscheidung, nicht Phase 17)*". Zeile 15 (Gate P7/A6): Vermerk „*E6 entschieden 2026-10-17: Gate P7/A6 erfüllt (deal-bezogen max 2 CRITICALs je Trade, Quell-Definition)*". **AK: < 25 000 B** |
| `docs/INDEX.md` | Zeile 24 `- [CLAUDE.md](../CLAUDE.md) — 📗 20KB · …`, Zeile 27 `… ROADMAP.md … 📗 **38 KB** …` | Größen auf die gemessenen Werte nach dem Sweep; Phase-16-Einträge aus „Active phases" unter „Closed phases" verschieben; Header-Card `updated:` |
| `phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md` (📕) | Dateiende | **nur anhängen:** `> 🟡 **Korrekturhinweis <Datum> (Phase 17 A-3):** §4 „Unbekannt geblieben" — Scheduler-Stopp 10-08 und Start 10-11 19:02 sind VM-Reboots (Journal: Boot-Ende 10-08 16:38:49 / -Start 16:59:39; Boot-Ende 10-11 15:40:58, Scheduler SIGKILL 15:40:57 nach Stop-Timeout, Start 19:02 = grafischer Login). Nikinger 2026-10-17: Reboots vom VM-Host ausgelöst. §5 E1–E8 entschieden → docs/concepts/phase17_testbed_plan.md §1.` |

- **Zeilen-Hinweis:** der Plan-Commit selbst fügt in root `CLAUDE.md` das Phase-17-Banner (14 Zeilen) und Tabellenzeile 17 ein → die Banner-Anker oben stehen bei der Ausführung **14 Zeilen tiefer** (z. B. Phase-16-ERÖFFNET ab Z. 118). In `docs/INDEX.md` kommen 2 Zeilen unter „Active phases" dazu. Maßgeblich sind die Verbatim-Strings.
- **Nicht** in A-3: `bridge.py`/`wiring.py`/`llm_openai_compat.py`-Docstrings. Die ändern sich mit ihrem Code (B-3, C-3, B-7).
- **AK:** `find . -name "*.md" -not -path "./.agents/*" -not -path "*/.pytest_cache/*" -not -path "*/.venv/*" -size +40k` enthält keine 📗/🔄-Datei außer den drei Altlasten `docs/INDEX.md`, `phase15_v4/CLAUDE.md`, `phase7_reward/CLAUDE.md`. Diese werden nur im Phasenkopf **gelistet**, nicht umgebaut (§10).

#### A-4 — Operator (Nikinger): Push + Fremddatei

```bash
git push -u origin main          # e19c178 (Phase-16-Closeout) + Plan-Commit + A-Commits
```
- `sunshine_2026.906.222525-1+ubuntu24.04_amd64.deb` (10,8 MB, untracked) aus dem Repo-Root entfernen oder verschieben. Das ist **Nikinger-Aktion**; die Exec-Session fasst die Datei nicht an.
- **Block-A-Commits:** 2 (A-0+A-1+A-2 Doku · A-3 Sweep).

---

### Block B — Mess- und Geldpfad-Defekte (Scheduler gestoppt)

#### B-0 — Scheduler stoppen + IG-Probe anfordern

```bash
systemctl --user stop tradingbot-scheduler.service     # dauert heute bis 90 s, endet ggf. in SIGKILL (D13, erwartet)
ps aux | grep "scheduler.run" | grep -v grep           # Gegenprobe: leer
```
Recorder, Discovery und WebUI laufen weiter (T22).

Danach bittet die Exec-Session den Nikinger um den **IG-Probe** (1 Datenpunkt, Demo, bei gestopptem Scheduler):

```bash
cd /home/trading-bot/trading-bot && phase1_broker_wrapper/.venv/bin/python - <<'EOF'
from broker_wrapper import get_broker     # verified offline 2026-10-17; _request(params=…) ig_adapter.py:264-276
b = get_broker("ig_demo"); env = b.connect(); assert env.ok, env.error
body = b._request("GET", "/prices/IX.D.DAX.IFMM.IP", version="3", auth=True,
                  params={"resolution": "MINUTE_5", "max": 1, "pageSize": 1})
p = body["prices"][0]
print({k: p.get(k) for k in ("snapshotTime", "snapshotTimeUTC")})
b.disconnect()
EOF
```

Erwartung: beide Felder vorhanden, `snapshotTimeUTC` = `snapshotTime` − 2 h, also ISO ohne Offset. Das Ergebnis kommt in den Phasenkopf.

#### B-1 — IG-Zeitstempel (D1, P1)

- **Anker** `ig_adapter.py:909`: `        timestamp=p.get("snapshotTime") or p.get("snapshotTimeUTC", ""),`
- **Edit:**
  ```python
          # Phase 17 B-1: UTC first. ``snapshotTime`` is the account's LOCAL time (Europe/Berlin,
          # +2 h CEST, measured 2026-10-17) and normalize_bar_ts stored it as UTC — every IG REST
          # bar landed in the future (divergence sampler 233/233 no_comparator, F1 gate blind).
          timestamp=p.get("snapshotTimeUTC") or p.get("snapshotTime", ""),
  ```
- **B-1b (nur wenn der Probe `snapshotTimeUTC` NICHT zeigt):** `data_foundation/models.py:95-96`, Anker `        if "/" in raw:` / `            dt = datetime.strptime(raw, "%Y/%m/%d %H:%M:%S")`. Den geparsten naiven Wert als `ZoneInfo("Europe/Berlin")` interpretieren (`dt.replace(tzinfo=ZoneInfo("Europe/Berlin"))`); `_iso_from_dt` rechnet dann nach UTC um. Den Kommentar `:63-66` anpassen. Test: `"2026/10/16 09:00:00"` → `"2026-10-16T07:00:00.000Z"`, `"2026/10/26 09:00:00"` → `"2026-10-26T08:00:00.000Z"` (DST).
- **Tests P1 (+1):** `test_parse_bar_prefers_snapshot_time_utc_over_local_snapshot_time` — Eingabe beide Felder → `bar.timestamp == "2026-10-16T07:00:00"`. Die bestehenden Fixtures mit nur `snapshotTime` bleiben grün (Fallback).
- **AK:** P1 98 grün. Die Datenreparatur (Löschen) folgt erst in **E-3**, weil sie den Recorder-Stopp braucht.

#### B-2 — Divergenz-Sampler (D2, P12 + P8)

**P12 `data_foundation/heartbeat.py`:**
1. `compute_return_divergence` (Z. 228–251, Anker `def compute_return_divergence(ig_bars: list[Any], yf_bars: list[Any]) -> float | None:`) **ersetzen**. Geprüft per `rg -n compute_return_divergence` (2026-10-17): der **einzige Code-Aufrufer** ist `heartbeat.py:351`, die übrigen Treffer sind 📕-Doku und der Testkommentar `test_heartbeat.py:217`. Ein Alias ist also nicht nötig; den Docstring-Verweis `heartbeat.py:271` (`siehe :func:`compute_return_divergence``) auf `window_return_divergence` umstellen. Neuer Code:
   ```python
   # Phase 17 B-2 (2026-10-17): yF 1m bars reach the archive 15.6–20.3 min after their timestamp
   # (p10/max, measured 2026-10-16); the comparator window must end this long before "now".
   COMPARATOR_LAG_MIN: int = 25
   IG_SAMPLE_COUNT: int = 8        # 8 × 5m = 40 min → always ≥ 1 complete bar older than the lag
   MIN_YF_BARS: int = 4            # ≥ 4 of the 5 one-minute bars, or the window is not comparable


   def window_return_divergence(ig_bar: Any, yf_bars: list[Any]) -> float | None:
       """|return(IG 5m bar) − return(yF 1m bars over the SAME five minutes)| (Phase 17 B-2).

       return = (last close − first open) / first open; a constant CFD-vs-cash basis cancels.
       ``None`` when a side has no usable open. Replaces ``compute_return_divergence``, which
       summed two 5-minute IG returns against two 1-minute yF returns (different horizons).
       """
       if not yf_bars or not ig_bar.open or not yf_bars[0].open:
           return None
       ig_r = (ig_bar.close - ig_bar.open) / abs(ig_bar.open)
       yf_r = (yf_bars[-1].close - yf_bars[0].open) / abs(yf_bars[0].open)
       return abs(ig_r - yf_r)
   ```
2. `DivergenceSampler.sample_epic` (Z. 297–371): Docstring anpassen und den Rumpf **von Z. 311 bis zum Methodenende Z. 371** ersetzen. Die verbatim Anker:
   - Z. 311 `        today = self.now_fn().strftime("%Y-%m-%d")`
   - Z. 312 `        if self._last_sample_date.get(epic) == today:`
   - Z. 314 `        self._last_sample_date[epic] = today` (wandert nach (g))
   - Z. 316 `        ig_bars = self.budgeted_ig.get_bars(epic, resolution="5m", count=3)`
   - Z. 319 `        ig_bar = ig_bars[-1]`
   - Z. 351 `        delta = compute_return_divergence(ig_bars, yf_bars)`

   Der neue Ablauf:
   - (a) Throttle prüfen, aber **noch nicht setzen**.
   - (b) `ig_bars = self.budgeted_ig.get_bars(epic, resolution="5m", count=IG_SAMPLE_COUNT)`; leer → `return`. Kein Throttle, der nächste Pass versucht es erneut.
   - (c) `now = _parse(self.now_fn().isoformat())`. Frische-Check auf `ig_bars[-1]` wie bisher. Bei stale: Event + `mark_stale_fn` + Throttle setzen + `return`.
   - (d) `cutoff = now - timedelta(minutes=COMPARATOR_LAG_MIN)`; `complete = [b for b in ig_bars if _parse(b.ts) + timedelta(minutes=5) <= cutoff]`. Leer → Event `divergence_no_comparator` mit `reason="no_complete_bar"`, `return` ohne Throttle.
   - (e) `ig_bar = complete[-1]`, Fenster `[ig_bar.ts, +5 min)`, `yf_bars = list(self.archive.window(epic, "1m", start, end, sources=("yf",)))`. Bei `len(yf_bars) < MIN_YF_BARS` → Event `no_comparator` mit `reason="partial_yf_window"` und `n_yf`, `return` ohne Throttle.
   - (f) `delta = window_return_divergence(ig_bar, yf_bars)`; `None` → Event `no_comparator` mit `reason="zero_open"`, `return` ohne Throttle.
   - (g) **Erst jetzt** `self._last_sample_date[epic] = today`. `delta*100 <= threshold_pct` → Streak 0 + **neues** Event `{"event": "divergence_ok", "epic", "delta", "ig_bar_ts", "n_yf"}`. Sonst `quote_divergence` (bestehende Felder + `ig_bar_ts`) und die Streak-Logik **unverändert** (≥ 2 → `mark_mismatch_fn`).

**P8 `scripts/wiring.py`:**

3. Neue Modul-Funktion, z. B. hinter `_utc_iso`:
   ```python
   def _sampler_due(now: datetime, config: SchedulerConfig) -> bool:
       """Phase 17 B-2: sample only inside the trading window and ≥ 40 min after the open."""
       from scheduler.clock import Phase
       if Clock(config, now_fn=lambda: now).classify(now) is not Phase.WINDOW:
           return False
       local = now.astimezone(ZoneInfo(config.tz))
       open_h, open_m = (int(p) for p in config.window_open.split(":"))
       return local >= local.replace(hour=open_h, minute=open_m, second=0, microsecond=0) + timedelta(minutes=40)
   ```
4. Anker Z. 1095 `            if divergence_sampler is not None:` → `            if divergence_sampler is not None and _sampler_due(_now(), config):`.

**Tests:**
- P12, die 7 Sampler-Tests `test_heartbeat.py:240-410` umstellen:
  - `_FakeIGBroker` liefert `count` 5m-Bars mit dem neuesten Start konfigurierbar (Default `DAY 09:30`); Test-`now` = `DAY 09:35` → Vergleichsbar 09:05, yF-Fenster 09:05–09:09.
  - Die bisherigen Absichten bleiben: Throttle nach Erfolg, nur-yF-Komparator, `no_comparator` typisiert, Mismatch erst nach 2 Divergenzen, Agreement setzt die Streak zurück, stale, Budget-Veto.
  - Neu (+4): `test_no_comparator_does_not_consume_daily_throttle`, `test_partial_yf_window_is_no_comparator`, `test_agreement_emits_divergence_ok`, `test_window_return_divergence_same_window`.
- P8 (+2): `test_sampler_due_false_on_weekend_and_before_open_plus_40`, `test_sampler_due_true_mid_window` (neue Datei `tests/test_wiring_sampler_gate.py`, Muster `test_wiring_schema_floor.py`).
- **AK:** P12 ≥ 153, P8 ≥ 263.

#### B-3 — Promotion-Bridge (D3, P15 + P8)

**P15 `instinct/bridge.py`:**
1. Z. 131–132: nach den Lessons/Rewards zusätzlich `trades = self.db.get_recent_trades(n=self.trades_n)`. Das ist der reservierte Parameter `trades_n=500` (Docstring Z. 91–95 anpassen: „trades for the validator").
2. Z. 146–148 ersetzen:
   ```python
                   decision = self.validator.validate(instinct, trades)
                   self.db.update_instinct_status(int(row_id), decision.decision)
   ```
3. Z. 167–168 → `"evidence_trade_ids_json": list(instinct.evidence_trade_ids),` / `"contradictions_trade_ids_json": list(instinct.contradictions_trade_ids),` (Docstring Z. 156–160 entsprechend).
4. Docstring Z. 22–25 und Z. 177 („called once at scheduler start **and** after each close"): „called **once at scheduler start**; a promotion takes effect from the next restart (exec_cfg is read at construction)" (T18).

**P15 Tests:**
- `_FakeValidator.validate(self, instinct, trades)` gibt `InstinctValidation(decision=self._decision, evidence_count=0, contradiction_count=0, reason="")` zurück — die echte Dataclass, damit die Form nie wieder abweicht.
- `_FakeDB` bekommt `get_recent_trades(self, n=500)` → `[]` (konfigurierbar).
- Neu (+2):
  - `test_after_trade_closed_passes_db_trades_to_validator`.
  - `test_bridge_contract_real_database_and_validator`:
    - Setup: `persistence.Database(tmp/"t.sqlite").run_migrations()` mit 3 CLOSED-Trades per `insert_trade` (Pflichtfelder `deal_id, epic, direction, size, open_level, currency, open_ts, session_date, status`); echter `InstinctValidator()`; Fake-Extractor mit `Instinct(trigger="avoid BUY", domain="entry", status="proposed", evidence_trade_ids=(1, 2, 3))`; dann `after_trade_closed(3)`.
    - Erwartung: genau 1 Zeile, `json.loads(evidence_trade_ids_json) == [1, 2, 3]`, `status == "validated"`, `validated_utc` gesetzt.
    - Dieser **eine** Test fängt alle drei Nahtfehler.

**P8 `scripts/wiring.py` `_build_reward_sink`:**

5. Eigener Extractor-Client:
   - Neue Konstanten oberhalb der Funktion: `_INSTINCT_EXTRACTOR_MAX_TOKENS = 2048` und `_INSTINCT_EXTRACTOR_TIMEOUT_S = 60.0`, mit Kommentar (D3 Punkt 5).
   - Anker Z. 400 `    instinct_extractor = SingleShotInstinctExtractor(llm_client=llm)` → `llm_client=<zweiter Client mit diesen Werten>`. In C-4 läuft der Bau über `_build_llm`; bis dahin ein zweiter `LLMClient(...)` mit `max_tokens=_INSTINCT_EXTRACTOR_MAX_TOKENS, timeout_s=_INSTINCT_EXTRACTOR_TIMEOUT_S`, sonst identisch.
6. Kommentar Z. 945–947 (`On every close the bridge re-runs ``promote()`` + ``load_rules()``,` …) auf T18 korrigieren.

**P8 Test (+1)** in `tests/test_wiring_reward_sink.py`: `test_extractor_has_own_client_with_instinct_limits` → `bridge.extractor._llm.max_tokens == 2048` und `is not sink.brain`-Client (Attributnamen per Lesen von `Brain.__init__` bestätigen).

**AK:** P15 ≥ 128, P8 ≥ 264.

#### B-4 — Abschneiden sichtbar, Meter vor Parse (D4, P4)

**`llm_client.py` `_attempt` (Z. 378–423):**
1. Den Meter-Block Z. 411–422 (`        # Best-effort metering — never let a meter problem break the pick. The` … `log.warning("token_meter.record failed: %s", exc)`) **vor** Z. 400 `        text = _strip_fences(_extract_text(message))` verschieben. Kommentar: „meter first: a response that fails to parse was still billed (Phase 17 B-4)".
2. Den Parse-Fehlerzweig (Z. 401–410) so erweitern, dass vor dem `raise` gilt: `if getattr(message, "stop_reason", None) == "max_tokens": raise LLMResponseError(f"LLM output truncated (stop_reason=max_tokens, max_tokens={self.max_tokens}, model={self.model})")`. Das ist nicht-transient: `ask_candidate` wickelt es als `LLM call failed: …` ab und wiederholt **nicht** (T20). Ein **parsebares** Ergebnis mit `stop_reason == "max_tokens"` bleibt gültig; nur Abschneiden **plus** Parse-Fehler wirft.

**`llm_openai_compat.py` `_attempt` (Z. 242–287):**

3. Analog: nach `body = self._raw_call(payload)` (Z. 258) zuerst metern, dann `choice = body["choices"][0]`; `self.last_finish_reason = choice.get("finish_reason")`. Bei Parse-Fehler und `finish_reason == "length"` → `LLMResponseError("LLM output truncated (finish_reason=length, …)")`. Im Konstruktor `self.last_finish_reason: str | None = None`.

**Tests P4 (+4):**
- `test_llm_client_truncated_unparseable_raises_without_retry` (`_raw_call` einmal gerufen).
- `test_llm_client_meters_even_when_parse_fails` (tmp-Meter: 2 Records nach 2 Fehlversuchen).
- `test_openai_compat_length_truncation_raises_without_retry`.
- `test_openai_compat_meters_even_when_parse_fails`.

**AK:** P4 ≥ 167.

#### B-5 — Monitor-Re-Adoption (D5, T8, P5 + P8)

**P5 `execution/monitor.py`:**
1. Signatur: hinter `    sleep_fn: Callable[[float], None] = _time.sleep,` (Z. 71) ein neues kw-only `entry_at: datetime | None = None,` (Docstring: „the real open time when re-adopting after a restart; default ``now_fn()``").
2. Z. 90 `    entry = now_fn()` → `    entry = entry_at if entry_at is not None else now_fn()`.

**P5 `execution/executor.py`:**

3. Import Z. 59 → `from execution.monitor import _position_present, monitor_position`.
4. Neue Methode **zwischen** `_notify_closed` (endet vor Z. 435 `    # -- Phase-10 (V3) abstain-lessons seam (Decision J) ---------------------`) und diesem Kommentar:
   ```python
       def resume_open_position(self) -> ExecutionResult | None:
           """Phase 17 B-5 (T8): re-adopt a position still open at the broker after a restart.

           ``reconcile_startup`` leaves a *present* reference alone ("the monitor handles it") — but
           the monitor only ever runs inside ``run()`` right after ``place_order``, so after a
           restart nobody watched it (AEX id 26: 6 days open, max_hold never applied). This picks
           the first ``OPEN`` record with a ``deal_id`` the broker still holds, monitors it from its
           **recorded** open time (an already-elapsed max_hold / square-off closes immediately — T8)
           and fires the Phase-7 close seam. ``None`` when nothing needs adopting. The runner calls
           this only in the WINDOW phase (a close needs an open market).
           """
           for ref in self.exec_state.open_references():
               rec = self.exec_state.get(ref) or {}
               deal_id = rec.get("deal_id")
               if rec.get("status") != "OPEN" or not deal_id:
                   continue  # PENDING without a deal_id is reconcile_startup's job
               positions_env = self.broker.get_open_positions()
               if not positions_env.ok:
                   logger.warning("resume: open-positions read failed — not re-adopting %s this cycle", ref)
                   return None
               if not _position_present(positions_env, deal_id):
                   continue  # gone at the broker → reconcile_startup marks it closed (missing)
               plan = OrderPlan(
                   epic=rec["epic"], direction=rec["direction"], size=float(rec["size"]),
                   stop_level=float(rec["stop_level"]), limit_level=float(rec["limit_level"]),
                   deal_reference=ref, currency=self.config.default_currency,
               )
               entry_at = datetime.fromisoformat(str(rec["recorded_at"]).replace("Z", "+00:00"))
               logger.warning("resume: re-adopting open position %s (deal_id=%s, opened %s)", ref, deal_id, rec["recorded_at"])
               try:
                   result = monitor_position(
                       self.broker, self.exec_state, plan, deal_id, self.config,
                       now_fn=self.now_fn, sleep_fn=self.sleep_fn, entry_at=entry_at,
                   )
               except ExecutionAbort as exc:
                   return self._abort(str(exc), plan=plan, deal_id=deal_id)
               self._notify_closed(result)
               return result
           return None
   ```

**P8 `scheduler/runner.py`:**

5. `_ExecutorLike` (Z. 154 `class _ExecutorLike(Protocol):`, Methode Z. 162 `    def run(self) -> Any: ...`): an den Docstring (Z. 155–160) den Satz anhängen „Optionally ``resume_open_position() -> ExecutionResult | None`` (Phase 17 B-5) — read via ``getattr``, so a fake without it keeps the runner bit-identical."
6. WINDOW-Zweig, Anker Z. 386–388 `        elif phase is Phase.WINDOW:` / `            self._warm_session()` / `            self._maybe_reconcile(state, now)`. **Direkt danach** einfügen:
   ```python
               # Phase 17 B-5: a position left open by a restart is monitored first (T8).
               resume = getattr(self._executor, "resume_open_position", None)
               resumed = resume() if callable(resume) else None
               if resumed is not None:
                   state = self._state_store.record_cycle(state, resumed)
                   self._clock.sleep(self._cycle_interval_s)
                   return
   ```

**Tests:**
- P5 (+5):
  - `test_monitor_entry_at_applies_max_hold_from_recorded_open`.
  - `test_resume_monitors_present_open_record_from_recorded_at`.
  - `test_resume_returns_none_when_position_missing_at_broker`.
  - `test_resume_skips_pending_without_deal_id`.
  - `test_resume_closes_immediately_when_max_hold_elapsed` (erwartet `TIME_STOP` + `close_position` genau einmal).
- P8 (+2): `test_window_runs_resumed_position_instead_of_research` (Fake-Executor mit `resume_open_position` → Research-Fake nie gerufen) und `test_window_without_resume_method_is_unchanged`.

**AK:** P5 ≥ 195, P8 ≥ 266. Den Live-Beweis liefert die Re-Adoption-Probe in E-4.

#### B-6 — Breaker Worst-Case (D6, T9, P8)

**`scripts/wiring.py`:**
1. Neue Modul-Funktion:
   ```python
   def _realized_pnl_today(conn: Any, session_date: str) -> float:
       """Today's P&L for the daily-loss breaker — booked P&L **plus the worst case of every OPEN row**.

       Phase 17 B-6 (T9): a broker-closed trade stays ``status='OPEN'`` with ``profit_loss`` NULL until
       IG settles (1 h 06 – 1 h 54 measured), which left the breaker blind to a fresh stop-out. Each
       OPEN row now counts as ``-initial_risk`` (the planned stop loss). An OPEN row without
       ``initial_risk`` cannot be bounded → raise; ``AutoConfirm`` treats a raising reader as
       fail-closed (blocks + logs critical).
       """
       row = conn.execute(
           "SELECT COALESCE(SUM(CASE WHEN status='OPEN' THEN -initial_risk ELSE profit_loss END), 0.0), "
           "COALESCE(SUM(status='OPEN' AND initial_risk IS NULL), 0) "
           "FROM trade_outcomes WHERE session_date = ? AND (profit_loss IS NOT NULL OR status='OPEN')",
           (session_date,),
       ).fetchone()
       if row is not None and row[1]:
           raise RuntimeError("OPEN trade without initial_risk — the breaker cannot bound today's loss")
       return float(row[0]) if row is not None else 0.0
   ```
2. Closure Z. 1009–1016 (Anker `    def realized_pnl_today(session_date: str) -> float:`) → Rumpf `return _realized_pnl_today(db.conn, session_date)`; Docstring „(Contract E + Phase 17 B-6 worst case)".
- **Tests P8 (+3)**, neue Datei `tests/test_wiring_breaker.py` (echte `persistence.Database(":memory:")` + `run_migrations()`):
  - `test_booked_pnl_only_when_no_open_rows`.
  - `test_open_row_counts_as_minus_initial_risk`.
  - `test_open_row_without_initial_risk_raises`.
- **AK:** P8 ≥ 269.

#### B-7 — Abstain-Naht (D7, P8)

**`scripts/wiring.py`:**
1. Z. 758–760: `def on_no_trade(self, cycle_outcome: Any) -> None:` → `-> Any:`; `            inner.on_no_trade(cycle_outcome)` → `            record_id = inner.on_no_trade(cycle_outcome)`. Am Ende der Methode (nach dem `try/except`) `            return record_id`. Docstring Z. 747–753: den Satz „locked ``AbstainSink.on_no_trade(cycle_outcome) -> None`` contract" ersetzen durch „passes the sink's ``record_id`` through — the executor links it into ``decision_context.abstain_record_id`` (3 669/3 669 NULL before Phase 17 B-7)".
2. Reihenfolge Z. 993–995 umdrehen: `abstain_sink = _enrich_abstain_detail(_observed_abstain_sink(_build_abstain_sink(config, paper_engine=paper_engine), config.observability_path), research)`. Die Anreicherung (und ab C-5 das `llm_unavailable`-Flag) muss **vor** der Klassifikation des Events liegen.
- **Tests P8 (+2)**, neue Datei `tests/test_wiring_abstain_seam.py`:
  - `test_observed_sink_returns_inner_record_id`.
  - `test_enriched_outer_wrapper_feeds_observed_classification`.
- **AK:** P8 ≥ 271; live ab Tag 1 `abstain_record_id IS NOT NULL` für jede neue NO_TRADE-Zeile (E-3).

#### B-8 — Paper-Logstufen (D8, T11/E4, P10)

`abstain_lessons/paper.py` Z. 321 (`logger.critical("PaperDebateCaller.request_pick failed: %s", exc)`), Z. 386 (`logger.critical("PaperEngine.on_debate_abstain failed: %s", exc)`), Z. 465 (`logger.critical("PaperEngine.open_scheduled_pairs failed for %s: %s", epic, exc)`), Z. 701–703 (`logger.critical(` / `"PaperTradeTracker reflect failed for record %s: %s", record_id, exc`) → jeweils `logger.warning(`.

Jede Stelle bekommt den Kommentar `# Phase 17 B-8 (E4): external-dependency failure (quote/LLM) — WARNING; an LLM outage is reported once by research_tick (LLM_UNAVAILABLE).`. **Nicht** ändern: Z. 563 und 685 (lokale Fehler).

- **Tests P10 (+1):** `test_get_price_failure_logs_warning_not_critical` (`caplog`, `PaperEngine.on_debate_abstain` mit werfendem `quote_fetch`).
- **AK:** P10 ≥ 166.

#### B-9 — Stop-Timeout (D13, T10, P16-Unit)

- `phase16_activation/systemd/tradingbot-scheduler.service:32`, Anker `SuccessExitStatus=143` → darunter `TimeoutStopSec=360`.
- Kommentarzeile darüber: `# Phase 17 B-9: SIGTERM is honoured after the running cycle sleep (≤ 300 s) — 90 s default killed every stop (09-23, 09-30, 10-11).`
- **Test:** `bash scripts/install_units.sh --verify` exit 0. Die Installation läuft erst in E-3, der Operator braucht dafür `daemon-reload`.

#### B-10 — Discovery-Beleg + Wrapper-Text (D12, P14)

1. `source_registry/run.py` `run_once`, an **allen drei** Rückgabestellen jeweils direkt **vor** der `return`-Zeile:
   - unarmed: Z. 205 `            result = CycleResult(ts_utc=ts_utc, armed=False, stale_count=0, rows_written=0)` … Z. 207 `            logger.debug("discovery cycle skipped: not armed")` → vor Z. 208 `            return result`;
   - nothing stale: Z. 212 `            result = CycleResult(ts_utc=ts_utc, armed=True, stale_count=0, rows_written=0)` … Z. 214 `            logger.debug("discovery cycle skipped: nothing stale (ttl=%d days)", self._profile_ttl_days)` → vor Z. 215 `            return result`;
   - Ende: Z. 247 `        result = CycleResult(` … → vor Z. 255 `        return result`.

   Die eingefügte Zeile:
   - `logger.info("discovery cycle %s: armed=%s stale=%d rows_written=%d errors=%d", result.ts_utc, result.armed, result.stale_count, result.rows_written, len(result.errors))`.
   - Das ist eine Zeile pro Stunde (`interval_s=3600`, Z. 169). Der Zeitstempel steckt **im Text**, weil `basicConfig` ohne `asctime` loggt (Z. 336).
   - Die zwei `logger.debug(...)`-Zeilen bleiben.
2. `scripts/run_discovery.sh:46` Anker `printf '%s [run_discovery] starting daemon from %s (unarmed ⇒ noop)...\n' \` → `(noop unless ARMED)`. Das K1-Muster `\[run_discovery\] starting daemon` (`autonomy_report.py:153`) bleibt treffend.
- **Tests P14 (+1):** `test_run_once_logs_discovery_cycle_line_with_ts` (`caplog`, Level INFO, Text enthält `discovery cycle 20` und `armed=`).
- **AK:** P14 ≥ 62. **Block-B-Sweep Σ ≥ 1992** (+28: P1 +1 · P4 +4 · P5 +5 · P8 +10 · P10 +1 · P12 +4 · P14 +1 · P15 +2).

---

### Block C — LLM-Austausch (Scheduler gestoppt)

#### C-1 — `phase8_scheduler/scheduler/llm_profiles.py` (NEU, stdlib-only)

```python
"""Phase 17 C-1 — which LLM serves which role (T4/T5/T16). Pure data + two pure functions.

Imported by the composition root (``scripts/wiring.py``) and the config check; imports nothing
cross-phase. A profile maps every role to a RoleSpec; ``model``/``max_tokens``/``timeout_s`` =
``None`` keep the phase config's own value, so the "anthropic" profile is bit-identical to the
pre-Phase-17 wiring.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

LLM_ROLES: tuple[str, ...] = ("research", "debate", "lesson", "instinct", "reflect", "paper_debate")


@dataclass(frozen=True)
class ProviderSpec:
    kind: str                           # "anthropic" | "openai_compat"
    base_url: str | None = None
    api_key_service: str | None = None
    api_key_username: str | None = None


@dataclass(frozen=True)
class RoleSpec:
    provider: str
    model: str | None = None
    max_tokens: int | None = None
    timeout_s: float | None = None


PROVIDERS: dict[str, ProviderSpec] = {
    "anthropic": ProviderSpec(kind="anthropic"),
    # Abo-Kontingent (Nikinger 2026-10-17). Endpoint + model id: verify with the C-7 smoke (§9).
    "minimax": ProviderSpec(kind="openai_compat", base_url="https://api.minimax.io/v1",
                            api_key_service="trading-bot-minimax-bot", api_key_username="api_key"),
}

_ANTHROPIC = RoleSpec(provider="anthropic")
# max_tokens/timeout: room for a reasoning model's <think> block (C-3 strips it) — C-7 measures.
_M3 = RoleSpec(provider="minimax", model="MiniMax-M3", max_tokens=4096, timeout_s=90.0)

LLM_PROFILES: dict[str, dict[str, RoleSpec]] = {
    "anthropic": {role: _ANTHROPIC for role in LLM_ROLES},
    "research_m3": {**{role: _ANTHROPIC for role in LLM_ROLES}, "research": _M3},
    "all_m3": {role: _M3 for role in LLM_ROLES},
}


def role_spec(profile: str, role: str) -> RoleSpec: ...           # KeyError-frei: ValueError mit Liste
def check_llm_profile(profile: str, *, pricing: Mapping[str, tuple[float, float]],
                      default_models: Mapping[str, str],
                      exempt_models: tuple[str, ...]) -> None: ...
```

Signatur mit Ausnahmeliste: `check_llm_profile(profile, *, pricing, default_models, exempt_models: tuple[str, ...])`. Sie wirft `ValueError` in vier Fällen:
- unbekanntes Profil oder unbekannter Provider;
- eine `claude-*`-ID an einen Provider mit `kind != "anthropic"`;
- ein aufgelöstes Modell (`spec.model or default_models[role]`) **ohne** Preiszeile;
- ein Modell eines Nicht-Anthropic-Providers, das **nicht** in `exempt_models` steht.

Der vierte Fall gibt es, weil die Modell-ID an **drei** Stellen als Literal steht (`_M3.model` hier, Preiszeile P4 `models.py`, `SchedulerConfig.budget_exempt_models`). Eine Umbenennung, die die Ausnahmeliste vergisst, würde Research still wieder unter den Cap stellen. So fällt der Fehler beim Start laut auf (T7).

**Tests P8 (+7)** `tests/test_llm_profiles.py`:
- `test_anthropic_profile_keeps_phase_defaults`.
- `test_research_m3_routes_only_research_to_minimax`.
- `test_all_m3_routes_every_role_to_minimax`.
- `test_check_rejects_unknown_profile`.
- `test_check_rejects_claude_on_foreign_provider`.
- `test_check_rejects_model_without_pricing`.
- `test_check_rejects_non_exempt_foreign_model`.

Ein siebter Test `test_check_accepts_shipped_profiles` (echte `ResearchConfig().pricing_usd_per_mtok` + echte Default-Modelle) kommt erst im **C-3-Commit** dazu: er braucht die neue Preiszeile, und ein Commit darf keinen roten Test hinterlassen.

#### C-2 — `SchedulerConfig` (P8)

`scheduler/config.py`, unter Z. 140 (Anker `    daily_token_budget: int | None = 300_000  # Phase 16 C3 …`):

```python
    # Phase 17 C-2 (T5/T17): LLM routing profile (scheduler/llm_profiles.py). A code default is the
    # only restart-proof switch (systemd ExecStart passes no flags). Flip 1 → "research_m3" in its
    # own commit after the demo smoke (C-7); Flip 2 → "all_m3" only on a Nikinger go (C-8).
    llm_profile: str = "anthropic"
    # Phase 17 D-1 (T7): calls of these models do NOT count against daily_token_budget (MiniMax
    # Abo-Kontingent — Nikinger 2026-10-17: "für alle MiniMax-M3-Calls unlimited, danach messen").
    budget_exempt_models: tuple[str, ...] = ("MiniMax-M3",)
```
- `__post_init__` (Z. 229, „never raises") **nicht** anfassen. Die Prüfung läuft in `build_scheduler` (C-4).
- **Test P8 (+1):** `test_config` Defaults der zwei Felder.

#### C-3 — OpenAI-Compat-Härtung + Preiszeile (P4)

**`research/llm_openai_compat.py`:**
1. Docstring Z. 1–8 („Cold, dormant fallback … **Not wired into any live path.**") → „OpenAI-compatible client — wired via ``phase8_scheduler/scheduler/llm_profiles.py`` since Phase 17 (MiniMax M3 for research, T4/T5); OpenRouter stays the default endpoint for ``scripts/openrouter_smoke.py``". Den Abschnitt „Switch instructions" (Z. 21–48) durch einen Verweis auf `_build_llm` ersetzen.
2. Konstruktor: neues kw-Arg `api_key_username: str = _KEYRING_USERNAME,` (nach `api_key_service`), `self.api_key_username = api_key_username`; Z. 170 → `keyring.get_password(self.api_key_service, self.api_key_username)` (Fehlermeldung Z. 172–176 nennt beide).
3. `_attempt`, nach dem B-4-Umbau:
   - (a) `_raw_call` in `try/except _HTTPStatusFault`: bei `status_code == 400` **und** `"response_format" in payload` einmal ohne `response_format` erneut senden (`log.info`), sonst re-raise. Das entspricht `LLMClient._attempt:388-398` und verbraucht nicht den transienten Retry.
   - (b) Vor `_strip_fences`: `<think>`-Blöcke entfernen. Hilfsfunktion `_strip_think(text: str) -> str` mit `re.sub(r"(?s)<think>.*?</think>", "", text).strip()`. Steht danach noch `"<think>"` im Text (unterminiert) → `LLMResponseError("unterminated <think> block (finish_reason=…, max_tokens=…)")` ohne Retry.
   - (c) Fehlermeldungen Z. 235/237 `"OpenRouter call failed …"` → `"OpenAI-compat call failed (base_url=…)…"`.

**`research/models.py:539`:** unter `    "claude-haiku-4-5-20251001": (1.0, 5.0),` die Zeile `    "MiniMax-M3": (0.0, 0.0),  # Phase 17 C-3: Abo-Kontingent — Grenzkosten 0 (T7); keeps token_meter from warning on every call`.

**Tests P4 (+4):**
- `test_think_block_is_stripped_before_json_parse`.
- `test_unterminated_think_raises_without_retry`.
- `test_400_with_response_format_retries_once_without_it`.
- `test_custom_api_key_username_is_used`.

**Test P8 (+1):** `test_check_accepts_shipped_profiles` (aus C-1 nachgezogen; mit `exempt_models=SchedulerConfig().budget_exempt_models`).

**AK:** P4 ≥ 171, P8 ≥ 280.

#### C-4 — Eine Bau-Funktion für alle Clients + Profil-Check + Preflight + Startzeile (P8)

**`scripts/wiring.py`:**
1. Neue Modul-Funktion `_build_llm(role, llm_profile, *, default_model, max_tokens, temperature, timeout_s, research_config=None, cache_system=False)`:
   - `spec = role_spec(llm_profile, role)`, `provider = PROVIDERS[spec.provider]`.
   - `model = spec.model or default_model`, analog `max_tokens`/`timeout_s`.
   - `kind == "anthropic"` → `LLMClient(model, api_key=research.credentials.get_credential("anthropic_api_key"), max_tokens, temperature, timeout_s, token_meter_path=str(_USAGE_LOG), config=research_config or ResearchConfig(), cache_system=cache_system)`.
   - Sonst `OpenAICompatLLMClient(model, base_url=provider.base_url, api_key_service=provider.api_key_service, api_key_username=provider.api_key_username, timeout_s, max_tokens, temperature, token_meter_path=…, config=…, cache_system=cache_system)`.
   - Docstring: die **eine** Stelle (T16); mit dem Profil `anthropic` bit-identisch zu den alten Aufrufen.
2. Neue Modul-Funktion `_debate_config(llm_profile)`:
   - `DebateConfig()`. Hat die Debate-Rolle ein `model`, dann `dataclasses.replace(cfg, model_bull=m, model_bear=m, model_judge=m)` plus bei gesetztem `max_tokens` `max_tokens_agent=…, max_tokens_judge=…`.
   - Begründung im Docstring: `ask_agent` überschreibt `client.model` je Rolle aus dieser Config (§5).
3. Die 6 Stellen + 1 neue umstellen. Die Signaturen bekommen ein kw-only `llm_profile: str = "anthropic"`, wo kein `config` vorliegt; der Default hält die bestehenden Tests unverändert.

   | Stelle (Anker) | Rolle | Werte |
   |---|---|---|
   | `_build_research` Z. 313 `    llm = LLMClient(` | `research` | `default_model=config.model, max_tokens=config.max_tokens, temperature=config.temperature, timeout_s=config.timeout_s, research_config=config` |
   | `_make_debate_runner._build` Z. 344 | `debate` | `cfg = _debate_config(llm_profile)`; `default_model=cfg.model_judge, max_tokens=cfg.max_tokens_judge, temperature=cfg.temperature_judge, timeout_s=research_config.timeout_s, research_config=research_config, cache_system=True` |
   | `_build_reward_sink` Z. 390 | `lesson` | `default_model=cfg.lesson_model, max_tokens=cfg.lesson_max_tokens, temperature=cfg.lesson_temperature, timeout_s=cfg.lesson_timeout_s` |
   | `_build_reward_sink` (B-3-Client) | `instinct` | `default_model=cfg.lesson_model, max_tokens=_INSTINCT_EXTRACTOR_MAX_TOKENS, temperature=cfg.lesson_temperature, timeout_s=_INSTINCT_EXTRACTOR_TIMEOUT_S` |
   | `_build_abstain_sink` Z. 470 | `reflect` | `config.llm_profile`; Lesson-Werte |
   | `_build_paper_engine` Z. 527 | `paper_debate` | `default_model=dcfg.model_judge, max_tokens=dcfg.max_tokens_judge, temperature=dcfg.temperature_judge, timeout_s=dcfg.wall_clock_timeout_s` |
   | `_build_paper_tracker` Z. 685 | `reflect` | wie `_build_abstain_sink` |

   Die dann ungenutzten lokalen Importe `LLMClient` / `get_credential` in diesen Funktionen entfernen.
4. `build_scheduler`, vor `research = _build_research(…)` (Anker `    research = _build_research(` Z. ~935):
   - `check_llm_profile(config.llm_profile, pricing=ResearchConfig().pricing_usd_per_mtok, default_models={...}, exempt_models=config.budget_exempt_models)` mit den Defaults `research: ResearchConfig().model`, `debate`/`paper_debate: DebateConfig().model_judge`, `lesson`/`instinct`/`reflect: RewardConfig().lesson_model`.
   - Den drei Buildern `llm_profile=config.llm_profile` übergeben.
5. `preflight_fn` (Z. 1178–1197), nach Punkt 3: Punkt 4 „every non-anthropic provider of the active profile has its key". Ablauf: `import keyring`; für jeden Provider `{role_spec(config.llm_profile, r).provider for r in LLM_ROLES}` mit `kind != "anthropic"` und `not keyring.get_password(p.api_key_service, p.api_key_username)` → `RuntimeError` mit dem exakten Seed-Befehl (`python scripts/store_minimax_key.py --service … --username …`).

**`scheduler/run.py:206-212`:** Format `"starting scheduler daemon (account=%s, max_trades=%d, daily_loss_cap=%s, cycle=%dmin, llm_profile=%s)."` + `config.llm_profile`. Die Report-Parser bleiben treffend (§5 Start-Zeile).

**Tests P8:**
- `tests/test_wiring_reward_sink.py`: die Fixture `no_keyring` stubbt **zusätzlich** `research.credentials` (`monkeypatch.setitem(sys.modules, "research.credentials", SimpleNamespace(get_credential=…))`). `_build_llm` liest dort; ohne Stub läse der Test den echten Keyring (§8).
- Neu (+4) `tests/test_wiring_llm_routing.py`:
  - `test_build_llm_anthropic_profile_is_bit_identical_for_research` (Klasse `LLMClient`, `model == "claude-sonnet-4-6"`, `max_tokens == 1024`).
  - `test_build_llm_research_m3_returns_openai_compat_minimax`.
  - `test_debate_config_all_m3_renames_all_three_roles`.
  - `test_debate_config_anthropic_is_default`.

**AK:** P8 ≥ 284. `rg -n "\bLLMClient\(" phase8_scheduler/scripts/wiring.py` und `rg -n "OpenAICompatLLMClient\(" phase8_scheduler/scripts/wiring.py` → je genau 1 Treffer (beide in `_build_llm`). Das `\b` ist nötig, sonst trifft das erste Muster auch `OpenAICompatLLMClient(`.

#### C-5 — `LLM_UNAVAILABLE` (D9, T11/E7, P4 + P8 + P10)

1. **P4 `research/research.py`:** `self.last_llm_error: bool = False` neben `self.last_abort_detail` (Z. 154) und Reset neben Z. 175. Im `except LLMResponseError as exc:` (Z. 200) vor dem `return` `self.last_llm_error = True`. Kommentar: „display/observability only — gates nothing (root rule 3)".
2. **P8 `scheduler/research_tick.py`:**
   - Unter Z. 89 `REASON_LLM_UNAVAILABLE: str = "LLM_UNAVAILABLE"  # Phase 17 C-5 (E7): research.run() abstained on an LLM error` und `_LLM_UNAVAILABLE_ALERT_STREAK: int = 3`.
   - `__init__` (Z. 156–163, nach `        self._now_fn = now_fn or (lambda: datetime.now(timezone.utc))`): `self._llm_fail_streak = 0`.
   - Pick-Zweig: nach Z. 210 `        if candidates:` / Z. 211 `            state.last_no_trade_reason = None` → `            self._llm_fail_streak = 0`.
   - Abstain-Zweig, Anker Z. 219 `        state.last_no_trade_reason = REASON_LLM_ABSTAIN`, Z. 223 `        logger.info("research tick: abstain (no candidate, reason=%s).", REASON_LLM_ABSTAIN)`, Z. 225 `            picked=False, n=0, reason=REASON_LLM_ABSTAIN,`. Neu:
     - `getattr(self._research, "last_llm_error", False)` → `reason = REASON_LLM_UNAVAILABLE`, Streak +1, genau bei `== 3` ein `logger.critical("research tick: LLM unavailable for %d consecutive ticks — last error: %s", …, abort_detail)`;
     - sonst Streak 0, `reason = REASON_LLM_ABSTAIN`;
     - `reason` an allen drei Ankern verwenden.
   - **Begriff (verbindlich):** `LLM_UNAVAILABLE` = **jeder** nicht behebbare LLM-Fehler, also auch ein B-4-Abschneiden. Ein dauerhaft abschneidendes Modell ist für Entscheidungen genauso ausgefallen; der Alarm nach 3 Ticks ist dort gewollt.
   - Die Unterscheidung „abgeschnitten" vs. „nicht erreichbar" steckt im `detail`/Log-Text (`LLM output truncated` bzw. `HTTP …`). D-2 und der Shakedown-Bericht zählen beides getrennt per `grep -c`.
3. **P8 `scripts/wiring.py` `_enrich_abstain_detail`** (Z. 736–742): im `research_empty`-Zweig zuerst `if getattr(research, "last_llm_error", False):` → `cycle_outcome = {**cycle_outcome, "llm_unavailable": True, "detail": getattr(research, "last_abort_detail", None) or "LLM error"}`, sonst die bestehende `reasoning`-Logik.
4. **P10 `abstain_lessons/models.py`:**
   - `AbstainReason` um `REASON_LLM_UNAVAILABLE = "reason_llm_unavailable"`.
   - Docstring Z. 33 „The 12 reasons" → „13".
   - `classifier.py:64-68`: im `research_empty`-Zweig `reason = REASON_LLM_UNAVAILABLE if cycle_outcome.get("llm_unavailable") is True else REASON_NO_CANDIDATES`.
   - Die Tabelle `abstain_records.reason` hat **keinen** CHECK (Migration 005 geprüft), es braucht also keine Migration.

**Tests:**
- P4 (+1): `test_llm_error_sets_last_llm_error_and_run_resets_it`.
- P8 (+3):
  - `test_llm_error_sets_llm_unavailable_reason`.
  - `test_three_consecutive_llm_errors_log_one_critical`.
  - `test_pick_resets_llm_fail_streak`.
- P10 (+1): `test_research_empty_with_llm_unavailable_classifies_own_reason`.
- P10 `test_models.py:47` `== 12` → `== 13`. **Erwarteter** Rot-Test, kein Bug (§8).

**AK:** P4 ≥ 172, P8 ≥ 287, P10 ≥ 167.

#### C-6 — Key-Skript + Smoke-Skript (root + P4)

1. **`scripts/store_minimax_key.py`:**
   - `main()` → `main(argv: list[str] | None = None)`, `parser.parse_args(argv)`.
   - Neue Args `--service` (Default `SERVICE_NAME`) und `--username` (Default `USERNAME`); alle drei Pfade (`--status`, `--delete`, Setzen) nutzen `args.service`/`args.username`.
   - Docstring um den Bot-Key-Aufruf ergänzen (`--service trading-bot-minimax-bot --username api_key`).
   - **Test root (+1):** `tests/test_store_minimax_key.py::test_status_honours_service_and_username` (monkeypatched `keyring.get_password`).
2. **`phase4_research/scripts/openrouter_smoke.py`:**
   - Args `--base-url` (Default `https://openrouter.ai/api/v1`), `--key-service` (Default `openrouter`), `--key-username` (Default `api_key`), `--max-tokens` (Default 1024), `--timeout-s` (Default 60).
   - Diese an `OpenAICompatLLMClient(...)` (Z. 117) durchreichen.
   - Ausgabe zusätzlich `finish_reason=<client.last_finish_reason>` und `latency_s=<…>` (`time.monotonic`).
   - Mit `--show-raw` die ersten 400 Zeichen der Rohantwort nach stderr. Dafür das letzte `content` im Client als `self.last_raw_text` mitführen (C-3-Commit, eine Zeile).
   - Kein Test (Operator-Skript, nicht collected — wie heute).

#### C-7 — Operator: Bot-Key + M3-Smoke → Flip 1

1. **Nikinger:** `phase1_broker_wrapper/.venv/bin/python scripts/store_minimax_key.py --service trading-bot-minimax-bot --username api_key`. Der Key kommt aus der MiniMax-Konsole, die Eingabe ist verdeckt.
2. **Nikinger:** Smoke, Kosten 1 Call aus dem Abo:
   ```bash
   phase1_broker_wrapper/.venv/bin/python phase4_research/scripts/openrouter_smoke.py \
     --model MiniMax-M3 --base-url https://api.minimax.io/v1 \
     --key-service trading-bot-minimax-bot --key-username api_key \
     --max-tokens 4096 --timeout-s 90 --show-raw
   ```
   Erwartung: `PASS (pick)` oder `PASS (valid abstain)`, `finish_reason=stop`, Tokens und Latenz in den Phasenkopf.
   - FAIL → **nicht flippen**. Diagnose nach §8 (400 / truncated / 401 / unterminated think), dann ggf. `max_tokens`/`timeout_s` in `_M3` anpassen (eigener Commit) und den Smoke wiederholen.
   - Verlangt der Endpoint eine **andere Modell-ID** (z. B. mit Suffix), betrifft die Änderung **drei** Stellen in einem Commit: `_M3.model` (`scheduler/llm_profiles.py`), die Preiszeile (`phase4_research/research/models.py`) und `SchedulerConfig.budget_exempt_models` (`scheduler/config.py`). `check_llm_profile` meldet eine vergessene Stelle beim Start (C-1).
3. **Exec:** **Flip-1-Commit allein** — `config.py` `llm_profile: str = "research_m3"` + Test-Pin. Commit-Message: `phase17+phase8: flip research to MiniMax M3 (Flip 1, after demo smoke PASS <ts>)`.

#### C-8 — Flip 2 (`all_m3`) — **gegated** (T5)

- Nur nach Nikinger-Go in E-5.
- Dann eigener Commit `llm_profile: str = "all_m3"`, Restart, **1 Handelstag** Shakedown auf `all_m3`, Auswertung mit Report v5 (`--expect-llm-profile all_m3`).
- Kriterien und Abbruchregel dieses Tages stehen **vorab** im Abschnitt „§F2 Flip-2-Tag" der Shakedown-Vorregistrierung (E-2). Sie ist vor dem ersten Restart committet, damit gilt T23 auch für diesen bedingten Lauf.
- Abbruch → Revert-Commit, wenn eine dieser Schwellen erreicht ist:
  - ≥ 3 × `DebateLLMError`;
  - ≥ 3 × `LLM output truncated`;
  - `LLM_UNAVAILABLE`-CRITICAL.
- Ohne Go: nichts tun, Prereg v5 pinnt `research_m3`.
- **Block-C-Sweep Σ ≥ 2015** (+23: P4 +5 · P8 +16 · P10 +1 · root +1).

---

### Block D — Token-Budget (T7)

#### D-1 — Budget-Ausnahme an allen drei Zählstellen (D10, P8 + E-1)

1. **`scheduler/budget.py:180-182`**, Anker `            if _record_local_date(rec.get("ts"), self._tz) == today:` — davor:
   ```python
               if rec.get("model") in self._config.budget_exempt_models:
                   continue  # Phase 17 D-1 (T7): Abo-Kontingent — measured (llm_usage.json), not capped
   ```
   Den Docstring von `consumed_today` um den Satz ergänzen.
2. **`webui/api.py:289-307`**, Anker Z. 294 `            if _record_local_date(rec.get("ts"), tz) == today:` / Z. 295 `                tokens += _record_tokens(rec)`: Z. 295 ersetzen durch ein `if rec.get("model") in cfg.budget_exempt_models: exempt_tokens += _record_tokens(rec)` / `else: tokens += _record_tokens(rec)`. `exempt_tokens = 0` steht neben `tokens = calls = 0` (Z. 289). Die Kosten- und Call-Summen zählen weiter alle Records. Neues Feld `"exempt_tokens": exempt_tokens` im Return. `app.js` bleibt unverändert, das Feld steht für `curl` und Report bereit.
3. **Report:** E-1 (gleiche Quelle `SchedulerConfig().budget_exempt_models`).
- **Tests P8 (+3):**
  - `test_budget_ignores_exempt_model_records`.
  - `test_budget_counts_non_exempt_records`.
  - `test_webui_token_usage_separates_exempt_tokens`.
- **AK:** P8 ≥ 290; Σ ≥ 2018.

#### D-2 — Entscheidungspunkt K6 (Nikinger, nach dem Shakedown, **kein Code**)

E-5 legt dem Nikinger die Shakedown-Messung vor:
- M3-Tokens/Tag und Calls/Tag;
- Anthropic-Tokens/Tag;
- `LLM_UNAVAILABLE`-Zählung;
- `truncated`-Zählung;
- Research-PASS-Quote im Vergleich zu 10-12…10-16.

Der Nikinger wählt die K6-Einheit für Prereg v5:

| Option | Inhalt |
|---|---|
| (a) | Nicht-Ausnahme-Tokens < 300 k vor 17:30 — **Default, wenn keine Antwort** |
| (b) | Euro-Cap |
| (c) | Call-Quote für das Abo |
| (d) | K6 entfällt für Ausnahme-Modelle |

---

### Block E — Test-Fundament

#### E-1 — Report v5 (D11, T21, P16 `scripts/autonomy_report.py`)

Alles hinter `--prereg {v4,v5}`. Default `v4` bleibt **verdikt-identisch**; die 15 bestehenden Tests pinnen das.

Anker (die `def`-Zeilen, e19c178):
- `def llm_usage_per_day(` Z. 369
- `def critical_count_after_opens(` Z. 428
- `def extract_caps_from_scheduler_log(scheduler_log: Path) -> dict[str, Any]:` Z. 480
- `def evaluate_k2(` Z. 633
- `def evaluate_k5(` Z. 771
- `def evaluate_k6(` Z. 804
- `def evaluate_k7(` Z. 858
- `def _build_day_report(` Z. 990
- `def _build_summary_report(` Z. 1045
- `def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:` Z. 1111
- `def main(argv: list[str] | None = None) -> int:` Z. 1135

Die neuen Evaluatoren stehen **hinter** `evaluate_k8` (`def evaluate_k8(` Z. 903) und vor `_iter_trading_days`.

1. **`_parse_args`** (Z. 1111–1133):
   - `--prereg` (choices `v4`, `v5`, Default `v4`).
   - `--journal-file PATH` (optional).
   - `--expect-llm-profile STR` (optional).
   - `--summary`-Hilfetext von „7" auf „PASS criteria".
2. **`llm_usage_per_day`** (Z. 369–425): kw-Arg `exempt_models: tuple[str, ...] = ()`.
   - Ausnahme-Records zählen nicht in `tokens`/`exhausted_at`, sondern in die **neuen** Keys `exempt_tokens`/`exempt_calls`.
   - Default `()` ⇒ v4 identisch.
3. **Neue Evaluatoren** (Signaturen wie die bestehenden, `CriterionResult`, Verdikt `NA` wo kein Beleg möglich):

   | Funktion | Regel (v5) | Quelle |
   |---|---|---|
   | `count_discovery_cycles_per_day(log: Path) -> dict[date, int]` | Regex `discovery cycle (?P<ts>\d{4}-\d{2}-\d{2}T[\d:.]+Z):` → Berlin-Tag | `run_discovery.log` (B-10) |
   | `evaluate_k2_v5(state_dir, bars_db, from_day, to_day)` | **jeder** Handelstag: Scheduler-Health ≥ 1 **und** Recorder-Bars ≥ 1 **und** Discovery-Zyklen ≥ 1; WebUI bleibt „operator-gesichtet" (Hinweis) | behebt `:1064` |
   | `evaluate_k6_v5(usage_json, from_day, to_day, *, threshold, exempt_models)` | Nicht-Ausnahme-Tokens nie ≥ `threshold` vor 17:30; `measured` trägt `exempt_tokens_per_day` | `SchedulerConfig().budget_exempt_models` (Import `from scheduler.config import SchedulerConfig`) |
   | `evaluate_k7_v5(…, expected_llm_profile)` | Caps wie v4 **und** jede Start-Zeile im Fenster trägt `llm_profile=<expected>` | Start-Zeile (C-4) |
   | `evaluate_k9(journal_file, from_day, to_day, *, max_per_day=10)` | Zeilen mit `Scheduled restart job` je Berlin-Tag ≤ 10; `journal_file is None` → `NA` | Operator-Export (E-4) |
   | `evaluate_k10(trading_db, scheduler_log, from_day, to_day)` | 0 CLOSE im Fenster → `NA`; sonst **0** Zeilen `CRITICAL instinct.bridge` **und** **0** `extractor returned ok=False` **und** jede im Fenster angelegte `instincts`-Zeile hat `evidence_trade_ids_json IS NOT NULL` | Log + DB |
   | `evaluate_k11(health_jsonl, from_day, to_day)` | **jeder** Handelstag ≥ 1 Event `divergence_ok` oder `quote_divergence` | `research_health.jsonl` (B-2) |

4. **K5** bleibt in v5 die v3-Regel (alle CRITICALs ≤ 5 je 24 h nach OPEN, T11). Zusätzlich das Feld `by_logger` je Trade in `measured`:
   - `critical_count_after_opens(..., by_logger: bool = False)`; Regex `CRITICAL (?P<logger>\S+):`.
   - Die SQL bekommt `deal_id` dazu, `deal_related` zählt Zeilen mit der deal_id (A6-Quell-Definition, nur berichtet).
5. **`_build_day_report` / `_build_summary_report`**: kw-Arg `prereg: str = "v4"`.
   - Bei `v5`: Kriterien `"2"`, `"6"`, `"7"` durch die v5-Varianten ersetzen, `"9"`, `"10"`, `"11"` ergänzen und `"5"` mit `by_logger=True`.
   - `main` reicht `prereg`, `journal_file`, `expect_llm_profile` durch.
- **Tests P16 (+7):**
  - `test_v4_default_criteria_unchanged`.
  - `test_k2_v5_requires_discovery_cycle_every_day`.
  - `test_k6_v5_ignores_exempt_model_tokens`.
  - `test_k7_v5_fails_on_profile_change_in_window`.
  - `test_k9_counts_scheduled_restart_jobs_and_na_without_file`.
  - `test_k10_na_without_close_fail_on_bridge_critical`.
  - `test_k11_requires_divergence_event_every_trading_day`.
- **Regression-AK:** `--from 2026-09-30 --to 2026-10-13 --summary` (v4) liefert weiter FAIL K1/K5/K6 und PASS K3/K4/K7/K8 — dieselben Verdikte wie Session #38 (Handover §2). Ausgabe nach `/tmp`.
- **AK:** P16 ≥ 22; Σ ≥ 2025 (Endstand vor E-2).

#### E-2 — Shakedown-Vorregistrierung (📕, VOR dem Restart)

Neue Datei `phase17_testbed/PHASE17_SHAKEDOWN_PREREGISTRATION.md` (Header-Card `status: locked`, INDEX-Zeile im selben Commit, Nikinger-Freigabe beim Commit, T23). Inhalt:

- **Fenster:** Tag 1 = erster voller Handelstag nach dem E-3-Start, Tag 2 = der nächste Handelstag. Start-Zeitstempel = die `starting scheduler daemon`-Zeile aus E-3.
- **Gepinnte Werte:** `account=demo` · `max_trades=5` · `daily_loss_cap=1800.0` · `cycle=5min` · `llm_profile=research_m3` · `daily_token_budget=300 000` (Nicht-Ausnahme) · Ausnahme `MiniMax-M3`.
- **Kriterien** (alle PASS nötig, K3/K4 nur berichtet):

  | K | Regel |
  |---|---|
  | K1 | Start-Zeilen je Dienst ≤ 2 (1 Start + 1 erlaubtes Ereignis) |
  | K2 | v5-Regel |
  | K5 | v3-Regel |
  | K6 | v5-Regel |
  | K7 | v5-Regel |
  | K8 | v3-Regel |
  | K9 | v5-Regel (Journal-Export) |
  | K10 | v5-Regel (`NA` zulässig) |
  | K11 | v5-Regel |

- **Erlaubte Operator-Ereignisse (gezählt, nie still):**
  - (a) **Re-Adoption-Probe** — einmal, wenn eine Position offen ist: `systemctl --user restart tradingbot-scheduler.service`. Erwartet ≤ 2 Zyklen später `resume: re-adopting open position …` und einen regulären Close mit geschlossener `trade_outcomes`-Zeile. Das ist das „+1" in K1.
  - (b) Tagesexport Journal (E-4).
  - Ein VM-Host-Reboot = K1 FAIL, mit Ursache „VM-Host" (T10).
- **FAIL-Regel:** Befund → Fix-Step in Phase 17 → **neue** Shakedown-Vorregistrierung `-S2` → neuer Lauf. **Kein** Kriterium wird gelockert.
- **§F2 Flip-2-Tag (bedingt, nur bei Nikinger-Go in E-5):**
  - 1 Handelstag mit `llm_profile=all_m3`;
  - dieselben Kriterien, K7 gegen `all_m3`;
  - Abbruch + Revert nach C-8;
  - Start = die erste Start-Zeile nach dem Flip-2-Commit.

  Der Abschnitt wird **jetzt** mit vorregistriert, sonst wäre der Flip-2-Tag ein Lauf ohne vorab festgelegte Kriterien (T23).
- **Report-Befehl** (Operator, nach Tag 2):
  ```bash
  phase1_broker_wrapper/.venv/bin/python phase16_activation/scripts/autonomy_report.py --prereg v5 \
    --from <D1> --to <D2> --summary --journal-file data/reports/journal_<D1>_to_<D2>.txt \
    --expect-llm-profile research_m3
  ```

#### E-3 — Deploy (Operator, alle vier Dienste kurz gestoppt)

```bash
cd /home/trading-bot/trading-bot
systemctl --user stop tradingbot-recorder.service tradingbot-discovery.service tradingbot-webui.service
ps aux | grep -E "scheduler.run|data_foundation.run|source_registry.run|uvicorn" | grep -v grep   # leer
cp data/bars.sqlite        data/bars.sqlite.bak-$(date +%Y%m%d)-pre-p17-igts
cp data/trading_bot.sqlite data/trading_bot.sqlite.bak-$(date +%Y%m%d)-pre-p17-legacy
sqlite3 data/bars.sqlite "SELECT COUNT(*) FROM bars WHERE source='ig';"                     # erwartet ≈ 3730
sqlite3 data/bars.sqlite "DELETE FROM bars WHERE source='ig'; SELECT changes();"           # T14
sqlite3 data/trading_bot.sqlite "UPDATE instincts SET trigger = '[legacy-p16] ' || trigger WHERE evidence_trade_ids_json IS NULL AND trigger NOT LIKE '[legacy-p16]%'; SELECT changes();"   # erwartet 29 (T12)
bash scripts/install_units.sh && systemctl --user daemon-reload                              # B-9
systemctl --user start tradingbot-scheduler.service tradingbot-recorder.service tradingbot-discovery.service tradingbot-webui.service
sleep 30 && systemctl --user is-active tradingbot-scheduler.service tradingbot-recorder.service tradingbot-discovery.service tradingbot-webui.service
grep "starting scheduler daemon" data/state/run_scheduler.log | tail -1   # … cycle=5min, llm_profile=research_m3).
```

**Day-0-Checks** (Exec-Session liest, Nikinger bestätigt) — Ergebnisse in den Phasenkopf:
1. Kein `PreflightError` im Log.
2. Der erste Research-Call steht in `llm_usage.json` als `"model": "MiniMax-M3"`.
3. Neue `source='ig'`-Bars haben `ts_utc <= fetched_at`.
4. Neue `decision_context`-Zeilen haben `abstain_record_id` gesetzt.
5. `run_discovery.log` zeigt `discovery cycle 2026-…`.
6. Nach ≥ 40 min WINDOW erscheint ≥ 1 `divergence_ok`/`quote_divergence` oder ein typisiertes `no_comparator` mit `reason`.

#### E-4 — Shakedown (2 Handelstage, Operator)

- Täglich, nach Handelsschluss:
  ```bash
  journalctl --user -u tradingbot-scheduler.service -u tradingbot-recorder.service \
    -u tradingbot-discovery.service -u tradingbot-webui.service \
    --since "<D1> 00:00" --until "<D2+1> 00:00" -o short-iso --no-pager \
    > data/reports/journal_<D1>_to_<D2>.txt
  ```
- Re-Adoption-Probe nach E-2 (a), falls eine Position offen ist.
- **Nichts** anderes anfassen.

#### E-5 — Auswertung, Entscheidungen, Prereg v5

1. Report-Befehl E-2 → Verdikte + Messwerte D-2 in den Phasenkopf.
2. **Nikinger-Entscheidungen:** C-8 Flip 2 (ja → Commit + 1-Tage-Shakedown `all_m3`, Report mit `--expect-llm-profile all_m3`) · D-2 K6-Einheit.
3. `phase17_testbed/PHASE17_AUTONOMY_PREREGISTRATION_v5.md` (📕, `status: locked`, INDEX):
   - 10 Handelstage, K1–K11 nach v5 mit Schwellen wie Prereg v3: K3 ≥ 5 Trades, K4 ≥ 8/10, K5 ≤ 5.
   - K6 nach D-2.
   - Profil gepinnt.
   - Erlaubte Ereignisse wie E-2, ohne die Re-Adoption-Probe.
   - Startbedingung „Start-Zeile nach Commit-Zeit".
   - **Committet vor dem Start** des 10-Tage-Laufs. Der Start selbst gehört nicht mehr zu Phase 17 (T3).

#### E-6 — Closeout

- `phase17_testbed/PHASE17_CLOSEOUT_HANDOVER.md` (Muster `PHASE16_CLOSEOUT_HANDOVER.md`: §0 BLUF + 5-Zeilen-Bilanz, offline/live-Matrix, offene Entscheidungen).
- Bild `docs/architecture/phase17_testbed.svg` (1080×1080, XML-valide, als PNG geprüft).
- Statuspflege root `CLAUDE.md` / `ROADMAP.md` / `README.md` / `docs/INDEX.md`; Memory aktualisieren.
- `check_doc_rotation.py --strict` exit 0.
- Push = Nikinger.

---

## §7 Akzeptanzkriterien

| AK | Kriterium | Beleg |
|---|---|---|
| **AK1** | Step-0-Ritual protokolliert (auch No-Op) | Phasenkopf A-1 |
| **AK2** | Baseline Σ **1964** vor dem ersten Fix; jeder Block endet mit Σ ≥ Vorblock + neue Tests, 0 rot | Phasenkopf-Tabellen |
| **AK3** | A-3-Drift korrigiert; `ROADMAP.md` < 40 000 B; root `CLAUDE.md` < 25 000 B; P16-Handover trägt den Reboot-Vermerk | `wc -c`, `tail` |
| **AK4** | IG-Probe dokumentiert; `_parse_bar` bevorzugt `snapshotTimeUTC`; nach E-3 0 alte `ig`-Zeilen, neue mit `ts_utc <= fetched_at` | P1-Test + SQL |
| **AK5** | Sampler: an jedem Shakedown-Tag ≥ 1 `divergence_ok`/`quote_divergence`; keine Samples außerhalb WINDOW/vor Öffnung+40; keine `mismatch`-Marke ohne zwei echte Divergenzen | K11 + `source_spend` |
| **AK6** | Bridge-Contract-Test mit echter DB grün; live nach dem ersten CLOSE: neue `instincts` mit Evidence, 0 `instinct.bridge`-CRITICAL | K10 |
| **AK7** | Abschneiden wirft explizit, Fehl-Parses gemetert | P4-Tests |
| **AK8** | Re-Adoption: Tests grün; live, sofern im Shakedown eine Position offen war: Log `resume: re-adopting` + regulärer Close | E-4 |
| **AK9** | Breaker Worst-Case + NULL fail-closed | P8-Tests |
| **AK10** | `abstain_record_id` ab Tag 1 gesetzt; `reason_llm_unavailable` als Klasse | SQL + P10-Test |
| **AK11** | 0 `CRITICAL abstain_lessons.paper: Paper(Engine\|DebateCaller\|TradeTracker reflect)` im Shakedown | `grep` |
| **AK12** | Scheduler-Stopp außerhalb eines Monitors endet ohne `status=9/KILL` | Journal E-3/E-4 |
| **AK13** | `discovery cycle`-Zeile ≥ 1/Stunde Laufzeit; Wrapper-Text korrigiert | Log |
| **AK14** | Profile: Tests grün; `check_llm_profile` lehnt Fehlprofile ab; `anthropic` bit-identisch; genau ein `LLMClient(` in der P8-Wiring | Tests + `rg` |
| **AK15** | M3-Smoke PASS dokumentiert (Modell, Tokens, `finish_reason`, Latenz); Flip 1 als **eigener** Commit; Start-Zeile `llm_profile=research_m3`; Research-Records `MiniMax-M3` ab Tag 1 | Phasenkopf + Log |
| **AK16** | `LLM_UNAVAILABLE`: Tests grün (live nur bei Ausfall beobachtbar) | P4/P8/P10-Tests |
| **AK17** | Budget ignoriert `MiniMax-M3` an allen drei Zählstellen; Shakedown: 0 `BUDGET`-Blocks | K6 v5 + Log |
| **AK18** | Report v5: Tests grün; v3-Fenster-Verdikte unverändert | P16-Tests + `/tmp`-Report |
| **AK19** | Shakedown-Prereg **vor** dem E-3-Start committet; Shakedown PASS in allen nicht-berichtenden Kriterien | `git log` vs. Start-Zeile + Report |
| **AK20** | Prereg v5 committet (Profil + K6-Einheit gepinnt) | `git log` |
| **AK21** | Closeout-Handover + SVG + INDEX + Status + Memory; Phasenkopf trägt genau einen Session-Block; `check_doc_rotation.py --strict` exit 0 | E-6 |

**Phasen-Abnahme = AK19 + AK20** (setzt AK1–AK18 voraus) **+ AK21.**

---

## §8 Fehlgriffe, die wie andere Fehler aussehen (Symptom → erster Verdächtiger)

| Symptom | Erster Verdächtiger | Zweiter |
|---|---|---|
| `test_wiring_reward_sink.py` hängt / liest echten Keyring nach C-4 | Fixture stubbt nur `reward.credentials`, `_build_llm` liest `research.credentials` | — |
| Nach B-1 meldet `BudgetedIGBarProvider` erstmals `stale_history` | **Gewollt:** der F1-Schutz (`service.py:150`) sieht jetzt echte Alter — vorher waren sie negativ | IG liefert für das Epic wirklich tote Historie (F1) |
| Nach B-2 weiter 100 % `divergence_no_comparator` | B-1 nicht deployt (`ig_bar_ts` im Event > Event-`ts`) | Recorder steht (yF-Lag > 25 min) → `reason` im Event lesen |
| Nach B-2 werden Epics `mismatch` markiert | `n_yf` im `quote_divergence`-Event < 5 oder Fenster nicht `[ts, ts+5m)` | echte Entkopplung (CFD-Basis springt) — zwei Tage hintereinander prüfen |
| Nach Flip 1 abstained Research **jeden** Zyklus | `LLM error: … HTTP 400` (Endpoint lehnt `response_format` ab → C-3-Fallback greift nicht) | `truncated` → `max_tokens`; `HTTP 401` → Key (Preflight hätte fangen müssen → Service/Username prüfen); `unterminated <think>` → `max_tokens` zu klein |
| `LLM_UNAVAILABLE`-CRITICAL nach 3 Ticks | MiniMax-Abo-Fenster/Quote (HTTP 429 im Log) | Netz/DNS; Key widerrufen |
| WebUI-Token-Karte bleibt nahe 0 % | **Gewollt:** M3 zählt nicht (`exempt_tokens` im JSON) | — |
| Report sagt K6 FAIL, Bot blockte aber nicht | Report ohne `--prereg v5` gelaufen (v4 zählt alle Tokens) | — |
| Scheduler-Stopp endet weiter in SIGKILL | Units nicht neu installiert (`install_units.sh` + `daemon-reload`) | Stopp **während** eines Monitors (bis `max_hold`) — dann ist der Kill nach 360 s erwartet; die Re-Adoption fängt es auf |
| Re-Adoption schließt direkt nach dem Restart | **Gewollt** (T8): `recorded_at` + 240 min oder 17:15 schon überschritten | — |
| Position offen, aber keine Re-Adoption | Record ist `PENDING` ohne `deal_id` (Aufgabe von `reconcile_startup`) | Restart außerhalb WINDOW → wartet bis 09:00 (gewollt) |
| Breaker blockt den ganzen Tag, CRITICAL „OPEN trade without initial_risk" | **Gewollt fail-closed**: eine heutige OPEN-Zeile ohne `initial_risk` (SQL prüfen) | — |
| Bridge schreibt nur `proposed` | `MIN_EVIDENCE=3` bei wenigen Trades — **kein Defekt** | Extractor nennt IDs, die nicht in den letzten 500 Trades stehen |
| `ValueError: status must be one of …` aus der Bridge | `.decision` nicht verwendet (B-3 Punkt 2 unvollständig) | — |
| `abstain_record_id` bleibt NULL | `_Observed` gibt weiter `None` zurück **oder** Wrapper-Reihenfolge falsch | Context-Recorder aus (`enable_context_persistence`) |
| `test_models.py` rot mit `13 != 12` | **Erwartet** nach C-5 — Pin auf 13 | — |
| K2-v5 FAIL „discovery 0" | Discovery-Dienst nicht neu gestartet (alte Code-Version) | Daemon unarmed (`DISCOVERY_ARMED` fehlt) |
| `database is locked` beim E-3-DELETE | Recorder lief noch | WebUI hält `mode=ro`-Handle (harmlos für `bars.sqlite`) |
| Scheduler startet nicht: `ValueError … no pricing row` | C-3-Preiszeile fehlt oder Modell-ID-Tippfehler (`MiniMax-M3`) | — |
| Scheduler startet nicht: `ValueError … not budget-exempt` | Modell-ID an nur einer oder zwei der drei Stellen geändert (`_M3.model` / P4-Preiszeile / `budget_exempt_models`, C-7) | — |
| Research wird nach einer Modell-ID-Änderung wieder vom Budget gebremst | `budget_exempt_models` nicht mitgezogen **und** `check_llm_profile` umgangen (z. B. Test-Profil) | WebUI `exempt_tokens` = 0 → die Records tragen eine andere ID |
| K11 FAIL („kein Divergenz-Event an Tag X") | **Erst die Pass-Zeiten prüfen:** der Sampler läuft nur im Universe-Refresh (alle 240 min). Wegen der 40-min-Sperre zählen nur die Pässe gegen 13:0x und 17:0x (`bar_fetch`-Stunden in `research_health.jsonl`), ein Neustart kann sie verschieben | erst danach der Sampler selbst: `reason` im `no_comparator`-Event (`no_complete_bar` / `partial_yf_window` / `no_yf_bars`) |
| `LLM_UNAVAILABLE` steigt, aber der Endpoint antwortet | **Gewollt:** auch Abschneiden zählt dazu (C-5-Begriff) — `grep -c "LLM output truncated"` im Log trennt es | `unterminated <think>` |
| SQL-Fenster über `open_ts`/`close_ts` zählen falsch | gemischte Offsets: `open_ts` trägt `+02:00`, `close_ts` `Z` — erst parsen, nie String-vergleichen | `date(open_ts)` in SQLite rechnet nach UTC um |
| `journalctl`-Export dauert Minuten | ohne Unit-Filter/`--since` gerufen | — |
| Flip 2: Debatte abstained alles / `DebateLLMError` | `max_tokens_agent=512` zu klein für ein Reasoning-Modell → `_debate_config` übernimmt `max_tokens` aus der RoleSpec nicht | `ask_agent` setzt ein `claude-*`-Modell (DebateConfig nicht überschrieben) |
| `git push` rejected | `origin/main` bewegt — nie `--force` | — |

---

## §9 „Bei Ausführung verifizieren" — vollständige Liste

Was hier **nicht** steht, gilt als geprüft (Stand 2026-10-17).

1. **IG v3 `/prices` liefert `snapshotTimeUTC`** (IG-Doku sagt ja, live nie gesehen) — B-0-Probe. Fehlt das Feld → B-1b.
2. **MiniMax-Endpoint `https://api.minimax.io/v1/chat/completions` und Modell-ID `MiniMax-M3`** für das Abo. Der Dev-Wrapper nutzt `https://api.minimax.io/anthropic` + `MiniMax-M3[1m]` (`scripts/claude-minimax`). Ob die OpenAI-kompatible Route dieselbe ID ohne `[1m]` erwartet, zeigt nur der C-7-Smoke.
3. **Unterstützt MiniMax `response_format: {"type": "json_object"}`?** Der Fallback (C-3) ist gebaut; der Smoke zeigt, ob er nötig ist.
4. **Schreibt M3 `<think>`-Blöcke in `content`?** (MiniMax-M2-Verhalten). `--show-raw` im Smoke.
5. **M3-Tokenverbrauch und Latenz je Research-Call** — Smoke. Die Werte `max_tokens=4096` / `timeout_s=90` in `_M3` sind **Annahmen**, bei Abweichung anpassen (eigener Commit).
6. **MiniMax akzeptiert `temperature=0.2`** (Research-Default `models.py:604`).
7. **Abo-Grenzen** (Anfragen je Zeitfenster) — wirken als HTTP 429 → `LLM_UNAVAILABLE`.
8. **Genauer Journal-Text eines Auto-Restarts** — erwartet `Scheduled restart job, restart counter is at N`. Offline nicht erzeugbar; erstes echtes Vorkommen gegen die K9-Regex prüfen.
9. **Wirkung von `TimeoutStopSec=360` beim VM-Host-Reboot.** Der Host kann früher hart ausschalten.
10. **Attributnamen in `Brain`** für den B-3-Test (`Brain.__init__`, `brain.py:175`: vermutlich `self._llm`).
11. **`phase8_scheduler/scripts/smoke_test.py` läuft offline weiter** (nutzt Fakes, nicht die Wiring) — nach Block C einmal starten.
12. **`webui/static/app.js` liest nur bekannte Felder** (`exempt_tokens` wird ignoriert) — `grep -n "consumed_tokens\|calls_today" phase8_scheduler/webui/static/app.js`.
13. **Konzept-Dateinamen für ARCHITECTURE A-3** (`ls docs/concepts/ | grep -E "phase1[0-6]"`).
14. **Ob der Recorder nach einem Stopp Lücken nachholt.** Relevant nur, wenn E-3 länger als wenige Minuten dauert; Lücken sind dann Messlücken, keine Fehler.

---

## §10 Out-of-Scope (Phase 17 baut das **nicht**)

| Was | Warum nicht |
|---|---|
| WebUI-Layout (Σ-P&L oben, Trades-Seitenliste, Lessons bis unten) | T2; Nikinger-Wunsch bleibt als Kandidat (Phase-16-Handover §4) |
| Backoff-Anker `_pending_close[...].closed_at`, `close_ts`-Cold-Reconstruct, Smoke-Muster für `_build_*`, `requires-python` | T2 |
| ATR/Range/`regime_tag` in `market_regime_snapshots` | so entworfen (Phase 10 Block B, „degradiert immer auf `quote_only`") |
| Debatten-Felder in `decision_context` für Debatten-Abstains (`judge_decision` etc.) | Erweiterung, kein Defekt; Transkript steht in `debate_log.json` |
| `abstain_records.context_json` befüllen | nie verdrahtet, kein Konsument |
| Lessons für Trades 24/25 nachholen | Ausfall 10-09; kein Nachhol-Mechanismus vorhanden (wäre neu) |
| Preflight-Universe-Refresher außerhalb WINDOW | nur der Sampler-Teil wird gegated (B-2); Discover/Promote/Resolver bleiben |
| Teilbar (laufender IG-5m-Bar) wird archiviert | ohne Konsument nach B-2 (Sampler nimmt nur abgeschlossene Bars) |
| Unterbrechbarer Runner-Schlaf | T10 — `TimeoutStopSec` reicht |
| Strategie/Edge, Live-Konto, GapRescue, Force-Trigger | T24, Hard Rules |
| Formaler Phase-9-Closeout; Größe von `phase15_v4/CLAUDE.md` (82 KB) und `phase7_reward/CLAUDE.md` (52 KB) | Nikinger-Entscheidung bzw. Doku-Umbau ohne Messwert — nur gelistet (A-3) |
| Start des 10-Tage-Laufs | T3: gehört zur Testreihe nach Phase 17 |

---

## §11 Operator-Aktionen (Nikinger, nicht die Exec-Session)

| # | Wann | Was | Kosten |
|---|---|---|---|
| 1 | A-4 | `git push -u origin main` | — |
| 2 | A-4 | `sunshine_…deb` aus dem Repo-Root räumen | — |
| 3 | B-0 | IG-Probe (bei gestopptem Scheduler) | 1 IG-Datenpunkt (Allowance 8 195/10 000) |
| 4 | C-7 | Bot-Key setzen; M3-Smoke | 1 Call aus dem Abo |
| 5 | E-2 | Shakedown-Prereg freigeben | — |
| 6 | E-3 | Deploy-Sequenz | — |
| 7 | E-4 | 2 Handelstage laufen lassen, Journal exportieren, ggf. Re-Adoption-Probe | Research ≈ 102 M3-Calls/Tag (Abo) · Anthropic (Debatte, Lessons, Paper-Debatte, Reflect) ≈ 60–90 k Tokens ≈ 0,3–0,5 €/Tag · Sampler 64–192 IG-Pkt/Tag (8 Bars × 8 Epics × bis zu 3 Pässe) |
| 8 | E-5 | Entscheidungen C-8 + D-2; Prereg v5 freigeben | — |
| 9 | E-6 | Push | — |

---

## §12 Commit-Konvention

- `phase17: <imperative>` für reine Phase-17-Docs.
- Cross-Phase immer mit beiden Scopes, z. B. `phase17+phase15: bridge — pass trades, read .decision, write *_json keys (B-3)`.
- Ein Step pro Commit; die Flips C-7/C-8 **allein**.
- Jede neue `.md`/`.svg` bringt ihre `docs/INDEX.md`-Zeile im selben Commit.
- Erwartete Anzahl: A 2 · B 10 · C 7 (+ Flip 2 optional) · D 1 · E 4 + Closeout.

---

## §13 Reviews

- **Advisor vor dem Ansatz (2026-10-17, Plan-Session)**. Übernommen:
  - Swap und K6 getrennt behandeln, weil ein Modellwechsel den Token-Cap nicht bewegt (T7);
  - Username-Fehlpassung beim Dev-Key (T6, C-3 Punkt 2);
  - Abschneide-Sichtbarkeit **vor** dem Swap (B-4);
  - Debatte per Config-Override statt P6-Code (C-4 `_debate_config`);
  - Contract-Test mit echter DB inklusive Migrationen (B-3);
  - Re-Adoption-Details (`recorded_at`, Währung, Sofort-Close, Runner statt `executor.run`; T8, B-5);
  - `initial_risk` NULL fail-closed (T9);
  - Start-Zeilen-Parser bleibt treffend (C-4, §5);
  - zwei Starts je Boot (`PartOf=graphical-session.target`, §2.2) und Journal als K9-Quelle (E-1);
  - statischer Discovery-Text (B-10);
  - Abnahme bei Prereg v5 + Shakedown (T3).
- **Advisor vor „fertig" (2026-10-17, nach Commit `988f8da`)**. Alle sieben Punkte sind im Folge-Commit eingearbeitet:
  - (1) Der bedingte Flip-2-Tag bekommt vorab Kriterien: E-2 §F2, C-8.
  - (2) Die Modell-ID steht an drei Stellen. `check_llm_profile` prüft jetzt auch die Budget-Ausnahme (C-1, C-4, C-7, §8).
  - (3) `compute_return_divergence` hat als einzigen Code-Aufrufer `heartbeat.py:351`; per `rg` belegt (B-2).
  - (4) Fehlende Verbatim-Anker ergänzt: B-2, B-5, B-10, C-5, D-1, E-1.
  - (5) Die ROADMAP-Überschrift behauptet keinen Phase-9-Closeout mehr (A-3).
  - (6) Begriff `LLM_UNAVAILABLE` umfasst auch Abschneiden; getrennt gezählt per Log (C-5, §8).
  - (7) K11-Fehlgriff: zuerst die Pass-Zeiten prüfen (§8).

---

## §14 Nachtrag 2026-10-18 — Executor-Test GLM (OpenCode) + Bot-Provider z.ai Pay-per-use

> **Auslöser (Nikinger 2026-10-18):** Der 20-€-MiniMax-Plan wird durch den 20-€-z.ai-Coding-Plan ersetzt.
> Der Executor soll ein fähigeres Modell als M3 werden („offener Test", Rückweg: MiniMax-Endpoint bis **2026-11-15**).
>
> Antworten:
> 1. **nur OpenCode** — Claude Code bleibt Anthropic-only;
> 2. Start `glm-5.3-flash`, die **ganze Familie** (`glm-5.2`, `glm-5.3`, `glm-5.3-flash`) bleibt für die Evaluation zugelassen;
> 3. Bot-Provider = **Option b**, die allgemeine z.ai-API mit Pay-per-use;
> 4. Review-Gate und Rückfallregel **ja**. Dazu der Quirk: zeigt `glm-5.2` auf dem Kontingent einen Flash-ähnlichen Verbrauch, ist ein 5.2-Durchlauf ein sinnvoller Test.
>
> **Dieser Abschnitt hat Vorrang** vor §1 und §6, wo sie sich widersprechen.

### 14.1 Was überschrieben wird

| Stelle | bisher | neu |
|---|---|---|
| T4 | MiniMax M3 über OpenAI-Compat | **GLM über die allgemeine z.ai-API (Pay-per-use)**, weiter mit `OpenAICompatLLMClient`. Das Modell wählt der Nikinger nach dem Familien-Smoke (14.4) |
| T5 | Profile `research_m3` / `all_m3` | **`research_glm` / `all_glm`**; Flip 1 / Flip 2 gegated wie bisher |
| T6 | Bot-Key `trading-bot-minimax-bot` / `api_key` | **`trading-bot-zai-bot` / `api_key`** (Pay-per-use, Keyring). **Nie** der Coding-Plan-Key oder -Endpoint |
| T7 | M3 budgetfrei, „Grenzkosten 0" | Das gewählte GLM-Bot-Modell bleibt **budgetfrei**, weil die Kadenz Research auf ≤ 102 Calls/Tag begrenzt. Es bekommt aber eine **echte Preiszeile**, damit € gemessen wird; D-2 entscheidet dann € vs. Token |
| T22 | Exec Sonnet 5 (Claude Code) | **OpenCode + z.ai Coding Plan**, Start `zai-coding-plan/glm-5.3-flash`. Claude Code (Anthropic) macht nur das Review-Gate (14.2) |
| C-1 | `PROVIDERS["minimax"]`, `_M3`, `research_m3`/`all_m3` | `PROVIDERS["zai"] = ProviderSpec(kind="openai_compat", base_url="https://api.z.ai/api/paas/v4", api_key_service="trading-bot-zai-bot", api_key_username="api_key")`; `_GLM = RoleSpec(provider="zai", model="<C-7-Wahl>", max_tokens=4096, timeout_s=90.0)`; Profile `research_glm`/`all_glm` |
| C-1 (neu) | — | `check_llm_profile` wirft zusätzlich, wenn eine Nicht-Anthropic-`base_url` den Pfad **`/coding/`** enthält. Der Coding-Plan-Endpoint ist für den Bot verboten; eine Sperre träfe auch den Executor. Test `test_check_rejects_coding_plan_endpoint` (+1) |
| C-2 | `budget_exempt_models = ("MiniMax-M3",)` | `("<C-7-Wahl>",)` |
| C-3 | Preiszeile `"MiniMax-M3": (0.0, 0.0)` | Preiszeilen für die ganze Familie mit **echten** USD/Mtok (in, out): `"glm-5.3": (1.4, 4.4)`, `"glm-5.2": (1.4, 4.4)`, `"glm-5.3-flash": (0.15, 0.5)`. Quelle: models.dev-Katalog `~/.cache/opencode/models.json`, Provider `zai`, Stand 2026-10-18; vor dem Commit gegen die z.ai-Preisseite prüfen (14.6 Nr. 17). Ein späterer Modellwechsel braucht dann nur noch `_GLM.model` + `budget_exempt_models` |
| C-6 | Seed-Aufruf MiniMax | `store_minimax_key.py --service trading-bot-zai-bot --username api_key`. Der Skriptname bleibt, der Seeder ist generisch |
| C-7 | M3-Smoke | **Familien-Smoke** (14.4) |
| C-8 | `all_m3` | `all_glm` |
| D-1, E-2, E-5 | `MiniMax-M3`, `research_m3` | das gewählte GLM-Modell, `research_glm` |
| §8/§9, MiniMax-Zeilen | MiniMax | gelten sinngemäß für z.ai; Ergänzungen in 14.5/14.6 |
| §7 (neu) | — | **AK22:** Review-Gate PASS ist vor dem E-3-Start im Phasenkopf dokumentiert (Session, Befunde, Fix-Commits) |

### 14.2 Executor-Test (OpenCode)

- **Setup (Nikinger):** `opencode auth login` → Provider „Z.AI Coding Plan" (`zai-coding-plan`) → Key.
  - `opencode.json` bleibt **unverändert**: Der Katalog kennt `glm-5.2`, `glm-5.2-highspeed`, `glm-5.3`, `glm-5.3-flash`, `glm-5.3-highspeed` bereits.
  - Endpoint ist `https://api.z.ai/api/coding/paas/v4` (Katalog `~/.cache/opencode/models.json`, 2026-10-18).
  - `opencode models zai-coding-plan` listet die Modelle erst **nach** dem Login. Heute meldet der Befehl „Provider not found", das ist erwartet.
  - Der Key landet in `~/.local/share/opencode/auth.json` (0600), wie heute bei `minimax`/`google`/`nvidia`. Das ist Harness-Infrastruktur außerhalb des Repos, keine Bot-Credential; der Bot-Key liegt im Keyring (T6).
- **Einstieg:** `AGENTS.md` → root `CLAUDE.md` → `phase17_testbed/CLAUDE.md` → dieser Plan, **zuerst §14**.
- **Modelle:**
  - Start `glm-5.3-flash`.
  - Zur Evaluation zugelassen: `glm-5.2` und `glm-5.3`; die `-highspeed`-Varianten nur auf Nikinger-Wunsch.
  - **5.2-Quirk:** zeigt `glm-5.2` auf dem Plan-Kontingent einen Flash-ähnlichen Verbrauch, folgt ein 5.2-Durchlauf auf einem vergleichbaren Step.
- **Evaluations-Protokoll** (Tabelle im Phasenkopf), je Exec-Session:
  - Modell;
  - Steps;
  - Kontingent vorher/nachher (der Nikinger liest es im z.ai-Dashboard ab);
  - Tests grün/rot;
  - Rückfall-Ereignisse.
- **Rückfallregel:** Der Step geht an MiniMax M3.1 Flash Preview in OpenCode (Endpoint bis 2026-11-15) oder an Claude Code (Anthropic), wenn eines davon eintritt:
  - der Executor scheitert zweimal am selben Step;
  - ein roter Test steht nach 3 Fix-Versuchen noch.
- **Review-Gate (Pflicht, vor E-3):** Eine Claude-Code-Session (Anthropic, Opus) prüft alle Exec-Commits von A-0 bis D-1. Schwerpunkte:
  - **B-5** — Order-Pfad;
  - **B-6** — Breaker, Hard Rule 5;
  - **C-4** — LLM-Verdrahtung, Startup-Check;
  - **B-3** — Bridge;
  - **B-2** — die `mismatch`-Einbahnstraße.

  Befunde werden **vor** dem Deploy als Fix-Commits erledigt. Erst „Review PASS" gibt E-3 frei.

### 14.3 Bot-Provider (Option b)

- Allgemeine z.ai-API, Pay-per-use: **`https://api.z.ai/api/paas/v4`** (Katalog-Provider `zai`).
- **Nie** `https://api.z.ai/api/coding/paas/v4`. Laut [Usage Policy](https://docs.z.ai/devpack/usage-policy) ist der Coding Plan „only … within officially supported tools"; Verstöße führen zu Drosselung, Sperre und ab dem dritten Mal zum Bann. Die C-1-Prüfung erzwingt das beim Start.
- Eigener Key `trading-bot-zai-bot` / `api_key` mit Guthaben (Nikinger).
- GLM liefert Reasoning in **`reasoning_content`**, nicht in `content`. Der C-3-`<think>`-Strip bleibt als harmloser Schutz.
- **Kostenschätzung Research** — eine **Annahme**, der Reasoning-Anteil ist unbekannt. Gerechnet mit 102 Calls/Tag × ≈ 3,5 k Input + ≈ 1,5 k Output:
  - `glm-5.3` ≈ 1,2 $/Tag;
  - `glm-5.3-flash` ≈ 0,13 $/Tag;
  - zum Vergleich heute: Sonnet ≈ 1,0 €/Tag, aber nur bis zum Cap.

### 14.4 C-7 neu — Familien-Smoke (Nikinger, 3 Calls Pay-per-use, < 0,01 $)

```bash
for m in glm-5.3 glm-5.3-flash glm-5.2; do
  phase1_broker_wrapper/.venv/bin/python phase4_research/scripts/openrouter_smoke.py \
    --model "$m" --base-url https://api.z.ai/api/paas/v4 \
    --key-service trading-bot-zai-bot --key-username api_key \
    --max-tokens 4096 --timeout-s 90 --show-raw
done
```

- Je Modell kommen PASS/FAIL, Tokens, `finish_reason` und Latenz in den Phasenkopf.
- Danach **wählt der Nikinger das Research-Modell**.
- Ein Commit setzt `_GLM.model` + `budget_exempt_models`; die Preiszeilen liegen seit C-3 vor.
- Erst dann folgt der Flip-1-Commit `llm_profile="research_glm"`.

### 14.5 Ergänzung §8 (Fehlgriffe)

| Symptom | Erster Verdächtiger | Zweiter |
|---|---|---|
| Scheduler startet nicht: `ValueError … /coding/ endpoint` | **Gewollt fail-closed:** die `base_url` zeigt auf den Coding Plan | — |
| Research `LLM_UNAVAILABLE` mit HTTP 402/429 und „balance" | z.ai-Guthaben (Pay-per-use) leer | Rate-Limit des Kontos |
| OpenCode: `Provider not found: zai-coding-plan` | `opencode auth login` fehlt | Katalog veraltet (`~/.cache/opencode/models.json`) |
| Kontingent schmilzt schneller als erwartet | Session läuft auf `glm-5.3` statt `-flash` (Modell im Session-Header prüfen) | großer Kontext: der Plan (111 KB) wird wiederholt komplett gelesen → nur die nötigen Abschnitte lesen |

### 14.6 Ergänzung §9 (bei Ausführung verifizieren)

15. **Pay-per-use-Endpoint:** Der Katalog sagt `https://api.z.ai/api/paas/v4`, eine Doku-Zusammenfassung nannte `https://api.z.ai/api/v1`. Der C-7-Smoke entscheidet.
16. Braucht Pay-per-use einen **eigenen Key**, oder rechnet z.ai denselben Account-Key je nach Endpoint ab? (z.ai-Konsole, Nikinger)
17. **Echte z.ai-Preise** je Modell. Der models.dev-Katalog nennt `glm-5.3`/`glm-5.2` mit 1,4/4,4 und `glm-5.3-flash` mit 0,15/0,5 USD/Mtok. Vor dem C-3-Commit gegen die z.ai-Preisseite prüfen.
18. Zählen **Reasoning-Tokens gegen `max_tokens`** (Abschneiden bei 4096)? Der Smoke zeigt es am `finish_reason`.
19. Unterstützt z.ai **`response_format: {"type": "json_object"}`**? Sonst greift der C-3-Fallback.
20. **Kontingent-Verbrauch je GLM-Modell** im Coding Plan (z.ai-Dashboard) — die Grundlage des 5.2-Quirks.

### 14.7 Σ-Ziele

Die C-1-Prüfung auf `/coding/` bringt **+1** P8-Test. Damit gilt:
- Block C Σ ≥ **2016** (P8 ≥ 288 nach C-5);
- D-1 Σ ≥ **2019** (P8 ≥ 291);
- E-1 Σ ≥ **2026**.

Die P8-Schwellen der einzelnen Steps in §6 ab C-1 verschieben sich um +1.

### 14.8 Notiz 2026-10-18 — die Executor-Integration macht **eurofyx-fleet**, nicht dieser Plan

> **Nikinger 2026-10-18:** „die Integration selbst passiert über die Eurofleet (getrennt vom Plan)".
> Ersetzt den Punkt „Setup (Nikinger)" in 14.2.

**Zuständigkeiten:**

| Wer | Was |
|---|---|
| **eurofyx-fleet** (privates Infra-Repo des Nikingers) | OpenCode-Provider `zai-coding-plan` einrichten (Auth), Modellwahl/Default, Neustart von `opencode.service`, Kündigung/Rückweg MiniMax (Endpoint bis 2026-11-15) |
| **Phase-17-Exec-Session** | fasst `~/.config/opencode/`, `~/.local/share/opencode/auth.json` und `opencode.service` **nicht** an. Sie trägt nur ihre Zeile in die Executor-Evaluation im Phasenkopf ein |
| **Bot / dieses Repo** | unverändert. Der Bot nutzt **nie** den Coding-Plan (14.3); sein Pay-per-use-Key `trading-bot-zai-bot` ist ein Bot-Thema (C-6/C-7) und gehört nicht zur Fleet-Integration |

**Was die Fleet-Integration wissen muss** (Stand 2026-10-18, selbst gemessen):
- OpenCode **1.18.33** (`~/.opencode/bin/opencode`).
- Der Katalog `~/.cache/opencode/models.json` führt Provider `zai-coding-plan` mit API `https://api.z.ai/api/coding/paas/v4` und den Modellen `glm-5.2`, `glm-5.2-highspeed`, `glm-5.3`, `glm-5.3-flash`, `glm-5.3-highspeed`. In `opencode.json` sind deshalb keine eigenen Modell-Einträge nötig.
- `opencode models` listet nur Provider mit Login. Vor dem Login meldet `zai-coding-plan` „Provider not found".
- Heutige Keys in `auth.json` (0600): `google`, `nvidia`, `minimax`.
- `opencode.service` startet `opencode serve` auf der Tailscale-IP, Port 4096. Ein Neustart unterbricht laufende Sessions.
- Start-Modell `glm-5.3-flash`. Die Familie `glm-5.2`/`glm-5.3` ist zur Evaluation zugelassen, inklusive 5.2-Quirk (14.2).

**Schnittstelle zurück zum Plan:** Die erste Exec-Session (A-0) startet erst, wenn die Fleet „OpenCode + z.ai bereit" meldet (Nikinger). Bis dahin gilt der Rückweg aus 14.2 (MiniMax in OpenCode bis 2026-11-15 oder Claude Code). Am Plan selbst ändert sich dadurch nichts.

---

## §15 Nachtrag 2026-10-19 — Provider-Plastizität (Miniplan, Plan-Session Opus 5.5 in Claude Code)

> **Auslöser (Nikinger 2026-10-19):** *„der Endpunkt für trading bot Aktivitäten sollte so umgebaut werden, das er mit
> sämtlichen ‚gängigen' Endpunkten funktioniert (anthropic, openai, die chinesischen Anbieter etc)."* Input: die
> Working-Notes `phase17_testbed/provider_plasticity/` (MiniMax M3, 2026-10-19).
>
> **Was §15 ist:** eine **In-place-Änderung von C-1, C-3, C-4, C-6, C-7** — kein Block C2, keine Phase 18
> (Nikinger Q2). Block C hat am 2026-10-19 **null Zeilen Code** (`ls phase8_scheduler/scheduler/` — kein
> `llm_profiles.py`; `grep -n "_build_llm\|llm_profile" phase8_scheduler/scripts/wiring.py` trifft nur Kommentare
> Z. 390/414/443). Ändern kostet also keinen Rückbau. **Reihenfolge §14 → §15 → §6:** wo §15 einer Stelle in §6/§14
> widerspricht, gilt §15. §14 (z.ai `/paas/v4`, nie `/coding/`; `trading-bot-zai-bot`; Familien-Smoke) bleibt
> **wortgleich** gültig.
>
> **BLUF:** Jeder OpenAI-kompatible Provider ist **ein Daten-Eintrag** in `PROVIDERS` — keine `if provider == …`-Zeile
> im Code. Der Client lernt genau **drei** Request-Quirks (`max_tokens_field`, `send_temperature`, `extra_body`) plus eine strengere Coding-Plan-Sperre (T31), deren
> Defaults den heutigen Payload **bytegleich** lassen. Neun Einträge werden ausgeliefert; Live-Beleg in **zwei Stufen**:
> Familien-Smoke über kostenlose Gateway-Modelle jetzt, native Endpoints erst, wenn der Nikinger dort einen Key hat.
> Ehrliche Grenze: „null Code-Commit pro Provider" ist unter T17 **nicht** erreichbar — ein neuer **aktiver** Provider
> ist ein reiner Daten-Commit an ≤ 3 Literalstellen, und `check_llm_profile` nennt beim Start die vergessene.

### 15.1 Nikinger-Antworten (2026-10-19, diese Session)

| Frage (`04_open_questions.md`) | Antwort |
|---|---|
| Q1 Provider-Liste | z.ai/GLM, OpenAI, DeepSeek, Qwen, Kimi, OpenRouter **und MiniMax**; Tests über die **kostenlosen Modelle der jeweiligen Familie via OpenCode** („just for testing") |
| Q2 Ort | **§15-Nachtrag zu Block C** (empfohlen) |
| Q3 Konfig-Form | **T17 bleibt: Python-Dict** in `llm_profiles.py` (empfohlen) — kein YAML |
| Q4 Live-Stufe | **Zwei Stufen** (Rückfrage, empfohlen): Stufe 1 Familien-Smoke über Gateways mit Gratis-Modellen; Stufe 2 nativer Smoke je Eintrag, sobald ein nativer Key existiert |
| Q5 Block-C-Kompatibilität | (Plan-Session) C-1/C-3/C-4/C-6/C-7 werden **ergänzt**, nicht ersetzt; §15.4 nennt jede Stelle |
| Q6 Report/K7 | (Plan-Session) nur Anker: E-1 liest `llm_profile` aus der Startzeile (C-4 Punkt 6) — §15 ändert daran nichts, weil keine neuen Profile entstehen |
| Q7 Budget-Ausnahmen | (Plan-Session) **eine** Liste `budget_exempt_models` (wie C-2/§14). Sie betrifft nur Modelle **aktiver** Profile; Smoke-Modelle laufen ohne Meter-Datei |
| Q8 Closeout-Reihenfolge | entfällt: §15 läuft **in** Block C, also vor D/E-3 |

### 15.2 Gelockte Entscheidungen T25–T31 (je Zeile mit Begründung — nicht gutgemeint aufmachen)

| ID | Entscheidung | Begründung |
|---|---|---|
| **T25** | Genau **zwei** Client-Klassen: `LLMClient` (Anthropic, nativ) und `OpenAICompatLLMClient` (alles andere). Ein Provider = ein `ProviderSpec`-Eintrag. **Keine** Verzweigung nach Provider-Namen im Code | Alle neun Ziel-Provider sprechen `POST {base_url}/chat/completions` mit Bearer-Auth (Doku 2026-10-19, §15.3). Eine dritte Klasse oder `if name == …` wäre die Drift, die die Notes beklagen |
| **T26** | Quirks sind **Felder direkt auf `ProviderSpec`**, keine eigene `QuirkSpec`-Klasse, und **provider-, nie modellbezogen** | Eine Klasse mit drei Feldern, die nur in `ProviderSpec` lebt, ist Verpackung. Provider-bezogen, weil `ask_agent` (P6) `client.model` je Debatten-Rolle **überschreibt** (§5, C-4 Punkt 2): ein am Modellnamen hängender Quirk würde im Konstruktor für das falsche Modell entschieden. Braucht ein Modell andere Quirks, bekommt es einen eigenen Eintrag (z. B. `openai` vs. ein späteres `openai_legacy`) |
| **T27** | Genau drei Quirks: `max_tokens_field ∈ {"max_tokens","max_completion_tokens"}`, `send_temperature: bool`, `extra_body: Mapping[str, Any]`. **Gestrichen:** `streaming`, `extra_headers`, `response_format_policy` | Je Feld ein belegter Provider (§15.3): OpenAI GPT-5-Linie verlangt `max_completion_tokens` und lehnt `temperature` ab; Kimi führt `max_tokens` als deprecated; Denk-Schalter (DeepSeek/GLM `thinking`, Qwen `enable_thinking`) sind Nicht-Standard-Body-Felder → `extra_body`. **Streaming** würde Parse- und Meter-Pfad (B-4) umbauen, Non-Stream funktioniert bei allen kommerziellen Modellen; Qwen-Open-Source-Modelle, die nur streamen, sind damit bewusst außen vor. **extra_headers**: kein Ziel-Provider verlangt einen (OpenRouter-Attribution ist optional). **response_format_policy**: alle dokumentierten Provider akzeptieren `json_object`; der Rest fängt der C-3-(a)-400-Fallback |
| **T28** | Defaults = heutiger Payload **bytegleich** inkl. Schlüssel-Reihenfolge `model, messages, max_tokens, temperature, response_format`. `extra_body` wird **zuerst** eingesetzt und darf **keinen** reservierten Schlüssel enthalten (`model, messages, max_tokens, max_completion_tokens, temperature, response_format, stream`) → `ValueError` im **Client-Konstruktor** | Der Konstruktor ist der eine Engpass, durch den Bot (`_build_llm`) **und** Smoke laufen. `stream` ist reserviert, damit niemand per Hintertür Streaming einschaltet, das der Parser nicht kann (T27) |
| **T29** | **Eine** Abbildung `ProviderSpec → Client-kwargs`: reine Funktion `client_kwargs(spec)` in `llm_profiles.py`, benutzt von `_build_llm` **und** vom Smoke-Skript (`--provider`). Ein Test erzwingt, dass jedes `ProviderSpec`-Feld außer `kind` abgebildet ist | Sonst testet der Smoke eine andere Konstruktion als der Bot. Der Feld-Abdeckungstest macht ein neues Quirk-Feld ohne Abbildung sofort rot |
| **T31** | Die Coding-Plan-Sperre wird verschärft: `check_provider` wirft, wenn `"coding" in base_url.lower()` (statt nur Pfad `/coding/`, §14.1) | Gemessen 2026-10-19 über alle 10 `*coding*`-Provider im Katalog `~/.cache/opencode/models.json`: der Pfad-Test trifft **4**, der neue Test **7**. Alibaba (`coding-intl.dashscope.aliyuncs.com`, `coding.dashscope.aliyuncs.com`) und KUAE tragen „coding" im **Host**. Strenger als §14, nie lockerer; keiner der 9 Einträge enthält „coding". **Grenze:** MiniMax-Coding-Plan (`api.minimax.io/anthropic/v1`) und umans sind per URL unsichtbar. Gegen sie hilft nur die Key-Regel (§15.3 `minimax`, Stufe 2) |
| **T30** | Live-Status je Eintrag steht als **Kommentar** am Eintrag (`# doc 2026-10-19 <url> · live: —`), kein Datenfeld. Stufe 1 = Gateway-Familien-Smoke (Gratis-Modelle), Stufe 2 = nativer Smoke; ein Eintrag gilt erst nach **Stufe 2** als für einen Flip zugelassen | Nikinger Q4 (zwei Stufen). Ein Gateway-Smoke belegt das Antwortformat der Modellfamilie, **nicht** `base_url`/Auth/Feldnamen des nativen Endpoints. Ein Statusfeld würde von keinem Code gelesen (YAGNI) |

**Abgelehnt (nicht wieder vorschlagen):** YAML (`PyYAML` ist im venv **nicht** installiert — `import yaml` → `ModuleNotFoundError`, 2026-10-19; zweite Wahrheit neben der P4-Preistabelle; widerspricht T17). Anthropic-kompatible Shims der Fremdanbieter (T4: `output_config.format` dort ungeprüft). Preise/Ausnahmeliste in dieselbe Datei ziehen (Cross-Phase-Umbau P4→P8 ohne gemessenen Nutzen; `check_llm_profile` fängt die Drift schon beim Start). Umbenennen von `openrouter_smoke.py` (§14.4-Befehle zeigen darauf).

### 15.3 Quirk-Tabelle (Doku-Stand 2026-10-19; „live" trägt nur der Nikinger ein)

| Eintrag | `base_url` | Keyring (service / user) | `max_tokens_field` | `send_temperature` | `extra_body` (Default) | Doku-Beleg 2026-10-19 | Stufe 1 (Gateway) | Stufe 2 (nativ) |
|---|---|---|---|---|---|---|---|---|
| `anthropic` | — (SDK) | `tradingbot` (unverändert) | — | — | — | live seit P4 | — | ✅ |
| `zai` | `https://api.z.ai/api/paas/v4` (§14) | `trading-bot-zai-bot` / `api_key` | `max_tokens` | `True` (Range 0–1, 0,2 ok) | `{}` — **thinking default an** | docs.z.ai/api-reference/llm/chat-completion: `json_object` ja, `thinking.type` enabled/disabled | — | §14.4 + Gratis `glm-4.7-flash` |
| `minimax` | `https://api.minimax.io/v1` (Plan C-1) | `trading-bot-minimax-bot` / `api_key` | `max_tokens` | `True` | `{}` | **nicht abgerufen** → §15.7 Nr. 21 | `opencode_zen` `minimax-m3.1-flash-free` | ✅ mit dem Abo-Key in `trading-bot-minimax-bot` (Nikinger 2026-10-19, §15.7 Nr. 27; gültig bis 2026-11-15) |
| `openai` | `https://api.openai.com/v1` | `trading-bot-openai-bot` / `api_key` | **`max_completion_tokens`** | **`False`** | `{}` | platform.openai.com 403 für WebFetch; belegt über Microsoft-Foundry-Doku „GPT-5 … use `max_completion_tokens` … don't support temperature" → §15.7 Nr. 22 | — (kein Gratis-Modell) | wenn Key |
| `deepseek` | `https://api.deepseek.com` | `trading-bot-deepseek-bot` / `api_key` | `max_tokens` | `True` (im Thinking-Modus wirkungslos) | `{}` — **thinking default an** | api-docs.deepseek.com/api/create-chat-completion: `json_object` ja, `thinking.type`, `reasoning_content` | `opencode_zen` `deepseek-v4.1-flash-free` | wenn Key |
| `qwen` | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` | `trading-bot-qwen-bot` / `api_key` | `max_tokens` | `True` | `{}` — Qwen3.5+ **thinking default an**, `enable_thinking` nur via Body | alibabacloud …/compatibility-of-openai-with-dashscope zeigt **workspace-spezifische** URLs `https://{WorkspaceId}.<region>.maas.aliyuncs.com/compatible-mode/v1` → §15.7 Nr. 23 | — | wenn Key **und** URL aus der Konsole |
| `kimi` | `https://api.moonshot.ai/v1` | `trading-bot-kimi-bot` / `api_key` | **`max_completion_tokens`** (`max_tokens` deprecated) | `True` — Doku schweigt → §15.7 Nr. 24 | `{}` | platform.kimi.ai/docs/api/chat: `json_object` ja, `thinking` (K2.6), `reasoning_effort` (K3) | — | wenn Key |
| `openrouter` | `https://openrouter.ai/api/v1` | `trading-bot-openrouter-bot` / `api_key` (**nicht** der M1-Key `openrouter`) | `max_tokens` | `True` | `{}` | M1-Smoke 2026-07 (Memory) | `minimax/minimax-m3.1-flash:free` | = Stufe 1 (Gateway ist hier der native Endpoint) |
| `opencode_zen` | `https://opencode.ai/inference/openai/v1` | `trading-bot-opencode-bot` / `api_key` (**nie** `~/.local/share/opencode/auth.json`, §14.8) | `max_tokens` | `True` | `{}` | Katalog `~/.cache/opencode/models.json` Provider `opencode`, Feld `api` (2026-10-19) → §15.7 Nr. 25 | = Stufe 1 | = Stufe 1 |

**Keine Preiszeilen für die Smoke-Modelle.** `check_llm_profile` verlangt Preiszeilen nur für Modelle **aktiver** Profile; der Smoke schreibt keine Meter-Datei (`token_meter_path=None`), ein unbekanntes Modell kostet dort 0 + WARNING (`token_meter.py`, fail-soft). **Keine neuen Profile** außer §14 (`research_glm`/`all_glm`): ein Profil entsteht erst mit einem Flip.

### 15.4 Änderungen an Block C (Exec: in den genannten Step-Commit einarbeiten, keine eigenen Commits)

Zeilen = Stand HEAD `6dff4bd` (2026-10-19), selbst gelesen. **Der Verbatim-String ist der Anker.**

#### C-1 (+) — `scheduler/llm_profiles.py`

1. Importzeile im C-1-Codeblock: `from dataclasses import dataclass` → `from dataclasses import dataclass, field, fields`; `from typing import Mapping` → `from typing import Any, Mapping`.
2. `ProviderSpec` erhält **nach** `api_key_username: str | None = None` drei Felder:
   ```python
       # §15 T26/T27: provider-level request quirks (never model-level — P6 ask_agent rewrites
       # client.model per role). Defaults reproduce the pre-§15 payload byte for byte (T28).
       max_tokens_field: str = "max_tokens"          # "max_tokens" | "max_completion_tokens"
       send_temperature: bool = True
       extra_body: Mapping[str, Any] = field(default_factory=dict)
   ```
3. `PROVIDERS` = die neun Einträge aus §15.3, je mit Kommentar `# doc 2026-10-19 <url> · live: —` (T30). `zai` exakt wie §14.1. `minimax` bleibt mit `trading-bot-minimax-bot` drin (Nikinger Q1). Nur `openai` setzt `max_tokens_field="max_completion_tokens", send_temperature=False`; nur `kimi` setzt `max_tokens_field="max_completion_tokens"`. Alle `extra_body` leer.
4. Neue reine Funktionen (unter `role_spec`):
   ```python
   _MAX_TOKENS_FIELDS: tuple[str, ...] = ("max_tokens", "max_completion_tokens")


   def check_provider(name: str, spec: ProviderSpec) -> None:
       """Raise ValueError if ``spec`` cannot work. Pure; called by check_llm_profile per active provider."""
       # kind ∈ {"anthropic","openai_compat"}; for openai_compat: base_url starts with "https://",
       # contains no "coding" anywhere (case-insensitive; T31 — tightens the §14 /coding/ rule), api_key_service + api_key_username
       # non-empty, max_tokens_field in _MAX_TOKENS_FIELDS. Message names provider + field + value.


   def client_kwargs(spec: ProviderSpec) -> dict[str, Any]:
       """The ONE ProviderSpec → OpenAICompatLLMClient kwargs mapping (T29) — _build_llm and the smoke use it."""
       return {"base_url": spec.base_url, "api_key_service": spec.api_key_service,
               "api_key_username": spec.api_key_username, "max_tokens_field": spec.max_tokens_field,
               "send_temperature": spec.send_temperature, "extra_body": dict(spec.extra_body)}
   ```
5. `check_llm_profile`: die §14-`/coding/`-Prüfung **wohnt** jetzt in `check_provider`; `check_llm_profile` ruft `check_provider(p, PROVIDERS[p])` für jeden Provider des Profils (vor den vier Regeln aus C-1). Der §14-Test `test_check_rejects_coding_plan_endpoint` bleibt unverändert grün (er ruft `check_llm_profile`).
6. **Tests P8 (+3)** in `tests/test_llm_profiles.py`:
   - `test_check_provider_rejects_http_missing_key_bad_field_and_coding_host` — vier `pytest.raises(ValueError)`-Blöcke: `base_url="http://…"`, `api_key_service=None`, `max_tokens_field="max_output_tokens"` und `base_url="https://coding-intl.dashscope.aliyuncs.com/v1"` (T31: Host statt Pfad).
   - `test_every_shipped_provider_is_well_formed` — `for n, s in PROVIDERS.items(): check_provider(n, s)`; plus `assert set(PROVIDERS) >= {"anthropic","zai","minimax","openai","deepseek","qwen","kimi","openrouter","opencode_zen"}`. Obermenge, nicht Gleichheit: ein neuer Eintrag bleibt ein reiner Daten-Commit ohne Test-Edit.
   - `test_client_kwargs_covers_every_quirk_field` — `assert set(client_kwargs(PROVIDERS["openai"])) == {f.name for f in fields(ProviderSpec)} - {"kind"}`.

#### C-3 (+) — `research/llm_openai_compat.py` (P4)

Zusätzlich zu C-3 Punkt 1–3 (und §14):

4. Konstruktor (Anker Z. 119 `        api_key_service: str = "openrouter",`): nach dem C-3-`api_key_username`-Argument drei kw-Args
   `max_tokens_field: str = "max_tokens",`, `send_temperature: bool = True,`, `extra_body: Mapping[str, Any] | None = None,`. Im Rumpf (nach Z. 155 `        self.temperature = temperature`):
   ```python
           # §15 T27/T28: provider quirks, validated here — the one choke point the bot and the smoke share.
           if max_tokens_field not in ("max_tokens", "max_completion_tokens"):
               raise ValueError(f"max_tokens_field must be max_tokens|max_completion_tokens, got {max_tokens_field!r}")
           reserved = set(extra_body or {}) & _RESERVED_PAYLOAD_KEYS
           if reserved:
               raise ValueError(f"extra_body must not set client-owned keys: {sorted(reserved)}")
           self.max_tokens_field = max_tokens_field
           self.send_temperature = send_temperature
           self.extra_body: dict[str, Any] = dict(extra_body or {})
   ```
   Modulkonstante unter Z. 82 `_KEYRING_USERNAME = "api_key"`: `_RESERVED_PAYLOAD_KEYS = frozenset({"model", "messages", "max_tokens", "max_completion_tokens", "temperature", "response_format", "stream"})`. Import `from typing import Any` → `from typing import Any, Mapping`. Docstring-Args um die drei Felder ergänzen.
5. `_attempt`, Payload (Anker Z. 258 `        payload = {` bis Z. 267 `        }`) ersetzen durch:
   ```python
           payload: dict[str, Any] = {
               **self.extra_body,  # first: client-owned keys below always win (T28; reserved keys rejected in __init__)
               "model": self.model,
               "messages": [
                   {"role": "system", "content": f"{system}\n\n{schema_instruction}"},
                   {"role": "user", "content": user},
               ],
               self.max_tokens_field: self.max_tokens,
           }
           if self.send_temperature:
               payload["temperature"] = self.temperature
           payload["response_format"] = {"type": "json_object"}
   ```
   Der C-3-(a)-400-Fallback entfernt danach nur `response_format` (`{k: v for k, v in payload.items() if k != "response_format"}`). **Pflicht:** seine `log.info`-Zeile enthält den ersten Fehlertext (`"HTTP 400 with response_format — retrying once without it; first fault: %s", exc`; `str(exc)` trägt `body[:300]`, Z. 103). Sonst sieht der Operator nur den zweiten Fehler (§15.6).
6. **Bestehenden Test anpassen (erwartet, kein Bug):** `tests/test_llm_openai_compat.py:176` `test_bad_request_400_raises_immediately_no_retry` wird durch C-3 (a) **rot**, aber nur an `assert len(calls) == 1`: der Fallback sendet ein zweites Mal, `responses.pop(0)` auf der leeren Liste wirft `IndexError`, der als `LLMResponseError` gewrappt wird — `pytest.raises` bleibt also grün und täuscht. Neu: **zwei** `_FakeResponse(400, text="bad request")`, `assert len(calls) == 2`, `assert "response_format" in calls[0]["json"]` und `assert "response_format" not in calls[1]["json"]`. Umbenennen in `test_bad_request_400_retries_once_without_response_format_then_raises`. Netto ±0 Tests.
7. **Tests P4 (+5)** in `tests/test_llm_openai_compat.py` (Muster `_client` Z. 44 + `_fake_post` Z. 49 + `_happy_body` Z. 37):
   - `test_default_quirks_payload_is_unchanged` — `assert list(calls[0]["json"]) == ["model", "messages", "max_tokens", "temperature", "response_format"]`.
   - `test_max_completion_tokens_field_replaces_max_tokens` — `max_tokens_field="max_completion_tokens"` → Schlüssel da, `"max_tokens"` fehlt.
   - `test_send_temperature_false_omits_temperature`.
   - `test_extra_body_is_merged_into_payload` — `extra_body={"thinking": {"type": "disabled"}}` → im Payload.
   - `test_invalid_quirks_raise_value_error_at_construction` — `extra_body={"stream": True}` und `max_tokens_field="x"` je `pytest.raises(ValueError)`, ohne Netz-Call.

#### C-4 (+) — `scripts/wiring.py` (P8)

7. `_build_llm`, Nicht-Anthropic-Zweig: statt der einzelnen kwargs `base_url=…, api_key_service=…, api_key_username=…` steht `OpenAICompatLLMClient(model, **client_kwargs(provider), timeout_s=…, max_tokens=…, temperature=…, token_meter_path=…, config=…, cache_system=cache_system)` (T29). Import `client_kwargs` neben `role_spec, PROVIDERS`.
8. Heutige Anker der sieben Stellen (die Zahlen in C-4/T16 sind verschoben): `_build_research` Z. 331 `    llm = LLMClient(` · `_make_debate_runner._build` Z. 362 `        llm = LLMClient(` · `_build_reward_sink` Z. 428 `    llm = LLMClient(` und Z. 445 `    instinct_llm = LLMClient(` · `_build_abstain_sink` Z. 525 `        client = LLMClient(` · `_build_paper_engine` Z. 582 `        client = LLMClient(` · `_build_paper_tracker` Z. 740 `        client = LLMClient(` · `build_scheduler` Z. 992 `    research = _build_research(`.
9. **Test P8 (+1)** in `tests/test_wiring_llm_routing.py`: `test_build_llm_passes_provider_quirks_to_openai_compat` — `monkeypatch.setitem(LLM_PROFILES, "t_openai", {r: RoleSpec(provider="openai", model="gpt-x") for r in LLM_ROLES})`, `_build_llm("research", "t_openai", …)` → Instanz `OpenAICompatLLMClient` mit `max_tokens_field == "max_completion_tokens"`, `send_temperature is False`, `base_url == "https://api.openai.com/v1"`. Kein Keyring-Zugriff (der Client liest lazy).

#### C-6 (+) — `phase4_research/scripts/openrouter_smoke.py`

3. Zusätzlich zu den C-6-Flags: `--provider NAME` (Choices = `sorted(PROVIDERS)` ohne `anthropic`). Mit `--provider`: `kw = client_kwargs(PROVIDERS[args.provider])` und `OpenAICompatLLMClient(model=args.model, **kw, max_tokens=args.max_tokens, timeout_s=args.timeout_s)`. `--provider` zusammen mit `--base-url`/`--key-service`/`--key-username` → `parser.error(...)`. Ohne `--provider` verhält sich das Skript wie C-6 (OpenRouter-Default, §14.4-Befehle unverändert).
   - Import `from scheduler.llm_profiles import PROVIDERS, client_kwargs` — **funktioniert ohne `sys.path`-Eingriff**: das venv hat `scheduler` editable installiert (`python -c "import scheduler"` aus `/tmp` → `phase8_scheduler/scheduler/__init__.py`, 2026-10-19). Bewusste Ausnahme von der Abhängigkeitsrichtung P8→P4: ein Operator-Skript, nicht collected, und genau das, was T29 verlangt.
   - Ausgabezeile zusätzlich `provider=<name|custom>`.
   - Kein Test (Operator-Skript, wie C-6).

#### C-7 (+) — Live-Belege in zwei Stufen (Nikinger; T30)

**Vorher (Nikinger, einmalig je Key):** `phase1_broker_wrapper/.venv/bin/python scripts/store_minimax_key.py --service <service> --username api_key` (C-6-Seeder, generisch). Der OpenCode-Zen-Key ist ein **eigener** API-Key aus der OpenCode-Konsole — **nie** aus `auth.json` kopieren (§14.8, Harness-Infrastruktur).

**Stufe 1 — Familien-Smoke, Gratis-Modelle (Kosten 0 €; IDs = Katalog 2026-10-19, vor dem Lauf in `~/.cache/opencode/models.json` gegenprüfen — Gratis-IDs rotieren):**
```bash
S=phase4_research/scripts/openrouter_smoke.py; PY=phase1_broker_wrapper/.venv/bin/python
for m in deepseek-v4.1-flash-free minimax-m3.1-flash-free glm-5.3-flash-free; do   # glm: Katalog 2026-10-19 sagt glm-4.7-free, Zen-Doku nennt GLM-5.3-Flash Free — die vorhandene ID nehmen
  $PY $S --provider opencode_zen --model "$m" --max-tokens 4096 --timeout-s 90 --show-raw; done
$PY $S --provider openrouter --model minimax/minimax-m3.1-flash:free --max-tokens 4096 --timeout-s 90 --show-raw
$PY $S --provider zai --model glm-4.7-flash --max-tokens 4096 --timeout-s 90 --show-raw   # z.ai Gratis-Modell, nativer Endpoint
```
Danach §14.4 (GLM-Familie, Pay-per-use) **mit `--provider zai`** statt der drei Einzelflags.

**Stufe 2 — nativ, nur wo ein Key existiert:** `$PY $S --provider <openai|deepseek|qwen|kimi|minimax> --model <id> --max-tokens 4096 --timeout-s 90 --show-raw`. Für `qwen` zuerst die Workspace-URL aus der Konsole in `PROVIDERS["qwen"].base_url` eintragen (eigener Commit, §15.7 Nr. 23).

**Protokoll:** je Lauf PASS/FAIL, `finish_reason`, Tokens, Latenz als Zeile in den Phasenkopf **und** den `live:`-Kommentar am Eintrag aktualisieren (Exec, ein Doku-Commit für alle). Ein FAIL ist **kein** Blocker für Block C — nur ein Eintrag mit Stufe-2-PASS darf in ein Flip-Profil (T30).

### 15.5 Σ-Ziele (ersetzt §14.7)

| Stand | P4 | P8 | Σ |
|---|---:|---:|---:|
| heute (gemessen 2026-10-19, diese Session, 16 Suites einzeln) | 167 | 264 | **1978** |
| nach Block B (Plan) | 167 | — | ≥ 1992 |
| nach Block C (§6 + §14 + §15: P4 +5, P8 +4) | ≥ 177 | ≥ 292 | **≥ 2025** |
| nach D-1 | — | ≥ 295 | ≥ 2028 |
| nach E-1 | — | — | ≥ 2035 |

### 15.6 Ergänzung §8 (Fehlgriffe, die wie andere Fehler aussehen)

| Symptom | Erster Verdächtiger | Zweiter |
|---|---|---|
| Log zeigt den `response_format`-Retry, danach ein anderer 400 | **Quirk-Felder des Eintrags** (falsches `max_tokens_field`, unerwünschtes `temperature`, fremder `extra_body`-Schlüssel). Ursache steht im **ersten** Fehlertext der Retry-Zeile | erst danach: Provider kann wirklich kein `json_object` |
| `test_bad_request_400_…` rot nur an `len(calls)`, `pytest.raises` grün | **erwartet** durch C-3 (a): Test nach §15.4 C-3 Nr. 6 umbauen — **nicht** den Fallback „reparieren" | — |
| Smoke `HTTP 400 … max_tokens` / „unsupported parameter" bei `openai` | Eintrag nutzt `max_tokens` statt `max_completion_tokens` | Modell ist **kein** Reasoning-Modell und will `temperature` → eigener Eintrag (T26), nicht Quirk am Modell |
| Smoke `finish_reason=length` mit leerem `content`, Tokens hoch | Denk-Modus default an (DeepSeek/GLM/Qwen3.5+): Reasoning frisst `max_tokens` | `extra_body={"thinking": {"type": "disabled"}}` (DeepSeek/GLM) bzw. `{"enable_thinking": False}` (Qwen) — Datenänderung am Eintrag, Nikinger-Entscheidung |
| Qwen `HTTP 400 … enable_thinking … stream` | Open-Source-Qwen-Modell, das nur streamt (T27) | kommerzielles Modell wählen oder `enable_thinking: False` |
| `ValueError: extra_body must not set client-owned keys` beim Start | gewollt (T28) — Eintrag versucht `stream`/`max_tokens` per Body zu setzen | — |
| Smoke `401` bei `opencode_zen` | Key aus `auth.json` statt eigenem API-Key, oder Gratis-Modell nicht per API freigegeben | §15.7 Nr. 25 |
| Smoke `ModuleNotFoundError: scheduler` | Skript mit System-Python statt venv-Python gestartet | — |
| `test_every_shipped_provider_is_well_formed` rot nach Qwen-URL-Commit | Workspace-URL ohne `https://` oder mit „coding" (Alibaba-Coding-Plan `coding-intl.dashscope…` / `coding.dashscope…` — **gewollt** gefangen, T31) | — |

### 15.7 Ergänzung §9 (bei Ausführung verifizieren — vollständig; was hier nicht steht, ist selbst geprüft)

21. **MiniMax nativ** `https://api.minimax.io/v1`: Feldnamen, `json_object`, Temperatur-Range (Doku nicht abgerufen; Plan C-1 hatte die URL schon unter Vorbehalt). Stufe-2-Smoke entscheidet.
22. **OpenAI**: `platform.openai.com` lieferte WebFetch **403**. Beleg nur indirekt (Microsoft-Foundry-Reasoning-Doku). Ob `json_object` auf der GPT-5-Linie mit Chat Completions geht → Stufe-2-Smoke.
23. **Qwen `base_url`**: die Doku zeigt 2026-10-19 nur noch workspace-spezifische Hosts; ob `dashscope-intl.aliyuncs.com/compatible-mode/v1` noch antwortet, ist ungeprüft. Ob `json_object` bei Denk-Modus-Modellen geht: Doku schweigt.
24. **Kimi `temperature`**: Doku schweigt; ältere Thinking-Modelle verlangten eine feste Temperatur. Bei `HTTP 400 … temperature` → `send_temperature=False` am Eintrag.
25. ✅ **Geklärt 2026-10-19 (Doku [opencode.ai/docs/zen](https://opencode.ai/docs/zen/)):** Der Zen-API-Key ist ausdrücklich für direkte Aufrufe außerhalb von OpenCode gedacht („for applications calling the endpoints directly"). Endpoint `https://opencode.ai/inference/openai/v1/chat/completions` bestätigt. Datenpolitik der Gratis-Modelle: **GLM-5.3-Flash Free** und **DeepSeek V4.1 Flash Free** = zero retention, kein Training; MiMo/Exo u. a. = Daten können zur Modellverbesserung genutzt werden. Der Smoke-Prompt ist synthetisch (`_smoke_context`, keine Konto-/Positionsdaten), also unkritisch. Laut Doku-Liste heißt das GLM-Gratis-Modell evtl. `glm-5.3-flash-free` statt `glm-4.7-free` → ID vor dem Lauf im Katalog prüfen
26. **z.ai Gratis-Modell** `glm-4.7-flash` auf `/paas/v4`: Katalog sagt Preis 0; ob es mit einem Pay-per-use-Key ohne Guthaben antwortet, zeigt der Smoke.
27. ✅ **Entschieden 2026-10-19 (Nikinger):** Der MiniMax-Abo-Key ist vorhanden und funktioniert. Er wird für den Bot in den **eigenen** Namespace `trading-bot-minimax-bot` / `api_key` geseedet (gleicher Wert, getrennter Eintrag; der Dev-Key `trading-bot-minimax` bleibt unberührt, T6-Isolationsmuster). Das deckt sich mit dem ursprünglichen T6 („Das Abo-Kontingent deckt API-Nutzung"). Stufe-2-Smoke `minimax` ist damit freigegeben. **Ablauf:** der MiniMax-Endpoint gilt bis **2026-11-15** (§14). Danach muss jedes Profil, das `minimax` nutzt, zurückgeflippt werden

### 15.8 Was §15 **nicht** tut

- keine Modell-Empfehlung, kein Flip (bleibt §14/C-7/C-8);
- kein Streaming, keine Header, keine dritte Client-Klasse (T25/T27);
- keine Preiszeilen außer §14 (GLM-Familie) — ein neuer **aktiver** Provider bringt seine Preiszeile im Flip-Commit mit, `check_llm_profile` erzwingt das;
- kein Code in P6/P7/P13 (T13 unverändert); Berührt werden nur P4 (`llm_openai_compat.py`, Smoke-Skript) und P8 (`llm_profiles.py`, `wiring.py`) — beide in T13.
