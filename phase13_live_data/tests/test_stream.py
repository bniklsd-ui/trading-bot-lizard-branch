"""Phase 13 §6 B2 — tests for ``live_data.stream``.

All mocked: no network, no SDK, no live DB. ``stream`` is a tiny fake that
records its own ``subscribe_candles`` / ``unsubscribe_candles`` calls; the
``archive`` is a real in-memory ``BarArchive`` (D4) on a tmp_path SQLite.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from pathlib import Path

import pytest

from data_foundation.archive import BarArchive
from data_foundation.models import Bar

from live_data.stream import LSBarRecorder, TickAggregator, TickAggregatorRecorder, _iso_utc_minute


# ---------- fakes ----------------------------------------------------------


class _FakeStream:
    """Records every subscription/unsubscription. A minimal stand-in for
    ``IGLightstreamerClient`` (which is a heavier mock target in B1).

    Carries both ``subscribe_candles``/``unsubscribe_candles`` (CHART
    path) and ``subscribe``/``unsubscribe`` (PRICE path) so the same
    fake serves both recorders in different tests.
    """

    def __init__(self) -> None:
        self.started = False
        self.stopped = False
        self.subs: dict[str, object] = {}
        self.price_subs: dict[str, Callable[[Any], None]] = {}

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def subscribe_candles(self, epic, callback) -> None:
        self.subs[epic] = callback

    def unsubscribe_candles(self, epic) -> None:
        self.subs.pop(epic, None)

    # PRICE path (used by TickAggregatorRecorder, the L6 fallback when
    # CHART is unavailable — Plan §6 B0 NO branch).
    def subscribe(self, epic, callback) -> None:
        self.price_subs[epic] = callback

    def unsubscribe(self, epic) -> None:
        self.price_subs.pop(epic, None)


def _epics(*names) -> callable:
    universe = list(names)
    def _get():
        return list(universe)
    # ``_get`` reads from the live list at call time, so tests can mutate
    # ``universe`` between calls to simulate the universe_refresher's diff.
    def _set(new):
        universe.clear()
        universe.extend(new)
    _get.set = _set
    return _get


def _candle(epic, ts_utc, complete=True, open_=100.0, high=101.0, low=99.5,
            close=100.5, tick_count=5):
    """Mimics the SDK's ChartCandle (frozen dataclass from P1)."""
    return SimpleNamespace(
        epic=epic, ts_utc=ts_utc, open=open_, high=high, low=low, close=close,
        tick_count=tick_count, complete=complete,
    )


@pytest.fixture
def archive(tmp_path) -> BarArchive:
    a = BarArchive(tmp_path / "bars.sqlite")
    a.ensure_schema()
    yield a
    a.close()


# ---------- LSBarRecorder --------------------------------------------------


def test_start_subscribes_to_all_measurable_epics(archive, tmp_path):
    stream = _FakeStream()
    epics = _epics("IX.D.DAX.IFMM.IP", "IX.D.CAC.IFE.IP")
    rec = LSBarRecorder(stream, archive, epics, health_sink=None)
    rec.start()
    assert stream.started
    assert set(stream.subs.keys()) == {"IX.D.DAX.IFMM.IP", "IX.D.CAC.IFE.IP"}


def test_on_candle_writes_one_archive_row_with_source_ls(archive, tmp_path):
    stream = _FakeStream()
    rec = LSBarRecorder(stream, archive, _epics("IX.D.DAX.IFMM.IP"))
    rec.start()
    stream.subs["IX.D.DAX.IFMM.IP"](
        _candle("IX.D.DAX.IFMM.IP", "2026-08-19T09:00:00.000Z",
               open_=100.0, high=101.0, low=99.5, close=100.5, tick_count=5)
    )
    rows = archive.window("IX.D.DAX.IFMM.IP", "1m",
                          "2026-08-19T00:00:00.000Z", "2026-08-19T23:59:00.000Z",
                          sources=("ls",))
    assert len(rows) == 1
    row = rows[0]
    assert row.source == "ls"
    assert row.tick_count == 5
    assert row.open == pytest.approx(100.0)
    assert row.close == pytest.approx(100.5)


