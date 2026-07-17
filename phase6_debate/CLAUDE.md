---
status: closed-phase
purpose: Phase-6 head — Bull/Bear/Judge debate, 11 locked decisions A–K, debate_runner seam
read-when: working in phase6_debate/ — read this head + its newest Session-stopped block first
detail: L2
up: ../CLAUDE.md
down:
  - ./SESSIONS_ARCHIVE.md      # full session history (L3)
  - ./README.md
  - ../docs/concepts/phase6_debate_concept.md   # full concept/plan snapshot (L3)
updated: 2026-07-17
---
# CLAUDE.md — Phase 6: Bull/Bear/Judge-Debatte (`phase6_debate/`)

> Erster Mehr-Agenten-AI-Pfad + **teuerster Pfad im System**. Kostenkorrektheit
> (Caching + Metering + Caps) wiegt hier so schwer wie Funktionsumfang.
> **Quelle der Wahrheit ist der Code, nicht dieses Dokument.**
> Vollständiges Design + alle 11 gelockten Entscheidungen (A–K):
> `../docs/concepts/phase6_debate_concept.md`.

## AI-Grenze (Projekt-Kernprinzip)
„So wenig AI wie möglich, so viel AI wie nötig." Phase 6 fügt AI **nur** für
**Bull/Bear-Argumente + Judge-Synthese** hinzu (finale Richtung + TRADE/ABSTAIN).
ALLES andere ist deterministischer Code: Kontextaufbau, Caps/Budget, Persistenz,
Fehlerbehandlung. Die Debatte bekommt **niemals** den Broker oder eine VETO-/Gate-
Funktion in die Hand — sie liefert nur Richtung/ABSTAIN und kann **keinen** VETO /
kein Gate überschreiben (strukturell kein Force-Trigger: sie referenziert sie nicht).

## Harte Regeln (nicht verhandelbar)
- `confidence` ist **ADVISORY und gatet NICHTS** (Decision H). Nur das qualitative
  Judge-`decision ∈ {TRADE, ABSTAIN}` entscheidet. Wer später eine numerische
  Confidence-Schwelle einbauen will → **stop**, das ist genau das Anti-Pattern
  (ECE ~0.1, unkalibriert), das Decision H ausschließt. Die Zahl wird nur fürs
  P7-Outcome-Anchoring geloggt.
- Jeder Fehler / Cap-Breach / Context-Fehler an **jeder** Stelle → **ABSTAIN →
  NO_TRADE** (fail-closed, geloggt). Nie „trotzdem traden", nie eine Exception nach außen.
- **Caching AN** (`cache_system=True`); der Meter MUSS die Cache-Felder loggen —
  sonst ist die teuerste Optimierung der Phase **unsichtbar**. `usage_report` zeigt
  Cache-Hit-Ratio + Σ-Kosten pro Debatte.
