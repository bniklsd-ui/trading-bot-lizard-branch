#!/usr/bin/env python3
"""Read-only instrument-verification harness (v1.6 hotfix, Step 2 — the v3 seam).

Consolidates the two one-off tools the v1.5/v1.6 instrument-onboarding work relied on —
``scripts/resolve_epics.py`` (IG-side: does the epic exist, is it EUR, does it have
real-time bars for the momentum VETO) and ``phase3_external_data/scripts/smoke_test.py``
(yFinance-side: does the ticker actually serve daily/intraday data) — into **one**
machine-readable PASS/FAIL verdict per instrument, instead of two separately-run,
separately-read tools whose combined verdict a human has to assemble by hand.

**Why this exists (the v1.6 root cause, restated):** ``^FCHI``/``^IBEX`` went into
``EXTENDED_UNIVERSE`` as "well-known public symbols, not live-verified" — the yfinance side
was never actually checked with a tool before the live daemon hit it. This harness is the
fix to that *process* gap, not just the one incident: every instrument in the universe now
has a single, repeatable, machine-checkable verdict instead of a mix of "confirmed" /
"inferred" / "assumed" per field.

**v3 seam, documented but not built here:** a later semi-automatic research step
(``InstrumentSpec(source="research_promoted")``, reserved since v1.5 —
``phase4_research/research/models.py``) will want to gate a candidate instrument's
promotion on exactly this kind of verdict before it ever enters the live universe. The pure
check functions below (:func:`check_ig_side`, :func:`check_yf_side`, :func:`verdict_for`)
take duck-typed broker/fetcher arguments and do no I/O of their own, so that future
promotion pipeline can import them the same way the test suite already imports this
phase-less script — via ``importlib.util.spec_from_file_location`` (precedent:
``tests/test_diag_score_distribution.py`` / ``tests/test_resolve_epics.py``) — without this
needing to become an installable package. Not wired up now; v1.6 runs it manually
(operator).

**Read-only — no order, no writes.** Calls only ``get_market_info`` / ``get_ohlcv`` (broker,
both GETs) and ``get_history`` / ``get_bars`` / ``get_volume_anomaly`` (Phase-3 fetcher,
network reads). Never touches ``open_position`` / any persistence.

Checklist per instrument (the v1.6 "Was" plan §2 Step 2 acceptance criteria):
    - ``currency_eur``: IG ``get_market_info`` reports ``currency == "EUR"``.
    - ``min_deal_size_ok``: a positive ``min_deal_size`` is present.
    - ``ig_ohlcv_available``: a real-time bar probe returns at least one bar (the momentum
      VETO's actual data source — Phase-5 ``vetos.py``, never yFinance).
    - ``yf_daily_ok``: Phase-3 ``get_history`` returns non-empty daily bars.
    - ``yf_intraday_ok``: Phase-3 ``get_bars(resolution="5m")`` returns non-empty bars, OR
      the honest string ``"skipped(market closed)"`` when Phase-3 itself degrades to
      ``None`` off-hours (the P3 off-hours discipline — never scored as a failure).
    - ``volume_proxy_ok``: ``None`` when no ``volume_proxy`` is configured (not applicable,
      not a failure — concept C3, reduced-signal tolerated); else whether
      ``get_volume_anomaly().volume_available`` is ``True``.

A verdict is ``FAIL`` iff at least one check is boolean ``False`` — a skip string or a
``None`` (not-applicable) never fails it.

Output discipline (repo convention, mirrors ``resolve_epics.py`` / ``diag_score_distribution.py``):
human narrative -> **stderr**; machine-readable JSON -> **stdout**, always. Exit 0 in every
expected case (a report tool, not a pass/fail test runner); an unexpected error is not
swallowed.

Usage:
    python scripts/verify_instrument.py                          # the full EXTENDED_UNIVERSE
    python scripts/verify_instrument.py --epic IX.D.CAC.IFE.IP    # one known instrument
    python scripts/verify_instrument.py --epic IX.D.NEW.EPIC.IP --yf-ticker "^NEWIDX" \\
        --volume-proxy NEWETF.DE                                  # an ad-hoc new candidate
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Callable

# Mirrors resolve_epics.py / Phase-3's own RateLimiter minimum-spacing convention.
# 2026-07-04: IGAdapter._request also retries 429s itself now (Phase 1 hardening Step 1) —
# this pacing stays belt-and-braces (avoids 429s; the adapter retry survives them).
_DEFAULT_PACE_S = 0.6

# A tiny probe for real-time bar availability (the momentum VETO source, P5). Kept minimal,
# mirrors resolve_epics.py's own probe.
_OHLCV_RESOLUTION = "MINUTE_5"
_OHLCV_COUNT = 3

_REQUIRED_CURRENCY = "EUR"


def _eprint(message: str = "") -> None:
    print(message, file=sys.stderr)


def _ok(env: Any) -> bool:
    return bool(getattr(env, "ok", False))


def _data(env: Any) -> dict[str, Any]:
    return getattr(env, "data", None) or {}


def _error_message(env: Any) -> str | None:
    """Best-effort human-readable message from a not-ok Envelope's ``.error``."""
    err = getattr(env, "error", None)
    if err is None:
        return None
    if isinstance(err, dict):
        return err.get("message") or err.get("code") or str(err)
    return str(err)


