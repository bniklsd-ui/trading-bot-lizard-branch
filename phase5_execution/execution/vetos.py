"""The pre-trade VETO layer — ``pre_trade_check()`` = 5 HARD VETOs (concept §5 + Phase 15 C3).

Where the gates (``gates.py``) ask *is this candidate eligible?*, the VETOs ask *is
reality still safe **right now**?* — a last-millisecond reality check on a **fresh**
snapshot taken immediately before the order. All five are **hard** (any fail = no
trade) and **fail-closed**: a data error, a not-``ok`` envelope, or too few bars is a
veto, never a silent pass. There is no soft warning here — a soft warning that trades
anyway is exactly the Force-Trigger anti-pattern (Decision B).

- **VETO 1** ``veto_status_and_window`` — market TRADEABLE and inside the trade window.
- **VETO 2** ``veto_spread`` — fresh ``spread_pct`` within ``max_spread_pct``.
- **VETO 3** ``veto_momentum`` — adverse-momentum guard read **only** from IG
  real-time bars (``broker.get_ohlcv``), **never** Phase-3 ``get_momentum()`` (delayed).
- **VETO 4** ``veto_position_conflict`` — no open opposite position, room under
  ``max_parallel_positions``.
- **VETO 5** ``longterm_pre_trade_check`` — deterministic predicates from promoted
  Phase-15 Instincts (``config.longterm_rules``). Empty tuple by default ⇒ inactive
  ⇒ bit-identical to pre-C3 behaviour (Phase 15 AK9). Promotion is gated upstream
  by ``promote_eligible`` (``phase15_v4/instinct/promotion.py``) — a predicate
  cannot reach here without ``n_closed >= instinct_n_min`` AND
  ``enable_instinct_promotion is True``.

Pure where possible: VETO 1/2/4 take pre-fetched envelopes; VETO 3 fetches its own
bars (the broker is duck-typed — passed in, never imported). VETO 5 takes the
already-built candidate dict + the config's rule tuple — no broker, no clock.
The window predicate is reused from ``gates.gate_time_window`` (same package) so the
tz logic lives once. Phase-isolated: ``execution.*`` + stdlib only, no sibling-package
imports (``phase15_v4/instinct/*`` is **never** imported here — the rules travel as
plain callables in the config, see ``vetos.py`` §C3 docstring).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from execution.config import ExecutionConfig
from execution.gates import gate_time_window
from execution.models import VetoVerdict

logger = logging.getLogger(__name__)

# Direction vocabulary — what ``open_position`` enforces. No options vocabulary.
_OPPOSITE = {"BUY": "SELL", "SELL": "BUY"}

_TRADEABLE = "TRADEABLE"


def veto_status_and_window(
    price_env: Any, now: datetime, config: ExecutionConfig
) -> VetoVerdict:
    """VETO 1: market is TRADEABLE (fresh ``get_price``) and ``now`` is in-window.

    Fail-closed: a not-``ok`` price envelope is a veto (we cannot verify the market
    is open). The window predicate reuses :func:`gates.gate_time_window`.
    """
    if not price_env.ok:
        return VetoVerdict(
            ok=False, veto="status_window", reason="price snapshot unavailable",
        )

    status = (price_env.data or {}).get("market_status")
    if status != _TRADEABLE:
        return VetoVerdict(
            ok=False,
            veto="status_window",
            reason=f"market_status {status!r} != {_TRADEABLE}",
        )

    if not gate_time_window(now, config).ok:
        return VetoVerdict(
            ok=False,
            veto="status_window",
            reason=(
                f"outside trade window {config.trading_window_start}-"
                f"{config.trading_window_end} {config.tz}"
            ),
        )

    return VetoVerdict(ok=True, veto="status_window", reason="")


def veto_spread(price_env: Any, config: ExecutionConfig) -> VetoVerdict:
    """VETO 2: fresh ``spread_pct`` within ``max_spread_pct`` (percent of ask).

    Uses the **fresh** ``get_price`` spread, not the ``spread_pct_at_pick`` Phase 4
    stored — the spread can blow out between research and the order. Fail-closed on a
    not-``ok`` envelope or a missing ``spread_pct``.
    """
    if not price_env.ok:
        return VetoVerdict(ok=False, veto="spread", reason="price snapshot unavailable")

    spread_pct = (price_env.data or {}).get("spread_pct")
    if spread_pct is None:
        return VetoVerdict(ok=False, veto="spread", reason="spread_pct missing")

    if spread_pct > config.max_spread_pct:
        return VetoVerdict(
            ok=False,
            veto="spread",
            reason=f"spread {spread_pct}% > max {config.max_spread_pct}%",
        )

    return VetoVerdict(ok=True, veto="spread", reason="")


def veto_momentum(
    broker: Any, epic: str, direction: str, config: ExecutionConfig
) -> VetoVerdict:
    """VETO 3: adverse-momentum guard from IG real-time bars (``get_ohlcv``).

    Reads ``broker.get_ohlcv(epic, momentum_resolution, momentum_count)`` and
    computes ``net_return_pct = (close_last - close_first) / close_first * 100``
    over the bar **closes** (percent — consistent with ``spread_pct`` and the
    ``_pct`` config name). A BUY into a sharp drop
    (``net_return_pct <= -threshold``) or a SELL into a sharp rally
    (``net_return_pct >= +threshold``) is vetoed.

    **v1, tune at profit** — a blunt directional guard, not a hidden confidence
    system. Fail-closed: a not-``ok`` envelope, a raised fault, fewer than 2 bars,
    or a missing/zero close is a veto. Momentum is **never** taken from Phase-3
    ``get_momentum()`` (delayed quote — a context signal, not a hard gate).
    """
    try:
        env = broker.get_ohlcv(epic, config.momentum_resolution, config.momentum_count)
    except Exception as exc:  # fail-closed: never proceed to an order on a data fault
        logger.warning("momentum veto: get_ohlcv raised for %s: %s", epic, exc)
        return VetoVerdict(ok=False, veto="momentum", reason=f"get_ohlcv raised: {exc}")

    if not env.ok:
        return VetoVerdict(ok=False, veto="momentum", reason="ohlcv snapshot unavailable")

    bars = (env.data or {}).get("bars", [])
    if len(bars) < 2:
        return VetoVerdict(
            ok=False, veto="momentum", reason=f"too few bars ({len(bars)})",
        )

    first_close = bars[0].get("close")
    last_close = bars[-1].get("close")
    if not first_close or last_close is None:  # 0/None close ⇒ unusable data
        return VetoVerdict(ok=False, veto="momentum", reason="missing or zero close price")

    net_return_pct = (last_close - first_close) / first_close * 100.0
    threshold = config.momentum_veto_threshold_pct

    if direction == "BUY" and net_return_pct <= -threshold:
        return VetoVerdict(
            ok=False,
            veto="momentum",
            reason=f"BUY into drop: net_return {net_return_pct:.3f}% <= -{threshold}%",
        )
    if direction == "SELL" and net_return_pct >= threshold:
        return VetoVerdict(
            ok=False,
            veto="momentum",
            reason=f"SELL into rally: net_return {net_return_pct:.3f}% >= {threshold}%",
        )

    return VetoVerdict(ok=True, veto="momentum", reason="")


def veto_position_conflict(
    open_positions_env: Any, candidate: dict[str, Any], config: ExecutionConfig
) -> VetoVerdict:
    """VETO 4: no open opposite position on the epic, room under max_parallel.

    Fresh ``get_open_positions``. Fail-closed on a not-``ok`` envelope. An open
    **opposite** position on the **same** epic is a hard conflict; the parallel cap
    (``max_parallel_positions``) is also enforced here on the fresh snapshot.
    """
    if not open_positions_env.ok:
        return VetoVerdict(
            ok=False,
            veto="position_conflict",
            reason="open-positions snapshot unavailable",
        )

    direction = candidate.get("direction")
    epic = candidate.get("epic")
    opposite = _OPPOSITE.get(direction)
    positions = (open_positions_env.data or {}).get("positions", [])

    for pos in positions:
        if pos.get("epic") == epic and pos.get("direction") == opposite:
            return VetoVerdict(
                ok=False,
                veto="position_conflict",
                reason=f"open {opposite} position on {epic} conflicts with {direction}",
            )

    if len(positions) >= config.max_parallel_positions:
        return VetoVerdict(
            ok=False,
            veto="position_conflict",
            reason=(
                f"{len(positions)} open >= max_parallel_positions "
                f"{config.max_parallel_positions}"
            ),
        )

    return VetoVerdict(ok=True, veto="position_conflict", reason="")


def longterm_pre_trade_check(
    candidate: dict[str, Any], rules: tuple[Any, ...]
) -> VetoVerdict:
    """VETO 5: deterministic, promoted Phase-15 Instinct predicates.

    Each rule in ``rules`` is ``Callable[[dict], bool]`` — ``True`` means "this
    candidate passes the rule", ``False`` means "vetoed". Empty tuple (the
    ``ExecutionConfig.longterm_rules`` default) ⇒ ``ok=True`` ⇒ **bit-identical**
    to pre-C3 behaviour (Phase 15 AK9).

    **Fail-closed on exceptions:** a rule that raises is a hard veto — same
    discipline as VETO 1–4 (a faulty long-term rule must never let a trade slip
    through). The exception's message is captured into ``reason`` so the operator
    log shows exactly which rule misfired.

    **Where ``rules`` comes from (Phase-15 wiring, not built here):**
    ``phase5_execution`` never imports ``phase15_v4``. The promotion-gate
    (``phase15_v4/instinct/promotion.py:promote_eligible``) returns the validated
    Instinct rows; a later wiring step (out of C3 scope) compiles each row into a
    plain deterministic predicate and bundles them into ``config.longterm_rules``.
    A predicate reaches VETO 5 **only** if ``promote_eligible`` opens both gates
    (``n_closed >= instinct_n_min`` AND ``enable_instinct_promotion is True`` —
    Phase 15 P10/P12). Until then, the field stays at its default ``()`` and VETO 5
    is a no-op.

    Args:
        candidate: the already-built trade candidate dict (the same one passed
            through VETO 1–4). Read-only — predicates must not mutate it.
        rules: tuple of ``Callable[[dict], bool]``. May be empty.

    Returns:
        ``VetoVerdict(ok=True, veto="longterm", reason="")`` if every rule passes
        (or there are no rules). The first rule that returns ``False`` or raises
        short-circuits with ``ok=False`` and a precise ``reason`` — the same shape
        as VETO 1–4.
    """
    if not rules:
        return VetoVerdict(ok=True, veto="longterm", reason="")

    for idx, rule in enumerate(rules):
        try:
            decision = rule(candidate)
        except Exception as exc:  # noqa: BLE001 — fail-closed, mirror VETO 1-4 discipline
            return VetoVerdict(
                ok=False,
                veto="longterm",
                reason=f"rule[{idx}] raised: {exc}",
            )
        if not decision:
            return VetoVerdict(
                ok=False,
                veto="longterm",
                reason=f"rule[{idx}] vetoed",
            )
    return VetoVerdict(ok=True, veto="longterm", reason="")


def pre_trade_check(
    broker: Any, candidate: dict[str, Any], now: datetime, config: ExecutionConfig
) -> VetoVerdict:
    """Run all 5 VETOs on a FRESH snapshot; return the first ``ok=False``.

    Each VETO reads its own fresh data (a single ``get_price`` feeds VETO 1+2; VETO 3
    fetches its own ``get_ohlcv``; VETO 4 a fresh ``get_open_positions``; VETO 5
    uses the already-built candidate + ``config.longterm_rules`` — no broker, no
    clock). The first failing veto short-circuits — a status veto must not even
    reach ``get_ohlcv``. No AI, no delayed data. All clear ⇒ ``ok=True``.
    """
    epic = candidate["epic"]
    direction = candidate["direction"]

    price_env = broker.get_price(epic)

    verdict = veto_status_and_window(price_env, now, config)
    if not verdict.ok:
        return verdict

    verdict = veto_spread(price_env, config)
    if not verdict.ok:
        return verdict

    verdict = veto_momentum(broker, epic, direction, config)
    if not verdict.ok:
        return verdict

    verdict = veto_position_conflict(broker.get_open_positions(), candidate, config)
    if not verdict.ok:
        return verdict

    verdict = longterm_pre_trade_check(candidate, config.longterm_rules)
    if not verdict.ok:
        return verdict

    return VetoVerdict(ok=True, veto="pre_trade_check", reason="")
