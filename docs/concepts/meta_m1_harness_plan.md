---
status: plan (ausführungsreif)
purpose: Meta-Phase M1 — Harness-Unabhängigkeit (Build-Front). Vorregistriertes Bake-off Claude Code vs. OpenCode + kalter P4/P6-Provider-Fallback. Direkt an Sonnet in Claude Code übergebbar.
read-when: Ausführung der Meta-Phase M1; NICHT bei Session-Start anderer Phasen
detail: L2
up: ./CLAUDE.md
updated: 2026-07-08
---

# Meta-Phase M1 — Harness-Unabhängigkeit (Build-Front)
## Detaillierter Implementierungsplan für Claude Code

> **Author:** M1-Browser-Planungschat, 2026-07-08.
> **Audience:** Claude Code (Sonnet). Dieser Plan ist ausführungsreif — Entscheidungen sind
> gelockt, Schritte sequenziert, Namen fixiert. Nichts hier muss neu hergeleitet werden.
> **Inputs:** `PHASE10_META_KICKOFF_HANDOVER.md`, `docs/concepts/meta_phase_unabhaengigkeit_konzept.md`,
> Nikinger-Locks 2026-07-08 (Δ, P, Kosten, Budget, Harness-Set, Modell, Testfeld, Fallback-Scope).
> **Drift-Konvention:** Alles, was gegen den echten Repo-Stand geprüft werden muss, ist als
> **[VERIFY]** markiert — bei Ausführung verifizieren, nie als gesichert übernehmen. Der
> Planungschat hatte nur einen teilweise veralteten Projekt-Snapshot; **Code ist Wahrheit.**
> **Doc-Layers-Konvention gilt:** jede neue `.md` bekommt eine L1-Header-Card (≤15 Zeilen YAML)
> und einen One-Liner in `docs/INDEX.md` **im selben Commit**; Session-Rotationsregel beachten.

---

## §0 Mission + gelockte Entscheidungen

**Mission M1:** Eine vorregistrierte Messung, ob der Bot-Code mit einem offenen Harness
(OpenCode) statt Claude Code gebaut werden kann — plus, unabhängig vom Ausgang, zwei
Feuerlöscher: (a) ein Harness-neutraler Kontext-Einstieg (`AGENTS.md`), (b) ein getesteter,
**kalter** provider-agnostischer LLM-Fallback für P4/P6. **Kein Bot-Feature. Kein Umbau der
Live-Pfade.** Der Phase-9-Live-Test bleibt vollständig unberührt.

**⚠ Zentrale, vorab bekannte Konsequenz (kein Bug, kein Grund zum Anpassen):** Mit den
vorregistrierten Werten gilt `E = 73,50 € < M = 120 €` — die Migrationsentscheidung ist
damit **bereits determiniert: KEINE Migration**, unabhängig vom Messergebnis. Der Bake-off
wird trotzdem in vollem Umfang durchgeführt: sein Zweck ist der **Feuerlöscher-Test des
Build-Pfads** (belastbare Zahl für einen Zwangsfall + Nachweis der Kontext-Portabilität),
nicht mehr Entscheidungsinput. Δ/X/M nach Sicht von Ergebnissen zu ändern ist verboten
(Anti-Shopping, Konzept §4).

### Gelockte Entscheidungen (Nikinger, 2026-07-08)

