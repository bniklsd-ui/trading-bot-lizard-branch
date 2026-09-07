"""Tests for ``phase15_v4/instinct/bridge.py`` (Phase 16 D2.4).

Pins (Plan §6 D2.4):
- ``after_trade_closed`` never raises (best-effort).
- ``promote()`` returns ``[]`` when ``enable_instinct_promotion=False``.
- ``promote()`` honors ``promote_eligible`` semantics: gates on
  ``n_closed >= instinct_n_min``.
- ``load_rules()`` returns an empty tuple when no rows are promoted
  (AK9-Erbe).
- ``load_rules()`` returns compiled predicates when ``status='promoted'``
  rows exist.
- Per-instinct failures don't abort the whole batch.
- Extractor returning ``ok=False`` is logged INFO + no inserts.
"""

from __future__ import annotations

import sys
from typing import Any

import pytest


_REPO_ROOT = "/home/trading-bot/trading-bot"
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


from instinct.bridge import InstinctBridge  # noqa: E402
from instinct.models import InstinctConfig  # noqa: E402


class _FakeDB:
    """Minimal DB fake for bridge tests.

    Tracks inserts + status updates + returns canned lessons/rewards/count.
    Each method is parameterisable so tests can drive different scenarios
    (empty DB, extractor failure, n-closed-below-gate, etc.).
    """

    def __init__(
        self,
        *,
        lessons: list | None = None,
        rewards: list | None = None,
        n_closed: int = 0,
        validated_rows: list | None = None,
        promoted_rows: list | None = None,
        insert_raises: Exception | None = None,
    ) -> None:
        self.lessons = lessons or []
        self.rewards = rewards or []
        self.n_closed = n_closed
        self._validated = validated_rows or []
        self._promoted = promoted_rows or []
        self.inserted: list[dict] = []
        self.status_updates: list[tuple[int, str]] = []
        self.insert_raises = insert_raises
        self._next_id = 100

    # -- read methods ----------------------------------------------------
    def get_recent_lessons(self, n: int = 20) -> list[dict]:
        return list(self.lessons)

    def get_recent_rewards(self, n: int = 20) -> list[dict]:
        return list(self.rewards)

    def count_closed_trades(self) -> int:
        return self.n_closed

    def list_instincts(self, status: str | None = None, n: int | None = None) -> list[dict]:
        if status == "validated":
            return [dict(r) for r in self._validated]
        if status == "promoted":
            return [dict(r) for r in self._promoted]
        return []

    # -- write methods ---------------------------------------------------
    def insert_instinct(self, row: dict) -> int:
        if self.insert_raises is not None:
            raise self.insert_raises
        self._next_id += 1
        self.inserted.append(dict(row))
        return self._next_id

    def update_instinct_status(self, row_id: int, status: str) -> bool:
        self.status_updates.append((row_id, status))
        return True


class _FakeInstinctExtractionResult:
    __slots__ = ("ok", "instincts", "error")

    def __init__(self, ok: bool, instincts: list | None = None, error: str | None = None) -> None:
        self.ok = ok
        self.instincts = list(instincts) if instincts else []
        self.error = error


class _FakeExtractor:
    """Fake ``InstinctExtractor`` — returns whatever the test seeded."""

    def __init__(
        self,
        ok: bool = True,
        instincts: list | None = None,
        error: str | None = None,
        raise_exc: Exception | None = None,
    ) -> None:
        self._result = _FakeInstinctExtractionResult(ok, instincts, error)
        self.raise_exc = raise_exc
        self.calls: list[dict] = []

    def extract(self, *, lessons: list, rewards: list) -> Any:
        self.calls.append({"lessons": lessons, "rewards": rewards})
        if self.raise_exc is not None:
            raise self.raise_exc
        return self._result


class _FakeValidator:
    """Fake ``InstinctValidator`` — returns ``validated`` for every instinct."""

    def __init__(self, decision_value: str = "validated") -> None:
        self._decision = decision_value
        self.calls: list = []

    def validate(self, instinct):
        self.calls.append(instinct)
        class _D:
            def __init__(self, value: str) -> None:
                self.value = value
        return _D(self._decision)


