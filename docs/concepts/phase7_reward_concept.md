# Phase 7 — Reward/Brain — Detaillierter Claude-Code-Plan

> **Quelle der Wahrheit = Repo-Code.** Dieser Plan wurde am 2026-06-16 gegen den **Live-Code auf
> Google Drive** (Repo-Stand nach P6-Merge `main = 49cda8a`) verifiziert, nicht gegen Konzepte.
> Verifizierte Verträge stehen in §3. Was *nicht* gepinnt werden konnte, ist als `[VERIFY]`
> markiert und gehört in **Step 1** (billige greps, bevor Code entsteht).
>
> **Vorgehen:** strikt TDD, gemockt (kein Netz / kein echter LLM in Unit-Tests). CLAUDE.md-Skelett
> als **erste** Aktion. Kein Subtask „done" ohne grünes `pytest`. Atomic commits. **Hard Rule
> „Commit ⇒ Note-Update":** jeder Abschluss-Commit aktualisiert im selben Commit Status-Tabelle +
> `## Session stopped`.
>
> **Modell-Empfehlung:** Standard-Implementierung mit dem üblichen Modell; die mit **→ Opus**
> markierten Steps (7-Brain, 6-Synthetik-Trennung) mit Opus fahren — dort liegt die eigentliche
> Komplexität/Risiko (Prompt-+Test-Qualität der Lesson-Extraktion; Korrektheit der Synthetik/Echt-
> Trennung ist metrik-/ehrlichkeits-kritisch).

> **⚠ Revision 2026-06-16-b — ECC-Scope-Lock (Erkenntnis aus Memory-Abgleich).** Eine ältere Notiz
> beschrieb „ECC-Pattern" als **Instinct-Promotion** (AI schlägt Instincts mit trigger/domain/evidence
> vor → Code validiert → Promote zu **VETO**). Das ist **NICHT** Phase 7. P7 baut bewusst das
> **schlanke** Modell: **Reward-Score + Freitext-Lessons + observe-only Confidence**, **ohne**
> VETO-Berührung. Begründung: das echte P2-Schema (`reward_pts` + `trade_lessons`, kein Instinct-
> Schema) und der Architektur-Doc stützen reward+lessons; und eine AI-getriebene Promotion auf **null
> validierten Outcomes** würde Risiko zurück in die Safety-Schicht importieren. Die **volle
> Instinct-Umsetzung** ist ein **separater, späterer Step** → §7b.

---

## 0. Gelockte Architekturentscheidungen (vom Advisor-Chat bestätigt)

| # | Entscheidung | Kern |
|---|---|---|
| **Step 0** | Turbo-Cleanup | grep, nur `turbo_candidates.json` (frozen) + Referenzen bleiben; Rest in P7-Touch bereinigen; sonst dokumentierter No-Op. |
| **A** | Write-Seam | Optionaler, duck-typed `reward_sink` (Protocol), default `None` → **P5 bit-identisch**. **Zwei** Methoden: `on_trade_opened` (Decision-Kontext) + `on_trade_closed` (Outcome+Reward+Lesson). Spiegelt exakt das bestehende `debate_runner`-Muster. |
| **B** | Scoring | **Prozess-bewusst ab Tag 1 (B2)**, nicht outcome-only. Score-Delta = gebremste Outcome-Komponente **+** Prozess-Komponente aus realen Signalen. |
| **C** | Confidence | `f(Wilson-Lower-Bound(win_rate), expectancy_R, N)`; **N < N_min=10 → INSUFFICIENT (fließt in nichts)**. SQN als Nebenmetrik. **v1 observe-only** — gatet keine Order, moduliert (noch) **nicht** `risk_pct`. |
| **D** | Feedback-Stabilität | Binäres `get_risk_level` (Schwelle 50) **unverändert**; P7 schreibt nur `score_after`. Score auf **[0,100]** clampen, Per-Trade-`|delta|` ≤ Config-Cap, konservativ, am echten Profit getunt. |
| **E** | Lesson-Extraktion | **Vom Close-Critical-Path entkoppelt:** Reward atomar schreiben, dann best-effort `reflect()`. Ein Haiku-Call, swappbare Schnittstelle (Batch/Scheduler später). **Intensiv getestet → Opus.** |
| **F** | Reuse | `research.LLMClient`, `research.token_meter` (8-Feld), `credentials`-Shim wiederverwenden. Kein zweites Mess-System. |
| **G** | Ownership/Migration | P7 besitzt `trade_outcomes`-Writes über **P2-CRUD** (existiert, getestet). **Eine** minimale P2-Berührung: Whitelist-Tuples + Migration `002` für `initial_risk`/`r_multiple`. |
| **H** | Bootstrap | Produktion **fail-safe-neutral** bis echte Outcomes. **Hart getrennte Orte** Synthetik vs. Echt (separater DB-Pfad + Tag), eigene Steps. **→ Opus.** |
| **I** | Loop-Closure | **In dieser Phase:** Lessons schreiben **+** sicherstellen, dass P4-Research sie via `get_recent_lessons` in den Prompt zieht (verifizieren, sonst verdrahten). |
| **J** | Fail-closed Writes | Alle P7-Writes best-effort, werfen nie in den P5-Close-Pfad. Fehlschlag ⇒ **`logger.critical`** (kein `error` — die Lernlogik hebt sich bewusst ab), idempotenter Retry via `deal_id`. |

---

## 1. Verify-against-code (Step 1, vor jedem Code — billige greps)

Alles in §3 ist bereits gepinnt. Diese Punkte konnte der Plan **nicht** final pinnen — Claude Code
grep't sie zuerst und trägt die echten Shapes in CLAUDE.md ein:

1. **`get_trade_history`-Record-Shape** in `broker_wrapper/adapters/ig_adapter.py`: welche Felder pro
   geschlossener Transaktion (Match-Key auf `deal_id`/`deal_reference`? `profit_loss`/`profitAndLoss`,
   `open_level`, `close_level`, `size`, `date`, `currency`?). → bestimmt, wie P7 P&L+Levels auflöst.
2. **`OrderPlan`-Felder** (`execution/models.py`) und **`OrderResult`/`place_order`-Return**
   (`execution/order.py`): exakter Status-Enum (`OPEN`/…), `deal_id`-Feld, ob ein Entry-Fill-Level
   geliefert wird (`level`/`open_level`). → für `on_trade_opened`-Payload.
3. **Debate-Outcome-Shape** (`debate/…`) + `data/state/debate_log.json`-Record: liefert der Judge
   `.confidence`, `.decision`, `.direction`, `.rationale`? Wie korreliert ein Log-Eintrag mit dem
   späteren Trade (gemeinsame Zyklus-ID / `deal_reference` / Timestamp)? → für `debate_confidence`.
