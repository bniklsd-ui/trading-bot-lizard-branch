# Phase 8 — Implementierungsplan für Claude Code

> **Status:** Architektur geklärt (20 Entscheidungen unten gelockt + 7 offene Fragen
> beantwortet), Contracts gegen Handover verifiziert. **Quelle der Wahrheit bleibt das
> Repo-Code** (entpackter Baum auf Google Drive / GitHub raw). Wo dieser Plan eine Signatur
> nennt, ist sie als **Annahme aus dem Handover** markiert und in **Step 1 gegen echten Code
> zu verifizieren**, bevor darauf gebaut wird.
>
> **Mission (Sonder-Notiz, zuerst lesen):** Phase 8 heißt „Scheduler", aber das Ziel ist
> **autonome, unbeaufsichtigte Erzeugung echter Demo-Trades** — denn alles danach (Confidence
> aus `INSUFFICIENT`, P9-Instinct-Promotion) ist auf reale Outcomes gegatet. „Einen Cron-Job
> bauen" ist *nicht* die Aufgabe. Der harte Pfad ist die **autonome Kandidaten-Generierung**;
> ohne sie sammelt der Scheduler **null Daten**.
>
> **Bauprinzip unverändert:** „So wenig AI wie möglich, so viel wie nötig." **Phase 8 fügt
> KEINE neue AI hinzu** — ein Scheduler ist reine Mechanik. AI bleibt auf P4-Research-Pick,
> P6-Debatte, P7-Lesson beschränkt (alle aus Vorphasen, unverändert wiederverwendet).
>
> **Build-Reihenfolge (verbindlich):** Cleanup → Verify → autonome Kandidaten → Auto-Confirm/
> Safety → Reconcile-Pass → Loop/Daemon → **zuletzt** Web-UI. Unter Zeit-/Token-Druck fällt
> die UI weg, **nie** die Safety.

---

## 0. Geklärte Architektur-Entscheidungen (gelockt)

| # | Entscheidung | Festlegung |
|---|---|---|
| 1 | Prozessmodell | **Langlaufender Daemon** (ein Python-Prozess), interne Loop mit injizierbarem `now_fn`/`sleep_fn`. **Kein** externer Cron, **keine** APScheduler-Lib. Grund: warme IG-Session/Token-Refresh + Lightstreamer + Keyring-Erreichbarkeit. |
| 2 | Marktzeiten-Logik | **Reuse `external_data/market_hours.py` (P3) + Gate-1-Fenster** (09:30–11:19 CET, aus P5-Config). Europe/Berlin, DST-aware. |
| 3 | Cycle-Kadenz | **Konfigurierbar** (`cycle_interval_min`, Default 5 für Testrun). Bei offener Position übernimmt P5-`monitor_position`. |
| 4 | Research-Trigger | **Scheduler triggert echtes P4-Research explizit** (`research_tick`) und **populiert frische Candidates VOR** `executor.run()`, sodass Gate 2 sie als fresh sieht und **nicht** re-callt. Reuse der P4-`wiring`-Factory. Auditierbar. |
| 5 | `no_trade_reason` | **Gerüst jetzt, minimal befüllt** (`reason_code`-Enum) in stderr + `scheduler_state.json`. **Volles v3-Signalmodell = P9.** Kein neuer AI-Call. |
| 6 | Auto-Confirm | **`confirm_fn`-Implementierung**, gibt `True` nur bei: demo + Kill-Switch aus + unter Trade-Cap + unter Tages-Loss-Cap + Budget ok. Deterministischer Code, ersetzt P5-Human-Confirm. |
| 7 | „Demo-only" strukturell | **Hart fail-closed**: Auto-Confirm verweigert gegen alles ≠ `account='demo'`. Kein Config-Bool allein. Live-Auto-Confirm architektonisch gesperrt bis Profit-Validierung. |
| 8 | Kill-Switch | **Datei-basiert** (`data/state/KILL`). Jeder Loop prüft sie. Funktioniert UI-unabhängig; UI darf sie nur setzen/löschen. |
| 9 | Fehler-Backoff | **Exponentielles Backoff bei Cycle-Exception; nach `max_consecutive_failures` (Default 3) → Kill-Switch + sauberer Stop.** Schwellwert konfigurierbar, Begründung siehe §Modul `backoff`. |
| 10 | Tages-Loss-Circuit-Breaker | **Jetzt (Demo).** Derselbe Code schützt später Live (P9e-Vorgriff). De-riskt den „Dauer-Trader". |
| 11 | `CLOSED_BY_BROKER`-Reconcile | **Idempotenter Reconcile-Tick** (Startup + periodisch + Shutdown): Broker-SL/TP-Closes ohne Close-Confirm → P&L nach Settlement aus `get_trade_history` → `update_trade_close` + `insert_reward` nachholen, idempotent via `deal_id`. Reuse P1-`reconcile_positions` + P7-Retry. |
| 12 | Budget-Gate | **Deterministisches Tages-/Zyklus-Token-Budget** (reuse 8-Feld `token_meter`). Überschreitung → keine neuen Cycles; Monitoring/Reconcile laufen weiter. |
| 13 | UI-Stack | **FastAPI (read-mostly JSON-API) + statisches HTML/JS, kein Build-Step, kein React/npm.** |
| 14 | UI-Prozessmodell | **Separater Prozess**, Datei-basierte Steuerung. UI liest SQLite (read-only) + JSON-State, „steuert" nur via Kill-/Command-Datei. Trader-Integrität hängt **nie** von der UI ab. *(P10-Hook: spätere Aktionen wie „Deep Research starten" gehen über dieselbe Command-Datei — Architektur offen halten, jetzt nicht bauen.)* |
| 15 | UI-Scope | Read: Score-Verlauf, Confidence-Status (+N), letzte Lessons, offene/geschl. Trades, Tages-P&L, Trade-Count vs. Cap, Scheduler-Status, letzter Cycle + `no_trade_reason`, Backoff/Error. Control: Start/Stop/Kill. Keine Param-Edits. |
| 16 | UI-Design | GitHub-Dark-Palette, Monospace, kein Emoji. **Buttons/Knöpfe Richtung Glass-/Skeuo-/Neumorphism** (nicht Brutalismus). Polling 5–10 s, keine WebSockets v1. *Design jetzt nicht überoptimieren.* |
| 17 | UI-Auth/Bind | **Bind `127.0.0.1` only, keine Auth (Testphase).** *Carry-over: später trotzdem leichte Auth (Extra-Sicherheit) → §Carry-overs.* |
| 18 | Scheduler-State | **`data/state/scheduler_state.json`** (Trade-Count, last-research-ts, Backoff-Counter, Kill-Reason, Tages-Loss-Akku, last-reconciled-ts). Datums-Rollover Europe/Berlin, idempotent. JSON-State-Muster wie P2. |
| 19 | Paket/Naming | **`phase8_scheduler/`, Paket `scheduler`.** Entry `python -m scheduler.run`. Composition-Root `scripts/wiring.py` reiht sich nach P7 ein. |
| 20 | Deployment v1 | **`scripts/run_scheduler.sh`, Start in entsperrter Session** (Keyring erreichbar) + **fail-closed Keyring-Preflight** + `## known issue`-Note zu Background/Headless. Volles systemd-Hardening → defer. |

**Caps-Defaults (Testrun, am echten Output zu tunen):** `max_trades_per_day=5`,
`cycle_interval_min=5`, `max_consecutive_failures=3`, `daily_loss_cap` → **bewusst zu setzen
(offene Frage, siehe Modul `safety`)**.

---

## Step 0 — Turbo-/Legacy-Bereinigung (eigener Commit, VOR jeder Logik)

Phase 4 hat das große Aufräumen erledigt; hier erwarten wir **Bestätigung, keinen Fund**. Bleibt
trotzdem als stehender Schritt drin.

1. `grep -ri "call\|put\|strike\|otm\|issuer\|turbo_research" --include=*.py` über das ganze
   Repo → **muss leer** sein (außer dem bewusst dokumentierten `turbo_candidates.json`-Legacy-
   Namen). Bei Treffer: melden, **nicht** still patchen.
2. **`turbo_candidates.json`** bleibt eingefroren (Phase-5-Gate-2-Contract) — nicht umbenennen.

**Done when:** grep sauber, dokumentiert im Commit-Body.

---

## Step 0b — Doku-Reconciliation (selber erster Commit)

Die projektweiten Docs hängen noch auf Phase 7. **Vor** dem Build angleichen:

1. Root-`CLAUDE.md` „Current state" → **Phase 8 in Umsetzung**; Phase 7 → ✅ abgeschlossen +
   live-verifiziert + gepusht (2026-06-26).
2. `README.md`-Statustabelle: Zeile 7 → ✅ abgeschlossen; Zeile 8 → 🔄 In Umsetzung.
3. `ROADMAP.md` Phase-7-Block → Checkboxen/Status final; Phase-8-Checkboxen vorbereiten.
4. **Hard Rule „Commit ⇒ Note-Update"** gilt ab hier für jeden Abschluss-Commit.

**Bewusst NICHT hier:** der stale Modell-String in `the_council.jsx`
(`claude-sonnet-4-20250514`) — Council ist P9-Scope, nicht P8. Nur vermerken.

---

## Step 1 — Contract-Verify gegen echten Repo-Code (vor jeder Implementierung)

