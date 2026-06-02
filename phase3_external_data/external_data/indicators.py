"""Indicator computations — the deterministic core of Phase 3 (concept §10).

Pure functions: a pandas DataFrame goes in, a dataclass (or ``None``) comes out.
**No I/O, no network, no clock** — these functions never decide anything and never
gate an order; they only turn yFinance raw bars into the contract dataclasses in
:mod:`external_data.models`. The fetcher (``fetcher.py``) is responsible for fetching,
caching, off-hours discipline and for applying the hygiene helpers below before
calling these.

DataFrames follow the yFinance ``Ticker.history()`` shape: ``Open``/``High``/``Low``/
``Close``/``Volume`` columns on a (typically tz-aware) ``DatetimeIndex``. Every
function guards against empty data and division by zero.

Honesty notes encoded here (see concept §12):

- ``MomentumResult.is_realtime`` and ``DriftResult.is_realtime`` are always ``False``:
  yFinance ``^GDAXI`` is a delayed quote (~15 min). A "15-minute momentum" measured
  here is a context signal, never a hard-VETO input.
- Volume degrades gracefully: when ``volume_available`` is ``False`` (``^GDAXI``
  without an ETF proxy) the z-score is ``0.0`` and the anomaly flags are ``False``,
  but a fully-populated :class:`VolumeAnomaly` is still returned (never ``None``).
"""

from __future__ import annotations

import pandas as pd

from . import timeutil
from .models import DriftResult, HighLowDistance, MomentumResult, VolumeAnomaly

# Threshold constants (concept §10).
_ANOMALY_Z = 2.0
_EXTREME_Z = 3.0
_NEAR_PCT = 1.5
_OUTLIER_IQR_FACTOR = 3.0


def _bar_ts_iso(ts: pd.Timestamp) -> str:
    """Format a bar's index timestamp as canonical ISO 8601 UTC.

    A tz-naive timestamp is treated as UTC; a tz-aware one is converted to UTC.
    Delegates the actual formatting to :func:`timeutil.iso_from_dt` so the output
    matches every other timestamp in the codebase.
    """
    return timeutil.iso_from_dt(ts.to_pydatetime())


# -- main indicators ----------------------------------------------------------

def compute_drift(
    daily_df: pd.DataFrame, intraday_df: pd.DataFrame, *, ticker: str
) -> DriftResult | None:
    """Intraday drift of the current price versus today's open.

    ``today_open`` is the ``Open`` of the most recent daily bar; ``current_price``
    is the ``Close`` of the most recent intraday (5m) bar. The fetcher only calls
    this during market hours, so "most recent" == today.

    Args:
        daily_df: Daily bars (the last row is today's bar).
        intraday_df: 5-minute bars (the last row is the current price).
        ticker: yFinance symbol, stored on the result.

    Returns:
        A :class:`DriftResult`, or ``None`` if either frame is empty or
        ``today_open <= 0`` (no usable open).
    """
    if daily_df.empty or intraday_df.empty:
        return None

    today_open = float(daily_df["Open"].iloc[-1])
    if today_open <= 0:
        return None

    last_bar = intraday_df.iloc[-1]
    current_price = float(last_bar["Close"])
    drift_pct = (current_price - today_open) / today_open * 100.0

    return DriftResult(
        ticker=ticker,
        today_open=today_open,
        current_price=current_price,
        drift_pct=drift_pct,
        as_of=_bar_ts_iso(intraday_df.index[-1]),
        is_realtime=False,
    )


def compute_momentum(
    bars_5m_df: pd.DataFrame, *, ticker: str, window_minutes: int = 15
) -> MomentumResult | None:
    """Short-window momentum from 5-minute bars.

    ``bars_back = max(1, round(window_minutes / 5))`` (15 min → 3 bars). The
    momentum is the percentage change from the ``Close`` ``bars_back`` rows before
    the last bar to the last ``Close``.

    Args:
        bars_5m_df: 5-minute bars.
        ticker: yFinance symbol, stored on the result.
        window_minutes: Requested window in minutes (default 15).

    Returns:
        A :class:`MomentumResult` with ``is_realtime=False`` (delay-honest), or
        ``None`` if there are too few bars or the start price is non-positive.
    """
    bars = bars_5m_df.sort_index()
    bars_back = max(1, round(window_minutes / 5))
    if len(bars) < bars_back + 1:
        return None

    price_now = float(bars["Close"].iloc[-1])
    price_start = float(bars["Close"].iloc[-(bars_back + 1)])
    if price_start <= 0:
        return None

    momentum_pct = (price_now - price_start) / price_start * 100.0

    return MomentumResult(
        ticker=ticker,
        window_minutes=window_minutes,
        momentum_pct=momentum_pct,
        price_now=price_now,
        price_start=price_start,
        as_of=_bar_ts_iso(bars.index[-1]),
        source_resolution="5m",
        is_realtime=False,
    )


