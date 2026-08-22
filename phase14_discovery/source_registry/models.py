"""Phase 14 (Discovery-Then-Deterministic) — data contracts for ``source_registry``.

Types only — no logic, no I/O, no AI. Mirrors the ``phase9_universe/universe/models.py``
convention (status/source-vokabular as module constants, ``dataclass(frozen=True)`` for
records, ``Protocol`` for pluggable sources).

The Phase-14 architecture splits the question "which source can serve epic X?" into three
parts (Plan §1):

1. **Discovery first** — each source exposes its own delivery spectrum as a
   :class:`SourceProfile`.
2. **Cross-product second** — :class:`SourceAvailability` is one row of
   ``instrument_source_availability`` (Migration 007), the IG-Epic × Source × Resolution
   cross-product.
3. **Determinism last** — the consumer reads the table through
   :class:`SourceAvailabilityStore` (``store.py``) and becomes simpler, not more complex.

Phase isolation (D3-Muster of ``UniverseStore``/``BarArchive``): the ``status`` and
``source`` vocabularies below are *deliberate duplicates* of the Phase-12 constants
in ``phase12_data_foundation/data_foundation/models.py``. A cross-phase import here
would either cycle the package graph or pull Phase-14 into Phase-12's load path
(the wrong direction); duplication is the cheap, structurally correct choice.
The two vocabularies are asserted identical in §5.1 / D18 — a future drift between
them is the next bug to fix at the shared point (this file + that one), not at any
caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


# ---------------------------------------------------------------------------
# Source vocabulary (mirror of Phase-12 KNOWN_SOURCES — see module docstring).
# ---------------------------------------------------------------------------

SOURCE_IG = "ig"
SOURCE_YF = "yf"
SOURCE_LS = "ls"
SOURCE_CAPITAL = "capital"  # Phase 13 §6 C1 (Session 12): S3 partial backfill source

# The bar-archive gatekeeper (Phase-12 D4, ``KNOWN_SOURCES`` in
# ``phase12_data_foundation/data_foundation/models.py:23-25``) is the authoritative
# list of what may be written into ``bars.source``. The availability TABLE does NOT
# enforce this membership — a source that lives here but not in ``KNOWN_SOURCES``
# is *discoverable*, never *insertable* into the archive (D17). Adding a new source
# is a deliberate two-step: register it here (Discovery can write it), THEN add it to
# ``KNOWN_SOURCES`` (the archive will accept it). One Source per row in both, or
# neither — never only the second.
REGISTRY_SOURCES: frozenset[str] = frozenset(
    {SOURCE_IG, SOURCE_YF, SOURCE_LS, SOURCE_CAPITAL}
)

# ---------------------------------------------------------------------------
# Status vocabulary (mirror of Phase-12 KNOWN_DATA_SOURCE_STATUSES — D18).
# ---------------------------------------------------------------------------

STATUS_OK = "ok"
STATUS_UNVERIFIED = "unverified"
STATUS_NO_SOURCE = "no_source"
STATUS_NO_INTRADAY_SOURCE = "no_intraday_source"
STATUS_MISMATCH = "mismatch"
STATUS_STALE_SOURCE = "stale_source"  # Phase 13 §6 A4: IG returned ok=True but `ts` too old

# The availability table's `status` column uses this exact vocabulary (D18). It is
# the same vocabulary as ``data_source_status`` in ``instrument_universe`` (Phase-12 D7),
# because the yF projection is a 1:1 copy (Plan §5.1) — not a translation.
KNOWN_AVAILABILITY_STATUSES: frozenset[str] = frozenset(
    {
        STATUS_OK, STATUS_UNVERIFIED, STATUS_NO_SOURCE,
        STATUS_NO_INTRADAY_SOURCE, STATUS_MISMATCH, STATUS_STALE_SOURCE,
    }
)


# ---------------------------------------------------------------------------
# Origin vocabulary (Module-level constants — see Plan §5.1 / §5.2 table).
# ---------------------------------------------------------------------------

ORIGIN_DISCOVERY = "discovery"  # a `Source.discover()` has populated this row
ORIGIN_REGISTRY = "registry"    # a projection from `instrument_universe` (A4, yF)
ORIGIN_DERIVED = "derived"      # derived from existing knowledge, no network (D6: 'ig')
ORIGIN_OPERATOR = "operator"    # set by hand

KNOWN_ORIGINS: frozenset[str] = frozenset(
    {ORIGIN_DISCOVERY, ORIGIN_REGISTRY, ORIGIN_DERIVED, ORIGIN_OPERATOR}
)


# ---------------------------------------------------------------------------
# Resolution vocabulary.
# ---------------------------------------------------------------------------

RESOLUTION_1M = "1m"
RESOLUTION_5M = "5m"
RESOLUTION_1H = "1h"
RESOLUTION_1D = "1d"

KNOWN_RESOLUTIONS: frozenset[str] = frozenset(
    {RESOLUTION_1M, RESOLUTION_5M, RESOLUTION_1H, RESOLUTION_1D}
)


# ---------------------------------------------------------------------------
# Records (dataclass, frozen — no setter surprises).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SourceAvailability:
    """One row of ``instrument_source_availability`` (Migration 007).

    PK is ``(epic, source, resolution)`` — a Source can serve an Epic at multiple
    resolutions (1m, 5m, 1h, 1d), each its own row. The dataclass itself does NOT
    enforce the PK (it can't, the PK is a tuple) — :class:`SourceAvailabilityStore.upsert`
    does, via ``INSERT … ON CONFLICT(epic, source, resolution) DO UPDATE``.

    ``status`` vocabulary is fixed (``KNOWN_AVAILABILITY_STATUSES``). ``origin`` is
    fixed (``KNOWN_ORIGINS``). ``source_symbol`` carries the source's own symbol —
    the column whose absence in the Concept schema made ``EPIC_MAP`` structurally
    irreplaceable (Plan §3.2, B2); today, ``instrument_universe.yf_ticker`` is exactly
    ``source_symbol WHERE source='yf'``.
    """

    epic: str
    source: str
    resolution: str
    source_symbol: str | None
    status: str
    origin: str
    history_min_days: int | None
    latency_min: int | None
    last_verified_utc: str
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.status not in KNOWN_AVAILABILITY_STATUSES:
            raise ValueError(f"invalid availability status: {self.status!r}")
        if self.origin not in KNOWN_ORIGINS:
            raise ValueError(f"invalid origin: {self.origin!r}")
        if self.resolution not in KNOWN_RESOLUTIONS:
            raise ValueError(f"invalid resolution: {self.resolution!r}")


@dataclass(frozen=True)
class SourceProfile:
    """What a source says about its own delivery spectrum — the result of one
    :meth:`Source.discover` run.

    Fail-soft by design: a single broken source does not kill the whole discovery
    cycle. The ``errors`` tuple carries per-row failure reasons (typically the
    upstream API returned 404 / no_symbol / network error); ``probe_calls_used`` is
    the run's Kontingent-Verbrauch that the daemon books into ``source_spend``
    (Plan D13, ``spend_kind='discovery'``).
    """

    source: str
    rows: tuple[SourceAvailability, ...]
    probe_calls_used: int = 0
    errors: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Protocol — the one contract every pluggable source implements (Plan §5.2).
# ---------------------------------------------------------------------------


class Source(Protocol):
    """One discoverable data source.

    Implementations:
    - ``IGDerivedSource``     — derives a row for each epic in ``epics`` from
                                the fact that *every* ``instrument_universe`` row IS
                                an IG epic (D6). Never touches the network. Probed
                                by the Test-2 acceptance (Plan §6 A3): a Broker-Fake
                                whose every method raises must not stop ``discover``.
    - ``LSStaticSource``      — reads ``bars.source='ls'`` cardinality, emits
                                ``no_source`` while empty. No network either.
    - ``RegistryYFSource``    — projects ``UniverseRecord`` rows from
                                ``instrument_universe`` into yF availability rows,
                                ``origin='registry'`` (D4).
    - ``CapitalSource.discover`` (Phase-14 B1b) — hits
                                ``GET /api/v1/markets?searchTerm=…`` once B1a's
                                response form has been observed by the operator.
    """

    def name(self) -> str:
        """Stable identifier — also the ``source`` column in the table."""
        ...

    def discover(
        self,
        epics: Sequence[str],
        *,
        max_probe_calls: int,
    ) -> SourceProfile:
        """What can this source serve for ``epics``? Caller passes the epic list
        (from ``instrument_universe``); source decides which it can answer.

        ``max_probe_calls`` is the hard Deckel for this run (Plan D14, default 8).
        The implementation must NOT exceed it; the daemon's ``SourceBudget`` books
        whatever the implementation reports in ``SourceProfile.probe_calls_used``
        against the existing ``source_spend`` ledger (D13).

        Implementations must be fail-soft: a network/API error on one epic → empty
        ``SourceAvailability`` + error string in ``SourceProfile.errors``. Never
        raise out of ``discover`` — that would kill the whole Discovery cycle on
        one bad row (Plan §8.5).
        """
        ...
