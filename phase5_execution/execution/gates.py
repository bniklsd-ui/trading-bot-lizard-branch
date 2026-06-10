"""The suitability gates of the Phase-5 pipeline — Gate 1/2/3/5 (concept §3).

Gates answer *is this candidate even eligible?* — before the fresh-snapshot VETOs
(Step 5) and the order (Step 6). They are pure, testable functions: the
orchestrator (Step 8) fetches the broker envelopes / state once and passes them
in; nothing here does I/O, reads a clock it wasn't given, or calls AI.

- **Gate 1** ``gate_time_window`` — are we inside the configured trade window?
- **Gate 2** ``gate_load_candidates`` — is there a fresh research candidate (else
  run research once, lazily injected, and reload)? Empty ⇒ abstain.
- **Gate 3** ``gate_constraints`` — budget available and room under
  ``max_parallel_positions``?
- **Gate 5** ``gate_direction_consistency`` (ex-"Direction Fix", Decision A) — a
  thin **pass-through** check that ``direction`` is BUY/SELL and there's no open
  *opposite* position on the same epic. **No FLIP / no fix** — the direction
  arrives finished and clamped from Phase 4. Together with ``build_order_plan``
  (Step 6) this is the Phase-6 seam: the debate can replace the direction source
  without rewriting the gates.

Gate 4 (sizing) is ``sizing.py`` (Step 4). Every gate returns a
:class:`~execution.models.GateVerdict`; ``ok=False`` means no trade this cycle
(``reason`` is logged to stderr by the executor — never stdout). Phase-isolated:
stdlib + ``execution`` types only, no sibling-package imports.
"""

from __future__ import annotations

from datetime import datetime, time
from typing import Any, Callable
from zoneinfo import ZoneInfo

from execution.config import ExecutionConfig
from execution.models import GateVerdict

# Direction vocabulary — what ``open_position`` enforces. No options vocabulary.
_VALID_DIRECTIONS = ("BUY", "SELL")
_OPPOSITE = {"BUY": "SELL", "SELL": "BUY"}


def _parse_hhmm(value: str) -> time:
    """Parse an ``"HH:MM"`` window string into a ``datetime.time``."""
    hour, minute = (int(part) for part in value.split(":", 1))
    return time(hour=hour, minute=minute)


def gate_time_window(now: datetime, config: ExecutionConfig) -> GateVerdict:
    """Gate 1: is ``now`` (interpreted in ``config.tz``) inside the trade window?

    ``now`` is converted to ``config.tz`` (``astimezone`` if tz-aware; assumed to
    already be in-zone if naive), then its time-of-day is compared inclusively
    against ``trading_window_start``/``trading_window_end``.
    """
    zone = ZoneInfo(config.tz)
    local = now.astimezone(zone) if now.tzinfo is not None else now
    current = local.time()
    start = _parse_hhmm(config.trading_window_start)
    end = _parse_hhmm(config.trading_window_end)
    if start <= current <= end:
        return GateVerdict(ok=True, gate="time_window", reason="")
    return GateVerdict(
        ok=False,
        gate="time_window",
        reason=(
            f"{current.strftime('%H:%M')} outside trade window "
            f"{config.trading_window_start}-{config.trading_window_end} {config.tz}"
        ),
    )


def gate_load_candidates(
    state: Any,
    research_runner: Callable[[], list[dict[str, Any]]],
    config: ExecutionConfig,
) -> tuple[GateVerdict, dict[str, Any] | None]:
    """Gate 2: obtain a fresh research candidate, running research if needed.

    If ``state.candidates_are_fresh()`` the stored candidates are used as-is;
    otherwise ``research_runner()`` is invoked (lazily injected — keeps Phase 4
    out of this module) and the candidates are re-read via ``load_candidates()``
    so the persisted file is the single source of truth. An empty result is an
    **abstain** (no trade), not a fault. On a pick, the **first** candidate is
    returned (Phase 4 persists at most one).
    """
    if not state.candidates_are_fresh():
        research_runner()

    candidates = state.load_candidates()
    if not candidates:
        return (
            GateVerdict(
                ok=False,
                gate="load_candidates",
                reason="no fresh candidate (research abstained or empty)",
            ),
            None,
        )
    return GateVerdict(ok=True, gate="load_candidates", reason=""), candidates[0]


def gate_constraints(
    account_env: Any,
    open_positions_env: Any,
    candidate: dict[str, Any],
    config: ExecutionConfig,
) -> GateVerdict:
    """Gate 3: budget available and room under ``max_parallel_positions``.

    Fail-safe: if either envelope is not ``ok`` we cannot verify eligibility, so
    the gate rejects (a no-trade, distinct from a VETO). Reads ``available`` from
    the account and counts ``positions`` from the open-positions envelope.
    """
    if not account_env.ok:
        return GateVerdict(
            ok=False, gate="constraints", reason="account snapshot unavailable",
        )
    if not open_positions_env.ok:
        return GateVerdict(
            ok=False, gate="constraints", reason="open-positions snapshot unavailable",
        )

    available = float((account_env.data or {}).get("available", 0) or 0)
    if available <= 0:
        return GateVerdict(
            ok=False, gate="constraints", reason=f"no available budget ({available})",
        )

    positions = (open_positions_env.data or {}).get("positions", [])
    if len(positions) >= config.max_parallel_positions:
        return GateVerdict(
            ok=False,
            gate="constraints",
            reason=(
                f"{len(positions)} open >= max_parallel_positions "
                f"{config.max_parallel_positions}"
            ),
        )

    return GateVerdict(ok=True, gate="constraints", reason="")


def gate_direction_consistency(
    candidate: dict[str, Any], open_positions_env: Any
) -> GateVerdict:
    """Gate 5: direction is BUY/SELL and no open *opposite* position on the epic.

    A pure pass-through consistency check — **no fix, no FLIP**. The direction is
    already final and long-bias-clamped from Phase 4. A same-direction or
    different-epic open position does **not** block here (parallel count is Gate 3
    / VETO 4). Fail-safe: a not-``ok`` positions envelope rejects.
    """
    direction = candidate.get("direction")
    if direction not in _VALID_DIRECTIONS:
        return GateVerdict(
            ok=False,
            gate="direction_consistency",
            reason=f"invalid direction {direction!r} (expected BUY/SELL)",
        )

    if not open_positions_env.ok:
        return GateVerdict(
            ok=False,
            gate="direction_consistency",
            reason="open-positions snapshot unavailable",
        )

    epic = candidate.get("epic")
    opposite = _OPPOSITE[direction]
    positions = (open_positions_env.data or {}).get("positions", [])
    for pos in positions:
        if pos.get("epic") == epic and pos.get("direction") == opposite:
            return GateVerdict(
                ok=False,
                gate="direction_consistency",
                reason=f"open {opposite} position on {epic} conflicts with {direction}",
            )

    return GateVerdict(ok=True, gate="direction_consistency", reason="")