# -- after_trade_closed: best-effort + never raises ------------------------


def test_after_trade_closed_calls_extractor_with_lessons_and_rewards() -> None:
    """Extractor sees the DB-returned lessons + rewards (one call per close)."""
    lessons = [{"id": 1, "text": "spread too wide"}]
    rewards = [{"id": 2, "score_after": 50.0}]
    db = _FakeDB(lessons=lessons, rewards=rewards)
    extractor = _FakeExtractor(ok=True, instincts=[])
    bridge = InstinctBridge(db=db, extractor=extractor, validator=_FakeValidator(), cfg=InstinctConfig())

    bridge.after_trade_closed(trade_id=42)

    assert len(extractor.calls) == 1
    assert extractor.calls[0]["lessons"] == lessons
    assert extractor.calls[0]["rewards"] == rewards


def test_after_trade_closed_never_raises_when_extractor_explodes() -> None:
    """Extractor raising must be swallowed (Critical + continue)."""
    db = _FakeDB()
    extractor = _FakeExtractor(raise_exc=RuntimeError("boom"))
    bridge = InstinctBridge(db=db, extractor=extractor, validator=_FakeValidator(), cfg=InstinctConfig())

    # The whole point: no exception escapes to the trade path.
    bridge.after_trade_closed(trade_id=1)


def test_after_trade_closed_never_raises_when_db_insert_explodes() -> None:
    """DB.insert_instinct raising must be swallowed at the per-instinct level."""
    from instinct.models import Instinct
    instincts = [Instinct(trigger="avoid BUY", domain="entry", status="proposed")]
    db = _FakeDB(insert_raises=RuntimeError("db down"))
    extractor = _FakeExtractor(ok=True, instincts=instincts)
    bridge = InstinctBridge(db=db, extractor=extractor, validator=_FakeValidator(), cfg=InstinctConfig())

    # Per-instinct resilience — must not raise.
    bridge.after_trade_closed(trade_id=1)


def test_after_trade_closed_skips_silently_on_extractor_failure(caplog) -> None:
    """Extractor returning ok=False logs INFO and produces no inserts."""
    import logging
    db = _FakeDB()
    extractor = _FakeExtractor(ok=False, error="llm 400")
    bridge = InstinctBridge(db=db, extractor=extractor, validator=_FakeValidator(), cfg=InstinctConfig())

    with caplog.at_level(logging.INFO, logger="instinct.bridge"):
        bridge.after_trade_closed(trade_id=1)

    assert len(db.inserted) == 0
    assert any("extractor returned ok=False" in r.message for r in caplog.records)


def test_after_trade_closed_inserts_proposed_and_updates_to_validated() -> None:
    """Happy path: extract → insert → validator validated → status update."""
    from instinct.models import Instinct
    instincts = [
        Instinct(trigger="avoid BUY", domain="entry", status="proposed", evidence_trade_ids=(1, 2)),
        Instinct(trigger="avoid SELL", domain="entry", status="proposed", evidence_trade_ids=(3,)),
    ]
    db = _FakeDB()
    extractor = _FakeExtractor(ok=True, instincts=instincts)
    validator = _FakeValidator(decision_value="validated")
    bridge = InstinctBridge(db=db, extractor=extractor, validator=validator, cfg=InstinctConfig())

    bridge.after_trade_closed(trade_id=1)

    # Both instincts inserted, then both updated to 'validated'.
    assert len(db.inserted) == 2
    assert len(db.status_updates) == 2
    for _row_id, new_status in db.status_updates:
        assert new_status == "validated"
    # Validator was called once per instinct.
    assert len(validator.calls) == 2


# -- promote --------------------------------------------------------------


