---
status: archive
purpose: Verbatim archive of the Phase 1-14 sections rotated out of `ROADMAP.md` — Phases 1-8 on 2026-08-31 (Phase-15-A-5) + Phases 9-14 on 2026-10-19 (Phase-17-A-3). Phase 9 bleibt formell offen (Code produktiv seit 2026-07-06, kein formaler Closeout — Nikinger §10 des Phase-17-Plans); Phase 11 ist 🛑 DEFERRED; Phase 10/12/13/14 sind ✅. Full per-phase details live here; ROADMAP.md keeps only the compact summary + this link.
read-when: auditing historical phase-1-8 decisions — never at session start
detail: L3
up: ./ROADMAP.md
updated: 2026-10-19 (+ Phasen 9–14 rotiert, Phase-17 A-3) | 2026-08-31
---
# ROADMAP_ARCHIVE.md — Phases 1–8 (Closed, Live-verified)

> **Warum diese Datei existiert:** seit 2026-07-03 sind alle Phasen 1–8 abgeschlossen und
> live-verifiziert. Mit Phase 15 Block A Step **A-5** (2026-08-31) wurden die ausführlichen
> Per-Phase-Beschreibungen **verbatim** aus `ROADMAP.md` hierhin rotiert (analog zur
> `SESSIONS_ARCHIVE.md`-Regel aus `CLAUDE.md`). ROADMAP.md trägt jetzt nur noch eine
> kompakte Summary-Tabelle + diesen Link.
>
> **Auditability:** die Inhalte sind **wortgleich, unverändert** — dieselbe Regel wie bei
> `docs/sessions/root_claude_md_phase_status_archive.md` (kein Umschreiben, nur Verschiebung).
> Bei Phasen-1-8-Closeout-Re-Reviews den Stand auf `ROADMAP.md` vor 2026-08-31 (~Commit
> vor A-5) rekonstruieren — der relevante `ROADMAP.md`-HEAD ist in der A-5-Session-
> Commit-Message verlinkt.

---

## Phase 1 — Broker API Wrapper ✅ Abgeschlossen (live-verifiziert, Demo)

**Goal:** A unified Python interface that talks to any supported broker
and emits standard envelopes. Live-tested against IG Demo.

- [x] Concept document
- [x] `broker_wrapper/` module with adapter ABC + IG REST implementation
- [x] Envelope JSON contract
- [x] Credentials via OS keyring
- [x] CLI for standalone testing
- [x] Polling stream client (fallback)
- [x] **Smoke test against live IG Demo account** (PASS inkl. `--order`)
- [x] Lightstreamer streaming client (offizielles SDK, `PRICE`-Feed, CONOK/SUBOK + Live-Ticks 2026-05-21)
- [x] Verify trade-history parsing *(Phase 7 P&L-Resolver: in der Praxis gepivotet — IG-Demo bucht
  History erst nach Settlement, daher ist die **Close-Deal-Confirmation** die primäre lag-freie
  P&L-Quelle; `get_trade_history` bleibt heuristischer Fallback)*

**Done when:** `python scripts/smoke_test.py --order` succeeds end-to-end
against the demo account. ✅ — 2026-05-21. Confirmed epic
`IX.D.DAX.IFMM.IP` (Deutschland 40 Kassa, 1 €/Punkt, EUR, min_deal_size 0.5).

> ⚠ IG Europe GmbH Live-Account noch ausstehend (vor Production-Go-Live kritisch).

**Directory:** [`phase1_broker_wrapper/`](./phase1_broker_wrapper/)
**Concept:** [`docs/concepts/phase1_broker_api_konzept.md`](./docs/concepts/phase1_broker_api_konzept.md)

---

## Phase 2 — Persistenz (SQLite + JSON) ✅ Abgeschlossen (live-verifiziert)

**Goal:** Data layer for the rest of the bot. No business logic, just storage.

- [x] SQLite schema: `trade_lessons`, `trade_outcomes`, `reward_pts`, `ig_config_state`
  (+ V2 `market_regime_snapshots`, `decision_context` as empty placeholders)
- [x] JSON state files: `ig_state.json`, `ig_config.json`, `turbo_candidates.json`
- [x] TTL handling for `turbo_candidates.json` (30 min)
- [x] Migrations / schema versioning (`001_initial.sql`)
- [x] Reader/writer abstractions (`db.py`, `state.py`)

**Done when:** All schemas exist, can read/write/migrate. ✅ 59 unit tests green +
live-verified via `scripts/live_test.py` (durability, TTL, Phase-1 integration) — 2026-05-22.

> Note: Die Prozess-Spalten in `reward_pts` existieren bereits → Phase 7 braucht für
> prozess-bewusstes Scoring **keine** Migration; nur `initial_risk`/`r_multiple`/`account`
> kommen additiv in `002` dazu.

**Directory:** [`phase2_persistence/`](./phase2_persistence/)
**Concept:** [`docs/concepts/phase2_persistence_konzept.md`](./docs/concepts/phase2_persistence_konzept.md)

---

## Phase 3 — External Data (yFinance) ✅ Abgeschlossen (live-verifiziert)

**Goal:** Market data outside the broker (drift, long-term history, brain context). Pure code, no AI.

- [x] yFinance wrapper (rate-limited, cached)
- [x] 30-day price history retrieval
- [x] High/low distance calculation
- [x] Volume anomaly detection (z-score; ETF-Proxy `EXS1.DE`, da `^GDAXI` kein Volume hat)
- [x] Drift calculation (`today_open vs. now %`)
- [x] Momentum (Kontext-Signal) + `get_brain_context` + `TickerMapper` (IG-Epic → yFinance-Symbol)

**Done when:** Given any DAX-related ticker, can return drift, history, and anomaly flags reliably.
✅ 70 unit tests green + live-verified (`RESULT: 6/6 passed` gegen reales `^GDAXI`) — 2026-06-02.

> ⚠ **Phase-5/7-Flag:** `get_momentum()` ist ~15 min verzögert — ein **Kontext-Signal**, KEIN
> harter Momentum-VETO (der sitzt in Phase 5 an IG-Echtzeit-Bars `get_ohlcv`).

**Directory:** [`phase3_external_data/`](./phase3_external_data/)
**Concept:** [`docs/concepts/phase3_external_data_konzept.md`](./docs/concepts/phase3_external_data_konzept.md)

---

## Phase 4 — research.py + LLM Kandidaten ✅ Abgeschlossen (live-getestet)

> Legacy-Benennung: das Modul hieß im Konzept-Erbe `turbo_research.py`; es heißt jetzt
> `research.py` (Klasse `Research`). Output-Datei `turbo_candidates.json` behält ihren
> **Legacy-Namen** (Phase-2/Phase-5-Gate-2-Contract). DAX-**CFDs**, keine Optionen/Turbos.

**Goal:** LLM picks one candidate per session based on code-prepared data. AI's first appearance.

- [x] Session health check
- [x] LLM pick underlyings (drift, last 8 trades, brain lessons, score)
- [x] Probe epics by allowlist (uses broker_wrapper)
- [x] Candidate filter (CFD-Filter: Spread, Drift-Eignung, Score-Coupling; confidence-Floor)
- [x] Save to `turbo_candidates.json`
- [x] Code-side validation of LLM output (`validator.py` = Halluzinations-Guard)

**Done when:** Running `research.py` produces a valid `turbo_candidates.json`. ✅ 88 unit tests
green + live-getestet (`RESULT: 3/3 passed`, IG Demo + realer LLM-Call) — 2026-06-09.

> ⚠ Live-getestet ≠ profit-validiert. Pipeline-**Logik** läuft korrekt end-to-end; keine echten
> Trades platziert/ausgewertet.
> ℹ **v1.5-Relevanz:** `epic_allowlist` (Default 1 Epic) + der Sub-50-Doppel-Clamp
> (long-bias + Confidence-Floor) sind die Hauptursachen für den Near-Constant-Abstain →
> siehe `phase8_scheduler/PHASE8_V1.5_HOTFIX_HANDOVER.md`.

