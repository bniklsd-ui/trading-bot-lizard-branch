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

**Why the size filter is magnitude-based (live-debug 2026-06-23).** IG's
``/history/transactions`` returns ``size`` as a **signed** string (``"-19.8"`` for a
SELL, ``"+19.8"`` for a BUY); ``ig_adapter._parse_transaction`` passes it through
verbatim (``broker_wrapper/adapters/ig_adapter.py``). ``OpenedTrade.size`` is always
the **unsigned** deal quantity, so the filter compares **magnitudes**
(``abs(abs(tx_size) - abs(opened.size))``) — an exact signed compare silently rejected
every SELL forever (the first reward live run, deal ``DIAAAAXTGBTEYAC`` size ``19.8``,
hit exactly this). The direction is recovered for free anyway: IG's ``profit_loss``
already carries the correct sign. (The cleaner fix — normalising the sign in the P1
adapter — is deferred to keep this phase-isolated; see contract 1.1.)

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
``.initial_risk``, and (for the plausibility guard below) ``.open_ts`` are read, so
the recorder may pass either a real ``OpenedTrade`` or a minimal context rebuilt from
the persisted trade row.

**Plausibility guard (Phase-10 V3 Bug-A fix, 2026-07-17 session).** Branch 3's
magnitude match had no check that a candidate transaction even postdates the trade's
own open — a live incident (row `id=6`, documented in this session's
``phase10_v3/CLAUDE.md``) matched a different epic's 7-day-old, already-settled
transaction onto a same-size same-day trade, copying its wrong ``close_level``
(``profit_loss`` looked plausible by coincidence — same fixed ``stop_distance_points``
+ size ⇒ structurally similar loss magnitude). Fix: reject any candidate whose
``close_date`` predates ``opened.open_ts``. The two fields carry **different**
timezone conventions (IG's ``close_date`` is UTC; ``opened.open_ts`` is local,
e.g. ``+02:00`` — see ``build_opened``, ``execution/executor.py``), so the guard
parses both as tz-aware instants and compares in UTC — a naive lexical compare
would reject same-day legitimate matches too (an 11:31 UTC close sorts before a
12:49 ``+02:00`` open despite being ~40 min *after* it in real time).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
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


def _parse_instant(value: Any) -> datetime | None:
    """Best-effort parse an IG/``open_ts`` timestamp into a tz-aware UTC instant.

    Returns ``None`` on anything unparseable/missing — callers must treat that as
    "can't compare", never as a rejection signal (the plausibility guard is
    deliberately conservative: an unparseable timestamp must not reject an
    otherwise-usable candidate).
    """
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        # No explicit offset (IG's dateUtc/legacy fields sometimes omit it) — the
        # field name implies UTC; assume UTC rather than guessing a local zone.
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _r_multiple(profit_loss: float, initial_risk: float) -> float:
    """``R = profit_loss / initial_risk``; an ``initial_risk == 0`` resolves to ``0.0``
    (defensive — no ``ZeroDivisionError``)."""
    return (profit_loss / initial_risk) if initial_risk != 0 else 0.0


