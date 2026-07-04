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

    def __post_init__(self) -> None:
        if self.status not in _VALID_STATUSES:
            raise ValueError(f"invalid status: {self.status!r}")
        if self.source not in _VALID_SOURCES:
            raise ValueError(f"invalid source: {self.source!r}")

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
