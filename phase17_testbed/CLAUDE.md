---
status: live
purpose: PHASE-HEAD, Phase 17 (Prüfstand) — 🔄 eröffnet 2026-10-17 (Plan-Session, Opus 5.5). Keine neuen Features. Tiefe Härtung des Bestehenden — vier Phase-16-PASS-Blocker + drei neu gemessene stille Totalausfälle zu, LLM pro Rolle austauschbar (Research zuerst auf GLM über die z.ai-API mit Pay-per-use, Plan §14), Report + Vorregistrierung v5 als Fundament für die ausgiebigen Tests. Executor: offener Test GLM in OpenCode (§14).
read-when: jede Phase-17-Exec-Session — zuerst diesen Kopf, dann den `## Session stopped`-Block, dann den Plan
detail: L1
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase17_testbed_plan.md               # 📕 der Plan (T1–T24, D1–D13, Blöcke A–E, AK1–AK21, §8 Fehlgriffe, §9 Verify)
  - ../phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md     # 📕 Vorgänger-Handover (§4 PASS-Blocker, §5 E1–E8)
  - ../phase16_activation/scripts/autonomy_report.py       # Report-Skript, Block E erweitert es in place (--prereg v5)
  - ./SESSIONS_ARCHIVE.md                                  # rotierte Session-Blöcke (L3, newest-first)
