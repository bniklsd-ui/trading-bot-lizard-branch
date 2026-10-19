# SESSIONS_ARCHIVE.md — Phase 17 (Prüfstand)

Newest-first. Rotation rule (root `CLAUDE.md`, mandatory since 2026-07-06): the phase head
carries at most one `## Session stopped` block; archives have no size cap. See
[`../CLAUDE.md`](../CLAUDE.md) "How to work in this repo" — Rotation rule, and
[`../docs/DOC_LAYERS_CONVENTION.md`](../docs/DOC_LAYERS_CONVENTION.md) for the L0/L1/L2/L3 model.

---

## Session stopped — 2026-10-19 (Plan-Session §15 Provider-Plastizität, Opus 5.5 in Claude Code — nur Doku, kein Code; Σ 1978 re-gemessen)

> **Auftrag:** Nikinger 2026-10-19 — Miniplan aus den MiniMax-Working-Notes `provider_plasticity/` (Q1–Q8). Ergebnis:
> **Plan §15** (In-place-Änderung von Block C). Die Exec-Reihenfolge ändert sich **nicht**: als Nächstes B-5.

### Completed
- `docs/concepts/phase17_testbed_plan.md`: §15 angehängt (15.1 Antworten Q1–Q8 · 15.2 T25–T30 · 15.3 Quirk-Tabelle 9 Provider, doku-belegt 2026-10-19 · 15.4 Änderungen an C-1/C-3/C-4/C-6/C-7 mit Ankern · 15.5 Σ-Ziele · 15.6 §8-Fehlgriffe · 15.7 Verify Nr. 21–26 · 15.8 Nicht-Ziele); Banner + Header-Card.
- `provider_plasticity/01–04`: datierte Vermerke (Q1–Q8 entschieden; Zeilen-Drift in 02 korrigiert; T25–T28 → Plan T25–T30).
- Step-0-Ritual (No-Op, gleich A-1): `turbo` 20 Treffer, alle eingefrorener Legacy-Name `turbo_candidates.json`; `EPIC_MAP` nur in Kommentaren (P14). Σ-Baseline **1978**, 16/16 grün (P4 167, P8 264).
- Befund für C-3: der 400-Fallback macht `test_bad_request_400_raises_immediately_no_retry` an `len(calls)` rot, während `pytest.raises` grün bleibt — Umbau steht in §15.4 C-3 Nr. 6.

