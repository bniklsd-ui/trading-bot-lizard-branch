# Phase 8 → v1.5 Hotfix — Handover for the Concept/Planning Session

> **Audience:** the Claude **browser/web** concept session that will turn this into a
> detailed, step-by-step v1.5 implementation plan (then handed back to Claude Code).
> **Author:** Claude Code, 2026-06-30, from a read-only analysis of the live code
> (code = source of truth). **No code was changed to write this file.**
>
> **What this file is:** a grounded problem statement + suggested resolution directions
> for the three reasons Phase 8 has not yet produced a *net-new, meaningful* autonomous
> demo trade. It is deliberately **diagnosis + options + open questions**, not a finished
> plan — the plan is the browser session's job.
>
> **What this file is NOT:** an implementation. It does not pick the final knob values,
> does not write code, and does not merge anything.

---

## 0. TL;DR for the planner

Phase 8 (the autonomous scheduler) is **code-complete, 181 tests green, and mechanically
proven** end-to-end. It is **merge-ready with honest flags** (see §6). What it has **not**
done is open+close a *net-new autonomous* demo trade inside one clean run, because the bot
almost always **abstains**. Three root causes, in priority order:

| # | Nikinger's words | Root cause (code) | Where the fix lives |
|---|---|---|---|
| **C** | "needs more variety of what to trade" | **Universe = 1 instrument.** `epic_allowlist = ("IX.D.DAX.IFMM.IP",)` | P4 `research` + P3 `ticker_map` (config + curated data) |
| **B** | "initial BUY/SELL signal too strong … should differentiate" | **Two clamps fire together below score 50**: long-bias forces BUY-only **and** confidence floor jumps 55→70 → forced abstain | P4 `candidate_filter` + `ResearchConfig` |
| **A** | "lessons are not real lessons" | **Code-verification trades feed lessons back into the prompt** with no quarantine | P7 `reward` + P4 `context_builder` |

**The single highest-leverage change is C** (variety). With one instrument and a
conservative direction clamp, the bot has almost nothing it is *allowed* to pick, so it
abstains and collects zero data — exactly what the mission warned about.

**Cross-cutting guardrail for all three:** the project's core principle ("so wenig AI wie
möglich") and the hard rules (demo-only, no VETO bypass, AI never triggers an order
directly) must survive untouched. **v1.5 adds no new AI** — it widens the *deterministic*
inputs the existing single research call chooses from, and tunes *deterministic* gates.

---

## 1. Where Phase 8 actually stands (honest state for the merge decision)

Pulled verbatim-in-spirit from `phase8_scheduler/CLAUDE.md` → `## Session stopped — 2026-06-29`.

### Proven (live, 2026-06-29 operator run `RESULT 3/3`)
- ✅ **Daemon lifecycle** — preflight → bounded loop → clean shutdown, no exception/orphan.
- ✅ **State persistence** (`scheduler_state.json`, all fields, atomic).
- ✅ **Autonomous *real* P4 research ran** (Sonnet) and produced a **correct fail-safe
  ABSTAIN** in the conservative regime (score 45.83 < 50 → floor 70, by design — not a bug).
- ✅ **Reconcile + reward loop on 2 real prior demo trades** — IG history fetched, P&L
  back-filled, real Haiku lessons extracted (`open→close→reward→lesson` on real outcomes).
- ✅ **Token budget now armed by default** (`200_000` ≈ €0.8/day runaway breaker).

### NOT yet proven (the gate that has been blocking the ✅-flip)
- ❌ A **net-new autonomous trade opened *and* closed in one clean run** (research abstained
  both cycles → the auto-confirm/order path from a *fresh* autonomous candidate was never
  observed end-to-end in a single run).
- ❌ The **safety breakers actually tripping** (no loss occurred; budget was off that run).
- ❌ **Multi-cycle / multi-day behaviour** (only 2 bounded cycles).
- ❌ **Edge / profitability** (never in scope — long-run live operation).

### Why this matters for v1.5
The first three "not proven" items are blocked by the **same thing**: the bot abstains too
often to generate the trades that would exercise them. **Fixing C/B/A is what unblocks the
remaining live proof** — not more scheduler code.

---

## 2. Issue C — Variety of what to trade (**the main blocker**)

