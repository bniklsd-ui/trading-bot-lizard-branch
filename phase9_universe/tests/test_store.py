"""Tests for ``UniverseStore`` (Phase 9 / V2 Step 1).

Applies migration 004's SQL directly against a temp SQLite file (no cross-phase
import of ``persistence`` — mirrors the plan's "in-memory SQLite + migration SQL
directly" test convention). ``import universe.*`` still pulls in no cross-phase
module at load time; only this test file reads the migration's ``.sql`` text via a
plain path, which is not a Python import.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from universe.exceptions import UniverseStoreError
from universe.models import (
    STATUS_ACTIVE,
    STATUS_DISCOVERED,
    STATUS_QUARANTINED,
    STATUS_VERIFIED,
    UniverseRecord,
)
from universe.store import UniverseStore, utc_iso_now

_MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "phase2_persistence" / "migrations"
# 004 creates instrument_universe; 006 (Phase 12, D5/D7) adds registry-truth columns to it
# plus paper_trades.resolution_source — 006's ALTER on paper_trades needs that table to
# already exist, hence 005 in between (creates it). Same incremental order as production.
_MIGRATION_004 = _MIGRATIONS_DIR / "004_phase9_instrument_universe.sql"
_MIGRATION_005 = _MIGRATIONS_DIR / "005_v3_learning.sql"
_MIGRATION_006 = _MIGRATIONS_DIR / "006_phase12_data_foundation.sql"


@pytest.fixture()
def store(tmp_path) -> UniverseStore:
    db_path = tmp_path / "universe_test.sqlite"
    bootstrap = sqlite3.connect(str(db_path))
    bootstrap.executescript(_MIGRATION_004.read_text(encoding="utf-8"))
    bootstrap.executescript(_MIGRATION_005.read_text(encoding="utf-8"))
    bootstrap.executescript(_MIGRATION_006.read_text(encoding="utf-8"))
    bootstrap.commit()
    bootstrap.close()
    s = UniverseStore(db_path)
    yield s
    s.close()


def _record(epic: str = "IX.D.DAX.IFMM.IP", **overrides) -> UniverseRecord:
    now = utc_iso_now()
    defaults = dict(
        epic=epic,
        name=None,
        yf_ticker="^GDAXI",
        volume_proxy="EXS1.DE",
        point_value=1.0,
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


def test_migration_creates_expected_table(store: UniverseStore):
    rows = store.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    assert "instrument_universe" in {r[0] for r in rows}


# -- UniverseRecord to_row/from_row round-trip -----------------------------


def test_record_round_trip_symmetry():
    rec = _record(checks={"ig_side": "PASS", "yf_side": "PASS"}, fail_count=2, data_degraded=True)
    row = rec.to_row()
    restored = UniverseRecord.from_row(row)
    assert restored == rec


def test_record_round_trip_empty_checks_stays_empty_dict():
    rec = _record(checks={})
    row = rec.to_row()
    assert row["checks_json"] is None
    restored = UniverseRecord.from_row(row)
    assert restored.checks == {}


def test_record_rejects_invalid_status():
    with pytest.raises(ValueError):
        _record(status="not_a_real_status")


def test_record_rejects_invalid_source():
    with pytest.raises(ValueError):
        _record(source="not_a_real_source")


# -- seed_curated -----------------------------------------------------------


def test_seed_curated_idempotent(store: UniverseStore):
    specs = [
        SimpleNamespace(
            epic="IX.D.DAX.IFMM.IP",
            yf_ticker="^GDAXI",
            volume_proxy="EXS1.DE",
            point_value=1.0,
            min_deal_size=0.5,
            currency="EUR",
        ),
        SimpleNamespace(
            epic="IX.D.STXE.IFM.IP",
            yf_ticker="^STOXX50E",
            volume_proxy="EXW1.DE",
            point_value=2.0,
            min_deal_size=0.5,
            currency="EUR",
        ),
    ]
    inserted_first = store.seed_curated(specs)
    assert inserted_first == 2

    inserted_second = store.seed_curated(specs)
    assert inserted_second == 0  # INSERT OR IGNORE — already-known epics are a no-op

    dax = store.get("IX.D.DAX.IFMM.IP")
    assert dax is not None
    assert dax.status == STATUS_ACTIVE
    assert dax.source == "curated"
    assert dax.point_value_source == "curated_confirmed"

    stxe = store.get("IX.D.STXE.IFM.IP")
    assert stxe is not None
    assert stxe.point_value_source is None  # not DAX -> must pass the Step-2 resolver


def test_seed_curated_four_instruments_exactly(store: UniverseStore):
    specs = [
        SimpleNamespace(
            epic=e, yf_ticker=None, volume_proxy=None, point_value=1.0,
            min_deal_size=0.5, currency="EUR",
        )
        for e in (
            "IX.D.DAX.IFMM.IP",
            "IX.D.STXE.IFM.IP",
            "IX.D.CAC.IFE.IP",
            "IX.D.IBEX.IFM.IP",
        )
    ]
    inserted = store.seed_curated(specs)
    assert inserted == 4
    assert len(store.active_universe()) == 4


# -- upsert_discovered / get --------------------------------------------------


def test_upsert_discovered_then_get(store: UniverseStore):
    rec = _record(epic="IX.D.NEW.IFM.IP")
    store.upsert_discovered(rec)
    fetched = store.get("IX.D.NEW.IFM.IP")
    assert fetched == rec


def test_upsert_discovered_overwrites_on_conflict(store: UniverseStore):
    rec = _record(epic="IX.D.NEW.IFM.IP", status=STATUS_DISCOVERED)
    store.upsert_discovered(rec)
    updated = _record(epic="IX.D.NEW.IFM.IP", status=STATUS_VERIFIED, point_value=2.0)
    store.upsert_discovered(updated)
    fetched = store.get("IX.D.NEW.IFM.IP")
    assert fetched.status == STATUS_VERIFIED
    assert fetched.point_value == 2.0


def test_get_missing_epic_returns_none(store: UniverseStore):
    assert store.get("IX.D.NOPE.IFM.IP") is None


# -- status roundtrip + fail_count increment ---------------------------------


def test_set_status_roundtrip(store: UniverseStore):
    rec = _record(epic="IX.D.NEW.IFM.IP", status=STATUS_DISCOVERED)
    store.upsert_discovered(rec)
    store.set_status("IX.D.NEW.IFM.IP", STATUS_VERIFIED, checks={"ig_side": "PASS"})
    fetched = store.get("IX.D.NEW.IFM.IP")
    assert fetched.status == STATUS_VERIFIED
    assert fetched.checks == {"ig_side": "PASS"}
    assert fetched.last_verified_at is not None


def test_set_status_fail_increment(store: UniverseStore):
    rec = _record(epic="IX.D.NEW.IFM.IP", status=STATUS_ACTIVE, fail_count=1)
    store.upsert_discovered(rec)
    store.set_status("IX.D.NEW.IFM.IP", STATUS_ACTIVE, fail_increment=True)
    assert store.get("IX.D.NEW.IFM.IP").fail_count == 2
    store.set_status("IX.D.NEW.IFM.IP", STATUS_QUARANTINED, fail_increment=True)
    assert store.get("IX.D.NEW.IFM.IP").fail_count == 3


def test_set_status_missing_epic_raises(store: UniverseStore):
    with pytest.raises(UniverseStoreError):
        store.set_status("IX.D.NOPE.IFM.IP", STATUS_VERIFIED)


def test_set_status_reset_fail_count(store: UniverseStore):
    rec = _record(epic="IX.D.NEW.IFM.IP", status=STATUS_ACTIVE, fail_count=2)
    store.upsert_discovered(rec)
    store.set_status("IX.D.NEW.IFM.IP", STATUS_ACTIVE, reset_fail_count=True)
    assert store.get("IX.D.NEW.IFM.IP").fail_count == 0


def test_set_status_data_degraded_set_and_clear(store: UniverseStore):
    rec = _record(epic="IX.D.NEW.IFM.IP", status=STATUS_ACTIVE, data_degraded=False)
    store.upsert_discovered(rec)
    store.set_status("IX.D.NEW.IFM.IP", STATUS_ACTIVE, data_degraded=True)
    assert store.get("IX.D.NEW.IFM.IP").data_degraded is True
    store.set_status("IX.D.NEW.IFM.IP", STATUS_ACTIVE, data_degraded=False)
    assert store.get("IX.D.NEW.IFM.IP").data_degraded is False


def test_set_status_default_kwargs_preserve_existing_fields(store: UniverseStore):
    rec = _record(epic="IX.D.NEW.IFM.IP", status=STATUS_ACTIVE, fail_count=2, data_degraded=True)
    store.upsert_discovered(rec)
    store.set_status("IX.D.NEW.IFM.IP", STATUS_ACTIVE)
    fetched = store.get("IX.D.NEW.IFM.IP")
    assert fetched.fail_count == 2
    assert fetched.data_degraded is True


def test_set_pricing(store: UniverseStore):
    rec = _record(epic="IX.D.NEW.IFM.IP", point_value=None, point_value_source=None)
    store.upsert_discovered(rec)
    store.set_pricing("IX.D.NEW.IFM.IP", 2.0, "name_lotsize_agree")
    fetched = store.get("IX.D.NEW.IFM.IP")
    assert fetched.point_value == 2.0
    assert fetched.point_value_source == "name_lotsize_agree"


def test_set_pricing_missing_epic_raises(store: UniverseStore):
    with pytest.raises(UniverseStoreError):
        store.set_pricing("IX.D.NOPE.IFM.IP", 1.0, "ig_fields")


# -- list_by_status / active_universe ordering -------------------------------


def test_list_by_status_filters_and_multi(store: UniverseStore):
    store.upsert_discovered(_record(epic="A", status=STATUS_DISCOVERED))
    store.upsert_discovered(_record(epic="B", status=STATUS_VERIFIED))
    store.upsert_discovered(_record(epic="C", status=STATUS_QUARANTINED))

    discovered = store.list_by_status(STATUS_DISCOVERED)
    assert [r.epic for r in discovered] == ["A"]

    multi = store.list_by_status(STATUS_DISCOVERED, STATUS_QUARANTINED)
    assert {r.epic for r in multi} == {"A", "C"}


def test_list_by_status_empty_args_returns_empty(store: UniverseStore):
    assert store.list_by_status() == []


def test_active_universe_deterministic_order(store: UniverseStore):
    now = utc_iso_now()
    store.upsert_discovered(_record(epic="Z", status=STATUS_ACTIVE, created_at=now, updated_at=now))
    store.upsert_discovered(_record(epic="A", status=STATUS_ACTIVE, created_at=now, updated_at=now))
    store.upsert_discovered(_record(epic="M", status=STATUS_DISCOVERED, created_at=now, updated_at=now))

    active = store.active_universe()
    assert [r.epic for r in active] == ["A", "Z"]  # same created_at -> epic tiebreak


# -- Phase 12: set_symbol / measurable_universe / conflict-preserve ---------


def test_set_symbol_writes_all_four_fields(store: UniverseStore):
    store.upsert_discovered(_record(epic="IX.D.NEW.IFM.IP", yf_ticker=None))
    store.set_symbol("IX.D.NEW.IFM.IP", "^GDAXI", symbol_source="resolver", status="ok")
    fetched = store.get("IX.D.NEW.IFM.IP")
    assert fetched.yf_ticker == "^GDAXI"
    assert fetched.data_source_status == "ok"
    assert fetched.symbol_source == "resolver"
    assert fetched.symbol_checked_at is not None


def test_set_symbol_missing_epic_raises(store: UniverseStore):
    with pytest.raises(UniverseStoreError):
        store.set_symbol("IX.D.NOPE.IFM.IP", "^GDAXI", symbol_source="resolver", status="ok")


def test_measurable_universe_filters_active_and_ok(store: UniverseStore):
    store.upsert_discovered(_record(epic="OK-ACTIVE", status=STATUS_ACTIVE))
    store.set_symbol("OK-ACTIVE", "^GDAXI", symbol_source="resolver", status="ok")
    store.upsert_discovered(_record(epic="UNVERIFIED-ACTIVE", status=STATUS_ACTIVE))
    store.upsert_discovered(_record(epic="OK-DISCOVERED", status=STATUS_DISCOVERED))
    store.set_symbol("OK-DISCOVERED", "^FCHI", symbol_source="resolver", status="ok")

    measurable = store.measurable_universe()
    assert [r.epic for r in measurable] == ["OK-ACTIVE"]


def test_measurable_universe_empty_when_nothing_verified(store: UniverseStore):
    store.upsert_discovered(_record(epic="A", status=STATUS_ACTIVE))
    assert store.measurable_universe() == []


def test_upsert_discovered_preserves_registry_truth_on_conflict(store: UniverseStore):
    """A re-discovery of an already-known epic must not clobber a verified symbol (D5) —
    upsert_discovered's default-record conflict branch excludes registry-truth columns."""
    store.upsert_discovered(_record(epic="IX.D.DAX.IFMM.IP", yf_ticker=None))
    store.set_symbol("IX.D.DAX.IFMM.IP", "^GDAXI", symbol_source="resolver", status="ok")

    # Simulate discovery re-touching the same epic with a fresh default-shaped record
    # (yf_ticker=None, data_source_status=DS_UNVERIFIED — today's actual discovery.py output).
    store.upsert_discovered(_record(epic="IX.D.DAX.IFMM.IP", yf_ticker=None, name="Germany 40"))

    fetched = store.get("IX.D.DAX.IFMM.IP")
    assert fetched.yf_ticker == "^GDAXI"
    assert fetched.data_source_status == "ok"
    assert fetched.symbol_source == "resolver"
    # non-preserved columns still update normally
    assert fetched.name == "Germany 40"


def test_to_instrument_spec_shape():
    rec = _record(epic="IX.D.DAX.IFMM.IP", status=STATUS_ACTIVE, source="curated")
    spec = rec.to_instrument_spec()
    assert spec == {
        "epic": "IX.D.DAX.IFMM.IP",
        "yf_ticker": "^GDAXI",
        "volume_proxy": "EXS1.DE",
        "point_value": 1.0,
        "min_deal_size": 0.5,
        "currency": "EUR",
        "source": "curated",
    }
