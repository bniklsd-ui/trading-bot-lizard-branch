"""The market-data fetcher — Phase 3's public interface (concept §11).

``MarketDataFetcher`` ties together the mapper, the on-disk cache, the market-hours
guard and the pure indicator functions behind a **single network point**,
:func:`_raw_download`. Every public method follows the same pipeline:

    epic → yf symbol  (EpicNotMappedError propagates — programmer error)
      → off-hours guard (intraday methods return None outside trading hours)
      → cache lookup    (hit → no network)
      → rate-limited fetch + retry (the only place that touches yFinance)
      → cache.set
      → hygiene + indicator compute → dataclass

Design rules encoded here (concept §11/§12, top-level CLAUDE.md):

- **One network site.** :func:`_raw_download` is the *only* function that imports
  and calls yFinance. It is imported lazily so the package (and the whole unit-test
  suite) runs with yFinance absent; tests monkeypatch this function.
- **No custom session.** yFinance ≥ 0.2.6x drives ``curl_cffi`` internally; passing
  a ``requests.Session`` raises ``YFDataException``. We pass nothing.
- **Two failure modes, both retried** with exponential backoff: a yFinance
  ``YFRateLimitError`` (detected by class name to avoid importing yFinance) becomes
  :class:`RateLimitError`; an empty / too-short DataFrame becomes
  :class:`DataUnavailableError`.
- **Off-hours discipline.** Intraday methods return ``None`` (never a stale cache
  value served as fresh) outside 09:00–17:30 Europe/Berlin. Daily-based methods run
  any time.
- **Delay honesty.** Momentum/drift carry ``is_realtime=False`` (set by the indicator
  functions): yFinance ``^GDAXI`` is a delayed quote.
"""

from __future__ import annotations

import logging
import time as _time
from datetime import timedelta
from zoneinfo import ZoneInfo

import pandas as pd

from . import indicators, timeutil
from .cache import FileCache
from .exceptions import DataUnavailableError, ExternalDataError, RateLimitError
from .market_hours import is_market_open
from .models import (
    BrainContext,
    DriftResult,
    HighLowDistance,
    MomentumResult,
    PriceBar,
    VolumeAnomaly,
)
from .ticker_map import TickerMapper

log = logging.getLogger(__name__)

_TZ = ZoneInfo("Europe/Berlin")

# Indirection so tests can neutralise both the rate-limiter and the backoff waits
# (``monkeypatch.setattr(fetcher, "_SLEEP", lambda s: None)``) without real delays.
_SLEEP = _time.sleep

# Retry budget for the single network call (concept §11 / correction §1.2).
_MAX_RETRIES = 3
_BACKOFF_BASE_S = 1.0

# yFinance's rate-limit exception is matched by class name so this module never
# has to import yFinance at top level (keeps unit tests yFinance-free).
_RATE_LIMIT_EXC_NAMES = {"YFRateLimitError"}

# Cache TTLs by bar resolution (concept §9). ``1d`` is special-cased to expire at
# the next Europe/Berlin midnight (the day's bar is final once the day rolls over).
_INTRADAY_TTL_S = {"5m": 120, "30m": 300}


# -- the one network point ----------------------------------------------------

def _raw_download(symbol: str, *, period: str, interval: str) -> "pd.DataFrame":
    """Download raw OHLCV from yFinance — the **only** network call site.

    yFinance is imported lazily here so the rest of the package imports cleanly
    without it; the unit tests monkeypatch this function and never hit the network.
    No ``requests.Session`` is passed — yFinance handles session/cookies/crumb via
    ``curl_cffi`` itself (passing one raises ``YFDataException`` since 0.2.6x).

    Args:
        symbol: yFinance symbol (e.g. ``"^GDAXI"``).
        period: yFinance period string (e.g. ``"1d"``, ``"60d"``, ``"6mo"``).
        interval: yFinance interval string (e.g. ``"1d"``, ``"5m"``).

    Returns:
        The yFinance ``Ticker.history()`` DataFrame.
    """
    import yfinance as yf

    return yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=False)


