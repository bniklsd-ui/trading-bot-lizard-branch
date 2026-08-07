---
status: snapshot
purpose: Erste H1-Live-Woche ausgewertet — Funnel weiterhin kollabiert (0 Kandidaten, 5/5 Tage), aber der eigentliche Befund ist ein IG-`/prices`-Endpoint-Ausfall ab 08-04, ausgelöst durch die 5-Minuten-Tracker-Kadenz (nicht den 30-Minuten-Öffnungs-Intervall), der über die Promotion-Pipeline fast das gesamte `instrument_universe` in Quarantäne geschickt hat. WI-2/W2 bleibt unbeantwortet (kein einziger TIME_STOP diese Woche — die Frage wurde nie erreicht, nicht widerlegt).
read-when: vor einem Scheduler-Neustart mit `--enable-shadow-schedule`, oder beim Nachvollziehen warum `instrument_universe` von >20 auf 4 aktive Epics geschrumpft ist
detail: L3
up: ./CLAUDE.md
updated: 2026-08-07
---

# Datenwoche-Review 3 — 2026-08-07 (Mo 08-03 bis Fr 08-07, H1 erstmals live)

> **Kopfbefund, damit nichts falsch gedeutet wird:** Der Scheduler lief die ganze Woche
> durchgehend (ein einziger Start 2026-08-01 12:18 lokal, kein Neustart, kein Crash, sauberer
> Stop kurz vor dieser Session) — **kein Trading-Risiko**: 0 echte Trades diese Woche, die
> `trade_outcomes`-Tabelle ist seit 07-20 unverändert. Der Forschungs-Funnel ist weiterhin
> vollständig kollabiert (0 Kandidaten an allen 5 Tagen, wie in den beiden Vorwochen). H1
> (zeitgesteuerte Shadow-Pairs) hat produziert wie geplant — **und genau dadurch einen
> IG-`/prices`-Ausfall aufgedeckt**, der ab Montagnachmittag (08-04) einsetzte, bis heute
> (Freitag, 08-07 15:14 lokal, letzter Verify-Versuch) nicht behoben ist, und über die
> Phase-9-Promotion-Pipeline **18 von 22 `instrument_universe`-Epics in Quarantäne geschickt
> hat — inklusive des seit Wochen live-verifizierten Kerns** (DAX/CAC/IBEX/AEX/STXE,
> `point_value_source='ig_fields'`). Das ist der eigentlich wichtige Befund dieser Woche, nicht
> die Shadow-Pair-Zahlen selbst.
>
> **WI-2/W2 bleibt unbeantwortet.** Von den 95 resolved Shadow-Pair-Trades (alle aus 08-03 +
> der ersten Hälfte von 08-04, bevor der Ausfall griff) hat **kein einziger** einen `TIME_STOP`
> gesehen — aber das ist **keine** Antwort auf W2 (Geometrie vs. Signalhorizont), sondern ein
> Artefakt: `TIME_STOP` erfordert Bars bis `time_stop_utc`, und genau die Bars blieben durch
> den Ausfall aus. W2 wurde diese Woche nicht getestet, nicht widerlegt.
>
> Quellen (alle read-only, `mode=ro` / Log-Lesen): `data/trading_bot.sqlite`,
> `data/state/scheduler_state.json`, `logs/scheduler_5a_variety_.log` (8636 Zeilen,
> durchgehend 08-01 12:18 bis 08-07 17:28). Kein Code berührt, keine Migration, kein
> Scheduler-Neustart.

---

## 1. Faktenlage der Woche

| Tag | Research-Zyklen (Abstains) | Kandidaten | Shadow-Pairs geöffnet | davon resolved | davon expired | davon noch OPEN (Stand 08-07) |
|---|---|---|---|---|---|---|
| Mo 08-03 | 72 | 0 | 144 | 144 | 0 | 0 |
| Di 08-04 | 67 | 0 | 128 | 46 | 82 | 0 |
| Mi 08-05 | 74 | 0 | 128 | 0 | 0 | 128 |
| Do 08-06 | 73 | 0 | 128 | 0 | 0 | 128 |
| Fr 08-07 | 74 | 0 | 72 | 0 | 0 | 72 |
| **Σ** | **360** | **0** | **600** | **190\*** | **82\*** | **328** |

