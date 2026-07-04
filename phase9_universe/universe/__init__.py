"""Phase 9 (V2 — Foundation) — universe package.

Autonomous instrument discovery -> verify -> promote pipeline. Replaces the
hand-curated ``EXTENDED_UNIVERSE`` tuple (``phase4_research/research/models.py``)
with a DB-backed, 100%-code-evaluated pipeline (Bauprinzip: no new AI anywhere in
this layer). Full design: ``../docs/concepts/phase9_v2_foundation_plan(1).md``.

Public exports grow per module (mirrors ``research``/``scheduler``/``reward``).
"""

from __future__ import annotations

from .exceptions import UniverseError, UniverseSafetyError, UniverseStoreError
from .models import (
    POINT_VALUE_SOURCE_CURATED_CONFIRMED,
    POINT_VALUE_SOURCE_IG_FIELDS,
    POINT_VALUE_SOURCE_NAME_LOTSIZE_AGREE,
    SOURCE_CURATED,
    SOURCE_RESEARCH_PROMOTED,
    STATUS_ACTIVE,
    STATUS_DISCOVERED,
    STATUS_QUARANTINED,
    STATUS_RETIRED,
    STATUS_VERIFIED,
    UniverseRecord,
)
from .pricing import confirm_curated, resolve_point_value
from .store import UniverseStore

__all__ = [
    "UniverseError",
    "UniverseSafetyError",
    "UniverseStoreError",
    "STATUS_DISCOVERED",
    "STATUS_VERIFIED",
    "STATUS_ACTIVE",
    "STATUS_QUARANTINED",
    "STATUS_RETIRED",
    "SOURCE_CURATED",
    "SOURCE_RESEARCH_PROMOTED",
    "POINT_VALUE_SOURCE_IG_FIELDS",
    "POINT_VALUE_SOURCE_NAME_LOTSIZE_AGREE",
    "POINT_VALUE_SOURCE_CURATED_CONFIRMED",
    "UniverseRecord",
    "UniverseStore",
    "resolve_point_value",
    "confirm_curated",
]