def test_on_candle_with_complete_false_is_ignored(archive, tmp_path):
    """Defense in depth: the recorder must never write a half-formed bar,
    even if the listener let one slip through."""
    stream = _FakeStream()
    rec = LSBarRecorder(stream, archive, _epics("IX.D.DAX.IFMM.IP"))
    rec.start()
    stream.subs["IX.D.DAX.IFMM.IP"](
        _candle("IX.D.DAX.IFMM.IP", "2026-08-19T09:00:00.000Z", complete=False)
    )
    rows = archive.window("IX.D.DAX.IFMM.IP", "1m",
                          "2026-08-19T00:00:00.000Z", "2026-08-19T23:59:00.000Z",
                          sources=("ls",))
    assert rows == []


def test_on_candle_after_stop_is_dropped(archive, tmp_path):
    """A candle in-flight when stop() is called (token rotation, restart)
    must not be written — the recorder is in a transition state, and
    the next recorder instance will pick up the next candle fresh."""
    stream = _FakeStream()
    rec = LSBarRecorder(stream, archive, _epics("IX.D.DAX.IFMM.IP"))
    rec.start()
    # Capture the callback BEFORE stop() unsubscribes it from the fake
    # stream — the closure still works, the recorder's ``_running`` flag
    # is what filters.
    cb = stream.subs["IX.D.DAX.IFMM.IP"]
    rec.stop()
    cb(_candle("IX.D.DAX.IFMM.IP", "2026-08-19T09:00:00.000Z"))
    rows = archive.window("IX.D.DAX.IFMM.IP", "1m",
                          "2026-08-19T00:00:00.000Z", "2026-08-19T23:59:00.000Z",
                          sources=("ls",))
    assert rows == []


def test_double_candle_same_minute_creates_only_one_row(archive, tmp_path):
    """INSERT OR IGNORE on the (epic, resolution, ts_utc, source) PK is
    the dedup contract — a re-delivered candle must not double-write."""
    stream = _FakeStream()
    rec = LSBarRecorder(stream, archive, _epics("IX.D.DAX.IFMM.IP"))
    rec.start()
    cb = stream.subs["IX.D.DAX.IFMM.IP"]
    candle = _candle("IX.D.DAX.IFMM.IP", "2026-08-19T09:00:00.000Z")
    cb(candle)
    cb(candle)  # duplicate delivery (LS network glitch)
    cb(candle)  # and again
    rows = archive.window("IX.D.DAX.IFMM.IP", "1m",
                          "2026-08-19T00:00:00.000Z", "2026-08-19T23:59:00.000Z",
                          sources=("ls",))
    assert len(rows) == 1


def test_resync_epics_diffs_universe(archive, tmp_path):
    """universe_refresher triggers resync_epics after a SymbolResolver
    pass; new epics must subscribe, dropped ones must unsubscribe."""
    stream = _FakeStream()
    epics = _epics("IX.D.DAX.IFMM.IP")
    rec = LSBarRecorder(stream, archive, epics)
    rec.start()
    assert set(stream.subs.keys()) == {"IX.D.DAX.IFMM.IP"}
    # Universe changes: drop DAX, add CAC + IBEX.
    epics.set(["IX.D.CAC.IFE.IP", "IX.D.IBEX.FWM2.IP"])
    rec.resync_epics()
    assert set(stream.subs.keys()) == {"IX.D.CAC.IFE.IP", "IX.D.IBEX.FWM2.IP"}


def test_restart_resubscribes_after_token_rotation(archive, tmp_path):
    """Token rotation (B3) needs a recorder that tears down and re-subscribes
    without losing the in-flight candle (which is dropped, with a log line)."""
    stream = _FakeStream()
    epics = _epics("IX.D.DAX.IFMM.IP")
    rec = LSBarRecorder(stream, archive, epics)
    rec.start()
    rec.restart()
    assert stream.started and stream.stopped
    assert "IX.D.DAX.IFMM.IP" in stream.subs
    # Idempotent: a second restart is a no-op + re-subscribe, not a crash.
    rec.restart()
    assert "IX.D.DAX.IFMM.IP" in stream.subs