4. **`research.LLMClient`** öffentliche Methode(n) + Signatur (single-shot Pfad) und
   **`research.token_meter`**-Record-Funktion (8-Feld, cache-aware). → für Reuse (F).
5. **`research/context_builder.py` + `research/prompt.py`:** zieht der Research-Prompt **heute schon**
   `db.get_recent_lessons(...)`? → entscheidet, ob Loop-Closure (I) reines Schreiben ist oder eine
   kleine P4-Prompt-Erweiterung braucht.
6. **Aktuelle Modell-Strings** in `research`-Config (P4 nutzte `claude-sonnet-4-20250514`; P6
   `claude-haiku-4-5-20251001` / `claude-sonnet-4-6`). P7-Lesson-Default = **`claude-haiku-4-5-20251001`**.
7. **`execution/protocols.py`** (`BrokerProtocol`/`DbProtocol`/`StateProtocol`): Stilvorlage für das
   neue `RewardSink`-Protocol.

Ergebnis in `phase7_reward/CLAUDE.md` unter `## Verifizierte Contracts` festhalten.

---

## 2. Step 0 — Turbo-Cleanup

```
rg -i "turbo" --type py --type sql --type md
```
- Einzig legitime Treffer: **`turbo_candidates.json`** (frozen Contract: P2-`state.py`, P5-Gate 2,
  `seed_candidate.py`) + dessen dokumentierte Referenzen. **Nicht** umbenennen.
- Alles andere in von P7 erstelltem/berührtem Code (neues `phase7_reward/`-Paket) vermeiden.
- Wenn außerhalb des Frozen-Filenames nichts auftaucht → **dokumentierter No-Op** in CLAUDE.md
  (`Step 0: grep clean, nur frozen turbo_candidates.json — kein Cleanup nötig`).

---

## 2b. Step 0b — Codebase-Doku-Reconciliation (NEU — direkt nach Step 0, vor Step 1)

> Zweck: **Web-Doku == Codebase-Doku.** Die Web-Planungsdokumente werden parallel korrigiert
> (ECC-Scope-Lock); damit die im Repo eingecheckte Doku nicht denselben veralteten/widersprüchlichen
> Stand trägt, gleicht Claude Code die `.md`-Files der Codebase an — **bis ins oberste `.md`-File,
> wenn nötig.**

```
rg -i "instinct|ECC|promote|reward.?punishment|reflect|outcome.anchored" --type md
```
- **Kanonische Aussage, gegen die abgeglichen wird** (überall identisch formulieren):
  *„Phase 7 = Reward-Score (`reward_pts`, prozess-bewusst) + Freitext-Lessons (`trade_lessons`) +
  observe-only outcome-anchored Confidence. Keine VETO-Berührung. Die volle Instinct-Promotion-ECC
  ist ein separater, späterer Step (P9), gated auf reale Outcomes."*
- **Zu prüfende/anzugleichende Files** (Treffer reconcilen, nicht blind löschen):
  - **oberstes Repo-`README.md` / `ROADMAP.md`** (falls vorhanden) — Build-Order/ECC-Framing.
  - **per-Phase `CLAUDE.md`** (v.a. P2 — beschreibt die Tabellen; P6 — `debate_log`-Vorwärtskompat).
  - **`docs/architecture/tradingbot_v2_architecture.*`** — der Architektur-Doc zeigt bereits
    `reward_pts`+`trade_lessons`+`reflect()` (= reward+lessons, **konsistent**); nur sicherstellen,
    dass **kein** Instinct→VETO-Pfeil/Label das schlanke Modell überschreibt. Ändern **nur** falls
    ein Instinct-Promotion-Label existiert.
  - alle `phase*_konzept.md` / Handover-Files, die „ECC"/„Reward/Punishment" erwähnen.
- **Wenn nichts Widersprüchliches gefunden** → dokumentierter No-Op in CLAUDE.md (analog Step 0).
- **Done-Kriterium:** `rg` zeigt keine Instinct-Promotion-/Instinct-→-VETO-Framing mehr in `.md`;
  jede P7-Erwähnung trägt die kanonische Aussage. Commit ⇒ Note-Update.

---

## 3. Verifizierte Contracts (gegen Live-Code 2026-06-16 gepinnt)

### `persistence.Database` — vollständig implementiert, getestet (P2, 59 Tests)
```python
# Writes existieren bereits — P7 RUFT sie, reimplementiert sie NICHT:
insert_trade(trade: dict) -> int          # setdefault status=OPEN, broker=ig, created/updated=now; json_fields=("gate_path",)
update_trade_close(deal_id: str, close_data: dict) -> bool
                                          # close_data: close_level, profit_loss, close_ts(→now), status(→CLOSED)
                                          # berechnet hold_duration_min aus open_ts→close_ts; False wenn deal_id unbekannt
insert_reward(trade_id: int, reward: dict) -> int     # setdefault calculated_at=now
insert_lesson(trade_id: int, lesson: dict) -> int     # json_fields=("market_context_json","embedding_json"); extracted_at=now
get_current_score() -> float              # latest reward_pts.score_after, sonst 50.0
get_risk_level() -> str                   # "AGGRESSIV" if score > 50.0 else "KONSERVATIV"  (strikt >; 50.0 → KONSERVATIV)
get_recent_trades(n=8) / get_recent_lessons(n=5) / get_trade_by_deal_id(deal_id) / get_open_trades()
mark_lesson_used(lesson_id) -> None       # used_in_research += 1, last_used_ts=now
```
- **`_REWARD_COLUMNS` enthält bereits**: `outcome_score_delta, score_after, win_loss, pnl_raw,
  process_score_delta, veto_trigger_count, gate_fail_count, debate_confidence, spread_at_entry_pct,
  calculated_at`. → **B2 (Prozess-Spalten schreiben) braucht KEINE Migration.**
- **`_TRADE_COLUMNS`/`_REWARD_COLUMNS` haben KEIN** `initial_risk`/`r_multiple` → Migration `002` +
  Whitelist-Erweiterung (Step 12).
  - ⟳ **2026-06-18 (Verify-against-code, Operator-Entscheidung):** `_TRADE_COLUMNS` hat **auch KEIN
    `account`** — aber `OpenedTrade.account ("demo"|"live")` (§6 Step 3) + die Demo-Edge-Query
    (`include_demo_in_edge`, §6 Step 6) brauchen ihn persistiert. Migration `002` fügt daher **auch
    `account TEXT`** hinzu, `_TRADE_COLUMNS += ("initial_risk", "account")` (s. Step 12). Sonst
    würde `_insert` den `account`-Key still verwerfen (Whitelist-Schnitt).
