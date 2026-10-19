"""The orchestrator — the whole execution cycle in one place (concept §8).

:class:`Executor` composes the individually-built, individually-tested pieces of
Phase 5 into a single ``run()``: session health → startup reconcile → the four
suitability Gates (1/2/3/5) → Gate 4 sizing → the four fresh-snapshot VETOs →
human-confirm → write-ahead placement → monitoring. It writes **no** new broker,
gate, or VETO logic; every rule already lives in ``gates.py`` / ``sizing.py`` /
``vetos.py`` / ``order.py`` / ``monitor.py``. This is pure composition.

**No AI here.** Phase 5 itself contains no AI: the lazy Phase-4 ``research_runner``
reached through Gate 2 (``gate_load_candidates``) when no fresh candidate is stored is
injected, so this module never imports Phase 4. An optional Phase-6 ``debate_runner``
(Decision A) may likewise be injected between Gate 2 and Gate 3; it too is duck-typed
and never imported here, and it defaults to ``None`` (no debate → Phase 5 unchanged).

Result vocabulary (documented in :mod:`execution.models`):

- ``CLOSED_BY_BROKER`` / ``TIME_STOP`` — a position was opened and ended (monitor).
- ``OPEN`` — opened, monitor returned it open (only if monitoring is skipped).
- ``NO_TRADE`` — a gate/VETO/abstain said no; clean, exit 0.
- ``ABORTED_BY_USER`` — human-confirm declined; no order placed.
- ``ABORT`` — fail-closed: session health, reconcile, an unresolved ``PENDING``
  order, or a failed time-stop close. ``ig_bot.py`` (Step 9) exits non-zero on this.

Aborts are **returned**, not raised: ``ExecutionAbort`` / ``ReconcileConflict``
(both ``ExecutionError``, neither a subclass of the other) are caught at the run
boundary and surfaced as ``ExecutionResult(status="ABORT", ...)`` so the CLI has a
single result object to serialise. Every gate/VETO/abort reason is logged to
**stderr**; stdout is reserved for that machine-readable JSON (Step 9).

Determinism: ``now_fn`` / ``sleep_fn`` are injected (keyword-only, defaulting to the
real clock / sleep) — the same pattern ``monitor.py`` and ``order.py`` already use,
so tests drive Gate 1, the VETO window check, the PENDING re-check loop, and the
monitor loop with no real time passing. The §8 signature stub did not list them; this
is a code-as-source-of-truth reconciliation (dated §8 annotation).

Phase-isolated: ``execution.*`` + stdlib only; broker / db / state are duck-typed
(passed in, never imported).
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from typing import Any, Callable

from execution.config import ExecutionConfig
from execution.exceptions import ExecutionAbort, ReconcileConflict
from execution.execution_state import ExecutionState
from execution.gates import (
    gate_constraints,
    gate_direction_consistency,
    gate_load_candidates,
    gate_time_window,
)
from execution.models import ExecutionResult, OrderPlan
from execution.monitor import _position_present, monitor_position
from execution.order import build_order_plan, place_order, reconcile_startup
from execution.sizing import compute_size, select_risk_pct
from execution.vetos import pre_trade_check

logger = logging.getLogger(__name__)


class Executor:
    """Run one execution cycle (concept §8). All collaborators are injected (DI)."""

    def __init__(
        self,
        broker: Any,
        db: Any,
        state: Any,
        exec_state: ExecutionState,
        config: ExecutionConfig,
        research_runner: Callable[[], list[dict[str, Any]]],
        confirm_fn: Callable[[OrderPlan], bool],
        *,
        debate_runner: Callable[[dict[str, Any]], Any] | None = None,
        reward_sink: Any | None = None,
        abstain_sink: Any | None = None,
        context_recorder: Any | None = None,
        now_fn: Callable[[], datetime] = datetime.now,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        """Wire the cycle's collaborators.

        Args:
            broker: duck-typed broker (the :class:`~execution.protocols.BrokerProtocol`
                surface — session, market probes, OHLCV, order/close/reconcile).
            db: read-only :class:`~execution.protocols.DbProtocol` (risk level / score).
            state: :class:`~execution.protocols.StateProtocol` (candidate JSON store).
            exec_state: the write-ahead idempotency store (Phase 5's own JSON file).
            config: the run's :class:`ExecutionConfig` (all tunables).
            research_runner: lazy Phase-4 runner for Gate 2 (``build_research(cfg).run``);
                injected so Phase 4 stays out of this module.
            confirm_fn: human-confirm predicate (``ig_bot`` stdin prompt; ``--yes`` →
                ``lambda _p: True``; tests: a stub).
            debate_runner: optional Phase-6 Bull/Bear/Judge hook, injected between Gate 2
                and Gate 3 (Decision A). ``None`` (the default) → no debate, so Phase 5
                stays **AI-free and bit-identical**. When present it is called with the
                Gate-2 candidate and returns a duck-typed debate outcome (read here as
                ``.decision`` / ``.direction`` / ``.rationale`` — **no Phase-6 import**;
                phase isolation): ``ABSTAIN`` → ``NO_TRADE``; ``TRADE`` → the candidate's
                direction is enriched in-memory (possibly reversed). The runner never
                receives the broker or any gate/VETO — it cannot bypass one (Decision J).
            reward_sink: optional Phase-7 outcome/reward hook (Decision A), injected with
                the same DI pattern. ``None`` (the default) → the seam is skipped and
                Phase 5 stays **bit-identical and AI-free**. When present it is called
                ``on_trade_opened`` after a position opens (before monitoring) and
                ``on_trade_closed`` after the monitor returns a real close — both with a
                duck-typed snapshot (no Phase-7 import here; phase isolation). It is a
                **passive** consumer of snapshots: it never receives the broker write
                path, a Gate, or a VETO, so it cannot bypass one. Both calls are guarded
                — a raising sink is logged ``critical`` and never crashes the cycle (J).
            abstain_sink: optional Phase-10 (V3) no-trade-lessons hook, same DI pattern
                as ``reward_sink``. ``None`` (the default) → the seam is skipped, Phase 5
                stays bit-identical. When present, ``on_no_trade(cycle_outcome)`` is
                called once on **every** NO_TRADE return path (never on a trade path)
                via the shared ``_no_trade`` helper — see :class:`execution.protocols.
                AbstainSink`. Also passive/guarded (Decision J), no Phase-10 import here.
                Returns the persisted abstain ``record_id`` (``None`` on failure), which
                feeds ``context_recorder`` below.
            context_recorder: optional Phase-10 (V3) Block-B hook (``market_context``),
                same DI pattern. ``None`` (the default) → the seam is skipped, Phase 5
                stays bit-identical. When present, ``on_decision(...)`` is called once per
                cycle on **all three** outcomes — TRADE (``_notify_opened``), NO_TRADE
                (``_no_trade``), and the post-debate **ABORT** path (a broker-rejected
                order is exactly this case — Nikinger-authorized scope extension beyond
                the original TRADE/NO_TRADE-only plan, 2026-07-17). The earlier
                session-health/reconcile ABORT (before any candidate exists) is
                deliberately **not** recorded — nothing decided yet to report. Passive/
                guarded (Decision J), no Phase-10 import here.
            now_fn / sleep_fn: injected clock / sleep for deterministic tests.
        """
        self.broker = broker
        self.db = db
        self.state = state
        self.exec_state = exec_state
        self.config = config
        self.research_runner = research_runner
        self.confirm_fn = confirm_fn
        self.debate_runner = debate_runner
        self.reward_sink = reward_sink
        self.abstain_sink = abstain_sink
        self.context_recorder = context_recorder
        self.now_fn = now_fn
        self.sleep_fn = sleep_fn

    # -- result helpers -----------------------------------------------------

    def _no_trade(
        self,
        rule: str,
        reason: str,
        *,
        epic: str | None = None,
        failed_gate: str | None = None,
        veto: str | None = None,
        debate_decision: str | None = None,
        research_empty: bool = False,
        error: str | None = None,
        price_env: Any = None,
    ) -> ExecutionResult:
        """A clean no-trade outcome (gate/VETO/abstain) — exit 0, no order placed.

        The single funnel every NO_TRADE return path already goes through — also the
        Phase-10 (V3) abstain-sink seam (:meth:`_notify_no_trade`) and the Block-B
        context-recorder seam (:meth:`_notify_context`). The keyword-only params are the
        S2 classifier contract fields the caller knows about at its point in the cycle;
        unset ones default to their "nothing to report" value (``None``/``False``) and
        are harmless when no sink/recorder is injected. ``price_env`` (Phase-10 B4-fix,
        2026-07-31) is only in scope at the Gate-4/VETO call sites (fetched for sizing) —
        earlier gates pass ``None``, which is harmless (no spread to report yet).
        """
        logger.info("no trade: %s — %s", rule, reason)
        cycle_outcome = {
            "outcome": "NO_TRADE",
            "epic": epic,
            "failed_gate": failed_gate,
            "veto": veto,
            "debate_decision": debate_decision,
            "research_empty": research_empty,
            "error": error,
            # Phase-10 B4-fix (2026-07-31): `reason` is the richest text available at
            # every call site (a gate's message, a VETO's message, or — for the DEBATE
            # stage — the Judge's own abstain rationale). Previously computed and logged
            # but never handed to the classifier, so every AbstainRecord.detail landed
            # at the model default "" (see phase10_v3/DATA_WEEK_REVIEW_2026-07-31.md §4 B4).
            "detail": reason,
        }
        record_id = self._notify_no_trade(cycle_outcome)
        spread_pct = (price_env.data or {}).get("spread_pct") if price_env is not None else None
        self._notify_context(
            outcome="NO_TRADE",
            epic=epic,
            spread_pct=spread_pct,
            gate_results_json=json.dumps({"failed_gate": failed_gate}) if failed_gate else None,
            veto_results_json=json.dumps({"veto": veto}) if veto else None,
            abstain_record_id=record_id,
        )
        return ExecutionResult(
            status="NO_TRADE", deal_id=None, plan=None, detail=f"{rule}: {reason}"
        )

    def _abort(
        self,
        detail: str,
        *,
        plan: OrderPlan | None = None,
        deal_id: str | None = None,
        candidate: dict[str, Any] | None = None,
        debate_outcome: Any = None,
        price_env: Any = None,
    ) -> ExecutionResult:
        """A fail-closed abort outcome — the CLI exits non-zero, operator attends.

        Phase-10 (V3) Block-B context-recorder seam: recorded only when the caller
        passes a ``candidate`` (the post-``place_order``/monitor abort — a broker
        rejection is exactly this path, e.g. 2026-07-15's flagged incident). The earlier
        session-health/reconcile abort (before any candidate exists) never passes one,
        so it stays unrecorded — deliberate, see the constructor's ``context_recorder``
        docstring. ``price_env`` (Phase-10 B4-fix, 2026-07-31) is only ever passed by the
        post-``place_order``/monitor call site, which by then has a fresh Gate-4 price
        snapshot in scope.

        ``detail`` (e.g. IG's own reject reason, ``order.py``'s ``"order {ref} REJECTED
        by broker: {reason}"``) is folded into ``veto_results_json`` alongside the fixed
        "vetos pass" note (2026-07-17 Bug-B fix — the ABORT row's visibility from the
        first Block-B session didn't yet carry *why* it aborted, only *that* it did;
        this closes that gap for the next occurrence without a schema change).
        """
        logger.error("abort: %s", detail)
        if candidate is not None:
            spread_pct = (
                (price_env.data or {}).get("spread_pct") if price_env is not None else None
            )
            self._notify_context(
                outcome="ABORT",
                epic=candidate.get("epic"),
                candidate=candidate,
                debate_outcome=debate_outcome,
                spread_pct=spread_pct,
                gate_results_json=json.dumps({"gates": "1,2,3,4,5 pass"}),
                veto_results_json=json.dumps({"vetos": "pass", "abort_detail": detail}),
            )
        return ExecutionResult(
            status="ABORT", deal_id=deal_id, plan=plan, detail=detail
        )

    # -- the cycle ----------------------------------------------------------

    def run(self) -> ExecutionResult:
        """Execute one cycle. Returns the outcome; never lets an abort escape.

        See the module docstring for the status vocabulary and the abort-is-returned
        contract. The flow short-circuits at the first gate/VETO that says no.
        """
        # 1) Session health + 2) startup reconcile — both can fail closed.
        try:
            account_env = self._ensure_session()
            reconcile_startup(self.broker, self.exec_state, self.config)
        except (ExecutionAbort, ReconcileConflict) as exc:
            return self._abort(str(exc))

        # 3) Gate 1 — trade window. ``now`` is captured once and reused for the
        # VETO window check (the VETOs' freshness comes from re-fetched broker
        # snapshots, not the wall clock).
        now = self.now_fn()
        g1 = gate_time_window(now, self.config)
        if not g1.ok:
            return self._no_trade(g1.gate, g1.reason, failed_gate="G1")

        # 4) Gate 2 — fresh research candidate (runs research lazily if stale).
        g2, candidate = gate_load_candidates(
            self.state, self.research_runner, self.config
        )
        if not g2.ok or candidate is None:
            return self._no_trade(g2.gate, g2.reason, research_empty=True)

        # 4.5) Phase-6 debate seam (Decision A) — between Gate 2 and Gate 3. When no
        # runner is injected this is skipped entirely (Phase 5 stays AI-free). The
        # outcome is read duck-typed (no Phase-6 import): ABSTAIN → NO_TRADE; TRADE →
        # enrich the candidate's direction in-memory (the Judge may reverse the seed,
        # Decision B). Every downstream gate/VETO then reads the resolved direction.
        # ``outcome`` is hoisted to run-scope (default None) so the Phase-7 open seam can
        # read the Judge confidence whether or not a debate ran (verified-contract 1.3).
        outcome: Any = None
        if self.debate_runner is not None:
            try:
                outcome = self.debate_runner(candidate)
            except Exception as exc:  # noqa: BLE001 — defense: the debate is contractually
                # fail-closed (Decision J), but a throwing runner must never crash the
                # cycle either → treat it as a clean NO_TRADE, never "trade anyway".
                return self._no_trade(
                    "debate", f"debate_runner failed: {exc}",
                    epic=candidate["epic"], error=str(exc),
                )
            if getattr(outcome, "decision", "TRADE") == "ABSTAIN":
                return self._no_trade(
                    "debate", getattr(outcome, "rationale", "") or "abstain",
                    epic=candidate["epic"], debate_decision="ABSTAIN",
                )
            direction = getattr(outcome, "direction", None)
            if direction:
                candidate = {**candidate, "direction": direction}

        # 5) Gate 3 + Gate 5 — share one fresh open-positions snapshot.
        positions_env = self.broker.get_open_positions()
        g3 = gate_constraints(account_env, positions_env, candidate, self.config)
        if not g3.ok:
            return self._no_trade(g3.gate, g3.reason, epic=candidate["epic"], failed_gate="G3")
        g5 = gate_direction_consistency(candidate, positions_env)
        if not g5.ok:
            return self._no_trade(g5.gate, g5.reason, epic=candidate["epic"], failed_gate="G5")

        # 6) Gate 4 — sizing. One fresh price (reused by build_order_plan) + market info.
        epic = candidate["epic"]
        price_env = self.broker.get_price(epic)
        market_info_env = self.broker.get_market_info(epic)
        risk_pct = select_risk_pct(self.db, self.config)
        size, size_reason = compute_size(
            account_env, price_env, market_info_env, risk_pct, self.config, epic=epic
        )
        if size_reason is not None:
            return self._no_trade(
                "sizing", size_reason, epic=epic, failed_gate="G4", price_env=price_env
            )

        # 7) The four HARD VETOs on a fresh snapshot, immediately before the order.
        veto = pre_trade_check(self.broker, candidate, now, self.config)
        if not veto.ok:
            return self._no_trade(
                veto.veto, veto.reason, epic=epic, veto=veto.veto, price_env=price_env
            )

        # 8) Build the resolved order plan (reuse the Gate-4 fresh price + market info).
        plan = build_order_plan(candidate, size, price_env, market_info_env, self.config)

        # 9) Human-confirm — the last gate before any broker order (Decision D).
        if self.config.require_confirm and not self.confirm_fn(plan):
            logger.info("human-confirm declined for %s — no order placed", plan.deal_reference)
            return ExecutionResult(
                status="ABORTED_BY_USER",
                deal_id=None,
                plan=plan,
                detail="human-confirm declined",
            )

        # 10) Place (write-ahead, PENDING fail-closed), then monitor if open.
        try:
            place_result = place_order(
                self.broker, self.exec_state, plan, self.config, sleep_fn=self.sleep_fn
            )
            if place_result.status == "OPEN":
                # Phase-7 open seam (Decision A): record the decision context after the
                # position is confirmed OPEN and **before** monitoring. Guarded — a
                # raising sink never disturbs the order/monitor path (Decision J).
                self._notify_opened(candidate, plan, place_result, price_env, outcome, now)
                result = monitor_position(
                    self.broker,
                    self.exec_state,
                    plan,
                    place_result.deal_id,
                    self.config,
                    now_fn=self.now_fn,
                    sleep_fn=self.sleep_fn,
                )
                # Phase-7 close seam: fire on a real close, then return the cycle result.
                self._notify_closed(result)
                return result
            return place_result
        except (ExecutionAbort, ReconcileConflict) as exc:
            return self._abort(
                str(exc), plan=plan, candidate=candidate, debate_outcome=outcome,
                price_env=price_env,
            )

    # -- Phase-7 reward seam (Decision A/J) ---------------------------------

    def _notify_opened(
        self,
        candidate: dict[str, Any],
        plan: OrderPlan,
        place_result: ExecutionResult,
        price_env: Any,
        outcome: Any,
        now: datetime,
    ) -> None:
        """Fire ``reward_sink.on_trade_opened`` + the Block-B ``context_recorder`` with the
        open decision context.

        No-op per-seam when that seam has no sink/recorder injected (Phase 5 bit-identical
        with both ``None``). Fail-closed: a failure building or delivering either snapshot
        is logged ``critical`` and never raised — the order/monitor path is unaffected
        (Decision J).
        """
        if self.reward_sink is not None:
            try:
                opened = build_opened(
                    candidate, plan, place_result, price_env, outcome,
                    score_at_open=self.db.get_current_score(), now=now,
                    point_value=self.config.point_value_for(plan.epic),
                )
                self.reward_sink.on_trade_opened(opened)
            except Exception as exc:  # noqa: BLE001 - the sink must never kill the cycle (J)
                logger.critical("reward_sink.on_trade_opened failed: %s", exc)

        self._notify_context(
            outcome="TRADE",
            epic=candidate.get("epic"),
            candidate=candidate,
            debate_outcome=outcome,
            spread_pct=(price_env.data or {}).get("spread_pct"),
            gate_results_json=json.dumps({"gates": "1,2,3,4,5 pass"}),
            veto_results_json=json.dumps({"vetos": "pass"}),
            deal_id=place_result.deal_id,
        )

    def _notify_closed(self, result: ExecutionResult) -> None:
        """Fire ``reward_sink.on_trade_closed`` after a real close (broker SL/TP or time-stop).

        No-op when no sink is injected, or when the cycle did not end in a real close
        (only ``CLOSED_BY_BROKER`` / ``TIME_STOP`` carry a settled outcome — an OPEN /
        ABORT result is left for the next cycle's reconcile). Fail-closed (Decision J).
        """
        if self.reward_sink is None or result.status not in ("CLOSED_BY_BROKER", "TIME_STOP"):
            return
        try:
            self.reward_sink.on_trade_closed(build_closed(result, now=self.now_fn()))
        except Exception as exc:  # noqa: BLE001 - the sink must never kill the cycle (J)
            logger.critical("reward_sink.on_trade_closed failed: %s", exc)

    # -- Phase-17 (B-5) monitor re-adoption seam (T8) ------------------------

    def resume_open_position(self) -> ExecutionResult | None:
        """Phase 17 B-5 (T8): re-adopt a position still open at the broker after a restart.

        ``reconcile_startup`` leaves a *present* reference alone ("the monitor handles it") —
        but the monitor only ever runs inside :meth:`run` right after :func:`~execution.order.place_order`,
        so after a restart nobody watched it (AEX id 26: 6 days open, ``max_hold`` never applied).
        This picks the first ``OPEN`` record with a ``deal_id`` the broker still holds, monitors it
        from its **recorded** open time (an already-elapsed ``max_hold`` / ``square_off`` closes
        immediately — T8) and fires the Phase-7 close seam. ``None`` when nothing needs adopting.
        The runner calls this only in the WINDOW phase (a close needs an open market).
        """
        for ref in self.exec_state.open_references():
            rec = self.exec_state.get(ref) or {}
            deal_id = rec.get("deal_id")
            if rec.get("status") != "OPEN" or not deal_id:
                continue  # PENDING without a deal_id is reconcile_startup's job
            positions_env = self.broker.get_open_positions()
            if not positions_env.ok:
                logger.warning(
                    "resume: open-positions read failed — not re-adopting %s this cycle", ref
                )
                return None
            if not _position_present(positions_env, deal_id):
                continue  # gone at the broker → reconcile_startup marks it closed (missing)
            plan = OrderPlan(
                epic=rec["epic"], direction=rec["direction"], size=float(rec["size"]),
                stop_level=float(rec["stop_level"]), limit_level=float(rec["limit_level"]),
                deal_reference=ref, currency=self.config.default_currency,
            )
            entry_at = datetime.fromisoformat(
                str(rec["recorded_at"]).replace("Z", "+00:00")
            )
            logger.warning(
                "resume: re-adopting open position %s (deal_id=%s, opened %s)",
                ref, deal_id, rec["recorded_at"]
            )
            try:
                result = monitor_position(
                    self.broker, self.exec_state, plan, deal_id, self.config,
                    now_fn=self.now_fn, sleep_fn=self.sleep_fn, entry_at=entry_at,
                )
            except ExecutionAbort as exc:
                return self._abort(str(exc), plan=plan, deal_id=deal_id)
            self._notify_closed(result)
            return result
        return None

    # -- Phase-10 (V3) abstain-lessons seam (Decision J) ---------------------

    def _notify_no_trade(self, cycle_outcome: dict[str, Any]) -> str | None:
        """Fire ``abstain_sink.on_no_trade`` with the S2 classifier cycle-outcome dict.

        No-op (returns ``None``) when no sink is injected (Phase 5 bit-identical).
        Fail-closed: a failure building or delivering the dict is logged ``critical`` and
        never raised — every NO_TRADE path is unaffected (Decision J), mirroring
        ``_notify_opened``. Returns the persisted abstain ``record_id`` on success (``None``
        on failure/no-sink) — Block-B's ``context_recorder`` links it into
        ``decision_context.abstain_record_id``.
        """
        if self.abstain_sink is None:
            return None
        try:
            return self.abstain_sink.on_no_trade(cycle_outcome)
        except Exception as exc:  # noqa: BLE001 - the sink must never kill the cycle (J)
            logger.critical("abstain_sink.on_no_trade failed: %s", exc)
            return None

    # -- Phase-10 (V3) Block-B market-context seam (Decision J) --------------

    def _notify_context(
        self,
        *,
        outcome: str,
        epic: str | None,
        candidate: dict[str, Any] | None = None,
        debate_outcome: Any = None,
        spread_pct: float | None = None,
        gate_results_json: str | None = None,
        veto_results_json: str | None = None,
        deal_id: str | None = None,
        abstain_record_id: str | None = None,
    ) -> None:
        """Fire ``context_recorder.on_decision`` — ``outcome`` is one of ``"TRADE"``,
        ``"NO_TRADE"``, or ``"ABORT"``.

        No-op when no recorder is injected (Phase 5 bit-identical). Fail-closed: a failure
        is logged ``critical`` and never raised — mirrors ``_notify_opened``/
        ``_notify_no_trade`` (Decision J), even though ``ContextRecorder.on_decision``
        already guards itself (defense in depth, same double-guard style as the other
        seams). ``spread_pct`` (Phase-10 B4-fix, 2026-07-31) is the caller's freshest
        ``price_env``-derived spread, or ``None`` when no price snapshot was in scope yet
        (``ContextRecorder`` already accepted this param — the gap was every call site
        never passing it, see phase10_v3/DATA_WEEK_REVIEW_2026-07-31.md §4 B4).
        """
        if self.context_recorder is None:
            return
        try:
            self.context_recorder.on_decision(
                outcome=outcome,
                epic=epic,
                candidate=candidate,
                debate_outcome=debate_outcome,
                spread_pct=spread_pct,
                gate_results_json=gate_results_json,
                veto_results_json=veto_results_json,
                deal_id=deal_id,
                abstain_record_id=abstain_record_id,
                now_utc=self.now_fn(),
            )
        except Exception as exc:  # noqa: BLE001 - the recorder must never kill the cycle (J)
            logger.critical("context_recorder.on_decision failed: %s", exc)

    # -- internals ----------------------------------------------------------

    def _ensure_session(self) -> Any:
        """Verify the broker session is healthy; return the account envelope.

        Connects if needed (``.ok`` required) and fetches the account (``.ok``
        required). The account envelope is returned so the caller reuses it for
        Gate 3 and sizing — one ``get_account`` per cycle.

        Raises:
            ExecutionAbort: connect failed or the account snapshot is not ``ok``.
        """
        if not self.broker.is_connected():
            connect_env = self.broker.connect()
            if not connect_env.ok:
                error = getattr(connect_env, "error", None) or {}
                raise ExecutionAbort(
                    f"broker connect failed ({error.get('code', '?')}) — cannot proceed"
                )

        account_env = self.broker.get_account()
        if not account_env.ok:
            error = getattr(account_env, "error", None) or {}
            raise ExecutionAbort(
                f"account snapshot unavailable ({error.get('code', '?')}) — "
                "session health unverifiable, failing closed"
            )
        return account_env


# -- Phase-7 snapshot builders (lazy reward import; verified-contracts 1.2/1.3) ----
#
# These translate the executor's in-flight locals into the Phase-7 ``OpenedTrade`` /
# ``ClosedTrade`` data contracts. ``reward.models`` is imported **lazily inside** each
# helper so the module-level imports stay ``execution.* + stdlib`` and a sink-free run
# (``reward_sink=None``) never pulls in ``reward`` — mirroring how ``ig_bot.py`` lazily
# imports ``scripts.wiring``. The contracts are stdlib-only frozen dataclasses (no
# anthropic/broker/db deps), used here purely as the single-source-of-truth payload shape.

# DAX cash CFD = 1 € / point — the default when a caller passes no ``point_value``.
# v1.5 (Issue C): ``ExecutionConfig`` now carries a per-epic ``point_values`` map and
# the executor passes ``config.point_value_for(plan.epic)`` here, so the reconstructed
# ``initial_risk`` matches the point value Gate-4 sizing used. Default 1.0 keeps every
# existing caller (and the DAX path) bit-identical.
_POINT_VALUE = 1.0

# v1.5 (Phase-8 hotfix Step 4 A, 2026-07-01): the prefix a **manual seed** candidate's
# ``reasoning`` starts with (``scripts/seed_candidate.py`` writes "MANUAL SEED (not a real
# research pick): …"). ``build_opened`` uses it to tag the trade's lesson provenance so the
# P4 research prompt can exclude verification-trade lessons downstream. Intra-phase coupling
# (the seed tool lives in this same phase); a real Phase-4 research pick never contains it
# (see the P8 ``test_no_manual_seed_marker`` invariant), and a test here pins the derivation.
_SEED_MARKER_PREFIX = "MANUAL SEED"


def build_opened(
    candidate: dict[str, Any],
    plan: OrderPlan,
    place_result: ExecutionResult,
    price_env: Any,
    outcome: Any,
    *,
    score_at_open: float,
    now: datetime,
    point_value: float = 1.0,
) -> Any:
    """Build the ``OpenedTrade`` decision-context snapshot captured the moment a trade opens.

    ``place_order`` drops the real fill ``level`` (verified-contract 1.2), so the intended
    entry is reconstructed from the fresh ``price_env`` exactly as ``build_order_plan`` did
    (BUY → ask / SELL → bid), and ``initial_risk`` is ``|entry - stop| * size * point_value``.
    ``debate_confidence`` comes from the in-memory ``outcome`` (``None`` when no debate ran,
    verified-contract 1.3). ``account`` is the bootstrap-phase ``"demo"`` constant — the
    durable demo/live source is the wiring layer (Step 13), which knows the broker name.

    ``provenance`` (v1.5 Phase-8 hotfix Step 4 A) is ``"verification"`` when the candidate is a
    manual seed (its ``reasoning`` starts with ``_SEED_MARKER_PREFIX``) else ``"autonomous"`` —
    a deterministic string check, no AI. It rides into ``trade_lessons.market_context_json`` at
    close (via the recorder) so the research prompt can exclude verification-trade lessons. It
    gates nothing (root rule 3).
    """
    from reward.models import OpenedTrade  # lazy: keep execution.* + stdlib at module scope

    data = price_env.data or {}
    if plan.direction == "BUY":
        entry = data.get("ask") if data.get("ask") is not None else data.get("bid")
    else:  # SELL
        entry = data.get("bid") if data.get("bid") is not None else data.get("ask")
    intended_open_level = float(entry)
    initial_risk = abs(intended_open_level - plan.stop_level) * plan.size * point_value

    # v1.5 (Phase-8 hotfix Step 4 A): tag lesson provenance so a later research prompt can
    # drop verification-trade lessons. Deterministic string check — NO AI. A manual seed's
    # ``reasoning`` starts with the seed marker; a real Phase-4 pick never does → "autonomous".
    reasoning = candidate.get("reasoning") or ""
    provenance = "verification" if reasoning.startswith(_SEED_MARKER_PREFIX) else "autonomous"

    return OpenedTrade(
        deal_reference=plan.deal_reference,
        deal_id=place_result.deal_id or "",
        epic=plan.epic,
        direction=plan.direction,
        size=plan.size,
        intended_open_level=intended_open_level,
        stop_level=plan.stop_level,
        limit_level=plan.limit_level,
        currency=plan.currency,
        initial_risk=initial_risk,
        research_confidence=candidate.get("llm_confidence"),
        debate_confidence=getattr(outcome, "confidence", None),
        gate_path={
            "gates": "1,2,3,4,5 pass",
            "debate": getattr(outcome, "decision", None),
        },
        spread_at_entry_pct=data.get("spread_pct"),
        score_at_open=score_at_open,
        session_date=now.strftime("%Y-%m-%d"),
        open_ts=now.isoformat(),
        account="demo",  # bootstrap phase; wiring (Step 13) owns the durable demo/live tag
        provenance=provenance,  # v1.5 (Step 4 A): "verification" for seeds, else "autonomous"
    )


def build_closed(result: ExecutionResult, *, now: datetime) -> Any:
    """Build the minimal ``ClosedTrade`` close fact from the monitor's ``ExecutionResult``.

    Carries the realised ``close_level`` / ``profit_loss`` when the monitor surfaced them
    from the close deal confirmation (TIME_STOP path, 2026-06-23) — the lag-free P&L
    source. They are ``None`` on a ``CLOSED_BY_BROKER`` close, where ``pnl_resolver``
    falls back to ``get_trade_history``.
    """
    from reward.models import ClosedTrade  # lazy: keep execution.* + stdlib at module scope

    return ClosedTrade(
        deal_reference=result.plan.deal_reference if result.plan is not None else "",
        deal_id=result.deal_id or "",
        status=result.status,
        closed_at=now.isoformat(),
        close_level=result.close_level,
        profit_loss=result.profit_loss,
    )