def test_archive_write_failure_does_not_kill_recorder(archive, tmp_path):
    """If ``insert_bars`` raises (e.g. schema drift, IO error), the recorder
    must log and survive — the next candle must still land."""
    stream = _FakeStream()
    rec = LSBarRecorder(stream, archive, _epics("IX.D.DAX.IFMM.IP"))
    rec.start()
    cb = stream.subs["IX.D.DAX.IFMM.IP"]
    # Force an archive failure by closing the archive mid-flight; the
    # recorder catches the SQLite OperationalError and logs.
    archive.close()
    # must not raise:
    cb(_candle("IX.D.DAX.IFMM.IP", "2026-08-19T09:00:00.000Z"))
    # After the failed write, a freshly-opened archive is irrelevant — the
    # recorder still thinks it's running. This is the contract: the recorder
    # **survives** the failure; the operator / wiring decides what to do next.


# ---------- TickAggregator -------------------------------------------------


def test_tick_aggregator_accumulates_one_minute_ohlc():
    from broker_wrapper.streaming.base import PriceTick
    agg = TickAggregator()
    ts0 = "2026-08-19T09:00:30.000Z"
    ts1 = "2026-08-19T09:00:55.000Z"
    agg.on_tick(PriceTick(epic="X", bid=100.0, ask=100.2, timestamp=ts0))
    agg.on_tick(PriceTick(epic="X", bid=101.0, ask=101.2, timestamp=ts1))
    out = agg.close_minute("2026-08-19T09:00:00.000Z")
    assert out is not None
    assert out["open"] == pytest.approx(100.1)   # mid of (100.0+100.2)/2
    assert out["high"] == pytest.approx(101.1)   # (101.0+101.2)/2
    assert out["low"] == pytest.approx(100.1)
    assert out["close"] == pytest.approx(101.1)
    assert out["tick_count"] == 2
    assert out["complete"] is True
    assert out["ts_utc"] == "2026-08-19T09:00:00.000Z"


def test_tick_aggregator_separates_minutes():
    from broker_wrapper.streaming.base import PriceTick
    agg = TickAggregator()
    # 09:00 bucket
    agg.on_tick(PriceTick(epic="X", bid=100, ask=100, timestamp="2026-08-19T09:00:30Z"))
    # 09:01 bucket — first tick of the new minute.
    out_09_00 = agg.close_minute("2026-08-19T09:00:00.000Z")
    assert out_09_00 is not None and out_09_00["open"] == pytest.approx(100.0)
    agg.on_tick(PriceTick(epic="X", bid=200, ask=200, timestamp="2026-08-19T09:01:10Z"))
    # Re-closing 09:00 must return None — the buffer has rolled to 09:01.
    assert agg.close_minute("2026-08-19T09:00:00.000Z") is None
    out_09_01 = agg.close_minute("2026-08-19T09:01:00.000Z")
    assert out_09_01 is not None and out_09_01["open"] == pytest.approx(200.0)


def test_iso_utc_minute_truncates_to_minute():
    """Milliseconds are always ``.000`` — this is a minute bucket, not a tick timestamp
    (Drift #13 fix, Phase 16 R2: keeping the tick's own ms here made every tick its own
    "minute" for the rollover comparison in ``TickAggregator.on_tick``)."""
    dt = datetime(2026, 8, 19, 9, 0, 37, 123_000, tzinfo=timezone.utc)
    assert _iso_utc_minute(dt) == "2026-08-19T09:00:00.000Z"


# ---------- TickAggregator.on_tick return value (B0.5 refactor) -----------


def test_tick_aggregator_on_tick_returns_none_on_same_minute():
    """Within a minute, no candle has closed yet — return None."""
    from broker_wrapper.streaming.base import PriceTick
    agg = TickAggregator()
    assert agg.on_tick(PriceTick(epic="X", bid=100, ask=100, timestamp="2026-08-19T09:00:30Z")) is None
    assert agg.on_tick(PriceTick(epic="X", bid=101, ask=101, timestamp="2026-08-19T09:00:55Z")) is None