- `_insert` schneidet Record mit Whitelist → unbekannte Keys werden ignoriert (column-injection-safe).
- **Jede Write-Methode committet intern** → keine method-übergreifende Transaktion. Konsequenz: erst
  `update_trade_close` (Close-Fakt), dann `insert_reward` (Scoring). Scheitert der Reward-Insert, ist
  der Trade trotzdem korrekt geschlossen → idempotenter Retry via `deal_id` möglich (J).
- `_RISK_THRESHOLD = _DEFAULT_SCORE = 50.0`. **Kein Clamp in der DB** → P7 clampt `score_after` auf
  [0,100] **vor** dem Insert.

### `execution.ExecutionState` — operativ, NICHT anfassen
- JSON `data/state/execution_state.json`, keyed by `deal_reference`. Record:
  `{deal_reference, epic, direction, size, stop_level, limit_level, status(PENDING/OPEN/CLOSED),
  deal_id, recorded_at, updated_at}`. Methoden: `record_pending(plan)`, `mark_open(ref, deal_id)`,
  `mark_closed(ref)`, `open_references()`, `get(ref) -> dict|None`.
- Docstring **explizit**: „not a learning/outcome store (that is Phase 7's SQLite)". → P7 reichert es
  **nicht** an. Es liefert aber `stop_level`+`size` → initiales Risiko rekonstruierbar.

### `execution.monitor.monitor_position(...) -> ExecutionResult`
- Status `CLOSED_BY_BROKER` (Broker-SL/TP) oder `TIME_STOP`; trägt `deal_id`, `plan`, `detail`.
- **Trägt KEIN `profit_loss`/`close_level`.** → P7 löst P&L+Level über `broker.get_trade_history` auf.

### `execution.Executor` — die Naht (Decision A spiegelt `debate_runner`)
```python
Executor.__init__(broker, db, state, exec_state, config, research_runner, confirm_fn, *,
                  debate_runner=None, now_fn=datetime.now, sleep_fn=time.sleep)
```
- DI-Muster: optionale Kollaborateure default `None`, duck-typed, **nie importiert**.
- `run()`-Fluss: session → reconcile → Gate1 → Gate2(+lazy research) → **[debate seam]** → Gate3/5 →
  Gate4 sizing → VETOs → `build_order_plan` → human-confirm → `place_order` → `monitor_position`
  (**returnt direkt**).
- Im Scope zur Open-Zeit: `candidate` (epic, direction, llm_confidence, reasoning, score_at_pick…),
  `outcome` (Debate, falls vorhanden), `plan`, `place_result` (status OPEN, deal_id),
  `account_env`/`price_env`/`market_info_env`, `risk_pct`, `size`.

### `broker_wrapper.adapters.BrokerAdapter`
- **`get_trade_history(days: int = 30) -> Envelope`** — „Closed transactions within the last days days."
  **= autoritative realisierte-P&L-Quelle.** Außerdem: `get_account`, `get_open_positions`,
  `close_position(deal_id)`, `get_price`, `get_market_info`, `get_ohlcv`. Envelope: immer `.ok` vor `.data`.
- **⚠ Caveat (P1-`README` Z.174, wörtlich):** *„Trade-history parsing is best-effort. IG's transaction
  format varies by deal type; cross-check against a known closed deal."* → `pnl_resolver` (Step 9)
  muss defensiv sein, der Level-Fallback ist **nicht optional**, und `[VERIFY]` 1.1 (exakte
  Record-Shape) ist Pflicht **vor** dem Bauen.

### Migrations
- Nur `migrations/001_initial.sql` existiert → P7-Migration = **`002_phase7_reward.sql`** (additiv, idempotent).

---

## 4. Modul-Struktur (neues Paket `phase7_reward/`, Paketname `reward`)

```
phase7_reward/
├── README.md
├── CLAUDE.md                       # Skelett ZUERST (Step 2): Regeln, Decisions, AI-Grenze, Naht, ## Session stopped
├── requirements.txt                # anthropic SDK (via research-Reuse) — i.d.R. keine neue Dep
├── reward/
│   ├── __init__.py                 # exports: RewardSink, RewardConfig, compute_confidence, Scorer, Brain, OpenedTrade, ClosedTrade
│   ├── models.py                   # OpenedTrade, ClosedTrade, RewardConfig, ConfidenceReport, RewardResult, LessonResult; Exceptions
│   ├── confidence.py               # Wilson-LB + Expectancy(R) + SQN + N_min-Gating  (reine Mathe, deterministisch)
│   ├── scorer.py                   # Prozess-bewusstes Reward-Delta + Clamping (B2, D)  (deterministisch)
│   ├── pnl_resolver.py             # ClosedTrade → (close_level, profit_loss, r_multiple) via get_trade_history (+ Fallback)
│   ├── brain.py                    # reflect(): Lesson-Extraktion, Haiku, best-effort, swappbar (E)  [→ Opus]
│   ├── recorder.py                 # RewardSink-Impl: on_trade_opened/on_trade_closed orchestriert alles (A, J)
│   ├── synthetic.py                # SyntheticTradeGenerator + harte Synthetik/Echt-Trennung (H)  [→ Opus]
│   └── credentials.py              # dünner Shim → broker_wrapper.credentials.get_credential (anthropic_api_key)
├── migrations/
│   └── 002_phase7_reward.sql       # ADD COLUMN initial_risk / r_multiple  (Step 12)
├── scripts/
│   ├── wiring.py                   # baut RewardSink mit echten P1/P2/research-Instanzen; verdrahtet in Executor(reward_sink=…)
│   ├── backfill_synthetic.py       # Operator-Tool: schreibt NUR in separaten Synthetik-DB-Pfad (Guard gegen Live-DB)  [→ Opus]
│   ├── smoke_test.py               # ein echter Haiku-reflect()-Lauf, DRY (kein DB-Write)
│   └── live_test.py                # voller open→close→reward→lesson-Zyklus gegen IG-Demo (Operator), exit 0
└── tests/
    ├── conftest.py                 # FakeBroker(+get_trade_history), FakeDB, FakeLLM, FakeExecState, OpenedTrade/ClosedTrade-Factories
    ├── test_confidence.py          # ★ höchste Priorität: Wilson, Expectancy, SQN, N_min-Sentinel (≥14)
    ├── test_scorer.py              # ★ Prozess-vs-Outcome-Trennung, Clamping, Bounds (≥12)
    ├── test_pnl_resolver.py        # History-Match, R-Multiple, Fallback-Flag (≥8)
    ├── test_brain.py               # reflect() mit FakeLLM, best-effort-Fehlerpfad → critical-log, kein Crash (≥8)
    ├── test_recorder.py            # on_trade_opened/closed-Orchestrierung, fail-closed, idempotenz (≥10)
    ├── test_synthetic.py           # Synthetik/Echt-Trennung: Live-DB-Pfad wird NIE getroffen (≥8)
    └── test_executor_seam.py       # reward_sink=None → P5 bit-identisch; mit Sink → beide Callbacks gefeuert (≥6)
```

Repo-Konventionen: `from __future__ import annotations`, Type-Hints + Docstrings, eine Datei = eine
Verantwortung, eigene typisierte Exceptions, nie still schlucken, **Logging → stderr / stdout nur
maschinenlesbares JSON**, `pytest` ohne Netz/echtes LLM, atomic commits.

---

## 5. Config-Defaults (`RewardConfig` — v1, am echten Profit zu tunen, NICHT vorab optimieren)

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
| `lesson_model` | `"claude-haiku-4-5-20251001"` | E/F — `[VERIFY]` aktueller String |
| `lesson_max_tokens` | `400` | E — eine knappe Lesson |
| `lesson_temperature` | `0.3` | E |
| `lesson_timeout_s` | `20.0` | E — eigener Timeout, blockt den Close-Pfad nie hart |
| `include_demo_in_edge` | `True` *(Demo-/Bootstrap-Phase)* | H — Demo-Trades **SIND** die Datenquelle, bis Profitabilität absehbar ist → `True`, damit der Loop end-to-end läuft und die Confidence überhaupt aus `INSUFFICIENT` herauskommt. **Caveat (ehrlich):** Demo-Fills/Spreads ≠ Live → Demo-Confidence ist **nicht** live-edge-validiert. Demo bleibt `account='demo'`-getaggt → bei Go-Live re-baselinen/ausschließbar. |
| `live_db_path` | `"data/trading_bot.sqlite"` ⟳ | H — Live-Ziel. ⟳ **2026-06-18 (Step 3, Code = Source of Truth):** der echte P2-DB-Name ist `data/trading_bot.sqlite` (P2-`CLAUDE.md`/`scripts/init_db.py`), **nicht** `…/trading_bot.db` — `RewardConfig.live_db_path` defaultet auf den echten `.sqlite`-Pfad. |
| `synthetic_db_path` | `"data/synthetic_reward.db"` | H — Synthetik-Ziel (Backfill-Tool schreibt NUR hierhin) |

---

## 6. Build-Reihenfolge (strikt TDD — jede Stufe grün, bevor weiter)

> **Frühe Schritte (Reihenfolge):** Step 0 (Turbo-Cleanup, §2) → **Step 0b** (Codebase-Doku-
> Reconciliation, §2b) → Step 1 (Verify-against-code, §1) → **dann** der Build ab Step 2. Step 2
> (CLAUDE.md-Skelett) ist die erste **Build**-Aktion (Konvention), nach der Housekeeping-Phase.

### Step 2 — `CLAUDE.md`-Skelett (ERSTE Build-Aktion)
Modul-Baum (§4), gelockte Decisions (§0), AI-Grenze (AI **nur** Lesson-Extraktion), die Naht (`reward_sink`),
`## Verifizierte Contracts` (aus Step 1), `## Session stopped`. Wird laufend nachgezogen.

### Step 3 — `reward/models.py` (nur Typen, keine Logik)
- `OpenedTrade` (Decision-Kontext, am Open bekannt): `deal_reference, deal_id, epic, direction, size,
  intended_open_level, stop_level, limit_level, currency, initial_risk, research_confidence,
  debate_confidence|None, gate_path(dict), spread_at_entry_pct, score_at_open, session_date, open_ts, account`
  (`"demo"|"live"`).
- `ClosedTrade`: `deal_reference, deal_id, status("CLOSED_BY_BROKER"|"TIME_STOP"), closed_at`.
- `ConfidenceReport`: `state("OK"|"INSUFFICIENT"), n, win_rate_raw, win_rate_wilson_lb, expectancy_r,
  sqn|None, confidence_value|None`.
- `RewardResult`: `outcome_delta, process_delta, score_before, score_after, win_loss, r_multiple`.
- `LessonResult`: `lesson_text|None, market_context, ok(bool), error|None`.
- `RewardConfig` (§5). Exceptions: `RewardError`, `PnLUnavailable`.
- `initial_risk` Berechnung dokumentieren: `abs(intended_open_level - stop_level) * size * point_value`.

### Step 4 — `reward/confidence.py` ★ (reine Mathe, deterministisch, kein I/O)
```python
def wilson_lower_bound(successes: int, n: int, z: float = 1.96) -> float | None:
    """Wilson-Score-Lower-Bound. n==0 → None. Konservativer Win-Rate-Schätzer (klein-N-stabil)."""

def expectancy_r(r_multiples: list[float]) -> float | None:
    """Mittel der R-Multiples (P&L / initiales Risiko). [] → None."""

def system_quality_number(r_multiples: list[float]) -> float | None:
    """√N · mean(R)/stdev(R). Nebenmetrik; bei N<2 oder stdev==0 → None. (Van Tharp; N>30 für Signifikanz.)"""

def compute_confidence(r_multiples: list[float], wins: int, n: int, cfg: RewardConfig) -> ConfidenceReport:
    """N < n_min → state=INSUFFICIENT, confidence_value=None (fließt in NICHTS).
    Sonst: confidence_value = bounded combiner aus wilson_lower_bound & expectancy_r (v1-Formel,
    config-tunbar). win_rate_wilson_lb, expectancy_r, sqn, n IMMER befüllt (= die eigentlichen Logging-Größen)."""
```
- **Tests (≥14):** Wilson gegen bekannte Werte (z. B. 7/10, 0/10, 10/10 — nie 0/1-Kollaps); n=0 → None;
  Expectancy/SQN korrekt + Edge-Cases (leer, stdev 0); **N_min-Gate**: N=9 → INSUFFICIENT mit
  `confidence_value=None`, N=10 → OK; Monotonie (mehr Wins → höhere Wilson-LB bei festem N).
- Anti-Pattern-Beweis-Test: naive Win-Rate 1/1 = 100 % ist NICHT die Confidence (INSUFFICIENT, weil N<10).

### Step 5 — `reward/scorer.py` ★ (deterministisch — Decision B2 + D)
```python
class Scorer:
    def __init__(self, cfg: RewardConfig) -> None: ...
    def score(self, *, r_multiple: float, status: str, spread_at_entry_pct: float,
              debate_confidence: float | None, score_before: float) -> RewardResult:
        """Prozess-bewusstes Delta:
        outcome_delta  = clamp(outcome_weight * clip(r_multiple, ±r_clip), gewichtet mit loss_asymmetry)
        process_delta  = Prozess-Qualität UNABHÄNGIG vom Outcome:
                         + clean_exit_bonus wenn status==CLOSED_BY_BROKER (geplanter SL/TP getroffen)
                         - Abzug wenn status==TIME_STOP (Drift, kein Edge realisiert)
                         + Bonus wenn spread_at_entry_pct <= tight_spread_pct (sauberer Entry)
                         (debate_confidence nur als schwaches Prozess-Signal, NICHT als Multiplikator)
        gesamt_delta   = clamp(outcome_delta + process_delta, ±max_delta_per_trade)
        score_after    = clamp(score_before + gesamt_delta, score_min, score_max)
        win_loss       = WIN/LOSS/BREAKEVEN aus r_multiple."""
```
- **Kernprinzip (Tests, ≥12):** guter Outcome + schlechter Prozess (TIME_STOP, weiter Spread) wird
  **schwächer** belohnt als guter Outcome + sauberer Prozess; Pech-Verlust an geplantem SL (sauberer
  Prozess) wird **weniger** bestraft als sloppy-Verlust. Clamping greift (Score nie <0/>100;
  `|delta|` nie >Cap). Symmetrie bei `loss_asymmetry=1.0`. Reiner Outcome-only-Modus wäre als Anti-
  Pattern markiert — Test stellt sicher, dass `process_delta` tatsächlich differenziert.

### Step 6 — `reward/synthetic.py` + Trennung **[→ Opus]** (Decision H)
> **Zwei verschiedene Dinge sauber trennen:** *synthetic* = generierte Testdaten (nie real, eigene
> DB). *demo* = echte IG-Demo-Account-Trades (reale Fills, kein echtes Geld) — legitime Bootstrap-Daten.
- `SyntheticTradeGenerator`: erzeugt **klar gelabelte** R-Multiple-Verteilungen (`synthetic=True`) für
  Tests der Confidence/Scorer-Mathe.
- **Harte Orts-Trennung (synthetic):** Live-Pfad schreibt **immer** `live_db_path`; jeder synthetische
  Schreiber **immer** `synthetic_db_path`. Grenze = der DB-Pfad, nicht nur ein Flag (defense-in-depth:
  zusätzlich `synthetic=True`-Tag). `synthetic=True`-Daten fließen **nie** in die Live-Edge-Metrik,
  unabhängig von jedem Flag.
- **Demo-Trades (Bootstrap):** echte Demo-Trades laufen über den **normalen** Pfad in die `live_db_path`,
  getaggt `account='demo'`. Ob sie in die Edge-Metrik zählen, steuert **`include_demo_in_edge`**
  (Default **`True`** für die Bootstrap-Phase — siehe §5). Bei Go-Live re-baselinen, dann via Tag
  ausschließbar.
- **Tests (≥8):** ein `synthetic=True`-Schreibvorgang trifft den Live-DB-Pfad **niemals** (Pfad-Guard);
  bei `include_demo_in_edge=True` zählen `account='demo'`-Trades in die Edge-Query, bei `False` nicht;
  Tags konsistent gesetzt.

### Step 7 — `reward/brain.py` **[→ Opus]** (Decision E, F, J)
```python
class Brain:
    def __init__(self, llm_client, token_meter, cfg: RewardConfig) -> None: ...   # research.LLMClient REUSE
    def reflect(self, closed: ClosedTrade, outcome: RewardResult, market_context: dict) -> LessonResult:
        """EIN Haiku-Call (single-shot), eigener Timeout. Baut Prompt aus Outcome + R + Prozess-Signalen
        + market_context, parst lesson_text, token_meter.record(...). BEST-EFFORT: jede Exception →
        LessonResult(ok=False, error=...), KEIN Re-raise. Swappbare Schnittstelle (LessonExtractor-
        Protocol), damit Batch/Scheduler später ohne Reward-Code-Änderung andocken."""
```
- AI-Grenze: Brain extrahiert **nur Sprache → Erkenntnis**. Keine Zahlen-/Score-Entscheidung.
- **Tests (≥8):** FakeLLM liefert valide Lesson → `trade_lessons`-Record korrekt; Malformed-JSON/
  Timeout/Exception → `ok=False`, **kein Crash**; token_meter wird additiv befüllt; Prompt enthält
  R-Multiple + Status + market_context.
- ⟳ **2026-06-19 (Step 7 gebaut — Code = Source of Truth, zwei dokumentierte Abweichungen):**
  (1) **Signatur `Brain(llm_client, cfg)`**, nicht `Brain(llm_client, token_meter, cfg)`:
  `research.LLMClient.ask_candidate` **meter't bereits intern** (ruft `research.token_meter.record`
  und legt den Record auf `client.last_usage` ab). Ein zweites `token_meter` würde **doppelt
  zählen** — also wird `token_meter` **transitiv über den Client** wiederverwendet (Decision F
  erfüllt) und der Brain liest `last_usage` nur zur Beobachtung zurück. Spiegelt exakt, wie der
  P6-`debate` `last_usage` liest statt neu zu metern. (2) **Log-Level:** die *eigene* best-effort-
  LLM-Fehlschlag-Zeile des Brains ist `logger.warning` (eine fehlende **optionale** Lesson, **kein**
  DB-Write, kein Daten-Integritätsfehler); das `logger.critical` aus Decision J gehört in den
  **Recorder** (Step 8), wo die DB-*Writes* passieren. (3) Der `eigene Timeout` (§5
  `lesson_timeout_s`) = der **Transport-Timeout** des Clients (von der Wiring, Step 13, gesetzt) —
  kein separater Threading-Timeout; ein Timeout wird zur Exception → vom best-effort-Wrapper zu
  `ok=False`. `reward/credentials.py` bleibt **Step 13** (Wiring), nicht Step 7 (spiegelt P6, das
  `debate/credentials.py` erst im Wiring-Modul ergänzte) → Step 7 ist unit-only, keyring-/SDK-frei.

