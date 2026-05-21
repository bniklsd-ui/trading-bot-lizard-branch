# Lightstreamer Integration Notes (Phase 1-V2)

> Supplement to `phase1_broker_api_konzept.md`.
> **Status: ✅ LIVE-TESTED (official Lightstreamer SDK).** PASS on 2026-05-21 against IG
> demo — CONOK + SUBOK + 3 real DAX `PRICE` ticks via `scripts/test_lightstreamer.py`.
>
> ⚠ **Current implementation = official SDK (v10, see bottom).** The "Was gebaut wurde"
> and "TLCP Protokoll — Referenz" sections below describe the abandoned raw-TLCP-over-HTTP
> approach (v1–v9) and are kept only as a historical record — they no longer match the code.

---

## Was gebaut wurde (historisch — raw TLCP, abgelöst in v10)

`IGLightstreamerClient` war ursprünglich als raw-TLCP-over-HTTP-Client implementiert
(TLCP-2.1.0, ~270 Zeilen). Dieser Ansatz scheiterte: IG lieferte HTTP 400 auf
`create_session.txt`. Er wurde in v10 durch einen Wrapper um das offizielle
Lightstreamer-SDK ersetzt.

Geänderte Dateien:
- `broker_wrapper/adapters/ig_adapter.py` — `_lightstreamer_endpoint` capture in `_login()`, `lightstreamer_endpoint` property
- `broker_wrapper/streaming/ig_lightstreamer.py` — vollständige TLCP-Implementierung
- `broker_wrapper/factory.py` — `get_stream(adapter) -> IGLightstreamerClient`
- `broker_wrapper/streaming/__init__.py` — `IGLightstreamerClient`, `PriceCallback` exportiert
- `tests/test_lightstreamer.py` — 17 neue Tests

---

## Gap 1 — `lightstreamerEndpoint` aus Session extrahieren ✅

`POST /session` (v2) gibt im Response-Body zurück:
```json
{
  "currentAccountId": "Z6BEGX",
  "lightstreamerEndpoint": "https://push.lightstreamer.com/...",
  ...
}
```

In `ig_adapter.py`, Methode `_login()`, ergänzt:
```python
body_meta = resp.json() if resp.content else {}
current = body_meta.get("currentAccountId")
self._lightstreamer_endpoint = body_meta.get("lightstreamerEndpoint", "")

if current and current != self._account_id:
    self._switch_account(self._account_id)
```

Property auf `IGAdapter`:
```python
@property
def lightstreamer_endpoint(self) -> str:
    return self._lightstreamer_endpoint or ""
```

---

## Gap 2 — IG-spezifisches Lightstreamer Auth-Format ✅

IG verwendet kein Standard-Username/Password. Stattdessen:
```
LS_user     = account_id              # z.B. "Z6BEGX"
LS_password = "CST-{cst}|XST-{security_token}"
```

Beide Werte kommen aus dem `IGAdapter` nach erfolgreichem `connect()`:
```python
adapter._account_id       # → LS_user
adapter._cst              # → Teil von LS_password
adapter._security_token   # → Teil von LS_password
```

---

## Gap 3 — Factory-Pfad für Lightstreamer ✅

```python
# factory.py
def get_stream(adapter: IGAdapter) -> IGLightstreamerClient:
    if not adapter.is_connected():
        raise RuntimeError("connect() must be called before get_stream()")
    return IGLightstreamerClient(
        cst=adapter._cst,
        security_token=adapter._security_token,
        account_id=adapter._account_id,
        lightstreamer_endpoint=adapter.lightstreamer_endpoint,
    )
```

---

## TLCP Protokoll — Referenz

IG nutzt Lightstreamer's Text-based Client Protocol (TLCP) über HTTP.

### Session erstellen
```
POST {lightstreamer_endpoint}/lightstreamer/create_session.txt
Body (form-encoded):
  LS_protocol=TLCP-2.4.0.lightstreamer.com   # 2.1.0 → HTTP 400 (siehe v9)
  LS_cid=mgQkwtwdysogQz2BJ4Ji kOj2Bg          # Pflicht, sonst SYNC ERROR
  LS_adapter_set=DEFAULT
  LS_user={account_id}
  LS_password=CST-{cst}|XST-{security_token}
```

