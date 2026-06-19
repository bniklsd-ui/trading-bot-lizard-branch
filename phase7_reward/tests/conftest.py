"""Shared fixtures for the Phase-7 reward test suite.

Mocked, no network, no real LLM, no real credentials (project rule). Grows per
module, mirroring the Phase-4/5/6 conftest rhythm. Steps 3–6 (models / confidence /
scorer / synthetic) were pure math and needed no fakes; **Step 7 introduces the first
P7 fake** — a scripted ``FakeLLM`` standing in for the shared ``research.LLMClient``
(the brain's only collaborator) — plus tiny factories for the contract dataclasses.
"""

from __future__ import annotations

from typing import Any, Callable

import pytest

from reward.models import ClosedTrade, RewardResult

# A representative successful-call usage record (the 8-field token_meter shape the
# real client sets on ``last_usage``). FakeLLM copies it per call.
_DEFAULT_USAGE: dict[str, Any] = {
    "input_tokens": 320,
    "output_tokens": 40,
    "cache_read_input_tokens": 0,
    "cache_creation_input_tokens": 0,
    "est_cost_usd": 0.00052,
    "est_cost_eur": 0.00048,
}


class FakeLLM:
    """Scripted stand-in for the shared ``research.LLMClient`` (no SDK, no network).

    Returns ``answers`` in order from ``ask_candidate`` and sets ``last_usage`` to a
    copy of ``usage`` per successful call (exactly what the real client does and what
    the brain reads back for observability). The ``(system, user, schema)`` of every
    call is recorded in ``seen_systems`` / ``seen_users`` / ``seen_schemas`` so the
    prompt-content tests can assert. ``raises_exc`` makes the call raise that exception
    (the fail-closed path) **before** ``last_usage`` is set. If the script runs out,
    the last answer is repeated.

    Mirrors the Phase-6 conftest ``FakeLLM`` shape (settable ``model``/``temperature``/
    ``max_tokens``, ``last_usage``) so the brain can be driven exactly like the debate.
    """

    def __init__(
        self,
        answers: list[Any],
        *,
        usage: dict[str, Any] | None = None,
        raises_exc: BaseException | None = None,
    ) -> None:
        self._answers = list(answers)
        self._i = 0
        self._usage = usage if usage is not None else dict(_DEFAULT_USAGE)
        self.raises_exc = raises_exc

        # set by the wiring on the real client; defaulted here so duck-typing holds.
        self.model = "claude-haiku-4-5-20251001"
        self.temperature = 0.3
        self.max_tokens = 400
        self.last_usage: dict[str, Any] | None = None

        self.calls = 0
        self.seen_systems: list[str] = []
        self.seen_users: list[str] = []
        self.seen_schemas: list[dict] = []

    def ask_candidate(self, system: str, user: str, json_schema: dict) -> dict:
        self.calls += 1
        self.seen_systems.append(system)
        self.seen_users.append(user)
        self.seen_schemas.append(json_schema)
        if self.raises_exc is not None:
            raise self.raises_exc
        self.last_usage = dict(self._usage)
        idx = self._i
        self._i += 1
        if idx >= len(self._answers):
            return self._answers[-1]
        return self._answers[idx]


class LLMResponseError(Exception):
    """Local stand-in for ``research.models.LLMResponseError`` (matched by behaviour).

    The brain catches ``Exception`` broadly (best-effort, Decision J), so the tests
    never need to import the real Phase-4 exception — a same-named local one drives
    the exhausted-retry path without crossing the phase boundary.
    """


@pytest.fixture
def make_closed() -> Callable[..., ClosedTrade]:
    """Factory for a :class:`ClosedTrade` (overridable fields)."""

    def _make(**overrides: Any) -> ClosedTrade:
        fields: dict[str, Any] = {
            "deal_reference": "bot-abc123",
            "deal_id": "DIAAAAXQ6CSGTA5",
            "status": "CLOSED_BY_BROKER",
            "closed_at": "2026-06-19T15:30:00.000Z",
        }
        fields.update(overrides)
        return ClosedTrade(**fields)

    return _make


@pytest.fixture
def make_reward() -> Callable[..., RewardResult]:
    """Factory for a :class:`RewardResult` (overridable fields)."""

    def _make(**overrides: Any) -> RewardResult:
        fields: dict[str, Any] = {
            "outcome_delta": 2.0,
            "process_delta": 1.5,
            "score_before": 50.0,
            "score_after": 53.5,
            "win_loss": "WIN",
            "r_multiple": 1.4,
        }
        fields.update(overrides)
        return RewardResult(**fields)

    return _make


@pytest.fixture
def market_context() -> dict[str, Any]:
    """A representative market-context dict (with an honest ``None`` to render n/a)."""
    return {
        "regime": "trending_up",
        "drift_pct": 0.42,
        "spread_pct_at_entry": 0.03,
        "volume_z_score": None,
    }