### Step 8 — `reward/recorder.py` (Decision A, J — die Orchestrierung)
```python
class RewardSink:                       # erfüllt das (in protocols zu definierende) RewardSink-Protocol
    def __init__(self, db, broker, scorer, brain, confidence_provider, cfg) -> None: ...
    def on_trade_opened(self, opened: OpenedTrade) -> None:
        """db.insert_trade(OPEN-Record inkl. gate_path, research_confidence, initial_risk[Step 12],
        session_date, intended levels). Best-effort, Fehler → logger.critical, kein Re-raise (J)."""
    def on_trade_closed(self, closed: ClosedTrade) -> None:
        """1) pnl_resolver.resolve(closed) → close_level, profit_loss, r_multiple
        2) db.update_trade_close(deal_id, …)
        3) score_before = db.get_current_score(); scorer.score(…) → RewardResult
        4) db.insert_reward(trade_id, {outcome_score_delta, process_score_delta, score_after, win_loss,
           pnl_raw, r_multiple[Step12], veto_trigger_count, gate_fail_count, debate_confidence,
           spread_at_entry_pct})
        5) brain.reflect(…) best-effort → db.insert_lesson(…)
        JEDER Schritt einzeln gekapselt; Fehler → logger.critical + weiter (J). Trade bleibt am Broker
        geschlossen; Reward/Lesson sind Buchhaltung/Lernen, keine Safety-Schicht."""
```
- **Tests (≥10):** voller open→close-Pfad schreibt alle drei Tabellen; Reward-Insert-Fehler ⇒
  critical-log, Trade trotzdem CLOSED; Lesson-Fehler ⇒ Reward steht trotzdem; idempotenz: zweimaliges
  `on_trade_closed` für denselben `deal_id` verdoppelt den Score nicht (Guard via `get_trade_by_deal_id`-
  Status oder vorhandenem Reward).
