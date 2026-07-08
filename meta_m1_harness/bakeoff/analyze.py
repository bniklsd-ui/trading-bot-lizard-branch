"""Summarizes M1 bake-off trials.jsonl into a per-harness comparison + noise check."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from harness_bakeoff import TrialResult


def load_trials(path: Path) -> list[TrialResult]:
    trials: list[TrialResult] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                trials.append(TrialResult(**json.loads(line)))
    return trials


def summarize(trials: list[TrialResult]) -> dict:
    by_harness: dict[str, list[TrialResult]] = {}
    for trial in trials:
        by_harness.setdefault(trial.harness, []).append(trial)

    per_harness: dict[str, dict] = {}
    for harness, group in by_harness.items():
        wall_seconds = [t.wall_seconds for t in group]
        tokens = [t.usage_tokens for t in group if t.usage_tokens is not None]

        by_repeat: dict[int, list[TrialResult]] = {}
        for t in group:
            by_repeat.setdefault(t.repeat, []).append(t)
        repeat_pass_rates = [
            sum(1 for t in rgroup if t.gate_passed) / len(rgroup)
            for rgroup in by_repeat.values()
        ]

        per_harness[harness] = {
            "gate_pass_rate": sum(1 for t in group if t.gate_passed) / len(group),
            "wall_seconds_mean": statistics.fmean(wall_seconds) if wall_seconds else 0.0,
            "wall_seconds_stdev": statistics.pstdev(wall_seconds) if len(wall_seconds) > 1 else 0.0,
            "usage_tokens_sum": sum(tokens),
            "edit_failures": sum(t.edit_failures for t in group),
            "within_harness_spread": (
                max(repeat_pass_rates) - min(repeat_pass_rates) if repeat_pass_rates else 0.0
            ),
        }

    names = list(per_harness.keys())
    gap = None
    noise = None
    if len(names) == 2:
        a, b = names
        gap = abs(per_harness[a]["gate_pass_rate"] - per_harness[b]["gate_pass_rate"])
        max_within = max(
            per_harness[a]["within_harness_spread"], per_harness[b]["within_harness_spread"]
        )
        noise = max_within > gap

    return {"per_harness": per_harness, "gap": gap, "noise": noise}


def render_markdown(summary: dict) -> str:
    lines = [
        "# M1 Bake-off Summary",
        "",
        "| Harness | gate_pass_rate | wall_s (mean±std) | tokens | edit_failures |",
        "|---|---|---|---|---|",
    ]
    for harness, stats in summary["per_harness"].items():
        lines.append(
            f"| {harness} | {stats['gate_pass_rate']:.2f} | "
            f"{stats['wall_seconds_mean']:.1f}±{stats['wall_seconds_stdev']:.1f} | "
            f"{stats['usage_tokens_sum']:.0f} | {stats['edit_failures']} |"
        )
    if summary["gap"] is not None:
        lines.append("")
        if summary["noise"]:
            lines.append(
                f"Gap = {summary['gap']:.2f} — **not distinguishable** "
                "(within-harness spread exceeds the between-harness gap)."
            )
        else:
            lines.append(f"Gap = {summary['gap']:.2f} (distinguishable).")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="M1 bake-off results analyzer")
    parser.add_argument(
        "--trials", type=Path, default=Path("meta_m1_harness/results/trials.jsonl")
    )
    args = parser.parse_args(argv)
    print(render_markdown(summarize(load_trials(args.trials))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
