---
status: plan (ausführungsreif)
purpose: Phase 10 (V3) — Abstain-/No-Trade-Lessons echt auf main + Persistenz-Reform (Regime-Snapshots, Decision-Context) + Paper-Trades. Direkt an Sonnet in Claude Code übergebbar.
read-when: Ausführung der Phase 10 (V3); NICHT bei Session-Start anderer Phasen
detail: L2
up: ../../phase10_v3/CLAUDE.md
updated: 2026-07-09
---

# Phase 10 (V3) — Abstain-Lessons + Persistenz-Reform + Paper-Trades
## Detaillierter Implementierungsplan für Claude Code

> **Author:** V3-Browser-Planungschat, 2026-07-09 (Do, abends — Ausführung beginnt Fr 2026-07-10).
> **Audience:** Claude Code (Sonnet). Entscheidungen sind gelockt, Schritte sequenziert, Namen fixiert.
> **Inputs:** `PHASE10_V3_KICKOFF_HANDOVER.md`, `meta_m1_harness/specs/S1–S7.md` (Bauplan, zweifach
> real durchgebaut), `META_M1_CLOSEOUT_HANDOVER.md`, Nikinger-Locks 2026-07-09 (V3-D1…D10).
> **Drift-Konvention:** Der Planungschat hatte einen **teilweise veralteten** Projekt-Snapshot
> (Root-CLAUDE.md dort zeigte noch P7). Alles gegen den echten Repo-Stand zu Prüfende ist
> **[VERIFY]** markiert — bei Ausführung verifizieren, nie als gesichert übernehmen. **Code ist Wahrheit.**
> **Doc-Layers-Konvention gilt:** jede neue `.md` bekommt eine L1-Header-Card + One-Liner in
> `docs/INDEX.md` **im selben Commit**; Session-Rotationsregel beachten.

---

## §0 Mission + gelockte Entscheidungen

**Mission V3:** Der Bot wird lernfähig aus seinen eigenen Abstains — **mit den Daten, die da
sind.** Kein Research-Layer-Umbau, kein Broker-Wrapper-Umbau (spätere Phase). Drei Blöcke:
**Step 0** (Daten-Auswertung, docs-only), **Block A** (Abstain-Lessons echt auf main, Specs
S1–S7 als Bauplan), **Block B** (Persistenz-Reform: `market_regime_snapshots` +
`decision_context` + **Paper-Trades**). Block C (UI) ist **nicht Teil dieses Plans** (§13).

**⚠ Harte Arbeitsteilung (nicht verhandelbar):** Der Baseline-Live-Lauf läuft wochentags.
**Bot-berührende Steps NUR am Wochenende** (Markt zu, Bot steht). **Wochentags nur
docs-only / read-only.** Jeder Step trägt unten sein Fenster. Wochentags-Regeln für CC:
read-only auf `data/` (SQLite via `mode=ro`-URI), keine Migration, kein Scheduler-Restart,
keine `live_test.py`, Unit-Tests (isoliert, tmp_path, gemockt) erlaubt, Commits nur docs-only.

**AI-Grenzen dieser Phase:** Genau **zwei** AI-Nähte, beide best-effort, beide triggern nie
eine Order: (1) `reflect_abstain` (Spiegel des P7-`reflect()`-Musters, Haiku, Tages-Cap),
(2) optionaler **Council-Paper-Call** (Flag, default AUS, Cap 3/Tag) — Output landet
ausschließlich in `paper_trades`, nie im Order-Pfad. VETOs/Gates unantastbar. Klassifizierung,
Persistenz, Paper-Auflösung, Regime-Features = deterministischer Code.

### Gelockte Entscheidungen (Nikinger, 2026-07-09)

| # | Thema | Lock |
|---|---|---|
| V3-D1 | Abstain-Persistenz | Tabellen in `data/trading_bot.sqlite` via **P2-Migration 005** (Nr. **[VERIFY]**, nach 004). Zugriff über phase-eigene Store-Klassen mit eigener sqlite3-Connection (**UniverseStore-Muster**, `db.py`-Whitelist unberührt **[VERIFY]**: Own-Connection-Stores umgehen die Whitelist wie UniverseStore). |
| V3-D2 | Paket-Ort | `phase10_v3/` als Umbrella. Paket `abstain_lessons/` exakt wie S1–S7 (Anker bleiben gültig); Paper-Trade-Modul **im selben Paket** (`paper.py`, `paper_store.py`). Zweites Paket `market_context/` für Block B. Tests in `phase10_v3/tests/`. |
| V3-D3 | S6 Research-Injektion | **V3 flag-gated, default OFF** (`include_abstain_lessons=False` ⇒ bit-identisch). **Aktivierung ist NICHT V3** — separater Operator-Schritt nach manueller Review der ersten ~20 Lessons (Pro-Trade-Bias-Risiko). Paper-Lessons via Parameter ausschließbar. Erneute Entscheidung später. |
| V3-D4 | Block-B-Scope | V3 = `market_regime_snapshots` (deterministische Features + **observe-only `regime_tag`**) + `decision_context` (Bull/Bear-Digest, Judge, VETO-/Gate-Faktoren, Outcome-Link). **NICHT V3:** `lesson_embeddings`, Regime-*Nutzung* (Floor/Directions-Modulation), typisierte Signal-Objekte (Research-Layer → spätere Phase). |
| V3-D5 | Paper-Trigger | **Nur `REASON_DEBATE_ABSTAIN`** (Kandidat existiert, Debatte sagte nein). **Nie** VETO-/Gate-Abstains (Safety wird nie kontrafaktisch "widerlegt" — keine "VETO kostet Geld"-Lessons), nie `research_empty` (kein Kandidat ⇒ undefiniert). |
| V3-D6 | Paper-Richtungsquelle | **Hybrid mit klarem Fokus auf deterministisch:** (primär) **Both-Sides-Shadow-Tracking** — Long UND Short vom selben Entry, null LLM-Kosten, beantwortet "war der Abstain richtig?" (verlieren beide ⇒ Abstain validiert). (sekundär) **Council-Paper-Call** hinter Flag `enable_paper_debate` (default OFF), Cap 3/Tag, expliziter Paper-Modus mit erzwungenem Pick. |
| V3-D7 | Paper-Auflösung + Trennung | Deterministisch: virtueller Entry (BUY→ask/SELL→bid, **frische Quote** zum Abstain-Zeitpunkt), gleiche SL/TP-Distanzen wie reale Sizing-Logik **[VERIFY Symbole]**, retrospektive Bar-Auflösung am virtuellen Time-Stop (ein `get_ohlcv`-Call/Epic, first-touch; SL+TP in derselben Bar ⇒ konservativ SL; Bars fehlen ⇒ `EXPIRED_UNRESOLVED`, nie raten). **Harte Trennung:** eigene Tabelle `paper_trades`, nie `trade_outcomes`/`reward_pts`, zählt **nie** in Confidence-N, Lessons `source='paper'`-getrennt. Kein Order-Call, nicht mal Demo. |
| V3-D8 | reflect-Aktivierung | Klassifizierung + Persistenz ab Wiring **immer an** (best-effort). `reflect` (Haiku) ab Wiring an, aber **nur** Debate-Abstains + Paper-Resolutions, **gemeinsamer Tages-Cap 10** (DB-gezählt, restart-sicher). |
| V3-D9 | Sequenzierung | Fr 10.07 = Steps 0–3 (docs-only/read-only). **WE 1 (11.–12.07.)** = Block A komplett + **eine** Migration 005 mit *allen* neuen Tabellen + Sink live. Woche 2 wochentags = Review-Note + Konzeptarbeit (docs-only). **WE 2 (18.–19.07.)** = Block B + Paper-Pipeline. Drop-Order unter Druck: §14. |
| V3-D10 | Housekeeping + Block C | Standard-Housekeeping (§3). **UI (Block C) raus aus diesem Plan** — Operator-Kontrolle über Paper-Trades vorerst via Config + Command-File (P8-Command-Pfad-Hook); UI-Toggle/-Anzeige = Block-C-Kandidat (§13). |

