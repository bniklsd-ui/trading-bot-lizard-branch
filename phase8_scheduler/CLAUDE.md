---
status: closed-phase
purpose: Phase-8 head — autonomous scheduler loop, caps/breakers, verified contracts (phase ✅ live-verified 2026-07-03)
read-when: working in phase8_scheduler/ — read this head + its newest Session-stopped block first
detail: L2
up: ../CLAUDE.md
down:
  - ./SESSIONS_ARCHIVE.md      # full session history (L3)
  - ./README.md
  - ../docs/concepts/phase8_scheduler_concept.md   # full concept/plan snapshot (L3)
updated: 2026-07-06
---
# CLAUDE.md — Phase 8: Scheduler (`phase8_scheduler/`)

> Macht den Bot **autonom**: ein langlaufender Daemon, der unbeaufsichtigt echte
> Demo-Trades erzeugt. **Quelle der Wahrheit ist der Code, nicht dieses Dokument.**
> Vollständiges Design + alle 20 gelockten Entscheidungen + Modul-Plan:
> `../docs/concepts/phase8_scheduler_concept.md`.

## Mission (zuerst lesen)
Phase 8 heißt „Scheduler", aber das Ziel ist **autonome, unbeaufsichtigte Erzeugung
echter Demo-Trades** — alles danach (Confidence aus `INSUFFICIENT`, P9-Instinct-
Promotion) ist auf **reale Outcomes** gegatet. „Einen Cron-Job bauen" ist **nicht** die
Aufgabe. Der harte Pfad ist die **autonome Kandidaten-Generierung** über echtes
P4-Research (**nie** `seed_candidate.py`); ohne sie sammelt der Scheduler **null Daten**.

## AI-Grenze (Projekt-Kernprinzip)
„So wenig AI wie möglich, so viel AI wie nötig." **Phase 8 fügt KEINE neue AI hinzu** —
ein Scheduler ist reine Mechanik. AI bleibt exakt wo sie war: P4-Research-Pick,
(optionale) P6-Debatte, P7-Lesson — alle aus Vorphasen **unverändert** wiederverwendet.
Wer hier ein LLM „entscheiden/sizen/timen/vetoen" lassen will → **stop**, das ist Code.

## Scope
- **DRIN:** Marktzeiten-Daemon (injizierbares `now_fn`/`sleep_fn`), expliziter
  Research-Trigger (autonome Candidates), Auto-Confirm (`confirm_fn`-Ersatz, demo-only,
  fail-closed), Datei-Kill-Switch, Backoff/Trip, Tages-Loss-Breaker, Token-Budget,
  idempotenter Reconcile-Pass, `scheduler_state.json`, Wiring + Operator-Scripts,
  **zuletzt** eine read-mostly Web-UI.
- **DRAUSSEN (Carry-overs):** volles v3-Research-Signalmodell (nur `no_trade_reason`-
  Gerüst jetzt), Instinct→VETO-ECC / Council / `decision_context`-Befüllung (P9),
  Confidence gatet `risk_pct` (bleibt observe-only), UI-Auth, UI-Aktionen über start/stop
  hinaus (P10), `reflect()` Batch-API, volles systemd-Hardening, Live-Account.

## Build-Reihenfolge (verbindlich)
Cleanup → Verify → **autonome Candidates** → Auto-Confirm/Safety → Reconcile →
Loop/Daemon → **zuletzt** Web-UI. Unter Zeit-/Token-Druck fällt die UI weg, **nie** die
Safety. **Stand 2026-06-30: Module 1–12 gebaut + grün (181 Tests) — Phase 8 code-complete +
🟡 nach `main` gemerged** (ehrlich geflaggt, s. `## Session stopped — 2026-06-30`). Es fehlte
damals ein echter Mehr-Zyklen-/Mehr-Tage-Lauf, der (a) einen netto-neuen autonomen Trade in
**einem** sauberen Lauf öffnet+schließt und (b) die Safety-Breaker tatsächlich auslösen sieht —
**beides carried in den v1.5-Hotfix** (`PHASE8_V1.5_HOTFIX_HANDOVER.md`: der Bot abstained fast
immer → Variety + Clamp/Floor + echte Lessons). **Token-Budget by-default scharf** (Default
`200_000` ≈ €0.8/Tag; vorher `None`/aus).

