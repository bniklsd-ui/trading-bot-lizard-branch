---
status: live
purpose: Meta-Phase M1 head — Harness-Unabhängigkeit (Build-Front). Vorregistrierter Bake-off
  Claude Code vs. OpenCode + kalter P4/P6-Provider-Fallback. Orthogonal zum funktionalen Strang.
read-when: Arbeit an M1 — read this head + newest Session-stopped block first
detail: L2
up: ../docs/INDEX.md
down:
  - ../docs/concepts/meta_m1_harness_plan.md          # ausführungsreifer Plan (L3, Quelle der Schritte)
  - ../docs/concepts/meta_phase_unabhaengigkeit_konzept.md   # Hypothese/Theorie-Dokument (L3)
  - ./META_M1_PREREGISTRATION.md                      # Δ/P/K/E/M gelockt (Step 2)
updated: 2026-07-08
---

# Meta-Phase M1 — Harness-Unabhängigkeit — Claude Code context

## Project

Eine vorregistrierte Messung, ob der Bot-Code mit einem offenen Harness (OpenCode) statt
Claude Code gebaut werden kann — plus, unabhängig vom Ausgang, zwei Feuerlöscher: (a) ein
harness-neutraler Kontext-Einstieg (`AGENTS.md`), (b) ein getesteter, **kalter**
provider-agnostischer LLM-Fallback für P4/P6. **Kein Bot-Feature. Kein Umbau der Live-Pfade.**
Der Phase-9-Live-Test bleibt vollständig unberührt.

Eigener Meta-Strang „M" (orthogonal zur funktionalen Roadmap-Nummerierung 1–11), hochzählbar
(M2, M3, …). Voller Plan (Steps 0–10, Decisions M1-D1…D13): `meta_m1_harness_plan.md`. Volle
Hypothese/Theorie: `meta_phase_unabhaengigkeit_konzept.md`.

**⚠ Vorab bekannt (kein Bug):** mit den vorregistrierten Werten gilt E = 73,50 € < M = 120 € —
die Migrationsentscheidung ist bereits determiniert (KEINE Migration), unabhängig vom
Messergebnis. Der Bake-off läuft trotzdem voll durch — Zweck ist der Feuerlöscher-Test des
Build-Pfads, nicht Entscheidungsinput.

## Module-Tree (wächst mit den Steps)

```
meta_m1_harness/
├── CLAUDE.md                      ← dieser Kopf
├── META_M1_PREREGISTRATION.md     ← Step 2 (Δ/P/K/E/M gelockt, vor jedem Trial committet)
├── specs/                         ← Step 3 (S0–S7, self-contained Trial-Prompts)
├── bakeoff/                       ← Step 4 (harness_bakeoff.py, analyze.py, preamble.txt)
├── tests/                         ← Step 4 (mocked, kein Subprocess/Netz)
└── results/                       ← Step 7+ (trials.jsonl, META_M1_RESULTS.md, META_M1_DECISION.md)
```

## Status

