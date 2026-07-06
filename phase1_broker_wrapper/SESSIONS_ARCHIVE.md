---
status: archive
purpose: Verbatim session-history archive rotated out of `CLAUDE.md` **and** `lightstreamer_integration_notes.md`
read-when: auditing how a past phase-1 / Lightstreamer decision came about — never needed at session start
detail: L3
up: ./CLAUDE.md
updated: 2026-07-06
---

# phase1_broker_wrapper — Session Archive

> The blocks below were moved here **verbatim, unedited** from `CLAUDE.md` **and** `lightstreamer_integration_notes.md` on 2026-07-06
> (Doc-Layers rotation, Nikinger-approved — same auditability rule as the 2026-07-03 root
> CLAUDE.md archive move). Source order preserved (newest-first unless noted). The newest
> `## Session stopped` block always stays in the source file; at each session end, the
> previously-newest block rotates here.

---

## — Source: `CLAUDE.md` —

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

---


---

## — Source: `lightstreamer_integration_notes.md` —

## Session stopped — 2026-05-21

### Completed
- v8: subscription migrated to `PRICE:{account_id}:{epic}` (dead `L1:`/`MARKET:` feed).
- v9: protocol bumped to `TLCP-2.4.0.lightstreamer.com` — still HTTP 400 at create_session.
- **v10 (current): `IGLightstreamerClient` rewritten to wrap the official Lightstreamer
  SDK (`lightstreamer-client-lib>=2.2.2`).** Raw TLCP deleted. `requirements.txt`,
  `phase1_broker_wrapper/CLAUDE.md`, and `scripts/test_lightstreamer.py` docstring updated.
- `tests/test_lightstreamer.py`: rewritten for the SDK. Full suite **49/49 green**.

### Live test result — ✅ PASS (2026-05-21, 08:04 UTC, DAX open)
```
[CONOK ] session established  (+0.3s)   status CONNECTED:WS-STREAMING
[SUBOK ] subscription confirmed for IX.D.DAX.IFMM.IP
[TICK #01] bid=24745.5  ask=24747.3  ts=2026-05-21T08:04:30.231Z
[TICK #02] bid=24745.0  ask=24746.8  ts=2026-05-21T08:04:30.702Z
[TICK #03] bid=24744.8  ask=24746.6  ts=2026-05-21T08:04:30.831Z
result: PASS  (3 ticks in 0.5s)
```
The official-SDK rewrite (v10) connected over WebSocket and delivered live `PRICE` ticks —
the raw-TLCP HTTP 400 wall is gone. Phase 1 Lightstreamer is complete.

### Done
- Phase 1 Lightstreamer marked ✅ in `phase1_broker_wrapper/CLAUDE.md` + `README.md`,
  root `CLAUDE.md` ("Current state") + `README.md`, and this file.

### Open questions / blockers
- `lightstreamerEndpoint` URL ✅ confirmed live: `https://demo-apd.marketdatasystems.com`
- SDK connects to IG demo (→ CONOK) ✅ confirmed live (`CONNECTED:WS-STREAMING`)
- PRICE feed delivers ticks ✅ confirmed live (3 ticks, real DAX bid/ask)
- IG Europe GmbH live account still pending (noted in CLAUDE.md) — re-test against live before go-live

---

## Session stopped — 2026-05-20

### Completed
- `broker_wrapper/adapters/ig_adapter.py`: added `self._lightstreamer_endpoint = ""` in `__init__`; capture `body_meta.get("lightstreamerEndpoint", "")` in `_login()`; added `lightstreamer_endpoint` property
- `broker_wrapper/streaming/ig_lightstreamer.py`: full TLCP-2.1.0 implementation — `_create_ls_session`, `_open_bind_stream`, `_send_subscribe`, `_resubscribe_all`, `_reader_loop`, `_read_from_response`, `_handle_line`, `_handle_update`, plus helpers `_ensure_scheme` and `_utm_to_iso`
- `broker_wrapper/factory.py`: added `get_stream(adapter) -> IGLightstreamerClient`
- `broker_wrapper/streaming/__init__.py`: exported `IGLightstreamerClient` and `PriceCallback`
- `tests/test_lightstreamer.py`: 19 tests — all green; full suite 50/50 passing
- **stop() hang fix (v2)**: `socket.shutdown(SHUT_RD)` via `resp.raw._connection.sock` in `_interrupt_response()`
- **create_session hang fix (v3)**: `stream=True`, parse headers only
- **iter_content GC fix (v4)**: replaced `for chunk in iter_content():` with `resp.raw.read()` in header parse loop
- **dual-decoder fix (v5)**: replaced `iter_content()` in main read loop with `resp.raw.read()`
- **bind_session fix (v6)**: `create_session.txt` sends preamble messages but NOT CONOK — CONOK/PROBE/U come from `bind_session.txt`. Added `_open_bind_stream()` method; `create_session.txt` response is now closed after header parsing.
- **LS_cid fix (v7)**: added `LS_cid=mgQkwtwdysogQz2BJ4Ji kOj2Bg` to `create_session.txt` POST — mandatory TLCP-2.1.0 key; without it IG returns SYNC ERROR on all subsequent requests.

