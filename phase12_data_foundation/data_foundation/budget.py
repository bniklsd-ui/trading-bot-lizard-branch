"""``SourceBudget`` — persistent IG-points spend ledger + ``can_spend`` prediction (D10).

Replaces the ``_PAPER_ALLOWANCE_FLOOR``/``_PAPER_BUDGET_COOLDOWN_MIN`` placeholder
mechanic in ``phase8_scheduler/scripts/wiring.py`` structurally: a declared
``QuotaModel``, a persistent ledger (``source_spend`` in ``data/bars.sqlite``, same
file as ``BarArchive``, D4), an observation table fed from the real ``allowance``
object IG returns on every successful ``/prices`` call, and a ``can_spend``
prediction that checks *before* a fetch instead of discovering exhaustion from a
403 (the 2026-08-03 incident this is modelled against, §5).

Owns its own ``sqlite3`` connection (D3 phase isolation) to the *same physical
file* ``BarArchive`` writes to — either class can be instantiated first; both
issue idempotent ``CREATE TABLE IF NOT EXISTS`` DDL for the tables they use.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

_CREATE_SOURCE_SPEND = """
CREATE TABLE IF NOT EXISTS source_spend (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    ts_utc TEXT NOT NULL,
    points INTEGER NOT NULL,
    kind   TEXT NOT NULL
)
"""
_CREATE_ALLOWANCE_OBSERVATIONS = """
CREATE TABLE IF NOT EXISTS allowance_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    observed_at TEXT NOT NULL,
    total INTEGER, remaining INTEGER, expiry TEXT
)
"""


def _default_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def _parse(ts_utc: str) -> datetime:
    normalized = ts_utc.replace("Z", "+00:00") if ts_utc.endswith("Z") else ts_utc
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@dataclass(frozen=True)
class QuotaModel:
    """A declared per-source quota. ``points_per_window=None`` means "no known
    cap" (``can_spend`` then only defers to a live observation, never blocks on
    the model alone)."""

    source: str
    points_per_window: int | None
    window_days: int | None


# §9.5/§9.11: 10,000 points / rolling 7-day window is IG's documented default for
# historical-price allowance — confirm against a real ``totalAllowance`` observation
# at execution and adjust here (a code commit, not config drift, per D10/D18).
IG_QUOTA_V1 = QuotaModel(source="ig", points_per_window=10_000, window_days=7)


class SourceBudget:
    """Spend ledger + prediction for one :class:`QuotaModel` source.

    ``expiry`` passed to :meth:`record_allowance` is treated as an **absolute**
    ISO-8601 UTC instant (the moment the current allowance window resets) —
    documented assumption pending live confirmation of IG's real ``allowance``
    field shapes (§9.5). If IG's ``allowanceExpiry`` turns out to be a
    seconds-remaining counter instead, the caller (``BudgetedIGBarProvider``,
    Step 4) converts it to an absolute instant before calling this method — this
    class never re-derives "now" from anything but ``now_fn``.
    """

    def __init__(
        self,
        db_path: str | Path,
        model: QuotaModel,
        *,
        reserve_points: int = 1_500,
        now_fn: Callable[[], datetime] = _default_now,
    ) -> None:
        self.db_path = str(db_path)
        self.model = model
        self.reserve_points = reserve_points
        self._now_fn = now_fn
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(_CREATE_SOURCE_SPEND)
        self.conn.execute(_CREATE_ALLOWANCE_OBSERVATIONS)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # -- writes -------------------------------------------------------------

    def record_spend(self, points: int, kind: str) -> None:
        """Book ``points`` spent against this source (``kind`` e.g. ``'tracker'``,
        ``'probe'``, ``'sample'``, ``'research'``, ``'manual'``)."""
        self.conn.execute(
            "INSERT INTO source_spend (source, ts_utc, points, kind) VALUES (?, ?, ?, ?)",
            (self.model.source, _iso(self._now_fn()), points, kind),
        )
        self.conn.commit()

    def record_allowance(
        self, total: int | None, remaining: int | None, expiry: str | None
    ) -> None:
        """Persist one observed ``allowance`` object (any/all fields may be
        ``None`` — e.g. an exhausted response that carries no allowance object
        at all still gets a row, so the gap itself is visible in the ledger)."""
        self.conn.execute(
            "INSERT INTO allowance_observations (observed_at, total, remaining, expiry) "
            "VALUES (?, ?, ?, ?)",
            (_iso(self._now_fn()), total, remaining, expiry),
        )
        self.conn.commit()

    # -- reads ----------------------------------------------------------------

    def window_start(self) -> str | None:
        """Current window's start instant, derived from the latest observation
        carrying a non-null ``expiry`` (``expiry - window_days``). ``None`` when
        no such observation exists yet **or** the model has no ``window_days`` —
        callers then fall back to "everything ever spent" (documented ceiling:
        without a real observation we cannot know when IG's window last rolled
        over)."""
        if self.model.window_days is None:
            return None
        row = self.conn.execute(
            "SELECT expiry FROM allowance_observations "
            "WHERE expiry IS NOT NULL ORDER BY observed_at DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        try:
            expiry_dt = _parse(row["expiry"])
        except ValueError:
            # §9.5: IG's real allowanceExpiry shape is unconfirmed at plan time — if a
            # caller ever passes something that isn't an absolute ISO instant (e.g. a
            # raw seconds-remaining counter, unconverted), fail soft into "no usable
            # observation" rather than crashing can_spend() — the one call every IG
            # fetch depends on. Conservative direction: falls back to summing every
            # spend ever recorded (spent_in_window's no-observation path).
            return None
        return _iso(expiry_dt - timedelta(days=self.model.window_days))

    def spent_in_window(self) -> int:
        """Sum of points spent since :meth:`window_start` (or, absent any
        observation, since the very first ledger row — "eigene Rechnung ab
        erstem Spend")."""
        ws = self.window_start()
        if ws is None:
            row = self.conn.execute(
                "SELECT COALESCE(SUM(points), 0) AS total FROM source_spend WHERE source = ?",
                (self.model.source,),
            ).fetchone()
        else:
            row = self.conn.execute(
                "SELECT COALESCE(SUM(points), 0) AS total FROM source_spend "
                "WHERE source = ? AND ts_utc >= ?",
                (self.model.source, ws),
            ).fetchone()
        return int(row["total"])

    def remaining_estimate(self) -> int | None:
        """``min(model-based remaining, latest-observation-based remaining)`` —
        an observation, when it disagrees with our own bookkeeping, wins by
        being the smaller (more conservative) number. ``None`` only when
        neither a capped model nor any observation exists (fully unknown)."""
        candidates: list[int] = []
        if self.model.points_per_window is not None:
            candidates.append(self.model.points_per_window - self.spent_in_window())

        obs_row = self.conn.execute(
            "SELECT observed_at, remaining FROM allowance_observations "
            "WHERE remaining IS NOT NULL ORDER BY observed_at DESC LIMIT 1"
        ).fetchone()
        if obs_row is not None:
            # Strict '>' (not '>='), deliberately: the observed `remaining` already
            # reflects whatever spend was just booked when the response arrived (an
            # IG /prices call's allowance object and its own point cost land in the
            # ledger at the same instant) -- counting that spend again on top would
            # double-count it. Do not "harmonize" this with spent_in_window's '>='.
            spent_since = self.conn.execute(
                "SELECT COALESCE(SUM(points), 0) AS total FROM source_spend "
                "WHERE source = ? AND ts_utc > ?",
                (self.model.source, obs_row["observed_at"]),
            ).fetchone()["total"]
            candidates.append(int(obs_row["remaining"]) - int(spent_since))

        return min(candidates) if candidates else None

    def can_spend(self, points: int) -> bool:
        """``True`` iff spending ``points`` would still leave the reserve floor
        intact. An unconstrained budget (no model cap, no observation ever
        seen) is permissive — ``True``, since there's nothing to block against."""
        est = self.remaining_estimate()
        if est is None:
            return True
        return (est - points) > self.reserve_points

    def predicted_exhaustion_days(self, daily_rate: float) -> float | None:
        """Days until :meth:`remaining_estimate` hits zero at ``daily_rate``
        points/day. ``None`` when the estimate or the rate is unusable."""
        est = self.remaining_estimate()
        if est is None or daily_rate <= 0:
            return None
        return est / daily_rate
