"""Dependency wiring for Phase 8 — the composition root that builds the autonomous daemon.

This is the **only** place the phase-isolated ``scheduler`` package is bound to the concrete
Phase-1…7 implementations. Every ``scheduler/`` module duck-types its collaborators and imports
nothing cross-phase; here :func:`build_scheduler` constructs the real adapters and injects them
into a single :class:`~scheduler.runner.SchedulerRunner`.

It assembles the **full** trading cycle (unlike the Phase-6/7 wirings, which each wired only their
own seam): one shared, warm IG-Demo broker drives the real Phase-4 :class:`Research`, the Phase-6
``debate_runner`` **and** the Phase-7 ``reward_sink`` are both injected into one Phase-5
:class:`Executor`, and the scheduler modules (clock / state / safety / backoff / budget /
research_tick / reconcile / runner) wrap it. **No new AI** — the AI stays inside the reused P4 pick,
P6 debate and P7 lesson; the scheduler is pure mechanics around them.

Five points worth pinning (code = source of truth — see the dated concept §11 annotation):

1. **Replicates the P4/P6/P7 builders inline, does not import their ``scripts.wiring``.** Phase 4, 5,
   6, 7 and 8 each ship a ``scripts/wiring.py``; the module name ``scripts.wiring`` collides. So this
   builds ``Research`` / the ``debate_runner`` / the ``RewardSink`` **directly from the installed
   ``research`` / ``debate`` / ``reward`` packages** — exactly how Phase 7 replicated Phase-5's
   ``build_executor`` instead of importing it.

2. **Structural demo-lock (Decision 7 / verified Contract D).** :func:`build_scheduler` raises if
   ``config.account != "demo"`` and only ever calls ``get_broker("ig_demo")``. ``AutoConfirm``
   re-checks ``config.account`` at runtime — defense in depth, two independent locks.

3. **All data paths resolved to the absolute ``<repo_root>/data/`` tree.** The ``SchedulerConfig``
   path defaults are repo-relative; a daemon may start from any cwd, so they are rewritten (via
   ``dataclasses.replace``) to the canonical gitignored tree that Phase-2 ``init_db.py`` and the
   Phase-4…7 wirings already use — DB, ``scheduler_state.json``, ``KILL``, the command file, the
   v1.6 ``research_health.jsonl`` observability log, plus the shared ``llm_usage.json`` (token
   budget) and ``execution_state.json`` (reconcile).

4. **The three runner closures live here**, where cross-phase access is allowed:
   ``realized_pnl_today`` (the daily-loss breaker's DB read), ``pending_reconcile_fn`` (the Phase-5
   ``reconcile_startup`` over the shared broker), and ``preflight_fn`` (keyring reachable + migration
   002 applied). The runner stays import-isolated; these closures carry the cross-phase knowledge.

5. **One shared ``now_fn``** threads through the clock, the executor (Gate-1 / VETO window), the
   research tick, the reconciler and the token budget, so a fake clock drives the whole stack when
   ``live_test`` / a test injects one. The executor keeps its own real ``sleep_fn`` (the monitor
   genuinely waits for the broker / time-stop); only the *loop* cadence uses the injected ``sleep_fn``.

Construction touches the keyring (the IG-Demo creds via the Phase-1 factory **and** the Anthropic key
via the reused shims) but does **no** network request — IG ``connect`` and the Anthropic SDK are all
lazy (they fire inside ``Executor.run`` / ``Research.run`` / ``Debate.run`` / ``Brain.reflect``). So
``pytest`` does not import this module; the operator scripts ``run.py`` / ``smoke_test`` (offline,
uses fakes — does not call this) / ``live_test`` are its callers. Every cross-phase import is lazy
**inside** the functions, so ``import scripts.wiring`` itself is offline-safe (mirrors Phase 7).
"""

from __future__ import annotations

import dataclasses
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from scheduler.backoff import BackoffTracker
from scheduler.budget import TokenBudget
from scheduler.clock import Clock
from scheduler.config import SchedulerConfig
from scheduler.reconcile import Reconciler
from scheduler.research_tick import ResearchTick
from scheduler.runner import SchedulerRunner
from scheduler.safety import AutoConfirm
from scheduler.state import StateStore

logger = logging.getLogger("phase8.wiring")

