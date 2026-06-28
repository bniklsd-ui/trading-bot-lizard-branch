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
Safety.

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
| `scheduler/safety.py` | `AutoConfirm` `confirm_fn`: demo + kill + caps + loss-breaker + budget | ✅ (Modul 6, 18 Tests) |
| `scheduler/backoff.py` | konsekutive-Fehler-Tracking + Backoff-Schedule | ⬜ |
| `scheduler/budget.py` | Token-Budget-Gate (reuse `token_meter`/`llm_usage.json`) | ✅ (Modul 7, 13 Tests) |
| `scheduler/research_tick.py` | expliziter echter P4-Trigger + `no_trade_reason` (der Blocker) | ⬜ |
| `scheduler/reconcile.py` | `CLOSED_BY_BROKER`-P&L-Nachzieh-Pass (idempotent) — reuse P5/P7 | ⬜ |
| `scheduler/runner.py` | die Loop / Daemon-Orchestrator + Preflight + Shutdown | ⬜ |
| `webui/api.py` + `webui/static/*` | FastAPI read-mostly + statisches Dashboard | ⬜ (zuletzt) |
| `scripts/wiring.py` · `run.py` · `run_scheduler.sh` · `smoke_test.py` · `live_test.py` | Composition + Operator-Tools | ⬜ |
| `tests/*` | gemockt, kein Netz/LLM/echter sleep (≥50, Schwerpunkt `test_runner` + `test_safety`) | ⬜ |

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

## Session stopped — 2026-06-28 (Modul 7: `scheduler/budget.py` — das Token-Budget-Gate)

### Completed
- **`scheduler/budget.py`** — `TokenBudget`, das deterministische Tages-Token-Budget (Decision 12,
  **kein AI**). Erfüllt das in Modul 6 definierte `safety.Budget`-Protocol (**löst den Stub ein**).
  Reuse des geteilten 8-Feld-Meters (`data/state/llm_usage.json`, von `research.token_meter`
  geschrieben über P4/P6/P7) — **kein** zweites Mess-System; es gibt **keinen** importierbaren Reader
  (nur das Script `usage_report.py`), also liest `budget.py` das JSON-Array selbst (fail-soft).
  - `consumed_today() -> int` — summiert alle vier billed Token-Felder (`input`+`output`+
    `cache_creation`+`cache_read`, tolerant gegen fehlende Keys) über die Records, deren UTC-`ts`
    auf **heute in `config.tz`** fällt (alle Modelle; system-weites Tagesbudget).
  - `is_exhausted() -> bool` — `daily_token_budget None` → False (+ 1 WARNING beim Konstruieren);
    sonst `consumed_today() >= budget` (Grenze inklusive). **Wirft nie** (Auto-Confirm vertraut dem Bool).
- **`scheduler/__init__.py`** exportiert jetzt zusätzlich `TokenBudget`.
- **`tests/test_budget.py`** — **13 Tests**: unter/über/exakt am Budget; cache-Felder gezählt;
  6-Feld-Record (ohne `cache_*`) toleriert; nur heutige Records; **Berlin-Grenze** (`22:30Z` zählt
  zum nächsten Berlin-Tag, CEST +2); fehlende/korrupte Log → 0 (fail-open, kein Raise); Bad-`ts`
  geskippt; `None` → 1 `scheduler.budget`-WARNING + nie erschöpft; **Protocol-Handoff** (echtes
  `TokenBudget` als `AutoConfirm.budget` → `REASON_BUDGET`); Export-Identität.

### Vier Konzept↔Code-Reconciliations (Code = Source of Truth)
- **(1) Konstruktor `TokenBudget(config, usage_log_path, *, now_fn=None)`** statt `(config,
  token_meter)` — das P4-`token_meter` hat **kein** Read-API; `budget.py` liest die JSON direkt. Der
  Pfad kommt explizit (wie `safety.py` `kill_path` nimmt) + `now_fn` für die Tagesgrenze. **Kein
  Edit an `config.py`/Modul 1.**
- **(2) Berlin-Tagesgrenze aus UTC-`ts`** — der Meter schreibt UTC (`Z`-Suffix), der Tag ist
  `config.tz` → `ts` wird **vor** `.date()` nach `config.tz` konvertiert. Stdlib-only (`fromisoformat`
  + `Z`→`+00:00` + `zoneinfo`), **kein** `research.timeutil`-Import (Isolation: `import
  scheduler.budget` zieht **NONE** cross-phase).
- **(3) Token-Maß = alle vier billed Felder** (tolerant gegen fehlende `cache_*`) → undercountet
  nie. v1, tunbar.
- **(4) Advisory-Budget fail-OPEN** (Log-Read-Fehler → consumed 0 → nicht erschöpft) — bewusst
  **anders** als `safety.py`s fail-CLOSED Loss-Breaker (Kosten-Kappe, kein Geld-Safety-Gate).

### Verifiziert (gemockt / lokal — kein Netz, kein LLM; Live = Operator)
- `pytest phase8_scheduler/tests -v` → **96 passed** (10 config + 6 exceptions + 19 clock + 18
  state + 12 killswitch + 18 safety + 13 budget). `py_compile` clean. **Import-Isolation:** `import
  scheduler.budget` zieht **NONE** broker_wrapper/persistence/external_data/research/execution/
  reward/debate/pandas/numpy/yfinance/anthropic/requests.
