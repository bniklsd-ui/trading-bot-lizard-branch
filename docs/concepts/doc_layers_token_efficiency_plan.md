# Plan: Token-Efficient .md Architecture ("Doc Layers")

> **For:** the Nikinger · **Written:** 2026-07-06 (planning session, Fable) · **Execute in:** session 2
> **Hard constraint: session 2 touches ONLY .md files. No code, no renames, no deletions of content — verbatim moves only.**
>
> ✅ **EXECUTED 2026-07-06, same session** (session budget allowed it — Nikinger go). All steps 1–6
> done except the commit itself (awaiting Nikinger green light after his auth-error retest).
> Verification: verbatim archive content == `git show HEAD` ranges (cmp-verified), heads ≤40KB,
> link check clean (1 pre-existing dead ROADMAP link fixed with dated note), diff is .md-only.

## Context

Project docs (excluding installed skills) total ~1.1MB across ~40 files. The bloat driver is
append-only `## Session stopped` history inside phase `CLAUDE.md` files — files the workflow
*requires* reading every session:

| File | Now | History share |
|---|---|---|
| `phase8_scheduler/CLAUDE.md` | 211KB | 31 session blocks ≈ 190KB |
| `phase7_reward/CLAUDE.md` | 94KB | 14 blocks ≈ 70KB |
| `phase5_execution/CLAUDE.md` / `phase6_debate/CLAUDE.md` | ~60KB each | similar |
| `phase9_universe/CLAUDE.md` (active) | 52KB | 10 blocks ≈ 30KB |
| `phase4_research/CLAUDE.md` | 50KB | similar |

