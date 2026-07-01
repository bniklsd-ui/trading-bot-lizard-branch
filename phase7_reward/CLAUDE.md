# CLAUDE.md — Phase 7: Reward/Brain (`phase7_reward/`)

> Die Phase, in der der Bot **lernt**: prozess-bewusster Reward-Score + Freitext-Lessons +
> observe-only outcome-anchored Confidence. **Quelle der Wahrheit ist der Code, nicht dieses
> Dokument.** Vollständiges Design + alle gelockten Entscheidungen (A–J) + Step 0–13:
> `../docs/concepts/phase7_reward_concept.md`.

## AI-Grenze (Projekt-Kernprinzip)
„So wenig AI wie möglich, so viel AI wie nötig." **Phase 7 nutzt AI NUR für die Lesson-Extraktion**
(`reflect()`, ein Haiku-Call, best-effort, vom Close-Critical-Path entkoppelt). **ALLES andere ist
deterministischer Code:** Reward-Delta (Outcome + Prozess), Confidence-Mathe (Wilson-LB /
Expectancy-R / SQN / N_min-Gating), P&L-Auflösung, Persistenz, Fehlerbehandlung. Wer hier ein LLM
„scoren/gaten/vetoen" lassen will → **stop**, das ist Code. Brain extrahiert **nur Sprache →
Erkenntnis**, **keine** Zahlen-/Score-Entscheidung.

