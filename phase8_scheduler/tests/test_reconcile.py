"""Module 10 (concept §9) — ``Reconciler``: the idempotent reconcile pass.

No network, no broker, no LLM: both collaborators are injected fakes — a ``FakeRewardSink``
(records ``reconcile_open_trades`` calls; configurable return / raise) and a recording/raising
zero-arg ``pending_reconcile_fn``. The behaviours pinned: the two-half composition, fail-closed
containment of each half (a raise in one never skips the other and never propagates), the
``last_reconcile_ts`` stamp on every pass, and that the P&L catch-up runs over *all* OPEN rows
(no deal_ids).
"""

from __future__ import annotations

import logging

import pytest

from scheduler import ReconcileReport as ExportedReconcileReport
from scheduler import Reconciler as ExportedReconciler
from scheduler.reconcile import ReconcileReport, Reconciler
from scheduler.state import SchedulerState


class _FakeRewardSink:
    """Duck-typed ``RewardSink``: records reconcile calls; returns a list or raises."""

    def __init__(self, *, result: list[str] | None = None, raises: Exception | None = None) -> None:
        self._result = result if result is not None else []
        self._raises = raises
        self.calls: list[list[str] | None] = []

    def reconcile_open_trades(self, deal_ids: list[str] | None = None) -> list[str]:
        self.calls.append(deal_ids)
        if self._raises is not None:
            raise self._raises
        return self._result


class _Pending:
    """A recording zero-arg pending-reconcile fn; optionally raises (orphan-PENDING conflict)."""

    def __init__(self, *, raises: Exception | None = None) -> None:
        self._raises = raises
        self.calls = 0

    def __call__(self) -> None:
        self.calls += 1
        if self._raises is not None:
            raise self._raises


def _fixed_now():
    from datetime import datetime, timezone

    return lambda: datetime(2026, 6, 28, 12, 0, tzinfo=timezone.utc)


def _state() -> SchedulerState:
    return SchedulerState(date="2026-06-28")


# --- happy path ------------------------------------------------------------


def test_happy_path_runs_both_halves_and_reports() -> None:
    """Pending fn called once; P&L catch-up returns deals → report + ts stamped."""
    sink = _FakeRewardSink(result=["D1"])
    pending = _Pending()
    rec = Reconciler(sink, pending, now_fn=_fixed_now())
    state = _state()

    report = rec.tick(state)

    assert report == ReconcileReport(pending_ok=True, resolved_deal_ids=["D1"], n_resolved=1)
    assert pending.calls == 1
    assert sink.calls == [None]  # all OPEN rows, no deal_ids
    assert state.last_reconcile_ts == "2026-06-28T12:00:00+00:00"


def test_nothing_open_is_a_clean_noop() -> None:
    """No OPEN rows → n_resolved=0, pending_ok=True, no error."""
    sink = _FakeRewardSink(result=[])
    rec = Reconciler(sink, _Pending(), now_fn=_fixed_now())
    state = _state()

    report = rec.tick(state)

    assert report == ReconcileReport(pending_ok=True, resolved_deal_ids=[], n_resolved=0)
    assert state.last_reconcile_ts is not None


# --- fail-closed containment ----------------------------------------------


def test_pending_raise_is_contained_and_pnl_still_runs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A raising orphan-PENDING pass → critical + pending_ok=False, but step 2 STILL runs."""
    sink = _FakeRewardSink(result=["D2"])
    pending = _Pending(raises=RuntimeError("unexpected broker position"))
    rec = Reconciler(sink, pending, now_fn=_fixed_now())
    state = _state()

    with caplog.at_level(logging.CRITICAL, logger="scheduler.reconcile"):
        report = rec.tick(state)  # must NOT raise

    assert report.pending_ok is False
    assert report.resolved_deal_ids == ["D2"]  # the P&L catch-up still ran
    assert sink.calls == [None]
    assert state.last_reconcile_ts is not None
    crit = [r for r in caplog.records if r.levelno == logging.CRITICAL]
    assert len(crit) == 1


def test_pnl_catchup_raise_is_contained(caplog: pytest.LogCaptureFixture) -> None:
    """A raising reconcile_open_trades → critical + resolved=[], no propagation."""
    sink = _FakeRewardSink(raises=RuntimeError("db unreachable"))
    rec = Reconciler(sink, _Pending(), now_fn=_fixed_now())
    state = _state()

    with caplog.at_level(logging.CRITICAL, logger="scheduler.reconcile"):
        report = rec.tick(state)  # must NOT raise

    assert report.pending_ok is True  # the pending half succeeded
    assert report.resolved_deal_ids == []
    assert report.n_resolved == 0
    assert state.last_reconcile_ts is not None
    crit = [r for r in caplog.records if r.levelno == logging.CRITICAL]
    assert len(crit) == 1


def test_both_halves_raise_both_contained(caplog: pytest.LogCaptureFixture) -> None:
    """Both halves raising → two criticals, no propagation, ts still stamped."""
    sink = _FakeRewardSink(raises=RuntimeError("db"))
    pending = _Pending(raises=RuntimeError("conflict"))
    rec = Reconciler(sink, pending, now_fn=_fixed_now())
    state = _state()

    with caplog.at_level(logging.CRITICAL, logger="scheduler.reconcile"):
        report = rec.tick(state)

    assert report == ReconcileReport(pending_ok=False, resolved_deal_ids=[], n_resolved=0)
    assert state.last_reconcile_ts is not None
    crit = [r for r in caplog.records if r.levelno == logging.CRITICAL]
    assert len(crit) == 2


# --- timestamp + plumbing --------------------------------------------------


def test_default_now_fn_is_tz_aware() -> None:
    """Without an injected now_fn the ts is still produced (tz-aware UTC default)."""
    from datetime import datetime

    rec = Reconciler(_FakeRewardSink(result=[]), _Pending())
    state = _state()
    rec.tick(state)
    assert state.last_reconcile_ts is not None
    assert datetime.fromisoformat(state.last_reconcile_ts).tzinfo is not None


def test_exported_from_package_root() -> None:
    """``from scheduler import Reconciler, ReconcileReport`` are the submodule objects."""
    assert ExportedReconciler is Reconciler
    assert ExportedReconcileReport is ReconcileReport