def _is_rate_limit_error(exc: BaseException) -> bool:
    """Return whether ``exc`` is yFinance's rate-limit error, matched by class name.

    Matching by name (rather than ``isinstance``) avoids importing yFinance at
    module level, so unit tests can simulate it with a locally-defined
    ``YFRateLimitError`` class.
    """
    return any(t.__name__ in _RATE_LIMIT_EXC_NAMES for t in type(exc).__mro__)


def _fetch_with_retry(
    symbol: str, *, period: str, interval: str, min_expected: int = 1
) -> "pd.DataFrame":
    """Fetch via :func:`_raw_download` with exponential backoff over both failure modes.

    Backoff is ``1s → 2s → 4s`` across at most :data:`_MAX_RETRIES` attempts:

    - A yFinance rate-limit error (``YFRateLimitError``) is retried, then on
      exhaustion re-raised as :class:`RateLimitError`.
    - A ``None`` / empty / shorter-than-``min_expected`` DataFrame is retried, then
      on exhaustion raised as :class:`DataUnavailableError`.
    - Any other exception propagates unchanged (e.g. real programmer errors).

    Args:
        symbol: yFinance symbol.
        period: yFinance period string.
        interval: yFinance interval string.
        min_expected: Minimum acceptable row count; fewer rows is treated as an
            unusable (too-short) frame.

    Returns:
        A non-empty DataFrame with at least ``min_expected`` rows.

    Raises:
        RateLimitError: yFinance kept rate-limiting us past the retry budget.
        DataUnavailableError: no usable data after the retry budget.
    """
    for attempt in range(_MAX_RETRIES):
        last_attempt = attempt == _MAX_RETRIES - 1
        try:
            df = _raw_download(symbol, period=period, interval=interval)
        except Exception as exc:  # noqa: BLE001 — narrowed immediately below
            if not _is_rate_limit_error(exc):
                raise
            log.warning("rate-limited fetching %s (attempt %d/%d)", symbol, attempt + 1, _MAX_RETRIES)
            if last_attempt:
                raise RateLimitError(f"yFinance rate-limited for {symbol!r}", retryable=True) from exc
            _SLEEP(_BACKOFF_BASE_S * (2 ** attempt))
            continue

        if df is None or df.empty or len(df) < min_expected:
            got = 0 if df is None else len(df)
            log.warning(
                "empty/short data for %s (got %d, want >= %d, attempt %d/%d)",
                symbol, got, min_expected, attempt + 1, _MAX_RETRIES,
            )
            if last_attempt:
                raise DataUnavailableError(
                    f"no usable data for {symbol!r} (got {got} rows, want >= {min_expected})",
                    retryable=True,
                )
            _SLEEP(_BACKOFF_BASE_S * (2 ** attempt))
            continue

        return df

    # Unreachable: the loop either returns or raises on the last attempt.
    raise DataUnavailableError(f"no usable data for {symbol!r}", retryable=True)


# -- (de)serialisation between DataFrames and cacheable records ----------------

def _df_to_records(df: "pd.DataFrame") -> list[dict]:
    """Serialise an OHLCV DataFrame to a JSON-friendly ``list[dict]`` for the cache.

    Each record carries the bar's timestamp as canonical ISO 8601 UTC plus the five
    OHLCV floats. NaN volume (common on indices) is stored as ``0.0``.
    """
    records: list[dict] = []
    for ts, row in df.iterrows():
        volume = row["Volume"]
        records.append(
            {
                "ts": timeutil.iso_from_dt(ts.to_pydatetime()),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": 0.0 if pd.isna(volume) else float(volume),
            }
        )
    return records


def _records_to_df(records: list[dict]) -> "pd.DataFrame":
    """Rebuild a yFinance-shaped OHLCV DataFrame from cached records.

    Columns ``Open/High/Low/Close/Volume`` on a tz-aware (UTC) ``DatetimeIndex``,
    so the indicator functions see the same shape whether the data came from a
    cache hit or a fresh fetch.
    """
    if not records:
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
    index = pd.to_datetime([r["ts"] for r in records], utc=True)
    return pd.DataFrame(
        {
            "Open": [r["open"] for r in records],
            "High": [r["high"] for r in records],
            "Low": [r["low"] for r in records],
            "Close": [r["close"] for r in records],
            "Volume": [r["volume"] for r in records],
        },
        index=index,
    )


