"""Shared fixtures for the Phase-7 reward test suite.

Mocked, no network, no real LLM, no real credentials (project rule). Grows per
module, mirroring the Phase-4/5/6 conftest rhythm. Steps 3–6 (models / confidence /
scorer / synthetic) were pure math and needed no fakes; **Step 7 introduces the first
P7 fake** — a scripted ``FakeLLM`` standing in for the shared ``research.LLMClient``
(the brain's only collaborator). **Steps 8–9 add the broker/DB fakes** — a scripted
``FakeBroker`` (only ``get_trade_history`` is used, returning an Envelope-shaped
object) and a ``FakeDB`` recording the Phase-2 CRUD calls — plus factories for the
contract dataclasses (``make_closed`` / ``make_opened`` / ``make_reward``) and a
``make_tx`` history-row builder.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import pytest

from reward.models import ClosedTrade, LessonResult, OpenedTrade, RewardResult

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


# ---------------------------------------------------------------------------
# Envelope / broker fakes (Steps 8–9) — duck-typed ``.ok`` / ``.data`` only
# ---------------------------------------------------------------------------


@dataclass
class FakeEnvelope:
    """Minimal stand-in for ``broker_wrapper.envelope.Envelope`` (``.ok`` / ``.data``).

    The reward layer only ever reads ``.ok`` (guard) then ``.data`` (contract 1.6) —
    it never imports the real Envelope (phase isolation).
    """

    ok: bool
    data: Any | None = None


class FakeBroker:
    """Scripted broker stand-in — only ``get_trade_history`` is exercised (Step 9).

    ``transactions`` is the list of ``Transaction.__dict__``-shaped history rows the
    next call returns (use ``make_tx``). ``ok=False`` returns a not-ok envelope (the
    ``pnl_resolver`` must treat that as unavailable). The reward sink is **never**
    handed an order/close path — this fake deliberately exposes nothing but read-only
    history (Decision: the sink can never bypass a VETO because it references none).
    """

    def __init__(
        self,
        transactions: list[dict[str, Any]] | None = None,
        *,
        ok: bool = True,
        responses: list[list[dict[str, Any]]] | None = None,
    ) -> None:
        self._transactions = list(transactions or [])
        # ``responses`` scripts a *different* row set per successive call (the last is
        # repeated) — used to simulate IG history lag clearing between the in-cycle close
        # and a later reconcile (e.g. ``[[], [make_tx()]]`` = empty, then a match).
        self._responses = [list(r) for r in responses] if responses is not None else None
        self._ok = ok
        self.history_calls = 0
        self.last_days: int | None = None

    def get_trade_history(self, days: int = 30) -> FakeEnvelope:
        self.history_calls += 1
        self.last_days = days
        if not self._ok:
            return FakeEnvelope(ok=False, data=None)
        if self._responses is not None:
            idx = min(self.history_calls - 1, len(self._responses) - 1)
            txs = list(self._responses[idx])
        else:
            txs = list(self._transactions)
        return FakeEnvelope(ok=True, data={"transactions": txs})


def make_tx(**overrides: Any) -> dict[str, Any]:
    """Build one ``get_trade_history`` row (the ``Transaction.__dict__`` shape, 1.1).

    Defaults to a +30pt winning DAX deal. Note the deliberately *unhelpful* match
    keys the resolver must ignore: ``epic`` is the **instrumentName** (display name,
    not the epic code) and ``direction`` is **hardcoded None**.
    """
    tx: dict[str, Any] = {
        "transaction_id": "REF-1",
        "epic": "Germany 40 Cash",  # instrumentName, NOT the epic code
        "direction": None,  # IG hardcodes this to None
        "size": 1.0,
        "open_level": 18000.0,
        "close_level": 18030.0,
        "profit_loss": 30.0,
        "currency": "EUR",
        "open_date": "2026-06-19T13:00:00",
        "close_date": "2026-06-19T15:30:00",
        "transaction_type": "DEAL",
    }
    tx.update(overrides)
    return tx


# ---------------------------------------------------------------------------
# DB + brain fakes (Step 8 recorder orchestration)
# ---------------------------------------------------------------------------


class FakeDB:
    """In-memory stand-in for the Phase-2 ``Database`` (records the CRUD the recorder makes).

    Only the methods the recorder calls are implemented (``insert_trade`` /
    ``update_trade_close`` / ``get_trade_by_deal_id`` / ``get_current_score`` /
    ``insert_reward`` / ``insert_lesson``); each mirrors the real semantics (status
    default OPEN, ``id`` PK on the row, ``get_current_score`` follows the latest
    reward). ``fail_on`` injects a ``RuntimeError`` from the named method(s) so the
    fail-closed (Decision J) paths can be exercised. Every call name is appended to
    ``calls`` for assertions.
    """

    def __init__(self, *, fail_on: set[str] | None = None, start_score: float = 50.0) -> None:
        self._fail_on = set(fail_on or ())
        self._trades: dict[str, dict[str, Any]] = {}  # deal_id -> row
        self._next_id = 1
        self.score = start_score
        self.rewards: list[tuple[int, dict[str, Any]]] = []
        self.lessons: list[tuple[int, dict[str, Any]]] = []
        self.closes: list[tuple[str, dict[str, Any]]] = []
        self.calls: list[str] = []

    def _maybe_fail(self, name: str) -> None:
        self.calls.append(name)
        if name in self._fail_on:
            raise RuntimeError(f"injected failure in {name}")

    def insert_trade(self, trade: dict[str, Any]) -> int:
        self._maybe_fail("insert_trade")
        tid = self._next_id
        self._next_id += 1
        row = dict(trade)
        row.setdefault("status", "OPEN")
        row["id"] = tid
        self._trades[trade["deal_id"]] = row
        return tid

    def update_trade_close(self, deal_id: str, close_data: dict[str, Any]) -> bool:
        self._maybe_fail("update_trade_close")
        row = self._trades.get(deal_id)
        if row is None:
            return False
        row["status"] = close_data.get("status", "CLOSED")
        row["close_level"] = close_data.get("close_level")
        row["profit_loss"] = close_data.get("profit_loss")
        row["close_ts"] = close_data.get("close_ts")
        self.closes.append((deal_id, dict(close_data)))
        return True

    def get_trade_by_deal_id(self, deal_id: str) -> dict[str, Any] | None:
        self._maybe_fail("get_trade_by_deal_id")
        row = self._trades.get(deal_id)
        return dict(row) if row is not None else None

    def get_open_trades(self) -> list[dict[str, Any]]:
        self._maybe_fail("get_open_trades")
        return [dict(r) for r in self._trades.values() if r.get("status") == "OPEN"]

    def get_current_score(self) -> float:
        self._maybe_fail("get_current_score")
        return self.score

    def insert_reward(self, trade_id: int, reward: dict[str, Any]) -> int:
        self._maybe_fail("insert_reward")
        self.rewards.append((trade_id, dict(reward)))
        if "score_after" in reward and reward["score_after"] is not None:
            self.score = float(reward["score_after"])
        return len(self.rewards)

    def insert_lesson(self, trade_id: int, lesson: dict[str, Any]) -> int:
        self._maybe_fail("insert_lesson")
        self.lessons.append((trade_id, dict(lesson)))
        return len(self.lessons)

    def update_trade_resolve_attempt(self, deal_id: str, iso_utc: str) -> None:
        """P12-Reconcile-Timing (Mini-Session 26): stamp the backoff slot."""
        self._maybe_fail("update_trade_resolve_attempt")
        row = self._trades.get(deal_id)
        if row is not None:
            row["last_resolve_attempt_utc"] = iso_utc


class FakeBrain:
    """Scripted lesson extractor (the recorder's ``brain`` collaborator, Step 7 surface).

    Returns ``result`` (default: a successful lesson echoing the passed
    ``market_context``) from ``reflect``; ``raises_exc`` makes it raise (to prove the
    recorder wraps the brain best-effort even though the real ``Brain`` never raises).
    Records each call's ``(closed, outcome, market_context)`` in ``calls``.
    """

    def __init__(
        self,
        result: LessonResult | None = None,
        *,
        raises_exc: BaseException | None = None,
    ) -> None:
        self._result = result
        self.raises_exc = raises_exc
        self.calls: list[tuple[Any, Any, dict[str, Any]]] = []

    def reflect(self, closed: Any, outcome: Any, market_context: dict[str, Any]) -> LessonResult:
        self.calls.append((closed, outcome, market_context))
        if self.raises_exc is not None:
            raise self.raises_exc
        if self._result is not None:
            return self._result
        return LessonResult(
            lesson_text="cut losers faster on time-stops",
            market_context=market_context,
            ok=True,
            error=None,
        )


@pytest.fixture
def make_opened() -> Callable[..., OpenedTrade]:
    """Factory for an :class:`OpenedTrade` (overridable fields)."""

    def _make(**overrides: Any) -> OpenedTrade:
        fields: dict[str, Any] = {
            "deal_reference": "bot-abc123",
            "deal_id": "DIAAAAXQ6CSGTA5",
            "epic": "IX.D.DAX.IFMM.IP",
            "direction": "BUY",
            "size": 1.0,
            "intended_open_level": 18000.0,
            "stop_level": 17970.0,
            "limit_level": 18045.0,
            "currency": "EUR",
            "initial_risk": 30.0,
            "research_confidence": 0.7,
            "debate_confidence": 0.62,
            "gate_path": {"gate1": True, "gate2": True},
            "spread_at_entry_pct": 0.03,
            "score_at_open": 50.0,
            "session_date": "2026-06-19",
            "open_ts": "2026-06-19T13:00:00.000Z",
            "account": "demo",
        }
        fields.update(overrides)
        return OpenedTrade(**fields)

    return _make


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
