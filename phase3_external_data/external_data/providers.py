"""``BarProvider`` chain (Phase 9 / V2 Step 6) — IG primary, yFinance fallback.

Redundancy over two IG transport paths (real-time REST bars primary, the
already-verified Lightstreamer stream a later step) plus yFinance as an
independent, delayed cross-check (Plan D8) — never the other way around: the
Momentum VETO (Phase 5) already sources exclusively from IG real-time bars and
this module changes nothing about that (it is *research*-context data quality,
never a safety-layer input).

:class:`ChainedBarProvider` is the seam Phase 3's ``MarketDataFetcher`` can be
given (``bar_provider=``, additive, default ``None`` = today's yFinance-only
path, bit-identical) to prefer IG bars over yFinance for a given epic, falling
back automatically when IG has none. All three provider classes are duck-typed
(``BarProvider`` is a ``Protocol``, not a base class) and do no caching/rate-
limiting of their own — that stays the fetcher's job.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Protocol, Sequence

from .models import PriceBar

logger = logging.getLogger(__name__)


class BarProvider(Protocol):
    """Anything that can answer "give me ``count`` bars at ``resolution`` for ``epic``"."""

    def get_bars(self, epic: str, *, resolution: str, count: int) -> list[PriceBar] | None: ...


# Phase-3-side resolution names -> IG's ``get_ohlcv`` resolution strings.
_IG_RESOLUTION_MAP: dict[str, str] = {
    "1m": "MINUTE",
    "5m": "MINUTE_5",
    "15m": "MINUTE_15",
    "1h": "HOUR",
    "1d": "DAY",
}


class IGBarProvider:
    """Real-time bars from the Phase-1 broker's ``get_ohlcv`` (REST).

    Duck-typed ``broker`` (only ``get_ohlcv`` is called). Never raises: a
    broker exception, a not-ok envelope, an unmapped resolution, or an empty
    bar list all degrade to ``None`` — exactly like Phase 3's own off-hours
    discipline, so :class:`ChainedBarProvider` can treat every provider
    uniformly (``None`` = "try the next one").
    """

    def __init__(self, broker: Any) -> None:
        self._broker = broker

    def get_bars(self, epic: str, *, resolution: str, count: int) -> list[PriceBar] | None:
        ig_resolution = _IG_RESOLUTION_MAP.get(resolution)
        if ig_resolution is None:
            return None
        try:
            env = self._broker.get_ohlcv(epic, ig_resolution, count)
        except Exception:  # noqa: BLE001 — a provider must never crash the chain
            return None
        if not getattr(env, "ok", False):
            return None
        raw_bars = (getattr(env, "data", None) or {}).get("bars") or []
        if not raw_bars:
            return None
        return [
            PriceBar(
                ts=b.get("timestamp", ""),
                open=float(b.get("open", 0.0)),
                high=float(b.get("high", 0.0)),
                low=float(b.get("low", 0.0)),
                close=float(b.get("close", 0.0)),
                volume=float(b.get("volume", 0.0)),
            )
            for b in raw_bars
        ]


class YFinanceBarProvider:
    """Delegates to an already-constructed Phase-3 fetcher (no re-implementation).

    Preserves the fetcher's own off-hours discipline (an intraday resolution
    returns ``None`` outside market hours) and circuit breaker — this class is
    a thin adapter to the :class:`BarProvider` shape, not a second data path.
    """

    def __init__(self, fetcher: Any) -> None:
        self._fetcher = fetcher

    def get_bars(self, epic: str, *, resolution: str, count: int) -> list[PriceBar] | None:
        try:
            return self._fetcher.get_bars(epic, resolution=resolution, count=count)
        except Exception:  # noqa: BLE001 — a provider must never crash the chain
            return None


class ChainedBarProvider:
    """Tries each ``(name, provider)`` pair in order; the first non-``None`` wins.

    Emits a ``{"event": "bar_fetch", "provider": name, "epic": epic, "ok": bool}``
    to ``health_sink`` per attempt (Phase 8 observability — diagnostic only,
    gates nothing) if one is given.
    """

    def __init__(
        self,
        providers: Sequence[tuple[str, BarProvider]],
        health_sink: Callable[[dict], None] | None = None,
    ) -> None:
        self._providers = list(providers)
        self._health_sink = health_sink

    def get_bars(self, epic: str, *, resolution: str, count: int) -> list[PriceBar] | None:
        for name, provider in self._providers:
            try:
                bars = provider.get_bars(epic, resolution=resolution, count=count)
            except Exception:  # noqa: BLE001 — a provider must never crash the chain
                bars = None
            ok = bars is not None
            if self._health_sink is not None:
                try:
                    self._health_sink({"event": "bar_fetch", "provider": name, "epic": epic, "ok": ok})
                except Exception:  # noqa: BLE001 — a health sink must never break the chain
                    logger.warning("bar_fetch health_sink failed", exc_info=True)
            if ok:
                return bars
        return None
