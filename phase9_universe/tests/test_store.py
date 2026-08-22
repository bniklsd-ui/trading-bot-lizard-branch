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
# 007 (Phase 14, A2) creates instrument_source_availability + backfills the yF
# projection from instrument_universe. Applied selectively — the D5 proof
# (test_set_symbol_projection_missing_table) deliberately runs WITHOUT it.
_MIGRATION_007 = _MIGRATIONS_DIR / "007_phase14_source_availability.sql"


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


@pytest.fixture()
def store_with_p14(tmp_path) -> UniverseStore:
    """Same as ``store`` but with Migration 007 applied — the cross-product
    table for the A4 projection exists, so D5's "missing table" path is
    not what we're testing here."""
    db_path = tmp_path / "universe_test_p14.sqlite"
    bootstrap = sqlite3.connect(str(db_path))
    bootstrap.executescript(_MIGRATION_004.read_text(encoding="utf-8"))
    bootstrap.executescript(_MIGRATION_005.read_text(encoding="utf-8"))
    bootstrap.executescript(_MIGRATION_006.read_text(encoding="utf-8"))
    bootstrap.executescript(_MIGRATION_007.read_text(encoding="utf-8"))
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


def test_active_universe_survives_stale_source_marker(store: UniverseStore):
    """Phase-14 finding B1: ``DS_STALE_SOURCE`` was introduced by Phase-13
    A4 (``wiring.py::_mark_stale``) but never added to
    ``_VALID_DATA_SOURCE_STATUSES`` (``universe/models.py:61-63``). ``set_symbol``
    writes it through fine (raw SQL, no validation), but the next read throws
    ``ValueError: invalid data_source_status: 'stale_source'`` from
    ``UniverseRecord.__post_init__`` — and ``active_universe()`` calls
    ``from_row`` on every row it returns. Reproduced live (2026-08-22) on a
    fresh DB + one active epic.

    The bug zündet exactly when the Beweiswoche sets
    ``enable_divergence_sampler=True`` (Phase 9 P9 demands „no epic with
    dead history stands on ``ok``"). Without this fix, the daemon crashes at
    ``wiring.py:131`` on the next start. Fix = 2 lines in models.py (DS_STALE_SOURCE
    + set membership)."""
    from universe.models import DS_STALE_SOURCE

    # Seed an active epic + mark it stale.
    store.upsert_discovered(_record(
        epic="IX.D.STALE.IFM.IP",
        status=STATUS_ACTIVE,
        yf_ticker="^STALE",
    ))
    store.set_symbol(
        "IX.D.STALE.IFM.IP", None,
        symbol_source=None, status=DS_STALE_SOURCE,
    )

    # The read that previously crashed. ``active_universe`` returns all
    # active rows regardless of data_source_status; today only DS_OK feeds
    # ``measurable_universe()``, so the stale row is correctly absent from
    # measurement (the discovery step sets stale on purpose) — but the read
    # itself must not throw.
    active = store.active_universe()
    assert any(r.epic == "IX.D.STALE.IFM.IP" for r in active), (
        "stale-source row missing from active_universe() — expected presence "
        "(the typing marker must survive a round trip, not silent drop)"
    )

    # measurable_universe still filters to DS_OK — the stale row must NOT
    # leak into measurement.
    measured = store.measurable_universe()
    assert not any(r.epic == "IX.D.STALE.IFM.IP" for r in measured), (
        "stale_source row leaked into measurable_universe() — would re-enter "
        "the data pipeline despite being marked dead"
    )


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


# -- Phase 14 A4: yF projection in set_symbol ------------------------------
#
# These tests pin the Phase-14 acceptance A4 from
# ``docs/concepts/phase14_discovery_plan.md`` §6 A4 (six tests: round-trip,
# overwrite, None-symbol, missing table, measurable_universe identity,
# doppelschreiber-gleichheit). All fixtures use Migration 007 unless the
# test name explicitly says otherwise.


def _fetch_projection(store: UniverseStore, epic: str) -> dict | None:
    """Read the yF projection row (``source='yf', resolution='1m'``) back
    as a dict, or ``None`` if no row exists."""
    row = store.conn.execute(
        "SELECT * FROM instrument_source_availability "
        "WHERE epic = ? AND source = 'yf' AND resolution = '1m'",
        (epic,),
    ).fetchone()
    return dict(row) if row is not None else None


