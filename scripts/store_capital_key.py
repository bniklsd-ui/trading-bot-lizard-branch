#!/usr/bin/env python3
"""Store the Capital.com Demo-API credentials into the OS keyring.

Same strategy as ``scripts/store_minimax_key.py`` and
``meta_m1_harness/bakeoff/store_bakeoff_key.py`` (getpass, no shell
history, no file, no AI-visible input) — its own dedicated keyring
service namespace (``trading-bot-capital.*``), deliberately independent
of the four other namespaces
(``tradingbot`` = live bot,
``trading-bot-bakeoff-runner`` = M1,
``trading-bot-bakeoff-void`` = M1 fork,
``trading-bot-minimax`` = Claude-Code-harness key).

Phase 13 §6 C1 (Session 11 hybrid decision 2026-08-19): Path B's
probe reads three keys — ``identifier``, ``password``, ``api_key`` —
all under the same service prefix. Hard Rule 1 holds: no credential
in any file.

Usage:
    python scripts/store_capital_key.py
    python scripts/store_capital_key.py --status
    python scripts/store_capital_key.py --delete
"""

from __future__ import annotations

import argparse
import getpass

import keyring
from keyring.errors import PasswordDeleteError

SERVICE_NAME = "trading-bot-capital"
FIELDS = ("identifier", "password", "api_key")


def _is_set(field: str) -> bool:
    return keyring.get_password(SERVICE_NAME, field) is not None


def _delete(field: str) -> None:
    try:
        keyring.delete_password(SERVICE_NAME, field)
    except PasswordDeleteError:
        pass  # idempotent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--status", action="store_true",
        help="show which fields are set (no values shown)",
    )
    parser.add_argument(
        "--delete", action="store_true",
        help="remove all stored credentials (idempotent)",
    )
    args = parser.parse_args()

    if args.status:
        for f in FIELDS:
            print(f"{'✓' if _is_set(f) else '✗'}  {SERVICE_NAME}/{f}")
        return 0

    if args.delete:
        for f in FIELDS:
            _delete(f)
        print(f"deleted: {SERVICE_NAME}/{{{', '.join(FIELDS)}}}")
        return 0

    # Seed each field. Prompt three times; abort on any empty input.
    for f in FIELDS:
        existing = "✓ set" if _is_set(f) else "✗ not set"
        prompt = f"Enter Capital.com {f} ({existing}, input hidden): "
        value = getpass.getpass(prompt)
        if not value:
            print(f"empty {f} — aborting (no partial writes)")
            return 1
        keyring.set_password(SERVICE_NAME, f, value)
        print(f"stored: {SERVICE_NAME}/{f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
