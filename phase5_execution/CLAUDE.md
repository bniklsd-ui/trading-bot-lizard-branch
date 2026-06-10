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
│   ├── gates.py          # ✅ Step 3 — Gate 1/2/3/5 (15 Tests)
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
    ├── test_execution_state.py # ✅ Step 2 — write-ahead Idempotenz (10 Tests)
    └── test_gates.py           # ✅ Step 3 — Gate 1/2/3/5 (15 Tests)
```

## Session stopped — 2026-06-10 (Step 3)

### Stand
**Step 3 erledigt** (`gates.py` — Gate 1/2/3/5, reine Funktionen, kein I/O/Clock/AI/Netzwerk).
`pytest phase5_execution/tests -v` → **48 passed** (33 + 15 gates). Bestehende Suites unberührt
(P1 49 · P2 59 · P3 70 · P4 88). Steps 0 + C + 1 + 2 committet (`…`, `bf2de18`); **Step 3
committet, falls** der Operator es triggert (sonst atomarer Commit `phase5: gates 1/2/3/5
(Step 3)`).

### Zuletzt gemacht (Step 3)
- `execution/gates.py` — vier Funktionen:
  - `gate_time_window(now, config)` — Gate 1: `now`→`ZoneInfo(config.tz)`, Time-of-Day
    inklusive `start ≤ t ≤ end`; lokaler `_parse_hhmm`.
  - `gate_load_candidates(state, research_runner, config) -> (GateVerdict, dict|None)` — Gate 2:
    `candidates_are_fresh()` → bei stale `research_runner()` (injiziert, lazy) → `load_candidates()`
    neu lesen; **erster** Candidate; leer → Abstain (`ok=False, None`).
  - `gate_constraints(account_env, open_positions_env, candidate, config)` — Gate 3:
    `available > 0` (aus `get_account().data`), `len(positions) < max_parallel_positions`;
    **env-nicht-ok → reject** (fail-safe).
  - `gate_direction_consistency(candidate, open_positions_env)` — Gate 5: direction ∈ {BUY,SELL},
    keine offene **Gegen**-Position auf **demselben** Epic; **kein** FLIP. Env-nicht-ok → reject.
  - Gate-IDs: `time_window`/`load_candidates`/`constraints`/`direction_consistency`.
- `tests/conftest.py` — gewachsen (Phase-4-Rhythmus): `_FakeEnv` (duck-typed `.ok`/`.data`),
  `make_candidate`-Factory (Phase-4 10-Key-Contract), `FakeState` (konfigurierbar
  `candidates_are_fresh`/`load_candidates`, recording `clear_candidates`). `DEFAULT_EPIC` ergänzt.
- `tests/test_gates.py` — **15 Tests** (≥8): Gate1 in/out/custom-Fenster inkl. tz-Konvertierung;
  Gate2 fresh→erster Pick (Runner nicht gerufen) / stale→Runner→reload / leer→Abstain; Gate3
  budget+room pass / kein-budget / at-max-parallel / env-nicht-ok ×2; Gate5 invalid-direction /
  Gegen-Position / gleiche-Richtung+anderes-Epic pass / env-nicht-ok.
- **Konzept §3** mit dated Annotation (2026-06-10): tz-Konvertierung, erster-Candidate, available-
  Lesepfad, env-nicht-ok→reject, Gate-5-nur-Gegen-Position, Gate-IDs, Testzahl.

### Nächster Schritt — **Step 4** (`sizing.py` — Gate 4)
Konzept §4: `select_risk_pct(db, config)` (`get_risk_level()`: KONSERVATIV →
`risk_pct_conservative`, AGGRESSIV → `risk_pct_aggressive`) und
`compute_size(account_env, price_env, market_info_env, risk_pct, config) -> (float, str|None)`
über P1 `calc_position_size(available_balance=…, risk_pct=risk_pct/100, price=ask,
point_value=1.0)`, **ab auf 0.1**; Ergebnis `< market_info.min_deal_size` → `(0.0,
'below_min_deal_size')` (kein Trade, kein Clamp nach oben). **Wichtig:** Config-`risk_pct` ist
**Prozent** → `/100` an `calc_position_size` (Konzept §0-Annotation). Tests ≥5. `conftest.py`
wächst um `FakeDB` (`get_risk_level`) — `FakeBroker` erst Step 5/6.

### Offene Punkte / [VERIFY]
- IG-Erwartung der absoluten `stop_level`/`limit_level`-Richtung im **Live**-Test (Step 6/10,
  Operator) — Code rechnet BUY: stop unter / limit über Entry.
- `get_ohlcv`-Bar-Shape (`close`-Feld) für VETO 3 erst in Step 5 endgültig gegen `ig_adapter.py`
  prüfen (Konzept nennt `{timestamp, open, high, low, close, volume}`).
- `calc_position_size`-Signatur (`available_balance`, `risk_pct` als Bruchteil, `point_value`,
  Ab-Rundung auf 0.1) in Step 4 direkt gegen `filters.py` gegenlesen, bevor `sizing.py` baut.

### Gotchas
- `setuptools` war im venv **nicht** vorinstalliert; `dev_install.sh` installiert es upfront.
- `pytest` nutzt `phase5_execution/pyproject.toml` als rootdir-Config (kein `[tool.pytest]` nötig).
- Tests importieren `from execution.<modul>` + `from tests.conftest import …` — dank editable
  Install aus Step C (kein `sys.path`).
- Step-0-`grep` (`-i`) matcht das **englische Wort „call"**; daher in Kommentaren
  „order"/„broker I/O" statt „…call" — Done-Check sauber halten.
- `execution_state.json` ist nun **gitignored** (root `.gitignore`, Step-2-Reconciliation,
  analog `turbo_candidates.json`/`llm_usage.json`).
- Gates nehmen **Envelopes direkt** (kein Broker) → kein FakeBroker in Step 3 nötig; der kommt
  mit den VETOs (Step 5) / Order (Step 6), die selbst `get_price`/`get_ohlcv`/`get_open_positions` rufen.
