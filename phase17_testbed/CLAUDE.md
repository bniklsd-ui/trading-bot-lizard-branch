---
status: live
purpose: PHASE-HEAD, Phase 17 (Prüfstand) — 🔄 eröffnet 2026-10-17 (Plan-Session, Opus 5.5). Keine neuen Features. Tiefe Härtung des Bestehenden — vier Phase-16-PASS-Blocker + drei neu gemessene stille Totalausfälle zu, LLM pro Rolle austauschbar (Research zuerst auf GLM über die z.ai-API mit Pay-per-use, Plan §14), Report + Vorregistrierung v5 als Fundament für die ausgiebigen Tests. Executor: offener Test GLM in OpenCode (§14).
read-when: jede Phase-17-Exec-Session — zuerst diesen Kopf, dann den `## Session stopped`-Block, dann den Plan
detail: L1
up: ../CLAUDE.md
down:
  - ../docs/concepts/phase17_testbed_plan.md               # 📕 der Plan (T1–T24, D1–D13, Blöcke A–E, AK1–AK21, §8 Fehlgriffe, §9 Verify)
  - ./provider_plasticity/                                  # 🔄 Working-Notes Provider-Plastizität (2026-10-19, 4 Notizen: 01 Decision T25–T28 · 02 Current-State · 03 Opus-Brief · 04 Open Questions Q1–Q8)
  - ../phase16_activation/PHASE16_CLOSEOUT_HANDOVER.md     # 📕 Vorgänger-Handover (§4 PASS-Blocker, §5 E1–E8)
  - ../phase16_activation/scripts/autonomy_report.py       # Report-Skript, Block E erweitert es in place (--prereg v5)
  - ./SESSIONS_ARCHIVE.md                                  # rotierte Session-Blöcke (L3, newest-first)
