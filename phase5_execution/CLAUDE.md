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
│   ├── execution_state.py# ⬜ Step 2 — write-ahead Idempotenz
│   ├── gates.py          # ⬜ Step 3 — Gate 1/2/3/5
│   ├── sizing.py         # ⬜ Step 4 — Gate 4
│   ├── vetos.py          # ⬜ Step 5 — pre_trade_check (4 VETOs)
│   ├── order.py          # ⬜ Step 6 — place/reconcile/build_order_plan
│   ├── monitor.py        # ⬜ Step 7 — Polling + Time-Stop
│   ├── executor.py       # ⬜ Step 8 — Orchestrator
│   └── ig_bot.py         # ⬜ Step 9 — CLI Composition Root
├── scripts/              # ⬜ Step 10 — wiring/smoke_test/live_test
└── tests/
    ├── test_packaging.py # ✅ Step C — editable-install Beweis (6 Tests grün)
    ├── test_config.py    # ✅ Step 1 — Config-Defaults + frozen (4 Tests)
    └── test_models.py    # ✅ Step 1 — Models + Exceptions (13 Tests)
```

## Session stopped — 2026-06-10 (Step 1)

### Stand
**Step 1 erledigt** (Typen/Config, **keine Logik, kein I/O, kein Netzwerk**).
`pytest phase5_execution/tests -v` → **23 passed** (6 Packaging + 4 Config + 13 Models/Exceptions).
Bestehende Suites unberührt (P1 49 · P2 59 · P3 70 · P4 88). **Nicht committet, falls** der
Operator den Step-1-Commit selbst triggert (sonst als eigener atomarer Commit `phase5: ...`).
Steps 0 + C sind bereits committet (Branch `phase5-execution`, `ed9c407`, `1a35f2a`).

### Zuletzt gemacht (Step 1)
- `execution/config.py` — `ExecutionConfig` (`@dataclass(frozen=True)`), alle §0-Tunables.
  Reconciled Units: `max_spread_pct=0.5` (**% of ask**), `risk_pct_*` als **Prozent** (sizing.py
  teilt /100). **Neues Feld** `max_parallel_positions=1` (nicht in §0-Tabelle; Gate 3/VETO 4
  brauchen es; v1) → Konzept §0 mit dated Annotation ergänzt.
- `execution/exceptions.py` — `ExecutionError`(Basis, `code`-Attr) → `GateRejected`,
  `VetoRejected`, `ExecutionAbort` (fail-closed), `ReconcileConflict`. Gate/VETO = no-trade
  (exit 0); Abort = Operator/exit≠0.
- `execution/protocols.py` — `EnvelopeLike` + `BrokerProtocol`/`DbProtocol`/`StateProtocol`
  (`@runtime_checkable`), nur die geprüften Methoden. Hält die Kernlogik frei von harten
  Schwester-Imports.
- `execution/models.py` — frozen `OrderPlan`/`GateVerdict`/`VetoVerdict`/`ExecutionResult`
  (Status-Strings im Docstring dokumentiert). `OrderPlan` = Phase-6-Naht.
- `execution/__init__.py` bleibt export-leer (Phase-4-Präzedenz: Public-Surface erst mit dem
  Orchestrator, Step 8). Tests importieren Submodule direkt (`from execution.config import …`).

### Nächster Schritt — **Step 2** (`execution_state.py`)
`ExecutionState(path="data/state/execution_state.json")`: `record_pending(plan)` (write-ahead
**vor** `open_position`), `mark_open(ref, deal_id)`, `mark_closed(ref)`, `open_references()`,
`get(ref)`. Atomar schreiben (temp + `os.replace`), korrupte Datei → `ExecutionError`, nie still
überschreiben. `tests/test_execution_state.py` ≥6. **Hier startet `tests/conftest.py`** (noch kein
Broker nötig — `tmp_path`-Fixture reicht; `FakeBroker` kommt mit Step 3/5/6).

### Offene Punkte / [VERIFY]
- Verbleibend für spätere Steps: IG-Erwartung der absoluten `stop_level`/`limit_level`-Richtung
  im **Live**-Test (Step 6/10, Operator) — Code rechnet BUY: stop unter / limit über Entry.

### Gotchas
- `setuptools` war im venv **nicht** vorinstalliert; `dev_install.sh` installiert es upfront
  (frischer venv ohne Netzwerk → build-isolation-Install schlägt fehl).
- `pytest` nutzt `phase5_execution/pyproject.toml` als rootdir-Config (kein `[tool.pytest]` nötig).
- Tests importieren `from execution.<modul>` — funktioniert dank des editable Installs aus Step C
  (kein `sys.path`-Hack).
- Step-0-`grep` (`-i`) matcht das **englische Wort „call"**; deshalb in `.py`-Kommentaren
  „research run"/„broker I/O" statt „…call" verwendet, damit der Done-Check sauber bleibt.