**Directory:** [`phase4_research/`](./phase4_research/)
**Concept:** [`docs/concepts/phase4_research_plan_konzept.md`](./docs/concepts/phase4_research_plan_konzept.md)

---

## Phase 5 — ig_bot.py Gates 1–5 + pre_trade ✅ Abgeschlossen (live-verifiziert)

**Goal:** First end-to-end execution path. Manual trigger only, no scheduler yet.

- [x] Gate 1: Time Window check (09:30–11:19 CET)
- [x] Gate 2: Load Candidates (lazy-calls Phase 4 if missing)
- [x] Gate 3: Constraints (budget, concurrent positions)
- [x] Gate 4: Broker sizing (**risk-per-trade ÷ stop-distance**)
- [x] Gate 5: Direction Consistency (`gate_direction_consistency` — pass-through, no FLIP)
- [x] `pre_trade_check()` — 4 VETOs (status/window, spread, momentum via `get_ohlcv` IG-Echtzeit, position conflict)
- [x] Place order via broker_wrapper (write-ahead `deal_reference`, PENDING fail-closed)
- [x] Monitor position (polling, time-stop close) + Close + Startup reconcile

**Done when:** Manually triggering `ig_bot.py` against IG Demo opens and closes a trade through all
gates. ✅ live-verified (`live_test.py`: echte SELL-Order → time-stop-close, `RESULT: 4/4 passed`)
— 2026-06-12. ⚠ Live-verified ≠ profit-validated (edge ist Phase 7 + Live-Betrieb).

> ℹ Test-Count nach P6+P7: **146** grüne P5-Unit-Tests (P7-Abschluss 2026-06-26:
> P1 52 · P2 62 · P4 94 · P5 146 · P6 70 · P7 128). **Die 4 VETOs (`execution/vetos.py`) sind
> unantastbar — kein v1.5-Knob darf sie berühren.**

**Directory:** [`phase5_execution/`](./phase5_execution/)
**Concept:** [`docs/concepts/phase5_concept.md`](./docs/concepts/phase5_concept.md)

---

## Phase 6 — Bull/Bear/Judge Debate ✅ Abgeschlossen (live-verifiziert)

**Goal:** Replace the simple direction decision with an adversarial early-stop debate.

> **AI boundary:** AI is used **only** for Bull/Bear arguments + Judge synthesis. Context assembly,
> budget/caps, persistence, fail-closed handling are deterministic code. The debate **never** sees
> the broker or any VETO/Gate function.

- [x] Bull/Bear = **Haiku 4.5** (`claude-haiku-4-5-20251001`), Judge = **Sonnet 4.6** (`claude-sonnet-4-6`), config-overridable
- [x] Early-stop (`max_rounds=5`) + hard caps (calls / cumulative tokens / wall-clock) → any breach → **ABSTAIN**
- [x] Judge is the **direction source** — may flip the Phase-4 seed BUY↔SELL; `decision ∈ {TRADE, ABSTAIN}`; `confidence` advisory, gates nothing
- [x] Caching + extended 8-field token-meter
- [x] Forward-compatible JSON audit `debate_log.json`
- [x] Seam: `debate_runner` injected **between Gate 2 and Gate 3**; default passthrough keeps Phase 5 AI-free

**Done when:** Debate runs reliably; every error/cap-breach → fail-closed ABSTAIN → NO_TRADE.
✅ Done + live-verified 2026-06-16 (`main = 49cda8a`; one Demo cycle: 3 real calls → ABSTAIN → NO_TRADE).
⚠ Live-verified ≠ profit-validated.

> **Caching-Realität:** Haiku cacht erst ab 4096-Token-Präfix → Bull/Bear (~850–1040 Tokens) cachen
> nie; nur der Judge schreibt Cache; Cache-Reads nur bei `rounds_used >= 2`.
> ℹ **v1.5-Relevanz:** Die Debatte ist der **bereits gebaute Differentiator** — sie kann die
> Richtung flippen, läuft aber nur auf einem *erzeugten* Kandidaten. Loosening des P4-Gates lässt
> die Debatte die nuancierte Arbeit tun (v1.5 Block B).

**Directory:** [`phase6_debate/`](./phase6_debate/)
**Concept:** [`docs/concepts/phase6_debate_concept.md`](./docs/concepts/phase6_debate_concept.md)

---

## Phase 7 — Reward/Brain ✅ Abgeschlossen + live-verifiziert (2026-06-26, gepusht)

> **Scope-Lock (lean model):** Phase 7 = **Reward-Score** (`reward_pts`, prozess-bewusst) +
> **free-text Lessons** (`trade_lessons`) + **observe-only outcome-anchored Confidence**.
> **Keine VETO-Berührung.** Die volle **Instinct→VETO-Promotion (ECC)** ist **Phase 9f**, gegatet
> auf reale Outcomes.

**Goal:** Der Feedback-Loop schließt — aus realen Trade-Ergebnissen werden Score + Lessons, die in
spätere Research-Zyklen zurückfließen.

- [x] `RewardSink` write-seam (`on_trade_opened`/`on_trade_closed`), default `None` → Phase 5 bit-identisch
- [x] Prozess-bewusster Reward-Score (`reward_pts`: outcome + process Δ, clamped [0,100], per-trade `|Δ|` capped) → `score_after`
- [x] Score → risk_level unverändert (binäres `get_risk_level`, Schwelle 50)
- [x] Outcome-anchored Confidence `f(Wilson-LB(win_rate), expectancy_R, SQN, N)`, `N_min=10` → INSUFFICIENT; **observe-only, gatet nichts**
- [x] `reflect()` nach jedem Close — ein Haiku-Call, best-effort, vom Close-Critical-Path entkoppelt → `trade_lessons`
- [x] Lessons-Loop-Closure: Research-Prompt injiziert `get_recent_lessons`; `mark_lesson_used`
- [x] **P&L-Pivot:** realisierter P&L + `close_level` reisen **lag-frei aus der Close-Confirmation** mit; `get_trade_history` nur Fallback. Migration `002` = `initial_risk`/`r_multiple`/`account`
- [x] Synthetik/Echt-Trennung (harte DB-Pfad-Grenze + `SyntheticSafetyError`); `include_demo_in_edge=True` (Bootstrap, vor Go-Live re-baselinen)

**Done when:** `pytest phase7_reward/tests/` grün. ✅ **128 P7-Unit-Tests**; Regression
**P1 52 · P2 62 · P4 94 · P5 146 · P6 70** grün; `live_test.py` **5/5** gegen IG Demo. ⚠
live-verifiziert ≠ profit-validiert (erst **ein** Trade; Edge-Metrik läuft bei `score=50`/`INSUFFICIENT`).

> ℹ **v1.5-Relevanz:** Die bisherigen Lessons stammen aus **Verifikations-Trades** und fließen
> ungefiltert in den Research-Prompt → v1.5 Block A (Lesson-Provenance-Quarantäne).

**Directory:** `phase7_reward/` *(package `reward`)*
**Concept:** [`docs/concepts/phase7_reward_concept.md`](./docs/concepts/phase7_reward_concept.md) · **Kickoff:** ~~PHASE7_KICKOFF_HANDOVER.md~~ *(Link korrigiert 2026-07-06: Datei existierte nie im Repo — nur Browser-Session-Artefakt)*

---

## Phase 8 — Scheduler ✅ live-verifiziert (2026-07-03) — zwei autonome Trades + ein auslösender Safety-Breaker (Token-Budget) live bewiesen