def _records_to_bars(records: list[dict]) -> list[PriceBar]:
    """Map cached records directly to :class:`PriceBar` objects."""
    return [
        PriceBar(
            ts=r["ts"],
            open=r["open"],
            high=r["high"],
            low=r["low"],
            close=r["close"],
            volume=r["volume"],
        )
        for r in records
    ]


# -- rate limiter -------------------------------------------------------------

class RateLimiter:
    """Token-bucket limiter enforcing a minimum gap between network calls.

    A single shared instance is held by the fetcher; :meth:`wait` blocks (via the
    module-level :data:`_SLEEP`) until at least ``min_interval_s`` has elapsed since
    the previous call. The first call never blocks.
    """

    def __init__(self, min_interval_s: float = 0.5) -> None:
        """Args:
        min_interval_s: Minimum seconds between consecutive network calls.
        """
        self._min_interval_s = min_interval_s
        self._last_call: float | None = None

    def wait(self) -> None:
        """Block until the minimum interval since the previous call has elapsed."""
        now = _time.monotonic()
        if self._last_call is not None:
            elapsed = now - self._last_call
            if elapsed < self._min_interval_s:
                _SLEEP(self._min_interval_s - elapsed)
        self._last_call = _time.monotonic()


# -- TTL / partition helpers --------------------------------------------------

def _today_berlin_str() -> str:
    """Today's date in Europe/Berlin as ``YYYY-MM-DD`` (cache-key partition)."""
    return timeutil._utcnow().astimezone(_TZ).date().isoformat()


