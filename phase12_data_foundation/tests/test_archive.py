"""Tests for ``data_foundation.archive.BarArchive`` (Plan §6 Step 1)."""

from __future__ import annotations

import pytest

from data_foundation.archive import BarArchive
from data_foundation.exceptions import ArchiveError
from data_foundation.models import (
    SOURCE_IG,
    SOURCE_YF,
    Bar,
    normalize_bar_ts,
)


def _bar(epic="IX.D.DAX.IFMM.IP", resolution="1m", ts="2026-08-11T09:00:00.000Z",
         source=SOURCE_YF, close=100.0) -> Bar:
    return Bar(
        epic=epic, resolution=resolution, ts_utc=ts,
        open=close, high=close, low=close, close=close, volume=10.0,
        source=source, fetched_at="2026-08-11T09:00:01.000Z",
    )


@pytest.fixture
def archive(tmp_path):
    a = BarArchive(tmp_path / "bars.sqlite")
    a.ensure_schema()
    yield a
    a.close()


def test_ensure_schema_idempotent(archive):
    archive.ensure_schema()
    archive.ensure_schema()  # second call must not raise


def test_insert_dedup_identical_bar(archive):
    bar = _bar()
    assert archive.insert_bars([bar]) == 1
    assert archive.insert_bars([bar]) == 0  # identical PK -> INSERT OR IGNORE, no-op


def test_insert_rejects_unknown_source(archive):
    bad = _bar(source="bloomberg")
    with pytest.raises(ArchiveError):
        archive.insert_bars([bad])


def test_insert_batch_with_bad_source_is_atomic(archive):
    """A bad source anywhere in the batch must reject the whole call -- no
    partial write left behind for a later insert_bars() call to accidentally
    commit alongside itself."""
    good = _bar(ts="2026-08-11T09:00:00.000Z")
    bad = _bar(ts="2026-08-11T09:01:00.000Z", source="bloomberg")
    with pytest.raises(ArchiveError):
        archive.insert_bars([good, bad])
    result = archive.window(
        "IX.D.DAX.IFMM.IP", "1m", "2026-08-11T00:00:00.000Z", "2026-08-12T00:00:00.000Z"
    )
    assert result == []  # the good bar was NOT partially committed


def test_window_bounds_inclusive_exclusive(archive):
    archive.insert_bars([
        _bar(ts="2026-08-11T09:00:00.000Z"),
        _bar(ts="2026-08-11T09:01:00.000Z"),
        _bar(ts="2026-08-11T09:02:00.000Z"),
    ])
    result = archive.window(
        "IX.D.DAX.IFMM.IP", "1m", "2026-08-11T09:00:00.000Z", "2026-08-11T09:02:00.000Z"
    )
    ts_list = [b.ts_utc for b in result]
    assert "2026-08-11T09:00:00.000Z" in ts_list  # start inclusive
    assert "2026-08-11T09:01:00.000Z" in ts_list
    assert "2026-08-11T09:02:00.000Z" not in ts_list  # end exclusive


def test_window_source_preference(archive):
    archive.insert_bars([
        _bar(ts="2026-08-11T09:00:00.000Z", source=SOURCE_YF, close=100.0),
        _bar(ts="2026-08-11T09:00:00.000Z", source=SOURCE_IG, close=101.0),
    ])
    result = archive.window(
        "IX.D.DAX.IFMM.IP", "1m", "2026-08-11T08:00:00.000Z", "2026-08-11T10:00:00.000Z"
    )
    assert len(result) == 1
    assert result[0].source == SOURCE_IG  # ig ranks before yf in the default prefer tuple
    assert result[0].close == 101.0


