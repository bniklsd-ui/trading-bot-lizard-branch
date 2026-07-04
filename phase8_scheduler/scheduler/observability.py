"""Module — per-cycle diagnostic health log (v1.6 Phase-8 hotfix, Step 0).

The prior state of the world: the only signal about *why* a cycle did or did not trade was
raw stderr WARNING noise from the Phase-3 fetcher and the Phase-4 orchestrator — nothing
persisted, nothing per-cycle, nothing an operator could inspect after the fact. The
``^FCHI``/``^IBEX`` yfinance blocker (v1.6 diagnosis) exposed this directly: without a
structured log there was no way to tell "teil-degradiert vs. komplett unavailable" from the
live run alone, and the Nikinger explicitly asked for this to double as a safety net for a
future recurrence ("sophisticated logging, in order to later find the correct issues if they
occur again" — v1.6 Step 3 Tolerate decision).

This module is the write side of that log: one append-only JSON-Lines file,
``data/state/research_health.jsonl`` (gitignored, alongside the other P8 state files), one
record per WINDOW cycle regardless of pick/abstain/cap-block. Every field mirrors data
Phase 4 already computes (``Research.last_context_health`` / ``last_abort_detail``, both
v1.6-Step-0 additions there) and Phase 8's own :class:`~scheduler.research_tick.ResearchResult`
— this module does no additional Phase-3/Phase-4 work, it only persists.

**No AI here** — pure mechanics, diagnostic-only (root rule 3: gates nothing). Stdlib-only
(``json``/``logging``/``pathlib``/``datetime``) — ``import scheduler.observability`` pulls
nothing cross-phase, the same isolation discipline every other scheduler module holds.

Design notes (code = source of truth):

- **Plain append, not atomic tmp+``os.replace``.** Every other P8 state file
  (``scheduler_state.json``, the kill/command files) is a whole-file snapshot that must never
  be read half-written, so those use the tmp+rename pattern. A JSONL log only ever *grows*;
  an interrupted append leaves at most one truncated trailing line, and :func:`iter_records`
  tolerates that by skipping any line that fails to parse — self-healing, consistent with the
  project's existing fail-soft discipline (``state.py``'s ``load()``), without needing a
  rewrite-the-whole-file cost on every cycle.
- **Fail-soft write.** A write failure (disk full, permission error, …) is logged
  ``critical`` and swallowed — an observability write must never crash a data-collection
  cycle; it is bookkeeping, not safety.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

logger = logging.getLogger("scheduler.observability")


def record_cycle(
    path: str,
    *,
    ts: datetime,
    context_health: dict[str, dict[str, Any]] | None,
    picked: bool,
    n: int,
    reason: str | None,
    abort_detail: str | None,
) -> None:
    """Append one JSON-Lines record describing this cycle's research outcome.

    Args:
        path: path to the JSONL log (``data/state/research_health.jsonl``, from
            ``SchedulerConfig.observability_path``). Parent directory is created if missing.
        ts: the cycle's timestamp (the runner passes ``clock.now()`` — daemon-zone, tz-aware).
        context_health: the per-epic health snapshot (``Research.last_context_health``, or
            ``None``/``{}`` when research was never triggered this cycle, e.g. a cap-block).
        picked: whether a candidate was written this cycle (``ResearchResult.picked``).
        n: candidate count (0 or 1, ``ResearchResult.n``).
        reason: the coarse ``no_trade_reason`` code, or ``None`` on a pick
            (``ResearchResult.reason``).
        abort_detail: the free-text reason behind ``reason`` (``ResearchResult.abort_detail``
            — Phase-4's ``Research.last_abort_detail``), or ``None`` on a pick.

    Never raises — a write failure is logged ``critical`` and swallowed (see module
    docstring). Called once per WINDOW cycle by the runner, whether or not research actually
    ran this cycle.
    """
    record = {
        "ts": ts.isoformat(),
        "context_health": context_health or {},
        "picked": picked,
        "n": n,
        "reason": reason,
        "abort_detail": abort_detail,
    }
    _append(path, record)


def _append(path: str, record: dict[str, Any]) -> None:
    """Shared fail-soft JSONL append (see module docstring: plain append, never atomic)."""
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except OSError:
        logger.critical("failed to append observability record to %s", path, exc_info=True)


def record_event(path: str, event: dict[str, Any]) -> None:
    """Append an arbitrary event dict to the same log (Phase 9 / V2 Step 6).

    The generic sibling of :func:`record_cycle`'s fixed per-cycle schema — for the
    provider-chain (``bar_fetch``), circuit-breaker (``circuit_open``), divergence
    (``quote_divergence``), and universe (``universe_*``) event types the Plan's
    Cross-Phase-Edit-Register calls for. ``event`` must carry its own ``"event"``
    key (the caller decides the shape); a ``ts`` is stamped here if the caller did
    not already supply one. Same fail-soft discipline as :func:`record_cycle` — a
    write failure is logged ``critical`` and swallowed, never raised.
    """
    record = dict(event)
    record.setdefault("ts", datetime.now().isoformat())
    _append(path, record)


# -- divergence check (Phase 9 / V2 Step 6) -----------------------------------
# Deterministic, gates nothing (root rule 3) — a diagnostic cross-check between the
# IG-bar close (the momentum VETO's actual data source) and yFinance's last price
# (the ~15-min-delayed research signal), never the other way around.

def compute_divergence_pct(ig_close: float, yf_last: float) -> float:
    """``abs(ig_close - yf_last) / ig_close * 100`` — undefined (0.0) if ``ig_close`` is 0."""
    if ig_close == 0:
        return 0.0
    return abs(ig_close - yf_last) / abs(ig_close) * 100.0


def check_divergence(
    epic: str, ig_close: float, yf_last: float, *, threshold_pct: float = 0.5
) -> dict[str, Any] | None:
    """Return a ``quote_divergence`` event dict if the two sources disagree beyond
    ``threshold_pct``, else ``None`` (no event — the common case). Pure, no I/O; the
    caller passes the result to :func:`record_event` if not ``None``.
    """
    pct = compute_divergence_pct(ig_close, yf_last)
    if pct <= threshold_pct:
        return None
    return {"event": "quote_divergence", "epic": epic, "pct": pct}


def iter_records(path: str) -> Iterator[dict[str, Any]]:
    """Yield every well-formed record from the log, oldest first.

    Fail-soft on both axes: a missing file yields nothing (not an error — the daemon may not
    have run a WINDOW cycle yet), and any individual line that fails to parse as a JSON object
    is skipped with a WARNING rather than aborting the whole read (self-healing against a
    truncated trailing line from an interrupted append — see module docstring). Not used by
    the daemon itself (write-only in the hot path); provided for operator tooling / a future
    Web-UI addendum, and exercised directly by the test suite.
    """
    p = Path(path)
    if not p.exists():
        return
    with p.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                logger.warning("observability log %s: skipping unparseable line %d", path, lineno)
                continue
            if not isinstance(record, dict):
                logger.warning("observability log %s: skipping non-object line %d", path, lineno)
                continue
            yield record
