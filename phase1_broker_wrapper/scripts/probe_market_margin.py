#!/usr/bin/env python3
"""Live probe for IG's margin-factor fields on CFD indices (Phase 16 D3.0).

L7 (B3 Margin-Headroom) needs IG's real per-instrument margin requirement to
replace the static leverage cap with a margin-based sizing cap. The candidate
fields are ``instrument.marginFactor``, ``instrument.marginFactorUnit`` and
``instrument.marginDepositBands`` — all **unverified** until now.

This probe hits ``GET /markets/{epic}`` (v3, authenticated) for every epic
passed on the CLI, dumps the relevant fields **raw** (JSON) so we can write the
D3.1 ``MarketInfo`` extension and the D3.2 sizing-cap formula against ground
truth. It does not place orders.

Usage:
    python phase1_broker_wrapper/scripts/probe_market_margin.py \
        --epic IX.D.DAX.IFMM.IP \
        --epic IX.D.IBEX.IFM.IP \
        --epic IX.D.AEX.IFM.IP

Output:
- stdout: machine-readable JSON (a list, one entry per epic, in the order given)
- stderr: human-readable summary + per-epic verdict

Exit codes:
- 0  every epic reachable, ``marginFactor`` + ``marginFactorUnit`` populated, unit == ``PERCENTAGE``
- 1  at least one epic failed (HTTP error, broker rejection, etc.) — inspect stderr
- 2  probe succeeded but a field is missing or has an unexpected unit (D3.1 needs a richer extraction)

**Important:** this is an operator-run probe — it hits the IG demo account and
exercises the demo-side rate-limit / auth cycle exactly like ``smoke_test.py``.
No network in pytest; no automated test for this script (same convention as
``smoke_test.py`` + ``test_lightstreamer.py`` — see ``phase1_broker_wrapper/CLAUDE.md``).

**Reading the verdict:** Plan §6 D3.0 expects ``marginFactor`` numeric and
``marginFactorUnit == "PERCENTAGE"``. Anything else (``POINTS``, ``MARGIN_DEPOSIT_BANDS``
missing, etc.) means D3.1 must extract additional / different fields, and the
finding goes into the Phasenkopf (per Plan §6 D3.0: „Weicht es ab → Feldnamen
im Phasenkopf festhalten, D3.1 entsprechend").
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

# scripts/ -> phase1_broker_wrapper/ (so ``from broker_wrapper import ...`` resolves)
_PHASE1_DIR = Path(__file__).resolve().parent.parent
if str(_PHASE1_DIR) not in sys.path:
    sys.path.insert(0, str(_PHASE1_DIR))

from broker_wrapper import get_broker  # noqa: E402
from broker_wrapper.exceptions import BrokerError  # noqa: E402


# Default epics — the three CFD indices the bot currently knows about, all
# weekend-free under Phase 16 B3 (the weekend SUN* epics are filtered out
# before they reach the universe). Override via ``--epic`` as needed.
DEFAULT_EPICS = (
    "IX.D.DAX.IFMM.IP",
    "IX.D.IBEX.IFM.IP",
    "IX.D.AEX.IFM.IP",
)


# What Plan §6 D3.0 expects from IG. Exposed as constants so the verdict logic
# and the printed expectations stay in one place — easier to extend if D3.1 needs
# more fields later.
EXPECTED_MARGIN_FACTOR_UNIT = "PERCENTAGE"


def _probe_one(broker: Any, epic: str) -> dict[str, Any]:
    """Hit ``GET /markets/{epic}`` (v3, auth) and pull out the margin-related slice.

    Returns a dict ready for JSON-serialisation. Captures BrokerError
    subclasses (e.g. ``EpicNotFoundError``, ``AuthenticationError``,
    ``MarketOfflineError``) and encodes them in the result instead of raising —
    one bad epic must not abort the whole probe (the operator wants to see all
    three answers at once, not stop at the first unknown epic).
    """
    entry: dict[str, Any] = {"epic": epic, "request_ok": False}
    try:
        body = broker._request("GET", f"/markets/{epic}", version="3", auth=True)
    except BrokerError as exc:
        entry["error"] = {
            "code": exc.code,
            "message": str(exc),
            "retryable": getattr(exc, "retryable", None),
        }
        return entry

    entry["request_ok"] = True
    instr = body.get("instrument") or {}
    rules = body.get("dealingRules") or {}
    snapshot = body.get("snapshot") or {}

    entry["instrument_name"] = instr.get("name")
    entry["instrument_type"] = instr.get("type")
    entry["currency"] = instr.get("currencies") or instr.get("currency")

    # The three fields Plan §6 D3.0 calls out as candidates — pulled raw, no
    # normalisation, so the operator sees exactly what IG returned.
    raw_margin_factor = instr.get("marginFactor")
    raw_margin_factor_unit = instr.get("marginFactorUnit")
    raw_margin_deposit_bands = instr.get("marginDepositBands")

    entry["margin_factor_raw"] = raw_margin_factor
    entry["margin_factor_unit_raw"] = raw_margin_factor_unit
    entry["margin_deposit_bands_raw"] = raw_margin_deposit_bands

    # Verdict against the expected shape.
    has_numeric = isinstance(raw_margin_factor, (int, float)) and raw_margin_factor is not None
    unit_ok = raw_margin_factor_unit == EXPECTED_MARGIN_FACTOR_UNIT
    if has_numeric and unit_ok:
        entry["verdict"] = "ok"
    elif raw_margin_factor is None or raw_margin_factor_unit is None:
        entry["verdict"] = "field_missing"
    elif not unit_ok:
        entry["verdict"] = f"unit_unexpected:{raw_margin_factor_unit}"
    else:
        entry["verdict"] = "unknown_shape"

    # Full raw slices for the D3.1 / D3.2 implementation review — operator can
    # inspect any field IG might have that we didn't anticipate.
    entry["instrument_full"] = instr
    entry["dealing_rules_full"] = rules
    entry["snapshot_market_status"] = snapshot.get("marketStatus")
    return entry


def _print_human_line(entry: dict[str, Any]) -> None:
    """One short stderr line per epic — the operator's at-a-glance verdict."""
    epic = entry["epic"]
    if not entry.get("request_ok"):
        err = entry.get("error", {})
        print(
            f"  [ERR] {epic}: {err.get('code', '?')} — {err.get('message', '?')}",
            file=sys.stderr,
        )
        return

    mf = entry["margin_factor_raw"]
    unit = entry["margin_factor_unit_raw"]
    verdict = entry.get("verdict", "?")
    name = entry.get("instrument_name") or "?"
    name_short = (name[:30] + "…") if name and len(name) > 30 else name
    status = entry.get("snapshot_market_status") or "?"
    print(
        f"  [{verdict}] {epic} ({name_short}, {status}): "
        f"marginFactor={mf!r} marginFactorUnit={unit!r}",
        file=sys.stderr,
    )


