from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

import harness_bakeoff as bo


class _FakeCompleted:
    def __init__(self, stdout: str = "", returncode: int = 0) -> None:
        self.stdout = stdout
        self.returncode = returncode
        self.stderr = ""


def _make_spec(tmp_path: Path, step_id: str = "S1") -> bo.StepSpec:
    spec_path = tmp_path / f"{step_id}.md"
    spec_path.write_text("spec body", encoding="utf-8")
    return bo.StepSpec(
        step_id=step_id, spec_path=spec_path, base_tag="base-0", gate_argv=["true"]
    )


def _some_weekday_at(hour: int) -> datetime:
    base = datetime.now(ZoneInfo("Europe/Berlin")).date()
    days_ahead = (1 - base.weekday()) % 7  # 1 = Tuesday
    target = base + timedelta(days=days_ahead)
    return datetime(target.year, target.month, target.day, hour, 0, tzinfo=ZoneInfo("Europe/Berlin"))


def _some_weekend_at(hour: int) -> datetime:
    base = datetime.now(ZoneInfo("Europe/Berlin")).date()
    days_ahead = (5 - base.weekday()) % 7  # 5 = Saturday
    target = base + timedelta(days=days_ahead)
    return datetime(target.year, target.month, target.day, hour, 0, tzinfo=ZoneInfo("Europe/Berlin"))


# --- _compute_edit_failures (3 fixed cases) --------------------------------------------


@pytest.mark.parametrize(
    "exit_ok,files_changed,gate_passed,expected",
    [
        (True, 0, False, 1),  # claimed success, wrote nothing, gate failed -> edit failure
        (True, 3, False, 0),  # wrote something, gate just failed -> not an edit failure
        (False, 0, False, 0),  # harness itself failed -> not an edit failure
    ],
)
def test_compute_edit_failures(exit_ok, files_changed, gate_passed, expected):
    assert bo._compute_edit_failures(exit_ok, files_changed, gate_passed) == expected


# --- BudgetGuard -------------------------------------------------------------------------


def test_budget_guard_trips_over_cap():
    guard = bo.BudgetGuard(cap_eur=1.0)
    guard.add_manual_eur(0.5)
    with pytest.raises(bo.BudgetExceeded):
        guard.add_manual_eur(0.6)


def test_budget_guard_stays_under_cap():
    guard = bo.BudgetGuard(cap_eur=10.0)
    guard.add_manual_eur(5.0)
    assert guard.remaining() == pytest.approx(5.0)


def test_budget_guard_add_uses_price_table():
    guard = bo.BudgetGuard(cap_eur=1000.0)
    guard.add(tokens_in=1_000_000, tokens_out=0)
    price_in, _ = bo.PRICE_EUR_PER_MTOK["sonnet-5"]
    assert guard.spent_eur == pytest.approx(price_in)


# --- assert_offhours (in/out/override) ----------------------------------------------------


def test_assert_offhours_raises_during_trading_window(monkeypatch):
    monkeypatch.delenv("BAKEOFF_FORCE_WINDOW", raising=False)
    with pytest.raises(SystemExit):
        bo.assert_offhours(_some_weekday_at(12))


def test_assert_offhours_passes_on_weekend(monkeypatch):
    monkeypatch.delenv("BAKEOFF_FORCE_WINDOW", raising=False)
    bo.assert_offhours(_some_weekend_at(12))  # must not raise


def test_assert_offhours_override(monkeypatch):
    monkeypatch.setenv("BAKEOFF_FORCE_WINDOW", "1")
    bo.assert_offhours(_some_weekday_at(12))  # must not raise despite in-window


# --- assert_clean_repo (dirty -> SystemExit) -----------------------------------------------


def test_assert_clean_repo_missing_git_dir_exits(tmp_path):
    with pytest.raises(SystemExit):
        bo.assert_clean_repo(tmp_path)


