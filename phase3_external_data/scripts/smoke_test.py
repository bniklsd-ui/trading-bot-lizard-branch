#!/usr/bin/env python3
"""Quick live sanity check for the Phase 3 external-data layer (concept §17.1).

Drives the whole fetcher pipeline once against **real yFinance** and prints the
research prompt-dict. It *prints, it does not hard-assert* — the hard-assert /
PASS-FAIL verification with an exit code is ``scripts/live_test.py`` (Step 10).

This is a **live** script: it touches the network, is non-deterministic, needs no IG
account, and is deliberately not collected by ``pytest`` / CI. Run it manually.

Convention (concept §17): human-readable progress goes to **stderr**; the single
machine-readable JSON (the prompt-dict) goes to **stdout**.

Usage:
    python scripts/smoke_test.py
    python scripts/smoke_test.py --epic IX.D.DAX.IFMM.IP --volume-proxy EXS1.DE
    python scripts/smoke_test.py --verbose
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Make the `external_data` package importable when run as a script (Phase-2 pattern).
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent  # phase3_external_data/
sys.path.insert(0, str(_PACKAGE_ROOT))

from external_data import FileCache, MarketDataFetcher, TickerMapper  # noqa: E402
from external_data.exceptions import ExternalDataError  # noqa: E402
from external_data.market_hours import is_market_open  # noqa: E402

_REPO_ROOT = _PACKAGE_ROOT.parent
_DEFAULT_CACHE_DIR = _REPO_ROOT / "data" / "cache"

log = logging.getLogger("phase3.smoke_test")


def _eprint(message: str = "") -> None:
    """Print a human-facing line to stderr (stdout is reserved for the JSON)."""
    print(message, file=sys.stderr)


def _run(label: str, fn):
    """Call ``fn`` and print a one-line stderr status; never abort the run.

    A smoke run shouldn't die because one method hit a transient 429 — an
    :class:`ExternalDataError` is reported and turned into ``None`` so the remaining
    methods still execute.
    """
    try:
        result = fn()
    except ExternalDataError as exc:
        _eprint(f"  {label:<16}: ERROR {type(exc).__name__}: {exc}")
        return None
    _eprint(f"  {label:<16}: {_summarize(result)}")
    return result


def _summarize(result) -> str:
    """Compact human rendering — lists collapse to a length, everything else repr's."""
    if result is None:
        return "None"
    if isinstance(result, list):
        return f"{len(result)} bars"
    return repr(result)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 3 external-data smoke test (live yFinance, prints only)."
    )
    parser.add_argument(
        "--epic", default="IX.D.DAX.IFMM.IP",
        help="IG epic to fetch (default: %(default)s)",
    )
    parser.add_argument(
        "--volume-proxy", default=None, metavar="YF_SYMBOL",
        help="optional ETF volume proxy, e.g. EXS1.DE (iShares Core DAX)",
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

    mapper = TickerMapper()
    if args.volume_proxy:
        mapper.register_volume_proxy(args.epic, args.volume_proxy)
    cache = FileCache(args.cache_dir)
    fetcher = MarketDataFetcher(mapper, cache)

    market_open = is_market_open()
    _eprint(
        f"epic={args.epic}  yf={mapper.epic_to_yf(args.epic)}  "
        f"market_open={market_open}  volume_proxy={args.volume_proxy or '—'}"
    )
    if not market_open:
        _eprint(
            "market closed → intraday methods (drift/momentum/5m bars) return None; "
            "daily methods (history/volume/high_low) still produce values. Expected, "
            "not an error."
        )

    _eprint("methods:")
    _run("drift", lambda: fetcher.get_drift(args.epic))
    _run("momentum_15m", lambda: fetcher.get_momentum(args.epic))
    _run("bars(5m,5)", lambda: fetcher.get_bars(args.epic, resolution="5m", count=5))
    _run("history(30d)", lambda: fetcher.get_history(args.epic, days=30))
    _run("volume_anomaly", lambda: fetcher.get_volume_anomaly(args.epic))
    _run("high_low", lambda: fetcher.get_high_low_distance(args.epic))

    ctx = _run("brain_context", lambda: fetcher.get_brain_context(args.epic))

    # Single machine-readable line on stdout: the LLM-facing prompt dict.
    prompt = ctx.to_prompt_dict() if ctx is not None else {}
    print(json.dumps(prompt, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