- **Harte Caps** auf Calls **und** kumulative Tokens **und** Wall-Clock pro Zyklus.
  Breach → ABSTAIN (nie „trotzdem").
- `turbo_candidates.json` **NICHT anfassen/umbenennen** (frozen P2/P5-Contract).
  Der Candidate wird nach Gate 2 **nur in-memory** angereichert.
- **DB read-only** (bis P7). Kein SQLite-Schreiben — nur `data/state/debate_log.json`
  (gitignored, vorwärtskompatibel zu den P9-Tabellen `decision_context` /
  `market_regime_snapshots`).
- Richtung ist **BUY/SELL** only. Kein `CALL`/`PUT`/`strike`/`otm`/`issuer`/`FLIP`/
  `option_check`/`turbo` im Paket (Step 0). Englisches „call/put" nur als Prosa
  vermeiden (in Docstrings „invocation"/„request"); `*_call(s)`-Identifier sind ok.
- Logging → **stderr**; stdout nur maschinenlesbares JSON. Atomic commits. Kein
  Subtask „done" ohne grünes `pytest` (gemockt, **kein Netz, KEIN echtes LLM** in Unit-Tests).
- **Cross-Phase-Reuse** (`research.LLMClient` / `research.token_meter` / Pricing) ist
  die **dokumentierte Ausnahme** (Decision F) — im Modul-Docstring benannt, nicht versteckt.
- **Commit ⇒ Note-Update (zwingend, auch auf direkte Anweisung).** Jeder Commit, der ein
  Modul/einen Step abschließt, **muss** im selben Commit den Status (Datei-/Modul-Tabelle
  „⏳→✅") **und** den `## Session stopped`-Block dieser Datei aktualisieren — der „Nicht
  committet"-Hinweis im Handover wird auf „committet `<sha>`" geflippt. Das gilt **auch**, wenn
  der User „commit" sagt, **ohne** ein Note-Update zu erwähnen: erst die Note synchronisieren,
  dann committen (Note im Commit enthalten). Grund: wiederkehrendes Problem — Step committet,
  aber das Handover behauptet weiter „nicht committet" und die nächste Session startet auf
  falschem Stand. Wenn ein Commit *kein* Step-Abschluss ist (z. B. WIP), das im Block vermerken.

## Die 11 Entscheidungen (A–K, gelockt)
| # | Thema | Festlegung |
|---|---|---|
| **A** | Platzierung | Debatte als injiziertes `debate_runner`-Callable **zwischen Gate 2 und Gate 3** in `executor.run()`. Minimale P5-Edit erlaubt. **Neuer Konstruktor-Arg default = No-Op-Passthrough** → P5 ohne Runner AI-frei + alle P5-Tests grün. |
| **B** | Override | Debatte ist die **echte Richtungsquelle**: Judge emittiert finale `direction`, die vom P4-Seed **abweichen darf** (Flip BUY↔SELL). P4-Candidate = Seed + Epic + Kontext. |
| **C** | Modell pro Rolle | Bull/Bear default **`claude-haiku-4-5-20251001`** ($1/$5), Judge default **`claude-sonnet-4-6`** ($3/$15). Alle drei config-überschreibbar. |
| **D** | Client-Form | **Single-shot beibehalten** (`research.LLMClient.ask_candidate(system, user, json_schema)` pro Agenten-Turn). Transkript in den `user`-Content serialisiert; **kein** Multi-Turn-Umbau (maximiert Cache-Reads am stabilen Präfix). |
| **E** | Runden | **Early-Stop**: `max_rounds=5`, Judge bricht bei Konsens früher ab. Harte Caps auf Calls/Tokens/Wall-Clock. Jede Cap-Überschreitung → **ABSTAIN**. |
| **F** | Geteilte Infra | Phase 6 **importiert `research.token_meter` + Pricing + `LLMClient`** als dokumentierte Phasen-Ausnahme. Keine vorzeitige `llm_common`-Extraktion. |
| **G** | token_meter | Record **additiv** um `cache_read_input_tokens` + `cache_creation_input_tokens` erweitern (alte Felder bleiben → kein Bruch des „frozen"-Kontrakts). `usage_report` zeigt Cache-Hit-Ratio. **P4-Tests erneut grün.** |
| **H** | Confidence | Judge emittiert qualitatives `decision ∈ {TRADE, ABSTAIN}`. `confidence` wird **nur geloggt**, gatet **nichts** — auch keine Schwellen-Abstain. |
| **I** | Persistenz | **Kein SQLite** (DB read-only bis P7). In-memory ans Result + **JSON-Audit** `data/state/debate_log.json` (gitignored). Schema vorwärtskompatibel zu P9. |
| **J** | Fail-closed | API-Timeout/Fehler/Cap-Breach → **ABSTAIN → NO_TRADE**. `debate_runner` bekommt **strukturell nie** Broker oder VETO-Funktionen. |
| **K** | Council | `verbesserungsvorschlaege` (Council-Skill) = **Phase 9**, nicht jetzt. P6 baut nur die saubere Naht. |

## Modell-Split
Bull/Bear = **Haiku 4.5** (`claude-haiku-4-5-20251001`), Judge = **Sonnet 4.6**
(`claude-sonnet-4-6`), alle config-überschreibbar (`model_bull`/`model_bear`/
`model_judge`). Pricing-Rows existieren bereits in `ResearchConfig.pricing_usd_per_mtok`.

## Geerbte Contracts (Repo = Wahrheit — vor dem Bauen je [VERIFY] prüfen)
- **Naht in `phase5_execution/execution/executor.py`** (gelesen, `executor.py:148`):
  nach Gate 2 liefert `gate_load_candidates(self.state, self.research_runner, self.config)`
  ein `candidate`-**dict** (`epic, direction("BUY"|"SELL"), llm_confidence, reasoning,
  spread_pct_at_pick, drift_at_pick|None, score_at_pick, threshold_applied, generated_at,
  source`). Genau hier injiziert P6 den `debate_runner`.
- **`research.LLMClient`** (Phase 4): `LLMClient(model, api_key, *, max_tokens, temperature,
  timeout_s, token_meter_path=None, config=None, enable_thinking=False)` ·
  `ask_candidate(system, user, json_schema) -> dict` (1 Retry, structured-output primär,
  Fallback plain + fence-strip + balanced-`{}`). `_build_create_kwargs` setzt **KEIN**
  `cache_control` → P6 ergänzt additiv (`llm_caching.py`).
- **`research.token_meter`**: `record(usage, model, config, path) -> dict` (frozen 6-Feld-Record)
  · `estimate_cost(...)` cache-aware (write 1.25×, read 0.1×). Liest Cache-Felder bereits,
  **schreibt sie aber nicht** → Decision G erweitert genau das additiv.
- **Broker** (Phase 1, **nur vom deterministischen Context-Builder**, nie vom LLM):
  `get_price(epic).data` (`bid, ask, spread, spread_pct, market_status, timestamp`),
  `get_ohlcv(epic, resolution, count).data = {"bars":[…], "allowance":{…}}` (Bar-Close-
  Feldname **[VERIFY]**), `get_market_info(epic).data` (`min_deal_size, currency,
  instrument_type, market_status`).
- **Credentials:** `from broker_wrapper.credentials import get_credential`, Key
  `"anthropic_api_key"` (wie P4 `research/credentials.py`).

## Naht zu Phase 5
`debate_runner` zwischen Gate 2 und Gate 3 in `executor.run()`. **Default-Passthrough**
(`DebateOutcome(decision="TRADE", direction=candidate["direction"], …, rounds_used=0)`)
hält P5 ohne echten Runner bit-identisch + AI-frei. `decision=="ABSTAIN"` → `NO_TRADE`;
sonst Candidate **in-memory** mit der (ggf. geflippten) Richtung angereichert, dann Gate 3 /
Gate 5 / Sizing / VETOs / `build_order_plan` **unverändert**. Kein Gate/VETO wird angefasst.
→ P5-Edit + ≥4 Regressionstests = **Modul-Schritt 9**.

## Paket-Layout (Step C — ✅ erledigt)
Importierbares Paket = **`debate`**, genestet als `phase6_debate/debate/` (Konvention
wie `phase4_research/research/`, `phase5_execution/execution/`). `pyproject.toml`/`tests/`/
`scripts/` auf Projekt-Ebene. Editable installs via Repo-Root `scripts/dev_install.sh`
(installiert P6 **nach** P4) — **kein `sys.path`-Hack**. Import: `from debate.<modul> import …`.

## Datei-/Modul-Übersicht (TDD-geordnet — pro Modul Tests zuerst, dann grün, dann Commit)
| Datei | Zweck | Status |
|---|---|---|
| `pyproject.toml` · `requirements.txt` · `README.md` · `CLAUDE.md` | Scaffold + Packaging (Step C) | ✅ |
| `debate/__init__.py` | Paket-Marker; re-exportiert seit Modul 1 die Contract-Typen | ✅ |
| `debate/models.py` | `DebateConfig`, `DebateContext`, `AgentTurn`, `DebateOutcome`, Exceptions (types only, frozen) | ✅ Modul 1 |
| `debate/context_builder.py` | CODE: Candidate + 1 frischer Broker-Snapshot → frozen `DebateContext` (die AI-Grenze) | ✅ Modul 2 |
| `debate/timeutil.py` | ISO-8601-UTC-Stempel (`_utcnow()`-Seam, je Phase dupliziert) → `DebateContext.generated_at` | ✅ Modul 2 |
| `debate/prompts.py` | Bull/Bear/Judge System+User-Templates + JSON-Schemas (DE) **+ `build_paper_pick_prompt` (§10.3 Council-Paper-Call, additiv, 2026-07-17 — forced-pick Single-Shot, kein ABSTAIN, zero Diff am Live-Judge-Pfad)** | ✅ Modul 3 (·§10.3) |
| `debate/llm_caching.py` | additiver `cache_control`-Wrapper um `research.LLMClient` + Meter-Erweiterung | ✅ Modul 4 |
| `debate/budget.py` | Call-/Token-/Wall-Clock-Caps + kumulatives Metering, fail-closed | ✅ Modul 5 |
| `debate/debate.py` | Orchestrator: Runden-Loop, Early-Stop, Kompression, fail-closed (Kern) | ✅ Modul 6 |
| `debate/audit.py` | `debate_log.json` (vorwärtskompatibles Schema) | ✅ Modul 7 |
| `debate/credentials.py` | reuse Phase-1 `get_credential("anthropic_api_key")` | ✅ Modul 8 |
| `scripts/wiring.py` · `smoke_test.py` · `live_test.py` | `build_debate` + `debate_runner`-Factory; Operator-Live | ✅ Modul 8 |
| `tests/test_packaging.py` | Editable-Install-Smoke (`import debate`) | ✅ |
| P5 `executor.py`-Edit + Regression | `debate_runner`-Naht + ≥4 neue Executor-Tests | ✅ Modul 9 |

## Offene [VERIFY] (vor dem Bauen gegen echten Code / SDK prüfen)
1. ~~**`anthropic`-SDK block-level `cache_control` auf `system`**~~ ✅ **RESOLVED
   (Modul 4, 2026-06-15, SDK 0.106.0):** Ein plain-String-`system` kann **keinen**
   `cache_control`-Marker tragen → System als **Content-Block-Liste** senden:
   `system=[{"type":"text","text":…,"cache_control":{"type":"ephemeral"}}]`.
   `anthropic.types.TextBlockParam` hat das Feld `cache_control`;
   `CacheControlEphemeralParam` = `{type, ttl?}`, also ist `{"type":"ephemeral"}` gültig.
2. ~~**`message.usage`-Cache-Feldnamen**~~ ✅ **RESOLVED (Modul 4, SDK 0.106.0):**
   `Usage` hat `cache_read_input_tokens` **und** `cache_creation_input_tokens`
   (beide werden von `token_meter._usage_int` bereits gelesen).
3. ~~**`get_ohlcv.data["bars"]` Close-Feldname**~~ ✅ **RESOLVED (Modul 2, 2026-06-15):**
   `get_ohlcv(epic, res, count).data = {"bars":[…], "allowance":{…}}`; jede Bar =
   `OHLCBar.__dict__ = {timestamp, open, high, low, close, volume}`; Close-Feld = **`close`**
   (Mid-Price; `0.0`/`None` bei schlechten Daten). Quelle:
   `phase1_broker_wrapper/.../ig_adapter.py` (`_parse_bar`), gespiegelt von P5-VETO-3
   (`vetos.py:131`).
4. **Modulnamen-Kollision** `scripts.wiring` (P4/P5/P6) — P6-Wiring darf nicht die
   falsche `wiring` importieren.

> 🔁 **Phase-10 (V3) Council-Paper-Call edit (2026-07-17, §10.3, code = source of truth):**
> `debate/prompts.py` gained an **additive sibling** to the live Judge: `_PAPER_PICK_SYSTEM` +
> `_paper_pick_schema()` + `build_paper_pick_prompt(digest)` — a single-shot forced-pick prompt
> (no ABSTAIN branch, `direction` required not nullable) for `phase10_v3`'s
> `PaperDebateCaller.request_pick(...)`. `build_judge_prompt`/`_judge_schema`/the live
> Bull/Bear/Judge orchestrator are **untouched** — zero diff on the real debate path. The
> caller lives in `phase10_v3/abstain_lessons/paper.py` and never imports `debate` (the
> prompt builder is injected by `phase8_scheduler/scripts/wiring.py`, the only cross-phase
> composition point), mirroring how `debate_runner` is duck-typed into `phase5_execution`.
> **P6 70 → 76** (+6 tests, `test_prompts.py`). Detail: `phase10_v3/CLAUDE.md` → this
> session's `## Session stopped` block.

## Done-Kriterien (Phase-6-Gate)
- `pytest phase6_debate/tests -v` grün, **≥45 Tests** (alle gemockt, kein Netz, KEIN echtes
  LLM), davon `test_debate.py` ≥12, `test_llm_caching.py` ≥6, `test_budget.py` ≥6.
- Regression grün: `pytest phase5_execution/tests -v` (inkl. ≥4 neue Executor-Tests) **und**
  `pytest phase4_research/tests -v` (additive Meter/Client-Edits, Default-Verhalten unverändert).
- `bash scripts/dev_install.sh` + alle Suiten grün **ohne** `sys.path`-Hack.
- Beweis-Tests: (a) Judge-Flip → geflippte Richtung in `build_order_plan`; (b) Budget-Breach
  **oder** LLM-Fehler mitten in der Debatte → zuverlässig ABSTAIN/NO_TRADE, keine Order;
  (c) `cache_system=True` setzt den Marker **und** der Meter-Record trägt die Cache-Felder.
- Operator-`live_test.py`: Debatte im vollen Executor gegen IG Demo, sauberes Ende
  (TRADE→open/close **oder** ABSTAIN→NO_TRADE), `debate_log.json` entsteht, `usage_report`
  zeigt **Cache-_Creation_ > 0**. `exit 0`. ✅ **erfüllt (2026-06-16)** — Live-Lauf war `RESULT 3/4`
  (einziger Fail = die alte `cache_reads > 0`-Assertion), nach dem Assertion-Fix (dieser Step) ist
  ein sauberer 1-Runden-ABSTAIN `4/4`. ⚠ **Reconciliation (Code = Source of Truth):** „Cache-_Reads_
  > 0" war das ursprüngliche Kriterium, ist aber ein **False-Negative** bei 1-Runden-Debatten —
  Haikus 4096-Token-Floor lässt Bull/Bear nie cachen, ein Cache-**Read** entsteht erst bei
  `rounds_used >= 2` (Präfix ≥2× getroffen). Daher gilt jetzt: **Creation immer**, **Reads nur
  Mehr-Runden** (Details: Post-Live-Test-Block Punkt 1).

---

## Session stopped — 2026-06-16 (Post-Live-Test — Cache-Assertion-Fix + Doku-Flip auf live-verifiziert)

### Completed
- **`scripts/live_test.py` — Cache-Assertion gelockert (Post-Live-Test Punkt 1, das einzige
  Code-Delta dieses Steps).** Im `if debate_ran:`-Zweig: `rounds_used` aus dem Audit-Record gelesen
  (`audit.py` schreibt es) und im Record-Append-Check angezeigt; aus den neuen `llm_usage.json`-Records
  **beide** Cache-Summen gebildet (`cache_creation_input_tokens` + `cache_read_input_tokens`, beide von
  `token_meter.record` geschrieben). Neue Logik: **`cache_creation > 0` immer** fordern (beweist den
  `cache_control`-Marker am Judge/Sonnet-Präfix), **`cache_read > 0` nur bei `rounds_used >= 2`** — sonst
  Skip-Hinweis statt FAIL. Docstring (Kopf) auf die Zwei-Teil-Semantik (Creation immer / Reads nur
  Mehr-Runden) umgeschrieben. **Grund:** der erste Live-Lauf war `RESULT 3/4`, einziger Fail = das
  bestätigte False-Negative (Haikus 4096-Token-Floor → Bull/Bear cachen nie; 1-Runden-Early-Stop liest
  keinen Präfix neu). Netto: ein sauberer 1-Runden-ABSTAIN ist jetzt `4/4`. **Kein Unit-Test** (Scripts
  werden nicht von `pytest` collected — konsistent mit P4/P5; Suiten bleiben **70 / P5 135 / P4 88**).
- **Doku auf ✅ live-verifiziert geflippt (Operator-Entscheidung 2026-06-16 — jetzt, nicht erst nach
  dem 4/4-Re-Run, weil der Pfad bereits live bewiesen ist und der einzige Fail dieser gefixte Test-Bug
  war).** Root-`CLAUDE.md` (Active-Phase-Zeile + Phase-6-Status-Block, gespiegelt an der Phase-5-Form,
  inkl. Cache-Reconciliation + Item-2-Deferral) · `ROADMAP.md` (alle `[ ]`→`[x]`, „Done when"-Cache-Zeile
  reconciled, „(to be created)" entfernt) · `phase6_debate/README.md` (Status-Zeile) · diese `CLAUDE.md`
  (Done-Kriterien-Cache-Zeile annotiert, Post-Live-Test Punkt 1 = ✅ erledigt, Punkt 2 = ⏸ zurückgestellt
  mit der Operator-Begründung). Überall der stehende Caveat **live-verifiziert ≠ profit-validiert** (ein
  ABSTAIN-Zyklus, kein Edge gemessen — das ist Phase 7).
- **Item 2 (Seed-`--reasoning`-Override, P5-Scope) bewusst zurückgestellt.** Begründung des Operators:
  (a) Profitabilität ist nicht Test-Scope, (b) die Ausführbarkeit eines Trades ist in Phase 5 bereits
  live bewiesen. Separate, spätere Aufgabe.

### Verifiziert
- `pytest phase6_debate/tests -q` → **70**, `pytest phase5_execution/tests -q` → **135**,
  `pytest phase4_research/tests -q` → **88** (alle unverändert — das Delta ist script-only + Doku).
- `python -c "import ast; ast.parse(...)"` auf `live_test.py` → OK (Syntax + Struktur intakt).
- ✅ **Operator-Live-Lauf bestätigt (2026-06-16, BUY-Seed im Fenster): `RESULT: 4/4 passed`.**
  Debatte lief (3 echte Calls), `rounds_used=1`, **ABSTAIN** (Judge entwertete den „MANUAL SEED" +
  die schwache −0,05%-Bewegung), `NO_TRADE`, `debate_log.json` angehängt, `cache_creation=1073` (>0,
  Marker greift), `cache_read=0` korrekt übersprungen (1-Runden-Debatte). Der Assertion-Fix wirkt
  exakt wie geplant — die einzige zuvor rote Prüfung ist jetzt grün.
- **Top-Level-Docs zusätzlich geflippt:** Root-`README.md` (Status-Tabelle Phase 6 = ✅ + Fußnote ³),
  `docs/concepts/phase6_debate_concept.md` (Banner = ✅ gebaut + live-verifiziert). `ARCHITECTURE.md`
  trägt keinen Status-Marker → unverändert.

### Gemerged + gepusht (2026-06-16) ✅
- Dieser Step committet als **`49cda8a`** auf `phase6-debate`, dann **fast-forward nach `main`
  gemerged** (`c8d5ba1..49cda8a`, keine Konflikte — `origin/main` war Ancestor) und **gepusht**:
  `origin/main` = `49cda8a`, `origin/phase6-debate` = `49cda8a` (neu angelegt). Damit ist die
  **gesamte Phase 6** (Module 1–9 + dieser Post-Live-Test-Step) auf `main` und remote. Operator-
  Freigabe für Push+Merge erteilt (2026-06-16). _(Diese „pushed+merged"-Notiz selbst ist der
  Folge-Commit obendrauf.)_
- **Phase 6 ist code-complete + live-verifiziert (4/4), gemerged + gepusht.**

### Next (außerhalb dieser Phase)
- Optional/später: ein TRADE-durch-die-Debatte-Lauf mit **neutralem** Seed (Post-Live-Test Punkt 2,
  P5-Scope) und P7-Substrat (Outcome-Anchoring) — beides außerhalb dieser Phase.

### Gotchas (für den Re-Entry)
- Branch **`phase6-debate`**. Dieser Step = **script-only + Doku** (kein neues Modul, keine P5/P4-Code-Edits).
  Bei Commit die Hard-Regel (Commit ⇒ Note-Update) beachten: diese Note + die geflippten Top-Level-Docs
  gehören in **denselben** Commit.
- Die `Cache-Reads > 0`-Erwartung ist **nur** bei `rounds_used >= 2` gültig — wer den Live-Test bei einer
  Mehr-Runden-Debatte sieht, sollte dort Reads > 0 erwarten; bei 1-Runden-ABSTAIN ist `cache_read=0` korrekt.

---


> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