| # | Thema | Lock |
|---|---|---|
| M1-D1 | Vorregistrierung | **Δ = 10 pp** `gate_pass_rate`-Abstand (Auflösung bei 10 Trials/Harness = 10 pp). **P = 35 %**, Ausfallkosten (2 Wochen) = **210 €** (14 d × 1 h × 15 €) → **E = 73,50 €**. Migrationskosten **M = 120 €** (8 h × 15 €). Regel: **migrieren nur wenn Gap ≤ Δ UND E ≥ M.** Werte stehen VOR der ersten Zahl; `META_M1_PREREGISTRATION.md` wird vor jedem Trial committet und danach nie editiert (nur superseded). |
| M1-D2 | Strang & Namen | Eigener **Meta-Strang „M"**, hochzählbar (M2, M3, …). Verzeichnis `meta_m1_harness/`, Doku-Präfix `META_M1_*`. Funktionale Nummerierung unangetastet: Phase 10 = V3, Phase 11 = V4 bleiben wie in ROADMAP gelockt. |
| M1-D3 | Harness-Set | **Claude Code (Referenz) vs. OpenCode (Challenger).** Aider nur als Ersatzkandidat, falls OpenCode am Setup-Smoke (§8, S0) irreparabel scheitert — dann Operator-Entscheidung, kein Auto-Swap. |
| M1-D4 | Modell fixiert | **Sonnet 5, Effort Medium, in beiden Harnessen** (reale Execution-Config des Projekts). Exakter Model-String **[VERIFY]** bei Ausführung (`claude --help` / OpenCode-Modellliste). Ist Effort in OpenCode nicht settbar **[VERIFY]**: beide Harnesse auf das nächste gemeinsam settbare Setting stellen; wenn keines existiert, beide auf Default und als Validity-Note in `META_M1_RESULTS.md` dokumentieren. Temperatur/Toolset so weit wie möglich angleichen, Abweichungen dokumentieren. |
| M1-D5 | Auth | **Kein Subscription-Plugin** (Anthropic-Legal-Request PR #18186; ToS-Risiko trifft den eigenen Account). Beide Harnesse laufen in Messläufen auf **demselben separaten Anthropic-API-Key**. ~~`ANTHROPIC_API_KEY` nur als Env in der Bake-off-Shell, nie in Dateien~~ — **korrigiert 2026-07-08 (Nikinger-Override):** auch kein Shell-Env-Export. Derselbe Keyring-Ansatz wie beim Bot selbst — eigener dedizierter Keyring-Service (`trading-bot-bakeoff-runner`, seed via `meta_m1_harness/bakeoff/store_bakeoff_key.py`), vom Runner (`harness_bakeoff.py`) pro Subprocess-Call frisch geholt und nur in dessen eigenes Environment gegeben, nie in die interaktive Operator-Shell exportiert. Drei getrennte Keyring-Namespaces (live `tradingbot`, fork-neutralisiert `trading-bot-bakeoff-void`, bakeoff-Runner `trading-bot-bakeoff-runner`) — keine Vermischung möglich. Trials nur **außerhalb des Handelsfensters** (§9 Offhours-Guard). |
| M1-D6 | Budget | **50 € hart** für API-Spend der Messläufe + Smokes. Referenz-Build (§8b) läuft über die normale Claude-Code-Subscription-Session (= gewöhnliche Dev-Arbeit, kein API-Spend). Budget-Guard im Runner; bei Erreichen: sauberer Abbruch + Report mit Teilergebnis. |
| M1-D7 | Testfeld | **Abstain-/No-Trade-Lessons-Modul** (V3-Item, vorgezogen als Messobjekt). Ziel-Verzeichnis im Fork: `phase10_v3/` mit Paket `abstain_lessons/`. Spec-Suite S1–S7 dient **doppelt**: Messinstrument jetzt, realer Build später (der echte Build auf `main` ist NICHT Teil von M1 — er gehört dem V3-Chat, der die Specs übernimmt/anpasst). |
| M1-D8 | Isolation | Wegwerf-Fork außerhalb des Live-Trees, `git remote remove origin`, **Keyring-Service-Namen im Fork neutralisiert** (fail-fast statt Live-Creds), `git reset --hard` + `clean -fdq` zwischen Trials, `assert_clean_repo`-Guard. Live-Repo/DB/State/Keyring des Phase-9-Laufs sind unerreichbar zu machen, nicht nur „nicht angefasst". |
| M1-D9 | Messdesign | **S1–S5 gemessen** (N = 5) × **2 Repeats** × 2 Harnesse = **20 Trials**, jeder Trial startet von Tag `base-(k−1)`. S6–S7 nur im Referenz-Build (Modul-Vollständigkeit + weitere base-Tags, ungemessen). Primärmetrik `gate_pass_rate`; sekundär `edit_failures`, `wall_seconds`, `usage_tokens`, `turns` (wo verfügbar). **Rausch-Regel:** Innerhalb-Harness-Varianz > Zwischen-Harness-Abstand ⇒ Ergebnis = Rauschen. |
| M1-D10 | P4/P6-Kalt-Fallback | In Scope (Konzept-DoD). `OpenAICompatLLMClient` via **OpenRouter** in `phase4_research/research/` — **rein additiv, null Diff am Live-Pfad** (kein Config-Key, kein Default-Wiring; Wechsel-Anleitung nur als Doku). Deckt P6 automatisch mit ab (P6 reused `research.LLMClient`, dokumentierte Ausnahme Decision F/P6). Mocked Unit-Tests + genau **ein** realer Operator-Smoke-Call durch den P4-Validator. Modellwahl bei Ausführung nach aktuellem OpenRouter-Katalog **[VERIFY]**. |
| M1-D11 | AGENTS.md | Repo-Root auf `main`: Pointer auf `CLAUDE.md` + Doc-Layers-Navigation + **explizite** „@ref on need-to-know"-Anweisung (Frontmatter-Link-Graph wird von fremden Harnessen NICHT auto-geparst — Konzept Decision E). Portabilitäts-Nachweis = qualitativer Annex in `META_M1_RESULTS.md` (hat OpenCode die Navigation in den Trials befolgt?). |
| M1-D12 | Decision H (Laufzeit-Swap) | **Vertagt.** Der echte P4/P6-Modelltausch ist NICHT Teil von M1. M1 liefert nur den kalten Fallback (M1-D10). |
| M1-D13 | Out of Scope | V2-Baseline-Auswertung (echter Trade + Variety-These) ist ausdrücklich **nicht** M1 — offenes Item, separater docs-only-Auftrag nach Ende des Baseline-Laufs (§3 legt die Merker-Notiz an). |

### Leitplanken (unverändert, bestätigt)

Kein neues AI im Bot-Code dieser Phase (das Testfeld-Modul hat genau EINE AI-Naht, `reflect_abstain`,
best-effort und default-aus — Spiegel des P7-Musters) · AI-Output triggert nie eine Order ·
VETOs/Gates unantastbar · Credentials nur im Keyring bzw. Session-Env (nie Dateien) · Live-Runs =
Operator · TDD, keine Netzwerk-Calls in Unit-Tests · atomare Commits + Commit ⇒ Note-Update ·
stderr-Logging · Doc-Layers-Konvention (Header-Cards, INDEX, Session-Rotation) · Handover nach
~20–30 Tool-Calls via `## Session stopped`.

---

## §1 Schrittsequenz (Übersicht)

| Step | Inhalt | Ort | Commit-Grenze |
|---|---|---|---|
| 0 | `meta_m1_harness/CLAUDE.md`-Skeleton + INDEX-Einträge (allererste Aktion) | main | eigener Commit |
| 1 | Housekeeping: Legacy-Grep, Regression-Baseline, .md↔Code-Verify, ROADMAP-Meta-Strang | main | 1–2 Commits |
| 2 | `META_M1_PREREGISTRATION.md` — vor jeder Messung committen | main | eigener Commit |
| 3 | Spec-Suite `meta_m1_harness/specs/S0–S7.md` | main | eigener Commit |
| 4 | Bake-off-Instrument: `bakeoff/harness_bakeoff.py` + `analyze.py` + Unit-Tests | main | eigener Commit |
| 5 | Fork-Setup + Harness-Setup + Setup-Smoke S0 (Operator + Code) | Fork | fork-lokal |
| 6 | Referenz-Build S1–S7 im Fork → Tags `base-1…base-7` | Fork | fork-lokal |
| 7 | Messläufe S1–S5 × 2 × 2 (Offhours, Budget-Checkpoints) | Fork | results in main |
| 8 | Auswertung → `META_M1_RESULTS.md` + `META_M1_DECISION.md` | main | eigener Commit |
| 9 | `AGENTS.md` auf `main` | main | eigener Commit |
| 10 | P4/P6-Kalt-Fallback: `OpenAICompatLLMClient` + Tests + Operator-Smoke | main | eigener Commit |
| Post | Doku-Sync, Session-Block, Handover | main | eigener Commit |

Reihenfolge-Begründung: 2 (Vorregistrierung) MUSS vor 6/7 in der Git-History liegen — die
History ist der Beweis gegen Confirmation-Shopping. 9/10 sind vom Bake-off unabhängig und
könnten notfalls vorgezogen werden, bleiben aber hinter 8, damit der RESULTS-Annex (D11)
die Trial-Beobachtungen einbeziehen kann.

---

## §2 Step 0 — Phasen-Skeleton (allererste Aktion)

1. `meta_m1_harness/CLAUDE.md` anlegen: Header-Card, Zweck (eine Absatz-Fassung von §0),
   Modul-Tree (specs/, bakeoff/, results/), Verweis auf diesen Plan + Konzept, leerer
   `## Session stopped`-Block.
2. `docs/INDEX.md`: One-Liner für `meta_m1_harness/CLAUDE.md` und diesen Plan (Plan-Datei
   nach `docs/concepts/meta_m1_harness_plan.md` einsortieren, falls sie dem Repo noch fehlt).
3. **[VERIFY]** `docs/DOC_LAYERS_CONVENTION.md` kurz lesen (Header-Card-Format exakt übernehmen).

**Akzeptanz:** Ein Commit; Skeleton existiert; INDEX konsistent.

---

## §3 Step 1 — Housekeeping

1. **Legacy-Grep (Ritual):** `grep -rn -i "turbo\|CALL/PUT\|pre_trade_option_check\|expected hold" --include="*.py" --include="*.md"` —
   bekannter aktiver Restbestand `turbo_candidates.json` (P5-Gate-2-Contract) bleibt; alles
   andere bereinigen oder begründet protokollieren (Commit-Message).
2. **Regression-Baseline:** volle `pytest`-Suite über alle Phasen. Erwartung **[VERIFY]**:
   P1 87 · P2 76 · P3 100 · P4 141 · P5 154 · P6 70 · P7 133 · P8 217 · P9 72 · root 77,
   alle grün. Realen Count protokollieren = Baseline für alle M1-Regressionen.
3. **.md↔Code-Verify (docs-only):** `ROADMAP.md`, `ARCHITECTURE.md`, `README.md`, Root-`CLAUDE.md`
   gegen As-Built prüfen (Stichproben: V2-Universum DB-gestützt, Migration 004, providers.py,
   Doc-Layers-Verweise). Drift fixen, wortgleiche Historie nie umschreiben.
4. **ROADMAP-Erweiterung:** neue Sektion `## Meta-Strang (orthogonal, hochzählbar)` mit
   M1-Eintrag (Ziel, DoD-Kurzform, Verweis auf Plan + Preregistration). Funktionale Phasen
   unverändert. Zusätzlich unter Phase 9 einen Merker eintragen:
   *„Offen (kein Blocker, separater docs-only-Auftrag): V2-Baseline-Auswertung — echter
   open→close-Trade unter V2-Universum + Variety-These (Abstain-Quote bei 8 Epics)."*

**Akzeptanz:** Baseline grün + protokolliert; ROADMAP trägt Meta-Strang + V2-Merker; kein
Verhaltenscode geändert.

---

## §4 Step 2 — Vorregistrierung (kritischer Commit)

`meta_m1_harness/META_M1_PREREGISTRATION.md` mit exakt diesem Inhalt (Header-Card ergänzen):

- **Hypothese H_Build** (wörtlich aus Konzept §1) + H0_Build.
- **Vorregistrierte Werte:** Δ = 10 pp · P = 0,35 · K(2-Wochen-Ausfall) = 210 € ·
  E = P × K = 73,50 € · M(Migration) = 120 €.
- **Entscheidungsregel:** migrieren ⇔ (gemessener `gate_pass`-Gap ≤ Δ) ∧ (E ≥ M).
  **Feststellung vor Messung:** E < M ⇒ Migration ist unabhängig vom Messergebnis
  ausgeschlossen; der Bake-off dient als Feuerlöscher-Test (Zahl für den Zwangsfall).
- **Rausch-Regel:** Ist die Innerhalb-Harness-Streuung der `gate_pass_rate` größer als der
  Zwischen-Harness-Abstand, wird der Abstand als „nicht unterscheidbar" berichtet.
- **Messdesign:** S1–S5, 2 Repeats, 2 Harnesse, Start je Trial von `base-(k−1)`,
  Reset-Disziplin, Modell/Effort fixiert (M1-D4), Budget-Cap 50 €.
- **Verbot:** Keine Änderung von Δ, P, K, M, Messdesign nach diesem Commit. Korrekturen nur
  als neues, dated Dokument mit Begründung (Supersede, nie Edit).

**Akzeptanz:** Eigener Commit, zeitlich VOR Step 5–7 (Git-History = Beweis).

---

## §5 Step 3 — Spec-Suite (Testfeld: Abstain-/No-Trade-Lessons)

Dateien `meta_m1_harness/specs/S0.md … S7.md`. Jede Spec ist **self-contained** (wird als
Prompt-Text in den Trial injiziert, §7) und folgt dem Format: *Ziel · Dateien · Exakte Namen ·
Tests · Gate-Kommando · Scope-Grenzen*. Die Specs definieren ihre Input-Contracts **explizit
im Text** — sie hängen bewusst NICHT an unsicheren Live-Shapes (deterministische Trials).
Der spätere echte V3-Build gleicht die Contracts dann gegen den realen Executor/Runner ab
**[VERIFY dann]**.

**Gemeinsame Konventionen aller Specs (in jede Spec-Datei als Kopfblock übernehmen):**
Python, `from __future__ import annotations`, Type-Hints, Docstrings, pytest mit Mocks (keine
Netzwerk-Calls), stderr-Logging, eine Datei = eine Verantwortung. Ziel-Paket:
`phase10_v3/abstain_lessons/` mit `tests/` daneben (`phase10_v3/tests/`).

### S0 — Setup-Smoke (ungemessen, nur §8a)
Triviale Aufgabe zur Harness-Verifikation: Datei `phase10_v3/smoke.py` mit
`def smoke() -> str: return "ok"` + Test `phase10_v3/tests/test_smoke.py`.
**Gate:** `pytest phase10_v3/tests/test_smoke.py -q` → Exit 0.

### S1 — Modelle + Taxonomie
**Dateien:** `phase10_v3/abstain_lessons/__init__.py`, `models.py`, `exceptions.py`,
`phase10_v3/tests/test_models.py`.
**Exakte Namen:**
- `class AbstainStage(str, Enum)`: `RESEARCH_EMPTY="research_empty"`, `GATE="gate"`,
  `VETO="veto"`, `DEBATE="debate"`, `ERROR="error"`.
- `class AbstainReason(str, Enum)`: `REASON_NO_CANDIDATES`, `REASON_GATE_TIME_WINDOW`,
  `REASON_GATE_CONSTRAINTS`, `REASON_GATE_SIZING`, `REASON_GATE_DIRECTION`,
  `REASON_VETO_SPREAD`, `REASON_VETO_MOMENTUM`, `REASON_VETO_STATUS_WINDOW`,
  `REASON_VETO_POSITION_CONFLICT`, `REASON_DEBATE_ABSTAIN`, `REASON_ERROR_FAILCLOSED`,
  `REASON_UNCLASSIFIED` (Werte = Name in lowercase).
- `@dataclass(frozen=True) class AbstainRecord`: `record_id: str`, `created_utc: str`,
  `epic: str | None`, `stage: AbstainStage`, `reason: AbstainReason`, `detail: str = ""`,
  `context_json: str = "{}"`, `lesson: str | None = None`, `lesson_extracted: bool = False`;
  Klassenmethode `new(...) -> AbstainRecord` (uuid4 + UTC-ISO), Methode
  `to_row() -> tuple` / Klassenmethode `from_row(row) -> AbstainRecord`.
- `exceptions.py`: `class AbstainLessonError(Exception)`,
  `class AbstainStoreError(AbstainLessonError)`.
**Tests:** Konstruktion, Frozen-Verhalten (Mutation wirft), Enum-Vollständigkeit (12 Reasons),
`new()`-Defaults, `to_row`/`from_row`-Roundtrip.
**Gate:** `pytest phase10_v3/tests/test_models.py -q`.

### S2 — Deterministischer Klassifizierer
**Datei:** `classifier.py`, Tests `test_classifier.py`.
**Input-Contract (im Spec-Text fixiert):** `Mapping[str, Any]` mit Keys
`outcome` (`"NO_TRADE"`), `epic: str|None`, `failed_gate: str|None` (`"G1".."G5"`),
`veto: str|None` (`"spread"|"momentum"|"status_window"|"position_conflict"`),
`debate_decision: str|None` (`"ABSTAIN"`), `research_empty: bool`, `error: str|None`.
**Exakte Namen:** `def classify_abstain(cycle_outcome: Mapping[str, Any]) -> AbstainRecord`;
Helfer `_reason_from_gate(gate_id: str) -> AbstainReason`,
`_reason_from_veto(veto_id: str) -> AbstainReason`.
**Prioritätsordnung (fixiert):** `error` → `REASON_ERROR_FAILCLOSED`; sonst `research_empty`
→ `REASON_NO_CANDIDATES`; sonst `failed_gate` (G1→TIME_WINDOW, G2→NO_CANDIDATES,
G3→CONSTRAINTS, G4→SIZING, G5→DIRECTION); sonst `debate_decision=="ABSTAIN"` →
`REASON_DEBATE_ABSTAIN`; sonst `veto` (Mapping s. o.); sonst `REASON_UNCLASSIFIED`.
Unbekannte Gate-/Veto-IDs → `REASON_UNCLASSIFIED` (fail-closed, wirft nie).
**Tests:** table-driven über alle 12 Reasons + Prioritätskonflikte (z. B. error UND veto
gesetzt) + unbekannte IDs + leeres Mapping.
**Gate:** `pytest phase10_v3/tests/test_classifier.py -q`.

### S3 — Persistenz (eigener Store)
**Datei:** `store.py`, Tests `test_store.py`.
**Exakte Namen:** `class AbstainStore` mit `__init__(self, db_path: Path)` (eigene
sqlite3-Connection, Muster `UniverseStore` — im Fork **nicht** ans P2-Migrationsframework
koppeln; realer Build entscheidet später Migration-Nr. **[VERIFY dann]**),
`ensure_schema() -> None` (CREATE TABLE IF NOT EXISTS `abstain_records` mit Spalten exakt
wie `AbstainRecord.to_row`, PK `record_id`), `insert(record) -> None` (idempotent via
`INSERT OR IGNORE`), `recent(limit: int = 20) -> list[AbstainRecord]` (newest first),
`recent_lessons(limit: int = 5) -> list[str]` (nur `lesson_extracted=1`, non-null lesson),
`set_lesson(record_id: str, lesson: str) -> None`, `close() -> None`, Context-Manager.
Fehler → `AbstainStoreError`.
**Tests:** tmp_path-DB, Schema-Erzeugung, insert/recent-Ordnung, Idempotenz (Doppel-Insert),
set_lesson + recent_lessons-Filter, Fehlerpfad (kaputter Pfad → AbstainStoreError).
**Gate:** `pytest phase10_v3/tests/test_store.py -q`.

### S4 — reflect-Variante (einzige AI-Naht, default aus)
**Datei:** `reflect.py`, Tests `test_reflect.py`.
**Exakte Namen:** `class AbstainLLM(Protocol)` mit
`def complete(self, prompt: str, timeout_s: float) -> str`;
`def build_abstain_prompt(record: AbstainRecord) -> str` (deterministisch, enthält reason/
stage/detail, fordert EINE Lehre in ≤2 Sätzen, Deutsch);
`def validate_abstain_lesson(text: str) -> str` (strip, non-empty, ≤300 Zeichen, einzeiliger
Absatz — sonst `AbstainLessonError`);
`def reflect_abstain(record: AbstainRecord, llm: AbstainLLM | None = None, timeout_s: float = 20.0) -> str | None`
— `llm is None` → `None` (Default-aus-Prinzip); jeder Fehler → `logger.critical` + `None`,
**wirft nie** (P7-Konvention für Lern-Writes).
**Tests:** nur Mock-LLM (kein Netz): None-Default, Happy-Path, Validator-Reject (zu lang,
leer), LLM-Exception → None + critical-Log (caplog), Timeout-Param wird durchgereicht.
**Gate:** `pytest phase10_v3/tests/test_reflect.py -q`.

### S5 — Sink + Wiring-Naht (Cross-File-Edit, realistischster Trial)
**Dateien:** `sink.py`, Tests `test_sink.py`; zusätzlich minimal-invasive Naht in
`phase5_execution/` **[VERIFY-FORK: exakter Symbolort — NO_TRADE-Rückgabepfade des
Executors]** nach dem `reward_sink`-Muster.
**Exakte Namen:** `class AbstainSink(Protocol)` mit
`def on_no_trade(self, cycle_outcome: Mapping[str, Any]) -> None`;
`class AbstainLessonSink` (`__init__(store: AbstainStore, llm: AbstainLLM | None = None)`),
implementiert `on_no_trade` = classify → insert → optional reflect → set_lesson; best-effort,
wirft nie in den Aufrufer (critical-Log). Executor-Naht: neuer optionaler Parameter
`abstain_sink=None` — **Default `None` ⇒ Verhalten bit-identisch** (beweispflichtig).
**Tests:** Sink-Aufruf auf NO_TRADE-Pfaden (Stub/Mock-Executor-Setup nach Muster der
bestehenden P5-Tests **[VERIFY-FORK]**), KEIN Aufruf auf Trade-Pfad, Default-None-Bit-
Identität, Sink-Exception erreicht Aufrufer nicht.
**Gate:** `pytest phase10_v3/tests/test_sink.py phase5_execution/tests/ -q` (neue Tests +
volle P5-Regression grün).

### S6 — Research-Injektion (nur Referenz-Build, ungemessen)
Flag-gated Prompt-Erweiterung in `phase4_research/` **[VERIFY-FORK: Prompt-Builder-Symbol]**:
`include_abstain_lessons: bool = False` (Config-Default aus ⇒ bit-identisch); bei `True`
werden `AbstainStore.recent_lessons(5)` als eigener Prompt-Block injiziert (analog
`get_recent_lessons`-Muster). Tests: Flag an/aus, Bit-Identität bei aus, P4-Regression.
**Gate:** `pytest phase10_v3/tests/test_research_injection.py phase4_research/tests/ -q`.

### S7 — Abstain-Report-CLI (nur Referenz-Build, ungemessen)
`phase10_v3/scripts/abstain_report.py`: deterministische Zusammenfassung (Counts je
`AbstainReason`, letzte N Records, Anteil mit Lesson) auf stdout, `--db`-Arg, kein Netz.
Tests: Golden-Output gegen tmp-DB. **Gate:** `pytest phase10_v3/tests/test_report.py -q`.

**Akzeptanz Step 3:** Specs S0–S7 committet; jede Spec self-contained; ein Sonnet-Executor
könnte jede Spec ohne diesen Plan lesen und bauen.

---

## §6 Step 4 — Bake-off-Instrument

**Dateien:** `meta_m1_harness/bakeoff/harness_bakeoff.py`, `analyze.py`, `preamble.txt`,
`meta_m1_harness/tests/test_bakeoff_runner.py`, `test_analyze.py`.

**`harness_bakeoff.py` — exakte Namen:**
- `@dataclass(frozen=True) class HarnessConfig`: `name: str`, `argv_template: list[str]`
  (Platzhalter `{prompt}` und `{prompt_file}`; **Model-Flag hier einbacken**, damit das
  Modell nie zwischen Harnessen driftet), `usage_regex: str | None = None` (named group
  `tokens`), `timeout_s: int = 1800` (hängender Harness = Datenpunkt, kein Retry).
- `@dataclass class TrialResult`: `harness: str`, `step: str`, `repeat: int`,
  `exit_ok: bool`, `gate_passed: bool`, `wall_seconds: float`, `edit_failures: int`,
  `files_changed: int`, `usage_tokens: float | None = None`, `error: str = ""`,
  `extra: dict = field(default_factory=dict)`.
- `@dataclass(frozen=True) class StepSpec`: `step_id: str`, `spec_path: Path`,
  `base_tag: str`, `gate_argv: list[str]`.
- Git-Isolation: `_git(repo, *args, check=True)`, `assert_clean_repo(repo)` (kein Repo /
  dirty ⇒ `SystemExit` mit `[safety]`-Meldung), `snapshot_ref(repo)`,
  `reset_to(repo, ref)` (`reset --hard` + `clean -fdq`), `changed_files(repo, ref) -> list[str]`.
- Guards: `assert_offhours(now: datetime) -> None` — verweigert Mo–Fr 08:00–18:00
  Europe/Berlin, Override nur via Env `BAKEOFF_FORCE_WINDOW=1` (bewusst hässlich);
  `class BudgetGuard` (`cap_eur: float`, `add(tokens_in, tokens_out)`,
  `add_manual_eur(eur)`, `remaining() -> float`, Überschreitung ⇒ `BudgetExceeded`).
  Preistabelle `PRICE_EUR_PER_MTOK: dict` als Konstante **[VERIFY: aktuelle Sonnet-Preise
  bei Ausführung eintragen]**; ist Usage für einen Harness nicht parsebar, fordert der
  Runner nach jedem (Harness×Step)-Block eine Operator-Eingabe des kumulierten
  Console-Spends (`add_manual_eur`).
- `def run_trial(repo: Path, harness: HarnessConfig, spec: StepSpec, repeat: int, budget: BudgetGuard) -> TrialResult`:
  `reset_to(spec.base_tag)` → Prompt = `preamble.txt` + Spec-Dateiinhalt → Harness-Subprocess
  (capture stdout/stderr) → `gate_argv` als Subprocess → Metriken sammeln → Ergebnis.
  **`edit_failures`-Definition (fixiert):** `1` wenn `exit_ok` und `files_changed == 0`
  und `gate_passed == False` (Harness meldet Erfolg, hat aber nichts geschrieben), sonst `0`.
- `def run_matrix(repo, harnesses, specs, repeats, budget, results_path) -> list[TrialResult]`:
  Reihenfolge Step-major, Harness-alternierend (Zeit-/Tagesdrift verteilt sich), JSONL-Append
  nach **jedem** Trial (`results/trials.jsonl`, ein JSON-Objekt/Zeile), Reset auch nach dem
  letzten Trial.
- `def main() -> int`: argparse `--repo` (Pflicht), `--steps S1,S2,…`, `--harness cc,oc`,
  `--repeats 2`, `--results`, `--dry-run` (druckt Matrix + argv, führt nichts aus).
- Harness-Templates als Konstanten (Shapes, **[VERIFY]** gegen `--help` beider CLIs vor dem
  ersten Trial — falsche argv misst nichts):
  `CLAUDE_CODE = HarnessConfig("claude_code", ["claude", "-p", "{prompt}", "--model", "<MODEL>", "--output-format", "json", "--dangerously-skip-permissions"])`
  — Skip-Permissions ist NUR wegen Fork-Isolation (M1-D8) vertretbar;
  `OPENCODE = HarnessConfig("opencode", ["opencode", "run", "{prompt}", "--model", "anthropic/<MODEL>"])`
  — Permission-/Effort-Parität herstellen **[VERIFY]** und in RESULTS dokumentieren.

**`preamble.txt` (verbatim):**
„Du arbeitest im Repo-Root eines isolierten Test-Forks. Implementiere exakt die folgende
Spec. Lies CLAUDE.md und referenzierte Dateien nur bei Bedarf (@ref on need-to-know).
Führe nach der Implementierung das Gate-Kommando der Spec aus und iteriere, bis es grün ist
oder du nicht weiterkommst. Ändere nichts außerhalb des Spec-Scopes. Committe nicht."

**`analyze.py` — exakte Namen:** `load_trials(path: Path) -> list[TrialResult]`,
`summarize(trials) -> dict` (je Harness: `gate_pass_rate`, Mittel/Streuung `wall_seconds`,
Summe `usage_tokens`, `edit_failures`; Gap; Rausch-Check: max. Innerhalb-Spread der
Pass-Rates über Repeats vs. Gap), `render_markdown(summary) -> str`, `main()`.

**Unit-Tests (kein Subprocess, kein Netz — `subprocess.run` gemockt):** Reset wird vor jedem
Trial und nach dem letzten aufgerufen; JSONL-Schema stabil; `edit_failures`-Logik (3 Fälle);
BudgetGuard-Trip; `assert_offhours` (innerhalb/außerhalb/Override); `assert_clean_repo`
(dirty ⇒ SystemExit); analyze-Golden.

**Akzeptanz:** `pytest meta_m1_harness/tests/ -q` grün; `--dry-run` druckt plausible Matrix.

---

## §7–§9 Steps 5–7 — Fork, Referenz-Build, Messläufe

### §7 Step 5 — Fork-Setup + Setup-Smoke (Operator + Claude Code gemeinsam)
1. Live-Zustand sichern: Baseline-Scheduler gestoppt ODER Offhours bestätigt (Checkliste).
2. `git clone ~/trading-bot ~/bakeoff/trading-bot-fork` (Pfad außerhalb des Live-Trees),
   im Fork: `git remote remove origin`.
3. **Keyring-Neutralisierung (Base-Commit im Fork):** ~~Service-Namen-Konstante ... [VERIFY:
   exaktes Symbol] ... dito für den Anthropic-Key-Service des Bots [VERIFY]~~ — **verifiziert
   2026-07-08:** es gibt genau **ein** Symbol, `SERVICE_NAME: Final[str] = "tradingbot"` in
   `phase1_broker_wrapper/broker_wrapper/credentials.py:40`, das sowohl IG-Creds als auch
   `anthropic_api_key` gemeinsam trägt (differenziert nur über den `name`-Parameter). Ein
   einziger Zeilen-Edit auf `"trading-bot-bakeoff-void"` neutralisiert beides. Commit, dann
   `git tag base-0`.
4. OpenCode installieren + konfigurieren (Modell `claude-sonnet-5`, Effort/Variant-Flag
   **[VERIFY am installierten OpenCode]** — Flag heißt `--variant`, konkreter Wert
   provider-spezifisch, siehe `harness_bakeoff.py`). ~~Provider Anthropic via
   `ANTHROPIC_API_KEY`-Env ... Claude Code: gleiche Env in der Bake-off-Shell~~ — **korrigiert
   2026-07-08 (Nikinger-Override, siehe M1-D5):** kein Shell-Env-Export. Key = der
   **separate** Bake-off-Key (Operator legt ihn in der Anthropic-Console an, dann
   `python meta_m1_harness/bakeoff/store_bakeoff_key.py` — Keyring-Service
   `trading-bot-bakeoff-runner`, getrennt vom Live-Service und vom fork-neutralisierten
   Service). `harness_bakeoff.py` holt den Key pro Subprocess-Call aus dem Keyring.
5. **Setup-Smoke:** S0 je Harness 1× via Runner (`--steps S0 --repeats 1`). Beide grün ⇒
   weiter. OpenCode irreparabel rot ⇒ Stopp, Operator entscheidet Aider-Substitution (M1-D3).

### §8 Step 6 — Referenz-Build (ungemessen)
Claude Code baut im Fork S1–S7 sequenziell in der **normalen Subscription-Session**
(gewöhnliche Dev-Arbeit, kein API-Spend): je Spec implementieren → Gate grün → Commit →
`git tag base-<k>`. Ergebnis: `base-1 … base-7`. Validity-Fußnote für RESULTS: beide
Harnesse starten Messtrials von identischen (CC-autorisierten) Basen — symmetrisch.

### §9 Step 7 — Messläufe
`python meta_m1_harness/bakeoff/harness_bakeoff.py --repo ~/bakeoff/trading-bot-fork
--steps S1,S2,S3,S4,S5 --harness claude_code,opencode --repeats 2` — außerhalb des
Handelsfensters (Guard erzwingt es). ~~`ANTHROPIC_API_KEY` gesetzt~~ — **korrigiert
2026-07-08:** kein Env-Setzen nötig/gewollt, der Runner holt den Key selbst aus dem Keyring
(`store_bakeoff_key.py` vorher einmalig ausführen, s. Step 5 Punkt 4 / M1-D5). Budget-
Checkpoints nach jedem (Harness×Step)-Block; `BudgetExceeded` ⇒ sauberer Stopp, Teilergebnis
zählt.
`results/trials.jsonl` nach `meta_m1_harness/results/` ins Haupt-Repo kopieren + committen.
**Kostenschätzung (nur Planungsgröße, keine Zusage):** 20 Trials × grob 0,5–2 € ≈ 10–40 € —
innerhalb 50 €, aber Checkpoints ernst nehmen.

**Akzeptanz Steps 5–7:** 20 Trials (oder dokumentierter Budget-Stopp) in `trials.jsonl`;
kein einziger Schreibzugriff außerhalb des Forks; Live-Lauf unberührt.

---

## §10 Step 8 — Auswertung + Entscheidung

1. `analyze.py` über `trials.jsonl` → Tabelle.
2. `meta_m1_harness/META_M1_RESULTS.md` (dated Snapshot): Zahlen, Varianz, Rausch-Check,
   Validity-Notes (Effort-/Permission-Parität, Usage-Erfassung), **Annex Kontext-Portabilität**
   (qualitativ: hat OpenCode CLAUDE.md/Doc-Layers-Navigation befolgt? Beispiele zitieren).
3. `meta_m1_harness/META_M1_DECISION.md`: Anwendung der vorregistrierten Regel — erwartetes
   Ergebnis „keine Migration" (E < M), **mit** der gemessenen Zahl als Feuerlöscher-Befund
   („im Zwangsfall ist OpenCode-Gap = X pp bekannt"). Keine Nachjustierung von Δ/M/P.

**Akzeptanz:** Beide Dokumente committet (Header-Cards + INDEX); Regel wörtlich angewandt.

---

## §11 Step 9 — AGENTS.md (main)

`AGENTS.md` im Repo-Root, ~30 Zeilen, Inhalt (sinngemäß fixiert):
Zweck (Harness-neutraler Einstieg) · „Lies zuerst `CLAUDE.md` — Single Source of Truth" ·
Doc-Layers-Navigation (INDEX → Header-Card → Body, up/down-Links statt Directory-Suche) ·
**explizit:** „Frontmatter-/@ref-Verweise werden NICHT automatisch geladen — referenzierte
Dateien on need-to-know selbst öffnen" · Working-Style-Präzedenz (getesteter Code > Konzept
> Status-Prosa) · Verbotsliste-Kurzform (Credentials, VETO-Bypass, AI-Order-Direkttrigger).
INDEX-One-Liner im selben Commit.

---

## §12 Step 10 — P4/P6-Kalt-Fallback (rein additiv)

1. **[VERIFY zuerst]:** `phase4_research/research/llm_client.py` lesen — exakte öffentliche
   Schnittstelle (Klassen-/Methodenname, Signatur, Rückgabeform inkl. token_meter-Felder,
   Exception-Typen) übernehmen. Der Adapter spiegelt sie 1:1.
2. **Neue Datei** `phase4_research/research/llm_openai_compat.py`:
   `class OpenAICompatLLMClient` — Konstruktor
   `(base_url: str = "https://openrouter.ai/api/v1", model: str, api_key_service: str = "openrouter", timeout_s: float = 60.0)`;
   Key via Keyring (Service `openrouter`, Username `api_key`, über bestehenden
   Credentials-Helper **[VERIFY API]**); HTTP via `requests` (Konvention);
   `POST {base_url}/chat/completions`; JSON-Erzwingung: `response_format={"type":"json_object"}`
   plus prompt-seitige Schema-Anweisung (Anthropic-`output_config`/`cache_control` haben hier
   kein Äquivalent — cache-Parameter werden als No-op akzeptiert, damit die Signatur passt);
   HTTP-/Parse-Fehler auf die bestehenden typisierten LLM-Exceptions mappen **[VERIFY Namen]**;
   Usage-Felder in die token_meter-Form bringen (cache-Felder = 0). Docstring enthält die
   **Wechsel-Anleitung** (welche eine Zeile im Wiring zu tauschen wäre) — mehr Wiring gibt es
   nicht: **null Diff an bestehenden Dateien.**
3. **Tests** `phase4_research/tests/test_llm_openai_compat.py` (requests gemockt): Happy-JSON,
   malformed JSON ⇒ typisierter Fehler, HTTP 429 ⇒ Rate-Limit-Typ, Timeout, Usage-Mapping,
   Key-fehlt ⇒ sauberer typisierter Fehler. Plus volle P4-Regression grün.
4. **Operator-Smoke** `phase4_research/scripts/openrouter_smoke.py`: baut einen minimalen
   research-ähnlichen Prompt, **ein** realer Call gegen OpenRouter (Modell als `--model`-Arg;
   Empfehlung bei Ausführung nach aktuellem Katalog wählen **[VERIFY]** — großes
   Open-Weight-Instruct-Modell), Output durch den echten P4-Validator **[VERIFY
   Einstiegsfunktion in `validator.py`]**, Ausgabe `PASS/FAIL` + Modell + Token. Operator
   führt aus (OpenRouter-Key vorher im Keyring hinterlegen); Ergebnis wortgleich in
   `META_M1_RESULTS.md` §Fallback protokollieren. Danach bleibt der Adapter **kalt**.

**Akzeptanz:** Adapter + Tests grün; P4/P6-Regression grün; `git diff` zeigt außer neuer
Datei/Tests/Script **keinen** Live-Pfad-Diff; Smoke-PASS dokumentiert.

---

## §13 Post — Doku-Sync + Handover

`meta_m1_harness/CLAUDE.md` Status + `## Session stopped` (Rotationsregel!); Root-`CLAUDE.md`
Current-state-Zeile für M1; ROADMAP-Meta-Strang-Status; INDEX vollständig; Abschluss-Commit.
Handover-Notiz an den V3-Chat: Specs S1–S7 liegen als geprüfter Bauplan für den echten
Abstain-Lessons-Build bereit (Contracts vor Übernahme gegen realen Executor/Runner
verifizieren).

---

## §14 Cross-Phase-Edit-Register (Haupt-Repo `main`)

| Phase/Ort | Änderung | Charakter |
|---|---|---|
| Root | `AGENTS.md` neu | additiv |
| Root/Docs | ROADMAP Meta-Strang + V2-Merker, INDEX-Zeilen, Header-Cards | docs-only |
| `meta_m1_harness/` | komplett neu (CLAUDE.md, Preregistration, Specs, bakeoff, results, RESULTS/DECISION) | additiv |
| `phase4_research/` | `research/llm_openai_compat.py`, `tests/test_llm_openai_compat.py`, `scripts/openrouter_smoke.py` | **rein additiv, null Diff an Bestandsdateien** |
| alle übrigen Phasen | **keine Änderung** (S5/S6-Nähte existieren nur im Wegwerf-Fork) | — |

## §15 Offene Items (bewusst NICHT M1)

- **V2-Baseline-Auswertung** (echter Trade + Variety-These) — separater docs-only-Auftrag
  nach Laufende; Merker steht in ROADMAP (§3.4).
- **Decision H** — echter P4/P6-Laufzeit-Swap: eigener späterer Schritt (ggf. M2).
- **Echter Abstain-Lessons-Build auf main** — gehört dem V3-Chat (Specs liegen bereit).
- **Aider** — nur Contingency (M1-D3).

---

> **Definition of Done M1:** (1) `META_M1_PREREGISTRATION.md` liegt in der Git-History VOR
> jedem Trial. (2) 20 Messtrials (oder dokumentierter Budget-Stopp) in `trials.jsonl`.
> (3) `META_M1_RESULTS.md` + `META_M1_DECISION.md` mit wörtlich angewandter vorregistrierter
> Regel. (4) `AGENTS.md` auf main. (5) `OpenAICompatLLMClient` mit grünen mocked Tests +
> dokumentiertem Operator-Smoke-PASS, null Live-Pfad-Diff. (6) Alle Regressionen grün;
> Live-Test der Phase 9 zu keinem Zeitpunkt berührt.
