---
status: snapshot
purpose: Auswertung der ersten Datenwoche (2026-07-20 bis 2026-07-24, --enable-paper-debate) gegen WI-1...WI-6 aus der Vordiagnose — Ergebnis: zwei der Mess-Pipelines liefen die ganze Woche fehlerhaft; V4-Scope-Entscheidung verschoben auf eine saubere Woche
read-when: bei der V4-Scope-Entscheidung, oder beim Nachvollziehen warum WI-1/WI-2 diese Woche nicht beantwortbar waren
detail: L3
up: ./CLAUDE.md
updated: 2026-07-25
---

# Datenwoche-Review — 2026-07-25 (Mo 07-20 bis Fr 07-24)

> **Kopfbefund zuerst, damit nichts falsch gedeutet wird:** Diese Woche hat die zwei
> wichtigsten Fragen der Vordiagnose (`TRADE_DATA_DIAGNOSIS_2026-07-19.md`) **nicht**
> beantwortet — nicht weil die Daten dagegen sprechen, sondern weil zwei der drei
> eingesetzten Mess-Werkzeuge die ganze Woche über **fehlerhaft liefen** (100 % Fehlerquote,
> silent, `logger.critical`-only). Einen V4-Scope aus dieser Woche zu schneiden hieße, die
> Lücke mit Vermutung zu füllen — genau das, was vermieden werden soll. **Empfehlung: V4-Schnitt
> verschieben auf eine saubere Woche**, nach den beiden Fixes unten + einer Operator-Klärung.

## Watch-Item-Status (gegen `TRADE_DATA_DIAGNOSIS_2026-07-19.md`)

| # | Frage | Status diese Woche | Warum |
|---|---|---|---|
| WI-1 | Kommt an einem roten Tag ein echter SELL-Seed? | **Nicht testbar** | Research erreichte Di–Fr **an keinem einzigen Zyklus** die Kandidaten-Stufe (100 % `REASON_NO_CANDIDATES`, 4 volle Tage). Montags einziger Handelstag zeigte durchgehend **positiven** Drift (0.33–0.81 %) — kein roter Tag im gesamten Fenster, an dem Research überhaupt einen Seed produzierte. |
| WI-2 | Shadow-Pair-Exit-Verteilung (das Schlüssel-Experiment) | **Tot** | 15 Paper-Trades erzeugt (6 Shadow-Paare + 3 Council-Picks, alle Montag), **0 aufgelöst** — Tracker-Bug, s. u. |
| WI-3 | Budget-Kappe täglich ~14–15 Uhr? | **Bestätigt** | 5/5 Tage 193k–202k Tokens (Kappe 200k); letzter Research-Zyklus 14:34–15:45 lokal, jeden Tag. |
| WI-4 | Paper-Zeilen ohne Flag-Flip ≈ 0? | **Bestätigt (invertiert bestätigt)** | Mit `--enable-paper-debate` liefen 15 Paper-Trades an einem Tag — der Flip wirkt architektonisch wie geplant. Aber: nur Montag, weil Di–Fr keine Debatte mehr stattfand (Funnel-Kollaps, neuer Befund unten). |
| WI-5 | Lesson-Zitat-Häufigkeit in Abstain-Begründungen | **Keine frische Evidenz** | `last_no_trade_detail` (nur Snapshot des letzten Zyklus) zeigt diese Woche keinen Lesson-Zitat-Fall; die Vorwochen-Belege aus der Diagnose bleiben unverändert gültig, nichts Neues bestätigt oder widerlegt. |
| WI-6 | Entry-Timing nahe Square-off? | **Keine neue Evidenz** | Der einzige reale Trade dieser Woche (13:51 lokal) liegt weit vor Square-off (17:15) — bestätigt W6 nicht zusätzlich, widerlegt es aber auch nicht. |

## Neue Befunde (wichtiger als die WI-Liste)

### N1 — Broker-Reject `INSUFFICIENT_FUNDS`, zweimal, DAX **und** AEX (widerlegt die AEX-Stop-Distanz-Hypothese)

