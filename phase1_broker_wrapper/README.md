# broker_wrapper — Phase 1

Unified broker abstraction for the trading bot. Pure REST + Lightstreamer streaming,
runs standalone, emits standard JSON envelopes consumable by tests, CLI, FastAPI,
and the bot core.

## What it is, what it isn't

**Is:**
- A single Python interface (`BrokerAdapter`) every broker implements.
- An IG Markets REST adapter (raw `requests`, no third-party trading-ig).
- A polling stream client as functional fallback.
- A Lightstreamer client (official `lightstreamer-client-lib` SDK, live-tested against IG demo).
- A deterministic tradeable-filter rules engine (Code, not AI).
- A CLI for standalone smoke-testing and shell piping.
- OS-keyring credential management.
- ✓ REST smoke-tested against IG demo — full lifecycle including order open/close verified.

**Isn't (yet):**
- Backtesting infrastructure. (Phase 3.)
- The bot itself. This module is a tool, not a strategy.

Lightstreamer streaming is live-tested: CONOK/SUBOK + real DAX ticks confirmed against
IG demo on 2026-05-21 via `scripts/test_lightstreamer.py`.

## Install

```bash
pip install -r requirements.txt
```

## First-time setup — credentials

Production credentials live ONLY in the OS keyring. No plaintext files,
no env vars, no config commits. Future AI sessions on this codebase
cannot read them.

```bash
# List known credential keys
python scripts/store_credential.py --list

# Store each one (input is hidden, prompted via getpass)
# Note: IG username is the login identifier shown in MyIG → Personal details,
# which may differ from your email address.
python scripts/store_credential.py ig_demo_username
python scripts/store_credential.py ig_demo_password
python scripts/store_credential.py ig_demo_api_key
python scripts/store_credential.py ig_demo_account_id

# Verify (shows ✓/✗ only, never values)
python scripts/store_credential.py --status
```

For production keys, repeat with `ig_username`, `ig_password`,
`ig_api_key`, `ig_account_id`.

## REST smoke test

```bash
python scripts/smoke_test.py                          # read-only, auto-selects first TRADEABLE INDICES epic
python scripts/smoke_test.py --order --size 1         # full lifecycle: open + close demo position
python scripts/smoke_test.py --epic IX.D.DAX.IFMM.IP  # explicit confirmed epic
```

The smoke test exercises connect → account → search → market info →
price → OHLCV → positions → reconcile → disconnect. With `--order`, it
also opens and closes a demo position.

**Session throttling:** IG blocks rapid successive logins from the same account.
If you get `service.security.authentication.failure-invalid-client-security-token`
after a successful run, wait 2–3 minutes before retrying. Not an issue in
production where the bot holds one persistent session.

## Lightstreamer live test

`scripts/test_lightstreamer.py` validates the streaming connection end-to-end —
something neither `pytest` (mocked HTTP) nor `smoke_test.py` (REST only) can do.

```bash
python scripts/test_lightstreamer.py                          # wait for 3 ticks, 30s timeout
python scripts/test_lightstreamer.py --ticks 5 --timeout 60  # stricter check
python scripts/test_lightstreamer.py --epic IX.D.DAX.IFMM.IP # explicit epic
```

What it validates:
- `lightstreamerEndpoint` is returned by `POST /session` (the Gap 1 fix in `_login()`)
- IG accepts `CST-...|XST-...` auth format over TLCP
- TLCP session creates and `CONOK` is received
- Subscription to `L1:{epic}` returns `SUBOK`
- `PriceTick` callbacks are delivered via `U,...` stream lines
- `stop()` cleans up the reader thread

**Must run during market hours** (Mon–Fri 08:00–22:30 CET). Outside hours the
DAX index is CLOSED and may deliver zero ticks even on a healthy connection.
Exit code 0 = PASS, 1 = FAIL (see output for debug hints on failure).

## CLI usage (standalone, JSON output)

Every command prints one Envelope JSON object to stdout.

