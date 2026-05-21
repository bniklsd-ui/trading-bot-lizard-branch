# IG Lightstreamer — Implementation Reference for Claude Code

> **This document exists because the previous implementation used a deprecated API
> that was decommissioned 12 days before this document was written.**
> Read the root cause first — it explains why the current code does not produce ticks.

---

## Rule 0 — Root Cause (read this first)

The `MARKET:{epic}` subscription and its `L1:{epic}` alias were **decommissioned
by IG on 8 May 2026**. Any code that subscribes using `MARKET:`, `L1:`, or
fields `BID / OFFER / UPDATE_TIME / MARKET_STATE` **will silently connect but
receive zero ticks**.

Source: https://labs.ig.com/streaming-api-reference.html
> ⚠ This subscription reaches end of life on 1 May 2026 and will be
> decommissioned on 8 May 2026. L1, an alias for MARKET, is also affected.
> Please migrate to the PRICE subscription before then.

---

## Rule 1 — The new subscription format

Everything that was `MARKET:{epic}` or `L1:{epic}` must become:

```
PRICE:{account_id}:{epic}
```

The `account_id` is the IG account identifier (e.g. `Z6BEGX`), not the username.
It is available as `adapter._account_id` after a successful `connect()`.

**Data adapter** also changes: `DEFAULT` → `Pricing`

### Updated TLCP subscription request

```
POST {control_address}/lightstreamer/control.txt
Content-Type: application/x-www-form-urlencoded

LS_session={session_id}
LS_op=add
LS_table=1
LS_id=PRICE:Z6BEGX:IX.D.DAX.IFMM.IP
LS_schema=BIDPRICE1 ASKPRICE1 TIMESTAMP NET_CHG NET_CHG_PCT DLG_FLAG DELAY
LS_mode=MERGE
LS_data_adapter=Pricing
```

### Old vs new — field mapping

| Old field (dead) | New field | Description |
|---|---|---|
| `BID` | `BIDPRICE1` | Top-of-ladder bid price |
| `OFFER` | `ASKPRICE1` | Top-of-ladder ask price |
| `UPDATE_TIME` | `TIMESTAMP` | UTC milliseconds since epoch |
| `MARKET_STATE` | `DLG_FLAG` | TRADEABLE, CLOSED, AUCTION, etc. |
| `CHANGE` | `NET_CHG` | Price change vs open |
| `CHANGE_PCT` | `NET_CHG_PCT` | Percentage change |
| `MARKET_DELAY` | `DELAY` | 1=delayed, 0=live |

### Parsing `TIMESTAMP`

`TIMESTAMP` is **UTC milliseconds since epoch** (integer string), not a time string.

```python
import datetime

def _timestamp_to_iso(ts_millis_str: str) -> str:
    if not ts_millis_str:
        return ""
    try:
        ms = int(ts_millis_str)
        dt = datetime.datetime.fromtimestamp(ms / 1000.0, tz=datetime.timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"
    except (ValueError, TypeError):
        return ts_millis_str
```

### Parsing `DLG_FLAG` → market status

`DLG_FLAG` is a string constant: `"TRADEABLE"`, `"CLOSED"`, `"AUCTION"`, etc.
Map directly to the existing `MarketStatus` type in `models.py`.

---

## Rule 2 — TLCP protocol version

The previous implementation used `TLCP-2.1.0`. IG's Go and Rust community
implementations use `TLCP-2.4.0.lightstreamer.com`.

```
LS_protocol=TLCP-2.4.0.lightstreamer.com
```

Change this in the `create_session` request body.

---

## Rule 3 — Connection parameters (auth format)

IG's official documentation is explicit:

| TLCP field | Value |
|---|---|
| `LS_user` | account_id (e.g. `Z6BEGX`) |
| `LS_password` | `CST-{cst_token}\|XST-{security_token}` |
| `LS_adapter_set` | `DEFAULT` |
| `LS_protocol` | `TLCP-2.4.0.lightstreamer.com` |

**Common mistake in forum code:** Putting the CST/XST in `LS_user` and the
REST password in `LS_password`. This connects but does not authenticate correctly.

---

## Rule 4 — POST body, not URL parameters

TLCP `create_session.txt` and `control.txt` parameters **must go in the POST
body**, not as URL query parameters.

```python
# CORRECT
response = requests.post(
    f"{endpoint}/lightstreamer/create_session.txt",
    data={                              # ← form-encoded body
        "LS_protocol": "TLCP-2.4.0.lightstreamer.com",
        "LS_user": account_id,
        "LS_password": f"CST-{cst}|XST-{security_token}",
        "LS_adapter_set": "DEFAULT",
    },
    stream=True,
)

# WRONG — will fail or get "password check failure"
response = requests.get(
    f"{endpoint}/lightstreamer/create_session.txt"
    f"?LS_user={account_id}&LS_password=CST-..."
)
```

