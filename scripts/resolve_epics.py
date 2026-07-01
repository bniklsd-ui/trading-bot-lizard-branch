#!/usr/bin/env python3
"""Read-only IG-demo epic resolver (v1.5 hotfix, Step 2 / Issue C — variety).

Resolves the curated multi-instrument shortlist (DAX + Euro Stoxx 50 + CAC 40 [+ AEX /
IBEX 35]) to their **exact IG-demo epic strings** and per-instrument facts, so the operator
can populate the typed research universe (``research.models.InstrumentSpec``) and the P5
``ExecutionConfig.point_values`` map **without guessing** — exactly how ``IX.D.DAX.IFMM.IP``
was confirmed in Phase 1.

For each search term it runs ``broker.search_markets`` and, for each hit, ``get_market_info``
(currency / min_deal_size / lot_size / status) and a tiny ``get_ohlcv`` probe (are real-time
bars available for the momentum VETO?). It prints per hit: ``epic``, ``instrumentName``,
``currency``, ``min_deal_size``, ``lot_size``, ``market_status`` and ``ohlcv_available``.

**Read-only — no order, no writes.** It calls only ``search_markets`` / ``get_market_info``
/ ``get_ohlcv`` (all GETs). It never touches ``open_position`` / ``close_position`` / any
persistence. Decision-5 consistency: ``search_markets`` is used here purely as a **one-time
setup resolver**, NOT as a runtime universe selector (the runtime universe stays the
code-curated ``InstrumentSpec`` list — no dragnet).

⚠ **Point value is NOT resolved here.** IG's ``get_market_info`` does not expose the
account-currency value of one index point; ``lot_size`` is surfaced as a hint only. The
operator confirms each instrument's point value from IG's contract details / a manual demo
trade and enters it into ``InstrumentSpec.point_value`` + ``ExecutionConfig.point_values``.

⚠ **Paced by default (fixed 2026-07-01, found via the first live run).** ``IGAdapter`` raises
``RateLimitError`` on HTTP 429 with no built-in retry/backoff (the caller decides), and a
5-term run makes ~35+ back-to-back REST calls (search + get_market_info + get_ohlcv per hit).
The first unpaced run showed exactly the rate-limit failure signature at the tail: 3/4 hits
for "France 40" failed ``get_market_info`` outright, the one that resolved had
``ohlcv_available=False``, and the next two search terms failed completely. A short sleep
between every broker call (``--pace-s``, default 0.6s — matches Phase-3's own
``RateLimiter`` minimum spacing convention) fixes this; injectable ``sleep_fn`` keeps unit
tests instant.

The live run is the **operator's** job (keyring + network — project rule). This module's
resolution functions take a **duck-typed broker** so they are unit-testable offline with a
fake; only ``main()`` builds the real ``ig_demo`` broker (imported lazily).

Output discipline (repo convention, mirrors ``diag_score_distribution.py`` /
``inspect_history.py``): human narrative -> **stderr**; machine-readable JSON -> **stdout**,
always. Exit 0 in every expected case (a report tool); an unexpected error is not swallowed.

Usage:
    python scripts/resolve_epics.py
    python scripts/resolve_epics.py --term "France 40" --term "Netherlands 25" --term "Spain 35"
    python scripts/resolve_epics.py --pace-s 1.0   # slower, if 0.6s still trips a limit
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any, Callable

# The locked v1.5 shortlist (concept: 3-4 curated liquid EUR index CFDs). DAX is already
# confirmed (IX.D.DAX.IFMM.IP) — included so the operator sees it resolve the same way.
_DEFAULT_TERMS: tuple[str, ...] = (
    "Germany 40",       # DAX (already confirmed — sanity)
    "EU Stocks 50",     # Euro Stoxx 50
    "France 40",        # CAC 40
    "Netherlands 25",   # AEX (optional)
    "Spain 35",         # IBEX 35 (optional)
)

# A tiny probe for real-time bar availability (the momentum VETO source, P5). Kept minimal
# so the resolver is cheap; the real VETO uses MINUTE_5 × 12.
_OHLCV_RESOLUTION = "MINUTE_5"
_OHLCV_COUNT = 3

# Default pacing between broker calls — matches Phase-3's own RateLimiter minimum spacing
# (external_data/fetcher.py) as the repo's established "be gentle with a broker/data API"
# convention. See the module docstring for why this exists.
_DEFAULT_PACE_S = 0.6


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


def probe_ohlcv(
    broker: Any, epic: str, *, sleep_fn: Callable[[float], None] = time.sleep, pace_s: float = _DEFAULT_PACE_S
) -> bool:
    """Return True if a small ``get_ohlcv`` probe yields at least one bar (fail-soft)."""
    try:
        env = broker.get_ohlcv(epic, _OHLCV_RESOLUTION, _OHLCV_COUNT)
    except Exception:  # noqa: BLE001 — a resolver probe must never crash the run
        return False
    finally:
        sleep_fn(pace_s)
    if not _ok(env):
        return False
    return bool(_data(env).get("bars"))


def resolve_epic(
    broker: Any, epic: str, *, sleep_fn: Callable[[float], None] = time.sleep, pace_s: float = _DEFAULT_PACE_S
) -> dict[str, Any]:
    """Resolve one epic's tradeable facts via ``get_market_info`` + an OHLCV probe.

    Read-only. Returns a stable dict; missing/failed fields degrade to ``None``/``False``
    rather than raising, so one bad epic never aborts the whole resolution. Paced (see
    module docstring) — a sleep follows both broker calls this makes.
    """
    info_env = broker.get_market_info(epic)
    sleep_fn(pace_s)
    info = _data(info_env)
    return {
        "epic": epic,
        "market_info_ok": _ok(info_env),
        "market_info_error": None if _ok(info_env) else _error_message(info_env),
        "name": info.get("name"),
        "instrument_type": info.get("instrument_type"),
        "currency": info.get("currency"),
        "min_deal_size": info.get("min_deal_size"),
        "lot_size": info.get("lot_size"),  # hint only — NOT the point value (see docstring)
        "market_status": info.get("market_status"),
        "ohlcv_available": probe_ohlcv(broker, epic, sleep_fn=sleep_fn, pace_s=pace_s),
    }


def resolve_term(
    broker: Any, term: str, *, sleep_fn: Callable[[float], None] = time.sleep, pace_s: float = _DEFAULT_PACE_S
) -> dict[str, Any]:
    """Search one term and resolve every hit (read-only). Fail-soft on a bad search."""
    try:
        search_env = broker.search_markets(term)
    except Exception as exc:  # noqa: BLE001
        return {"term": term, "search_ok": False, "error": str(exc), "hits": []}
    finally:
        sleep_fn(pace_s)
    if not _ok(search_env):
        return {"term": term, "search_ok": False, "error": _error_message(search_env), "hits": []}

    results = _data(search_env).get("results", []) or []
    hits = [
        resolve_epic(broker, r["epic"], sleep_fn=sleep_fn, pace_s=pace_s)
        for r in results if r.get("epic")
    ]
    return {"term": term, "search_ok": True, "error": None, "hits": hits}


def resolve_all(
    broker: Any,
    terms: tuple[str, ...],
    *,
    sleep_fn: Callable[[float], None] = time.sleep,
    pace_s: float = _DEFAULT_PACE_S,
) -> list[dict[str, Any]]:
    """Resolve every search term into its hits (read-only, paced)."""
    return [resolve_term(broker, term, sleep_fn=sleep_fn, pace_s=pace_s) for term in terms]


def _format_report(report: list[dict[str, Any]]) -> str:
    """Human-readable narrative for stderr."""
    lines: list[str] = ["[resolve] read-only epic resolution (no order, no writes)"]
    for block in report:
        term = block["term"]
        if not block["search_ok"]:
            lines.append(f"[resolve] {term!r}: search FAILED ({block.get('error')})")
            continue
        if not block["hits"]:
            lines.append(f"[resolve] {term!r}: no hits")
            continue
        lines.append(f"[resolve] {term!r}: {len(block['hits'])} hit(s)")
        for h in block["hits"]:
            if not h["market_info_ok"]:
                lines.append(f"    {h['epic']}  | get_market_info FAILED ({h.get('market_info_error')})")
                continue
            lines.append(
                f"    {h['epic']}  | {h.get('name')!r} | {h.get('currency')} | "
                f"min={h.get('min_deal_size')} lot={h.get('lot_size')} | "
                f"{h.get('market_status')} | ohlcv={'yes' if h['ohlcv_available'] else 'no'}"
            )
    lines.append("[resolve] NOTE: point_value is NOT resolved here — confirm it manually per instrument.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--broker", default="ig_demo", help="broker name (default: ig_demo — demo only)")
    parser.add_argument(
        "--term", action="append", dest="terms", default=None,
        help="a search term to resolve (repeatable); defaults to the curated shortlist",
    )
    parser.add_argument(
        "--pace-s", type=float, default=_DEFAULT_PACE_S,
        help=f"seconds to sleep between broker calls (default: {_DEFAULT_PACE_S}) — raise this "
             "if a run still shows rate-limit-shaped failures (get_market_info FAILED / "
             "ohlcv=no / search FAILED clustered near the end of the run)",
    )
    args = parser.parse_args(argv)
    terms = tuple(args.terms) if args.terms else _DEFAULT_TERMS

    # Lazy import so `import scripts.resolve_epics` (unit tests) needs no broker/keyring/network.
    from broker_wrapper import get_broker

    broker = get_broker(args.broker)
    connect_env = broker.connect()
    if not _ok(connect_env):
        _eprint(f"[resolve] broker connect failed for {args.broker!r} — cannot resolve.")
        print(json.dumps({"broker": args.broker, "connected": False, "report": []}, indent=2))
        return 0

    report = resolve_all(broker, terms, pace_s=args.pace_s)
    _eprint(_format_report(report))
    print(json.dumps({"broker": args.broker, "connected": True, "report": report}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
