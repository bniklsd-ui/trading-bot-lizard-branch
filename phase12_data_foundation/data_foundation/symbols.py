"""``SymbolResolver`` — derived + code-verified epic -> yFinance symbol mapping (D5/D6).

Replaces the three divergent, hand-declared symbol tables (discovery's old static table,
``instrument_universe.yf_ticker``, ``TickerMapper._MAP``) with one: the registry
(``instrument_universe``, via ``UniverseStore``) is the single writer of ``yf_ticker``
(``UniverseStore.set_symbol``, the only caller), and a symbol only becomes trusted after
a deterministic price comparison against IG's own snapshot — never declared, never
guessed by an LLM (Bauprinzip, Plan §1: "Kein LLM in dieser Phase").

``SEED_SYMBOL_CANDIDATES`` is not a mapping the resolver trusts blindly — it is the
longlist of *candidates* :func:`candidates_for` proposes for a newly-discovered name; a
candidate only earns ``data_source_status='ok'`` after :func:`price_agreement` passes
against a live IG snapshot (D6). This module never touches ``instrument_universe``
directly — it is handed a duck-typed ``store`` (``UniverseStore``-shaped: ``get``,
``list_by_status``, ``set_symbol``) so it stays phase-isolated (D3): no cross-phase
import of ``universe.*`` at module top.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

from data_foundation.exceptions import ResolverError

# Registry status vocabulary (mirrors universe.models — duplicated, not imported, for the
# same phase-isolation reason data_foundation.models duplicates it; D3).
DS_OK = "ok"
DS_UNVERIFIED = "unverified"
DS_NO_SOURCE = "no_source"
DS_NO_INTRADAY_SOURCE = "no_intraday_source"
DS_MISMATCH = "mismatch"

SYMBOL_SOURCE_SEED = "seed"
SYMBOL_SOURCE_RESOLVER = "resolver"
SYMBOL_SOURCE_OPERATOR = "operator"

_STATUS_ACTIVE = "active"
_STATUS_DISCOVERED = "discovered"

# Seed candidate table (verbatim discovery's former static symbol table, D5) plus the
# four search-term classes ``discovery.SEARCH_TERMS`` already sweeps but that never had a
# yFinance mapping (weekday indices that are not the DAX/CAC/IBEX/AEX/MIB/STXE core).
SEED_SYMBOL_CANDIDATES: tuple[tuple[str, str], ...] = (
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
    ("US 500", "^GSPC"),
    ("US Tech 100", "^NDX"),
    ("Wall Street", "^DJI"),
    ("UK 100", "^FTSE"),
)

_WEEKEND_SPECIAL_INFO_SUBSTR = "weekend instrument"
_WEEKEND_NAME_SUBSTRINGS = ("wochenend", "weekend")


def candidates_for(name: str | None) -> list[str]:
    """Case-insensitive substring matches against :data:`SEED_SYMBOL_CANDIDATES`, in
    table order. Empty when ``name`` is falsy or matches nothing — never guesses."""
    if not name:
        return []
    lowered = name.lower()
    return [symbol for pattern, symbol in SEED_SYMBOL_CANDIDATES if pattern.lower() in lowered]


def is_weekend_instrument(
    name: str | None, market_info: Mapping[str, Any] | None, *, epic: str | None = None
) -> bool:
    """Whether an instrument only trades in IG's synthetic weekend window (D7 — such an
    epic structurally has no yFinance intraday source and is typed ``no_intraday_source``,
    never ``no_source``).

    Signal order (Step-0a live finding, 2026-08-11): primary is a literal "weekend
    instrument" substring in ``market_info['specialInfo']`` — the reliable signal, since a
    restricted-hours *weekday* instrument could in principle also carry non-null
    ``openingHours`` without being a weekend instrument. Secondary: ``openingHours`` is
    populated at all (``None`` for every normal weekday instrument, per the same live
    check). **Neither is reachable from ``resolve_epic`` today** — ``get_market_info``
    (the only market-info source wired into ``UniverseRecord``) projects both fields away
    (Step-0a finding, ``ig_adapter.py:479-513``); a raw ``/markets`` call would be needed
    to populate them. Until that exists, every call passes ``market_info=None`` and only
    the fallback runs: a "wochenend"/"weekend" substring in ``name``, or a ``SUN`` epic
    segment (live-confirmed 2026-08-15 against production: all four active weekend rows —
    ``IX.D.SUNDAX.*``/``IX.D.SUNNAS.*``/``IX.D.SUNDOW.*``/``IX.D.SUNFUN.*`` — carry
    "Wochenend" in ``name`` already, so the fallback alone covers today's universe).
    """
    if market_info:
        special_info = str(market_info.get("specialInfo") or "").lower()
        if _WEEKEND_SPECIAL_INFO_SUBSTR in special_info:
            return True
        if market_info.get("openingHours") is not None:
            return True
    if name and any(substr in name.lower() for substr in _WEEKEND_NAME_SUBSTRINGS):
        return True
    if epic and any(segment.startswith("SUN") for segment in epic.upper().split(".")):
        return True
    return False


def price_agreement(ig_mid: float, yf_last: float, *, tolerance_pct: float = 2.0) -> bool:
    """Whether ``yf_last`` is within ``tolerance_pct`` percent of ``ig_mid``.

    A non-positive ``ig_mid`` can never agree with anything (guards a degenerate
    snapshot from producing a division by zero or a meaningless ratio).
    """
    if ig_mid <= 0:
        return False
    return abs(ig_mid - yf_last) / ig_mid * 100.0 <= tolerance_pct


def _default_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(ts: str) -> datetime:
    normalized = ts.replace("Z", "+00:00") if ts.endswith("Z") else ts
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@dataclass
class ResolverReport:
    """Outcome of one :meth:`SymbolResolver.resolve_universe` pass."""

    checked: int = 0
    verified: list[str] = field(default_factory=list)
    no_source: list[str] = field(default_factory=list)
    no_intraday: list[str] = field(default_factory=list)
    mismatch: list[str] = field(default_factory=list)
    unverified: list[str] = field(default_factory=list)


class SymbolResolver:
    """Derives + verifies ``yf_ticker`` for every active/discovered ``instrument_universe``
    row (D6), one deterministic decision per epic — never raises out of
    :meth:`resolve_universe` (fail-soft per epic, mirrors ``promotion.run_promotion_cycle``).

    ``quote_fetch(epic)`` returns an IG ``Price``-shaped mapping (``broker.get_price().data``
    — keys ``bid``/``ask``, **no** ``mid`` field; this class computes ``(bid+ask)/2``
    itself). ``yf_last_fetch(symbol)`` returns ``(price, bar_timestamp_iso) | None``
    (``MarketDataFetcher.get_last_price``'s shape) or raises — a raise is treated exactly
    like ``None`` (yFinance-side failure never crashes a resolve pass, Konzept C3).

    Liveness gate (N1, both required — a Nikinger decision that deliberately goes further
    than the XETRA-only ``market_open_fn`` D6 names): a comparison is only booked when the
    market is open *and* the yFinance bar is fresher than ``max_yf_age_min``. Without the
    second half, a stale (e.g. previous-close) yFinance bar compared against IG's live
    24h-CFD price would repeatedly disagree on a real gap day and wrongly stamp
    ``mismatch``.
    """

    def __init__(
        self,
        store: Any,
        quote_fetch: Callable[[str], Mapping[str, float]],
        yf_last_fetch: Callable[[str], tuple[float, str] | None],
        *,
        market_open_fn: Callable[[], bool] | None = None,
        max_yf_age_min: int = 30,
        now_fn: Callable[[], datetime] = _default_now,
    ) -> None:
        self._store = store
        self._quote_fetch = quote_fetch
        self._yf_last_fetch = yf_last_fetch
        self._max_yf_age_min = max_yf_age_min
        self._now_fn = now_fn
        if market_open_fn is None:
            from external_data.market_hours import is_market_open as market_open_fn  # lazy, D3
        self._market_open_fn = market_open_fn

    def resolve_epic(self, rec: Any) -> str:
        """Resolve one ``UniverseRecord``-shaped ``rec``. Returns the resulting
        ``data_source_status`` (also the value written to the store, unless the branch is
        the "we learned nothing" no-op). A ``quote_fetch``/``yf_last_fetch`` failure
        degrades to "no signal this pass", same as a closed market — the only exception
        this method itself raises is :class:`ResolverError` for a malformed yFinance bar
        timestamp (a caller-must-see programmer-error case, not a normal degrade path).
        A ``store.set_symbol`` failure (e.g. the epic vanished mid-pass) is **not** caught
        here — :meth:`resolve_universe` is the fail-soft-per-epic boundary.
        """
        if is_weekend_instrument(rec.name, None, epic=rec.epic):
            if rec.data_source_status != DS_NO_INTRADAY_SOURCE:
                self._store.set_symbol(
                    rec.epic, rec.yf_ticker, symbol_source=rec.symbol_source, status=DS_NO_INTRADAY_SOURCE
                )
            return DS_NO_INTRADAY_SOURCE

        is_operator = rec.symbol_source == SYMBOL_SOURCE_OPERATOR
        candidate = rec.yf_ticker
        if candidate is None and not is_operator:
            matches = candidates_for(rec.name)
            candidate = matches[0] if matches else None

        if candidate is None:
            if rec.data_source_status != DS_NO_SOURCE:
                self._store.set_symbol(rec.epic, None, symbol_source=None, status=DS_NO_SOURCE)
            return DS_NO_SOURCE

        try:
            if not self._market_open_fn():
                return rec.data_source_status  # market closed — we learned nothing
            quote = self._quote_fetch(rec.epic)
            bid, ask = float(quote["bid"]), float(quote["ask"])
            ig_mid = (bid + ask) / 2.0
            yf_result = self._yf_last_fetch(candidate)
        except Exception:  # noqa: BLE001 — a fetch failure is "learned nothing", not a crash
            return rec.data_source_status

        if yf_result is None:
            return rec.data_source_status
        yf_last, yf_ts = yf_result
        try:
            age_min = (self._now_fn() - _parse_iso(yf_ts)).total_seconds() / 60.0
        except ValueError as exc:
            raise ResolverError(f"unparseable yFinance bar timestamp: {yf_ts!r}") from exc
        if age_min > self._max_yf_age_min:
            return rec.data_source_status  # stale bar — we learned nothing

        symbol_source = rec.symbol_source or (
            SYMBOL_SOURCE_SEED if rec.yf_ticker == candidate else SYMBOL_SOURCE_RESOLVER
        )

        if price_agreement(ig_mid, yf_last):
            self._store.set_symbol(rec.epic, candidate, symbol_source=symbol_source, status=DS_OK)
            return DS_OK

        # Disagreement: no counter column (a would-be counter field would just be a fourth
        # divergent store for the same fact) — data_source_status itself is the two-step
        # state machine, discriminated on whether THIS candidate was already booked by a
        # prior pass (not on the status alone — migration 006 defaults every row to
        # `unverified`, so gating on status==DS_UNVERIFIED escalates a fresh epic's very
        # first disagreement straight to `mismatch`, defeating "not on the first failure"
        # for exactly the population that exists post-migration). A fresh epic, or one
        # whose candidate just changed, always gets one free `unverified` pass first; a
        # persistent mismatch stays `mismatch` rather than flapping back to `unverified`.
        already_booked = rec.yf_ticker == candidate
        if rec.data_source_status == DS_MISMATCH and already_booked:
            next_status = DS_MISMATCH
        elif rec.data_source_status == DS_UNVERIFIED and already_booked:
            next_status = DS_MISMATCH
        else:
            next_status = DS_UNVERIFIED
        if not is_operator:
            self._store.set_symbol(rec.epic, candidate, symbol_source=symbol_source, status=next_status)
        else:
            self._store.set_symbol(
                rec.epic, rec.yf_ticker, symbol_source=SYMBOL_SOURCE_OPERATOR, status=next_status
            )
        return next_status

    def resolve_universe(self) -> ResolverReport:
        """One pass over every active/discovered epic. Fail-soft per epic — one epic's
        exception never aborts the pass (mirrors ``promotion.run_promotion_cycle``)."""
        report = ResolverReport()
        records = self._store.list_by_status(_STATUS_ACTIVE, _STATUS_DISCOVERED)
        for rec in records:
            report.checked += 1
            try:
                status = self.resolve_epic(rec)
            except Exception:  # noqa: BLE001 — one epic must never abort the whole pass
                report.unverified.append(rec.epic)
                continue
            bucket = {
                DS_OK: report.verified,
                DS_NO_SOURCE: report.no_source,
                DS_NO_INTRADAY_SOURCE: report.no_intraday,
                DS_MISMATCH: report.mismatch,
            }.get(status, report.unverified)
            bucket.append(rec.epic)
        return report
