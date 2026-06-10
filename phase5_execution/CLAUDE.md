# CLAUDE.md — Phase 5: Execution (`phase5_execution/`)

> Erster Order-Pfad des Bots. Demo, manueller Trigger, KEIN Scheduler (= Phase 8).
> Quelle der Wahrheit ist der Code, nicht dieses Dokument.
> Vollständiges Design + alle 8 gelockten Entscheidungen:
> `../docs/concepts/phase5_concept.md`.

## AI-Grenze (Projekt-Kernprinzip)
„So wenig AI wie möglich, so viel AI wie nötig." **Phase 5 enthält KEINE AI.** Alle Gates,
VETOs, Sizing, Order, Monitoring, Reconcile sind deterministischer Code. Die einzige AI im
System bleibt der eine Phase-4-Research-Call (über Gate 2 ausgelöst, lazy). Wer hier ein LLM
„entscheiden/sizen/vetoen" lassen will → stop, das ist Code (oder Phase 6).

## Scope
- **DRIN:** Gate 1–5, `pre_trade_check` (4 VETOs), place/monitor/close, reconcile-on-startup,
  Human-Confirm.
- **DRAUSSEN:** Bull/Bear/Judge (P6), Token-Metering (P6), Outcome-Schreiben (P7),
  Lightstreamer-Stream (P8), ATR-SL/TP, Live-Trading (braucht IG Europe GmbH Konto).

## Paket-Layout (Step C)
Importierbares Paket = **`execution`**, genestet als `phase5_execution/execution/` (Konvention
wie `phase4_research/research/`). `pyproject.toml`/`tests/`/`scripts/` auf Projekt-Ebene.
Imports im Code/Tests: `from execution.<modul> import …`. Editable installs via
`scripts/dev_install.sh` (Repo-Root) — **kein `sys.path`-Hack** mehr.

## Harte Regeln (nicht verhandelbar)
- Step 0 erledigt: kein `option_check`/`CALL`/`PUT`/`strike`/`otm`/`issuer`/`FLIP` in Phase 5.
  Gate 5 heißt `gate_direction_consistency` (reiner Pass-Through-Check, KEIN FLIP).
- Alle 4 VETOs sind HART (= kein Trade). Datenfehler/zu wenige Bars → fail-closed (Veto).
- Momentum-VETO NUR aus `broker.get_ohlcv` (IG-Echtzeit), **NIEMALS** Phase-3-`get_momentum()`.
- Write-ahead `deal_reference` VOR `open_position`; `PENDING` → **kein** zweiter Order-Call,
  fail-closed (bounded Re-Check, sonst `ExecutionAbort`).
- `require_confirm` default AN; `--yes` nur bewusst. **Demo only.**
- `Database` read-only (Outcome-Schreiben = Phase 7). `turbo_candidates.json` NICHT umbenennen.
- Logging → **stderr**; stdout nur maschinenlesbares JSON. Atomic commits. Kein Subtask „done"
  ohne grünes `pytest` (gemockt, kein Netzwerk, **keine echte Order** in Unit-Tests).