- ⟳ **2026-06-19 (Step 8 gebaut — Code = Source of Truth, drei dokumentierte Abweichungen):**
  (1) **In-Memory-Stash zwingend:** `trade_outcomes` hat **keine** Spalten für `spread_at_entry_pct`/
  `debate_confidence` (die liegen in `reward_pts`, erst am Close geschrieben) → der volle Prozess-Kontext
  kann nicht über die DB von open→close laufen. `on_trade_opened` stasht daher die `OpenedTrade` in
  `self._opened[deal_id]`; `on_trade_closed` liest sie zurück (gleiche Sink-Instanz, ein Executor-Zyklus).
  Die DB-Zeile bleibt der durable Anker (`trade_id`-PK + Status + kalter Minimal-Resolve-Kontext beim
  Restart; kein Stash → Neutral-Prozess-Defaults, durable Signale R/Exit scoren normal). (2) **`confidence_provider`**
  wird **optional + keyword-only** (Konzept hatte ihn positional vor `cfg`): **observe-only** (keine
  Confidence-DB-Spalte) → best-effort aufgerufen + geloggt, nie geschrieben, gatet nichts (Decision C);
  `cfg` steht vor ihm. (3) **Idempotenz = OPEN/CLOSED-Status**; Reihenfolge `resolve` **vor**
  `update_trade_close`, damit `PnLUnavailable` den Trade OPEN/retry-bar lässt. Residual-Edge (ehrlich):
  `insert_reward`-Fehler **nach** dem Close → Trade CLOSED/ungescored, Retry skippt → Reward verloren
  (geloggt `critical`) — die benignere Seite vs. Doppel-Scoring. `veto_trigger_count`/`gate_fail_count`
  bleiben v1 NULL (nicht score-tragend).