---

## Rule 5 — ControlAddress handling

The `create_session.txt` response contains a `ControlAddress` line. This is the
host for subsequent `control.txt` calls (subscriptions, unsubscriptions).
It may differ from the main endpoint (IG uses load balancers).

```
OK
SessionId:S-abc123
ControlAddress:push-live-abc.marketdatasystems.com
KeepaliveMillis:5000
```

The `ControlAddress` may be a hostname only (no scheme, no path). Normalise it:

```python
def _build_control_url(control_address: str, scheme: str = "https") -> str:
    """Normalise ControlAddress to a full URL."""
    if control_address.startswith("http"):
        return control_address
    return f"{scheme}://{control_address}"

# Then use:
control_url = _build_control_url(control_address)
response = requests.post(f"{control_url}/lightstreamer/control.txt", data={...})
```

---

## Rule 6 — Streaming transport: HTTP vs WebSocket

The TLCP protocol works over **both** HTTP streaming and WebSocket.
Community implementations (Go, Rust) use WebSocket; the HTTP streaming approach
is functional but has more edge cases.

### HTTP streaming (current approach — fix in place)

```python
response = requests.post(
    f"{endpoint}/lightstreamer/bind_session.txt",
    data={"LS_session": session_id},
    stream=True,
    timeout=None,          # ← critical: no timeout on the stream itself
)
for line in response.iter_lines(decode_unicode=True):
    ...
```

`timeout=None` is required for the bind request. A finite timeout will kill
the stream mid-session. Use `timeout=(10, None)` if you want a connect timeout
only: `(connect_timeout_s, read_timeout_s)`.

### WebSocket alternative (more robust)

```python
import websocket  # pip install websocket-client

def _wss_endpoint(https_endpoint: str) -> str:
    return https_endpoint.replace("https://", "wss://").replace("http://", "ws://")

ws_url = f"{_wss_endpoint(endpoint)}/lightstreamer"
ws = websocket.create_connection(ws_url)

# TLCP frames are sent as text messages
ws.send(f"create_session\r\nLS_protocol=TLCP-2.4.0.lightstreamer.com\r\n"
        f"LS_user={account_id}\r\nLS_password=CST-{cst}|XST-{security_token}\r\n"
        f"LS_adapter_set=DEFAULT\r\n")
```

For the demo account the WebSocket URL is:
```
wss://demo-apd.marketdatasystems.com/lightstreamer
```

---

## Rule 7 — LOOP rebind

When the server sends a `LOOP` response in the stream, the client must
reconnect by calling `bind_session.txt` again with the same session ID.
**Do not create a new session** — just rebind.

```python
for line in response.iter_lines(decode_unicode=True):
    if line.startswith("LOOP"):
        # rebind: call bind_session.txt again
        self._bind_and_read(session_id)
        return
```

If rebind fails because the CST/XST tokens have expired (401 response), call
`broker.connect()` to re-authenticate, then create a new LS session with
the fresh tokens.

---

## Rule 8 — Threading

IG's documentation states explicitly:
> A Lightstreamer connection needs an active thread to stream data.
> Creating multiple Lightstreamer connections on the main thread may cause
> connections to drop intermittently.

The reader loop **must** run in a daemon thread separate from the main thread.
`start()` → `threading.Thread(target=self._reader_loop, daemon=True).start()`.
Never call `bind_session` from the main thread.

---

## Rule 9 — Known IG-specific URLs

These are the hardcoded fallbacks if `lightstreamerEndpoint` is empty or
returns an unexpected format:

| Environment | URL |
|---|---|
| Demo | `https://demo-apd.marketdatasystems.com` |
| Live | `https://apd.marketdatasystems.com` |

The `lightstreamerEndpoint` field from `POST /session` should return the correct
URL and should always be preferred over these hardcoded values. Print it during
`test_lightstreamer.py` to verify.

---

## Rule 10 — Subscription limit

IG allows a maximum of **40 market items** per connection. The bot subscribes
to one epic at a time — well within limit. Do not create multiple connections
to work around this; IG will revoke API permissions.

---

## Complete three-patch summary

These are the three specific changes needed in the existing implementation:

### Patch 1 — `_send_subscribe()` in `ig_lightstreamer.py`

