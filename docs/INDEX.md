---
status: live
purpose: L0 map of every project .md — one line each; start navigation here
read-when: locating any doc, or deciding whether a file is worth reading at all
detail: L0
up: ../CLAUDE.md
down: every project doc (that is the point)
updated: 2026-07-06
---
# Doc Index (L0)

> **The layer model** (full spec: [DOC_LAYERS_CONVENTION.md](./DOC_LAYERS_CONVENTION.md)):
> **L0** = this index · **L1** = a living doc's ≤15-line header card (read via `Read` with
> `limit: 15` — decide from the card whether to descend, follow its `up:`/`down:` links to hop) ·
> **L2** = lean living bodies (≤40KB) · **L3** = archives & dated snapshots, read only when auditing.
>
> **Maintenance:** new .md file ⇒ add one line here in the same commit. Sizes are approximate.
> Oversize check: `find . -name "*.md" -not -path "./.agents/*" -not -path "*/.pytest_cache/*" -size +40k`
> — every hit must be a 📕/📦, never a 📗/🔄.
>
> Glyphs: 🔄 active-phase · 📗 live (maintained) · 📕 snapshot (dated, **never edit**) · 📦 archive (verbatim history).

## Root & governance
- [CLAUDE.md](../CLAUDE.md) — 📗 14KB · rules, conventions, working style, current state; auto-loaded every session
- [AGENTS.md](../AGENTS.md) — 📗 1KB · harness-neutral entry point for non-Claude-Code agents; points to `CLAUDE.md` + doc-layers navigation (M1 Step 9)
- [README.md](../README.md) — 📗 13KB · human overview + machine setup (venv, keyring, smoke test)
- [ROADMAP.md](../ROADMAP.md) — 📗 25KB · Phase 1–11 plan + status per phase
- [ARCHITECTURE.md](../ARCHITECTURE.md) — 📗 18KB · system layers, components, risks
- [HANDOVER_PROMPT.md](./HANDOVER_PROMPT.md) — 📗 · wiederverwendbarer Auftragstext für Phasen-Abschluss/-Deferral; seit 2026-08-11 auf Claude Code umgeschrieben (Repo statt Google Drive)
- [DOC_LAYERS_CONVENTION.md](./DOC_LAYERS_CONVENTION.md) — 📗 · generic (project-agnostic) doc-layers spec

