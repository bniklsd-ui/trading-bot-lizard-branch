"""Phase-14 Block A2 — tests for ``source_registry.store.SourceAvailabilityStore``.

All mocked: in-memory / tmp_path SQLite, no network, no live DB. The fixture
applies Migrations 004-006 to set up ``instrument_universe`` (the source the
yF-backfill in Migration 007 reads from) and Migration 007 to materialise
``instrument_source_availability``.

Test list (Plan §6 A2, 12 tests):

1. ensure/Migration legt die Tabelle an, ``PRAGMA table_info`` zeigt alle 10 Spalten
2. ``upsert`` schreibt, ``for_epic`` liest zurück (Round-Trip inkl. ``source_symbol=None``)
3. ``upsert`` derselben ``(epic, source, resolution)`` **überschreibt**, legt keine zweite Zeile an
4. ``upsert_many`` gibt die Zahl der berührten Zeilen zurück
5. ``for_source('capital', status='ok')`` filtert korrekt
6. ``for_epic(epic, resolution='1m')`` filtert korrekt
7. ``symbol_for`` liefert 'DE40' für die Capital-Zeile
8. ``symbol_for`` liefert ``None`` für eine unbekannte Kombination (**wirft nicht**)
9. ``stale_rows(ttl_days=7)`` liefert genau die Zeile mit altem ``last_verified_utc``
10. eine Zeile mit einem ``source``, der **nicht** in ``KNOWN_SOURCES`` steht, lässt
    sich schreiben und lesen (D17: die Tabelle gattet NICHT, der Archiv-Schreibpfad gattet)
11. **Identitätsprobe des Migrations-Backfills:** eine Fixture-DB mit den 22 Zeilen
    aus Plan §2.2 (5 active+ok, 3 active+no_intraday_source, 14 verified+unverified),
    Migration 007 anwenden ⇒ ``for_source('yf', status='ok')`` liefert **genau** die
    fünf Epics aus §2.2, und die drei SUN*-Epics stehen auf no_intraday_source.
12. Migration 007 zweimal anwenden ist ein No-Op (``INSERT OR IGNORE``, keine Duplikate)
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from source_registry.models import (
    ORIGIN_REGISTRY,
    RESOLUTION_1M,
    SOURCE_CAPITAL,
    SOURCE_IG,
    SOURCE_LS,
    SOURCE_YF,
    STATUS_NO_INTRADAY_SOURCE,
    STATUS_OK,
    SourceAvailability,
)
from source_registry.store import SourceAvailabilityStore, _shift_days, utc_iso_now

_MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "phase2_persistence" / "migrations"
_MIGRATION_004 = _MIGRATIONS_DIR / "004_phase9_instrument_universe.sql"
_MIGRATION_005 = _MIGRATIONS_DIR / "005_v3_learning.sql"
_MIGRATION_006 = _MIGRATIONS_DIR / "006_phase12_data_foundation.sql"
_MIGRATION_007 = _MIGRATIONS_DIR / "007_phase14_source_availability.sql"


@pytest.fixture()
def db_path(tmp_path) -> Path:
    """A tmp_path SQLite that has migrations 004/005/006/007 applied.

    Migration 007's yF-backfill INSERT … SELECT reads from instrument_universe,
    so 004 must be there (creates the table). 005/006 add the relevant columns
    (data_source_status in 006). 007 then adds instrument_source_availability
    AND backfills it from whatever instrument_universe rows exist (none, in
    this fresh fixture — backfill-tested in test 11 with a populated fixture).
    """
    path = tmp_path / "registry_test.sqlite"
    bootstrap = sqlite3.connect(str(path))
    bootstrap.executescript(_MIGRATION_004.read_text(encoding="utf-8"))
    bootstrap.executescript(_MIGRATION_005.read_text(encoding="utf-8"))
    bootstrap.executescript(_MIGRATION_006.read_text(encoding="utf-8"))
    bootstrap.executescript(_MIGRATION_007.read_text(encoding="utf-8"))
    bootstrap.commit()
    bootstrap.close()
    return path


@pytest.fixture()
def store(db_path) -> SourceAvailabilityStore:
    s = SourceAvailabilityStore(db_path)
    yield s
    s.close()


def _availability(**overrides) -> SourceAvailability:
    """A valid ``(IX.D.DAX.IFMM.IP, capital, 1m)`` row with optional overrides."""
    defaults = dict(
        epic="IX.D.DAX.IFMM.IP",
        source=SOURCE_CAPITAL,
        resolution=RESOLUTION_1M,
        source_symbol="DE40",
        status=STATUS_OK,
        origin="operator",
        history_min_days=30,
        latency_min=1,
        last_verified_utc="2026-08-22T12:00:00.000Z",
        notes="seeded by test",
    )
    defaults.update(overrides)
    return SourceAvailability(**defaults)


# ---------- Test 1: Migration applies, all 10 columns present --------------


def test_migration_007_creates_table_with_all_ten_columns(db_path):
    """The Migration 007 file creates ``instrument_source_availability`` with
    exactly the 10 columns of Plan §5.1 (epic, source, resolution, source_symbol,
    status, origin, history_min_days, latency_min, last_verified_utc, notes) and
    PK (epic, source, resolution) — the order matters for `SELECT *` round-trips
    via ``sqlite3.Row``."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cols = [r["name"] for r in conn.execute(
        "PRAGMA table_info(instrument_source_availability)"
    ).fetchall()]
    assert cols == [
        "epic", "source", "resolution", "source_symbol", "status", "origin",
        "history_min_days", "latency_min", "last_verified_utc", "notes",
    ]
    # The PK is declared inline in the CREATE TABLE (``PRIMARY KEY (epic,
    # source, resolution)`` at the end of the column list), which is how
    # SQLite encodes it — the PK info lives in `table_info.pk` (column
    # `pk` is 1-based; non-PK columns have pk=0). ``PRAGMA primary_key_list``
    # is empty for this layout. Mirrors the convention used by
    # ``UniverseStore``'s `instrument_universe` PK check.
    pk_cols = [r["name"] for r in conn.execute(
        "PRAGMA table_info(instrument_source_availability)"
    ).fetchall() if r["pk"] > 0]
    assert pk_cols == ["epic", "source", "resolution"]

    # The source-status composite index from the migration.
    indexes = {r["name"] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index'"
    ).fetchall()}
    assert "idx_isa_source_status" in indexes
    conn.close()


