"""Core value types for Phase 12 (Datenfundament): the ``Bar`` shape stored in the
archive, the source/status vocabularies (D5/D7/§4.1), and timestamp normalization.

``_iso_from_dt``/``normalize_bar_ts`` duplicate (not import) the ISO-8601-UTC-ms-Z
formatter from ``phase3_external_data.external_data.timeutil`` on purpose — same
phase-isolation reason Phase 3 itself documents for duplicating Phase 2's version
(D3: no cross-phase import at module top).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from data_foundation.exceptions import ArchiveError

# Known bar sources (D4 schema `bars.source`, CHECK-equivalent enforced in code —
# see BarArchive.insert_bars).
SOURCE_IG = "ig"
SOURCE_YF = "yf"
SOURCE_LS = "ls"
KNOWN_SOURCES: frozenset[str] = frozenset({SOURCE_IG, SOURCE_YF, SOURCE_LS})

# Registry `data_source_status` vocabulary (D7, Migration 006 default 'unverified').
DS_OK = "ok"
DS_UNVERIFIED = "unverified"
DS_NO_SOURCE = "no_source"
DS_NO_INTRADAY = "no_intraday_source"
DS_MISMATCH = "mismatch"
KNOWN_DATA_SOURCE_STATUSES: frozenset[str] = frozenset(
    {DS_OK, DS_UNVERIFIED, DS_NO_SOURCE, DS_NO_INTRADAY, DS_MISMATCH}
)


@dataclass(frozen=True)
class Bar:
    """One OHLCV bar as stored in ``BarArchive`` (D4 schema, §4.1).

    ``ts_utc``/``fetched_at`` are ISO 8601 UTC strings with millisecond precision
    and a ``Z`` suffix (repo-wide canonical format) — pass raw provider timestamps
    through :func:`normalize_bar_ts` first.
    """

    epic: str
    resolution: str
    ts_utc: str
    open: float
    high: float
    low: float
    close: float
    volume: float | None
    source: str
    fetched_at: str
    tick_count: int | None = None  # Phase 13 §6 A2/A5: filled by S1 (LS), null for yF/IG-REST


def _iso_from_dt(dt: datetime) -> str:
    """Format an aware/naive datetime as ISO 8601 UTC with ms precision + 'Z'.

    A naive datetime is treated as already-UTC (documented ceiling, §9.3 — IG's
    ``snapshotTime`` carries no explicit offset and has never been live-verified
    against a real DST boundary; upgrade this to a real TZ conversion if that
    ever turns out to matter for the archive's minute-level dedup).
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def normalize_bar_ts(raw: str) -> str:
    """Normalize a raw bar timestamp (any known source format) to ISO 8601 UTC
    with ms precision and a 'Z' suffix.

    Known input shapes:
      - IG classic ``"yyyy/MM/dd HH:mm:ss"`` (``get_ohlcv``'s ``snapshotTime``,
        §9.3-confirmed: not ISO, no explicit offset).
      - ISO with ``Z``/offset (already-normalized or ``snapshotTimeUTC``-style).
      - ISO without offset (yFinance-style naive local/UTC timestamps).

    Args:
        raw: the provider's raw timestamp string.

    Raises:
        ArchiveError: ``raw`` is empty or matches none of the known shapes.
    """
    raw = (raw or "").strip()
    if not raw:
        raise ArchiveError("empty bar timestamp")
    try:
        if "/" in raw:
            dt = datetime.strptime(raw, "%Y/%m/%d %H:%M:%S")
        else:
            normalized = raw.replace("Z", "+00:00") if raw.endswith("Z") else raw
            dt = datetime.fromisoformat(normalized)
    except ValueError as e:
        raise ArchiveError(f"unrecognized bar timestamp format: {raw!r}") from e
    return _iso_from_dt(dt)
