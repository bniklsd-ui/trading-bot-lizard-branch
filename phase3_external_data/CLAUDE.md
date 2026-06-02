# external_data — Claude Code context

## Project
Phase 3 of a DAX intraday trading bot. This package is the market-data layer
outside the broker. Full design and all decisions: see
`../docs/concepts/phase3_external_data_konzept.md`.

**Status:** 🚧 in progress — step-by-step build per concept §14. See
`## Session stopped` at the bottom of this file for the current step.

## Stack
- Python 3.11+ · `yfinance>=0.2.65,<0.3` · `pandas>=2.0.0`
- `curl_cffi` comes transitively with yfinance (no custom session passed)
- `pytest` for tests (mocked, no network)

## Commands
```bash
pip install -r requirements.txt
pytest tests/ -v                       # mocked, no network
python scripts/smoke_test.py           # quick sanity (live)
python scripts/live_test.py            # hard-assert verification (live)
```
Run pytest from this directory (`phase3_external_data/`). Same layout pattern
as Phase 1/2 — the package `external_data` ends up on the path via the test
package layout.

## Architecture
**100% deterministic code — no LLM call anywhere in Phase 3.** One package,
single network point.

- `MarketDataFetcher` (`external_data/fetcher.py`) — public interface;
  per-method pipeline: `epic→yf` → off-hours guard → cache lookup →
  rate-limited fetch+retry → indicator compute → dataclass return.
- `_raw_download(symbol, period, interval) -> pd.DataFrame` — **the only**
  network call site. Tests monkeypatch this.
- `RateLimiter` — token-bucket, min. 0.5 s between calls.
- `FileCache` (`cache.py`) — JSON on disk, TTL via stored `expires_at`,
  atomic writes (temp + `os.replace`).
- `TickerMapper` (`ticker_map.py`) — IG epic → yf symbol; separate
  `_VOLUME_MAP` for ETF-volume proxies (`^GDAXI` degrades without one).
- `indicators.py` — pure functions on DataFrames (drift, momentum, volume
  z-score, high/low distance).
- `models.py` — dataclasses (`PriceBar`, `DriftResult`, ..., `BrainContext`).
- `market_hours.py` — `is_market_open()` for Mo–Fr 09:00–17:30 Europe/Berlin
  (DST-aware via `zoneinfo`).
- `timeutil.py` — `utc_iso_now()` / `parse_iso()`, **duplicated** from Phase 2
  (no cross-phase import — phase isolation).

## Runtime data location
- Cache: `<repo_root>/data/cache/*.json`
- Gitignored via an explicit `data/cache/` rule in the root `.gitignore`
  (added 2026-06-02 in Step 5 — the concept/this-file previously assumed it was
  already covered, but no rule matched the cache JSONs; reconciled then).
- `FileCache(cache_dir)` parameterised in the constructor; default computed in
  scripts/entrypoints per the Phase-2 `init_db.py` pattern.

## Key design decisions
- **Off-hours discipline:** intraday methods return `None` outside market
  hours — never serve stale intraday cache as fresh.
- **Delay-honesty:** `MomentumResult.is_realtime = False` always (yFinance is
  ~15 min delayed). `to_prompt_dict()` surfaces `momentum_is_realtime: False`
  to the LLM consumer.
- **`^GDAXI` volume degrades:** default `_VOLUME_MAP = {}` →
  `volume_available=False`, `z_score=0.0`. ETF-proxy hook via
  `register_volume_proxy(epic, "EXS1.DE")`.
- **Cache TTLs:** 1d bars → bis Mitternacht Europe/Berlin · 5m → 120 s ·
  30m → 300 s.
- **Two rate-limit error modes** both handled with exp-backoff:
  `YFRateLimitError` → `RateLimitError`; empty/short DataFrame →
  `DataUnavailableError`.

## ⚠ Phase-5 momentum-VETO flag (cross-phase notice)

The concept (§13) explicitly states: a **hard momentum VETO in Phase 5 must
not source from `get_momentum()`**. yFinance is ~15 min delayed; a
"15-minute momentum" would measure a window ending ~15 min ago, useless for
a VETO on an imminent trade. The hard VETO should come from Phase-1/IG
real-time bars. Phase-3 `get_momentum()` is a delayed **context signal** for
the Research prompt — not a VETO input. Phase 3 builds correctly; the VETO
sourcing decision belongs in the Phase-5 concept session.

