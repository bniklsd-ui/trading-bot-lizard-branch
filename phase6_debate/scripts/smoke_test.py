#!/usr/bin/env python3
"""DRY smoke test for the Phase-6 debate — one real Bull/Bear/Judge debate, no executor.

Runs a single debate over a **seeded** Phase-4 candidate against IG Demo + a **real
LLM request**, prints the transcript + token summary, and exits 0. It is *dry*: no
executor, no order, and **no audit write** (``build_debate(with_audit=False)``) — just
the debate, so the operator can eyeball the rounds and the cache behaviour before the
hard-asserted ``live_test.py``.

Seed a candidate first with the existing Phase-5 tool (30-min TTL)::

    python phase5_execution/scripts/seed_candidate.py --direction SELL

Live script: touches the keyring + IG Demo + a real Anthropic request; non-deterministic;
deliberately not collected by ``pytest`` / CI. **The operator runs it.**

Output discipline: progress + the human-readable transcript/summary → **stderr**; the
single machine-readable outcome JSON → **stdout**.

Usage:
    python scripts/smoke_test.py
    python scripts/smoke_test.py --broker ig_demo --verbose
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

_STATE_DIR = _PROJECT_ROOT.parent / "data" / "state"

log = logging.getLogger("phase6.smoke_test")


def _eprint(message: str = "") -> None:
    print(message, file=sys.stderr)


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

    from broker_wrapper import get_broker
    from persistence import StateManager

    from scripts.wiring import build_debate

    # The seeded Phase-4 candidate Gate 2 would normally hand the debate.
    state = StateManager(str(_STATE_DIR))
    candidates = state.load_candidates()
    if not candidates:
        _eprint("[smoke] no seeded candidate found in turbo_candidates.json — seed one "
                "first:\n  python phase5_execution/scripts/seed_candidate.py --direction SELL")
        return 1
    candidate = candidates[0]
    _eprint(f"[smoke] candidate: {candidate['direction']} {candidate['epic']} "
            f"(seed conf {candidate.get('llm_confidence')})")

    # Connect the broker — the context builder reads fresh price/OHLCV/market-info.
    broker = get_broker(args.broker)
    connect_env = broker.connect()
    if not getattr(connect_env, "ok", False):
        _eprint(f"[smoke] broker connect failed: {getattr(connect_env, 'error', None)}")
        return 1

    _eprint("[smoke] --- running one debate (dry, real LLM, no audit write) ---")
    debate = build_debate(broker, with_audit=False)
    outcome: Any = debate.run(candidate)

    # Human-readable transcript + cost summary → stderr.
    _eprint(f"\n[smoke] verdict: {outcome.decision} "
            f"direction={outcome.direction} confidence={outcome.confidence} "
            f"(advisory) rounds={outcome.rounds_used}")
    _eprint(f"[smoke] rationale: {outcome.rationale}")
    for turn in outcome.transcript:
        text = turn.text if len(turn.text) <= 280 else turn.text[:277] + "..."
        _eprint(f"  · r{turn.round} {turn.agent} [{turn.model}]: {text}")
    ts = outcome.token_summary
    _eprint(f"\n[smoke] tokens: in={ts.get('input_tokens')} out={ts.get('output_tokens')} "
            f"cache_read={ts.get('cache_read_input_tokens')} "
            f"cache_write={ts.get('cache_creation_input_tokens')} "
            f"≈${ts.get('est_cost_usd')} / €{ts.get('est_cost_eur')}")

    # Machine-readable: the full outcome.
    print(json.dumps(outcome.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
