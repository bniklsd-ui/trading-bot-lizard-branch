---
status: closed-phase
purpose: Phase-4 head — research.py LLM candidate selection, 8 locked decisions, candidate contract
read-when: working in phase4_research/ — read this head + its newest Session-stopped block first
detail: L2
up: ../CLAUDE.md
down:
  - ./SESSIONS_ARCHIVE.md      # full session history (L3)
  - ./README.md
  - ../docs/concepts/phase4_research_plan_konzept.md   # full concept/plan snapshot (L3)
updated: 2026-07-06
---
# research — Claude Code context (Phase 4)

## Project
Phase 4 of a DAX intraday CFD trading bot. This package is the **research
layer** — the single AI step (candidate selection) wrapped in deterministic
code-side validation, filtering, and persistence. Full design and all locked
decisions: `../docs/concepts/phase4_research_plan_konzept.md`.

**Status:** ✅ Code-complete + live-**tested** (2026-06-09). 88 mocked tests green;
`scripts/live_test.py` → `RESULT: 3/3 passed` against IG Demo + a real LLM call. See
the latest `## Session stopped` block below for the final state. Next phase (Phase 5)
is kicked off in the browser concept session, not here.

> ⚠ **Live-tested ≠ profit-validated.** "Live-tested" here means the pipeline runs
> *correctly* end-to-end (correct context, contract-valid pick or clean abstain, safe
> no-trade on every failure path — incl. a real markets-closed abstain at 07:18). It
> does **not** mean the bot is profitable: no real trades have been placed or
> evaluated, so the bot's edge is **unknown** and out of scope here. Trade execution
> is Phase 5; profitability is anchored to outcomes only in Phase 7 + live running.

> 🔁 **Phase-7 additive edit (2026-06-22, Decision I / Phase-7 Step 11 — loop-closure,
> code = source of truth):** the Phase-7 concept (§6 Step 11) demanded the one missing half
> of the learning loop be wired **here**. The read→prompt half was already in place
> (`context_builder` pulls `get_recent_lessons(5)`; `prompt._render_lessons` renders them);
> Step 11 adds the **mark-used** write-back: `research.py`'s `_DBLike` gained
> `mark_lesson_used`, and a best-effort `_mark_lessons_used(context.recent_lessons)` runs
> **after a successful `ask_candidate`** (before validation) — so the pre-LLM aborts never
> over-count. This is the **first DB write from research** (otherwise read-only here): a
> benign `used_in_research` increment, **not** a trade/outcome write, VETO/safety layer
> untouched. Failures log a `warning` and never break the cycle. Default research behaviour
> is otherwise unchanged (+6 tests → **88 → 94**; `FakeDB` gained a recording
> `mark_lesson_used`). Detail: `phase7_reward/` + `docs/concepts/phase7_reward_concept.md` §6 Step 11.

> 🔁 **Phase-8 additive edit (2026-06-29 — UI surfacing, code = source of truth):** the dashboard needed
> the LLM's **prose abstain reason**, which the schema already produces (`prompt.py` `required:[abstain,
> reasoning]`) but `run()` discarded. `research.py` now keeps it: a new instance attr
> `Research.last_no_pick_reasoning`, reset each `run()` and filled from `raw["reasoning"]` **only** on the
> valid-abstain branch (`vr.candidate is None`, i.e. `abstain=true`) — **not** on REJECT/filter (there the
> `reasoning` is the model's *pick* rationale, misleading as a skip reason). **Display-only: it gates
> nothing and never becomes a candidate** (root rule 3 intact); `run()`'s return type + all behaviour are
> unchanged. Phase 8 reads it (`scheduler/research_tick.py`) into `scheduler_state.last_no_trade_detail`
> for the UI. +2 P4 tests (**94 → 96**). Detail: `phase8_scheduler/CLAUDE.md` → `## UI-Erweiterung — 2026-06-29`.

