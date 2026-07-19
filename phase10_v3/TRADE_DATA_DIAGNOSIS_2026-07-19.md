---
status: snapshot
purpose: Strukturdiagnose vor der V4-Datenwoche — warum nur BUY-Trades, warum alle per SL gestoppt; 6 Befunde mit Beweisen + falsifizierbaren Watch-Items für die Woche ab 2026-07-20; formt den V4-Scope NACH der Datenwoche
read-when: bei der V4-Scope-Entscheidung (nach der Datenwoche ab 2026-07-20) oder beim Auswerten der Watch-Items; nicht bei normalem Session-Start
detail: L3
up: ./CLAUDE.md
updated: 2026-07-19
---

# Trade-Daten-Diagnose — 2026-07-19 (vor der V4-Datenwoche)

> **Auftrag (Nikinger, 2026-07-19):** Der Bot hat fast nur BUY-Trades auf DAX ausgeführt, alle
> per Stop-Loss beendet. V4 soll den Bot nicht profitabel machen, sondern **konsistent handeln
> lassen, damit beurteilbare Daten entstehen**. Diese Diagnose benennt strukturelle Schwächen
> mit Daten-/Code-Beweis und definiert, was die Woche ab 2026-07-20 beobachten muss, um jede
> These zu bestätigen oder zu verwerfen. **V4 wird aus den Watch-Item-Ergebnissen geformt,
> nicht aus diesem Dokument allein.**
>
> Quellen (alle read-only, `mode=ro`): `data/trading_bot.sqlite`, `data/state/debate_log.json`,
> `data/state/research_health.jsonl`, `data/state/scheduler_state.json`,
> `data/state/llm_usage.json`; Code-Anker jeweils inline.

## 0. Faktenlage (Stand 2026-07-19)

**Alle jemals ausgeführten autonomen Trades** (`trade_outcomes`, 3 Zeilen):

| id | Epic | Richtung | Entry | Haltezeit | Exit | P&L | R |
|---|---|---|---|---|---|---|---|
| 4 | DAX (IFMM) | BUY | 2026-07-02 16:58 | 9.3 min | SL (−30 pts exakt) | −585.00 € | −1.00 |
| 5 | DAX (IFMM) | BUY | 2026-07-03 09:28 | 3.6 min | SL (−30 pts exakt) | −651.16 € | −0.97 |
| 6 | DAX (IGN) | BUY | 2026-07-10 12:49 | 42.2 min | SL (lt. Lesson R=−0.97; `close_level`/`profit_loss` der Zeile sind die bekannte Bug-A-Korruption, Kopien aus id=5) | ~−669 € | ~−0.97 |

**Debatten** (`debate_log.json`, 20 Einträge seit 2026-06-16): Seed-Richtung **19× BUY, 1× SELL**
(einzige SELL-Seed: 2026-06-16, ältester Eintrag). Ergebnis: 15× ABSTAIN auf BUY-Seed, 4× TRADE
(alle BUY, Seed nie geflippt), 1× ABSTAIN auf SELL-Seed. Der 4. TRADE (AEX, 2026-07-15 11:57)
wurde vom Broker REJECTED (Bug-B-Vorfall, Grund unrettbar verloren).

**Trichter gesamt:** ~97.6 % Research-Abstain (Step-0-Analyse) → von den Picks ~80 %
Debatte-Abstain → 3 ausgeführte Trades in ~5 Wochen Betrieb. `drift_at_pick` bei den
Trade-Entries: +2.30 %, +3.08 %, +0.21 % — **alle Entries nach bereits gelaufener
Aufwärtsbewegung.**

---

## Befund W1 — Der BUY-Bias entsteht in Phase 4 (Research), und er ist eine Abstain-Asymmetrie, kein Direction-Flip-Problem

**These:** Das Research-LLM schlägt bei positivem Drift BUY vor; bei **negativem** Drift schlägt
es nicht SELL vor, sondern **abstaint**. Richtungsentscheidung ist also faktisch
„BUY oder nichts".

**Beweis:**
- 19/20 Debatte-Seeds sind BUY (`debate_log.json`); die Debatte hat einen Seed nie geflippt
  (sie darf es: Judge-Schema erlaubt Richtungswechsel).