> **✅ Update (2026-07-03): Phase 8 ABGESCHLOSSEN + live-verifiziert.** Beide oben genannten
> fehlenden Punkte sind jetzt bewiesen — der weiterlaufende Live-Test lieferte einen **zweiten**
> net-new autonomen open→close **und** einen tatsächlich **auslösenden Safety-Breaker** (das
> Tages-Token-Budget erschöpfte sich mitten im Lauf und blockierte weitere Trades, fail-closed,
> kein Crash). Nikinger-bestätigt. Der 🟡-Merge-Flag oben ist damit **historisch** (Stand
> 2026-06-30) — der aktuelle Stand ist ✅. Details: `## Session stopped — 2026-07-03 (✅
> Phase-8-Live-Beweis abgeschlossen)` unten. **Nächster Track = V2** (siehe
> `PHASE8_CLOSEOUT_HANDOVER.md`), noch nicht in Claude Code gestartet.

## Harte Regeln (nicht verhandelbar)
- **Demo-only strukturell, fail-closed.** Auto-Confirm gibt `True` **nur** bei: `account
  == "demo"` (aus der Config, **nicht** aus dem `OrderPlan` — der trägt kein `account`,
  s. Contract D) **und** Kill-Switch aus **und** unter Trade-Cap **und** über
  Loss-Breaker **und** Budget ok. Alles ≠ demo → `False` + `logger.critical`. Live-Auto-
  Confirm ist architektonisch gesperrt bis Profit-Validierung.
- **Kein manueller Seed im autonomen Pfad.** `research_tick` ruft **ausschließlich** das
  echte `Research.run()`. Der Marker `"MANUAL SEED (not a real research pick)"` (s.
  Contract C) darf in einem autonomen Candidate **nie** auftauchen (`test_no_manual_seed_marker`).
- **Naht-Treue (additiv, P5 bit-identisch):** der Scheduler verdrahtet `confirm_fn`/
  `reward_sink`/`research_runner` über die **bestehenden** Executor-Seams; er bekommt
  **nie** Broker-Write/Gate/VETO direkt → kann strukturell keinen VETO umgehen.
- **Determinismus:** `now_fn`/`sleep_fn` injiziert; **kein echter `sleep`/Netz/LLM** in
  Unit-Tests; die Loop wird über `now_fn` getrieben + nach K Iterationen abgebrochen.
- **Fail-closed Writes/State:** atomic `scheduler_state.json` (tmp+`os.replace`); jeder
  Cycle prüft den Kill-Switch; Cycle-Exception → Backoff, `max_consecutive_failures` in
  Folge → Kill `auto:backoff` + sauberer Stop.
- **Keyring nie in Dateien**; `get_credential` (Contract: `SERVICE_NAME="tradingbot"`).
  `turbo_candidates.json` NICHT umbenennen. Logging → **stderr**, stdout nur JSON.
  Atomic commits. Kein Subtask „done" ohne grünes `pytest` (gemockt).
- **Commit ⇒ Note-Update (zwingend).** Jeder Step-Abschluss-Commit aktualisiert im
  **selben** Commit die Modul-/Status-Tabelle **und** den `## Session stopped`-Block.

## Caps-Defaults (Testrun, am echten Output zu tunen — Operator-bestätigt 2026-06-27)
- `max_trades_per_day = 5`, `cycle_interval_min = 5`, `max_consecutive_failures = 3`.
- `daily_loss_cap ≈ 3× initial_risk eines Trades` → auf dem ~30K-Demo ≈ **€1800** (eine
  Verlustserie von ~3 pausiert den Tag); v1, am echten Wert tunen. Für ein ~€1K-Live-
  Konto bei Go-Live re-baselinen (≈ €60).
