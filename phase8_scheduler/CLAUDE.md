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
Safety. **Stand 2026-06-30: Module 1–12 gebaut + grün (181 Tests) — Phase 8 code-complete +
🟡 nach `main` gemerged** (ehrlich geflaggt, s. `## Session stopped — 2026-06-30`). **Bewusst
KEIN ✅-„live-verifiziert"-Flip** wie P5/P6/P7 — gemerged mit dem ehrlichen Flag „mechanisch
bewiesen, autonomer Trade noch NICHT live-bewiesen", um den Build weiterzutragen. Es fehlt ein
echter Mehr-Zyklen-/Mehr-Tage-Lauf, der (a) einen netto-neuen autonomen Trade in **einem** sauberen
Lauf öffnet+schließt und (b) die Safety-Breaker tatsächlich auslösen sieht — **beides carried in den
v1.5-Hotfix** (`PHASE8_V1.5_HOTFIX_HANDOVER.md`: der Bot abstained fast immer → Variety + Clamp/Floor
+ echte Lessons). **Token-Budget by-default scharf** (Default `200_000` ≈ €0.8/Tag; vorher `None`/aus).

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
| `scheduler/exceptions.py` | `SchedulerError`/`PreflightError`/… | ✅ (Modul 2, 6 Tests) |
| `scheduler/clock.py` | `now_fn`/`sleep_fn` injizierbar; Phasen-Klassifikation (config-Fenster + Weekday; `is_market_open` lazy via `market_is_open`) | ✅ (Modul 3, 19 Tests) |
| `scheduler/state.py` | `SchedulerState` ↔ `scheduler_state.json` (atomic); Tages-Rollover (Europe/Berlin) + `record_cycle` (Contract E) | ✅ (Modul 4, 18 Tests) |
| `scheduler/killswitch.py` | KILL-Datei lesen/setzen/löschen (von `safety` + `webui` geteilt) — fail-soft, atomic | ✅ (Modul 5, 12 Tests) |
| `scheduler/command.py` | Start/Stop-Command-Datei (`scheduler_command.json`) lesen/schreiben/löschen — von `webui` (Schreiber) + `runner` (Leser) geteilt; fail-soft, atomic; **soft** Pause/Resume (≠ hartem KILL) | ✅ (Modul 12, 10 Tests) |
| `scheduler/safety.py` | `AutoConfirm` `confirm_fn`: demo + kill + caps + loss-breaker + budget | ✅ (Modul 6, 18 Tests) |
| `scheduler/backoff.py` | konsekutive-Fehler-Tracking + Backoff-Schedule | ✅ (9 Tests) |
| `scheduler/budget.py` | Token-Budget-Gate (reuse `token_meter`/`llm_usage.json`) | ✅ (Modul 7, 13 Tests) |
| `scheduler/research_tick.py` | expliziter echter P4-Trigger + `no_trade_reason` (der Blocker) | ✅ (Modul 8, 14 Tests) |
| `scheduler/observability.py` | v1.6 Step 0 — per-Zyklus JSONL-Diagnose-Log (`record_cycle`/`iter_records`), Sicherheitsnetz für Rückfälle | ✅ (v1.6, 9 Tests) |
| `scheduler/reconcile.py` | `CLOSED_BY_BROKER`-P&L-Nachzieh-Pass (idempotent) — reuse P5/P7 | ✅ (7 Tests) |
| `scheduler/runner.py` | die Loop / Daemon-Orchestrator + Preflight + Shutdown + `request_stop()` | ✅ (Modul 10, 18 Tests) |
| `scheduler/run.py` | `python -m scheduler.run` Entry (in-package, lazy `scripts.wiring`, SIGTERM/SIGINT → `request_stop`) | ✅ (Modul 11, 6 Tests) |
| `scripts/wiring.py` | Composition Root `build_scheduler()` — voller P1–P7-Stack (Debatte + Reward in EINEN Executor), 3 Closures | ✅ (Modul 11, operator-run) |
| `scripts/run_scheduler.sh` · `smoke_test.py` · `live_test.py` | Operator-Tools (Start-Script · offline Sim-Tag mit Fakes · echter unbeaufsichtigter IG-Demo-Zyklus) | ✅ (Modul 11, operator-run) |
| `webui/api.py` + `webui/static/*` + `scripts/run_webui.sh` | FastAPI read-mostly (DB `mode=ro` + `scheduler_state.json` + Kill/Command-Dateien) + statisches Dark-Neumorphism-Dashboard (GitHub-Dark, Monospace, Polling 7 s, kein Build-Step); Control **nur** Datei-Writes. **+ Token-Meter-Card** (`/api/token_usage`) **+ Last-Cycle-Reasoning** (`/api/last_cycle` zeigt jetzt Research-Pick + Bull/Bear/Judge-Transkript) — s. `## UI-Erweiterung — 2026-06-29` | ✅ (Modul 12, 18 Tests) |
| `tests/*` | gemockt, kein Netz/LLM/echter sleep (181, Schwerpunkt `test_runner` + `test_safety` + `test_webui`) | ✅ |

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
  Feiertagskalender** (Feiertage fallen in Broker-/VETO-fail-closed). ⟳ **2026-06-28
  (Modul 3, Code = Wahrheit):** das frühere „WINDOW nutzt P5 `trading_window_start/end`
  (09:30–11:19)" war stale — die echte P5-`ExecutionConfig` ist `09:00`/`17:30`
  (`execution/config.py:99-100`), bereits in Modul 1 übernommen. `clock.classify` nutzt
  daher `SchedulerConfig.window_open/close` (test-überschreibbar); `is_market_open` wird
  nur als **laufzeit-Markt-offen-Prädikat** via `Clock.market_is_open` reused (lazy Import,
  damit der heiße Klassifikations-Pfad stdlib-only bleibt).
- `broker_wrapper.credentials.get_credential(name)` (`credentials.py:56`,
  `SERVICE_NAME="tradingbot"`, wirft `CredentialNotFoundError`) für den Keyring-Preflight.

---

## Session stopped — 2026-07-02 (🎉 erster autonomer Trade + v1.7-Webui-Diagnose)

> **Der historische Moment:** heute (2026-07-02) hat der Scheduler zum ersten Mal überhaupt einen
> **echten, autonom generierten, net-new Trade** platziert — der harte Kern der Phase-8-Mission.
> **DAX BUY**, `deal_id=DIAAAAXW7U4AWAP`, size 19.5, `open_level=25617.0`. Entstanden aus einem
> echten P4-Research-Pick (conf 62) → echter P6-Bull/Bear/Judge-Debatte → Entscheidung **TRADE**
> (nicht ABSTAIN, wie fast jeden Zyklus zuvor). Order ACCEPTED 16:58:32; vom Broker per SL/TP
> geschlossen 17:07:21. P&L-Auflösung folgt dem aus Phase 7 bekannten IG-Settlement-Lag-Muster
> (Reconciler-Retry läuft periodisch weiter, kein neuer Bug).

### Auslöser für die v1.7-Diagnose
Kurz nach dem Trade meldete Nikinger die Webui als "kaputt": Trade-Zähler + Realized-P&L-Karte
zeigten falsche/veraltete Werte, Score-/Confidence-/Lessons-Karten leer. Zwei parallele
Untersuchungen (read-only, Code + Live-DB + Live-Log) fanden eine präzise, kleine, webui-only
Ursache — **kein** Zusammenhang mit dem am selben Tag gemergten `provenance`-Fix (konklusiv
ausgeschlossen: kein Code-Pfad im Repo liest `trade_outcomes` positional), **kein**
Sicherheitsproblem (DB/Broker/Loss-Breaker bestätigt korrekt + unberührt).

### Befund (Details: `docs/concepts/phase8_v1.7_hotfix_plan.md`)
`scheduler/state.py` dokumentiert bereits selbst (Design Point 3), dass `realized_pnl_today` ein
bewusster *best-effort*-Snapshot ist, **nicht** die Quelle der Wahrheit — der Loss-Breaker liest
deshalb bereits direkt aus der DB (`scripts/wiring.py:301-308`). Die Webui hat diese
Unterscheidung nie bekommen: `/api/status` reicht den lagging State-Snapshot durch, während
`/api/trades` auf demselben Dashboard bereits korrekt aus der DB liest — daraus die sichtbare
Inkonsistenz, zum ersten Mal überhaupt, weil es der erste echte Trade lang genug war (~9 min
IG-Lag), um die Lücke sichtbar zu machen. **Nikinger bestätigte live:** der Trade-Zähler
korrigierte sich selbst (0/5 → 1/5), sobald der Zyklus durchlief — "einige Elemente sind einfach
extrem verzögert". `realized_pnl_today` bleibt dagegen strukturell falsch für jeden
`CLOSED_BY_BROKER`-Trade (nicht selbstheilend) — das ist der eigentliche Fix-Punkt. Die leeren
Score-/Confidence-/Lessons-Karten sind ein separater, korrekter Nicht-Bug (Folge des
`archive_verification_trades.py --commit`-Laufs von heute, der `reward_pts`/`trade_lessons` auf
null kaskadiert hat).