### Leitplanken (unverändert, bestätigt)

AI-Output triggert nie eine Order · VETOs/Gates unantastbar · alle neuen Nähte default-inert
(Default `None`/`False` ⇒ bit-identisch, beweispflichtig) · Credentials nur Keyring · TDD,
keine Netzwerk-Calls in Unit-Tests · atomare Commits + Commit ⇒ Note-Update · stderr-Logging ·
Doc-Layers-Konvention · Handover nach ~20–30 Tool-Calls via `## Session stopped` ·
Live-Baseline wochentags nie berühren.

---

## §1 Schrittsequenz (Übersicht)

| Step | Inhalt | Fenster | Commit-Grenze |
|---|---|---|---|
| 0 | `phase10_v3/CLAUDE.md`-Skeleton + INDEX (allererste Aktion) | Fr (docs-only) | eigener Commit |
| 1 | Housekeeping: Legacy-Grep, Regression-Baseline, .md↔Code-Verify | Fr (read-only + docs) | 1–2 Commits |
| 2 | **Step-0-Datenanalyse** → dated Analyse-Doc | Fr (read-only, `mode=ro`) | eigener Commit |
| 3 | **Contract-Verifikation** S1–S7 + Block-B-Anker gegen As-Built → Anker-Annex | Fr (read-only + docs) | eigener Commit |
| 4 | Migration **005** (alle Tabellen) + `AbstainStore`/`PaperTradeStore` | **WE 1** | eigener Commit |
| 5 | Block-A-Module: S1 models · S2 classifier · S4 reflect | **WE 1** | je Spec ein Commit |
| 6 | S5-Naht real (P5-Executor + P8-Wiring, Sink live) + S7-Report + S6 dunkel | **WE 1** | 2–3 Commits |
| 7 | WE1-Abschluss: volle Regression, DB-Backup-Protokoll, Mo-Restart-Beweis | WE 1 → Mo | eigener Commit |
| 8 | Woche-2-Review-Note (Record-Verteilung, Lesson-Qualität) | Wo 2 (docs-only) | eigener Commit |
| 9 | Block B: `market_context/` (Regime-Features + Writer + Seams) | **WE 2** | 2 Commits |
| 10 | Paper-Pipeline: Shadow-Pair, Auflösung, Tracker, optionaler Council-Call | **WE 2** | 2–3 Commits |
| 11 | Post: Doku-Sync, ROADMAP, Session-Rotation, Handover | WE 2 | eigener Commit |

Reihenfolge-Begründung: 2+3 MÜSSEN vor WE 1 liegen — die Analyse liefert die
`cycle_outcome`-Feld-Zuordnung und die Contract-Anker, ohne die Step 6 blind verdrahtet.
Migration 005 enthält bereits die Block-B-/Paper-Tabellen (Schema nur **einmal** anfassen),
auch wenn deren Write-Pfade erst WE 2 kommen.

---

## §2 Step 0 — Phasen-Skeleton (allererste Aktion, Fr)

1. `phase10_v3/CLAUDE.md`: Header-Card, Zweck (Absatz-Fassung von §0), Modul-Tree
   (`abstain_lessons/`, `market_context/`, `scripts/`, `tests/`), Verweis auf diesen Plan +
   Kickoff-Handover + Specs, leerer `## Session stopped`-Block.
2. `docs/INDEX.md`: One-Liner für `phase10_v3/CLAUDE.md` + diesen Plan (Plan liegt unter
   `docs/concepts/phase10_v3_plan.md`; einsortieren, falls dem Repo noch fehlend).
3. **[VERIFY]** `docs/DOC_LAYERS_CONVENTION.md` kurz lesen (Header-Card-Format exakt).

**Akzeptanz:** Ein Commit; Skeleton existiert; INDEX konsistent.

---

## §3 Step 1 — Housekeeping (Fr, read-only + docs)

1. **Legacy-Grep (Ritual):** `grep -rn -i "turbo\|CALL/PUT\|pre_trade_option_check\|expected hold" --include="*.py" --include="*.md"` —
   bekannter aktiver Restbestand `turbo_candidates.json` (P5-Gate-2-Contract) bleibt; alles
   andere bereinigen (docs-only) oder begründet protokollieren.
