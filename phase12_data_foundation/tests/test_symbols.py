"""Tests for ``data_foundation.symbols`` (Plan §6 Step 3)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import pytest

from data_foundation.exceptions import ResolverError
from data_foundation.symbols import (
    DS_MISMATCH,
    DS_NO_INTRADAY_SOURCE,
    DS_NO_SOURCE,
    DS_OK,
    DS_UNVERIFIED,
    SYMBOL_SOURCE_OPERATOR,
    SYMBOL_SOURCE_RESOLVER,
    SYMBOL_SOURCE_SEED,
    ResolverReport,
    SymbolResolver,
    candidates_for,
    is_weekend_instrument,
    price_agreement,
)


# -- candidates_for -----------------------------------------------------------


def test_candidates_for_finds_match():
    assert candidates_for("Germany 40") == ["^GDAXI"]


def test_candidates_for_case_insensitive_substring():
    assert candidates_for("germany 40 kassa") == ["^GDAXI"]


def test_candidates_for_no_match_returns_empty():
    assert candidates_for("Some Unknown Index") == []


def test_candidates_for_empty_name_returns_empty():
    assert candidates_for(None) == []
    assert candidates_for("") == []


# -- is_weekend_instrument -----------------------------------------------------


def test_weekend_instrument_special_info_primary_signal():
    market_info = {"specialInfo": "The weekend instruments prices are determined by IG."}
    assert is_weekend_instrument("Sunday DAX", market_info) is True


def test_weekend_instrument_opening_hours_secondary_signal():
    market_info = {"openingHours": {"marketTimes": [{"openTime": "07:00", "closeTime": "21:40"}]}}
    assert is_weekend_instrument("Some Index", market_info) is True


def test_weekday_instrument_null_opening_hours_not_weekend():
    market_info = {"openingHours": None, "specialInfo": ""}
    assert is_weekend_instrument("Germany 40", market_info) is False


def test_weekend_instrument_name_fallback_no_market_info():
    assert is_weekend_instrument("Wochenend DAX", None) is True
    assert is_weekend_instrument("Weekend Index", None) is True


def test_normal_name_no_market_info_not_weekend():
    assert is_weekend_instrument("Germany 40", None) is False
    assert is_weekend_instrument(None, None) is False


def test_weekend_instrument_epic_segment_fallback():
    """Live-confirmed 2026-08-15: all four production weekend epics carry a name
    fallback hit too, but the epic-segment check is the plan's documented second half of
    the fallback and must work standalone (e.g. an unnamed/blank-name discovery hit)."""
    assert is_weekend_instrument(None, None, epic="IX.D.SUNDAX.IGN.IP") is True
    assert is_weekend_instrument("", None, epic="IX.D.SUNNAS.IAE.IP") is True


def test_normal_epic_no_sun_segment_not_weekend():
    assert is_weekend_instrument("Germany 40", None, epic="IX.D.DAX.IFMM.IP") is False


# -- price_agreement ------------------------------------------------------------


def test_price_agreement_within_tolerance():
    assert price_agreement(100.0, 101.5, tolerance_pct=2.0) is True


def test_price_agreement_at_boundary():
    assert price_agreement(100.0, 102.0, tolerance_pct=2.0) is True


def test_price_agreement_outside_tolerance():
    assert price_agreement(100.0, 103.0, tolerance_pct=2.0) is False


def test_price_agreement_non_positive_ig_mid_never_agrees():
    assert price_agreement(0.0, 0.0) is False
    assert price_agreement(-5.0, -5.0) is False


# -- SymbolResolver: fakes ------------------------------------------------------


@dataclass
class _FakeRecord:
    epic: str
    name: str | None = None
    yf_ticker: str | None = None
    symbol_source: str | None = None
    data_source_status: str = DS_UNVERIFIED
    status: str = "discovered"


class _FakeStore:
    def __init__(self, records: list[_FakeRecord]):
        self._by_epic = {r.epic: r for r in records}
        self.set_symbol_calls: list[tuple] = []

    def get(self, epic: str) -> _FakeRecord | None:
        return self._by_epic.get(epic)

    def list_by_status(self, *statuses: str) -> list[_FakeRecord]:
        return [r for r in self._by_epic.values() if r.status in statuses]

    def set_symbol(self, epic: str, yf_ticker, *, symbol_source, status: str) -> None:
        self.set_symbol_calls.append((epic, yf_ticker, symbol_source, status))
        rec = self._by_epic[epic]
        rec.yf_ticker = yf_ticker
        rec.symbol_source = symbol_source
        rec.data_source_status = status


NOW = datetime(2026, 8, 15, 10, 0, 0, tzinfo=timezone.utc)


def _fresh_ts(minutes_ago: float = 1.0) -> str:
    dt = NOW - timedelta(minutes=minutes_ago)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def _resolver(
    store,
    *,
    quote=None,
    yf_last=None,
    market_open=True,
    max_yf_age_min=30,
):
    def quote_fetch(epic):
        if quote is None:
            raise AssertionError("quote_fetch should not have been called")
        return quote

    def yf_last_fetch(symbol):
        if callable(yf_last):
            return yf_last(symbol)
        return yf_last

    return SymbolResolver(
        store,
        quote_fetch,
        yf_last_fetch,
        market_open_fn=lambda: market_open,
        max_yf_age_min=max_yf_age_min,
        now_fn=lambda: NOW,
    )


# -- SymbolResolver.resolve_epic -------------------------------------------------


def test_resolve_epic_no_candidate_yields_no_source():
    rec = _FakeRecord(epic="E1", name="Totally Unknown Index")
    store = _FakeStore([rec])
    resolver = _resolver(store)

    assert resolver.resolve_epic(rec) == DS_NO_SOURCE
    assert rec.data_source_status == DS_NO_SOURCE
    assert rec.yf_ticker is None


def test_resolve_epic_weekend_instrument_yields_no_intraday_source():
    rec = _FakeRecord(epic="E2", name="Wochenend DAX")
    store = _FakeStore([rec])
    resolver = _resolver(store)

    assert resolver.resolve_epic(rec) == DS_NO_INTRADAY_SOURCE
    assert rec.data_source_status == DS_NO_INTRADAY_SOURCE


def test_resolve_epic_market_closed_books_nothing():
    rec = _FakeRecord(epic="E3", name="Germany 40", data_source_status=DS_UNVERIFIED)
    store = _FakeStore([rec])
    resolver = _resolver(store, market_open=False)

    assert resolver.resolve_epic(rec) == DS_UNVERIFIED
    assert store.set_symbol_calls == []  # we learned nothing


def test_resolve_epic_agreement_yields_ok_and_resolver_source():
    rec = _FakeRecord(epic="E4", name="Germany 40")
    store = _FakeStore([rec])
    resolver = _resolver(
        store, quote={"bid": 100.0, "ask": 100.2}, yf_last=(100.1, _fresh_ts())
    )

    assert resolver.resolve_epic(rec) == DS_OK
    assert rec.yf_ticker == "^GDAXI"
    assert rec.symbol_source == SYMBOL_SOURCE_RESOLVER
    assert rec.data_source_status == DS_OK


def test_resolve_epic_agreement_on_preexisting_symbol_yields_seed_source():
    rec = _FakeRecord(epic="E5", name="Germany 40", yf_ticker="^GDAXI")
    store = _FakeStore([rec])
    resolver = _resolver(
        store, quote={"bid": 100.0, "ask": 100.2}, yf_last=(100.1, _fresh_ts())
    )

    resolver.resolve_epic(rec)
    assert rec.symbol_source == SYMBOL_SOURCE_SEED


def test_resolve_epic_stale_yf_bar_books_nothing():
    rec = _FakeRecord(epic="E6", name="Germany 40")
    store = _FakeStore([rec])
    resolver = _resolver(
        store,
        quote={"bid": 100.0, "ask": 100.2},
        yf_last=(100.1, _fresh_ts(minutes_ago=45)),
        max_yf_age_min=30,
    )

    assert resolver.resolve_epic(rec) == DS_UNVERIFIED
    assert store.set_symbol_calls == []


def test_resolve_epic_first_disagreement_yields_unverified_not_mismatch():
    rec = _FakeRecord(epic="E7", name="Germany 40", data_source_status=DS_OK, yf_ticker="^GDAXI")
    store = _FakeStore([rec])
    resolver = _resolver(
        store, quote={"bid": 100.0, "ask": 100.2}, yf_last=(120.0, _fresh_ts())
    )

    assert resolver.resolve_epic(rec) == DS_UNVERIFIED
    assert rec.yf_ticker == "^GDAXI"  # candidate stays booked for the next pass


def test_resolve_epic_second_consecutive_disagreement_yields_mismatch():
    rec = _FakeRecord(
        epic="E8", name="Germany 40", data_source_status=DS_UNVERIFIED, yf_ticker="^GDAXI"
    )
    store = _FakeStore([rec])
    resolver = _resolver(
        store, quote={"bid": 100.0, "ask": 100.2}, yf_last=(120.0, _fresh_ts())
    )

    assert resolver.resolve_epic(rec) == DS_MISMATCH


def test_resolve_epic_fresh_epic_first_disagreement_yields_unverified():
    """Migration 006 defaults every row to `unverified` with yf_ticker=None — a fresh
    epic's very first disagreement must get one free `unverified` pass, not escalate
    straight to `mismatch` (the population that actually exists post-migration)."""
    rec = _FakeRecord(epic="E7B", name="Germany 40")  # default status=DS_UNVERIFIED, no symbol yet
    store = _FakeStore([rec])
    resolver = _resolver(
        store, quote={"bid": 100.0, "ask": 100.2}, yf_last=(120.0, _fresh_ts())
    )

    assert resolver.resolve_epic(rec) == DS_UNVERIFIED
    assert rec.yf_ticker == "^GDAXI"  # candidate now booked, for next pass's comparison


def test_resolve_epic_persistent_mismatch_stays_mismatch():
    rec = _FakeRecord(
        epic="E8B", name="Germany 40", data_source_status=DS_MISMATCH, yf_ticker="^GDAXI"
    )
    store = _FakeStore([rec])
    resolver = _resolver(
        store, quote={"bid": 100.0, "ask": 100.2}, yf_last=(120.0, _fresh_ts())
    )

    assert resolver.resolve_epic(rec) == DS_MISMATCH  # sticky, does not flap to unverified


def test_resolve_epic_operator_symbol_never_overwritten():
    rec = _FakeRecord(
        epic="E9",
        name="Germany 40",
        yf_ticker="^CUSTOM",
        symbol_source=SYMBOL_SOURCE_OPERATOR,
        data_source_status=DS_OK,
    )
    store = _FakeStore([rec])
    resolver = _resolver(
        store, quote={"bid": 100.0, "ask": 100.2}, yf_last=(120.0, _fresh_ts())
    )

    resolver.resolve_epic(rec)
    assert rec.yf_ticker == "^CUSTOM"
    assert rec.symbol_source == SYMBOL_SOURCE_OPERATOR
    # status still updates — the operator's symbol is checked, just never replaced
    assert rec.data_source_status == DS_UNVERIFIED


def test_resolve_epic_quote_fetch_exception_books_nothing():
    rec = _FakeRecord(epic="E10", name="Germany 40")
    store = _FakeStore([rec])

    def boom(epic):
        raise RuntimeError("network blip")

    resolver = SymbolResolver(
        store, boom, lambda s: (100.0, _fresh_ts()), market_open_fn=lambda: True, now_fn=lambda: NOW
    )
    assert resolver.resolve_epic(rec) == DS_UNVERIFIED
    assert store.set_symbol_calls == []


def test_resolve_epic_yf_none_result_books_nothing():
    rec = _FakeRecord(epic="E11", name="Germany 40")
    store = _FakeStore([rec])
    resolver = _resolver(store, quote={"bid": 100.0, "ask": 100.2}, yf_last=None)

    assert resolver.resolve_epic(rec) == DS_UNVERIFIED
    assert store.set_symbol_calls == []


def test_resolve_epic_unparseable_yf_timestamp_raises_resolver_error():
    rec = _FakeRecord(epic="E12", name="Germany 40")
    store = _FakeStore([rec])
    resolver = _resolver(
        store, quote={"bid": 100.0, "ask": 100.2}, yf_last=(100.0, "not-a-timestamp")
    )

    with pytest.raises(ResolverError):
        resolver.resolve_epic(rec)


# -- SymbolResolver.resolve_universe --------------------------------------------


def test_resolve_universe_buckets_by_outcome():
    ok_rec = _FakeRecord(epic="OK", name="Germany 40", status="active")
    weekend_rec = _FakeRecord(epic="WK", name="Wochenend DAX", status="active")
    nosrc_rec = _FakeRecord(epic="NS", name="Unknown Index", status="discovered")
    store = _FakeStore([ok_rec, weekend_rec, nosrc_rec])
    resolver = _resolver(
        store, quote={"bid": 100.0, "ask": 100.2}, yf_last=(100.1, _fresh_ts())
    )

    report = resolver.resolve_universe()
    assert report.checked == 3
    assert report.verified == ["OK"]
    assert report.no_intraday == ["WK"]
    assert report.no_source == ["NS"]


def test_resolve_universe_is_fail_soft_per_epic():
    good = _FakeRecord(epic="GOOD", name="Germany 40", status="active")
    bad = _FakeRecord(epic="BAD", name="France 40", status="active")
    store = _FakeStore([good, bad])

    def quote_fetch(epic):
        if epic == "BAD":
            raise RuntimeError("boom")
        return {"bid": 100.0, "ask": 100.2}

    resolver = SymbolResolver(
        store,
        quote_fetch,
        lambda s: (100.1, _fresh_ts()),
        market_open_fn=lambda: True,
        now_fn=lambda: NOW,
    )

    report = resolver.resolve_universe()
    assert report.checked == 2
    assert report.verified == ["GOOD"]
    assert "BAD" in report.unverified


def test_resolve_universe_survives_a_set_symbol_failure():
    """resolve_epic itself does not catch a store.set_symbol failure (e.g. the epic
    vanished mid-pass) — resolve_universe is the fail-soft boundary, not resolve_epic."""
    good = _FakeRecord(epic="GOOD", name="Germany 40", status="active")
    exploding = _FakeRecord(epic="EXPLODE", name="France 40", status="active")
    store = _FakeStore([good, exploding])

    def set_symbol(epic, yf_ticker, *, symbol_source, status):
        if epic == "EXPLODE":
            raise RuntimeError("row vanished mid-pass")
        good.yf_ticker, good.symbol_source, good.data_source_status = yf_ticker, symbol_source, status

    store.set_symbol = set_symbol
    resolver = _resolver(
        store, quote={"bid": 100.0, "ask": 100.2}, yf_last=(100.1, _fresh_ts())
    )

    report = resolver.resolve_universe()
    assert report.checked == 2
    assert report.verified == ["GOOD"]
    assert "EXPLODE" in report.unverified


def test_resolve_universe_ignores_retired_and_quarantined():
    active = _FakeRecord(epic="A", name="Germany 40", status="active")
    retired = _FakeRecord(epic="R", name="Germany 40", status="retired")
    store = _FakeStore([active, retired])
    resolver = _resolver(
        store, quote={"bid": 100.0, "ask": 100.2}, yf_last=(100.1, _fresh_ts())
    )

    report = resolver.resolve_universe()
    assert report.checked == 1
    assert "R" not in report.verified
