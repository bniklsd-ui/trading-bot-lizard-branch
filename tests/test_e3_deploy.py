"""Tests for the **E-3 deploy script** (Phase 17, Plan §20 E-3a + §22 E-22c).

`scripts/e3_deploy.sh` is the mechanical transcription of the deploy sequence —
it exists because two things must not go wrong on the deploy morning:

1. **The start must land before 09:00 Berlin.** A start after 09:00 puts the
   `starting scheduler daemon` line on a day that is no longer "the first full
   trading day after the start" (Prereg BLUF) ⇒ K7-v5 fails *by construction*.
   The script refuses to start the scheduler in that case.
2. **The data repair must write the expected number of rows.** A second run or
   a changed live DB shifts `changes()` — the script aborts instead of
   continuing into the unit install.

Both are pinned here as subprocess tests with a **fake `systemctl`** and a
**fake `sqlite3`** on `PATH` (same harness pattern as
`test_scheduler_hold.py`) — no systemd, no network, no live `data/`. The
repository root is redirected via `E3_REPO_ROOT`, the data directory via
`E3_DATA_DIR`, the clock via `E3_LATEST_START`/the fake `date`.

The step *order* is pinned as well: it is the whole point of the script
(Plan §20 E-3a: stop the services BEFORE the DELETE, release the hold BEFORE
the install, start AFTER the data repair).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DEPLOY_SCRIPT = REPO_ROOT / "scripts" / "e3_deploy.sh"

ALL_UNITS = (
    "tradingbot-scheduler.service",
    "tradingbot-recorder.service",
    "tradingbot-discovery.service",
    "tradingbot-webui.service",
)

_FAKE_SYSTEMCTL = """#!/usr/bin/env bash
echo "$@" >> "${SYSTEMCTL_LOG}"
if [[ "$1" == "--user" && "$2" == "is-active" ]]; then
    echo "active"
    exit 0
fi
if [[ "$1" == "--user" && "$2" == "start" ]]; then
    printf '%s INFO scheduler.run: starting scheduler daemon (account=demo, max_trades=5, daily_loss_cap=1800.0, cycle=5min, llm_profile=research_m3).\n' \
        "$(date '+%Y-%m-%d %H:%M:%S')" >> "${SCHED_LOG}"
fi
exit 0
"""

_FAKE_SQLITE = """#!/usr/bin/env bash
echo "$@" >> "${SQLITE_LOG}"
case "$*" in
    *DELETE*) echo "${FAKE_CHANGES_IG:-3770}" ;;
    *UPDATE*) echo "${FAKE_CHANGES_INSTINCT:-29}" ;;
    *) echo 0 ;;
esac
"""

_FAKE_DATE = """#!/usr/bin/env bash
if [[ "$1" == "-Is" ]]; then echo "2026-11-09T07:30:00+01:00"; exit 0; fi
if [[ "$1" == "+%H:%M" ]]; then echo "${FAKE_NOW_HM:-07:35}"; exit 0; fi
if [[ "$1" == "+%Y%m%d" ]]; then echo "20261109"; exit 0; fi
exec /bin/date "$@"
"""


@pytest.fixture
def env(tmp_path: Path) -> dict[str, str]:
    """Fake environment: tmp repo, fake systemctl/sqlite3/date, no live data."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    for name, body in (
        ("systemctl", _FAKE_SYSTEMCTL),
        ("sqlite3", _FAKE_SQLITE),
        ("date", _FAKE_DATE),
    ):
        path = fake_bin / name
        path.write_text(body)
        path.chmod(0o755)

    repo = tmp_path / "repo"
    (repo / "data" / "state").mkdir(parents=True)
    (repo / "scripts").mkdir()
    shutil.copy(DEPLOY_SCRIPT, repo / "scripts" / "e3_deploy.sh")
    # the deploy script calls the tracked installer — it must run against the
    # tmp repo (its unit sources live in <repo>/phase16_activation/systemd)
    shutil.copy(REPO_ROOT / "scripts" / "install_units.sh", repo / "scripts" / "install_units.sh")
    (repo / "phase16_activation" / "systemd").mkdir(parents=True)
    for unit in ALL_UNITS:
        shutil.copy(
            REPO_ROOT / "phase16_activation" / "systemd" / unit,
            repo / "phase16_activation" / "systemd" / unit,
        )

    # the backup step copies both live DBs — dummy files are enough (the real
    # writes happen through the fake sqlite3)
    for name in ("bars.sqlite", "trading_bot.sqlite"):
        (repo / "data" / name).write_bytes(b"")

    # the daemon writes its start-line into the scheduler log (that is what
    # the deploy script waits for) — the fake systemctl appends it on "start"
    sched_log = repo / "data" / "state" / "run_scheduler.log"
    sched_log.write_text("")

    home = tmp_path / "home"
    home.mkdir()

    child_env = dict(os.environ)
    child_env.update(
        {
            "HOME": str(home),
            "PATH": f"{fake_bin}:{os.environ.get('PATH', '')}",
            "SYSTEMCTL_LOG": str(tmp_path / "systemctl.log"),
            "SQLITE_LOG": str(tmp_path / "sqlite.log"),
            "SCHED_LOG": str(sched_log),
            "E3_REPO_ROOT": str(repo),
            "E3_DATA_DIR": str(repo / "data"),
            "E3_SKIP_PREFLIGHT": "1",
            "E3_START_POLL": "1",
            "E3_PREFLIGHT_WAIT": "0",
            "FAKE_NOW_HM": "07:35",
        }
    )
    return child_env


