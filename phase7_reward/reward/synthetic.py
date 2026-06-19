"""Synthetic-data generation + the hard synthetic/live separation (Step 6, Decision H).

**Pure, deterministic, no DB writes** — no network, no LLM, no broker. Like
:mod:`reward.confidence` and :mod:`reward.scorer`, every number here is plain code.

Decision H keeps three data sources cleanly apart:

- **synthetic** — generated test data (``synthetic=True``), used to exercise the
  confidence/scorer math. It must **never** reach the live store: the boundary is
  the *DB path* ("Grenze = der DB-Pfad, nicht nur ein Flag"), with the ``synthetic``
  tag as defense-in-depth.
- **demo** — real IG-demo trades (real fills, no real money). They flow through the
  normal path into the live DB, tagged ``account='demo'``, and count toward the edge
  metric only while ``include_demo_in_edge`` is set (the bootstrap default).
- **live** — real-money trades; always count toward the edge.

This module ships the *library* for that separation; the actual synthetic-DB
*writer* is the Step-13 operator CLI ``backfill_synthetic.py``, which calls
:func:`guard_synthetic_path` **before** opening any database. Three pieces:

- :class:`SyntheticTradeGenerator` → labelled R-multiple distributions.
- :func:`guard_synthetic_path` → the path boundary (raises before a live write).
- :func:`select_edge_set` → the ``include_demo_in_edge`` + synthetic-exclusion rule,
  producing the ``(r_multiples, wins, n)`` triple :func:`reward.compute_confidence`
  consumes.
"""

from __future__ import annotations

import random
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from reward.models import RewardConfig, SyntheticSafetyError

__all__ = [
    "SyntheticTrade",
    "SyntheticTradeGenerator",
    "guard_synthetic_path",
    "select_edge_set",
]

# Sentinel so ``_field`` can distinguish "absent, use default" from "required".
_REQUIRED = object()


@dataclass(frozen=True)
class SyntheticTrade:
    """One clearly-labelled synthetic trade outcome (never real).

    Attributes:
        r_multiple: realised P&L over initial risk (the scoring unit).
        win_loss: ``"WIN"`` | ``"LOSS"`` | ``"BREAKEVEN"`` from the sign of ``r_multiple``.
        account: the data-source tag; defaults to ``"synthetic"``.
        synthetic: always ``True`` — the defense-in-depth flag on top of the path split.
    """

    r_multiple: float
    win_loss: str
    account: str = "synthetic"
    synthetic: bool = True


def _win_loss(r_multiple: float) -> str:
    """Classify an R-multiple the same way the scorer does (sign → label)."""
    if r_multiple > 0:
        return "WIN"
    if r_multiple < 0:
        return "LOSS"
    return "BREAKEVEN"


