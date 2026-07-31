---
status: closed-phase
purpose: Phase-5 head — ig_bot Gates 1–5, 4 VETOs, sizing, decisions A–H, inherited contracts
read-when: working in phase5_execution/ — read this head + its newest Session-stopped block first
detail: L2
up: ../CLAUDE.md
down:
  - ./SESSIONS_ARCHIVE.md      # full session history (L3)
  - ./README.md
  - ../docs/concepts/phase5_concept.md   # full concept/plan snapshot (L3)
updated: 2026-07-17
---
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
  **⟳ 2026-06-23:** `.data` trägt jetzt zusätzlich `close_level`/`profit_loss`/`profit_currency`/
  `close_deal_reference` aus dem Close-Confirm (best-effort; `None` wenn der Confirm lagte) — die
  **lag-freie** P&L-Quelle für Phase 7. `monitor_position` reicht sie in `ExecutionResult` durch.
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

> 🔁 **Phase-6-Edit (2026-06-16, Decision A — additiv, Code = Source of Truth):** Phase 6
> (Modul 9) hat `executor.py` **additiv** um einen **keyword-only** `debate_runner:
> Callable[[dict], Any] | None = None` erweitert. Naht **zwischen Gate 2 und Gate 3** in
> `run()`: läuft ein Runner, wird sein Outcome **duck-typed** gelesen (`.decision`/`.direction`/
> `.rationale`) — **kein** P6-Import, Phasen-Isolation gewahrt; `ABSTAIN` → `NO_TRADE`, sonst
> wird `candidate["direction"]` in-memory (ggf. geflippt) gesetzt, alle Gates/VETOs/Sizing
> **unverändert**. **Default `None` ⇒ P5 bit-identisch + AI-frei** (alle 130 Bestands-Tests
> grün; +5 neue Naht-Regressionstests in `test_executor.py` → **135**). Das ist die in
> Decision A erlaubte „minimale P5-Edit" — die Debatte bekommt **nie** Broker/Gate/VETO
> (Decision J). Detail: `phase6_debate/` (Modul 9) + `docs/concepts/phase6_debate_concept.md`.

> 🔁 **Phase-7-Edit (2026-06-22, Decision A — additiv, Code = Source of Truth):** Phase 7
> (Reward, Step 10) hat `executor.py` **additiv** um einen **keyword-only** `reward_sink: Any |
> None = None` erweitert (`protocols.py`: neues duck-typed `RewardSink`-Protocol). Naht **um den
> place/monitor-Block**: nach `place_result.status == "OPEN"` (vor `monitor_position`)
> `on_trade_opened`, nach dem Monitor-Return `on_trade_closed` (nur bei `CLOSED_BY_BROKER`/
> `TIME_STOP`) — **beide guarded** (`try/except` → `logger.critical`, kein Re-raise). Der Sink ist
> **passiv**: er bekommt nur Snapshots, **nie** Broker-Write/Gate/VETO → kann strukturell keinen
> VETO umgehen (Decision J). `build_opened`/`build_closed` importieren `reward.models` **lazy** →
> P5-Modul-Imports bleiben `execution.* + stdlib`. **Default `None` ⇒ P5 bit-identisch + AI-frei**
> (135 → **142**, +7 Seam-Tests in `test_executor.py`; `FakeDB` um `get_current_score` ergänzt).
> Detail: `phase7_reward/` + `docs/concepts/phase7_reward_concept.md` §6 Step 10.

> 🔁 **Phase-7-Edit (2026-06-23, cross-phase — user-authorized "specific yes"):** **lag-freie
> P&L am Close.** `ExecutionResult` bekam **additiv** `close_level: float | None = None` +
> `profit_loss: float | None = None` (Defaults ⇒ alle Bestands-Konstruktionen bleiben gültig).
> `monitor.py` liest im **TIME_STOP**-Zweig `close_env.data` (`close_position` reicht jetzt den
> Close-Confirm durch, s. P1-Edit) und füllt die beiden Felder; `CLOSED_BY_BROKER` bleibt `None`
> (kein bot-eigener Close-Confirm → P7 fällt auf die History zurück). **Warum:** IG-Demo bucht
> `get_trade_history` erst nach Settlement (intraday 0 Zeilen) → der Reward braucht die realisierte
> P&L direkt aus dem Close-Confirm. `build_closed` (P7-Naht in `executor.py`) reicht beide Felder in
> den `ClosedTrade`. **Additiv, P5 bit-identisch** (Defaults); +4 Tests (`test_monitor.py` +2,
> `test_executor.py` +2 für `build_closed`) → **142 → 146**. Detail: `phase7_reward/` + Konzept §9.