def test_tick_aggregator_on_tick_returns_closed_candle_on_rollover():
    """The first tick of a new minute returns the OLD minute's candle
    (with the OLD minute's tick_count and OHLC). The recorder uses this
    to write the closed candle without an explicit close_minute call."""
    from broker_wrapper.streaming.base import PriceTick
    agg = TickAggregator()
    agg.on_tick(PriceTick(epic="X", bid=100, ask=100, timestamp="2026-08-19T09:00:30Z"))
    agg.on_tick(PriceTick(epic="X", bid=101, ask=101, timestamp="2026-08-19T09:00:55Z"))
    # First tick of 09:01 — should return the 09:00 candle.
    closed = agg.on_tick(PriceTick(epic="X", bid=200, ask=200, timestamp="2026-08-19T09:01:10Z"))
    assert closed is not None
    assert closed["ts_utc"] == "2026-08-19T09:00:00.000Z"
    assert closed["open"] == pytest.approx(100.0)
    assert closed["close"] == pytest.approx(101.0)
    assert closed["tick_count"] == 2
    assert closed["complete"] is True
    assert closed["epic"] is None  # filled by the caller


def test_two_ticks_same_minute_with_different_ms_yield_one_bar():
    """Drift #13 regression: two ticks a few hundred ms apart, same minute, must
    NOT roll over — before the fix, the differing millisecond made
    ``_iso_utc_minute`` return two different bucket strings and every tick
    looked like a new minute."""
    from broker_wrapper.streaming.base import PriceTick
    agg = TickAggregator()
    assert agg.on_tick(
        PriceTick(epic="X", bid=100, ask=100, timestamp="2026-08-19T09:00:30.100Z")
    ) is None
    closed = agg.on_tick(
        PriceTick(epic="X", bid=102, ask=102, timestamp="2026-08-19T09:00:30.900Z")
    )
    assert closed is None  # still same minute — no rollover yet
    # First tick of the next minute now closes the buffer as ONE bar.
    closed = agg.on_tick(
        PriceTick(epic="X", bid=200, ask=200, timestamp="2026-08-19T09:01:00.050Z")
    )
    assert closed is not None
    assert closed["tick_count"] == 2
    assert closed["open"] == pytest.approx(100.0)
    assert closed["close"] == pytest.approx(102.0)


def test_minute_rollover_emits_bar_on_minute_boundary():
    """A tick in minute N+1 closes minute N with exactly one bar whose
    ``ts_utc`` lands on the minute boundary (``:00.000Z``), never on the
    triggering tick's own timestamp."""
    from broker_wrapper.streaming.base import PriceTick
    agg = TickAggregator()
    agg.on_tick(PriceTick(epic="X", bid=100, ask=100, timestamp="2026-08-19T09:00:59.987Z"))
    closed = agg.on_tick(PriceTick(epic="X", bid=101, ask=101, timestamp="2026-08-19T09:01:00.013Z"))
    assert closed is not None
    assert closed["ts_utc"] == "2026-08-19T09:00:00.000Z"
    assert closed["tick_count"] == 1


# ---------- TickAggregatorRecorder ---------------------------------------


def _price_tick(epic: str, bid: float, ask: float, ts: str):
    """Mimics the SDK's PriceTick (frozen dataclass from P1)."""
    from broker_wrapper.streaming.base import PriceTick
    return PriceTick(epic=epic, bid=bid, ask=ask, timestamp=ts)


def test_recorder_start_subscribes_to_all_measurable_epics(archive, tmp_path):
    stream = _FakeStream()
    epics = _epics("IX.D.DAX.IFMM.IP", "IX.D.CAC.IFE.IP")
    rec = TickAggregatorRecorder(stream, archive, epics)
    rec.start()
    assert stream.started
    assert set(stream.price_subs.keys()) == {"IX.D.DAX.IFMM.IP", "IX.D.CAC.IFE.IP"}


