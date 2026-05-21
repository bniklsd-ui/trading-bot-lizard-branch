# Phase 1 — Broker API Wrapper: Konzept

> **Status:** COMPLETE · Live-verified gegen IG Demo · 31 Unit-Tests pass · smoke_test.py PASS (inkl. --order)
> **Bauprinzip:** So wenig AI wie möglich, so viel AI wie nötig.
> Code macht alles was Code kann. AI trifft nur Entscheidungen die genuines Urteilsvermögen erfordern.

---

## Entscheidungslog (finalisiert)

| Thema | Entscheidung | Begründung |
|---|---|---|
| Produkt | **DAX CFD auf IG** | Kein Commission auf Index-CFDs, Spread ~1-2 Punkte intraday, kein Issuer-Risiko wie bei Turbos, kein Expiry wie bei Futures |
| Broker | **IG Markets Deutschland EUR** | Einzel-Broker, einheitliche REST API, EUR-Konto, kein GBX/FX-Noise |
| API-Bibliothek | **Raw `requests`** | Keine Abhängigkeit von `trading-ig`, volle Kontrolle über Error-Paths |
| Streaming | **PollingStreamClient** (Fallback) + **IGLightstreamerClient** (✅ live-getestet, offizielles SDK) | Modular — 1-Zeilen-Wechsel via Factory; SDK negotiiert WebSocket/TLCP |
| Order-Typen | **MARKET · LIMIT · STOP** + `modify_position` | Market-only = Footgun bei Spread-Widening |
| Credentials | **OS Keyring** (`keyring`-lib) | Kein Plaintext auf Disk, AI kann keine Keys aus Dateien lesen |
| Idempotenz | **`deal_reference` (UUID)** pro Order | Netzwerkabbruch → Reconcile via `reconcile_positions()` |
| Tradeable-Filter | **Code (filters.py)**, nicht AI | Spread%, MarketStatus, Currency, MinSize = deterministische Regeln |
| Response-Format | **Envelope JSON** (einheitlich) | `{ok, ts, broker, method, data, error, latency_ms}` — CLI, FastAPI, Bot = identische Parser |
| Historische Daten | **`get_historical_ohlcv(epic, from, to, res)`** in Scope | Backtesting braucht das, von Anfang an eingebaut |

---

## Bestätigtes Instrument (live verifiziert)

| Feld | Wert |
|---|---|
| Epic | `IX.D.DAX.IFMM.IP` |
| Name | Deutschland 40-Kassa (1 €) |
| Typ | INDICES |
| Währung | EUR |
| min_deal_size | 0.5 |
| lot_size | 1.0 €/Punkt |
| Spread (typisch) | ~1.8 Punkte (~0.007%) |
| Fill-Typ | Market — sofortige Ausführung, level zurückgegeben |
| Account | Z6BEGX (Demo, EUR, 30.000 €) |

Weitere verfügbare DAX-Epics (alle TRADEABLE, alle INDICES):
- `IX.D.DAX.IFMG.IP` — Deutschland 40-Kassa (5 €/Punkt)
- `IX.D.DAX.IFD.IP` — Deutschland 40-Kassa (25 €/Punkt)

Epic-Discovery immer via `search_markets("DAX")` — nie hardcoden.

---

## Package-Struktur