# -- IG side --------------------------------------------------------------------------------

def check_ig_side(
    broker: Any,
    epic: str,
    *,
    sleep_fn: Callable[[float], None] = time.sleep,
    pace_s: float = _DEFAULT_PACE_S,
) -> dict[str, Any]:
    """Currency / min_deal_size / real-time-bar checks against the broker (read-only, paced).

    Fail-soft per sub-check: a broker error degrades that check to ``False`` (never raises),
    mirroring ``resolve_epics.resolve_epic``'s discipline so one bad instrument never aborts
    a multi-instrument run.
    """
    info_env = broker.get_market_info(epic)
    sleep_fn(pace_s)
    info = _data(info_env)
    info_ok = _ok(info_env)
    currency_eur = info_ok and info.get("currency") == _REQUIRED_CURRENCY
    min_deal_size = info.get("min_deal_size")
    min_deal_size_ok = info_ok and isinstance(min_deal_size, (int, float)) and min_deal_size > 0

    ohlcv_available = False
    try:
        ohlcv_env = broker.get_ohlcv(epic, _OHLCV_RESOLUTION, _OHLCV_COUNT)
        ohlcv_available = _ok(ohlcv_env) and bool(_data(ohlcv_env).get("bars"))
    except Exception:  # noqa: BLE001 — a probe must never crash the run
        ohlcv_available = False
    finally:
        sleep_fn(pace_s)

    return {
        "market_info_ok": info_ok,
        "market_info_error": None if info_ok else _error_message(info_env),
        "currency": info.get("currency"),
        "currency_eur": currency_eur,
        "min_deal_size": min_deal_size,
        "min_deal_size_ok": min_deal_size_ok,
        "ig_ohlcv_available": ohlcv_available,
    }


# -- yFinance side (Phase-3) ------------------------------------------------------------------

def check_yf_side(fetcher: Any, epic: str, *, volume_proxy: str | None = None) -> dict[str, Any]:
    """Daily / intraday / optional-volume-proxy checks against the Phase-3 fetcher.

    Reuses Phase-3's own off-hours honesty (``get_bars`` returns ``None`` outside market
    hours by design — ``fetcher.py``'s off-hours discipline) rather than re-implementing a
    market-hours check here: a ``None`` intraday result is reported as an honest skip, never
    a failure.
    """
    yf_daily_ok = False
    try:
        history = fetcher.get_history(epic, days=5)
        yf_daily_ok = bool(history)
    except Exception:  # noqa: BLE001 — a probe must never crash the run
        yf_daily_ok = False

    yf_intraday_ok: bool | str
    try:
        bars = fetcher.get_bars(epic, resolution="5m", count=5)
    except Exception:  # noqa: BLE001 — a real fetch failure (in-hours) is a genuine False
        yf_intraday_ok = False
    else:
        # A ``None`` return is Phase-3's own off-hours discipline (fetcher.py) — an honest
        # skip, never a failure. An empty-but-not-None list would be a genuine False.
        yf_intraday_ok = "skipped(market closed)" if bars is None else bool(bars)

    volume_proxy_ok: bool | None = None
    if volume_proxy is not None:
        try:
            va = fetcher.get_volume_anomaly(epic)
            volume_proxy_ok = bool(va is not None and getattr(va, "volume_available", False))
        except Exception:  # noqa: BLE001
            volume_proxy_ok = False

    return {
        "yf_daily_ok": yf_daily_ok,
        "yf_intraday_ok": yf_intraday_ok,
        "volume_proxy_ok": volume_proxy_ok,
    }


# -- verdict --------------------------------------------------------------------------------

def verdict_for(epic: str, ig_checks: dict[str, Any], yf_checks: dict[str, Any]) -> dict[str, Any]:
    """Combine the two check dicts into one PASS/FAIL verdict.

    A check fails the verdict **only** when its value is boolean ``False`` — a skip string
    (``"skipped(market closed)"``) or ``None`` (not applicable, e.g. no volume proxy
    configured) never fails it.
    """
    checks = {
        "currency_eur": ig_checks["currency_eur"],
        "min_deal_size_ok": ig_checks["min_deal_size_ok"],
        "ig_ohlcv_available": ig_checks["ig_ohlcv_available"],
        "yf_daily_ok": yf_checks["yf_daily_ok"],
        "yf_intraday_ok": yf_checks["yf_intraday_ok"],
        "volume_proxy_ok": yf_checks["volume_proxy_ok"],
    }
    failed_checks = [name for name, value in checks.items() if value is False]
    return {
        "epic": epic,
        "checks": checks,
        "verdict": "FAIL" if failed_checks else "PASS",
        "failed_checks": failed_checks,
    }