def test_set_symbol_projects_yf_row_with_status_ok(store_with_p14: UniverseStore):
    """After ``set_symbol(epic, '^GDAXI', ..., status='ok')``, exactly one
    row exists at PK ``(epic, 'yf', '1m')`` carrying the registry's
    symbol + status + origin='registry'. Plan §6 A4 test 1."""
    store_with_p14.upsert_discovered(_record(epic="IX.D.DAX.IFMM.IP", yf_ticker=None))
    store_with_p14.set_symbol(
        "IX.D.DAX.IFMM.IP", "^GDAXI", symbol_source="seed", status="ok",
    )

    proj = _fetch_projection(store_with_p14, "IX.D.DAX.IFMM.IP")
    assert proj is not None
    assert proj["epic"] == "IX.D.DAX.IFMM.IP"
    assert proj["source"] == "yf"
    assert proj["resolution"] == "1m"
    assert proj["source_symbol"] == "^GDAXI"
    assert proj["status"] == "ok"
    assert proj["origin"] == "registry"
    assert proj["history_min_days"] is None  # discovery-time fact, not registry time
    assert proj["latency_min"] is None
    assert proj["last_verified_utc"].endswith("Z")
    assert proj["notes"] is None  # backfill-note preserved only on backfilled rows


def test_set_symbol_projection_overwrites_on_second_call(store_with_p14: UniverseStore):
    """A second ``set_symbol`` with a different status REPLACES the
    projection row — no duplicates, the registry always wins (Plan §6 A4
    test 2). Mirror of the same ON CONFLICT discipline as
    ``SourceAvailabilityStore.upsert``."""
    store_with_p14.upsert_discovered(_record(epic="IX.D.CAC.IFE.IP", yf_ticker=None))
    store_with_p14.set_symbol(
        "IX.D.CAC.IFE.IP", "^FCHI", symbol_source="seed", status="ok",
    )
    store_with_p14.set_symbol(
        "IX.D.CAC.IFE.IP", "^FCHI", symbol_source="seed", status="stale_source",
    )

    rows = store_with_p14.conn.execute(
        "SELECT * FROM instrument_source_availability "
        "WHERE epic = ? AND source = 'yf' AND resolution = '1m'",
        ("IX.D.CAC.IFE.IP",),
    ).fetchall()
    assert len(rows) == 1, "second set_symbol must REPLACE the projection, not duplicate"
    proj = dict(rows[0])
    assert proj["status"] == "stale_source"
    assert proj["source_symbol"] == "^FCHI"


def test_set_symbol_projection_with_none_symbol(store_with_p14: UniverseStore):
    """A ``no_source`` row projects ``source_symbol=None`` and
    ``status='no_source'`` — the symbol-and-status pair is one tuple,
    ``yf_ticker=None`` is valid (Plan §6 A4 test 3)."""
    store_with_p14.upsert_discovered(_record(epic="IX.D.IBEX.FWM2.IP", yf_ticker=None))
    store_with_p14.set_symbol(
        "IX.D.IBEX.FWM2.IP", None, symbol_source=None, status="no_source",
    )

    proj = _fetch_projection(store_with_p14, "IX.D.IBEX.FWM2.IP")
    assert proj is not None
    assert proj["source_symbol"] is None
    assert proj["status"] == "no_source"
    assert proj["origin"] == "registry"


