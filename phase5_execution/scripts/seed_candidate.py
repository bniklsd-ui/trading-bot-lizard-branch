#!/usr/bin/env python3
"""Seed one **manual** research candidate with a fresh 30-minute TTL (operator tool).

Phase 5's order path is exercised live by feeding Gate 2 a candidate that did **not**
come from a real Phase-4 research run. Writing it through
``StateManager.save_candidates([...])`` stamps a fresh ``generated_at`` / ``expires_at``
(TTL 30 min) into the very ``turbo_candidates.json`` that ``gate_load_candidates`` reads.

Why this exists: the seed self-expires after 30 minutes. If it is stale when
``live_test.py`` / ``smoke_test.py`` runs, Gate 2 considers the candidates not fresh and
invokes the real Phase-4 research hook instead — a real, non-deterministic LLM request
that may abstain, so the deterministic order path never runs. Re-seed **immediately
before** the live run (ideally inside the 09:00–17:30 Europe/Berlin trade window) so
``candidates_are_fresh()`` is true and research is skipped.

This is a manual seed, **not** a real pick: the LLM boundary is untouched and the written
``reasoning`` says so. It writes the frozen 10-field Phase-4→5 candidate contract.

Output discipline (project rule, same as Phase 3/4/5): human-readable progress →
**stderr**; the single machine-readable JSON (the saved candidate) → **stdout**.

Usage:
    python scripts/seed_candidate.py
    python scripts/seed_candidate.py --epic IX.D.DAX.IFMM.IP --direction BUY --confidence 70
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# scripts/seed_candidate.py -> scripts/ -> phase5_execution/ -> repo root (same as wiring.py).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_STATE_DIR = _REPO_ROOT / "data" / "state"

# persistence is an editable-installed sibling package (Step C); no sys.path hack needed.
from persistence import StateManager  # noqa: E402

_VALID_DIRECTIONS = ("BUY", "SELL")


def _eprint(message: str = "") -> None:
    """Human-readable progress → stderr (stdout is reserved for the JSON)."""
    print(message, file=sys.stderr)


def _format_iso(dt: datetime) -> str:
    """ISO 8601 UTC with ms precision and Z suffix (mirrors persistence._format_iso)."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def build_candidate(epic: str, direction: str, confidence: float) -> dict:
    """Build the frozen 10-field Phase-4→5 candidate contract for a manual seed."""
    return {
        "epic": epic,
        "direction": direction,
        "llm_confidence": float(confidence),
        "reasoning": (
            "MANUAL SEED (not a real research pick): a single valid DAX-CFD candidate "
            "injected to exercise the Phase-5 order path downstream of Gate 2 "
            "(Gate 3/5 -> Gate 4 sizing -> 4 VETOs -> place order -> monitor). "
            "Self-expires via the 30-min StateManager TTL — re-seed right before a live run."
        ),
        "spread_pct_at_pick": 0.03,
        "drift_at_pick": 0.1,
        "score_at_pick": 50.0,
        "threshold_applied": 55.0,
        "generated_at": _format_iso(datetime.now(timezone.utc)),
        "source": "research",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--epic", default="IX.D.DAX.IFMM.IP", help="instrument epic (default: DAX cash CFD)"
    )
    parser.add_argument(
        "--direction",
        default="BUY",
        choices=_VALID_DIRECTIONS,
        help="trade direction (default: BUY)",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=70.0,
        help="advisory llm_confidence 0-100 (default: 70)",
    )
    args = parser.parse_args(argv)

    candidate = build_candidate(args.epic, args.direction, args.confidence)

    state = StateManager(str(_STATE_DIR))
    state.save_candidates([candidate])  # stamps a fresh generated_at / expires_at (TTL 30 min)

    fresh = state.candidates_are_fresh()
    _eprint(f"[seed] wrote 1 candidate to {_STATE_DIR / 'turbo_candidates.json'}")
    _eprint(f"[seed] {candidate['direction']} {candidate['epic']} (conf {candidate['llm_confidence']})")
    _eprint(f"[seed] candidates_are_fresh() -> {fresh} (30-min TTL; re-seed before each live run)")
    if not fresh:  # defensive: should never happen right after a save
        _eprint("[seed] WARNING: candidate is not fresh immediately after seeding")

    # Machine-readable: echo exactly what was persisted (the candidate dict).
    print(json.dumps(candidate, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
