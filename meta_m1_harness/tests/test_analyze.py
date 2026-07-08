from __future__ import annotations

import json
from pathlib import Path

import pytest

import analyze
from harness_bakeoff import TrialResult


def _write_trials(path: Path, trials: list[TrialResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for t in trials:
            fh.write(json.dumps(t.__dict__) + "\n")


def test_load_trials_roundtrip(tmp_path):
    trials = [
        TrialResult(
            harness="cc", step="S1", repeat=1, exit_ok=True, gate_passed=True,
            wall_seconds=1.0, edit_failures=0, files_changed=2, usage_tokens=100.0,
        ),
    ]
    path = tmp_path / "trials.jsonl"
    _write_trials(path, trials)

    assert analyze.load_trials(path) == trials


def test_summarize_and_noise_golden():
    trials = [
        TrialResult(harness="cc", step="S1", repeat=1, exit_ok=True, gate_passed=True,
                    wall_seconds=10.0, edit_failures=0, files_changed=1, usage_tokens=100.0),
        TrialResult(harness="cc", step="S1", repeat=2, exit_ok=True, gate_passed=True,
                    wall_seconds=12.0, edit_failures=0, files_changed=1, usage_tokens=110.0),
        TrialResult(harness="oc", step="S1", repeat=1, exit_ok=True, gate_passed=False,
                    wall_seconds=20.0, edit_failures=1, files_changed=0, usage_tokens=90.0),
        TrialResult(harness="oc", step="S1", repeat=2, exit_ok=True, gate_passed=True,
                    wall_seconds=18.0, edit_failures=0, files_changed=1, usage_tokens=95.0),
    ]

    summary = analyze.summarize(trials)

    assert summary["per_harness"]["cc"]["gate_pass_rate"] == pytest.approx(1.0)
    assert summary["per_harness"]["oc"]["gate_pass_rate"] == pytest.approx(0.5)
    assert summary["gap"] == pytest.approx(0.5)
    # cc: both repeats passed -> zero within-harness spread. oc: repeat 1 failed, repeat 2
    # passed -> spread 1.0, which exceeds the 0.5 gap -> reported as noise.
    assert summary["per_harness"]["oc"]["within_harness_spread"] == pytest.approx(1.0)
    assert summary["noise"] is True

    markdown = analyze.render_markdown(summary)
    assert "not distinguishable" in markdown
    assert "cc" in markdown and "oc" in markdown


def test_summarize_single_harness_has_no_gap():
    trials = [
        TrialResult(harness="cc", step="S1", repeat=1, exit_ok=True, gate_passed=True,
                    wall_seconds=1.0, edit_failures=0, files_changed=1),
    ]
    summary = analyze.summarize(trials)
    assert summary["gap"] is None
    assert summary["noise"] is None
