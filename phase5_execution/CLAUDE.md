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
│   ├── sizing.py         # ✅ Step 4 — Gate 4 (13 Tests; sizing reworked 2026-06-12)
│   ├── vetos.py          # ✅ Step 5 — pre_trade_check (4 VETOs) (20 Tests)
│   ├── order.py          # ✅ Step 6 — place/reconcile/build_order_plan (15 Tests)
│   ├── monitor.py        # ✅ Step 7 — Polling + Time-Stop + Close (6 Tests)
│   ├── executor.py       # ✅ Step 8 — Orchestrator (8 Tests)
│   └── ig_bot.py         # ✅ Step 9 — CLI Composition Root (18 Tests)
├── scripts/              # ✅ Step 10 — wiring/smoke_test/live_test (operator-run, no CI)
└── tests/
    ├── conftest.py             # ✅ Step 2 — make_order_plan/order_plan Factory
    ├── test_packaging.py       # ✅ Step C — editable-install Beweis (6 Tests grün)
    ├── test_config.py          # ✅ Step 1 — Config-Defaults + frozen (4 Tests)
    ├── test_models.py          # ✅ Step 1 — Models + Exceptions (13 Tests)
    ├── test_execution_state.py # ✅ Step 2 — write-ahead Idempotenz (10 Tests)
    ├── test_gates.py           # ✅ Step 3 — Gate 1/2/3/5 (15 Tests)
    ├── test_sizing.py          # ✅ Step 4 — Gate 4 (13 Tests; sizing reworked 2026-06-12)
    ├── test_vetos.py           # ✅ Step 5 — pre_trade_check 4 VETOs (20 Tests)
    ├── test_order.py           # ✅ Step 6 — place/reconcile/build_order_plan (15 Tests)
    ├── test_monitor.py         # ✅ Step 7 — Polling + Time-Stop + Close (6 Tests)
    ├── test_executor.py        # ✅ Step 8 — full-cycle orchestrator (8 Tests)
    └── test_ig_bot.py          # ✅ Step 9 — CLI helpers (exit/serialise/argparse/confirm, 18 Tests)
