#!/usr/bin/env python3
"""Hard-assert live verification for the Phase-6 debate — the Phase-6 gate.

Runs one **full** Phase-5 execution cycle **with the Bull/Bear/Judge debate injected**
at the Gate-2↔Gate-3 seam, against IG Demo, and asserts the cycle's invariants, then
exits ``0`` (PASS) / ``1`` (FAIL). It auto-confirms (running live_test *is* the consent)
and, when a fresh candidate exists and the debate returns TRADE through all gates/VETOs,
**places a real Demo order** and monitors it to a close (``max_hold_minutes`` /
``poll_interval_s`` overridden small so the time-stop closes within ~a minute).

A clean ``NO_TRADE`` (a gate/VETO/debate-ABSTAIN said no) is **also** a valid exit-0
outcome. Only a fail-closed ``ABORT`` is a failure.

**When the debate actually ran** (Gate 1 passed + a fresh seeded candidate existed), two
extra proofs are asserted: a new record was appended to ``debate_log.json`` (the Module-7
audit), and the token meter shows **cache reads > 0** (proof the prefix caching is
working — Decision D). When the debate did **not** run (market closed → Gate 1, or no
fresh candidate), those proofs are skipped (the cycle still passes if clean).

Seed a candidate first (30-min TTL), in the trade window, with the current move::

    python phase5_execution/scripts/seed_candidate.py --direction SELL

Live script: keyring + IG Demo + a real Anthropic request + a real Demo order;
non-deterministic; deliberately not collected by ``pytest`` / CI. **The operator runs
it.** Prereqs: IG Demo creds + ``anthropic_api_key`` in the keyring;
``bash scripts/dev_install.sh``.

Output discipline: the PASS/FAIL table + ``RESULT`` line → **stderr**; the single
machine-readable result JSON → **stdout**.

Usage:
    python scripts/live_test.py
    python scripts/live_test.py --broker ig_demo --verbose
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Make the project dir importable so the (non-installed) `scripts` package resolves.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent  # phase6_debate/
sys.path.insert(0, str(_PROJECT_ROOT))

from execution.config import ExecutionConfig  # noqa: E402
from execution.ig_bot import make_confirm_fn, result_to_dict  # noqa: E402

log = logging.getLogger("phase6.live_test")

_PLACED_AND_CLOSED = {"CLOSED_BY_BROKER", "TIME_STOP"}
_NO_ORDER = {"NO_TRADE", "ABORTED_BY_USER"}
_OK_STATUSES = _PLACED_AND_CLOSED | _NO_ORDER

_DATA_STATE = _PROJECT_ROOT.parent / "data" / "state"
_DEBATE_LOG = _DATA_STATE / "debate_log.json"
_USAGE_LOG = _DATA_STATE / "llm_usage.json"


def _eprint(message: str = "") -> None:
    print(message, file=sys.stderr)


def _load_json_array(path: Path) -> list[dict[str, Any]]:
    """Load a JSON-array log, tolerating absence/corruption (advisory read)."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []
    return data if isinstance(data, list) else []


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--broker", default="ig_demo", help="broker id (default: ig_demo)")
    parser.add_argument("--verbose", action="store_true", help="DEBUG logging")
    args = parser.parse_args(argv)

    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    # Short hold + fast polling so a placed order self-closes (time-stop) quickly.
    config = ExecutionConfig(max_hold_minutes=1, poll_interval_s=10)
    check = _Check()

    from scripts.wiring import build_executor

    # Snapshot the audit/usage logs so we can detect what the debate appended.
    debate_records_before = len(_load_json_array(_DEBATE_LOG))
    usage_records_before = len(_load_json_array(_USAGE_LOG))

    _eprint(f"[live] building executor + debate (broker={args.broker}, "
            f"max_hold={config.max_hold_minutes}m, poll={config.poll_interval_s}s)")
    executor = build_executor(
        config,
        confirm_fn=make_confirm_fn(auto_yes=True, dry=False),
        broker_name=args.broker,
    )

    _eprint("[live] --- running full cycle with debate (IG Demo; may place + close) ---")
    result: Any = None
    try:
        result = executor.run()
        run_ok = True
    except Exception as exc:  # noqa: BLE001 — the gate must report, not crash
        run_ok = False
        log.exception("executor.run raised")
        _eprint(f"[live] run() raised: {type(exc).__name__}: {exc}")

    check("executor.run() completed without raising", run_ok)

    if run_ok:
        check("status is a clean, known outcome (not ABORT)",
              result.status in _OK_STATUSES,
              f"status={result.status} detail={result.detail!r}")

        debate_records = _load_json_array(_DEBATE_LOG)
        debate_ran = len(debate_records) > debate_records_before

        if debate_ran:
            _eprint("[live] the debate ran this cycle — asserting its proofs.")
            last = debate_records[-1]
            check("a debate record was appended to debate_log.json",
                  True, f"final_decision={last.get('final_decision')} "
                        f"final_direction={last.get('final_direction')}")
            usage_records = _load_json_array(_USAGE_LOG)
            new_usage = usage_records[usage_records_before:]
            cache_reads = sum(r.get("cache_read_input_tokens", 0) for r in new_usage)
            check("token meter shows cache reads > 0 (prefix caching works)",
                  cache_reads > 0, f"cache_read_input_tokens={cache_reads}")
        else:
            _eprint("[live] the debate did NOT run this cycle (Gate 1 / no fresh "
                    "candidate). Skipping the debate-specific proofs — still a valid "
                    "exit-0 if the cycle was clean. Seed a candidate in the window and "
                    "re-run to exercise the debate.")

        if result.status in _PLACED_AND_CLOSED:
            _eprint(f"[live] outcome: ORDER PLACED → {result.status}")
            check("a deal_id was assigned", bool(result.deal_id),
                  f"deal_id={result.deal_id!r}")
        else:
            _eprint(f"[live] outcome: {result.status} — clean no-trade "
                    "(gate/VETO/debate-ABSTAIN said no). A valid exit-0 result.")

    # Machine-readable: the cycle result (empty object if the run raised).
    print(json.dumps(result_to_dict(result) if run_ok else {}, indent=2))

    passed = check.total - check.failures
    _eprint(f"\nRESULT: {passed}/{check.total} passed")
    return 0 if check.failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