## Scope-Lock (schlankes Modell — Konzept Rev. 2026-06-16-b)
P7 = **Reward-Score** (`reward_pts`, prozess-bewusst ab Tag 1) + **Freitext-Lessons**
(`trade_lessons`) + **observe-only outcome-anchored Confidence**. **KEINE VETO-Berührung.** Die
volle **Instinct→VETO-Promotion** („ECC": strukturierte Instincts → validiert → Promote zu VETO)
ist ein **separater, späterer Step** (**Phase 9f** / Konzept §7b), gated auf reale Outcomes —
Promotion auf null validierten Outcomes würde Risiko zurück in die Safety-Schicht importieren.
P7 baut nur das **Substrat** (`trade_lessons` + `reward_pts`).

> 🔁 **Phase-8 v1.5-hotfix edit (2026-07-01, Issue A — lesson provenance, code = source of truth):**
> `OpenedTrade` gained `provenance: str = "autonomous"` (`reward/models.py`; **default** keeps every
> existing construction valid + it stays the trailing field), and `recorder._extract_lesson` writes
> `opened.provenance` (cold reconcile without a stash → `"unknown"`) into the lesson's `market_context`
> → persisted verbatim into the existing `trade_lessons.market_context_json` blob — **no migration / no
> schema change**. **Why:** verification-trade lessons (seeded, sub-minute time-stops) pollute the P4
> research prompt, and the seed marker is otherwise never persisted; a schema touch is out of hotfix
> scope, so the free-form context JSON is the honest home for a precise tag. The tag is set at open by
> the **P5 executor seam** (`build_opened`, from the candidate seed marker — deterministic, no AI) and
> read by the **P4** prompt filter (new P2 `get_recent_lessons_for_prompt`). **The reward/score math is
> provably untouched** — `provenance` rides only in the lesson's context, never in a score input, and
> lessons gate nothing (root rule 3, Decision C/J intact). +3 P7 tests (**128 → 131**). Detail:
> `docs/concepts/phase8_v1.5_hotfix_plan.md` Step 4.

## Harte Regeln (nicht verhandelbar)
- **`confidence` ist observe-only und gatet NICHTS** (Decision C). N < `n_min=10` → `INSUFFICIENT`
  (fließt in NICHTS). Moduliert in v1 **nicht** `risk_pct`. Wer eine Confidence-Schwelle einbaut →
  **stop** (gleiches Anti-Pattern wie P6 Decision H).
- **Alle P7-Writes sind best-effort, fail-closed** (Decision J): sie werfen **nie** in den
  P5-Close-Pfad. Jeder Fehlschlag → **`logger.critical`** (bewusst nicht `error` — die Lernlogik
  hebt sich ab), idempotenter Retry via `deal_id`. Der Trade bleibt am Broker geschlossen; Reward/
  Lesson sind Buchhaltung/Lernen, **keine** Safety-Schicht.
- **`reward_sink` bekommt strukturell NIE** den Broker als Schreib-/Order-Pfad, **nie** eine VETO-/
  Gate-Funktion. Es liest den Broker höchstens read-only (`get_trade_history` für P&L). Es kann
  **keinen** VETO umgehen, weil es keinen referenziert.
- **Score auf [0,100] clampen** (P2 clampt **nicht**) **vor** dem Insert; Per-Trade-`|delta|` ≤
  `max_delta_per_trade`. Binäres `get_risk_level` (Schwelle 50) bleibt **unverändert** — P7 schreibt
  nur `score_after`.
- **Reuse statt Neubau** (Decision F/G): `research.LLMClient` + `research.token_meter` (8-Feld,
  cache-aware) wiederverwenden; Persistenz über die **P2-CRUD** (`insert_trade`/`update_trade_close`/
  `insert_reward`/`insert_lesson`) — kein zweites Mess-System, keine neue DB-Schicht.
- **Synthetik ≠ Demo ≠ Live** (Decision H): *synthetic* (generierte Testdaten) schreibt **immer**
  `synthetic_db_path` (Pfad-Guard, nie `live_db_path`) + Tag `synthetic=True`; *demo* (echte
  IG-Demo-Trades) läuft normal in `live_db_path`, getaggt `account='demo'`, zählt via
  `include_demo_in_edge` (Default `True` in der Bootstrap-Phase) in die Edge-Metrik.
- **`turbo_candidates.json` NICHT anfassen/umbenennen** (frozen P2/P5-Contract). Richtung ist
  **BUY/SELL** only. Logging → **stderr**; stdout nur maschinenlesbares JSON. Atomic commits. Kein
  Subtask „done" ohne grünes `pytest` (gemockt, **kein Netz, KEIN echtes LLM** in Unit-Tests).
- **Commit ⇒ Note-Update (zwingend, auch auf direkte Anweisung).** Jeder Step-Abschluss-Commit
  aktualisiert im **selben** Commit die Modul-/Status-Tabelle **und** den `## Session stopped`-Block.

## Die gelockten Entscheidungen (A–J — Kurzform; Details: Konzept §0)
| # | Thema | Festlegung |
|---|---|---|
| **Step 0** | Turbo-Cleanup | Nur frozen `turbo_candidates.json` bleibt; P7-Code führt **keine** neuen Turbo-Refs ein. Sonst No-Op. |
| **A** | Write-Seam | Optionaler, duck-typed `reward_sink` (Protocol), default `None` → **P5 bit-identisch**. Zwei Methoden: `on_trade_opened` (Decision-Kontext) + `on_trade_closed` (Outcome+Reward+Lesson). Spiegelt `debate_runner`. |
| **B** | Scoring | **Prozess-bewusst ab Tag 1 (B2)**, nicht outcome-only. Score-Delta = gebremste Outcome-Komponente **+** Prozess-Komponente aus realen Signalen. |
| **C** | Confidence | `f(Wilson-LB(win_rate), expectancy_R, N)`; **N < n_min=10 → INSUFFICIENT** (fließt in nichts). SQN als Nebenmetrik. **v1 observe-only** — gatet keine Order, moduliert nicht `risk_pct`. |
| **D** | Feedback-Stabilität | Binäres `get_risk_level` (Schwelle 50) **unverändert**; P7 schreibt nur `score_after`. Clamp [0,100], `|delta|` ≤ Cap, konservativ, am echten Profit getunt. |
| **E** | Lesson-Extraktion | **Vom Close-Critical-Path entkoppelt:** Reward atomar schreiben, dann best-effort `reflect()`. Ein Haiku-Call, swappbare Schnittstelle (Batch/Scheduler später). **[→ Opus]** |
| **F** | Reuse | `research.LLMClient`, `research.token_meter` (8-Feld), `credentials`-Shim wiederverwenden. Kein zweites Mess-System. |
| **G** | Ownership/Migration | P7 besitzt `trade_outcomes`-Writes über **P2-CRUD**. **Eine** minimale P2-Berührung: Whitelist-Tuples + Migration `002` für `initial_risk`/`r_multiple` (Step 12). |
| **H** | Bootstrap | Produktion **fail-safe-neutral** bis echte Outcomes. **Hart getrennte Orte** Synthetik vs. Echt (separater DB-Pfad + Tag), eigene Steps. **[→ Opus]** |
| **I** | Loop-Closure | Lessons schreiben **+** sicherstellen, dass P4-Research sie via `get_recent_lessons` zieht (✅ **zieht es bereits** — Contract 1.5). **✅ Step 11 (2026-06-22): `mark_lesson_used` in `research.py` verdrahtet** (nach erfolgreichem LLM-Call, best-effort). |
| **J** | Fail-closed Writes | Alle P7-Writes best-effort, werfen nie in den P5-Close-Pfad. Fehlschlag ⇒ `logger.critical`, idempotenter Retry via `deal_id`. |

## Die Naht (`reward_sink`, Decision A — spiegelt `debate_runner`)
`Executor` bekommt einen optionalen keyword-only `reward_sink` (default `None` ⇒ P5 bit-identisch +
AI-frei). **Zwei Callbacks** im `run()`-Pfad (Step 10):
- **`on_trade_opened(opened)`** — nach `place_result.status == "OPEN"` und **vor** `monitor_position`.
- **`on_trade_closed(closed)`** — `monitor_position`-Return in Variable fangen, **dann** Callback,
  **dann** `return`. Beide Aufrufe in `try/except` → ein werfender Sink kippt den Zyklus **nie** (J).
Der Sink referenziert **nie** Gate/VETO/Order-Pfad. (⚠ Implementierungs-Details, die der Live-Code
diktiert, stehen unten unter *Verifizierte Contracts* 1.2/1.3/1.7.)

## Modul-Struktur (neues Paket `phase7_reward/`, Paketname `reward`) — Status pro Step
| Datei | Zweck | Status |
|---|---|---|
| `pyproject.toml` · `requirements.txt` · `README.md` · `CLAUDE.md` | Scaffold + Packaging (Step 2) | ✅ |
| `reward/__init__.py` | Paket-Marker; re-exportiert die Contract-Typen + `RewardConfig` + Exceptions (Step 3) **+ `compute_confidence` (Step 4) + `Scorer` (Step 5) + Synthetik-Surface (Step 6) + `Brain`/`LessonExtractor` (Step 7) + `resolve` (Step 9) + `RewardSink` (Step 8)** | ✅ |
| `reward/models.py` | `OpenedTrade`/`ClosedTrade`/`RewardConfig`/`ConfidenceReport`/`RewardResult`/`LessonResult` + Exceptions (types only); **+ `SyntheticSafetyError` (Step 6)** | ✅ Step 3 (·6) |
| `reward/confidence.py` | Wilson-LB + Expectancy-R + SQN + N_min-Gating (reine Mathe) ★ | ✅ Step 4 |
| `reward/scorer.py` | Prozess-bewusstes Reward-Delta + Clamping (B2/D) ★ | ✅ Step 5 |
| `reward/synthetic.py` | `SyntheticTradeGenerator` + Pfad-Guard + Edge-Selector (harte Synthetik/Echt-Trennung, H) [→ Opus] | ✅ Step 6 |
| `reward/brain.py` | `Brain.reflect()` + `LessonExtractor`-Protocol: Lesson-Extraktion, EIN Haiku-Call, best-effort, swappbar (E) [→ Opus] | ✅ Step 7 |
| `reward/recorder.py` | `RewardSink`-Impl: `on_trade_opened` (insert+in-memory-Stash) / `on_trade_closed` (resolve→close→score→reward→best-effort-Lesson), fail-closed pro Schritt, idempotent via Status (A/J) **+ `reconcile_open_trades` (Live-Debug 2026-06-23): idempotenter Retry für noch-OPEN-Trades bei IG-History-Lag** | ✅ Step 8 (·13b) |
| `reward/pnl_resolver.py` | `resolve()` → (close_level, profit_loss, r_multiple). **Bevorzugt lag-frei den Close-Confirm** (`closed.profit_loss` → direkt; `closed.close_level`+Richtung → aus Levels; Step 13c); **sonst** heuristischer `get_trade_history`-Match (**Size-Betrag**+Level+Recency, **kein** deal_id; Size magnituden-basiert weil IG SELL negativ signt). no-match → `PnLUnavailable` | ✅ Step 9 (·13b·13c) |
| `reward/credentials.py` | dünner Shim → `broker_wrapper.credentials.get_credential("anthropic_api_key")` (verbatim P4/P6-Spiegel, `parents[2]`-Bootstrap) | ✅ Step 13 |
| `002_phase7_reward.sql` — **liegt in `phase2_persistence/migrations/`** (Code=SoT, s. Step-12-Block), **nicht** `phase7_reward/migrations/` | `ADD COLUMN initial_risk` / `r_multiple` **/ `account`** (Operator 2026-06-18, s. 1.7) + Whitelist-Erweiterung `persistence/db.py` (`_TRADE_COLUMNS`/`_REWARD_COLUMNS`) | ✅ Step 12 |
| `scripts/wiring.py` (`build_reward_sink`/`build_brain`/`build_executor`, spiegelt P6 — Executor direkt aus `execution`, `reward_sink` injiziert, **keine** P5-Edit) · `backfill_synthetic.py` (guard-first, nie live) · `smoke_test.py` (1× echter Haiku-`reflect`, DRY) · `live_test.py` (voller open→close→reward→lesson **+ reconcile-Retry bei IG-Lag**) · `inspect_history.py` (**read-only** History-Dump, Live-Debug 2026-06-23) | Composition + Operator-Tools | ✅ Step 13 (·13b) |
| `execution/protocols.py`-Edit + `executor.py`-Edit (P5) + Regression | `RewardSink`-Protocol + Naht (Decision A) — keyword-only `reward_sink=None` ⇒ P5 bit-identisch; `on_trade_opened`/`on_trade_closed` um `monitor_position`, beide guarded (J); `build_opened`/`build_closed` mit **lazy** `reward.models`-Import | ✅ Step 10 |
| `tests/{__init__,test_models,test_packaging}.py` | Step-3-Tests (21: Contracts/frozen/§5-Defaults/Exceptions + Editable-Install-Smoke) | ✅ Step 3 |
| `tests/test_confidence.py` | Wilson/Expectancy/SQN/N_min-Gate + Anti-Pattern-Beweis + Monotonie (30 Fälle, Ziel ≥14) ★ | ✅ Step 4 |
| `tests/test_scorer.py` | Prozess-vs-Outcome-Trennung, Clamping, Symmetrie/Asymmetrie, R-Clip, schwaches Debate-Signal (18 Fälle, Ziel ≥12) ★ | ✅ Step 5 |
| `tests/test_synthetic.py` | Generator-Determinismus/Labels, Pfad-Guard trifft Live-Pfad nie (+Aliasing), Edge-Selector Synthetik-Ausschluss + Demo-Toggle (11 Fälle, Ziel ≥8) | ✅ Step 6 |
| `tests/conftest.py` + `tests/test_brain.py` | erster P7-Fake (`FakeLLM`); valide Lesson → `ok=True`-verbatim, Prompt trägt R/Status/Kontext, alle Fehlerpfade → `ok=False`/kein Raise, AI-Grenze, Protocol (12 Fälle, Ziel ≥8) | ✅ Step 7 |
| `tests/test_pnl_resolver.py` | exakter/mehrdeutiger Match (size+Level+Recency), BUY-Win/SELL-Loss-R-Vorzeichen, `initial_risk==0` defensiv, not-ok/no-match/unbrauchbar → `PnLUnavailable`, ignoriert epic/direction (12 Fälle, Ziel ≥8) | ✅ Step 9 |
| `tests/test_recorder.py` | open→close schreibt alle 3 Tabellen + Delta-Mapping; PnLUnavailable→critical/kein Reward/Trade bleibt OPEN; Reward-Insert-Fehler→critical/Trade CLOSED; Lesson-Fehler→Reward bleibt; idempotenter Doppel-Close; no-Stash-Reconstruct; confidence_provider best-effort (14 Fälle, Ziel ≥10) | ✅ Step 8 |
| `tests/test_executor_seam.py` → **verlegt nach** `phase5_execution/tests/test_executor.py` | `reward_sink=None` → P5 bit-identisch; mit Sink → beide Callbacks + gebaute Snapshots; Debate-Flip; TIME_STOP; NO_TRADE feuert nicht; werfender Sink kippt den Zyklus nicht (7 Fälle, Ziel ≥6). **Placement-Reconciliation:** Executor + Fakes leben in P5, cross-test-package-Fake-Reuse ist nicht baubar → getestet, wo die Naht lebt (spiegelt den Debate-Seam-Präzedenzfall) | ✅ Step 10 |

Repo-Konventionen: `from __future__ import annotations`, Type-Hints + Docstrings, eine Datei = eine
Verantwortung, eigene typisierte Exceptions, nie still schlucken, Logging → stderr, `pytest` ohne
Netz/echtes LLM, atomic commits.

## Config-Defaults (`RewardConfig` — v1, am echten Profit zu tunen; Konzept §5)
| Feld | Default | Bezug |
|---|---|---|
| `n_min` | `10` | C — unter N_min keine belastbare Confidence (Wilson stabil ab ~n=10) |
| `wilson_z` | `1.96` | C — 95 %-Niveau, Lower-Bound als konservativer Schätzer |
| `point_value` | `1.0` | R-Multiple (DAX CFD 1 €/Punkt) |
| `score_min` / `score_max` | `0.0` / `100.0` | D — Clamp-Bounds |
| `max_delta_per_trade` | `5.0` | D — harter Cap auf `|outcome_delta + process_delta|` |
| `outcome_weight` | `2.0` | D — Skala der Outcome-Komponente (× geclamptes R) |
| `r_clip` | `3.0` | D — R-Multiple vor Scoring auf ±r_clip clippen (Tail-Schutz) |
| `process_weight` | `1.5` | B2 — Skala der Prozess-Komponente |
| `loss_asymmetry` | `1.0` | D — >1 ⇒ Verluste bewegen stärker; default symmetrisch |
| `tight_spread_pct` | `0.05` | B2 — Spread ≤ → guter Entry-Zustand (Prozess-Plus) |
| `clean_exit_bonus` | `1.0` | B2 — Exit via geplantem SL/TP (CLOSED_BY_BROKER) vs. Drift (TIME_STOP) |
| `lesson_model` | `"claude-haiku-4-5-20251001"` | E/F — ✅ valid + gepreist (s. 1.4) |
| `lesson_max_tokens` | `400` | E — eine knappe Lesson |
| `lesson_temperature` | `0.3` | E |
| `lesson_timeout_s` | `20.0` | E — eigener Timeout, blockt den Close-Pfad nie hart |
| `include_demo_in_edge` | `True` (Bootstrap) | H — Demo-Trades SIND die Datenquelle; Demo-Confidence ist nicht live-edge-validiert (re-baselinen bei Go-Live) |
| `live_db_path` | `"data/trading_bot.sqlite"` | H — Live-Ziel; **echter** P2-Pfad (`reward/models.py:347`; Konzept-§5-String `.db` war stale, s. 1.7) |
| `synthetic_db_path` | `"data/synthetic_reward.db"` | H — Synthetik-Ziel (Backfill-Tool schreibt NUR hierhin) |

## Verifizierte Contracts (Step 1 — gegen Live-Code gepinnt, 2026-06-18)
> Gepinnt gegen den Repo-Stand auf `main` (`49cda8a` + dieser Pre-Step). ⚠ = Befund, der vom
> Konzept abweicht / es unter-spezifiziert und in einen späteren Build-Step einfließt.

**(1.1) `get_trade_history`-Record-Shape — HÖCHSTE PRIORITÄT (`broker_wrapper/adapters/ig_adapter.py:555`):**
- `get_trade_history(days=30) -> Envelope`; `.data = {"transactions": [Transaction.__dict__, …]}`.
- `Transaction`-Felder (`broker_wrapper/models.py:117`): `transaction_id` (← IG `reference`), `epic`
  (← IG **`instrumentName`** = Anzeigename, **nicht** der Epic-Code), `direction` (**hardcoded
  `None`**), `size`, `open_level`, `close_level`, `profit_loss` (← `profitAndLoss`, Währungs-
  Buchstabe gestrippt), `currency`, `open_date`, `close_date`, `transaction_type`.
- ⚠ **KEIN `deal_id`, KEIN `deal_reference` im Record.** Das §9-Match „per deal_id/deal_reference"
  ist **unmöglich** — Matching muss heuristisch sein (instrumentName + size + Datum/Level-Nähe). Der
  **Level-basierte Fallback** im `pnl_resolver` (Step 9) ist damit der **primäre** Sicherungspfad,
  **nicht** optional. Bestätigt den P1-README-Caveat „best-effort, cross-check against a known deal".
- ⚠ **`size` ist VORZEICHENBEHAFTET (Live-Debug 2026-06-23).** IG liefert in `/history/transactions`
  ein `size` mit Vorzeichen (`-19.8` für SELL); `_parse_transaction` reicht es als **negativen Float**
  durch (`ig_adapter.py:863`, **kein** Sign-Handling). `OpenedTrade.size` ist immer unsigned → der
  `pnl_resolver`-Size-Filter vergleicht **Beträge** (`abs(abs(tx_size) − abs(size))`); ein exakter
  Vergleich verwarf **jeden SELL für immer** (erster Reward-Live-Lauf, deal `DIAAAAXTGBTEYAC`,
  size 19.8 → „no usable history row"). Fix sitzt **defensiv im P7-Resolver** (Phasen-Isolation); der
  „korrektere" Ort (Sign-Normalisierung im P1-Adapter) ist **bewusst zurückgestellt** — eine
  Cross-Phase-Berührung der live-verifizierten, gemergten P1 ist nicht nötig. **Operator-Flag:** wenn
  P1 je angefasst wird, dort `size` normalisieren und diese Resolver-Defensive prüfen.

**(1.2) `OrderPlan` / `OrderResult` / `place_order` (`execution/models.py`, `execution/order.py`, `ig_adapter.py`):**
- `OrderPlan(epic, direction, size, stop_level, limit_level, deal_reference, currency)` — absolute
  Level; **kein** Entry-/Open-Level-Feld.
- `open_position` → `OrderResult` = `{deal_reference, deal_id, status, epic, direction, size, level,
  reason, timestamp}`; `status ∈ {ACCEPTED, REJECTED, PENDING, UNKNOWN}`; `level` = echter Fill.
- ⚠ `place_order` returnt `ExecutionResult(status, deal_id, plan, detail)` — **der OPEN-`level` geht
  verloren**. Der echte Fill-Level wird nicht durchgereicht. `trade_outcomes.open_level` ist **NOT
  NULL** → Step 10 muss `open_level`/`intended_open_level` aus dem Executor-`price_env`
  rekonstruieren (oder aus `stop_level ± stop_distance_points` zurückrechnen). `initial_risk =
  abs(intended_open_level − stop_level) · size · point_value`.
- ✅ **GEÄNDERT (2026-06-23, Step 13c — cross-phase, user-authorized): der CLOSE-Level/-P&L wird
  jetzt DURCHGEREICHT.** Ursprünglich trug `monitor_position`/`ExecutionResult` **kein**
  `profit_loss`/`close_level` → P7 löste P&L nur über `get_trade_history` auf. **Befund:** IG-Demo
  bucht Transaktionen erst nach Settlement (intraday 0 Zeilen) → History intraday unbrauchbar.
  **Fix:** `close_position` (P1) pollt jetzt den Close-Confirm → `ExecutionResult.close_level`/
  `profit_loss` (P5, **nur TIME_STOP**) → `ClosedTrade.close_level`/`profit_loss` (P7) → der
  `pnl_resolver` **bevorzugt** diese lag-freie Quelle vor der History (die bleibt Fallback für
  `CLOSED_BY_BROKER`/Confirm-Timeout/Cold-Reconcile).

**(1.3) Debate-Outcome + `debate_log.json` (`debate/models.py`, `debate/audit.py`):**
- `DebateOutcome(decision, direction, confidence, rationale, rounds_used, transcript, token_summary)`
  — Judge liefert `.decision`/`.direction`/`.confidence`/`.rationale`. ✓
- `debate_log.json`-Record: `{ts, epic, seed_direction, final_decision, final_direction, confidence,
  rounds_used, rationale, regime_snapshot{…}, transcript[…], token_summary{…}}`.
- ⚠ **Kein `deal_id`/`deal_reference`/Zyklus-ID im Audit-Record → kein Join-Key zum Trade.** P7s
  `debate_confidence` muss aus dem **in-memory** Outcome zur Open-Zeit kommen (Executor-Scope), nicht
  aus dem Log rekonstruiert. Der Executor hält `outcome` aktuell **nicht** über den Enrichment-Block
  hinaus (`executor.py:171-184`) → Step 10 fängt `getattr(outcome, "confidence", None)`, default
  `None`, wenn keine Debatte lief.

**(1.4) Research-Reuse-Fläche (`research/llm_client.py`, `research/token_meter.py`, `research/models.py`):**
- `LLMClient(model, api_key, *, max_tokens, temperature, timeout_s, token_meter_path=None,
  config=None, enable_thinking=False, cache_system=False)`; `ask_candidate(system, user, json_schema)
  -> dict` (single-shot, 1 Retry). `token_meter.record(usage, model, config, path) -> dict` (8-Feld,
  cache-aware). Beide direkt für `brain.py` reusen.
- Default-Research-Modell = `claude-sonnet-4-6`; Pricing-Rows vorhanden: sonnet-4-6 (3/15), opus-4-8
  (5/25), **haiku-4-5-20251001 (1/5)** → `lesson_model="claude-haiku-4-5-20251001"` ist valid +
  gepreist.

**(1.5) Loop-Closure (Decision I) = der „Ja"-Zweig:**
- `research/context_builder.py:184` ruft bereits `db.get_recent_lessons(5)`; `research/prompt.py:215`
  rendert sie (`_render_lessons`). **Der Research-Prompt zieht Lessons bereits.** Step 11 = reines
  Schreiben, **keine** P4-Prompt-Änderung.
- ✅ **GELÖST (Step 11, 2026-06-22):** `db.mark_lesson_used` existierte, wurde aber **nicht von
  Research gerufen** → die „mark used"-Seite war unverdrahtet. **Step 11 verdrahtet sie** in
  `research/research.py`: `_DBLike` um `mark_lesson_used` erweitert + best-effort `_mark_lessons_used`
  **nach** dem erfolgreichen `ask_candidate` (vor der Validierung) → markiert alle in den Prompt
  gerenderten `context.recent_lessons` als genutzt; die Pre-LLM-Abbrüche (Preflight/leeres Universum/
  LLM-Fehler) markieren **nichts** (kein Over-Counting). **Erster DB-Write aus P4-Research** — ein
  benigner `used_in_research`-Increment, **kein** Trade/Outcome-Write, VETO-Schicht unberührt.

**(1.6) Protocol-Stil (`execution/protocols.py`):** `@runtime_checkable class XProtocol(Protocol)`,
Docstring, nur genutzte Methoden, `EnvelopeLike` für Broker-Returns (immer `.ok` vor `.data`). Das
`RewardSink`-Protocol (Step 10) spiegelt das exakt.

**(1.7) P2-Contracts (`persistence/db.py`, `migrations/001_initial.sql`) — Konzept §3 bestätigt, mit einer Lücke:**
- `_TRADE_COLUMNS` (19 Spalten; **kein `initial_risk`**, **kein `account`**), `_REWARD_COLUMNS`
  (hat bereits `process_score_delta, veto_trigger_count, gate_fail_count, debate_confidence,
  spread_at_entry_pct` → **B2 braucht KEINE Migration**; **kein `r_multiple`**), `_LESSON_COLUMNS`
  (json: `market_context_json`, `embedding_json`). Methoden (`insert_trade`/`update_trade_close`/
  `insert_reward`/`insert_lesson`/`get_current_score`/`get_risk_level(>50)`/`get_trade_by_deal_id`/
  `get_open_trades`/`get_recent_*`/`mark_lesson_used`) verhalten sich exakt wie §3 behauptet.
- `trade_outcomes` NOT NULL: `deal_id, epic, broker(dflt ig), direction, size, open_level, currency,
  open_ts, status(dflt OPEN), session_date, created_at(dflt), updated_at(dflt)` → `on_trade_opened`
  muss liefern: `deal_id, epic, direction, size, open_level, currency, open_ts, session_date`.
- ✅ **ERLEDIGT (Step 12, 2026-06-22): `account`-Spalte hinzugefügt.** `OpenedTrade.account
  ("demo"|"live")` (Step 3) und die Demo-Edge-Query (`include_demo_in_edge`, Step 6) brauchen sie
  persistiert. Das Konzept-§3/§12 spezifizierte Migration 002 nur mit `initial_risk` + `r_multiple` —
  **Step 12 erweiterte sie um `account TEXT`** und nahm `"account"` in `_TRADE_COLUMNS` (Whitelist)
  auf. Damit fließt der Demo/Live-Tag durch `insert_trade` → `trade_outcomes`. (Konzept §3/§12 mit
  dieser dateierten Entscheidung annotiert.)
- ⚠ **DB-Pfad-Diskrepanz:** der echte P2-Default ist `data/trading_bot.sqlite`
  (`init_db.py`/P2-CLAUDE.md), das Konzept §5 schreibt `data/trading_bot.db` für `live_db_path`. In
  Step 13 (`wiring.py`) den **echten** P2-Pfad nutzen, nicht den Konzept-String blind übernehmen.
- Migration-Runner (`persistence/migrations.py`): `NNN_*.sql`, `_schema_version`-Tabelle, wendet
  Versionen > current aufsteigend an, versions-gegated idempotent (`ADD COLUMN` selbst ist nicht
  re-runbar, aber der Guard verhindert Re-Apply). `002_phase7_reward.sql` wird auto-angewandt.
  ✅ **Step 12: bestätigt.** Der Runner scannt **nur** `schema.MIGRATIONS_DIR =
  phase2_persistence/migrations/` (`db.py:75`, `schema.py:14`) → `002` liegt **dort** (nicht im
  Konzept-§4-Pfad `phase7_reward/migrations/`), sonst fände `init_db.py`/`Database.run_migrations()`
  sie nie. Frische DB erreicht jetzt **Version 2**; die vier versions-asserting P2-Tests wurden v1→v2
  nachgezogen (+1 Spalten-Beweis, +2 Round-Trip-Beweise → **P2 59 → 62**).

## Step 0 / Step 0b — Housekeeping-Ergebnisse (2026-06-18)
- **Step 0 (Turbo-Cleanup) = dokumentierter No-Op.** `rg -i turbo` trifft nur den **frozen**
  Contract `turbo_candidates.json` (P2 `state.py`, P5 Gate 2/`seed_candidate.py`) + dessen
  dokumentierte Doku-Referenzen. Nichts umbenennen; das neue `phase7_reward/`-Paket führt **keine**
  Turbo-Referenz ein.
- **Step 0b (Codebase-Doku-Reconciliation) erledigt.** Kein Instinct→VETO-Framing in der Doku (der
  einzige „ECC"-Treffer in `phase4_research_plan_konzept.md:21` ist **„ECE"** = Calibration Error, ein
  False-Positive). **Eine echte Korrektur:** `ROADMAP.md` listete `longterm_pre_trade_check() VETO`
  unter Phase 7 — das widersprach dem Scope-Lock; Phase-7-Bullets auf das schlanke Modell geflippt,
  Instinct→VETO nach **Phase 9f** verschoben. Root-`CLAUDE.md` „Current state" auf Phase 7 geflippt
  (kanonische Aussage + Phase-7-Status-Block). `ARCHITECTURE.md`/`README.md`/
  `phase2_persistence_konzept.md` waren bereits konsistent (unverändert).

---

## Session stopped — 2026-06-23 (Step 13c — lag-free P&L from the close confirm, **cross-phase**)

> Auslöser: nach Step 13b lief `live_test` erneut `3/5` — diesmal **nicht** signed-size, sondern
> `inspect_history.py` bewies, dass **IG-Demo Transaktionen erst nach Settlement bucht**:
> `get_trade_history(days=1)` = **0 Zeilen** intraday; die einzige `days=30`-Zeile ist ein 11 Tage
> alter, gesettelter Deal (Vorzeichen `size=-19.9` bestätigte zusätzlich den 13b-Fix). Kein
> Reconcile-Fenster in Sekunden/Minuten gewinnt das Rennen → die History ist **intraday unbrauchbar**
> als P&L-Quelle. **User-Entscheidung (explizites „specific yes" für cross-phase):** P&L aus dem
> **Close-Deal-Confirm** auflösen (sofort verfügbar), nicht aus der History.

### Completed (cross-phase — P1 + P5 + P7, mit dated Notes in JEDER berührten `.md`)
- **P1 `ig_adapter.close_position`** — pollt jetzt den Close-Confirm: DELETE-`dealReference` fangen →
  `_poll_confirms` (derselbe Helper wie `open_position` für den Fill-`level`) → `close_level` +
  realisiertes `profit`/`profitCurrency` **additiv** in `.data`. **Best-effort + safe:** Confirm-Poll
  in `try/except`, der Close bleibt **ok-returning für jeden akzeptierten DELETE** (Confirm-Fehler/
  -Timeout → `None`-Felder, **nie** ein Error-Envelope) ⇒ P5-Close/Abort-Verhalten unverändert.
  +3 Tests → **P1 49 → 52**.
- **P5 `ExecutionResult`** +`close_level`/+`profit_loss` (Defaults `None`); **`monitor.py`** liest im
  **TIME_STOP**-Zweig `close_env.data` (CLOSED_BY_BROKER bleibt `None`). **Additiv, P5 bit-identisch.**
  +4 Tests (`test_monitor.py` +2, `test_executor.py` +2 build_closed) → **P5 142 → 146**.
- **P7** `ClosedTrade` +`close_level`/+`profit_loss`; `build_closed` (Naht in `executor.py`) füllt sie;
  **`pnl_resolver.resolve` Präferenz-Reihenfolge:** (1) `closed.profit_loss` → direkt (exakt, IG-
  realisierte P&L), (2) `closed.close_level`+Richtung → `(close−open)·size·point_value·sign`
  (kleine Approx: Open-Seite = `intended_open_level`), (3) sonst der bestehende History-Match
  (CLOSED_BY_BROKER/Confirm-Timeout/Cold-Reconcile). `_OpenCtx` +`direction` (für Branch 2 im
  Cold-Pfad). +4 Tests (resolver +3, recorder +1) → **P7 124 → 128**.

### Reconciliation (Code = Source of Truth)
- **Contract 1.2 aktualisiert:** „monitor trägt KEIN profit_loss/close_level" gilt **nur noch** für
  `CLOSED_BY_BROKER`; der bot-eigene TIME_STOP-Close reicht jetzt die realisierte P&L durch.
- **Branch 2 ist eine kleine Approximation** (Open-Seite = intended, nicht der echte Open-Fill — den
  droppt `place_order`, Contract 1.2). Exakt nur, wenn IG `profit` im Close-Confirm liefert (Branch 1).
  ✅ **RESOLVED am Live-Lauf (2026-06-26): Branch 1 feuerte** — IG liefert `profit` im Close-Confirm
  (`profit_loss=-41.16` vs. die Level-Rechnung ≈ -21.56; die Differenz **ist** der Spread, den nur die
  realisierte P&L erfasst → Branch 1 ist sogar genauer als Branch 2). Der Open-Fill-Folge-Step ist
  damit **nicht** nötig.
- **13b bleibt komplementär:** der magnituden-Size-Match + `reconcile_open_trades` sind weiterhin der
  Fallback-Pfad (CLOSED_BY_BROKER / Confirm-Timeout), der die (verzögerte) History nutzt.

### Verifiziert (gemockt/lokal — kein Netz; Live = Operator)
- **Regression grün:** **P1 52 · P2 62 · P4 94 · P5 146 · P6 70 · P7 128.** Alle Edits additiv (Defaults
  halten P1/P5 bit-identisch).

### ✅ Live-verifiziert (2026-06-26) — `live_test.py` 5/5
- **Operator-Lauf bestanden:** SELL-Seed (mit der Abwärtsbewegung) → Order ACCEPTED
  (`deal_id=DIAAAAXUYTL77A3`, size 19.6, open 24771.3) → Time-Stop-Close → der **Close-Confirm**
  lieferte close 24772.4 + `profit_loss=-41.16` → **in-cycle resolve gelang** (kein History-Fallback,
  kein Reconcile nötig) → `trade_outcomes` CLOSED + `reward_pts` (1) + `trade_lessons` (1, echte Haiku)
  → **`RESULT: 5/5`**, exit 0. Damit ist der **ganze** Reward-Loop end-to-end live bewiesen
  (place → monitor → close-confirm-P&L → score → reward → lesson). ⚠ **live-verifiziert ≠
  profit-validiert** — ein Trade beweist den Pfad, nicht die Edge.
- **Zwei Vorläufer-NO_TRADEs** (SELL-in-rally 06-23, BUY-in-drop 06-26) waren **korrekte** Momentum-
  VETOs (Seed gegen die Bewegung) — kein Bug. Lehre: in Richtung des `get_ohlcv`-net-return seeden.
- Die zwei stale OPEN-Deals (`DIAAAAXTGBTEYAC`/`DIAAAAXTGMAF2A9` aus den Debug-Läufen) bleiben als
  Demo-Daten stehen (oder via unscoped `reconcile_open_trades()` aufräumbar, sobald IG sie bucht).
- **Doku auf ✅ live-verifiziert geflippt + Merge `phase7-reward` → `main`** in **diesem** Commit
  (Operator-Freigabe 2026-06-26).

### Gotchas (für den Re-Entry)
- Branch **`phase7-reward`**. Step 13c ist **cross-phase** (P1+P5+P7) auf explizite User-Freigabe;
  jede berührte Phase hat eine dated Note (P1/P5 `CLAUDE.md` 🔁-Block, hier, Konzept §9, root CLAUDE.md).
- **AI-Grenze gewahrt:** close_position-Confirm, ExecutionResult-Felder, Resolver-Branches sind reiner Code.
- **`close_position` darf NIE wegen eines Confirm-Fehlers erroren** — der Confirm ist best-effort-Enrichment;
  ein akzeptierter DELETE bleibt ok (sonst kippt P5 in einen `ExecutionAbort`).

---

## Session stopped — 2026-06-23 (Step 13b — Reward-Live-Debug: signed-size fix + reconcile/retry)

> Auslöser: der **erste** Operator-Reward-Live-Lauf (`live_test.py`) war **`RESULT: 3/5`** — Order
> platziert + per Time-Stop geschlossen (deal `DIAAAAXTGBTEYAC`, SELL, size 19.8), aber
> `trade_outcomes` blieb **OPEN** und **kein `reward_pts`**. Einzige Ursache: `pnl_resolver.resolve()`
> warf `PnLUnavailable` (Branch „candidates empty" → `get_trade_history` lieferte Transaktionen, aber
> keine matchte size=19.8). Zwei mit dem einen Datenpunkt konsistente Ursachen — der Fix deckt **beide**.

### Completed (alles in `phase7_reward/` — **keine** Cross-Phase-Code-Edit)
- **`reward/pnl_resolver.py` — magnituden-basierter Size-Match.** Filter `abs(float(tx_size) − size)` →
  `abs(abs(float(tx_size)) − abs(size))`. **Grund:** IG signt das History-`size` (`-19.8` für SELL;
  `_parse_transaction` reicht es als negativen Float durch) → ein exakter Vergleich verwarf **jeden SELL
  für immer**, unabhängig von Lag. `opened.size` ist immer unsigned; positive Sizes bleiben unverändert
  (der Fix kann nur helfen). Modul-Docstring um den Befund erweitert. Der saubere Ort (P1-Adapter)
  bleibt **bewusst zurückgestellt** (Phasen-Isolation; nur dokumentiert, s. Contract 1.1).
- **`reward/recorder.py` — `reconcile_open_trades(deal_ids=None)` (die „spätere Pass").** IG-History kann
  einen frisch geschlossenen Deal Sekunden–Minuten verzögern → in-cycle `resolve` darf legitim
  `PnLUnavailable` werfen + den Trade OPEN lassen. Der neue Reconcile fährt den Close für noch-OPEN-Zeilen
  erneut: **exakter retained `ClosedTrade`** (`self._pending_close`, gleicher Prozess — behält den echten
  Exit-Status) **oder** Minimal-Rekonstruktion aus der DB-Zeile (Restart; Exit-Typ unbekannt → konservativ
  `"TIME_STOP"`). Delegiert an das geguardete `on_trade_closed` → **idempotent** über den OPEN/CLOSED-Status
  (kein Doppel-Scoring). `_pending_close` wird nach dem Close-Fakt gepoppt (kein Leak).
- **`scripts/live_test.py` — Reconcile-Retry vor den Asserts.** Bei `PLACED→TIME_STOP` und noch-OPEN-Zeile:
  `executor.reward_sink.reconcile_open_trades([deal_id])` in einer beschränkten Schleife
  (`--reconcile-attempts` default 3 × `--reconcile-wait` default 20 s) bis CLOSED oder Attempts erschöpft,
  **dann** die harten `trade_outcomes`(CLOSED)+`reward_pts`-Checks. Fortschritt → stderr.
- **`scripts/inspect_history.py` (NEU, read-only).** Dumpt `get_trade_history(days)`-Rohtransaktionen (v. a.
  das echte `size`-Vorzeichen + ob der Close erscheint) + die OPEN-`trade_outcomes`. **Pure read** — kein
  Order/Close/DB-Write. Entscheidet Lag vs. signed-size am Live-Record. Operator-Tool.
- **Tests (gemockt):** `test_pnl_resolver.py` +1 (negative `size=-19.8` matcht `opened.size=19.8`);
  `test_recorder.py` +5 (Reconcile löst nach Lag auf; reused retained Status; idempotent; cold-Rekonstruktion
  → TIME_STOP; scoped auf deal_ids lässt andere OPEN). `conftest.py`: `FakeBroker(responses=[…])`
  (Lag-Sequenz) + `FakeDB.get_open_trades`.

### Verifiziert (gemockt/lokal — kein Netz; der Live-Re-Run ist Operator)
- `pytest phase7_reward/tests -q` → **124 passed** (118 + 6). `py_compile` + `--help` (live_test,
  inspect_history) exit 0; `import reward.recorder` offline (hat `reconcile_open_trades`).
- **Regression grün + unberührt:** **P2 62 · P4 94 · P5 142 · P6 70** (Step 13b ist rein additiv im
  P7-Paket — **kein** P1/P2/P4/P5-Code berührt).

### Next — Operator (User führt aus; Claude macht Code + gemockte/lokale Tests)
1. (read-only, jederzeit) `python phase7_reward/scripts/inspect_history.py` → echtes `size`-Vorzeichen +
   ob `DIAAAAXTGBTEYAC` inzwischen in der History steht (bestätigt, welche Ursache aktiv war).
2. **Im Handelsfenster** neu seeden (`seed_candidate.py --direction SELL`, TTL 30 min) →
   `python phase7_reward/scripts/live_test.py` → erwartet open→Time-Stop→(Reconcile-Retry)→
   `trade_outcomes` CLOSED + `reward_pts` → **`RESULT: 5/5`**, exit 0. **Dann** Doku auf ✅ live-verifiziert
   flippen + Merge `phase7-reward` → `main`. ⚠ **code-complete ≠ live-verifiziert ≠ profit-validiert.**
- Housekeeping: die **stale** OPEN-Zeile `DIAAAAXTGBTEYAC` lässt sich per unscoped
  `reconcile_open_trades()` aufräumen (History hat aufgeholt + Size-Fix matcht sie) oder als Demo-Daten
  stehen lassen — Operator-Entscheidung.

### Gotchas (für den Re-Entry)
- Branch **`phase7-reward`**. Step 13b ist **kein neuer Build-Step**, sondern der Live-Debug-Fix nach dem
  ersten Reward-Live-Lauf — Phase 7 bleibt code-complete, **offen ist der saubere 5/5-Re-Run + Doku-Flip + Merge**.
- **AI-Grenze gewahrt:** Resolver/Reconcile/inspect sind **reine Mathe/Code** — kein LLM. Die einzige AI im
  Paket bleibt `Brain.reflect`.
- **Der Fix sitzt im P7-Resolver, nicht in P1.** Wer das IG-`size`-Vorzeichen im P1-Adapter „sauberer"
  normalisieren will: zulässig, aber Cross-Phase — erst mit Operator absprechen (P1 ist live-verifiziert + gemergt).

---

## Session stopped — 2026-06-23 (Step 13 — Wiring + Credentials-Shim + Operator-Scripts) → **Phase 7 code-complete**

### Completed (alles additiv in `phase7_reward/`, **keine** Cross-Phase-Code-Edit)
- **`reward/credentials.py`** — Keyring-Shim, **verbatim** gespiegelt von `debate/credentials.py`/
  `research/credentials.py` (`parents[2]`-Bootstrap auf `phase1_broker_wrapper`, re-exportiert
  `get_credential("anthropic_api_key")`, `__all__`). Die eine dokumentierte Phasen-Ausnahme
  (Decision F / Hard Rule 1). **Nicht** von Unit-Tests importiert.
- **`scripts/wiring.py`** — die Composition (spiegelt P6-Wiring): `build_reward_sink(broker, db, *,
  reward_config=None)` (Scorer(cfg) + reused `research.LLMClient` Haiku aus `cfg.lesson_*` +
  Brain(llm,cfg) → `RewardSink(db=…, broker=…, scorer=…, brain=…, cfg=…)`), `build_brain(*,
  reward_config=None)` (Standalone für smoke), `build_executor(config, *, confirm_fn,
  broker_name="ig_demo", reward_config=None)` baut den P5-`Executor` **direkt aus dem installierten
  `execution`-Paket** (löst die `scripts.wiring`-Namenskollision P4/P5/P6/P7), teilt **einen** Broker,
  `research_runner=_no_research` (seeded-candidate Live-Pfad), **`reward_sink=` injiziert**, tz-aware
  `now_fn`. **Keine P5-`ig_bot.py`-Edit** (Phasen-Isolation; P6-Präzedenz). Reward-Live-Pfad ist
  **debatte-frei** (einzige AI = die Lesson-Haiku; `debate_confidence=None`, vom Scorer behandelt).
- **`scripts/smoke_test.py`** — ein **echter** Haiku-`reflect()` über einen handgebauten `ClosedTrade`
  + `RewardResult` + `market_context`, **DRY** (kein DB-Write, kein Executor). Lesson + `last_usage`
  → stderr, `LessonResult`-JSON → stdout; exit 0 bei `ok`, sonst 1.
- **`scripts/live_test.py`** — voller open→close→reward→lesson gegen IG-Demo (spiegelt P6-`live_test`):
  `build_executor(reward_sink injiziert)`, short-hold (`max_hold=1`/`poll=10s`), reuse
  `execution.ig_bot.make_confirm_fn`/`result_to_dict`. Bei platziertem+geschlossenem Order **harte**
  Checks gegen `data/trading_bot.sqlite`: `trade_outcomes`-Zeile CLOSED + `reward_pts`-Zeile; die
  `trade_lessons`-Zeile ist **best-effort** (einzige AI, Decision E/J) → nur Info-Zeile, **nicht**
  hart gegated. `NO_TRADE`/Abstain = valider exit 0 (Reward-Proofs übersprungen). Reuse P5
  `seed_candidate.py` (kein neues Seed-Tool).
- **`scripts/backfill_synthetic.py`** [→ Opus] — Operator-Tool. **`guard_synthetic_path(db_path, cfg)`
  ist der ERSTE ausführbare Schritt** (vor jedem DB-Open) → `SyntheticSafetyError` + exit 2, wenn das
  Ziel == `live_db_path`. Sonst: `SyntheticTradeGenerator` → `Database(target)` + `run_migrations()` →
  je Trade eine CLOSED `trade_outcomes`-Zeile (`account='synthetic'`, `initial_risk=1.0`) + eine via
  `Scorer.score(...)` bepunktete `reward_pts`-Zeile; danach `compute_confidence`-Summary (observe-only).
  stdout=Summary-JSON, stderr=Fortschritt + Guard-Bestätigung.

### Reconciliation (Code = Source of Truth — Konzept §6 Step 13 dateiert)
- **Wiring spiegelt P6, nicht „inject in ig_bot.py":** Konzept §13 erlaubte „… (oder an `ig_bot.py`-
  Composition)". Gewählt: P7 baut ein **eigenes** `build_executor` (wie P6), **keine** P5-Datei-Berührung
  → Phasen-Isolation gewahrt, P5 bit-identisch.
- **Reward-Live-Pfad debatte-frei** (bewusst): das Konzept verlangt „voller open→close→reward→lesson",
  **nicht** Debatte. Debatte ist orthogonal (später additiv via P6-`debate_runner` injizierbar) → der
  Live-Gate bleibt billig/deterministisch (eine AI-Zeile statt vier).
- **`trade_lessons` im live_test = Info, nicht hart-gegated:** die Lesson ist best-effort (Decision E/J;
  ein flaky Haiku-Call darf den Close nie brechen) → `trade_outcomes`(CLOSED) + `reward_pts` sind die
  harten Proofs, die Lesson wird gemeldet. Konzept-§7-Done-Kriterium „erzeugt eine Lesson-Zeile" gilt
  in der Praxis (gesunder Lauf schreibt sie), ist aber nicht als FAIL gegatet.
- **Keine neuen Unit-Tests** (Scripts + Shim sind operator-run, nicht von `pytest` collected — konsistent
  P4/P5/P6); der testbare Kern der Synthetik-Trennung (`guard_synthetic_path`/`select_edge_set`/
  `compute_confidence`) ist bereits in Steps 4/6 gedeckt (inkl. §7(c)-Beweis „Synthetik trifft Live nie").

### Verifiziert (gemockt/lokal — kein Netz; Live-Lauf = Operator)
- `py_compile` aller 5 Dateien OK. `import reward.credentials` **offline** (re-exportiert `get_credential`),
  `import scripts.wiring` **offline** (alle 3 Entry-Points, **kein** Netz/Keyring — alle Cross-Phase-Imports
  lazy in den Funktionskörpern). `--help` aller 3 CLIs exit 0.
- **`backfill_synthetic.py` end-to-end gegen Temp-DB gelaufen** (lokaler SQLite-Write, **kein Netz**):
  `--n 12 --win-rate 0.6 --seed 7` → 12 `trade_outcomes` + 12 `reward_pts`, **Migration-002-Spalten
  befüllt** (`account='synthetic'`, `initial_risk=1.0`, `r_multiple=1.5`), `confidence=OK`, exit 0.
  **Guard-Refusal** (`--db-path data/trading_bot.sqlite`) → `REFUSED` + exit 2, **kein** Write.
- **Regression grün + unberührt:** **P7 118 · P2 62 · P4 94 · P5 142 · P6 70** (Step 13 ist rein additiv
  im P7-Paket, **keine** Cross-Phase-Code-Edit).

### Next — Operator (User führt aus; Claude macht Code + gemockte/lokale Tests)
1. `bash scripts/dev_install.sh` (installiert P1–P7 editable).
2. `python phase2_persistence/scripts/init_db.py` (wendet Migration 002 an — die Reward-Spalten).
3. **Im Handelsfenster** (09:00–17:30 Europe/Berlin), **mit** dem aktuellen `get_ohlcv`-net-return:
   `python phase5_execution/scripts/seed_candidate.py --direction SELL` (TTL 30 min!).
4. `python phase7_reward/scripts/smoke_test.py` (DRY — ein echter Haiku-`reflect`, sichtbare Lesson + Kosten).
5. `python phase7_reward/scripts/live_test.py` → erwartet open→Time-Stop-close → `trade_outcomes`+`reward_pts`
   (+ best-effort `trade_lessons`), `exit 0`. **Dann** Doku auf ✅ live-verifiziert flippen + Merge `phase7-reward`
   → `main` (beides Operator-Entscheidung). ⚠ **code-complete ≠ live-verifiziert ≠ profit-validiert.**
- Optional: `python phase7_reward/scripts/backfill_synthetic.py --n 40 --win-rate 0.55 --seed 7` (NUR
  synthetischer Pfad — Guard schützt die Live-DB).

### Gotchas (für den Re-Entry)
- Branch **`phase7-reward`**. **Phase 7 ist code-complete** (Steps 0–13); offen ist **nur** der Operator-
  Live-Lauf + der Doku-Flip auf „live-verifiziert" + der Merge nach `main`.
- **AI-Grenze gewahrt:** die einzige AI im ganzen Paket bleibt `Brain.reflect` (ein Haiku-Call, best-effort).
  Wiring/Scripts sind reine Komposition. Wer hier scoren/gaten/vetoen per LLM will → **stop**.
- **`reward.credentials`/`scripts.wiring` lesen den Keyring erst beim Aufruf von `build_*`** (nicht beim
  Import) → `pytest`/`--help` bleiben offline. Der Anthropic-Key wird beim `build_reward_sink`/`build_brain`
  gelesen; der SDK-Call feuert erst in `reflect`.

---

## Session stopped — 2026-06-22 (Step 12 — Migration `002` + minimale P2-Whitelist-Berührung, Decision G)

### Completed
- **`phase2_persistence/migrations/002_phase7_reward.sql`** (NEU) — additive, version 2:
  `ADD COLUMN trade_outcomes.initial_risk REAL` + `trade_outcomes.account TEXT` +
  `reward_pts.r_multiple REAL`. Damit landen die Felder, die `Scorer`/`RewardSink`/`build_opened`
  bereits **schreiben**, gegen die echte DB (vorher von der P2-Whitelist still verworfen).
- **`phase2_persistence/persistence/db.py`** (einzige Logik-nahe P2-Berührung, **keine** Logik-Änderung):
  `_TRADE_COLUMNS += ("initial_risk", "account")` und `_REWARD_COLUMNS += ("r_multiple",)`. `_insert`
  schneidet weiterhin per Whitelist — die vom Reward-Layer gesendeten Keys werden jetzt persistiert.
- **`phase2_persistence/tests/test_migrations.py`** — vier versions-asserting Tests v1→v2 nachgezogen
  (`test_fresh_db_reaches_version_2`, `test_rerun_is_noop` → Version 2 + 2 `_schema_version`-Zeilen,
  `test_find_pending_respects_current` → `[1,2]`/`[2]`/`[]`, `test_database_run_migrations_idempotent`
  → 2) + **neu** `test_phase7_columns_present` (PRAGMA-Beweis, dass 002 die Spalten anlegt).
- **`phase2_persistence/tests/test_db.py`** — **+2 Round-Trip-Beweise**:
  `test_insert_trade_persists_initial_risk_and_account` + `test_insert_reward_persists_r_multiple`
  (gegen die migrierte `db`-Fixture → Migration **und** Whitelist zusammen bewiesen).

### Reconciliation (Code = Source of Truth — Konzept §4/§6 Step 12 dateiert)
- **Migrations-Datei liegt in `phase2_persistence/migrations/`, NICHT `phase7_reward/migrations/`**
  (wie Konzept §4 listet). Grund: der Runner (`persistence/migrations.py`) und
  `Database.run_migrations()` scannen **nur** `schema.MIGRATIONS_DIR = phase2_persistence/migrations/`
  (`db.py:75`, `schema.py:14`). Anderswo abgelegt würde `init_db.py` sie nie anwenden + eine frische
  DB hätte die Spalten nicht. Deckt sich mit der P2-Regel „DDL lebt **nur** in `migrations/*.sql`".
  (Operator-bestätigt: phase2-Dir + 3/4 Tests fixen, statt den Runner multi-dir-fähig zu machen.)
- **Idempotenz von 002:** `ADD COLUMN` ist in SQLite nicht selbst `IF NOT EXISTS` → die Re-Apply-Sperre
  kommt aus der `_schema_version`-Tabelle (Version 2 wird genau einmal angewandt; Re-Run = No-Op).
  Die Crash-mid-script-Recovery-Kante ist **bestehendes** Runner-Verhalten — außerhalb Step-12-Scope.

### Verifiziert (gemockt — kein Netz, kein LLM, Temp-/Local-SQLite)
- `pytest phase2_persistence/tests -q` → **62 passed** (59 + 3 neue). **Regression grün + unberührt:**
  **P7 118 · P4 94 · P5 142 · P6 70.** (Nur P2 änderte Verhalten; alle anderen Suiten nutzen
  Fakes/Temp-DBs und importieren nichts Betroffenes.)
- Safety-Grep vorab bestätigte: `test_migrations.py` ist der **einzige** versions-asserting Ort; die
  `run_migrations`-Caller in `init_db.py`/`live_test.py` asserten **keine** feste Versionsnummer.

### Next — **Step 13** (`wiring.py` + Operator-Scripts) — getrennt zu planen
- `reward/credentials.py` (dünner Shim → `broker_wrapper.credentials.get_credential("anthropic_api_key")`,
  spiegelt P4/P6), `scripts/wiring.py` (baut `RewardSink` mit echtem P1-Broker / P2-`Database` /
  reused `research.LLMClient` (Haiku) + verdrahtet `reward_sink` in eine Composition — spiegelt P6s
  eigenes `build_executor`, **keine** P5-`ig_bot.py`-Änderung), `scripts/backfill_synthetic.py` [→ Opus]
  (harter Guard gegen `live_db_path`), `scripts/smoke_test.py` (ein echter Haiku-`reflect()`, DRY),
  `scripts/live_test.py` (voller open→close→reward→lesson gegen IG-Demo). **Smoke/Live = Operator-Lauf.**
- Beim Wiring den **echten** P2-Pfad `data/trading_bot.sqlite` nutzen (config-Tabelle oben + `models.py:347`).

### Gotchas (für den Re-Entry)
- Branch **`phase7-reward`**. Step 12 ist eine **P2**-Berührung (vom Konzept Decision G verlangt) — die
  Tests laufen in der **P2**-Suite (`pytest phase2_persistence/tests`); **P2 ist jetzt 62, nicht 59.**
- **AI-Grenze gewahrt:** Migration + Whitelist sind reines Schema/Code — kein LLM.
- ⚠ Eine **stale** Dev-/Runtime-DB (gitignored `data/trading_bot.sqlite`) auf Version 1 bekommt 002 beim
  nächsten `init_db.py`/`Database.run_migrations()` **automatisch** (idempotent). Kein manueller Eingriff.

---

## Session stopped — 2026-06-22 (Step 11 — Loop-Closure: `mark_lesson_used` in P4-Research verdrahtet)

### Completed
- **`phase4_research/research/research.py`** (Phase-4-Edit, vom Konzept §6 Step 11 / Decision I
  **explizit verlangt**): die „read→prompt"-Hälfte des Loops war bereits verdrahtet (Contract 1.5 —
  `build_context` zieht `get_recent_lessons(5)`, `prompt._render_lessons` rendert sie); **Step 11
  verdrahtet die fehlende „mark used"-Hälfte.**
  - `_DBLike`-Protocol um `mark_lesson_used(lesson_id)` erweitert (+ Docstring: Research macht jetzt
    **einen** Bookkeeping-Write, die Loop-Closure — **kein** Trade/Outcome-Write).
  - Neuer best-effort Helper `_mark_lessons_used(lessons)`: iteriert die Lessons, skippt fehlende `id`,
    `mark_lesson_used` pro Lesson in `try/except` → **`log.warning` + weiter** (Bookkeeping darf den
    Zyklus / die No-Trade-Entscheidung **nie** brechen).
  - Aufruf **direkt nach** erfolgreichem `ask_candidate` (vor der Validierung) — der semantisch
    korrekte „used in research"-Punkt (das Modell hat den Prompt mit den Lessons **beantwortet**). Die
    Pre-LLM-Abbrüche (Preflight/leeres Universum/LLM-Fehler) returnen davor → **kein** Mark.
- **`phase4_research/tests/conftest.py`** — `FakeDB` um `mark_lesson_used` (recording via `marked_used`)
  + `mark_raises`-Injektion erweitert (additiv; Bestands-Tests unberührt).
- **`phase4_research/tests/test_research.py`** — **+6 Loop-Closure-Tests** (Ziel ≥4): PASS markiert
  `[1,2]`; Abstain-Antwort markiert (LLM erreicht); leeres Universum / Session-Health-Fail / LLM-Fehler
  markieren **nichts**; Lesson ohne `id` wird geskippt; werfendes `mark_lesson_used` bricht den
  PASS-Zyklus **nicht** (Pick trotzdem gespeichert).

### Reconciliation (Code = Source of Truth — Konzept §6 Step 11 dateiert)
- **Placement: nach erfolgreichem `ask_candidate`, vor der Validierung** — **nicht** in `build_context`
  (würde bei Pre-LLM-Abstains over-counten) und **nicht** in der reinen `prompt.py` (keine Seiteneffekte/
  kein DB). Best-effort/`warning` (P4 ist nicht die Safety-Schicht; P7s `critical` gilt für die
  Outcome-/Reward-Writes). **Erster DB-Write aus P4-Research** — konzept-sanktioniert (Decision I).

### Verifiziert (gemockt — kein Netz, kein LLM)
- `pytest phase4_research/tests -q` → **94 passed** (88 + 6; `test_validator.py` bleibt 18). **Regression
  grün + unberührt:** **P7 118 · P5 142 · P6 70 · P2 59** (P2 bestätigt den `mark_lesson_used`/
  `get_recent_lessons`-Contract via `test_db.py` — unverändert).

### Next — **Step 12** (Migration `002` + minimale P2-Berührung, Decision G)
- `migrations/002_phase7_reward.sql` (additiv, idempotent über die `_schema_version`-Tabelle):
  `ALTER TABLE trade_outcomes ADD COLUMN initial_risk REAL;` + `… ADD COLUMN account TEXT;` +
  `ALTER TABLE reward_pts ADD COLUMN r_multiple REAL;`. `persistence/db.py`: **nur**
  `_TRADE_COLUMNS += ("initial_risk", "account")` + `_REWARD_COLUMNS += ("r_multiple",)`
  (Whitelist-Erweiterung — keine Logik-Änderung). **P2-Tests (59) danach grün.** Damit landen die vom
  Recorder/Seam bereits geschriebenen Felder (heute still verworfen) gegen die echte DB. Danach Step 13
  (Wiring + Operator-Scripts).

### Gotchas (für den Re-Entry)
- Branch **`phase7-reward`**. Step 11 ist eine **P4**-Datei-Berührung (vom P7-Konzept verlangt) —
  die Tests laufen in der **P4**-Suite (`pytest phase4_research/tests`).
- **AI-Grenze gewahrt:** `mark_lesson_used` ist deterministisches Bookkeeping (Increment + Timestamp),
  kein LLM. Wer hier den LLM „entscheiden" lässt, welche Lesson genutzt wurde → **stop** (alle
  gerenderten Lessons sind genutzt — Code-Regel).

---

## Session stopped — 2026-06-22 (Step 10 — Executor-Naht verdrahtet; **erste P5-Berührung**)

### Completed
- **`execution/protocols.py`** — neues `@runtime_checkable class RewardSink(Protocol)` (Stilvorlage =
  bestehende Protocols, Contract 1.6). Zwei Methoden `on_trade_opened(opened: Any)` /
  `on_trade_closed(closed: Any)` — Payloads **`Any`** (duck-typed → **kein** `reward`-Import in P5).
- **`execution/executor.py`** — additiver, **keyword-only** `reward_sink: Any | None = None` (default
  `None` ⇒ **P5 bit-identisch + AI-frei**, spiegelt `debate_runner`). `outcome` auf **Run-Scope**
  gehoben (`outcome: Any = None` vor dem Debate-Block) → die Open-Naht liest `getattr(outcome,
  "confidence", None)` ob mit/ohne Debatte (Contract 1.3). Im place/monitor-Block: `_notify_opened(...)`
  **nach** `place_result.status == "OPEN"` und **vor** `monitor_position`; `monitor_position`-Return
  gefangen → `_notify_closed(result)` → `return`. **Beide `_notify_*` guarded** (`try/except Exception`
  → `logger.critical`, kein Re-raise, Decision J); `_notify_closed` feuert **nur** bei `status ∈
  {CLOSED_BY_BROKER, TIME_STOP}` (OPEN/ABORT = kein settled Close → Reconcile-Sache).
- **`build_opened`/`build_closed`** = Modul-Helper, die die Executor-Locals in die P7-Contracts
  (`OpenedTrade`/`ClosedTrade`) übersetzen. `intended_open_level` aus `price_env` rekonstruiert
  (BUY→ask/SELL→bid, exakt wie `build_order_plan` — `place_order` droppt den Fill-`level`, Contract 1.2);
  `initial_risk = |entry − stop|·size·point_value`.
- **`phase5_execution/tests/test_executor.py`** — **+7 Seam-Tests** (Ziel ≥6) + `_RecordingSink`;
  `FakeDB` um `get_current_score` (DbProtocol-vollständig) ergänzt, `_DebateOutcome` um `confidence`,
  `_build` um `reward_sink`.

### Drei dokumentierte Konzept↔Code-Reconciliations (Code = Source of Truth — auch Konzept §6 Step 10 dateiert)
1. **Lazy `reward.models`-Import** *innerhalb* von `build_opened`/`build_closed` (nicht Modul-Top) →
   `executor.py`-Modul-Imports bleiben `execution.* + stdlib`; ein sink-freier Lauf zieht **kein**
   `reward` (laufzeit-bewiesen: `import execution.executor` → kein `reward`/`anthropic` in `sys.modules`).
   Spiegelt `ig_bot.py`s lazy `scripts.wiring`-Import. Die Contracts sind die Single-Source-of-Truth-
   Payload-Form (stdlib-only Dataclasses, dependency-light) — kein lokales Re-Modellieren der ~18 Felder.
2. **`point_value=1.0` + `account="demo"` als v1-Konstanten:** `ExecutionConfig` hat **kein**
   `point_value` (DAX 1 €/pt; `sizing.py` hardcodet 1.0 ebenso) → `build_opened` nutzt dieselbe
   Konstante. `account` ist in der Bootstrap-Phase fest `"demo"` (einziger getesteter Pfad; Go-Live
   ist fern + gated) — der **durable** Demo/Live-Tag gehört in die Wiring-Schicht (Step 13, kennt
   `broker_name`) und kann dort gehärtet/überschrieben werden.
3. **Test-Placement:** Konzept §4 listete `phase7_reward/tests/test_executor_seam.py`; die Tests leben
   stattdessen in `phase5_execution/tests/test_executor.py` (wo Executor + Fakes liegen, neben dem
   strukturgleichen Debate-Seam). Cross-test-package-Fake-Reuse ist nicht baubar → getestet, wo die
   Naht lebt. Der P7-Suite-Count (118) bleibt; die Naht-Regression sitzt in P5 (135 → **142**).

### Verifiziert (gemockt — kein Netz, kein LLM, keine echte Order)
- `pytest phase5_execution/tests -q` → **142 passed** (135 + 7 Seam). **Regression grün + unberührt:**
  **P7 118 · P4 88 · P6 70.** Inkl. Beweis-Tests: `reward_sink=None` bit-identisch; voller BUY-Pfad →
  beide Callbacks **einmal** mit korrekten Snapshots (`intended_open_level==ask 18000`, `initial_risk==30.0`,
  `account=="demo"`, `debate_confidence is None`); Debate-Flip → `direction=="SELL"`/entry==bid/
  `debate_confidence==0.82`; TIME_STOP-Close feuert `on_trade_closed` mit `status=="TIME_STOP"`;
  NO_TRADE/Abstain feuert **keinen** Callback; werfender `on_trade_opened`/`on_trade_closed` kippt den
  Zyklus **nicht** (`CLOSED_BY_BROKER` returnt trotzdem, Decision J).
- **Phasen-Isolation:** `import execution.executor` zieht **kein** `reward`/`anthropic` (laufzeit-geprüft).

### Next — **Step 11** (Loop-Closure, Decision I)
- Contract 1.5: `research/context_builder.py` zieht Lessons **bereits** (`get_recent_lessons(5)`) +
  `research/prompt.py` rendert sie → **kein** P4-Prompt-Change nötig. Offen: `db.mark_lesson_used`
  wird **nicht** von Research gerufen → die „mark used"-Seite ist unverdrahtet. Step 11 = `mark_lesson_used`
  verdrahten (kleiner, klar gekennzeichneter P4-Sub-Step) + Test: eine P7-geschriebene Lesson taucht im
  nächsten Research-Kontext auf, P4-Tests danach grün. **Danach** Step 12 (Migration 002 + P2-Whitelist),
  Step 13 (Wiring + Operator-Scripts — wo `account` seine durable Demo/Live-Quelle bekommt).

### Gotchas (für den Re-Entry)
- Branch **`phase7-reward`**. P5-Seam-Tests laufen in der **P5**-Suite (`pytest phase5_execution/tests`),
  nicht der P7-Suite. `phase1_broker_wrapper/.venv/bin/python -m pytest …`.
- ⚠ **Migration 002 (Step 12) fehlt noch:** `build_opened` schreibt `initial_risk`/`account` (und der
  Recorder `r_multiple`), aber die P2-Whitelist **verwirft sie still** bis Step 12 → gegen die echte DB
  landen sie erst nach Migration. Unit-Tests (FakeDB / gebaute Snapshots) prüfen sie schon voll.
- **AI-Grenze gewahrt:** die Naht ist **passiv** — sie reicht nur Snapshots; sie bekommt **nie** Broker-
  Write/Gate/VETO (kann strukturell keinen VETO umgehen). Der Sink ist default `None` (P5 AI-frei).

---

## Session stopped — 2026-06-19 (Step 8 — `reward/recorder.py` orchestration; the linked-steps pair 9→8 is done)

### Completed
- **`reward/recorder.py`** — `class RewardSink(*, db, broker, scorer, brain, cfg, confidence_provider=None)`
  (alle keyword-only). Die Naht-Impl für Step 10. Referenziert **keinen** Gate/VETO/Order-Pfad (kann
  strukturell keinen VETO umgehen). **Jeder Persistenz-Schritt einzeln gekapselt → Fehler `logger.critical`
  + weiter; ein äußerer Guard macht beide Callbacks total (werfen nie, Decision J).**
  - **`on_trade_opened(opened)`** → `db.insert_trade(...)` (`intended_open_level`→`open_level`,
    `initial_risk`/`account` für Migration 002) **+ In-Memory-Stash** `self._opened[deal_id] = opened`.
  - **`on_trade_closed(closed)`** (retry-freundliche Reihenfolge): (0) Idempotenz-Guard via
    `get_trade_by_deal_id`-Status (`!= OPEN` → skip; `None` → critical/return; liefert `trade_id`-PK) →
    (1) `pnl_resolver.resolve(...)` **vor** dem Close (PnLUnavailable → critical, Trade bleibt OPEN, retry-bar) →
    (2) `update_trade_close` → (3)/(4) `get_current_score` + `scorer.score` + `insert_reward`
    (`outcome_delta`→`outcome_score_delta`, `process_delta`→`process_score_delta`, +`pnl_raw`/`r_multiple`/
    `debate_confidence`/`spread_at_entry_pct`) → (5) best-effort `brain.reflect` → `insert_lesson`.
- **Drei dokumentierte Konzept↔Code-Reconciliations (Code = Source of Truth, im Modul-Docstring + Konzept §6 Step 8 dateiert):**
  1. **In-Memory-Stash zwingend:** `trade_outcomes` hat **keine** Spalten für `spread_at_entry_pct`/
     `debate_confidence` (die liegen in `reward_pts`, erst am Close geschrieben) → der volle Prozess-Kontext
     kann **nicht** über die DB von open→close laufen. Stash (gleiche Sink-Instanz, ein Zyklus) trägt ihn;
     die DB-Zeile ist der durable Anker (`trade_id`-PK + OPEN/CLOSED-Status + kalter Minimal-Resolve-Kontext
     beim Restart). **Kein Stash → Neutral-Defaults** (`_NO_STASH_SPREAD=1.0` = kein Entry-Bonus, debate=None);
     die durablen Signale (R, Exit-Status) scoren normal.
  2. **`confidence_provider` = optionaler, keyword-only Forward-Compat-Hook** (Konzept §8 hatte ihn positional).
     **Observe-only:** keine Confidence-DB-Spalte → wird best-effort aufgerufen + geloggt, **nie** geschrieben,
     **gatet nichts** (Decision C). `cfg` steht vor ihm in der Signatur.
  3. **Idempotenz = OPEN/CLOSED-Status** (Decision J sanktioniert „Status ODER vorhandener Reward"):
     zweiter Close eines CLOSED-Deals wird übersprungen → Score nie verdoppelt. **Residual-Edge** (ehrlich):
     scheitert `insert_reward` **nach** erfolgreichem `update_trade_close`, ist der Trade CLOSED aber ungescored
     und ein Retro-Retry skippt → Reward verloren (geloggt `critical`, manueller Fix); das ist die benignere
     Seite vs. Doppel-Scoring (Konzept-Reihenfolge bewusst gewählt). `veto_trigger_count`/`gate_fail_count`
     bleiben v1 NULL (nicht score-tragend).
- **`reward/__init__.py`** exportiert jetzt zusätzlich `RewardSink`. **`tests/conftest.py`** ergänzt um
  `FakeDB` (P2-CRUD-Recorder + `fail_on`-Injektion) und `FakeBrain` (scripted `reflect`, `raises_exc`).

### Verifiziert (gemockt — kein Netz, kein LLM, kein echter Broker/DB)
- `pytest phase7_reward/tests -v` → **118 passed** (104 + **14 neue Recorder-Fälle**, Ziel ≥10). Inkl. der
  Beweis-Tests: open→close schreibt **alle 3** Tabellen mit korrektem Delta-Mapping; **PnLUnavailable →
  `critical`, kein Reward, `update_trade_close` nicht erreicht → Trade bleibt OPEN** (retry-bar);
  **Reward-Insert-Fehler → `critical`, Trade trotzdem CLOSED**; Lesson-Fehler (raise **und** ok=False) →
  Reward bleibt; **idempotenter Doppel-Close verdoppelt den Score nicht** (1 Reward); unbekannter deal_id →
  `critical`/kein Crash; **no-Stash-Reconstruct** (anderes Sink-Instanz schließt aus der DB-Zeile);
  `confidence_provider` best-effort (aufgerufen + werfender Provider kippt den Close nicht);
  `market_context` an den Brain trägt `r_multiple`/`status`/`direction`.
- **Phasen-Isolation:** `import reward.recorder` / `from reward import RewardSink` zieht **kein**
  `anthropic`/`research`/`broker_wrapper`/`execution`/`persistence`/`debate` (laufzeit-geprüft → NONE).
  **Sibling-Suiten grün + unberührt** (Steps 8/9 fassen nur `phase7_reward/` + Konzept-`.md` an):
  **P2 59 · P4 88 · P5 135 · P6 70**.

### Next — **Step 10** (Executor-Naht verdrahten, Decision A) + **P5-Regression** — ⚠ **erste P5-Berührung**
- `execution/protocols.py`: `RewardSink`-Protocol ergänzen (Stilvorlage = bestehende Protocols, Contract 1.6).
- `execution/executor.py`: `Executor.__init__(..., *, debate_runner=None, reward_sink=None, …)`.
  - Nach `place_result.status == "OPEN"` und **vor** `monitor_position`: `if self.reward_sink:
    self.reward_sink.on_trade_opened(build_opened(...))` — `build_opened` rekonstruiert `intended_open_level`
    aus `price_env` (BUY→ask/SELL→bid; Contract 1.2: `place_order` droppt den Fill-`level`), `initial_risk =
    abs(intended_open_level − stop_level)·size·point_value`, `debate_confidence = getattr(outcome,
    "confidence", None)` (Contract 1.3: Executor hält `outcome` nicht über den Enrichment-Block → ggf. fangen).
  - `monitor_position`-Return in Variable fangen; **danach** `on_trade_closed(build_closed(result))`; dann `return`.
  - **Beide Aufrufe in `try/except`** → ein werfender Sink kippt den Zyklus nie (J). `reward_sink=None` → P5 **bit-identisch**.
- **Tests (≥6):** `reward_sink=None` → bestehende Executor-Tests grün; mit Sink → beide Callbacks mit
  korrekten Payloads; werfender Sink → Zyklus liefert trotzdem sein `ExecutionResult`. **Pflicht-Regression P5 135 / P4 88 / P6 70.**

### Gotchas (für den Re-Entry)
- Branch **`phase7-reward`**. `pytest phase7_reward/tests -v` läuft direkt (editable-install).
- **AI-Grenze:** der Recorder orchestriert nur; die **einzige** AI ist das delegierte `brain.reflect` (best-effort).
  Wer hier scoren/gaten per LLM will → **stop** (das ist Scorer/Code).
- **Step 10 ist die erste P5-Datei-Berührung** — Decision A verlangt `reward_sink=None` ⇒ P5 bit-identisch.
  Spiegelt exakt das `debate_runner`-Default-Passthrough-Muster (Contract: `execution/executor.py`).
- ⚠ **Migration 002 (Step 12) fehlt noch:** `initial_risk`/`account`/`r_multiple` werden vom Recorder
  geschrieben, aber die P2-Whitelist verwirft sie still bis Step 12 → gegen die echte DB landen sie erst
  nach Migration. Unit-Tests (`FakeDB`) prüfen sie schon voll.

---

## Session stopped — 2026-06-19 (Step 9 — `reward/pnl_resolver.py`; built **before** Step 8 to resolve the linked-steps note)

### Build-order decision (the „current+next step are linked" note, resolved)
- The Step-7 block flagged: *„Step 8 braucht `pnl_resolver` (Step 9) — ggf. 9 vor 8 bauen oder im
  Recorder stubben."* Step 8s `on_trade_closed` ruft `resolve()` als **ersten** Schritt → den Recorder
  zuerst zu bauen würde den Resolver stubben. **Entscheidung (Operator-bestätigt): 9 vor 8.** Step 8
  konsumiert den **echten** Resolver über einen `FakeBroker` (kein Stub). Konzept-konform (Done-Kriterien
  sind reihenfolge-agnostisch). Beide Steps in **einer** Session, **zwei** atomare Commits.

### Completed
- **`reward/pnl_resolver.py`** — `resolve(closed, broker, opened, cfg) -> (close_level, profit_loss,
  r_multiple)`. **Deterministisch, kein AI, kein DB-Write.** Heuristischer History-Match, weil der
  IG-Record **kein `deal_id`** trägt (1.1): `epic` = **instrumentName** (Anzeigename, nicht der
  Epic-Code), `direction` = **hardcoded None** → beide als Match-Key unbrauchbar. Match = **harter
  size-Filter** + **open-level-Nähe** zu `opened.intended_open_level`, Tie-Break = **Recency** (jüngstes
  `close_date`; via Pre-Sort + `min`). `r_multiple = profit_loss / opened.initial_risk`; `initial_risk==0`
  → `0.0` (defensiv, **kein** ZeroDivision, raised nicht). `opened` ist **duck-typed** (nur `.size`/
  `.intended_open_level`/`.initial_risk`) → der Recorder kann einen Minimal-Kontext aus der DB-Zeile reichen.
- **Fallback = fail-closed (Decision J, Operator 2026-06-19):** kein brauchbarer Match (IG-Lag) oder
  not-ok-Envelope → **`PnLUnavailable`**. Das Konzept-§9-Level-Approx (`profit_loss ≈ (close_level −
  open_level)·…`) ist **nicht baubar** — `ClosedTrade` trägt **kein `close_level`** → würde eine Zahl
  erfinden. Stattdessen idempotenter Retry via `deal_id` (Recorder loggt `critical`, Trade bleibt am
  Broker geschlossen). Da der einzige Erfolgspfad ein echter History-Match ist, braucht v1 **keinen**
  `pnl_source`-Tag (die „approximated"-Provenienz entfällt).
- **`reward/__init__.py`** exportiert jetzt zusätzlich `resolve`. **`tests/conftest.py`** ergänzt um
  `FakeEnvelope`/`FakeBroker` (nur `get_trade_history`, duck-typed `.ok`/`.data`), `make_tx`
  (Transaction-`__dict__`-Shape mit den **unbrauchbaren** Keys epic=instrumentName/direction=None) und
  `make_opened` (OpenedTrade-Factory).

### Verifiziert (gemockt — kein Netz, kein LLM, kein echter Broker)
- `pytest phase7_reward/tests -v` → **104 passed** (92 + **12 neue Resolver-Fälle**, Ziel ≥8). Inkl.
  exakter Single-Match; Disambiguierung per Level-Nähe; Recency-Tie-Break; BUY-Win → +R / SELL-Loss → −R
  (kein Vorzeichen-Flip nötig, IG-`profit_loss` trägt das Vorzeichen); `initial_risk==0` → r=0.0/kein
  Raise; not-ok-Envelope/leere History/no-size-match/unbrauchbares (pl=None) → `PnLUnavailable`;
  **Match ignoriert epic/direction** (beweist heuristisch, nicht deal-id).
- **Phasen-Isolation:** `import reward.pnl_resolver` zieht **kein** `anthropic`/`research`/`broker_wrapper`/
  `execution`/`persistence`/`debate` (laufzeit-geprüft → NONE). Import-Smoke `from reward import resolve`
  OK (`is reward.pnl_resolver.resolve`).

### Next — **Step 8** (`reward/recorder.py` — die Orchestrierung, Decision A/J) — **jetzt unblocked**
- `class RewardSink(db, broker, scorer, brain, *, confidence_provider=None, cfg)`. `on_trade_opened` →
  `db.insert_trade(...)` **+ in-memory-Stash** `self._opened[deal_id] = opened`. ⚠ **Warum Stash:**
  `trade_outcomes` hat **keine** Spalten für `spread_at_entry_pct`/`debate_confidence`/`stop_level`/
  `limit_level` (die liegen in `reward_pts`, erst am Close geschrieben) → der volle Prozess-Kontext muss
  **in-memory** von open→close getragen werden (gleiche RewardSink-Instanz, ein Executor-Zyklus). Die
  DB-Zeile (`get_trade_by_deal_id`) liefert nur `trade_id`-PK + Idempotenz-Status.
- `on_trade_closed(closed)` (Konzept-Reihenfolge, retry-freundlich): (0) Idempotenz-Guard via
  `get_trade_by_deal_id`-Status (`!= "OPEN"` → skip; None → critical/return) → (1) `resolve(...)` (wirft
  `PnLUnavailable` **vor** `update_trade_close` → Trade bleibt OPEN, retry-bar) → (2) `update_trade_close`
  → (3) `score_before = get_current_score()`; `scorer.score(...)` mit Stash-Prozess-Signalen → (4)
  `insert_reward(trade_id, {outcome_score_delta, process_score_delta, score_after, win_loss, pnl_raw,
  r_multiple, debate_confidence, spread_at_entry_pct})` → (5) `brain.reflect(...)` best-effort →
  `insert_lesson(...)`. **JEDER Schritt einzeln gekapselt; Fehler → `logger.critical` + weiter (J).**
- ⚠ `r_multiple`/`initial_risk`/`account` fehlen bis Migration 002 (Step 12); P2-`_insert` verwirft
  unbekannte Keys still → das Schreiben ist gegen die echte DB harmlos und gegen `FakeDB` voll geprüft.

### Gotchas (für den Re-Entry)
- Branch **`phase7-reward`**. `pytest phase7_reward/tests -v` läuft direkt (editable-install).
- **AI-Grenze:** `pnl_resolver` ist **reine Mathe** — kein LLM, keine Heuristik-Halluzination (eine
  deterministische, dokumentierte Match-Regel). Wer hier einen LLM „den Trade matchen" lässt → **stop**.
- **Fallback ist Raise, nicht Erfinden:** wer in Step 8/9 eine Level-Approx-Zahl in den Reward schreibt →
  **stop** (Operator-Entscheidung: lieber `PnLUnavailable` + idempotenter Retry als eine erfundene P&L).
- `FakeBroker`/`make_tx`/`make_opened` liegen in `tests/conftest.py`.

---

## Session stopped — 2026-06-19 (Step 7 — `reward/brain.py` lesson extraction, the only AI) [→ Opus]

### Completed
- **`reward/brain.py`** — das **einzige AI-Modul der Phase** (Decision E). `class Brain(llm_client,
  cfg)` mit `reflect(closed, outcome, market_context) -> LessonResult`: **EIN** Haiku-Call über den
  wiederverwendeten `research.LLMClient` (duck-typed via lokalem `_LLMClientLike`-Protocol — **kein**
  `research`-Import, Phasen-Isolation, exakt wie P6 `debate._LLMClientLike`). Baut `(system, user,
  schema)` via `_build_lesson_prompt` (deutsch, AI-Grenze im System-Prompt: **eine** knappe Lektion,
  **keine** Zahlen/Score/Risiko-Entscheidung; `_fmt`-Choke-Point `None → "n/a"`, nie gefälschte 0),
  ruft `ask_candidate`, zieht `lesson_text` (leer/fehlt → Fehler).
- **`LessonExtractor`-Protocol** (`@runtime_checkable`, eine Methode `reflect`) = die **swappbare**
  Schnittstelle (Decision E) — der Step-8-Recorder bindet sich daran, nicht an `Brain`, damit ein
  späterer Batch/Scheduler-Extractor ohne Reward-Code-Änderung andockt. `Brain` erfüllt es.
- **Best-effort / fail-closed (Decision E/J):** der ganze `reflect`-Body in `try/except Exception` →
  jede Exception (Malformed/leer/`LLMResponseError`/Timeout/beliebig) → `LessonResult(ok=False,
  lesson_text=None, error=str(exc))`, **kein Re-raise, kein Crash**. `market_context` wird unverändert
  durchgereicht (der Recorder persistiert es als `market_context_json`).
- **`reward/__init__.py`** exportiert jetzt zusätzlich `Brain` + `LessonExtractor`.

### Drei dokumentierte Konzept↔Code-Reconciliations (Code = Source of Truth — auch in Konzept §6 Step 7 dateiert)
1. **Signatur `Brain(llm_client, cfg)`**, nicht `Brain(llm_client, token_meter, cfg)`: `ask_candidate`
   **meter't bereits intern** (ruft `research.token_meter.record`, legt den Record auf
   `client.last_usage`). Ein zweites `token_meter` würde **doppelt zählen** → `token_meter` wird
   **transitiv über den Client** wiederverwendet (Decision F erfüllt), `Brain` liest `last_usage` nur
   zur Beobachtung. Spiegelt P6 (`debate` liest `last_usage` statt neu zu metern).
2. **Log-Level:** die *eigene* best-effort-LLM-Fehlschlag-Zeile des Brains ist `logger.warning` (eine
   fehlende **optionale** Lesson, **kein** DB-Write) — das `logger.critical` aus Decision J gehört in
   den **Recorder** (Step 8), wo die Writes passieren.
3. **`reward/credentials.py` bleibt Step 13** (Wiring), nicht Step 7 → Step 7 ist unit-only, keyring-/
   SDK-frei (spiegelt P6, das `debate/credentials.py` erst im Wiring-Modul ergänzte).

### Verifiziert (gemockt — kein Netz, kein LLM)
- `pytest phase7_reward/tests -v` → **92 passed** (80 + **12 neue Brain-Fälle**, Ziel ≥8). Inkl.: valide
  Lesson → `ok=True`-verbatim + `market_context`-Echo; Prompt enthält R-Multiple (`-1.25`) + `TIME_STOP`
  + Kontext-Key + ehrliches `volume_z_score: n/a`; alle Fehlerpfade (fehlender/leerer `lesson`-Key,
  non-dict, `LLMResponseError`, `RuntimeError`, `TimeoutError`) → `ok=False`/kein Raise; Metering-Pfad
  setzt `last_usage`; leerer `market_context` crasht nicht; `isinstance(brain, LessonExtractor)`.
- **`tests/conftest.py`** neu (erster P7-Fake): scripted `FakeLLM` (gespiegelt an P6 — `answers`,
  `last_usage`-Set pro Call, `raises_exc`, `seen_systems`/`seen_users`/`seen_schemas`) + lokaler
  `LLMResponseError`-Stand-in + Factories `make_closed`/`make_reward`/`market_context`.
- **Phasen-Isolation:** `import reward.brain` zieht **kein** `anthropic`/`research`/`broker_wrapper`/
  `execution`/`persistence` (laufzeit-geprüft → NONE). Import-Smoke `from reward import Brain,
  LessonExtractor` OK. **Sibling-Suiten grün + unberührt** (Step 7 fasst nur `phase7_reward/` an):
  **P2 59 · P4 88 · P5 135 · P6 70**.

### Next — **Step 8** (`reward/recorder.py` — die Orchestrierung, Decision A/J)
- `class RewardSink(db, broker, scorer, brain, confidence_provider, cfg)` (erfüllt das in Step 10 zu
  definierende `RewardSink`-Protocol). `on_trade_opened(opened)` → `db.insert_trade(OPEN-Record inkl.
  gate_path, research_confidence, initial_risk, account, session_date, intended levels)`. `on_trade_closed(closed)`
  → 1) `pnl_resolver.resolve` (Step 9), 2) `db.update_trade_close`, 3) `score_before = get_current_score()`
  + `scorer.score`, 4) `db.insert_reward`, 5) `brain.reflect` best-effort → `db.insert_lesson`. **JEDER
  Schritt einzeln gekapselt; Fehler → `logger.critical` + weiter (J)**; idempotenz via `deal_id` (zweites
  `on_trade_closed` verdoppelt den Score nicht). ⚠ Step 8 braucht `pnl_resolver` (Step 9) — Reihenfolge
  prüfen: ggf. 9 vor 8 bauen oder den Resolver in Step 8 injizieren/stubben (TDD).

