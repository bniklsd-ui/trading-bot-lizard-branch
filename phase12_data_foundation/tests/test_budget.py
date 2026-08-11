"""Tests for ``data_foundation.budget.SourceBudget`` (Plan §6 Step 2)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from data_foundation.budget import IG_QUOTA_V1, QuotaModel, SourceBudget


class FakeClock:
    def __init__(self, start: datetime):
        self.now = start

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **kwargs) -> None:
        self.now += timedelta(**kwargs)


@pytest.fixture
def clock():
    return FakeClock(datetime(2026, 8, 11, 8, 0, 0, tzinfo=timezone.utc))


def test_empty_ledger(tmp_path, clock):
    b = SourceBudget(tmp_path / "bars.sqlite", IG_QUOTA_V1, now_fn=clock)
    assert b.spent_in_window() == 0
    assert b.remaining_estimate() == 10_000
    assert b.can_spend(300) is True


def test_spend_accumulates_in_window(tmp_path, clock):
    b = SourceBudget(tmp_path / "bars.sqlite", IG_QUOTA_V1, now_fn=clock)
    b.record_spend(300, "tracker")
    b.record_spend(300, "probe")
    assert b.spent_in_window() == 600
    assert b.remaining_estimate() == 10_000 - 600


def test_can_spend_respects_reserve(tmp_path, clock):
    b = SourceBudget(
        tmp_path / "bars.sqlite", IG_QUOTA_V1, reserve_points=1_500, now_fn=clock
    )
    b.record_spend(8_000, "research")
    # remaining = 2000; 2000 - 300 = 1700 > 1500 -> True
    assert b.can_spend(300) is True
    b.record_spend(300, "research")
    # remaining = 1700; 1700 - 300 = 1400 > 1500 -> False
    assert b.can_spend(300) is False


def test_08_03_incident_regression(tmp_path, clock):
    """The 2026-08-03 incident: 33 fetches x 300 points exhausted the real
    allowance. Modelled here as pure spend-tracking (no observation) against
    IG_QUOTA_V1 -- can_spend(300) must go False *before* the 33rd, exhausting
    call, proving the budget would have caught it in advance (Plan §6 Step 2
    acceptance criterion)."""
    b = SourceBudget(tmp_path / "bars.sqlite", IG_QUOTA_V1, now_fn=clock)
    tripped_at = None
    for i in range(1, 34):
        if not b.can_spend(300):
            tripped_at = i
            break
        b.record_spend(300, "tracker")
    assert tripped_at is not None
    assert tripped_at < 33
    assert b.can_spend(300) is False


def test_record_allowance_with_none_fields(tmp_path, clock):
    """An exhausted response carrying no allowance object at all -- all-None
    fields must not raise and must not be used as a remaining_estimate basis."""
    b = SourceBudget(tmp_path / "bars.sqlite", IG_QUOTA_V1, now_fn=clock)
    b.record_spend(500, "tracker")
    b.record_allowance(total=None, remaining=None, expiry=None)
    # falls back to the model-based estimate, unaffected by the None observation
    assert b.remaining_estimate() == 10_000 - 500


def test_observation_wins_when_smaller_than_calculation(tmp_path, clock):
    b = SourceBudget(tmp_path / "bars.sqlite", IG_QUOTA_V1, now_fn=clock)
    b.record_spend(300, "tracker")  # model-based remaining = 9700
    b.record_allowance(total=10_000, remaining=200, expiry=None)  # far smaller
    assert b.remaining_estimate() == 200


def test_spends_after_observation_are_deducted(tmp_path, clock):
    b = SourceBudget(tmp_path / "bars.sqlite", IG_QUOTA_V1, now_fn=clock)
    b.record_allowance(total=10_000, remaining=5_000, expiry=None)
    clock.advance(seconds=1)
    b.record_spend(300, "tracker")
    assert b.remaining_estimate() == 5_000 - 300


def test_window_rollover_via_expiry_observation(tmp_path, clock):
    b = SourceBudget(tmp_path / "bars.sqlite", IG_QUOTA_V1, now_fn=clock)
    b.record_spend(9_000, "tracker")
    assert b.spent_in_window() == 9_000  # no observation yet -> counts everything

    # Observe an allowance whose window resets 3 days from now -> window_start
    # is (expiry - 7 days) = 4 days in the past, i.e. before the spend above.
    expiry = (clock() + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    b.record_allowance(total=10_000, remaining=1_000, expiry=expiry)

    # Two days later, IG's window actually rolls over: a fresh observation whose
    # boundary is now clearly *after* the old spend's ts_utc (days apart, not a
    # one-second artifact) must roll the old spend out of scope entirely.
    clock.advance(days=2)
    new_expiry = (clock() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    b.record_allowance(total=10_000, remaining=10_000, expiry=new_expiry)
    assert b.spent_in_window() == 0  # the 9000-point spend is now before window_start


def test_unparseable_expiry_falls_back_soft(tmp_path, clock):
    """§9.5: IG's real allowanceExpiry field shape is unconfirmed -- if it turns
    out to be a raw seconds-remaining counter (not an absolute ISO instant) and
    reaches record_allowance unconverted, window_start()/can_spend() must not
    crash the one guard that runs before every IG fetch. Fail-soft: treated as
    no usable observation."""
    b = SourceBudget(tmp_path / "bars.sqlite", IG_QUOTA_V1, now_fn=clock)
    b.record_allowance(total=10_000, remaining=5_000, expiry="604800")  # seconds, not ISO
    assert b.window_start() is None
    assert b.can_spend(300) is True  # must not raise


def test_predicted_exhaustion_days(tmp_path, clock):
    b = SourceBudget(tmp_path / "bars.sqlite", IG_QUOTA_V1, now_fn=clock)
    b.record_spend(5_000, "tracker")  # remaining = 5000
    assert b.predicted_exhaustion_days(daily_rate=1_000) == pytest.approx(5.0)
    assert b.predicted_exhaustion_days(daily_rate=0) is None


def test_persistence_across_two_instances(tmp_path, clock):
    db_path = tmp_path / "bars.sqlite"
    b1 = SourceBudget(db_path, IG_QUOTA_V1, now_fn=clock)
    b1.record_spend(1_234, "tracker")
    b1.close()

    b2 = SourceBudget(db_path, IG_QUOTA_V1, now_fn=clock)
    assert b2.spent_in_window() == 1_234


def test_unconstrained_budget_is_permissive(tmp_path, clock):
    unlimited = QuotaModel(source="yf", points_per_window=None, window_days=None)
    b = SourceBudget(tmp_path / "bars.sqlite", unlimited, now_fn=clock)
    assert b.remaining_estimate() is None
    assert b.can_spend(1_000_000) is True
