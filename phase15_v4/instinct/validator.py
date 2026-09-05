"""Instinct validation — **deterministic code only**, no LLM (Plan §1 P11 / AK8).

The validator is the only authority that may move an :class:`Instinct` out of
``proposed``. It counts ``evidence_trade_ids`` against ``contradictions_trade_ids``
after joining both against the **real** ``trade_outcomes`` rows provided by the
caller (the caller's trade context — the validator never reaches for the DB on
its own; the wiring decides).

Why deterministic (CLAUDE.md "Core principle"):
- The LLM has already had its say at extraction time. Re-asking an LLM "is this
  instinct well-supported?" is the exact anti-pattern the project guards against:
  hallucinated validation is structurally indistinguishable from real validation.
- The validator runs on every instinct, every cycle. Determinism makes its
  decisions auditable — re-running on the same trades MUST produce the same
  verdict (this is the property the regression tests pin).

Decision rule (Plan §6 C2):
- ``evidence_count > contradictions_count`` and ``evidence_count >= MIN_EVIDENCE``
  → ``validated``
- ``contradictions_count >= evidence_count`` → ``refuted`` (the rule is contradicted
  by at least as many trades as support it — no signal either way)
- otherwise (insufficient evidence, tie in favour of evidence) → stay ``proposed``

``MIN_EVIDENCE = 3`` is a deliberately conservative floor — one trade cannot
establish a pattern. Tunable later on real data; today the harness has ``n=8``
closed trades, so any instinct supported by <3 rows is structurally unpromotable
through the evidence gate alone (Plan §1 P12 — promotion still needs
``n_closed >= InstinctConfig.instinct_n_min``, default 50).

This module imports nothing from ``extractor.py``, ``brain.py``,
``research.llm_client`` or any other LLM-touching code — enforced by the
``test_validator_has_no_llm`` regression test (Plan §7 AK8).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Iterable

from instinct.models import Instinct

logger = logging.getLogger(__name__)

__all__ = ["InstinctValidator", "InstinctValidation"]


# Conservative floor: a single supporting trade cannot establish a pattern.
# Tunable later on real data; today n=8 makes any instinct with <3 evidence
# rows structurally unpromotable even if it passes the contradiction check.
MIN_EVIDENCE: int = 3


@dataclass(frozen=True)
class InstinctValidation:
    """Outcome of validating one :class:`Instinct` against real trades.

    Attributes:
        decision: ``"validated"`` | ``"refuted"`` | ``"proposed"``
            (``"proposed"`` = "evidence/contradiction counts do not warrant a
            transition yet"; the caller leaves the DB row untouched).
        evidence_count: number of supporting trades that were found in
            ``trades`` (i.e. evidence IDs that resolve to real rows).
        contradiction_count: same for contradictions.
        reason: short string suitable for a log line. Empty when the decision
            is obvious from the counts.
    """

    decision: str
    evidence_count: int
    contradiction_count: int
    reason: str

    def __post_init__(self) -> None:
        if self.decision not in ("validated", "refuted", "proposed"):
            raise ValueError(
                f"decision must be one of validated/refuted/proposed, "
                f"got {self.decision!r}"
            )
        if self.evidence_count < 0 or self.contradiction_count < 0:
            raise ValueError("counts must be non-negative")


class InstinctValidator:
    """Deterministic validator — counts evidence vs. contradictions.

    Stateless beyond ``MIN_EVIDENCE``. Pure function: same instinct + same trades
    ⇒ same verdict, every time (the regression tests pin this).
    """

    def __init__(self, min_evidence: int = MIN_EVIDENCE) -> None:
        """Bind the minimum-evidence floor. Default :data:`MIN_EVIDENCE` = 3."""
        if min_evidence <= 0:
            raise ValueError(f"min_evidence must be > 0, got {min_evidence}")
        self._min_evidence = min_evidence

    def validate(
        self,
        instinct: Instinct,
        trades: Iterable[dict[str, Any]],
    ) -> InstinctValidation:
        """Decide whether ``instinct`` advances out of ``proposed``.

        Args:
            instinct: the candidate. ``evidence_trade_ids`` and
                ``contradictions_trade_ids`` are the LLM's claim; this method
                counts how many of those IDs resolve to **real** trade rows
                in ``trades``.
            trades: an iterable of trade rows (any object that supports
                ``in`` — typically ``list[dict[str, Any]]``). Each row's ``id``
                key is checked; rows without ``id`` are ignored (defensive).

        Returns:
            :class:`InstinctValidation` with one of three decisions.
        """
        # Build the set of real trade IDs once. ``trades`` may be a generator
        # — iterate it through a set so each id is unique and lookups are O(1).
        real_ids: set[int] = set()
        for row in trades:
            row_id = row.get("id") if isinstance(row, dict) else None
            if isinstance(row_id, int):
                real_ids.add(row_id)

        evidence_count = sum(
            1 for tid in instinct.evidence_trade_ids if tid in real_ids
        )
        contradiction_count = sum(
            1 for tid in instinct.contradictions_trade_ids if tid in real_ids
        )

        # Decision rule — see module docstring.
        if (
            evidence_count > contradiction_count
            and evidence_count >= self._min_evidence
        ):
            decision = "validated"
            reason = (
                f"evidence={evidence_count} > contradictions={contradiction_count} "
                f"(min_evidence={self._min_evidence})"
            )
        elif contradiction_count >= evidence_count and contradiction_count > 0:
            decision = "refuted"
            reason = (
                f"contradictions={contradiction_count} >= evidence={evidence_count}"
            )
        else:
            decision = "proposed"
            if evidence_count < self._min_evidence:
                reason = (
                    f"evidence={evidence_count} < min_evidence={self._min_evidence} "
                    f"(insufficient signal)"
                )
            else:
                reason = (
                    f"evidence={evidence_count} == contradictions={contradiction_count} "
                    f"(no clear signal)"
                )

        logger.info(
            "instinct.validate: id=%s -> %s (%s)",
            instinct.id,
            decision,
            reason,
        )
        return InstinctValidation(
            decision=decision,
            evidence_count=evidence_count,
            contradiction_count=contradiction_count,
            reason=reason,
        )
