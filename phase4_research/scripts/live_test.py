#!/usr/bin/env python3
"""Hard-assert live verification for the Phase-4 research layer — the Phase-4 gate.

Runs one **full** research cycle against IG Demo + the real Anthropic call and
asserts the cycle's invariants, then exits ``0`` (PASS) / ``1`` (FAIL). This is
the analogue of Phase-3's ``scripts/live_test.py`` and the concept's Done-Kriterium:
the run must end in **exactly one** outcome — a valid persisted ``turbo_candidates
.json`` *or* a clean, documented abstain — and on a persisted pick the frozen
10-field Candidate contract must hold.

Unlike ``smoke_test.py`` this one uses the **real** ``StateManager``: a PASS
writes ``<repo_root>/data/state/turbo_candidates.json`` (the Phase-4 → Phase-5
hand-off). An abstain writes an empty list (no trade). Both are exit-0 outcomes;
the run()-logged reason (printed to stderr below) tells which and why.

The hallucination proof-test (an invented epic / inflated confidence / old
``CALL`` caught by the validator before it becomes a candidate) is covered
deterministically by ``tests/test_research.py`` and runs in CI — it is *not*
forced here, because this script drives the **real** model and cannot make it
hallucinate on demand. The guarantee this script adds is that the same validator
+ filter path executes live and only a contract-valid pick is ever persisted.

Live script: touches the keyring + IG Demo + the LLM, is non-deterministic, and
is deliberately not collected by ``pytest`` / CI.

Output discipline (concept §8): the PASS/FAIL table + ``RESULT`` line → **stderr**;
the single machine-readable JSON (the persisted candidate list) → **stdout**.

Prereqs: IG Demo creds + ``anthropic_api_key`` in the keyring (Phase-1
``scripts/store_credential.py``), and the ``anthropic`` SDK installed.

Usage:
    python scripts/live_test.py
    python scripts/live_test.py --epic IX.D.DAX.IFMM.IP --volume-proxy EXS1.DE
    python scripts/live_test.py --model claude-sonnet-4-6 --verbose
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Make the `research` package + the wiring importable when run as a script.
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent  # phase4_research/
sys.path.insert(0, str(_PACKAGE_ROOT))

from research import ResearchConfig  # noqa: E402

log = logging.getLogger("phase4.live_test")

# The frozen Phase-4 → Phase-5 Candidate contract (concept §; CLAUDE.md).
_CONTRACT_KEYS = {
    "epic", "direction", "llm_confidence", "reasoning", "spread_pct_at_pick",
    "drift_at_pick", "score_at_pick", "threshold_applied", "generated_at", "source",
}


def _eprint(message: str = "") -> None:
    """Human-readable progress → stderr (stdout is reserved for the JSON)."""
    print(message, file=sys.stderr)


class _Check:
    """Tiny PASS/FAIL recorder so the script reads like a checklist."""

    def __init__(self) -> None:
        self.failures = 0
        self.total = 0

    def __call__(self, label: str, condition: bool, detail: str = "") -> bool:
        self.total += 1
        ok = bool(condition)
        if not ok:
            self.failures += 1
        mark = "✓" if ok else "✗"
        suffix = f" — {detail}" if detail else ""
        _eprint(f"  {mark} {label}{suffix}")
        return ok


def _is_iso_utc(value: Any) -> bool:
    """True if ``value`` parses as an ISO-8601 UTC instant (``...Z``)."""
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _check_contract(check: _Check, cand: dict[str, Any], config: ResearchConfig) -> None:
    """Assert a persisted candidate honours the frozen 10-field contract."""
    check("candidate has exactly the 10 contract keys",
          set(cand) == _CONTRACT_KEYS,
          f"got {sorted(cand)}")
    check("epic ∈ allow-list", cand.get("epic") in config.epic_allowlist,
          f"epic={cand.get('epic')!r}")
    check("direction ∈ {BUY, SELL}", cand.get("direction") in ("BUY", "SELL"),
          f"direction={cand.get('direction')!r}")
    conf = cand.get("llm_confidence")
    check("llm_confidence is 0..100",
          isinstance(conf, (int, float)) and 0 <= conf <= 100,
          f"llm_confidence={conf!r}")
    check("source == 'research'", cand.get("source") == "research",
          f"source={cand.get('source')!r}")
    check("generated_at is ISO-8601 UTC", _is_iso_utc(cand.get("generated_at")),
          f"generated_at={cand.get('generated_at')!r}")
    spread = cand.get("spread_pct_at_pick")
    check("spread_pct_at_pick is numeric", isinstance(spread, (int, float)),
          f"spread_pct_at_pick={spread!r}")


def _build_config(args: argparse.Namespace) -> ResearchConfig:
    return ResearchConfig(
        model=args.model,
        epic_allowlist=(args.epic,),
        volume_proxy=args.volume_proxy or None,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epic", default=ResearchConfig().epic_allowlist[0],
                        help="anchor / allow-list epic (default: DAX cash)")
    parser.add_argument("--volume-proxy", default=ResearchConfig().volume_proxy,
                        help="ETF volume proxy for ^GDAXI (default: EXS1.DE; "
                             "pass empty to disable)")
    parser.add_argument("--model", default=ResearchConfig().model,
                        help="Anthropic model id")
    parser.add_argument("--verbose", action="store_true", help="DEBUG logging")
    args = parser.parse_args(argv)

    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    config = _build_config(args)
    check = _Check()

    from scripts.wiring import build_research  # noqa: E402

    _eprint(f"[live] building research (epic={config.epic_allowlist[0]}, "
            f"model={config.model}, volume_proxy={config.volume_proxy})")
    research = build_research(config)

    # Start from a clean slate so the post-run assertions are unambiguous.
    research.state.clear_candidates()

    _eprint("[live] --- running full cycle (IG Demo + real LLM) ---")
    persisted: list[dict[str, Any]] = []
    try:
        candidates = research.run()
        run_ok = True
    except Exception as exc:  # noqa: BLE001 — the gate must report, not crash
        candidates = []
        run_ok = False
        log.exception("research.run raised")
        _eprint(f"[live] run() raised: {type(exc).__name__}: {exc}")

    check("research.run() completed without raising", run_ok)

    # The persistence invariant: load_candidates() must mirror the run() return.
    reloaded = research.state.load_candidates() if run_ok else []
    check("persistence invariant: load_candidates() mirrors run() return",
          len(reloaded) == len(candidates),
          f"run()={len(candidates)} reloaded={len(reloaded)}")

    if candidates:
        # PASS path — a candidate was persisted; assert the frozen contract.
        persisted = reloaded
        _eprint("[live] outcome: PICK — validating the persisted contract")
        check("exactly one candidate persisted", len(reloaded) == 1,
              f"count={len(reloaded)}")
        if reloaded:
            _check_contract(check, reloaded[0], config)
    elif run_ok:
        # Abstain path — a clean no-trade is a valid exit-0 outcome.
        _eprint("[live] outcome: ABSTAIN — clean no-trade (reason in the log "
                "above: session-health / empty universe / LLM error / validator "
                "REJECT / filter REJECT).")
        check("abstain persisted an empty candidate list", reloaded == [],
              f"reloaded={reloaded!r}")

    # Machine-readable: exactly what is on disk (a 1-list on PASS, [] on abstain).
    print(json.dumps(persisted, indent=2))

    passed = check.total - check.failures
    _eprint(f"\nRESULT: {passed}/{check.total} passed")
    return 0 if check.failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