```
broker_wrapper/                  ← Python-Package (pip install -e .)
├── __init__.py                  ← Public surface: get_broker, Envelope, Exceptions
├── envelope.py                  ← Envelope dataclass · ok_envelope() · error_envelope() · LatencyTimer
├── exceptions.py                ← BrokerError-Hierarchie (AuthError, MarketOffline, RateLimit, ...)
├── credentials.py               ← OS Keyring access · get_credential(name) · store_credential()
├── models.py                    ← Price · OHLCBar · MarketInfo · Account · Position · OrderResult · Transaction
├── filters.py                   ← is_tradeable() · FilterConfig · calc_spread_pct() · calc_position_size()
├── factory.py                   ← get_broker("ig" | "ig_demo") → BrokerAdapter
├── cli.py                       ← Standalone CLI: python -m broker_wrapper.cli get-price --epic X
├── adapters/
│   ├── base.py                  ← BrokerAdapter (ABC) — 14 abstract methods
│   └── ig_adapter.py            ← IGAdapter — vollständige IG REST Implementierung (~620 Zeilen)
└── streaming/
    ├── base.py                  ← StreamClient (ABC) · PriceTick · PollingStreamClient ✓
    └── ig_lightstreamer.py      ← IGLightstreamerClient ✅ (offizielles Lightstreamer-SDK, PRICE-Feed, live-getestet)

scripts/
├── store_credential.py          ← getpass-Prompt → OS Keyring (AI sieht Input nie)
└── smoke_test.py                ← End-to-End Test gegen Demo-Account (live verifiziert)

tests/
├── test_envelope.py             ← 7 Tests: ok/error envelopes, JSON round-trip, timer
├── test_filters.py              ← 10 Tests: spread, status, currency, sizing
└── test_ig_adapter.py           ← 14 Tests: HTTP mocks, login, price, order validation
```

---

## BrokerAdapter Interface (vollständig)

```python
class BrokerAdapter(ABC):
    name: str

    # Session
    def connect(self) -> Envelope: ...
    def disconnect(self) -> Envelope: ...
    def is_connected(self) -> bool: ...

    # Marktdaten
    def get_price(self, epic: str) -> Envelope: ...
    # data: {epic, bid, ask, spread, spread_pct, market_status, timestamp}

    def get_ohlcv(self, epic: str, resolution: str, count: int) -> Envelope: ...
    # data: {bars: [{timestamp, open, high, low, close, volume}], allowance: {...}}

    def get_historical_ohlcv(self, epic: str, from_dt: str, to_dt: str, resolution: str) -> Envelope: ...
    # from_dt/to_dt: ISO 8601 UTC · resolution: MINUTE_5, HOUR, DAY, ... (15 Optionen)

    def get_market_info(self, epic: str) -> Envelope: ...
    # data: {epic, name, instrument_type, currency, expiry, min_deal_size, lot_size, market_status}

    def search_markets(self, query: str) -> Envelope: ...
    # data: {query, results: [{epic, name, type, expiry, market_status, bid, ask}]}

    # Account
    def get_account(self) -> Envelope: ...
    # data: {account_id, balance, available, profit_loss, currency}

    def get_open_positions(self) -> Envelope: ...
    # data: {positions: [{deal_id, deal_reference, epic, direction, size, open_level, currency, ...}]}

    def get_trade_history(self, days: int = 30) -> Envelope: ...
    # data: {transactions: [{transaction_id, epic, direction, size, open_level, close_level, profit_loss, ...}]}

    # Orders
    def open_position(
        self,
        epic: str,
        direction: Literal["BUY", "SELL"],
        size: float,
        order_type: Literal["MARKET", "LIMIT", "STOP"] = "MARKET",
        *,
        level: float | None = None,          # required for LIMIT/STOP
        stop_level: float | None = None,
        limit_level: float | None = None,
        deal_reference: str | None = None,   # idempotency key — auto-generated if None
        currency: str | None = None,
    ) -> Envelope: ...
    # data: {deal_reference, deal_id, status, epic, direction, size, level, reason, timestamp}
    # status: "ACCEPTED" | "REJECTED" | "PENDING"
    # error data always contains deal_reference for reconciliation

    def close_position(self, deal_id: str) -> Envelope: ...
    def modify_position(self, deal_id: str, *, stop_level=None, limit_level=None) -> Envelope: ...

    def reconcile_positions(self, expected_references: list[str] | None = None) -> Envelope: ...
    # data: {broker_position_count, broker_deal_ids, present, missing, unexpected}
```

---

## Envelope-Format (jede Methode)

