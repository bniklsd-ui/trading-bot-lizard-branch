---
status: live
purpose: PHASE-HEAD, Phase 17 (Prüfstand) — 🔄 eröffnet 2026-10-17 (Plan-Session, Opus 5.5). Keine neuen Features. Tiefe Härtung des Bestehenden — vier Phase-16-PASS-Blocker + drei neu gemessene stille Totalausfälle zu, LLM pro Rolle austauschbar (Research zuerst auf **MiniMax-M3 über die MiniMax-Abo-API** — Planwechsel 2026-11-03, Plan §16), Report + Vorregistrierung v5 als Fundament für die ausgiebigen Tests. Executor: offener Test GLM in OpenCode (§14).
read-when: jede Phase-17-Exec-Session — zuerst diesen Kopf, dann den `## Session stopped`-Block, dann den Plan
detail: L1
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase17_testbed_plan.md               # 📕 der Plan (T1–T24, D1–D13, Blöcke A–E, AK1–AK21, §8 Fehlgriffe, §9 Verify)
  - ./PHASE17_SHAKEDOWN_PREREGISTRATION.md                  # 📕 **E-2 — Shakedown-Vorregistrierung (locked, T23-Freigabe 2026-11-04)**: Fenster = 2 Handelstage nach dem E-3-Start, gepinnte Werte (demo · max_trades 5 · daily_loss_cap 1800.0 · cycle 5min · llm_profile research_m3 · Budget 300k · **Ausnahme: alle MiniMax-Modelle**), K1/K2/K5/K6/K7/K8/K9/K10/K11 (K3/K4 nur berichtet), erlaubte Ereignisse, FAIL-Regel, §F2, Report-Befehl, **Aktiv-Block** (wird am E-3-Tag eingetragen)
  - ./provider_plasticity/                                  # 🔄 Working-Notes Provider-Plastizität (2026-10-19, 4 Notizen: 01 Decision T25–T28 · 02 Current-State · 03 Opus-Brief · 04 Open Questions Q1–Q8)
  - ../phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md     # 📕 Vorgänger-Handover (§4 PASS-Blocker, §5 E1–E8)
  - ../phase16_activation/scripts/autonomy_report.py       # Report-Skript, Block E erweitert es in place (--prereg v5)
  - ./SESSIONS_ARCHIVE.md                                  # rotierte Session-Blöcke (L3, newest-first)
