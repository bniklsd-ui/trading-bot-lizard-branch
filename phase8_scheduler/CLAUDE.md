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
| `scheduler/exceptions.py` | `SchedulerError`/`PreflightError`/… | ⬜ |
| `scheduler/clock.py` | `now_fn`/`sleep_fn` injizierbar; Phasen-Klassifikation (reuse `is_market_open` + P5-Fenster) | ⬜ |
| `scheduler/state.py` | `SchedulerState` ↔ `scheduler_state.json`; Tages-Rollover (Europe/Berlin) | ⬜ |
| `scheduler/killswitch.py` | KILL-Datei lesen/setzen/löschen (von `safety` + `webui` geteilt) | ⬜ |
| `scheduler/safety.py` | `AutoConfirm` `confirm_fn`: demo + kill + caps + loss-breaker + budget | ⬜ |
| `scheduler/backoff.py` | konsekutive-Fehler-Tracking + Backoff-Schedule | ⬜ |
| `scheduler/budget.py` | Token-Budget-Gate (reuse `token_meter`/`llm_usage.json`) | ⬜ |
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
  Feiertagskalender** (Feiertage fallen in Broker-/VETO-fail-closed). `clock.py` reusen
  für „Handelstag/Markt offen"; die WINDOW-Phase nutzt P5 `config.trading_window_start/
  end` (09:30–11:19 — Defaults im `clock.py`-Step gegen `execution/config.py` prüfen).
- `broker_wrapper.credentials.get_credential(name)` (`credentials.py:56`,
  `SERVICE_NAME="tradingbot"`, wirft `CredentialNotFoundError`) für den Keyring-Preflight.

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
