# Phase 8 → v1.6 Hotfix — Handover

> **Audience:** the next Claude Code (or a Claude-web planning) session that will diagnose
> and fix the v1.6 issues. **Author:** Claude Code, 2026-07-02, from the operator's first
> live v1.5 daemon run + a read-only look at the code (code = source of truth).
> **What this file is:** an honest statement of what the v1.5 hotfix *delivered*, what it
> *still failed to produce* live, and the concrete blocker that surfaced on the first run
> — plus directions and open questions for v1.6. It is **diagnosis + options, not a fix.**
>
> **Why a fresh session:** the real troubleshooting needs deep, cross-phase work (P3 data
> layer + instrument onboarding), and — critically — **there is no real logging/observability
> yet**, so the exact root cause can't be pinned from the current raw yfinance stderr. v1.6
> should treat "add real logging first" as step zero.

---

## 0. TL;DR

v1.5 shipped all three planned **code** fixes (B clamp/floor, C 4-instrument universe, A
lesson provenance) — merged to `main` with honest flags. But on the **first live daemon run
(2026-07-02)** two of the four instruments (**CAC 40 `^FCHI`, IBEX 35 `^IBEX`**) produce a
storm of yfinance errors — `possibly delisted; no price data found (period=1d)` — so their
Phase-3 **brain context degrades to `None`** (reduced-signal). This is **exactly the risk
flagged (but never operator-verified) at the end of the Step-2 variety work**: those two
tickers were "well-known public symbols, **not** live-verified," unlike DAX `^GDAXI` and
Euro Stoxx 50 `^STOXX50E` (both verified). The **net-new autonomous open→close** (v1.5's
whole point) is therefore **still not proven live**, now additionally hampered by degraded
signal on half the universe.

**It is NOT a hard crash** — the fetcher falls back to the last daily close and the daemon
keeps running; DAX + Euro Stoxx 50 still get full context. And it is **NOT the v1.5
provenance code** — that layer is fine. It is a **data-layer / instrument-onboarding** gap.

---

## 1. What v1.5 delivered (verified: code + mocked tests; merged to `main`)

All three blockers from `PHASE8_V1.5_HOTFIX_HANDOVER.md` were addressed. No new AI; VETOs/gates
untouched; demo-only preserved.

- **B — Clamp/Floor (`phase4_research`)**: `enable_long_bias_clamp` True→**False**,
  `confidence_floor_low_score` 70→**55**, decoupled floor boundary (`confidence_floor_below_score`).
  Data-collection mode, provisional, re-baseline before live.
- **C — Variety (`research.models.EXTENDED_UNIVERSE`)**: DAX + Euro Stoxx 50 + CAC 40 + IBEX 35
  (4 EUR instruments), per-epic brain context, per-epic `point_value` seam in P5 Gate-4, wiring
  opts P4/P8 into it. **⚠ see §2 — two of the four are not actually usable for signal yet.**
- **A — Lesson provenance (`phase7_reward`/`phase5_execution`/`phase2_persistence`/`phase4_research`)**:
  `OpenedTrade.provenance` (write-path) → `market_context_json` blob (no migration); read-path
  `db.get_recent_lessons_for_prompt(...)` filters verification-trade lessons out of the P4 prompt
  (tag + hold-time + reversible date quarantine); reward/score math untouched. + webui provenance
  badge (display-only).
- **Tests (mocked, green at merge):** P1 52 · P2 67 · P3 72 · P4 122 · P5 154 · P6 70 · P7 131 · P8 182.

---

## 2. What v1.5 still FAILED to produce (the live gap + the new blocker)

### 2a. The concrete blocker — yfinance `^FCHI` / `^IBEX` return no data
Operator's first live run (2026-07-02) log (excerpt):
```
ERROR yfinance: $^IBEX: possibly delisted; no price data found  (period=1d)
WARNING external_data.fetcher: empty/short data for ^IBEX (got 0, want >= 4, attempt 2/3)
...
WARNING external_data.fetcher: brain_context: momentum unavailable for IX.D.IBEX.IFM.IP
WARNING external_data.fetcher: intraday price unavailable for ^IBEX; using last daily close
```

**Code path (read-only trace):**
- P4 `context_builder._safe_brain_context` → P3 `MarketDataFetcher.get_brain_context(epic)` →
  `external_data.fetcher` downloads the mapped yFinance symbol.
- Ticker map (`phase3_external_data/external_data/ticker_map.py`): `IX.D.CAC.IFE.IP → "^FCHI"`,
  `IX.D.IBEX.IFM.IP → "^IBEX"` (added in Step 2; commented "well-known, **not** live-verified").
- On empty data the fetcher retries 3×, then degrades that epic's brain context to `None`
  (concept C3 "reduced-signal, tolerated") — the epic is **not** dropped from the universe
  (tradeability comes from the broker probe, a separate path), it just reaches the LLM with
  `n/a` signals.

**Effect:** the "variety" that v1.5 added is **half-effective** — DAX (`^GDAXI`) and Euro Stoxx 50
(`^STOXX50E`, live-verified) get full brain context; **CAC 40 and IBEX 35 get none**, plus the
run is flooded with yfinance error noise.

**Root cause: unknown / not yet pinned** (hence a fresh session). `^FCHI` and `^IBEX` *are* the
standard Yahoo symbols for CAC 40 / IBEX 35, so a wrong-string theory is not obvious. Candidate
hypotheses for v1.6 to test (see §3).

