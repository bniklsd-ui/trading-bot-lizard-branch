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
│   ├── config.py         # ⬜ Step 1 — ExecutionConfig
│   ├── exceptions.py     # ⬜ Step 1
│   ├── protocols.py      # ⬜ Step 1 — Broker/Db/State Protocols
│   ├── models.py         # ⬜ Step 1 — OrderPlan/GateVerdict/VetoVerdict/ExecutionResult
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
    └── test_packaging.py # ✅ Step C — editable-install Beweis (6 Tests grün)
```

## Session stopped — 2026-06-10 (Step 0 + Step C)

### Stand
Composition-Root steht; **noch keine Execution-Logik**. `pytest phase5_execution/tests -v` →
**6 passed** (Packaging-Beweis). Alle bestehenden Suites grün geblieben: P1 49 · P2 59 · P3 70 ·
P4 88. **Nicht committet** (Operator triggert Commits — Step 0 und Step C sind zwei eigene Commits).

### Zuletzt gemacht
- **Step 0 (Terminologie):** `ROADMAP.md` Phase-5-Abschnitt korrigiert — „Gate 5: Direction Fix"
  → `gate_direction_consistency` (kein FLIP), `pre_trade_option_check()` → `pre_trade_check()`.
  (Root-`CLAUDE.md`/`README.md` waren bereits sauber; ROADMAP-Zeile „FLIP-logic" bleibt — die
  gehört zu **Phase 6** Bull/Bear/Judge, kein Options-Erbe.) Greenfield-Paket → Step-0-`grep`
  trivial sauber.
- **Step C (editable installs):** `pyproject.toml` für alle fünf Pakete (`broker-wrapper`,
  `persistence`, `external-data`, `research`, `execution`) mit
  `[tool.setuptools.packages.find] include=["<pkg>*"]` (schließt `scripts`/`tests` aus).
  `scripts/dev_install.sh` (Repo-Root, P1→P2→P3→P4→P5). Phase-5-Skeleton: `execution/__init__.py`
  (leer), `requirements.txt`, `README.md`, `tests/__init__.py`, `tests/test_packaging.py`.
  Alle fünf editable installiert, `find_spec` aus `/tmp` für alle fünf True (kein `sys.path`).
- **Konzept-Reconciliation** (`docs/concepts/phase5_concept.md`, dated 2026-06-10): `max_spread_pct`
  = **0.5 % (nicht ~1.8 pts)**; `risk_pct` Config = Prozent → `/100`; `get_ohlcv`-Bar-Shape +
  `close`-Feld; `open_position` `stop/limit` = absolute Level; `OrderResult.status`-Enum;
  Paket-Layout `execution/` genestet (Tree war schematisch).

### Nächster Schritt
**Step 1** (eine Step pro Session): `execution/config.py` (`ExecutionConfig` frozen dataclass,
alle Felder aus Konzept §0 — `max_spread_pct=0.5`, `risk_pct_*` als Prozent, MINUTE_5/12,
0.15 %, stop=30/limit=45, Fenster 09:00–17:30 / square-off 17:15 Europe/Berlin, poll=15,
require_confirm=True, max_hold=240, reconcile_unexpected_aborts=True) · `exceptions.py`
(`ExecutionError`→`GateRejected`/`VetoRejected`/`ExecutionAbort`/`ReconcileConflict`) ·
`protocols.py` (Broker/Db/State Protocols — nur die geprüften Methoden) · `models.py`
(`OrderPlan`/`GateVerdict`/`VetoVerdict`/`ExecutionResult` frozen). Tests: Config-Defaults +
Verdict-Immutabilität. `conftest.py` mit `FakeBroker` (deckt `get_ohlcv`/`open_position`/
`get_open_positions`/`reconcile_positions`/`close_position`) kommt mit den ersten Logik-Steps.

### Offene Punkte / [VERIFY]
- Erledigt für Step C. Verbleibende [VERIFY] für spätere Steps: exakte IG-Erwartung der
  absoluten `stop_level`/`limit_level`-Richtung im **Live**-Test (Step 6/10, Operator) — Code
  rechnet BUY: stop unter / limit über Entry, SELL umgekehrt.

### Gotchas
- `setuptools` war im venv **nicht** vorinstalliert; `dev_install.sh` installiert es upfront.
  Bei frischem venv ohne Netzwerk schlägt der editable-Install der build-isolation fehl.
- Leeres Junk-Verzeichnis `broker_wrapper/{adapters,streaming}` (Brace-Expansion-Artefakt, kein
  `__init__.py`) → von `find` ignoriert; **nicht** Phase 5, nicht angefasst.
- `pytest` nutzt `phase5_execution/pyproject.toml` als rootdir-Config (kein `[tool.pytest]` nötig).
- `import research`/`external_data` ziehen `anthropic`/`yfinance` NICHT beim Import (lazy) — der
  Packaging-Test nutzt trotzdem bewusst `find_spec` statt echtem Import (robust + nebenwirkungsfrei).