> 🔁 **Phase-8 v1.5-hotfix edit (2026-07-01, Issue B — clamp/floor relax, code = source of truth):**
> Step-1 measurement found **100% of scored `bot_score`s below 50** → the below-50 double-clamp
> force-abstained every cycle. Two `ResearchConfig` **defaults were relaxed for demo data-collection**
> and the floor boundary was **decoupled**: `enable_long_bias_clamp` **True → False** (⚠ reverses
> Decision 7 — the long-bias clamp is off; the P6 debate + 4 VETOs are now the direction check),
> `confidence_floor_low_score` **70.0 → 55.0** (the 70 floor was unreachable at sub-50 scores), and a
> new field `confidence_floor_below_score = 50.0` replaced the hardcoded `candidate_filter._NEUTRAL_SCORE`
> literal so the floor boundary is independent of the clamp boundary. **All provisional — re-baseline
> before live** (Phase-7 outcome-anchored confidence replaces the blunt floor); every changed default
> carries a loud inline comment. **No VETO/gate touched**; only `phase4_research/`. +3 candidate_filter
> tests (**96 → 99**; the clamp *mechanism* stays covered via an explicit `clamped_config()`). Detail:
> `docs/concepts/phase8_v1.5_hotfix_plan.md` Step 3 + `phase8_scheduler/CLAUDE.md`.

> 🔁 **Phase-8 v1.5-hotfix edit (2026-07-01, Issue C — variety / typed universe, code = source of truth):**
> Step 2A widened the research universe from a single hardcoded epic to a typed, validated list — **no new
> AI**, DAX-only path bit-identical. `research/models.py` gained `InstrumentSpec` (epic/yf_ticker/volume_proxy/
> point_value/min_deal_size/currency/source) + `load_universe()` (EUR-only, fail-closed drop+warn, empty →
> ValueError); `ResearchConfig.universe` is now the **single source of truth** (reconciled with the legacy
> `epic_allowlist` in `__post_init__` — pass `universe=[InstrumentSpec…]` to widen, or keep constructing with
> `epic_allowlist=(...)` and it derives). **Per-epic brain context (the heart):** `ResearchContext.brain_contexts`
> keyed by epic; `context_builder` fetches a snapshot per tradeable epic; `prompt` renders each non-anchor
> snapshot; `candidate_filter`/`research.py` drift-coherence + `drift_at_pick` key on the candidate's OWN epic
> (fallback to the anchor `brain_context` for pre-v1.5 callers). `scripts/wiring.py` registers per-epic
> ticker/proxy from the universe. **Cross-phase companions:** P5 got a per-epic `point_value` seam
> (`ExecutionConfig.point_values`) and a new read-only operator resolver `scripts/resolve_epics.py`
> (repo-root). +18 P4 tests (**99 → 117**). Real epic strings (Euro Stoxx 50 / CAC 40) land in **Step 2B**
> after the operator runs `resolve_epics.py`. Detail: `docs/concepts/phase8_v1.5_hotfix_plan.md` Step 2 +
> `phase8_scheduler/CLAUDE.md` → `## Session stopped` (Step 2A).

> 🔁 **Phase-8 v1.5-hotfix edit (2026-07-01, Issue C, Step 2 COMPLETE, code = source of truth):**
> `research/models.py` gained a public `EXTENDED_UNIVERSE` (DAX + Euro Stoxx 50 + CAC 40 + IBEX 35 — 4
> EUR instruments, matching the locked "3-4 curated" decision) alongside the unchanged private
> `_DEFAULT_UNIVERSE` — a bare `ResearchConfig()` still defaults to DAX-only (no existing test/caller
> changes); only `scripts/wiring.py` (P4's `build_research` default, and P8's daemon-critical
> `_build_research`) opts explicitly into `EXTENDED_UNIVERSE`. **All four have live-confirmed
> `ohlcv_available=True`** (a second, paced `resolve_epics.py --pace-s 1.0` run confirmed the first
> run's CAC 40/AEX/IBEX failures were rate-limit noise, not real unavailability — `IGAdapter` raises
> `RateLimitError` on HTTP 429 with no built-in retry). Euro Stoxx 50's `yf_ticker="^STOXX50E"` /
> `volume_proxy="EXW1.DE"` are additionally **fully live-verified** via `phase3_external_data/scripts/
> smoke_test.py` (real drift/momentum/history + genuine non-zero EXW1.DE volume). CAC 40 (`^FCHI`) and
> IBEX 35 (`^IBEX`) base tickers are well-known public symbols, **not yet live-verified**; neither has a
> volume proxy (no confidently-known ETF ticker guessed — degrades to reduced-signal, concept C3). All
> three non-DAX `point_value`s remain **inferred** from IG's "(X€)" cash-instrument naming, not
> independently confirmed. AEX was searched and returned a genuine empty result (not rate-limited) —
> left out, matching the decision table's "optional" bracket. Test count unchanged at **120** (existing
> tests broadened, not added). Detail: `phase8_scheduler/CLAUDE.md` -> `## Session stopped` (Step 2
> complete).