> 🔁 **Phase-8 v1.5-hotfix edit (2026-07-01, Issue C — per-epic point_value in Gate-4 sizing, code = source
> of truth):** multi-instrument sizing must use each instrument's account-currency value of one point
> (`risk / (stop_pts × point_value)`). Because the **`Candidate`/`turbo_candidates.json` contract is frozen**
> and IG's `get_market_info` does **not** expose a point value, the seam is **P5-side**: `ExecutionConfig`
> gained `point_values: dict[epic→float]` (default `{}`) + `point_value_for(epic)` (→ 1.0 default = DAX/any
> unmapped epic). `sizing.compute_size(..., *, epic=None)` uses it (falls back to the market_info-echoed epic);
> `executor` passes the candidate epic and `build_opened(..., point_value=config.point_value_for(plan.epic))`
> so `initial_risk` matches. **Additive, default `{}` → every epic 1.0 → the DAX/default path is bit-identical**
> (P5 146 → **153**, +7 tests: 4 sizing, 2 config, 1 executor). This is **Gate-4 sizing, not a VETO** — the 4
> VETOs + 5 gates are untouched. ⚠ **Two SoTs by design**: this map ↔ P4 `InstrumentSpec.point_value` (the
> frozen cross-phase contract carries no point value); non-DAX values are **provisional** until the operator
> confirms them via `scripts/resolve_epics.py` (v1.5 Step 2B) — comment flags at both sites; re-baseline before
> live. Detail: `docs/concepts/phase8_v1.5_hotfix_plan.md` Step 2A.5 + `phase8_scheduler/CLAUDE.md`.

> 🔁 **Phase-8 v1.5-hotfix edit (2026-07-01, Issue A — lesson provenance, code = source of truth):**
> `build_opened` (`executor.py`) now stamps the trade's **lesson provenance** onto the `OpenedTrade` so
> the P4 research prompt can later exclude verification-trade lessons. **Why:** lessons from code-
> verification trades (seeded, sub-minute forced time-stops) pollute the single AI decision's input, and
> the literal seed marker `"MANUAL SEED (not a real research pick)"` (`scripts/seed_candidate.py:62`) is
> otherwise **never persisted** (only `llm_confidence` was). **What:** a **deterministic** check (no AI)
> — `provenance = "verification" if candidate.reasoning.startswith(_SEED_MARKER_PREFIX) else
> "autonomous"` (new module const, intra-phase coupling to the seed tool). It flows into the new
> `OpenedTrade.provenance` field (P7), which the P7 recorder writes into `market_context_json` at close.
> **Additive, `reward_sink=None` bit-identical** (`build_opened` only runs when a sink is wired). Gate-
> path/VETOs/sizing untouched; lessons gate nothing (root rule 3). +1 seam test (**153 → 154**). Detail:
> `docs/concepts/phase8_v1.5_hotfix_plan.md` Step 4.

> 🔁 **Phase-10 (V3) Block-A edit (2026-07-11, retroactive note — code = source of truth,
> missing from this file until now):** `executor.py` gained a keyword-only `abstain_sink: Any |
> None = None` (mirrors `reward_sink`'s DI pattern exactly). `_no_trade` moved from a
> `@staticmethod` to an instance method so it could reach `self.abstain_sink`; a new
> `_notify_no_trade` fires `abstain_sink.on_no_trade(cycle_outcome)` on **every** NO_TRADE
> return path (never on a trade path), guarded (`try/except` → `logger.critical`, Decision J).
> **Additive, `abstain_sink=None` bit-identical** (P5 154 → **161**, +7 seam tests). Detail:
> `phase10_v3/` + `docs/concepts/phase10_v3_plan.md` §7.2.

> 🔁 **Phase-10 (V3) Block-B edit (2026-07-17, code = source of truth):** `executor.py` gained a
> keyword-only `context_recorder: Any | None = None` (same DI pattern). Three call sites, not
> two: `_notify_opened` (TRADE), `_notify_no_trade`'s caller `_no_trade` (NO_TRADE — now returns
> the real abstain `record_id` for the FK link, see `abstain_lessons/sink.py`'s widened
> `on_no_trade -> str | None`), and — **a scope extension beyond the original plan, Nikinger-
> authorized** — the post-`place_order`/monitor `_abort` call site (`ABORT`, e.g. a broker-
> rejected order after a TRADE debate decision; this is exactly 2026-07-15's flagged incident,
> "BUY decision, no executed trade"). `_abort` moved from `@staticmethod` to an instance method
> (same reason `_no_trade` did in Block A) and only records when the caller passes a
> `candidate` — the earlier session-health/reconcile `_abort` call site (before Gate 1, no
> candidate exists yet) passes none, so it stays deliberately unrecorded. New shared
> `_notify_context` helper, guarded like every other seam (Decision J). **Additive,
> `context_recorder=None` bit-identical** (P5 161 → **167**, +6 seam tests). Detail:
> `phase10_v3/market_context/` + this session's `phase10_v3/CLAUDE.md` session block.

