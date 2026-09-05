"""Tests for the Phase 16 B3 weekend-market filter (Plan §6 B3 + §7 AK9).

Covers:

1. ``is_weekend_market`` — pure function with 5 cases (``.SUN`` Epic, German name,
   English name, ``None`` name, normal DAX negative).
2. ``discovery._passes_code_filter`` — the discovery sweep bumps ``filtered[weekend_market]``
   on a hit with a weekend name.
3. ``promotion.run_promotion_cycle`` Step 3 — actively demotes any ``IX.D.SUN*`` row that
   slipped into ``STATUS_ACTIVE`` in a previous run (live-DB state at 2026-09-05: 3 active
   ``SUN*`` rows, Plan §3 L5).
4. ``promotion.run_promotion_cycle`` Step 2 — never activates a verified weekend market,
   even when the active-universe cap is not full.

No network, no LLM, no broker — fixtures mirror the patterns in
``test_discovery.py`` and ``test_promotion.py``.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from universe.discovery import discover
from universe.models import (
    STATUS_ACTIVE,
    STATUS_DISCOVERED,
    STATUS_QUARANTINED,
    STATUS_VERIFIED,
    UniverseRecord,
    is_weekend_market,
)
from universe.promotion import run_promotion_cycle
from universe.store import UniverseStore, utc_iso_now

_MIGRATIONS_DIR = (
    Path(__file__).resolve().parents[2] / "phase2_persistence" / "migrations"
)
_MIGRATION_004 = _MIGRATIONS_DIR / "004_phase9_instrument_universe.sql"
_MIGRATION_005 = _MIGRATIONS_DIR / "005_v3_learning.sql"
_MIGRATION_006 = _MIGRATIONS_DIR / "006_phase12_data_foundation.sql"


@pytest.fixture()
def store(tmp_path) -> UniverseStore:
    db_path = tmp_path / "weekend_test.sqlite"
    bootstrap = sqlite3.connect(str(db_path))
    bootstrap.executescript(_MIGRATION_004.read_text(encoding="utf-8"))
    bootstrap.executescript(_MIGRATION_005.read_text(encoding="utf-8"))
    bootstrap.executescript(_MIGRATION_006.read_text(encoding="utf-8"))
    bootstrap.commit()
    bootstrap.close()
    s = UniverseStore(db_path)
    yield s
    s.close()


def _env(ok: bool, data: dict | None = None) -> SimpleNamespace:
    return SimpleNamespace(ok=ok, data=data or {}, error=None if ok else {"message": "boom"})


def _market_info(
    *, name: str = "Deutschland 40 Kassa (1€)", instrument_type: str = "INDICES",
    currency: str = "EUR", min_deal_size: float = 0.5, lot_size: float = 1.0,
    market_status: str = "TRADEABLE",
) -> SimpleNamespace:
    return _env(
        True,
        {
            "name": name,
            "instrument_type": instrument_type,
            "currency": currency,
            "min_deal_size": min_deal_size,
            "lot_size": lot_size,
            "market_status": market_status,
        },
    )


class _FakeBroker:
    """Duck-typed broker for ``discover`` (search_markets + get_market_info)."""

    def __init__(self, search_results: dict, market_infos: dict) -> None:
        self.search_results = search_results
        self.market_infos = market_infos

    def search_markets(self, term: str):
        return _env(True, {"results": self.search_results.get(term, [])})

    def get_market_info(self, epic: str):
        return self.market_infos.get(epic, _env(False))


def _recording_sleep() -> tuple:
    calls: list[float] = []

    def sleep_fn(s: float) -> None:
        calls.append(s)

    return sleep_fn, calls


# -- is_weekend_market: 5 cases (Plan §6 B3) ----------------------------------


def test_is_weekend_market_matches_dot_sun_epic() -> None:
    """The structural Epic pattern is the primary signal."""
    assert is_weekend_market("IX.D.SUNDAX.IGN.IP", "Some Weekday Name") is True


def test_is_weekend_market_matches_german_name_marker() -> None:
    """Belt-and-braces: German IG name 'Wochenend-...' also trips it."""
    assert is_weekend_market("IX.D.SOMETHING.IFM.IP", "Wochenend-Wall Street Kassa (1€)") is True


def test_is_weekend_market_matches_english_name_marker() -> None:
    """English IG variant: 'Weekend ...' name also trips it (future-proof)."""
    assert is_weekend_market("IX.D.SOMETHING.IFM.IP", "Weekend UK 100") is True


def test_is_weekend_market_tolerates_none_name() -> None:
    """None name on either side must not crash; the other side still evaluates."""
    assert is_weekend_market("IX.D.SUNDAX.IGN.IP", None) is True
    assert is_weekend_market(None, "Wochenend-Deutschland 40") is True


def test_is_weekend_market_does_not_match_normal_epic() -> None:
    """Negative: a normal weekday DAX must NOT be filtered."""
    assert is_weekend_market("IX.D.DAX.IFMM.IP", "Deutschland 40 Kassa (1€)") is False


# -- Discovery: weekend market filtered out ----------------------------------


def test_discover_filters_weekend_market(store: UniverseStore) -> None:
    """A hit carrying the 'Wochenend-' name marker must be bumped as ``weekend_market``.

    Mirrors the structure of ``test_filter_currency_not_eur`` in ``test_discovery.py``.
    """
    broker = _FakeBroker(
        search_results={
            "Wall Street": [
                {"epic": "IX.D.SUNDOW.IAE.IP"},
            ]
        },
        market_infos={
            "IX.D.SUNDOW.IAE.IP": _market_info(name="Wochenend-Wall Street-Kassa (1€)"),
        },
    )
    sleep_fn, _ = _recording_sleep()
    report = discover(
        broker, store, search_terms=("Wall Street",), sleep_fn=sleep_fn
    )

    assert report.new == []
    assert report.filtered == {"weekend_market": 1}


# -- Promotion Step 3: active weekend epic is demoted -------------------------


def test_promotion_demotes_active_weekend_epic(store: UniverseStore) -> None:
    """A weekend epic already in ``active`` (live-DB shape at 2026-09-05) gets demoted
    to ``quarantined`` on the next cycle, with ``reason='weekend_market'`` recorded.
    """
    epic = "IX.D.SUNDAX.IGN.IP"
    now = utc_iso_now()
    # Seed an active weekend row, exactly like the live-DB state pre-B3.
    rec = UniverseRecord(
        epic=epic,
        name="Wochenend-Deutschland 40 (1€)",
        currency="EUR",
        status=STATUS_ACTIVE,
        source="curated",
        created_at=now,
        updated_at=now,
        point_value=1.0,
        point_value_source="ig_fields",
        fail_count=0,
    )
    store.upsert_discovered(rec)

    broker = SimpleNamespace(get_market_info=lambda e: _env(True, {}))
    fetcher = SimpleNamespace(
        get_history=lambda *a, **kw: [1, 2, 3],
        get_bars=lambda *a, **kw: [1, 2, 3],
        get_volume_anomaly=lambda *a, **kw: SimpleNamespace(volume_available=True),
    )
    events: list[dict] = []
    report = run_promotion_cycle(
        broker, fetcher, store, is_demo=True,
        sleep_fn=lambda s: None,
        health_sink=events.append,
    )

    assert epic in report.demoted
    assert any(ev.get("event") == "universe_demote" and ev.get("reason") == "weekend_market"
               for ev in events)
    rec_after = store.get(epic)
    assert rec_after.status == STATUS_QUARANTINED
    assert rec_after.checks.get("reason") == "weekend_market"


# -- Promotion Step 2: verified weekend epic is never activated ---------------


def test_promotion_never_activates_weekend_epic(store: UniverseStore) -> None:
    """Step 2 must ``continue`` past a verified weekend epic without activating it,
    even when the active-universe cap is far from full.
    """
    epic = "IX.D.SUNDOW.IAE.IP"
    # Seed a verified weekend row (would normally auto-activate under Step 2).
    rec = UniverseRecord(
        epic=epic,
        name="Wochenend-Wall Street Kassa (1€)",
        currency="EUR",
        status=STATUS_VERIFIED,
        source="research_promoted",
        created_at=utc_iso_now(),
        updated_at=utc_iso_now(),
        point_value=1.0,
        point_value_source="ig_fields",
    )
    store.upsert_discovered(rec)

    broker = SimpleNamespace(get_market_info=lambda e: _env(True, {}))
    fetcher = SimpleNamespace(
        get_history=lambda *a, **kw: [1, 2, 3],
        get_bars=lambda *a, **kw: [1, 2, 3],
        get_volume_anomaly=lambda *a, **kw: SimpleNamespace(volume_available=True),
    )
    report = run_promotion_cycle(
        broker, fetcher, store, is_demo=True, sleep_fn=lambda s: None
    )

    assert epic not in report.activated
    assert report.activated == []
    rec_after = store.get(epic)
    assert rec_after.status == STATUS_VERIFIED  # untouched
