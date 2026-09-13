---
status: snapshot
purpose: Phase-14 B1a Probe-Output (Capital.com /markets Antwort-Form) — die **beobachtete** Form, gegen die `CapitalSource.discover()` (B1b) gebaut wird. Roh-Output des Operator-Runs vom 2026-08-22.
read-when: Block B1b wird gebaut; jede Frage zur Feldnamen-Wahl in `discover()`; jede Regression-Diagnose, die fragt „hat sich die API verändert?".
detail: L3
up: ../docs/concepts/phase14_discovery_plan.md
down:
  - ../phase13_live_data/scripts/probe_capital.py   # der Operator-Run, der diesen Output erzeugt hat (--markets-Modus aus Session 5)
updated: 2026-08-22
---
# Phase-14 B1a Probe-Output — `GET /api/v1/markets?searchTerm=...`

**Run-Datum:** 2026-08-22 (Operator-Run, Demo-Konto, kostenlos)
**Aufruf:** `python phase13_live_data/scripts/probe_capital.py --markets --terms "Germany 40,France 40,Spain 35"`
**Auth:** `POST /api/v1/session` → HTTP 200, `account_type=CFD`, CST + X-SECURITY-TOKEN erhalten

## Befunde (was die Probe gelehrt hat)

| # | Befund | Konsequenz für B1b |
|---|---|---|
| 1 | **Response-Form:** `{ "markets": [ ... ] }` — Array, je Eintrag ein Market-Objekt | `discover()` iteriert über `markets`, filtert, emittiert eine `SourceAvailability` pro Match |
| 2 | **`epic`-Feld ist das gesuchte Source-Symbol** (z.B. `"DE40"`, `"FR40"`, `"SP35"`) | geht 1:1 in `instrument_source_availability.source_symbol` (B2-Identity-These, exakt wie yF) |
| 3 | **`instrumentType` ist `"INDICES"`** (nicht `"CFD"`, wie der bestehende Prices-Probe-Filter annimmt) | B1b filtert auf `instrumentType == "INDICES"`. **Offener Bug im bestehenden Filter** (`live_data/backfill.py:339-366`): `"CFD"` matched nie, der Fallback greift heute. |
| 4 | **Spain 35 IST verfügbar** als `epic: "SP35"` (war bisher Path-C-Territorium in Phase 13) | Block B kann Coverage erweitern — Dukascopy-Fallback wird überflüssig für SP35 |
| 5 | Sucht mit `searchTerm=<instrumentName>` → erster Eintrag mit `instrumentName == searchTerm` + `instrumentType == "INDICES"` ist die kanonische IG-Epic-Übersetzung | B1b-Such-Algorithmus: `for epic in input: name = instrument_universe[epic].name; GET /markets?searchTerm=name; first INDICES match → SourceAvailability` |
| 6 | `delayTime: 0` für alle drei → Echtzeit | `history_min_days=30, latency_min=0` (analog zu IG) für die `capital`-Zeilen, NICHT die 15-Min-yF-Heuristik |
| 7 | Jeder Markteintrag hat `instrumentId` (numerisch), `epic` (kurz), `symbol` (lang/kurz), `bid`/`offer` (Live-Preise), `lotSize`, `tickSize`, `pipPosition` | B1b braucht nur `epic` + `instrumentName` + `instrumentType`. Die anderen Felder sind für Discover **irrelevant** — kein Mapping ins Schema |
| 8 | `marketStatus: "CLOSED"` für alle drei am Wochenende | erwartbar (Markt zu), kein B1b-Sonderfall — Discover prüft Verfügbarkeit via Existenz des Eintrags, nicht via `marketStatus` |

## Roh-Output (3 Terme, vollständig)

### Germany 40 → DE40 ✓