- `account = "demo"` **hart** (Auto-Confirm verweigert alles ≠ demo).

## Modul-Struktur (`scheduler` Paket) — Status pro Step
| Datei | Zweck | Status |
|---|---|---|
| `pyproject.toml` · `requirements.txt` · `README.md` · `CLAUDE.md` | Scaffold + Packaging (Step 2) | ✅ |
| `scheduler/__init__.py` | Paket-Marker (Exports wachsen pro Modul) | ✅ (leer) |
| `scheduler/config.py` | `SchedulerConfig` (frozen) — alle Tunables an einem Ort | ✅ (Modul 1, 10 Tests) |
| `scheduler/exceptions.py` | `SchedulerError`/`PreflightError`/… | ✅ (Modul 2, 6 Tests) |
| `scheduler/clock.py` | `now_fn`/`sleep_fn` injizierbar; Phasen-Klassifikation (config-Fenster + Weekday; `is_market_open` lazy via `market_is_open`) | ✅ (Modul 3, 19 Tests) |
| `scheduler/state.py` | `SchedulerState` ↔ `scheduler_state.json` (atomic); Tages-Rollover (Europe/Berlin) + `record_cycle` (Contract E) | ✅ (Modul 4, 18 Tests) |
| `scheduler/killswitch.py` | KILL-Datei lesen/setzen/löschen (von `safety` + `webui` geteilt) — fail-soft, atomic | ✅ (Modul 5, 12 Tests) |
| `scheduler/command.py` | Start/Stop-Command-Datei (`scheduler_command.json`) lesen/schreiben/löschen — von `webui` (Schreiber) + `runner` (Leser) geteilt; fail-soft, atomic; **soft** Pause/Resume (≠ hartem KILL) | ✅ (Modul 12, 10 Tests) |
| `scheduler/safety.py` | `AutoConfirm` `confirm_fn`: demo + kill + caps + loss-breaker + budget | ✅ (Modul 6, 18 Tests) |
| `scheduler/backoff.py` | konsekutive-Fehler-Tracking + Backoff-Schedule | ✅ (9 Tests) |
| `scheduler/budget.py` | Token-Budget-Gate (reuse `token_meter`/`llm_usage.json`) | ✅ (Modul 7, 13 Tests) |
| `scheduler/research_tick.py` | expliziter echter P4-Trigger + `no_trade_reason` (der Blocker) | ✅ (Modul 8, 14 Tests) |
| `scheduler/observability.py` | v1.6 Step 0 — per-Zyklus JSONL-Diagnose-Log (`record_cycle`/`iter_records`), Sicherheitsnetz für Rückfälle | ✅ (v1.6, 9 Tests) |
| `scheduler/reconcile.py` | `CLOSED_BY_BROKER`-P&L-Nachzieh-Pass (idempotent) — reuse P5/P7 | ✅ (7 Tests) |
| `scheduler/runner.py` | die Loop / Daemon-Orchestrator + Preflight + Shutdown + `request_stop()` + optionaler `universe_refresher` (Phase 9/V2, Default `None` = bit-identisch) | ✅ (Modul 10, 24 Tests — 18 + 6 v2) |
| `scheduler/run.py` | `python -m scheduler.run` Entry (in-package, lazy `scripts.wiring`, SIGTERM/SIGINT → `request_stop`) | ✅ (Modul 11, 6 Tests) |
| `scripts/wiring.py` | Composition Root `build_scheduler()` — voller P1–P7-Stack (Debatte + Reward in EINEN Executor), 3 Closures + `universe_refresher`-Closure (Phase 9/V2) | ✅ (Modul 11, operator-run) |
| `scripts/run_scheduler.sh` · `smoke_test.py` · `live_test.py` | Operator-Tools (Start-Script · offline Sim-Tag mit Fakes · echter unbeaufsichtigter IG-Demo-Zyklus) | ✅ (Modul 11, operator-run) |
| `webui/api.py` + `webui/static/*` + `scripts/run_webui.sh` | FastAPI read-mostly (DB `mode=ro` + `scheduler_state.json` + Kill/Command-Dateien) + statisches Dark-Neumorphism-Dashboard (GitHub-Dark, Monospace, Polling 7 s, kein Build-Step); Control **nur** Datei-Writes. **+ Token-Meter-Card** (`/api/token_usage`) **+ Last-Cycle-Reasoning** (`/api/last_cycle` zeigt jetzt Research-Pick + Bull/Bear/Judge-Transkript) — s. `## UI-Erweiterung — 2026-06-29`. **v1.7 (2026-07-02): `/api/status`s `trades_today`/`realized_pnl_today` DB-gespeist** (nicht mehr der lagging `scheduler_state.json`-Snapshot) — s. `## Session stopped — 2026-07-02 (v1.7: /api/status DB-gespeist)` | ✅ (Modul 12, 20 Tests) |
| `tests/*` | gemockt, kein Netz/LLM/echter sleep (199, Schwerpunkt `test_runner` + `test_safety` + `test_webui`) | ✅ |