# --- Runtime data locations (gitignored) ------------------------------------
# scripts/wiring.py -> scripts/ -> phase8_scheduler/ -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[2]
_DATA_DIR = _REPO_ROOT / "data"
_DB_PATH = _DATA_DIR / "trading_bot.sqlite"           # the real Phase-2 DB
_STATE_DIR = _DATA_DIR / "state"
_CACHE_DIR = _DATA_DIR / "cache"
_USAGE_LOG = _STATE_DIR / "llm_usage.json"            # shared 8-field token meter
_EXEC_STATE_PATH = _STATE_DIR / "execution_state.json"
_SCHED_STATE_PATH = _STATE_DIR / "scheduler_state.json"
_KILL_PATH = _STATE_DIR / "KILL"
_COMMAND_PATH = _STATE_DIR / "scheduler_command.json"
_OBSERVABILITY_PATH = _STATE_DIR / "research_health.jsonl"  # v1.6 Step 0 per-cycle health log


def _no_research() -> list[dict[str, Any]]:
    """The no-op Gate-2 ``research_runner`` injected into the executor (verified Contract B).

    The scheduler runs the **real** Phase-4 research explicitly in ``research_tick`` *before*
    ``executor.run()``, writing a fresh ``turbo_candidates.json``. So Gate 2 must never re-call
    research: on a pick the candidate file is fresh and this is never invoked; on an abstain the
    file is a fresh ``[]`` and this no-op runs (does nothing) → ``NO_TRADE`` without a second LLM
    bill. Returning an empty list keeps the Phase-4 stack off the executor's Gate-2 path entirely.
    """
    return []


def _build_research(broker: Any, db: Any, state: Any) -> Any:
    """Build the real Phase-4 :class:`Research` over the shared broker/db/state (Contract G).

    Mirrors Phase-4 ``scripts.wiring.build_research`` but takes the *shared* broker/db/state so the
    warm IG session is reused (Decision 1) — built directly from the ``research`` package to dodge
    the ``scripts.wiring`` name collision. Registers the ETF volume proxy on the anchor epic so
    ``^GDAXI`` does not degrade to ``volume_available=False`` (Decision 5). The Anthropic key is read
    from the keyring here; the SDK is lazy (fires inside ``Research.run``).

    v1.5 Issue C, Step 2B: the daemon's ``ResearchConfig`` is built with
    ``universe=EXTENDED_UNIVERSE`` (DAX + Euro Stoxx 50, confirmed via
    ``scripts/resolve_epics.py`` 2026-07-01) — unconditionally, since this function takes
    no config override (unlike Phase-4's own ``build_research``). This is the actual
    daemon-critical widening: every autonomous cycle now sees both instruments.
    """
    from external_data import FileCache, MarketDataFetcher, TickerMapper
    from research import EXTENDED_UNIVERSE, Research, ResearchConfig
    from research.credentials import get_credential
    from research.llm_client import LLMClient

    config = ResearchConfig(universe=EXTENDED_UNIVERSE)
    mapper = TickerMapper()
    # v1.5 (Issue C): register each curated instrument's yFinance ticker + volume proxy
    # from the typed universe (SoT). DAX default unchanged → daemon behaviour identical.
    for spec in config.universe or ():
        if spec.yf_ticker:
            mapper.register(spec.epic, spec.yf_ticker)
        if spec.volume_proxy:
            mapper.register_volume_proxy(spec.epic, spec.volume_proxy)
    market_data = MarketDataFetcher(mapper, FileCache(str(_CACHE_DIR)))
    llm = LLMClient(
        model=config.model,
        api_key=get_credential("anthropic_api_key"),
        max_tokens=config.max_tokens,
        temperature=config.temperature,
        timeout_s=config.timeout_s,
        token_meter_path=str(_USAGE_LOG),
        config=config,
    )
    return Research(broker, db, state, market_data, llm, config)


def _make_debate_runner(broker: Any) -> Callable[[dict[str, Any]], Any]:
    """Build the Phase-6 ``debate_runner`` (Bull/Bear/Judge) over the shared broker.

    Replica of Phase-6 ``scripts.wiring.make_debate_runner`` built from the ``debate`` package: the
    closure constructs the :class:`Debate` once (lazily, on first use) with the reused Phase-4
    ``LLMClient`` (``cache_system=True``) and the Module-7 audit bound to ``debate_log.json``, then
    reuses it. One debate per executor cycle; the executor reads the outcome duck-typed.
    """
    from debate import Debate, DebateConfig
    from debate.audit import write_debate
    from debate.credentials import get_credential
    from research.llm_client import LLMClient
    from research.models import ResearchConfig

    holder: dict[str, Any] = {}

    def _build() -> Any:
        cfg = DebateConfig()
        research_config = ResearchConfig()
        llm = LLMClient(
            model=cfg.model_judge,
            api_key=get_credential("anthropic_api_key"),
            max_tokens=cfg.max_tokens_judge,
            temperature=cfg.temperature_judge,
            timeout_s=research_config.timeout_s,
            token_meter_path=str(_USAGE_LOG),
            config=research_config,
            cache_system=True,
        )

        def audit(outcome: Any, ctx: Any) -> None:
            write_debate(outcome, ctx, str(_DATA_DIR / "state" / "debate_log.json"))

        return Debate(broker, llm, cfg, audit=audit)

    def debate_runner(candidate: dict[str, Any]) -> Any:
        if "debate" not in holder:
            holder["debate"] = _build()
        logger.info("debate_runner: Bull/Bear/Judge for %s", candidate.get("epic"))
        return holder["debate"].run(candidate)

    return debate_runner


