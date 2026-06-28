"""Module 7 — ``TokenBudget``: today's token sum vs the daily cap.

No network, no LLM: a JSON usage log over ``tmp_path`` (the shape ``research.token_meter``
writes), a fixed ``now_fn`` to pin "today" deterministically, and a ``caplog`` probe of the
single disabled-budget WARNING. The Europe/Berlin day boundary is exercised against a UTC
``ts`` (the meter writes UTC; the daemon's day is ``config.tz``), and the
``Budget``-Protocol handoff to Module 6's ``AutoConfirm`` is proven end-to-end.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from scheduler import TokenBudget as ExportedTokenBudget
from scheduler.budget import TokenBudget
from scheduler.config import SchedulerConfig
from scheduler.safety import REASON_BUDGET, AutoConfirm
from scheduler.state import SchedulerState, StateStore

_BERLIN = ZoneInfo("Europe/Berlin")


def _write_log(tmp_path, records: list[dict]) -> str:
    """Write a usage-log JSON array and return its path."""
    path = tmp_path / "state" / "llm_usage.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    return str(path)


def _rec(ts: str, *, inp: int = 0, out: int = 0, cw: int = 0, cr: int = 0) -> dict:
    """A token-meter-shaped record (UTC ``ts`` with a Z suffix)."""
    return {
        "ts": ts,
        "model": "claude-haiku-4-5-20251001",
        "input_tokens": inp,
        "output_tokens": out,
        "cache_creation_input_tokens": cw,
        "cache_read_input_tokens": cr,
        "est_cost_usd": 0.0,
        "est_cost_eur": 0.0,
    }


def _budget(path: str, *, cap: int | None, now: datetime) -> TokenBudget:
    config = SchedulerConfig(daily_token_budget=cap)
    return TokenBudget(config, path, now_fn=lambda: now)


# A fixed "now" in Berlin (CEST = +2 on 2026-06-28).
_NOW = datetime(2026, 6, 28, 12, 0, tzinfo=_BERLIN)


# --- consumed_today / is_exhausted core ------------------------------------


def test_under_budget_not_exhausted(tmp_path) -> None:
    """Today's tokens below the cap → not exhausted."""
    path = _write_log(tmp_path, [_rec("2026-06-28T09:00:00.000Z", inp=400, out=100)])
    budget = _budget(path, cap=1000, now=_NOW)
    assert budget.consumed_today() == 500
    assert budget.is_exhausted() is False


def test_over_budget_is_exhausted(tmp_path) -> None:
    """Today's tokens above the cap → exhausted."""
    path = _write_log(tmp_path, [_rec("2026-06-28T09:00:00.000Z", inp=900, out=200)])
    budget = _budget(path, cap=1000, now=_NOW)
    assert budget.consumed_today() == 1100
    assert budget.is_exhausted() is True


def test_exactly_at_budget_is_exhausted(tmp_path) -> None:
    """Boundary: consumed == budget exhausts it (the cap is inclusive, ``>=``)."""
    path = _write_log(tmp_path, [_rec("2026-06-28T09:00:00.000Z", inp=600, out=400)])
    budget = _budget(path, cap=1000, now=_NOW)
    assert budget.consumed_today() == 1000
    assert budget.is_exhausted() is True


def test_token_sum_includes_cache_fields(tmp_path) -> None:
    """All four billed token fields are summed (input + output + cache_*)."""
    path = _write_log(
        tmp_path, [_rec("2026-06-28T09:00:00.000Z", inp=100, out=50, cw=30, cr=20)]
    )
    budget = _budget(path, cap=1000, now=_NOW)
    assert budget.consumed_today() == 200


def test_tolerates_six_field_records_without_cache_keys(tmp_path) -> None:
    """An older 6-field record (no ``cache_*`` keys) counts input + output, no crash."""
    rec = {
        "ts": "2026-06-28T10:00:00.000Z",
        "model": "claude-sonnet-4-6",
        "input_tokens": 921,
        "output_tokens": 185,
        "est_cost_usd": 0.0,
        "est_cost_eur": 0.0,
    }
    path = _write_log(tmp_path, [rec])
    budget = _budget(path, cap=5000, now=_NOW)
    assert budget.consumed_today() == 1106


# --- day boundary (Europe/Berlin from a UTC ts) ----------------------------


def test_only_todays_records_counted(tmp_path) -> None:
    """Yesterday's record is excluded; only today's tokens sum."""
    path = _write_log(
        tmp_path,
        [
            _rec("2026-06-27T09:00:00.000Z", inp=5000, out=5000),  # yesterday
            _rec("2026-06-28T09:00:00.000Z", inp=300, out=100),    # today
        ],
    )
    budget = _budget(path, cap=10_000, now=_NOW)
    assert budget.consumed_today() == 400


