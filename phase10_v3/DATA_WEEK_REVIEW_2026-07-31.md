---
status: snapshot
purpose: Auswertung der zweiten Datenwoche (2026-07-27 bis 07-31) — Funnel-Kollaps bestätigt, WI-1/WI-5 beantwortet (W1+W5 bestätigt), WI-2 zum zweiten Mal tot; drei neue harte Befunde (point_value-Drift = 40x-Oversizing, Reward-Score-Inversion, Leverage-Cap ohne Headroom) + V4/Phase-11-Scope-Vorschlag mit 7 Hypothesen
read-when: bei der Phase-11-(V4-)Scope-Entscheidung, oder beim Nachvollziehen warum der Bot seit 2026-07-21 faktisch keine Kandidaten mehr produziert
detail: L3
up: ./CLAUDE.md
updated: 2026-07-31
---

# Datenwoche-Review 2 — 2026-07-31 (Mo 07-27 bis Fr 07-31)

> **Kopfbefund, damit nichts falsch gedeutet wird:** Die Woche lief **mechanisch sauber** (kein
> Crash, kein Kill, 0 `consecutive_failures`, 366 Zyklen) und hat trotzdem **null Trades und null
> neue Paper-Trades** produziert. Der Grund ist **nicht** das Marktregime: an drei von fünf
> Sessions war der DAX negativ, es gab also Stoff. Der Bot hat in **366 Zyklen genau einen**
> Kandidaten erzeugt — und der wurde vom Broker abgelehnt.
>
> **Antwort auf die Frage „haben wir genug Daten?": Ja — genug, um den Phase-11-Scope zu
> schneiden. Nein — nicht genug, um WI-2 zu beantworten** (zweite Woche in Folge tot, diesmal
> nicht wegen eines Tracker-Bugs, sondern weil der Funnel kollabiert ist).
>
> **Empfehlung, die sich von der letzten Woche unterscheidet:** *nicht* auf eine dritte saubere
> Woche warten. Wir wissen jetzt, **warum** die saubere Woche nicht kommt — siehe H1 in §5.
>
> Quellen (alle read-only, `mode=ro` / Log-Lesen): `data/trading_bot.sqlite`,
> `data/state/{research_health.jsonl, llm_usage.json, scheduler_state.json, debate_log.json,
> execution_state.json}`, `logs/scheduler_5a_variety_.log`, `data/cache/GDAXI_1d_*.json`.
> Code-Anker jeweils inline. Kein Code berührt (Wochentags-Regel).

---

## 1. Faktenlage der Woche

| Tag | Research-Zyklen | Kandidaten | Debatten | Trades | Paper-Trades | Research-Ende (lokal) | Tokens |
|---|---|---|---|---|---|---|---|
| Mo 07-27 | 73 | 0 | 0 | 0 | 0 | 15:25 | 200.270 |
| Di 07-28 | 74 | 0 | 0 | 0 | 0 | 15:30 | 200.386 |
| Mi 07-29 | 74 | 0 | 0 | 0 | 0 | 15:31 | 201.869 |
| Do 07-30 | 72 | **1** | **1** | 0 (ABORT) | 0 | 15:22 | 201.337 |
| Fr 07-31 | 73 | 0 | 0 | 0 | 0 | 15:27 | 201.254 |
| **Σ** | **366** | **1** | **1** | **0** | **0** | — | **1.005.116 (≈ 3,78 €)** |

`abstain_records` der Woche: **364 Zeilen, 100 % `research_empty` / `REASON_NO_CANDIDATES`**
(die Differenz 366→364: der 07-30-Pick lief in einen ABORT — ABORT-Zyklen schreiben
bewusst keinen Abstain-Record; plus **eine** fehlende Zeile am 07-27, s. §6).

**Kumulativ, alles was der Bot je getan hat** (nicht nur diese Woche):

- `abstain_records`: **1.036**
- Debatten gesamt: **30** — davon Seed-Richtung **29× BUY, 1× SELL** (die eine SELL ist
  weiterhin die vom 2026-06-16). Die Debatte hat **nie** eine Seed-Richtung geflippt.
- Debatte-Entscheidungen: 22× ABSTAIN, **8× TRADE** — alle 8 BUY.
- Davon real ausgeführt: **4** (alle DAX, alle per SL, alle R ≈ −1.0).
- **Davon vom Broker abgelehnt: 4** (07-15 AEX, 07-20 DAX, 07-20 AEX, 07-30 AEX) —
  **50 % aller Trade-Entscheidungen der Projekthistorie sind an einem Sizing-Konfigurationsfehler
  gestorben, nicht am Markt.** Ursache jetzt bewiesen, s. Befund B1.

**Marktlage der Woche** (yFinance-Tagesbars, `data/cache/GDAXI_1d_2026-07-31.json`, DAX-Sessions):
−0,39 % · −0,13 % · −0,36 % · +0,49 % (Intraday-Ranges 0,78–1,37 %). **Drei von vier
auswertbaren Sessions rot.** Es gab also die roten Tage, die WI-1 braucht.

