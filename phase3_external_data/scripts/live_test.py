#!/usr/bin/env python3
"""Hard-assert live verification for the Phase 3 external-data layer (concept §17.2).

This is the **verification gate before Phase 4** — the analogue of Phase 2's
``scripts/live_test.py``. It exercises every public method against real ``^GDAXI``
plus behavioural assertions about caching, the rate limiter and off-hours discipline,
prints a PASS/FAIL table, and exits ``0`` (all pass) / ``1`` (≥1 fail).

It is a **live** script: it touches the network, is non-deterministic, needs no IG
account, and is deliberately not collected by ``pytest`` / CI. Run it manually before
a phase transition.

Convention (concept §17): the human-readable table + RESULT line go to **stderr**; the
single machine-readable JSON (the full ``brain_context.to_dict()``) goes to **stdout**.

Designed to run in BOTH market states: during XETRA hours the intraday methods must
return values; outside them they must return ``None`` (a *passing* check), so the
script is runnable any time of day. ``--clear-cache`` is optional — every check
(including the rate-limiter timing, which self-provisions a fresh temp cache) is
robust to a warm cache from a prior run.

> Caveat: a real yFinance ``429 Too Many Requests`` can make a run fail — that is a
> network/upstream state, not a code defect. On failure, retry with ``--clear-cache``
> after a short pause before distrusting the code.

Usage:
    python scripts/live_test.py
    python scripts/live_test.py --clear-cache --verbose
    python scripts/live_test.py --volume-proxy EXS1.DE
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import shutil
import sys
import tempfile
import time
from pathlib import Path

# Make the `external_data` package importable when run as a script (Phase-2 pattern).
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent  # phase3_external_data/
sys.path.insert(0, str(_PACKAGE_ROOT))

from external_data import FileCache, MarketDataFetcher, TickerMapper  # noqa: E402
from external_data import fetcher as fetcher_module  # noqa: E402
from external_data.market_hours import is_market_open  # noqa: E402

_REPO_ROOT = _PACKAGE_ROOT.parent
_DEFAULT_CACHE_DIR = _REPO_ROOT / "data" / "cache"

# Two other built-in epics used purely to force the rate-limiter spacing check on
# always-available daily symbols distinct from the primary one.
_SECONDARY_EPIC_A = "IX.D.DOW.DAILY.IP"     # → ^DJI
_SECONDARY_EPIC_B = "CS.D.EURUSD.MINI.IP"   # → EURUSD=X

# Keys the prompt-dict must expose (concept §4.1).
_PROMPT_KEYS = {
    "ticker", "drift_pct", "momentum_15m_pct", "momentum_is_realtime",
    "volume_z_score", "volume_available", "distance_to_high_pct",
    "distance_to_low_pct", "range_30d", "generated_at",
}

log = logging.getLogger("phase3.live_test")


def _eprint(message: str = "") -> None:
    """Print a human-facing line to stderr (stdout is reserved for the JSON)."""
    print(message, file=sys.stderr)


class _Counter:
    """Wraps ``fetcher._raw_download`` to count real network calls and time them."""

    def __init__(self) -> None:
        self.count = 0
        self.times: list[float] = []
        self._real = fetcher_module._raw_download

    def install(self) -> None:
        def _counting(symbol, *, period, interval):
            self.count += 1
            self.times.append(time.monotonic())
            return self._real(symbol, period=period, interval=interval)

        fetcher_module._raw_download = _counting

    def restore(self) -> None:
        fetcher_module._raw_download = self._real


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 3 external-data live verification (hard assertions, exit 0/1)."
    )
    parser.add_argument("--epic", default="IX.D.DAX.IFMM.IP", help="IG epic (default: %(default)s)")
    parser.add_argument(
        "--volume-proxy", default=None, metavar="YF_SYMBOL",
        help="optional ETF volume proxy, e.g. EXS1.DE (tests the live ETF-volume path)",
    )
    parser.add_argument(
        "--clear-cache", action="store_true",
        help="wipe the cache dir before the run (makes cache-hit/rate-limiter checks meaningful)",
    )
    parser.add_argument(
        "--cache-dir", default=str(_DEFAULT_CACHE_DIR),
        help=f"cache directory (default: {_DEFAULT_CACHE_DIR})",
    )
    parser.add_argument("--verbose", action="store_true", help="DEBUG logging")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s %(message)s",
        stream=sys.stderr,
    )

    if args.clear_cache:
        shutil.rmtree(args.cache_dir, ignore_errors=True)
        _eprint(f"cleared cache dir {args.cache_dir}")

    mapper = TickerMapper()
    if args.volume_proxy:
        mapper.register_volume_proxy(args.epic, args.volume_proxy)
    cache = FileCache(args.cache_dir)
    fetcher = MarketDataFetcher(mapper, cache)

    counter = _Counter()
    counter.install()

    market_open = is_market_open()
    _eprint(
        f"epic={args.epic}  yf={mapper.epic_to_yf(args.epic)}  "
        f"market_open={market_open}  volume_proxy={args.volume_proxy or '—'}"
    )

    results: list[tuple[str, bool, str]] = []

    def _check(name: str, fn) -> None:
        """Run a check function returning ``(passed, detail)``; never crash the run."""
        try:
            passed, detail = fn()
        except Exception as exc:  # noqa: BLE001 — a check must never crash the harness
            results.append((name, False, f"{type(exc).__name__}: {exc}"))
            return
        results.append((name, bool(passed), detail))

    try:
        _check("connectivity", lambda: _check_connectivity(fetcher, args.epic, counter))
        _check("daily_indicators", lambda: _check_daily_indicators(fetcher, args.epic, args.volume_proxy))
        _check("market_regime", lambda: _check_market_regime(fetcher, args.epic, market_open))
        _check("cache_hit", lambda: _check_cache_hit(fetcher, args.epic, counter))
        _check("rate_limiter", lambda: _check_rate_limiter(counter))
        _check("brain_context", lambda: _check_brain_context(fetcher, args.epic))

        ctx = fetcher.get_brain_context(args.epic)
    finally:
        counter.restore()

    # -- report -----------------------------------------------------------
    _eprint("")
    for name, passed, detail in results:
        mark = "✓" if passed else "✗"
        _eprint(f"  {mark} {name:<17} — {detail}")
    n_pass = sum(1 for _, p, _ in results if p)
    n_total = len(results)
    if n_pass == n_total:
        _eprint(f"\nRESULT: {n_pass}/{n_total} passed")
    else:
        fails = ", ".join(name for name, p, _ in results if not p)
        _eprint(f"\nRESULT: {n_pass}/{n_total} passed — FAILED: {fails}")

    # Single machine-readable line on stdout: the full brain context.
    print(json.dumps(ctx.to_dict() if ctx is not None else {}, indent=2, default=str))
    return 0 if n_pass == n_total else 1


# -- individual checks (each returns (passed, detail)) ------------------------

def _check_connectivity(fetcher, epic, counter) -> tuple[bool, str]:
    before = counter.count
    bars = fetcher.get_history(epic, days=30)
    delta = counter.count - before
    ok = (
        len(bars) >= 20
        and all(b.high >= b.low and b.close > 0 for b in bars)
    )
    return ok, f"{len(bars)} daily bars, high>=low & close>0, network +{delta}"


def _check_daily_indicators(fetcher, epic, volume_proxy) -> tuple[bool, str]:
    vol = fetcher.get_volume_anomaly(epic)
    hl = fetcher.get_high_low_distance(epic)

    v_ok = vol is not None and math.isfinite(vol.z_score)
    if volume_proxy:
        v_ok = v_ok and vol.volume_available and bool(vol.volume_source) and vol.today_volume > 0
        v_detail = f"proxy {vol.volume_source}: available={vol.volume_available}, vol={vol.today_volume:.0f}, z={vol.z_score:.2f}"
    else:
        v_ok = v_ok and (vol.volume_available is False) and (vol.is_anomaly is False)
        v_detail = f"degrade: available={vol.volume_available}, is_anomaly={vol.is_anomaly}, z={vol.z_score:.2f}"

    h_ok = (
        hl is not None
        and hl.rolling_high >= hl.rolling_low
        and hl.distance_to_high_pct >= -1e-6   # -eps: fresh-ATH edge (current > rolling high)
        and hl.distance_to_low_pct >= -1e-6
        and hl.current_price > 0
    )
    h_detail = (
        f"high>=low={hl.rolling_high >= hl.rolling_low}, "
        f"d_high={hl.distance_to_high_pct:.2f}%, d_low={hl.distance_to_low_pct:.2f}%"
        if hl is not None else "high_low=None"
    )
    return (v_ok and h_ok), f"volume[{v_detail}] · high_low[{h_detail}]"


def _check_market_regime(fetcher, epic, market_open) -> tuple[bool, str]:
    drift = fetcher.get_drift(epic)
    momentum = fetcher.get_momentum(epic)
    bars = fetcher.get_bars(epic, resolution="5m", count=5)

    if market_open:
        present = drift is not None and momentum is not None and bars is not None and len(bars) > 0
        plausible = present and (
            abs(drift.drift_pct) < 10
            and abs(momentum.momentum_pct) < 5
            and momentum.is_realtime is False
        )
        detail = (
            f"open: drift={drift.drift_pct:.2f}%, momentum={momentum.momentum_pct:.2f}%, "
            f"is_realtime={momentum.is_realtime}, bars={None if bars is None else len(bars)}"
            if present else "open: one of drift/momentum/bars was None (unexpected)"
        )
        return plausible, detail

    # Market closed / weekend — all three intraday methods MUST be None (Decision 3).
    all_none = drift is None and momentum is None and bars is None
    return all_none, f"closed: drift/momentum/bars all None = {all_none} (expected)"


def _check_cache_hit(fetcher, epic, counter) -> tuple[bool, str]:
    # get_history(epic) was already fetched by the connectivity check → this repeat
    # must perform zero network calls.
    before = counter.count
    fetcher.get_history(epic, days=30)
    delta = counter.count - before
    return delta == 0, f"second get_history → network +{delta} (expect +0, served from cache)"


def _check_rate_limiter(counter) -> tuple[bool, str]:
    # Self-provision a fresh cache so the two probe fetches are GUARANTEED misses,
    # making this check robust to a warm cache from a prior run. (Concept §17.2 relied
    # on --clear-cache for this; we strengthen it to be cache-independent — two forced
    # misses on distinct always-available daily symbols, the limiter must space the two
    # real network calls by >= 0.5 s.)
    tmp_dir = tempfile.mkdtemp(prefix="p3_ratelimit_")
    try:
        probe = MarketDataFetcher(TickerMapper(), FileCache(tmp_dir))
        start = len(counter.times)
        probe.get_history(_SECONDARY_EPIC_A, days=5)   # ^DJI    — daily, always available
        probe.get_history(_SECONDARY_EPIC_B, days=5)   # EURUSD=X — daily, always available
        new_times = counter.times[start:]
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    if len(new_times) < 2:
        return False, f"expected 2 fresh network calls, saw {len(new_times)}"
    spacing = new_times[1] - new_times[0]
    return spacing >= 0.5 - 0.05, f"spacing between two misses = {spacing:.3f}s (expect >= 0.5)"


def _check_brain_context(fetcher, epic) -> tuple[bool, str]:
    ctx = fetcher.get_brain_context(epic)
    if ctx is None:
        return False, "get_brain_context returned None"
    prompt = ctx.to_prompt_dict()
    missing = _PROMPT_KEYS - set(prompt)
    ok = not missing
    return ok, ("all prompt keys present" if ok else f"missing keys: {sorted(missing)}")


if __name__ == "__main__":
    raise SystemExit(main())
