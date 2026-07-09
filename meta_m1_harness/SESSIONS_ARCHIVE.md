---
status: archive
purpose: Verbatim history of superseded `## Session stopped` blocks from meta_m1_harness/CLAUDE.md.
  Rotated in on every new session-stopped write per the repo's Doc-Layers rotation rule.
read-when: auditing M1 history; never at session start
detail: L3
up: ./CLAUDE.md
updated: 2026-07-08
---

# meta_m1_harness — Session Archive (newest-first)

## Session stopped — 2026-07-08 (OpenCode S0 zweimal real gelaufen, kritischer Isolationsbefund gefixt, Step 7 noch nicht gestartet)

**Vorherige Session** (Steps 0–6, alle Details): siehe unten in dieser Datei.

### Completed
- **PATH/Auth/Effort/Variant geklärt** (uncommitted, `harness_bakeoff.py`): OpenCode-Binary
  lauffähig, aber nicht automatisch auf PATH in non-interaktiven Shells (`.bashrc`-Export gilt
  nur interaktiv) — Fix ist PATH beim Runner-Aufruf erweitern, kein Code-Change. Env-Var-Auth
  empirisch bestätigt: `ANTHROPIC_API_KEY` nur im Subprocess-Env (aus dem Keyring, nie in eine
  eigene Shell exportiert) reicht für OpenCode, **kein** `/connect`/`auth.json`-Schreiben nötig
  — M1-D5 hält. `--variant`/`--effort` **korrigiert von `medium` auf `high`** (Nikinger, gegen
  docs.claude.com verifiziert: Sonnet 5 defaulted bei ungesetztem Effort auf `high`, nicht
  `medium` — das ist die reale Projekt-Execution-Config, die M1-D4 referenziert). Plan-Doc
  (`meta_m1_harness_plan.md`, M1-D4 + §8 Schritt 4) mit datierten Strikethrough-Korrekturen
  versehen.
- **Kosten-Parsing automatisiert** (echter Bug, live gefunden): weder `CLAUDE_CODE` noch
  `OPENCODE` hatten ein `usage_regex` gesetzt → jeder Trial löste den interaktiven
  Manual-Spend-Prompt aus, der auf `input()` mit geschlossenem stdin (Skript-Aufruf ohne
  Operator) sofort mit `EOFError` abstürzte — **nach** bereits real bezahltem Harness-Call, das
  Ergebnis ging komplett verloren, und die Matrix brach für alle Folge-Trials ab. Fix: beide
  Harnesse parsen jetzt ihre eigene autoritative Kosten-Angabe direkt aus dem JSON-Output
  (`total_cost_usd` bei Claude Code, `cost` je `step_finish`-Event bei OpenCode, `findall`+Summe
  statt `search`-erstes-Match, da OpenCodes NDJSON mehrere Steps haben kann) — kein manueller
  Prompt mehr nötig im Normalfall. `_prompt_operator_for_manual_spend` fängt jetzt zusätzlich
  `EOFError` ab (0.0 loggen statt Trial+Restlauf verlieren) als Fallback-Härtung. Trial-Logging
  neu (`_write_trial_log`, `results/logs/*.log`) — vorher wurde stdout/stderr nach dem
  Regex-Parse komplett verworfen, keine Post-Mortem-Möglichkeit.
- **🔴 Kritischer Isolationsbefund (live gefunden, M1-D8 betroffen):** der erste echte
  OpenCode/S0-Retry lief durch (`exit_ok=true`), aber `gate_passed=false, files_changed=0` —
  Trial-Log zeigt: der OpenCode-Agent führte in seinem eigenen Bash-Tool
  `cd /home/trading-bot/trading-bot && pytest ...` aus — **das Live-Repo, nicht den Fork** —
  trotz korrekt gesetztem Subprocess-`cwd=<fork>`. Der Agent schrieb `phase10_v3/smoke.py` +
  `phase10_v3/tests/test_smoke.py` real in dieses Live-Repo (nie committet, sofort per
  `rm -rf phase10_v3/` entfernt, verifiziert: kein Rest, kein Git-Tracking). Root Cause:
  Subprocess-`cwd` allein ist **keine** harte Sandbox-Grenze für einen Agenten mit eigenem
  Shell-Zugriff — er kann mit einem absoluten Pfad herausnavigieren. **Zwei-Schichten-Fix:**
  (a) `--dir {repo}` zum `OPENCODE`-argv-Template hinzugefügt (OpenCodes eigenes
  Scoping-Flag, fehlte vorher komplett); (b) neuer OS-Level-Lockdown
  (`_live_repo_lockdown()`/`_restore_permissions()`): entfernt das Write-Bit von jeder
  Datei/jedem Verzeichnis im Live-Repo für exakt die Dauer jedes Harness-Subprocess-Calls
  (echte OS-User-Permission, kein Convention-Only-Schutz) — als Backstop für **beide**
  Harnesse, nicht nur OpenCode, falls Claude Code mit `--dangerously-skip-permissions`
  dasselbe je täte. Getestet (28 Tests grün, inkl. neuem
  `test_live_repo_lockdown_strips_and_restores_write_bit`, echter `PermissionError`
  gegen ein `tmp_path`) und per `--dry-run` gegen die echte Argv-Templatisierung verifiziert
  (`--dir` löst korrekt zum Fork-Pfad auf) — **aber noch nicht gegen einen echten Lauf
  bestätigt**, das war explizit der nächste Schritt, den der Nikinger selbst übernimmt.
