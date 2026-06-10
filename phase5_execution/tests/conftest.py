"""Shared fixtures for the Phase-5 test suite.

Grows step-by-step (mirroring the Phase-4 conftest rhythm), no network, no real
credentials:

- Step 2: an ``OrderPlan`` factory (``make_order_plan``/``order_plan``).
- Step 3 (gates): a duck-typed ``_FakeEnv`` (``.ok``/``.data``, the envelope
  shape the gates read — we deliberately do **not** import the real ``Envelope``,
  proving phase isolation), a ``make_candidate`` factory (the Phase-4 candidate
  contract dict), and a ``FakeState`` (configurable candidate freshness/loading).
  ``FakeBroker``/``FakeDB`` arrive with Steps 4/5 — the gates take envelopes
  directly, so no broker fake is needed yet.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Callable

import pytest

from execution.models import OrderPlan

DEFAULT_EPIC = "IX.D.DAX.IFMM.IP"


@dataclass
class _FakeEnv:
    """Duck-typed stand-in for a Phase-1 ``Envelope`` — only ``.ok``/``.data``."""

    ok: bool
    data: dict[str, Any] | None = None


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


# --- Step 3 (gates) -------------------------------------------------------


@pytest.fixture
def make_candidate() -> Callable[..., dict[str, Any]]:
    """Return a factory for a Phase-4 contract candidate dict (10 keys).

    Defaults to a healthy BUY pick on the anchor epic; any field overridable.
    """

    def _factory(
        *,
        epic: str = DEFAULT_EPIC,
        direction: str = "BUY",
        llm_confidence: float = 70.0,
        reasoning: str = "test pick",
        spread_pct_at_pick: float = 0.03,
        drift_at_pick: float | None = 0.1,
        score_at_pick: float = 60.0,
        threshold_applied: float = 55.0,
        generated_at: str = "2026-06-10T09:05:00.000Z",
        source: str = "research",
    ) -> dict[str, Any]:
        return {
            "epic": epic,
            "direction": direction,
            "llm_confidence": llm_confidence,
            "reasoning": reasoning,
            "spread_pct_at_pick": spread_pct_at_pick,
            "drift_at_pick": drift_at_pick,
            "score_at_pick": score_at_pick,
            "threshold_applied": threshold_applied,
            "generated_at": generated_at,
            "source": source,
        }

    return _factory


class FakeState:
    """Configurable stand-in for ``StateManager`` (Gate 2 surface only).

    ``fresh`` drives ``candidates_are_fresh()``; ``candidates`` is what
    ``load_candidates()`` returns. ``clear_candidates`` calls are recorded.
    """

    def __init__(
        self,
        *,
        fresh: bool = True,
        candidates: list[dict[str, Any]] | None = None,
    ) -> None:
        self._fresh = fresh
        self.candidates = candidates if candidates is not None else []
        self.fresh_calls = 0
        self.load_calls = 0
        self.clear_calls = 0

    def candidates_are_fresh(self) -> bool:
        self.fresh_calls += 1
        return self._fresh

    def load_candidates(self) -> list[dict[str, Any]]:
        self.load_calls += 1
        return list(self.candidates)

    def clear_candidates(self) -> None:
        self.clear_calls += 1
        self.candidates = []