> **Mission (zuerst lesen):** „Scheduler" ist nur der Name — das Ziel ist **autonome,
> unbeaufsichtigte Erzeugung realer Demo-Trades**, weil alles nach P8 (Confidence aus
> `INSUFFICIENT`, P9-Instinct-Promotion) auf **reale Outcomes** gegatet ist. Der harte Pfad ist
> **autonome Kandidaten-Generierung** via echtes Phase-4-Research (nie der manuelle Seed).
> **Kein neues AI** — ein Scheduler ist reine Mechanik; AI bleibt bei P4-Pick / P6-Debatte /
> P7-Lesson. Build-Reihenfolge bindend: **Cleanup → Verify → autonome Kandidaten →
> Auto-Confirm/Safety → Reconcile → Loop/Daemon → (zuletzt) Web-UI**; unter Druck fällt die UI,
> nie die Safety.

**Goal:** Ein langlaufender Daemon, der aufwacht, recherchiert, im Fenster tradet, reconcilet und
schläft — und so die ersten realen Outcome-Daten sammelt.

- [x] Pre-Steps: Step 0 (Legacy-grep — clean), Step 0b (Docs), Step 1 (Contract-Verify), Step 2 (Scaffold `phase8_scheduler/`, pkg `scheduler`)
- [x] `clock.py` — Marktzeiten-Phasen (reuse `is_market_open` + Gate-1-Fenster), injizierbares `now_fn`/`sleep_fn`
- [x] `state.py` — `scheduler_state.json` (Trade-Count, Tages-Loss, Backoff, Kill-Reason), Europe/Berlin-Rollover
- [x] `safety.py` — Auto-Confirm `confirm_fn` (demo-only fail-closed + Caps + Loss-Breaker + Budget)
- [x] `killswitch.py` — file-based KILL (UI-unabhängig); `command.py` — UI-/P10-Command-Pfad; `backoff.py` — Consecutive-Failure-Trip; `budget.py` — Token-Budget (default scharf, 200k ≈ €0.8/Tag)
- [x] `research_tick.py` — autonome Kandidaten (echtes P4-Research, nie der Seed; `no_trade_reason`-Skelett)
- [x] `reconcile.py` — idempotenter `CLOSED_BY_BROKER`-P&L-Catch-up
- [x] `runner.py` — die Loop/Daemon + fail-closed Keyring-Preflight + graceful shutdown
- [x] `scripts/` — wiring (voller P1–P7-Stack), `run.py` entry, `run_scheduler.sh`, smoke_test, live_test
- [x] Web-UI (`webui/`, FastAPI read-mostly + statisches Dashboard) — **zuletzt gebaut**

**Status (ehrlich):** Alle 12 Module gebaut, **199 Unit-Tests grün**, v1.5+v1.6+v1.7 gemergt nach
`main` (2026-07-02). ✅ **Bewiesen** (Operator-Runs + Mocks): Daemon-Lifecycle (preflight →
bounded loop → clean shutdown), State-Persistenz, autonomes **echtes** P4-Research mit korrektem
Fail-Safe-Abstain, reconcile+reward auf realen Demo-Trades, scharfes Token-Budget, read-only
Web-UI, **ein netto-neuer autonomer Trade open *und* close in einem sauberen Lauf** (2026-07-02,
DAX BUY `DIAAAAXW7U4AWAP`) — **und jetzt (2026-07-03, Nikinger-bestätigt) beide zuletzt offenen
Beweis-Punkte der Mission:** ein **zweiter** net-new autonomer open→close, **und** ein Safety-
Breaker, der **tatsächlich auslöst** (das Tages-Token-Budget erschöpfte sich mitten im Live-Lauf
und blockierte weitere Trades — fail-closed, kein Crash, exakt wie designed). ⚠ **Weiterhin außerhalb
des Scopes/nicht Ziel dieses Flips:** Trade-*Qualität*/Konsistenz über viele Zyklen hinweg (Mechanik
ist bewiesen, Edge nicht); Multi-Day-Verhalten im Detail; Edge/Profitabilität (nie im Scope, wird
es auch künftig nicht sein).

**Why der ursprüngliche Gap + die drei Hotfix-Tracks:** der Bot **abstaint** anfangs fast jeden
Zyklus (Single-Instrument-Universum + Sub-50-Doppel-Clamp). **v1.5** (Varietät C + Clamp/Floor B +
echte Lessons A) behob den Hauptblocker — siehe
[`phase8_scheduler/PHASE8_V1.5_HOTFIX_HANDOVER.md`](./phase8_scheduler/PHASE8_V1.5_HOTFIX_HANDOVER.md).
**v1.6** fand + fixte einen zweiten, bis dahin unbemerkten Prompt-Leak-Kanal („Cause A part 2") und
ergänzte Observability + eine Instrument-Verification-Harness — direktes Ergebnis noch am selben
Tag: **der erste echte autonome Trade**. **v1.7** fixte eine kleine webui-only Anzeige-
Inkonsistenz, die der lange Trade-Lebenszyklus (~9 min IG-Settlement-Lag) erstmals sichtbar
machte (kein Sicherheitsproblem). Das ursprüngliche „Done when" (live net-new autonomer
open→close + demonstrierbarer Breaker-Trip) ist damit **vollständig erreicht** (2026-07-03) — ein
zweiter net-new open→close **und** ein tatsächlich auslösender Breaker (Token-Budget) liegen jetzt
beide vor. Fortlaufende Trade-Qualitäts-Datensammlung bleibt ein informatives Nebenprodukt des
weiterlaufenden Betriebs, ist aber **nicht** Bedingung dieses ✅-Flips (der deckt Mechanik, nicht Edge).