### Gotchas (für den Re-Entry)
- Branch **`phase7-reward`**. `pytest phase7_reward/tests -v` läuft direkt (editable-install).
- **AI-Grenze gewahrt:** `Brain` extrahiert **nur Sprache → Erkenntnis** — kein Score, keine Zahl. Wer
  hier den LLM scoren/gaten lassen will → **stop** (das ist Code, Steps 4/5/8).
- **Metering ist transitiv** (über `client.last_usage`) — wer in Step 8/13 ein zweites `token_meter`
  einbaut, zählt doppelt. Der Brain-Timeout = der Transport-`timeout_s` des Clients (Wiring setzt ihn
  aus `lesson_timeout_s`); kein separater Threading-Timeout.
- `FakeLLM`/`LLMResponseError` liegen in `tests/conftest.py` (direkt importierbar:
  `from tests.conftest import FakeLLM, LLMResponseError`); Brain fängt `Exception` breit → Tests müssen
  die echte P4-Exception **nicht** importieren.

---

## Session stopped — 2026-06-19 (Step 6 — `reward/synthetic.py` synthetic/live separation)

### Completed
- **`reward/synthetic.py`** (pure deterministic Library — **kein DB-Write, kein Netz, kein LLM**;
  Decision H). Drei Teile:
  - **`SyntheticTradeGenerator(seed)`** → `generate(n, *, win_rate, win_r=1.5, loss_r=-1.0, jitter=0,
    account="synthetic") -> list[SyntheticTrade]`. Reproduzierbar via `random.Random(seed)`; jeder
    Trade `synthetic=True`; `win_loss` aus dem **finalen** R-Vorzeichen. `edge_inputs(trades)`
    (staticmethod) → `(r_multiples, wins, n)` direkt für `compute_confidence`.
  - **`guard_synthetic_path(target, cfg) -> str`** = DIE Grenze. Resolved `target` und
    `cfg.live_db_path` via `Path.resolve()` und wirft `SyntheticSafetyError`, wenn sie dieselbe Datei
    sind (fängt Relativ-vs-Absolut-Aliasing). Jeder synthetische Schreiber ruft das **vor** dem Öffnen
    einer DB → strukturell unmöglich, Synthetik in die Live-DB zu schreiben. (Konzept §7 (c)-Beweis.)
  - **`select_edge_set(records, cfg) -> (r_multiples, wins, n)`** = die `include_demo_in_edge`-Regel:
    `synthetic`-getaggte raus (immer), `account=='demo'` raus außer `include_demo_in_edge`, `'live'`
    immer rein. Nimmt `SyntheticTrade` **oder** Mapping-Rows (forward-compat für den DB-Provider in
    Step 8). `wins` = strikt positive R (Breakeven ist **kein** Win).
