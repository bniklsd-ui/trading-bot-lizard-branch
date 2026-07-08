"""M1 harness bake-off runner — measures Claude Code vs. OpenCode on identical step specs.

Never touches the live repo: every trial resets an isolated fork to a `base-N` git tag before
and after running, via ``git reset --hard`` + ``git clean -fdq``. See
``meta_m1_harness/META_M1_PREREGISTRATION.md`` for the locked measurement design this instrument
implements, and ``docs/concepts/meta_m1_harness_plan.md`` §6 for the full spec.

Credential handling (corrected 2026-07-08, Nikinger override of the plan's original M1-D5
wording): the separate bake-off Anthropic key is never a shell-exported env var and never in
a file — same OS-keyring strategy as the bot itself (see
``phase1_broker_wrapper/broker_wrapper/credentials.py``). Seed it once via
``store_bakeoff_key.py``; this module fetches it from the keyring and hands it to each harness
subprocess's own environment only, in memory, per call — never the operator's shell.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from datetime import time as dt_time
from pathlib import Path
from zoneinfo import ZoneInfo

import keyring

logger = logging.getLogger(__name__)


# Own dedicated keyring namespace — deliberately independent of broker_wrapper.credentials
# ("tradingbot", the live bot's service) and of the fork's neutralized service
# ("trading-bot-bakeoff-void", M1-D8). See store_bakeoff_key.py.
BAKEOFF_KEYRING_SERVICE = "trading-bot-bakeoff-runner"
BAKEOFF_KEYRING_USERNAME = "anthropic_api_key"


class BudgetExceeded(Exception):
    """Raised when a charge would push cumulative bake-off spend past the hard cap."""


PRICE_EUR_PER_MTOK: dict[str, tuple[float, float]] = {
    # ponytail: placeholder Sonnet-5 pricing (input, output) in EUR/million tokens.
    # [VERIFY] against current Anthropic pricing before Step 5/7 ever spends real budget
    # (M1 plan §6 flags this constant explicitly).
    "sonnet-5": (3.0, 15.0),
}


@dataclass(frozen=True)
class HarnessConfig:
    """A coding harness's CLI shape. Model flag is baked into argv_template so it never drifts."""

    name: str
    argv_template: list[str]
    usage_regex: str | None = None  # must have a named group `tokens`
    timeout_s: int = 1800


@dataclass
class TrialResult:
    harness: str
    step: str
    repeat: int
    exit_ok: bool
    gate_passed: bool
    wall_seconds: float
    edit_failures: int
    files_changed: int
    usage_tokens: float | None = None
    error: str = ""
    extra: dict = field(default_factory=dict)


@dataclass(frozen=True)
class StepSpec:
    step_id: str
    spec_path: Path
    base_tag: str
    gate_argv: list[str]


class BudgetGuard:
    """Hard EUR cap on bake-off spend. Trips before the cap is crossed, not after."""

    def __init__(self, cap_eur: float, model_key: str = "sonnet-5") -> None:
        self.cap_eur = cap_eur
        self.model_key = model_key
        self.spent_eur = 0.0

    def add(self, tokens_in: float, tokens_out: float) -> None:
        price_in, price_out = PRICE_EUR_PER_MTOK[self.model_key]
        cost = (tokens_in / 1_000_000) * price_in + (tokens_out / 1_000_000) * price_out
        self._charge(cost)

    def add_manual_eur(self, eur: float) -> None:
        self._charge(eur)

    def remaining(self) -> float:
        return self.cap_eur - self.spent_eur

    def _charge(self, eur: float) -> None:
        if self.spent_eur + eur > self.cap_eur:
            raise BudgetExceeded(
                f"budget exceeded: {self.spent_eur + eur:.2f}€ > {self.cap_eur:.2f}€ cap"
            )
        self.spent_eur += eur


# --- Git isolation -----------------------------------------------------------------


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=check
    )


def assert_clean_repo(repo: Path) -> None:
    if not (repo / ".git").exists():
        raise SystemExit(f"[safety] {repo} is not a git repo — refusing to run bake-off trials")
    status = _git(repo, "status", "--porcelain", check=False)
    if status.stdout.strip():
        raise SystemExit(
            f"[safety] {repo} has uncommitted changes — refusing to run bake-off trials "
            "against a dirty tree"
        )


def snapshot_ref(repo: Path) -> str:
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def reset_to(repo: Path, ref: str) -> None:
    _git(repo, "reset", "--hard", ref)
    _git(repo, "clean", "-fdq")


def changed_files(repo: Path, ref: str) -> list[str]:
    # git diff alone misses brand-new untracked files (harnesses are told not to commit) -
    # combine tracked-file diffs against ref with untracked-but-not-gitignored new files.
    tracked = _git(repo, "diff", "--name-only", ref).stdout.splitlines()
    untracked = _git(repo, "ls-files", "--others", "--exclude-standard").stdout.splitlines()
    return sorted({line.strip() for line in (*tracked, *untracked) if line.strip()})


