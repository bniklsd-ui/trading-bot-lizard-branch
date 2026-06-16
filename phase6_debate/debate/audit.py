"""Phase-6 debate audit — append-only JSON log (Decision I).

The SQLite DB stays **read-only until Phase 7**, so the only persistence the
debate gets is a gitignored JSON audit at ``data/state/debate_log.json``. This
module owns that file: :func:`write_debate` turns a finished
:class:`~debate.models.DebateOutcome` plus its read-only
:class:`~debate.models.DebateContext` into one forward-compatible record and
appends it atomically.

**Forward-compatible schema (concept §7).** The record is shaped so a future
Phase-9 ingest can populate the planned tables **without reshaping**:

    record key        → Phase-9 destination
    ----------------- ---------------------------------------------------------
    ts                → row timestamp
    epic              → market_regime_snapshots.epic / decision_context.epic
    seed_direction    → decision_context (the Phase-4 proposal)
    final_decision    → decision_context.decision  (TRADE | ABSTAIN)
    final_direction   → decision_context.direction (BUY | SELL | null)
    confidence        → decision_context.confidence (ADVISORY — gates nothing,
                        Phase-7 outcome-anchoring input only; Decision H)
    rounds_used       → decision_context.rounds_used
    rationale         → decision_context.rationale
    regime_snapshot   → market_regime_snapshots (spread_pct, market_status,
                        drift_at_pick, score_at_pick, recent_bars_summary)
    transcript        → decision_context (the full Bull/Bear/Judge sequence)
    token_summary     → cost/usage aggregate (input/output/cache_* + est cost)

**Isolation.** Imports only ``debate.models`` / ``debate.timeutil`` + stdlib —
no ``anthropic`` / ``broker_wrapper`` / ``research``. Logging → stderr; stdout is
reserved for machine-readable JSON. The write is best-effort: an I/O error is
logged and swallowed (the audit must never break a debate result — and the
orchestrator's injected ``audit`` callable swallows on top of this).
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from typing import Any

from debate import timeutil
from debate.models import DebateContext, DebateOutcome

log = logging.getLogger(__name__)


def _load_log(path: str) -> list[dict[str, Any]]:
    """Load the existing audit array, tolerating absence / corruption.

    Mirrors ``research.token_meter._load_log``: a missing file → empty list
    (first write); a corrupt / non-list file is logged and treated as empty
    rather than raising — the advisory audit is not worth aborting over.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("debate audit: could not read %s (%s) — starting fresh", path, exc)
        return []
    if not isinstance(data, list):
        log.warning("debate audit: %s is not a JSON array — starting fresh", path)
        return []
    return data


def _build_record(outcome: DebateOutcome, ctx: DebateContext) -> dict[str, Any]:
    """Assemble the forward-compatible audit record (schema mapping in the module docstring)."""
    return {
        "ts": timeutil.utc_iso_now(),
        "epic": ctx.epic,
        "seed_direction": ctx.seed_direction,
        "final_decision": outcome.decision,
        "final_direction": outcome.direction,
        "confidence": outcome.confidence,  # advisory only — gates nothing (Decision H)
        "rounds_used": outcome.rounds_used,
        "rationale": outcome.rationale,
        # → Phase-9 market_regime_snapshots
        "regime_snapshot": {
            "spread_pct": ctx.spread_pct,
            "market_status": ctx.market_status,
            "drift_at_pick": ctx.drift_at_pick,
            "score_at_pick": ctx.score_at_pick,
            "recent_bars_summary": ctx.recent_bars_summary,
        },
        # → Phase-9 decision_context (the full Bull/Bear/Judge sequence);
        # to_dict() already normalises the transcript tuple to a list of dicts.
        "transcript": outcome.to_dict()["transcript"],
        "token_summary": dict(outcome.token_summary),
    }


def write_debate(
    outcome: DebateOutcome, ctx: DebateContext, path: str | None
) -> dict[str, Any]:
    """Build a debate audit record and append it atomically to ``path``.

    Args:
        outcome: The orchestrator's verdict (Module 6).
        ctx: The read-only context the debate argued over (Module 2) — the source
            of the ``regime_snapshot`` fields.
        path: Destination JSON file (``data/state/debate_log.json`` in wiring).
            ``None`` → **do not write**, just return the record (the dry / unit-test
            path, exactly like ``token_meter.record``).

    Returns:
        The record dict (JSON-serialisable). Writing is best-effort: an I/O error
        is logged to stderr and swallowed — the audit must never break a result.
    """
    rec = _build_record(outcome, ctx)
    if path is None:
        return rec

    try:
        records = _load_log(path)
        records.append(rec)
        directory = os.path.dirname(path) or "."
        os.makedirs(directory, exist_ok=True)
        # Atomic replace: write a sibling temp file, fsync-free dump, then os.replace.
        fd, tmp = tempfile.mkstemp(dir=directory, prefix=".debate_log.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(records, fh, indent=2)
                fh.write("\n")
            os.replace(tmp, path)
        except OSError:
            # Clean up the temp file on a failed replace, then re-raise to the outer handler.
            if os.path.exists(tmp):
                os.remove(tmp)
            raise
    except OSError as exc:
        log.warning("debate audit: could not append record to %s (%s)", path, exc)
    return rec