Repo-Konventionen: `from __future__ import annotations`, Type-Hints + Docstrings, eine
Datei = eine Verantwortung, eigene typisierte Exceptions, nie still schlucken, Logging →
stderr, `pytest` ohne Netz/echtes LLM, atomic commits.

## Step 0 / Step 0b — Housekeeping-Ergebnisse (2026-06-27)
- **Step 0 (Legacy-/Turbo-Cleanup) = dokumentierter No-Op (sauber).** `grep -rniE
  "\b(strike|otm|issuer|turbo_research)\b"` über alle `*.py` = **0 Treffer**; die
  `CALL`/`PUT`-Treffer sind ausschließlich (a) Guard-Kommentare/Tests, die die
  Options-Vokabel **ablehnen** (P4 `validator`/`prompt`, P5 `test_gates`), (b) der
  HTTP-Verb `PUT` im IG-Adapter und (c) der IG-`otc`-Endpoint. Der frozen
  `turbo_candidates.json`-Name bleibt (P2/P5-Gate-2-Contract) — nicht umbenennen. P8
  führt **keine** neue Turbo-Referenz ein.
- **Step 0b (Doku-Reconciliation) erledigt.** Root-`CLAUDE.md` „Current state" →
  **Phase 8 in Umsetzung** (Phase 7 ✅ + gemergt als historischer Block darunter);
  `README.md`-Statustabelle Zeile 7 (P7 ✅) + Zeile 8 (P8 🔄, Mission-Fußnote ⁵);
  `ROADMAP.md` Phase-8-Block auf das Konzept-Modell (Mission + reale Module +
  Done-Kriterium + Concept-Link). **Note (nicht gefixt):** der stale Modell-String in
  `the_council.jsx` (`claude-sonnet-4-20250514`) ist **P9-Scope** und liegt außerhalb des
  Repos.

## Verifizierte Contracts (Step 1 — gegen Live-Code gepinnt, 2026-06-27)
> Gepinnt gegen den Repo-Stand auf `phase7-reward`/`main`. ⚠ = Befund, der vom Konzept-
> Handover abweicht / es unter-spezifiziert und einen Build-Step formt. Diese ⚠-Befunde
> sind der Grund, warum die naive Konzept-Formulierung an diesen Stellen **nicht** 1:1
> baubar ist — vor Step Safety/Loop/Reconcile heranziehen.

**(A) ⚠ `confirm_fn` ist ein KONSTRUKTOR-Argument, NICHT ein `run()`-Argument**
(`phase5_execution/execution/executor.py:69`,:149,:229):
- Echte Signatur: `Executor(broker, db, state, exec_state, config, research_runner,
  confirm_fn, *, debate_runner=None, reward_sink=None, now_fn=datetime.now,
  sleep_fn=time.sleep)`; **`run()` ist arglos** → `run() -> ExecutionResult`.
