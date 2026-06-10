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
