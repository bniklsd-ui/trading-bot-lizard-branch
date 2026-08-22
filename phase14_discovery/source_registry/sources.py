"""Phase 14 — drei Source-Profile (Plan §6 A3).

Alle drei sind **ohne Netz** — das ist die strukturelle Kostenzusicherung
für D6 (kein IG-/prices-Call, kein IG-search_markets, kein Capital.com-
Fetch, kein yFinance-Fetch). Die IG-Zeile wird abgeleitet, die yF-Zeile
wird aus `instrument_universe` projiziert, die LS-Zeile ist statisch
(`bars.source='ls'` = 0 heute).

Konstanten für die History-/Latency-Heuristik (yF ≈ 15 min hinter dem
Markt, IG-LS echtzeit, Capital.com ≈ 1 min wenn aktiv) sind hier als
Modul-Konstanten definiert. Sie fließen in `latency_min` und
`history_min_days` der Availability-Zeilen ein — Phase-15-Consumer
können sie als Selektions-Heuristik lesen.
"""

from __future__ import annotations

from typing import Iterable

from source_registry.models import (
    Source,
    SourceAvailability,
    SourceProfile,
    ORIGIN_DERIVED,
    ORIGIN_REGISTRY,
    RESOLUTION_1M,
    SOURCE_IG,
    SOURCE_LS,
    SOURCE_YF,
    STATUS_NO_SOURCE,
    STATUS_OK,
)
from source_registry.store import utc_iso_now


# History-/Latency-Heuristik (Plan §6 A3 + Phase-12-Beobachtung).
# Heuristik, nicht Vertrag — der Konsument darf die Werte lesen, sich
# aber nicht darauf verlassen, dass sie exakt der Realität entsprechen.
_IG_LATENCY_MIN = 0
_YF_LATENCY_MIN = 15
_LS_LATENCY_MIN = 0

_IG_HISTORY_MIN_DAYS = 30
_YF_HISTORY_MIN_DAYS = 7


class IGDerivedSource:
    """D6: jede `instrument_universe`-Zeile *ist* per Definition eine
    IG-Epic. Diese Source leitet daraus eine Availability-Zeile pro
    übergebener Epic ab — **null Netz-Calls**, **null Kontingent-Verbrauch**.

    Der strukturelle Kostentest (Plan §6 A3 Test 2): ein Broker-Fake,
    dessen jede Methode `AssertionError` wirft, ist als Sentinel
    anwesend; `discover()` läuft trotzdem durch und `probe_calls_used == 0`.
    Der komplementäre Source-Code-Test (``test_sources.py::test_no_broker_wrapper_import_*``)
    pinnt strukturell, dass diese Klasse `broker_wrapper` nicht importiert.
    """

    def name(self) -> str:
        return SOURCE_IG

    def discover(
        self,
        epics: Iterable[str],
        *,
        max_probe_calls: int,
    ) -> SourceProfile:
        now = utc_iso_now()
        rows = tuple(
            SourceAvailability(
                epic=epic,
                source=SOURCE_IG,
                resolution=RESOLUTION_1M,
                source_symbol=None,  # D6: die IG-Epic IST das eigene Symbol
                status=STATUS_OK,
                origin=ORIGIN_DERIVED,
                history_min_days=_IG_HISTORY_MIN_DAYS,
                latency_min=_IG_LATENCY_MIN,
                last_verified_utc=now,
            )
            for epic in epics
        )
        # max_probe_calls wird respektiert (nie überschritten — D6
        # verbietet IG-Calls, daher gibt es nichts zu zählen). Die
        # Caller-Seite (Daemon in Block C) bekommt `probe_calls_used == 0`
        # und bucht entsprechend 0 in `source_spend` (D13).
        return SourceProfile(
            source=SOURCE_IG,
            rows=rows,
            probe_calls_used=0,
            errors=(),
        )