- **`reward/models.py`** ergänzt um **`SyntheticSafetyError(RewardError)`** (`code="SYNTHETIC_SAFETY"`,
  Class-Attr-Muster wie P5/P6). ⚠ Step-6-Erweiterung der Exception-Liste (Konzept §6 Step 3 nannte nur
  `RewardError`/`PnLUnavailable`) — im models-Docstring annotiert.
- **`reward/__init__.py`** exportiert jetzt zusätzlich `SyntheticTrade`, `SyntheticTradeGenerator`,
  `guard_synthetic_path`, `select_edge_set`, `SyntheticSafetyError`.
- **Arbeitsteilung (gepinnt, Konzept §Step 13):** der **echte** Synthetik-DB-*Schreiber* ist das
  Step-13-Operator-CLI `backfill_synthetic.py` (schreibt NUR `synthetic_db_path`, bricht ab bei ==
  `live_db_path`) — es **konsumiert** `guard_synthetic_path`. Step 6 bleibt deshalb **pure Library**
  (wie `confidence.py`/`scorer.py`) und hängt **nicht** an den `account`/`r_multiple`-Spalten, die
  erst Migration 002 (Step 12) bringt.

### Verifiziert (gemockt — kein Netz, kein LLM)
- `pytest phase7_reward/tests -v` → **80 passed** (69 + **11 neue Synthetik-Fälle**, Ziel ≥8). Inkl.
  Generator-Determinismus (gleicher Seed → identische R), `win_rate≈wins/n`, **Guard wirft auf dem
  Live-Pfad** + Aliasing-Beweis (relativ vs. absolut), Edge-Selector schließt Synthetik **immer** aus
  und togglet Demo via `include_demo_in_edge`.
