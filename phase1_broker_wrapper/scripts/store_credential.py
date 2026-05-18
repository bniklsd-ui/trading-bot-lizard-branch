#!/usr/bin/env python3
"""Store a credential into the OS keyring.

Usage:
    python scripts/store_credential.py ig_username
    python scripts/store_credential.py ig_password
    python scripts/store_credential.py ig_api_key
    python scripts/store_credential.py ig_account_id

The value is read via getpass (no echo, no shell history). Any AI agent
helping you build this bot never sees the input or stored value.

To list which credentials are set without revealing values:
    python scripts/store_credential.py --status

To delete:
    python scripts/store_credential.py --delete ig_password
"""

from __future__ import annotations

import argparse
import getpass
import sys

# Allow running from project root: python scripts/store_credential.py
sys.path.insert(0, ".")

from broker_wrapper.credentials import (  # noqa: E402
    store_credential, delete_credential, check_credentials,
    IG_USERNAME, IG_PASSWORD, IG_API_KEY, IG_ACCOUNT_ID,
    IG_DEMO_USERNAME, IG_DEMO_PASSWORD, IG_DEMO_API_KEY, IG_DEMO_ACCOUNT_ID,
)


KNOWN = [
    IG_USERNAME, IG_PASSWORD, IG_API_KEY, IG_ACCOUNT_ID,
    IG_DEMO_USERNAME, IG_DEMO_PASSWORD, IG_DEMO_API_KEY, IG_DEMO_ACCOUNT_ID,
]


def main() -> int:
    p = argparse.ArgumentParser(description="Manage broker credentials in OS keyring.")
    p.add_argument("name", nargs="?", help="credential key (see --status for list)")
    p.add_argument("--status", action="store_true",
                   help="show which credentials are set (no values shown)")
    p.add_argument("--delete", metavar="NAME",
                   help="remove a credential from the keyring")
    p.add_argument("--list", action="store_true",
                   help="show known credential names")
    args = p.parse_args()

    if args.list:
        print("Known credential keys:")
        for k in KNOWN:
            print(f"  {k}")
        return 0

    if args.status:
        results = check_credentials(KNOWN)
        print("Credential status (✓ = set, ✗ = not set):")
        for name, ok in results.items():
            mark = "✓" if ok else "✗"
            print(f"  {mark}  {name}")
        return 0

    if args.delete:
        if args.delete not in KNOWN:
            print(f"warn: '{args.delete}' is not a known credential name", file=sys.stderr)
        delete_credential(args.delete)
        print(f"deleted: {args.delete}")
        return 0

    if not args.name:
        p.print_help()
        return 1

    if args.name not in KNOWN:
        print(f"warn: '{args.name}' is not in the known list. Proceeding anyway.",
              file=sys.stderr)

    prompt = f"Enter value for {args.name} (input hidden): "
    value = getpass.getpass(prompt)
    if not value:
        print("empty value — aborting", file=sys.stderr)
        return 1
    confirm = getpass.getpass("Confirm: ")
    if value != confirm:
        print("values do not match — aborting", file=sys.stderr)
        return 1

    store_credential(args.name, value)
    print(f"stored: {args.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