> 🔁 **Phase-8 v1.5-hotfix edit (2026-07-01, Issue A — lesson provenance, code = source of truth):**
> the research prompt is fed the newest `trade_lessons`; every lesson today came from a **code-
> verification trade** (seeded, sub-minute forced time-stop) → it describes the test harness, not a
> market decision, and pollutes the single AI decision's input. **Fix (read-path here):**
> `context_builder.build_context` now calls a **new** P2 method `db.get_recent_lessons_for_prompt(5,
> …)` instead of `get_recent_lessons(5)`, driven by three new **provisional** `ResearchConfig` fields
> — `lesson_exclude_provenance=("verification",)` (precise tag written since v1.5), `lesson_min_hold_min
> =2.0` (fallback that catches the pre-tag polluted lessons — all sub-minute), `lesson_quarantine_before
> =None` (reversible one-time date reset, off by default). Downstream is automatic: `research.py`'s
> `_mark_lessons_used(context.recent_lessons)` now marks only the surviving (real) lessons; `prompt`
> renders only them. **Lessons still gate nothing** (root rule 3); the reward/score math never reads
> these getters (untouched). The write-side (who stamps `provenance`) is the P5 executor seam + P7
> recorder — see those phases. +2 P4 tests (**120 → 122**; `FakeDB` gained the new method). Detail:
> `docs/concepts/phase8_v1.5_hotfix_plan.md` Step 4.

> 🔁 **Phase-8 v1.6-hotfix edit (2026-07-02, Cause A part 2 — trade-history provenance, code = source
> of truth):** the v1.5 fix above only cleaned the `recent_lessons` channel. `build_context` also
> reads `db.get_recent_trades(8)` — a **second, separate** channel into the same single-AI-call
> prompt — which stayed unfiltered. A live v1.6 run showed the LLM's abstain reasoning citing fake
> "three consecutive losses totaling ~345€" from the three seeded verification trades (sub-minute
> forced time-stops), read straight off the raw trade-history table. **Fix (mirrors the lesson fix
> exactly, one level down):** `context_builder.build_context` now calls a **new** P2 method
> `db.get_recent_trades_for_prompt(8, …)` instead of `get_recent_trades(8)`, driven by three new
> **provisional** `ResearchConfig` fields — `recent_trades_exclude_provenance=("verification",)`,
> `recent_trades_min_hold_min=2.0`, `recent_trades_quarantine_before=None` — same three-signal
> precision order, but against the real `trade_outcomes.provenance` column (migration 003, P2) rather
> than a JSON blob. **Trade history still gates nothing** (root rule 3) — this only shapes the
> prompt. The write-side (who stamps `provenance` on the trade row) is the P7 recorder's
> `_open_record` (the tag already existed on `OpenedTrade`, it just never reached the trade row
> before this fix). +2 P4 tests (**133 → 135**; `FakeDB` gained `get_recent_trades_for_prompt`).
> Detail: `docs/concepts/phase8_v1.6_hotfix_plan.md` §6 + `phase8_scheduler/CLAUDE.md` →
> `## Session stopped — 2026-07-02 (v1.6-Hotfix: Cause A part 2)`.