Dieser Schritt pinnt alle Annahmen, auf denen der Plan steht. **Kein Build-Code**, nur Lesen +
Notieren. Wenn eine Signatur abweicht, **erst hier korrigieren**, dann bauen.

1. **Seed→ABSTAIN-Mechanismus bestätigen (kritisch):**
   - `phase5_execution/scripts/seed_candidate.py` öffnen → den Marker-String („DIES IST EIN
     MANUELL ERSTELLTER SEED" o.ä.) finden und notieren, **wo** er sitzt (reasoning/header).
   - `phase4_research/.../research.py` + `build_prompt`/`candidate.to_dict()` prüfen: der echte
     Research-Output enthält diesen Marker **niemals**. → **Assertion-Test schreiben**
     (`test_no_manual_seed_marker`): ein realer (gemockter) Research-Pick darf den Marker-String
     nicht enthalten. Das ist die Garantie, dass autonome Candidates handelbar sind.
2. **Executor-Naht verifizieren:** `executor.run(...)`-Signatur + `Executor.__init__`. Erwartet
   (Handover): `__init__(..., *, debate_runner=None, reward_sink=None, now_fn, sleep_fn)`,
   `run(..., confirm_fn=...)`. **Klären:**
   - Wie übergibt man `confirm_fn`? (Konstruktor vs. `run()`-Argument.)
   - Was ist der Rückgabe-Typ von `run()`? (für `state.record_cycle`).
3. **Gate-2-Freshness-Contract (entscheidet Decision 4):**
   - Wenn `research_tick` **frische** Candidates schreibt → ruft Gate 2 Research **nicht** erneut?
   - Wenn `research_tick` **abstaint** (leere, aber frische Liste via `save_candidates([])`) →
     behandelt Gate 2 das als „keine Candidates, fresh" → `NO_TRADE` **ohne** Re-Call? (Sonst
     droht doppeltes Research + LLM-Kosten.) Gegen `StateManager.candidates_are_fresh()` +
     Gate-2-Code prüfen.
4. **Confirm-Pfad:** wo genau im Pfad wird `confirm_fn` aufgerufen (vor `place_order`)? Bekommt
   es genug Kontext (epic, direction, size, account) für die Demo-/Cap-Checks?
5. **Reconcile-Bausteine:** `broker.reconcile_positions(...)`, `ExecutionState`
   (write-ahead `deal_reference`), `broker.get_trade_history(days=30)`-Rückgabeform,
   P2-`update_trade_close` + `insert_reward`-Signaturen, P7-`reward_sink.on_trade_closed`.
6. **Momentum-VETO-Quelle (stehender TODO):** bestätigen, dass der P5-Momentum-VETO bereits aus
   `get_ohlcv` (IG-Echtzeit) sourcet, nicht aus P3-`get_momentum()`. ARCHITECTURE sagt ja —
   **verifizieren, nicht annehmen**. Falls nicht: als separaten Fund melden (nicht in P8 fixen,
   außer es blockt den autonomen Pfad).
7. **`token_meter`-API** (8-Feld) für das Budget-Gate; **`market_hours.py`-API** (Funktionsname,
   Rückgabe) für `clock`; **Keyring-`get_credential`** für den Preflight.
8. **Composition Root:** P7-`scripts/wiring.py` als Vorlage lesen — wie werden P1/P2/P3/P4/P6/P7
   real verdrahtet (`live_db_path=data/trading_bot.sqlite`, `register_volume_proxy("EXS1.DE")`,
   `reward_sink`, `debate_runner`)? P8-`wiring.py` erweitert exakt das.

**Done when:** ein kurzer `## Verified contracts`-Block in `phase8_scheduler/CLAUDE.md` hält die
echten Signaturen + den Gate-2-Freshness-Befund fest. **Erst dann** beginnt der Build.

---

## Verifizierte geerbte Contracts (Annahmen aus Handover — Step 1 bestätigt)

- **P5-Executor:** ⚠ **korrigiert (Step 1, 2026-06-27, Code = Wahrheit):** echte Signatur
  `Executor(broker, db, state, exec_state, config, research_runner, confirm_fn, *,
  debate_runner=None, reward_sink=None, now_fn=datetime.now, sleep_fn=time.sleep)` — **`confirm_fn`
  ist ein KONSTRUKTOR-Argument, `run()` ist arglos** (`run() -> ExecutionResult`), **nicht**
  `run(confirm_fn=...)` wie hier ursprünglich angenommen (Finding A). Der Executor wird **einmal**
  mit `confirm_fn=AutoConfirm` gebaut; die Loop ruft bare `run()`; `AutoConfirm` liest State/Caps
  **live** pro Aufruf. `config.require_confirm` ist default **True** → Auto-Confirm wird aufgerufen
  (Wiring darf es nicht auf `False` setzen). Default-`reward_sink`/`debate_runner` halten P5
  bit-identisch — P8 verdrahtet den **vollen** Zyklus.
- **P4-Research:** `Research.run() -> list[Candidate]`; schreibt `turbo_candidates.json` (1 Pick |
  `[]`=Abstain, TTL 30 min). ⚠ **Reconciliation (Finding G):** P4-`scripts/wiring.py`
  `build_research()` baut sich **einen eigenen** Broker → für die warme IG-Session (Decision 1)
  konstruiert P8-`wiring.py` `Research` **direkt aus dem `research`-Paket** mit dem **geteilten**
  Broker (spiegelt P7, das den Executor direkt aus `execution` baut), statt P4s Factory zu rufen.
- **P3:** `external_data/market_hours.py`-Guard (Marktzeiten); `MarketDataFetcher`.
- **P2:** `Database` (alle Writes vorhanden/getestet), `update_trade_close`, `insert_reward`,
  `get_recent_*`, `get_current_score`; `StateManager.{save,load,clear}_candidates`,
  `candidates_are_fresh()`. `init_db.py` wendet Migration `002` an (`initial_risk`,
  `r_multiple`, `account`).
- **P1:** `IGAdapter` (Demo-Creds via Keyring `SERVICE_NAME="tradingbot"`),
  `reconcile_positions`, `get_trade_history(days=30)` (Fallback-P&L, heuristisch),
  `is_connected()`/`connect()` (Session-Keepalive).
- **P7:** `reward_sink` (Protocol, `on_trade_opened`/`on_trade_closed`), `confidence`-Modul
  (observe-only), `reflect()` (unverändert, **nicht** in P8 angefasst). Zusätzlich liefert P7
  (Step 13b) **`reward_sink.reconcile_open_trades(deal_ids=None)`** — idempotenter
  `CLOSED_BY_BROKER`-P&L-Nachzieh, den `reconcile.py` wiederverwendet (Finding F).

> **⟳ Step-1 Code-Reconciliations (2026-06-27, Code = Source of Truth).** Die obigen
> Handover-Annahmen wurden gegen den Live-Code gepinnt; fünf weichen ab und formen den Build.
> Volle Details + `file:line` in `phase8_scheduler/CLAUDE.md` → `## Verifizierte Contracts`.
> - **A — `confirm_fn` ist Konstruktor-Arg, `run()` arglos** (oben korrigiert). Executor einmal mit
>   `AutoConfirm` bauen; Loop = bare `run()`.
> - **B — Gate-2-Freshness re-callt Research bei `[]`** (`candidates_are_fresh()` ist `False` für eine
>   leere Liste, `state.py:150`): `save_candidates([])` bei Abstain verhindert den Re-Call **nicht**.
>   ⇒ **No-op-`research_runner`** in den Executor injizieren (P7-Muster); echtes Research läuft
>   **vorher** in `research_tick`. Betrifft Decision 4 + Step 1.3 + die §10-Loop-Skizze.
> - **C — Seed-Marker ist englisch** `"MANUAL SEED (not a real research pick)"`
>   (`seed_candidate.py:62`) → das ist der `test_no_manual_seed_marker`-String (Step 1.1).
> - **D — `confirm_fn(plan)` bekommt einen `OrderPlan` OHNE `account`-Feld** (`executor.py:229`):
>   der `order_ctx.account=="demo"`-Doppel-Check (§5/Decision 6/7) ist aus dem Plan **nicht**
>   verfügbar → Demo-Lock strukturell im Wiring (`config.account="demo"`, nur `ig_demo`-Broker).
> - **E — `realized_pnl_today` aus der DB lesen**, nicht nur aus dem Cycle-Result: `CLOSED_BY_BROKER`
>   trägt kein sofortiges `profit_loss` (erst per Reconcile aufgelöst) → der Loss-Breaker (Decision 10/
>   §5) summiert die heutigen `trade_outcomes`/`reward_pts` über `session_date`.
> - **F/G** — Reconcile reuse + ein geteilter Broker (oben annotiert).

---

## Modul-Aufbau `phase8_scheduler/` (Paket `scheduler`)