\* Korrektur zur Erstauswertung im Chat: 190 = 144 (08-03, alles resolved) + 46 (08-04, nur die
Vormittagshälfte). `abstain_records` (360, alle `REASON_NO_CANDIDATES`) bestätigt den seit
zwei Wochen bekannten Funnel-Kollaps unverändert — nichts Neues gegenüber
`DATA_WEEK_REVIEW_2026-07-31.md` §1/§2, hier nicht erneut vertieft.

**Pair-Volumen war höher als in der letzten Session geschätzt** (dort: „~80 Paare/Tag bei
8 aktiven Epics"): 144 am Montag, weil das aktive Universum zu diesem Zeitpunkt bereits über
8 Epics hinausgewachsen war (Phase-9-Promotion lief seit der letzten Review weiter und hatte
neue Instrumente aktiviert, unabhängig von H1). Die 30-Minuten-Deadline-Guard-Rechnung aus der
letzten Session war korrekt für 8 Epics — das reale Universum war größer, bis der Ausfall es
wieder auf 4 zurückwarf (s. §3).

**Council-Paper-Call:** die 3 `COUNCIL_PICK`-Zeilen in der DB sind Altbestand vom 07-20 (der
frühere `--enable-paper-debate`-Testtag), keine neuen diese Woche — konsistent mit 0 echten
Debatten (der Call hängt an `REASON_DEBATE_ABSTAIN`, die diese Woche nie auftrat).

---

## 2. H1-Befund: was die Shadow-Pairs zeigen — und was nicht

**Korrektur einer Fehllesung aus der Chat-Erstauswertung:** die anfängliche Lesart „52 SL zu
43 TP, also ~45 % Trefferquote" war falsch. Bei einem Both-Sides-Paar (gleicher Entry, SL 30 /
TP 45 Punkte, spiegelverkehrt BUY+SELL) ist die SL/TP-Verteilung **mechanisch gekoppelt, keine
Trefferquote**:

- Move ≥ 45 Punkte in eine Richtung → eine Seite TP, die Gegenseite SL → **1 TP + 1 SL**.
- Move 30–44 Punkte, dann Umkehr → eine Seite SL, die Gegenseite bleibt unresolvable in den
  verbliebenen Bars → **1 SL allein** (Singleton).
- Move bleibt innerhalb ±30 Punkte → keine Seite resolved.

Gegenprobe an den echten Paar-Mustern (95 resolved Zeilen, gruppiert nach
`abstain_record_id`): 43 vollständige Paare (22+21, beide Seiten resolved) × 2 Zeilen = 86,
plus 9 Singleton-`SELL:SL`-Zeilen (Gegenseite dieses Paars noch offen/expired) = **86 + 9 = 95,
exakt** — keine unerklärte Differenz:

| Muster | Anzahl | Bedeutung |
|---|---|---|
| `BUY:SL, SELL:TP` | 22 | Move ≥45 Pkt nach unten |
| `BUY:TP, SELL:SL` | 21 | Move ≥45 Pkt nach oben |
| `SELL:SL` (Singleton) | 9 | Move 30–44 Pkt nach oben, dann Umkehr — **alle 9 SELL, keine BUY** |

**Das sagt die Daten wirklich aus:** von 52 SL-Ereignissen entstanden 43 aus einem
vollständigen ≥45-Punkte-Move (eine Aussage über die realisierte Tagesrange, keine über Edge)
und 9 aus einem 30–44-Punkte-Move mit Umkehr — und alle 9 davon sind `SELL:SL`, keine einzige
`BUY:SL`. Das ist richtungskonsistent mit dem in `scheduler_state.json` festgehaltenen
Marktbild dieser Woche (DAX 0,06 % unter dem 30-Tage-Hoch, 1,05 % Drift) — ein steigender
Markt lässt SELL-Positionen häufiger auf halbem Weg umkehren, bevor sie TP erreichen. Kohärent,
kein Bug, aber ein Beleg für Richtungs-Bias in der Truncation, nicht für Geometrie-Edge.