- Smoking Gun `scheduler_state.json.last_no_trade_detail` (2026-07-17, breiter roter Tag):
  *„All instruments show negative drift (−0.59 % to −0.93 %) … **While a SELL could be
  considered** given the negative drift, the 15m momentum is slightly positive (0.07 %) which
  creates conflicting signals … the risk-adjusted case for abstaining is strong."* — Das Modell
  erwägt SELL explizit zweimal und redet es sich beide Male aus.
- Code-seitig ist **kein** Clamp aktiv: `enable_long_bias_clamp=False` seit v1.5
  (`phase4_research/research/models.py:609`) — der Bias kommt nicht aus einem Config-Schalter,
  sondern aus dem Entscheidungsverhalten des LLM auf den gegebenen Features (Drift/Momentum/
  30d-High-Breakout sind allesamt Long-gerahmte Trendfolge-Signale; ein „Abstand zum 30d-Low"-
  Frame für Short-Setups existiert im Prompt spiegelbildlich, wird aber nie als hinreichend
  gewertet).

**Konsequenz für Datensammlung:** Solange kein SELL je ausgeführt wird, ist unentscheidbar, ob
die Verluste an der Richtungslogik oder an der Trade-Geometrie (W2) liegen.

**Watch-Item WI-1 (falsifizierbar):** An jedem Tag der kommenden Woche mit negativem Tages-Drift
(jetzt via `market_regime_snapshots` maschinell greifbar): erzeugt Research einen SELL-Pick oder
einen Abstain? **Prediction: Abstain.** Wenn ≥1 echter SELL-Seed auftaucht, ist W1 abgeschwächt
(dann war die BUY-Serie teils Marktregime-Artefakt einer Aufwärtsphase). Wenn eine ganze rote
Woche null SELL-Seeds liefert, ist W1 bestätigt → V4-Kandidat: symmetrische Richtungs-Frames im
Prompt (SELL als gleichwertiges First-Class-Outcome), nicht mehr AI, nur anderes Framing.

## Befund W2 — Die fixe 30-Punkte-Stop-Distanz liegt auf DAX unterhalb des Marktrauschens; die Trade-Geometrie verliert auch ohne Richtungsfehler

**These:** Bei DAX ~25.600 sind 30 Punkte = **0.117 %**. Der Bot selbst betrachtet ±0.15 %/h als
normales Rauschen (Momentum-VETO-Schwelle, `ExecutionConfig.momentum_veto_threshold_pct=0.15`).
Der Stop liegt **innerhalb** des Bandes, das der eigene VETO-Code als unauffällig durchwinkt.
Ergebnis: SL-Treffer in Minuten, unabhängig von der Richtungsqualität.

**Beweis:**
- Trades 4/5 wurden in 9.3 bzw. **3.6 Minuten** exakt −30 Punkte ausgestoppt — DAX bewegt 30
  Punkte routinemäßig in Einzelminuten.
- Geometrie-Rechnung: Stop 30 / Limit 45 (`execution/config.py:127-128`). Unter reinem Random
  Walk ohne Drift ist P(−30 vor +45) = 45/75 = **60 %** → EV = 0.4·45 − 0.6·30 = **0 Punkte
  vor Kosten**; Spread (~2 pts) macht die Geometrie strukturell negativ. Dazu kommt
  Adverse Selection: Entry nach +2.3 %/+3.1 % gelaufenem Drift (15-min-verzögertes Signal)
  kauft lokale Hochs — Mean-Reversion drückt sofort auf den engen Stop.
- Kein Trade hat je den Limit (+45) oder den Time-Stop (240 min) erreicht; Signalhorizont
  (30d-High-Breakout, Tages-Drift) und Stop-Horizont (Minuten) passen nicht zusammen.
- Gegenprobe andere Richtung: auf AEX (~1.100) sind dieselben 30 Punkte **2.73 %** — Faktor
  ~23 zwischen den Epics. Fix-Punkte über Instrumente hinweg sind in beide Richtungen
  dekalibriert (deckt sich mit der unbestätigten Bug-B-AEX-Reject-Hypothese,
  `phase5_execution/CLAUDE.md`).