```json
{
  "ok": true,
  "ts": "2026-05-19T08:34:27.844Z",
  "broker": "ig",
  "method": "open_position",
  "data": {
    "deal_reference": "bot-975eff035ea3499b80956f4d",
    "deal_id": "DIAAAAXH7MVC2AB",
    "status": "ACCEPTED",
    "epic": "IX.D.DAX.IFMM.IP",
    "direction": "BUY",
    "size": 1.0,
    "level": 24615.9,
    "reason": "SUCCESS",
    "timestamp": "2026-05-19T08:34:27.844Z"
  },
  "error": null,
  "latency_ms": 310
}
```

Fehler-Envelope (Order rejected, aber API-Call ok — status im data):
```json
{
  "ok": true,
  "method": "open_position",
  "data": { "status": "REJECTED", "reason": "MARKET_OFFLINE", "deal_reference": "bot-..." },
  "error": null
}
```

Fehler-Envelope (technischer Fehler):
```json
{
  "ok": false,
  "method": "open_position",
  "data": { "deal_reference": "bot-abc123..." },
  "error": { "code": "MARKET_OFFLINE", "message": "405 ...", "retryable": true },
  "latency_ms": 84
}
```

**Wichtig:** `ok=true` bedeutet der API-Call war erfolgreich — nicht zwingend dass die Order ausgeführt wurde. Immer `data["status"]` prüfen nach `open_position`.

**CLI exit codes:** 0 = ok, 1 = error. Output immer ein JSON-Objekt auf stdout.

---

## Credentials (Schlüsselnamen)

```python
# In credentials.py als Konstanten:
IG_USERNAME       = "ig_username"
IG_PASSWORD       = "ig_password"
IG_API_KEY        = "ig_api_key"
IG_ACCOUNT_ID     = "ig_account_id"

IG_DEMO_USERNAME  = "ig_demo_username"
IG_DEMO_PASSWORD  = "ig_demo_password"
IG_DEMO_API_KEY   = "ig_demo_api_key"
IG_DEMO_ACCOUNT_ID = "ig_demo_account_id"
```

**Zugriff im Code immer über:**
```python
from broker_wrapper.credentials import get_credential, IG_API_KEY
key = get_credential(IG_API_KEY)  # liest aus OS Keyring, wirft CredentialNotFoundError wenn fehlt
```

**Credential-Hinweise aus der Praxis:**
- `ig_demo_username` ist der IG Login-Identifier aus MyIG → Personal details — kann vom Email abweichen
- Demo- und Live-API-Keys sind vollständig getrennt — immer den richtigen verwenden
- Ubuntu: venv aktivieren vor Credential-Zugriff (`source .venv/bin/activate`)

**Niemals:** config.json, .env-Files, Klartext auf Disk (Produktion).

---

## Filters (Code, nicht AI)

```python
from broker_wrapper.filters import is_tradeable, FilterConfig, calc_position_size

cfg = FilterConfig(
    max_spread_pct=0.5,          # reject wenn Spread > 0.5%
    min_market_status=("TRADEABLE",),
    require_currency="EUR",
    max_min_deal_size=None,
)

verdict = is_tradeable(price, market_info, cfg)
# verdict.ok: bool
# verdict.rule: "SPREAD_TOO_WIDE" | "MARKET_STATUS" | "WRONG_CURRENCY" | "MIN_SIZE_TOO_LARGE" | None
# verdict.reason: str | None

size = calc_position_size(
    available_balance=10000,
    risk_pct=0.08,   # 8% des verfügbaren Kapitals
    price=24616.0,   # aktueller ask-Preis
    point_value=1.0, # 1 €/Punkt für IX.D.DAX.IFMM.IP
    cap=2.0,         # max Größe
)
# → size wird auf 0.1-Schritt abgerundet (IG CFD-Minimum-Step)
```

---

## Streaming