- Import-Smoke: `from reward import SyntheticTradeGenerator, guard_synthetic_path, select_edge_set,
  SyntheticSafetyError` OK; `guard_synthetic_path(cfg.live_db_path, cfg)` wirft (`code=SYNTHETIC_SAFETY`);
  gen(12)→`compute_confidence` = `OK`. **Sibling-Suiten grün + unberührt** (Step 6 fasst nur
  `phase7_reward/` an): **P2 59 · P4 88 · P5 135 · P6 70**.

### Next — **Step 7** (`reward/brain.py` — Lesson-Extraktion, EIN Haiku-Call, best-effort) **[→ Opus]**
- `class Brain(llm_client, token_meter, cfg)` mit `reflect(closed, outcome, market_context) ->
  LessonResult`. **Reuse** `research.LLMClient` + `research.token_meter` (Decision F; `lesson_model=
  "claude-haiku-4-5-20251001"`, eigener Timeout `lesson_timeout_s`). **Best-effort/fail-closed (J):**
  jede Exception (Malformed-JSON/Timeout/…) → `LessonResult(ok=False, error=…)`, **kein Re-raise, kein
  Crash**. Swappbares `LessonExtractor`-Protokoll (Batch/Scheduler später). **≥8 Tests mit FakeLLM**
  (valide Lesson → korrekter `trade_lessons`-Record-Shape; Fehlerpfade → `ok=False`; `token_meter`
  additiv; Prompt enthält R-Multiple + Status + market_context). **Erstes AI-Modul der Phase** —
  AI-Grenze: Brain extrahiert **nur Sprache → Erkenntnis**, **keine** Zahlen/Score-Entscheidung.