2. **Regression-Baseline:** volle `pytest`-Suite. Erwartung **[VERIFY]**: P1 87 · P2 76 ·
   P3 100 · P4 141 · P5 154 · P6 70 · P7 133 · P8 217 · P9 72 · root 77 **+ M1-Tests
   (`meta_m1_harness/tests/`, Count [VERIFY])**, alle grün. Realen Count protokollieren.
   ⚠ Nur Unit-Tests (isoliert) — keine `live_test.py`, kein Netz.
3. **.md↔Code-Verify (docs-only):** Root-`CLAUDE.md` Current-state (muss M1-geschlossen +
   V3-aktiv zeigen **[VERIFY]**), `ROADMAP.md` (Meta-Strang + V3-Sektion), `docs/INDEX.md`,
   `AGENTS.md`-Präsenz. Drift fixen; dated Snapshots nie editieren.

**Akzeptanz:** Baseline grün + protokolliert; Root-Docs tragen V3 als aktive Phase; kein
Verhaltenscode geändert; `data/` unberührt.

---

## §4 Step 2 — Datenanalyse (Fr, read-only — das Wochentags-Kernstück)

**Output:** `phase10_v3/STEP0_DATA_ANALYSIS_2026-07-10.md` (dated Snapshot, L3, Header-Card
+ INDEX-Zeile). **Nichts am laufenden Bot ändern** — Lücken werden identifiziert und als
Wiring-Anforderungen an §7 übergeben, nie sofort gefixt.

**Quellen (Pfade [VERIFY]):** `data/state/debate_log.json` · `data/state/research_health.jsonl` ·
`data/state/scheduler_state.json` · `data/trading_bot.sqlite` — SQLite ausschließlich via
`sqlite3.connect("file:data/trading_bot.sqlite?mode=ro", uri=True)` (Bot läuft parallel).

**Inhalt (drei Abschnitte):**

**(a) V2-Baseline-Auswertung:** Trades seit 2026-07-06 (`trade_outcomes`, erwartet 0 oder
wenige — bei 0 ehrlich "weiterhin offen" dokumentieren, nichts erfinden). Zyklen/Tag,
Abstains/Tag. **Variety-These:** Abstain-Quote vs. Anzahl aktiver Epics — soweit die Daten
es hergeben (`instrument_universe`-Status-Historie **[VERIFY Spalten]**); wenn nicht
beantwortbar: als solches protokollieren, Messlücke benennen.

**(b) Abstain-Ist-Analyse:** Alle historischen Abstains aus `debate_log.json`
(decision==ABSTAIN), `research_health.jsonl` (Events: keine Kandidaten, Preflight-Fails,
Universe-Zustände **[VERIFY Event-Namen]**) und Scheduler-State manuell auf die
`REASON_*`-Taxonomie (S1, 12 Werte) mappen → **empirische Häufigkeitstabelle**. Welche
Reasons dominieren? Welche kommen real nie vor? Das gewichtet, wo Lessons Wert haben
(informiert V3-D8-Stage-Filter und die Woche-2-Review).

**(c) Gap-Check (Feld-Mapping-Tabelle):** Für jedes Feld des S2-Contracts (`outcome`, `epic`,
`failed_gate`, `veto`, `debate_decision`, `research_empty`, `error`) und jedes Block-B-Feld
(Bull/Bear-Argumente, Judge-Confidence, `rounds_used`, VETO-Ergebnisse, Gate-Ergebnisse,
spread/Quote zum Entscheidungszeitpunkt, Bars/ATR-Verfügbarkeit): **loggt der Bot es heute?
Wo? In welcher Form? Hat der Executor es zur Naht-Zeit im Scope?** Fehlende Felder →
Liste "muss an der Naht assembliert/durchgereicht werden" (Input für §7.2).
Zusatzfrage für Paper-Trades: liegt zum Debate-Abstain-Zeitpunkt eine frische Quote vor,
oder braucht `open_shadow_pair` einen eigenen Quote-Call? **[VERIFY]**

**Kein Backfill historischer Abstains in die neue Tabelle** (YAGNI) — dieses Doc IST der
historische Record; die Tabelle füllt sich ab Montag-Restart.

**Akzeptanz:** Doc committet (docs-only); Häufigkeitstabelle + Feld-Mapping vollständig;
Bot lief währenddessen ununterbrochen weiter.

---

## §5 Step 3 — Contract-Verifikation (Fr, read-only Code-Lektüre + docs)

Die Specs S1–S7 haben ihre Input-Contracts **bewusst selbst definiert** (deterministische
Trials). Vor dem echten Build: Contracts gegen As-Built abgleichen. **Output:** Abschnitt
`## Verified anchors (2026-07-10)` in `phase10_v3/CLAUDE.md` — je Zeile
`Contract-Element → Datei:Symbol (Zeile)`. Dieser Annex ist ab WE 1 die bindende Anker-Liste.

Zu verifizieren (Lesen, nichts ändern):

1. **P5-Executor** `phase5_execution/execution/executor.py` **[VERIFY]**: alle
   NO_TRADE-Rückgabepfade (Gate-Fail, VETO-Fail, Debate-ABSTAIN, Error-fail-closed);
   exakte Stelle + Signatur der `reward_sink`- und `debate_runner`-Nähte (Konstruktor vs.
   `run()`-Param); welche Objekte (candidate, price_env, Gate-/VETO-Resultate) an jedem
   NO_TRADE-Punkt im Scope sind.
2. **P8-Wiring** `phase8_scheduler/scheduler/runner.py` + Config-Modul **[VERIFY]**: wo der
   Executor gebaut wird, wo `reward_sink`/`debate_runner` injiziert werden, wie Config-Keys
   deklariert sind, wo der Loop-Tick für den Paper-Tracker andocken kann,
   Observability-Event-Konvention (`research_health.jsonl`-Writer).
3. **P2-Migrationsframework** `phase2_persistence/` **[VERIFY]**: Migrations-Verzeichnis +
   Namenskonvention (`004_…` → nächste Nr.), Runner-Mechanik, ob `db.py`-Whitelist für
   Own-Connection-Stores irrelevant ist (UniverseStore-Präzedenz prüfen).
4. **UniverseStore** `phase9_universe/universe/store.py`: Connection-Muster,
   `ensure_schema`-Praxis neben Migration (übernehmen wie vorgefunden), Fehler-Mapping.
