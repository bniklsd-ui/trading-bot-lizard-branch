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
| `debate/__init__.py` | Paket-Marker (Exports noch leer; landen mit den Modulen) | ✅ Stub |
| `debate/models.py` | `DebateConfig`, `DebateContext`, `AgentTurn`, `DebateOutcome`, Exceptions | ⏳ Modul 1 (nächster Schritt) |
| `debate/context_builder.py` | CODE: Candidate + 1 frischer Broker-Snapshot → frozen `DebateContext` (die AI-Grenze) | ⏳ Modul 2 |
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
3. **`get_ohlcv.data["bars"]` Close-Feldname** (gleiche offene Stelle wie P5-VETO-3)
   für `recent_bars_summary`.
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

## Session stopped — 2026-06-12 (Scaffold + Step C + Konzept-Korrektur)

### Completed
- **Step 0 (Naming-Hygiene + Doc-Abgleich)** ✅ committed (`c8d5ba1`, lokal, **nicht** gepusht):
  `ROADMAP.md` + Root-`CLAUDE.md` Phase-6-Zeilen auf das gelockte 11-Entscheidungs-Konzept +
  die AI-Grenze gezogen. `turbo_candidates.json` unangetastet; kein Code geändert.
- **Konzept-Korrektur** in `docs/concepts/phase6_debate_concept.md`: dieses `CLAUDE.md` wird
  **up-front im Scaffold** angelegt (wie P1–P5, z. B. P4 Step 1) — **nicht** auf Step 10
  verschoben. Step 10 finalisiert nur noch `README.md` + den finalen Session-stopped-Stand.
  Begründung: das `CLAUDE.md` ist die Wissens-/Protokoll-/Handover-Basis und muss ab Session 1
  existieren. Step 0 / Scaffold / Step C im Konzept als **DONE** annotiert (nicht doppelt machen).
- **Scaffold `phase6_debate/`** ✅ (gespiegelt an P4/P5): `pyproject.toml` (`name="debate"`,
  `include=["debate*"]`), `requirements.txt` (nur `pytest`; `anthropic` via P4-Install),
  `README.md`, dieses `CLAUDE.md`, `debate/__init__.py` (Exports noch leer), `tests/__init__.py`
  + `tests/test_packaging.py` (Import-Smoke), `scripts/__init__.py`.
- **Step C (Packaging)** ✅: `scripts/dev_install.sh` (Repo-Root) um `phase6_debate` erweitert
  (Reihenfolge P1→…→P6, nach P4). `import debate` löst über den editable install auf — **kein
  `sys.path`-Hack**.
- **Verifiziert:** `pytest phase6_debate/tests -v` grün (Packaging-Smoke); P4 (88) + P5 (130)
  Suiten unberührt grün; Step-0-grep auf `phase6_debate/` ohne Treffer.

### Next
- **Modul 1 — `debate/models.py` + `tests/test_models.py`** (≥5 Tests): `DebateConfig` (alle
  Felder aus der Defaults-Tabelle §0), `DebateContext`/`AgentTurn`/`DebateOutcome` (frozen,
  immutabel), Exceptions (`DebateError` → `DebateBudgetExceeded`, `DebateLLMError`). Doku-Test:
  `confidence` taucht in **keiner** Gating-Verzweigung auf; Konstante `confidence_gates_nothing`
  existiert. Types only, keine Logik (wie P4-`models.py` Step 1). Danach Modul 2 (`context_builder`).

### Offene Punkte / [VERIFY]
- SDK `cache_control`-Form (Modul 4), `message.usage`-Cache-Feldnamen (Modul 4),
  `get_ohlcv`-Close-Feldname (Modul 2), `scripts.wiring`-Namenskollision (Modul 8). Jeweils
  **vor** dem betroffenen Modul gegen echten Code/SDK prüfen — genau das hat in P4/P5 den
  `CALL/PUT`- und `currencyCode`-Bug gefangen.

### Gotchas (für den Re-Entry)
- `debate/__init__.py` exportiert noch **nichts** — `import debate` ist absichtlich leer
  (Exports landen mit Modul 1/6). Der Packaging-Test prüft genau das.
- **Nicht committet** über Step 0 hinaus (User: „no commit yet") — Working Tree liegt zur
  Review. Beim nächsten Commit: scaffold + Step C + Konzept-Korrektur sind ein logischer Block.
- `requirements.txt` enthält bewusst **kein** `anthropic` — es kommt über den P4-editable-install.
