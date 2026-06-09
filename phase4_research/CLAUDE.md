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

## Session stopped — 2026-06-08 (Step 8)

### Completed — Step 8 (`scripts/` wiring + smoke + live + credentials shim)
- `research/credentials.py` — the **single, documented** phase-isolation exception
  (Decision 6). Self-contained `sys.path` bootstrap to `phase1_broker_wrapper`
  (`Path(__file__).parents[2]`) → re-exports `broker_wrapper.credentials.get_credential`
  (`__all__`). Docstring states *why* (Hard Rule 1: one keyring path, no second
  credential code path). Key `anthropic_api_key`; seed via Phase-1
  `scripts/store_credential.py`. **Not** imported by unit tests (LLM key is a ctor arg,
  mocked) → suite stays keyring-free.
- `scripts/wiring.py` — `build_research(config=None) -> Research`. `sys.path` bootstrap
  (own pkg + P1/P2/P3), builds **real** collaborators: broker via Phase-1 factory
  **`get_broker("ig_demo")`** (canonical build point — no direct `IGAdapter(...)`),
  `Database(data/trading_bot.sqlite)`, `StateManager(data/state)`,
  `MarketDataFetcher(TickerMapper+register_volume_proxy(anchor, config.volume_proxy),
  FileCache(data/cache))`, `LLMClient(... api_key=get_credential("anthropic_api_key"),
  token_meter_path=data/state/llm_usage.json, config=config)`. Cross-phase imports are
  **lazy inside `build_research`** → `import scripts.wiring` is network/DB-free; only the
  *call* reads the keyring. No network at construction (IG connect + SDK are lazy in
  `run()`).
- `scripts/smoke_test.py` — one **live DRY** run. Swaps `research.state` for a `_DryState`
  (no-op `save_candidates` recorder) **after** `build_research`, prints the deterministic
  context (universe / brain / score / risk via an extra `build_context`) + the cycle
  outcome to **stderr**, and the would-be-saved JSON to **stdout**. Prints, does not
  assert. Argparse `--epic/--volume-proxy/--model/--verbose`.