def compute_volume_anomaly(
    daily_df: pd.DataFrame,
    *,
    ticker: str,
    lookback_days: int = 30,
    volume_available: bool,
    volume_source: str | None,
) -> VolumeAnomaly:
    """Z-score of today's volume against a rolling lookback.

    Never returns ``None`` — when ``volume_available`` is ``False`` (e.g. ``^GDAXI``
    without an ETF proxy) it degrades to a fully-populated object with
    ``z_score=0.0`` and both anomaly flags ``False``.

    The rolling window is the ``lookback_days`` daily volumes **before** today.

    Args:
        daily_df: Daily bars (the last row is today).
        ticker: yFinance symbol (the IG-epic's mapped symbol).
        lookback_days: Number of prior days in the rolling window.
        volume_available: ``False`` if the source reports no real volume.
        volume_source: The yFinance symbol the volume came from (audit), or
            ``None`` when unavailable.

    Returns:
        A fully-populated :class:`VolumeAnomaly`.
    """
    as_of = _bar_ts_iso(daily_df.index[-1]) if not daily_df.empty else timeutil.utc_iso_now()
    today_volume = float(daily_df["Volume"].iloc[-1]) if not daily_df.empty else 0.0

    window = daily_df["Volume"].iloc[-(lookback_days + 1):-1] if not daily_df.empty else pd.Series(dtype=float)
    rolling_mean = float(window.mean()) if len(window) > 0 else 0.0
    # Sample std (ddof=1); a single-element window yields NaN → treat as 0.0.
    rolling_std = float(window.std()) if len(window) > 1 else 0.0
    if rolling_std != rolling_std:  # NaN guard
        rolling_std = 0.0

    if not volume_available or rolling_std == 0.0:
        z_score = 0.0
    else:
        z_score = (today_volume - rolling_mean) / rolling_std

    is_anomaly = volume_available and abs(z_score) >= _ANOMALY_Z
    is_extreme = volume_available and abs(z_score) >= _EXTREME_Z

    return VolumeAnomaly(
        ticker=ticker,
        today_volume=today_volume,
        rolling_mean=rolling_mean,
        rolling_std=rolling_std,
        z_score=z_score,
        is_anomaly=is_anomaly,
        is_extreme=is_extreme,
        lookback_days=lookback_days,
        as_of=as_of,
        volume_available=volume_available,
        volume_source=volume_source,
    )


def compute_high_low_distance(
    daily_df: pd.DataFrame,
    current_price: float,
    *,
    ticker: str,
    lookback_days: int = 90,
) -> HighLowDistance | None:
    """Distance of the current price to a rolling high/low band.

    The band is the max ``High`` / min ``Low`` over the last ``lookback_days``
    daily bars. Distances are signed percentages of ``current_price``.

    Args:
        daily_df: Daily bars.
        current_price: The reference price (in-hours: last 5m close; off-hours:
            last daily close — the fetcher decides which).
        ticker: yFinance symbol, stored on the result.
        lookback_days: Rolling-window length in days (default 90).

    Returns:
        A :class:`HighLowDistance`, or ``None`` if the frame is empty or
        ``current_price <= 0``.
    """
    if daily_df.empty or current_price <= 0:
        return None

    window = daily_df.iloc[-lookback_days:]
    rolling_high = float(window["High"].max())
    rolling_low = float(window["Low"].min())

    distance_to_high_pct = (rolling_high - current_price) / current_price * 100.0
    distance_to_low_pct = (current_price - rolling_low) / current_price * 100.0

    return HighLowDistance(
        ticker=ticker,
        lookback_days=lookback_days,
        rolling_high=rolling_high,
        rolling_low=rolling_low,
        current_price=current_price,
        distance_to_high_pct=distance_to_high_pct,
        distance_to_low_pct=distance_to_low_pct,
        is_near_high=distance_to_high_pct < _NEAR_PCT,
        is_near_low=distance_to_low_pct < _NEAR_PCT,
        as_of=_bar_ts_iso(daily_df.index[-1]),
    )


# -- hygiene helpers (applied by the fetcher before computing) ----------------

def _ffill_gaps(df: pd.DataFrame) -> pd.DataFrame:
    """Forward-fill NaN gaps (weekend/holiday holes) in a daily frame.

    Returns a copy; a no-op when the frame has no NaNs. yFinance daily frames
    omit non-trading days entirely, so this mainly fills the occasional missing
    field rather than whole rows.
    """
    return df.ffill()


def _drop_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Drop coarse ``Close`` outliers via an IQR filter.

    Keeps rows whose ``Close`` is within ``3 * IQR`` of the median ``Close``
    (``IQR = Q3 - Q1``). When ``IQR == 0`` (degenerate / constant series) the
    frame is returned unchanged, since no meaningful threshold exists.
    """
    if df.empty:
        return df
    close = df["Close"]
    q1 = close.quantile(0.25)
    q3 = close.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0:
        return df
    median = close.median()
    mask = (close - median).abs() <= _OUTLIER_IQR_FACTOR * iqr
    return df[mask]
