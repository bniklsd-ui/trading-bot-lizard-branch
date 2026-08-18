"""Tests for ``data_foundation.service`` (Plan §6 Step 4 + Phase 13 §6 A2). No network."""

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


def test_ig_provider_normalizes_ig_raw_timestamps(archive, budget):
    """U1 (P12.5 plan §3): IG's real ``get_ohlcv`` shape is ``"yyyy/MM/dd HH:mm:ss"``,
    never ISO -- the provider must normalize it, not pass it through raw."""
    broker = _FakeBroker(bars=[
        {"timestamp": "2026/08/17 14:15:00", "open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 9}
    ])
    provider = BudgetedIGBarProvider(broker, budget)

    bars = provider.get_bars(EPIC, resolution="1m", count=1)

    assert bars is not None
    assert bars[0].ts == "2026-08-17T14:15:00.000Z"


def test_ig_provider_returns_none_on_unparseable_timestamp(archive, budget):
    broker = _FakeBroker(bars=[
        {"timestamp": "not a date", "open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 9}
    ])
    events = []
    provider = BudgetedIGBarProvider(broker, budget, health_sink=events.append)

    assert provider.get_bars(EPIC, resolution="1m", count=1) is None
    assert events[-1]["reason"] == "bad_timestamp"


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


# -- BarService.get_window (tracker seam, Phase 13 §6 A2: pure archive read) --


def test_get_window_returns_archive_rows_only(archive, budget):
    """A pure archive read: whatever the archive holds, the tracker gets — nothing else."""
    from data_foundation.models import Bar

    ts = _iso(NOW - timedelta(minutes=2))
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc=ts, open=1, high=1, low=1, close=1, volume=1, source="yf", fetched_at=ts)])
    fake = _FakeProvider()  # raises on `get_bars` via getattr default — must never be called
    svc = BarService(archive, [("yf", fake)], budget, now_fn=lambda: NOW)

    result = svc.get_window(EPIC, "1m", _iso(NOW - timedelta(minutes=5)), _iso(NOW))

    assert fake.calls == []
    assert len(result) == 1
    assert result[0]["timestamp"] == ts
    assert result[0]["source"] == "yf"


def test_get_window_empty_archive_returns_empty(archive, budget):
    """Empty archive ⇒ empty window. No chain call. No fallback."""
    fake = _FakeProvider()
    svc = BarService(archive, [("yf", fake)], budget, now_fn=lambda: NOW)

    result = svc.get_window(EPIC, "1m", _iso(NOW - timedelta(minutes=5)), _iso(NOW))

    assert result == []
    assert fake.calls == []


def test_get_window_never_fetches(archive, budget):
    """L12 — die strukturelle Kostenzusicherung.

    Both providers raise AssertionError on ``get_bars``. ``get_window`` must complete
    (returning whatever the archive holds, here empty) without ever invoking either
    provider. This is the test that fails if the IG-top-up or full-window refetch
    is reintroduced — it doesn't pin a number (which tomorrow's parametrization
    would invalidate), it pins the structure."""
    class _ExplodingProvider:
        def get_bars(self, epic, *, resolution, count):
            raise AssertionError("no fetch allowed — get_window must read archive only")

    yf = _ExplodingProvider()
    ig = _ExplodingProvider()
    svc = BarService(archive, [("yf", yf), ("ig", ig)], budget, now_fn=lambda: NOW)

    # Empty archive: nothing to return, must not raise.
    result = svc.get_window(EPIC, "1m", _iso(NOW - timedelta(minutes=5)), _iso(NOW))
    assert result == []


def test_get_window_passes_through_tick_count(archive, budget):
    """``tick_count`` rides through ``_bar_to_dict`` so the coverage / source-delta
    reports can read it; the tracker itself doesn't, but the dict shape stays
    stable for all readers."""
    from data_foundation.models import Bar

    ts = _iso(NOW - timedelta(minutes=1))
    archive.insert_bars([Bar(
        epic=EPIC, resolution="1m", ts_utc=ts, open=1, high=1, low=1, close=1, volume=1,
        source="ls", fetched_at=ts, tick_count=42,
    )])
    svc = BarService(archive, [], budget, now_fn=lambda: NOW)

    result = svc.get_window(EPIC, "1m", _iso(NOW - timedelta(minutes=5)), _iso(NOW))

    assert result and result[0]["tick_count"] == 42


def test_get_window_tick_count_defaults_to_none_for_old_rows(archive, budget):
    """Rows written before A5's schema migration carry no ``tick_count`` — the dict
    must expose ``None`` rather than KeyError."""
    from data_foundation.models import Bar

    ts = _iso(NOW - timedelta(minutes=1))
    archive.insert_bars([Bar(epic=EPIC, resolution="1m", ts_utc=ts, open=1, high=1, low=1, close=1, volume=1, source="yf", fetched_at=ts)])
    svc = BarService(archive, [], budget, now_fn=lambda: NOW)

    result = svc.get_window(EPIC, "1m", _iso(NOW - timedelta(minutes=5)), _iso(NOW))

    assert result and result[0]["tick_count"] is None


def test_bar_service_has_no_ig_provider_attribute(archive, budget):
    """Structure guard against a silent re-opening of the IG-top-up path. The
    old ``_ig_provider`` attribute is gone; if anyone re-introduces it, this
    test fails at instantiation (the attribute is still created) instead of
    at runtime (the fetch path is still gone)."""
    svc = BarService(archive, [("yf", _FakeProvider()), ("ig", _FakeProvider())], budget)
    assert not hasattr(svc, "_ig_provider")


# -- BarProvider protocol compliance ------------------------------------------


def test_bar_service_implements_bar_provider_protocol(archive, budget):
    svc = BarService(archive, [], budget, now_fn=lambda: NOW)
    assert hasattr(svc, "get_bars") and callable(svc.get_bars)
