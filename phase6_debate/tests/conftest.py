"""Shared fixtures for the Phase-6 debate test suite.

Mocked, no network, no real LLM, no real credentials (project rule). Grows
per module, mirroring the Phase-4/5 conftest rhythm:

- Module 2 (``context_builder``): a duck-typed ``_FakeEnv`` (``.ok``/``.data`` —
  the Phase-1 envelope shape, deliberately **not** importing the real
  ``Envelope``, proving phase isolation), a ``make_bars`` helper, a configurable
  ``FakeBroker`` (``get_price``/``get_ohlcv``/``get_market_info``, invocation-
  recording), and a baseline ``candidate`` dict (the frozen Phase-4 contract).
- Module 6 (``debate`` orchestrator): a scripted ``FakeLLM`` standing in for the
  shared ``research.LLMClient`` — queued answers, configurable per-turn ``usage``
  (sets ``last_usage`` like the real client), settable ``model``/``temperature``/
  ``max_tokens``, and turn recording so tests can assert role order / budgets /
  the (compressed) transcript each turn saw. No SDK, no network.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import pytest

DEFAULT_EPIC = "IX.D.DAX.IFMM.IP"


@dataclass
class _FakeEnv:
    """Duck-typed stand-in for a Phase-1 ``Envelope`` — only ``.ok``/``.data``."""

    ok: bool
    data: dict[str, Any] | None = None


def make_bars(closes: list[float]) -> list[dict[str, Any]]:
    """Build ``get_ohlcv`` bar dicts from a list of closes.

    Mirrors the Phase-1 ``OHLCBar.__dict__`` shape
    (``timestamp, open, high, low, close, volume``); only ``close`` is read by the
    context builder's bar summary, so the other OHLC fields just echo the close.
    """
    return [
        {
            "timestamp": f"2026-06-15T09:{i:02d}:00Z",
            "open": c,
            "high": c,
            "low": c,
            "close": c,
            "volume": 0.0,
        }
        for i, c in enumerate(closes)
    ]


class FakeBroker:
    """Configurable, invocation-recording stand-in for the read-only broker.

    Exposes exactly the surface the context builder reads
    (``get_price``/``get_ohlcv``/``get_market_info``), each returning a preset
    ``_FakeEnv``. ``ohlcv_raises`` makes ``get_ohlcv`` raise (the fail-closed
    data-fault path). Invocation args are recorded so tests can assert each probe
    is read **exactly once**.
    """

    def __init__(
        self,
        *,
        price_env: _FakeEnv | None = None,
        ohlcv_env: _FakeEnv | None = None,
        market_info_env: _FakeEnv | None = None,
        ohlcv_raises: bool = False,
    ) -> None:
        self.price_env = price_env or _FakeEnv(
            ok=True,
            data={
                "epic": DEFAULT_EPIC,
                "bid": 17999.0,
                "ask": 18000.0,
                "spread": 1.0,
                "spread_pct": 0.03,
                "market_status": "TRADEABLE",
                "timestamp": "2026-06-15T09:05:00Z",
            },
        )
        self.ohlcv_env = ohlcv_env or _FakeEnv(
            ok=True, data={"bars": make_bars([18000.0, 18010.0, 18020.0])}
        )
        self.market_info_env = market_info_env or _FakeEnv(
            ok=True,
            data={
                "min_deal_size": 0.5,
                "currency": "EUR",
                "instrument_type": "CFD",
                "market_status": "TRADEABLE",
            },
        )
        self.ohlcv_raises = ohlcv_raises

        self.get_price_calls: list[str] = []
        self.get_ohlcv_calls: list[tuple[str, str, int]] = []
        self.get_market_info_calls: list[str] = []

    def get_price(self, epic: str) -> _FakeEnv:
        self.get_price_calls.append(epic)
        return self.price_env

    def get_ohlcv(self, epic: str, resolution: str, count: int) -> _FakeEnv:
        self.get_ohlcv_calls.append((epic, resolution, count))
        if self.ohlcv_raises:
            raise RuntimeError("simulated get_ohlcv fault")
        return self.ohlcv_env

    def get_market_info(self, epic: str) -> _FakeEnv:
        self.get_market_info_calls.append(epic)
        return self.market_info_env


_DEFAULT_USAGE: dict[str, Any] = {
    "input_tokens": 100,
    "output_tokens": 20,
    "cache_read_input_tokens": 0,
    "cache_creation_input_tokens": 0,
    "est_cost_usd": 0.001,
    "est_cost_eur": 0.0009,
}


class FakeLLM:
    """Scripted stand-in for the shared ``research.LLMClient`` (no SDK, no network).

    Returns ``answers`` in order from ``ask_candidate`` and sets ``last_usage`` to a
    copy of ``usage`` per turn (exactly what ``llm_caching.ask_agent`` reads back).
    The orchestrator sets ``model``/``temperature``/``max_tokens`` per turn; each is
    recorded in ``turns`` at request time, and the ``user`` message each turn saw is
    recorded in ``seen_users`` (so the compression test can assert the prompt view).
    ``raises_on`` makes the request at that 0-based index raise (the fail-closed
    request path). If the script runs out, the last answer is repeated.
    """

    def __init__(
        self,
        answers: list[dict[str, Any]],
        *,
        usage: dict[str, Any] | None = None,
        raises_on: int | None = None,
    ) -> None:
        self._answers = list(answers)
        self._i = 0
        self._usage = usage if usage is not None else dict(_DEFAULT_USAGE)
        self.raises_on = raises_on

        # set per turn by ask_agent (model/temperature) + the orchestrator (max_tokens)
        self.model = ""
        self.temperature = 0.0
        self.max_tokens = 0
        self.last_usage: dict[str, Any] | None = None

        self.turns: list[tuple[str, float, int]] = []  # (model, temperature, max_tokens)
        self.seen_users: list[str] = []

    def ask_candidate(self, system: str, user: str, json_schema: dict) -> dict:
        idx = self._i
        self._i += 1
        self.turns.append((self.model, self.temperature, self.max_tokens))
        self.seen_users.append(user)
        if self.raises_on is not None and idx == self.raises_on:
            raise RuntimeError("simulated LLM fault")
        self.last_usage = dict(self._usage)
        if idx >= len(self._answers):
            return self._answers[-1]
        return self._answers[idx]


@pytest.fixture
def make_candidate() -> Callable[..., dict[str, Any]]:
    """Factory for a Phase-4 candidate dict (the frozen P4→P5 contract keys)."""

    def _make(**overrides: Any) -> dict[str, Any]:
        candidate: dict[str, Any] = {
            "epic": DEFAULT_EPIC,
            "direction": "BUY",
            "llm_confidence": 62.0,
            "reasoning": "seed: bullish breakout on the DAX intraday range.",
            "spread_pct_at_pick": 0.05,
            "drift_at_pick": 0.42,
            "score_at_pick": 58.0,
            "threshold_applied": 55.0,
            "generated_at": "2026-06-15T09:00:00.000Z",
            "source": "research",
        }
        candidate.update(overrides)
        return candidate

    return _make


@pytest.fixture
def candidate(make_candidate: Callable[..., dict[str, Any]]) -> dict[str, Any]:
    """A baseline BUY candidate."""
    return make_candidate()


@pytest.fixture
def broker() -> FakeBroker:
    """A healthy, tradeable FakeBroker with three usable bars."""
    return FakeBroker()
