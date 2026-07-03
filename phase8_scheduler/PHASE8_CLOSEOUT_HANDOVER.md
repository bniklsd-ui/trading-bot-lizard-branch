# Phase 8 Closeout → V2 Kickoff Handover

> **Author:** Claude Code, 2026-07-03, docs-only session (no code/tests touched).
> **Audience:** the browser (Konzept) planning session that turns this into a detailed
> V2 research plan, which a later Claude Code "Wie" session translates into build steps.
> **What this file is:** (1) an honest closeout of what Phase 8 achieved, mechanically
> and via the v1.5–v1.7 hotfix arc; (2) a **proposal** to reframe the roadmap's next
> tracks — V2 = autonomous epic research + reliable data input, V3 = persistence reform +
> no-trade lessons + UI, V4 = everything sophisticated/optional, deferred. This is
> **diagnosis + proposal, not a built plan** — same posture as
> `PHASE8_V1.5_HOTFIX_HANDOVER.md` / `PHASE8_V1.6_HANDOVER.md` before it.
>
> **Why this reframe now:** the operator (the Nikinger) noticed — again, on today's
> elongated live-test run — that yfinance data is intermittently unavailable for some
> instruments (`^FCHI`/`^IBEX`). Rather than hotfix that out of the current version a
> third time, the call is to stop patching symptoms and re-scope: the hotfix arc (§2)
> shows the same two structural gaps resurfacing under different names each time.

---

## §0 Purpose

Two jobs, in order:

1. **Close out Phase 8 honestly** — what's proven, what isn't, so nothing is silently
   dropped when the roadmap's focus shifts.
2. **Propose the V2/V3/V4 reframe** — so the browser session has a concrete starting
   point instead of the current ROADMAP's Phase-9 ordering (which front-loads
   sophisticated AI extensions before the data/universe foundation is solid).

No code changes, no fixes, no new AI in this session. Pure handover.

---

## §1 What Phase 8 achieved (mission: autonomous, unsupervised real demo trades)

### ✅ Proven (operator runs + mocks)
- Daemon lifecycle: preflight → bounded loop → clean shutdown, no orphan state.
- State persistence (`scheduler_state.json`, atomic writes, day rollover).
- **Autonomous real P4 research** (Sonnet) with correct fail-safe ABSTAIN under
  conservative scoring — not a mocked/seeded pick.
- Reconcile + reward loop on real prior demo trades (open→close→reward→lesson).
- A sharp, by-default token budget (runaway-cost breaker).
- A read-only web UI (file/DB-only control surface — can never touch trading directly).
- **The hard, previously-unproven core of the mission: a net-new autonomous
  open→close in one clean run** (2026-07-02, DAX BUY `deal_id=DIAAAAXW7U4AWAP` — real
  P4 pick → real P6 Bull/Bear/Judge debate → TRADE decision → ACCEPTED → broker-closed
  by SL/TP).

### ⚠ Still NOT proven
- **Trade quality** across multiple cycles (one trade proves mechanics, not
  consistency or edge).
- A safety breaker **actually tripping** live (the "5b breaker-fire run" from the
  v1.5 plan is still outstanding).
- Multi-day behaviour.
- Edge / profitability — **never in scope for Phase 8**, and still not in scope here.

### Honest status
🟡 — mechanically proven, live test intentionally still running (the Nikinger is
collecting trade-quality data via the v1.6 observability log rather than stopping at
the first "it trades"). **No ✅ doc-flip yet** — that remains the Nikinger's call.

---

## §2 The hotfix arc (v1.5 → v1.6 → v1.7) — what each tried to fix

### v1.5 — "the bot almost never trades" (near-constant abstain)
Three causes diagnosed and fixed:
- **C (main blocker) — single-instrument universe.** `epic_allowlist` had exactly one
  epic (DAX). Fixed: `EXTENDED_UNIVERSE` (4 EUR index CFDs: DAX, Euro Stoxx 50, CAC 40,
  IBEX 35), per-epic brain context, per-epic `point_value` seam in P5 sizing.
- **B — sub-50 double-clamp.** Below `bot_score` 50, two clamps fired together
  (long-bias → BUY-only, **and** confidence floor jumping 55→70) — near-impossible to
  clear. Fixed: decoupled the two knobs, relaxed both for data-collection mode.
