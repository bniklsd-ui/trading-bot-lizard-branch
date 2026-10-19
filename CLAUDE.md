---
status: live
purpose: Single source of truth for project rules, conventions, hard rules, and current phase status
read-when: always — auto-loaded at session start; everything else hangs off this file
detail: L2
up: docs/INDEX.md
down:
  - docs/INDEX.md          # L0 map of every project doc
  - ROADMAP.md
  - ARCHITECTURE.md
  - phase17_testbed/CLAUDE.md   # active phase head (🟡 korrigiert 2026-10-17: stand seit 09-05 auf phase9_universe)
updated: 2026-10-19 (A-3 sweep — 4 Banner-Blöcke nach docs/sessions/root_claude_md_phase_status_archive.md rotiert; Tabelle Phasen 9–13 einzeilig; Phasen-17-Banner bleibt + Phasen-17-Zeile in Tabelle)
---
# CLAUDE.md — Project Instructions

> Read this file before doing anything in this repository.
> It is the single source of truth for project rules, conventions, and current state.

---

## What this project is

A multi-phase, AI-augmented CFD trading bot for the DAX.
Primary broker: IG Markets (EUR account). Multi-broker abstraction in place.

The bot is structured around a **5-Gate Execution Pipeline** with adversarial
AI-driven direction decisions (Bull/Bear/Judge debate) and a deterministic VETO
cascade.

Full architecture: `docs/architecture/tradingbot_v2_architecture.svg`
Build order: `ROADMAP.md`

---

## Core principle (read carefully)

**Bauprinzip:** So wenig AI wie möglich, so viel AI wie nötig.

**Code macht:**
- Alle API-Calls (GET, POST, DELETE)
- Authentication, Session-Handling, Token-Refresh
- Spread / Drift / Momentum / Sizing — alle Berechnungen
- VETO-Checks (alle vier sind Code, nicht AI)
- Gate-Logik (True/False Entscheidungen)
- Persistenz (SQLite Reads/Writes, JSON Reads/Writes)
- TTL-Verwaltung, Retry-Logik, Error-Handling, Normalisierungen

**AI macht NUR:**
- "Welcher Kandidat?" — Research LLM
- Bull/Bear/Judge Debatte (Richtungsentscheidung)
- Lesson-Extraktion nach Trade (Longterm Brain)
- Council-Evaluation (Strategieprüfung)
- **NICHTS sonst**

If you find yourself reaching for an LLM call to do data fetching, formatting,
filtering, validation, or any deterministic logic — STOP. Use code instead.

---

## Hard Rules (no exceptions)

1. **Never put credentials in files.** Not in `.env`, not in JSON, not in YAML,
   not anywhere on disk. Credentials live ONLY in the OS keyring
   (macOS Keychain / Windows Credential Manager / Linux Secret Service).
   Access via `broker_wrapper/credentials.py`.

2. **Never bypass VETOs.** If you find code that skips a VETO check "for testing"
   or "for now" — flag it loudly. VETOs are the difference between a working bot
   and a blown account.

3. **Never let AI output trigger an order directly.** Every AI output
   (Bull/Bear/Judge APPROVED, Research candidate selection) MUST pass through
   code-side validation before any order is placed. Hallucinations are a real
   risk and are mitigated structurally, not by trust.

4. **Never test against real money first.** All new code is exercised against
   the IG Demo account via `scripts/smoke_test.py` before being trusted with the
   live account. No exceptions.

5. **The Force Trigger must respect Daily PNL.** Per the architecture analysis,
   the manual override (`ig_bot_force_trigger`) should be **locked** when daily
   PNL is negative. Human override at moments of emotional vulnerability is the
   biggest identified risk.

6. **Output envelope is canonical.** Every broker adapter method returns an
   `Envelope` JSON object (see `broker_wrapper/envelope.py`). Do not deviate
   from this shape. Tests, CLI, FastAPI, and bot core all depend on it.

---

## Current state