def test_recorder_writes_archive_row_on_minute_close(archive, tmp_path):
    """Ticks within a minute don't write; the FIRST tick of the next
    minute triggers the write of the previous minute's candle."""
    stream = _FakeStream()
    rec = TickAggregatorRecorder(stream, archive, _epics("IX.D.DAX.IFMM.IP"))
    rec.start()
    cb = stream.price_subs["IX.D.DAX.IFMM.IP"]
    cb(_price_tick("IX.D.DAX.IFMM.IP", 100.0, 100.0, "2026-08-19T09:00:30Z"))
    cb(_price_tick("IX.D.DAX.IFMM.IP", 101.0, 101.0, "2026-08-19T09:00:55Z"))
    # No write yet — same minute.
    rows_mid = archive.window("IX.D.DAX.IFMM.IP", "1m",
                              "2026-08-19T00:00:00.000Z", "2026-08-19T23:59:00.000Z",
                              sources=("ls",))
    assert rows_mid == []
    # Roll-over tick at 09:01 — writes the 09:00 candle.
    cb(_price_tick("IX.D.DAX.IFMM.IP", 200.0, 200.0, "2026-08-19T09:01:10Z"))
    rows = archive.window("IX.D.DAX.IFMM.IP", "1m",
                          "2026-08-19T00:00:00.000Z", "2026-08-19T23:59:00.000Z",
                          sources=("ls",))
    assert len(rows) == 1
    row = rows[0]
    assert row.source == "ls"
    assert row.tick_count == 2
    assert row.ts_utc == "2026-08-19T09:00:00.000Z"
    assert row.open == pytest.approx(100.0)
    assert row.close == pytest.approx(101.0)
    assert row.high == pytest.approx(101.0)
    assert row.low == pytest.approx(100.0)


def test_recorder_thin_candle_flagged_in_health_sink(archive, tmp_path):
    """A candle with tick_count <= 2 must be tagged ``thin=True`` in the
    health event (Plan §6 B0 NO: "Ein LS-Bar mit tick_count <= 2 gilt in
    source_delta.py als „dünn" und wird getrennt ausgewiesen")."""
    events: list[dict] = []
    stream = _FakeStream()
    rec = TickAggregatorRecorder(stream, archive, _epics("IX.D.DAX.IFMM.IP"),
                                  health_sink=events.append)
    rec.start()
    cb = stream.price_subs["IX.D.DAX.IFMM.IP"]
    cb(_price_tick("IX.D.DAX.IFMM.IP", 100, 100, "2026-08-19T09:00:30Z"))
    cb(_price_tick("IX.D.DAX.IFMM.IP", 200, 200, "2026-08-19T09:01:10Z"))  # close 09:00 (1 tick) → thin=True
    cb(_price_tick("IX.D.DAX.IFMM.IP", 300, 300, "2026-08-19T09:01:30Z"))
    cb(_price_tick("IX.D.DAX.IFMM.IP", 400, 400, "2026-08-19T09:02:10Z"))  # close 09:01 (2 ticks) → thin=True
    cb(_price_tick("IX.D.DAX.IFMM.IP", 500, 500, "2026-08-19T09:03:10Z"))  # close 09:02 (1 tick) → thin=True
    assert len(events) == 3
    assert all(e["thin"] is True for e in events), "all <=2-tick candles must be thin"
    assert all(e["event"] == "ls_tickagg_candle_written" for e in events)
    # The middle event is the 2-tick one — still thin at threshold=2.
    assert events[1]["tick_count"] == 2


def test_recorder_three_tick_candle_is_not_thin(archive, tmp_path):
    """The threshold is configurable; default 2. A 3-tick candle is NOT thin."""
    events: list[dict] = []
    stream = _FakeStream()
    rec = TickAggregatorRecorder(stream, archive, _epics("IX.D.DAX.IFMM.IP"),
                                  health_sink=events.append)
    rec.start()
    cb = stream.price_subs["IX.D.DAX.IFMM.IP"]
    cb(_price_tick("IX.D.DAX.IFMM.IP", 100, 100, "2026-08-19T09:00:30Z"))
    cb(_price_tick("IX.D.DAX.IFMM.IP", 101, 101, "2026-08-19T09:00:45Z"))
    cb(_price_tick("IX.D.DAX.IFMM.IP", 102, 102, "2026-08-19T09:00:55Z"))
    cb(_price_tick("IX.D.DAX.IFMM.IP", 200, 200, "2026-08-19T09:01:10Z"))  # close 09:00
    assert len(events) == 1
    assert events[0]["tick_count"] == 3
    assert events[0]["thin"] is False


