"""Promotion gate — deterministic, code-only, never raises (Plan §1 P10/P12).

The **only** way an :class:`Instinct` reaches VETO 5 is through
:func:`promote_eligible`. Two conditions, both must hold:

1. ``cfg.enable_instinct_promotion is True`` (P10 — default ``False``).
2. ``n_closed >= cfg.instinct_n_min`` (P12 — default ``50``).

Until both gates are open the function returns ``[]`` — it never promotes
``proposed`` rows (the validator is the only authority for that transition,
see ``validator.py``), and it never promotes ``refuted`` rows.

Today (``n_closed = 8``) the second gate is closed. AK7 pins that the harness
refuses correctly: ``test_promotion_refuses_below_n_min`` is the
**phase-acceptance test** (P13).

The function is pure — no DB, no I/O, no clock. The caller (a later
Phase-15 wiring step) reads ``Database.list_instincts(status="validated")``,
counts closed trades via ``Database`` getters, and passes both into here.
This separation keeps the gate testable without a database fixture.
"""

from __future__ import annotations

from typing import Iterable

from instinct.models import Instinct, InstinctConfig

__all__ = ["promote_eligible"]


def promote_eligible(
    instincts: Iterable[Instinct],
    n_closed: int,
    cfg: InstinctConfig,
) -> list[Instinct]:
    """Return the subset of ``instincts`` that may be promoted right now.

    Both gates must be open; otherwise the empty list is returned. The
    function does **not** mutate the input iterable, does **not** touch
    the database, and does **not** raise — a pure gate function.

    The ``status`` of each input instinct is also checked: only ``"validated"``
    rows are eligible. ``proposed`` and ``refuted`` rows are skipped (the
    validator is the only authority for ``proposed`` → ``validated``/``refuted``,
    and ``refuted`` rows never promote).

    Args:
        instincts: any iterable of :class:`Instinct` rows (typically
            ``Database.list_instincts(status="validated")``).
        n_closed: number of closed trades the bot has accumulated.
        cfg: the :class:`InstinctConfig` carrying the two promotion gates.

    Returns:
        A new list of instincts that are eligible for promotion right now.
        Empty when either gate is closed or no input is ``validated``.
    """
    # Gate 1 — master switch (P10). Off by default; flipping it is a
    # Nikinger-authorized config change.
    if not cfg.enable_instinct_promotion:
        return []

    # Gate 2 — closed-trade floor (P12). Deliberately separate from
    # ``RewardConfig.n_min = 10`` (Wilson confidence threshold — see
    # ``models.py`` docstring + Plan §9.6).
    if n_closed < cfg.instinct_n_min:
        return []

    # Status filter — only ``validated`` rows are eligible. ``proposed``
    # belongs to the validator, ``refuted`` never promotes.
    return [i for i in instincts if i.status == "validated"]