Only the **newest** session block is the live handover (convention: "replace or update this block
at the start of each new session") — everything older is audit history read ~never, but paid for
on every session start.

Three precedents already exist in-repo; the design below only generalizes them:
1. **Verbatim-move archive** — `docs/sessions/root_claude_md_phase_status_archive.md` (Nikinger-decided 2026-07-03): moved, not rewritten, with a "why this file exists" header.
2. **One-line index** — memory `MEMORY.md`: `- [Title](file.md) — hook`.
3. **~40KB soft cap** — acknowledged in root CLAUDE.md's Doku-Hygiene note.

Nikinger decisions (2026-07-06): archives live **in-phase**; phase CLAUDE.md keeps **latest 1**
session block; external .md sets get a **generic convention only** (no restructure outside repo);
plus the added core requirement: **layered metadata + links** so a model reads a file's header
card to decide whether to descend and where to hop next.

---

## Design: the 4-layer model

The principle: *never read a whole file to find out you didn't need it.* Every hop down costs more
tokens; metadata at each layer tells you whether the hop is worth it.

```
L0  docs/INDEX.md            one line per doc (path · status · size · read-when)   ~4KB, read always
L1  header card              top ≤15 lines of each LIVING doc (via head/Read-limit) ~0.3KB per file
L2  doc body                 the lean living document itself                        target ≤40KB
L3  archives & snapshots     SESSIONS_ARCHIVE.md, concepts/, handovers              read only when auditing
```

### L1 header card spec (living docs only)

YAML frontmatter — same family as the memory-file convention, greppable, readable via
`Read(limit=15)` without loading the body:

```yaml
---
status: live | snapshot | archive | closed-phase
purpose: <one sentence — what this file answers>
read-when: <trigger, e.g. "working in phase9_universe">
detail: L2            # this file's layer
up: ../CLAUDE.md      # coarser doc that indexes this one
down:                 # finer-grained docs this one links into
  - SESSIONS_ARCHIVE.md        # full session history (L3)
  - ../docs/concepts/phase9_v2_foundation_plan(1).md   # full plan (L3)
updated: 2026-07-06
---
```

`up`/`down` is the layering link the Nikinger asked for: from any file you can climb to coarser
or descend to finer detail without a directory search. Links are relative paths; a missing target
is a doc bug findable by grep.

**Snapshots/archives get NO in-file card** — dated files stay byte-identical (existing
"dated snapshot convention", e.g. PHASE8_CLOSEOUT_HANDOVER.md). Their metadata lives only in
`docs/INDEX.md` (L0). Exception: newly *created* archive files get a card, since we author them.

### L0 index spec — `docs/INDEX.md`

One line per project .md (excluding `.agents/`, `.pytest_cache/`), grouped by kind, format:

```markdown
- [phase8_scheduler/CLAUDE.md](../phase8_scheduler/CLAUDE.md) — 📗 live · ~25KB · phase-8 head (closed phase); history → SESSIONS_ARCHIVE.md
- [docs/concepts/phase8_scheduler_concept.md](concepts/phase8_scheduler_concept.md) — 📕 snapshot · 60KB · full P8 concept; read only for P8 archaeology
```

Status glyphs: 📗 live · 📕 snapshot (never edit) · 📦 archive · 🔄 active-phase.
Header of INDEX.md states the maintenance rule (see Rules below) and the layer model in ~10 lines.

### Rotation rule (stops future bloat — the actual fix)

At session end, when appending the new `## Session stopped` block to the phase CLAUDE.md:
**move the previous block verbatim to `<phase>/SESSIONS_ARCHIVE.md`** (newest-first order there).
Phase CLAUDE.md therefore always carries exactly one session block. Archive files have no size
cap — they're L3, never read at session start.

---

## Session-2 worklist (ordered)

### Step 1 — Create per-phase `SESSIONS_ARCHIVE.md` + strip history (the ~430KB win)

For every file with >1 `## Session stopped` (or dated `## UI-Overhaul`/`## Bugfix`/`## UI-Erweiterung`) block:

- `phase8_scheduler/CLAUDE.md` → `phase8_scheduler/SESSIONS_ARCHIVE.md` (all blocks except newest; ~190KB)
- `phase7_reward/CLAUDE.md` → `phase7_reward/SESSIONS_ARCHIVE.md`
- `phase6_debate/CLAUDE.md`, `phase5_execution/CLAUDE.md`, `phase4_research/CLAUDE.md` → ditto
- `phase9_universe/CLAUDE.md` (active) → keep newest 1, archive the 9 older
- Check & apply same to: `phase3_external_data/CLAUDE.md` (27KB), `phase1_broker_wrapper/CLAUDE.md`, `phase1_broker_wrapper/lightstreamer_integration_notes.md` (31KB — has its own session blocks per root CLAUDE.md)

**Method (verbatim guarantee + cheap tokens):** locate block boundaries with `grep -n "^## "`,
extract with `sed -n 'A,Bp' >> ARCHIVE`, then delete the same ranges — do NOT retype content
through Write. Spot-check with `git diff --stat` + `diff <(extracted) <(original range)`.
Each archive file gets the standard "why this file exists / moved verbatim / newest-first"
header modeled on the root archive, plus an L1 card.
In the stripped CLAUDE.md, leave one pointer line where the history was:
`> Ältere Session-Blöcke: verbatim in [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) (newest-first).`

### Step 2 — Header cards (L1) on living docs

Add YAML frontmatter card to: root `CLAUDE.md`, `ROADMAP.md`, `ARCHITECTURE.md`, `README.md`,
all 9 phase `CLAUDE.md`, phase `README.md`s, `lightstreamer_integration_notes.md`,
`lightstreamer_ig_reference.md`, the new `SESSIONS_ARCHIVE.md`s, `docs/INDEX.md` itself.
~15 lines each, `up`/`down` links wired (phase CLAUDE.md ↑ root CLAUDE.md; ↓ its archive,
concept doc, README). **Do not touch** concepts/, handovers, dated scripts/*.md reports —
snapshot convention; they're covered by INDEX.md only.

### Step 3 — `docs/INDEX.md` (L0)

Create with all project .md files, grouped: Root & governance / Active phase / Closed phases
(head + archive pairs) / Concepts & plans (snapshots) / Handovers (snapshots) / Session archives /
Test-run reports. Sizes rounded, read-when hooks one line each.

### Step 4 — Root `CLAUDE.md` rule additions (~15 lines, inside "How to work in this repo")

- The 4-layer model in 4 lines + pointer to `docs/INDEX.md`.
- Rotation rule (mandatory, extends the existing session-end ritual).
- Index maintenance: new .md file ⇒ add one line to `docs/INDEX.md` in the same commit.
- Navigation guidance: "start at INDEX.md or a header card (`Read` with `limit: 15`); descend
  `down:` links only when the card says the answer is deeper."
- Update the existing Doku-Hygiene note to reference the new convention.

### Step 5 — Generic convention doc: `docs/DOC_LAYERS_CONVENTION.md` (~3KB, project-agnostic)

The reusable spec for vaults outside this repo: layer model, header-card schema, index format,
rotation rule, verbatim-move rule, the "read limit-15 first" navigation protocol. Written so it
can be dropped into any .md collection (e.g. ~/.claude memory already half-follows it). No
external files are restructured in session 2.

### Step 5b — Carry the "Working style" section into the convention doc

**Already done in the planning session (2026-07-06, Nikinger-approved):** root `CLAUDE.md`
gained a `## Working style (how to act, not just what to do)` section — behavioral calibration
for capable models, adapted from Fable-5-system-prompt formulations: source-of-truth precedence
(tested code > concept doc > status prose), act-vs-ask boundary, locked-decisions-stay-locked,
faithful outcome reporting (no "should work"), root-cause-over-symptom, read-enough-then-act,
cold-reader handovers.

For session 2: include a project-agnostic version of these seven bullets in
`docs/DOC_LAYERS_CONVENTION.md` (they're the behavioral half of the convention; the layer model
is the structural half). Nothing else in root CLAUDE.md needs a fable-pass — README/ROADMAP/
ARCHITECTURE contain no behavioral instructions (verified 2026-07-06).

### Step 6 — Commit hygiene

Atomic commits per step, scope `docs:` e.g. `docs: rotate phase4-8 session history to in-phase archives (verbatim)`.
Everything is on `phase9-v2-foundation` branch; no code files in any diff (verify: `git diff --stat | grep -v '\.md'` must be empty).

## Expected outcome

- Session-start read cost for a phase: 211KB → ~25KB worst case (phase 8); all phase heads ≤40KB.
- ~430KB of history moved (not lost) to L3.
- Any doc's relevance decidable from ≤15 lines; cross-file hops via explicit `up`/`down` links.
- Future bloat structurally prevented by the rotation rule, not by periodic cleanups.

## Verification (session 2, end)

1. `find . -name "*.md" -not -path "./.agents/*" -not -path "*/.pytest_cache/*" -size +40k` → only snapshots/archives listed.
2. Link check: extract all relative `](...)` targets from living docs + INDEX.md, `test -f` each.
3. Verbatim check: for each rotated file, `git show HEAD~1:<file>` block vs archive block diff = empty.
4. `pytest` baselines untouched (no code changed — nothing to run, `git diff --stat` proves it).
5. Fresh-eyes test: from `docs/INDEX.md` alone, locate "where is the P7 signed-size fix documented" in ≤2 hops.

## Explicitly out of scope / skipped (YAGNI)

- No file renames or moves of existing snapshots (would break ~25 inbound links).
- No condensation/rewriting of concept docs — they're L3 snapshots; INDEX.md line suffices.
- No lint/check script — the grep one-liners above live in INDEX.md's header instead (no-code constraint, and a script nobody runs is debt).
- No restructure of ~/.claude memory or other external vaults (generic convention only, per Nikinger decision).
