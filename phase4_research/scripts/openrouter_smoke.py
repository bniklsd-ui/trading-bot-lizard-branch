#!/usr/bin/env python3
"""Operator smoke test for the OpenAI-compatible client (M1 Step 10 → Phase 17 C-6).

**Not run in CI, not run by Claude Code.** Real network call, real (small) spend
against a real provider API key — the operator runs this by hand. Seed the key
once, then smoke-test a chosen model:

    python phase4_research/scripts/openrouter_smoke.py --store-key
    python phase4_research/scripts/openrouter_smoke.py --model <openrouter-model-id>

There is deliberately no baked-in default ``--model``: check
https://openrouter.ai/models for the current catalog and pick a large, current
open-weight instruct model at run time — a hardcoded id here would silently rot
as the catalog changes.

**Phase 17 C-6 (§15.4):** ``--provider <name>`` takes the endpoint, the keyring
namespace **and the request quirks** from the bot's own provider register
(``scheduler/llm_profiles.py``) — so the smoke sends **exactly** the payload the
bot would send (§15 T29: one mapping, bot and smoke). The explicit flags
(``--base-url`` / ``--key-service`` / ``--key-username``) stay available for a
one-off endpoint and are **mutually exclusive** with ``--provider``.

Builds one **real** research prompt via ``research.prompt.build_prompt`` (the
same pure function the live bot uses, pointed at a small synthetic single-epic
context — no P1/P2/P3 collaborators, no real broker/DB call), sends it through
``OpenAICompatLLMClient``, and runs whatever comes back through the real
``research.validator.validate_candidate`` — the same safety core that gates every
live pick. This proves the client's plumbing (prompt → provider → parse →
validator) genuinely round-trips, not just that the adapter's own mocked unit
tests pass.

Prints one PASS/FAIL line + model + token usage + finish_reason + latency to
stdout. The smoke prompt is synthetic — no account, no position, no market data.
"""

from __future__ import annotations

import argparse
import getpass
import logging
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import keyring

# Make the `research` package importable when run as a script (same bootstrap
# pattern as scripts/live_test.py).
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent  # phase4_research/
sys.path.insert(0, str(_PACKAGE_ROOT))

from research.llm_openai_compat import OpenAICompatLLMClient  # noqa: E402
from research.models import LLMResponseError, ResearchContext  # noqa: E402
from research.prompt import build_prompt  # noqa: E402
from research.validator import validate_candidate  # noqa: E402
from scheduler.llm_profiles import PROVIDERS, client_kwargs  # noqa: E402

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
log = logging.getLogger("phase4.openrouter_smoke")

_SMOKE_EPIC = "IX.D.DAX.IFMM.IP"
_THRESHOLD = 55.0
_ALLOWED_DIRECTIONS = ("BUY", "SELL")

# Phase 17 C-6: the providers the bot may talk to (the Anthropic-native client
# has its own smoke — ``scripts/live_test.py`` — so it is not in this list).
_SMOKE_PROVIDERS = sorted(name for name in PROVIDERS if name != "anthropic")


class _FixedTradeableBroker:
    """Fixed TRADEABLE / tight-spread price for the validator's live recheck.

    This script smoke-tests the prompt/schema/parse/validator round-trip
    through OpenRouter — it deliberately does **not** touch the real P1 broker
    (no live-market dependency; that path is already covered by
    ``scripts/live_test.py`` against the primary Anthropic client).
    """

    def get_price(self, epic: str) -> SimpleNamespace:
        return SimpleNamespace(ok=True, data={"spread_pct": 0.05, "market_status": "TRADEABLE"})