# ---------- Test 2: upsert / for_epic round-trip (incl. source_symbol=None) -


def test_upsert_then_for_epic_round_trip_including_null_symbol(store):
    """Writing then reading yields a structurally identical row — including
    the ``source_symbol=None`` case (D6: the derived 'ig' row has no source
    symbol of its own — it IS the IG epic)."""
    # Two rows: one with a source_symbol, one without.
    store.upsert(_availability(source=SOURCE_CAPITAL, source_symbol="DE40"))
    store.upsert(_availability(source=SOURCE_IG, source_symbol=None))

    rows = store.for_epic("IX.D.DAX.IFMM.IP")
    by_source = {r.source: r for r in rows}
    assert set(by_source) == {SOURCE_CAPITAL, SOURCE_IG}
    assert by_source[SOURCE_CAPITAL].source_symbol == "DE40"
    assert by_source[SOURCE_IG].source_symbol is None
    # Round-trip integrity of the rest of the row.
    for r in rows:
        assert r.epic == "IX.D.DAX.IFMM.IP"
        assert r.resolution == RESOLUTION_1M
        assert r.status == STATUS_OK


# ---------- Test 3: upsert on the same PK overwrites, no second row -------


def test_upsert_is_idempotent_on_pk(store):
    """Two ``upsert`` calls with the same ``(epic, source, resolution)`` PK
    leave exactly one row — the second overwrites the first. Same ON CONFLICT
    shape as ``UniverseStore.upsert_discovered`` (``universe/store.py:130-137``)."""
    store.upsert(_availability(source_symbol="DE40"))
    store.upsert(_availability(source_symbol="FR40", notes="second write"))
    rows = store.for_epic("IX.D.DAX.IFMM.IP", resolution=RESOLUTION_1M)
    assert len(rows) == 1
    assert rows[0].source_symbol == "FR40"
    assert rows[0].notes == "second write"