> 🔁 **Bug-B follow-up (2026-07-17, same-day follow-up session, code = source of truth):**
> the ABORT visibility landed above still didn't carry *why* it aborted — `_abort()`'s
> `_notify_context` call hardcoded `veto_results_json=json.dumps({"vetos": "pass"})`, dropping
> the actual `detail` string (which carries IG's own reject reason, from `order.py`'s
> `f"order {ref} REJECTED by broker: {reason}"`). Now folded in:
> `json.dumps({"vetos": "pass", "abort_detail": detail})` — no schema/migration change, reuses
> the existing `veto_results_json` TEXT column. **This closes the visibility gap for the *next*
> broker rejection — it does not recover 2026-07-15's actual reason**, which was only ever
> logged to stderr and is confirmed unrecoverably lost (no log file covers that date). One
> hypothesis flagged to the Nikinger, unconfirmed: the rejected order was on **AEX**, not DAX —
> `ExecutionConfig.stop_distance_points`/`limit_distance_points` are fixed constants applied to
> every epic, and the existing v1.5-hotfix note above already flags non-DAX `point_values` as
> provisional; the same DAX-calibration risk plausibly extends to stop/limit distances. P5 167
> unchanged (extended the existing Bug-B seam test rather than adding a new one). Detail:
> `phase10_v3/CLAUDE.md` → this session's `## Session stopped` block.