Antwort:
```
OK
SessionId:S-...
ControlAddress:...
KeepaliveMillis:5000
```

### Subscription hinzufügen
```
POST {control_address}/lightstreamer/control.txt
Body:
  LS_session={session_id}
  LS_op=add
  LS_table=1
  LS_id=PRICE:{account_id}:{epic}    # z.B. PRICE:Z6BEGX:IX.D.DAX.IFMM.IP
  LS_schema=BIDPRICE1 ASKPRICE1 TIMESTAMP NET_CHG NET_CHG_PCT DLG_FLAG DELAY
  LS_mode=MERGE
  LS_data_adapter=Pricing
```
> ⚠ Das alte `L1:`/`MARKET:`-Feed wurde am 8. Mai 2026 von IG abgeschaltet.
> Es verbindet weiterhin (CONOK/SUBOK), liefert aber keine Ticks mehr.
> Details: `lightstreamer_ig_reference.md`.

### Stream lesen
```
POST {lightstreamer_endpoint}/lightstreamer/bind_session.txt
Body:
  LS_session={session_id}
```

Antwort (chunked streaming):
```
PROBE                          # heartbeat — kein Response nötig
CONOK,{session_id},...         # connection ok
SUBOK,1,1,5                    # subscription ok
U,1,1,24615.9|24617.0|08:30:00.000|24800.0|24400.0  # update
```

Update: `U,{table},{item},{field1}|{field2}|...`
Leerstring = Feld unverändert seit letztem Update (MERGE-Mode).
Kein PROBE für >15s → Session tot → neu verbinden.

---

## Offene Fragen (noch live zu verifizieren)

1. **`lightstreamerEndpoint` URL-Format auf IG Demo:** Die Implementierung
   erwartet `https://push.lightstreamer.com` Style. `_ensure_scheme()` normalisiert
   sowohl `hostname` als auch `https://hostname` Varianten. Beim ersten
   `test_lightstreamer.py`-Lauf: den gedruckten Endpoint-Wert prüfen.

2. **`ControlAddress` Response-Format:** Kann nur ein Hostname oder eine vollständige
   URL sein — `_ensure_scheme()` behandelt beide. Empirisch bestätigen.

3. **Market-Hours:** Test muss während Handelszeiten (Mo–Fr 08:00–22:30 CET) laufen,
   sonst keine Ticks trotz funktionierender Verbindung.

Nach erfolgreicher Live-Validierung:
- Open questions hier als ✅ markieren
- `lightstreamer_integration_notes.md` Status auf "COMPLETE" setzen
- Phase 1 in `CLAUDE.md` und `README.md` vollständig als ✅ schließen

---

---

## Bug fix — create_session hang + stop() hang (2026-05-20, v3)

`scripts/test_lightstreamer.py` hung indefinitely after printing "[4] start stream".
Traceback (from ^C) showed the hang was inside `stream.start()` → `_create_ls_session()`
→ `self._http.post(...)` → `r.content` → `urllib3.read_chunked()` → `socket.readline()`.

**Primary root cause (v3):**

`create_session.txt` returns a `Transfer-Encoding: chunked` response that never closes
— it IS the primary TLCP data stream. The old code called it **without `stream=True`**
and accessed `resp.text`, which tries to download the entire body → blocks forever.

**Also wrong:** the reader loop called `bind_session.txt` as its primary source.
`bind_session.txt` is for reconnects only; the initial data stream is the
`create_session.txt` response.

**Changes in `broker_wrapper/streaming/ig_lightstreamer.py` (v3):**

1. `_create_ls_session()`: use `stream=True, timeout=(10.0, 15.0)`. Parse ONLY the
   metadata headers via `iter_content()` + manual line split. Stop at first non-header
   TLCP line (CONOK, PROBE, etc.) and push remaining bytes to `self._pending`. Store
   the live response in `self._response`.

2. `__init__()`: add `self._pending: bytes = b""` for leftover bytes.

3. `_reader_loop()`: read from `self._response` (the create_session stream). Reconnect
   via full `_create_ls_session()` on error.

4. `_bind_and_read()` → replaced by `_read_from_response(resp)`: reads from any
   `requests.Response`, starts with `self._pending`, uses `iter_content(chunk_size=512)`.

