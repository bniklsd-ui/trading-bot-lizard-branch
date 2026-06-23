"""Dependency wiring for Phase 7 — build a real :class:`RewardSink` + executor seam.

This is the **only** place the phase-isolated ``reward`` package is bound to the
concrete Phase-1/2/4/5 implementations. Every ``reward/`` module duck-types its
collaborators and imports nothing cross-phase; here we construct the real adapters
(through their **editable-install** import names — no ``sys.path`` hack) and inject
them.

Three entry points:

- :func:`build_reward_sink` — the :class:`~reward.recorder.RewardSink` composed from
  the reused Phase-4 ``research.LLMClient`` (Haiku, configured from the ``lesson_*``
  knobs — Decision F), a :class:`~reward.scorer.Scorer`, the :class:`~reward.brain.Brain`
  lesson extractor (the only AI), the real Phase-1 broker (read **only** for
  ``get_trade_history`` — never order/close, Decision J), and the Phase-2 ``Database``.
- :func:`build_brain` — the standalone lesson extractor, for the dry ``smoke_test``.
- :func:`build_executor` — a fully wired Phase-5 :class:`Executor` **with the reward
  sink injected** at the place/monitor seam, for the operator ``live_test``.

**The ``scripts.wiring`` name collision.** Phase 4, 5, 6 and 7 each ship a
``scripts/wiring.py``; the module name ``scripts.wiring`` collides. So
:func:`build_executor` constructs the Phase-5 :class:`Executor` **directly from the
installed ``execution`` package** rather than importing Phase-5's
``scripts.wiring.build_executor`` — exactly how Phase 5/6 dodged the collision. The
broker is built **once** and shared by the executor and the sink, so the sink's
read-only ``get_trade_history`` reuses the session the executor already opened.

The reward live path is deliberately **debate-free** (the only AI is the lesson
Haiku; ``debate_confidence`` is ``None``, which the scorer handles) — cheaper and
deterministic. Debate is orthogonal and can be layered in later by also injecting a
``debate_runner`` (Phase-6 wiring), without touching the reward seam.

Construction touches the keyring (the IG Demo creds via the Phase-1 factory **and**
the Anthropic key via the Decision-F ``reward.credentials`` shim) but does **no**
network request — IG ``connect`` and the Anthropic SDK are both lazy (they fire
inside ``Executor.run`` / ``Brain.reflect``). So ``pytest`` does not import this
module; the operator scripts ``smoke_test.py`` / ``live_test.py`` /
``backfill_synthetic.py`` are its only callers.

Runtime data lives under the gitignored ``<repo_root>/data/`` tree, the same layout
Phase-2 ``scripts/init_db.py`` provisions and Phase-3/4/5/6 reuse.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

logger = logging.getLogger("phase7.wiring")

# --- Runtime data locations (gitignored) ------------------------------------
# scripts/wiring.py -> scripts/ -> phase7_reward/ -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _REPO_ROOT / "data"
_DB_PATH = _DATA_DIR / "trading_bot.sqlite"  # the real Phase-2 DB (verified-contract 1.7)
_STATE_DIR = _DATA_DIR / "state"
_EXEC_STATE_PATH = _STATE_DIR / "execution_state.json"
_USAGE_LOG = _STATE_DIR / "llm_usage.json"  # shared token meter (Decision F)


def _build_llm(cfg: Any) -> Any:
    """Build the shared ``research.LLMClient`` for lesson extraction (Decision F).

    Configured with the ``lesson_*`` knobs from :class:`~reward.models.RewardConfig`
    and a ``ResearchConfig`` for pricing (the token meter's USD→EUR source). The key
    is read from the keyring here; the Anthropic SDK itself is lazy (fires only on
    ``Brain.reflect`` → ``ask_candidate``). No network request at construction.
    """
    from research.llm_client import LLMClient
    from research.models import ResearchConfig

    from reward.credentials import get_credential

    research_config = ResearchConfig()  # pricing + USD→EUR source for the token meter
    return LLMClient(
        model=cfg.lesson_model,
        api_key=get_credential("anthropic_api_key"),
        max_tokens=cfg.lesson_max_tokens,
        temperature=cfg.lesson_temperature,
        timeout_s=cfg.lesson_timeout_s,
        token_meter_path=str(_USAGE_LOG),
        config=research_config,
    )


def build_brain(*, reward_config: Any | None = None) -> Any:
    """Construct a standalone :class:`~reward.brain.Brain` lesson extractor.

    The dry ``smoke_test`` path: it exercises one real Haiku ``reflect`` without an
    executor or a DB. The keyring *is* read (the Anthropic key); no network happens
    until ``reflect`` actually runs.

    Args:
        reward_config: the run's :class:`~reward.models.RewardConfig`; defaults to the
            §5 values (Haiku lesson model).

    Returns:
        A ready-to-``reflect`` :class:`~reward.brain.Brain`.
    """
    from reward import Brain, RewardConfig

    cfg = reward_config if reward_config is not None else RewardConfig()
    return Brain(_build_llm(cfg), cfg)


def build_reward_sink(broker: Any, db: Any, *, reward_config: Any | None = None) -> Any:
    """Construct a fully wired :class:`~reward.recorder.RewardSink`.

    Composes the reused Phase-4 LLM client (Haiku) + :class:`~reward.scorer.Scorer` +
    :class:`~reward.brain.Brain` over the **passed-in** broker (read-only —
    ``get_trade_history`` for P&L, never order/close) and Phase-2 ``Database`` (CRUD
    only). The broker/db are shared with the executor in the live path.

    Args:
        broker: the real Phase-1 broker (shared with the executor).
        db: the Phase-2 ``Database``.
        reward_config: the run's :class:`~reward.models.RewardConfig`; defaults to §5.

    Returns:
        A :class:`~reward.recorder.RewardSink` satisfying the executor's seam protocol.
    """
    from reward import Brain, RewardConfig, RewardSink, Scorer

    cfg = reward_config if reward_config is not None else RewardConfig()
    llm = _build_llm(cfg)
    return RewardSink(
        db=db,
        broker=broker,
        scorer=Scorer(cfg),
        brain=Brain(llm, cfg),
        cfg=cfg,
    )


def _no_research() -> list[dict[str, Any]]:
    """A no-op Gate-2 research hook for the reward live path.

    The Phase-7 live path runs against a **seeded** candidate (Phase-5
    ``scripts/seed_candidate.py``), so ``gate_load_candidates`` finds a fresh
    candidate and never invokes research. Returning an empty list keeps the Phase-4
    research stack out of this wiring entirely; the only AI here is the lesson Haiku.
    """
    return []


def build_executor(
    config: Any,
    *,
    confirm_fn: Callable[[Any], bool],
    broker_name: str = "ig_demo",
    reward_config: Any | None = None,
) -> Any:
    """Construct a Phase-5 :class:`Executor` **with the reward sink injected** at the seam.

    Built directly from the installed ``execution`` package (not Phase-5's
    ``scripts.wiring`` — see the module docstring on the name collision). The broker is
    built **once** and shared by the executor and the sink. Gate 2's ``research_runner``
    is a no-op (the live path uses a seeded candidate); the reward sink records the
    trade's open→close lifecycle into ``trade_outcomes`` / ``reward_pts`` /
    ``trade_lessons`` (best-effort, fail-closed — Decision J).

    No network request happens here — IG ``connect`` is lazy (fires inside
    ``Executor.run``); the Anthropic key is read at construction but the SDK is lazy
    (fires when the first lesson is extracted at close).

    Args:
        config: the Phase-5 ``ExecutionConfig`` (all execution tunables).
        confirm_fn: the human-confirm predicate (``live_test`` auto-confirms).
        broker_name: the Phase-1 broker id (default ``ig_demo``; Demo only).
        reward_config: optional :class:`~reward.models.RewardConfig` for the sink.

    Returns:
        A ready-to-``run`` :class:`Executor`.
    """
    from broker_wrapper import get_broker
    from execution.execution_state import ExecutionState
    from execution.executor import Executor
    from persistence import Database, StateManager

    broker = get_broker(broker_name)  # shared by the executor and the reward sink
    db = Database(str(_DB_PATH))
    state = StateManager(str(_STATE_DIR))
    exec_state = ExecutionState(str(_EXEC_STATE_PATH))

    reward_sink = build_reward_sink(broker, db, reward_config=reward_config)

    # tz-aware now in config.tz so Gate 1 / the VETO window are correct regardless of
    # the server's local timezone (the executor's bare datetime.now default is naive).
    zone = ZoneInfo(config.tz)
    return Executor(
        broker,
        db,
        state,
        exec_state,
        config,
        _no_research,
        confirm_fn,
        reward_sink=reward_sink,
        now_fn=lambda: datetime.now(zone),
    )