```
phase8_scheduler/
├── CLAUDE.md                    # ERSTE Aktion: Skelett + ## Session stopped + ## Verified contracts
├── README.md
├── requirements.txt             # fastapi, uvicorn (UI); sonst reuse Vorphasen
├── scheduler/
│   ├── __init__.py
│   ├── config.py                # SchedulerConfig — alle Tunables an einem Ort
│   ├── exceptions.py            # SchedulerError, PreflightError, ...
│   ├── clock.py                 # now_fn/sleep_fn injizierbar; Phasen-Klassifikation
│   ├── state.py                 # SchedulerState <-> scheduler_state.json; Tages-Rollover
│   ├── killswitch.py            # KILL-Datei lesen/setzen/löschen (von safety + UI genutzt)
│   ├── safety.py                # Auto-Confirm confirm_fn: demo + killswitch + caps + loss-breaker + budget
│   ├── backoff.py               # konsekutive-Fehler-Tracking + Backoff-Schedule
│   ├── budget.py                # Token-Budget-Gate (reuse token_meter)
│   ├── research_tick.py         # expliziter echter P4-Trigger + no_trade_reason
│   ├── reconcile.py             # CLOSED_BY_BROKER P&L-Nachzieh-Pass (idempotent)
│   └── runner.py                # die Loop / der Daemon-Orchestrator
├── webui/
│   ├── api.py                   # FastAPI read-only Endpoints + Control (schreibt Kill/Command)
│   └── static/{index.html,app.js,style.css}
├── scripts/
│   ├── wiring.py                # Composition Root: voller P1–P7-Stack + SchedulerRunner
│   ├── run.py                   # python -m scheduler.run Entry
│   ├── run_scheduler.sh         # dokumentierter Start in entsperrter Session
│   ├── smoke_test.py            # 1 simulierter Tag, Fake-Clock, kein echter Trade
│   └── live_test.py             # echter unbeaufsichtigter Zyklus gegen IG Demo (nicht in CI)
└── tests/                       # gemockt, kein Netz, kein echtes LLM, kein echter sleep
```

> **One file = one responsibility.** Killswitch ist ein eigenes Mini-Modul, weil `safety`
> (Leser) und `webui` (Schreiber) es teilen.

> **⟳ Angepasst 2026-06-28 (Modul 2 `exceptions.py` gebaut, Code = Source of Truth):** Das
> „…" hinter `SchedulerError, PreflightError` bleibt **bewusst leer** — die einzige custom
> Raise-Stelle ist `runner.preflight()` (`PreflightError`, fail-closed Keyring/Broker/DB). Alle
> anderen Module returnen Werte oder fehlschlagen fail-closed **ohne** Re-raise (`safety`→
> `(bool, reason)`, `budget`→`bool`, `reconcile`/`research_tick`→`logger.critical`, `killswitch`/
> `state` self-heal). Spekulative `StateError`/`BudgetError` wären jetzt toter Code → die Datei
> wächst pro Modul, falls ein späteres genuin einen neuen Typ braucht. `code`-Class-Attr-Muster
> wie P5/P6/P7. **6 Tests grün** (Paket-Suite 10+6=16).

---

### 1. `config.py` + Tests

```python
@dataclass(frozen=True)
class SchedulerConfig:
    # Zeit
    window_open: time            # default aus P5-Config (09:30 CET)
    window_close: time           # default 11:19 CET
    tz: str = "Europe/Berlin"
    cycle_interval_min: int = 5
    idle_poll_min: int = 5
    pre_open_lead_min: int = 10          # wie früh Session aufwärmen
    # Caps / Safety
    account: str = "demo"                # HART: Auto-Confirm verweigert alles != "demo"
    max_trades_per_day: int = 5
    daily_loss_cap: float | None = None  # MUSS gesetzt werden — None => Breaker inaktiv (loud warn)
    max_consecutive_failures: int = 3
    backoff_base_s: float = 30.0
    backoff_cap_s: float = 600.0
    # Budget
    daily_token_budget: int | None = 200_000  # ⟳ 2026-06-29 (Code=Wahrheit): Default war None
                                               # (Breaker aus). Nach dem ersten Live-Lauf bewusst auf
                                               # 200_000 geflippt (Operator-Entscheidung): ein v1-
                                               # Runaway-Breaker ≈ €0.8/Tag (Sonnet-Research-Rate, die
                                               # eine Endlosschleife dominiert) — by-default scharf,
                                               # damit der Daemon kosten-sicher ist, auch wenn der Flag
                                               # vergessen wird. None = explizit deaktiviert.
    # Reconcile
    reconcile_interval_min: int = 15
    # Pfade
    live_db_path: str = "data/trading_bot.sqlite"
    state_path: str = "data/state/scheduler_state.json"
    kill_path: str = "data/state/KILL"
    command_path: str = "data/state/scheduler_command.json"
```

- Tests (≥3): Defaults korrekt; `account != "demo"` ist erlaubt zu konstruieren, aber `safety`
  verweigert (nicht hier hart fehlschlagen — Trennung der Verantwortung); `daily_loss_cap=None`
  erzeugt eine geloggte WARNING-Markierung (kein Crash).

> **⟳ Angepasst 2026-06-28 (Modul 1 gebaut, Code = Source of Truth) — zwei Reconciliations:**
> 1. **Handelsfenster = volles Marktfenster `09:00`–`17:30`** (Operator-Entscheidung 2026-06-28),
>    **nicht** das hier skizzierte `09:30`–`11:19`. Das „aus P5-Config (09:30 CET)" war faktisch
>    falsch: die echte, live-verifizierte P5-`ExecutionConfig.trading_window_start/_end` ist
>    `09:00`/`17:30` (und `external_data.market_hours.is_market_open` läuft ebenso `09:00–17:30`).
>    Das volle Fenster maximiert Trade-Versuche = mehr reale Demo-Daten (die Phasen-Mission). P5s
>    Gate 1 re-checkt `09:00–17:30` unabhängig.
> 2. **Fenster als `HH:MM`-Strings** (`"09:00"`), **nicht** `datetime.time` — gemäß `CLAUDE.md`-
>    Build-Note „Zeitfenster (reuse P5-Strings)" und dem Source-of-Truth-Sibling P5 (Strings, via
>    `gates._parse_hhmm` geparst). Hält ein einziges Parse-Idiom, das `clock.py` (Modul 2)
>    wiederverwendet. — `daily_loss_cap` bleibt Default `None` + lauter `__post_init__`-WARNING
>    (Operator-Produktionswert ≈ €1800 wird erst im Wiring gesetzt). **10 Tests grün.**

### 2. `clock.py` + Tests

```python
class Clock:
    def __init__(self, config, *, now_fn=..., sleep_fn=...): ...
    def now(self) -> datetime: ...                     # tz-aware Europe/Berlin
    def classify(self, now) -> Phase: ...              # PRE_OPEN | WINDOW | POST_WINDOW | IDLE
    def seconds_until(self, target_phase, now) -> float: ...
    def sleep(self, seconds: float) -> None: ...       # delegiert an sleep_fn (Tests: no-op)
```

- Reuse `external_data/market_hours.py` für „ist Handelstag / Markt offen". Wochenende/Feiertag
  → IDLE bis nächster Pre-Open.
- DST: tz-aware Arithmetik, **keine** naiven `timedelta`-Stunden-Hacks.
- Tests (≥6, Fake-`now_fn`): vor Fenster → PRE_OPEN; im Fenster → WINDOW; nach Fenster bis
  Mitternacht → POST_WINDOW; Wochenende → IDLE; `seconds_until(WINDOW)` korrekt über
  Mitternacht; DST-Wechseltag plausibel.

> **⟳ Angepasst 2026-06-28 (Modul 3 gebaut, Code = Source of Truth) — drei Reconciliations:**
> 1. **`classify` ist config-getrieben, `is_market_open` lazy reused.** Decision 2 verlangt
>    Reuse von `market_hours`, aber `is_market_open` vermengt Weekday **und** 09:00–17:30 →
>    es kann nicht allein „heute Handelstag?" um 08:00 (Pre-Open) beantworten, und das
>    Scheduler-WINDOW ist **config-getrieben** (test-überschreibbar), nicht an P3s festes
>    Fenster gekoppelt. ⇒ `classify` = Weekday-Check + config-`window_open/close` (lokales
>    `_parse_hhmm`, von P5 gespiegelt, **nicht** importiert); P3s Prädikat wird als
>    Laufzeit-Guard via `Clock.market_is_open(now)` **lazy** reused — so bleibt `import
>    scheduler.clock` stdlib-only (Import-Isolation bewiesen). v1 **kein Feiertagskalender**
>    (Weekday-Proxy, gleiche P3-Vereinfachung).
> 2. **★ DST-korrekt via UTC-Subtraktion.** `(a-b)` zweier datetimes mit **demselben**
>    `ZoneInfo` rechnet naiv wall-clock (63h für eine Spanne über die Frühjahrs-Umstellung,
>    real 62h). `seconds_until` konvertiert beide Seiten nach UTC vor der Subtraktion →
>    Tests pinnen 62h (Spring-Forward) / 64h (Fall-Back), **nicht** 63h. Exakt das geforderte
>    „keine naiven `timedelta`-Stunden-Hacks".
> 3. **`Phase`-Enum + `market_is_open` ergänzt** die skizzierte API; `seconds_until(IDLE)`
>    wirft `ValueError` (IDLE hat keine Einzel-Start-Zeit; kein Sleep-Target). **19 Tests.**

### 3. `state.py` + Tests

```python
@dataclass
class SchedulerState:
    date: str                    # YYYY-MM-DD Europe/Berlin
    trades_today: int = 0
    realized_pnl_today: float = 0.0
    last_research_ts: str | None = None
    last_reconcile_ts: str | None = None
    consecutive_failures: int = 0
    kill_reason: str | None = None
    last_no_trade_reason: str | None = None

class StateStore:
    def load(self) -> SchedulerState: ...
    def save(self, state) -> None: ...               # atomic write (tmp+rename)
    def rollover_if_new_day(self, state, now) -> SchedulerState: ...  # Counter/Loss reset
    def record_cycle(self, state, result) -> SchedulerState: ...
```