- `scripts/live_test.py` — the **hard-asserted Phase-4 gate**. Real `StateManager`,
  `clear_candidates()` → `run()` → asserts: run() didn't raise; `load_candidates()`
  mirrors the `run()` return (the one-save invariant); on a PICK the persisted dict
  honours the **frozen 10-field contract** (keys / epic∈allowlist / direction∈{BUY,SELL}
  / conf 0–100 / source=="research" / ISO `generated_at` / numeric `spread_pct_at_pick`);
  on an ABSTAIN the list is empty. Both outcomes = `exit 0`. `_Check` table + `RESULT:
  N/M passed` → stderr; persisted JSON → stdout. The hallucination **proof-test** is
  *not* forced live (a real model won't hallucinate on demand) — it's deterministically
  covered by `test_research.py` (invented epic) + `test_validator.py` in CI; `live_test`
  guarantees the same validator/filter path runs live and only a contract-valid pick is
  persisted.
- **Concept reconciliation:** dated §8 annotation added to
  `docs/concepts/phase4_research_plan_konzept.md` (self-bootstrapping shim; `get_broker`
  factory; lazy cross-phase imports; DRY-via-state-swap; live proof-test = CI-covered;
  no script unit tests).
- **Verification:** `py_compile` clean on all four; `smoke_test.py --help` /
  `live_test.py --help` → exit 0 (no network — `anthropic` lazy in `_raw_call`, yfinance
  lazy in P3); `import scripts.wiring` resolves (shim path-bootstrap works);
  `pytest tests/ -v` → **still 84 passed** (`test_validator.py` 18 ≥ 12; scripts not
  collected). **Not committed** (operator triggers commits).

### Next — Step 9 (finalize `README.md` + this `CLAUDE.md`)
- `README.md`: flip the banner to ✅ code-complete; add a `## Run` section with the live
  commands (`python scripts/smoke_test.py`, `python scripts/live_test.py`) + the prereqs
  (IG Demo creds, `anthropic_api_key` in keyring, `pip install -r requirements.txt`) and
  the stdout/stderr split.
- This `CLAUDE.md`: confirm the AI-boundary / Candidate-contract / 8-decisions sections
  are final; mark the confidence-floor explicitly provisional (Phase-7 replaces).
- After Step 9 the **only** open item is the operator's live gate run (below).

### Operator's gate (the user runs this — Claude does code + mocked tests only)
- `cd phase4_research && python scripts/live_test.py` → expect a valid
  `data/state/turbo_candidates.json` **or** a documented clean abstain, `exit 0`.
- Prereqs: `pip install -r requirements.txt` (installs `anthropic` in the venv); IG Demo
  creds + `anthropic_api_key` seeded in the keyring (Phase-1
  `scripts/store_credential.py anthropic_api_key`). Run `scripts/smoke_test.py` first for
  a DRY sanity check. Market-closed → expect a clean abstain (still `exit 0`).
- When the gate passes, mark Phase 4 ✅ live-verified in the **top-level** `CLAUDE.md`
  "Current state" + root `README.md` (Phase-5 concept/transition happens in the browser
  session, not here).

### Open questions / blockers
- None. Step 8 is code-complete; the live run is the operator's job. `anthropic` is not
  needed for unit tests (lazy + mocked); it's only required for the two live scripts.

---

## Session stopped — 2026-06-08 (Step 7, superseded by Step 8 above)

### Completed — Step 7 (`research.py` orchestrator — the full `run()` cycle)
- `research/research.py` — `class Research(__init__(broker, db, state, market_data,
  llm, config))` + `run() -> list[Candidate]`. **Pure composition** of Steps 2–6;
  imports only `research.*` + stdlib (collaborators via local `typing.Protocol`s
  `_BrokerLike`/`_DBLike`/`_StateLike`/`_FetcherLike`/`_LLMLike` — **no**
  `anthropic`/`broker_wrapper`/`external_data`/`persistence` import). Flow:
  1. `_preflight()` — `is_connected()` → else `connect()` (`.ok` req) →
     `get_account().ok` → anchor `get_price().ok` **and** `market_status ==
     TRADEABLE` (`anchor = config.epic_allowlist[0]`). Any fail → `ResearchAbort`,
     caught → empty save, **no LLM call**.
  2. `build_context`; empty `tradeable_epics` → empty save, **no LLM call**.
  3. `confidence_threshold` + `resolve_allowed_directions` (off `context.bot_score`).
  4. `build_prompt`.
  5. The **single** `llm.ask_candidate`; `LLMResponseError` → empty save.
  6. `drift = (context.brain_context or {}).get("drift_pct")`; `validate_candidate(...
     score_at_pick=context.bot_score, drift_at_pick=drift)`; `not vr.valid`
     (REJECT) **or** `vr.candidate is None` (abstain) → empty save.
  7. `apply_filter`; `not fv.ok` → empty save (a soft `drift_coherence_warn` is
     `ok=True` → **passes**).
  8. PASS → `state.save_candidates([candidate.to_dict()])`; return `[candidate]`.
  **Invariant:** exactly one `save_candidates` per cycle; stderr logging only,
  stdout untouched (result JSON is Step-8's job → `run()` stays I/O-free).
- `research/__init__.py` — now exports `Research` + `ResearchConfig`.
- `tests/conftest.py` — `FakeBroker` extended with the session-health surface
  (`is_connected`/`connect`/`get_account` + `connected`/`connect_ok`/`account_ok`
  toggles, `connect_calls`/`account_calls` counters); new `FakeState` (recording
  `save_candidates` sink) + `state` fixture. Existing fakes untouched (defaults
  healthy → 18 validator / 13 context tests stay green).
- `tests/test_research.py` — **8 passed** (≥5): full PASS (1 saved, `spread_pct_at
  _pick` = fresh recheck, `drift_at_pick` passthrough); abstain (empty save, LLM
  **was** called); validator REJECT (hallucinated epic); LLM-error; session-health
  fail ×2 (account + connect → empty save, **`llm.calls == []`**); empty universe
  (no LLM call); soft drift-warn still PASSES + saves.
- **Concept reconciliation:** dated §7 annotation added to
  `docs/concepts/phase4_research_plan_konzept.md` (preflight order; both
  validator-fail sub-branches; `fv.ok`-only gate; stdout discipline; DI Protocols;
  conftest growth).
- **Verification:** `pytest tests/ -v` → **84 passed** (76 + 8). `test_validator.py`
  stays **18** (≥12). `research.py` real imports = `research.*` + stdlib only
  (grep). `from research import Research, ResearchConfig` resolves. **Not
  committed** (operator triggers commits).

### Next — Step 8 (`scripts/` — wiring + smoke + live; operator runs the live ones)
- `scripts/wiring.py`: `sys.path` bootstrap → build **real** `IGAdapter` (Demo
  creds via keyring), `Database`, `StateManager`, `MarketDataFetcher` (**`register
  _volume_proxy("EXS1.DE")`** from `config.volume_proxy`), `LLMClient`
  (`get_credential("anthropic_api_key")` via the new `research/credentials.py`
  shim → reuses `broker_wrapper.credentials.get_credential`). One factory
  `build_research(config) -> Research`. Resolve `usage_log_path` to
  `<repo_root>/data/state/llm_usage.json`.
- `research/credentials.py`: thin shim documenting the deliberate isolation
  exception (Decision 6) — `get_credential` re-export from Phase 1.
- `scripts/smoke_test.py`: one real Research run, **DRY** (`save` no-op), prints
  context + LLM answer + validator/filter verdicts. Manual.
- `scripts/live_test.py`: full cycle vs IG Demo + real LLM → writes valid
  `turbo_candidates.json` **or** documents a clean abstain; **hard-asserted**,
  `exit 0` = PASS. **Operator runs it** (real network — not in CI).
- Then Step 9: finalize `README.md` + this file. **Phase-4 gate** is then met
  (≥40 tests incl. validator ≥12 ✅; the proof-test = hallucinated epic caught by
  the validator is already green in `test_research.py`).

### Open questions / blockers
- None. Step 8 is the operator-facing wiring + live test; the live network run is
  the user's job (per project rule: Claude does code + mocked tests only).

---

## Session stopped — 2026-06-08 (Step 6, superseded by Step 7 above)

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
