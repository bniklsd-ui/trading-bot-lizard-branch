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
updated: 2026-10-19 (Exec-Session #5 ENDE — B-5 Monitor-Re-Adoption, 1 Commit in P5+P8, Σ 1978 + 5 P5 + 2 P8 = **1985** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Plan-Session §15 Provider-Plastizität — Forward-Agenda C2 → Plan §15, Σ-Ziele C/D/E-1 +9, Σ 1978 re-gemessen) | 2026-10-19 (Exec-Session #4 ANSCHLUSS — `provider_plasticity/` Working-Notes-Set angelegt (kein Plan, Input für Opus-Miniplan-Session; 5 INDEX-Einträge); Nikinger-Entscheidungen Q1–Q8 ausstehend) | 2026-10-19 (Exec-Session #4 ENDE — B-4 Abschneiden sichtbar, 1 Commit in P4, Σ 1974 + 4 P4-Tests = **1978** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #3 ENDE — B-3 Promotion-Bridge Nahtfehler, 2 Commits in P15+P8, Σ 1971 + 2 P15 + 1 P8 = **1974** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #2 ENDE — B-2 Divergenz-Sampler Reparatur, Σ 1965 + 4 P12-Tests + 2 P8-Tests = **1971** grün) | 2026-10-19 (Exec-Session #1 ENDE — A-0+A-1+A-2 + A-3 + B-0 + B-1, Σ 1965) | 2026-10-18 (Plan-§14-Nachtrag) | 2026-10-17 (Plan-Session, Opus 5.5)
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
| Nach Exec-Session #5 (B-5, 2026-10-19) | **1985** | +5 P5 + 2 P8 |
| Ziel nach Block B / C / D / E-1 | ≥ 1992 / ≥ 2025 / ≥ 2028 / ≥ 2035 | Plan §6 + §14 (+1) + §15 (+9, P4 +5 · P8 +4) |
| Re-Messung Exec-Session #5 (2026-10-19) | **1985** | unverändert, 16/16 grün |

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
| B-6 … B-10 | ⏳ |
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
| #5 (B-5) | 2026-10-19 | MiniMax-M3-Fallback (Plan §14.2) — kein z.ai-Modell heute in Verwendung | B-5 Monitor-Re-Adoption (D5, T8, P5 + P8) | n/a | Σ 1978 → **1985** (+7, P5 +5 + P8 +2 ✓ Plan-AK exakt) | — | B-5 ist die letzte Single-Commit-Block: 1 Commit (154f460) in P5+P8. Bit-Identität via `getattr(self._executor, "resume_open_position", None)` — alle Bestands-Fakes unverändert grün |
| — | — | — | — | — | — | — | Der 5.2-Quirk: bei Flash-ähnlichem Kontingent-Verbrauch einen vergleichbaren Step mit `glm-5.2` fahren |

**Review-Gate vor E-3 (AK22):** ⏳ (Claude-Code-Session, Anthropic; Schwerpunkte B-5, B-6, C-4, B-3, B-2)

> **Integration des Executors = eurofyx-fleet, getrennt vom Plan (Plan §14.8, Nikinger 2026-10-18).** Die Fleet richtet ein: OpenCode-Provider `zai-coding-plan` (Auth), Modell, Neustart von `opencode.service`, MiniMax-Rückweg. Diese Exec-Session fasst `~/.config/opencode/`, `auth.json` und `opencode.service` **nicht** an. A-0 startet erst, wenn die Fleet „OpenCode + z.ai bereit" meldet.

---

## Session stopped — 2026-10-19 (Exec-Session #5 ENDE — Block B-5 Monitor-Re-Adoption, 1 Commit in P5+P8, Σ 1978 + 5 P5 + 2 P8 = **1985** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung)

> **Auftrag:** Nikinger 2026-10-19 (später Session): „Mini Plan is written, go on please." → Exec-Session #5 setzt die explizite **Next**-Priorität aus Exec-Session #4 + die §15-Plan-Session-Festlegung „als Nächstes B-5" um: **B-5 Monitor-Re-Adoption (D5, T8, P5 + P8)** per Plan §6 B-5 verbatim (T13: Code in P5 + P8 ✓, beide Phasen für Cross-Phase-Edits freigegeben).
>
> **Executor-Modus:** MiniMax-M3-Fallback (Plan §14.2) — unverändert. `~/.config/opencode/`, `auth.json`, `opencode.service` weiterhin unangefasst.

### Completed — diese Exec-Session (1 Commit)

| # | Commit | Phase | Inhalt |
|---|---|---|---|
| 1 | `154f460` | P5 + P8 | **P5 `execution/monitor.py`**: kw-only-Param `entry_at: datetime \| None = None` hinter `sleep_fn` (default = bit-identisch zum Status quo); `entry = entry_at if entry_at is not None else now_fn()` (Default-Pfad nutzt weiterhin `now_fn()`); Docstring ergänzt um die T8-Semantik („an already-elapsed max_hold/square-off closes immediately"). **P5 `execution/executor.py`**: Import `from execution.monitor import _position_present, monitor_position` (Z. 59); neue Methode `resume_open_position() -> ExecutionResult \| None` zwischen `_notify_closed` (Ende Z. 433) und dem Phase-10-Seam-Kommentar (Z. 435), iteriert `exec_state.open_references()`, filtert auf `status='OPEN'` + `deal_id`, fragt `broker.get_open_positions()`, springt bei nicht-ok read mit Logger-Warning zurück, überspringt am Broker verschwundene Refs (reconcile_startups missing-Set), baut `OrderPlan` aus dem Record (`currency=self.config.default_currency`), parst `recorded_at` (UTC ISO) als `entry_at`; `monitor_position(... entry_at=entry_at)`; `ExecutionAbort` → `self._abort(...)`; `self._notify_closed(result)` damit der Phase-7-Close-Seam den Re-Adopt-Pfad mit dem real-Close-Fall identisch abrechnet. **P8 `scheduler/runner.py`**: `_ExecutorLike` Protocol-Docstring (Z. 155–160) um „Optionally ``resume_open_position() -> ExecutionResult \| None`` (Phase 17 B-5) — read via ``getattr``, so a fake without it keeps the runner bit-identical" ergänzt; WINDOW-Zweig (Z. 386–388) **direkt danach** (vor `_maybe_refresh_universe` und allen weiteren WINDOW-Operationen): `resume = getattr(self._executor, "resume_open_position", None); resumed = resume() if callable(resume) else None; if resumed is not None: state = self._state_store.record_cycle(state, resumed); self._clock.sleep(self._cycle_interval_s); return` — `getattr(... , None)` ist die kritische Bit-Identität für alle Bestands-Fakes ( `_FakeExecutor` heute ohne die Methode). |
| 1b | (gleicher Commit) | P5 + P8 | **P5 `tests/test_monitor.py` +1**: `test_entry_at_applies_max_hold_from_recorded_open` — `entry_at = _at(9,0)`, `now_fn = _Clock(_at(14,0))`, `config = ExecutionConfig()` (max_hold 240 min); `result.status == "TIME_STOP"`, `"max_hold" in detail`, `close_position_calls == [DEAL_ID]`. **P5 `tests/test_executor.py` +4** (Helper-Funktionen `_seed_open_reference` + `_tz_aware_now`): `test_resume_monitors_present_open_record_from_recorded_at` (Broker `[present, gone]` → `CLOSED_BY_BROKER`, `sink.closed` gefeuert mit demselben `ClosedTrade` wie `run()`); `test_resume_returns_none_when_position_missing_at_broker` (Broker leer → `None`, `close_position_calls == []`); `test_resume_skips_pending_without_deal_id` (`record_pending` ohne `mark_open` → Broker **nie** gefragt, PENDING ref bleibt in `open_references()`); `test_resume_closes_immediately_when_max_hold_elapsed` (recorded 09:00Z + now 14:00Z = 5 h > 4 h max_hold → `TIME_STOP` mit `"max_hold" in detail`, `close_position_calls == [DEAL_ID]` genau einmal). **P8 `tests/test_runner.py` +2** (neue `_FakeResumableExecutor`-Klasse mit `resume_open_position()`): `test_window_without_resume_method_is_unchanged` (Default-`_FakeExecutor` ohne die Methode → `getattr` returns `None`, WINDOW fällt durch zum Standard-`research_tick`+`executor.run`-Pfad, `trades_today == 1`) und `test_window_runs_resumed_position_instead_of_research` (`_FakeResumableExecutor(resume_result=_Result("TIME_STOP", profit_loss=-30.0))` → `executor.resume_calls == 1`, `executor.run_calls == 0`, `research_tick.calls == 0`, `trades_today == 1`, `realized_pnl_today == -30.0`). **Σ-Steigerung:** P5 190 → **195** (+5 ✓ Plan-AK exakt), P8 264 → **266** (+2 ✓ Plan-AK exakt), Σ 1978 → **1985** (+7). Keine Regressionen in den übrigen 14 Suites (P2-Persistenz als Externer Konsument mit-verifiziert — 82 grün unverändert). |

### Test-Detail (B-5, neu hinzugekommen)

P5 (`test_monitor.py`):
- `test_entry_at_applies_max_hold_from_recorded_open` — s. Commit-Tabelle 1b.

P5 (`test_executor.py`):
- Helper `_seed_open_reference`/`_tz_aware_now` schreiben via `_read`/`_write` direkt in den Store (Record-Level-Test-Hack, dokumentiert mit `# noqa: SLF001`), weil die öffentliche API `recorded_at` immer auf `_utcnow()` setzt — die Tests brauchen eine andere Recorded-At, sonst ist der elapsed-Check tautologisch. TZ-aware `now_fn` ist erforderlich, weil `fromisoformat(...replace("Z", "+00:00"))` immer eine aware datetime produziert (Subtraktion gegen naive now würde `TypeError` werfen).
- `test_resume_monitors_present_open_record_from_recorded_at` — `positions_sequence=[_positions(_open_position()), _positions()]`, der erste Monitor-Poll sieht die Position, der zweite (oder die direkten Sequenz-Wiederholung) sieht sie weg → CLOSED_BY_BROKER; `sink.closed[0].deal_id == "DIAAAA-FAKE"` pinnt, dass die Phase-7-Naht die reale `deal_id` des re-adoptierten Trades bekommt.
- `test_resume_returns_none_when_position_missing_at_broker` — Broker-Positionsliste enthält das DEAL_ID nicht, der Open-Record bleibt **unverändert** in `exec_state` (reconcile_startups missing-Set übernimmt).
- `test_resume_skips_pending_without_deal_id` — `record_pending` ohne `mark_open` → `status='PENDING'`, `deal_id=None`; resume filtert raus ohne Broker-Call; der PENDING-Ref bleibt in `open_references()` zur späteren reconcile_startup-Bearbeitung.
- `test_resume_closes_immediately_when_max_hold_elapsed` — recorded 09:00Z, now 14:00Z (5 h > 4 h default max_hold), Broker present; `result.status == "TIME_STOP"`, `close_position_calls == [DEAL_ID]` (genau einmal; pre-Resume würde der erste Poll bereits 5 h alt sehen).

P8 (`test_runner.py`):
- `_FakeResumableExecutor` hat **explizit** eine `resume_open_position()`-Methode (kein duck-typing über Dunder-Erbschaft) — der Test der WINDOW-Branch hängt am echten Methoden-Lookup.
- `test_window_without_resume_method_is_unchanged` — pinnt das `getattr(... , None)`-Pattern: ein Fake ohne die Methode darf den Runner **nicht** brechen, der bestehende `test_window_happy_path_runs_research_then_bare_execute` (Z. 277–290) tut das implizit — dieser neue Test macht es explizit.
- `test_window_runs_resumed_position_instead_of_research` — der Symmetrie-Test: wenn `resume()` etwas liefert, wird der `record_cycle` mit dem resumed-Ergebnis gefüttert (`trades_today` ++, `realized_pnl_today += -30.0`) und der Loop nimmt den üblichen `cycle_interval_s`-Sleep, bevor er zur nächsten Iteration geht.

### Next (geplante Folgesessions, in Priorität)
- **B-6 Breaker Worst-Case (D6, T9, P8).** `scripts/wiring.py`: neue Modul-Funktion `_realized_pnl_today(conn, session_date) -> float` (OPEN-Zeilen zählen als `-initial_risk`; OPEN mit `initial_risk IS NULL` → `RuntimeError` → `AutoConfirm` fail-closed); Closure Z. 1009–1016 ersetzt Rumpf + erweitert Docstring. +3 P8-Tests in neuer Datei `tests/test_wiring_breaker.py` (echte `persistence.Database(":memory:")` + `run_migrations()`): `test_booked_pnl_only_when_no_open_rows`, `test_open_row_counts_as_minus_initial_risk`, `test_open_row_without_initial_risk_raises`. Plan-AK P8 ≥ **269**, Σ-Ziel nach B-6 ≥ **1988**.
- **B-7, B-8, B-9, B-10** in Plan §6.
- **Block C (LLM-Austausch)** wartet auf OpenCode + z.ai-Fleet-„bereit"-Meldung (Plan §14.8). Heute nicht blockierend (MiniMax-Fallback läuft).
- **Datenreparatur der 3 730 alten `source='ig'`-Bars** (Plan T14) folgt erst in **E-3** zusammen mit dem Scheduler-Restart; bis dahin bleibt der DB-Zustand mit den +2-h-Bars stehen.

### B-5 Σ-Steigerung (2026-10-19, Plan §6 Kommandoform)

| Suite | grün (nach B-4) | grün (nach B-5) | Δ |
|---|---:|---:|---:|
| P1 broker_wrapper | 98 | 98 | — |
| P2 persistence | 82 | 82 | — |
| P3 external_data | 108 | 108 | — |
| P4 research | 167 | 167 | — |
| **P5 execution** | 190 | **195** | **+5** |
| P6 debate | 76 | 76 | — |
| P7 reward | 170 | 170 | — |
| **P8 scheduler** | 264 | **266** | **+2** |
| P9 universe | 95 | 95 | — |
| P10 v3 | 165 | 165 | — |
| P12 data_foundation | 153 | 153 | — |
| P13 live_data | 85 | 85 | — |
| P14 discovery | 61 | 61 | — |
| P15 v4 | 128 | 128 | — |
| P16 activation | 15 | 15 | — |
| root `tests/` | 121 | 121 | — |
| **Σ 16 Suites** | **1978** | **1985** | **+7** |
| meta_m1 (informativ, nicht in Σ) | 28 | 28 | — |

### Open questions / blockers
- **Scheduler ist gestoppt** (`is-active=failed`). Vor E-3 muss er wieder hochfahren — der Recorder muss dann mit dem Klonen-Bar-Löschen (Plan T14, `DELETE FROM bars WHERE source='ig'`) zusammen laufen, weil sonst `bars.sqlite is locked` (Plan §8 Fehlgriff). Bis zum E-3 wird die alte IG-Historie (3 730 Bars mit `ts_utc` +2h in der Zukunft) NICHT angerührt; das ist **gewollt** und **kein Datenverlust**, weil der Fix in `ig_adapter.py:909` wirkt und neue Bars korrekt schreibt. **Identisch zu Session #1/#2/#3/#4 — keine Änderung.**
- **Promotion-Bridge-Backfill für die 29 NULL-Zeilen**: unverändert offen (Session #3).
- **Fleet §14.8 (OpenCode + z.ai)** weiterhin offen. Heute nicht blockierend.
- **B-5-Live-Beweis** (E-4-Probe) noch ausstehend — die `resume_open_position()`-Methode selbst ist grün, aber der Beweis, dass sie nach einem echten Restart einen AEX-Orphan tatsächlich vom `recorded_at` an weitermonitoren würde, kommt erst in der Shakedown-Phase.
- **TZ-Wahrheit der `recorded_at`-Deserialisierung (find-now-during-tests):** `fromisoformat(recorded_at.replace("Z", "+00:00"))` liefert immer eine tz-aware UTC-datetime; die `monitor_position`-Subtraktion `(now - entry)` wirft `TypeError`, wenn `now` (aus `self.now_fn`) naive ist. **Live**: in `wiring.py` ist der Executor mit `tz.now` (UTC) gebaut → kompatibel. **Tests**: daher die `_tz_aware_now()`-Helper. Das ist **kein Defekt** — es ist genau die Stelle, an der eine naive now_fn-Architektur (P5-Tests-Default) gegen die tz-aware Live-Bindestelle stößt; die Tests müssen die Live-Realität nachstellen. **Folgepunkt:** Wenn jemals ein zweiter Konsument resume_open_position mit naivem now_fn aufruft, explodiert es — im Code nicht vorgesehen, aber als Sicherheits-Note für künftige Adapter sinnvoll (kein Plan-Tracker-Punkt, nur Erfahrung).

### Session-end-Hinweis (für die Exec-Session selbst)
- **Plan-AK-Stand nach dieser Session:** Session #1 ✅ AK1-AK4 + Session #2 ✅ +6 + Session #3 ✅ +3 + Session #4 ✅ +4 + **Session #5 ✅ +7 (P5 +5 + P8 +2)** = Σ 1985. Plan-AK-Block-B Sweep Σ ≥ 1992 noch **7 Tests entfernt** (B-5..B-10 verbleibend: B-6 +3, B-7 +2, B-8 +1, B-9 +0 (Unit-Test läuft in E-3), B-10 +1 = +7 exakt).
- B-5 lokal ahead (`154f460` = 1 Commit nach `origin/main = d086603+phase17-A-3+...+d18de05`), wartet auf Nikinger-Push.
- **Schlüssel-Erkenntnisse für Block-C / Block-E:**
  - B-5 schließt den ersten der vier Phase-16-PASS-Blocker (Monitor-Orphan: AEX id 26 lief 6 Tage ohne `max_hold`-Check, Phase-16-Closeout §4). Die anderen drei sind Token-Budget (K6 — D-Block), Promotion-Bridge (`bridge.py:146`-Familie, mit B-3 Halbwerk repariert), Breaker-Blindfenster (B-6 als nächstes).
  - `getattr(self._executor, "resume_open_position", None)` ist die einzige **strukturelle** Bit-Identität zwischen neuer WINDOW-Branch und altem Verhalten — jeder Executor ohne die Methode (alle Bestands-Fakes, alle Bestands-Wire-ups) läuft exakt wie vor B-5. Wenn eine spätere Session `assert hasattr(self._executor, "resume_open_position")` o. ä. hinzufügen wollte → STOP, das bricht die Bit-Identität.
  - `_seed_open_reference` schreibt via `_read`/`_write` direkt in die JSON-Datei (private API, `# noqa: SLF001`). Das ist **kein** sauberer API-Weg, aber die einzige Möglichkeit, `recorded_at` außerhalb von `_utcnow()` zu setzen — wenn `recorded_at` jemals zu einem First-Class-Konstruktor-Argument wird, fällt das weg. Heute nicht.

### Next start (für die Folgesession, kalt einsteigen ohne Neu-Lesen)

**B-6 Breaker Worst-Case (D6, T9, P8).** Anker: `scripts/wiring.py` Top-Level **neue** Funktion `_realized_pnl_today(conn: Any, session_date: str) -> float` (T9-SQL mit `CASE WHEN status='OPEN' THEN -initial_risk ELSE profit_loss END`, NULL-`initial_risk`-Check via zweites `SUM` der OPEN-und-NULL-Zeilen wirft `RuntimeError`); Closure Z. 1009–1016 (Anker `def realized_pnl_today(session_date: str) -> float:`) → Rumpf `return _realized_pnl_today(db.conn, session_date)` + Docstring „(Contract E + Phase 17 B-6 worst case)". Neue Datei `phase8_scheduler/tests/test_wiring_breaker.py` mit +3 Tests gegen echte `persistence.Database(":memory:")` + `run_migrations()`: `test_booked_pnl_only_when_no_open_rows`, `test_open_row_counts_as_minus_initial_risk`, `test_open_row_without_initial_risk_raises`. Plan-AK P8 ≥ **269**.
Block-B Σ-Ziel ≥ 1992 noch 7 Tests entfernt nach B-6 (B-6 = +3, Σ 1988).
Scheduler bleibt gestoppt (B-0). Push = Nikinger. Block C wartet auf OpenCode-Fleet-„bereit"-Meldung.

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
