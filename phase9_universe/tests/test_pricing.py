"""Tests for the deterministic point_value resolver (Phase 9 / V2 Step 2).

Pure fixture dicts, no network, no broker — matches the plan's acceptance
criterion: ``resolve_point_value`` is a pure function.
"""

from __future__ import annotations

from universe.models import UniverseRecord
from universe.pricing import confirm_curated, resolve_point_value


def _record(point_value: float | None, **overrides) -> UniverseRecord:
    defaults = dict(
        epic="IX.D.STXE.IFM.IP",
        currency="EUR",
        status="active",
        source="curated",
        created_at="2026-07-04T00:00:00.000Z",
        updated_at="2026-07-04T00:00:00.000Z",
        point_value=point_value,
    )
    defaults.update(overrides)
    return UniverseRecord(**defaults)


# -- ig_fields path (dormant against real P1 data today, but pure-function testable) --


def test_ig_fields_value_of_one_pip_resolves():
    market_info = {"value_of_one_pip": "2.0", "name": "irrelevant", "lot_size": 999}
    assert resolve_point_value(market_info) == (2.0, "ig_fields")


def test_ig_fields_contract_size_fallback_resolves():
    market_info = {"contract_size": 1.0, "name": "irrelevant", "lot_size": 999}
    assert resolve_point_value(market_info) == (1.0, "ig_fields")


def test_ig_fields_ambiguous_string_falls_through_to_name_check():
    market_info = {
        "value_of_one_pip": "2 EUR per point",  # not cleanly numeric -> ambiguous
        "name": "Frankreich 40 Kassa (1€)",
        "lot_size": 1.0,
    }
    assert resolve_point_value(market_info) == (1.0, "name_lotsize_agree")


def test_ig_fields_zero_or_negative_is_not_accepted():
    market_info = {"value_of_one_pip": "0", "name": "Deutschland 40 Kassa (1€)", "lot_size": 1.0}
    assert resolve_point_value(market_info) == (1.0, "name_lotsize_agree")


# -- name/lot_size cross-check path --------------------------------------------


def test_name_lotsize_agree_happy_path_stxe():
    market_info = {"name": "EU Stocks 50 Kassa (2€)", "lot_size": 2.0}
    assert resolve_point_value(market_info) == (2.0, "name_lotsize_agree")


def test_name_lotsize_mismatch_returns_none():
    market_info = {"name": "Frankreich 40 Kassa (1€)", "lot_size": 2.0}
    assert resolve_point_value(market_info) is None


def test_name_missing_eur_marker_returns_none():
    market_info = {"name": "Some Index Future", "lot_size": 1.0}
    assert resolve_point_value(market_info) is None


def test_name_present_but_lot_size_missing_returns_none():
    market_info = {"name": "Deutschland 40 Kassa (1€)", "lot_size": None}
    assert resolve_point_value(market_info) is None


def test_comma_decimal_in_name_is_parsed():
    market_info = {"name": "Spanien 35 Kassa (2,5€)", "lot_size": 2.5}
    assert resolve_point_value(market_info) == (2.5, "name_lotsize_agree")


def test_lot_size_non_numeric_returns_none():
    market_info = {"name": "Deutschland 40 Kassa (1€)", "lot_size": "not-a-number"}
    assert resolve_point_value(market_info) is None


def test_nothing_resolvable_returns_none():
    assert resolve_point_value({}) is None


def test_name_lotsize_zero_is_not_accepted():
    # 2026-07-04 review polish: path 2 carries the same `> 0` guard as path 1 —
    # a hypothetical "(0€)" + lot_size 0 must not resolve to point_value 0
    # (which would zero out P5 sizing math downstream).
    market_info = {"name": "Broken Index Kassa (0€)", "lot_size": 0.0}
    assert resolve_point_value(market_info) is None


# -- confirm_curated ------------------------------------------------------------


def test_confirm_curated_matching_returns_true():
    record = _record(point_value=2.0)
    market_info = {"name": "EU Stocks 50 Kassa (2€)", "lot_size": 2.0}
    assert confirm_curated(record, market_info) is True


def test_confirm_curated_contradiction_returns_false():
    record = _record(point_value=2.0)
    market_info = {"name": "EU Stocks 50 Kassa (1€)", "lot_size": 1.0}
    assert confirm_curated(record, market_info) is False


def test_confirm_curated_unresolvable_returns_none():
    record = _record(point_value=2.0)
    market_info = {"name": "no eur marker here", "lot_size": None}
    assert confirm_curated(record, market_info) is None


def test_confirm_curated_record_without_point_value_returns_none():
    record = _record(point_value=None)
    market_info = {"name": "EU Stocks 50 Kassa (2€)", "lot_size": 2.0}
    assert confirm_curated(record, market_info) is None