### Next
- **v1.7-Plan geschrieben** (das „Was"): `docs/concepts/phase8_v1.7_hotfix_plan.md` — kleiner,
  webui-only Fix (`/api/status` DB-gespeist statt Snapshot-gespeist, mirror `/api/trades` +
  `wiring.py`s bereits bewiesenes Query-Muster). Eine spätere „Wie"-Session baut daraus den
  Ausführungsplan + implementiert. **Kein Code in dieser Session** — Nikinger-Anweisung.
- Offene Nikinger-Entscheidung (Plan §3.3): zählt der heutige Trade als v1.6-Step-4s „5a
  Varietäts-Run"-Beweis, oder braucht 5a noch einen saubereren/längeren Lauf?
- Die laufende v1.6-Instrument-Verifikation/-Live-Test-Kette läuft unverändert weiter,
  unabhängig vom v1.7-Fix.

### Gotchas (für den Re-Entry)
- Branch **`v1.6`** (v1.7 noch nicht auf eigenem Branch — Nikinger-Entscheidung beim Start der
  „Wie"-Session).
- **AI-Grenze:** v1.7 ist reine Webui-/Display-Logik, kein LLM-Touch geplant.
- Provenance-Hypothese für die Webui-Inkonsistenz ist **konklusiv ausgeschlossen** — eine
  spätere Session sollte sie nicht erneut verfolgen (s. Plan §1).

---

## Session stopped — 2026-07-02 (v1.6-Hotfix: Cause A part 2 — the `recent_trades` prompt-channel leak)

> **Auslöser:** während des laufenden v1.6-Live-Tests (Step-2-Harness gelaufen, Daemon-Variety-
> Lauf online) bemerkte Nikinger, dass die UI-Abstain-Reasoning weiterhin auf alte Test-Trade-Daten
> referenziert ("the recent trade history shows three consecutive losses totaling ~345€") — er las
> das zunächst als "alte Lessons nicht ausgeschlossen". Diagnose (Code + Live-DB, kein Live-Netz
> nötig) zeigte: die v1.5-Step-4-A-Lesson-Filterung war **korrekt** (alle 3 Test-Lessons haben
> `hold_duration_min < 2.0` → schon vom `min_hold_min`-Fallback ausgeschlossen). Der echte Leak war
> ein **zweiter, bisher unbemerkter Kanal**: `context_builder.build_context` liest zusätzlich
> `db.get_recent_trades(8)` — die rohe Trade-History-Tabelle, gerendert in denselben Prompt — und
> dieser Read blieb **ungefiltert**. Genau die drei geseedeten Verifikations-Trades (Zeitstempel
> 0.01/0.02/1.03 min Hold) erschienen dort als "drei Verlust-Trades" und färbten die
> LLM-Abstain-Begründung ein.

### Nikinger-Entscheidungen (via AskUserQuestion, vor der Implementierung gelockt)
- **Filter-Ansatz:** eine echte `provenance`-Spalte via **Migration 003** (statt der
  migrationsfreien Hold-Time-only-Variante) — sauber dokumentiert, mirror der v1.5-Lesson-Lösung.
- **Bestehende 3 Test-Trades:** aus der Live-DB **archivieren** (nicht nur code-seitig filtern) —
  ein neues, gitignored `data/archive/`-Verzeichnis, dokumentiert warum/was.

### Completed (P2 + P4 + P7 — additiv, jede Datei dated-note-annotiert)
- **P2 `migrations/003_phase8_trade_provenance.sql`** (neu) — `ALTER TABLE trade_outcomes ADD
  COLUMN provenance TEXT`, ausführlicher Header-Kommentar (mirror 002-Stil): erklärt den
  Zwei-Kanal-Leak, dass `provenance` vorher nur im Lesson-Blob lag, nie auf der Trade-Zeile selbst.
  Frische DB erreicht jetzt **Version 3**. `persistence/db.py`: `_TRADE_COLUMNS += ("provenance",)`
  + neue **`get_recent_trades_for_prompt(n, *, min_hold_min, quarantine_before,
  exclude_provenance)`** — exaktes Gegenstück zu `get_recent_lessons_for_prompt` (v1.5), aber gegen
  `trade_outcomes.provenance` statt den JSON-Blob (kein `json_extract` nötig — echte Spalte).
  `get_recent_trades` bleibt unangetastet für andere Caller.
- **P7 `reward/recorder.py::_open_record`** — `"provenance": opened.provenance` ergänzt (das Feld
  existierte schon auf `OpenedTrade`, erreichte aber nie die `trade_outcomes`-Zeile — nur den
  Lesson-Kontext via `_extract_lesson`). Migration-003-gated wie `initial_risk`/`account` es für 002 waren.
- **P4** — drei neue **provisorische** `ResearchConfig`-Felder, exaktes Mirror der Lesson-Knobs:
  `recent_trades_exclude_provenance=("verification",)`, `recent_trades_min_hold_min=2.0`,
  `recent_trades_quarantine_before=None`. `context_builder.build_context` ruft jetzt
  `db.get_recent_trades_for_prompt(8, …)` statt `db.get_recent_trades(8)`; `_DBLike`-Protocol
  entsprechend erweitert. **Trade-History gatet weiterhin nichts** (root rule 3) — nur der Prompt
  ändert sich.
- **Neues Skript `scripts/archive_verification_trades.py`** (repo-root, phaseless, mirror
  `verify_instrument.py`-Stil) — **dry-run per Default**; nur `--commit` schreibt
  `data/archive/verification_<UTC-Stamp>.json` (Snapshot **vor** dem Delete: `trade_outcomes` +
  kaskadierende `trade_lessons`/`reward_pts`/`market_regime_snapshots`/`decision_context`) und
  löscht dann die `trade_outcomes`-Zeilen — FK-`ON DELETE CASCADE` (die `Database` öffnet mit
  `PRAGMA foreign_keys = ON`) räumt die Kinder automatisch mit ab, kein separates Kinder-Delete
  nötig. Auswahl: `provenance='verification'` **oder** `hold_duration_min < --hold-threshold-min`
  (Fallback für die migrationsälteren, ungetaggten Trades) — ODER-verknüpft; `--ids` überschreibt
  beide Heuristiken explizit. `.gitignore` um `data/archive/` ergänzt (dated Note, gleiche
  Konvention wie die anderen `data/`-Einträge). Kein `data/archive/README.md` — das Repo trackt
  grundsätzlich **nichts** unter `data/` (`git ls-files data/` ist leer); die Doku lebt hier + im
  Skript-Docstring + im v1.6-Plan statt in einer ohnehin gitignorten Datei.
- **Tests:** P2 **75** (67 → +8: Migrations-Version 2→3 + Spalten-Test + 5 neue
  `get_recent_trades_for_prompt`-Fälle + 1 Provenance-Round-Trip + 1 NULL-Default-Test), P4 **135**
  (133 → +2: Wiring-Test wie beim Lesson-Filter), P7 **133** (131 → +2: `_open_record`-Provenance-
  Round-Trip + Autonomous-Default), root-`tests` **64** (50 → +14: der neue Archive-Script-Suite).
  P5 unberührt (**154**).

### Reconciliation (Code = Source of Truth)
- **Warum der Leak trotz v1.5 Step 4 A passierte:** v1.5 fixte den `recent_lessons`-Kanal
  vollständig korrekt — der Fehler war eine **unvollständige Diagnose**, nicht ein kaputter Fix.
  `build_context` hat zwei P2-Reads, die beide in denselben Prompt fließen
  (`context_builder.py:234`/`240` vor diesem Fix); nur einer wurde 2026-07-01 gefiltert.
- **`trade_outcomes` hatte strukturell keine Provenance-Info vor Migration 003** — `provenance`
  lief bisher nur bis in `trade_lessons.market_context_json` (Recorder-`_extract_lesson`). Die
  Trade-Zeile selbst blieb "blind" — das war der eigentliche strukturelle Gap, den Migration 003 schließt.

### ✅ Live-verifiziert (2026-07-02, noch am selben Tag — Operator-Lauf)
- Migration 003 lief über `init_db.py` gegen die Live-DB → Schema-Version **3** bestätigt.
- `scripts/archive_verification_trades.py --commit` lief erfolgreich →
  `data/archive/verification_20260702T145156Z.json` geschrieben; `trade_outcomes`/`trade_lessons`
  in der Live-DB jetzt **leer** (die 3 Verifikations-Trades + ihre Lessons sind archiviert).
- **UI + LLM-Prompt bestätigt sauber:** Nikinger sieht keine Lessons mehr in der Webui, und die
  LLM-Abstain-Begründung referenziert die alten Test-Trades nicht mehr. Ein nachfolgender
  Research-Zyklus (16:52) bekam sogar erstmals wieder einen echten P4-Pick (BUY DAX, conf=58),
  der dann korrekt vom P6-Debate-Layer **aus Marktgründen** (Echtzeit-IG-Bars widersprachen dem
  verzögerten yFinance-Seed) auf ABSTAIN gesetzt wurde — System arbeitet wie designed, kein Bug.
  ⚠ `scheduler_state.json → last_no_trade_detail` zeigt noch den alten Text — das Feld
  aktualisiert sich nur bei einem **Research-Level**-Abstain (der letzte war 14:18, vor dem
  Archiv-Lauf 14:51); ein künftiger Abstain zeigt sauberen Text. Kein Bug, nur ein noch nicht
  neu geschriebenes Display-Feld.
- Kein weiterer offener Punkt zu Cause A — beide Prompt-Kanäle (Lessons + Trade-History) sind jetzt
  provenance-gefiltert **und live bestätigt**.

### Next
- Die laufende v1.6-Instrument-Verifikation/-Live-Test-Kette ist von diesem Fix unabhängig und
  läuft unverändert weiter → **Step 4** (5a Varietäts-Run für den net-new autonomen open→close,
  5b Breaker-Fire-Run) bleibt das offene Live-Beweis-Gate; danach Step 5 (Doku-Flip). Kein
  weiterer Code ist für v1.6 geplant, außer ein Live-Lauf deckt einen neuen Bug auf.

### Gotchas (für den Re-Entry)
- Branch **`v1.6`**. Dieser Fix ist additiv über P2+P4+P7 — Regression läuft **pro Phase separat**
  (`tests.conftest`-Namenskollision, s. Memory `reference_running_phase_tests`).
- **AI-Grenze gewahrt:** reine Schema-/Filter-/Skript-Änderung, kein LLM-Touch.
- Migration 003 ist additiv + idempotent (Runner-Versions-Guard) — eine bestehende Dev-DB auf
  Version 2 bekommt Spalte 3 automatisch beim nächsten `run_migrations()`/`init_db.py`.

---

## Session stopped — 2026-07-02 (v1.6-Hotfix: „Wie"-Session — Step 3a (Tolerieren) + Step 0 (Observability) + Step 2 (Verification-Harness) implementiert)

> **Auslöser:** die „Wie"-Session, die aus dem „Was"-Plan (`docs/concepts/phase8_v1.6_hotfix_plan.md`)
> den file-für-file-Ausführungsplan baute (Plan-Mode, `AskUserQuestion` für die vier offenen §4-
> Scope-Fragen, Nikinger-Freigabe), dann direkt implementiert. **Kein Live-/Netz-Lauf diese Session**
> (Operator-Job) — alles gemockt/offline.

### Vier Nikinger-Entscheidungen (via AskUserQuestion, vor der Implementierung gelockt)
1. **Step 3 = Tolerieren** (nicht Drop/Fix) — `^FCHI`/`^IBEX` bleiben unverändert im Universum, nur
   der `requirements.txt`-Pin wird korrigiert. **Bedingung:** von „sophisticated logging" begleitet,
   um bei einer Wiederholung die echte Ursache zu finden — Step 0 wurde dadurch vom Nice-to-have zum
   Sicherheitsnetz.
2. **Step 0 = Lean + Error-Detail** — nicht nur „welches Feld degradiert", sondern auch „warum"
   (das tatsächliche Fetch-Exception-Text), via einer additiven P3-Feld-Ergänzung.
3. **Step 2 (Harness) = jetzt bauen**, nicht auf v3 verschieben.
4. **Reihenfolge:** die Nummerierung 0→1→2→3→4→5 im Plan-Dokument bleibt für Kontinuität zum „Was",
   aber die **tatsächliche Baureihenfolge** wich bewusst ab (dokumentiert im Plan-Dokument selbst,
   §„Ausführungsreihenfolge-Notiz") — Step 3a zuerst (billig, entkoppelt von Step 0), dann Step 0,
   dann Step 2, dann der Live-Beweis (Operator) und der Doku-Flip.

### Completed (alle additiv, gemockt/offline verifiziert)
- **Step 3a — Tolerieren:** `phase3_external_data/requirements.txt` von `yfinance>=0.2.65,<0.3`
  (stale) auf `yfinance>=1.4.0,<1.5` (die tatsächlich installierte/getestete Version) re-gepinnt —
  eine **separate Hygiene-Korrektur**, **nicht** der Fix für den Live-Ausfall (der war intermittente
  Yahoo-Flakiness, H4). **Korrektur einer vorherigen Theorie:** die „Versions-Pin-Drift"-Hypothese
  (installiert `1.4.1` vs. damals gepinnt `<0.3`) ist **widerlegt** — sowohl der fehlgeschlagene
  Live-Lauf als auch der erfolgreiche Diagnose-Lauf liefen gegen dieselbe `1.4.1`. Kein
  `ticker_map.py`/`EXTENDED_UNIVERSE`-Code-Touch. Dated Notes in `phase3_external_data/CLAUDE.md` +
  `docs/concepts/phase8_v1.6_hotfix_plan.md` (Step 3 auf ✅ Tolerieren geflippt).
- **Step 0 — Observability (P3 + P4 + P8, additiv durchgängig):**
  - **P3** (`external_data/models.py`/`fetcher.py`): `BrainContext.field_errors: dict[str,str]`
    (default `{}`) — die bisher verworfene Exception jedes fehlgeschlagenen Sub-Fetches
    (drift/momentum/volume/high_low/history) wird jetzt in `get_brain_context`s `_safe()`-Helfer
    gesammelt. **Nicht** in `to_prompt_dict()` (LLM-Shape unverändert), **wohl** in `to_dict()`
    (für den P8-Log). +1 Test (72→73).
  - **P4** (`research/models.py`/`context_builder.py`/`research.py`): `ResearchContext.
    brain_context_health` (per-Epic `{"status": "full"|"degraded"|"unavailable", "missing":[...],
    "errors":{...}}`, aus den bereits vorhandenen `brain_contexts`-Prompt-Dicts abgeleitet — **kein**
    zweiter P3-Call). `Research` bekommt zwei neue Instanz-Attribute (Muster wie
    `last_no_pick_reasoning`): `last_context_health` (Kopie von `context.brain_context_health` nach
    jedem `build_context()`) + `last_abort_detail` (der exakte Freitext-Grund aus **jedem**
    `_abstain()`-Aufruf — breiter als `last_no_pick_reasoning`, das nur den LLM-Prosa-Fall deckt).
    Beide reset am Zyklus-Anfang. +11 Tests (122→133: 5 context_builder, 6 research).
  - **P8** (neu `scheduler/observability.py` + Wiring): `record_cycle()` hängt einen JSON-Lines-
    Record pro WINDOW-Zyklus an `data/state/research_health.jsonl` an (plain append, **nicht**
    tmp+`os.replace` — ein JSONL-Log wächst nur, eine unterbrochene Zeile wird beim Lesen toleriert);
    `iter_records()` als fail-soft Reader (Operator-Tooling/späteres Webui). `ResearchResult` (in
    `research_tick.py`) trägt jetzt `context_health`/`abort_detail` (defensiv per `getattr` gelesen).
    `SchedulerConfig.observability_path` (Default `data/state/research_health.jsonl`). `runner.py`s
    WINDOW-Branch fängt den bisher **verworfenen** `ResearchResult`-Return jetzt ab und schreibt den
    Log-Eintrag — nur auf dem `can_open`-PASS-Pfad (ein Cap-Block triggert nie Research). Root
    `.gitignore` um den neuen Pfad ergänzt (verifiziert via `git check-ignore`). +15 Tests
    (182→197: 9 observability, 4 research_tick, 2 runner).
- **Step 2 — Instrument-Verification-Harness:** **neu** `scripts/verify_instrument.py`
  (repo-root, phasenlos — spiegelt `resolve_epics.py`/`diag_score_distribution.py`). Konsolidiert
  IG-Seite (`get_market_info`+`get_ohlcv`-Probe, spiegelt `resolve_epics.resolve_epic`) und
  yFinance-Seite (`get_history`/`get_bars`/`get_volume_anomaly`, spiegelt P3-`smoke_test.py`) zu
  **einem** PASS/FAIL-Verdikt pro Instrument (`currency_eur`/`min_deal_size_ok`/
  `ig_ohlcv_available`/`yf_daily_ok`/`yf_intraday_ok`/`volume_proxy_ok`). Reused P3s eigene
  Off-Hours-Ehrlichkeit (`get_bars` → `None` außerhalb der Handelszeit) statt einen zweiten
  Markt-Check zu bauen — ein `None`-Intraday-Ergebnis wird als `"skipped(market closed)"`
  reportet, **nie** als Fail gewertet. Default iteriert `research.models.EXTENDED_UNIVERSE`
  (lazy-imported); `--epic`/`--yf-ticker`/`--volume-proxy` verifiziert einen Ad-hoc-Kandidaten
  (die künftige v3-Promotion-Nutzung). **v3-Naht dokumentiert, nicht gebaut:** die reinen
  Check-Funktionen (`check_ig_side`/`check_yf_side`/`verdict_for`) sind duck-typed + I/O-frei,
  importierbar via `importlib.util.spec_from_file_location` wie die Testsuite es schon tut.
  **Neu** `tests/test_verify_instrument.py` (root, importlib-Pattern) — 22 Tests (root-`tests`
  28→50).

### Verifiziert (gemockt/offline — Live/Netz = Operator)
- Jede Phase **separat** gelaufen (bekannte `tests.conftest`-Namenskollision):
  **P1 52 · P2 67 · P3 73 (+1) · P4 133 (+11) · P5 154 · P6 70 · P7 131 · P8 197 (+15) ·
  root-`tests` 50 (+22)** — alle grün, exakt den erwarteten Deltas entsprechend (keine
  unerwarteten neuen/fehlenden Tests). `py_compile` clean auf allen berührten/neuen Dateien.
- **Import-Isolation erneut bestätigt:** `import scheduler.runner`/`scheduler.observability`
  ziehen weiterhin **NONE** cross-phase; `import research.research`/`research.context_builder`
  ziehen weiterhin **NONE** cross-phase (broker_wrapper/persistence/external_data/anthropic
  nicht geladen).
- `python scripts/verify_instrument.py --help` → exit 0, `git check-ignore
  data/state/research_health.jsonl` → bestätigt ignoriert.

### Next (Operator)
1. **Step 4 — Live-Beweis** (unverändert aus v1.5-Step-5, jetzt mit Step-0-Sichtbarkeit): 5a
   Varietäts-Run (mehrere Demo-Tage, normale Caps → den ersten netto-neuen autonomen open→close
   fangen) + 5b Breaker-Fire-Run (enge Caps → einen Safety-Breaker tatsächlich auslösen sehen).
   Ein Abstain-lastiger Tag ist jetzt aus `data/state/research_health.jsonl` erklärbar statt
   geraten.
2. **Optional, nicht blockierend:** `python scripts/verify_instrument.py` gegen echtes IG-Demo +
   yfinance laufen lassen → das erste konsolidierte Verdikt für alle vier Instrumente (ersetzt die
   verstreuten Einzel-Checks aus v1.5).
3. **Nach 5a/5b:** Step 5 — Doku-Flip auf ✅ (ROADMAP/README/root-CLAUDE.md), weiterhin **kein**
   Profit-/Edge-Claim.
- **Commit:** vorgeschlagen (atomar denkbar: (1) Step 3a re-pin+docs, (2) P3 field_errors, (3) P4
  context-health+abort-detail, (4) P8 observability+wiring, (5) verify_instrument.py+tests, (6) docs),
  wartet auf Nikinger-Trigger.

### Offene Punkte / blockers
- Keine technischen. Der optionale H4-Spot-Check (zweiter zeitversetzter Diagnose-Lauf, im „Was"-
  Plan als Carry vermerkt) bleibt weiterhin optional/nicht blockierend — die Zwei-Zeitpunkte-
  Evidenz aus Step 1 gilt als ausreichend.

---

## Session stopped — 2026-07-02 (v1.6-Kickoff: Initial-Plan „das Was" geschrieben + Step 1 (Diagnose) live gelaufen — docs-only, KEIN Code)

> **Auslöser:** der Nikinger startete v1.6 mit einem Sonderauftrag: den **initialen v1.6-Plan
> (das „Was")** erstellen — zukunftssicher Richtung **v3 (semi-automatisches Research)** — und in
> eine physische Plan-Datei schreiben, inkl. Dokumentation, **warum der Plan in Claude Code statt
> im Web-Chat** entstand (Konventions-Abweichung, bewusst). Zwei-Stufen-Modell: diese Session =
> „Was"; eine spätere Claude-Code-Session = „Wie" (Ausführungsplan); erst danach Code. Direkt im
> Anschluss lief der Nikinger **Step 1 (Diagnose)** selbst gegen echtes yfinance/IG —
> Output-Datei geliefert, hier ausgewertet + in den Plan eingearbeitet.
> **Kein Trading-/Scheduler-Code berührt** (docs + Memory only).

### Ursprünglicher Kern-Befund (Code = Wahrheit — verfeinert das v1.6-Handover §2a)
- Die Fehler-Signatur (`period=1d`, `got 0, want >= 4`) matcht die **Intraday-5m-Fetches**
  (`fetcher.py:352/401/450`, alle `period="1d", interval="5m"`); das Operator-Log
  `intraday price unavailable for ^IBEX; using last daily close` (`fetcher.py:453`) beweist
  zugleich: die **Daily-Fetches funktionierten**. → Arbeitshypothese **H1**: Yahoo liefert für
  `^FCHI`/`^IBEX` Daily-, aber **keine 5m-Intraday-Daten**; der Brain-Context ist vermutlich
  **teil-degradiert** (drift/momentum `None`, Daily-Signale intakt), nicht komplett `None` —
  genau das kann heute niemand sehen (Observability-Gap → bestätigt „Step 0 = Logging zuerst").

### ⟳ Step-1-Ergebnis (Operator-Lauf, `scripts/2026_07_02-v1.6-step1-diagnosis.md`) — dreht die Diagnose
- **H1 widerlegt:** `^FCHI` UND `^IBEX` lieferten sowohl `period=5d,interval=1d` (5 rows) als
  auch `period=1d,interval=5m` (**19 rows**) — identisch zur `^GDAXI`-Kontrolle. Kein
  Daily-vs-Intraday-Unterschied. **H2 hinfällig** (weitere Intervall-Varianten liefen sauber
  durch). Der volle P3-`smoke_test.py`-Lauf war für **beide** Epics grün (drift/momentum/bars/
  history/brain_context populiert; nur `volume` degradiert — der **erwartete** C3-Pfad ohne
  registrierten Proxy, kein Bug).
- **H4 gestützt:** dieselben Fetches, die im Live-Lauf `possibly delisted` warfen, liefen jetzt
  fehlerfrei — Zwei-Zeitpunkte-Kontrast **ist** der Intermittenz-Beweis, kein zweiter
  Wiederholungslauf nötig (optionaler Spot-Check als Carry vermerkt).
- **★ Neuer, bisher undokumentierter Befund: yfinance-Versions-Pin-Drift.** Installiert
  `yfinance==1.4.1`, aber `phase3_external_data/requirements.txt:6` pinnt `>=0.2.65,<0.3` —
  eine Major-Version-Drift außerhalb des dokumentierten Pins; plausibelster Root-Cause-
  Kandidat für die Intermittenz (yfinance 0.2.x→1.x hatte größere interne Rewrites/API-
  Änderungen). Muss in der „Wie"-Session verifiziert werden.
- **Auswirkung auf Step 3:** die binäre Fix-vs-Drop-Regel im Plan passt nicht mehr sauber —
  eine **dritte Option „Tolerieren"** (Versions-Pin klären + bestehende Retry/Backoff-Logik
  gegen dieses Fehlerbild härten, Instrumente bleiben im Universum) ist jetzt die plausiblere
  erste Wahl vor Fix/Drop. Im Plan §1-Addendum + §3 + §4-Frage-6 nachgeführt.

### Completed (docs-only)
- **`docs/concepts/phase8_v1.6_hotfix_plan.md`** (NEU — die physische Plan-Datei, v1.5-Format):
  §0a Warum-Claude-Code-statt-Web (3 Gründe: Root-Cause nur per Code-Lektüre eingrenzbar;
  v1.5-Anker-Drift; v3-Naht `InstrumentSpec.source="research_promoted"` muss verifiziert statt
  erinnert werden) · §0b Leitplanken (carried) · §1 Befund-Update + Hypothesen H1–H4 · §2 die
  **v3-Linse** (Fix = „validate"-Hälfte des validate→promote-Pfads + permanente per-Epic-Daten-
  Health-Observability, kein Ticker-Patch, keine AI) · §3 Steps: 0 Observability → 1 Diagnose
  (Operator) → 2 **Instrument-Verification-Harness** (konsolidiert `resolve_epics.py` +
  P3-`smoke_test.py` zu EINEM wiederholbaren Verdikt; der künftige v3-Promotion-Gate) → 3 Fix
  oder Drop (Entscheidungsregel: verifizierter Fix > ehrlicher Drop; „Universum-Ehrlichkeit
  schlägt Instrumenten-Zahl") → 4 Live-Beweis (carried 5a/5b) → 5 Doku-Flip + point_value-Carry ·
  §4 offene Fragen für die „Wie"-Session · §5 antizipiertes Cross-Phase-Register.
- **Pointer:** dated Note im `PHASE8_V1.6_HANDOVER.md`-Kopf (Plan existiert; Handover bleibt
  Diagnose-Dokument); root-`CLAUDE.md` „Active phase" um den Plan-Link ergänzt; Memory
  aktualisiert.
- **Step-1-Ergebnis eingearbeitet:** `docs/concepts/phase8_v1.6_hotfix_plan.md` §1 (dated
  Addendum: H1 widerlegt, H2 hinfällig, H4 gestützt, Versions-Drift-Befund), §3 (Fix-vs-Drop
  → Fix-Tolerieren-Drop nachgeführt, „Tolerieren" als neue Präferenz-1), §4 (neue Frage 6:
  Versions-Pin-Klärung). Roh-Output des Operator-Laufs liegt in
  `scripts/2026_07_02-v1.6-step1-diagnosis.md`.

### Verifiziert
- **Kein Code berührt** — `git status` zeigt ausschließlich `.md`-Dateien (+ die neue
  Operator-Output-Datei) → Regression per Definition unberührt (Baseline bleibt P1 52 ·
  P2 67 · P3 72 · P4 122 · P5 154 · P6 70 · P7 131 · P8 182; kein Test-Lauf nötig/gelaufen).
  Alle im Plan zitierten file:line-Anker gegen den echten Baum verifiziert
  (`fetcher.py:352/401/450/453`, `models.py:294/304/369`, `research_tick.py:84-89`,
  `context_builder.py:141`); yfinance-Versions-Drift bestätigt (`pip show yfinance` → `1.4.1`
  vs. `phase3_external_data/requirements.txt:6` → `>=0.2.65,<0.3`).

### Next (frische Session)
1. **Die „Wie"-Session:** aus `docs/concepts/phase8_v1.6_hotfix_plan.md` den file-für-file-
   Ausführungsplan bauen — jetzt mit dem Step-1-Ergebnis als Startpunkt (Versions-Pin-Frage
   §4.6 zuerst klären, dann „Tolerieren"-vs-Fix/Drop entscheiden), plus die übrigen offenen
   Fragen §4 mit dem Nikinger locken (Log-Format/-Ort, Abstain-Taxonomie, Harness-Verortung).
2. **Optional (Operator, billig, nicht blockierend):** ein zweiter, zeitversetzter H1-Spot-
   Check (Carry-Vermerk in §3), falls die „Wie"-Session zusätzliche Intermittenz-Evidenz will.
3. Danach Implementierung in Plan-Reihenfolge (Step 0 Observability zuerst).
- **Branch:** `v1.6` (neu, von `main`). **Commit:** dieser Step ist committet (Nikinger-
  getriggert); „Commit ⇒ Note-Update" gilt im selben Commit.

### Offene Punkte / blockers
- Keine technischen. Die §4-Fragen des Plans sind bewusst offen (gehören in die „Wie"-Session,
  nicht hierher entschieden).

---

## Session stopped — 2026-07-02 (v1.5 nach `main` gemergt + ehrlich geflaggt; erster Live-Lauf → yFinance-Blocker; v1.6-Handover geschrieben)

> **Auslöser:** der Nikinger hat den v1.5-Daemon **live** laufen lassen — er produziert
> yFinance-Fehler. Auftrag (gleiche Taktik wie beim P8-Merge): **v1.5 mit ehrlicher Doku nach `main`
> pushen + mergen**, stale Docs updaten, ein **v1.6-Handover** schreiben (was v1.5 lieferte + was es
> live NICHT produzierte), dann Session-stopped + Konventionen. **Kein Code-Fix diese Session** — das
> echte Troubleshooting ist deep cross-phase + es gibt **noch kein echtes Logging**, also gehört es in
> eine frische Session (ausdrücklicher Nikinger-Wunsch).

### Befund (Code = Wahrheit — NICHT der v1.5-Provenance-Code)
- **yFinance-Blocker:** `^IBEX` (und mit hoher Sicherheit `^FCHI`) liefern `possibly delisted; no price
  data found (period=1d)` → der P3-`fetcher` retryt 3× und degradiert den **Brain-Context** dieses Epics
  zu `None` (P4 `context_builder._safe_brain_context`; concept C3 „reduced-signal, toleriert"). **Kein
  Hard-Crash** (Fallback „using last daily close"), das Epic bleibt handelbar (Tradeability kommt vom
  Broker-Probe, nicht von yFinance), aber es erreicht den LLM mit `n/a`-Signalen + flutet die Logs.
- **Das ist exakt das im Step-2-Variety-Track geflaggte, aber NIE operator-verifizierte Risiko:**
  `^FCHI`/`^IBEX` waren „well-known public symbols, **not** live-verified" (nur DAX `^GDAXI` + Euro
  Stoxx 50 `^STOXX50E` sind verifiziert). Der Ticker-Map-Eintrag steht in
  `phase3_external_data/external_data/ticker_map.py`.
- **Effekt:** die v1.5-„Variety" ist **halb wirksam** — DAX + Euro Stoxx 50 voller Context, CAC 40 +
  IBEX 35 kein Context. Der **net-new autonome open→close** (v1.5-Ziel) bleibt **unbewiesen**.
- **Meta-Lücke:** es gibt **kein strukturiertes Logging** (nur rohe yFinance/fetcher-stderr-WARNINGs) →
  die Ursache ist aus dem aktuellen Output nicht sauber zu pinnen. v1.6-Step-0 = Observability.

### Completed (diese Session — nur Doku + Merge, KEIN Trading-/Scheduler-Code)
- **`phase8_scheduler/PHASE8_V1.6_HANDOVER.md`** (NEU) — was v1.5 lieferte (A/B/C + Provenance-UI,
  mockgrün) · was live noch fehlt (open→close, Breaker, Multi-Day, Edge) · der yFinance-Blocker
  (Symptome + Code-Pfad + Hypothesen) · die No-Logging-Meta-Lücke · v1.6-Richtungen (Observability →
  `^FCHI`/`^IBEX` verifizieren/fixen **oder** droppen → Live-Beweis) · Datei-Anker.
- **Stale-Docs ehrlich geflippt:** `README.md` (Statuszeile 8 + Fußnote ⁵), `ROADMAP.md`
  (Phase-8-Header + neuer ⚠-v1.5-Stand-Block), root `CLAUDE.md` („Active phase"-Opener) — alle mit dem
  v1.5-merged-Stand + yFinance-Blocker + v1.6-Pointer.
- **Merge:** `phase8-v1.5-hotfix` → `main` (fast-forward) + Push nach `origin` (s. u.).

### Verifiziert (mockgrün — Live = Operator)
- Regression unberührt (kein Code berührt diese Session): **P1 52 · P2 67 · P3 72 · P4 122 · P5 154 ·
  P6 70 · P7 131 · P8 182**. Die yFinance-Fehler sind ein **Laufzeit-/Daten-Problem**, kein Test-Fail.

### Next (frische Session — v1.6)
1. **Observability zuerst** (der Enabler): strukturiertes Per-Zyklus/Per-Epic-Brain-Context-Log
   (full/degraded/warum) + persistiertes Daemon-Run-Log; heute ist die Diagnose Blindflug.
2. **Den übersprungenen P3-Check nachholen:** `python phase3_external_data/scripts/smoke_test.py --epic
   IX.D.CAC.IFE.IP` und `--epic IX.D.IBEX.IFM.IP` gegen echtes yFinance — was liefert Yahoo für
   `^FCHI`/`^IBEX` wirklich (Symbol/period/interval)? (Operator-Lauf.)
3. **Fix oder Drop:** Symbol/period korrigieren (cross-phase P3) **oder** CAC 40 + IBEX 35 aus
   `EXTENDED_UNIVERSE` entfernen (zurück auf die zwei verifizierten DAX + Euro Stoxx 50) — beide additiv,
   cross-phase (models + ticker_map + Tests + abgeleitete P5-`point_values`).
4. **Dann Live-Beweis** (v1.5-Step-5): Varietäts-Run (open→close) + Breaker-Fire-Run.
- **Commit:** die Doku dieser Session ist committet + gemergt (Operator-getriggert).

### Offene Punkte / blockers
- yFinance `^FCHI`/`^IBEX` Ursache **ungepinnt** (bewusst — braucht Logging + den P3-smoke_test in einer
  frischen Session). `point_value` STXE/CAC/IBEX weiterhin **inferiert** (vor Live-Konto bestätigen).

---

## UI-Erweiterung — 2026-07-01 (Lesson-Provenance-Label — Addendum zu Step 4 A)

> **Auslöser:** der Nikinger, kurz vor dem Start von Step 5, bemerkte, dass die Lessons-Card im
> Dashboard weiterhin **alle** Lessons ohne Kennzeichnung zeigt — Frage: Bug oder echte Lücke?
> **Befund: kein Bug.** `webui/api.py`s `/api/lessons` liest per **eigenem** SQL direkt gegen die
> `mode=ro`-DB (nicht über `persistence.Database`), Step 4 hat nur den P4-Prompt-Pfad
> (`context_builder` → `get_recent_lessons_for_prompt`) berührt — das Webui war **nie** im Scope. Die
> Lücke ist real: eine Verifikations-Lesson ist im Dashboard von einer echten nicht unterscheidbar.
> **Nikinger-Freigabe:** „nur ein UI-Label, direkt umsetzen, kein Opus-Plan nötig."

### Completed (additiv, UI-only, DB bleibt read-only + **unfiltered**)
- **`webui/api.py` `/api/lessons`:** SELECT ergänzt um `json_extract(market_context_json,
  '$.provenance') AS provenance`. Die Liste bleibt **komplett** (DB = Source of Truth für den
  Operator) — nur eine zusätzliche Spalte, kein Filter.
- **`webui/static/app.js` `renderLessons`:** neuer Helper `lessonProvenanceTag` — rendert ein
  kompaktes Pill-Badge neben dem Timestamp jeder Lesson: `verification` amber-akzentuiert
  (`.tag--accent`, wiederverwendet vom Confidence-Tag), `autonomous`/`unknown` gedämpft (Default
  `.tag`), fehlender Tag (pre-v1.5-Lessons, `market_context_json` ohne den Key oder ganz `NULL`) →
  **ehrlich als `"untagged"` gelabelt**, nicht stillschweigend als echt dargestellt.
- **`webui/static/style.css`:** eine kompakte `.lesson-provenance`-Modifier-Regel (kleinere
  Schriftgröße/Padding als der Standard-`.tag`, damit das Badge neben dem 10px-Timestamp nicht
  dominiert). Kein neues Farbschema — reuse der bestehenden `--amber`/`--dim`-Tokens.

### Verifiziert (gemockt + visuell — kein Netz/LLM/Broker nötig fürs UI)
- `pytest phase8_scheduler/tests -q` → **182 passed** (181 + 1: `test_lessons_expose_provenance`,
  plus die bestehende `test_lessons_returns_seeded_row` auf die neue 2-Zeilen-Fixture angepasst —
  ein getaggtes `autonomous` + ein pre-v1.5-`NULL`-Row, beide korrekt zurückgegeben, kein Crash).
  `node --check app.js` + `py_compile api.py` clean.
- **Visuell** gegen die **echte** `data/trading_bot.sqlite` (Scratch-Port 8011, Operator-`:8000`
  unberührt, per `agent-browser` gescreenshottet): alle 3 realen Lessons (alle pre-v1.5, kein Trade
  ist bisher mit dem neuen Code gelaufen) zeigen korrekt das gedämpfte `untagged`-Badge, kein Crash,
  `app.js`/`style.css` laden 200. Sobald der Step-5-Live-Lauf echte Trades erzeugt, werden neue
  Lessons automatisch `autonomous`/`verification` zeigen.

### Next
Zurück zu **Step 5** (Operator-Live-Läufe) — unverändert, s. Block unten. Diese Änderung ist rein
additiv und blockt nichts.
- **Commit:** vorgeschlagen, wartet auf Nikinger-Trigger.

---

## Session stopped — 2026-07-01 (v1.5-Hotfix: **Step 4 (A — Lesson-Provenance) ABGESCHLOSSEN** — präziser Provenance-Tag + Read-Path-Filter, kein Schema-Touch)

> **Auslöser:** der Nikinger startete Step 4 (A — Lesson-Provenance), den letzten Code-Step vor den
> Operator-Live-Läufen (Step 5). Plan-Freigabe: `~/.claude/plans/hello-claude-and-welcome-moonlit-waffle.md`.
> Eine gelockte Operator-Entscheidung (AskUserQuestion): **„Provenance-Tag persistieren, mit detaillierter
> Doku warum + was"** (Option B statt read-only-minimal). **Kein neues AI, kein VETO/Gate berührt, keine
> Migration.**

### Kern-Befund (⚠ warum der naive Plan nicht 1:1 baubar war — Code = Wahrheit)
Der literale Seed-Marker `"MANUAL SEED (not a real research pick)"` (`seed_candidate.py:62`) wird **nie
persistiert**: `build_opened` (`phase5_execution/execution/executor.py`) speicherte nur
`candidate["llm_confidence"]`; `OpenedTrade`/`trade_outcomes` haben **kein** `reasoning`-Feld. Ohne
Migration (Plan-Verbot) ist der Marker aus der DB für bestehende Lessons **nicht lesbar**. → Lösung:
präziser Tag **vorwärts** in den bestehenden `market_context_json`-Blob (kein Schema-Touch) + Hold-Time/
Datum als Fallback für die schon verschmutzten Lessons.

### Completed (alle additiv, Default-Pfad bit-identisch — Cross-Phase, jede Datei dated dokumentiert)
- **P7 `reward/models.py`:** `OpenedTrade.provenance: str = "autonomous"` (Default hält jede Bestands-
  Konstruktion gültig, trailing field). **P7 `reward/recorder.py`:** `_extract_lesson` schreibt
  `opened.provenance` (Cold-Reconcile ohne Stash → `"unknown"`) in `market_context` → `market_context_json`.
- **P5 `execution/executor.py`:** `build_opened` leitet `provenance` **deterministisch** (Modul-Const
  `_SEED_MARKER_PREFIX`, `reasoning.startswith(...)`, **kein AI**) ab — `"verification"` für Seeds, sonst
  `"autonomous"`. Nur mit `reward_sink`; `reward_sink=None` bit-identisch.
- **P2 `persistence/db.py`:** **neue** `get_recent_lessons_for_prompt(n, *, min_hold_min, quarantine_before,
  exclude_provenance)` — in-query Filter (JSON1 `json_extract … IS NOT` NULL-safe für den Tag + Hold-Time-
  Subquery + Datum), neueste N **Überlebende**. `get_recent_lessons` **unberührt**. P2 bleibt dummer
  parametrisierter Store.
- **P4 `research/models.py` + `context_builder.py`:** drei provisorische `ResearchConfig`-Felder
  (`lesson_exclude_provenance=("verification",)`, `lesson_min_hold_min=2.0`, `lesson_quarantine_before=None`
  — reversibler Reset, aus); `build_context` ruft den gefilterten Getter. Downstream automatisch
  (`_mark_lessons_used` markiert nur Überlebende, `prompt` rendert nur sie).
- **Reward-Pfad bewiesen unberührt:** `reward/*` ruft `get_recent_lessons*` nie; der Tag landet nur im
  Lesson-Context-JSON, nicht in einem Score-Input. Lessons gaten nichts (root rule 3).

### Verifiziert (gemockt/offline — Live = Operator)
- **P2 62→67 · P4 120→122 · P5 153→154 · P7 128→131.** Regression unberührt: **P1 52 · P3 72 · P6 70 ·
  P8 181.** `py_compile` clean; P4-Import-Isolation gewahrt (`import research.context_builder` zieht NONE
  cross-phase). Doku: hotfix-Plan Step 4 auf ✅ + Cross-Phase-Register erweitert; `🔁`-Notes in P2/P4/P5/P7
  CLAUDE.md; P2/P4-Konzept-Annotationen.

### Step 4 (A) ist damit ABGESCHLOSSEN
Damit sind **alle drei v1.5-Code-Fixes fertig** (B ✅ Clamp/Floor, C ✅ 4-Instrument-Universum, A ✅
Lesson-Provenance). Übrig ist **nur noch Step 5 (Operator-Live-Läufe)** — der ✅-Beweis, nicht mehr Code.

### Next (nächste Session / Operator)
1. **Step 5a — Varietäts-Run** (mehrere Demo-Tage, normalere Caps): den ersten **netto-neuen autonomen
   open→close** in einem sauberen Lauf einfangen (jetzt möglich: 4 Instrumente + gelockerter Clamp/Floor).
2. **Step 5b — Breaker-Fire-Run** (separat, enger Cap / kleiner `daily_loss_cap`): einen Safety-Breaker
   **tatsächlich auslösen** sehen. Diese zwei schließen das Phase-8-✅-Gate → dann Step 6 (Doku-Flip ✅,
   ROADMAP/README, Merge).
3. **Operator, nicht blockierend (aus der letzten Session getragen):** `smoke_test.py` für `^FCHI`/`^IBEX`
   (CAC/IBEX Basis-Ticker) + point_value-Bestätigung der drei Nicht-DAX-Instrumente vor echtem Live-Konto.
- **Commit:** vorgeschlagen (atomar: (1) P7+P5 write-path, (2) P2 getter + P4 filter/config, (3) docs),
  wartet auf Nikinger-Trigger.

### Offene Punkte / blockers
- Keine technischen. ⚠ Hold-Time (2.0 min) + Provenance-Tag sind **provisorische** v1.5-Data-Collection-
  Werte — vor Live re-baselinen. Bestehende (pre-tag) verschmutzte Lessons werden von der Hold-Time-
  Heuristik erfasst; die Datums-Quarantäne (`lesson_quarantine_before`) ist der optionale, reversible
  Hard-Reset-Hebel (default aus).

---

## Session stopped — 2026-07-01 (v1.5-Hotfix: **Step 2 (C — Variety) VOLLSTÄNDIG ABGESCHLOSSEN** — CAC 40 + IBEX 35 bestätigt, STXE voll live-verifiziert)

> **Auslöser:** der Nikinger hat die zwei angeforderten Operator-Schritte gelaufen (P3-`smoke_test.py`
> für STXE + ein **gepacter** `resolve_epics.py`-Re-Lauf für France 40/Netherlands 25/Spain 35) und die
> Ausgabe in dieselbe Datei angehängt (`scripts/2026_07_01-Testrun-Results.md`). **Kontext läuft hoch —
> dies ist der Session-Abschluss-Handover.**

### Befund — der Re-Lauf war ein ERFOLG, kein zweiter Fehlschlag
Der Nikinger meldete „again a failed run", aber die Daten zeigen das Gegenteil:
- **STXE-`smoke_test.py`:** voller `BrainContext` mit echten Werten (drift/momentum/history) UND
  `volume_available=True, volume_source='EXW1.DE'` mit echtem `today_volume=188152.0` — **`^STOXX50E`
  UND `EXW1.DE` sind jetzt beide live-verifiziert**, nicht mehr nur „öffentlich bekannt vermutet".
- **`resolve_epics.py --pace-s 1.0`** (die Pacing-Fix aus der letzten Session griff): **France 40 (CAC
  40) 4/4 Treffer sauber, `ohlcv_available=True` für alle**; **Spain 35 (IBEX 35) 4/4 Treffer sauber,
  `ohlcv_available=True` für alle**. Die Rate-Limit-Hypothese von letzter Session ist damit **bestätigt**
  (der erste Lauf war Artefakt, nicht echte Datenlage) — der zweite, gepacte Lauf beweist es.
- **Netherlands 25 (AEX):** `search_ok=true, hits=[]` — ein **echtes** Leer-Ergebnis (keine Rate-Limit-
  Signatur), IG hat unter diesem Suchbegriff schlicht keinen Markt. Bewusst nicht weiterverfolgt (im
  Locked-Decision-Table ohnehin „optional" geklammert; 4 bestätigte Instrumente erfüllen „3-4" bereits).

### Completed — Step 2B jetzt vollständig
- **`research/models.py` `EXTENDED_UNIVERSE`** von 2 auf **4 Instrumente** erweitert:
  DAX (unverändert) · **Euro Stoxx 50** `IX.D.STXE.IFM.IP` (yf_ticker+volume_proxy jetzt **voll
  live-verifiziert**, `point_value=2.0` bleibt inferiert) · **CAC 40** `IX.D.CAC.IFE.IP` („Frankreich 40
  Kassa (1€)" — die kleinste Kassa-Variante, passt am besten zum DAX-Muster; `point_value=1.0` inferiert
  aus der „(1€)"-Namenskonvention, `yf_ticker="^FCHI"` öffentlich bekannt/**nicht** live-verifiziert,
  `volume_proxy=None` bewusst — kein sicher bekannter ETF-Ticker geraten, C3-toleriert) · **IBEX 35**
  `IX.D.IBEX.IFM.IP` („Spanien 35 Kassa (2€)" — keine 1€-Variante vorhanden; `point_value=2.0` inferiert,
  `yf_ticker="^IBEX"` öffentlich bekannt/**nicht** live-verifiziert, `volume_proxy=None` bewusst).
  **Alle vier `ohlcv_available=True` live bestätigt** → kein Phantom-Instrument-Risiko für VETO 3.
- **P3 `ticker_map.py`:** zwei neue statische Einträge (`IX.D.CAC.IFE.IP → ^FCHI`,
  `IX.D.IBEX.IFM.IP → ^IBEX`), STXE-Kommentar auf „voll live-verifiziert" aktualisiert.
- **Keine Wiring-Änderung nötig** — die P4/P8-Wiring-Schleifen iterieren bereits generisch über
  `config.universe`/`EXTENDED_UNIVERSE`; vier Instrumente statt zwei fließen automatisch durch (verifiziert:
  `ResearchConfig(universe=EXTENDED_UNIVERSE).epic_allowlist` liefert alle 4 Epics, die abgeleitete
  `point_values`-Dict-Comprehension in `build_scheduler` ebenso).
- **Tests aktualisiert:** `test_universe.py` (4-Instrumente-Assertions, `volume_proxy is None` für
  CAC/IBEX geprüft), `test_ticker_map.py` (+1 Test für die zwei neuen statischen Einträge).

### Verifiziert (gemockt/offline — Live-Verifikation von `^FCHI`/`^IBEX` steht noch aus)
- **P3 71→72 · P4 unverändert 120** (Tests erweitert/umbenannt, keine neuen Testfunktionen nötig) ·
  root **28**. Regression unberührt: **P1 52 · P2 62 · P5 153 · P6 70 · P7 128 · P8 181**. `py_compile`
  clean. Import-Isolation bestätigt (`import scripts.wiring` in P8 zieht weiterhin NONE cross-phase).
  Direkt verifiziert: `ResearchConfig(universe=EXTENDED_UNIVERSE).epic_allowlist` = alle 4 Epics;
  abgeleitete `point_values` = `{DAX:1.0, STXE:2.0, CAC:1.0, IBEX:2.0}`.

### Step 2 (C — Variety) ist damit ABGESCHLOSSEN
Von 1 auf 4 EUR-Instrumente, alle mit bestätigtem `ohlcv_available=True` (VETO 3 kann für jedes
tatsächlich feuern statt phantom-blockieren). Kombiniert mit dem bereits erledigten Step 3 (B — Clamp/
Floor entkoppelt+relaxt) ist der **Hauptblocker der v1.5-Diagnose (1-Instrument-Universum + Doppel-Clamp)
jetzt vollständig behoben.** Übrig: Step 4 (A — Lesson-Provenance, kleiner, nach C/B sequenziert) + Step 5
(Operator-Live-Läufe, die den ✅-Beweis liefern).

### Next (für die nächste Session — frisch einsteigen)
1. **Operator (optional, vor dem nächsten Live-Lauf empfohlen, nicht blockierend):**
   `python phase3_external_data/scripts/smoke_test.py --epic IX.D.CAC.IFE.IP` und
   `--epic IX.D.IBEX.IFM.IP` laufen lassen, um `^FCHI`/`^IBEX` gegen echtes yfinance zu bestätigen
   (analog zum bereits erledigten STXE-Check). Kein Blocker für Step 4 oder einen Live-Testlauf — ein
   unverifizierter Ticker degradiert nur zu `brain_context=None` für dieses Epic (kein Crash), aber vor
   einem Live-Konto-Einsatz zwingend nachzuholen.
2. **Step 4 (A — Lesson-Provenance):** Seed-Marker (`"MANUAL SEED (not a real research pick)"`,
   `seed_candidate.py:62`) + Hold-Time-Heuristik zur Identifikation von Verifikations-Trades;
   `get_recent_lessons`/`context_builder.py:184`-Prompt-Filter, der sie ausschließt; Quarantäne-by-date
   für bestehende verschmutzte Lessons. **Kein Migration-003/DB-Schema-Touch** (Plan-Vorgabe). Reward/
   Score rechnet weiter auf allen Lessons — nur der Prompt wird gereinigt. Plan:
   `docs/concepts/phase8_v1.5_hotfix_plan.md` Step 4.
3. **Danach Step 5 (Operator-Live-Läufe):** 5a Varietäts-Run (mehrere Tage, fängt den ersten
   netto-neuen autonomen open→close mit dem jetzt 4-instrumentigen Universum + gelockertem Clamp/Floor
   ein) + 5b Breaker-Fire-Run (separat, enger Cap). Diese zwei schließen das Phase-8-✅-Gate.
- **Commit:** vorgeschlagen (atomar: (1) EXTENDED_UNIVERSE CAC+IBEX + P3-Mapping + Tests, (2) docs),
  wartet auf Nikinger-Trigger.

### Offene Punkte / blockers
- `^FCHI`/`^IBEX` (Basis-Ticker) und alle drei `point_value`-Werte (STXE/CAC/IBEX) bleiben **inferiert /
  öffentlich bekannt, nicht unabhängig live bestätigt** — vor einem echten Live-Konto-Einsatz zwingend
  verifizieren (Kontraktdetails/manueller Demo-Trade für point_value; `smoke_test.py` für die Ticker).
  Kein Blocker für die weitere v1.5-Arbeit (Demo-only, fail-closed bleibt intakt).
- CAC/IBEX haben bewusst **keinen** Volume-Proxy (kein sicher bekannter ETF-Ticker) — beide degradieren
  zu `volume_z_score=None` (reduced-signal, C3-toleriert, kein Bug).

---

## Session stopped — 2026-07-01 (v1.5-Hotfix: Step 2B (C) — Euro Stoxx 50 aufgenommen, CAC/AEX/IBEX zurückgestellt, resolve_epics.py-Rate-Limit-Fix)

> **Auslöser:** der Nikinger hat `scripts/resolve_epics.py` gegen IG-Demo laufen lassen und die
> Ausgabe als Datei geliefert (`scripts/2026_07_01-Testrun-Results.md`). Auftrag: „go in with the
> second half of our plan; wenn Replanning nötig ist, dokumentiere die Findings und sag Bescheid."

### Befund (Replanning-relevant, Code = Wahrheit)
- **Germany 40 (DAX):** 7 Treffer, alle sauber (`market_info_ok=True`, `ohlcv_available=True`).
  `IX.D.DAX.IFMM.IP` bestätigt unverändert korrekt.
- **EU Stocks 50 (Euro Stoxx 50):** 5 Treffer, sauber. Gewählt: **`IX.D.STXE.IFM.IP`** („EU Stocks
  50 Kassa (2€)", kleinste Kassa-Variante — analog zu DAX' `IFMM` (1€), gleiches Muster: Name „(X€)"
  + `lot_size==X` korrelieren exakt bei DAX). `currency=EUR`, `min_deal_size=0.5`,
  `market_status=TRADEABLE`, `ohlcv_available=True` — **live bestätigt**.
- **France 40 (CAC 40) + Netherlands 25 (AEX) + Spain 35 (IBEX):** **Befund = wahrscheinlich
  Rate-Limit-Kaskade, NICHT echte Datenlage.** `IGAdapter._request` wirft `RateLimitError` bei
  HTTP 429 **ohne eigenen Retry/Backoff** (`ig_adapter.py:321-322`) — der Resolver machte ~35
  ungebremste Broker-Calls direkt hintereinander (Germany 40: 15, EU Stocks 50: 11, dann France
  40). Genau ab da: 3/4 CAC-Treffer `get_market_info` komplett fehlgeschlagen, der 4. Treffer
  (`IX.D.CAC.IFD.IP`) mit `ohlcv_available=False`, **beide** folgenden Suchbegriffe komplett
  fehlgeschlagen (`error=None`, weil mein Skript den echten `env.error` nicht auslas — auch
  gefixt). **Bedeutung, warum das wichtig ist:** VETO 3 (Momentum) failt closed ohne Bars — ein
  Epic ohne `ohlcv_available` würde **nie** eine Order clearen (ein „Phantom"-Instrument). CAC 40
  / AEX / IBEX werden deshalb **bewusst NICHT** aufgenommen, bis ein sauberer Re-Lauf das klärt.

### Completed
- **`research/models.py`:** neues öffentliches `EXTENDED_UNIVERSE` (DAX + Euro Stoxx 50) neben dem
  unveränderten privaten `_DEFAULT_UNIVERSE` (DAX-only, bleibt der `ResearchConfig()`-bare-Default
  — **kein** bestehender Test/Caller ändert sich). `point_value=2.0` für STXE ist **inferiert** aus
  IG's „(2€)"-Namenskonvention (Analogie zum verifizierten DAX-Muster), **nicht** unabhängig
  bestätigt — Kommentar an Ort und Stelle. `yf_ticker="^STOXX50E"` / `volume_proxy="EXW1.DE"` sind
  öffentlich bekannte Symbole (Analogie DAX `^GDAXI`/`EXS1.DE"), **nicht** live gegen yfinance
  verifiziert. `research/__init__.py` exportiert `EXTENDED_UNIVERSE`. **+3 Tests** (`test_universe.py`).
- **P3 `ticker_map.py`:** statischer `_MAP`-Eintrag `IX.D.STXE.IFM.IP → ^STOXX50E` ergänzt (DAX-
  Muster: `_VOLUME_MAP` bleibt leer, Proxy weiter per `--volume-proxy`-Flag). **Grund, warum die
  2A.4-Wiring-Schleife das nicht ersetzt:** die dynamische Registrierung deckt den **Daemon**-Pfad,
  aber P3s eigene `smoke_test.py`/`live_test.py` bauen einen **bare** `TickerMapper()` — ohne den
  statischen Eintrag könnte der Operator die STXE-Ticker-Vermutung gar nicht unabhängig verifizieren
  (`EpicNotMappedError`). **+1 Test** (`test_ticker_map.py`).
- **Wiring (die eigentliche Verdrahtung des neuen Instruments):**
  - P4 `scripts/wiring.py` `build_research`: Default (kein `config`-Arg) → `ResearchConfig(universe=
    EXTENDED_UNIVERSE)`. Betrifft **nicht** `smoke_test.py`/`live_test.py` (die übergeben immer
    explizit `epic_allowlist=(args.epic,)` — bleiben Single-Epic-Tools, unverändert).
  - P8 `scripts/wiring.py` `_build_research`: **unconditional** `ResearchConfig(universe=
    EXTENDED_UNIVERSE)` (kein Override-Pfad hier) — das ist der **daemon-kritische** Punkt, jeder
    autonome Zyklus sieht jetzt beide Instrumente.
  - P8 `scripts/wiring.py` `build_scheduler`: `ExecutionConfig.point_values` wird jetzt **aus
    `EXTENDED_UNIVERSE` abgeleitet** (`{spec.epic: spec.point_value for spec in EXTENDED_UNIVERSE}`)
    statt hand-dupliziert — **eine** echte SoT (`InstrumentSpec.point_value`), die Wiring-Schicht
    projiziert sie nur in P5s Config-Form (löst die früher dokumentierte „zwei SoTs"-Sorge auf).
- **`scripts/resolve_epics.py` — Rate-Limit-Fix (Bug in meinem eigenen Tool, live gefunden):**
  injizierbares `sleep_fn` + `--pace-s` (Default 0.6 s, spiegelt P3s `RateLimiter`-Mindestabstand)
  pausiert jetzt **nach jedem** Broker-Call (`search_markets`/`get_market_info`/`get_ohlcv`).
  **Zweiter Fix:** `resolve_term`s „search failed"-Zweig hardcodete vorher `error: None` statt den
  echten `env.error` zu lesen — neuer `_error_message()`-Helfer surfaced jetzt die echte Meldung
  (z. B. „429 rate limited"), + neues `market_info_error`-Feld je Hit. **+3 Tests**
  (`tests/test_resolve_epics.py`: Pacing-Beweis, Error-Surfacing ×2).
- **C.4 (VETO-Quelle je Epic) read-only verifiziert (kein Code-Änderung nötig):**
  `execution/vetos.py:pre_trade_check` liest `epic = candidate["epic"]` und reicht es an
  `veto_momentum(broker, epic, ...)` durch — die Momentum-VETO-Quelle war **schon** per-Kandidat-
  Epic dynamisch (nicht hardcodiert), genau wie der Step-2-Plan es verlangte zu verifizieren.

### Verifiziert (gemockt/offline — Live-Rerun für CAC/AEX/IBEX ist Operator-Sache)
- **P3 70→71 · P4 117→120 · root tests 26→28.** Regression unberührt: **P5 153 · P6 70 · P7 128 ·
  P8 181**. `py_compile` clean auf allen berührten Dateien. Import-Isolation bestätigt: `import
  scripts.wiring` (P8) zieht weiterhin **NONE** cross-phase beim Modul-Laden (nur die lazy
  Funktionskörper-Imports wuchsen um einen Namen).

### Plan-Abweichung (dokumentiert, wie vom Nikinger verlangt)
- **CAC 40 / AEX / IBEX 35 bleiben zurückgestellt** — Step 2B ist damit **teilweise** erledigt
  (Euro Stoxx 50 drin, die anderen drei offen), nicht vollständig wie ursprünglich geplant.
- **Neuer Zwischenschritt entdeckt:** die 2A.4-Wiring-Schleife allein reicht nicht für Operator-
  Verifizierbarkeit neuer Ticker — ein **statischer P3-`TickerMapper`-Eintrag bleibt nötig**, damit
  der Operator `phase3_external_data/scripts/smoke_test.py --epic <neu> --volume-proxy <neu>`
  eigenständig gegen echtes yfinance laufen lassen kann, bevor der Daemon der Vermutung vertraut.

### Next
- **Operator:**
  1. `python phase3_external_data/scripts/smoke_test.py --epic IX.D.STXE.IFM.IP --volume-proxy
     EXW1.DE` laufen — verifiziert `^STOXX50E`/`EXW1.DE` gegen echtes yfinance, bevor der Daemon
     dem Brain-Context für dieses Epic vertraut.
  2. `python scripts/resolve_epics.py --term "France 40" --term "Netherlands 25" --term "Spain 35"`
     erneut laufen (jetzt gepaced, Default 0.6 s zwischen Calls; `--pace-s 1.0` falls immer noch
     Rate-Limit-Muster auftauchen) → saubere CAC/AEX/IBEX-Daten, insbesondere `ohlcv_available`.
  3. point_value je bestätigtem Instrument aus den IG-Kontraktdetails / einem manuellen Demo-Trade
     bestätigen (bleibt für STXE ebenfalls **inferiert**, nicht unabhängig bestätigt).
- **Nach dem Re-Lauf:** CAC 40 (+ ggf. AEX/IBEX) zu `EXTENDED_UNIVERSE` hinzufügen, falls
  `ohlcv_available=True` sauber bestätigt — sonst dokumentiert ausschließen (Phantom-Instrument-
  Risiko). **Danach Step 4 (A — Lesson-Provenance).**
- **Commit:** vorgeschlagen (atomar: (1) P3+P4 EXTENDED_UNIVERSE+TickerMapper+wiring+tests, (2)
  resolve_epics.py Rate-Limit-Fix+tests, (3) docs), wartet auf Nikinger-Trigger.

### Offene Punkte / blockers
- CAC 40 / AEX / IBEX 35 Resolution ist **inkonklusiv** (wahrscheinlich Rate-Limit-Artefakt) — kein
  Code-Blocker, aber ein Daten-Blocker für die restliche Step-2B-Populierung.
- Euro Stoxx 50s `point_value`/`yf_ticker`/`volume_proxy` sind **inferiert/öffentlich bekannt, nicht
  unabhängig live bestätigt** — vor einem Live-Lauf mit echtem Geld zwingend verifizieren.

---

## Session stopped — 2026-07-01 (v1.5-Hotfix: Step 2A (C) — typisiertes Universum + per-Epic Brain-Context + P5-point_value-Naht + resolve_epics.py)

> **Auslöser:** der Nikinger startet Step 2 (C — Variety, der größte Hebel) nach dem erledigten B.
> Plan-Freigabe (`~/.claude/plans/hello-claude-and-welcome-pure-kernighan.md`): **Step 2 splittet in
> 2A (jetzt, deterministisches Gerüst, DAX-only bit-identisch) + 2B (nachdem der Operator
> `resolve_epics.py` gegen IG-Demo läuft → echte Epic-Strings)**. Zwei gelockte Operator-Entscheidungen
> (AskUserQuestion): (1) „Framework now, populate later"; (2) **point_value JETZT in P5 Gate-4 threaden**
> (mit ehrlicher Doku). **Kein neues AI, kein VETO/Gate berührt.**

### Completed (Cross-Phase, alle additiv — Default-/DAX-Pfad bit-identisch)
- **2A.1 — typisiertes Universum (P4 `research/models.py`):** neues frozen `InstrumentSpec`
  (`epic`/`yf_ticker`/`volume_proxy`/`point_value`/`min_deal_size`/`currency`/`source`) + validierender
  `load_universe()` (EUR-only, epic non-empty, `point_value>0`/`min_deal_size>0`; malformed → drop+warn,
  alles invalid/leer → `ValueError` fail-closed) + `_DEFAULT_UNIVERSE` (DAX). `ResearchConfig` trägt jetzt
  `universe` als **Single Source of Truth**; `__post_init__` versöhnt: `universe=None` → aus dem Legacy
  `epic_allowlist`/`volume_proxy` **abgeleitet** (Backward-Compat für `epic_allowlist=(...)`-Konstruktion),
  `universe` gesetzt → `load_universe` + `epic_allowlist` daraus **re-derived**. `__init__.py` exportiert
  `InstrumentSpec`/`load_universe`. **+13 Tests** (`tests/test_universe.py`).
- **2A.2 — per-Epic Brain-Context (das Herz von C):** vorher bekam **nur** der Anchor-Epic Brain-Context.
  `ResearchContext.brain_contexts: dict[epic → dict|None]` (default `{}`, Back-Compat); `context_builder`
  holt jetzt einen Snapshot je tradeable Epic (∪ Anchor, order-preserving, deduped; degradiert je Epic
  einzeln zu `None`). `prompt._render_per_epic_snapshots` rendert die **Nicht-Anchor**-Snapshots (leer bei
  1 Epic → Prompt bit-identisch). `candidate_filter.apply_filter` Drift-Kohärenz keyt jetzt auf die
  **Kandidaten-eigene** `brain_contexts[epic]` (Fallback `brain_context` für pre-v1.5-Caller); `research.py`
  `drift_at_pick` aus dem **gepickten** Epic. **+5 Tests** (2 context_builder, 2 prompt, 1 candidate_filter).
- **2A.3 — `scripts/resolve_epics.py` (NEU, repo-root, phasenlos, read-only):** löst die kuratierte
  Shortlist (DAX+EuroStoxx50+CAC40[+AEX/IBEX]) via `search_markets`→`get_market_info`→`get_ohlcv`-Probe zu
  echten IG-Demo-Epic-Strings + Facts auf. **Nur GETs — keine Order, kein Write.** Broker-injiziert (offline
  testbar); `main()` baut den echten `ig_demo` lazy. ⚠ **point_value wird NICHT resolved** (IG exponiert es
  nicht — `lot_size` nur als Hinweis; Operator bestätigt manuell). stderr-Narrative/stdout-JSON. **+6 Tests**
  (`tests/test_resolve_epics.py`).
- **2A.4 — Wiring (P4 `scripts/wiring.py` + P8 `scripts/wiring.py`):** registrieren jetzt je
  `InstrumentSpec` aus `config.universe` das `yf_ticker`-Mapping + den Volume-Proxy (statt einmalig nur den
  Anchor). DAX-Default unverändert (^GDAXI ist TickerMapper-Builtin; Proxy = pre-v1.5).
- **2A.5 — point_value in P5 Gate-4 (Operator-entschieden „jetzt, ehrlich dokumentiert"):** `Candidate`-
  Kontrakt ist **frozen** + IG `get_market_info` exponiert **keinen** Point-Value → die Naht ist **P5-seitig**:
  `ExecutionConfig.point_values: dict[epic→float]` (default `{}`) + `point_value_for(epic)` (→ 1.0 default).
  `sizing.compute_size(..., epic=None)` nutzt `config.point_value_for(epic)` (Fallback: market_info-echoed
  epic → 1.0); `executor` reicht `epic` durch + `build_opened(..., point_value=config.point_value_for(plan.epic))`
  für konsistentes `initial_risk`. **Default `{}` → alles 1.0 → DAX bit-identisch.** ⚠ **Zwei SoTs** (P4
  `InstrumentSpec.point_value` ↔ P5 `point_values`) bewusst — der frozen Cross-Phase-Kontrakt trägt keinen
  Point-Value; beide non-DAX-Werte **provisorisch** bis `resolve_epics.py` (2B), Kommentar an beiden Stellen.
  Gate-4-Sizing, **kein VETO** (Leitplanke 3 intakt). **+7 Tests** (4 sizing, 2 config, 1 executor build_opened).

### Verifiziert (gemockt/offline — Live = Operator)
- **P4 99→117**, **P5 146→153**, root-`tests` 20→**26**. Regression unberührt: **P6 70 · P7 128 · P8 181**
  (P8 mockt Research; die neuen P4/P5-Felder sind alle additiv default-unchanged). `py_compile` clean auf
  allen berührten Dateien + `resolve_epics.py` + beiden Wirings.
- **Import-Isolation gewahrt:** `import research.models/candidate_filter/context_builder/prompt` zieht
  **NONE** broker_wrapper/external_data/persistence/anthropic (models.py fügte nur stdlib `logging` hinzu).

### Next
- **Operator (blockt 2B):** `python scripts/resolve_epics.py` gegen IG-Demo laufen (im Fenster; Keyring
  entsperrt) → die echten Epic-Strings + currency/min_deal_size/lot_size/ohlcv je Instrument zurückmelden.
  point_value je Instrument aus den IG-Kontraktdetails / einem manuellen Demo-Trade bestätigen.
- **Step 2B (nach Operator-Daten):** die bestätigten `InstrumentSpec`-Einträge (EuroStoxx50/CAC40[+AEX/IBEX])
  in die kuratierte Universe-Liste; P3 `TickerMapper._MAP`-Einträge (IG-Epic→yFinance) + Volume-Proxies
  (cross-phase P3-Edit, dated Note; DAX unverändert); `ExecutionConfig.point_values` je Epic füllen; per-Epic
  Sizing-Sanity + VETO-Quelle (`get_ohlcv`) verifizieren. **Danach Step 4 (A — Lesson-Provenance).**
- **Commit:** vorgeschlagen (atomar: (1) P4 universe+brain+tests, (2) P5 point_value+tests, (3) resolve_epics.py+test+wiring, (4) docs), wartet auf Nikinger-Trigger.

### Offene Punkte / blockers
- Keine technischen. ⚠ point_value-Doppel-SoT (P4/P5) ist bewusst + dokumentiert; bei Live-Go-Live
  re-baselinen. resolve_epics.py-Live-Lauf steht aus (Operator).

---

## Session stopped — 2026-07-01 (v1.5-Hotfix: Step 3 (B) — Clamp/Floor entkoppelt + relaxt; **VOR Step 2 gebaut**)

> **Auslöser:** die Step-1-Messung (`scripts/diag_score_distribution.py` gegen die echte DB) ergab
> **alle 3 gescorten Trades < 50** (100 %; current 45.83, Median 47.45, 0 % < 35). Der below-50-
> Doppel-Clamp feuert damit **jeden** Zyklus. Der Nikinger gab frei, **B vor C** zu ziehen (Plan-Reorder,
> ehrlich dokumentiert), weil (a) die Daten B als *konstanten* Blocker beweisen, (b) B klein/isoliert/
> ohne Operator-Prerequisite ist, (c) **C's Varietät bis B gelockert ist gedämpft** bleibt (unter Score 50
> ist ohne B alles BUY-only + Floor 70). **Kein neues AI, kein VETO/Gate berührt** — nur `phase4_research/`.

### Completed (nur `phase4_research/` + Doku — kein Trading-/Scheduler-Code)
- **Entkoppelt:** neues `ResearchConfig.confidence_floor_below_score = 50.0` (`research/models.py`);
  `candidate_filter.confidence_threshold` liest es statt des entfernten Modul-Literals
  `_NEUTRAL_SCORE = 50.0`. → Floor-Grenze und Direction-Clamp-Grenze (`long_bias_below_score`) sind jetzt
  **unabhängige Knobs** (vorher teilten sie zufällig 50.0 über zwei Mechanismen).
- **Relaxt (Defaults — Wiring überschreibt sie nie, s. `scripts/wiring.py:112/147/194` bare `ResearchConfig()`):**
  `enable_long_bias_clamp: True → **False**` (SELL unter neutral erlaubt; P6-Debatte + 4 VETOs = Richtungs-
  Check) und `confidence_floor_low_score: 70.0 → **55.0**` (der 70-Floor war bei Sub-50-Scores unerreichbar).
  Beide mit lautem `# v1.5 data-collection mode — re-baseline before live`-Kommentar; Docstring erklärt Entkopplung
  + provisorische Werte.
- **Tests:** `test_candidate_filter.py` 15 → 18 — neues Default-Verhalten asserted (Clamp off / Floor 55
  beidseitig / SELL unter neutral passiert), der Clamp-*Mechanismus* weiter gedeckt via explizitem
  `clamped_config()` (stellt die pre-v1.5-Werte her), + ein **Entkopplungs-Beweis** (Floor-Grenze 60 ≠
  Clamp-Grenze 50 → feuern unabhängig).

### Verifiziert (gemockt/offline — Live = Operator)
- `pytest phase4_research/tests -q` → **99 passed** (96 → 99; `--collect-only` bestätigte die wahre
  Startzahl 96, nicht die Grep-Schätzung 94). `test_research.py` (17) **unberührt** — keine clamp-abhängige
  Assertion brach. Direkt verifiziert: `ResearchConfig().enable_long_bias_clamp is False`,
  `confidence_threshold(40.0, ResearchConfig()) == 55.0`, `resolve_allowed_directions(40.0, ResearchConfig())
  == ("BUY","SELL")`.
- **Regression unberührt:** `pytest phase8_scheduler/tests -q` → **181 passed** (P8 mockt Research). Andere
  Phasen konsumieren diese Werte nicht asserted.

### Doku (der „ehrlich das Warum + Was"-Auftrag)
- `docs/concepts/phase8_v1.5_hotfix_plan.md`: Step-1-Messwerte-Tabelle eingetragen; §2-Sequenz mit der
  **B-vor-C-Reorder-Begründung** annotiert (Original sichtbar gelassen, nicht überschrieben); Step-3-Block
  mit dem Ist-Stand (inkl. der Detail-Abweichungen: Literal statt Config-Feld, B4 verworfen) auf ✅ geflippt.
- `docs/concepts/phase4_research_plan_konzept.md`: v1.5-Annotation an den `ResearchConfig`-Feldern + am
  stale `confidence_threshold`-Stub. `phase4_research/CLAUDE.md`: 🔁-Cross-Phase-Note + Decision-7-Bullet
  („ON by default" → „v1.5 OFF by default") aktualisiert.

### Next
- **Operator (optional, wann immer):** P8-Daemon / `phase4_research/scripts/live_test.py` im Handelsfenster
  laufen lassen → beobachten, dass jetzt ein **Kandidat erzeugt** wird (und in die Debatte läuft), wo vorher
  force-abstained wurde. Das ist der Live-Beleg für B (kein Doku-Flip nötig — B ist Mittel, nicht Ziel).
- **Step 2 (C — Universum, größter Hebel):** `InstrumentSpec`-Liste + validierender Loader + **per-Epic
  Brain-Context-Refactor** in `context_builder` (heute nur der Anchor-Epic bekommt Brain-Context!) + P3-
  `TickerMapper`-Eintrag + Volume-Proxy + `point_value`/`currency` je Instrument (Sizing hardcodet `1.0`/EUR)
  + Operator-Prerequisite `resolve_epics.py` (IG-Demo-Epic-Strings auflösen). Danach Step 4 (A — Lessons).
- **Commit:** vorgeschlagen (zwei atomare: Code+Tests, dann Doku), wartet auf Nikinger-Trigger.

### Offene Punkte / blockers
- Keine technischen. ⚠ n=3 ist ein winziges Sample — die Floor-55-Wahl ist ein grober,
  provisorischer Startwert für die Datensammlung, kein getunter Wert. Sobald mehr reale Outcomes da sind
  (nach C + Live-Läufen), gehört der Floor re-baselined (idealerweise durch Phase-7-Outcome-Anchoring ersetzt,
  nicht nur neu geraten).

---

## Session stopped — 2026-07-01 (v1.5-Hotfix: Step 1 — `bot_score`-Verteilungs-Diagnostic, read-only)

> **Auslöser:** der Nikinger bat um den nächsten Schritt nach dem Housekeeping. Gemäß Plan
> (`docs/concepts/phase8_v1.5_hotfix_plan.md` §Step 1) = „erst messen": ein read-only Script,
> das die `bot_score`-Verteilung (`reward_pts.score_after`) aus der Live-DB berichtet, damit die
> Floor-Werte in Step 3 (B) datengetrieben statt geraten sind. **Kein Trading-Code berührt.**

### Completed
- **`scripts/diag_score_distribution.py`** (NEU, **repo-root, phasenlos** — der Hotfix-Plan
  listet diese Datei explizit mit „—" in der Phase-Spalte des Cross-Phase-Edit-Registers).
  Stdlib-only (`sqlite3`/`statistics`/`argparse`/`json`), **keine** Cross-Phase-Imports.
  DB-Zugriff spiegelt `phase8_scheduler/webui/api.py:ro_connect` (`file:...?mode=ro`-URI,
  ein Write scheitert **strukturell**, nicht nur diszipliniert) — dupliziert statt importiert
  (Begründung im Docstring: `webui`/`scripts` sind nicht Teil des installierten Pakets;
  `persistence.Database` öffnet RW + hat keinen Full-Series-Getter). Query: `reward_pts LEFT
  JOIN trade_outcomes ON trade_id`, `ORDER BY id ASC` (chronologisch, keine LIMIT). Reine
  `compute_distribution(scores)`-Funktion (kein I/O) liefert min/max/median/mean/p25/p75
  (`statistics.quantiles(method="inclusive")`, bleibt garantiert in `[min,max]`) + Count/Anteil
  `<50`/`<35` (strikt, deckt sich mit dem echten Clamp in `candidate_filter.py`) +
  `current_score` (letztes Element in ID-Reihenfolge — **nicht** sortiert, entspricht exakt
  `get_current_score()`s Semantik). Drei unterschiedene „insufficient"-Gründe (`database not
  found` / `reward_pts table missing` / `no reward_pts rows`) münden alle im selben stabilen
  JSON-Schema (nie ein Sonderformat für den Fehlerfall). `small_sample`-Flag (n<10, echot
  `reward.confidence.n_min` informell, **kein** Import) zeigt trotzdem alle Stats — unterdrückt
  nichts. Output-Disziplin: Mensch-lesbare Narrative → stderr, JSON → stdout (immer, kein Flag),
  spiegelt `phase7_reward/scripts/inspect_history.py`. Exit 0 in jedem erwarteten Fall
  (Report-Tool, kein Pass/Fail-Test); ein echter unerwarteter Fehler wird **nicht** geschluckt.
- **`tests/test_diag_score_distribution.py`** (NEU, **repo-root `tests/`** — bewusst **kein**
  neues `scripts/__init__.py`, um die bestehende `scripts.wiring`-Namenskollision über P4–P8
  nicht zu riskieren; Modul-Load via `importlib.util.spec_from_file_location`). **20 Tests**:
  12 reine `compute_distribution`-Fälle (leer/Einzelpunkt/**chronologische Reihenfolge** ≠
  sortiert/Boundary exakt-50/exakt-35 ausgeschlossen/Median gerade+ungerade/Ties/p25-p75
  innerhalb min-max/small-sample-Grenze/negative Robustheit) + 8 `tmp_path`-SQLite-
  Integrationstests über `main()` (befüllte DB/leere Tabelle/fehlende DB-Datei/fehlende
  Tabelle/**Read-only-Beweis** — ein Write auf der `_ro_connect`-Connection wirft/`NULL`-
  Account→„unknown"/stdout ist valides JSON + stderr trägt die Narrative).

### Design-Entscheidungen (aus einer Plan-Agent-Review verifiziert, nicht selbst geraten)
- `statistics.median()` statt `quantiles()[1]` (unterschiedliche Interpolation); `quantiles(...,
  method="inclusive")` statt Default `"exclusive"` (letzteres kann außerhalb `[min,max]`
  extrapolieren — für einen Operator verwirrend).
- **LEFT JOIN, nicht INNER** — die Score-Verteilung zählt jede `reward_pts`-Zeile, auch falls
  ein Join-Partner je fehlen sollte; `account` degradiert dann zu `NULL`→„unknown" statt eine
  Score-Zeile stillschweigend zu droppen.
- **`trade_outcomes.account` ist NULL für Zeilen vor Migration 002** (kein Backfill) → der
  „unknown"-Bucket ist kein Edge-Case, sondern erwartetes Verhalten auf der echten DB.

### Verifiziert (gemockt/lokal — keine echte DB berührt, Live-Lauf = Operator)
- `pytest tests -q` → **20 passed**. `python scripts/diag_score_distribution.py --help` exit 0.
- Manueller Smoke-Test gegen eine Scratch-DB (nicht `data/trading_bot.sqlite`): befüllter Pfad
  (4 Zeilen, gemischte Accounts) und der `database not found`-Pfad beide mit korrekter stderr-
  Narrative + stabilem stdout-JSON bestätigt.
- **Regression unberührt** (kein Trading-Code angefasst): `pytest phase8_scheduler/tests -q` →
  weiterhin **181 passed**.

### Next
- **Operator:** `python scripts/diag_score_distribution.py` gegen die echte
  `data/trading_bot.sqlite` laufen lassen und die Ausgabe (v. a. `n`, `current_score`,
  `below_50`/`below_35`-Anteile, `median`/`p25`) zurückmelden — das gated die Floor-Werte in
  **Step 3 (B: Clamp/Floor entkoppeln + relaxen)**. Bei sehr kleinem `n` (aktuell erwartet, nur
  eine Handvoll früherer Demo-Trades) ist die Verteilung nur ein grober Hinweis, kein hartes
  Signal — `small_sample: true` macht das im Output explizit.
- **Danach Step 2 (C — Universum als `InstrumentSpec`-Liste, größter Hebel)**, dann Step 3 (B)
  mit den jetzt gemessenen Werten, dann Step 4 (A — Lesson-Provenance). Plan:
  `docs/concepts/phase8_v1.5_hotfix_plan.md`.
- **Commit:** vorgeschlagen, wartet auf Trigger durch den Nikinger (Working Agreement
  unverändert — Claude committet nicht automatisch).

### Offene Punkte / blockers
- Keine. Das Script ist bewusst minimal (nur `--db-path`) — kein `--json`-Flag nötig (JSON ist
  immer auf stdout), kein Limit (volle Historie gewollt, anders als die Webui-Sparkline-Cap 200).

---

## Session stopped — 2026-06-30 (v1.5-Hotfix: initiales Housekeeping — Step 0 + Step 0b, KEINE Trading-Code-Änderung)

> **Auslöser:** der Nikinger startet die v1.5-Hotfix-Implementierung (`docs/concepts/
> phase8_v1.5_hotfix_plan.md`, der Browser-Planungs-Output). Erste Aktion gemäß Plan: **Step 0
> (Cleanup + Verify-Baseline)** + **Step 0b (Doku-Reconciliation)**, „ein Schritt nach dem
> anderen" — Step 1 (Diagnostic-Script) und die echten Fixes (C/B/A) sind explizit **nicht**
> Teil dieser Session. Reine **Docs + git-hygiene**, kein Trading-Code berührt.

### Completed
- **Branch:** `phase8-v1.5-hotfix` von `main` (HEAD `457dc9e`) erstellt — alle v1.5-Commits
  laufen hier, nicht auf `main`.
- **Step 0a (Turbo-Cleanup) — bestätigter No-Op.** `grep` nach `turbo_research|
  pre_trade_option_check|strike|otm|issuer` über `*.py` → **0 Treffer**. Alle `CALL`/`PUT`-Treffer
  sind Guard-Kommentare/Tests, die die Options-Vokabel **ablehnen**, oder der HTTP-Verb `PUT`.
  Nichts zu entfernen — wie schon am 2026-06-27 dokumentiert, jetzt erneut bestätigt.
- **Step 0c (Verify-Baseline) — grün, wahre Testzahlen ausgelesen** (nicht geraten): `pytest`
  pro Phase separat (gleicher `tests.conftest`-Namenskollisions-Grund wie immer) →
  **P1 52 · P2 62 · P3 70 · P4 96 · P5 146 · P6 70 · P7 128 · P8 181** — alle grün. Damit
  **P8 = 181** (nicht 173) und **P4 = 96** (nicht 94) als wahre aktuelle Werte bestätigt.
- **git-Hygiene (`.gitignore`):**
  - P8-Laufzeit-State ergänzt: `data/state/scheduler_state.json`,
    `data/state/scheduler_command.json`, `data/state/KILL` (gleiches Reconciliation-Muster wie
    P3/P4/P5/P6 zuvor — diese drei waren schlicht nie ergänzt worden).
  - Harness-Artefakte ergänzt: `.claude/`, `.agents/`, `skills-lock.json` (lokales Dev-Tooling,
    kein Projekt-Source — Operator-Entscheidung diese Session).
- **Architektur-Diagramm an den „Right Place" verschoben** (Operator-Entscheidung): die
  untracked `docs/concepts/tradingbot_v2_architecture_concept.svg/.pdf` (byte-identisch mit dem
  zuvor gelöschten `docs/concepts/tradingbot_v2_architecture.svg/.pdf`, 45142 Bytes SVG bestätigt)
  → `docs/architecture/tradingbot_v2_architecture.svg/.pdf` (der von README/ARCHITECTURE.md/
  root-`CLAUDE.md` referenzierte, zuvor **tote** Pfad — `docs/architecture/` war leer). Git
  erkannte es automatisch als Rename. Die per-Phase `*_konzept`/`*_architecture`-SVG/PDF-Exports
  bleiben in `docs/concepts/` (Konvention: sibling zur `.md`) und wurden dort getrackt.
  **`ROADMAP.md`** (stale getrackte Kopie) entfernt, **`ROADMAP(updated).md`** (die as-built-
  Ersatzfassung aus der Browser-Session) an ihre Stelle umbenannt.
- **`ARCHITECTURE.md` auf as-built gebracht** (war seit 2026-06-16 stale, vor-Phase-5-Vokabular):
  `turbo_research.py`→`research.py` (mit Hinweis: `turbo_candidates.json` behält den
  eingefrorenen Legacy-Namen); `pre_trade_option_check()`→die echten 4 VETOs (`status_window`/
  `spread`/`momentum`/`position_conflict`, `execution/vetos.py`); Gate-5 `CALL/PUT`→**BUY/SELL**;
  Gate-1-Fenster `09:30–11:19`→**`09:00–17:30`** (echte `ExecutionConfig`); Gate-4-Sizing auf
  **risk-per-trade ÷ stop-distance**; Friend-Bot-Reward-Formel (`base+gain×10`) durch das echte
  **Phase-7-Prozess-Score-Modell** ersetzt; `longterm_pre_trade_check() ≥120 Tage`-VETO als
  **deferred auf Phase 9f** markiert (nicht aktuell); **Phase 7 + 8 zu Komponenten + Per-Phase-
  Link-Liste ergänzt** (stoppte vorher bei P6); Risk-Liste #2 („Score-as-emotion") auf „durch
  Phase 7 adressiert" aktualisiert; #1 (Force Trigger) um den Fund ergänzt, dass das P2-Schema-
  Feld `force_trigger_locked` existiert, aber **keine** Force-Trigger-Funktion es bisher
  durchsetzt (kein neuer Scope — nur ehrlich dokumentiert). Alle Edits halten die
  Ehrlichkeits-Leitplanke: keine Produktions-Autonomie-, Lessons-Qualitäts- oder Edge-Behauptung.
- **README.md / root `CLAUDE.md` / `ROADMAP.md`: KEIN Edit nötig.** Die ursprünglich vermutete
  „181 vs. 173"-/„94 vs. 96"-Inkonsistenz erwies sich bei genauerem Lesen als **falscher Alarm**:
  die „Current state"/„Stand"-Header-Abschnitte (die **aktuell geltenden** Aussagen) sagen in
  allen drei Dateien bereits korrekt **181**; die `173`-/`94`-Vorkommen liegen ausschließlich in
  **datierten historischen `## Session stopped`-Journal-Blöcken**, die den Zustand zum jeweiligen
  damaligen Zeitpunkt korrekt beschreiben (z. B. der 2026-06-29-Block, bevor die UI-Runden 2–6
  fünf weitere Tests addierten: 173→178→181). Diese rückwirkend zu „korrigieren" wäre
  revisionistisch und würde der eigenen Journal-Konvention des Projekts widersprechen. **Hygiene-
  Prinzip angewandt: keine Aktion, wo keine nötig ist** — dem Nikinger hiermit ehrlich gemeldet
  statt erzwungener Edits.

### Verifiziert
- `pytest phase8_scheduler/tests -q` → **181 passed** (re-run nach allen Doc-Edits — unverändert,
  da kein Code berührt wurde). Alle Phasen P1–P8 separat grün (s. o.).
- `git status --short` ist sauber: `ROADMAP.md` getrackt (nicht „(updated)"), Harness-Dirs +
  P8-State-Dateien ignoriert (`git check-ignore` bestätigt alle sechs Pfade), Architektur-Diagramm
  unter `docs/architecture/`, kein toter Link mehr (`grep` über README/ARCHITECTURE/CLAUDE.md
  bestätigt: alle drei zeigen auf den jetzt existierenden Pfad, keine Reste auf den alten).
- Kein Legacy-/Options-Vokabular mehr als *aktuelle* Aussage in `ARCHITECTURE.md` (nur die
  Reconciliation-Notiz + ein „kein CALL/PUT"-Guard-Satz bleiben — beide gewollt).

### Next
- **Step 1 (operator-run, danach):** `scripts/diag_score_distribution.py` (read-only
  `bot_score`-Verteilungs-Diagnostic) bauen + vom Nikinger laufen lassen — die Werte gaten die
  Floor-Tuning-Entscheidung in Step 3 (B).
- **Danach Steps 2–4** (der eigentliche Fix): C (Universum als `InstrumentSpec`-Liste, größter
  Hebel) → B (Clamp/Floor entkoppeln + relaxen) → A (Lesson-Provenance). Plan:
  `docs/concepts/phase8_v1.5_hotfix_plan.md`.
- **Commit:** zwei vorgeschlagene atomare Commits warten auf Trigger durch den Nikinger (siehe
  Plan-Datei `~/.claude/plans/hello-claude-and-welcome-bubbly-barto.md`):
  1. `chore: gitignore P8 state + harness artifacts; move arch diagram to docs/architecture`
  2. `docs: reconcile ARCHITECTURE.md to Phase-8 as-built`

### Offene Punkte / blockers
- Keine technischen Blocker. Eine Stilfrage für den Nikinger (nicht blockierend, nur notiert):
  das P2-Schema-Feld `force_trigger_locked` existiert seit Phase 2, wird aber von keiner
  Funktion durchgesetzt — kein v1.5-Scope, aber ein Hard-Rule-5-relevanter Gap, falls Force
  Trigger je gebaut wird (P9+).

---

> **Auslöser:** der Nikinger — Phase 8 ist code-complete und KÖNNTE gemerged werden, wartet aber auf
> einen „echten" autonomen Demo-Trade, der **nie oder sehr spät** kommt. Auftrag: **read-only Analyse +
> ein Handover-File** (kein Code), das die drei Ursachen benennt + Lösungsrichtungen vorschlägt, für eine
> **Claude-Web-Planungssession** (→ detaillierter v1.5-Plan). Phase 8 darf mit ehrlichen Flags gemerged
> werden. **Auto-Modus** (die Aufgabe IST das Schreiben eines Plans). **Kein Code geändert** (nur read-only
> grep/Read + ein neues `.md`).

### Completed
- **`phase8_scheduler/PHASE8_V1.5_HOTFIX_HANDOVER.md`** (NEU) — der Handover für die Web-Planungssession.
  Struktur: TL;DR-Tabelle · Phase-8-Ist-Stand (verified/unverified) · §2 Issue C · §3 Issue B · §4 Issue A
  (je code-anchored Diagnose + Optionen + offene Fragen) · §5 Cross-Cutting-Constraints · §6 Merge-Empfehlung
  mit ehrlichen Flags · §7 v1.5-Sequencing · §8 Datei/Zeilen-Anker. **Diagnose + Optionen, kein fertiger
  Plan** (das ist die Web-Session).
- **Memory** geschrieben: `project_phase8_v15_hotfix.md` (+ MEMORY.md-Index-Zeile) — v1.5 = vereinbarter
  nächster Track.

### Die drei Ursachen (code = source of truth, alle im Handover verankert)
- **C (Hauptblocker) — Variety:** Universe = EIN Instrument `epic_allowlist = ("IX.D.DAX.IFMM.IP",)`
  (`research/models.py:320`). Jedes neue Epic braucht P4-Allow-list **+** P3-`TickerMapper`-Eintrag
  (`external_data/ticker_map.py`) **+** Volume-Proxy **+** Sizing-Sanity. Größter Hebel.
- **B — Richtungssignal zu stark:** unter `bot_score < 50` feuern ZWEI Clamps zusammen — Long-Bias →
  BUY-only (`candidate_filter.py:70+`) **und** Confidence-Floor springt 55→70 (`candidate_filter.py:47-66`,
  `models.py:328-329`). Genau das hat den 2026-06-29-Lauf abstained (Score 45.83). Fix: lockern/entkoppeln,
  damit überhaupt ein Candidate entsteht → die **bestehende P6-Debatte + die 4 VETOs** differenzieren
  (kein neues AI).
- **A — Lessons unecht:** Verifikations-Trades speisen `get_recent_lessons(5)` in den P4-Prompt
  (`context_builder.py:184`), keine Provenance-Filterung. P7 hat den `account`-Tag (demo/live,
  `models.py:145`), aber KEIN „Verifikations-Trade"-Flag. Quarantäne/Purge — aber echte Lessons fließen
  erst, nachdem C/B echte Trades erzeugen (Sequencing).

### Merge-Empfehlung (im Handover §6, ehrliche Flags)
- **Merge `phase8-scheduler` → `main` jetzt**, geflaggt „code-complete, mechanisch bewiesen (181 Tests),
  autonomer-Trade-unverifiziert". Der Rest-Live-Beweis ist von der **Research-Überkonservativität** (C/B)
  geblockt — eine Strategie-Schicht-Sorge, sauberer als eigener v1.5-Hotfix auf frischem Branch getrackt
  als am Phase-8-Tail. v1.5 NICHT in `phase8-scheduler`.
- ✅ verified: Daemon-Lifecycle · State · autonomes echtes P4-Research mit korrektem Fail-Safe-Abstain ·
  Reconcile+Reward auf realen früheren Trades · scharfes Token-Budget · read-only Web-UI.
- ⚠ NOT verified: netto-neuer autonomer open→close in einem sauberen Lauf · Safety-Breaker, die
  **tatsächlich auslösen** · Mehr-Tage-Verhalten · Edge/Profit (nie im Scope).

### Verifiziert
- **Kein Code geändert** — `git status` zeigt nur das neue `.md` (+ die Memory-Dateien außerhalb des Repos).
  Bestands-Tests unberührt (P1 52 · P2 62 · P4 94/96 · P5 146 · P6 70 · P7 128 · P8 181). Read-only Analyse.

### Next
- **Nikinger / Claude Web:** aus dem Handover (§2–§4 + §5 + §7) den detaillierten v1.5-Plan bauen, dann
  zurück zu Claude Code zur Umsetzung. Empfohlene Reihenfolge: **erst messen** (live `bot_score`-Verteilung,
  wie oft < 50?) → **C** (1–2 kuratierte Instrumente) → **B** (Clamp/Floor entkoppeln/lockern für die
  Datensammlung) → **A** (Lesson-Provenance) → Operator-Live-Lauf fängt den netto-neuen open→close + einen
  auslösenden Safety-Breaker.
- **Merge:** wenn der Nikinger ihn triggert (Phase 8 mit ehrlichen Flags → `main`).

### Offene Punkte / blockers
- Keine technischen Blocker fürs Handover. Offene **Entscheidungen** für die Web-Session (im Handover als
  „Open questions" gelistet): welche IG-Demo-Epics confirmt der Operator? Permanente vs. temporäre
  „Data-Collection-Mode"-Lockerung? Lesson-Provenance per Spalte (Migration 003) oder Heuristik?

---

## Bugfix — 2026-06-29 (erster `live_test`-Lauf: `'Envelope' object has no attribute 'get'`)

> **Auslöser:** der erste Operator-`live_test.py`-Lauf gegen IG-Demo brach im Preflight ab —
> `'Envelope' object has no attribute 'get'`. **Code = Source of Truth.**

### Ursache
- Die Phase-1-`Envelope` (`broker_wrapper/envelope.py`) ist ein **`@dataclass`** mit Attributen
  `.ok` / `.data` / `.error` — **keine** Mapping, **kein** `.get()`. `runner.py` las den
  `broker.connect()`-Return aber mit **`env.get("ok")`** (in `preflight` **und** `_warm_session`)
  und das `_BrokerLike`-Protocol behauptete fälschlich „a mapping with an `'ok'` key".
- **Warum CI grün, live rot:** der Unit-Test-`_FakeBroker` gab **`dict`s** zurück (`{"ok": …}`) →
  `.get()` funktionierte im Test, schlug aber gegen den **echten** `IGAdapter.connect() -> Envelope`
  fehl. Klassischer „fake diverges from the real return shape" → live-only Bug, in CI unsichtbar.

### Fix (rein in `phase8_scheduler/`, additiv außerhalb der zwei Lese-Stellen)
- **`scheduler/runner.py`:** `env.get("ok")` → **`env.ok`**, `env.get("error")` → **`env.error`**
  (beide Stellen, `preflight`:202 + `_warm_session`:338). Neues `_EnvelopeLike`-Protocol (liest
  `.ok`/`.error` per Property) + `_BrokerLike` korrigiert (`connect`/`disconnect -> _EnvelopeLike`);
  `Mapping`-Import entfernt (ungenutzt). Dated Docstring-Reconciliation #8. `is_connected() -> bool`
  war **nie** betroffen (bare bool).
- **`tests/test_runner.py`:** neuer `_Env`-Stand-in (`.ok`/`.error`, **kein** `.get`); `_FakeBroker`
  gibt jetzt `_Env` zurück statt `dict` → die Fakes **matchen die echte Envelope-Form**. **+1
  Regressions-Test** `test_broker_envelope_read_by_attribute_not_mapping` (asserted: der Return hat
  **kein** `.get`, und `run()` läuft trotzdem durch → ein dict-style-Read würde wieder failen).

### Verifiziert (gemockt / offline — kein Netz; Live = Operator-Re-Run)
- `pytest phase8_scheduler/tests -q` → **172 passed** (171 + 1 Regression). `py_compile` clean.
  Regression unberührt (Edit nur in `phase8_scheduler/`): P1 52 · P2 62 · P4 94 · P5 146 · P6 70 · P7 128.
- **Offen:** Operator-`live_test.py`-Re-Run gegen IG-Demo (der Preflight passiert jetzt den
  Broker-Connect). Erwartung unverändert (sauberer Stop + State + CLOSED-Trade `reward_pts` **oder**
  valider No-Trade-Lauf).

---

## Session stopped — 2026-06-29 (erster grüner `live_test`-Lauf — Analyse + Token-Budget scharf)

> **Auslöser:** der Nikinger hat `live_test.py --iterations 2 --max-hold-min 1 --daily-loss-cap 1800`
> gegen IG-Demo gelaufen → **RESULT 3/3 passed**. Analyse-Auftrag: „Problem? Wenn ja, Fix-Plan."
> **Befund: kein Bug.** Die 3/3 sind echt. Aber der Lauf hat die Mission **nur teilweise** bewiesen
> (Research hat beide Zyklen abstained) + er deckte eine deaktivierte Safety-Kappe auf.

### Analyse (Code = Source of Truth)
- **3/3 PASS ist by-design, kein maskierter Fail.** `live_test.py` (Docstring Z. 9–16) ist bewusst
  lenient: ein sauberer No-Order-Lauf (Abstain/VETO/Cap/ruhig) ist ein **valider PASS** (P5/6/7-Disziplin).
- **Warum Research beide Zyklen abstained:** der echte P4-Call (`claude-sonnet-4-6`) lief korrekt, aber
  der Markt-Score war `45.83 < 50` → KONSERVATIV → `candidate_filter.confidence_threshold` zog den
  **strengeren Floor 70.0** (statt Default 55.0, `research/models.py:327-329`). Der LLM-Self-Report blieb
  drunter → Abstain. **Risk-Management-Clamp by-design, kein Defekt.** Floor **nicht** gesenkt (Out of
  scope: P4 markiert ihn als provisorisch, P7-outcome-anchored ersetzt ihn).
- **Der Reward-Loop wurde DOCH auf echten Daten geübt:** der Reconcile-Pass löste **2 reale** frühere
  Demo-Trades auf (`DIAAAAXTGBTEYAC`, `DIAAAAXTGMAF2A9`) — IG-History geholt, P&L nachgezogen, echte
  Haiku-Lessons extrahiert. open→close→reward→lesson ist damit auf realen Outcomes live-bewiesen.

### Completed (Fix — rein in `phase8_scheduler/`, additiv)
- **Token-Budget by-default scharf** (der Nikinger: „real cap + flag, $0.75–€1/Tag max").
  `scheduler/config.py`: `daily_token_budget` Default `None` → **`200_000`** (≈ €0.82/Tag bei der
  Sonnet-Research-Rate ~1700 Tok ≈ $0.0075/Call, die einen Runaway dominiert → ~227K Tok/$;
  Cache-Reads werden voll gezählt → der Breaker trippt **vor** €1, nie danach). `None` bleibt als
  **expliziter** Deaktivierungs-Sentinel.
- **Flags:** `scheduler/run.py` `--daily-token-budget` Default `None`→`200_000` + neues
  `--no-token-budget` (spiegelt `--no-loss-cap`); `scripts/live_test.py` neues `--token-budget`
  (Default `200_000`, `0` → deaktiviert). Beide threaden in `SchedulerConfig`.
- **Tests (in-phase):** `test_run.py` Defaults `200_000` + neuer `test_no_token_budget_disables_breaker`;
  `test_config.py` Default `200_000`. **→ 173 passed** (172 + 1).
- **Doku:** Konzept §1 (Z. 244) + §7 (Z. 495) dated annotiert; root `CLAUDE.md` Phase-8-Block ehrlich
  (proven/unproven, kein ✅-Flip).

### Verifiziert (gemockt / offline — Live = Operator)
- `pytest phase8_scheduler/tests -q` → **173 passed**. `python -m scheduler.run --help` + `live_test.py
  --help` exit 0, zeigen die neuen Defaults. Mit Default-Config feuert die „token budget is DISABLED"-
  WARNING **nicht** mehr. Regression unberührt (Edit nur in `phase8_scheduler/`).

### Was der 2026-06-29-Lauf BEWIESEN hat
- ✅ Daemon-Lifecycle: Preflight → bounded Loop → sauberer Shutdown (keine Exception/Orphan).
- ✅ State-Persistenz (`scheduler_state.json`, alle Felder).
- ✅ Autonomes echtes P4-Research lief (Sonnet) + korrekter Fail-Safe-ABSTAIN im KONSERVATIV-Regime.
- ✅ Reconcile + Reward-Loop auf **realen** früheren Demo-Trades (2 aufgelöst, echte Haiku-Lessons).

### NOCH NICHT bewiesen (braucht einen echten Mehr-Zyklen-/Mehr-Tage-Lauf)
- ❌ Ein **netto-neuer** autonomer Trade, in **einem** sauberen Lauf geöffnet **und** geschlossen
  (Research abstained beide Zyklen → der Auto-Confirm-/Order-Pfad aus einem frischen autonomen
  Candidate wurde diesen Lauf **nicht** end-to-end beobachtet; er geschah nur über frühere Läufe,
  sichtbar als die 2 reconciled Trades).
- ❌ Die Safety-Breaker, die **tatsächlich auslösen** (kein Verlust eingetreten; Budget war diesen Lauf
  aus — jetzt scharf, aber das Auslösen ist weiterhin live-unverifiziert).
- ❌ Mehr-Zyklen-Verhalten über ein volles Handelsfenster / mehrere Tage (nur 2 bounded Zyklen).
- ❌ Edge / Profitabilität (nie im Scope — Langzeit-Live-Betrieb).

### Next
- **Operator:** `live_test.py` in einem **nicht-konservativen** Fenster (Score ≥ 50 → Floor 55) erneut
  laufen, um einen netto-neuen autonomen open→close zu fangen; ggf. ein längerer Mehr-Zyklen-Lauf.
  WARNING „token budget is DISABLED" muss weg sein.
- **Erst danach** Doku-Flip auf ✅ (ROADMAP/README) + Merge `phase8-scheduler` → `main`. Gated auf die
  4 unbewiesenen Punkte.
- **Commit:** committet, **falls** der Operator es triggert (Branch `phase8-scheduler`); „Commit ⇒
  Note-Update" im selben Commit.

---

## UI-Erweiterung — 2026-06-29 (Token-Meter + detailliertes Last-Cycle-Reasoning)

> **Auslöser:** der Nikinger ließ den Daemon + die UI laufen, alles funktionierte, und bat — **vor** einem
> späteren Overhaul — um zwei **additive** Karten. Bewusst **kein** Redesign: rein additiv im bestehenden
> Dark-Neumorphism-Token-Set (`static/style.css` `:root`); **kein** Design-Skill (der Overhaul ist später).
> **UI-only, file/DB read-only** — kein Trading-/Scheduler-Modul berührt.

### Completed (alle in `webui/`)
- **Token-Meter (`GET /api/token_usage`):** liest die geteilte `llm_usage.json` über die **importierten**
  `scheduler.budget`-Helfer (`_load_log`/`_record_tokens`/`_record_local_date` — identische Berlin-Tagesgrenze
  wie der Breaker), summiert **heutige** Tokens + €/$-Kosten + Calls, gibt `{consumed_tokens, budget, percent,
  cost_eur_today, cost_usd_today, calls_today}`. Fail-soft (fehlend/korrupt → Nullen). Neue Full-Width-Card
  `card--tokens` (Bar amber >80 % / rot ≥100 %; `budget=None` → „off"/`percent=None`).
- **Last-Cycle-Reasoning (`GET /api/last_cycle` erweitert, additiv):** zusätzlich `research_pick` (letzter
  `turbo_candidates.json`-Eintrag: `reasoning`/`llm_confidence`/`direction`/`score`/`threshold`/`generated_at`)
  + `debate` (letzter `debate_log.json`-Eintrag: `final_decision`/`final_direction`/`confidence`/`rounds`/
  `rationale` + `transcript` Bull/Bear/Judge mit vollem `text`; `usage` gedroppt für schlanke Payload). Beides
  **most-recent on disk** → die UI labelt sie mit eigenem Timestamp + **„from an earlier cycle"**-Stale-Marker
  (Vergleich Artefakt-Datum vs. `session_date`), da Pick/Debatte nur bei echtem Pick/Debatte entstehen. Card
  `card--cycle` um RESEARCH-PICK- + DEBATE-Blöcke erweitert (collapsible `<details>` je Agent, Farbcodierung
  Bull=grün/Bear=rot/Judge=lila). Neuer fail-soft Helfer `_load_json_array`.
- **Ehrliche Grenze (dokumentiert, nicht gefixt):** der **Abstain-Prosa-Grund** wird nirgends persistiert (nur
  der Code `LLM_ABSTAIN`) → auf einem Abstain-Zyklus bleibt der Research-Pick-Block leer; das Reasoning kommt
  aus dem **letzten** echten Pick/Debatte. Echten Abstain-Text gäbe es erst mit einer P4/P9-Änderung (das
  reservierte `no_trade_reason`-Taxonomie-Gerüst) — außerhalb Scope.

### Verifiziert (gemockt/offline + visuell — kein Netz nötig fürs UI)
- `pytest phase8_scheduler/tests -q` → **178 passed** (171 → 178: +3 token_usage [heute-only / fehlender Log /
  Budget=None→percent None], +2 last_cycle [Pick+Debatte populiert / fehlende Artefakte→null, Bestandsfelder
  unberührt]). `node --check app.js` + `py_compile api.py` clean.
- **Visuell** gegen die echte `data/state/` (separater Port 8011, Operator-`:8000` unberührt) via
  agent-browser-Screenshot: Token-Card 18 %/€0.1555/26 Calls; Last-Cycle zeigt leeren Pick (aktueller Abstain)
  + die **stale 06/16-Debatte** mit vollen Bull/Bear/Judge-Transkripten (Stale-Marker korrekt).

### Next (unverändert)
- Operator-Re-Run von `live_test.py` im nicht-konservativen Fenster; **danach** Doku-Flip auf ✅ + Merge.
- **Commit:** committet, **falls** der Operator es triggert (Branch `phase8-scheduler`); „Commit ⇒ Note-Update".

---

## UI-Erweiterung — 2026-06-29 (LLM-Abstain-Prosa-Grund in der UI)

> **Auslöser:** der Nikinger wollte den **echten LLM-Abstain-Grund** (Prosa) sehen, nicht nur den Code
> `LLM_ABSTAIN`. **Befund (klein):** das Schema (`research/prompt.py`) hat `required:[abstain, reasoning]`
> → das Modell liefert **immer** eine Prosa-`reasoning`, auch bei `abstain=true` — sie wurde nur verworfen
> (`validator.py:100-102` gibt valid-abstain ohne sie zurück; `research.py:199` nutzt nur den Code-String).
> **Kein Schema-/Prompt-Change, keine neue AI.**

### Completed (additiv; **eine** P4-Berührung, sonst P8/UI)
- **P4 `research/research.py`** (cross-phase, additiv, **display-only — gatet nichts, wird nie ein
  Candidate**, root rule 3 intakt): neues Instanz-Attribut `last_no_pick_reasoning`, in `run()` pro Zyklus
  auf `None` zurückgesetzt und **nur** auf dem echten valid-abstain-Zweig (`vr.candidate is None`,
  `abstain=true`) aus `raw["reasoning"]` (gestrippt) gefüllt. Bewusst **nicht** auf REJECT/Filter (dort ist
  `reasoning` die *Pick*-Begründung → als Skip-Grund irreführend).
- **P8 `scheduler/state.py`:** neues Feld `last_no_trade_detail: str | None` (display-only) + Reset im
  `rollover_if_new_day`. `load()` self-heilt unbekannte/fehlende Keys → additiv-sicher.
- **P8 `scheduler/research_tick.py`:** setzt `state.last_no_trade_detail` neben `last_no_trade_reason` —
  abstain → `getattr(self._research, "last_no_pick_reasoning", None)` (defensiv, Fake ohne Attr ok),
  pick/exception → `None`. `_ResearchLike`-Protocol um das optionale Attr ergänzt.
- **P8 `webui/`:** `/api/last_cycle` gibt `last_no_trade_detail` zurück; `app.js` `renderCycle` zeigt es
  **im RESEARCH-PICK-Block als „ABSTAIN REASONING"**, wenn kein Pick aber ein Detail da ist (sonst der
  bisherige Empty-State). Reuse der bestehenden `.reason-block`-Styles — **kein** neues CSS.

### Verifiziert (gemockt/offline + visuell)
- `pytest phase4_research/tests -q` → **96** (94 + 2: abstain captures prose / pick clears it).
- `pytest phase8_scheduler/tests -q` → **181** (178 + 3: research_tick surfaces/clears detail, state
  round-trip+rollover, webui last_cycle exposes detail). `node --check app.js` clean.
- **Visuell** (throwaway-Webui mit Temp-State, das `last_no_trade_detail` trägt): RESEARCH PICK rendert
  „ABSTAIN REASONING" + die volle Modell-Prosa. Screenshot an den Operator.
- **Regression** logisch unberührt (P4-Change = additives Attribut; P6/P7 reusen `LLMClient`/`token_meter`,
  nicht die `Research`-Klasse).

### Grenzen (ehrlich, dokumentiert)
- **Füllt sich erst beim NÄCHSTEN Abstain-Zyklus nach Daemon-Neustart** — alte Zyklen sind nicht
  backfillbar (die Prosa wurde damals nicht gespeichert).
- **Nur der echte `abstain=true`-Pfad** trägt Prosa; Pre-LLM-Aborts (empty universe, LLM-Error,
  session-health) + Validator/Filter-Rejects → `last_no_trade_detail` bleibt `None`, der Code-Grund zeigt.
- **Operator:** Daemon **und** Webui neu starten (neue P4/P8-Code), dann Browser hart neu laden.

---

## UI-Overhaul Runde 6 — 2026-06-29 (Score-Gravur: breiter + tiefer, ohne Light-Lippe)

> **Auslöser:** der Nikinger: Gravur stimmt, aber **breiter (2–3×, kaum sichtbar)**, die **Light-
> Lippe weglassen** (passt nicht), und bei mehr Breite **tiefer** wirken lassen. Reine Tuning-Edit.

### Completed
- **`.spark-light` entfernt** (CSS + `app.js`-Pfad) — keine helle Unterlippe mehr.
- **Breiter + tiefer:** statt einer schmalen Schattenkante jetzt **zwei gestapelte dunkle Soft-
  Layer** als breite Nut: `.spark-shadow2` (16px, blur 2.8, α0.62) + `.spark-shadow` (9px, blur 1,
  α0.96) unter dem Amber-Kern (`.spark-line` 5px) → der Graph sitzt in einem klar sichtbaren, tiefen
  Trench (kein Light-Lip). `app.js` zeichnet beide Schatten leicht nach unten versetzt (`translate
  0,1.5`/`0,1`); Area-Fill auf 0.2 reduziert; `is-fresh`-Draw-on deckt beide Schatten + Linie.

### Verifiziert
- `pytest phase8_scheduler/tests -q` → **181 passed**; `node --check app.js` clean; visual :8011 +
  Score-Close-up (breite tiefe Nut, kein Light-Lip), Konsole fehlerfrei.
- **Commit:** committet, falls der Operator es triggert (Branch `phase8-scheduler`).

---

## UI-Overhaul Runde 5 — 2026-06-29 (Score: die Graph-LINIE selbst in den Metall graviert)

> **Auslöser:** der Nikinger: der tiefe Recess „looks great", aber gemeint war — **die Graph-Linie
> selbst** (nicht ein Rechteck/Well drumherum) **größer** machen und **ihre Form** als Stempel nutzen,
> „so that the graph itself has weight". Möglich? Ja. Reine `style.css` + ein `app.js`-SVG-Markup-Edit.

### Completed
- **`.spark-well` → flache polierte Metallplatte** (statt tiefer Recess): mid-tone `var(--surface)` +
  leichter `inset`-Schatten + polierter Sheen `::before`; Höhe 168→**184**. Die Platte ist jetzt nur
  noch der Träger — der Held ist die gravierte Linie.
- **Graph-Linie selbst graviert** (`app.js` `renderScore` zeichnet 3 Pfade desselben `line`-d):
  `.spark-shadow` (dunkle Kopie, `translate(0,-2.2)` = obere Schattenkante) + `.spark-light` (helle
  Kopie, `translate(0,2.2)` = untere Licht-Lippe) flankieren den **dickeren Amber-Kern** (`.spark-line`,
  `stroke-width 5`, `vector-effect:non-scaling-stroke`) → die Linie sieht in die Platte **eingestanzt**
  aus und bekommt Gewicht. Area-Fill auf opacity 0.3 reduziert; End-Dot größer (r 4.5) mit dunklem Ring.
  `is-fresh`-Draw-on animiert jetzt alle drei Pfade synchron.

### Verifiziert (gemockt/offline + visuell)
- `pytest phase8_scheduler/tests -q` → **181 passed**; `node --check app.js` clean.
- **Visuell** :8011 @1920×1080 (+ Score-Close-up): die Graph-Linie liest als in die polierte Cognac-
  Platte gravierte Nut (dunkle Ober-, helle Unterkante), dicker + mit Gewicht; Konsole fehlerfrei.
- **Commit:** committet, falls der Operator es triggert (Branch `phase8-scheduler`); „Commit ⇒ Note-Update".

---

## UI-Overhaul Runde 4 — 2026-06-29 (Palette: Cognac-Metall + dunkelbraunes Leder · polished-scraped · Score-Gravur)

> **Auslöser:** der Nikinger wollte die Palette durchprobieren. Ich habe via `<body data-theme>` drei
> Kandidaten gebaut (steel/cognac/nickel) + offline-Screenshots gezeigt. **Wahl: Cognac-Metall**
> („unique element color"), aber Leder **sehr dunkelbraun, ~#0C0C0D-Realm**. Plus zwei Korrekturen:
> (a) Metall-Textur behalten, aber **polished-scraped** statt gleichmäßig gebürstet; (b) der „stamped
> into metal"-Effekt am Score sollte **nur eine gravierte Linie UM den Chart** sein, **kein** versenktes
> Rechteck. Reine `style.css`-Änderung.

### Completed (alle in `webui/static/style.css`)
- **Palette (in `:root` gebacken, Kandidaten-Blöcke wieder entfernt):** Metall = warm Titanium/Cognac
  (`--surface #2f2b2a`, `--panel` warmes Cognac-Gradient, `--shadow-lt #4b443e` warm); Leder
  **near-black dunkelbraun** (`--bg #0c0b0a`, `--leather-grad` `#141010→#0c0b0a→#060605`). Text +
  Amber/Green/Red-Indikatoren **unverändert** (Nikinger: „seem fine"). `--leather-grad`-Variable bleibt
  (sauberer Swap-Punkt).
- **Metall-Textur → polished-scraped** (`.card` background): ein diagonaler **Reflection-Sweep** (polish)
  + zwei leicht **schräge, unregelmäßige Scrape-Linien** (eine helle 1deg, eine dunkle -1.4deg) statt der
  gleichmäßigen vertikalen Bürstung → liest poliert-geschabt, nicht gebürstet.
- **Score = tief gestanzte Graph-Fläche** (`.spark-well`): **Korrektur nach Feedback** — der „stamped
  into metal" gilt der **Graph-Fläche selbst**, „clearly visible and deep". (Ein Zwischenschritt mit nur
  einer gravierten Linie **um** den Chart war daneben.) Final: ein **tiefer Recess auf allen Seiten**
  (mehrlagige `inset`-Shadows oben/unten/links/rechts + crisper Top-Shadow-Edge + untere Light-Lippe +
  dunkler Floor `#15110f`→`--surface-2`), `::before` deepening-Vignette oben; die Orange-Nadel glüht unten
  in der Vertiefung. `.spark` z-index 2.

### Verifiziert (gemockt/offline + visuell)
- `pytest phase8_scheduler/tests -q` → **181 passed**; `node --check app.js` clean (app.js unberührt).
- **Visuell** :8011 @1920×1080: dunkelbraunes Leder, Cognac-Panels heben sich klar ab, polished-scraped
  Sheen sichtbar, Score-Gravurlinie rahmt den Chart (Close-up bestätigt), Konsole fehlerfrei. Die drei
  Kandidaten-Themes wurden per `data-theme` live gescreenshottet, dann verworfen (nur Cognac gebacken).
- **Commit:** committet, falls der Operator es triggert (Branch `phase8-scheduler`); „Commit ⇒ Note-Update".

---

## UI-Overhaul Runde 3 — 2026-06-29 (Finish: scrollendes Leder · Gasket-Mounting · Metall-Textur)

> **Auslöser:** der Nikinger: „zwei small fixes, dann kann die UI so bleiben" — (1) das Leder soll
> **nicht fixed** sein, sondern mit dem Inhalt scrollen; (2) die Panels wirken „nur draufgeworfen" →
> **mehr Abstand** + eine **mechanische Verbindung** Leder↔Panel; (3) ein bisschen **Metall-Textur**.
> Gelockte Operator-Entscheidung (AskUserQuestion): Mounting = **Stitched leather gasket** (das Leder
> umfasst + vernäht jedes Panel), nicht Corner-Bolts / Rivet-Rail. **Reine `style.css`-Änderung.**

### Completed (alle in `webui/static/style.css`)
- **Leder scrollt mit** (war `position:fixed` / `background-attachment:fixed`): `.grain` → `position:
  absolute` in einem `position:relative` Body; `html,body{height:100%}` → `html{height:100%}` +
  `body{min-height:100%}`, damit der Body mit dem Inhalt wächst und die `inset:0`-Leder-Schicht die
  **volle Scroll-Höhe** deckt (verifiziert: grain-rect ≈ docHeight). `background-attachment:fixed` weg.
- **Mehr Abstand:** `.grid` gap `clamp(14,1.6vw,22)` → **`clamp(20,2.2vw,34)`**, padding großzügiger
  → mehr Leder **zwischen** den Panels (die Montagefläche).
- **Stitched leather gasket** (`.card::after`): ein gestricheltes Amber-Seam `inset:-9px` um **jedes**
  Panel auf dem Leder + Routed-Pocket-Groove (`inset 0 0 0 1px` dunkel) → das Leder „greift" und
  vernäht das Metall-Instrument. `.card{position:relative}` ergänzt (Containing-Block fürs Seam).
- **Brushed-Metal-Textur** auf den Karten: feine vertikale Striation (`repeating-linear-gradient` 90deg,
  ~0.022 alpha) über dem `--panel`-Sheen → liest als gebürstetes Metall, subtil.
- (Runde-3-Vorlauf in derselben Sitzung schon drin: tieferes Relief `--shadow-dk/lt`, `--cast`
  Ambient-Drop, domed `--panel`, Chrome-Edge/Chamfer am `.card` — die „mehr Tiefe"-Bitte davor.)

### Verifiziert (gemockt/offline + visuell)
- `pytest phase8_scheduler/tests -q` → **181 passed**; `node --check app.js` clean (app.js unberührt).
- **Visuell** :8011 @1920×1080: Gasket-Seams rahmen alle Panels, Leder zwischen ihnen sichtbar +
  **scrollt** (Scroll-Screenshot zeigt Leder unter dem Fold), Brushed-Textur subtil, Konsole fehlerfrei.
- **Commit:** committet, falls der Operator es triggert (Branch `phase8-scheduler`); „Commit ⇒ Note-Update".

---

## UI-Overhaul Runde 2 — 2026-06-29 (Leder-Dash-Cockpit: Textur + Instrumente + Motion)

> **Auslöser:** der Nikinger mochte Runde 1 („def the right decision") und wollte weiter: (1) ein
> **stoff-/lederartiger** Hintergrund, (2) die einzelnen UI-Elemente als **Instrumente** lesen (etwas
> Varianz erlaubt), (3) **kleine Libs erlaubt**, wenn sie helfen — „decent, yet unique", (4) **kleine
> statische Animationen** + Animationen beim Renew/Render + Button-Press. Gelockte Operator-
> Entscheidungen (AskUserQuestion): **odometer.js vendoren** (rollende Cockpit-Ziffern) · **Refined**
> (nicht Pronounced). Weiter **UI-only, file/DB read-only, fail-soft** — kein Trading-/Scheduler-/
> Safety-Modul berührt, `webui/api.py` unverändert. **Design-Skill** `redesign-existing-projects`
> invoked.

### Completed (alle in `webui/static/`, additiv)
- **NEU `webui/static/vendor/odometer.min.js` + `odometer-theme.css`** — odometer 0.4.8 (MIT)
  **lokal vendored** (offline-safe, **kein Runtime-CDN**; einmal beim Build via cdnjs geholt). Theme =
  **minimal** (clean, erbt unsere Mono + `currentColor`); die **car**-Variante wurde **verworfen**, weil
  sie ein `@import` auf Google Fonts trägt → das hätte die Offline-Garantie gebrochen. Geladen **vor**
  `app.js` (sonst `window.Odometer` undefined). Rollgeschwindigkeit in `style.css` auf 0.9s gedrosselt
  (Theme-Default 2s).
- **`style.css` — Leder-Dash:** `body`-Background = warmer Hide-Ton-Gradient + Edge-Vignette + die
  Ambient-Amber/Steel-Radials; `.grain` von vertikalem Brushing auf **fine-leather Pebble** (inline
  `feTurbulence` SVG-Data-URI, **kein** Asset-File, opacity 0.09, blend overlay). `background-attachment:
  fixed`. **Stitch-Naht:** ein faint amber gestricheltes `::after`-Seam unter der Topbar.
- **`style.css` — Instrumente (Varianz, thin bezels auf den drei Signatur-Stücken):**
  · **SCORE** = gerahmtes Instrument (machined Bezel-Ring + Glass-Glare-`::before`; Amber-Nadel mit Glow);
    Draw-on (`stroke-dasharray`) nur bei echtem Daten-Change.
  · **TOKEN METER** = Fuel-Gauge (`.meter-ticks` Tick-Marks + `.meter-redline` schraffierte 80→100%-
    Gefahrenzone; Bar eased width 0.7s; Normal steel-blue / warn amber / over rot unverändert).
  · **CONFIDENCE** = kleines **Dial** (inline-SVG Radial-Arc `n/n_min`, Mitte = n; Farbe via Klasse
    is-ok grün / INSUFFICIENT amber / unavailable dim) im Card-Head → **keine** Extra-Höhe.
  · Andere Karten bleiben clean Brushed-Metal (Refined, nicht über-instrumentiert).
- **`app.js` — Motion-Infrastruktur (alles fail-soft + `prefers-reduced-motion`-aware):**
  · **`setNum(id,val,dp)`** routet die Headline-Zahlen (trades-today, tokens, cost, score-now) durch den
    Odometer (rollende Ziffern) + Glow-`flash-tick` bei Change; **Fallback** `textContent`, wenn
    `window.Odometer` fehlt → UI bricht nie. **P&L NICHT über Odometer:** odometer 0.4.8 **verschluckt das
    Minus** (live verifiziert: `-41.16` → „41.16" — ein Verlust läse sich als Gewinn!) → eigener
    **`tweenSigned()`** rAF-Count-up mit `fmtSigned` (+/- korrekt).
  · **Change-Gating** (`renderIfChanged`, JSON-Vergleich pro Sektion) für cycle/score/trades/lessons →
    rebaut DOM nur bei echtem Change. **Fixt einen echten Bug:** der 7-s-Poll baute die LAST-CYCLE-Karte
    jedes Mal neu und **klappte jedes vom User geöffnete Debate-`<details>` wieder zu** — jetzt nicht mehr.
  · **Renew-Animationen:** Tick-Flash bei Wert-Change, Score-Draw-on, Confidence-Dial-Arc-Tween,
    **neue Trades-Zeile** (`row-new` Amber-Sweep, erste Paint-Runde ausgenommen), `updated`-Pip-Blink.
  · **Idle:** Brand-Mark Amber-Glow „breathe" (4.6s). **Button-Press:** Glow-Ripple `::after` + der
    bestehende Inset/translateY; Success-`flash()` `--cyan`→**`--amber`** gefixt.
  · Alle Runde-2-Animationen unter `@media (prefers-reduced-motion: reduce)` deaktiviert (CSS + JS-Guards).

### Verifiziert (gemockt/offline + visuell — kein Netz/LLM/Broker; UI importiert den Trader nie)
- `node --check app.js` clean; grep: **0** alte Palette-/`--cyan`-Reste.
- `pytest phase8_scheduler/tests -q` → **181 passed** (test_webui prüft API + index→app.js/style.css;
  die zusätzlichen Vendor-`<link>/<script>` brechen nichts).
- **Visuell** auf throwaway **:8011** (Operator-Port unberührt) via agent-browser @1920×1080: Leder-Dash
  + Stitch + die drei Instrument-Treatments + Fuel-Gauge-Ticks/Redline sichtbar; `GET /vendor/*` → **200**
  (lokal, kein CDN); **Konsole fehlerfrei**; `window.Odometer===true`; P&L = `+0.00` (Tween, Minus
  korrekt); Odometer-negativ-Bug **vor** dem Fix reproduziert + **nach** dem Fix (tweenSigned) erledigt.
- **Regression** logisch unberührt (CSS/HTML/JS-only; api.py/Trader nicht angefasst).

### Grenzen / Next
- **Operator:** im laufenden Setup nur **Browser hart neu laden** (Static + ein neues Vendor-Verzeichnis;
  **kein** Daemon-/API-Neustart nötig).
- **Static-Screenshots zeigen keine Bewegung** — die Motion (Odometer-Roll, Tweens, Draw-on, Ripple,
  Breathe) ist verdrahtet + fehlerfrei, aber im PNG nicht sichtbar; live im Browser sichtbar.
- Mission unverändert: netto-neuer autonomer open→close + auslösende Safety-Breaker gaten den ✅-Flip +
  Merge — **nicht** das UI.
- **Commit:** committet, **falls** der Operator es triggert (Branch `phase8-scheduler`); „Commit ⇒
  Note-Update" im selben Commit. **Neu im Repo:** `webui/static/vendor/` (zwei vendored Dateien).

---

## UI-Overhaul — 2026-06-29 („Mechanics Overhaul": Warm-Metal-Cockpit-Reskin + 16:9-Layout)

> **Auslöser:** der Nikinger ließ Daemon + UI laufen und wollte — während ein echter Demo-Trade
> reift — einen **visuellen** Overhaul: (1) das aus dem Konzept kopierte GitHub-Dark-Farbschema
> raus, rein ein **polierter, weicher Metall-Look** wie ein 2015+-BMW-Cockpit; (2) **16:9 oder
> breiter** statt der hohen ~1440px-Spalte. **Reskin + Re-Flow, KEIN Redesign** (die Karten +
> Neumorphism gefielen). **UI-only, file/DB read-only** — kein Trading-/Scheduler-/Safety-Modul
> berührt, `webui/api.py` unverändert. Zwei gelockte Operator-Entscheidungen (AskUserQuestion):
> **Ambient-Akzent = Amber / warm metal**; **Layout = Repack auf Instrument-Cluster (~1800px)**.
> Design-Skill `redesign-existing-projects` invoked (Projekt-Konvention).

### Completed (alle in `webui/static/`, additiv)
- **`style.css` — Palette-Swap (`:root`) „Gunmetal + Amber":** warm-graphite Canvas (`--bg
  #16151a`), brushed-panel Surfaces (`--surface #1d1c21` + neuer `--panel`-Gradient), warm-Alu
  Text (`--text #d8d2c8`/`--muted`/`--dim` in **einer** warmen Grau-Familie), **ein** Ambient-
  Akzent `--amber #e6a24c` (Brand-Mark, Tags, Score-„Nadel"-Sparkline, Focus, Control-Msg, Table-
  Hover), `--blue` → Steel-Blue **nur** als Sekundär-Info (Token-Meter-Normalbalken). Profit-Grün/
  Loss-Rot **behalten**, nur metall-weicher (`#6bbf8a`/`#e0685f`). Alle früher hardcodeten
  GitHub-Dark-rgba-Glows mit-umgefärbt (Body-Radials, Brand-Glow, Pulse, Kill-Banner, Meter-,
  Spark-Drop-Shadows). `--cyan` = Legacy-Alias auf neutrales Silber (kein zweiter Akzent).
- **`style.css` — Metall-Politur (weich, nicht überzogen):** `.card` bekommt den `--panel`-Sheen
  (Top→Bottom) + 1px Inner-Top-Highlight (`inset 0 1px 0 rgba(255,255,255,.045)` = Chrome-Kante)
  über dem bestehenden `--rise`-Neumorphism; `.grain` von horizontalen auf **vertikale** Brushed-
  Striation gedreht (opacity 0.05).
- **`style.css` — Layout (CSS-only, kein HTML-Strukturwechsel):** `.grid` max-width **1440 → 1800px**;
  12-Col via `order:` umgeordnet in einen **Landscape-Instrument-Cluster**: Reihe 1 Gauge-Band
  STATUS·CONTROL·CONFIDENCE·TOKENS (je `span 3`, vier gleiche Viertel), Reihe 2 SCORE·TRADES (je
  `span 6`), Reihe 3 LAST-CYCLE(`7`)·LESSONS(`5`). `.status-stats` von 1×4 auf **2×2** (gauge-artig,
  füllt die durch `align-items:stretch` entstehende Höhe → keine tote Fläche, CLEAR-KILL bricht
  nicht mehr um). Neuer Zwischen-Breakpoint **`max-width:1320px`** (Band → 2-across, Panels → full)
  vor der bestehenden 900px-Full-Stack-Regel.
- **`app.js` — eine Farb-Literal-Änderung:** das inline-SVG `spark-grad` stop-color `#3fb950` →
  `#e6a24c` (die einzige Farbe, die keine CSS-Var liest). Sonst **nichts** an `app.js`.
- **`screenshots/dashboard.png`** auf den neuen Look aktualisiert.

### Verifiziert (gemockt/offline + visuell — kein Netz/LLM/Broker; UI importiert den Trader nie)
- `node --check app.js` clean; grep auf alle alten Palette-Literale = **0** Rest.
- `pytest phase8_scheduler/tests -q` → **181 passed** (UI-Tests prüfen API + dass index app.js/
  style.css referenziert, **nicht** CSS-Inhalt → unberührt). Regression logisch unberührt
  (CSS/HTML-only).
- **Visuell** gegen die echte `data/state/` auf separatem Port **:8011** (Operator-Port unberührt)
  via agent-browser bei **1920×1080**: Gauge-Band + Score/Trades liegen above-the-fold (echtes
  16:9-At-a-Glance), Amber-Cockpit-Palette kohärent, kein Umbruch, Sparkline = glühende Amber-Nadel.

### Grenzen / Next (unverändert)
- **Operator:** im laufenden Setup nur **Browser hart neu laden** (Static-Reskin, kein Daemon-/API-
  Neustart nötig — nur `webui/static/*` + ein `app.js`-Literal geändert).
- Mission unberührt: der **netto-neue autonome open→close** + auslösende Safety-Breaker stehen
  weiter aus (gaten den ✅-Doku-Flip + Merge — **nicht** das UI).
- **Commit:** committet, **falls** der Operator es triggert (Branch `phase8-scheduler`); „Commit ⇒
  Note-Update" im selben Commit.

---

## Session stopped — 2026-06-28 (Modul 12: `webui/` Web-UI + reale Start/Stop-Pause — **Phase 8 code-complete**)

> Operator-Notiz: der `smoke_test` war erfolgreich; der `live_test` wartet aufs Handelsfenster.
> In der Zwischenzeit die **letzte** Einheit gebaut (Konzept §12, „zuletzt, read-mostly"). Zwei
> Operator-Entscheidungen diese Session: **Visual = Dark-Neumorphism** (GitHub-Dark-Palette aus den
> Konzept-SVGs als Canvas + die weiche Neumorphism/Glass-Tiefe aus `ui_concept/`); **Controls =
> reale Start/Stop** inkl. des Extra-Schritts (Daemon pollt die Command-Datei). Dashboard mit der
> `frontend-design`-Skill gebaut.

### Completed
- **`scheduler/command.py`** (NEU, spiegelt `killswitch.py`) — die Start/Stop-Command-Datei
  (`data/state/scheduler_command.json`), von `webui` (Schreiber) + `runner` (Leser) geteilt.
  `read_command` (`"start"`|`"stop"`|`None`, fail-soft, toleriert hand-geschriebenes bare word),
  `write_command` (atomic `.tmp`+`os.replace`, validiert `cmd`), `clear_command`. **Semantik bewusst
  ≠ KILL:** `stop` = **weiche, reversible Pause** (Daemon-Prozess bleibt am Leben), KILL = harter Stop.
  Exportiert als Modul aus `scheduler/__init__.py`.
- **`scheduler/runner.py`** (additive Edit — der „Extra-Schritt", konzept-sanktioniert §12 „Daemon
  pollt"). Loop-Top nach dem Kill-Check: `command.read_command(config.command_path) == "stop"` →
  **Pause-Iteration** (kein warm/reconcile/research/execute; `clock.sleep(idle_poll)`; `continue`;
  **kein** `break`, **kein** State-Feld berührt — die UI leitet PAUSED aus der Command-Datei ab) → ein
  späteres `start`/Löschen resumed denselben Daemon. **Keine Command-Datei ⇒ bit-identisch** (Default
  unverändert; additiv wie die `reward_sink`/`debate_runner`-Nähte). Docstring-Reconciliation #7 ergänzt.
- **`webui/api.py`** (NEU, FastAPI, bind 127.0.0.1) — `create_app(config)` + Modul-`app` (demo-locked
  Default-Config mit absoluten `data/`-Pfaden wie das Wiring). **DB strikt read-only** (`ro_connect`:
  `file:…?mode=ro` → Write wirft `OperationalError`, der Isolations-Beweis); `_query` fail-soft (fehlende
  DB/Tabelle → `[]`). Endpoints §12: `GET /api/{status,score,confidence,lessons,trades,last_cycle}` +
  `POST /api/{kill,clear_kill,command}`. **Control = nur Datei-Writes** (kein Executor/Broker/Runner-
  Import → UI-Crash kann Trading strukturell nicht berühren, Decision 14). Cross-Phase-`reward`-Import
  (Confidence-Mathe) **lazy im Endpoint** → `import webui.api` zieht nur `fastapi`+`scheduler.*`+stdlib
  (laufzeit-geprüft: reward/anthropic/broker_wrapper/execution NOT loaded).
- **`webui/static/{index.html,style.css,app.js}`** (NEU, kein Build-Step) — Dark-Neumorphism, Monospace
  (offline-sichere System-Mono-Stack, **kein** CDN-Fetch), kein Emoji. Karten: Status · Control (Start/
  Stop/Kill/Clear) · Score-Sparkline (inline-SVG) · Confidence (observe-only) · Last Cycle · Trades-
  Tabelle · Lessons. Vanilla `fetch`-Polling 7 s, fail-soft (`api down`-Footer hält letzte Werte),
  Profit grün / Loss rot.
- **`scripts/run_webui.sh`** (NEU, spiegelt `run_scheduler.sh`) — `PYTHONPATH=phase8_scheduler exec
  uvicorn webui.api:app --host 127.0.0.1`. Braucht **keinen** Keyring (kein Broker-Talk). `--port`.
- **`tests/test_command.py`** (10) + **`tests/test_webui.py`** (13, FastAPI `TestClient`, Temp-SQLite +
  Temp-State; inkl. **read-only-Connection-rejects-write**-Isolationsbeweis) + **`tests/test_runner.py`**
  (+2: `stop`→Pause-Iteration ohne `executor.run`; `start`→normaler Zyklus).

### Reconciliations / Design-Entscheidungen (Code = Source of Truth)
- **`webui` ist NICHT installiert** (pyproject `include=["scheduler*"]` schließt es bewusst aus — „UI
  läuft als separater Prozess"). Importierbar im Test, weil pytest `phase8_scheduler/` auf `sys.path`
  legt (tests/ ist Paket, phase8_scheduler/ nicht); für `uvicorn` setzt `run_webui.sh` `PYTHONPATH`.
- **Confidence-Endpoint reused P7** (`select_edge_set` + `compute_confidence`, `ConfidenceReport.state`/
  `win_rate_wilson_lb` — **nicht** `status`/`wilson_lb`); fehlschlagend → `state="UNAVAILABLE"`, nie 500.
- **PAUSED-Quelle = die Command-Datei selbst** (die UI liest sie direkt) → **kein** `state.py`-Feld
  nötig (Modul 4 unberührt). `running_state` = HALTED (KILL) > PAUSED (cmd stop) > RUNNING.
- **Pause berührt kein State-Feld** im Runner → ein echter `last_no_trade_reason` wird nicht überschrieben.

### Verifiziert (gemockt / offline — kein Netz, kein LLM; Live = Operator)
- `pytest phase8_scheduler/tests -q` → **171 passed** (146 + 10 command + 2 runner + 13 webui).
  `py_compile`/`bash -n`/`node --check` clean. Static-Serving + alle 6 GET + 3 POST end-to-end via
  `TestClient` geprüft (index referenziert app.js/style.css; `mode=ro` weist Write ab).
- **Import-Isolation:** `import webui.api` zieht **NONE** reward/anthropic/broker_wrapper/execution;
  `import scheduler.command` zieht NONE cross-phase. `import scheduler.runner` unverändert isoliert.
- **Regression unberührt** (Edits **nur** in `phase8_scheduler/`; P1–P7 importieren `scheduler.*` nicht):
  P1 52 · P2 62 · P4 94 · P5 146 · P6 70 · P7 128.
- **Neue Runtime-Deps installiert** (waren in `requirements.txt`, inert bis jetzt): `fastapi`/`uvicorn`
  in den geteilten venv; `httpx` (TestClient) bereits da.

### Next — **Operator-Live-Lauf** (Phase-8-Gate schließen)
- Im Handelsfenster `python phase8_scheduler/scripts/live_test.py` gegen IG-Demo → erste reale autonome
  Outcomes. Parallel `bash phase8_scheduler/scripts/run_webui.sh` → `http://127.0.0.1:8000` öffnen,
  Karten gegen die echte `data/trading_bot.sqlite` prüfen; Kill/Start/Stop schreiben die Dateien;
  bei laufendem Daemon: Stop pausiert / Start resumed / Kill hält.
- **Danach** Doku auf ✅ flippen (ROADMAP P8, README-Statustabelle), Post-Build-Schritte (Architektur-
  SVG/`ARCHITECTURE.md`, `phase8_scheduler_konzept.svg`, P9-Handover), Merge `phase8-scheduler` → `main`.

### Offene Punkte / [VERIFY]
- `live_test.py` ist noch **nicht** live gelaufen (Operator) — Erwartung unverändert (sauberer Stop +
  State + CLOSED-Trade mit `reward_pts` **oder** valider No-Trade-Lauf).
- **Commit:** committet, **falls** der Operator es triggert (Branch `phase8-scheduler`); „Commit ⇒
  Note-Update" im selben Commit.

---

## Session stopped — 2026-06-28 (Modul 11: `scripts/wiring.py` + `scheduler/run.py` + Operator-Scripts — der Composition Root)

### Completed
- **`scripts/wiring.py`** — `build_scheduler(config, *, now_fn=None, sleep_fn=None, max_iterations=None,
  exec_config=None) -> SchedulerRunner`, der **einzige** Ort, an dem `scheduler` an den echten P1–P7-
  Stack gebunden wird (Konzept §11, **kein AI**). Baut den **vollen** Zyklus (anders als P6/P7-Wiring,
  die je nur ihre eine Naht verdrahteten): EIN geteilter warmer `ig_demo`-Broker treibt das echte P4-
  `Research`, der P6-`debate_runner` **und** der P7-`reward_sink` werden **beide** in EINEN P5-`Executor`
  injiziert (`confirm_fn=AutoConfirm` — Contract A; `research_runner=_no_research` — Contract B), drumherum
  die Scheduler-Module (`Clock`/`StateStore`/`AutoConfirm`/`BackoffTracker`/`TokenBudget`/`ResearchTick`/
  `Reconciler`/`SchedulerRunner`). Alle Cross-Phase-Imports **lazy in den Funktionskörpern** → `import
  scripts.wiring` zieht **NONE** cross-phase (offline-importierbar, spiegelt P7).
- **`scheduler/run.py`** — `python -m scheduler.run` Entry **im Paket** (nicht `scripts/`, da `-m` das
  installierte Paket braucht; spiegelt `execution/ig_bot.py`). Argparse-Caps → demo-gelockte
  `SchedulerConfig` → lazy `from scripts.wiring import build_scheduler` (sys.path-insert) → SIGTERM/SIGINT
  → `runner.request_stop()` → `runner.run()`. `PreflightError` → exit 2 (sauber, kein Trade). Logging →
  stderr.
- **`scheduler/runner.py`** (additive Modul-10-Erweiterung) — `request_stop()` (non-sticky In-Memory-Flag)
  + Loop-Top-Check (vor dem Kill-Switch). **Bewusst NICHT** die KILL-Datei: ein Signal-Stop darf keinen
  Halt persistieren, der den nächsten Restart blockt.
- **`scripts/run_scheduler.sh`** — dokumentierter Start in **entsperrter** Session (Keyring/Secret-Service,
  Q3) + `# known issue`-Note zu Background/Headless; `exec python -m scheduler.run "$@"`.
- **`scripts/smoke_test.py`** — **offline** simulierter Tag mit Fakes + Fake-Clock (Konzept §11; bewusst
  **anders** als P5/P6/P7-„real dry stack" — der Loop-Wert sind die Mechanik: Phasen/Cap/Kill). Druckt 3
  Szenarien (voller Tag · CAP_BLOCK · Kill-Switch), kein Netz/Keyring/Order. **Lokal gelaufen: 3/3, exit 0.**
- **`scripts/live_test.py`** — echter unbeaufsichtigter IG-Demo-Zyklus (operator-run, nicht CI):
  `build_scheduler(sleep_fn=no-op, max_iterations, exec_config=short-hold)` → `runner.run()` → read-only
  DB/State-Asserts: sauberer Stop · State persistiert · **falls** heute ein CLOSED-Trade → `reward_pts`
  vorhanden (autonomer open→close→reward-Beweis); ein No-Trade-Lauf (Abstain/VETO/Cap/ruhig) ist valider
  PASS (P5/P6/P7-Disziplin). Im Fenster laufen.
- **`tests/test_run.py`** (6, offline) + **`tests/test_runner.py`** (+2 `request_stop`).

### Acht Konzept↔Code-Reconciliations (Code = Source of Truth — dated §11-Annotation im Konzept)
1. **Wiring repliziert die P4/P6/P7-Builder inline** (aus `research`/`debate`/`reward`), importiert **nicht**
   deren `scripts.wiring` (Namenskollision) — wie P7 `build_executor` replizierte statt P5 zu importieren.
2. **`run.py` lebt im Paket (`scheduler/run.py`), nicht `scripts/`** — `python -m scheduler.run` braucht es
   installiert (`include=["scheduler*"]` schließt `scripts/` aus); spiegelt `execution/ig_bot.py`.
3. **Struktureller Demo-Lock im Wiring** (Decision 7 / Contract D): `build_scheduler` wirft bei
   `config.account != "demo"`, baut **nur** `get_broker("ig_demo")`; `AutoConfirm` re-checkt zur Laufzeit
   (zwei unabhängige Locks).
4. **Alle Daten-Pfade absolut auf den `<repo_root>/data/`-Baum** (via `dataclasses.replace`) → der Daemon
   ist cwd-unabhängig + teilt exakt die Dateien von `init_db.py` + P4–P7.
5. **Die drei Runner-Closures leben im Wiring:** `realized_pnl_today` (DB-`SUM(profit_loss)` via `db.conn`,
   Contract E) · `pending_reconcile_fn` (P5-`reconcile_startup` über den geteilten Broker) · `preflight_fn`
   (Keyring `get_credential(IG_DEMO_API_KEY)` + **Migration-002-Check** via `PRAGMA table_info` → `account`-
   Spalte; **verifiziert, migriert nicht** — ein Safety-Daemon mutiert kein Schema).
6. **EIN geteiltes `now_fn`** durch Clock/Executor/ResearchTick/Reconciler/TokenBudget; der Executor behält
   sein **eigenes echtes `sleep_fn`** (der Monitor muss real warten) — nur die **Loop-Kadenz** nutzt das
   injizierte `sleep_fn`.
7. **`smoke_test` = offline Sim-Tag mit Fakes** (Konzept §11, bewusste Abweichung vom P5/P6/P7-Muster).
8. **Graceful Stop = `request_stop()`** (non-sticky, Loop-Top-Check) statt KILL-Datei — sonst blockt ein
   Signal den nächsten Restart. In-Progress-`sleep` läuft v1 erst aus (Latenz; interruptible-sleep = später).

### Verifiziert (gemockt / offline — kein Netz, kein LLM; Live = Operator)
- `pytest phase8_scheduler/tests -v` → **146 passed** (138 + 2 `request_stop` + 6 `test_run`). `py_compile`
  aller neuen Dateien + `bash -n run_scheduler.sh` clean. **`smoke_test.py` lokal gelaufen → 3/3, exit 0.**
  `python -m scheduler.run --help` exit 0; `live_test.py --help` exit 0 (beide offline — Cross-Phase-Import
  lazy in `main`). **Import-Isolation:** `import scheduler.run` / `import scripts.wiring` /
  `import scheduler.runner` ziehen **NONE** cross-phase beim Laden.
- **Regression grün + unberührt** (rein additiv, separat gelaufen): P1 52 · P2 62 · P4 94 · P5 146 · P6 70 ·
  P7 128.

### Next — **Modul 12: `webui/` (FastAPI read-mostly + statisches Dashboard)** — **zuletzt**
- `webui/api.py` (FastAPI, bind `127.0.0.1`): read-only DB-Connection (`mode=ro`) + `scheduler_state.json`;
  Endpoints `/api/{status,score,confidence,lessons,trades,last_cycle}` (read) + `POST /api/{kill,clear_kill,
  command}` (schreibt **nur** Kill-/Command-Datei — Decision 14, der Trader hängt **nie** an der UI).
  `webui/static/{index.html,app.js,style.css}` (GitHub-Dark, Monospace, Glass-/Neumorphism-Buttons, Polling
  5–10 s, kein Build-Step). Tests ≥5 (FastAPI `TestClient`, gemockte DB/State). **`fastapi`+`uvicorn` sind die
  einzigen neuen Runtime-Deps (nur UI).** Unter Druck fällt die UI weg, **nie** die Safety.
- **Operator (vor/parallel zu Modul 12):** im Fenster `python phase8_scheduler/scripts/live_test.py` gegen
  IG-Demo → erste reale autonome Demo-Outcomes sammeln.

### Offene Punkte / [VERIFY]
- `live_test.py` ist noch **nicht** live gelaufen (Operator). Erwartung im Fenster: sauberer Stop + State +
  entweder ein CLOSED-Trade mit `reward_pts` **oder** ein valider No-Trade-Lauf.
- **Commit:** committet, **falls** der Operator es triggert (Branch `phase8-scheduler`); „Commit ⇒
  Note-Update" im selben Commit.

---

## Session stopped — 2026-06-28 (Modul 10: `scheduler/runner.py` — die Loop, das Herzstück)

### Completed
- **`scheduler/runner.py`** — `SchedulerRunner`, der Daemon-Orchestrator, der die Module 1–9
  *ausführt* (Konzept §10, **kein AI** — reine Mechanik; die AI bleibt in den getriebenen
  Kollaboratoren: P4-`ask_candidate` in `research_tick`, P6-Debatte + P7-Lesson in
  `executor.run()`). Drei öffentliche Methoden:
  - **`preflight()`** — fail-closed: injizierter `preflight_fn()` (Keyring + DB/Migrations, vom
    Wiring gebaut) **und** `broker.connect()`; Fehler → `PreflightError` → sauberer Exit, **kein**
    Trade-Versuch (Deployment-Top-Risk Q3).
  - **`run()`** — `preflight()` → einmal Startup-Reconcile (forced) → die §10-Loop: pro Iteration
    `clock.now()` → `rollover_if_new_day` → Kill-Switch-Check (gesetzt → `kill_reason` + break) →
    `clock.classify` → Phasen-Arbeit, jede Iteration `try/except/finally`: Cycle-Exception →
    `logger.critical` + `backoff.record_failure`; `should_trip` → `killswitch.set_kill("auto:
    backoff")` + break, sonst `clock.sleep(delay_s)`; **`finally: state_store.save`**. Nach der
    Loop **immer** `shutdown()` + save.
  - **`shutdown(state)`** — fail-soft: finaler Reconcile + `broker.disconnect`, jeder Schritt
    geguarded (`critical`, kein Re-raise) — ein sauberer Stop crasht nie.
  - **Phasen-Arbeit (`_run_phase`):** PRE_OPEN = warm + reconcile + sleep `min(seconds_until(WINDOW),
    idle_poll)`; **WINDOW** = warm + reconcile + `auto_confirm.can_open` (Pre-Cycle-Gate, spart
    Tokens) → bei OK `research_tick.ensure_candidates` dann **bare `executor.run()`** (Contract A!)
    → `record_cycle`, sonst `last_no_trade_reason = reason`; POST_WINDOW = warm + forced Reconcile +
    sleep bis nächstem Pre-Open; IDLE = nur `idle_poll`-Sleep.
- **`scheduler/__init__.py`** exportiert jetzt zusätzlich `SchedulerRunner` (zuletzt importiert —
  hängt von allen anderen Submodulen ab).
- **`tests/test_runner.py`** — **16 Tests** (deterministisch, kein Netz/LLM/echter Sleep): echter
  `Clock` mit stepping `now_fn` (1 Aufruf/Iteration, weil alle Kollaboratoren Fakes sind, die
  `clock.now` nicht rufen) + recording `sleep_fn`, Fake-Kollaboratoren, **echter** `StateStore` auf
  `tmp_path`, `max_iterations`-Stop. Abgedeckt: Fixture-Zeiten-Klassifikation; WINDOW-Happy-Path
  (research → **bare** `run()` → OPEN bumpt `trades_today`); NO_TRADE zählt nicht; **CAP_BLOCK via
  echtem `AutoConfirm`** (kein research/execute, Reason gesetzt); PRE_OPEN/POST_WINDOW/IDLE;
  voller simulierter Tag (IDLE→PRE_OPEN→WINDOW→POST_WINDOW, `tick`=5, 4 Sleeps); Kill-Switch →
  stop + shutdown; **Backoff-Trip via echtem `BackoffTracker`** (3 Exceptions → `set_kill("auto:
  backoff")`); transienter Fehler → Backoff-Delay-Sleep, dann Recovery; Preflight-Fail (`preflight_
  fn` raises / `broker.connect` not-ok → `PreflightError`, nie Loop); Preflight-Pass; Reconcile-
  Throttle; Package-Export-Identität.

### Sechs Konzept↔Code-Reconciliations (Code = Source of Truth — dated §10-Annotation im Konzept)
- **(1) `broker.ensure_session()` → privates `_warm_session()`** komponiert aus den **echten**
  P1-Methoden `is_connected()`/`connect()` + `env["ok"]`-Check (kein `ensure_session` existiert,
  `ig_adapter.py:137,157,178`). Raise in der Loop → caught → Backoff; in `preflight`/`shutdown`
  vom Caller gewrapped/geguarded.
- **(2) Konstruktor droppt `budget`** (Konzept §10 listete es): das Budget-Gate sitzt bereits in
  `auto_confirm.can_open()`; die Loop ruft Budget nie direkt → ungenutzte Dependency. Gleiche
  „drop the unused injected dep"-Disziplin wie `reconcile.py` (db/state_store) / `research_tick.py`.
- **(3) Cross-Phase-Preflight-Probes INJIZIERT, nicht inlined.** Konzept §10 inlined
  `get_credential` + DB-Check; um die Import-Isolation (`import scheduler.runner` zieht NONE
  cross-phase) + 100%-Unit-Testbarkeit zu wahren, nimmt der Runner ein keyword-frei
  `preflight_fn: Callable[[], None]` (wirft bei Fehler), das das Wiring mit Keyring+DB backt —
  exakt das Muster `safety.realized_pnl_today` / `reconcile.pending_reconcile_fn`. `broker.connect()`
  macht der Runner selbst (hält den Broker eh).
- **(4) `killswitch_path` → `config.kill_path`** (Runner hält die Config; kein Extra-Arg).
- **(5) Stop-Bedingung = keyword-only `max_iterations: int | None = None`** (Default None = echter
  Endlos-Daemon; Tests übergeben K). `now_fn`/`sleep_fn` sind über den `Clock` injiziert.
- **(6) `reconcile_interval_min` via kleinem Throttle** (`_maybe_reconcile`/`_due`, UTC-Compare,
  DST-sicher) — die 5-min-WINDOW-Kadenz hämmert nicht jeden Cycle `get_trade_history`; Reconcile
  ist **forced** bei Startup, POST_WINDOW, Shutdown (Decision 11). Idempotent ⇒ Über-Laufen ist
  nur Kosten, nie Korrektheit.

### Verifiziert (gemockt / lokal — kein Netz, kein LLM; Live = Operator)
- `pytest phase8_scheduler/tests -v` → **138 passed** (10 config + 6 exceptions + 19 clock + 18
  state + 12 killswitch + 18 safety + 13 budget + 10 research_tick + 9 backoff + 7 reconcile + **16
  runner**). `py_compile` clean. **Import-Isolation:** `import scheduler.runner` zieht **NONE**
  broker_wrapper/persistence/external_data/research/execution/reward/debate/pandas/numpy/yfinance/
  anthropic/requests.
- **Regression grün + unberührt** (rein additiv, separat gelaufen): P1 52 · P2 62 · P4 94 · P5 146
  · P6 70 · P7 128.

### Next — **Modul 11: `scripts/wiring.py` + `run.py` + `run_scheduler.sh` + `smoke_test.py` + `live_test.py`** (Konzept §11 — der Composition Root)
- **`wiring.py`** (`build_scheduler(config) -> SchedulerRunner`): EINEN geteilten **warmen** Broker
  (Contract G), `Database`(`live_db_path`), `StateManager`, `MarketDataFetcher`
  (`register_volume_proxy("EXS1.DE")`), `Research` **direkt** aus dem `research`-Paket (Contract G,
  Namenskollision umgehen), `reward_sink` (P7) + `debate_runner` (P6); den Executor **einmal** mit
  `confirm_fn=AutoConfirm` + **No-op-`research_runner`** (Contract B) + `reward_sink`/`debate_runner`
  bauen; die drei Closures backen: `realized_pnl_today` (DB-`SELECT … session_date`),
  `pending_reconcile_fn` (P5-`reconcile_startup` über den geteilten Broker), **`preflight_fn`**
  (Keyring `get_credential` + DB/Migrations-Check); Caps setzen (`daily_loss_cap≈1800`,
  `account="demo"` **hart**, nur `ig_demo`-Broker); dann `Clock`/`StateStore`/`AutoConfirm`/
  `BackoffTracker`/`TokenBudget`/`ResearchTick`/`Reconciler` → `SchedulerRunner` (`max_iterations=
  None`).
- **`run.py`** (`python -m scheduler.run`): Config laden, `build_scheduler`, `runner.run()`,
  SIGTERM/SIGINT → `shutdown`. **`run_scheduler.sh`** (entsperrte Session, Keyring-Note).
  **`smoke_test.py`** (1 simulierter Tag, Fake-Clock, kein echter Trade). **`live_test.py`**
  (echter unbeaufsichtigter Zyklus gegen IG Demo, nicht in CI). **Danach** Modul 12 Web-UI (zuletzt).

### Offene Punkte / [VERIFY]
- `wiring.py`: das `preflight_fn` muss den **echten** IG-Demo-Keyring-Key prüfen + die DB-Version
  (Migration 002) — gegen `broker_wrapper.credentials.get_credential` + `persistence`/`init_db.py`
  gegenlesen, bevor gebaut wird. P7-`scripts/wiring.py` (`build_executor`/`build_reward_sink`) ist
  die Vorlage (geteilter Broker, `_no_research`, tz-aware `now_fn`).
- **Commit:** committet, **falls** der Operator es triggert (Branch `phase8-scheduler`); „Commit ⇒
  Note-Update" im selben Commit.

---

## Session stopped — 2026-06-28 (`scheduler/reconcile.py` — idempotenter Reconcile-Pass)

### Completed
- **`scheduler/reconcile.py`** — `Reconciler`, der Daten-Recovery-Pass (Konzept §9, **kein AI**,
  **reine Komposition** zweier bereits gebauter+getesteter Stücke — Contract F). **Mission-kritisch:**
  ein geschlossener Trade, dessen P&L in-cycle nicht aufgelöst werden konnte (IG bucht History erst
  nach Settlement → `CLOSED_BY_BROKER` lässt die `trade_outcomes`-Zeile **OPEN**, ohne Reward/Lesson),
  wird per späterem Pass nachgezogen, sobald die History aufholt — sonst gehen die realen Demo-Daten
  verloren. `tick(state) -> ReconcileReport`, **durchgehend fail-closed (wirft nie in die Loop)**:
  1. **orphan PENDING** via injizierter zero-arg `pending_reconcile_fn` (wraps P5 `reconcile_startup`);
     raised sie (`ReconcileConflict`/`ExecutionAbort`) → `critical` + `pending_ok=False`, **Schritt 2
     läuft trotzdem**.
  2. **CLOSED_BY_BROKER-P&L-Nachzieh** via `reward_sink.reconcile_open_trades()` (P7, None = alle OPEN;
     idempotent via OPEN/CLOSED-Status; defensiv geguarded, obwohl die echte Methode nie wirft).
  3. `state.last_reconcile_ts` stempeln; `ReconcileReport(pending_ok, resolved_deal_ids, n_resolved)`.
- **`scheduler/__init__.py`** exportiert jetzt zusätzlich `Reconciler` + `ReconcileReport`.
- **`tests/test_reconcile.py`** — **7 Tests**: happy-path (beide Hälften + ts + `reconcile_open_trades`
  mit `None`); nichts offen → No-op; **pending raised → contained + Schritt 2 läuft weiter**;
  `reconcile_open_trades` raised → contained; **beide raised → 2 criticals, kein Re-raise, ts gesetzt**;
  Default-`now_fn` tz-aware; Package-Export-Identität.

### Drei Konzept↔Code-Reconciliations (Code = Source of Truth — dated §9-Annotation im Konzept)
- **(1) Ctor `Reconciler(reward_sink, pending_reconcile_fn, *, now_fn=None)`** statt
  `(broker, db, reward_sink, state_store)`. **Beide Reuse-Ziele INJIZIERT, nicht importiert** → die
  verifizierte Import-Isolation bleibt erhalten (`import scheduler.reconcile` zieht **NONE** cross-phase).
  `broker`+P5-`reconcile_startup` → zero-arg `pending_reconcile_fn`-Closure (Wiring bindet sie am
  Composition-Root); `db` raus (reward_sink besitzt es); `state_store` raus (mutate+Runner-persistiert,
  wie `research_tick`/`record_cycle`/`backoff`); `now_fn` rein (Determinismus).
- **(2) Komposition, keine Reimplementierung** (Contract F): `reconcile_open_trades` macht
  History-Resolve→`update_trade_close`+`insert_reward` (idempotent) bereits — `reconcile.py` ruft nur.
- **(3) orphan-PENDING-Hälfte teil-redundant** mit dem executor-eigenen `reconcile_startup`; der
  Scheduler-Pass ergänzt Between-Window-Abdeckung + den P&L-Nachzieh. **Scheduling** = Runner (§10);
  **Closure bauen + Broker teilen** = Wiring (Modul 11).

### Verifiziert (gemockt / lokal — kein Netz, kein LLM; Live = Operator)
- `pytest phase8_scheduler/tests -v` → **122 passed** (10 config + 6 exceptions + 19 clock + 18 state +
  12 killswitch + 18 safety + 13 budget + 10 research_tick + 9 backoff + 7 reconcile). `py_compile` clean.
  **Import-Isolation:** `import scheduler.reconcile` zieht **NONE** broker_wrapper/persistence/
  external_data/research/execution/reward/debate/pandas/numpy/yfinance/anthropic/requests.
- **Regression grün + unberührt** (rein additiv): P2 62 · P4 94 · P5 146 · P7 128. P1 52 · P6 70 unverändert.

### Next — **Modul 10: `scheduler/runner.py`** (Konzept §10 — die Loop, das Herzstück; **Schwerpunkt-Tests ≥8**)
- `SchedulerRunner(*, clock, state_store, killswitch_path, auto_confirm, backoff, budget,
  research_tick, reconciler, executor, broker, config)` + `preflight()` (fail-closed: Keyring/`get_credential`
  + `broker.connect` + DB/Migrations da → sonst `PreflightError` → sauberer Exit, **kein** Trade) +
  `run()` (die Hauptschleife) + `shutdown()` (finaler Reconcile + Session schließen). Loop-Skizze §10:
  rollover → killswitch-Check → `clock.classify` → PRE_OPEN(ensure_session+reconcile) / WINDOW
  (reconcile → `auto_confirm.can_open` Pre-Cycle-Gate → `research_tick.ensure_candidates` → **bare
  `executor.run()`** (Contract A: `confirm_fn=AutoConfirm` ist am Konstruktor, **nicht** hier) →
  `record_cycle` → `backoff.record_success`) / POST_WINDOW(finaler Reconcile) / IDLE; `except` →
  `backoff.record_failure` → `should_trip` → `killswitch.set_kill("auto:backoff")`+shutdown; `finally:
  state_store.save`. **Determinismus:** `now_fn`/`sleep_fn` injiziert, Loop über `now_fn` getrieben + nach
  K Iterationen via injizierbare Stop-Bedingung abgebrochen (kein echter sleep/Netz).
- **Danach** Modul 11 `wiring.py` (No-op-`research_runner`, EINEN Broker teilen, `pending_reconcile_fn`-
  Closure, `realized_pnl_today`-Closure, Caps setzen) + Operator-Scripts → **zuletzt** Web-UI.

### Offene Punkte / [VERIFY]
- `runner.py`: Contract A (bare `run()`, `confirm_fn` am Konstruktor) + die §10-Loop-Skizze + die
  Stop-Bedingungs-Injektion für deterministische Tests heranziehen. `preflight` = Deployment-Top-Risk Q3
  (Keyring/Secret-Service in entsperrter Session).
- **Commit:** committet, **falls** der Operator es triggert (Branch `phase8-scheduler`); „Commit ⇒
  Note-Update" im selben Commit.

---

## Session stopped — 2026-06-28 (`scheduler/backoff.py` — konsekutive-Fehler-Tracking + Backoff)

### Completed
- **`scheduler/backoff.py`** — `BackoffTracker`, die Fehler-Gedächtnis-Einheit der Loop (Konzept
  §6 / Decision 9, **kein AI**, reine Arithmetik). **Advisory**: trackt den Counter + rechnet
  Delay/Trip-Verdikt, **setzt den Kill-Switch nie selbst** — das macht der Runner (§10) auf
  `should_trip`. Stdlib-only, importiert nur `scheduler.config`/`scheduler.state`.
  - `record_failure(state)` / `record_success(state)` — mutate+return (wie `record_cycle`/
    `research_tick`); berühren **nur** `consecutive_failures` (state.py-Docstring: dieses Feld
    ist „owned by backoff.py").
  - `should_trip(state)` — `consecutive_failures >= config.max_consecutive_failures` (boundary-
    inklusiv).
  - `delay_s(state)` — `n<=0 → 0.0` (total/defensiv); sonst `min(backoff_base_s · 2^(n-1),
    backoff_cap_s)` (Defaults: 30→60→120→…→cap 600; der Cap bound't, kein Overflow-Guard nötig).
- **`scheduler/__init__.py`** exportiert jetzt zusätzlich `BackoffTracker`.
- **`tests/test_backoff.py`** — **9 Tests**: failure inkrementiert (gleiches Objekt); success
  resettet; should_trip unter Schwelle False / **at-threshold** True; `delay_s` exponentiell
  (30/60/120); Cap clamps; `n<=0 → 0.0` dann base nach einer Failure; **Feld-Isolation** (nur
  `consecutive_failures` berührt, alle anderen State-Felder unverändert); Package-Export-Identität.

### Drei Konzept↔Code-Reconciliations (Code = Source of Truth — dated §6-Annotation im Konzept)
- **(1) Advisory, nicht selbst-trippend.** `BackoffTracker` meldet nur `should_trip`; der
  **Runner** (§10) ruft `killswitch.set_kill(..., "auto:backoff")` + `shutdown()`. Single-
  responsibility (spiegelt den Trip-Log, der im Runner lebt, nicht in `killswitch.py`).
- **(2) `delay_s` total — `n<=0 → 0.0`** (Skizze `min(base·2^(n-1), cap)` ist bei n=0 undefiniert).
- **(3) Mutate-and-return**; `record_*` berühren nur `consecutive_failures`. Fehler-Klassifikation
  (transient vs. strukturell) bleibt v1-deferred (reine konsekutive Cycle-Exceptions).

### Verifiziert (gemockt / lokal — kein Netz, kein LLM; Live = Operator)
- `pytest phase8_scheduler/tests -v` → **115 passed** (10 config + 6 exceptions + 19 clock + 18
  state + 12 killswitch + 18 safety + 13 budget + 10 research_tick + 9 backoff). `py_compile` clean.
  **Import-Isolation:** `import scheduler.backoff` zieht **NONE** broker_wrapper/persistence/
  external_data/research/execution/reward/debate/pandas/numpy/yfinance/anthropic/requests.
- **Regression grün + unberührt** (rein additiv): P2 62 · P4 94 · P5 146 · P7 128 (separat
  gelaufen). P1 52 · P6 70 unverändert.

### Next — **Modul 9: `scheduler/reconcile.py`** (Konzept §9, Komposition — nicht neu bauen)
- `Reconciler(broker, db, reward_sink, state_store).tick(state) -> ReconcileReport`: **Komposition**
  aus (a) `reconcile_startup` (P5 `execution/order.py`, läuft bereits in **jedem** `executor.run()`
  — orphan PENDING) + (b) **`reward_sink.reconcile_open_trades(deal_ids=None)`** (P7 Step 13b,
  idempotenter `CLOSED_BY_BROKER`-P&L-Nachzieh über `get_trade_history`, fail-closed) — **Contract
  F**. Idempotent via `deal_id`; läuft Startup + alle `reconcile_interval_min` + Shutdown.
  `last_reconcile_ts` aktualisieren. Fail-closed (`logger.critical`, kein Re-raise). Tests ≥5
  (orphan→closed; broker-closed→P&L+reward; bereits gebucht→kein Doppel-Insert; History-Fehler→
  fail-closed weiter; nichts offen→No-op). **Vor Bau Contract F + die P7-`reconcile_open_trades`-
  Signatur gegenlesen.**
- **Danach** Modul 10 `runner.py` (§10, die Loop) → Modul 11 `wiring.py` → **zuletzt** UI.

### Offene Punkte / [VERIFY]
- `reconcile.py`: P7-`reward_sink.reconcile_open_trades`-Rückgabeform + `broker.reconcile_positions`-
  `.data` (Contract F) gegenlesen, bevor `Reconciler` baut.
- **Commit:** committet, **falls** der Operator es triggert (Branch `phase8-scheduler`); „Commit ⇒
  Note-Update" im selben Commit.

---

## Session stopped — 2026-06-28 (Modul 8: `scheduler/research_tick.py` — autonome Kandidaten, der Blocker)

### Completed
- **`scheduler/research_tick.py`** — `ResearchTick`, der **autonome Kandidaten-Generator** (die
  eigentliche Phasen-Mission; Decision 4/5, **kein neues AI** — die einzige AI ist der eine
  P4-`ask_candidate`-Call **innerhalb** `Research.run()`, unverändert reused). Triggert pro Zyklus
  das **echte** `Research.run()` (über das duck-typed `_ResearchLike`-Protocol → kein
  `research`-Import, Phasen-Isolation), klassifiziert das Ergebnis, schreibt einen minimalen
  `no_trade_reason`, fail-closed bei jedem Fehler. **Nie** `seed_candidate.py` → der Marker
  `"MANUAL SEED"` taucht in einem autonomen Pick **nie** auf (`test_no_manual_seed_marker`).
  - `ensure_candidates(state) -> ResearchResult`: stempelt **immer** `state.last_research_ts`
    (Versuch fand statt); dann **pick** (`run()` non-empty) → `picked=True`, `reason=None`,
    `last_no_trade_reason` cleared; **abstain** (`[]`) → `picked=False`, `REASON_LLM_ABSTAIN`;
    **exception** → `logger.critical` (kein Re-raise), **defensiver** `save_candidates([])` über
    `research.state` (stale Pick darf nicht getradet werden), `REASON_PREFLIGHT`.
  - `ResearchResult(picked, n, reason)` (frozen); Reason-Konstanten `REASON_LLM_ABSTAIN`/
    `REASON_PREFLIGHT` (v1) + deklariert-aber-reserviert `REASON_EMPTY_UNIVERSE`/
    `REASON_VALIDATOR_REJECT`/`REASON_FILTER_FAIL` (P9).
- **`scheduler/__init__.py`** exportiert jetzt zusätzlich `ResearchTick` + `ResearchResult`.
- **`tests/test_research_tick.py`** — **10 Tests**: PASS (Pick, Reason cleared, ts, run×1);
  abstain → `LLM_ABSTAIN`; exception → `PREFLIGHT_FAIL` + 1 critical + `save_candidates([])` +
  kein Re-raise; cleanup-fehlschlag-auch → 2 criticals, swallowed; **`test_no_manual_seed_marker`**;
  `last_research_ts` auf **jedem** Outcome (parametrisiert pass/abstain/exception); Default-`now_fn`
  tz-aware; Package-Export-Identität.

### Zwei Konzept↔Code-Reconciliations (Code = Source of Truth — dated §8-Annotation im Konzept)
- **(H) ★ 5-Code-Taxonomie kollabiert auf 2 v1-Buckets.** `Research.run() -> list[Candidate]`
  trägt **keine** Begründung (nur stderr-Log) → unterscheidbar sind nur pick/abstain/exception.
  v1: `PREFLIGHT_FAIL` (raise) + `LLM_ABSTAIN` (`[]`-Umbrella); `EMPTY_UNIVERSE`/`VALIDATOR_REJECT`/
  `FILTER_FAIL` deklariert, gesetzt erst in P9 (P4 muss einen Grund liefern). Decision 5 konform;
  `safety.py:97` antizipiert die Trennung (Gate-Block- vs. No-Candidate-Taxonomie).
- **(C) Konstruktor** `ResearchTick(research, *, now_fn=None)` statt `(research, state_store)`:
  mutiert nur den übergebenen `SchedulerState` (wie `record_cycle`/`backoff`), der **Runner**
  persistiert (`finally: state_store.save`) → `state_store` (ungenutzt) raus, keyword-only `now_fn`
  rein (Determinismus). Fail-closed Clear reused `research.state` — keine Extra-Dependency.
  **Freshness ist NICHT hier** (Contract B): der No-op-`research_runner` im Executor (Wiring/Modul
  11) verhindert den Gate-2-Re-Call; `research_tick` läuft nur echtes Research **vor** `run()`.

### Verifiziert (gemockt / lokal — kein Netz, kein LLM; Live = Operator)
- `pytest phase8_scheduler/tests -v` → **106 passed** (10 config + 6 exceptions + 19 clock + 18
  state + 12 killswitch + 18 safety + 13 budget + 10 research_tick). `py_compile` clean.
  **Import-Isolation:** `import scheduler.research_tick` zieht **NONE** broker_wrapper/persistence/
  external_data/research/execution/reward/debate/pandas/numpy/yfinance/anthropic/requests.
- **Regression grün + unberührt** (rein additiv): P2 62 · P4 94 · P5 146 · P7 128 (separat
  gelaufen). P1 52 · P6 70 unverändert (kein berührter Import).

### Next — **Modul 6: `scheduler/backoff.py`** (Konzept §6, klein, TDD ≥5) — die letzte mechanische Einheit vor dem Runner
- `BackoffTracker(config)` mit `record_success(state)`/`record_failure(state)` (mutate+return wie
  `record_cycle`/`research_tick`), `should_trip(state)` (`consecutive_failures >=
  max_consecutive_failures`), `delay_s(state)` (`min(backoff_base_s * 2^(n-1), backoff_cap_s)`).
  Trip → der Runner setzt `killswitch.set_kill(..., "auto:backoff")` + sauberer Stop (§10). Tests:
  Erfolg resettet; 3 Fehler → trip; 2 → kein trip; `delay_s` exponentiell + cap; Reset setzt delay
  zurück. Stdlib-only, kein Re-raise.
- **Danach** Modul 9 `reconcile.py` (§9, Komposition aus `reconcile_startup` (P5, läuft schon in
  jedem `run()`) + `reward_sink.reconcile_open_trades` (P7) — Contract F) → Modul 10 `runner.py`
  (§10, die Loop) → Modul 11 `wiring.py` (No-op-`research_runner` injizieren, EINEN Broker teilen,
  `realized_pnl_today`-Closure, `daily_loss_cap≈1800`, `daily_token_budget`) → **zuletzt** UI.

### Offene Punkte / [VERIFY]
- `wiring.py`/Modul 11: `Research` direkt aus `research` bauen (geteilter Broker, Contract G);
  **No-op-`research_runner`** in den Executor (Contract B); `realized_pnl_today`-Closure (Query im
  Modul-6-Block) + `daily_loss_cap≈1800` + `daily_token_budget` + `now_fn=clock.now` an `ResearchTick`.
- **Commit:** committet, **falls** der Operator es triggert (Branch `phase8-scheduler`); „Commit ⇒
  Note-Update" gilt im selben Commit.

---

## Session stopped — 2026-06-28 (Modul 7: `scheduler/budget.py` — das Token-Budget-Gate)

### Completed
- **`scheduler/budget.py`** — `TokenBudget`, das deterministische Tages-Token-Budget (Decision 12,
  **kein AI**). Erfüllt das in Modul 6 definierte `safety.Budget`-Protocol (**löst den Stub ein**).
  Reuse des geteilten 8-Feld-Meters (`data/state/llm_usage.json`, von `research.token_meter`
  geschrieben über P4/P6/P7) — **kein** zweites Mess-System; es gibt **keinen** importierbaren Reader
  (nur das Script `usage_report.py`), also liest `budget.py` das JSON-Array selbst (fail-soft).
  - `consumed_today() -> int` — summiert alle vier billed Token-Felder (`input`+`output`+
    `cache_creation`+`cache_read`, tolerant gegen fehlende Keys) über die Records, deren UTC-`ts`
    auf **heute in `config.tz`** fällt (alle Modelle; system-weites Tagesbudget).
  - `is_exhausted() -> bool` — `daily_token_budget None` → False (+ 1 WARNING beim Konstruieren);
    sonst `consumed_today() >= budget` (Grenze inklusive). **Wirft nie** (Auto-Confirm vertraut dem Bool).
- **`scheduler/__init__.py`** exportiert jetzt zusätzlich `TokenBudget`.
- **`tests/test_budget.py`** — **13 Tests**: unter/über/exakt am Budget; cache-Felder gezählt;
  6-Feld-Record (ohne `cache_*`) toleriert; nur heutige Records; **Berlin-Grenze** (`22:30Z` zählt
  zum nächsten Berlin-Tag, CEST +2); fehlende/korrupte Log → 0 (fail-open, kein Raise); Bad-`ts`
  geskippt; `None` → 1 `scheduler.budget`-WARNING + nie erschöpft; **Protocol-Handoff** (echtes
  `TokenBudget` als `AutoConfirm.budget` → `REASON_BUDGET`); Export-Identität.

### Vier Konzept↔Code-Reconciliations (Code = Source of Truth)
- **(1) Konstruktor `TokenBudget(config, usage_log_path, *, now_fn=None)`** statt `(config,
  token_meter)` — das P4-`token_meter` hat **kein** Read-API; `budget.py` liest die JSON direkt. Der
  Pfad kommt explizit (wie `safety.py` `kill_path` nimmt) + `now_fn` für die Tagesgrenze. **Kein
  Edit an `config.py`/Modul 1.**
- **(2) Berlin-Tagesgrenze aus UTC-`ts`** — der Meter schreibt UTC (`Z`-Suffix), der Tag ist
  `config.tz` → `ts` wird **vor** `.date()` nach `config.tz` konvertiert. Stdlib-only (`fromisoformat`
  + `Z`→`+00:00` + `zoneinfo`), **kein** `research.timeutil`-Import (Isolation: `import
  scheduler.budget` zieht **NONE** cross-phase).
- **(3) Token-Maß = alle vier billed Felder** (tolerant gegen fehlende `cache_*`) → undercountet
  nie. v1, tunbar.
- **(4) Advisory-Budget fail-OPEN** (Log-Read-Fehler → consumed 0 → nicht erschöpft) — bewusst
  **anders** als `safety.py`s fail-CLOSED Loss-Breaker (Kosten-Kappe, kein Geld-Safety-Gate).

### Verifiziert (gemockt / lokal — kein Netz, kein LLM; Live = Operator)
- `pytest phase8_scheduler/tests -v` → **96 passed** (10 config + 6 exceptions + 19 clock + 18
  state + 12 killswitch + 18 safety + 13 budget). `py_compile` clean. **Import-Isolation:** `import
  scheduler.budget` zieht **NONE** broker_wrapper/persistence/external_data/research/execution/
  reward/debate/pandas/numpy/yfinance/anthropic/requests.
- **Regression grün + unberührt** (rein additiv): P2 62 · P5 146 · P7 128 (separat gelaufen). P1 52 ·
  P4 94 · P6 70 unverändert.

### Next — **Modul 8: `scheduler/research_tick.py`** (Konzept §8 — der eigentliche Blocker: autonome Candidates)
- `ResearchTick(research, state_store).ensure_candidates(state) -> ResearchResult`: triggert
  **ausschließlich** das echte `Research.run()` (P4, via Wiring) → frische `turbo_candidates.json`
  (1 Pick | `[]`), **nie** `seed_candidate.py` (kein `"MANUAL SEED"`-Marker → `test_no_manual_seed_
  marker`). `no_trade_reason` minimal (`EMPTY_UNIVERSE|LLM_ABSTAIN|VALIDATOR_REJECT|FILTER_FAIL|
  PREFLIGHT_FAIL`) → `state.last_no_trade_reason`. **Freshness-Disziplin (Contract B):** bei Abstain
  `save_candidates([])`, aber Gate 2 re-callt bei `[]` → der **No-op-`research_runner`** muss in den
  Executor injiziert werden (Wiring/Modul 11), echtes Research läuft **vorher** hier. `last_research_ts`
  aktualisieren.

### Offene Punkte / [VERIFY]
- `wiring.py`/Modul 11: `TokenBudget(config, _USAGE_LOG, now_fn=tz_now)` (Pfad `data/state/llm_usage.json`
  wie P4/P6/P7-Wiring) an `AutoConfirm` reichen; `realized_pnl_today`-Closure (Query in Modul-6-Block)
  + `daily_loss_cap≈1800` + `daily_token_budget` setzen; **No-op-`research_runner`** + EINEN Broker teilen.
- **Commit:** committet, **falls** der Operator es triggert (Branch `phase8-scheduler`); „Commit ⇒
  Note-Update" gilt im selben Commit.

---

## Session stopped — 2026-06-28 (Modul 6: `scheduler/safety.py` — das Auto-Confirm-Gate)

### Completed
- **`scheduler/safety.py`** — `AutoConfirm`, der deterministische `confirm_fn`-Ersatz für den
  P5-Human-Confirm (das schwerste Safety-Modul, **kein AI**). Fünf harte Gates, **alle** müssen
  halten, sonst `(False, reason)`:
  1. **Demo-Lock (strukturell, config-only — Contract D):** `config.account == "demo"`, sonst
     `False` + `logger.critical`. Liest **nicht** den `OrderPlan` (der trägt kein `account`).
  2. **Kill-Switch aus:** `killswitch.is_set(kill_path)` False (Modul 5, live pro Aufruf gelesen).
  3. **Unter Trade-Cap:** `state.trades_today < config.max_trades_per_day`.
  4. **Über Loss-Breaker:** `daily_loss_cap is not None` UND heutige realized P&L `> -cap` —
     **aus der DB** (Contract E) via injiziertem `realized_pnl_today(session_date)`, **nicht**
     `state.realized_pnl_today` (Snapshot-Falle). DB-Read **fail-CLOSED** (wirft → block).
  5. **Budget nicht erschöpft:** `budget.is_exhausted()` False (duck-typed `Budget`-Protocol).
- **Zwei Aufruf-Flächen, ein gemeinsamer `_evaluate`** (können nie divergieren): `can_open(state)
  -> (bool, reason)` (Pre-Cycle-Gate, spart Tokens) + `__call__(order_plan) -> bool` (Final-Gate;
  lädt State **live** aus dem Store — Contract A, kein Snapshot; ignoriert `order_plan`).
- **`scheduler/__init__.py`** exportiert jetzt zusätzlich `AutoConfirm` + `Budget`.
- **`tests/test_safety.py`** — **18 Tests**: happy-path (can_open + __call__); `account="live"` →
  NOT_DEMO + 1 critical; Demo-Lock schlägt andere Fails; Kill blockt + **live** in `__call__`;
  Cap at-limit/under; Loss unter Cap / **exakt am Cap** / knapp drüber; session_date == `state.date`;
  **P&L-Read-Fehler → fail-closed block** + critical; Loss-Cap None → 1 `scheduler.safety`-WARNING +
  kein Block + Reader nie gerufen; Budget erschöpft; `can_open`/`__call__` konsistent; `__call__`
  ignoriert Plan-Felder; Package-Export-Identität.

### Drei Konzept↔Code-Reconciliations + zwei Design-Entscheidungen (Code = Source of Truth)
- **(1) Konstruktor +5. Arg `realized_pnl_today: Callable[[str], float]`** — die §5-Skizze
  `AutoConfirm(config, state_store, kill_path, budget)` hat keine DB-P&L-Quelle, Contract E
  verlangt sie. Injizierte Closure (Wiring backt sie DB-seitig) hält `safety` phasen-isoliert
  (`import scheduler.safety` zieht **NONE** cross-phase). **Query-Form (für Wiring/Modul 11):**
  `SELECT COALESCE(SUM(profit_loss),0.0) FROM trade_outcomes WHERE session_date=? AND profit_loss
  IS NOT NULL` (OPEN/CANCELLED sind NULL → fallen raus); Argument = `state.date`.
- **(2) §5-`order_ctx.account=="demo"`-Doppel-Check entfällt** (Contract D: kein `account` im
  `OrderPlan`) → Demo-Lock config-only; strukturelle zweite Hälfte (nur `ig_demo`-Broker) = Wiring.
- **(3) `budget` = duck-typed `Budget`-Protocol** (Operator-Sondernotiz: „stub via Protocol" statt
  Modul 7 vorziehen). Modul-7-`TokenBudget` wird es erfüllen.
- **Design A:** Loss-Breaker-DB-Read **fail-CLOSED** (wirft → block + critical; im Zweifel nicht traden).
- **Design B:** eigene `scheduler.safety`-WARNING bei `daily_loss_cap=None` beim Konstruieren
  (zusätzlich zur `config`-WARNING — `config` warnt vorm Wert, `safety` warnt, dass **sein** Gate
  aus ist; eine WARNING pro Verantwortung).

### Verifiziert (gemockt / lokal — kein Netz, kein LLM; Live = Operator)
- `pytest phase8_scheduler/tests -v` → **83 passed** (10 config + 6 exceptions + 19 clock + 18
  state + 12 killswitch + 18 safety). `py_compile` clean. **Import-Isolation:** `import
  scheduler.safety` zieht **NONE** broker_wrapper/persistence/external_data/research/execution/
  reward/debate/pandas/numpy/yfinance/anthropic/requests.
- **Regression grün + unberührt** (rein additiv in `phase8_scheduler/`): P2 62 · P5 146 · P7 128
  (cross-referenzierte Phasen separat gelaufen — `tests.conftest`-Namenskollision). P1 52 · P4 94 ·
  P6 70 unverändert (kein berührter Import).

### Next — **Modul 7: `scheduler/budget.py`** (Konzept §7, TDD ≥3) — löst den `Budget`-Protocol-Stub ein
- `TokenBudget(config, token_meter)` mit `consumed_today() -> int` + `is_exhausted() -> bool` (muss
  das in `safety.py` definierte `Budget`-Protocol erfüllen). **Kein Reader** in `token_meter`
  (Contract bestätigt) → die heutigen 8-Feld-Records aus `data/state/llm_usage.json` selbst
  summieren, `ts`-Datum-Filter **Europe/Berlin** (konsistent mit `state`-Rollover).
  `daily_token_budget=None` → nie erschöpft + **eine** WARNING (gehört `budget.py`, nicht `config`).
  Tests: unter Budget → False; über → True; None → False + WARNING.
- **Danach Modul 8 `research_tick.py`** (der eigentliche Blocker: autonome Candidates) + Modul 9
  `reconcile.py` + Modul 11 `runner.py`. Beim Wiring: die `realized_pnl_today`-Closure mit der
  obigen Query an `AutoConfirm` reichen; `daily_loss_cap≈1800` setzen.

### Offene Punkte / [VERIFY]
- `wiring.py`/Modul 11: `realized_pnl_today`-Closure (Query oben) + `daily_loss_cap` setzen; EINEN
  Broker teilen (Contract G); `Research` direkt aus `research` bauen.
- **Commit:** dieser Step ist committet, **falls** der Operator es triggert (Branch
  `phase8-scheduler`); „Commit ⇒ Note-Update" gilt im selben Commit (Status-Tabelle ✅ + dieser Block).

---

## Session stopped — 2026-06-28 (Modul 5: `scheduler/killswitch.py`)

### Completed
- **`scheduler/killswitch.py`** — der Datei-Kill-Switch (`data/state/KILL`, Decision 8),
  **stateless Modul-Funktionen** (Konzept §4-Signaturen), **fail-soft / wirft nie**:
  - `is_set(kill_path)` = reine Existenzprüfung (robust gegen **jeden** Inhalt — auch ein
    leeres `touch` oder eine halb-geschriebene Datei lesen als „halted"; fail-safe Richtung).
  - `set_kill(kill_path, reason)` = mkdir parent + **atomic** (`.tmp`+`os.replace`) JSON
    `{"reason", "ts"(UTC ISO)}`. Konvention: Backoff-Trip `"auto:backoff"`, UI/Operator
    `"manual:<text>"`. Der laute Trip-Log bleibt im **Runner** (Loop loggt `critical`) →
    killswitch ist im Happy-Path still (single responsibility, wie `state.py`).
  - `clear_kill(kill_path)` = `unlink(missing_ok=True)` (fehlende Datei → no-op).
  - `read_reason(kill_path)` = tolerant: missing/empty/unparseable → `None`; JSON-Objekt →
    `"reason"`; Plain-Text → stripped raw (Operator-Hand-Reason); unlesbare existierende
    Datei → **eine** WARNING + `None`.
- **`scheduler/__init__.py`** exportiert jetzt zusätzlich das **Modul** `killswitch`
  (`from . import killswitch`; Consumer rufen `killswitch.is_set(...)`, wie die §10-Loop-Skizze).
- **`tests/test_killswitch.py`** — **12 Tests**: is_set False→True; auto-/manual-Reason
  roundtrip; parent-dir auto + kein `.tmp`-Rest; clear disengaged; clear-missing no-op;
  read missing→None; leeres `touch` = is_set True + reason None; Plain-Text→raw;
  overwrite (latest wins); unlesbar→1 WARNING+None (monkeypatched `read_text`); Modul-Export-Identität.

### Design-Notizen (Code = Source of Truth — dated §4-Annotation im Konzept)
- **Inhalt = JSON `{reason, ts}`** (Konzept sagt nur „Reason+Timestamp") — konsistent mit
  `scheduler_state.json`, sauberer roundtrip. **`is_set` = nur Existenz** (operator-touchbar).
  **`read_reason` fail-soft** (empty/plain-text/unparseable toleriert). **atomic + parent-dir**
  (Paket-Pattern). **Als Modul-Namespace exportiert**, nicht als bare Funktionen am Paket-Root.

### Verifiziert (gemockt / lokal — kein Netz, kein LLM; Live = Operator)
- `pytest phase8_scheduler/tests -v` → **65 passed** (10 config + 6 exceptions + 19 clock +
  18 state + 12 killswitch). `py_compile` clean. **Import-Isolation:** `import
  scheduler.killswitch` zieht **NONE** cross-phase/heavy (pure stdlib: json/os/datetime/
  pathlib/logging).
- **Regression grün + unberührt** (rein additiv in `phase8_scheduler/`): P1 52 · P2 62 ·
  P4 94 · P5 146 · P6 70 · P7 128 (separat gelaufen — `tests.conftest`-Namenskollision).

### Next — **Modul 6: `scheduler/safety.py`** (Konzept §5, das Auto-Confirm-Gate — schwerstes Safety-Modul, TDD ≥8 Tests)
- `AutoConfirm(config, state_store, kill_path, budget)` als `confirm_fn`-Ersatz für den
  P5-Human-Confirm. `__call__(order_ctx) -> bool` (Final-Gate vor `place_order`) **und**
  `can_open(state) -> (bool, reason)` (Pre-Cycle-Gate, spart LLM-Tokens). `True` **nur** wenn
  **alle** harten Bedingungen: (1) `config.account == "demo"` (Demo-Lock strukturell aus der
  **Config**, **nicht** aus dem `OrderPlan` — Contract D; alles ≠ demo → `False` +
  `logger.critical`); (2) `killswitch.is_set` False; (3) `state.trades_today <
  max_trades_per_day`; (4) Tages-Loss-Breaker: `daily_loss_cap is not None` und
  heutige realized P&L `> -daily_loss_cap` — **aus der DB** (Contract E), **nicht** aus
  `state.realized_pnl_today` (Snapshot-Falle, s. Modul-4-Reconciliation); `None` → eine
  WARNING, kein Block; (5) `budget.is_exhausted()` False. ⚠ **Vor Bau Contracts A/D/E
  heranziehen** + `budget.py`-API (Modul 7, evtl. vorzuziehen oder per Protocol stubben).

### Offene Punkte / [VERIFY]
- `safety.py`: `realized_pnl_today` aus der **DB** lesen (Contract E) — die DB-Query-Form
  beim Wiring/Modul 6 klären (heutige `trade_outcomes`/`reward_pts` über `session_date`).
  `budget` ist eine Dependency → entweder Modul 7 `budget.py` vorziehen oder via Protocol stubben.
- **Commit:** dieser Step ist committet (Operator-getriggert, Branch `phase8-scheduler`);
  „Commit ⇒ Note-Update" im selben Commit.

---

## Session stopped — 2026-06-28 (Modul 4: `scheduler/state.py`)

### Completed
- **`scheduler/state.py`** — `SchedulerState` (mutable `@dataclass`, concept §3:
  date/trades_today/realized_pnl_today/last_research_ts/last_reconcile_ts/
  consecutive_failures/kill_reason/last_no_trade_reason) + `StateStore`:
  - `load()` **self-heals, never raises** — missing file → fresh `SchedulerState()`;
    corrupt/partial JSON → **eine** WARNING + fresh state; unbekannte Keys gedroppt,
    fehlende defaulted (forward/backward-compat via `dataclasses.fields`-Filter).
  - `save()` **atomic** (`.tmp` + `os.replace`) — die P2 `_atomic_write`-Pattern **lokal
    kopiert** (nicht importiert; `import scheduler.state` zieht **NONE** cross-phase/heavy).
  - `rollover_if_new_day(state, now)` — neues Europe/Berlin-Datum ⇒ reset
    trades/pnl/failures + `kill_reason`/`last_no_trade_reason`=None, `date`=today;
    **behält** `last_research_ts`/`last_reconcile_ts` (last-action ts, keine Day-Counter).
    Idempotent (same-day = no-op). `now` muss tz-aware in der Daemon-Zone sein (Clock liefert das).
  - `record_cycle(state, result)` — duck-typed (kein `execution`-Import); `trades_today += 1`
    nur bei `TRADE_STATUSES = {OPEN, CLOSED_BY_BROKER, TIME_STOP}` (**Contract E**);
    `profit_loss` best-effort akkumuliert wenn present. Berührt **nicht**
    `consecutive_failures` (backoff), `last_no_trade_reason` (Loop/research_tick) oder die ts.
- **`scheduler/__init__.py`** exportiert jetzt zusätzlich `SchedulerState` + `StateStore`.
- **`tests/test_state.py`** — **18 Tests**: roundtrip; load missing/corrupt(1 WARNING)/
  tolerant(unknown+missing keys); atomic save (parent auto-created, kein `.tmp`-Rest);
  rollover new-day/same-day/idempotent/fresh-init; `record_cycle` × {OPEN,CLOSED_BY_BROKER,
  TIME_STOP} zählt / × {NO_TRADE,ABORTED_BY_USER,ABORT} zählt nicht; pnl present vs None;
  failures/reason unberührt; Package-Export-Identität.

### Eine Konzept↔Code-Reconciliation (Code = Source of Truth — dated §3-Annotation im Konzept)
- **`realized_pnl_today` = best-effort persisted Snapshot, NICHT die Loss-Breaker-Quelle.**
  `record_cycle` faltet P&L nur wenn das Cycle-Result sie trägt (zur Cycle-Zeit = der
  TIME_STOP-Pfad; **Contract E**: `CLOSED_BY_BROKER` liefert `profit_loss=None`, erst per
  Reconcile/Modul 9 aufgelöst) → das Feld kann für broker-closes der DB hinterherhängen.
  Der **autoritative** Tages-Loss-Breaker (`safety.py`/Modul 5) liest die heutige realized
  P&L aus der **DB** (Contract E) und hängt **nicht** an diesem Feld. Hält Modul 4
  self-contained + vermeidet eine Doppelzähl-Falle (jetzt geflaggt, damit kein späteres
  Modul den Breaker fälschlich an diesen Snapshot hängt).

### Verifiziert (gemockt / lokal — kein Netz, kein LLM; Live = Operator)
- `pytest phase8_scheduler/tests -v` → **53 passed** (10 config + 6 exceptions + 19 clock
  + 18 state). `py_compile` clean. **Import-Isolation:** `import scheduler.state` zieht
  **NONE** von broker_wrapper/persistence/external_data/research/execution/reward/debate/
  pandas/numpy/yfinance/anthropic/requests.
- **Regression grün + unberührt** (rein additiv in `phase8_scheduler/`): P1 52 · P2 62 ·
  P4 94 · P5 146 · P6 70 · P7 128 (separat gelaufen — `tests.conftest`-Namenskollision).

### Next — **Modul 5: `scheduler/killswitch.py`** (Konzept §4, klein, TDD)
- Modul-Funktionen `is_set(kill_path)`, `set_kill(kill_path, reason)`, `clear_kill(kill_path)`,
  `read_reason(kill_path)`. Datei-Existenz = Wahrheit; Reason+Timestamp im Inhalt
  (`auto:backoff` vom Backoff-Trip, `manual:<text>` von UI/Operator). Geteilt von `safety`
  (Leser) + `webui` (Schreiber) → eigenes Mini-Modul (one file = one responsibility).
  Tests ≥4: set→is_set True; clear→False; reason roundtrip; fehlende Datei → kein Crash.
  Stdlib-only, fail-soft (fehlende/korrupte Datei → kein Raise, wie `state.load`).

### Offene Punkte / [VERIFY] (für spätere Module, jetzt nur dokumentiert)
- `safety.py`: `daily_loss_cap`-Produktionswert (≈€1800) + `realized_pnl_today` aus der **DB**
  (Contract E, s. Reconciliation oben) — beim Wiring setzen, **nicht** an den State-Snapshot hängen.
- **Commit:** dieser Step ist committet, **falls** der Operator es triggert (Branch
  `phase8-scheduler`); „Commit ⇒ Note-Update" gilt im selben Commit.

---

## Session stopped — 2026-06-28 (Modul 3: `scheduler/clock.py`)

### Completed
- **`scheduler/clock.py`** — `Phase`-Enum (`PRE_OPEN | WINDOW | POST_WINDOW | IDLE`) +
  `Clock(config, *, now_fn, sleep_fn)`: `now()` (tz-aware in `config.tz`), `classify(now)`,
  `seconds_until(target, now)`, `sleep(s)` (delegiert an `sleep_fn`), `market_is_open(now)`.
  Erstes echtes Logik-Modul. `_parse_hhmm` **lokal gespiegelt** von P5 `gates._parse_hhmm`
  (nicht importiert — Phasen-Isolation für einen Einzeiler).
- **`scheduler/__init__.py`** exportiert jetzt zusätzlich `Clock` + `Phase`.
- **`tests/test_clock.py`** — **19 Tests**: alle 4 Phasen + Weekend; inklusive Fenster-
  Grenzen (09:00/17:30 → WINDOW); `seconds_until` same-day/across-midnight/across-weekend,
  strikt-nächster bei Boundary==now, `PRE_OPEN`-Target, `IDLE`→`ValueError`; `now`/`sleep`-
  Delegation; `market_is_open`-Delegation an P3; **config-getriebenes Fenster** (Override
  reklassifiziert); Package-Export.

### Zwei Design-Entscheidungen (Code = Source of Truth — dated §2-Annotation im Konzept)
- **★ DST-Falle gefixt:** `(a - b)` zweier datetimes mit **demselben** `ZoneInfo`-Objekt
  rechnet **naiv wall-clock** (eine Spanne über die Frühjahrs-Umstellung liefert 63h statt
  real 62h). `seconds_until` konvertiert daher **beide Seiten nach UTC** vor der Subtraktion
  → DST-korrekt (Tests pinnen 62h Spring-Forward / 64h Fall-Back, **nicht** 63h). Das ist
  exakt das vom Konzept geforderte „keine naiven `timedelta`-Stunden-Hacks".
- **Konzept↔Code-Reconciliation (market_hours-Reuse, Decision 2):** `is_market_open`
  vermengt Weekday **und** 09:00–17:30 → es kann `classify` nicht allein „heute Handelstag?"
  um 08:00 beantworten, und das Scheduler-WINDOW ist **config-getrieben** (test-überschreibbar),
  nicht an P3s festes Fenster gekoppelt. Aufteilung: `classify` = Weekday-Check + config-Fenster
  (`_parse_hhmm`); P3s Prädikat wird **lazy** via `Clock.market_is_open` reused (Laufzeit-Guard
  im Runner). So bleibt der heiße Pfad stdlib-only (Import-Isolation bewiesen: `import
  scheduler.clock` zieht **kein** pandas/external_data — erst der `market_is_open`-Aufruf).
  v1 **kein Feiertagskalender** (Weekday-Proxy, gleiche P3-Vereinfachung; Feiertage →
  Broker-/VETO-fail-closed downstream).

### Verifiziert (gemockt / lokal — kein Netz, kein LLM; Live = Operator)
- `pytest phase8_scheduler/tests -v` → **35 passed** (10 config + 6 exceptions + 19 clock).
  `py_compile` clean. **Import-Isolation:** `import scheduler.clock` zieht **NONE** von
  pandas/numpy/external_data/yfinance/broker_wrapper/execution/research/reward.
- **Regression grün + unberührt** (additiv in `phase8_scheduler/`; nur ein read-only lazy
  Import von `external_data.market_hours`): P1 52 · P2 62 · P4 94 · P5 146 · P6 70 · P7 128
  (separat gelaufen — `tests.conftest`-Namenskollision; jede Phase einzeln).

### Next — **Modul 4: `scheduler/state.py`** (Konzept §3, TDD)
- `SchedulerState`-Dataclass (date/trades_today/realized_pnl_today/last_research_ts/
  last_reconcile_ts/consecutive_failures/kill_reason/last_no_trade_reason) + `StateStore`
  (`load`/`save` **atomic** tmp+`os.replace` wie P2 `state.py`; `rollover_if_new_day` resettet
  Counter/Loss/Failures bei neuem Europe/Berlin-Datum, idempotent; `record_cycle` inkrementiert
  `trades_today` **nur** bei echtem Trade-Status {OPEN, CLOSED_BY_BROKER, TIME_STOP} — Contract E).
  Tests ≥5 (roundtrip, Rollover resettet/selber-Tag-nicht, atomic überlebt Teil-Write,
  record_cycle nur bei Trade). Kein Netz/LLM. **Clock liefert `now` für den Rollover.**

### Offene Punkte / [VERIFY] (für spätere Module, jetzt nur dokumentiert)
- `safety.py`: `daily_loss_cap`-Produktionswert (≈€1800) + `realized_pnl_today` aus der DB
  (Contract E) — beim Wiring setzen.
- **Commit:** dieser Step ist committet, **falls** der Operator es triggert (Branch
  `phase8-scheduler`); „Commit ⇒ Note-Update" gilt im selben Commit.

---

## Session stopped — 2026-06-28 (Modul 2: `scheduler/exceptions.py`)

### Completed
- **`scheduler/exceptions.py`** — `SchedulerError` (Basis, `code="SCHEDULER_ERROR"`) →
  `PreflightError` (`code="PREFLIGHT_ERROR"`). `code`-Class-Attr-Muster **verbatim wie P5**
  (`execution/exceptions.py`), stdlib-only, **importiert nichts cross-phase**.
- **`scheduler/__init__.py`** exportiert jetzt zusätzlich `SchedulerError` + `PreflightError`.
- **`tests/test_exceptions.py`** — **6 Tests**: Basis ist `Exception` + Code; `PreflightError`
  erbt + überschreibt Code; distinkte Codes; Family-Catch (`except SchedulerError`);
  Message-Roundtrip + `code` am Instance; Package-Export-Identität.

### Bewusste Scope-Entscheidung (minimal + ehrlich — dated §-Annotation im Konzept)
- Das Konzept-`exceptions.py # SchedulerError, PreflightError, ...` lässt das „…" — **bleibt
  leer.** Die **einzige** custom Raise-Stelle ist `runner.preflight()` (`PreflightError`,
  fail-closed Keyring/Broker/DB — der Deployment-Top-Risk Q3). Alle anderen Module returnen
  Werte oder fehlschlagen fail-closed **ohne** Re-raise (`safety`→`(bool, reason)`, `budget`→
  `bool`, `reconcile`/`research_tick`→`logger.critical`, `killswitch`/`state` self-heal). Keine
  spekulativen `StateError`/`BudgetError` → die Datei **wächst pro Modul** bei echtem Bedarf.

### Verifiziert (gemockt / lokal — kein Netz, kein LLM; Live = Operator)
- `pytest phase8_scheduler/tests -v` → **16 passed** (10 config + 6 exceptions). `py_compile`
  clean. **Import-Isolation:** `import scheduler.exceptions` zieht **kein** cross-phase/heavy
  Modul (NONE).
- **Regression grün + unberührt** (additiv in `phase8_scheduler/`): **P5 146 · P7 128** (separat
  gelaufen — `tests.conftest`-Namenskollision; jede Phase einzeln). P1 52 · P2 62 · P4 94 · P6 70
  unverändert.

### Next — **Modul 3: `scheduler/clock.py`** (erstes echtes Logik-Modul, TDD)
- `Clock(config, *, now_fn, sleep_fn)` mit `now() -> datetime` (tz-aware Europe/Berlin),
  `classify(now) -> Phase` (PRE_OPEN | WINDOW | POST_WINDOW | IDLE), `seconds_until(target, now)`,
  `sleep(s)` (delegiert an `sleep_fn`, Tests no-op). **Reuse `external_data.market_hours.
  is_market_open`** für „Handelstag/Markt offen" (Mo–Fr, DST-aware); die WINDOW-Phase nutzt
  `config.window_open`/`window_close` (**09:00–17:30 bereits bestätigt**, s. Modul-1-Block) via
  einem `_parse_hhmm`-Idiom (spiegelt P5 `gates._parse_hhmm`). DST: tz-aware Arithmetik, **keine**
  naiven `timedelta`-Stunden-Hacks. Tests ≥6 mit Fake-`now_fn` (Wochenende→IDLE, vor/in/nach
  Fenster, `seconds_until(WINDOW)` über Mitternacht, DST-Tag plausibel).

### Offene Punkte / [VERIFY] (für spätere Module, jetzt nur dokumentiert)
- `safety.py`: `daily_loss_cap`-Produktionswert (≈€1800) + `realized_pnl_today` aus der DB
  (Contract E) — beim Wiring setzen.
- **Commit:** dieser Step ist committet, **falls** der Operator es triggert (Branch
  `phase8-scheduler`); „Commit ⇒ Note-Update" gilt im selben Commit.

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
