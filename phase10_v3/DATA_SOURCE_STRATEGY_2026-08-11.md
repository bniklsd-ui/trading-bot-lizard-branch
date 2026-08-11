---
status: snapshot
purpose: Entscheidung zur Bar-Datenquelle, nachdem IGs Kontingent für historische Kursdaten (10.000 Datenpunkte/Woche, feste 7-Tage-Fenster) als harte Obergrenze bestätigt ist — H1 braucht ~165 Fetches/Woche, das Kontingent erlaubt 33. Unabhängig bestätigt durch einen Kollegen des Nikinger mit eigenem IG-Setup. ENTSCHEIDUNG - der Paper-Tracker wird auf die BEREITS GEBAUTE ChainedBarProvider-Kette (IG→yFinance) umgestellt, nicht auf Lightstreamer und nicht auf einen Eigenbau. Begründung, Gegenargumente und Grenzen unten.
read-when: bevor an H1s Bar-Beschaffung, an Lightstreamer (Phase 9 Step 7b) oder an einer weiteren Datenquelle gearbeitet wird
detail: L3
up: ./CLAUDE.md
updated: 2026-08-11
---

# Datenquellen-Strategie — Entscheidung (2026-08-11)

> **BLUF:** IGs Kontingent ist **10.000 historische Datenpunkte pro Woche**. H1 braucht bei der
> aktuellen Konfiguration **~49.500**. Das ist kein Tuning-Problem, sondern ein
> Architektur-Problem: **IG darf nicht länger die Bar-Quelle sein.** Die Lösung liegt bereits im
> Repo — `ChainedBarProvider` (IG→yFinance, Phase 9 Step 6, gebaut und getestet). Der
> Paper-Tracker ist der **einzige** Bar-Konsument, der noch fest an `broker.get_ohlcv` hängt.
> **Lightstreamer löst dieses Problem nicht** (Begründung §4) — es bleibt wertvoll, aber für
> eine andere Frage.

## 1. Der bestätigte Befund

| | |
|---|---|
| Kontingent | **10.000 Datenpunkte / Woche**, kontoweit |
| Reset | `allowanceExpiry` = **7 Tage ab dem ersten Request nach einem Reset** (festes Fenster, **nicht** rollend) |
| Im erschöpften Zustand | nur 403, **kein** `allowance`-Objekt — der Reset-Zeitpunkt ist dann prinzipiell nicht abfragbar |
| Quelle | IG Labs + mehrere unabhängige Entwicklerberichte; deckt sich mit unserer eigenen Messung (≈19.800 Punkte am 08-03/08-04, Erschöpfung nach ~1 Tag) |

**Budget-Rechnung, das eigentliche Ergebnis:**

| Konfiguration | Punkte/Woche | gegen 10.000 |
|---|---|---|
| heute (`MINUTE` × 300, ~165 Fetches/Woche) | ~49.500 | **5× drüber** |
| `MINUTE_5` × 60 | ~9.900 | **99 % — null Reserve** |

Das ist der Grund, warum der billigere-Bars-Hebel allein nicht reicht: er landet exakt auf der
Decke und lässt nichts für die Phase-9-Promotion-Probe oder einen einzigen Retry übrig.

## 2. Unabhängige Bestätigung (Nikinger, 2026-08-11)

Ein Kollege des Nikinger ist mit einem **eigenen** IG-basierten Setup unabhängig auf dasselbe
Limit gelaufen. Zwei verwertbare Punkte daraus — beide sind Evidenz, keine Meinung:

- **Seine Lösung: mehrere Datenquellen, „geshuffelt", IG nur noch für echte Orders.** Das ist
  strukturell exakt das, was `ChainedBarProvider` hier bereits tut. Zwei Setups sind unabhängig
  bei derselben Antwort gelandet.
- **Limit-Erhöhung bei IG: gescheitert.** Deckt sich mit dem verbreiteten Bild, dass IG solche
  Anfragen von Privatkunden generisch beantwortet oder ignoriert. ⇒ **Eine Limit-Erhöhung ist
  keine planbare Abhängigkeit.** Sie kostet nichts und darf parallel versucht werden, aber kein
  Schritt darf darauf warten.
- Seine Wahl der Multi-Source-Route war ausdrücklich ein **Ausweichen**, weil er
  Lightstreamer nicht zum Laufen bekam. Unsere Lage ist hier besser (s. §4) — das ändert die
  Bewertung von Lightstreamer, aber nicht die Entscheidung unten.

## 3. Entscheidung

**Der Paper-Tracker bekommt seine Bars künftig über `ChainedBarProvider`, nicht über
`broker.get_ohlcv`.**

Das ist die Wiederverwendung von bereits gebautem, getestetem Code — kein neuer Baustein:

| Vorhanden | Ort | Status |
|---|---|---|
| `BarProvider` (Protocol) | `phase3_external_data/external_data/providers.py:28` | ✅ |
| `IGBarProvider` | dito `:44` | ✅ |
| `YFinanceBarProvider` | dito `:83` | ✅ |
| `ChainedBarProvider` (erste nicht-`None`-Antwort gewinnt, best-effort, `bar_fetch`-Event je Versuch) | dito `:101` | ✅ |
| Verdrahtung für den **Research**-Pfad | `wiring.py::_build_market_data:132`, Flag `enable_ig_bars` (Default AUS) | ✅ |
| Verdrahtung für den **Tracker**-Pfad | — | ❌ **die Lücke** |

Der Tracker ist damit der **einzige** verbliebene Bar-Konsument, der IG hart verdrahtet hat.
Der Eingriff ist entsprechend klein: `_build_paper_tracker`s `bar_fetch` ruft die Kette statt
des Brokers.