> ✅⚠ **Bug-B AUFGELÖST + zwei Sizing-Befunde (2026-07-31, Phase-10-Datenwoche-2-Review,
> weekday read-only — volle Beweise: `phase10_v3/DATA_WEEK_REVIEW_2026-07-31.md` §4 B1/B3):**
> - **Der 2026-07-15-AEX-Reject ist erklärt** — die Hypothese im Block direkt darüber zeigte auf
>   das richtige Instrument, aber die falsche Konstante: **nicht** die Stop-Distanz, sondern
>   `point_value`. `phase8_scheduler/scripts/wiring.py:616` baut `point_values` aus der statischen
>   4-Epic-`EXTENDED_UNIVERSE`, während Research die 8-Epic-DB-Universe (V2) handelt → AEX fällt
>   auf `point_value_for()`s Default **1.0** zurück statt der live-aufgelösten **40.0**
>   (`instrument_universe.point_value_source='ig_fields'`, „Niederlande 25 Kassa (40€)") →
>   **40× Oversizing**. **Alle drei** je platzierten AEX-Orders (07-15, 07-20, 07-30) wurden mit
>   `INSUFFICIENT_FUNDS` abgelehnt; die 07-30-Order hätte am 30-Punkte-Stop **120 % des Kontos**
>   riskiert. **Fix-Teil hier in P5:** `ExecutionConfig.point_value_for()` (`execution/config.py:156`)
>   darf für ein unbekanntes Epic **nicht still `1.0`** liefern, sondern muss fail-closed sein —
>   sonst ist das nächste von V2 promotete Epic wieder still auf 1.0. (Der Map-Quellen-Fix liegt in
>   P8.) **Merkposten:** genau dieses Risiko stand seit v1.5 als Doku-Notiz in diesem File
>   („non-DAX point_values provisional, re-baseline before live") — eine Doku-Notiz hat es nicht
>   verhindert.
> - **`max_leverage = 20.0` lässt null Margin-Headroom** (`execution/config.py:114`,
>   `sizing.py:65`): `cap_size` pinnt die Nominale konstruktionsbedingt auf **exakt**
>   `available × 20`, und auf DAX ist dieser Cap bei **jedem** Trade bindend (das Risikomodell
>   verlangt bei 30-Punkte-Stop und 3 % Risiko rechnerisch ~25× Hebel). Der Bot fragt die
>   tatsächliche Margin-Anforderung nie ab. Empirisch am 2026-07-20, selbes Epic, selber Vormittag:
>   Size **22,1 → REJECTED**, Size **22,0 → ACCEPTED**. Nebenwirkung: eine zweite parallele
>   Position (`max_parallel`) ist so nie finanzierbar. Braucht eine Designentscheidung
>   (Headroom im Cap **oder** echte Margin-Abfrage vor der Order) → Phase-11-Scope.
> Nichts davon angewendet: Wochentags-Regel (read-only), und P5 ist nicht die aktive Phase.

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

## Session stopped — 2026-06-12 (Step 11 — Doku-Abschluss + Repo-weiter Phase-5-Flip)

### Stand
**Step 11 erledigt — Phase 5 ist DOKU-vollständig abgeschlossen.** Die Live-Gate-Verifikation
(Block direkt unten) ist die fachliche Wahrheit; Step 11 bringt nur die Doku in Deckung. Keine
Produktiv-Code-Änderung (Code ist done + live bewiesen). `pytest phase5_execution/tests -q` →
**130 passed** (unverändert — die Doku-Edits berühren keinen Code-Pfad). Committet auf
`phase5-execution` als ein atomarer Commit (`phase5: Step 11 docs + repo-wide phase-5 flip`).
**Merge → `main` bleibt die Operator-Entscheidung** (Zeitpunkt/PR).

### Zuletzt gemacht (Step 11)
- **`README.md` (Phase 5)** — der stale „Status: in progress … modules are not built yet"-Banner
  war schlicht falsch → auf ✅ code-complete + live-verifiziert (Demo) geflippt, mit dem
  live-verified≠profit-validated-Caveat (gleiche Disziplin wie Phase 4). **Run-Sektion korrigiert:**
  der CLI-Entry ist `python -m execution.ig_bot` (lief vorher fälschlich als
  `python phase5_execution/ig_bot.py`); `--dry`/`--yes`/`--epic` dokumentiert; Operator-Live-Gate
  als Reihenfolge `seed_candidate.py --direction SELL` → `smoke_test.py` → `live_test.py`
  (TTL-30-min-Hinweis, Richtung = aktueller `get_ohlcv`-net-return für VETO 3, Fenster
  09:00–17:30 Europe/Berlin). stdout=JSON / stderr=Logs + `dev_install.sh`-Setup beibehalten.
- **`requirements.txt` (Phase 5)** — geprüft, **unverändert korrekt** (keine neuen Runtime-Deps;
  nur `pytest`; Runtime über die editable installs der Schwester-Pakete).
- **Top-Level `../CLAUDE.md` „Current state"** — Active phase Phase 4 → **Phase 5 ✅ abgeschlossen
  + live-verifiziert**; Phase-5-Status-Block ergänzt (130 Tests; live SELL open→Time-Stop-close
  2026-06-12; `currencyCode`-Fix; Risk-per-Trade-Sizing; live-verified≠profit-validated;
  Phase-6-Konzept in der Browser-Session).
- **Root `../README.md`** — Status-Tabelle Phase 5 „Nicht begonnen" → ✅ Abgeschlossen
  (live-verifiziert, Demo) + Fußnote mit dem live-verified≠profit-Caveat.
- **`../ROADMAP.md`** — Phase-5-Checkboxen gehakt + „Done when … ✅ 130 unit tests +
  live-verified via `live_test.py` (real open→time-stop-close, IG Demo) — 2026-06-12"
  (Muster wie Phase 2).
- **Keine Konzept-Annotation** — Step 11 ist reine Doku, keine Design-Entscheidung geändert.

### Nächster Schritt
- **Operator:** Merge `phase5-execution` → `main` (Zeitpunkt/PR nach Wahl).
- **Phase 6** (Bull/Bear/Judge) — Konzept/Transition passiert in der **Browser-Session**, nicht
  hier. Carry-over bleibt: `risk_pct`/Stop-Limit/Momentum-Threshold/`max_leverage` sind **v1**
  (am Profit zu tunen, Phase 7); SL/TP-Level-Richtung BUY ist live nur implizit (über SELL)
  bestätigt — expliziter BUY-Live-Check nice-to-have, nicht blockierend.

### Offene Punkte / blockers
- Keine. Phase 5 ist code-complete, live-verifiziert (4/4) und doku-konsistent. Profitabilität
  ist bewusst out-of-scope (Phase 7 + Live-Betrieb).

---


> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