# ---------- Test 4: upsert_many returns the count of rows passed ----------


def test_upsert_many_returns_count_of_rows(store):
    n = store.upsert_many([
        _availability(epic="IX.D.AEX.IFM.IP", source=SOURCE_CAPITAL),
        _availability(epic="IX.D.MIB.MFM.IP", source=SOURCE_CAPITAL),
        _availability(epic="IX.D.IBEX.FWM2.IP", source=SOURCE_CAPITAL),
    ])
    assert n == 3
    assert len(store.for_source(SOURCE_CAPITAL)) == 3


# ---------- Test 5: for_source('capital', status='ok') filters correctly ---


def test_for_source_with_status_filter(store):
    """``for_source('capital', status='ok')`` returns only the OK rows for
    that source — the Discovery daemon's primary query path (Plan §6 A2)."""
    store.upsert_many([
        _availability(epic="IX.D.AEX.IFM.IP", status=STATUS_OK),
        _availability(epic="IX.D.MIB.MFM.IP", status=STATUS_OK),
        _availability(
            epic="IX.D.IBEX.FWM2.IP",
            status=STATUS_NO_INTRADAY_SOURCE,
            source_symbol=None,
        ),
    ])

    only_ok = store.for_source(SOURCE_CAPITAL, status=STATUS_OK)
    assert {r.epic for r in only_ok} == {"IX.D.AEX.IFM.IP", "IX.D.MIB.MFM.IP"}

    # Without the status filter, all three come back (in epic order).
    all_capital = store.for_source(SOURCE_CAPITAL)
    assert {r.epic for r in all_capital} == {
        "IX.D.AEX.IFM.IP", "IX.D.MIB.MFM.IP", "IX.D.IBEX.FWM2.IP",
    }


# ---------- Test 6: for_epic(epic, resolution='1m') filters correctly ------


def test_for_epic_with_resolution_filter(store):
    """The same epic at multiple resolutions = multiple rows; the resolution
    filter narrows to the one the consumer asks for."""
    store.upsert_many([
        _availability(source=SOURCE_CAPITAL, resolution=RESOLUTION_1M),
        _availability(source=SOURCE_CAPITAL, resolution="5m", source_symbol="DE40"),
        _availability(source=SOURCE_YF, resolution=RESOLUTION_1M, source_symbol="^GDAXI"),
    ])

    only_1m = store.for_epic("IX.D.DAX.IFMM.IP", resolution=RESOLUTION_1M)
    assert len(only_1m) == 2
    assert all(r.resolution == RESOLUTION_1M for r in only_1m)
    assert {r.source for r in only_1m} == {SOURCE_CAPITAL, SOURCE_YF}


# ---------- Test 7: symbol_for returns the source's own symbol ------------


def test_symbol_for_returns_source_specific_symbol(store):
    """The Capital row carries 'DE40' as its source_symbol — that is the
    value that replaces ``EPIC_MAP.get(epic)`` in ``live_data/backfill.py:180``
    after Phase-14 B2."""
    store.upsert(_availability(source=SOURCE_CAPITAL, source_symbol="DE40"))
    assert store.symbol_for("IX.D.DAX.IFMM.IP", SOURCE_CAPITAL) == "DE40"


# ---------- Test 8: symbol_for returns None on unknown combinations -------


def test_symbol_for_returns_none_on_unknown_combination(store):
    """``symbol_for`` returns ``None`` (does NOT raise) when no row matches —
    the contract Phase-14 B2's ``run_capital_backfill`` will rely on:
    "no row in the registry" reads as "this source does not serve this epic",
    fall-back-to-Path-C is the consumer's decision."""
    assert store.symbol_for("IX.D.NEVER.SEEN.IP", SOURCE_CAPITAL) is None
    # Known epic, unknown source → also None (the table is the truth).
    store.upsert(_availability(source=SOURCE_CAPITAL))
    assert store.symbol_for("IX.D.DAX.IFMM.IP", SOURCE_LS) is None
    # Default resolution is '1m' (Plan §5.3 contract).
    assert store.symbol_for("IX.D.DAX.IFMM.IP", SOURCE_CAPITAL) == "DE40"


