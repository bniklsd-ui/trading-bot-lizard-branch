"""Tests for ``data_foundation.service`` (Plan §6 Step 4). No network."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from data_foundation.archive import BarArchive
from data_foundation.budget import IG_QUOTA_V1, SourceBudget
from data_foundation.service import BarService, BudgetedIGBarProvider

EPIC = "IX.D.DAX.IFMM.IP"
NOW = datetime(2026, 8, 16, 10, 0, 0, tzinfo=timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


class _FakeProvider:
    """A named BarProvider fake: returns a fixed bar list, or None, records calls."""

    def __init__(self, bars=None):
        self.bars = bars
        self.calls: list[tuple] = []

    def get_bars(self, epic, *, resolution, count):
        self.calls.append((epic, resolution, count))
        return self.bars


def _pricebar(ts, close=100.0):
    from external_data.models import PriceBar

    return PriceBar(ts=ts, open=close, high=close, low=close, close=close, volume=10.0)


@pytest.fixture
def archive(tmp_path) -> BarArchive:
    a = BarArchive(tmp_path / "bars.sqlite")
    a.ensure_schema()
    yield a
    a.close()


@pytest.fixture
def budget(tmp_path) -> SourceBudget:
    return SourceBudget(tmp_path / "bars.sqlite", IG_QUOTA_V1, now_fn=lambda: NOW)


class _FakeBroker:
    def __init__(self, allowance=None, bars=None, ok=True, raises=False):
        self.allowance = allowance or {}
        self.bars = bars if bars is not None else [
            {"timestamp": _iso(NOW), "open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 9}
        ]
        self.ok = ok
        self.raises = raises
        self.calls: list[tuple] = []

    def get_ohlcv(self, epic, resolution, count):
        self.calls.append((epic, resolution, count))
        if self.raises:
            raise RuntimeError("boom")
        return SimpleNamespace(ok=self.ok, data={"bars": self.bars, "allowance": self.allowance})


# -- BudgetedIGBarProvider ----------------------------------------------------


def test_budgeted_ig_refuses_when_cannot_spend(archive, budget):
    budget.record_spend(9_900, "tracker")  # leaves < reserve for a 300-point ask
    broker = _FakeBroker()
    events = []
    provider = BudgetedIGBarProvider(broker, budget, health_sink=events.append)

    result = provider.get_bars(EPIC, resolution="1m", count=300)

    assert result is None
    assert broker.calls == []  # no broker call at all
    assert events[-1] == {
        "event": "bar_fetch", "provider": "ig", "epic": EPIC, "ok": False,
        "reason": "budget", "spend_kind": "research",
    }


def test_budgeted_ig_books_spend_and_allowance_on_success(archive, budget):
    # allowanceExpiry is IG's real shape: seconds remaining, not absolute ISO
    # (phase12_data_foundation/CLAUDE.md Session 4, live-verified 2026-08-17).
    broker = _FakeBroker(allowance={"totalAllowance": 10_000, "remainingAllowance": 9_700, "allowanceExpiry": 345_600})
    provider = BudgetedIGBarProvider(broker, budget, now_fn=lambda: NOW)

    bars = provider.get_bars(EPIC, resolution="1m", count=1)

    assert bars is not None and len(bars) == 1
    assert budget.spent_in_window() == 1
    assert budget.remaining_estimate() == 9_700 - 0  # observation wins, no spend recorded after it


def test_budgeted_ig_never_raises_on_broker_exception(archive, budget):
    broker = _FakeBroker(raises=True)
    provider = BudgetedIGBarProvider(broker, budget)
    assert provider.get_bars(EPIC, resolution="1m", count=1) is None


def test_budgeted_ig_never_raises_on_not_ok_envelope(archive, budget):
    broker = _FakeBroker(ok=False)
    provider = BudgetedIGBarProvider(broker, budget)
    assert provider.get_bars(EPIC, resolution="1m", count=1) is None


def test_budgeted_ig_unmapped_resolution_returns_none(archive, budget):
    provider = BudgetedIGBarProvider(_FakeBroker(), budget)
    assert provider.get_bars(EPIC, resolution="bogus", count=1) is None


# -- BarService.get_bars (research seam) --------------------------------------


def test_get_bars_archive_hit_makes_zero_chain_calls(archive, budget):
    ts = _iso(NOW - timedelta(minutes=1))
    from data_foundation.models import Bar

    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc=ts, open=1, high=1, low=1, close=1, volume=1, source="yf", fetched_at=ts)])
    yf = _FakeProvider([_pricebar(ts)])
    ig = _FakeProvider([_pricebar(ts)])
    svc = BarService(archive, [("yf", yf), ("ig", ig)], budget, now_fn=lambda: NOW - timedelta(minutes=0, seconds=30))

    result = svc.get_bars(EPIC, resolution="1m", count=1)

    assert yf.calls == [] and ig.calls == []
    assert result is not None


def test_get_bars_gap_uses_chain_yf_first_and_writes_through(archive, budget):
    ts = _iso(NOW)
    yf = _FakeProvider([_pricebar(ts)])
    ig = _FakeProvider([_pricebar(ts)])
    svc = BarService(archive, [("yf", yf), ("ig", ig)], budget, now_fn=lambda: NOW)

    result = svc.get_bars(EPIC, resolution="1m", count=1)

    assert result is not None
    assert yf.calls and not ig.calls  # yF-first: IG never tried when yF succeeds
    archived = archive.window(EPIC, "1m", _iso(NOW - timedelta(minutes=5)), _iso(NOW + timedelta(minutes=1)))
    assert len(archived) == 1 and archived[0].source == "yf"


def test_get_bars_falls_back_to_ig_when_yf_returns_none(archive, budget):
    ts = _iso(NOW)
    yf = _FakeProvider(None)
    ig = _FakeProvider([_pricebar(ts)])
    svc = BarService(archive, [("yf", yf), ("ig", ig)], budget, now_fn=lambda: NOW)

    result = svc.get_bars(EPIC, resolution="1m", count=1)

    assert result is not None
    assert ig.calls
    archived = archive.window(EPIC, "1m", _iso(NOW - timedelta(minutes=5)), _iso(NOW + timedelta(minutes=1)))
    assert archived[0].source == "ig"


def test_get_bars_unknown_resolution_returns_none(archive, budget):
    svc = BarService(archive, [], budget, now_fn=lambda: NOW)
    assert svc.get_bars(EPIC, resolution="bogus", count=1) is None


def test_get_bars_empty_chain_result_returns_none(archive, budget):
    svc = BarService(archive, [("yf", _FakeProvider(None)), ("ig", _FakeProvider(None))], budget, now_fn=lambda: NOW)
    assert svc.get_bars(EPIC, resolution="1m", count=1) is None


# -- BarService.get_window (tracker seam) -------------------------------------


def test_get_window_archive_hit_makes_zero_chain_calls(archive, budget):
    ts = _iso(NOW - timedelta(seconds=30))  # within the last resolution-minute of "now"
    from data_foundation.models import Bar

    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc=ts, open=1, high=1, low=1, close=1, volume=1, source="ig", fetched_at=ts)])
    yf, ig = _FakeProvider(), _FakeProvider()
    svc = BarService(archive, [("yf", yf), ("ig", ig)], budget, now_fn=lambda: NOW)

    result = svc.get_window(EPIC, "1m", _iso(NOW - timedelta(minutes=5)), _iso(NOW))

    assert result and result[0]["source"] == "ig"
    assert yf.calls == [] and ig.calls == []


def test_get_window_ig_topup_fires_when_yf_result_is_short(archive, budget):
    """The Advisor finding: a short-but-non-None yF result must not silently stop the
    chain — get_window must top up from IG so the tracker's window still reaches the
    tail it needs."""
    start = NOW - timedelta(minutes=10)
    end = NOW
    short_ts = _iso(start + timedelta(minutes=1))   # far from the tail
    full_ts = _iso(end - timedelta(seconds=30))     # within the last resolution-minute
    yf = _FakeProvider([_pricebar(short_ts)])        # doesn't reach the tail
    ig = _FakeProvider([_pricebar(short_ts), _pricebar(full_ts)])  # reaches it
    svc = BarService(archive, [("yf", yf), ("ig", ig)], budget, now_fn=lambda: NOW)

    result = svc.get_window(EPIC, "1m", _iso(start), _iso(end))

    assert ig.calls, "IG top-up must fire when yF's result doesn't cover the tail"
    sources = {b["source"] for b in result}
    assert "ig" in sources
    assert any(b["timestamp"] == full_ts for b in result)


def test_get_window_ig_topup_does_not_fire_when_yf_already_covers_tail(archive, budget):
    start = NOW - timedelta(minutes=10)
    end = NOW
    full_ts = _iso(end - timedelta(seconds=30))  # within the last resolution-minute
    yf = _FakeProvider([_pricebar(full_ts)])
    ig = _FakeProvider([_pricebar(full_ts)])
    svc = BarService(archive, [("yf", yf), ("ig", ig)], budget, now_fn=lambda: NOW)

    svc.get_window(EPIC, "1m", _iso(start), _iso(end))

    assert not ig.calls


def test_get_window_mixed_source_reports_per_bar_source(archive, budget):
    from data_foundation.models import Bar

    old_ts = _iso(NOW - timedelta(minutes=8))
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc=old_ts, open=1, high=1, low=1, close=1, volume=1, source="ig", fetched_at=old_ts)])
    tail_ts = _iso(NOW - timedelta(seconds=30))
    yf = _FakeProvider([_pricebar(old_ts), _pricebar(tail_ts)])
    svc = BarService(archive, [("yf", yf), ("ig", _FakeProvider())], budget, now_fn=lambda: NOW)

    result = svc.get_window(EPIC, "1m", _iso(NOW - timedelta(minutes=10)), _iso(NOW))

    by_ts = {b["timestamp"]: b["source"] for b in result}
    assert by_ts[old_ts] == "ig"   # archive's preferred source wins (BarArchive.window's `prefer`)
    assert by_ts[tail_ts] == "yf"


def test_get_window_no_ig_provider_configured_returns_whatever_archive_has(archive, budget):
    yf = _FakeProvider([_pricebar(_iso(NOW - timedelta(minutes=5)))])  # doesn't reach tail
    svc = BarService(archive, [("yf", yf)], budget, now_fn=lambda: NOW)

    result = svc.get_window(EPIC, "1m", _iso(NOW - timedelta(minutes=10)), _iso(NOW))

    assert result  # whatever was archived, no crash from a missing "ig" entry


# -- BarProvider protocol compliance ------------------------------------------


def test_bar_service_implements_bar_provider_protocol(archive, budget):
    svc = BarService(archive, [], budget, now_fn=lambda: NOW)
    assert hasattr(svc, "get_bars") and callable(svc.get_bars)