## Conventions
- All timestamps ISO 8601 UTC, ms precision, `Z` suffix.
- Type hints + `from __future__ import annotations` everywhere.
- Logging to **stderr** only — stdout reserved for machine-readable JSON.
- Tests monkeypatch `fetcher._raw_download` — no network in unit tests.

## Don't
- Don't import `broker_wrapper` or `persistence` — phase isolation.
- Don't pass a custom `requests.Session` to yFinance (curl_cffi handles it;
  passing a Session raises `YFDataException` since yfinance 0.2.6x).
- Don't add a second yFinance call site — `_raw_download` is THE point.
- Don't serve stale intraday cache as fresh — return `None` instead.
- Don't add an LLM call anywhere — Phase 3 is 100% code.
- Don't consider a subtask done until `pytest tests/ -v` is green.

## After every task or subtask
- Add `pytest` tests in `tests/` for every new function (mocked, no network).
- Update `../docs/concepts/phase3_external_data_konzept.md` if a design
  decision changed.
- Update the `## Session stopped` block at the bottom — even within the
  same session — so the next session can pick up cold.

---

## Session stopped — 2026-06-02 (Phase 3 ✅ live-verified)

### Live gate — PASSED
- `python scripts/live_test.py --clear-cache` → **RESULT: 6/6 passed**, exit 0
  (against real `^GDAXI`, market open). `--volume-proxy EXS1.DE` verified the live
  ETF-volume path (`volume_available=True`, `volume_source=EXS1.DE`, `today_volume>0`,
  `z=-1.36`). Phase 3 is **live-verified** — the Phase-4 gate is cleared.
- **Rate-limiter check hardened (post-gate):** the original check needed two *fresh*
  network misses and could spuriously fail on a warm cache (a back-to-back run without
  `--clear-cache` showed `rate_limiter` "saw 0 (cached?)" — expected, since `^DJI`/
  `EURUSD=X` daily caches live until Berlin midnight). `_check_rate_limiter` now
  self-provisions a throwaway temp `FileCache` for its probe fetcher, so both probe
  fetches are guaranteed misses and the 0.5 s spacing is always measurable — the gate
  now passes 6/6 with or without `--clear-cache`. Concept §17.2 check 5 annotated.

### Completed
- **Step 10 — `scripts/live_test.py`** (concept §17.2) — the **hard-assert
  verification gate** before Phase 4.
  - Exercises every public method against real `^GDAXI` with PASS/FAIL assertions;
    stderr table `✓/✗ <name> — <detail>` + `RESULT: N/6 passed`; full
    `brain_context.to_dict()` JSON on **stdout**; exit `0` (all pass) / `1` (any fail).
    Entrypoint mirrors `smoke_test.py`. Runs in **both** market states (intraday values
    when open; `None` as a *passing* check when closed → runnable any time).
  - Six checks: (1) connectivity/completeness (`get_history` non-empty, `len>=20`,
    `high>=low` & `close>0`); (2) daily indicators (`volume` finite z; degrade without
    proxy / `volume_available`+`volume_source`+`today_volume>0` with `--volume-proxy`;
    `high_low` band sane, distances `>= -1e-6` for the fresh-ATH edge); (3) market-regime
    branch (open → drift/momentum/bars present + plausible + `is_realtime False`;
    closed → all three `None`); (4) cache-hit (2nd `get_history` adds **0** network
    calls); (5) rate-limiter spacing (two forced misses on `^DJI` then `EURUSD=X` ≥
    0.5−0.05 s apart); (6) `get_brain_context` tolerance (not `None`, all §4.1 prompt
    keys present). A `_Counter` wraps `fetcher._raw_download` (count + `monotonic`
    timestamps) and is restored in a `finally`. Argparse `--epic` / `--volume-proxy` /
    `--clear-cache` (`shutil.rmtree` before building `FileCache`) / `--cache-dir` /
    `--verbose`. Each check is wrapped so it records a failed entry instead of crashing.
  - **No new deps** (pure stdlib + the package; `yfinance` already pinned, Niklas
    installed it). **No pytest tests by design** (concept §17). Non-network checks:
    `py_compile` clean; `--help` → exit 0; `pytest tests/ -q` still **70 passed**
    (scripts not collected — no pytest config, default `test_*.py`).
  - **Live run is Niklas's job** — the Phase-4 gate:
    `python scripts/live_test.py --clear-cache` → expect `RESULT: 6/6 passed`, exit 0
    (also `--volume-proxy EXS1.DE` to verify the ETF-volume path).
  - Docs: `README.md` banner flipped to ✅ code-complete + a `## Run` section with the
    live-script commands and the stdout/stderr + 429 caveats.

