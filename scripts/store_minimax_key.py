#!/usr/bin/env python3
"""Store the `claude-minimax` wrapper's MiniMax API key into the OS keyring.

Same strategy as `meta_m1_harness/bakeoff/store_bakeoff_key.py` (getpass, no shell history,
no file, no AI-visible input) — its own dedicated keyring service, deliberately independent
of `broker_wrapper.credentials` (SERVICE_NAME="tradingbot", the LIVE bot's namespace), the
bake-off runner's key ("trading-bot-bakeoff-runner") and the fork's neutralized service
("trading-bot-bakeoff-void"). This is the fourth, separate concern: the key used only by
`scripts/claude-minimax` to run Claude Code against MiniMax M3 for cost reasons
(Phase 13 Step A0.0). Does not change which model the bot itself calls.

Usage:
    python scripts/store_minimax_key.py
    python scripts/store_minimax_key.py --status
    python scripts/store_minimax_key.py --delete
"""

from __future__ import annotations

import argparse
import getpass

import keyring
from keyring.errors import PasswordDeleteError

SERVICE_NAME = "trading-bot-minimax"
USERNAME = "minimax_api_key"


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

    value = getpass.getpass("Enter the MiniMax API key (input hidden): ")
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
