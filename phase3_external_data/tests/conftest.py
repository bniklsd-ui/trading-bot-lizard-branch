"""Shared pytest fixtures for the external-data tests.

No network, no real credentials — yFinance is never reached (the only network
point, ``fetcher._raw_download``, is monkeypatched in later steps). This file
grows step-by-step per concept §15 (``tmp_cache``, ``sample_dax_daily``,
``sample_dax_5m`` arrive with the cache/indicator/fetcher steps).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest

from external_data import timeutil
from external_data.cache import FileCache


@pytest.fixture
def tmp_cache(tmp_path):
    """A :class:`FileCache` rooted at a per-test ``tmp_path`` subdirectory.

    Isolated from the real ``data/cache/`` and auto-cleaned by pytest. The
    directory is created lazily by ``FileCache.__init__``; using a subdir of
    ``tmp_path`` also exercises the ``parents=True`` mkdir path.
    """
    return FileCache(str(tmp_path / "cache"))


@pytest.fixture
def frozen_clock(monkeypatch):
    """Freeze ``timeutil._utcnow`` at a fixed instant.

    Returns a setter ``set(dt)`` so a test can choose the frozen UTC instant;
    defaults to Monday 2026-05-25 09:00:00 UTC (= 11:00 Europe/Berlin in CEST,
    well inside the trading window). Patching ``timeutil._utcnow`` covers every
    module that reads the clock module-qualified (e.g. ``market_hours``).
    """

    def set(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        monkeypatch.setattr(timeutil, "_utcnow", lambda: dt)
        return dt

    set(datetime(2026, 5, 25, 9, 0, 0, tzinfo=timezone.utc))
    return set


def _make_daily(volume_per_day: float) -> pd.DataFrame:
    """Build a deterministic daily OHLCV frame (~35 business days, DAX-ish).

    Close drifts gently up from ~18 000; High/Low straddle it; Open trails the
    prior close. The index is a tz-aware (Europe/Berlin) business-day range so
    the frame mirrors yFinance's daily ``^GDAXI`` shape.
    """
    index = pd.bdate_range("2026-04-06", periods=35, tz="Europe/Berlin")
    closes = [18000.0 + i * 12.0 for i in range(len(index))]
    opens = [closes[0]] + closes[:-1]  # each open = previous close
    highs = [c + 40.0 for c in closes]
    lows = [c - 45.0 for c in closes]
    volumes = [volume_per_day] * len(index)
    return pd.DataFrame(
        {"Open": opens, "High": highs, "Low": lows, "Close": closes, "Volume": volumes},
        index=index,
    )


@pytest.fixture
def sample_dax_daily() -> pd.DataFrame:
    """~35 daily bars with a steady non-zero volume (volume path available)."""
    return _make_daily(volume_per_day=1_000_000.0)


@pytest.fixture
def sample_dax_daily_zero_volume() -> pd.DataFrame:
    """Same shape but ``Volume=0`` — the ``^GDAXI`` no-native-volume degrade case."""
    return _make_daily(volume_per_day=0.0)


@pytest.fixture
def sample_dax_5m() -> pd.DataFrame:
    """Eight 5-minute bars on one trading morning (enough for a 15-min window).

    Close rises monotonically (17 980 → 18 015) so a positive-drift / positive-
    momentum scenario is the default; tests that need a negative sign slice or
    reorder this frame.
    """
    index = pd.date_range("2026-05-25T09:00:00", periods=8, freq="5min", tz="Europe/Berlin")
    closes = [17980.0, 17985.0, 17990.0, 17995.0, 18000.0, 18005.0, 18010.0, 18015.0]
    opens = [closes[0]] + closes[:-1]
    highs = [c + 8.0 for c in closes]
    lows = [c - 8.0 for c in closes]
    volumes = [5000.0] * len(index)
    return pd.DataFrame(
        {"Open": opens, "High": highs, "Low": lows, "Close": closes, "Volume": volumes},
        index=index,
    )
