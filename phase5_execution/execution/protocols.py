"""Structural typing for Phase-5 collaborators (``typing.Protocol``).

The execution core (gates / sizing / vetos / order / monitor / executor) is
phase-isolated: it never imports ``broker_wrapper`` / ``persistence`` /
``research`` directly. It depends only on the *shapes* declared here, and the
wiring layer (Step 10) injects the real instances. This keeps the logic testable
with fakes and the package importable without the sibling runtime deps.

Only the methods Phase 5 actually calls are declared, with signatures verified
against the real adapters (code = source of truth). Broker methods return an
:class:`EnvelopeLike` — always check ``.ok`` before reading ``.data``.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class EnvelopeLike(Protocol):
    """The broker's canonical return shape (``broker_wrapper.envelope``).

    ``ok`` gates everything; on success read ``data``, on failure read ``error``
    (``{code, message, retryable}``).
    """

    ok: bool
    data: Any
    error: Any


@runtime_checkable
class BrokerProtocol(Protocol):
    """The broker surface Phase 5 uses (subset of ``IGAdapter``).

    Session, market probes, the real-time OHLCV momentum source, and the order /
    reconcile calls. ``direction`` is always ``"BUY"`` / ``"SELL"``;
    ``stop_level`` / ``limit_level`` are **absolute price levels**.
    """

    def connect(self) -> EnvelopeLike: ...

    def is_connected(self) -> bool: ...

    def get_account(self) -> EnvelopeLike: ...

    def get_price(self, epic: str) -> EnvelopeLike: ...

    def get_market_info(self, epic: str) -> EnvelopeLike: ...

    def get_ohlcv(self, epic: str, resolution: str, count: int) -> EnvelopeLike: ...

    def get_open_positions(self) -> EnvelopeLike: ...

    def open_position(
        self,
        epic: str,
        direction: str,
        size: float,
        order_type: str = ...,
        *,
        stop_level: float | None = ...,
        limit_level: float | None = ...,
        deal_reference: str | None = ...,
        currency: str | None = ...,
    ) -> EnvelopeLike: ...

    def close_position(self, deal_id: str) -> EnvelopeLike: ...

    def reconcile_positions(
        self, expected_references: list[str] | None = ...,
    ) -> EnvelopeLike: ...


@runtime_checkable
class DbProtocol(Protocol):
    """The read-only persistence surface Phase 5 uses (subset of ``Database``).

    Phase 5 never *writes* the DB — outcome/lesson writing is Phase 7.
    """

    def get_risk_level(self) -> str: ...        # "AGGRESSIV" | "KONSERVATIV"

    def get_current_score(self) -> float: ...


@runtime_checkable
class StateProtocol(Protocol):
    """The JSON-state surface Phase 5 uses (subset of ``StateManager``)."""

    def load_candidates(self) -> list[dict[str, Any]]: ...

    def candidates_are_fresh(self) -> bool: ...

    def clear_candidates(self) -> None: ...

    def load_bot_config(self) -> dict[str, Any]: ...


@runtime_checkable
class RewardSink(Protocol):
    """Optional Phase-7 outcome/reward hook (Decision A) — injected, default ``None``.

    The executor calls these two passive callbacks around a trade's lifecycle:
    ``on_trade_opened`` after ``place_order`` confirms OPEN (before monitoring) and
    ``on_trade_closed`` after the monitor returns a real close. Both receive a
    duck-typed snapshot payload (``reward.models.OpenedTrade`` / ``ClosedTrade`` at
    runtime — declared ``Any`` here so Phase 5 imports nothing from ``reward``).

    The sink is handed **only** snapshots — never the broker write path, a Gate, or a
    VETO — so it structurally cannot bypass one (Decision J). When no sink is injected
    (the default) the seam is skipped entirely and Phase 5 is bit-identical + AI-free.
    Implementations must be fail-closed: a raising callback never crashes the cycle
    (the executor guards both calls).
    """

    def on_trade_opened(self, opened: Any) -> None: ...

    def on_trade_closed(self, closed: Any) -> None: ...
