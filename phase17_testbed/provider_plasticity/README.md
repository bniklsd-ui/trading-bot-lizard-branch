---
status: working-set
purpose: Working notes for the provider-plasticity decision (Nikinger 2026-10-19) — material for an upcoming Opus miniplan session, not yet a plan
read-when: (a) picking up the provider-plasticity topic cold, (b) Opus session that needs to plan the multi-provider LLM extension
detail: L0 (index for this folder) — opens the body files in order
up: ../CLAUDE.md
down:
  - ./01_decision_proposal.md   # T25–T28 sketch + locked-decision phrasing for Opus
  - ./02_current_state.md       # what the code already does (Block C scope, llm_profiles.py, OpenAICompatLLMClient)
  - ./03_opus_brief.md          # the single-page brief for Opus
  - ./04_open_questions.md      # items Nikinger hasn't decided yet (provider list, scope, where this lives in Phase 17)
created: 2026-10-19
---

# provider_plasticity/ — Phase 17 Working Notes

**Topic:** endpoint-Abstraktion des Trading-Bots so umbauen, dass sie mit
sämtlichen „gängigen" Providern funktioniert (Anthropic, OpenAI, die chinesischen
Anbieter etc.).

**Status:** working set. **Noch kein Plan.** Diese Notes sammeln die Entscheidung
(Nikinger 2026-10-19), den Ist-Stand (Code = Source-of-Truth), und die offenen
Fragen — genau das, was eine Opus-Session zum Planen braucht.

## Reading order

1. **Decision-Proposal** — was die gelockte Entscheidung im Kern sagt + T25–T28-Skizze
2. **Current-State** — was der Code heute schon kann (Block C aus Plan §6 reicht
   für 2–3 weitere Provider, hat aber 2–3 Lücken für „alle gängigen")
3. **Opus-Brief** — die einseitige Übergabe an die Opus-Session (Frage + Scope +
   gewünschte Lieferform)
4. **Open-Questions** — was die Opus-Session von Nikinger zurückfragen muss,
   bevor sie plant (Provider-Liste, Phase-17 vs. Folgephase, Miniplan-Granularität)

## Ownership

- **Editor:** Opus-Miniplan-Session (geplant).
- **Reviewer:** Nikinger (vor jedem Folge-Commit, der aus diesem Material entsteht).
- **Source of Truth:** am Ende der Opus-Session wandert eine Anker-Section in den
  Plan (`../docs/concepts/phase17_testbed_plan.md` §1 als T25–T28) **und** der
  Plan selbst wird um den neuen Block erweitert.
