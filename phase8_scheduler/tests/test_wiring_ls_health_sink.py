"""Regression tests for ``scripts.wiring._ls_health_sink`` (Phase 16, R1 / Drift #12).

**Why this file exists.** ``wiring.py:1240`` called ``record_event`` in the LS bar-stream
health sink without importing it — every other call site in this module imports it locally
(Z. 230/653/756/791/906/1136), this one didn't. The call sat inside a closure three levels
deep (``_build_recorder`` inside ``build_scheduler``) that needs a live broker to reach, so no
test exercised it; it ran to a ``NameError`` on every bar write in production for the life of
the feature (4 368 060 tracebacks, Phase-13 commit ``a58a352`` onward). ``_ls_health_sink`` is
the extraction that makes the import testable at module level, same pattern as
``test_wiring_reward_sink.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(_PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(_PROJECT_DIR))

from scripts.wiring import _ls_health_sink  # noqa: E402


def test_ls_health_sink_records_event(tmp_path: Path) -> None:
    """A real event reaches the observability file — proves the sink is wired, not a stub."""
    obs_path = tmp_path / "observability.jsonl"
    sink = _ls_health_sink(str(obs_path))

    sink({"event": "ls_tickagg_candle_written", "epic": "IX.D.DAX.IFMM.IP", "tick_count": 3})

    lines = obs_path.read_text().splitlines()
    assert len(lines) == 1
    assert '"ls_tickagg_candle_written"' in lines[0]
    assert '"IX.D.DAX.IFMM.IP"' in lines[0]


def test_ls_health_sink_does_not_raise_nameerror(tmp_path: Path) -> None:
    """The regression pin: before the fix this raised ``NameError: record_event``."""
    obs_path = tmp_path / "observability.jsonl"
    sink = _ls_health_sink(str(obs_path))

    try:
        sink({"event": "ls_tickagg_candle_written"})
    except NameError as exc:  # pragma: no cover — the bug this test exists to catch
        pytest.fail(f"health sink raised NameError (Drift #12 regressed): {exc}")