5. `_handle_line()`: added `log.info()` for CONOK and SUBOK milestones.

**Retained from earlier fix:**
- `stop()` with `_interrupt_response()` using `socket.shutdown(SHUT_RD)` — correct.
- `self._http = requests.Session()` reinit in `start()`.

**`scripts/test_lightstreamer.py`**: rewritten. Tracks CONOK/SUBOK/tick milestones
via a logging handler. Exit code 2 = PARTIAL (CONOK+SUBOK but no ticks = market closed).

Tests: 48/48 passing.

---

## Bug fix — iter_content() generator GC closes streaming socket (2026-05-20, v4)

After v3, `--debug` output showed a rapid reconnect loop: `create_session.txt` returned
200 and `control.txt` returned 200 (subscribe OK), but then immediately "Resetting dropped
connection" and a new `create_session.txt` — no CONOK ever appeared.

**Root cause:**

`_create_ls_session()` used `for chunk in resp.iter_content(chunk_size=256):` to parse
session headers, then `break` when the first non-header TLCP line was found. Breaking out
of the `for` loop causes the `iter_content()` generator to go out of scope and be GC'd.
Python calls `generator.close()` → throws `GeneratorExit` into urllib3's
`yield from self.raw.stream()` → urllib3 closes the underlying TCP socket.
By the time `_read_from_response()` calls `resp.iter_content(chunk_size=512)`, the
socket is already dead — the generator yields nothing — and the reader loop immediately
hits the reconnect path.

**Fix (`ig_lightstreamer.py`, `_create_ls_session()`):**

Replaced `for chunk in resp.iter_content(chunk_size=256):` with:
```python
while not metadata_done:
    chunk = resp.raw.read(256)
    if not chunk:
        break
    ...
```

`resp.raw.read(n)` is a plain method call with no generator. The read position is stored
in `resp.raw._fp` and is shared with any subsequent `resp.iter_content()` call, so
`_read_from_response()` continues from exactly where the header parse left off.

**Fix (`tests/test_lightstreamer.py`, `_mock_streaming_response()`):**

Updated to mock `raw.read.side_effect = [text.encode(), b""]` instead of
`iter_content.return_value`.

Tests: 48/48 passing.

---

## Bug fix — iter_content() uses urllib3's read_chunked(), raw.read() uses http.client's decoder (2026-05-20, v5)

After v4, `_create_ls_session()` uses `resp.raw.read(256)` for header parsing and
`_read_from_response()` uses `resp.iter_content(chunk_size=512)` for the main loop.
These two code paths use **different, unsynchronised chunked-transfer decoders**:

- `resp.raw.read(n)` → `urllib3.HTTPResponse._raw_read()` → `_fp_read()` →
  **`http.client.HTTPResponse.read(n)`** — Python's own built-in chunked decoder,
  which maintains its own `chunk_left` counter and reads chunk-size lines internally.
- `resp.iter_content(n)` → `urllib3.HTTPResponse.stream(n)` → (because
  `self.chunked and self.supports_chunked_reads()`) → **urllib3's `read_chunked()`** →
  `_update_chunk_length()` → `self._fp.fp.readline()` — reads chunk-size lines
  directly from the raw socket file, **bypassing** `http.client.HTTPResponse`'s state.

After `resp.raw.read(256)` advances `http.client.HTTPResponse`'s decoder by 256 bytes,
the raw socket is at an arbitrary offset inside a chunk. urllib3's
`_update_chunk_length()` reads the next line from that offset and gets a fragment of
TLCP text (e.g. `ush\r\n` from the middle of `CONOK,...`) instead of a hex chunk size
→ `InvalidChunkLength(got length b'ush\r\n', 256 bytes read)`.

The `256 bytes read` in the exception repr is `response.tell()`, confirming exactly
256 decoded bytes were consumed by the header parse before the main loop failed.

**Fix (`ig_lightstreamer.py`, `_read_from_response()`):**

Replaced `for chunk in resp.iter_content(chunk_size=512):` with:
```python
while not self._stop_event.is_set():
    chunk = resp.raw.read(512)
    if not chunk:
        break
```
Both header parse and main loop now use the same `http.client.HTTPResponse` decoder,
so they advance the same state machine and the raw socket pointer stays consistent.
Stop behaviour is unchanged: `socket.shutdown(SHUT_RD)` interrupts `resp.raw.read()`
just as it interrupted `iter_content()`.

