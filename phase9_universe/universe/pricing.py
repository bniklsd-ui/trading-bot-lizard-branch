"""Deterministic ``point_value`` resolver (Phase 9 / V2 Step 2).

Replaces the carried-over v1.5 inference (a single-source read of IG's "(X€)"
naming convention, documented but never independently confirmed — see
``phase4_research/research/models.py``'s ``InstrumentSpec`` docstring) with a
code-proof: no resolvable value, no activation (Decision D6).

Resolution order (first match wins, both pure code, no AI, no I/O):

1. **IG instrument fields** — ``value_of_one_pip`` / ``one_pip_means`` /
   ``contract_size``. **Currently dormant against real data**: as of this step,
   ``phase1_broker_wrapper``'s ``MarketInfo.to_dict()`` only exposes
   ``epic``/``name``/``instrument_type``/``currency``/``expiry``/
   ``min_deal_size``/``lot_size``/``market_status`` — no raw IG pip/contract
   fields are passed through yet. This path is implemented and unit-tested
   against fixtures now so it activates automatically, with no code change
   here, the day a P1 field-passthrough extension adds those keys (tracked as
   an open item, not built in this step — deliberately not "extremely
   necessary" today since path 2 already gives every currently-seeded
   instrument a real proof path). Parsing is strict: ambiguous/unparseable
   values fall through to path 2 rather than guessing.
2. **Name / lot_size cross-check** — regex ``\\((\\d+(?:[.,]\\d+)?)\\s*€\\)`` on
   ``name``, compared against ``lot_size``. Only when **both** are present and
   numerically equal does this count as resolved — this is exactly the
   documented v1.5 single-source inference pattern, now treated as a
   *two-source agreement* instead of a single unverified read.
3. Otherwise ``None`` — no proof, no activation.

``confirm_curated`` reconciles a curated, provisionally-seeded record's
``point_value`` (e.g. the v1.5 STXE/CAC/IBEX inferred values) against what the
resolver can prove today. Its return type is ``bool | None`` (a deliberate,
documented widening of the plan's stated ``bool`` — the plan's own prose
describes three real outcomes: confirmed / contradicted / not yet resolvable,
which a bare ``bool`` cannot represent without conflating "no evidence" with
"contradicted"): ``None`` = the resolver has no proof either way (record stays
as-is), ``True`` = the resolved value matches the curated value (promotion.py,
Step 4, upgrades ``point_value_source``), ``False`` = contradiction (Step 4
quarantines — a curated-but-disproven point_value is more dangerous than a
missing one).
"""

from __future__ import annotations

import re
from typing import Any

from universe.models import UniverseRecord

_NAME_EUR_RE = re.compile(r"\((\d+(?:[.,]\d+)?)\s*€\)")

# A resolved point_value must exactly match the curated value here — both are
# code-derived point values (small whole numbers/decimals in practice, e.g. 1.0,
# 2.0), not sums of floating-point arithmetic, so an exact comparison is safe and
# avoids silently accepting a materially different value through tolerance.
_MATCH_TOLERANCE = 1e-9


def _parse_ig_field_value(raw: Any) -> float | None:
    """Parse a raw IG pip/contract-size field into a float, or ``None`` if ambiguous.

    IG returns these as strings, sometimes with surrounding whitespace or a unit
    suffix. Only a clean, fully-numeric string (after stripping) is accepted —
    anything else (empty, non-numeric, multiple tokens) resolves to ``None`` so
    the caller falls through to the name/lot_size cross-check instead of
    guessing at a value from an ambiguous field.
    """
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    text = str(raw).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def resolve_point_value(market_info: dict[str, Any]) -> tuple[float, str] | None:
    """Deterministically resolve a point_value from IG market data.

    ``None`` means "not provable" — the caller must not activate the
    instrument on an unresolved point_value (Decision D6).
    """
    ig_value = _parse_ig_field_value(market_info.get("value_of_one_pip"))
    if ig_value is None:
        ig_value = _parse_ig_field_value(market_info.get("contract_size"))
    if ig_value is not None and ig_value > 0:
        return (ig_value, "ig_fields")

    name = market_info.get("name")
    lot_size = market_info.get("lot_size")
    if name and lot_size is not None:
        match = _NAME_EUR_RE.search(str(name))
        if match:
            name_value = float(match.group(1).replace(",", "."))
            try:
                lot_size_value = float(lot_size)
            except (TypeError, ValueError):
                return None
            if abs(name_value - lot_size_value) < _MATCH_TOLERANCE:
                return (name_value, "name_lotsize_agree")

    return None


def confirm_curated(record: UniverseRecord, market_info: dict[str, Any]) -> bool | None:
    """Reconcile a curated record's provisional ``point_value`` against proof.

    Returns ``None`` if :func:`resolve_point_value` cannot prove anything for
    this ``market_info`` (record stays exactly as-is — no regression, no false
    confirmation); ``True`` if the resolved value matches ``record.point_value``
    (Step 4 upgrades ``point_value_source``); ``False`` if it contradicts it
    (Step 4 quarantines — a disproven curated value is a live risk, worse than
    an honestly-missing one).
    """
    resolved = resolve_point_value(market_info)
    if resolved is None:
        return None
    resolved_value, _source = resolved
    if record.point_value is None:
        return None
    return abs(resolved_value - record.point_value) < _MATCH_TOLERANCE
