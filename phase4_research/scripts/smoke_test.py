#!/usr/bin/env python3
"""Quick **live** DRY sanity run of the Phase-4 research cycle (concept §8).

Runs one real ``Research.run`` against IG Demo + the real Anthropic call, but
**persists nothing** — the ``StateManager`` is swapped for a DRY sink whose
``save_candidates`` is a no-op recorder. Use it to eyeball the deterministic
context the LLM sees and the cycle's outcome (a pick or an abstain) without
touching ``turbo_candidates.json``. It *prints*; it does not hard-assert — the
hard-asserted gate is ``live_test.py``.

Output discipline (concept §8, same as Phase 3): all human-readable progress
goes to **stderr**; the single machine-readable JSON (the candidate list that
*would* have been saved) goes to **stdout**.

This is a live script: it touches the keyring + IG Demo + the LLM, is
non-deterministic, and is deliberately not collected by ``pytest`` / CI.

Prereqs: IG Demo creds + ``anthropic_api_key`` seeded in the keyring (Phase-1
``scripts/store_credential.py``), and the ``anthropic`` SDK installed.

Usage:
    python scripts/smoke_test.py
    python scripts/smoke_test.py --epic IX.D.DAX.IFMM.IP --volume-proxy EXS1.DE
    python scripts/smoke_test.py --model claude-sonnet-4-6 --verbose
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Make the `research` package + the wiring importable when run as a script.
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent  # phase4_research/
sys.path.insert(0, str(_PACKAGE_ROOT))

from research import ResearchConfig  # noqa: E402

log = logging.getLogger("phase4.smoke_test")


def _eprint(message: str = "") -> None:
    """Human-readable progress → stderr (stdout is reserved for the JSON)."""
    print(message, file=sys.stderr)


class _DryState:
    """A no-op ``StateManager`` stand-in — records, never writes to disk."""

    def __init__(self) -> None:
        self.saved: list[dict[str, Any]] | None = None

    def save_candidates(self, candidates: list[dict[str, Any]]) -> None:
        """Capture the payload instead of persisting it (DRY)."""
        self.saved = candidates


def _build_config(args: argparse.Namespace) -> ResearchConfig:
    """Build a ResearchConfig reflecting the CLI overrides."""
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

    # Import the wiring lazily so --help works without the keyring / SDK.
    from research.context_builder import build_context  # noqa: E402
    from scripts.wiring import build_research  # noqa: E402

    _eprint(f"[smoke] building research (epic={config.epic_allowlist[0]}, "
            f"model={config.model}, volume_proxy={config.volume_proxy})")
    research = build_research(config)

    # Swap in the DRY sink so the run persists nothing.
    dry = _DryState()
    research.state = dry

    # Show the deterministic context the LLM will see. This re-probes the broker
    # (run() builds its own context internally) — fine for a manual smoke run.
    # Connect first so the universe probe has a live session.
    if not research.broker.is_connected():
        conn = research.broker.connect()
        _eprint(f"[smoke] broker connect ok={getattr(conn, 'ok', False)}")
    context = build_context(research.broker, research.db, research.market_data, config)
    _eprint("[smoke] --- deterministic context ---")
    _eprint(f"  bot_score={context.bot_score}  risk_level={context.risk_level}")
    _eprint(f"  tradeable_epics ({len(context.tradeable_epics)}): "
            f"{json.dumps(context.tradeable_epics, indent=2)}")
    _eprint(f"  brain_context: {json.dumps(context.brain_context, indent=2)}")
    _eprint(f"  recent_trades={len(context.recent_trades)}  "
            f"recent_lessons={len(context.recent_lessons)}")

    # Run the real cycle (validator + filter live inside run(); the DRY sink
    # captures the post-gate result without writing it).
    _eprint("[smoke] --- running cycle (real LLM call) ---")
    candidates = research.run()

    if candidates:
        cand = candidates[0]
        _eprint(f"[smoke] RESULT: PASS — 1 candidate "
                f"{cand.direction} {cand.epic} (conf={cand.llm_confidence}, "
                f"floor={cand.threshold_applied})")
        _eprint(f"  reasoning: {cand.reasoning}")
    else:
        _eprint("[smoke] RESULT: ABSTAIN — no candidate (see log above for the "
                "reason: session-health / empty universe / LLM error / validator "
                "REJECT / filter REJECT). Nothing would be saved.")

    # Machine-readable: exactly what would have been persisted.
    would_save = dry.saved if dry.saved is not None else []
    print(json.dumps(would_save, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