## Active phases (10 — V3: Abstain-Lessons + Persistenz-Reform + Paper-Trades; 11 — V3-Fortsetzung: Funnel-/Mess-Fixes, lives in the same directory)
- [phase10_v3/CLAUDE.md](../phase10_v3/CLAUDE.md) — 🔄 phase head (covers both Phase 10 and Phase 11 work); Block A ✅ (Monday-restart-proof 2026-07-14) + Block B ✅ (market_context + Paper-Pipeline live 2026-07-17); Council-Paper-Call deferred; Phase 11 (2026-08-01, claimed from the deferred "V4" numbering — V4 is now Phase 12) — B1/B2/B5/B4(H6) fixed, B3 deferred, H1 (time-scheduled shadow pairs) built + wired default OFF, awaiting a live arm · [archive](../phase10_v3/SESSIONS_ARCHIVE.md)
- [phase10_v3/PHASE11_DEFERRAL_HANDOVER.md](../phase10_v3/PHASE11_DEFERRAL_HANDOVER.md) — 📕 **Notbremse 2026-08-11: Phase 11 DEFERRED** vor Erreichen ihrer Ziele. Status · Delta · Durability-Anforderungen A–G für den neuen Datenfundament-Track · offene Entscheidungen (u. a. Nummerierung). **Erstes Dokument der nächsten Session.**
- [docs/architecture/data_foundation.svg](./architecture/data_foundation.svg) — 📕 1080×1080: Fehlerbild (eine Tatsache, drei Speicher) + Zielbild (Anforderungen A–G); enthält den Befund, dass die Mehrquellen-Kette seit Phase 9 gebaut ist und nie lief
- [phase10_v3/STEP0_DATA_ANALYSIS_2026-07-10.md](../phase10_v3/STEP0_DATA_ANALYSIS_2026-07-10.md) — 📕 dated Step-2 data analysis (V2-baseline, abstain reasons, gap-check)
- [phase10_v3/WEEK1_REVIEW_2026-07-17.md](../phase10_v3/WEEK1_REVIEW_2026-07-17.md) — 📕 Step-8 catch-up review: abstain-record distribution + first live `REASON_DEBATE_ABSTAIN` cluster (reflect path unproven, watch item)
- [phase10_v3/TRADE_DATA_DIAGNOSIS_2026-07-19.md](../phase10_v3/TRADE_DATA_DIAGNOSIS_2026-07-19.md) — 📕 pre-V4 Strukturdiagnose: 6 Befunde (BUY-Abstain-Asymmetrie, Sub-Noise-Stop, Budget-Blindfleck …) + falsifizierbare Watch-Items WI-1…WI-6 für die Datenwoche ab 2026-07-20
- [phase10_v3/DATA_WEEK_REVIEW_2026-07-25.md](../phase10_v3/DATA_WEEK_REVIEW_2026-07-25.md) — 📕 erste Datenwoche ausgewertet: WI-2 tot (Paper-Tracker-Bug), WI-1 untestbar (Funnel-Kollaps Di–Fr); 2 Bugs root-caused + gefixt, `INSUFFICIENT_FUNDS`-Reject als Operator-Punkt geflaggt; V4-Scope verschoben auf saubere Woche
- [phase10_v3/DATA_WEEK_REVIEW_2026-07-31.md](../phase10_v3/DATA_WEEK_REVIEW_2026-07-31.md) — 📕 zweite Datenwoche: 366 Zyklen → 1 Kandidat → 0 Trades; W1+W5 bestätigt (frische Zitate), WI-2 erneut tot; 3 neue Bugs seit Rollout (point_value-Drift 40x, Reward-Score-Inversion, Paper-Lesson-Prompt) + Phase-11-Scope-Vorschlag H1–H7
- [phase10_v3/DATA_WEEK_REVIEW_2026-08-07.md](../phase10_v3/DATA_WEEK_REVIEW_2026-08-07.md) — 📕 erste H1-Live-Woche: Funnel weiterhin kollabiert (0 Kandidaten, 5/5 Tage); Kernbefund ist ein IG-`/prices`-Ausfall ab 08-04 (5-Min-Tracker-Kadenz, nicht der 30-Min-Öffnungs-Intervall), der 18/22 `instrument_universe`-Epics in Quarantäne schickte; WI-2/W2 weiterhin unbeantwortet (Artefakt, nicht widerlegt) — ⚠ **§3 Root Cause superseded**, s. nächster Eintrag
- [phase10_v3/ALLOWANCE_INCIDENT_2026-08-08.md](../phase10_v3/ALLOWANCE_INCIDENT_2026-08-08.md) — 📕 korrigiert obige §3.1/§3.2: **kein IG-Ausfall**, sondern das eigene Konto-Kontingent für historische Kursdaten, aufgebraucht vom Paper-Tracker (300 Datenpunkte **pro Fetch**, ≈19.800 in einem Tag); + Tracker-Fix (Stale-Expiry ohne Fetch, Budget-Breaker, `env.error`) + Restart-Gate — vor jedem Scheduler-Neustart lesen
- [phase10_v3/OUTAGE_EXPIRED_PAPER_IDS_2026-08-08.json](../phase10_v3/OUTAGE_EXPIRED_PAPER_IDS_2026-08-08.json) — 📕 die 390 `paper_id`s, die durch den Allowance-Ausfall (nicht durch Geometrie) auf `EXPIRED_UNRESOLVED` kippen; **vor** dem ersten Tracker-Tick gesichert, danach nicht mehr unterscheidbar
- [phase10_v3/DATA_SOURCE_STRATEGY_2026-08-11.md](../phase10_v3/DATA_SOURCE_STRATEGY_2026-08-11.md) — 📕 **Entscheidung:** IGs Kontingent ist bestätigt 10.000 Datenpunkte/Woche (festes 7-Tage-Fenster), H1 bräuchte ~49.500 → der Paper-Tracker wird auf die **bereits gebaute** `ChainedBarProvider`-Kette (IG→yFinance) umgestellt; **nicht** Lightstreamer (Live-Ticks ≠ historische Bars) und **nicht** Eigenbau; unabhängig bestätigt durch ein zweites IG-Setup
- [phase10_v3/H4_LESSON_FEEDBACK_SCOPE_2026-08-08.md](../phase10_v3/H4_LESSON_FEEDBACK_SCOPE_2026-08-08.md) — 📕 H4-Scoping gegen As-Built: 4 Trades (alle BUY, alle Verluste) → 4 Lessons → **5.973 Renderings** über zwei Prompt-Kanäle; `relevance_score` existiert und wird von keiner Query gelesen (H4-a braucht keine Migration); Empfehlung H4-a zuerst und allein
- [docs/concepts/phase10_v3_plan.md](./concepts/phase10_v3_plan.md) — 📕 execution-ready plan (locked decisions V3-D1…D10, Steps 0–11)
- [docs/concepts/PHASE10_V3_KICKOFF_HANDOVER.md](./concepts/PHASE10_V3_KICKOFF_HANDOVER.md) — 📕 kickoff handover from M1-close into V3

