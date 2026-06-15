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
| `debate/prompts.py` | Bull/Bear/Judge System+User-Templates + JSON-Schemas (DE) | ⏳ Modul 3 |
| `debate/llm_caching.py` | additiver `cache_control`-Wrapper um `research.LLMClient` + Meter-Erweiterung | ⏳ Modul 4 |
| `debate/budget.py` | Call-/Token-/Wall-Clock-Caps + kumulatives Metering, fail-closed | ⏳ Modul 5 |
| `debate/debate.py` | Orchestrator: Runden-Loop, Early-Stop, Kompression, fail-closed (Kern) | ⏳ Modul 6 |
| `debate/audit.py` | `debate_log.json` (vorwärtskompatibles Schema) | ⏳ Modul 7 |
| `debate/credentials.py` | reuse Phase-1 `get_credential("anthropic_api_key")` | ⏳ Modul 8 |
| `scripts/wiring.py` · `smoke_test.py` · `live_test.py` | `build_debate` + `debate_runner`-Factory; Operator-Live | ⏳ Modul 8 |
| `tests/test_packaging.py` | Editable-Install-Smoke (`import debate`) | ✅ |
| P5 `executor.py`-Edit + Regression | `debate_runner`-Naht + ≥4 neue Executor-Tests | ⏳ Modul 9 |

## Offene [VERIFY] (vor dem Bauen gegen echten Code / SDK prüfen)
1. **`anthropic`-SDK-Version** unterstützt block-level `cache_control` auf `system`
   (bzw. System als Content-Block-Liste). Falls nicht → Form anpassen.
2. **`message.usage`-Cache-Feldnamen** (`cache_creation_input_tokens` /
   `cache_read_input_tokens`) gegen die SDK-Version.
3. ~~**`get_ohlcv.data["bars"]` Close-Feldname**~~ ✅ **RESOLVED (Modul 2, 2026-06-15):**
   `get_ohlcv(epic, res, count).data = {"bars":[…], "allowance":{…}}`; jede Bar =
   `OHLCBar.__dict__ = {timestamp, open, high, low, close, volume}`; Close-Feld = **`close`**
   (Mid-Price; `0.0`/`None` bei schlechten Daten). Quelle:
   `phase1_broker_wrapper/.../ig_adapter.py` (`_parse_bar`), gespiegelt von P5-VETO-3
   (`vetos.py:131`).
4. **Modulnamen-Kollision** `scripts.wiring` (P4/P5/P6) — P6-Wiring darf nicht die
   falsche `wiring` importieren.

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
  zeigt **Cache-Reads > 0**. `exit 0`.

---

## Session stopped — 2026-06-15 (Modul 2 — `context_builder.py`)

### Completed
- **Modul 2 — `debate/context_builder.py` + `debate/timeutil.py` + `tests/conftest.py` +
  `tests/test_context_builder.py`** ✅: `build_debate_context(candidate, broker, config)
  -> DebateContext`. **CODE-only — die AI-Grenze.** Liest GENAU EINEN frischen Snapshot
  (`get_price` → `get_ohlcv` → `get_market_info`, je **einmal**), faltet ihn mit dem
  Candidate-Seed zu einem frozen `DebateContext`. Der Broker wird hier (Code) gelesen; die
  Agenten bekommen ihn nie. Frischer `spread_pct`/`market_status` aus `get_price` überschreibt
  `spread_pct_at_pick`; `recent_bars_summary` aus den IG-Echtzeit-Bars (first/last close + net %,
  gespiegelt von P5-VETO-3). **Fail-closed:** not-ok-Envelope / raised fault / `market_status ≠
  TRADEABLE` / <2 Bars / 0-oder-None-Close → `DebateError` (→ ABSTAIN im Orchestrator).
  `drift_at_pick=None` crasht nicht. **Isolation:** importiert nur `debate.models`/
  `debate.timeutil`/stdlib (Broker via lokalem `Protocol`) — kein `anthropic`/`broker_wrapper`/
  `research`.
