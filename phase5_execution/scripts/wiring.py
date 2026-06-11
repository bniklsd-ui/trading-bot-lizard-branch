"""Dependency wiring for Phase 5 — build a real :class:`Executor` (concept §10).

This is the **only** place the phase-isolated ``execution`` package is bound to the
concrete Phase-1/2/3/4 implementations. Every ``execution/`` module types its
collaborators duck-typed / via ``typing.Protocol`` and imports nothing cross-phase;
here we construct the real adapters (through their **editable-install** import names —
no ``sys.path`` hack) and inject them through the :class:`Executor` constructor.

Construction touches the keyring (IG Demo creds via the Phase-1 factory) but does
**no** network request — IG ``connect`` is lazy (it fires inside ``Executor.run``).
The Anthropic key is read only if/when Gate 2 actually runs research (the
``research_runner`` builds the Phase-4 stack lazily). So ``pytest`` does not import
this module; the operator scripts ``ig_bot.py`` / ``smoke_test.py`` / ``live_test.py``
are its only callers.

The ``research_runner`` (Gate 2's lazy Phase-4 hook) is built **here**, constructing a
``Research`` that **shares** this executor's ``broker`` / ``db`` / ``state`` instances —
so research persists to the very ``turbo_candidates.json`` that ``gate_load_candidates``
re-reads, and reuses the already-open broker session. We construct ``Research`` directly
from the installed ``research`` public API rather than reusing Phase-4's
``scripts.wiring.build_research`` (which is not installed and whose ``scripts`` module
name would collide with this one) — a §10 reconciliation, code = source of truth.

Runtime data lives under the gitignored ``<repo_root>/data/`` tree, the same layout
Phase-2 ``scripts/init_db.py`` provisions (SQLite + ``state/``) and Phase-3 uses for
``cache/``.
"""

from __future__ import annotations

import dataclasses
import logging
from datetime import datetime
from typing import Any, Callable
from zoneinfo import ZoneInfo
from pathlib import Path

from execution.config import ExecutionConfig
from execution.execution_state import ExecutionState
from execution.executor import Executor

logger = logging.getLogger("phase5.wiring")

# --- Runtime data locations (gitignored) ------------------------------------
# scripts/wiring.py -> scripts/ -> phase5_execution/ -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _REPO_ROOT / "data"
_DB_PATH = _DATA_DIR / "trading_bot.sqlite"
_STATE_DIR = _DATA_DIR / "state"
_CACHE_DIR = _DATA_DIR / "cache"
_EXEC_STATE_PATH = _STATE_DIR / "execution_state.json"
_USAGE_LOG = _STATE_DIR / "llm_usage.json"


def _make_research_runner(
    broker: Any,
    db: Any,
    state: Any,
    research_config: Any | None,
    epic_override: str | None,
) -> Callable[[], list[dict[str, Any]]]:
    """Build Gate 2's lazy Phase-4 research hook (shares broker/db/state).

    The returned closure builds the Phase-4 stack only when invoked (stale/missing
    candidates), runs one research cycle — which **persists** to the shared
    ``StateManager`` — and returns the picks as dicts. ``gate_load_candidates``
    ignores the return value and re-reads ``load_candidates()``; the persistence side
    effect is the point.
    """

    def research_runner() -> list[dict[str, Any]]:
        # Lazy Phase-4 imports — only reached when research must actually run.
        from external_data import FileCache, MarketDataFetcher, TickerMapper
        from research import Research, ResearchConfig
        from research.credentials import get_credential
        from research.llm_client import LLMClient

        rcfg = research_config if research_config is not None else ResearchConfig()
        if epic_override:
            rcfg = dataclasses.replace(rcfg, epic_allowlist=(epic_override,))

        mapper = TickerMapper()
        if rcfg.volume_proxy:
            mapper.register_volume_proxy(rcfg.epic_allowlist[0], rcfg.volume_proxy)
        market_data = MarketDataFetcher(mapper, FileCache(str(_CACHE_DIR)))

        llm = LLMClient(
            model=rcfg.model,
            api_key=get_credential("anthropic_api_key"),
            max_tokens=rcfg.max_tokens,
            temperature=rcfg.temperature,
            timeout_s=rcfg.timeout_s,
            token_meter_path=str(_USAGE_LOG),
            config=rcfg,
        )

        # Share the executor's broker/db/state so research persists where Gate 2 reads.
        research = Research(broker, db, state, market_data, llm, rcfg)
        logger.info("research_runner: running Phase-4 research for %s", rcfg.epic_allowlist[0])
        return [candidate.to_dict() for candidate in research.run()]

    return research_runner


def build_executor(
    config: ExecutionConfig,
    *,
    confirm_fn: Callable[[Any], bool],
    broker_name: str = "ig_demo",
    research_config: Any | None = None,
    epic_override: str | None = None,
) -> Executor:
    """Construct a fully wired :class:`Executor` against IG Demo + Phase-2/3/4.

    Builds the real Phase-1 broker (``ig_demo``), Phase-2 ``Database`` /
    ``StateManager``, the Phase-5 ``ExecutionState`` write-ahead store, and Gate 2's
    lazy ``research_runner`` (sharing broker/db/state), then injects them — plus the
    operator's ``confirm_fn`` — into the orchestrator.

    No network request happens here — IG ``connect`` is lazy and fires inside
    ``Executor.run``; the Anthropic key is read only if research actually runs.

    Args:
        config: the run's :class:`ExecutionConfig` (all tunables).
        confirm_fn: the human-confirm predicate (from ``ig_bot``: stdin / ``--yes`` /
            ``--dry``; ``smoke_test`` passes a dry decliner; ``live_test`` auto-confirms).
        broker_name: the Phase-1 broker id (default ``ig_demo``; Phase 5 is Demo only).
        research_config: optional Phase-4 ``ResearchConfig`` for the research hook.
        epic_override: optional research allow-list epic (``ig_bot --epic``).

    Returns:
        A ready-to-``run`` :class:`Executor`.
    """
    # Phase-1 broker — keyring-backed, no network at construction.
    from broker_wrapper import get_broker

    broker = get_broker(broker_name)

    # Phase-2 persistence — on-disk SQLite + JSON state under data/ (read-only here).
    from persistence import Database, StateManager

    db = Database(str(_DB_PATH))
    state = StateManager(str(_STATE_DIR))

    # Phase-5 own write-ahead idempotency store.
    exec_state = ExecutionState(str(_EXEC_STATE_PATH))

    research_runner = _make_research_runner(
        broker, db, state, research_config, epic_override
    )

    # tz-aware now in config.tz so Gate 1 / the VETO window are correct regardless of
    # the server's local timezone (the executor's bare datetime.now default is naive).
    zone = ZoneInfo(config.tz)
    return Executor(
        broker,
        db,
        state,
        exec_state,
        config,
        research_runner,
        confirm_fn,
        now_fn=lambda: datetime.now(zone),
    )