## Die 8 Entscheidungen (A–H) — Kurzform (Details: Konzept §0)
- **A** Gate 5 = `gate_direction_consistency` (kein „Fix"/FLIP; Richtung kommt fertig aus P4).
- **B** Genau **4 HARTE** VETOs auf **frischem** Snapshot: Status/Zeit · Spread · Momentum
  (`get_ohlcv`) · Position/Constraint.
- **C** Composition Root via **editable installs** (Step C, erledigt).
- **D** Human-Confirm vor `open_position`, default AN; `--yes` Override. Demo.
- **E** Eigene `deal_reference` write-ahead persistieren; Reconcile-on-Startup; `PENDING`
  fail-closed, nie blind zweite Order.
- **F** `risk_pct` score-gekoppelt via `get_risk_level()`; `calc_position_size(point_value=1.0)`,
  ab auf 0.1; gerundete Size < `min_deal_size` → kein Trade.
- **G** SL/TP beim Entry (absolute Level aus festen Config-Punkten; ATR = späterer Swap).
- **H** Monitoring per Polling; Close-Trigger: Position weg (broker SL/TP) **oder** Time-Stop.

## Die 4 VETOs (CFD-spezifisch, deterministisch — `vetos.py`, noch zu bauen)
1. **Status/Zeit** — frischer `get_price`: `market_status=="TRADEABLE"` UND `now` im Fenster.
2. **Spread (frisch)** — `price.spread_pct ≤ max_spread_pct` (**Default 0.5 %**, nicht
   `spread_at_pick`).
3. **Momentum** — `get_ohlcv(epic, MINUTE_5, 12)`; `net_return=(close_last−close_first)/close_first`
   über **`close`**; BUY & `net_return ≤ −0.15 %` → Veto, SELL & `net_return ≥ +0.15 %` → Veto;
   Datenfehler/zu wenige Bars → Veto. **Schwelle 0.15 % = v1, am Profit zu tunen.**
4. **Position/Constraint** — frischer `get_open_positions`: keine offene Gegen-Position,
   `max_parallel` nicht erreicht.

`SL/TP`-Punkte (`stop=30`/`limit=45`) ebenfalls **v1, am Profit zu tunen.**

## Geerbte Contracts (Repo = Wahrheit, gegen `ig_adapter.py`/`filters.py`/`persistence` geprüft)
- **`get_ohlcv(epic, resolution, count).data`** = `{"bars":[…], "allowance":{…}}`; Bar =
  `{timestamp, open, high, low, close, volume}` (Mid). `MINUTE_5` ∈ `VALID_RESOLUTIONS`,
  `count ∈ (0,1000]`. VETO 3 liest **`close`**.
- **`open_position(epic, direction, size, *, stop_level, limit_level, deal_reference, currency)`**
  → `stop_level`/`limit_level` = **absolute Preis-Level**. `.data` = `{deal_reference, deal_id,
  status, epic, direction, size, level, reason, timestamp}`, `status ∈ {ACCEPTED, REJECTED,
  PENDING, UNKNOWN}` (ACCEPTED = bestätigt, PENDING = Confirm-Timeout). `direction ∈ {BUY,SELL}`
  Pflicht.
- **`get_open_positions().data` = `{"positions":[…]}`** (kein nacktes Array); Position-Dict =
  `{deal_id, deal_reference, epic, direction, size, open_level, …, stop_level, limit_level}`.
- **`reconcile_positions(expected_references=…).data`** = `{broker_position_count,
  broker_deal_ids, present, missing, unexpected}` (die drei Mengen nur mit Refs).
- **`close_position(deal_id)`** schlägt Richtung/Size selbst nach und schließt gegenläufig.
- **P2** `StateManager(state_dir)`: `load_candidates()`/`candidates_are_fresh()`/`save_candidates`/
  `clear_candidates`/`load_bot_config()`. `Database(path)`: `get_risk_level()→
  "AGGRESSIV"|"KONSERVATIV"` (Schwelle Score 50), `get_current_score()`,
  `get_recent_trades/lessons`. **DB read-only.**
- **Sizing** `calc_position_size(*, available_balance, risk_pct, price, point_value=1.0, cap=None)`
  → `notional = balance × risk_pct`, **ab auf 0.1**. Config-`risk_pct` ist **Prozent** →
  `sizing.py` übergibt `risk_pct/100`.
- **Factory** `from broker_wrapper import get_broker; get_broker("ig_demo")` (Keyring, keine
  Netzwerk-Action bei Konstruktion). Credentials: `broker_wrapper.credentials.get_credential`.

## Naht für Phase 6
Hand-off „Candidate → Gates → Order" so bauen, dass P6 die Richtungs-/Size-Quelle
(Bull/Bear/Judge) **austauschen** kann, ohne Gates neu zu schreiben — `gate_direction_consistency`
+ `build_order_plan` sind die Naht.

## Datei-/Modul-Übersicht (Soll, Konzept §"Modul-Plan")
```
phase5_execution/
├── pyproject.toml        # Step C ✅  (Paket „execution")
├── requirements.txt      # ✅ (keine neuen Runtime-Deps)
├── README.md             # ✅
├── CLAUDE.md             # ✅ (diese Datei)
├── execution/
│   ├── __init__.py       # ✅ (exportiert noch nichts)
│   ├── config.py         # ✅ Step 1 — ExecutionConfig (frozen)
│   ├── exceptions.py     # ✅ Step 1 — ExecutionError-Hierarchie
│   ├── protocols.py      # ✅ Step 1 — Broker/Db/State Protocols + EnvelopeLike
│   ├── models.py         # ✅ Step 1 — OrderPlan/GateVerdict/VetoVerdict/ExecutionResult
│   ├── execution_state.py# ✅ Step 2 — write-ahead Idempotenz (10 Tests)
│   ├── gates.py          # ⬜ Step 3 — Gate 1/2/3/5
│   ├── sizing.py         # ⬜ Step 4 — Gate 4
│   ├── vetos.py          # ⬜ Step 5 — pre_trade_check (4 VETOs)
│   ├── order.py          # ⬜ Step 6 — place/reconcile/build_order_plan
│   ├── monitor.py        # ⬜ Step 7 — Polling + Time-Stop
│   ├── executor.py       # ⬜ Step 8 — Orchestrator
│   └── ig_bot.py         # ⬜ Step 9 — CLI Composition Root
├── scripts/              # ⬜ Step 10 — wiring/smoke_test/live_test
└── tests/
    ├── conftest.py             # ✅ Step 2 — make_order_plan/order_plan Factory
    ├── test_packaging.py       # ✅ Step C — editable-install Beweis (6 Tests grün)
    ├── test_config.py          # ✅ Step 1 — Config-Defaults + frozen (4 Tests)
    ├── test_models.py          # ✅ Step 1 — Models + Exceptions (13 Tests)
    └── test_execution_state.py # ✅ Step 2 — write-ahead Idempotenz (10 Tests)
```

## Session stopped — 2026-06-10 (Step 2)

### Stand
**Step 2 erledigt** (`execution_state.py` — write-ahead Idempotenz, **erste Logik + I/O**,
kein Netzwerk). `pytest phase5_execution/tests -v` → **33 passed** (23 + 10 execution_state).
Bestehende Suites unberührt (P1 49 · P2 59 · P3 70 · P4 88). **Nicht committet** — Operator
triggert die Commits (sonst eigener atomarer Commit `phase5: execution_state write-ahead
idempotency (Step 2)`). Steps 0 + C committet (`ed9c407`, `1a35f2a`); Step 1 ggf. noch offen.

### Zuletzt gemacht (Step 2)
- `execution/execution_state.py` — `ExecutionState(path="data/state/execution_state.json")`
  mit `record_pending(plan)` (write-ahead **vor** `open_position`), `mark_open(ref, deal_id)`,
  `mark_closed(ref)`, `open_references()` (Refs in `{PENDING, OPEN}` → reconcile-Input),
  `get(ref)` (Copy oder `None`). Datei-Form `{"records": {<ref>: {…}}}`, 10 Felder/Record.
  Record-Status `PENDING→OPEN→CLOSED` (bewusst getrennt von `ExecutionResult.status`).
  Atomic-Write (temp + `os.replace`) + ISO-Stamp gespiegelt aus P2 `persistence.state`
  (lokale `_utcnow`/`_format_iso`, **kein** Cross-Phase-Import). Korrupte Datei **und**
  unbekannte Ref → `ExecutionError` (nie still überschreiben/anlegen).
- `tests/conftest.py` — **neu** (erste Phase-5-Conftest): `make_order_plan`-Factory (unique
  `bot-<uuid4hex>`-Ref, alle Felder überschreibbar) + `order_plan`-Single-Fixture.
- `tests/test_execution_state.py` — **10 Tests**: write-ahead vor „Order"; mark_open/closed-
  Übergänge; open_references pending+open ohne closed; korrupte Datei → Exception (alle
  Read-Pfade); kein `.tmp`-Rest + Durability über „Neustart"; unbekannte Ref ×2 → Exception;
  `get` unknown→None / known→Copy (Tamper-sicher); fehlende Datei liest leer (legt sie nicht an).
- **Konzept §2** mit dated Annotation (2026-06-10) ergänzt: Datei-Form, Status-Vokabular,
  unbekannte-Ref-raises, Atomic/ISO aus P2, Testzahl.

### Nächster Schritt — **Step 3** (`gates.py` — Gate 1/2/3/5)
Reine, testbare Funktionen (Konzept §3): `gate_time_window(now, config)`,
`gate_load_candidates(state, research_runner, config) -> (GateVerdict, dict|None)` (Gate 2:
`load_candidates()`+`candidates_are_fresh()`; stale/leer → injizierten `research_runner()`
rufen, neu laden; leer → Abstain), `gate_constraints(account_env, open_positions_env,
candidate, config)` (Gate 3: budget>0, offene < `max_parallel_positions`),
`gate_direction_consistency(candidate, open_positions_env)` (Gate 5: direction ∈ {BUY,SELL},
keine offene Gegen-Position auf demselben Epic — **kein** FLIP). `research_runner: Callable`
injiziert (Phase 4 lazy). Tests ≥8. **`conftest.py` wächst** um `FakeBroker`/`FakeState`/
`FakeDB` + Envelope-Fake (noch kein Netzwerk).

### Offene Punkte / [VERIFY]
- Verbleibend für spätere Steps: IG-Erwartung der absoluten `stop_level`/`limit_level`-Richtung
  im **Live**-Test (Step 6/10, Operator) — Code rechnet BUY: stop unter / limit über Entry.
- `get_ohlcv`-Bar-Shape (`close`-Feld) für VETO 3 erst in Step 5 endgültig gegen `ig_adapter.py`
  zu prüfen (Konzept nennt `{timestamp, open, high, low, close, volume}`).

### Gotchas
- `setuptools` war im venv **nicht** vorinstalliert; `dev_install.sh` installiert es upfront.
- `pytest` nutzt `phase5_execution/pyproject.toml` als rootdir-Config (kein `[tool.pytest]` nötig).
- Tests importieren `from execution.<modul>` — dank editable Install aus Step C (kein `sys.path`).
- Step-0-`grep` (`-i`) matcht das **englische Wort „call"**; daher in Kommentaren
  „order"/„broker I/O" statt „…call" — Done-Check sauber halten.
- `execution_state.json` ist neuer operativer State unter `data/state/` — gitignored prüfen,
  falls ein Live-Lauf ihn anlegt (analog `turbo_candidates.json`/`llm_usage.json`).