```bash
python -m broker_wrapper.cli --broker ig_demo get-account
python -m broker_wrapper.cli --broker ig_demo get-price --epic IX.D.DAX.IFMM.IP
python -m broker_wrapper.cli --broker ig_demo search --query DAX
python -m broker_wrapper.cli --broker ig_demo ohlcv \
    --epic IX.D.DAX.IFMM.IP --resolution MINUTE_5 --count 20
python -m broker_wrapper.cli --broker ig_demo historical \
    --epic IX.D.DAX.IFMM.IP --from 2026-05-01T00:00:00 --to 2026-05-10T00:00:00 \
    --resolution HOUR
python -m broker_wrapper.cli --broker ig_demo reconcile --refs bot-abc bot-def
```

## Programmatic usage

```python
from broker_wrapper import get_broker
from broker_wrapper.factory import get_stream

# REST
broker = get_broker("ig_demo")
broker.connect()
price = broker.get_price("IX.D.DAX.IFMM.IP")
if price.ok:
    print(price.data["bid"], price.data["ask"])

# Streaming
stream = get_stream(broker)
stream.subscribe("IX.D.DAX.IFMM.IP", lambda tick: print(tick.bid, tick.ask))
stream.start()
# ... bot runs ...
stream.stop()
broker.disconnect()
```

## Envelope shape

Every method returns this:

```json
{
  "ok": true,
  "ts": "2026-05-14T13:42:11.123Z",
  "broker": "ig",
  "method": "get_price",
  "data": { ... },
  "error": null,
  "latency_ms": 127
}
```

Errors:

```json
{
  "ok": false,
  "ts": "...",
  "broker": "ig",
  "method": "open_position",
  "data": { "deal_reference": "bot-abc..." },
  "error": {
    "code": "INSUFFICIENT_FUNDS",
    "message": "...",
    "retryable": false
  },
  "latency_ms": 84
}
```

## Idempotency

`open_position()` accepts a client-supplied `deal_reference`. If the
network drops mid-call, the bot can later call `reconcile_positions()`
with the reference list — the wrapper compares against broker truth and
returns which references are `present` / `missing` / `unexpected`.

## Running tests

```bash
pytest tests/ -v   # 48 tests: envelope(7) · filters(10) · ig_adapter(14) · lightstreamer(17)
```

All unit tests use mocked HTTP — no network, no credentials needed.

## What goes where in this module

```
broker_wrapper/
├── envelope.py            ← standard response container
├── exceptions.py          ← typed error hierarchy
├── credentials.py         ← OS keyring access
├── models.py              ← normalized cross-broker dataclasses
├── filters.py             ← deterministic "tradeable?" rules + sizing math
├── factory.py             ← get_broker("ig"|"ig_demo") · get_stream(adapter)
├── cli.py                 ← standalone CLI / JSON pipe
├── adapters/
│   ├── base.py            ← BrokerAdapter ABC
│   └── ig_adapter.py      ← IG REST implementation + lightstreamer_endpoint property
└── streaming/
    ├── base.py            ← StreamClient ABC + PollingStreamClient
    └── ig_lightstreamer.py  ← official Lightstreamer SDK wrapper · live-tested

scripts/
├── store_credential.py    ← credential storage (getpass, OS keyring)
├── smoke_test.py          ← REST end-to-end test (48 steps, order lifecycle)
└── test_lightstreamer.py  ← Lightstreamer live stream validation (run during market hours)
```

## Open items / known limits

1. **Lightstreamer live-tested ✅.** Built on the official `lightstreamer-client-lib`
   SDK; CONOK/SUBOK + real DAX `PRICE` ticks confirmed against IG demo on 2026-05-21
   via `python scripts/test_lightstreamer.py`. See `lightstreamer_integration_notes.md`.
2. **DAX CFD epic confirmed:** `IX.D.DAX.IFMM.IP` — "Deutschland 40-Kassa (1 €)",
   `min_deal_size: 0.5`, `lot_size: 1.0 €/point`, EUR, spread ~1.8 pts (~0.007%).
   Use `search_markets()` to discover epics rather than hardcoding in case IG
   changes their naming.
3. **Trade-history parsing** is best-effort. IG's transaction format varies by
   deal type; cross-check against a known closed deal before relying on it.
4. **IG Europe GmbH live account** required before real-money trading. Current
   HTADU/GBX is a UK entity account — not correct for German residents post-Brexit.
   Open a fresh EUR account at ig.com/de.