def test_coverage_ratio_zero_partial_full(archive):
    # zero: no bars at all
    assert archive.coverage_ratio(
        "IX.D.DAX.IFMM.IP", "1m", "2026-08-11T09:00:00.000Z", "2026-08-11T09:10:00.000Z"
    ) == 0.0

    # partial: 5 of 10 expected minutes present
    archive.insert_bars([
        _bar(ts=f"2026-08-11T09:0{i}:00.000Z") for i in range(5)
    ])
    ratio = archive.coverage_ratio(
        "IX.D.DAX.IFMM.IP", "1m", "2026-08-11T09:00:00.000Z", "2026-08-11T09:10:00.000Z"
    )
    assert ratio == pytest.approx(0.5)

    # full: all 10 expected minutes present (5 more inserted)
    archive.insert_bars([
        _bar(ts=f"2026-08-11T09:0{i}:00.000Z") for i in range(5, 10)
    ])
    ratio = archive.coverage_ratio(
        "IX.D.DAX.IFMM.IP", "1m", "2026-08-11T09:00:00.000Z", "2026-08-11T09:10:00.000Z"
    )
    assert ratio == pytest.approx(1.0)


def test_latest_ts_empty_then_set(archive):
    assert archive.latest_ts("IX.D.DAX.IFMM.IP", "1m") is None
    archive.insert_bars([_bar(ts="2026-08-11T09:05:00.000Z")])
    archive.insert_bars([_bar(ts="2026-08-11T09:01:00.000Z")])
    assert archive.latest_ts("IX.D.DAX.IFMM.IP", "1m") == "2026-08-11T09:05:00.000Z"


def test_bars_written_since(archive):
    assert archive.bars_written_since("2026-08-11T00:00:00.000Z") == 0
    archive.insert_bars([_bar()])
    assert archive.bars_written_since("2026-08-11T00:00:00.000Z") == 1
    assert archive.bars_written_since("2026-08-12T00:00:00.000Z") == 0


def test_bars_written_since_respects_end_bound(archive):
    """Without an upper bound, a query for a PAST day would count everything fetched
    from that day's start until now — silently reporting a dead day as healthy (the
    exact bug this param exists to close, Plan §6 Step 6)."""
    archive.insert_bars([Bar(
        epic="IX.D.DAX.IFMM.IP", resolution="1m", ts_utc="2026-08-11T09:00:00.000Z",
        open=100, high=100, low=100, close=100, volume=1, source=SOURCE_YF,
        fetched_at="2026-08-11T09:00:01.000Z",
    )])
    archive.insert_bars([Bar(
        epic="IX.D.DAX.IFMM.IP", resolution="1m", ts_utc="2026-08-12T09:00:00.000Z",
        open=100, high=100, low=100, close=100, volume=1, source=SOURCE_YF,
        fetched_at="2026-08-12T09:00:01.000Z",
    )])
    # open-ended (no end_utc): both bars count, matches the original contract
    assert archive.bars_written_since("2026-08-11T00:00:00.000Z") == 2
    # bounded to just the 11th: only that day's bar counts
    assert archive.bars_written_since(
        "2026-08-11T00:00:00.000Z", "2026-08-12T00:00:00.000Z"
    ) == 1


def test_bars_written_since_counts_distinct_minute_not_per_source(archive):
    """The same minute covered by both IG and yFinance must count once, not
    twice -- bars_written_since feeds the Mess-Heartbeat's (Step 6) 'Bars
    heute' figure, which must not be inflated by source multiplicity."""
    archive.insert_bars([
        _bar(ts="2026-08-11T09:00:00.000Z", source=SOURCE_YF),
        _bar(ts="2026-08-11T09:00:00.000Z", source=SOURCE_IG),
        _bar(ts="2026-08-11T09:01:00.000Z", source=SOURCE_YF),
    ])
    assert archive.bars_written_since("2026-08-11T00:00:00.000Z") == 2


# -- Phase 13 §6 A5: sources filter (L10) --------------------------------------


