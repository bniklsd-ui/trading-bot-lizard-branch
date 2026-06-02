"""Tests for ``external_data.indicators`` (concept §10 / §15 — the core).

Pure functions, so no clock, no network, no monkeypatching needed: every test
builds a small pandas frame and asserts on the returned dataclass. Expected
numeric values are recomputed from the fixtures with the same formula rather
than hard-coded, so the tests document the algorithm without being brittle.
"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from external_data import indicators
from external_data.models import HighLowDistance, VolumeAnomaly

_COLS = ["Open", "High", "Low", "Close", "Volume"]


# -- builders -----------------------------------------------------------------

def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=_COLS)


def _bars_from_closes(closes: list[float]) -> pd.DataFrame:
    """5-minute bars with an ascending tz-aware index built from a close list."""
    index = pd.date_range("2026-05-25T09:00:00", periods=len(closes), freq="5min", tz="Europe/Berlin")
    opens = [closes[0]] + closes[:-1]
    highs = [c + 8.0 for c in closes]
    lows = [c - 8.0 for c in closes]
    return pd.DataFrame(
        {"Open": opens, "High": highs, "Low": lows, "Close": closes, "Volume": [1000.0] * len(closes)},
        index=index,
    )


def _daily_with_volumes(window_vols: list[float], today_vol: float) -> pd.DataFrame:
    """Daily frame whose last row is 'today' and the rest are the rolling window."""
    vols = window_vols + [today_vol]
    index = pd.bdate_range("2026-04-06", periods=len(vols), tz="Europe/Berlin")
    closes = [18000.0 + i for i in range(len(vols))]
    return pd.DataFrame(
        {"Open": closes, "High": [c + 5 for c in closes], "Low": [c - 5 for c in closes],
         "Close": closes, "Volume": vols},
        index=index,
    )


def _daily_hl(rolling_high: float, rolling_low: float, n: int = 5) -> pd.DataFrame:
    """Daily frame with a fixed High max / Low min band (for high/low tests)."""
    index = pd.bdate_range("2026-04-06", periods=n, tz="Europe/Berlin")
    mid = (rolling_high + rolling_low) / 2
    return pd.DataFrame(
        {"Open": [mid] * n, "High": [rolling_high] * n, "Low": [rolling_low] * n,
         "Close": [mid] * n, "Volume": [1000.0] * n},
        index=index,
    )


# -- drift --------------------------------------------------------------------

def test_drift_normal(sample_dax_daily, sample_dax_5m):
    result = indicators.compute_drift(sample_dax_daily, sample_dax_5m, ticker="^GDAXI")
    assert result is not None
    today_open = float(sample_dax_daily["Open"].iloc[-1])
    current = float(sample_dax_5m["Close"].iloc[-1])
    assert result.today_open == today_open
    assert result.current_price == current
    assert result.drift_pct == pytest.approx((current - today_open) / today_open * 100.0)
    assert result.is_realtime is False
    assert result.ticker == "^GDAXI"


def test_drift_open_zero_returns_none(sample_dax_daily, sample_dax_5m):
    df = sample_dax_daily.copy()
    df.iloc[-1, df.columns.get_loc("Open")] = 0.0
    assert indicators.compute_drift(df, sample_dax_5m, ticker="^GDAXI") is None


def test_drift_empty_daily_returns_none(sample_dax_5m):
    assert indicators.compute_drift(_empty(), sample_dax_5m, ticker="^GDAXI") is None


def test_drift_empty_intraday_returns_none(sample_dax_daily):
    assert indicators.compute_drift(sample_dax_daily, _empty(), ticker="^GDAXI") is None


# -- momentum -----------------------------------------------------------------

def test_momentum_normal_positive(sample_dax_5m):
    result = indicators.compute_momentum(sample_dax_5m, ticker="^GDAXI", window_minutes=15)
    assert result is not None
    closes = list(sample_dax_5m["Close"])
    price_now, price_start = closes[-1], closes[-4]  # bars_back = 3
    assert result.price_now == price_now
    assert result.price_start == price_start
    assert result.momentum_pct == pytest.approx((price_now - price_start) / price_start * 100.0)
    assert result.momentum_pct > 0
    assert result.source_resolution == "5m"


def test_momentum_negative_sign():
    df = _bars_from_closes([18100.0, 18080.0, 18060.0, 18040.0, 18020.0])
    result = indicators.compute_momentum(df, ticker="^GDAXI", window_minutes=15)
    assert result is not None
    assert result.momentum_pct < 0


def test_momentum_too_few_bars_returns_none(sample_dax_5m):
    # window 15 → bars_back 3 → needs 4 bars; give it 3.
    assert indicators.compute_momentum(sample_dax_5m.iloc[:3], ticker="^GDAXI", window_minutes=15) is None


def test_momentum_is_realtime_false(sample_dax_5m):
    result = indicators.compute_momentum(sample_dax_5m, ticker="^GDAXI")
    assert result is not None
    assert result.is_realtime is False


def test_momentum_bars_back_rounding(sample_dax_5m):
    # window 7 → round(7/5)=1 → price_start is the 2nd-to-last close.
    result = indicators.compute_momentum(sample_dax_5m, ticker="^GDAXI", window_minutes=7)
    assert result is not None
    assert result.price_start == float(sample_dax_5m["Close"].iloc[-2])


# -- volume -------------------------------------------------------------------

def test_volume_normal_z_is_anomaly():
    window = [900.0, 950.0, 1000.0, 1050.0, 1100.0, 900.0, 950.0, 1000.0, 1050.0, 1100.0]
    w = pd.Series(window)
    today = w.mean() + 2.5 * w.std()  # z ≈ 2.5 → anomaly, not extreme
    df = _daily_with_volumes(window, today)
    result = indicators.compute_volume_anomaly(
        df, ticker="^GDAXI", lookback_days=10, volume_available=True, volume_source="EXS1.DE"
    )
    assert result.z_score == pytest.approx((today - w.mean()) / w.std())
    assert result.is_anomaly is True
    assert result.is_extreme is False
    assert result.volume_source == "EXS1.DE"


def test_volume_below_threshold_not_anomaly():
    window = [900.0, 950.0, 1000.0, 1050.0, 1100.0, 900.0, 950.0, 1000.0, 1050.0, 1100.0]
    w = pd.Series(window)
    today = w.mean() + 1.0 * w.std()  # z ≈ 1.0 → not an anomaly
    df = _daily_with_volumes(window, today)
    result = indicators.compute_volume_anomaly(
        df, ticker="^GDAXI", lookback_days=10, volume_available=True, volume_source=None
    )
    assert abs(result.z_score) < 2.0
    assert result.is_anomaly is False


def test_volume_extreme():
    window = [900.0, 950.0, 1000.0, 1050.0, 1100.0, 900.0, 950.0, 1000.0, 1050.0, 1100.0]
    w = pd.Series(window)
    today = w.mean() + 3.5 * w.std()  # z ≈ 3.5 → extreme
    df = _daily_with_volumes(window, today)
    result = indicators.compute_volume_anomaly(
        df, ticker="^GDAXI", lookback_days=10, volume_available=True, volume_source="EXS1.DE"
    )
    assert result.is_anomaly is True
    assert result.is_extreme is True


def test_volume_std_zero_guard(sample_dax_daily):
    # sample_dax_daily has constant volume → rolling_std 0 → z 0, no crash.
    result = indicators.compute_volume_anomaly(
        sample_dax_daily, ticker="^GDAXI", volume_available=True, volume_source="EXS1.DE"
    )
    assert result.rolling_std == 0.0
    assert result.z_score == 0.0
    assert result.is_anomaly is False
    assert result.is_extreme is False


def test_volume_unavailable_degrades(sample_dax_daily_zero_volume):
    result = indicators.compute_volume_anomaly(
        sample_dax_daily_zero_volume, ticker="^GDAXI", volume_available=False, volume_source=None
    )
    assert isinstance(result, VolumeAnomaly)  # full object, never None
    assert result.volume_available is False
    assert result.volume_source is None
    assert result.z_score == 0.0
    assert result.is_anomaly is False
    assert result.is_extreme is False
    assert result.today_volume == 0.0


# -- high / low ---------------------------------------------------------------

def test_high_low_near_high():
    df = _daily_hl(rolling_high=19000.0, rolling_low=17000.0)
    current = 18990.0  # 0.05 % below the high
    result = indicators.compute_high_low_distance(df, current, ticker="^GDAXI")
    assert result is not None
    assert result.rolling_high == 19000.0
    assert result.rolling_low == 17000.0
    assert result.is_near_high is True
    assert result.is_near_low is False


def test_high_low_near_low():
    df = _daily_hl(rolling_high=19000.0, rolling_low=17000.0)
    current = 17010.0  # 0.06 % above the low
    result = indicators.compute_high_low_distance(df, current, ticker="^GDAXI")
    assert result is not None
    assert result.is_near_low is True
    assert result.is_near_high is False


def test_high_low_mid_is_near_neither():
    df = _daily_hl(rolling_high=19000.0, rolling_low=17000.0)
    current = 18000.0  # ~5.5 % from each side
    result = indicators.compute_high_low_distance(df, current, ticker="^GDAXI")
    assert result is not None
    assert result.is_near_high is False
    assert result.is_near_low is False


def test_high_low_current_zero_returns_none():
    df = _daily_hl(rolling_high=19000.0, rolling_low=17000.0)
    assert indicators.compute_high_low_distance(df, 0.0, ticker="^GDAXI") is None


def test_high_low_empty_returns_none():
    assert indicators.compute_high_low_distance(_empty(), 18000.0, ticker="^GDAXI") is None


# -- hygiene helpers ----------------------------------------------------------

def test_ffill_gaps_fills_nan():
    df = _bars_from_closes([18000.0, 18010.0, 18020.0, 18030.0])
    df.iloc[2, df.columns.get_loc("Close")] = math.nan
    filled = indicators._ffill_gaps(df)
    assert not filled["Close"].isna().any()
    # The NaN at row 2 is filled from row 1 (18010.0).
    assert filled["Close"].iloc[2] == 18010.0


def test_drop_outliers_removes_spike():
    df = _bars_from_closes([18000.0, 18010.0, 18020.0, 30000.0, 18030.0])  # one spike
    cleaned = indicators._drop_outliers(df)
    assert 30000.0 not in list(cleaned["Close"])
    assert len(cleaned) == 4


def test_drop_outliers_iqr_zero_is_noop():
    df = _bars_from_closes([18000.0, 18000.0, 18000.0, 18000.0])  # constant → IQR 0
    cleaned = indicators._drop_outliers(df)
    assert len(cleaned) == len(df)
