"""Phase 17 B-6 (T9) — ``wiring._realized_pnl_today``: the daily-loss breaker's DB reader.

Carries the worst case of every OPEN row when today's booking is still settling.
A broker-closed trade stays ``status='OPEN'`` with ``profit_loss`` NULL until IG
settles (1 h 06 – 1 h 54 measured, Phase-16-Closeout §4), which left the breaker
blind to a fresh stop-out. Each OPEN row now counts as ``-initial_risk`` (the
planned stop loss). An OPEN row without ``initial_risk`` cannot be bounded → raise;
``AutoConfirm`` treats a raising reader as fail-closed (blocks + logs critical).

Real ``persistence.Database(":memory:")`` + ``run_migrations()`` (mirror of
``phase15_v4/tests/test_instinct_bridge.py::test_bridge_contract_real_database_and_validator``,
B-3 Commit `3377b0a`) — a stub is **not** enough here because the test asserts an
actual schema + SQL result, not a re-implementation.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

# scripts/ -> phase8_scheduler/ (so ``from scripts.wiring import ...`` resolves)
_PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(_PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(_PROJECT_DIR))

from persistence.db import Database  # noqa: E402


@pytest.fixture
def db() -> Database:
    """A real in-memory Database with all migrations applied."""
    d = Database(":memory:")
    d.run_migrations()
    return d


def _today_iso() -> str:
    """Today's session date in ``YYYY-MM-DD`` (Berlin-aware would matter only at the
    midnights around 23:00/00:00 CET; the test seeds its own rows with this value
    and asserts only that the SUM filters by ``session_date`` exactly)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _seed_closed_trade(
    db: Database,
    *,
    session_date: str,
    profit_loss: float,
    deal_id: str = "DIAAA-CL",
) -> int:
    """Seed a CLOSED trade with realised P&L; default row carries no ``initial_risk``."""
    row_id = db.insert_trade(
        {
            "deal_id": deal_id,
            "epic": "IX.D.DAX.IFMM.IP",
            "direction": "BUY",
            "size": 1.0,
            "currency": "EUR",
            "open_level": 18000.0,
            "close_level": 18030.0,
            "open_ts": f"{session_date}T09:05:00Z",
            "close_ts": f"{session_date}T14:30:00Z",
            "profit_loss": profit_loss,
            "session_date": session_date,
        }
    )
    db.conn.execute(
        "UPDATE trade_outcomes SET status = 'CLOSED' WHERE id = ?", (row_id,)
    )
    return row_id


def _seed_open_trade(
    db: Database,
    *,
    session_date: str,
    initial_risk: float | None,
    deal_id: str = "DIAAA-OP",
) -> int:
    """Seed an OPEN trade (``status='OPEN'`` is the DB insert default); ``initial_risk``
    of None simulates the unbounded row that must raise."""
    record: dict[str, Any] = {
        "deal_id": deal_id,
        "epic": "IX.D.DAX.IFMM.IP",
        "direction": "BUY",
        "size": 1.0,
        "currency": "EUR",
        "open_level": 18000.0,
        "open_ts": f"{session_date}T10:00:00Z",
        "session_date": session_date,
    }
    if initial_risk is not None:
        record["initial_risk"] = initial_risk
    return db.insert_trade(record)


def test_booked_pnl_only_when_no_open_rows(db: Database) -> None:
    """Phase 17 B-6: only CLOSED rows with realised P&L → their ``profit_loss`` sum
    is the breaker's reading. Booking behaviour unchanged vs pre-B-6 when nothing
    is open."""
    today = _today_iso()
    # Two winner days, one loser day, none yet-pending-settlement.
    _seed_closed_trade(db, session_date=today, profit_loss=120.0, deal_id="DIAAA-W1")
    _seed_closed_trade(db, session_date=today, profit_loss=80.0, deal_id="DIAAA-W2")
    _seed_closed_trade(db, session_date=today, profit_loss=-40.0, deal_id="DIAAA-L1")

    from scripts.wiring import _realized_pnl_today
    assert _realized_pnl_today(db.conn, today) == pytest.approx(160.0)  # 120 + 80 - 40


def test_open_row_counts_as_minus_initial_risk(db: Database) -> None:
    """Phase 17 B-6 (T9): an OPEN row with ``initial_risk`` counts as ``-initial_risk``
    for the breaker. Booked P&L from CLOSED rows is summed unchanged; today's
    ``profit_loss`` from any CLOSED row whose ``profit_loss`` is settled is read
    as-is.

    Combined scenario: +50 from a settled CLOSED winner, -30 (the planned stop
    loss) from one still-open row. Total = 20 — the breaker sees 20 of today's
    risk consumed, **not** 50, because the OPEN row's stop-out is counted as
    worst case. Pre-B-6 the breaker would have seen +50 only and happily opened
    another trade.
    """
    today = _today_iso()
    _seed_closed_trade(db, session_date=today, profit_loss=50.0, deal_id="DIAAA-W1")
    _seed_open_trade(db, session_date=today, initial_risk=30.0, deal_id="DIAAA-OP-A")

    from scripts.wiring import _realized_pnl_today
    assert _realized_pnl_today(db.conn, today) == pytest.approx(20.0)  # 50 + (-30)


def test_open_row_without_initial_risk_raises(db: Database) -> None:
    """Phase 17 B-6 (T9): an OPEN row with NULL ``initial_risk`` cannot be bounded
    → ``_realized_pnl_today`` raises ``RuntimeError``; ``AutoConfirm`` treats a
    raising reader as fail-closed (blocks + logs critical, Contract E).

    The test seeds the bookable winner for context, then the unbounded OPEN row,
    and asserts the raise happens **before** the SUM is returned.
    """
    today = _today_iso()
    _seed_closed_trade(db, session_date=today, profit_loss=15.0, deal_id="DIAAA-W1")
    _seed_open_trade(db, session_date=today, initial_risk=None, deal_id="DIAAA-OP-B")

    from scripts.wiring import _realized_pnl_today
    with pytest.raises(RuntimeError, match="OPEN trade without initial_risk"):
        _realized_pnl_today(db.conn, today)