```python
from broker_wrapper.streaming import PollingStreamClient, PriceTick
from broker_wrapper import get_broker

broker = get_broker("ig_demo")
broker.connect()

stream = PollingStreamClient(broker, interval_s=1.0)
stream.start()
stream.subscribe("IX.D.DAX.IFMM.IP", lambda tick: print(tick.bid, tick.ask))
# ... bot runs ...
stream.stop()
broker.disconnect()
```

**IGLightstreamerClient** (production, ✅ live-getestet 2026-05-21):
- Interface identisch — `stream.subscribe("IX.D.DAX.IFMM.IP", callback)` unverändert
- Wechsel: Factory-Änderung, kein Consumer-Code berührt
- Datei: `streaming/ig_lightstreamer.py` — Wrapper um das offizielle
  `lightstreamer-client-lib` SDK; `PRICE:{account_id}:{epic}` über den `Pricing`-Adapter.
  (Der frühere raw-TLCP-over-HTTP-Ansatz scheiterte an HTTP 400 — siehe
  `lightstreamer_integration_notes.md` v10.)

---

## IG-spezifische Hinweise

### Endpoints (alle live verifiziert)
| Operation | Methode | Endpoint | Version |
|---|---|---|---|
| Login | POST | /session | v2 |
| Account | GET | /accounts | v1 |
| Positionen | GET | /positions | v2 |
| Market-Info | GET | /markets/{epic} | v3 |
| Preise (historisch) | GET | /prices/{epic} | v3 |
| Suche | GET | /markets?searchTerm= | v1 |
| Order öffnen | POST | /positions/otc | v2 |
| Confirm | GET | /confirms/{dealRef} | v1 |
| Order schließen | POST + `_method: DELETE` | /positions/otc | v1 |
| Position modifizieren | PUT | /positions/otc/{dealId} | v2 |

### Auth-Flow
```
POST /session → CST + X-SECURITY-TOKEN in Response-Headers (nicht im Body!)
Session-Timeout: 6h → Adapter refresht bei 401 automatisch einmal
Username = IG Login-Identifier (MyIG → Personal details), nicht zwingend Email
```

### Session-Throttling
IG begrenzt schnelle Logins vom selben Account. Bei:
`service.security.authentication.failure-invalid-client-security-token`
→ 2–3 Minuten warten. Im Produktivbetrieb irrelevant (eine persistente Session).

### Fehler-Mapping
```
HTTP 401 → re-login + retry once
HTTP 403 → AuthenticationError (nicht retryable)
HTTP 404 → EpicNotFoundError
HTTP 405 → MarketOfflineError (retryable)
HTTP 429 → RateLimitError (retryable, backoff)
HTTP 5xx → BrokerError (retry bis max_retries)
400 validation.pattern.invalid → Credentials-Format falsch (nicht Email-Error)
```

### Search-Filter für DAX Index-CFDs
```python
# Immer nach type=="INDICES" und market_status=="TRADEABLE" filtern
# um ETFs, Shares etc. auszuschließen
for r in search_results:
    if r["type"] == "INDICES" and r["market_status"] == "TRADEABLE":
        epic = r["epic"]
        break
```

---

## smoke_test.py — angewandte Fixes

Beide Fixes sind in `scripts/smoke_test.py` eingebaut:

1. **Epic-Auswahl:** Filtert nach `type=="INDICES"` + `market_status=="TRADEABLE"` statt nach Name mit "DAX". Verhindert, dass ETFs oder geschlossene SHARES-Instrumente ausgewählt werden.

2. **Close-Logic:** Prüft `data["status"] == "ACCEPTED"` vor `close_position`. Verhindert versuchtes Schließen einer rejected Order.

---

## Error-Code-Referenz