### Phase 3 status
**Code-complete.** All 10 build steps done; 70 mocked tests green; both live scripts
written. The **only** remaining item is Niklas's `live_test.py` run ending exit 0 —
that is the verification gate. The phase transition itself (and the Phase-4 concept)
happens in the browser concept session, not here (top-CLAUDE.md). When the live gate
passes, update the top-level `CLAUDE.md` "Current state" + `README.md` status table to
mark Phase 3 ✅ live-verified.

### Earlier (this session)
- **Step 9 — `scripts/smoke_test.py`** (concept §17.1) — quick **live** sanity run.
  - Drives the full fetcher pipeline once against real yFinance and prints the
    research prompt-dict. *Prints, does not hard-assert* (that's Step 10's
    `live_test.py`). Entrypoint mirrors Phase-2 `init_db.py`: `_PACKAGE_ROOT` on
    `sys.path`, `_DEFAULT_CACHE_DIR = <repo_root>/data/cache`,
    `logging.basicConfig(stream=sys.stderr)`. **stdout = single prompt-dict JSON;
    stderr = all human progress** (concept §17 split).
  - Argparse: `--epic` (default `IX.D.DAX.IFMM.IP`), `--volume-proxy` (e.g. `EXS1.DE`),
    `--cache-dir`, `--verbose`. Registers the volume proxy on the mapper when given.
    Runs `get_drift` / `get_momentum` / `get_bars(5m,5)` / `get_history(30d)` /
    `get_volume_anomaly` / `get_high_low_distance` / `get_brain_context`, each via a
    `_run(label, fn)` helper that catches `ExternalDataError` → prints `ERROR …` and
    continues (one transient 429 won't abort the run). Prints the off-hours
    expected-behaviour note when the market is closed.
  - **No pytest tests by design** (concept §17 — live, non-deterministic, not
    collected by CI). Non-network verification done: `python -m py_compile
    scripts/smoke_test.py` clean; `python scripts/smoke_test.py --help` → usage,
    exit 0 (imports resolve without yfinance — only pandas is pulled in);
    `pytest tests/ -q` still **70 passed** (scripts not collected).
  - **Live run is Niklas's job:** `python scripts/smoke_test.py` (+ `--volume-proxy
    EXS1.DE` for the ETF-volume path).

### Earlier (this session)
- **Step 8 — `external_data/__init__.py` exports** (concept §14.7 / §18) +
  `tests/test_package_exports.py`.
  - `external_data/__init__.py`: replaced the placeholder with real re-exports —
    `from .cache import FileCache`, `from .fetcher import MarketDataFetcher`,
    `from .ticker_map import TickerMapper`; `__all__` = those three (the names §18
    requires). Contract dataclasses + exceptions intentionally **not** in `__all__`
    — they stay importable from `external_data.models` / `external_data.exceptions`
    (existing consumer/test pattern). Docstring documents the network-free-import
    invariant (yfinance still lazy in `_raw_download`).
  - `tests/test_package_exports.py`: 3 tests — three names importable from the
    package root; each is the *same object* as its submodule definition (re-export,
    not a copy); `__all__` is exactly the three. No network, no fixtures.
  - **`pytest tests/ -v` → 70 passed** (Steps 3–8; 67 prior + 3 new). Bare
    `python -c "import external_data; print(external_data.__all__)"` resolves without
    yfinance installed.
  - `requirements.txt` (the other half of §14.7) was already present + correct —
    untouched.

### Earlier (this session)
- **Step 7 — `fetcher.py`** (concept §11) + `tests/test_fetcher.py`.
  - `external_data/fetcher.py`: the public interface. `_raw_download(symbol, *,
    period, interval)` — **the only** network site, lazy `import yfinance`, **no**
    custom session (curl_cffi internal). Module-level `_SLEEP = time.sleep`
    indirection so tests neutralise backoff + rate-limiter waits.
    `_fetch_with_retry` — exp backoff 1→2→4 s, ≤3 tries; rate-limit detected by
    **class name** (`_is_rate_limit_error`, matches `YFRateLimitError` without
    importing yfinance) → `RateLimitError`; empty/short DF → `DataUnavailableError`;
    any other exception propagates. `RateLimiter` (token bucket, ≥0.5 s, first call
    never blocks). Cache ↔ DataFrame (de)serialisation helpers (`_df_to_records`,
    `_records_to_df`, `_records_to_bars`) so hit and miss paths compute identically.
    `MarketDataFetcher(mapper, cache, rate_limiter=None)` with private `_get_records`
    (key → cache.get hit/miss → wait → fetch+retry → cache.set). Public methods:
    `get_drift` / `get_bars` / `get_momentum` (intraday, off-hours → `None`),
    `get_history` / `get_volume_anomaly` / `get_high_low_distance` (daily, always
    run), `get_brain_context` (each sub-`get_*` in its own `try/except
    ExternalDataError` → field `None` + WARNING, never crashes). Daily history runs
    through `indicators._ffill_gaps` + `_drop_outliers` before computing. TTL policy
    lives here: `1d` → seconds-to-next-Berlin-midnight (`_seconds_until_berlin_midnight`,
    clock via `timeutil._utcnow`), `5m` → 120 s, `30m` → 300 s. `get_high_low_distance`
    current_price = last 5m close in-hours (falls back to last daily close if that
    intraday fetch is `DataUnavailable`), last daily close off-hours.
  - `tests/test_fetcher.py`: **15 tests** (all mocked — monkeypatch
    `fetcher._raw_download` + `fetcher._SLEEP`, local `YFRateLimitError` stand-in,
    `fake_download` factory routes by interval): cache-hit→no 2nd fetch;
    miss→fetch→cache write; empty→retry→`DataUnavailableError`;
    `YFRateLimitError`→retry→`RateLimitError`; off-hours drift/momentum/5m-bars→`None`
    + no fetch; daily off-hours allowed; momentum `is_realtime is False`; volume
    degrade (no proxy) + volume proxy path (fetches proxy symbol); high/low off-hours
    uses last daily close; `get_brain_context` tolerance (5m fails → drift+momentum
    `None`, daily fields + history intact, full prompt-dict keys); `EpicNotMappedError`
    propagates (no fetch); `RateLimiter.wait` invoked once per miss, not on hit.
  - **`pytest tests/ -v` → 67 passed** (Steps 3–7; 52 prior + 15 new). No network,
    yfinance not required.
  - **Mismatch fixed (concept↔code):** concept §11 typed `get_bars`
    `-> list[PriceBar]`, but the off-hours guard + §17.2 live check require `None`
    off-hours for an intraday resolution. Implemented `-> list[PriceBar] | None`;
    added a dated "Angepasst 2026-06-02 (Step 7)" note in concept §11 (Source =
    Source of Truth).

### Earlier (prior session)
- **Step 6 — `indicators.py`** (concept §10, the core) + `tests/test_indicators.py`.
  - `external_data/indicators.py`: pure functions (DataFrame in → dataclass out,
    no I/O / network / clock). `compute_drift` (today_open = last daily Open,
    current = last 5m Close; guards empty/`open<=0`; `is_realtime=False`),
    `compute_momentum` (`bars_back=max(1,round(window/5))`, guards too-few-bars /
    `price_start<=0`; `is_realtime=False`), `compute_volume_anomaly` (window =
    `lookback_days` vols **before** today; sample std; `not available`/`std==0`→
    z=0; thresholds 2.0/3.0; **never None** — degrades full object),
    `compute_high_low_distance` (rolling max High / min Low over lookback; signed
    distances; near<1.5%; guards empty/`current<=0`). Hygiene helpers
    `_ffill_gaps` (df.ffill) and `_drop_outliers` (IQR on Close, keep
    `|Close-median| <= 3·IQR`; `IQR==0`→no-op). Private `_bar_ts_iso` converts a
    bar index Timestamp → UTC ISO via `timeutil.iso_from_dt`.
  - `external_data/timeutil.py`: added `iso_from_dt(dt)` (canonical formatter for
    an arbitrary aware instant; converts to UTC, naive→UTC); `utc_iso_now()` now
    delegates to it. (`cache.py`'s own `_format_iso` left untouched — verified
    Step-5 code, identical format.)
  - `tests/conftest.py`: added `sample_dax_daily`, `sample_dax_daily_zero_volume`,
    `sample_dax_5m` DataFrame fixtures (yFinance `.history()` shape, tz-aware index).
  - `tests/test_indicators.py`: 22 tests (drift 4, momentum 5, volume 5,
    high/low 5, hygiene 3) — expected numbers recomputed from fixtures, not
    hard-coded.
  - **`pytest tests/ -v` → 52 passed** (Steps 3–6). pandas 3.0.3 / numpy 2.4.6
    installed in the venv.

- **Step 5 — `cache.py`** (concept §9) + `tests/test_cache.py`.
  - `external_data/cache.py`: `FileCache(cache_dir)` — eager mkdir; one JSON file
    per key `{"expires_at": "<ISO>", "data": [...]}`; atomic write (temp +
    `os.replace`, mirroring Phase-2 `state.py`). `make_key(symbol, resolution,
    date)` strips leading `^` (`^GDAXI`→`GDAXI`) and replaces `=` (`EURUSD=X`→
    `EURUSD_X`) → FS-safe. TTL via stored absolute `expires_at` compared to
    `timeutil._utcnow()` (frozen-clock testable); `set` stores `now + ttl`.
    `get` → `None` on missing/expired/corrupt, corrupt **self-heals** (unlink) +
    WARNING, never raises. `clear_expired()` → count of expired/corrupt removed.
    Module-local `_format_iso(dt)` mirrors `timeutil.utc_iso_now`'s format for an
    arbitrary instant (timeutil only formats "now"). TTL *policy* (resolution→TTL)
    intentionally lives in the fetcher, not here.
  - `tests/conftest.py`: added `tmp_cache` fixture (`FileCache` in `tmp_path`).
  - `tests/test_cache.py`: 12 tests (make_key determinism + `^`/`=`-safe;
    resolution-distinct keys; set/get roundtrip; missing→`None`; TTL fresh→hit;
    TTL expired→`None`; corrupt JSON→`None`+self-heal; missing-`expires_at`→
    treated-as-corrupt; `clear_expired` count incl. corrupt sweep; `cache_dir`
    creation; atomic write leaves no `.tmp`).
  - **`pytest tests/ -v` → 30 passed** (Steps 3–5).
  - **Mismatch fixed (concept↔code):** concept §2 and this file claimed
    `data/cache/` was already gitignored — it was not (root `.gitignore` only
    covered `*.sqlite` + named state JSONs). Added `data/cache/` to root
    `.gitignore` (commented), and reconciled the §2 note + the runtime-data note
    above. Verified via `git check-ignore data/cache/<x>.json`.

### Earlier (prior session)
- **Step 1 — Scaffold.** `phase3_external_data/` tree, empty `__init__.py`s,
  `requirements.txt`, `README.md` skeleton, `CLAUDE.md` skeleton (this file).
- **Step 2 — Contracts.**
  - `external_data/exceptions.py`: `ExternalDataError` base (code+retryable
    via Phase-1 pattern) and the three subclasses
    `EpicNotMappedError` (not-retryable, propagates as programmer error),
    `DataUnavailableError` (retryable), `RateLimitError` (retryable).
  - `external_data/models.py`: dataclasses `PriceBar`, `DriftResult`,
    `MomentumResult` (`is_realtime=False` default — delay-honest),
    `VolumeAnomaly` (with `volume_available` + `volume_source` for
    degrade path), `HighLowDistance`, `BrainContext`. `BrainContext`
    exposes `to_prompt_dict()` (concept §4.1 key set incl.
    `momentum_is_realtime` and `range_30d`) and `to_dict()` (full incl.
    `price_history_30d` via `dataclasses.asdict`).
  - Verified by `python3 -c "..."` import+sanity check (no pytest tests
    needed — pure dataclasses, no logic to exercise yet).
- **Step 3 — `timeutil.py` + `market_hours.py`.**
  - `external_data/timeutil.py`: `utc_iso_now()` / `parse_iso()` duplicated
    from Phase 2 (identical `...123Z` ms format), **plus** the concept-§6
    monkeypatchable `_utcnow()` indirection (Phase 2 lacked it). `utc_iso_now()`
    reads the clock via `_utcnow()` so tests can freeze it.
  - `external_data/market_hours.py`: `is_market_open(now=None)` — Mo–Fr
    09:00–17:30 `Europe/Berlin`, DST-aware via `zoneinfo` (boundaries
    inclusive). `now=None` → `timeutil._utcnow()` (referenced module-qualified
    so a patch is seen, per §15); naive datetimes treated as UTC. Holiday
    calendar deliberately omitted in v1 (TODO hook in docstring; holidays fall
    into the later `DataUnavailableError` path).
  - `tests/conftest.py`: minimal shell with a `frozen_clock` fixture
    (patches `timeutil._utcnow`; returns a setter, defaults Mon 2026-05-25
    09:00 UTC). Will grow with `tmp_cache` / sample-DataFrame fixtures in
    later steps.
  - `tests/test_market_hours.py`: 9 tests green (weekday-in-window, Sat, Sun,
    before-open, after-close, DST-season divergence, inclusive boundaries,
    `now=None` clock path, naive-as-UTC). `pytest tests/ -v` → **9 passed**.
- **Step 4 — `ticker_map.py`.**
  - `external_data/ticker_map.py`: `TickerMapper` with class-level `_MAP`
    (incl. `IX.D.DAX.IFMM.IP → ^GDAXI`, `IX.D.DAX.DAILY.IP`, `CS.D.EURUSD.MINI.IP
    → EURUSD=X`, `IX.D.DOW.DAILY.IP → ^DJI`) and empty `_VOLUME_MAP`
    (ETF-proxy hook → `^GDAXI` degrades). `__init__` copies the class defaults
    into **per-instance** dicts so `register` / `register_volume_proxy` are
    instance-local (no shared-class-dict leakage — design note in docstring;
    concept §8 signatures unchanged). `epic_to_yf` raises `EpicNotMappedError`
    on miss (exact-match, case-sensitive); `epic_to_volume_yf` → `None` when no
    proxy. `register_volume_proxy` docstring carries the §8 caveat (ETF volume
    ≈ ETF trading interest, not index volume).
  - `tests/test_ticker_map.py`: 9 tests green (known epics incl. non-`^`;
    unknown→`EpicNotMappedError` with `code`/`retryable` asserted; `register`;
    override; volume-proxy-missing→`None`; `register_volume_proxy`→hit;
    case-sensitivity; `^`-symbol integrity; instance isolation).
  - `pytest tests/ -v` → **18 passed** (Step 3 + Step 4).

### Next
- **All build steps (1–10) are complete.** Nothing left to *code* in Phase 3.
- **Niklas:** run `python scripts/live_test.py --clear-cache` (the verification gate)
  → expect `RESULT: 6/6 passed`, exit 0. Optionally `--volume-proxy EXS1.DE`. A 429
  failure is upstream state, not a code defect — retry with `--clear-cache` after a
  short pause.
- **After the gate passes:** mark Phase 3 ✅ live-verified in the **top-level**
  `CLAUDE.md` "Current state" and the root `README.md` status table; the Phase-4
  concept/transition happens in the browser session, not in Claude Code.

### Open questions / blockers
- None. Phase 3 is code-complete (all 10 steps; 70 mocked tests green; both live
  scripts written). The single open item is the live `live_test.py` gate run, which
  Niklas performs.
- `yfinance` is **not** needed for unit tests (`_raw_download` imports it lazily;
  tests monkeypatch it). It is only required for the manual live scripts
  (`smoke_test.py`, `live_test.py`), which Niklas runs — already installed in the venv.
