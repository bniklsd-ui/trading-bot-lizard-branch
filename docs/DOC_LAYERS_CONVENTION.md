---
status: live
purpose: Generic (project-agnostic) spec of the Doc-Layers convention — layer model, header cards, index, rotation, behavioral rules
read-when: applying this convention to a new .md collection, or checking a rule's exact wording
detail: L2
up: INDEX.md
updated: 2026-07-06
---
# Doc-Layers Convention (v1, 2026-07-06)

A structure for .md collections that lets an AI model (or a human) **decide whether a file is
worth reading from ≤15 lines**, and hop between files via explicit links instead of directory
searches. Written project-agnostic: drop it into any repo, vault, or notes directory.

**Principle: never read a whole file to find out you didn't need it.** Every layer down costs
more tokens; metadata at each layer prices the hop before you take it.

## The 4 layers

| Layer | What | Read cost | Read when |
|---|---|---|---|
| **L0** | `INDEX.md` — one line per doc: path · status glyph · ~size · read-when hook | ~4KB | always; navigation starts here |
| **L1** | header card — YAML frontmatter, ≤15 lines, top of every **living** doc | ~0.3KB (`Read` with `limit: 15`) | before opening any body |
| **L2** | the living doc body — kept lean, soft cap **≤40KB** | varies | when the card says the answer is here |
| **L3** | archives & dated snapshots — history, full concepts, superseded plans | large | only when auditing how something came about |

## L1 header card schema

```yaml
---
status: live | snapshot | archive | closed-phase
purpose: <one sentence — what this file answers>
read-when: <concrete trigger>
detail: L2            # this file's layer
up: <path>            # the coarser doc that indexes this one
down:                 # finer-detail docs this one links into (with a hint comment each)
  - <path>            # <what's down there>
updated: YYYY-MM-DD
---
```

- `up`/`down` are **detail-layer links**: climb up for overview, descend for depth. A missing
  target is a doc bug (findable: extract `](...)` + `up:`/`down:` paths, `test -f` each).
- **Dated snapshots and pre-existing archives get NO in-file card** — they stay byte-identical
  (auditability). Their metadata lives only in `INDEX.md`. Newly *authored* archive files do
  get a card, since we write them.

## INDEX.md (L0) format

One line per doc, grouped by kind:
`- [path](path) — <glyph> <~size> · <read-when hook>`
Glyphs: 🔄 active · 📗 live (maintained) · 📕 snapshot (dated, never edit) · 📦 archive (verbatim history).
Maintenance rule: **new .md file ⇒ its index line lands in the same commit.**
Oversize check (every hit must be 📕/📦): `find . -name "*.md" -size +40k` (minus tooling dirs).

## Rotation rule (the anti-bloat mechanism)

Living logs (session handovers, running status) grow append-only and become dead weight. Fix
structurally, not by periodic cleanup:

1. The living doc carries exactly **one** current handover block (the newest).
2. When appending a new block, move the previously-newest block **verbatim, unedited** to the
   sibling `SESSIONS_ARCHIVE.md` (newest-first). Never retype content — move it mechanically
   (`sed -n 'A,Bp'`), and verify the split reassembles byte-identical before deleting.
3. Archives have no size cap; they're L3 and never read at session start.

## Behavioral rules (how a model should act in the collection)

These pair with the structure — layering only pays off if the reader behaves accordingly:

- **Source-of-truth precedence: tested artifact > design doc > status prose.** On conflict,
  trust the artifact, fix the doc immediately with a dated correction note.
- **Read enough, then act.** Read the minimum the layers allow, but never skip comprehension
  of what a change touches. Once you have enough to act, act — don't re-derive established facts.
- **Locked decisions stay locked.** Pinned decisions/contracts in a doc aren't re-litigated
  mid-task; contradicting evidence becomes an explicit finding for the human, never a silent deviation.
- **Report outcomes faithfully.** Failures are stated with output; skipped steps are named;
  verified results are stated plainly without hedging.
- **Root cause over symptom.** Before a fix, find every consumer of the thing you touch; fix
  once at the shared point.
- **Act vs. ask.** Proceed on reversible, in-scope steps; stop for destructive actions,
  out-of-scope edits, and genuine scope changes.
- **Write handovers for a cold reader.** Lead with the outcome; no session-local shorthand;
  next step specific enough to start without re-reading everything.

## Applying to a new collection (checklist)

1. Create `INDEX.md` with all files, statuses, hooks.
2. Card every living doc (top-of-file YAML, ≤15 lines, `up`/`down` wired).
3. Rotate history out of living logs into sibling archives (verbatim, verified).
4. Add the rotation + index-maintenance rules to the collection's root instructions file.
5. Never rename existing files for the convention — links elsewhere break; the index adapts to
   names as they are.
