# AGENTS.md

Harness-neutral entry point. Claude Code auto-loads `CLAUDE.md`; if you're a different
agent/harness, read this first, then go read `CLAUDE.md` yourself — nothing auto-loads it for you.

## Read this first

**`CLAUDE.md` (repo root) is the single source of truth** for rules, conventions, and current
project state. Read it before touching anything in this repository.

## Navigation (Doc-Layers convention)

Docs here follow a layered model (full spec: `docs/DOC_LAYERS_CONVENTION.md`):

1. Start at `docs/INDEX.md` (L0) — one line per doc, tells you if it's worth opening at all.
2. A living doc's top ~15 lines are a YAML header card (L1): `purpose`/`read-when` decide
   whether the body is worth reading; `up:`/`down:` are links to the coarser/finer doc.
3. Only then read the body (L2), or an archive/dated snapshot (L3) if you're auditing history.

**`up:`/`down:` links are plain text, not an auto-resolved graph.** No tool loads the files
they point to for you — open them yourself, only when the task actually needs them
(on need-to-know), not by default.

## Working-style precedence

Tested code/artifact > concept/design doc > status prose. On conflict, trust what's actually
running, then fix the doc with a dated correction note — never silently trust prose over code.

## Hard prohibitions (full detail in `CLAUDE.md`)

- Never put credentials anywhere but the OS keyring — not `.env`, not JSON/YAML, not code.
- Never bypass a VETO check "for now" or "for testing."
- Never let AI output (candidate selection, Bull/Bear/Judge) trigger an order without
  code-side validation first.