def _seconds_until_berlin_midnight() -> int:
    """Seconds from now until the next Europe/Berlin midnight (>= 1).

    Used as the daily-bar TTL: a ``1d`` bar is final once the local day rolls over.
    Reads the clock via :func:`timeutil._utcnow` so a frozen test clock is honoured.
    """
    now_local = timeutil._utcnow().astimezone(_TZ)
    next_midnight = (now_local + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return max(1, int((next_midnight - now_local).total_seconds()))


def _ttl_for_resolution(resolution: str) -> int:
    """TTL in seconds for a bar resolution (concept §9)."""
    if resolution == "1d":
        return _seconds_until_berlin_midnight()
    return _INTRADAY_TTL_S.get(resolution, 120)


def _is_intraday_resolution(resolution: str) -> bool:
    """Whether a resolution is intraday (minute/hour bars → off-hours guarded)."""
    return resolution.endswith(("m", "h"))


# -- the fetcher --------------------------------------------------------------

class MarketDataFetcher:
    """Cached, rate-limited yFinance access plus indicator computation.

    The public interface for Phase 4 (research), Phase 5 (pre-trade context only)
    and Phase 7 (Longterm Brain). Construct with a :class:`TickerMapper` and a
    :class:`FileCache`; a default :class:`RateLimiter` is created if none is given.
    """

    def __init__(
        self,
        ticker_mapper: TickerMapper,
        cache: FileCache,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        """Args:
        ticker_mapper: Resolves IG epics to yFinance symbols (+ volume proxies).
        cache: On-disk TTL cache for serialised bars.
        rate_limiter: Optional shared limiter; a 0.5 s default is used if omitted.
        """
        self._mapper = ticker_mapper
        self._cache = cache
        self._rate_limiter = rate_limiter or RateLimiter()

    # -- core fetch+cache helper ------------------------------------------

    def _get_records(
        self,
        symbol: str,
        *,
        resolution: str,
        period: str,
        interval: str,
        min_expected: int = 1,
    ) -> list[dict]:
        """Return cached records for ``symbol``/``resolution`` or fetch + cache them.

        A cache hit returns immediately (no network). A miss waits on the rate
        limiter, fetches with retry, serialises and caches the result.
        """
        key = self._cache.make_key(symbol, resolution, _today_berlin_str())
        cached = self._cache.get(key)
        if cached is not None:
            log.debug("cache hit %s", key)
            return cached

        log.debug("cache miss %s — fetching", key)
        self._rate_limiter.wait()
        df = _fetch_with_retry(symbol, period=period, interval=interval, min_expected=min_expected)
        records = _df_to_records(df)
        self._cache.set(key, records, _ttl_for_resolution(resolution))
        return records

    # -- Phase 4 (turbo_research) -----------------------------------------

    def get_drift(self, epic: str) -> DriftResult | None:
        """Intraday drift vs. today's open. ``None`` off-hours (intraday-guarded)."""
        symbol = self._mapper.epic_to_yf(epic)
        if not is_market_open():
            log.info("market closed, skipping intraday fetch (drift) for %s", symbol)
            return None
        daily = self._get_records(symbol, resolution="1d", period="5d", interval="1d")
        intraday = self._get_records(symbol, resolution="5m", period="1d", interval="5m")
        daily_df = indicators._ffill_gaps(_records_to_df(daily))
        intraday_df = _records_to_df(intraday)
        return indicators.compute_drift(daily_df, intraday_df, ticker=symbol)

    def get_bars(
        self, epic: str, resolution: str = "5m", count: int = 20
    ) -> list[PriceBar] | None:
        """Return the last ``count`` bars at ``resolution``.

        Intraday resolutions are off-hours guarded → ``None`` when the market is
        closed (concept §17.2; reconciles the §11 ``list[PriceBar]`` signature, which
        did not account for the off-hours discipline). A ``1d`` resolution always runs.
        """
        symbol = self._mapper.epic_to_yf(epic)
        intraday = _is_intraday_resolution(resolution)
        if intraday and not is_market_open():
            log.info("market closed, skipping intraday bars for %s", symbol)
            return None
        period = "1d" if intraday else _period_for_days(count)
        records = self._get_records(symbol, resolution=resolution, period=period, interval=resolution)
        bars = _records_to_bars(records)
        return bars[-count:] if count > 0 else bars

    def get_history(self, epic: str, days: int = 30) -> list[PriceBar]:
        """Return the last ``days`` daily bars (always runs — daily, off-hours safe)."""
        symbol = self._mapper.epic_to_yf(epic)
        records = self._get_records(
            symbol, resolution="1d", period=_period_for_days(days), interval="1d"
        )
        df = indicators._drop_outliers(indicators._ffill_gaps(_records_to_df(records)))
        bars = _records_to_bars(_df_to_records(df))
        return bars[-days:] if days > 0 else bars

    # -- Phase 5 (pre_trade — CONTEXT only, never a VETO source; concept §13) --

    def get_momentum(self, epic: str, minutes: int = 15) -> MomentumResult | None:
        """Short-window momentum (context signal). ``None`` off-hours.

        ``MomentumResult.is_realtime`` is always ``False`` — yFinance ``^GDAXI`` is
        ~15 min delayed, so this is **not** a hard-VETO input (see the Phase-5 flag
        in ``CLAUDE.md``).
        """
        symbol = self._mapper.epic_to_yf(epic)
        if not is_market_open():
            log.info("market closed, skipping intraday fetch (momentum) for %s", symbol)
            return None
        bars_back = max(1, round(minutes / 5))
        records = self._get_records(
            symbol, resolution="5m", period="1d", interval="5m", min_expected=bars_back + 1
        )
        return indicators.compute_momentum(_records_to_df(records), ticker=symbol, window_minutes=minutes)

    # -- Phase 7 (Longterm Brain) -----------------------------------------

    def get_volume_anomaly(self, epic: str, lookback_days: int = 30) -> VolumeAnomaly | None:
        """Volume z-score vs. a rolling lookback (always runs — daily).

        Uses the ETF-volume proxy when registered (``volume_available=True``,
        ``volume_source`` set); otherwise fetches the index symbol and degrades
        gracefully (``volume_available=False``, ``z_score=0.0``). Never returns
        ``None`` for the indicator itself — the ``| None`` is for ``DataUnavailable``
        tolerance in :meth:`get_brain_context`.
        """
        symbol = self._mapper.epic_to_yf(epic)
        proxy = self._mapper.epic_to_volume_yf(epic)
        fetch_symbol = proxy if proxy is not None else symbol
        records = self._get_records(
            fetch_symbol, resolution="1d", period=_period_for_days(lookback_days + 5), interval="1d"
        )
        daily_df = indicators._drop_outliers(indicators._ffill_gaps(_records_to_df(records)))
        return indicators.compute_volume_anomaly(
            daily_df,
            ticker=symbol,
            lookback_days=lookback_days,
            volume_available=proxy is not None,
            volume_source=proxy,
        )

    def get_high_low_distance(self, epic: str, lookback_days: int = 90) -> HighLowDistance | None:
        """Distance of the current price to a rolling high/low band (always runs).

        ``current_price`` is the last 5m close during market hours (falling back to
        the last daily close if that intraday fetch is unavailable), and the last
        daily close off-hours — so the indicator works at night too (Phase-7 lesson
        extraction after the close).
        """
        symbol = self._mapper.epic_to_yf(epic)
        records = self._get_records(
            symbol, resolution="1d", period=_period_for_days(lookback_days + 5), interval="1d"
        )
        daily_df = indicators._drop_outliers(indicators._ffill_gaps(_records_to_df(records)))
        if daily_df.empty:
            return None

        current_price = float(daily_df["Close"].iloc[-1])
        if is_market_open():
            try:
                intraday = self._get_records(symbol, resolution="5m", period="1d", interval="5m")
                current_price = float(_records_to_df(intraday)["Close"].iloc[-1])
            except DataUnavailableError:
                log.warning("intraday price unavailable for %s; using last daily close", symbol)

        return indicators.compute_high_low_distance(
            daily_df, current_price, ticker=symbol, lookback_days=lookback_days
        )

    # -- composite (Phase 4 + 7) ------------------------------------------

    def get_brain_context(self, epic: str) -> BrainContext | None:
        """Assemble a fail-tolerant :class:`BrainContext` across all indicators.

        ``epic_to_yf`` runs first and propagates :class:`EpicNotMappedError`
        (programmer error). Every other indicator is fetched in its own
        ``try/except`` over :class:`ExternalDataError`: a missing one becomes a
        ``None`` field plus a WARNING, never a crash. Off-hours intraday fields are
        simply ``None`` (the methods return ``None``, not an error).
        """
        symbol = self._mapper.epic_to_yf(epic)

        def _safe(label: str, fn):
            try:
                return fn()
            except ExternalDataError as exc:
                log.warning("brain_context: %s unavailable for %s (%s)", label, epic, exc)
                return None

        drift = _safe("drift", lambda: self.get_drift(epic))
        momentum = _safe("momentum", lambda: self.get_momentum(epic))
        volume = _safe("volume", lambda: self.get_volume_anomaly(epic))
        high_low = _safe("high_low", lambda: self.get_high_low_distance(epic))
        history = _safe("history", lambda: self.get_history(epic, days=30)) or []

        return BrainContext(
            ticker=epic,
            yf_symbol=symbol,
            drift=drift,
            momentum_15m=momentum,
            volume=volume,
            high_low=high_low,
            price_history_30d=history,
            generated_at=timeutil.utc_iso_now(),
        )


# -- period helper ------------------------------------------------------------

def _period_for_days(days: int) -> str:
    """Map a desired number of trading days to a yFinance daily ``period`` string.

    yFinance daily frames omit non-trading days, so we request a generous calendar
    window (≈ 2× the trading days requested, with sane floors) and the methods slice
    the tail. Capped at ``"2y"`` for very long lookbacks.
    """
    if days <= 5:
        return "1mo"
    if days <= 30:
        return "3mo"
    if days <= 90:
        return "1y"
    if days <= 180:
        return "2y"
    return "5y"