class LSStaticSource:
    """Solange ``bars.source='ls'`` = 0 ist (heute, Plan §2.2 nachgemessen),
    liefert diese Source eine ``no_source``-Zeile pro Epic. Statisches
    Profil — kein DB-Lookup, keine I/O.

    Wenn der Lightstreamer echte Bars liefert (Block C Step 10, gated auf
    die Beweiswoche — Plan §6 C-Block-C), bekommt diese Source einen
    ``bars.source='ls' > 0``-Check und emittiert dann ``status='ok'`` mit
    der gemessenen Latenz. Bis dahin: statisch.
    """

    def name(self) -> str:
        return SOURCE_LS

    def discover(
        self,
        epics: Iterable[str],
        *,
        max_probe_calls: int,
    ) -> SourceProfile:
        now = utc_iso_now()
        rows = tuple(
            SourceAvailability(
                epic=epic,
                source=SOURCE_LS,
                resolution=RESOLUTION_1M,
                source_symbol=None,  # LS nutzt die IG-Epic direkt
                status=STATUS_NO_SOURCE,
                origin=ORIGIN_DERIVED,
                history_min_days=None,  # irrelevant solange status=no_source
                latency_min=_LS_LATENCY_MIN,
                last_verified_utc=now,
            )
            for epic in epics
        )
        return SourceProfile(
            source=SOURCE_LS,
            rows=rows,
            probe_calls_used=0,
            errors=(),
        )


class RegistryYFSource:
    """Spiegelt ``instrument_universe`` → ``instrument_source_availability``
    für ``source='yf'``.

    Komplementär zur A4-yF-Projektion in ``UniverseStore.set_symbol``: die
    Migration-007-Backfill setzt den Grundbestand einmalig, A4 hält ihn bei
    jedem ``set_symbol``-Call aktuell, und diese Source ist der explizite
    **Full-Refresh-Pfad** für den Discovery-Daemon (Block C). Bei einem
    epochalen Refresh iteriert der Daemon über die aktiven Epics und ruft
    für jede ``discover`` auf; das Resultat wird via
    ``SourceAvailabilityStore.upsert_many`` in die Tabelle geschrieben.

    Konstruktor nimmt einen ``universe_store``-Duck-Shape: er braucht nur
    ``.get(epic) → UniverseRecord-ähnlich oder None``. (Falls die
    Refresh-Schleife anders herum will — alle Universe-Zeilen auf einmal —
    ruft der Daemon einfach ``store.list_by_status(...)`` und reicht die
    Epics weiter. Diese Klasse bleibt schmal.)

    Fail-soft per §8.5: ein internes Versagen (DB-Wackler, ein kaputter
    Store-Proxy) landet im ``errors``-Tupel, **nicht** als Raise.
    """

    def __init__(self, universe_store) -> None:
        self._store = universe_store

    def name(self) -> str:
        return SOURCE_YF

    def discover(
        self,
        epics: Iterable[str],
        *,
        max_probe_calls: int,
    ) -> SourceProfile:
        now = utc_iso_now()
        rows: list[SourceAvailability] = []
        errors: list[str] = []
        for epic in epics:
            try:
                rec = self._store.get(epic)
            except Exception as exc:
                # Fail-soft: ein kaputter Store-Wert kippt nicht den ganzen
                # Discovery-Cycle. §8.5 — „one bad row must not kill the
                # whole Discovery cycle".
                errors.append(f"{epic}: {exc}")
                continue
            if rec is None:
                # Epic nicht in der Universe — überspringen. Der Daemon
                # fragt hier nur aktive Epics an; wenn die Registry leer
                # ist, wurde die Epic wahrscheinlich zurückgezogen, das
                # ist nicht unser Problem.
                continue
            rows.append(
                SourceAvailability(
                    epic=rec.epic,
                    source=SOURCE_YF,
                    resolution=RESOLUTION_1M,
                    source_symbol=rec.yf_ticker,
                    # D18 + A4: 1:1-Identität der status-Vokabulare. Kein
                    # Downgrade — `no_intraday_source` bleibt
                    # `no_intraday_source`, `unverified` bleibt `unverified`.
                    status=rec.data_source_status,
                    origin=ORIGIN_REGISTRY,
                    history_min_days=_YF_HISTORY_MIN_DAYS,
                    latency_min=_YF_LATENCY_MIN,
                    last_verified_utc=now,
                )
            )
        return SourceProfile(
            source=SOURCE_YF,
            rows=tuple(rows),
            probe_calls_used=0,
            errors=tuple(errors),
        )


# Re-export the Protocol-side names so callers don't need a separate
# ``from source_registry.models import Source`` (defensive: not every
# implementation needs to subclass a common base, but the names should
# be reachable from one place).
__all__ = [
    "IGDerivedSource",
    "LSStaticSource",
    "RegistryYFSource",
    "Source",  # re-export
]