- Atomic write (tmp + `os.replace`) gegen Korruption bei Crash mitten im Schreiben.
- Rollover: bei neuem Datum `trades_today`/`realized_pnl_today`/`consecutive_failures` = 0,
  `kill_reason`/`last_no_trade_reason` zurücksetzen. **Idempotent** über Prozess-Restart.
- Tests (≥5): roundtrip; Rollover resettet Counter; selber Tag resettet **nicht**; atomic write
  überlebt simulierten Teil-Write; `record_cycle` inkrementiert nur bei tatsächlichem Trade.

> **⟳ Angepasst 2026-06-28 (Modul 4 `state.py` gebaut, Code = Source of Truth):**
> 1. **`realized_pnl_today` ist ein best-effort persisted Snapshot, NICHT die Quelle des
>    Loss-Breakers.** `record_cycle` faltet `result.profit_loss` nur ein, wenn das Cycle-Result
>    sie zur Cycle-Zeit trägt — das ist der **TIME_STOP**-Pfad. Verifiziert (Contract E):
>    `CLOSED_BY_BROKER` liefert `profit_loss=None` (erst per Reconcile-Pass / Modul 9 aufgelöst),
>    also kann dieses Feld der DB für broker-geschlossene Trades hinterherhängen. Der
>    **autoritative** Tages-Loss-Breaker (`safety.py`/Modul 5, §5 Punkt 4) liest die heutige
>    realized P&L aus der **DB** (Contract E) und hängt **nicht** an diesem Feld — das vermeidet
>    eine Doppelzähl-Falle und hält Modul 4 self-contained. (Spätere Module dürfen den Breaker
>    **nicht** an diesen Snapshot binden.)
> 2. **`load()` self-heilt, wirft nie** (wie `killswitch`/`state`-Zeile im exceptions-Scope):
>    fehlende Datei → fresh `SchedulerState()`, korrupt/partiell → eine WARNING + fresh state;
>    unbekannte Keys gedroppt, fehlende defaulted (forward/backward-compat). `rollover` behält
>    `last_research_ts`/`last_reconcile_ts` (last-action ts), resettet nur Day-Counter +
>    `kill_reason`/`last_no_trade_reason`; resettet das **State-Feld** `kill_reason`, **nicht**
>    die `KILL`-Datei (die gehört `killswitch.py`). `record_cycle` ist duck-typed (kein
>    `execution`-Import). **18 Tests grün** (Paket-Suite 53).

### 4. `killswitch.py` + Tests

```python
def is_set(kill_path) -> bool: ...
def set_kill(kill_path, reason: str) -> None: ...     # schreibt Datei mit Reason+Timestamp
def clear_kill(kill_path) -> None: ...
def read_reason(kill_path) -> str | None: ...
```

- Datei-Existenz = Wahrheit. Auto-Auslösung (Backoff) schreibt Reason `auto:backoff`,
  UI/Operator schreibt `manual:<text>`.
- Tests (≥4): set→is_set True; clear→False; reason roundtrip; fehlende Datei → kein Crash.

