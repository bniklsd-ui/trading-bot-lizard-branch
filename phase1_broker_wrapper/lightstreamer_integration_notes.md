# Lightstreamer Integration Notes (Phase 1-V2)

> Supplement to `phase1_broker_api_konzept.md`.
> Add this section to the konzept when Phase 1-V2 starts.

---

## Was zu bauen ist

`streaming/ig_lightstreamer.py` — `IGLightstreamerClient` vollständig implementieren.
Interface ist bereits fertig definiert (identisch zu `PollingStreamClient`).
Factory-Pfad anpassen. Keine Consumer-Code-Änderungen.

---

## Gap 1 — `lightstreamerEndpoint` aus Session extrahieren

`POST /session` (v2) gibt im Response-Body zurück:
```json
{
  "currentAccountId": "Z6BEGX",
  "lightstreamerEndpoint": "https://push.lightstreamer.com/...",
  ...
}
```

In `ig_adapter.py`, Methode `_login()`, muss ergänzt werden:
```python
body_meta = resp.json() if resp.content else {}
current = body_meta.get("currentAccountId")
self._lightstreamer_endpoint = body_meta.get("lightstreamerEndpoint", "")

if current and current != self._account_id:
    self._switch_account(self._account_id)
```

Dazu Property auf `IGAdapter`:
```python
@property
def lightstreamer_endpoint(self) -> str:
    return self._lightstreamer_endpoint or ""
```

---

## Gap 2 — IG-spezifisches Lightstreamer Auth-Format

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

## Gap 3 — Factory-Pfad für Lightstreamer

`factory.py` braucht eine Hilfsfunktion (oder `get_stream()`) die nach
`broker.connect()` einen fertigen `IGLightstreamerClient` zurückgibt:

```python
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

Oder alternativ als `IGAdapter`-Methode: `adapter.create_stream_client() -> IGLightstreamerClient`.

---

## TLCP Protokoll — Überblick für die Implementierung

IG nutzt Lightstreamer's Text-based Client Protocol (TLCP) über HTTP.

### Session erstellen
```
POST {lightstreamer_endpoint}/lightstreamer/create_session.txt
Body (form-encoded):
  LS_protocol=TLCP-2.1.0
  LS_adapter_set=DEFAULT
  LS_user={account_id}
  LS_password=CST-{cst}|XST-{security_token}
```

Antwort (Text, Zeilenweise):
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
  LS_id=L1:{epic}          # z.B. L1:IX.D.DAX.IFMM.IP
  LS_schema=BID OFFER UPDATE_TIME HIGH LOW
  LS_mode=MERGE
  LS_data_adapter=DEFAULT
```

### Stream lesen (bind_session)
```
POST {lightstreamer_endpoint}/lightstreamer/bind_session.txt
Body:
  LS_session={session_id}
```

Antwort ist ein HTTP-Streaming-Response (chunked). Jedes Update eine Zeile:
```
PROBE                          # heartbeat — ignorieren
CONOK,{session_id},...         # connection confirmed
SUBOK,1,1,5                    # subscription ok (table 1, item 1, 5 fields)
U,1,1,24615.9|24617.0|08:30:00.000|24800.0|24400.0  # update
```

Update-Format: `U,{table},{item},{field1}|{field2}|...`
Felder in derselben Reihenfolge wie im `LS_schema` angegeben.
Leerstring = Feld unverändert seit letztem Update.

### Heartbeat / PROBE
IG sendet alle 5s ein `PROBE`. Kein Response nötig.
Wenn kein PROBE für >15s → Session tot → neu verbinden.

---

## Implementation-Ansatz (Empfehlung)

Raw TLCP mit `requests` (streaming response):

```python
import requests

response = requests.post(
    f"{endpoint}/lightstreamer/bind_session.txt",
    data={"LS_session": session_id},
    stream=True,
    timeout=30,
)

for line in response.iter_lines(decode_unicode=True):
    if line.startswith("U,"):
        _parse_update(line)
    elif line == "PROBE":
        pass  # heartbeat, continue
```

Reconnect-Logik: bei Verbindungsabbruch `create_session` neu aufrufen
(neue Session-ID), dann Subscriptions wiederholen.

Alternativ: `pip install lightstreamer-client-python` (offizielles SDK von Lightstreamer).
Weniger Code, aber externe Abhängigkeit — widerspricht dem Bauprinzip "raw requests".

---

## Prompt für Claude Code Session

```
Implement IGLightstreamerClient in streaming/ig_lightstreamer.py.

Context:
- Read CLAUDE.md and phase1_broker_api_konzept.md first
- Read streaming/base.py for the StreamClient interface to implement
- Read streaming/ig_lightstreamer.py for the existing skeleton and TODOs
- Read adapters/ig_adapter.py to understand the session/token model
- Read the Lightstreamer integration notes (this file)

Task:
1. Add `_lightstreamer_endpoint` capture to `_login()` in ig_adapter.py
2. Add `lightstreamer_endpoint` property to IGAdapter
3. Implement IGLightstreamerClient using raw TLCP over requests (no SDK)
4. Add `get_stream(adapter)` to factory.py
5. Write unit tests in tests/test_lightstreamer.py (mock the HTTP streaming)

The interface is fixed — start() stop() subscribe(epic, cb) unsubscribe(epic).
PriceTick(epic, bid, ask, timestamp) is the callback payload.
All methods must be thread-safe (PollingStreamClient is the reference).
```

---

## Session stopped — 2026-05-20

### Completed
- `broker_wrapper/adapters/ig_adapter.py`: added `self._lightstreamer_endpoint = ""` in `__init__`; capture `body_meta.get("lightstreamerEndpoint", "")` in `_login()`; added `lightstreamer_endpoint` property
- `broker_wrapper/streaming/ig_lightstreamer.py`: full TLCP-2.1.0 implementation (~270 lines) — `_create_ls_session`, `_send_subscribe`, `_resubscribe_all`, `_reader_loop`, `_bind_and_read`, `_handle_line`, `_handle_update`, plus helpers `_ensure_scheme` and `_update_time_to_iso`
- `broker_wrapper/factory.py`: added `get_stream(adapter) -> IGLightstreamerClient`
- `broker_wrapper/streaming/__init__.py`: exported `IGLightstreamerClient` and `PriceCallback`
- `tests/test_lightstreamer.py`: 17 new tests — all green; full suite 48/48 passing

### Next
- Live validation: run `scripts/smoke_test.py --epic IX.D.DAX.IFMM.IP` and verify Lightstreamer stream delivers PriceTick callbacks (requires demo credentials in keyring)
- If smoke test passes, update Phase 1 status in CLAUDE.md Lightstreamer note and consider Phase 2 start

### Open questions / blockers
- `lightstreamerEndpoint` URL format on IG demo: the implementation expects `https://push.lightstreamer.com` style — confirm this is what IG returns (not verified against live/demo yet; only tested with mocked HTTP)
- IG's `ControlAddress` field: may return just a hostname or a full URL depending on IG environment — `_ensure_scheme` handles both; confirm empirically
- IG Europe GmbH live account still pending (noted in CLAUDE.md) — live account needed before production use
