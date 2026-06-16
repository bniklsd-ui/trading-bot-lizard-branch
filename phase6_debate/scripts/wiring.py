"""Dependency wiring for Phase 6 — build a real :class:`Debate` and the executor seam.

This is the **only** place the phase-isolated ``debate`` package is bound to the
concrete Phase-1/2/4/5 implementations. Every ``debate/`` module duck-types its
collaborators and imports nothing cross-phase; here we construct the real adapters
(through their **editable-install** import names — no ``sys.path`` hack) and inject
them.

Three entry points:

- :func:`build_debate` — the shared ``research.LLMClient`` (built with
  ``cache_system=True`` — Decision D/F), the real Phase-1 broker (read **once** by
  the context builder; the agents never get it — Decision J), and the Module-7 audit
  bound to ``data/state/debate_log.json``, composed into a :class:`Debate`.
- :func:`make_debate_runner` — the lazy ``debate_runner`` factory injected at the
  Phase-5 Gate-2↔Gate-3 seam (the analogue of Phase-5's ``research_runner``).
- :func:`build_executor` — a fully wired Phase-5 :class:`Executor` **with the debate
  injected**, for the operator ``live_test``.

**The ``scripts.wiring`` name collision (the §8 [VERIFY]).** Phase 4, 5 and 6 each
ship a ``scripts/wiring.py``; the module name ``scripts.wiring`` collides. So
:func:`build_executor` constructs the Phase-5 :class:`Executor` **directly from the
installed ``execution`` package** rather than importing Phase-5's
``scripts.wiring.build_executor`` — exactly how Phase 5 dodged the Phase-4 collision
(it built ``Research`` directly from the installed ``research`` API). The broker is
built **once** and shared by the executor and the debate, so the debate reuses the
session the executor already opened.

Construction touches the keyring (the Anthropic key, via the Decision-F
``debate.credentials`` shim) but does **no** network request — IG ``connect`` and the
Anthropic SDK are both lazy (they fire inside ``Executor.run`` / ``Debate.run``). So
``pytest`` does not import this module; the operator scripts ``smoke_test.py`` /
``live_test.py`` are its only callers.

Runtime data lives under the gitignored ``<repo_root>/data/`` tree, the same layout
Phase-2 ``scripts/init_db.py`` provisions and Phase-3/4/5 reuse.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from debate import Debate, DebateConfig
from debate.audit import write_debate

logger = logging.getLogger("phase6.wiring")

# --- Runtime data locations (gitignored) ------------------------------------
# scripts/wiring.py -> scripts/ -> phase6_debate/ -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _REPO_ROOT / "data"
_DB_PATH = _DATA_DIR / "trading_bot.sqlite"
_STATE_DIR = _DATA_DIR / "state"
_EXEC_STATE_PATH = _STATE_DIR / "execution_state.json"
_USAGE_LOG = _STATE_DIR / "llm_usage.json"
_DEBATE_LOG = _STATE_DIR / "debate_log.json"


def build_debate(
    broker: Any,
    *,
    debate_config: DebateConfig | None = None,
    with_audit: bool = True,
) -> Debate:
    """Construct a fully wired :class:`Debate` over a shared, already-built broker.

    Builds the shared Phase-4 :class:`LLMClient` (``cache_system=True``, key from the
    keyring, usage metered to ``llm_usage.json``, pricing from a ``ResearchConfig``)
    and (when ``with_audit``) the Module-7 audit sink bound to ``debate_log.json``, and
    injects the **passed-in** broker (read once by the context builder — never handed
    to a model).

    No network request happens here — IG ``connect`` and the Anthropic SDK are lazy
    and fire inside ``Debate.run``. The keyring *is* read (the Anthropic key).

    Args:
        broker: the real Phase-1 broker (shared with the executor in the live path).
        debate_config: the run's :class:`DebateConfig`; defaults to the locked §0 values.
        with_audit: bind the ``debate_log.json`` audit sink (default). ``smoke_test``
            passes ``False`` for a dry run that writes no audit record ("kein Save").

    Returns:
        A ready-to-``run`` :class:`Debate`.
    """
    cfg = debate_config if debate_config is not None else DebateConfig()

    # Phase-4 reuse (Decision F): the shared client + its pricing config.
    from debate.credentials import get_credential
    from research.llm_client import LLMClient
    from research.models import ResearchConfig

    research_config = ResearchConfig()  # pricing + USD→EUR source for the token meter
    llm = LLMClient(
        # model / temperature / max_tokens are set per turn by the orchestrator +
        # ask_agent; these initial values are placeholders for the shared client.
        model=cfg.model_judge,
        api_key=get_credential("anthropic_api_key"),
        max_tokens=cfg.max_tokens_judge,
        temperature=cfg.temperature_judge,
        timeout_s=research_config.timeout_s,
        token_meter_path=str(_USAGE_LOG),
        config=research_config,
        cache_system=True,  # cache the stable system+context prefix (Decision D)
    )

    # Module-7 audit adapted to the Debate's (outcome, ctx) -> None sink shape.
    def audit(outcome: Any, ctx: Any) -> None:
        write_debate(outcome, ctx, str(_DEBATE_LOG))

    return Debate(broker, llm, cfg, audit=audit if with_audit else None)


def make_debate_runner(
    broker: Any, *, debate_config: DebateConfig | None = None
) -> Callable[[dict[str, Any]], Any]:
    """Build the Phase-5 seam's lazy ``debate_runner`` (shares the executor's broker).

    The returned closure builds the :class:`Debate` once (on first invocation, so the
    keyring/SDK are touched only if the seam actually runs) and reuses it, returning
    the :class:`~debate.models.DebateOutcome` the executor reads duck-typed. One
    debate per executor cycle.
    """
    holder: dict[str, Debate] = {}

    def debate_runner(candidate: dict[str, Any]) -> Any:
        if "debate" not in holder:
            holder["debate"] = build_debate(broker, debate_config=debate_config)
        logger.info("debate_runner: running Bull/Bear/Judge for %s", candidate.get("epic"))
        return holder["debate"].run(candidate)

    return debate_runner


def _no_research() -> list[dict[str, Any]]:
    """A no-op Gate-2 research hook for the debate live path.

    The Phase-6 live path runs against a **seeded** candidate (Phase-5
    ``scripts/seed_candidate.py``), so ``gate_load_candidates`` finds a fresh
    candidate and never invokes research. Returning an empty list keeps the Phase-4
    research stack out of this wiring entirely; the AI here is the debate, not research.
    """
    return []


def build_executor(
    config: Any,
    *,
    confirm_fn: Callable[[Any], bool],
    broker_name: str = "ig_demo",
    debate_config: DebateConfig | None = None,
) -> Any:
    """Construct a Phase-5 :class:`Executor` **with the debate injected** at the seam.

    Built directly from the installed ``execution`` package (not Phase-5's
    ``scripts.wiring`` — see the module docstring on the name collision). The broker is
    built **once** and shared by the executor and the debate. Gate 2's
    ``research_runner`` is a no-op (the live path uses a seeded candidate); the debate
    is the AI path, injected as ``debate_runner``.

    No network request happens here — IG ``connect`` is lazy (fires inside
    ``Executor.run``); the Anthropic key is read when the debate first runs.

    Args:
        config: the Phase-5 ``ExecutionConfig`` (all execution tunables).
        confirm_fn: the human-confirm predicate (``live_test`` auto-confirms).
        broker_name: the Phase-1 broker id (default ``ig_demo``; Demo only).
        debate_config: optional :class:`DebateConfig` for the injected debate.

    Returns:
        A ready-to-``run`` :class:`Executor`.
    """
    from broker_wrapper import get_broker
    from execution.execution_state import ExecutionState
    from execution.executor import Executor
    from persistence import Database, StateManager

    broker = get_broker(broker_name)  # shared by the executor and the debate
    db = Database(str(_DB_PATH))
    state = StateManager(str(_STATE_DIR))
    exec_state = ExecutionState(str(_EXEC_STATE_PATH))

    debate_runner = make_debate_runner(broker, debate_config=debate_config)

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
        debate_runner=debate_runner,
        now_fn=lambda: datetime.now(zone),
    )
