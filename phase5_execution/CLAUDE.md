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
│   ├── sizing.py         # ✅ Step 4 — Gate 4 (11 Tests)
│   ├── vetos.py          # ✅ Step 5 — pre_trade_check (4 VETOs) (20 Tests)
│   ├── order.py          # ✅ Step 6 — place/reconcile/build_order_plan (15 Tests)
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
    ├── test_gates.py           # ✅ Step 3 — Gate 1/2/3/5 (15 Tests)
    ├── test_sizing.py          # ✅ Step 4 — Gate 4 (11 Tests)
    ├── test_vetos.py           # ✅ Step 5 — pre_trade_check 4 VETOs (20 Tests)
    └── test_order.py           # ✅ Step 6 — place/reconcile/build_order_plan (15 Tests)
```

## Session stopped — 2026-06-11 (Step 6)

### Stand
**Step 6 erledigt** (`order.py` — der erste Order-Pfad: `reconcile_startup` /
`build_order_plan` / `place_order` mit Write-ahead-Idempotenz + PENDING-fail-closed,
Decision E). Reine Funktionen, Broker duck-typed (`execution.*` + stdlib only, **keine**
Schwester-Imports). `pytest phase5_execution/tests -v` → **94 passed** (79 + 15 order).
Bestehende Suites unberührt (P1 49 · P2 59 · P3 70 · P4 88). Steps 0 + C + 1–5 committet
(zuletzt `3833179`); **Step 6 committet, falls** der Operator es triggert (sonst atomarer
Commit `phase5: order.py write-ahead place + reconcile (Step 6)`).

### Zuletzt gemacht (Step 6)
- `execution/order.py` — drei Funktionen (alle Logging → stderr):
  - `reconcile_startup(broker, exec_state, config)` — vor jedem Lauf:
    `reconcile_positions(expected_references=open_references())`. Leere Refs → kein
    Broker-Request. `not env.ok` → `ExecutionAbort` (Truth unverifizierbar). `missing` →
    `mark_closed` (Orphan, INFO). `unexpected` → bei `reconcile_unexpected_aborts`
    `ReconcileConflict`, sonst WARNING. `present` bleibt offen (Monitor-Sache, Step 7).
  - `build_order_plan(candidate, size, price_env, config)` — **rein**. `deal_reference =
    f"bot-{uuid4().hex[:24]}"` (≤30 Zeichen, **IG-Limit**, wie Adapter `_new_deal_reference`).
    Entry-Seite: **BUY vom `ask`, SELL vom `bid`**; BUY → stop **unter**/limit **über**,
    SELL invertiert; absolute Level aus `stop_/limit_distance_points`.
  - `place_order(broker, exec_state, plan, config, *, sleep_fn=time.sleep)` — 1)
    `record_pending` **WRITE-AHEAD vor** dem einzigen `open_position`; 2) ein
    `open_position(..., deal_reference=ref)`; 3) Branch: **ACCEPTED** → `mark_open` →
    `ExecutionResult("OPEN")`; **PENDING/UNKNOWN** → `_resolve_pending` (bounded Re-Check
    via `reconcile_positions([ref])`, max `pending_recheck_attempts`, `sleep_fn` dazwischen;
    present → `_lookup_deal_id`+`mark_open`, sonst Record bleibt **PENDING** + `ExecutionAbort`,
    **kein** zweiter Order-Call); **REJECTED** → `mark_closed` + `ExecutionAbort`;
    **`not env.ok`** (Transportfehler, mehrdeutig) → Record bleibt **PENDING** + `ExecutionAbort`.
- `config.py` — neue Felder `pending_recheck_attempts=3` / `pending_recheck_interval_s=2.0`
  (v1; Konzept §0 hatte sie „bei Konsum" vertagt).
- `tests/conftest.py` — `FakeBroker` um `open_position` (recording `open_position_calls`,
  echo der Ref ins Result) + `reconcile_positions` (recording `reconcile_calls`, konfig.
  present/missing/unexpected) erweitert.
- `tests/test_order.py` — **15 Tests** (≥8): build_order_plan BUY/SELL-Level + Ref-Länge≤30
  + Ref-Unique; write-ahead **vor** `open_position`; ACCEPTED → OPEN; PENDING→present → OPEN
  (genau **ein** Order-Call); PENDING ungelöst → Abort, Record **PENDING**, ein Call,
  N Re-Checks; UNKNOWN → Re-Check; Transportfehler → Abort + PENDING; REJECTED → CLOSED +
  Abort; reconcile_startup empty/missing/unexpected-abort/unexpected-warn/not-ok.
- **Konzept §6** mit dated Annotation (2026-06-11): deal_reference-Länge-[VERIFY] gelöst,
  Stop/Limit-Richtung + Preis-Seite, neue Config-Felder, Reject-Refinement (nur REJECTED →
  mark_closed; Transportfehler bleibt PENDING), OrderResult/reconcile-`.data`-Form.

### Nächster Schritt — **Step 7** (`monitor.py` — Polling + Time-Stop + Close)
Konzept §7: `monitor_position(broker, exec_state, plan, deal_id, config, *,
now_fn=datetime.now, sleep_fn=time.sleep) -> ExecutionResult`. Loop alle `poll_interval_s`:
`get_open_positions` → `deal_id` weg → broker-SL/TP gefüllt → `mark_closed`,
status `CLOSED_BY_BROKER`. `now >= square_off_time` **oder** `elapsed >= max_hold_minutes`
→ `broker.close_position(deal_id)` → `mark_closed`, status `TIME_STOP`. `now_fn`/`sleep_fn`
injiziert (deterministische Tests, kein echtes Warten). `close_position`-Fehler →
`ExecutionAbort`. **Zuerst** `close_position` gegen `ig_adapter.py:661` gegenlesen (schlägt
Richtung/Size selbst nach, `.data={"deal_id","status":"submitted"}`). Tests ≥6 (FakeBroker um
`close_position` erweitern; gemockte `now_fn`/`sleep_fn`): Position verschwindet →
CLOSED_BY_BROKER; square_off → TIME_STOP; max_hold → TIME_STOP; close-Fehler → Abort;
Loop terminiert immer; state am Ende closed.

### Offene Punkte / [VERIFY]
- IG-Erwartung der **absoluten** `stop_level`/`limit_level` (BUY: stop unter/limit über) bleibt
  ein **Operator-Live-Check** (Step 10) — Unit-Tests prüfen nur die Arithmetik.
- `_lookup_deal_id` toleriert eine fehlende `deal_id` (Ref ist der Idempotenz-Schlüssel); ob
  IG nach PENDING→present zuverlässig die `deal_reference` an der Position mitliefert, ist im
  Live-Test (Step 10) zu bestätigen.

### Gotchas
- **Step-0-`grep` (`-i`) matcht das englische Wort „call"** (und `\bCALL\b` auch in „call-…",
  bare „Call"): in neuen Kommentaren/Docstrings „invocation"/„order"/„broker request" statt
  „…call" — sonst verschmutzt der Done-Check. Identifier `*_calls` sind ok (`\bCALL\b` matcht
  „calls" nicht).
- `_FakeEnv` hat **kein** `error`-Attribut by default; `place_order` liest es via
  `getattr(env, "error", None)`. Im Transportfehler-Test wird `broker.open_env.error` dynamisch
  gesetzt (dataclass nicht frozen).
- `place_order(..., sleep_fn=_no_sleep)` in Tests → Re-Check-Schleife ohne echtes Warten;
  `pending_recheck_interval_s=0.0` in der Test-Config zusätzlich.
- Eine **PENDING/Transportfehler-Order wird NIE `mark_closed`** — nur `REJECTED` (bestätigt
  keine Position). Das ist der Kern von „nie blind eine zweite Order".

---

## Session stopped — 2026-06-11 (Step 5, superseded by Step 6 above)

### Stand
**Step 5 erledigt** (`vetos.py` — `pre_trade_check()` = die 4 HARTEN VETOs auf frischem
Snapshot, fail-closed; reine Funktionen außer dem `get_ohlcv`-Abruf in VETO 3, **keine**
Schwester-Imports). `pytest phase5_execution/tests -v` → **79 passed** (59 + 20 vetos).
Bestehende Suites unberührt (P1 49 · P2 59 · P3 70 · P4 88). Steps 0 + C + 1 + 2 + 3 + 4
committet (zuletzt `4d9ba4e`); **Step 5 committet, falls** der Operator es triggert (sonst
atomarer Commit `phase5: pre_trade_check 4 VETOs (Step 5)`).

### Zuletzt gemacht (Step 5)
- `execution/vetos.py` — 4 VETOs + Orchestrator (alle → `VetoVerdict`, fail-closed):
  - `veto_status_and_window(price_env, now, config)` — VETO 1: env-nicht-ok / `market_status
    != "TRADEABLE"` / außerhalb Fenster → Veto. Fenster-Prädikat **reused** via
    `gates.gate_time_window(now, config).ok` (gleiches Paket, keine tz-Duplikat-Logik).
  - `veto_spread(price_env, config)` — VETO 2: frischer `spread_pct > max_spread_pct` → Veto
    (nicht `spread_pct_at_pick`).
  - `veto_momentum(broker, epic, direction, config)` — VETO 3 (★ `get_ohlcv`): `net_return_pct
    = (close_last−close_first)/close_first × 100` über **`close`**; BUY & `≤ −threshold` /
    SELL & `≥ +threshold` → Veto. env-nicht-ok / **breites Exception** / <2 Bars / fehlender
    bzw. 0-Close → fail-closed Veto (stderr-Log). NIEMALS P3 `get_momentum()`. „v1, am Profit
    zu tunen".
  - `veto_position_conflict(open_positions_env, candidate, config)` — VETO 4: offene
    **Gegen**-Position auf demselben Epic **oder** `len(positions) ≥ max_parallel_positions`
    → Veto. Lokales `_OPPOSITE`.
  - `pre_trade_check(broker, candidate, now, config)` — ein frischer `get_price` → VETO 1+2;
    `veto_momentum` (eigener `get_ohlcv`); frischer `get_open_positions` → VETO 4. Erstes
    `ok=False` zurück (short-circuit), sonst `VetoVerdict(ok=True, veto="pre_trade_check")`.
  - VETO-IDs: `status_window`/`spread`/`momentum`/`position_conflict`.
- `tests/conftest.py` — **`FakeBroker`** (`get_price`/`get_ohlcv`/`get_open_positions`,
  konfigurierbar inkl. `ohlcv_raises`, recording für Short-Circuit-Asserts) + `make_bars`-Helper.
- `tests/test_vetos.py` — **20 Tests** (≥10): jeder VETO pass+fail; Momentum BUY-Abwärts /
  SELL-Aufwärts veto, innerhalb Threshold pass, aligned-Rally pass, zu wenige Bars / env-nicht-ok
  / raise → veto; Spread über Max; Status ≠ TRADEABLE; außerhalb Fenster; Gegen-Position;
  at-max-parallel; `pre_trade_check` all-pass (4 frische Snapshots) **und** Short-Circuit
  (Status-Veto ⇒ `get_ohlcv`/`get_open_positions` nie gerufen).
- **Konzept §5** mit dated Annotation (2026-06-11): Bar-Shape-[VERIFY] aufgelöst (`close`),
  `net_return`-als-Prozent, Window-Reuse, Exception→fail-closed, VETO-IDs, Testzahl.

### Nächster Schritt — **Step 6** (`order.py` — Platzieren mit Write-ahead, Confirm, PENDING-fail-closed)
Konzept §6: `reconcile_startup(broker, exec_state, config)` (vor jedem Lauf
`reconcile_positions(expected_references=exec_state.open_references())`; `missing` →
`mark_closed`, `unexpected` → bei `reconcile_unexpected_aborts` `ExecutionAbort`/`ReconcileConflict`).
`build_order_plan(candidate, size, price_env, config)` (`deal_reference="bot-"+uuid4().hex`;
`stop_level`/`limit_level` aus `stop_/limit_distance_points` relativ zum Preis — **BUY: stop
unter / limit über**, SELL umgekehrt; absolute Level). `place_order(broker, exec_state, plan,
config)` (1) `record_pending` **WRITE-AHEAD vor** `open_position`; 2) `open_position(...,
deal_reference=ref)`; 3) ACCEPTED → `mark_open`; 4) **PENDING** → bounded Re-Check
(`reconcile_positions([ref])`/`get_open_positions`, max N), present → `mark_open`, sonst
`ExecutionAbort` (**kein** zweiter `open_position`-Call); 5) klarer Reject → `mark_closed` +
raise). Tests ≥8 (FakeBroker; write-ahead vor Order; PENDING → genau **ein** `open_position`-Call
+ Abort; reconcile missing/unexpected). **Zuerst** gegen `ig_adapter.py` prüfen: `open_position`-
Signatur (`stop_level`/`limit_level` absolut, `deal_reference`, `currency`), `OrderResult.data`-
Felder (`status ∈ {ACCEPTED,REJECTED,PENDING,UNKNOWN}`, `deal_id`), `reconcile_positions`-`.data`
(`present/missing/unexpected`). FakeBroker um `open_position`/`reconcile_positions` erweitern.

### Offene Punkte / [VERIFY]
- IG-Erwartung der absoluten `stop_level`/`limit_level`-Richtung im **Live**-Test (Step 6/10,
  Operator) — Code rechnet BUY: stop unter / limit über Entry. In Step 6 die `open_position`-
  Signatur + `OrderResult.data`-Form direkt gegen `ig_adapter.py` gegenlesen, bevor `order.py` baut.
- `calc_position_size`-Mirror: bei P1-Formeländerung `_round_down_size` in `sizing.py` nachziehen
  (bewusste Kopplung, Phasen-Isolation > DRY hier — Konzept-§4-Annotation).

### Gotchas
- `setuptools` war im venv **nicht** vorinstalliert; `dev_install.sh` installiert es upfront.
- `pytest` nutzt `phase5_execution/pyproject.toml` als rootdir-Config (kein `[tool.pytest]` nötig).
- Tests importieren `from execution.<modul>` + `from tests.conftest import …` — dank editable
  Install aus Step C (kein `sys.path`).
- **`make_candidate`/`make_order_plan` sind pytest-Fixtures** (geben eine Factory zurück) →
  **nicht** direkt `from tests.conftest import make_candidate` aufrufen; als Test-Parameter
  anfordern. `FakeBroker`/`FakeState`/`FakeDB`/`make_bars`/`_FakeEnv` sind hingegen direkt
  importierbar.
- Step-0-`grep` (`-i`) matcht das **englische Wort „call"**; daher in Kommentaren
  „order"/„broker I/O" statt „…call" — Done-Check sauber halten.
- `execution_state.json` ist nun **gitignored** (root `.gitignore`, Step-2-Reconciliation,
  analog `turbo_candidates.json`/`llm_usage.json`).
- Sizing ist float-empfindlich: `int(raw*10)/10.0` schneidet ab — z. B. raw `0.6` → `0.5`
  (Double-Repräsentation). Testwerte auf das 0.1-Grid legen.
- VETO 3 `net_return` ist **Prozent** (`×100`) — passend zu `momentum_veto_threshold_pct`/
  `spread_pct`. Bei neuen Momentum-Tests Closes so wählen, dass der Prozent-Move klar über/unter
  0.15 liegt.