5. **P6-Debatte** `phase6_debate/debate/` **[VERIFY]**: Shape des Debatte-Resultats
   (decision, confidence, rounds_used — sind Bull/Bear-Argumente/Digests zugänglich?);
   kleinste **additive** Reuse-Form für einen Paper-Modus-Call (§11.3).
6. **Sizing/SL-TP** `phase5_execution/` (Gate 4 / `filters.calc_position_size` o. ä.
   **[VERIFY]**): deterministische Funktion(en) für Stop-Distanz/Limit-Distanz + Time-Stop-
   Dauer (Config-Key), die `open_shadow_pair` identisch aufruft.
7. **Bars** `phase1_broker_wrapper` `get_ohlcv`-Signatur (Auflösung, max Fenster,
   Rate-Limits **[VERIFY]** — 403-Allowance-Incident 07-06 im Kopf behalten) und ob der
   Momentum-VETO-Bar-Fetch im Executor-Scope wiederverwendbar ist (§10.2-Regel).
8. **P4-Prompt-Builder** (S6-Anker): Symbol des Lesson-Blocks (`get_recent_lessons`-Muster)
   **[VERIFY]**.
9. **P7-Reflect-Muster** `phase7_reward/reward/brain.py` **[VERIFY]**: LLM-Client-Reuse-Form
   (`research.LLMClient`-Adapter, Timeout, best-effort-Konvention) — `reflect.py` spiegelt sie.

**Akzeptanz:** Annex committet; jeder S-Spec-Contract und jedes Block-B-/Paper-Feld hat
entweder einen realen Anker oder einen expliziten Eintrag "an Naht assemblieren".

---

## §6 Step 4 — Migration 005 + Stores (WE 1)

**⚠ Operator-Checkliste vor Migration (WE, Bot gestoppt):** Scheduler steht (Markt zu
bestätigen) → **Backup** `cp data/trading_bot.sqlite data/trading_bot.sqlite.bak-2026-07-11`
(gitignored) → Migration ausführen → Schema verifizieren → Backup-Protokoll in CLAUDE.md.

**Datei:** `phase2_persistence/persistence/migrations/005_v3_learning.sql` **[VERIFY Pfad/Konvention]**.
Eine Migration, alle V3-Tabellen (Block B/Paper-Write-Pfade kommen erst WE 2 — Schema jetzt):

1. **`abstain_records`** — Spalten exakt `AbstainRecord.to_row` (S1): `record_id TEXT PRIMARY KEY`,
   `created_utc TEXT NOT NULL`, `epic TEXT`, `stage TEXT NOT NULL`, `reason TEXT NOT NULL`,
   `detail TEXT NOT NULL DEFAULT ''`, `context_json TEXT NOT NULL DEFAULT '{}'`,
   `lesson TEXT`, `lesson_extracted INTEGER NOT NULL DEFAULT 0`.
   Index auf `created_utc`, Index auf `reason`.
2. **`paper_trades`** — `paper_id TEXT PRIMARY KEY`, `abstain_record_id TEXT NOT NULL`,
   `variant TEXT NOT NULL` (`SHADOW_BUY|SHADOW_SELL|COUNCIL_PICK`), `epic TEXT NOT NULL`,
   `direction TEXT NOT NULL` (`BUY|SELL`), `created_utc TEXT NOT NULL`,
   `entry_level REAL NOT NULL`, `stop_distance REAL NOT NULL`, `limit_distance REAL`,
   `time_stop_utc TEXT NOT NULL`, `status TEXT NOT NULL DEFAULT 'OPEN'`
   (`OPEN|RESOLVED|EXPIRED_UNRESOLVED`), `resolved_utc TEXT`, `exit_reason TEXT`
   (`SL|TP|TIME_STOP`), `exit_level REAL`, `pnl_points REAL`, `r_multiple REAL`,
   `council_confidence INTEGER`, `lesson TEXT`, `lesson_extracted INTEGER NOT NULL DEFAULT 0`,
   `context_json TEXT NOT NULL DEFAULT '{}'`. Index auf `status`, `created_utc`.
3. **`market_regime_snapshots` / `decision_context`** — existieren als P2-Placeholder
   **[VERIFY Schema in `001_initial.sql` + evtl. vorhandene Writes in `db.py`]**. Benötigte
   Spalten (Soll):
   - `market_regime_snapshots`: `snapshot_id TEXT PK`, `created_utc`, `epic`,
     `spread_pct REAL`, `atr_points REAL` (nullable), `range_pct REAL` (nullable),
     `time_bucket TEXT`, `regime_tag TEXT` (nullable, observe-only), `data_source TEXT`
     (`ig_bars|yfinance|quote_only`), `degraded INTEGER DEFAULT 0`,
     `decision_context_id TEXT` (nullable Link).
   - `decision_context`: `context_id TEXT PK`, `created_utc`, `epic`,
     `candidate_json TEXT`, `bull_summary TEXT`, `bear_summary TEXT`,
     `judge_decision TEXT`, `judge_confidence INTEGER`, `rounds_used INTEGER`,
     `veto_results_json TEXT`, `gate_results_json TEXT`, `outcome TEXT` (`TRADE|NO_TRADE`),
     `deal_id TEXT` (nullable), `abstain_record_id TEXT` (nullable).
   Fehlende Spalten **additiv** via `ALTER TABLE … ADD COLUMN` in 005 (nie droppen);
   passt der Placeholder gar nicht **[VERIFY]**, entscheidet CC dokumentiert (bevorzugt:
   Placeholder additiv erweitern; nur bei komplett leerem, nie beschriebenem Placeholder
   ohne Code-Referenzen: DROP+CREATE in 005 mit Begründung im Migrations-Kommentar).

**Stores (Own-Connection, UniverseStore-Muster):**

- `phase10_v3/abstain_lessons/store.py`: `class AbstainStore` — `__init__(self, db_path: Path)`,
  `ensure_schema() -> None` (IF-NOT-EXISTS-DDL **identisch zu 005**, praktisch für
  tmp-DB-Tests; Muster wie UniverseStore vorgefunden **[VERIFY]**), `insert(record) -> None`
  (`INSERT OR IGNORE`, idempotent), `recent(limit: int = 20) -> list[AbstainRecord]`,
  `recent_lessons(limit: int = 5) -> list[str]` (nur `lesson_extracted=1`, non-null),
  `set_lesson(record_id: str, lesson: str) -> None`,
  `count_lessons_today(now_utc: str) -> int` (für den Reflect-Cap, DB-gezählt),
  `close()`, Context-Manager. Fehler → `AbstainStoreError`.
