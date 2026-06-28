"""Module 5 — the file-based kill-switch: existence, reason round-trip, fail-soft reads.

No network, no broker, no LLM: pure file I/O against ``tmp_path``, plus a ``caplog`` probe
of the single read-error WARNING and a module-export identity check. The fail-soft contract
(never raises) is exercised on the missing-file / empty / plain-text paths.
"""

from __future__ import annotations

import logging

import pytest

from scheduler import killswitch as exported_killswitch
from scheduler import killswitch


def _kill(tmp_path) -> str:
    """A nested kill path so the parent-dir-creation behaviour is covered."""
    return str(tmp_path / "state" / "KILL")


def test_is_set_false_then_true_after_set(tmp_path) -> None:
    """Existence is the truth: False with no file, True once ``set_kill`` wrote it."""
    path = _kill(tmp_path)
    assert killswitch.is_set(path) is False
    killswitch.set_kill(path, "auto:backoff")
    assert killswitch.is_set(path) is True


def test_auto_reason_roundtrips(tmp_path) -> None:
    """``set_kill`` then ``read_reason`` returns the auto-trip reason verbatim."""
    path = _kill(tmp_path)
    killswitch.set_kill(path, "auto:backoff")
    assert killswitch.read_reason(path) == "auto:backoff"


def test_manual_reason_roundtrips(tmp_path) -> None:
    """A manual operator/UI reason round-trips too."""
    path = _kill(tmp_path)
    killswitch.set_kill(path, "manual:operator stop")
    assert killswitch.read_reason(path) == "manual:operator stop"


def test_set_kill_creates_parent_and_leaves_no_tmp(tmp_path) -> None:
    """The parent dir is auto-created and no ``.tmp`` lingers after an atomic write."""
    path = tmp_path / "data" / "state" / "KILL"
    killswitch.set_kill(str(path), "auto:backoff")
    assert path.exists()
    assert path.parent.is_dir()
    assert list(path.parent.glob("*.tmp")) == []


def test_clear_kill_disengages(tmp_path) -> None:
    """After ``clear_kill`` the switch is off and there is no reason to read."""
    path = _kill(tmp_path)
    killswitch.set_kill(path, "auto:backoff")
    killswitch.clear_kill(path)
    assert killswitch.is_set(path) is False
    assert killswitch.read_reason(path) is None


def test_clear_missing_file_is_noop(tmp_path) -> None:
    """Clearing an absent switch never raises (fail-soft)."""
    killswitch.clear_kill(_kill(tmp_path))  # must not raise


def test_read_reason_missing_file_is_none(tmp_path) -> None:
    """No file → no reason."""
    assert killswitch.read_reason(_kill(tmp_path)) is None


def test_empty_touched_file_is_set_but_no_reason(tmp_path) -> None:
    """An operator's bare ``touch`` halts the daemon (is_set True) with no reason."""
    path = tmp_path / "KILL"
    path.touch()
    assert killswitch.is_set(str(path)) is True
    assert killswitch.read_reason(str(path)) is None


def test_read_reason_plain_text_returns_raw(tmp_path) -> None:
    """A hand-written, non-JSON reason is returned as the stripped raw text."""
    path = tmp_path / "KILL"
    path.write_text("  stopped by hand  \n", encoding="utf-8")
    assert killswitch.read_reason(str(path)) == "stopped by hand"


def test_set_kill_overwrites_latest_reason_wins(tmp_path) -> None:
    """Re-engaging with a new reason replaces the old one."""
    path = _kill(tmp_path)
    killswitch.set_kill(path, "auto:backoff")
    killswitch.set_kill(path, "manual:operator stop")
    assert killswitch.read_reason(path) == "manual:operator stop"


def test_read_reason_unreadable_warns_and_returns_none(
    tmp_path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """An existing-but-unreadable file → one WARNING + None (never raises)."""
    path = tmp_path / "KILL"
    path.touch()

    def _boom(*_args, **_kwargs):
        raise OSError("permission denied")

    monkeypatch.setattr("pathlib.Path.read_text", _boom)
    with caplog.at_level(logging.WARNING, logger="scheduler.killswitch"):
        result = killswitch.read_reason(str(path))
    assert result is None
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "unreadable" in warnings[0].message


def test_exported_module_from_package_root() -> None:
    """``from scheduler import killswitch`` is the submodule namespace."""
    import scheduler

    assert exported_killswitch is scheduler.killswitch
    assert killswitch is scheduler.killswitch