Tests: 48/48 passing.

---

## Bug fix — create_session.txt sends preamble only; CONOK comes from bind_session.txt (2026-05-20, v6)

After v5, the `InvalidChunkLength` crash was gone. Instead the reader loop received
many `LS← Preamble: preparing push` lines but NO CONOK ever appeared — the test
timed out with "no CONOK within 15s". The `IncompleteRead(286 bytes read)` at the
end was caused by `stream.stop()` shutting down the socket, not by the server.

**Root cause:**

The v3 fix assumed `create_session.txt` was the perpetual TLCP data stream and noted
that `bind_session.txt` was "for reconnects only". This was wrong for IG's server.

IG's `create_session.txt` response body contains:
1. Metadata headers: `OK`, `SessionId:...`, `ControlAddress:...`, `KeepaliveMillis:...`
2. Server preamble messages: `Preamble: preparing push` (repeated, server warming up)
3. Connection closes (or body ends) — **CONOK is never sent here**

The actual TLCP event stream (CONOK, PROBE, SUBOK, U updates) comes from
**`bind_session.txt`**, which must be called after `create_session.txt` and
subscriptions.

**Correct protocol flow (empirically confirmed):**
1. POST `create_session.txt` → parse SessionId + ControlAddress, then CLOSE response
2. POST `control.txt` → subscribe to epics
3. POST `bind_session.txt` → perpetual stream: CONOK, PROBE, SUBOK, U updates

**Changes in `broker_wrapper/streaming/ig_lightstreamer.py` (v6):**

1. `_create_ls_session()`: after parsing headers, call `resp.close()`. Do NOT store
   the response in `self._response`. Remove `self._pending`.

2. New `_open_bind_stream()`: POST `control_address + /lightstreamer/bind_session.txt`
   with `LS_session=session_id`, `stream=True`. Store response in `self._response`.
   Returns the response for the reader thread.

3. `start()`: call `_open_bind_stream()` after `_resubscribe_all()`.

4. `_reader_loop()`: reconnect path calls `_open_bind_stream()` instead of reading
   from `self._response` set by `_create_ls_session()`.

5. `_read_from_response()`: removed `buf = self._pending` / `self._pending = b""` lines.
   `buf` starts empty — the bind_session stream begins with CONOK, no pre-existing bytes.

6. `__init__()`: removed `self._pending`.

**`tests/test_lightstreamer.py` (v6):**

- `test_create_session_parses_ok_response`: replaced `assert c._response is not None`
  with `mock_resp.close.assert_called_once()` and `assert c._response is None`.
- Added `test_open_bind_stream_posts_to_bind_session`.

Tests: 49/49 passing.

---

## Bug fix — missing LS_cid causes SYNC ERROR on all subsequent requests (2026-05-20, v7)

After v6, every `bind_session.txt` (and `control.txt`) returned exactly 12 bytes =
`SYNC ERROR\r\n`, causing an immediate reconnect loop. Session ID and ControlAddress
were returned correctly, but the session itself was invalid.

**Root cause:**

`create_session.txt` was missing the `LS_cid` parameter — a mandatory "protocol
magic key" required by all Lightstreamer TLCP 2.1.0 clients. Without it, IG's server
creates the session in a degraded state that rejects all subsequent operations with
`SYNC ERROR`. This was confirmed by:
- The Lightstreamer TLCP 2.1.0 specification
- The `trading-ig` Python reference implementation
- Lightstreamer official quickstart examples

**Standard value (same for all Lightstreamer TLCP clients):**
```
LS_cid=mgQkwtwdysogQz2BJ4Ji kOj2Bg
```
(The space is intentional; `requests.post(data={...})` encodes it as `+`.)

**Fix (`ig_lightstreamer.py`, `_create_ls_session()`):**

Added `"LS_cid": "mgQkwtwdysogQz2BJ4Ji kOj2Bg"` to the `create_session.txt` POST.
Also added `"Preamble:"` to the recognized-header skip list so preamble messages
(`Preamble: preparing push`) appearing in the metadata section don't abort the header
parser before SessionId/ControlAddress are found.