### Gotchas (für den Re-Entry)
- Branch **`phase7-reward`**. `pytest phase7_reward/tests -v` läuft direkt (editable-install).
- **Decision-Treue:** Grenze Synthetik↔Live ist der **DB-Pfad** (`guard_synthetic_path`), nicht nur das
  Flag; `synthetic=True` ist Defense-in-Depth. Synthetik fließt **nie** in die Edge-Metrik.
- Step 6 schreibt **bewusst keine** DB — der Schreiber ist Step 13. Wer hier `Database(...)` öffnet,
  greift Step 13/12 vor (account/r_multiple-Spalten fehlen noch).
- `synthetic.py` ist stdlib-only (`random`/`pathlib`); kein numpy, keine echte LLM-/DB-Abhängigkeit.

---

## Session stopped — 2026-06-18 (Step 5 — `reward/scorer.py` ★ process-aware scoring)

### Completed
- **`reward/scorer.py`** (pure deterministic math — **kein I/O, kein Netz, kein LLM**): `class
  Scorer(cfg)` mit `score(*, r_multiple, status, spread_at_entry_pct, debate_confidence,
  score_before) -> RewardResult`. Prozess-bewusstes Delta (Decision B2/D):
  - `outcome_delta = outcome_weight · clip(r_multiple, ±r_clip) · asym` mit `asym=loss_asymmetry`
    nur auf Verlusten (`clipped_r < 0`), sonst `1.0`.
  - `process_delta = process_weight · (exit + entry + debate)`, **unabhängig** vom Outcome:
    `exit = +clean_exit_bonus` (`CLOSED_BY_BROKER`) / `−clean_exit_bonus` (`TIME_STOP`) / `0` sonst;
    `entry = +clean_exit_bonus` wenn `spread_at_entry_pct ≤ tight_spread_pct`; `debate =
    (debate_confidence − 0.5)` bzw. `0` bei `None`.
  - `total = clamp(outcome+process, ±max_delta_per_trade)`; `score_after = clamp(score_before+total,
    score_min, score_max)`; `win_loss` aus `r_multiple` (>0 WIN / <0 LOSS / =0 BREAKEVEN);
    `RewardResult.r_multiple` trägt den **rohen** (ungeclippten) Wert.
