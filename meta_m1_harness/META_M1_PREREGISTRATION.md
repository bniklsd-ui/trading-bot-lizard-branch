---
status: locked
purpose: Preregistered Δ/P/K/E/M values + decision rule for the M1 harness bake-off — committed
  before any trial exists, per this doc's own anti-shopping prohibition. Never edited after commit.
read-when: applying the M1 decision rule to measured trial results (Step 8); auditing whether the
  rule was set before or after the numbers were seen
detail: L2
up: ./CLAUDE.md
updated: 2026-07-08
---

# META_M1_PREREGISTRATION

> **This document is committed before the first bake-off trial runs and is never edited
> afterward.** Corrections happen only as a new, dated, superseding document with a stated
> reason — never as an edit to this file. Changing Δ, P, K, M, or the measurement design after
> seeing results is "shopping for a migration-friendly outcome" and is explicitly forbidden by
> the source Konzept (`docs/concepts/meta_phase_unabhaengigkeit_konzept.md`, §4 Anti-Pattern-
> Warnung).

## Hypothesis (verbatim, from Konzept §1)

**H_Build:** Für sequentielle Schritt-Ausführung gegen einen detaillierten Plan erreicht ein
offener Harness (OpenCode oder Aider) + **festes Modell** eine Task-Completion- und
Edit-Zuverlässigkeit **innerhalb einer vorab definierten Toleranz Δ** von Claude Code +
demselben Modell.

**H0_Build (Null):** Der Abstand ist > Δ (der offene Harness ist auf *meinem* Repo spürbar
schlechter). → Nicht migrieren; Claude Code bleiben, kalter Fallback genügt.

## Preregistered values

| Symbol | Value | Meaning |
|---|---|---|
| Δ | **10 pp** | Max. accepted `gate_pass_rate` gap between harnesses (resolution at 10 trials/harness = 10 pp) |
| P | **0.35** | P(Anthropic becomes unusable for me within 12 months) |
| K | **210 €** | Cost of a ~2-week outage (14 d × 1 h/d × 15 €/h) |
| E | **73.50 €** | Expected outage cost = P × K |
| M | **120 €** | Migration cost (8 h × 15 €/h) |

## Decision rule

**Migrate ⇔ (measured `gate_pass` gap ≤ Δ) AND (E ≥ M).**

**Predetermined fact (not a bug, not a reason to adjust anything):** E (73.50 €) < M (120 €)
already, before any measurement exists. Migration is therefore excluded **regardless of the
bake-off's outcome**. The bake-off still runs to completion in full — its purpose is a
fire-extinguisher test of the build path (a defensible number for a forced-migration scenario,
and proof that context portability works), not a decision input.

## Noise rule

If within-harness variance (spread of `gate_pass_rate` across the 2 repeats) is greater than
the between-harness gap, the gap is reported as **"not distinguishable"** rather than as a
winner/loser.

## Measurement design

- Steps **S1–S5** measured (N = 5 real step specs), **2 repeats** each, **2 harnesses**
  (Claude Code vs. OpenCode) = **20 trials** total.
- Each trial starts from git tag `base-(k−1)` (the reference-build state immediately before
  that step) inside an isolated, throwaway fork — never the live repo/DB/state/keyring.
- Model and effort fixed identically across both harnesses (M1-D4); deviations documented in
  `META_M1_RESULTS.md`, not silently absorbed.
- Budget cap: **50 €** hard, guarded by `BudgetGuard` in the runner; a trip produces a clean
  stop and a partial-result report, not a crash.
- S6–S7 run only in the reference build (module completeness, further base tags), unmeasured.

## Prohibition

No changes to Δ, P, K, M, or the measurement design after this document's commit. Any
correction is a new, dated, superseding document stating the reason — this file is never
edited again.
