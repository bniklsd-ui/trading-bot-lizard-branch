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
| `debate/prompts.py` | Bull/Bear/Judge System+User-Templates + JSON-Schemas (DE) | ✅ Modul 3 |
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

## Session stopped — 2026-06-16 (Module 9 + 8 zusammen — P5-Naht + Wiring/Scripts/Credentials)

### Warum 9 + 8 in EINER Session (dokumentierte Ausnahme zum Ein-Modul-Rhythmus)
Modul 8 (`live_test.py`) fährt die Debatte **im vollen P5-Executor** — das geht erst, wenn der
Executor einen `debate_runner` akzeptiert (Modul-9-Naht). Die beiden sind also **hart gekoppelt**;
8 allein ließe `live_test` eine ganze Session lang gestrandet. Darum diese Session: erst Modul 9
(die testbare Naht), dann Modul 8 (Wiring + Scripts + Credentials). **Operator-Freigabe** dieser
Ausnahme erteilt (2026-06-16). Präzedenz: P5 baute Steps 9+10 aus demselben Kopplungsgrund zusammen.

### Completed — Modul 9 (P5-Naht, **Decision A**, additiv)
- **`phase5_execution/execution/executor.py`** — neuer **keyword-only** Ctor-Arg
  `debate_runner: Callable[[dict], Any] | None = None` (nach `*`, neben `now_fn`/`sleep_fn`).
  Naht **zwischen Gate 2 und Gate 3** (Schritt „4.5"): `outcome = debate_runner(candidate)`;
  `getattr(outcome,"decision")=="ABSTAIN"` → `_no_trade("debate", rationale)`; sonst
  `candidate = {**candidate, "direction": outcome.direction}` (in-memory, ggf. **geflippt**,
  Decision B). **Duck-typed gelesen** (`.decision`/`.direction`/`.rationale`) — **kein** P6-Import,
  Phasen-Isolation gewahrt. `None` (Default) → Naht übersprungen → **P5 bit-identisch + AI-frei**
  (alle 130 P5-Tests unverändert, keine Testdatei angefasst außer den 4 neuen).
- **`tests/test_executor.py`** — **+5 Tests** (jetzt 13): Flip (BUY-Seed + TRADE/SELL → Order ist
  **SELL**), ABSTAIN → NO_TRADE (`"debate"` im detail, **kein** `open_position`, Gate 3 nie
  erreicht), TRADE same-dir → öffnet normal, `debate_runner=None` → Baseline. Lokaler
  `_DebateOutcome`-Stand-in (SimpleNamespace-artig) → **kein** P6-Import in der P5-Suite.

### Completed — Modul 8 (alles in `phase6_debate/`)
- **`debate/credentials.py`** — Keyring-Shim, **verbatim gespiegelt** von
  `research/credentials.py` (Phase-1 `get_credential("anthropic_api_key")`, `__all__`,
  `parents[2]`-Bootstrap). Die eine dokumentierte Phasen-Ausnahme (Hard Rule 1). **Nicht** von
  Unit-Tests importiert.
- **`scripts/wiring.py`** — `build_debate(broker, *, debate_config=None, with_audit=True)` baut den
  **geteilten** `research.LLMClient` mit **`cache_system=True`** (Key aus Keyring-Shim,
  `token_meter_path` → `data/state/llm_usage.json`, Pricing aus `ResearchConfig`) + bindet den
  **Modul-7-Audit-Callable** `lambda o,c: write_debate(o,c,"…/debate_log.json")` → `Debate`.
  `make_debate_runner(broker)` = lazy `debate_runner`-Factory (baut die Debatte **einmal**, teilt
  den Broker). `build_executor(config, *, confirm_fn, …)` baut den P5-`Executor` **direkt aus dem
  installierten `execution`-Paket** (löst die **`scripts.wiring`-Namenskollision** P4/P5/P6 — genau
  wie P5 die P4-Kollision löste), teilt **einen** Broker zwischen Executor + Debatte, `research_runner`
  = No-Op (`_no_research`, Live-Pfad nutzt **geseedeten** Candidate), `debate_runner` injiziert,
  tz-aware `now_fn`.
- **`scripts/smoke_test.py`** — eine **echte** Debatte über den geseedeten Candidate, **dry**
  (kein Executor, `with_audit=False` → **kein** `debate_log`-Write). Lädt den Candidate aus
  `StateManager.load_candidates()` (Operator seedet vorher via P5 `seed_candidate.py`), connectet
  den Broker (Context-Builder braucht frische Preise), druckt Transkript + `token_summary`
  (inkl. Cache-Reads) → stderr, Outcome-JSON → stdout.
- **`scripts/live_test.py`** — Operator-Gate: Debatte **im vollen Executor** (P6-`build_executor`,
  auto-confirm, `max_hold=1`/`poll=10s`). Wiederverwendet `execution.ig_bot.make_confirm_fn`/
  `result_to_dict` (installiertes Paket, **keine** `scripts`-Kollision). Asserts: sauberes Ende
  (kein ABORT); **wenn die Debatte lief** (Gate 1 ok + frischer Seed) → neuer `debate_log.json`-
  Record **und** `cache_read_input_tokens > 0` (Caching-Beweis); sonst die Debatte-Proofs sauber
  übersprungen (immer noch valider exit 0). `RESULT: N/M` → stderr, JSON → stdout.
- **Keine P6-Unit-Tests** für Scripts/Credentials (konsistent mit P4/P5 — Scripts werden nicht
  collected). P6-Unit-Zahl bleibt **70**.

### Verifiziert
- `pytest phase5_execution/tests -q` → **135** (130 + 5 Naht-Regression). `pytest phase6_debate/tests
  -q` → **70** (unverändert). `pytest phase4_research/tests -q` → **88** (unverändert).
- Hygiene-grep clean (Prosa „request/invocation" statt „call"); `py_compile` der 4 Dateien OK;
  `import scripts.wiring` (aus `phase6_debate/`) löst **ohne** Netz/Keyring; `smoke/live --help` exit 0.
- **Committet als NICHT-live-getestete Baseline** (Module 8+9, dieser Commit = HEAD von
  `phase6-debate`; Hard-Regel `4abd8b3` befolgt: Note + Modul-8/9-Zeilen (✅) + P5-/Concept-
  Annotationen im selben Commit). ⚠ **Bewusst als sauberer Rollback-Punkt getaggt:**
  **`phase6-pre-live-test`** markiert den Stand „Code-complete, **noch nicht** live-verifiziert"
  — exakt vor dem ersten Operator-Live-Lauf. Falls der Live-Pfad debuggt werden muss, ist
  `git checkout phase6-pre-live-test` der definierte saubere Ausgangszustand (Muster wie
  `phase4-pre-schema-fix`). Die konkrete Commit-SHA: `git rev-list -n1 phase6-pre-live-test`.

### scripts.wiring-Kollision [VERIFY] — **RESOLVED**
P6-`live_test` importiert P6-`scripts.wiring.build_executor`; das baut den Executor **selbst** aus
`execution.*` (nie P5-`scripts.wiring`). `ig_bot`-Helfer kommen aus dem `execution`-Paket (kein
`scripts`-Name) → keine Kollision. Einziger geteilter Broker zwischen Executor + Debatte.

### Next — Operator-Live-Gate (User führt aus; Claude macht Code + gemockte Tests)
1. `bash scripts/dev_install.sh` (installiert P1–P6 editable).
2. **Im Handelsfenster** (09:00–17:30 Europe/Berlin), **mit** dem aktuellen `get_ohlcv`-net-return:
   `python phase5_execution/scripts/seed_candidate.py --direction SELL` (TTL 30 min!).
3. `python phase6_debate/scripts/smoke_test.py` (dry — Transkript + Cache-Reads sichtbar).
4. `python phase6_debate/scripts/live_test.py` → erwartet sauberes Ende, neuer `debate_log.json`-
   Record, `exit 0`. ⚠ **Die `Cache-Reads > 0`-Assertion ist bei einer 1-Runden-Debatte ein
   erwartetes False-Negative** — Details + Fix im Post-Live-Test-Block unten (Punkt 1). Danach
   Phase-6 ✅ live-verifiziert flippen (Top-Level-Doku).
- Bei grünem Gate: **Phase 6 ist code-complete** — nur noch der Operator-Lauf + Doku-Flip offen.

### Post-Live-Test — Folge-Schritte (nächste Session)
> Erkenntnisse aus **Smoke + Live** (2026-06-16). Smoke: echte LLM-Debatte über den SELL-Seed
> (3 Calls, 1 Runde, Early-Stop, Verdict **ABSTAIN**, `cache_read=0`/`cache_write=1072`, ~$0.013).
> **Live (`live_test.py`) ist GELAUFEN** → `RESULT: 3/4 passed`, **einziger Fail = die
> `cache_reads > 0`-Assertion** (erwartetes False-Negative, s. Punkt 1+4). Der ganze P6-Pfad ist
> damit **end-to-end live bewiesen** (build_executor → injizierter `debate_runner` → 3 echte
> Bull/Bear/Judge-Calls → fail-closed ABSTAIN → `NO_TRADE` → `debate_log.json` geschrieben).
> Diese Schritte als Nächstes angehen; um weitere Befunde ergänzen.

1. **`cache_reads > 0`-Assertion in `live_test.py` lockern (live bestätigtes False-Negative).**
   Grund (gegen die `claude-api`-Caching-Referenz bestätigt): **Haiku-4.5-Mindest-Cache-Präfix =
   4096 Tokens**, Sonnet-4.6 = 2048. Bull/Bear (Haiku, ~850–1040 Input-Tokens) liegen **weit unter
   4096** → cachen **nie** (`cache_creation=0`); nur der Judge (Sonnet) schreibt Cache. **Cache-READ
   braucht denselben Präfix ≥2×** — bei Early-Stop in Runde 1 läuft jede Rolle genau **einmal** →
   kein Re-Read → `cache_read=0`, auch beim Judge. Caching greift also erst bei **Mehr-Runden**-
   Debatten. **Fix:** Assertion entkoppeln — `cache_creation > 0` **immer** fordern (beweist, dass
   der Marker greift), `cache_read > 0` **nur bei `rounds_used >= 2`**. (Sonst meldet ein sauberer
   1-Runden-Lauf fälschlich FAIL.) → kleiner Folge-Commit auf dem `phase6-pre-live-test`-Tag.
   **Der Live-Lauf 2026-06-16 hat genau das getan: `RESULT: 3/4`, einziger Fail = diese Assertion**
   (alle anderen Checks grün). Nach dem Fix einen sauberen Lauf erwarten (1-Runden-ABSTAIN → 4/4,
   `exit 0`), **dann** Phase-6 ✅ live-verifiziert im Top-Level-Doku flippen.
2. **Seed-Reasoning-Bias → Debatte ABSTAINt → kein Order-Pfad.** Der manuelle Seed trägt
   `reasoning="MANUAL SEED (not a real research pick) …"`; das fließt in `DebateContext.seed_reasoning`
   → in den Prompt → der Judge entwertet es **korrekt** → ABSTAIN. Folge: `live_test.py` endet
   wahrscheinlich `NO_TRADE` (valider exit 0, beweist die Naht + `debate_log.json`), **platziert aber
   keine Order**. Wer den Order-Pfad **durch** die Debatte live üben will: einen Candidate mit
   **neutralem, plausiblem** `reasoning` seeden (nicht den self-defeating Default). Optional (P5-Scope,
   separat): `phase5_execution/scripts/seed_candidate.py` einen `--reasoning`-Override / neutraleren
   Default geben. (Der Order-/Monitor-Pfad selbst ist in P5 bereits live bewiesen — nicht blockierend.)
3. **P7-Vorausnotizen (Outcome-Anchoring).** `debate_log.json` + advisory `confidence` sind genau das
   P7-Substrat (Smoke erzeugte bereits die korrekte Record-Form). Kosten ~**$0.013/Runde** (×Runden).
   Caching-ROI prüfen: durch Haikus 4096-Floor cachen Bull/Bear faktisch nie — mehr Hebel liegt in
   **kurzen, stabilen Judge-Prompts** (Sonnet cacht) als im Versuch, die Haiku-Arguer zu cachen; ggf.
   `cache_system`-Nutzen / Modell-Split neu bewerten (Decision C/D bleiben gelockt — das ist P7-Tuning).
4. **Erster Live-Lauf — Ergebnis (2026-06-16).** `live_test.py` gegen IG Demo lief sauber:
   `debate_runner` feuerte (3 echte Calls), Verdict **ABSTAIN** (Judge entwertete den als „MANUAL
   SEED" markierten Seed + die schwache +0.102%-Bewegung — exakt wie im Smoke, s. Punkt 2),
   Executor → `NO_TRADE`, **`debate_log.json`-Record angehängt** (`final_decision=ABSTAIN`,
   `final_direction=None`) → Modul-7-Audit auch live bewiesen. `RESULT: 3/4` (nur die Cache-Assertion
   rot, s. Punkt 1). **Kein** IG-Validierungsfehler (à la P5 `currencyCode`), **kein** Schema-/Prompt-
   Edge, **keine** Exception — der Pfad ist funktional live korrekt. Platzhalter bleibt: weitere
   Live-Befunde (besonders ein TRADE-durch-die-Debatte-Lauf mit neutralem Seed, Punkt 2) hier anhängen.

### Gotchas (für den Re-Entry)
- Branch **`phase6-debate`**. Module 1–7 committet (Modul 7 = HEAD vor dieser Session); **Module 8+9
  noch nicht** — Working Tree: `phase5_execution/execution/executor.py` + `…/tests/test_executor.py`
  (Modul 9) **und** `phase6_debate/debate/credentials.py` + `phase6_debate/scripts/{wiring,smoke_test,
  live_test}.py` + diese Note + P5-/Concept-Annotationen (Modul 8).
- **Modul 9 editiert eine P5-Datei** — das ist **Decision A** (P6-Scope: „minimale P5-Edit erlaubt"),
  nicht Scope-Bruch. Default `None` hält P5 bit-identisch. In `phase5_execution/CLAUDE.md` dateiert
  vermerkt (wie Modul 4 seine P4-Edits in der P4-`CLAUDE.md`).
- `build_debate(with_audit=False)` ist der **einzige** Weg, eine Debatte **ohne** `debate_log`-Write
  zu fahren (smoke). Der Live-Pfad/`make_debate_runner` schreibt immer.
- **`live_test` braucht einen frischen Seed** im Fenster, sonst überspringt es die Debatte-Proofs
  (Gate 1 / kein Candidate) — das ist **kein** Fehler, nur „Debatte lief diesen Zyklus nicht".

---

## Session stopped — 2026-06-16 (Modul 7 — `debate/audit.py`, vorwärtskompatibler JSON-Audit)

### Completed
- **Modul 7 — `debate/audit.py` + `tests/test_audit.py`** ✅ (≥5 → **8 neue Tests**):
  `write_debate(outcome: DebateOutcome, ctx: DebateContext, path: str | None) -> dict`.
  Baut **einen** vorwärtskompatiblen Record (Concept §7) aus Outcome + Context und hängt ihn
  **atomar** an `data/state/debate_log.json` an. **Schema** exakt §7:
  `{ts, epic, seed_direction, final_decision, final_direction, confidence(advisory), rounds_used,
  rationale, regime_snapshot{spread_pct, market_status, drift_at_pick, score_at_pick,
  recent_bars_summary}, transcript[...], token_summary{6 keys}}`. **P9-Mapping als Modul-Docstring-
  Tabelle** (`regime_snapshot`→`market_regime_snapshots`, `transcript`/`decision`/…→`decision_context`).
- **Atomar (Decision I, §7):** `_load_log` (gespiegelt von `token_meter._load_log` — fehlend→`[]`,
  korrupt/non-list→Warnung+frisch, nie Raise) → append → `tempfile.mkstemp` im **selben** Verzeichnis
  → `json.dump` → `os.replace(tmp, path)` (bewusste Verbesserung gegenüber dem in-place-Write von
  `token_meter`). Fehlgeschlagener Replace räumt das Temp-File ab; jeder `OSError` wird **geloggt +
  geschluckt** (best-effort, der Audit bricht **nie** ein Ergebnis — der Orchestrator-Callable schluckt
  zusätzlich obendrauf). `os.makedirs(..., exist_ok=True)` legt fehlende Pfade an.
- **`path=None` → kein Write, Record zurück** (Dry/Unit-Pfad, exakt wie `token_meter.record`).
- **`confidence` advisory:** wandert nur in den Record (Decision H), in **keine** Verzweigung. Transkript
  via `outcome.to_dict()["transcript"]` (Tuple→list-Normalisierung schon in `models.py`).
- **Isolation:** importiert nur `debate.models`/`debate.timeutil` + stdlib (`json`/`os`/`logging`/
  `tempfile`/`typing`) — **kein** `anthropic`/`broker_wrapper`/`research` (laufzeit-geprüft: keins der
  drei in `sys.modules` nach `import debate.audit`). Logging→stderr. Hygiene-grep clean.
- **`.gitignore`:** `data/state/debate_log.json` ergänzt (dateierte §0-Reconciliation wie P3/P4/P5;
  `git check-ignore` → IGNORED). **`debate/__init__.py` unverändert** — Zugriff via
  `from debate.audit import write_debate` (wie `context_builder`/`prompts`/`budget`).
- **Verifiziert:** `pytest phase6_debate/tests -q` → **70 passed** (62 + 8); Regression grün:
  **P4 88** · **P5 130** (rein additiv im P6-Paket + 1 `.gitignore`-Zeile). **Committet** (dieser
  Commit = HEAD von `phase6-debate`; Hard-Regel `4abd8b3` befolgt: Note + Modul-7-Zeile (✅) +
  `.gitignore` im selben Commit. Eine self-referenzielle SHA ist im Commit nicht eintragbar →
  konkrete SHA trägt der nächste Session-Block nach, wie die Vorgänger-Module).

### Next
- **Modul 8 — `scripts/wiring.py` + `smoke_test.py` + `live_test.py` + `debate/credentials.py`**
  (Concept §8). `wiring.py`: baut den geteilten `research.LLMClient` (Keyring `anthropic_api_key`
  via `debate/credentials.py`-Shim = Phase-1 `get_credential`), `token_meter_path` →
  `data/state/llm_usage.json`, instanziiert `Debate(broker, llm, cfg, audit=...)` mit echtem Broker
  + **Audit-Callable** `lambda o, c: write_debate(o, c, "data/state/debate_log.json")` (Modul 7 →
  Callable-Adapter). Liefert die **Runner-Factory** `debate_runner = lambda cand: build_debate(cfg).run(cand)`
  (lazy/DI, analog P5 `research_runner`). `smoke_test.py` = eine echte Debatte, dry (kein Executor/Save).
  `live_test.py` = Operator-Lauf im vollen P5-Executor (Modul 9-Naht muss dafür existieren — Reihenfolge
  prüfen: ggf. Modul 9 vor `live_test.py`).
- **⚠ [VERIFY] vor Modul 8:** `scripts.wiring`-Namenskollision (P4/P5/P6 haben alle `scripts/wiring.py`).
  P6-Wiring darf **nicht** versehentlich P4/P5-`scripts.wiring` importieren — Client/Debate selbst bauen,
  Import-Pfad isolieren (war eine P5-Falle).

### Offene Punkte / [VERIFY]
- `scripts.wiring`-Namenskollision (Modul 8, s. o.). Sonst nichts offen.

### Gotchas (für den Re-Entry)
- Branch **`phase6-debate`**. Module 1–7 committet (Modul 6 `2330d7d`; **Modul 7 = HEAD**, SHA siehe
  `git log -1`) — rein additiv: `debate/audit.py`, `tests/test_audit.py`, `.gitignore`, diese `CLAUDE.md`.
- `write_debate` ist **kein** Top-Level-Export; Modul 8 bindet es als Audit-**Callable** `(o,c)->None`
  an den Orchestrator (`Debate(..., audit=lambda o, c: write_debate(o, c, path))`).
- Test-Helfer in `test_audit.py` sind lokal (`_make_outcome`/`_make_context`, Direkt-Konstruktion der
  frozen Dataclasses) — **kein** conftest-Touch nötig (Modul 7 berührt keine geteilten Fixtures).
- Clock-Freeze im Test via `monkeypatch.setattr(timeutil, "_utcnow", …)` (autouse-Fixture) → `ts`
  deterministisch.

---

## Session stopped — 2026-06-15 (Modul 6 — `debate/debate.py`, der Orchestrator-Kern)

### Completed
- **Modul 6 — `debate/debate.py` + `tests/test_debate.py`** ✅ (≥12 → **14 neue Tests**):
  `class Debate(broker, llm_client, config, *, audit=None, now_fn=time.monotonic)` +
  `run(candidate) -> DebateOutcome`. **Reine Komposition** der Module 2–5 — keine neue AI-Logik;
  die einzige AI sind die Bull/Bear/Judge-Requests via `ask_agent`. Flow: `build_debate_context`
  (Fehler → ABSTAIN, **null** Agenten-Requests) → Runden-Loop `1..max_rounds` je **Bull→Bear→Judge**
  (`budget.register`+`budget.check` nach jedem Turn) → Early-Stop bei Judge-`conclude=true` →
  Verdict aus letztem Judge-Answer.
- **Fail-closed (Decision J):** `try/except DebateError` (deckt `DebateLLMError` +
  `DebateBudgetExceeded` + Context-`DebateError`) **plus** defensives `except Exception` →
  **ABSTAIN** mit `rationale=str(exc)`, Teil-Transkript/`token_summary` mitgeführt. **Nie** eine
  Exception nach außen, **nie** „trotzdem traden".
- **AI-Output-Validierung (Hard Rule 3):** `decision ∉ {TRADE,ABSTAIN}` → ABSTAIN; `TRADE` ohne
  brauchbare `direction ∈ {BUY,SELL}` → fail-closed ABSTAIN; `ABSTAIN` → `direction=None`
  (egal was das Modell lieferte). `confidence` wird via `_as_float` nur **geloggt/getragen** und
  taucht in **keiner** Steuer-Verzweigung auf (Decision H — Test pinnt: low-conf tradet, high-conf
  ABSTAIN tradet nicht).
- **Deterministische Transkript-Kompression (v1, kein Extra-Request):** Latch bei kumulativen
  Input-Tokens > `compression_trigger_pct × max_cumulative_input_tokens`; ab dann rendern die
  Prompts eine **komprimierte Sicht** (`_compress` = jüngster Turn je Agent, in Rundenreihenfolge).
  Das **volle** Transkript bleibt für `DebateOutcome.transcript` + Audit erhalten (Decision I) —
  Test pinnt beides (Runde-1-Marker verschwindet aus dem späten Prompt, Outcome trägt alle 9 Turns).
- **`Debate`-Export** in `debate/__init__.py` ergänzt (`from debate.debate import Debate`).
- **Isolation:** `debate.py` importiert nur `debate.*` + stdlib — **kein** `anthropic`/
  `broker_wrapper`/`research` (Broker + Client duck-typed via lokalem `Protocol`). Hygiene-grep clean.
- **Verifiziert:** `pytest phase6_debate/tests -q` → **62 passed** (48 + 14); Regression grün:
  **P4 88** · **P5 130** (Session rein additiv im P6-Paket — kein Fremd-File berührt).

### Zwei dokumentierte Design-Entscheidungen (Code = Source of Truth; Concept §6 stimmt sonst)
- **`audit` ist ein injizierter Callable** `(outcome, ctx) -> None`, nicht ein Objekt mit
  `.write(...)`. Modul 7 liefert `write_debate(outcome, ctx, path)`; die Modul-8-`wiring` adaptiert
  das zu diesem Callable (Pfad gebunden). Hält Modul 6 von der Modul-7-Signatur entkoppelt; Tests
  geben einen Recorder. Audit wird **genau einmal** vor Return gerufen (nur wenn `ctx` gebaut wurde;
  Audit-Fehler werden geloggt + geschluckt, brechen das Ergebnis nie).
- **Per-Rollen-`max_tokens` setzt der Orchestrator** direkt am geteilten Client
  (`self._llm.max_tokens = max_tokens_agent|max_tokens_judge`) **vor** `ask_agent` — das ist der
  **einzige** Per-Turn-Knopf, den `ask_agent` nicht setzt (`ask_agent` setzt Model+Temperatur).
  Vermeidet eine erneute Edit am committeten Modul 4. (→ Concept §6 mit dieser dated Reconciliation
  zu annotieren, falls noch nicht.)

### Next
- **Modul 7 — `debate/audit.py` + `tests/test_audit.py`** (≥5 Tests, Concept §7, Decision I):
  `write_debate(outcome: DebateOutcome, ctx: DebateContext, path: str | None) -> dict` — append an
  `debate_log.json` (atomar via temp + `os.replace`; korrupte Datei → frisch + Warnung, wie
  `token_meter._load_log`; `path=None` → nicht schreiben, Record zurückgeben). **Vorwärtskompatibles
  Schema** (P9 `decision_context` / `market_regime_snapshots` ohne Reshaping ingestierbar):
  `{ts, epic, seed_direction, final_decision, final_direction, confidence(advisory), rounds_used,
  rationale, regime_snapshot{spread_pct, market_status, drift_at_pick, score_at_pick,
  recent_bars_summary}, transcript[...], token_summary{...}}`. Mapping-Kommentar im Modul. Tests:
  Schema vollständig + alle P9-Mapping-Keys; atomar; korrupte Datei → frisch; `path=None` schreibt
  nicht; append erhält Vorgänger. **Wiring (Modul 8) adaptiert `write_debate` → den Audit-Callable.**

### Offene Punkte / [VERIFY]
- Kein [VERIFY] für Modul 7 offen. Übrig fürs Paket: `scripts.wiring`-Namenskollision (P4/P5/P6)
  → **Modul 8** (P6-Wiring darf nicht P4/P5-`scripts.wiring` importieren — baut Client/Debate selbst).

### Gotchas (für den Re-Entry)
- Branch **`phase6-debate`**. Module 1–5 committet (`b2da0db`…`ad6ff65`); **Modul 6 noch nicht** —
  Working Tree liegt zur Review (rein im P6-Paket: `debate/debate.py`, `debate/__init__.py`,
  `tests/conftest.py` (FakeLLM), `tests/test_debate.py`, diese `CLAUDE.md`). ⚠ **Neue Hard-Regel
  (`4abd8b3`): Commit ⇒ Note-Update im selben Commit** — beim Committen die Modul-6-Zeile (✅) +
  diesen Block mit hineinnehmen und „noch nicht committet" → „committet `<sha>`" flippen.
- **`audit` = Callable**, nicht `.write`-Objekt (s. o.) — Modul 7 baut die Funktion, Modul 8 bindet
  sie als `lambda o, c: write_debate(o, c, path)`.
- **`FakeLLM`** (conftest) ist scripted: `answers`-Liste, `usage`-dict (→ `last_usage`),
  `raises_on`-Index, `turns`/`seen_users`-Recording. Direkt importierbar
  (`from tests.conftest import FakeLLM`), **kein** Fixture.
- `_compress` hält den **jüngsten** Turn je Agent (nicht die Historie) — bewusst „verlustarm" v1;
  LLM-basierte Kompression ist ein späterer Swap (Carry-over).

---

## Session stopped — 2026-06-15 (Modul 5 — `debate/budget.py`)

### Completed
- **Modul 5 — `debate/budget.py` + `tests/test_budget.py`** ✅ (≥6 → **10 neue Tests**):
  `class DebateBudget(config, *, now_fn=time.monotonic)` — die **Kosten-Disziplin-Struktur**
  der Phase (Decision E/J). `register(usage: dict)` faltet pro Turn genau den
  `ask_agent`-Rückgabe-Record (`token_meter`-Shape) in die Akkumulatoren (zählt **einen** Turn,
  toleriert fehlende Keys **und** `{}` via `_as_int`/`_as_float`). `check()` raised
  **`DebateBudgetExceeded` beim ERSTEN** Breach von `max_total_calls` /
  `max_cumulative_input_tokens` / `max_cumulative_output_tokens` / `wall_clock_timeout_s`
  (Grenze: **`>` = Breach, `==` erlaubt** = Cap ist „max allowed"; Breach-Detail genannt + auf
  stderr geloggt). `summary() -> dict` liefert das Aggregat in **exakt der Audit-Key-Menge**
  (Modul 7 / Concept §7: `input_tokens`/`output_tokens`/`cache_read_input_tokens`/
  `cache_creation_input_tokens`/`est_cost_usd`/`est_cost_eur`) **+ `total_calls`** (additiv,
  forward-compat-unschädlich) → passt ohne Reshaping auf `DebateOutcome.token_summary`.
- **Wall-Clock deterministisch:** `now_fn` injiziert (wie P5 `executor`/`monitor`); Tests
  nutzen einen `_FakeClock` (Sequenz, letzter Wert wiederholt) → **kein echtes Warten**;
  Boundary-Test pinnt `==` erlaubt / `>` breacht.
- **Isolation:** `budget.py` importiert nur `debate.models` (`DebateBudgetExceeded`/
  `DebateConfig`) + stdlib (`time`/`logging`/`typing`) — **kein** `anthropic`/`broker_wrapper`/
  `research`. Hygiene-grep clean.
- **Verifiziert:** `pytest phase6_debate/tests -q` → **48 passed** (38 + 10); Regression grün:
  **P4 88** · **P5 130** (Session ist rein additiv im P6-Paket — keine Fremd-Datei berührt).
  **Nicht committet** (User triggert Commits).

### Next
- **Modul 6 — `debate/debate.py` + `tests/test_debate.py`** (≥12 Tests, Concept §6, **Kern der
  Phase**): `class Debate(broker, llm_client, config, *, audit=None, now_fn=time.monotonic)` +
  `run(candidate: dict) -> DebateOutcome`. Flow: (1) `build_debate_context(candidate, broker,
  config)` — Fehler → **ABSTAIN** (fail-closed, kein Agenten-Request); (2) Runden-Loop
  `1..max_rounds`: **Bull**(Haiku) → **Bear**(Haiku) → **Judge**(Sonnet) via `ask_agent` +
  `prompts.build_*_prompt`; nach jedem Turn `budget.register(usage)` + `budget.check()` (Breach
  → ABSTAIN); (3) Transkript-Kompression bei `compression_trigger_pct` (deterministisch, **kein**
  Extra-Request in v1); (4) Early-Stop bei Judge-`conclude=true`; (5) Endurteil = letzter
  Judge-Output → `DebateOutcome`, `decision=="ABSTAIN"` → `direction=None`; (6) **jeder**
  `DebateError`/`DebateLLMError`/`DebateBudgetExceeded` an jeder Stelle → ABSTAIN (nie Exception
  nach außen, nie „trotzdem traden"); (7) `audit.write(...)` vor Return (falls gesetzt — Audit ist
  aber erst Modul 7; in Modul 6 `audit=None`/injizierter Stub). `confidence` darf in **keiner**
  Steuer-Verzweigung auftauchen (advisory-only-Test). `token_summary` = `budget.summary()`.
- **`Debate`-Export** landet in `debate/__init__.py` mit Modul 6 (Concept §"Modul-Tree":
  `exports: Debate, DebateConfig, DebateOutcome`).

### Offene Punkte / [VERIFY]
- Kein [VERIFY] offen für Modul 6 (Context-Builder/Prompts/Caching/Budget sind alle gebaut +
  grün). Übrig fürs Paket: `scripts.wiring`-Namenskollision (P4/P5/P6) → **Modul 8**.

### Gotchas (für den Re-Entry)
- Branch **`phase6-debate`**. Module 1–3 committet (`b2da0db`, `a82cbc7`, `3275626`); **Modul 4
  + Modul 5 noch nicht committet** — Working Tree liegt zur Review. ⚠ **Modul 4 fasst 4 P4-Dateien
  an** (additiv) — beim Commit mit hineinnehmen (s. Modul-4-Block unten); **Modul 5 ist rein im
  P6-Paket** (`debate/budget.py` + `tests/test_budget.py`).
- `DebateBudget.summary()` liefert `total_calls` **zusätzlich** zu den 6 Audit-Keys — Modul 6/7
  dürfen sich darauf verlassen, dass die 6 Audit-Keys da sind, und `total_calls` ignorieren/nutzen.
- `register` zählt **jeden** Turn (auch leeres `{}`-Usage); `check()` ist getrennt → Modul 6 ruft
  beide pro Turn (erst `register`, dann `check`).
- `budget.py` ist **kein** Top-Level-Export — Zugriff via `from debate.budget import DebateBudget`.

---

## Session stopped — 2026-06-15 (Modul 4 — `llm_caching.py` + additive P4-Edits)

### Completed
- **Modul 4 — `debate/llm_caching.py` + `tests/test_llm_caching.py`** ✅ (≥6 → **9 neue Tests**):
  dünner P6-Seam `ask_agent(client, system, user, schema, *, model, temperature) -> (dict, dict)`
  über den **einen geteilten** `research.LLMClient` (Decision-F-Reuse; **kein** zweiter Call-Punkt,
  **kein** `llm_common`). Setzt `client.model`/`temperature` pro Turn, gibt `(answer, usage_record)`
  zurück (`usage` = `token_meter`-Record-dict → passt auf `DebateBudget.register`, Modul 5).
  Client-Fehler → **`DebateLLMError`** (fail-closed → ABSTAIN). Importiert nur `debate.models` +
  stdlib (Client duck-typed via `Protocol`; **kein** `anthropic`-Import).
- **Additive P4-Edits (dokumentierte Decision-F/G-Ausnahme, P4-Default bit-identisch):**
  1. `research/llm_client.py`: Ctor `cache_system: bool = False` + `_build_create_kwargs(...,
     cache_system=False)` → bei `True` wird `system` zur **Content-Block-Liste** mit
     `cache_control:{"type":"ephemeral"}` (plain-String kann den Marker nicht tragen, SDK 0.106
     `TextBlockParam`). `_raw_call` reicht `self.cache_system` durch. Neu: `self.last_usage` fängt
     in `_attempt` den Meter-Record ab (Per-Turn-Usage für den reusing caller).
  2. `research/token_meter.py`: `record(...)` additiv um `cache_read_input_tokens` +
     `cache_creation_input_tokens` (8-Feld-Record; alte 6 unverändert).
  3. `scripts/usage_report.py`: `cache_hit_ratio()` + Cache-Spalten + Cache-Hit-Zeile im TOTAL.
  4. `tests/test_token_meter.py`: Frozen-Shape-Test auf 8 Keys angepasst.
- **[VERIFY] #1 + #2 RESOLVED** (SDK 0.106.0) — Content-Block-Liste für `cache_control`;
  `Usage` hat beide Cache-Felder. Details: Concept §4 + die [VERIFY]-Liste oben.
- **Verifiziert:** `pytest phase6_debate/tests -q` → **38 passed** (29 + 9); Regression grün:
  **P4 88** (additive Edits, Default unverändert), **P5 130**. Hygiene-grep clean (Achtung: `\bPUT\b`
  matcht das engl. Verb „put", `\bCALL\b` „call" → in Prosa „set/request" nutzen). `llm_caching.py`
  importiert nichts aus `anthropic`. `usage_report` zeigt Cache-Hit-Ratio (manuell sanity-geprüft).
  **Nicht committet** (User triggert Commits).

### Next
- **Modul 5 — `debate/budget.py` + `tests/test_budget.py`** (≥6 Tests, Concept §5, Decision E/J):
  `class DebateBudget.__init__(config, *, now_fn=time.monotonic)`; `register(usage: dict)` (nach
  jedem Turn — `usage` ist genau der `ask_agent`-Rückgabe-dict); `check()` → **raises
  `DebateBudgetExceeded`** beim **ersten** Breach von `max_total_calls` /
  `max_cumulative_input_tokens` / `max_cumulative_output_tokens` / `wall_clock_timeout_s`;
  `summary() -> dict` (Aggregat für `DebateOutcome.token_summary`, inkl. Cache-Felder).
  Tests mit **injizierter `now_fn`** (gemockte Zeit, **kein echtes Warten**): jeder Cap einzeln löst
  aus; Aggregat summiert input/output/cache; unter Cap kein Raise; Wall-Clock deterministisch.
- **Kein [VERIFY] offen für Modul 5.** (Übrig: `scripts.wiring`-Namenskollision → Modul 8.)

### Offene Punkte / [VERIFY]
- `scripts.wiring`-Namenskollision (P4/P5/P6) — **vor Modul 8** prüfen. Sonst nichts offen.

### Gotchas (für den Re-Entry)
- Branch **`phase6-debate`**. Module 1–3 committet (`b2da0db`, `a82cbc7`, `3275626`); **Modul 4
  noch nicht** — Working Tree liegt zur Review. **Modul 4 fasst P4-Dateien an** (4 Stück, additiv) —
  beim Commit mit hineinnehmen (`research/llm_client.py`, `research/token_meter.py`,
  `scripts/usage_report.py`, `tests/test_token_meter.py`) + die P4-`CLAUDE.md`-Notiz.
- `ask_agent`-`usage` ist ein **dict** (Record), kein SDK-Usage-Objekt → Modul 5 `register` nimmt dicts.
- Geteilter Client: `cache_system` wird **bei Konstruktion** gesetzt (Modul 8 wiring), nicht pro Call.

---

## Session stopped — 2026-06-15 (Modul 3 — `prompts.py`)

### Completed
- **Modul 3 — `debate/prompts.py` + `tests/test_prompts.py`** ✅: `build_bull_prompt` /
  `build_bear_prompt` / `build_judge_prompt(context, transcript) -> (system, user, json_schema)`.
  Reine Funktionen, **kein AI/I/O/Clock** — letzter Code-Schritt vor den AI-Requests, gespiegelt
  an P4 `research.prompt`. Importiert nur `debate.models` (+ stdlib). Prompts sind **Deutsch**.
  - **Cache-Präfix-Disziplin (Decision D):** Rollen-Instruktion **+** gerenderter Kontext stehen
    im **system**-Block (stabil über die ganze Debatte → Modul-4-`cache_control` liest Cache);
    nur das wachsende **Transkript** steht im **user**-Teil. Test pinnt das Invariant
    (`test_context_in_system_not_in_user`).
  - **Delay-Ehrlichkeit:** System trennt das **VERZÖGERTE** P4-Stimmungsbild (Seed/Drift,
    yFinance ~15 min) explizit von den **IG-ECHTZEIT**-Feldern (Spread, jüngste Bars). `None`
    → ehrliches „n/a" über den einen `_fmt`-Choke-Point (nie als 0 gefälscht, wie P4).
  - **Schemas** (frische Dicts je Request): Bull/Bear minimal (`{"argument": str}`); Judge =
    `{decision∈{TRADE,ABSTAIN}, direction(BUY|SELL|null), confidence(number|null), rationale,
    conclude(bool)}`. **Anthropic-Regeln aus P4 befolgt:** nullable via **`anyOf`** + `null`-Branch
    (Type-Arrays → 400), **kein** `minimum`/`maximum` auf `confidence` (Range nur in Prosa;
    `confidence` ist advisory, Decision H — gatet nichts). Judge ist die echte Richtungsquelle
    (darf den Seed in die Gegenrichtung umkehren), `conclude` steuert den Early-Stop (Modul 6).
- **Hygiene-Gotcha gelöst:** Der §0-`grep -i` matchte (a) englisches „call" in einem Kommentar
  („per call" → „per request") und (b) die Banned-Token-Liste im Test selbst → Tokens werden jetzt
  **split-then-joined** (`"CA"+"LL"` …), damit die Literale nicht im Source stehen. Gate wieder clean.
- **Verifiziert:** `pytest phase6_debate/tests -q` → **29 passed** (19 + 10 neu, ≥6 gefordert);
  Regression grün: P4 **88**, P5 **130** unberührt. Hygiene-grep clean; `prompts.py` importiert
  nichts aus `anthropic`/`broker_wrapper`/`research`. **Nicht committet** (User triggert Commits).

### Next
- **Modul 4 — `debate/llm_caching.py` + `tests/test_llm_caching.py`** (≥6 Tests, Concept §4) —
  **Cache-Präfix + Meter-Erweiterung (Decision D/G/F)**. Zwei **additive** Edits im **P4-Code**
  (dokumentierte Ausnahme):
  1. `research/llm_client.py` → `_build_create_kwargs(..., cache_system: bool=False)`: bei `True`
     `cache_control:{"type":"ephemeral"}` auf den System-Block; Konstruktor um `cache_system=False`
     erweitern (durchgereicht). **Default False ⇒ P4 unverändert** (alle 88 P4-Tests müssen grün bleiben).
  2. `research/token_meter.py` → `record(...)` additiv um `cache_read_input_tokens` +
     `cache_creation_input_tokens` (via `_usage_int`-Helfer, existieren schon); `usage_report.py`
     um Cache-Hit-Ratio + Σ-Kosten/Debatte erweitern.
  - P6-seitig dünner Wrapper `ask_agent(client, system, user, schema, *, model, temperature) ->
    (dict, usage)`, ruft den geteilten `research.LLMClient` mit `cache_system=True` und gibt `usage`
    für `budget.py` (Modul 5) zurück.
- **[VERIFY] vor Modul 4 (gegen installierte `anthropic`-SDK):** (a) block-level `cache_control` auf
  `system` unterstützt? Falls SDK nur Content-Block-Liste akzeptiert → System als
  `[{"type":"text","text":…,"cache_control":…}]` bauen. (b) `message.usage`-Feldnamen
  (`cache_creation_input_tokens` / `cache_read_input_tokens`) gegen die SDK-Version.
- ⚠ **Modul 4 editiert P4-Code** (außerhalb des P6-Pakets) — das ist die explizit dokumentierte
  Decision-F/G-Ausnahme. Default-Verhalten von P4 muss **bit-identisch** bleiben (cache default aus).

### Offene Punkte / [VERIFY]
- SDK `cache_control`-Form + `message.usage`-Cache-Feldnamen (Modul 4),
  `scripts.wiring`-Namenskollision (Modul 8). Jeweils **vor** dem betroffenen Modul prüfen.

### Gotchas (für den Re-Entry)
- Branch **`phase6-debate`**. Module 1+2 sind committet (`b2da0db`, `a82cbc7`); **Modul 3 noch nicht**
  — Working Tree liegt zur Review (User triggert Commits).
- `prompts.py` ist **kein** Top-Level-Export — Zugriff via `from debate.prompts import …`.
- Hygiene-Disziplin: englisches „call/put" in Prosa/Kommentaren vermeiden (matcht `grep -i`);
  in Tests, die auf Abwesenheit prüfen, Tokens split-then-joinen.

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