def test_window_sources_filter_returns_only_matching_source(archive):
    """``sources=("yf",)`` returns only yF rows — even when IG rows for the same
    minutes exist in the archive."""
    archive.insert_bars([
        _bar(ts="2026-08-11T09:00:00.000Z", source=SOURCE_YF),
        _bar(ts="2026-08-11T09:00:00.000Z", source=SOURCE_IG),
        _bar(ts="2026-08-11T09:01:00.000Z", source=SOURCE_YF),
    ])
    rows = archive.window(
        "IX.D.DAX.IFMM.IP", "1m",
        "2026-08-11T00:00:00.000Z", "2026-08-11T10:00:00.000Z",
        sources=("yf",),
    )
    assert len(rows) == 2
    assert all(b.source == "yf" for b in rows)


def test_window_sources_none_keeps_unfiltered_contract(archive):
    """``sources=None`` is the default — bit-identical to pre-A5."""
    archive.insert_bars([
        _bar(ts="2026-08-11T09:00:00.000Z", source=SOURCE_YF),
        _bar(ts="2026-08-11T09:00:00.000Z", source=SOURCE_IG),
    ])
    rows = archive.window(
        "IX.D.DAX.IFMM.IP", "1m",
        "2026-08-11T00:00:00.000Z", "2026-08-11T10:00:00.000Z",
    )
    # Without `sources`, the prefer-ranking collapses to one row per ts_utc.
    # Default prefer=("ig","ls","yf") so IG wins.
    assert len(rows) == 1
    assert rows[0].source == "ig"


def test_window_sources_combined_with_prefer(archive):
    """``sources`` filters first, ``prefer`` ranks within the surviving set."""
    archive.insert_bars([
        _bar(ts="2026-08-11T09:00:00.000Z", source=SOURCE_YF),
        _bar(ts="2026-08-11T09:00:00.000Z", source=SOURCE_IG),
    ])
    rows = archive.window(
        "IX.D.DAX.IFMM.IP", "1m",
        "2026-08-11T00:00:00.000Z", "2026-08-11T10:00:00.000Z",
        sources=("yf", "ig"),  # both pass the filter
        prefer=("yf", "ig"),   # but yF wins within them
    )
    assert len(rows) == 1
    assert rows[0].source == "yf"


def test_window_sources_unknown_source_returns_empty(archive):
    """A sources tuple that doesn't match any row is a no-op, not an error."""
    archive.insert_bars([_bar(ts="2026-08-11T09:00:00.000Z", source=SOURCE_YF)])
    rows = archive.window(
        "IX.D.DAX.IFMM.IP", "1m",
        "2026-08-11T00:00:00.000Z", "2026-08-11T10:00:00.000Z",
        sources=("nonexistent",),
    )
    assert rows == []


def test_insert_bars_writes_tick_count_none_without_error(archive):
    """A2 added the ``tick_count`` column; A5 pins that ``None`` round-trips for
    callers that don't care about the new field (the yF recorder, the legacy
    test fixtures)."""
    bar = _bar(ts="2026-08-11T09:00:00.000Z", source=SOURCE_YF)
    assert archive.insert_bars([bar]) == 1
    rows = archive.window("IX.D.DAX.IFMM.IP", "1m",
                          "2026-08-11T00:00:00.000Z", "2026-08-11T10:00:00.000Z",
                          sources=("yf",))
    assert len(rows) == 1
    assert rows[0].tick_count is None


class TestNormalizeBarTs:
    def test_ig_classic_format(self):
        assert normalize_bar_ts("2026/08/11 09:00:00") == "2026-08-11T09:00:00.000Z"

    def test_iso_with_z(self):
        assert normalize_bar_ts("2026-08-11T09:00:00.123Z") == "2026-08-11T09:00:00.123Z"

    def test_already_normalized_naive_iso(self):
        assert normalize_bar_ts("2026-08-11T09:00:00") == "2026-08-11T09:00:00.000Z"

    def test_rejects_unrecognized(self):
        with pytest.raises(ArchiveError):
            normalize_bar_ts("not-a-timestamp")

    def test_rejects_empty(self):
        with pytest.raises(ArchiveError):
            normalize_bar_ts("")