### Step 9 — `reward/pnl_resolver.py` (P&L-Auflösung)
```python
def resolve(closed: ClosedTrade, broker, opened: OpenedTrade, cfg) -> tuple[float, float, float]:
    """broker.get_trade_history(days=…) → Transaktion per deal_id/deal_reference matchen →
    (close_level, profit_loss). r_multiple = profit_loss / opened.initial_risk.
    Deal noch nicht in History (IG-Lag) → Fallback: aus Levels approximieren
    (profit_loss ≈ (close_level - open_level)·size·point_value·sign), pnl_source='approximated' setzen
    + logger.critical. NIE raten ohne Flag."""
```
- **Tests (≥8):** exakter History-Match; Fallback-Pfad setzt Flag; R-Multiple-Vorzeichen für BUY/SELL
  korrekt; `initial_risk==0` → defensiv (kein ZeroDivision, BREAKEVEN/None).
- `[VERIFY]` Step 1.1 liefert die History-Feldnamen.
- ⟳ **2026-06-19 (Step 9 gebaut — Code = Source of Truth, zwei dokumentierte Abweichungen):**
  (1) **Match ist heuristisch, nicht per `deal_id`/`deal_reference`:** der IG-History-Record trägt
  **keinen** deal_id/deal_reference (verifizierter Contract 1.1); `epic` = **instrumentName**
  (Anzeigename ≠ Epic-Code), `direction` = **hardcoded None**. → Match = harter `size`-Filter +
  `open_level`-Nähe zu `opened.intended_open_level`, Tie-Break = Recency (jüngstes `close_date`).
  Vorzeichen kommt gratis: IG-`profit_loss` trägt es bereits → kein per-Direction-Flip.
  (2) **Fallback = `PnLUnavailable` werfen, NICHT aus Levels approximieren** (Operator-Entscheidung):
  ein `ClosedTrade` trägt **kein `close_level`** → die skizzierte Approximation
  `profit_loss ≈ (close_level − open_level)·…` würde eine Zahl **erfinden**. Stattdessen no-match/not-ok
  → `PnLUnavailable` (fail-closed), idempotenter Retry via `deal_id`, sobald die History aufholt. Da
  der einzige Erfolgspfad ein echter History-Match ist, braucht v1 **keinen** `pnl_source`-Tag; die
  Rückgabe bleibt das §9-`tuple[float, float, float]`. `opened` wird **duck-typed** (nur `.size`/
  `.intended_open_level`/`.initial_risk`).

### Step 10 — Executor-Naht verdrahten (Decision A) + **P5-Regression**
- `execution/protocols.py`: `RewardSink`-Protocol ergänzen (Stilvorlage = bestehende Protocols).
- `execution/executor.py`: `Executor.__init__(..., *, debate_runner=None, reward_sink=None, …)`.
  - Nach erfolgreichem `place_result.status == "OPEN"` und **vor** `monitor_position`:
    `if self.reward_sink: self.reward_sink.on_trade_opened(build_opened(...))`.
  - `monitor_position`-Return in Variable fangen; **danach**
    `if self.reward_sink: self.reward_sink.on_trade_closed(build_closed(result))`; dann `return result`.
  - Beide Aufrufe in `try/except` → ein werfender Sink darf den Zyklus **nie** kippen (J).
- **Tests (≥6):** `reward_sink=None` → `run()` **bit-identisch** (bestehende Executor-Tests bleiben grün);
  mit Sink → beide Callbacks mit korrekten Payloads gefeuert; werfender Sink ⇒ Zyklus liefert trotzdem
  sein normales `ExecutionResult`.
