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

## Session stopped — 2026-07-04 (Hardening plan Steps 0–2 — 429 retry + MarketInfo pip-field passthrough)

> **Auslöser:** Nikinger-Auftrag — Phase-9 Live-Tests stehen aus (können gerade nicht
> gefahren werden), also Ausführung von `docs/concepts/phase1_hardening_plan.md` (Fable/
> Opus-Plan) vorziehen, da dieser Plan keine Live-Tests braucht. Auto-Modus, medium.

### Completed
- **Step 0 (Baseline):** volle Regression lief exakt wie erwartet (P1 52 · P2 76 ·
  P3 100 · P4 141 · P5 154 · P6 70 · P7 133 · P8 217 · P9 69 · root 77). Kein Drift.
  `phase1_broker_wrapper/CLAUDE.md` existierte bereits (Plan-[VERIFY] war falsch —
  keine Skeleton-Erstellung nötig).
- **Step 1 — 429-Retry/Backoff in `_request`** (`ig_adapter.py`): additive
  Konstruktor-Parameter `retry_429_attempts=2`, `retry_429_base_s=1.0`,
  `sleep_fn=time.sleep`. Neuer `retry_429_count`-Parameter auf `_request`
  (unabhängig vom bestehenden `attempt`-Zähler für Timeout/5xx/401-Relogin —
  keine Vermischung der Retry-Semantiken). 429 → bis zu `retry_429_attempts`
  gepacte Retries (`base * 2**count`), danach unverändert `RateLimitError`.
  Die fünf Call-Site-Pacings (`resolve_epics.py`, `verify_instrument.py`,
  `discovery.py`, `promotion.py` — `diag_lightstreamer_multi.py`s `sleep_fn` ist
  unrelated LS-Settle-Wait, nicht HTTP-Pacing, Plan war hier leicht ungenau)
  bleiben unangetastet + bekamen je einen dated Kommentar. **+5 Tests**
  (429→Erfolg nach 1 Retry, 429×3→Erschöpfung+RateLimitError, `retry_429_attempts=0`
  Opt-out, kein Sleep bei 200, 401-Relogin-Regressionsguard — zuvor ungetestet).
- **Step 2 — `get_market_info` Pip-/Contract-Feld-Passthrough:** `MarketInfo`
  (`models.py`) bekam drei additive `str | None = None`-Felder:
  `value_of_one_pip`, `one_pip_means`, `contract_size`. `get_market_info` mappt sie
  aus `instr.get("valueOfOnePip"/"onePipMeans"/"contractSize")`, fehlende Keys →
  `None`, kein Crash. **P9s `pricing.resolve_point_value` liest exakt diese
  Feldnamen bereits fixture-getestet** (`test_ig_fields_value_of_one_pip_resolves`
  etc.) — Pfad 1 (`ig_fields`) aktiviert sich damit ohne jede P9-Änderung, sobald
  ein Operator-Lauf gegen echte IG-Demo-Daten geht. **+4 Tests** (Happy-Path
  Passthrough, fehlende Keys → `None`, bestehende 8 Felder byte-identisch,
  `to_dict`-Key-Set-Roundtrip) — vorher gab es **null** Tests für
  `get_market_info` (Plan §0 Befund 3 bestätigt).

### Verifiziert (gemockt/offline)
- `pytest phase1_broker_wrapper/tests -v` → **61 passed** (52 → 61, +9: 5 vom
  429-Retry + 4 vom Pip-Passthrough).
- Volle Cross-Phase-Regression unverändert grün (kein Test außerhalb P1 editiert):
  P2 76 · P3 100 · P4 141 · P5 154 · P6 70 · P7 133 · P8 217 · P9 69 · root 77.
- `py_compile` clean auf allen berührten Dateien. Kein Public-Surface-Bruch: alle
  neuen Felder additiv mit `None`-Default, `_poll_confirms` erbt den 429-Schutz
  gratis (ruft `_request` intern auf, kein eigener Edit nötig).

### Next
- **Step 3 — Test-Backfill** (Plan §5, größter verbleibender Step: `_parse_bar`/
  `get_ohlcv`-Happy-Path zuerst — Regressionsschutz für P9s `IGBarProvider`-Wiring
  —, dann `_parse_transaction`/`get_trade_history`, `search_markets`,
  `open_position`-Happy-Path/`_poll_confirms`/`reconcile_positions`, restliche
  `_request`-Pfade). Erwartung ~52→~80+, bewusst als **eigener Step/Commit**
  belassen (Plan-Konvention: ein Step = ein Commit), nicht in dieser Session
  mitgezogen.
- **Operator (sobald möglich):** ein `verify_instrument`-Lauf gegen die DAX-Epic
  zeigt jetzt `value_of_one_pip`/`one_pip_means`/`contract_size` im
  `market_info`-Envelope — das wäre der erste echte Beweis, ob P9s Pfad 1
  gegenüber Pfad 2 (Namens-/lot_size-Kreuzcheck) übereinstimmt oder abweicht.
- Danach unverändert offen (aus Phase-9-Notizen, nicht Teil dieser Session):
  die zwei Phase-9-Live-Läufe (`--enable-ig-bars`, Step 7a LS-Diagnose).

### Offene Punkte / blockers
- Keine technischen. **Commit-fertig, wartet auf Nikinger-Trigger** (Claude
  committet nicht automatisch).