- `phase10_v3/abstain_lessons/paper_store.py`: `class PaperTradeStore` — analog:
  `insert(trade)`, `open_trades() -> list[PaperTrade]`,
  `mark_resolved(paper_id, exit_reason, exit_level, pnl_points, r_multiple, resolved_utc)`,
  `mark_expired(paper_id, resolved_utc)`, `set_lesson(paper_id, lesson)`,
  `count_today(variant: PaperVariant | None, now_utc: str) -> int` (Caps),
  `recent_lessons(limit: int = 5) -> list[str]`. Fehler → `PaperTradeError`.

**Tests** (`phase10_v3/tests/test_store.py`, `test_paper_store.py`): tmp_path-DB,
Schema, insert/recent-Ordnung, Idempotenz, set_lesson-Filter, count_today-Grenzen
(Tageswechsel), Fehlerpfad (kaputter Pfad → typisierter Fehler).
**Gate:** `pytest phase10_v3/tests/test_store.py phase10_v3/tests/test_paper_store.py -q`
+ P2-Regression (Migration bricht nichts).

---

## §7 Steps 5–6 — Block-A-Module + Naht (WE 1)

### §7.1 Step 5 — S1/S2/S4 (exakt nach Spec, an main-Konventionen angepasst)

- **S1 `models.py` + `exceptions.py`** — Namen/Felder wörtlich aus Spec S1:
  `AbstainStage` (5 Werte), `AbstainReason` (12 Werte), `AbstainRecord` (frozen, `new`/
  `to_row`/`from_row`); `AbstainLessonError`, `AbstainStoreError`; **zusätzlich**
  `PaperTradeError(AbstainLessonError)`. Normale Projekt-Konventionen gelten (die aus M1
  bekannte bare-pytest-/`__init__.py`-Sensitivität der Specs ist auf main irrelevant —
  `__init__.py` gehören selbstverständlich dazu).
  Tests: S1-Liste (Konstruktion, frozen, Enum-Vollständigkeit, Roundtrip).
- **S2 `classifier.py`** — `classify_abstain(cycle_outcome: Mapping[str, Any]) -> AbstainRecord`,
  Helfer `_reason_from_gate`, `_reason_from_veto`; Prioritätsordnung wörtlich aus S2
  (error → research_empty → failed_gate → debate → veto → UNCLASSIFIED); unbekannte IDs →
  `REASON_UNCLASSIFIED`, wirft nie. **Der Contract bleibt wie gespecct** — die Zuordnung
  realer Executor-Felder → Contract-Keys geschieht an der Naht (§7.2), nicht im Classifier.
  Tests: table-driven alle 12 Reasons + Prioritätskonflikte + leeres Mapping.
- **S4 `reflect.py`** — `AbstainLLM(Protocol)` mit `complete(prompt, timeout_s) -> str`;
  `build_abstain_prompt(record) -> str` (deterministisch, EINE Lehre ≤2 Sätze, Deutsch);
  `validate_abstain_lesson(text) -> str` (strip, non-empty, ≤300 Zeichen, einzeilig);
  `reflect_abstain(record, llm, timeout_s: float = 20.0) -> str | None` (best-effort, jede
  Exception → `None` + stderr-Log). LLM-Anbindung: dünner Adapter über `research.LLMClient`
  nach P7-`brain.py`-Muster **[VERIFY Reuse-Form]**, Modell Haiku 4.5. **Zusätzlich**
  `build_paper_lesson_prompt(trade: PaperTrade, sibling: PaperTrade | None) -> str`
  (deterministisch; enthält beide Shadow-Seiten-Resultate, fragt EINE Lehre, Deutsch;
  Validierung via `validate_abstain_lesson`).
  Tests: S4-Liste + Paper-Prompt-Golden + Validator-Grenzfälle (301 Zeichen, Newlines).

**Gate:** `pytest phase10_v3/tests/ -q` grün.

### §7.2 Step 6 — Sink, Executor-Naht, Wiring, S7, S6-dunkel

- **`sink.py`:** `class AbstainSink(Protocol)` mit `on_no_trade(cycle_outcome) -> None`;
  `class AbstainLessonSink`:
  `__init__(store: AbstainStore, llm: AbstainLLM | None = None, paper_engine: "PaperEngine | None" = None, reflect_stages: frozenset[AbstainStage] = frozenset({AbstainStage.DEBATE}), reflect_daily_cap: int = 10)`.
  `on_no_trade` = classify → insert → (Stage in `reflect_stages` UND
  `store.count_lessons_today(...) + paper_lessons_heute < cap` **[gemeinsamer Cap, via
  beide Stores gezählt]** → reflect → set_lesson) → (reason == `REASON_DEBATE_ABSTAIN` UND
  `paper_engine` gesetzt → `paper_engine.on_debate_abstain(cycle_outcome, record)`).
  **Wirft nie in den Aufrufer** (`logger.critical`). `paper_engine` bleibt in WE 1 `None`
  (kommt WE 2) — Naht existiert ab jetzt.
- **P5-Executor-Naht [VERIFY exakter Ort aus §5-Annex]:** neuer optionaler Parameter
  `abstain_sink=None` exakt nach `reward_sink`-Muster (gleiche Ebene: Konstruktor oder
  `run()` — wie vorgefunden). An **jedem** NO_TRADE-Rückgabepfad: `cycle_outcome`-Dict
  gemäß Gap-Check-Mapping (§4c) assemblieren (Keys exakt S2-Contract; zusätzlich
  `candidate`, `price_env`/Quote-Digest in `context_json`-tauglicher Form für Paper/Block B)
  und Sink best-effort aufrufen. **Default `None` ⇒ bit-identisch (beweispflichtig).**
- **P8-Wiring [VERIFY Ort]:** Config-Keys (Namen fixiert): `enable_abstain_lessons: bool = True`,
  `enable_abstain_reflect: bool = True`, `reflect_daily_cap: int = 10`. Runner baut bei
  `enable_abstain_lessons` `AbstainStore(live_db_path)` + `AbstainLessonSink(...)` (llm nur
  wenn `enable_abstain_reflect`) und übergibt an den Executor. Observability-Event
  `abstain_recorded` (reason, stage, epic) in `research_health.jsonl` nach bestehender
  Event-Konvention **[VERIFY]**.