Tests: 49/49 passing.

---

## Bug fix — L1/MARKET decommissioned (8 May 2026) → migrate to PRICE subscription (2026-05-21, v8)

After v7 the connection layer was confirmed live (CONOK + SUBOK, ControlAddress,
bind_session all ✅) but **no `U` ticks ever arrived**. The connection was healthy;
the subscription was dead.

**Root cause:**

IG decommissioned the `MARKET:{epic}` subscription and its `L1:{epic}` alias on
**8 May 2026**. Any subscription using `MARKET:`/`L1:` (fields `BID OFFER UPDATE_TIME …`)
still returns SUBOK but the server sends zero updates. The committed code
(`6817b09`) subscribed via `L1:{epic}` — hence the silent no-tick behaviour.
Source: `lightstreamer_ig_reference.md`, Rule 0.

(An uncommitted working-tree experiment had switched to `CHART:{epic}:TICK`. That
was unverified and not the reference's prescribed feed; it has been replaced.)

**Fix (`ig_lightstreamer.py`, `_send_subscribe()`):**

Subscribe to IG's official replacement feed — the per-account `PRICE` item via the
`Pricing` data adapter:
```python
"LS_id":           f"PRICE:{self._account_id}:{epic}",
"LS_schema":       "BIDPRICE1 ASKPRICE1 TIMESTAMP NET_CHG NET_CHG_PCT DLG_FLAG DELAY",
"LS_mode":         "MERGE",
"LS_data_adapter": "Pricing",
```
Field mapping: `BID→BIDPRICE1`, `OFFER→ASKPRICE1`, `UPDATE_TIME→TIMESTAMP`
(TIMESTAMP is Unix ms — same as the old UTM).

**Deliberately NOT changed:**
- **TLCP-2.1.0 + LS_cid** handshake kept — it was already proven live (CONOK/SUBOK).
  Changing only the subscription isolates the fix to the actual root cause. (The
  reference Rule 2 suggests bumping to TLCP-2.4.0; left as a fallback if PRICE still
  yields no ticks.)
- `_handle_update` — parses positionally (indices 0/1/2), so the new schema fits
  unchanged.
- `_field_cache` — MERGE-mode "empty = unchanged" caching already implemented; the
  PRICE feed (MERGE) needs exactly this. The previous note's "DISTINCT" comment was
  corrected to MERGE.
- `_utm_to_iso` — already converts ms-since-epoch → ISO; TIMESTAMP is identical, so
  no change (functionally equal to the reference's `_timestamp_to_iso`).

**Tests (`tests/test_lightstreamer.py`):**

Added `test_send_subscribe_uses_price_feed` (asserts `PRICE:{account_id}:{epic}`,
`BIDPRICE1 ASKPRICE1 TIMESTAMP…` schema, `MERGE`, `Pricing` adapter). Updated stale
DISTINCT/BID-OFR-UTM comments in the update-parsing tests.

Tests: 51/51 passing.

---

## Bug fix — IG rejects TLCP-2.1.0 at create_session → bump to 2.4.0 (2026-05-21, v9)

The first live run after v8 failed **before any subscription**:
```
POST /lightstreamer/create_session.txt HTTP/1.1  400 0
HTTPError: 400 Bad Request ... /lightstreamer/create_session.txt
[ERR] no CONOK within 15s — session creation failed
```

**Root cause:**

IG's Lightstreamer server now rejects the `TLCP-2.1.0` protocol string with HTTP 400.
The v8 note's claim that the 2.1.0 handshake was "proven live" was stale — it no longer
holds. This is the previously-deferred **reference Patch 2** (Rule 2), now forced by
live evidence. Confirmed externally:
- `lightstreamer_ig_reference.md` Rule 2: use `TLCP-2.4.0.lightstreamer.com`.
- Web + canonical Go client `sklinkert/igmarkets`: IG requires
  `TLCP-2.4.0.lightstreamer.com`, with the **same** `LS_cid`
  (`mgQkwtwdysogQz2BJ4Ji kOj2Bg`), `LS_adapter_set=DEFAULT`, `LS_user=accountId`,
  `LS_password=CST-…|XST-…` we already send — so only the protocol string was wrong.

**Fix (`ig_lightstreamer.py`, `_create_ls_session()`):**
```python
"LS_protocol": "TLCP-2.4.0.lightstreamer.com",   # was "TLCP-2.1.0"
```
Nothing else changed. The HTTP `create_session.txt` response stays in the
`OK`/`SessionId:`/`ControlAddress:` format the existing parser handles (the comma-`CONOK`
format is the WebSocket variant, which we do not use), so no parser change was needed.
Module/`_create_ls_session` docstrings updated to drop the 2.1.0 references.

**Tests:** added `test_create_session_uses_tlcp_2_4` (asserts the posted
`LS_protocol == "TLCP-2.4.0.lightstreamer.com"`). Full suite 52/52 passing.

---

## Bug fix — raw HTTP TLCP 400 unresolved → switch to the official Lightstreamer SDK (2026-05-21, v10)

After v9 the live test STILL failed at the very first server call:
```
POST /lightstreamer/create_session.txt HTTP/1.1  400 0
HTTPError: 400 Bad Request ... /lightstreamer/create_session.txt
```
The 400 is opaque (empty body) and happens before any subscription, so neither the PRICE
migration (v8) nor the protocol bump (v9) could fix it. We had applied all three documented
reference patches and the hand-rolled raw-TLCP-over-HTTP handshake was still rejected.

**Decision:** stop hand-rolling TLCP. This is the reference's explicit fallback ("if raw
TLCP continues to have issues after the three patches, switch to the official SDK"). The
canonical working IG client (`sklinkert/igmarkets`) uses WebSocket, and IG now recommends
the official Lightstreamer Python SDK (the old `trading_ig.lightstreamer` module is
deprecated in its favour). The SDK negotiates transport (WebSocket w/ HTTP fallback), the
TLCP version, reconnect, LOOP rebind, MERGE caching and keepalive internally.

**Dependency:** `lightstreamer-client-lib>=2.2.2` (added to `requirements.txt`).
Import: `from lightstreamer.client import LightstreamerClient, Subscription,
SubscriptionListener, ClientListener`. It is a protocol library, not a broker library
(reference pre-cleared this against the no-broker-libs rule).

**Rewrite (`broker_wrapper/streaming/ig_lightstreamer.py`):**
`IGLightstreamerClient` is now a thin wrapper over the SDK. Public surface is unchanged
(constructor kwargs `cst/security_token/account_id/lightstreamer_endpoint`; `_cst`,
`_security_token`, `_account_id`, `_endpoint` attrs; `StreamClient` interface; `_utm_to_iso`).
- `start()`: `LightstreamerClient(endpoint, "DEFAULT")`,
  `connectionDetails.setUser(account_id)`,
  `connectionDetails.setPassword("CST-{cst}|XST-{security_token}")`, `connect()`,
  then subscribe the registered backlog.
- `_do_subscribe()`: `Subscription("MERGE", ["PRICE:{account_id}:{epic}"],
  ["BIDPRICE1","ASKPRICE1","TIMESTAMP"])`, `setDataAdapter("Pricing")`,
  `addListener(_PriceListener)`, `client.subscribe(sub)`.
- `_PriceListener(SubscriptionListener).onItemUpdate` → `PriceTick`; logs `SUBOK` on
  `onSubscription`. `_ClientListener(ClientListener).onStatusChange` logs `CONOK` on
  `CONNECTED:*`. (The CONOK/SUBOK substrings keep `scripts/test_lightstreamer.py`'s
  milestone scraper working with no script-logic change.)
All raw-TLCP internals were deleted (`_create_ls_session`, `_open_bind_stream`,
`_send_subscribe`, `_reader_loop`, `_read_from_response`, `_handle_*`, `_interrupt_response`,
`_ensure_scheme`, `_http`, `_field_cache`, `_table_map`).

**Tests:** `tests/test_lightstreamer.py` rewritten to mock the SDK
(`LightstreamerClient`/`Subscription`) — start/stop/subscribe/unsubscribe + `_PriceListener`
dispatch + retained `_utm_to_iso`/adapter/factory tests. Verified the real (unmocked) SDK
accepts our exact `Subscription`/`setDataAdapter` args and listener signatures.

Tests: **49/49 passing** (mocked, no network).

---

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
