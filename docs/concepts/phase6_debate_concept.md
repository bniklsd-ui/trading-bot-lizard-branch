# Phase 6 — Implementierungsplan für Claude Code (Bull/Bear/Judge-Debatte)

> **Status:** Architektur geklärt (11 Entscheidungen A–K unten gelockt), Contracts gegen den
> **echten Repo-Code** (`main`, Stand 2026-06-12) verifiziert — nicht gegen Konzeptdokumente.
> Phase 6 ist der **erste echte Mehr-Agenten-AI-Pfad** und der **teuerste Pfad im System**.
> Kostenkorrektheit (Caching + Metering + Caps) wiegt hier so schwer wie Funktionsumfang.
>
> **Quelle der Wahrheit bleibt das Repo.** Jede Signatur unten ist gegen `executor.py`,
> `gates.py`, `llm_client.py`, `token_meter.py`, `models.py` gelesen. Jede **[VERIFY]**-Stelle
> ist **vor** dem Bauen gegen den echten Code / die installierte SDK zu prüfen — genau das hat
> in P4/P5 den `CALL/PUT`- und den `currencyCode`-Bug gefangen.
>
> **AI-Grenze (Projekt-Kernprinzip):** „So wenig AI wie möglich, so viel AI wie nötig." Phase 6
> fügt AI **nur** für Bull/Bear-Argumentation + Judge-Synthese hinzu. Sizing, Gates, VETOs,
> Order, Monitoring, Reconcile, **und der gesamte Kontextaufbau** bleiben deterministischer Code.
> Die Debatte bekommt **niemals** den Broker oder die VETO-Funktionen in die Hand.

---

## 0. Geklärte Architektur-Entscheidungen (gelockt)

