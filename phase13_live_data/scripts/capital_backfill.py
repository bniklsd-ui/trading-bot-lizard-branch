#!/usr/bin/env python3
"""Phase 13 §6 C1 — Operator script for the Capital.com backfill (Pfad B).

Lückengetriebenes Befüllen des Bar-Archivs mit Capital.com-S3-Bars
für die Epics, die der Probe-Test 2026-08-19 als funktionierend
gemeldet hat (DE40 = Germany 40, FR40 = France 40). Epics ausserhalb
dieser Liste (Spain 35 = IBEX, AEX, MIB) sind Path-C-Territorium
(Dukascopy) und werden vom Script stillschweigend übersprungen —
der Caller kann sie später durch einen Dukascopy-Backfill abdecken.

Usage:
    # Single-day fill for two confirmed epics
    python phase13_live_data/scripts/capital_backfill.py \\
        --epics IX.D.DAX.IFMM.IP,IX.D.CAC.IFE.IP \\
        --start 2026-08-21T08:00:00Z \\
        --end   2026-08-21T16:00:00Z

    # All measurable-universe epics (auto-skip unmapped)
    python phase13_live_data/scripts/capital_backfill.py \\
        --auto \\
        --start 2026-08-21T08:00:00Z \\
        --end   2026-08-21T16:00:00Z

    # Dry-run (no archive writes, no auth)
    python phase13_live_data/scripts/capital_backfill.py \\
        --epics IX.D.DAX.IFMM.IP --auto \\
        --start 2026-08-21T08:00:00Z \\
        --end   2026-08-21T09:00:00Z --dry-run

Output: stderr = menschliche Erzählung, stdout = JSON Envelope
mit per-epic results (analog probe_chart_stream.py / probe_capital.py).

Operator-run, kostenlos (Demo-Konto), aber IG-auth-äquivalent:
Live-Auth mit Demo-Credentials. **Nicht** in Tests (Repo-Konvention).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_KEYRING_SERVICE = "trading-bot-capital"
_DEFAULT_DB_PATH = _REPO_ROOT / "data" / "bars.sqlite"


def _eprint(message: str = "") -> None:
    print(message, file=sys.stderr)


def _read_field(field: str) -> str:
    import keyring
    value = keyring.get_password(_KEYRING_SERVICE, field)
    if not value:
        from broker_wrapper.exceptions import CredentialNotFoundError
        raise CredentialNotFoundError(
            f"Capital.com credential '{_KEYRING_SERVICE}/{field}' not in keyring — "
            f"run `python scripts/store_capital_key.py` first"
        )
    return value


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--epics",
        help="comma-separated IG-style epics to backfill (e.g. "
             "'IX.D.DAX.IFMM.IP,IX.D.CAC.IFE.IP'). Ignored if --auto is set.",
    )
    parser.add_argument(
        "--auto", action="store_true",
        help="auto-discover measurable-universe epics from the data DB",
    )
    parser.add_argument(
        "--start", required=True,
        help="start UTC ISO 8601 (e.g. '2026-08-21T08:00:00Z')",
    )
    parser.add_argument(
        "--end", required=True,
        help="end UTC ISO 8601 (e.g. '2026-08-21T16:00:00Z')",
    )
    parser.add_argument(
        "--db", default=str(_DEFAULT_DB_PATH),
        help=f"path to bars.sqlite (default: {_DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="skip auth + skip writes; just print the plan",
    )
    parser.add_argument(
        "--base", default="https://demo-api-capital.backend-capital.com",
        help="Capital.com base URL (override only for live or alternate demo)",
    )
    return parser.parse_args()


def _resolve_epics(args: argparse.Namespace) -> list[str]:
    """Return the list of epics the script will process."""
    if args.auto:
        sys.path.insert(0, str(_REPO_ROOT))
        from universe import UniverseStore
        store = UniverseStore(args.db)
        try:
            epics = [r.epic for r in store.measurable_universe()]
        finally:
            store.close()
        return epics
    return [s.strip() for s in (args.epics or "").split(",") if s.strip()]


def main(argv: list[str] | None = None) -> int:
    args = _parse_args()

    start = datetime.fromisoformat(args.start.replace("Z", "+00:00"))
    end = datetime.fromisoformat(args.end.replace("Z", "+00:00"))
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    if end <= start:
        _eprint("[capital_backfill] --end must be after --start")
        print(json.dumps({"ok": False, "error": "end_not_after_start"}))
        return 2

    epics = _resolve_epics(args)
    if not epics:
        _eprint("[capital_backfill] no epics resolved (--auto found empty or --epics empty)")
        print(json.dumps({"ok": False, "error": "no_epics"}))
        return 2

    _eprint(f"[capital_backfill] plan: {len(epics)} epics, "
             f"window [{start.isoformat()}, {end.isoformat()})")
    if args.dry_run:
        print(json.dumps({
            "ok": True, "dry_run": True, "epics": epics,
            "start": start.isoformat(), "end": end.isoformat(),
        }, indent=2))
        return 0

    # Read creds → build CapitalSource → load archive → run backfill.
    try:
        identifier = _read_field("identifier")
        password = _read_field("password")
        api_key = _read_field("api_key")
    except Exception as exc:
        _eprint(f"[capital_backfill] keyring read failed: {exc}")
        print(json.dumps({"ok": False, "error": f"keyring_failed: {exc}"}))
        return 3

    sys.path.insert(0, str(_REPO_ROOT))
    from data_foundation.archive import BarArchive
    from live_data.backfill import CapitalSource, run_capital_backfill

    archive = BarArchive(args.db)
    try:
        # Don't open the archive in any schema-mutating way; the new
        # source tag 'capital' is already in KNOWN_SOURCES post-Session-12
        # Step 1 — insert_bars will accept it without ensure_schema.
        source = CapitalSource(
            identifier=identifier,
            custom_password=password,
            api_key=api_key,
            base_url=args.base,
        )
    except Exception as exc:
        _eprint(f"[capital_backfill] setup failed: {exc}")
        print(json.dumps({"ok": False, "error": f"setup_failed: {exc}"}))
        return 1

    try:
        results = run_capital_backfill(source, archive, epics, start, end)
    except Exception as exc:  # noqa: BLE001 — top-level safety net
        _eprint(f"[capital_backfill] backfill raised: {exc}")
        print(json.dumps({"ok": False, "error": f"backfill_raised: {exc}",
                          "partial_results": results}))
        return 1

    written_total = sum(results.values())
    payload = {
        "ok": True,
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "epics_total": len(epics),
        "bars_written_total": written_total,
        "results": results,
        "next_step_hint": (
            "all requested epics covered by Capital.com — run source_delta.py "
            "to see how the new bars compare to yF (Phase 13 P6)"
            if written_total > 0 else
            "no bars written — check keyring, network, or the probe output "
            "for the most recent state of Capital.com auth"
        ),
    }
    print(json.dumps(payload, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