- **Regression grün + unberührt** (rein additiv): P2 62 · P5 146 · P7 128 (separat gelaufen). P1 52 ·
  P4 94 · P6 70 unverändert.

### Next — **Modul 8: `scheduler/research_tick.py`** (Konzept §8 — der eigentliche Blocker: autonome Candidates)
- `ResearchTick(research, state_store).ensure_candidates(state) -> ResearchResult`: triggert
  **ausschließlich** das echte `Research.run()` (P4, via Wiring) → frische `turbo_candidates.json`
  (1 Pick | `[]`), **nie** `seed_candidate.py` (kein `"MANUAL SEED"`-Marker → `test_no_manual_seed_
  marker`). `no_trade_reason` minimal (`EMPTY_UNIVERSE|LLM_ABSTAIN|VALIDATOR_REJECT|FILTER_FAIL|
  PREFLIGHT_FAIL`) → `state.last_no_trade_reason`. **Freshness-Disziplin (Contract B):** bei Abstain
  `save_candidates([])`, aber Gate 2 re-callt bei `[]` → der **No-op-`research_runner`** muss in den
  Executor injiziert werden (Wiring/Modul 11), echtes Research läuft **vorher** hier. `last_research_ts`
  aktualisieren.

### Offene Punkte / [VERIFY]
- `wiring.py`/Modul 11: `TokenBudget(config, _USAGE_LOG, now_fn=tz_now)` (Pfad `data/state/llm_usage.json`
  wie P4/P6/P7-Wiring) an `AutoConfirm` reichen; `realized_pnl_today`-Closure (Query in Modul-6-Block)
  + `daily_loss_cap≈1800` + `daily_token_budget` setzen; **No-op-`research_runner`** + EINEN Broker teilen.
- **Commit:** committet, **falls** der Operator es triggert (Branch `phase8-scheduler`); „Commit ⇒
  Note-Update" gilt im selben Commit.

---

## Session stopped — 2026-06-28 (Modul 6: `scheduler/safety.py` — das Auto-Confirm-Gate)

### Completed
- **`scheduler/safety.py`** — `AutoConfirm`, der deterministische `confirm_fn`-Ersatz für den
  P5-Human-Confirm (das schwerste Safety-Modul, **kein AI**). Fünf harte Gates, **alle** müssen
  halten, sonst `(False, reason)`:
  1. **Demo-Lock (strukturell, config-only — Contract D):** `config.account == "demo"`, sonst
     `False` + `logger.critical`. Liest **nicht** den `OrderPlan` (der trägt kein `account`).
  2. **Kill-Switch aus:** `killswitch.is_set(kill_path)` False (Modul 5, live pro Aufruf gelesen).
  3. **Unter Trade-Cap:** `state.trades_today < config.max_trades_per_day`.
  4. **Über Loss-Breaker:** `daily_loss_cap is not None` UND heutige realized P&L `> -cap` —
     **aus der DB** (Contract E) via injiziertem `realized_pnl_today(session_date)`, **nicht**
     `state.realized_pnl_today` (Snapshot-Falle). DB-Read **fail-CLOSED** (wirft → block).
  5. **Budget nicht erschöpft:** `budget.is_exhausted()` False (duck-typed `Budget`-Protocol).
- **Zwei Aufruf-Flächen, ein gemeinsamer `_evaluate`** (können nie divergieren): `can_open(state)
  -> (bool, reason)` (Pre-Cycle-Gate, spart Tokens) + `__call__(order_plan) -> bool` (Final-Gate;
  lädt State **live** aus dem Store — Contract A, kein Snapshot; ignoriert `order_plan`).
- **`scheduler/__init__.py`** exportiert jetzt zusätzlich `AutoConfirm` + `Budget`.
- **`tests/test_safety.py`** — **18 Tests**: happy-path (can_open + __call__); `account="live"` →
  NOT_DEMO + 1 critical; Demo-Lock schlägt andere Fails; Kill blockt + **live** in `__call__`;
  Cap at-limit/under; Loss unter Cap / **exakt am Cap** / knapp drüber; session_date == `state.date`;
  **P&L-Read-Fehler → fail-closed block** + critical; Loss-Cap None → 1 `scheduler.safety`-WARNING +
  kein Block + Reader nie gerufen; Budget erschöpft; `can_open`/`__call__` konsistent; `__call__`
  ignoriert Plan-Felder; Package-Export-Identität.

### Drei Konzept↔Code-Reconciliations + zwei Design-Entscheidungen (Code = Source of Truth)
- **(1) Konstruktor +5. Arg `realized_pnl_today: Callable[[str], float]`** — die §5-Skizze
  `AutoConfirm(config, state_store, kill_path, budget)` hat keine DB-P&L-Quelle, Contract E
  verlangt sie. Injizierte Closure (Wiring backt sie DB-seitig) hält `safety` phasen-isoliert
  (`import scheduler.safety` zieht **NONE** cross-phase). **Query-Form (für Wiring/Modul 11):**
  `SELECT COALESCE(SUM(profit_loss),0.0) FROM trade_outcomes WHERE session_date=? AND profit_loss
  IS NOT NULL` (OPEN/CANCELLED sind NULL → fallen raus); Argument = `state.date`.