- **`debate/timeutil.py`** — per-Phase-Duplikat (wie P1–P4) mit `_utcnow()`-Seam für
  Test-Time-Freeze → `DebateContext.generated_at` (ISO-8601 UTC, ms, `Z`).
- **`DebateConfig` additiv erweitert:** `bars_resolution="MINUTE_5"` + `bars_count=12` —
  **verbatim aus den gelockten P5-Momentum-Defaults** (`ExecutionConfig`), kein erfundener
  Wert. §0-Defaults-Tabelle hier + Concept-§0 mit dateiertem Reconciliation-Hinweis aktualisiert.
- **[VERIFY] #3 (get_ohlcv-Close-Feld) RESOLVED** — `close` (s. oben).
- **Verifiziert:** `pytest phase6_debate/tests -q` → **19 passed** (7 + 12 neu, ≥6 gefordert);
  Regression grün: P4 **88**, P5 **130** unberührt. Hygiene-grep clean. **Nicht committet**
  (User triggert Commits).

### Next
- **Modul 3 — `debate/prompts.py` + `tests/test_prompts.py`** (≥6 Tests, Concept §3):
  drei System-Prompts (Bull/Bear/Judge, **Deutsch**) + drei Structured-Output-Schemas. System+
  Kontext-Block **stabil über alle Turns** (Cache-Präfix, Decision D); nur das wachsende
  Transkript steht im `user`-Teil. Prompts müssen **ehrlich** kommunizieren: `drift_at_pick`/
  `seed_*` = verzögertes P4-Stimmungsbild (yFinance ~15 min), `spread_pct`/`recent_bars_summary`
  = IG-Echtzeit. Judge-Schema: `{decision:"TRADE|ABSTAIN", direction:"BUY|SELL|null",
  confidence:0-100, rationale, conclude:bool}` (`conclude` steuert Early-Stop). Tests: jedes
  Schema valide; Kontext vollständig im stabilen Block; Transkript seriell im user-Teil;
  `direction:null` bei ABSTAIN erlaubt; **kein** Options-Vokabular irgendwo (Hygiene).
- **[VERIFY] vor Modul 3:** keine neue offene Stelle; Anthropic-Schema-Eigenheiten aus P4
  beachten (Structured Outputs lehnen Type-Arrays/`minimum`/`maximum` ab → `anyOf` für nullable,
  Range im Code prüfen; s. P4 `prompt.py:_build_schema`).