updated: 2026-10-19 (Exec-Session #3 ENDE — B-3 Promotion-Bridge Nahtfehler, 2 Commits in P15+P8, Σ 1971 + 2 P15 + 1 P8 = **1974** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #2 ENDE — B-2 Divergenz-Sampler Reparatur, Σ 1965 + 4 P12-Tests + 2 P8-Tests = **1971** grün) | 2026-10-19 (Exec-Session #1 ENDE — A-0+A-1+A-2 + A-3 + B-0 + B-1, Σ 1965) | 2026-10-18 (Plan-§14-Nachtrag) | 2026-10-17 (Plan-Session, Opus 5.5)
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
systemctl --user stop tradingbot-scheduler.service       # bis B-9 deployt ist: ≤ 90 s, ggf. SIGKILL (Plan D13, erwartet)
ps aux | grep "scheduler.run" | grep -v grep             # Gegenprobe: leer
```

- Recorder, Discovery und WebUI halten keine IG-Session und laufen weiter (Plan T22).
- Den Neustart macht nur **E-3**, die Deploy-Sequenz im Plan.

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
| Ziel nach Block B / C / D / E-1 | ≥ 1992 / ≥ 2016 / ≥ 2019 / ≥ 2026 | Plan §6 + 1 Test aus §14 (C-1 `/coding/`-Prüfung) |

## Phase-17-Status

| Block | Status |
|---|---|
| A Haushalt | ✅ (Session #1) |
| B-0 Scheduler-Stopp + IG-Probe | ✅ (Session #1) |
| B-1 IG-UTC-first | ✅ (Session #1) |
| B-2 Divergenz-Sampler | ✅ (Session #2) |
| B-3 Promotion-Bridge (3 Nahtfehler) | ✅ (Session #3) |
| B-4 … B-10 | ⏳ |
| C LLM-Austausch | ⏳ |
| D Token-Budget | ⏳ |
| E Test-Fundament | ⏳ |

## Executor-Evaluation (Plan §14.2 — je Exec-Session eine Zeile)

| Session | Datum | Modell (`zai-coding-plan/…`) | Steps | Kontingent vorher → nachher (z.ai-Dashboard) | Tests | Rückfall | Notiz |
|---|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — | Der 5.2-Quirk: bei Flash-ähnlichem Kontingent-Verbrauch einen vergleichbaren Step mit `glm-5.2` fahren |

**Review-Gate vor E-3 (AK22):** ⏳ (Claude-Code-Session, Anthropic; Schwerpunkte B-5, B-6, C-4, B-3, B-2)

> **Integration des Executors = eurofyx-fleet, getrennt vom Plan (Plan §14.8, Nikinger 2026-10-18).** Die Fleet richtet ein: OpenCode-Provider `zai-coding-plan` (Auth), Modell, Neustart von `opencode.service`, MiniMax-Rückweg. Diese Exec-Session fasst `~/.config/opencode/`, `auth.json` und `opencode.service` **nicht** an. A-0 startet erst, wenn die Fleet „OpenCode + z.ai bereit" meldet.

---

## Session stopped — 2026-10-19 (Exec-Session #3 ENDE — Block B-3 Promotion-Bridge, 2 Commits in P15+P8, Σ 1971 + 2 P15 + 1 P8 = **1974** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung)

> **Auftrag:** Nikinger 2026-10-19 (später Session): „Lets go on with the next step!" → Exec-Session #3 setzt die explizite **Next**-Priorität aus Session #2 um: **B-3 Promotion-Bridge (D3, P15 + P8)** per Plan §6 B-3 verbatim (T13: Code in P15 + P8 ✓, beide Phasen für Cross-Phase-Edits freigegeben).
>
> **Executor-Modus:** MiniMax-M3-Fallback (Plan §14.2) — unverändert. `~/.config/opencode/`, `auth.json`, `opencode.service` weiterhin unangefasst.

### Completed — diese Exec-Session (2 Commits)

| # | Commit | Phase | Inhalt |
|---|---|---|---|
| 1 | `phase17+phase15: B-3 — Promotion-Bridge Nahtfehler (trades param, .decision, _json keys)` | P15 | `instinct/bridge.py`: `_extract_and_validate` Z. 131–132 → + `trades = self.db.get_recent_trades(n=self.trades_n)`; Z. 146–148 → `decision = self.validator.validate(instinct, trades)` + `self.db.update_instinct_status(int(row_id), decision.decision)` (Nahtfehler 1+2); `_instinct_to_row` Z. 167–168 → Keys `evidence_trade_ids_json` / `contradictions_trade_ids_json` (Nahtfehler 3, _INSTINCT_COLUMNS-Whitelist hat sonst verschluckt → 29/29 NULL); Modul-/Funktion-/Parameter-Docstrings angepasst (T18: „a promotion takes effect from the next restart") |
| 1b | (gleicher Commit) | P15 | `tests/test_instinct_bridge.py`: `_FakeValidator.validate` akzeptiert jetzt `(instinct, trades)` + returnt die echte `InstinctValidation`-Dataclass (nie mehr `._D.value`-Shim); `_FakeDB.get_recent_trades(n=500)` neu (echo der `n` für Regressions-Pin) + import von `InstinctValidation`; **+1 P15-Test** `test_after_trade_closed_passes_db_trades_to_validator`; **+1 P15-Test** `test_bridge_contract_real_database_and_validator` — echte `persistence.Database(tmp/"bridge_contract.sqlite").run_migrations()` + 3 CLOSED-Trades + echter `InstinctValidator(min_evidence=3)`; dieser **eine** Test fängt alle drei Nahtfehler (`.json`-NULL → #3, `status='proposed'` → #1 oder #2) |
| 2 | `phase17+phase8: B-3 — Eigener Extractor-Client (2048 tokens / 60 s) + T18-Comment` | P8 | `scripts/wiring.py`: neue Modul-Konstanten `_INSTINCT_EXTRACTOR_MAX_TOKENS = 2048` (4× Brain's `lesson_max_tokens`; Instinct-Payloads sind strukturierte Arrays) und `_INSTINCT_EXTRACTOR_TIMEOUT_S = 60.0` (gegen Brain's kürzerem `lesson_timeout_s`); `_build_reward_sink` baut jetzt einen **zweiten** `LLMClient` mit diesen Limits für den Extractor (Brain- und Extractor-Client teilen model + key + token-meter, nur Per-Call-Knöpfe getrennt); Build-Pfad bleibt inline bis C-4 den Bau in `_build_llm` zieht. T18-Comment in `build_scheduler` (Anker Z. 963) korrigiert: „a promotion takes effect from the next restart — executor reads exec_cfg once at construction" |
| 2b | (gleicher Commit) | P8 | `tests/test_wiring_reward_sink.py` (+1 Test): `test_extractor_has_own_client_with_instinct_limits` — pin't, dass `bridge.extractor._llm is not sink.brain._llm` (Phase-15-Mirror: Brain `self._llm = llm_client` brain.py:184, Extractor `self._llm = llm_client` extractor.py:262) UND dass der Extractor-Client die Modul-Konstanten transportiert (`max_tokens == 2048`, `timeout_s == 60.0`) UND dass `model` + `token_meter_path` zwischen Brain und Extractor identisch bleiben (das Modell trennt sich nicht, nur die Per-Call-Knöpfe). 4/4 reward-sink-tests grün |

**Σ-Steigerung:** P15 126 → **128** (+2 ✓ Plan-AK exakt: +1 Param-Test + 1 Contract-Test), P8 263 → **264** (+1 ✓ Plan-AK exakt), Σ 1971 → **1974** (+3). Keine Regressionen in den übrigen 14 Suites (P2-Persistenz als Externer Konsument mit-verifiziert — 82 grün unverändert).

### Next (geplante Folgesessions, in Priorität)
- **B-4 Abschneiden sichtbar (D4, P4).** `_attempt` (P4 `llm_client.py:378–423` + P4 `llm_openai_compat.py:242–287`): Meter **vor** Parse; `stop_reason=="max_tokens"` / `finish_reason=="length"` → `LLMResponseError` ohne Retry. +4 P4-Tests.
- **B-5 Monitor-Re-Adoption (D5, T8, P5 + P8).** `monitor_position(entry_at=...)` + `Executor.resume_open_position()` + `_ExecutorLike` Protocol-Erweiterung + WINDOW-Zweig im Runner. +5 P5-Tests + 2 P8-Tests.
- **B-6, B-7, B-8, B-9, B-10** in Plan §6.
- **Block C (LLM-Austausch)** wartet auf OpenCode + z.ai-Fleet-„bereit"-Meldung (Plan §14.8). Heute nicht blockierend (MiniMax-Fallback läuft).
- **Datenreparatur der 3 730 alten `source='ig'`-Bars** (Plan T14) folgt erst in **E-3** zusammen mit dem Scheduler-Restart; bis dahin bleibt der DB-Zustand mit den +2-h-Bars stehen.

### B-3 Σ-Steigerung (2026-10-19, Plan §6 Kommandoform)

| Suite | grün (nach B-2) | grün (nach B-3) | Δ |
|---|---:|---:|---:|
| P1 broker_wrapper | 98 | 98 | — |
| P2 persistence | 82 | 82 | — |
| P3 external_data | 108 | 108 | — |
| P4 research | 163 | 163 | — |
| P5 execution | 190 | 190 | — |
| P6 debate | 76 | 76 | — |
| P7 reward | 170 | 170 | — |
| **P8 scheduler** | 263 | **264** | **+1** |
| P9 universe | 95 | 95 | — |
| P10 v3 | 165 | 165 | — |
| P12 data_foundation | 153 | 153 | — |
| P13 live_data | 85 | 85 | — |
| P14 discovery | 61 | 61 | — |
| **P15 v4** | 126 | **128** | **+2** |
| P16 activation | 15 | 15 | — |
| root `tests/` | 121 | 121 | — |
| **Σ 16 Suites** | **1971** | **1974** | **+3** |
| meta_m1 (informativ, nicht in Σ) | 28 | 28 | — |

### Open questions / blockers
- **Scheduler ist gestoppt** (`is-active=failed`). Vor E-3 muss er wieder hochfahren — der Recorder muss dann mit dem Klonen-Bar-Löschen (Plan T14, `DELETE FROM bars WHERE source='ig'`) zusammen laufen, weil sonst `bars.sqlite is locked` (Plan §8 Fehlgriff). Bis zum E-3 wird die alte IG-Historie (3 730 Bars mit `ts_utc` +2h in der Zukunft) NICHT angerührt; das ist **gewollt** und **kein Datenverlust**, weil der Fix in `ig_adapter.py:909` wirkt und neue Bars korrekt schreibt. **Identisch zu Session #2 — keine Änderung.**
- **Promotion-Bridge-Backfill für die 29 NULL-Zeilen** (Phase-15-Closeout §3 Befund-2 Erbe): die 29 Live-DB-Instinct-Zeilen mit `evidence_trade_ids_json IS NULL` werden NICHT retroaktiv gefixt — kein Konsument liest sie heute, AK9-Erbe gilt (`longterm_rules == ()` ⇒ `veto5_empty_rules_is_identity` bleibt grün). Folgearbeit: einmaliger Operator-`UPDATE`-Backfill oder Verwerfen der Null-Zeilen via `DELETE FROM instincts WHERE evidence_trade_ids_json IS NULL` — Entscheidung Block E oder außerhalb der Phase 17.
- **Fleet §14.8 (OpenCode + z.ai)** weiterhin offen. Heute nicht blockierend.
- **C-1-Step `check_llm_profile`** wird um `/coding/`-Endpoint-Check erweitert (Plan §14.1, +1 P8-Test) — gehört zu Block C, nicht zu A/B.

### Session-end-Hinweis (für die Exec-Session selbst)
- **Plan-AK-Stand nach dieser Session:** Session #1 ✅ AK1-AK4 + Session #2 ✅ +6 AK-Block-B Sweep (P12 +4 + P8 +2) + **Session #3 ✅ +3 AK-Block-B Sweep (P15 +2 + P8 +1)** = Σ 1974. Plan-AK-Block-B Sweep Σ ≥ 1992 noch **18 Tests entfernt** (B-4..B-10 verbleibend).
- **K11-Anker (Shakedown):** B-3 hat das Bridge-Statement verifizierbar gemacht (`status == 'validated'`, `evidence_trade_ids_json` populiert). K11 erwartet ≥ 1 `divergence_ok`-Event je Handelstag (B-2-Quelle) — B-3 ändert die K11-Mechanik nicht, aber die Promotion-Bridge-Spur ist jetzt erstmalig in der Lage, validierte Instincts tatsächlich zu erzeugen (`InstinctValidator` bekommt Trades, zählt, transitioned `proposed` → `validated` und stempelt `validated_utc`). Damit kann Block-E-3 (Prereg v5) einen `validate`-Audit-Hook spendieren, der die erste `proposed→validated`-Transition live nachweist.
- **K11-Konsistenz mit dem alten Code:** der alte Bridge-Pfad hat `evidence_trade_ids` an `_INSTINCT_COLUMNS` vorbei geschrieben (Whitelist-Drift). Mit B-3 Fix landen sie im Schema; ein hypothetischer Backfill-SQL-`UPDATE` (siehe Open-Questions) wird nach Konsumenten-Entscheidung sauber.
- B-3 lokal ahead (`3377b0a` + `7c7251d` = 2 Commits vor `origin/main = a5d08cd+phase17-A-3`), wartet auf Nikinger-Push.

### Next start (für die Folgesession, kalt einsteigen ohne Neu-Lesen)

**B-4 Abschneiden sichtbar (D4, P4).** Anker: `phase4_research/research/llm_client.py:378–423` (`_attempt`) und `phase4_research/research/llm_openai_compat.py:242–287` (`_attempt`). Zwei Edits pro Datei: (1) Den Meter-Block **vor** Parse verschieben (Kommentar: „meter first: a response that fails to parse was still billed"); (2) Parse-Fehlerzweig erweitern um `if getattr(message, "stop_reason", None) == "max_tokens": raise LLMResponseError(...)` (bzw. `finish_reason == "length"` im OpenAI-Compat-Pfad). Beide nicht-transient — `ask_candidate` wickelt es als „LLM call failed" ab und wiederholt **nicht**. +4 P4-Tests (`test_llm_client_truncated_unparseable_raises_without_retry`, `test_llm_client_meters_even_when_parse_fails`, `test_openai_compat_length_truncation_raises_without_retry`, `test_openai_compat_meters_even_when_parse_fails`). Plan-AK P4 ≥ 167.
Block-B Σ-Ziel ≥ 1992 noch 18 Tests entfernt nach B-4 (B-4 = +4, Σ 1978).
Scheduler bleibt gestoppt (B-0). Push = Nikinger. Block C wartet auf OpenCode-Fleet-„bereit"-Meldung.