- **A — verification-trade lesson leak.** Seeded verification trades' lessons fed
  unfiltered into the P4 research prompt via `get_recent_lessons`, biasing the LLM
  toward false-pattern abstains. Fixed: a `provenance` tag + a filtered prompt-read.

### v1.6 — "the fix from A wasn't complete" + observability
- **Found "Cause A part 2":** a **second, previously unnoticed** prompt channel —
  `context_builder.build_context` also read the raw `db.get_recent_trades(8)` table,
  ungated by any provenance filter, and fed the same three verification trades into
  the LLM's abstain reasoning ("three consecutive losses"). Fixed via a real
  `provenance` DB column (migration 003) + a filtered
  `get_recent_trades_for_prompt` read.
- **Added observability** (the meta-fix this arc kept needing): per-cycle,
  per-epic JSONL diagnostic log
  (`phase8_scheduler/scheduler/observability.py` → `data/state/research_health.jsonl`),
  plus `BrainContext.field_errors` (P3, the actual fetch exception per degraded field)
  and `ResearchContext.brain_context_health` (P4, per-epic full/degraded/unavailable +
  `missing`/`errors`).
- **Added an instrument-verification harness** (`scripts/verify_instrument.py`) —
  consolidates the IG-side probe (market info + real-time OHLCV) and the yFinance-side
  probe (daily/intraday/volume-proxy) into **one PASS/FAIL verdict per instrument**.
  Today it runs manually against the curated universe or an ad-hoc `--epic`; it is the
  **"validate" half** of an envisioned validate→promote pipeline (documented, not built).
- **Decision on `^FCHI`/`^IBEX`: tolerated, not fixed or dropped** — a stale yfinance
  version pin was corrected, but the intermittency itself (Yahoo-side, most likely
  rate-limiting) was left as-is, backed by the new observability so a recurrence is
  *visible* instead of silent. This is exactly the issue that resurfaced on today's
  run — tolerating it did not make it go away, it only made it diagnosable.
- **Direct result the same day: the first real autonomous trade** (§1).

### v1.7 — webui-only display fix
`/api/status`'s `trades_today`/`realized_pnl_today` were read from a lagging
`scheduler_state.json` snapshot instead of the DB — visible for the first time because
the 2026-07-02 trade was the first one to live long enough (~9 min IG settlement lag)
to expose the gap. Fixed: both fields are now DB-fed, mirroring `/api/trades` and the
already-correct loss-breaker query. No safety impact (DB/broker/loss-breaker were
already correct; only the display lagged).

### The through-line (why this handover proposes a reframe)
Three hotfix rounds, and **the same two structural weaknesses keep resurfacing under
different names**:

1. **Data-input reliability.** yfinance intermittency was "found" in v1.5's live run,
   "tolerated with observability" in v1.6, and is **back today** on the elongated
   v1.6/v1.7 live test — the same `^FCHI`/`^IBEX` symptom. It was never actually fixed,
   only made visible. Separately, the P1 Lightstreamer streaming client
   (`phase1_broker_wrapper/lightstreamer_ig_reference.md`,
   `lightstreamer_integration_notes.md`) was live-verified in Phase 1 but has **never
   been wired into the research/context data path** — P3/P4 rely entirely on yfinance
   (~15 min delayed) plus IG's real-time bars only for the momentum VETO, not for
   general signal quality.
2. **No autonomous epic discovery.** The universe is still a hand-curated tuple
   (`EXTENDED_UNIVERSE` in `phase4_research/research/models.py`). `verify_instrument.py`
   (v1.6) proves an instrument is *usable*, but nothing *finds* candidate instruments or
   *promotes* verified ones into the live universe automatically — that seam is
   documented but not built.

Both gaps sit **below** the sophisticated-AI work the current ROADMAP Phase 9 lists
next (Council, Bull/Bear/Judge handover-logic, Instinct-ECC). Building those on top of
an unreliable data layer and a static universe would just give the next set of hotfixes
a fancier failure mode.

---

## §3 The reframe — why

Current `ROADMAP.md` Phase 9 ("V2 Erweiterungen") lists, in order: 9a Council, 9b
Handover-Logik, 9c SQLite V2 extensions, 9d Reward/Punishment reform, 9e Force Trigger
safeguard, 9f Instinct-Promotion. This ordering was written before the v1.5–v1.7 arc
proved (repeatedly) that the actual bottleneck is upstream of all of that: **can the
bot reliably find good instruments and get clean data for them at all?**