---

## 2. Watch-Item-Status (gegen `TRADE_DATA_DIAGNOSIS_2026-07-19.md`)

| # | Frage | Status | Beleg |
|---|---|---|---|
| **WI-1** | Kommt an einem roten Tag ein echter SELL-Seed? | **BEANTWORTET — W1 bestätigt** | Am 07-30 (breite europäische Schwäche, DAX/CAC/IBEX −0,29 % bis −0,75 %) erzeugte Research **einen BUY** — auf AEX, dem einzigen Instrument mit *positivem* Drift. Die Pick-Begründung sagt es selbst: *„The mixed European picture (broad weakness) makes a SELL on DAX/CAC/IBEX tempting, **but** recent trade history shows 4 consecutive BUY losses on DAX — avoiding that instrument."* Es bleibt bei 29:1 BUY-Seeds. |
| **WI-2** | Shadow-Pair-Exit-Verteilung (das Schlüssel-Experiment) | **Zum zweiten Mal tot** | 0 neue Paper-Trades. Nicht wegen eines Bugs — der Trigger ist `REASON_DEBATE_ABSTAIN`, und es gab genau eine Debatte, die TRADE sagte. Die 15 Zeilen der Vorwoche bleiben **Backfill-Artefakte** (alle `resolved_utc` = `2026-07-27T07:05:40Z`), nicht als R-Multiples verwertbar. |
| **WI-3** | Budget-Kappe täglich ~14–15 Uhr? | **Bestätigt, 5/5** | 200.270 / 200.386 / 201.869 / 201.337 / 201.254 Tokens; letzter Research-Zyklus 15:22–15:31 lokal. **10 von 10 Handelstagen** seit 07-20. Ø ~2 h blinder Nachmittag pro Tag. |
| **WI-4** | Paper-Zeilen ohne Flag-Flip ≈ 0? | **Gegenstandslos** | Es entstanden 0 Zeilen, weil der Trigger stromabwärts des kollabierten Funnels sitzt — genau das ist der Kern-Designfehler (→ H1). ⚠ Der `--enable-paper-debate`-Flag-Status **dieser** Woche ist nicht rekonstruierbar: `run_scheduler.sh` reicht `"$@"` nur durch und loggt die Argumente nicht, und das Logfile beginnt erst am 07-29. Für WI-4 ohne Belang (ohne Debatte-Abstain feuert der Council-Call ohnehin nie); am 07-20 war er nachweislich an (3 `COUNCIL_PICK`-Zeilen). |
| **WI-5** | Lesson-Zitat-Häufigkeit in Abstain-Begründungen | **BEANTWORTET — W5 bestätigt** | Beide auswertbaren Rationales der Woche zitieren die Verlustserie **explizit als Abstain-Grund**. Heute (07-31): *„(1) All four recent trades are losses … the active lessons explicitly warn about poor entry quality … (5) The pattern of consecutive stop-outs suggests the current market regime is not favorable for this bot's entry methodology."* Die 4 Lessons wurden bis heute **4.529×** in den Research-Prompt gerendert (`used_in_research`: 1414/1395/1058/662). |
| **WI-6** | Entry-Timing nahe Square-off? | **Keine neue Evidenz** | Ein einziger Entry-Versuch (10:03 lokal). Nebenbefund: durch die Budget-Kappe (WI-3) ist ein Spät-Entry inzwischen strukturell **unmöglich** — Research endet 15:2x, das Fenster liefe bis 17:30. W6 ist damit praktisch entschärft, aber unbeantwortet. |

**Damit sind die zwei Richtungs-Thesen (W1, W5) bestätigt und die eine Geometrie-These (W2)
weiterhin unbeantwortet.** W2 ist die These, die entscheidet, ob Richtungslogik überhaupt das
Problem ist — sie braucht WI-2, und WI-2 braucht H1.

---

## 3. Der eigentliche Befund: eine sich selbst verstärkende Rückkopplung

**Vorab die Beweis-Abgrenzung, damit der Befund nicht überdehnt wird:** belegt ist der
**Mechanismus** (die Lessons dämpfen, wörtlich zitiert, 4.529 Renderings). **Nicht** belegt ist,
dass er allein den Kollaps *verursacht* — die Pick-Rate pro Tag schwankt stark und unerklärt:
07-13 **0** · 07-14 **0** · 07-15 6 · 07-16 **0** · 07-17 **0** · 07-20 **9** · 07-21…29 **0** ·
07-30 **1** · 07-31 **0**. Es gab also Null-Pick-Tage **vor** dem vierten Verlust, und der
07-20 lieferte 9 Picks, obwohl bereits drei Verluste im Prompt standen. Die Rückkopplung ist
damit ein **belegter Verstärker mit offener Hinreichendkeit**, kein bewiesener Alleinverursacher.
(Für die Phase-11-Entscheidung ist das eher ein Argument *für* H1: wenn die Pick-Rate ohnehin
erratisch nahe null ist, ist es umso aussichtsloser, die Messung an sie zu koppeln.)

