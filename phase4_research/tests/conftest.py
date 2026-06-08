"""Shared pytest fixtures for the Phase-4 research tests.

No network, no real credentials, no real LLM. This file grows step-by-step:
Step 2 added a ``FakeBroker`` (for the validator's live-spread recheck) and a
sample ``universe``. Step 3 extends ``FakeBroker`` with ``get_market_info`` and
adds ``FakeDB`` / ``FakeFetcher`` (for ``context_builder``). ``FakeLLM`` arrives
with Step 5, mirroring the Phase-3 conftest rhythm.
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
    """Configurable broker whose ``get_price`` / ``get_market_info`` drive probes.

    Construct with the desired recheck outcome; every ``get_price`` call returns
    that same env (the validator issues exactly one recheck per validation; the
    context builder probes once per allow-listed epic). Defaults to a healthy
    TRADEABLE EUR quote with a small spread.

    ``get_price`` is the Step-2 surface (validator live recheck). ``get_market_info``
    is the Step-3 addition (context-builder universe probe): a separate ``info_ok``
    / ``currency`` / ``min_deal_size`` / ``name`` config so a test can fail the
    market-info leg independently of the price leg.
    """

    def __init__(
        self,
        *,
        ok: bool = True,
        spread_pct: float | None = 0.03,
        market_status: str | None = "TRADEABLE",
        info_ok: bool = True,
        currency: str | None = "EUR",
        min_deal_size: float = 0.5,
        name: str = "Germany 40 Cash (1 EUR)",
    ) -> None:
        self._ok = ok
        self._spread_pct = spread_pct
        self._market_status = market_status
        self._info_ok = info_ok
        self._currency = currency
        self._min_deal_size = min_deal_size
        self._name = name
        self.calls: list[str] = []
        self.info_calls: list[str] = []

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

    def get_market_info(self, epic: str) -> _FakeEnv:
        self.info_calls.append(epic)
        if not self._info_ok:
            return _FakeEnv(ok=False, data=None)
        return _FakeEnv(
            ok=True,
            data={
                "epic": epic,
                "name": self._name,
                "instrument_type": "INDICES",
                "currency": self._currency,
                "expiry": None,
                "min_deal_size": self._min_deal_size,
                "lot_size": 1.0,
                "market_status": self._market_status,
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


# --------------------------------------------------------------------------- #
# Step 3 — context-builder collaborators (Phase-2 DB + Phase-3 fetcher)        #
# --------------------------------------------------------------------------- #


class EpicNotMappedError(Exception):
    """Local stand-in for Phase-3's ``EpicNotMappedError``.

    The context builder catches the real one **by class name** (phase isolation —
    it never imports ``external_data``). A test raising this same-named local
    exception exercises that guard without pulling Phase 3 onto the path.
    """


class FakeDB:
    """Configurable Phase-2 ``Database`` stand-in for the context reads.

    Each accessor returns its configured value; ``get_recent_trades`` /
    ``get_recent_lessons`` record the requested ``n`` so a test can assert the
    8/5 limits.
    """

    def __init__(
        self,
        *,
        trades: list[dict[str, Any]] | None = None,
        lessons: list[dict[str, Any]] | None = None,
        score: float = 55.0,
        risk_level: str = "AGGRESSIV",
    ) -> None:
        self._trades = trades if trades is not None else []
        self._lessons = lessons if lessons is not None else []
        self._score = score
        self._risk_level = risk_level
        self.trade_n: list[int] = []
        self.lesson_n: list[int] = []

    def get_recent_trades(self, n: int = 8) -> list[dict[str, Any]]:
        self.trade_n.append(n)
        return list(self._trades)

    def get_recent_lessons(self, n: int = 5) -> list[dict[str, Any]]:
        self.lesson_n.append(n)
        return list(self._lessons)

    def get_current_score(self) -> float:
        return self._score

    def get_risk_level(self) -> str:
        return self._risk_level


class _FakeBrainContext:
    """Wraps a prompt dict so the builder can call ``to_prompt_dict()`` on it."""

    def __init__(self, prompt_dict: dict[str, Any]) -> None:
        self._prompt_dict = prompt_dict

    def to_prompt_dict(self) -> dict[str, Any]:
        return dict(self._prompt_dict)


class FakeFetcher:
    """Configurable Phase-3 ``MarketDataFetcher`` stand-in.

    ``get_brain_context`` returns a :class:`_FakeBrainContext` wrapping the
    configured prompt dict, or ``None`` (``returns_none``), or raises the
    configured exception (e.g. the local :class:`EpicNotMappedError`).
    """

    def __init__(
        self,
        *,
        prompt_dict: dict[str, Any] | None = None,
        returns_none: bool = False,
        raises: Exception | None = None,
    ) -> None:
        self._prompt_dict = prompt_dict
        self._returns_none = returns_none
        self._raises = raises
        self.calls: list[str] = []

    def get_brain_context(self, epic: str) -> Any:
        self.calls.append(epic)
        if self._raises is not None:
            raise self._raises
        if self._returns_none or self._prompt_dict is None:
            return None
        return _FakeBrainContext(self._prompt_dict)


def _make_prompt_dict(**overrides: Any) -> dict[str, Any]:
    """Build a realistic 10-key Phase-3 ``to_prompt_dict()`` (overridable)."""
    base: dict[str, Any] = {
        "ticker": DEFAULT_EPIC,
        "drift_pct": 0.42,
        "momentum_15m_pct": 0.11,
        "momentum_is_realtime": False,
        "volume_z_score": -1.36,
        "volume_available": True,
        "distance_to_high_pct": -1.2,
        "distance_to_low_pct": 3.8,
        "range_30d": {"low": 17500.0, "high": 18400.0},
        "generated_at": "2026-06-05T09:30:00.000Z",
    }
    base.update(overrides)
    return base


@pytest.fixture
def db() -> FakeDB:
    """A healthy default DB (some trades + lessons, neutral-ish score)."""
    return FakeDB(
        trades=[
            {"id": 2, "epic": DEFAULT_EPIC, "direction": "BUY", "profit_loss": 12.5},
            {"id": 1, "epic": DEFAULT_EPIC, "direction": "SELL", "profit_loss": -4.0},
        ],
        lessons=[{"id": 7, "lesson_text": "Trend day; held to target."}],
        score=55.0,
        risk_level="AGGRESSIV",
    )


@pytest.fixture
def prompt_dict() -> dict[str, Any]:
    """A full 10-key Phase-3 prompt dict (all indicators present)."""
    return _make_prompt_dict()


@pytest.fixture
def fetcher(prompt_dict: dict[str, Any]) -> FakeFetcher:
    """A fetcher returning the full brain context."""
    return FakeFetcher(prompt_dict=prompt_dict)


@pytest.fixture
def research_context(
    universe: list[dict[str, Any]], prompt_dict: dict[str, Any]
):
    """A fully-populated ``ResearchContext`` built **directly** (Step 4 prompt tests).

    Constructed without ``build_context`` so the prompt tests don't depend on the
    Step-3 builder. Imported lazily to keep the module import free of `research`
    side effects (consistent with the other fakes here being import-light).
    """
    from research.models import ResearchContext

    return ResearchContext(
        tradeable_epics=list(universe),
        recent_trades=[
            {
                "session_date": "2026-06-04",
                "direction": "BUY",
                "epic": DEFAULT_EPIC,
                "profit_loss": 12.5,
                "status": "CLOSED",
            },
            {
                "session_date": "2026-06-03",
                "direction": "SELL",
                "epic": DEFAULT_EPIC,
                "profit_loss": -4.0,
                "status": "CLOSED",
            },
        ],
        recent_lessons=[{"lesson_text": "Trend day; held to target."}],
        bot_score=55.0,
        risk_level="AGGRESSIV",
        brain_context=dict(prompt_dict),
        anchor_epic=DEFAULT_EPIC,
    )


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


# --------------------------------------------------------------------------- #
# Step 5 — LLM-client collaborators (mocked SDK surface; no network, no SDK)   #
# --------------------------------------------------------------------------- #


@dataclass
class _FakeUsage:
    """Duck-typed stand-in for an Anthropic ``usage`` object (token meter)."""

    input_tokens: int = 120
    output_tokens: int = 40
    cache_creation_input_tokens: int | None = None
    cache_read_input_tokens: int | None = None


@dataclass
class _FakeTextBlock:
    """A single ``type="text"`` content block of an Anthropic ``Message``."""

    text: str
    type: str = "text"


@dataclass
class _FakeMessage:
    """Duck-typed Anthropic ``Message`` — only ``content`` + ``usage`` are read."""

    content: list[Any]
    usage: _FakeUsage = field(default_factory=_FakeUsage)


def make_message(payload: dict[str, Any], *, fenced: bool = False,
                 usage: _FakeUsage | None = None) -> _FakeMessage:
    """Build a ``_FakeMessage`` whose single text block is ``json.dumps(payload)``.

    With ``fenced=True`` the JSON is wrapped in a ```json … ``` fence (exercises
    the fallback path's fence-strip).
    """
    import json as _json

    body = _json.dumps(payload)
    if fenced:
        body = f"```json\n{body}\n```"
    return _FakeMessage(
        content=[_FakeTextBlock(text=body)],
        usage=usage if usage is not None else _FakeUsage(),
    )


def make_text_message(text: str, *, usage: _FakeUsage | None = None) -> _FakeMessage:
    """Build a ``_FakeMessage`` with arbitrary (possibly non-JSON) text."""
    return _FakeMessage(
        content=[_FakeTextBlock(text=text)],
        usage=usage if usage is not None else _FakeUsage(),
    )


# Test-only exception classes. The client classifies faults BY CLASS NAME
# (phase-isolation pattern — it never imports ``anthropic``), so these names
# matter: ``BadRequestError`` → structured-output fallback; an unrecognised name
# with no transient status → non-transient (no retry).
class BadRequestError(Exception):
    """Stand-in for ``anthropic.BadRequestError`` (HTTP 400)."""

    status_code = 400


class AuthenticationError(Exception):
    """Stand-in for ``anthropic.AuthenticationError`` (HTTP 401, non-transient)."""

    status_code = 401


class FakeRawCall:
    """Scripted stand-in for ``LLMClient._raw_call``.

    Construct with a list of *actions*; each call pops the next one and either
    returns it (a ``_FakeMessage``) or raises it (an ``Exception`` instance).
    Records every call's ``json_schema`` kwarg so tests can assert the
    structured-vs-plain path and the call count (retry behaviour).
    """

    def __init__(self, actions: list[Any]) -> None:
        self._actions = list(actions)
        self.calls: list[dict[str, Any]] = []

    def __call__(self, system: str, user: str, *, json_schema: Any) -> Any:
        self.calls.append({"system": system, "user": user, "json_schema": json_schema})
        action = self._actions.pop(0)
        if isinstance(action, BaseException):
            raise action
        return action


class FakeLLM:
    """Stand-in implementing ``ask_candidate`` for the Step-7 orchestrator tests.

    Returns a configured raw dict (or raises a configured exception), recording
    the prompts it was asked with. Not used by the Step-5 client tests (those
    drive the real ``LLMClient`` via :class:`FakeRawCall`), but lands now per the
    conftest growth plan so Step 7 can wire it without touching this file.
    """

    def __init__(self, raw: dict[str, Any] | None = None,
                 raises: Exception | None = None) -> None:
        self._raw = raw if raw is not None else {"abstain": True, "reasoning": "n/a"}
        self._raises = raises
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def ask_candidate(self, system: str, user: str, json_schema: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((system, user, json_schema))
        if self._raises is not None:
            raise self._raises
        return dict(self._raw)