def verify_instrument(
    broker: Any,
    fetcher: Any,
    epic: str,
    *,
    volume_proxy: str | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    pace_s: float = _DEFAULT_PACE_S,
) -> dict[str, Any]:
    """Run both check sets for one instrument and return its verdict."""
    ig_checks = check_ig_side(broker, epic, sleep_fn=sleep_fn, pace_s=pace_s)
    yf_checks = check_yf_side(fetcher, epic, volume_proxy=volume_proxy)
    return verdict_for(epic, ig_checks, yf_checks)


def _format_report(results: list[dict[str, Any]]) -> str:
    """Human-readable narrative for stderr."""
    lines: list[str] = ["[verify] read-only instrument verification (no order, no writes)"]
    for r in results:
        if r["verdict"] == "PASS":
            lines.append(f"  {r['epic']}: PASS")
        else:
            lines.append(f"  {r['epic']}: FAIL (failed: {', '.join(r['failed_checks'])})")
    return "\n".join(lines)


def _default_targets() -> list[dict[str, Any]]:
    """The curated universe, epic + its configured ticker/proxy (lazy P4 import).

    Lazy so ``import scripts.verify_instrument``-style loading (the test suite) needs no
    network/broker/yfinance — only the call path touches Phase 4.
    """
    from research.models import EXTENDED_UNIVERSE

    return [
        {"epic": spec.epic, "yf_ticker": spec.yf_ticker, "volume_proxy": spec.volume_proxy}
        for spec in EXTENDED_UNIVERSE
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--broker", default="ig_demo", help="broker name (default: ig_demo — demo only)")
    parser.add_argument(
        "--epic", action="append", dest="epics", default=None,
        help="an IG epic to verify (repeatable); defaults to the full EXTENDED_UNIVERSE",
    )
    parser.add_argument(
        "--yf-ticker", default=None,
        help="yFinance symbol override — only valid with exactly one --epic (an ad-hoc new "
             "candidate not yet in ticker_map.py); an already-mapped --epic works without it",
    )
    parser.add_argument(
        "--volume-proxy", default=None,
        help="optional ETF volume-proxy symbol for the --epic override",
    )
    parser.add_argument(
        "--pace-s", type=float, default=_DEFAULT_PACE_S,
        help=f"seconds to sleep between broker calls (default: {_DEFAULT_PACE_S})",
    )
    parser.add_argument(
        "--cache-dir", default=None,
        help="yFinance cache dir (default: <repo_root>/data/cache, shared with Phase 3)",
    )
    args = parser.parse_args(argv)

    if args.epics:
        if args.yf_ticker is not None and len(args.epics) != 1:
            _eprint("[verify] --yf-ticker only applies when exactly one --epic is given.")
            print(json.dumps({"broker": args.broker, "connected": False, "results": []}, indent=2))
            return 0
        targets = [
            {"epic": epic, "yf_ticker": args.yf_ticker, "volume_proxy": args.volume_proxy}
            for epic in args.epics
        ]
    else:
        targets = _default_targets()

    # Lazy imports so `import scripts.verify_instrument` (unit tests) needs no
    # broker/keyring/network/yfinance — only main() touches them.
    from broker_wrapper import get_broker
    from external_data.cache import FileCache
    from external_data.fetcher import MarketDataFetcher
    from external_data.ticker_map import TickerMapper

    repo_root = Path(__file__).resolve().parent.parent
    cache_dir = args.cache_dir or str(repo_root / "data" / "cache")

    broker = get_broker(args.broker)
    connect_env = broker.connect()
    if not _ok(connect_env):
        _eprint(f"[verify] broker connect failed for {args.broker!r} — cannot verify.")
        print(json.dumps({"broker": args.broker, "connected": False, "results": []}, indent=2))
        return 0

    mapper = TickerMapper()
    for t in targets:
        if t["yf_ticker"] is not None:
            mapper.register(t["epic"], t["yf_ticker"])
        if t["volume_proxy"] is not None:
            mapper.register_volume_proxy(t["epic"], t["volume_proxy"])
    fetcher = MarketDataFetcher(mapper, FileCache(cache_dir))

    results = [
        verify_instrument(
            broker, fetcher, t["epic"], volume_proxy=t["volume_proxy"], pace_s=args.pace_s
        )
        for t in targets
    ]

    _eprint(_format_report(results))
    print(json.dumps({"broker": args.broker, "connected": True, "results": results}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
