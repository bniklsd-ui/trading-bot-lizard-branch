"""Import-smoke tests for ``scripts.wiring._build_reward_sink`` (Phase 16, Block E pre-step).

**Why this file exists.** ``scripts/wiring.py`` is documented as "operator-run, not
pytest-collected" (module docstring, last paragraph) — so every wiring edit shipped without an
integration test. Phase-16 commit ``bfab841`` (D2.6) rewrote 5 lines of ``_build_reward_sink``
and put a bug in every one of them: a ``ModuleNotFoundError`` (Phase-15 not on the runtime
path), five ``intinct``/``instinct`` typos, and one wrong ``SingleShotInstinctExtractor``
signature. Each surfaced one-at-a-time on an operator daemon restart, costing four rounds.

These tests are the choke point that catches all of them at once. They are cheap because every
constructor in the chain — ``LLMClient``, ``Scorer``, ``Brain``, ``RewardSink``,
``SingleShotInstinctExtractor``, ``InstinctValidator``, ``InstinctBridge`` — is pure attribute
binding (verified 2026-09-07); the Anthropic SDK and the IG session are lazy. The single impure
call is the keyring read, stubbed below.

Setup mirrors ``test_wiring_schema_floor.py``: ``phase8_scheduler/`` onto ``sys.path`` so
``from scripts.wiring import ...`` resolves. No network, no keyring, no LLM, no ``data/`` writes.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Any

import pytest

# scripts/ -> phase8_scheduler/ (so ``from scripts.wiring import ...`` resolves)
_PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(_PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(_PROJECT_DIR))

from scripts.wiring import _build_reward_sink  # noqa: E402


class _FakeDB:
    """Records the bridge's reads instead of touching SQLite.

    Recording, not just returning empties: ``InstinctBridge.promote`` and ``load_rules`` both
    swallow **every** exception and return ``[]`` / ``()`` (bridge.py:201, 216). Against a bare
    sentinel a broken call would look identical to a working one. Asserting the calls landed
    proves the real path ran rather than the ``except`` arm.
    """

    def __init__(self) -> None:
        self.calls: list[tuple[Any, ...]] = []

    def list_instincts(self, status: str) -> list[dict[str, Any]]:
        self.calls.append(("list_instincts", status))
        return []

    def count_closed_trades(self) -> int:
        self.calls.append(("count_closed_trades",))
        return 0


@pytest.fixture
def no_keyring(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub ``reward.credentials`` in ``sys.modules`` before the lazy import runs.

    ``_build_reward_sink`` does ``from reward.credentials import get_credential`` inside the
    function body, and that consults ``sys.modules`` first — so the stub wins and the real
    module (which imports ``keyring``) is never loaded. Phase-7's own docstring states unit
    tests must not import it; this keeps that promise. ``monkeypatch.setitem`` is mandatory,
    not style: a leaked ``sys.modules`` entry would poison the other 256 Phase-8 tests running
    in the same process.
    """
    monkeypatch.setitem(
        sys.modules,
        "reward.credentials",
        types.SimpleNamespace(get_credential=lambda *a, **k: "fake-key-not-a-secret"),
    )


def test_build_reward_sink_returns_sink_and_bridge(no_keyring: None) -> None:
    """The regression test for all four ``bfab841`` bugs — one call trips every one of them.

    ModuleNotFoundError (``from instinct import ...``), both ``NameError`` typos, and the
    ``TypeError`` from the wrong extractor signature all fire on this single invocation.
    """
    broker, db = object(), _FakeDB()

    sink, bridge = _build_reward_sink(broker, db)

    assert type(sink).__name__ == "RewardSink"
    assert type(bridge).__name__ == "InstinctBridge"
    # Identity, not truthiness: catches a future broker/db argument swap.
    assert sink.db is db
    assert sink.broker is broker
    assert bridge.db is db


def test_instinct_hook_is_bound_to_the_returned_bridge(no_keyring: None) -> None:
    """The D2.6 contract itself: the sink's close-seam hook must be *this* bridge's method.

    Phase-16 D2.6 exists to route ``RewardSink._on_trade_closed`` into extract → validate →
    promote. A hook bound to some other object, or left ``None``, would leave the sink working
    and the Promotion-Bridge silently dead — green tests, no instincts. Checking ``__self__``
    is what distinguishes "wired" from "constructed".
    """
    sink, bridge = _build_reward_sink(object(), _FakeDB())

    assert sink.instinct_hook is not None
    assert sink.instinct_hook.__self__ is bridge
    assert sink.instinct_hook.__func__.__name__ == "after_trade_closed"


def test_bridge_promote_and_load_rules_run_for_real(no_keyring: None) -> None:
    """Covers hunk 3 of ``bfab841`` — the two calls ``build_scheduler`` makes on the bridge.

    ``build_scheduler`` (wiring.py:888-890) calls ``promote()`` then ``load_rules()`` to seed
    ``exec_cfg.longterm_rules``. Those live outside ``_build_reward_sink``, so the test above
    would not notice if Phase-15 renamed either method — and because both swallow exceptions,
    a rename fails **silently** into a permanently empty rule set. Asserting the recorded db
    reads is the only way to tell the live path from the ``except`` arm.

    Empty results are the correct expectation today (AK9-Erbe: ``longterm_rules == ()``).
    """
    _, bridge = _build_reward_sink(object(), db := _FakeDB())

    assert bridge.promote() == []
    assert bridge.load_rules() == ()
    assert ("list_instincts", "validated") in db.calls
    assert ("count_closed_trades",) in db.calls
    assert ("list_instincts", "promoted") in db.calls


def test_extractor_has_own_client_with_instinct_limits(no_keyring: None) -> None:
    """Phase 17 B-3 (D3): the InstinctExtractor must own a **separate** LLM
    client with its own ``max_tokens`` / ``timeout_s``, distinct from the
    Brain's client.

    Without this, the instinct payload (a structured array of ``Instinct``
    objects) gets clipped by the Brain's tighter ``lesson_max_tokens`` and
    hangs on the Brain's shorter ``lesson_timeout_s`` — both wrong for the
    task. The two clients share the same model + key + token meter, so a
    future change to ``build_scheduler`` accidentally routing both through
    one client must fail loudly here.

    Pins (``phase8_scheduler/scripts/wiring.py``): the module-level
    constants ``_INSTINCT_EXTRACTOR_MAX_TOKENS = 2048`` and
    ``_INSTINCT_EXTRACTOR_TIMEOUT_S = 60.0`` are the values ``_build_reward_sink``
    reads when it builds the Extractor's client.
    """
    sink, bridge = _build_reward_sink(object(), _FakeDB())

    # Brain stores its LLM under ``self._llm`` (brain.py:184); the Extractor
    # mirrors that attribute name (extractor.py:262). Reading both confirms
    # they are distinct instances while the per-call limits match the
    # module-level constants.
    brain_llm = sink.brain._llm
    instinct_llm = bridge.extractor._llm

    assert instinct_llm is not brain_llm, (
        "Bridge.Extractor and Sink.Brain must not share an LLM client — "
        "D3 calls for separate per-call max_tokens / timeout_s"
    )
    assert instinct_llm.max_tokens == 2048
    assert instinct_llm.timeout_s == 60.0
    # Both clients stay on the same model + key + token meter (the whole
    # point of separation is the per-call knob values, not the model).
    assert instinct_llm.model == brain_llm.model
    assert instinct_llm.token_meter_path == brain_llm.token_meter_path
