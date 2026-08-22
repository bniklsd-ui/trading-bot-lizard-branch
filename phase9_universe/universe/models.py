"""Data contracts for the Phase 9 (V2) instrument-universe pipeline.

Types only — no logic, no I/O, no AI (mirrors the Phase-4/7/8 ``models.py``
convention). :class:`UniverseRecord` is the row shape of the ``instrument_universe``
table (migration 004); :class:`UniverseStore` (``store.py``) is the only thing that
reads/writes it.

Status vocabulary (module constants, mirrors the ``REASON_*`` pattern in
``phase8_scheduler/scheduler/research_tick.py``):

    discovered -> verified -> active
                      |           |
                      v           v (IG-side fail x N)
                 quarantined <----+
                      |
                      v (never reached by v1 promotion cycle)
                  retired

``PASS`` verification without a resolved ``point_value`` leaves a record at
``discovered`` (no progress, no error — Decision D6: no proof, no activation). An
IG-side health failure on an ``active`` record increments ``fail_count`` toward
demotion; a yFinance-side failure only sets ``data_degraded`` and never demotes
(Konzept C3 — reduced-signal is tolerated).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

STATUS_DISCOVERED = "discovered"
STATUS_VERIFIED = "verified"
STATUS_ACTIVE = "active"
STATUS_QUARANTINED = "quarantined"
STATUS_RETIRED = "retired"

_VALID_STATUSES = frozenset(
    {STATUS_DISCOVERED, STATUS_VERIFIED, STATUS_ACTIVE, STATUS_QUARANTINED, STATUS_RETIRED}
)

SOURCE_CURATED = "curated"
SOURCE_RESEARCH_PROMOTED = "research_promoted"

_VALID_SOURCES = frozenset({SOURCE_CURATED, SOURCE_RESEARCH_PROMOTED})

# point_value_source vocabulary (pricing.py, Step 2)
POINT_VALUE_SOURCE_IG_FIELDS = "ig_fields"
POINT_VALUE_SOURCE_NAME_LOTSIZE_AGREE = "name_lotsize_agree"
POINT_VALUE_SOURCE_CURATED_CONFIRMED = "curated_confirmed"

# data_source_status vocabulary (Phase 12 / Decision D7, migration 006). Measurement
# (paper/shadow) is gated on DS_OK via UniverseStore.measurable_universe(); every other
# value is a typed, loud reason it is excluded — never a silent None.
DS_OK = "ok"
DS_UNVERIFIED = "unverified"
DS_NO_SOURCE = "no_source"
DS_NO_INTRADAY_SOURCE = "no_intraday_source"
DS_MISMATCH = "mismatch"
# Phase 13 §6 A4 (F1): IG lieferte ok=True auf tote Historie — geschrieben von
# wiring.py::_mark_stale. Ohne diese Konstante wirft UniverseRecord.__post_init__
# beim LESEN ValueError, sobald die Beweiswoche enable_divergence_sampler=True setzt
# (Phase-14-Plan §3.1 reproduziert: ValueError invalid data_source_status: 'stale_source').
DS_STALE_SOURCE = "stale_source"

_VALID_DATA_SOURCE_STATUSES = frozenset(
    {DS_OK, DS_UNVERIFIED, DS_NO_SOURCE, DS_NO_INTRADAY_SOURCE, DS_MISMATCH, DS_STALE_SOURCE}
)

# symbol_source vocabulary (Phase 12 / Decision D5-D6) — who last set yf_ticker.
SYMBOL_SOURCE_SEED = "seed"
SYMBOL_SOURCE_RESOLVER = "resolver"
SYMBOL_SOURCE_OPERATOR = "operator"

_VALID_SYMBOL_SOURCES = frozenset(
    {SYMBOL_SOURCE_SEED, SYMBOL_SOURCE_RESOLVER, SYMBOL_SOURCE_OPERATOR}
)


@dataclass(frozen=True)
class UniverseRecord:
    """One row of ``instrument_universe`` (migration 004).

    ``checks`` is the deserialized form of the DB's ``checks_json`` TEXT column
    (the last verify-instrument verdict) — always a ``dict``, defaulting to ``{}``
    when the column is ``NULL`` or empty (a fresh ``discovered`` row has never been
    verified yet).
    """

    epic: str
    currency: str
    status: str
    source: str
    created_at: str
    updated_at: str
    name: str | None = None
    yf_ticker: str | None = None
    volume_proxy: str | None = None
    point_value: float | None = None
    point_value_source: str | None = None
    min_deal_size: float | None = None
    checks: dict[str, Any] = field(default_factory=dict)
    fail_count: int = 0
    data_degraded: bool = False
    last_verified_at: str | None = None
    data_source_status: str = DS_UNVERIFIED
    symbol_source: str | None = None
    symbol_checked_at: str | None = None

    def __post_init__(self) -> None:
        if self.status not in _VALID_STATUSES:
            raise ValueError(f"invalid status: {self.status!r}")
        if self.source not in _VALID_SOURCES:
            raise ValueError(f"invalid source: {self.source!r}")
        if self.data_source_status not in _VALID_DATA_SOURCE_STATUSES:
            raise ValueError(f"invalid data_source_status: {self.data_source_status!r}")
        if self.symbol_source is not None and self.symbol_source not in _VALID_SYMBOL_SOURCES:
            raise ValueError(f"invalid symbol_source: {self.symbol_source!r}")

    def to_row(self) -> dict[str, Any]:
        """Return the DB-column-shaped dict (``checks`` -> JSON text, bool -> int)."""
        return {
            "epic": self.epic,
            "name": self.name,
            "yf_ticker": self.yf_ticker,
            "volume_proxy": self.volume_proxy,
            "point_value": self.point_value,
            "point_value_source": self.point_value_source,
            "min_deal_size": self.min_deal_size,
            "currency": self.currency,
            "status": self.status,
            "source": self.source,
            "checks_json": json.dumps(self.checks) if self.checks else None,
            "fail_count": self.fail_count,
            "data_degraded": 1 if self.data_degraded else 0,
            "last_verified_at": self.last_verified_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "data_source_status": self.data_source_status,
            "symbol_source": self.symbol_source,
            "symbol_checked_at": self.symbol_checked_at,
        }

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "UniverseRecord":
        """Build a record from a DB row dict (``sqlite3.Row`` cast to ``dict``)."""
        checks_json = row.get("checks_json")
        checks = json.loads(checks_json) if checks_json else {}
        return cls(
            epic=row["epic"],
            name=row.get("name"),
            yf_ticker=row.get("yf_ticker"),
            volume_proxy=row.get("volume_proxy"),
            point_value=row.get("point_value"),
            point_value_source=row.get("point_value_source"),
            min_deal_size=row.get("min_deal_size"),
            currency=row["currency"],
            status=row["status"],
            source=row["source"],
            checks=checks,
            fail_count=int(row.get("fail_count") or 0),
            data_degraded=bool(row.get("data_degraded") or 0),
            last_verified_at=row.get("last_verified_at"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            data_source_status=row.get("data_source_status") or DS_UNVERIFIED,
            symbol_source=row.get("symbol_source"),
            symbol_checked_at=row.get("symbol_checked_at"),
        )

    def to_instrument_spec(self) -> dict[str, Any]:
        """Return an ``InstrumentSpec``-shaped plain dict (Phase 4's constructor kwargs).

        Deliberately a plain dict, not a ``research.InstrumentSpec`` import — Phase 4
        builds its own typed value from this (phase isolation, per the plan §8). Only
        meaningful for ``STATUS_ACTIVE`` records with a resolved ``point_value``; the
        caller (Phase 4/8 wiring, Step 5) is responsible for that filtering via
        :meth:`UniverseStore.active_universe`.
        """
        return {
            "epic": self.epic,
            "yf_ticker": self.yf_ticker,
            "volume_proxy": self.volume_proxy,
            "point_value": self.point_value,
            "min_deal_size": self.min_deal_size,
            "currency": self.currency,
            "source": self.source,
        }
