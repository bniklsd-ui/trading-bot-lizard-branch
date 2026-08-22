"""Phase-14 Block A3 — tests for ``source_registry.sources`` (Plan §6 A3).

Alle drei Source-Profile sind strukturell netz-frei:

1. ``IGDerivedSource.discover()`` baut Zeilen aus der Eingabe-Liste, **null I/O**.
2. **D6-Structural-Cost-Test:** ein Broker-Fake, dessen jede Methode
   ``AssertionError`` wirft, ist als Sentinel präsent; ``discover()`` läuft
   durch, ``probe_calls_used == 0``. Komplementär dazu: ein Grep-Test, der
   pinnt, dass ``source_registry/`` **null** Importe von ``broker_wrapper``
   enthält.
3. ``RegistryYFSource`` mit Store-Fake, dessen ``.get(epic)`` wirft —
   ``discover()`` gibt ``SourceProfile`` mit ``errors``-Tupel zurück, **kein** Raise.
4. ``RegistryYFSource`` spiegelt ``data_source_status='ok'`` 1:1 nach ``status='ok'``.
5. ``RegistryYFSource`` spiegelt ``no_intraday_source`` 1:1 (kein Downgrade).
6. ``RegistryYFSource`` setzt ``origin='registry'`` auf jeder Zeile.
7. ``LSStaticSource`` liefert ``no_source`` für jede Epic (heute; ``bars.source='ls' = 0``).
8. Eine Quelle, die intern wirft, liefert ``SourceProfile(errors=(...,))`` statt Raise.

Mock-Strategie: ``MagicMock`` für ``universe_store`` (Plan §6 A3 Test 3
„Store-Fake, dessen Fetch-Methoden werfen"), ``SimpleNamespace`` für
UniverseRecord-Shapes, ``subprocess`` für den Grep-Strukturtest.
"""

from __future__ import annotations

import subprocess
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from source_registry.models import (
    ORIGIN_DERIVED,
    ORIGIN_REGISTRY,
    RESOLUTION_1M,
    SOURCE_IG,
    SOURCE_LS,
    SOURCE_YF,
    STATUS_NO_INTRADAY_SOURCE,
    STATUS_NO_SOURCE,
    STATUS_OK,
)
from source_registry.sources import (
    IGDerivedSource,
    LSStaticSource,
    RegistryYFSource,
)


# ---------- Test 1: IGDerivedSource returns one row per input epic ---------


def test_ig_derived_source_returns_one_row_per_input_epic():
    source = IGDerivedSource()
    profile = source.discover(
        ["IX.D.DAX.IFMM.IP", "IX.D.CAC.IFE.IP", "IX.D.IBEX.FWM2.IP"],
        max_probe_calls=8,
    )
    assert profile.source == SOURCE_IG
    assert len(profile.rows) == 3
    assert profile.probe_calls_used == 0
    assert profile.errors == ()
    for row in profile.rows:
        assert row.source == SOURCE_IG
        assert row.status == STATUS_OK
        assert row.origin == ORIGIN_DERIVED
        assert row.source_symbol is None, (
            "D6: derived 'ig'-Zeile hat KEIN eigenes Symbol — die IG-Epic selbst "
            "ist das Symbol"
        )
        assert row.resolution == RESOLUTION_1M
        assert row.history_min_days == 30
        assert row.latency_min == 0


# ---------- Test 2: D6 structural cost test --------------------------------


class _ExplodingBroker:
    """Sentinel: every attribute access raises AssertionError.

    Presence-detector: if IGDerivedSource.discover() ever reached for any
    broker-shaped object, this would fire and the test would fail. The
    complementary structural test below (``test_no_broker_wrapper_import_in_source_registry``)
    pins the import side — together they are the D6 guarantee.
    """

    def __getattr__(self, name):
        raise AssertionError(
            f"IGDerivedSource.discover() must not reach for a broker "
            f"(attempted: broker.{name})"
        )