- **Pflicht-Regression:** `pytest` für **P5 (135) / P4 (88) / P6 (70)** erneut grün.
- ⟳ **2026-06-22 (Step 10 gebaut — Code = Source of Truth, drei dokumentierte Abweichungen):**
  (1) **`build_opened`/`build_closed` importieren `reward.models` LAZY** (innerhalb der Helper), damit
  `executor.py`s Modul-Imports `execution.* + stdlib` bleiben und ein sink-freier Lauf **kein** `reward`
  zieht (laufzeit-bewiesen). Spiegelt `ig_bot.py`s lazy `scripts.wiring`-Import; die Contracts
  (`OpenedTrade`/`ClosedTrade`, stdlib-only Dataclasses) sind die Single-Source-of-Truth-Payload-Form
  statt eines lokalen Re-Modellierens. (2) **`point_value=1.0` + `account="demo"` als v1-Konstanten:**
  `ExecutionConfig` hat **kein** `point_value` (DAX 1 €/pt; `sizing.py` hardcodet 1.0 ebenso); `account`
  ist in der Bootstrap-Phase fest `"demo"` (der **durable** Demo/Live-Tag gehört in die Wiring-Schicht,
  Step 13, die `broker_name` kennt). (3) **Test-Placement:** die Seam-Tests liegen in
  `phase5_execution/tests/test_executor.py` (wo Executor + Fakes leben, neben dem strukturgleichen
  Debate-Seam), **nicht** in `phase7_reward/tests/test_executor_seam.py` (§4) — cross-test-package-Fake-
  Reuse ist nicht baubar. **Regression: P5 135 → 142** (+7 Seam-Tests); P7 118 · P4 88 · P6 70 unberührt.
  Zusätzlich: `outcome` auf Run-Scope gehoben (Contract 1.3); `_notify_closed` feuert nur bei
  `CLOSED_BY_BROKER`/`TIME_STOP`; `FakeDB` um `get_current_score` (DbProtocol-vollständig) ergänzt.

### Step 11 — Loop-Closure (Decision I)
- `[VERIFY]` (Step 1.5): zieht `research/prompt.py`/`context_builder.py` heute schon
  `db.get_recent_lessons(...)` in den Prompt?
  - **Ja** → P7 schließt den Loop allein durch Schreiben + `mark_lesson_used`; **Test**: eine via P7
    geschriebene Lesson taucht im nächsten Research-Kontext auf.
  - **Nein** → kleine P4-Erweiterung: Lessons-Block in den Prompt injizieren + `mark_lesson_used`
    buchen (separater, klar gekennzeichneter Sub-Step; **P4-Tests** danach grün).
- ⟳ **2026-06-22 (Step 11 gebaut — Code = Source of Truth):** Es ist der **„Ja"-Zweig** (Contract 1.5
  bestätigt: `context_builder.py:184` zieht `get_recent_lessons(5)`, `prompt.py:_render_lessons` rendert
  sie) → **keine** P4-Prompt-Änderung. Verdrahtet wurde **nur** die „mark used"-Hälfte in
  `research/research.py`: `_DBLike` += `mark_lesson_used`, best-effort `_mark_lessons_used(context.recent_lessons)`
  **nach** erfolgreichem `ask_candidate` (vor der Validierung — der semantisch korrekte „used in research"-
  Punkt; **nicht** in `build_context`, das würde bei Pre-LLM-Abstains over-counten, und **nicht** in der
  reinen `prompt.py`). Fehlende `id` → skip; werfendes `mark_lesson_used` → `log.warning` + weiter (Bookkeeping
  bricht den Zyklus nie). **Erster DB-Write aus P4-Research** — benigner `used_in_research`-Increment, kein
  Trade/Outcome-Write. **+6 Tests → P4 88 → 94**; P7 118 · P5 142 · P6 70 · P2 59 unberührt. (Der Test „eine
  P7-geschriebene Lesson taucht im nächsten Research-Kontext auf" ist strukturell schon durch die
  context_builder-/prompt-Tests gedeckt; der neue Beweis ist die `mark_lesson_used`-Verdrahtung.)

### Step 12 — Migration `002` + minimale P2-Berührung (Decision G)
- `migrations/002_phase7_reward.sql` (additiv, idempotent):
  `ALTER TABLE trade_outcomes ADD COLUMN initial_risk REAL;`
  `ALTER TABLE trade_outcomes ADD COLUMN account TEXT;`   ⟳ 2026-06-18 (s. u.)
  `ALTER TABLE reward_pts ADD COLUMN r_multiple REAL;`
- `persistence/db.py`: **nur** `_TRADE_COLUMNS += ("initial_risk", "account")` und
  `_REWARD_COLUMNS += ("r_multiple",)` (Whitelist-Erweiterung — keine Logik-Änderung). Das ist die
  **einzige** P2-Berührung. **P2-Tests (59) danach grün.**
- Migration-Runner gegen echtes `persistence/migrations.py` verifizieren (Versionstabelle, Idempotenz).
- ⟳ **2026-06-18 (Verify-against-code, Operator-Entscheidung):** Das gelieferte Schema
  (`migrations/001_initial.sql`) hat **keine `account`-Spalte** in `trade_outcomes`. Da der
  Demo/Live-Tag (`OpenedTrade.account`, §6 Step 3) persistiert werden muss, damit
  `include_demo_in_edge` (§6 Step 6) ihn filtern kann, fügt Migration `002` zusätzlich
  **`account TEXT`** hinzu (oben), und die Whitelist nimmt `"account"` mit auf. Hinweis: `ADD COLUMN`
  ist in SQLite nicht selbst idempotent — die Idempotenz kommt aus der `_schema_version`-Tabelle
  (Runner wendet Version 2 nur einmal an).
- ⟳ **2026-06-22 (Step 12 gebaut — Code = Source of Truth, zwei dokumentierte Abweichungen):**
  (1) **Die Migrations-Datei liegt in `phase2_persistence/migrations/002_phase7_reward.sql`, NICHT
  `phase7_reward/migrations/`** (wie der §4-Modulbaum listet): der Runner (`persistence/migrations.py`)
  und `Database.run_migrations()` scannen **nur** `schema.MIGRATIONS_DIR = phase2_persistence/migrations/`
  (`db.py:75`, `schema.py:14`). Anderswo abgelegt würde `init_db.py`/`Database.run_migrations()` sie nie
  finden + eine frische DB hätte die Spalten nicht; deckt sich mit der P2-Regel „DDL lebt nur in
  `migrations/*.sql`". (Operator-bestätigt: phase2-Dir + Tests fixen, statt den Runner multi-dir-fähig
  zu machen.) (2) **P2-Test-Folge:** eine frische DB erreicht jetzt **Version 2** → die **vier**
  versions-asserting Tests in `test_migrations.py` wurden v1→v2 nachgezogen (nicht nur drei: auch
  `test_database_run_migrations_idempotent`); zusätzlich +1 Spalten-Beweis (`test_phase7_columns_present`)
  und +2 Round-Trip-Beweise in `test_db.py` → **P2 59 → 62** (das „59" ist historisch; der Anstieg ist
  neue Coverage für diese Änderung, keine Regression). Regression unberührt: P7 118 · P4 94 · P5 142 · P6 70.

### Step 13 — `wiring.py` + Operator-Scripts
- `wiring.py`: baut `RewardSink` mit echten P1-Broker / P2-`Database` / reused `research.LLMClient` +
  `token_meter`; gibt ihn an `Executor(reward_sink=…)` (oder an `ig_bot.py`-Composition).
