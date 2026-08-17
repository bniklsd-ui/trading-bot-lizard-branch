"""``BarService`` — the one bar-fetching seam for research and the paper tracker (D8/D9).

Archive-first (``BarArchive``, Step 1), then a budget-aware fallback chain (yFinance
first — free — IG only on a real gap, Nikinger-decision this session, resolves a
contradiction between D9's prose and the plan's original chain-order sketch), every
externally-fetched bar written through with provenance (``source``). Replaces two
independent, budget-blind IG-bar paths: the research ``enable_ig_bars`` chain
(``phase8_scheduler/scripts/wiring.py::_build_market_data``, default off, "gebaut, nie
gelaufen" — the Phase-11 root cause) and the paper tracker's raw
``broker.get_ohlcv(epic, "MINUTE", 300)`` call with its own ad-hoc allowance guesswork.

``BudgetedIGBarProvider`` and ``BarService`` both implement the Phase-3
``external_data.providers.BarProvider`` Protocol (duck-typed, no import of a base class
needed) so ``BarService`` can be handed straight to ``MarketDataFetcher(bar_provider=...)``
exactly like a plain ``ChainedBarProvider`` was before.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Sequence

import logging

from data_foundation.models import Bar, normalize_bar_ts

logger = logging.getLogger("data_foundation.service")

# Phase-3-side resolution names -> minutes per bar (for count/window-span estimation).
# Mirrors external_data.providers._IG_RESOLUTION_MAP's key set exactly.
_RESOLUTION_MINUTES: dict[str, int] = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "1d": 1440}


def _default_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def _parse_iso(ts: str) -> datetime:
    normalized = ts.replace("Z", "+00:00") if ts.endswith("Z") else ts
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


class BudgetedIGBarProvider:
    """IG real-time bars, gated on :class:`~data_foundation.budget.SourceBudget` (D10).

    Duplicates ``external_data.providers.IGBarProvider``'s epic->IG-resolution mapping
    and envelope handling rather than wrapping it — this class needs the raw ``env`` to
    read ``env.data["allowance"]`` (booked via ``budget.record_allowance``) and to gate
    the call on ``budget.can_spend`` *before* the broker is touched, neither of which
    ``IGBarProvider`` exposes (adding them would change a Phase-3 class's contract for a
    Phase-12 need). Never raises — a provider must always degrade to ``None`` (mirrors
    ``IGBarProvider``'s own contract, ``providers.py:47-52``).
    """

    def __init__(
        self,
        broker: Any,
        budget: Any,
        *,
        spend_kind: str = "research",
        health_sink: Callable[[dict], None] | None = None,
        now_fn: Callable[[], datetime] = _default_now,
    ) -> None:
        self._broker = broker
        self._budget = budget
        self._spend_kind = spend_kind
        self._health_sink = health_sink
        self._now_fn = now_fn

    def _emit(self, epic: str, ok: bool, *, reason: str | None = None) -> None:
        if self._health_sink is None:
            return
        event: dict[str, Any] = {
            "event": "bar_fetch", "provider": "ig", "epic": epic, "ok": ok,
            "spend_kind": self._spend_kind,
        }
        if reason is not None:
            event["reason"] = reason
        try:
            self._health_sink(event)
        except Exception:  # noqa: BLE001 — a health sink must never break the chain
            pass

    def get_bars(self, epic: str, *, resolution: str, count: int) -> list[Any] | None:
        from external_data.providers import _IG_RESOLUTION_MAP
        from external_data.models import PriceBar

        ig_resolution = _IG_RESOLUTION_MAP.get(resolution)
        if ig_resolution is None:
            return None
        if not self._budget.can_spend(count):
            self._emit(epic, False, reason="budget")
            return None
        try:
            env = self._broker.get_ohlcv(epic, ig_resolution, count)
        except Exception:  # noqa: BLE001 — a provider must never crash the chain
            self._emit(epic, False, reason="exception")
            return None
        if not getattr(env, "ok", False):
            self._emit(epic, False, reason="not_ok")
            return None
        data = getattr(env, "data", None) or {}
        raw_bars = data.get("bars") or []
        if not raw_bars:
            self._emit(epic, False, reason="empty")
            return None
        bars = [
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
        self._budget.record_spend(len(bars), self._spend_kind)
        allowance = data.get("allowance") or {}
        if allowance:
            expiry_seconds = allowance.get("allowanceExpiry")
            expiry_iso = (
                _iso(self._now_fn() + timedelta(seconds=int(expiry_seconds)))
                if expiry_seconds is not None else None
            )
            self._budget.record_allowance(
                allowance.get("totalAllowance"),
                allowance.get("remainingAllowance"),
                expiry_iso,
            )
        self._emit(epic, True)
        return bars


class BarService:
    """Archive-first, budget-aware bar access — implements the ``BarProvider`` Protocol.

    ``providers`` is a ``Sequence[tuple[str, BarProvider]]``, the same shape
    ``external_data.providers.ChainedBarProvider`` takes — this class builds its own
    internal ``ChainedBarProvider`` over it, wrapping ``health_sink`` so every event still
    reaches the caller's sink unchanged *and* the winning provider's name is captured for
    the write-through ``source`` tag (``ChainedBarProvider`` itself is reused unmodified,
    not reimplemented — it never exposes which leg won, only whether the overall call
    succeeded, via its ``health_sink`` events).
    """

    def __init__(
        self,
        archive: Any,
        providers: Sequence[tuple[str, Any]],
        budget: Any,
        *,
        health_sink: Callable[[dict], None] | None = None,
        now_fn: Callable[[], datetime] = _default_now,
    ) -> None:
        from external_data.providers import ChainedBarProvider

        self._archive = archive
        self._budget = budget
        self._now_fn = now_fn
        self._ig_provider = dict(providers).get("ig")
        self._last_source: str | None = None

        def _capture(event: dict[str, Any]) -> None:
            if event.get("event") == "bar_fetch" and event.get("ok"):
                self._last_source = event.get("provider")
            if health_sink is not None:
                health_sink(event)

        self._chain = ChainedBarProvider(list(providers), health_sink=_capture)

    # -- research seam --------------------------------------------------------

    def get_bars(self, epic: str, *, resolution: str, count: int) -> list[Any] | None:
        minutes = _RESOLUTION_MINUTES.get(resolution)
        if minutes is None:
            return None
        end = self._now_fn()
        start = end - timedelta(minutes=minutes * count)
        if self._archive.coverage_ratio(epic, resolution, _iso(start), _iso(end)) >= 1.0:
            bars = self._archive.window(epic, resolution, _iso(start), _iso(end))
            return [_bar_to_pricebar(b) for b in bars[-count:]] if bars else None

        self._last_source = None
        bars = self._chain.get_bars(epic, resolution=resolution, count=count)
        if bars:
            self._write_through(epic, resolution, bars, self._last_source)
        return bars

    # -- tracker seam -----------------------------------------------------------

    def get_window(
        self, epic: str, resolution: str, start_utc: str, end_utc: str
    ) -> list[dict[str, Any]]:
        minutes = _RESOLUTION_MINUTES.get(resolution, 1)
        archived = self._archive.window(epic, resolution, start_utc, end_utc)
        if _covers_tail(archived, end_utc, minutes):
            return [_bar_to_dict(b) for b in archived]

        count = max(1, int((_parse_iso(end_utc) - _parse_iso(start_utc)).total_seconds() // 60 // minutes) + 1)
        self._last_source = None
        bars = self._chain.get_bars(epic, resolution=resolution, count=count)
        if bars:
            self._write_through(epic, resolution, bars, self._last_source)
            archived = self._archive.window(epic, resolution, start_utc, end_utc)

        if not _covers_tail(archived, end_utc, minutes) and self._ig_provider is not None:
            # yF alone didn't reach the tail (off-hours/short/empty — known intraday
            # intermittency, phase3_external_data/CLAUDE.md). Explicit IG top-up,
            # bypassing chain order — get_window's correctness matters more than its
            # cost here; the tracker's staleness/attempt caps are the final backstop,
            # not a substitute for trying IG when yF genuinely came up short.
            ig_bars = self._ig_provider.get_bars(epic, resolution=resolution, count=count)
            if ig_bars:
                self._write_through(epic, resolution, ig_bars, "ig")
                archived = self._archive.window(epic, resolution, start_utc, end_utc)

        return [_bar_to_dict(b) for b in archived]

    # -- shared -------------------------------------------------------------

    def _write_through(
        self, epic: str, resolution: str, bars: Sequence[Any], source: str | None
    ) -> None:
        if source is None:
            return
        fetched_at = _iso(self._now_fn())
        archive_bars = [
            Bar(
                epic=epic, resolution=resolution, ts_utc=normalize_bar_ts(b.ts),
                open=b.open, high=b.high, low=b.low, close=b.close, volume=b.volume,
                source=source, fetched_at=fetched_at,
            )
            for b in bars
        ]
        try:
            self._archive.insert_bars(archive_bars)
        except Exception:  # noqa: BLE001 — a write-through failure must never break the
            # caller's read (the fetched bars are still returned/used); logged so a
            # persistent archive fault is visible, not silently swallowed forever.
            logger.warning("BarService write-through failed for %s/%s", epic, resolution, exc_info=True)


def _covers_tail(bars: Sequence[Any], end_utc: str, resolution_minutes: int) -> bool:
    """Whether ``bars``' latest timestamp reaches within one bar-interval of ``end_utc``
    (i.e. the window is current, not just partially populated)."""
    if not bars:
        return False
    latest = bars[-1].ts_utc
    cutoff = _iso(_parse_iso(end_utc) - timedelta(minutes=resolution_minutes))
    return latest >= cutoff


def _bar_to_dict(bar: Any) -> dict[str, Any]:
    return {
        "timestamp": bar.ts_utc, "open": bar.open, "high": bar.high,
        "low": bar.low, "close": bar.close, "source": bar.source,
    }


def _bar_to_pricebar(bar: Any) -> Any:
    from external_data.models import PriceBar

    return PriceBar(
        ts=bar.ts_utc, open=bar.open, high=bar.high, low=bar.low,
        close=bar.close, volume=bar.volume or 0.0,
    )
