#!/usr/bin/env python3
"""Phase 15 §6 D3 — Operator-Tool for Pfad A (S4 GapRescue).

Doppel-Sperre (Plan §6 D3, S. 689):
  1. ``RescueConfig.enable_gap_rescue=True`` muss im Aufruf gesetzt sein
     (per Default ``False`` — Schalter wird vom Operator bewusst umgelegt).
  2. ``--apply`` muss zusätzlich übergeben werden (sonst ``--dry-run``-Default).

Erst **beide** Bedingungen zusammen führen zu einem Schreib-Pfad;
eine einzelne Bedingung reicht **nicht** aus — gleiche Disziplin wie
``promote_eligible`` (P10) und ``enable_shadow_schedule`` /
``enable_divergence_sampler``.

Pfad A ist **kein** Scheduler-Feature. ``enable_gap_rescue`` lebt **nur**
in :class:`~live_data.rescue.RescueConfig` (Phase 13) — **kein** Feld in
``SchedulerConfig``, **kein** Wiring in ``phase8_scheduler/`` (Plan §4:
Phase 8 ist NICHT cross-phase-freigegeben für Phase 15). Die
Scheduler-Lock-Pfad-B-Disziplin (L18 / D19 = IG Default AUS, Mini-Session
24) wird durch Pfad A **nicht** aufgehoben — Pfad A macht das Aufheben
erst *möglich*, falls der Operator es bewusst will.

Usage:

    # Default: --dry-run, enable_gap_rescue=False ⇒ nur Plan, kein Schreib-Pfad
    python phase13_live_data/scripts/gap_rescue_operator.py \\
        --start 2026-09-01T08:00:00Z \\
        --end   2026-09-01T16:00:00Z \\
        --auto

    # Bewusst scharf: enable_gap_rescue=True UND --apply
    python phase13_live_data/scripts/gap_rescue_operator.py \\
        --enable-gap-rescue --apply \\
        --start 2026-09-01T08:00:00Z \\
        --end   2026-09-01T16:00:00Z \\
        --auto

    # Nur Plan mit Punkteschätzung
    python phase13_live_data/scripts/gap_rescue_operator.py \\
        --start 2026-09-01T08:00:00Z \\
        --end   2026-09-01T16:00:00Z \\
        --epics IX.D.DAX.IFMM.IP,IX.D.CAC.IFE.IP

Output: stderr = menschliche Erzählung, stdout = JSON Envelope
mit per-epic results (analog ``scripts/capital_backfill.py``).

Kosten-Achtung: Pfad A bucht gegen ``source_spend`` mit
``spend_kind='rescue'``. Der Plan §6 D3 + §9.2 nennt **560
Punkte/Woche** als grobe Schätzung (P13-Findings §8.2, **nicht
nachgerechnet**). Wer scharfschaltet, MUSS vorab mit
``python phase13_live_data/scripts/source_delta.py`` (oder einem
direkten ``source_spend``-SQL-Read) das verbleibende Budget prüfen.

Operator-run, kostenpflichtig (Demo-Konto). **Nicht** in Tests
(Repo-Konvention).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DB_PATH = _REPO_ROOT / "data" / "bars.sqlite"
_DEFAULT_UNIVERSE_DB_PATH = _REPO_ROOT / "data" / "trading_bot.sqlite"


def _eprint(message: str = "") -> None:
    print(message, file=sys.stderr)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--start", required=True,
        help="start UTC ISO 8601 (e.g. '2026-09-01T08:00:00Z')",
    )
    parser.add_argument(
        "--end", required=True,
        help="end UTC ISO 8601 (e.g. '2026-09-01T16:00:00Z')",
    )
    parser.add_argument(
        "--epics",
        help="comma-separated IG-style epics (e.g. "
             "'IX.D.DAX.IFMM.IP,IX.D.CAC.IFE.IP'). Ignored if --auto is set.",
    )
    parser.add_argument(
        "--auto", action="store_true",
        help="auto-discover measurable-universe epics from the data DB",
    )
    parser.add_argument(
        "--db", default=str(_DEFAULT_DB_PATH),
        help=f"path to bars.sqlite (default: {_DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--universe-db", default=str(_DEFAULT_UNIVERSE_DB_PATH),
        help=f"path to trading_bot.sqlite (default: {_DEFAULT_UNIVERSE_DB_PATH})",
    )
    parser.add_argument(
        "--max-points-per-run", type=int, default=560,
        help="Punkte-Deckel pro Lauf (Plan §6 D3 + §9.2: 560/Woche "
             "aus P13-Findings §8.2, nicht nachgerechnet).",
    )
    parser.add_argument(
        "--enable-gap-rescue", action="store_true",
        help="BEIDE Bedingungen für Schreib-Pfad: enable_gap_rescue=True "
             "UND --apply. Dieser Flag setzt die erste Bedingung; --apply "
             "setzt die zweite. Default AUS (Plan §6 D3).",
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Schreib-Pfad aktivieren (zweite Bedingung der Doppel-Sperre). "
             "Ohne --apply bleibt der Lauf --dry-run.",
    )
    parser.add_argument(
        "--broker", default="ig_demo",
        help="Broker-Alias (Default: ig_demo, analog scheduler.run / smoke_test.py)",
    )
    return parser.parse_args(argv)


def _resolve_epics(args: argparse.Namespace) -> list[str]:
    """Return the list of epics the script will process."""
    if args.auto:
        sys.path.insert(0, str(_REPO_ROOT))
        from universe import UniverseStore
        store = UniverseStore(args.universe_db)
        try:
            return [r.epic for r in store.measurable_universe()]
        finally:
            store.close()
    return [s.strip() for s in (args.epics or "").split(",") if s.strip()]


def _build_broker(broker_alias: str):
    """Build the IG broker adapter (Phase-1 contract).

    Credentials read via :func:`broker_wrapper.credentials.get_credential` —
    never from disk, never from env unless ``fallback_env=True`` is set
    internally. Fail-closed if the keyring entry is missing.
    """
    sys.path.insert(0, str(_REPO_ROOT))
    from broker_wrapper.factory import get_broker
    return get_broker(broker_alias)


def _estimate_points(epic_count: int, max_points_per_run: int) -> int:
    """Estimate the IG-Punkte spend for the plan.

    Conservative upper-bound: ``epic_count * GapRescue.max_points_per_call``
    (default 60, Plan §5.6). The script does NOT pre-scan for gaps — that
    would itself cost network + a partial write. The Operator decides
    against this estimate + the actual ``source_spend`` ledger.
    """
    return min(epic_count * 60, max_points_per_run)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    start = datetime.fromisoformat(args.start.replace("Z", "+00:00"))
    end = datetime.fromisoformat(args.end.replace("Z", "+00:00"))
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    if end <= start:
        _eprint("[gap_rescue_operator] --end must be after --start")
        print(json.dumps({"ok": False, "error": "end_not_after_start"}))
        return 2

    epics = _resolve_epics(args)
    if not epics:
        _eprint("[gap_rescue_operator] no epics resolved "
                 "(--auto found empty or --epics empty)")
        print(json.dumps({"ok": False, "error": "no_epics"}))
        return 2

    sys.path.insert(0, str(_REPO_ROOT))
    from live_data.rescue import RescueConfig

    cfg = RescueConfig(
        enable_gap_rescue=args.enable_gap_rescue,
        epics=tuple(epics),
        max_points_per_run=args.max_points_per_run,
    )

    estimated_points = _estimate_points(len(epics), cfg.max_points_per_run)
    write_path_active = cfg.enable_gap_rescue and args.apply

    _eprint(
        f"[gap_rescue_operator] plan: {len(epics)} epics, "
        f"window [{start.isoformat()}, {end.isoformat()}), "
        f"est_points={estimated_points}, "
        f"enable_gap_rescue={cfg.enable_gap_rescue}, "
        f"--apply={args.apply} "
        f"→ {'WRITE' if write_path_active else 'DRY-RUN'}"
    )

    if not write_path_active:
        # Default path: --dry-run. Print the plan + the Doppel-Sperre-Status.
        # No keyring read, no broker connect, no archive writes.
        plan = {
            "ok": True,
            "dry_run": True,
            "config": asdict(cfg),
            "window": {"start": start.isoformat(), "end": end.isoformat()},
            "epics": epics,
            "estimated_points": estimated_points,
            "doppel_sperre": {
                "enable_gap_rescue": cfg.enable_gap_rescue,
                "apply": args.apply,
                "write_path_active": write_path_active,
                "missing": (
                    [] if write_path_active else
                    [c for c, v in [
                        ("enable_gap_rescue=True", cfg.enable_gap_rescue),
                        ("--apply", args.apply),
                    ] if not v]
                ),
            },
            "next_step_hint": (
                "pass BOTH --enable-gap-rescue AND --apply to activate the write path"
                if not write_path_active else
                "write path active — bars will be written to source='ig'"
            ),
        }
        print(json.dumps(plan, indent=2, default=str))
        return 0

    # Write path active: both conditions met. Real cost will be booked
    # against ``source_spend`` with ``spend_kind='rescue'``. Read budget
    # + build broker + build GapRescue + run per-epic.
    sys.path.insert(0, str(_REPO_ROOT))
    from data_foundation.archive import BarArchive
    from data_foundation.budget import IG_QUOTA_V1, SourceBudget
    from live_data.rescue import GapRescue

    budget = SourceBudget(args.db, IG_QUOTA_V1)
    archive = BarArchive(args.db)
    try:
        archive.ensure_schema()
        broker = _build_broker(args.broker)
        rec = GapRescue(broker, budget, archive,
                        max_points_per_call=cfg.max_points_per_run // max(len(epics), 1))
    except Exception as exc:  # noqa: BLE001 — top-level safety net
        _eprint(f"[gap_rescue_operator] setup failed: {exc}")
        archive.close()
        budget.close()
        print(json.dumps({"ok": False, "error": f"setup_failed: {exc}"}))
        return 1

    from live_data.rescue import RescueReport  # local alias for type clarity

    results: dict[str, dict] = {}
    for epic in epics:
        try:
            report: RescueReport = rec.rescue_epic(epic, start.isoformat(), end.isoformat())
        except Exception as exc:  # noqa: BLE001 — per-epic fail-soft
            results[epic] = {"error": f"rescue_raised: {exc}"}
            continue
        results[epic] = {
            "gaps_found": report.gaps_found,
            "bars_written": report.bars_written,
            "points_spent": report.points_spent,
            "skipped_reason": report.skipped_reason,
        }

    written_total = sum(r.get("bars_written", 0) for r in results.values()
                        if isinstance(r, dict))
    spent_total = sum(r.get("points_spent", 0) for r in results.values()
                      if isinstance(r, dict))
    payload = {
        "ok": True,
        "dry_run": False,
        "config": asdict(cfg),
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "epics_total": len(epics),
        "bars_written_total": written_total,
        "points_spent_total": spent_total,
        "results": results,
        "next_step_hint": (
            "check `source_spend` ledger for kind='rescue' rows to verify the "
            "booked cost; run source_delta.py if any epic returned bars_written > 0"
        ),
    }
    print(json.dumps(payload, indent=2, default=str))
    archive.close()
    budget.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