### Diagnosis (code-anchored)
- The research universe is a **single epic**:
  - `phase4_research/research/models.py:320` →
    `epic_allowlist: tuple[str, ...] = ("IX.D.DAX.IFMM.IP",)`
  - Concept Decision 5 (P4 `CLAUDE.md`): "**Epic universe = hybrid, code-curated** …
    **No** `search_markets("DAX")` dragnet." The default is intentionally one confirmed
    DAX-CFD epic, with the docstring noting "**room for 1-2 curated siblings (which then
    also need a `TickerMapper` entry)**" (`models.py:285-286`).
- `context_builder.build_context` probes **only** the allow-list epics
  (`phase4_research/research/context_builder.py`), so the LLM is handed a one-row
  instrument table and can only pick that row or abstain.
- Net effect: every cycle is "DAX, BUY or SELL, or nothing." With the §3 clamp on top,
  it collapses to "DAX BUY, or nothing." Almost always nothing.

### What "more variety" requires (the real surface area — for the planner to scope)
Adding an instrument is **not** a one-line config change; it touches a curated chain. For
**each** new epic the planner must account for:

1. **P4 `epic_allowlist`** — add the IG epic string (`ResearchConfig`, `models.py:320`).
   Confirm the epic exists + is tradeable on the IG **demo** account (operator task; this
   is how `IX.D.DAX.IFMM.IP` was confirmed in Phase 1).
2. **P3 `TickerMapper`** — `phase3_external_data/external_data/ticker_map.py` maps each IG
   epic → its yFinance symbol so `get_brain_context(epic)` can return drift/momentum/etc.
   An unmapped epic raises `EpicNotMappedError` (P4 guards it → that epic silently drops
   from the universe). **No mapper entry = no brain context = effectively no candidate.**
3. **Volume proxy (optional)** — index symbols (e.g. `^GDAXI`) report no native volume;
   P3 uses an ETF proxy (`EXS1.DE`) registered in wiring. A new index instrument may need
   its own proxy or will run with `volume_z_score = None` (tolerated, just weaker signal).
4. **Sizing / risk sanity** — P5 sizing is risk-per-trade ÷ stop-distance. A different
   instrument has a different point value / min deal size / typical stop distance. Confirm
   the existing config produces a sane size ≥ `min_deal_size` for each new instrument
   (Phase-5 `CLAUDE.md` already flagged sizing as v1-tunable).
5. **Spread / tradeability filter** — `context_builder` already drops epics that fail
   `market_status == TRADEABLE`, `spread_pct ≤ max_spread_pct`, or `currency == "EUR"`.
   A non-EUR instrument is dropped today; decide whether v1.5 keeps EUR-only.

### Suggested direction (options to decide in the plan)
- **Option C1 — minimal, safe (recommended starting point):** add **1–2 curated DAX-
  adjacent instruments** the operator can confirm on IG demo (e.g. a second DAX
  contract/related index already known-tradeable), each with its `TickerMapper` entry and
  (if an index) a volume proxy. Keeps the "code-curated, no dragnet" decision intact.
- **Option C2 — broaden the asset set:** add a small curated basket across uncorrelated
  underlyings (an index, a major FX-CFD, a commodity-CFD). Higher payoff for "variety" but
  more per-instrument validation (mapping, proxy, sizing, EUR question) and a bigger
  prompt. Probably a **v1.6**, not v1.5.
- **Explicitly out of scope (keep deferred):** the `search_markets` dynamic-universe
  dragnet — Decision 5 rejected it on purpose (hallucination + cost surface). Don't revive
  it in a hotfix.

### Open questions for the planner
- Which exact IG-demo epics will the operator confirm as tradeable + EUR-denominated?
- Do all candidates need full P3 brain context, or is a reduced-signal instrument
  (volume `None`) acceptable to widen variety faster?
- Does the confidence floor / clamp (§3) need per-instrument tuning, or one global set?

---

## 3. Issue B — The BUY/SELL signal is too strong (can't differentiate)

### Diagnosis (code-anchored)
The bot can't "do a different trade" when the market is "technically BUY" because **two
deterministic clamps fire together** the moment `bot_score < 50`:

1. **Direction clamp → BUY-only** (Decision 7, default ON):
   - `ResearchConfig.long_bias_below_score = 50.0`, `enable_long_bias_clamp = True`
     (`phase4_research/research/models.py:322-323`).
   - `candidate_filter.resolve_allowed_directions(...)`
     (`phase4_research/research/candidate_filter.py:70+`): when enabled and
     `bot_score < long_bias_below_score`, the permitted set is clamped to `("BUY",)`. SELL
     is removed from both the prompt's schema enum **and** the deterministic filter — the
     LLM literally can't offer a short.
