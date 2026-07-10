---
status: snapshot
purpose: Step-2 Datenanalyse (dated, L3) — V2-Baseline-Auswertung + Abstain-Ist-Analyse + Gap-Check gegen S2-Contract/Block-B, Grundlage für Migration 005 (WE 1)
read-when: vor Step 4 (Migration 005) oder bei der D3/D4-Scope-Entscheidung; NICHT bei normalem Phase-10-Session-Start (das ist phase10_v3/CLAUDE.md)
detail: L3
up: ./CLAUDE.md
updated: 2026-07-10
---

# Step 0 — Datenanalyse (2026-07-10, Fr, read-only)

> Quellen: `data/state/debate_log.json`, `data/state/research_health.jsonl`,
> `data/state/scheduler_state.json`, `data/state/execution_state.json`,
> `data/trading_bot.sqlite` (ausschließlich `sqlite3.connect("file:...?mode=ro", uri=True)`).
> Der Bot lief während der gesamten Analyse ununterbrochen weiter; nichts geschrieben.
> **Kein Backfill** historischer Abstains in eine neue Tabelle (YAGNI) — dieses Doc IST der
> historische Record; die Tabelle füllt sich ab Montag-Restart.

## (a) V2-Baseline-Auswertung

**Trades:** `trade_outcomes` enthält genau **2 Zeilen**, beide vor dem strikten
V2-Baseline-Startdatum (2026-07-06, per Kickoff-Handover):

| id | epic | Richtung | open→close | P&L | gate_path |
|---|---|---|---|---|---|
| 4 | DAX | BUY | 2026-07-02 16:58→17:07 (9.3 min) | **-585.00 EUR** | Gates 1-5 pass, Debatte TRADE |
| 5 | DAX | BUY | 2026-07-03 09:28→09:31 (3.6 min) | **-651.16 EUR** | Gates 1-5 pass, Debatte TRADE |

**Ehrlich dokumentiert:** seit dem eigentlichen 2026-07-06-Baseline-Cutoff sind es
**weiterhin 0 neue Trades** (letzter Research-Zyklus im Log: 2026-07-09 17:26). Beide
existierenden Trades sind schnelle Stop-outs (< 10 min Haltezeit, beide BUY, beide
Verlust) — kein Signal für oder gegen die V2-Pipeline, nur zwei Datenpunkte. Nichts
erfunden, nichts extrapoliert.

**Zyklen/Tag, Abstains/Tag** (`research_health.jsonl`, 335 Zyklen-Records total,
2026-07-02 bis 2026-07-09):

| Tag | Zyklen | davon Picks (→Debatte) | davon LLM_ABSTAIN (Research-Stufe) |
|---|---|---|---|
| 07-02 | 12 | 2 | 10 |
| 07-03 | 87 | 5 | 71 (+ 11 session-health-Aborts, s. u.) |
| 07-06 | 45 | 0 | 45 |
| 07-07 | 78 | 1 | 77 |
| 07-08 | 68 | 0 | 68 |
| 07-09 | 45 | 0 | 45 |

**Abstain-Quote insgesamt: 327/335 = 97.6 %** (auf Research-Stufe, vor jeder Debatte).
Von den 8 Zyklen, die einen Kandidaten fanden (`picked=true`), gingen 2 in TRADE, 6 in
Debatte-ABSTAIN (Details siehe `debate_log.json`, deckungsgleich mit den 8
`final_decision=ABSTAIN`/`TRADE`-Einträgen ab 2026-07-02).

**Variety-These (Abstain-Quote vs. Anzahl aktiver Epics):** `instrument_universe`
enthält aktuell **9 `active`** + 6 `verified`(-not-yet-promoted) Epics — mehr als die 8
aktiven Epics, die der Kickoff-Handover nennt (kleine Drift, plausibel: Universe-Refresh
lief zwischen Handover-Schreibzeitpunkt und heute mindestens einmal). **Nicht
beantwortbar als echte Zeitreihe:** `instrument_universe` trägt nur den aktuellen
`status` + `updated_at`, keine Status-Übergangs-Historie — es gibt also keinen Weg,
"Abstain-Quote am Tag X" gegen "aktive Epics am Tag X" zu korrelieren, ohne diese
History-Tabelle nachzurüsten. **Messlücke, hier benannt, nicht gelöst** (kein
Block-B-Scope, kein Fix am laufenden Bot).