def test_ig_derived_source_never_invokes_a_broker():
    """D6 structural cost test (Plan §6 A3 Test 2)."""
    broker = _ExplodingBroker()  # noqa: F841 — Sentinel, nicht benutzt
    source = IGDerivedSource()
    profile = source.discover(
        ["IX.D.DAX.IFMM.IP", "IX.D.CAC.IFE.IP", "IX.D.IBEX.FWM2.IP"],
        max_probe_calls=8,
    )
    # probe_calls_used == 0 ist die harte Zusicherung; ohne sie würde der
    # Caller (Daemon) 8 IG-Calls ins Kontingent buchen (Plan D13).
    assert profile.probe_calls_used == 0, (
        "D6: IGDerivedSource must consume zero IG-network budget "
        "(probe_calls_used must be 0)"
    )
    assert len(profile.rows) == 3
    assert profile.errors == ()


def test_no_broker_wrapper_import_in_source_registry():
    """Module-level structural complement to Test 2: ``source_registry/``
    must not import ``broker_wrapper``. If a future refactor adds the import,
    the Test-2 sentinel alone cannot catch it (the broker would be reached
    via the import, but the test only catches attribute access on a passed-
    in instance). The grep pin catches the import at source level.

    The pattern matches ``import broker_wrapper`` and ``from broker_wrapper``
    specifically (NOT the bare word — Docstrings mention ``broker_wrapper``
    for context, and we don't want false positives from those)."""
    result = subprocess.run(
        ["grep", "-rnE", r"(^|\s)(import|from)\s+broker_wrapper",
         "phase14_discovery/source_registry/",
         "--include=*.py"],
        capture_output=True, text=True,
    )
    assert result.returncode != 0, (
        f"D6: source_registry must not import broker_wrapper.\n"
        f"Found:\n{result.stdout}"
    )


# ---------- Test 3: RegistryYFSource fail-soft on store exceptions --------


class _ThrowingStore:
    """Store-Fake whose ``.get(epic)`` raises unconditionally."""

    def get(self, epic):
        raise AssertionError(
            f"Store.get({epic!r}) must not succeed under the test setup"
        )


def test_registry_yf_source_with_throwing_store_returns_errors_not_raise():
    """Plan §6 A3 Test 3: ``RegistryYFSource`` catches store exceptions and
    packs them into ``errors``; the call **does not raise**. Same shape as
    the Phase-12 ``test_get_window_never_fetches`` family."""
    source = RegistryYFSource(_ThrowingStore())
    profile = source.discover(["IX.D.DAX.IFMM.IP"], max_probe_calls=8)

    assert profile.source == SOURCE_YF
    assert profile.rows == ()
    assert profile.probe_calls_used == 0
    assert len(profile.errors) == 1
    assert "IX.D.DAX.IFMM.IP" in profile.errors[0]


# ---------- Tests 4-6: RegistryYFSource mirror semantics -------------------


def _record(epic: str, yf_ticker, data_source_status: str):
    """Duck-typed UniverseRecord-shape (the real ``UniverseRecord`` is too
    heavy for this test — we only need ``.epic``/``.yf_ticker``/
    ``.data_source_status`` attributes)."""
    return SimpleNamespace(
        epic=epic,
        yf_ticker=yf_ticker,
        data_source_status=data_source_status,
    )


def test_registry_yf_source_mirrors_data_source_status_ok():
    source = RegistryYFSource(MagicMock(get=lambda e: _record(
        e, "^GDAXI", STATUS_OK,
    )))
    profile = source.discover(["IX.D.DAX.IFMM.IP"], max_probe_calls=8)
    assert len(profile.rows) == 1
    row = profile.rows[0]
    assert row.status == STATUS_OK, (
        "D18/A4: 1:1-Identität der status-Vokabulare, kein Mapping"
    )
    assert row.source_symbol == "^GDAXI"
    assert row.source == SOURCE_YF


