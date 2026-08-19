"""``BarService`` — the one bar-reading seam for research and the paper tracker (D8/D9).

Phase 13 §6 A2 cut: ``get_window`` is a pure archive read. Acquisition is a separate
subsystem (S1 Lightstreamer, S2 yF-Recorder, S3 external, S4 IG-rescue) that writes
into the same ``BarArchive``; consumers never fetch. Replaces the two budget-blind
IG-bar paths of Phase 12 — the research ``enable_ig_bars`` chain and the paper
tracker's raw ``broker.get_ohlcv(epic, "MINUTE", 300)`` calls — and the chain itself
only feeds the *research* seam (``get_bars``); the tracker seam never buys.

The structural cost guarantee (L12) is ``test_get_window_never_fetches`` in
``tests/test_service.py`` — an IG-provider whose ``get_bars`` raises ``AssertionError``
must never be reached on the tracker path.

``BudgetedIGBarProvider`` and ``BarService`` both implement the Phase-3
``external_data.providers.BarProvider`` Protocol (duck-typed, no import of a base class
needed) so ``BarService`` can be handed straight to ``MarketDataFetcher(bar_provider=...)``
exactly like a plain ``ChainedBarProvider`` was before.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Sequence

import logging

from data_foundation.exceptions import ArchiveError
from data_foundation.models import Bar, normalize_bar_ts

logger = logging.getLogger("data_foundation.service")

# Phase-3-side resolution names -> minutes per bar (kept because the research seam
# uses it to derive the window span from a `count`).
_RESOLUTION_MINUTES: dict[str, int] = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "1d": 1440}


def _default_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def _age_minutes(ts: str, now: datetime) -> float:
    """Minutes between ``ts`` (ISO 8601 UTC) and ``now``. Used by the A4 stale-tolerance
    check. Returns float minutes; .tzaware on both sides via ``_parse_iso``."""
    normalized = ts.replace("Z", "+00:00") if ts.endswith("Z") else ts
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (now - dt).total_seconds() / 60.0


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
        stale_tolerance_min: int = 120,
    ) -> None:
        self._broker = broker
        self._budget = budget
        self._spend_kind = spend_kind
        self._health_sink = health_sink
        self._now_fn = now_fn
        # Phase 13 §6 A4 (L8): how old a bar's `ts` may be before we treat the bundle
        # as stale. 120 min was the empirical floor for F1 (one-month-old IG Forward
        # history with `ok=True`). Default; the sampler in A6 has its own knob — see
        # Plan §6 A6.1 for the deliberate non-sharing.
        self._stale_tolerance_min = stale_tolerance_min

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
        try:
            bars = [
                PriceBar(
                    ts=normalize_bar_ts(b.get("timestamp", "")),
                    open=float(b.get("open", 0.0)),
                    high=float(b.get("high", 0.0)),
                    low=float(b.get("low", 0.0)),
                    close=float(b.get("close", 0.0)),
                    volume=float(b.get("volume", 0.0)),
                )
                for b in raw_bars
            ]
        except ArchiveError:
            self._emit(epic, False, reason="bad_timestamp")
            return None
        self._budget.record_spend(len(bars), self._spend_kind)
        # Phase 13 §6 A4 (L8): IG may return a bundle whose newest bar is hours or days
        # old while the envelope still says ok=True (F1 — IX.D.IBEX.FWM2.IP, 301 bars
        # with ts 2026-07-17 + fetched_at 2026-08-18). Reject such bundles; the call
        # has already been billed by IG, so the spend above is correct — do NOT move
        # this check before record_spend, or the ledger under-reports.
        newest = max(b.ts for b in bars)
        if _age_minutes(newest, self._now_fn()) > self._stale_tolerance_min:
            self._emit(epic, False, reason="stale_history")
            return None
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
    """Archive-first bar access — implements the ``BarProvider`` Protocol.

    Two seams:

    - ``get_bars`` (research): archive → chain fallback. The chain is still budgeted
      and writes through with provenance, so a research call can source fresh data
      when the archive's coverage is short. This is the seam that legitimately
      *wants* fresh data — leaving it on the chain is L15.
    - ``get_window`` (tracker): pure archive read (Phase 13 §6 A2 / L1, L2). No
      chain. No budget. The tracker resolves paper trades from the archive only;
      when the trade's window is not yet covered, the guard sits in the caller
      (the ``window_ok`` closure, Plan §6 A3), not here.

    ``providers`` is a ``Sequence[tuple[str, BarProvider]]`` — the same shape
    ``external_data.providers.ChainedBarProvider`` takes. The chain is built and
    used only by ``get_bars``; it is irrelevant to the tracker seam.
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

    # -- tracker seam (Phase 13 A2: pure archive read) ------------------------

    def get_window(
        self, epic: str, resolution: str, start_utc: str, end_utc: str
    ) -> list[dict[str, Any]]:
        """Reine Archiv-Lesung. Fetcht nie (L1/L2) — Beschaffung ist ein eigenes Subsystem."""
        return [
            _bar_to_dict(b)
            for b in self._archive.window(epic, resolution, start_utc, end_utc)
        ]

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
                tick_count=getattr(b, "tick_count", None),
            )
            for b in bars
        ]
        try:
            self._archive.insert_bars(archive_bars)
        except Exception:  # noqa: BLE001 — a write-through failure must never break the
            # caller's read (the fetched bars are still returned/used); logged so a
            # persistent archive fault is visible, not silently swallowed forever.
            logger.warning("BarService write-through failed for %s/%s", epic, resolution, exc_info=True)


def _bar_to_dict(bar: Any) -> dict[str, Any]:
    return {
        "timestamp": bar.ts_utc, "open": bar.open, "high": bar.high,
        "low": bar.low, "close": bar.close, "source": bar.source,
        "tick_count": getattr(bar, "tick_count", None),
    }


def _bar_to_pricebar(bar: Any) -> Any:
    from external_data.models import PriceBar

    return PriceBar(
        ts=bar.ts_utc, open=bar.open, high=bar.high, low=bar.low,
        close=bar.close, volume=bar.volume or 0.0,
    )
