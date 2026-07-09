#!/usr/bin/env python3
"""Operator smoke test for the cold OpenAI-compatible fallback (M1 Step 10).

**Not run in CI, not run by Claude Code.** Real network call, real (small) spend
against a real OpenRouter API key — the operator runs this by hand. Seed the key
once, then smoke-test a chosen model:

    python phase4_research/scripts/openrouter_smoke.py --store-key
    python phase4_research/scripts/openrouter_smoke.py --model <openrouter-model-id>

There is deliberately no baked-in default ``--model``: check
https://openrouter.ai/models for the current catalog and pick a large, current
open-weight instruct model at run time — a hardcoded id here would silently rot
as the catalog changes.

Builds one **real** research prompt via ``research.prompt.build_prompt`` (the
same pure function the live bot uses, pointed at a small synthetic single-epic
context — no P1/P2/P3 collaborators, no real broker/DB call), sends it through
``OpenAICompatLLMClient`` to OpenRouter, and runs whatever comes back through
the real ``research.validator.validate_candidate`` — the same safety core that
gates every live pick. This proves the fallback's plumbing (prompt → OpenRouter
→ parse → validator) genuinely round-trips, not just that the adapter's own
mocked unit tests pass.

Prints one PASS/FAIL line + model + token usage to stdout. The adapter stays
**cold** after this — nothing here, or anywhere else, wires it into any live
path (``scripts/wiring.py`` is untouched).
"""

from __future__ import annotations

import argparse
import getpass
import logging
import sys
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

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
log = logging.getLogger("phase4.openrouter_smoke")

_SMOKE_EPIC = "IX.D.DAX.IFMM.IP"
_THRESHOLD = 55.0
_ALLOWED_DIRECTIONS = ("BUY", "SELL")


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
        help="OpenRouter model id (check https://openrouter.ai/models first).",
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

    client = OpenAICompatLLMClient(model=args.model)
    context = _smoke_context()
    system, user, schema = build_prompt(context, _THRESHOLD, _ALLOWED_DIRECTIONS)

    try:
        raw = client.ask_candidate(system, user, schema)
    except LLMResponseError as exc:
        print(f"FAIL model={args.model} reason={exc}")
        return 1

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

    if not result.valid:
        print(f"FAIL model={args.model} tokens={tokens} reason=validator reject: {result.rejected_reason}")
        return 1

    verdict = "PASS (pick)" if result.candidate else "PASS (valid abstain)"
    print(f"{verdict} model={args.model} tokens={tokens}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
