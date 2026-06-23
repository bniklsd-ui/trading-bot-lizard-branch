#!/usr/bin/env python3
"""Operator tool — write synthetic reward data into a **separate** synthetic DB.

Generates reproducible, clearly-labelled synthetic trades (``account='synthetic'``)
and writes them — as CLOSED ``trade_outcomes`` + scored ``reward_pts`` rows — into a
**dedicated** SQLite file, so the confidence/scorer math can be exercised on
bootstrap data without ever polluting the live store (Decision H).

**The hard safety boundary.** Before opening *any* database, this calls
:func:`reward.guard_synthetic_path`, which **raises** if the target resolves to
``RewardConfig.live_db_path`` (``data/trading_bot.sqlite``). The guard is the *first*
executable step — synthetic data can never land in the live DB, and the tool never
auto-targets it. The ``account='synthetic'`` tag is defense-in-depth on top of the
path split.

After writing, it prints the confidence the synthetic distribution yields
(``compute_confidence``) so the operator can see the bootstrap edge — observe-only,
gating nothing (Decision C).

Live-ish script: it writes a SQLite file, so it is **not** collected by ``pytest`` /
CI. The separation's testable core (``guard_synthetic_path`` / ``select_edge_set`` /
``compute_confidence``) is unit-covered in ``tests/test_synthetic.py`` /
``test_confidence.py``. **The operator runs this.**

Output discipline: progress + the guard confirmation + the confidence report →
**stderr**; the single machine-readable summary JSON → **stdout**. Exits ``0`` on a
successful write, ``2`` if the guard refused the target.

Usage:
    python scripts/backfill_synthetic.py --n 40 --win-rate 0.55 --seed 7
    python scripts/backfill_synthetic.py --db-path data/synthetic_reward.db
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("phase7.backfill_synthetic")


def _eprint(message: str = "") -> None:
    print(message, file=sys.stderr)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=30, help="number of synthetic trades")
    parser.add_argument("--win-rate", type=float, default=0.55, help="winner probability [0,1]")
    parser.add_argument("--seed", type=int, default=None, help="RNG seed (reproducible)")
    parser.add_argument("--win-r", type=float, default=1.5, help="nominal R of a winner")
    parser.add_argument("--loss-r", type=float, default=-1.0, help="nominal R of a loser")
    parser.add_argument("--jitter", type=float, default=0.0, help="symmetric R noise")
    parser.add_argument(
        "--db-path", default=None,
        help="target SQLite file (default: RewardConfig.synthetic_db_path)",
    )
    parser.add_argument("--verbose", action="store_true", help="DEBUG logging")
    args = parser.parse_args(argv)

    logging.basicConfig(
        stream=sys.stderr,
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    from reward import (
        RewardConfig,
        Scorer,
        SyntheticTradeGenerator,
        compute_confidence,
        guard_synthetic_path,
    )
    from reward.models import SyntheticSafetyError

    cfg = RewardConfig()
    target = args.db_path if args.db_path is not None else cfg.synthetic_db_path

    # --- THE HARD SAFETY BOUNDARY — before opening any database (Decision H). ---
    try:
        resolved = guard_synthetic_path(target, cfg)
    except SyntheticSafetyError as exc:
        _eprint(f"[backfill] REFUSED: {exc}")
        return 2
    _eprint(f"[backfill] guard ok — writing synthetic data to {resolved} "
            f"(live DB {Path(cfg.live_db_path).resolve()} is protected)")

    # --- generate reproducible, clearly-labelled synthetic trades. ---
    gen = SyntheticTradeGenerator(args.seed)
    trades = gen.generate(
        args.n,
        win_rate=args.win_rate,
        win_r=args.win_r,
        loss_r=args.loss_r,
        jitter=args.jitter,
    )

    # --- write them into the synthetic DB via the Phase-2 CRUD. ---
    from persistence import Database

    db = Database(resolved)
    try:
        db.run_migrations()  # schema + migration 002 columns in the synthetic file
        scorer = Scorer(cfg)
        now = _now_iso()
        session_date = now[:10]
        for i, t in enumerate(trades):
            initial_risk = 1.0
            profit_loss = t.r_multiple * initial_risk * cfg.point_value
            open_level = 18000.0
            trade_id = db.insert_trade({
                "deal_id": f"SYNTH-{i:04d}",
                "epic": "SYNTHETIC",
                "direction": "BUY",  # placeholder; account='synthetic' is the real tag
                "size": 1.0,
                "open_level": open_level,
                "close_level": open_level + profit_loss,
                "currency": "EUR",
                "open_ts": now,
                "close_ts": now,
                "profit_loss": profit_loss,
                "status": "CLOSED",
                "session_date": session_date,
                "account": "synthetic",       # migration 002
                "initial_risk": initial_risk,  # migration 002
            })
            reward = scorer.score(
                r_multiple=t.r_multiple,
                status="CLOSED_BY_BROKER",
                spread_at_entry_pct=cfg.tight_spread_pct,
                debate_confidence=None,
                score_before=db.get_current_score(),
            )
            db.insert_reward(trade_id, {
                "outcome_score_delta": reward.outcome_delta,
                "process_score_delta": reward.process_delta,
                "score_after": reward.score_after,
                "win_loss": reward.win_loss,
                "pnl_raw": profit_loss,
                "r_multiple": reward.r_multiple,  # migration 002
                "spread_at_entry_pct": cfg.tight_spread_pct,
            })
        score_after = db.get_current_score()
    finally:
        db.close()

    # --- the bootstrap confidence the synthetic distribution yields (observe-only). ---
    r_multiples, wins, n = SyntheticTradeGenerator.edge_inputs(trades)
    report = compute_confidence(r_multiples, wins, n, cfg)
    _eprint(f"[backfill] wrote {n} synthetic trades + rewards. "
            f"confidence={report.state} "
            f"(win_rate_wilson_lb={report.win_rate_wilson_lb}, "
            f"expectancy_r={report.expectancy_r}, sqn={report.sqn}, "
            f"value={report.confidence_value}); final score={score_after}")

    summary = {
        "db_path": resolved,
        "n": n,
        "win_rate_requested": args.win_rate,
        "wins": wins,
        "score_after": score_after,
        "confidence": {
            "state": report.state,
            "n": report.n,
            "win_rate_raw": report.win_rate_raw,
            "win_rate_wilson_lb": report.win_rate_wilson_lb,
            "expectancy_r": report.expectancy_r,
            "sqn": report.sqn,
            "confidence_value": report.confidence_value,
        },
    }
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