✅ Steps 0–4 fertig, getestet, `meta-m1-harness` per Fast-Forward in `phase9-v2-foundation`
gemergt; aktiver Branch jetzt **`meta_working`**. Fork lebt unter `~/bakeoff/trading-bot-fork`,
`base-0` (Keyring neutralisiert). **Setup-Smoke S0: claude_code ✅ grün, opencode ❌**
(OpenCode ist schlicht noch nicht installiert/auf PATH — `[Errno 2] No such file or
directory: 'opencode'`, **kein** M1-D3-Fall von „irreparabel rot"). **✅ Step 6
(Referenz-Build S1–S7 im Fork) fertig** — `base-1`…`base-7` getaggt, jedes Gate beim
Committen grün, volle Cross-Phase-Regression im Fork danach bestätigt grün. Nächster
Schritt braucht OpenCode-Install (Step 7, der gemessene Bake-off).

## Session stopped — 2026-07-08 (Steps 0–6 fertig, Branch `meta_working`, Step 7 gegatet auf OpenCode-Install)

### Completed
- **Step 0** (`0c5773e`): Phasen-Skeleton (`meta_m1_harness/CLAUDE.md`) + INDEX-Einträge für
  alle drei M1-Quelldokumente (Plan, Konzept, Kickoff-Handover) + eine vierte, unabhängige
  Idee-Notiz (`market_snapshot_middleman_konzept.md`), die zeitgleich vom Nikinger eingefügt
  wurde.
- **Step 1** (`c936945`): Legacy-Grep sauber (nur bekannter `turbo_candidates.json`-Rest).
  Voller Regressions-Baseline **grün** und deckungsgleich mit dem Plan: P1 87 · P2 76 ·
  P3 100 · P4 141 · P5 154 · P6 70 · P7 133 · P8 217 · P9 72 · root 77 — eigene Memory
  (`reference_running_phase_tests.md`) mit dem frischen Stand aktualisiert. **Echte Doku-
  Drift gefunden und gefixt:** ROADMAP Phase-9-Checkliste stand komplett auf `[ ]`, obwohl
  Steps 1–6+7a längst als ✅ im Phasenkopf standen — Boxen korrigiert, `LiveQuoteCache`-
  Wiring bewusst offen gelassen (echt noch nicht verdrahtet, per grep verifiziert).
  ARCHITECTURE.md nannte Migration 004 fälschlich "planned, not yet built" — korrigiert.
  ROADMAP-Meta-Strang-Sektion + V2-Baseline-Merker ergänzt.
- **Step 2** (`796f96f`): `META_M1_PREREGISTRATION.md` — Δ=10pp, P=0,35, K=210€, E=73,50€,
  M=120€, Migrationsregel, Rausch-Regel, Messdesign. Verbatim aus Konzept §1/§3/§4, vor
  jedem Trial committet (Git-History = Anti-Shopping-Beweis).
  **⚠ Auffälligkeit:** dieser Commit landet auf einem lokalen Feature-Branch, nicht auf
  `main` — die "Git-History als Beweis"-Eigenschaft des Preregistration-Locks hält nur,
  solange der Branch nicht umgeschrieben/gerebased wird, bevor der erste Trial läuft.
- **Step 3** (`769f2b8`): Specs S0–S7 (Abstain-/No-Trade-Lessons-Testfeld) — self-contained,
  verbatim aus dem Plan transkribiert. Ein Selbstwiderspruch beim ersten Entwurf der S2-Gate-
  Mapping-Zeile wurde noch in derselben Bearbeitung bemerkt und bereinigt (G2→NO_CANDIDATES
  ist jetzt eindeutig, ohne die widersprüchliche erste Fassung).
- **Step 4** (`74611b0`): `harness_bakeoff.py` + `analyze.py` + `preamble.txt` + 19 gemockte
  Tests, alle grün. `--dry-run` live gegen dieses Repo verifiziert: druckt die volle
  20-Trial-Matrix (S1–S5 × 2 Repeats × 2 Harnesse) mit korrekten `base-N`-Tags,
  Step-major/Harness-alternierend, **ohne** ein einziges subprocess/git-Kommando
  auszulösen (per Test **und** per echtem Lauf bestätigt).
- **Post-Step-4-Korrekturen** (`be4b7d7`, gleiche Session, Nikinger-Feedback): (a) Harness-
  Templates auf `claude-sonnet-5`/`--effort medium` (Claude Code) bzw.
  `anthropic/claude-sonnet-5`/`--variant <VERIFY>`/`--format json`/`--auto` (OpenCode)
  präzisiert — verifiziert gegen `claude --help` (diese Session) + OpenCode-Docs (WebFetch).
  (b) **Auth-Override:** M1-D5s ursprüngliches „`ANTHROPIC_API_KEY` als Bake-off-Shell-Env"
  vom Nikinger verworfen — **kein Key je in einer Env-Var oder Datei**, auch nicht
  experimentell. Stattdessen derselbe Keyring-Ansatz wie beim Bot: neues
  `store_bakeoff_key.py` (Service `trading-bot-bakeoff-runner`, dediziert, getrennt vom
  Live-Service `tradingbot` und vom fork-neutralisierten `trading-bot-bakeoff-void`);
  `harness_bakeoff.py` holt den Key pro Subprocess-Call frisch aus dem Keyring, gibt ihn
  nur ins jeweilige Subprocess-Environment. Plan-Doc an allen drei betroffenen Stellen mit
  datierten Strikethrough-Korrekturen versehen (nicht stillschweigend umgeschrieben). 21
  Tests grün.

- **Post-Setup-Smoke-Fixes** (`7107913`, `0bf5ccd`, gleiche Session): zwei echte Bugs aus dem
  ersten realen S0-Lauf gefunden und gefixt. (a) `_prompt_operator_for_manual_spend` crashte
  auf deutsches Komma-Dezimal (`0,22` → `ValueError`) — normalisiert jetzt Komma→Punkt +
  re-prompted statt abzustürzen (ein Absturz hätte einen bereits ausgeführten, bereits
  bezahlten Trial ergebnislos verworfen). Verifiziert: der Fork blieb trotz Absturz sauber
  auf `base-0` — der `finally: reset_to(...)`-Guard hielt. (b) **Echter Messfehler:**
  `changed_files()` nutzte nur `git diff --name-only`, das neue **untracked** Dateien
  (Harnesse committen laut Preamble nicht) unsichtbar macht — der claude_code/S0-Trial zeigte
  `gate_passed=true, files_changed=0`, ein Widerspruch. Hätte `edit_failures` (eine
  Kernmetrik) bei jedem Harness, der etwas schreibt aber am Gate scheitert, fälschlich auf 1
  gesetzt. Fix: Union aus `git diff` (tracked) + `git ls-files --others --exclude-standard`
  (untracked). 3 neue Tests gegen ein echtes Wegwerf-Git-Repo (nicht gemockt). 27 Tests grün.

- **Step 6 — Referenz-Build S1–S7, komplett** (im Fork, eigene Commits/Tags dort, nicht in
  diesem Repo): Claude-Code-only, normale Subscription-Session, kein API-Spend. Je Spec:
  implementieren → Gate exakt wie in der Spec → Commit → `git tag base-<k>`.
  - **S1** Modelle+Taxonomie (5 Tests) · **S2** Klassifizierer (19 Tests, table-driven, alle
    12 Reasons) · **S3** `AbstainStore` (5 Tests, eigene sqlite3-Connection, kein
    P2-Migrationsframework) · **S4** `reflect_abstain` (6 Tests, die einzige AI-Naht,
    default aus) · **S5** Sink + Executor-Wiring (**der härteste Trial**, Cross-File-Edit in
    `phase5_execution/`: `abstain_sink`-Param gehängt an `_no_trade()`, den einen
    Choke-Point, den alle 8 NO_TRADE-Pfade schon durchlaufen — volle P5-Regression **vor**
    neuen Tests bestätigt unverändert grün (154), dann +4+3 = 161) · **S6**
    Research-Prompt-Injektion (`include_abstain_lessons`-Flag in `build_prompt()`,
    **bewusst vom Spec-Wortlaut abgewichen** — `AbstainStore`-Fetch bleibt außerhalb, da
    `build_prompt` explizit "no I/O" dokumentiert; P4-Regression vorher 141, danach 144) ·
    **S7** Report-CLI (2 Tests, Golden-Output, standalone smoke-verifiziert).
  - **Echter Bug live gefunden + gefixt:** die geteilte venv's editable Install von
    `research` zeigt fest auf das **Original-Repo**, nicht den Fork — nur weil S6s eigenes
    Gate-Kommando `phase4_research/tests/` mit einschließt, wurde das per
    pyproject.toml-Sys.path-Insertion zufällig überdeckt. `phase10_v3/tests/conftest.py`
    erzwingt jetzt zusätzlich den fork-lokalen `phase4_research/`-Pfad — Root-Fix, nicht nur
    Symptom (jedes einzelne Spec-Gate war für sich schon robust, aber `pytest
    phase10_v3/tests/` als Ganzes vorher nicht). `base-7` per `git tag -f` auf den Fix
    vorgezogen.
  - **Volle Cross-Phase-Regression im Fork danach:** P1 87 · P2 76 · P3 100 · P4 144 ·
    P5 158 · P6 70 · P7 133 · P8 217 · P9 72 · phase10_v3 43 · root 77 — alles grün.

### Next
- **Step 7** (der eigentliche gemessene Bake-off) braucht zuerst: OpenCode tatsächlich
  installiert und auf PATH (`curl -fsSL https://opencode.ai/install | bash` oder
  `npm i -g opencode-ai@latest`), danach S0 für opencode erneut grün bekommen; `--variant`-
  Wert gegen die installierte Instanz verifizieren. Danach:
  `python meta_m1_harness/bakeoff/harness_bakeoff.py --repo ~/bakeoff/trading-bot-fork
  --steps S1,S2,S3,S4,S5 --harness claude_code,opencode --repeats 2` (außerhalb des
  Handelsfensters, Budget-Cap 50 €).
- Branch `meta_working` (ab `phase9-v2-foundation`, `meta-m1-harness` per FF gemergt) ist der
  aktive Arbeits-Branch; alle Step-6-Commits/Tags leben nur im Fork, nicht hier.

### Open questions / blockers
- `V2-Baseline-Auswertung` (echter Trade + Variety-These) bleibt offen, orthogonal, kein
  M1-Blocker (Merker in ROADMAP §Phase 9 hinterlegt).
- OpenCode-Installationsstatus unklar (Operator-Prereq, s. o.) — einziger Blocker vor Step 7.
