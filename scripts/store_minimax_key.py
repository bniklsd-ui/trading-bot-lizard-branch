#!/usr/bin/env python3
"""Store an LLM API key into the OS keyring (name kept for history).

Same strategy as `meta_m1_harness/bakeoff/store_bakeoff_key.py` (getpass, no shell history,
no file, no AI-visible input) — its own dedicated keyring service, deliberately independent
of `broker_wrapper.credentials` (SERVICE_NAME="tradingbot", the LIVE bot's namespace), the
bake-off runner's key ("trading-bot-bakeoff-runner") and the fork's neutralized service
("trading-bot-bakeoff-void"). This is the fourth, separate concern: the key used only by
`scripts/claude-minimax` to run Claude Code against MiniMax M3 for cost reasons
(Phase 13 Step A0.0). Does not change which model the bot itself calls.

**Phase 17 C-6 (generic seeder):** `--service` / `--username` make the same script store
any provider key the bot uses. The bot's own providers each have their **own** keyring
namespace (never `tradingbot`) — see `phase8_scheduler/scheduler/llm_profiles.py`:

    python scripts/store_minimax_key.py --service trading-bot-zai-bot --username api_key
    python scripts/store_minimax_key.py --service trading-bot-minimax-bot --username api_key

The default (`trading-bot-minimax` / `minimax_api_key`) is the **dev-harness** key and stays
untouched by the bot (isolation pattern M1).

Usage:
    python scripts/store_minimax_key.py
    python scripts/store_minimax_key.py --status
    python scripts/store_minimax_key.py --delete
    python scripts/store_minimax_key.py --service <service> --username <username> [--status|--delete]
"""

from __future__ import annotations

import argparse
import getpass

import keyring
from keyring.errors import PasswordDeleteError

SERVICE_NAME = "trading-bot-minimax"
USERNAME = "minimax_api_key"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--status", action="store_true", help="show whether the key is set (no value shown)"
    )
    parser.add_argument("--delete", action="store_true", help="remove the stored key")
    parser.add_argument(
        "--service",
        default=SERVICE_NAME,
        help=(
            "OS-keyring service (namespace) of the key. Default: the dev-harness "
            f"namespace {SERVICE_NAME!r}. The bot's providers use their own namespaces "
            "(trading-bot-zai-bot, trading-bot-minimax-bot, …)."
        ),
    )
    parser.add_argument(
        "--username",
        default=USERNAME,
        help=f"OS-keyring username of the key. Default: {USERNAME!r}.",
    )
    args = parser.parse_args(argv)

    if args.status:
        is_set = keyring.get_password(args.service, args.username) is not None
        print(f"{'✓' if is_set else '✗'}  {args.service}/{args.username}")
        return 0

    if args.delete:
        try:
            keyring.delete_password(args.service, args.username)
        except PasswordDeleteError:
            pass  # already absent — idempotent, same as broker_wrapper.credentials
        print(f"deleted: {args.service}/{args.username}")
        return 0

    value = getpass.getpass(f"Enter the API key for {args.service}/{args.username} (input hidden): ")
    if not value:
        print("empty value — aborting")
        return 1
    confirm = getpass.getpass("Confirm: ")
    if value != confirm:
        print("values do not match — aborting")
        return 1

    keyring.set_password(args.service, args.username, value)
    print(f"stored: {args.service}/{args.username}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
