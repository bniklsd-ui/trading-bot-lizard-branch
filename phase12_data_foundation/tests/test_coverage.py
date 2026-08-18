"""Tests for ``data_foundation.coverage.assess_window`` (Phase 13 §6 Step A1, §6 tests).

Greift ausschließlich die in §6 A1 gelisteten 9 Fälle ab; folgt der Stil-Konvention
von ``test_archive.py`` (Modul-imports, ``@pytest.fixture``, Top-Level ``def test_*``).
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from data_foundation.coverage import (
    MAX_WINDOW_GAP_MIN,
    MIN_WINDOW_RATIO,
    WindowCoverage,
    assess_window,
)


START = "2026-08-11T09:00:00.000Z"
END = "2026-08-11T14:00:00.000Z"  # 300-Min-Fenster, 1-Min-Cadence, expected=300


def _iso(dt: datetime) -> str:
    """ISO 8601 UTC ms + 'Z' — selbe Form wie ``models.normalize_bar_ts``."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def _minutes(n: int, *, start_utc: str = START) -> list[str]:
    """``n`` aufeinanderfolgende 1-Min-ISO-Stempel ab ``start_utc``."""
    base = datetime.fromisoformat(start_utc.replace("Z", "+00:00"))
    return [_iso(base + timedelta(minutes=i)) for i in range(n)]


# --- die neun Pflicht-Tests aus Plan §6 Step A1 ---

def test_full_window_is_covered():
    result = assess_window(_minutes(300), START, END, 1)
    assert result.covered is True
    assert result.ratio == 1.0
    assert result.largest_gap_min == 0
    assert result.reason is None


def test_empty_input_is_not_covered():
    result = assess_window([], START, END, 1)
    assert result.covered is False
    assert result.reason == "empty"


def test_mid_window_gap_triggers_gap_reason_even_at_good_ratio():
    # 20-Min-Loch ab Minute 60 — das ist der F3-Test (erfundene TIME_STOP).
    full = _minutes(300)
    hole = full[:60] + full[80:]  # 280 distinkte Minuten, Quote ≈ 0,93
    result = assess_window(hole, START, END, 1)
    assert result.covered is False
    assert result.reason == "gap"
    assert result.ratio > MIN_WINDOW_RATIO  # Quote sagt OK, Lücke sagt nein
    assert result.largest_gap_min >= 20


def test_gap_at_window_start_is_a_gap():
    result = assess_window(
        _minutes(280, start_utc="2026-08-11T09:20:00.000Z"), START, END, 1
    )
    assert result.covered is False
    assert result.reason == "gap"


def test_gap_at_window_end_is_a_gap():
    result = assess_window(_minutes(280), START, END, 1)  # nur 09:00..13:39
    assert result.covered is False
    assert result.reason == "gap"


def test_even_sparseness_is_sparse():
    # 150 distinkte Minuten in gleichmäßigen 2-Min-Schritten — kein run > 1 Min,
    # aber Quote unter der Schwelle.
    full = _minutes(300)
    sparse = full[::2]
    result = assess_window(sparse, START, END, 1)
    assert result.covered is False
    assert result.reason == "sparse"


def test_gap_reason_takes_precedence_over_sparse():
    # Sowohl Quote (≈ 0,22) als auch Lücke (> 5 Min) würden greifen — gap gewinnt.
    full = _minutes(300)
    timestamps = full[:60] + full[80:85]  # 65 marks, Schwanz-Lücke ~215 Min
    result = assess_window(timestamps, START, END, 1)
    assert result.covered is False
    assert result.reason == "gap"
    assert result.ratio < MIN_WINDOW_RATIO  # sparse wäre auch fällig


def test_zero_length_window_has_no_division_error():
    same = "2026-08-11T09:00:00.000Z"
    result = assess_window([], same, same, 1)
    assert result.covered is False  # kein ZeroDivisionError


def test_duplicate_timestamps_count_once():
    one = "2026-08-11T10:00:00.000Z"
    result = assess_window(
        [one, one, one],
        "2026-08-11T09:00:00.000Z",
        "2026-08-11T11:00:00.000Z",
        1,
    )
    assert result.present == 1
    assert result.expected == 120


# --- defensive Begleit-Tests (bezahlte Pflicht-Tests sind grün, diese sichern die Naht) ---

def test_timestamps_outside_window_are_ignored():
    # 1 Treffer in der Mitte, 5 völlig außerhalb — present bleibt 1.
    inside = "2026-08-11T10:00:00.000Z"
    outside = [
        "2026-08-10T09:00:00.000Z",  # vor dem Fenster
        "2026-08-12T09:00:00.000Z",  # nach dem Fenster
        "2026-08-11T14:00:00.000Z",  # genau auf end (exklusiv) → auch raus
    ]
    result = assess_window([inside, *outside, inside, inside], START, END, 1)
    assert result.present == 1
    assert result.expected == 300


def test_default_thresholds_match_module_constants():
    # Default-Konstanten sind die Konstanten — der Vertrag hängt nicht an einer
    # versteckten Zahl.
    assert MIN_WINDOW_RATIO == 0.90
    assert MAX_WINDOW_GAP_MIN == 5


def test_return_type_is_frozen_windowcoverage():
    result = assess_window(_minutes(300), START, END, 1)
    assert isinstance(result, WindowCoverage)
    with pytest.raises(Exception):
        result.covered = False  # type: ignore[misc]
