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
2. ☐ `validator.py` + `test_validator.py` **first** (safety core, **≥12 tests**).
3. ☐ `context_builder.py` (+ tests ≥6) — P1 probe / P2 reads / P3 brain context.
4. ☐ `prompt.py` (+ tests ≥5) — `(system, user, json_schema)`.
5. ☐ `llm_client.py` (+ tests ≥6) — Anthropic wrapper, Structured Outputs +
   fallback + 1 retry. **Token meter built here** (USD + EUR), **plus**
   `scripts/usage_report.py` summary, **plus the `.gitignore` fix** (see below).
6. ☐ `candidate_filter.py` (+ tests ≥6) — the **real** deterministic gate.
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

> ⚠ **Step-5 must-do:** `data/state/llm_usage.json` is **not** gitignored yet
> (root `.gitignore` covers `turbo_candidates.json`, `*.sqlite`, `ig_state.json`,
> `data/cache/` — but not the usage log). Step 5 adds a `.gitignore` rule for it,
> the same reconciliation Phase 3 did for `data/cache/`. Don't forget.

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

## Session stopped — 2026-06-05

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

### Next — Step 2 (the safety core)
- `research/validator.py` + `tests/test_validator.py` **first** (concept §2,
  **≥12 tests** — the most important test of the phase). Pure function
  `validate_candidate(raw, epic_universe, threshold, allowed_directions, broker,
  max_spread_pct) -> ValidationResult`. Check order: abstain → required fields →
  **epic ∈ universe** → direction ∈ allowed → confidence numeric/0-100/≥threshold
  → **live-spread recheck** (fresh `get_price`, `env.ok`, `spread_pct ≤ max`,
  `market_status == "TRADEABLE"`) → PASS builds `Candidate` with
  `spread_pct_at_pick` from the fresh price. Mandatory test cases listed in concept
  §2 (invented epic, `CALL`, sub-/at-threshold confidence, >100, wide spread,
  non-TRADEABLE, `get_price` ok=False, missing fields, abstain, clean BUY, SELL).
- Use a `FakeBroker` in `tests/conftest.py` returning canned `Envelope`-shaped
  objects for `get_price` (no real broker).

### Open questions / blockers
- None. One step per session per the operator's instruction — Step 2 next session.