| # | Thema | Festlegung | Begründung |
|---|---|---|---|
| **A** | Platzierung & Edit | Debatte als injiziertes `debate_runner`-Callable **zwischen Gate 2 und Gate 3** in `executor.run()`. **Minimale Edit an `phase5_execution/execution/executor.py` erlaubt.** Neues Paket `phase6_debate/` (analog `phase4_research/research/`). **Der neue Konstruktor-Arg ist default ein No-Op-Passthrough** → P5 bleibt ohne Debatte AI-frei und alle bestehenden P5-Tests grün. **Pflicht: volle P5-Suite erneut + neue Regressionstests (siehe §Regression).** | Das ist die in P5 bewusst gebaute Naht (`gate_direction_consistency` + `build_order_plan`). Default-Passthrough hält den „No AI in P5"-Invariant **strukturell**, nicht nur per Konvention. |
| **B** | Override vs. bestätigen | Debatte ist die **echte Richtungsquelle**: Bull/Bear argumentieren, Judge emittiert finale `direction`, die vom P4-Seed **abweichen darf** (Flip BUY↔SELL möglich). P4-Candidate = Seed + Epic + Kontext. | Confirm-only würde den Bear zum Feigenblatt machen; der adversariale Wert (und die Kosten) rechtfertigen sich nur, wenn ein Flip möglich ist. Gate 5 ist Pass-Through und verträgt eine geflippte Richtung. |
| **C** | Modell pro Rolle | Bull/Bear default **`claude-haiku-4-5-20251001`** ($1/$5), Judge default **`claude-sonnet-4-6`** ($3/$15). **Alle drei Modelle config-überschreibbar** (`model_bull`/`model_bear`/`model_judge`). Pricing-Rows existieren bereits. | Bull/Bear sind die Call-Mehrheit; Haiku dort senkt Kosten ~3× ohne Synthese-Qualität (Judge) zu opfern. Konfigurierbar, falls Haiku im Betrieb argumentativ zu schwach ist → dann pro Rolle auf Sonnet hochziehen. |
| **D** | Client-Form | **Single-shot beibehalten** (`research.LLMClient.ask_candidate(system, user, json_schema)` pro Agenten-Turn wiederverwenden). Debatten-Transkript wird in den `user`-Content serialisiert; **kein** Umbau auf eine multi-turn-`messages`-Liste. | Passt zum bewährten Client **und** maximiert Cache-Reads (stabiler System+Kontext-Präfix, nur das Transkript wächst). Ein Multi-Turn-Umbau wäre mehr Risiko am erprobten Retry-Pfad für wenig Gewinn. |
| **E** | Runden-Struktur | **Early-Stop**: `max_rounds` (default 5), Judge bricht bei Konsens/klarer Lage früher ab. **Harte Caps** auf Calls **und** kumulative Tokens **und** Wall-Clock pro Zyklus. Jede Cap-Überschreitung → **fail-closed → ABSTAIN**. | „Fix 5×3" ist die Kostenexplosion. Early-Stop + harte Caps machen die Kosten-Disziplin strukturell. Cap-Breach traded nie „trotzdem". |
| **F** | Geteilte LLM-Infra | v1 pragmatisch: Phase 6 **importiert `research.token_meter` + Pricing + `LLMClient`** als **dokumentierte Phase-Ausnahme** (wie `research/credentials.py` Phase 1 wiederverwendet). Keine vorzeitige `llm_common`-Extraktion. | Ein zweiter Consumer rechtfertigt noch keine Extraktion. Die Ausnahme wird im Modul-Docstring + CLAUDE.md benannt, nicht versteckt. |
| **G** | token_meter erweitern | Record-Form **additiv** um `cache_read_input_tokens` + `cache_creation_input_tokens` erweitern (alte Felder bleiben → kein Bruch des „frozen"-Kontrakts). Per-Debatte-Aggregat. `usage_report.py` zeigt Cache-Hit-Ratio + Kosten pro Debatte. **P4-Tests erneut grün.** | Ohne das ist Caching **unsichtbar** — du kannst nicht beweisen, dass die teuerste Optimierung der Phase greift. Additiv = rückwärtskompatibel (Cache-Felder = 0 in P4). |
| **H** | Confidence-Semantik | Judge emittiert qualitative `decision ∈ {TRADE, ABSTAIN}` (Reasoning-Output). `confidence` wird **nur geloggt**, gatet **nichts** — auch keine Schwellen-Abstain. | Eine numerische Confidence-Schwelle wäre genau das frequenz-/zahlbasierte Anti-Pattern aus der Freund's-Bot-Analyse. ECE ~0.1 → die Zahl ist fürs Gating wertlos, fürs spätere P7-Outcome-Anchoring aber sammelnswert. |
| **I** | Persistenz | **Kein SQLite** (DB ist bis P7 read-only). In-memory ans Result + **JSON-Audit** `data/state/debate_log.json` (gitignored, wie `llm_usage.json`). **Audit-Schema vorwärtskompatibel** zu den P9-Tabellen `decision_context` / `market_regime_snapshots`, damit die Daten **später fürs Lernen** ohne Reshaping ingestierbar sind (Feld-Mapping in §Audit). | Hält den DB-read-only-Invariant. Voller Bull/Bear/Judge-Verlauf bleibt erhalten — nur nicht in der Lern-DB. |
| **J** | Fail-closed | API-Timeout/Fehler/Cap-Breach mitten in der Debatte → **ABSTAIN → NO_TRADE**, nie „trotzdem traden". `debate_runner` bekommt **strukturell nie** Broker oder VETO-Funktionen. | Konsistent mit dem VETO-fail-closed-Prinzip; macht „kein Force-Trigger" strukturell (die Debatte *kann* keinen VETO umgehen, weil sie ihn nicht referenziert). |
| **K** | Council-Bezug | `verbesserungsvorschlaege` aus dem Council-Skill = **Phase 9**, nicht jetzt. Phase 6 baut nur die saubere Naht. | Scope-Disziplin. |

### Config-Defaults (`DebateConfig`, v1 — am echten Profit/Kosten zu tunen, nicht jetzt)

| Feld | Default | Bezug |
|---|---|---|
| `model_bull` / `model_bear` | `claude-haiku-4-5-20251001` | Decision C, überschreibbar |
| `model_judge` | `claude-sonnet-4-6` | Decision C, überschreibbar |
| `max_rounds` | `5` | Decision E (1 Runde = Bull + Bear + Judge-Interim) |
| `early_stop` | `True` | Decision E |
| `max_total_calls` | `18` (= 5×3 + Puffer) | harter Cap, Breach → ABSTAIN |
| `max_cumulative_input_tokens` | `120_000` | harter Cap, Breach → ABSTAIN |
| `max_cumulative_output_tokens` | `12_000` | harter Cap, Breach → ABSTAIN |
| `wall_clock_timeout_s` | `120` | harter Cap, Breach → ABSTAIN |
| `cache_system` | `True` | Decision D/G (Phase 6 cacht den stabilen Präfix) |
| `compression_trigger_pct` | `0.65` | Transkript-Kompression bei ~65 % des Token-Budgets |
| `temperature_bull` / `temperature_bear` | `0.4` | etwas Divergenz erwünscht |
| `temperature_judge` | `0.1` | Synthese soll konsistent sein |
| `max_tokens_agent` | `512` | pro Bull/Bear-Turn |
| `max_tokens_judge` | `768` | Judge braucht Synthese-Raum |
| `debate_log_path` | `data/state/debate_log.json` | gitignored Audit |
| `confidence_gates_nothing` | `True` (Label/Doku) | Decision H — Konstante zur Selbstdokumentation, kein Verhalten |
| `bars_resolution` | `"MINUTE_5"` | Module 2 — IG-Echtzeit-Bars für `recent_bars_summary` |
| `bars_count` | `12` (≈ 1 h) | Module 2 — Bar-Fenster für `recent_bars_summary` |

> 📝 **Reconciliation 2026-06-15 (Code = Source of Truth, Module 2):** Die obige
> Tabelle hatte ursprünglich **keine** Bar-Resolution/-Count-Felder, der
> `context_builder` braucht aber eine Auflösung/Anzahl für `get_ohlcv`. Die zwei
> Felder `bars_resolution`/`bars_count` wurden **additiv** zu `DebateConfig`
> ergänzt — **verbatim** aus den gelockten Phase-5-Momentum-Defaults übernommen
> (`ExecutionConfig.momentum_resolution="MINUTE_5"` / `momentum_count=12`, gleiche
> Bars, gleiches Instrument), kein neuer/erfundener Wert. v1, am Profit zu tunen.

### Anmerkung zu Decision H (bewusste Wette — für später festgehalten)

Decision H ist **schärfer als das Kickoff-Handover** (das eine provisorische Confidence-Schwelle
für ABSTAIN erlaubt). Hier gatet `confidence` **nichts**; nur das qualitative Judge-`decision`
(TRADE/ABSTAIN) entscheidet. Das vermeidet das zahl-/frequenzbasierte Confidence-Anti-Pattern
(ECE ~0.1 → eine unkalibrierte Zahl zum Gate zu machen ist Selbstbetrug).

**Der Preis dieser Wette:** Man verliert die billige Möglichkeit, „nur bei hoher Überzeugung
traden" per Schwelle zu erzwingen. **Die richtige Reaktion**, falls der Judge im Betrieb zu oft
schwach-überzeugt `TRADE` sagt, ist **bessere Judge-Prompts / strengere Early-Stop-/Konsens-Logik
(Decision E)** — **nicht** das nachträgliche Einziehen einer numerischen Confidence-Schwelle. Wer
später eine `confidence`-Schwelle einbauen will → stop, das ist genau das Anti-Pattern, das diese
Entscheidung ausschließt. Die geloggte Confidence (Audit + `llm_usage`/`debate_log`) dient
**ausschließlich** dem späteren P7-Outcome-Anchoring, nie dem Gating in P6.

---

## Step 0 — Legacy-/Naming-Hygiene (eigener Commit, VOR jeder Logik) — **diesmal leicht**

> ✅ **DONE 2026-06-12** (commit `c8d5ba1`, lokal, nicht gepusht): `ROADMAP.md` +
> Root-`CLAUDE.md` Phase-6-Zeilen auf die gelockten 11 Entscheidungen + die AI-Grenze
> gezogen. `turbo_candidates.json` unangetastet; kein Code geändert.

P4/P5 haben Options-/`CALL`/`PUT`-Logik bereits entfernt; die einzigen verbliebenen „turbo"-Treffer
im Code sind der **eingefrorene** Dateiname `turbo_candidates.json` und Prosa, die ihn als
Legacy-Namen erklärt. Phase-6-Step-0 ist daher minimal:

1. **Im neuen Paket `phase6_debate/` keine** „turbo"/Options-Begriffe einführen
   (`CALL`/`PUT`/`strike`/`otm`/`issuer`/`FLIP`/`option_check`). Richtung ist **BUY/SELL**.
2. **`turbo_candidates.json` NICHT anfassen/umbenennen.** Phase 6 liest den Candidate **nach**
   Gate 2 (also nach dem `load_candidates()`) und reichert ihn **nur in-memory** an — die
   persistierte Datei und ihr Schema bleiben unverändert (siehe §Naht). Kommentar im Code:
   *„legacy name, frozen contract — Phase 6 enriches the loaded candidate in-memory only."*
3. **Doku-Abgleich:** Root-`CLAUDE.md` / `ROADMAP.md` Phase-6-Zeilen auf das neue Paket +
   die AI-Grenze ziehen (Debatte = AI nur für Argumente/Synthese).

**Done when:**
`grep -rin "turbo\|\bCALL\b\|\bPUT\b\|strike\|otm\|issuer\|FLIP\|option_check" phase6_debate/ --include=*.py`
liefert **keinen** Treffer; `turbo_candidates.json` bleibt unangetastet. Eigener Commit.
> ⚠ Step-0-`grep -i` matcht englisches „call"/„put" in Prosa (z. B. „LLM call", „put at risk").
> In Docstrings „invocation"/„request" schreiben; `*_call(s)`-Identifier sind ok.

---

## Step C — Packaging: editable install (eigener Commit, früh)

> ✅ **DONE 2026-06-12** (Scaffold-Block, noch nicht committet): `phase6_debate/pyproject.toml`
> (`name="debate"`, `include=["debate*"]`) + Repo-Root `scripts/dev_install.sh` um
> `phase6_debate` erweitert (Reihenfolge P1→…→P6, nach P4). `import debate` löst über den
> editable install auf — **kein `sys.path`-Hack**; `pytest phase6_debate/tests -v` grün
> (Packaging-Smoke `tests/test_packaging.py`). [VERIFY] Top-Level-Importname = `debate` (bestätigt).

Wie P5: editable installs, kein `sys.path`-Hack im Runtime-Paket.

1. **`phase6_debate/pyproject.toml`** (minimal, wie P5). **[VERIFY]** echten Top-Level-Importnamen
   (`import debate`) eintragen.
2. **`scripts/dev_install.sh` (repo-root) erweitern:** Phase 6 in Abhängigkeitsreihenfolge
   **nach P4** installieren (P6 importiert `research`): `P1 → P2 → P3 → P4 → P5 → P6`.
3. **Cross-Phase-Reuse über editable install**, nicht `sys.path`: `from research import token_meter`,
   `from research.llm_client import LLMClient`, `from research.models import ResearchConfig`
   lösen über den P4-editable-install auf. `credentials.py` reuse wie in P4
   (`from broker_wrapper.credentials import get_credential`, Key `"anthropic_api_key"`).

**Done when:** frische venv → `bash scripts/dev_install.sh` → `pytest phase6_debate/tests -v`
grün **ohne** `sys.path`-Manipulation.

---

## Verifizierte geerbte Contracts (Repo = Wahrheit)

### Die Naht in `phase5_execution/execution/executor.py` (gelesen, exakt)
Aktuell zwischen Schritt 4 und 5:
```python
# 4) Gate 2
g2, candidate = gate_load_candidates(self.state, self.research_runner, self.config)
if not g2.ok or candidate is None:
    return self._no_trade(g2.gate, g2.reason)
# ── HIER fügt Phase 6 die Debatte ein ──
# 5) Gate 3 + Gate 5 ...
```
`candidate` ist ein **dict** mit den Keys aus `turbo_candidates.json`:
`epic, direction("BUY"|"SELL"), llm_confidence, reasoning, spread_pct_at_pick,
drift_at_pick|None, score_at_pick, threshold_applied, generated_at, source`.

### `research.LLMClient` (Phase 4, wiederverwendet — Signatur gelesen)
```python
LLMClient(model, api_key, *, max_tokens, temperature, timeout_s,
          token_meter_path=None, config=None, enable_thinking=False)
ask_candidate(system: str, user: str, json_schema: dict) -> dict   # 1 Retry, structured-output primär
```
- Structured Outputs via `output_config={"format": {"type": "json_schema", "schema": ...}}`
  (das alte `output_format` ist API-weit deprecated). Fallback: plain call + fence-strip + balanced-`{}`-Extraktion.
- Sampling-Params werden für Opus 4.7/4.8 automatisch gedroppt (`_supports_sampling`). Haiku/Sonnet akzeptieren `temperature`.
- **`_build_create_kwargs` setzt KEIN `cache_control`** → Phase 6 muss das additiv ergänzen (siehe Modul „llm_caching"/Decision G).

### `research.token_meter` (Phase 4, wiederverwendet — gelesen)
```python
record(usage, model, config, path) -> dict
# frozen record: {ts, model, input_tokens, output_tokens, est_cost_usd, est_cost_eur}
estimate_cost(usage, model, config) -> (usd, eur)   # cache-aware: write 1.25×, read 0.1×
```
- Liest cache-Felder bereits für die Kostenrechnung, **schreibt sie aber nicht** in den Record → Decision G erweitert genau das additiv.
- Pricing in `ResearchConfig.pricing_usd_per_mtok` (verifiziert 2026-06-08):
  `claude-sonnet-4-6 (3,15)`, `claude-opus-4-8 (5,25)`, `claude-haiku-4-5-20251001 (1,5)`. `usd_to_eur=0.92`.

### Broker (Phase 1, **nur vom deterministischen Context-Builder** genutzt, nie vom LLM)
- `get_price(epic).data`: `bid, ask, spread, spread_pct, market_status, timestamp`.
- `get_ohlcv(epic, resolution, count).data = {"bars":[…], "allowance":{…}}`; Bar = `{timestamp, open, high, low, close, volume}` (Mid). **[VERIFY]** Close-Feldname gegen echten Code (war schon P5-VETO-3-[VERIFY]).
- `get_market_info(epic).data`: `min_deal_size, currency, instrument_type, market_status`.

---

## Modul-Plan (TDD-geordnet — pro Modul Tests zuerst, dann grün, dann Commit)

Verzeichnis **neu**: `phase6_debate/`. Struktur (gespiegelt an `phase4_research/`):

> 📝 **Korrektur 2026-06-12 (Code = Source of Truth):** Das `CLAUDE.md` wird **up-front im
> initialen Scaffold** angelegt (✅ erledigt), **nicht** auf Step 10 verschoben — konsistent mit
> P1–P5 (z. B. P4 legte sein `CLAUDE.md` in Step 1 an). Es ist die Wissens-/Protokoll-/Handover-
> Basis und muss ab Session 1 existieren; der `## Session stopped`-Block wird **fortlaufend**
> gepflegt, nicht erst am Phasenende geschrieben. Step 10 finalisiert daher nur noch `README.md`
> + den finalen Session-stopped-Stand (siehe annotiertes Step 10).

```
phase6_debate/
├── pyproject.toml            # Step C
├── requirements.txt          # nur P6-eigene Dev-Deps (anthropic kommt via P4-install)
├── README.md
├── CLAUDE.md                 # inkl. ## Session stopped (Pflicht)
├── debate/
│   ├── __init__.py           # exports: Debate, DebateConfig, DebateOutcome
│   ├── models.py             # DebateConfig, DebateContext, AgentTurn, DebateOutcome, Exceptions
│   ├── context_builder.py    # CODE: candidate + 1 frischer Snapshot → DebateContext (frozen)
│   ├── prompts.py            # Bull/Bear/Judge System+User-Templates + JSON-Schemas
│   ├── llm_caching.py        # additiver cache_control-Wrapper um research.LLMClient + Meter-Ext
│   ├── budget.py             # Call-/Token-/Wall-Clock-Caps + kumulatives Metering, fail-closed
│   ├── debate.py             # Orchestrator: Runden-Loop, Early-Stop, Kompression, fail-closed
│   ├── audit.py              # debate_log.json (vorwärtskompatibles Schema)
│   └── credentials.py        # reuse phase1 get_credential ("anthropic_api_key")
├── scripts/
│   ├── wiring.py             # build_debate(cfg) + debate_runner-Factory (lazy, DI)
│   ├── smoke_test.py         # eine Debatte, echtes LLM, dry (kein Executor, kein save)
│   └── live_test.py          # Debatte im vollen Executor gegen IG Demo (Operator führt aus)
└── tests/
    ├── conftest.py           # FakeLLM (scripted Bull/Bear/Judge), FakeBroker, Fixtures
    ├── test_context_builder.py
    ├── test_prompts.py
    ├── test_llm_caching.py
    ├── test_budget.py
    ├── test_debate.py        # Kern: override/abstain/early-stop/caps/fail-closed
    └── test_audit.py
```

### 1. `models.py` + Tests
```python
@dataclass(frozen=True)
class DebateConfig: ...        # alle Felder aus der Defaults-Tabelle §0

@dataclass(frozen=True)
class DebateContext:           # vom CODE gebaut, read-only, das EINZIGE was die Agenten sehen
    epic: str
    seed_direction: str        # P4-Candidate-Richtung (der „Vorschlag")
    seed_reasoning: str        # candidate["reasoning"]
    seed_confidence: float     # candidate["llm_confidence"] (advisory)
    spread_pct: float          # FRISCH aus get_price
    market_status: str
    recent_bars_summary: str   # kompakte Textform aus get_ohlcv (IG-Echtzeit)
    drift_at_pick: float | None
    score_at_pick: float
    generated_at: str

@dataclass(frozen=True)
class AgentTurn:
    round: int; agent: str     # "BULL"|"BEAR"|"JUDGE"
    model: str; text: str
    usage: dict                # input/output/cache_* tokens + est cost

@dataclass(frozen=True)
class DebateOutcome:
    decision: str              # "TRADE"|"ABSTAIN"
    direction: str | None      # "BUY"|"SELL"|None (None bei ABSTAIN)
    confidence: float          # ADVISORY ONLY — gatet nichts (Decision H)
    rationale: str
    rounds_used: int
    transcript: tuple[AgentTurn, ...]
    token_summary: dict        # Aggregat: input/output/cache_read/cache_write/est_cost_*
```
- Exceptions: `DebateError` (Basis) → `DebateBudgetExceeded`, `DebateLLMError`. **Nie still schlucken**, immer fail-closed in `debate.py` zu ABSTAIN gewandelt.
- Tests (≥5): Config-Defaults korrekt; Outcome/Context immutabel; `confidence` nie in einer Gating-Verzweigung referenziert (Doku-Test: Konstante `confidence_gates_nothing` existiert).

### 2. `context_builder.py` + Tests — **deterministisch, das ist die AI-Grenze**
```python
def build_debate_context(candidate, broker, config) -> DebateContext:
    """CODE-only. Liest GENAU EINEN frischen Snapshot (get_price + get_ohlcv +
    get_market_info), fasst ihn + die Candidate-Felder zu einem frozen
    DebateContext zusammen. Der Broker wird HIER (Code) gelesen — die LLM-Agenten
    bekommen ihn NIE. recent_bars_summary aus get_ohlcv (IG-Echtzeit, MINUTE_5).
    market_status ≠ TRADEABLE / get_ohlcv-Fehler → DebateError (→ ABSTAIN)."""
```
- **[VERIFY]** Close-Feldname aus `get_ohlcv.data["bars"]` (gleiche offene Stelle wie P5-VETO-3).
- Tests (≥6, FakeBroker): Kontext vollständig; frischer spread überschreibt `spread_pct_at_pick`; `drift_at_pick=None` crasht nicht; `get_ohlcv`-Fehler → DebateError; nicht-TRADEABLE → DebateError; Broker wird genau **einmal** je Probe gelesen.

### 3. `prompts.py` + Tests
- Drei System-Prompts (Bull, Bear, Judge) + drei Structured-Output-Schemas. Alle auf Deutsch.
  - **Bull:** argumentiert für LONG (BUY), gegeben Kontext + bisheriges Transkript.
  - **Bear:** argumentiert für SHORT (SELL), gegeben Kontext + bisheriges Transkript.
  - **Judge:** wägt ab, emittiert `{decision, direction, confidence, rationale, conclude}` (`conclude:bool` steuert Early-Stop).
- Der **System+Kontext-Block ist stabil über alle Turns** (Cache-Präfix); nur das wachsende Transkript steht im `user`-Teil. **WICHTIG:** Prompts müssen ehrlich kommunizieren, dass `drift_at_pick`/`seed_*` aus P4 ein **verzögertes** Stimmungsbild sind (yFinance ~15 min); die frischen Felder (`spread_pct`, `recent_bars_summary`) sind IG-Echtzeit.
- Judge-Schema (structured):
  ```json
  {"decision":"TRADE|ABSTAIN","direction":"BUY|SELL|null",
   "confidence":0-100,"rationale":"...","conclude":true|false}
  ```
- Tests (≥6): jedes Schema valide; Kontext vollständig im stabilen Block; Transkript korrekt seriell im user-Teil; Judge-Schema lässt `direction:null` bei ABSTAIN zu; kein `CALL/PUT`/Options-Vokabular irgendwo.

### 4. `llm_caching.py` + Tests — **Cache-Präfix + Meter-Erweiterung (Decision D/G)**
> Konsequenz aus D+F+G. Hält den **einen** Call-Punkt (`research.LLMClient`) und ergänzt
> additiv `cache_control` + die Cache-Token-Records. **P4-Verhalten bleibt unverändert
> (default cache aus).**

Zwei additive Edits **im P4-Code** (Decision F/G, dokumentierte Ausnahme):
1. `research/llm_client.py` → `_build_create_kwargs(..., cache_system: bool = False)`:
   bei `True` einen `cache_control: {"type":"ephemeral"}`-Marker auf den System-Block setzen,
   und den Konstruktor um `cache_system: bool = False` erweitern (durchgereicht). **Default
   False ⇒ P4 unverändert.** **[VERIFY]** gegen die installierte `anthropic`-SDK-Version, dass
   block-level `cache_control` auf `system` unterstützt wird; falls die SDK das nur als Liste von
   Content-Blocks akzeptiert, System als `[{"type":"text","text":..., "cache_control":...}]` bauen.
2. `research/token_meter.py` → `record(...)`-Record **additiv** um `cache_read_input_tokens` +
   `cache_creation_input_tokens` erweitern (Werte via `_usage_int`, die Helfer existieren schon).
   `usage_report.py` um Cache-Hit-Ratio + Σ-Kosten pro Debatte erweitern.
- P6-seitig dünner Wrapper `ask_agent(client, system, user, schema, *, model, temperature) -> (dict, usage)`,
  der den geteilten Client mit `cache_system=True` aufruft und die `usage` für `budget.py` zurückgibt.
- **[VERIFY]** `message.usage`-Feldnamen (`cache_creation_input_tokens` / `cache_read_input_tokens`) gegen die SDK-Version.
- Tests (≥6, FakeLLM/monkeypatched `_build_create_kwargs`): `cache_system=True` setzt den Marker, `False` (P4-Default) nicht; Meter-Record enthält die beiden Cache-Felder; Cache-Felder=0 bei P4-Default; `estimate_cost` rechnet Read 0.1× / Write 1.25× korrekt; unbekanntes Modell → Kosten 0 + Warnung (bestehendes Verhalten).

> 📝 **Reconciliation 2026-06-15 (Code = Source of Truth, Modul 4, anthropic SDK 0.106.0):**
> - **[VERIFY] #1 (cache_control-Form) RESOLVED:** plain-String-`system` kann den Marker nicht
>   tragen → `_build_create_kwargs(cache_system=True)` baut `system` als
>   `[{"type":"text","text":…,"cache_control":{"type":"ephemeral"}}]` (Content-Block-Liste,
>   `TextBlockParam.cache_control`). `cache_system=False` (P4-Default) lässt `system` ein
>   plain String → **P4-Request bit-identisch**. `cache_system` ist sowohl Konstruktor-Arg
>   (default False) als auch optionaler `_build_create_kwargs`-Parameter; `_raw_call` reicht
>   `self.cache_system` durch.
> - **[VERIFY] #2 (usage-Feldnamen) RESOLVED:** `Usage` hat `cache_read_input_tokens` +
>   `cache_creation_input_tokens` (von `_usage_int` schon gelesen).
> - **`usage`-Rückgabe von `ask_agent` ist ein dict** (der `token_meter`-Record, via neuer
>   additiver `LLMClient.last_usage`-Attribut-Erfassung in `_attempt`) — passt direkt auf
>   `DebateBudget.register(usage: dict)` (§5). `ask_agent` setzt `client.model`/`temperature`
>   pro Turn auf dem **einen geteilten** Client; Caching steuert das Konstruktor-`cache_system`,
>   nicht der Call.
> - **P4-Test-Anpassung (Teil der additiven Decision-G-Edit):** `test_record_returns_frozen_shape`
>   prüft jetzt 8 Keys (6 alt + 2 Cache); alle 88 P4-Tests bleiben grün.
> - **`ask_agent`-Fehler → `DebateLLMError`** (fail-closed; Orchestrator → ABSTAIN).

### 5. `budget.py` + Tests — Caps & kumulatives Metering (Decision E/J)
```python
class DebateBudget:
    def __init__(self, config, *, now_fn=time.monotonic): ...
    def register(self, usage: dict) -> None:        # nach jedem Turn
    def check(self) -> None:                        # raises DebateBudgetExceeded bei Breach
    def summary(self) -> dict                        # Aggregat für DebateOutcome.token_summary
```
- Caps: `max_total_calls`, `max_cumulative_input_tokens`, `max_cumulative_output_tokens`, `wall_clock_timeout_s`. **Erster Breach → `DebateBudgetExceeded`** (vom Orchestrator zu ABSTAIN gewandelt).
- Tests (≥6, injizierte `now_fn`): jeder Cap einzeln löst aus; Aggregat summiert input/output/cache korrekt; unter Cap → kein Raise; Wall-Clock-Timeout deterministisch (gemockte Zeit, **kein echtes Warten**).

### 6. `debate.py` + Tests — **Orchestrator (der Kern der Phase)**
```python
class Debate:
    def __init__(self, broker, llm_client, config, *,
                 audit=None, now_fn=time.monotonic): ...    # alles DI
    def run(self, candidate: dict) -> DebateOutcome: ...
```
Flow (Richtung kommt vom Judge, Bull/Bear nur Argumente):
1. `ctx = build_debate_context(candidate, broker, config)` — Fehler → **ABSTAIN** (fail-closed, geloggt).
2. Runden-Loop `1..max_rounds`, je Runde: **Bull** (Haiku) → **Bear** (Haiku) → **Judge** (Sonnet).
   Nach jedem Turn `budget.register(usage)` + `budget.check()`; Breach → **ABSTAIN**.
3. Transkript-Kompression bei `compression_trigger_pct`: komprimiere zu (Bull-Position,
   Bear-Position, Judge-Zwischenstand, offene Punkte) und fahre fort — **verlustarm, deterministisch**
   (Code, kein zusätzlicher LLM-Call für die Kompression in v1; einfache strukturierte Verdichtung).
4. **Early-Stop:** Judge `conclude=true` → Runde beenden.
5. Endurteil = letzter Judge-Output → `DebateOutcome`. `decision=="ABSTAIN"` → `direction=None`.
6. Jeder `DebateLLMError`/`DebateBudgetExceeded`/`DebateError` an **jeder** Stelle → **ABSTAIN**
   mit Begründung (nie Exception nach außen, nie „trotzdem traden"). Logs → **stderr**.
7. `audit.write(outcome, ctx)` (falls audit gesetzt), bevor `run()` zurückkehrt.
- **Determinismus-Grenze strukturell:** `Debate` referenziert **keine** VETO-/Gate-Funktion und gibt
  den Broker **nie** an einen LLM-Call weiter — der Broker wird nur in Schritt 1 (Code) gelesen.
- Tests (≥12, FakeLLM scripted, gemockte Zeit — **Kern der Phase**):
  Bull/Bear/Judge in korrekter Reihenfolge je Runde; Judge **bestätigt** Seed → `decision=TRADE, direction=seed`;
  Judge **flippt** (BUY→SELL) → Outcome trägt die geflippte Richtung; Judge `conclude=true` Runde 2 → Early-Stop (keine Runde 3);
  `max_rounds` ausgeschöpft ohne Konsens → letztes Judge-Urteil zählt;
  Budget-Breach mitten in Runde 3 → ABSTAIN; `DebateLLMError` (transient erschöpft) → ABSTAIN;
  Context-Builder-Fehler → ABSTAIN (kein einziger Agenten-Call); Kompression triggert bei Schwelle und Debatte läuft korrekt weiter;
  `confidence` taucht in **keiner** Steuer-Verzweigung auf (advisory-only-Test); Audit wird genau einmal geschrieben;
  Transkript im Outcome ist vollständig + immutabel.

> 📝 **Reconciliation 2026-06-15 (Code = Source of Truth, Modul 6 gebaut):** Zwei
> Implementierungs-Details, die der §6-Stub offenließ:
> - **`audit` ist ein injizierter Callable** `(outcome, ctx) -> None` (nicht ein
>   Objekt mit `.write(...)`). Modul 7 liefert `write_debate(outcome, ctx, path)`;
>   die Modul-8-`wiring` bindet das als `lambda o, c: write_debate(o, c, path)`. Das
>   hält den Orchestrator von der Modul-7-Signatur entkoppelt (DI; Tests geben einen
>   Recorder). Audit wird **genau einmal** vor Return gerufen, **nur** wenn `ctx`
>   gebaut wurde; ein Audit-Fehler wird geloggt + geschluckt (bricht das Ergebnis nie).
> - **Per-Rollen-`max_tokens` setzt der Orchestrator** direkt am geteilten Client
>   (`llm_client.max_tokens = max_tokens_agent|max_tokens_judge`) **vor** `ask_agent`
>   — der einzige Per-Turn-Knopf, den `ask_agent` (Modul 4) nicht setzt (`ask_agent`
>   setzt Model + Temperatur). Vermeidet eine erneute Edit am bereits committeten
>   Modul 4; `ask_agent`-Signatur bleibt unverändert.
> - **Kompression:** das **volle** Transkript bleibt für `DebateOutcome.transcript` +
>   Audit erhalten; nur die **Prompt-Sicht** wird ab Schwelle komprimiert
>   (`_compress` = jüngster Turn je Agent, in Rundenreihenfolge) — Decision-I-konform.

### 7. `audit.py` + Tests — **vorwärtskompatibles JSON (Decision I)**
```python
def write_debate(outcome: DebateOutcome, ctx: DebateContext, path: str | None) -> dict:
    """Append einen Record an debate_log.json (atomar, korrupte Datei → frisch + Warnung,
    wie token_meter._load_log). path=None → nicht schreiben (Tests), Record wird zurückgegeben."""
```
Record-Schema (so gewählt, dass P9 es ohne Reshaping in `decision_context` /
`market_regime_snapshots` ingestieren kann — Mapping als Kommentar im Modul):
```json
{
  "ts": "<iso-utc>",
  "epic": "...",
  "seed_direction": "BUY|SELL",
  "final_decision": "TRADE|ABSTAIN",
  "final_direction": "BUY|SELL|null",
  "confidence": 0-100,                  // advisory; P7-Outcome-Anchoring-Input, kein Gate
  "rounds_used": 3,
  "rationale": "...",
  "regime_snapshot": {                  // → P9 market_regime_snapshots
     "spread_pct": ..., "market_status": "...", "drift_at_pick": ...,
     "score_at_pick": ..., "recent_bars_summary": "..."
  },
  "transcript": [                       // → P9 decision_context (Bull/Bear/Judge-Verlauf)
     {"round":1,"agent":"BULL","model":"...","text":"...","usage":{...}}, ...
  ],
  "token_summary": {"input_tokens":..,"output_tokens":..,
                    "cache_read_input_tokens":..,"cache_creation_input_tokens":..,
                    "est_cost_usd":..,"est_cost_eur":..}
}
```
- Tests (≥5): Record-Schema vollständig + alle P9-Mapping-Keys vorhanden; atomar (temp + `os.replace`); korrupte Datei → frisch + Warnung, kein Crash; `path=None` schreibt nicht, gibt Record; append erhält Vorgänger-Records.

### 8. `scripts/`
- **`wiring.py`:** baut den geteilten `research.LLMClient` (Demo-Keyring `anthropic_api_key`),
  setzt den `token_meter_path` auf das echte `data/state/llm_usage.json`, instanziiert `Debate`
  mit echtem Broker (für den Context-Snapshot) + `audit`. Liefert die **Runner-Factory**
  `debate_runner = lambda candidate: build_debate(cfg).run(candidate)` (lazy, DI — analog
  P5 `research_runner`). **[VERIFY]** Modulnamen-Kollision: P6-`scripts.wiring` darf nicht
  versehentlich P4/P5-`scripts.wiring` importieren (gleicher Modulname, war eine P5-Falle).
- **`smoke_test.py`:** eine echte Debatte über einen geseedeten Candidate, **dry** (kein Executor,
  kein Save), druckt das Transkript + `token_summary` (inkl. Cache-Reads). Schnell, manuell.
- **`live_test.py`:** **Operator-Lauf.** Debatte **im vollen P5-Executor** gegen IG Demo
  (Executor mit echtem `debate_runner` verdrahtet), hart asserted: Lauf endet sauber
  (TRADE→open/close **oder** ABSTAIN→NO_TRADE), `debate_log.json` entsteht, `usage_report`
  zeigt **Cache-Reads > 0** (Beweis, dass Caching greift). `exit 0` = PASS. Läuft **nicht** in CI.

### 9. P5-Executor-Edit + **Regression** (Decision A — explizit)
Minimale Edit in `phase5_execution/execution/executor.py`:
1. Konstruktor: neuer **keyword-only** Arg `debate_runner: Callable[[dict], DebateOutcome] = _passthrough_debate`.
   `_passthrough_debate(candidate)` gibt `DebateOutcome(decision="TRADE", direction=candidate["direction"], confidence=candidate.get("llm_confidence",0.0), rationale="passthrough", rounds_used=0, transcript=(), token_summary={})`
   zurück → **ohne** echten Runner bleibt P5 bit-identisch + AI-frei.
2. In `run()` direkt **nach Gate 2**:
   ```python
   outcome = self.debate_runner(candidate)
   if outcome.decision == "ABSTAIN":
       return self._no_trade("debate", outcome.rationale)
   candidate = {**candidate, "direction": outcome.direction, "debate": {
       "confidence": outcome.confidence, "rationale": outcome.rationale,
       "rounds_used": outcome.rounds_used}}    # in-memory enrichment, Datei unverändert
   ```
   Danach laufen Gate 3 / Gate 5 / Sizing / VETOs / `build_order_plan` unverändert mit der
   (ggf. geflippten) Richtung. **Kein Gate/VETO wird angefasst.**
3. `scripts/wiring.py` (P5) optional erweitern, um den echten P6-`debate_runner` zu injizieren
   (lazy import von `debate`), default bleibt Passthrough.

**Pflicht-Regression (deine A-Anmerkung):**
- **Volle P5-Suite erneut grün** (`pytest phase5_execution/tests -v`) — der Default-Passthrough
  garantiert, dass die bestehenden Tests **ohne Änderung** bestehen.
- **Neue P5-Regressionstests in `test_executor.py` (≥4):**
  (a) Default-Executor (kein `debate_runner`) verhält sich exakt wie vor P6 (Passthrough);
  (b) injizierter Stub-Runner mit `ABSTAIN` → `NO_TRADE`, **keine** Order;
  (c) injizierter Stub-Runner **flippt** die Richtung → `build_order_plan`/`open_position` bekommen die geflippte Richtung;
  (d) `debate_runner` wirft (sollte nie, aber Defense) → fail-closed (`ABORT`/`NO_TRADE`), **keine** Order.
- **Volle P4-Suite erneut grün** (additive `cache_system`/Meter-Edits, Default-Verhalten unverändert).

### 10. `README.md` · `requirements.txt` · `CLAUDE.md`

> 📝 **Korrektur 2026-06-12:** `CLAUDE.md` **und** `requirements.txt` werden **up-front im
> Scaffold** angelegt (✅ erledigt, siehe Step C / Modul-Tree-Korrektur), nicht hier. Step 10
> reduziert sich damit auf das **Finalisieren von `README.md`** (Status auf code-complete flippen,
> `## Run` mit den realen Live-Kommandos) + das **fortlaufend gepflegte `## Session stopped`** im
> bereits existierenden `CLAUDE.md` (kein Neu-Schreiben). Die unten vorgegebene CLAUDE.md-Struktur
> ist bereits umgesetzt — **nicht doppelt anlegen.**
- `requirements.txt`: nur P6-eigene Dev-Deps; Runtime (`anthropic`) kommt über den P4-editable-install.
- `README.md`: kurz — was `phase6_debate/` ist (Bull/Bear/Judge, AI nur für Argumente/Synthese,
  Richtungsquelle, fail-closed→ABSTAIN), wie man `smoke_test.py`/`live_test.py` startet, Verweis auf `CLAUDE.md`.
- **`CLAUDE.md`** schreibt Claude Code selbst — **diese Struktur vorgeben** (an P4/P5 orientiert),
  mit dem `## Session stopped`-Block (Pflicht, am Sessionende befüllen):

```markdown
# CLAUDE.md — Phase 6: Bull/Bear/Judge-Debatte (phase6_debate/)

> Erster Mehr-Agenten-AI-Pfad + teuerster Pfad im System. Quelle der Wahrheit ist der Code.

## AI-Grenze (Projekt-Kernprinzip)
AI macht NUR: Bull/Bear-Argumente + Judge-Synthese (Richtung + TRADE/ABSTAIN).
ALLES andere ist Code: Kontextaufbau, Caps/Budget, Persistenz, Fehlerbehandlung.
Die Debatte bekommt NIE den Broker oder eine VETO-/Gate-Funktion. Sie liefert nur
Richtung/ABSTAIN und kann KEINEN VETO/kein Gate überschreiben (kein Force-Trigger).

## Harte Regeln (nicht verhandelbar)
- confidence ist ADVISORY und gatet NICHTS (Decision H). Nur Judge-`decision` entscheidet.
- Jeder Fehler / Cap-Breach / Context-Fehler → ABSTAIN (fail-closed). Nie „trotzdem traden".
- Caching AN (cache_system=True), Meter MUSS Cache-Felder loggen — sonst ist die teuerste
  Optimierung unsichtbar. usage_report zeigt Cache-Hit-Ratio.
- turbo_candidates.json NICHT anfassen. Candidate wird nur IN-MEMORY angereichert.
- DB read-only (P7). Kein SQLite-Schreiben — nur debate_log.json (vorwärtskompatibel zu P9).
- Logging → stderr; stdout nur maschinenlesbares JSON. Atomic commits. Kein Subtask „done"
  ohne grünes pytest (gemockt, kein Netz, KEIN echtes LLM in Unit-Tests).
- Cross-Phase-Reuse (research.LLMClient/token_meter/Pricing) ist die dokumentierte Ausnahme.

## Die 11 Entscheidungen (A–K)  <Tabelle aus §0 übernehmen.>
## Modell-Split  Bull/Bear=Haiku 4.5, Judge=Sonnet 4.6, alle config-überschreibbar.
## Geerbte Contracts  <Kurzliste P1/P4-Signaturen + Verweis auf diesen Plan.>
## Naht zu Phase 5  debate_runner zwischen Gate 2 und Gate 3; Default-Passthrough hält P5 AI-frei.
## Datei-/Modul-Übersicht  <Baum + eine Zeile Zweck je Datei.>

## Session stopped
<!-- Pflicht am Ende JEDER Session. -->
- **Stand:** <Datum, was code-complete + grün ist (Testzahl P6/P5/P4)>.
- **Zuletzt gemacht:** <Module/Commits>.
- **Nächster Schritt:** <konkret>.
- **Offene Punkte / [VERIFY]:** <SDK cache_control-Form, usage-Cache-Feldnamen, get_ohlcv-Close-Feld>.
- **Gotchas:** <Stolperfallen für den Re-Entry>.
```

---

## Done-Kriterien (Phase-6-Gate)
- `pytest phase6_debate/tests -v` grün, **≥45 Tests** (alle gemockt, **kein Netz, KEIN echtes LLM**),
  davon `test_debate.py` ≥12, `test_llm_caching.py` ≥6, `test_budget.py` ≥6.
- **Regression grün:** `pytest phase5_execution/tests -v` (inkl. ≥4 neue Executor-Tests) **und**
  `pytest phase4_research/tests -v` (additive Meter/Client-Edits, Default-Verhalten unverändert).
- `bash scripts/dev_install.sh` + alle drei Suiten grün **ohne** `sys.path`-Hack (P6 nach P4 installiert).
- `grep` aus Step 0 zeigt keine turbo/options-Treffer in `phase6_debate/`; `turbo_candidates.json` unangetastet.
- **Beweis-Tests:** (a) Judge-Flip → geflippte Richtung landet in `build_order_plan`;
  (b) Budget-Breach **oder** LLM-Fehler mitten in der Debatte → zuverlässig **ABSTAIN/NO_TRADE**, keine Order;
  (c) `cache_system=True` setzt den Marker **und** der Meter-Record trägt die Cache-Felder.
- `python phase6_debate/scripts/live_test.py` (Operator): Debatte im vollen Executor gegen IG Demo,
  sauberes Ende (TRADE→open/close **oder** ABSTAIN→NO_TRADE), `debate_log.json` entsteht,
  `usage_report` zeigt **Cache-Reads > 0**. `exit 0`.

---

## Bewusst NICHT in Phase 6 (Carry-overs)
- **Outcome-/Lesson-Schreiben + Confidence-Outcome-Anchoring** → **Phase 7**. P6 *loggt* die
  Judge-Confidence (advisory) ins Audit, damit P7 sie outcome-verankern kann (`f(win_rate,
  expectancy, sample_size)`, N_min=10) — P6 selbst gatet damit nichts.
- **SQLite-Population** (`decision_context`, `market_regime_snapshots`) → **Phase 9**. P6 schreibt
  nur das **vorwärtskompatible** `debate_log.json`; DB bleibt read-only.
- **Council-Integration** (`verbesserungsvorschlaege` als strukturierter Input) → **Phase 9**.
- **Scheduler/Daemon** (Debatte periodisch) → **Phase 8**. P6 = manueller Trigger über den Executor.
- **LLM-basierte Transkript-Kompression** → späterer Swap; P6-v1 komprimiert deterministisch im Code.
- **Live-Trading** → braucht das IG-Europe-GmbH-Konto. P6 bleibt Demo.

---

## Offene [VERIFY] (vor dem Bauen gegen echten Code / SDK prüfen)
1. **`anthropic`-SDK-Version im Repo** unterstützt block-level `cache_control` auf `system`
   (bzw. System als Content-Block-Liste). Falls nicht → Form anpassen, ggf. SDK pinnen/upgraden.
2. **`message.usage`-Cache-Feldnamen** (`cache_creation_input_tokens` / `cache_read_input_tokens`)
   gegen die SDK-Version (der token_meter referenziert sie bereits).
3. **`get_ohlcv.data["bars"]` Close-Feldname** (gleiche offene Stelle wie P5-VETO-3) für `recent_bars_summary`.
4. **Modulnamen-Kollision** `scripts.wiring` (P4/P5/P6) — P6-Wiring darf nicht die falsche `wiring` importieren.
```