# ---------- Test 9: stale_rows(ttl_days=7) picks the right rows -----------


def test_stale_rows_filters_by_ttl(store):
    """Only rows older than ``now_utc - ttl_days`` come back; the fresh row
    does NOT. Comparison is lexicographic over ISO strings — sound because
    every timestamp in the column comes from the same ``utc_iso_now``
    formatter (Plan §6 A2 implementation hint)."""
    store.upsert_many([
        # Fresh — written today, well within the 7-day window.
        _availability(
            epic="IX.D.FRESH.IP",
            last_verified_utc="2026-08-22T10:00:00.000Z",
        ),
        # Old — 30 days back, must come back as stale.
        _availability(
            epic="IX.D.OLD.IP",
            source=SOURCE_LS,
            source_symbol=None,
            last_verified_utc="2026-07-23T10:00:00.000Z",
        ),
    ])

    stale = store.stale_rows(ttl_days=7, now_utc="2026-08-22T12:00:00.000Z")
    assert {r.epic for r in stale} == {"IX.D.OLD.IP"}
    # Lexicographic ordering of the column is preserved by the SQL ORDER BY.
    assert stale[0].epic == "IX.D.OLD.IP"


# ---------- Test 10: a source outside KNOWN_SOURCES is allowed (D17) -----


def test_table_does_not_gate_source_membership(store):
    """D17: the AVAILABILITY table does NOT enforce ``KNOWN_SOURCES`` — a
    source that lives here but not in the bars-side ``KNOWN_SOURCES`` may be
    DISCOVERED. The gatekeeper is ``BarArchive.insert_bars`` on the WRITE side,
    not the registry. Adding a new source = DB-row + (later) one-line edit
    to ``KNOWN_SOURCES``."""
    store.upsert(_availability(source="dukas_copy", source_symbol="DE40",
                                status=STATUS_OK, origin="operator"))
    rows = store.for_source("dukas_copy")
    assert len(rows) == 1
    assert rows[0].source == "dukas_copy"


# ---------- Test 11: Migration backfill reproduces today's substrate ------