Die Kette selbst:

```
4 BUY-Trades → alle per SL beendet (Sub-Noise-Stop, W2)
   ↓
4 Lessons ("prüfe die Entry-Qualität") + 4 Verlustzeilen in recent_trades
   ↓  (zwei getrennte Kanäle, dasselbe Signal, doppelt gewichtet — W5)
Research-Prompt bei JEDEM Zyklus (4.529 Renderings)
   ↓
LLM abstaint 365/366 — und begründet es wörtlich mit der Verlustserie
   ↓
keine Trades → keine neuen Outcomes → keine neuen Lessons → die 4 alten bleiben
   ↓  (zurück nach oben)
```

Die Schleife ist **selbstverstärkend**: das einzige, was die Lessons entkräften könnte (ein
anderes Trade-Ergebnis), ist genau das, was sie unwahrscheinlicher machen. Ob sie stark genug
ist, den Funnel *allein* zu schließen, ist nach der Abgrenzung oben offen — dass sie in die
schließende Richtung wirkt, ist belegt. Der 07-30-Pick zeigt die Logik in Reinform: das Modell liest
„4 BUY-Verluste auf DAX" nicht als *„vielleicht die Gegenrichtung"*, sondern als
*„DAX meiden"* — es weicht auf das Instrument mit positivem Drift aus und kauft dort. Die
Verluste dämpfen also die **Instrumentenwahl**, nicht die **Richtungswahl**. Das ist genau die
Asymmetrie aus W1, jetzt mit einem frischen, expliziten Zitat.