def _build_reward_sink(broker: Any, db: Any) -> Any:
    """Build the Phase-7 :class:`RewardSink` over the shared broker (read-only) + db.

    Replica of Phase-7 ``scripts.wiring.build_reward_sink`` built from the ``reward`` package: the
    reused Phase-4 ``LLMClient`` (Haiku, from ``RewardConfig.lesson_*``) + :class:`Scorer` +
    :class:`Brain` (the only AI). The broker is read **only** for ``get_trade_history`` (P&L /
    reconcile), never order/close (Decision J). The Anthropic key is read here; the SDK is lazy.
    """
    from research.llm_client import LLMClient
    from research.models import ResearchConfig
    from reward import Brain, RewardConfig, RewardSink, Scorer
    from reward.credentials import get_credential

    cfg = RewardConfig()
    llm = LLMClient(
        model=cfg.lesson_model,
        api_key=get_credential("anthropic_api_key"),
        max_tokens=cfg.lesson_max_tokens,
        temperature=cfg.lesson_temperature,
        timeout_s=cfg.lesson_timeout_s,
        token_meter_path=str(_USAGE_LOG),
        config=ResearchConfig(),
    )
    return RewardSink(db=db, broker=broker, scorer=Scorer(cfg), brain=Brain(llm, cfg), cfg=cfg)


