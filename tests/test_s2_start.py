"""Tests for the **-S2 start script** (Phase 17, Plan §26 F-26f + the locked -S2 prereg).

`scripts/s2_start.sh` runs from a systemd timer on Mon 2026-11-16 07:30 Berlin.
Three things must hold, all pinned here:

1. **Refusal outside D1-before-08:55.** A ``Persistent=`` catch-up after a late
   boot (or any other day) must not start the scheduler — the registered window
   needs D1 to be a full trading day (prereg BLUF, K7-v5).
2. **The start sequence is the prereg's**: release the hold → install the units →
   start **only** the scheduler (recorder/discovery/webui keep running — F-26f).
3. **The Aktiv-Block is entered and committed** before 09:00 (S1 finding N1),
   from the start line, HEAD and the open-position count.

Harness: the ``test_e3_deploy.py`` pattern — a tmp git repo, a fake
``systemctl``/``date``/``sqlite3`` on ``PATH``, no systemd, no network, no live
``data/``. The venv python the script calls is symlinked to this interpreter.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "s2_start.sh"
PREREG = REPO_ROOT / "phase17_testbed" / "PHASE17_SHAKEDOWN_PREREGISTRATION_S2.md"
UNITS = (
    "tradingbot-scheduler.service",
    "tradingbot-recorder.service",
    "tradingbot-discovery.service",
    "tradingbot-webui.service",
)

_FAKE_SYSTEMCTL = """#!/usr/bin/env bash
echo "$@" >> "${SYSTEMCTL_LOG}"
if [[ "$2" == "is-active" ]]; then echo active; exit 0; fi
if [[ "$2" == "start" ]]; then
    printf '%s INFO scheduler.run: starting scheduler daemon (account=demo, max_trades=5, daily_loss_cap=1800.0, cycle=5min, llm_profile=%s).\\n' \\
        "2026-11-16 07:31:02,123" "${FAKE_PROFILE:-all_m3}" >> "${SCHED_LOG}"
fi
exit 0
"""

_FAKE_DATE = """#!/usr/bin/env bash
case "$1" in
    +%F) echo "${FAKE_DAY}"; exit 0 ;;
    +%H:%M) echo "${FAKE_NOW_HM}"; exit 0 ;;
    -Is) echo "2026-11-16T07:30:00+01:00"; exit 0 ;;
esac
exec /bin/date "$@"
"""

_FAKE_SQLITE = """#!/usr/bin/env bash
echo 0
"""


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
        check=True, capture_output=True, text=True,
    ).stdout


@pytest.fixture
def env(tmp_path: Path) -> dict[str, str]:
    """Tmp git repo with the script, the installer, the units, the prereg and a held scheduler."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    for name, body in (("systemctl", _FAKE_SYSTEMCTL), ("date", _FAKE_DATE), ("sqlite3", _FAKE_SQLITE)):
        (fake_bin / name).write_text(body)
        (fake_bin / name).chmod(0o755)

    repo = tmp_path / "repo"
    for rel in ("scripts/s2_start.sh", "scripts/install_units.sh",
                "phase17_testbed/PHASE17_SHAKEDOWN_PREREGISTRATION_S2.md",
                *(f"phase16_activation/systemd/{u}" for u in UNITS)):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO_ROOT / rel, repo / rel)
    venv_bin = repo / "phase1_broker_wrapper" / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    (venv_bin / "python").symlink_to(sys.executable)
    state = repo / "data" / "state"
    state.mkdir(parents=True)
    (state / "run_scheduler.log").write_text("")
    (state / "execution_state.json").write_text('{"records": {"r1": {"status": "CLOSED"}}}')
    (state / "SCHEDULER_HELD").write_text("hold\n")
    _git(repo, "init", "-q")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "init")

    home = tmp_path / "home"
    home.mkdir()
    child = dict(os.environ)
    child.update({
        "HOME": str(home),
        "PATH": f"{fake_bin}:{os.environ.get('PATH', '')}",
        "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
        "SYSTEMCTL_LOG": str(tmp_path / "systemctl.log"),
        "SCHED_LOG": str(state / "run_scheduler.log"),
        "S2_REPO_ROOT": str(repo),
        "S2_SKIP_PREFLIGHT": "1",
        "S2_START_POLL": "1",
        "S2_PREFLIGHT_WAIT": "0",
        "FAKE_DAY": "2026-11-16",
        "FAKE_NOW_HM": "07:35",
    })
    return child


