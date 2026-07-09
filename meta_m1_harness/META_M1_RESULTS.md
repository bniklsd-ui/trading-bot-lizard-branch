---
status: closed
purpose: Dated snapshot — measured M1 bake-off results (Step 8, §10 of the plan). Numbers,
  variance, noise-check, validity notes, context-portability annex, plus a Step-10 fallback
  smoke appendix. The Step-8 content is never edited after commit — corrections are a new,
  dated, superseding document; the Fallback section is a plan-specified additive append
  (§12 point 4), clearly dated and demarcated, not a correction.
read-when: auditing the M1 bake-off outcome, or applying the preregistered decision rule
detail: L2
up: ./CLAUDE.md
updated: 2026-07-09
---

# META_M1_RESULTS — measured 2026-07-09

Measured against `meta_m1_harness/META_M1_PREREGISTRATION.md` (committed 2026-07-08, before
any trial ran). Design: S1–S5, 2 repeats, 2 harnesses = 20 trials. All 20 ran to completion —
no `BudgetExceeded` stop, no crash, no timeout.

## Headline table (from `analyze.py`, S1–S5 only — S0 excluded, spec-defined "ungemessen")

| Harness | gate_pass_rate | wall_s (mean±std) | real spend (USD) | edit_failures |
|---|---|---|---|---|
| claude_code | 0.90 (9/10) | 118.3±94.3 | $6.90 | 0 |
| opencode | 0.90 (9/10) | 154.5±101.7 | $4.37 | 0 |

**Gap = 0.00 pp.** Both harnesses tied exactly at 90%.

## Noise check (preregistered rule)

Within-harness spread (max − min `gate_pass_rate` across the 2 repeats, per harness):
each harness has exactly one failing trial out of 10, both landing in **S1** — spread per
harness = 1/5 (one repeat 100%, the other 80%, within S1) — larger than the 0.00 pp
between-harness gap. Per the preregistered noise rule: **the gap is reported as "not
distinguishable," not as a winner/loser.**

## Per-step gate detail

| Step | claude_code (r1, r2) | opencode (r1, r2) |
|---|---|---|
| S1 — Modelle+Taxonomie | ❌ ✅ | ✅ ❌ |
| S2 — Klassifizierer | ✅ ✅ | ✅ ✅ |
| S3 — Persistenz | ✅ ✅ | ✅ ✅ |
| S4 — reflect (AI-Naht) | ✅ ✅ | ✅ ✅ |
| S5 — Sink+Wiring (Cross-File) | ✅ ✅ | ✅ ✅ |

