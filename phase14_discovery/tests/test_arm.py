"""Phase-14 Block C1 — tests for ``source_registry.arm``.

All mocked: ``tmp_path`` only, no network, no live DB, no scheduler process touched.
The arm-flag is a file-based operator control; tests construct files inline via
``tmp_path`` and assert :func:`is_armed` / :func:`arm` / :func:`disarm` /
:func:`read_state` semantics.

Test list (Plan §6 C1, ≥ 6; 12 here to pin every fail-soft direction explicitly):

1. missing file → ``False`` (safe direction)
2. empty file (hand-``touch``ed) → ``False``
3. broken JSON → ``False``
4. ``{"armed": false}`` → ``False``
5. ``{"armed": true, "by": ..., "ts": ...}`` → ``True`` + extra keys tolerated
6. ``{"armed": "true"}`` (string, not JSON-bool) → ``False`` — strict type
7. ``{"armed": 1}`` (int, not JSON-bool) → ``False``
8. ``{"armed": null}`` → ``False``
9. ``{}`` (no key) → ``False``
10. ``arm()`` then ``is_armed()`` → ``True``; parent dir is created if missing
11. ``arm()`` is atomic (``tmp`` + ``os.replace``); ``read_state`` sees the new payload
12. ``disarm()`` removes the file; ``disarm()`` on a missing file is a no-op
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from source_registry.arm import (
    DEFAULT_ARM_PATH,
    arm,
    disarm,
    is_armed,
    read_state,
)


# ---------------------------------------------------------------------------
# is_armed — safe direction: every ambiguity reads as False
# ---------------------------------------------------------------------------


def test_is_armed_returns_false_when_file_missing(tmp_path: Path) -> None:
    assert is_armed(str(tmp_path / "DISCOVERY_ARMED")) is False


def test_is_armed_returns_false_when_file_empty(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """An empty file is the typical hand-``touch`` state — must read as unarmed."""
    flag = tmp_path / "DISCOVERY_ARMED"
    flag.touch()
    assert is_armed(str(flag)) is False


def test_is_armed_returns_false_when_broken_json(tmp_path: Path) -> None:
    flag = tmp_path / "DISCOVERY_ARMED"
    flag.write_text("{this is not json", encoding="utf-8")
    assert is_armed(str(flag)) is False


def test_is_armed_returns_false_when_armed_false(tmp_path: Path) -> None:
    flag = tmp_path / "DISCOVERY_ARMED"
    flag.write_text(json.dumps({"armed": False, "by": "operator", "ts": "x"}), encoding="utf-8")
    assert is_armed(str(flag)) is False


def test_is_armed_returns_true_when_armed_true_with_extra_keys(tmp_path: Path) -> None:
    """The arm payload carries ``by`` and ``ts`` — extra keys must not disarm."""
    flag = tmp_path / "DISCOVERY_ARMED"
    flag.write_text(
        json.dumps({"armed": True, "by": "dashboard", "ts": "2026-08-22T19:00:00+00:00"}),
        encoding="utf-8",
    )
    assert is_armed(str(flag)) is True


def test_is_armed_returns_false_when_armed_value_is_string_not_bool(tmp_path: Path) -> None:
    """``"true"`` (string) is NOT the JSON boolean True — strict type matters."""
    flag = tmp_path / "DISCOVERY_ARMED"
    flag.write_text(json.dumps({"armed": "true"}), encoding="utf-8")
    assert is_armed(str(flag)) is False


def test_is_armed_returns_false_when_armed_value_is_int_one(tmp_path: Path) -> None:
    """``1`` is not the JSON boolean True."""
    flag = tmp_path / "DISCOVERY_ARMED"
    flag.write_text(json.dumps({"armed": 1}), encoding="utf-8")
    assert is_armed(str(flag)) is False


def test_is_armed_returns_false_when_armed_value_is_null(tmp_path: Path) -> None:
    flag = tmp_path / "DISCOVERY_ARMED"
    flag.write_text(json.dumps({"armed": None}), encoding="utf-8")
    assert is_armed(str(flag)) is False


def test_is_armed_returns_false_when_no_armed_key(tmp_path: Path) -> None:
    flag = tmp_path / "DISCOVERY_ARMED"
    flag.write_text(json.dumps({"foo": "bar"}), encoding="utf-8")
    assert is_armed(str(flag)) is False


# ---------------------------------------------------------------------------
# arm / disarm / read_state — the happy paths + atomicity + parent-dir creation
# ---------------------------------------------------------------------------


def test_arm_then_is_armed_roundtrip(tmp_path: Path) -> None:
    flag = tmp_path / "DISCOVERY_ARMED"
    assert is_armed(str(flag)) is False
    arm(str(flag), by="dashboard")
    assert is_armed(str(flag)) is True
    # Payload structure: read_state returns the dict for the UI display.
    state = read_state(str(flag))
    assert state is not None
    assert state["armed"] is True
    assert state["by"] == "dashboard"
    assert "ts" in state


def test_arm_creates_parent_directory(tmp_path: Path) -> None:
    """``data/state/`` may not exist on a fresh checkout — arm() must mkdir -p."""
    flag = tmp_path / "deep" / "nested" / "DISCOVERY_ARMED"
    arm(str(flag), by="operator")
    assert is_armed(str(flag)) is True


def test_arm_is_atomic_no_tmp_file_left(tmp_path: Path) -> None:
    """``arm()`` writes via ``.tmp`` + ``os.replace``; no half-written file is ever visible."""
    flag = tmp_path / "DISCOVERY_ARMED"
    arm(str(flag), by="dashboard")
    # No .tmp sibling should remain.
    siblings = list(flag.parent.iterdir())
    assert siblings == [flag], f"unexpected siblings after arm(): {siblings}"


def test_disarm_removes_file(tmp_path: Path) -> None:
    flag = tmp_path / "DISCOVERY_ARMED"
    arm(str(flag), by="dashboard")
    assert is_armed(str(flag)) is True
    disarm(str(flag))
    assert is_armed(str(flag)) is False
    assert not flag.exists()


def test_disarm_on_missing_file_is_noop(tmp_path: Path) -> None:
    """Per plan: ``disarm()`` on a missing file is a no-op, never raises."""
    flag = tmp_path / "DISCOVERY_ARMED"
    assert not flag.exists()
    disarm(str(flag))  # must not raise
    assert not flag.exists()


# ---------------------------------------------------------------------------
# read_state — UI display
# ---------------------------------------------------------------------------


def test_read_state_returns_none_when_file_missing(tmp_path: Path) -> None:
    assert read_state(str(tmp_path / "DISCOVERY_ARMED")) is None


def test_read_state_returns_none_when_broken_json(tmp_path: Path) -> None:
    flag = tmp_path / "DISCOVERY_ARMED"
    flag.write_text("not json", encoding="utf-8")
    assert read_state(str(flag)) is None


def test_read_state_returns_full_payload(tmp_path: Path) -> None:
    flag = tmp_path / "DISCOVERY_ARMED"
    arm(str(flag), by="dashboard")
    state = read_state(str(flag))
    assert state is not None
    assert set(state.keys()) >= {"armed", "by", "ts"}


# ---------------------------------------------------------------------------
# Module-level default path — the single source of truth for the file location
# ---------------------------------------------------------------------------


def test_default_arm_path_is_under_data_state() -> None:
    """The default path must be the same one Phase-8 webui/api.py uses (sync contract)."""
    assert DEFAULT_ARM_PATH == Path("data") / "state" / "DISCOVERY_ARMED"