```json
{
  "ok": true,
  "http_status": 200,
  "url": "https://demo-api-capital.backend-capital.com/api/v1/markets?searchTerm=Germany+40",
  "content_type": "application/json",
  "raw_text_snippet": "{\"markets\":[{\"instrumentName\":\"Germany 40\",\"instrumentId\":508931114652423506,\"expiry\":\"-\",\"epic\":\"DE40\",\"symbol\":\"DE40\",\"instrumentType\":\"INDICES\",\"marketStatus\":\"CLOSED\",\"lotSize\":1,\"percentageChange\":-0.08,\"bid\":26108.3,\"offer\":26116.3,\"updateTime\":\"2026-08-21T22:59:57.256\",\"updateTimeUTC\":\"2026-08-21T20:59:57.256\",\"delayTime\":0,\"streamingPricesAvailable\":true,\"scalingFactor\":1,\"marketModes\":[\"REGULAR\"],\"pipPosition\":0,\"tickSize\":0.1},{\"instrumentName\":\"Gold\",\"instrumentId\":27045129890124996,\"...",
  "raw_body": {
    "markets": [
      {
        "instrumentName": "Germany 40",
        "instrumentId": 508931114652423506,
        "expiry": "-",
        "epic": "DE40",
        "symbol": "DE40",
        "instrumentType": "INDICES",
        "marketStatus": "CLOSED",
        "lotSize": 1,
        "percentageChange": -0.08,
        "bid": 26108.3,
        "offer": 26116.3,
        "updateTime": "2026-08-21T22:59:57.256",
        "updateTimeUTC": "2026-08-21T20:59:57.256",
        "delayTime": 0,
        "streamingPricesAvailable": true,
        "scalingFactor": 1,
        "marketModes": ["REGULAR"],
        "pipPosition": 0,
        "tickSize": 0.1
      },
      {
        "instrumentName": "Gold",
        "instrumentId": 27045129890124996,
        "epic": "GOLD",
        "symbol": "Gold",
        "instrumentType": "COMMODITIES",
        "marketStatus": "CLOSED"
      },
      {
        "instrumentName": "France 40",
        "instrumentId": 6810413677172050,
        "epic": "FR40",
        "symbol": "FR40",
        "instrumentType": "INDICES",
        "marketStatus": "CLOSED"
      },
      {
        "instrumentName": "Borussia Dortmund",
        "instrumentId": 41240275998034,
        "epic": "BVB",
        "symbol": "BVB",
        "instrumentType": "SHARES",
        "marketStatus": "CLOSED"
      },
      {
        "instrumentName": "US Wall Street 30",
        "instrumentId": 1679716659553719492,
        "epic": "US30",
        "symbol": "US30",
        "instrumentType": "INDICES",
        "marketStatus": "CLOSED"
      },
      {
        "instrumentName": "Live Cattle",
        "instrumentId": 7092970985706692,
        "epic": "LIVECATTLE",
        "symbol": "Live Cattle",
        "instrumentType": "COMMODITIES",
        "marketStatus": "CLOSED"
      }
    ]
  }
}
```

### France 40 → FR40 ✓

```json
{
  "ok": true,
  "http_status": 200,
  "url": "https://demo-api-capital.backend-capital.com/api/v1/markets?searchTerm=France+40",
  "content_type": "application/json",
  "raw_text_snippet": "{\"markets\":[{\"instrumentName\":\"France 40\",\"instrumentId\":6810413677172050,\"expiry\":\"-\",\"epic\":\"FR40\",\"symbol\":\"FR40\",\"instrumentType\":\"INDICES\",\"marketStatus\":\"CLOSED\",\"lotSize\":1,...},{\"instrumentName\":\"Air France\",\"instrumentId\":300647732562,\"expi",
  "raw_body": {
    "markets": [
      {
        "instrumentName": "France 40",
        "instrumentId": 6810413677172050,
        "epic": "FR40",
        "symbol": "FR40",
        "instrumentType": "INDICES",
        "marketStatus": "CLOSED"
      },
      {
        "instrumentName": "Air France",
        "instrumentId": 300647732562,
        "epic": "AFP",
        "symbol": "AFp",
        "instrumentType": "SHARES",
        "marketStatus": "CLOSED"
      },
      {
        "instrumentName": "Gold",
        "instrumentId": 27045129890124996,
        "epic": "GOLD",
        "symbol": "Gold",
        "instrumentType": "COMMODITIES",
        "marketStatus": "CLOSED"
      },
      {
        "instrumentName": "Germany 40",
        "instrumentId": 508931114652423506,
        "epic": "DE40",
        "symbol": "DE40",
        "instrumentType": "INDICES",
        "marketStatus": "CLOSED"
      },
      {
        "instrumentName": "BIOHAVEN ORD",
        "instrumentId": 2398644745622724,
        "epic": "BHVN",
        "symbol": "BHVN",
        "instrumentType": "SHARES",
        "marketStatus": "CLOSED"
      }
    ]
  }
}
```

### Spain 35 → SP35 ✓ (neu entdeckt — Dukascopy-Fallback überflüssig)