def _run(env: dict[str, str], args: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(DEPLOY_SCRIPT), *(args or [])],
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )


def _calls(env: dict[str, str], key: str = "SYSTEMCTL_LOG") -> list[str]:
    log = Path(env[key])
    if not log.exists():
        return []
    return [line for line in log.read_text().splitlines() if line.strip()]


def _systemctl_calls(env: dict[str, str]) -> list[str]:
    return _calls(env)


def _sqlite_calls(env: dict[str, str]) -> list[str]:
    return _calls(env, "SQLITE_LOG")


# ── Reihenfolge (der Kern des Skripts) ────────────────────────────────────────


def test_step_order_is_plan_conform(env: dict[str, str]) -> None:
    """The order is Plan §20 E-3a: hold → stop → backup → repair → install → start.

    Pinned because every one of the six orders is load-bearing: the recorder
    holds `bars.sqlite` (stop before the DELETE), the hold must be gone before
    the installer enables the scheduler, and the scheduler may only start after
    the data repair.
    """
    result = _run(env)
    assert result.returncode == 0, result.stdout + result.stderr

    syscalls = _systemctl_calls(env)
    stop_idx = next(i for i, c in enumerate(syscalls) if c.startswith("--user stop"))
    start_idx = next(i for i, c in enumerate(syscalls) if c.startswith("--user start"))
    assert stop_idx < start_idx, syscalls

    sqlite_calls = _sqlite_calls(env)
    delete_idx = next(i for i, c in enumerate(sqlite_calls) if "DELETE" in c)
    update_idx = next(i for i, c in enumerate(sqlite_calls) if "UPDATE" in c)
    assert delete_idx < update_idx, sqlite_calls

    log = (Path(env["E3_DATA_DIR"]) / "state" / "e3_deploy.log").read_text()
    assert log.index("Schritt 1") < log.index("Schritt 2") < log.index("Schritt 3")
    assert log.index("Schritt 3") < log.index("Schritt 4") < log.index("Schritt 5")
    assert log.index("Schritt 5") < log.index("Schritt 6") < log.index("Schritt 7")


def test_dry_run_changes_nothing(env: dict[str, str]) -> None:
    """`--dry-run` prints the plan and touches neither systemd nor the DBs."""
    result = _run(env, ["--dry-run"])
    assert result.returncode == 0, result.stdout + result.stderr
    assert _systemctl_calls(env) == []
    assert _sqlite_calls(env) == []
    assert "Schritt 6" in result.stderr


# ── Die zwei Guards ───────────────────────────────────────────────────────────


def test_start_after_latest_start_aborts_without_starting(env: dict[str, str]) -> None:
    """Past the latest start time the scheduler is NOT started (K7 protection).

    A start after 09:00 Berlin puts the start-line outside the preregistered
    window ⇒ K7-v5 fails by construction ⇒ the window would be burned. The
    script aborts *before* `systemctl --user start`.
    """
    env["FAKE_NOW_HM"] = "09:12"
    result = _run(env)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "ABORT" in result.stderr
    assert not any(c.startswith("--user start") for c in _systemctl_calls(env)), _systemctl_calls(env)


def test_unexpected_changes_count_aborts_before_install(env: dict[str, str]) -> None:
    """A `changes()` mismatch aborts the deploy (no unit install, no start).

    This is the second run of the script (or a changed live DB): the DELETE
    would remove 0 rows instead of 3 770 — the deploy must not continue.
    """
    env["FAKE_CHANGES_IG"] = "0"
    result = _run(env)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "ABORT" in result.stderr
    assert not any(c.startswith("--user start") for c in _systemctl_calls(env))
    # the install (enable) must not have run either
    assert not any(" enable " in f" {c} " for c in _systemctl_calls(env))


def test_expected_changes_counts_pass(env: dict[str, str]) -> None:
    """With the expected counts the deploy runs to the end."""
    result = _run(env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK: ig-Bars gelöscht (3770)" in result.stderr
    assert "OK: Instincts markiert (29)" in result.stderr
    assert any(c.startswith("--user start") for c in _systemctl_calls(env))


# ── Das Skript ist ein Plan-Transkript ────────────────────────────────────────


def test_script_contains_the_plan_values(env: dict[str, str]) -> None:
    """The pinned Plan values are in the script (max_trades/daily_loss_cap live
    in the unit, not here) — the ones the script owns: 3 770 ig-Bars, 29
    Instincts, the 09:00 guard."""
    text = DEPLOY_SCRIPT.read_text(encoding="utf-8")
    assert "E3_EXPECT_IG:-3770" in text
    assert "E3_EXPECT_INSTINCT:-29" in text
    assert "E3_LATEST_START:-08:55" in text
    assert "llm_profile=research_m3" in text
    assert "DELETE FROM bars WHERE source='ig'" in text
    assert "[legacy-p16] " in text