def test_promote_disabled_returns_empty_list() -> None:
    """``enable_instinct_promotion=False`` ⇒ no promotion (master switch)."""
    cfg = InstinctConfig(instinct_n_min=50, enable_instinct_promotion=False)
    db = _FakeDB(validated_rows=[{"id": 1, "trigger": "avoid BUY", "domain": "entry"}])
    bridge = InstinctBridge(db=db, extractor=_FakeExtractor(), validator=_FakeValidator(), cfg=cfg)

    assert bridge.promote() == []
    assert len(db.status_updates) == 0  # nothing promoted


def test_promote_below_n_closed_returns_empty_list() -> None:
    """``n_closed < instinct_n_min`` ⇒ no promotion (P12 gate)."""
    cfg = InstinctConfig(instinct_n_min=50, enable_instinct_promotion=True)
    db = _FakeDB(
        validated_rows=[{"id": 1, "trigger": "avoid BUY", "domain": "entry"}],
        n_closed=8,  # << 50
    )
    bridge = InstinctBridge(db=db, extractor=_FakeExtractor(), validator=_FakeValidator(), cfg=cfg)

    assert bridge.promote() == []
    assert len(db.status_updates) == 0


def test_promote_above_n_closed_promotes_validated_rows() -> None:
    """``n_closed >= instinct_n_min`` ⇒ validated rows promoted."""
    cfg = InstinctConfig(instinct_n_min=50, enable_instinct_promotion=True)
    db = _FakeDB(
        validated_rows=[
            {"id": 1, "trigger": "avoid BUY", "domain": "entry", "status": "validated"},
            {"id": 2, "trigger": "avoid SELL", "domain": "entry", "status": "validated"},
        ],
        n_closed=100,
    )
    bridge = InstinctBridge(db=db, extractor=_FakeExtractor(), validator=_FakeValidator(), cfg=cfg)

    promoted_ids = bridge.promote()
    assert sorted(promoted_ids) == [1, 2]
    assert db.status_updates == [(1, "promoted"), (2, "promoted")]


def test_promote_never_raises_on_db_failure() -> None:
    """``list_instincts`` raising must not propagate (best-effort)."""
    class _BrokenDB(_FakeDB):
        def list_instincts(self, status: str | None = None, n: int | None = None) -> list[dict]:
            raise RuntimeError("db down")
    cfg = InstinctConfig(instinct_n_min=50, enable_instinct_promotion=True)
    bridge = InstinctBridge(db=_BrokenDB(), extractor=_FakeExtractor(), validator=_FakeValidator(), cfg=cfg)
    assert bridge.promote() == []


# -- load_rules ------------------------------------------------------------


def test_load_rules_empty_db_returns_empty_tuple() -> None:
    """No promoted rows ⇒ empty tuple (AK9-Erbe)."""
    db = _FakeDB()
    bridge = InstinctBridge(db=db, extractor=_FakeExtractor(), validator=_FakeValidator(), cfg=InstinctConfig())
    assert bridge.load_rules() == ()


def test_load_rules_compiles_promoted_into_predicates() -> None:
    """Promoted rows compile into real predicates that fire on candidates."""
    db = _FakeDB(
        promoted_rows=[
            {"id": 1, "trigger": "avoid BUY", "domain": "entry", "status": "promoted",
             "evidence_trade_ids_json": "[]", "contradictions_trade_ids_json": "[]"},
        ]
    )
    bridge = InstinctBridge(db=db, extractor=_FakeExtractor(), validator=_FakeValidator(), cfg=InstinctConfig())

    preds = bridge.load_rules()
    assert len(preds) == 1
    assert preds[0]({"direction": "BUY", "epic": "IX.D.DAX.IFMM.IP"}) is True


def test_load_rules_never_raises_on_failure() -> None:
    class _BrokenDB(_FakeDB):
        def list_instincts(self, status: str | None = None, n: int | None = None) -> list[dict]:
            raise RuntimeError("db down")
    bridge = InstinctBridge(
        db=_BrokenDB(), extractor=_FakeExtractor(), validator=_FakeValidator(), cfg=InstinctConfig()
    )
    assert bridge.load_rules() == ()
