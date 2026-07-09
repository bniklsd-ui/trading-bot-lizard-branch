---
status: handover
purpose: Closeout handover for the next Web-Chat planning session — M1's intentional drifts
  from its own locked plan, and an optional M2 proposal (code-quality + cross-model bake-off).
read-when: planning what comes after M1; NOT during implementation
detail: L3
up: ./CLAUDE.md
updated: 2026-07-09
---
# Closeout Handover → next planning chat · after Meta-Phase M1

> Format: **Status + Delta (intentional drifts) + open decisions + file paths**. No
> re-transcription of implementation detail — **code is truth**. This is the entry point,
> not the plan. Companion to `PHASE10_META_KICKOFF_HANDOVER.md` (which kicked M1 off);
> this one closes it.

---

## 1. Status — where M1 stands

**Closed. Steps 0–10 all done.** The preregistered bake-off ran to completion (20/20 trials,
no budget stop, no isolation incident): `gate_pass_rate` 90%/90%, gap 0.00pp — **not
distinguishable** per M1's own noise rule. Applying the locked rule literally: **no
migration** (predetermined by E=73.50€ < M=120€ regardless, now doubly confirmed by the
measured gap). Two orthogonal deliverables shipped alongside the measurement: `AGENTS.md`
(repo-root, harness-neutral entry point) and a cold, tested, never-wired-in OpenRouter
fallback for P4/P6 (`OpenAICompatLLMClient`), smoke-PASSed against a real model. Full
numbers: `META_M1_RESULTS.md` + `META_M1_DECISION.md`.

---

## 2. Delta — intentional drifts from the locked plan (`meta_m1_harness_plan.md`)

Everything below is a **deliberate, surfaced** deviation from what was originally written
down — not silent scope creep. Read this before assuming the plan doc is exactly what ran.

- **M1-D4 (effort):** plan said `Medium`; corrected to **`High`** mid-M1 (verified against
  docs.claude.com — Sonnet 5 actually defaults to `high`, which is the real project config
  the decision meant to reference). Dated strikethrough in the plan doc, not silently edited.
- **M1-D5 (auth):** plan allowed a shell-exported env var; Nikinger overrode this to
  **keyring-only, no env var ever** — stricter than written, same isolation logic taken
  further.
- **Live-repo lockdown (`--dir` + OS-level write-lock)** was **not** in the original plan —
  added after a real incident (an OpenCode trial escaped its assigned fork and wrote into
  *this* live repo despite a correctly-set subprocess `cwd`). Confirmed holding across all
  20 real measured trials afterward.
- **Cost-parsing automation** — not planned, added after a real bug: the original
  manual-spend-prompt crashed on non-interactive `EOFError`, silently discarding an
  already-paid trial's result. Both harnesses now parse their own authoritative cost from
  JSON output.
- **Gate-command interpretation, deliberately NOT changed:** the runner's gate check is a
  bare `pytest ...` (no `python -m`), so whether a trial's `phase10_v3.*` import resolves
  depends on `__init__.py` markers the specs leave to agent judgment. This caused S1's one
  real failure per harness. **Judged as legitimate signal, not an instrument bug** (the gate
  command is the literal text every agent is shown, and the rest of this repo already
  carries proper `__init__.py` markers) — flagged, not silently patched. **Relevant for M2**
  (§3) if a quality-focused follow-up wants this removed as a confound.
- **`OpenAICompatLLMClient` constructor:** the plan's literal listed parameter order
  (`base_url` defaulted, then `model` un-defaulted) isn't valid Python syntax. Interpreted
  as `model` positional + the rest keyword-only, mirroring `LLMClient`'s own established
  pattern — same intent, syntactically real.
- **Credentials `[VERIFY API]` resolved negatively:** the existing `get_credential` helper
  is hardcoded to `SERVICE_NAME="tradingbot"` — it cannot target a separate service. Wrote a
  small, self-contained keyring accessor instead of reusing it (same isolation pattern as
  the bake-off key: a dedicated `openrouter` service, never `tradingbot`).
- **Budget reality vs. the locked 50€ cap:** the bake-off key's real balance was ~10€ at one
  point mid-M1 — below the code's own cap, which would never have tripped before a real
  API insufficient-credit error. Surfaced (M1-D6 is a locked decision, not silently edited);
  Nikinger topped up to $54.03 same-session.
