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

**Active phase:** Phase 4 — Research (LLM candidate selection): ✅ abgeschlossen +
live-verifiziert. Phase-5-Konzept (ig_bot Gates 1–5) ausstehend (Browser-Konzept-Session
leitet den Phasenwechsel ein — nicht hier in Claude Code).

**Phase 4 status:** ✅ Abgeschlossen + live-verifiziert (2026-06-08)
- 88 Unit-Tests grün (gemockt, `_raw_call` der einzige mockbare LLM-Punkt — kein
  Netzwerk, kein `anthropic`-Import im Unit-Run; `test_validator.py` 18 ≥ 12) +
  live-verifiziert via `phase4_research/scripts/live_test.py` → `RESULT: 3/3 passed`
  gegen IG Demo + realen LLM-Call (run() ohne Exception, 1-Save-Invariante,
  Abstain → leere Liste). `smoke_test.py` als DRY-Sanity vorgeschaltet.
- **Einziger AI-Schritt** = `llm_client.ask_candidate` ("welcher Kandidat?"). Alles
  andere ist Code: Context-Assembly (P1/P2/P3), Validator (Halluzinations-Guard),
  `candidate_filter` (das reale Gate), Persistenz, Retry. LLM-Output erreicht **nie**
  `open_position` ohne Validator + Filter; LLM-`confidence` ist Rohdatum, **nicht** das
  Gate (Phase 7 ankert es an Outcomes).
- Code in `phase4_research/` (importiert nichts aus Phase 1/2/3 zur Laufzeit — nur
  via `scripts/wiring.py`-Bootstrap; Phasen-Isolation) · Konzept in
  `docs/concepts/phase4_research_plan_konzept.md` · Candidate-Persistenz in
  gitignored Root-`data/state/turbo_candidates.json` (Legacy-Name, TTL 30 min);
  Token-/Kosten-Log in `data/state/llm_usage.json` (gitignored).
- Erkenntnis (Code = Source of Truth, Konzept §4 annotiert): **Anthropic Structured
  Outputs lehnen JSON-Schema-Type-Arrays ab** (`{"type": ["string","null"]}` → HTTP
  400) — der Code nutzt `anyOf` für nullable Enums; numerische Constraints
  (`minimum`/`maximum`) sind ebenfalls nicht unterstützt → der `confidence`-Bereich
  wird vom Validator durchgesetzt. Baseline-Tag vor dem Fix: `phase4-pre-schema-fix`.

**Phase 3 status:** ✅ Abgeschlossen + live-verifiziert (2026-06-02)
- 70 Unit-Tests grün (gemockt, `_raw_download` monkeypatched — kein Netzwerk) +
  live-verifiziert via `phase3_external_data/scripts/live_test.py --clear-cache`
  → `RESULT: 6/6 passed` gegen reales yFinance `^GDAXI` (Konnektivität, Daily-
  Indikatoren, Markt-Regime-Verzweigung, Cache-Hit, Rate-Limiter-Abstand,
  `get_brain_context`-Toleranz). ETF-Volume-Proxy-Pfad via `--volume-proxy EXS1.DE`
  bestätigt (`volume_available=True`, `volume_source=EXS1.DE`, `today_volume>0`).
- 100 % Code, **kein LLM-Call** (Bauprinzip). yFinance liefert Rohwerte, Code rechnet
  Drift/Momentum/Volume-z/HighLow. Einziger Netzwerk-Punkt: `fetcher._raw_download`.
- Code in `phase3_external_data/` (importiert nichts aus Phase 1/2 — Phasen-Isolation)
  · Plan/Konzept in `docs/concepts/phase3_external_data_konzept.md`
- Runtime-Cache in gitignored Root-`data/cache/*.json` (TTL: 1d bis Mitternacht
  Europe/Berlin · 5m 120 s · 30m 300 s)
- ⚠ **Phase-5-Flag:** `get_momentum()` ist ~15 min verzögert (yFinance Delayed Quote) —
  ein **Kontext-Signal**, KEIN harter Momentum-VETO. Der VETO gehört in Phase 5 an
  Phase-1/IG-Echtzeit-Bars (siehe `phase3_external_data/CLAUDE.md` + Konzept §13).
- Erkenntnisse (Code = Source of Truth, Konzept entsprechend annotiert): `get_bars`
  ist `list[PriceBar] | None` (Off-Hours-Disziplin, §11); der Live-Rate-Limiter-Check
  provisioniert sich einen frischen Temp-Cache statt `--clear-cache` zu brauchen (§17.2)

**Phase 2 status:** ✅ Abgeschlossen + live-verifiziert (2026-05-22)
- 59 Unit-Tests grün (gemockt) + live-verifiziert via `phase2_persistence/scripts/live_test.py`
  (Durability über Prozess-Neustart, Candidates-TTL-Selbstlöschung, Phase-1→Phase-2
  Integration gegen IG Demo)
- Code in `phase2_persistence/` · Konzept in `docs/concepts/phase2_persistence_konzept.md`
- Runtime-Daten in gitignored Root-`data/` (`trading_bot.sqlite` + `state/*.json`),
  angelegt via `scripts/init_db.py`
- Erkenntnis (Code = Source of Truth): `get_open_positions().data` ist ein Dict
  `{"positions": [...]}`, keine blanke Liste — Konzept-Beispiel entsprechend korrigiert

**Phase 1 status:** ✅ Abgeschlossen
- Live-verifiziert gegen IG Demo · smoke_test PASS inkl. `--order`
- Confirmed epic: `IX.D.DAX.IFMM.IP` — Deutschland 40-Kassa (1 €/Punkt), EUR, min_deal_size: 0.5
- Code in `phase1_broker_wrapper/` · Konzept in `docs/concepts/phase1_broker_api_konzept.md`
- Lightstreamer client live-getestet gegen IG Demo (offizielles `lightstreamer-client-lib`
  SDK, `PRICE`-Feed) — CONOK/SUBOK + Live-Ticks bestätigt am 2026-05-21; Polling-Client
  bleibt als Fallback → Notes: `phase1_broker_wrapper/lightstreamer_integration_notes.md`
- IG Europe GmbH Live-Account noch ausstehend (vor Production-Go-Live kritisch)

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

**When in doubt about scope or AI vs. code: default to code.**
The "AI as little as possible" principle resolves most ambiguity.

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