def _smoke_context() -> ResearchContext:
    """A minimal, deterministic single-epic context — no I/O, no AI."""
    return ResearchContext(
        tradeable_epics=[
            {
                "epic": _SMOKE_EPIC,
                "name": "Germany 40 Cash",
                "spread_pct": 0.05,
                "market_status": "TRADEABLE",
                "min_deal_size": 0.5,
            }
        ],
        recent_trades=[],
        recent_lessons=[],
        bot_score=50.0,
        risk_level="normal",
        brain_context=None,
        anchor_epic=_SMOKE_EPIC,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--model",
        default=None,
        help="Provider model id (check the provider's model list first).",
    )
    parser.add_argument(
        "--provider",
        default=None,
        choices=_SMOKE_PROVIDERS,
        help=(
            "Use the bot's own provider entry (endpoint + keyring namespace + request "
            f"quirks) from scheduler/llm_profiles.py. One of: {', '.join(_SMOKE_PROVIDERS)}."
        ),
    )
    parser.add_argument(
        "--base-url",
        default="https://openrouter.ai/api/v1",
        help="API base (without --provider). Default: OpenRouter.",
    )
    parser.add_argument(
        "--key-service",
        default="openrouter",
        help="OS-keyring service of the API key (without --provider). Default: openrouter.",
    )
    parser.add_argument(
        "--key-username",
        default="api_key",
        help="OS-keyring username of the API key (without --provider). Default: api_key.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1024,
        help="Token limit of the call. Default: 1024.",
    )
    parser.add_argument(
        "--timeout-s",
        type=float,
        default=60.0,
        help="Transport timeout in seconds. Default: 60.",
    )
    parser.add_argument(
        "--show-raw",
        action="store_true",
        help="Print the first 400 characters of the raw reply to stderr.",
    )
    parser.add_argument(
        "--store-key",
        action="store_true",
        help="Prompt for the OpenRouter API key and store it in the OS keyring "
        "(service=openrouter, username=api_key), then exit.",
    )
    args = parser.parse_args()

    if args.store_key:
        key = getpass.getpass("OpenRouter API key: ")
        keyring.set_password("openrouter", "api_key", key)
        print("Stored in the OS keyring. Re-run with --model <id> to smoke-test.")
        return 0

    if not args.model:
        parser.error("--model is required (see --help), or run --store-key first")

    if args.provider:
        # §15.4: the provider entry carries endpoint + keyring namespace + quirks —
        # the smoke sends exactly what the bot would send (T29).
        if args.base_url != "https://openrouter.ai/api/v1" or args.key_service != "openrouter" \
                or args.key_username != "api_key":
            parser.error(
                "--provider takes the endpoint and the keyring namespace from the "
                "provider register — do not combine it with --base-url/--key-service/"
                "--key-username"
            )
        client = OpenAICompatLLMClient(
            args.model,
            **client_kwargs(PROVIDERS[args.provider]),
            max_tokens=args.max_tokens,
            timeout_s=args.timeout_s,
        )
        provider_label = args.provider
    else:
        client = OpenAICompatLLMClient(
            args.model,
            base_url=args.base_url,
            api_key_service=args.key_service,
            api_key_username=args.key_username,
            max_tokens=args.max_tokens,
            timeout_s=args.timeout_s,
        )
        provider_label = "custom"

    context = _smoke_context()
    system, user, schema = build_prompt(context, _THRESHOLD, _ALLOWED_DIRECTIONS)

    started = time.monotonic()
    try:
        raw = client.ask_candidate(system, user, schema)
    except LLMResponseError as exc:
        latency = time.monotonic() - started
        print(
            f"FAIL provider={provider_label} model={args.model} "
            f"latency_s={latency:.2f} reason={exc}"
        )
        return 1
    latency = time.monotonic() - started

    if args.show_raw:
        # The first 400 characters of the raw reply — so a failed parse can be
        # judged by eye (think blocks, prose fences, empty content).
        print(f"--- raw reply (first 400 chars) ---\n{client.last_raw_text[:400]}", file=sys.stderr)

    result = validate_candidate(
        raw,
        context.tradeable_epics,
        _THRESHOLD,
        _ALLOWED_DIRECTIONS,
        _FixedTradeableBroker(),
        max_spread_pct=0.5,
        score_at_pick=context.bot_score,
        drift_at_pick=None,
    )

    usage = client.last_usage or {}
    tokens = f"in={usage.get('input_tokens', '?')} out={usage.get('output_tokens', '?')}"
    finish = f"finish_reason={client.last_finish_reason}"
    timing = f"latency_s={latency:.2f}"

    if not result.valid:
        print(
            f"FAIL provider={provider_label} model={args.model} tokens={tokens} "
            f"{finish} {timing} reason=validator reject: {result.rejected_reason}"
        )
        return 1

    verdict = "PASS (pick)" if result.candidate else "PASS (valid abstain)"
    print(
        f"{verdict} provider={provider_label} model={args.model} tokens={tokens} "
        f"{finish} {timing}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