- **S7 `scripts/abstain_report.py`:** deterministische Zusammenfassung (Counts je
  `AbstainReason`, letzte N Records, Lesson-Anteil), `--db`-Arg, kein Netz; Paper-Sektion
  folgt WE 2 (Platzhalter `--paper` erst dann).
- **S6 dunkel:** Flag `include_abstain_lessons: bool = False` am P4-Prompt-Builder
  **[VERIFY Symbol]**; bei `True`: `AbstainStore.recent_lessons(5)` als eigener Prompt-Block
  (analog `get_recent_lessons`-Muster); Signatur sieht `include_paper_lessons: bool = False`
  bereits vor (liest dann zusätzlich `PaperTradeStore.recent_lessons`). **Default aus ⇒
  bit-identisch. Aktivierung ist ausdrücklich NICHT V3** (V3-D3).

**Tests:** Sink-Aufruf auf allen NO_TRADE-Pfaden (Stub-Executor nach P5-Testmuster
**[VERIFY]**), KEIN Aufruf auf Trade-Pfad, Default-None-Bit-Identität, Sink-Exception
erreicht Aufrufer nie, Reflect-Cap greift, Stage-Filter greift, S6-Flag an/aus +
Bit-Identität, Report-Golden gegen tmp-DB.
**Gate:** `pytest phase10_v3/tests/ phase5_execution/tests/ phase8_scheduler/tests/ phase4_research/tests/ -q` grün.

### §7.3 Step 7 — WE1-Abschluss + Montag-Restart-Beweis

Volle Regression über alle Phasen grün (Baseline-Vergleich §3.2). Commit + Push.
Root-`CLAUDE.md`-Current-state + `phase10_v3/CLAUDE.md`-Session-Block. **Montag:** Operator
startet den Scheduler regulär; Beweis = erste `abstain_records`-Rows + `abstain_recorded`-
Events im Health-Log; Zeilen wortgleich in `phase10_v3/CLAUDE.md` protokollieren.

**Akzeptanz WE 1:** Migration angewandt (Backup protokolliert); S1–S5+S7 auf main; S6
dunkel; alle Nähte default-inert bewiesen; Regression grün; Montag-Restart-Beweis erbracht.

---

## §8 Step 8 — Woche-2-Review (wochentags, docs-only)

`phase10_v3/WEEK1_REVIEW_2026-07-1X.md` (dated): Record-Verteilung je Reason vs.
Step-0-Erwartung (§4b), Stichprobe der Reflect-Lessons (Qualität, Redundanz, Pro-Trade-
Bias?), Auffälligkeiten im Health-Log. **Zweck:** Input für die spätere D3-Flip-Entscheidung
(nicht in V3) und Feinschliff der Block-B-Spalten/Paper-Parameter vor WE 2 — Abweichungen
vom Plan hier notieren, CC übernimmt sie als gelockte Korrekturen in §9–§11.

Parallel (Browser-Chat, nicht CC, optional): Block-C-UI-Mini-Konzept · konzeptionelle
Research-V4-Notizen (typisierte Signale etc.) — **ausdrücklich kein Code.**

---

## §9 Step 9 — Block B: `market_context/` (WE 2)

**Paket** `phase10_v3/market_context/`: `__init__.py`, `models.py`, `exceptions.py`,
`regime.py`, `writer.py`.

- **`models.py`:** `@dataclass(frozen=True) class RegimeSnapshot` (Felder = Tabellenspalten
  §6.3, `new(...)`-Klassenmethode uuid4+UTC, `to_row`/`from_row`);
  `@dataclass(frozen=True) class DecisionContext` (analog).
  `exceptions.py`: `class MarketContextError(Exception)`.
- **`regime.py`:** `def compute_regime_features(bars: Sequence[Mapping] | None, spread_pct: float | None, now_utc: datetime) -> RegimeSnapshot`
  — deterministisch: `atr_points` (klassisches ATR über verfügbare Bars, nullable wenn
  Bars fehlen), `range_pct`, `time_bucket` (`OPEN|MORNING|LUNCH|AFTERNOON|CLOSE`, Europe/
  Berlin-Grenzen als Konstanten), `data_source`, `degraded`.
  `def classify_regime_tag(snapshot: RegimeSnapshot) -> str | None` — simple dokumentierte
  Schwellen (`TREND|CHOP|HIGH_VOL_OPEN|LUNCH_DRIFT`), **observe-only**, `None` bei
  unzureichenden Daten. Schwellwerte als Modul-Konstanten mit Kommentar "kalibrieren nach
  Datenlage, nutzt nichts".
- **`writer.py`:** `class MarketContextWriter` (Own-Connection, Muster §6):
  `insert_snapshot(snap) -> None`, `insert_decision_context(ctx) -> None`, best-effort-
  Fassade `class ContextRecorder` mit `on_decision(decision_context_fields, regime_inputs) -> None`
  (baut beide Rows, verlinkt `decision_context_id`, wirft nie — `logger.critical`).
- **Naht:** optionaler Parameter `context_recorder=None` am P5-Executor (gleiches Muster
  wie `abstain_sink`), aufgerufen an **beiden** Ausgängen (TRADE mit `deal_id`, NO_TRADE
  mit `abstain_record_id` — Reihenfolge: Sink zuerst, dessen `record_id` dann in den
  Context). **[VERIFY aus §5-Annex, ob ein Aufruf am Zyklus-Ende genügt oder zwei
  Call-Sites nötig sind.]** P8-Config: `enable_context_persistence: bool = True`; Wiring im
  Runner. Observability-Event `context_recorded`.
- **⚠ Harte Regel Datenquellen:** **KEINE zusätzlichen IG-Calls nur für Snapshots.**
  Bars kommen ausschließlich aus dem, was der Zyklus ohnehin gefetcht hat (Momentum-VETO-
  Bars, falls im Scope **[VERIFY §5.7]**) — sonst bleiben `atr_points`/`range_pct` NULL und
  `data_source='quote_only'`. Der 403-Allowance-Incident wiederholt sich nicht wegen
  Observability.

