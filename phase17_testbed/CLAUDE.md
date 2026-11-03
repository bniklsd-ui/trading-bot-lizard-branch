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
updated: 2026-11-03 (Exec-Session #8 ENDE — **Block B abgeschlossen**: B-7 Abstain-Naht + B-8 Paper-Logstufen + B-9 Stop-Timeout + B-10 Discovery-Beleg, 4 Code-Commits, Σ 2000 + 4 = **2004** grün; Scheduler `disabled`+`inactive` (Hold) + 3 Units laufen weiter) | 2026-10-25 (Exec-Session #7 ENDE — Scheduler-Hold: systemd-Autostart aus + getrackter Repo-Guard `data/state/SCHEDULER_HELD`, +12 root-Tests, Σ **2000**) | 2026-10-19 (Exec-Session #6 ENDE — B-6 Breaker Worst-Case, 1 Commit in P8, Σ 1985 + 3 P8-Tests = **1988** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #5 ENDE — B-5 Monitor-Re-Adoption, 1 Commit in P5+P8, Σ 1978 + 5 P5 + 2 P8 = **1985** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Plan-Session §15 Provider-Plastizität — Forward-Agenda C2 → Plan §15, Σ-Ziele C/D/E-1 +9, Σ 1978 re-gemessen) | 2026-10-19 (Exec-Session #4 ANSCHLUSS — `provider_plasticity/` Working-Notes-Set angelegt (kein Plan, Input für Opus-Miniplan-Session; 5 INDEX-Einträge); Nikinger-Entscheidungen Q1–Q8 ausstehend) | 2026-10-19 (Exec-Session #4 ENDE — B-4 Abschneiden sichtbar, 1 Commit in P4, Σ 1974 + 4 P4-Tests = **1978** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #3 ENDE — B-3 Promotion-Bridge Nahtfehler, 2 Commits in P15+P8, Σ 1971 + 2 P15 + 1 P8 = **1974** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #2 ENDE — B-2 Divergenz-Sampler Reparatur, Σ 1965 + 4 P12-Tests + 2 P8-Tests = **1971** grün) | 2026-10-19 (Exec-Session #1 ENDE — A-0+A-1+A-2 + A-3 + B-0 + B-1, Σ 1965) | 2026-10-18 (Plan-§14-Nachtrag) | 2026-10-17 (Plan-Session, Opus 5.5)
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
| Scheduler-Hold (B-0 → E-3) | ✅ aktiv (2026-10-25): systemd `disabled` + `data/state/SCHEDULER_HELD`, beide Repo-Türen (Installer, Restart-Helper) respektieren den Marker — **Freigabe erst in E-3** (`bash scripts/install_units.sh --release-hold`) |
| C LLM-Austausch | ⏳ — **zuerst Plan §14, dann §15** (Provider-Plastizität, in place) |
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
| #8 (B-7…B-10) | 2026-11-03 | MiniMax-M3-Fallback (Plan §14.2) — kein z.ai-Modell heute in Verwendung | B-7 Abstain-Naht (D7, P8) · B-8 Paper-Logstufen (D8, P10) · B-9 Stop-Timeout (D13, P16-Unit) · B-10 Discovery-Beleg (D12, P14) | n/a | Σ 2000 → **2004** (+4: P8 +2 · P10 +1 · P14 +1 ✓ Plan-AK exakt; B-9 +0, Unit-Test läuft in E-3) | — | **4 Commits, ein Block-Teil**: `5d02e7c` (B-7) · `02faf44` (B-8) · `f221f3c` (B-9) · `4eefbda` (B-10). **Anker-Drift nur bei B-7** (Plan Z. 758–760 → heute Z. 841–856, ≈ +83 Zeilen > +60-Schwelle → im Phasenkopf dokumentiert, Plan bleibt 📕-Snapshot); B-8/B-9/B-10 **null Drift**. Negativ-Beweis je Test: mit dem pre-Fix-Code rot (stash), mit dem Fix grün. B-9 brachte eine **Host-Notiz**: getrackte Unit über `install_units.sh` installiert (Datei-Kopie + daemon-reload), damit `--check` exit 0 bleibt — Hold unangetastet (Unit bleibt `disabled`+`inactive`, Start erst in E-3) |
| #6 (B-6) | 2026-10-19 | MiniMax-M3-Fallback (Plan §14.2) — kein z.ai-Modell heute in Verwendung | B-6 Breaker Worst-Case (D6, T9, P8) | n/a | Σ 1985 → **1988** (+3, P8 +3 ✓ Plan-AK exakt) | — | Plan-Anker Z. 1009–1016 (Closure `realized_pnl_today`) ist zwischen Plan-Session 2026-10-17 und Session #6 auf Z. 1066–1073 gewandert (~$+57$ Zeilen durch Folge-Commits in P15/P8); **kleiner Drift**, semantisch unverändert. Neuer Modul-Helper `_realized_pnl_today` direkt nach `_sampler_due` einsortiert (B-Block-Helper-Section). Test-File `tests/test_wiring_breaker.py` neu — DB-Path `:memory:` (sqlite3 in-memory, ein Connection über Test-Lifetime, keine `tmp_path`-Notwendigkeit) |
| #5 (B-5) | 2026-10-19 | MiniMax-M3-Fallback (Plan §14.2) — kein z.ai-Modell heute in Verwendung | B-5 Monitor-Re-Adoption (D5, T8, P5 + P8) | n/a | Σ 1978 → **1985** (+7, P5 +5 + P8 +2 ✓ Plan-AK exakt) | — | B-5 ist die letzte Single-Commit-Block: 1 Commit (154f460) in P5+P8. Bit-Identität via `getattr(self._executor, "resume_open_position", None)` — alle Bestands-Fakes unverändert grün |
| — | — | — | — | — | — | — | Der 5.2-Quirk: bei Flash-ähnlichem Kontingent-Verbrauch einen vergleichbaren Step mit `glm-5.2` fahren |

**Review-Gate vor E-3 (AK22):** ⏳ (Claude-Code-Session, Anthropic; Schwerpunkte B-5, B-6, B-7, B-8, B-9, B-10, C-4, B-3, B-2)

> **Integration des Executors = eurofyx-fleet, getrennt vom Plan (Plan §14.8, Nikinger 2026-10-18).** Die Fleet richtet ein: OpenCode-Provider `zai-coding-plan` (Auth), Modell, Neustart von `opencode.service`, MiniMax-Rückweg. Diese Exec-Session fasst `~/.config/opencode/`, `auth.json` und `opencode.service` **nicht** an. A-0 startet erst, wenn die Fleet „OpenCode + z.ai bereit" meldet.

---

## Session stopped — 2026-11-03 (Exec-Session #8 ENDE — **Block B abgeschlossen**: B-7 Abstain-Naht + B-8 Paper-Logstufen + B-9 Stop-Timeout + B-10 Discovery-Beleg; 4 Code-Commits, Σ 2000 + 4 = **2004** grün; Scheduler `disabled`+`inactive` (Hold) + 3 Units laufen weiter)

> **Auftrag:** Nikinger 2026-11-03 (Web-Chat): Phase 17 fortsetzen — „Start by reading the .md files … A good start is the /concept folder", „The phase is separated into steps, and the progress is noted … keep it recent". Der **Plan war detailliert genug** (Plan §6 B-7…B-10 mit Verbatim-Ankern, AKs und Testnamen) → **atomar abgearbeitet, kein Re-Planen**. Reihenfolge: Plan-§-Reihenfolge B-7 → B-8 → B-9 → B-10, ein Commit pro Block (Konvention der Exec-Sessions #2–#6).
> **Executor-Modus:** MiniMax-M3 (OpenCode) — kein z.ai-Modell heute. `~/.config/opencode/`, `auth.json`, `opencode.service` unangefasst (Plan §14.8).
> **Bot-Ritual (vorab geprüft):** Scheduler war bereits `disabled` + `inactive` (Hold-Marker `data/state/SCHEDULER_HELD`, aus Session #7), `install_units.sh --check` exit 0. Recorder/Discovery/WebUI `enabled` + `active` — **unangefasst** (nur der Discovery-*Code* geändert, kein Neustart → Bot-Ritual „Neustart macht nur E-3").
> **Cross-Phase-Freigabe:** alle vier Blöcke liegen in der T13-Liste (P8, P10, P16, P14) — keine Nachfrage nötig.

### Completed — diese Exec-Session (4 Code-Commits + 1 Docs-Commit)

| # | Commit | Phase | Inhalt |
|---|---|---|---|
| 1 | `5d02e7c` | P8 | **B-7 — Abstain-Naht (D7).** `scripts/wiring.py`: (a) `_observed_abstain_sink` reicht den `record_id` des inneren Sinks durch (`-> Any`, `record_id = inner.on_no_trade(...)`, `return record_id` **nach** dem try/except — ein Observability-Fehler darf den Wert nicht wieder verschlucken); Docstring-Satz „locked `AbstainSink.on_no_trade(cycle_outcome) -> None` contract" ersetzt. (b) **Reihenfolge im Composition Root umgedreht**: `_observed_abstain_sink(_enrich_abstain_detail(sink, research), path)` → `_enrich_abstain_detail(_observed_abstain_sink(sink, path), research)` — die Anreicherung liegt jetzt **vor** der Klassifikation des `abstain_recorded`-Events (vorher sah nur die Persistierung den angereicherten Zyklus). Das ist die Reihenfolge, die ab **C-5** das `llm_unavailable`-Flag rechtzeitig in die Klassifikation bringt. **+2 P8-Tests** (neu `phase8_scheduler/tests/test_wiring_abstain_seam.py`): `test_observed_sink_returns_inner_record_id`, `test_enriched_outer_wrapper_feeds_observed_classification` (Classifier-Spy: **pinnt die Reihenfolge**, nicht nur den Rückgabewert — mit der Alt-Reihenfolge sieht der Classifier `generic` statt `ENRICHED-PROSE`). Negativ-Beweis: beide Tests mit dem pre-B-7-`wiring.py` rot (stash). **P8 269 → 271** ✓ Plan-AK (≥ 271). |
| 2 | `02faf44` | P10 | **B-8 — Paper-Logstufen (D8, T11/E4).** `abstain_lessons/paper.py`: vier Stellen von `critical` → `warning` (Ausfälle **externer** Abhängigkeiten): `PaperDebateCaller.request_pick failed` (Z. 323), `PaperEngine.on_debate_abstain failed` (Z. 390), `PaperEngine.open_scheduled_pairs failed for %s` (Z. 471), `PaperTradeTracker reflect failed for record %s` (Z. 709). Jede mit dem Plan-Kommentar „# Phase 17 B-8 (E4): external-dependency failure (quote/LLM) — WARNING; an LLM outage is reported once by research_tick (LLM_UNAVAILABLE)." **Unverändert `critical`** (lokale Fehler = Bug-Indikatoren): `PaperTradeTracker bar fetch failed` (Z. 569) und `PaperTradeTracker resolve failed` (Z. 691). **+1 P10-Test** (`test_get_price_failure_logs_warning_not_critical`, caplog): Gegenprobe mit pre-B-8-Code rot. **P10 165 → 166** ✓ Plan-AK (≥ 166). |
| 3 | `f221f3c` | P16-Unit | **B-9 — Stop-Timeout (D13, T10).** `phase16_activation/systemd/tradingbot-scheduler.service`: `TimeoutStopSec=360` unter `SuccessExitStatus=143`, mit Plan-Kommentar („SIGTERM is honoured after the running cycle sleep (≤ 300 s) — 90 s default killed every stop (09-23, 09-30, 10-11)"). Vorher: systemd-Default 90 s → **jeder** Stop endete in SIGKILL, ohne dass `shutdown()` (finaler Reconcile + `broker.disconnect()`) je lief. Akzeptanz: `bash scripts/install_units.sh --verify` → exit 0 (`systemd-analyze --user verify: ok`). |
| 4 | `4eefbda` | P14 | **B-10 — Discovery-Beleg (D12).** `source_registry/run.py::run_once`: an **allen drei** Rückgabestellen (unarmed · armed+nichts-stale · realer Zyklus) eine INFO-Zeile direkt vor dem `return`: `"discovery cycle %s: armed=%s stale=%d rows_written=%d errors=%d"` — der Zeitstempel steckt **im Text** (`basicConfig` ohne `asctime`), eine Zeile pro Zyklus (≈ 1/Stdunde, `interval_s=3600`); die zwei `logger.debug(...)`-Zeilen bleiben. Davor gab es **keinen** append-only Beleg (nur `discovery_state.json`, in place, und eine unsichtbare debug-Zeile). Dazu `scripts/run_discovery.sh`: Starttext „(unarmed ⇒ noop)" → „(noop unless ARMED)" (das K1-Muster `\[run_discovery\] starting daemon` bleibt treffend). **+1 P14-Test** (`test_run_once_logs_discovery_cycle_line_with_ts`, caplog, alle drei Pfade): Gegenprobe mit pre-B-10-Code rot. **P14 61 → 62** ✓ Plan-AK (≥ 62). |
| 5 | (dieser Commit) | P17-Doku | **Doku-Propagierung:** dieser Block + Rotation von Session #7 → `SESSIONS_ARCHIVE.md` + Σ-Tabelle + Block-Status + Executor-Evaluations-Zeile + Bot-Ritual-Hinweis + die vier getroffenen Phasenköpfe (P8/P10/P14/P16) mit additivem „Phase-17-Edit"-Block (Muster B-5/B-6) + `docs/INDEX.md`. |

### Gemessen (Host 201, `trading-bot-VMware-Virtual-Platform`)

| | vorher | nachher |
|---|---|---|
| `is-enabled tradingbot-scheduler.service` | `disabled` | `disabled` (unverändert) |
| `is-active tradingbot-scheduler.service` | `inactive` | `inactive` (unverändert) |
| recorder / discovery / webui | enabled + active | enabled + active (unverändert) |
| `bash scripts/install_units.sh --check` | exit 0 | exit 0 (siehe „B-9-Host-Notiz" unten) |
| `bash scripts/install_units.sh --verify` | exit 0 | exit 0 (`systemd-analyze --user verify: ok`) |
| `data/state/SCHEDULER_HELD` | vorhanden | vorhanden (unberührt) |
| `data/state/KILL` | nicht vorhanden | nicht vorhanden (unberührt) |
| Σ-Sweep (16 Suiten + root) | 2000 | **2004** (16/16 grün) |

**B-9-Host-Notiz (bewusster Schritt, außerhalb des Commits):** die getrackte Unit wurde über den **getrackten Installer** auf 201 installiert (`bash scripts/install_units.sh` → Datei-Kopie + `daemon-reload`), **bevor** `--check` sonst dauerhaft rot gelaufen wäre (`installed=differs` → DRIFT, exit 1, weil die installierte Kopie die neue `TimeoutStopSec`-Zeile noch nicht hatte). Der **Hold blieb unangetastet**: die Scheduler-Unit bleibt `disabled` + `inactive`; gestartet wird weiterhin **erst in E-3**. Die drei anderen Units blieben `enabled` + `active` (der Installer hat sie nur idempotent re-enabled, **nicht** gestartet).

### Plan-AK-Stand nach dieser Session

- **Block B ist vollständig abgeschlossen** (B-0 … B-10): Exec-Session #1 (A-0…A-2, A-3, B-0, B-1) · #2 (B-2) · #3 (B-3) · #4 (B-4) · #5 (B-5) · #6 (B-6) · #7 (Scheduler-Hold) · **#8 (B-7, B-8, B-9, B-10)**.
- **Plan-AK Block-B-Sweep:** Σ ≥ 1992 → **2004** ✓ (Plan-Ziel übertroffen; +4 exakt wie im Plan vorgesehen: B-7 +2 P8 · B-8 +1 P10 · B-9 +0 (Unit-Test läuft in E-3) · B-10 +1 P14).
- **Σ 2000 → 2004** (P8 269→271 · P10 165→166 · P14 61→62; alle übrigen 13 Suiten + root unverändert grün).

### Drift-Konsolidierung (Anker)

- **B-7:** Plan-Anker Z. 758–760 → heute Z. 841–856 (≈ **+83 Zeilen**), Docstring Z. 747–753 → Z. 830–843, Reihenfolge Z. 993–995 → Z. 1094–1108. **Größer als die +60-Zeilen-Schwelle**, die der Session-#6-Block als „Plan-Snapshot updaten statt nur Drift protokollieren" markiert hat. **Entscheidung dieser Session:** der Plan ist ein **📕 dated snapshot** (`status: snapshot`) und wird **nicht** editiert (Anti-Pattern „📕 dated snapshot edit", T24: nur angehängter datierter Vermerk); der Drift ist hier vollständig dokumentiert und die Edits liefen am **realen Ort** (Verbatim-Anker, nicht Zeilennummer). *Für die Nikinger-Entscheidung offen:* Plan-Snapshot-Neuauflage (Datum + Zeilen) vor Block C.
- **B-8 / B-9 / B-10:** **kein Drift** — alle Anker exakt wie im Plan (P10 `paper.py:321/386/465/701`, P16-Unit `SuccessExitStatus=143`, P14 `run.py` 3× `return result` + `run_discovery.sh:46`).

### Next (geplante Folgesessions, in Priorität)

- **Block C — LLM-Austausch** (Plan §14 zuerst, dann §15): C-1 `scheduler/llm_profiles.py` (NEU, stdlib-only) → C-2 `SchedulerConfig.llm_profile` → C-3 OpenAI-Compat-Härtung + Preiszeile → C-4 **eine** Bau-Funktion für alle 7 Clients + Profil-Check + Preflight + Startzeile → C-5 `LLM_UNAVAILABLE` (eigene Abstain-Klasse, D9) → C-6 Key-Skript + Smoke-Skript → **C-7 Familien-Smoke (Nikinger, 3 Calls Pay-per-use < 0,01 $)** → C-8 „Flip 2" (**gegated**, nur mit Nikinger-Go nach dem Shakedown). Σ-Ziel Block C ≥ **2025**. **B-7 ist die Vorbedingung für C-5** — das `llm_unavailable`-Flag erreicht die Klassifikation jetzt rechtzeitig.
- **E-3-Vorbereitung (Pflicht-Schritt, noch offen):** der Hold muss **vor** E-3 freigegeben werden, sonst bleibt die Scheduler-Unit `disabled` (der R5-Autostart-Beweis fehlt danach). Freigabe: `bash scripts/install_units.sh --release-hold` → `bash scripts/install_units.sh` (enabled alle vier) → `systemctl --user start tradingbot-scheduler.service …` (Plan §6 E-3). Der E-3-Block im Plan (`docs/concepts/phase17_testbed_plan.md`) ist `status: snapshot` (L3) und wurde **nicht** editiert — der Release-Schritt steht hier (Phase-17-Kopf) und gehört in den E-3-Lauf.
- **Datenreparatur der 3 730 alten `ig`-Bars** (Plan T14: löschen statt verschieben) — folgt in **E-3** zusammen mit dem Scheduler-Restart; bis dahin bleibt der DB-Zustand mit den +2-h-Bars stehen.
- **Live-Beweis B-5/B-6** (Monitor-Re-Adoption, Breaker-Worst-Case) kommt erst mit E-3/E-4 (Handelstag).
- **Fleet-Abstimmung (eurfleet-Session):** deren Repo (Restart-Liste) ist theirs — der Bot-Anteil ist hier erledigt. 201 wird am **31.10.** wie geplant gepatcht; der Reboot darf den Scheduler nicht starten (Autostart `disabled` + Guard).

### Open questions / blockers

- **Scheduler ist gestoppt** (`is-active=inactive`, `is-enabled=disabled`). Alle übrigen Punkte (Datenreparatur der 3 730 alten `ig`-Bars, Promotion-Bridge-Backfill 29 NULL-Zeilen, Fleet §14.8 OpenCode + z.ai, B-5-/B-6-Live-Beweis) — **keine Änderung** gegenüber Session #1–#7.
- **Plan-Snapshot-Drift > +60 Zeilen (B-7-Anker):** im Phasenkopf dokumentiert, **nicht** im Plan gefixt (📕-Konvention). Braucht eine Nikinger-Entscheidung, ob der Plan vor Block C neu aufgelegt wird.
- **Hold-Marker ist untracked** (`data/state/` → pro Host). Ein zweiter Host braucht den Marker ebenfalls, wenn der Scheduler dort gestoppt bleiben soll.
- **Kein Eingriff in Phase-16-Doku:** `phase16_activation/PHASE16_E3_RUNBOOK_v4.md` §3 beschreibt die Deploy-Sequenz ohne Hold — ein Cross-Phase-Edit wäre außerhalb Phase 17. Der Release-Schritt steht hier (Phase-17-Kopf); der Nikinger entscheidet, ob P16 nachgezogen wird.
- **B-10 wirkt erst ab dem nächsten Discovery-Neustart** (E-3) — der laufende Daemon nutzt noch den alten Code.
- **Review-Gate vor E-3 (AK22)** ist weiterhin ⏳ (Claude-Code-Session, Anthropic; Schwerpunkte B-5, B-6, C-4, B-3, B-2 — B-7/B-8/B-9/B-10 kommen hinzu).

### Session-end-Hinweis

- **Σ 2004** (16 Suiten + root, Sweep-Kommando aus dem Phase-Kopf). meta_m1 informativ, nicht in Σ.
- **Commits:** 5 (4 Code-Blöcke + 1 Doku). Push = Nikinger (Phase-17-Konvention).
- **Kern-Erkenntnis:** *Block B ist keine Sammlung kosmetischer Fixes, sondern die Voraussetzung dafür, dass die ausgiebigen Tests nach Phase 17 überhaupt etwas messen.* B-7 stellt die **Verlinkung** zwischen Abstain-Lesson und `decision_context` her (3 669/3 669 NULL → ab Tag 1 nach E-3 `abstain_record_id IS NOT NULL`), B-8 senkt das K5-Rauschen an der Quelle (statt das Kriterium zu lockern), B-9 verhindert, dass jeder Stop per SIGKILL endet (ohne `shutdown()`-Reconcile), B-10 macht den Discovery-Daemon überhaupt erst aus einer append-only Quelle belegbar.

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
