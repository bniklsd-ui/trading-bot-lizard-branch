---
status: closed
purpose: Dated snapshot — the M1 decision, applying the preregistered rule from
  META_M1_PREREGISTRATION.md literally against META_M1_RESULTS.md. Never edited after
  commit — corrections are a new, dated, superseding document.
read-when: checking whether/why M1 concluded "migrate" or "don't migrate"
detail: L1
up: ./CLAUDE.md
updated: 2026-07-09
---

# META_M1_DECISION — 2026-07-09

## Rule (verbatim from `META_M1_PREREGISTRATION.md`, committed 2026-07-08)

**Migrate ⇔ (measured `gate_pass` gap ≤ Δ) AND (E ≥ M).**

## Inputs

| Symbol | Preregistered value | Measured / known |
|---|---|---|
| Δ | 10 pp | — |
| gate_pass gap | — | **0.00 pp** (90% vs. 90%, `META_M1_RESULTS.md`) |
| E | 73.50 € | — |
| M | 120 € | — |

## Applying the rule

- Gap (0.00 pp) ≤ Δ (10 pp) → **TRUE**
- E (73.50 €) ≥ M (120 €) → **FALSE**

**Migrate = TRUE AND FALSE = FALSE.**

## Decision: **No migration.**

This was the predetermined outcome stated in the preregistration itself, before any trial
ran — E < M alone already excludes migration regardless of the bake-off's result. Nothing
about the measured numbers changes that; no re-adjustment of Δ/P/K/M was made or considered
(prohibited by the preregistration's own anti-shopping clause).

## Fire-extinguisher finding (the bake-off's actual purpose)

The bake-off ran to completion anyway, because its purpose was never this decision — it was
a defensible number for a *forced*-migration scenario (Anthropic becomes unusable) and a
proof that the build path/context portability actually works with a foreign harness. That
number, now known:

**In a forced-migration case, OpenCode's measured `gate_pass_rate` gap vs. Claude Code on
this repo's real conventions is 0 pp (not distinguishable from noise) at N=20 trials
(S1–S5 × 2 repeats).** Both harnesses passed 9/10 measured trials, with the one failure per
harness independently traceable to the same root cause (see `META_M1_RESULTS.md`), not a
harness-capability gap. Context portability (M1-D11) also held qualitatively — OpenCode
followed the doc-layers `CLAUDE.md`/phase-head navigation selectively and correctly where it
had a genuine cross-phase information need (Annex, `META_M1_RESULTS.md`).

**Practical takeaway:** if Anthropic access is ever lost, OpenCode + the same model is a
credible fallback build path for this repo — not a theoretical one. Claude Code remains the
default (no cost/benefit reason to switch today); this is insurance, confirmed to work,
not a plan to act on.

## Status

M1's core measurement question (H_Build vs. H0_Build) is answered: not rejected, gap within
tolerance. Steps 9 (`AGENTS.md`) and 10 (P4/P6 cold fallback) remain open, per the plan
(`docs/concepts/meta_m1_harness_plan.md` §11–§12) — orthogonal to this decision, not gated on
it.