2. **Confidence floor jumps 55 → 70** in the same regime:
   - `confidence_floor_default = 55.0`, `confidence_floor_low_score = 70.0`
     (`models.py:328-329`); `confidence_threshold(...)` returns the **70** floor when
     `bot_score < 50` (`candidate_filter.py:47-66`).
   - This is exactly what abstained the 2026-06-29 live run: real Sonnet call, market score
     45.83 < 50 → floor 70 → the model's self-report stayed under it → abstain.

So below neutral score, the bot is simultaneously **forced long** and **held to a stricter
bar** — the worst combination for "differentiate and maybe take a contrarian trade." The
two knobs were designed conservatively (avoid shorting into a down-bias; Phase 7 was meant
to replace the blunt floor with outcome-anchored confidence), but they currently over-clamp.

### Note: the differentiation machinery already exists downstream
- The **P6 Bull/Bear/Judge debate** *can flip* the direction (judge emits the final
  `direction`, may flip BUY↔SELL — Phase 6 Decision B). But the debate only runs on a
  **candidate that was generated**. If the clamp + floor abstain before a candidate exists,
  the debate never gets the chance to differentiate. **Loosening the P4 gate is what lets
  the existing debate do the nuanced work the Nikinger is asking for.**

### Suggested direction (options to decide in the plan)
- **Option B1 — decouple the two clamps:** treat "which directions are allowed" and "how
  high is the confidence bar" as independent. E.g. keep a (gentler) floor but allow SELL
  below neutral, or vice-versa. Today they're hard-coupled at the same `50.0` boundary.
- **Option B2 — relax the conservative regime:** lower `confidence_floor_low_score` toward
  `confidence_floor_default`, and/or widen `long_bias_below_score` so the clamp engages
  only in a *strongly* biased market (e.g. score < 35), not merely below neutral.
- **Option B3 — let the debate be the differentiator (recommended pairing):** keep P4's
  gate permissive enough to *generate* a candidate, and lean on the **already-built** P6
  debate + the 4 deterministic VETOs to be the real direction check. This matches the
  architecture's intent (P4 = "which candidate?", P6 = direction adversarial check) and
  adds no new AI.
- **Disable-clamp toggle for the data-collection phase:** `enable_long_bias_clamp = False`
  is already a supported config flag — the plan could turn it **off for demo data
  collection** (still demo-only, still VETO-gated), then re-baseline with outcome data.

### Hard guardrails (must hold)
- These are **gate-tuning** changes, not VETO changes. The four VETOs
  (`execution/vetos.py`) and the 5-gate pipeline stay **untouched** — loosening a research
  floor must never loosen a safety VETO.
- LLM `confidence` remains **advisory**, never the order trigger (root rule 3). The
  deterministic `candidate_filter` stays the gate.
