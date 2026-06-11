# Phase 5 — Implementierungsplan für Claude Code

> **Status:** Architektur geklärt (8 Entscheidungen A–H unten gelockt), Contracts gegen
> das echte Repo-Code (Phase 1–4) verifiziert über das Phase-5-Kickoff-Handover.
> Dieser Plan ist der erste **Execution-Pfad** des Bots — hier wird zum ersten Mal eine
> (Demo-)Order platziert. Korrektheit der Gates/VETOs wiegt schwerer als Feature-Umfang.
>
> **Quelle der Wahrheit bleibt das Repo.** Wo dieser Plan eine Signatur nennt, ist sie
> aus dem Handover gegen `ig_adapter.py` / `filters.py` / `persistence` / `credentials.py`
> verifiziert. Jede mit **[VERIFY]** markierte Stelle ist **vor** dem Bauen gegen den
> echten Code zu prüfen (z. B. die genaue `.data`-Form von `get_ohlcv`).
>
> **Keine AI in Phase 5.** Gates, VETOs, Sizing, Order, Monitoring, Reconcile sind
> **deterministischer Code**. Die einzige AI bleibt der eine Phase-4-Research-Call (über
> Gate 2 ausgelöst). Bull/Bear/Judge ist Phase 6. → Kein `token_meter` in Phase 5.

---

## 0. Geklärte Architektur-Entscheidungen (gelockt)

| # | Thema | Festlegung | Begründung |
|---|---|---|---|
| **A** | Step 0 / Gate 5 | `pre_trade_option_check()` → **`pre_trade_check()`**. Gate 5 ist **kein „Fix"**, sondern ein dünner **Direction-Konsistenzcheck** (`direction ∈ {BUY,SELL}` + keine offene Gegen-Position auf demselben Epic). | Richtung kommt fertig + geclampt aus Phase 4. „Direction Fix"/FLIP ist Options-Erbe. Ehrlicher Name; das 5-Gate-Modell bleibt; Phase 6 (Debatte überschreibt Richtung) bekommt eine saubere Hand-off-Naht. |
| **B** | VETO-Set | **Genau 4, alle HART** (= Abbruch, kein Trade), alle auf **frischem** Snapshot unmittelbar vor Order: (1) Status/Zeit, (2) Spread, (3) **Momentum aus `get_ohlcv`**, (4) Position/Constraint. | 6a nicht verhandelbar: Momentum **nur** aus IG-Echtzeit-Bars, nie Phase 3. Weiche Warnungen, die auf dem ersten Execution-Pfad trotzdem traden, **sind** das Force-Trigger-Anti-Pattern. Gates = Eignung, VETOs = Last-Millisecond-Realitätscheck auf frischen Daten. |
| **C** | Composition Root | **Editable installs** (`pip install -e` pro Package, je ein minimales `pyproject.toml`). | `ig_bot.py` ist der erste echte Composition Root; Phase 8 läuft das als Daemon. `sys.path`-Hacks sind für einen langlebigen Scheduler + saubere `pytest`-Collection fragil. Das Handover hat das **bewusst hierher** vertagt. |
| **D** | Human-Confirm | Phase 5 bleibt **Demo**. Confirm-Gate vor `open_position` **default AN** (`require_confirm=True`); Override `--yes` für spätere Automatik. | Baut den Code-Pfad, den Live zwingend braucht, jetzt statt in P8 anzuflanschen. „Defense against runtime AI agency" ist architektonisch. |
| **E** | Idempotenz | Eigene `deal_reference` (`bot-{uuid4hex}`) **write-ahead** persistieren **vor** `open_position`. **Reconcile-on-Startup** jeden Lauf. `PENDING` → **kein** Retry-Order, bounded Re-Check, sonst **fail-closed** + Operator-Hinweis. | Echtes Geld-Risiko. Doppel-Order-Schutz > Komfort. Nie blind eine zweite Order. |
| **F** | Sizing (Gate 4) | `risk_pct` aus `load_bot_config()`, **score-gekoppelt** via `get_risk_level()`. `calc_position_size(point_value=1.0)`, ab auf 0.1. **Gerundete Size < `min_deal_size` → kein Trade.** | Nutzt vorhandene P1/P2-Hebel, kein neues System. |
| **G** | SL/TP | **Beim Entry** (`stop_level`/`limit_level`). v1: **feste Punkte aus Config**. ATR als dokumentierter späterer Swap (kann die VETO-Bars wiederverwenden). | Risiko vor dem Monitoring definiert; überlebt Monitor-Crash broker-seitig. Feste Punkte = kleinste stille Fehlerfläche. |
| **H** | Monitoring/Close | **Polling** (`get_open_positions`/`get_price`). Close-Trigger: (a) Position weg (broker-seitiges SL/TP gefüllt), (b) **Time-Stop** (Square-off + `max_hold`). Lightstreamer (PRICE-Sub) erst P8. | Robust, kein Stream-Lifecycle bei manuellem Trigger. |

### Config-Defaults (v1 — werden am echten Profit getunt, nicht jetzt)

| Feld | Default | Bezug |
|---|---|---|
| `trading_window_start` / `trading_window_end` | `09:00` / `17:30` (Europe/Berlin) | Gate 1, **konfigurierbar** |
| `square_off_time` | `17:15` (Europe/Berlin) | Monitor Time-Stop |
| `max_hold_minutes` | `240` (4 h) | Monitor Time-Stop |
| `max_spread_pct` | `0.5` (**% of ask**, nicht Punkte) — wie Phase-4 `ResearchConfig.max_spread_pct` | VETO 2 |
| `momentum_resolution` / `momentum_count` | `MINUTE_5` / `12` (≈1 h) | VETO 3 |
| `momentum_veto_threshold_pct` | `0.15` | VETO 3 |
| `risk_pct_conservative` / `risk_pct_aggressive` | `0.5` / `1.0` (**Prozent**) | Gate 4, Wahl via `get_risk_level()` |
| `stop_distance_points` / `limit_distance_points` | `30` / `45` (1.5R) | SL/TP |
| `poll_interval_s` | `15` | Monitor |
| `require_confirm` | `True` | Human-Confirm |
| `reconcile_unexpected_aborts` | `True` | Reconcile fail-closed |