### Offene Punkte / [VERIFY]
- SDK `cache_control`-Form (Modul 4), `message.usage`-Cache-Feldnamen (Modul 4),
  `scripts.wiring`-Namenskollision (Modul 8). Jeweils **vor** dem betroffenen Modul prüfen.
  ([VERIFY] #3 `get_ohlcv`-Close ist erledigt.)

### Gotchas (für den Re-Entry)
- Branch **`phase6-debate`**. Modul 1 **und** Modul 2 sind **noch nicht committet** —
  Working Tree liegt zur Review (User triggert Commits).
- `context_builder` ist **kein** Top-Level-Export (`debate/__init__.py` unverändert) — Zugriff
  via `from debate.context_builder import build_debate_context` (wie P4 `build_context`).
- `DebateConfig.bars_resolution`/`bars_count` sind der einzige config-Touch; `get_ohlcv` wird
  mit genau diesen Werten gerufen (Test `test_each_probe_read_exactly_once` pinnt das).

---

## Session stopped — 2026-06-15 (Modul 1 — `models.py`)

### Completed
- **Modul 1 — `debate/models.py` + `tests/test_models.py`** ✅: alle Contract-Typen als
  `@dataclass(frozen=True)` — `DebateConfig` (exakt die §0-Defaults: Bull/Bear=Haiku 4.5,
  Judge=Sonnet 4.6, `max_rounds=5`, Caps 18/120k/12k/120s, `cache_system=True`,
  `compression_trigger_pct=0.65`, Temps 0.4/0.4/0.1, `max_tokens_agent/judge=512/768`,
  `debate_log_path`, **`confidence_gates_nothing=True`** = reine Selbst-Doku, Decision H),
  `DebateContext` (frischer Snapshot + Seed-Felder), `AgentTurn`, `DebateOutcome` (+ `to_dict()`,
  Transkript→list für den Audit). Exceptions `DebateError` → `DebateBudgetExceeded`/`DebateLLMError`
  (alle → fail-closed ABSTAIN im Orchestrator). **7 Tests grün** (Packaging-Smoke + 6 Modell-Tests).
- **Pricing bewusst NICHT in `DebateConfig`** dupliziert (Decision F): Kosten/USD→EUR kommen aus
  der geteilten `research.ResearchConfig`, die den P4-`LLMClient`/`token_meter` konfiguriert.
- `debate/__init__.py` re-exportiert jetzt die Contract-Typen (wie P4 sein `__init__` wachsen ließ);
  `Debate`-Orchestrator-Export landet mit Modul 6.
- **Isolation bestätigt:** `models.py` importiert nur stdlib (`dataclasses`, `typing`) — kein
  `anthropic`/`broker_wrapper`/`research`. Hygiene-grep (`--include=*.py`) **clean** (Prosa nach der
  §0-⚠-Vorgabe entschärft: „request/invocation" statt „call", „reverse" statt „flip", keine
  Options-Identifier ausgeschrieben).
- **Verifiziert:** `pytest phase6_debate/tests -q` → 7 passed; P4 (88) + P5 (130) unberührt grün.

### Next
- **Modul 2 — `debate/context_builder.py` + `tests/test_context_builder.py`** (≥6 Tests, FakeBroker):
  `build_debate_context(candidate, broker, config) -> DebateContext`. **CODE-only, das ist die
  AI-Grenze** — liest GENAU EINEN frischen Snapshot (`get_price` + `get_ohlcv` + `get_market_info`),
  baut `recent_bars_summary` aus den IG-Echtzeit-Bars. `market_status ≠ TRADEABLE` / `get_ohlcv`-Fehler
  → `DebateError` (→ ABSTAIN). Frischer `spread_pct` überschreibt `spread_pct_at_pick`. `drift_at_pick=None`
  darf nicht crashen. Broker je Probe genau **einmal** gelesen.
- **[VERIFY] vor Modul 2:** `get_ohlcv.data["bars"]`-Close-Feldname gegen echten P1-Code (gleiche
  offene Stelle wie P5-VETO-3). conftest braucht einen `FakeBroker` mit `get_price`/`get_ohlcv`/
  `get_market_info` (P4/P5-conftest als Vorlage).

### Offene Punkte / [VERIFY]
- SDK `cache_control`-Form (Modul 4), `message.usage`-Cache-Feldnamen (Modul 4),
  `get_ohlcv`-Close-Feldname (Modul 2), `scripts.wiring`-Namenskollision (Modul 8). Jeweils
  **vor** dem betroffenen Modul gegen echten Code/SDK prüfen.

### Gotchas (für den Re-Entry)
- Branch **`phase6-debate`** (Scaffold-Commit `c810a3b`). Modul 1 ist **noch nicht committet** —
  Working Tree liegt zur Review (User triggert Commits).
- `DebateOutcome.to_dict()` normalisiert das Transkript-Tupel zu einer **list** (asdict lässt es
  sonst Tupel) — der Audit (Modul 7) will ein JSON-Array.
- `requirements.txt` enthält bewusst **kein** `anthropic` — es kommt über den P4-editable-install.
- Hygiene-Disziplin: in Docstrings „request/invocation" statt „call", „reverse" statt „flip"
  schreiben (sonst matcht der `grep -i`-Gate).
