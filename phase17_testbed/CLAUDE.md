---
status: live
purpose: PHASE-HEAD, Phase 17 (Prüfstand) — 🔄 eröffnet 2026-10-17 (Plan-Session, Opus 5.5). Keine neuen Features. Tiefe Härtung des Bestehenden — vier Phase-16-PASS-Blocker + drei neu gemessene stille Totalausfälle zu, LLM pro Rolle austauschbar (Research zuerst auf **MiniMax-M3 über die MiniMax-Abo-API** — Planwechsel 2026-11-03, Plan §16), Report + Vorregistrierung v5 als Fundament für die ausgiebigen Tests. Executor: offener Test GLM in OpenCode (§14).
read-when: jede Phase-17-Exec-Session — zuerst diesen Kopf, dann den `## Session stopped`-Block, dann den Plan
detail: L1
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase17_testbed_plan.md               # 📕 der Plan (T1–T24, D1–D13, Blöcke A–E, AK1–AK21, §8 Fehlgriffe, §9 Verify)
  - ./provider_plasticity/                                  # 🔄 Working-Notes Provider-Plastizität (2026-10-19, 4 Notizen: 01 Decision T25–T28 · 02 Current-State · 03 Opus-Brief · 04 Open Questions Q1–Q8)
  - ../phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md     # 📕 Vorgänger-Handover (§4 PASS-Blocker, §5 E1–E8)
  - ../phase16_activation/scripts/autonomy_report.py       # Report-Skript, Block E erweitert es in place (--prereg v5)
  - ./SESSIONS_ARCHIVE.md                                  # rotierte Session-Blöcke (L3, newest-first)
