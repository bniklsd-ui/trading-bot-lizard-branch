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
updated: 2026-11-04 (Review-Session #17 — **AK22-Review-Gate ausgeführt** (Plan §21, Claude Code/Anthropic/Opus, read-only): 27 code-tragende Commits geprüft, Σ 2053 grün; **❌ kein PASS — E-3 gesperrt**: R1 Report-v5-Gesamtverdikt faltet K3/K4 ein (Shakedown nie PASS) · R2 K7-v5 FAIL by construction (Start-Zeile vor D1) · R3 B-8-Downgrade umschließt lokalen Code (Nikinger-Entscheidung) · H1–H4) | 2026-11-04 (Exec-Session #16 — **E-2 ausgeführt**: Shakedown-Vorregistrierung `PHASE17_SHAKEDOWN_PREREGISTRATION.md` geschrieben, `status: locked` nach T23-Freigabe; **Nikinger-Entscheidung „alle MiniMax-Modelle ausnehmen“** ⇒ Code-Commit in P8 (`budget_exempt_models = ("MiniMax-M3", "MiniMax-M3.1-Flash")`, 2 Pins verschärft, Negativ-Beweis erbracht, P8 299 unverändert, Σ **2053**); 1 Code-Commit + 1 Doku-Commit) | 2026-11-04 (Exec-Session #15 — **E-1 ausgeführt** (Plan §18): Report v5 in `phase16_activation/scripts/autonomy_report.py` — `llm_usage_per_day` mit `exempt_models` (D-1-Fortsetzung, inkl. `exhausted_at`-Summation) + 6 v5-Evaluatoren (K2/K6/K7/K9/K10/K11) + `count_discovery_cycles_per_day` + K5-`by_logger`/`deal_related` + CLI `--prereg {v4,v5}`/`--journal-file`/`--expect-llm-profile`/`--exempt-model`; 1 Code-Commit in P16 + 1 Doku-Commit, Σ 2046 + 7 = **2053** grün (P16 15 → 22); v4-Verdikte **unverändert** (FAIL K1/K5/K6 · PASS K2/K3/K4/K7/K8); **5 fail-closed-Entscheidungen** (K7 ohne Start-Zeile ⇒ FAIL, K9 ohne Zeitstempel ⇒ FAIL, K2/K11 ohne Handelstag ⇒ NA, K10 ohne CLOSE ⇒ NA, Ausnahmeliste lazy aus `SchedulerConfig()`); **v5-Läufe vor E-3 sind false FAILs** (K2/K11 brauchen den Deploy) | 2026-11-04 (Exec-Session #14 — **der nächste Block geschrieben**: Plan §18 = Block E / E-1 (Report v5: Token-Budget-Ausnahme im Report + v5-Kriterien K2/K5/K7/K9/K10/K11), Anker re-verifiziert (null Drift) + 2 live gemessene Voraussetzungen; **dokumentarische Session, kein Code** — Σ unverändert **2046**; Session-Ende + **Push**) | 2026-11-04 (Exec-Session #13 — **D-1 ausgeführt** (Plan §17): Token-Budget-Ausnahme an `budget_exempt_models` — `scheduler/budget.py` (Exempt-Records überspringen) + `webui/api.py` (`exempt_tokens` separat), 1 Code-Commit + 1 Doku-Commit, Σ 2043 + 3 = **2046** grün; D-2 bleibt Nikinger-Entscheidungspunkt (K6-Einheit, **kein Code**); Report-Zählort folgt in E-1) | 2026-11-03 (Exec-Session #12 — **der nächste Block geschrieben**: Plan §17 = Block D / D-1 (Budget-Ausnahme an zwei P8-Zählstellen, Anker re-verifiziert) + D-2 als Entscheidungspunkt; **dokumentarische Session, kein Code** — Σ unverändert **2043**; Session-Ende + **Push**) | 2026-11-03 (Exec-Session #11 — **C-7-Smoke PASS (Operator: beide MiniMax-Modelle PASS)** + **C-8 Flip 1** ausgeführt: `llm_profile = "research_m3"` (nur Research → MiniMax-M3), 1 Code-Commit + 1 Doku-Commit, Σ 2042 + 1 = **2043** grün; **inert bis E-3** (Hold); Flip 2 `all_m3` bleibt gegated) | 2026-11-03 (Exec-Session #10 — **Planwechsel z.ai → MiniMax** (Abo/M Plan, Nikinger-Entscheidung 2026-11-03): M-1 = Provider-Register umgestellt (Profil `research_m3`/`all_m3`, Modell `MiniMax-M3` mit `max_tokens=8192`, Preiszeile `(0.0, 0.0)`, `budget_exempt_models=("MiniMax-M3",)`, Quirks `max_completion_tokens`), 1 Code-Commit + 1 Doku-Commit, Σ 2041 + 1 = **2042** grün; **C-7 wartet auf den Nikinger** (Key `trading-bot-minimax-bot` + Familien-Smoke); **Frist 2026-11-15**) | 2026-11-03 (Exec-Session #9 ENDE — **Block C (Code C-1…C-6) abgeschlossen**: Provider-Register + LLM-Austausch (`_build_llm`) + `LLM_UNAVAILABLE` + Key-/Smoke-Skript, 6 Commits, Σ 2004 + 37 = **2041** grün; **C-7 wartet auf den Nikinger** (Bot-Key `trading-bot-zai-bot` fehlt, Familien-Smoke)) | 2026-11-03 (Exec-Session #8 ENDE — **Block B abgeschlossen**: B-7 Abstain-Naht + B-8 Paper-Logstufen + B-9 Stop-Timeout + B-10 Discovery-Beleg, 4 Code-Commits, Σ 2000 + 4 = **2004** grün; Scheduler `disabled`+`inactive` (Hold) + 3 Units laufen weiter) | 2026-10-25 (Exec-Session #7 ENDE — Scheduler-Hold: systemd-Autostart aus + getrackter Repo-Guard `data/state/SCHEDULER_HELD`, +12 root-Tests, Σ **2000**) | 2026-10-19 (Exec-Session #6 ENDE — B-6 Breaker Worst-Case, 1 Commit in P8, Σ 1985 + 3 P8-Tests = **1988** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #5 ENDE — B-5 Monitor-Re-Adoption, 1 Commit in P5+P8, Σ 1978 + 5 P5 + 2 P8 = **1985** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Plan-Session §15 Provider-Plastizität — Forward-Agenda C2 → Plan §15, Σ-Ziele C/D/E-1 +9, Σ 1978 re-gemessen) | 2026-10-19 (Exec-Session #4 ANSCHLUSS — `provider_plasticity/` Working-Notes-Set angelegt (kein Plan, Input für Opus-Miniplan-Session; 5 INDEX-Einträge); Nikinger-Entscheidungen Q1–Q8 ausstehend) | 2026-10-19 (Exec-Session #4 ENDE — B-4 Abschneiden sichtbar, 1 Commit in P4, Σ 1974 + 4 P4-Tests = **1978** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #3 ENDE — B-3 Promotion-Bridge Nahtfehler, 2 Commits in P15+P8, Σ 1971 + 2 P15 + 1 P8 = **1974** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #2 ENDE — B-2 Divergenz-Sampler Reparatur, Σ 1965 + 4 P12-Tests + 2 P8-Tests = **1971** grün) | 2026-10-19 (Exec-Session #1 ENDE — A-0+A-1+A-2 + A-3 + B-0 + B-1, Σ 1965) | 2026-10-18 (Plan-§14-Nachtrag) | 2026-10-17 (Plan-Session, Opus 5.5)
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
- **E-3-Zeitpunkt (AK22 R2, Nikinger-Entscheidung 2026-11-04, Option a) — Pflicht:** der
  Scheduler-Start (E-3, Plan §20 Schritt 7) erfolgt **am Morgen von D1 vor 09:00 Berlin** an einem
  Handelstag (Mo–Fr); alle E-3-Schritte davor (Backups, T14, T12, Units) laufen am selben Morgen.
  Dann ist D1 der „erste volle Handelstag nach dem E-3-Start" (Prereg BLUF), die
  `starting scheduler daemon`-Zeile liegt **im** Fenster (K7-v5) und K1 zählt genau den einen
  regulären Start. Ein Start nach 09:00 oder an einem Vortag/Wochenende ⇒ K7-v5 **FAIL by
  construction** (keine Start-Zeile in `[D1, D2]`). Die §20-Day-0-Checks laufen damit **auf D1**.
  **Konsequenz:** es gibt keinen Puffertag mehr — ein gescheiterter Day-0-Check ist ein Befund
  **im** Fenster ⇒ FAIL-Regel (`-S2` + neuer Lauf). *Nicht gewählte Alternative (Nikinger-Entscheidung,
  falls gewünscht):* E-3 einen Tag früher (Day-0-Checks als Puffer), dann **ein** bewusster
  Scheduler-Neustart am Morgen von D1 vor 09:00 als gezählter Start — das liest „die Start-Zeile
  aus E-3" (Prereg BLUF) anders und ist deshalb nicht übernommen.
  Prereg und Plan bleiben unverändert (beide 📕/locked) — diese Zeile ist die Ausführungsregel.

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
| Review-Session #17 (AK22, read-only, 2026-11-04) | **2053** | selbst gemessen, unverändert (kein Code), 16/16 grün |

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

**Review-Gate vor E-3 (AK22):** ❌ **kein PASS** — Review-Session #17 (2026-11-04, Claude Code / Anthropic / Opus, Plan §21). **E-3 bleibt gesperrt**, bis R1 + R2 geschlossen und an der Stelle nachgeprüft sind. Befundliste: Abschnitt „AK22 — Review-Gate-Ergebnis" direkt darunter.

## AK22 — Review-Gate-Ergebnis (2026-11-04, Review-Session #17)

> Auftrag Plan §21. Harness **Claude Code / Anthropic / Opus** (§14.2). Read-only: kein Deploy, kein
> Dienst-Start/Stop, kein Keyring, kein Netz, kein Schreiben in `data/` (Report-Läufe nur in den
> Scratchpad, DBs `mode=ro`). Bot im HOLD (`install_units.sh --check` exit 0). Dieser Abschnitt ist
> **kein** Session-Block — er bleibt stehen, bis das Gate PASS ist (AK22 = „im Phasenkopf dokumentiert").

| Feld | Wert |
|---|---|
| Session | Review-Session #17 (AK22) |
| Datum | 2026-11-04 |
| Harness / Modell | Claude Code · Anthropic · Opus |
| Geprüfter Umfang | **27** code-tragende Commits: die 26 SHAs aus Plan §21 E-21a (`2675129` … `fa02a6a`) **+ `2c7b9c1`** (A-Block, `scripts/check_doc_rotation.py` +1 Zeile `PHASE_DIRS` — trägt Code, fehlt in E-21a) |
| Tests | Σ **2053** grün, 16/16 (selbst gemessen) |
| Verdikt | ❌ **kein PASS** — 2 × „Fix vor Deploy" (R1, R2) · 1 Nikinger-Entscheidung (R3) · 4 Hinweise (H1–H4) |

### Befunde

| # | Schweregrad | Ort | Befund | Reproduktion | Fix-Vorschlag |
|---|---|---|---|---|---|
| **R1** | **Fix vor Deploy** (Code, P16) | `phase16_activation/scripts/autonomy_report.py:744-754` (`SummaryReport.to_dict`) · `:1801-1805` · `:2002` | Der v5-`overall_verdict` faltet **K3/K4** ein, obwohl die Prereg sie „nur berichtet (kein PASS/FAIL)" führt (`PHASE17_SHAKEDOWN_PREREGISTRATION.md:35`). K4 ist in **jedem** 2-Tage-Fenster strukturell `PARTIAL` (gemessen gegen das registrierte 10-Tage-Fenster) ⇒ der Shakedown kann **nie** `PASS` / Exit 0 liefern. Zweite Drift an derselben Stelle: Exit-Map `PARTIAL → 1`, die Prereg sagt `2 = PARTIAL/ERROR` (`:160`). | `autonomy_report.py --prereg v5 --from 2026-10-07 --to 2026-10-08 --summary --expect-llm-profile research_m3 --exempt-model MiniMax-M3 --exempt-model MiniMax-M3.1-Flash --reports-dir <scratch>` ⇒ K3 PASS (6), **K4 PARTIAL**; `--from 2026-10-12 --to 2026-10-13` ⇒ K3 FAIL (0) + K4 PARTIAL | v5: K3/K4 in `criteria` behalten, als `reported_only` markieren, aus der Aggregation nehmen; Exit-Map an die Prereg angleichen (`PARTIAL → 2`). +1 P16-Test „K3 FAIL + K4 PARTIAL + Rest PASS ⇒ overall PASS, exit 0". **Vor E-3**, weil eine Aggregationsänderung nach den Daten eine nachträgliche Kriterienänderung wäre (Prereg „Warum") |
| **R2** | **Fix vor Deploy** (Entscheidung Nikinger: a/b) | `autonomy_report.py:1385` (`profile_ok = bool(lines) and …`) · `:655-684` (`start_lines_in_window`) vs. Prereg `:28` + `:92`, Plan §20 (Day-0) + §21 E-21e | **Widerspruch zwischen gelockten Dokumenten:** K7-v5 verlangt eine `starting scheduler daemon`-Zeile **im** Fenster `[D1, D2]`; die Prereg legt D1 auf den ersten vollen Handelstag **nach** dem E-3-Start, §20 verifiziert am Deploy-Tag (Tag 0). Die einzige Start-Zeile liegt damit auf Tag 0, **außerhalb** des Fensters ⇒ K7 FAIL **by construction** (ohne Neustart im Fenster). | `evaluate_k7_v5(trading_db, run_scheduler.log, 2026-10-13, 2026-10-14, expected_llm_profile="research_m3")` ⇒ `FAIL — no 'starting scheduler daemon' line inside the window` (letzter Start 10-12, Fenster ab 10-13) | **(a)** Doku: Scheduler-Start (E-3) am Morgen von D1 **vor 09:00 Berlin** pinnen — dann ist D1 der erste volle Handelstag nach dem Start, die Zeile liegt im Fenster, und K1s „1 regulärer Start" wird wahr. Kein Code, aber Tag 0 = D1. **(b)** Code: K7-v5 akzeptiert zusätzlich die **regierende** Start-Zeile (letzte vor D1 00:00) — ändert den Regeltext einer gelockten Prereg ⇒ `-S2`-Begründung nötig. **Empfehlung (a)** |
| **R3** | **Nikinger-Entscheidung** (plan-konform; §21-E1-Frage = **Nein**) | `phase10_v3/abstain_lessons/paper.py:317-324` · `:381-390` · `:463-471` · `:700-710` | B-8 senkt an vier Stellen `critical → warning` — der `try` umschließt dort aber auch **lokalen** Code (`prompt_builder`, `open_shadow_pair`, `store.insert`, `_maybe_council_pick`, `build_paper_lesson_prompt`, `validate_abstain_lesson`, `store.set_lesson`). Ein NameError/TypeError/sqlite-Fehler dort loggt jetzt WARNING ⇒ für K5 und AK11 unsichtbar (**F8: AK11 grün by construction**). Der Code entspricht Plan §6 B-8 wörtlich (T11/E4) — kein Reviewer-Zwang. | Code-Lesung der vier `except Exception`-Blöcke | `except` teilen: Programmierfehler (`NameError, AttributeError, TypeError, ImportError, sqlite3.Error`) → `logger.critical`, Rest → `warning`. +1 P10-Test. Empfehlung: **vor E-3 mitnehmen** (eine Datei, gleicher Commit-Typ wie B-8) |
| H1 | Hinweis (Input Prereg v5, E-5) | `autonomy_report.py:1497` (`evaluate_k10`) · `:744-754` | F8-Rest: K10 wird an einem CLOSE-Tag **PASS ohne jede Bridge-Aktivität** (0 CRITICAL + 0 `ok=False` + 0 neue Zeilen). Ein `NA` eines Pflichtkriteriums (K9 ohne Journal, K10 ohne CLOSE) zählt im Gesamtverdikt als nicht-blockierend. | Code-Lesung | Prereg v5: positives Bridge-Signal je CLOSE; `NA` eines Pflichtkriteriums ≠ PASS. **Jetzt nicht** (Prereg gelockt) |
| H2 | Hinweis | `phase15_v4/instinct/bridge.py:142` → `phase2_persistence/persistence/db.py:228` | `get_recent_trades(n=500)` liefert **alle** `trade_outcomes` inkl. `OPEN` — der Validator zählt eine offene Trade-ID als Evidenz (Docstring sagt „closed trades"). Heute ohne Wirkung (Promotion-Gatter zu: `n_closed ≥ 50` + Flag aus). | Code-Lesung | bei Gelegenheit nur `status='CLOSED'` übergeben |
| H3 | Hinweis (Doku-Drift) | Plan §21 Kopf + E-21a | „22 Code-Commits", die Tabelle listet **26** SHAs; `2c7b9c1` fehlt (⇒ 27). „AK22 (Plan §7)" — §7 führt AK1–AK21, AK22 steht in §14.1 (Plan Z. 1356). | `git log`, `grep -n AK22` | hier vermerkt; der Plan bleibt 📕-Snapshot |
| H4 | Hinweis (Beobachtung) | `phase8_scheduler/scheduler/run.py:203-219` | Die Start-Zeile wird **vor** `runner.run()` (Preflight) geschrieben: Preflight-Fehler (z. B. fehlender MiniMax-Key) ⇒ Start-Zeile + Exit 2 ⇒ `Restart=on-failure` alle 30 s ⇒ K1/K9 FAIL. Laut und fail-closed — **kein** Defekt, aber der Day-0-Check „Start-Zeile mit Profil" beweist allein nicht, dass der Daemon läuft. | Code-Lesung | Day-0 zusätzlich `is-active` + kein `preflight failed` im Log |

### Pflicht-Schwerpunkte + Ergänzungen (§21 E-21b) — Antworten

| # | Bereich | Ergebnis |
|---|---|---|
| P1 | B-5 Order-Pfad | ✅ Code = Plan §6 B-5 wörtlich. Kein Handeln ohne frische Broker-Wahrheit (`get_open_positions` nicht ok ⇒ `None`; Position weg ⇒ übersprungen). Einstieg = `execution_state.recorded_at` (gesetzt in `record_pending`, nie überschrieben). Sofort-Close: `monitor_position` prüft `now − entry ≥ max_hold` bzw. `square_off` schon im ersten Poll. Normalpfad bit-identisch (`entry_at=None ⇒ now_fn()`, `run()` unverändert). Nur WINDOW (`runner.py:389-398`). |
| P2 | B-6 Breaker (Hard Rule 5) | ✅ `_realized_pnl_today` (`wiring.py:104-128`): OPEN ⇒ `−initial_risk` (`initial_risk = abs(entry − stop) · size · pv` ≥ 0, `executor.py:638`); OPEN ohne `initial_risk` ⇒ `RuntimeError` ⇒ `AutoConfirm` blockt mit `REASON_LOSS` + `critical` (`safety.py:224-236`, Test `test_safety.py:201`). Kein Force-Trigger-Code existiert, der den Breaker umgehen könnte. |
| P3 | C-4 Verdrahtung + Startup-Check | ✅ `LLMClient(` 1 · `OpenAICompatLLMClient(` 1 in `wiring.py`. `anthropic`-Profil bit-identisch zu den 7 Alt-Konstruktionen (Modell/Key/Limits/Timeout/Meter/`cache_system` je Stelle verglichen; die drei `credentials`-Module re-exportieren dieselbe P1-Funktion). Startup-Check: 4 Fehlerklassen, `ValueError` vor jedem Client; auf den ausgelieferten Defaults grün (`research_m3`), unbekanntes Profil / fehlende Ausnahme ⇒ laut; `build_scheduler` liegt außerhalb des `try` (`run.py:203`) ⇒ Exit ≠ 0. Preflight nennt den Seed-Befehl (`wiring.py:1486-1492`). |
| P4 | B-3 Bridge | ✅ `validate(instinct, trades)` · `decision.decision` · `*_json`-Keys (Whitelist `db.py:54-58`) · Contract-Test mit echter DB (`test_instinct_bridge.py:368`). Rest: H2. |
| P5 | B-2 `mismatch`-Einbahnstraße | ✅ Gleiches Fenster `[ts, ts+5 min)` halboffen (`archive.py:184`), nur Bars mit Ende ≤ now − 25 min, Throttle erst nach echtem Vergleich (Ausnahme `stale` = echter Fehler), `mismatch` erst ab Streak 2 (Reset bei `divergence_ok`). Gate `_sampler_due`: WINDOW + Öffnung + 40 min. |
| E1 | B-7 / B-8 | B-7 ✅ (`record_id` durch beide Wrapper, Enrich außen). B-8: **R3**. |
| E2 | B-9 / B-10 | ✅ `TimeoutStopSec=360`; `install_units.sh --check` exit 0. Discovery-Zeile an allen 3 Rückgabestellen, `ts_utc` im Text, Unit `StandardError=append:`. |
| E3 | C-1 / C-3 / C-5 / C-6 | ✅ Quirks auf `ProviderSpec` (provider-, nicht modellbezogen); 400-Fallback ohne `response_format` verbraucht keinen Retry; `<think>`-Strip, unterminierter Block ⇒ harter Fehler; `LLM_UNAVAILABLE` eigene Klasse, `critical` genau einmal bei Streak 3; kein Key im Repo (Scan über 56 Nicht-Doku-Dateien der Phase 17), Keyring in Tests gemonkeypatcht. |
| E4 | E-1 Report v5 | v4-Regression reproduziert (FAIL K1/K5/K6 · PASS K2/K3/K4/K7/K8), Default `--prereg v4`; v5-Evaluatoren fail-closed wie spezifiziert. Aber: **R1**, **R2**, H1. |
| E5 | E-2 Ausnahme-Familie | ✅ Exakt-Match an allen 4 Stellen (`budget.py:187` · `webui/api.py:302` · Report via `--exempt-model` / `SchedulerConfig` · `llm_profiles.py` Klasse 4); Anthropic-Pfad unberührt. |
| E6 | Scheduler-Hold | ✅ `install_units.sh` enabled nicht · `restart-services.sh` startet nicht (`start_one`), Stop bleibt möglich. |
| E7 | F8 („grün ohne Messung?") | Grün ohne Messung möglich: **AK11** (R3), **K10** + `NA`-Faltung (H1). Rot ohne Defekt by construction: **overall/K4** (R1), **K7** (R2). Alle übrigen Checks verlangen ein positives Signal. |

**Nächster Schritt (E-21d Nr. 2/3):** R1 (+ R3, falls freigegeben) als Fix-Commit(s), R2 als Nikinger-Entscheidung (a/b) → Re-Review **nur** der betroffenen Stellen → dann „Review PASS" hier eintragen ⇒ E-3 frei.

> **Integration des Executors = eurofyx-fleet, getrennt vom Plan (Plan §14.8, Nikinger 2026-10-18).** Die Fleet richtet ein: OpenCode-Provider `zai-coding-plan` (Auth), Modell, Neustart von `opencode.service`, MiniMax-Rückweg. Diese Exec-Session fasst `~/.config/opencode/`, `auth.json` und `opencode.service` **nicht** an. A-0 startet erst, wenn die Fleet „OpenCode + z.ai bereit" meldet.

---


---

## Session stopped — 2026-11-04 (Review-Session #17 — **AK22-Review-Gate ausgeführt** (Plan §21, Claude Code / Anthropic / Opus, read-only): 27 code-tragende Commits geprüft, **❌ kein PASS — E-3 gesperrt** (R1 + R2 Fix vor Deploy, R3 Nikinger-Entscheidung); 0 Code-Commits, Σ **2053** unverändert)

> **Auftrag:** Nikinger (2026-11-04): „führe Plan §21 (AK22) aus". **Plan war detailliert genug** (§21: Umfang, Fragen je Bereich, Nicht-tun-Liste, Output-Format) → kein Re-Planen, atomar abgearbeitet.
> **Harness:** Claude Code · Anthropic · Opus — die einzige AK22-qualifizierte Kombination (§14.2).
> **Read-only:** kein Deploy, kein Dienst-Start/Stop, kein Keyring, kein Netz, kein Schreiben in `data/` (Report-Läufe nach `--reports-dir <scratchpad>`, DBs `mode=ro`). Bot im HOLD: `install_units.sh --check` exit 0.
> **Analyse ≠ Fix** (Memory-Regel): diese Session schreibt **keinen** Fix-Code — die Befunde gehen mit Datei:Zeile + Reproduktion in den Abschnitt „AK22 — Review-Gate-Ergebnis" oben.

### Completed

| # | Was | Ergebnis |
|---|---|---|
| 1 | Umfang gegen `git log` abgeglichen | **27** code-tragende Commits seit A-0 (26 aus E-21a + `2c7b9c1`); §21 nennt „22" (H3) |
| 2 | Σ-Sweep (16 Suiten + root) | **2053** grün, 16/16 |
| 3 | 5 Pflicht-Schwerpunkte P1–P5 + Ergänzungen E1–E7 | Antworten-Tabelle im AK22-Abschnitt; P1–P5 ✅ |
| 4 | v4-Regression `--from 2026-09-30 --to 2026-10-13 --summary` | reproduziert: FAIL K1/K5/K6 · PASS K2/K3/K4/K7/K8 |
| 5 | v5-Läufe auf zwei historischen 2-Tage-Fenstern | **R1** belegt (K4 immer `PARTIAL` ⇒ nie PASS) |
| 6 | `evaluate_k7_v5` auf einem Fenster ohne Start-Zeile | **R2** belegt (FAIL by construction) |
| 7 | Offline-Proben C-4 | `_check_llm_profile(SchedulerConfig())` grün; Fehlprofil/fehlende Ausnahme ⇒ `ValueError`; `build_scheduler` außerhalb des `try` ⇒ Exit ≠ 0 |
| 8 | Key-Hygiene-Scan (56 Nicht-Doku-Dateien) | kein Key im Repo, Keyring in Tests gemonkeypatcht |
| 9 | Advisor-Gegenprüfung vor dem Verdikt | bestätigt „kein PASS"; schärft R1 (Exit-Map-Drift) und R2 (Widerspruch gelockter Dokumente) |

### Next

- **Drei Nikinger-Fragen vor dem Fix:**
  1. **Wer schreibt R1** (P16, `autonomy_report.py`, + 1 Test)? Exec-Session (OpenCode) oder diese Claude-Code-Session nach Freigabe.
  2. **R2: Option (a) oder (b)?** Empfehlung (a) = Scheduler-Start in E-3 am Morgen von D1 vor 09:00 Berlin pinnen (kein Code).
  3. **R3: B-8-`except` teilen** (Programmierfehler → `critical`) vor E-3 — ja/nein?
- Danach: Fix-Commit(s) → **Re-Review nur der betroffenen Stellen** (Claude Code) → „Review PASS" in den AK22-Abschnitt ⇒ **E-3** (Plan §20).
- H1 (K10 ohne Bridge-Aktivität, `NA`-Faltung) geht als Input in **Prereg v5** (E-5).
- **Frist 2026-11-15** (MiniMax-Abo) läuft weiter — die R1/R2-Klärung kostet Tage im 2-Tage-Fenster.

### Open questions / blockers

- **E-3 gesperrt** bis R1 + R2 geschlossen und nachgeprüft sind.
- Push der Phase-17-Commits seit dem letzten Push = Nikinger.



---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
