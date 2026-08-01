"""Module 10 (concept §10) — ``SchedulerRunner``: the loop / daemon orchestrator.

This is the piece that *runs* everything the prior nine modules built. Each of them
(``clock`` / ``state`` / ``killswitch`` / ``safety`` / ``backoff`` / ``budget`` /
``research_tick`` / ``reconcile``) is a pure, phase-isolated unit that mutates a
:class:`~scheduler.state.SchedulerState` and returns — none of them runs anything. The runner
ties them into one deterministic, fail-closed cycle: every iteration it reads the clock, checks
the kill-switch, reconciles broker-closes, asks the auto-confirm gate whether a trade may even be
attempted, triggers the real Phase-4 research, drives a **bare** ``executor.run()`` (Contract A —
``confirm_fn=AutoConfirm`` is wired at the executor's *constructor*, not passed here), records the
outcome, and — on a cycle exception — backs off, tripping the kill-switch after
``max_consecutive_failures`` in a row.

**No new AI.** A scheduler is pure mechanics. The only AI in the whole loop is what already lives
inside the collaborators it drives (the Phase-4 ``ask_candidate`` inside ``research_tick``, the
Phase-6 debate + Phase-7 lesson inside ``executor.run()``) — all reused unchanged. The runner
itself never sees a Gate / VETO / order / LLM; it can structurally not bypass a safety check
because it does not reference one.

**Deterministic by construction.** Time and sleep are injected through the :class:`~scheduler.clock.Clock`
(``now_fn`` / ``sleep_fn``), and the loop takes an optional ``max_iterations`` stop condition — so
tests drive a fake clock, pass a no-op sleep, and bound the loop, with no real wall-clock, no real
sleep, and no network (the Nikinger's flagged special task: "Contract A + the deterministic
loop-driving — injected ``now_fn``/``sleep_fn`` + a stop condition").

Repo conventions apply (``from __future__ import annotations``, type hints + docstrings, one file =
one responsibility, logging to a module logger on **stderr**, never swallow silently). Module-level
imports are stdlib + ``scheduler.*`` only — ``import scheduler.runner`` pulls nothing cross-phase
(the proven package isolation); the collaborators it cannot import are duck-typed via local
``typing.Protocol``\\s (``_BrokerLike`` / ``_ExecutorLike``), mirroring ``state.CycleResult`` /
``reconcile._RewardSinkLike``.

---

Concept↔code reconciliations (dated 2026-06-28, code = source of truth):

1. **``broker.ensure_session()`` → private :meth:`_warm_session`.** The concept §10 loop sketch
   calls ``broker.ensure_session()``, but no such method exists — the Phase-1 adapter exposes
   ``is_connected() -> bool`` / ``connect() -> Envelope`` / ``disconnect() -> Envelope``
   (``ig_adapter.py:137,157,178``). The runner composes the warm-up from the real methods:
   *"if not connected, connect; raise on a non-ok envelope"*. Raised inside the loop → caught →
   backoff; inside :meth:`preflight` → wrapped to :class:`~scheduler.exceptions.PreflightError`.

2. **The constructor drops ``budget``.** The concept §10 signature lists ``budget``, but the
   budget gate is already inside ``auto_confirm.can_open()`` (Module 6 holds the budget) and the
   loop never calls it directly — so it would be an unused dependency. Dropping it is the same
   "drop the unused injected dep" discipline ``reconcile.py`` (dropped ``db`` / ``state_store``)
   and ``research_tick.py`` (dropped ``state_store``) already used.

3. **Cross-phase preflight probes are injected, not inlined.** The concept §10 ``preflight``
   inlines ``get_credential`` + a DB/migrations check. To preserve the import-isolation and keep
   the runner 100% unit-testable, those cross-phase touches are an injected ``preflight_fn``
   (raises on failure) that the Module-11 wiring backs with the keyring + DB checks — exactly the
   pattern ``safety.py`` (the ``realized_pnl_today`` closure) and ``reconcile.py`` (the
   ``pending_reconcile_fn`` closure) established. The runner additionally runs ``broker.connect()``
   itself (it already holds the broker for the loop's warm-up).

4. **``killswitch_path`` folded into ``config.kill_path``** — the runner holds the config; no
   separate path argument (the §10 sketch passed ``killswitch_path`` separately).

5. **The stop condition is a keyword-only ``max_iterations``** (default ``None`` ⇒ the real
   infinite daemon; tests pass ``K`` to bound the loop) — the concept's "bricht die Schleife nach
   K Iterationen". ``now_fn`` / ``sleep_fn`` are already injected via the ``Clock``.

6. **``reconcile_interval_min`` is honored via a small throttle** (:meth:`_maybe_reconcile`) so the
   5-minute WINDOW cadence does not hammer ``get_trade_history`` every cycle; reconcile is *forced*
   on startup, in POST_WINDOW, and at shutdown (Decision 11: "Startup + periodisch + Shutdown").
   The pass is idempotent, so over-running would only be a cost concern, never a correctness one.

7. **Web-UI start/stop is a soft pause via the command file** (Module 12, concept §12 "Daemon
   pollt"). After the kill-switch check the loop reads ``command.read_command(config.command_path)``;
   a ``"stop"`` makes the iteration a no-op idle (no ``break``, no state field touched — the UI
   derives PAUSED from the command file) so a later ``"start"`` / cleared file resumes the same live
   daemon. The KILL file stays the *hard* stop. **No command file ⇒ behavior is bit-identical** to
   before (the default path is unchanged) — additive, like the ``reward_sink`` / ``debate_runner``
   seams elsewhere.

8. **The broker return is an Envelope read by ATTRIBUTE, not a mapping** (fixed 2026-06-29, the
   first ``live_test`` run). The Phase-1 ``Envelope`` is a ``@dataclass`` (``.ok`` / ``.data`` /
   ``.error``) with **no** ``.get()``; the original Module-10 code read ``env.get("ok")`` and the
   ``_BrokerLike`` protocol mis-documented "a mapping with an ``'ok'`` key". This passed CI only
   because the test ``_FakeBroker`` returned plain ``dict``\\s, then raised ``'Envelope' object has
   no attribute 'get'`` against the real broker on the first live cycle. Now ``preflight`` and
   ``_warm_session`` read ``env.ok`` / ``env.error`` (see :class:`_EnvelopeLike`), and the fakes
   return objects matching that shape so the contract divergence cannot recur. Lesson: a fake that
   diverges from the real return shape turns a live-only bug invisible in CI.

9. **v1.6 (Phase-8 hotfix Step 0, observability) — one diagnostic log write per WINDOW cycle.**
   Right after ``research_tick.ensure_candidates`` (whose return value used to be discarded), the
   ``ResearchResult`` is now captured and handed to ``observability.record_cycle`` — a per-epic
   brain-context health snapshot plus the free-text no-trade reason, appended to
   ``config.observability_path``. Fail-soft (the module never raises out), diagnostic-only (gates
   nothing), and only on the ``can_open`` PASS branch — a cap-blocked cycle never triggered research
   in the first place, so there is nothing to log for it beyond ``state.last_no_trade_reason``
   (already recorded). Purely additive: no observability call ⇒ the WINDOW branch's trading logic
   is byte-for-byte the same as before Step 0.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Protocol

from scheduler import command, killswitch, observability
from scheduler.backoff import BackoffTracker
from scheduler.clock import Clock, Phase
from scheduler.config import SchedulerConfig
from scheduler.exceptions import PreflightError, SchedulerError
from scheduler.reconcile import Reconciler
from scheduler.research_tick import ResearchTick
from scheduler.safety import AutoConfirm
from scheduler.state import SchedulerState, StateStore

logger = logging.getLogger("scheduler.runner")


class _EnvelopeLike(Protocol):
    """A Phase-1 :class:`~broker_wrapper.envelope.Envelope` return — read by **attribute**.

    ⚠ **Reconciliation (2026-06-29, first live run — code = source of truth):** the real
    ``Envelope`` is a ``@dataclass`` (``broker_wrapper/envelope.py``) with ``.ok`` / ``.data`` /
    ``.error`` **attributes** — it is **not** a mapping and has **no** ``.get()``. The original
    Module-10 ``_BrokerLike`` wrongly documented "a mapping with an ``'ok'`` key" and the runner
    read ``env.get("ok")``; that worked only because the unit-test ``_FakeBroker`` returned plain
    ``dict``\\s, so it passed in CI but raised ``'Envelope' object has no attribute 'get'`` against
    the real broker on the first ``live_test``. The runner now reads ``env.ok`` / ``env.error`` and
    the fakes return objects matching this shape (so the contract divergence can't recur).
    """

    @property
    def ok(self) -> bool: ...

    @property
    def error(self) -> Any: ...


class _BrokerLike(Protocol):
    """The slice of the Phase-1 broker the runner drives (duck-typed — no cross-phase import).

    The real ``IGAdapter`` satisfies it; tests pass a tiny fake. ``connect`` / ``disconnect``
    return an :class:`~broker_wrapper.envelope.Envelope` (an object with ``.ok`` / ``.error``
    **attributes**, see :class:`_EnvelopeLike`) and never raise on broker errors (they return an
    error envelope) — the runner reads ``env.ok``. ``is_connected`` returns a bare ``bool``.
    """

    def is_connected(self) -> bool: ...

    def connect(self) -> _EnvelopeLike: ...

    def disconnect(self) -> _EnvelopeLike: ...


class _ExecutorLike(Protocol):
    """The slice of the Phase-5 ``Executor`` the runner drives (duck-typed).

    ``run()`` is **arg-less** (Contract A: ``confirm_fn`` is a constructor argument set by the
    wiring) and returns an ``ExecutionResult`` — itself a ``state.CycleResult`` (``.status`` /
    ``.profit_loss``) the runner hands straight to ``StateStore.record_cycle``.
    """

    def run(self) -> Any: ...


class SchedulerRunner:
    """The autonomous trading daemon's main loop (concept §10).

    Holds references to its collaborators (not snapshots) and runs them in the §10 cycle. The loop
    is fully deterministic: time and sleep come from the injected :class:`~scheduler.clock.Clock`,
    and ``max_iterations`` bounds it for tests.

    Args:
        clock: the :class:`~scheduler.clock.Clock` (phase classification + injectable now/sleep).
        state_store: the :class:`~scheduler.state.StateStore` (load/save/rollover/record_cycle).
        config: the frozen :class:`~scheduler.config.SchedulerConfig` (cadence + ``kill_path`` +
            ``reconcile_interval_min``).
        auto_confirm: the :class:`~scheduler.safety.AutoConfirm` gate; its ``can_open(state)`` is
            the pre-cycle gate (it also is the executor's ``confirm_fn``, wired separately).
        backoff: the :class:`~scheduler.backoff.BackoffTracker` (consecutive-failure memory).
        research_tick: the :class:`~scheduler.research_tick.ResearchTick` (real Phase-4 trigger).
        reconciler: the :class:`~scheduler.reconcile.Reconciler` (idempotent P&L catch-up pass).
        executor: anything satisfying :class:`_ExecutorLike` (the Phase-5 ``Executor``).
        broker: anything satisfying :class:`_BrokerLike` (the Phase-1 adapter), for the warm-up.
        preflight_fn: a zero-arg callable the wiring backs with the keyring + DB/migrations checks;
            it **raises** on a failed prerequisite (the runner wraps that to ``PreflightError``).
        universe_refresher: optional zero-arg callable (Phase 9 / V2, Plan §8 Step 5) the wiring
            backs with a discover + ``run_promotion_cycle`` pass against the ``instrument_universe``
            table. Default ``None`` ⇒ never called — today's behaviour, bit-identical. When set, it
            runs once in :meth:`preflight` and then at most once per
            ``config.universe_refresh_interval_min`` inside the WINDOW phase (never nested inside a
            research tick — a Gate-2 candidate pick and a universe refresh are independent passes).
            Best-effort/fail-soft (a refresh failure is logged ``critical``, never propagated — a
            stale universe is a data-freshness concern, not a safety one).
        paper_tracker: optional Phase-10 (V3) Block-B ``PaperTradeTracker``-shaped object
            (``.tick() -> None``). Default ``None`` ⇒ never called, bit-identical. When set,
            ticked once per WINDOW-phase cycle (after the executor run) — resolving OPEN
            paper trades past their time-stop needs no market-open check itself (retrospective
            bar resolution), but tying it to the same cadence as everything else is simplest.
            Best-effort/fail-soft, same discipline as ``universe_refresher``.
        shadow_pair_scheduler: optional zero-arg callable (Phase 11 / H1) the wiring backs
            with a time-scheduled Both-Sides-Shadow-pair pass over the active DB universe,
            fully decoupled from ``REASON_DEBATE_ABSTAIN``. Default ``None`` -> never
            called, bit-identical. When set, runs at most once per
            ``config.shadow_schedule_interval_min`` inside the WINDOW phase (same
            throttled pattern as ``universe_refresher``, but **not** also fired in
            :meth:`preflight` -- a timer tick needs no warm-up call). Best-effort/fail-soft.
        max_iterations: optional loop bound. ``None`` (default) ⇒ run forever (the real daemon);
            a positive int ⇒ stop after that many iterations (deterministic tests).
    """

    def __init__(
        self,
        *,
        clock: Clock,
        state_store: StateStore,
        config: SchedulerConfig,
        auto_confirm: AutoConfirm,
        backoff: BackoffTracker,
        research_tick: ResearchTick,
        reconciler: Reconciler,
        executor: _ExecutorLike,
        broker: _BrokerLike,
        preflight_fn: Callable[[], None],
        universe_refresher: Callable[[], Any] | None = None,
        paper_tracker: Any | None = None,
        shadow_pair_scheduler: Callable[[], Any] | None = None,
        max_iterations: int | None = None,
    ) -> None:
        self._clock = clock
        self._state_store = state_store
        self._config = config
        self._auto_confirm = auto_confirm
        self._backoff = backoff
        self._research_tick = research_tick
        self._reconciler = reconciler
        self._executor = executor
        self._broker = broker
        self._preflight_fn = preflight_fn
        self._universe_refresher = universe_refresher
        self._paper_tracker = paper_tracker
        self._shadow_pair_scheduler = shadow_pair_scheduler
        self._max_iterations = max_iterations
        # Non-sticky graceful-stop flag (set by request_stop(), checked at the loop top).
        # Deliberately NOT the kill-switch file: a SIGTERM-driven stop must not persist a
        # halt that would block the next restart (the KILL file is for genuine, sticky halts).
        self._stop_requested = False

        self._kill_path = config.kill_path
        self._command_path = config.command_path
        self._cycle_interval_s = config.cycle_interval_min * 60
        self._idle_poll_s = config.idle_poll_min * 60
        self._reconcile_interval_s = config.reconcile_interval_min * 60
        self._shadow_schedule_interval_s = config.shadow_schedule_interval_min * 60

    # --- preflight ---------------------------------------------------------

    def preflight(self) -> None:
        """Fail-closed startup check — raise :class:`PreflightError` if anything is unverifiable.

        Two probes (concept Q3, the deployment top-risk): the injected ``preflight_fn`` (keyring /
        Secret-Service reachable + DB & migrations present, wiring-built) and ``broker.connect()``.
        On any failure the daemon exits cleanly **without attempting any trade** — it must never
        trade on an unverified credential / DB path. Called once at the top of :meth:`run`.
        """
        try:
            self._preflight_fn()
        except Exception as exc:  # noqa: BLE001 — any unverifiable prerequisite is fatal, fail-closed
            raise PreflightError(f"preflight check failed: {exc}") from exc

        env = self._broker.connect()
        if not env.ok:  # Envelope is a dataclass (.ok / .error), NOT a mapping — see _EnvelopeLike
            raise PreflightError(f"broker connect failed: {env.error}")

        self._run_universe_refresher()

    # --- graceful stop -----------------------------------------------------

    def request_stop(self) -> None:
        """Ask the loop to stop cleanly at the next iteration boundary (non-sticky).

        Sets an in-memory flag the loop checks at the top of each iteration; the loop then breaks
        and runs :meth:`shutdown`. Used by the ``run.py`` SIGTERM/SIGINT handler — deliberately
        *not* the kill-switch file, so a signal-driven stop does not persist a halt that would block
        the next restart. Safe to call from a signal handler (a single boolean assignment); an
        in-progress ``clock.sleep`` completes before the stop takes effect (v1 latency).
        """
        self._stop_requested = True

    # --- the loop ----------------------------------------------------------

    def run(self) -> None:
        """Run the main loop until the kill-switch, a backoff trip, or ``max_iterations``.

        Calls :meth:`preflight` first (a ``PreflightError`` propagates — clean exit, no trade), does
        one forced startup reconcile, then loops the §10 cycle. Each iteration is wrapped so a cycle
        exception is contained (logged ``critical`` → backoff), the state is always saved in a
        ``finally``, and a clean stop always runs :meth:`shutdown`.
        """
        self.preflight()

        state = self._state_store.load()
        self._startup_reconcile(state)

        iteration = 0
        while self._max_iterations is None or iteration < self._max_iterations:
            iteration += 1
            now = self._clock.now()
            state = self._state_store.rollover_if_new_day(state, now)
            try:
                if self._stop_requested:
                    logger.info("stop requested — shutting down.")
                    break
                if killswitch.is_set(self._kill_path):
                    state.kill_reason = killswitch.read_reason(self._kill_path)
                    logger.critical("kill switch set: %s — stopping.", state.kill_reason)
                    break
                if command.read_command(self._command_path) == "stop":
                    # Soft, reversible pause (UI ``stop``): keep the process alive and do no
                    # trading work until the command flips to ``start`` / is cleared. Distinct
                    # from the kill-switch (the hard stop above): no ``break``, no state field
                    # touched (the UI derives PAUSED from the command file directly), so a later
                    # ``start`` resumes the same live daemon. Idle-poll cadence while paused.
                    logger.info("paused by command file (ui:stop) — idling.")
                    self._clock.sleep(self._idle_poll_s)
                    continue
                self._run_phase(self._clock.classify(now), state, now)
                self._backoff.record_success(state)
            except Exception:  # noqa: BLE001 — a bad cycle must never crash the data-collection daemon
                logger.critical("cycle failure", exc_info=True)
                state = self._backoff.record_failure(state)
                if self._backoff.should_trip(state):
                    killswitch.set_kill(self._kill_path, "auto:backoff")
                    state.kill_reason = "auto:backoff"
                    logger.critical(
                        "backoff tripped after %d consecutive failures — kill switch set, stopping.",
                        state.consecutive_failures,
                    )
                    break
                self._clock.sleep(self._backoff.delay_s(state))
            finally:
                self._state_store.save(state)

        self.shutdown(state)
        self._state_store.save(state)

    def _run_phase(self, phase: Phase, state: SchedulerState, now: datetime) -> None:
        """Do one cycle's worth of work for ``phase`` (concept §10). May raise → caught by the loop.

        PRE_OPEN warms the session + reconciles, then sleeps until WINDOW (capped by the idle poll).
        WINDOW warms + reconciles, runs the pre-cycle gate, and on a pass triggers real research +
        a bare ``executor.run()`` (Contract A), recording the outcome. POST_WINDOW does a forced
        final reconcile then sleeps to the next pre-open (capped by the idle poll — 2026-07-11
        fix, see ``phase8_scheduler/CLAUDE.md``: an uncapped sleep here blocked ``request_stop()``
        and the kill-switch for the whole POST_WINDOW→PRE_OPEN gap, up to a full weekend). IDLE
        just sleeps.
        """
        if phase is Phase.PRE_OPEN:
            self._warm_session()
            self._maybe_reconcile(state, now)
            self._clock.sleep(
                min(self._clock.seconds_until(Phase.WINDOW, now), self._idle_poll_s)
            )
        elif phase is Phase.WINDOW:
            self._warm_session()
            self._maybe_reconcile(state, now)
            self._maybe_refresh_universe(state, now)
            self._maybe_run_shadow_pairs(state, now)
            ok, reason = self._auto_confirm.can_open(state)
            if ok:
                research_result = self._research_tick.ensure_candidates(state)
                # v1.6 (Phase-8 hotfix Step 0, observability): one per-cycle diagnostic record,
                # whether or not this tick produced a pick — the safety net for diagnosing a
                # future recurrence of the ^FCHI/^IBEX-style intermittent data gap without
                # needing another ad-hoc live investigation.
                observability.record_cycle(
                    self._config.observability_path,
                    ts=now,
                    context_health=research_result.context_health,
                    picked=research_result.picked,
                    n=research_result.n,
                    reason=research_result.reason,
                    abort_detail=research_result.abort_detail,
                )
                result = self._executor.run()  # Contract A: bare run(); confirm_fn at the ctor
                state = self._state_store.record_cycle(state, result)
            else:
                state.last_no_trade_reason = reason
            self._run_paper_tracker()
            self._clock.sleep(self._cycle_interval_s)
        elif phase is Phase.POST_WINDOW:
            self._warm_session()
            self._maybe_reconcile(state, now, force=True)
            self._clock.sleep(
                min(self._clock.seconds_until(Phase.PRE_OPEN, now), self._idle_poll_s)
            )
        else:  # Phase.IDLE
            self._clock.sleep(self._idle_poll_s)

    # --- shutdown ----------------------------------------------------------

    def shutdown(self, state: SchedulerState) -> None:
        """Stop cleanly: a final reconcile + close the broker session. Fail-soft, never raises.

        Run once when the loop ends (kill-switch, backoff trip, or ``max_iterations``). Each step is
        individually guarded (``critical`` on failure, no re-raise) so a stop never crashes — the
        whole point of a clean shutdown. The caller persists ``state`` afterwards.
        """
        try:
            self._warm_session()
            self._reconciler.tick(state)
        except Exception:  # noqa: BLE001 — a failed final reconcile must not crash the shutdown
            logger.critical("shutdown reconcile failed", exc_info=True)
        try:
            self._broker.disconnect()
        except Exception:  # noqa: BLE001 — a failed disconnect must not crash the shutdown
            logger.critical("shutdown broker disconnect failed", exc_info=True)

    # --- internals ---------------------------------------------------------

    def _warm_session(self) -> None:
        """Ensure the IG session is live, composing the Phase-1 ``is_connected`` / ``connect``.

        No-op when already connected; otherwise ``connect()`` and raise on a non-ok envelope (no
        ``ensure_session`` exists — reconciliation 1). Raised inside the loop → caught → backoff;
        inside :meth:`preflight` / :meth:`shutdown` it is wrapped / guarded by the caller.
        """
        if self._broker.is_connected():
            return
        env = self._broker.connect()
        if not env.ok:  # Envelope is a dataclass (.ok / .error), NOT a mapping — see _EnvelopeLike
            raise SchedulerError(f"broker connect failed: {env.error}")

    def _maybe_reconcile(
        self, state: SchedulerState, now: datetime, *, force: bool = False
    ) -> None:
        """Run the reconcile pass, throttled to ``reconcile_interval_min`` unless ``force``.

        ``force`` (startup / POST_WINDOW / shutdown) always runs; otherwise the pass runs only when
        it is :meth:`_due` (honoring Decision 11's ``reconcile_interval_min``, so the 5-min WINDOW
        cadence does not re-hit ``get_trade_history`` every cycle). The pass itself never raises.
        """
        if force or self._due(state.last_reconcile_ts, now):
            self._reconciler.tick(state)

    def _due(self, last_ts: str | None, now: datetime) -> bool:
        """Whether the reconcile interval has elapsed since ``last_ts`` (tz-safe, UTC compare).

        ``None`` (never reconciled) → ``True``. ``last_ts`` is the ISO timestamp the reconciler
        stamped via its ``now_fn=clock.now`` (tz-aware in ``config.tz``); an unparseable value is
        treated as due (fail-soft toward reconciling). Both instants are compared in UTC so a DST
        boundary cannot distort the elapsed seconds.
        """
        return self._due_after(last_ts, now, self._reconcile_interval_s)

    def _due_after(self, last_ts: str | None, now: datetime, interval_s: float) -> bool:
        """Generic tz-safe "has ``interval_s`` elapsed since ``last_ts``" check.

        Shared by :meth:`_due` (reconcile) and the universe-refresh throttle (Plan §8 Step 5) —
        same fail-soft-toward-running semantics (missing/unparseable ``last_ts`` → due).
        """
        if not last_ts:
            return True
        try:
            last = datetime.fromisoformat(last_ts)
        except ValueError:
            return True
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        elapsed = (now.astimezone(timezone.utc) - last.astimezone(timezone.utc)).total_seconds()
        return elapsed >= interval_s

    def _run_universe_refresher(self) -> None:
        """Fire-and-forget call of the injected ``universe_refresher`` (fail-soft).

        No-op when ``None`` (default — the daemon's behaviour stays bit-identical without a
        wiring opt-in). A refresh failure is logged ``critical`` and never propagated: a stale
        ``instrument_universe`` table is a data-freshness concern, not a safety one — it must
        never trip backoff/kill the way a cycle exception does.
        """
        if self._universe_refresher is None:
            return
        try:
            self._universe_refresher()
        except Exception:  # noqa: BLE001 — fail-soft, see docstring
            logger.critical("universe refresher failed", exc_info=True)

    def _run_paper_tracker(self) -> None:
        """Fire-and-forget ``paper_tracker.tick()`` (fail-soft, same pattern as
        ``_run_universe_refresher``). No-op when ``None`` (default — bit-identical).
        """
        if self._paper_tracker is None:
            return
        try:
            self._paper_tracker.tick()
        except Exception:  # noqa: BLE001 — fail-soft, see docstring
            logger.critical("paper tracker tick failed", exc_info=True)

    def _maybe_refresh_universe(self, state: SchedulerState, now: datetime) -> None:
        """Run the universe refresher, throttled to ``config.universe_refresh_interval_min``.

        Called from the WINDOW phase only, deliberately **not** nested inside
        ``research_tick.ensure_candidates`` — a discover/promote pass and a Gate-2 candidate
        pick are independent passes (Plan §8 Step 5: "nie innerhalb eines Research-Ticks").
        """
        if self._universe_refresher is None:
            return
        interval_s = self._config.universe_refresh_interval_min * 60
        if not self._due_after(state.last_universe_refresh_ts, now, interval_s):
            return
        self._run_universe_refresher()
        state.last_universe_refresh_ts = now.isoformat()

    def _run_shadow_pair_scheduler(self) -> None:
        """Fire-and-forget call of the injected ``shadow_pair_scheduler`` (fail-soft),
        same pattern as ``_run_universe_refresher``. No-op when ``None`` (default —
        bit-identical, Phase 11 / H1 opt-in).
        """
        if self._shadow_pair_scheduler is None:
            return
        try:
            self._shadow_pair_scheduler()
        except Exception:  # noqa: BLE001 — fail-soft, see docstring
            logger.critical("shadow pair scheduler failed", exc_info=True)

    def _maybe_run_shadow_pairs(self, state: SchedulerState, now: datetime) -> None:
        """Run the shadow-pair scheduler, throttled to
        ``config.shadow_schedule_interval_min`` (Phase 11 / H1).

        Called from the WINDOW phase only, independent of the auto-confirm gate and the
        research tick — paper trades never touch the real trade caps, and this tick is
        fully decoupled from ``REASON_DEBATE_ABSTAIN`` by design (that's the point of H1).
        """
        if self._shadow_pair_scheduler is None:
            return
        if not self._due_after(state.last_shadow_pairs_ts, now, self._shadow_schedule_interval_s):
            return
        self._run_shadow_pair_scheduler()
        state.last_shadow_pairs_ts = now.isoformat()

    def _startup_reconcile(self, state: SchedulerState) -> None:
        """One forced reconcile before the loop (Decision 11 "Startup"). Fail-soft; saves state.

        Warms the session and runs the pass; a warm-up failure here is logged ``critical`` but not
        fatal (the loop will retry + back off). Persists the stamped ``last_reconcile_ts`` so the
        first WINDOW iteration's throttle starts from a known point.
        """
        try:
            self._warm_session()
            self._reconciler.tick(state)
        except Exception:  # noqa: BLE001 — a failed startup reconcile must not stop the daemon starting
            logger.critical("startup reconcile failed", exc_info=True)
        self._state_store.save(state)