```json
{
  "ok": true,
  "http_status": 200,
  "url": "https://demo-api-capital.backend-capital.com/api/v1/markets?searchTerm=Spain+35",
  "content_type": "application/json",
  "raw_text_snippet": "{\"markets\":[{\"instrumentName\":\"Spain 35\",\"instrumentId\":1387370618105648466,\"expiry\":\"-\",\"epic\":\"SP35\",\"symbol\":\"SP35\",\"instrumentType\":\"INDICES\",\"marketStatus\":\"CLOSED\",\"lotSize\":1,...},{\"instrumentName\":\"Ethereum/USD\",\"instrumentId\":5983666832495",
  "raw_body": {
    "markets": [
      {
        "instrumentName": "Spain 35",
        "instrumentId": 1387370618105648466,
        "epic": "SP35",
        "symbol": "SP35",
        "instrumentType": "INDICES",
        "marketStatus": "CLOSED",
        "lotSize": 1,
        "percentageChange": 0.02,
        "bid": 19952.5,
        "offer": 19968.5,
        "updateTime": "2026-08-21T19:58:05.421",
        "updateTimeUTC": "2026-08-21T17:58:05.421",
        "delayTime": 0
      },
      {
        "instrumentName": "Ethereum/USD",
        "instrumentId": 5983666832495812,
        "epic": "ETHUSD",
        "symbol": "ETH/USD",
        "instrumentType": "CRYPTOCURRENCIES",
        "marketStatus": "TRADEABLE"
      },
      {
        "instrumentName": "Gold",
        "instrumentId": 27045129890124996,
        "epic": "GOLD",
        "symbol": "Gold",
        "instrumentType": "COMMODITIES",
        "marketStatus": "CLOSED"
      },
      {
        "instrumentName": "Mapfre",
        "instrumentId": 229042015982930,
        "epic": "MAP",
        "symbol": "MAP",
        "instrumentType": "SHARES",
        "marketStatus": "CLOSED"
      },
      {
        "instrumentName": "Tecnicas Reunidas",
        "instrumentId": 356812998071634,
        "epic": "TRE",
        "symbol": "TRE",
        "instrumentType": "SHARES",
        "marketStatus": "CLOSED"
      },
      {
        "instrumentName": "Bitcoin/USD",
        "instrumentId": 2604592722433220,
        "epic": "BTCUSD",
        "symbol": "BTC/USD",
        "instrumentType": "CRYPTOCURRENCIES",
        "marketStatus": "TRADEABLE"
      },
      {
        "instrumentName": "Telefonica",
        "instrumentId": 353243880248658,
        "epic": "TEF",
        "symbol": "TEF",
        "instrumentType": "SHARES",
        "marketStatus": "CLOSED"
      },
      {
        "instrumentName": "Marston's Plc",
        "instrumentId": 14659320381730960,
        "epic": "MARS",
        "symbol": "MARS",
        "instrumentType": "SHARES",
        "instrumentStatus": "CLOSED",
        "tickSize": 1e-06
      }
    ]
  }
}
```

## Was B1b daraus bauen muss

```python
class CapitalSource:  # lebt in phase13_live_data/live_data/backfill.py
    def discover(self, epics, *, max_probe_calls=8) -> SourceProfile:
        """Phase-14 B1b. Discover-Form ist build 1:1 gegen die oben dokumentierte
        /markets-Antwort. Sucht mit `instrument_universe.name` als searchTerm,
        filtert auf `instrumentType == "INDICES"` + exact `instrumentName`-Match,
        emittiert eine `SourceAvailability` mit `source_symbol = markets[0].epic`."""
        rows = []
        errors = []
        for epic in epics:
            try:
                # ... auth + GET /markets?searchTerm=<name> ...
                # ... filter: instrumentName == name AND instrumentType == "INDICES" ...
                if not matches:
                    rows.append(SourceAvailability(
                        epic=epic, source="capital", resolution="1m",
                        source_symbol=None,
                        status="no_source",
                        origin="discovery",
                        history_min_days=None, latency_min=None,
                        last_verified_utc=utc_iso_now(),
                        notes=f"no INDICES match for searchTerm={name!r}",
                    ))
                    continue
                m = matches[0]
                rows.append(SourceAvailability(
                    epic=epic, source="capital", resolution="1m",
                    source_symbol=m["epic"],   # "DE40" / "FR40" / "SP35"
                    status="ok",
                    origin="discovery",
                    history_min_days=30, latency_min=0,
                    last_verified_utc=utc_iso_now(),
                ))
            except Exception as exc:
                errors.append(f"{epic}: {exc}")
        return SourceProfile(source="capital", rows=tuple(rows), probe_calls_used=..., errors=tuple(errors))
```

**Nicht-B1b-Stoff (separate Tasks, nicht in dieser Datei):**

- **B2:** `EPIC_MAP` raus, `SourceAvailabilityStore.symbol_for(epic, 'capital')` rein. Diese Datei ist die Vorlage.
- **Offener Bug im bestehenden Filter:** `live_data/backfill.py:339-366` (`_extract_ohlc`) sucht `"CFD"` in `instrumentType` — was nie matched (Realität ist `"INDICES"`). Der Fallback `candidates = [m for m in markets if m.get("instrumentName") == index_name]` rettet es heute. B1b macht den Filter richtig — der bestehende sollte nachgezogen werden (Phase 14 B2 oder separates Hygiene-Ticket, Nikinger-Entscheidung).