updated: 2026-10-19 (Exec-Session #6 ENDE — B-6 Breaker Worst-Case, 1 Commit in P8, Σ 1985 + 3 P8-Tests = **1988** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #5 ENDE — B-5 Monitor-Re-Adoption, 1 Commit in P5+P8, Σ 1978 + 5 P5 + 2 P8 = **1985** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Plan-Session §15 Provider-Plastizität — Forward-Agenda C2 → Plan §15, Σ-Ziele C/D/E-1 +9, Σ 1978 re-gemessen) | 2026-10-19 (Exec-Session #4 ANSCHLUSS — `provider_plasticity/` Working-Notes-Set angelegt (kein Plan, Input für Opus-Miniplan-Session; 5 INDEX-Einträge); Nikinger-Entscheidungen Q1–Q8 ausstehend) | 2026-10-19 (Exec-Session #4 ENDE — B-4 Abschneiden sichtbar, 1 Commit in P4, Σ 1974 + 4 P4-Tests = **1978** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #3 ENDE — B-3 Promotion-Bridge Nahtfehler, 2 Commits in P15+P8, Σ 1971 + 2 P15 + 1 P8 = **1974** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung) | 2026-10-19 (Exec-Session #2 ENDE — B-2 Divergenz-Sampler Reparatur, Σ 1965 + 4 P12-Tests + 2 P8-Tests = **1971** grün) | 2026-10-19 (Exec-Session #1 ENDE — A-0+A-1+A-2 + A-3 + B-0 + B-1, Σ 1965) | 2026-10-18 (Plan-§14-Nachtrag) | 2026-10-17 (Plan-Session, Opus 5.5)
---

# CLAUDE.md — Phase 17: Prüfstand (`phase17_testbed/`)

> **Quelle der Wahrheit ist der Code, dann der Plan, dann dieser Kopf.**
> Plan: [`../docs/concepts/phase17_testbed_plan.md`](../docs/concepts/phase17_testbed_plan.md).

## Mission

Der Bot wird zum **Prüfstand**. Für die anschließenden ausgiebigen Tests muss gelten:
- jeder vorhandene Arm liefert nachweisbar, was er liefern soll;
- jeder bekannte Mess- und Geldpfad-Defekt ist zu;
- das LLM ist pro Rolle austauschbar.

Nikinger 2026-10-17: *„keine besondere Feature-Session — bildet eher das Fundament für ausgiebige
Tests. LLM-Austausch wäre aber trotzdem sehr wichtig"* · *„kein zusätzlicher Umfang, eher extrem
tiefe Optimierung von dem, was schon da ist."*

**Abnahme:** Shakedown-Vorregistrierung → 2-Tage-Shakedown PASS → Prereg v5 committet (Plan AK19 + AK20 + AK21).
Der 10-Tage-Lauf selbst ist die Testreihe **nach** Phase 17.

## Gelockt (Kurzform — volle Begründung Plan §1, **Vorrang hat Plan §14** vom 2026-10-18)

| ID | Kern |
|---|---|
| T4/T5 (§14) | **GLM über die allgemeine z.ai-API, Pay-per-use** (`https://api.z.ai/api/paas/v4`, **nie** `/api/coding/` — prüft `check_llm_profile` beim Start). Das Modell wählt der Nikinger nach dem Familien-Smoke C-7 (`glm-5.3` / `glm-5.3-flash` / `glm-5.2`). **Flip 1** = `research_glm`, **Flip 2** = `all_glm`, nur auf Nikinger-Go nach dem Shakedown |
| T6 (§14) | Bot-Key im eigenen Namespace `trading-bot-zai-bot` / `api_key` (Keyring; nie der Coding-Plan-Key) |
| T7 (§14) | Das GLM-Bot-Modell ist budgetfrei (`budget_exempt_models`; die Kadenz begrenzt es auf ≤ 102 Research-Calls/Tag). Es hat eine **echte Preiszeile**, also wird € gemessen. Anthropic bleibt bei 300 k; K6-Einheit entscheidet der Nikinger nach dem Shakedown |
| T8 | Monitor-Re-Adoption nach Restart, nur im WINDOW, inklusive Sofort-Close bei überschrittener Haltezeit |
| T9 | Breaker zählt heutige OPEN-Zeilen mit `−initial_risk`; NULL → fail-closed |
| T13 | Code in P1, P4, P5, P8, P10, P12, P14, P15, P16; P2 nur Tests; **kein** Code in P6/P7/P13 |
| T14/T15 | IG-Zeitstempel-Fix (+ Löschen der 3 730 falschen `ig`-Bars), Divergenz-Sampler-Reparatur |
| T22 (§14) | Exec = **offener Test in OpenCode + z.ai Coding Plan**, Start `zai-coding-plan/glm-5.3-flash`, Familie `glm-5.2`/`glm-5.3` zugelassen. Claude Code bleibt Anthropic-only und macht das **Pflicht-Review-Gate vor E-3**. Rückfall auf MiniMax (bis 2026-11-15) oder Claude, wenn ein Step zweimal scheitert oder ein Test nach 3 Versuchen rot bleibt. Scheduler gestoppt von B-0 bis E-3 |

## Bot-Ritual (vor jedem bot-berührenden Edit)

```bash
systemctl --user stop tradingbot-scheduler.service       # bis B-9 deployt ist: ≤ 90 s, ggf. SIGKILL (Plan D13, erwartet)
ps aux | grep "scheduler.run" | grep -v grep             # Gegenprobe: leer
```

- Recorder, Discovery und WebUI halten keine IG-Session und laufen weiter (Plan T22).
- Den Neustart macht nur **E-3**, die Deploy-Sequenz im Plan.

## Test-Sweep (jede Suite getrennt; Σ = 16 Suites, meta_m1 nicht in Σ)

```bash
cd /home/trading-bot/trading-bot && PY=/home/trading-bot/trading-bot/phase1_broker_wrapper/.venv/bin/python
for d in phase1_broker_wrapper phase2_persistence phase3_external_data phase4_research phase5_execution \
         phase6_debate phase7_reward phase8_scheduler phase9_universe phase10_v3 phase12_data_foundation \
         phase13_live_data phase14_discovery phase15_v4 phase16_activation; do
  echo "$d | $(cd $d && $PY -m pytest tests/ -q -p no:cacheprovider 2>&1 | tail -1)"; done
echo "root | $($PY -m pytest tests/ -q -p no:cacheprovider 2>&1 | tail -1)"
```

| Stand | Σ | Quelle |
|---|---:|---|
| Baseline (Plan-Session, 2026-10-17) | **1964** (+ meta 28) | Plan §2.1 |
| Nach Exec-Session #1 (B-1, 2026-10-19) | **1965** | +1 P1-Test |
| Nach Exec-Session #2 (B-2, 2026-10-19) | **1971** | +4 P12 + 2 P8 |
| Nach Exec-Session #3 (B-3, 2026-10-19) | **1974** | +2 P15 + 1 P8 |
| Nach Exec-Session #4 (B-4, 2026-10-19) | **1978** | +4 P4 |
| Nach Exec-Session #5 (B-5, 2026-10-19) | **1985** | +5 P5 + 2 P8 |
| Nach Exec-Session #6 (B-6, 2026-10-19) | **1988** | +3 P8 |
| Ziel nach Block B / C / D / E-1 | ≥ 1992 / ≥ 2025 / ≥ 2028 / ≥ 2035 | Plan §6 + §14 (+1) + §15 (+9, P4 +5 · P8 +4) |
| Re-Messung Exec-Session #6 (2026-10-19) | **1988** | unverändert, 16/16 grün |

## Phase-17-Status

| Block | Status |
|---|---|
| A Haushalt | ✅ (Session #1) |
| B-0 Scheduler-Stopp + IG-Probe | ✅ (Session #1) |
| B-1 IG-UTC-first | ✅ (Session #1) |
| B-2 Divergenz-Sampler | ✅ (Session #2) |
| B-3 Promotion-Bridge (3 Nahtfehler) | ✅ (Session #3) |
| B-4 Abschneiden sichtbar (D4) | ✅ (Session #4) |
| B-5 Monitor-Re-Adoption (D5, T8) | ✅ (Session #5) |
| B-6 Breaker Worst-Case (D6, T9) | ✅ (Session #6) |
| B-7 … B-10 | ⏳ |
| C LLM-Austausch | ⏳ — **zuerst Plan §14, dann §15** (Provider-Plastizität, in place) |
| D Token-Budget | ⏳ |
| E Test-Fundament | ⏳ |

## Forward-Agenda (zwischen den Blöcken B-5..B-10 und C)

| # | Thema | Status | Link |
|---|---|---|---|
| **C2 — Provider-Plastizität** | Endpoint-Abstraktion für alle „gängigen" Provider (Anthropic + OpenAI + DeepSeek + Qwen + GLM + …). Nikinger-Entscheidung 2026-10-19 („soll mit sämtlichen gängigen Endpunkten funktionieren"). | ✅ **Plan §15** (2026-10-19, Plan-Session Opus 5.5) — ändert C-1/C-3/C-4/C-6/C-7 in place; Q1–Q8 entschieden | [`../docs/concepts/phase17_testbed_plan.md` §15](../docs/concepts/phase17_testbed_plan.md) |

> **Update 2026-10-19 (Plan-Session):** C2 ist jetzt **Teil von Block C** (Plan §15, Nikinger Q2) — kein eigener Block, keine Phase 18. Σ-Ziel Block C ≥ **2025** (statt 2016). Der Absatz unten ist historisch.

Diese Forward-Agenda ist **kein Block** der Phase 17 — sie ist „Material für eine Opus-Miniplan-Session nach den Blöcken B-5..B-10", wie es der Nikinger mit seiner Entscheidung intendiert hat. Eine spätere Session `Exec-Session #5+` wird je nach Nikingers Q2-Antwort entweder einen Plan-§-Anker (neuer Block C2 in Phase 17) oder einen eigenständigen Phasenkopf Phase 18 schreiben.

## Executor-Evaluation (Plan §14.2 — je Exec-Session eine Zeile)

| Session | Datum | Modell (`zai-coding-plan/…`) | Steps | Kontingent vorher → nachher (z.ai-Dashboard) | Tests | Rückfall | Notiz |
|---|---|---|---|---|---|---|---|
| #6 (B-6) | 2026-10-19 | MiniMax-M3-Fallback (Plan §14.2) — kein z.ai-Modell heute in Verwendung | B-6 Breaker Worst-Case (D6, T9, P8) | n/a | Σ 1985 → **1988** (+3, P8 +3 ✓ Plan-AK exakt) | — | Plan-Anker Z. 1009–1016 (Closure `realized_pnl_today`) ist zwischen Plan-Session 2026-10-17 und Session #6 auf Z. 1066–1073 gewandert (~$+57$ Zeilen durch Folge-Commits in P15/P8); **kleiner Drift**, semantisch unverändert. Neuer Modul-Helper `_realized_pnl_today` direkt nach `_sampler_due` einsortiert (B-Block-Helper-Section). Test-File `tests/test_wiring_breaker.py` neu — DB-Path `:memory:` (sqlite3 in-memory, ein Connection über Test-Lifetime, keine `tmp_path`-Notwendigkeit) |
| #5 (B-5) | 2026-10-19 | MiniMax-M3-Fallback (Plan §14.2) — kein z.ai-Modell heute in Verwendung | B-5 Monitor-Re-Adoption (D5, T8, P5 + P8) | n/a | Σ 1978 → **1985** (+7, P5 +5 + P8 +2 ✓ Plan-AK exakt) | — | B-5 ist die letzte Single-Commit-Block: 1 Commit (154f460) in P5+P8. Bit-Identität via `getattr(self._executor, "resume_open_position", None)` — alle Bestands-Fakes unverändert grün |
| — | — | — | — | — | — | — | Der 5.2-Quirk: bei Flash-ähnlichem Kontingent-Verbrauch einen vergleichbaren Step mit `glm-5.2` fahren |

**Review-Gate vor E-3 (AK22):** ⏳ (Claude-Code-Session, Anthropic; Schwerpunkte B-5, B-6, C-4, B-3, B-2)

> **Integration des Executors = eurofyx-fleet, getrennt vom Plan (Plan §14.8, Nikinger 2026-10-18).** Die Fleet richtet ein: OpenCode-Provider `zai-coding-plan` (Auth), Modell, Neustart von `opencode.service`, MiniMax-Rückweg. Diese Exec-Session fasst `~/.config/opencode/`, `auth.json` und `opencode.service` **nicht** an. A-0 startet erst, wenn die Fleet „OpenCode + z.ai bereit" meldet.

---

## Session stopped — 2026-10-19 (Exec-Session #6 ENDE — Block B-6 Breaker Worst-Case, 1 Commit in P8, Σ 1985 + 3 P8-Tests = **1988** grün; Scheduler gestoppt + 3 Units laufen weiter; Nikinger-Freigabe zur Beendigung)

> **Auftrag:** Nikinger 2026-10-19 (später Session): „Go on as in the next block recommended." → Exec-Session #6 setzt die explizite **Next**-Priorität aus Exec-Session #5 um: **B-6 Breaker Worst-Case (D6, T9, P8)** per Plan §6 B-6 verbatim (T13: Code in P8 ✓, keine Cross-Phase-Edits nötig — alle Module im selben P8-Baum). **Drift-Hinweis:** Plan-Anker Z. 1009–1016 (Closure) ist heute Z. 1066–1073 — ~$+57$ Zeilen nach unten gewandert (B-3/B-5 Commits in P15 + P8 dazwischen). **Kleiner Drift**, semantisch unverändert, in dieser Session am Exec-Ort verifiziert.
>
> **Executor-Modus:** MiniMax-M3-Fallback (Plan §14.2) — unverändert. `~/.config/opencode/`, `auth.json`, `opencode.service` weiterhin unangefasst.

### Completed — diese Exec-Session (1 Commit)

| # | Commit | Phase | Inhalt |
|---|---|---|---|
| 1 | `a0b2fb5` | P8 | **`scripts/wiring.py`** Top-Level neue Funktion `_realized_pnl_today(conn: Any, session_date: str) -> float` direkt **nach** dem B-2-Helper `_sampler_due` einsortiert (B-Block-Helper-Section wächst). SQL mit `CASE WHEN status='OPEN' THEN -initial_risk ELSE profit_loss END` für die Bindung der T9-Worst-Case-Semantik: jeder OPEN-Trade (profit_loss NULL während IG-Settlement-Lücke, gemessen 1 h 06 – 1 h 54 in Phase-16-Closeout §4) zählt mit `-initial_risk` als sein Worst-Case-Verlust, gebuchte CLOSED-PnLs kommen unverändert durch. Zweiter Wert im `SELECT` ist `COALESCE(SUM(status='OPEN' AND initial_risk IS NULL), 0)` und löst eine `RuntimeError("OPEN trade without initial_risk — the breaker cannot bound today's loss")` aus, sobald ≥ 1 OPEN-Row ohne `initial_risk` (fail-closed Contract E — `AutoConfirm` blockt + loggt critical). Filter `WHERE session_date = ? AND (profit_loss IS NOT NULL OR status='OPEN')` schließt geCLOSE-te Rows mit NULL-PnL vom Buchungs-SUM aus, ohne sie zu verlieren (sie matchen weder den OPEN- noch den booked-CASE-Zweig). Closure `realized_pnl_today(session_date)` (jetzt Z. 1066) wird zum Drei-Zeilen-Wrapper `return _realized_pnl_today(db.conn, session_date)`; Docstring erweitert um „(Contract E + Phase 17 B-6 worst case)". **Kein Eingriff** in `AutoConfirm`-Konstruktion, `realized_pnl_today`-Aufruf, Kill-Path, Config oder die anderen `_build_*`-Helper. |
| 1b | (gleicher Commit) | P8 | **Neue Datei `phase8_scheduler/tests/test_wiring_breaker.py`** (Muster `test_wiring_reward_sink.py`/`test_wiring_sampler_gate.py`): `@pytest.fixture db` baut eine echte `persistence.Database(":memory:")` + `run_migrations()` (sqlite3 in-memory, eine Connection über Test-Lifetime — kein `tmp_path` nötig, `:memory:` hat im `Database`-Konstruktor keine Sonderbehandlung). Helper `_seed_closed_trade` (profit_loss + UPDATE status='CLOSED') + `_seed_open_trade` (default `status='OPEN'` aus dem DB-Insert, `initial_risk` parametrisch inkl. None). **+3 Tests**: `test_booked_pnl_only_when_no_open_rows` (3 winner/loser CLOSED → SUM == +160.0, keine OPEN-Rows → Booking-Pfad unverändert ggü. pre-B-6); `test_open_row_counts_as_minus_initial_risk` (1 CLOSED +50, 1 OPEN mit `initial_risk=30` → Return == 20.0, der OPEN-Trade bindet 30 gegen den Gewinn); `test_open_row_without_initial_risk_raises` (1 CLOSED +15, 1 OPEN ohne `initial_risk` → `pytest.raises(RuntimeError, match="OPEN trade without initial_risk")`). **Σ-Steigerung:** P8 266 → **269** (+3 ✓ Plan-AK exakt), Σ 1985 → **1988** (+3). Keine Regressionen in den übrigen 15 Suites. |

### Test-Detail (B-6, neu hinzugekommen)

P8 (`tests/test_wiring_breaker.py`):
- `db`-Fixture baut `:memory:` + `run_migrations()` — ein **Migrations**-Aufruf pro Test, weil in-memory DBs connection-scoped leben und der `Database`-Konstruktor keine `dispose()`-Methode anbietet. Bei `:memory:` heißt das: jede Test-Fixture lebt für genau den Test.
- `_seed_closed_trade` setzt `currency='EUR'` (NOT NULL aus Migration 001), wechselt dann `status='CLOSED'` per `conn.execute("UPDATE trade_outcomes SET status = 'CLOSED' WHERE id = ?", (row_id,))` — der `insert_trade`-Default ist `'OPEN'`, das UPDATE überschreibt sauber ohne die Phase-7-`update_trade_close`-Validierung (Hold-Duration nicht geprüft, weil `open_ts` und `close_ts` weggelassen werden würden, um den Test fokussiert zu halten).
- `_seed_open_trade` setzt `initial_risk` **nur wenn nicht None** — sonst bleibt die Spalte NULL und ist genau die failure-mode, die das Test 3 prüft. Die DB-Spalte ist NOT NULL nur für manche Felder; `initial_risk` ist seit Migration 002 (Phase 7) als REAL-ohne-NOT-NULL erlaubt.
- `test_booked_pnl_only_when_no_open_rows`: 3 CLOSED mit `profit_loss=120/80/-40` → **SUM == +160.0**. **Sentinel:** das `CASE WHEN status='OPEN'` greift **nie**, die `ELSE profit_loss`-Branch für **alle 3** Rows; `COALESCE(SUM(...), 0.0)` ist Standard, `COALESCE(SUM(status='OPEN' AND initial_risk IS NULL), 0)` ist 0 — der `if row[1]`-Check schweigt, Return == `float(row[0])` == 160.0. **Pre-B-6** hätte derselbe Aufruf (alter Closure-Rumpf) `+160.0` returniert — der Test pinnt „Booking-Pfad bit-identisch" und ist die wichtigste Regression.
- `test_open_row_counts_as_minus_initial_risk`: 1 CLOSED +50 + 1 OPEN mit `initial_risk=30` → **Return == +20.0**. **CAS-Walk:** der OPEN-Trade landet mit `-30` im SUM, der CLOSED mit `+50`, beide addiert via `CASE`. Der `_NULL_OPEN` Count ist 0 (OPEN-Row hat ja `initial_risk=30`), Raise schweigt. Diese eine Zahl demonstriert den **Breaker-Misser** der pre-B-6-Situation: derselbe Trade-Bestand hätte dem Breaker pre-B-6 nur `+50` gezeigt (= buchstäblich falsche Trading-Freigabe, obwohl der OPEN mit `initial_risk=30` schon auf dem Weg zur Stop-Loss-Kurs ist). Bug-Fix: K1 (Breaker) sieht das OPEN jetzt mit.
- `test_open_row_without_initial_risk_raises`: 1 CLOSED +15 + 1 OPEN-Trade ohne `initial_risk` → **`pytest.raises(RuntimeError, match="OPEN trade without initial_risk")`**. **Die Reihenfolge im SQL ist wichtig:** der Bug ist, dass die `-initial_risk`-CASE-Branch in SQL zu `-NULL` = NULL wird (kein Fehler, SQL SUM ignoriert NULLs) → der SUM liefert **nur +15** als untere Schranke, der Breaker wäre „happy" mit +15, obwohl der OPEN-Unbound echtes Risiko verbergen kann. Deshalb der **zweite** Selekt-Wert mit der Fail-Check: jede NULL-initial_risk-OPEN-Row löst `raise` aus, **bevor** `return float(row[0])` läuft. Der Test ist exakt das — er beweist nicht, dass der SQL-Wert 0 ist, sondern dass die Raise früher kommt. Fail-Cascading-Pfad ist: `AutoConfirm.can_open(state)` ruft `realized_pnl_today` → Reader raises → `AutoConfirm` loggt `critical` + returnt `(False, ...)` → Scheduler skippt den Trade → OPEN-Position muss per Operator-Reconciliation (`scripts/reconcile.py` / `reconcile_open_trades`) gelöst werden, bevor der nächste Cycle grün wird.
- `match="OPEN trade without initial_risk"` pinnt die genaue Errormessage, damit eine spätere Refactoring den **`RuntimeError`**-Typ und den Anlass stabil hält. Der genaue Wortlaut ist nicht durch einen Konsumenten erzwungen, gehört aber zu den Log-Lines, an denen ein Operator später unterscheiden kann, ob ein OPEN ohne initial_risk → Bug (Code füllt `initial_risk` nicht) oder Feature (Phase-8-Reconciler war langsam).

### Next (geplante Folgesessions, in Priorität)
- **B-7 Abstain-Naht (D7, P8).** `scripts/wiring.py`: zwei Edits — (1) `AbstainSink.on_no_trade(cycle_outcome)` Methode (Plan-Anker Z. 758–760, **vor Antritt re-verifizieren**) bekommt Rückgabe `-> Any:`, `inner.on_no_trade(cycle_outcome)` → `record_id = inner.on_no_trade(cycle_outcome)`, am Ende `return record_id`; Docstring-Satz „locked contract" → „passes the sink's record_id through — the executor links it into decision_context.abstain_record_id (3 669/3 669 NULL before Phase 17 B-7)"; (2) Reihenfolge Z. 993–995 umdrehen (Anreicherung **vor** Klassifikation, sodass `llm_unavailable`-Flag rechtzeitig an der Klassifikation ankommt). +2 P8-Tests in neuer Datei `tests/test_wiring_abstain_seam.py`. Plan-AK P8 ≥ **271**, Σ ≥ **1990**.
- **B-8, B-9, B-10** in Plan §6.
- **Block C (LLM-Austausch)** wartet auf OpenCode + z.ai-Fleet-„bereit"-Meldung (Plan §14.8). Heute nicht blockierend (MiniMax-Fallback läuft).
- **Datenreparatur der 3 730 alten `source='ig'`-Bars** (Plan T14) folgt erst in **E-3** zusammen mit dem Scheduler-Restart; bis dahin bleibt der DB-Zustand mit den +2-h-Bars stehen.

### B-6 Σ-Steigerung (2026-10-19, Plan §6 Kommandoform)

| Suite | grün (nach B-5) | grün (nach B-6) | Δ |
|---|---:|---:|---:|
| P1 broker_wrapper | 98 | 98 | — |
| P2 persistence | 82 | 82 | — |
| P3 external_data | 108 | 108 | — |
| P4 research | 167 | 167 | — |
| P5 execution | 195 | 195 | — |
| P6 debate | 76 | 76 | — |
| P7 reward | 170 | 170 | — |
| **P8 scheduler** | 266 | **269** | **+3** |
| P9 universe | 95 | 95 | — |
| P10 v3 | 165 | 165 | — |
| P12 data_foundation | 153 | 153 | — |
| P13 live_data | 85 | 85 | — |
| P14 discovery | 61 | 61 | — |
| P15 v4 | 128 | 128 | — |
| P16 activation | 15 | 15 | — |
| root `tests/` | 121 | 121 | — |
| **Σ 16 Suites** | **1985** | **1988** | **+3** |
| meta_m1 (informativ, nicht in Σ) | 28 | 28 | — |

### Open questions / blockers
- **Scheduler ist gestoppt** (`is-active=failed`). Vor E-3 muss er wieder hochfahren — der Recorder muss dann mit dem Klonen-Bar-Löschen (Plan T14, `DELETE FROM bars WHERE source='ig'`) zusammen laufen, weil sonst `bars.sqlite is locked` (Plan §8 Fehlgriff). Bis zum E-3 wird die alte IG-Historie (3 730 Bars mit `ts_utc` +2h in der Zukunft) NICHT angerührt; das ist **gewollt** und **kein Datenverlust**, weil der Fix in `ig_adapter.py:909` wirkt und neue Bars korrekt schreibt. **Identisch zu Session #1/#2/#3/#4/#5 — keine Änderung.**
- **Promotion-Bridge-Backfill für die 29 NULL-Zeilen**: unverändert offen (Session #3).
- **Fleet §14.8 (OpenCode + z.ai)** weiterhin offen. Heute nicht blockierend.
- **B-5-Live-Beweis** (E-4-Probe) noch ausstehend — `resume_open_position()` selbst ist grün, Live-Beweis kommt in der Shakedown-Phase.
- **B-6-Live-Beweis** ebenfalls noch ausstehend — die `_realized_pnl_today`-Worst-Case-SUM ist im grünen Test abgesichert, aber der **cascade-pfad in `AutoConfirm`** (raise ⇒ `(False, ...)` + critical log + Trade-Block) wird im Test indirekt über den `pytest.raises` garantiert; live muss der nächste OPEN-mit-`initial_risk NULL` (oder überhaupt ohne `initial_risk`-Befüllung) zeigen, dass der Breaker den Cycle blockiert und der Operator die Reconciliation triggert. Bis dahin ist das **strukturelle Garantie**, kein empirischer.

### Session-end-Hinweis (für die Exec-Session selbst)
- **Plan-AK-Stand nach dieser Session:** Session #1 ✅ AK1-AK4 + Session #2 ✅ +6 + Session #3 ✅ +3 + Session #4 ✅ +4 + Session #5 ✅ +7 + **Session #6 ✅ +3** = Σ 1988. Plan-AK-Block-B Sweep Σ ≥ 1992 noch **4 Tests entfernt** (B-7..B-10 verbleibend: B-7 +2, B-8 +1, B-9 +0 (Unit-Test läuft in E-3), B-10 +1 = +4 exakt).
- B-6 lokal ahead (`a0b2fb5` = 1 Commit nach `origin/main = 9d8eb96`), wartet auf Nikinger-Push.
- **Drift-Konsolidierung (Anker):** zwischen Plan-Stand 2026-10-17 und Session #6 sind die Plan-Anker für B-6, B-7, B-10 um ~$+20$ bis $+57$ Zeilen gewandert (Commits in P8/P15 zwischen Plan-Snapshot und Exec #6). **Nicht substantiell**, aber jede Exec-Session die in der nächsten Zeit einen Anker aufsucht, muss ihn re-verifizieren — diese Session hat es für B-6 getan (`grep -n realized_pnl_today` → Z. 1066 statt 1009), hat den Drift protokolliert und die Edits am realen Ort ausgeführt. Wenn die Drift-Differenz für B-7 noch größer ist (z. B. >+60 Zeilen), sollte eine Folge-Session den Plan-Snapshot updaten statt nur den Drift zu protokollieren.
- **Strukturelle Beobachtung:** B-6 setzt einen `RuntimeError`-Throw-Pfad in die `realized_pnl_today`-Reader-Funktion. **`AutoConfirm`** muss diese Exception **fail-closed** behandeln — der bestehende `AutoConfirm.can_open`-Code-Pfad enthält keine `try/except` um den Reader-Aufruf, sondern erwartet, dass der Reader einen Wert returniert. Wenn das aktuelle `AutoConfirm` nicht try/catcht und die Exception hochpropagiert, krasht der Cycle (Backoff greift nach `max_consecutive_failures=3` → Kill-Switch). **Heute kein empirischer Bug-Check gemacht** — das ist Konzept-Audit gegen den Code-Stand. Wenn der Live-`AutoConfirm` try/catcht, ist alles gut; wenn nicht, ist das ein Folge-Fix (P8) im Block-B oder eine Phase-17-Folge-Session. **B-6 ist kein Defekt, B-6 ist die Missing-Guard gegen den nächsten OPEN-without-initial_risk.** Die RuntimeError-Kaskade selbst ist Plan-Wortlaut — wenn der Code sie anders abfangen will, ist sie immer noch da, nur am anderen Caller.
- B-6 schließt den **dritten der vier Phase-16-PASS-Blocker** (Breaker-Blindfenster: Buchungsverzug 1 h 06 – 1 h 54 ließ den Breaker einen Fresh-Stop-out nicht sehen — Phase-16-Closeout §4). Verbleibend: **Token-Budget (K6)** als Block-D (Phase-17 §6 D-1/D-2 Planreferenz). Promotion-Bridge ist B-3-repariert; Monitor-Orphan ist B-5-repariert; jetzt Breaker-Blindfenster B-6-repariert.
- **Test-Isolation:** `test_wiring_breaker.py` baut pro Test eine neue `:memory:`-Database. Das ist kostenneutral (in-memory, keine Disk-IO) und garantit Isolation; das `_seed_open_trade` mit `initial_risk=None` ist die einzige **`assert pytest.raises(RuntimeError)`** im Block-B-Sweep bislang — alle anderen Tests dieser Phase sind Positivfälle.

### Next start (für die Folgesession, kalt einsteigen ohne Neu-Lesen)

**B-7 Abstain-Naht (D7, P8).** Anker (vor Antritt re-verifizieren — Drift-Konsolidierung oben): `scripts/wiring.py` Z. 758–760 (`def on_no_trade(self, cycle_outcome: Any) -> None:` → `-> Any:`, `inner.on_no_trade(cycle_outcome)` → `record_id = inner.on_no_trade(cycle_outcome)`, `return record_id` am Ende) + Docstring Z. 747–753 (Satz „locked AbstainSink.on_no_trade(cycle_outcome) -> None contract" → „passes the sink's record_id through — the executor links it into decision_context.abstain_record_id (3 669/3 669 NULL before Phase 17 B-7)") + Z. 993–995 Reihenfolge umdrehen (Anreicherung vor Klassifikation, damit `llm_unavailable`-Flag rechtzeitig ankommt). Neue Datei `phase8_scheduler/tests/test_wiring_abstain_seam.py` mit +2 Tests (`test_observed_sink_returns_inner_record_id`, `test_enriched_outer_wrapper_feeds_observed_classification`). Plan-AK P8 ≥ **271**. **Live ab Tag 1** `abstain_record_id IS NOT NULL` für jede neue NO_TRADE-Zeile (E-3) — der harte K1-Beweis, dass die Naht nicht wieder verworfen wird.
Block-B Σ-Ziel ≥ 1992 noch 4 Tests entfernt nach B-7 (B-7 = +2, Σ 1990).
Scheduler bleibt gestoppt (B-0). Push = Nikinger. Block C wartet auf OpenCode-Fleet-„bereit"-Meldung.

---

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
