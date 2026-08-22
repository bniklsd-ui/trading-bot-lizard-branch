"""Phase 14 (Discovery-Then-Deterministic) — public surface of ``source_registry``.

The package exposes:

- Models (``models``): :class:`SourceAvailability`, :class:`SourceProfile`,
  :class:`Source` protocol, and the frozen ``REGISTRY_SOURCES`` /
  ``KNOWN_AVAILABILITY_STATUSES`` / ``KNOWN_ORIGINS`` / ``KNOWN_RESOLUTIONS``
  vocabularies. Plan §5.1.
- Store (``store``): :class:`SourceAvailabilityStore` — the *only* writer to
  ``instrument_source_availability`` (Migration 007). Plan §5.3.
- Sources (``sources``): the three source profiles that are net-free by
  construction (:class:`IGDerivedSource`, :class:`LSStaticSource`,
  :class:`RegistryYFSource`). The 4th ``Source`` (Capital.com) lives in
  Phase 13's ``backfill.py`` per the freigegebene Cross-Phase-Liste. Plan §5.2 / §6 A3.
- Arm-flag (``arm``): the file-based Discovery-armed switch. Plan §5.4 / §6 C1.
- Daemon (``run``): the standalone entrypoint (``python -m source_registry.run``).
  Plan §6 C2.

Vocabulary & data shape are deliberately duplicated against Phase 12's
``data_foundation.models`` (D18): the two never import each other, and a
future drift is fixed at *both* shared points. See ``models`` docstring.
"""

from __future__ import annotations

from source_registry.arm import (
    DEFAULT_ARM_PATH,
    arm,
    disarm,
    is_armed,
    read_state,
)
from source_registry.models import (
    KNOWN_AVAILABILITY_STATUSES,
    KNOWN_ORIGINS,
    KNOWN_RESOLUTIONS,
    ORIGIN_DERIVED,
    ORIGIN_DISCOVERY,
    ORIGIN_OPERATOR,
    ORIGIN_REGISTRY,
    REGISTRY_SOURCES,
    RESOLUTION_1D,
    RESOLUTION_1H,
    RESOLUTION_1M,
    RESOLUTION_5M,
    SOURCE_CAPITAL,
    SOURCE_IG,
    SOURCE_LS,
    SOURCE_YF,
    STATUS_MISMATCH,
    STATUS_NO_INTRADAY_SOURCE,
    STATUS_NO_SOURCE,
    STATUS_OK,
    STATUS_STALE_SOURCE,
    STATUS_UNVERIFIED,
    Source,
    SourceAvailability,
    SourceProfile,
)
from source_registry.sources import (
    IGDerivedSource,
    LSStaticSource,
    RegistryYFSource,
)
from source_registry.store import (
    SourceAvailabilityStore,
    utc_iso_now,
)

__all__ = [
    # arm
    "DEFAULT_ARM_PATH",
    "arm",
    "disarm",
    "is_armed",
    "read_state",
    # models — sources
    "REGISTRY_SOURCES",
    "SOURCE_CAPITAL",
    "SOURCE_IG",
    "SOURCE_LS",
    "SOURCE_YF",
    # models — statuses
    "KNOWN_AVAILABILITY_STATUSES",
    "STATUS_MISMATCH",
    "STATUS_NO_INTRADAY_SOURCE",
    "STATUS_NO_SOURCE",
    "STATUS_OK",
    "STATUS_STALE_SOURCE",
    "STATUS_UNVERIFIED",
    # models — origins
    "KNOWN_ORIGINS",
    "ORIGIN_DERIVED",
    "ORIGIN_DISCOVERY",
    "ORIGIN_OPERATOR",
    "ORIGIN_REGISTRY",
    # models — resolutions
    "KNOWN_RESOLUTIONS",
    "RESOLUTION_1D",
    "RESOLUTION_1H",
    "RESOLUTION_1M",
    "RESOLUTION_5M",
    # models — records & protocol
    "Source",
    "SourceAvailability",
    "SourceProfile",
    # sources
    "IGDerivedSource",
    "LSStaticSource",
    "RegistryYFSource",
    # store
    "SourceAvailabilityStore",
    "utc_iso_now",
]