Zwei der drei TRADE-Entscheidungen dieser Woche wurden vom Broker abgelehnt, **nicht** wegen
Stop-Distanz (die aus der Bug-B-Nachsession unbestätigt vermutete AEX-spezifische Ursache ist
damit widerlegt — derselbe Fehler traf zuerst DAX):

- `2026-07-20T07:59:22Z` DAX (IGN), TRADE @ conf 58 → `ABORT`, `abort_detail`: *"order … REJECTED
  by broker: INSUFFICIENT_FUNDS"*
- `2026-07-20T08:20:35Z` AEX, TRADE @ conf 62 → `ABORT`, gleicher Grund
- `2026-07-20T11:52:17Z` DAX (IGN), TRADE @ conf 60 → **erfolgreich** (`deal_id=DIAAAAX4BPA55AH`,
  size 22.0, später −643.50 € per SL — vierter BUY-DAX-Stop-out in Folge, bestätigt Befund W2 aus
  der Vordiagnose erneut)

**Das ist kein flaches "Konto zu klein"** — derselbe Vormittag hatte einen erfolgreichen Trade
mit vergleichbarer Size (22.0 vs. unbekannt bei den Rejects, aber gleiche Größenordnung). Die
verfügbare Margin schwankt offenbar. Naheliegendste Erklärung (aus dem Bestand bekannt, nicht neu
verifiziert): `phase7_reward/CLAUDE.md` dokumentiert **zwei stehengebliebene OPEN-Demo-Deals**
aus früheren Debug-Läufen (`DIAAAAXTGBTEYAC`/`DIAAAAXTGMAF2A9`), die seit Wochen Margin binden
könnten, kombiniert mit dem kumulierten Verlust von jetzt ~4×~650 € auf einem Konto unbekannter
tatsächlicher Größe (Doku nennt "~30K", unverifiziert).

**Operator-Check durchgeführt (2026-07-25, Nikinger, `broker_wrapper.cli`):**

```
get-account   → balance=26815.63, available=26815.63, profit_loss=0.0, currency=EUR
get-positions → positions: []
```

**Ergebnis: die Stale-Deal-Hypothese ist widerlegt.** `available == balance` exakt, **keine**
offenen Positionen (auch die beiden alten Debug-Deals aus `phase7_reward/CLAUDE.md` sind nicht
mehr da/gebunden) — kein anhaltendes Margin-Problem. Die Balance selbst ist plausibel (~30K
Doku-Annahme minus die inzwischen 4 realen Verluste à ~650 € ≈ 27.5K, nah an den gemessenen
26.815,63 €) — auch keine unerwartete Konto-Verkleinerung.

**Damit bleibt Montags `INSUFFICIENT_FUNDS` unerklärt, aber nachweislich transient/
zeitpunktbezogen** — kein Dauerzustand. Denkbare Erklärungen (keine geprüft, nur benannt): eine
kurzzeitige IG-eigene Margin-Reservierung durch die zwei fast gleichzeitigen Order-Versuche
(07:59 DAX, 08:20 AEX, nur 21 Min. auseinander) oder eine Diskrepanz zwischen der bot-seitigen
Sizing-Annahme (fixer Hebel/`point_value`) und IG's tatsächlicher Margin-Berechnung im jeweiligen
Moment. **Kein Fix vorgeschlagen** — mangels Reproduktion nichts Konkretes zu tun außer
beobachten: sollte der Reject nächste Woche wiederkehren, lohnt ein Blick auf den zeitlichen
Abstand zum letzten Order-Versuch und auf `get_account` unmittelbar danach (nicht Tage später).

### N2 — Funnel-Kollaps: Di–Fr komplett null Kandidaten (schlimmer als die Vorwoche)

Anders als die Vordiagnose ("~97.6 % Abstain, aber doch gelegentliche Picks") zeigte diese Woche
an **vier von fünf Tagen 100 % `REASON_NO_CANDIDATES`** — nicht ein einziger Zyklus erreichte
Gate 2. Nur Montag produzierte 9 Debatten. Das ist eine eigene, unbeantwortete Frage für eine
saubere Woche: ist das Marktregime-bedingt (eine besonders flaue Woche) oder ein weiterer
struktureller Effekt? Mit nur einer Woche Beobachtung nicht unterscheidbar — **kein Fix
vorgeschlagen, nur benannt.**