**Was diese Woche NICHT beantwortet wurde:** ob die 240-Minuten-Haltedauer je erreicht wird
(W2s eigentliche Frage — Signalhorizont vs. Stop-Horizont). `resolve_paper_trade` sah in
keinem der 95 Fälle genug Bars, um bis `time_stop_utc` zu kommen, **weil der IG-Ausfall genau
in diesem Zeitraum begann** — nicht weil das Signal/die Geometrie das Zeitfenster nie erreicht.
Die 82 `EXPIRED_UNRESOLVED` vom Dienstag sind derselbe Effekt: `resolve_paper_trade` bekam
Bars, aber nicht genug, um die volle Haltedauer abzudecken (s. §3 für den Mechanismus). WI-2
bleibt offen — braucht eine Woche ohne diesen Ausfall.

---

## 3. Der eigentliche Befund: IG-`/prices`-Ausfall + Kaskaden-Schaden am `instrument_universe`

### 3.1 Endpoint-spezifisch, nicht Session-weit

`instrument_universe.checks_json` (von der Phase-9-Promotion-Pipeline, `verify_instrument.py::
check_ig_side`, unabhängig vom H1-Code) zeigt für **jedes** der 18 heute quarantined Epics
denselben Bruch, in **derselben** Verify-Runde, Sekunden auseinander:

```
"currency_eur": true, "min_deal_size_ok": true, "ig_ohlcv_available": false
```

`currency_eur`/`min_deal_size_ok` kommen aus `get_market_info` (funktioniert),
`ig_ohlcv_available` aus einem `get_ohlcv`-Probe (`/prices/{epic}`, schlägt fehl) — **derselbe
Auth, dieselbe Session, ein Endpoint tot, der andere gesund.** Das ist ein enger Beleg für eine
endpoint-spezifische Sperre (typischerweise IGs separates Historical-Price-Allowance-Kontingent,
getrennt vom allgemeinen Request-Limit) — die genaue Ursache (Wochenkontingent erschöpft vs.
etwas anderes) ist von hier aus nicht abschließend feststellbar; das ist ein Live-Check
(Nikinger, per Repo-Konvention).

### 3.2 Root Cause: die 5-Minuten-Tracker-Kadenz, NICHT der 30-Minuten-Öffnungs-Intervall

**Korrektur zur letzten Session:** dort stand „der Intervall-Regler (`shadow_schedule_interval_min`)
ist die Stellschraube, falls die IG-Allowance zu heiß läuft." Das ist falsch für dieses
Ausfallmuster. `shadow_schedule_interval_min` (30 min) steuert nur das **Öffnen** neuer Paare.
Das **Resolven** läuft über `_run_paper_tracker()`, das im WINDOW-Zweig **jeden** Zyklus tickt —
`cycle_interval_min` = 5 min, ~102 Ticks/Tag, unverändert seit Block B (2026-07-17), aber vor H1
mit fast nichts zu tun (nur die seltenen Debatte-Abstain-Paare). Ein `get_ohlcv`-Call pro Epic
mit fälliger `OPEN`-Position, pro Tick:

```
Ausfall beginnt → get_ohlcv schlägt fehl → Trade bleibt OPEN (Exception, kein resolve/expire)
   ↓
nächster Tick, 5 min später: derselbe Trade ist immer noch fällig + neue Paare kamen dazu
   ↓  (Rückstand wächst monoton, jeder Tick mehr betroffene Epics als der vorige)
```

Beleg direkt aus dem Log — CRITICAL-Zeilen `PaperTradeTracker bar fetch failed` pro Tag,
**monoton eskalierend**, kein Plateau:

| Tag | CRITICAL (bar fetch failed) |
|---|---|
| Mo 08-03 | 218 |
| Di 08-04 | 516 |
| Mi 08-05 | 786 |
| Do 08-06 | 1148 |
| Fr 08-07 | 1564 |
| **Σ** | **4232** |

Das passt exakt zur Größenordnung (~1000+/Tag), die eine wachsende Rückstands-Menge über eine
5-Minuten-Kadenz erzeugt — nicht zu einer 30-Minuten-Kadenz. **Für Montag heißt das konkret:**
ein Neustart mit demselben Flag würde sofort wieder gegen einen möglicherweise noch toten
Endpoint anlaufen, weil 328 `OPEN`-Zeilen (Stand heute) beim nächsten Tick alle erneut fällig
sind — das ist der eine Punkt, der einen Neustart blockiert (s. §5).