## (b) Abstain-Ist-Analyse (empirische Häufigkeitstabelle gegen S1-Taxonomie)

Mapping der realen Log-Werte auf die 12-Werte-`AbstainReason`-Taxonomie (`meta_m1_harness/specs/S1.md`):

| Realer Log-Wert | Quelle | Häufigkeit | → `AbstainReason` |
|---|---|---|---|
| `reason="LLM_ABSTAIN"`, `abort_detail="validator abstain (no pick)"` | `research_health.jsonl` | **316 / 335 (94.3 %)** | `REASON_NO_CANDIDATES` (research-empty, vor Gate 2) |
| `abort_detail="session-health abort: get_account not ok"` | `research_health.jsonl` | **11 / 335 (3.3 %)** | **Keine saubere Zuordnung** — siehe Gap-Finding unten |
| `debate_decision=="ABSTAIN"` (`final_decision` in `debate_log.json`) | `debate_log.json` | **6** (alle 8 Picks minus 2 TRADE) | `REASON_DEBATE_ABSTAIN` |
| Gate 1/3/4/5 fail | *(kein Log gefunden)* | **0 beobachtet** | `REASON_GATE_TIME_WINDOW` / `_CONSTRAINTS` / `_SIZING` / `_DIRECTION` — real nie aufgetreten |
| VETO (spread/momentum/status_window/position_conflict) | *(kein Log gefunden)* | **0 beobachtet** | `REASON_VETO_*` — real nie aufgetreten |
| `error` gesetzt (fail-closed, außerhalb Session-Health) | *(kein Log gefunden)* | **0 beobachtet** | `REASON_ERROR_FAILCLOSED` — real nie aufgetreten |

**Dominanter Befund:** `REASON_NO_CANDIDATES` (Research-Stufe) macht **94 % aller
Nicht-Trades** aus — das ist bei Weitem der Reason, wo Lessons den größten Hebel haben
(informiert V3-D8: der gemeinsame Reflect-Cap von 10/Tag wird fast ausschließlich von
dieser einen Reason konkurriert werden; die Woche-2-Review sollte prüfen, ob eine
Stage-Gewichtung nötig wird, falls `REASON_DEBATE_ABSTAIN` sonst nie einen Reflect-Slot
bekommt). Gate-/VETO-Reasons sind in 8 Tagen Betrieb **nie** aufgetreten — plausibel
(Kandidaten kommen ohnehin selten durch, und wenn, hat die Debatte in 6/8 Fällen selbst
ABSTAIN entschieden) — heißt aber auch: diese Zweige der `AbstainReason`-Taxonomie sind
bislang völlig ungetestet gegen echte Daten, nur gegen die S2-Unit-Tests.

**Gap-Finding (b):** die 11 `session-health abort`-Ereignisse (3.3 % aller Zyklen, alle
am 07-03) sind laut P5-Executor-Anker (Step-3-Annex unten) ein **`ABORT`-Status, kein
`NO_TRADE`** — der Executor gibt bei Session-Health-/Reconcile-Fail-Closed `ABORT`
zurück, nicht `NO_TRADE` (`executor.py:159-160`). Der Plan verdrahtet `abstain_sink`
ausdrücklich nur an **NO_TRADE**-Pfaden (§7.2) — diese 11 Ereignisse würden also **nicht**
in `abstain_records` landen, obwohl sie real und wiederkehrend sind. Das ist keine
Lücke, die heute gefixt wird (außerhalb Scope), aber eine, die die Woche-2-Review kennen
sollte, falls session-health-Aborts als eigene Lesson-Quelle irgendwann gewünscht sind.

## (c) Gap-Check (Feld-Mapping-Tabelle)

**S2-Contract-Felder** (`cycle_outcome: Mapping[str, Any]`):

