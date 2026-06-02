"""Tests for ``external_data.fetcher`` — mocked, no network (concept §15).

The only network point, ``fetcher._raw_download``, is monkeypatched in every test;
``fetcher._SLEEP`` is neutralised so retry/backoff and the rate limiter never wait.
The yFinance rate-limit error is simulated by a locally-defined ``YFRateLimitError``
class (the fetcher matches it by class name, so yFinance need not be installed).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest

from external_data import fetcher
from external_data.exceptions import (
    DataUnavailableError,
    EpicNotMappedError,
    RateLimitError,
)
from external_data.ticker_map import TickerMapper

EPIC = "IX.D.DAX.IFMM.IP"
SYMBOL = "^GDAXI"


class YFRateLimitError(Exception):
    """Stand-in for ``yfinance.exceptions.YFRateLimitError`` (matched by name)."""


def make_fake_download(
    daily=None, m5=None, *, calls=None, fail_intervals=(), raise_exc=None
):
    """Build a fake ``_raw_download`` that routes by ``interval``.

    ``1d`` → ``daily`` fixture, ``5m`` → ``m5`` fixture. ``calls`` (a list) records
    every call as ``(symbol, period, interval)``. ``fail_intervals`` returns an empty
    frame for the named intervals; ``raise_exc`` raises it on every call.
    """

    def _fake(symbol, *, period, interval):
        if calls is not None:
            calls.append((symbol, period, interval))
        if raise_exc is not None:
            raise raise_exc
        if interval in fail_intervals:
            return pd.DataFrame()
        if interval == "1d":
            return daily.copy() if daily is not None else pd.DataFrame()
        if interval == "5m":
            return m5.copy() if m5 is not None else pd.DataFrame()
        return pd.DataFrame()

    return _fake


@pytest.fixture
def no_sleep(monkeypatch):
    """Neutralise every blocking sleep in the fetcher (backoff + rate limiter)."""
    monkeypatch.setattr(fetcher, "_SLEEP", lambda *_: None)


# -- caching / fetching -------------------------------------------------------

def test_cache_hit_skips_second_fetch(monkeypatch, tmp_cache, frozen_clock, sample_dax_daily):
    calls: list = []
    monkeypatch.setattr(fetcher, "_raw_download", make_fake_download(daily=sample_dax_daily, calls=calls))
    md = fetcher.MarketDataFetcher(TickerMapper(), tmp_cache)

    md.get_history(EPIC)
    md.get_history(EPIC)

    assert len(calls) == 1  # second call served from cache, no network


def test_miss_fetches_and_writes_cache(monkeypatch, tmp_cache, frozen_clock, sample_dax_daily):
    calls: list = []
    monkeypatch.setattr(fetcher, "_raw_download", make_fake_download(daily=sample_dax_daily, calls=calls))
    md = fetcher.MarketDataFetcher(TickerMapper(), tmp_cache)

    md.get_history(EPIC)

    assert len(calls) == 1
    key = tmp_cache.make_key(SYMBOL, "1d", fetcher._today_berlin_str())
    assert tmp_cache.get(key) is not None


def test_empty_dataframe_retries_then_raises_data_unavailable(
    monkeypatch, tmp_cache, frozen_clock, no_sleep
):
    calls: list = []
    monkeypatch.setattr(
        fetcher, "_raw_download", make_fake_download(daily=None, calls=calls)  # 1d → empty
    )
    md = fetcher.MarketDataFetcher(TickerMapper(), tmp_cache)

    with pytest.raises(DataUnavailableError):
        md.get_history(EPIC)
    assert len(calls) == fetcher._MAX_RETRIES  # exhausted the retry budget


def test_rate_limit_retries_then_raises_rate_limit_error(
    monkeypatch, tmp_cache, frozen_clock, no_sleep
):
    calls: list = []
    monkeypatch.setattr(
        fetcher,
        "_raw_download",
        make_fake_download(calls=calls, raise_exc=YFRateLimitError("429 Too Many Requests")),
    )
    md = fetcher.MarketDataFetcher(TickerMapper(), tmp_cache)

    with pytest.raises(RateLimitError):
        md.get_history(EPIC)
    assert len(calls) == fetcher._MAX_RETRIES


# -- off-hours discipline -----------------------------------------------------

def _saturday(frozen_clock):
    # 2026-05-23 is a Saturday → market closed.
    frozen_clock(datetime(2026, 5, 23, 12, 0, tzinfo=timezone.utc))


def test_offhours_drift_returns_none_without_fetching(
    monkeypatch, tmp_cache, frozen_clock, sample_dax_daily, sample_dax_5m
):
    _saturday(frozen_clock)
    calls: list = []
    monkeypatch.setattr(
        fetcher, "_raw_download",
        make_fake_download(daily=sample_dax_daily, m5=sample_dax_5m, calls=calls),
    )
    md = fetcher.MarketDataFetcher(TickerMapper(), tmp_cache)

    assert md.get_drift(EPIC) is None
    assert calls == []  # intraday guard short-circuits before any network call


def test_offhours_momentum_returns_none(
    monkeypatch, tmp_cache, frozen_clock, sample_dax_5m
):
    _saturday(frozen_clock)
    monkeypatch.setattr(fetcher, "_raw_download", make_fake_download(m5=sample_dax_5m))
    md = fetcher.MarketDataFetcher(TickerMapper(), tmp_cache)

    assert md.get_momentum(EPIC) is None


def test_offhours_intraday_bars_return_none(
    monkeypatch, tmp_cache, frozen_clock, sample_dax_5m
):
    _saturday(frozen_clock)
    calls: list = []
    monkeypatch.setattr(fetcher, "_raw_download", make_fake_download(m5=sample_dax_5m, calls=calls))
    md = fetcher.MarketDataFetcher(TickerMapper(), tmp_cache)

    assert md.get_bars(EPIC, resolution="5m") is None
    assert calls == []


def test_daily_methods_run_off_hours(
    monkeypatch, tmp_cache, frozen_clock, sample_dax_daily
):
    _saturday(frozen_clock)
    calls: list = []
    monkeypatch.setattr(fetcher, "_raw_download", make_fake_download(daily=sample_dax_daily, calls=calls))
    md = fetcher.MarketDataFetcher(TickerMapper(), tmp_cache)

    bars = md.get_history(EPIC, days=30)
    assert len(bars) == 30
    assert calls and all(interval == "1d" for _, _, interval in calls)


# -- indicator wiring ---------------------------------------------------------

def test_momentum_is_never_realtime(
    monkeypatch, tmp_cache, frozen_clock, sample_dax_5m
):
    monkeypatch.setattr(fetcher, "_raw_download", make_fake_download(m5=sample_dax_5m))
    md = fetcher.MarketDataFetcher(TickerMapper(), tmp_cache)

    result = md.get_momentum(EPIC)
    assert result is not None
    assert result.is_realtime is False  # delay honesty (concept §12)


def test_volume_degrades_without_proxy(
    monkeypatch, tmp_cache, frozen_clock, sample_dax_daily
):
    monkeypatch.setattr(fetcher, "_raw_download", make_fake_download(daily=sample_dax_daily))
    md = fetcher.MarketDataFetcher(TickerMapper(), tmp_cache)

    vol = md.get_volume_anomaly(EPIC)
    assert vol is not None
    assert vol.volume_available is False
    assert vol.volume_source is None
    assert vol.z_score == 0.0
    assert vol.is_anomaly is False


def test_volume_uses_registered_proxy(
    monkeypatch, tmp_cache, frozen_clock, sample_dax_daily
):
    calls: list = []
    monkeypatch.setattr(fetcher, "_raw_download", make_fake_download(daily=sample_dax_daily, calls=calls))
    mapper = TickerMapper()
    mapper.register_volume_proxy(EPIC, "EXS1.DE")
    md = fetcher.MarketDataFetcher(mapper, tmp_cache)

    vol = md.get_volume_anomaly(EPIC)
    assert vol is not None
    assert vol.volume_available is True
    assert vol.volume_source == "EXS1.DE"
    # The proxy symbol — not the index — is what got fetched.
    assert calls and all(symbol == "EXS1.DE" for symbol, _, _ in calls)


def test_high_low_offhours_uses_last_daily_close(
    monkeypatch, tmp_cache, frozen_clock, sample_dax_daily
):
    _saturday(frozen_clock)
    calls: list = []
    monkeypatch.setattr(fetcher, "_raw_download", make_fake_download(daily=sample_dax_daily, calls=calls))
    md = fetcher.MarketDataFetcher(TickerMapper(), tmp_cache)

    hl = md.get_high_low_distance(EPIC)
    assert hl is not None
    expected_close = float(sample_dax_daily["Close"].iloc[-1])
    assert hl.current_price == expected_close
    assert all(interval == "1d" for _, _, interval in calls)  # no intraday fetch off-hours


# -- composite / errors -------------------------------------------------------

def test_brain_context_tolerates_missing_intraday(
    monkeypatch, tmp_cache, frozen_clock, no_sleep, sample_dax_daily, sample_dax_5m
):
    # In-hours, but every 5m fetch fails → drift & momentum degrade to None while
    # daily-based fields and history stay populated; nothing crashes.
    monkeypatch.setattr(
        fetcher,
        "_raw_download",
        make_fake_download(daily=sample_dax_daily, m5=sample_dax_5m, fail_intervals=("5m",)),
    )
    md = fetcher.MarketDataFetcher(TickerMapper(), tmp_cache)

    ctx = md.get_brain_context(EPIC)
    assert ctx is not None
    assert ctx.drift is None
    assert ctx.momentum_15m is None
    assert ctx.volume is not None
    assert ctx.high_low is not None  # falls back to last daily close
    assert len(ctx.price_history_30d) > 0
    # Prompt dict is complete with explicit None gaps.
    prompt = ctx.to_prompt_dict()
    for key in (
        "ticker", "drift_pct", "momentum_15m_pct", "momentum_is_realtime",
        "volume_z_score", "volume_available", "distance_to_high_pct",
        "distance_to_low_pct", "range_30d", "generated_at",
    ):
        assert key in prompt
    assert prompt["drift_pct"] is None
    assert prompt["momentum_15m_pct"] is None


def test_unmapped_epic_propagates(monkeypatch, tmp_cache, frozen_clock):
    calls: list = []
    monkeypatch.setattr(fetcher, "_raw_download", make_fake_download(calls=calls))
    md = fetcher.MarketDataFetcher(TickerMapper(), tmp_cache)

    with pytest.raises(EpicNotMappedError):
        md.get_drift("NO.SUCH.EPIC")
    assert calls == []  # mapping fails before any fetch


def test_rate_limiter_wait_invoked_on_miss(
    monkeypatch, tmp_cache, frozen_clock, sample_dax_daily
):
    monkeypatch.setattr(fetcher, "_raw_download", make_fake_download(daily=sample_dax_daily))

    class SpyLimiter(fetcher.RateLimiter):
        def __init__(self) -> None:
            super().__init__()
            self.waits = 0

        def wait(self) -> None:
            self.waits += 1
            super().wait()

    spy = SpyLimiter()
    md = fetcher.MarketDataFetcher(TickerMapper(), tmp_cache, rate_limiter=spy)

    md.get_history(EPIC)
    assert spy.waits == 1  # one miss → one rate-limited wait

    md.get_history(EPIC)
    assert spy.waits == 1  # cache hit → no additional wait