## Prior phase (9 — V2 Foundation, baseline collection continues weekdays)
- [phase9_universe/CLAUDE.md](../phase9_universe/CLAUDE.md) — 🔄 16KB · phase head; Steps 2–8 open; read + newest Session-stopped block first
- [phase9_universe/README.md](../phase9_universe/README.md) — 🔄 1KB · public surface
- [docs/concepts/phase9_v2_foundation_plan(1).md](./concepts/phase9_v2_foundation_plan(1).md) — 📕 38KB · the full V2 plan (§-referenced from the phase head)
- [docs/concepts/phase1_hardening_plan.md](./concepts/phase1_hardening_plan.md) — 📗 14KB · P1-hardening side-track plan (Steps 0–3 done)
- [docs/concepts/doc_layers_token_efficiency_plan.md](./concepts/doc_layers_token_efficiency_plan.md) — 📕 11KB · this restructure's plan (executed 2026-07-06)

## Meta-Strang (M — orthogonal, Build-/Laufzeit-Unabhängigkeit)
- [meta_m1_harness/CLAUDE.md](../meta_m1_harness/CLAUDE.md) — 📗 14KB · M1 phase head — **✅ CLOSED, Steps 0–10 all done**: no migration (gap 0pp), AGENTS.md shipped, P4/P6 cold fallback smoke-PASSed · [archive](../meta_m1_harness/SESSIONS_ARCHIVE.md) 15KB
- [meta_m1_harness/META_M1_PREREGISTRATION.md](../meta_m1_harness/META_M1_PREREGISTRATION.md) — 📕 4KB · Δ/P/K/E/M + decision rule, committed before any trial, never edited (only superseded)
- [meta_m1_harness/META_M1_RESULTS.md](../meta_m1_harness/META_M1_RESULTS.md) — 📕 10KB · measured 2026-07-09: gate_pass_rate 90%/90%, gap 0pp not-distinguishable, portability annex, + Step-10 fallback smoke appendix
- [meta_m1_harness/META_M1_DECISION.md](../meta_m1_harness/META_M1_DECISION.md) — 📕 3KB · rule applied literally: no migration (E<M); fire-extinguisher finding = gap 0pp
- `meta_m1_harness/specs/S0.md`…`S7.md` — 📗 · self-contained bake-off trial specs (Abstain-/No-Trade-Lessons testfield); S0/S1–S5 measured, S6/S7 reference-build-only
- `meta_m1_harness/bakeoff/` (`harness_bakeoff.py`, `analyze.py`, `preamble.txt`, `store_bakeoff_key.py`) — 📗 · the measurement instrument; `--dry-run` prints the trial matrix without executing anything; the bake-off Anthropic key lives only in the OS keyring (`store_bakeoff_key.py` seeds it), never a shell env var or file
- [docs/concepts/meta_m1_harness_plan.md](./concepts/meta_m1_harness_plan.md) — 📕 36KB · execution-ready plan (Steps 0–10, locked decisions M1-D1…D13)
- [docs/concepts/meta_phase_unabhaengigkeit_konzept.md](./concepts/meta_phase_unabhaengigkeit_konzept.md) — 📕 16KB · Hypothesis/theory doc (H_Build/H_Runtime, Decisions A–H)
- [docs/concepts/PHASE10_META_KICKOFF_HANDOVER.md](./concepts/PHASE10_META_KICKOFF_HANDOVER.md) — 📕 8KB · kickoff handover from Phase 9 close-out into the Meta-Phase
- [docs/concepts/market_snapshot_middleman_konzept.md](./concepts/market_snapshot_middleman_konzept.md) — 📕 8KB · gated V2.5/V3 idea capture (MarketSnapshot middleman); not built, not part of M1