> **🔄 2026-10-17 — Phase 17 (Prüfstand) ERÖFFNET (Plan-Session, Opus 5.5).** Plan
> [`docs/concepts/phase17_testbed_plan.md`](./docs/concepts/phase17_testbed_plan.md), Phasenkopf
> [`phase17_testbed/CLAUDE.md`](./phase17_testbed/CLAUDE.md). **Keine neuen Features** — tiefe Härtung des
> Bestehenden (Nikinger). Inhalt:
> - die vier Phase-16-PASS-Blocker;
> - drei neu gemessene stille Totalausfälle: IG-REST-Bars +2 h in der Zukunft gestempelt; der
>   Divergenz-Sampler hat in 233 von 233 Läufen nie verglichen; `decision_context.abstain_record_id`
>   ist 3 669/3 669 leer;
> - LLM pro Rolle austauschbar. Research zuerst auf GLM über die z.ai-API mit Pay-per-use (Plan §14, 2026-10-18; ersetzt MiniMax M3). Der Bot nutzt nie den Coding-Plan-Endpoint;
> - Report + Shakedown → Prereg v5 als Fundament der ausgiebigen Tests.
>
> Exec: offener Test GLM in OpenCode (z.ai Coding Plan), Claude Code bleibt Anthropic-only mit Pflicht-Review vor dem Deploy (Plan §14). Σ-Baseline 1964. E1–E8 aus dem Phase-16-Handover sind entschieden
> (Plan §1); **E6: Gate P7/A6 gilt als erfüllt.**

