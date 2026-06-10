"""Write-ahead idempotency store for the Phase-5 order path (concept §2).

Decision E (concept §0) demands the bot's own ``deal_reference`` be persisted
**before** ``open_position`` is ever invoked, and reconciled on every startup, so
a crash between "I'm about to place this order" and "the broker confirmed it"
never leads to a blind second order. Neither ``StateManager`` nor ``Database``
(read-only here; outcome writing is Phase 7) has a contract for *in-flight* order
state, so Phase 5 owns one small operational JSON file:
``data/state/execution_state.json``.

This file holds **operational** state only — in-flight / open references and the
fields needed to reconcile them. It is **not** a learning/outcome store (that is
Phase 7's SQLite). Records move through a small lifecycle:

    PENDING  -> recorded write-ahead, before open_position
    OPEN     -> broker confirmed (deal_id known)
    CLOSED   -> position gone (broker SL/TP, time-stop, or reconcile)

That record-level ``status`` is deliberately **distinct** from the
``ExecutionResult.status`` vocabulary in :mod:`execution.models` (OPEN /
CLOSED_BY_BROKER / TIME_STOP / NO_TRADE / …) — this is the persisted order
lifecycle, not the cycle outcome.

Writes are atomic (temp file + ``os.replace``), mirroring the verified Phase-2
``persistence.state`` convention — a crash mid-write never leaves a half-written
file. A corrupt file fails loud (``ExecutionError``); it is **never** silently
overwritten. Phase-isolated: stdlib + :mod:`execution.models` /
:mod:`execution.exceptions` only.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from execution.exceptions import ExecutionError
from execution.models import OrderPlan

# Record lifecycle states (see module docstring). Kept distinct from
# ExecutionResult.status on purpose.
PENDING = "PENDING"
OPEN = "OPEN"
CLOSED = "CLOSED"

# A reference is "open" (and so a reconcile input) until it is closed.
_OPEN_STATES = (PENDING, OPEN)


def _utcnow() -> datetime:
    """Current UTC time. Indirected so tests can monkeypatch the clock."""
    return datetime.now(timezone.utc)


def _format_iso(dt: datetime) -> str:
    """Format a datetime as ISO 8601 UTC with ms precision and Z suffix."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


class ExecutionState:
    """Persistent record of in-flight / open order references (one JSON file).

    Keyed by ``deal_reference`` (``bot-<uuid4hex>``, unique per plan). The file is
    created lazily on the first write; until then reads return an empty store.
    """

    def __init__(self, path: str = "data/state/execution_state.json") -> None:
        """Remember ``path`` and ensure its parent directory exists."""
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    # -- internal helpers ---------------------------------------------------

    def _read(self) -> dict[str, dict[str, Any]]:
        """Return the ``records`` map, or ``{}`` if the file has never been written.

        A present-but-corrupt file raises ``ExecutionError`` — we fail loud rather
        than silently discard in-flight order state.
        """
        if not self._path.exists():
            return {}
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise ExecutionError(
                f"Corrupt execution state at {self._path}: {exc}"
            ) from exc
        return data.get("records", {})

    def _write(self, records: dict[str, dict[str, Any]]) -> None:
        """Atomically persist the ``records`` map (temp file + ``os.replace``)."""
        payload = {"records": records}
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        os.replace(tmp, self._path)

    def _require(
        self, records: dict[str, dict[str, Any]], deal_reference: str
    ) -> dict[str, Any]:
        """Return the record for ``deal_reference`` or raise — never auto-create."""
        record = records.get(deal_reference)
        if record is None:
            raise ExecutionError(
                f"Unknown deal_reference {deal_reference!r} in {self._path}"
            )
        return record

    # -- public API (concept §2) -------------------------------------------

    def record_pending(self, plan: OrderPlan) -> None:
        """Write-ahead a ``PENDING`` record for ``plan`` — **before** open_position.

        Persists the fields needed to reconcile the order later. Called once, just
        before the broker order; if the process dies after this and before
        confirmation, startup reconcile finds the dangling reference.
        """
        records = self._read()
        now = _format_iso(_utcnow())
        records[plan.deal_reference] = {
            "deal_reference": plan.deal_reference,
            "epic": plan.epic,
            "direction": plan.direction,
            "size": plan.size,
            "stop_level": plan.stop_level,
            "limit_level": plan.limit_level,
            "status": PENDING,
            "deal_id": None,
            "recorded_at": now,
            "updated_at": now,
        }
        self._write(records)

    def mark_open(self, deal_reference: str, deal_id: str) -> None:
        """Mark a recorded reference ``OPEN`` and attach the broker ``deal_id``."""
        records = self._read()
        record = self._require(records, deal_reference)
        record["status"] = OPEN
        record["deal_id"] = deal_id
        record["updated_at"] = _format_iso(_utcnow())
        self._write(records)

    def mark_closed(self, deal_reference: str) -> None:
        """Mark a recorded reference ``CLOSED`` (broker SL/TP, time-stop, reconcile)."""
        records = self._read()
        record = self._require(records, deal_reference)
        record["status"] = CLOSED
        record["updated_at"] = _format_iso(_utcnow())
        self._write(records)

    def open_references(self) -> list[str]:
        """References still considered open (``PENDING`` or ``OPEN``).

        This is the ``expected_references`` input to startup reconcile.
        """
        records = self._read()
        return [
            ref
            for ref, record in records.items()
            if record.get("status") in _OPEN_STATES
        ]

    def get(self, deal_reference: str) -> dict[str, Any] | None:
        """Return a copy of the record for ``deal_reference``, or ``None``."""
        record = self._read().get(deal_reference)
        return dict(record) if record is not None else None