- Der Konzept-Handover („Verifizierte geerbte Contracts") behauptete `run(confirm_fn=…)`
  und die Loop-Skizze macht `executor.run(confirm_fn=auto_confirm)` — **falsch.** ⇒ Der
  Executor wird in `wiring.py` **einmal** mit `confirm_fn=AutoConfirm` gebaut; die Loop
  ruft jeden Zyklus **bare `run()`**. `AutoConfirm.__call__` muss daher **live** State/
  Caps zur Aufruf-Zeit lesen (hält Referenzen auf `state_store` + `budget`, **kein**
  Snapshot). `config.require_confirm` ist default **True** (P5) → `AutoConfirm` wird
  tatsächlich aufgerufen; das Wiring darf es **nicht** auf `False` setzen.

**(B) ⚠ Gate-2-Freshness re-callt Research bei leerer Liste** (`gates.py:84`,
`phase2_persistence/persistence/state.py:150`):
- `gate_load_candidates`: `if not state.candidates_are_fresh(): research_runner()` → dann
  `load_candidates()`. Aber `candidates_are_fresh()` returnt `bool(data.get("candidates"))`
  → **`False` für `[]`**. ⇒ `save_candidates([])` bei Abstain verhindert den Re-Call
  **nicht** (Gate 2 würde Research **erneut** callen → doppelte LLM-Kosten).
- **Mechanismus (P7-Muster):** in den Executor einen **No-op-`research_runner`**
  (`_no_research` → `[]`) injizieren; das **echte** P4-Research läuft explizit in
  `research_tick` **vor** `run()`. Dann: Pick → frische Datei → `candidates_are_fresh()`
  True → No-op nie gerufen → Executor nutzt den Pick; Abstain → No-op läuft (tut nichts)
  → `load_candidates()` `[]` → `NO_TRADE`, **kein** zweiter Call.

**(C) Seed-Marker ist englisch** (`phase5_execution/scripts/seed_candidate.py:62`):
- `reasoning = "MANUAL SEED (not a real research pick): …"` (nicht die deutsche
  Handover-Vermutung). `test_no_manual_seed_marker` asserted: das `reasoning` eines
  echten (gemockten) P4-Picks enthält **nie** `"MANUAL SEED"`.

**(D) ⚠ `confirm_fn` bekommt einen `OrderPlan` ohne `account`-Feld** (`executor.py:229`,
`execution/models.py` `OrderPlan`):
- Aufruf: `confirm_fn(plan)`; `OrderPlan = {epic, direction, size, stop_level,
  limit_level, deal_reference, currency}`. ⇒ Der Konzept-`order_ctx.account == "demo"`-
  Doppel-Check ist aus dem Plan **nicht** verfügbar. Der Demo-Lock ist **strukturell im
  Wiring**: nur `get_broker("ig_demo")` bauen + `config.account = "demo"`; `AutoConfirm`
  liest `config.account` (nicht den Plan).

**(E) `run()` returnt `ExecutionResult(status, deal_id, plan, detail, close_level,
profit_loss)`** (`execution/models.py`, `executor.py`):
- `status ∈ {OPEN, CLOSED_BY_BROKER, TIME_STOP, NO_TRADE, ABORTED_BY_USER, ABORT}`.
  `record_cycle` keyt auf `status`: ein realer Trade = {OPEN, CLOSED_BY_BROKER,
  TIME_STOP} (inkrementiert `trades_today`); NO_TRADE/ABORTED_BY_USER/ABORT nicht.
- ⚠ `profit_loss` ist bei **TIME_STOP** gesetzt, bei **CLOSED_BY_BROKER** `None` (erst per
  Reconcile aufgelöst). ⇒ `realized_pnl_today` für den Loss-Breaker aus der **DB** lesen
  (heutige `trade_outcomes`/`reward_pts` über `session_date`), nicht nur aus dem
  Cycle-Result — sonst entgeht die broker-geschlossene P&L dem Breaker.

**(F) Reconcile-Reuse — nicht neu bauen:**
- `broker.reconcile_positions(expected_references=…).data = {broker_position_count,
  broker_deal_ids, present, missing, unexpected}`. **`reconcile_startup`
  (`execution/order.py`) läuft bereits in JEDEM `executor.run()`** (`executor.py:158`,
  orphan PENDING). P7 lieferte (Step 13b) **`reward_sink.reconcile_open_trades(deal_ids=
  None)`** — idempotenter `CLOSED_BY_BROKER`-P&L-Nachzieh über `get_trade_history`,
  fail-closed. ⇒ `reconcile.py` ist **Komposition** dieser beiden, **keine**
  Reimplementierung.
- `get_trade_history(days=30).data = {"transactions":[…]}` (`ig_adapter.py:555`): **kein
  `deal_id`**, `size` **vorzeichenbehaftet** (SELL negativ) — der P7-Resolver matcht
  heuristisch (Betrag + Level + Recency); v. a. **intraday erst nach Settlement gebucht**
  → der lag-freie Pfad ist der Close-Confirm (P7 13c). Das ist bereits P7-gelöst; P8 ruft
  nur `reconcile_open_trades` auf.

**(G) Composition Root — EINEN Broker für die warme Session** (`phase7_reward/scripts/
wiring.py:149` als Vorlage; `phase4_research/scripts/wiring.py:50`):
- P7-`build_executor` ist die Vorlage (ein geteilter Broker für Executor + `reward_sink`,
  `research_runner=_no_research`, tz-aware `now_fn`). P4-`build_research()` baut sich
  **einen eigenen** `get_broker("ig_demo")` → würde die warme IG-Session (Decision 1)
  brechen. ⇒ P8-`wiring.py` konstruiert `Research` **direkt aus dem `research`-Paket**
  (geteilter Broker/db/state), genau wie P7 den `Executor` direkt aus `execution` baut
  (umgeht zugleich die `scripts.wiring`-Namenskollision P4/P5/P6/P7/P8). `Research.run()
  -> list[Candidate]` (`research/research.py`).

**Bestätigt as-assumed (kein ⚠):**
- Momentum-VETO sourcet aus `broker.get_ohlcv` (IG-Echtzeit), **nie** P3-`get_momentum()`
  (`execution/vetos.py` / P5-CLAUDE) — kein Fix nötig.
- `token_meter.record(usage, model, config, path)` (`research/token_meter.py:120`) hängt
  8-Feld-Records (`ts`, `input_tokens`, `output_tokens`, `est_cost_eur`, …) an
  `data/state/llm_usage.json`. **Kein Reader** → `budget.py` summiert die heutigen
  Records selbst (Filter `ts`-Datum in Europe/Berlin).
- `external_data.market_hours.is_market_open(now=None) -> bool`
  (`external_data/market_hours.py:24`): Mo–Fr 09:00–17:30 Europe/Berlin, DST-aware, **kein
  Feiertagskalender** (Feiertage fallen in Broker-/VETO-fail-closed). ⟳ **2026-06-28
  (Modul 3, Code = Wahrheit):** das frühere „WINDOW nutzt P5 `trading_window_start/end`
  (09:30–11:19)" war stale — die echte P5-`ExecutionConfig` ist `09:00`/`17:30`
  (`execution/config.py:99-100`), bereits in Modul 1 übernommen. `clock.classify` nutzt
  daher `SchedulerConfig.window_open/close` (test-überschreibbar); `is_market_open` wird
  nur als **laufzeit-Markt-offen-Prädikat** via `Clock.market_is_open` reused (lazy Import,
  damit der heiße Klassifikations-Pfad stdlib-only bleibt).
- `broker_wrapper.credentials.get_credential(name)` (`credentials.py:56`,
  `SERVICE_NAME="tradingbot"`, wirft `CredentialNotFoundError`) für den Keyring-Preflight.

---

## Session stopped — 2026-07-04 (Phase 9 / V2 Step 5 — `universe_refresher`-Naht, additiv)

> **Auslöser:** Phase 9 (V2)-Kickoff-Session, Step 5 des Ausführungsplans
> (`docs/concepts/phase9_v2_foundation_plan(1).md`) — die P8-Integrationshälfte der
> DB-Universum-Anbindung. Phase 8 selbst bleibt sonst unverändert.

### Completed (additiv, Default-Pfad bit-identisch)
- **`scheduler/config.py`:** neues `universe_refresh_interval_min: int = 240`.
- **`scheduler/state.py`:** neues Cross-Day-Feld `last_universe_refresh_ts: str | None =
  None` (wie `last_reconcile_ts` — von `rollover_if_new_day` unberührt, self-healing via
  den bestehenden Feld-Filter).
- **`scheduler/runner.py`:** `SchedulerRunner.__init__` bekam einen optionalen
  keyword-only `universe_refresher: Callable[[], Any] | None = None` (Default `None` =
  heutiges Verhalten, bit-identisch). Aufgerufen (a) einmalig in `preflight()`
  (fail-soft, guarded — ein Refresh-Fehler stoppt den Daemon-Start nicht), (b) danach
  höchstens 1× je `universe_refresh_interval_min` in der WINDOW-Phase (throttled via
  neuem generischem `_due_after()`, aus dem bestehenden `_due()` extrahiert — **niemals**
  innerhalb von `research_tick.ensure_candidates`, ein Discover/Promote-Pass ist
  unabhängig von einem Gate-2-Pick). **+6 neue Tests** in `test_runner.py`
  (None→nie gerufen, Preflight-Call, Never-run→sofort due, Throttle innerhalb des
  Intervalls, Re-Run nach Intervall-Ablauf, Fail-soft bei Exception — kein Crash, kein
  Backoff-Trip). **P8 199 → 205.**
- **`scripts/wiring.py`:** neue `_build_universe_from_db()` (dupliziert — nicht
  importiert — aus P4s `scripts.wiring.build_universe_from_db`, gleicher Grund wie
  `_build_research` direkt aus dem `research`-Paket baut statt P4s Factory zu
  importieren: die `scripts.wiring`-Namenskollision über die Phasen). `_build_research`
  nutzt sie jetzt statt hartkodiertem `EXTENDED_UNIVERSE`. Neue `universe_refresher`-
  Closure in `build_scheduler()` (Discover + `run_promotion_cycle` über den geteilten
  Broker + `research.market_data`, `is_demo=(config.account=="demo")`), an
  `SchedulerRunner(...)` durchgereicht.
- **Manuell end-to-end verifiziert** (kein pytest, `scripts/wiring.py` wird laut
  Konvention nicht von pytest importiert): eine echte Migration-004-DB mit 1 geseedeten
  DAX-Record → `build_universe_from_db` liefert `[DAX]`; leere/fehlende DB → Fallback
  auf `EXTENDED_UNIVERSE` (4 Instrumente), kein Crash, korrekt geloggte Warnung.

### Verifiziert
- `pytest phase8_scheduler/tests -q` → **205 passed** (199 + 6). Volle Regression
  unverändert grün: P1 52 · P2 76 · P3 73 · P4 141 (+6, s. `phase4_research/CLAUDE.md`) ·
  P5 154 · P6 70 · P7 133 · root 64 · P9 67.
- `py_compile` clean auf allen berührten Dateien.

### Next
- Phase 9 (V2) Steps 6–7 (BarProvider-Kette + Lightstreamer, V2b) sind noch offen —
  siehe `phase9_universe/CLAUDE.md` für den aktuellen Stand des Universe-Pakets selbst.
- Operator-Live-Runs (Step 8: Autonomie-Beweis + Breaker-Fire) folgen erst nach V2b.

### Offene Punkte / blockers
- Keine technischen.

---


> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
