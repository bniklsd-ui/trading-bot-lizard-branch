"""Block B (Step 9) — deterministic regime-feature extraction (V3-D4, observe-only).

**No VETO-code touch (verified this session):** ``phase5_execution/execution/vetos.py``'s
``pre_trade_check`` only ever returns a ``VetoVerdict`` — the ``get_ohlcv`` bars fetched
inside ``veto_momentum`` for VETO 3 never leave that function, so the executor has no bars
in scope at either exit (TRADE or NO_TRADE) without editing safety-critical VETO code, which
is out of bounds for this session (root ``CLAUDE.md`` hard rule 2). Callers therefore pass
``bars=None`` in practice today; this module still handles a real ``bars`` sequence correctly
(a future session may wire a dedicated regime-only bar fetch) — the fallback path
(``data_source="quote_only"``) is the plan's own sanctioned degradation (§14 drop-order #3),
not a shortcut taken here.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import Mapping, Sequence
from zoneinfo import ZoneInfo

from market_context.models import RegimeSnapshot

_BERLIN = ZoneInfo("Europe/Berlin")

# Time-of-day buckets (Europe/Berlin, DAX-session-shaped). Boundaries are module
# constants — "kalibrieren nach Datenlage, nutzt nichts" (plan §9), tune later.
_OPEN_END_H = 9
_MORNING_END_H = 11
_LUNCH_END_H = 14
_AFTERNOON_END_H = 17

# regime_tag thresholds — observe-only (V3-D4), gate nothing. Tune once there's data.
_CHOP_RANGE_PCT = 0.15       # range below this over the window -> CHOP
_HIGH_VOL_RANGE_PCT = 0.6    # range above this during OPEN -> HIGH_VOL_OPEN
_TREND_MIN_NET_MOVE_PCT = 0.3  # |close[-1]-close[0]| / close[0] above this -> TREND


def _time_bucket(now_utc: datetime) -> str:
    """Wall-clock time bucket in Europe/Berlin — needs no bars."""
    local = now_utc.astimezone(_BERLIN)
    hour = local.hour + local.minute / 60.0
    if hour < _OPEN_END_H:
        return "OPEN"
    if hour < _MORNING_END_H:
        return "MORNING"
    if hour < _LUNCH_END_H:
        return "LUNCH"
    if hour < _AFTERNOON_END_H:
        return "AFTERNOON"
    return "CLOSE"


def _atr_points(bars: Sequence[Mapping]) -> float | None:
    """Classic ATR (mean true range) over the given bars. ``None`` if fewer than 2 bars."""
    if len(bars) < 2:
        return None
    true_ranges = []
    prev_close = bars[0]["close"]
    for bar in bars[1:]:
        high, low, close = bar["high"], bar["low"], bar["close"]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        true_ranges.append(tr)
        prev_close = close
    return sum(true_ranges) / len(true_ranges)


def _range_pct(bars: Sequence[Mapping]) -> float | None:
    """(max high - min low) / first close, as a percent. ``None`` if bars are empty."""
    if not bars:
        return None
    first_close = bars[0]["close"]
    if not first_close:
        return None
    highest = max(b["high"] for b in bars)
    lowest = min(b["low"] for b in bars)
    return (highest - lowest) / first_close * 100.0


def compute_regime_features(
    bars: Sequence[Mapping] | None,
    spread_pct: float | None,
    now_utc: datetime,
    *,
    epic: str | None = None,
) -> RegimeSnapshot:
    """Build a :class:`RegimeSnapshot`. ``bars=None``/too-short -> degraded quote-only row."""
    time_bucket = _time_bucket(now_utc)
    if not bars or len(bars) < 2:
        return RegimeSnapshot.new(
            epic=epic,
            spread_pct=spread_pct,
            atr_points=None,
            range_pct=None,
            time_bucket=time_bucket,
            regime_tag=None,
            data_source="quote_only",
            degraded=True,
        )
    snapshot = RegimeSnapshot.new(
        epic=epic,
        spread_pct=spread_pct,
        atr_points=_atr_points(bars),
        range_pct=_range_pct(bars),
        time_bucket=time_bucket,
        regime_tag=None,
        data_source="ig_bars",
        degraded=False,
    )
    tag = classify_regime_tag(snapshot)
    return snapshot if tag is None else dataclasses.replace(snapshot, regime_tag=tag)


def classify_regime_tag(snapshot: RegimeSnapshot) -> str | None:
    """Simple documented thresholds — observe-only (V3-D4), gates nothing.

    ``None`` whenever the inputs are insufficient (degraded/quote-only snapshots always
    resolve to ``None`` here, since ``range_pct`` is required).
    """
    if snapshot.range_pct is None:
        return None
    if snapshot.time_bucket == "OPEN" and snapshot.range_pct >= _HIGH_VOL_RANGE_PCT:
        return "HIGH_VOL_OPEN"
    if snapshot.time_bucket == "LUNCH" and snapshot.range_pct < _CHOP_RANGE_PCT:
        return "LUNCH_DRIFT"
    if snapshot.range_pct < _CHOP_RANGE_PCT:
        return "CHOP"
    if snapshot.range_pct >= _TREND_MIN_NET_MOVE_PCT:
        return "TREND"
    return None
