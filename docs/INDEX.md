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
- [README.md](../README.md) — 📗 13KB · human overview + machine setup (venv, keyring, smoke test)
- [ROADMAP.md](../ROADMAP.md) — 📗 25KB · Phase 1–11 plan + status per phase
- [ARCHITECTURE.md](../ARCHITECTURE.md) — 📗 18KB · system layers, components, risks
- [DOC_LAYERS_CONVENTION.md](./DOC_LAYERS_CONVENTION.md) — 📗 · generic (project-agnostic) doc-layers spec

## Active phase (9 — V2 Foundation)
- [phase9_universe/CLAUDE.md](../phase9_universe/CLAUDE.md) — 🔄 16KB · phase head; Steps 2–8 open; read + newest Session-stopped block first
- [phase9_universe/README.md](../phase9_universe/README.md) — 🔄 1KB · public surface
- [docs/concepts/phase9_v2_foundation_plan(1).md](./concepts/phase9_v2_foundation_plan(1).md) — 📕 38KB · the full V2 plan (§-referenced from the phase head)
- [docs/concepts/phase1_hardening_plan.md](./concepts/phase1_hardening_plan.md) — 📗 14KB · P1-hardening side-track plan (Steps 0–3 done)
- [docs/concepts/doc_layers_token_efficiency_plan.md](./concepts/doc_layers_token_efficiency_plan.md) — 📕 11KB · this restructure's plan (executed 2026-07-06)

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
- [phase8_scheduler/CLAUDE.md](../phase8_scheduler/CLAUDE.md) — 📗 22KB · scheduler head, verified contracts (✅ live 2026-07-03) · [README](../phase8_scheduler/README.md) · [archive](../phase8_scheduler/SESSIONS_ARCHIVE.md) 192KB

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
- [PHASE8_CLOSEOUT_HANDOVER.md](../phase8_scheduler/PHASE8_CLOSEOUT_HANDOVER.md) — 📕 17KB · V2/V3/V4 reframe proposal (P9 kickoff source)
- [PHASE8_V1.5_HOTFIX_HANDOVER.md](../phase8_scheduler/PHASE8_V1.5_HOTFIX_HANDOVER.md) — 📕 23KB · [V1.6](../phase8_scheduler/PHASE8_V1.6_HANDOVER.md) 11KB

## Session archives (📦 verbatim history, newest-first)
- [docs/sessions/root_claude_md_phase_status_archive.md](./sessions/root_claude_md_phase_status_archive.md) — 📦 37KB · root "Current state" narrative as of 2026-07-03
- Per-phase `SESSIONS_ARCHIVE.md` — 📦 · linked from each phase head above (rotated 2026-07-06)

## Test-run reports (📕 dated)
- [scripts/2026_07_01-Testrun-Results.md](../scripts/2026_07_01-Testrun-Results.md) — 📕 8KB
- [scripts/2026_07_02-v1.6-step1-diagnosis.md](../scripts/2026_07_02-v1.6-step1-diagnosis.md) — 📕 7KB