> **✅ v1.6/v1.7/Live-Beweis-Stand (2026-07-03, ehrlich):** `^FCHI`/`^IBEX` liefern weiterhin
> intermittierend keine Kursdaten (*„possibly delisted"*, vermutlich Yahoo-Rate-Limiting) —
> **toleriert** (Version-Pin korrigiert, per-Zyklus-Observability macht Degradation sichtbar),
> nicht gefixt oder gedroppt (kein Hard-Crash, kein VETO betroffen — Momentum-VETO nutzt
> IG-Echtzeit-Bars, nicht yFinance); Aufnahme in den V2-Reframe-Vorschlag (siehe Pointer unten).
> `webui/api.py`s `/api/status` liest `trades_today`/`realized_pnl_today` seit v1.7 aus der DB statt
> einem lagging State-Snapshot. **Der weiterlaufende Live-Test lieferte den zweiten net-new
> autonomen open→close UND Step 5b (Breaker-Fire): das Tages-Token-Budget erschöpfte sich
> mitten im Lauf und blockierte weitere Trades — fail-closed, kein Crash.** Beide zuletzt offenen
> Beweis-Punkte der Phase-8-Mission sind damit geschlossen (Nikinger-bestätigt, 2026-07-03). Details:
> [`phase8_scheduler/CLAUDE.md`](./phase8_scheduler/CLAUDE.md) (Session-Journal, aktuellster
> Stand), [`phase8_scheduler/PHASE8_V1.6_HANDOVER.md`](./phase8_scheduler/PHASE8_V1.6_HANDOVER.md),
> [`docs/concepts/phase8_v1.6_hotfix_plan.md`](./docs/concepts/phase8_v1.6_hotfix_plan.md),
> [`docs/concepts/phase8_v1.7_hotfix_plan.md`](./docs/concepts/phase8_v1.7_hotfix_plan.md).

**Directory:** [`phase8_scheduler/`](./phase8_scheduler/) *(pkg `scheduler` + `webui`)*
**Concept:** [`docs/concepts/phase8_scheduler_concept.md`](./docs/concepts/phase8_scheduler_concept.md)

> 📌 **2026-07-03:** [`phase8_scheduler/PHASE8_CLOSEOUT_HANDOVER.md`](./phase8_scheduler/PHASE8_CLOSEOUT_HANDOVER.md)
> closes out Phase 8 (written before the ✅ flip above landed; still the fuller writeup of the
> v1.5–v1.7 arc) and proposed reframing the old Phase 9 into V2 (autonomous epic research +
> reliable lightstreamer/yfinance data-input) → V3 (DB reform + no-trade lessons + UI) → V4 (the
> old 9a–9f, deferred). **The reshape below applies that proposal** — done as the initial
> housekeeping step of the V2 track (2026-07-03), per a detailed execution plan from a browser
> planning session: [`docs/concepts/phase9_v2_foundation_plan(1).md`](./docs/concepts/phase9_v2_foundation_plan(1).md).

---

## Phase 9 — V2: Foundation (Autonome Epic-Research + Daten-Input-Zuverlässigkeit)

> **Status: in Arbeit (Stand 2026-07-07; gekürzt 2026-09-05, Phase-16-Plan-Session — Wortlaut
> bis dahin in `git log -p ROADMAP.md`).** Steps 1–6 + 7a gebaut (7b ohne Fix-Target);
> Live-Baseline-Lauf seit 2026-07-06, Tag 1 end-to-end bewiesen, erster DB-Universum-Pick (CAC).
> Offen: V2-Baseline-Auswertung (echter `open→close`-Trade unter V2 + Variety-These) — seit
> 2026-07-02 acht autonome Trades (id 4–11 CLOSED, davon 4 seit 08-25) und damit faktisch erbracht; `--enable-ig-bars`
> durch Phase-12 `enable_bar_service` abgelöst. Handover:
> [`phase9_universe/PHASE9_V2_LIVE_RESULTS_HANDOVER.md`](./phase9_universe/PHASE9_V2_LIVE_RESULTS_HANDOVER.md) ·
> Plan: [`docs/concepts/phase9_v2_foundation_plan(1).md`](./docs/concepts/phase9_v2_foundation_plan(1).md) ·
> Phase-Head: [`phase9_universe/CLAUDE.md`](./phase9_universe/CLAUDE.md).

**Goal:** die zwei strukturellen Lücken schließen, die den gesamten v1.5→v1.7-Hotfix-Arc
getrieben haben — bevor weitere sophisticated-AI-Arbeit (die alte Phase 9, jetzt Phase 15/V4)
auf einem unzuverlässigen Datenfundament aufbaut.

> **Korrektur (2026-07-08, M1-Housekeeping):** die Checkliste unten stand noch auf `[ ]`,
> obwohl der Status-Block oben + `phase9_universe/CLAUDE.md`s Kontrakt-Tabelle Steps 1–6 + 7a
> längst als ✅ führen — gegen den Code verifiziert (`universe/{discovery,pricing,promotion,
> store,models}.py` existieren, `phase2_persistence/migrations/004_phase9_instrument_universe.sql`
> existiert). Getestetes Verhalten schlägt Doku-Prosa (Working-style-Regel); Boxen unten korrigiert.

### 9a — Autonome Epic-Research (discover → validate → promote)
- [x] `discovery.py` — Seed-Suchbegriff-Sweep + IG `search_markets` + Code-Filter (EUR, Index-CFD,
  TRADEABLE, Kassa-Variante, min size) — kein LLM
- [x] `pricing.py` — deterministischer `point_value`-Resolver (IG-Felder + Namens-/lot_size-Kreuzcheck)
- [x] `promotion.py` — Statusmaschine `discovered → verified → active` voll autonom auf Demo;
  Auto-Demotion (`active → quarantined`) bei wiederholten IG-Verify-Fails
- [x] Migration 004 (`instrument_universe`) + `UniverseStore`; `EXTENDED_UNIVERSE` wird einmaliger
  Seed (`source="curated"`)
- [x] P4 liest das aktive DB-Universum; P8-Runner bekommt eine Universe-Refresh-Naht

### 9b — Daten-Input-Zuverlässigkeit
- [x] `BarProvider`-Kette IG→yFinance + yFinance-Härtung (Backoff, Circuit-Breaker)
- [x] Deterministischer Divergenz-Check (IG-Bar-Close vs. yFinance-Last), gated nichts
- [x] Lightstreamer-Multi-Epic-Diagnose (7a, live 2026-07-06) — **NEGATIV-Befund**, kein Bug,
  kein Fix-Target (7b unblocked-aber-leer)
- [ ] ~~`LiveQuoteCache` in den P4-Research-Kontext verdrahtet~~ — *gegenstandslos (korrigiert
  2026-09-05, Phase 16 A-3): `LiveQuoteCache` existiert nicht im Repo (0 Treffer);
  der Bedarf ist durch Phase-12-`BarService.get_window` + Phase-13 LS-Tick-Aggregation
  strukturell abgelöst*

**Leitplanke:** kein neues AI im Daten-/Universum-Layer (Discovery-/Promotion-Kriterien sind
100 % code-evaluiert); VETOs/Gates unangetastet; demo-only fail-closed.

**Done when:** mindestens ein net-new Epic durchläuft `discovered → verified → active` ohne
manuellen Code-Edit und erscheint im nächsten Research-Zyklus; ein Safety-Breaker feuert live
(carried-over 5b aus dem v1.5-Plan); STXE/CAC/IBEX-`point_value` wird per Code bestätigt oder
ehrlich quarantänisiert.

**Directory:** `phase9_universe/` *(pkg `universe`)*
**Plan:** [`docs/concepts/phase9_v2_foundation_plan(1).md`](./docs/concepts/phase9_v2_foundation_plan(1).md)

---

## Phase 10 — V3: Persistenz-Reform + No-Trade-Lessons + (optionales) UI

> **Status: ✅ abgeschlossen (Closeout 2026-08-25) — Block A ✅ live auf main seit WE 1
> (2026-07-11, Montag-Restart-Beweis 2026-07-14) + Block B ✅ live auf main seit WE 2
> (2026-07-17) + Bugfix-Block 2026-07-25/31/08-08 + H1 (1 Woche gelaufen) + H4-a.**
> **Council-Paper-Call ✅ gebaut, default `False`, bis auf weiteres in mind Phase 15**
> (Nikinger 2026-08-25). Phase-11-Inhalte (WI-2/W2, H3/H5/H7, B3-Margin-Headroom) bleiben
> offen und gehören in den Datenfundament-Track (Phase 12/13/14) — dort dokumentiert,
> nicht hier. Ausführungsreifer Plan lag
> vor: [`docs/concepts/phase10_v3_plan.md`](./docs/concepts/phase10_v3_plan.md) (Decisions
> V3-D1…D10, Steps 0–11); Kickoff-Kontext:
> [`docs/concepts/PHASE10_V3_KICKOFF_HANDOVER.md`](./docs/concepts/PHASE10_V3_KICKOFF_HANDOVER.md).
> Phase head: [`phase10_v3/CLAUDE.md`](./phase10_v3/CLAUDE.md). Block C (UI) ist explizit
> **nicht** Teil dieses Plans (geparkt, Plan §13) — Abschnitt 10c unten bleibt daher offen.
> ⚠ **2026-07-17 Doku-Fix (code = source of truth):** die 10a/10b-Bullets unten waren seit der
> ursprünglichen Phase-9-Formulierung nicht mehr aktualisiert worden — as-built ist stärker
> (echte `abstain_records`-Taxonomie mit 12 Reasons statt nur der 3 genannten, + eine
> Both-Sides-Shadow-Paper-Pipeline, die im ursprünglichen Text gar nicht vorkam). Bullets unten
> auf den echten Baustand geflippt.

**Goal:** die aktuellen SQLite-V2-Erweiterungen bauen + „warum tradet der Bot nicht" zu einem
lernbaren Signal machen, nicht nur einem verworfenen Reason-Code.

### 10a — SQLite V2 Extensions
- [x] `+ market_regime_snapshots` — Migration 005 (epic-scoped, DROP+CREATE über den
  FK-inkompatiblen P2-Platzhalter), Writer live seit Block B (`market_context/writer.py`);
  observe-only `regime_tag`, degradiert auf `data_source="quote_only"` ohne Bars
- [x] `+ decision_context` — Migration 005, Writer live seit Block B; Bull/Bear-Summary aus
  `DebateOutcome.transcript`, Outcome ∈ `{TRADE, NO_TRADE, ABORT}`
- [ ] `+ lesson_embeddings` (vector store, semantic similarity) — optional/später, V4+

### 10b — No-Trade (Abstain) Lessons
- [x] Eigene `abstain_records`-Tabelle + 12-Reason-Taxonomie (`AbstainReason`,
  `classify_abstain`) — geht über die ursprünglich skizzierten 3 P8-`research_tick`-Reasons
  hinaus (Migration 005, live seit Block A, 318+ reale Zeilen Stand 2026-07-17)
- [x] `reflect_abstain()` (P10, Haiku, best-effort, Tages-Cap) auf `REASON_DEBATE_ABSTAIN`
  erweitert (nicht `reward.brain.reflect()` selbst — eigene, schlankere P10-Reflect-Funktion,
  gleiches Reuse-Muster wie P7); Lessons-Rückspeisung in den P4-Prompt liegt **gebaut, aber
  dunkel** (S6, `include_abstain_lessons=False`, V3-D3 — Aktivierung ist ein separater
  Operator-Schritt nach Lesson-Review, nicht Teil von V3)
- [x] **Zusätzlich (nicht ursprünglich geplant):** Both-Sides-Shadow-Paper-Pipeline
  (`PaperEngine`/`PaperTradeTracker`) — beantwortet "war der Abstain richtig?" für
  `REASON_DEBATE_ABSTAIN`-Fälle deterministisch, ohne Order/Broker-Touch. Council-Paper-Call
  (LLM-Forced-Pick-Variante, `PaperDebateCaller` + additiver Judge-Prompt-Sibling in
  `phase6_debate/`) **✅ gebaut (2026-07-17, Folge-Session)**, hinter Flag
  `enable_paper_debate` (default `False`) — Nikinger flippt, wann gewünscht.

### 10c — UI-Erweiterungen (optional, niedrigere Priorität als 10a/10b)
- [ ] Aufbauend auf dem v1.6-Observability-Log + dem v1.7-DB-gespeisten Status

**Done when:** Abstain-Zyklen erzeugen genauso Lessons wie geschlossene Trades; `decision_context`/
`market_regime_snapshots` sind befüllt statt leer. **Erreicht (2026-07-17)** — live Rows folgen
mit dem nächsten Scheduler-Restart (Nikinger).

**📕 Closeout 2026-08-25:** Phase 10 ist abgeschlossen. Council-Paper-Call-Implementation
bleibt im Code (default `False`) als Eingangs-Schnittstelle für Phase 15 (V4 — Council für
Live-Trades + Handover + Reward-Reform). Vollständiger Handover:
[`phase10_v3/PHASE10_CLOSEOUT_HANDOVER.md`](./phase10_v3/PHASE10_CLOSEOUT_HANDOVER.md),
Bild: [`docs/architecture/phase10_v3.svg`](./docs/architecture/phase10_v3.svg).

**Directory:** [`phase10_v3/`](./phase10_v3/)

---

## Phase 11 — V3-Fortsetzung: Funnel-/Mess-Fixes *(aus der zweiten Datenwoche-Review)*

> **Status: 🛑 DEFERRED seit 2026-08-11 (Notbremse, Nikinger-Entscheidung).** B1/B2/B4/B5 sowie
> H1 und H4-a sind gebaut und liegen auf `main`; **WI-2/W2 — die eine Frage, für die es diese
> Phase gibt — bleibt unbeantwortet.** Drei Datenwochen sind an drei unterschiedlichen
> Infrastruktur-Ausfällen gescheitert, nie an der Messung. Die gemeinsame Wurzel ist wichtiger
> als diese Phase: das **Datenfundament**. Nichts wird zurückgerollt; „deferred" heißt keine
> weitere H-Serie, kein Paper-Trade-Ausbau, kein H1-Scharfschalten, bis das Fundament steht.
> Vollständige Begründung, Durability-Anforderungen (A–G) und offene Entscheidungen:
> [`phase10_v3/PHASE11_DEFERRAL_HANDOVER.md`](./phase10_v3/PHASE11_DEFERRAL_HANDOVER.md),
> Bild: [`docs/architecture/data_foundation.svg`](./docs/architecture/data_foundation.svg).
> **Nummerierung final (Nikinger-Entscheidung 2026-08-11):** „Phase 12 = Datenfundament, V4 →
> Phase 13" (Handover §4.1, ausgeführt in [`docs/concepts/phase12_data_foundation_plan.md`](./docs/concepts/phase12_data_foundation_plan.md) D2).
> Der neue Datenfundament-Track lebt als eigene Phase 12 direkt unter dieser (s. u.); V4 ist
> jetzt **Phase 13** (weiter unten), unverändert im Inhalt, zusätzlich gegatet auf ein
> bestandenes Phase-12-PASS (dieselbe Logik wie diese Notbremse: keine weitere
> AI-Sophistication-Arbeit auf einem unzuverlässigen Datenfundament).
>
> ⟳ **Korrektur (2026-08-18, Nikinger-Entscheidung):** nach dem Scheitern von P12.5 ist
> **Phase 13 = Live-Datenfundament** (der strukturelle Schnitt + vierstufige Beschaffung,
> s. u.); **V4 rutscht auf Phase 14**. Jede „Phase 13 (V4)"-Nennung in älteren Zeilen meint
> jetzt Phase 14.
>
> ⟳ **Korrektur (2026-08-22, Nikinger-Entscheidung):** die "discovery-then-deterministic"-
> Architektur aus Block C des Phase-13-Re-Plans wird **eigene Phase 14** (s. u.); V4 rutscht
> entsprechend auf **Phase 15**. Jede „Phase 14 (V4)"-Nennung in älteren Zeilen meint jetzt
> **Phase 15**. Plan für die Live-Daten-Beschaffung:
> [`docs/concepts/phase13_live_data_plan.md`](./docs/concepts/phase13_live_data_plan.md).
>
> Numbering claimed 2026-08-01 (Nikinger-Entscheidung)
> — vorher stand hier "Phase 11 = V4"; V4 ist jetzt **Phase 13** (unten), unverändert im Inhalt.
> Diese Phase ist **keine** neue AI-Sophistication-Arbeit, sondern das Fix-/Diagnostik-Ergebnis
> der zweiten V3-Datenwoche: [`phase10_v3/DATA_WEEK_REVIEW_2026-07-31.md`](./phase10_v3/DATA_WEEK_REVIEW_2026-07-31.md)
> §4 (Befunde B1-B5) + §5 (Hypothesen H1-H7). **Directory:** lebt vorerst weiter in
> [`phase10_v3/`](./phase10_v3/) (`abstain_lessons/`, `market_context/`) — keine physische
> Verzeichnis-Verschiebung in dieser Session, das ist eine eigene, größere Entscheidung.

**Goal:** die Research-Funnel-/Mess-Probleme beheben, die die zweite V3-Datenwoche aufgedeckt hat
(366 Zyklen → 1 Kandidat → 0 Trades), bevor an der Richtungslogik selbst weitergearbeitet wird.

### 11a — Bugs aus der Datenwoche-2-Review
- [x] **B1** `point_value`-Drift (40× Oversizing auf AEX) — P8-Sizing-Quelle + P5-Fail-closed-Guard
  gefixt (2026-08-01)
- [x] **B2** Reward-Score-Skala (`debate_confidence` 0-100 statt [0,1]) — Skala gefixt
  (2026-08-01); Residuum (**H3**, `clean_exit_bonus` auf Stop-outs) bewusst offen gelassen
- [x] **B5** Paper-/Abstain-Lesson-Prompt/Validator-Zeichengrenzen-Drift — gefixt (2026-08-01)
- [x] **B4 / H6** leeres Mess-Substrat (`abstain_records.detail`/`spread_pct` nie befüllt) —
  gefixt (2026-08-01): `detail` wird jetzt aus dem Executor durchgereicht (+ die
  `Research.last_no_pick_reasoning`-Anreicherung für den dominanten `research_empty`-Fall in der
  P8-Wiring), `spread_pct` an allen drei `_notify_context`-Call-Sites verdrahtet
- [ ] **B3** Leverage-Cap ohne Margin-Headroom — **NICHT gefixt, Design + Prep dokumentiert**
  für eine eigene, größere Session (P1-Adapter-Feld + P5-Gate-4-Änderung, cross-phase; braucht
  zuerst einen Live-Demo-Call gegen `/markets/{epic}`, um IGs echte Margin-Felder zu bestätigen).
  Details: `phase5_execution/CLAUDE.md` B3-Block.

### 11b — H1-H7 (offene Hypothesen, Reihenfolge H2→H1→H6, danach datengetrieben H7/H4/H3/H5)
- [x] **H2** (B1-Anteil) — gefixt, s. 11a. B3-Anteil bleibt offen.
- [x] **H6** — gefixt, s. 11a (B4).
- [ ] **H1** *(größter Hebel, nächste eigene Session)* — Shadow-Pairs zeitgesteuert statt an
  `REASON_DEBATE_ABSTAIN` gekoppelt (neuer Scheduler-Tick + schlanker `PaperEngine`-Einstieg,
  ~130 Paare/Tag, IG-Allowance-Budget einplanen). Beantwortet WI-2 (Sub-Noise-Geometrie-Frage,
  **H7**) an einem Tag statt in Wochen.
- [ ] **H3** — Reward-Loop-Residuum (`clean_exit_bonus` auf Stop-outs) — Designfrage, nach B2.
- [ ] **H4** — Lesson-Sackgasse aufbrechen (Relevanz-Decay, Doppelzählung Lessons/`recent_trades`
  beenden, Lessons skopieren).
- [ ] **H5** — Nachmittag zurückkaufen (Prompt-Caching für Research, `LLMClient(cache_system=True)`
  existiert bereits, wird von Research nicht genutzt).
- [ ] **H7** — Geometrie-Rahmenfrage (30/45-Punkte-DAX-Stops gewinnbar?) — datengetrieben, wartet
  auf H1s Ergebnis.

**Done when:** B1-B5 entschieden (gefixt oder bewusst dokumentiert-deferred, ✅ erreicht
2026-08-01) UND mindestens H1 gebaut + WI-2 beantwortet.

**Directory:** [`phase10_v3/`](./phase10_v3/) *(vorerst — kein Verzeichnis-Split in dieser Session)*

---

## Phase 12 — Datenfundament (Registry + BarService + Bar-Archiv + Recorder)

> **Status: ✅ abgeschlossen (Closeout 2026-08-25) — Steps 0–8.5 auf `main`, 143 Tests grün
> (Stand 2026-08-25), 18 Phase-12-Commits auf `origin/main`.** **Die strukturelle Antwort
> auf das P12.5-Scheitern steht in Phase 13+14** (Nikinger 2026-08-25): der Auflöse-Pfad
> kauft nie wieder Daten — Phase 13 Block A trennte Beschaffung und Verbrauch, Phase 14
> macht Quellen zur Registry-Zeile. **Phase-12-Beweiswoche wird nicht wieder aufgenommen**;
> die Phase-13-Beweiswoche läuft seit Mo 2026-08-25 separat, gegen die Phase-13-Architektur.
> P12.5 wurde 2026-08-18 formal CLOSED + GESCHEITERT — die fünf Code-Edits (U1/U2/U3/U5 +
> Entscheidung B) bleiben **unabhängig korrekt im Repo**. Notbremse aus Phase 11 (oben):
> die gemeinsame Wurzel war strukturell, nicht messbar — durch Phase 13+14 abgelöst.
> Closeout-Handover: [`phase12_data_foundation/PHASE12_CLOSEOUT_HANDOVER.md`](./phase12_data_foundation/PHASE12_CLOSEOUT_HANDOVER.md),
> Bild: [`docs/architecture/phase12_closeout.svg`](./docs/architecture/phase12_closeout.svg).
> As-Built-Analyse: [`PHASE12_5_CLOSEOUT_HANDOVER.md`](./phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md),
> Sofort-Befund: [`PHASE12_5_FAILURE_HANDOVER.md`](./phase12_data_foundation/PHASE12_5_FAILURE_HANDOVER.md).
> Plan: [`docs/concepts/phase12_data_foundation_plan.md`](./docs/concepts/phase12_data_foundation_plan.md).
>
> **Tag-1-Live-Auswertung (2026-08-17):** die Kette Resolver → Registry → `measurable_universe()`
> → Recorder/BarService → `bars.sqlite` läuft end-to-end im Echtbetrieb (5 `ok`-Epics, 3 typisiert
> `no_intraday_source`, 1891 Bars an einem Tag, IG-Verbrauch erstmals gemessen: 136/10 000 Punkte).
> **Gemessen wurde trotzdem nichts:** der Messarm `enable_shadow_schedule` ist Default `False` und
> im laufenden Prozess nicht gesetzt ⇒ 0 Paper-Zeilen — dieselbe Fehlerklasse wie `enable_ig_bars`,
> diesmal aber an Tag 1 bemerkt. Stand, Befunde und Entscheidungen A–D:
> [`phase12_data_foundation/PHASE12_PREPROOF_HANDOVER.md`](./phase12_data_foundation/PHASE12_PREPROOF_HANDOVER.md),
> Bild dazu: [`docs/architecture/phase12_preproof.svg`](./docs/architecture/phase12_preproof.svg).
>
> **P12.5 (Messarm-Fixes) — formal CLOSED, GESCHEITERT (2026-08-18):** Steps 1–3 fixten U1/U2/U3/
> U5 + Entscheidung B, alle live gegen echte Daten bewiesen korrekt (`pairs_opened: 90`,
> `pairs_resolved: 66`, `resolution_source` erstmals real befüllt). Aber der scharf gestellte
> Messarm exponierte einen fünften, vorher nie aufgerufenen Pfad: `BarService.get_window` fordert
> bei jedem Coverage-Miss das **komplette** Fenster neu an (≈301 IG-Punkte/Top-up) statt nur die
> Lücke — 4731/10 000 Wochenpunkte in ~4 Stunden verbrannt, Requirement F (Soll < 1500/Woche) am
> ersten Tag gerissen. Nikinger-Intervention: Scheduler gestoppt, P12.5 ohne weitere Bauschritte
> geschlossen. Sofort-Befund des Interventionstags:
> [`phase12_data_foundation/PHASE12_5_FAILURE_HANDOVER.md`](./phase12_data_foundation/PHASE12_5_FAILURE_HANDOVER.md).
>
> **Closeout-Analyse (2026-08-18, nachgemessen — korrigiert die obige Root-Cause-Erzählung):**
> Von **1782 bei IG gekauften 1-Min-Bars trugen 1638 (92 %) Zeitstempel, die bereits als
> yFinance-Bar im Archiv lagen** — gekauft wurde für 4515 Punkte fast nur, was ohnehin schon da war.
> Ursache ist nicht U3 (die `and`-Bedingung kurzschließt links, U3s Schwelle wurde nie erreicht),
> sondern `_covers_tail`s Anspruch auf eine ≤ 1 Minute alte Bar gegen yFinances ~15 Minuten
> Eigenverzug: der teure Zweig war der Normalfall, latent seit Step 4, scharf erst durch das
> Einschalten des Messarms. **Empfehlung daher kein weiterer Patch, sondern ein struktureller
> Schnitt** (Auflöse-Pfad kauft nie wieder Daten; die Frage wechselt von „reicht das Archiv bis
> jetzt?" zu „deckt es das Fenster dieses Trades bis `time_stop_utc`?"). Offene Entscheidungen
> (Weg / Label / Wiederanlauf) und der volle As-Built-Stand:
> [`phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md`](./phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md),
> Bild: [`docs/architecture/phase12_5_failure.svg`](./docs/architecture/phase12_5_failure.svg).

**Goal:** eine echte Beweis-Messwoche läuft durch, ohne dass Infrastruktur die Messung tötet.
Instrument-Registry wird die eine Wahrheit (abgeleitetes, code-verifiziertes Symbol-Mapping statt
Deklaration), ein `BarService` wird der eine Bar-Pfad für alle Konsumenten, jede gefetchte Bar
landet in einem eigenen Archiv (`data/bars.sqlite`), ein Recorder-Prozess (yFinance-only) schreibt
kontinuierlich unabhängig vom Bot-Zustand, und ein Mess-Heartbeat lässt einen Ausfalltag am selben
Tag auffallen statt erst Wochen später.

**Done when:** siehe Plan §7 (PASS-Kriterien A–G + Kern). WI-2/W2-Auswertung selbst bleibt
Phase-11-Wiederaufnahme, nicht Teil dieser Phase.

**Directory:** [`phase12_data_foundation/`](./phase12_data_foundation/)

---

## Phase 13 — Live-Datenfundament *(eröffnet 2026-08-18 nach dem Scheitern von P12.5, abgeschlossen 2026-08-31)*

> **Status: ✅ abgeschlossen (Closeout 2026-08-31, Session 18).** Blöcke A + B + C code-complete (Stand 2026-08-22) + Beweiswoche ausgewertet (Mini-Session 23, 2026-08-31) + Pfad-C-Entscheidung (Mini-Session 24, 2026-08-31) + Befund-Inversion. 74 Phase-13-Tests grün, 53 `phase13:`-Commits auf `origin/main`, Σ 1703 grün repo-weit.
> **Plan:** [`docs/concepts/phase13_live_data_plan.md`](./docs/concepts/phase13_live_data_plan.md)
> (gelockte Entscheidungen L1–L17 + L18 Pfad-C-Erweiterung, Blöcke A/B/C, §9-Drift-Liste).
> **Block-C-Closeout + Phase-14-Handoff (2026-08-22):**
> [`docs/concepts/phase13_c_block_c_replan.md`](./docs/concepts/phase13_c_block_c_replan.md).
> **Beweiswoche-Findings (2026-08-31, Mini-Session 23) + Pfad-C-Nachtrag (§8, Mini-Session 24):**
> [`phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md`](../phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md) — 14-Tage-Fenster source_delta-Diagnose, drei empirische Befunde (B1 IG-Bars-Lücke 2/13 Tage **by-design**, B2 53.6 % Divergenzrate **Stichprobe Operator-Run-Tag**, B3 `last_verified_utc` semantisch korrekt unter Pfad C); Befund-Inversion: **kein Recorder-Mapping-Bug** — Phase-13-Architektur sieht strukturell keine kontinuierliche `source='ig'`-Beschaffung vor.
> **Closeout-Handover (2026-08-31, Session 18):**
> [`phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md`](../phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md) — Pattern-Vergleich zu Phase-12-CLOSEOUT (§0 BLUF + 5-Zeilen-Bilanz, L1–L18, F1/F2/F3 + B1/B2/B3, Pfad-C-Entscheidung, §9 Konsistenz-Regeln inkl. IG-Default-AUS, §10 Don'ts).
> **Vorgeschichte:** [`phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md`](./phase12_data_foundation/PHASE12_5_CLOSEOUT_HANDOVER.md) und [`phase12_data_foundation/PHASE12_CLOSEOUT_HANDOVER.md`](./phase12_data_foundation/PHASE12_CLOSEOUT_HANDOVER.md) (Pattern-Vorbild).

**Goal:** Beschaffung und Verbrauch von Kursdaten endgültig trennen. Kein Konsumentenpfad löst
je einen externen Fetch aus; Beschaffung ist ein vierstufiges, nach Kosten/Latenz gestaffeltes
System in *ein* Archiv (S1 LS-Kerzen → S2 yF-Recorder → S3 Fremdquelle → S4 budgetierte
IG-Rettung, Default AUS). Die Abdeckungsfrage gilt dem **ganzen** Trade-Fenster statt dem
Schwanz. Drei nachgemessene Befunde tragen die Phase (Plan §4): tote IG-Historie mit `ok=True`,
ein dagegen blinder Divergenz-Sampler, und eine **erfundene** `TIME_STOP`-Auflösung bei einer
Lücke mitten im Fenster. Drei empirische Beweiswoche-Befunde (B1/B2/B3) bestätigen + invertieren
(kein Recorder-Mapping-Bug, sondern Architektur-konform).

**Block-Stand 2026-08-31 (final):**

- **Block A** (Schnitt + `assess_window` + Tracker-Guard + Stale-Assertion + Sampler-Reparatur
  + Registry-Hygiene) — ✅ committed, `git log` zeigt 13+ Commits zwischen A0 und A7+A7.5.
- **Block B** (Lightstreamer + TickAggregator-Fallback + Scheduler-Lebenszyklus +
  Token-Rotation) — ✅ committed, B0=NO → L6-Fallback aktiv. B0-Probe-Ergebnis im
  `phase13_live_data/CLAUDE.md` Kopf.
- **Block C** (Capital.com Pfad B + `GapRescue` S4 + `source_delta.py`) — ✅ **PARTIAL by
  design**: Pfad B live-verifiziert 2026-08-22 (962 `source='capital'`-Bars, DAX + CAC);
  Spain 35 (IBEX) wartet auf Phase 14 (Dukascopy wird dort eine Quell-Registry-Zeile, kein
  Backfill-Code mehr). Vollständiger Block-C-Stand im Re-Plan-Handover.
- **Beweiswoche** (Plan §7 P1–P9) — ✅ **gelaufen 2026-08-25 → 2026-08-31**, Mini-Session 23
  wertet aus, Mini-Session 24 entscheidet Pfad C (IG = S4-GapRescue, Default AUS, L18).

**Done-Kriterium:** erfüllt. Beweiswoche gelaufen + Pfad-C-Entscheidung getroffen +
Befund-Inversion dokumentiert. Erste Akzeptanzbedingung (strukturelle Kostenzusicherung
statt Zählwert) bleibt gelockt — `test_get_window_never_fetches` ist der Beleg.

**Directory:** [`phase13_live_data/`](../phase13_live_data/) (Kopf + Modul-Tabelle in
`phase13_live_data/CLAUDE.md`).

---

## Phase 14 — Discovery-Then-Deterministic *(eröffnet 2026-08-22 aus dem Session-13-Architektur-Insight, abgeschlossen 2026-08-31)*

> **Status: ✅ abgeschlossen (Closeout 2026-08-31, Session 23).** Blöcke 0 + A + B + C code-complete + Block-D-Doku-Updates ✅ (Stand 2026-08-31, Mini-Sessions 21+22+23+24) + D5-Handover **komplett freigegeben** (Mini-Session 24, Pfad-C-Entscheidung 2026-08-31). **Phase-13-CLOSE-OUT (Commit `0ff55d2`) hat die D5-Handover-Voraussetzung freigegeben.** 61 Phase-14-Tests grün, 54 `phase14:`-Commits auf `origin/main`, 38 Zeilen in `instrument_source_availability`, Σ 1703 grün repo-weit.
> **Plan:** [`docs/concepts/phase14_discovery_plan.md`](./docs/concepts/phase14_discovery_plan.md)
> (D1–D20 gelockt, Blöcke 0/A/B/C/D mit Verbatim-Ankern, Akzeptanz A1–A8, Drift-Liste §9,
> §11 Post-Execution-Korrekturnotizen).
> **Closeout-Handover (2026-08-31, Session 23):** [`phase14_discovery/PHASE14_CLOSEOUT_HANDOVER.md`](../phase14_discovery/PHASE14_CLOSEOUT_HANDOVER.md) — Pattern-Vergleich zu Phase-12/13 (§0 BLUF + 5-Zeilen-Bilanz, D1–D20 mit D19 = IG-Default-AUS + D20 = Brücke zur Phase 15, A1–A8-Akzeptanz mit Beleg, §9 13 Konsistenz-Regeln, §10 Don'ts).
> **Phasenkopf:** [`phase14_discovery/CLAUDE.md`](../phase14_discovery/CLAUDE.md)
> (Modul-Tabelle jetzt mit `Tests`-Spalte + Σ-Sweep-Tabelle + Phase-14-Closeout-Row, Session-23-Block).
> **Concept-Skizze:** [`docs/concepts/phase14_discovery_concept.md`](./docs/concepts/phase14_discovery_concept.md)
> (drei Bausteine: Quell-Profil + Kreuzungs-Tabelle + Konsumenten-Umstellung; sieben offene
> Fragen für die Plan-Session — vom Plan Q1–Q7 beantwortet).
> **Block-C-Handoff:** [`docs/concepts/phase13_c_block_c_replan.md`](./docs/concepts/phase13_c_block_c_replan.md)
> §3 + §5 (warum die Architektur eine eigene Phase rechtfertigt; was Phase 14 implizit
> absorbiert: hardcoded `EPIC_MAP`, Path C Dukascopy).
> **Spezial-Pläne (alle abgeschlossen, D5-Beweis erbracht):**
>   - [`phase14_discovery/PHASE14_C_DAEMON_CWD_BUG_PLAN.md`](../phase14_discovery/PHASE14_C_DAEMON_CWD_BUG_PLAN.md) (P14-C, Discovery-Daemon-CWD-Path-Bug, Mini-Session 17, 2026-08-26) — ARM-Pfad absolut
>   - [`phase14_discovery/PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md`](../phase14_discovery/PHASE14_D_DAEMON_SIGNAL_CAP_PLAN.md) (P14-D, Discovery-Daemon-Signal-Response-Bug, Mini-Session 18, 2026-08-26 + §10 Korrekturnotiz 2026-08-31) — `signal_check_interval_s`-Cap
>   - [`phase14_discovery/PHASE14_E_RECORDER_LOOP_PLAN.md`](../phase14_discovery/PHASE14_E_RECORDER_LOOP_PLAN.md) (P14-E, Recorder-Sleep-Cap + Restart-Loop-Hunt, Mini-Session 20, 2026-08-28 + §2 D3-Korrekturnotiz) — Cross-Phase-Phase-12
>   - [`phase14_discovery/PHASE14_F_DOC_ROTATION_HOOK_STEP2_PLAN.md`](../phase14_discovery/PHASE14_F_DOC_ROTATION_HOOK_STEP2_PLAN.md) (P14-F, Doc-Rotation-Hook Step 2, Mini-Session 22+24, 2026-08-31) — `--strict` als Default nach D5-Beweis
>
> **Akzeptanz A1–A8 (Plan §7), Stand 2026-08-22 nach Session 9, A1–A8 alle grün (unverändert):**
> A1 (Discovery 0 IG-Punkte strukturell), A2 (`grep EPIC_MAP phase13_live_data/*.py` leer),
> A3 (`measurable_universe()`-Identität), A4 (yF-Projektion), A5 (Daemon unscharf = nichts),
> A6 (UI warnt + scharf per Datei), A7 (`source_delta.py` Drei-Fälle-Trennung), A8 (Sweep
> 1659→1698→1703).
>
> **Block-D ✅ (Mini-Session 21, 2026-08-31) + P14-F ✅ (Mini-Session 22+24):**
> Block-D Hygiene-Edits als 4 Commits + P14-F Doc-Rotation-Hook Step 2 als 5 Commits
> (`94e0c35`/`d32e93a`/`8fe439c`/`8db5a1c`/`c4f7d9c`).
>
> **D5-Handover-Status 2026-08-31 (Mini-Session 23 + 24):** **komplett freigegeben** —
> architektonisch (Mini-Session 23: Tabelle + Discovery + Source-Delta arbeiten wie designed)
> + operativ (Mini-Session 24: Pfad-C-Entscheidung, IG = S4-GapRescue Default AUS, by-design,
> Phase-13-Recorder-Mapping-Initiative entfällt als architektur-konform — siehe
> [Findings-Notiz §8.1](../phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md)).
> **Phase-13-CLOSE-OUT (Commit `0ff55d2`) hat die formale Phase-14-D5-Handover-Voraussetzung
> freigegeben** — Phase 14 ist abgeschlossen.

**Goal:** jede Quelle (IG, yFinance, LS, Capital.com, später Dukascopy) **exponiert selbst**,
was sie liefern kann. Eine DB-Tabelle (`instrument_source_availability`) hält die Kreuzung
zwischen IG-Tradeable-Epics und verfügbaren Quellen. Konsumenten lesen die Tabelle, nicht den
Code. Hinzufügen einer Quelle ist eine Konfiguration, kein Code-Deploy.

**Why this is its own phase (Nikinger 2026-08-22):** die "discovery-then-deterministic"-
Architektur ist umfangreich genug (neues Schema, neue Schnittstelle pro Quelle, drei
Konsumenten-Migrationen, ToS-Tracking via `notes`-Spalte, Profile-Cache-TTL), dass sie den
Block-C-Closure sprengen würde. Phase 14 ist die **Brücke** zwischen dem
Datenfundament (Phase 13) und der AI-Sophistication (Phase 15): V4 setzt voraus, dass die
Daten-Infrastruktur **konfigurierbar** ist, nicht nur vorhanden.

**Scope-Skizze** (Concept, kein Plan):

- Quell-Profil-Schnittstelle (`SourceProfile` + `Source.discover()`), implementiert für
  Capital.com, yFinance, IG; LS bleibt Sonderfall (kein Discovery-API, Profil statisch).
- Phase-2-Migration `007_instrument_source_availability.sql` (Nummer in Plan-Session zu
  bestätigen).
- `run_capital_backfill` liest die Tabelle statt `EPIC_MAP`; `BarArchive.window(sources=…)`
  wird tabellenbewusst statt rang-bewusst; `source_delta.py` P6 trennt „nicht abrufbar" von
  „abrufbar und divergiert".
- Path C Dukascopy wird eine Quell-Registry-Zeile, **kein** Code-Touch in `live_data/`.

**Done-Kriterium** (Concept, zu schärfen in der Plan-Session): eine neue Quelle (Dukascopy
als Test-Kandidat) ist mit ≤ 50 Zeilen Commit angebunden, ohne dass ein Konsument
angefasst wird. `grep -rn "EPIC_MAP" phase13_live_data/ --include=*.py` ist leer.
*(`--include=*.py` ist Absicht: Phasenkopf, Session-Archiv und Closeout-Handover nennen
`EPIC_MAP` in ihrer Chronik und werden nicht editiert — 📕/📦-Konvention. Präzisiert
2026-08-22 im Phase-14-Plan §7/A2.)*

**Directory:** noch nicht angelegt — entsteht in der Plan-Session.

---