updated: 2026-11-04 (Exec-Session #16 — **E-2 ausgeführt**: Shakedown-Vorregistrierung `PHASE17_SHAKEDOWN_PREREGISTRATION.md` geschrieben, `status: locked` nach T23-Freigabe; **Nikinger-Entscheidung „alle MiniMax-Modelle ausnehmen“** ⇒ Code-Commit in P8 (`budget_exempt_models = ("MiniMax-M3", "MiniMax-M3.1-Flash")`, 2 Pins verschärft, Negativ-Beweis erbracht, P8 299 unverändert, Σ **2053**); 1 Code-Commit + 1 Doku-Commit) | 2026-11-04 (Exec-Session #15 — **E-1 ausgeführt** (Plan §18): Report v5 in `phase16_activation/scripts/autonomy_report.py` — `llm_usage_per_day` mit `exempt_models` (D-1-Fortsetzung, inkl. `exhausted_at`-Summation) + 6 v5-Evaluatoren (K2/K6/K7/K9/K10/K11) + `count_discovery_cycles_per_day` + K5-`by_logger`/`deal_related` + CLI `--prereg {v4,v5}`/`--journal-file`/`--expect-llm-profile`/`--exempt-model`; 1 Code-Commit in P16 + 1 Doku-Commit, Σ 2046 + 7 = **2053** grün (P16 15 → 22); v4-Verdikte **unverändert** (FAIL K1/K5/K6 · PASS K2/K3/K4/K7/K8); **5 fail-closed-Entscheidungen** (K7 ohne Start-Zeile ⇒ FAIL, K9 ohne Zeitstempel ⇒ FAIL, K2/K11 ohne Handelstag ⇒ NA, K10 ohne CLOSE ⇒ NA, Ausnahmeliste lazy aus `SchedulerConfig()`); **v5-Läufe vor E-3 sind false FAILs** (K2/K11 brauchen den Deploy) | 2026-11-04 (Exec-Session #14 — **der nächste Block geschrieben**: Plan §18 = Block E / E-1 (Report v5: Token-Budget-Ausnahme im Report + v5-Kriterien K2/K5/K7/K9/K10/K11), Anker re-verifiziert (null Drift) + 2 live gemessene Voraussetzungen; **dokumentarische Session, kein Code** — Σ unverändert **2046**; Session-Ende + **Push**) | 2026-11-04 (Exec-Session #13 — **D-1 ausgeführt** (Plan §17): Token-Budget-Ausnahme an `budget_exempt_models` — `scheduler/budget.py` (Exempt-Records überspringen) + `webui/api.py` (`exempt_tokens` separat), 1 Code-Commit + 1 Doku-Commit, Σ 2043 + 3 = **2046** grün; D-2 bleibt Nikinger-Entscheidungspunkt (K6-Einheit, **kein Code**); Report-Zählort folgt in E-1) | 2026-11-03 (Exec-Session #12 — **der nächste Block geschrieben**: Plan §17 = Block D / D-1 (Budget-Ausnahme an zwei P8-Zählstellen, Anker re-verifiziert) + D-2 als Entscheidungspunkt; **dokumentarische Session, kein Code** — Σ unverändert **2043**; Session-Ende + **Push**) | 2026-11-03 (Exec-Session #11 — **C-7-Smoke PASS (Operator: beide MiniMax-Modelle PASS)** + **C-8 Flip 1** ausgeführt: `llm_profile = "research_m3"` (nur Research → MiniMax-M3), 1 Code-Commit + 1 Doku-Commit, Σ 2042 + 1 = **2043** grün; **inert bis E-3** (Hold); Flip 2 `all_m3` bleibt gegated) | 2026-11-03 (Exec-Session #10 — **Planwechsel z.ai → MiniMax** (Abo/M Plan, Nikinger-Entscheidung 2026-11-03): M-1 = Provider-Register umgestellt (Profil `research_m3`/`all_m3`, Modell `MiniMax-M3` mit `max_tokens=8192`, Preiszeile `(0.0, 0.0)`, `budget_exempt_models=("MiniMax-M3",)`, Quirks `max_completion_tokens`), 1 Code-Commit + 1 Doku-Commit, Σ 2041 + 1 = **2042** grün; **C-7 wartet auf den Nikinger** (Key `trading-bot-minimax-bot` + Familien-Smoke); **Frist 2026-11-15**) | 2026-11-03 (Exec-Session #9 ENDE — **Block C (Code C-1…C-6) abgeschlossen**: Provider-Register + LLM-Austausch (`_build_llm`) + `LLM_UNAVAILABLE` + Key-/Smoke-Skript, 6 Commits, Σ 2004 + 37 = **2041** grün; **C-7 wartet auf den Nikinger** (Bot-Key `trading-bot-zai-bot` fehlt, Familien-Smoke)) | 2026-11-03 (Exec-Session #8 ENDE — **Block B abgeschlossen**: B-7 Abstain-Naht + B-8 Paper-Logstufen + B-9 Stop-Timeout + B-10 Discovery-Beleg, 4 Code-Commits, Σ 2000 + 4 = **2004** grün; Scheduler `disabled`+`inactive` (Hold) + 3 Units laufen weiter) | 2026-10-25 (Exec-Session #7 ENDE — Scheduler-Hold: systemd-Autostart aus + getrackter Repo-Guard `data/state/SCHEDULER_HELD`, +12 root-Tests, Σ **2000**) | 2026-10-19 (Exec-Session #6 ENDE — B-6 Breaker Worst-Case, 1 Commit in P8, Σ 1985 + 3 P8-Tests = **1988** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #5 ENDE — B-5 Monitor-Re-Adoption, 1 Commit in P5+P8, Σ 1978 + 5 P5 + 2 P8 = **1985** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Plan-Session §15 Provider-Plastizität — Forward-Agenda C2 → Plan §15, Σ-Ziele C/D/E-1 +9, Σ 1978 re-gemessen) | 2026-10-19 (Exec-Session #4 ANSCHLUSS — `provider_plasticity/` Working-Notes-Set angelegt (kein Plan, Input für Opus-Miniplan-Session; 5 INDEX-Einträge); Nikinger-Entscheidungen Q1–Q8 ausstehend) | 2026-10-19 (Exec-Session #4 ENDE — B-4 Abschneiden sichtbar, 1 Commit in P4, Σ 1974 + 4 P4-Tests = **1978** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #3 ENDE — B-3 Promotion-Bridge Nahtfehler, 2 Commits in P15+P8, Σ 1971 + 2 P15 + 1 P8 = **1974** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #2 ENDE — B-2 Divergenz-Sampler Reparatur, Σ 1965 + 4 P12-Tests + 2 P8-Tests = **1971** grün) | 2026-10-19 (Exec-Session #1 ENDE — A-0+A-1+A-2 + A-3 + B-0 + B-1, Σ 1965) | 2026-10-18 (Plan-§14-Nachtrag) | 2026-10-17 (Plan-Session, Opus 5.5)
---

# CLAUDE.md — Phase 17: Prüfstand (`phase17_testbed/`)

> **Quelle der Wahrheit ist der Code, dann der Plan, dann dieser Kopf.**
> Plan: [`../docs/concepts/phase17_testbed_plan.md`](../docs/concepts/phase17_testbed_plan.md).

## Mission

Der Bot wird zum **Prüfstand**. Für die anschließenden ausgiebigen Tests muss gelten:
- jeder vorhandene Arm liefert nachweisbar, was er liefern soll;
- jeder bekannte Mess- und Geldpfad-Defekt ist zu;
- das LLM ist pro Rolle austauschbar.

Nikinger 2026-10-17: *„keine besondere Feature-Session — bildet eher das Fundament für ausgiebige
Tests. LLM-Austausch wäre aber trotzdem sehr wichtig"* · *„kein zusätzlicher Umfang, eher extrem
tiefe Optimierung von dem, was schon da ist."*

**Abnahme:** Shakedown-Vorregistrierung → 2-Tage-Shakedown PASS → Prereg v5 committet (Plan AK19 + AK20 + AK21).
Der 10-Tage-Lauf selbst ist die Testreihe **nach** Phase 17.

## Gelockt (Kurzform — volle Begründung Plan §1, **Vorrang hat Plan §16** vom 2026-11-03)

| ID | Kern |
|---|---|
| T4/T5 (§16) | **MiniMax-M3 über die MiniMax-Abo-API** (`https://api.minimax.io/v1`, OpenAI-kompatibel; **nie** ein Coding-Plan-Endpoint — prüft `check_llm_profile` beim Start). Das Modell bestätigt der Nikinger nach dem Familien-Smoke C-7 (`MiniMax-M3` / `MiniMax-M3.1-Flash`). **Flip 1** = `research_m3`, **Flip 2** = `all_m3`, nur auf Nikinger-Go nach dem Shakedown |
| T6 (§16) | Bot-Key im eigenen Namespace `trading-bot-minimax-bot` / `api_key` (Keyring; nie der Coding-Plan-Key, nie der Executor-Key) |
| T7 (§16) | Das MiniMax-Bot-Modell ist budgetfrei (`budget_exempt_models`; Abo/M Plan ⇒ Grenzkosten 0, die Kadenz begrenzt es auf ≤ 102 Research-Calls/Tag). Es hat eine **Preiszeile** `(0.0, 0.0)` (Abo) — die Pay-per-use-Preise ($0.30/$1.20 pro Mtok, Doku 2026-11-03) stehen als Kommentar daneben, falls der Key wechselt. Anthropic bleibt bei 300 k; K6-Einheit entscheidet der Nikinger nach dem Shakedown |
| T8 | Monitor-Re-Adoption nach Restart, nur im WINDOW, inklusive Sofort-Close bei überschrittener Haltezeit |
| T9 | Breaker zählt heutige OPEN-Zeilen mit `−initial_risk`; NULL → fail-closed |
| T13 | Code in P1, P4, P5, P8, P10, P12, P14, P15, P16; P2 nur Tests; **kein** Code in P6/P7/P13 |
| T14/T15 | IG-Zeitstempel-Fix (+ Löschen der 3 730 falschen `ig`-Bars), Divergenz-Sampler-Reparatur |
| T22 (§14) | Exec = **offener Test in OpenCode + z.ai Coding Plan**, Start `zai-coding-plan/glm-5.3-flash`, Familie `glm-5.2`/`glm-5.3` zugelassen. Claude Code bleibt Anthropic-only und macht das **Pflicht-Review-Gate vor E-3**. Rückfall auf MiniMax (bis 2026-11-15) oder Claude, wenn ein Step zweimal scheitert oder ein Test nach 3 Versuchen rot bleibt. Scheduler gestoppt von B-0 bis E-3 |
| **§16 (2026-11-03)** | **Planwechsel: der Bot-Anbieter ist wieder MiniMax** (Abo/M Plan, Key `trading-bot-minimax-bot`) — der z.ai-Pay-per-use-Plan (§14) ist für den **Bot** überholt; §14 bleibt für den **Executor** (T22) gültig. **Frist 2026-11-15:** danach muss jedes Profil, das `minimax` nutzt, zurückgeflippt werden (sicherer Default `anthropic`) |

## Bot-Ritual (vor jedem bot-berührenden Edit)

```bash
systemctl --user stop tradingbot-scheduler.service       # bis E-3 deployt ist
ps aux | grep "scheduler.run" | grep -v grep             # Gegenprobe: leer
```

- Recorder, Discovery und WebUI halten keine IG-Session und laufen weiter (Plan T22).
- Den Neustart macht nur **E-3**, die Deploy-Sequenz im Plan.
- **Stop-Timeout (B-9, seit 2026-11-03):** die Scheduler-Unit trägt jetzt
  `TimeoutStopSec=360` (Plan T10) — der SIGTERM wird nach dem laufenden Zyklus-Sleep
  (≤ 300 s) gewürdigt, statt nach 90 s per SIGKILL zu enden. Vor E-3 installiert ist
  die Unit **nicht** (bis dahin gilt der 90-s-Default, Plan D13).
- **Scheduler-HOLD (B-0, seit 2026-10-25, Exec-Session #7):** der Scheduler ist über den
  Stopp hinaus **autostart-fest abgesichert** — systemd `disabled` + Marker
  `data/state/SCHEDULER_HELD` (operator-sticky, Muster `KILL`/`DISCOVERY_ARMED`). Beide
  Repo-Türen respektieren den Marker: `scripts/install_units.sh` enabled die Scheduler-Unit
  bei Hold **nicht**, `scripts/restart-services.sh` startet sie bei Hold **nicht**.
  Zustandsprüfung: `bash scripts/install_units.sh --check` (exit 0 = alles wie erwartet;
  Drift → exit 1). Nicht von Hand `enable`/`start` ohne Freigabe.
  Freigabe (E-3): `bash scripts/install_units.sh --release-hold` → `bash scripts/install_units.sh`
  → `systemctl --user start tradingbot-scheduler.service`.

## Test-Sweep (jede Suite getrennt; Σ = 16 Suites, meta_m1 nicht in Σ)

```bash
cd /home/trading-bot/trading-bot && PY=/home/trading-bot/trading-bot/phase1_broker_wrapper/.venv/bin/python
for d in phase1_broker_wrapper phase2_persistence phase3_external_data phase4_research phase5_execution \
         phase6_debate phase7_reward phase8_scheduler phase9_universe phase10_v3 phase12_data_foundation \
         phase13_live_data phase14_discovery phase15_v4 phase16_activation; do
  echo "$d | $(cd $d && $PY -m pytest tests/ -q -p no:cacheprovider 2>&1 | tail -1)"; done
echo "root | $($PY -m pytest tests/ -q -p no:cacheprovider 2>&1 | tail -1)"
```

| Stand | Σ | Quelle |
|---|---:|---|
| Baseline (Plan-Session, 2026-10-17) | **1964** (+ meta 28) | Plan §2.1 |
| Nach Exec-Session #1 (B-1, 2026-10-19) | **1965** | +1 P1-Test |
| Nach Exec-Session #2 (B-2, 2026-10-19) | **1971** | +4 P12 + 2 P8 |
| Nach Exec-Session #3 (B-3, 2026-10-19) | **1974** | +2 P15 + 1 P8 |
| Nach Exec-Session #4 (B-4, 2026-10-19) | **1978** | +4 P4 |
| Nach Exec-Session #5 (B-5, 2026-10-19) | **1985** | +5 P5 + 2 P8 |
| Nach Exec-Session #6 (B-6, 2026-10-19) | **1988** | +3 P8 |
| Ziel nach Block B / C / D / E-1 | ≥ 1992 / ≥ 2025 / ≥ 2028 / ≥ 2035 | Plan §6 + §14 (+1) + §15 (+9, P4 +5 · P8 +4) |
| Re-Messung Exec-Session #6 (2026-10-19) | **1988** | unverändert, 16/16 grün |
| Nach Exec-Session #7 (Scheduler-Hold, 2026-10-25) | **2000** | +12 root-Tests (root 121 → 133), 16/16 grün |
| Nach Exec-Session #8 (B-7…B-10, 2026-11-03) | **2004** | +2 P8 (271) · +1 P10 (166) · +1 P14 (62), 16/16 grün |
| Nach Exec-Session #9 (Block C, Code C-1…C-6, 2026-11-03) | **2041** | +23 P8 (294) · +10 P4 (177) · +2 P10 (168) · +2 root (135), 16/16 grün |
| Nach Exec-Session #10 (M-1 Provider-Wechsel z.ai → MiniMax, 2026-11-03) | **2042** | +1 P8 (295, Quirks-Pin am MiniMax-Eintrag), 16/16 grün |
| Nach Exec-Session #11 (C-7-Smoke PASS + C-8 Flip 1, 2026-11-03) | **2043** | +1 P8 (296, Default-Pin), 16/16 grün |
| Nach Exec-Session #12 (nächster Block D-1 geschrieben, dokumentarisch) | **2043** | unverändert (kein Code), 16/16 grün |
| Nach Exec-Session #13 (D-1 Token-Budget-Ausnahme, 2026-11-04) | **2046** | +3 P8 (299), 16/16 grün |
| Nach Exec-Session #14 (nächster Block E-1 geschrieben, dokumentarisch) | **2046** | unverändert (kein Code), 16/16 grün |
| Nach Exec-Session #15 (E-1 Report v5, 2026-11-04) | **2053** | +7 P16 (15 → 22), 16/16 grün |
| Nach Exec-Session #16 (E-2 Shakedown-Prereg + MiniMax-Familie-Ausnahme, 2026-11-04) | **2053** | unverändert (P8 299 → 299 — 2 Pins verschärft, keine neue Testzahl), 16/16 grün |

## Phase-17-Status

| Block | Status |
|---|---|
| A Haushalt | ✅ (Session #1) |
| B-0 Scheduler-Stopp + IG-Probe | ✅ (Session #1) |
| B-1 IG-UTC-first | ✅ (Session #1) |
| B-2 Divergenz-Sampler | ✅ (Session #2) |
| B-3 Promotion-Bridge (3 Nahtfehler) | ✅ (Session #3) |
| B-4 Abschneiden sichtbar (D4) | ✅ (Session #4) |
| B-5 Monitor-Re-Adoption (D5, T8) | ✅ (Session #5) |
| B-6 Breaker Worst-Case (D6, T9) | ✅ (Session #6) |
| B-7 Abstain-Naht (D7) | ✅ (Session #8) — `record_id`-Durchreich + Enrich-vor-Klassifikation, P8 269 → 271 |
| B-8 Paper-Logstufen (D8, T11/E4) | ✅ (Session #8) — 4× `critical` → `warning`, P10 165 → 166 |
| B-9 Stop-Timeout (D13, T10) | ✅ (Session #8) — `TimeoutStopSec=360`, Unit verifiziert + installiert (holdfest) |
| B-10 Discovery-Beleg + Wrapper-Text (D12) | ✅ (Session #8) — append-only Logzeile je Zyklus, P14 61 → 62 |
| **Block B (Mess-/Geldpfad-Defekte) — gesamt** | ✅ **abgeschlossen** (Sessions #1–#8): alle 13 Befunde D1–D13 behandelt, Σ **2004** |
| C LLM-Austausch | 🔄 **Code C-1…C-6 ✅** (Session #9, Σ **2041**): Provider-Register (9 Einträge) · `_build_llm` (eine Bau-Funktion) · `_debate_config` · Profil-Check beim Start · Preflight-Key-Check · `LLM_UNAVAILABLE` · Key-/Smoke-Skript. **M-1 ✅** (Session #10, Σ **2042**): Provider-Wechsel auf **MiniMax** (Profil `research_m3`/`all_m3`, Modell `MiniMax-M3`, Preiszeile `(0.0,0.0)`, `budget_exempt_models=("MiniMax-M3",)`, Quirks `max_completion_tokens`). **C-7 ✅** (Session #11): Familien-Smoke **beide Modelle PASS** (`MiniMax-M3` 3.62 s / `stop` / 751→164 · `MiniMax-M3.1-Flash` PASS, reines JSON) — `json_object` wird von MiniMax **akzeptiert** (kein 400). **C-8 Flip 1 ✅** (Session #11, Σ **2043**): `llm_profile = "research_m3"` — **nur** Research → MiniMax-M3, alle anderen Rollen Anthropic; **inert bis E-3** (Hold). **Offen: Flip 2 (`all_m3`, nach Shakedown) · Modellwahl vertagt (M3 vs. M3.1-Flash)** |
| Scheduler-Hold (B-0 → E-3) | ✅ aktiv (2026-10-25): systemd `disabled` + `data/state/SCHEDULER_HELD`, beide Repo-Türen (Installer, Restart-Helper) respektieren den Marker — **Freigabe erst in E-3** (`bash scripts/install_units.sh --release-hold`) |
| D Token-Budget | 🔄 **D-1 ✅** (Session #13, 2026-11-04, Σ **2046**): die Budget-Ausnahme ist im Code — `scheduler/budget.py::consumed_today()` überspringt Records von `budget_exempt_models` (MiniMax-M3 ⇒ Abo-Kontingent, „measured, not capped"), `webui/api.py::/api/token_usage` meldet sie separat als `exempt_tokens` (Kosten/Calls zählen weiter alle Records). **+3 P8-Tests** (296 → 299). **E-1 ✅** (Session #15): der **dritte** Zählort ist geschlossen — `autonomy_report.py::llm_usage_per_day()` kennt die Ausnahme jetzt (`exempt_tokens`/`exempt_calls`, **auch** in der `exhausted_at`-Summation übersprungen). **Report-Zahl = Budget-Zahl.** **D-2** = Nikinger-Entscheidungspunkt (K6-Einheit, nach dem Shakedown, **kein Code**) |
| E Test-Fundament | 🔄 **E-1 Definition ✅** (Session #14: **Plan §18** — Report v5: `llm_usage_per_day` trägt `exempt_tokens`/`exempt_calls` (D-1-Fortsetzung) + v5-Evaluatoren K2/K5/K7/K9/K10/K11; Anker re-verifiziert (**null Drift**), v4-Regressions-Baseline live gemessen, **2 Voraussetzungen** gemessen: v5-K2/K11 sind **erst nach E-3** messbar). **E-1 ✅** (Session #15, 2026-11-04, Σ **2053**): Report v5 im Code — `--prereg {v4,v5}` (Default v4, verdikt-identisch) · `llm_usage_per_day` mit `exempt_models` (D-1-Fortsetzung) · `evaluate_k2_v5` (Discovery-Zyklen statt Proxy) · `evaluate_k6_v5` · `evaluate_k7_v5` (Profil-Pin, fail-closed) · `evaluate_k9` (Journal, NA ohne Datei) · `evaluate_k10` (Instinct-Bridge, NA ohne CLOSE) · `evaluate_k11` (Divergenz) + `count_discovery_cycles_per_day` · K5-`by_logger`/`deal_related` · CLI `--journal-file`/`--expect-llm-profile`/`--exempt-model`. **+7 P16-Tests** (15 → 22), Negativ-Beweis erbracht. **Offen:** E-3 (Deploy) → E-4 (Shakedown) → E-5 (Auswertung + D-2/Flip-2-Entscheidungen + Prereg v5) → E-6 (Closeout). **E-2 ✅** (Session #16, 2026-11-04): die **Shakedown-Vorregistrierung** ist geschrieben — [`PHASE17_SHAKEDOWN_PREREGISTRATION.md`](./PHASE17_SHAKEDOWN_PREREGISTRATION.md), `status: locked` nach **T23-Freigabe** (Nikinger, 2026-11-04); alle gepinnten Werte live gegen den Code geprüft (**null Drift**), Fenster = die ersten zwei Handelstage **nach** dem E-3-Start, Aktiv-Block wird am E-3-Tag **eingetragen**; **Nikinger-Entscheidung „ausnahme alle minimax Modelle“** ⇒ 1 Code-Commit in P8 (`budget_exempt_models` = MiniMax-Familie). ⚠ v5-Verdikte sind **erst nach E-3** belastbar (K2/K11 brauchen die Deploy-Belege) |

## Forward-Agenda (zwischen den Blöcken B-5..B-10 und C)

| # | Thema | Status | Link |
|---|---|---|---|
| **C2 — Provider-Plastizität** | Endpoint-Abstraktion für alle „gängigen" Provider (Anthropic + OpenAI + DeepSeek + Qwen + GLM + …). Nikinger-Entscheidung 2026-10-19 („soll mit sämtlichen gängigen Endpunkten funktionieren"). | ✅ **Plan §15** (2026-10-19, Plan-Session Opus 5.5) — ändert C-1/C-3/C-4/C-6/C-7 in place; Q1–Q8 entschieden | [`../docs/concepts/phase17_testbed_plan.md` §15](../docs/concepts/phase17_testbed_plan.md) |

> **Update 2026-10-19 (Plan-Session):** C2 ist jetzt **Teil von Block C** (Plan §15, Nikinger Q2) — kein eigener Block, keine Phase 18. Σ-Ziel Block C ≥ **2025** (statt 2016). Der Absatz unten ist historisch.

Diese Forward-Agenda ist **kein Block** der Phase 17 — sie ist „Material für eine Opus-Miniplan-Session nach den Blöcken B-5..B-10", wie es der Nikinger mit seiner Entscheidung intendiert hat. Eine spätere Session `Exec-Session #5+` wird je nach Nikingers Q2-Antwort entweder einen Plan-§-Anker (neuer Block C2 in Phase 17) oder einen eigenständigen Phasenkopf Phase 18 schreiben.

## Executor-Evaluation (Plan §14.2 — je Exec-Session eine Zeile)

| Session | Datum | Modell (`zai-coding-plan/…`) | Steps | Kontingent vorher → nachher (z.ai-Dashboard) | Tests | Rückfall | Notiz |
|---|---|---|---|---|---|---|---|
| #16 (E-2 Shakedown-Prereg) | 2026-11-04 | MiniMax-M3-Fallback (Plan §14.2) — kein z.ai-Modell heute in Verwendung | **E-2**: Shakedown-Vorregistrierung (P17-Doku) + MiniMax-Familien-Ausnahme (P8, 1 Config-Zeile) | n/a | Σ 2053 → **2053** (P8 299 → 299, 2 Pins verschärft, 16/16 grün) | — | **Anker null Drift** (alle §19-E-2c-Anker am 2026-11-04 live nachgemessen: `run.py:47-49/60-62/72-74/78-80/156` · `config.py:149/154` · `autonomy_report.py` 9 Evaluatoren + 4 CLI-Flags + 5 Konstanten · Unit `ExecStart` ohne Flags · v4-Format-Vorbild). **T23-Freigabe des Nikinger** (2026-11-04) mit **einer** Änderung gegenüber §19: „ausnahme alle minimax Modelle" ⇒ `budget_exempt_models = ("MiniMax-M3", "MiniMax-M3.1-Flash")` (Variante A, Exakt-Match; Prefix-Regel vom Nikinger verworfen). **Negativ-Beweis:** mit dem Pre-Code-`config.py` sind beide P8-Pins rot. **Kein** Code in P16 — die Report-Seite liest nur die Ausnahmeliste (`--exempt-model` ist repeatable, beide IDs werden mitgegeben). **Aktiv-Block bleibt bis E-3 leer** (D1/D2/HEAD/offene Position stehen erst nach dem Deploy fest) |
| #15 (E-1 Report v5) | 2026-11-04 | MiniMax-M3-Fallback (Plan §14.2) — kein z.ai-Modell heute in Verwendung | **E-1**: Report v5 (`autonomy_report.py`, P16) — `llm_usage_per_day` mit `exempt_models` + 6 v5-Evaluatoren + `count_discovery_cycles_per_day` + K5-`by_logger` + CLI-Flags | n/a | Σ 2046 → **2053** (+7 P16: 22, 16/16 grün) | — | **Anker null Drift** (alle 11 §6-E-1-Anker, vor der Implementierung re-verifiziert) + **alle Quellen live geprüft** (Discovery-Beleg `run.py:211/225/272` · Start-Zeile `run.py:206-214` · Bridge-Texte `bridge.py:125/146/230/244` · Divergenz `heartbeat.py:384` + `observability.py:140` · Live-DB `instincts` 29/29 ohne Evidenz). **Regression-AK erfüllt:** v4-Baseline vor/nach dem Fix **identisch** (FAIL K1/K5/K6 · PASS K2/K3/K4/K7/K8). **Negativ-Beweis:** mit dem pre-E-1-Code sind genau die 7 neuen Tests rot, die 15 Bestandstests grün. **5 fail-closed-Entscheidungen** (F8-Klasse): K7 ohne Start-Zeile im Fenster ⇒ FAIL · K9 ohne Zeitstempel ⇒ FAIL · K2/K11 ohne Handelstag ⇒ NA · K10 ohne CLOSE ⇒ NA · Ausnahmeliste lazy + `--exempt-model` schlägt. **v5-Lauf vor E-3 = false FAILs** (K2/K11 brauchen den Deploy) |
| #14 (nächster Block geschrieben) | 2026-11-04 | MiniMax-M3-Fallback (Plan §14.2) — kein z.ai-Modell heute in Verwendung | **Plan §18 = Block E / E-1** ausführbar geschrieben (Doku, **kein Code**) | n/a | Σ **2046** (unverändert — dokumentarische Session) | — | **Anker re-verifiziert** (2026-11-04): alle 11 §6-E-1-Anker in `phase16_activation/scripts/autonomy_report.py` **null Drift** (P16 seit der Plan-Session unangefasst). **Live gemessen:** v4-Baseline `--from 2026-09-30 --to 2026-10-13 --summary` ⇒ FAIL K1/K5/K6 · PASS K2/K3/K4/K7/K8 (deckt sich mit §6 E-1 + Handover §2). **2 Voraussetzungen gefunden:** v5-K2 (`discovery cycle`-Zeilen: **0**, Discovery-Daemon läuft seit 11-01, also vor B-10) und v5-K11 (`divergence_ok`/`quote_divergence`: **0**, Scheduler im HOLD) sind **erst nach E-3** messbar ⇒ ein v5-Lauf vor E-3 wäre ein false FAIL (F8-Klasse). AK: P16 15 → 22, Σ ≥ 2053 |
| #13 (D-1) | 2026-11-04 | MiniMax-M3-Fallback (Plan §14.2) — kein z.ai-Modell heute in Verwendung | D-1: Token-Budget-Ausnahme an zwei P8-Zählstellen (`scheduler/budget.py` + `webui/api.py`) | n/a | Σ 2043 → **2046** (+3 P8, 16/16 grün) | — | **Anker unverändert** (2026-11-04): `scheduler/budget.py` `consumed_today()` Z. 168–190 · `webui/api.py` `/api/token_usage` Z. 277–320 — beide wie in §17 D-1 notiert. **Negativ-Beweis:** Budget- und WebUI-Test mit dem pre-D-1-Code **rot** (`test_budget_counts_non_exempt_records` ist ein Regressions-Pin und per Definition auch vorher grün). **Dritter Zählort** (`autonomy_report.py::llm_usage_per_day()`) bleibt **E-1** (Block E) — der Report kennt die Ausnahme erst ab E-1. **D-2** = Nikinger-Entscheidungspunkt (K6, kein Code) |
| #12 (nächster Block geschrieben) | 2026-11-03 | MiniMax-M3-Fallback (Plan §14.2) — kein z.ai-Modell heute in Verwendung | **Plan §17 = Block D / D-1** ausführbar geschrieben (Doku, **kein Code**) | n/a | Σ **2043** (unverändert — dokumentarische Session) | — | **Anker re-verifiziert** (2026-11-03): `scheduler/budget.py` `consumed_today()` Z. 176–183 · `webui/api.py` `/api/token_usage` Z. 277–308 — beide **unverändert** gegenüber §6 D-1; der dritte Zählort (`autonomy_report.py::llm_usage_per_day` Z. 369 ff.) gehört zu **E-1/Block E**, nicht in D-1. 3 Testnamen fest, AK **P8 296 → 299** / **Σ ≥ 2046**. **D-2** = Nikinger-Entscheidungspunkt (K6, kein Code). **Session beendet + Push** (8 Commits der Phase-17-Folge) |
| #11 (C-7-Smoke + C-8 Flip 1) | 2026-11-03 | MiniMax-M3-Fallback (Plan §14.2) — kein z.ai-Modell heute in Verwendung | C-8 Flip 1: `llm_profile = "research_m3"` (P8) | n/a | Σ 2042 → **2043** (+1 P8, 16/16 grün) | — | **C-7-Smoke (Operator) PASS**: `MiniMax-M3` (valid abstain, in 751 / out 164, `finish_reason=stop`, **3.62 s**, Denk-Block inline → C-3-Strip belegt) · `MiniMax-M3.1-Flash` (valid abstain, reines JSON, Reasoning getrennt). ⇒ MiniMax akzeptiert `response_format: json_object` (**kein 400** — §15.7 Nr. 21 teilweise geklärt). **Flip 1 = eine Zeile**, wirkt erst mit **E-3** (Hold), Rollback = eine Zeile. Commit `2ee73e6` + Doku-Commit |
| #10 (M-1 Provider-Wechsel) | 2026-11-03 | MiniMax-M3-Fallback (Plan §14.2) — kein z.ai-Modell heute in Verwendung | M-1 Provider-Register z.ai → **MiniMax** (P8 + P4) | n/a | Σ 2041 → **2042** (+1 P8, 16/16 grün) | — | **Planwechsel** (Nikinger 2026-11-03): der Bot-LLM-Anbieter ist wieder der **MiniMax-Abo-Key** (M Plan), nicht z.ai Pay-per-use. Ein Commit (`4d57d99`) + Doku-Commit. **Frist 2026-11-15** — danach zurückflippen. Modellwahl **MiniMax-M3** (Benchmark-Vergleich: frontier-Klasse, BrowseComp 83.5 > Opus 4.7 79.3; PostTrainBench #3 hinter Opus 4.7/GPT-5.5) |
| #9 (Block C, Code) | 2026-11-03 | MiniMax-M3-Fallback (Plan §14.2) — kein z.ai-Modell heute in Verwendung | C-1 Provider-Register (P8) · C-2 Config-Defaults (P8) · C-3 OpenAI-Compat-Härtung + GLM-Preiszeilen (P4) · C-4 `_build_llm` + `_debate_config` + Profil-Check + Preflight (P8) · C-5 `LLM_UNAVAILABLE` (P4+P8+P10) · C-6 Key-/Smoke-Skript (root+P4) | n/a | Σ 2004 → **2041** (+37: P8 +23 · P4 +10 · P10 +2 · root +2; Plan-AK Block C Σ ≥ 2025 ✓, P4 ≥ 177 ✓, P8 ≥ 292 ✓, P10 ≥ 167 ✓) | — | **6 Commits**: `698e9ea` (C-1) `145e80e` (C-2) `4190802` (C-3) `1a61229` (C-4) `edeeab8` (C-5) `6d1f69d` (C-6). **AK C-4 erfüllt:** `LLMClient(` → 1 Treffer, `OpenAICompatLLMClient(` → 1 Treffer in `wiring.py` (beide in `_build_llm`). **Abweichung:** C-4 lieferte **+7** P8-Tests statt +5 (AK ist eine Untergrenze; 2 zusätzliche Tests: unbekanntes Profil wirft vor jedem Client · Client-Oberfläche). **C-7 wartet auf den Nikinger** (Key `trading-bot-zai-bot` im Keyring **nicht** vorhanden — gemessen) |
| #8 (B-7…B-10) | 2026-11-03 | MiniMax-M3-Fallback (Plan §14.2) — kein z.ai-Modell heute in Verwendung | B-7 Abstain-Naht (D7, P8) · B-8 Paper-Logstufen (D8, P10) · B-9 Stop-Timeout (D13, P16-Unit) · B-10 Discovery-Beleg (D12, P14) | n/a | Σ 2000 → **2004** (+4: P8 +2 · P10 +1 · P14 +1 ✓ Plan-AK exakt; B-9 +0, Unit-Test läuft in E-3) | — | **4 Commits, ein Block-Teil**: `5d02e7c` (B-7) · `02faf44` (B-8) · `f221f3c` (B-9) · `4eefbda` (B-10). **Anker-Drift nur bei B-7** (Plan Z. 758–760 → heute Z. 841–856, ≈ +83 Zeilen > +60-Schwelle → im Phasenkopf dokumentiert, Plan bleibt 📕-Snapshot); B-8/B-9/B-10 **null Drift**. Negativ-Beweis je Test: mit dem pre-Fix-Code rot (stash), mit dem Fix grün. B-9 brachte eine **Host-Notiz**: getrackte Unit über `install_units.sh` installiert (Datei-Kopie + daemon-reload), damit `--check` exit 0 bleibt — Hold unangetastet (Unit bleibt `disabled`+`inactive`, Start erst in E-3) |
| #6 (B-6) | 2026-10-19 | MiniMax-M3-Fallback (Plan §14.2) — kein z.ai-Modell heute in Verwendung | B-6 Breaker Worst-Case (D6, T9, P8) | n/a | Σ 1985 → **1988** (+3, P8 +3 ✓ Plan-AK exakt) | — | Plan-Anker Z. 1009–1016 (Closure `realized_pnl_today`) ist zwischen Plan-Session 2026-10-17 und Session #6 auf Z. 1066–1073 gewandert (~$+57$ Zeilen durch Folge-Commits in P15/P8); **kleiner Drift**, semantisch unverändert. Neuer Modul-Helper `_realized_pnl_today` direkt nach `_sampler_due` einsortiert (B-Block-Helper-Section). Test-File `tests/test_wiring_breaker.py` neu — DB-Path `:memory:` (sqlite3 in-memory, ein Connection über Test-Lifetime, keine `tmp_path`-Notwendigkeit) |
| #5 (B-5) | 2026-10-19 | MiniMax-M3-Fallback (Plan §14.2) — kein z.ai-Modell heute in Verwendung | B-5 Monitor-Re-Adoption (D5, T8, P5 + P8) | n/a | Σ 1978 → **1985** (+7, P5 +5 + P8 +2 ✓ Plan-AK exakt) | — | B-5 ist die letzte Single-Commit-Block: 1 Commit (154f460) in P5+P8. Bit-Identität via `getattr(self._executor, "resume_open_position", None)` — alle Bestands-Fakes unverändert grün |
| — | — | — | — | — | — | — | Der 5.2-Quirk: bei Flash-ähnlichem Kontingent-Verbrauch einen vergleichbaren Step mit `glm-5.2` fahren |

**Review-Gate vor E-3 (AK22):** ⏳ (Claude-Code-Session, Anthropic; Schwerpunkte B-5, B-6, B-7, B-8, B-9, B-10, C-4, B-3, B-2)

> **Integration des Executors = eurofyx-fleet, getrennt vom Plan (Plan §14.8, Nikinger 2026-10-18).** Die Fleet richtet ein: OpenCode-Provider `zai-coding-plan` (Auth), Modell, Neustart von `opencode.service`, MiniMax-Rückweg. Diese Exec-Session fasst `~/.config/opencode/`, `auth.json` und `opencode.service` **nicht** an. A-0 startet erst, wenn die Fleet „OpenCode + z.ai bereit" meldet.

---


---

## Session stopped — 2026-11-04 (Exec-Session #16 — **E-2 ausgeführt**: Shakedown-Vorregistrierung geschrieben (T23-Freigabe des Nikinger) + MiniMax-**Familie**-Ausnahme im Code; 1 Code-Commit in P8 + 1 Doku-Commit, Σ **2053** unverändert)

> **Auftrag:** Nikinger (Web-Chat, 2026-11-04): Phase 17 fortsetzen. Der Special-Task verweist auf Plan §19 (**E-2 = Shakedown-Vorregistrierung**) mit dem **T23-Gate**: der Commit der Prereg-Datei wartet auf die Freigabe der gepinnten Werte; D1/D2 sind erst nach E-3 bekannt. **Plan war detailliert genug** (§19 mit vollständigem Inhalts-Entwurf + live geprüften Ankern) → **atomar abgearbeitet**, kein Re-Planen nötig.
> **Bot-Ritual (Session-Start + Session-Ende verifiziert):** Scheduler `disabled` + `inactive` (Hold-Marker `data/state/SCHEDULER_HELD`), kein `scheduler.run`-Prozess, `install_units.sh --check` exit 0, Recorder/Discovery/WebUI `enabled` + `active` (unangetastet). **Kein Neustart, kein Netz-Call, kein Live-Key** durch den Agenten.
> **Cross-Phase-Freigabe:** E-2 = **P17-Doku** + **P8** (eine Config-Zeile, vom Nikinger ausdrücklich entschieden: „ausname alle minimax Modelle" → Variante A „Familie aufzählen"). Kein Touch in P1/P4/P5/P10/P12/P14/P15/P16.

### Completed — diese Exec-Session (1 Code-Commit + 1 Doku-Commit)

| # | Commit | Phase | Inhalt |
|---|---|---|---|
| 1 | `fa02a6a` | P8 | **MiniMax-Familien-Ausnahme** (`scheduler/config.py:150-160`): `budget_exempt_models = ("MiniMax-M3", "MiniMax-M3.1-Flash")` — Nikinger-Entscheidung 2026-11-04 („ausname alle minimax Modelle", Variante A = Familie aufzählen, Exakt-Match beibehalten). Zwei Pins verschärft: `test_budget.py::test_budget_ignores_exempt_model_records` prüft jetzt **beide** IDs, `test_config.py::test_llm_profile_default_is_research_m3_with_the_minimax_model_exempt` pinnt das Tupel. **Negativ-Beweis:** mit dem Pre-Code-`config.py` sind **beide** Tests rot. **P8 299 → 299** (keine neue Testzahl — die Pins sind verschärft), Σ **2053** unverändert. |
| 2 | (dieser Commit) | P17-Doku + root | **E-2 — die Vorregistrierung.** `phase17_testbed/PHASE17_SHAKEDOWN_PREREGISTRATION.md` (**NEU**, `status: locked` nach T23-Freigabe) + **eine** `docs/INDEX.md`-Zeile **im selben Commit** + Phasenkopf (Block-E-Zeile, Σ-Tabelle, Executor-Zeile #16, dieser Block + Rotation #15 → `SESSIONS_ARCHIVE.md`, `down:`-Link auf die neue Datei) + root-`CLAUDE.md` (Banner + Phasen-17-Zeile) + `ROADMAP.md`. **Kein Code** in diesem Commit. |

### Was E-2 festhält (Inhalt der Vorregistrierung)

| Abschnitt | Inhalt |
|---|---|
| **BLUF** | Fenster = Tag 1 = erster voller Handelstag **nach** dem E-3-Start, Tag 2 = der nächste Handelstag; Start-Zeitstempel = die `starting scheduler daemon`-Zeile aus E-3. Zweck = **kein** Autonomie-Test, sondern **2-Tage-Prüfstand-Fenster** (B-1…B-10, C-1…C-8, D-1, E-1 live belegen, inkl. der neuen Kriterien K9/K10/K11). Profit bleibt **kein** Kriterium. |
| **Gepinnte Werte** (live am 2026-11-04 gegen den Code geprüft, **null Drift**) | `account=demo` (`run.py:156`, hart) · `max_trades=5` (`run.py:72-74`) · `daily_loss_cap=1800.0` (`run.py:47-49`) · `cycle=5min` (`run.py:78-80`) · `llm_profile=research_m3` (`config.py:149`) · `daily_token_budget=300 000` (`run.py:60-62`, nur Nicht-Ausnahme-Modelle) · **Ausnahme: alle MiniMax-Modelle** (`config.py:154`: `MiniMax-M3` + `MiniMax-M3.1-Flash`) |
| **Kriterien** (alle PASS nötig; **K3/K4 nur berichtet**) | K1 ≤ 2 Starts je Dienst · K2-v5 je Handelstag ≥1 Scheduler-Event + ≥1 Bar + ≥1 Discovery-Zyklus · K5 ≤ 5 CRITICALs je 24 h nach OPEN · K6-v5 Budget nie vor 17:30 erschöpft · K7-v5 Caps + `llm_profile=research_m3` (ohne Start-Zeile ⇒ FAIL) · K8 Liveness je Handelstag · K9 ≤ 10 Restart-Jobs je Berlin-Tag · K10 0 Bridge-CRITICALs + Evidenz je neuer Instinct (NA ohne CLOSE) · K11 ≥ 1 Divergenz-Event je Handelstag |
| **Erlaubte Operator-Ereignisse** | (a) Re-Adoption-Probe **einmal** (nur bei offener Position; erwartet `resume: re-adopting open position …` + regulärer Close) = das „+1" in K1 · (b) Tagesexport Journal (der Export selbst ist kein Ereignis) · **ein VM-Host-Reboot = K1 FAIL** (T10). Alles andere ist ein Befund. |
| **FAIL-Regel** | Befund → Fix-Step in Phase 17 → **neue** Vorregistrierung `-S2` → neuer Lauf. **Kein** Kriterium wird gelockert (T3/T23). |
| **§F2 Flip-2-Tag** | 1 Handelstag `all_m3`, dieselben Kriterien, K7 gegen `all_m3`, Abbruch + Revert nach C-8 — **jetzt mit vorregistriert** (sonst wäre der Flip-2-Tag ein Lauf ohne vorab festgelegte Kriterien). |
| **Report-Befehl** | Journal-Export (E-4) → `autonomy_report.py --prereg v5 --from <D1> --to <D2> --summary --journal-file … --expect-llm-profile research_m3 --exempt-model MiniMax-M3 --exempt-model MiniMax-M3.1-Flash --reports-dir data/reports` |
| **Aktiv-Block** | Vom Operator **am E-3-Tag eingetragen** (Eintragung, kein Edit): Start-Zeitstempel · D1 · D2 · HEAD-Commit · offene Position bei Start · Re-Adoption-Probe |

### Die eine Änderung gegenüber dem Plan-Entwurf §19 (Nikinger-Entscheidung)

- **Der Nikinger hat die Token-Ausnahme von `MiniMax-M3` auf „alle MiniMax-Modelle" erweitert** (2026-11-04, Frage in dieser Session). Umgesetzt als **Familien-Aufzählung** `("MiniMax-M3", "MiniMax-M3.1-Flash")` in `SchedulerConfig.budget_exempt_models` (P8, 1 Zeile) — das Matching ist im Code überall **Exakt-Match** (`budget.py:187`, `webui/api.py:302`, `autonomy_report.py:494/509`, `llm_profiles.py:377`); eine Prefix-Regel wäre ein Cross-Phase-Edit über **P16** hinaus gewesen (vom Nikinger verworfen).
- **Warum der Code mit muss:** die Vorregistrierung pinnt **Werte** — wenn der Code nur ein Modell ausnimmt, wäre das **Dok-vs-Code-Drift** (genau der Defekt-Typ, den Phase 17 abstellt). Der Startup-Check `check_llm_profile` deckt den Rest ab: ein **künftiges** MiniMax-Modell ohne Eintrag ⇒ der Start wird verweigert und die fehlende ID wird **genannt** (kein stilles Zählen gegen das Cap).
- **Bekannte Lücke (kein Blocker):** `MiniMax-M3.1-Flash` hat **noch keine Preiszeile** in P4 (`research/models.py`) ⇒ ein Modellwechsel M3 → Flash (Entscheidung E-5) bräuchte zusätzlich eine Preiszeile `(0.0, 0.0)` (Abo), sonst verweigert `check_llm_profile` den Start. **Bis dahin bleibt M3 aktiv.**

### Gemessen (Host 202, Session-Ende)

| | Wert |
|---|---|
| `is-enabled` / `is-active` tradingbot-scheduler | `disabled` / `inactive` (Hold unangetastet) |
| `ps aux | grep scheduler.run` | 0 Treffer |
| `bash scripts/install_units.sh --check` | exit 0 |
| Σ (16 Suiten + root) | **2053** (P8 299 unverändert — die Ausnahme-Familie steckt in den verschärften Pins, keine neue Testzahl), 16/16 grün |
| `check_doc_rotation.py --strict` | exit 0 |

### Next (der übernächste Block)

- **E-3** (Hold-Freigabe + Deploy, **Operator**) — macht den Flip 1 wirksam und erzeugt die K2/K11-Belege. Ablauf: Plan §6 E-3 (4 Dienste stoppen · `bars.sqlite` sichern + `DELETE FROM bars WHERE source='ig'` (T14, ≈ 3 730 Zeilen) · `instincts` mit `[legacy-p16] ` markieren (T12, 29 Zeilen) · `install_units.sh` + `daemon-reload` · 4 Units starten). **Day-0-Checks** (Plan §6 E-3) + zusätzlich `grep -c "discovery cycle" data/state/run_discovery.log` > 0.
- **Review-Gate AK22** (Claude-Code-Session, Anthropic) ist **vor** E-3 fällig — ⏳ offen.
- **E-4** (Shakedown, 2 Handelstage, Operator — Journal-Export) → **E-5** (Auswertung + **D-2** K6-Einheit + **Flip-2**-Entscheidung + **Modellwahl** M3 vs. Flash + Prereg v5) → **E-6** (Closeout).
- **D-2** bleibt ein **Nikinger-Entscheidungspunkt ohne Code** (K6-Einheit, nach dem Shakedown).
- **Frist 2026-11-15** — Abo-Key/Endpoint: jedes `minimax`-Profil vor dem Datum zurückflippen (Default `anthropic`).

### Open questions / blockers

- **Review-Gate vor E-3 (AK22)** weiterhin ⏳ (Schwerpunkte B-5…B-10, C-4…C-6, B-3, B-2, **E-1**).
- **Modellwahl vertagt** (M3 vs. M3.1-Flash) — Profil und Modell sind getrennte Datenstellen; die Flash-Preiszeile fehlt noch (siehe oben).
- **K9-Regex unbewiesen:** der exakte Journal-Text eines Auto-Restarts (`Scheduled restart job, restart counter is at N`) existiert im Repo noch nicht (Plan §9 #8) — die erste echte Vorkommen muss gegen das Muster geprüft werden (E-4).
- **Frist 2026-11-15** (Abo) — im Phasenkopf + Plan §16 dokumentiert.

### Session-end-Hinweis

- **Σ 2053** (16 Suiten + root). meta_m1 informativ, nicht in Σ.
- **Diese Session:** 1 Code-Commit (P8) + 1 Doku-Commit.
- **Kern-Erkenntnis (neu):** eine Vorregistrierung pinnt **Werte** — und gepinnte Werte müssen **im Code stehen**, sonst ist die Vorregistrierung ein Dokument über einen Zustand, den es nicht gibt. Genau das hat der Nikinger beim Review bemerkt (Ausnahme: eine Modell-ID → die ganze Familie).



---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