| Feld | Loggt der Bot es heute? Wo? | Naht-Bedarf |
|---|---|---|
| `outcome` ("NO_TRADE") | Implizit über den Executor-Rückgabepfad, nicht als String geloggt | Am `_no_trade`-Helper zu setzen (`executor.py:130-136`) |
| `epic` | Ja — `candidate`/Zyklus-Kontext (ab Gate 2), `research_health.jsonl` (`context_health`-Keys) | Aus lokalem `candidate`/Loop-Scope assemblieren |
| `failed_gate` | Nein als String — nur implizit über welchen `if`-Zweig im Executor getroffen wird | Muss an der Naht aus dem jeweiligen Gate-Resultat (`g1.gate` etc.) gesetzt werden |
| `veto` | Nein als String — analog, `veto.veto` ist ein lokales Objekt, nicht persistiert | Muss an der Naht gesetzt werden |
| `debate_decision` | Ja — `debate_log.json.final_decision`, aber nur als Rolling-Log (10 Einträge, kein Full-History) | `outcome.decision` liegt im Executor-Scope bereits vor (`DebateOutcome.decision`) |
| `research_empty` | Ja, indirekt — `research_health.jsonl.reason=="LLM_ABSTAIN"` | Boolean muss an der Naht aus Gate-2-Kontext abgeleitet werden |
| `error` | Teilweise — `session-health abort`-Fälle sind `ABORT`, nicht `NO_TRADE` (s. o.), werden vom aktuellen Plan-Scope nicht erfasst | Bewusste Lücke, dokumentiert in (b) |

**Block-B-Felder** (`decision_context` / `market_regime_snapshots`):

| Feld | Heute geloggt? Wo? | Form |
|---|---|---|
| Bull/Bear-Argumente | Ja, vollständig — `DebateOutcome.transcript` (Tupel aller `AgentTurn`s), NICHT auf `DebateOutcome` selbst als Summary-Feld | Braucht eine Extraktions-/Kompressions-Funktion (Bull/Bear-Text aus `transcript` ziehen), keine reine Durchreiche |
| Judge-Confidence, `rounds_used` | Ja, direkt auf `DebateOutcome` (`confidence`, `rounds_used`) | Direkt durchreichbar |
| VETO-/Gate-Ergebnisse | Nein als strukturierte Daten (s. o., S2-Gap) | Gleiche Naht wie `failed_gate`/`veto` oben |
| Spread/Quote zum Entscheidungszeitpunkt | Teilweise — `debate_log.json.regime_snapshot.spread_pct` existiert **nur für gepickte Kandidaten** (die an die Debatte gingen), nicht für die 94 % reinen Research-Abstains | Für Research-Stufe-Abstains fehlt ein Spread-Snapshot komplett — echte Lücke |
| Bars/ATR-Verfügbarkeit | Teilweise — `context_health` pro Epic zeigt `status`/`missing` (z. B. `"missing": ["volume"]`), aber kein ATR/Range direkt | `regime.py` muss ATR/Range selbst aus vorhandenen Bars rechnen, nicht aus einem vorhandenen Feld lesen |
| **Datenqualität real (neuer Fund):** `IX.D.CAC.IFE.IP` degraded in 324/335 Zyklen (96.7 %), `IX.D.IBEX.IFM.IP` in 281/335 (83.9 %), beide fehlend `volume` — DAX/STOXX50 dagegen fast durchgehend `full` | `research_health.jsonl.context_health` | **Bestätigt, dass `data_source`/`degraded`-Felder im Regime-Snapshot keine theoretische Vorsicht sind, sondern für 2 von 4 aktuell instrumentierten Epics der Normalfall** |

**Paper-Trade-Zusatzfrage:** liegt zum Debate-Abstain-Zeitpunkt eine frische Quote vor?
**Ja, teilweise** — `debate_log.json` trägt ein `regime_snapshot`-Objekt pro Eintrag
(inkl. `spread_pct`, aber kein explizites Bid/Ask-Quote-Paar) — `open_shadow_pair`
braucht `quote["ask"]`/`quote["bid"]`, die in dieser Form **nicht** vorliegen. Ein
eigener Quote-Call bei `on_debate_abstain` ist also nötig, exakt wie der Plan in §10.2
bereits als bewusste Ausnahme von der "keine zusätzlichen Calls"-Regel vorsieht.

## Bestätigung

Bot lief während der gesamten Analyse weiter (`last_research_ts` in
`scheduler_state.json` wurde während der Session mehrfach neuer als beim ersten Read);
`data/trading_bot.sqlite` wurde ausschließlich über `mode=ro`-URI geöffnet.