**Proposal:** reorder around that finding. Foundation first (V2), then persistence +
learning-from-non-trades + UI polish (V3), then the sophisticated/optional work that
was originally Phase 9 (V4) — gated on the foundation actually holding up.

This is a **proposal for the browser session to formalize**, not a decision made here.

---

## §4 Proposed V2 — Autonomous Epic Research + Data-Input Reliability (the foundation)

### 4a. Real autonomous research for useful epics
Move from the hand-curated `EXTENDED_UNIVERSE` tuple to an actual
**validate → promote** pipeline:
- `scripts/verify_instrument.py` already does the *validate* half (IG + yFinance
  probes → one verdict). It explicitly documents (not builds) a v3 seam:
  `InstrumentSpec.source="research_promoted"` as the future promotion tag, with
  duck-typed, I/O-free check functions (`check_ig_side`/`check_yf_side`/`verdict_for`)
  already importable for reuse.
- What's missing: (a) a **discovery** step (candidate instrument search, not just
  verification of a pre-picked list) and (b) a **promotion** step (verified candidates
  entering `EXTENDED_UNIVERSE` — or its successor — without a manual code edit each
  time).
- **Guardrail carried forward unchanged:** this is still "which candidate" work,
  not sizing/gating — stays on the AI-does-research-only side of the Bauprinzip.
  No VETO/Gate touch.

### 4b. Reliable lightstreamer / yfinance rework
- yfinance intermittency (`^FCHI`/`^IBEX`, most likely Yahoo-side rate-limiting) has
  resurfaced across v1.5/v1.6/today — tolerating it with observability was a
  stopgap, not a fix. V2 should decide: harden the fetch/retry path structurally
  (backoff, circuit-breaker, multi-attempt spread over time) and/or **evaluate wiring
  the already-verified P1 Lightstreamer client into the data path** where it can
  improve signal quality beyond yfinance's ~15 min delay — build on the v1.6
  observability seams (`BrainContext.field_errors`, `ResearchContext.brain_context_health`,
  `research_health.jsonl`) so any future degradation is diagnosable immediately, not
  after a hotfix round.
- **Guardrail carried forward unchanged:** the momentum VETO already sources from IG
  real-time bars, never yfinance/Lightstreamer research data — this work is about
  *signal quality for research*, not a safety-layer change.

### Cross-cutting guardrails for V2 (unchanged project principles)
No new AI in the data/universe layer (Bauprinzip: discovery/promotion criteria are
code-evaluated, not LLM-decided); VETOs/Gates untouched; demo-only stays intact;
additive, tested, phase-isolated per the existing convention.

---

## §5 Proposed V3 — Persistence Reform + No-Trade Lessons + (optional) UI

- **DB reform** — the current ROADMAP 9c items: `market_regime_snapshots`,
  `decision_context` (currently empty placeholders since Phase 2), optionally
  `lesson_embeddings` for semantic lesson similarity.
- **No-trade (abstain) lessons** — extend P7's `reflect()` beyond CLOSED trades to
  ABSTAIN cycles, so "why didn't it trade" becomes a learnable signal, not just a
  discarded reason code. Groundwork already exists but is underused:
  - `phase8_scheduler/scheduler/research_tick.py` declares `REASON_EMPTY_UNIVERSE` /
    `REASON_VALIDATOR_REJECT` / `REASON_FILTER_FAIL` but only ever sets the two v1
    umbrella codes (`REASON_LLM_ABSTAIN`, `REASON_PREFLIGHT_FAIL`) — the finer
    taxonomy needs P4 to actually report which reason fired.
  - `research/research.py`'s `last_no_pick_reasoning` and
    `scheduler/state.py`'s `last_no_trade_detail` already surface the LLM's abstain
    prose for **display** (v1.6/UI work) — but nothing persists or reflects on it yet.
  - V3 would connect these: persist abstain context + reason, run `reflect()` (or an
    abstain-specific variant) on it, feed resulting lessons back — mirroring the
    closed-trade lesson loop.
- **UI enhancements** (optional) — building on the v1.6 observability log and the
  v1.7 DB-fed status fix; lower priority than the two items above.

---

## §6 Proposed V4 — Sophisticated / Optional (deferred)

