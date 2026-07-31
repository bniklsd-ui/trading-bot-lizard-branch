---
status: closed-phase
purpose: Phase-8 head — autonomous scheduler loop, caps/breakers, verified contracts (phase ✅ live-verified 2026-07-03)
read-when: working in phase8_scheduler/ — read this head + its newest Session-stopped block first
detail: L2
up: ../CLAUDE.md
down:
  - ./SESSIONS_ARCHIVE.md      # full session history (L3)
  - ./README.md
  - ../docs/concepts/phase8_scheduler_concept.md   # full concept/plan snapshot (L3)
updated: 2026-07-11
---
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
🟡 nach `main` gemerged** (ehrlich geflaggt, s. `## Session stopped — 2026-06-30`). Es fehlte
damals ein echter Mehr-Zyklen-/Mehr-Tage-Lauf, der (a) einen netto-neuen autonomen Trade in
**einem** sauberen Lauf öffnet+schließt und (b) die Safety-Breaker tatsächlich auslösen sieht —
**beides carried in den v1.5-Hotfix** (`PHASE8_V1.5_HOTFIX_HANDOVER.md`: der Bot abstained fast
immer → Variety + Clamp/Floor + echte Lessons). **Token-Budget by-default scharf** (Default
`200_000` ≈ €0.8/Tag; vorher `None`/aus).

> **✅ Update (2026-07-03): Phase 8 ABGESCHLOSSEN + live-verifiziert.** Beide oben genannten
> fehlenden Punkte sind jetzt bewiesen — der weiterlaufende Live-Test lieferte einen **zweiten**
> net-new autonomen open→close **und** einen tatsächlich **auslösenden Safety-Breaker** (das
> Tages-Token-Budget erschöpfte sich mitten im Lauf und blockierte weitere Trades, fail-closed,
> kein Crash). Nikinger-bestätigt. Der 🟡-Merge-Flag oben ist damit **historisch** (Stand
> 2026-06-30) — der aktuelle Stand ist ✅. Details: `## Session stopped — 2026-07-03 (✅
> Phase-8-Live-Beweis abgeschlossen)` unten. **Nächster Track = V2** (siehe
> `PHASE8_CLOSEOUT_HANDOVER.md`), noch nicht in Claude Code gestartet.

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
| `scheduler/runner.py` | die Loop / Daemon-Orchestrator + Preflight + Shutdown + `request_stop()` + optionaler `universe_refresher` (Phase 9/V2, Default `None` = bit-identisch); POST_WINDOW-Sleep seit 2026-07-11 gecappt (s. `## Session stopped — 2026-07-11`) | ✅ (Modul 10, 24 Tests — 18 + 6 v2) |
| `scheduler/run.py` | `python -m scheduler.run` Entry (in-package, lazy `scripts.wiring`, SIGTERM/SIGINT → `request_stop`) | ✅ (Modul 11, 6 Tests) |
| `scripts/wiring.py` | Composition Root `build_scheduler()` — voller P1–P7-Stack (Debatte + Reward in EINEN Executor), 3 Closures + `universe_refresher`-Closure (Phase 9/V2) | ✅ (Modul 11, operator-run) |
| `scripts/run_scheduler.sh` · `smoke_test.py` · `live_test.py` | Operator-Tools (Start-Script · offline Sim-Tag mit Fakes · echter unbeaufsichtigter IG-Demo-Zyklus) | ✅ (Modul 11, operator-run) |
| `webui/api.py` + `webui/static/*` + `scripts/run_webui.sh` | FastAPI read-mostly (DB `mode=ro` + `scheduler_state.json` + Kill/Command-Dateien) + statisches Dark-Neumorphism-Dashboard (GitHub-Dark, Monospace, Polling 7 s, kein Build-Step); Control **nur** Datei-Writes. **+ Token-Meter-Card** (`/api/token_usage`) **+ Last-Cycle-Reasoning** (`/api/last_cycle` zeigt jetzt Research-Pick + Bull/Bear/Judge-Transkript) — s. `## UI-Erweiterung — 2026-06-29`. **v1.7 (2026-07-02): `/api/status`s `trades_today`/`realized_pnl_today` DB-gespeist** (nicht mehr der lagging `scheduler_state.json`-Snapshot) — s. `## Session stopped — 2026-07-02 (v1.7: /api/status DB-gespeist)` | ✅ (Modul 12, 20 Tests) |
| `tests/*` | gemockt, kein Netz/LLM/echter sleep (199, Schwerpunkt `test_runner` + `test_safety` + `test_webui`) | ✅ |

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

