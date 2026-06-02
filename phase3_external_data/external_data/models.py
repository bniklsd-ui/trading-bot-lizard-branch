"""Data contracts for the external-data layer.

These dataclasses are the integration surface to Phase 4 (research),
Phase 5 (pre-trade gates — context only) and Phase 7 (Longterm Brain).
Honesty about provenance is encoded in the fields themselves:

- ``is_realtime`` is **always** ``False`` for yFinance-sourced momentum:
  the upstream feed is delayed ~15 min for ``^GDAXI``. The LLM consumer
  must see this and the ``BrainContext.to_prompt_dict`` mirror exposes it.
- ``volume_available`` distinguishes "we have volume" from "this index
  reports zero volume". ``^GDAXI`` has no native volume; an optional
  ETF-proxy hook in :class:`TickerMapper` can supply one.

All timestamps are ISO 8601 UTC with ms precision and a ``Z`` suffix
(identical format to Phase 1/2 — see :mod:`external_data.timeutil`).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PriceBar:
    """One OHLCV bar, source-agnostic.

    Attributes:
        ts: ISO 8601 UTC timestamp of the bar's start.
        open: Opening price.
        high: High of the bar.
        low: Low of the bar.
        close: Closing price.
        volume: Traded volume; ``0.0`` if the source does not report volume.
    """

    ts: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class DriftResult:
    """Today's intraday drift versus the opening print.

    ``drift_pct`` is positive when the current price is above today's open
    (bullish drift) and negative when below. ``is_realtime`` is fixed to
    ``False`` for yFinance because the feed is delayed.
    """

    ticker: str
    today_open: float
    current_price: float
    drift_pct: float
    as_of: str
    is_realtime: bool = False


@dataclass
class MomentumResult:
    """Short-window momentum from 5-minute bars.

    ``window_minutes`` is the requested window (default 15). ``bars_back``
    inside the indicator function rounds the window to the nearest number
    of 5-minute bars. ``is_realtime`` is **always** ``False`` for yFinance:
    a "15-minute momentum" here measures a window ending ~15 min ago, so
    it is a context signal — not a hard-VETO input (see Phase-5 flag).
    """

    ticker: str
    window_minutes: int
    momentum_pct: float
    price_now: float
    price_start: float
    as_of: str
    source_resolution: str = "5m"
    is_realtime: bool = False


@dataclass
class VolumeAnomaly:
    """Z-score of today's volume vs. a rolling lookback.

    Degrades gracefully when the source does not report volume (e.g.
    ``^GDAXI`` without an ETF proxy): ``volume_available=False`` and
    ``z_score=0.0`` / ``is_anomaly=False`` / ``is_extreme=False``.

    Attributes:
        z_score: ``(today_volume - rolling_mean) / rolling_std``.
        is_anomaly: ``volume_available and abs(z_score) >= 2.0``.
        is_extreme: ``volume_available and abs(z_score) >= 3.0``.
        volume_available: ``False`` if the source reports no volume.
        volume_source: yFinance symbol the volume came from (``None`` if
            unavailable). Useful for audit when an ETF proxy is registered.
    """

    ticker: str
    today_volume: float
    rolling_mean: float
    rolling_std: float
    z_score: float
    is_anomaly: bool
    is_extreme: bool
    lookback_days: int
    as_of: str
    volume_available: bool = True
    volume_source: str | None = None


@dataclass
class HighLowDistance:
    """Distance of the current price to a rolling high/low band.

    ``distance_to_high_pct`` and ``distance_to_low_pct`` are non-negative
    percentages. ``is_near_high`` / ``is_near_low`` use a fixed 1.5 %
    threshold, matching the concept doc.
    """

    ticker: str
    lookback_days: int
    rolling_high: float
    rolling_low: float
    current_price: float
    distance_to_high_pct: float
    distance_to_low_pct: float
    is_near_high: bool
    is_near_low: bool
    as_of: str


@dataclass
class BrainContext:
    """Composite market-context payload assembled from all indicators.

    Used by Phase 4 (research prompt input) and Phase 7 (lesson
    extraction). Each indicator field is **optional** — a partial result
    is acceptable; ``MarketDataFetcher.get_brain_context`` is fail-tolerant
    and sets a sub-field to ``None`` rather than raising when one indicator
    is unavailable.

    Attributes:
        ticker: The original IG epic the caller passed in (not the yFinance
            symbol — that lives in ``yf_symbol``).
        yf_symbol: The yFinance symbol resolved from ``ticker``.
        price_history_30d: Daily bars for the last ~30 trading days.
        generated_at: ISO 8601 UTC timestamp of when this snapshot was built.
    """

    ticker: str
    yf_symbol: str
    drift: DriftResult | None
    momentum_15m: MomentumResult | None
    volume: VolumeAnomaly | None
    high_low: HighLowDistance | None
    price_history_30d: list[PriceBar] = field(default_factory=list)
    generated_at: str = ""

    def to_prompt_dict(self) -> dict[str, Any]:
        """Compact view for the LLM Research prompt.

        Only the fields the model needs to decide; raw OHLCV is intentionally
        omitted. Missing values are emitted as ``None`` rather than dropped
        so the LLM can see the gap explicitly.

        The exact key set is part of the Phase-4 / Phase-6 contract — do
        not rename or drop keys without bumping that contract.
        """
        drift_pct = self.drift.drift_pct if self.drift is not None else None
        momentum_pct = self.momentum_15m.momentum_pct if self.momentum_15m is not None else None
        momentum_realtime = (
            self.momentum_15m.is_realtime if self.momentum_15m is not None else False
        )

        if self.volume is not None:
            volume_z: float | None = self.volume.z_score if self.volume.volume_available else None
            volume_available = self.volume.volume_available
        else:
            volume_z = None
            volume_available = False

        dist_high = self.high_low.distance_to_high_pct if self.high_low is not None else None
        dist_low = self.high_low.distance_to_low_pct if self.high_low is not None else None

        if self.price_history_30d:
            highs = [bar.high for bar in self.price_history_30d]
            lows = [bar.low for bar in self.price_history_30d]
            range_30d: dict[str, float] | None = {"low": min(lows), "high": max(highs)}
        else:
            range_30d = None

        return {
            "ticker": self.ticker,
            "drift_pct": drift_pct,
            "momentum_15m_pct": momentum_pct,
            "momentum_is_realtime": momentum_realtime,
            "volume_z_score": volume_z,
            "volume_available": volume_available,
            "distance_to_high_pct": dist_high,
            "distance_to_low_pct": dist_low,
            "range_30d": range_30d,
            "generated_at": self.generated_at,
        }

    def to_dict(self) -> dict[str, Any]:
        """Full serialisation including ``price_history_30d``.

        Suitable for ``trade_lessons.market_context_json`` in Phase 2/7.
        Sub-dataclasses are converted via :func:`dataclasses.asdict`;
        ``None`` sub-fields are preserved.
        """
        return {
            "ticker": self.ticker,
            "yf_symbol": self.yf_symbol,
            "drift": asdict(self.drift) if self.drift is not None else None,
            "momentum_15m": asdict(self.momentum_15m) if self.momentum_15m is not None else None,
            "volume": asdict(self.volume) if self.volume is not None else None,
            "high_low": asdict(self.high_low) if self.high_low is not None else None,
            "price_history_30d": [asdict(bar) for bar in self.price_history_30d],
            "generated_at": self.generated_at,
        }
