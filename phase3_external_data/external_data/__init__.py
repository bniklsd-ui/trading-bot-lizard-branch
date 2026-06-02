"""external_data — Phase 3 yFinance market-data layer.

Public entry points (concept §18): the three objects a downstream phase needs to
construct the layer —

    from external_data import MarketDataFetcher, TickerMapper, FileCache

The contract dataclasses (``PriceBar``, ``DriftResult``, …, ``BrainContext``) and the
exception hierarchy stay importable from their submodules (``external_data.models`` /
``external_data.exceptions``) — they are the integration surface for Phase 4/5/7 but
are intentionally kept out of the top-level ``__all__`` to keep the package's public
face small.

Importing this package is network-free: ``fetcher`` imports ``pandas`` at module top
(a hard dependency) but only imports ``yfinance`` lazily inside ``_raw_download``, so
``import external_data`` works without yFinance installed.
"""

from __future__ import annotations

from .cache import FileCache
from .fetcher import MarketDataFetcher
from .ticker_map import TickerMapper

__all__ = ["MarketDataFetcher", "TickerMapper", "FileCache"]
