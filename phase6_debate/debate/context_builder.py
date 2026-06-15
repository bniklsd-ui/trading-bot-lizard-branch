"""Module 2 — deterministic context assembly. **This is the AI boundary.**

``build_debate_context`` reads exactly **one** fresh broker snapshot
(``get_price`` + ``get_ohlcv`` + ``get_market_info``) and folds it together with
the Phase-4 candidate (the *seed*) into a frozen :class:`DebateContext`. The
broker is read **here, in code** — the Bull/Bear/Judge agents never receive it
(Decision J — structural fail-safe: the debate cannot reach the broker, so it
cannot bypass a VETO or place an order).

100% deterministic, no AI. Imports only ``debate.models`` / ``debate.timeutil`` /
stdlib (the broker is typed via a local ``Protocol``) — no ``anthropic`` /
``broker_wrapper`` / ``research`` import, matching the Phase-4 ``context_builder``
isolation pattern.

Fail-closed: a not-``ok`` envelope, a raised broker fault, a non-``TRADEABLE``
market, or unusable bar data raises :class:`DebateError`. The orchestrator
(Module 6) converts that to a fail-closed ABSTAIN → NO_TRADE; it is never raised
out to Phase 5 (Decision J). Logging → stderr only.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol

from debate.models import DebateConfig, DebateContext, DebateError
from debate.timeutil import utc_iso_now

logger = logging.getLogger(__name__)

# IG's go-state. Mirrors the Phase-1 ``MarketStatus`` literal + Phase-5 VETO use.
_TRADEABLE = "TRADEABLE"


class _BrokerLike(Protocol):
    """The minimal read-only broker surface the context builder needs.

    Typed locally (not imported from ``broker_wrapper``) to keep this module
    phase-isolated. Each method returns an Envelope-shaped object with ``.ok``
    (bool) and ``.data`` (dict) — see the Phase-1 ``Envelope`` contract.
    """

    def get_price(self, epic: str) -> Any: ...
    def get_ohlcv(self, epic: str, resolution: str, count: int) -> Any: ...
    def get_market_info(self, epic: str) -> Any: ...


def build_debate_context(
    candidate: dict[str, Any], broker: _BrokerLike, config: DebateConfig
) -> DebateContext:
    """Assemble the read-only :class:`DebateContext` the agents argue over.

    Reads each broker probe **exactly once**. The fresh live ``spread_pct`` and
    ``market_status`` from ``get_price`` supersede the candidate's
    ``spread_pct_at_pick`` (the candidate's spread is stale by the time the debate
    runs). ``recent_bars_summary`` is built from the IG real-time ``get_ohlcv``
    bars — the agents' real-time price picture, in contrast to the delayed
    Phase-4 ``drift_at_pick`` sentiment.

    Args:
        candidate: the loaded Phase-4 candidate dict (frozen P4→P5 contract keys:
            ``epic, direction, llm_confidence, reasoning, spread_pct_at_pick,
            drift_at_pick|None, score_at_pick, threshold_applied, generated_at,
            source``).
        broker: the connected broker (read-only surface; see :class:`_BrokerLike`).
        config: the debate config (supplies ``bars_resolution`` / ``bars_count``).

    Returns:
        A frozen :class:`DebateContext`.

    Raises:
        DebateError: on any not-``ok`` envelope, raised broker fault,
            non-``TRADEABLE`` market, or unusable bar data. The orchestrator turns
            this into a fail-closed ABSTAIN.
    """
    epic = candidate["epic"]

    # --- probe 1: fresh price (gates on live market status) ----------------
    price_env = broker.get_price(epic)
    if not getattr(price_env, "ok", False):
        raise DebateError(f"get_price not ok for {epic}")
    price = price_env.data or {}
    market_status = price.get("market_status")
    if market_status != _TRADEABLE:
        raise DebateError(f"market not tradeable for {epic}: {market_status!r}")
    spread_pct = price.get("spread_pct")
    if spread_pct is None:
        raise DebateError(f"missing spread_pct for {epic}")

    # --- probe 2: IG real-time bars → recent_bars_summary ------------------
    try:
        ohlcv_env = broker.get_ohlcv(epic, config.bars_resolution, config.bars_count)
    except Exception as exc:  # fail-closed: never build a context on a data fault
        logger.warning("context build: get_ohlcv raised for %s: %s", epic, exc)
        raise DebateError(f"get_ohlcv raised for {epic}: {exc}") from exc
    if not getattr(ohlcv_env, "ok", False):
        raise DebateError(f"get_ohlcv not ok for {epic}")
    bars = (ohlcv_env.data or {}).get("bars", [])
    recent_bars_summary = _summarise_bars(bars, config.bars_resolution)

    # --- probe 3: market info (completeness / status cross-check) ----------
    info_env = broker.get_market_info(epic)
    if not getattr(info_env, "ok", False):
        raise DebateError(f"get_market_info not ok for {epic}")

    return DebateContext(
        epic=epic,
        seed_direction=candidate["direction"],
        seed_reasoning=candidate.get("reasoning", ""),
        seed_confidence=candidate.get("llm_confidence", 0.0),
        spread_pct=spread_pct,
        market_status=market_status,
        recent_bars_summary=recent_bars_summary,
        drift_at_pick=candidate.get("drift_at_pick"),  # None must not crash
        score_at_pick=candidate.get("score_at_pick", 0.0),
        generated_at=utc_iso_now(),
    )


def _summarise_bars(bars: list[dict[str, Any]], resolution: str) -> str:
    """Compact, deterministic text summary of the IG real-time bar closes.

    Mirrors the Phase-5 VETO-3 close-read discipline: needs ≥2 bars and a usable
    (non-zero, non-``None``) first/last close, else the data is unusable and we
    fail closed. The summary reports the window, first/last close, and net %.

    Raises:
        DebateError: fewer than 2 bars or a missing/zero boundary close.
    """
    if len(bars) < 2:
        raise DebateError(f"too few bars ({len(bars)})")
    first_close = bars[0].get("close")
    last_close = bars[-1].get("close")
    if not first_close or last_close is None:  # 0/None close ⇒ unusable data
        raise DebateError("missing or zero close price")
    net_return_pct = (last_close - first_close) / first_close * 100.0
    return (
        f"{len(bars)} x {resolution} bars (IG real-time): "
        f"first close {first_close:.1f}, last close {last_close:.1f}, "
        f"net {net_return_pct:+.3f}%"
    )