def resolve(closed: Any, broker: Any, opened: Any, cfg: RewardConfig) -> tuple[float, float, float]:
    """Resolve ``(close_level, profit_loss, r_multiple)`` for a closed trade.

    **Preference order (lag-free first, 2026-06-23).** IG demo only books
    ``get_trade_history`` after settlement, so it is unusable intraday. When the close
    deal confirmation gave us the realised close (the bot-issued ``TIME_STOP`` path,
    carried on the :class:`~reward.models.ClosedTrade`), we use it directly and never
    touch the broker:

    1. ``closed.profit_loss`` present → use it verbatim (IG's realised P&L); the close
       level is ``closed.close_level`` or, absent that, the intended open level.
    2. ``closed.close_level`` present (+ a known direction) → compute
       ``(close − open) · size · point_value · sign`` (a small approximation: the open
       side uses ``intended_open_level``, exact only if IG also returned ``profit``).
    3. otherwise (``CLOSED_BY_BROKER``, a confirm timeout, or a cold reconcile) → the
       heuristic ``get_trade_history`` magnitude match below.

    Args:
        closed: the :class:`~reward.models.ClosedTrade` (``close_level`` / ``profit_loss``
            preferred when present; ``closed_at`` is advisory recency context).
        broker: a read-only broker exposing ``get_trade_history(days) -> Envelope``.
            The reward layer is **never** handed an order/close path.
        opened: duck-typed open context — ``.size``, ``.intended_open_level``,
            ``.initial_risk`` and (for branch 2) ``.direction`` are read.
        cfg: the reward config (``point_value`` is used by branch 2).

    Returns:
        ``(close_level, profit_loss, r_multiple)``. ``r_multiple = profit_loss /
        initial_risk``; an ``initial_risk == 0`` is handled defensively as ``0.0``.

    Raises:
        PnLUnavailable: the history envelope was not ok, or no usable row matched the
            open context. Fail-closed — never fabricates a P&L.
    """
    initial_risk = float(opened.initial_risk)

    # (1)/(2) Lag-free resolution from the close deal confirmation (preferred).
    direct_pl = getattr(closed, "profit_loss", None)
    direct_level = getattr(closed, "close_level", None)
    if direct_pl is not None:
        close_level = float(direct_level) if direct_level is not None else float(opened.intended_open_level)
        profit_loss = float(direct_pl)
        logger.debug("pnl_resolver: using close-confirm P&L for deal_id=%s pl=%s",
                     getattr(closed, "deal_id", "?"), profit_loss)
        return close_level, profit_loss, _r_multiple(profit_loss, initial_risk)
    if direct_level is not None:
        direction = getattr(opened, "direction", None)
        sign = 1.0 if direction == "BUY" else -1.0 if direction == "SELL" else None
        if sign is not None:
            close_level = float(direct_level)
            profit_loss = (
                (close_level - float(opened.intended_open_level))
                * float(opened.size) * float(cfg.point_value) * sign
            )
            logger.debug("pnl_resolver: computed P&L from close level for deal_id=%s pl=%s",
                         getattr(closed, "deal_id", "?"), profit_loss)
            return close_level, profit_loss, _r_multiple(profit_loss, initial_risk)
        # direction unknown → fall through to the history match.

    # (3) Fallback: heuristic transaction-history match (settlement-delayed on IG demo).
    env = broker.get_trade_history(days=_HISTORY_DAYS)
    if not getattr(env, "ok", False):
        raise PnLUnavailable(
            f"get_trade_history not ok for deal_id={getattr(closed, 'deal_id', '?')}"
        )

    data = getattr(env, "data", None) or {}
    transactions: list[dict[str, Any]] = list(data.get("transactions", []))

    size = float(opened.size)
    intended_open_level = float(opened.intended_open_level)

    # Plausibility guard (Bug-A fix): a transaction that settled before this trade's
    # own open cannot be its close. ``None`` (open_ts missing/unparseable) disables
    # the guard entirely for this call — conservative, never rejects on "don't know".
    own_open_instant = _parse_instant(getattr(opened, "open_ts", None))

    # Hard filter: same size *magnitude* (IG signs the history size — see module
    # docstring) + a usable (non-null) close level and P&L.
    candidates: list[dict[str, Any]] = []
    for tx in transactions:
        tx_size = tx.get("size")
        if tx_size is None or abs(abs(float(tx_size)) - abs(size)) > _SIZE_TOL:
            continue
        if tx.get("profit_loss") is None or tx.get("close_level") is None:
            continue
        if tx.get("open_level") is None:
            continue
        if own_open_instant is not None:
            tx_close_instant = _parse_instant(tx.get("close_date"))
            if tx_close_instant is not None and tx_close_instant < own_open_instant:
                continue  # settled before this trade even opened — not its close
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
    r_multiple = _r_multiple(profit_loss, initial_risk)

    logger.debug(
        "pnl_resolver matched deal_id=%s → close_level=%s profit_loss=%s r=%s",
        getattr(closed, "deal_id", "?"), close_level, profit_loss, r_multiple,
    )
    return close_level, profit_loss, r_multiple