- **Zwei bewusste v1-Modellierungs-Entscheidungen** (im Modul-Docstring dokumentiert, weil §5 dafür
  **keinen** eigenen Knopf hat — Magnituden sind v1/tunbar, Decision D; nur die *relativen*
  Eigenschaften sind load-bearing, wie beim Confidence-Combiner): (1) der **Clean-Entry**-Bonus
  reused `clean_exit_bonus` als Prozess-Einheit; (2) das **Debate**-Signal ist `(conf − 0.5)` — max.
  ±0.5 einer Einheit, also schwächer als die ±1-Einheit-Exit/Entry-Signale ⇒ „schwaches Prozess-
  Signal, **kein** Multiplikator" (Konzept §6 Step 5), additiv und zentriert auf 0.5.
- **`reward/__init__.py`** exportiert jetzt zusätzlich `Scorer` (Helper-Klasse bleibt auch unter
  `reward.scorer` importierbar).

### Verifiziert (gemockt — kein Netz, kein LLM)
- `pytest phase7_reward/tests -v` → **69 passed** (21 Step-3 + 30 Step-4 + **18 neue Scorer-Fälle**,
  Ziel war ≥12). Inkl. der geforderten Beweis-Tests: guter Outcome/sauberer Prozess **>** guter
  Outcome/schlechter Prozess (gleiches R); Pech-Verlust am geplanten SL **>** sloppy-Verlust; `process_delta`
  bewegt den Score bei `r_multiple=0` **unabhängig** vom Outcome; Clamping (Score nie <0/>100,
  `|delta|`≤Cap); Symmetrie bei `loss_asymmetry=1.0`; R-Clip saturiert; Debate schwach + kein
  Multiplikator (`outcome_delta` unverändert).
- Import-Smoke gegen die Editable-Install: `from reward import Scorer` OK (clean 55.0 vs drift 50.5
  bei identischem +1R → prozess-bewusst). **Sibling-Suiten grün + unberührt** (Step 5 fasst nur
  Dateien in `phase7_reward/` + `__init__.py` an): **P2 59 · P4 88 · P5 135 · P6 70**.
- **Keyring-Preflight (Operator-autorisiert, read-only, nach Maschinen-Migration):**
  `store_credential.py --status` → **alle 4 `ig_demo_*` ✓, alle 4 Live-`ig_*` ✗** (erwartet — Live ist
  bewusst ungeseedet), `anthropic_api_key` **✓** (für Step 7 Brain). **Secret-Service-Backend hat die
  Migration überlebt; keine Neukonfiguration nötig** für Demo/Dev.

### Next — **Step 6** (`reward/synthetic.py` + harte Synthetik/Echt-Trennung, Decision H) **[→ Opus]**
- `SyntheticTradeGenerator`: klar gelabelte R-Multiple-Verteilungen (`synthetic=True`) für Confidence/
  Scorer-Mathe-Tests. **Harte Orts-Trennung:** jeder synthetische Schreiber zielt **immer** auf
  `synthetic_db_path` (Pfad-Guard — **nie** `live_db_path`); Demo-Trades laufen normal in `live_db_path`,
  getaggt `account='demo'`, gesteuert via `include_demo_in_edge`. **≥8 Tests:** ein `synthetic=True`-
  Schreibvorgang trifft den Live-Pfad **niemals** (Pfad-Guard ist die Grenze, nicht nur ein Flag).
- Reihenfolge danach: Step 7 `brain.py` (Haiku `reflect()`, best-effort) **[→ Opus]**, dann 8–13.

### Gotchas (für den Re-Entry)
- Branch **`phase7-reward`**. `pytest phase7_reward/tests -v` läuft direkt (editable-install). Bei
  frischem venv: `bash scripts/dev_install.sh`.
- **Decision-Treue:** Score/Confidence gaten **nichts** (Decision C/D) — wer in Step 6+ eine Schwelle
  einbaut, die einen Trade/`risk_pct` beeinflusst → **stop**. `scorer.py` ist reine Mathe, stdlib-only.
