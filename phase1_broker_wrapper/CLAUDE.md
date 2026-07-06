---
status: closed-phase
purpose: Phase-1 head — IG broker wrapper (Envelope contract, auth, REST+Lightstreamer), hardening state
read-when: working in phase1_broker_wrapper/ — read this head + its newest Session-stopped block first
detail: L2
up: ../CLAUDE.md
down:
  - ./SESSIONS_ARCHIVE.md      # full session history (L3)
  - ./README.md
  - ../docs/concepts/phase1_broker_api_konzept.md   # full concept/plan snapshot (L3)
updated: 2026-07-06
---
# broker_wrapper — Claude Code context

## Project
Phase 1 of a DAX intraday trading bot. This package is the broker abstraction layer.
Full architecture and all decisions: see `phase1_broker_api_konzept.md`.

## Stack
- Python 3.11+ · venv at `.venv/` · activate before any command
- `requests` for REST · `keyring` for credentials · `pytest` for tests
- `lightstreamer-client-lib` for streaming (official SDK — a protocol library, NOT a broker library)
- No third-party *broker* libraries (raw REST for all broker calls)

## Commands
```bash
source .venv/bin/activate
pytest tests/ -v                                               # 49 unit tests (incl. Lightstreamer SDK), no network
python scripts/smoke_test.py --epic IX.D.DAX.IFMM.IP          # REST end-to-end check
python scripts/smoke_test.py --order --size 1                  # full order lifecycle
python scripts/test_lightstreamer.py                           # Lightstreamer live stream validation
python scripts/test_lightstreamer.py --ticks 5 --timeout 60   # stricter live stream check
python -m broker_wrapper.cli --broker ig_demo get-account
```

## Architecture
Every broker method returns an `Envelope` — never raises on broker errors.
Credentials live in OS keyring only — never in files. See `broker_wrapper/credentials.py`.
`BrokerAdapter` (ABC) in `adapters/base.py` is the interface everything implements.
`IGAdapter` in `adapters/ig_adapter.py` is the IG REST implementation (~620 lines).
`StreamClient` (ABC) in `streaming/base.py` defines the streaming interface.
`PollingStreamClient` in `streaming/base.py` is the working REST-polling fallback.
`IGLightstreamerClient` in `streaming/ig_lightstreamer.py` — wraps the official
Lightstreamer SDK (`lightstreamer-client-lib`); subscribes to `PRICE:{account_id}:{epic}`
on the `Pricing` adapter. Live-tested ✅ against IG demo 2026-05-21 (CONOK/SUBOK + ticks);
re-validate via `scripts/test_lightstreamer.py` during market hours.
`get_stream(adapter)` in `factory.py` — creates a configured `IGLightstreamerClient`
from a connected `IGAdapter`.

> 🔁 **Phase-7-Edit (2026-06-23, cross-phase — user-authorized "specific yes"):**
> `IGAdapter.close_position` now **polls the close deal confirmation** for the realised
> close. The DELETE returns only a `dealReference`; we capture it, call
> `_poll_confirms(close_ref)` (the same helper `open_position` uses for the fill `level`),
> and surface `close_level` + realised `profit`/`profitCurrency` additively in the envelope
> `data` (`{deal_id, status, close_level, profit_loss, profit_currency, close_deal_reference}`).
> **Why:** Phase 7 needs P&L at close time, but IG demo only books `/history/transactions`
> **after settlement** (verified 2026-06-23: `get_trade_history(days=1)` returns 0 rows
> intraday) — so the transaction-history path is unusable for same-session reward. The close
> confirm is the lag-free source. **Best-effort + safe:** the confirm poll is wrapped in
> `try/except` and the close stays **ok-returning for any accepted DELETE** (a confirm
> failure/timeout → `None` fields, never an error envelope) → P5's existing close/abort
> behaviour is unchanged. +3 mocked tests in `tests/test_ig_adapter.py` (P1 49 → **52**).
> Detail: `phase7_reward/` + `docs/concepts/phase7_reward_concept.md` §9.

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
- Don't add third-party broker libraries (`trading-ig`, `ib_insync` etc.) — the
  official Lightstreamer SDK is a protocol library, not a broker library, and is the
  sanctioned streaming transport
- Don't add credentials to any file, including `.env`
- Don't use `raise` in adapter methods for broker errors — return error envelopes
- Don't modify `BrokerAdapter` (ABC) without updating all implementations
- Don't consider a subtask done until `pytest tests/ -v` is green

## After every task or subtask
- Add `pytest`-compatible tests in `tests/` for every new function (mocked HTTP, no live calls)
- Update `phase1_broker_api_konzept.md` if any architectural decision changed
- If the session ends mid-task, append a `## Session stopped` section to the
  relevant notes file (e.g. `lightstreamer_integration_notes.md`) containing:
  - What was completed (with file names and function names)
  - What is next
  - Any open questions or blockers

---

## Session stopped — 2026-07-04 (Hardening plan Step 3: Test-Backfill — Plan ABGESCHLOSSEN)