Both harnesses' single failure is on S1, and both failures share the same root cause,
independently reproduced: the harness's gate command (`_STEP_GATE_ARGV`) invokes a bare
`pytest phase10_v3/tests/test_models.py -q` — this does **not** add the repo root to
`sys.path` (unlike `python -m pytest`, which the agents themselves used for their own
self-verification in some trials). Whether the `phase10_v3.abstain_lessons.*` import then
resolves depends on `__init__.py` package markers, which S1's own "Scope-Grenzen" wording
leaves to agent judgement ("kein `__init__.py` über das hinaus, was `phase10_v3/` als
importierbares Paket braucht"). The trial that added the markers passed; the trial that
didn't, failed. From S2 onward every trial added them and both harnesses ran gate-clean.
**Not treated as a gate-command bug** (see Session-stopped block, 2026-07-09, in
`CLAUDE.md`): the gate command is the literal text shown to every agent as "Gate-Kommando",
and the rest of this project's own phases already carry proper `__init__.py` markers — a
harness correctly reproducing that convention is inside the intended measurement, not noise
introduced by the instrument.

## Validity notes

- **Effort/permission parity:** both harnesses ran `claude-sonnet-5` at the highest settable
  effort (`--effort high` / `--variant high`, M1-D4-corrected 2026-07-08) with non-interactive
  auto-approve (`--dangerously-skip-permissions` / `--auto`) — symmetric, both defensible only
  inside the M1-D8 fork isolation.
- **Usage capture:** all 20 trials parsed a real authoritative cost from the harness's own
  JSON output (`total_cost_usd` / summed per-step `cost`) — zero fallback to the manual-spend
  prompt, zero `null` `usage_tokens`.
- **Isolation:** confirmed against two independent real incidents this session (2026-07-09) —
  the `--dir`+lockdown fix (added after a real OpenCode live-repo escape on 2026-07-08) held
  across all 20 trials; `git status` in the live repo stayed clean throughout, verified after
  every batch.
- **Console-reported vs. computed spend — reconciled:** initial operator eyeball of the
  console (~$7, Sonnet-5 line item, S2–S5 slice) looked lower than this document's own
  per-trial sum ($9.30). Checked for a double-counting bug in OpenCode's per-step `cost`
  summing (`findall`+sum over NDJSON `step_finish` events) and found none (35 per-step values
  in a sampled S5 trial are non-monotonic — real per-step costs, not a cumulative running
  total re-summed). Operator then read the console's exact total-for-today: **$9.27**, a 0.3%
  match against this document's $9.30. Confirms the per-trial JSON-sourced figures here are
  accurate; the earlier "~$7" was an imprecise glance, not a real discrepancy.
- **Small unexplained Haiku charge (~$0.08) on the same key:** confirmed **not** hidden inside
  any trial's own cost accounting — every `claude_code` trial's `modelUsage` field lists only
  `claude-sonnet-5`, and neither harness config ever specifies a Haiku model. All "haiku"
  string matches in the trial logs are prose/docstring content the agents wrote or read (e.g.
  citing `phase7_reward`'s existing Haiku-based `reflect()` pattern), not evidence of a live
  Haiku call. Most likely a small internal housekeeping call from the `claude`/`opencode` CLI
  tooling itself (e.g. session-title generation) outside the harness's own visible token
  accounting — does not affect this document's totals.

## Annex — context portability (M1-D11, qualitative)

Question: did OpenCode (a harness with no native CLAUDE.md auto-loading, unlike Claude Code)
actually follow the `preamble.txt` instruction — *"Lies CLAUDE.md und referenzierte Dateien
nur bei Bedarf (@ref on need-to-know)"* — the same doc-layers navigation pattern `AGENTS.md`
(Step 9) is meant to generalize?

**Yes, and selectively — not a blanket read-everything habit:**

- **S2 (Klassifizierer, fully self-contained spec):** zero `CLAUDE.md` reads in either repeat.
  Correct — S2's own spec has everything needed, no cross-phase contract to look up.
- **S4 (reflect-Variante, the one AI-seam):** opened `phase7_reward/CLAUDE.md` in both
  repeats — the phase head documenting Phase 7's existing Haiku-based `reflect()` pattern
  (Decision E), i.e. it went looking for prior art for the *one* AI-touching piece of the spec
  before writing `LessonExtractor`, unprompted by anything in S4's own (self-contained) text.
- **S5 (Sink+Wiring, the cross-file edit into `phase5_execution/`):** opened
  `phase5_execution/CLAUDE.md` in both repeats — the phase head documenting the gates/VETOs
  it needed to hook `abstain_sink` into, again unprompted by S5's own spec text (which is
  self-contained by design and doesn't name that file).

This is the qualitative portability evidence M1-D11 asks for: OpenCode used the doc-layers
head-card navigation (`up:`/`down:` links, phase heads) exactly where it had a genuine
cross-phase information need, and skipped it where the spec was already sufficient — the same
selective behavior `AGENTS.md` (Step 9) is meant to make reproducible for any harness, not
just Claude Code's native auto-load.

---

## Fallback — Step 10 operator smoke (appended 2026-07-09, additive, Step-8 content above unchanged)

Per plan §12 point 4: the operator-run smoke test result, logged verbatim. Two real runs
against OpenRouter, both via `phase4_research/scripts/openrouter_smoke.py` (`OpenAICompatLLMClient`,
the real `research.prompt.build_prompt`, the real `research.validator.validate_candidate`):

**Run 1 — `tencent/hy3:free` — FAIL (model capability, not an adapter bug):**
```
FAIL model=tencent/hy3:free reason=OpenRouter call failed: _HTTPStatusFault('HTTP 400:
{"error":{"message":"Provider returned error","code":400,"metadata":{"raw":"{\"code\":400,
\"reason\":\"INVALID_REQUEST_BODY\",\"message\":\"Model 'tencent/hy3' does not support
'json_object' response format. Supported formats: json_schema.\",\"metadata\":{}}",
"provider_name":"Novita","is_byok":false}
```
This model (via its Novita backend) only supports the stricter `json_schema` response
format, not the `json_object` mode this adapter deliberately uses (the locked plan's design
choice — see `llm_openai_compat.py`'s module docstring). **Not a defect:** the adapter
correctly classified this as a non-transient 400 and raised `LLMResponseError` immediately
with zero wasted retries — the same behavior `test_bad_request_400_raises_immediately_no_retry`
asserts on a mocked response, now confirmed against a real provider. Some fraction of
OpenRouter's catalog will fail this way; picking a `json_object`-capable model (as Run 2 did)
avoids it.

**Run 2 — `nvidia/nemotron-3-ultra-550b-a55b:free` — PASS (valid abstain):**
```
PASS (valid abstain) model=nvidia/nemotron-3-ultra-550b-a55b:free tokens=in=572 out=349
```
A genuine end-to-end round trip: real HTTP call → JSON parse (fence-strip path) → the real
`validate_candidate` → a legitimate `abstain=true` response, correctly recognized as
`valid=True, candidate=None`. Cost logged as $0.00 (no pricing row for this model in
`ResearchConfig.pricing_usd_per_mtok` — the meter's documented graceful-unknown-model
behavior, not a crash) — consistent with the model being OpenRouter's free tier.

**Caveat (honest reporting):** this run exercised the abstain branch of the validator, not
the full pick branch (epic/direction/confidence fields) — the model chose not to pick. The
plumbing this smoke test exists to prove (prompt → OpenRouter → parse → validator) is fully
exercised either way; a pick-branch round trip was not additionally forced.

**Conclusion:** Step 10 smoke-PASS achieved (plan §12 acceptance). The adapter stays cold —
`phase4_research/scripts/wiring.py` is untouched, nothing here is wired into any live path.