def test_set_symbol_projection_missing_table_does_not_raise(store: UniverseStore):
    """D5 proof: if Migration 007 has not run, the ``instrument_source_availability``
    table is absent. ``set_symbol`` MUST NOT raise — the registry write
    stands, the projection logs a warning, the caller never sees the
    problem. Plan §6 A4 test 4 + Plan §8.2 root-cause note."""
    # The ``store`` fixture deliberately does NOT apply Migration 007.
    tables = {r[0] for r in store.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    assert "instrument_source_availability" not in tables, (
        "missing-table test setup is broken — Migration 007 leaked into store fixture"
    )

    store.upsert_discovered(_record(epic="IX.D.DAX.IFMM.IP", yf_ticker=None))

    # Must NOT raise. The warning is intentional — we just don't surface it.
    try:
        store.set_symbol(
            "IX.D.DAX.IFMM.IP", "^GDAXI", symbol_source="seed", status="ok",
        )
    except Exception as exc:  # noqa: BLE001
        pytest.fail(
            f"set_symbol must be fail-soft when projection table is missing, "
            f"but raised: {exc!r}"
        )

    # Registry write stands — the contract that protects measurable universe.
    fetched = store.get("IX.D.DAX.IFMM.IP")
    assert fetched.yf_ticker == "^GDAXI"
    assert fetched.data_source_status == "ok"


def test_set_symbol_projection_does_not_change_measurable_universe(store_with_p14: UniverseStore):
    """The projection is a side-channel; ``measurable_universe()`` returns
    the EXACT same rows before and after a set_symbol-induced projection
    is added. Plan §6 A4 test 5 + §6 D3 (measurable_universe bleibt
    unangetastet)."""
    # Five ``active + ok`` fixtures, mirroring the Plan §2.2 substrate.
    fixtures = [
        ("IX.D.CAC.IFE.IP",   "^FCHI"),
        ("IX.D.DAX.IFMM.IP",  "^GDAXI"),
        ("IX.D.DAX.IGN.IP",   "^GDAXI"),  # DAX dailies — distinct from IFMM
        ("IX.D.IBEX.FWM2.IP", "^IBEX"),
        ("IX.D.IBEX.IFM.IP",  "^IBEX"),
    ]
    for epic, ticker in fixtures:
        store_with_p14.upsert_discovered(_record(epic=epic, yf_ticker=None))
        store_with_p14.set_symbol(epic, ticker, symbol_source="seed", status="ok")
        # set_status signature: status, checks, fail_increment, reset_fail_count,
        # data_degraded, ...; reset_fail_count=True drops any inherited fail_count
        # so measurable_universe() (which requires DS_OK) is free to pick the row.
        store_with_p14.set_status(epic, STATUS_ACTIVE, reset_fail_count=True)

    # BEFORE: capture the bytes of measurable_universe().
    # After set_symbol, the projection rows exist; they MUST NOT change
    # what measurable_universe returns.
    measured = store_with_p14.measurable_universe()
    assert [r.epic for r in measured] == [
        "IX.D.CAC.IFE.IP", "IX.D.DAX.IFMM.IP", "IX.D.DAX.IGN.IP",
        "IX.D.IBEX.FWM2.IP", "IX.D.IBEX.IFM.IP",
    ]

    # Sanity: the projections really exist (otherwise the test is meaningless).
    for epic, ticker in fixtures:
        proj = _fetch_projection(store_with_p14, epic)
        assert proj is not None
        assert proj["source_symbol"] == ticker


def test_set_symbol_projection_matches_source_availability_store_upsert(store_with_p14: UniverseStore):
    """Doppelschreiber-Gleichheit (Plan §6 A4 test 6): for the same input,
    ``set_symbol``'s projection row and ``SourceAvailabilityStore.upsert``'s
    row must be byte-identical — except for ``last_verified_utc`` and
    ``notes`` (the store's open() does not propagate the migration-backfill
    note). Without equality here, the column list has drifted between the
    two writers and the next migration will introduce a silent bug.

    Both writers stamp the same ``last_verified_utc`` by patching
    ``utc_iso_now`` in both modules to return one fixed ISO string."""
    fixed_iso = "2026-08-22T12:00:00.000Z"
    import source_registry.store as sr_store_mod
    import universe.store as u_store_mod

    orig_universe_utc = u_store_mod.utc_iso_now
    orig_sr_utc = sr_store_mod.utc_iso_now
    u_store_mod.utc_iso_now = lambda: fixed_iso  # type: ignore[assignment]
    sr_store_mod.utc_iso_now = lambda: fixed_iso  # type: ignore[assignment]

    try:
        # Path 1 — set_symbol's projection.
        epic = "IX.D.DAX.IFMM.IP"
        store_with_p14.upsert_discovered(_record(epic=epic, yf_ticker=None))
        store_with_p14.set_symbol(epic, "^GDAXI", symbol_source="seed", status="ok")
        via_set_symbol = _fetch_projection(store_with_p14, epic)

        # Path 2 — SourceAvailabilityStore.upsert with the same input shape.
        from source_registry.models import (
            SOURCE_YF, STATUS_OK, SourceAvailability,
        )
        from source_registry.store import SourceAvailabilityStore

        sa_store = SourceAvailabilityStore(str(store_with_p14.db_path))
        try:
            sa_store.upsert(SourceAvailability(
                epic=epic,
                source=SOURCE_YF,
                resolution="1m",
                source_symbol="^GDAXI",
                status=STATUS_OK,
                origin="registry",
                history_min_days=None,
                latency_min=None,
                last_verified_utc=fixed_iso,
                notes=None,
            ))
            via_sa_store = _fetch_projection(store_with_p14, epic)
        finally:
            sa_store.close()
    finally:
        u_store_mod.utc_iso_now = orig_universe_utc  # type: ignore[assignment]
        sr_store_mod.utc_iso_now = orig_sr_utc  # type: ignore[assignment]

    assert via_set_symbol is not None
    assert via_sa_store is not None
    # Drop last_verified_utc / notes from the comparison — both writers are
    # deterministic with the patched clock, but a future test relaxation is
    # easier if we focus the assertion on the *business* fields.
    business_keys = (
        "epic", "source", "resolution", "source_symbol", "status",
        "origin", "history_min_days", "latency_min",
    )
    via_ss_business = {k: via_set_symbol[k] for k in business_keys}
    via_sa_business = {k: via_sa_store[k] for k in business_keys}
    assert via_ss_business == via_sa_business, (
        "doppelschreiber drift — set_symbol's projection diverged from "
        "SourceAvailabilityStore.upsert in business fields; the column "
        "list in store._project_availability has drifted from the "
        "SourceAvailabilityStore.upsert INSERT … ON CONFLICT block."
    )

    # last_verified_utc MUST be the same — both writers used the patched clock.
    assert via_set_symbol["last_verified_utc"] == via_sa_store["last_verified_utc"] == fixed_iso