> **✅ 2026-10-16 — Phase 16 (Freischaltung) ABGESCHLOSSEN MIT TEILBILANZ (Session #38, Opus 5.5).**
> Einstieg: [`phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md`](./phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md),
> Bild [`docs/architecture/phase16_activation.svg`](./docs/architecture/phase16_activation.svg). **Erreicht:** 6 von 9
> Löchern live zu (L7 per Code + Live-Probe), Bot handelt wieder, Autostart nach Reboot bewiesen, Backoff-Fix live (Buchungsverzug 24 h → 1–2 h).
> **Nicht erreicht:** AK15 — kein vorregistrierter Autonomie-Lauf PASS (v3 FAIL K1/K5/K6, v4 FAIL K6). Vier PASS-Blocker
> für die Folgearbeit: Token-Budget (K6), Promotion-Bridge live tot (`bridge.py:146` ruft `validate()` ohne `trades`),
> Monitor-Orphan nach Restart, Breaker-Blindfenster bis IG-Settlement. **Gate P7/A6 (Phase-15-Folgepunkt):** deal-bezogene
> CRITICALs max 2 je Trade über 15 OPENs (Quell-Definition A6 erfüllt), K5 nach registrierter Lesart FAIL —
> Öffnen von Gate P7 = Nikinger-Entscheidung E6 im Handover. Σ **1964** grün
> (16 Suites einzeln). Nummer/Rahmen der Folgearbeit = offene Nikinger-Entscheidung E1 im Handover (E1–E8).

> ⟳ Doc-Rotation 2026-10-19 (Phase-17 A-3): die vier Banner-Blöcke "Phase 16 ERÖFFNET (alt, 2026-09-05 Fable-5.1)", "Phase 15 ABGESCHLOSSEN (2026-09-05 Session #13)", "🟡 Korrekturhinweis 2026-09-08 (Phase 16 Exec-Session #23, Doc-Drift-Repair)" und "Phase 13+14 ABGESCHLOSSEN (2026-08-31 Sessions 18+23)" sind wortgleich in den Datums-Abschnitt `docs/sessions/root_claude_md_phase_status_archive.md` rotiert; das Inhaltsverzeichnis bleibt unverändert, die Tabelle unten führt Phasen 9-13 jetzt einzeilig.

> 📦 **Doku-Hygiene (2026-07-03):** die volle Phase-1–8-Chronik, die vorher hier stand, ist
> **wortgleich, unverändert** ausgelagert nach
> [`docs/sessions/root_claude_md_phase_status_archive.md`](./docs/sessions/root_claude_md_phase_status_archive.md)
> (root `CLAUDE.md` war über der empfohlenen ~40KB-Grenze; reine Verschiebung, kein Umschreiben —
> gleiche Auditability-Regel wie bei `## Session stopped`-Blöcken). Neue Phase-Status-Updates gehören
> ab jetzt in die jeweilige Phasen-`CLAUDE.md`, nicht mehr hierher.
> **Update 2026-07-06:** dieses Prinzip ist jetzt repo-weit generalisiert — Doc-Layers-Konvention
> (L0-Index + Header-Cards + per-Phase `SESSIONS_ARCHIVE.md` + Rotationsregel), siehe
> [`docs/INDEX.md`](./docs/INDEX.md) und [`docs/DOC_LAYERS_CONVENTION.md`](./docs/DOC_LAYERS_CONVENTION.md).

**Kompakter Stand pro Phase** (Details im Archiv oben oder in der jeweiligen Phasen-`CLAUDE.md`):

| Phase | Status |
|---|---|
| 1 — Broker Wrapper | ✅ Abgeschlossen, live-verifiziert |
| 2 — Persistenz | ✅ Abgeschlossen, live-verifiziert |
| 3 — External Data | ✅ Abgeschlossen, live-verifiziert |
| 4 — research.py + LLM | ✅ Abgeschlossen, live-getestet ≠ profit-validiert |
| 5 — ig_bot Gates 1–5 | ✅ Abgeschlossen, live-verifiziert ≠ profit-validiert |
| 6 — Bull/Bear/Judge Debatte | ✅ Abgeschlossen, live-verifiziert ≠ profit-validiert |
| 7 — Reward/Brain | ✅ live-verifiziert + gemerged (2026-06-26) |
| 8 — Scheduler | ✅ **live-verifiziert (2026-07-03)** — zwei autonome Trades + ein tatsächlich auslösender Safety-Breaker (Token-Budget), Nikinger-bestätigt. Details: `phase8_scheduler/CLAUDE.md` |
| 9 — V2: Foundation (autonome Epic-Research + Daten-Zuverlässigkeit) | 🔄 in Arbeit (Stand 2026-07-07, Code produktiv seit 2026-07-06). Phasenkopf: [`phase9_universe/CLAUDE.md`](./phase9_universe/CLAUDE.md); Live-Ergebnisse: [`PHASE9_V2_LIVE_RESULTS_HANDOVER.md`](./phase9_universe/PHASE9_V2_LIVE_RESULTS_HANDOVER.md). 🟡 *2026-10-19: Status-Prosa veraltet — formaler Closeout nie geschrieben (Nikinger-Entscheidung, nicht Phase 17).* |
| 10 — V3: Persistenz-Reform + No-Trade-Lessons + Paper-Trades | ✅ abgeschlossen Closeout 2026-08-25 (Σ 1698, 165 Tests). Phasenkopf: [`phase10_v3/CLAUDE.md`](./phase10_v3/CLAUDE.md); Handover: [`PHASE10_CLOSEOUT_HANDOVER.md`](./phase10_v3/PHASE10_CLOSEOUT_HANDOVER.md). |
| 11 — V3-Fortsetzung: Funnel-/Mess-Fixes (aus Datenwoche-2-Review) | 🛑 DEFERRED (Notbremse 2026-08-11). Handover: [`phase10_v3/PHASE11_DEFERRAL_HANDOVER.md`](./phase10_v3/PHASE11_DEFERRAL_HANDOVER.md). |
| 12 — Datenfundament (Registry + BarService + Bar-Archiv + Recorder) | ✅ abgeschlossen Closeout 2026-08-25 (Σ 1698, 143 Tests). Phasenkopf: [`phase12_data_foundation/CLAUDE.md`](./phase12_data_foundation/CLAUDE.md); Handover: [`PHASE12_CLOSEOUT_HANDOVER.md`](./phase12_data_foundation/PHASE12_CLOSEOUT_HANDOVER.md). |
| 13 — Live-Datenfundament (4-stufige Beschaffung: LS → yF → Fremdquelle → IG-Rettung) | ✅ abgeschlossen Closeout 2026-08-31 Session 18 (Σ 1703, 74 Tests). Phasenkopf: [`phase13_live_data/CLAUDE.md`](./phase13_live_data/CLAUDE.md); Handover: [`PHASE13_CLOSEOUT_HANDOVER.md`](./phase13_live_data/PHASE13_CLOSEOUT_HANDOVER.md); Beweiswoche: [`PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md`](./phase13_live_data/PHASE13_BEWEISWOCHE_FINDINGS_2026-08-31.md). |
| 14 — Discovery-Then-Deterministic (Quellen-Registry + autonomer Discovery-Daemon) | ✅ abgeschlossen Closeout 2026-08-31 Session 23 (Σ 1703, 61 Tests, D5 freigegeben). Phasenkopf: [`phase14_discovery/CLAUDE.md`](./phase14_discovery/CLAUDE.md); Handover: [`PHASE14_CLOSEOUT_HANDOVER.md`](./phase14_discovery/PHASE14_CLOSEOUT_HANDOVER.md). |
| 15 — V4: Sophisticated/Optional (Council · Handover · Reward-Reform · Force-Trigger · Instinct-ECC) | ✅ abgeschlossen Closeout 2026-09-05 Session #13 (Σ 1843, 18+6 Commits). Phasenkopf: [`phase15_v4/CLAUDE.md`](./phase15_v4/CLAUDE.md); Handover: [`PHASE15_CLOSEOUT_HANDOVER.md`](./phase15_v4/PHASE15_CLOSEOUT_HANDOVER.md). 🟡 *2026-10-16 (Phase-16-Closeout):* Promotion-Bridge gebaut, **live tot** (`bridge.py:146`); Ledger-Restore + Migration 008/009 erledigt. |
| 16 — Freischaltung (alle Löcher zu, alle Arme scharf, 2-Wochen-Autonomie-Test) | ✅ **abgeschlossen mit Teilbilanz (Closeout 2026-10-16, Session #38)** — 6/9 Löcher live zu + L7 per Live-Probe (L2 Token-Budget ❌, L6 Bridge gebaut aber live tot), Bot handelt wieder (17 Trades seit 09-28), systemd-Autostart live bewiesen; **AK15 nie PASS** (v3 09-30→10-13 FAIL K1/K5/K6, v4-Brücke FAIL K6). Σ 1964 grün (+121 seit 1843). Handover: [`phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md`](./phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md) · Bild: [`docs/architecture/phase16_activation.svg`](./docs/architecture/phase16_activation.svg) · Plan [`docs/concepts/phase16_activation_plan.md`](./docs/concepts/phase16_activation_plan.md) · Phasenkopf [`phase16_activation/CLAUDE.md`](./phase16_activation/CLAUDE.md). 🟡 *Korrigiert 2026-10-16:* die Zeile stand seit 09-05 auf „Exec-Session startet mit Block A Step A-0". |
| 17 — Prüfstand (Mess- und Geldpfad-Defekte zu, LLM pro Rolle austauschbar, Report + Prereg v5) | 🔄 **eröffnet 2026-10-17 (Plan-Session, Opus 5.5)** — Plan [`docs/concepts/phase17_testbed_plan.md`](./docs/concepts/phase17_testbed_plan.md) · Phasenkopf [`phase17_testbed/CLAUDE.md`](./phase17_testbed/CLAUDE.md); Exec startet mit Block A Step A-0 |

**Meta-Strang M1 — Harness-Unabhängigkeit — ✅ CLOSED (2026-07-09):** orthogonal zur
Nummerierung oben. Vorregistrierter Bake-off Claude Code vs. OpenCode: `gate_pass_rate`
90%/90%, Gap 0,00pp → **keine Migration** (E<M, jetzt zusätzlich messbestätigt). Plus
`AGENTS.md` + ein getesteter, kalter P4/P6-Fallback (`OpenAICompatLLMClient`), beide
smoke-verifiziert. Details: [`meta_m1_harness/CLAUDE.md`](./meta_m1_harness/CLAUDE.md);
optionaler nächster Schritt (ungelockt):
[`META_M1_CLOSEOUT_HANDOVER.md`](./meta_m1_harness/META_M1_CLOSEOUT_HANDOVER.md).

---

## File organization (where things go)

```
~/trading-bot/                              ← root
├── README.md                               ← human-facing overview
├── CLAUDE.md                               ← this file
├── ARCHITECTURE.md                         ← architecture summary + links
├── ROADMAP.md                              ← Phase 1–9 plan
├── .gitignore
│
├── docs/
│   ├── concepts/                           ← Phase-N concept docs
│   │   ├── phase1_broker_api_konzept.md
│   │   ├── phase2_persistence_konzept.md
│   │   └── phase3_external_data_konzept.md
│   ├── architecture/
│   │   ├── tradingbot_v2_architecture.svg
│   │   └── tradingbot_v2_architecture.pdf
│   └── sessions/                           ← (optional) chat session summaries
│
├── data/                                   ← runtime SQLite + JSON state (gitignored)
├── phase1_broker_wrapper/                  ← Phase 1 code ✅
├── phase2_persistence/                     ← Phase 2 code ✅
├── phase3_external_data/                   ← Phase 3 code ✅
└── ...
```

**Rule:** Each phase is a self-contained directory with its own `README.md`,
`requirements.txt`, and optionally its own `CLAUDE.md`. Cross-phase imports
happen only via well-defined contracts (e.g. Envelope JSON for broker_wrapper).

---

## Conventions

**Python:**
- Type hints everywhere (`from __future__ import annotations`)
- Docstrings on every public function/class (purpose, args, raises)
- `pytest` for tests, mock HTTP — no network calls in unit tests
- `requests` for HTTP, NOT `urllib` or `httpx` (consistency)
- One file = one responsibility (do not bloat modules)

**Errors:**
- Custom typed exception hierarchy in `exceptions.py`
- Never swallow exceptions silently — log + raise or log + return error envelope
- HTTP errors map to envelope error codes (see existing IGAdapter for pattern)

**Logging:**
- Use the standard `logging` module
- Logs go to stderr, never stdout (stdout is reserved for envelope JSON)
- DEBUG for internals, INFO for milestones, WARNING/ERROR for problems

**Git:**
- Atomic commits — one logical change per commit
- Commit message format: `<scope>: <imperative>` e.g. `broker_wrapper: fix epic search timeout`
- Never commit credentials. Never commit `.venv/`. Never commit `__pycache__/`.

---

## How to work in this repo

**Starting a session:**

1. Confirm which phase is active (check "Current state" above)
2. Read the relevant phase README (e.g. `phase1_broker_wrapper/README.md`)
3. Check `git status` and `git log -5` to understand recent work
4. Run existing tests before making changes (`pytest tests/ -v`)
5. If a `## Session stopped` block exists in the active phase's `CLAUDE.md` or
   relevant notes file — read it first. It records exactly where the previous
   session ended and what comes next.

**Navigating docs (token discipline — the Doc-Layers model):**

Start at [`docs/INDEX.md`](./docs/INDEX.md) (L0: one line per doc). Living docs carry a
≤15-line YAML header card (L1) — read it via `Read` with `limit: 15` and decide from
`purpose`/`read-when` whether the body (L2) is worth loading; hop between files via the card's
`up:`/`down:` links instead of directory searches. Archives and dated snapshots (L3:
`SESSIONS_ARCHIVE.md`, `docs/concepts/`, handovers) are read only when auditing history —
never at session start. Full spec: [`docs/DOC_LAYERS_CONVENTION.md`](./docs/DOC_LAYERS_CONVENTION.md).

**During a session:**

- After every subtask: run `pytest tests/ -v` before moving on.
  A subtask is not done until its tests are green.
- Write tests in the phase's `tests/` directory for every new function
  (mocked HTTP, no live network calls in unit tests).
- If any architectural decision changes, update the relevant concept doc in
  `docs/concepts/` immediately — not at the end of the session.

**Ending a session (mandatory):**

Before closing, append a `## Session stopped` block to the active phase's
`CLAUDE.md` (or the task's notes file if one exists, e.g.
`lightstreamer_integration_notes.md`). This is the handover to the next session.
Without it, context is lost and the next session starts cold.

```markdown
## Session stopped — <YYYY-MM-DD>

### Completed
- `<file>`: <what was done>

### Next
- <exact next step, specific enough to start without re-reading everything>

### Open questions / blockers
- <anything unresolved>
```

Replace or update this block at the start of each new session once read.

**Rotation rule (mandatory since 2026-07-06):** when appending the new `## Session stopped`
block, move the previously-newest block **verbatim** to the phase's `SESSIONS_ARCHIVE.md`
(newest-first). A phase `CLAUDE.md` carries exactly **one** session block; archives have no
size cap. New .md file created ⇒ add its one-liner to `docs/INDEX.md` in the same commit.

**When in doubt about scope or AI vs. code: default to code.**
The "AI as little as possible" principle resolves most ambiguity.

---

## Working style (how to act, not just what to do)

> Added 2026-07-06 (Fable-5 pass, Nikinger-approved): these calibrate judgment for capable
> models — they complement the rules above, they don't replace them.

- **Source-of-truth precedence: tested code > concept doc > README/status prose.**
  On conflict, trust the code, fix the doc immediately, and leave a dated note in the doc
  that it was corrected against code. Read docs first (cheaper), verify against code before
  building on a contract.

- **Act vs. ask.** Proceed without asking on reversible, in-phase steps that follow from the
  agreed plan — asking permission for routine in-scope work wastes the session. Stop and ask
  (the Nikinger decides) for: destructive or hard-to-reverse actions, cross-phase code edits,
  anything touching live (non-demo) money paths, and genuine scope changes.

- **Locked decisions stay locked.** Phase docs pin decisions and verified contracts
  (e.g. "Decision A–J" blocks). Don't re-litigate or silently "improve" them mid-implementation.
  If new evidence contradicts a locked decision, surface it as a finding and let the Nikinger
  decide — never deviate quietly.

- **Report outcomes faithfully.** If tests fail, say so and show the output. If a step was
  skipped, say that. When something is done and verified, state it plainly — no hedging,
  no "should work". A wrong "it works" costs more than an honest "it's broken";
  this project trades real money on the difference.

- **Root cause over symptom.** Before fixing a bug, find every caller of what you're about to
  touch; fix once at the shared point, not per reported symptom. The smallest diff in the
  wrong place is a second bug.

- **Read enough, then act.** Read the minimum needed (phase head + newest `## Session stopped`
  block first), but never skip comprehension of the code a change touches. Once you have
  enough information to act, act — don't re-derive facts already established in the session.

- **Handovers are written for a cold reader.** Lead with the outcome (what happened, what's
  next), spell out terms instead of session-local shorthand, and make the next step specific
  enough to start without re-reading everything.

- **Advisor usage (Claude Code, `/advisor` active).** Consult the Advisor in exactly these
  cases — no more, no less:
  1. **[VERIFY] mismatch:** the as-built code deviates from the plan's contract → ask the
     Advisor *before* reinterpreting it yourself, never adjust silently.
  2. **A test/gate keeps failing after 2–3 fix attempts** → consult the Advisor with the
     diff + error output instead of iterating further.
  3. **Before declaring a weekend block (Block A/B) done** → the Advisor checks against the
     plan's acceptance criteria + Definition of Done.

  Do NOT consult for: routine edits, locked decisions (they stay locked), or anything the
  plan already specifies exactly.

---

## Phase transitions

A phase is considered "done" when:
- All planned components exist
- Smoke test passes against the relevant environment (demo or local)
- Phase README documents what was built, known limitations, and integration points
- The next phase's concept document is ready in `docs/concepts/`

Phase transitions happen in the **Claude browser interface** (Konzept-Session),
not in Claude Code. Claude Code implements; Claude (browser) plans.

---

## Anti-patterns to flag

If you see any of these, stop and discuss with the human:

- LLM call inside a Gate, VETO, or sizing calculation
- Credentials in any file other than the keyring
- An AI output triggering an order without code-side validation
- A "temporary" hardcoded value that bypasses a check
- A test that hits the live (non-demo) IG account
- Force Trigger usage without checking Daily PNL
- Any direct broker call outside `broker_wrapper/` (always go through the wrapper)
- A subtask marked done without passing `pytest tests/ -v`
- A session ending without a `## Session stopped` block written
- A phase `CLAUDE.md` accumulating >1 session block (rotation rule skipped), or a
  new .md file missing from `docs/INDEX.md`
- Editing a 📕 dated snapshot (concepts, handovers, archives) instead of superseding it