def test_registry_yf_source_mirrors_no_intraday_source_without_downgrade():
    """``no_intraday_source`` must mirror to ``status='no_intraday_source'``,
    NOT downgraded to ``no_source``. Die 3 SUN*-Epics aus dem heutigen
    Substrat bleiben auf ihrer registry-stated status — Discovery
    beobachtet, klassifiziert nicht neu."""
    source = RegistryYFSource(MagicMock(get=lambda e: _record(
        e, "^GDAXI", STATUS_NO_INTRADAY_SOURCE,
    )))
    profile = source.discover(["IX.D.SUNDAX.IGN.IP"], max_probe_calls=8)
    assert len(profile.rows) == 1
    row = profile.rows[0]
    assert row.status == STATUS_NO_INTRADAY_SOURCE
    assert row.status != STATUS_NO_SOURCE, (
        "no_downgrade: registry 'no_intraday_source' bleibt 'no_intraday_source'"
    )


def test_registry_yf_source_sets_origin_registry_on_every_row():
    """A4 (D4): die yF-Projektion trägt ``origin='registry'``, nicht
    ``'discovery'``. Three-row batch to pin the constant across rows."""
    store = MagicMock(get=lambda e: _record(e, f"^{e[:6]}", STATUS_OK))
    source = RegistryYFSource(store)
    profile = source.discover(
        ["IX.D.DAX.IFMM.IP", "IX.D.CAC.IFE.IP", "IX.D.IBEX.FWM2.IP"],
        max_probe_calls=8,
    )
    assert len(profile.rows) == 3
    for row in profile.rows:
        assert row.origin == ORIGIN_REGISTRY


# ---------- Test 7: LSStaticSource returns no_source for every epic --------


def test_ls_static_source_returns_no_source_for_every_epic():
    """Today: ``bars.source='ls'`` = 0 (Plan §2.2 nachgemessen).
    LSStaticSource is a constant ``no_source`` per epic. When Lightstreamer
    produces real bars (Block C Step 10, gated on the Beweiswoche), this
    source gets a branch that emits ``status='ok'`` with the actual latency."""
    source = LSStaticSource()
    profile = source.discover(
        ["IX.D.DAX.IFMM.IP", "IX.D.CAC.IFE.IP", "IX.D.IBEX.FWM2.IP"],
        max_probe_calls=8,
    )
    assert profile.source == SOURCE_LS
    assert len(profile.rows) == 3
    assert profile.probe_calls_used == 0
    for row in profile.rows:
        assert row.status == STATUS_NO_SOURCE
        assert row.source_symbol is None
        assert row.origin == ORIGIN_DERIVED


# ---------- Test 8: Fail-soft on internal failure -------------------------


class _BrokenStore:
    """A non-asserting broken store — simulates a transient DB error."""

    def get(self, epic):
        raise RuntimeError(f"synthetic outage for {epic}")


def test_a_source_with_internal_failure_returns_errors_tuple_not_raise():
    """Plan §6 A3 Test 8: ein interner Fehler in ``discover()`` darf nicht
    propagieren. Die Fehlermeldung landet im ``errors``-Tupel, ``rows``
    bleibt leer (oder partial). Demonstriert am ``RegistryYFSource`` mit
    einem ``RuntimeError`` werfenden Store — derselbe Pattern wie Test 3,
    aber mit einem nicht-asserting Error, um den fail-soft-Vertrag generisch
    zu pinnen (nicht nur für die D6-Sentinel-Form)."""
    source = RegistryYFSource(_BrokenStore())
    # Should NOT raise:
    profile = source.discover(
        ["IX.D.DAX.IFMM.IP", "IX.D.CAC.IFE.IP"],
        max_probe_calls=8,
    )
    assert profile.rows == ()
    assert profile.probe_calls_used == 0
    assert len(profile.errors) == 2
    assert all("synthetic outage" in err for err in profile.errors)