- Any loosening is **demo-only** by construction (Phase 8's structural demo-lock) and must
  be re-baselined before any live account (the floor is provisional precisely because
  Phase 7 outcome-anchoring is meant to replace it).

### Open questions for the planner
- Where does `bot_score` come from and what's its live distribution? It's
  `db.get_current_score()` (P2). If it sits structurally below 50 most of the time, the
  conservative regime is the *default* regime, not the exception — which would make this
  the dominant cause of abstains. **Worth measuring before picking knob values.**
- Should the relaxed values be permanent, or a **temporary "data-collection mode"** that
  reverts once enough real outcomes exist to anchor confidence (Phase 7/9)?

---

## 4. Issue A — Lessons are not real lessons

### Diagnosis (code-anchored)
- The P7 brain extracts a free-text lesson after **every** closed trade
  (`phase7_reward/reward/brain.py`, one Haiku call, best-effort). The earlier demo trades
  were **code-verification trades** — e.g. forced SELL seeds, opened only to prove the
  place→monitor→close path, time-stopped after ~1 minute. Lessons distilled from those
  describe the *test harness*, not a genuine market decision.
- Those lessons then **feed straight back into the next research prompt**:
  - `phase4_research/research/context_builder.py:184` → `recent_lessons = db.get_recent_lessons(5)`
  - rendered into the prompt by `prompt._render_lessons` and marked used by P4's loop-closure
    write-back (`research.py` `mark_lesson_used`).
- So low-quality lessons aren't just cosmetic — they **pollute the input** to the single AI
  decision, biasing future picks on noise. The learning loop is wired correctly; it's being
  fed verification noise.
- **Note on the existing synthetic/real split:** P7 already has the *concept* of a data-
  source tag — `ClosedTrade.account` (`"demo"|"live"`, `models.py:145`) and
  `select_edge_set(include_demo_in_edge=...)` (`models.py:315`), plus a hard
  synthetic-DB-path guard (`guard_synthetic_path`). **But there is no "this was a
  verification/throwaway trade" flag**, and lesson *selection for the prompt*
  (`get_recent_lessons`) is **not** filtered by trade quality/provenance.

### Suggested direction (options to decide in the plan)
- **Option A1 — quarantine verification trades from the lesson pool (recommended):**
  introduce a provenance flag distinguishing *autonomous real-decision* trades from
  *operator/verification/seed* trades (the seed marker already exists:
  `"MANUAL SEED (not a real research pick)"`, `seed_candidate.py:62`). Then have
  `get_recent_lessons` (or a P4-side filter) **exclude lessons sourced from verification
  trades**. The reward/score math can still run on them; they just don't teach the prompt.
- **Option A2 — purge the existing polluted lessons:** the lessons in the DB today were
  born from verification trades. A one-shot, operator-run cleanup (or a "lessons before
  date X are quarantined") gives the autonomous run a clean slate. Pair with A1 so it
  doesn't re-pollute.
- **Option A3 — raise the bar for what becomes a lesson:** only call `reflect()` for trades
  that were genuine autonomous decisions with a real hold (not a sub-minute forced
  time-stop). Cheaper on Haiku tokens too.
- **The deeper truth (state honestly in the plan):** lessons only become *real* once there
  are **real autonomous outcomes** to reflect on — which is gated on fixing C + B first.
  A is partly a **sequencing** issue: fix variety + clamps → get real trades → get real
  lessons. A1/A2 stop the *old noise* from contaminating that.

### Hard guardrails (must hold)
- Lessons are **display/prompt context**, never a gate (root rule 3 — they already "gate
  nothing"). Any change stays additive and best-effort/fail-closed (the P7 discipline:
  errors `logger.critical`, never break the close path).
- Don't touch the synthetic-DB-path guard or the live/demo split — extend, don't rewire.

### Open questions for the planner
- Is "verification trade" best identified by the seed marker, by an explicit DB column, or
  by a heuristic (hold-time < N, operator-triggered)? A column is cleanest but touches P2
  (migration 003) — decide if that's in v1.5 scope.
- Purge vs. quarantine-by-date for the existing polluted lessons?

---

## 5. Cross-cutting constraints (the planner must honour all of these)

These are non-negotiable from `CLAUDE.md` (root + phase). A v1.5 plan that violates one is
wrong by construction.

1. **No new AI.** v1.5 widens *deterministic* inputs (universe) and tunes *deterministic*
   gates (clamp/floor) and *deterministic* data hygiene (lesson provenance). The only AI
   sites stay: P4 `ask_candidate`, P6 debate, P7 `reflect`. If a step reaches for an LLM to
   filter/score/decide — stop, it's code.
2. **AI never triggers an order directly** (root rule 3). The validator + `candidate_filter`
   + VETOs + auto-confirm chain stays in front of every order.
3. **Never bypass a VETO.** §3's loosening is *research-gate* tuning only. The 4 VETOs and
   5 gates in P5 are untouched.
4. **Demo-only, fail-closed.** Phase 8's structural demo-lock (config `account="demo"`,
   only `get_broker("ig_demo")`, `AutoConfirm` re-check) stays. All loosened knobs are for
   **demo data collection**; re-baseline before live (the floor/clamp are explicitly
   provisional pending Phase-7 outcome anchoring).
5. **Additive seams, phase isolation.** Cross-phase changes follow the established pattern:
   additive, default-unchanged, dated concept reconciliations, each phase's tests stay
   green. Touching P2 (a migration), P3 (ticker map), P4 (config/filter), P7 (provenance)
   are all *allowed* but each is a documented cross-phase edit, not a Phase-8 edit.
6. **Credentials only in the keyring. Don't rename `turbo_candidates.json`.** Standard.
7. **Live tests are the operator's job.** Claude Code does code + mocked tests; the
   Nikinger runs the IG-demo / network / real-LLM runs.

---

## 6. Merge recommendation (honest flags)

**Recommendation: merge `phase8-scheduler` → `main` now, flagged as
"code-complete, mechanically proven, autonomous-trade-unverified," and pursue C/B/A as the
v1.5 hotfix on a fresh branch.**

Rationale: Phase 8 the *scheduler* is done and green (181 tests). The remaining live proof
is blocked not by scheduler bugs but by the **research over-conservatism** (C/B) — which is
a *different concern* (the research/strategy layer), better tracked as its own hotfix than
as an open Phase-8 tail. Merging unblocks downstream work; the flags keep it honest.

### Flags to carry into `main` docs (ROADMAP / README / root CLAUDE.md)
- ✅ **Verified:** daemon lifecycle, state persistence, autonomous real-P4 research with
  correct fail-safe abstain, reconcile+reward loop on real prior demo trades, armed token
  budget, full safety *code paths* (unit-proven), read-only Web-UI.
- ⚠️ **NOT verified (carried to v1.5):** a net-new autonomous open→close in one clean run;
  safety breakers *actually tripping* live; multi-day behaviour; **any** notion of edge /
  profitability.
- ⚠️ **Known cause of the gap:** single-instrument universe + below-neutral double-clamp →
  near-constant abstain. This is the v1.5 hotfix, not a Phase-8 defect.

### Do NOT claim
- That the bot trades autonomously "in production" (it abstains).
- That lessons are meaningful yet (they're from verification trades).
- Any profitability / edge (never measured, never in scope).

---

## 7. Suggested v1.5 sequencing (for the plan to refine)

A dependency-ordered sketch — the browser session should turn each into concrete steps:

1. **Measure first (cheap, read-only):** what is the live `bot_score` distribution? How
   often is it < 50? This tells you whether B (clamp/floor) or C (universe) dominates, and
   what knob values are sane. *(Operator-run; no code.)*
2. **C — widen the universe (1–2 curated instruments):** P4 `epic_allowlist` + P3
   `TickerMapper` entries + volume proxy + sizing sanity per instrument. Biggest lever.
3. **B — relax/decouple the clamp + floor** for demo data collection (decouple direction
   from confidence; consider clamp-off mode). Lean on the existing P6 debate + VETOs for
   the real direction check.
4. **A — lesson provenance:** quarantine verification-trade lessons from the prompt
   (flag/filter) + purge the existing polluted ones. Best done *after* C/B so real lessons
   start flowing.
5. **Operator live run:** with variety + relaxed gates, capture the **net-new autonomous
   open→close** and (by setting a tight cap) watch a **safety breaker actually trip** — the
   two proofs that finally close the Phase-8 ✅ gate.

**If time/tokens get tight:** do C, then B. Variety + a permissive-enough gate is the
minimum that produces autonomous trades. A (lessons) and profitability tuning can follow.

---

## 8. Appendix — key file/line anchors (verified 2026-06-30, code = source of truth)

| Concern | File:line |
|---|---|
| Single-epic universe default | `phase4_research/research/models.py:320` |
| Universe docstring ("room for 1-2 curated siblings + TickerMapper entry") | `phase4_research/research/models.py:285-286` |
| Long-bias clamp config | `phase4_research/research/models.py:322-323` |
| Confidence floor config (55 / 70) | `phase4_research/research/models.py:328-329` |
| `confidence_threshold` (floor jumps below score 50) | `phase4_research/research/candidate_filter.py:47-66` |
| `resolve_allowed_directions` (BUY-only clamp) | `phase4_research/research/candidate_filter.py:70+` |
| Universe probe (only allow-list epics) | `phase4_research/research/context_builder.py` |
| Lessons fed into the prompt | `phase4_research/research/context_builder.py:184` |
| IG epic → yFinance ticker map (needs an entry per new epic) | `phase3_external_data/external_data/ticker_map.py` |
| Autonomous research trigger (where abstain is classified) | `phase8_scheduler/scheduler/research_tick.py` |
| Seed marker (how verification picks are tagged) | `phase5_execution/scripts/seed_candidate.py:62` |
| P7 trade provenance tag (`account` demo/live) + edge filter | `phase7_reward/reward/models.py:145, 315` |
| P7 lesson extraction (Haiku `reflect`) | `phase7_reward/reward/brain.py` |
| The 2026-06-29 conservative-abstain analysis | `phase8_scheduler/CLAUDE.md` → `## Session stopped — 2026-06-29` |
| 4 VETOs (must NOT be touched by v1.5) | `phase5_execution/execution/vetos.py` |

---

*End of handover. The browser concept session should produce the detailed, step-by-step
v1.5 plan from §2–§4 (resolutions) + §5 (constraints) + §7 (sequencing). Implementation
returns to Claude Code after the plan is locked.*