- Live-Repo-Kontamination entfernt (`rm -rf phase10_v3/`, war nie committet).
- Zwei echte S0-Trials liefen real (claude_code: gate grün, 4 Dateien, $0.50; opencode: beide
  Versuche `gate_passed=false` aus dem oben beschriebenen Grund, $0.16 + $0.08) —
  `results/trials.jsonl`/`results/logs/` sind bewusst weiterhin uncommitted (Rohdaten, kein
  Bestandteil des vorregistrierten S1–S5-Messlaufs, S0 ist laut Spec "ungemessen").

### Next
- **Der Nikinger führt den nächsten echten S0-Retry selbst aus** (Session-Entscheidung: nicht
  unbeaufsichtigt lassen, falls Kosten durch unerwartetes Verhalten eskalieren):
  ```
  export PATH="/home/trading-bot/.opencode/bin:$PATH"
  python meta_m1_harness/bakeoff/harness_bakeoff.py --repo ~/bakeoff/trading-bot-fork \
    --steps S0 --harness claude_code,opencode --repeats 1
  ```
  Erwartung: `opencode`-Trial bleibt jetzt im Fork (per `--dir` + Lockdown-Backstop),
  `gate_passed=true`. Falls wieder ein Live-Repo-Escape auftritt (`git status --porcelain`
  im Live-Repo nach dem Lauf prüfen) — sofort stoppen, nicht weiterlaufen lassen, M1-D3
  „irreparabel rot"-Frage neu aufwerfen.
- Sobald S0 für **beide** Harnesse sauber grün ist (im Fork, nicht im Live-Repo): **Step 7**
  (der gemessene Bake-off):
  `python meta_m1_harness/bakeoff/harness_bakeoff.py --repo ~/bakeoff/trading-bot-fork
  --steps S1,S2,S3,S4,S5 --harness claude_code,opencode --repeats 2` (außerhalb des
  Handelsfensters, Budget-Cap 50 €, jetzt mit automatischem Kosten-Parsing — kein manuelles
  Eintippen von 20 Spend-Werten mehr nötig).
- Branch `meta_working` ist der aktive Arbeits-Branch; alle Step-6-Commits/Tags leben nur im
  Fork, nicht hier. Die Code-Fixes dieser Session (`harness_bakeoff.py`,
  `tests/test_bakeoff_runner.py`, `CLAUDE.md`, `docs/concepts/meta_m1_harness_plan.md`) sind
  **uncommitted** — Commit steht noch aus (Nikinger-Entscheidung, ob vor oder nach dem
  nächsten S0-Retry).

### Open questions / blockers
- Der `--dir`+Lockdown-Fix ist unit-getestet, aber **nicht** gegen einen echten OpenCode-Lauf
  bestätigt — das ist der unmittelbare nächste Schritt (s. o.), bewusst dem Nikinger überlassen.
- `V2-Baseline-Auswertung` (echter Trade + Variety-These) bleibt offen, orthogonal, kein
  M1-Blocker (Merker in ROADMAP §Phase 9 hinterlegt).

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
- **OpenCode ist bereits installiert** (2026-07-08, Nikinger bestätigt) — global unter
  `~/.opencode/bin/opencode` (v1.17.15, **nicht** in der Python-venv — es ist kein
  Python-Paket, braucht keine `pip install`). `~/.bashrc` trägt bereits
  `export PATH=/home/trading-bot/.opencode/bin:$PATH` (Zeilen 121–122) — ein frisches
  Terminal (oder `source ~/.bashrc`) sollte reichen. **[VERIFY nächste Session]:** `which
  opencode` in einer echten interaktiven Shell bestätigen, dann Setup-Smoke S0 für opencode
  erneut versuchen (`--variant`-Wert gegen `opencode run --help` prüfen, war noch offen).
- **Step 7** (der eigentliche gemessene Bake-off), sobald S0 für **beide** Harnesse grün ist:
  `python meta_m1_harness/bakeoff/harness_bakeoff.py --repo ~/bakeoff/trading-bot-fork
  --steps S1,S2,S3,S4,S5 --harness claude_code,opencode --repeats 2` (außerhalb des
  Handelsfensters, Budget-Cap 50 €).
- Branch `meta_working` (ab `phase9-v2-foundation`, `meta-m1-harness` per FF gemergt) ist der
  aktive Arbeits-Branch; alle Step-6-Commits/Tags leben nur im Fork, nicht hier.

### Open questions / blockers
- `V2-Baseline-Auswertung` (echter Trade + Variety-These) bleibt offen, orthogonal, kein
  M1-Blocker (Merker in ROADMAP §Phase 9 hinterlegt).
- Kein echter Blocker mehr vor Step 7 — nur noch die S0-Re-Verifikation für opencode (s. o.).
