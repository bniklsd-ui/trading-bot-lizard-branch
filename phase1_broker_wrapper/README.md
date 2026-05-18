# broker_wrapper — Phase 1

Unified broker abstraction for the trading bot. Pure REST, runs standalone,
emits standard JSON envelopes consumable by tests, CLI, FastAPI, and the
bot core.

## What it is, what it isn't

**Is:**
- A single Python interface (`BrokerAdapter`) every broker implements.
- An IG Markets REST adapter (raw `requests`, no third-party trading-ig).
- A polling stream client as functional fallback.
- A skeleton Lightstreamer client (next iteration finishes it).
- A deterministic tradeable-filter rules engine (Code, not AI).
- A CLI for standalone smoke-testing and shell piping.
- OS-keyring credential management.

**Isn't (yet):**
- Live-tested against a real IG account. Smoke-test first against demo.
- Backtesting infrastructure. (Phase 3.)
- The bot itself. This module is a tool, not a strategy.

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
python scripts/store_credential.py ig_demo_username
python scripts/store_credential.py ig_demo_password
python scripts/store_credential.py ig_demo_api_key
python scripts/store_credential.py ig_demo_account_id

# Verify (shows ✓/✗ only, never values)
python scripts/store_credential.py --status
```

For production keys, repeat with `ig_username`, `ig_password`,
`ig_api_key`, `ig_account_id`.

## Smoke test

```bash
python scripts/smoke_test.py                 # read-only checks against demo
python scripts/smoke_test.py --order         # also place + close a tiny order
python scripts/smoke_test.py --epic IX.D.DAX.IFM.IP
```

The smoke test exercises connect → account → search → market info →
price → OHLCV → positions → reconcile → disconnect. With `--order`, it
also opens and closes a demo position.

## CLI usage (standalone, JSON output)

Every command prints one Envelope JSON object to stdout.

```bash
python -m broker_wrapper.cli --broker ig_demo get-account
python -m broker_wrapper.cli --broker ig_demo get-price --epic IX.D.DAX.IFM.IP
python -m broker_wrapper.cli --broker ig_demo search --query DAX
python -m broker_wrapper.cli --broker ig_demo ohlcv \
    --epic IX.D.DAX.IFM.IP --resolution MINUTE_5 --count 20
python -m broker_wrapper.cli --broker ig_demo historical \
    --epic IX.D.DAX.IFM.IP --from 2026-05-01T00:00:00 --to 2026-05-10T00:00:00 \
    --resolution HOUR
python -m broker_wrapper.cli --broker ig_demo reconcile --refs bot-abc bot-def
```

## Programmatic usage

```python
from broker_wrapper import get_broker

broker = get_broker("ig_demo")
env = broker.connect()
assert env.ok

price = broker.get_price("IX.D.DAX.IFM.IP")
if price.ok:
    print(price.data["bid"], price.data["ask"])

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
pytest tests/ -v
```

The unit tests use mocked HTTP — no network, no credentials needed.

## What goes where in this module

```
broker_wrapper/
├── envelope.py            ← standard response container
├── exceptions.py          ← typed error hierarchy
├── credentials.py         ← OS keyring access
├── models.py              ← normalized cross-broker dataclasses
├── filters.py             ← deterministic "tradeable?" rules + sizing math
├── factory.py             ← get_broker("ig" | "ig_demo")
├── cli.py                 ← standalone CLI / JSON pipe
├── adapters/
│   ├── base.py            ← BrokerAdapter ABC
│   └── ig_adapter.py      ← IG REST implementation
└── streaming/
    ├── base.py            ← StreamClient ABC + PollingStreamClient
    └── ig_lightstreamer.py  ← skeleton, finished next session
```

## Open items / known limits

1. **Lightstreamer not finished.** Production streaming pending; polling
   client works in the meantime.
2. **Endpoint specifics need live verification.** The IG REST endpoints
   used here are written from the public API documentation. Each one
   should be hit against the demo account in the smoke test before
   trusting it with real money.
3. **DAX CFD epics** — exact epic strings depend on your IG product
   subscriptions. Use `search` to discover them rather than hardcoding.
4. **Trade-history parsing** is best-effort. IG's transaction format
   varies by deal type; cross-check against a known closed deal.