updated: 2026-11-04 (Exec-Session #14 — **der nächste Block geschrieben**: Plan §18 = Block E / E-1 (Report v5: Token-Budget-Ausnahme im Report + v5-Kriterien K2/K5/K7/K9/K10/K11), Anker re-verifiziert (null Drift) + 2 live gemessene Voraussetzungen; **dokumentarische Session, kein Code** — Σ unverändert **2046**; Session-Ende + **Push**) | 2026-11-04 (Exec-Session #13 — **D-1 ausgeführt** (Plan §17): Token-Budget-Ausnahme an `budget_exempt_models` — `scheduler/budget.py` (Exempt-Records überspringen) + `webui/api.py` (`exempt_tokens` separat), 1 Code-Commit + 1 Doku-Commit, Σ 2043 + 3 = **2046** grün; D-2 bleibt Nikinger-Entscheidungspunkt (K6-Einheit, **kein Code**); Report-Zählort folgt in E-1) | 2026-11-03 (Exec-Session #12 — **der nächste Block geschrieben**: Plan §17 = Block D / D-1 (Budget-Ausnahme an zwei P8-Zählstellen, Anker re-verifiziert) + D-2 als Entscheidungspunkt; **dokumentarische Session, kein Code** — Σ unverändert **2043**; Session-Ende + **Push**) | 2026-11-03 (Exec-Session #11 — **C-7-Smoke PASS (Operator: beide MiniMax-Modelle PASS)** + **C-8 Flip 1** ausgeführt: `llm_profile = "research_m3"` (nur Research → MiniMax-M3), 1 Code-Commit + 1 Doku-Commit, Σ 2042 + 1 = **2043** grün; **inert bis E-3** (Hold); Flip 2 `all_m3` bleibt gegated) | 2026-11-03 (Exec-Session #10 — **Planwechsel z.ai → MiniMax** (Abo/M Plan, Nikinger-Entscheidung 2026-11-03): M-1 = Provider-Register umgestellt (Profil `research_m3`/`all_m3`, Modell `MiniMax-M3` mit `max_tokens=8192`, Preiszeile `(0.0, 0.0)`, `budget_exempt_models=("MiniMax-M3",)`, Quirks `max_completion_tokens`), 1 Code-Commit + 1 Doku-Commit, Σ 2041 + 1 = **2042** grün; **C-7 wartet auf den Nikinger** (Key `trading-bot-minimax-bot` + Familien-Smoke); **Frist 2026-11-15**) | 2026-11-03 (Exec-Session #9 ENDE — **Block C (Code C-1…C-6) abgeschlossen**: Provider-Register + LLM-Austausch (`_build_llm`) + `LLM_UNAVAILABLE` + Key-/Smoke-Skript, 6 Commits, Σ 2004 + 37 = **2041** grün; **C-7 wartet auf den Nikinger** (Bot-Key `trading-bot-zai-bot` fehlt, Familien-Smoke)) | 2026-11-03 (Exec-Session #8 ENDE — **Block B abgeschlossen**: B-7 Abstain-Naht + B-8 Paper-Logstufen + B-9 Stop-Timeout + B-10 Discovery-Beleg, 4 Code-Commits, Σ 2000 + 4 = **2004** grün; Scheduler `disabled`+`inactive` (Hold) + 3 Units laufen weiter) | 2026-10-25 (Exec-Session #7 ENDE — Scheduler-Hold: systemd-Autostart aus + getrackter Repo-Guard `data/state/SCHEDULER_HELD`, +12 root-Tests, Σ **2000**) | 2026-10-19 (Exec-Session #6 ENDE — B-6 Breaker Worst-Case, 1 Commit in P8, Σ 1985 + 3 P8-Tests = **1988** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #5 ENDE — B-5 Monitor-Re-Adoption, 1 Commit in P5+P8, Σ 1978 + 5 P5 + 2 P8 = **1985** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Plan-Session §15 Provider-Plastizität — Forward-Agenda C2 → Plan §15, Σ-Ziele C/D/E-1 +9, Σ 1978 re-gemessen) | 2026-10-19 (Exec-Session #4 ANSCHLUSS — `provider_plasticity/` Working-Notes-Set angelegt (kein Plan, Input für Opus-Miniplan-Session; 5 INDEX-Einträge); Nikinger-Entscheidungen Q1–Q8 ausstehend) | 2026-10-19 (Exec-Session #4 ENDE — B-4 Abschneiden sichtbar, 1 Commit in P4, Σ 1974 + 4 P4-Tests = **1978** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #3 ENDE — B-3 Promotion-Bridge Nahtfehler, 2 Commits in P15+P8, Σ 1971 + 2 P15 + 1 P8 = **1974** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #2 ENDE — B-2 Divergenz-Sampler Reparatur, Σ 1965 + 4 P12-Tests + 2 P8-Tests = **1971** grün) | 2026-10-19 (Exec-Session #1 ENDE — A-0+A-1+A-2 + A-3 + B-0 + B-1, Σ 1965) | 2026-10-18 (Plan-§14-Nachtrag) | 2026-10-17 (Plan-Session, Opus 5.5)
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
| D Token-Budget | 🔄 **D-1 ✅** (Session #13, 2026-11-04, Σ **2046**): die Budget-Ausnahme ist im Code — `scheduler/budget.py::consumed_today()` überspringt Records von `budget_exempt_models` (MiniMax-M3 ⇒ Abo-Kontingent, „measured, not capped"), `webui/api.py::/api/token_usage` meldet sie separat als `exempt_tokens` (Kosten/Calls zählen weiter alle Records). **+3 P8-Tests** (296 → 299). **Offen:** der **dritte** Zählort (`autonomy_report.py::llm_usage_per_day()`) folgt in **E-1** (Block E) — bis dahin weicht die Report-Zahl von der Budget-Zahl ab (Plan §17 D-1c, gehört in den Shakedown-Vermerk). **D-2** = Nikinger-Entscheidungspunkt (K6-Einheit, nach dem Shakedown, **kein Code**) |
| E Test-Fundament | 🔄 **E-1 Definition ✅** (Session #14: **Plan §18** — Report v5: `llm_usage_per_day` trägt `exempt_tokens`/`exempt_calls` (D-1-Fortsetzung) + v5-Evaluatoren K2/K5/K7/K9/K10/K11; Anker re-verifiziert (**null Drift**), v4-Regressions-Baseline live gemessen, **2 Voraussetzungen** gemessen: v5-K2/K11 sind **erst nach E-3** messbar). **Code offen** — E-1 ist der nächste Commit (P16); danach E-2 (Shakedown-Prereg) → E-3 (Deploy) → E-4 (Shakedown) → E-5 (Auswertung + D-2/Flip-2-Entscheidungen + Prereg v5) → E-6 (Closeout) |

## Forward-Agenda (zwischen den Blöcken B-5..B-10 und C)

| # | Thema | Status | Link |
|---|---|---|---|
| **C2 — Provider-Plastizität** | Endpoint-Abstraktion für alle „gängigen" Provider (Anthropic + OpenAI + DeepSeek + Qwen + GLM + …). Nikinger-Entscheidung 2026-10-19 („soll mit sämtlichen gängigen Endpunkten funktionieren"). | ✅ **Plan §15** (2026-10-19, Plan-Session Opus 5.5) — ändert C-1/C-3/C-4/C-6/C-7 in place; Q1–Q8 entschieden | [`../docs/concepts/phase17_testbed_plan.md` §15](../docs/concepts/phase17_testbed_plan.md) |

> **Update 2026-10-19 (Plan-Session):** C2 ist jetzt **Teil von Block C** (Plan §15, Nikinger Q2) — kein eigener Block, keine Phase 18. Σ-Ziel Block C ≥ **2025** (statt 2016). Der Absatz unten ist historisch.

Diese Forward-Agenda ist **kein Block** der Phase 17 — sie ist „Material für eine Opus-Miniplan-Session nach den Blöcken B-5..B-10", wie es der Nikinger mit seiner Entscheidung intendiert hat. Eine spätere Session `Exec-Session #5+` wird je nach Nikingers Q2-Antwort entweder einen Plan-§-Anker (neuer Block C2 in Phase 17) oder einen eigenständigen Phasenkopf Phase 18 schreiben.

## Executor-Evaluation (Plan §14.2 — je Exec-Session eine Zeile)

| Session | Datum | Modell (`zai-coding-plan/…`) | Steps | Kontingent vorher → nachher (z.ai-Dashboard) | Tests | Rückfall | Notiz |
|---|---|---|---|---|---|---|---|
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

## Session stopped — 2026-11-04 (Exec-Session #14 — **der nächste Block ist geschrieben**: Plan §18 = Block E / E-1 (Report v5) mit **re-verifizierten Ankern** (null Drift) + **2 live gemessenen Voraussetzungen**; **dokumentarische Session, kein Code** — Σ unverändert **2046**; Session-Ende + **Push**)

> **Auftrag:** Nikinger 2026-11-04 (Web-Chat): „Sehr gut. Session beenden, next schreiben, commit, push." → (1) den **nächsten Block** (E-1) ausführbar schreiben, (2) die Session beenden, (3) committen, (4) pushen.
> **Bot-Ritual (am Session-Ende verifiziert):** Scheduler `disabled` + `inactive` (Hold-Marker `data/state/SCHEDULER_HELD`), kein `scheduler.run`-Prozess, `install_units.sh --check` exit 0, Recorder/Discovery/WebUI `enabled` + `active` (unangetastet). **Kein Neustart, kein Netz-Call, kein Live-Key** durch den Agenten.
> **Cross-Phase-Freigabe:** keine Code-Änderung in dieser Session → keine Cross-Phase-Freigabe nötig.

### Completed — diese Exec-Session (1 Doku-Commit)

| # | Commit | Phase | Inhalt |
|---|---|---|---|
| 1 | (dieser Commit) | P17-Doku + Plan | **§18 „Ausführungsblock E-1"** im Plan-Snapshot: Anker gegen den Code vom 2026-11-04 **re-verifiziert** (alle 11 §6-E-1-Anker in `phase16_activation/scripts/autonomy_report.py` — **null Drift**, P16 seit der Plan-Session unangefasst) + Code-Skizzen (`llm_usage_per_day` mit `exempt_tokens`/`exempt_calls` = D-1-Fortsetzung · `evaluate_k6_v5` · CLI-Flags `--prereg/--journal-file/--expect-llm-profile/--exempt-model` · v5-Evaluatoren-Tabelle mit live geprüften Quellen) + **v4-Regressions-Baseline live gemessen** (FAIL K1/K5/K6 · PASS K2/K3/K4/K7/K8) + **2 live gemessene Voraussetzungen** + 7 Testnamen + AK (P16 15 → 22, Σ ≥ 2053). **P17-Phasenkopf:** Block-E-Zeile, Executor-Zeile #14, Σ-Tabelle, Session-#14-Block + Rotation #13 → `SESSIONS_ARCHIVE.md`. `docs/INDEX.md` + `ROADMAP.md` + root-`CLAUDE.md`. **Kein Code** — Σ unverändert **2046**. |

### Der nächste Block — E-1 in Kurzform (Details im Plan §18)

| Ort | Änderung | Test |
|---|---|---|
| `autonomy_report.py::llm_usage_per_day` (Z. 369) | `exempt_models` kw-Arg; Exempt-Records zählen in `exempt_tokens`/`exempt_calls` — **auch** in der `exhausted_at`-Summation | `test_k6_v5_ignores_exempt_model_tokens` |
| `autonomy_report.py` (neue Evaluatoren, hinter `evaluate_k8` Z. 903) | `evaluate_k2_v5` · `evaluate_k6_v5` · `evaluate_k7_v5` · `evaluate_k9` · `evaluate_k10` · `evaluate_k11` + `count_discovery_cycles_per_day` | `test_k2_v5_requires_discovery_cycle_every_day` · `test_k7_v5_fails_on_profile_change_in_window` · `test_k9_counts_scheduled_restart_jobs_and_na_without_file` · `test_k10_na_without_close_fail_on_bridge_critical` · `test_k11_requires_divergence_event_every_trading_day` |
| `_parse_args` (Z. 1111) + `main` (Z. 1135) | `--prereg {v4,v5}` · `--journal-file` · `--expect-llm-profile` · `--exempt-model` (repeatable) | `test_v4_default_criteria_unchanged` |

**Warum E-1 jetzt:** D-1 hat die Ausnahme ins **Budget-Gate** und die **WebUI** gebracht — der **Report** (der dritte Zählort) kennt sie erst ab E-1. Ohne E-1 weicht die Report-Zahl von der Budget-Zahl ab (im Shakedown wäre das eine falsche K6-Aussage).

### ⚠ Zwei live gemessene Voraussetzungen (2026-11-04 — neu gegenüber §6 E-1)

| Beleg | Ist | Folge |
|---|---|---|
| `grep -c "discovery cycle" data/state/run_discovery.log` | **0** (Daemon läuft seit 2026-11-01 00:24, also **vor** B-10 vom 2026-11-03) | v5-K2 **erst nach E-3** messbar |
| `grep -c "divergence_ok\|quote_divergence" data/state/research_health.jsonl` | **0** (Datei zuletzt 2026-10-19; die Events kommen aus dem **Scheduler**, der im HOLD steht) | v5-K11 **erst nach E-3** messbar |

⇒ E-1 ist **implementierbar und unit-testbar** (Fixtures), aber ein v5-Verdikt ist **erst nach dem E-3-Deploy** sinnvoll — sonst wäre es ein **false FAIL** (F8-Klasse: „Kriterium erkennt einen toten Bot nicht"). Der E-3-Deploy startet alle vier Dienste neu ⇒ ab dann tragen Discovery- und Scheduler-Prozess den B-2/B-10-Code. **Ergänzung zu den E-3-Day-0-Checks:** `grep -c "discovery cycle" data/state/run_discovery.log` > 0.

**Regression-Baseline (live, 2026-11-04, vor der Implementierung):**
`--from 2026-09-30 --to 2026-10-13 --summary` ⇒ **FAIL K1 · FAIL K5 · FAIL K6 · PASS K2 · PASS K3 · PASS K4 · PASS K7 · PASS K8**, `overall_verdict: FAIL` — deckt sich mit §6 E-1 und dem Phase-16-Handover §2. Nach E-1 muss derselbe Aufruf **dieselben Verdikte** liefern.

### Gemessen (Host 201, Session-Ende)

| | Wert |
|---|---|
| `is-enabled` / `is-active` tradingbot-scheduler | `disabled` / `inactive` (Hold unangetastet) |
| `ps aux | grep scheduler.run` | 0 Treffer |
| `bash scripts/install_units.sh --check` | exit 0 |
| Σ (16 Suiten + root) | **2046** (unverändert — keine Code-Änderung) |
| `check_doc_rotation.py --strict` | exit 0 |

### Next (der übernächste Block)

- **E-1 ausführen** (Plan §18, **ein Commit in P16**): Anker, Skizzen, Testnamen und AKs sind
  fest → atomar abgearbeitet, kein Re-Planen nötig. Regressions-AK = die oben gemessene
  v4-Baseline (Verdikte, nicht Payload).
- **E-2** (Shakedown-Vorregistrierung, 📕) — nach E-1, **vor** E-3 (der Fenster = die ersten zwei
  Handelstage **nach** dem E-3-Start).
- **E-3** (Hold-Freigabe + Deploy, Operator) — der Schritt, der den Flip 1 **wirksam** macht und
  die K2/K11-Belege erzeugt.
- **D-2** bleibt ein **Nikinger-Entscheidungspunkt ohne Code** (K6-Einheit, nach dem Shakedown).
- **Frist 2026-11-15** — Abo-Key/Endpoint: jedes `minimax`-Profil vor dem Datum zurückflippen
  (Default `anthropic`).

### Open questions / blockers

- **E-1 ist der nächste Code-Block**; die Ausführung selbst ist der nächsten Session vorbehalten.
- **Modellwahl vertagt** (M3 vs. M3.1-Flash) — Profil und Modell sind getrennte Datenstellen.
- **Frist 2026-11-15** (Abo) — im Phasenkopf + Plan §16 dokumentiert.
- **Review-Gate vor E-3 (AK22)** weiterhin ⏳ (Claude-Code-Session, Anthropic; Schwerpunkte
  B-5…B-10, C-4…C-6, B-3, B-2).

### Session-end-Hinweis

- **Σ 2046** (16 Suiten + root). meta_m1 informativ, nicht in Σ.
- **Diese Session:** 1 Doku-Commit (Plan §18 + Phasenköpfe), **kein Code**.
- **Push:** die 4 Commits der Phase-17-Folge (D-1 Code · D-1 Doku · §18 Doku) gehen in diesem
  Schritt auf `origin/main`.
- **Kern-Erkenntnis:** ein Kriterium, dessen Beleg erst **nach** dem Deploy entsteht, ist bis
  dahin kein PASS/FAIL, sondern ein **false FAIL** — die Umkehrung von „grün ohne Messung".
  Deshalb steht die Voraussetzung jetzt **im Block**, nicht erst im Shakedown.


---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
