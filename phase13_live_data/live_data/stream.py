"""Phase 13 §6 B2 — S1 live stream recorder.

Acquires completed 1-min candles from an
:class:`~broker_wrapper.streaming.ig_lightstreamer.IGLightstreamerClient`
and writes them through to the ``BarArchive`` with ``source='ls'`` (and
``tick_count`` from the LS field). The archive is the single source of
truth for downstream consumers — this recorder never returns a candle
to a caller, it only persists.

`TickAggregator` is the L6-fallback: when CHART is unavailable on the
account tier (Plan §6 B0 NO branch), we fall back to the existing
``PRICE:``-tick subscription and aggregate ticks into 1-min OHLC bars
in-process. ``tick_count`` is then the number of ticks that landed in
the minute — a candle with ``tick_count == 1`` is **not** a real OHLC
(it is one tick dressed up); the source-delta report (C3) tags such
bars separately as "thin".

Bauprinzip: fail-soft everywhere. A bad candle must not crash the
recorder; a failing archive write must not break the next one; a
token rotation must not lose the in-flight candle (it is flushed
or dropped with a logged warning, depending on ``complete``).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

logger = logging.getLogger("live_data.stream")

Resolution = str  # "1m" | "5m" | …
EpicsFn = Callable[[], list[str]]
HealthSink = Callable[[dict[str, Any]], None]


def _iso_utc_minute(dt: datetime) -> str:
    """Truncate to minute and return the ISO 8601 UTC string for the bar's open time."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    truncated = dt.replace(second=0, microsecond=0)
    ms = dt.microsecond // 1000
    return truncated.strftime("%Y-%m-%dT%H:%M:00.") + f"{ms:03d}Z"


@dataclass
class _TickBuffer:
    """One-minute open/high/low/close/volume accumulator for the L6 fallback."""

    minute_start_utc: str
    open: float = 0.0
    high: float = float("-inf")
    low: float = float("inf")
    close: float = 0.0
    tick_count: int = 0