```python
# BEFORE (dead)
"LS_id": f"L1:{epic}",
"LS_schema": "BID OFFER UPDATE_TIME HIGH LOW",
"LS_data_adapter": "DEFAULT",

# AFTER (correct)
"LS_id": f"PRICE:{self._account_id}:{epic}",
"LS_schema": "BIDPRICE1 ASKPRICE1 TIMESTAMP NET_CHG NET_CHG_PCT DLG_FLAG DELAY",
"LS_data_adapter": "Pricing",
```

### Patch 2 — `_create_ls_session()` in `ig_lightstreamer.py`

```python
# BEFORE
"LS_protocol": "TLCP-2.1.0",

# AFTER
"LS_protocol": "TLCP-2.4.0.lightstreamer.com",
```

### Patch 3 — `_handle_update()` in `ig_lightstreamer.py`

```python
# BEFORE — fields by position: [0]=BID [1]=OFFER [2]=UPDATE_TIME
bid = fields[0]
ask = fields[1]
timestamp = fields[2]

# AFTER — fields by position match BIDPRICE1 ASKPRICE1 TIMESTAMP ...
# Schema: BIDPRICE1 ASKPRICE1 TIMESTAMP NET_CHG NET_CHG_PCT DLG_FLAG DELAY
bid_str   = fields[0] if len(fields) > 0 else ""
ask_str   = fields[1] if len(fields) > 1 else ""
ts_str    = fields[2] if len(fields) > 2 else ""

# Empty string means "unchanged since last update" in MERGE mode
bid = float(bid_str) if bid_str else self._last_bid.get(item_id, 0.0)
ask = float(ask_str) if ask_str else self._last_ask.get(item_id, 0.0)
timestamp = _timestamp_to_iso(ts_str) if ts_str else _utc_now_iso()

# Cache last known values for MERGE-mode empty fields
self._last_bid[item_id] = bid
self._last_ask[item_id] = ask
```

**Why caching matters:** In MERGE mode, IG only sends changed fields.
If bid changes but ask doesn't, `fields[1]` will be an empty string.
The implementation must cache the last known value per item.

---

## Fallback option — official Lightstreamer Python SDK

If raw TLCP continues to have issues after the three patches, switch to the
official SDK. It handles reconnects, LOOP, WebSocket/HTTP, and MERGE caching
automatically.

```bash
pip install lightstreamer-client-python  # version 2.2.0+
```

```python
from lightstreamer.client import LightstreamerClient, Subscription

client = LightstreamerClient(lightstreamer_endpoint, "DEFAULT")
client.connectionDetails.setUser(account_id)
client.connectionDetails.setPassword(f"CST-{cst}|XST-{security_token}")
client.connect()

sub = Subscription(
    "MERGE",
    [f"PRICE:{account_id}:{epic}"],
    ["BIDPRICE1", "ASKPRICE1", "TIMESTAMP"],
)
sub.setDataAdapter("Pricing")
sub.addListener(my_listener)
client.subscribe(sub)
```

The `lightstreamer-client-python` package is not a broker library — it is a
communication protocol library, analogous to `requests` for HTTP. It does not
violate the "no third-party broker libraries" rule in `CLAUDE.md`.

Add to `requirements.txt` only if switching to this option:
```
lightstreamer-client-python>=2.2.0
```

---

## Verification

After applying the three patches:

```bash
# Run during market hours: Mon–Fri 08:00–22:30 CET
python scripts/test_lightstreamer.py --ticks 3 --timeout 30
```

Expected successful output:
```
[1] connect (REST)
  [OK ] account=Z6BEGX
  [OK ] lightstreamer_endpoint=https://demo-apd.marketdatasystems.com

[2] create IGLightstreamerClient
  [OK ] stream client created

[3] subscribe to IX.D.DAX.IFMM.IP

[4] start stream — waiting up to 30s for 3 ticks...
  [TICK #01] bid=24615.0  ask=24617.0  ts=2026-05-20T09:42:01.123Z  (+1.2s)
  [TICK #02] bid=24614.5  ask=24616.5  ts=2026-05-20T09:42:06.451Z  (+6.5s)
  [TICK #03] bid=24615.8  ask=24617.8  ts=2026-05-20T09:42:11.200Z  (+11.2s)

result: PASS  (3 ticks received in 11.2s)
```

If `[TICK]` lines appear but bid/ask are `0.0`, the field names in `LS_schema`
are still wrong. Double-check Patch 1.

If no ticks at all despite `SUBOK` in logs:
1. Verify `LS_data_adapter=Pricing` (not `DEFAULT`)
2. Verify item is `PRICE:{account_id}:{epic}` (not `MARKET:` or `L1:`)
3. Check that the market is open (run during trading hours)