## 4. Warum NICHT Lightstreamer (das ist der Punkt, an dem man sich vertun kann)

Lightstreamer liefert einen **Live-Tick-Strom**. Der Tracker braucht **historische Bars** für
ein Fenster, das vor Stunden geschlossen hat — er fragt rückblickend „wo lag High/Low zwischen
`created_utc` und `time_stop_utc`?".

Ein Live-Stream beantwortet diese Frage nur, wenn wir ihn **selbst durchgehend mitschreiben und
persistieren**. Das ist nicht „Lightstreamer statt Eigenbau" — **das ist der Eigenbau**, nur mit
freundlicherem Namen: dauerhafte Subscription über die ganze Handelszeit, eigene Bar-Aggregation,
eigene Persistenz, eigene Lückenbehandlung bei Reconnects.

Und der harte Punkt: **IGs Kontingent ist kontoweit und quellenunabhängig.** Auch ein perfekt
laufender Lightstreamer füllt den historischen Topf nicht wieder auf.

**Unsere Lightstreamer-Lage ist trotzdem besser als die des Kollegen** — Phase 9 Step 7a lief
live (2026-07-06) mit einem **negativen** Befund: kein Multi-Epic-Bug, alle 4 Epics subscriben
sauber (`phase1_broker_wrapper/lightstreamer_integration_notes.md`). Step 7b wurde als
„unblocked-aber-leer" geparkt, **weil es nichts zu fixen gab**. Das bleibt so. Lightstreamer ist
weiterhin die richtige Antwort auf *Live-Quotes* (sein eigentlicher Phase-9-Zweck) — nur nicht
auf retrospektive Auflösung.

> ⚠ Die damalige Parkentscheidung fiel unter der Annahme, Bar-Volumen sei praktisch gratis.
> Diese Annahme ist jetzt widerlegt. Das ändert die Priorität von Step 7b **nicht** (s. o.),
> aber die Begründung im Phase-9-Dokument sollte beim nächsten Anfassen nachgezogen werden.

## 5. Grenzen dieser Entscheidung — ehrlich, nicht weggeredet

1. **yFinance-Bars sind nicht IGs Handelskurse.** Andere Quelle, anderer Spread, andere
   Zeitstempel. Für die *Geometrie*-Frage (WI-2: erreicht ein 30/45-Punkte-Setup je seinen
   Time-Stop?) ist das vertretbar; für Fill-Genauigkeit wäre es das nicht. **Es verändert, was
   WI-2 misst**, und muss beim Auswerten dabeistehen — nicht erst, wenn jemand stolpert.
2. **Die Gegenmaßnahme dafür ist ebenfalls schon gebaut und nicht verdrahtet:** der
   Divergenz-Check aus Phase 9 Step 6 (`quote_divergence`-Event ist in
   `scheduler/observability.py:103-104` bereits vorgesehen). Damit lässt sich die Abweichung
   **messen** statt annehmen. Das gehört unmittelbar hinter Schritt 1.
3. **Abdeckung ist unvollständig:** **15 von 22** Epics im `instrument_universe` haben einen
   `yf_ticker`, **7 nicht**. Für die 7 gibt es keinen Fallback — sie bleiben IG-abhängig oder
   müssen gemappt werden. Das ist vor einer Messwoche zu entscheiden, nicht danach.
4. **yFinance hat eigene Grenzen** (1-Minuten-Bars ~7 Tage, 5-Minuten ~60 Tage, plus eigenes
   Throttling). Für ein 240-Minuten-Fenster reicht das bequem; die Härtung dagegen
   (RateLimiter + Circuit-Breaker) ist in Phase 9 Step 6 bereits enthalten und wird
   mitbenutzt.
5. **Der Fetch-Budget-Breaker bleibt trotzdem sinnvoll.** Er schützt jetzt nicht mehr die
   Messung, sondern die *anderen* IG-Verbraucher (Promotion-Probe, Research) vor einem
   erneuten Leerlauf des Kontos.

## 6. Reihenfolge

1. **Tracker → `ChainedBarProvider`** (IG primär, yFinance Fallback). Klein, in bereits
   berührtem Code, Wochenende/Bot gestoppt.
2. **Divergenz-Check verdrahten**, damit Punkt 5.1 gemessen statt vermutet wird.
3. **`yf_ticker`-Lücke schließen** (7 Epics) **oder** bewusst akzeptieren und dokumentieren.
4. **Limit-Anfrage an IG** — parallel, kostenlos, **ohne** dass irgendetwas darauf wartet
   (§2).
5. **Lightstreamer (Step 7b)** bleibt geparkt und unabhängig. Falls es je angefasst wird, dann
   für Live-Quotes, nicht für die Tracker-Auflösung.

**Nicht Teil dieser Entscheidung:** ein eigener Tick-Recorder/Bar-Store. Das ist die
teuerste Option, und sie wird erst interessant, wenn Punkt 1–3 nachweislich nicht reichen —
also nach einer echten Messwoche, nicht vorher.

## 7. Offen

- Alle Punkte oben sind **ungebaut** — dies ist eine Entscheidung, kein Änderungsprotokoll.
- Das **Restart-Gate** aus [`ALLOWANCE_INCIDENT_2026-08-08.md`](./ALLOWANCE_INCIDENT_2026-08-08.md)
  §6 gilt unverändert: erst ein beobachtetes `remainingAllowance`, dann Universe-Reset, dann
  H1. Schritt 1 oben senkt den künftigen Verbrauch, füllt aber kein erschöpftes Kontingent auf.
- `_PAPER_ALLOWANCE_FLOOR` kann nach dem ersten erfolgreichen Call von `2000` (Platzhalter) auf
  ~15 % des dann beobachteten `totalAllowance` gesetzt werden.
