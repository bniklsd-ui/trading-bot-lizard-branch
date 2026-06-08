# research — Claude Code context (Phase 4)

## Project
Phase 4 of a DAX intraday CFD trading bot. This package is the **research
layer** — the single AI step (candidate selection) wrapped in deterministic
code-side validation, filtering, and persistence. Full design and all locked
decisions: `../docs/concepts/phase4_research_plan_konzept.md`.

**Status:** 🚧 in progress — step-by-step build per the concept's
"Build-Reihenfolge". See `## Session stopped` at the bottom for the current step.

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
   `("BUY",)` when `bot_score < 50`** is ON by default.
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
7. ☐ `research.py` orchestrator (+ tests ≥5).
8. ☐ `scripts/` — `wiring.py`, `smoke_test.py`, `live_test.py` (operator runs the
   live ones; not in CI).
9. ☐ finalize `README.md` + this file.

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

## Step 1 log — 2026-06-05 (superseded by the Step 2 handover below)

### Completed — Step 1 (scaffold + `models.py`)
- Created `phase4_research/` tree: `research/` (package), `tests/` (empty marker),
  `scripts/` (dir only — files arrive in Step 8), `requirements.txt` (`anthropic`
  pinned, dev `pytest`), `README.md`, this `CLAUDE.md`.