def test_late_utc_record_counts_toward_next_berlin_day(tmp_path) -> None:
    """A 22:30Z record is 00:30 Berlin next day (CEST +2) → counts for that Berlin day.

    Pins the DST-aware boundary: the record stamped 2026-06-27T22:30Z falls on the Berlin
    date 2026-06-28, so a ``now`` on 2026-06-28 must include it.
    """
    path = _write_log(tmp_path, [_rec("2026-06-27T22:30:00.000Z", inp=700, out=0)])
    budget = _budget(path, cap=10_000, now=_NOW)
    assert budget.consumed_today() == 700
    # ...and a ``now`` on 2026-06-27 must NOT include it
    earlier = datetime(2026, 6, 27, 23, 0, tzinfo=_BERLIN)
    assert _budget(path, cap=10_000, now=earlier).consumed_today() == 0


# --- fail-soft / fail-open -------------------------------------------------


def test_missing_log_file_is_zero_and_not_exhausted(tmp_path) -> None:
    """No usage log → 0 consumed, not exhausted (advisory budget fails OPEN)."""
    budget = _budget(str(tmp_path / "state" / "absent.json"), cap=1000, now=_NOW)
    assert budget.consumed_today() == 0
    assert budget.is_exhausted() is False


def test_corrupt_log_counts_zero_no_raise(tmp_path) -> None:
    """A truncated/corrupt log → 0 (fail-open, never raises)."""
    path = tmp_path / "state" / "llm_usage.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('[{"ts": "2026-06-28T09:00:00Z", "input_tokens":', encoding="utf-8")
    budget = _budget(str(path), cap=1000, now=_NOW)
    assert budget.consumed_today() == 0
    assert budget.is_exhausted() is False


def test_record_with_bad_ts_is_skipped_others_summed(tmp_path) -> None:
    """A record with a missing/garbage ``ts`` is skipped; valid today records still count."""
    path = _write_log(
        tmp_path,
        [
            {"input_tokens": 999, "output_tokens": 999},          # no ts → skipped
            _rec("not-a-timestamp", inp=999),                      # bad ts → skipped
            _rec("2026-06-28T09:00:00.000Z", inp=120, out=80),     # today → counted
        ],
    )
    budget = _budget(path, cap=10_000, now=_NOW)
    assert budget.consumed_today() == 200


# --- disabled budget (None) ------------------------------------------------


def test_none_budget_warns_once_and_never_exhausts(
    tmp_path, caplog: pytest.LogCaptureFixture
) -> None:
    """``daily_token_budget=None`` → one ``scheduler.budget`` WARNING + never exhausted."""
    path = _write_log(tmp_path, [_rec("2026-06-28T09:00:00.000Z", inp=10**9)])
    with caplog.at_level(logging.WARNING, logger="scheduler.budget"):
        budget = _budget(path, cap=None, now=_NOW)
    warnings = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING and r.name == "scheduler.budget"
    ]
    assert len(warnings) == 1
    assert "DISABLED" in warnings[0].message
    assert budget.is_exhausted() is False  # even a billion tokens does not exhaust


# --- Protocol handoff to Module 6 ------------------------------------------


def test_satisfies_autoconfirm_budget_protocol(tmp_path) -> None:
    """A real ``TokenBudget`` works as ``AutoConfirm``'s budget → exhausted blocks BUDGET.

    Proves Module 6's duck-typed ``Budget`` stub matches Module 7's concrete class.
    """
    path = _write_log(tmp_path, [_rec("2026-06-28T09:00:00.000Z", inp=2000, out=0)])
    budget = _budget(path, cap=1000, now=_NOW)  # 2000 >= 1000 → exhausted

    config = SchedulerConfig(
        daily_loss_cap=1800.0,
        state_path=str(tmp_path / "s.json"),
        kill_path=str(tmp_path / "KILL"),
    )
    store = StateStore(config.state_path)
    gate = AutoConfirm(config, store, config.kill_path, budget, lambda _d: 0.0)

    state = SchedulerState(date="2026-06-28", trades_today=0)
    assert gate.can_open(state) == (False, REASON_BUDGET)


# --- exports ---------------------------------------------------------------


def test_exported_from_package_root() -> None:
    """``from scheduler import TokenBudget`` is the submodule class."""
    assert ExportedTokenBudget is TokenBudget
