"""Realised P&L + level resolution for a closed trade (concept §6 Step 9).

**Deterministic, no AI, no DB write.** Given a :class:`~reward.models.ClosedTrade`,
the broker, and the trade's open context, return ``(close_level, profit_loss,
r_multiple)`` for the scorer. This is the bridge between the Phase-5 close fact
(``monitor_position`` returns *no* P&L — verified-contract 1.2) and the Phase-2
reward row.

**Why the match is heuristic (verified-contract 1.1).** ``broker.get_trade_history``
returns rows with **no ``deal_id``/``deal_reference``**; worse, ``epic`` is the
instrument *display name* (``instrumentName``, e.g. ``"Germany 40 Cash"``) rather than
the epic code we hold, and ``direction`` is hardcoded ``None``. So neither id, epic,
nor direction can key the match. What *is* reliable is ``size`` (a hard filter) and
``open_level`` (a proximity discriminator against the intended entry), tie-broken by
recency — the just-closed trade is the most recent matching row.

**Fallback = fail-closed (Decision J, operator decision 2026-06-19).** The concept §9
sketched a level-approximation fallback (``profit_loss ≈ (close_level - open_level)·…``),
but a ``ClosedTrade`` carries **no ``close_level``** to approximate from, so that path
is not buildable without fabricating a number. Instead, no usable match (IG history
lag, or a not-ok envelope) raises :class:`~reward.models.PnLUnavailable`; the recorder
(Step 8) catches it, logs ``critical``, leaves the trade closed at the broker, and
retries idempotently via ``deal_id`` on a later pass once history catches up. Because
the only successful path is a real history match, no ``pnl_source`` provenance tag is
needed in v1.

The ``opened`` argument is **duck-typed**: only ``.size``, ``.intended_open_level``,
and ``.initial_risk`` are read, so the recorder may pass either a real ``OpenedTrade``
or a minimal context rebuilt from the persisted trade row.
"""

from __future__ import annotations

import logging
from typing import Any

from reward.models import PnLUnavailable, RewardConfig

logger = logging.getLogger(__name__)

# How far back to ask for history. The trade just closed, so a short window suffices;
# 30 matches the adapter default and is harmless. v1 constant (tune later if needed).
_HISTORY_DAYS = 30

# Sizes are clean broker quantities (0.5, 1.0, …); a tiny tolerance guards float noise
# without ever merging two genuinely different sizes.
_SIZE_TOL = 1e-6


def _normalise_ts(value: Any) -> str:
    """Best-effort normalise an IG date string for chronological string comparison.

    IG date formats vary by field (``openDateUtc`` vs ``openDate``); for the recency
    tie-break we only need a monotonic key, so we strip a trailing ``Z`` and compare
    the leading ``YYYY-MM-DDTHH:MM:SS`` lexically (ISO order == chronological order).
    Unparseable/missing values sort first (``""``), i.e. are treated as least recent.
    """
    if not isinstance(value, str):
        return ""
    return value.rstrip("Z")[:19]


def resolve(closed: Any, broker: Any, opened: Any, cfg: RewardConfig) -> tuple[float, float, float]:
    """Resolve ``(close_level, profit_loss, r_multiple)`` for a closed trade.

    Args:
        closed: the :class:`~reward.models.ClosedTrade` (its ``closed_at`` is advisory
            context; the heuristic does not need it beyond recency ordering).
        broker: a read-only broker exposing ``get_trade_history(days) -> Envelope``.
            The reward layer is **never** handed an order/close path.
        opened: duck-typed open context — only ``.size``, ``.intended_open_level`` and
            ``.initial_risk`` are read.
        cfg: the reward config (reserved for future tunables; v1 uses module constants).

    Returns:
        ``(close_level, profit_loss, r_multiple)``. ``r_multiple = profit_loss /
        initial_risk``; an ``initial_risk == 0`` is handled defensively as ``0.0``
        (no ``ZeroDivisionError``) — the match is still valid.

    Raises:
        PnLUnavailable: the history envelope was not ok, or no usable row matched the
            open context (size within tolerance, with a non-null ``profit_loss`` and
            ``close_level``). Fail-closed — never fabricates a P&L.
    """
    env = broker.get_trade_history(days=_HISTORY_DAYS)
    if not getattr(env, "ok", False):
        raise PnLUnavailable(
            f"get_trade_history not ok for deal_id={getattr(closed, 'deal_id', '?')}"
        )

    data = getattr(env, "data", None) or {}
    transactions: list[dict[str, Any]] = list(data.get("transactions", []))

    size = float(opened.size)
    intended_open_level = float(opened.intended_open_level)

    # Hard filter: same size + a usable (non-null) close level and P&L.
    candidates: list[dict[str, Any]] = []
    for tx in transactions:
        tx_size = tx.get("size")
        if tx_size is None or abs(float(tx_size) - size) > _SIZE_TOL:
            continue
        if tx.get("profit_loss") is None or tx.get("close_level") is None:
            continue
        if tx.get("open_level") is None:
            continue
        candidates.append(tx)

    if not candidates:
        raise PnLUnavailable(
            f"no usable history row for deal_id={getattr(closed, 'deal_id', '?')} "
            f"(size={size}); IG lag — retry later"
        )

    # Pick the smallest open-level distance; resolve level ties by recency. Pre-sorting
    # by close_date descending lets ``min`` (which keeps the first of equal keys) return
    # the most recent row among equal-distance candidates — the just-closed trade.
    candidates.sort(key=lambda tx: _normalise_ts(tx.get("close_date")), reverse=True)
    best = min(
        candidates,
        key=lambda tx: abs(float(tx["open_level"]) - intended_open_level),
    )

    close_level = float(best["close_level"])
    profit_loss = float(best["profit_loss"])

    initial_risk = float(opened.initial_risk)
    r_multiple = (profit_loss / initial_risk) if initial_risk != 0 else 0.0

    logger.debug(
        "pnl_resolver matched deal_id=%s → close_level=%s profit_loss=%s r=%s",
        getattr(closed, "deal_id", "?"), close_level, profit_loss, r_multiple,
    )
    return close_level, profit_loss, r_multiple