- `research/models.py` — **types only, no logic**:
  - `Candidate` (frozen Phase 4→5 contract, 10 fields + `to_dict()`),
  - `ResearchContext` (deterministic prompt input; `tradeable_epics`,
    P2 reads, `brain_context` = 10-key dict|None, `anchor_epic`),
  - `ValidationResult` (`valid`/`candidate`/`rejected_reason`; abstain =
    `valid=True, candidate=None`),
  - `ResearchConfig` — all concept-§1 defaults **plus** the token-meter fields
    (this session's decision: **USD + EUR**): `pricing_usd_per_mtok`
    (per-model `(in,out)` USD/Mtok, dated estimate caveat), `usd_to_eur=0.92`,
    `usage_log_path=None` (wiring resolves to `data/state/llm_usage.json`).
  - Exceptions: `ResearchError` base, `LLMResponseError`, `ResearchAbort`.
- `research/__init__.py` deliberately exports nothing yet (real exports land with
  `Research` in Step 7).
- **Verification:** `py_compile` clean; import-sanity (`ResearchConfig()` builds
  with correct defaults, no `anthropic` import, no network); `Candidate(...)
  .to_dict()` round-trips the 10 contract keys, JSON-serialisable. No pytest file
  yet **by design** — pure types/dataclasses, no logic to exercise (mirrors the
  Phase-3 Step-2 contracts call). Phase 1/2/3 suites untouched.
- **No concept↔code mismatch** found this step — inherited contracts re-verified
  against the repo code and all matched the concept.

## Session stopped — 2026-06-08 (Step 6)

### Completed — Step 6 (`candidate_filter.py` — THE real deterministic gate)
- `research/candidate_filter.py` — three pure functions (no I/O / clock / AI;
  imports only `research.models` + stdlib):
  - `confidence_threshold(bot_score, config)` — coarse provisional floor
    (`confidence_floor_low_score` at `bot_score < 50.0` else
    `confidence_floor_default`). Module const `_NEUTRAL_SCORE = 50.0`, kept
    **distinct** from `config.long_bias_below_score` (separate knobs, same default).
  - `resolve_allowed_directions(bot_score, config)` — long-bias clamp to
    `("BUY",)` when `enable_long_bias_clamp and bot_score < long_bias_below_score`.
  - `apply_filter(candidate, context, config) -> FilterVerdict` — ordered hard
    rules off the **universe entry** (`context.tradeable_epics`): in-universe
    (`epic_not_in_universe`), spread ≤ `max_spread_pct` (`spread_too_wide`),
    `market_status == TRADEABLE` (`not_tradeable`), direction in clamped set
    (`direction_not_allowed`); then a **soft** drift-coherence sanity:
    SELL vs drift `> +_DRIFT_COHERENCE_PCT` (0.5%) or BUY vs drift `< -0.5%` →
    `FilterVerdict(ok=True, rule="drift_coherence_warn")` (passes WITH warning —
    P3 drift is ~15 min delayed, never a reject; `drift_pct is None` → skipped).
- `research/models.py` — added local `FilterVerdict` dataclass (`ok / rule /
  reason / details`), mirroring `broker_wrapper.filters.FilterVerdict`'s shape but
  **not** imported (phase isolation). Soft-warn convention documented: `ok=True`
  with a `rule` set = "passed with a coherence warning".
- `tests/test_candidate_filter.py` — **15 passed** (≥6): floor 55/70; clamp
  on/off; SELL filtered at score<50; clean BUY passes; SELL ok at neutral;
  spread-too-wide / not-tradeable / epic-not-in-universe rejects; drift-incoherent
  SELL **and** BUY warn-but-pass; drift `None` no-warn; `brain_context=None`
  graceful. No conftest change needed (`research_context` + `dataclasses.replace`).
- **Concept reconciliation:** dated §6 annotation added to
  `docs/concepts/phase4_research_plan_konzept.md` (local `FilterVerdict`; literal
  `50.0` floor boundary; `_DRIFT_COHERENCE_PCT=0.5` soft warn; universe-entry-based
  checks).
- **Verification:** `py_compile` clean; `pytest tests/ -v` → **76 passed**
  (61 + 15). `test_validator.py` stays **18** (≥12). `candidate_filter.py` imports
  nothing from `anthropic`/`broker_wrapper`/`external_data`/`persistence`.
  **Not committed** (operator triggers commits).

### Next — Step 7 (`research.py` orchestrator)
- `class Research(__init__(broker, db, state, market_data, llm, config))` + `run()
  -> list[Candidate]` (concept §7, tests ≥5). Flow: session-health pre-flight
  (`is_connected`/`connect`, `get_account().ok`, anchor `get_price` TRADEABLE) →
  `ResearchAbort` on fail; `build_context`; `confidence_threshold` +
  `resolve_allowed_directions`; `build_prompt`; the **single** `llm.ask_candidate`
  (`LLMResponseError` → abstain); `validate_candidate(... score_at_pick=
  context.bot_score, drift_at_pick=<context.brain_context["drift_pct"]>)`; then
  `apply_filter`; PASS → `state.save_candidates([candidate.to_dict()])`. Every
  abstain/reject/error → `save_candidates([])`. stderr logging; stdout = result
  JSON only. Use `FakeLLM` (already in conftest) + the existing fakes.
- Then Step 8 scripts (`wiring.py`, `smoke_test.py`, `live_test.py`,
  `research/credentials.py` shim) — **operator** runs the live ones — and Step 9
  docs finalize.

### Open questions / blockers
- None. `_DRIFT_COHERENCE_PCT = 0.5` is a deliberately blunt soft-warn constant
  (not tuned); the hard momentum VETO is Phase 5 (IG real-time bars), not here.

---

## Session stopped — 2026-06-08 (Step 5, superseded by Step 6 above)

### Completed — Step 5 (`llm_client.py` + token meter + `.gitignore` fix)
- `research/llm_client.py` — `LLMClient.ask_candidate(system, user, json_schema) -> dict`,
  **the single AI call site of the whole bot.**
  - **Billing decision ("which way"):** **Messages API only** — one `client.messages.create`
    per cycle, billed purely per token. **No** Managed Agents, **no** server-side tools
    (those add a hosted-agent-loop + per-session-container charge on top of tokens — the
    "second bill"). All non-AI work is our code → only the one call's tokens bill.
  - **Structured Outputs** via `output_config={"format":{"type":"json_schema","schema":…}}`
    (the deprecated top-level `output_format` is **not** used) with the dynamic schema from
    `prompt.py`. **Fallback:** plain call → fence-strip → `json.loads`.
  - **Sampling-param drop:** `_supports_sampling()` omits `temperature` for Opus 4.7/4.8
    (they 400 on it); default `claude-sonnet-4-6` keeps `temperature=0.2`. **Thinking off**
    by default (configurable via `enable_thinking`). **Caching** intentionally off.
  - **Retry (Decision 8):** SDK `max_retries=0`; own policy = exactly 1 retry on transient
    (network/timeout/5xx/429/JSON-parse), **no** retry on a content answer (incl. `abstain`)
    or 400/auth → `LLMResponseError`. Faults classified **by class name** → unit run never
    imports `anthropic`. One mockable site: `_raw_call` (lazy SDK import) + pure
    `_build_create_kwargs`.
- `research/token_meter.py` — `estimate_cost()` (USD+EUR, incl. cache multipliers, unknown
  model → 0) + `record()` appending the frozen 6-key record to `data/state/llm_usage.json`
  (JSON array; `path=None` → no write). `ts` via `timeutil`.
- `scripts/usage_report.py` (+ `scripts/__init__.py`) — pure `summarize()` by model/day +
  `format_report()`; runnable standalone.
- **Reconciliations:** `models.py` Opus-4.8 pricing `(15,75)→(5,25)` (dated note); root
  `.gitignore` += `data/state/llm_usage.json`; concept §5 dated annotation.
- `tests/conftest.py` — added `_FakeUsage`/`_FakeMessage`/`make_message`/`FakeRawCall` +
  `FakeLLM` (for Step 7) + named test exceptions (`BadRequestError`/`AuthenticationError`).
- **Verification:** `pytest tests/ -v` → **61 passed** (41 + 10 llm_client + 6 token_meter +
  4 usage_report). Meta-path import-guard confirms the unit run never imports
  `anthropic`/`broker_wrapper`/`external_data`/`persistence`. `git check-ignore` passes.
  **Not committed** (operator triggers commits).

### Next — Step 6 (`candidate_filter.py` — THE real deterministic gate)
- `confidence_threshold(bot_score, config)` (55 ≥50 / 70 <50), `resolve_allowed_directions`
  (long-bias clamp to `("BUY",)` when `bot_score < long_bias_below_score`), and
  `apply_filter(candidate, context, config) -> FilterVerdict` (spread ≤ max, TRADEABLE,
  direction in clamped set, **soft** drift-coherence warn — not a hard reject; concept §6).
  Tests ≥6 (floor 55/70, clamp on/off, SELL filtered at score<50, clean BUY passes).
- Then Step 7 orchestrator (`research.py`, uses `FakeLLM` from conftest), Step 8 scripts +
  `research/credentials.py` shim + **operator live test** (real network — user runs it).

### Open questions / blockers
- None. Default model stays `claude-sonnet-4-6` (well-prompted); thinking off but
  configurable (user-confirmed this session). Live `_raw_call` test is the operator's job,
  lands with Step 8.

---

## Step 4 log — 2026-06-05 (superseded by the Step 5 handover above)

### Completed — Step 4 (`prompt.py` — deterministic prompt assembly)
- `research/prompt.py` — `build_prompt(context, threshold, allowed_directions) ->
  (system, user, json_schema)`. Pure function, no I/O/clock/AI. Static system prompt
  (DAX intraday CFD analyst, pick ≤1 **only from the list** or abstain, data ~15 min
  delayed → sentiment not real-time, BUY/SELL only, abstain on doubt). Code-built user
  message: delayed market snapshot (every `None` → `"n/a"` via one `_fmt()` choke point,
  never `0`), recent-trades table (`date | direction | epic | pnl | status`), active
  lessons (`lesson_text`), decision block (score / risk / floor / permitted directions),
  tradeable-instruments table (`epic | name | spread% | min_size`), answer-format note.
  `json_schema` with **dynamic** `epic` enum (`[*epics, None]`) and `direction` enum
  reflecting the clamp (`[*allowed_directions, None]`); `required=["abstain","reasoning"]`,
  `additionalProperties=False`. Empty universe → `epic` enum `[None]` (no crash).
- `tests/conftest.py` — added a `research_context` fixture (direct `ResearchContext`
  construction, so prompt tests don't depend on `build_context`). Existing fixtures
  untouched.
- `tests/test_prompt.py` — **10 passed** (≥5): 3-tuple + system constraints; universe in
  user table **and** schema enum; honest `None` render (off-hours + whole-snapshot-None);
  schema shape (required/additionalProperties/0-100); BUY-only clamp in enum + instruction
  blocks; trades+lessons rendered; empty trades/lessons graceful; floor/score in user;
  empty-universe edge.
- **Verification:** `py_compile` clean; `pytest tests/ -v` → **41 passed** (31 + 10), no
  network; confirmed `prompt.py` imports only `research.models` + stdlib (no
  `anthropic`/`broker_wrapper`/`external_data`/`persistence`). **Committed** to
  `phase4-research` (no merge to `main`).

### Concept↔code reconciliation (Step 4)
- §4 `direction`-schema enum made **dynamic** from `allowed_directions` (concept stub
  showed static `["BUY","SELL",None]`); `None` rendered as `"n/a"`; trade table columns =
  `date|direction|epic|pnl|status`; system prompt forbids CALL/PUT explicitly. Dated note
  added to `docs/concepts/phase4_research_plan_konzept.md` §4.

### Next — Step 5 (`llm_client.py` + token meter + `.gitignore` fix)
- `LLMClient.ask_candidate(system, user, json_schema) -> dict` (concept §5, tests ≥6).
  Primary path = Anthropic Structured Outputs (`output_format`/json_schema); fallback =
  plain call + fence-strip + `json.loads`. **Exactly 1 retry** on *transient* faults
  (network/timeout/5xx/parse-/schema-fail), **no** retry on a valid `abstain` or a
  content answer. **One mockable raw SDK call site** (the Phase-3 `_raw_download`
  analogue) — lazy-import `anthropic`; unit tests mock it, no network.
- **Also in Step 5 (don't forget):** the **token meter** — read `usage.input_tokens`/
  `output_tokens` (+ cache fields) from each response, append `{ts, model, input_tokens,
  output_tokens, est_cost_usd, est_cost_eur}` to `data/state/llm_usage.json` (pricing +
  `usd_to_eur` already in `ResearchConfig`); a `scripts/usage_report.py` summary; **and
  the `.gitignore` rule** for `data/state/llm_usage.json` (root `.gitignore` covers the
  other state files but not this one — the same reconciliation Phase 3 did for
  `data/cache/`). Add `FakeLLM`/raw-call fakes to conftest.

### Open questions / blockers
- None. One step per session — Step 5 next session.

---

## Step 3 log — 2026-06-05 (superseded by the Step 4 handover above)

### Completed — Step 3 (`context_builder.py` — deterministic input side)
- `research/context_builder.py` — `build_context(broker, db, market_data, config)
  -> ResearchContext`. 100% code, no AI. Per allow-list epic: `get_price` +
  `get_market_info`, kept only if `env.ok` **and** `market_status == "TRADEABLE"`
  **and** `spread_pct ≤ config.max_spread_pct` **and** `currency == "EUR"` → universe
  dict `{epic, name, spread_pct, market_status, min_deal_size}`. P2 reads
  (`get_recent_trades(8)`/`get_recent_lessons(5)`/`get_current_score`/
  `get_risk_level`). P3 `get_brain_context(anchor).to_prompt_dict()` (10 keys), every
  `None` passed through verbatim. Empty universe → empty `tradeable_epics` (abstain
  path for Step 7). Collaborators typed via local `Protocol`s (`_BrokerLike`,
  `_DBLike`, `_FetcherLike`) — **no** `broker_wrapper`/`external_data`/`persistence`
  import.
- `tests/conftest.py` — extended `FakeBroker` with `get_market_info` (separate
  `info_ok`/`currency`/`min_deal_size`/`name` toggles; `get_price` untouched so the 18
  validator tests stay green); added `FakeDB`, `FakeFetcher`, `_FakeBrainContext`,
  local `EpicNotMappedError`, `_make_prompt_dict()` helper + `db`/`prompt_dict`/
  `fetcher` fixtures.
- `tests/test_context_builder.py` — **13 passed** (≥6): full context; empty
  trades/lessons; `volume_z_score=None` pass-through; all-intraday-`None` off-hours;
  untradeable status / wide spread / non-EUR drop-outs; `get_price` ok=False;
  `get_market_info` ok=False; `EpicNotMappedError` → `brain_context None`; defensive
  `None` return; non-guard exception re-raises; two-epic allow-list partial probe.
- **Verification:** `py_compile` clean; `pytest tests/ -v` → **31 passed** (18 + 13),
  no network; confirmed `anthropic`/`broker_wrapper`/`external_data`/`persistence`
  never imported in the unit run. **Not committed** (operator triggers commits).

### Concept↔code reconciliation (Step 3)
- §3 offered two tradeability-check options; took the **env.data-direct** one (no
  `Price`/`MarketInfo` rebuild, no `is_tradeable` call) for phase isolation, consistent
  with the validator. `EpicNotMappedError` caught **by class name**, not imported. Dated
  note added to `docs/concepts/phase4_research_plan_konzept.md` §3.

*(Step-3 "Next/Open" trimmed — superseded; see the Step 4 handover above.)*
