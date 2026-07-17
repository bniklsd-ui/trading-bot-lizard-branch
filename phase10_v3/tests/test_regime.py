"""Step 9 tests — regime.py feature extraction + time_bucket/regime_tag thresholds."""

from __future__ import annotations

from datetime import datetime, timezone

from market_context.regime import (
    _atr_points,
    _range_pct,
    _time_bucket,
    classify_regime_tag,
    compute_regime_features,
)


def _bar(o, h, l, c):
    return {"open": o, "high": h, "low": l, "close": c}


def test_atr_hand_calc():
    # true ranges: max(11-9, |11-10|, |9-10|)=2 ; max(12-10, |12-11|, |10-11|)=2
    bars = [_bar(10, 10, 10, 10), _bar(10, 11, 9, 11), _bar(11, 12, 10, 12)]
    assert _atr_points(bars) == 2.0


def test_atr_none_with_fewer_than_two_bars():
    assert _atr_points([_bar(10, 10, 10, 10)]) is None
    assert _atr_points([]) is None


def test_range_pct_hand_calc():
    bars = [_bar(100, 101, 99, 100), _bar(100, 103, 98, 101)]
    # (max high 103 - min low 98) / first close 100 * 100 = 5.0
    assert _range_pct(bars) == 5.0


def test_time_bucket_boundaries():
    # All inputs given in UTC; Europe/Berlin is UTC+2 in July (CEST) — converted internally.
    assert _time_bucket(datetime(2026, 7, 17, 6, 59, tzinfo=timezone.utc)) == "OPEN"  # 08:59 Berlin
    assert _time_bucket(datetime(2026, 7, 17, 7, 30, tzinfo=timezone.utc)) == "MORNING"  # 09:30
    assert _time_bucket(datetime(2026, 7, 17, 9, 30, tzinfo=timezone.utc)) == "LUNCH"  # 11:30
    assert _time_bucket(datetime(2026, 7, 17, 12, 30, tzinfo=timezone.utc)) == "AFTERNOON"  # 14:30
    assert _time_bucket(datetime(2026, 7, 17, 15, 30, tzinfo=timezone.utc)) == "CLOSE"  # 17:30


def test_compute_regime_features_degrades_to_quote_only_without_bars():
    now = datetime(2026, 7, 17, 9, 0, tzinfo=timezone.utc)
    snap = compute_regime_features(None, spread_pct=0.05, now_utc=now, epic="IX.D.DAX.IFMM.IP")
    assert snap.data_source == "quote_only"
    assert snap.degraded is True
    assert snap.atr_points is None
    assert snap.range_pct is None
    assert snap.regime_tag is None  # classify_regime_tag requires range_pct
    assert snap.epic == "IX.D.DAX.IFMM.IP"
    assert snap.spread_pct == 0.05


def test_compute_regime_features_degrades_with_a_single_bar():
    now = datetime(2026, 7, 17, 9, 0, tzinfo=timezone.utc)
    snap = compute_regime_features([_bar(10, 10, 10, 10)], None, now)
    assert snap.data_source == "quote_only"
    assert snap.degraded is True


def test_compute_regime_features_with_real_bars():
    now = datetime(2026, 7, 17, 6, 0, tzinfo=timezone.utc)  # 08:00 Berlin -> OPEN
    bars = [_bar(100, 101, 99, 100), _bar(100, 105, 95, 102)]  # range_pct = 10.0 >= HIGH_VOL
    snap = compute_regime_features(bars, 0.02, now, epic="X")
    assert snap.data_source == "ig_bars"
    assert snap.degraded is False
    assert snap.atr_points is not None
    assert snap.range_pct == 10.0
    assert snap.time_bucket == "OPEN"
    assert snap.regime_tag == "HIGH_VOL_OPEN"


def test_classify_regime_tag_chop():
    now = datetime(2026, 7, 17, 7, 30, tzinfo=timezone.utc)  # 09:30 Berlin -> MORNING
    bars = [_bar(100, 100.02, 99.98, 100), _bar(100, 100.03, 99.97, 100.01)]
    snap = compute_regime_features(bars, None, now)
    assert snap.time_bucket == "MORNING"
    assert snap.regime_tag == "CHOP"


def test_classify_regime_tag_lunch_drift():
    now = datetime(2026, 7, 17, 9, 30, tzinfo=timezone.utc)  # 11:30 Berlin -> LUNCH
    bars = [_bar(100, 100.02, 99.98, 100), _bar(100, 100.03, 99.97, 100.01)]
    snap = compute_regime_features(bars, None, now)
    assert snap.time_bucket == "LUNCH"
    assert snap.regime_tag == "LUNCH_DRIFT"


def test_classify_regime_tag_none_without_range_pct():
    from market_context.models import RegimeSnapshot

    snap = RegimeSnapshot.new(
        epic=None, spread_pct=None, atr_points=None, range_pct=None,
        time_bucket="MORNING", regime_tag=None, data_source="quote_only", degraded=True,
    )
    assert classify_regime_tag(snap) is None
