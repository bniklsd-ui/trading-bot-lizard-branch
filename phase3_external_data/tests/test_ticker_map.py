"""Tests for ``external_data.ticker_map.TickerMapper`` (concept §8, §15).

No network — pure in-memory mapping. Covers default lookups, the
not-mapped error path, runtime registration, the ETF-volume-proxy hook,
case-sensitivity, ``^``-symbol integrity, and per-instance isolation.
"""

from __future__ import annotations

import pytest

from external_data.exceptions import EpicNotMappedError
from external_data.ticker_map import TickerMapper


def test_epic_to_yf_known_epics():
    m = TickerMapper()
    assert m.epic_to_yf("IX.D.DAX.IFMM.IP") == "^GDAXI"
    assert m.epic_to_yf("CS.D.EURUSD.MINI.IP") == "EURUSD=X"


def test_unknown_epic_raises():
    m = TickerMapper()
    with pytest.raises(EpicNotMappedError) as exc_info:
        m.epic_to_yf("XX.D.UNKNOWN.IP")
    err = exc_info.value
    assert err.code == "EPIC_NOT_MAPPED"
    assert err.retryable is False
    assert "XX.D.UNKNOWN.IP" in str(err)


def test_register_adds_mapping():
    m = TickerMapper()
    m.register("CS.D.GBPUSD.MINI.IP", "GBPUSD=X")
    assert m.epic_to_yf("CS.D.GBPUSD.MINI.IP") == "GBPUSD=X"


def test_register_overrides_existing():
    m = TickerMapper()
    m.register("IX.D.DAX.IFMM.IP", "DAX.OVERRIDE")
    assert m.epic_to_yf("IX.D.DAX.IFMM.IP") == "DAX.OVERRIDE"


def test_volume_proxy_missing_returns_none():
    m = TickerMapper()
    # ^GDAXI epic has no native volume and no proxy registered by default.
    assert m.epic_to_volume_yf("IX.D.DAX.IFMM.IP") is None


def test_register_volume_proxy_hit():
    m = TickerMapper()
    m.register_volume_proxy("IX.D.DAX.IFMM.IP", "EXS1.DE")
    assert m.epic_to_volume_yf("IX.D.DAX.IFMM.IP") == "EXS1.DE"


def test_lookup_is_case_sensitive():
    m = TickerMapper()
    with pytest.raises(EpicNotMappedError):
        m.epic_to_yf("ix.d.dax.ifmm.ip")


def test_caret_symbols_preserved():
    m = TickerMapper()
    assert m.epic_to_yf("IX.D.DAX.DAILY.IP") == "^GDAXI"
    assert m.epic_to_yf("IX.D.DOW.DAILY.IP") == "^DJI"


def test_registration_is_instance_local():
    m1 = TickerMapper()
    m1.register("CS.D.GBPUSD.MINI.IP", "GBPUSD=X")
    m1.register_volume_proxy("IX.D.DAX.IFMM.IP", "EXS1.DE")

    m2 = TickerMapper()
    # A fresh mapper must not see m1's registrations (no class-dict leakage).
    with pytest.raises(EpicNotMappedError):
        m2.epic_to_yf("CS.D.GBPUSD.MINI.IP")
    assert m2.epic_to_volume_yf("IX.D.DAX.IFMM.IP") is None
