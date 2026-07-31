"""Process-aware reward scoring for Phase 7 (concept §6 Step 5, Decision B2/D).

**Pure, deterministic, no I/O** — no network, no LLM, no broker, no DB. Together
with :mod:`reward.confidence` this is one of the two most test-critical modules in
the phase (★), and it is *not* AI: the "AI as little as possible" principle puts
every number here in plain code. A score is never an LLM output.

The product is a :class:`~reward.models.RewardResult` for one closed trade. Its
score delta is **process-aware from day one** (Decision B2), not outcome-only: a
clean win that hit a planned SL/TP through a tight entry spread is rewarded *more*
than the same win that merely drifted into a time-stop, and an unlucky loss at a
planned stop is punished *less* than a sloppy one. The two components are:

- ``outcome_delta`` — the braked outcome signal, proportional to the R-multiple
  clipped to ``±r_clip`` (a tail guard), scaled by ``outcome_weight`` and, on
  losses, by ``loss_asymmetry`` (``>1`` makes losses bite harder; default
  symmetric).
- ``process_delta`` — the process-quality signal, **independent of the outcome**:
  a planned exit (``CLOSED_BY_BROKER``) vs a drift exit (``TIME_STOP``), a tight
  vs wide entry spread, plus a *weak* nudge from the debate confidence (additive,
  centred at 0.5 — never a multiplier).

The summed delta is clamped to ``±max_delta_per_trade``, then ``score_after`` is
clamped to ``[score_min, score_max]`` (the DB does **not** clamp — verified-contract
1.7; the clamp lives here, before the insert).

The exact magnitudes are v1 defaults to be tuned on real profit (Decision D); like
the confidence combiner their precise shape is **not** load-bearing — what the tests
pin are the *relative* properties (good process beats bad process at equal outcome,
the clamps hold, symmetry at ``loss_asymmetry=1.0``, the process component genuinely
differentiates). Two v1 modelling choices that ``RewardConfig`` does not give a
dedicated knob for, documented here as deliberate:

* the **clean-entry** bonus reuses ``clean_exit_bonus`` as the unit process signal
  (there is no separate entry-magnitude field in concept §5);
* the **debate** signal is ``(debate_confidence / 100 - 0.5)`` — ``debate_confidence``
  is the real ``DebateOutcome.confidence`` scale, **0-100**, not ``[0, 1]``
  (Phase-10 B2-fix, 2026-07-31: the pre-fix code treated it as already ``[0, 1]``,
  so a confidence of e.g. 60 produced ``+59.5`` instead of ``+0.1`` — a ~120x
  overshoot that clamped ``total_delta`` to ``+max_delta_per_trade`` on every single
  trade regardless of outcome, see
  ``phase10_v3/DATA_WEEK_REVIEW_2026-07-31.md`` §4 B2). Normalized, this signal is
  at most ``±0.5`` of a unit, intrinsically weaker than the ``±1``-unit exit/entry
  signals, which is exactly the "weak process signal, not a multiplier" the concept
  asks for. ⚠ The scale fix alone does **not** make the reward loop outcome-neutral
  on a losing streak: a ``CLOSED_BY_BROKER`` stop-out still earns the full
  ``clean_exit_bonus`` (it hit the planned SL), so the score still drifts upward
  (~+1.2 per consecutive loss) after this fix — whether a stop-out should count as a
  "clean exit" is an open design question, not addressed here (Phase-11 H3).

Conventions mirror :mod:`reward.confidence`: stdlib only, reads every tunable from
the passed :class:`~reward.models.RewardConfig`.
"""

from __future__ import annotations

from reward.models import RewardConfig, RewardResult

__all__ = ["Scorer"]


def _clamp(x: float, lo: float, hi: float) -> float:
    """Clamp ``x`` to ``[lo, hi]`` (mirrors the inline clamp in ``confidence.py``)."""
    return min(hi, max(lo, x))


class Scorer:
    """Turn one closed trade's outcome + process signals into a clamped score delta.

    Deterministic and stateless beyond the config it is constructed with. Decision
    B2/D: process-aware, clamped, conservative, tuned on real profit later.
    """

    def __init__(self, cfg: RewardConfig) -> None:
        """Bind the (immutable) reward config; all tunables are read from it."""
        self.cfg = cfg

    def score(
        self,
        *,
        r_multiple: float,
        status: str,
        spread_at_entry_pct: float,
        debate_confidence: float | None,
        score_before: float,
    ) -> RewardResult:
        """Compute the process-aware reward delta for one closed trade.

        Args:
            r_multiple: realised P&L over initial risk (raw; clipped only for
                scoring). Sign drives ``win_loss``.
            status: the close status — ``"CLOSED_BY_BROKER"`` (planned SL/TP hit) or
                ``"TIME_STOP"`` (drift, no edge realised). Any other value is treated
                as a neutral exit (no exit signal).
            spread_at_entry_pct: the entry spread as a fraction; ``<= tight_spread_pct``
                earns the clean-entry process bonus.
            debate_confidence: the in-memory debate confidence at open time, on its
                real **0-100** scale (``DebateOutcome.confidence``), or ``None`` when
                no debate ran. A **weak, additive** process nudge only.
            score_before: the score read before this trade (``get_current_score``).

        Returns:
            A frozen :class:`~reward.models.RewardResult` carrying both delta
            components, the before/after scores, the win/loss label, and the **raw**
            R-multiple.
        """
        cfg = self.cfg

        # --- outcome component (braked, clipped, loss-asymmetric) ---
        clipped_r = _clamp(r_multiple, -cfg.r_clip, cfg.r_clip)
        asymmetry = cfg.loss_asymmetry if clipped_r < 0 else 1.0
        outcome_delta = cfg.outcome_weight * clipped_r * asymmetry

        # --- process component (independent of the outcome) ---
        if status == "CLOSED_BY_BROKER":
            exit_signal = cfg.clean_exit_bonus
        elif status == "TIME_STOP":
            exit_signal = -cfg.clean_exit_bonus
        else:
            exit_signal = 0.0

        entry_signal = (
            cfg.clean_exit_bonus if spread_at_entry_pct <= cfg.tight_spread_pct else 0.0
        )

        # Weak, centred, additive — never a multiplier (concept §6 Step 5).
        # debate_confidence is 0-100 (DebateOutcome.confidence), not [0, 1] — divide
        # before centering (Phase-10 B2-fix, 2026-07-31; see module docstring).
        debate_signal = (
            0.0 if debate_confidence is None else (debate_confidence / 100.0 - 0.5)
        )

        process_delta = cfg.process_weight * (exit_signal + entry_signal + debate_signal)

        # --- combine, clamp the per-trade delta, then clamp the resulting score ---
        total_delta = _clamp(
            outcome_delta + process_delta,
            -cfg.max_delta_per_trade,
            cfg.max_delta_per_trade,
        )
        score_after = _clamp(score_before + total_delta, cfg.score_min, cfg.score_max)

        if r_multiple > 0:
            win_loss = "WIN"
        elif r_multiple < 0:
            win_loss = "LOSS"
        else:
            win_loss = "BREAKEVEN"

        return RewardResult(
            outcome_delta=outcome_delta,
            process_delta=process_delta,
            score_before=score_before,
            score_after=score_after,
            win_loss=win_loss,
            r_multiple=r_multiple,
        )