class LSBarRecorder:
    """S1 — write-through IG-Lightstreamer candles to the archive.

    ``stream`` is anything that exposes ``start()``, ``stop()`` and
    ``subscribe_candles(epic, callback)`` — in production, the
    ``IGLightstreamerClient``; in tests, a tiny fake. ``epics_fn()``
    is called at start() and at every ``resync_epics()`` to ask **who**
    is currently measurable, so the recorder adapts to the universe
    without the wiring layer having to push a list.
    """

    def __init__(
        self,
        stream: Any,
        archive: Any,
        epics_fn: EpicsFn,
        *,
        resolution: str = "1m",
        health_sink: HealthSink | None = None,
    ) -> None:
        self._stream = stream
        self._archive = archive
        self._epics_fn = epics_fn
        self._resolution = resolution
        self._health_sink = health_sink
        self._subscribed: set[str] = set()
        # Phase 13 §6 B3: this recorder is restarted on token rotation; a
        # flag tells ``on_candle`` to drop in-flight writes during the
        # brief unsubscribe/resubscribe window.
        self._running = False

    # -- lifecycle ----------------------------------------------------------

    def start(self) -> None:
        """Start the underlying stream and subscribe to all measurable epics."""
        if self._running:
            return
        self._running = True
        self._stream.start()
        self._resync_epics()

    def stop(self) -> None:
        """Unsubscribe from all candles and stop the underlying stream. Idempotent."""
        if not self._running:
            return
        self._running = False
        for epic in list(self._subscribed):
            try:
                self._stream.unsubscribe_candles(epic)
            except Exception:  # noqa: BLE001 — recorder must not crash the daemon
                logger.debug("unsubscribe_candles for %s failed during stop", epic, exc_info=True)
        self._subscribed.clear()
        try:
            self._stream.stop()
        except Exception:  # noqa: BLE001
            logger.debug("stream.stop() raised", exc_info=True)

    def restart(self) -> None:
        """Token rotation hook (Plan §6 B3). Tear down and re-subscribe.

        New IGs CST/XST = new auth header. A candle that was in-flight
        when the old token died is dropped with a warning — the next
        candle is from the new token, and the recorder is back online.
        """
        logger.info("LSBarRecorder: restart (token rotation)")
        self.stop()
        self.start()

    def resync_epics(self) -> None:
        """Diff the universe against what we currently subscribe; add
        new, remove dropped. Called from ``universe_refresher`` after a
        SymbolResolver pass discovers fresh epics or quarantines some.
        """
        if not self._running:
            return
        self._resync_epics()

    # -- internals ----------------------------------------------------------

    def _resync_epics(self) -> None:
        try:
            current = set(self._epics_fn() or [])
        except Exception:  # noqa: BLE001 — never crash on a stale query
            logger.exception("epics_fn() raised during resync; skipping")
            return
        to_add = current - self._subscribed
        to_remove = self._subscribed - current
        for epic in to_remove:
            try:
                self._stream.unsubscribe_candles(epic)
            except Exception:  # noqa: BLE001
                logger.debug("unsubscribe_candles for %s failed", epic, exc_info=True)
            self._subscribed.discard(epic)
        for epic in to_add:
            try:
                self._stream.subscribe_candles(epic, self.on_candle)
            except Exception:  # noqa: BLE001
                logger.warning("subscribe_candles for %s failed", epic, exc_info=True)
                continue
            self._subscribed.add(epic)

    # -- callback (registered with the stream) -----------------------------

    def on_candle(self, candle: Any) -> None:
        """Persist one completed candle. Fail-soft — an archive failure
        is logged, not raised; an in-flight candle during a token rotation
        is dropped with a warning.

        A candle with ``complete=False`` is **ignored** — the LS server
        only sends ``CONS_END==1`` for finished minutes, and our
        ``_CandleListener`` already enforces this, but defense in depth:
        the recorder must never write a half-formed bar.
        """
        if not self._running:
            logger.debug(
                "LSBarRecorder.on_candle(%s @ %s) dropped: recorder not running",
                candle.epic, getattr(candle, "ts_utc", "?"),
            )
            return
        if not getattr(candle, "complete", True):
            # Defence in depth — _CandleListener already filters this.
            return
        from data_foundation.models import Bar
        from data_foundation.exceptions import ArchiveError

        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        bar = Bar(
            epic=candle.epic,
            resolution=self._resolution,
            ts_utc=getattr(candle, "ts_utc"),
            open=candle.open,
            high=candle.high,
            low=candle.low,
            close=candle.close,
            # LS doesn't carry volume in the CHART scheme we subscribe
            # to; recorders that need volume (e.g. for the divergence
            # sampler) read it from the yF archive instead.
            volume=None,
            source="ls",
            fetched_at=now_iso,
            tick_count=getattr(candle, "tick_count", None),
        )
        try:
            self._archive.insert_bars([bar])
            if self._health_sink is not None:
                self._health_sink({
                    "event": "ls_candle_written",
                    "epic": candle.epic,
                    "ts_utc": candle.ts_utc,
                    "tick_count": bar.tick_count,
                })
        except ArchiveError as exc:
            # An archive shape problem (e.g. source not in KNOWN_SOURCES,
            # which it is — but defend the contract): log, do not raise.
            logger.error("LSBarRecorder: archive rejected %s @ %s: %s",
                         candle.epic, candle.ts_utc, exc)
        except Exception:  # noqa: BLE001 — the recorder survives a DB hiccup
            logger.exception("LSBarRecorder: insert_bars failed for %s @ %s",
                             candle.epic, candle.ts_utc)


class TickAggregator:
    """L6 fallback — PRICE-ticks → 1-min OHLC bars (mid price).

    Used when IG's CHART subscription is unavailable on this account
    (Plan §6 B0 NO branch). The aggregator lives in the same process
    as the LS recorder, accumulating ticks per minute and emitting a
    ``ChartCandle``-shaped dict when the minute closes.

    Note: a candle with ``tick_count == 1`` is **not** a real OHLC. The
    archive is the same ``Bar`` table; only ``source='ls'`` (real CHART)
    and ``source='ls_tick_agg'`` (this fallback) carry the distinction.
    A future source-delta report (C3) flags ``tick_count < threshold``
    candles as "thin" — letting operators tell a real 1-tick bar from
    a recorder gap.
    """

    def __init__(self) -> None:
        self._current: _TickBuffer | None = None

    def on_tick(self, tick: Any) -> dict[str, Any] | None:
        """Fold one ``PriceTick`` into the current minute's buffer.

        Returns the candle-shaped dict for the minute that **just
        closed** when the new tick is in a different minute than the
        current buffer (None otherwise). The caller fills in ``epic`` —
        the aggregator doesn't know it; the recorder does.

        Bucket = the tick's timestamp truncated to the minute. The
        first tick of a new minute starts a new buffer; the previous
        one's candle is returned to the caller, who is expected to
        write it to the archive.

        The old minute-buffer pattern (``close_minute``) is preserved
        for tests and external callers that want explicit flushing.
        """
        ts = _parse_iso(getattr(tick, "timestamp", ""))
        if ts is None:
            return None
        minute_start = _iso_utc_minute(ts)
        mid = (tick.bid + tick.ask) / 2.0

        closed: dict[str, Any] | None = None
        if self._current is not None and self._current.minute_start_utc != minute_start:
            # Minute rollover: serialize the OLD buffer before it gets
            # overwritten by the new minute's first tick. Returning the
            # closed candle lets the recorder write it to the archive
            # without a separate explicit-close call.
            closed = self._serialize(self._current)

        if self._current is None or self._current.minute_start_utc != minute_start:
            self._current = _TickBuffer(
                minute_start_utc=minute_start,
                open=mid, high=mid, low=mid, close=mid, tick_count=1,
            )
        else:
            buf = self._current
            if mid > buf.high:
                buf.high = mid
            if mid < buf.low:
                buf.low = mid
            buf.close = mid
            buf.tick_count += 1

        return closed

    def close_minute(self, minute_start_utc: str) -> dict[str, Any] | None:
        """Return a candle-shaped dict for the named minute, or None if
        the current buffer is for a different minute (caller raced).

        Use this when you need to flush a minute on a timer rather than
        waiting for the next tick to roll over. ``TickAggregatorRecorder``
        uses ``on_tick``'s return value instead; this method stays for
        tests and external callers.
        """
        buf = self._current
        if buf is None or buf.minute_start_utc != minute_start_utc:
            return None
        if buf.tick_count == 0:
            return None
        return self._serialize(buf)

    def _serialize(self, buf: _TickBuffer) -> dict[str, Any]:
        """Render one buffer as a candle-shaped dict. ``epic`` is filled by the caller."""
        return {
            "epic": None,  # filled by caller (the recorder knows the epic)
            "ts_utc": buf.minute_start_utc,
            "open": buf.open,
            "high": buf.high,
            "low": buf.low,
            "close": buf.close,
            "tick_count": buf.tick_count,
            "complete": True,
        }