def test_migration_007_backfill_reproduces_todays_substrate(db_path, store):
    """Plan §2.2 (Live-DB-Substrat, gemessen 2026-08-22):
    ``instrument_universe`` hat 22 Zeilen — 5 active+ok, 3 active+no_intraday_source,
    14 verified+unverified. Nach Migration 007 muss ``for_source('yf', status='ok')``
    **genau** die 5 active+ok-Epics liefern, und die 3 SUN*-Epics müssen auf
    ``no_intraday_source`` stehen.

    Migration 007's INSERT … SELECT is the *only* way these rows come into
    being for the SUN* epics — ``SymbolResolver.resolve_epic`` ruft
    ``set_symbol`` in 6 von 8 Pfaden nicht (Phase-14 Plan §5.1). This test is
    the proof: backfill's identity claim (B2, source_symbol ≡ yf_ticker)
    holds before any new code can introduce drift."""
    # Re-open with the bootstrap conn (the fixture's closed one) to insert
    # the 22 rows. After insert, re-apply 007 to trigger the backfill — but
    # the fixture already applied 007 to an empty universe, so the backfill
    # has nothing to find. We need to seed the universe *before* 007.
    # Easiest path: rebuild the fixture inline, applying 004-006, seeding 22
    # rows, then applying 007.
    fresh = db_path.parent / "backfill_test.sqlite"
    if fresh.exists():
        fresh.unlink()

    bootstrap = sqlite3.connect(str(fresh))
    bootstrap.row_factory = sqlite3.Row
    bootstrap.executescript(_MIGRATION_004.read_text(encoding="utf-8"))
    bootstrap.executescript(_MIGRATION_005.read_text(encoding="utf-8"))
    bootstrap.executescript(_MIGRATION_006.read_text(encoding="utf-8"))

    # Seed the 22 rows (Plan §2.2 inventory).
    rows_to_seed = [
        # 5 active + ok
        ("IX.D.CAC.IFE.IP",   "active",     "ok",                  "^FCHI"),
        ("IX.D.DAX.IFMM.IP",  "active",     "ok",                  "^GDAXI"),
        ("IX.D.DAX.IGN.IP",   "active",     "ok",                  "^GDAXI"),
        ("IX.D.IBEX.FWM2.IP", "active",     "ok",                  "^IBEX"),
        ("IX.D.IBEX.IFM.IP",  "active",     "ok",                  "^IBEX"),
        # 3 active + no_intraday_source
        ("IX.D.SUNDAX.IGN.IP", "active",    "no_intraday_source",  "^GDAXI"),
        ("IX.D.SUNDOW.IAE.IP", "active",    "no_intraday_source",  "^DJI"),
        ("IX.D.SUNNAS.IAE.IP", "active",    "no_intraday_source",  "^IXIC"),
        # 14 verified + unverified (some yf_ticker set, some NULL — the backfill
        # carries the value verbatim, so a NULL stays a NULL source_symbol).
        ("IX.D.AEX.IFM.IP",   "verified",   "unverified",  None),
        ("IX.D.AEX.MFM.IP",   "verified",   "unverified",  None),
        ("IX.D.AEX.MFS.IP",   "verified",   "unverified",  None),
        ("IX.D.MIB.MFM.IP",   "verified",   "unverified",  None),
        ("IX.D.MIB.MFS.IP",   "verified",   "unverified",  None),
        ("IX.D.IBEX.FWM3.IP", "verified",   "unverified",  None),
        ("IX.D.IBEX.FWM4.IP", "verified",   "unverified",  None),
        ("IX.D.DOW.IFE.IP",   "verified",   "unverified",  "^DJI"),
        ("IX.D.FTSE.IFE.IP",  "verified",   "unverified",  "^FTSE"),
        ("IX.D.NASDAQ.IFE.IP", "verified",  "unverified",  "^IXIC"),
        ("IX.D.SPTRD.IFE.IP", "verified",   "unverified",  "^SPX"),
        ("IX.D.STXE.IFE.IP",  "verified",   "unverified",  "^STOXX50E"),
        ("IX.D.SUNDAX.IFMM.IP", "verified", "unverified", "^GDAXI"),
        ("IX.D.SUNFUN.IFE.IP", "verified",   "unverified", None),
    ]
    now = "2026-08-22T12:00:00.000Z"
    for epic, status, dss, yf_ticker in rows_to_seed:
        bootstrap.execute(
            "INSERT INTO instrument_universe "
            "(epic, currency, status, source, yf_ticker, data_source_status, "
            " created_at, updated_at) "
            "VALUES (?, 'EUR', ?, 'research_promoted', ?, ?, ?, ?)",
            (epic, status, yf_ticker, dss, now, now),
        )
    bootstrap.commit()

    # NOW apply 007 — backfill reads from the seeded universe.
    bootstrap.executescript(_MIGRATION_007.read_text(encoding="utf-8"))
    bootstrap.commit()
    bootstrap.close()

    s = SourceAvailabilityStore(fresh)

    # The hard part of the acceptance: exactly the 5 active+ok Epics come
    # back from for_source('yf', status='ok').
    yf_ok = {r.epic for r in s.for_source(SOURCE_YF, status=STATUS_OK)}
    assert yf_ok == {
        "IX.D.CAC.IFE.IP", "IX.D.DAX.IFMM.IP", "IX.D.DAX.IGN.IP",
        "IX.D.IBEX.FWM2.IP", "IX.D.IBEX.IFM.IP",
    }

    # The 3 SUN* epics stand on no_intraday_source — exactly the substrate.
    sun_epics = s.for_epic("IX.D.SUNDAX.IGN.IP") + s.for_epic("IX.D.SUNDOW.IAE.IP") + s.for_epic("IX.D.SUNNAS.IAE.IP")
    assert all(r.status == STATUS_NO_INTRADAY_SOURCE for r in sun_epics)
    assert all(r.source == SOURCE_YF for r in sun_epics)
    assert all(r.origin == ORIGIN_REGISTRY for r in sun_epics)

    # The total yF rows = all 22 instrument_universe rows (one backfill row each).
    all_yf = s.for_source(SOURCE_YF)
    assert len(all_yf) == 22

    # B2 identity: source_symbol for a yF row == yf_ticker from instrument_universe.
    # Pick a row we know the yf_ticker for.
    dax = next(r for r in all_yf if r.epic == "IX.D.DAX.IFMM.IP")
    assert dax.source_symbol == "^GDAXI"

    # A NULL yf_ticker must project as NULL source_symbol — backfill must
    # NOT fill in a fake default.
    aex = next(r for r in all_yf if r.epic == "IX.D.AEX.IFM.IP")
    assert aex.source_symbol is None

    s.close()