def _run(broker_name: str, epics: list[str], *, pretty: bool) -> int:
    broker = get_broker(broker_name)
    print(f"Probe: broker={broker_name}, epics={list(epics)}", file=sys.stderr)

    print("[1] connect", file=sys.stderr)
    connect_env = broker.connect()
    if not connect_env.ok:
        print(
            f"  [ERR] connect failed: {connect_env.error}",
            file=sys.stderr,
        )
        return 1

    print("[2] GET /markets/{epic} for each epic", file=sys.stderr)
    results: list[dict[str, Any]] = []
    try:
        for epic in epics:
            entry = _probe_one(broker, epic)
            results.append(entry)
            _print_human_line(entry)
    finally:
        print("[3] disconnect", file=sys.stderr)
        broker.disconnect()

    # Machine-readable output (always JSON, regardless of --pretty).
    json.dump(results, sys.stdout, indent=2, default=str)
    print()  # trailing newline

    # Verdict for the operator's PASS/FAIL signal.
    any_request_failed = any(not r.get("request_ok") for r in results)
    any_field_missing = any(r.get("verdict") == "field_missing" for r in results)
    any_unit_unexpected = any(
        isinstance(r.get("verdict"), str) and r["verdict"].startswith("unit_unexpected:")
        for r in results
    )

    print("", file=sys.stderr)
    if any_request_failed:
        print(
            "RECOMMENDATION: at least one epic failed to fetch — re-run after "
            "credential / network check; the probe cannot confirm the field shape.",
            file=sys.stderr,
        )
        return 1
    if any_field_missing or any_unit_unexpected:
        print(
            f"RECOMMENDATION: D3.1 must extract additional / different fields. "
            f"Expected ``marginFactorUnit == {EXPECTED_MARGIN_FACTOR_UNIT!r}``. "
            f"Note any non-PERCENTAGE unit + the full ``instrument_full`` slice "
            f"for that epic in the Phase-16 Phasenkopf before touching D3.1.",
            file=sys.stderr,
        )
        return 2

    print(
        f"RECOMMENDATION: all {len(results)} epics expose "
        f"``marginFactor`` (numeric) + ``marginFactorUnit == {EXPECTED_MARGIN_FACTOR_UNIT!r}``. "
        f"D3.1 can extend ``MarketInfo`` 1:1; D3.2 can use "
        f"``available_balance * margin_headroom / (price * point_value * margin_factor / 100)``.",
        file=sys.stderr,
    )
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description=(
            "Live probe for IG's margin-factor fields on the demo account "
            "(Phase 16 D3.0, see plan §6)."
        ),
    )
    p.add_argument(
        "--broker", default="ig_demo",
        help="broker key from broker_wrapper.get_broker (default: ig_demo)",
    )
    p.add_argument(
        "--epic", action="append", default=None, metavar="EPIC",
        help="epic to probe (repeatable; default: DAX + IBEX + AEX)",
    )
    p.add_argument(
        "--quiet", action="store_true",
        help="lower the broker_wrapper log level to WARNING (less stdout clutter)",
    )
    args = p.parse_args()

    if args.quiet:
        # The wrapper's logger is verbose at INFO during requests; quiet for the
        # operator's interactive experience. Does NOT silence stderr summary lines.
        logging.getLogger("broker_wrapper").setLevel(logging.WARNING)

    epics = list(args.epic) if args.epic else list(DEFAULT_EPICS)
    return _run(args.broker, epics, pretty=True)


if __name__ == "__main__":
    raise SystemExit(main())