- `backfill_synthetic.py` **[→ Opus]**: Operator-Tool, schreibt **ausschließlich** `synthetic_db_path`,
  **harter Guard**: bricht ab, wenn der Zielpfad == `live_db_path`. Nie auto-live.
- `smoke_test.py`: ein echter Haiku-`reflect()`-Lauf, DRY. `live_test.py`: voller
  open→close→reward→lesson gegen IG-Demo (kleine Size), hart asserted, `exit 0` (Operator, nicht CI).
- ⟳ **2026-06-23 (Step 13 gebaut — Code = Source of Truth, vier dokumentierte Reconciliations):**
  (1) **`wiring.py` spiegelt P6, statt in `ig_bot.py` zu injizieren** (die §13-Alternative): P7 baut ein
  **eigenes** `build_executor` direkt aus dem installierten `execution`-Paket (löst die
  `scripts.wiring`-Kollision P4/P5/P6/P7) und injiziert `reward_sink=` — **keine** P5-Datei-Berührung,
  Phasen-Isolation gewahrt. Drei Entry-Points: `build_reward_sink(broker, db, …)`, `build_brain(…)`
  (smoke), `build_executor(config, *, confirm_fn, …)`. `token_meter` wird **transitiv** über den reused
  `LLMClient` reused (kein zweites Mess-System — wie Brain/Step 7). (2) **Reward-Live-Pfad debatte-frei**
  (einzige AI = die Lesson-Haiku; `debate_confidence=None`) — billiger/deterministischer Live-Gate;
  Debatte ist orthogonal (später additiv via P6-`debate_runner`). (3) **`live_test.py`:** harte Proofs =
  `trade_outcomes`(CLOSED) + `reward_pts`; die `trade_lessons`-Zeile ist **best-effort** (Decision E/J) →
  Info-Zeile, nicht FAIL-gegated. (4) **Keine neuen Unit-Tests** (Scripts + Shim operator-run, nicht
  collected — konsistent P4/P5/P6; der testbare Synthetik-Kern ist in Steps 4/6 gedeckt, inkl.
  §7(c)-Beweis). `backfill_synthetic.py` ruft `guard_synthetic_path` als **ersten** Schritt (vor jedem
  DB-Open) → exit 2 + kein Write, wenn Ziel == `live_db_path` (end-to-end gegen Temp-DB verifiziert).
  **Regression:** P7 118 · P2 62 · P4 94 · P5 142 · P6 70. **Phase 7 ist code-complete (Steps 0–13);
  offen ist nur der Operator-Live-Lauf + Doku-Flip auf „live-verifiziert" + Merge.**

---

## 7. Done-Kriterien (Phase-7-Gate)
- `pytest phase7_reward/tests/ -v` grün, **≥66 Tests** (Verteilung §4), Schwerpunkt `test_confidence.py`
  + `test_scorer.py`.
- **Regression grün:** P6 70 / P5 135 / P4 88 / P2 59.
- **Step 0b done:** `rg -i "instinct|ECC|promote" --type md` zeigt kein Instinct→VETO-Framing mehr;
  jede P7-Erwähnung in der Codebase-Doku trägt die kanonische Aussage (§2b).
- `reward_sink=None` beweisbar bit-identisch (Executor-Regression).
- **Beweis-Tests:** (a) N=9 liefert INSUFFICIENT, `confidence_value=None`; (b) guter Outcome/schlechter
  Prozess < guter Outcome/sauberer Prozess; (c) ein synthetischer Schreibvorgang trifft den Live-DB-
  Pfad nie; (d) Reward-Insert-Fehler ⇒ `logger.critical`, Trade bleibt CLOSED.
- `live_test.py` (Operator): erzeugt einen realen Demo-Trade-Outcome → `trade_outcomes`+`reward_pts`+
  `trade_lessons`-Row, `exit 0`. **Label ehrlich: live-verifiziert ≠ profit-validiert.**

## 7b. Empfehlung: volle ECC-Umsetzung (Instinct-Promotion) = separater, späterer Step

Die **volle** Vision (aus der älteren Notiz) — AI extrahiert strukturierte **Instincts**
(`trigger / domain(entry/exit/sizing/timing) / confidence / evidence_trade_ids[] /
contradictions_trade_ids[]`), Code **validiert** sie gegen echte Outcomes und **promotet** bewährte
zu deterministischen Regeln/VETOs (mit Prune→Archiv) — ist bewusst **NICHT in P7**. Empfohlener Ort:

- **Wann:** erst **nachdem** P7 über die Demo-/Bootstrap-Phase eine belastbare Lesson-/Outcome-Basis
  gesammelt hat (Größenordnung deutlich über `n_min`). Instinct-Promotion auf dünner Datenbasis ist
  genau das epistemisch gefährliche Muster, das vermieden werden soll.
- **Wo in der Roadmap:** als **eigener Step in P9 (V2)** — dort liegen ohnehin die strukturierten
  Lern-Bausteine (`decision_context`, `market_regime_snapshots`, Lesson-Embeddings/Vektor-Store) und
  die Council-Integration. Die Instinct-Schicht ist dieselbe Familie und konsumiert P7s `trade_lessons`
  + `reward_pts` als Input.
- **Harte Leitplanke:** „Promote zu VETO" darf die deterministische VETO-Schicht **nur** über einen
  deterministischen/menschlich gegateten Promotion-Schritt erreichen — eine promotete Regel wird
  **deterministischer Code**, die AI bleibt außerhalb der VETO-Auswertung. Das „keine AI in VETOs"-
  Prinzip bleibt unangetastet.
- **Substrat ist bereits da:** P7 schreibt `trade_lessons` (Freitext + `relevance_score` +
  `used_in_research`) und `reward_pts` (inkl. Prozess-Spalten) so, dass ein späterer Instinct-Layer
  ohne Reshaping darauf aufsetzen kann. P7 baut also den **Boden**, nicht das Instinct-System selbst.

---

## 8. Bewusst NICHT in Phase 7 (Carry-overs)
- **Confidence verdrahtet `risk_pct`/gatet Orders** → bewusst nicht (C: observe-only v1). Erst messen.
- **Batch-API / Scheduler-getriebenes `reflect()`** → P8-Hebel, Schnittstelle ist swappbar (E).
- **V2-Tabellen `decision_context` / `market_regime_snapshots`** (Writes existieren in db.py!) → **P9**,
  nicht P7. `process_score_delta`-Embedding-Reform ebenfalls P9.
- **Volle Instinct-Promotion-ECC** (strukturierte Instincts → validiert → Promote zu VETO) → **§7b /
  P9**, gated auf reale Outcomes. P7 baut nur das Substrat (`trade_lessons` + `reward_pts`).
- **Council-`verbesserungsvorschlaege`** als Pipeline-Input → P9.