> 🔁 **Phase-8 v1.6-hotfix edit (2026-07-02, Step 0 — observability, code = source of truth):** the
> v1.6 diagnosis of the `^FCHI`/`^IBEX` yfinance blocker exposed a meta-gap — no structured record of
> "which brain-context signal was full/degraded/unavailable per epic, and why". Fix (additive, gates
> nothing — root rule 3): `research/models.py`'s `ResearchContext` gained `brain_context_health`
> (per-epic `{"status": "full"|"degraded"|"unavailable", "missing":[...], "errors":{...}}`), derived
> in `context_builder.build_context` **from the already-fetched** `brain_contexts` prompt-dicts (the
> "which field" half is free — every `None` gap was already explicit) plus the new Phase-3
> `BrainContext.field_errors` (the "why" half — see `phase3_external_data/CLAUDE.md`'s matching note).
> `research.py`'s `Research` gained two new instance attributes mirroring the existing
> `last_no_pick_reasoning` pattern: `last_context_health` (copied from `context.brain_context_health`
> after every `build_context()`) and `last_abort_detail` (the exact free-text reason from **every**
> `_abstain()` call — broader than `last_no_pick_reasoning`, which only covers the model's own prose
> on a valid abstain). Both reset each cycle, both read defensively (`getattr`) by Phase 8's
> `research_tick.py`, which persists them into a new per-cycle JSONL log
> (`scheduler/observability.py`). +11 P4 tests (**122 → 133**: 5 `test_context_builder.py`, 6
> `test_research.py`). Detail: `docs/concepts/phase8_v1.6_hotfix_plan.md` Step 0 +
> `phase8_scheduler/CLAUDE.md` → `## Session stopped` (v1.6 „Wie").

> 🔁 **Phase-9 (V2) additive edit (2026-07-04, Step 5 — DB-backed universe, code = source of
> truth):** `research/models.py` gained `universe_from_records(records, *, fallback=
> EXTENDED_UNIVERSE)` — builds+validates an `InstrumentSpec` tuple from plain dicts (e.g. a
> Phase-9 `UniverseRecord.to_instrument_spec()`), falling back (with a `logger.warning`, never
> silent/never a crash) when `records` is empty. Phase 4 still imports **nothing** from the
> Phase-9 `universe` package — the dict boundary preserves phase isolation. `scripts/wiring.py`'s
> `build_research()` default now calls a new `build_universe_from_db()` (opens a Phase-9
> `UniverseStore`, lazy import, wrapped fail-soft) instead of hardcoding `EXTENDED_UNIVERSE`; an
> unbuilt/unseeded/unreachable Phase-9 DB on any given checkout still falls back to
> `EXTENDED_UNIVERSE` — **bit-identical to pre-Phase-9 behaviour** in that case. +6 P4 tests
> (**135 → 141**). Detail: `phase9_universe/CLAUDE.md` → `## Session stopped` (Step 5).

## The AI boundary (read first)
**Only one thing here is AI:** the single `llm_client.ask_candidate` call ("which
candidate?"). Everything else is plain code:
- context assembly (P1 broker probes, P2 reads, P3 brain context)
- the validator (hallucination guard)
- the `candidate_filter` (the **real** gate)
- persistence, retry, logging

The LLM **never** triggers an order. Its output passes the validator and the
deterministic filter first. LLM self-reported `confidence` is stored as raw data
but is **not** the gate (uncalibrated; Phase 7 anchors it to outcomes).

## Stack
- Python 3.11+ · `anthropic` SDK (the **only** new dep — live scripts + real call
  only; unit tests lazy-import + mock it) · `pytest` (mocked, no network).
- Run `pytest` from this directory (`phase4_research/`), same layout pattern as
  Phase 1/2/3 — the `research` package lands on the path via the test layout.

## The 8 locked decisions (concept §0)
1. **`direction` = `"BUY"` / `"SELL"`** only — what `open_position()` enforces.
   No CALL/PUT anywhere.
2. **DI via constructor.** `wiring.py`/`live_test.py` resolve real P1/P2/P3
   instances via `sys.path` bootstrap (like Phase-2 `live_test`).
3. **Structured Outputs as the primary path** (`output_format` json_schema, `epic`
   as an enum of the real list). Manual parse + fence-strip is fallback only. The
   validator runs **independently, always.**
4. **LLM confidence is epistemically weak** → store it, use it only as a coarse
   low floor, **not** the gate. The deterministic `candidate_filter` is the gate.
   Floor is documented as provisional (Phase-7 replaces it).
5. **Epic universe = hybrid, code-curated.** `epic_allowlist` config, default
   `("IX.D.DAX.IFMM.IP",)`. **No** `search_markets("DAX")` dragnet. Probe each epic
   via `get_price` + `get_market_info`, filter with `is_tradeable`.
6. **Credentials:** reuse Phase-1 `get_credential` (same keyring,
   `SERVICE_NAME="tradingbot"`). Key: `anthropic_api_key`. A thin Phase-4 shim
   documents the deliberate isolation exception.
7. **`allowed_directions`** config flag, default both; **long-bias clamp to
   `("BUY",)` when `bot_score < 50`** — was ON by default; ⚠ **v1.5 (2026-07-01):
   OFF by default** for demo data-collection (see the Phase-8 v1.5 note above;
   re-baseline before live).
8. **LLM error behaviour: exactly 1 retry**, only on *transient* faults
   (network/5xx/timeout/parse-/schema-fail). **No** retry on a valid `abstain` or
   a validator REJECT (those are content answers, not transport faults). Any final
   failure → `save_candidates([])` → no trade.

## Candidate contract (Phase 4 → Phase 5, frozen)
`turbo_candidates.json` holds, per pick, a dict with exactly:
`epic, direction("BUY"|"SELL"), llm_confidence(0-100, advisory), reasoning,
spread_pct_at_pick, drift_at_pick(|None), score_at_pick, threshold_applied,
generated_at(ISO-8601 UTC), source("research")`.
Abstain/reject → **empty list**, no `abstain` field on a persisted candidate.
See `research/models.py` (`Candidate`).

## Inherited contracts (verified against repo code — code = source of truth)
- **P1** `IGAdapter`: `connect/is_connected/get_account`; `get_price(epic).data`
  has `bid, ask, spread, spread_pct, market_status, timestamp`;
  `get_market_info(epic).data` has `min_deal_size, currency, instrument_type,
  market_status`; `open_position` requires `direction in ("BUY","SELL")`.
  `MarketStatus` is a `Literal` **string** ("TRADEABLE", …). `filters.is_tradeable`
  takes `Price`/`MarketInfo` **objects** (not dicts; `env.data` is the dict) —
  Step 3 reconstructs them or checks `spread_pct`/`market_status` off `env.data`.
  Always check `env.ok` before `env.data`.
- **P2** `Database`: `get_recent_trades(8)`, `get_recent_lessons(5)`,
  `get_current_score()`, `get_risk_level()`, `mark_lesson_used(id)`.
  `StateManager`: `save_candidates(list[dict])`, `load_candidates()`,
  `candidates_are_fresh()`, `clear_candidates()` (TTL 30 min). `CANDIDATES_FILE =
  "turbo_candidates.json"` (legacy name, frozen).
- **P3** `MarketDataFetcher.get_brain_context(epic) -> BrainContext | None`, then
  `.to_prompt_dict()` = **10 keys incl. `generated_at`** (Step 0.5). Every
  indicator value may be `None` (off-hours / unavailable). Practically never
  returns `None` for a mapped epic, but **propagates `EpicNotMappedError`** for an
  unmapped one → guard with `try/except EpicNotMappedError` + defensive `is None`.
- **Credentials:** `from broker_wrapper.credentials import get_credential`;
  `get_credential("anthropic_api_key")`; seed via `scripts/store_credential.py`.

## Build roadmap (strict TDD — each stage green before the next)
1. ✅ **scaffold + `models.py`** (types only).
2. ✅ `validator.py` + `test_validator.py` (safety core, **18 tests** ≥12) +
   `timeutil.py` (ISO stamp source).
3. ✅ `context_builder.py` (+ tests, **13** ≥6) — P1 probe / P2 reads / P3 brain context.
4. ✅ `prompt.py` (+ tests, **10** ≥5) — `(system, user, json_schema)`.
5. ✅ `llm_client.py` (+ tests, **10** ≥6) — Anthropic wrapper, Structured Outputs +
   fallback + 1 retry. **Token meter built** (`token_meter.py`, **6** tests, USD + EUR),
   **plus** `scripts/usage_report.py` summary (**4** tests), **plus the `.gitignore` fix**.
6. ✅ `candidate_filter.py` (+ tests, **15** ≥6) — the **real** deterministic gate.
7. ✅ `research.py` orchestrator (+ tests, **8** ≥5) — composes Steps 2–6, every
   non-PASS branch → `save_candidates([])`. `__init__.py` now exports
   `Research`/`ResearchConfig`.
8. ✅ `scripts/` — `wiring.py`, `smoke_test.py`, `live_test.py` + `research/
   credentials.py` shim (operator runs the live ones; not in CI).
9. ✅ finalize `README.md` + this file (+ top-level `CLAUDE.md`/`README.md` flipped to
   ✅ live-verified after the operator gate passed).

**Phase-4 gate:** `pytest tests/ -v` green, **≥40 tests**, `test_validator.py`
≥12; `live_test.py` writes a valid `turbo_candidates.json` (or a documented
abstain), exit 0; the proof-test (a hallucinated epic / inflated confidence /
old `CALL`) is caught by the validator before it becomes a candidate.

## Token / cost meter (user addition — design locked, built in Step 5)
Reads `usage.input_tokens`/`output_tokens` (+ cache fields) from each Anthropic
response; **appends** `{ts, model, input_tokens, output_tokens, est_cost_usd,
est_cost_eur}` to `data/state/llm_usage.json`. Per-model pricing + `usd_to_eur`
live in `ResearchConfig` (already present in `models.py`). `usage_report.py`
totals the log by model/day. Stays entirely in Phase 4.

> ✅ **Step-5 done (2026-06-08):** `data/state/llm_usage.json` is now gitignored
> (root `.gitignore`, dated reconciliation block mirroring the Phase-3 `data/cache/`
> rule). Verified via `git check-ignore data/state/llm_usage.json`.

> 🔁 **Phase-6 additive edit (2026-06-15, Decision F/G — code = source of truth):**
> Phase 6 reuses this stack (the documented cross-phase exception) and extended it
> **additively**, default behaviour for Phase 4 **unchanged**:
> - `token_meter.record` now also logs `cache_read_input_tokens` +
>   `cache_creation_input_tokens` (8-field record; old 6 keys unchanged → no consumer
>   break; they stay `0` for Phase 4, which doesn't cache). `test_token_meter` updated
>   to the 8-key shape; all 88 P4 tests stay green.
> - `LLMClient(cache_system=False)` (new ctor arg, **default off** = P4 untouched) +
>   `_build_create_kwargs(..., cache_system=False)`: when on, `system` is sent as a
>   content-block list carrying `cache_control:{"type":"ephemeral"}` (SDK 0.106
>   `TextBlockParam`). `LLMClient.last_usage` now captures the meter record per call
>   so a reusing caller can read per-turn usage. `usage_report.py` gained a
>   cache-hit-ratio + the two cache columns.
> - Full detail lives in `phase6_debate/` (Modul 4) + `docs/concepts/phase6_debate_concept.md` §4.

## Conventions
- `from __future__ import annotations`, type hints + docstrings everywhere.
- Own typed exceptions (`research/models.py`: `ResearchError` base,
  `LLMResponseError`, `ResearchAbort`). Never swallow silently.
- Logging → **stderr**; stdout reserved for machine-readable JSON.
- Tests are mocked, **no network / no real LLM**. The single raw SDK call is the
  one mockable point (Phase-3 `_raw_download` analogue).
- One file = one responsibility. Atomic commits.

## Don't
- Don't let any LLM output reach `open_position` without the validator + filter.
- Don't use LLM confidence as the gate — that's `candidate_filter`'s job.
- Don't write `CALL`/`PUT`/`strike`/`otm`/`issuer` anywhere — DAX CFD, BUY/SELL.
- Don't rename `turbo_candidates.json` (Phase-2/Phase-5 contract).
- Don't import a real LLM into unit tests — lazy-import + mock the SDK.
- Don't add a second LLM call site — `ask_candidate` is THE point.
- Don't consider a subtask done until `pytest tests/ -v` is green.

## After every task or subtask
- Add mocked `pytest` tests in `tests/` for every new function (no network).
- Update `../docs/concepts/phase4_research_plan_konzept.md` if a design decision
  changed (code = source of truth — annotate the doc with a dated note).
- Update the `## Session stopped` block below — even within a session — so the
  next session picks up cold.

---

## Session stopped — 2026-06-08 (Step 9 + Structured-Outputs schema fix, live-verified)

### Completed — schema fix + Step 9 (docs) — Phase 4 is DONE
- **Live gate exposed a real bug** (operator ran `smoke_test.py`/`live_test.py`): every
  Structured-Output call 400'd — `output_config.format.schema: Invalid schema: Enum value
  '…' does not match declared type '['string', 'null']'`. Anthropic Structured Outputs
  **rejects JSON-Schema type-array unions** (`{"type": ["string","null"]}`); the supported
  union form is `anyOf`. Numeric constraints (`minimum`/`maximum`) are also unsupported.
  - **`research/prompt.py:_build_schema`** — nullable `epic`/`direction`/`confidence` now
    use `anyOf` (string/number branch + `{"type":"null"}` branch); dropped `minimum`/
    `maximum` on `confidence` (range enforced independently by `validator.py` — defence in
    depth; the decoding-layer enum stays as the anti-hallucination guard). Empty universe →
    `epic` enum `[]` (well-formed; never sent — orchestrator abstains first).
  - **`research/llm_client.py`** — hardened the plain-call fallback with a pure
    `_extract_json_object()` (recovers the first balanced `{…}` from prose-wrapped text);
    retry policy + single `_raw_call` site unchanged. (Once the schema is valid this path is
    essentially never hit — it's the safety net.)
- **Positive proof-test added** (`tests/test_research.py::
  test_run_valid_pick_is_accepted_and_persisted_to_contract`) — the deterministic mirror of
  the hallucination-reject: a fabricated, fully-valid BUY pick flows through validator +
  filter + persistence and is asserted against the **frozen 10-field contract** (same checks
  `live_test.py` runs on a real pick). Guarantees the PASS path in CI without a live pick.
- **Concept reconciliation:** dated §4 annotation + corrected the inline schema stub to the
  `anyOf` form (`docs/concepts/phase4_research_plan_konzept.md`, Code = Source of Truth).
- **Docs finalized (Step 9):** this file + `README.md` flipped to ✅ live-verified (+ a
  `## Run` section); top-level `CLAUDE.md` "Current state" + root `README.md` now show
  Phase 4 ✅ abgeschlossen + live-verifiziert.
- **Reversibility:** annotated baseline tag **`phase4-pre-schema-fix`** (`81d7362`) captures
  the broken pre-fix state; concept-doc working copy backed up to
  `/tmp/phase4_konzept.pre-schema-fix.bak`.
- **Verification:** `pytest tests/ -v` → **88 passed** (was 84; +3 fallback/​helper in
  `test_llm_client.py`, +1 positive proof-test). `test_validator.py` stays **18** (≥12).
  Operator live re-run: `smoke_test.py`/`live_test.py` now log a single `POST /v1/messages
  "HTTP/1.1 200 OK"` (no 400, no fallback, no retry) → genuine model abstain →
  `live_test.py` `RESULT: 3/3 passed`, exit 0. **Not committed** (operator triggers commits).

### Next — Phase 5 (browser concept session, not here)
- Phase 4 is code-complete and live-verified; the only remaining cross-phase item (the
  Phase-5 momentum VETO against IG real-time bars) is explicitly carried over (concept §13).
  The Phase-5 concept/transition happens in the Claude browser interface, then implementation
  returns to Claude Code.

### Open questions / blockers
- None. If a future model/SDK rejects the `anyOf` schema, the hardened plain-call fallback
  + the always-on validator/filter still guarantee a safe abstain (never a fabricated trade).

---


> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