class SyntheticTradeGenerator:
    """Deterministic generator of labelled R-multiple distributions (for tests).

    Reproducible: construct with a fixed ``seed`` to get an identical sequence. The
    output never touches a database — it feeds the pure confidence/scorer math.
    """

    def __init__(self, seed: int | None = None) -> None:
        """Bind a private RNG seeded by ``seed`` (``None`` → nondeterministic)."""
        self._rng = random.Random(seed)

    def generate(
        self,
        n: int,
        *,
        win_rate: float,
        win_r: float = 1.5,
        loss_r: float = -1.0,
        jitter: float = 0.0,
        account: str = "synthetic",
    ) -> list[SyntheticTrade]:
        """Generate ``n`` synthetic trades with roughly ``win_rate`` winners.

        Each trade is a win (``r ≈ win_r``) with probability ``win_rate``, else a loss
        (``r ≈ loss_r``); ``jitter`` adds a symmetric ``±jitter`` uniform wobble. The
        ``win_loss`` label always reflects the **final** sign of ``r_multiple``, and
        every trade is tagged ``synthetic=True``.

        Args:
            n: number of trades (``>= 0``).
            win_rate: probability a trade is a winner (``0.0 <= win_rate <= 1.0``).
            win_r: nominal R-multiple of a winner.
            loss_r: nominal R-multiple of a loser.
            jitter: symmetric uniform noise added to each R-multiple.
            account: the account tag for the batch (default ``"synthetic"``).

        Returns:
            A list of :class:`SyntheticTrade`.

        Raises:
            ValueError: if ``n < 0`` or ``win_rate`` is outside ``[0, 1]``.
        """
        if n < 0:
            raise ValueError(f"n must be >= 0, got {n}")
        if not 0.0 <= win_rate <= 1.0:
            raise ValueError(f"win_rate must be in [0, 1], got {win_rate}")

        trades: list[SyntheticTrade] = []
        for _ in range(n):
            base = win_r if self._rng.random() < win_rate else loss_r
            r = base + (self._rng.uniform(-jitter, jitter) if jitter else 0.0)
            trades.append(
                SyntheticTrade(
                    r_multiple=r,
                    win_loss=_win_loss(r),
                    account=account,
                    synthetic=True,
                )
            )
        return trades

    @staticmethod
    def edge_inputs(
        trades: Iterable[SyntheticTrade],
    ) -> tuple[list[float], int, int]:
        """Extract ``(r_multiples, wins, n)`` for :func:`reward.compute_confidence`.

        No filtering — the caller passes an already-selected, homogeneous list (use
        :func:`select_edge_set` when a heterogeneous record set needs the source rules
        applied). ``wins`` counts strictly positive R-multiples (breakeven is not a win).
        """
        r_multiples = [t.r_multiple for t in trades]
        wins = sum(1 for r in r_multiples if r > 0)
        return r_multiples, wins, len(r_multiples)


def guard_synthetic_path(target: str | Path, cfg: RewardConfig) -> str:
    """Return the resolved ``target`` path, or raise if it is the live database.

    The single safety boundary of Decision H: any synthetic writer must call this
    **before** opening a database, so synthetic data can never land in the live store.
    Both paths are resolved with :meth:`pathlib.Path.resolve` so a relative spelling
    can't alias the live path past the check.

    Args:
        target: the intended synthetic write path.
        cfg: the reward config (its ``live_db_path`` is the forbidden target).

    Returns:
        The resolved absolute ``target`` path as a string.

    Raises:
        SyntheticSafetyError: if ``target`` resolves to ``cfg.live_db_path``.
    """
    target_resolved = Path(target).resolve()
    live_resolved = Path(cfg.live_db_path).resolve()
    if target_resolved == live_resolved:
        raise SyntheticSafetyError(
            f"refusing to write synthetic data to the live database path "
            f"({target_resolved}); synthetic writes must target a separate file "
            f"(cfg.synthetic_db_path)"
        )
    return str(target_resolved)


def _field(rec: Any, name: str, default: Any = _REQUIRED) -> Any:
    """Read ``name`` from a mapping row or an object (e.g. :class:`SyntheticTrade`)."""
    if isinstance(rec, Mapping):
        if name in rec:
            return rec[name]
    elif hasattr(rec, name):
        return getattr(rec, name)
    if default is _REQUIRED:
        raise KeyError(f"record is missing required field {name!r}")
    return default


def select_edge_set(
    records: Iterable[Any], cfg: RewardConfig
) -> tuple[list[float], int, int]:
    """Apply the edge-source rules and return ``(r_multiples, wins, n)``.

    The rules (Decision H), per record (a :class:`SyntheticTrade` or a mapping row
    carrying ``r_multiple`` / ``account`` / ``synthetic``):

    - drop anything tagged ``synthetic`` (never counts, regardless of any flag);
    - drop ``account == 'demo'`` unless ``cfg.include_demo_in_edge``;
    - keep everything else (``'live'`` always counts).

    ``wins`` counts strictly positive R-multiples (breakeven is not a win). The result
    feeds :func:`reward.compute_confidence` directly. Forward-compatible: the later
    DB-backed provider (Step 8) supplies joined trade+reward rows in the same shape.
    """
    r_multiples: list[float] = []
    for rec in records:
        if _field(rec, "synthetic", False):
            continue
        if _field(rec, "account", None) == "demo" and not cfg.include_demo_in_edge:
            continue
        r_multiples.append(float(_field(rec, "r_multiple")))
    wins = sum(1 for r in r_multiples if r > 0)
    return r_multiples, wins, len(r_multiples)