- **`results/trials.jsonl` commit status — self-corrected:** an earlier session note in
  `CLAUDE.md` wrongly called this "intentionally uncommitted raw data." The plan (§9)
  explicitly requires it committed; caught and fixed before the actual commit.

---

## 3. Open decision — optional M2 proposal (Nikinger idea, not designed or locked)

**The idea:** M1 measured a narrow thing — binary `gate_pass_rate`, model and effort matched
identically across harnesses. It answers "does the harness itself matter, all else equal,"
not "what code quality do I actually get." A follow-up **M2** would test **code quality**
directly, and cross **both** harness and model, e.g. (Nikinger's own example, not a locked
choice): OpenCode + GLM vs. Claude Code standard with Sonnet 5 at **`auto` effort** — i.e.
each tool's own out-of-the-box default, not M1's deliberately-matched "both at `high`."

**Why this needs its own design pass, not a copy of M1's:**
- **Different control variables, on purpose.** M1 isolated the harness variable (same model,
  same effort). M2 as sketched does the opposite — it compares *whole configurations*
  (harness+model+effort as shipped). Both are valid questions; they are **not the same
  experiment** and shouldn't be presented as a continuation of M1's numbers.
- **"Code quality" has no ready metric.** `gate_pass_rate` was cheap and binary; quality
  isn't. Real options, each with trade-offs: an LLM-as-judge against a rubric (readability,
  convention-adherence, over-engineering/ponytail-style review, test-quality not just
  test-count) — itself an AI judgment, worth weighing against this repo's "as little AI as
  possible" principle if it's ever more than diagnostic; a Nikinger-scored sample review;
  or automated proxies (docstring coverage, complexity) as a cheaper partial signal.
- **The gate-command confound from §2 mostly disappears** if M2 grades quality directly
  rather than binary pass/fail — worth deciding explicitly rather than inheriting silently.
- **GLM is only an example.** Needs the same "check the current catalog, don't hardcode a
  stale id" treatment M1 already applied to the OpenRouter smoke test's model choice.
- **Needs its own Δ/P/K/E/M-equivalent preregistration** — M2 answers a different question
  than M1's migration-cost framing, so M1's numbers don't transfer; a real cost/benefit
  case for *this* measurement should exist before it runs, same anti-shopping discipline
  `META_M1_PREREGISTRATION.md` modeled.

Nothing here is designed — it's a kickoff seed for the next Web-Chat session, same role
`meta_phase_unabhaengigkeit_konzept.md` played for M1.

---

## 4. Watch-items (small, not fixed, just context)

- S1's split result (each harness failed exactly one of its two repeats) is the only real
  precedent this repo has for "how much within-harness noise to expect at N=2 repeats" —
  useful for calibrating M2's own repeat count before committing budget to it.
- The bare-`pytest` gate-command sensitivity (§2) will very likely resurface in any future
  measured suite that reuses these same S0–S7 specs verbatim — known, not re-discovered.

---

## 5. File paths (entry points, don't read until needed)

- **M1 phase head (closed):** `meta_m1_harness/CLAUDE.md`.
- **Numbers + decision:** `meta_m1_harness/META_M1_RESULTS.md` + `META_M1_DECISION.md`.
- **Preregistration (structural model for a future M2 one):** `meta_m1_harness/META_M1_PREREGISTRATION.md`.
- **Full M1 plan (structural model for a future M2 plan):** `docs/concepts/meta_m1_harness_plan.md`.
- **The cold fallback, if M2 wants a third comparison point:** `phase4_research/research/llm_openai_compat.py`.
- **Harness-neutral entry point:** `AGENTS.md` (repo root).
- **Roadmap Meta-Strang bucket:** `ROADMAP.md` → `## Meta-Strang`.

---

## 6. One sentence for a cold reader

M1 closed with a clean "no migration, and the fallback genuinely works" — every deviation
from its own plan is written down above, not buried in commit messages; M2, if the Nikinger
wants it, is a different, harder question (code quality, not gate-pass) that needs its own
preregistration, not a rerun of M1's.