**Genau dieselbe Last am 08-07 selbst gesunken (1564 statt weiter steigend)** — nicht weil sich
etwas erholt hat, sondern weil die Promotion-Pipeline zwischenzeitlich fast das ganze Universum
demotiert hat (s. §3.3): weniger aktive Epics → weniger neue Paare pro Tick → langsamer
wachsender Rückstand. Der Ausfall hat begonnen, seine eigene Messfläche zu verkleinern.

### 3.3 Kaskaden-Schaden: `instrument_universe` von >20 auf 4 aktive Epics

`check_ig_side` (derselbe `get_ohlcv`-Probe) läuft **unabhängig von H1** auch in der
Phase-9-Promotion (`universe_refresher`, alle 240 min). Ein IG-seitiger Fail demotiert nach
`demote_after_fails` (= 3) in Quarantäne — korrektes Verhalten für ein wirklich schlechtes
Instrument, aber hier trifft es **jedes** Instrument gleichermaßen, weil der Endpoint selbst tot
ist, nicht die Instrumente:

| Status | Anzahl | Anmerkung |
|---|---|---|
| `quarantined` | 18 | inkl. des seit Wochen live-verifizierten Kerns (DAX×2, CAC, IBEX×2, AEX×2, STXE — alle `point_value_source='ig_fields'`) |
| `active` | 4 | alle `IX.D.SUN*` (neuere Discovery-Funde), `fail_count=2`, `data_degraded=1` — **eine Verify-Runde vom Aussterben entfernt** |

Das ist **nicht** ein Messproblem, das sich mit mehr Zeit von selbst löst — es ist eine
Fehlinterpretation eines Verfügbarkeits-Ausfalls als Instrumenten-Untauglichkeit, mit echten
Kosten: Phase 9 hat Wochen gebraucht, um den Kern auf `ig_fields`-Pricing zu verifizieren
(s. `phase9_universe/CLAUDE.md`), und der ist jetzt weg. Wenn der Ausfall anhält, demotiert die
nächste Verify-Runde auch die letzten 4.

---

## 4. Kleinkram (nicht handlungsbedürftig diese Woche, nur protokolliert)

- **B5-Restfehlerrate:** trotz des 07-31/08-01-Fixes (Zeichengrenze jetzt im Prompt) schlugen
  diese Woche **10 von 68** Reflect-Versuchen (`abstain_lessons/reflect.py`) weiterhin mit
  „lesson text too long" fehl (321–382 Zeichen bei einer 300-Zeichen-Grenze), alle am 08-03/08-04
  (den einzigen Tagen mit resolved Pairs). Der Fix reduziert die Rate, schließt sie nicht — das
  LLM überschreitet die im Prompt genannte Grenze weiterhin gelegentlich. Kein neuer Bug, nur
  quantifiziert; ein Kandidat für eine härtere serverseitige Kürzung statt Prompt-Instruktion,
  falls das relevant wird.
- **`env.error` wird verschluckt:** `phase8_scheduler/scripts/wiring.py::_build_paper_tracker`s
  `bar_fetch` wirft `RuntimeError(f"get_ohlcv not ok for {epic}")` ohne `env.error` — bei 4232
  CRITICAL-Zeilen diese Woche stand **nirgends im Log** der tatsächliche IG-Fehlercode. Die
  Diagnose in §3.1 kam ausschließlich über `instrument_universe.checks_json` zustande (ein
  Nebenprodukt der Promotion-Pipeline, nicht des Trackers selbst). Reine
  Beobachtbarkeits-Lücke, kein Verhaltens-Bug — Fix-Kandidat für eine Wochenend-Session.
- **Der Council-Paper-Call-Flag-Status dieser Woche** ist aus dem Log nicht rekonstruierbar
  (dasselbe bekannte `run_scheduler.sh`-Logging-Loch wie in der 07-31-Review) — ohne Belang, da
  ohnehin 0 Debatten liefen.

---

## 5. Was ausdrücklich funktioniert (gegen Über-Fixen)