**Watch-Item WI-2 (das Schlüssel-Experiment der Woche):** Die Block-B-Shadow-Pairs
(`paper_trades`, Variante BUY **und** SELL gleichzeitig, gleicher Moment, gleiches Epic) sind
ein natürliches Kontrollexperiment: **Wenn beide Seiten eines Pairs per SL enden, killt das
Rauschen, nicht die Richtung** (W2 bestätigt). Wenn eine Seite systematisch TP/Time-Stop
erreicht, trägt die Richtungswahl doch Signal (W2 abgeschwächt, W1 wichtiger). Auswertung:
`exit_reason`-Verteilung je Pair in `paper_trades` am Wochenende. Voraussetzung: es entstehen
überhaupt Pairs (siehe W4).

## Befund W3 — Das Tages-Token-Budget ist kein Ausnahme-Breaker mehr, sondern die tägliche Betriebsgrenze: der Bot ist jeden Nachmittag blind

**These:** `daily_token_budget=200_000` (`scheduler/config.py:134`, als „runaway breaker"
gedacht) wird **jeden einzelnen Handelstag** erreicht und beendet den Research-Tag ~14:00–15:00
— vor dem US-Open-Overlap (15:30), 2.5–3.5 h vor Fensterende 17:30.

**Beweis:** `llm_usage.json`-Tagessummen: 07-13: 200.110 · 07-14: 202.652 · 07-15: 195.493 ·
07-16: 201.250 · 07-17: 201.654 Tokens — fünf von fünf Tagen an der Kappe.
`scheduler_state.json`: `last_no_trade_reason=BUDGET`, `last_research_ts=2026-07-17T14:51`.

**Konsequenz:** Systematischer Blindfleck am Nachmittag = weniger Zyklen, weniger Kandidaten,
weniger Daten — direkt gegen das V4-Ziel. Trade 4 (16:58) wäre unter dem heutigen
Budget-Verhalten nie entstanden.

**Watch-Item WI-3:** Pro Tag den Timestamp des letzten Research-Zyklus notieren (steht in
`research_health.jsonl`). Prediction: Budget-Kappe täglich ~14:00–15:00. V4-Hebel ist dann
**nicht** „Budget erhöhen", sondern Zyklus verbilligen (Prompt-Caching wie in P6, kleinerer
Kontext, oder Zyklus-Intervall strecken) — Kosten-Deckel ~0.75 €/Tag ist ja gewollt.

## Befund W4 — Die Daten-Pipeline für „konsistent handeln" existiert schon (Paper-Trades), triggert aber fast nie; der stärkste ungenutzte Hebel ist bereits gebaut

**These:** Für das V4-Ziel (Daten erzeugen ohne Profit-Anspruch) sind echte Orders gar nicht
nötig — aber die Paper-Pipeline triggert nur auf `REASON_DEBATE_ABSTAIN`, und der feuerte in
2 Wochen genau **5×, an einem einzigen Tag, auf einem einzigen Epic** (`abstain_records`:
313/318 = 98.4 % `REASON_NO_CANDIDATES`, wo kein Paper-Trade entsteht). `paper_trades` hat
Stand heute **0 Zeilen** (Block B ging erst 2026-07-17 abends live — Montag ist der erste
echte Testtag).

**Beweis:** `abstain_records`-Verteilung (Week-1-Review + eigene Zählung); `paper_trades`
COUNT=0; Council-Paper-Call (erzwungener BUY/SELL-Pick, Cap 3/Tag, nur `paper_trades`-Output)
ist **gebaut + getestet, aber aus** (`enable_paper_debate=False`,
`phase8_scheduler/scripts/wiring.py`).

**Watch-Item WI-4:** Zählen, wie viele `paper_trades`-Zeilen die Woche real erzeugt.
Prediction: nahe 0 über den Debate-Abstain-Trigger allein. **Empfehlung an den Nikinger
(Operator-Flip, kein Code):** `enable_paper_debate=True` setzen — bis zu 3 erzwungene
Council-Picks/Tag liefern genau die konsistenten, risikofreien Datenpunkte, die V4 beurteilen
soll, und WI-2 bekommt dadurch überhaupt erst eine belastbare Stichprobe.

## Befund W5 — Der Lesson-Loop wirkt aktuell als genereller Trade-Dämpfer, nicht als Richtungs-Korrektiv

