"""Dependency wiring for Phase 8 — the composition root that builds the autonomous daemon.

This is the **only** place the phase-isolated ``scheduler`` package is bound to the concrete
Phase-1…7 implementations. Every ``scheduler/`` module duck-types its collaborators and imports
nothing cross-phase; here :func:`build_scheduler` constructs the real adapters and injects them
into a single :class:`~scheduler.runner.SchedulerRunner`.

It assembles the **full** trading cycle (unlike the Phase-6/7 wirings, which each wired only their
own seam): one shared, warm IG-Demo broker drives the real Phase-4 :class:`Research`, the Phase-6
``debate_runner``, the Phase-7 ``reward_sink``, **and** the Phase-10 (V3) ``abstain_sink`` are all
injected into one Phase-5 :class:`Executor`, and the scheduler modules (clock / state / safety /
backoff / budget / research_tick / reconcile / runner) wrap it. **No new AI beyond one more
best-effort, capped call** — the AI stays inside the reused P4 pick, P6 debate, P7 lesson, and now
P10's ``reflect_abstain`` (Haiku, off unless `enable_abstain_reflect`); the scheduler is pure
mechanics around them.

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
from datetime import datetime, timezone
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


def _build_universe_from_db(db_path: Any = None) -> tuple:
    """Build the research universe from the Phase-9 (V2) ``instrument_universe`` table.

    Duplicated (not imported) from Phase 4's ``scripts.wiring.build_universe_from_db`` —
    every phase's ``scripts/wiring.py`` shares the module name ``scripts.wiring``, so P8
    cannot import P4's directly (the established reason ``_build_research`` below is
    built straight from the ``research`` package instead of importing P4's factory).
    Falls back to ``EXTENDED_UNIVERSE`` with a ``logger.warning`` if the DB is
    unreachable or empty — never silently, never a crash.
    """
    from research import EXTENDED_UNIVERSE, universe_from_records

    path = Path(db_path) if db_path is not None else _DB_PATH
    try:
        from universe import UniverseStore  # noqa: PLC0415 — lazy, phase isolation

        store = UniverseStore(path)
        try:
            records = [rec.to_instrument_spec() for rec in store.active_universe()]
        finally:
            store.close()
    except Exception as exc:  # noqa: BLE001 — any DB problem is a graceful fallback, not a crash
        logger.warning(
            "_build_universe_from_db: instrument_universe unreachable (%s) — "
            "falling back to EXTENDED_UNIVERSE", exc,
        )
        return EXTENDED_UNIVERSE
    return universe_from_records(records, fallback=EXTENDED_UNIVERSE)


def _build_market_data(mapper: Any, cache: Any, broker: Any, *, enable_ig_bars: bool) -> Any:
    """Build the research ``MarketDataFetcher``, optionally with the IG→yFinance chain.

    ``enable_ig_bars=False`` (default) ⇒ ``MarketDataFetcher(mapper, cache)`` — the
    yFinance-only path, bit-identical. ``True`` (Phase 9 / V2 Step 6) injects a
    :class:`~external_data.providers.ChainedBarProvider` (IG real-time REST bars primary,
    yFinance fallback) so ``get_bars()`` prefers IG; each attempt's ``bar_fetch`` event
    lands in the v1.6 ``research_health.jsonl`` log via ``observability.record_event``.
    The yFinance leg delegates to a *raw* fetcher (no ``bar_provider`` — breaks the
    self-reference); the raw and outer fetchers share **one** ``RateLimiter`` and **one**
    circuit breaker so the anti-429 spacing / per-symbol circuit state are not duplicated.
    Only ``get_bars()`` consults the chain — drift/momentum/history/volume are unaffected.
    """
    from external_data import MarketDataFetcher

    if not enable_ig_bars:
        return MarketDataFetcher(mapper, cache)

    from external_data.fetcher import RateLimiter, _TickerCircuit
    from external_data.providers import (
        ChainedBarProvider,
        IGBarProvider,
        YFinanceBarProvider,
    )
    from scheduler.observability import record_event

    obs_path = str(_OBSERVABILITY_PATH)

    def _health_sink(event: dict[str, Any]) -> None:
        record_event(obs_path, event)

    shared_limiter = RateLimiter()
    shared_circuit = _TickerCircuit()
    raw_fetcher = MarketDataFetcher(
        mapper, cache, rate_limiter=shared_limiter, circuit=shared_circuit
    )
    chain = ChainedBarProvider(
        [("ig", IGBarProvider(broker)), ("yf", YFinanceBarProvider(raw_fetcher))],
        health_sink=_health_sink,
    )
    return MarketDataFetcher(
        mapper,
        cache,
        rate_limiter=shared_limiter,
        circuit=shared_circuit,
        bar_provider=chain,
    )


def _build_research(broker: Any, db: Any, state: Any, *, enable_ig_bars: bool = False) -> Any:
    """Build the real Phase-4 :class:`Research` over the shared broker/db/state (Contract G).

    Mirrors Phase-4 ``scripts.wiring.build_research`` but takes the *shared* broker/db/state so the
    warm IG session is reused (Decision 1) — built directly from the ``research`` package to dodge
    the ``scripts.wiring`` name collision. Registers the ETF volume proxy on the anchor epic so
    ``^GDAXI`` does not degrade to ``volume_available=False`` (Decision 5). The Anthropic key is read
    from the keyring here; the SDK is lazy (fires inside ``Research.run``).

    v1.5 Issue C, Step 2B: the daemon's ``ResearchConfig`` used to be built
    unconditionally with ``universe=EXTENDED_UNIVERSE`` (DAX + Euro Stoxx 50, confirmed
    via ``scripts/resolve_epics.py`` 2026-07-01). **Phase 9 (V2) Step 5:** the universe
    now comes from the ``instrument_universe`` DB table (:func:`_build_universe_from_db`),
    falling back to ``EXTENDED_UNIVERSE`` if that table is empty/unreachable — an
    unbuilt/unseeded Phase 9 on a given checkout behaves exactly like before (bit-identical).
    """
    from external_data import FileCache, TickerMapper
    from research import Research, ResearchConfig
    from research.credentials import get_credential
    from research.llm_client import LLMClient

    config = ResearchConfig(universe=_build_universe_from_db())
    mapper = TickerMapper()
    # v1.5 (Issue C): register each curated instrument's yFinance ticker + volume proxy
    # from the typed universe (SoT). DAX default unchanged → daemon behaviour identical.
    for spec in config.universe or ():
        if spec.yf_ticker:
            mapper.register(spec.epic, spec.yf_ticker)
        if spec.volume_proxy:
            mapper.register_volume_proxy(spec.epic, spec.volume_proxy)
    market_data = _build_market_data(
        mapper, FileCache(str(_CACHE_DIR)), broker, enable_ig_bars=enable_ig_bars
    )
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


class _AbstainLLMAdapter:
    """Wraps the reused Phase-4 ``LLMClient`` to satisfy ``AbstainLLM.complete(prompt,
    timeout_s) -> str``. ``LLMClient`` has no free-text call, only the JSON-schema
    ``ask_candidate`` — a one-field schema (``{"lesson": string}``) gets a plain string
    back out. ``timeout_s`` is accepted for Protocol-compliance; the real per-call
    timeout is already ``LLMClient``'s own ``timeout_s`` (set at construction below).
    """

    _SCHEMA = {
        "type": "object",
        "properties": {"lesson": {"type": "string"}},
        "required": ["lesson"],
        "additionalProperties": False,
    }

    def __init__(self, client: Any) -> None:
        self._client = client

    def complete(self, prompt: str, timeout_s: float) -> str:
        result = self._client.ask_candidate(system="", user=prompt, json_schema=self._SCHEMA)
        return result["lesson"]


def _build_abstain_sink(config: SchedulerConfig, paper_engine: Any = None) -> Any:
    """Build the Phase-10 (V3) :class:`AbstainLessonSink` over its own DB connection.

    ``AbstainStore`` opens its **own** ``sqlite3`` connection (the UniverseStore
    pattern — phase isolation, no ``persistence.Database`` import), so it needs no
    shared broker/db argument, unlike ``_build_reward_sink``. The LLM adapter (Haiku,
    reused Phase-4 ``LLMClient`` + ``RewardConfig.lesson_*`` knobs — same model/timeout
    the reward-sink lesson extraction already uses) is only built when
    ``config.enable_abstain_reflect`` — reflect stays best-effort/capped either way, but
    skipping the client construction when reflect is off avoids touching the keyring
    for a call that will never fire. ``paper_engine`` (Block B, ``None`` unless
    ``config.enable_paper_trades``) is threaded straight into the sink's existing
    ``paper_engine`` seam (``sink.py``, wired dark since Block A).
    """
    from abstain_lessons.sink import AbstainLessonSink
    from abstain_lessons.store import AbstainStore

    store = AbstainStore(str(_DB_PATH))
    store.ensure_schema()

    llm = None
    if config.enable_abstain_reflect:
        from research.llm_client import LLMClient
        from research.models import ResearchConfig
        from reward import RewardConfig
        from reward.credentials import get_credential

        cfg = RewardConfig()
        client = LLMClient(
            model=cfg.lesson_model,
            api_key=get_credential("anthropic_api_key"),
            max_tokens=cfg.lesson_max_tokens,
            temperature=cfg.lesson_temperature,
            timeout_s=cfg.lesson_timeout_s,
            token_meter_path=str(_USAGE_LOG),
            config=ResearchConfig(),
        )
        llm = _AbstainLLMAdapter(client)

    return AbstainLessonSink(
        store, llm=llm, paper_engine=paper_engine, reflect_daily_cap=config.reflect_daily_cap,
    )


def _build_paper_engine(config: SchedulerConfig, broker: Any, exec_cfg: Any) -> Any:
    """Build the Phase-10 (V3) Block-B :class:`PaperEngine` (Both-Sides-Shadow-Tracking,
    V3-D5/D6). ``quote_fetch`` wraps ``broker.get_price(epic)`` — one fresh call per
    debate-abstain trigger (the plan's sanctioned exception to "no extra IG calls",
    §10.2: a stale entry would corrupt every R-multiple). ``exec_cfg`` supplies the
    **same fixed** ``stop_distance_points``/``limit_distance_points``/``max_hold_minutes``
    the real order path sizes against (verified this session — Gate-4 sizing reads them
    directly, not a per-trade computed value).

    Council-Paper-Call (§10.3, 2026-07-17 session): when ``config.enable_paper_debate``
    (default ``False`` — stays off this session, the Nikinger flips it later), a
    :class:`~abstain_lessons.paper.PaperDebateCaller` is built the same way the
    reflect LLM is below in :func:`_build_abstain_sink` (same credential shim, same
    ``LLMClient``/``ResearchConfig`` construction) and wired in. Model is the real
    Judge's (``DebateConfig().model_judge``, Sonnet — not the cheap Haiku reflect
    model): the point of the feature is "what would the council pick if forced", and
    the cap (default 3/day) keeps the cost trivial regardless.
    """
    from abstain_lessons.paper import PaperEngine
    from abstain_lessons.paper_store import PaperTradeStore

    store = PaperTradeStore(str(_DB_PATH))
    store.ensure_schema()

    def quote_fetch(epic: str) -> dict[str, float]:
        env = broker.get_price(epic)
        if not env.ok:
            raise RuntimeError(f"get_price not ok for {epic}")
        data = env.data or {}
        return {"bid": data["bid"], "ask": data["ask"]}

    debate_caller = None
    if config.enable_paper_debate:
        from abstain_lessons.paper import PaperDebateCaller
        from debate.models import DebateConfig
        from debate.prompts import build_paper_pick_prompt
        from research.llm_client import LLMClient
        from research.models import ResearchConfig
        from reward.credentials import get_credential

        dcfg = DebateConfig()
        client = LLMClient(
            model=dcfg.model_judge,
            api_key=get_credential("anthropic_api_key"),
            max_tokens=dcfg.max_tokens_judge,
            temperature=dcfg.temperature_judge,
            timeout_s=dcfg.wall_clock_timeout_s,
            token_meter_path=str(_USAGE_LOG),
            config=ResearchConfig(),
        )
        debate_caller = PaperDebateCaller(client, build_paper_pick_prompt)

    return PaperEngine(
        store, quote_fetch, exec_cfg,
        debate_caller=debate_caller, council_daily_cap=config.paper_debate_daily_cap,
    )


# 1-min bars covering the longest possible hold (v1 max_hold_minutes=240) — well under
# the IG get_ohlcv 1000-bar cap (phase1_broker_wrapper/adapters/ig_adapter.py:423-441).
_PAPER_BAR_COUNT = 300


def _build_paper_tracker(config: SchedulerConfig, broker: Any) -> Any:
    """Build the Phase-10 (V3) Block-B :class:`PaperTradeTracker`. ``bar_fetch`` wraps
    one ``get_ohlcv(epic, "MINUTE", _PAPER_BAR_COUNT)`` call per affected epic per
    tick. ``reflect_cap_check`` reads **both** stores' daily lesson counts against the
    shared ``reflect_daily_cap`` (V3-D8) — own connections (cheap; mirrors
    ``_observed_abstain_sink``'s "recompute rather than thread state" choice).

    Deliberately **not** threaded with the scheduler's shared (``config.tz``-local,
    test-injectable) ``_now`` clock: the tracker's own default (real UTC) is always
    correct against ``created_utc``/``time_stop_utc`` regardless of ``config.tz``, and
    this best-effort secondary system doesn't need lock-step determinism with the main
    executor loop.
    """
    from abstain_lessons.paper import PaperTradeTracker
    from abstain_lessons.paper_store import PaperTradeStore
    from abstain_lessons.store import AbstainStore

    paper_store = PaperTradeStore(str(_DB_PATH))
    paper_store.ensure_schema()
    abstain_store = AbstainStore(str(_DB_PATH))
    abstain_store.ensure_schema()

    def bar_fetch(epic: str) -> list[dict[str, Any]]:
        env = broker.get_ohlcv(epic, "MINUTE", _PAPER_BAR_COUNT)
        if not env.ok:
            raise RuntimeError(f"get_ohlcv not ok for {epic}")
        return (env.data or {}).get("bars", [])

    llm = None
    if config.enable_abstain_reflect:
        from research.llm_client import LLMClient
        from research.models import ResearchConfig
        from reward import RewardConfig
        from reward.credentials import get_credential

        cfg = RewardConfig()
        client = LLMClient(
            model=cfg.lesson_model,
            api_key=get_credential("anthropic_api_key"),
            max_tokens=cfg.lesson_max_tokens,
            temperature=cfg.lesson_temperature,
            timeout_s=cfg.lesson_timeout_s,
            token_meter_path=str(_USAGE_LOG),
            config=ResearchConfig(),
        )
        llm = _AbstainLLMAdapter(client)

    def reflect_cap_check() -> bool:
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        combined = (
            abstain_store.count_lessons_today(now_iso) + paper_store.count_lessons_today(now_iso)
        )
        return combined < config.reflect_daily_cap

    return PaperTradeTracker(paper_store, bar_fetch, llm=llm, reflect_cap_check=reflect_cap_check)


def _enrich_abstain_detail(inner: Any, research: Any) -> Any:
    """Wrap ``inner`` (an :class:`AbstainSink`) to backfill ``cycle_outcome["detail"]`` with
    the Phase-4 ``Research``'s own ``last_no_pick_reasoning`` on a ``research_empty`` (Gate 2)
    abstain (Phase-10 B4/H6-fix, 2026-07-31).

    Gate 2's own ``detail`` (threaded through by the executor's B4-fix) is a fixed generic
    string ("no fresh candidate (research abstained or empty)") — it never carries the
    model's actual abstain prose. ``research_empty`` is the dominant NO_TRADE case (364/366
    cycles in the 2026-07-31 data-week review), so this is the one that matters most: the
    same warm ``Research`` instance ``research_tick`` just drove still holds
    ``last_no_pick_reasoning`` from that same cycle's LLM call (reset to ``None`` on every
    ``run()``, so it only ever carries the current cycle's own reasoning or nothing —
    never a stale value from a prior cycle). Only overwrites when the model actually
    produced prose (a genuine LLM abstain); a preflight/exception abstain leaves Gate 2's
    generic detail in place, still better than empty. See
    ``phase10_v3/DATA_WEEK_REVIEW_2026-07-31.md`` §4 B4.
    """

    class _Enriched:
        def on_no_trade(self, cycle_outcome: Any) -> Any:
            if cycle_outcome.get("research_empty") is True:
                reasoning = getattr(research, "last_no_pick_reasoning", None)
                if reasoning:
                    cycle_outcome = {**cycle_outcome, "detail": reasoning}
            return inner.on_no_trade(cycle_outcome)

    return _Enriched()


def _observed_abstain_sink(inner: Any, observability_path: str) -> Any:
    """Wrap ``inner`` (an :class:`AbstainSink`) with the ``abstain_recorded`` observability
    event (reason, stage, epic) — the generic ``record_event`` call, not ``record_cycle``'s
    fixed schema (verified-anchors annex, ``phase10_v3/CLAUDE.md``). Classification is pure
    and cheap (stdlib-only, no I/O) so re-running it here for the log line, alongside the
    real classify+persist inside ``inner``, is simpler than threading the record back out
    of the locked ``AbstainSink.on_no_trade(cycle_outcome) -> None`` contract.
    """
    from abstain_lessons.classifier import classify_abstain
    from scheduler.observability import record_event

    class _Observed:
        def on_no_trade(self, cycle_outcome: Any) -> None:
            inner.on_no_trade(cycle_outcome)
            try:
                record = classify_abstain(cycle_outcome)
                record_event(observability_path, {
                    "event": "abstain_recorded",
                    "reason": record.reason.value,
                    "stage": record.stage.value,
                    "epic": record.epic,
                })
            except Exception as exc:  # noqa: BLE001 — observability must never break the cycle
                logger.critical("abstain observability event failed: %s", exc)

    return _Observed()


def _build_context_recorder(config: SchedulerConfig) -> Any:
    """Build the Phase-10 (V3) Block-B :class:`ContextRecorder` over its own DB connection.

    ``MarketContextWriter`` opens its **own** ``sqlite3`` connection (the same
    UniverseStore/AbstainStore pattern), so it needs no shared broker/db argument.
    """
    from market_context.writer import ContextRecorder, MarketContextWriter

    writer = MarketContextWriter(str(_DB_PATH))
    writer.ensure_schema()
    return ContextRecorder(writer)


def _observed_context_recorder(inner: Any, observability_path: str) -> Any:
    """Wrap ``inner`` (a :class:`ContextRecorder`) with the ``context_recorded``
    observability event (outcome, epic) — mirrors ``_observed_abstain_sink``."""
    from scheduler.observability import record_event

    class _Observed:
        def on_decision(self, **kwargs: Any) -> None:
            inner.on_decision(**kwargs)
            try:
                record_event(observability_path, {
                    "event": "context_recorded",
                    "outcome": kwargs.get("outcome"),
                    "epic": kwargs.get("epic"),
                })
            except Exception as exc:  # noqa: BLE001 — observability must never break the cycle
                logger.critical("context observability event failed: %s", exc)

    return _Observed()


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
            ``_build_universe_from_db()`` — the Phase-9/V2 DB universe research actually trades
            (Phase-10 B1-fix, 2026-07-31; fail-soft to ``EXTENDED_UNIVERSE``), so Gate-4 sizing
            uses the confirmed per-epic point value for every active instrument, not the
            fail-closed default); ``live_test`` passes a short-hold one so a placed demo trade
            closes quickly.

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
        # v1.5 Issue C, Step 2B / Phase-10 B1-fix (2026-07-31): derive point_values from
        # the SAME universe research actually trades — the Phase-9/V2 DB universe, via
        # the same _build_universe_from_db() helper _build_research() uses below (fail-soft
        # to EXTENDED_UNIVERSE if the DB is unreachable/empty). The prior version sourced
        # this map from the static 4-epic EXTENDED_UNIVERSE while research already traded
        # the 8-epic DB universe — every epic outside those 4 (e.g. AEX, point_value 40.0)
        # silently fell back to ExecutionConfig.point_value_for()'s 1.0 default, causing a
        # 40x oversizing on every AEX order (all 3 ever placed were broker-rejected on
        # INSUFFICIENT_FUNDS; see phase10_v3/DATA_WEEK_REVIEW_2026-07-31.md §4 B1).
        # InstrumentSpec.point_value remains the single source of truth; this wiring layer
        # (a legitimate cross-phase composition point) projects it into P5's
        # ExecutionConfig.point_values shape. sizing.compute_size now fails closed (no
        # trade) for any epic absent from a populated point_values map (execution/sizing.py)
        # — an unmapped epic can no longer silently size at 1.0.
        exec_cfg = ExecutionConfig(
            point_values={spec.epic: spec.point_value for spec in _build_universe_from_db()}
        )

    # --- the shared, warm trading core ---
    broker = get_broker("ig_demo")  # the ONE broker (Decision 1, Contract G)
    db = Database(str(_DB_PATH))
    state = StateManager(str(_STATE_DIR))
    exec_state = ExecutionState(str(_EXEC_STATE_PATH))

    research = _build_research(broker, db, state, enable_ig_bars=config.enable_ig_bars)
    debate_runner = _make_debate_runner(broker)
    reward_sink = _build_reward_sink(broker, db)
    paper_engine = None
    paper_tracker = None
    if config.enable_paper_trades:
        paper_engine = _build_paper_engine(config, broker, exec_cfg)
        paper_tracker = _build_paper_tracker(config, broker)
    abstain_sink = None
    if config.enable_abstain_lessons:
        abstain_sink = _observed_abstain_sink(
            _enrich_abstain_detail(
                _build_abstain_sink(config, paper_engine=paper_engine), research
            ),
            config.observability_path,
        )
    context_recorder = None
    if config.enable_context_persistence:
        context_recorder = _observed_context_recorder(
            _build_context_recorder(config), config.observability_path
        )

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
        abstain_sink=abstain_sink,
        context_recorder=context_recorder,
        now_fn=_now,                  # shared clock; executor keeps its own real sleep_fn
    )

    clock = Clock(config, now_fn=_now, sleep_fn=sleep_fn)
    backoff = BackoffTracker(config)
    research_tick = ResearchTick(research, now_fn=_now)

    def pending_reconcile_fn() -> None:
        """Orphan-PENDING reconcile (Phase-5 ``reconcile_startup`` over the shared broker)."""
        reconcile_startup(broker, exec_state, exec_cfg)

    reconciler = Reconciler(reward_sink, pending_reconcile_fn, now_fn=_now)

    def universe_refresher() -> None:
        """Phase 9 (V2) discover + promote pass over the shared broker (Plan §8 Step 5).

        Makes zero LLM calls (Bauprinzip: null new AI in this layer). Reuses the same
        warm broker + the already-built Phase-4 ``Research``'s Phase-3 fetcher
        (``research.market_data`` — same ticker-mapper registrations, no second
        ``MarketDataFetcher`` instance). Lazy import of ``universe`` so a checkout
        without Phase 9 built yet still imports this wiring module cleanly — the
        runner never calls this closure unless it is actually wired in (only on the
        line that passes it to ``SchedulerRunner`` below), so an ``ImportError`` here
        would only surface at daemon start, not at module import time.
        """
        from research import EXTENDED_UNIVERSE
        from universe import UniverseStore, discover, run_promotion_cycle

        universe_store = UniverseStore(_DB_PATH)
        try:
            # Idempotent (INSERT OR IGNORE on epic): the live-verified curated
            # four seed as status=active so the DB universe is never empty on
            # day one. Was never called anywhere (2026-07-06 finding) — the
            # store method existed since Step 1, callerless.
            universe_store.seed_curated(EXTENDED_UNIVERSE)
            discover(broker, universe_store)
            run_promotion_cycle(
                broker,
                research.market_data,
                universe_store,
                is_demo=(config.account == "demo"),
            )
        finally:
            universe_store.close()

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
        universe_refresher=universe_refresher,
        paper_tracker=paper_tracker,
        max_iterations=max_iterations,
    )