> **Annotation 2026-06-10 (Code = Source of Truth, [VERIFY] aufgelöst gegen `ig_adapter.py`/
> `filters.py`):**
> - **`max_spread_pct`**: das `~1.8 pts` war falsch geraten. `Price.spread_pct` (aus
>   `calc_spread_pct`) ist eine **Prozentzahl** (`(ask-bid)/ask*100`); Phase-4
>   `ResearchConfig.max_spread_pct = 0.5`. Phase-5-Default daher **`0.5` (%)** — VETO 2
>   vergleicht `price.spread_pct ≤ 0.5`.
> - **`risk_pct` Einheiten**: `calc_position_size(..., risk_pct=...)` behandelt `risk_pct`
>   als **Bruchteil** (`notional = balance × risk_pct`). Die Config-Werte sind als **Prozent**
>   gemeint (Operator-Entscheidung 2026-06-10) → `sizing.py` übergibt `risk_pct/100`
>   (`0.5` → 0.5 % Notional). Inline in `sizing.py` dokumentieren.
> - **`get_ohlcv(...).data`** = `{"bars":[...], "allowance":{...}}`; je Bar
>   `{timestamp, open, high, low, close, volume}` (Mid aus bid/ask). VETO 3 liest **`close`**.
> - **`open_position` `stop_level`/`limit_level`** = **absolute Preis-Level** (nicht Distanzen);
>   `build_order_plan` rechnet die Punkt-Distanzen relativ zum Entry-Preis in absolute Level um.
>   `OrderResult.data.status ∈ {ACCEPTED, REJECTED, PENDING, UNKNOWN}` (ACCEPTED = bestätigt,
>   PENDING = Confirm-Timeout → fail-closed).
>
> **Annotation 2026-06-10 (Step 1 — neues Config-Feld):** `ExecutionConfig.max_parallel_positions`
> (Default **1**) steht **nicht** in der obigen Defaults-Tabelle, wird aber von Gate 3 und VETO 4
> gebraucht („offene Positionen < max_parallel"). Default 1 = DAX-Intraday, eine Position; **v1**,
> am Profit zu tunen. PENDING-Recheck-Tunables (`order.py`, Step 6) kommen erst, wenn sie konsumiert
> werden.

---

## Step 0 — Legacy-Terminologie bereinigen (eigener Commit, VOR jeder Logik)

Gleiche Klasse von Altlasten wie der `CALL/PUT`-Bug in Phase 4 — **kein** Kosmetik-Problem.

**Aufgaben (ein sauberer Commit, keine Execution-Logik):**

1. **`pre_trade_option_check()` → `pre_trade_check()`** überall, wo der Name aus dem
   Referenzbot stammt. „option" suggeriert ein Instrument, das es nicht gibt — wir handeln
   **DAX-CFDs**.
2. **Gate 5 ehrlich machen:** kein „Direction Fix"/FLIP. Im CFD-Modell ist `direction`
   bereits `BUY`/`SELL` (Long-Bias-Clamp ist in Phase 4 passiert). Gate 5 = reiner
   **Direction-Konsistenzcheck** (siehe Modul 5). Name im Code/Doku: `gate_direction_consistency`.
3. **Options-Semantik aus jedem VETO-/Gate-Entwurf verbannen:** kein `strike`, `otm`,
   `issuer`, `expiry`, `CALL`/`PUT`, `FLIP`. Die 4 VETOs sind für einen CFD neu gefasst
   (Modul 4), **nicht** aus dem Referenzbot kopiert.
4. **`turbo_candidates.json` als Name einfrieren** — Phase-2/4-Contract, Gate 2 erwartet
   ihn. Kommentar: *„legacy name; Inhalt = DAX-CFD-Kandidaten, keine Turbos."* **Nicht** umbenennen.
5. **Doku-Korrektur:** falls die Root-`CLAUDE.md`/ROADMAP an Phase 5 noch „option_check" /
   „Direction Fix (FLIP)" trägt → auf CFD-Wording ziehen.

**Done when:** `grep -rin "option_check\|\bCALL\b\|\bPUT\b\|strike\|otm\|issuer\|FLIP" phase5_execution/ --include=*.py`
liefert keine instrumenten-/options-bezogenen Treffer mehr. Eigener Commit.

---

## Step C — Composition Root: editable installs (eigener Commit, früh)

Erst hierdurch lösen alle vier Phasen + Phase 5 sauber zur Laufzeit auf — danach
funktionieren `pytest` und `ig_bot.py` ohne `sys.path`-Hack.

**Aufgaben:**

1. **Je ein minimales `pyproject.toml`** an jedes Package, das noch keins hat
   (`broker_wrapper`, `persistence`, `external_data`, `phase4_research`/`research`,
   `phase5_execution`). **[VERIFY]** den **echten Top-Level-Importnamen** jedes Packages
   (z. B. `import broker_wrapper`) und trag ihn korrekt ein — nicht raten.
   ```toml
   [build-system]
   requires = ["setuptools>=68"]
   build-backend = "setuptools.build_meta"

   [project]
   name = "<package-name>"
   version = "0.1.0"
   requires-python = ">=3.11"
   # dependencies bleiben in der jeweiligen requirements.txt (dev), hier nur das Nötigste
   ```
2. **Dev-Install-Skript** `scripts/dev_install.sh` (repo-root): `pip install -e` für jedes
   Package in Abhängigkeitsreihenfolge (P1 → P2 → P3 → P4 → P5).
3. **`sys.path`-Bootstrap entfernen**, sobald `pytest` + `wiring.py` ohne ihn grün sind.
   Falls ein Sibling-Package ein Problem macht → **[VERIFY]** und melden, **nicht**
   den Hack heimlich wieder einbauen.

> **Phase-Isolation bleibt:** editable installs ändern nur das *Packaging*, **nicht** die
> Code-Abhängigkeiten. Kernlogik importiert Schwester-Packages weiterhin **nur** über
> definierte Contracts; Collaborators via `typing.Protocol`; cross-phase nur lazy in der
> Wiring-/Gate-2-Schicht.

**Done when:** frische venv → `bash scripts/dev_install.sh` → `pytest phase5_execution/tests -v`
grün **ohne** `sys.path`-Manipulation.

---

## Verifizierte geerbte Contracts (aus dem Handover, Repo = Wahrheit)

### Phase 1 — `broker_wrapper` (immer `env.ok` vor `env.data`)
- **Session:** `connect()` · `is_connected() -> bool` · `get_account() -> Envelope`
  (`.data`: `balance, available, profit_loss, currency`).
- **Markt:** `get_price(epic)` (`.data`: `bid, ask, spread, spread_pct, market_status,
  timestamp`) · `get_market_info(epic)` (`.data`: `min_deal_size, currency,
  instrument_type, market_status`).
- **`get_ohlcv(epic, resolution, count)`** — IG-Echtzeit-Bars. `resolution ∈
  VALID_RESOLUTIONS` (`MINUTE, MINUTE_5, MINUTE_15, …`), `count ∈ (0,1000]`. **Quelle des
  Momentum-VETO.** **[VERIFY]** die exakte `.data`-Form (Candle-Liste, Feldnamen
  `open/high/low/close` bzw. bid/ask-OHLC).
- **Orders:** `open_position(epic, direction, size, order_type="MARKET", *, level,
  stop_level, limit_level, deal_reference, currency)` — **`direction ∈ ("BUY","SELL")`
  Pflicht**, `size > 0`, LIMIT/STOP brauchen `level`. Gibt `OrderResult` (pollt `/confirms`;
  Timeout → `dealStatus="PENDING"`). `close_position(deal_id)` ·
  `modify_position(deal_id, *, stop_level, limit_level)` ·
  `reconcile_positions(expected_references=None)` (→ `present/missing/unexpected`) ·
  `get_open_positions()` (**`.data = {"positions":[...]}`** — kein nackter Array!).
- **Filter:** `is_tradeable(price, market_info, FilterConfig)` (nimmt **Objekte**, nicht
  `env.data`-Dicts) · `calc_spread_pct(bid, ask)` · `calc_position_size(*,
  available_balance, risk_pct, price, point_value=1.0, cap=None)` → rundet **ab** auf 0.1.
- **Envelope:** `.ok` (bool) · `.data` · `.error = {code, message, retryable}`.

### Phase 2 — `persistence`
- `Database.get_recent_trades(8)` · `get_recent_lessons(5)` · `get_current_score()` ·
  `get_risk_level()` · `mark_lesson_used(id)`. **Outcome-Schreiben = Phase 7, NICHT hier.**
- `StateManager.save_candidates/load_candidates/candidates_are_fresh/clear_candidates`
  (TTL 30 min, self-clearing) · `is_account_state_fresh()` · `load_account_state()` ·
  `load_bot_config()`.

### Phase 4 — Candidate-Contract (eingefroren, von Gate 2 konsumiert)
`data/state/turbo_candidates.json`, pro Pick: `epic, direction("BUY"|"SELL"),
llm_confidence(advisory), reasoning, spread_pct_at_pick, drift_at_pick|None,
score_at_pick, threshold_applied, generated_at(ISO-UTC), source("research")`.
**Abstain/Reject → leere Liste.** `direction` ist **direkt** order-tauglich.
Research-Aufruf bei fehlend/stale: `build_research(config).run()` (lazy import in Wiring).

### Credentials
`from broker_wrapper.credentials import get_credential` (Keyring `SERVICE_NAME="tradingbot"`).
IG-Demo-Keys bereits geseedet.

---

## Modul-Plan (TDD-geordnet — pro Modul Tests zuerst, dann grün, dann Commit)

Verzeichnis **neu**: `phase5_execution/`. Struktur:

> **Annotation 2026-06-10 (Step C umgesetzt — Paket-Layout):** Der unten gezeigte *flache*
> Baum ist schematisch. Realisiert wird die **etablierte Repo-Konvention**: das importierbare
> Paket heißt **`execution`** und liegt **genestet** unter dem Projekt-Verzeichnis als
> `phase5_execution/execution/` (genau wie `phase4_research/research/`,
> `phase3_external_data/external_data/`). `pyproject.toml`/`requirements.txt`/`README.md`/
> `CLAUDE.md`/`tests/`/`scripts/` liegen auf der Projekt-Ebene `phase5_execution/`. Grund:
> ein flaches Layout mit `pyproject.toml` **im** Paketverzeichnis ist für setuptools-
> Package-Discovery fragil; die `[tool.setuptools.packages.find] include = ["execution*"]`
> Form bleibt sauber. Imports im Code/Tests daher `from execution.<modul> import …`.
> Editable-Install-Reihenfolge in `scripts/dev_install.sh` (Repo-Root): P1→P2→P3→P4→P5.

```
phase5_execution/
├── pyproject.toml            # Step C
├── requirements.txt
├── README.md
├── CLAUDE.md                 # inkl. ## Session stopped (Pflicht)
├── __init__.py
├── config.py                 # ExecutionConfig (alle Tunables aus §0)
├── exceptions.py             # typisierte Fehler
├── protocols.py              # Broker/Db/State als typing.Protocol
├── models.py                 # OrderPlan, GateVerdict, VetoVerdict, ExecutionResult
├── execution_state.py        # Write-ahead-Refs + offene Positionen (eigene JSON-Datei)
├── gates.py                  # Gate 1/2/3/5
├── sizing.py                 # Gate 4
├── vetos.py                  # pre_trade_check() = 4 VETOs (Momentum aus get_ohlcv)
├── order.py                  # place_order: write-ahead, confirm/PENDING, fail-closed
├── monitor.py                # Polling-Loop + Time-Stop + close
├── executor.py               # Orchestrator: Gates → VETOs → confirm → place → monitor
├── ig_bot.py                 # CLI-Entry (--yes, --epic, --dry), baut via wiring, ruft Executor
├── scripts/
│   ├── wiring.py             # baut ECHTE Instanzen (editable imports), build_executor()
│   ├── smoke_test.py         # read-only: Gates+VETOs DRY, KEINE Order
│   └── live_test.py          # voller open+close-Zyklus gegen IG Demo (Operator führt aus)
└── tests/
    ├── test_execution_state.py
    ├── test_gates.py
    ├── test_sizing.py
    ├── test_vetos.py
    ├── test_order.py
    ├── test_monitor.py
    └── test_executor.py      # voller Flow, FakeBroker
```

### 1. `config.py` · `exceptions.py` · `protocols.py` · `models.py`
- `ExecutionConfig` (`@dataclass(frozen=True)`): alle Felder aus der Defaults-Tabelle §0,
  `from __future__ import annotations`, Type-Hints.
- `exceptions.py`: `ExecutionError` (Basis) → `GateRejected`, `VetoRejected`,
  `ExecutionAbort` (fail-closed, Operator), `ReconcileConflict`. Nie still schlucken.
- `protocols.py`: `BrokerProtocol`, `DbProtocol`, `StateProtocol` (nur die oben
  verifizierten Methoden) — **keine harten Imports** der Schwester-Packages in der Kernlogik.
- `models.py` (Dataclasses):
  ```python
  @dataclass(frozen=True)
  class OrderPlan:
      epic: str
      direction: str            # "BUY"|"SELL"
      size: float
      stop_level: float
      limit_level: float
      deal_reference: str
  @dataclass(frozen=True)
  class GateVerdict:  ok: bool; gate: str; reason: str
  @dataclass(frozen=True)
  class VetoVerdict:  ok: bool; veto: str; reason: str
  @dataclass(frozen=True)
  class ExecutionResult: status: str; deal_id: str | None; plan: OrderPlan | None; detail: str
  ```
- Tests: Config-Defaults korrekt; Verdicts immutabel.

### 2. `execution_state.py` + Tests — Write-ahead-Idempotenz (eigene JSON-Datei)
> **Geerbte Lücke, hier aufgelöst:** `StateManager` hat dafür keinen Contract; `Database`
> ist Phase 7. Phase 5 besitzt eine **eigene** Datei `data/state/execution_state.json` —
> reine operative State (in-flight/offene Refs), **kein** Lern-/Outcome-Datum.

```python
class ExecutionState:
    def __init__(self, path: str = "data/state/execution_state.json") -> None: ...
    def record_pending(self, plan: OrderPlan) -> None:        # write-ahead, VOR open_position
    def mark_open(self, deal_reference: str, deal_id: str) -> None:
    def mark_closed(self, deal_reference: str) -> None:
    def open_references(self) -> list[str]:                    # für reconcile-on-startup
    def get(self, deal_reference: str) -> dict | None:
```
- Atomar schreiben (temp-file + `os.replace`), bei korrupter Datei klar fehlschlagen
  (`ExecutionError`), nie still überschreiben.
- Tests (≥6): write-ahead persistiert vor „Order"; `mark_open/closed` Status-Übergänge;
  `open_references()` listet pending+open; korrupte Datei → Exception; atomic-write
  hinterlässt keine halbe Datei.

> **Annotation 2026-06-10 (Step 2 umgesetzt — Code = Source of Truth):**
> - **Datei-Form:** `{"records": {<deal_reference>: {…}}}` — ein Dict, gekeyt auf die
>   (uuid-eindeutige) `deal_reference`. Pro Record: `deal_reference, epic, direction,
>   size, stop_level, limit_level, status, deal_id, recorded_at, updated_at`.
> - **Record-Status-Vokabular** = `PENDING → OPEN → CLOSED` (bewusst **getrennt** vom
>   `ExecutionResult.status` aus `models.py`; das ist der persistierte Order-Lifecycle,
>   nicht das Cycle-Ergebnis). `open_references()` = Refs in `{PENDING, OPEN}`.
> - **Unbekannte Ref bei `mark_open`/`mark_closed` → `ExecutionError`** (nie still
>   anlegen/überschreiben — signalisiert einen Logikfehler; konsistent mit „nie still
>   überschreiben" für die korrupte Datei).
> - **Atomic-Write + ISO-Stamp** spiegeln die verifizierte Phase-2-`persistence.state`-
>   Konvention (temp + `os.replace`; `_format_iso`/`_utcnow` lokal, **kein** Cross-Phase-
>   Import → Phasen-Isolation bleibt).
> - 10 Tests (≥6) grün; `pytest phase5_execution/tests -v` → **33 passed** (23 + 10).
>   **Neu:** `tests/conftest.py` mit `make_order_plan`/`order_plan`-Factory.

### 3. `gates.py` + Tests — Gate 1/2/3/5 (reine, testbare Funktionen)
```python
def gate_time_window(now: datetime, config) -> GateVerdict:
    """Gate 1: now ∈ [trading_window_start, trading_window_end] in config.tz."""
def gate_load_candidates(state, research_runner, config) -> tuple[GateVerdict, dict | None]:
    """Gate 2: load_candidates()+candidates_are_fresh(); stale/leer → research_runner()
    aufrufen (lazy, injiziert), neu laden. Leere Liste → Abstain (kein Trade)."""
def gate_constraints(account_env, open_positions_env, candidate, config) -> GateVerdict:
    """Gate 3: available-Budget > 0; offene Positionen < max_parallel; kein Constraint-Bruch."""
def gate_direction_consistency(candidate, open_positions_env) -> GateVerdict:
    """Gate 5 (ehemals 'Direction Fix'): direction ∈ {BUY,SELL}; keine offene
    Gegen-Position auf demselben Epic. Pass-Through-Konsistenz, KEIN Fix/FLIP."""
```
- `research_runner: Callable[[], list[dict]]` wird injiziert (Wiring liefert
  `lambda: build_research(cfg).run()`), damit Gate 2 testbar bleibt und Phase 4 lazy bleibt.
- Tests (≥8): Gate1 innerhalb/außerhalb Fenster (inkl. tz); Gate1 konfigurierbares Fenster;
  Gate2 frische Candidates → pass; Gate2 stale → ruft Runner → neu geladen; Gate2 leer →
  Abstain; Gate3 kein Budget → reject; Gate5 ungültige Richtung → reject; Gate5 offene
  Gegen-Position → reject.

> **Annotation 2026-06-10 (Step 3 umgesetzt — Code = Source of Truth):**
> - **Gate 1 tz:** `now` wird nach `ZoneInfo(config.tz)` konvertiert (`astimezone` wenn
>   tz-aware, sonst als bereits-in-Zone angenommen); Vergleich auf **Time-of-Day**,
>   inklusive Grenzen `start ≤ t ≤ end`. Lokaler `_parse_hhmm`-Helper.
> - **Gate 2** liefert den **ersten** Candidate (Phase 4 persistiert ≤1). Reihenfolge:
>   `candidates_are_fresh()` → bei stale `research_runner()` rufen → `load_candidates()`
>   neu lesen (persistierte Datei = Single Source). Leer → Abstain (`ok=False, None`).
> - **Gate 3 budget** liest `available` aus `get_account().data` (verifiziert gegen
>   `ig_adapter.py:520` / `models.py:65`), Schwelle `available ≤ 0 → reject`. Positionen aus
>   `get_open_positions().data["positions"]` (`{"positions":[…]}`, nie nackt). **Env-nicht-ok
>   → reject** (fail-safe: Eignung nicht verifizierbar = nicht eignungsfähig) — bewusst
>   getrennt vom VETO (Step 5, frischer Snapshot).
> - **Gate 5** blockt **nur** eine offene **Gegen**-Position auf **demselben** Epic; gleiche
>   Richtung / anderes Epic blockt hier nicht (Parallel-Count = Gate 3 / VETO 4). Env-nicht-ok
>   → reject. Kein Fix/FLIP.
> - Gate-IDs: `"time_window"`/`"load_candidates"`/`"constraints"`/`"direction_consistency"`.
> - 15 Tests (≥8) grün; `pytest phase5_execution/tests -v` → **48 passed** (33 + 15).
>   `conftest.py` gewachsen um `_FakeEnv`, `make_candidate`-Factory, `FakeState`.

### 4. `sizing.py` + Tests — Gate 4
```python
def select_risk_pct(db, config) -> float:
    """get_risk_level(): KONSERVATIV → risk_pct_conservative, AGGRESSIV → ...aggressive."""
def compute_size(account_env, price_env, market_info_env, risk_pct, config) -> tuple[float, str | None]:
    """calc_position_size(available_balance=..., risk_pct=..., price=ask, point_value=1.0),
    ab auf 0.1. Wenn Ergebnis < market_info.min_deal_size → (0.0, 'below_min_deal_size')."""
```
- Size < `min_deal_size` → **kein Trade** (Executor bricht sauber ab, kein Clamp nach oben).
- Tests (≥5): konservativer vs aggressiver risk_pct via mock `get_risk_level`; Rundung ab
  auf 0.1; Size unter min → `(0.0, reason)`; `available`-Lesepfad korrekt; 0-Balance → kein Trade.

> **Annotation 2026-06-11 (Step 4 umgesetzt — Code = Source of Truth):**
> - **Phasen-Isolation gehalten (Operator-Entscheidung):** `compute_size` importiert
>   **nicht** `broker_wrapper.filters.calc_position_size`, sondern spiegelt dessen
>   verifizierte Arithmetik lokal in `_round_down_size` (`int(raw * 10) / 10.0`,
>   `notional = balance × risk_pct`, `0.0` bei nicht-positiver Balance/Preis) — gleiche
>   Disziplin wie `gates.py`/`execution_state.py` (Schwester-Imports nur lazy in der
>   Wiring-Schicht). Bewusste Kopplung: ändert sich die Phase-1-Formel, muss dieser Helper
>   nachziehen (Hinweis im Docstring).
> - **`risk_pct`-Einheiten:** Config-Werte sind **Prozent**; `compute_size` übergibt
>   `risk_pct / 100` (Bruchteil) an die Arithmetik — wie §0-Annotation festgelegt.
> - **Reason-Vokabular (no-trade Codes):** `account_snapshot_unavailable` /
>   `price_snapshot_unavailable` / `market_info_snapshot_unavailable` (env nicht ok,
>   fail-safe) und `below_min_deal_size`. **0-Balance** liefert size `0.0` → fällt unter
>   `min_deal_size` → ebenfalls `below_min_deal_size` (ein klarer Code, kein separater
>   `zero_size`).
> - **Lesepfade** (gegen `ig_adapter.py` `.to_dict()` geprüft): `available` aus
>   `get_account().data`, `ask` aus `get_price().data`, `min_deal_size` aus
>   `get_market_info().data`. `env.ok` immer vor `env.data`.
> - 11 Tests (≥5) grün; `pytest phase5_execution/tests -v` → **59 passed** (48 + 11).
>   `conftest.py` gewachsen um `FakeDB` (`get_risk_level`).

### 5. `vetos.py` + Tests — `pre_trade_check()` = die 4 HARTEN VETOs
**Alle auf FRISCHEM Snapshot unmittelbar vor der Order. Erster Fail = Abbruch.**
```python
def veto_status_and_window(price_env, now, config) -> VetoVerdict:     # VETO 1
    """market_status == 'TRADEABLE' (frischer get_price) UND now im Fenster."""
def veto_spread(price_env, config) -> VetoVerdict:                     # VETO 2
    """price.spread_pct ≤ config.max_spread_pct (frisch, nicht spread_at_pick)."""
def veto_momentum(broker, epic, direction, config) -> VetoVerdict:    # VETO 3 (★ get_ohlcv)
    """get_ohlcv(epic, config.momentum_resolution, config.momentum_count).
    net_return = (close_last - close_first)/close_first.
    BUY  & net_return <= -threshold  → VETO (in scharfen Abwärts-Move kaufen).
    SELL & net_return >= +threshold  → VETO (in scharfen Aufwärts-Move verkaufen).
    Datenfehler/zu wenige Bars → VETO (fail-closed). NIEMALS Phase-3-get_momentum()."""
def veto_position_conflict(open_positions_env, candidate, config) -> VetoVerdict:  # VETO 4
    """Frischer get_open_positions: keine offene Gegen-Position; max_parallel nicht erreicht."""

def pre_trade_check(broker, candidate, now, config) -> VetoVerdict:
    """Ruft alle 4 frisch (eigene get_price/get_ohlcv/get_open_positions). Erstes
    VetoVerdict mit ok=False zurück; sonst ok=True. KEIN LLM, keine verzögerten Daten."""
```
- **[VERIFY]** Close-Feldname aus `get_ohlcv.data` (Modul 4 momentum) — Bar-Shape erst lesen.
- **v1-Interpretation** von VETO 3 (adverse Momentum-Sperre) im Docstring als „v1, am
  Profit zu tunen" markieren — kein verstecktes Confidence-System.
- Tests (≥10): jeder VETO einzeln pass+fail; Momentum BUY-veto bei Abwärts-Move;
  Momentum SELL-veto bei Aufwärts-Move; Momentum knapp unter Threshold → pass; zu wenige
  Bars → veto; `get_ohlcv`-Error → veto; Spread frisch über Max → veto; Status ≠ TRADEABLE
  → veto; Gegen-Position → veto; `pre_trade_check` bricht beim ersten Fail ab.

> **Annotation 2026-06-11 (Step 5 umgesetzt — Code = Source of Truth):**
> - **[VERIFY] Bar-Shape aufgelöst** (gegen `ig_adapter.py:384` + `_parse_bar:819`,
>   `models.py:OHLCBar`): `get_ohlcv(...).data` = `{"bars": [...], "allowance": {...}}`;
>   je Bar ein Dict (aus `OHLCBar.__dict__`) mit Keys `timestamp, open, high, low, close,
>   volume` (Mid aus bid/ask). VETO 3 liest **`close`**. `MINUTE_5` ∈ `VALID_RESOLUTIONS`,
>   `get_price().data.spread_pct` ist **Prozent** (`(ask-bid)/ask*100`).
> - **`net_return` als Prozent:** der Code rechnet `net_return_pct = (close_last −
>   close_first)/close_first × 100` und vergleicht gegen `momentum_veto_threshold_pct`
>   (= **Prozent**, Default 0.15). Konsistent mit `spread_pct`/`max_spread_pct` und dem
>   `_pct`-Namen — sonst hätte der Bruchteil (0.0015) nie die Schwelle (0.15) erreicht.
> - **Window-Prädikat wiederverwendet:** `veto_status_and_window` nutzt
>   `gates.gate_time_window(now, config).ok` (gleiches Paket) — keine Duplikat-tz-Logik.
> - **Fail-closed Exception-Handling:** `veto_momentum` fängt ein breites `Exception`
>   um den `get_ohlcv`-Datenabruf → Veto (mit stderr-Log), der Order-Pfad läuft nie bei
>   einem unerwarteten Datenfehler weiter. Auch `env.ok=False` / <2 Bars / fehlender
>   bzw. 0-Close → Veto.
> - **VETO-4** blockt eine offene **Gegen**-Position auf demselben Epic **und** erzwingt
>   `len(positions) ≥ max_parallel_positions` auf dem frischen Snapshot.
> - **VETO-IDs:** `status_window`/`spread`/`momentum`/`position_conflict`; `pre_trade_check`
>   gibt bei Erfolg `VetoVerdict(ok=True, veto="pre_trade_check")` und short-circuited beim
>   ersten Fail (ein Status-Veto erreicht `get_ohlcv` nie — im Test geprüft).
> - 20 Tests (≥10) grün; `pytest phase5_execution/tests -v` → **79 passed** (59 + 20).
>   `conftest.py` gewachsen um `FakeBroker` + `make_bars`-Helper.

### 6. `order.py` + Tests — Platzieren mit Write-ahead, Confirm, PENDING-fail-closed
```python
def reconcile_startup(broker, exec_state, config) -> None:
    """Vor jedem Lauf: reconcile_positions(expected_references=exec_state.open_references()).
    'missing' (wir denken offen, Broker nicht) → mark_closed/orphan-resolved.
    'unexpected' (Broker hat, wir nicht) → bei reconcile_unexpected_aborts=True:
    ExecutionAbort (nicht stapeln), sonst loggen."""
def build_order_plan(candidate, size, price_env, config) -> OrderPlan:
    """deal_reference = 'bot-' + uuid4().hex. stop_level/limit_level aus
    stop_/limit_distance_points relativ zu price (BUY: stop unter, limit über; SELL umgekehrt)."""
def place_order(broker, exec_state, plan, config) -> ExecutionResult:
    """1) exec_state.record_pending(plan)  ← WRITE-AHEAD vor dem Call.
       2) open_position(epic, direction, size, stop_level, limit_level, deal_reference=ref).
       3) confirmed → exec_state.mark_open(ref, deal_id); status='OPEN'.
       4) dealStatus=='PENDING' → bounded Re-Check (reconcile_positions([ref]) /
          get_open_positions, max N Versuche). present → mark_open. Sonst:
          ExecutionAbort (fail-closed, KEIN zweiter open_position-Call).
       5) klarer Reject (z.B. nicht-retryable error) → exec_state.mark_closed(ref); raise."""
```
- Stop-/Limit-Level-Richtung **[VERIFY]** gegen IG-Erwartung (Punkte vs. absolutes Level)
  in `open_position`.
- Tests (≥8, FakeBroker): write-ahead vor open_position geschrieben; confirmed → OPEN +
  state; PENDING → bounded Re-Check → present → OPEN; PENDING bleibt → ExecutionAbort, **nur
  ein** open_position-Call; reconcile_startup missing → mark_closed; unexpected → Abort;
  nicht-retryable Reject → raise + state aufgeräumt; deal_reference eindeutig pro Plan.

> **Annotation 2026-06-11 (Step 6 umgesetzt — Code = Source of Truth):**
> - **[VERIFY] `deal_reference`-Länge aufgelöst** (gegen `ig_adapter.py:809`
>   `_new_deal_reference` + Kommentar *"IG accepts up to 30 chars"*): der Konzept-Stub
>   `'bot-' + uuid4().hex` ist **36 Zeichen** und würde von IG abgelehnt. `build_order_plan`
>   nutzt daher **`f"bot-{uuid4().hex[:24]}"`** (28 Zeichen, ≤30), wie der Adapter selbst.
>   Test prüft `len(deal_reference) <= 30`.
> - **[VERIFY] Stop-/Limit-Richtung & Preis-Seite:** `stop_level`/`limit_level` sind
>   **absolute Level** (gegen `ig_adapter.py:585` `open_position` → `body["stopLevel"]`/
>   `["limitLevel"]`). Entry-Seite: **BUY rechnet vom `ask`, SELL vom `bid`** (Spread in
>   Fill-Richtung kreuzen); BUY → stop **unter**/limit **über**, SELL invertiert. Die echte
>   IG-Erwartung der absoluten Level bleibt ein **Operator-Live-Check** (Step 10).
> - **PENDING-Recheck-Tunables neu in `ExecutionConfig`** (Konzept §0 hatte sie „erst bei
>   Konsum" vertagt): `pending_recheck_attempts=3`, `pending_recheck_interval_s=2.0` (v1).
>   `place_order` nimmt ein injizierbares `sleep_fn=time.sleep` → Tests treiben die
>   Re-Check-Schleife ohne echtes Warten.
> - **Refinement Schritt 5 (Reject-Handling):** der Konzept-Stub sagte *„klarer Reject
>   (z.B. nicht-retryable error) → mark_closed; raise"*. **Verfeinert:** nur ein bestätigter
>   **`status == "REJECTED"`** heißt definitiv „keine Position" → `mark_closed` + `ExecutionAbort`.
>   Ein **opaker `not env.ok`-Transportfehler** ist **mehrdeutig** (die Order *kann* live sein,
>   da der Adapter erst nach dem POST `/confirms` pollt) → wird wie `PENDING` behandelt: Record
>   bleibt **PENDING**, `ExecutionAbort` (fail-closed), Startup-Reconcile löst es im nächsten
>   Lauf. „Nie eine möglicherweise-live Order als closed markieren, nie blind eine zweite Order."
>   `UNKNOWN`-Status → ebenfalls Re-Check-Pfad (fail-closed).
> - **`OrderResult.data`-Form** (gegen `models.py:96` + `_normalize_deal_status:899`):
>   `{deal_reference, deal_id, status, epic, direction, size, level, reason, timestamp}`,
>   `status ∈ {ACCEPTED, REJECTED, PENDING, UNKNOWN}`. `reconcile_positions(...).data` =
>   `{broker_position_count, broker_deal_ids, present, missing, unexpected}` (die drei Mengen
>   nur bei gesetzten `expected_references`). Nach PENDING→present holt `_lookup_deal_id` die
>   `deal_id` aus `get_open_positions` (Refs ↔ deal_id-Mapping); fehlende deal_id ist nicht
>   fatal (Ref ist der Idempotenz-Schlüssel).
> - **VETO/Order-Naht Phase 6** unverändert: `build_order_plan` + `place_order` sind reine
>   Funktionen, Broker duck-typed (`execution.*` + stdlib only, kein Schwester-Import).
> - 15 Tests (≥8) grün; `pytest phase5_execution/tests -v` → **94 passed** (79 + 15).
>   `conftest.py` `FakeBroker` um `open_position`/`reconcile_positions` erweitert.

### 7. `monitor.py` + Tests — Polling + Time-Stop + Close
```python
def monitor_position(broker, exec_state, plan, deal_id, config, *,
                     now_fn=datetime.now, sleep_fn=time.sleep) -> ExecutionResult:
    """Loop alle poll_interval_s:
       - get_open_positions: deal_id nicht mehr da → broker-seitiges SL/TP gefüllt →
         exec_state.mark_closed; status='CLOSED_BY_BROKER'.
       - now >= square_off_time ODER elapsed >= max_hold_minutes →
         broker.close_position(deal_id) → mark_closed; status='TIME_STOP'.
       now_fn/sleep_fn injiziert für deterministische Tests (kein echtes Warten)."""
```
- Tests (≥6, FakeBroker, gemockte `now_fn`/`sleep_fn`): Position verschwindet →
  CLOSED_BY_BROKER; square_off erreicht → close_position aufgerufen → TIME_STOP; max_hold
  erreicht → TIME_STOP; close_position-Fehler → ExecutionAbort (Operator); Loop terminiert
  immer; state am Ende `closed`.

> **Annotation 2026-06-11 (Step 7 umgesetzt — Code = Source of Truth):**
> - **`close_position`-Contract** (gegen `ig_adapter.py:661`): der Adapter schlägt
>   Richtung/Size **selbst** nach und schließt gegenläufig; ok → `.data={"deal_id",
>   "status":"submitted"}`. **Ist die `deal_id` nicht (mehr) offen → Error-Envelope**
>   (`BrokerError`). **Edge (v1):** verschwindet die Position *zwischen* dem
>   `get_open_positions`-Check und dem Time-Stop-`close_position`, schlägt der Close fehl →
>   `ExecutionAbort` (Konzept §7 „close_position-Fehler → Abort"; sicher, kein Doppel-Schritt,
>   Operator reconciled). Bewusst **nicht** den Error geparst, um „schon weg" von echtem
>   Fehler zu unterscheiden — späteres Refinement.
> - **Max-Hold-Anker:** `entry = now_fn()` **einmal beim Monitor-Eintritt**; `elapsed =
>   now − entry ≥ max_hold_minutes`. (Konzept ließ den Anker offen.)
> - **Unsicherer Read:** ein **`not ok`** `get_open_positions` wird **nicht** als Close
>   interpretiert (keine Schließung aus einem fehlgeschlagenen Read inferieren) → WARNING +
>   weiter pollen; der Time-Stop garantiert Terminierung.
> - **Square-Off-Prädikat** wiederverwendet `gates._parse_hhmm` + das
>   `gate_time_window`-tz-Idiom (`now.astimezone(ZoneInfo(config.tz))` falls tz-aware, sonst
>   in-Zone angenommen) — Vergleich `time-of-day ≥ square_off_time`. Keine Duplikat-Logik.
> - **Status-Vokabular** (bereits in `models.py` dokumentiert): `CLOSED_BY_BROKER` /
>   `TIME_STOP`; `ExecutionResult.detail` trägt `square_off` bzw. `max_hold`. **Keine**
>   models-/config-Änderung nötig (`poll_interval_s`/`square_off_time`/`max_hold_minutes`
>   existieren).
> - **Naht Phase 6** unberührt: reine Funktion, Broker duck-typed (`execution.*` + stdlib only).
> - 6 Tests (≥6) grün; `pytest phase5_execution/tests -v` → **100 passed** (94 + 6).
>   `conftest.py` `FakeBroker` um `close_position` + `positions_sequence` (eine Env pro
>   `get_open_positions`-Aufruf, letzte wiederholt) erweitert.

### 8. `executor.py` + Tests — Orchestrator (der ganze Pfad)
```python
class Executor:
    def __init__(self, broker, db, state, exec_state, config,
                 research_runner, confirm_fn): ...   # alles DI
    def run(self) -> ExecutionResult: ...
```
Flow (alles Code):
1. `broker.connect()`/`is_connected()`; Session-Health (`get_account().ok`). Fail → Abort.
2. `reconcile_startup(...)`. Konflikt → Abort.
3. **Gate 1** time_window → fail → ExecutionResult('NO_TRADE', reason).
4. **Gate 2** load_candidates (ggf. `research_runner()`); leer → 'NO_TRADE' (Abstain).
5. **Gate 3** constraints; **Gate 5** direction_consistency → fail → 'NO_TRADE'.
6. **Gate 4** Sizing; size < min → 'NO_TRADE'.
7. **`pre_trade_check`** (4 VETOs, frisch) → fail → 'NO_TRADE' (VetoRejected-Grund geloggt).
8. `plan = build_order_plan(...)`.
9. **Human-Confirm:** `if config.require_confirm and not confirm_fn(plan): return 'ABORTED_BY_USER'`.
10. `place_order(...)` → bei OPEN: `monitor_position(...)`.
11. Jede REJECT/VETO/Abort-Begründung nach **stderr**; stdout nur maschinenlesbares
    Ergebnis-JSON.
- `confirm_fn: Callable[[OrderPlan], bool]` injiziert (ig_bot: stdin-Prompt; `--yes`:
  `lambda _p: True`; Tests: Stub).
- Tests (≥8, FakeBroker): voller Pfad open→close (Position verschwindet) → erfolgreicher
  Lebenszyklus; Gate-1-Fail → kein LLM/keine Order; Gate-2-Abstain → kein Order; VETO-Fail
  → kein Order; size<min → kein Order; `require_confirm` + confirm_fn=False → ABORTED_BY_USER,
  **kein** open_position; Session-Health-Fail → Abort; reconcile-Konflikt → Abort.

> **Annotation 2026-06-11 (Step 8 umgesetzt — Code = Source of Truth):**
> - **Injizierte `now_fn`/`sleep_fn` am `Executor`** (keyword-only, Default `datetime.now`/
>   `time.sleep`): die §8-Signatur-Skizze listet sie nicht, aber `monitor.py`/`order.py`
>   injizieren sie bereits — derselbe Pattern macht Gate 1, den VETO-Fenster-Check, die
>   PENDING-Re-Check-Schleife und den Monitor-Loop **deterministisch testbar** (kein echtes
>   Warten). `now = now_fn()` wird **einmal** geholt und für Gate 1 **und** `pre_trade_check`
>   wiederverwendet (die VETO-Frische kommt aus neu geholten Broker-Snapshots, nicht der
>   Wall-Clock); `now_fn` wird zusätzlich an `monitor_position` durchgereicht.
> - **Aborts werden `return`ed, nicht `raise`d:** `ExecutionAbort`/`ReconcileConflict` werden
>   an der `run()`-Grenze gefangen und als `ExecutionResult(status="ABORT", …)` zurückgegeben
>   (Status-Vokabular bereits in `models.py` dokumentiert) → Step-9-`ig_bot` mappt
>   `status == "ABORT"` auf `exit != 0`. Ein einziges Ergebnis-Objekt zum Serialisieren.
> - **Single-Fetch-Reuse:** `get_account` wird in `_ensure_session()` einmal geholt und für
>   Gate 3 + Sizing wiederverwendet; `get_open_positions` einmal für Gate 3 **und** Gate 5;
>   `get_price` einmal für Sizing **und** `build_order_plan`. `pre_trade_check` holt seine
>   **eigenen** frischen Snapshots (das ist der Sinn der VETOs). Weniger Broker-Roundtrips,
>   gleiche Korrektheit im synchronen Single-Run.
> - **FakeBroker erweitert** (conftest): Session-/Sizing-Fläche `is_connected`/`connect`/
>   `get_account`/`get_market_info` (Default `available` modest → Default-Pfad no-traded am
>   Sizing; der Happy-Path-Test setzt `available=2_000_000` für eine valide Size ≈0.5).
> - 8 Tests (≥8) grün; `pytest phase5_execution/tests -v` → **108 passed** (100 + 8). Proof-
>   Tests (b) adverse-Momentum-VETO + (c) Confirm-abgelehnt liegen hier; (a) PENDING→ein
>   `open_position`+Abort in `test_order.py`.

### 9. `ig_bot.py` — CLI-Entry / Composition Root
- `argparse`: `--yes` (confirm überspringen), `--epic` (optional Override), `--dry`
  (Gates+VETOs ohne Order), `--broker ig_demo` (Default).
- Baut den Executor über `scripts/wiring.build_executor(config)`; `confirm_fn` = stdin
  `y/N`-Prompt (Default), bei `--yes` immer True.
- Druckt Ergebnis-Envelope als JSON auf stdout, Logs auf stderr. `exit 0` bei sauberem
  Lauf (auch `NO_TRADE`/`ABORTED_BY_USER` sind kein Fehler), `exit != 0` nur bei `ExecutionAbort`.

> **Annotation 2026-06-11 (Step 9 umgesetzt — Code = Source of Truth):**
> - **`ig_bot.py` liegt im `execution`-Paket** (`execution/ig_bot.py`, wie der Modul-Baum) →
>   `python -m execution.ig_bot`. Der `build_executor`-Import ist **lazy in `main()`** (ein
>   `sys.path.insert(<phase5_execution/>)` + `from scripts.wiring import build_executor`), damit
>   `--help` + die Unit-Tests **kein** Keyring/Netz brauchen. Das ist die **einzige**
>   `sys.path`-Stelle und nur im Entry-Script (Phase-4-Präzedenz) — das `execution`-Runtime-Paket
>   bleibt sys.path-frei.
> - **Exit-Code:** `exit_code(result)` = `1` **nur** bei `status == "ABORT"`, sonst `0`
>   (`NO_TRADE`/`ABORTED_BY_USER` sind saubere Läufe). Aborts werden vom Executor als
>   `status="ABORT"` **zurückgegeben** (nicht geraised, Step-8-Entscheidung) → `ig_bot` mappt sie.
> - **`--dry` = Confirm-False:** kein eigener Dry-Modus im Executor — `make_confirm_fn(dry=True)`
>   loggt den gebauten `OrderPlan` und gibt `False` → die volle Gate/Sizing/VETO-Pipeline läuft,
>   der Plan wird gebaut, **kein** `open_position` (Confirm-Gate stoppt), Ergebnis
>   `ABORTED_BY_USER` (von `ig_bot` als „DRY RUN" gelabelt). Kein Executor-Change.
> - **`--epic`** ist ein **Research-Allow-List-Override** (Phase-4-Semantik), kein
>   `ExecutionConfig`-Feld — `ig_bot` reicht `epic_override` an `build_executor` durch (die
>   `ResearchConfig` für den `research_runner`); der Executor selbst nimmt das Epic aus dem Candidate.
> - **Ergebnis-Serialisierung:** `result_to_dict = dataclasses.asdict` (rekursiv in den
>   `OrderPlan`) → JSON auf **stdout**, Human-Summary auf **stderr**.
> - 18 Tests (≥) grün (`test_ig_bot.py`, rein, kein Netz/Keyring/Wiring-Import); `pytest
>   phase5_execution/tests -v` → **126 passed** (108 + 18).

### 10. `scripts/`
- **`wiring.py`:** baut **echte** `IGAdapter` (Demo-Creds via Keyring), `Database`,
  `StateManager`, `ExecutionState`, `research_runner = lambda: build_research(cfg).run()`
  (lazy import von Phase 4). Eine Factory `build_executor(config) -> Executor`. Editable-
  Install-Imports (kein `sys.path`).
- **`smoke_test.py`:** liest read-only, fährt Gates + `pre_trade_check` **DRY**
  (`--dry`-Pfad, kein `open_position`), druckt jeden Gate-/VETO-Verdict. Schnell, manuell.
- **`live_test.py`:** voller open→close-Zyklus gegen IG Demo (kleine Size), hart asserted,
  `exit 0` = PASS. **Operator führt es aus**, läuft **nicht** in CI.

### 11. `README.md` · `requirements.txt` · `CLAUDE.md`
- `requirements.txt`: nur Phase-5-eigene Dev-Deps (Runtime-Deps der Schwester-Packages
  kommen über deren editable installs).
- `README.md`: kurz — was `phase5_execution/` ist (erster Execution-Pfad, Demo, manueller
  Trigger), wie man `ig_bot.py`/`smoke_test.py`/`live_test.py` startet, Verweis auf
  `CLAUDE.md` für die harten Regeln.
- **`CLAUDE.md`** schreibt Claude Code wie gewohnt selbst — **diese Struktur vorgeben**
  (an den bewährten älteren Phase-`CLAUDE.md`s orientiert). VETO-3-Schwelle + SL/TP-Punkte
  explizit als „v1, am Profit zu tunen" markieren; den `## Session stopped`-Block leer
  anlegen, Befüllung am Sessionende:

```markdown
# CLAUDE.md — Phase 5: Execution (phase5_execution/)

> Erster Order-Pfad des Bots. Demo, manueller Trigger, KEIN Scheduler (= Phase 8).
> Quelle der Wahrheit ist der Code, nicht dieses Dokument.

## AI-Grenze (Projekt-Kernprinzip)
„So wenig AI wie möglich, so viel AI wie nötig." **Phase 5 enthält KEINE AI.** Alle Gates,
VETOs, Sizing, Order, Monitoring, Reconcile sind deterministischer Code. Die einzige AI im
System bleibt der eine Phase-4-Research-Call (über Gate 2 ausgelöst). Wer hier ein LLM
„entscheiden/sizen/vetoen" lassen will → stop, das ist Code (oder Phase 6).

## Scope
- DRIN: Gate 1–5, pre_trade_check (4 VETOs), place/monitor/close, reconcile, Human-Confirm.
- DRAUSSEN: Bull/Bear/Judge (P6), Token-Metering (P6), Outcome-Schreiben (P7),
  Lightstreamer (P8), ATR-SL/TP, Live-Trading (IG Europe GmbH nötig).

## Harte Regeln (nicht verhandelbar)
- Step 0 erledigt: kein option_check/CALL/PUT/strike/otm/FLIP mehr.
- Alle 4 VETOs sind HART (= kein Trade). Datenfehler/zu wenige Bars → fail-closed (Veto).
- Momentum-VETO NUR aus broker.get_ohlcv (IG-Echtzeit), NIEMALS Phase-3-get_momentum().
- Write-ahead deal_reference VOR open_position; PENDING → kein zweiter Order-Call, fail-closed.
- require_confirm default AN; --yes nur bewusst. Demo only.
- Database read-only (Outcome-Schreiben = Phase 7). turbo_candidates.json NICHT umbenennen.
- Logging → stderr; stdout nur maschinenlesbares JSON. Atomic commits. Kein Subtask „done"
  ohne grünes pytest (gemockt, kein Netzwerk, keine echte Order in Unit-Tests).

## Die 8 Entscheidungen (A–H)
<Tabelle aus dem Execution-Plan §0 übernehmen — Festlegung + Begründung pro Zeile.>

## Die 4 VETOs (CFD-spezifisch, deterministisch)
1. Status/Zeit · 2. Spread (frisch) · 3. Momentum (get_ohlcv) · 4. Position/Constraint.
<Quelle + Threshold je VETO; VETO-3-Schwelle als „v1, zu tunen".>

## Geerbte Contracts (Repo = Wahrheit)
<Kurzliste der genutzten P1/P2/P4-Signaturen + Verweis auf den Execution-Plan.>

## Naht für Phase 6
Hand-off „Candidate → Gates → Order" so, dass P6 Richtungs-/Size-Quelle austauschen kann,
ohne Gates neu zu schreiben (Gate 5 + build_order_plan).

## Datei-/Modul-Übersicht
<Baum aus dem Execution-Plan, eine Zeile Zweck je Datei.>

## Session stopped
<!-- Pflicht. Am Ende JEDER Claude-Code-Session befüllen, sonst kein sauberer Re-Entry. -->
- **Stand:** <Datum, was code-complete + grün ist (Testzahl)>.
- **Zuletzt gemacht:** <Module/Commits dieser Session>.
- **Nächster Schritt:** <konkret, das nächste Modul/der nächste Test>.
- **Offene Punkte / [VERIFY]:** <noch ungeprüfte Contracts, z.B. get_ohlcv-Bar-Shape>.
- **Gotchas:** <Stolperfallen, die der nächste Session-Start kennen muss>.
```

---

## Done-Kriterien (Phase-5-Gate)
- `pytest phase5_execution/tests -v` grün, **≥45 Tests** (alle gemockt, **kein Netzwerk,
  keine echte Order** in Unit-Tests), davon `test_vetos.py` ≥10, `test_executor.py` ≥8.
- `bash scripts/dev_install.sh` + `pytest` grün **ohne** `sys.path`-Hack (Step C bewiesen).
- `grep` aus Step 0 zeigt keine option/CALL/PUT/strike/otm/FLIP-Logik mehr.
- `python phase5_execution/scripts/live_test.py` öffnet **und** schließt einen Trade gegen
  IG Demo durch **alle** Gates + VETOs, `exit 0` (Operator-Lauf).
- **Beweis-Tests:** (a) ein erzwungenes `PENDING` führt zu **genau einem** `open_position`-
  Call + `ExecutionAbort` (kein Doppel-Order); (b) ein adverser Momentum-Snapshot
  (`get_ohlcv`) vetoed zuverlässig vor der Order; (c) `require_confirm` + abgelehnte
  Bestätigung platziert **keine** Order.

---

## Bewusst NICHT in Phase 5 (Carry-overs)
- **Bull/Bear/Judge-Debatte** (ersetzt die einfache Richtungsquelle) → **Phase 6**. Phase 5
  baut den Hand-off „Candidate → Gates → Order" so, dass Phase 6 Richtungs-/Size-Quelle
  **austauschen** kann, ohne Gates neu zu schreiben (Gate 5 + `build_order_plan` sind die Naht).
- **Token-Metering** → erst wenn AI dazukommt (Phase 6): Phase-4-`token_meter`
  **wiederverwenden**, kein zweites Mess-System. Phase 5 hat keinen AI-Call.
- **Outcome-/Lesson-Schreiben** in SQLite → **Phase 7** (`Database` ist hier read-only:
  `get_recent_trades/lessons/score/risk_level`).
- **Lightstreamer-Stream** (PRICE-Subscription) → erst **Phase 8** bei Bedarf. Phase 5 = Polling.
- **ATR-basierte SL/TP** → späterer Swap (kann die VETO-3-Bars wiederverwenden). Phase 5 =
  feste Config-Punkte.
- **Live-Trading** → braucht das **IG Europe GmbH**-Konto (deutsche Residency). Phase 5
  bleibt **Demo**.
