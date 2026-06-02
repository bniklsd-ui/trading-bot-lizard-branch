"""Smoke test for the package's public exports (concept §18).

No network, no fixtures: importing the top-level names must not trigger a yFinance
import (``_raw_download`` imports it lazily), so this also guards the "package imports
clean without yfinance" invariant the whole test suite relies on.
"""

from __future__ import annotations

import external_data
from external_data import FileCache, MarketDataFetcher, TickerMapper


def test_top_level_names_importable():
    # The three concept-§18 entry points are importable from the package root.
    assert MarketDataFetcher is not None
    assert TickerMapper is not None
    assert FileCache is not None


def test_exports_are_the_submodule_objects():
    # Top-level names are the very same objects as their submodule definitions
    # (re-exports, not shadow copies).
    assert external_data.MarketDataFetcher is external_data.fetcher.MarketDataFetcher
    assert external_data.TickerMapper is external_data.ticker_map.TickerMapper
    assert external_data.FileCache is external_data.cache.FileCache


def test_all_lists_exactly_the_three_entry_points():
    assert set(external_data.__all__) == {"MarketDataFetcher", "TickerMapper", "FileCache"}