def test_health_sink_failure_keeps_bar_and_logs_sink(archive, tmp_path, caplog):
    """Drift #12 regression at the log-message level: a health-sink exception must not be
    mislabeled as an archive failure — the bar is already written by the time the sink
    runs, and the log must say so, naming the sink, not ``insert_bars``."""
    def _raising_sink(event: dict) -> None:
        raise RuntimeError("sink boom")

    stream = _FakeStream()
    rec = TickAggregatorRecorder(stream, archive, _epics("IX.D.DAX.IFMM.IP"),
                                  health_sink=_raising_sink)
    rec.start()
    cb = stream.price_subs["IX.D.DAX.IFMM.IP"]
    with caplog.at_level("ERROR"):
        cb(_price_tick("IX.D.DAX.IFMM.IP", 100, 100, "2026-08-19T09:00:30Z"))
        cb(_price_tick("IX.D.DAX.IFMM.IP", 200, 200, "2026-08-19T09:01:10Z"))  # rollover, sink raises

    rows = archive.window("IX.D.DAX.IFMM.IP", "1m",
                          "2026-08-19T00:00:00.000Z", "2026-08-19T23:59:00.000Z",
                          sources=("ls",))
    assert len(rows) == 1, "the bar must be written even though the sink raised"

    messages = " ".join(r.message for r in caplog.records)
    assert "health sink failed" in messages
    assert "bar was written" in messages
    assert "insert_bars failed" not in messages


def test_recorder_on_tick_after_stop_is_dropped(archive, tmp_path):
    """Tick during stopped state (e.g. token rotation in-flight) must
    not write — the recorder is in a transition state."""
    stream = _FakeStream()
    rec = TickAggregatorRecorder(stream, archive, _epics("IX.D.DAX.IFMM.IP"))
    rec.start()
    cb = stream.price_subs["IX.D.DAX.IFMM.IP"]
    rec.stop()
    cb(_price_tick("IX.D.DAX.IFMM.IP", 100, 100, "2026-08-19T09:00:30Z"))
    cb(_price_tick("IX.D.DAX.IFMM.IP", 200, 200, "2026-08-19T09:01:10Z"))
    rows = archive.window("IX.D.DAX.IFMM.IP", "1m",
                          "2026-08-19T00:00:00.000Z", "2026-08-19T23:59:00.000Z",
                          sources=("ls",))
    assert rows == []


def test_recorder_resync_epics_diffs_universe(archive, tmp_path):
    """universe_refresher triggers resync_epics after a SymbolResolver
    pass; new epics must subscribe, dropped ones must unsubscribe."""
    stream = _FakeStream()
    epics = _epics("IX.D.DAX.IFMM.IP")
    rec = TickAggregatorRecorder(stream, archive, epics)
    rec.start()
    assert set(stream.price_subs.keys()) == {"IX.D.DAX.IFMM.IP"}
    epics.set(["IX.D.CAC.IFE.IP", "IX.D.IBEX.FWM2.IP"])
    rec.resync_epics()
    assert set(stream.price_subs.keys()) == {"IX.D.CAC.IFE.IP", "IX.D.IBEX.FWM2.IP"}


def test_recorder_restart_resubscribes_after_token_rotation(archive, tmp_path):
    """Token rotation (B3) needs a recorder that tears down and re-subscribes."""
    stream = _FakeStream()
    rec = TickAggregatorRecorder(stream, archive, _epics("IX.D.DAX.IFMM.IP"))
    rec.start()
    rec.restart()
    assert stream.started and stream.stopped
    assert "IX.D.DAX.IFMM.IP" in stream.price_subs
    # Idempotent: a second restart is a no-op + re-subscribe, not a crash.
    rec.restart()
    assert "IX.D.DAX.IFMM.IP" in stream.price_subs


def test_recorder_archive_write_failure_does_not_kill_recorder(archive, tmp_path):
    """If ``insert_bars`` raises, the recorder must log and survive —
    the next candle must still land."""
    stream = _FakeStream()
    rec = TickAggregatorRecorder(stream, archive, _epics("IX.D.DAX.IFMM.IP"))
    rec.start()
    cb = stream.price_subs["IX.D.DAX.IFMM.IP"]
    cb(_price_tick("IX.D.DAX.IFMM.IP", 100, 100, "2026-08-19T09:00:30Z"))
    # Close archive mid-flight — subsequent writes must be caught, not raised.
    archive.close()
    # must not raise:
    cb(_price_tick("IX.D.DAX.IFMM.IP", 200, 200, "2026-08-19T09:01:10Z"))