def build_scheduler(
    config: SchedulerConfig,
    *,
    now_fn: Callable[[], datetime] | None = None,
    sleep_fn: Callable[[float], None] | None = None,
    max_iterations: int | None = None,
    exec_config: Any | None = None,
) -> SchedulerRunner:
    """Compose the full autonomous daemon into a ready-to-``run`` :class:`SchedulerRunner`.

    Builds one shared warm IG-Demo broker + the Phase-2 DB/state, the real Phase-4 ``Research``, the
    Phase-6 ``debate_runner`` and Phase-7 ``reward_sink`` (both injected into one Phase-5
    ``Executor`` with ``confirm_fn=AutoConfirm`` — Contract A — and ``research_runner=_no_research``
    — Contract B), then the scheduler modules around it. All cross-phase construction is lazy here.

    Args:
        config: the :class:`SchedulerConfig`. **Must** have ``account == "demo"`` (the structural
            demo-lock; anything else raises). Its path fields are rewritten to the absolute data tree.
        now_fn: optional shared clock source (default real tz-aware now in ``config.tz``). Threaded
            through the clock, executor, research tick, reconciler and budget for deterministic runs.
        sleep_fn: optional **loop-cadence** sleep (default real ``time.sleep``). The executor keeps
            its own real sleep (the monitor must actually wait); only ``clock.sleep`` uses this.
        max_iterations: optional loop bound (``None`` ⇒ run forever; ``live_test`` passes a few).
        exec_config: optional Phase-5 ``ExecutionConfig`` (default: ``point_values`` derived from
            ``research.EXTENDED_UNIVERSE`` — v1.5 Issue C, so Gate-4 sizing uses the confirmed
            per-epic point value, not the 1.0 fallback, for every non-DAX instrument); ``live_test``
            passes a short-hold one so a placed demo trade closes quickly.

    Returns:
        A wired :class:`SchedulerRunner`.

    Raises:
        ValueError: if ``config.account != "demo"`` (live auto-confirm is architecturally locked).
    """
    if config.account != "demo":
        raise ValueError(
            f"build_scheduler refuses account={config.account!r}: the autonomous daemon is "
            "demo-only and architecturally locked against live until profit validation."
        )

    # Rewrite the (repo-relative) path fields to the canonical absolute data tree, so the daemon is
    # cwd-independent and shares exactly the files init_db.py + the P4–P7 wirings use.
    config = dataclasses.replace(
        config,
        live_db_path=str(_DB_PATH),
        state_path=str(_SCHED_STATE_PATH),
        kill_path=str(_KILL_PATH),
        command_path=str(_COMMAND_PATH),
        observability_path=str(_OBSERVABILITY_PATH),
    )

    from broker_wrapper import get_broker
    from broker_wrapper.credentials import IG_DEMO_API_KEY, get_credential
    from execution.config import ExecutionConfig
    from execution.execution_state import ExecutionState
    from execution.executor import Executor
    from execution.order import reconcile_startup
    from persistence import Database, StateManager

    _now = now_fn or (lambda: datetime.now(ZoneInfo(config.tz)))
    if exec_config is not None:
        exec_cfg = exec_config
    else:
        # v1.5 Issue C, Step 2B: derive point_values from the SAME confirmed universe
        # research uses (research.EXTENDED_UNIVERSE), rather than hand-duplicating point
        # values in a second file — InstrumentSpec.point_value is the single source of
        # truth; this wiring layer (a legitimate cross-phase composition point) projects
        # it into P5's ExecutionConfig.point_values shape. DAX (1.0) is the field's own
        # default for any unmapped epic, so it doesn't need an explicit entry.
        from research import EXTENDED_UNIVERSE

        exec_cfg = ExecutionConfig(
            point_values={spec.epic: spec.point_value for spec in EXTENDED_UNIVERSE}
        )

    # --- the shared, warm trading core ---
    broker = get_broker("ig_demo")  # the ONE broker (Decision 1, Contract G)
    db = Database(str(_DB_PATH))
    state = StateManager(str(_STATE_DIR))
    exec_state = ExecutionState(str(_EXEC_STATE_PATH))

    research = _build_research(broker, db, state)
    debate_runner = _make_debate_runner(broker)
    reward_sink = _build_reward_sink(broker, db)

    # --- the scheduler modules ---
    state_store = StateStore(config.state_path)
    budget = TokenBudget(config, str(_USAGE_LOG), now_fn=_now)

    def realized_pnl_today(session_date: str) -> float:
        """Today's realized P&L from the DB (the daily-loss breaker's source — Contract E)."""
        row = db.conn.execute(
            "SELECT COALESCE(SUM(profit_loss), 0.0) FROM trade_outcomes "
            "WHERE session_date = ? AND profit_loss IS NOT NULL",
            (session_date,),
        ).fetchone()
        return float(row[0]) if row is not None else 0.0

    auto_confirm = AutoConfirm(config, state_store, config.kill_path, budget, realized_pnl_today)

    executor = Executor(
        broker,
        db,
        state,
        exec_state,
        exec_cfg,
        _no_research,                 # Contract B: real research runs in research_tick first
        auto_confirm,                 # Contract A: confirm_fn at the constructor; loop calls bare run()
        debate_runner=debate_runner,
        reward_sink=reward_sink,
        now_fn=_now,                  # shared clock; executor keeps its own real sleep_fn
    )

    clock = Clock(config, now_fn=_now, sleep_fn=sleep_fn)
    backoff = BackoffTracker(config)
    research_tick = ResearchTick(research, now_fn=_now)

    def pending_reconcile_fn() -> None:
        """Orphan-PENDING reconcile (Phase-5 ``reconcile_startup`` over the shared broker)."""
        reconcile_startup(broker, exec_state, exec_cfg)

    reconciler = Reconciler(reward_sink, pending_reconcile_fn, now_fn=_now)

    def preflight_fn() -> None:
        """Fail-closed startup probe: keyring reachable + DB migration 002 applied."""
        # 1) Keyring / Secret-Service reachable (the deployment top-risk, concept Q3). Raises if the
        #    demo cred cannot be read from the keyring (or the env fallback).
        get_credential(IG_DEMO_API_KEY, fallback_env=True)
        # 2) DB migrations present — migration 002 added trade_outcomes.account (the reward/account
        #    tag). Verify rather than silently migrate (a safety-critical daemon does not mutate schema).
        cols = {row[1] for row in db.conn.execute("PRAGMA table_info(trade_outcomes)").fetchall()}
        if "account" not in cols:
            raise RuntimeError(
                "DB schema out of date (migration 002 not applied — 'account' column missing). "
                "Run `python phase2_persistence/scripts/init_db.py` before starting the daemon."
            )

    return SchedulerRunner(
        clock=clock,
        state_store=state_store,
        config=config,
        auto_confirm=auto_confirm,
        backoff=backoff,
        research_tick=research_tick,
        reconciler=reconciler,
        executor=executor,
        broker=broker,
        preflight_fn=preflight_fn,
        max_iterations=max_iterations,
    )
