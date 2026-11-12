"""Tests for the **Scheduler-Hold** (Phase 17 B-0) in the shell helpers.

The Phase-17 decision B-0 keeps the scheduler deliberately stopped (Plan §6 —
only the scheduler holds an IG session, Plan T22) until E-3. Two doors could
switch it back on without anybody asking:

1. ``scripts/install_units.sh`` — the tracked installer ends with
   ``systemctl --user enable <all four units>``; an update run that re-runs it
   re-enables the scheduler's **autostart**, so the next reboot starts the
   stopped scheduler.
2. ``scripts/restart-services.sh`` — the repo's own restart helper starts the
   scheduler wrapper (``nohup``), independent of systemd.

Both are gated by the operator-sticky marker ``data/state/SCHEDULER_HELD``
(same pattern as ``KILL`` / ``DISCOVERY_ARMED``). The tests drive both scripts
as subprocesses (root ``tests/`` harness, same pattern as
``test_check_doc_rotation.py``) with a **fake ``systemctl``** on ``PATH`` and a
temporary ``HOME`` — no systemd, no network, no touch of the live
``data/state`` directory (``TRADINGBOT_HOLD_FILE`` points the marker at a tmp
path).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALL_SCRIPT = REPO_ROOT / "scripts" / "install_units.sh"
RESTART_SCRIPT = REPO_ROOT / "scripts" / "restart-services.sh"

ALL_UNITS = (
    "tradingbot-scheduler.service",
    "tradingbot-recorder.service",
    "tradingbot-discovery.service",
    "tradingbot-webui.service",
)
SCHEDULER_UNIT = "tradingbot-scheduler.service"
OTHER_UNITS = tuple(u for u in ALL_UNITS if u != SCHEDULER_UNIT)

# Fake `systemctl`: logs every call, answers `is-enabled` from the environment.
_FAKE_SYSTEMCTL = """#!/usr/bin/env bash
echo "$@" >> "${SYSTEMCTL_LOG}"
if [[ "$1" == "--user" && "$2" == "is-enabled" ]]; then
    unit="$3"
    if [[ "$unit" == "tradingbot-scheduler.service" ]]; then
        state="${FAKE_SCHEDULER_ENABLED:-enabled}"
    else
        state="${FAKE_OTHER_ENABLED:-enabled}"
    fi
    echo "$state"
    case "$state" in
        disabled) exit 1 ;;
        not-found) exit 4 ;;
        *) exit 0 ;;
    esac