- **(2) §5-`order_ctx.account=="demo"`-Doppel-Check entfällt** (Contract D: kein `account` im
  `OrderPlan`) → Demo-Lock config-only; strukturelle zweite Hälfte (nur `ig_demo`-Broker) = Wiring.
- **(3) `budget` = duck-typed `Budget`-Protocol** (Operator-Sondernotiz: „stub via Protocol" statt
  Modul 7 vorziehen). Modul-7-`TokenBudget` wird es erfüllen.
- **Design A:** Loss-Breaker-DB-Read **fail-CLOSED** (wirft → block + critical; im Zweifel nicht traden).
- **Design B:** eigene `scheduler.safety`-WARNING bei `daily_loss_cap=None` beim Konstruieren
  (zusätzlich zur `config`-WARNING — `config` warnt vorm Wert, `safety` warnt, dass **sein** Gate
  aus ist; eine WARNING pro Verantwortung).

### Verifiziert (gemockt / lokal — kein Netz, kein LLM; Live = Operator)
- `pytest phase8_scheduler/tests -v` → **83 passed** (10 config + 6 exceptions + 19 clock + 18
  state + 12 killswitch + 18 safety). `py_compile` clean. **Import-Isolation:** `import
  scheduler.safety` zieht **NONE** broker_wrapper/persistence/external_data/research/execution/
  reward/debate/pandas/numpy/yfinance/anthropic/requests.
- **Regression grün + unberührt** (rein additiv in `phase8_scheduler/`): P2 62 · P5 146 · P7 128
  (cross-referenzierte Phasen separat gelaufen — `tests.conftest`-Namenskollision). P1 52 · P4 94 ·
  P6 70 unverändert (kein berührter Import).

### Next — **Modul 7: `scheduler/budget.py`** (Konzept §7, TDD ≥3) — löst den `Budget`-Protocol-Stub ein
- `TokenBudget(config, token_meter)` mit `consumed_today() -> int` + `is_exhausted() -> bool` (muss
  das in `safety.py` definierte `Budget`-Protocol erfüllen). **Kein Reader** in `token_meter`
  (Contract bestätigt) → die heutigen 8-Feld-Records aus `data/state/llm_usage.json` selbst
  summieren, `ts`-Datum-Filter **Europe/Berlin** (konsistent mit `state`-Rollover).
  `daily_token_budget=None` → nie erschöpft + **eine** WARNING (gehört `budget.py`, nicht `config`).
  Tests: unter Budget → False; über → True; None → False + WARNING.
- **Danach Modul 8 `research_tick.py`** (der eigentliche Blocker: autonome Candidates) + Modul 9
  `reconcile.py` + Modul 11 `runner.py`. Beim Wiring: die `realized_pnl_today`-Closure mit der
  obigen Query an `AutoConfirm` reichen; `daily_loss_cap≈1800` setzen.

### Offene Punkte / [VERIFY]
- `wiring.py`/Modul 11: `realized_pnl_today`-Closure (Query oben) + `daily_loss_cap` setzen; EINEN
  Broker teilen (Contract G); `Research` direkt aus `research` bauen.
- **Commit:** dieser Step ist committet, **falls** der Operator es triggert (Branch
  `phase8-scheduler`); „Commit ⇒ Note-Update" gilt im selben Commit (Status-Tabelle ✅ + dieser Block).

---

## Session stopped — 2026-06-28 (Modul 5: `scheduler/killswitch.py`)

