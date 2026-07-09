"""M1 harness bake-off runner — measures Claude Code vs. OpenCode on identical step specs.

Never touches the live repo: every trial resets an isolated fork to a `base-N` git tag before
and after running, via ``git reset --hard`` + ``git clean -fdq``. See
``meta_m1_harness/META_M1_PREREGISTRATION.md`` for the locked measurement design this instrument
implements, and ``docs/concepts/meta_m1_harness_plan.md`` §6 for the full spec.

Live-repo lockdown (added 2026-07-08 after a real incident): a harness subprocess's own ``cwd``
is not a hard sandbox boundary — an agent's own shell tool can ``cd`` anywhere the OS user can
reach, including out of the fork. Real case: an OpenCode/S0 trial ran ``cd
/home/trading-bot/trading-bot && pytest ...`` from inside its own bash tool and wrote
``phase10_v3/`` into *this* live repo despite ``cwd=<fork>``, while the harness's own gate-check
(correctly scoped to the fork) saw nothing and reported a false ``gate_passed=false``. Every
harness subprocess call is now wrapped in ``_live_repo_lockdown()``, which strips the write bit
from every file/dir in this live repo (this process's own OS user, so it is a real enforced
boundary, not just a convention) for the call's duration and restores it after — a backstop, not
a replacement for correctly scoping each harness to the fork (see OPENCODE's ``--dir`` flag).

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
    # Verified 2026-07-08 against docs.claude.com model overview: real Sonnet-5 price is
    # $3/$15 per MTok standard, $2/$10 introductory (until 2026-08-31, active now) — both in
    # USD, and OpenCode's own model registry reports the same $2/$10 figures. Kept at the
    # higher (3.0, 15.0) numbers here deliberately as a conservative EUR stand-in: real cost is
    # lower than this in USD terms, so the BudgetGuard trips earlier than a real overspend
    # could occur, never later. ponytail: no live FX lookup, add one only if the cap starts
    # tripping too early in practice.
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


# --- Live-repo lockdown (defense-in-depth, see module docstring) -------------------------

_LIVE_REPO_ROOT = Path(__file__).resolve().parents[2]


def _live_repo_lockdown() -> list[tuple[Path, int]]:
    """Strip the write bit from every file/dir in the live repo. Returns the (path, original
    mode) pairs needed to restore it — always pass this to _restore_permissions(), even on an
    exception path, or the live repo stays locked."""
    original: list[tuple[Path, int]] = []
    paths = [_LIVE_REPO_ROOT, *(p for p in _LIVE_REPO_ROOT.rglob("*") if ".git" not in p.parts)]
    for p in paths:
        try:
            mode = p.stat().st_mode
        except OSError:
            continue
        original.append((p, mode))
        try:
            p.chmod(mode & ~0o222)
        except OSError:
            pass
    return original


def _restore_permissions(original: list[tuple[Path, int]]) -> None:
    for p, mode in original:
        try:
            p.chmod(mode)
        except OSError:
            pass


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


def _write_trial_log(
    harness: HarnessConfig, spec: StepSpec, repeat: int, stdout: str, stderr: str
) -> None:
    # Raw regex-parsed stdout/stderr was previously discarded after each trial, leaving no way
    # to diagnose a trial that exits 0 but does nothing (real case: opencode/S0, 2026-07-08).
    log_dir = Path(__file__).parent.parent / "results" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{harness.name}_{spec.step_id}_r{repeat}_{int(time.time())}.log"
    log_path.write_text(f"--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}\n", encoding="utf-8")


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
                part.format(prompt=prompt, prompt_file=str(spec.spec_path), repo=str(repo))
                for part in harness.argv_template
            ]
            # Fetched fresh from the keyring for this one subprocess call only — never
            # exported into the operator's own shell, never persisted anywhere.
            proc_env = {**os.environ, "ANTHROPIC_API_KEY": _fetch_bakeoff_api_key()}
            # Live-repo lockdown for exactly the harness's own subprocess call — see module
            # docstring. Lifted immediately after so this trial's own bookkeeping writes
            # (log file, trials.jsonl) still work.
            _locked_perms = _live_repo_lockdown()
            try:
                proc = subprocess.run(
                    argv, cwd=repo, capture_output=True, text=True, timeout=harness.timeout_s,
                    env=proc_env,
                )
            finally:
                _restore_permissions(_locked_perms)
            exit_ok = proc.returncode == 0
            _write_trial_log(harness, spec, repeat, proc.stdout, proc.stderr)
            if harness.usage_regex:
                # findall + sum, not search-first-match: OpenCode's --format json streams one
                # JSON object per step, so a multi-step trial can emit several cost lines: a
                # first-match-only would silently undercount. Claude Code's --output-format
                # json emits one final object, so sum-of-one == the same value either way.
                matches = re.findall(harness.usage_regex, proc.stdout)
                if matches:
                    usage_tokens = sum(float(m) for m in matches)
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
            # usage_regex captures each harness's own authoritative real cost (USD) straight
            # from its JSON output — total_cost_usd (Claude Code) / cost (OpenCode) — not a
            # token count. Passed straight to the EUR cap: USD and EUR trade near parity, and
            # treating USD as EUR is the conservative direction (never understates real spend).
            budget.add_manual_eur(usage_tokens)
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
        try:
            raw = input(
                f"[bakeoff] usage unparseable for {harness.name}/{spec.step_id} — enter "
                "cumulative console spend in EUR for this trial (e.g. 0.22 or 0,22): "
            )
        except EOFError:
            # No operator attached (non-interactive run) — money was already spent on this
            # trial's real subprocess call; record 0.0 and flag loudly rather than crashing and
            # losing the whole trial result (and aborting every trial still queued after it).
            logger.warning(
                "%s/%s: no operator to answer the manual-spend prompt (non-interactive stdin) "
                "— recording spend as 0.0, verify the real cost manually against the console",
                harness.name, spec.step_id,
            )
            return 0.0
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
# (WebFetch). Model string is claude-sonnet-5. Effort corrected 2026-07-08 (Nikinger, same
# session) from the plan's original "Medium" to "high": docs.claude.com confirms Sonnet 5
# defaults to effort=high on both the Claude API and Claude Code when unset ("auto") — that IS
# the project's real/production execution config referenced by M1-D4 ("reale Execution-Config
# des Projekts"), not medium. OpenCode's --variant value confirmed 2026-07-08 via `opencode
# models anthropic --verbose` (real call, ANTHROPIC_API_KEY from keyring in the subprocess env
# only, nothing persisted to disk) — claude-sonnet-5's variants are {low, medium, high, xhigh,
# max}; "high" matches Claude Code's --effort high exactly (M1-D4, corrected value).

CLAUDE_CODE = HarnessConfig(
    name="claude_code",
    argv_template=[
        "claude", "-p", "{prompt}",
        "--model", "claude-sonnet-5",
        "--effort", "high",
        "--output-format", "json",
        "--dangerously-skip-permissions",  # defensible only inside the M1-D8 fork isolation
    ],
    # verified 2026-07-08 (real `claude -p --output-format json` call): the single JSON object
    # carries one top-level "total_cost_usd" field — the SDK's own authoritative real cost.
    usage_regex=r'"total_cost_usd":(?P<tokens>[\d.]+)',
)

OPENCODE = HarnessConfig(
    name="opencode",
    argv_template=[
        "opencode", "run", "{prompt}",
        "--model", "anthropic/claude-sonnet-5",
        "--variant", "high",  # corrected 2026-07-08 — matches Claude Code's --effort high (M1-D4)
        "--format", "json",
        "--auto",  # non-interactive permission auto-approve, defensible only in the M1-D8 fork
        "--dir", "{repo}",  # added 2026-07-08: subprocess cwd alone did not confine the agent
        # (real incident — see module docstring); --dir is OpenCode's own scoping flag.
    ],
    # verified 2026-07-08 (real `opencode run --format json` call): NDJSON, one "step_finish"
    # event per step with its own "cost" field — summed by run_trial() across every step.
    usage_regex=r'"cost":(?P<tokens>[\d.]+)',
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


def _print_matrix(
    repo: Path, harnesses: list[HarnessConfig], specs: list[StepSpec], repeats: int
) -> None:
    for spec in specs:
        for repeat in range(1, repeats + 1):
            for harness in harnesses:
                argv = [
                    part.format(
                        prompt=f"<prompt:{spec.step_id}>",
                        prompt_file=str(spec.spec_path),
                        repo=str(repo),
                    )
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
        _print_matrix(args.repo, harnesses, specs, args.repeats)
        return 0

    assert_offhours(datetime.now(ZoneInfo("Europe/Berlin")))
    assert_clean_repo(args.repo)
    budget = BudgetGuard(cap_eur=50.0)
    run_matrix(args.repo, harnesses, specs, args.repeats, budget, args.results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