def test_assert_clean_repo_dirty_exits(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr(bo, "_git", lambda repo, *a, **k: _FakeCompleted(stdout=" M foo.py\n"))
    with pytest.raises(SystemExit):
        bo.assert_clean_repo(tmp_path)


def test_assert_clean_repo_clean_passes(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr(bo, "_git", lambda repo, *a, **k: _FakeCompleted(stdout=""))
    bo.assert_clean_repo(tmp_path)  # must not raise


# --- run_trial / run_matrix: reset discipline + JSONL schema -------------------------------


def test_run_trial_resets_before_and_after(tmp_path, monkeypatch):
    resets: list[str] = []
    monkeypatch.setattr(bo, "assert_clean_repo", lambda repo: None)
    monkeypatch.setattr(bo, "reset_to", lambda repo, ref: resets.append(ref))
    monkeypatch.setattr(bo, "snapshot_ref", lambda repo: "REF0")
    monkeypatch.setattr(bo, "changed_files", lambda repo, ref: ["foo.py"])
    monkeypatch.setattr(bo, "_load_preamble", lambda: "preamble")
    monkeypatch.setattr(
        bo.subprocess, "run", lambda argv, **kwargs: _FakeCompleted(stdout="tokens=42")
    )

    harness = bo.HarnessConfig(
        name="fake", argv_template=["fake", "{prompt}"], usage_regex=r"tokens=(?P<tokens>\d+)"
    )
    spec = _make_spec(tmp_path)
    result = bo.run_trial(tmp_path, harness, spec, repeat=1, budget=bo.BudgetGuard(cap_eur=1000.0))

    assert resets == ["base-0", "REF0"]  # reset before the trial, reset back after
    assert result.gate_passed is True
    assert result.usage_tokens == 42.0


def test_run_trial_manual_spend_path_when_usage_unparseable(tmp_path, monkeypatch):
    monkeypatch.setattr(bo, "assert_clean_repo", lambda repo: None)
    monkeypatch.setattr(bo, "reset_to", lambda repo, ref: None)
    monkeypatch.setattr(bo, "snapshot_ref", lambda repo: "REF0")
    monkeypatch.setattr(bo, "changed_files", lambda repo, ref: ["foo.py"])
    monkeypatch.setattr(bo, "_load_preamble", lambda: "preamble")
    monkeypatch.setattr(bo.subprocess, "run", lambda argv, **kwargs: _FakeCompleted(stdout="no usage here"))
    monkeypatch.setattr(bo, "_prompt_operator_for_manual_spend", lambda harness, spec: 1.23)

    harness = bo.HarnessConfig(name="fake", argv_template=["fake", "{prompt}"], usage_regex=None)
    spec = _make_spec(tmp_path)
    budget = bo.BudgetGuard(cap_eur=1000.0)
    bo.run_trial(tmp_path, harness, spec, repeat=1, budget=budget)

    assert budget.spent_eur == pytest.approx(1.23)


def test_run_matrix_resets_after_last_trial_and_writes_stable_jsonl(tmp_path, monkeypatch):
    resets: list[str] = []
    monkeypatch.setattr(bo, "assert_clean_repo", lambda repo: None)
    monkeypatch.setattr(bo, "reset_to", lambda repo, ref: resets.append(ref))
    monkeypatch.setattr(bo, "snapshot_ref", lambda repo: "REF0")
    monkeypatch.setattr(bo, "changed_files", lambda repo, ref: ["foo.py"])
    monkeypatch.setattr(bo, "_load_preamble", lambda: "preamble")
    monkeypatch.setattr(
        bo.subprocess, "run", lambda argv, **kwargs: _FakeCompleted(stdout="tokens=1")
    )

    harness = bo.HarnessConfig(
        name="fake", argv_template=["fake", "{prompt}"], usage_regex=r"tokens=(?P<tokens>\d+)"
    )
    spec = _make_spec(tmp_path)
    results_path = tmp_path / "results" / "trials.jsonl"

    results = bo.run_matrix(
        tmp_path, [harness], [spec], repeats=2, budget=bo.BudgetGuard(cap_eur=1000.0),
        results_path=results_path,
    )

    assert len(results) == 2
    assert resets[-1] == "REF0"  # reset happens after the very last trial too
    assert resets.count("base-0") == 2  # and before every trial

    lines = results_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    expected_keys = {
        "harness", "step", "repeat", "exit_ok", "gate_passed", "wall_seconds",
        "edit_failures", "files_changed", "usage_tokens", "error", "extra",
    }
    for line in lines:
        assert set(json.loads(line)) == expected_keys


# --- main() --dry-run: prints a matrix, touches nothing -------------------------------------


def test_dry_run_prints_matrix_and_touches_nothing(tmp_path, monkeypatch, capsys):
    specs_dir = tmp_path / "meta_m1_harness" / "specs"
    specs_dir.mkdir(parents=True)
    (specs_dir / "S1.md").write_text("spec", encoding="utf-8")

    touched = {"subprocess": False, "git": False}
    monkeypatch.setattr(bo.subprocess, "run", lambda *a, **k: touched.__setitem__("subprocess", True))
    monkeypatch.setattr(bo, "_git", lambda *a, **k: touched.__setitem__("git", True))

    exit_code = bo.main(
        ["--repo", str(tmp_path), "--steps", "S1", "--harness", "claude_code", "--dry-run"]
    )

    assert exit_code == 0
    assert touched == {"subprocess": False, "git": False}
    out = capsys.readouterr().out
    assert "S1" in out
    assert "claude_code" in out