- Die exakten Scorer-Magnituden sind **v1** (am echten Profit zu tunen); Tests pinnen *relative*
  Eigenschaften, nicht die konkreten Zahlen (außer wo die Arithmetik der Vertrag ist: Clamps, rohes R).

---

## Session stopped — 2026-06-18 (Step 4 — `reward/confidence.py` ★ pure confidence math)

### Completed
- **`reward/confidence.py`** (pure deterministic math — **kein I/O, kein Netz, kein LLM**):
  - `wilson_lower_bound(successes, n, z=1.96) -> float|None` — Wilson-Score-Lower-Bound;
    `n<=0 → None`; klein-N-stabil (1/1 ≈ 0.2065, **nicht** 1.0; 0 Wins → 0.0 als konservativer Floor).
  - `expectancy_r(r_multiples) -> float|None` — Mittel der R-Multiples; `[] → None`.
  - `system_quality_number(r_multiples) -> float|None` — `√N·mean/stdev` (Sample-stdev, ddof=1);
    `N<2` oder stdev==0 → None (Nebenmetrik).
  - `compute_confidence(r_multiples, wins, n, cfg) -> ConfidenceReport` — **N < cfg.n_min →
    `INSUFFICIENT`, `confidence_value=None`** (gatet nichts); sonst `OK` mit gebremstem v1-Combiner
    (`_combine_confidence`: 50/50 aus Wilson-LB ∈[0,1] und linear auf [0,1] gemapptem Expectancy via
    `r_clip`, → [0,100]). Sub-Metriken (`win_rate_raw`/`wilson_lb`/`expectancy_r`/`sqn`) **immer**
    befüllt, wenn berechenbar — **unabhängig** vom Gate (Logging-Größen). `n` aus dem Arg, **nicht**
    aus `len(r_multiples)` (Caller besitzt die Edge-Set-Auswahl, inkl. `include_demo_in_edge`).
- **`reward/__init__.py`** exportiert jetzt zusätzlich `compute_confidence` (Helper bleiben unter
  `reward.confidence` importierbar).

### Verifiziert (gemockt — kein Netz, kein LLM)
- `pytest phase7_reward/tests -v` → **51 passed** (21 Step-3 + **30 neue Confidence-Fälle**, Ziel war
  ≥14). Inkl. den geforderten Beweis-Tests: (a) **N=9 → INSUFFICIENT, `confidence_value=None`**;
  (b) **Anti-Pattern: 1/1 = 100 % naive Rate ist NICHT die Confidence** (INSUFFICIENT); Wilson gegen
  Lehrbuchwerte (7/10≈0.3968, 10/10≈0.7225, 0/10=0.0), Monotonie, LB ≤ Raw-Rate, SQN-Edge-Cases.
- Import-Smoke gegen die Editable-Install: `from reward import compute_confidence` OK; 1/1 →
  `INSUFFICIENT`/`None`, 6/10 → `OK`/conf≈43.30. Sibling-Suiten unberührt (Step 4 fasst nur Dateien
  in `phase7_reward/` an + `__init__.py`).

### Next — **Step 5** (`reward/scorer.py` ★ — Decision B2/D, ebenfalls reine Mathe, kein I/O)
- `class Scorer(cfg)` mit `score(*, r_multiple, status, spread_at_entry_pct, debate_confidence,
  score_before) -> RewardResult`. **Prozess-bewusstes Delta:** `outcome_delta` = `outcome_weight ·
  clip(r_multiple, ±r_clip)` (mit `loss_asymmetry` auf Verluste); `process_delta` **unabhängig** vom
  Outcome (+`clean_exit_bonus` bei `CLOSED_BY_BROKER`, Abzug bei `TIME_STOP`, +Bonus bei
  `spread_at_entry_pct ≤ tight_spread_pct`; `debate_confidence` nur schwaches Prozess-Signal, **kein**
  Multiplikator). `gesamt = clamp(outcome+process, ±max_delta_per_trade)`; `score_after =
  clamp(score_before+gesamt, score_min, score_max)`; `win_loss` aus `r_multiple`. **≥12 Tests:**
  guter Outcome/schlechter Prozess < guter Outcome/sauberer Prozess; Pech-Verlust am SL < sloppy-
  Verlust; Clamping (nie <0/>100, `|delta|`≤Cap); Symmetrie bei `loss_asymmetry=1.0`; `process_delta`
  differenziert (Anti-Outcome-only). Exportiert `Scorer` aus `reward/__init__.py`.

### Gotchas (für den Re-Entry)
- Branch **`phase7-reward`**. `pytest phase7_reward/tests -v` läuft direkt (editable-install). Bei
  frischem venv: `bash scripts/dev_install.sh`.
- **Decision-Treue:** `confidence` gatet **nichts** — wer in Step 5+ eine Confidence-Schwelle einbaut
  → **stop**. Der v1-Combiner ist observe-only; seine exakte Form ist **nicht** load-bearing — was
  zählt, ist das `INSUFFICIENT`-Gate + die Sub-Metriken (so dokumentiert).
- `confidence.py` ist **stdlib-only** (`math`/`statistics`) — bewusst kein numpy (no-extra-deps-Grain).

---

## Session stopped — 2026-06-18 (Step 3 — `reward/models.py` data contracts)

### Completed
- **`reward/models.py`** (types only, keine Logik): frozen Dataclasses `OpenedTrade`, `ClosedTrade`,
  `ConfidenceReport`, `RewardResult`, `LessonResult`, `RewardConfig` (alle §5-Defaults) + Exceptions
  `RewardError` → `PnLUnavailable` (`code`-Class-Attr-Muster wie P5/P6). Feldsätze exakt aus Konzept
  §6 Step 3 / §5. `initial_risk`-Formel im Feld-Docstring dokumentiert (`abs(intended_open_level −
  stop_level) · size · point_value`) — der **Wert** wird vom Caller zur Open-Zeit berechnet (Step 10),
  die Dataclass trägt ihn nur.
- **⚠ Bewusste Konzept-Abweichung (Code = Source of Truth):** `RewardConfig.live_db_path` defaultet
  auf den **echten** P2-Pfad `"data/trading_bot.sqlite"` (P2-`CLAUDE.md`/`init_db.py`), **nicht** auf
  den Konzept-§5-String `"data/trading_bot.db"`. Konzept §5 mit dateierter Notiz annotiert.
- **`reward/__init__.py`** re-exportiert jetzt die Step-3-Typen (`RewardConfig`, die 5 Dataclasses,
  `RewardError`/`PnLUnavailable`) + `__all__` (wie P4/P6 ihr `__init__` pro Modul wachsen ließen).
- **Tests** `tests/{__init__,test_models,test_packaging}.py` — **21 Tests grün**: §5-Defaults (inkl.
  korrigierter `live_db_path`), Construct/Read-back, `FrozenInstanceError`, `ConfidenceReport`-
  INSUFFICIENT trägt `confidence_value=None`, `LessonResult` ok/error-Form, Exception-Hierarchie +
  distinkte Codes (`PnLUnavailable` als `RewardError` fangbar), Editable-Install-Smoke (`import reward`).

### Verifiziert (gemockt — kein Netz, kein LLM)
- `phase1_broker_wrapper/.venv/bin/python -m pip install -e phase7_reward` (P7 erstmals editable in den
  Projekt-venv, in dem P1–P6 schon installiert sind), dann `pytest phase7_reward/tests -v` → **21 passed**.
- `py_compile` der 4 Dateien OK; Hygiene-grep (`CALL`/`PUT`/`strike`/`otm`/`issuer`/`FLIP`/`turbo`/
  `option_check`) **clean**. Sibling-Suiten unberührt (Step 3 fasst nur Dateien in `phase7_reward/` an).

### Next — **Step 4** (`reward/confidence.py` ★ — reine Mathe, höchste Test-Priorität)
- `wilson_lower_bound(successes, n, z=1.96) -> float|None` (n==0 → None), `expectancy_r(r_multiples)
  -> float|None` ([] → None), `system_quality_number(r_multiples) -> float|None` (N<2 / stdev==0 →
  None), `compute_confidence(r_multiples, wins, n, cfg) -> ConfidenceReport` (N<n_min → INSUFFICIENT,
  `confidence_value=None`; sonst bounded combiner). **≥14 Tests** inkl. Anti-Pattern-Beweis (naive
  1/1=100 % ist NICHT die Confidence) + Monotonie. Kein I/O, deterministisch. Exportiert
  `compute_confidence` aus `reward/__init__.py`.

### Gotchas (für den Re-Entry)
- Branch **`phase7-reward`**. P7 ist jetzt **editable-installiert** in `phase1_broker_wrapper/.venv`
  (`reward 0.1.0`) → `pytest phase7_reward/tests -v` läuft direkt. Bei frischem venv: `bash
  scripts/dev_install.sh`.
- `models.py` ist **types-only** — `compute_confidence`/`Scorer`/`Brain`/`RewardSink` kommen erst in
  Steps 4/5/7/10; bis dahin bleiben sie aus `__all__` raus.
- `ConfidenceReport`-Optionals (`win_rate_*`/`expectancy_r`/`sqn`/`confidence_value`) sind `float|None`
  — Step 4 füllt sie für den OK-Fall, lässt sie für n=0 / INSUFFICIENT auf `None`.

---

## Session stopped — 2026-06-18 (Step 1 — Pre-Steps: Housekeeping + Verify + Scaffold)

### Completed
- **Step 0 (Turbo-Cleanup):** dokumentierter No-Op (s. o.) — nur frozen `turbo_candidates.json`.
- **Step 0b (Doku-Reconciliation):** `ROADMAP.md` Phase 7 auf das schlanke Modell geflippt +
  `longterm_pre_trade_check() VETO` → neues **Phase 9f**; Root-`CLAUDE.md` „Current state" → Phase 7
  (kanonische Aussage + Phase-7-Status-Block). Kein Instinct→VETO-Framing mehr in der Doku.
- **Step 1 (Verify-against-code):** 7 Verträge gegen Live-Code gepinnt (s. `## Verifizierte
  Contracts`), inkl. drei ⚠-Befunde, die spätere Build-Steps formen:
  (1.1) `get_trade_history` hat **kein** deal_id → `pnl_resolver`-Match heuristisch + Level-Fallback
  Pflicht (Step 9); (1.2/1.3) `place_order` droppt den Fill-`level` + Executor hält `outcome` nicht →
  `open_level`/`debate_confidence` zur Open-Zeit aus `price_env`/in-memory-Outcome fangen (Step 10);
  (1.7) **keine `account`-Spalte** → Migration-002-Scope-Entscheidung (Step 12) + DB-Pfad-Diskrepanz
  (Konzept `…/trading_bot.db` vs. echter `…/trading_bot.sqlite`, Step 13).
- **Step 2 (Scaffold):** `phase7_reward/` angelegt — `pyproject.toml` (pkg `reward`),
  `requirements.txt` (dev `pytest`, anthropic via `research`-Reuse), `README.md`, diese `CLAUDE.md`,
  `reward/__init__.py` (leer). `scripts/dev_install.sh` um `phase7_reward` (nach `phase6_debate`)
  erweitert (P1→…→P7). **Keine Reward-Logik, keine Tests** — das ist bewusst Steps 3–13.

### Verifiziert (gemockt / read-only — Live/Netz-Tests macht der Operator)
- `python -c "import ast; ast.parse(...)"` auf `reward/__init__.py` OK (import-clean, keine Logik).
- `rg -i "instinct|ECC|promote" --type md` → kein Instinct→VETO-Framing mehr; ROADMAP trägt keinen
  Phase-7-VETO-Punkt mehr. `rg -i turbo` unverändert außer Doku (keine neue Turbo-Ref durch P7).
- Bestands-Suiten unberührt (dieser Step schreibt **keine** Logik): P6 70 · P5 135 · P4 88 · P2 59.

### Next — **Step 3** (`reward/models.py`, nur Typen, keine Logik) — Beginn der Reward-Logik (TDD)
- `OpenedTrade` (am Open bekannt): `deal_reference, deal_id, epic, direction, size,
  intended_open_level, stop_level, limit_level, currency, initial_risk, research_confidence,
  debate_confidence|None, gate_path(dict), spread_at_entry_pct, score_at_open, session_date, open_ts,
  account("demo"|"live")`. `ClosedTrade`: `deal_reference, deal_id, status("CLOSED_BY_BROKER"|
  "TIME_STOP"), closed_at`. `ConfidenceReport`/`RewardResult`/`LessonResult`/`RewardConfig` (§5) +
  Exceptions `RewardError`/`PnLUnavailable`. `initial_risk = abs(intended_open_level − stop_level) ·
  size · point_value` dokumentieren. Danach **Step 4** `confidence.py` ★ (Wilson/Expectancy/SQN/
  N_min, ≥14 Tests) — höchste Test-Priorität.
- **Vor Step 9/10/12 die ⚠-Befunde 1.1/1.2/1.3/1.7 heranziehen** (sie sind der Grund, warum die
  naive Konzept-Formulierung dort nicht 1:1 baubar ist).

### Offene Punkte / [VERIFY] (für spätere Steps, jetzt nur dokumentiert)
- **Step 12:** ✅ entschieden (Operator 2026-06-18) — Migration 002 fügt `initial_risk` + `r_multiple`
  **+ `account TEXT`** hinzu; `_TRADE_COLUMNS += ("initial_risk", "account")`,
  `_REWARD_COLUMNS += ("r_multiple",)`. Idempotenz über die Versions-Tabelle (s. 1.7).
- **Step 13:** echter P2-DB-Pfad `data/trading_bot.sqlite` (nicht Konzept-`…/trading_bot.db`).
- **Step 9:** `pnl_resolver` ohne deal_id — Match-Heuristik + Level-Fallback (defensiv, `[VERIFY]`
  gegen einen echten geschlossenen Demo-Deal beim Operator-Live-Test).

### Gotchas (für den Re-Entry)
- Branch **`phase7-reward`** (abgezweigt von `phase6-debate`/`d306806`). Dieser Step = **Doku +
  Scaffold** (kein Logik-Code, keine Tests), committet als ein atomarer Commit (SHA via `git log`).
  Merge → `main` bleibt Operator-Entscheidung. Der `reward`-Editable-Install greift erst **nach**
  `bash scripts/dev_install.sh` (Operator).
- AI-Grenze einhalten: nur `reflect()` ist AI. Confidence/Scorer/pnl_resolver sind **reine** Mathe/
  Code — kein LLM, keine Heuristik-Halluzination.
- Decision-Treue: `confidence` gatet **nichts**, `reward_sink` default `None` muss P5 bit-identisch
  lassen, alle Writes fail-closed (`logger.critical`, nie in den Close-Pfad werfen).
