"""Shared fixtures for the Phase-5 test suite.

Starts small (Step 2): an ``OrderPlan`` factory so tests don't repeat the six
fields, and unique ``deal_reference``s so multiple plans in one test never
collide. Broker/Db/State fakes arrive with Steps 3/5/6.
"""

from __future__ import annotations

import uuid
from typing import Callable

import pytest

from execution.models import OrderPlan


@pytest.fixture
def make_order_plan() -> Callable[..., OrderPlan]:
    """Return a factory building an ``OrderPlan`` with a unique ``bot-`` ref.

    Any field is overridable; ``deal_reference`` defaults to a fresh
    ``bot-<uuid4hex>`` so callers can build several distinct plans.
    """

    def _factory(
        *,
        epic: str = "IX.D.DAX.IFMM.IP",
        direction: str = "BUY",
        size: float = 0.5,
        stop_level: float = 17970.0,
        limit_level: float = 18045.0,
        deal_reference: str | None = None,
    ) -> OrderPlan:
        return OrderPlan(
            epic=epic,
            direction=direction,
            size=size,
            stop_level=stop_level,
            limit_level=limit_level,
            deal_reference=deal_reference or f"bot-{uuid.uuid4().hex}",
        )

    return _factory


@pytest.fixture
def order_plan(make_order_plan: Callable[..., OrderPlan]) -> OrderPlan:
    """A single ready-made ``OrderPlan`` (the common single-plan case)."""
    return make_order_plan()