# --- Guards -------------------------------------------------------------------------


def assert_offhours(now: datetime) -> None:
    """Refuses Mon-Fri 08:00-18:00 Europe/Berlin. Override: env BAKEOFF_FORCE_WINDOW=1."""
    if os.environ.get("BAKEOFF_FORCE_WINDOW") == "1":
        return
    berlin_now = now.astimezone(ZoneInfo("Europe/Berlin"))
    if berlin_now.weekday() < 5 and dt_time(8, 0) <= berlin_now.time() < dt_time(18, 0):
        raise SystemExit(
            "[safety] inside the Mon-Fri 08:00-18:00 Europe/Berlin trading window — bake-off "
            "trials only run offhours. Set BAKEOFF_FORCE_WINDOW=1 to override."
        )


# --- Trial execution ------------------------------------------------------------------


def _compute_edit_failures(exit_ok: bool, files_changed: int, gate_passed: bool) -> int:
    """Harness claimed success but wrote nothing to disk — the plan's fixed definition."""
    return 1 if (exit_ok and files_changed == 0 and not gate_passed) else 0


def _load_preamble() -> str:
    return (Path(__file__).parent / "preamble.txt").read_text(encoding="utf-8").strip()


def _fetch_bakeoff_api_key() -> str:
    """Reads the separate bake-off Anthropic key from the OS keyring — never a shell env var,
    never a file. Seed it once via ``store_bakeoff_key.py``."""
    value = keyring.get_password(BAKEOFF_KEYRING_SERVICE, BAKEOFF_KEYRING_USERNAME)
    if not value:
        raise SystemExit(
            f"[safety] no bake-off Anthropic key in the OS keyring "
            f"(service={BAKEOFF_KEYRING_SERVICE!r}, username={BAKEOFF_KEYRING_USERNAME!r}). "
            "Run: python meta_m1_harness/bakeoff/store_bakeoff_key.py"
        )
    return value


def run_trial(
    repo: Path, harness: HarnessConfig, spec: StepSpec, repeat: int, budget: BudgetGuard
) -> TrialResult:
    assert_clean_repo(repo)
    reset_to(repo, spec.base_tag)
    ref_before = snapshot_ref(repo)
    try:
        error = ""
        exit_ok = False
        usage_tokens: float | None = None
        wall_start = time.monotonic()
        try:
            prompt = _load_preamble() + "\n\n" + spec.spec_path.read_text(encoding="utf-8")
            argv = [
                part.format(prompt=prompt, prompt_file=str(spec.spec_path))
                for part in harness.argv_template
            ]
            # Fetched fresh from the keyring for this one subprocess call only — never
            # exported into the operator's own shell, never persisted anywhere.
            proc_env = {**os.environ, "ANTHROPIC_API_KEY": _fetch_bakeoff_api_key()}
            proc = subprocess.run(
                argv, cwd=repo, capture_output=True, text=True, timeout=harness.timeout_s,
                env=proc_env,
            )
            exit_ok = proc.returncode == 0
            if harness.usage_regex:
                match = re.search(harness.usage_regex, proc.stdout)
                if match:
                    usage_tokens = float(match.group("tokens"))
        except subprocess.TimeoutExpired:
            error = "timeout"
        except OSError as exc:
            error = str(exc)
        wall_seconds = time.monotonic() - wall_start

        changed = changed_files(repo, ref_before)
        gate_passed = False
        if exit_ok:
            try:
                gate_proc = subprocess.run(
                    spec.gate_argv, cwd=repo, capture_output=True, text=True,
                    timeout=harness.timeout_s,
                )
                gate_passed = gate_proc.returncode == 0
            except (subprocess.TimeoutExpired, OSError) as exc:
                error = error or f"gate: {exc}"

        if usage_tokens is not None:
            # ponytail: usage_regex yields one combined token figure; costed entirely at
            # the (higher) output rate as a conservative upper bound on real spend.
            budget.add(tokens_in=0.0, tokens_out=usage_tokens)
        else:
            budget.add_manual_eur(_prompt_operator_for_manual_spend(harness, spec))

        return TrialResult(
            harness=harness.name,
            step=spec.step_id,
            repeat=repeat,
            exit_ok=exit_ok,
            gate_passed=gate_passed,
            wall_seconds=wall_seconds,
            edit_failures=_compute_edit_failures(exit_ok, len(changed), gate_passed),
            files_changed=len(changed),
            usage_tokens=usage_tokens,
            error=error,
        )
    finally:
        reset_to(repo, ref_before)


