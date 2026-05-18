# CLAUDE.md — Project Instructions

> Read this file before doing anything in this repository.
> It is the single source of truth for project rules, conventions, and current state.

---

## What this project is

A multi-phase, AI-augmented options trading bot for the DAX.
Primary broker: IG Markets (HTADU account, GBX). Multi-broker abstraction in place.

The bot is structured around a **5-Gate Execution Pipeline** with adversarial
AI-driven direction decisions (Bull/Bear/Judge debate) and a deterministic VETO
cascade. Performance baseline (reference architecture): 2–4% PNL/Trade,
58.700 GBP balance.

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

**Active phase:** Phase 1 — Broker API Wrapper
**Subpath:** `phase1_broker_wrapper/`

Code exists but is **untested against the live IG demo account**. Next concrete
work: run `python scripts/smoke_test.py` against the demo, fix anything that
breaks, document IG-specific quirks discovered in the process.

Known open items inside Phase 1:
1. Lightstreamer streaming client is a skeleton — polling client works as fallback
2. IG REST endpoints are written from public docs, not yet live-verified
3. DAX CFD epic strings are not hardcoded — use `search_markets()` to discover
4. Trade-history parsing is best-effort; cross-check against a known closed deal

See `phase1_broker_wrapper/README.md` for full Phase-1 specifics.

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
│   │   └── phase1_broker_api_konzept.md
│   ├── architecture/
│   │   ├── tradingbot_v2_architecture.svg
│   │   └── tradingbot_v2_architecture.pdf
│   └── sessions/                           ← (optional) chat session summaries
│
├── phase1_broker_wrapper/                  ← Phase 1 code (untested)
├── phase2_persistence/                     ← (future)
├── phase3_external_data/                   ← (future)
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

When starting a new Claude Code session:

1. Confirm which phase is active (check this file, top section "Current state")
2. Read the relevant phase README (e.g. `phase1_broker_wrapper/README.md`)
3. Check `git status` and `git log -5` to understand recent work
4. Run existing tests before making changes (`pytest tests/ -v`)
5. After changes: run tests, update phase README if anything new was learned

When in doubt about scope or whether to use AI vs. code: **default to code**.
The "AI as little as possible" principle is the single most important
architectural rule and should resolve most ambiguity.

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