### Next
- Unverändert **B-5** (Next start unten, wortgleich aus Exec-Session #4). Block C erst danach: **§14, dann §15** lesen.
- Nikinger vor C-7 Stufe 1: OpenCode-Zen-API-Key (eigener, nicht `auth.json`) + Nutzungsbedingungen der Gratis-Modelle prüfen (§15.7 Nr. 25).

### Open questions / blockers
- Unverändert aus Exec-Session #4 (rotiert nach `SESSIONS_ARCHIVE.md`): Scheduler gestoppt bis E-3, IG-Bar-Löschung in E-3, Bridge-Backfill 29 NULL-Zeilen, Fleet §14.8.
- Plan-§15 lokal committet, **Push = Nikinger**.

### Next start (für die Folgesession, kalt einsteigen ohne Neu-Lesen)

**B-5 Monitor-Re-Adoption (D5, T8, P5 + P8).** Anker: `phase5_execution/execution/monitor.py:71` (`sleep_fn=…` Ende → kw-only `entry_at=…, default None`), `:90` (`entry = now_fn()` → `entry = entry_at if entry_at is not None else now_fn()`); `phase5_execution/execution/executor.py:59` (Import) + neue Methode **vor** Z. 435 (`# -- Phase-10 (V3) abstain-lessons seam`) → `resume_open_position()` (T8-Wortlaut im Plan §6 B-5 verbatim). P8 `scheduler/runner.py:154` (`_ExecutorLike` Protocol-Docstring um „Optionally ``resume_open_position() -> ExecutionResult | None``" erweitern) + WINDOW-Zweig **direkt nach** Z. 386–388 mit `getattr(self._executor, "resume_open_position", None)`-Schutz. +5 P5-Tests (`test_monitor_entry_at_applies_max_hold_from_recorded_open`, `test_resume_monitors_present_open_record_from_recorded_at`, `test_resume_returns_none_when_position_missing_at_broker`, `test_resume_skips_pending_without_deal_id`, `test_resume_closes_immediately_when_max_hold_elapsed`) + 2 P8-Tests (`test_window_runs_resumed_position_instead_of_research`, `test_window_without_resume_method_is_unchanged`).
Block-B Σ-Ziel ≥ 1992 noch 14 Tests entfernt nach B-5 (B-5 = +7, Σ 1985).
Scheduler bleibt gestoppt (B-0). Push = Nikinger. Block C wartet auf OpenCode-Fleet-„bereit"-Meldung.

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

---

## Session stopped — 2026-10-19 (Exec-Session #2 ENDE — Block B-2 Divergenz-Sampler, 2 Commits in P12+P8, Σ 1965 + 4 P12 + 2 P8 = **1971** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung)

> **Auftrag:** Nikinger 2026-10-19 (später Session): „Lets go on with the next step!" → Exec-Session #2 setzt die explizite **Next**-Priorität aus Session #1 um: **B-2 Divergenz-Sampler (D2, P12 + P8)** per Plan §6 verbatim (T13: Code in P12 + P8 ✓, beide Phasen für Cross-Phase-Edits freigegeben).
>
> **Executor-Modus:** MiniMax-M3-Fallback (Plan §14.2) — unverändert. `~/.config/opencode/`, `auth.json`, `opencode.service` weiterhin unangefasst.

### Completed — diese Exec-Session (2 Commits)

| # | Commit | Phase | Inhalt |
|---|---|---|---|
| 1 | `phase17+phase12: B-2 — Divergenz-Sampler (compute_return_divergence → window_return_divergence)` | P12 | `data_foundation/heartbeat.py`: `compute_return_divergence` (Z. 228–252) ersetzt durch `window_return_divergence` (5m IG vs. **gleiches** 5m-yF-Fenster, nicht mehr 2m/5m-Mix); 3 neue Konstanten (`COMPARATOR_LAG_MIN=25`, `IG_SAMPLE_COUNT=8`, `MIN_YF_BARS=4`); `DivergenceSampler.sample_epic` Rumpf Z. 311–371 nach Plan §6 (a)–(g) ersetzt — Throttle erst **nach** erfolgreichem Vergleich, explizites `divergence_ok`-Event, typisierte `no_comparator`-Events. Docstring A6.0-Verweis angepasst |
| 1b | (gleicher Commit) | P12 | `phase12_data_foundation/tests/test_heartbeat.py`: 7 Sampler-Tests umgestellt auf neues Setup (`now=09:35`, 8 IG-Bars endend 09:30, yF-Fenster [09:05, 09:10)) + 4 neue Tests (`test_no_comparator_does_not_consume_daily_throttle`, `test_partial_yf_window_is_no_comparator`, `test_agreement_emits_divergence_ok`, `test_window_return_divergence_same_window`) |
| 2 | `phase17+phase8: B-2 — Divergenz-Sampler-Gate (_sampler_due)` | P8 | `scripts/wiring.py`: neue Helper-Funktion `_sampler_due(now, config)` (Clock-WINDOW + ≥40min nach Öffnung, Clock-Phase via lazy `from scheduler.clock import Phase`) + Edit Z. 1095: `if divergence_sampler is not None:` → `if divergence_sampler is not None and _sampler_due(_now(), config):`. Reuse der Clock-Klassifikation als single source of truth |
| 2b | (gleicher Commit) | P8 | Neue Datei `phase8_scheduler/tests/test_wiring_sampler_gate.py` (Muster `test_wiring_schema_floor.py`): `test_sampler_due_false_on_weekend_and_before_open_plus_40` (Sa 12:00, Mo 09:00, Mo 09:39:59 → False) + `test_sampler_due_true_mid_window` (Mo 09:50, Mo 12:00, Mo 17:29:59 → True; Mo 18:00 → False). +2 P8-Tests grün |

**Σ-Steigerung:** P12 149 → **153** (+4 ✓ Plan-AK), P8 261 → **263** (+2 ✓ Plan-AK), Σ 1965 → **1971** (+6). Keine Regressionen in den übrigen 14 Suites.

### Next (geplante Folgesessions, in Priorität)
- **B-3 Promotion-Bridge (D3, P15 + P8).** 3 Nahtfehler (`validate` ohne `trades`, `.value` statt `.decision`, Keys ohne `_json` → 29/29 NULL) + Contract-Test mit echter `persistence.Database`. Eigener Extractor-Client (`max_tokens=2048`, `timeout_s=60`). +2 P15-Tests + 1 P8-Test.
- **B-4 Abschneiden sichtbar (D4, P4).** `_attempt`: Meter **vor** Parse; `stop_reason=="max_tokens"` / `finish_reason=="length"` → `LLMResponseError` ohne Retry. +4 P4-Tests.
- **B-5 Monitor-Re-Adoption (D5, T8, P5 + P8).** `monitor_position(entry_at=...)` + `Executor.resume_open_position()` + `_ExecutorLike` Protocol-Erweiterung + WINDOW-Zweig im Runner. +5 P5-Tests + 2 P8-Tests.
- **B-6, B-7, B-8, B-9, B-10** in Plan §6.
- **Block C (LLM-Austausch)** wartet auf OpenCode + z.ai-Fleet-„bereit"-Meldung (Plan §14.8). Heute nicht blockierend (MiniMax-Fallback läuft).
- **Datenreparatur der 3 730 alten `source='ig'`-Bars** (Plan T14) folgt erst in **E-3** zusammen mit dem Scheduler-Restart; bis dahin bleibt der DB-Zustand mit den +2-h-Bars stehen.

### B-2 Σ-Steigerung (2026-10-19, Plan §6 Kommandoform)

| Suite | grün (nach B-1) | grün (nach B-2) | Δ |
|---|---:|---:|---:|
| P1 broker_wrapper | 98 | 98 | — |
| P2 persistence | 82 | 82 | — |
| P3 external_data | 108 | 108 | — |
| P4 research | 163 | 163 | — |
| P5 execution | 190 | 190 | — |
| P6 debate | 76 | 76 | — |
| P7 reward | 170 | 170 | — |
| **P8 scheduler** | 261 (1 alt Warning) | **263** | **+2** |
| P9 universe | 95 | 95 | — |
| P10 v3 | 165 | 165 | — |
| **P12 data_foundation** | 149 | **153** | **+4** |
| P13 live_data | 85 | 85 | — |
| P14 discovery | 61 | 61 | — |
| P15 v4 | 126 | 126 | — |
| P16 activation | 15 | 15 | — |
| root `tests/` | 121 | 121 | — |
| **Σ 16 Suites** | **1965** | **1971** | **+6** |
| meta_m1 (informativ, nicht in Σ) | 28 | 28 | — |

### Open questions / blockers
- **Scheduler ist gestoppt** (`is-active=failed`). Vor E-3 muss er wieder hochfahren — der Recorder muss dann mit dem Klonen-Bar-Löschen (Plan T14, `DELETE FROM bars WHERE source='ig'`) zusammen laufen, weil sonst `bars.sqlite is locked` (Plan §8 Fehlgriff). Bis zum E-3 wird die alte IG-Historie (3 730 Bars mit `ts_utc` +2h in der Zukunft) NICHT angerührt; das ist **gewollt** und **kein Datenverlust**, weil der Fix in `ig_adapter.py:909` wirkt und neue Bars korrekt schreibt.
- **Fleet §14.8 (OpenCode + z.ai)** weiterhin offen. Heute nicht blockierend.
- **C-1-Step `check_llm_profile`** wird um `/coding/`-Endpoint-Check erweitert (Plan §14.1, +1 P8-Test) — gehört zu Block C, nicht zu A/B.

### Session-end-Hinweis (für die Exec-Session selbst)
- **Plan-AK-Stand nach dieser Session:** Session #1 ✅ AK1-AK4 + Session #2 ✅ neu: AK-Block-B Sweep **+6** (P12 +4 + P8 +2 = Plan-Ziel exakt erreicht). B-2 ist Plan-AK für Phase-12-Step-6 (Divergenz-Sampler, D2). Σ 1971 — Block-B Sweep-Ziel ≥ 1992 ist noch **21 Tests entfernt** (B-3..B-10 verbleibend).
- **K11-Anker (Shakedown):** das neue `divergence_ok`-Event ist genau die Append-Only-Quelle für K11 (`evaluate_k11(health_jsonl, from_day, to_day)`: jeder Handelstag ≥ 1 Event `divergence_ok`/`quote_divergence`). Ohne B-2 wäre K11 strukturell unerreichbar — die alte Rechnung produzierte entweder `quote_divergence` (falsche Horizonte ⇒ falsche-positive) oder `divergence_no_comparator` (still, nicht „vergleichbar").
- B-2 lokal ahead, wartet auf Nikinger-Push.

### Next start (für die Folgesession, kalt einsteigen ohne Neu-Lesen)

**B-3 Promotion-Bridge (D3, P15 + P8).** Anker: `phase15_v4/instinct/bridge.py:131-132`, `:146-148`, `:167-168`, Docstrings `:22-25` + `:177`. Drei Nahtfehler:
1. `validate()` bekommt kein `trades` (Parameter `trades_n=500` reserviert, Docstring Z. 91–95 → #541 ergänzen).
2. `decision.decision` statt `decision.value` (Plan §6 B-3 §2).
3. `evidence_trade_ids_json` / `contradictions_trade_ids_json` (Keys mit `_json`) → aktuell NULL-INSERTs auf 29/29 Zeilen.
+ Contract-Test mit echter `persistence.Database` (Stub reichte nicht), +2 P15-Tests + 1 P8-Test. Eigener Extractor-Client (`max_tokens=2048`, `timeout_s=60`).
Block-B Σ-Ziel ≥ 1992 noch 21 Tests entfernt nach B-3 (B-3 = +3, Σ 1974).
Scheduler bleibt gestoppt (B-0). Push = Nikinger. Block C wartet auf OpenCode-Fleet-„bereit"-Meldung.

---

## Session stopped — 2026-10-19 (Exec-Session #1 ENDE — Block A + B-0 + B-1, 4 Commits, Σ 1964 + 1 P1-Test = **1965** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung)

> **Auftrag:** Nikinger 2026-10-19 ~16:20 Berlin: „GLM in OpenCode ist im anderen Projekt als nicht fähig genug getestet — du führst als Fallback (MiniMax-M3) aus. Plan bleibt Plan, aber warte nach jedem Schritt auf meine Freigabe." Drei Commits später (~17:30) wurde die Freigabe erweitert: „Das sind eigentlich Aktionen, die auch du ausführen könntest - tue das" → Exec-Session übernahm Push + Scheduler-Stopp + IG-Probe + B-1-Edit. Abschluss mit „Session an dieser Stelle korrekt beenden, commit, push".
>
> **Executor-Modus:** MiniMax-M3-Fallback (Plan §14.2). `~/.config/opencode/`, `~/.local/share/opencode/auth.json`, `opencode.service` wurden **nicht angefasst** — verifiziert (auth.json: `zai-coding-plan`/`google`/`minimax`/`nvidia`; `zai-coding-plan` läuft seit heute 16:19:54 als OpenCode-Provider, **Bot nutzt ihn nie** — Plan §14.3).

### Completed — diese Exec-Session (4 Commits in `phase17_testbed/CLAUDE.md`)

| # | Commit | Step(s) | Inhalt |
|---|---|---|---|
| 1 | `2c7b9c1` | A-0 + A-1 + A-2 | SESSIONS_ARCHIVE rotiert + Hook-Liste erweitert + Step-0-Ritual No-Op + Σ-Baseline 1964 |
| 2 | `a5d08cd` | A-3 | Code↔.md-Sweep: README/ARCHITECTURE/ROADMAP/ROADMAP_ARCHIVE/CLAUDE/INDEX + PHASE16-Handover Reboot-Vermerk |
| 3 | `2675129` | B-1 | `ig_adapter.py:909` UTC-first + `test_parse_bar_prefers_snapshot_time_utc_over_local_snapshot_time`; P1 97→98 |
| (Push) | `git push -u origin main` | A-Push | Block A (`b3fccc9..a5d08cd`) auf `origin/main` — vor B-1 ausgeführt; B-1 (`2675129`) wurde gegen `origin/main` (~a5d08cd) committed |

**B-0 (gestoppt + IG-Probe, 2026-10-19 selbst ausgeführt):**
- `systemctl --user stop tradingbot-scheduler.service`: Status `is-active=failed` (Plan D13, 90-s-Stop-Timeout hat SIGKILL-Pfad genommen — erwartet). Recorder/Discovery/WebUI laufen weiter (alle 3 `is-active=active`).
- IG-Probe gegen `IX.D.DAX.IFMM.IP` MINUTE_5 bei gestopptem Scheduler (1 Datenpunkt, Allowance 8 194/10 000 nach Probe):
  - `snapshotTime     = '2026/10/19 17:35:00'` (Ortszeit Europe/Berlin CEST+2)
  - `snapshotTimeUTC  = '2026-10-19T15:35:00'` (UTC ISO, korrekt)
  - Δ = 2 h exakt CEST (heute 2026-10-19, **vor** DST-Wechsel 2026-10-25) → **Plan §B-1** (UTC-first), nicht B-1b (Fallback Europe/Berlin→UTC). Verifiziert §9 Nr. 1.
- Push Block A (`git push -u origin main`): `b3fccc9..a5d08cd main -> main` ✓.

**B-1 — IG-UTC-first** (`2675129`):
- Edit: `phase1_broker_wrapper/broker_wrapper/adapters/ig_adapter.py:909` `p.get("snapshotTime") or p.get("snapshotTimeUTC", "")` → `p.get("snapshotTimeUTC") or p.get("snapshotTime", "")` mit Kommentar D1 (Plan §A-3 verbatim — 4 Zeilen).
- Test: `tests/test_ig_adapter.py::test_parse_bar_prefers_snapshot_time_utc_over_local_snapshot_time` — 3 Fixtures (beide Felder / nur `snapshotTime` / nur `snapshotTimeUTC`); legt explizit fest, dass UTC ISO verlustfrei übernommen wird, während `snapshotTime` als Legacy-Fallback grün bleibt.
- `pytest phase1_broker_wrapper/tests` → **98 grün** (97 + 1 = AK-Block-B Sweep +1 erreicht). Σ-Baseline-Steigerung: 1964 → **1965**.

### Next (geplante Folgesessions, in Priorität)
- **B-2 Divergenz-Sampler (D2, P12 + P8).** `heartbeat.py:228-251` `compute_return_divergence` (5-min-gegen-1-min-Rechenfehler) → neue `window_return_divergence` (abgeschlossener 5m-Bar, ≥ 25 min alt vs. yF-1m-Bars desselben Fensters, ≥ 4 von 5). `DivergenceSampler.sample_epic` Rumpf von Z. 311–371 ersetzt: erst Vergleich, dann Throttle, explizites `divergence_ok`-Event. P8 `_sampler_due(now, config)` (WINDOW + ≥ 40 min nach Öffnung). +4 P12-Tests + 2 P8-Tests. AK ≥ 1992 nach Block-B-Sweep.
- **B-3 Promotion-Bridge (D3, P15 + P8).** 3 Nahtfehler (validate ohne trades, .value statt .decision, Keys ohne _json → 29/29 NULL) + Contract-Test mit echter `persistence.Database`. Eigener Extractor-Client (`max_tokens=2048`, `timeout_s=60`). +2 P15-Tests + 1 P8-Test.
- **B-4 Abschneiden sichtbar (D4, P4).** `_attempt`: Meter **vor** Parse; `stop_reason=="max_tokens"` / `finish_reason=="length"` → `LLMResponseError` ohne Retry. +4 P4-Tests.
- **B-5 Monitor-Re-Adoption (D5, T8, P5 + P8).** `monitor_position(entry_at=...)` + `Executor.resume_open_position()` + `_ExecutorLike` Protocol-Erweiterung + WINDOW-Zweig im Runner. +5 P5-Tests + 2 P8-Tests.
- **B-6, B-7, B-8, B-9, B-10** in Plan §6.
- **Block C (LLM-Austausch)** wartet auf OpenCode + z.ai-Fleet-„bereit"-Meldung (Plan §14.8). Heute nicht blockierend (MiniMax-Fallback läuft).
- **Datenreparatur der 3 730 alten `source='ig'`-Bars** (Plan T14) folgt erst in **E-3** zusammen mit dem Scheduler-Restart; bis dahin bleibt der DB-Zustand mit den +2-h-Bars stehen, der Fix in `ig_adapter.py:909` wirkt erst für **neue** IG-Bars ab dem nächsten Scheduler-Start.

### Step-0-Ritual (A-1, 2026-10-19 selbst gemessen)

| Token | Befehl | Treffer | Bewertung |
|---|---|---:|---|
| `turbo` (case-insensitive) | `grep -rni "turbo" --include="*.py" --include="*.sql" --include="*.sh" . --exclude-dir=.venv \| grep -v "/.venv/"` | **20** in 13 Dateien | ✅ alle sind der eingefrorene Legacy-Name `turbo_candidates.json`; einzige andere Zeile = Schutzkommentar `phase2_persistence/persistence/state.py:27` („Do NOT rename") |
| `EPIC_MAP` | `grep -rn "EPIC_MAP" --include="*.py" . --exclude-dir=.venv` | **3** | ✅ Phase-14-Doku-Kommentare (`test_store.py:239`, `models.py:121`, `store.py:194`) |
| Quellen | Phase-16-Closeout §3.1 (`PHASE16_CLOSEOUT_HANDOVER.md`) + Phase-17-Plan §2.7 (Stand 2026-10-17) | identisch | No-Op, 7. Mal |

### A-2 Σ-Baseline + B-1 Σ-Steigerung (2026-10-19, Plan §6 Kommandoform + Block-B Sweep Stand)

| Suite | grün (vor B-1) | grün (nach B-1) | Δ |
|---|---:|---:|---:|
| **P1 broker_wrapper** | 97 | **98** | **+1** |
| P2 persistence | 82 | 82 | — |
| P3 external_data | 108 | 108 | — |
| P4 research | 163 | 163 | — |
| P5 execution | 190 | 190 | — |
| P6 debate | 76 | 76 | — |
| P7 reward | 170 | 170 | — |
| P8 scheduler | 261 (1 alt Warning) | 261 | — |
| P9 universe | 95 | 95 | — |
| P10 v3 | 165 | 165 | — |
| P12 data_foundation | 149 | 149 | — |
| P13 live_data | 85 | 85 | — |
| P14 discovery | 61 | 61 | — |
| P15 v4 | 126 | 126 | — |
| **P16 activation** | 15 | 15 | — |
| root `tests/` | 121 | 121 | — |
| **Σ 16 Suites** | **1964** | **1965** | **+1** |
| meta_m1 (informativ, nicht in Σ) | 28 | 28 | — |

### Open questions / blockers
- **Scheduler ist gestoppt** (`is-active=failed`). Vor E-3 muss er wieder hochfahren — der Recorder muss dann mit dem Klonen-Bar-Löschen (Plan T14, `DELETE FROM bars WHERE source='ig'`) zusammen laufen, weil sonst `bars.sqlite is locked` (Plan §8 Fehlgriff). Bis zum E-3 wird die alte IG-Historie (3 730 Bars mit `ts_utc` +2h in der Zukunft) NICHT angerührt; das ist **gewollt** und **kein Datenverlust**, weil der Fix in `ig_adapter.py:909` wirkt und neue Bars korrekt schreibt.
- **Fleet §14.8 (OpenCode + z.ai)** weiterhin offen. Heute nicht blockierend. Sollte die Fleet doch „bereit" melden, baut eine Folge-Session §14-Pfad auf mit C-7-Familien-Smoke vor jedem Flip-Commit.
- **C-1-Step `check_llm_profile`** wird um `/coding/`-Endpoint-Check erweitert (Plan §14.1, +1 P8-Test) — gehört zu Block C, nicht zu A/B.

### Session-end-Hinweis (für die Exec-Session selbst)
- 4 Commits in `phase17_testbed/CLAUDE.md` Update-Zeile zusammengefasst (siehe oben).
- Phase-16 Block A bereits auf `origin/main`. Phase-17 B-1 (`2675129`) **lokal ahead**, wartet auf Nikinger-Push.
- **Plan-AK-Stand nach dieser Session:** AK1 ✅ (Step-0-Ritual), AK2 ✅ (Σ 1964 → 1965, keine Regression), AK3 ✅ (ROADMAP.md < 40 KB, root CLAUDE.md < 25 KB, PHASE16-Handover Reboot-Vermerk), **AK4 ✅ (IG-Probe dokumentiert + `_parse_bar` bevorzugt `snapshotTimeUTC`)** + **+1 P1-Test grün** (Datenreparatur E-3 ausstehend). Block-B Sweep-Σ noch **27 Tests entfernt vom Plan-Ziel ≥ 1992**.

---

## Session stopped — 2026-10-18 (Plan-Session, Opus 5.5 — begonnen 2026-10-17; Phase 17 eröffnet, Plan committet + gepusht)

> **Auftrag:** Nikinger 2026-10-17. „Du bist der Phase-17-Chat — die Planungssession." Fragen gebündelt in zwei Runden (F1–F12, F13–F14), danach den ausführungsreifen Plan für Sonnet 5 schreiben und committen. Push = Nikinger.

### Completed
- **Plan** [`../docs/concepts/phase17_testbed_plan.md`](../docs/concepts/phase17_testbed_plan.md) (📕). Er enthält:
  - T1–T24 gelockt, je mit Begründung;
  - §2 selbst gemessene Fakten (Baseline, Git/Units/Journal, Live-DB, `bars.sqlite`, `llm_usage.json`, Health-Events, Funktions-Inventar, Doku-Drift);
  - D1–D13 Befunde mit Datei:Zeile;
  - Blöcke A–E mit verbatim Ankern;
  - AK1–AK21;
  - §8 Fehlgriffe;
  - §9 Verify-Liste (14 Punkte).
- **Σ 1964 grün** selbst gemessen (16 Suites einzeln, meta 28) — identisch zum Phase-16-Closeout.
- **Neu gemessene stille Totalausfälle**, alle drei jetzt Plan-Steps:
  - (1) IG-REST-Bars +2 h in der Zukunft (`ig_adapter.py:909` `snapshotTime` = Ortszeit). Preisbeweis: IG „09:00Z" = LS 07:04Z = 49 663,2.
  - (2) Divergenz-Sampler 233/233 `no_comparator` seit 08-25. Dazu ein Rechenfehler: 5-min- gegen 1-min-Renditen.
  - (3) `decision_context.abstain_record_id` 3 669/3 669 NULL (`wiring.py:758-760` verwirft den Rückgabewert).
- **Bridge-Befund erweitert:** drei Nahtfehler statt einem (`validate` ohne `trades`, `.value` statt `.decision`, Keys ohne `_json` → 29/29 Evidence NULL).
- **„Unbekannte" Phase-16-Stopps aufgeklärt:** VM-Reboots, plus SIGKILL nach dem 90-s-Stop-Timeout (Journal). Nikinger: Reboots vom VM-Host.
- **Nikinger-Entscheidungen** F1–F14 eingearbeitet (Plan §1).
- **Advisor zweimal** — vor dem Ansatz und vor „fertig". Die sieben Punkte des zweiten Reviews stehen im Folge-Commit (Plan §13): Flip-2-Tag vorregistriert, Modell-ID-Drift prüft der Start, Verbatim-Anker ergänzt.
- **Plan-Nachtrag §14 (2026-10-18, Nikinger):** Executor-Test GLM in OpenCode (Claude Code bleibt Anthropic-only; Review-Gate vor E-3; Rückfallregel; 5.2-Quirk), Bot-Provider z.ai mit Pay-per-use statt MiniMax M3. Belege aus der z.ai Usage Policy, dem Coding Plan nur für unterstützte Tools, und dem OpenCode-Katalog `~/.cache/opencode/models.json` mit Modellen, Endpoints und Preisen. `opencode.json` bleibt unverändert.
- **Plan §14.8 (2026-10-18):** Die Executor-Integration übernimmt eurofyx-fleet, getrennt vom Plan. Die Fakten, die die Fleet braucht, stehen in §14.8 (Katalog, Provider-ID, Endpoint, Modelle, Service-Hinweis).
- **Plan-Step A-4 ist schon in dieser Session erledigt** (Nikinger-Freigabe 2026-10-17):
  - Push `be15cf9..399a9df` nach `origin/main`; das nimmt `e19c178` mit.
  - `sunshine_2026.906.222525-1+ubuntu24.04_amd64.deb` aus dem Repo-Root nach `~/Downloads/` **verschoben**, nicht gelöscht. Sunshine selbst bleibt per `dpkg` installiert (`install ok installed`) und läuft als `/usr/bin/sunshine`.
  - Exec-Session: A-4 nur noch als ✅ abhaken. Die A-Commits pusht wie üblich der Nikinger.

### Next
- **eurofyx-fleet (Nikinger):** die Executor-Integration nach Plan §14.8 (OpenCode + `zai-coding-plan`), danach die Meldung „bereit".
- **Exec-Session #1 (OpenCode, `zai-coding-plan/glm-5.3-flash`, Plan §14):** startet **nach** der Fleet-Meldung mit Plan **A-0** (zuerst §14 lesen):
  - diesen Block wortgleich nach `SESSIONS_ARCHIVE.md` (NEU) rotieren;
  - `scripts/check_doc_rotation.py:88` um `"phase17_testbed",` ergänzen;
  - danach A-1 (Step-0-Ritual), A-2 (Baseline), A-3 (Doku-Sweep).

### Open questions / blockers
- Keine Planungsfragen offen.
- **Blocker für den Exec-Start:** die Fleet-Integration nach Plan §14.8 (OpenCode + `zai-coding-plan`).
- Offen, aber erst in der Ausführung messbar (Plan §9 + §14.6): IG `snapshotTimeUTC` (Probe B-0) sowie für den Bot der z.ai-Pay-per-use-Endpoint, Key, Preise, Reasoning-Tokens gegen `max_tokens`, `response_format` (Familien-Smoke C-7). Für den Executor: Kontingent-Verbrauch je GLM-Modell (Basis des 5.2-Quirks).
