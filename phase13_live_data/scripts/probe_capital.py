#!/usr/bin/env python3
"""Phase 13 §6 C1 — Probe B (Capital.com Demo API).

Hybrid-Entscheidung 2026-08-19 (Session 11): zuerst Capital.com, dann
Dukascopy als Fallback. Dieser Probe ist der **Gating-Live-Check** für
Pfad B — analog zu ``probe_chart_stream.py`` für Block B0.

Capital.com ist eine Broker-API (wie IG, mit API-Key → Session → CST/
X-SECURITY-TOKEN). Die Demo-API ist **kostenlos**, das Wochenkontingent
ist unabhängig vom IG-Kontingent. Die hier verifizierte Frage: liefert
die Demo-API 1-Minuten-Bars für Germany 40 / France 40 / Spain 35 —
und wie weit reicht die Historie zurück?

Wird gebraucht für: ``live_data/backfill.py`` (§6 C1, vier Regeln,
Fold-in-Checkliste 4 Stellen). Wird **nicht** gebraucht, wenn der
Operator Pfad B abbricht und auf Dukascopy (Pfad C) wechselt.

Usage:
    python phase13_live_data/scripts/probe_capital.py
    python phase13_live_data/scripts/probe_capital.py --indices "Germany 40,UK 100"
    python phase13_live_data/scripts/probe_capital.py --timeout 30
    python phase13_live_data/scripts/probe_capital.py --debug

Exit codes:
    0  YES    — alle Indizes liefern MINUTE-Bars
    1  NO     — Auth OK, aber kein Index liefert Bars
    2  PARTIAL— ≥ 1 Index liefert, andere nicht
    3  AUTH   — Keyring/Credentials/Verbindung fehlen

Output: stderr = menschliche Erzählung, stdout = JSON Envelope
(Repo-Konvention; siehe ``probe_chart_stream.py``). Kosten: 0
(Demo-Konto, keine Real-Orders).

Live, Netz, Keyring — operator-run, **nicht** in Tests
(Repo-Konvention; ``scripts/wiring.py`` ebenfalls operator-run).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
# Default to the DEMO base URL — Capital.com maintains a separate
# demo endpoint (``demo-api-capital.backend-capital.com``) that does
# NOT accept live-URL credentials and vice versa. Operators with a
# live API key must pass --base explicitly.
_DEFAULT_BASE = "https://demo-api-capital.backend-capital.com"
_DEFAULT_INDICES = ["Germany 40", "France 40", "Spain 35"]
_KEYRING_SERVICE = "trading-bot-capital"


def _eprint(message: str = "") -> None:
    print(message, file=sys.stderr)


def _read_field(field: str) -> str:
    """Read one Capital.com credential field from the project keyring.

    Uses raw ``keyring`` (not ``broker_wrapper.credentials``) because
    that helper is hardcoded to ``SERVICE_NAME='tradingbot'`` for the
    live-bot IG namespace. Capital.com needs its own service prefix,
    same pattern as ``store_minimax_key.py`` (which uses raw keyring
    for the same reason).
    """
    import keyring
    from keyring.errors import KeyringError
    value = keyring.get_password(_KEYRING_SERVICE, field)
    if not value:
        from broker_wrapper.exceptions import CredentialNotFoundError
        raise CredentialNotFoundError(
            f"Capital.com credential '{_KEYRING_SERVICE}/{field}' not in keyring — "
            f"run `python scripts/store_capital_key.py` first"
        )
    return value


def _read_creds() -> tuple[str, str, str]:
    """Read (identifier, password, api_key) from the project keyring."""
    return (
        _read_field("identifier"),
        _read_field("password"),
        _read_field("api_key"),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--base", default=_DEFAULT_BASE,
                        help=f"API base URL (default: {_DEFAULT_BASE})")
    parser.add_argument("--indices", default=",".join(_DEFAULT_INDICES),
                        help="comma-separated index names to probe")
    parser.add_argument("--timeout", type=int, default=30,
                        help="per-request timeout in seconds")
    parser.add_argument("--history-hours", type=int, default=1,
                        help="how far back to probe the history window (default 1h)")
    parser.add_argument("--keyring-service", default=_KEYRING_SERVICE,
                        help=f"keyring service prefix (default: {_KEYRING_SERVICE})")
    parser.add_argument("--debug", action="store_true",
                        help="verbose HTTP logging")
    args = parser.parse_args(argv)

    sys.path.insert(0, str(_REPO_ROOT))

    # ---------- credentials ----------
    try:
        identifier, password, api_key = _read_creds()
    except Exception as exc:
        _eprint(f"[probe_capital] keyring read failed: {exc}")
        print(json.dumps({
            "ok": False, "error": "keyring_unavailable",
            "service": _KEYRING_SERVICE,
            "hint": "seed via `python scripts/store_capital_key.py`",
        }))
        return 3

    import requests

    # Capital.com's documented session-auth contract (verified against
    # the official Swagger spec at https://capital.com/api, fetched
    # 2026-08-19):
    #
    #   POST /api/v1/session
    #   Header: X-CAP-API-KEY: <api_key>
    #   Body:   { "identifier":      <login_email>,
    #             "password":        <API_KEY_CUSTOM_PASSWORD>,
    #             "encryptedPassword": false }
    #
    # Two non-obvious facts the docs spell out but the obvious guessing
    # did not find:
    #   (a) The API key goes in the X-CAP-API-KEY HEADER, not the JSON
    #       body — the error code "error.null.api.key" refers to the
    #       header being absent, not to a JSON body field.
    #   (b) The "password" body field is the **API key's custom password**
    #       (set during key generation in Settings > API integrations),
    #       NOT the user's account password. Distinct values, distinct
    #       semantics — confirmed by the docs' own FAQ section.
    # Endpoint rate limit: 1 request per second per API key.
    auth_headers = {
        "X-CAP-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    auth_body = {
        "identifier": identifier,
        "password": password,
        "encryptedPassword": False,
    }

    if args.debug:
        redacted_headers = {
            "X-CAP-API-KEY": f"***({len(api_key)}c)",
            "Content-Type": "application/json",
        }
        redacted_body = {
            "identifier": f"***({len(identifier)}c)",
            "password":   f"***({len(password)}c)",
            "encryptedPassword": False,
        }
        _eprint(f"[probe_capital] debug auth headers: {json.dumps(redacted_headers)}")
        _eprint(f"[probe_capital] debug auth body: {json.dumps(redacted_body)}")

    _eprint(f"[probe_capital] auth POST {args.base}/api/v1/session")
    try:
        auth_resp = requests.post(
            f"{args.base}/api/v1/session",
            json=auth_body,
            headers=auth_headers,
            timeout=args.timeout,
        )
    except requests.RequestException as exc:
        _eprint(f"[probe_capital] auth request failed: {exc}")
        print(json.dumps({"ok": False, "error": f"connection_failed: {exc}"}))
        return 1

    if auth_resp.status_code != 200:
        snippet = (auth_resp.text or "")[:300]
        _eprint(f"[probe_capital] auth HTTP {auth_resp.status_code}: {snippet}")
        # Capture full response headers + body for diagnostics — the
        # errorCode alone is often ambiguous (e.g. error.null.accountId
        # can mean "live key against demo URL" OR "no demo accounts").
        full_body: dict | str = snippet
        try:
            full_body = auth_resp.json()
        except ValueError:
            pass
        # Differentiated hint per common error code.
        hint = ""
        if auth_resp.status_code == 429:
            hint = ("429 Too Many Requests — Capital.com's /session endpoint "
                    "is rate-limited to 1 request per second per API key; "
                    "wait ~5 s and re-run")
        elif "invalid.api.key" in snippet or "invalid.api_key" in snippet:
            hint = ("API key rejected — verify the key is active in "
                    "Settings > API integrations and not paused/expired")
        elif "null.accountId" in snippet:
            hint = (
                "401 + error.null.accountId — credentials are accepted "
                "but no account is bound to this API key. Two likely "
                "causes (Capital.com docs FAQ §8.5 explicit, Swagger "
                "§Generate-API-key): "
                "(1) the API key was generated on the LIVE platform and "
                "you're calling the DEMO URL — Capital.com issues separate "
                "API keys per account type; login to your DEMO account at "
                "https://demo.capital.com/, navigate to Settings > API "
                "integrations, generate a separate demo API key with its "
                "OWN custom password, and re-seed; "
                "(2) the account's status is SUSPENDED or BLOCKED — check "
                "your account dashboard"
            )
        elif "credentials.invalid" in snippet or "error.invalid" in snippet:
            hint = ("Credentials rejected — verify (a) identifier is your "
                    "login EMAIL (not username), (b) password is the "
                    "**API-key CUSTOM password** set during key generation "
                    "(NOT your account login password)")
        else:
            hint = "see Capital.com Swagger docs at https://capital.com/api"
        print(json.dumps({
            "ok": False,
            "error": f"auth_failed_{auth_resp.status_code}",
            "response_snippet": snippet,
            "response_body": full_body,
            "response_headers": dict(auth_resp.headers),
            "hint": hint,
        }))
        return 3

    cst = auth_resp.headers.get("CST", "")
    sec_token = auth_resp.headers.get("X-SECURITY-TOKEN", "")
    if not cst or not sec_token:
        _eprint("[probe_capital] auth response missing CST/X-SECURITY-TOKEN")
        print(json.dumps({"ok": False, "error": "auth_response_missing_tokens",
                          "headers_seen": list(auth_resp.headers.keys())}))
        return 3

    # Refresh the auth headers with the session tokens for subsequent
    # requests — X-CAP-API-KEY is for the initial auth only; everything
    # after uses CST + X-SECURITY-TOKEN.
    session_headers = {
        "CST": cst,
        "X-SECURITY-TOKEN": sec_token,
        "Content-Type": "application/json",
    }

    # Capital.com returns the account info in the response body — extract
    # the account type to verify we're on a demo account, not a live one.
    try:
        body = auth_resp.json() if auth_resp.text else {}
    except ValueError:
        body = {}
    account_type = "?"
    for acct in (body.get("accounts") or []):
        if acct.get("preferred"):
            account_type = acct.get("accountType", "?")
            break
    _eprint(f"[probe_capital] auth OK, account_type={account_type}")

    # ---------- per-index probe ----------
    indices = [s.strip() for s in args.indices.split(",") if s.strip()]
    # Capital.com's documented price-endpoint date format is
    # ``YYYY-MM-DDTHH:MM:SS`` — NO 'Z' suffix, NO milliseconds (per the
    # Swagger example for the activity-history endpoint, same convention
    # applied to the prices endpoint as confirmed empirically 2026-08-19:
    # ``error.invalid.from`` is returned when 'Z' is present). Their
    # parser is strict.
    now = datetime.now(timezone.utc)
    from_dt = (now - timedelta(hours=args.history_hours)).strftime("%Y-%m-%dT%H:%M:%S")
    to_dt = now.strftime("%Y-%m-%dT%H:%M:%S")
    _eprint(f"[probe_capital] probing {len(indices)} indices, window {from_dt} → {to_dt}")

    results: dict[str, dict] = {}
    for index_name in indices:
        _eprint(f"[probe_capital] searching {index_name!r} ...")
        try:
            search_resp = requests.get(
                f"{args.base}/api/v1/markets",
                params={"searchTerm": index_name},
                headers=session_headers,
                timeout=args.timeout,
            )
        except requests.RequestException as exc:
            results[index_name] = {"found": False, "error": f"search_failed: {exc}"}
            continue

        if search_resp.status_code != 200:
            results[index_name] = {"found": False,
                                   "error": f"search_http_{search_resp.status_code}"}
            continue

        try:
            markets = (search_resp.json() or {}).get("markets") or []
        except ValueError as exc:
            results[index_name] = {"found": False, "error": f"search_parse: {exc}"}
            continue

        # Prefer CFD indices; if multiple match, take the first one with
        # "CFD" in the type or name (the index CFDs are the rollable ones
        # we want for archive backfill).
        candidates = [
            m for m in markets
            if m.get("instrumentName") == index_name
            and "CFD" in (m.get("instrumentType") or "").upper()
        ]
        if not candidates:
            candidates = [m for m in markets if m.get("instrumentName") == index_name]
        if not candidates:
            results[index_name] = {
                "found": False,
                "error": "no_exact_name_match",
                "search_returned": [m.get("instrumentName") for m in markets[:5]],
            }
            continue

        epic = candidates[0].get("epic") or ""
        if not epic:
            results[index_name] = {"found": False, "error": "no_epic_in_match"}
            continue

        _eprint(f"[probe_capital] {index_name!r} → epic={epic}, fetching MINUTE bars ...")
        try:
            price_resp = requests.get(
                f"{args.base}/api/v1/prices/{epic}",
                params={"resolution": "MINUTE", "from": from_dt, "to": to_dt, "max": 1000},
                headers=session_headers,
                timeout=args.timeout,
            )
        except requests.RequestException as exc:
            results[index_name] = {"found": True, "epic": epic,
                                   "error": f"price_failed: {exc}"}
            continue

        if price_resp.status_code != 200:
            results[index_name] = {
                "found": True, "epic": epic,
                "error": f"price_http_{price_resp.status_code}",
                "snippet": (price_resp.text or "")[:200],
            }
            continue

        try:
            prices = (price_resp.json() or {}).get("prices") or []
        except ValueError as exc:
            results[index_name] = {"found": True, "epic": epic,
                                   "error": f"price_parse: {exc}"}
            continue

        first_ts = prices[0].get("snapshotTime") if prices else None
        last_ts = prices[-1].get("snapshotTime") if prices else None
        results[index_name] = {
            "found": True,
            "epic": epic,
            "resolution": "MINUTE",
            "bars_received": len(prices),
            "first_bar_ts": first_ts,
            "last_bar_ts": last_ts,
            "window_requested": {"from": from_dt, "to": to_dt},
        }

    # ---------- verdict ----------
    found_with_bars = [
        name for name, r in results.items()
        if r.get("found") and r.get("bars_received", 0) > 0 and "error" not in r
    ]
    found_count = len(found_with_bars)
    payload = {
        "ok": found_count == len(indices),
        "account_type": account_type,
        "found_count": found_count,
        "total_count": len(indices),
        "found_with_bars": found_with_bars,
        "results": results,
        "next_step_hint": (
            "Capital.com usable — build live_data/backfill.py for path B"
            if found_count == len(indices) else
            "PARTIAL — Capital.com covers some indices; "
            "build live_data/backfill.py with source='capital', "
            "remaining indices via Dukascopy (path C)"
            if found_count > 0 else
            "NO — fall back to Dukascopy (path C, requires Nikinger "
            "ToS-exception confirmation)"
        ),
    }
    print(json.dumps(payload, indent=2, default=str))

    if found_count == 0:
        return 1
    if found_count == len(indices):
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
