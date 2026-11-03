---
status: live
purpose: PHASE-HEAD, Phase 17 (Prüfstand) — 🔄 eröffnet 2026-10-17 (Plan-Session, Opus 5.5). Keine neuen Features. Tiefe Härtung des Bestehenden — vier Phase-16-PASS-Blocker + drei neu gemessene stille Totalausfälle zu, LLM pro Rolle austauschbar (Research zuerst auf GLM über die z.ai-API mit Pay-per-use, Plan §14), Report + Vorregistrierung v5 als Fundament für die ausgiebigen Tests. Executor: offener Test GLM in OpenCode (§14).
read-when: jede Phase-17-Exec-Session — zuerst diesen Kopf, dann den `## Session stopped`-Block, dann den Plan
detail: L1
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase17_testbed_plan.md               # 📕 der Plan (T1–T24, D1–D13, Blöcke A–E, AK1–AK21, §8 Fehlgriffe, §9 Verify)
  - ./provider_plasticity/                                  # 🔄 Working-Notes Provider-Plastizität (2026-10-19, 4 Notizen: 01 Decision T25–T28 · 02 Current-State · 03 Opus-Brief · 04 Open Questions Q1–Q8)
  - ../phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md     # 📕 Vorgänger-Handover (§4 PASS-Blocker, §5 E1–E8)
  - ../phase16_activation/scripts/autonomy_report.py       # Report-Skript, Block E erweitert es in place (--prereg v5)
  - ./SESSIONS_ARCHIVE.md                                  # rotierte Session-Blöcke (L3, newest-first)