Everything from the current ROADMAP Phase 9 not covered by V2/V3, plus any new
special functionality the Nikinger wants later: 9a Council Skill Integration, 9b
Bull/Bear/Judge Handover-Logik (context-window compression), 9d Reward/Punishment
reform beyond what P7 already delivered, 9e Force Trigger safeguard (the
`force_trigger_locked` schema field exists since Phase 2 but is enforced by no
function — a real gap, but not urgent since no Force Trigger function exists yet
either), 9f Instinct-Promotion (ECC) + Longterm VETO. All of this is **gated on real
outcomes** already per the existing ROADMAP language, and now additionally gated on
V2/V3 landing first — building Instinct-Promotion on top of an unreliable data layer
would promote noise into VETOs.

---

## §7 Carried-over open items (must reach the browser session)

- **5b — breaker-fire run.** A safety breaker has never been observed to actually
  trip live (tight-cap run from the v1.5 plan, still outstanding).
- **`point_value` for Euro Stoxx 50 / CAC 40 / IBEX 35 remain inferred**
  (from IG's "(X€)" naming convention), never independently confirmed against real
  contract details — must be confirmed before any live (non-demo) account use.
- **yfinance intermittency root cause still not conclusively pinned** — the v1.6
  diagnosis session ran two time-separated checks and found no reproducible pattern
  (both `^FCHI`/`^IBEX` fetches succeeded cleanly in the diagnosis run that followed a
  failed live run) — consistent with transient Yahoo-side rate-limiting, but not proven.
- **The Phase-8 ✅ doc-flip remains the Nikinger's call** — pending sufficient
  trade-quality data from the ongoing live test, not a technical blocker.

---

## §8 Next step + housekeeping note

**Next step:** V2 planning happens in the browser (Konzept session) — this handover is
its input. That session produces the detailed V2 research plan; a later Claude Code
"Wie" session turns it into concrete build steps, following the same two-stage
pattern used for the v1.6 hotfix (`docs/concepts/phase8_v1.6_hotfix_plan.md`'s §0a
explains the precedent).

**Explicit housekeeping note (not done in this session, flagged for the V2 track):**
Reshaping `ROADMAP.md`'s Phase 9 section into the V2/V3/V4 buckets proposed here is
the **initial housekeeping step of the V2 track** — mirroring the Step 0 / Step 0b
housekeeping that has opened every prior phase and hotfix round (legacy-grep,
doc-reconciliation) before any real build work started. This session deliberately
left `ROADMAP.md`'s content unchanged (only added a pointer to this file, see the
repo-wide pointer edits accompanying this handover) so the browser session decides
the actual bucket boundaries and phase numbering, rather than this session
pre-empting that call.

---

## §9 Key file anchors (the seams V2/V3 build on)

| Concern | File |
|---|---|
| The current hand-curated universe | `phase4_research/research/models.py` (`EXTENDED_UNIVERSE`, `InstrumentSpec`, `load_universe`) |
| Instrument validate-half (v1.6) — the seam to extend into validate→promote | `scripts/verify_instrument.py` |
| yFinance ticker map (the intermittent `^FCHI`/`^IBEX` entries) | `phase3_external_data/external_data/ticker_map.py` |
| Fetch/retry/degrade path + per-field error capture (v1.6) | `phase3_external_data/external_data/fetcher.py`, `external_data/models.py` (`BrainContext.field_errors`) |
| Per-epic brain-context health (v1.6) | `phase4_research/research/context_builder.py` / `research/models.py` (`ResearchContext.brain_context_health`) |
| Per-cycle/per-epic observability log (v1.6) | `phase8_scheduler/scheduler/observability.py` → `data/state/research_health.jsonl` |
| Abstain reason taxonomy (coarse today, the V3 no-trade-lessons seam) | `phase8_scheduler/scheduler/research_tick.py` (`REASON_*` constants) |
| Abstain prose (display-only today, not persisted/reflected-on) | `phase4_research/research/research.py` (`last_no_pick_reasoning`), `phase8_scheduler/scheduler/state.py` (`last_no_trade_detail`) |
| P1 Lightstreamer client — verified but not wired into the research data path | `phase1_broker_wrapper/lightstreamer_ig_reference.md`, `lightstreamer_integration_notes.md` |
| P7 lesson extraction (the pattern to mirror for abstain-lessons) | `phase7_reward/reward/brain.py` (`reflect()`) |

---

*End of handover. Diagnosis + proposal for the browser V2 planning session — no
code changed in this session.*
