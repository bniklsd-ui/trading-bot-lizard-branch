"""Module 7 — the daily token-budget gate (``TokenBudget``): cost cap, **no AI**.

The autonomous daemon runs a real Phase-4 research LLM call every cycle, so a runaway loop
could burn unbounded Anthropic tokens. **Decision 12** caps that: once today's consumed
tokens reach ``config.daily_token_budget``, no new trade cycles start (monitoring / reconcile
keep running). This is the concrete class that satisfies the duck-typed
:class:`scheduler.safety.Budget` Protocol that Module 6 already depends on.

It **reuses the existing 8-field token meter** rather than introducing a second metering
system: ``research.token_meter.record`` appends one record per LLM call to the shared
``data/state/llm_usage.json`` (across Phase 4 research, Phase 6 debate, Phase 7 lesson). There
is **no importable reader** for that log — the only aggregator is a script
(``phase4_research/scripts/usage_report.py``, all-time totals) — so this module reads the JSON
array itself, fail-soft, filters to **today**, and sums the token fields.

Four points worth pinning (code = source of truth — see the dated concept §7 annotation):

1. **Constructor takes ``usage_log_path`` + ``now_fn``, not ``token_meter``.** The concept §7
   sketch was ``TokenBudget(config, token_meter)``, but the Phase-4 ``token_meter`` module has
   **no read API** — there is nothing to inject from it (the concept's own note: "Kein Reader →
   budget.py summiert die heutigen Records selbst"). So the budget reads the log file directly:
   it needs *where* to read (``usage_log_path``, supplied by the wiring — the same shape as
   ``safety.py`` taking ``kill_path`` explicitly) and *the day boundary* (``now_fn``, tz-aware,
   for deterministic tests). ``config.py`` (Module 1) is **not** touched (no ``usage_log_path``
   field added — kept minimal).

2. **The "today" boundary is Europe/Berlin, computed from a UTC timestamp.** ``token_meter``
   writes ``ts`` in **UTC** with a ``Z`` suffix (``"2026-06-08T12:40:56.980Z"``), but the
   daemon's day boundary is ``config.tz`` (consistent with the ``state`` rollover). So each
   record's UTC ``ts`` is converted to ``config.tz`` *before* taking its date — a call at
   ``22:30Z`` belongs to the next Berlin day (CEST = +2). Stdlib only (``datetime.fromisoformat``
   with a ``Z``→``+00:00`` swap + ``zoneinfo``); ``research.timeutil`` is deliberately **not**
   imported, so ``import scheduler.budget`` pulls nothing cross-phase.

3. **The token measure is all four billed token fields** — ``input_tokens`` + ``output_tokens``
   + ``cache_creation_input_tokens`` + ``cache_read_input_tokens`` — each read tolerantly
   (older 6-field records lack the ``cache_*`` keys → 0). Counting all billed throughput means
   the budget never *undercounts* (Phase 6 caches → non-zero ``cache_*``). v1, tunable at real
   output.

4. **An advisory budget fails OPEN.** A missing / corrupt log → ``consumed_today() == 0`` → not
   exhausted → cycles allowed. This is deliberately *unlike* ``safety.py``'s fail-**closed**
   loss-breaker: the budget is a cost cap, not a money-safety gate, and the token meter itself
   is "advisory, never break a pick". A transient log-read glitch must not halt data collection.
   :meth:`is_exhausted` therefore **never raises** — the safety gate trusts the Protocol to
   return a bool.

Repo conventions apply (``from __future__ import annotations``, type hints + docstrings, one
file = one responsibility, logging to a module logger, never swallow silently). **No AI, no
network** — pure file read + arithmetic.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from scheduler.config import SchedulerConfig

logger = logging.getLogger("scheduler.budget")

# The billed token-count fields of a ``token_meter`` record. ``input_tokens`` /
# ``output_tokens`` are always present; the two ``cache_*`` fields were added for Phase 6 and
# are absent from older 6-field records (→ counted as 0). Summing all four is total billed
# throughput.
_TOKEN_FIELDS: tuple[str, ...] = (
    "input_tokens",
    "output_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
)


def _load_log(path: str) -> list[dict[str, Any]]:
    """Load the usage-log JSON array, tolerating absence / corruption (never raises).

    Missing file → ``[]``. Corrupt JSON or a non-array payload → one WARNING + ``[]``. Mirrors
    the fail-soft ``token_meter._load_log`` / ``usage_report.load_records`` pattern: the usage
    log is advisory, so a read problem yields "nothing consumed" rather than an exception.
    """
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        logger.warning("token usage log at %s unreadable (%s) — counting 0 today.", p, exc)
        return []
    if not isinstance(data, list):
        logger.warning("token usage log at %s is not a JSON array — counting 0 today.", p)
        return []
    return data


def _record_tokens(rec: dict[str, Any]) -> int:
    """Sum the billed token fields of one record, tolerating absent / non-int values.

    Each field is read via ``rec.get(f, 0) or 0`` then coerced to ``int``; a missing key,
    ``None``, or a non-numeric value contributes 0 rather than raising.
    """
    total = 0
    for field in _TOKEN_FIELDS:
        value = rec.get(field, 0) or 0
        try:
            total += int(value)
        except (TypeError, ValueError):
            continue
    return total


def _record_local_date(ts: Any, tz: ZoneInfo) -> date | None:
    """Return the record's calendar date in ``tz``, or ``None`` if ``ts`` is unusable.

    ``ts`` is the UTC ISO string ``token_meter`` writes (``"...Z"``). It is parsed with stdlib
    ``datetime.fromisoformat`` (swapping the ``Z`` for ``+00:00``); a naive parse is assumed
    UTC. The result is converted to ``tz`` and its ``.date()`` returned. A missing /
    non-string / unparseable ``ts`` returns ``None`` (the record is skipped, fail-soft).
    """
    if not isinstance(ts, str):
        return None
    try:
        normalized = ts.replace("Z", "+00:00") if ts.endswith("Z") else ts
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(tz).date()


class TokenBudget:
    """The daily token-budget gate (concept §7, Decision 12) — satisfies ``safety.Budget``.

    Args:
        config: the frozen :class:`~scheduler.config.SchedulerConfig`. Reads
            ``daily_token_budget`` (the cap, ``None`` ⇒ disabled) and ``tz`` (the day zone).
        usage_log_path: path to the shared ``data/state/llm_usage.json`` written by
            ``research.token_meter`` (resolved by the wiring).
        now_fn: returns the current tz-aware ``datetime``; defaults to now in ``config.tz``.
            Injected so tests can pin "today" deterministically.
    """

    def __init__(
        self,
        config: SchedulerConfig,
        usage_log_path: str,
        *,
        now_fn: Callable[[], datetime] | None = None,
    ) -> None:
        self._config = config
        self._usage_log_path = usage_log_path
        self._tz = ZoneInfo(config.tz)
        self._now_fn = now_fn or (lambda: datetime.now(self._tz))

        # One loud WARNING at construction when the budget is disabled — this warning lives in
        # budget.py (not config.py), so each module owns the warning for its own gate (mirrors
        # safety.py's loss-cap-None warning). Concept §7: "None → … + WARNING".
        if config.daily_token_budget is None:
            logger.warning(
                "TokenBudget: daily_token_budget is None — the token budget is DISABLED; "
                "cycles will never be budget-gated. Set daily_token_budget at wiring."
            )

    def consumed_today(self) -> int:
        """Return the total billed tokens recorded **today** (in ``config.tz``).

        Sums :func:`_record_tokens` over every usage-log record whose UTC ``ts`` maps to the
        current ``config.tz`` date. Counts all models (research + debate + lesson) — it is a
        system-wide daily budget over the shared meter. Fail-soft: a missing / corrupt log or a
        record with an unusable ``ts`` contributes nothing rather than raising.
        """
        today = self._now_fn().astimezone(self._tz).date()
        total = 0
        for rec in _load_log(self._usage_log_path):
            if not isinstance(rec, dict):
                continue
            if _record_local_date(rec.get("ts"), self._tz) == today:
                total += _record_tokens(rec)
        return total

    def is_exhausted(self) -> bool:
        """Return whether today's token budget is spent (``True`` ⇒ block new cycles).

        ``daily_token_budget is None`` ⇒ disabled ⇒ ``False`` (warned once at construction).
        Otherwise ``consumed_today() >= daily_token_budget`` (the boundary is inclusive: spending
        exactly the budget exhausts it). Never raises — the auto-confirm gate trusts this bool.
        """
        budget = self._config.daily_token_budget
        if budget is None:
            return False
        return self.consumed_today() >= budget
