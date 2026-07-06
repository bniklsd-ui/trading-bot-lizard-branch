"""Tests for the promotion status machine (Phase 9 / V2 Step 4).

Fake broker/fetcher (duck-typed, matching ``scripts/verify_instrument.py``'s
expected surface) + a real ``UniverseStore`` against a temp SQLite file.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from universe.exceptions import UniverseSafetyError
from universe.models import (
    STATUS_ACTIVE,
    STATUS_DISCOVERED,
    STATUS_QUARANTINED,
    STATUS_VERIFIED,
    UniverseRecord,
)
from universe.promotion import PromotionReport, run_promotion_cycle
from universe.store import UniverseStore, utc_iso_now

_MIGRATION_004 = (
    Path(__file__).resolve().parents[2]
    / "phase2_persistence"
    / "migrations"
    / "004_phase9_instrument_universe.sql"
)


@pytest.fixture()
def store(tmp_path) -> UniverseStore:
    db_path = tmp_path / "promotion_test.sqlite"
    bootstrap = sqlite3.connect(str(db_path))
    bootstrap.executescript(_MIGRATION_004.read_text(encoding="utf-8"))
    bootstrap.commit()
    bootstrap.close()
    s = UniverseStore(db_path)
    yield s
    s.close()


def _env(ok: bool, data: dict | None = None) -> SimpleNamespace:
    return SimpleNamespace(ok=ok, data=data or {}, error=None if ok else {"message": "boom"})


def _discovered(epic: str, **overrides) -> UniverseRecord:
    now = utc_iso_now()
    defaults = dict(
        epic=epic,
        name="Deutschland 40 Kassa (1€)",
        yf_ticker="^GDAXI",
        volume_proxy=None,
        point_value=None,
        point_value_source=None,
        min_deal_size=0.5,
        currency="EUR",
        status=STATUS_DISCOVERED,
        source="research_promoted",
        checks={},
        fail_count=0,
        data_degraded=False,
        last_verified_at=None,
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return UniverseRecord(**defaults)


class _FakeBroker:
    """``get_market_info`` + ``get_ohlcv``, both fully controllable per epic."""

    def __init__(self, market_infos: dict, ohlcv_ok: dict | None = None):
        self.market_infos = market_infos
        self.ohlcv_ok = ohlcv_ok or {}

    def get_market_info(self, epic: str):
        return self.market_infos.get(epic, _env(False))

    def get_ohlcv(self, epic: str, resolution: str, count: int):
        ok = self.ohlcv_ok.get(epic, True)
        return _env(ok, {"bars": [1, 2, 3]} if ok else {})


class _FakeFetcher:
    """``get_history`` + ``get_bars`` + ``get_volume_anomaly``, all pass by default."""

    def __init__(self, *, history_ok=True, bars_ok=True, volume_ok=True):
        self.history_ok = history_ok
        self.bars_ok = bars_ok
        self.volume_ok = volume_ok

    def get_history(self, epic: str, days: int):
        return [1, 2, 3] if self.history_ok else []

    def get_bars(self, epic: str, resolution: str, count: int):
        return [1, 2, 3] if self.bars_ok else []

    def get_volume_anomaly(self, epic: str):
        return SimpleNamespace(volume_available=self.volume_ok)


def _passing_market_info(name="Deutschland 40 Kassa (1€)", lot_size=1.0) -> SimpleNamespace:
    return _env(
        True,
        {
            "currency": "EUR",
            "min_deal_size": 0.5,
            "name": name,
            "lot_size": lot_size,
        },
    )


def _no_sleep(_s: float) -> None:
    pass


# -- Safety --------------------------------------------------------------------


def test_promotion_raises_when_not_demo(store: UniverseStore):
    broker = _FakeBroker({})
    fetcher = _FakeFetcher()
    with pytest.raises(UniverseSafetyError):
        run_promotion_cycle(broker, fetcher, store, is_demo=False, sleep_fn=_no_sleep)


# -- happy path: discovered -> verified -> active ------------------------------


def test_happy_path_discovered_to_active(store: UniverseStore):
    epic = "IX.D.DAX.IFMM.IP"
    store.upsert_discovered(_discovered(epic))
    broker = _FakeBroker({epic: _passing_market_info()})
    fetcher = _FakeFetcher()

    report = run_promotion_cycle(broker, fetcher, store, is_demo=True, sleep_fn=_no_sleep)

    assert report.verified == [epic]
    assert report.activated == [epic]
    rec = store.get(epic)
    assert rec.status == STATUS_ACTIVE
    assert rec.point_value == 1.0
    assert rec.point_value_source == "name_lotsize_agree"


def test_freshly_activated_epic_is_not_reverified_same_cycle(store: UniverseStore):
    # 2026-07-04 review polish: an epic verified in Step 1 and activated in Step 2
    # carries a full verify PASS from moments ago — Step 3's health-recheck must
    # skip it this cycle (no duplicate paced IG/yF traffic), and re-include it
    # from the next cycle on. get_ohlcv fires exactly once per verify_instrument
    # call, so its per-epic count is the verify count.
    epic = "IX.D.DAX.IFMM.IP"
    store.upsert_discovered(_discovered(epic))
    broker = _FakeBroker({epic: _passing_market_info()})
    fetcher = _FakeFetcher()
    ohlcv_calls: list[str] = []
    orig_get_ohlcv = broker.get_ohlcv

    def counting_get_ohlcv(e: str, resolution: str, count: int):
        ohlcv_calls.append(e)
        return orig_get_ohlcv(e, resolution, count)

    broker.get_ohlcv = counting_get_ohlcv

    report = run_promotion_cycle(broker, fetcher, store, is_demo=True, sleep_fn=_no_sleep)

    assert report.activated == [epic]
    assert ohlcv_calls.count(epic) == 1  # Step-1 verify only — no Step-3 re-verify

    # Next cycle: the now-established active IS health-rechecked normally.
    ohlcv_calls.clear()
    run_promotion_cycle(broker, fetcher, store, is_demo=True, sleep_fn=_no_sleep)
    assert ohlcv_calls.count(epic) == 1  # the regular Step-3 health-recheck


def test_pass_without_pricing_stays_discovered(store: UniverseStore):
    epic = "IX.D.NOPRICE.IP"
    store.upsert_discovered(_discovered(epic, name="Unresolvable Index"))
    broker = _FakeBroker({epic: _env(True, {"currency": "EUR", "min_deal_size": 0.5, "name": "Unresolvable Index", "lot_size": None})})
    fetcher = _FakeFetcher()

    report = run_promotion_cycle(broker, fetcher, store, is_demo=True, sleep_fn=_no_sleep)

    assert report.verified == []
    assert report.activated == []
    rec = store.get(epic)
    assert rec.status == STATUS_DISCOVERED
    assert rec.point_value is None


def test_verify_fail_quarantines_candidate(store: UniverseStore):
    epic = "IX.D.BADCUR.IP"
    store.upsert_discovered(_discovered(epic))
    broker = _FakeBroker({epic: _env(True, {"currency": "USD", "min_deal_size": 0.5, "name": "x", "lot_size": 1.0})})
    fetcher = _FakeFetcher()

    report = run_promotion_cycle(broker, fetcher, store, is_demo=True, sleep_fn=_no_sleep)

    assert report.quarantined == [epic]
    rec = store.get(epic)
    assert rec.status == STATUS_QUARANTINED
    assert rec.fail_count == 1


def test_yf_only_fail_at_discovery_activates_degraded(store: UniverseStore):
    # Konzept C3 at Step 1 (2026-07-06 live finding): a yFinance-side failure
    # during the INITIAL verify must not quarantine an IG-green candidate —
    # it proceeds to verified/active with data_degraded=1, mirroring what
    # Step 3 already grants established actives.
    epic = "IX.D.DAX.IFMM.IP"
    store.upsert_discovered(_discovered(epic))
    broker = _FakeBroker({epic: _passing_market_info()})
    fetcher = _FakeFetcher(history_ok=False, bars_ok=False, volume_ok=False)

    report = run_promotion_cycle(broker, fetcher, store, is_demo=True, sleep_fn=_no_sleep)

    assert report.quarantined == []
    assert report.verified == [epic]
    assert report.activated == [epic]
    rec = store.get(epic)
    assert rec.status == STATUS_ACTIVE
    assert rec.data_degraded is True
    assert rec.fail_count == 0  # IG side healthy — nothing counted


def test_ig_fail_at_discovery_still_quarantines_despite_healthy_yf(store: UniverseStore):
    # The inverse guard: C3 tolerance is yF-only — an IG-side failure at Step 1
    # quarantines regardless of a fully healthy yFinance side.
    epic = "IX.D.BADCUR2.IP"
    store.upsert_discovered(_discovered(epic))
    broker = _FakeBroker({epic: _env(True, {"currency": "USD", "min_deal_size": 0.5, "name": "x", "lot_size": 1.0})})
    fetcher = _FakeFetcher()  # yf all green

    report = run_promotion_cycle(broker, fetcher, store, is_demo=True, sleep_fn=_no_sleep)

    assert report.quarantined == [epic]
    assert store.get(epic).status == STATUS_QUARANTINED


# -- max_active cap -------------------------------------------------------------


def test_max_active_cap(store: UniverseStore):
    epics = [f"IX.D.EPIC{i}.IP" for i in range(3)]
    market_infos = {}
    for epic in epics:
        store.upsert_discovered(_discovered(epic, name=f"Foo (1€) {epic}"))
        market_infos[epic] = _passing_market_info(name=f"Foo (1€) {epic}", lot_size=1.0)
    broker = _FakeBroker(market_infos)
    fetcher = _FakeFetcher()

    report = run_promotion_cycle(broker, fetcher, store, is_demo=True, max_active=2, sleep_fn=_no_sleep)

    assert len(report.activated) == 2
    assert len(store.active_universe()) == 2


# -- demotion after repeated IG-side fails --------------------------------------


def test_demotion_after_ig_fails(store: UniverseStore):
    epic = "IX.D.DAX.IFMM.IP"
    store.upsert_discovered(_discovered(epic, status=STATUS_ACTIVE, point_value=1.0, point_value_source="curated_confirmed"))
    broker = _FakeBroker({epic: _env(False)})  # IG-side always fails (market_info not ok)
    fetcher = _FakeFetcher()

    # Cycle 1: fail_count 0->1
    run_promotion_cycle(broker, fetcher, store, is_demo=True, demote_after_fails=3, sleep_fn=_no_sleep)
    assert store.get(epic).status == STATUS_ACTIVE
    assert store.get(epic).fail_count == 1

    # Cycle 2: fail_count 1->2
    run_promotion_cycle(broker, fetcher, store, is_demo=True, demote_after_fails=3, sleep_fn=_no_sleep)
    assert store.get(epic).status == STATUS_ACTIVE
    assert store.get(epic).fail_count == 2

    # Cycle 3: fail_count 2->3 >= demote_after_fails -> quarantined
    report = run_promotion_cycle(broker, fetcher, store, is_demo=True, demote_after_fails=3, sleep_fn=_no_sleep)
    assert store.get(epic).status == STATUS_QUARANTINED
    assert epic in report.demoted


def test_yf_fail_never_demotes_only_degrades(store: UniverseStore):
    epic = "IX.D.DAX.IFMM.IP"
    store.upsert_discovered(
        _discovered(epic, status=STATUS_ACTIVE, point_value=1.0, point_value_source="curated_confirmed")
    )
    broker = _FakeBroker({epic: _passing_market_info()})
    fetcher = _FakeFetcher(history_ok=False, bars_ok=False, volume_ok=False)

    for _ in range(5):  # far more cycles than demote_after_fails would ever tolerate
        report = run_promotion_cycle(
            broker, fetcher, store, is_demo=True, demote_after_fails=2, sleep_fn=_no_sleep
        )

    assert store.get(epic).status == STATUS_ACTIVE  # never demoted
    assert epic not in report.demoted
    assert store.get(epic).data_degraded is True  # the yF-side signal, tracked separately
    assert store.get(epic).fail_count == 0  # IG side was healthy every cycle -> never counted


def test_data_degraded_clears_on_recovery(store: UniverseStore):
    epic = "IX.D.DAX.IFMM.IP"
    store.upsert_discovered(
        _discovered(epic, status=STATUS_ACTIVE, point_value=1.0, point_value_source="curated_confirmed")
    )
    broker = _FakeBroker({epic: _passing_market_info()})
    degraded_fetcher = _FakeFetcher(history_ok=False, bars_ok=False, volume_ok=False)
    run_promotion_cycle(broker, degraded_fetcher, store, is_demo=True, sleep_fn=_no_sleep)
    assert store.get(epic).data_degraded is True

    healthy_fetcher = _FakeFetcher()
    run_promotion_cycle(broker, healthy_fetcher, store, is_demo=True, sleep_fn=_no_sleep)
    assert store.get(epic).data_degraded is False


def test_fail_count_resets_after_ig_recovery(store: UniverseStore):
    epic = "IX.D.DAX.IFMM.IP"
    store.upsert_discovered(
        _discovered(epic, status=STATUS_ACTIVE, point_value=1.0, point_value_source="curated_confirmed")
    )
    failing_broker = _FakeBroker({epic: _env(False)})
    fetcher = _FakeFetcher()
    run_promotion_cycle(failing_broker, fetcher, store, is_demo=True, demote_after_fails=5, sleep_fn=_no_sleep)
    assert store.get(epic).fail_count == 1

    recovered_broker = _FakeBroker({epic: _passing_market_info()})
    run_promotion_cycle(recovered_broker, fetcher, store, is_demo=True, sleep_fn=_no_sleep)
    assert store.get(epic).fail_count == 0


# -- backoff staircase -----------------------------------------------------------


def test_backoff_staircase_delays_reverify(store: UniverseStore):
    epic = "IX.D.RETRY.IP"
    recent = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    store.upsert_discovered(
        _discovered(
            epic, status=STATUS_QUARANTINED, fail_count=2, last_verified_at=recent  # needs 4h backoff
        )
    )
    broker = _FakeBroker({epic: _passing_market_info()})
    fetcher = _FakeFetcher()

    report = run_promotion_cycle(broker, fetcher, store, is_demo=True, sleep_fn=_no_sleep)

    assert report.verified == []  # still in backoff, 1h < 2**2=4h
    assert store.get(epic).status == STATUS_QUARANTINED


def test_backoff_elapsed_allows_reverify(store: UniverseStore):
    epic = "IX.D.RETRY.IP"
    old = (datetime.now(timezone.utc) - timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    store.upsert_discovered(
        _discovered(epic, status=STATUS_QUARANTINED, fail_count=2, last_verified_at=old)
    )
    broker = _FakeBroker({epic: _passing_market_info()})
    fetcher = _FakeFetcher()

    report = run_promotion_cycle(broker, fetcher, store, is_demo=True, sleep_fn=_no_sleep)

    assert report.verified == [epic]  # 5h >= 2**2=4h -> eligible


def test_never_verified_is_always_eligible(store: UniverseStore):
    epic = "IX.D.FRESH.IP"
    store.upsert_discovered(_discovered(epic, last_verified_at=None))
    broker = _FakeBroker({epic: _passing_market_info()})
    fetcher = _FakeFetcher()

    report = run_promotion_cycle(broker, fetcher, store, is_demo=True, sleep_fn=_no_sleep)

    assert report.verified == [epic]


# -- curated confirmation + contradiction ----------------------------------------


def test_curated_confirmation_upgrades_source(store: UniverseStore):
    epic = "IX.D.STXE.IFM.IP"
    store.upsert_discovered(
        _discovered(
            epic, status=STATUS_ACTIVE, name="EU Stocks 50 Kassa (2€)",
            point_value=2.0, point_value_source=None,
        )
    )
    broker = _FakeBroker({epic: _passing_market_info(name="EU Stocks 50 Kassa (2€)", lot_size=2.0)})
    fetcher = _FakeFetcher()

    report = run_promotion_cycle(broker, fetcher, store, is_demo=True, sleep_fn=_no_sleep)

    assert epic in report.confirmed_pricing
    rec = store.get(epic)
    assert rec.point_value_source == "name_lotsize_agree"
    assert rec.status == STATUS_ACTIVE


def test_curated_contradiction_quarantines(store: UniverseStore):
    epic = "IX.D.STXE.IFM.IP"
    store.upsert_discovered(
        _discovered(
            epic, status=STATUS_ACTIVE, name="EU Stocks 50 Kassa (2€)",
            point_value=2.0, point_value_source=None,
        )
    )
    # Verify data disagrees: name/lot_size now says 1.0, not the curated 2.0.
    broker = _FakeBroker({epic: _passing_market_info(name="EU Stocks 50 Kassa (1€)", lot_size=1.0)})
    fetcher = _FakeFetcher()

    report = run_promotion_cycle(broker, fetcher, store, is_demo=True, sleep_fn=_no_sleep)

    assert epic in report.demoted
    assert store.get(epic).status == STATUS_QUARANTINED


# -- health_sink events -----------------------------------------------------------


def test_health_sink_receives_events(store: UniverseStore):
    epic = "IX.D.DAX.IFMM.IP"
    store.upsert_discovered(_discovered(epic))
    broker = _FakeBroker({epic: _passing_market_info()})
    fetcher = _FakeFetcher()

    events: list[dict] = []
    run_promotion_cycle(
        broker, fetcher, store, is_demo=True, sleep_fn=_no_sleep, health_sink=events.append
    )

    event_names = {e["event"] for e in events}
    assert "universe_verified" in event_names
    assert "universe_activated" in event_names


def test_report_dataclass_defaults():
    report = PromotionReport()
    assert report.verified == []
    assert report.activated == []
    assert report.demoted == []
    assert report.quarantined == []
    assert report.confirmed_pricing == []
    assert report.unchanged == 0
