"""Phase 16 D2.2 — Instinct → predicate compiler.

Turns a persisted ``Instinct`` row (status='promoted') into a runtime predicate
that VETO 5 (Phase 5, ``execution/vetos.py:longterm_pre_trade_check``) consumes.

**Grammar (deterministic, code-prüfbar):**

    ``^\\s*avoid\\s+(BUY|SELL)(?:\\s+on\\s+([A-Z0-9.]+))?\\s*$``

Two shapes:

- ``"avoid BUY"`` — broad veto on every BUY candidate.
- ``"avoid BUY on IX.D.DAX.IFMM.IP"`` — narrow veto on one Epic's BUY direction.

Anything outside this grammar ⇒ ``None`` + WARNING (``"no consumer for domain X"``
or ``"trigger does not match the grammar"``). Fail-closed by VETO 5 design —
the absence of a predicate means ``longterm_pre_trade_check`` returns ``None``
(no veto).

**Domain filter (Plan §1 P9):** only ``domain == "entry"`` is consumed today. Other
domains (``exit`` / ``sizing`` / ``timing``) are **defined in the schema** (Phase 15
C1) but no consumer yet — the WARNING here is the design-honest "no consumer for
domain X", never a silent pass. If a future phase adds an exit-side consumer,
this filter lifts (one-liner).

Why a Mini-Grammatik and not full Free-Text? **Hard Rule 3** (root ``CLAUDE.md``):
AI output may never trigger an order without code-side validation. The Mini-
Grammatik makes the AI→VETO transition **deterministically compile-checked**: the
LLM produces a structured trigger, the regex either matches (compiled predicate)
or doesn't (no predicate, no veto — not silent acceptance, explicit WARNING).
Phase 13 Opus-Review §13 #8 acknowledged that ``n_closed`` ≪ ``instinct_n_min``
makes the test reachability low (Plan §6 D2.2 "Bridge lebt, ist aber unter der
Schwelle"). The code is here, the test path is here, VETO 5 stays fail-closed.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Callable, Iterable, TYPE_CHECKING

from instinct.models import DOMAINS, Instinct


if TYPE_CHECKING:  # pragma: no cover - typing-only import
    pass


logger = logging.getLogger(__name__)


# Mini-Grammatik (Plan §1 P9): ``avoid BUY|SELL[ on EPIC]``.
# Case-insensitive, EPIC = uppercase letters + digits + dots.
TRIGGER_RE = re.compile(
    r"^\s*avoid\s+(BUY|SELL)(?:\s+on\s+([A-Z0-9.]+))?\s*$",
    re.IGNORECASE,
)

# Consumer-domain filter (Phase 16 D2.2 / Plan §1 P9). Only ``entry`` is consumed
# today (VETO 5 runs before trade open). Other domains are schema-defined
# (Phase 15 C1, Migration 009) but have no consumer yet — explicit WARNING.
_CONSUMER_DOMAINS: frozenset[str] = frozenset({"entry"})


def instinct_from_row(row: dict[str, Any]) -> Instinct:
    """Convert a persisted ``instincts`` row (dict) into a typed ``Instinct``.

    Mirrors :class:`instinct.models.Instinct`'s constructor — JSON-serialized
    ``evidence_trade_ids_json`` / ``contradictions_trade_ids_json`` are parsed
    back into tuples, defaults for the optional timestamp fields match the
    schema's NULL semantics. ``id`` is taken from the row if present.

    Used by :func:`compile_rules` (one row each) and by the test suite to seed
    fixtures without going through ``Database.insert_instinct``.
    """
    evidence_raw = row.get("evidence_trade_ids_json") or "[]"
    contradictions_raw = row.get("contradictions_trade_ids_json") or "[]"
    import json
    evidence = tuple(json.loads(evidence_raw) if isinstance(evidence_raw, str) else evidence_raw)
    contradictions = tuple(
        json.loads(contradictions_raw) if isinstance(contradictions_raw, str) else contradictions_raw
    )
    return Instinct(
        trigger=str(row.get("trigger") or ""),
        domain=str(row.get("domain") or "entry"),
        confidence=(None if row.get("confidence") is None else float(row["confidence"])),
        evidence_trade_ids=evidence,
        contradictions_trade_ids=contradictions,
        status=str(row.get("status") or "proposed"),
        created_utc=str(row.get("created_utc") or ""),
        validated_utc=row.get("validated_utc"),
        promoted_utc=row.get("promoted_utc"),
        archived_utc=row.get("archived_utc"),
        id=row.get("id"),
    )


def compile_rule(instinct: Instinct) -> Callable[[dict], bool] | None:
    """Compile one ``Instinct`` into a VETO-5 predicate, or ``None`` (logged WARNING).

    Returns a callable ``(candidate: dict) -> bool`` that returns ``True`` when
    the candidate **violates** the instinct (VETO 5 invokes the predicate and
    vetoes when it returns ``True``, per ``execution/vetos.py``). ``None`` means
    "no predicate compiled" — VETO 5 treats it as no-op, never as silent pass.

    The candidate dict shape (per ``execution.models.Candidate``) is exactly what
    Phase 5 VETO 5 already reads: ``.direction`` (string) + ``.epic`` (string).
    The compiler only inspects two keys; it ignores everything else.
    """
    if instinct.domain not in _CONSUMER_DOMAINS:
        logger.warning(
            "instinct.compile: no consumer for domain %r (instinct id=%s); "
            "schema-defined but unconsumed — define a downstream consumer before promoting.",
            instinct.domain, instinct.id,
        )
        return None
    if instinct.status != "promoted":
        # Caller-side discipline: ``compile_rules`` filters ``status='promoted'``
        # in SQL, but a defensive check here costs nothing.
        logger.warning(
            "instinct.compile: refusing non-promoted instinct id=%s status=%r",
            instinct.id, instinct.status,
        )
        return None

    match = TRIGGER_RE.match(instinct.trigger)
    if not match:
        logger.warning(
            "instinct.compile: trigger does not match the grammar: %r "
            "(instinct id=%s); expected 'avoid BUY|SELL[ on EPIC]'",
            instinct.trigger, instinct.id,
        )
        return None

    direction = match.group(1).upper()
    epic = match.group(2)  # may be None

    def predicate(candidate: dict[str, Any]) -> bool:
        """``True`` ⇔ the candidate matches the instinct's avoid-direction.

        A predicate matches when ``candidate["direction"]`` equals the avoid-
        direction **and** either no Epic was specified (broad veto) or the
        candidate's Epic equals the avoided Epic (narrow veto).
        """
        cand_direction = candidate.get("direction")
        if cand_direction is None:
            return False  # fail-open: a malformed candidate doesn't trigger VETO 5
        if cand_direction != direction:
            return False
        if epic is None:
            return True
        return candidate.get("epic") == epic

    return predicate


def compile_rules(rows: Iterable[dict[str, Any]]) -> tuple[Callable[[dict], bool], ...]:
    """Compile a sequence of persisted instinct rows into a tuple of predicates.

    Rows with ``status != 'promoted'`` or unmatchable triggers are skipped
    (with WARNING). The tuple preserves no order — VETO 5 short-circuits on
    the first ``True``, so order doesn't matter for correctness.

    Returns an empty tuple when no rows are compiled (e.g. today, before any
    promotion has fired — AK9-Erbe: ``longterm_rules == ()`` → no veto
    behaviour change, ``test_pre_trade_check_veto5_empty_rules_is_identity``
    stays green).
    """
    predicates: list[Callable[[dict], bool]] = []
    for row in rows:
        instinct = instinct_from_row(row)
        pred = compile_rule(instinct)
        if pred is not None:
            predicates.append(pred)
    return tuple(predicates)
