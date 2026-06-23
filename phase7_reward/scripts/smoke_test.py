#!/usr/bin/env python3
"""Dry sanity for the Phase-7 lesson extraction — one real Haiku ``reflect()``.

Runs the **only** AI in the phase exactly once against a hand-built, plausible closed
trade and prints the extracted lesson. **No DB write, no executor, no broker** — it
exercises ``Brain.reflect`` in isolation (the analogue of the Phase-6 ``smoke_test``'s
single dry debate), so the operator can eyeball the prompt→lesson behaviour and the
token cost before running the full ``live_test`` cycle.

Live script: it touches the keyring (the Anthropic key) and makes one real Anthropic
request, so it is **not** collected by ``pytest`` / CI. **The operator runs it.**
Prereqs: ``anthropic_api_key`` in the keyring; ``bash scripts/dev_install.sh``.

Output discipline: progress + the lesson + the token usage → **stderr**; the single
machine-readable :class:`~reward.models.LessonResult` JSON → **stdout**. Exits ``0``
when a lesson was extracted (``ok``), ``1`` otherwise — a clear go/no-go before live.

Usage:
    python scripts/smoke_test.py
    python scripts/smoke_test.py --status TIME_STOP --r-multiple -1.0 --verbose
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Make the project dir importable so the (non-installed) `scripts` package resolves.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent  # phase7_reward/
sys.path.insert(0, str(_PROJECT_ROOT))

from reward.models import ClosedTrade, RewardResult  # noqa: E402

log = logging.getLogger("phase7.smoke_test")


def _eprint(message: str = "") -> None:
    print(message, file=sys.stderr)


def _win_loss(r_multiple: float) -> str:
    """Sign → label (the scorer's convention)."""
    if r_multiple > 0:
        return "WIN"
    if r_multiple < 0:
        return "LOSS"
    return "BREAKEVEN"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epic", default="IX.D.DAX.IFMM.IP", help="epic for the context")
    parser.add_argument("--direction", default="BUY", choices=["BUY", "SELL"])
    parser.add_argument(
        "--status", default="CLOSED_BY_BROKER",
        choices=["CLOSED_BY_BROKER", "TIME_STOP"],
        help="exit status (planned SL/TP vs drift)",
    )
    parser.add_argument("--r-multiple", type=float, default=1.4, help="realised R-multiple")
    parser.add_argument("--spread", type=float, default=0.04, help="entry spread %% for context")
    parser.add_argument("--verbose", action="store_true", help="DEBUG logging")
    args = parser.parse_args(argv)

    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    from scripts.wiring import build_brain

    # A plausible closed trade + scored outcome (no scoring math is exercised here —
    # the values are illustrative inputs to the lesson prompt).
    now_iso = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    win_loss = _win_loss(args.r_multiple)
    closed = ClosedTrade(
        deal_reference="SMOKE-001",
        deal_id="SMOKE-001",
        status=args.status,
        closed_at=now_iso,
    )
    outcome = RewardResult(
        outcome_delta=0.0,
        process_delta=0.0,
        score_before=50.0,
        score_after=50.0,
        win_loss=win_loss,
        r_multiple=args.r_multiple,
    )
    # The same market_context shape the recorder builds at close.
    market_context = {
        "epic": args.epic,
        "direction": args.direction,
        "status": args.status,
        "spread_at_entry_pct": args.spread,
        "r_multiple": args.r_multiple,
        "win_loss": win_loss,
        "session_date": now_iso[:10],
    }

    _eprint(f"[smoke] building Brain (lesson model) and reflecting on a {win_loss} "
            f"{args.direction} trade (R={args.r_multiple}, exit={args.status}) …")
    brain = build_brain()
    lesson = brain.reflect(closed, outcome, market_context)

    if lesson.ok:
        _eprint(f"[smoke] lesson: {lesson.lesson_text}")
    else:
        _eprint(f"[smoke] no lesson extracted (best-effort failed): {lesson.error}")
    usage = getattr(brain._llm, "last_usage", None)  # observability only
    _eprint(f"[smoke] token usage: {usage}")

    # Machine-readable: the LessonResult.
    print(json.dumps(dataclasses.asdict(lesson), indent=2, default=str))

    _eprint(f"\nRESULT: {'ok' if lesson.ok else 'FAILED'}")
    return 0 if lesson.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
