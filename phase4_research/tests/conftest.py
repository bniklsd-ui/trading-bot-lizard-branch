"""Shared pytest fixtures for the Phase-4 research tests.

No network, no real credentials, no real LLM. This file grows step-by-step:
Step 2 needs only a ``FakeBroker`` (for the validator's live-spread recheck) and a
sample ``universe``. ``FakeDB`` / ``FakeFetcher`` / ``FakeLLM`` arrive with their
own steps (3, 5, 7), mirroring the Phase-3 conftest rhythm.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

DEFAULT_EPIC = "IX.D.DAX.IFMM.IP"


@dataclass
class _FakeEnv:
    """Duck-typed stand-in for a Phase-1 ``Envelope``.

    The validator only reads ``.ok`` and ``.data`` — we deliberately do **not**
    import the real ``Envelope`` (phase isolation; this also proves the validator
    is decoupled from ``broker_wrapper``).
    """

    ok: bool
    data: dict[str, Any] | None = None


class FakeBroker:
    """Configurable broker whose ``get_price`` drives the live recheck.

    Construct with the desired recheck outcome; every ``get_price`` call returns
    that same env (Step 2 issues exactly one recheck per validation). Defaults to
    a healthy TRADEABLE quote with a small spread.
    """

    def __init__(
        self,
        *,
        ok: bool = True,
        spread_pct: float | None = 0.03,
        market_status: str | None = "TRADEABLE",
    ) -> None:
        self._ok = ok
        self._spread_pct = spread_pct
        self._market_status = market_status
        self.calls: list[str] = []

    def get_price(self, epic: str) -> _FakeEnv:
        self.calls.append(epic)
        if not self._ok:
            return _FakeEnv(ok=False, data=None)
        return _FakeEnv(
            ok=True,
            data={
                "epic": epic,
                "bid": 18000.0,
                "ask": 18001.0,
                "spread": 1.0,
                "spread_pct": self._spread_pct,
                "market_status": self._market_status,
                "timestamp": "2026-06-05T09:30:00.000Z",
            },
        )


@pytest.fixture
def broker() -> FakeBroker:
    """A healthy default broker (ok, TRADEABLE, small spread)."""
    return FakeBroker()


@pytest.fixture
def universe() -> list[dict[str, Any]]:
    """Code-provided tradeable universe containing the default DAX epic."""
    return [
        {
            "epic": DEFAULT_EPIC,
            "name": "Germany 40 Cash (1 EUR)",
            "spread_pct": 0.03,
            "market_status": "TRADEABLE",
            "min_deal_size": 0.5,
        }
    ]


@pytest.fixture
def good_raw() -> dict[str, Any]:
    """A well-formed, in-universe BUY pick (the happy path)."""
    return {
        "abstain": False,
        "epic": DEFAULT_EPIC,
        "direction": "BUY",
        "confidence": 72.0,
        "reasoning": "Drift positive, spread tight, score neutral.",
    }