fi
exit 0
"""


@pytest.fixture
def env(tmp_path: Path) -> dict[str, str]:
    """Fake-sctl environment: tmp HOME, fake systemctl, tmp hold marker."""
    if shutil.which("systemd-analyze") is None:
        pytest.skip("systemd-analyze not available — install_units.sh cannot verify here")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    systemctl = fake_bin / "systemctl"
    systemctl.write_text(_FAKE_SYSTEMCTL)
    systemctl.chmod(0o755)
    # A fake `pgrep` — the restart helper refuses a double start when the
    # service is already alive ("already alive — skipping (refuse double-start)").
    # Without this fake the test sees the **live** bot: while the scheduler runs,
    # `start --dry-run` never reaches its "would nohup" branch and
    # `test_restart_start_would_start_scheduler_without_hold` fails on live state
    # instead of on the hold logic. Mid-plan fix (Nikinger, 2026-11-12): the test
    # was never hermetic against the running processes, only against data/state.
    pgrep = fake_bin / "pgrep"
    pgrep.write_text("#!/usr/bin/env bash\n# no service is running inside the test\nexit 1\n")
    pgrep.chmod(0o755)
    home = tmp_path / "home"
    home.mkdir()
    child_env = dict(os.environ)
    child_env.update(
        {
            "HOME": str(home),
            "PATH": f"{fake_bin}:{os.environ.get('PATH', '')}",
            "SYSTEMCTL_LOG": str(tmp_path / "systemctl.log"),
            "FAKE_SCHEDULER_ENABLED": "enabled",
            "FAKE_OTHER_ENABLED": "enabled",
            "TRADINGBOT_HOLD_FILE": str(tmp_path / "SCHEDULER_HELD"),
        }
    )
    return child_env


def _run(script: Path, args: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    """Run one of the shell helpers and capture stdout/stderr."""
    return subprocess.run(
        ["bash", str(script), *args],
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def _calls(env: dict[str, str]) -> list[str]:
    """Every argument list the fake systemctl saw."""
    log = Path(env["SYSTEMCTL_LOG"])
    if not log.exists():
        return []
    return [line for line in log.read_text().splitlines() if line.strip()]


def _enable_calls(env: dict[str, str]) -> list[str]:
    """Only the `enable` calls (fake systemctl logs `--user enable …`)."""
    return [c for c in _calls(env) if " enable " in f" {c} "]


def _hold_marker(env: dict[str, str]) -> Path:
    return Path(env["TRADINGBOT_HOLD_FILE"])


# ── install_units.sh ─────────────────────────────────────────────────────────


def test_install_enables_all_four_units_without_hold(env: dict[str, str]) -> None:
    """Without the marker every unit — scheduler included — gets enabled."""
    result = _run(INSTALL_SCRIPT, [], env)
    assert result.returncode == 0, result.stderr
    enable_calls = _enable_calls(env)
    assert len(enable_calls) == 1, enable_calls
    for unit in ALL_UNITS:
        assert unit in enable_calls[0], enable_calls[0]


def test_install_skips_scheduler_when_hold_marker_present(env: dict[str, str]) -> None:
    """With the marker the scheduler is NOT enabled — the other three are."""
    _hold_marker(env).write_text("Phase 17 B-0\n")
    result = _run(INSTALL_SCRIPT, [], env)
    assert result.returncode == 0, result.stderr
    enable_calls = _enable_calls(env)
    assert len(enable_calls) == 1, enable_calls
    assert SCHEDULER_UNIT not in enable_calls[0], enable_calls[0]
    for unit in OTHER_UNITS:
        assert unit in enable_calls[0], enable_calls[0]
    assert "HOLD" in result.stderr
    assert SCHEDULER_UNIT in result.stderr


def test_install_dry_run_never_touches_systemctl(env: dict[str, str]) -> None:
    """--dry-run changes nothing: no systemctl call at all."""
    _hold_marker(env).write_text("Phase 17 B-0\n")
    result = _run(INSTALL_SCRIPT, ["--dry-run"], env)
    assert result.returncode == 0, result.stderr
    assert _calls(env) == []
    assert "NOT enabling" in result.stderr


def test_install_check_is_green_when_scheduler_is_disabled_and_held(env: dict[str, str]) -> None:
    """--check: held scheduler disabled + all units installed → exit 0."""
    _install_units(env)  # fills the tmp HOME with the four unit files
    _hold_marker(env).write_text("Phase 17 B-0\n")
    env["FAKE_SCHEDULER_ENABLED"] = "disabled"
    result = _run(INSTALL_SCRIPT, ["--check"], env)
    assert result.returncode == 0, result.stderr
    assert "hold ACTIVE" in result.stderr
    assert "DRIFT" not in result.stderr


def test_install_check_flags_enabled_scheduler_under_hold_as_drift(env: dict[str, str]) -> None:
    """--check: a held-but-enabled scheduler is drift (the reboot trap)."""
    _install_units(env)
    _hold_marker(env).write_text("Phase 17 B-0\n")
    env["FAKE_SCHEDULER_ENABLED"] = "enabled"
    result = _run(INSTALL_SCRIPT, ["--check"], env)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "DRIFT" in result.stderr


def test_install_check_flags_missing_unit_file_as_drift(env: dict[str, str]) -> None:
    """--check: a unit file that is not installed is drift."""
    result = _run(INSTALL_SCRIPT, ["--check"], env)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "DRIFT" in result.stderr


def test_install_hold_creates_marker_and_disables_unit(env: dict[str, str]) -> None:
    """--hold: marker created, autostart of the scheduler switched off."""
    _install_units(env)
    result = _run(INSTALL_SCRIPT, ["--hold"], env)
    assert result.returncode == 0, result.stderr
    assert _hold_marker(env).exists()
    disable_calls = [c for c in _calls(env) if " disable " in f" {c} "]
    assert len(disable_calls) == 1, disable_calls
    assert SCHEDULER_UNIT in disable_calls[0]


def test_install_release_hold_removes_marker(env: dict[str, str]) -> None:
    """--release-hold: the marker is gone again (E-3 path)."""
    marker = _hold_marker(env)
    marker.write_text("Phase 17 B-0\n")
    result = _run(INSTALL_SCRIPT, ["--release-hold"], env)
    assert result.returncode == 0, result.stderr
    assert not marker.exists()


def test_install_release_hold_is_idempotent(env: dict[str, str]) -> None:
    """--release-hold without a marker is a no-op, not an error."""
    result = _run(INSTALL_SCRIPT, ["--release-hold"], env)
    assert result.returncode == 0, result.stderr
    assert "nothing to release" in result.stderr


def _install_units(env: dict[str, str]) -> None:
    """Fill the tmp HOME with the four unit files (no enable side effect)."""
    dest = Path(env["HOME"]) / ".config" / "systemd" / "user"
    dest.mkdir(parents=True, exist_ok=True)
    for unit in ALL_UNITS:
        shutil.copy(REPO_ROOT / "phase16_activation" / "systemd" / unit, dest / unit)


# ── restart-services.sh ──────────────────────────────────────────────────────


def test_restart_start_skips_scheduler_when_held(env: dict[str, str]) -> None:
    """`restart-services.sh start` must not start the held scheduler."""
    _hold_marker(env).write_text("Phase 17 B-0\n")
    result = _run(RESTART_SCRIPT, ["start", "--dry-run"], env)
    assert result.returncode == 0, result.stderr
    assert "HOLD" in result.stderr
    assert not any(
        "would nohup" in line and "run_scheduler.sh" in line for line in result.stderr.splitlines()
    ), result.stderr


def test_restart_status_reports_the_hold(env: dict[str, str]) -> None:
    """`status` surfaces the hold so the operator sees why it stays down."""
    _hold_marker(env).write_text("Phase 17 B-0\n")
    result = _run(RESTART_SCRIPT, ["status"], env)
    assert "SCHEDULER_HOLD present" in result.stderr


def test_restart_start_would_start_scheduler_without_hold(env: dict[str, str]) -> None:
    """Without the marker the scheduler is a normal start candidate again."""
    result = _run(RESTART_SCRIPT, ["start", "--dry-run"], env)
    assert result.returncode == 0, result.stderr
    assert "HOLD" not in result.stderr
    assert any(
        "would nohup" in line and "run_scheduler.sh" in line for line in result.stderr.splitlines()
    ), result.stderr
