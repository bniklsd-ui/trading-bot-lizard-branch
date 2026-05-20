# broker_wrapper — Claude Code context

## Project
Phase 1 of a DAX intraday trading bot. This package is the broker abstraction layer.
Full architecture and all decisions: see `phase1_broker_api_konzept.md`.

## Stack
- Python 3.11+ · venv at `.venv/` · activate before any command
- `requests` for HTTP · `keyring` for credentials · `pytest` for tests
- No third-party broker libraries (raw REST only)

## Commands
```bash
source .venv/bin/activate
pytest tests/ -v                                        # 31 unit tests, no network
python scripts/smoke_test.py --epic IX.D.DAX.IFMM.IP   # read-only demo API check
python scripts/smoke_test.py --order --size 1           # full lifecycle
python -m broker_wrapper.cli --broker ig_demo get-account
```

## Architecture
Every broker method returns an `Envelope` — never raises on broker errors.
Credentials live in OS keyring only — never in files. See `broker_wrapper/credentials.py`.
`BrokerAdapter` (ABC) in `adapters/base.py` is the interface everything implements.
`IGAdapter` in `adapters/ig_adapter.py` is the IG REST implementation (~620 lines).
`StreamClient` (ABC) in `streaming/base.py` defines the streaming interface.
`PollingStreamClient` in `streaming/base.py` is the working REST-polling fallback.
`IGLightstreamerClient` in `streaming/ig_lightstreamer.py` is a skeleton — to be implemented.

## Confirmed instrument (live-verified on demo)
Epic: `IX.D.DAX.IFMM.IP` · type: INDICES · currency: EUR
min_deal_size: 0.5 · lot_size: 1.0 €/point · spread ~1.8 pts

## Conventions
- All new methods return `Envelope` via `ok_envelope()` or `error_envelope()`
- Code does everything deterministic. AI does only: direction decisions, lessons, Council eval.
- No plaintext credentials ever — always `get_credential(key_name)` from keyring
- Tests go in `tests/` with mocked HTTP — no live API calls in unit tests
- Keep `filters.py` as the tradeable-check home — rules engine, not AI

## Don't
- Don't hardcode the DAX epic — always discover via `search_markets()`
- Don't add third-party broker libraries (`trading-ig`, `ib_insync` etc.)
- Don't add credentials to any file, including `.env`
- Don't use `raise` in adapter methods for broker errors — return error envelopes
- Don't modify `BrokerAdapter` (ABC) without updating all implementations

## After every task or subtask
- Add `pytest`-compatible tests in `tests/` for every new function (mocked HTTP, no live calls)
- Update `phase1_broker_api_konzept.md` if any architectural decision changed
- If the session ends mid-task, append a `## Session stopped` section to the
  relevant notes file (e.g. `lightstreamer_integration_notes.md`) containing:
  - What was completed (with file names and function names)
  - What is next
  - Any open questions or blockers
  - Don't consider a subtask done until its tests pass (`pytest tests/ -v`)