> 🔁 **Phase-10 (V3) additive edit (2026-07-19, Nikinger-beauftragt, code = source of truth):**
> `scheduler/run.py` gained `--enable-paper-debate` (mirrors `--enable-ig-bars` exactly:
> `store_true`, threads into `SchedulerConfig.enable_paper_debate`, default OFF unverändert) —
> the CLI arm for the already-built Council-Paper-Call (Phase 10 §10.3; wiring reads the config
> field since 2026-07-17). +1 test (`test_run.py`, **P8 221 → 222**). No other behaviour change.

> 🔁 **Phase-10 (V3) bugfix (2026-07-25, found during the first `--enable-paper-debate` data-week
> review, code = source of truth):** two silent 100%-failure-rate bugs in `scripts/wiring.py`,
> both live since Block B (2026-07-17), both root-caused against the week's logs
> (`phase10_v3/DATA_WEEK_REVIEW_2026-07-25.md` has the full forensic trail):
> - **`_build_paper_tracker`'s `bar_fetch`** called `broker.get_ohlcv(epic, "MINUTE_1", …)` —
>   `"MINUTE_1"` is not a valid IG resolution (`ig_adapter.VALID_RESOLUTIONS` has `"MINUTE"`, not
>   `"MINUTE_1"`). Every tick since the first paper trade went due (2026-07-20) raised and was
>   swallowed by the tracker's own best-effort guard (`logger.critical`, never crashes) — **422
>   consecutive failures over 5 days, 0 of 15 paper trades ever resolved.** Fixed: `"MINUTE"`
>   (two sites: docstring + the actual call). Confirmed the only occurrence repo-wide (grep). The
>   15 already-open paper trades from that week are **not** retroactively recoverable — a future
>   tick only fetches recent bars, not history back to their `created_utc` — the fix works
>   forward only.
> - **`_AbstainLLMAdapter._SCHEMA`** (the Haiku lesson-extraction call for `reflect_abstain`)
>   was missing `"additionalProperties": False` — Anthropic rejects Structured Outputs on an
>   `object`-type schema without it (HTTP 400, confirmed verbatim in this week's logs), so every
>   call fell back to a plain (non-JSON-constrained) completion; the prompt itself never asks for
>   JSON, so the German-prose fallback response failed `json.loads` at char 0 every time — **0
>   lessons extracted since this reflect path went live (2026-07-15), confirmed dead for its
>   entire lifetime, not just this week.** Fixed: added `"additionalProperties": False` (matches
>   the proven-working `phase7_reward/reward/brain.py` schema pattern) — no prompt change needed,
>   Structured Outputs constrains the output regardless of what the prompt literally says.
> - **Both fixes are additive, one-value corrections in already-V3-touched code**, applied
>   weekend/bot-stopped per the root `CLAUDE.md` "small necessary cleanup, note back to the
>   Nikinger" allowance — no gate/VETO/order-path touched. `scripts/wiring.py` has **no** dedicated
>   test file (documented "operator-run, not pytest-collected" convention, same as the
>   Council-Paper-Call session) — verified via `py_compile` (clean) + full regression (**P8 222 ·
>   P10 125, both unchanged** — the fixes touch only inline string/dict literals, no tested
>   module). A third finding from the same review — two `INSUFFICIENT_FUNDS` broker rejects this
>   week (refutes the earlier unconfirmed AEX-stop-distance hypothesis) — is **not** a code bug
>   and needs an operator `get_account`/`get_open_positions` check; see the review doc.

> ✅ **Phase-10 (V3) FINDING B1 — FIXED (2026-07-31, weekend bugfix session, bot stopped;
> full evidence: `phase10_v3/DATA_WEEK_REVIEW_2026-07-31.md` §4 B1):** `scripts/wiring.py:616`
> built `ExecutionConfig.point_values` from the **static** 4-epic `research.EXTENDED_UNIVERSE`,
> while research trades the **DB universe** (Phase 9 / V2, 8 active epics). Every epic outside
> those 4 silently fell back to `ExecutionConfig.point_value_for()`'s `1.0` default — for
> `IX.D.AEX.IFM.IP` the DB's own live-resolved value (`point_value_source='ig_fields'`) is
> **40.0** ("Niederlande 25 Kassa (40€)"). Result: **40× oversizing** — the 2026-07-30 order was
> sized 26.8 (intended risk 804 €, real risk at the 30-pt stop **32.160 € = 120 % of the
> account**, notional 1.18 M€); IG rejected it with `INSUFFICIENT_FUNDS`, as it did **all three**
> AEX orders ever placed (07-15, 07-20, 07-30). This also retroactively explains the 2026-07-15
> reject filed as "unrecoverably lost" in `phase5_execution/CLAUDE.md` — that note's AEX
> hypothesis pointed at the right instrument but the wrong constant (not stop distance,
> `point_value`).
> **Fixed, both parts** — the symptom fix alone would have left the next V2-promoted epic
> silently at 1.0: (a) `point_values` now sourced from `_build_universe_from_db()` (already
> existed **in this same file**, `wiring.py:105-129`, fail-soft fallback to `EXTENDED_UNIVERSE`
> included) instead of `EXTENDED_UNIVERSE`; and (b) `sizing.compute_size` (Phase-5 file, see
> `phase5_execution/CLAUDE.md`) now fails closed (`(0.0, "point_value_unmapped")`) for an epic
> absent from a **populated** `point_values` map, rather than silently sizing at 1.0 —
> `point_value_for()` itself is unchanged (its 1.0 default now only fires on an **empty** map,
> i.e. the feature genuinely unwired). No dedicated test file for `wiring.py` (documented
> "operator-run, not pytest-collected" convention) — verified via `py_compile` + unchanged
> P8 count (**222**, unaffected — the edit touches only an inline dict comprehension).

---

## Session stopped — 2026-07-11 (Hotfix: POST_WINDOW-Sleep gecappt — Kill-Switch/SIGINT waren bis zu ~63h wirkungslos)

> **Auslöser:** kein Phase-8-Arbeitsauftrag — Nebenbefund am Anfang der Phase-10-V3-
> Weekend-Session. Der Nikinger meldete: `Strg+C` im Scheduler-Terminal + Web-UI-Kill-
> Switch zeigten nach 10 Minuten keine Wirkung, Vermutung "wartet bis zum nächsten Zyklus,
> der am Wochenende Tage dauert". Diagnose bestätigte das exakt; Fix + Kill nach
> Nikinger-Freigabe (AskUserQuestion, 2026-07-11) durchgeführt, außerhalb des
> Phase-10-Scopes aber **extrem notwendig** (Root-`CLAUDE.md` Working-Style-Regel
> "b) extremely necessary, nach Check mit dem Nikinger").

### Was (Befund)
- **Prozess:** `python -m scheduler.run --daily-loss-cap 1800 --max-trades 5` (PID
  19860), gestartet Do 2026-07-09 13:28 CEST, lief trotz zweifachem Stop-Versuch
  (Ctrl+C **und** Dashboard-Kill-Switch) unverändert weiter bis zum manuellen `kill -9`
  in dieser Session (Sa 2026-07-11 07:44 UTC).
- **Kill-Switch griff, aber zu spät:** `data/state/KILL` existierte bereits
  (`{"reason": "manual:dashboard", "ts": "2026-07-11T07:32:03Z"}`), 11 Min. vor der
  Diagnose — genau die vom Nikinger beobachteten "10 Minuten ohne Wirkung".
- **Prozesszustand:** `wchan = hrtimer_nanosleep` — echter `time.sleep()`, kein Hang/Bug
  im Sinne eines Deadlocks. `scheduler_state.json` zeigte den letzten Reconcile Fr
  2026-07-10 17:29:30 CEST (POST_WINDOW nach Handelsschluss 17:30).

### Wo (Root Cause)
- `scheduler/runner.py::_run_phase`, **POST_WINDOW**-Zweig (vor dem Fix Zeile 370):
  `self._clock.sleep(self._clock.seconds_until(Phase.PRE_OPEN, now))` — **ein einziger,
  ungecappter** `time.sleep()`-Call. Von Freitag-Handelsschluss aus berechnet
  `seconds_until(PRE_OPEN)` den nächsten **Handelstag** (Montag `pre_open_time` =
  08:50 CEST, `window_open` 09:00 minus `pre_open_lead_min` 10) → ein Sleep von **~63
  Stunden am Stück**.
- `request_stop()` (Ctrl+C/SIGTERM-Handler, :260-269) setzt nur ein **In-Memory-Flag**;
  der Loop prüft es (wie den Kill-Switch, :292/:295) **ausschließlich am Top jeder
  Iteration** — also erst, **nachdem** der laufende `clock.sleep()`-Call zurückkehrt.
  Pythons `time.sleep()` retryt einen durch ein Signal unterbrochenen Syscall automatisch
  bis zum vollen Rest (PEP 475) — der Handler feuert sofort, aber der Sleep selbst läuft
  ungestört zu Ende. Für **PRE_OPEN** (:339-341) und **IDLE** (:372) ist das harmlos, weil
  beide bereits mit `self._idle_poll_s` (Default 5 Min) gecappt sind — **nur der
  POST_WINDOW-Zweig hatte kein Cap.** Ein Freitagabend-Stop-Versuch traf damit exakt den
  einzigen ungecappten Pfad, und zwar in seiner längsten Ausprägung (Wochenende statt
  Übernacht-Lücke).
- **Kein Scope-Zufall, dass niemand das vorher sah:** der Daemon läuft seit Phase-8-
  Live-Verifikation (2026-07-03) unbeaufsichtigt durch — ein Stop mitten in POST_WINDOW
  wurde vorher nie gebraucht/versucht.

### Wie (Fix)
- `scheduler/runner.py` POST_WINDOW-Zweig auf exakt das PRE_OPEN-Muster umgestellt:
  ```python
  self._clock.sleep(
      min(self._clock.seconds_until(Phase.PRE_OPEN, now), self._idle_poll_s)
  )
  ```
  Reiner Additiv-Cap, keine neue Abstraktion (bereits im gleichen File als Muster
  vorhanden). `_run_phase`-Docstring ergänzt (Verweis auf diesen Block).
- `tests/test_runner.py::test_post_window_forces_reconcile_and_sleeps_to_next_pre_open`
  verschärft: statt der laxen `sleep.sleeps[-1] > 0` jetzt
  `sleep.sleeps[-1] == cfg.idle_poll_min * 60` — pinnt das Cap-Verhalten, damit eine
  Regression hier künftig ein rotes Pytest ist, kein stilles Wieder-Aufreißen.
- **Effekt:** ein zukünftiger Stop (Ctrl+C, SIGTERM, Kill-Switch) während POST_WINDOW
  greift jetzt binnen **max. 5 Minuten** statt bis zu ~63 Stunden — WINDOW (`cycle_interval_s`,
  Default 5 Min) und PRE_OPEN/IDLE waren bereits in dieser Größenordnung.

### Warum (Impact/Einordnung)
- Der Kill-Switch ist laut Root-`CLAUDE.md` Hard Rule 2 ("Never bypass VETOs") /
  Konzept §4 die letzte Handbremse — genau in der unbeaufsichtigten Wochenend-/
  Übernacht-Phase am wichtigsten, in der dieser Bug sie am längsten lahmlegte. Kein
  Trading-Risiko in diesem konkreten Vorfall (Markt zu, `account="demo"` strukturell
  gesperrt), aber ein struktureller Blind Spot im Shutdown-Pfad, der bei einer echten
  Not-Aus-Situation (z. B. ein Freitagabend-Fehlverhalten) real ~63h Wirkungslosigkeit
  bedeutet hätte.
- **Parallel-Login-Risiko geprüft (Nikinger-Auflage):** `kill -9` überspringt
  `shutdown()` (finaler Reconcile + `broker.disconnect()`). Laut
  `phase1_broker_wrapper/lightstreamer_integration_notes.md` ("Parallel-login auth
  trap") sind IG-Session-Tokens **nur In-Memory** (kein On-Disk-Session-File) — kein
  Reboot nötig, die Session heilt sich beim nächsten **solo** `connect()` selbst.
  `ps aux` nach dem Kill bestätigt: **kein** zweiter `scheduler.run`-/IG-Login-Prozess
  aktiv — kein aktuelles Parallel-Login-Risiko. Ein Restart sollte trotzdem, wie immer,
  **sequenziell** erfolgen (nicht parallel zu einem laufenden Live-/Diagnose-Skript).
- **KILL-Datei bewusst NICHT gelöscht** — sie ist der sticky, operator-gesetzte Halt
  (`manual:dashboard`, 2026-07-11 07:32 UTC) und bleibt bis der Nikinger den Bot bewusst
  neu startet (`clear_kill` ist ein Operator-Schritt, keiner, den diese Session
  eigenmächtig zieht).

### Verifiziert
- `pytest phase8_scheduler/tests -q` → **217 passed** (unverändert — ein Test verschärft,
  keiner hinzugefügt/entfernt).
- Volle Cross-Phase-Regression unverändert grün gegen die Phase-10-Step-1-Baseline: P1 87
  · P2 76 · P3 100 · P4 148 · P5 154 · P6 70 · P7 133 · P9 72 · meta_m1_harness 28 ·
  root 77 (Summe unverändert 1162 + P8 217).
- `ps aux` nach dem Kill: kein `scheduler.run`-Prozess mehr aktiv, keine verwaisten
  IG-Login-Prozesse.

### Next
- **Operator (Nikinger):** Restart des Schedulers ist ein bewusster, separater Schritt
  (KILL-Datei erst löschen, dann `python -m scheduler.run …`) — nicht Teil dieser
  Session. Bis dahin steht der Bot (Markt ohnehin am Wochenende zu).
- Advisor-Tool war diese Session **nicht erreichbar** (ein Aufruf, sofortiger Fehler,
  keine weiteren Details in der Tool-Antwort) — exakte Fehlermeldung geht an den
  Nikinger zur eigenen Recherche (s. Chat-Antwort dieser Session), kein Repo-Fix hier.
- Zurück zu Phase 10 V3 Block A (Migration 005 etc., s. `## Session stopped —
  2026-07-10` in `../phase10_v3/CLAUDE.md`) — dieser Hotfix war ein Zwischenstopp, keine
  Änderung am Phase-10-Plan.

### Offene Punkte / blockers
- Keine technischen. Eine Operator-Entscheidung offen: wann der Scheduler wieder
  gestartet wird (kein Blocker für die Phase-10-Arbeit selbst).

---


> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