updated: 2026-11-03 (Exec-Session #9 ENDE — **Block C (Code C-1…C-6) abgeschlossen**: Provider-Register + LLM-Austausch (`_build_llm`) + `LLM_UNAVAILABLE` + Key-/Smoke-Skript, 6 Commits, Σ 2004 + 37 = **2041** grün; **C-7 wartet auf den Nikinger** (Bot-Key `trading-bot-zai-bot` fehlt, Familien-Smoke)) | 2026-11-03 (Exec-Session #8 ENDE — **Block B abgeschlossen**: B-7 Abstain-Naht + B-8 Paper-Logstufen + B-9 Stop-Timeout + B-10 Discovery-Beleg, 4 Code-Commits, Σ 2000 + 4 = **2004** grün; Scheduler `disabled`+`inactive` (Hold) + 3 Units laufen weiter) | 2026-10-25 (Exec-Session #7 ENDE — Scheduler-Hold: systemd-Autostart aus + getrackter Repo-Guard `data/state/SCHEDULER_HELD`, +12 root-Tests, Σ **2000**) | 2026-10-19 (Exec-Session #6 ENDE — B-6 Breaker Worst-Case, 1 Commit in P8, Σ 1985 + 3 P8-Tests = **1988** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #5 ENDE — B-5 Monitor-Re-Adoption, 1 Commit in P5+P8, Σ 1978 + 5 P5 + 2 P8 = **1985** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Plan-Session §15 Provider-Plastizität — Forward-Agenda C2 → Plan §15, Σ-Ziele C/D/E-1 +9, Σ 1978 re-gemessen) | 2026-10-19 (Exec-Session #4 ANSCHLUSS — `provider_plasticity/` Working-Notes-Set angelegt (kein Plan, Input für Opus-Miniplan-Session; 5 INDEX-Einträge); Nikinger-Entscheidungen Q1–Q8 ausstehend) | 2026-10-19 (Exec-Session #4 ENDE — B-4 Abschneiden sichtbar, 1 Commit in P4, Σ 1974 + 4 P4-Tests = **1978** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #3 ENDE — B-3 Promotion-Bridge Nahtfehler, 2 Commits in P15+P8, Σ 1971 + 2 P15 + 1 P8 = **1974** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #2 ENDE — B-2 Divergenz-Sampler Reparatur, Σ 1965 + 4 P12-Tests + 2 P8-Tests = **1971** grün) | 2026-10-19 (Exec-Session #1 ENDE — A-0+A-1+A-2 + A-3 + B-0 + B-1, Σ 1965) | 2026-10-18 (Plan-§14-Nachtrag) | 2026-10-17 (Plan-Session, Opus 5.5)
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

## Gelockt (Kurzform — volle Begründung Plan §1, **Vorrang hat Plan §14** vom 2026-10-18)

| ID | Kern |
|---|---|
| T4/T5 (§14) | **GLM über die allgemeine z.ai-API, Pay-per-use** (`https://api.z.ai/api/paas/v4`, **nie** `/api/coding/` — prüft `check_llm_profile` beim Start). Das Modell wählt der Nikinger nach dem Familien-Smoke C-7 (`glm-5.3` / `glm-5.3-flash` / `glm-5.2`). **Flip 1** = `research_glm`, **Flip 2** = `all_glm`, nur auf Nikinger-Go nach dem Shakedown |
| T6 (§14) | Bot-Key im eigenen Namespace `trading-bot-zai-bot` / `api_key` (Keyring; nie der Coding-Plan-Key) |
| T7 (§14) | Das GLM-Bot-Modell ist budgetfrei (`budget_exempt_models`; die Kadenz begrenzt es auf ≤ 102 Research-Calls/Tag). Es hat eine **echte Preiszeile**, also wird € gemessen. Anthropic bleibt bei 300 k; K6-Einheit entscheidet der Nikinger nach dem Shakedown |
| T8 | Monitor-Re-Adoption nach Restart, nur im WINDOW, inklusive Sofort-Close bei überschrittener Haltezeit |
| T9 | Breaker zählt heutige OPEN-Zeilen mit `−initial_risk`; NULL → fail-closed |
| T13 | Code in P1, P4, P5, P8, P10, P12, P14, P15, P16; P2 nur Tests; **kein** Code in P6/P7/P13 |
| T14/T15 | IG-Zeitstempel-Fix (+ Löschen der 3 730 falschen `ig`-Bars), Divergenz-Sampler-Reparatur |
| T22 (§14) | Exec = **offener Test in OpenCode + z.ai Coding Plan**, Start `zai-coding-plan/glm-5.3-flash`, Familie `glm-5.2`/`glm-5.3` zugelassen. Claude Code bleibt Anthropic-only und macht das **Pflicht-Review-Gate vor E-3**. Rückfall auf MiniMax (bis 2026-11-15) oder Claude, wenn ein Step zweimal scheitert oder ein Test nach 3 Versuchen rot bleibt. Scheduler gestoppt von B-0 bis E-3 |

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
| C LLM-Austausch | 🔄 **Code C-1…C-6 ✅** (Session #9, Σ **2041**): Provider-Register (9 Einträge) · `_build_llm` (eine Bau-Funktion) · `_debate_config` · Profil-Check beim Start · Preflight-Key-Check · `LLM_UNAVAILABLE` · Key-/Smoke-Skript. **Offen: C-7 (Operator: Bot-Key + Familien-Smoke) → C-8 (Flip 1 `research_glm`, gegated)** |
| Scheduler-Hold (B-0 → E-3) | ✅ aktiv (2026-10-25): systemd `disabled` + `data/state/SCHEDULER_HELD`, beide Repo-Türen (Installer, Restart-Helper) respektieren den Marker — **Freigabe erst in E-3** (`bash scripts/install_units.sh --release-hold`) |
| D Token-Budget | ⏳ |
| E Test-Fundament | ⏳ |

## Forward-Agenda (zwischen den Blöcken B-5..B-10 und C)

| # | Thema | Status | Link |
|---|---|---|---|
| **C2 — Provider-Plastizität** | Endpoint-Abstraktion für alle „gängigen" Provider (Anthropic + OpenAI + DeepSeek + Qwen + GLM + …). Nikinger-Entscheidung 2026-10-19 („soll mit sämtlichen gängigen Endpunkten funktionieren"). | ✅ **Plan §15** (2026-10-19, Plan-Session Opus 5.5) — ändert C-1/C-3/C-4/C-6/C-7 in place; Q1–Q8 entschieden | [`../docs/concepts/phase17_testbed_plan.md` §15](../docs/concepts/phase17_testbed_plan.md) |

> **Update 2026-10-19 (Plan-Session):** C2 ist jetzt **Teil von Block C** (Plan §15, Nikinger Q2) — kein eigener Block, keine Phase 18. Σ-Ziel Block C ≥ **2025** (statt 2016). Der Absatz unten ist historisch.

Diese Forward-Agenda ist **kein Block** der Phase 17 — sie ist „Material für eine Opus-Miniplan-Session nach den Blöcken B-5..B-10", wie es der Nikinger mit seiner Entscheidung intendiert hat. Eine spätere Session `Exec-Session #5+` wird je nach Nikingers Q2-Antwort entweder einen Plan-§-Anker (neuer Block C2 in Phase 17) oder einen eigenständigen Phasenkopf Phase 18 schreiben.

## Executor-Evaluation (Plan §14.2 — je Exec-Session eine Zeile)

| Session | Datum | Modell (`zai-coding-plan/…`) | Steps | Kontingent vorher → nachher (z.ai-Dashboard) | Tests | Rückfall | Notiz |
|---|---|---|---|---|---|---|---|
| #9 (Block C, Code) | 2026-11-03 | MiniMax-M3-Fallback (Plan §14.2) — kein z.ai-Modell heute in Verwendung | C-1 Provider-Register (P8) · C-2 Config-Defaults (P8) · C-3 OpenAI-Compat-Härtung + GLM-Preiszeilen (P4) · C-4 `_build_llm` + `_debate_config` + Profil-Check + Preflight (P8) · C-5 `LLM_UNAVAILABLE` (P4+P8+P10) · C-6 Key-/Smoke-Skript (root+P4) | n/a | Σ 2004 → **2041** (+37: P8 +23 · P4 +10 · P10 +2 · root +2; Plan-AK Block C Σ ≥ 2025 ✓, P4 ≥ 177 ✓, P8 ≥ 292 ✓, P10 ≥ 167 ✓) | — | **6 Commits**: `698e9ea` (C-1) `145e80e` (C-2) `4190802` (C-3) `1a61229` (C-4) `edeeab8` (C-5) `6d1f69d` (C-6). **AK C-4 erfüllt:** `LLMClient(` → 1 Treffer, `OpenAICompatLLMClient(` → 1 Treffer in `wiring.py` (beide in `_build_llm`). **Abweichung:** C-4 lieferte **+7** P8-Tests statt +5 (AK ist eine Untergrenze; 2 zusätzliche Tests: unbekanntes Profil wirft vor jedem Client · Client-Oberfläche). **C-7 wartet auf den Nikinger** (Key `trading-bot-zai-bot` im Keyring **nicht** vorhanden — gemessen) |
| #8 (B-7…B-10) | 2026-11-03 | MiniMax-M3-Fallback (Plan §14.2) — kein z.ai-Modell heute in Verwendung | B-7 Abstain-Naht (D7, P8) · B-8 Paper-Logstufen (D8, P10) · B-9 Stop-Timeout (D13, P16-Unit) · B-10 Discovery-Beleg (D12, P14) | n/a | Σ 2000 → **2004** (+4: P8 +2 · P10 +1 · P14 +1 ✓ Plan-AK exakt; B-9 +0, Unit-Test läuft in E-3) | — | **4 Commits, ein Block-Teil**: `5d02e7c` (B-7) · `02faf44` (B-8) · `f221f3c` (B-9) · `4eefbda` (B-10). **Anker-Drift nur bei B-7** (Plan Z. 758–760 → heute Z. 841–856, ≈ +83 Zeilen > +60-Schwelle → im Phasenkopf dokumentiert, Plan bleibt 📕-Snapshot); B-8/B-9/B-10 **null Drift**. Negativ-Beweis je Test: mit dem pre-Fix-Code rot (stash), mit dem Fix grün. B-9 brachte eine **Host-Notiz**: getrackte Unit über `install_units.sh` installiert (Datei-Kopie + daemon-reload), damit `--check` exit 0 bleibt — Hold unangetastet (Unit bleibt `disabled`+`inactive`, Start erst in E-3) |
| #6 (B-6) | 2026-10-19 | MiniMax-M3-Fallback (Plan §14.2) — kein z.ai-Modell heute in Verwendung | B-6 Breaker Worst-Case (D6, T9, P8) | n/a | Σ 1985 → **1988** (+3, P8 +3 ✓ Plan-AK exakt) | — | Plan-Anker Z. 1009–1016 (Closure `realized_pnl_today`) ist zwischen Plan-Session 2026-10-17 und Session #6 auf Z. 1066–1073 gewandert (~$+57$ Zeilen durch Folge-Commits in P15/P8); **kleiner Drift**, semantisch unverändert. Neuer Modul-Helper `_realized_pnl_today` direkt nach `_sampler_due` einsortiert (B-Block-Helper-Section). Test-File `tests/test_wiring_breaker.py` neu — DB-Path `:memory:` (sqlite3 in-memory, ein Connection über Test-Lifetime, keine `tmp_path`-Notwendigkeit) |
| #5 (B-5) | 2026-10-19 | MiniMax-M3-Fallback (Plan §14.2) — kein z.ai-Modell heute in Verwendung | B-5 Monitor-Re-Adoption (D5, T8, P5 + P8) | n/a | Σ 1978 → **1985** (+7, P5 +5 + P8 +2 ✓ Plan-AK exakt) | — | B-5 ist die letzte Single-Commit-Block: 1 Commit (154f460) in P5+P8. Bit-Identität via `getattr(self._executor, "resume_open_position", None)` — alle Bestands-Fakes unverändert grün |
| — | — | — | — | — | — | — | Der 5.2-Quirk: bei Flash-ähnlichem Kontingent-Verbrauch einen vergleichbaren Step mit `glm-5.2` fahren |

**Review-Gate vor E-3 (AK22):** ⏳ (Claude-Code-Session, Anthropic; Schwerpunkte B-5, B-6, B-7, B-8, B-9, B-10, C-4, B-3, B-2)

> **Integration des Executors = eurofyx-fleet, getrennt vom Plan (Plan §14.8, Nikinger 2026-10-18).** Die Fleet richtet ein: OpenCode-Provider `zai-coding-plan` (Auth), Modell, Neustart von `opencode.service`, MiniMax-Rückweg. Diese Exec-Session fasst `~/.config/opencode/`, `auth.json` und `opencode.service` **nicht** an. A-0 startet erst, wenn die Fleet „OpenCode + z.ai bereit" meldet.

---


---

## Session stopped — 2026-11-03 (Exec-Session #9 ENDE — **Block C, Code-Teil C-1…C-6 abgeschlossen**: Provider-Register + LLM-Austausch (`_build_llm`) + `LLM_UNAVAILABLE` + Key-/Smoke-Skript; 6 Commits, Σ 2004 + 37 = **2041** grün; **C-7 wartet auf den Nikinger** — Bot-Key `trading-bot-zai-bot` fehlt im Keyring)

> **Auftrag:** Nikinger 2026-11-03 (Web-Chat, zweite Session desselben Tages): „ja, pushen, und danach weiter mit dem nächsten Step" → (1) **Push** der 5 Commits aus Session #8 (`423a541..d7b6abe main -> main`, auftragsgemäß vom Nikinger freigegeben), (2) **Block C** abarbeiten — Plan §14 → §15 → §6 (die Reihenfolge, die §15 selbst festlegt). **Plan war detailliert genug** → atomar abgearbeitet, ein Commit pro Step, kein Re-Planen.
> **Executor-Modus:** MiniMax-M3 (OpenCode) — kein z.ai-Modell heute. `~/.config/opencode/`, `auth.json`, `opencode.service` unangefasst (Plan §14.8).
> **Bot-Ritual (vorab geprüft):** Scheduler `disabled` + `inactive` (Hold-Marker `data/state/SCHEDULER_HELD`), `install_units.sh --check` exit 0. Recorder/Discovery/WebUI `enabled` + `active` — unangefasst. **Kein Neustart, kein Live-Key, kein Netz-Call** in dieser Session (die Smokes sind Operator-Schritte).
> **Cross-Phase-Freigabe:** C-1/C-2/C-4 (P8), C-3/C-5/C-6 (P4), C-5 (P10), C-6 (root) — alle in der T13-Liste.

### Completed — diese Exec-Session (6 Code-Commits + 1 Doku-Commit)

| # | Commit | Phase | Inhalt |
|---|---|---|---|
| 1 | `698e9ea` | P8 | **C-1 — Provider-Register** `scheduler/llm_profiles.py` (NEU, stdlib-only): `ProviderSpec` (kind · base_url · Keyring-Namespace + **drei Quirks**: `max_tokens_field`, `send_temperature`, `extra_body` — T26/T27, provider- **nie** modellbezogen), `RoleSpec`, **neun** `PROVIDERS` (anthropic · zai · minimax · openai · deepseek · qwen · kimi · openrouter · opencode_zen — T25: ein Provider = ein Daten-Eintrag, keine `if provider == …`-Zeile), `LLM_PROFILES` (`anthropic` / `research_glm` / `all_glm`), `role_spec()` (KeyError-frei), `check_provider()` (kind · https · **kein „coding" im Host** (T31) · Keyring-Namespace · Quirks-Feld), `client_kwargs()` (T29: die **eine** Abbildung — Bot **und** Smoke benutzen sie), `check_llm_profile()` (4 Fehlerklassen). **+11 P8-Tests.** |
| 2 | `145e80e` | P8 | **C-2 — Config-Defaults**: `SchedulerConfig.llm_profile = "anthropic"` + `budget_exempt_models = ("glm-5.3",)`. Code-Default statt CLI-Flag (die systemd-Unit übergibt keine Flags → nur ein Code-Default ist restart-fest). `__post_init__` unangetastet. **+1 P8-Test.** |
| 3 | `4190802` | P4 + P8 | **C-3 — OpenAI-Compat-Härtung**: `api_key_username` als Konstruktor-Argument; die **drei Quirks** mit Validierung **im Konstruktor** (der eine Engpass, den Bot und Smoke teilen) und **bytegleichem** Default-Payload; **400-Fallback** (einmal ohne `response_format`, mit dem **ersten** Fehlertext im Log); **`<think>`-Strip** (unterminiert = harter, nicht-retrybarer Fehler); Fehlermeldungen „OpenAI-compat call failed (base_url=…)"; `last_raw_text` für `--show-raw`. Dazu die **GLM-Preiszeilen** (§14.1: `glm-5.3` 1.4/4.4 · `glm-5.2` 1.4/4.4 · `glm-5.3-flash` 0.15/0.5 USD/Mtok). **+9 P4 + 1 P8-Tests** (der Bestandstest „400 raises immediately no retry" wurde plan-konform umgebaut). |
| 4 | `1a61229` | P8 | **C-4 — eine Bau-Funktion**: `_build_llm(role, llm_profile, …)` baut **alle** Clients (Anthropic → `LLMClient`, sonst → `OpenAICompatLLMClient` mit `**client_kwargs(provider)`); `_debate_config(llm_profile)` benennt Bull/Bear/Judge um (Phase 6 überschreibt `client.model` je Rolle!); alle **sieben** Bau-Stellen umgestellt (research · debate · lesson · instinct · reflect · paper_debate · reflect-Tracker); `_check_llm_profile()` läuft in `build_scheduler` **vor** jedem Bau; **Preflight-Punkt 4**: jeder Nicht-Anthropic-Provider braucht seinen Key im Keyring (sonst startet der Daemon fröhlich und scheitert um 09:00); die **Start-Zeile** nennt `llm_profile`. **+7 P8-Tests** (AK: `LLMClient(` → 1 Treffer, `OpenAICompatLLMClient(` → 1 Treffer). |
| 5 | `edeeab8` | P4 + P8 + P10 | **C-5 — `LLM_UNAVAILABLE`** (D9): P4 setzt `last_llm_error`; P8 `research_tick` kennt `REASON_LLM_UNAVAILABLE` + **Fehler-Streak** (genau bei 3 ein `logger.critical`); P8-Wiring setzt das `llm_unavailable`-Flag **vor** der Klassifikation (die Reihenfolge, die B-7 geschaffen hat); P10 bekommt `REASON_LLM_UNAVAILABLE` (13 Gründe) — die Stage bleibt `RESEARCH_EMPTY`, nur der Grund unterscheidet sich; **keine Migration** (die Spalte hat keinen CHECK). **+1 P4 + 3 P8 + 2 P10-Tests.** |
| 6 | `6d1f69d` | root + P4 | **C-6 — Operator-Skripte**: `scripts/store_minimax_key.py` ist jetzt **generisch** (`--service`/`--username`, `main(argv)`); `openrouter_smoke.py` bekommt `--base-url`/`--key-service`/`--key-username`/`--max-tokens`/`--timeout-s`/`--show-raw` **und `--provider`** (§15.4: Endpoint + Keyring + Quirks aus dem Provider-Register — der Smoke sendet exakt den Bot-Payload; `--provider` ist mit den expliziten Flags **mutually exclusive**) plus `finish_reason`/`latency_s`/`provider=` in der Ausgabe. **+2 root-Tests.** |
| 7 | (dieser Commit) | P17-Doku | **Doku-Propagierung:** dieser Block + Rotation von Session #8 → `SESSIONS_ARCHIVE.md` + Σ-Tabelle + Block-Status + Executor-Evaluations-Zeile + die drei getroffenen Phasenköpfe (P8/P4/P10) + `docs/INDEX.md` + `ROADMAP.md` + root-`CLAUDE.md`. |

### Gemessen (Host 201)

| | vorher | nachher |
|---|---|---|
| `is-enabled` / `is-active` tradingbot-scheduler | `disabled` / `inactive` | `disabled` / `inactive` (unverändert) |
| recorder / discovery / webui | enabled + active | enabled + active (unverändert) |
| `bash scripts/install_units.sh --check` | exit 0 | exit 0 |
| Keyring `trading-bot-zai-bot/api_key` | — | **nicht gesetzt** (gemessen — Voraussetzung für C-7 fehlt) |
| Keyring `trading-bot-minimax-bot/api_key` | — | nicht gesetzt |
| Σ-Sweep (16 Suiten + root) | 2004 | **2041** (16/16 grün) |

### Plan-AK-Stand nach dieser Session

- **Block C, Code-Teil (C-1…C-6): ✅ abgeschlossen.** Σ **2041** ≥ 2025 ✓ · P4 **177** ≥ 177 ✓ · P8 **294** ≥ 292 ✓ · P10 **168** ≥ 167 ✓.
- **Plan-AK C-4:** `rg "\bLLMClient\(" phase8_scheduler/scripts/wiring.py` → **1** Treffer; `rg "OpenAICompatLLMClient\("` → **1** Treffer (beide in `_build_llm`) ✓.
- **Abweichung (ehrlich):** C-4 lieferte **+7** P8-Tests statt der geplanten +5. Der AK ist eine Untergrenze; die zwei zusätzlichen Tests decken „unbekanntes Profil wirft **vor** jedem Client" und die Client-Oberfläche ab.

### Was der Code **jetzt** kann (und was noch nicht)

- **Kann:** jeder OpenAI-kompatible Provider ist **ein Daten-Eintrag** (`PROVIDERS`), mit Quirks; das Bot verdrahtet **eine** Bau-Funktion; ein Profil-Wechsel ist ein Config-Wert; ein LLM-Ausfall ist von einem Modell-Abstain **unterscheidbar**; ein fehlender Provider-Key fällt **beim Start** auf, nicht um 09:00.
- **Kann noch nicht:** der Bot spricht **noch nicht** mit GLM — `llm_profile` steht auf `"anthropic"`. Das ist Absicht (T5/T8): **erst der C-7-Smoke, dann der Flip.**

### Next (geplante Folgesessions, in Priorität)

- **C-7 — Operator (Nikinger), zwei Schritte:**
  1. **Bot-Key seeden** (Pay-per-use, eigener Namespace — **nie** der Coding-Plan-Key):
     `python scripts/store_minimax_key.py --service trading-bot-zai-bot --username api_key`
  2. **Familien-Smoke** (3 Calls Pay-per-use, < 0,01 $ — Plan §14.4, mit `--provider zai`):
     ```bash
     PY=phase1_broker_wrapper/.venv/bin/python
     for m in glm-5.3 glm-5.3-flash glm-5.2; do
       $PY phase4_research/scripts/openrouter_smoke.py --provider zai --model "$m" \
         --max-tokens 4096 --timeout-s 90 --show-raw; done
     ```
     Je Modell PASS/FAIL, `finish_reason`, Tokens und Latenz hierher in den Phasenkopf (§14.4). **FAIL ⇒ nicht flippen** (Diagnose nach Plan §8/§15.6, dann ggf. `max_tokens`/`timeout_s` in `_GLM` anpassen — eigener Commit).
- **Danach (nach dem Nikinger-Go):** **Modellwahl** (`_GLM.model` + `budget_exempt_models` + Preiszeile — die drei Stellen, die zusammen geändert werden müssen) → **Flip 1** (`llm_profile = "research_glm"`, eigener Commit) → **C-8 („all_glm") bleibt gegated** bis nach dem Shakedown.
- **Block D (Token-Budget, T7/D-1):** die drei Zählstellen (P8 `budget.py` · WebUI-Karte · Report) müssen die `budget_exempt_models`-Ausnahme kennen.
- **Block E:** Report v5 (`--prereg v5`) · Shakedown-Vorregistrierung · **E-3-Deploy** (dort wird der Scheduler-Hold freigegeben) · 2-Tage-Shakedown · Prereg v5.
- **E-3-Vorbereitung (Pflicht-Schritt):** Hold-Freigabe `--release-hold` → Installer → `start` (sonst fehlt der R5-Autostart-Beweis).
- **Datenreparatur der 3 730 alten `ig`-Bars** (Plan T14) — folgt in **E-3**.

### Open questions / blockers

- **C-7 ist blockiert, bis der Nikinger den z.ai-Bot-Key seedet** (gemessen: `trading-bot-zai-bot/api_key` **nicht** im Keyring). Ohne Key kein Smoke, ohne Smoke kein Flip — **der Bot läuft unverändert auf Anthropic**, das ist der sichere Default.
- **`_GLM.model = "glm-5.3"` ist provisorisch** (Plan §14.4: der Nikinger wählt nach dem Familien-Smoke). Der Wechsel betrifft **drei** Stellen (`llm_profiles._GLM.model`, die Preiszeile in `research/models.py`, `SchedulerConfig.budget_exempt_models`) — `check_llm_profile` benennt die vergessene beim Start.
- **`budget_exempt_models` enthält nur `glm-5.3`** — das **MiniMax-Abo** (`trading-bot-minimax-bot`, gültig bis 2026-11-15) hat **kein** Profil; es ist nur ein Daten-Eintrag + Smoke-Ziel (§15.3/Q1). Ein Profil darauf braucht Preiszeile + Ausnahme im Flip-Commit.
- **MiniMax-Endpoint läuft am 2026-11-15 ab** (Plan §14.3) — nach dem Datum muss jedes Profil, das `minimax` nutzt, zurückgeflippt werden (aktuell: keins).
- **Plan-Snapshot-Drift** (B-7-Anker, ≈ +83 Zeilen) — im Phasenkopf dokumentiert, Plan bleibt 📕-Snapshot; Neuauflage ist eine offene Nikinger-Entscheidung.
- **Review-Gate vor E-3 (AK22)** weiterhin ⏳ (Claude-Code-Session, Anthropic; Schwerpunkte B-5…B-10, C-1…C-6, B-3, B-2).

### Session-end-Hinweis

- **Σ 2041** (16 Suiten + root, Sweep-Kommando aus dem Phase-Kopf). meta_m1 informativ, nicht in Σ.
- **Commits:** 7 (6 Code-Steps + 1 Doku). Push = Nikinger (Phase-17-Konvention).
- **Kern-Erkenntnis:** der Provider-Wechsel ist jetzt eine **Datenfrage** statt einer Codefrage — ein neuer Anbieter ist ein Commit auf `PROVIDERS` (plus Preiszeile + Ausnahme, wenn er *aktiv* wird), und `check_llm_profile` sagt beim Start, was fehlt. Die Kehrseite: die Entscheidung „welches Modell" ist bewusst **noch nicht** getroffen — sie gehört dem Nikinger nach dem gemessenen Smoke.

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
