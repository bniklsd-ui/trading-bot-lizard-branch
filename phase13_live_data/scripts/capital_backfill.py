#!/usr/bin/env python3
"""Phase 13 §6 C1 — Operator script for the Capital.com backfill (Pfad B).

Lückengetriebenes Befüllen des Bar-Archivs mit Capital.com-S3-Bars
für die Epics, für die ``SourceAvailabilityStore.symbol_for(epic,
"capital")`` einen Wert liefert. Epics ohne Eintrag in
``instrument_source_availability`` werden stillschweigend übersprungen
(``fetch_window`` gibt ``[]`` zurück, kein HTTP).

Phase-14 B2 (2026-08-22): das frühere hartkodierte Epic→Kürzel-Mapping
in ``live_data/backfill.py`` ist weg — das Script baut den Lookup hier
aus ``SourceAvailabilityStore`` (Migration 007). Discover hat vorher
die Zeilen geschrieben; ohne sie liefert der Lookup ``None`` für alle
Epics und der Lauf ist ein No-Op. Das ist Absicht: ein Discovery, das
noch nie gelaufen ist, darf nicht aus Versehen Daten holen.

Usage:
    # Single-day fill for epics the lookup resolves
    python phase13_live_data/scripts/capital_backfill.py \\
        --epics IX.D.DAX.IFMM.IP,IX.D.CAC.IFE.IP \\
        --start 2026-08-21T08:00:00Z \\
        --end   2026-08-21T16:00:00Z

    # All measurable-universe epics (auto-skip what the lookup rejects)
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
_DEFAULT_UNIVERSE_DB_PATH = _REPO_ROOT / "data" / "trading_bot.sqlite"


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
        "--universe-db", default=str(_DEFAULT_UNIVERSE_DB_PATH),
        help=f"path to trading_bot.sqlite holding instrument_universe "
             f"(default: {_DEFAULT_UNIVERSE_DB_PATH}). Used by --auto only.",
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
        store = UniverseStore(args.universe_db)
        try:
            epics = [r.epic for r in store.measurable_universe()]
        finally:
            store.close()
        return epics
    return [s.strip() for s in (args.epics or "").split(",") if s.strip()]


def _build_symbol_lookup(universe_db_path: str):
    """Build the IG-Epic → Capital-Kürzel lookup from
    ``instrument_source_availability`` (Phase-14 B2).

    Returns ``(lookup, store)``: the lookup is a closure that calls
    ``SourceAvailabilityStore.symbol_for(epic, "capital")`` for each
    epic; ``store`` is the underlying connection the caller MUST close.

    Fail-soft on missing migration 007: an older ``trading_bot.sqlite``
    without the Phase-14 table returns a lookup that always returns
    ``None`` — the backfill then becomes a no-op for every epic (the
    same safe-by-default behaviour as a ``CapitalSource`` constructed
    without a lookup). The store is still returned so the caller can
    close it.
    """
    from source_registry.store import SourceAvailabilityStore

    store = SourceAvailabilityStore(universe_db_path)
    try:
        # Probe the table — if it doesn't exist (Phase-14 migration not
        # applied yet), every ``symbol_for`` call raises ``OperationalError``.
        # We catch it here and hand back a null-lookup so the script
        # can still run, just with zero resolved epics.
        store.for_epic("__probe__")  # cheap existence check
        avail = True
    except Exception:  # noqa: BLE001 — fail-soft per Phase-14 B2 spec
        avail = False

    if not avail:
        def _null_lookup(_epic: str) -> str | None:
            return None
        return _null_lookup, store

    def _lookup(epic: str) -> str | None:
        try:
            return store.symbol_for(epic, "capital", "1m")
        except Exception:  # noqa: BLE001 — per-row fail-soft
            return None

    return _lookup, store


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

    # Phase-14 B2: build the symbol lookup from the discovery table.
    # Done BEFORE BarArchive so a missing migration 007 surfaces as a
    # no-op backfill (every epic → None → []) rather than as a bar-archive
    # error. The store is closed at the very end (after the backfill).
    symbol_lookup, avail_store = _build_symbol_lookup(args.universe_db)
    # Phase-14 B2 spec: warn loud when no availability rows exist, so the
    # operator notices the discovery daemon has never run on this DB.
    if symbol_lookup("IX.D.DAX.IFMM.IP") is None:
        _eprint(
            "[capital_backfill] WARNING: no 'capital' rows in "
            "instrument_source_availability — backfill will be a no-op "
            "until the Discovery daemon (Phase-14 C) writes availability rows"
        )

    archive = BarArchive(args.db)
    try:
        # ensure_schema() is idempotent (Phase-12 D4): adds columns
        # that are missing on older DBs (NOTABLY the ``tick_count``
        # column added by Phase-13 A2 — see commit e8c5b94), leaves
        # existing columns alone. Critical for live-DB backfills where
        # the bars.sqlite may pre-date Phase 13: without this call,
        # ``insert_bars`` raises ``OperationalError: table bars has no
        # column named tick_count`` (Nikinger-Run 2026-08-19, Session
        # 13). Without it, every Capital.com bar would silently fail
        # to write and the operator gets the misleading "0 bars
        # written" hint.
        archive.ensure_schema()
        # KNOWN_SOURCES has been extended with 'capital' (Session-12
        # Step 1); insert_bars now accepts the new tag.
        source = CapitalSource(
            identifier=identifier,
            custom_password=password,
            api_key=api_key,
            base_url=args.base,
        )
    except Exception as exc:
        _eprint(f"[capital_backfill] setup failed: {exc}")
        avail_store.close()
        print(json.dumps({"ok": False, "error": f"setup_failed: {exc}"}))
        return 1

    # Pre-bind results so the top-level safety net can emit a valid envelope
    # even when ``run_capital_backfill`` raises before assigning it (Phase-14
    # finding B4: NameError swallowed the original exception; now partial_results
    # is always present, default empty).
    results: dict[str, int] = {}
    try:
        results = run_capital_backfill(
            source, archive, epics, start, end,
            symbol_lookup=symbol_lookup,
        )
    except Exception as exc:  # noqa: BLE001 — top-level safety net
        _eprint(f"[capital_backfill] backfill raised: {exc}")
        avail_store.close()
        print(json.dumps({"ok": False, "error": f"backfill_raised: {exc}",
                          "partial_results": results}))
        return 1
    finally:
        try:
            avail_store.close()
        except Exception:  # noqa: BLE001 — close is best-effort
            pass

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