```python
"BROKER_ERROR"          # BrokerError (base)
"AUTH_ERROR"            # AuthenticationError
"CREDENTIAL_NOT_FOUND"  # CredentialNotFoundError
"MARKET_OFFLINE"        # MarketOfflineError (retryable)
"RATE_LIMIT"            # RateLimitError (retryable)
"INSUFFICIENT_FUNDS"    # InsufficientFundsError
"ORDER_REJECTED"        # OrderRejectedError
"EPIC_NOT_FOUND"        # EpicNotFoundError
"NETWORK_ERROR"         # NetworkError (retryable)
"PROTOCOL_ERROR"        # ProtocolError
```

---

## Nutzung

### Installation
```bash
cd phase1_broker_wrapper
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Credentials speichern (einmalig)
```bash
python scripts/store_credential.py ig_demo_username   # × 4 für alle Demo-Keys
python scripts/store_credential.py --status            # ✓/✗ pro Key
```

### Tests
```bash
pytest tests/ -v                                              # 31 Tests, kein Netzwerk
python scripts/smoke_test.py                                  # read-only vs Demo-API
python scripts/smoke_test.py --order --size 1                 # vollständiger Lifecycle
python scripts/smoke_test.py --epic IX.D.DAX.IFMM.IP          # mit bestätigtem Epic
```

### CLI (standalone JSON-Output)
```bash
python -m broker_wrapper.cli --broker ig_demo get-account
python -m broker_wrapper.cli --broker ig_demo get-price --epic IX.D.DAX.IFMM.IP
python -m broker_wrapper.cli --broker ig_demo ohlcv --epic IX.D.DAX.IFMM.IP --resolution MINUTE_5 --count 20
python -m broker_wrapper.cli --broker ig_demo historical --epic IX.D.DAX.IFMM.IP --from 2026-05-01T00:00:00 --to 2026-05-10T00:00:00 --resolution HOUR
python -m broker_wrapper.cli --broker ig_demo reconcile --refs bot-abc bot-def
```

### Programmatisch
```python
from broker_wrapper import get_broker

broker = get_broker("ig_demo")
broker.connect()

env = broker.get_price("IX.D.DAX.IFMM.IP")
if env.ok:
    print(env.data["bid"], env.data["spread_pct"])
else:
    print(env.error["code"], env.error["retryable"])

broker.disconnect()
```

---

## Offene Punkte (für spätere Phasen)

| Item | Phase | Priorität |
|---|---|---|
| IGLightstreamerClient gegen IG Europe **Live**-Account testen (Demo ✅) | vor Go-Live | Hoch |
| Rate-Limit Budget-Tracking (allowance aus /prices) | P2 | Hoch |
| Reconciliation braucht SQLite (expected_refs persistieren) | P2 | Hoch |
| IBKRAdapter für DAX Futures (Skalierung) | P4+ | Niedrig |
| IG Europe GmbH Live-Account (deutsches Konto, ig.com/de) | vor P-Live | Kritisch |
| Backtesting-Cache für historische OHLCV | P3 | Mittel |

---

## Was AI macht vs. was Code macht

```
CODE (dieser Wrapper):
├── Alle API-Calls (GET, POST, DELETE, PUT)
├── Auth + Token-Handling + Re-Login
├── Spread-Berechnung: (ask - bid) / ask * 100
├── Position-Sizing: balance × risk_pct / price
├── VETO-Checks: spread%, market_status, currency (filters.py)
├── Envelope-Wrapping jeder Response
├── Idempotenz via deal_reference
├── Error-Mapping HTTP → Exception-Typen
├── Retry-Logik mit Backoff
├── Historische Daten abrufen und zurückgeben
└── Persistenz (Phase 2: SQLite)

AI (andere Phasen):
├── Richtungsentscheidung (Bull/Bear/Judge-Debatte)
├── Kandidatenauswahl-Begründung (turbo_research)
├── Lesson-Extraktion nach Trade (Brain)
├── Council-Evaluation (Strategieprüfung)
└── NICHTS ANDERES
```

---

*Phase 1 abgeschlossen. Nächster Schritt: Phase 2 — SQLite Schema + JSON State.*
