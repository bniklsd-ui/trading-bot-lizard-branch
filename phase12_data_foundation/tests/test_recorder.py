"""Tests for ``data_foundation.recorder`` (Plan §6 Step 5). No network."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from data_foundation.archive import BarArchive
from data_foundation.recorder import Recorder, RecorderReport

EPIC_A = "IX.D.DAX.IFMM.IP"
EPIC_B = "IX.D.CAC.IFE.IP"
NOW = datetime(2026, 8, 16, 10, 0, 0, tzinfo=timezone.utc)


def _bar(ts: str, close: float = 100.0):
    return SimpleNamespace(ts=ts, open=close, high=close, low=close, close=close, volume=1.0)


@pytest.fixture
def archive(tmp_path) -> BarArchive:
    a = BarArchive(tmp_path / "bars.sqlite")
    a.ensure_schema()
    yield a
    a.close()


def _recorder(archive, *, state_path, get_bars=None, epics=(EPIC_A,), market_open=True,
              health_sink=None, sleep_fn=None):
    calls: list[str] = []

    def default_get_bars(epic, *, resolution, count):
        calls.append(epic)
        return [_bar("2026-08-16T09:55:00.000Z")]

    rec = Recorder(
        archive,
        get_bars or default_get_bars,
        lambda: list(epics),
        state_path=str(state_path),
        health_sink=health_sink,
        market_open_fn=lambda: market_open,
        now_fn=lambda: NOW,
        sleep_fn=sleep_fn or (lambda s: None),
    )
    return rec, calls


def test_tick_writes_only_for_epics_fn_epics(archive, tmp_path):
    rec, calls = _recorder(archive, epics=(EPIC_A, EPIC_B), state_path=tmp_path / "s.json")
    rec.tick()
    assert set(calls) == {EPIC_A, EPIC_B}
    window = archive.window(EPIC_A, "1m", "2026-08-16T00:00:00.000Z", "2026-08-17T00:00:00.000Z")
    assert len(window) == 1


def test_off_hours_is_a_no_op_no_fetch(archive, tmp_path):
    def get_bars(*a, **kw):
        raise AssertionError("must not fetch off-hours")

    rec, _ = _recorder(archive, get_bars=get_bars, market_open=False, state_path=tmp_path / "s.json")
    report = rec.tick()
    assert report.skipped_off_hours is True
    assert report.bars_written == 0


def test_overlap_dedup_across_two_ticks(archive, tmp_path):
    rec, _ = _recorder(archive, state_path=tmp_path / "s.json")
    r1 = rec.tick()
    r2 = rec.tick()
    assert r1.bars_written == 1
    assert r2.bars_written == 0  # same bar re-fetched, PK dedup
    window = archive.window(EPIC_A, "1m", "2026-08-16T00:00:00.000Z", "2026-08-17T00:00:00.000Z")
    assert len(window) == 1


def test_one_epic_error_does_not_stop_the_tick(archive, tmp_path):
    def get_bars(epic, *, resolution, count):
        if epic == EPIC_A:
            raise RuntimeError("boom")
        return [_bar("2026-08-16T09:55:00.000Z")]

    rec, _ = _recorder(archive, get_bars=get_bars, epics=(EPIC_A, EPIC_B), state_path=tmp_path / "s.json")
    report = rec.tick()
    assert report.bars_written == 1
    assert len(report.errors) == 1
    assert EPIC_A in report.errors[0]


def test_heartbeat_state_written_atomically(archive, tmp_path):
    state_path = tmp_path / "recorder_state.json"
    rec, _ = _recorder(archive, state_path=state_path)
    rec.tick()
    assert state_path.exists()
    assert not state_path.with_suffix(".json.tmp").exists()
    payload = json.loads(state_path.read_text())
    assert payload["epics"] == 1
    assert payload["bars_written"] == 1
    assert payload["skipped_off_hours"] is False


def test_request_stop_ends_run_forever(archive, tmp_path):
    ticks = []

    def get_bars(epic, *, resolution, count):
        ticks.append(epic)
        return [_bar("2026-08-16T09:55:00.000Z")]

    rec, _ = _recorder(archive, get_bars=get_bars, state_path=tmp_path / "s.json")

    def sleep_and_stop(seconds):
        rec.request_stop()

    rec._sleep_fn = sleep_and_stop
    rec.run_forever()
    assert len(ticks) == 1  # one tick, then stop requested during the sleep, loop exits


def test_report_numbers_are_correct(archive, tmp_path):
    rec, _ = _recorder(archive, epics=(EPIC_A, EPIC_B), state_path=tmp_path / "s.json")
    report = rec.tick()
    assert isinstance(report, RecorderReport)
    assert report.epics == 2
    assert report.bars_written == 2
    assert report.errors == []


def test_recorder_heartbeat_event_emitted(archive, tmp_path):
    events = []
    rec, _ = _recorder(archive, state_path=tmp_path / "s.json", health_sink=events.append)
    rec.tick()
    assert any(e.get("event") == "recorder_heartbeat" for e in events)
    ev = next(e for e in events if e["event"] == "recorder_heartbeat")
    assert ev["epics"] == 1
    assert ev["bars_written"] == 1


def test_health_sink_failure_never_breaks_tick(archive, tmp_path):
    def bad_sink(event):
        raise RuntimeError("sink boom")

    rec, _ = _recorder(archive, state_path=tmp_path / "s.json", health_sink=bad_sink)
    report = rec.tick()  # must not raise
    assert report.bars_written == 1
