#!/usr/bin/env python3
"""Store the bake-off's separate Anthropic API key into the OS keyring.

Same strategy as the bot's own `phase1_broker_wrapper/scripts/store_credential.py`
(getpass, no shell history, no file, no AI-visible input) — but its own dedicated keyring
service, deliberately independent of `broker_wrapper.credentials` (SERVICE_NAME="tradingbot",
the LIVE bot's namespace) and of the fork's neutralized service ("trading-bot-bakeoff-void",
which exists to make the live bot's credentials *unreachable* from inside the fork, M1-D8).
This key is a third, separate concern: the bake-off tool's own Anthropic key, used only to
launch the `claude`/`opencode` subprocesses in `harness_bakeoff.py`. Three distinct keyring
namespaces, none of which can cross-contaminate.

Usage:
    python meta_m1_harness/bakeoff/store_bakeoff_key.py
    python meta_m1_harness/bakeoff/store_bakeoff_key.py --status
    python meta_m1_harness/bakeoff/store_bakeoff_key.py --delete
"""

from __future__ import annotations

import argparse
import getpass

import keyring
from keyring.errors import PasswordDeleteError

SERVICE_NAME = "trading-bot-bakeoff-runner"
USERNAME = "anthropic_api_key"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--status", action="store_true", help="show whether the key is set (no value shown)"
    )
    parser.add_argument("--delete", action="store_true", help="remove the stored key")
    args = parser.parse_args()

    if args.status:
        is_set = keyring.get_password(SERVICE_NAME, USERNAME) is not None
        print(f"{'✓' if is_set else '✗'}  {SERVICE_NAME}/{USERNAME}")
        return 0

    if args.delete:
        try:
            keyring.delete_password(SERVICE_NAME, USERNAME)
        except PasswordDeleteError:
            pass  # already absent — idempotent, same as broker_wrapper.credentials
        print(f"deleted: {SERVICE_NAME}/{USERNAME}")
        return 0

    value = getpass.getpass("Enter the separate bake-off Anthropic API key (input hidden): ")
    if not value:
        print("empty value — aborting")
        return 1
    confirm = getpass.getpass("Confirm: ")
    if value != confirm:
        print("values do not match — aborting")
        return 1

    keyring.set_password(SERVICE_NAME, USERNAME, value)
    print(f"stored: {SERVICE_NAME}/{USERNAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
