"""Seed-term sweep + code filter — the "discover" half of discover->verify->promote.

Rein deterministisch (Decision D3, kein LLM): eine kuratierte Longlist von
Such**begriffen** (nicht Epics!) wird per ``broker.search_markets`` durchsucht;
jeder Treffer wird per ``broker.get_market_info`` aufgelöst und gegen Code-Kriterien
gefiltert (EUR, Index-CFD, TRADEABLE, Kassa-Variante bei Mehrfachtreffern,
min_deal_size > 0). Neue Epics landen als ``STATUS_DISCOVERED`` in der
``UniverseStore``; ``pricing.py`` (Step 2)/``promotion.py`` (Step 4) verifizieren/
aktivieren sie später — dieses Modul schreibt nur ``discovered``, nie ``active``.

Mirrors ``scripts/resolve_epics.py``'s call chain (``search_markets`` ->
``get_market_info`` per hit, paced), but is a **repeatable pipeline step**, not a
one-off operator resolver: unlike ``resolve_epics.py`` (Decision-5 consistency —
"search_markets is a one-time setup resolver, NOT a runtime universe selector"),
this module *is* the sanctioned runtime discovery step the plan's D3 introduces.
That is not a contradiction: ``resolve_epics.py`` predates the discover/verify/
promote pipeline and was explicitly a stopgap (its own docstring says so); this
module is the real thing D3 asked for.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from universe.models import SOURCE_RESEARCH_PROMOTED, STATUS_DISCOVERED, UniverseRecord
from universe.store import UniverseStore, utc_iso_now

# Curated seed longlist of search TERMS (not epics) — both German and English market
# names, because the IG-demo search is account-language-dependent (a German demo
# account returns German names like "Kassa"). A dead term only costs one paced call;
# the currency filter is the real gate for non-EUR hits (US/UK/CH), not this list.
SEARCH_TERMS: tuple[str, ...] = (
    "Germany 40",
    "Deutschland 40",
    "Europe 50",
    "France 40",
    "Frankreich 40",
    "Spain 35",
    "Spanien 35",
    "Netherlands 25",
    "Niederlande 25",
    "Italy 40",
    "Italien 40",
    "Switzerland 20",
    "Schweiz 20",
    "Sweden 30",
    "US 500",
    "US Tech 100",
    "Wall Street",
    "UK 100",
)

# Static name-pattern -> yFinance ticker mapping (no AI, no guessing — an unmatched
# name resolves to yf_ticker=None, tolerated as reduced-signal, Konzept C3).
KNOWN_YF_TICKERS: tuple[tuple[str, str], ...] = (
    ("Germany 40", "^GDAXI"),
    ("Deutschland 40", "^GDAXI"),
    ("Europe 50", "^STOXX50E"),
    ("EU Stocks 50", "^STOXX50E"),
    ("France 40", "^FCHI"),
    ("Frankreich 40", "^FCHI"),
    ("Spain 35", "^IBEX"),
    ("Spanien 35", "^IBEX"),
    ("Netherlands 25", "^AEX"),
    ("Niederlande 25", "^AEX"),
    ("Italy 40", "FTSEMIB.MI"),
    ("Italien 40", "FTSEMIB.MI"),
)

# Static name-pattern -> ETF volume-proxy ticker mapping. Deliberately sparse — no
# guessing an ETF ticker for an index without one confidently known (v1.5 principle).
KNOWN_VOLUME_PROXIES: tuple[tuple[str, str], ...] = (
    ("Germany 40", "EXS1.DE"),
    ("Deutschland 40", "EXS1.DE"),
    ("Europe 50", "EXW1.DE"),
    ("EU Stocks 50", "EXW1.DE"),
)


def _lookup(name: str, table: tuple[tuple[str, str], ...]) -> str | None:
    """First case-insensitive substring match in ``table``, or ``None``."""
    lowered = name.lower()
    for pattern, value in table:
        if pattern.lower() in lowered:
            return value
    return None


@dataclass
class DiscoveryReport:
    """Outcome of one :func:`discover` sweep."""

    terms_searched: int = 0
    hits: int = 0
    new: list[str] = field(default_factory=list)
    skipped_known: int = 0
    filtered: dict[str, int] = field(default_factory=dict)


def _ok(env: Any) -> bool:
    return bool(getattr(env, "ok", False))


def _data(env: Any) -> dict[str, Any]:
    return getattr(env, "data", None) or {}


def _bump(filtered: dict[str, int], reason: str) -> None:
    filtered[reason] = filtered.get(reason, 0) + 1


def _is_kassa_preferred(hit: dict[str, Any], siblings: list[dict[str, Any]]) -> bool:
    """True if ``hit`` is the Kassa (spot/cash) variant among same-term ``siblings``.

    Heuristic (codifies the documented DAX/STXE selection pattern, concept §"Kassa-
    Präferenz"): a name containing "forward" is never preferred when a
    non-forward sibling exists; among the remaining candidates the smallest
    ``lot_size`` wins (mirrors the "(1€) beats (2€)" DAX/STXE pattern).
    """
    name = (hit.get("name") or "").lower()
    is_forward = "forward" in name
    non_forward_siblings = [s for s in siblings if "forward" not in (s.get("name") or "").lower()]
    if non_forward_siblings and is_forward:
        return False
    candidates = non_forward_siblings if non_forward_siblings else siblings
    min_lot = min(
        (c.get("lot_size") for c in candidates if c.get("lot_size") is not None),
        default=None,
    )
    return hit.get("lot_size") == min_lot


def _passes_code_filter(
    hit: dict[str, Any], siblings: list[dict[str, Any]], filtered: dict[str, int]
) -> bool:
    """Apply every discovery criterion; bump ``filtered[reason]`` on the first failure."""
    if not hit.get("market_info_ok"):
        _bump(filtered, "market_info_fail")
        return False
    if hit.get("currency") != "EUR":
        _bump(filtered, "currency")
        return False
    if "INDICES" not in (hit.get("instrument_type") or "").upper():
        _bump(filtered, "instrument_type")
        return False
    if hit.get("market_status") != "TRADEABLE":
        _bump(filtered, "market_status")
        return False
    min_deal_size = hit.get("min_deal_size")
    if not min_deal_size or min_deal_size <= 0:
        _bump(filtered, "min_deal_size")
        return False
    if len(siblings) > 1 and not _is_kassa_preferred(hit, siblings):
        _bump(filtered, "kassa_variant")
        return False
    return True


def _resolve_hit(
    broker: Any, epic: str, *, sleep_fn: Callable[[float], None], pace_s: float
) -> dict[str, Any]:
    """One ``get_market_info`` probe, paced. Fail-soft — never raises."""
    try:
        env = broker.get_market_info(epic)
    except Exception:  # noqa: BLE001 — one bad epic must never kill the sweep
        return {"epic": epic, "market_info_ok": False}
    finally:
        sleep_fn(pace_s)
    info = _data(env)
    return {
        "epic": epic,
        "market_info_ok": _ok(env),
        "name": info.get("name"),
        "instrument_type": info.get("instrument_type"),
        "currency": info.get("currency"),
        "min_deal_size": info.get("min_deal_size"),
        "lot_size": info.get("lot_size"),
        "market_status": info.get("market_status"),
    }


def discover(
    broker: Any,
    store: UniverseStore,
    *,
    search_terms: tuple[str, ...] = SEARCH_TERMS,
    pace_s: float = 1.0,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> DiscoveryReport:
    """Sweep ``search_terms`` via the broker and persist newly-discovered epics.

    Fail-soft per term (one 500 never kills the whole sweep — mirrors
    ``resolve_epics.resolve_term``'s discipline). Already-known epics (any status)
    are skipped, never overwritten. Paced 1.0s default between broker calls (the
    confirmed anti-rate-limit spacing from the v1.5 hotfix's ``resolve_epics.py``
    fix, at the more conservative end since discovery makes far more calls than a
    one-off operator resolver).
    """
    report = DiscoveryReport()
    for term in search_terms:
        report.terms_searched += 1
        try:
            search_env = broker.search_markets(term)
        except Exception:  # noqa: BLE001 — fail-soft per term
            sleep_fn(pace_s)
            continue
        sleep_fn(pace_s)
        if not _ok(search_env):
            continue

        results = _data(search_env).get("results", []) or []
        epics = [r["epic"] for r in results if r.get("epic")]
        hits = [
            _resolve_hit(broker, epic, sleep_fn=sleep_fn, pace_s=pace_s) for epic in epics
        ]
        report.hits += len(hits)

        for hit in hits:
            epic = hit["epic"]
            if store.get(epic) is not None:
                report.skipped_known += 1
                continue
            if not _passes_code_filter(hit, hits, report.filtered):
                continue

            now = utc_iso_now()
            name = hit.get("name") or ""
            record = UniverseRecord(
                epic=epic,
                name=name,
                yf_ticker=_lookup(name, KNOWN_YF_TICKERS),
                volume_proxy=_lookup(name, KNOWN_VOLUME_PROXIES),
                point_value=None,
                point_value_source=None,
                min_deal_size=hit.get("min_deal_size"),
                currency=hit["currency"],
                status=STATUS_DISCOVERED,
                source=SOURCE_RESEARCH_PROMOTED,
                checks={},
                fail_count=0,
                data_degraded=False,
                last_verified_at=None,
                created_at=now,
                updated_at=now,
            )
            store.upsert_discovered(record)
            report.new.append(epic)

    return report