# ---------- Test 12: re-applying Migration 007 is a No-Op ----------------


def test_migration_007_is_idempotent(db_path):
    """Migration 007's ``CREATE TABLE IF NOT EXISTS`` + ``INSERT OR IGNORE``
    means a second apply leaves the schema and the row set untouched. Same
    idempotency contract as 001-006 (Phase-2 migrations.py docstring)."""
    backfill_path = db_path.parent / "idempotent_test.sqlite"
    if backfill_path.exists():
        backfill_path.unlink()
    bootstrap = sqlite3.connect(str(backfill_path))
    bootstrap.row_factory = sqlite3.Row
    bootstrap.executescript(_MIGRATION_004.read_text(encoding="utf-8"))
    bootstrap.executescript(_MIGRATION_005.read_text(encoding="utf-8"))
    bootstrap.executescript(_MIGRATION_006.read_text(encoding="utf-8"))

    # Seed exactly one row.
    bootstrap.execute(
        "INSERT INTO instrument_universe "
        "(epic, currency, status, source, yf_ticker, data_source_status, "
        " created_at, updated_at) "
        "VALUES ('IX.D.DAX.IFMM.IP', 'EUR', 'active', 'research_promoted', "
        "        '^GDAXI', 'ok', '2026-08-22T12:00:00.000Z', '2026-08-22T12:00:00.000Z')"
    )
    bootstrap.commit()

    # First apply: table + 1 backfill row.
    bootstrap.executescript(_MIGRATION_007.read_text(encoding="utf-8"))
    bootstrap.commit()
    count_after_first = bootstrap.execute(
        "SELECT COUNT(*) FROM instrument_source_availability"
    ).fetchone()[0]

    # Second apply: must NOT add rows (INSERT OR IGNORE on (epic, source, resolution) PK).
    bootstrap.executescript(_MIGRATION_007.read_text(encoding="utf-8"))
    bootstrap.commit()
    count_after_second = bootstrap.execute(
        "SELECT COUNT(*) FROM instrument_source_availability"
    ).fetchone()[0]
    assert count_after_first == count_after_second == 1
    bootstrap.close()


# ---------- Doppelschreiber-Schnittstelle: timestamp formatter contract ---


def test_utc_iso_now_format_matches_shift_days_contract():
    """The lexicographic ordering of stale_rows depends on every timestamp in
    the column coming from the same formatter. Pin the format: ISO 8601 UTC,
    ms precision, Z suffix — same shape as Phase-9/Phase-12."""
    s = utc_iso_now()
    # Shape: YYYY-MM-DDTHH:MM:SS.mmmZ
    assert len(s) == 24
    assert s[4] == "-" and s[7] == "-" and s[10] == "T" and s[23] == "Z"
    # Round-trip through shift_days yields another valid stamp.
    shifted = _shift_days(s, -3)
    parsed = datetime.strptime(shifted, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    assert abs((datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc) - parsed).days) == 3