### Next
- Run `python scripts/test_lightstreamer.py --timeout 30 --ticks 3 --debug` during market hours (Mon–Fri 08:00–22:30 CET)
  - PASS (exit 0): all confirmed, Phase 1 Lightstreamer is complete
  - PARTIAL (exit 2): CONOK+SUBOK confirmed (connection layer OK), re-run during market hours for ticks
- If PASS/PARTIAL: mark open questions below as ✅ and close Phase 1 Lightstreamer

### Open questions / blockers
- `lightstreamerEndpoint` URL format ✅ confirmed live: `https://demo-apd.marketdatasystems.com`
- `ControlAddress` response format ✅ confirmed live: bare hostname (e.g. `apd245f.marketdatasystems.com`), normalised by `_ensure_scheme()`
- `bind_session.txt` URL ✅ confirmed: uses `control_address + "/lightstreamer/bind_session.txt"`
- IG Europe GmbH live account still pending (noted in CLAUDE.md)


2026-07-06 lightstreamer diagnosis test run: 
htstreamer_multi.py
[diag] Lightstreamer multi-epic diagnosis — epics: ['IX.D.DAX.IFMM.IP', 'IX.D.STXE.IFM.IP', 'IX.D.CAC.IFE.IP', 'IX.D.IBEX.IFM.IP']
[diag] running mode M1 (one Subscription per epic)...
[diag] running mode M2 (one multi-item Subscription)...
[diag] hypothesis hits: {'H1_item_string': False, 'H2_subscription_limit': False, 'H3_mode_dependent': False, 'H4_instrument_class': False}
{
  "broker": "ig_demo",
  "connected": true,
  "epics": [
    "IX.D.DAX.IFMM.IP",
    "IX.D.STXE.IFM.IP",
    "IX.D.CAC.IFE.IP",
    "IX.D.IBEX.IFM.IP"
  ],
  "settle_s": 10.0,
  "m1": {
    "mode": "M1",
    "client_status": "CONNECTED:WS-STREAMING",
    "outcomes": {
      "IX.D.DAX.IFMM.IP": {
        "epic": "IX.D.DAX.IFMM.IP",
        "subscribed": true,
        "errors": [],
        "item_updates": 21
      },
      "IX.D.STXE.IFM.IP": {
        "epic": "IX.D.STXE.IFM.IP",
        "subscribed": true,
        "errors": [],
        "item_updates": 2
      },
      "IX.D.CAC.IFE.IP": {
        "epic": "IX.D.CAC.IFE.IP",
        "subscribed": true,
        "errors": [],
        "item_updates": 15
      },
      "IX.D.IBEX.IFM.IP": {
        "epic": "IX.D.IBEX.IFM.IP",
        "subscribed": true,
        "errors": [],
        "item_updates": 7
      }
    }
  },
  "m2": {
    "mode": "M2",
    "client_status": "CONNECTED:WS-STREAMING",
    "outcomes": {
      "IX.D.DAX.IFMM.IP": {
        "epic": "IX.D.DAX.IFMM.IP",
        "subscribed": true,
        "errors": [],
        "item_updates": 60
      },
      "IX.D.STXE.IFM.IP": {
        "epic": "IX.D.STXE.IFM.IP",
        "subscribed": true,
        "errors": [],
        "item_updates": 60
      },
      "IX.D.CAC.IFE.IP": {
        "epic": "IX.D.CAC.IFE.IP",
        "subscribed": true,
        "errors": [],
        "item_updates": 60
      },
      "IX.D.IBEX.IFM.IP": {
        "epic": "IX.D.IBEX.IFM.IP",
        "subscribed": true,
        "errors": [],
        "item_updates": 60
      }
    }
  },
  "hypothesis_hits": {
    "H1_item_string": false,
    "H2_subscription_limit": false,
    "H3_mode_dependent": false,
    "H4_instrument_class": false
  }
}

---