## Zwei Bugs — root-caused, gefixt diese Session (Details: 🔁-Notes in `phase8_scheduler/CLAUDE.md`)

Beide Fixes sind additiv, ein-Wert-Korrekturen in bereits von V3 Block A/B berührten Dateien,
am Wochenende bei gestopptem Bot, mit Unit-Test — passt in die "kleine, notwendige Bereinigung,
mit Notiz an den Nikinger"-Erlaubnis der Root-Konventionen. Kein Gate/VETO/Order-Pfad berührt.

**Bug 1 — `PaperTradeTracker` hat noch nie einen Paper-Trade aufgelöst (100 % Fehlerquote, seit
Block B am 07-17).** `phase8_scheduler/scripts/wiring.py:448` ruft
`broker.get_ohlcv(epic, "MINUTE_1", …)` — `"MINUTE_1"` ist keine gültige IG-Resolution (gültig:
`"MINUTE"`, `MINUTE_2/3/5/10/15/30`, …). 422 identische `CRITICAL`-Logs allein diese Woche,
0 Erfolge seit Rollout. Einzige Fundstelle im ganzen Repo (grep bestätigt). **Fix:** String auf
`"MINUTE"` korrigiert. **Wichtig: die 15 diese-Woche-erzeugten Paper-Trades sind trotz Fix nicht
mehr rettbar** — ein künftiger Tick holt nur aktuelle Bars, keine Historie bis zurück zum
Montag-Erstellungszeitpunkt. Die WI-2-Stichprobe dieser Woche ist verloren; der Fix wirkt erst
vorwärts.

**Bug 2 — `reflect_abstain` (Haiku-Lesson aus Debatte-Abstains) hat seit Rollout (07-15) noch nie
eine Lesson erzeugt.** Mechanismus jetzt zweifelsfrei aus den Logs bestätigt (nicht mehr
"unrekonstruierbar" wie im Week-1-Review): Anthropic lehnt den Structured-Output-Call mit
HTTP 400 ab (*"For 'object' type, 'additionalProperties' must be explicitly set to false"*) —
`_AbstainLLMAdapter._SCHEMA` (`wiring.py`) hat dieses Feld nicht, anders als das seit Wochen
funktionierende `brain.py`-Schema (`phase7_reward/reward/brain.py`), das es hat. Der Code fällt
korrekt auf den Klartext-Fallback zurück, aber `build_abstain_prompt` fordert nirgends JSON an →
die Klartext-Antwort (deutsche Prosa) lässt `json.loads` mit exakt dem beobachteten Fehler
scheitern. **Fix:** `additionalProperties: False` zum Schema ergänzt (identisch zum
bewährten `brain.py`-Muster) — der Prompt selbst muss nicht geändert werden, sobald Structured
Outputs greift, ignoriert das Modell die Klartext-Formulierung im Prompt ohnehin und liefert
Schema-konformes JSON (wie bei jedem anderen erfolgreichen `ask_candidate`-Call im Projekt).

## Empfehlung

1. **Kein V4-Scope aus dieser Woche schneiden.** Die Vordiagnose-Thesen W1–W6 bleiben unverändert
   in Kraft (nichts widerlegt, WI-3/WI-4 bestätigt, WI-1/WI-2 nur nicht testbar) — plus die zwei
   neuen Befunde N1 (Margin) und N2 (Funnel-Kollaps Di–Fr).
2. **Operator vor der nächsten Datenwoche:** `get_account`/`get_open_positions` prüfen (N1) —
   ohne das bleibt jede weitere Woche demselben Risiko ausgesetzt, Trades erneut wegzuwerfen.
3. **Nächste Datenwoche** läuft dann mit beiden Bugfixes automatisch sauberer (Paper-Pipeline
   funktionsfähig) — dort WI-1/WI-2 erneut prüfen, plus im Auge behalten, ob N2 (Funnel-Kollaps)
   sich wiederholt oder eine Ausnahme dieser Woche war.