- **Daemon-Stabilität unverändert stark:** ein einziger Start (08-01 12:18 lokal), **kein**
  Neustart, **kein** Crash, **kein** Backoff-Trip über die gesamte Woche trotz 4232
  CRITICAL-Zeilen — jede einzelne davon lief durch den bestehenden Best-Effort-Try/Except-Pfad
  (`PaperTradeTracker.tick`/`_run_paper_tracker`), genau wie designed. Der Ausfall hat den
  Haupt-Zyklus (Research/Gates/VETOs) nicht ein einziges Mal beeinträchtigt.
- **Kein Order-Risiko:** 0 echte Trades diese Woche (der Funnel produzierte 0 Kandidaten),
  `trade_outcomes` unverändert seit 07-20. Der eine `RATE_LIMIT`-Abort (08-04, Executor-
  Account-Snapshot) griff korrekt fail-closed, kein Doppel-Order-Risiko.
- **Sauberer Stop:** kein `KILL`-File gesetzt, letzter Reconcile 23:13 lokal (kurz vor dieser
  Session) — konsistent mit einem manuellen, geordneten Stop, nicht einem Absturz.
- **H1s eigener Code (Öffnen der Paare) lief fehlerfrei:** 0 `open_scheduled_pairs failed`-
  Zeilen die ganze Woche — `quote_fetch` (`get_price`) blieb durchgehend gesund, nur
  `get_ohlcv` (Tracker-Seite) brach ein. Die Diagnose in §3.2 bestätigt, dass H1s eigene
  Deadline-Guard-Logik (aus der letzten Session) korrekt griff — sie verhindert nur das
  *Öffnen* verspäteter Paare, nicht die hier gefundene *Resolve*-Lawine, weil letztere über den
  vorbestehenden Block-B-Tracker-Tick läuft, den die letzte Session nicht angefasst hat.

---

## 6. Empfehlung

1. **Vor jedem Neustart mit `--enable-shadow-schedule`: IG-`/prices`-Gesundheit live
   bestätigen** (Nikinger, Live-/Netzwerk-Check per Repo-Konvention — z. B. ein einzelner
   `get_ohlcv`-Call gegen `IX.D.DAX.IFMM.IP`). Ohne diese Bestätigung würde ein Neustart sofort
   wieder gegen die 328 fälligen `OPEN`-Zeilen anlaufen (s. §3.2) — entweder den Endpoint erst
   bestätigen, oder das Flag vorerst wieder aus lassen.
2. **`instrument_universe`-Entscheidung (Nikinger):** die 18 quarantined Epics per DB-Reset
   zurücksetzen (Präzedenzfall 2026-07-06, `phase9_universe/CLAUDE.md` „Nachtrag") sobald der
   Endpoint bestätigt gesund ist, oder abwarten, ob die Promotion-Pipeline sich von selbst
   erholt (sie tut das nur, wenn künftige Verify-Runden wieder `ig_ohlcv_available: true` sehen
   — kein automatischer Reset des `fail_count` ohne das). Die verbleibenden 4 aktiven Epics
   stehen bei `fail_count=2/3` — ohne Eingriff kippen sie in der nächsten Runde auch.
3. **Für eine Wochenend-Session (nicht jetzt):** zwei Fix-Kandidaten aus §3.2/§4 —
   (a) `env.error` in `bar_fetch` nicht verschlucken (kleine, isolierte Änderung), (b) die
   Tracker-Kadenz von der 5-Minuten-WINDOW-Schleife entkoppeln oder mit einem eigenen,
   längeren Intervall drosseln, damit ein einzelner Endpoint-Ausfall nicht mit wachsendem
   Rückstand eskaliert, statt gleichbleibend zu bleiben. Beides Nikinger-Entscheidung, keine
   Selbstläufer.
4. **WI-2/W2 braucht eine echte Woche.** Sobald der Endpoint bestätigt gesund ist und das
   Universum sich erholt hat (oder zurückgesetzt wurde), ist H1 selbst unverändert einsatzbereit
   — der Code hat sich diese Woche nicht als fehlerhaft erwiesen, nur als abhängig von einer
   Ressource, die ausfiel.
