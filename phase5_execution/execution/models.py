"""Data contracts for the Phase 5 execution pipeline (concept §1).

Frozen dataclasses, types only — no logic, no I/O. These are the integration
surface between the modules:

- :class:`OrderPlan` — the fully-resolved, ready-to-place order (built once at
  :func:`order.build_order_plan`, after every gate/VETO passes). This is also the
  **Phase-6 seam**: the debate replaces the direction/size *source*, but the plan
  shape and the order/monitor path downstream stay the same.
- :class:`GateVerdict` / :class:`VetoVerdict` — the ok/why result of a single
  gate or VETO (``ok=False`` carries the rule name + a human reason for the log).
- :class:`ExecutionResult` — the cycle outcome the executor returns and
  ``ig_bot.py`` serialises to stdout.

Direction vocabulary is **BUY / SELL** only — what ``open_position`` enforces.
No options vocabulary anywhere: this is a DAX CFD bot.
"""

from __future__ import annotations

from dataclasses import dataclass

# Allowed ``ExecutionResult.status`` values (documented, not enforced as a type
# so logging/serialisation stay simple):
#   "OPEN"             — order accepted and a position is open (then monitored)
#   "CLOSED_BY_BROKER" — broker-side SL/TP filled; position gone during monitor
#   "TIME_STOP"        — monitor closed it (square-off or max_hold reached)
#   "NO_TRADE"         — a gate/VETO/abstain said no; clean, exit 0
#   "ABORTED_BY_USER"  — human-confirm declined; no order placed
#   "ABORT"            — fail-closed abort (see ExecutionAbort); exit non-zero


@dataclass(frozen=True)
class OrderPlan:
    """A resolved order ready for ``open_position`` (BUY/SELL, absolute levels).

    ``stop_level`` / ``limit_level`` are **absolute price levels** (not point
    distances) — IG's ``stopLevel`` / ``limitLevel``. ``deal_reference`` is the
    write-ahead idempotency key (``bot-<uuid4hex>``), persisted *before* the order.
    ``currency`` is IG's required ``currencyCode`` (resolved from the instrument's
    ``market_info``, with a config fallback — IG rejects a null currency with HTTP 400).
    """

    epic: str
    direction: str            # "BUY" | "SELL"
    size: float
    stop_level: float
    limit_level: float
    deal_reference: str
    currency: str             # IG currencyCode (e.g. "EUR") — required by open_position


@dataclass(frozen=True)
class GateVerdict:
    """Result of a single Gate (1/2/3/5). ``ok=False`` => no trade this cycle."""

    ok: bool
    gate: str                 # gate identifier, e.g. "time_window"
    reason: str               # human-readable explanation (empty when ok)


@dataclass(frozen=True)
class VetoVerdict:
    """Result of a single pre-trade VETO. ``ok=False`` => hard abort of the order."""

    ok: bool
    veto: str                 # veto identifier, e.g. "momentum"
    reason: str               # human-readable explanation (empty when ok)


@dataclass(frozen=True)
class ExecutionResult:
    """Outcome of one execution cycle (see the status constants above)."""

    status: str
    deal_id: str | None
    plan: OrderPlan | None
    detail: str