> **⟳ Angepasst 2026-06-28 (Modul 5 `killswitch.py` gebaut, Code = Source of Truth):**
> Implementierungs-Klärungen zu den §4-Signaturen (alle benign, fail-soft):
> - **Inhalt = JSON `{"reason", "ts"(UTC ISO)}`** (das „Reason+Timestamp" konkretisiert) —
>   konsistent mit `scheduler_state.json`, sauberer `read_reason`-roundtrip.
> - **`is_set` = reine Existenzprüfung**, robust gegen jeden Inhalt (leeres `touch`,
>   halb-geschrieben → beide „halted"; fail-safe Richtung). **`set_kill` atomic** (`.tmp`+
>   `os.replace`, Paket-Pattern) + mkdir parent. **`clear_kill`** = `unlink(missing_ok=True)`.
> - **`read_reason` fail-soft, wirft nie**: missing/empty/unparseable → `None`; JSON-Objekt →
>   `"reason"`; Plain-Text → stripped raw (Operator-Hand-Reason); unlesbare existierende Datei
>   → eine WARNING + `None`. Der laute Trip-Log bleibt im **Runner** (Loop loggt `critical`),
>   killswitch ist im Happy-Path still (one file = one responsibility).
> - **Als Modul-Namespace exportiert** (`from scheduler import killswitch` → `killswitch.is_set
>   (...)`, wie die §10-Loop-Skizze), **nicht** als bare Funktionen am Paket-Root. **12 Tests
>   grün** (Paket-Suite 65). Stdlib-only (json/os/datetime/pathlib/logging), import-isoliert.

### 5. `safety.py` + Tests — **das Auto-Confirm-Gate (Code, kein AI)**

```python
class AutoConfirm:
    """confirm_fn-Ersatz für P5-Human-Confirm. Gibt True NUR bei allen harten Bedingungen."""
    def __init__(self, config, state_store, kill_path, budget): ...
    def can_open(self, state) -> tuple[bool, str | None]:
        """Pre-Cycle-Check VOR Research/Cycle (spart LLM-Tokens). Reason bei False."""
    def __call__(self, order_ctx) -> bool:
        """Final-Gate unmittelbar vor place_order (an executor.run als confirm_fn übergeben)."""
```

Harte Bedingungen (alle müssen erfüllt sein, sonst `False` + Reason):
1. **`config.account == "demo"` UND** `order_ctx.account == "demo"` (Doppel-Check, strukturell
   fail-closed; alles andere → `False`, `logger.critical`). **Niemals** Auto-Confirm gegen Live.
2. Kill-Switch nicht gesetzt.
3. `state.trades_today < config.max_trades_per_day`.
4. **Tages-Loss-Breaker:** `config.daily_loss_cap is not None` und
   `state.realized_pnl_today > -daily_loss_cap`. Ist der Cap `None` → **eine laute WARNING**
   beim Start, aber kein Block (du setzt den Wert bewusst — siehe offene Notiz unten).
5. Budget nicht überschritten (`budget.is_exhausted()` False).

> **⚠ Offene Notiz für Niklas (Decision 9 + 10):** `daily_loss_cap` und
> `max_consecutive_failures` sind die zwei Werte, die du **bewusst** setzen wolltest. Vorschlag
> Testrun: `daily_loss_cap` = das, was du an einem Demo-Tag maximal „verlieren" willst, bevor
> der Bot bis morgen pausiert (z. B. 3× `initial_risk` eines Trades). `max_consecutive_failures
> = 3`: ein transienter Blip soll nicht den Tag killen, drei Fehler in Folge sind strukturell
> (Auth/Keyring/DB) → lieber stoppen. Beide config-overridable; im Plan als Platzhalter, finaler
> Wert beim Wiring.

- Tests (≥8, gemockt): demo+alle ok → True; `account="live"` → False + critical; Kill gesetzt →
  False; Trade-Cap erreicht → False; Loss über Cap → False; Loss-Cap None → True + WARNING;
  Budget erschöpft → False; `can_open` und `__call__` konsistent.

> **⟳ Angepasst 2026-06-28 (Modul 6 `safety.py` gebaut, Code = Source of Truth) — drei
> Reconciliations + zwei Design-Entscheidungen:**
> 1. **Konstruktor bekommt ein 5. Arg `realized_pnl_today`.** Die §5-Skizze ist
>    `AutoConfirm(config, state_store, kill_path, budget)` — aber der eigene Loss-Breaker (§5
>    Punkt 4) + Contract E verlangen die heutige realized P&L **aus der DB**, wofür diese
>    Signatur keine Quelle hat. Das injizierte `realized_pnl_today: Callable[[str], float]`
>    (session_date → €) ist der minimale, phasen-isolierte Weg (kein P2-Import in `safety`; das
>    Wiring backt die Closure mit `SELECT COALESCE(SUM(profit_loss),0) FROM trade_outcomes WHERE
>    session_date=? AND profit_loss IS NOT NULL`). **Nicht** an `state.realized_pnl_today` hängen
>    (Snapshot-Falle, s. Modul-4-Reconciliation: `CLOSED_BY_BROKER` liefert `profit_loss=None`).
> 2. **Der §5-`order_ctx.account=="demo"`-Doppel-Check entfällt.** Contract D: der `OrderPlan` trägt
>    **kein** `account` → Demo-Lock ist **config-only** (`config.account`); `__call__(plan)` liest
>    **nichts** vom Plan. Strukturelle zweite Hälfte (nur `ig_demo`-Broker) lebt im Wiring.
> 3. **`budget` ist ein duck-typed `Budget`-Protocol** (`is_exhausted() -> bool`), **nicht** die
>    konkrete Modul-7-Klasse — `safety` (Modul 6) wird **vor** `budget.py` (Modul 7) gebaut (per
>    Operator-Sondernotiz: „stub via Protocol" statt Modul 7 vorziehen). Modul 7s `TokenBudget`
>    erfüllt das Protocol; Tests reichen einen Fake (spiegelt `CycleResult` in `state.py`).
> - **Design A — Loss-Breaker-DB-Read fail-CLOSED:** wirft der P&L-Reader (DB unreachable), wird
>   der Trade **geblockt** (`REASON_LOSS` + `critical`) — wir können nicht beweisen, dass wir unter
>   dem Cap sind ⇒ nicht traden (ein späterer Zyklus re-evaluiert + erholt sich). „Im Zweifel nicht
>   traden", die sichere Richtung.
> - **Design B — eigene WARNING bei `daily_loss_cap=None` beim Konstruieren** (Logger
>   `scheduler.safety`), zusätzlich zur `config.py`-WARNING: `config` warnt vor dem **Wert**,
>   `safety` warnt, dass **sein Gate** deaktiviert ist (eine WARNING pro Verantwortung; in einem
>   Safety-Modul ist die laute Selbst-Dokumentation eines abgeschalteten Gates gewollt).
> - **Reason-Codes** (`REASON_NOT_DEMO/KILL/CAP_BLOCK/LOSS_BREAKER/BUDGET`) als Modul-Konstanten →
>   `state.last_no_trade_reason` (§10-Loop); Gate-Reihenfolge most-structural-first
>   (demo → kill → cap → loss → budget). **18 Tests grün** (Paket-Suite 83).

### 6. `backoff.py` + Tests

```python
class BackoffTracker:
    def __init__(self, config): ...
    def record_success(self, state) -> SchedulerState: ...   # consecutive_failures = 0
    def record_failure(self, state) -> SchedulerState: ...    # +1
    def should_trip(self, state) -> bool: ...                 # >= max_consecutive_failures
    def delay_s(self, state) -> float: ...                    # min(base*2^(n-1), cap)
```

- **Begründung Schwellwert (#9):** Fehler werden **klassifiziert**, nicht blind gezählt — aber
  für v1 reicht „konsekutive Cycle-Exceptions". Transiente (Netz/5xx/Timeout) sollen das Backoff
  erhöhen, ein Erfolg resettet. Erst `max_consecutive_failures` (Default 3) in Folge → Trip
  (Kill-Switch `auto:backoff` + sauberer Shutdown). Für einen **Demo-Datensammler** ist ein
  Trip billig (Neustart am Folgetag), also bewusst eher früh tripsen als einen still hängenden
  oder dauer-fehlschlagenden Bot laufen lassen.
- Tests (≥5): Erfolg resettet; 3 Fehler → should_trip True; 2 Fehler → False; `delay_s` wächst
  exponentiell und respektiert `backoff_cap_s`; Reset nach Erfolg setzt delay zurück.

> **⟳ Angepasst 2026-06-28 (`backoff.py` gebaut, Code = Source of Truth) — drei
> Reconciliations:**
> 1. **Advisory, nicht selbst-trippend.** Die §6-Notiz „Trip → Kill-Switch `auto:backoff` +
>    sauberer Shutdown" — aber `BackoffTracker` **setzt den Kill-Switch nie selbst**; er meldet
>    nur `should_trip`. Der **Runner** (§10-Loop) ruft `killswitch.set_kill(..., "auto:backoff")`
>    + `shutdown()`. Single-responsibility (spiegelt den killswitch-Trip-Log, der ebenfalls im
>    Runner lebt, nicht in `killswitch.py`).
> 2. **`delay_s` ist total — `n <= 0 → 0.0`.** Die Skizze `min(base·2^(n-1), cap)` ist bei `n=0`
>    undefiniert; der Guard macht die Methode jederzeit sicher aufrufbar (die Loop ruft sie real
>    nur nach `record_failure`, also `n >= 1`). Der `cap` bound't das Ergebnis (kein
>    Overflow-Guard nötig).
> 3. **Mutate-and-return** (dasselbe Objekt), konsistent mit `state.record_cycle`/`research_tick`;
>    der Runner ist der einzige Persistenz-Eigentümer. `record_*` berühren **nur**
>    `consecutive_failures` (nicht `kill_reason`/Counter/`last_no_trade_reason`). **9 Tests grün**
>    (Paket-Suite 106 → 115). Fehler-**Klassifikation** (transient vs. strukturell) bleibt
>    bewusst v1-deferred (reine konsekutive Cycle-Exceptions).

### 7. `budget.py` + Tests

```python
class TokenBudget:
    def __init__(self, config, token_meter): ...
    def consumed_today(self) -> int: ...            # aus 8-Feld token_meter / llm_usage.json
    def is_exhausted(self) -> bool: ...             # consumed >= daily_token_budget
```

- Reuse `token_meter` / `llm_usage.json` (P4/P6). `daily_token_budget=None` → nie erschöpft
  (+ WARNING). Tagesgrenze Europe/Berlin konsistent mit `state`-Rollover.
  ⟳ **2026-06-29 (Code=Wahrheit):** Der Default ist jetzt `200_000` (≈ €0.8/Tag Runaway-Breaker,
  scharf by-default) statt `None`; `None` bleibt als **expliziter** Deaktivierungs-Sentinel
  (`--no-token-budget` in `scheduler/run.py`, `--token-budget 0` in `live_test.py`). Grund: der
  erste Live-Lauf (2026-06-29) lief mit deaktiviertem Budget → der Breaker soll nicht erst per
  vergessenem Flag scharf werden.
- Tests (≥3): unter Budget → False; über → True; None → False + WARNING.

> **⟳ Angepasst 2026-06-28 (Modul 7 `budget.py` gebaut, Code = Source of Truth) — vier
> Reconciliations:**
> 1. **Konstruktor `TokenBudget(config, usage_log_path, *, now_fn=None)`, nicht `(config,
>    token_meter)`.** Das P4-`token_meter`-Modul hat **kein** Read-API → nichts zu injizieren (die
>    §-eigene Notiz „Kein Reader → budget.py summiert selbst" bestätigt das). `budget.py` liest die
>    `llm_usage.json` direkt (fail-soft, spiegelt `usage_report.load_records`/`token_meter._load_log`).
>    Der Konstruktor braucht **wo** (`usage_log_path`, vom Wiring — wie `safety.py` `kill_path`
>    explizit nimmt) + **die Tagesgrenze** (`now_fn`, tz-aware, deterministische Tests). **Kein
>    Edit an `config.py`/Modul 1** (kein `usage_log_path`-Feld — minimal gehalten).
> 2. **Berlin-Tagesgrenze aus einem UTC-`ts`.** `token_meter` schreibt `ts` **UTC** mit `Z`-Suffix
>    (`"…Z"`), die Daemon-Tagesgrenze ist aber `config.tz` (konsistent mit `state`-Rollover) → jeder
>    Record-`ts` wird **vor** dem `.date()` nach `config.tz` konvertiert (ein `22:30Z`-Call zählt zum
>    nächsten Berlin-Tag, CEST +2). Stdlib-only (`datetime.fromisoformat` + `Z`→`+00:00` + `zoneinfo`);
>    `research.timeutil` **nicht** importiert → `import scheduler.budget` zieht **NONE** cross-phase.
> 3. **Token-Maß = alle vier billed Felder** (`input_tokens` + `output_tokens` +
>    `cache_creation_input_tokens` + `cache_read_input_tokens`), tolerant gegen fehlende Keys
>    (ältere 6-Feld-Records ohne `cache_*` → 0). So undercountet das Budget nie (P6 cached →
>    `cache_* > 0`). v1, am echten Output tunbar.
> 4. **Advisory-Budget = fail-OPEN** (fehlende/korrupte Log → `consumed 0` → nicht erschöpft →
>    Cycles erlaubt) — bewusst **anders** als der fail-CLOSED Loss-Breaker in `safety.py`: das Budget
>    ist eine Kosten-Kappe, kein Geld-Safety-Gate, und der Meter selbst ist „advisory, never break a
>    pick". `is_exhausted()` **wirft nie** (das Auto-Confirm-Gate vertraut dem Bool). **13 Tests grün**
>    (Paket-Suite 96), inkl. Protocol-Handoff (echtes `TokenBudget` als `AutoConfirm.budget` → BUDGET).

### 8. `research_tick.py` + Tests — **autonome Kandidaten (der Blocker)**

```python
class ResearchTick:
    def __init__(self, research, state_store): ...   # research = echte P4-Research-Instanz
    def ensure_candidates(self, state) -> ResearchResult:
        """Triggert echtes P4-Research, schreibt frische turbo_candidates.json (1 | []).
        Erfasst no_trade_reason bei Abstain. NIE seed_candidate.py."""
```

- Nutzt **ausschließlich** die echte `Research.run()` (über P4-Wiring) — **kein** manueller Seed
  → kein „DIES IST EIN MANUELL ERSTELLTER SEED"-Marker → Judge kann handeln statt zwangs-ABSTAIN.
- `no_trade_reason` (minimal, Decision 5): `EMPTY_UNIVERSE | LLM_ABSTAIN | VALIDATOR_REJECT |
  FILTER_FAIL | PREFLIGHT_FAIL` aus dem Research-Ergebnis ableiten, in `state.last_no_trade_reason`
  + stderr. Volles typisiertes Signalmodell (RESEARCH_V3 §4.1–4.4) bleibt **P9**.
- **Freshness-Disziplin (Decision 4 + Step 1.3):** schreibt frische Candidates, sodass das
  nachfolgende `executor.run()` an Gate 2 **nicht** erneut Research callt. Bei Abstain →
  `save_candidates([])` (frische leere Liste) → Gate 2 = NO_TRADE ohne Re-Call.
- Tests (≥5, gemockt): PASS-Pick → fresh Candidate geschrieben, kein Marker; Abstain → `[]` +
  `reason_code`; Research-Exception → fail-closed `[]` + `reason_code=PREFLIGHT_FAIL`;
  `test_no_manual_seed_marker` (aus Step 1.1); `last_research_ts` aktualisiert.

> **⟳ Angepasst 2026-06-28 (Modul 8 `research_tick.py` gebaut, Code = Source of Truth) — zwei
> Reconciliations:**
> 1. **★ Das 5-Code-`no_trade_reason`-Modell kollabiert in v1 auf ZWEI Buckets (Reconciliation
>    H).** `Research.run()` returnt **nur** `list[Candidate]` (`[]` | `[pick]`) — **keine**
>    Begründung; der granulare Grund (empty universe / LLM-error / validator-reject / valid
>    abstain / filter-reject) wird nur per `log.info` auf stderr geschrieben
>    (`phase4_research/research/research.py`). Aus dem Rückgabewert sind nur **pick / abstain
>    (`[]`) / exception** unterscheidbar ⇒ v1 setzt `PREFLIGHT_FAIL` (run() wirft) oder
>    `LLM_ABSTAIN` (run() → `[]`, der Umbrella für **alle** Abstain-Ursachen). `EMPTY_UNIVERSE`/
>    `VALIDATOR_REJECT`/`FILTER_FAIL` sind als Konstanten **deklariert, aber reserviert für P9**
>    (RESEARCH_V3, wenn P4 einen Grund zurückgibt) — exakt Decision 5 („minimal jetzt, volles
>    Modell = P9"); `safety.py` dokumentiert genau diese Trennung bereits (Gate-Block-Taxonomie
>    vs. No-Candidate-Taxonomie).
> 2. **Konstruktor `ResearchTick(research, *, now_fn=None)`** statt `(research, state_store)`.
>    Das Modul **mutiert** nur den übergebenen `SchedulerState` (`last_research_ts`/
>    `last_no_trade_reason`) — dasselbe mutate-and-return-Muster wie `state.record_cycle`/
>    `backoff`; der **Runner** ist der einzige Persistenz-Eigentümer (`finally:
>    state_store.save`, §10). ⇒ `state_store` (ungenutzt) entfällt; ein keyword-only `now_fn`
>    kommt dazu (Determinismus-Regel; die Skizze unter-spezifizierte die Timestamp-Quelle). Der
>    fail-closed Clear bei Exception reused das schon injizierte `research.state` (P2
>    `StateManager` → `save_candidates([])`), keine Extra-Dependency. **Freshness ist NICHT
>    hier** (Contract B): der No-op-`research_runner` im Executor (Wiring/Modul 11) verhindert
>    den Gate-2-Re-Call; `research_tick` läuft nur das echte Research **vor** `executor.run()`.
>    **10 Tests grün** (Paket-Suite 96 → 106).

### 9. `reconcile.py` + Tests

```python
class Reconciler:
    def __init__(self, broker, db, reward_sink, state_store): ...
    def tick(self, state) -> ReconcileReport:
        """1) broker.reconcile_positions (orphan PENDING). 2) CLOSED_BY_BROKER ohne Close-Confirm:
        P&L aus get_trade_history nachziehen -> update_trade_close + insert_reward. Idempotent."""
```

- **Idempotent via `deal_id`:** ein bereits geschlossen+gerewardeter Trade wird nicht doppelt
  gebucht. Reuse P7-Retry-Logik (`logger.critical` bei Fehlschlag, kein Re-raise).
- Läuft Startup + alle `reconcile_interval_min` + Shutdown.
- Tests (≥5): orphan PENDING → closed; broker-closed ohne Confirm → P&L nachgezogen + reward
  gebucht; bereits gebucht → **kein** Doppel-Insert (idempotent); History-Fehler → fail-closed,
  Loop läuft weiter; nichts offen → No-op.

> **⟳ Angepasst 2026-06-28 (`reconcile.py` gebaut, Code = Source of Truth) — drei
> Reconciliations:**
> 1. **Konstruktor `Reconciler(reward_sink, pending_reconcile_fn, *, now_fn=None)`** statt
>    `(broker, db, reward_sink, state_store)`. **Beide Reuse-Ziele werden INJIZIERT, nicht
>    importiert** — das ist, was die verifizierte Import-Isolation jedes Scheduler-Moduls wahrt
>    (`import scheduler.reconcile` zieht **NONE** cross-phase): `broker` + die P5-`reconcile_startup`
>    falten in eine zero-arg `pending_reconcile_fn`-Closure (das Wiring/Modul 11 bindet
>    `execution.order.reconcile_startup` über den geteilten broker/exec_state/`ExecutionConfig` am
>    Composition-Root, wo Cross-Phase-Imports erlaubt sind); `db` entfällt (`reward_sink` besitzt es —
>    `reconcile_open_trades` ist self-contained); `state_store` entfällt (mutiert
>    `state.last_reconcile_ts`, der **Runner** persistiert — wie `research_tick`/`record_cycle`/
>    `backoff`); `now_fn` kommt dazu (Determinismus). Muster wie `safety.Budget`/`state.CycleResult`/
>    `research_tick._ResearchLike`.
> 2. **Komposition, keine Reimplementierung** (Contract F): `reconcile_open_trades` macht den
>    History-Resolve → `update_trade_close` + `insert_reward` **bereits** (idempotent via OPEN/CLOSED-
>    Status). `reconcile.py` re-implementiert die §9-„Schritt-2"-SQL **nicht** — es ruft die getestete
>    P7-Methode. Beide Hälften fail-closed (je `logger.critical`, kein Re-raise; eine raisende Hälfte
>    überspringt die andere nie).
> 3. **Die orphan-PENDING-Hälfte ist teil-redundant** mit dem executor-eigenen per-Cycle
>    `reconcile_startup`; der Scheduler-Pass ergänzt die **Between-Window**-Abdeckung + den P&L-
>    Nachzieh, den der Executor nicht macht. **Scheduling** (Startup/periodisch/Shutdown) ist der
>    Runner (§10); die Closure bauen + Broker teilen ist das Wiring (Modul 11). **7 Tests grün**
>    (Paket-Suite 115 → 122).

### 10. `runner.py` + Tests — **die Loop**

```python
class SchedulerRunner:
    def __init__(self, *, clock, state_store, killswitch_path, auto_confirm, backoff,
                 budget, research_tick, reconciler, executor, broker, config): ...
    def preflight(self) -> None:
        """Fail-closed: Keyring erreichbar (get_credential), broker.connect ok, DB/Migrations da.
        Bei Fehler -> PreflightError -> sauberer Exit (KEIN Trade-Versuch)."""
    def run(self) -> None: ...        # die Hauptschleife
    def shutdown(self) -> None: ...   # final reconcile + Session sauber schließen
```

Loop-Skizze (alles deterministisch):

```
preflight()                                  # fail-closed, sonst Exit
while True:
    now = clock.now()
    state = state_store.rollover_if_new_day(state, now)
    if killswitch.is_set(kill_path):
        log.critical("kill switch set: %s", reason); shutdown(); break
    phase = clock.classify(now)
    try:
        if phase == PRE_OPEN:
            broker.ensure_session(); reconciler.tick(state)
            clock.sleep(min(seconds_until(WINDOW), idle_poll))
        elif phase == WINDOW:
            broker.ensure_session()
            reconciler.tick(state)                       # broker-closes aus letztem Cycle
            ok, reason = auto_confirm.can_open(state)    # Pre-Cycle-Gate (spart Tokens)
            if ok:
                research_tick.ensure_candidates(state)   # echtes P4, frische Candidates
                result = executor.run()                   # P4->P6->P5->P7 voll; bare run()
                                                         # (Finding A: confirm_fn=AutoConfirm ist am
                                                         #  Konstruktor injiziert, NICHT hier)
                state = state_store.record_cycle(state, result)
            else:
                state.last_no_trade_reason = reason      # z.B. CAP_BLOCK / KILL / BUDGET
            backoff.record_success(state)
            clock.sleep(cycle_interval)
        elif phase == POST_WINDOW:
            reconciler.tick(state)                        # finaler Nachzieh-Pass
            clock.sleep(seconds_until(next PRE_OPEN))
        else:  # IDLE
            clock.sleep(idle_poll)
    except Exception:
        log.critical("cycle failure", exc_info=True)
        state = backoff.record_failure(state)
        if backoff.should_trip(state):
            killswitch.set_kill(kill_path, "auto:backoff"); shutdown(); break
        clock.sleep(backoff.delay_s(state))
    finally:
        state_store.save(state)
```

- **Kein echter `sleep` in Tests** — `clock.sleep` ist no-op über `sleep_fn`; der Test treibt die
  Zeit über `now_fn` und bricht die Schleife nach K Iterationen (injizierbare Stop-Bedingung).
- Tests (≥8): voller simulierter Tag (PRE_OPEN→WINDOW→POST_WINDOW→IDLE); Research wird im Fenster
  getriggert; nach `max_trades_per_day` keine weiteren Trades (CAP_BLOCK); Kill-Switch stoppt die
  Loop + ruft shutdown; 3 Cycle-Exceptions → Backoff-Trip → KILL + shutdown; transiente Exception
  → Backoff-Sleep, dann weiter; `preflight`-Fail → Exit ohne Trade-Versuch; `state` wird in
  `finally` immer gespeichert.

> **⟳ Angepasst 2026-06-28 (Modul 10 `runner.py` gebaut, Code = Source of Truth) — sechs
> Reconciliations + 16 Tests:**
> 1. **`broker.ensure_session()` → privates `_warm_session()`.** Die §10-Skizze ruft
>    `broker.ensure_session()`, aber die Methode **existiert nicht** — der P1-Adapter hat
>    `is_connected()`/`connect()→Envelope`/`disconnect()` (`ig_adapter.py:137,157,178`). Der Runner
>    komponiert das Warmup aus den echten Methoden („falls nicht connected, connect; raise bei
>    `not env['ok']`"). Raise in der Loop → caught → Backoff; in `preflight`/`shutdown` vom Caller
>    gewrapped/geguarded.
> 2. **Konstruktor droppt `budget`.** Das Budget-Gate sitzt schon in `auto_confirm.can_open()`
>    (Modul 6 hält das Budget) — die Loop ruft Budget nie direkt ⇒ ungenutzte Dependency. Gleiche
>    „drop the unused injected dep"-Disziplin wie `reconcile.py` (db/state_store) /
>    `research_tick.py` (state_store).
> 3. **★ Cross-Phase-Preflight-Probes werden INJIZIERT, nicht inlined.** Die §10-`preflight`-Skizze
>    inlined `get_credential` + DB/Migrations-Check. Um die bewiesene Import-Isolation (`import
>    scheduler.runner` zieht NONE cross-phase) **und** die 100%-Unit-Testbarkeit zu wahren, nimmt
>    der Runner ein keyword-frei `preflight_fn: Callable[[], None]` (wirft bei Fehler), das das
>    Wiring (Modul 11) mit den Keyring- + DB-Checks backt — exakt das Muster, das `safety.py`
>    (`realized_pnl_today`-Closure) und `reconcile.py` (`pending_reconcile_fn`-Closure) etabliert
>    haben. `broker.connect()` macht der Runner zusätzlich selbst (er hält den Broker für das
>    Loop-Warmup ohnehin).
> 4. **`killswitch_path` → `config.kill_path`** (der Runner hält die Config; kein separater
>    Pfad-Arg wie in der §10-Skizze).
> 5. **Stop-Bedingung = keyword-only `max_iterations: int | None = None`** (Default None ⇒ echter
>    Endlos-Daemon; Tests übergeben K — die §10-„bricht die Schleife nach K Iterationen").
>    `now_fn`/`sleep_fn` sind bereits über den `Clock` injiziert.
> 6. **`reconcile_interval_min` via kleinem Throttle** (`_maybe_reconcile`/`_due`, UTC-Compare,
>    DST-sicher) — die 5-min-WINDOW-Kadenz hämmert nicht jeden Cycle `get_trade_history`; Reconcile
>    ist **forced** bei Startup, POST_WINDOW, Shutdown (Decision 11: „Startup + periodisch +
>    Shutdown"). Idempotent ⇒ Über-Laufen ist nur Kosten, nie Korrektheit.
> — **16 Tests grün** (Paket-Suite 122 → **138**): deterministisch über einen echten `Clock` mit
> stepping `now_fn` (1 Aufruf/Iteration, weil alle Kollaboratoren Fakes sind, die `clock.now` nicht
> rufen) + recording `sleep_fn` + `max_iterations`; **echter `AutoConfirm`/`BackoffTracker`** in den
> CAP-/Backoff-Tests (beweist das Zusammenspiel). Sibling-Suiten grün + unberührt (P1 52 · P2 62 ·
> P4 94 · P5 146 · P6 70 · P7 128).

### 11. `scripts/`

- **`wiring.py`** — Composition Root. Erweitert P7-`wiring.py`: baut echten `IGAdapter`
  (Demo-Keyring), `Database`(`live_db_path`), `StateManager`, `MarketDataFetcher`
  (`register_volume_proxy("EXS1.DE")`), `Research` (P4-Factory), `debate_runner` (P6),
  `reward_sink` (P7), dann `Clock`/`StateStore`/`AutoConfirm`/`BackoffTracker`/`TokenBudget`/
  `ResearchTick`/`Reconciler`/`Executor` → `SchedulerRunner`. Eine Factory
  `build_scheduler(config) -> SchedulerRunner`. **`account="demo"` hart gesetzt.**
- **`run.py`** — `python -m scheduler.run`: lädt Config, `build_scheduler`, `runner.run()`.
  SIGTERM/SIGINT-Handler → `shutdown()` (sauberer Stop, kein orphan).
- **`run_scheduler.sh`** — startet `run.py` **in einer entsperrten interaktiven Session**
  (damit gnome-keyring/Secret-Service erreichbar ist). Kommentar-Block mit der Background/
  Headless-Warnung (siehe Deployment-Note unten).
- **`smoke_test.py`** — ein simulierter Tag mit Fake-Clock + gemocktem Broker/Research/Executor,
  **kein** echter Trade. Druckt Phasen-Übergänge, Cap-Verhalten, Kill-Verhalten. Schnell, manuell.
- **`live_test.py`** — **echter** unbeaufsichtigter Lauf gegen IG Demo: startet im (oder kurz vor)
  Fenster, triggert echtes Research, lässt den vollen Zyklus laufen, prüft dass entweder ein
  realer Demo-Trade in `trade_outcomes`/`reward_pts`/`trade_lessons` landet **oder** ein
  dokumentierter `no_trade_reason` geschrieben wird, und dass ein sauberer Stop + Reconcile
  passiert. Hart asserted, `exit 0` = PASS. **Nicht** in CI.

> **⟳ Angepasst 2026-06-28 (Modul 11 gebaut, Code = Source of Truth) — acht Reconciliations:**
> 1. **Wiring repliziert die P4/P6/P7-Builder inline** (aus `research`/`debate`/`reward`), importiert
>    **nicht** deren `scripts.wiring` (`scripts.wiring`-Namenskollision P4/P5/P6/P7/P8) — exakt wie P7
>    `build_executor` replizierte statt P5 zu importieren. Baut den **vollen** Zyklus: Debatte **und**
>    Reward **beide** in EINEN Executor (die §11-Zeile „`Research` (P4-Factory)" ist faktisch korrigiert:
>    P4s Factory baut sich einen **eigenen** Broker → P8 baut `Research` direkt mit dem **geteilten**
>    Broker, Contract G).
> 2. **`run.py` lebt im Paket (`scheduler/run.py`), NICHT `scripts/`** — `python -m scheduler.run`
>    (§19-Entry) braucht es installiert (`pyproject include=["scheduler*"]` schließt `scripts/` aus).
>    Spiegelt `execution/ig_bot.py` + dessen lazy `scripts.wiring`-Import. (Die §11-Liste führte es unter
>    `scripts/` — der dokumentierte Entry diktiert den Paket-Ort.)
> 3. **`run.py`-Signal-Handler → `runner.request_stop()`**, **nicht** `shutdown()` direkt (wie hier
>    skizziert): `shutdown()` braucht den `state` (Loop-intern); ein **additives** non-sticky
>    `SchedulerRunner.request_stop()` (Loop-Top-Check) lässt die Loop sauber stoppen + selbst `shutdown()`
>    rufen. **Bewusst nicht** die KILL-Datei (die wäre sticky → blockt den nächsten Restart). In-Progress-
>    `sleep` läuft v1 erst aus (Latenz; interruptible-sleep = später).
> 4. **Struktureller Demo-Lock im Wiring** (Decision 7/Contract D): `build_scheduler` wirft bei
>    `config.account != "demo"`, baut nur `ig_demo`; `AutoConfirm` re-checkt zur Laufzeit.
> 5. **Alle Daten-Pfade absolut** (via `dataclasses.replace` auf den `<repo_root>/data/`-Baum) → cwd-
>    unabhängig, teilt exakt die Dateien von `init_db.py` + P4–P7 (DB, `scheduler_state.json`, `KILL`,
>    Command, `llm_usage.json`, `execution_state.json`, `cache/`).
> 6. **Die drei Runner-Closures leben im Wiring:** `realized_pnl_today` (DB-`SUM(profit_loss)` via
>    `db.conn`, Contract E) · `pending_reconcile_fn` (P5-`reconcile_startup`, geteilter Broker) ·
>    `preflight_fn` (Keyring `get_credential(IG_DEMO_API_KEY)` + **Migration-002-Check** via `PRAGMA
>    table_info` → `account`; **verifiziert, migriert nicht** — ein Safety-Daemon mutiert kein Schema).
> 7. **EIN geteiltes `now_fn`** durch Clock/Executor/ResearchTick/Reconciler/TokenBudget; der Executor
>    behält sein **eigenes echtes `sleep_fn`** (Monitor muss real warten) — nur die Loop-Kadenz nutzt das
>    injizierte `sleep_fn`. `build_scheduler(config, *, now_fn=None, sleep_fn=None, max_iterations=None,
>    exec_config=None)` — die Injektions-Parameter erlauben `live_test` (kurzer Hold, gebundene Loop).
> 8. **`smoke_test` = offline Sim-Tag mit Fakes** (Konzept-treu §11: „Fake-Clock + gemockter Broker/
>    Research/Executor") — bewusste Abweichung vom P5/P6/P7-„real dry stack", weil der Loop-Wert die
>    Mechanik (Phasen/Cap/Kill) ist. **Lokal gelaufen: 3/3, exit 0.** `live_test` ist lenient (No-Trade =
>    valider PASS, P5/P6/P7-Disziplin), hart nur: sauberer Stop + State persistiert + (falls CLOSED-Trade)
>    `reward_pts` vorhanden.
> — **146 Tests grün** (Paket-Suite 138 → 146: +2 `request_stop`, +6 `test_run`). `import scripts.wiring`/
> `scheduler.run` ziehen **NONE** cross-phase beim Laden (alle Cross-Phase-Imports lazy in den Funktionen).
> Sibling-Suiten grün + unberührt (P1 52 · P2 62 · P4 94 · P5 146 · P6 70 · P7 128).

### 12. Web-UI (`webui/`) — **zuletzt, read-mostly**

> **✅ gebaut 2026-06-28 (Code = Source of Truth) — Reconciliations:**
> (a) **Visual = Dark-Neumorphism** (Operator-Entscheidung): GitHub-Dark-Palette aus den Konzept-SVGs
> als Canvas + die weiche Neumorphism/Glass-Tiefe aus `phase8_scheduler/ui_concept/`; Monospace
> (offline-sichere System-Stack, **kein** CDN-Fetch), kein Emoji; Polling **7 s**.
> (b) **`POST /api/command` ist real verdrahtet** (Operator wollte funktionierende Start/Stop): der
> „# Daemon pollt"-Hinweis ist jetzt umgesetzt — neues `scheduler/command.py` (geteilt webui-Schreiber/
> runner-Leser) + ein **additiver** Loop-Top-Check in `runner.py`. `stop` = **weiche, reversible Pause**
> (Daemon-Prozess bleibt am Leben, kein Trade-Work bis `start`/Löschen), KILL bleibt der **harte** Stop.
> Keine Command-Datei ⇒ Loop bit-identisch. **PAUSED** wird von der UI direkt aus der Command-Datei
> abgeleitet (kein `state.py`-Feld nötig → Modul 4 unberührt); `running_state` = HALTED>PAUSED>RUNNING.
> (c) **`webui` ist NICHT installiert** (pyproject `include=["scheduler*"]`); `run_webui.sh` setzt
> `PYTHONPATH=phase8_scheduler`, Tests via pytest-`sys.path`. (d) Confidence reused P7
> `select_edge_set`+`compute_confidence` (`ConfidenceReport.state`/`win_rate_wilson_lb`); cross-phase
> `reward`-Import **lazy im Endpoint** → `import webui.api` zieht nur `fastapi`+`scheduler.*`+stdlib.
> 13 `test_webui`-Tests inkl. read-only-Connection-rejects-write-Isolationsbeweis; **P8 171 grün.**

```python
# webui/api.py  (FastAPI, bind 127.0.0.1)
GET  /api/status        -> Scheduler-Phase, running?, kill_reason, heute Trade-Count/Cap, Backoff
GET  /api/score         -> Score-Verlauf (aus reward_pts)
GET  /api/confidence    -> Confidence-Status + N (observe-only, INSUFFICIENT/OK)
GET  /api/lessons       -> letzte N trade_lessons
GET  /api/trades        -> offene + geschlossene Trades (trade_outcomes)
GET  /api/last_cycle    -> letzter Cycle + no_trade_reason
POST /api/kill          -> schreibt KILL-Datei (manual:<text>)
POST /api/clear_kill    -> löscht KILL-Datei
POST /api/command       -> schreibt scheduler_command.json (start/stop)   # Daemon pollt
```

- **Strikt read-only DB-Connection** (`sqlite3` mit `mode=ro`), liest `scheduler_state.json`.
  **Kein** direkter Funktionsaufruf in den Trader — Control nur über Kill-/Command-Datei
  (Decision 14). UI-Crash kann den Trader nie berühren.
- **`webui/static/`** — eine `index.html` + `app.js` (Polling 5–10 s, `fetch`) + `style.css`:
  GitHub-Dark, Monospace, **Buttons Richtung Glass-/Neumorphism** (CSS-only, kein Framework),
  kein Emoji. Karten: Status · Score-Sparkline · Confidence · Trades-Tabelle · letzte Lessons ·
  letzter Cycle/Reason · Kill-Toggle.
- **P10-Hook (nur Architektur, nicht bauen):** der `POST /api/command`-Pfad ist generisch genug,
  dass später Aktionen wie `{"cmd":"deep_research"}` ergänzt werden können, ohne das UI-Modell
  umzubauen. Jetzt nur `start`/`stop` implementieren.
- Tests (≥5, FastAPI `TestClient`, gemockte DB/State): `/api/status` Form korrekt; `/api/trades`
  liest read-only; `POST /api/kill` schreibt Datei; `POST /api/clear_kill` löscht; read-only
  Connection wirft bei Write-Versuch (Beweis der Isolation).

---

## Deployment-Note (Q3 — operativer Top-Risk, in `CLAUDE.md` + `run_scheduler.sh`)

Die Box läuft **always-on im Background**. Der einzige reale Stolperstein ist der
**gnome-keyring/Secret-Service-Zugriff**: er braucht eine **entsperrte** Login-Session mit
D-Bus. Da deine Live-Tests auf der Box bereits funktionieren, ist der Keyring in deiner
**aktuellen interaktiven Session** erreichbar. Das Risiko entsteht erst, wenn der Daemon in
einer **nicht-interaktiven** Session startet (reiner Background-Service ohne Session-Bus).

Maßnahmen im Plan:
1. **Fail-closed Keyring-Preflight** (`runner.preflight`): probiert `get_credential` und bricht
   mit klarer, umsetzbarer Fehlermeldung ab, wenn der Secret-Service nicht erreichbar ist — der
   Bot tradet **nie** ohne verifizierten Credential-Zugriff.
2. **v1-Empfehlung:** Daemon in einer persistenten, entsperrten User-Session starten (z. B.
   `tmux` unter eingeloggtem User, oder `systemd --user` mit `loginctl enable-linger` +
   Keyring-Auto-Unlock via PAM). `run_scheduler.sh` dokumentiert das; volles systemd-Hardening
   ist **P9/Ops-Carry-over**, nicht P8.
3. Wenn der Preflight in deinem Background-Setup fehlschlägt, ist das ein **echter Befund** —
   dann klären wir die Session-Strategie, bevor unbeaufsichtigt getradet wird.

---

## Done-Kriterien (Phase-8-Gate)

- `pytest phase8_scheduler/tests/ -v` grün (**≥50 Tests**, Schwerpunkt `test_runner.py` +
  `test_safety.py`).
- **Regression grün** (gegen echtes `pytest` abgleichen): P1 52 · P2 62 · P4 94 · P5 146 · P6 70
  · P7 128. P8 darf keine Vorphase brechen (additive Naht).
- `grep` aus Step 0 sauber; Step-0b-Docs angeglichen; `## Verified contracts`-Block in
  `phase8_scheduler/CLAUDE.md` gefüllt.
- **`test_no_manual_seed_marker`** beweist: echtes Research erzeugt nie den Seed-Marker.
- **`scripts/smoke_test.py`** fährt einen simulierten Tag deterministisch (kein Netz).
- **`scripts/live_test.py`** läuft unbeaufsichtigt gegen IG Demo: triggert echtes Research,
  fährt den vollen Zyklus, schreibt **entweder** einen realen Demo-Trade (`trade_outcomes` CLOSED
  + `reward_pts` + `trade_lessons`) **oder** einen dokumentierten `no_trade_reason`, reconcilet
  broker-closes idempotent, stoppt sauber — und sammelt damit die ersten realen Outcome-Daten.
- Kill-Switch + Backoff-Trip + Tages-Loss-Breaker live nachweisbar (Demo).

---

## Bewusst NICHT in Phase 8 (Carry-overs)

- **Volles v3-Research-Signalmodell** (typisierte Signale, Provenienz, Intraday-Regime,
  Confirmation) — nur das `no_trade_reason`-Gerüst minimal jetzt; der Rest **P9** (RESEARCH_V3).
- **Volle Instinct→VETO-ECC**, `decision_context`/`market_regime_snapshots`-Befüllung,
  Lesson-Embeddings, **Council-Integration**, Bull/Bear/Judge-Handover — **P9**, gegatet auf die
  in P8 gesammelten Outcomes.
- **Confidence verdrahtet `risk_pct`/gatet** — bleibt observe-only bis echte Daten da sind.
- **UI-Auth** (Decision 17) — Testphase localhost-only; leichte Auth später (Extra-Sicherheit).
- **UI-Aktionen wie „Deep Research starten"** (Decision 14) — P10; Command-Pfad bleibt offen,
  jetzt nicht gebaut.
- **`reflect()` auf Batch-API** (Q7) — unverändert P7-Stand.
- **Multi-Broker-Abstraktion**, volles systemd-Ops-Hardening, Live-Account-Zuschaltung — separat,
  nach Profit-Validierung.

---

## Post-Build-Schritte (nach grünem Gate)

1. `docs/architecture/` + `ARCHITECTURE.md` um die Scheduler-Schicht ergänzen.
2. `phase8_scheduler_konzept.svg` (1080×1080, GitHub-Dark, Monospace, Circle-Elemente, cairosvg-
   validiert).
3. `PHASE9_KICKOFF_HANDOVER.md` (V2-Scope: ECC, Council, SQLite-V2, Handover-Logik, v3-Research).
4. ROADMAP P8 → ✅; README-Statustabelle; `## Session stopped`-Block final.