**Tests:** Feature-Golden (ATR-Handrechnung), time_bucket-Grenzen, regime_tag-Schwellen,
Writer-tmp-DB + Link-Integrität, Recorder wirft nie, Executor-Naht Default-None-Bit-
Identität, Regression P5/P8.
**Gate:** `pytest phase10_v3/tests/ phase5_execution/tests/ phase8_scheduler/tests/ -q`.

---

## §10 Step 10 — Paper-Pipeline (WE 2)

### §10.1 `paper.py` — Modelle + deterministischer Kern

- `class PaperVariant(str, Enum)`: `SHADOW_BUY`, `SHADOW_SELL`, `COUNCIL_PICK`.
- `class PaperExit(str, Enum)`: `SL`, `TP`, `TIME_STOP`.
- `@dataclass(frozen=True) class PaperTrade` (Felder = Tabelle §6.2, `new(...)`,
  `to_row`/`from_row`).
- `def open_shadow_pair(abstain_record_id: str, epic: str, quote: Mapping[str, float], stop_distance: float, limit_distance: float | None, time_stop_utc: str, now_utc: str) -> list[PaperTrade]`
  — pure: SHADOW_BUY mit `entry_level=quote["ask"]`, SHADOW_SELL mit `entry_level=quote["bid"]`
  (Spiegel der P7-`open_level`-Rekonstruktion). Distanzen/Time-Stop kommen von der
  **identischen deterministischen Sizing-/Config-Logik des realen Pfads** — Aufrufer
  (PaperEngine) ruft dieselben Funktionen **[VERIFY Symbole aus §5.6]**.
- `def resolve_paper_trade(trade: PaperTrade, bars: Sequence[Mapping]) -> tuple[PaperExit, float]`
  — pure: Bars ab `created_utc` chronologisch; first-touch High/Low gegen virtuelles
  SL-/TP-Level (direction-korrekt); **SL und TP in derselben Bar ⇒ konservativ SL**;
  kein Touch bis `time_stop_utc` ⇒ `TIME_STOP` zum Close der letzten Bar ≤ time_stop;
  Rückgabe `(exit_reason, exit_level)`. `pnl_points` direction-signiert,
  `r_multiple = pnl_points / stop_distance`. Bars unzureichend (Lücke über Entry oder
  Time-Stop hinaus) ⇒ Aufrufer setzt `EXPIRED_UNRESOLVED` — **nie raten.**

### §10.2 `PaperEngine` + Tracker (Wiring)

- `class PaperEngine` (in `paper.py`):
  `__init__(store: PaperTradeStore, quote_fetch: Callable[[str], Mapping], sizing_fn: Callable[..., ...] [VERIFY], config: PaperConfig, debate_caller: "PaperDebateCaller | None" = None)`.
  `on_debate_abstain(cycle_outcome, record) -> None` (best-effort, wirft nie):
  wenn `enable_paper_trades`: frische Quote holen (**ein** Call, nur bei Debate-Abstain —
  bewusst erlaubt, im Gegensatz zur §9-Regel: Frequenz ≤ Debate-Abstains/Tag, und ein
  staler Entry würde jedes R-Multiple korrumpieren) → Shadow-Pair bauen + insert →
  optional Council-Pick (§10.3).
- `class PaperTradeTracker`:
  `__init__(store: PaperTradeStore, bar_fetch: Callable[[str, ...], Sequence[Mapping]] [VERIFY get_ohlcv-Signatur], llm: AbstainLLM | None, reflect_cap_check: Callable[[], bool])`.
  `tick(now_utc) -> None`: `open_trades()` mit `time_stop_utc <= now` → **ein**
  `get_ohlcv`-Call je betroffenem Epic (Auflösung 1MIN, Fenster Entry→TimeStop
  **[VERIFY API-Limits; reicht das Fenster nicht: gröbere Auflösung + `degraded`-Vermerk
  in context_json]**) → `resolve_paper_trade` je Trade → `mark_resolved` →
  Lesson-Reflect für das **Paar** (ein Call via `build_paper_lesson_prompt`, Sibling
  mitgeben; Cap-geteilt mit Abstain-Reflect via `reflect_cap_check`) → Observability-Event
  `paper_resolved`. Best-effort; Fehler je Trade isoliert (`logger.critical`), Tick läuft weiter.
- **P8-Wiring:** Config-Keys `enable_paper_trades: bool = True`,
  `enable_paper_debate: bool = False`, `paper_debate_daily_cap: int = 3`.
  Runner baut PaperEngine (in den Sink injiziert, §7.2-Naht) + Tracker; `tracker.tick(now)`
  im Scheduler-Loop nach dem regulären Zyklus **[VERIFY Andockpunkt aus §5.2]**; Tick auch
  außerhalb des Handelsfensters erlaubt (Auflösung braucht nur historische Bars).
  Observability-Events `paper_opened`, `paper_resolved`, `paper_expired`.

### §10.3 Council-Paper-Call (sekundär, Flag default AUS)

- `class PaperDebateCaller` (in `paper.py`): `request_pick(candidate_digest: Mapping) -> tuple[str, int] | None`
  — kleinste **additive** Reuse-Form der P6-Debatte **[VERIFY aus §5.5: bevorzugt neuer
  Builder/Param in `phase6_debate/`, null Diff am Live-Debattenpfad]** mit explizitem
  Paper-Framing im Prompt: *"PAPER-MODUS: kein echtes Geld. ABSTAIN ist nicht verfügbar —
  wähle BUY oder SELL und begründe in einem Satz."* Code-seitige Validierung: Richtung ∈
  {BUY, SELL}, Confidence ∈ [0,100]; alles andere ⇒ `None` (kein COUNCIL_PICK-Row, still).
  Cap via `PaperTradeStore.count_today(COUNCIL_PICK)`. **Output landet ausschließlich als
  `paper_trades`-Row** — strukturell unmöglich, dass er eine Order berührt.

### §10.4 Trennungs-Garantien (Tests, nicht Prosa)

- `reward/`- und `confidence/`-Code wird **nicht angefasst** (strukturelle Trennung).
- Integrationstest: DB mit N echten `trade_outcomes` + M `paper_trades` → Confidence-N
  und Score-Reads identisch zu "ohne paper_trades" (Golden).