class TickAggregatorRecorder:
    """S1 L6-fallback — PRICE ticks → 1-min OHLC bars → archive.

    The CHART path (``LSBarRecorder``) is dormant on accounts where IG's
    ``CHART:{epic}:1MINUTE`` subscription returns ``-1 Incorrect
    instrument setup`` (Plan §6 B0 NO branch, verified 2026-08-19 on the
    DAX demo epic). This recorder is the production path in that case:
    subscribe to the already-live-verified ``PRICE:{epic}`` stream
    (Phase 1, since 2026-05-21), aggregate ticks in-process per minute,
    write to the archive with ``source='ls'`` and ``tick_count`` (per
    Plan §5.6 / §6 B2).

    A candle with ``tick_count == 1`` is **not** a real OHLC bar — it
    is one tick dressed up. The source-delta report (C3,
    ``scripts/source_delta.py``) flags such bars separately as "thin";
    the recorder emits them tagged (``thin`` flag in the health event)
    so an operator can tell a real 1-tick bar from a recorder gap.

    Same lifecycle contract as ``LSBarRecorder``: ``start()``,
    ``stop()``, ``restart()`` (token rotation), ``resync_epics()``.
    Fail-soft: a bad tick must not crash the recorder; a failing
    archive write must not break the next one. Threading follows the
    same convention as ``LSBarRecorder`` (Plan §11: SDK callback thread,
    ``BarArchive`` connection — see Session-10-block note for the
    explicit decision).
    """

    def __init__(
        self,
        stream: Any,
        archive: Any,
        epics_fn: EpicsFn,
        *,
        resolution: str = "1m",
        health_sink: HealthSink | None = None,
        thin_threshold: int = 2,
    ) -> None:
        self._stream = stream
        self._archive = archive
        self._epics_fn = epics_fn
        self._resolution = resolution
        self._health_sink = health_sink
        # Plan §6 B0 NO: "Ein LS-Bar mit ``tick_count <= 2`` gilt in
        # ``source_delta.py`` als „dünn" und wird getrennt ausgewiesen."
        # The recorder tags such bars in its health event; the
        # threshold is configurable for the proof-week calibration.
        self._thin_threshold = thin_threshold
        self._subscribed: set[str] = set()
        self._aggregators: dict[str, TickAggregator] = {}
        self._callbacks: dict[str, Callable[[Any], None]] = {}
        self._running = False

    # -- lifecycle ----------------------------------------------------------

    def start(self) -> None:
        """Start the underlying stream and subscribe to all measurable epics."""
        if self._running:
            return
        self._running = True
        self._stream.start()
        self._resync_epics()

    def stop(self) -> None:
        """Unsubscribe from all PRICE streams and stop the underlying stream."""
        if not self._running:
            return
        self._running = False
        for epic in list(self._subscribed):
            try:
                self._stream.unsubscribe(epic)
            except Exception:  # noqa: BLE001 — recorder must not crash the daemon
                logger.debug("unsubscribe for %s failed during stop", epic, exc_info=True)
        self._subscribed.clear()
        self._aggregators.clear()
        self._callbacks.clear()
        try:
            self._stream.stop()
        except Exception:  # noqa: BLE001
            logger.debug("stream.stop() raised", exc_info=True)

    def restart(self) -> None:
        """Token rotation hook (Plan §6 B3). Tear down and re-subscribe.

        New IG CST/XST = new auth header. A tick that was in-flight
        when the old token died is dropped with a warning — the next
        minute is from the new token, and the recorder is back online.
        """
        logger.info("TickAggregatorRecorder: restart (token rotation)")
        self.stop()
        self.start()

    def resync_epics(self) -> None:
        """Diff the universe against what we currently subscribe; add
        new, remove dropped. Called from ``universe_refresher`` after a
        SymbolResolver pass discovers fresh epics or quarantines some.
        """
        if not self._running:
            return
        self._resync_epics()

    # -- internals ----------------------------------------------------------

    def _resync_epics(self) -> None:
        try:
            current = set(self._epics_fn() or [])
        except Exception:  # noqa: BLE001 — never crash on a stale query
            logger.exception("TickAggregatorRecorder: epics_fn() raised during resync; skipping")
            return
        to_add = current - self._subscribed
        to_remove = self._subscribed - current
        for epic in to_remove:
            try:
                self._stream.unsubscribe(epic)
            except Exception:  # noqa: BLE001
                logger.debug("unsubscribe for %s failed", epic, exc_info=True)
            self._subscribed.discard(epic)
            self._callbacks.pop(epic, None)
            self._aggregators.pop(epic, None)
        for epic in to_add:
            cb = self._make_callback(epic)
            self._callbacks[epic] = cb
            self._aggregators[epic] = TickAggregator()
            try:
                self._stream.subscribe(epic, cb)
                self._subscribed.add(epic)
            except Exception:  # noqa: BLE001
                logger.warning("subscribe for %s failed", epic, exc_info=True)
                # Keep the aggregator/callback around so a later resync
                # can retry; the recorder is honest about the gap.

    def _make_callback(self, epic: str) -> Callable[[Any], None]:
        """Return a per-epic PRICE callback bound to this recorder."""
        def _cb(tick: Any) -> None:
            self.on_tick(epic, tick)
        return _cb

    # -- callback (registered with the stream) -----------------------------

    def on_tick(self, epic: str, tick: Any) -> None:
        """Fold a tick into the per-epic aggregator; on minute rollover,
        persist the closed candle. Fail-soft.
        """
        if not self._running:
            logger.debug(
                "TickAggregatorRecorder.on_tick(%s @ %s) dropped: recorder not running",
                epic, getattr(tick, "timestamp", "?"),
            )
            return
        agg = self._aggregators.get(epic)
        if agg is None:
            return
        closed = agg.on_tick(tick)
        if closed is None:
            # Same-minute tick: aggregate, no write yet.
            return
        # Roll-over: the previous minute's bucket is ready. Fill in the
        # epic (the aggregator doesn't know it) and persist.
        closed["epic"] = epic
        self._write_candle(epic, closed)

    def _write_candle(self, epic: str, candle: dict[str, Any]) -> None:
        from data_foundation.exceptions import ArchiveError
        from data_foundation.models import Bar

        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        tick_count = candle["tick_count"]
        bar = Bar(
            epic=epic,
            resolution=self._resolution,
            ts_utc=candle["ts_utc"],
            open=candle["open"],
            high=candle["high"],
            low=candle["low"],
            close=candle["close"],
            # PRICE ticks don't carry volume; recorders / divergence
            # samplers that need volume read it from the yF archive.
            volume=None,
            source="ls",
            fetched_at=now_iso,
            tick_count=tick_count,
        )
        try:
            self._archive.insert_bars([bar])
            if self._health_sink is not None:
                self._health_sink({
                    "event": "ls_tickagg_candle_written",
                    "epic": epic,
                    "ts_utc": candle["ts_utc"],
                    "tick_count": tick_count,
                    # Plan §6 B0 NO: thin bars are tagged so the
                    # source-delta report (C3) can separate them from
                    # "real" 1-tick bars that happen to look identical.
                    "thin": tick_count <= self._thin_threshold,
                })
        except ArchiveError as exc:
            # An archive shape problem (e.g. source not in KNOWN_SOURCES,
            # which it is — but defend the contract): log, do not raise.
            logger.error("TickAggregatorRecorder: archive rejected %s @ %s: %s",
                         epic, candle.get("ts_utc"), exc)
        except Exception:  # noqa: BLE001 — the recorder survives a DB hiccup
            logger.exception("TickAggregatorRecorder: insert_bars failed for %s @ %s",
                             epic, candle.get("ts_utc"))


def _parse_iso(ts: str) -> datetime | None:
    """Parse a TS-8601 UTC string. Returns None on garbage — fail-soft."""
    if not ts:
        return None
    try:
        normalized = ts.replace("Z", "+00:00") if ts.endswith("Z") else ts
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None
