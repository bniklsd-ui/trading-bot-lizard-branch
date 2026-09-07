"""Tests for ``scripts.wiring._RebuildingBarStream`` (Phase 16 D1.2).

The wrapper exists to defeat a latent token-snapshot bug in
``IGLightstreamerClient``: it captures CST/XST at construction, so reusing the
same handle after the broker's ``_warm_session`` rotates the tokens yields an
auth-rejected LS subscription on the next keepalive — one CRITICAL per rotation,
directly into the A6 bucket. The wrapper defeats that by rebuilding the inner
object on every (re)start from a closure that reads the broker's CURRENT tokens.

Two contract cases (per Plan §6 D1.2 + §7 AK5b):

1. ``test_rebuilding_bar_stream_uses_fresh_tokens`` — a fresh build is invoked on
   every ``start()`` / ``restart()``, and the inner object ends up holding the
   CURRENT token (not the boot-time snapshot).
2. ``test_rebuilding_bar_stream_stop_before_start_is_noop`` — calling ``stop()``
   before any ``start()`` is a no-op (so a never-started arm or a pre-start
   shutdown is safe).

Setup mirrors ``test_wiring_schema_floor.py`` (Phase 16 B1) exactly:
``scripts/wiring.py`` is not an installed package, so we add ``phase8_scheduler/``
to ``sys.path`` here, the same way ``live_test.py`` does. The wrapper class is a
pure-Python helper with **no** cross-phase imports at module level — importing it
from a test is offline-safe.

No network, no keyring, no LLM, no real ``data/`` writes. Pure fakes.
"""

from __future__ import annotations

import sys
from pathlib import Path

# scripts/ -> phase8_scheduler/ (so ``from scripts.wiring import ...`` resolves)
_PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(_PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(_PROJECT_DIR))

from scripts.wiring import _RebuildingBarStream  # noqa: E402


class _FakeInner:
    """Duck-typed stand-in for ``TickAggregatorRecorder`` (or ``LSBarRecorder``).

    Records every ``start`` / ``stop`` and remembers the constructor argument
    (``token``) so the test can assert which build passed which value.
    """

    def __init__(self, token: str = "") -> None:
        self.token = token
        self.starts = 0
        self.stops = 0

    def start(self) -> None:
        self.starts += 1

    def stop(self) -> None:
        self.stops += 1


def test_rebuilding_bar_stream_uses_fresh_tokens() -> None:
    """``restart()`` must invoke the build_fn again and pass it the CURRENT token.

    Defends AK5b: after a broker-side session-token rotation, the runner's
    ``_restart_bar_stream`` must rebuild the inner LS client against the
    refreshed CST/XST, not reuse the stale boot-time snapshot. We simulate
    the rotation by mutating ``current_token[0]`` between start and restart,
    and verify the second build saw the new value.
    """
    current_token = ["cst-OLD"]
    build_count = 0
    token_seen: list[str] = []

    def _build() -> _FakeInner:
        nonlocal build_count
        build_count += 1
        token_seen.append(current_token[0])
        return _FakeInner(token=current_token[0])

    wrapper = _RebuildingBarStream(_build)

    # Initial start — uses the OLD token.
    wrapper.start()
    assert build_count == 1
    assert token_seen == ["cst-OLD"]
    first_inner = wrapper._inner
    assert first_inner is not None
    assert first_inner.token == "cst-OLD"
    assert first_inner.starts == 1
    assert first_inner.stops == 0

    # Simulate a broker-side token rotation (the _warm_session path).
    current_token[0] = "cst-NEW"

    # Restart — must rebuild with the NEW token, not reuse the old inner.
    wrapper.restart()
    assert build_count == 2
    assert token_seen == ["cst-OLD", "cst-NEW"]
    assert first_inner.stops == 1  # the old inner was stopped
    new_inner = wrapper._inner
    assert new_inner is not None
    assert new_inner.token == "cst-NEW"
    assert new_inner.starts == 1
    assert new_inner is not first_inner  # genuinely a fresh object


def test_rebuilding_bar_stream_stop_before_start_is_noop() -> None:
    """``stop()`` and ``restart()`` before any ``start()`` must not raise.

    Two on-ramps must be safe:
      * ``stop()`` on a freshly constructed wrapper (inner is ``None``).
      * ``restart()`` on a freshly constructed wrapper (stop on ``None``, then
        a real ``start()``).

    This mirrors a daemon that starts, never arms the bar stream, then shuts
    down — or a runner-path exception that hits ``_stop_bar_stream`` before
    the recorder was ever started.
    """
    build_count = 0

    def _build() -> _FakeInner:
        nonlocal build_count
        build_count += 1
        return _FakeInner(token="cst-INIT")

    wrapper = _RebuildingBarStream(_build)

    # Pre-start stop must be a no-op — must NOT raise.
    wrapper.stop()
    assert build_count == 0
    assert wrapper._inner is None

    # Pre-start restart is stop (no-op) then start — must build exactly once.
    wrapper.restart()
    assert build_count == 1
    assert wrapper._inner is not None
    assert wrapper._inner.token == "cst-INIT"
    assert wrapper._inner.starts == 1