> **Auslöser:** direkte Fortsetzung nach Steps 0–2 (committed a089126), gleiche
> Session. Nikinger-Freigabe: „commit mit Note, und außer Live-Tests/Validierung
> — geh weiter" — Step 3 ist reiner Mock/Offline-Test-Backfill, kein Live-Test
> nötig, also direkt weitergemacht statt auf einen neuen Trigger zu warten.

### Completed — Test-Backfill nach Live-Risiko-Reihenfolge (Plan §5)
- **`_parse_bar`/`get_ohlcv`/`get_historical_ohlcv`** (höchstes Risiko — P9s
  `IGBarProvider`-Wiring vom 2026-07-04 verlässt sich exakt auf diese Shape):
  Mid-Berechnung (beide Seiten, nur-bid, nur-ask, leer/`None`), volle
  Envelope-Shape `{"bars":[{timestamp,open,high,low,close,volume}], "allowance":...}`,
  invalid-resolution-Guard auf `get_historical_ohlcv` (vorher nur auf `get_ohlcv`
  getestet).
- **`_parse_transaction`/`get_trade_history`:** vorzeichenbehaftete `size`
  (`"-1.0"` → `-1.0`), `E12.34`-Currency-Stripping, fehlende Felder → `None`
  statt Crash, `days`-Bounds-Guard (`<=0`, `>365`).
- **`search_markets`:** Feld-Mapping (`instrumentType`→`type`, `bid`/`offer`→
  `bid`/`ask`, `market_status`-Normalisierung).
- **`get_account`:** Account-ID-Match, Fallback auf erstes Konto bei
  Nicht-Match, leere Accounts-Liste → `PROTOCOL_ERROR`-Envelope.
- **`get_open_positions`/`_parse_position`:** Happy-Path + fehlende optionale
  Felder (Direction-Default `"BUY"`, `stop_level`/`limit_level` → `None`).
- **`open_position`-Lebenszyklus:** ACCEPTED (Level+deal_id gesetzt) und
  REJECTED (Reason durchgereicht, `level=None`) — beide Fälle `env.ok=True`
  (Submission selbst war erfolgreich, der Deal-Status ist das eigentliche
  Ergebnis, nicht ein Fehler).
- **`reconcile_positions`:** present/missing/unexpected-Diff gegen
  `expected_references`, und der Fall ohne `expected_references` (Diff-Keys
  fehlen ganz statt leer zu sein).
- **`_poll_confirms`-Timeout-Pfad:** `time.monotonic`/`time.sleep` im
  `ig_adapter`-Modul gemockt (kein echtes 5s-Warten) — beweist den
  PENDING-Fallback + die `reason`-Message nach Timeout.
- **`_base_headers`/403:** unauthenticated (keine CST/Token-Header),
  authenticated (Header gesetzt), `auth=True` ohne Session →
  `AuthenticationError`; `_request`s 403-Mapping auf `AUTH_ERROR`.
- **+24 Tests** (52 → 61 nach Steps 1–2 → **85** nach Step 3, exakt in der vom
  Plan geschätzten Größenordnung +25–35 für den Gesamt-Backfill inkl. Steps 1–2).

### Verifiziert (gemockt/offline)
- `pytest phase1_broker_wrapper/tests -q` → **85 passed**, kein echtes Sleep
  in der ganzen Suite (0.24s Laufzeit — `_poll_confirms`-Timeout-Test wäre ohne
  Mock ~5s gewesen).
- Volle Cross-Phase-Regression unverändert grün, kein Test außerhalb P1
  editiert: P2 76 · P3 100 · P4 141 · P5 154 · P6 70 · P7 133 · P8 217 · P9 69 ·
  root 77. `py_compile` clean.
- Plan-Akzeptanz (§7) erfüllt: P1-Suite verdichtet (52→85), 429-Burst wird
  selbst überlebt (bewiesen), `get_market_info` trägt die drei Pip-Felder,
  kein Public-Surface-Bruch, P1 hat jetzt ein `CLAUDE.md` mit
  `## Session stopped`-Konvention (dieses selbst).

### Next
- **`docs/concepts/phase1_hardening_plan.md` ist damit vollständig abgearbeitet**
  (Steps 0–3). Kein weiterer Schritt in diesem Plan offen.
- **Operator (sobald möglich):** die zwei ausstehenden Phase-9-Live-Läufe
  (`--enable-ig-bars`-Beobachtung, Step 7a Lightstreamer-Diagnose) — unverändert
  offen, unabhängig von dieser P1-Arbeit. Ein `verify_instrument`-Lauf gegen die
  DAX-Epic würde jetzt zusätzlich die neuen Pip-Felder im `market_info`-Envelope
  zeigen (Step 2 dieser Session).
- **Commit:** dieser Stand (Step 3 + dieser Block) ist commit-fertig.

### Offene Punkte / blockers
- Keine technischen. Alles Live-Bezogene bleibt beim Nikinger (Phase-9 V2b-Läufe,
  unverändert seit den vorherigen Sessions).

> **Ältere Session-Blöcke** (verbatim ausgelagert, newest-first): [SESSIONS_ARCHIVE.md](./SESSIONS_ARCHIVE.md) — Rotation per Doc-Layers-Konvention ([docs/DOC_LAYERS_CONVENTION.md](../docs/DOC_LAYERS_CONVENTION.md)).