```

## Session stopped — 2026-06-12 (Position-Sizing-Rework — Gate 4)

### Stand
**Sizing-Rework erledigt** (die ⚠ PRIORITÄT aus der Steps-9+10-Session unten). Gate 4
sizt jetzt nach **Risk-per-Trade ÷ Stop-Distanz** statt notional ÷ Preis → ein ~€1 K-
Budget liefert eine handelbare Size ≥ `min_deal_size`. **Operator-gegengelesen** (beide
offenen Entscheidungen im Plan-Mode bestätigt). `pytest phase5_execution/tests -v` →
**128 passed** (war 126; +2 neue Sizing-Tests). Andere Suites unberührt (P1 49 · P2 59 ·
P3 70 · P4 88) — die Änderung ist Phase-5-isoliert. **Nicht committet** (Operator triggert).

### Zuletzt gemacht
- **`execution/sizing.py`** — `_round_down_size` → **`_size_from_risk`**:
  `raw = (balance × risk_pct) / (stop_distance_points × point_value)`, Notional-Deckel
  `cap = (balance × max_leverage) / (price × point_value)`, `min(raw, cap)`, **ab** auf 0.1,
  `0.0` bei nicht-positiver Balance/Stop/Preis. `compute_size`-Signatur **unverändert**
  (`config` trägt `stop_distance_points`/`max_leverage`); Reason-Codes unverändert; `risk_pct/100`
  bleibt. Modul-/Funktions-Docstrings warnen explizit: P1-`calc_position_size`-Spiegel **bewusst
  gelöst** — nicht „zurückfixen".
- **`execution/config.py`** — `risk_pct_conservative` `0.5→2.0`, `risk_pct_aggressive` `1.0→3.0`
  (jetzt Risk-per-Trade-Prozente), **neu** `max_leverage: float = 20.0`. Docstrings + Reconcile-
  Notiz aktualisiert. (Operator-Entscheidung 2026-06-12: 2.0/3.0 + Notional-Cap.)
- **Tests** — `test_sizing.py` neu gerechnet (stop=30/pt=1, preisunabhängig) + 2 neue Fälle:
  `test_thousand_euro_budget_is_tradeable` (die Regression: €1 K → 0.6 ≥ 0.5) und
  `test_leverage_cap_clips_oversized_risk` (tiny Stop + große Balance → Cap greift).
  `test_executor.py`/`conftest.py` Balances auf realistische ~€0.4–1.5 K (Default 400 → no-trade,
  Happy-Path 1500 → 1.0 lot); `test_config.py` Defaults + `max_leverage`.
- **Konzept** `docs/concepts/phase5_concept.md` — dated §4-Annotation (2026-06-12) + Decision-F-
  Zeile + Config-Tabelle (`⟳ 2026-06-12`-Marker, `max_leverage`-Zeile).

### Nächster Schritt — Operator-Live-Gate (⚠ ZWEI offene Aktionen) + Step 11
- **Live-Test-Lauf 2026-06-12 ~07:38 (Operator):** `live_test.py` lief sauber, aber Gate 1
  (Handelsfenster) hat **vor** Sizing/Order kurzgeschlossen — `07:38 outside trade window
  09:00-17:30 Europe/Berlin` → `NO_TRADE`, `RESULT: 2/2 passed`, exit 0. Der Markt/​das
  Fenster war noch zu; der Order-/Monitor-Pfad mit dem neuen Sizing ist damit **noch nicht**
  live durchlaufen. **Das ist KEIN Fehler** — nur das Zeitfenster.
- ⚠ **Aktion 1 — Candidate NEU SEEDEN:** der frisch geseedete Candidate (2026-06-12, 30-min
  TTL) **läuft vor 09:00 ab**. Vor dem nächsten Live-Lauf neu seeden (gleiches 10-Feld-Format,
  `source:"research"`, via `StateManager.save_candidates([...])` für frische TTL). **Kein**
  `risk_pct`/Balance-Hack mehr nötig — das ~30 K-Demo (oder ~€1 K) liefert jetzt eine valide Size.
- ⚠ **Aktion 2 — Live-Test ERNEUT laufen, INNERHALB des Fensters (09:00–17:30 Europe/Berlin):**
  `python scripts/smoke_test.py` (DRY) → `python scripts/live_test.py` gegen IG Demo. Jetzt
  erwartet: echter open→Time-Stop-close (kein erzwungenes `below_min`-NO_TRADE mehr), `exit 0` —
  **das** ist der eigentliche Beweis fürs neue Sizing + den Order-/Monitor-Pfad.
- Danach **Step 11** (`README.md`/`requirements.txt` + Top-Level-Doku-Flip) wie unten beschrieben.

### Offene Punkte
- Order-/Monitor-Pfad ist live weiterhin **ungetestet** (07:38-Lauf brach an Gate 1 ab), bis der
  Operator **innerhalb des Fensters** mit frischem Candidate + neuem Sizing einen Trade durchspielt
  (in CI über `test_executor.py`/`test_order.py` gedeckt). Siehe Aktion 1 + 2 oben.
- `max_leverage=20.0` / `risk_pct` 2.0/3.0 sind **v1** (am Profit zu tunen, nicht jetzt).

---

## Session stopped — 2026-06-11 (Steps 9 + 10)

### Stand
**Steps 9 + 10 erledigt** — Phase 5 ist **code-complete**. `ig_bot.py` (CLI-Entry, Step 9)
+ `scripts/` (`wiring.py`/`smoke_test.py`/`live_test.py`, Step 10, operator-run). `pytest
phase5_execution/tests -v` → **126 passed** (108 + 18 ig_bot). Bestehende Suites unberührt
(P1 49 · P2 59 · P3 70 · P4 88). Steps 0 + C + 1–9 committet (zuletzt `14f2c32`); **Step 10
committet, falls** der Operator es triggert (sonst atomarer Commit `phase5: wiring + smoke +
live scripts (Step 10)`). **Einziges offenes Item: der Operator-Live-Gate** (`scripts/
live_test.py` gegen IG Demo) + Step 11 (`README.md`/`requirements.txt`, Top-Level-Doku-Flip).

### Zuletzt gemacht (Steps 9 + 10)
- **`execution/ig_bot.py`** (Step 9) — CLI-Entry im `execution`-Paket (`python -m
  execution.ig_bot`). Reine, getestete Helfer: `exit_code` (1 nur bei `ABORT`, sonst 0),
  `result_to_dict` (`dataclasses.asdict`, rekursiv in `OrderPlan` → JSON auf **stdout**),
  `build_arg_parser`/`parse_args` (`--yes`/`--dry`/`--epic`/`--broker`/`--verbose`),
  `make_confirm_fn` (`--yes`→True · `--dry`→logge Plan + False (keine Order) · sonst stdin
  `y/N`, `input_fn` injizierbar). `main()` importiert `scripts.wiring.build_executor` **lazy**
  (ein `sys.path.insert(<phase5_execution/>)`) → kein Keyring/Netz bei `--help`/Unit-Tests.
  Human-Summary → **stderr**.
- **`execution/__init__.py`** — stale „exports land with Step 1" aufgelöst: exportiert jetzt
  `Executor`/`ExecutionConfig`/`ExecutionState`/`ExecutionResult`/`OrderPlan`/`GateVerdict`/
  `VetoVerdict`.
- **`tests/test_ig_bot.py`** — **18 Tests** (rein, kein Netz/Keyring/Wiring-Import):
  `exit_code` je Status (ABORT→1, Rest→0), `result_to_dict` mit/ohne Plan (JSON-roundtrip),
  argparse-Defaults+Flags, `make_confirm_fn` (yes/dry/stdin y·Y·yes·n·""·nope).
- **`scripts/wiring.py`** (Step 10) — `build_executor(config, *, confirm_fn,
  broker_name="ig_demo", research_config=None, epic_override=None) -> Executor`. Editable-
  Install-Imports (**kein** sys.path). Baut `get_broker(broker_name)`, `Database`,
  `StateManager`, `ExecutionState`. **`research_runner`** = Closure, die eine `Research`
  **lazy** baut und **broker/db/state teilt** (→ persistiert in dieselbe
  `turbo_candidates.json`, die Gate 2 liest); `Research` wird **direkt** aus dem installierten
  `research`-Paket konstruiert (nicht Phase-4-`scripts.build_research` — `scripts`-Namens-
  kollision; §10-Reconciliation). **tz-aware `now_fn`** = `lambda: datetime.now(ZoneInfo(
  config.tz))` (der Executor-Default `datetime.now` ist naiv → Gate-1/VETO-Fenster sonst
  server-tz-abhängig).
- **`scripts/smoke_test.py`** — DRY: `make_confirm_fn(dry=True)` → volle Pipeline, **keine**
  `open_position`. Druckt Outcome + would-be-Plan (stderr) + Result-JSON (stdout). Mirror P4.
- **`scripts/live_test.py`** — hart-asserted Operator-Gate: `make_confirm_fn(auto_yes=True)`,
  Config-Override `max_hold_minutes=1`/`poll_interval_s=10` → platzierte Order schließt
  schnell per Time-Stop (kein 4-h-Block). Asserts: run() ohne Raise; Status ∈ clean set (kein
  ABORT); bei platzierter Order `deal_id` + `exec_state`-Record endet `CLOSED`; sauberes
  `NO_TRADE`/Abstain = valider exit-0. `RESULT: N/M` → stderr, JSON → stdout.
- **Konzept §9 + §10** mit dated Annotationen (2026-06-11).

### ✅ ERLEDIGT 2026-06-12 (siehe Session-Block oben) — ~~⚠ PRIORITÄT — Position-Sizing überarbeiten~~ (Operator-Befund 2026-06-11)
- **Befund (live bestätigt):** Mit geseedetem Candidate lief der volle Pfad bis **Gate 4**;
  `compute_size` lieferte `below_min_deal_size` → `NO_TRADE`. Ursache ist die **Sizing-Mathematik**,
  nicht die Pipeline: `_round_down_size` rechnet `notional = balance × (risk_pct/100)`, dann
  `size = notional / price`. Für DAX ~18000 @ €1/Punkt, `min_deal_size=0.5`, `risk_pct=0.5 %`
  braucht das eine Balance von **~€1.8 M**, um überhaupt Size 0.5 zu erreichen. Selbst das
  **30 K**-Demokonto (Operator) rundet auf **0.0**.
- **Anforderung (Operator):** Das echte Konto wird mit **~€1 K Budget** laufen. Sizing **muss**
  bei ~€1 K eine sinnvolle, handelbare Size (≥ `min_deal_size` 0.5) liefern.
- **Richtung (zu bestätigen, nicht gelockt):** vom notional-÷-Preis-Modell auf ein
  **Risk-per-Trade-÷-Stop-Distanz-Modell** wechseln: `size = (balance × risk_pct) /
  (stop_distance_points × point_value)` — die Size hängt dann an der **SL-Distanz** statt am
  Indexpreis (€1 K × 2 % / (30 × €1) ≈ 0.66 → ab 0.5). Betrifft `execution/sizing.py`
  (`_round_down_size`/`compute_size`), die Config-`risk_pct_*`/`stop_distance_points` und die
  **bewusste Phase-1-`calc_position_size`-Spiegelung** (Kopplung lösen oder mitziehen). Ist eine
  **Semantik-Änderung** → Konzept §4/Decision F + Annotation aktualisieren, Operator gegenlesen.
- v1 war `below_min_deal_size` als „kein Bug" markiert — der Operator hat es jetzt als
  **echtes Sizing-Problem** eingeordnet. Siehe auch Projekt-Memory `project_phase5_sizing_rework`.

### Nächster Schritt — **Step 11** (`README.md` · `requirements.txt` + Doku-Flip) + Operator-Gate
- `requirements.txt`: nur Phase-5-eigene Dev-Deps (Runtime kommt über die editable installs
  der Schwester-Packages). `README.md`: kurz — was `phase5_execution/` ist (erster
  Execution-Pfad, Demo, manueller Trigger), wie man `ig_bot.py`/`smoke_test.py`/`live_test.py`
  startet, Verweis auf diese `CLAUDE.md`.
- **Operator-Gate (der User führt es aus — Claude macht Code + gemockte Tests):** frische venv
  → `bash scripts/dev_install.sh` → `python phase5_execution/scripts/smoke_test.py` (DRY-Sanity,
  keine Order) → `python phase5_execution/scripts/live_test.py` (realer open→close gegen IG
  Demo, `exit 0` = PASS; markt-geschlossen → sauberer NO_TRADE/Abstain, ebenfalls exit 0).
- Wenn der Live-Gate grün ist: Top-Level-`CLAUDE.md` „Current state" + Root-`README` auf
  Phase 5 ✅ live-verifiziert flippen (Phase-6-Konzept/Transition in der Browser-Session).

### Offene Punkte / [VERIFY]
- **IG-Erwartung der absoluten SL/TP-Level** (BUY: stop unter/limit über) bleibt der
  **Operator-Live-Check** in `live_test.py` — Unit-Tests prüfen nur die Arithmetik.
- ~~**Sizing rundet auf 0.0 → `below_min_deal_size`**~~ **✅ behoben 2026-06-12** (Risk-per-Trade-
  Modell, siehe Session-Block oben): das ~30 K-Demo **und** ein ~€1 K-Konto liefern jetzt eine
  valide Size. Manuelles Durchspielen braucht **keinen** Balance-/`risk_pct`-Hack mehr — nur einen
  **frisch geseedeten** Candidate (der alte ist abgelaufen). Der Order-/Monitor-Pfad bleibt live
  ungetestet, bis der Operator das mit frischem Candidate durchspielt (CI deckt ihn).
- `close_position`-vanished-Edge (Monitor, Step 7) bleibt v1 grob (Abort statt Error-Parse).

### Gotchas
- **Step-0-`grep` (`-i`)** matcht „call"/„put": in neuer Prosa „invocation"/„order"/„broker
  request"; `*_calls` ok. `ig_bot.py` + `scripts/*` sind sauber geprüft.
- **`scripts/` ist NICHT installiert** (pyproject `include=["execution*"]`) — die drei Scripts
  laufen direkt mit `sys.path.insert(<phase5_execution/>)` + `from scripts.wiring import …`
  (Phase-4-Muster). Das `execution`-Runtime-Paket bleibt sys.path-frei (editable install).
- **`scripts.wiring` darf NICHT Phase-4-`scripts.wiring` importieren** (gleicher Modulname →
  Kollision); Phase-5-Wiring baut `Research` selbst aus dem `research`-Paket.
- **`research_runner` teilt den Broker** mit dem Executor — der Broker ist beim Gate-2-Aufruf
  bereits via `_ensure_session()` connected; `Research._preflight` sieht `is_connected()=True`.
- `--epic` ist ein **Research-Allow-List-Override** (an `build_executor(epic_override=…)`), kein
  `ExecutionConfig`-Feld; der Executor nimmt das Epic aus dem Candidate.

---

## Session stopped — 2026-06-11 (Step 8, superseded by Steps 9 + 10 above)

### Stand
**Step 8 erledigt** (`executor.py` — der Orchestrator, der den ganzen Pfad komponiert:
Session-Health → Reconcile → Gate 1/2/3/5 → Gate 4 Sizing → 4 VETOs → Confirm → Place →
Monitor). **Reine Komposition** — keine neue Broker-/Gate-/VETO-Logik. `execution.*` +
stdlib only, Broker/DB/State duck-typed (kein Schwester-Import). `pytest
phase5_execution/tests -v` → **108 passed** (100 + 8 executor). Bestehende Suites unberührt
(P1 49 · P2 59 · P3 70 · P4 88). Steps 0 + C + 1–7 committet (zuletzt `9faab0a`); **Step 8
committet, falls** der Operator es triggert (sonst atomarer Commit `phase5: executor.py
orchestrator (Step 8)`).

### Zuletzt gemacht (Step 8)
- `execution/executor.py` — `class Executor(__init__(broker, db, state, exec_state, config,
  research_runner, confirm_fn, *, now_fn=datetime.now, sleep_fn=time.sleep))` + `run() ->
  ExecutionResult`. Flow (alles Code, **keine AI** außer dem lazy P4-`research_runner` in Gate 2):
  1. `_ensure_session()` — `is_connected()` → sonst `connect()` (`.ok`); `get_account()`
     (`.ok`) → sonst `ExecutionAbort`. Das Account-Env wird **zurückgegeben + downstream
     wiederverwendet** (ein `get_account` pro Lauf).
  2. `reconcile_startup(...)` — `ExecutionAbort`/`ReconcileConflict` → `ABORT`.
  3. `now = now_fn()` **einmal** (Gate 1 + VETO-Fenster teilen es). **Gate 1**
     `gate_time_window` → fail → `NO_TRADE`.
  4. **Gate 2** `gate_load_candidates` (lazy `research_runner` bei stale) → leer → `NO_TRADE`.
  5. `positions_env = get_open_positions()` **einmal** → **Gate 3** `gate_constraints` +
     **Gate 5** `gate_direction_consistency` (teilen das Env) → fail → `NO_TRADE`.
  6. **Gate 4** `get_price`(reused) + `get_market_info` + `select_risk_pct` + `compute_size`
     → `reason is not None` → `NO_TRADE`.
  7. **`pre_trade_check`** (4 frische VETOs) → fail → `NO_TRADE`.
  8. `build_order_plan(..., price_env)` (reused Gate-4-Preis).
  9. **Human-Confirm:** `require_confirm and not confirm_fn(plan)` → `ABORTED_BY_USER`
     (**kein** `open_position`, **kein** `record_pending`).
  10. `place_order(..., sleep_fn)`; bei `status=="OPEN"` → `monitor_position(..., now_fn,
      sleep_fn)`. `ExecutionAbort` aus place/monitor → `ABORT`.
  - **Aborts werden returned, nicht geraised** (`status="ABORT"`) → Step-9-`ig_bot` macht
    `exit != 0` bei `ABORT`. Logging → **stderr**; stdout bleibt Step-9-JSON. Helper
    `_no_trade`/`_abort`.
- `tests/conftest.py` — `FakeBroker` um die Session-/Sizing-Fläche erweitert: `is_connected`
  (default True) / `connect` / `get_account` (default `available` **modest** → Default-Pfad
  no-traded am Sizing) / `get_market_info` (default `min_deal_size=0.5`) + Recording-Counter.
- `tests/test_executor.py` — **8 Tests** (≥8): voller Pfad open→CLOSED_BY_BROKER (ein
  `open_position`, Record CLOSED, `research_runner` nicht gerufen); Gate-1-Fenster-Fail (kein
  Research/keine Order, `get_open_positions` nie); Gate-2-Abstain; **adverse-Momentum-VETO**
  (Proof-Test b, keine Order); size<min; **Confirm abgelehnt** (Proof-Test c, keine Order,
  kein Write-ahead); Session-Health-Fail → ABORT; Reconcile-Konflikt (`unexpected`) → ABORT.
- **Konzept §8** mit dated Annotation (2026-06-11): injizierte `now_fn`/`sleep_fn` am
  `Executor`; Aborts als `status="ABORT"` returned statt geraised; Single-Fetch-Reuse von
  account/positions/price; `account_env`-Reuse Session-Health↔Gate-3/Sizing.

### Nächster Schritt — **Step 9** (`ig_bot.py` — CLI-Entry / Composition Root)
Konzept §9: `argparse` (`--yes` confirm-Override → `lambda _p: True`; `--epic` Override;
`--dry` = Gates+VETOs ohne Order; `--broker ig_demo` Default). Baut den Executor über
`scripts/wiring.build_executor(config)` (Step 10), `confirm_fn` = stdin `y/N`-Prompt
(Default). Druckt das `ExecutionResult` als **JSON auf stdout**, Logs auf **stderr**.
`exit 0` bei sauberem Lauf (auch `NO_TRADE`/`ABORTED_BY_USER`), `exit != 0` **nur** bei
`status == "ABORT"`. ⚠ Step 9 + 10 (wiring/scripts) hängen zusammen — `ig_bot` braucht
`build_executor`; ggf. Step 10 (`wiring.py`) zuerst oder gemeinsam. Keine Unit-Tests für die
Live-Scripts (Operator führt sie aus); `ig_bot`-Argparse/Exit-Code-Mapping ist testbar.

### Offene Punkte / [VERIFY]
- IG-Erwartung der absoluten SL/TP-Level (BUY: stop unter/limit über) bleibt **Operator-
  Live-Check** (Step 10 `live_test.py`).
- `close_position`-vanished-Edge (Time-Stop-Close gegen schon-geschlossene Position →
  ExecutionAbort) bleibt v1 grob (Monitor, Step 7) — späteres Refinement.
- Sizing-Realität: bei realistischer Demo-Balance rundet die Size oft auf 0.0 → `below_min
  _deal_size` (kein Trade). Der Happy-Path-Test nutzt bewusst `available=2_000_000`, damit
  eine valide Size (≈0.5) entsteht — **kein** Hinweis auf einen Bug, nur Test-Arithmetik.

### Gotchas
- **Step-0-`grep` (`-i`)** matcht das englische Wort „call"/„put": in neuen Kommentaren/
  Docstrings „invocation"/„broker request"/„order" statt „…call". `*_calls` ist ok.
  `executor.py` + `conftest.py`-Zusatz sind gegen den Grep sauber geprüft.
- **`now_fn` wird einmal in `run()` gerufen** (Gate 1 + VETO teilen `now`) **und dann an
  `monitor_position` durchgereicht** (das es pro Loop ruft). Fixe `lambda: _at(10,0)` deckt
  beides ab; für Gate-1-Fail eine out-of-window-`lambda`.
- **`positions_sequence` im Voll-Pfad** muss **4** Envs liefern: Gate-3/5-Fetch (1, leer),
  VETO-4-Fetch (1, leer), Monitor-Poll-present (1), Monitor-Poll-gone (1) — der Executor holt
  `get_open_positions` für Gate 3+5 **einmal** (geteiltes Env).
- **`research_runner`** wird in Gate 2 **nur bei `not candidates_are_fresh()`** gerufen — die
  meisten Tests nutzen `FakeState(fresh=True, candidates=[…])` → Runner nicht gerufen.

---

## Session stopped — 2026-06-11 (Step 7, superseded by Step 8 above)

### Stand
**Step 7 erledigt** (`monitor.py` — Polling-Loop + Time-Stop + broker-seitige
Close-Erkennung, Decision H). Reine Funktion, Broker duck-typed (`execution.*` + stdlib
only, **keine** Schwester-Imports), `now_fn`/`sleep_fn` injiziert (deterministische Tests,
kein echtes Warten). `pytest phase5_execution/tests -v` → **100 passed** (94 + 6 monitor).
Bestehende Suites unberührt (P1 49 · P2 59 · P3 70 · P4 88). Steps 0 + C + 1–6 committet
(zuletzt `2027f19`); **Step 7 committet, falls** der Operator es triggert (sonst atomarer
Commit `phase5: monitor.py polling + time-stop close (Step 7)`).

### Zuletzt gemacht (Step 7)
- `execution/monitor.py` — `monitor_position(broker, exec_state, plan, deal_id, config, *,
  now_fn=datetime.now, sleep_fn=time.sleep) -> ExecutionResult`:
  - `entry = now_fn()` **einmal** (Max-Hold-Anker). Loop:
    1. `get_open_positions` — `ok` **und** `deal_id` **nicht** in `positions` → broker-SL/TP
       gefüllt → `mark_closed` → `ExecutionResult("CLOSED_BY_BROKER")`. **`not ok`** → **kein**
       Close inferieren (WARNING, weiter pollen).
    2. Time-Stop: `_is_after_square_off(now, config)` **oder** `(now−entry) ≥ max_hold` →
       `close_position(deal_id)`; `not ok` → `ExecutionAbort`; sonst `mark_closed` →
       `ExecutionResult("TIME_STOP")` (`detail` trägt `square_off`/`max_hold`).
    3. `sleep_fn(poll_interval_s)`, repeat.
  - `_is_after_square_off` **reused** `gates._parse_hhmm` + `gate_time_window`-tz-Idiom.
  - `_position_present(positions_env, deal_id)` — `any(p["deal_id"]==deal_id)`.
- `tests/conftest.py` — `FakeBroker` um `close_position` (recording `close_position_calls`,
  konfig. `close_env`) + `positions_sequence` (eine Env pro `get_open_positions`-Aufruf,
  letzte wiederholt → „present then gone") erweitert.
- `tests/test_monitor.py` — **6 Tests** (≥6): present→gone → CLOSED_BY_BROKER (kein
  close-Call, ein Sleep); square_off → TIME_STOP (close-Call); max_hold → TIME_STOP;
  close-Fehler → ExecutionAbort (genau ein close-Versuch); mehrere Polls mit Sleep dazwischen
  + Terminierung; `not ok`-Read → **kein** falscher Close, Time-Stop beendet. `_Clock`-Helper
  (Sequenz, letzte wiederholt) + zählendes `sleep_fn`.
- **Konzept §7** mit dated Annotation (2026-06-11): `close_position`-Contract +
  vanished-position-Edge (v1 Abort), Max-Hold-Anker, not-ok-Read-inferiert-keinen-Close,
  `_parse_hhmm`-Reuse, Status-Vokabular.

### Nächster Schritt — **Step 8** (`executor.py` — Orchestrator, der ganze Pfad)
Konzept §8: `class Executor(__init__(broker, db, state, exec_state, config, research_runner,
confirm_fn))` + `run() -> ExecutionResult`. Flow (alles Code, **keine AI** außer dem
lazy Phase-4-`research_runner` in Gate 2):
1. `connect()`/`is_connected()` + Session-Health (`get_account().ok`) → Fail → Abort.
2. `reconcile_startup(...)` → Konflikt → Abort.
3. **Gate 1** `gate_time_window` → fail → `ExecutionResult("NO_TRADE", reason)`.
4. **Gate 2** `gate_load_candidates` (ggf. `research_runner()`); leer → `NO_TRADE` (Abstain).
5. **Gate 3** `gate_constraints` + **Gate 5** `gate_direction_consistency` → fail → `NO_TRADE`.
6. **Gate 4** Sizing (`select_risk_pct`/`compute_size`); size<min → `NO_TRADE`.
7. **`pre_trade_check`** (4 VETOs, frisch) → fail → `NO_TRADE` (Grund geloggt).
8. `plan = build_order_plan(...)`.
9. **Human-Confirm:** `if config.require_confirm and not confirm_fn(plan): return
   ExecutionResult("ABORTED_BY_USER")` — **kein** `open_position`.
10. `place_order(...)` → bei OPEN: `monitor_position(...)`.
11. Jede REJECT/VETO/Abort-Begründung → **stderr**; stdout nur Ergebnis-JSON (Step 9 `ig_bot`).
`confirm_fn: Callable[[OrderPlan], bool]` injiziert. Tests ≥8 (FakeBroker): voller Pfad
open→close; Gate-1-Fail → kein LLM/keine Order; Gate-2-Abstain; VETO-Fail; size<min;
`require_confirm`+confirm=False → ABORTED_BY_USER (**kein** open_position); Session-Health-Fail
→ Abort; reconcile-Konflikt → Abort.

### Offene Punkte / [VERIFY]
- IG-Erwartung der absoluten SL/TP-Level (BUY: stop unter/limit über) bleibt **Operator-Live-Check**
  (Step 10).
- `close_position`-vanished-Edge (Time-Stop-Close gegen schon-geschlossene Position →
  ExecutionAbort) ist v1 bewusst grob — späteres Refinement (Error parsen → CLOSED_BY_BROKER
  statt Abort).
- Confirm-Fn-Signatur/Prompt-Pfad in Step 8/9 festzurren (stdin `y/N`, `--yes` → `lambda _p: True`).

### Gotchas
- **Step-0-`grep` (`-i`)** matcht das englische Wort „call"/„Call" (auch bare): in neuen
  Kommentaren/Docstrings „invocation"/„poll"/„broker request" statt „…call". Identifier
  `*_calls` sind ok (`\bCALL\b` matcht „calls" nicht).
- Monitor-Tests: `now_fn` wird **einmal für `entry`** + **einmal pro Loop-Iteration** gerufen
  → `_Clock`-Sequenz entsprechend dimensionieren (erste = entry). `mark_closed` braucht einen
  **existierenden** Record → in Tests `record_pending`+`mark_open` (Fixture `open_plan`) vor
  `monitor_position`.
- `positions_sequence` mutiert die Liste (`pop(0)`) bis 1 Element bleibt (wiederholt) — pro
  Test eine frische Liste bauen.
- Time-Stop-Reihenfolge: **erst** Position-weg-Check, **dann** Time-Stop (wenn Broker schon
  geschlossen hat, kein eigener Close).

---

## Session stopped — 2026-06-11 (Step 6, superseded by Step 7 above)

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