- Test: `PaperEngine` erhält VETO-/Gate-Abstain-Records → **kein** Insert (V3-D5-Guard
  liegt doppelt: im Sink-Trigger UND als Assertion in `on_debate_abstain`).
- Test: kein Symbol aus `paper.py` importiert `place_order`/Broker-Order-Pfad (Import-Scan).

**Tests gesamt §10:** Resolution-Golden-Tabelle (SL-first, TP-first, Same-Bar⇒SL,
TIME_STOP, Bars fehlen⇒EXPIRED), Shadow-Pair-Konstruktion (Entry-Seiten, Distanzen),
Tracker-Tick-Idempotenz (Doppel-Tick resolved nicht doppelt), Caps (Debate 3/Tag,
Reflect geteilt 10/Tag, Tageswechsel), Council-Validierung fail-closed, Sink-Integration
end-to-end (Debate-Abstain → Record + 2 Shadow-Rows), volle Regression.
**Gate:** `pytest phase10_v3/tests/ phase5_execution/tests/ phase6_debate/tests/ phase8_scheduler/tests/ -q` grün.

---

## §11 Step 11 — Post: Doku-Sync + Handover (WE 2)

`abstain_report.py` um `--paper`-Sektion erweitern (Counts je Variant/Exit, Abstain-
Validierungsquote: beide Shadows negativ = Abstain korrekt). ROADMAP: V3-Sektion mit
As-Built-Status. Root-`CLAUDE.md` Current-state. `phase10_v3/CLAUDE.md` Status +
`## Session stopped` (Rotationsregel). INDEX vollständig. Montag-Restart-Beweis Runde 2
(erste `paper_trades`- + Context-Rows) protokollieren. Handover-Notiz an den Folge-Chat:
offene Items = D3-Flip-Review (nach ~20 Lessons), Block-C-Entscheidung, V4-Gates
(Regime-Nutzung, typisierte Signale, Embeddings), Watch-Items aus Kickoff §5 unverändert.

---

## §12 Cross-Phase-Edit-Register (main)

| Phase/Ort | Änderung | Charakter |
|---|---|---|
| `phase2_persistence/` | Migration `005_v3_learning.sql` (2 neue Tabellen + additive ALTERs an 2 Placeholdern) | additiv; `db.py` unberührt **[VERIFY]** |
| `phase4_research/` | Prompt-Builder-Flag `include_abstain_lessons=False` (+ `include_paper_lessons=False`) | additiv, default-inert |
| `phase5_execution/` | Executor-Params `abstain_sink=None`, `context_recorder=None` + `cycle_outcome`-Assembly an NO_TRADE-Pfaden | Default `None` ⇒ bit-identisch (Test) |
| `phase6_debate/` | kleinste additive Paper-Modus-Reuse-Form **[VERIFY Shape]** | additiv, Live-Debattenpfad null Diff |
| `phase8_scheduler/` | Config-Keys (7), Wiring (Sink/Recorder/Engine/Tracker), Tracker-Tick im Loop, Observability-Events | Flags default wie §0/§7/§9/§10 |
| `phase10_v3/` | komplett neu (CLAUDE.md, abstain_lessons/, market_context/, scripts/, tests/, 2 dated Docs) | additiv |
| Root/Docs | ROADMAP-V3, INDEX-Zeilen, Header-Cards, Root-CLAUDE.md Current-state | docs-only |
| alle übrigen Phasen | **keine Änderung** (insb. `phase7_reward/`, VETOs, Gates, Order-Pfad) | — |

## §13 Geparkt (bewusst NICHT V3)

- **Block C / UI** — inkl. Nikinger-Frage "Paper-Trade-Entscheidung in der UI?": vorerst
  Operator-Kontrolle via Config-Flags + P8-Command-File-Pfad (Hook existiert); UI-Toggle +
  Paper-/Abstain-Anzeige = Block-C-Kandidatenliste für einen eigenen Mini-Plan nach A+B.
- **S6-Aktivierung** (D3-Flip) — nach Lesson-Review, eigener Operator-Schritt.
- **Regime-Nutzung, typisierte Signale, `lesson_embeddings`, Research-/Broker-Layer-Umbau** — V4+.
- **M2** — geparkt (Closeout §3), frühestens Wochentags-Abende nach V3-Start, kein Blocker.
- Watch-Items unverändert: Breaker-Fire 5b · point_value-Hard-Confirm vor Live ·
  yFinance-Root-Cause · Decision H.

## §14 Drop-Order unter Zeitdruck (fixiert)

1. **Council-Paper-Call (§10.3) fällt zuerst** (Flag bleibt ohnehin default aus — Naht
   `debate_caller=None` genügt).
2. **Paper-Tracker/Engine (§10.1–10.2) rutscht als Ganzes auf WE 3** (Schema liegt ab WE 1,
   nichts bricht).
3. **Block B (§9) fällt nie unter `decision_context`-Minimum** (Snapshots dürfen notfalls
   auf `quote_only` degradieren).
4. Block A und die Trennungs-Garantien (§10.4) sind unverzichtbar — wenn die wackeln,
   wird gestoppt, nicht gestutzt.

---

> **Definition of Done V3:**
> (1) `STEP0_DATA_ANALYSIS`-Doc committet VOR WE 1 (Git-History).
> (2) Migration 005 angewandt (Backup protokolliert); `abstain_records` füllt sich ab
> Montag-Restart — Beweiszeilen protokolliert.
> (3) S1–S5+S7 auf main, S6 dunkel; alle neuen Nähte default-inert mit Bit-Identitäts-Tests;
> volle Regression grün (Baseline §3.2).
> (4) Block-B-Writer live (Regime- + Context-Rows entstehen); keine zusätzlichen IG-Calls
> nur für Snapshots.
> (5) Paper-Pipeline: Shadow-Pair bei Debate-Abstain, deterministische Auflösung,
> `EXPIRED_UNRESOLVED` statt Raten; Council-Call hinter Flag+Cap; Trennungs-Garantien als
> grüne Tests (Confidence-N unberührt, kein Order-Pfad-Import).
> (6) Keine VETO-/Gate-/Order-Pfad-Änderung; Live-Baseline wochentags nie berührt.
> (7) Doku: INDEX/Header-Cards/ROADMAP/Session-Rotation konsistent; Handover-Notiz an den
> Folge-Chat.