### 2b. Still unproven live (carried from v1.5, unchanged)
- ❌ A **net-new autonomous open→close** in one clean run (the whole point of v1.5).
- ❌ A **safety breaker actually tripping** live.
- ❌ Multi-day behaviour; ❌ any edge/profitability (never in scope).

These were the v1.5 live goals; the run has not demonstrated them, and the degraded signal on
half the universe works against getting there.

### 2c. The meta-gap — no real logging/observability
The only signal today is raw yfinance/fetcher stderr WARNINGs. There is **no structured,
per-cycle, per-epic record** of "which instrument got full/degraded/no context and why," no
persisted daemon run log, and the abstain reason taxonomy is still the coarse v1 two-bucket
(`LLM_ABSTAIN`/`PREFLIGHT_FAIL`). Diagnosing *why* the bot does or doesn't trade over a
multi-day run is currently guesswork. **This is why v1.6 troubleshooting needs its own session.**

---

## 3. Suggested v1.6 directions (for the plan to refine — NOT decided)

Dependency-ordered; the planner should turn each into concrete steps.

1. **Step 0 — real logging/observability first (the enabler).** Before chasing the yfinance
   issue, give the daemon a structured run log: per-cycle, per-epic brain-context outcome
   (full / degraded-to-None / which signals missing), the research decision + reason, and the
   fetcher's actual failure detail — to `data/state/` and/or the webui. Without this, v1.6 is
   blind. (Likely P3 fetcher + P8 scheduler + a diagnostic script; additive.)
2. **Step 1 — run the P3 verification that was skipped.** The last two sessions explicitly
   flagged (never done): `python phase3_external_data/scripts/smoke_test.py --epic IX.D.CAC.IFE.IP`
   and `--epic IX.D.IBEX.IFM.IP` against real yfinance. That pass would have caught this *before*
   the live run. Do it, capture what yfinance actually returns for `^FCHI`/`^IBEX` (and try a
   bare `yf.download("^IBEX", period="1d")` / different `period`/`interval`).
3. **Step 2 — fix or drop, per the finding:**
   - If the symbol/period is the issue → correct the `TickerMapper` entry (cross-phase P3 edit)
     and/or the fetcher's request params; re-verify.
   - If yfinance simply won't serve these indices reliably → **drop CAC 40 + IBEX 35 from
     `EXTENDED_UNIVERSE`** (revert to the two verified instruments DAX + Euro Stoxx 50) so the
     universe is honest and quiet, and reconsider variety via a different verified instrument.
     Both are deep-ish, additive cross-phase edits (`research.models.EXTENDED_UNIVERSE` +
     `ticker_map` + tests + the derived P5 `point_values`).
4. **Step 3 — re-attempt the live proof (Step 5 of v1.5)** once signal is clean: variety run for
   the net-new open→close + a tight-cap breaker-fire run.
5. **Still open from v1.5 (carry):** `point_value` for STXE/CAC/IBEX remain **inferred** from IG's
   "(X€)" naming, not independently confirmed — confirm before any live account.

**Guardrails (unchanged, non-negotiable):** no new AI; VETOs/gates/demo-lock untouched; additive
cross-phase seams with dated notes; each phase's tests stay green; live/network runs are the
operator's job.

---

## 4. Merge recommendation (what this session did)

**Merged `phase8-v1.5-hotfix` → `main` now, flagged honestly** (same tactic as the Phase-8
merge): v1.5's *code* is complete + mocked-green and shouldn't sit on a branch; the remaining
work is a **different concern** (data-layer instrument onboarding + observability), better tracked
as v1.6 on a fresh branch than as an open v1.5 tail.

- ✅ **Verified:** the three v1.5 code fixes (B/C/A) + provenance UI, all mocked tests green.
- ⚠️ **NOT verified / carried to v1.6:** a net-new autonomous open→close live; a breaker tripping
  live; multi-day behaviour; edge/profit. **New blocker:** `^FCHI`/`^IBEX` yfinance failure →
  CAC/IBEX brain context degraded (half the universe reduced-signal). **Meta:** no real logging yet.
- **Do NOT claim:** that the 4-instrument variety works end-to-end (2 of 4 are signal-degraded);
  that the bot trades autonomously in production (still unproven); any profitability.

---

## 5. Key file/line anchors (verified 2026-07-02, code = source of truth)

| Concern | File |
|---|---|
| yFinance ticker map (the unverified `^FCHI`/`^IBEX` entries) | `phase3_external_data/external_data/ticker_map.py` (`_MAP`) |
| The fetch/retry/degrade path that logs the errors | `phase3_external_data/external_data/fetcher.py` |
| Per-epic brain-context guard (degrade to None) | `phase4_research/research/context_builder.py` (`_safe_brain_context`) |
| The 4-instrument universe | `phase4_research/research/models.py` (`EXTENDED_UNIVERSE`) |
| P3 operator verification (the skipped pass) | `phase3_external_data/scripts/smoke_test.py` |
| Autonomous research trigger + abstain classification (coarse v1 taxonomy) | `phase8_scheduler/scheduler/research_tick.py` |
| Momentum VETO source — **IG real-time bars, NOT yfinance** (so this issue does NOT weaken the VETO) | `phase5_execution/execution/vetos.py` |

---

*End of handover. v1.6 = observability first, then verify/fix the `^FCHI`/`^IBEX` data (or drop
them), then re-attempt the live open→close proof.*
