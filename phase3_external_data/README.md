# external_data — Phase 3

> **Status:** ✅ **live-verified 2026-06-02** — all 10 build steps done, **70 mocked
> tests** green, and `scripts/live_test.py --clear-cache` → `RESULT: 6/6 passed`
> against real `^GDAXI` (ETF-volume path verified via `--volume-proxy EXS1.DE`). See
> `CLAUDE.md` `## Session stopped` for details. Built per
> `docs/concepts/phase3_external_data_konzept.md`.

The market-data layer outside the broker. **100% deterministic code — no LLM
calls.** Fetches OHLCV from yFinance and computes drift, momentum, volume
z-score, and high/low distance for downstream phases.

> Rule of thumb: *"What is the broker telling me about my order?"* → Phase 1.
> *"What is the bot doing right now?"* → Phase 2.
> *"What is the market doing outside my broker?"* → Phase 3.

## What it is, what it isn't

**Is:** rate-limited cached yFinance access, indicator math, a single
network point (`fetcher._raw_download`), honest delay/availability labels.

**Isn't:** an order-decision input. yFinance is ~15 min delayed for `^GDAXI` —
see the Phase-5 momentum-VETO flag in `CLAUDE.md`.

## Install

```bash
pip install -r requirements.txt
# If yfinance fails to install: curl_cffi needs a C toolchain on some
# systems. On Debian/Ubuntu: sudo apt install build-essential libffi-dev
```

## Run

```bash
pytest tests/ -v                       # 70 mocked tests, no network

# live scripts (real yFinance, no IG account, NOT collected by pytest):
python scripts/smoke_test.py                       # quick sanity → prompt-dict on stdout
python scripts/smoke_test.py --volume-proxy EXS1.DE
python scripts/live_test.py --clear-cache          # hard-assert gate → RESULT: 6/6 passed, exit 0
python scripts/live_test.py --volume-proxy EXS1.DE # also verify the ETF-volume path
```

Both live scripts print human progress to **stderr** and a single machine-readable
JSON to **stdout**. `live_test.py` runs in both market states (intraday values when
open, `None` as a *passing* check when closed) and is the verification gate before
Phase 4. A real 429 fails a run (upstream state, not a code defect) — retry with
`--clear-cache` after a short pause.

## Layout

```
phase3_external_data/
├── external_data/
│   ├── __init__.py        exports MarketDataFetcher, TickerMapper, FileCache
│   ├── exceptions.py      ExternalDataError hierarchy
│   ├── models.py          Dataclasses (PriceBar, DriftResult, ..., BrainContext)
│   ├── timeutil.py        utc_iso_now / parse_iso / _utcnow
│   ├── market_hours.py    is_market_open() — Europe/Berlin, Mo–Fr 09:00–17:30
│   ├── ticker_map.py      TickerMapper (epic→yf, epic→volume-yf)
│   ├── cache.py           FileCache (JSON, TTL, atomic writes)
│   ├── indicators.py      pure functions (drift, momentum, volume, high/low)
│   └── fetcher.py         MarketDataFetcher + RateLimiter + _raw_download
├── scripts/
│   ├── smoke_test.py      quick sanity print
│   └── live_test.py       hard-assert verification (exitcode 0/1)
└── tests/                 70 tests, mocked _raw_download — no network
```

## Conventions

- `from __future__ import annotations`, type hints everywhere, docstrings on
  every public function/class.
- Logging via stdlib `logging`, **always to stderr** (stdout reserved for
  machine-readable JSON).
- Tests mock `fetcher._raw_download` — no network calls in unit tests.
- All timestamps ISO 8601 UTC, ms precision, `Z` suffix (identical format to
  Phase 1/2, duplicated `timeutil.py` — no cross-phase import).
- A subtask isn't done until `pytest tests/ -v` is green.

## Integration contract (phase isolation)

Phase 3 **never imports `broker_wrapper` or `persistence`**. It receives an IG
epic string and returns plain dataclasses / dicts. This keeps the layer runnable
offline (unit tests, analysis) with no broker connection.

Consumed by:

- **Phase 4** (`turbo_research`) — `get_drift`, `get_bars`, `get_history`
- **Phase 5** (`pre_trade`) — `get_momentum` (context only, NOT a VETO source)
- **Phase 7** (Longterm Brain) — `get_volume_anomaly`, `get_high_low_distance`,
  `get_brain_context().to_dict()` for `trade_lessons.market_context_json`
