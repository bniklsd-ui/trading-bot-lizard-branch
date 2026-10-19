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
updated: 2026-10-19 (Exec-Session #4 ENDE — B-4 Abschneiden sichtbar, 1 Commit in P4, Σ 1974 + 4 P4-Tests = **1978** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #3 ENDE — B-3 Promotion-Bridge Nahtfehler, 2 Commits in P15+P8, Σ 1971 + 2 P15 + 1 P8 = **1974** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #2 ENDE — B-2 Divergenz-Sampler Reparatur, Σ 1965 + 4 P12-Tests + 2 P8-Tests = **1971** grün) | 2026-10-19 (Exec-Session #1 ENDE — A-0+A-1+A-2 + A-3 + B-0 + B-1, Σ 1965) | 2026-10-18 (Plan-§14-Nachtrag) | 2026-10-17 (Plan-Session, Opus 5.5)
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
| Nach Exec-Session #3 (B-3, 2026-10-19) | **1974** | +2 P15 + 1 P8 |
| Nach Exec-Session #4 (B-4, 2026-10-19) | **1978** | +4 P4 |
| Ziel nach Block B / C / D / E-1 | ≥ 1992 / ≥ 2016 / ≥ 2019 / ≥ 2026 | Plan §6 + 1 Test aus §14 (C-1 `/coding/`-Prüfung) |

## Phase-17-Status

| Block | Status |
|---|---|
| A Haushalt | ✅ (Session #1) |
| B-0 Scheduler-Stopp + IG-Probe | ✅ (Session #1) |
| B-1 IG-UTC-first | ✅ (Session #1) |
| B-2 Divergenz-Sampler | ✅ (Session #2) |
| B-3 Promotion-Bridge (3 Nahtfehler) | ✅ (Session #3) |
| B-4 Abschneiden sichtbar (D4) | ✅ (Session #4) |
| B-5 … B-10 | ⏳ |
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

## Session stopped — 2026-10-19 (Exec-Session #4 ENDE — Block B-4 Abschneiden sichtbar, 1 Commit in P4, Σ 1974 + 4 P4-Tests = **1978** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung)

> **Auftrag:** Nikinger 2026-10-19 (später Session): „Lets go on with the next step!" → Exec-Session #4 setzt die explizite **Next**-Priorität aus Session #3 um: **B-4 Abschneiden sichtbar (D4, P4)** per Plan §6 B-4 verbatim (T13: Code in P4 ✓, Cross-Phase nicht nötig — beide Edits im selben P4-Modulbaum).
>
> **Executor-Modus:** MiniMax-M3-Fallback (Plan §14.2) — unverändert. `~/.config/opencode/`, `auth.json`, `opencode.service` weiterhin unangefasst.

### Completed — diese Exec-Session (1 Commit)

| # | Commit | Phase | Inhalt |
|---|---|---|---|
| 1 | `phase17+phase4: B-4 — Abschneiden sichtbar (meter-first, stop_reason=max_tokens / finish_reason=length)` | P4 | `research/llm_client.py` `_attempt` Z. 411–422 → **vor** Z. 400 verschoben (Kommentar: „meter first: a response that fails to parse was still billed"); Parse-Fehlerzweig Z. 416–432 erweitert um `if getattr(message, "stop_reason", None) == "max_tokens": raise LLMResponseError(f"LLM output truncated (stop_reason=max_tokens, max_tokens={...}, model={...})") from None` (T20 — nicht transient, `ask_candidate` wickelt es als „LLM call failed" ab und wiederholt **nicht**). `research/llm_openai_compat.py` `_attempt`: nach `body = self._raw_call(payload)` zuerst `choice = body["choices"][0]`; **`self.last_finish_reason: str \| None = choice.get("finish_reason")`** neu im Konstruktor (Z. 162–164); Meter-Block **vor** Parse verschoben (Z. 265–280); Parse-Fehlerzweig erweitert um `if self.last_finish_reason == "length": raise LLMResponseError(f"LLM output truncated (finish_reason=length, max_tokens={...}, model={...})") from None`. Docstring `_attempt` aktualisiert (T20 + B-4). |

**Σ-Steigerung:** P4 163 → **167** (+4 ✓ Plan-AK exakt: 2 für `llm_client.py` + 2 für `llm_openai_compat.py`; die neuen Tests sind `test_truncated_unparseable_raises_without_retry` / `test_meters_even_when_parse_fails` und `test_length_truncation_raises_without_retry` / `test_meters_even_when_parse_fails`), Σ 1974 → **1978** (+4). Keine Regressionen in den übrigen 15 Suites (P2-Persistenz als Externer Konsument mit-verifiziert — 82 grün unverändert).

### Test-Detail (B-4, neu hinzugekommen)

P4 (`test_llm_client.py`):
- `test_truncated_unparseable_raises_without_retry` — `SimpleNamespace` mit `content=[…]`, `usage=_FakeUsage()`, `stop_reason="max_tokens"` (FakeRawCall-Eintrag); `pytest.raises(LLMResponseError, match="stop_reason=max_tokens")`; `len(fake.calls) == 1` (kein Retry).
- `test_meters_even_when_parse_fails` — `make_text_message("not json at all")` zweimal (transient → `ask_candidate` retried einmal); Log-Datei `tmp_path / "llm_usage.json"`; nach `pytest.raises(LLMResponseError)` enthält sie **2 Records** (pre-B-4 wären es 0; jetzt exakt der Pre-B-4-Bug).

P4 (`test_llm_openai_compat.py`):
- `test_length_truncation_raises_without_retry` — `_FakeResponse(200, body)` mit `finish_reason="length"`; `pytest.raises(LLMResponseError, match="finish_reason=length")`; `len(calls) == 1`; `client.last_finish_reason == "length"` (neues Attribut).
- `test_meters_even_when_parse_fails` — Body ohne `finish_reason` (transient, retried einmal); Log-Datei `tmp_path / "llm_usage.json"`; nach `pytest.raises(LLMResponseError)` enthält sie **2 Records**.

### Next (geplante Folgesessions, in Priorität)
- **B-5 Monitor-Re-Adoption (D5, T8, P5 + P8).** `monitor_position(entry_at=...)` + `Executor.resume_open_position()` + `_ExecutorLike` Protocol-Erweiterung + WINDOW-Zweig im Runner. +5 P5-Tests + 2 P8-Tests.
- **B-6, B-7, B-8, B-9, B-10** in Plan §6 (Breaker Worst-Case, Abstain-Naht, Paper-Logstufen, Stop-Timeout, Discovery-Beleg).
- **Block C (LLM-Austausch)** wartet auf OpenCode + z.ai-Fleet-„bereit"-Meldung (Plan §14.8). Heute nicht blockierend (MiniMax-Fallback läuft).
- **Datenreparatur der 3 730 alten `source='ig'`-Bars** (Plan T14) folgt erst in **E-3** zusammen mit dem Scheduler-Restart; bis dahin bleibt der DB-Zustand mit den +2-h-Bars stehen.

### B-4 Σ-Steigerung (2026-10-19, Plan §6 Kommandoform)

| Suite | grün (nach B-3) | grün (nach B-4) | Δ |
|---|---:|---:|---:|
| P1 broker_wrapper | 98 | 98 | — |
| P2 persistence | 82 | 82 | — |
| P3 external_data | 108 | 108 | — |
| **P4 research** | 163 | **167** | **+4** |
| P5 execution | 190 | 190 | — |
| P6 debate | 76 | 76 | — |
| P7 reward | 170 | 170 | — |
| P8 scheduler | 264 | 264 | — |
| P9 universe | 95 | 95 | — |
| P10 v3 | 165 | 165 | — |
| P12 data_foundation | 153 | 153 | — |
| P13 live_data | 85 | 85 | — |
| P14 discovery | 61 | 61 | — |
| P15 v4 | 128 | 128 | — |
| P16 activation | 15 | 15 | — |
| root `tests/` | 121 | 121 | — |
| **Σ 16 Suites** | **1974** | **1978** | **+4** |
| meta_m1 (informativ, nicht in Σ) | 28 | 28 | — |

### Open questions / blockers
- **Scheduler ist gestoppt** (`is-active=failed`). Vor E-3 muss er wieder hochfahren — der Recorder muss dann mit dem Klonen-Bar-Löschen (Plan T14, `DELETE FROM bars WHERE source='ig'`) zusammen laufen, weil sonst `bars.sqlite is locked` (Plan §8 Fehlgriff). Bis zum E-3 wird die alte IG-Historie (3 730 Bars mit `ts_utc` +2h in der Zukunft) NICHT angerührt; das ist **gewollt** und **kein Datenverlust**, weil der Fix in `ig_adapter.py:909` wirkt und neue Bars korrekt schreibt. **Identisch zu Session #2/#3 — keine Änderung.**
- **Promotion-Bridge-Backfill für die 29 NULL-Zeilen**: unverändert offen (Session #3).
- **Fleet §14.8 (OpenCode + z.ai)** weiterhin offen. Heute nicht blockierend.
- **C-1-Step `check_llm_profile`** wird um `/coding/`-Endpoint-Check erweitert (Plan §14.1, +1 P8-Test) — gehört zu Block C, nicht zu A/B.
- **K6-Verbindung (C-5 / D-2):** B-4 macht den Meter jetzt **konsistent vor** dem Parse. Damit zählt K6 (`budget.py` `_TOKEN_FIELDS`) **jeden** abschneidenden Request — sowohl Anthropic (`stop_reason=max_tokens`) als auch OpenAI-Compat (`finish_reason=length`). Pre-B-4 unter-zählte das K6-Budget um genau diese Abschneider. Die M3-Ausnahmeliste (`budget_exempt_models`) bleibt davon unberührt — sie gilt nur für Anthropic-/M3-Calls, nicht für das Messen selbst.
- **Sensor für Shakedown-Bericht:** `last_finish_reason` ist jetzt auf jeder OpenAI-Compat-Instanz gesetzt (oder `None` initial). Auf der Anthropic-Seite fehlt eine entsprechende `last_stop_reason`-Surfaced-Property — die B-4-Tests lesen sie via `getattr(message, "stop_reason", None)`, ohne sie auf der Client-Instanz zu halten. Ob das ein Phase-17-Folgepunkt ist (Konsumenten-Wunsch aus C-5 / D-2 her) oder eine §10-Sache, lässt sich erst entscheiden, wenn ein Konsument „ich brauch `client.last_stop_reason`" sagt. **Heute nicht entschieden.**

### Session-end-Hinweis (für die Exec-Session selbst)
- **Plan-AK-Stand nach dieser Session:** Session #1 ✅ AK1-AK4 + Session #2 ✅ +6 AK-Block-B Sweep (P12 +4 + P8 +2) + Session #3 ✅ +3 AK-Block-B Sweep (P15 +2 + P8 +1) + **Session #4 ✅ +4 AK-Block-B Sweep (P4 +4)** = Σ 1978. Plan-AK-Block-B Sweep Σ ≥ 1992 noch **14 Tests entfernt** (B-5..B-10 verbleibend: B-5 +7, B-6 +3, B-7 +2, B-8 +1, B-9 +0 (Unit-Test läuft in E-3), B-10 +1 = +14 exakt).
- **K11 / K6 Anker:** B-4 hat den Token-Meter **vor** Parse verschoben — K6 sieht ab jetzt jeden abschneidenden Request. `last_finish_reason` (OpenAI-Compat) ist ein neuer Sensor; eine entsprechende `last_stop_reason` (Anthropic) ist im B-4-Commit **nicht** hinzugefügt worden — falls die K6-Berichtslinie das braucht, ist es ein Folgepunkt, kein B-4-Defekt.
- **T20-Verbindung:** die `LLMResponseError("LLM output truncated (…)", from None)` ist so konstruiert, dass `ask_candidate`'s Retry-Schleife sie als nicht-transient klassifiziert (`_is_transient` prüft `ConnectionError | TimeoutError | named SDK transient | status_code` — `LLMResponseError` matcht nichts davon) und sofort als `LLMResponseError(f"LLM call failed: {exc!r}") from exc` hochwirft. Der äußere Wrap ändert die Retry-Semantik nicht — `len(fake.calls) == 1` ist die Verifikation.
- B-4 lokal ahead (`138cf7b` = 1 Commit nach `origin/main = d086603`), wartet auf Nikinger-Push.

### Next start (für die Folgesession, kalt einsteigen ohne Neu-Lesen)

**B-5 Monitor-Re-Adoption (D5, T8, P5 + P8).** Anker: `phase5_execution/execution/monitor.py:71` (`sleep_fn=…` Ende → kw-only `entry_at=…, default None`), `:90` (`entry = now_fn()` → `entry = entry_at if entry_at is not None else now_fn()`); `phase5_execution/execution/executor.py:59` (Import) + neue Methode **vor** Z. 435 (`# -- Phase-10 (V3) abstain-lessons seam`) → `resume_open_position()` (T8-Wortlaut im Plan §6 B-5 verbatim). P8 `scheduler/runner.py:154` (`_ExecutorLike` Protocol-Docstring um „Optionally ``resume_open_position() -> ExecutionResult | None``" erweitern) + WINDOW-Zweig **direkt nach** Z. 386–388 mit `getattr(self._executor, "resume_open_position", None)`-Schutz. +5 P5-Tests (`test_monitor_entry_at_applies_max_hold_from_recorded_open`, `test_resume_monitors_present_open_record_from_recorded_at`, `test_resume_returns_none_when_position_missing_at_broker`, `test_resume_skips_pending_without_deal_id`, `test_resume_closes_immediately_when_max_hold_elapsed`) + 2 P8-Tests (`test_window_runs_resumed_position_instead_of_research`, `test_window_without_resume_method_is_unchanged`).
Block-B Σ-Ziel ≥ 1992 noch 14 Tests entfernt nach B-5 (B-5 = +7, Σ 1985).
Scheduler bleibt gestoppt (B-0). Push = Nikinger. Block C wartet auf OpenCode-Fleet-„bereit"-Meldung.