### Completed
- **`scheduler/killswitch.py`** — der Datei-Kill-Switch (`data/state/KILL`, Decision 8),
  **stateless Modul-Funktionen** (Konzept §4-Signaturen), **fail-soft / wirft nie**:
  - `is_set(kill_path)` = reine Existenzprüfung (robust gegen **jeden** Inhalt — auch ein
    leeres `touch` oder eine halb-geschriebene Datei lesen als „halted"; fail-safe Richtung).
  - `set_kill(kill_path, reason)` = mkdir parent + **atomic** (`.tmp`+`os.replace`) JSON
    `{"reason", "ts"(UTC ISO)}`. Konvention: Backoff-Trip `"auto:backoff"`, UI/Operator
    `"manual:<text>"`. Der laute Trip-Log bleibt im **Runner** (Loop loggt `critical`) →
    killswitch ist im Happy-Path still (single responsibility, wie `state.py`).
  - `clear_kill(kill_path)` = `unlink(missing_ok=True)` (fehlende Datei → no-op).
  - `read_reason(kill_path)` = tolerant: missing/empty/unparseable → `None`; JSON-Objekt →
    `"reason"`; Plain-Text → stripped raw (Operator-Hand-Reason); unlesbare existierende
    Datei → **eine** WARNING + `None`.
- **`scheduler/__init__.py`** exportiert jetzt zusätzlich das **Modul** `killswitch`
  (`from . import killswitch`; Consumer rufen `killswitch.is_set(...)`, wie die §10-Loop-Skizze).
- **`tests/test_killswitch.py`** — **12 Tests**: is_set False→True; auto-/manual-Reason
  roundtrip; parent-dir auto + kein `.tmp`-Rest; clear disengaged; clear-missing no-op;
  read missing→None; leeres `touch` = is_set True + reason None; Plain-Text→raw;
  overwrite (latest wins); unlesbar→1 WARNING+None (monkeypatched `read_text`); Modul-Export-Identität.

### Design-Notizen (Code = Source of Truth — dated §4-Annotation im Konzept)
- **Inhalt = JSON `{reason, ts}`** (Konzept sagt nur „Reason+Timestamp") — konsistent mit
  `scheduler_state.json`, sauberer roundtrip. **`is_set` = nur Existenz** (operator-touchbar).
  **`read_reason` fail-soft** (empty/plain-text/unparseable toleriert). **atomic + parent-dir**
  (Paket-Pattern). **Als Modul-Namespace exportiert**, nicht als bare Funktionen am Paket-Root.

### Verifiziert (gemockt / lokal — kein Netz, kein LLM; Live = Operator)
- `pytest phase8_scheduler/tests -v` → **65 passed** (10 config + 6 exceptions + 19 clock +
  18 state + 12 killswitch). `py_compile` clean. **Import-Isolation:** `import
  scheduler.killswitch` zieht **NONE** cross-phase/heavy (pure stdlib: json/os/datetime/
  pathlib/logging).
- **Regression grün + unberührt** (rein additiv in `phase8_scheduler/`): P1 52 · P2 62 ·
  P4 94 · P5 146 · P6 70 · P7 128 (separat gelaufen — `tests.conftest`-Namenskollision).

### Next — **Modul 6: `scheduler/safety.py`** (Konzept §5, das Auto-Confirm-Gate — schwerstes Safety-Modul, TDD ≥8 Tests)
- `AutoConfirm(config, state_store, kill_path, budget)` als `confirm_fn`-Ersatz für den
  P5-Human-Confirm. `__call__(order_ctx) -> bool` (Final-Gate vor `place_order`) **und**
  `can_open(state) -> (bool, reason)` (Pre-Cycle-Gate, spart LLM-Tokens). `True` **nur** wenn
  **alle** harten Bedingungen: (1) `config.account == "demo"` (Demo-Lock strukturell aus der
  **Config**, **nicht** aus dem `OrderPlan` — Contract D; alles ≠ demo → `False` +
  `logger.critical`); (2) `killswitch.is_set` False; (3) `state.trades_today <
  max_trades_per_day`; (4) Tages-Loss-Breaker: `daily_loss_cap is not None` und
  heutige realized P&L `> -daily_loss_cap` — **aus der DB** (Contract E), **nicht** aus
  `state.realized_pnl_today` (Snapshot-Falle, s. Modul-4-Reconciliation); `None` → eine
  WARNING, kein Block; (5) `budget.is_exhausted()` False. ⚠ **Vor Bau Contracts A/D/E
  heranziehen** + `budget.py`-API (Modul 7, evtl. vorzuziehen oder per Protocol stubben).

### Offene Punkte / [VERIFY]
- `safety.py`: `realized_pnl_today` aus der **DB** lesen (Contract E) — die DB-Query-Form
  beim Wiring/Modul 6 klären (heutige `trade_outcomes`/`reward_pts` über `session_date`).
  `budget` ist eine Dependency → entweder Modul 7 `budget.py` vorziehen oder via Protocol stubben.
- **Commit:** dieser Step ist committet (Operator-getriggert, Branch `phase8-scheduler`);
  „Commit ⇒ Note-Update" im selben Commit.

---

## Session stopped — 2026-06-28 (Modul 4: `scheduler/state.py`)

### Completed
- **`scheduler/state.py`** — `SchedulerState` (mutable `@dataclass`, concept §3:
  date/trades_today/realized_pnl_today/last_research_ts/last_reconcile_ts/
  consecutive_failures/kill_reason/last_no_trade_reason) + `StateStore`:
  - `load()` **self-heals, never raises** — missing file → fresh `SchedulerState()`;
    corrupt/partial JSON → **eine** WARNING + fresh state; unbekannte Keys gedroppt,
    fehlende defaulted (forward/backward-compat via `dataclasses.fields`-Filter).
  - `save()` **atomic** (`.tmp` + `os.replace`) — die P2 `_atomic_write`-Pattern **lokal
    kopiert** (nicht importiert; `import scheduler.state` zieht **NONE** cross-phase/heavy).
  - `rollover_if_new_day(state, now)` — neues Europe/Berlin-Datum ⇒ reset
    trades/pnl/failures + `kill_reason`/`last_no_trade_reason`=None, `date`=today;
    **behält** `last_research_ts`/`last_reconcile_ts` (last-action ts, keine Day-Counter).
    Idempotent (same-day = no-op). `now` muss tz-aware in der Daemon-Zone sein (Clock liefert das).
  - `record_cycle(state, result)` — duck-typed (kein `execution`-Import); `trades_today += 1`
    nur bei `TRADE_STATUSES = {OPEN, CLOSED_BY_BROKER, TIME_STOP}` (**Contract E**);
    `profit_loss` best-effort akkumuliert wenn present. Berührt **nicht**
    `consecutive_failures` (backoff), `last_no_trade_reason` (Loop/research_tick) oder die ts.
- **`scheduler/__init__.py`** exportiert jetzt zusätzlich `SchedulerState` + `StateStore`.
- **`tests/test_state.py`** — **18 Tests**: roundtrip; load missing/corrupt(1 WARNING)/
  tolerant(unknown+missing keys); atomic save (parent auto-created, kein `.tmp`-Rest);
  rollover new-day/same-day/idempotent/fresh-init; `record_cycle` × {OPEN,CLOSED_BY_BROKER,
  TIME_STOP} zählt / × {NO_TRADE,ABORTED_BY_USER,ABORT} zählt nicht; pnl present vs None;
  failures/reason unberührt; Package-Export-Identität.

### Eine Konzept↔Code-Reconciliation (Code = Source of Truth — dated §3-Annotation im Konzept)
- **`realized_pnl_today` = best-effort persisted Snapshot, NICHT die Loss-Breaker-Quelle.**
  `record_cycle` faltet P&L nur wenn das Cycle-Result sie trägt (zur Cycle-Zeit = der
  TIME_STOP-Pfad; **Contract E**: `CLOSED_BY_BROKER` liefert `profit_loss=None`, erst per
  Reconcile/Modul 9 aufgelöst) → das Feld kann für broker-closes der DB hinterherhängen.
  Der **autoritative** Tages-Loss-Breaker (`safety.py`/Modul 5) liest die heutige realized
  P&L aus der **DB** (Contract E) und hängt **nicht** an diesem Feld. Hält Modul 4
  self-contained + vermeidet eine Doppelzähl-Falle (jetzt geflaggt, damit kein späteres
  Modul den Breaker fälschlich an diesen Snapshot hängt).

### Verifiziert (gemockt / lokal — kein Netz, kein LLM; Live = Operator)
- `pytest phase8_scheduler/tests -v` → **53 passed** (10 config + 6 exceptions + 19 clock
  + 18 state). `py_compile` clean. **Import-Isolation:** `import scheduler.state` zieht
  **NONE** von broker_wrapper/persistence/external_data/research/execution/reward/debate/
  pandas/numpy/yfinance/anthropic/requests.
- **Regression grün + unberührt** (rein additiv in `phase8_scheduler/`): P1 52 · P2 62 ·
  P4 94 · P5 146 · P6 70 · P7 128 (separat gelaufen — `tests.conftest`-Namenskollision).

### Next — **Modul 5: `scheduler/killswitch.py`** (Konzept §4, klein, TDD)
- Modul-Funktionen `is_set(kill_path)`, `set_kill(kill_path, reason)`, `clear_kill(kill_path)`,
  `read_reason(kill_path)`. Datei-Existenz = Wahrheit; Reason+Timestamp im Inhalt
  (`auto:backoff` vom Backoff-Trip, `manual:<text>` von UI/Operator). Geteilt von `safety`
  (Leser) + `webui` (Schreiber) → eigenes Mini-Modul (one file = one responsibility).
  Tests ≥4: set→is_set True; clear→False; reason roundtrip; fehlende Datei → kein Crash.
  Stdlib-only, fail-soft (fehlende/korrupte Datei → kein Raise, wie `state.load`).

### Offene Punkte / [VERIFY] (für spätere Module, jetzt nur dokumentiert)
- `safety.py`: `daily_loss_cap`-Produktionswert (≈€1800) + `realized_pnl_today` aus der **DB**
  (Contract E, s. Reconciliation oben) — beim Wiring setzen, **nicht** an den State-Snapshot hängen.
- **Commit:** dieser Step ist committet, **falls** der Operator es triggert (Branch
  `phase8-scheduler`); „Commit ⇒ Note-Update" gilt im selben Commit.

---

## Session stopped — 2026-06-28 (Modul 3: `scheduler/clock.py`)

### Completed
- **`scheduler/clock.py`** — `Phase`-Enum (`PRE_OPEN | WINDOW | POST_WINDOW | IDLE`) +
  `Clock(config, *, now_fn, sleep_fn)`: `now()` (tz-aware in `config.tz`), `classify(now)`,
  `seconds_until(target, now)`, `sleep(s)` (delegiert an `sleep_fn`), `market_is_open(now)`.
  Erstes echtes Logik-Modul. `_parse_hhmm` **lokal gespiegelt** von P5 `gates._parse_hhmm`
  (nicht importiert — Phasen-Isolation für einen Einzeiler).
- **`scheduler/__init__.py`** exportiert jetzt zusätzlich `Clock` + `Phase`.
- **`tests/test_clock.py`** — **19 Tests**: alle 4 Phasen + Weekend; inklusive Fenster-
  Grenzen (09:00/17:30 → WINDOW); `seconds_until` same-day/across-midnight/across-weekend,
  strikt-nächster bei Boundary==now, `PRE_OPEN`-Target, `IDLE`→`ValueError`; `now`/`sleep`-
  Delegation; `market_is_open`-Delegation an P3; **config-getriebenes Fenster** (Override
  reklassifiziert); Package-Export.

### Zwei Design-Entscheidungen (Code = Source of Truth — dated §2-Annotation im Konzept)
- **★ DST-Falle gefixt:** `(a - b)` zweier datetimes mit **demselben** `ZoneInfo`-Objekt
  rechnet **naiv wall-clock** (eine Spanne über die Frühjahrs-Umstellung liefert 63h statt
  real 62h). `seconds_until` konvertiert daher **beide Seiten nach UTC** vor der Subtraktion
  → DST-korrekt (Tests pinnen 62h Spring-Forward / 64h Fall-Back, **nicht** 63h). Das ist
  exakt das vom Konzept geforderte „keine naiven `timedelta`-Stunden-Hacks".
- **Konzept↔Code-Reconciliation (market_hours-Reuse, Decision 2):** `is_market_open`
  vermengt Weekday **und** 09:00–17:30 → es kann `classify` nicht allein „heute Handelstag?"
  um 08:00 beantworten, und das Scheduler-WINDOW ist **config-getrieben** (test-überschreibbar),
  nicht an P3s festes Fenster gekoppelt. Aufteilung: `classify` = Weekday-Check + config-Fenster
  (`_parse_hhmm`); P3s Prädikat wird **lazy** via `Clock.market_is_open` reused (Laufzeit-Guard
  im Runner). So bleibt der heiße Pfad stdlib-only (Import-Isolation bewiesen: `import
  scheduler.clock` zieht **kein** pandas/external_data — erst der `market_is_open`-Aufruf).
  v1 **kein Feiertagskalender** (Weekday-Proxy, gleiche P3-Vereinfachung; Feiertage →
  Broker-/VETO-fail-closed downstream).

### Verifiziert (gemockt / lokal — kein Netz, kein LLM; Live = Operator)
- `pytest phase8_scheduler/tests -v` → **35 passed** (10 config + 6 exceptions + 19 clock).
  `py_compile` clean. **Import-Isolation:** `import scheduler.clock` zieht **NONE** von
  pandas/numpy/external_data/yfinance/broker_wrapper/execution/research/reward.
- **Regression grün + unberührt** (additiv in `phase8_scheduler/`; nur ein read-only lazy
  Import von `external_data.market_hours`): P1 52 · P2 62 · P4 94 · P5 146 · P6 70 · P7 128
  (separat gelaufen — `tests.conftest`-Namenskollision; jede Phase einzeln).

### Next — **Modul 4: `scheduler/state.py`** (Konzept §3, TDD)
- `SchedulerState`-Dataclass (date/trades_today/realized_pnl_today/last_research_ts/
  last_reconcile_ts/consecutive_failures/kill_reason/last_no_trade_reason) + `StateStore`
  (`load`/`save` **atomic** tmp+`os.replace` wie P2 `state.py`; `rollover_if_new_day` resettet
  Counter/Loss/Failures bei neuem Europe/Berlin-Datum, idempotent; `record_cycle` inkrementiert
  `trades_today` **nur** bei echtem Trade-Status {OPEN, CLOSED_BY_BROKER, TIME_STOP} — Contract E).
  Tests ≥5 (roundtrip, Rollover resettet/selber-Tag-nicht, atomic überlebt Teil-Write,
  record_cycle nur bei Trade). Kein Netz/LLM. **Clock liefert `now` für den Rollover.**

### Offene Punkte / [VERIFY] (für spätere Module, jetzt nur dokumentiert)
- `safety.py`: `daily_loss_cap`-Produktionswert (≈€1800) + `realized_pnl_today` aus der DB
  (Contract E) — beim Wiring setzen.
- **Commit:** dieser Step ist committet, **falls** der Operator es triggert (Branch
  `phase8-scheduler`); „Commit ⇒ Note-Update" gilt im selben Commit.

---

## Session stopped — 2026-06-28 (Modul 2: `scheduler/exceptions.py`)

### Completed
- **`scheduler/exceptions.py`** — `SchedulerError` (Basis, `code="SCHEDULER_ERROR"`) →
  `PreflightError` (`code="PREFLIGHT_ERROR"`). `code`-Class-Attr-Muster **verbatim wie P5**
  (`execution/exceptions.py`), stdlib-only, **importiert nichts cross-phase**.
- **`scheduler/__init__.py`** exportiert jetzt zusätzlich `SchedulerError` + `PreflightError`.
- **`tests/test_exceptions.py`** — **6 Tests**: Basis ist `Exception` + Code; `PreflightError`
  erbt + überschreibt Code; distinkte Codes; Family-Catch (`except SchedulerError`);
  Message-Roundtrip + `code` am Instance; Package-Export-Identität.

### Bewusste Scope-Entscheidung (minimal + ehrlich — dated §-Annotation im Konzept)
- Das Konzept-`exceptions.py # SchedulerError, PreflightError, ...` lässt das „…" — **bleibt
  leer.** Die **einzige** custom Raise-Stelle ist `runner.preflight()` (`PreflightError`,
  fail-closed Keyring/Broker/DB — der Deployment-Top-Risk Q3). Alle anderen Module returnen
  Werte oder fehlschlagen fail-closed **ohne** Re-raise (`safety`→`(bool, reason)`, `budget`→
  `bool`, `reconcile`/`research_tick`→`logger.critical`, `killswitch`/`state` self-heal). Keine
  spekulativen `StateError`/`BudgetError` → die Datei **wächst pro Modul** bei echtem Bedarf.

### Verifiziert (gemockt / lokal — kein Netz, kein LLM; Live = Operator)
- `pytest phase8_scheduler/tests -v` → **16 passed** (10 config + 6 exceptions). `py_compile`
  clean. **Import-Isolation:** `import scheduler.exceptions` zieht **kein** cross-phase/heavy
  Modul (NONE).
- **Regression grün + unberührt** (additiv in `phase8_scheduler/`): **P5 146 · P7 128** (separat
  gelaufen — `tests.conftest`-Namenskollision; jede Phase einzeln). P1 52 · P2 62 · P4 94 · P6 70
  unverändert.

### Next — **Modul 3: `scheduler/clock.py`** (erstes echtes Logik-Modul, TDD)
- `Clock(config, *, now_fn, sleep_fn)` mit `now() -> datetime` (tz-aware Europe/Berlin),
  `classify(now) -> Phase` (PRE_OPEN | WINDOW | POST_WINDOW | IDLE), `seconds_until(target, now)`,
  `sleep(s)` (delegiert an `sleep_fn`, Tests no-op). **Reuse `external_data.market_hours.
  is_market_open`** für „Handelstag/Markt offen" (Mo–Fr, DST-aware); die WINDOW-Phase nutzt
  `config.window_open`/`window_close` (**09:00–17:30 bereits bestätigt**, s. Modul-1-Block) via
  einem `_parse_hhmm`-Idiom (spiegelt P5 `gates._parse_hhmm`). DST: tz-aware Arithmetik, **keine**
  naiven `timedelta`-Stunden-Hacks. Tests ≥6 mit Fake-`now_fn` (Wochenende→IDLE, vor/in/nach
  Fenster, `seconds_until(WINDOW)` über Mitternacht, DST-Tag plausibel).

### Offene Punkte / [VERIFY] (für spätere Module, jetzt nur dokumentiert)
- `safety.py`: `daily_loss_cap`-Produktionswert (≈€1800) + `realized_pnl_today` aus der DB
  (Contract E) — beim Wiring setzen.
- **Commit:** dieser Step ist committet, **falls** der Operator es triggert (Branch
  `phase8-scheduler`); „Commit ⇒ Note-Update" gilt im selben Commit.

---

## Session stopped — 2026-06-28 (Modul 1: `scheduler/config.py`)

### Completed
- **`scheduler/config.py`** — frozen `SchedulerConfig` (Konzept §1), alle Tunables an einem
  Ort, **stdlib-only, importiert nichts cross-phase** (spiegelt P5 `execution/config.py`).
  `__post_init__` emittiert **eine** laute `logger.warning`, wenn `daily_loss_cap is None`
  (Breaker inaktiv — bewusste „setz es bewusst"-Markierung; read-only, kein Raise, frozen-safe).
- **`scheduler/__init__.py`** exportiert jetzt `SchedulerConfig` (+ `__all__`; Exports wachsen
  pro Modul).
- **`tests/test_config.py`** — **10 Tests** (Stil wie P5 `test_config`/P7 `test_models`): Defaults,
  frozen, `account="live"` baubar (Demo-Lock ist `safety.py`, nicht hier), `daily_loss_cap=None`
  → genau **eine** WARNING (caplog), gesetzter Cap → keine WARNING, `daily_token_budget=None`
  ohne Config-WARNING (gehört `budget.py`), Full-Override-Roundtrip, Package-Export-Identität,
  **+ die zwei Reconciliations gepinnt** (Fenster `09:00`/`17:30`, **nicht** `09:30`/`11:19`;
  `HH:MM`-Strings, nicht `time`).

### Zwei Konzept↔Code-Reconciliations (Code = Source of Truth, dated §1-Annotation im Konzept)
- **Handelsfenster = volles Marktfenster `09:00`–`17:30`** (Operator-Entscheidung 2026-06-28),
  **nicht** das Konzept-`09:30`–`11:19`. Das „aus P5-Config" war faktisch falsch — die echte,
  live-verifizierte P5-`ExecutionConfig` ist `09:00`/`17:30`, ebenso `market_hours.is_market_open`.
  Volles Fenster = mehr Trade-Versuche = mehr reale Demo-Daten (die Mission).
- **Fenster als `HH:MM`-Strings**, nicht `datetime.time` — gemäß Build-Note „reuse P5-Strings"
  + Source-of-Truth-Sibling P5. `clock.py` (Modul 2) reused dasselbe Parse-Idiom.

### Verifiziert (gemockt / lokal — kein Netz, kein LLM; Live = Operator)
- **`scheduler` editable-installiert** (`pip install -e phase8_scheduler` im Projekt-venv
  `phase1_broker_wrapper/.venv`) → `import scheduler` / `from scheduler import SchedulerConfig` OK.
- `pytest phase8_scheduler/tests -v` → **10 passed**. `py_compile` clean. **Import-Isolation
  bewiesen:** `import scheduler.config` zieht **kein** `broker_wrapper`/`persistence`/
  `external_data`/`research`/`execution`/`reward`/`debate`/`anthropic`/`requests` (NONE).
- **Regression grün + unberührt** (rein additiv in `phase8_scheduler/`): **P2 62 · P5 146 ·
  P7 128** (separat gelaufen — die Phasen teilen den `tests.conftest`-Modulnamen, daher **nicht**
  gemeinsam in einem `pytest`-Lauf collectbar; jede Phase einzeln). P1 52 · P4 94 · P6 70
  unverändert (kein berührter Import).

### Next — **Modul 2: `scheduler/exceptions.py`** (typisierte Hierarchie, TDD)
- `SchedulerError` (Basis, `code`-Class-Attr-Muster wie P5/P6/P7) → `PreflightError` (Keyring/
  Broker/DB-Preflight, `runner.preflight`), ggf. weitere (`SchedulerStateError`?). Klein; **danach
  Modul 3 `clock.py`** (das erste echte Logik-Modul: `now_fn`/`sleep_fn` injizierbar, Phasen-
  Klassifikation reuse `market_hours.is_market_open` + `config.window_open/close` via einem
  `_parse_hhmm`-Idiom; **gegen `execution/config.py` ist bereits bestätigt: P5-Fenster 09:00–17:30**).

### Offene Punkte / [VERIFY] (für spätere Module, jetzt nur dokumentiert)
- `clock.py`: P5-Fenster-Frage **gelöst** (09:00–17:30, s. o.) — `clock.classify` nutzt
  `config.window_open/close`; `market_hours.is_market_open` nur für „Handelstag/Markt offen".
- `safety.py`: `daily_loss_cap`-Produktionswert (≈€1800) + `realized_pnl_today` aus der **DB**
  (Contract E) — beim Wiring setzen, nicht im Config-Default.
- **Commit:** dieser Step ist noch **nicht** committet (Operator-Entscheidung; Branch
  `phase8-scheduler`). Beim Commit gilt „Commit ⇒ Note-Update": Status-Tabelle (oben ✅) **und**
  dieser Block sind im selben Commit aktuell.

---

## Session stopped — 2026-06-27 (Initial-Steps: Cleanup + Doku + Verify + Scaffold)

### Completed
- **Step 0 (Legacy-Grep):** dokumentierter No-Op — sauber (s. oben). Keine Code-Aktion.
- **Step 0b (Doku-Reconciliation):** root `CLAUDE.md` „Active phase" → Phase 8 (+ kurzer
  Befund-Block A–E); `README.md` Statustabelle Zeile 8 → 🔄 + Fußnote ⁵; `ROADMAP.md`
  Phase-8-Block neu (Mission + Module + Done + Concept-Link). Phase 7 bleibt als ✅
  historischer Block.
- **Step 2 (Scaffold):** `phase8_scheduler/` angelegt — `pyproject.toml` (pkg
  `scheduler`), `requirements.txt` (dev `pytest`; `fastapi`/`uvicorn` **nur** für die
  spätere UI), `README.md`, diese `CLAUDE.md`, `scheduler/__init__.py` (docstring-only,
  Exports wachsen pro Modul), `tests/__init__.py` (leer). `scripts/dev_install.sh` um
  `phase8_scheduler` erweitert (P1→…→P8). **Keine** Scheduler-Logik, **keine** Tests —
  das ist bewusst die Modul-Steps.
- **Step 1 (Verify-against-code):** 7 Contract-Gruppen A–G gegen Live-Code gepinnt (s.
  `## Verifizierte Contracts`), inkl. fünf ⚠-Befunde (A confirm_fn-Konstruktor, B Gate-2-
  Empty-List-Re-Call, C englischer Seed-Marker, D OrderPlan ohne account, E DB-P&L für den
  Loss-Breaker). Dated Konzept-Annotationen für A/B/D in
  `docs/concepts/phase8_scheduler_concept.md`.

### Verifiziert (gemockt / read-only — Live/Netz macht der Operator)
- `python -m py_compile` + `ast.parse` auf `scheduler/__init__.py` OK (import-clean,
  keine Logik). `bash -n scripts/dev_install.sh` OK. Step-0-Grep sauber.
- Bestands-Suiten unberührt (dieser Step schreibt **keine** Logik): erwartet
  P1 52 · P2 62 · P4 94 · P5 146 · P6 70 · P7 128 (Operator/CI bestätigt nach
  `dev_install.sh`).

### Next — **Modul 1: `scheduler/config.py`** (frozen `SchedulerConfig`, TDD, ≥3 Tests)
- Alle Tunables (Konzept §1) an einem Ort: Zeitfenster (reuse P5-Strings), Kadenz,
  Caps (`max_trades_per_day=5`, `daily_loss_cap≈1800`, `max_consecutive_failures=3`,
  Backoff base/cap), Budget, Reconcile-Intervall, Pfade (`live_db_path=data/
  trading_bot.sqlite`, `state_path`, `kill_path=data/state/KILL`, `command_path`),
  `account="demo"` hart. Tests: Defaults; `account != "demo"` baubar (Safety verweigert,
  nicht hier); `daily_loss_cap=None` → geloggte WARNING (kein Crash).
- **Vor `safety.py`/`runner.py`/`reconcile.py` die ⚠-Befunde A/B/D/E/G heranziehen.**

### Offene Punkte / [VERIFY] (für spätere Steps, jetzt nur dokumentiert)
- `clock.py`: P5-`execution/config.py`-Fenster-Defaults (09:30–11:19?) gegen den echten
  Code bestätigen, bevor die Phasen-Klassifikation gebaut wird.
- `safety.py`: `realized_pnl_today` aus der DB (Contract E), nicht nur Cycle-Result.
- `wiring.py`: `Research` direkt aus `research` bauen + EINEN Broker teilen (Contract G).
- Deployment-Top-Risk (Konzept Q3): Keyring/Secret-Service braucht eine **entsperrte**
  Session → fail-closed Preflight in `runner.preflight` + `run_scheduler.sh`-Note.
