"""Module 12 helper — the start/stop command file: round-trip, fail-soft reads, atomic write.

No network, no broker, no LLM: pure file I/O against ``tmp_path``, plus a module-export
identity check. The fail-soft contract (``read_command`` never raises) is exercised on the
missing / empty / corrupt / unknown-value paths.
"""

from __future__ import annotations

import json

import pytest

from scheduler import command as exported_command
from scheduler import command


def _cmd(tmp_path) -> str:
    """A nested command path so the parent-dir-creation behaviour is covered."""
    return str(tmp_path / "state" / "scheduler_command.json")


def test_read_none_when_missing(tmp_path) -> None:
    """No file → ``None`` (the default: run normally)."""
    assert command.read_command(_cmd(tmp_path)) is None


def test_stop_roundtrips(tmp_path) -> None:
    path = _cmd(tmp_path)
    command.write_command(path, "stop")
    assert command.read_command(path) == "stop"


def test_start_roundtrips_and_parent_dir_created(tmp_path) -> None:
    path = _cmd(tmp_path)
    command.write_command(path, "start")
    assert command.read_command(path) == "start"
    # atomic write leaves no .tmp residue
    assert list((tmp_path / "state").glob("*.tmp")) == []


def test_write_rejects_invalid_command(tmp_path) -> None:
    """The writer is in-process → a bad value is a programming error, not a tolerated blip."""
    with pytest.raises(ValueError):
        command.write_command(_cmd(tmp_path), "explode")


def test_read_unknown_value_is_none(tmp_path) -> None:
    """An unknown command in an otherwise-valid file reads as ``None`` (safe: don't pause)."""
    path = tmp_path / "cmd.json"
    path.write_text(json.dumps({"cmd": "frobnicate", "ts": "x"}), encoding="utf-8")
    assert command.read_command(str(path)) is None


def test_read_corrupt_is_none(tmp_path) -> None:
    """Unparseable, non-command text → ``None`` (never raises)."""
    path = tmp_path / "cmd.json"
    path.write_text("{not json at all", encoding="utf-8")
    assert command.read_command(str(path)) is None


def test_read_empty_is_none(tmp_path) -> None:
    path = tmp_path / "cmd.json"
    path.write_text("", encoding="utf-8")
    assert command.read_command(str(path)) is None


def test_read_tolerates_hand_written_bare_word(tmp_path) -> None:
    """An operator may hand-write a bare ``stop`` (not JSON) — still honored."""
    path = tmp_path / "cmd.json"
    path.write_text("stop", encoding="utf-8")
    assert command.read_command(str(path)) == "stop"


def test_clear_command_removes_file(tmp_path) -> None:
    path = _cmd(tmp_path)
    command.write_command(path, "stop")
    command.clear_command(path)
    assert command.read_command(path) is None
    command.clear_command(path)  # no-op on a missing file (fail-soft)


def test_exported_from_package_root() -> None:
    assert exported_command is command