**Wichtig für die Interpretation:** das ist kein LLM-Fehlverhalten. Das Modell tut exakt, was
der Prompt verlangt („When in doubt, ABSTAIN. A skipped session is cheap"), auf Basis der
Evidenz, die ihm Code hinlegt. Der Fehler sitzt im **Design der Evidenz**, nicht im Modell.

---

## 4. Neue Befunde (drei harte Bugs + zwei strukturelle Lücken)

Alle fünf sind **seit Rollout tot/falsch** und wurden diese Woche zum ersten Mal beweisbar.
**Nichts davon wurde gefixt** (Wochentags-Regel) — jeder Punkt trägt die exakte Fundstelle und
den Ersatz-Ausdruck, damit ein Folge-Session-Fix (Sonnet 5) ohne Nachrecherche möglich ist.

### B1 — `point_value`-Drift: AEX wird um **Faktor 40** zu groß gesized (⚠ sicherheitskritisch)

**Fundstelle:** `phase8_scheduler/scripts/wiring.py:616`

```python
exec_cfg = ExecutionConfig(
    point_values={spec.epic: spec.point_value for spec in EXTENDED_UNIVERSE}
)
```

`EXTENDED_UNIVERSE` ist die **statische 4-Epic-Liste** aus der v1.5-Zeit (DAX.IFMM, STXE, CAC,
IBEX.IFM). Research handelt aber seit Phase 9 (V2) aus der **DB-Universe** — aktuell **8 aktive
Epics**. Für jedes Epic, das nicht in der statischen Liste steht, gibt
`ExecutionConfig.point_value_for()` (`phase5_execution/execution/config.py:156`) still `1.0`
zurück.

**Realer Schaden, exakt nachgerechnet** (07-30, AEX):

| Größe | Bot-Annahme | Wahrheit (`instrument_universe`, `point_value_source='ig_fields'`) |
|---|---|---|
| point_value | 1,0 €/Punkt | **40,0 €/Punkt** („Niederlande 25 Kassa (**40€**)") |
| Size | 26,8 = 804,47 € / (30 × 1,0) | dieselbe Size = 26,8 |
| Nominale | 29.544 € | **1.181.773 €** |
| Risiko am 30-Punkte-Stop | 804 € (= 3 % Konto, wie gewollt) | **32.160 € = 120 % des Kontos** |

Die Size 26,8 stimmt bis auf die letzte Stelle mit dem write-ahead-Record in
`execution_state.json` überein — die Rechnung ist keine Schätzung. **IG hat die Order abgelehnt
(`INSUFFICIENT_FUNDS`) und damit faktisch das Konto geschützt.** Mit korrektem `point_value`
wäre die Size 0,6 gewesen (über `min_deal_size=0.2`) — die Order wäre durchgegangen.

**Das erklärt rückwirkend alle drei AEX-Rejects** (07-15, 07-20, 07-30 — 3 von 3 AEX-Orders der
Projekthistorie) und **löst damit den als „unrettbar verloren" abgelegten Bug-B-Vorfall vom
07-15** (`phase5_execution/CLAUDE.md`). Die dort geflaggte Hypothese („AEX-spezifische
Dekalibrierung fixer Konstanten") war **richtig in der Richtung, falsch in der Konstante**: es
ist nicht die Stop-Distanz, es ist der `point_value`.

**Fix (zwei Teile — Symptom *und* Ursache):**

1. *Quelle korrigieren.* Acht Zeilen weiter oben im **selben File** existiert bereits
   `_build_universe_from_db()` (`wiring.py:105-129`), das genau die DB-Specs mit korrektem
   `point_value` liefert und fail-soft auf `EXTENDED_UNIVERSE` zurückfällt:
   ```python
   point_values={spec.epic: spec.point_value for spec in _build_universe_from_db()}
   ```
2. *Ursache abstellen.* `point_value_for()` darf für ein unbekanntes Epic **nicht still `1.0`**
   liefern, sondern muss fail-closed sein (kein Trade). Sonst ist das nächste von V2 promotete
   Epic wieder still auf 1,0. — **Merkposten für Phase 11:** genau dieses Risiko stand seit
   v1.5 als Doku-Notiz in `phase5_execution/CLAUDE.md` („non-DAX point_values provisional,
   re-baseline before live"). Eine Doku-Notiz hat es nicht verhindert. Das ist das stärkste
   Argument für **strukturelle** statt dokumentierter Guards.

### B2 — Der Reward-Score steigt nach **jedem** Verlust (⚠ invertiert die Lernrichtung)

**Fundstelle:** `phase7_reward/reward/scorer.py:115`

```python
debate_signal = 0.0 if debate_confidence is None else (debate_confidence - 0.5)
```

Der Code (und der Kommentar „*Weak, centred, additive*") nimmt eine Confidence in **[0,1]** an.
Geliefert wird `DebateOutcome.confidence` auf der **0–100-Skala**
(`phase5_execution/execution/executor.py:578` → `getattr(outcome, "confidence", None)`, in
`reward_pts.debate_confidence` als 57/58/60 persistiert).

**Nachgerechnet an Trade 7 (Zeile aus `reward_pts`):**

```
outcome_delta = 2.0 × (−0,975) × 1,0                     = −1,95      ✔ DB: −1,95
process_delta = 1,5 × (1,0 + 1,0 + (60,0 − 0,5))         = +92,25     ✔ DB: +92,25
total_delta   = clamp(−1,95 + 92,25, ±5)                 = +5,00
score_after   = 65 + 5                                                = 70,0      ✔ DB: 70,0
```

Der beabsichtigte „schwache Nudge" ist um **Faktor ~120** überdimensioniert und dominiert alles.
Folge: **der per-Trade-Delta clamped bei jedem Trade auf +5** — Gewinn oder Verlust ist
mathematisch irrelevant. Empirisch: `score_after` = **55 → 60 → 65 → 70** über vier aufeinander
folgende Totalverluste.

**Warum das nicht nur kosmetisch ist:**

- `Database.get_risk_level()` (`phase2_persistence/persistence/db.py:271`) macht bei Score > 50
  **`AGGRESSIV`** → `risk_pct` **3 %** statt 2 % (`phase5_execution/execution/config.py:112-113`).
  **Der Bot erhöht nach vier Verlusten in Folge seinen Risikoeinsatz um 50 %.**
- Derselbe Score steht im Research-Prompt (`bot score: 70 · risk level: AGGRESSIV`) — das Modell
  bekommt „gesunder Bot" gemeldet, während es die vier Verluste in derselben Nachricht liest.
- Die P7-Doku sagt „Confidence gatet nichts" — das stimmt. Aber der **Score** gatet sehr wohl
  (`select_risk_pct` → `get_risk_level`). Diese Kopplung ist nirgends als solche dokumentiert.

**Warum die Unit-Tests das nie gesehen haben:** `phase7_reward/tests/test_scorer.py` übergibt
`debate_confidence=0.9 / 1.0 / 0.0` — die Tests kodieren die **falsche** Skalenannahme.

⚠ **Der Ein-Zeichen-Fix repariert den Loop NICHT.** Mit `debate_confidence / 100 - 0.5` ergäbe
derselbe Verlust-Trade:
`−1,95 + 1,5 × (1,0 + 1,0 + 0,1) = **+1,2**` — der Score stiege **immer noch** bei jedem
Verlust (50 → 54,8 über vier Trades), weil ein SL-Treffer als `CLOSED_BY_BROKER` den
`clean_exit_bonus` von +1,0 kassiert und der enge Spread nochmal +1,0. **Ob ein Stop-out ein
„sauberer Exit" ist, ist eine Phase-11-Designfrage, kein Sonnet-5-Fix.**

### B3 — Der Leverage-Cap lässt **null** Margin-Headroom

**Fundstelle:** `phase5_execution/execution/config.py:114` (`max_leverage: float = 20.0`,
Kommentar „ESMA ceiling") + `execution/sizing.py:65`.

`cap_size = (available_balance × max_leverage) / (price × point_value)` fixiert die Nominale auf
**exakt** `available × 20`. Auf DAX ist dieser Cap **bei jedem Trade** bindend (das Risikomodell
verlangt bei 30-Punkte-Stop und 3 % Risiko rechnerisch ~25× Hebel). Der Bot fragt an **keiner
Stelle** die tatsächliche Margin-Anforderung des Brokers ab.

**Empirischer Beweis, selber Vormittag, selbes Epic:**

| Zeit (UTC) | Size | Level | Nominale | Ergebnis |
|---|---|---|---|---|
| 07-20 07:59 | 22,1 | 24.842 | 549.017 € | **REJECTED** `INSUFFICIENT_FUNDS` |
| 07-20 11:52 | 22,0 | 24.920 | 548.246 € | ACCEPTED (`DIAAAAX4BPA55AH`) |

Rekonstruktion: verfügbar waren 27.459,13 € (= gemessene 26.815,63 € + der 643,50-€-Verlust
dieses Trades). `27.459,13 × 20 / 24.842,41 = 22,104` → abgerundet **22,1** — die Size klebt auf
der Cap-Kante. Bei ~5 % Margin-Faktor (die branchenübliche Entsprechung zu 20:1; **nicht aus dem
Repo verifizierbar**) entspricht das ~100 % Margin-Auslastung. **Beweisbar ist die Mechanik:
die Nominale ist konstruktionsbedingt auf `available × max_leverage` gepinnt, also ohne jeden
Puffer** — die Accept/Reject-Grenze lag empirisch zwischen Size 22,0 und 22,1. Nebenwirkung:
eine zweite parallele Position (`max_parallel`) ist so nie finanzierbar.

### B4 — Das Mess-Substrat von Block A/B ist leer

- **`abstain_records`: alle 1.036 Zeilen haben `detail = ''` und `context_json = '{}'`.**
  Gespeichert wird de facto nur `(uuid, timestamp, reason)`. Die inhaltsreichste Information,
  die der Bot ~70× pro Tag erzeugt — die **Abstain-Begründung des Modells** — existiert
  in-memory (`Research.last_no_pick_reasoning`) und wird ausschließlich als
  Ein-Zyklus-Snapshot nach `scheduler_state.json.last_no_trade_detail` geschrieben, wo sie
  70× täglich überschrieben wird. **Wir werfen jeden Tag ~70 Begründungen weg und haben genau
  eine.** (Genau diese eine ist in dieser Analyse die halbe Beweislast — der Rest ist verloren.)
- **`market_regime_snapshots`: alle 722 Zeilen `data_source='quote_only'`, `degraded=1`,
  `atr_points`/`range_pct`/`spread_pct`/`regime_tag` NULL** — auch die **4 Happy-Path-Zeilen**
  (der echte TRADE vom 07-20 und die drei ABORTs), wo ein Kandidat, ein Epic und ein frisches
  `price_env` im Scope waren.
  - Die fehlenden Bars (→ ATR/Range/`regime_tag`) sind **bewusste, dokumentierte Degradation**
    (`phase10_v3/market_context/regime.py:1-12`, Plan §14 Drop-Order #3): VETO-3-Bars verlassen
    `vetos.py` nicht, und VETO-Code anzufassen war out-of-bounds. **Kein Bug.**
  - `spread_pct` ist jedoch **kein** Bar-Feature: `ContextRecorder.on_decision` hat den Parameter
    (`market_context/writer.py:150`), und **keiner der drei Call-Sites im Executor übergibt ihn**
    (`executor.py:185`, `:222`, `:385`). Auf dem Happy Path liegt der Wert vor — das
    `debate_log.json` desselben 07-30-Zyklus trägt `spread_pct: 0.00907`. Kleine, echte
    Verdrahtungslücke: ein Keyword-Argument an zwei Call-Sites.
  - Netto: die Tabelle speichert heute `(uuid, timestamp, epic, time_bucket)` — 722 Zeilen ohne
    Signal.

### B5 — Zwei Drittel der Paper-Lessons werden bezahlt und weggeworfen

`build_paper_lesson_prompt` (`phase10_v3/abstain_lessons/reflect.py:62-65`) verlangt „maximal
zwei Sätze", `validate_abstain_lesson` (:78) erzwingt aber **≤ 300 Zeichen** — die
Zeichengrenze steht **nicht** im Prompt. Am 07-27 liefen 6 Reflect-Calls (Haiku, 07:05:43–57);
persistiert wurden 2 Lessons (auf 5 Zeilen, eine pro Paar-Mitglied), Längen **292** und **278**
Zeichen — knapp unter der Grenze. Die anderen 4 fielen mit `AbstainLessonError` durch.
Ein-String-Fix: die Zeichengrenze in den Prompt schreiben.

---

## 5. Sieben Hypothesen für Phase 11 (V4)

Sortiert nach Hebel, nicht nach Aufwand. **H1 und H2 sind die beiden, die ich für nicht
verhandelbar halte** — alles andere ist Kür.

### H1 — Die Messung vom Funnel entkoppeln (größter Hebel, fast kein neuer Code)

**Problem:** Jedes Datenwerkzeug von V3 (Shadow-Pairs, Council-Picks, Abstain-Lessons,
Decision-Context) hängt hinter *„Research hat einen Kandidaten geliefert"*. Das ist in dieser
Woche **1× von 366** passiert. **Der Messapparat ist hinter genau dem Engpass eingesperrt, den
er messen soll.** Zwei Wochen Datensammlung sind daran gestorben — WI-2 ist zweimal aus zwei
verschiedenen Gründen tot, aber beide Male hinter derselben Kopplung.

**Vorschlag:** Shadow-Pairs **zeitgesteuert** erzeugen statt ereignisgesteuert. Pro aktivem Epic
alle N Minuten ein BUY/SELL-Paar auf den aktuellen Quote, gleiche Geometrie
(`stop_distance_points`/`limit_distance_points`/`max_hold_minutes`), Auflösung über den
bestehenden `PaperTradeTracker`.

- 8 aktive Epics × alle 30 min × 8,5 h ≈ **130 Paare/Tag**, ohne Kapitaleinsatz.
- Beantwortet **WI-2 an einem einzigen Tag** statt in Wochen — und WI-2 ist der Diskriminator
  zwischen W1 (Richtung) und W2 (Geometrie), also die Frage, die den ganzen Rest priorisiert.
- Nebeneffekt: liefert sofort die Stichprobe, um die 30/45-Punkte-Geometrie **pro Instrument**
  zu kalibrieren (auf AEX sind 30 Punkte 2,7 %, auf DAX 0,12 % — Faktor 23).

**Wiederverwendung — gegen den Code geprüft, nicht geschätzt:**

- `open_shadow_pair()` (`abstain_lessons/paper.py:182`) nimmt `abstain_record_id` als **plain
  `str`**, keinen `AbstainRecord` — die Funktion ist unverändert nutzbar.
- `paper_trades.abstain_record_id` ist `TEXT NOT NULL`, **ohne `REFERENCES`-Klausel** (Schema
  geprüft) → **keine Migration nötig**, ein synthetischer Schlüssel (z. B. `sched:<uuid>`)
  genügt. Empfehlung: eigenes Präfix, damit sich zeitgesteuerte Paare in der Auswertung von
  Debatte-Paaren trennen lassen.
- `PaperTradeTracker` bleibt **unverändert** — er gruppiert intern nur nach
  `trade.abstain_record_id` (beliebiger String) und macht **einen `get_ohlcv`-Call pro
  betroffenem Epic pro Tick**, nicht pro Trade.
- Neu zu bauen ist wenig, aber nicht nichts: ein Scheduler-Tick (Muster existiert:
  `universe_refresher` + `_due_after()`) **plus ein zweiter Einstiegspunkt am `PaperEngine`** —
  `on_debate_abstain(record)` erwartet einen `AbstainRecord` und ruft zusätzlich den
  Council-Pick; der zeitgesteuerte Pfad braucht die schlanke Variante (~10 Zeilen).

**Kosten — ehrlich beziffert (nicht „gratis"):**

- **LLM: praktisch null.** Der Reflect-Call hängt am `reflect_daily_cap` (Default **10**,
  `scheduler/config.py:160`), geteilt mit dem Abstain-Sink → 130 Paare/Tag ergeben **10 Lessons/
  Tag, nicht 130**. Die R-Multiples selbst entstehen komplett deterministisch.
- **IG-Allowance: nicht null.** Jedes Paar braucht einen frischen `broker.get_price(epic)` →
  ~**136 zusätzliche Quote-Calls/Tag** (8 Epics × 17 Intervalle) plus die `get_ohlcv`-Ticks des
  Trackers. Plan §10.2 hat den Quote-Call als Ausnahme genehmigt, **weil er selten feuerte** —
  bei diesem Volumen gehört ein Allowance-Budget dazu. Die Erschöpfung ist im Repo ein
  dokumentierter Fehlerfall (HTTP 403 `exceeded-*-allowance`, inline in `ig_adapter._request`).
  Stellschraube ist das Intervall; ein Quote pro Epic und Intervall reicht für beide Seiten
  des Paares.

### H2 — Die Sizing-Wahrheitskette reparieren (sicherheitskritisch, vor jedem Live-Gedanken)

B1 + B3 zusammen. Drei Teile:

1. `point_values` aus der DB-Universe speisen (§4 B1, Ein-Ausdruck-Fix).
2. Unbekanntes Epic → **fail-closed kein Trade**, nicht still 1,0.
3. Margin-Headroom: entweder `max_leverage` mit echtem Puffer (z. B. 10–12×) **oder** — sauberer
   — vor der Order die tatsächliche Margin-Anforderung beim Broker prüfen (IGs
   `get_market_info` liefert Margin-Felder; heute fragt der Bot sie nie ab).

**Begründung in einem Satz:** 4 von 8 Trade-Entscheidungen der Projekthistorie sind hieran
gestorben, und der schlimmste Fall war eine Order mit **120 % Kontorisiko**, die nur deshalb
nicht ausgeführt wurde, weil der Broker sie ablehnte.

### H3 — Den Reward-Loop tatsächlich etwas messen lassen

B2. Reihenfolge: (a) Skalenfehler beheben, (b) **danach** die Designfrage stellen, ob ein
SL-Treffer den `clean_exit_bonus` verdient (heute: ja — deshalb bleibt der Score auch nach dem
Skalen-Fix bei jedem Verlust positiv, +1,2/Trade), (c) die undokumentierte Kopplung
Score → `get_risk_level` → `risk_pct` entweder explizit dokumentieren oder auftrennen. Solange
(a)–(c) offen sind, ist `reward_pts` eine Trade-Zählung mit Extraschritten.

### H4 — Die Lesson-Sackgasse aufbrechen

Die Rückkopplung aus §3. Kandidaten, absteigend nach Aufwand-Nutzen:

- **Relevanz-Decay / Alters-Cap** auf `get_recent_lessons_for_prompt` — 4 Datenpunkte aus
  ~4 Wochen dürfen nicht dauerhaft 100 % der Entscheidungen dominieren. Reiner Code.
- **Doppelzählung beenden:** Lessons *und* `recent_trades` transportieren dieselben 4 Verluste
  in denselben Prompt. Einer der beiden Kanäle reicht.
- **Lessons skopieren:** heute sind es freie Prosa-Sätze ohne Richtung/Instrument. „BUY auf DAX
  nach +2,3 % Drift ist schlecht gelaufen" ist verwertbar; „prüfe die Entry-Qualität" ist es
  nicht — es kann nur dämpfen, nie korrigieren.
- ⚠ **S6 (Abstain-/Paper-Lessons in den Research-Prompt) bleibt AUS.** Die 5 vorhandenen
  Paper-Lessons sind tautologisch („ein 1,5R-Gewinner zeigt, dass 1,5R gut ist"), auf beiden
  Seiten desselben Paares **wortgleich**, und aus Backfill-Artefakten abgeleitet. Sie jetzt in
  die eine AI-Entscheidung zu speisen, würde die Rückkopplung verstärken, nicht lösen.

### H5 — Den Nachmittag zurückkaufen

WI-3, 10/10 Tage. Der Hebel ist **nicht** „Budget erhöhen" (0,75 €/Tag ist der gewollte Deckel),
sondern Kosten pro Zyklus: der Research-Prompt ist ~2.500 Input-Tokens × ~73 Calls/Tag.
`LLMClient(cache_system=True)` (Prompt-Caching) existiert bereits und wird von Phase 6 genutzt —
Research nutzt es **nicht**. Alternativ: Zyklus-Intervall vormittags strecken. Beides Code,
kein AI-Umbau. Erwarteter Effekt: Handelsfenster von ~6,4 h auf ~8,5 h, inkl. US-Open-Overlap.

### H6 — Das Mess-Substrat füllen (B4)

`Research.last_no_pick_reasoning` in die `abstain_records`-Zeile schreiben, die ohnehin schon
angelegt wird (`detail` ist da, `context_json` ist da — beide sind leer). Dazu `spread_pct` an
den drei `_notify_context`-Call-Sites durchreichen. Ohne das kann V3s Tabellenwerk **keine**
Frage beantworten — auch nicht die von Phase 11. Sehr kleiner Aufwand, hoher Informationsgewinn:
~70 Modell-Begründungen/Tag statt 1.

### H7 — Rahmen: die Geometrie-Frage ist die Wurzel, und sie ist offen

W2 (Stop 30 / Limit 45 auf DAX = 0,117 % / 0,176 %, beides unterhalb der eigenen
Momentum-VETO-Rauschschwelle von 0,15 %) erklärt „alle enden im SL" **hinreichend** — auch ein
perfektes Richtungssignal würde so überwiegend ausgestoppt. Alle 4 realen Trades starben nach
3,6 / 9,3 / 42,2 / 10,6 Minuten; **kein einziger** hat je Limit oder Time-Stop (240 min) gesehen.
Signalhorizont (Tagesdrift, 30-Tage-Breakout) und Stop-Horizont (Minuten) passen nicht zusammen.

**Solange W2 nicht empirisch beantwortet ist, ist jede Arbeit an der Richtungslogik verfrüht** —
man würde ein Signal für eine Geometrie tunen, die auch mit perfektem Signal verliert. H1 liefert
die Antwort in Tagen. **Deshalb ist H1 der erste *inhaltliche* Schritt von Phase 11** (H2 läuft
davor, weil es klein und sicherheitskritisch ist — s. §8).

---

## 6. Was ausdrücklich funktioniert (gegen Über-Fixen)

- **Daemon-Stabilität:** 10/10 Handelstage ohne Crash, ohne Kill, `consecutive_failures: 0`,
  Reconcile tickt bis in den Abend. Der 07-11-POST_WINDOW-Hotfix hält.
- **Fail-closed-Verhalten:** Broker-Reject → ABORT, keine Doppel-Order, write-ahead-Idempotenz
  sauber. Der 40×-Oversizing-Fehler hat **keinen** Schaden angerichtet, weil die Kette dahinter
  gehalten hat.
- **Der Bug-2-Fix vom 07-25 ist live bewiesen** — und zwar *anders als der 07-27-Block annahm*:
  am 07-27 liefen 6 Haiku-Reflect-Calls (07:05:43–57, je ~324 Input-Tokens) über **denselben**
  gefixten `_AbstainLLMAdapter._SCHEMA` (`wiring.py:304-309`, genutzt von Abstain-Sink *und*
  Paper-Pfad), 2 davon persistierten Lessons. Kein HTTP 400. Der 07-27-Block schrieb „kein Call
  wurde versucht" — das galt für den *Debatte-Abstain*-Pfad, nicht für den Adapter. **Der Fix
  ist bestätigt; offen bleibt nur der Debatte-Abstain-Trigger selbst.**
- **Die Paper-Pipeline ist end-to-end bewiesen:** open → resolve → Lesson lief am 07-27
  vollständig durch. Das ist genau das Werkzeug, das H1 braucht — es funktioniert, es wird nur
  fast nie aufgerufen.
- **VETOs:** in 6 Wochen nie ausgelöst — weil Research/Debatte vorher filtern, nicht weil sie
  tot sind. Unverändert kein Handlungsbedarf, aber weiterhin live-ungetestet.
- **Die Debatte:** 22/30 ABSTAIN. Bei der aktuellen Geometrie (W2) eher Schutz als Fehler.

## 7. Kleinkram (nicht handlungsbedürftig, nur protokolliert)

- **07-27: 73 Research-Zyklen, aber nur 72 `abstain_records`/`context_recorded`.** Der
  09:00:00-Eröffnungszyklus erzeugte keinen Record (yFinance-Circuit war zu diesem Zeitpunkt
  offen). Einmalig in der Woche — 07-28/29/31 sind exakt 1:1, 07-30 ist 71+1 Pick = 72.
  Der 07-27-Session-Block sagt „72 Zyklen, 1:1"; korrekt sind 73 Zyklen / 72 Records.
- **Datenqualität:** an **keinem** Zyklus der Woche war der Kontext für alle 6 Epics `full`.
  Pro Tag ~219 von 438 Epic-Beobachtungen `degraded`, dominiert von fehlendem `volume`
  (3 der 6 Epics haben keinen Volume-Proxy) plus dem bekannten yFinance-Morgenausfall
  (09:00–09:31, `^GDAXI`/`^FCHI`/`^IBEX` je 0 rows, danach volle Erholung). Das Modell zitiert
  die Volume-z-Scores der beiden Epics, die welche haben, als Abstain-Argument
  („low participation").
- **Der Scheduler-Daemon lief zum Zeitpunkt dieser Analyse (Fr 21:26 lokal) nicht mehr**
  (letzter Reconcile 21:22, kein Prozess). Freitagabend nach Marktschluss unauffällig — falls
  das nicht der Nikinger war, startet er sich Montag aber auch nicht von selbst.
- `logs/scheduler_5a_variety_.log` beginnt erst am 07-29 08:01 (Daemon-Neustart, Datei
  überschrieben) — die 07-27-Reflect-Fehlschläge aus B5 sind daher nicht mehr im Log
  nachweisbar, nur über `llm_usage.json` + die DB rekonstruierbar.

---

## 8. Empfehlung

1. **Genug Daten für den Phase-11-Schnitt.** Die Vordiagnose-Thesen sind jetzt entschieden:
   **W1 bestätigt** (frisches Zitat), **W5 bestätigt** (frisches Zitat + 4.529 Renderings),
   **W3 bestätigt** (10/10 Tage), **W2 weiterhin offen** — und W2 ist die Wurzel.
2. **Nicht auf eine dritte Woche warten.** Zwei Wochen sind an derselben Kopplung gestorben.
   Eine dritte identische Woche liefert eine dritte identische Zeile in dieser Tabelle.
3. **Reihenfolge für Phase 11: H2 → H1 → H6**, dann mit echten Daten H7/H4/H3/H5 entscheiden.
   H2 steht vorn, **weil klein und sicherheitskritisch** (eine Order mit 120 % Kontorisiko darf
   nicht zweimal entstehen), nicht weil es das Wichtigste ist — **der erste inhaltliche Schritt
   ist H1**, und H6 macht dessen Ergebnisse überhaupt erst auswertbar.
4. **Die drei Bugs B1/B2/B5 sind ohne Phase-11-Scope fixbar** (klein, additiv, in bereits
   berührtem Code, jeweils mit Testabdeckung nachzuziehen — bei B2 zusätzlich die Testskala in
   `test_scorer.py` korrigieren, sonst bleibt der Fix ungeprüft). B3/B4 gehören in den
   Phase-11-Scope, weil sie Designentscheidungen brauchen.