## Closed phases (head 📗 + archive 📦 each; READMEs = public surface)
- [phase1_broker_wrapper/CLAUDE.md](../phase1_broker_wrapper/CLAUDE.md) — 📗 10KB · IG wrapper head (Envelope, auth, hardening) · [README](../phase1_broker_wrapper/README.md) · [archive](../phase1_broker_wrapper/SESSIONS_ARCHIVE.md) 11KB
- [phase1_broker_wrapper/lightstreamer_integration_notes.md](../phase1_broker_wrapper/lightstreamer_integration_notes.md) — 📗 26KB · LS/TLCP chronicle + Step-7a finding
- [phase1_broker_wrapper/lightstreamer_ig_reference.md](../phase1_broker_wrapper/lightstreamer_ig_reference.md) — 📗 13KB · LS protocol/field reference
- [phase2_persistence/CLAUDE.md](../phase2_persistence/CLAUDE.md) — 📗 6KB · persistence head (no archive — no history) · [README](../phase2_persistence/README.md)
- [phase3_external_data/CLAUDE.md](../phase3_external_data/CLAUDE.md) — 📗 28KB · yFinance head incl. P5-momentum-flag notice (single close-out block kept) · [README](../phase3_external_data/README.md)
- [phase4_research/CLAUDE.md](../phase4_research/CLAUDE.md) — 📗 27KB · research head, 8 locked decisions, candidate contract · [README](../phase4_research/README.md) · [archive](../phase4_research/SESSIONS_ARCHIVE.md) 25KB
- [phase5_execution/CLAUDE.md](../phase5_execution/CLAUDE.md) — 📗 18KB · gates/VETOs head, decisions A–H · [README](../phase5_execution/README.md) · [archive](../phase5_execution/SESSIONS_ARCHIVE.md) 44KB
- [phase6_debate/CLAUDE.md](../phase6_debate/CLAUDE.md) — 📗 19KB · debate head, decisions A–K · [README](../phase6_debate/README.md) · [archive](../phase6_debate/SESSIONS_ARCHIVE.md) 44KB
- [phase7_reward/CLAUDE.md](../phase7_reward/CLAUDE.md) — 📗 33KB · reward head, decisions A–J, pinned contracts · [README](../phase7_reward/README.md) · [archive](../phase7_reward/SESSIONS_ARCHIVE.md) 65KB
- [phase8_scheduler/CLAUDE.md](../phase8_scheduler/CLAUDE.md) — 📗 28KB · scheduler head, verified contracts (✅ live 2026-07-03; 2026-07-11 POST_WINDOW-sleep-cap hotfix) · [README](../phase8_scheduler/README.md) · [archive](../phase8_scheduler/SESSIONS_ARCHIVE.md) 196KB

## Concept docs (📕 snapshots — the plan a phase was built from)
- [phase1_broker_api_konzept.md](./concepts/phase1_broker_api_konzept.md) — 📕 17KB
- [phase2_persistence_konzept.md](./concepts/phase2_persistence_konzept.md) — 📕 24KB
- [phase3_external_data_konzept.md](./concepts/phase3_external_data_konzept.md) — 📕 32KB
- [phase4_research_plan_konzept.md](./concepts/phase4_research_plan_konzept.md) — 📕 46KB
- [phase5_concept.md](./concepts/phase5_concept.md) — 📕 54KB
- [phase6_debate_concept.md](./concepts/phase6_debate_concept.md) — 📕 42KB
- [phase7_reward_concept.md](./concepts/phase7_reward_concept.md) — 📕 48KB
- [phase8_scheduler_concept.md](./concepts/phase8_scheduler_concept.md) — 📕 62KB
- [phase8_v1.5_hotfix_plan.md](./concepts/phase8_v1.5_hotfix_plan.md) — 📕 33KB · [v1.6](./concepts/phase8_v1.6_hotfix_plan.md) 29KB · [v1.7](./concepts/phase8_v1.7_hotfix_plan.md) 10KB

## Handovers (📕 snapshots — session-to-session context transfers)
- [META_M1_CLOSEOUT_HANDOVER.md](../meta_m1_harness/META_M1_CLOSEOUT_HANDOVER.md) — 📕 7KB · M1 closeout for the next Web-Chat: intentional plan drifts + an optional M2 (code-quality + cross-model) proposal
- [PHASE9_V2_LIVE_RESULTS_HANDOVER.md](../phase9_universe/PHASE9_V2_LIVE_RESULTS_HANDOVER.md) — 📕 6KB · first V2 live-run results (2026-07-07): pipeline proven, open proof points, watch items
- [PHASE8_CLOSEOUT_HANDOVER.md](../phase8_scheduler/PHASE8_CLOSEOUT_HANDOVER.md) — 📕 17KB · V2/V3/V4 reframe proposal (P9 kickoff source)
- [PHASE8_V1.5_HOTFIX_HANDOVER.md](../phase8_scheduler/PHASE8_V1.5_HOTFIX_HANDOVER.md) — 📕 23KB · [V1.6](../phase8_scheduler/PHASE8_V1.6_HANDOVER.md) 11KB

## Session archives (📦 verbatim history, newest-first)
- [docs/sessions/root_claude_md_phase_status_archive.md](./sessions/root_claude_md_phase_status_archive.md) — 📦 37KB · root "Current state" narrative as of 2026-07-03
- Per-phase `SESSIONS_ARCHIVE.md` — 📦 · linked from each phase head above (rotated 2026-07-06)

## Test-run reports (📕 dated)
- [scripts/2026_07_01-Testrun-Results.md](../scripts/2026_07_01-Testrun-Results.md) — 📕 8KB
- [scripts/2026_07_02-v1.6-step1-diagnosis.md](../scripts/2026_07_02-v1.6-step1-diagnosis.md) — 📕 7KB