def _run(env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    repo = Path(env["S2_REPO_ROOT"])
    return subprocess.run(["bash", str(repo / "scripts" / "s2_start.sh"), *args],
                          env=env, capture_output=True, text=True, timeout=120)


def _systemctl_calls(env: dict[str, str]) -> list[str]:
    log = Path(env["SYSTEMCTL_LOG"])
    return log.read_text().splitlines() if log.exists() else []


@pytest.mark.parametrize(("day", "hm"), [("2026-11-16", "08:55"), ("2026-11-16", "09:10"), ("2026-11-17", "07:35")])
def test_refuses_outside_d1_before_0855(env: dict[str, str], day: str, hm: str) -> None:
    """A catch-up after 08:55 or on another day starts nothing and keeps the hold."""
    env.update({"FAKE_DAY": day, "FAKE_NOW_HM": hm})
    result = _run(env)

    assert result.returncode == 1, result.stderr
    assert "NOT started" in result.stderr
    assert _systemctl_calls(env) == []
    assert (Path(env["S2_REPO_ROOT"]) / "data" / "state" / "SCHEDULER_HELD").exists()


def test_start_sequence_starts_only_the_scheduler_and_enters_the_aktiv_block(env: dict[str, str]) -> None:
    """Release hold → install → start the scheduler only; then the Aktiv-Block is committed."""
    repo = Path(env["S2_REPO_ROOT"])
    result = _run(env)

    assert result.returncode == 0, result.stderr
    assert not (repo / "data" / "state" / "SCHEDULER_HELD").exists()
    calls = _systemctl_calls(env)
    starts = [c for c in calls if c.startswith("--user start")]
    assert starts == ["--user start tradingbot-scheduler.service"]
    assert calls.index("--user daemon-reload") < calls.index(starts[0])  # install before start

    prereg = (repo / "phase17_testbed" / "PHASE17_SHAKEDOWN_PREREGISTRATION_S2.md").read_text()
    assert "| **Start** | **2026-11-16 07:31:02,123 Europe/Berlin**" in prereg
    assert "llm_profile=all_m3" in prereg
    assert "| **Offene Position bei Start** | **0**" in prereg
    assert "nicht anwendbar" in prereg
    assert "*(einzutragen)*" not in prereg
    assert "Aktiv-Block eingetragen" in _git(repo, "log", "-1", "--format=%s")


def test_wrong_profile_in_the_start_line_aborts_without_aktiv_block(env: dict[str, str]) -> None:
    """A start line without llm_profile=all_m3 is K7 FAIL — loud exit, nothing entered."""
    env["FAKE_PROFILE"] = "research_m3"
    result = _run(env)

    assert result.returncode == 1
    assert "K7 FAIL" in result.stderr
    prereg = (Path(env["S2_REPO_ROOT"]) / "phase17_testbed" / "PHASE17_SHAKEDOWN_PREREGISTRATION_S2.md").read_text()
    assert "*(einzutragen)*" in prereg


def test_dry_run_changes_nothing(env: dict[str, str]) -> None:
    """--dry-run prints the steps and touches neither systemd, the hold nor the prereg."""
    repo = Path(env["S2_REPO_ROOT"])
    before = (repo / "phase17_testbed" / "PHASE17_SHAKEDOWN_PREREGISTRATION_S2.md").read_text()
    result = _run(env, "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "nothing was changed" in result.stderr
    assert _systemctl_calls(env) == []
    assert (repo / "data" / "state" / "SCHEDULER_HELD").exists()
    assert (repo / "phase17_testbed" / "PHASE17_SHAKEDOWN_PREREGISTRATION_S2.md").read_text() == before
