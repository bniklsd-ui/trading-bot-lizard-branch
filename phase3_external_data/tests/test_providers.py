"""Tests for the BarProvider chain (Phase 9 / V2 Step 6). No network."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from external_data import fetcher
from external_data.models import PriceBar
from external_data.providers import ChainedBarProvider, IGBarProvider, YFinanceBarProvider

EPIC = "IX.D.DAX.IFMM.IP"


def _env(ok: bool, data: dict | None = None):
    return SimpleNamespace(ok=ok, data=data or {})


def _ig_bar(ts="2026-07-04T09:00:00Z", o=1.0, h=2.0, low=0.5, c=1.5, v=100.0) -> dict:
    return {"timestamp": ts, "open": o, "high": h, "low": low, "close": c, "volume": v}


# -- IGBarProvider --------------------------------------------------------------


class _FakeBroker:
    def __init__(self, env=None, raises: bool = False):
        self._env = env
        self._raises = raises
        self.calls: list[tuple] = []

    def get_ohlcv(self, epic, resolution, count):
        self.calls.append((epic, resolution, count))
        if self._raises:
            raise RuntimeError("boom")
        return self._env


def test_ig_provider_maps_bars_correctly():
    broker = _FakeBroker(_env(True, {"bars": [_ig_bar()]}))
    provider = IGBarProvider(broker)
    bars = provider.get_bars(EPIC, resolution="5m", count=3)
    assert bars == [PriceBar(ts="2026-07-04T09:00:00Z", open=1.0, high=2.0, low=0.5, close=1.5, volume=100.0)]
    assert broker.calls == [(EPIC, "MINUTE_5", 3)]


def test_ig_provider_resolution_mapping():
    broker = _FakeBroker(_env(True, {"bars": [_ig_bar()]}))
    provider = IGBarProvider(broker)
    provider.get_bars(EPIC, resolution="1d", count=1)
    assert broker.calls == [(EPIC, "DAY", 1)]


def test_ig_provider_unmapped_resolution_returns_none():
    broker = _FakeBroker(_env(True, {"bars": [_ig_bar()]}))
    provider = IGBarProvider(broker)
    assert provider.get_bars(EPIC, resolution="30m", count=3) is None
    assert broker.calls == []  # never even called the broker


def test_ig_provider_not_ok_returns_none():
    broker = _FakeBroker(_env(False))
    provider = IGBarProvider(broker)
    assert provider.get_bars(EPIC, resolution="5m", count=3) is None


def test_ig_provider_empty_bars_returns_none():
    broker = _FakeBroker(_env(True, {"bars": []}))
    provider = IGBarProvider(broker)
    assert provider.get_bars(EPIC, resolution="5m", count=3) is None


def test_ig_provider_exception_returns_none():
    broker = _FakeBroker(raises=True)
    provider = IGBarProvider(broker)
    assert provider.get_bars(EPIC, resolution="5m", count=3) is None


# -- YFinanceBarProvider ----------------------------------------------------


class _FakeFetcher:
    def __init__(self, bars=None, raises: bool = False):
        self._bars = bars
        self._raises = raises
        self.calls: list[tuple] = []

    def get_bars(self, epic, resolution, count):
        self.calls.append((epic, resolution, count))
        if self._raises:
            raise RuntimeError("boom")
        return self._bars


def test_yfinance_provider_delegates():
    bars = [PriceBar(ts="t", open=1, high=1, low=1, close=1, volume=0)]
    fake = _FakeFetcher(bars=bars)
    provider = YFinanceBarProvider(fake)
    assert provider.get_bars(EPIC, resolution="5m", count=5) is bars
    assert fake.calls == [(EPIC, "5m", 5)]


def test_yfinance_provider_none_passthrough():
    fake = _FakeFetcher(bars=None)  # e.g. off-hours
    provider = YFinanceBarProvider(fake)
    assert provider.get_bars(EPIC, resolution="5m", count=5) is None


def test_yfinance_provider_exception_returns_none():
    fake = _FakeFetcher(raises=True)
    provider = YFinanceBarProvider(fake)
    assert provider.get_bars(EPIC, resolution="5m", count=5) is None


# -- ChainedBarProvider -------------------------------------------------------


class _StubProvider:
    def __init__(self, bars=None, raises: bool = False):
        self._bars = bars
        self._raises = raises
        self.calls = 0

    def get_bars(self, epic, *, resolution, count):
        self.calls += 1
        if self._raises:
            raise RuntimeError("boom")
        return self._bars


_BARS = [PriceBar(ts="t", open=1, high=1, low=1, close=1, volume=0)]


def test_chained_provider_first_wins():
    first = _StubProvider(bars=_BARS)
    second = _StubProvider(bars=None)
    chain = ChainedBarProvider([("ig", first), ("yf", second)])
    assert chain.get_bars(EPIC, resolution="5m", count=3) is _BARS
    assert first.calls == 1
    assert second.calls == 0  # never reached


def test_chained_provider_falls_through_to_second():
    first = _StubProvider(bars=None)
    second = _StubProvider(bars=_BARS)
    chain = ChainedBarProvider([("ig", first), ("yf", second)])
    assert chain.get_bars(EPIC, resolution="5m", count=3) is _BARS
    assert first.calls == 1
    assert second.calls == 1


def test_chained_provider_all_none_returns_none():
    chain = ChainedBarProvider([("ig", _StubProvider(bars=None)), ("yf", _StubProvider(bars=None))])
    assert chain.get_bars(EPIC, resolution="5m", count=3) is None


def test_chained_provider_exception_treated_as_none():
    first = _StubProvider(raises=True)
    second = _StubProvider(bars=_BARS)
    chain = ChainedBarProvider([("ig", first), ("yf", second)])
    assert chain.get_bars(EPIC, resolution="5m", count=3) is _BARS


def test_chained_provider_emits_health_events():
    events: list[dict] = []
    first = _StubProvider(bars=None)
    second = _StubProvider(bars=_BARS)
    chain = ChainedBarProvider([("ig", first), ("yf", second)], health_sink=events.append)
    chain.get_bars(EPIC, resolution="5m", count=3)
    assert events == [
        {"event": "bar_fetch", "provider": "ig", "epic": EPIC, "ok": False},
        {"event": "bar_fetch", "provider": "yf", "epic": EPIC, "ok": True},
    ]


def test_chained_provider_health_sink_exception_does_not_break_chain():
    def _boom(_event):
        raise RuntimeError("sink exploded")

    chain = ChainedBarProvider([("ig", _StubProvider(bars=_BARS))], health_sink=_boom)
    assert chain.get_bars(EPIC, resolution="5m", count=3) is _BARS


# -- fetcher.MarketDataFetcher bar_provider seam ------------------------------


def test_fetcher_default_bar_provider_none_uses_yfinance_path(monkeypatch, tmp_cache, frozen_clock, sample_dax_5m):
    from external_data.ticker_map import TickerMapper

    def fake_download(symbol, *, period, interval):
        return sample_dax_5m.copy()

    monkeypatch.setattr(fetcher, "_raw_download", fake_download)
    monkeypatch.setattr(fetcher, "_SLEEP", lambda *_: None)
    md = fetcher.MarketDataFetcher(TickerMapper(), tmp_cache)
    bars = md.get_bars(EPIC, resolution="5m", count=3)
    assert bars is not None and len(bars) == 3


def test_fetcher_with_bar_provider_delegates(tmp_cache, frozen_clock):
    from external_data.ticker_map import TickerMapper

    provider = _StubProvider(bars=_BARS)
    md = fetcher.MarketDataFetcher(TickerMapper(), tmp_cache, bar_provider=provider)
    result = md.get_bars(EPIC, resolution="5m", count=3)
    assert result is _BARS
    assert provider.calls == 1


def test_fetcher_with_bar_provider_still_off_hours_guarded(tmp_cache, frozen_clock):
    from datetime import datetime, timezone

    from external_data.ticker_map import TickerMapper

    frozen_clock(datetime(2026, 5, 23, 10, 0, tzinfo=timezone.utc))  # Saturday -> closed
    provider = _StubProvider(bars=_BARS)
    md = fetcher.MarketDataFetcher(TickerMapper(), tmp_cache, bar_provider=provider)
    result = md.get_bars(EPIC, resolution="5m", count=3)
    assert result is None
    assert provider.calls == 0  # never even asked
