---
status: closed-phase
purpose: Phase-7 head — reward/brain (score + lessons + observe-only confidence), decisions A–J, pinned contracts
read-when: working in phase7_reward/ — read this head + its newest Session-stopped block first
detail: L2
up: ../CLAUDE.md
down:
  - ./SESSIONS_ARCHIVE.md      # full session history (L3)
  - ./README.md
  - ../docs/concepts/phase7_reward_concept.md   # full concept/plan snapshot (L3)
updated: 2026-07-17
---
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

> 🔁 **Phase-8 v1.6-hotfix edit (2026-07-02, Cause A part 2 — trade-row provenance, code = source of
> truth):** the v1.5 fix above stamped `provenance` into the lesson's `market_context_json` blob, but
> never onto the `trade_outcomes` row itself — because a **second, separate** P4 prompt channel
> (`context_builder`'s raw `db.get_recent_trades`) read straight off that row and stayed unfiltered.
> A live v1.6 run showed the LLM's abstain reasoning citing fake "three consecutive losses" from the
> three seeded verification trades. **Fix:** `recorder.py::_open_record` now also writes
> `"provenance": opened.provenance` (the field already existed on `OpenedTrade` since v1.5 — this is a
> one-line addition, not a new field) into the `insert_trade` record; it lands against the real DB
> only after P2 migration 003 (`trade_outcomes.provenance TEXT`, same "written but silently dropped
> until the migration lands" pattern as `initial_risk`/`account` for migration 002). Read by a new P2
> `get_recent_trades_for_prompt` (P4's second filtered getter, mirroring
> `get_recent_lessons_for_prompt`). **Reward/score math remains provably untouched** — `provenance`
> only ever reaches an `insert_trade` record, never a `Scorer`/`compute_confidence` input; lessons and
> trade history both gate nothing (root rule 3, Decision C/J intact). +2 P7 tests (**131 → 133**:
> provenance round-trips through `on_trade_opened`; defaults to `"autonomous"` when not overridden).
> Detail: `docs/concepts/phase8_v1.6_hotfix_plan.md` §6 + `phase8_scheduler/CLAUDE.md` →
> `## Session stopped — 2026-07-02 (v1.6-Hotfix: Cause A part 2)`.

> 🔁 **Phase-10 (V3) finding — ✅ FIXED same-day, follow-up session (2026-07-17, Bug A —
> `pnl_resolver` history-match had no plausibility guard, code = source of truth). Original
> finding (Block-B forensic session) preserved below; fix summary first:** implemented exactly
> the suggested guard (reject any `get_trade_history` candidate whose `close_date` predates the
> trade's own `open_ts`), with one correction caught by advisor review before shipping — a naive
> lexical/string compare across the two timestamps is unsafe (`open_ts` carries a local offset
> like `+02:00`, IG's `close_date` is UTC; a legitimate same-day match could sort as "earlier"
> and be wrongly rejected). The shipped guard parses both as tz-aware instants (`_parse_instant`,
> new helper in `pnl_resolver.py`) and compares in real UTC, defaulting to *not* reject when
> either side is unparseable. `_OpenCtx` (`recorder.py`, the cold-reconcile path) gained
> `open_ts`. +4 tests (`test_pnl_resolver.py`, **133 → 137**), including a golden replay of the
> row-6 incident below and a dedicated tz-correctness case. **The already-persisted bad row
> (`id=6`) is not retroactively corrected** — its `status` is `CLOSED` so idempotent reconcile
> never revisits it; a correction needs a fresh `get_trade_history` read against IG (deal
> `DIAAAAXZEYXT8BC`, should be settled by now) + a manual `UPDATE`, both live-network/live-DB
> actions left to the Nikinger. Detail: `phase10_v3/CLAUDE.md` → this session's
> `## Session stopped` block.
> live `trade_outcomes` row `id=6` (deal `DIAAAAXZEYXT8BC`, epic `IX.D.DAX.IGN.IP`, BUY, open
> `25140.06`, closed 2026-07-10) has `close_level=25714.5` / `profit_loss=-651.16` —
> **byte-identical** to row `id=5` (deal `DIAAAAXXFLTFRAG`, a *different* epic, closed a full
> week earlier on 2026-07-03). Cross-checked against `data/state/execution_state.json`: row 5's
> own `stop_level` really is `25714.5` (internally consistent, it stopped out there); row 6's own
> `stop_level` is `25110.06` — nowhere near `25714.5`. A BUY closing at `25714.5` from an open of
> `25140.06` would be a +574pt profit, not the recorded loss — row 6's stored numbers are
> internally contradictory. **Root cause:** row 6 closed `CLOSED_BY_BROKER` (no lag-free
> close-confirm reaches `ExecutionResult` for that path — Contract 1.2, "CLOSED_BY_BROKER bleibt
> `None`"), so `pnl_resolver.resolve()` (`reward/pnl_resolver.py:139-188`) fell to its branch-3
> heuristic: match by size-magnitude + smallest open-level distance among `get_trade_history`
> rows, tie-broken by recency — **never** rejecting a candidate whose `close_date` predates the
> trade's own `open_ts`, or whose `open_level` is wildly far from the intended entry. IG demo's
> settlement lag (documented 2026-06-23) likely meant row 6's own transaction hadn't posted yet,
> leaving row 5's already-settled transaction (same size `22.3` magnitude — expected, sizing is
> config-deterministic, not itself a red flag) as the only/best magnitude match despite being 7
> days old and 600+ points away in `open_level`, and its `close_level`/`profit_loss` got copied
> onto row 6. (End of original forensic finding — see the fix summary at the top of this block.)

> ⚠ **Phase-10 (V3) FINDING — NOT YET FIXED (2026-07-31, second data-week review, weekday
> read-only session; full evidence: `phase10_v3/DATA_WEEK_REVIEW_2026-07-31.md` §4 B2):**
> **der Reward-Score steigt nach jedem Verlust.** `scorer.py:115` rechnet
> `debate_signal = debate_confidence - 0.5` und nimmt damit eine Confidence in **[0,1]** an
> (Kommentar: „*Weak, centred, additive*"). Geliefert wird `DebateOutcome.confidence` auf der
> **0–100-Skala** (`phase5_execution/execution/executor.py:578`, in `reward_pts.debate_confidence`
> als 57/58/60 persistiert). Nachgerechnet an Trade 7 (Zeile stimmt exakt):
> `outcome_delta = 2.0 × (−0,975) = −1,95`, `process_delta = 1,5 × (1 + 1 + 59,5) = +92,25` →
> `clamp(±5)` → **+5,00 bei jedem Trade, unabhängig vom Ergebnis**. Empirisch: `score_after`
> **55 → 60 → 65 → 70** über vier aufeinanderfolgende Totalverluste.
> **Nicht kosmetisch:** Score > 50 ⇒ `Database.get_risk_level()` = `AGGRESSIV` ⇒ P5-Gate-4
> `risk_pct` **3 % statt 2 %** — der Bot erhöht nach vier Verlusten seinen Einsatz. Derselbe
> Score steht zudem im Research-Prompt („bot score: 70 · risk level: AGGRESSIV"). Die
> P7-Doku sagt korrekt „**Confidence** gatet nichts" — der **Score** gatet aber sehr wohl
> (`sizing.select_risk_pct` → `get_risk_level`); diese Kopplung ist nirgends als solche
> dokumentiert.
> **Warum die Suite es nie sah:** `tests/test_scorer.py` übergibt `debate_confidence=0.9/1.0/0.0`
> — die Tests kodieren die falsche Skala. Ein Fix **muss** die Testskala mitziehen.
> ⚠ **Der Ein-Zeichen-Fix (`/100`) repariert den Loop NICHT:** derselbe Verlust-Trade ergäbe
> `−1,95 + 1,5 × (1 + 1 + 0,1) = **+1,2**` — der Score stiege weiter bei jedem Verlust, weil ein
> SL-Treffer als `CLOSED_BY_BROKER` den `clean_exit_bonus` (+1,0) kassiert und der enge Spread
> nochmal (+1,0). Ob ein Stop-out ein „sauberer Exit" ist, ist eine **Phase-11-Designfrage**,
> kein Quickfix. Nicht angewendet: Wochentags-Regel (read-only).

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
| `reward/pnl_resolver.py` | `resolve()` → (close_level, profit_loss, r_multiple). **Bevorzugt lag-frei den Close-Confirm** (`closed.profit_loss` → direkt; `closed.close_level`+Richtung → aus Levels; Step 13c); **sonst** heuristischer `get_trade_history`-Match (**Size-Betrag**+Level+Recency, **kein** deal_id; Size magnituden-basiert weil IG SELL negativ signt) **+ Plausibilitäts-Guard (Bug-A-Fix 2026-07-17): `close_date` < eigener `open_ts` (tz-aware UTC-Vergleich) → verworfen**. no-match → `PnLUnavailable` | ✅ Step 9 (·13b·13c·Bug-A) |
| `reward/credentials.py` | dünner Shim → `broker_wrapper.credentials.get_credential("anthropic_api_key")` (verbatim P4/P6-Spiegel, `parents[2]`-Bootstrap) | ✅ Step 13 |
| `002_phase7_reward.sql` — **liegt in `phase2_persistence/migrations/`** (Code=SoT, s. Step-12-Block), **nicht** `phase7_reward/migrations/` | `ADD COLUMN initial_risk` / `r_multiple` **/ `account`** (Operator 2026-06-18, s. 1.7) + Whitelist-Erweiterung `persistence/db.py` (`_TRADE_COLUMNS`/`_REWARD_COLUMNS`) | ✅ Step 12 |
| `scripts/wiring.py` (`build_reward_sink`/`build_brain`/`build_executor`, spiegelt P6 — Executor direkt aus `execution`, `reward_sink` injiziert, **keine** P5-Edit) · `backfill_synthetic.py` (guard-first, nie live) · `smoke_test.py` (1× echter Haiku-`reflect`, DRY) · `live_test.py` (voller open→close→reward→lesson **+ reconcile-Retry bei IG-Lag**) · `inspect_history.py` (**read-only** History-Dump, Live-Debug 2026-06-23) | Composition + Operator-Tools | ✅ Step 13 (·13b) |
| `execution/protocols.py`-Edit + `executor.py`-Edit (P5) + Regression | `RewardSink`-Protocol + Naht (Decision A) — keyword-only `reward_sink=None` ⇒ P5 bit-identisch; `on_trade_opened`/`on_trade_closed` um `monitor_position`, beide guarded (J); `build_opened`/`build_closed` mit **lazy** `reward.models`-Import | ✅ Step 10 |
| `tests/{__init__,test_models,test_packaging}.py` | Step-3-Tests (21: Contracts/frozen/§5-Defaults/Exceptions + Editable-Install-Smoke) | ✅ Step 3 |
| `tests/test_confidence.py` | Wilson/Expectancy/SQN/N_min-Gate + Anti-Pattern-Beweis + Monotonie (30 Fälle, Ziel ≥14) ★ | ✅ Step 4 |
| `tests/test_scorer.py` | Prozess-vs-Outcome-Trennung, Clamping, Symmetrie/Asymmetrie, R-Clip, schwaches Debate-Signal (18 Fälle, Ziel ≥12) ★ | ✅ Step 5 |
| `tests/test_synthetic.py` | Generator-Determinismus/Labels, Pfad-Guard trifft Live-Pfad nie (+Aliasing), Edge-Selector Synthetik-Ausschluss + Demo-Toggle (11 Fälle, Ziel ≥8) | ✅ Step 6 |
| `tests/conftest.py` + `tests/test_brain.py` | erster P7-Fake (`FakeLLM`); valide Lesson → `ok=True`-verbatim, Prompt trägt R/Status/Kontext, alle Fehlerpfade → `ok=False`/kein Raise, AI-Grenze, Protocol (12 Fälle, Ziel ≥8) | ✅ Step 7 |
| `tests/test_pnl_resolver.py` | exakter/mehrdeutiger Match (size+Level+Recency), BUY-Win/SELL-Loss-R-Vorzeichen, `initial_risk==0` defensiv, not-ok/no-match/unbrauchbar → `PnLUnavailable`, ignoriert epic/direction **+ 4 Bug-A-Guard-Fälle (stale-Match verworfen, tz-aware-Korrektheit, unparsbar→kein Reject, `open_ts` fehlt→Guard aus)** (16 Fälle) | ✅ Step 9 (·Bug-A) |
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


> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
