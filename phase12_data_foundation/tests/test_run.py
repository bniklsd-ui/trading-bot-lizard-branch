"""Tests for ``data_foundation.run``'s PID-file guard (Plan §6 Step 5). No network,
no real process spawned."""

from __future__ import annotations

import os

from data_foundation.run import _already_running, _pid_alive, _write_pid


def test_pid_alive_true_for_own_process():
    assert _pid_alive(os.getpid()) is True


def test_pid_alive_false_for_a_pid_that_does_not_exist():
    # PID 2**30 is astronomically unlikely to be a real live process.
    assert _pid_alive(2**30) is False


def test_already_running_false_when_pid_file_missing(tmp_path):
    assert _already_running(tmp_path / "recorder.pid") is False


def test_already_running_true_when_pid_file_names_a_live_process(tmp_path):
    pid_path = tmp_path / "recorder.pid"
    _write_pid(pid_path)  # writes os.getpid() — this test process is alive
    assert _already_running(pid_path) is True


def test_already_running_false_when_pid_file_names_a_dead_process(tmp_path):
    pid_path = tmp_path / "recorder.pid"
    pid_path.write_text(str(2**30), encoding="utf-8")
    assert _already_running(pid_path) is False


def test_already_running_false_on_corrupt_pid_file(tmp_path):
    pid_path = tmp_path / "recorder.pid"
    pid_path.write_text("not-a-pid", encoding="utf-8")
    assert _already_running(pid_path) is False


def test_write_pid_is_atomic_no_tmp_left_behind(tmp_path):
    pid_path = tmp_path / "recorder.pid"
    _write_pid(pid_path)
    assert pid_path.exists()
    assert int(pid_path.read_text()) == os.getpid()
    assert not pid_path.with_suffix(".pid.tmp").exists()