**These:** Alle 3 gespeicherten Lessons stammen aus den 3 BUY-Stop-outs und sagen sinngemäß
dasselbe („Stop korrekt getroffen — prüfe Entry-Qualität"). Sie stehen in **jedem**
Research-Prompt (`used_in_research`: 692/673/336) und tauchen im 07-17-Abstain-Rationale als
explizites Argument auf, **gar nicht** zu handeln („three consecutive losses and lessons
emphasizing entry quality review → the risk-adjusted case for abstaining is strong") — auch
gegen einen SELL, für den die BUY-Verluste keinerlei Evidenz sind.

**Beweis:** `trade_lessons` Zeilen 4–6 + `scheduler_state.json.last_no_trade_detail` (Zitat
oben). Verstärkend: `get_recent_trades(8)` speist dieselben 3 Verluste als „three consecutive
BUY losses" ein — zwei Kanäle, ein Signal, doppelt gewichtet.

**Watch-Item WI-5:** In den Abstain-Begründungen der Woche zählen, wie oft Lessons/Verlustserie
als Abstain-Grund zitiert werden. Wenn dominant → V4-Kandidat: Lesson-Relevanz-Decay oder
Stichproben-Cap im Prompt (Code, kein AI-Umbau), damit 3 alte Datenpunkte nicht dauerhaft die
Datenerzeugung drosseln. (Der `reflect_abstain`-Pfad hat zudem weiterhin 0 bestätigte Erfolge —
`lesson_extracted=0` überall; bestehendes Watch-Item aus dem Week-1-Review, mit frischen Logs
jetzt diagnostizierbar.)

## Befund W6 — Entry-Fenster und Square-off sind asymmetrisch: Entries bis 17:30 erlaubt, Zwangs-Close 17:15

**These/Beweis:** Gate 1 prüft nur `trading_window_start/end` (09:00–17:30,
`execution/gates.py:46-64`); der Monitor squared ab 17:15 (`monitor.py:117-120`). Ein Entry um
16:58 (Trade 4) hat maximal 17 Minuten Laufzeit statt `max_hold_minutes=240` — Time-Stop und
Limit sind für Spät-Entries strukturell unerreichbar, nur der (zu enge, W2) Stop ist real.
Genau genommen sind Entries 17:15–17:30 sogar sofort-square-off-pflichtig.

**Watch-Item WI-6:** Entry-Uhrzeiten der Woche protokollieren (real + paper). Kleiner,
deterministischer V4-Fix-Kandidat: „kein neuer Entry nach `square_off − max_hold`" bzw.
mindestens „nicht nach `square_off − X min`" — eine Zeile Gate-Logik, kein AI-Touch.

---

## Was ausdrücklich NICHT kaputt ist (gegen Über-Fixen in V4)

- **Mechanik/Risikomanagement:** Alle 3 SL-Exits exakt bei −30 Punkten, R sauber bei −1.0/−0.97,
  Sizing korrekt (initial_risk = size × 30 × point_value, ~2 % Konto). Fail-closed-Verhalten
  (Budget-Breaker, Broker-Reject → ABORT) hat funktioniert. Die Verluste sind kein
  Execution-Bug.
- **VETOs:** In 5 Wochen nie ausgelöst — nicht, weil sie tot sind, sondern weil Research/Debatte
  vorher filtern. Kein Handlungsbedarf, aber die VETO-Zweige der Abstain-Taxonomie bleiben
  live-ungetestet.
- **Die Debatte selbst:** Sie ist konservativ (80 % Abstain), aber das ist bei der aktuellen
  Trade-Geometrie (W2) eher Schutz als Fehler. Erst wenn W2 behoben ist, lohnt die Frage, ob
  sie zu streng ist.

## Verdichtung für die V4-Entscheidung (nach der Datenwoche)

Kausalkette der bisherigen Verluste, nach Beweislage geordnet:

1. **Geometrie (W2)** erklärt „alle enden im SL" hinreichend — auch ein perfektes
   Richtungssignal würde mit einem Sub-Noise-Stop überwiegend ausgestoppt. Diskriminator: WI-2
   (Shadow-Pairs).
2. **Abstain-Asymmetrie (W1)** erklärt „nur BUY" — Diskriminator: WI-1 (rote Tage).
3. **Budget-Blindfleck (W3) + seltene Paper-Trigger (W4)** erklären „zu wenig Daten" — der
   V4-Kernauftrag. Schnellster Hebel ist ein bereits gebauter Flag-Flip (WI-4).
4. W5/W6 sind reale, aber kleinere Verstärker.

**Nichts hiervon ist eine V4-Festlegung.** Die Woche ab 2026-07-20 liefert pro These ein
Ja/Nein; erst daraus wird der V4-Scope geschnitten.