def _prompt_operator_for_manual_spend(harness: HarnessConfig, spec: StepSpec) -> float:
    while True:
        raw = input(
            f"[bakeoff] usage unparseable for {harness.name}/{spec.step_id} — enter cumulative "
            "console spend in EUR for this trial (e.g. 0.22 or 0,22): "
        )
        try:
            return float(raw.strip().replace(",", "."))
        except ValueError:
            print(f"  not a number: {raw!r} — try again")


def run_matrix(
    repo: Path,
    harnesses: list[HarnessConfig],
    specs: list[StepSpec],
    repeats: int,
    budget: BudgetGuard,
    results_path: Path,
) -> list[TrialResult]:
    results: list[TrialResult] = []
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with results_path.open("a", encoding="utf-8") as fh:
        for spec in specs:
            for repeat in range(1, repeats + 1):
                for harness in harnesses:
                    result = run_trial(repo, harness, spec, repeat, budget)
                    fh.write(json.dumps(asdict(result)) + "\n")
                    fh.flush()
                    results.append(result)
    return results


# --- Harness templates + step registry ------------------------------------------------

# Verified 2026-07-08 against `claude --help` (this session) and https://opencode.ai/docs/cli/
# (WebFetch). Model string is claude-sonnet-5 per M1-D4 (Sonnet 5, Effort Medium, both
# harnesses). OpenCode's --variant value is still [VERIFY] — provider-specific naming,
# confirm against the installed OpenCode instance at Step 5 (Setup-Smoke S0) before trusting it.

CLAUDE_CODE = HarnessConfig(
    name="claude_code",
    argv_template=[
        "claude", "-p", "{prompt}",
        "--model", "claude-sonnet-5",
        "--effort", "medium",
        "--output-format", "json",
        "--dangerously-skip-permissions",  # defensible only inside the M1-D8 fork isolation
    ],
)

OPENCODE = HarnessConfig(
    name="opencode",
    argv_template=[
        "opencode", "run", "{prompt}",
        "--model", "anthropic/claude-sonnet-5",
        "--variant", "<VARIANT>",  # [VERIFY] provider-specific effort value at Step 5
        "--format", "json",
        "--auto",  # non-interactive permission auto-approve, defensible only in the M1-D8 fork
    ],
)

_HARNESS_BY_NAME: dict[str, HarnessConfig] = {"claude_code": CLAUDE_CODE, "opencode": OPENCODE}

_STEP_GATE_ARGV: dict[str, list[str]] = {
    "S0": ["pytest", "phase10_v3/tests/test_smoke.py", "-q"],
    "S1": ["pytest", "phase10_v3/tests/test_models.py", "-q"],
    "S2": ["pytest", "phase10_v3/tests/test_classifier.py", "-q"],
    "S3": ["pytest", "phase10_v3/tests/test_store.py", "-q"],
    "S4": ["pytest", "phase10_v3/tests/test_reflect.py", "-q"],
    "S5": ["pytest", "phase10_v3/tests/test_sink.py", "phase5_execution/tests/", "-q"],
    "S6": ["pytest", "phase10_v3/tests/test_research_injection.py", "phase4_research/tests/", "-q"],
    "S7": ["pytest", "phase10_v3/tests/test_report.py", "-q"],
}


def _base_tag_for(step_id: str) -> str:
    k = int(step_id[1:])
    return f"base-{max(k - 1, 0)}"


def _load_step_spec(repo: Path, step_id: str) -> StepSpec:
    return StepSpec(
        step_id=step_id,
        spec_path=repo / "meta_m1_harness" / "specs" / f"{step_id}.md",
        base_tag=_base_tag_for(step_id),
        gate_argv=_STEP_GATE_ARGV[step_id],
    )


def _print_matrix(harnesses: list[HarnessConfig], specs: list[StepSpec], repeats: int) -> None:
    for spec in specs:
        for repeat in range(1, repeats + 1):
            for harness in harnesses:
                argv = [
                    part.format(prompt=f"<prompt:{spec.step_id}>", prompt_file=str(spec.spec_path))
                    for part in harness.argv_template
                ]
                print(
                    f"{spec.step_id} repeat={repeat} harness={harness.name} "
                    f"base={spec.base_tag} argv={argv}"
                )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="M1 harness bake-off runner")
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--steps", default="S1,S2,S3,S4,S5")
    parser.add_argument("--harness", default="claude_code,opencode")
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument(
        "--results", type=Path, default=Path("meta_m1_harness/results/trials.jsonl")
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    harnesses = [_HARNESS_BY_NAME[name] for name in args.harness.split(",")]
    specs = [_load_step_spec(args.repo, step_id) for step_id in args.steps.split(",")]

    if args.dry_run:
        _print_matrix(harnesses, specs, args.repeats)
        return 0

    assert_offhours(datetime.now(ZoneInfo("Europe/Berlin")))
    assert_clean_repo(args.repo)
    budget = BudgetGuard(cap_eur=50.0)
    run_matrix(args.repo, harnesses, specs, args.repeats, budget, args.results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
