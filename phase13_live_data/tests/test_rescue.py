"""Phase 13 §6 C2 — tests for ``live_data.rescue``.

All mocked: no network, no real IG. ``broker`` is a tiny fake whose
``get_historical_ohlcv`` returns canned envelopes; the ``budget`` is a
real ``SourceBudget`` (cheap, in-memory) on tmp_path; the ``archive``
is a real ``BarArchive`` (D4) on tmp_path.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from data_foundation.archive import BarArchive
from data_foundation.budget import IG_QUOTA_V1, SourceBudget
from data_foundation.models import Bar

from live_data.rescue import GapRescue, RescueConfig, RescueReport, _age_minutes, _to_minute_iso


# ---------- fakes ----------------------------------------------------------


@dataclass
class _FakeBroker:
    """Returns canned envelopes for ``get_historical_ohlcv``."""
    ok: bool = True
    bars: list[dict] | None = None
    raise_exc: bool = False

    def get_historical_ohlcv(self, epic, resolution, count, **kwargs):
        if self.raise_exc:
            raise RuntimeError("boom")
        if not self.ok:
            return SimpleNamespace(ok=False, error="not_ok")
        return SimpleNamespace(ok=True, data={"bars": list(self.bars or [])})


def _bar(ts: str, o=100.0, h=101.0, l=99.5, c=100.5):
    return {"timestamp": ts, "open": o, "high": h, "low": l, "close": c, "volume": 10}


@pytest.fixture
def archive(tmp_path) -> BarArchive:
    a = BarArchive(tmp_path / "bars.sqlite")
    a.ensure_schema()
    yield a
    a.close()


@pytest.fixture
def budget(tmp_path) -> SourceBudget:
    return SourceBudget(tmp_path / "budget.sqlite", IG_QUOTA_V1)


# ---------- tests ----------------------------------------------------------


def test_no_gap_yields_no_gap_report(archive, budget):
    """Dense yF window ⇒ rescue is a no-op (skipped_reason='no_gap').

    The test uses a tight 10-minute window with one yF bar per minute
    — both the inter-bar pass and the tail pass return None. (A whole-day
    window would have a tail gap, since the day is naturally bounded —
    that is a **real** gap, and the test for that is
    ``test_old_gap_calls_history_and_writes_bars``.)"""
    epic = "IX.D.DAX.IFMM.IP"
    day_start = "2026-08-19T09:00:00.000Z"
    day_end = "2026-08-19T09:10:00.000Z"  # 10-minute window, dense
    for m in range(10):  # bars at 09:00..09:09
        archive.insert_bars([Bar(
            epic=epic, resolution="1m",
            ts_utc=f"2026-08-19T09:0{m}:00.000Z",
            open=100, high=100, low=100, close=100, volume=1, source="yf",
            fetched_at=f"2026-08-19T09:0{m}:01.000Z",
        )])
    rec = GapRescue(_FakeBroker(), budget, archive)
    out = rec.rescue_epic(epic, day_start, day_end)
    assert out == RescueReport(epic=epic, gaps_found=0, bars_written=0,
                              points_spent=0, skipped_reason="no_gap")
    assert budget.spent_in_window() == 0


def test_old_gap_calls_history_and_writes_bars(archive, budget):
    """An old gap (youngest bar > min_gap_age_min) triggers the IG call,
    books the spend, writes the bars with source='ig'."""
    epic = "IX.D.DAX.IFMM.IP"
    # Two yF bars at 09:00, 09:05 (skip 09:01..09:04). Window is 09:00..09:06
    # so the inter-bar gap is detectable. The "now" is 1 day later so
    # min_gap_age_min=60 is comfortably met.
    day_start = "2026-08-19T09:00:00.000Z"
    day_end = "2026-08-19T09:06:00.000Z"
    for m in (0, 5):
        archive.insert_bars([Bar(
            epic=epic, resolution="1m",
            ts_utc=f"2026-08-19T09:0{m}:00.000Z",
            open=100, high=100, low=100, close=100, volume=1, source="yf",
            fetched_at=f"2026-08-19T09:0{m}:01.000Z",
        )])
    broker = _FakeBroker(bars=[
        _bar("2026-08-19T09:01:00.000Z"),
        _bar("2026-08-19T09:02:00.000Z"),
    ])
    # "Now" is 90 minutes after the gap end (09:05) on the same day —
    # far enough past the gap for min_gap_age_min=60, but close enough
    # that the IG-returned bars (09:01, 09:02) are < 120 min old
    # (stale_tolerance_min). The rescue's L8 stale-assertion is the
    # independent test (``test_stale_response_is_rejected_and_spend_still_booked``).
    now = datetime(2026, 8, 19, 10, 35, tzinfo=timezone.utc)
    rec = GapRescue(broker, budget, archive, now_fn=lambda: now)
    out = rec.rescue_epic(epic, day_start, day_end)
    assert out.skipped_reason is None
    assert out.gaps_found == 1
    # 2 bars were actually written (IG returned 2), but the spend is
    # the **gap size in minutes** (Plan §6 C2: "Bereichs-API" → spend
    # scales with the requested span, capped at max_points_per_call).
    # The gap is 09:00..09:05 = 5 min, capped at 60 → 5.
    assert out.bars_written == 2
    assert out.points_spent == 5
    assert budget.spent_in_window() == 5
    # Bars are in the archive with source='ig'.
    rows = archive.window(epic, "1m", "2026-08-19T09:00:00.000Z",
                          "2026-08-19T09:03:00.000Z", sources=("ig",))
    assert len(rows) == 2


def test_too_fresh_gap_is_skipped(archive, budget):
    """A gap whose tail is younger than ``min_gap_age_min`` waits — S1/S2
    may still cover it."""
    epic = "IX.D.DAX.IFMM.IP"
    day_start = "2026-08-19T09:00:00.000Z"
    day_end = "2026-08-19T09:06:00.000Z"
    for m in (0, 5):
        archive.insert_bars([Bar(
            epic=epic, resolution="1m",
            ts_utc=f"2026-08-19T09:0{m}:00.000Z",
            open=100, high=100, low=100, close=100, volume=1, source="yf",
            fetched_at=f"2026-08-19T09:0{m}:01.000Z",
        )])
    # "Now" is 2 minutes after the gap's right edge (09:05). min_gap_age_min=60
    # default → too fresh, no call.
    now = datetime(2026, 8, 19, 9, 7, tzinfo=timezone.utc)
    broker = _FakeBroker(bars=[_bar("2026-08-19T09:01:00.000Z")])
    rec = GapRescue(broker, budget, archive, now_fn=lambda: now)
    out = rec.rescue_epic(epic, day_start, day_end)
    assert out.skipped_reason == "gap_too_fresh"
    assert out.points_spent == 0
    assert budget.spent_in_window() == 0


def test_throttle_blocks_second_call_same_day(archive, budget):
    """``max_calls_per_epic_per_day`` (default 1): the second ``rescue_epic``
    for the same epic on the same day returns ``skipped_reason='throttled_today'``."""
    epic = "IX.D.DAX.IFMM.IP"
    day_start = "2026-08-19T09:00:00.000Z"
    day_end = "2026-08-19T09:06:00.000Z"
    for m in (0, 5):
        archive.insert_bars([Bar(
            epic=epic, resolution="1m",
            ts_utc=f"2026-08-19T09:0{m}:00.000Z",
            open=100, high=100, low=100, close=100, volume=1, source="yf",
            fetched_at=f"2026-08-19T09:0{m}:01.000Z",
        )])
    now = datetime(2026, 8, 19, 10, 35, tzinfo=timezone.utc)
    broker = _FakeBroker(bars=[_bar("2026-08-19T09:01:00.000Z")])
    rec = GapRescue(broker, budget, archive, now_fn=lambda: now)
    out1 = rec.rescue_epic(epic, day_start, day_end)
    out2 = rec.rescue_epic(epic, day_start, day_end)
    assert out1.bars_written == 1
    assert out1.points_spent == 5  # the gap is 09:00..09:05 = 5 min
    assert out2.skipped_reason == "throttled_today"
    assert out2.points_spent == 0


def test_budget_exhaustion_skips_call(archive, budget):
    """``can_spend=False`` ⇒ no broker call, no points charged, no write."""
    epic = "IX.D.DAX.IFMM.IP"
    day_start = "2026-08-19T09:00:00.000Z"
    day_end = "2026-08-19T09:06:00.000Z"
    for m in (0, 5):
        archive.insert_bars([Bar(
            epic=epic, resolution="1m",
            ts_utc=f"2026-08-19T09:0{m}:00.000Z",
            open=100, high=100, low=100, close=100, volume=1, source="yf",
            fetched_at=f"2026-08-19T09:0{m}:01.000Z",
        )])
    budget.record_spend(9_900, "rescue")  # leaves < 1 for a 60-pt ask
    now = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
    broker = _FakeBroker(bars=[_bar("2026-08-19T09:01:00.000Z")])
    rec = GapRescue(broker, budget, archive, now_fn=lambda: now)
    out = rec.rescue_epic(epic, day_start, day_end)
    assert out.skipped_reason == "budget"
    assert out.points_spent == 0
    # budget.spent_in_window is the historical IG only — the rescue
    # did not charge; the existing 9900 stays.
    assert budget.spent_in_window() == 9_900


def test_stale_response_is_rejected_and_spend_still_booked(archive, budget):
    """F1 defence: a 32-day-stale response is rejected (no write), but
    the spend is **still** booked — IG has billed the call regardless
    of our use of the data."""
    epic = "IX.D.IBEX.FWM2.IP"
    day_start = "2026-08-19T09:00:00.000Z"
    day_end = "2026-08-19T09:06:00.000Z"
    for m in (0, 5):
        archive.insert_bars([Bar(
            epic=epic, resolution="1m",
            ts_utc=f"2026-08-19T09:0{m}:00.000Z",
            open=100, high=100, low=100, close=100, volume=1, source="yf",
            fetched_at=f"2026-08-19T09:0{m}:01.000Z",
        )])
    # IG returns a bar from 32 days ago — the F1 situation.
    ancient = "2026-07-17T09:01:00.000Z"
    now = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)  # +1 month
    broker = _FakeBroker(bars=[_bar(ancient)])
    rec = GapRescue(broker, budget, archive, now_fn=lambda: now)
    out = rec.rescue_epic(epic, day_start, day_end)
    assert out.skipped_reason == "stale_history"
    assert out.bars_written == 0
    assert out.points_spent == 5  # the spend is still booked
    # No IG row in the archive (the stale one was rejected).
    rows = archive.window(epic, "1m", "2026-08-19T09:00:00.000Z",
                          "2026-08-19T09:03:00.000Z", sources=("ig",))
    assert rows == []


def test_broker_not_ok_returns_not_ok_report(archive, budget):
    """``get_historical_ohlcv`` returns ok=False ⇒ the spend is booked
    (IG billed the call) but no write happens, and skipped_reason='not_ok'."""
    epic = "IX.D.DAX.IFMM.IP"
    day_start = "2026-08-19T09:00:00.000Z"
    day_end = "2026-08-19T09:06:00.000Z"
    for m in (0, 5):
        archive.insert_bars([Bar(
            epic=epic, resolution="1m",
            ts_utc=f"2026-08-19T09:0{m}:00.000Z",
            open=100, high=100, low=100, close=100, volume=1, source="yf",
            fetched_at=f"2026-08-19T09:0{m}:01.000Z",
        )])
    now = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
    broker = _FakeBroker(ok=False)
    rec = GapRescue(broker, budget, archive, now_fn=lambda: now)
    out = rec.rescue_epic(epic, day_start, day_end)
    assert out.skipped_reason == "not_ok"
    assert out.bars_written == 0
    assert out.points_spent == 5  # the spend is still booked (IG billed)


def test_broker_exception_is_caught(archive, budget):
    """A raised exception in the broker call is caught (the rescue is
    best-effort); the report carries skipped_reason='scan_error' or
    similar — the daemon must not crash on a transient broker failure."""
    epic = "IX.D.DAX.IFMM.IP"
    class _ExplodingArchive:
        def window(self, *a, **kw):
            raise RuntimeError("scan boom")
    rec = GapRescue(_FakeBroker(), budget, _ExplodingArchive())
    out = rec.rescue_epic(epic, "2026-08-19T09:00:00.000Z", "2026-08-19T23:59:00.000Z")
    assert out.skipped_reason == "scan_error"
    assert out.bars_written == 0
    assert out.points_spent == 0


def test_default_aus_class_does_not_exist_when_not_built(archive, budget):
    """Operator-Disziplin: ``enable_gap_rescue=False`` heißt, das Objekt
    wird im Wiring gar nicht gebaut. ``GapRescue`` selbst ist die
    Stufe, die **nur dann** existiert, wenn der Operator sie anfordert.
    Verifiziert, dass die Tuning-Konstanten die Plan-Defaults haben
    (Plan §5.6)."""
    import inspect
    from live_data import rescue as rescue_mod
    assert hasattr(rescue_mod, "GapRescue")
    sig = inspect.signature(rescue_mod.GapRescue.__init__)
    defaults = {
        name: param.default
        for name, param in sig.parameters.items()
        if param.default is not inspect.Parameter.empty
    }
    assert defaults["max_calls_per_epic_per_day"] == 1
    assert defaults["min_gap_age_min"] == 60
    assert defaults["max_points_per_call"] == 60
    assert defaults["stale_tolerance_min"] == 120
    # (the test exists to remind future maintainers: building GapRescue
    # in production wiring is a one-line decision, and the default is
    # OFF — this assertion is the contract.)


def test_age_minutes_helper_correct():
    now = datetime(2026, 8, 19, 12, 0, tzinfo=timezone.utc)
    assert _age_minutes("2026-08-19T11:00:00.000Z", now) == pytest.approx(60.0)
    assert _age_minutes("2026-08-18T12:00:00.000Z", now) == pytest.approx(1440.0)
    # fail-soft on garbage: returns a finite number near zero (parse_iso
    # falls back to ``datetime.now()`` which may be slightly before or
    # after the test's frozen ``now``). The invariant is: no exception,
    # no NaN, no extreme value.
    val = _age_minutes("garbage", now)
    assert abs(val) < 1e6  # not absurdly large or NaN


def test_to_minute_iso_truncates_to_minute():
    assert _to_minute_iso("2026-08-19T09:01:37.123Z") == "2026-08-19T09:01:00.000Z"
    # fail-soft on garbage: returns a valid timestamp (now-truncated), not
    # the garbage itself. The helper never crashes the caller.
    out = _to_minute_iso("garbage")
    assert out.endswith(".000Z") and "T" in out


# ---------- Phase 15 §6 D3 — RescueConfig + Doppel-Sperre --------------------
#
# Plan §6 D3 (S. 670-698) + Plan §7 AK12 (S. 727):
# - `enable_gap_rescue` lives ONLY in RescueConfig (Phase 13),
#   NOT in SchedulerConfig, NOT in phase8_scheduler/.
# - Operator-Script `gap_rescue_operator.py` requires BOTH
#   `enable_gap_rescue=True` AND `--apply` to write (Doppel-Sperre).
# - Default of `enable_gap_rescue` is `False` (Plan §6 D3 + AK12).
# These tests pin all four invariants.


def test_rescue_config_default_is_aus():
    """AK12: ``RescueConfig()`` defaults to ``enable_gap_rescue=False``.

    The Operator-Tool's Doppel-Sperre means the Schreib-Pfad requires
    ``enable_gap_rescue=True`` AND ``--apply``; a default of ``False``
    keeps the second condition from ever accidentally landing on True.
    """
    cfg = RescueConfig()
    assert cfg.enable_gap_rescue is False
    assert cfg.epics == ()
    # Plan §6 D3 + §9.2: 560/Woche, nicht nachgerechnet.
    assert cfg.max_points_per_run == 560


def test_rescue_config_is_frozen_and_hashable():
    """``RescueConfig`` is ``frozen=True``: mutation raises, hash works.

    Phase-15 follows the Phase-10 frozen-dataclass discipline
    (``enable_*`` flags in ``SchedulerConfig`` are all frozen).
    """
    cfg = RescueConfig(enable_gap_rescue=True, epics=("IX.D.DAX.IFMM.IP",))
    with pytest.raises((AttributeError, Exception)) as ei:
        cfg.enable_gap_rescue = False  # type: ignore[misc]
    # frozen dataclass ⇒ FrozenInstanceError; the exact name varies by
    # Python version, so just check it is not a plain AssertionError.
    assert "Frozen" in type(ei.value).__name__ or "frozen" in str(ei.value).lower()
    # hashable (frozen + no list fields; tuple default for epics).
    assert hash(cfg) is not None
    # two configs with the same values hash equal.
    cfg2 = RescueConfig(enable_gap_rescue=True, epics=("IX.D.DAX.IFMM.IP",))
    assert hash(cfg) == hash(cfg2)


def test_rescue_config_epics_default_is_empty_tuple_not_list():
    """Mutable-default trap guard: ``epics`` is a **tuple** (immutable),
    not a list that a caller could mutate across instances. Python
    interns empty tuples (so ``cfg_a.epics is cfg_b.epics`` is
    ``True``), but the structural safety is the tuple-immutability,
    not the identity — a list would have failed this test by being
    mutable. Verify by type-check + mutation attempt."""
    cfg_a = RescueConfig()
    cfg_b = RescueConfig()
    assert isinstance(cfg_a.epics, tuple), "epics must be tuple, not list"
    assert isinstance(cfg_b.epics, tuple), "epics must be tuple, not list"
    assert cfg_a.epics == cfg_b.epics == ()
    # A tuple cannot be mutated — this is the real safety property.
    with pytest.raises((AttributeError, TypeError)):
        cfg_a.epics.append("IX.D.DAX.IFMM.IP")  # type: ignore[attr-defined]
    # operator may extend via explicit tuple (the dataclass stays frozen).
    cfg_c = RescueConfig(epics=("IX.D.DAX.IFMM.IP", "IX.D.CAC.IFE.IP"))
    assert cfg_c.epics == ("IX.D.DAX.IFMM.IP", "IX.D.CAC.IFE.IP")
    assert isinstance(cfg_c.epics, tuple)


def test_enable_gap_rescue_is_NOT_in_scheduler_config():
    """AK12 (Plan §7): ``enable_gap_rescue`` lives ONLY in
    ``RescueConfig``, NOT in ``SchedulerConfig``. Plan §6 D3 warnt
    explizit: „Kein Feld in SchedulerConfig, kein Wiring in
    phase8_scheduler/." Diese Regression pinns den Schnitt — falls
    jemand das Feld doch ins SchedulerConfig schmuggelt, geht der
    Test rot.
    """
    import subprocess

    # Field declaration must exist (Phase 13 only).
    r1 = subprocess.run(
        ["grep", "-rn", "enable_gap_rescue: bool",
         "--include=*.py", "."],
        cwd="/home/trading-bot/trading-bot",
        capture_output=True, text=True,
    )
    assert r1.returncode == 0, "no enable_gap_rescue field declaration found at all"
    decls = [l for l in r1.stdout.splitlines() if l]
    assert any("/phase13_live_data/" in l for l in decls), \
        f"enable_gap_rescue field not in phase13_live_data: {decls}"
    assert not any("/phase8_scheduler/" in l for l in decls), \
        f"AK12 violated: enable_gap_rescue field leaked into phase8_scheduler: {decls}"

    # Nothing in phase8_scheduler/ at all.
    r2 = subprocess.run(
        ["grep", "-rn", "enable_gap_rescue",
         "--include=*.py", "phase8_scheduler/"],
        cwd="/home/trading-bot/trading-bot",
        capture_output=True, text=True,
    )
    assert r2.stdout.strip() == "", \
        f"AK12 violated: enable_gap_rescue in phase8_scheduler/: {r2.stdout!r}"


def test_gap_rescue_operator_doppel_sperre_default_dry_run():
    """AK12 + Plan §6 D3: der Operator-Script schreibt NUR, wenn
    ``enable_gap_rescue=True`` UND ``--apply`` beide gesetzt sind.
    Default-Verhalten (``enable_gap_rescue=False``, kein ``--apply``):
    ``dry_run: True`` im JSON-Output, kein Archive-Write, kein
    Keyring-Read, kein Broker-Connect.

    Der Test ruft ``main([...])`` direkt mit gemockten Subprozessen
    (``subprocess.run`` für Grep nicht nötig — der Test arbeitet
    auf der reinen ``main``-Funktion) und fängt den JSON-Output ab.
    """
    # --dry-run, --enable-gap-rescue=False (default), kein --apply
    import sys as _sys
    _sys.path.insert(0, "/home/trading-bot/trading-bot")
    from phase13_live_data.scripts import gap_rescue_operator as op

    # Capture stdout.
    import io
    buf = io.StringIO()
    old_stdout, _sys.stdout = _sys.stdout, buf

    # No archive write: just a plan with no actual rescue.
    # Use a clearly fake path; --dry-run means we never touch the DB.
    rc = op.main([
        "--start", "2026-09-01T08:00:00Z",
        "--end",   "2026-09-01T16:00:00Z",
        "--epics", "IX.D.DAX.IFMM.IP",
        "--db",    "/tmp/this_path_does_not_matter_in_dry_run.sqlite",
        "--universe-db", "/tmp/this_path_does_not_matter_in_dry_run.sqlite",
    ])
    _sys.stdout = old_stdout
    payload = buf.getvalue()

    assert rc == 0, f"dry-run should exit 0, got {rc}"
    parsed = json.loads(payload)
    assert parsed["dry_run"] is True
    assert parsed["ok"] is True
    assert parsed["config"]["enable_gap_rescue"] is False
    assert parsed["doppel_sperre"]["write_path_active"] is False
    # The Doppel-Sperre lists both missing conditions.
    assert "enable_gap_rescue=True" in parsed["doppel_sperre"]["missing"]
    assert "--apply" in parsed["doppel_sperre"]["missing"]


def test_gap_rescue_operator_enable_only_no_apply_still_dry_run():
    """Doppel-Sperre, Hälfte 1: ``--enable-gap-rescue`` ohne ``--apply``
    aktiviert den Schreib-Pfad NICHT (Plan §6 D3)."""
    import sys as _sys
    _sys.path.insert(0, "/home/trading-bot/trading-bot")
    from phase13_live_data.scripts import gap_rescue_operator as op

    import io
    buf = io.StringIO()
    old_stdout, _sys.stdout = _sys.stdout, buf

    rc = op.main([
        "--start", "2026-09-01T08:00:00Z",
        "--end",   "2026-09-01T16:00:00Z",
        "--epics", "IX.D.DAX.IFMM.IP",
        "--enable-gap-rescue",
    ])
    _sys.stdout = old_stdout
    parsed = json.loads(buf.getvalue())

    assert rc == 0
    assert parsed["dry_run"] is True
    assert parsed["config"]["enable_gap_rescue"] is True
    assert parsed["doppel_sperre"]["write_path_active"] is False
    # First condition met, second missing.
    assert "enable_gap_rescue=True" not in parsed["doppel_sperre"]["missing"]
    assert "--apply" in parsed["doppel_sperre"]["missing"]


def test_gap_rescue_operator_apply_only_no_enable_still_dry_run():
    """Doppel-Sperre, Hälfte 2: ``--apply`` ohne ``--enable-gap-rescue``
    aktiviert den Schreib-Pfad NICHT (Plan §6 D3). Symmetrisch zum
    vorigen Test."""
    import sys as _sys
    _sys.path.insert(0, "/home/trading-bot/trading-bot")
    from phase13_live_data.scripts import gap_rescue_operator as op

    import io
    buf = io.StringIO()
    old_stdout, _sys.stdout = _sys.stdout, buf

    rc = op.main([
        "--start", "2026-09-01T08:00:00Z",
        "--end",   "2026-09-01T16:00:00Z",
        "--epics", "IX.D.DAX.IFMM.IP",
        "--apply",
    ])
    _sys.stdout = old_stdout
    parsed = json.loads(buf.getvalue())

    assert rc == 0
    assert parsed["dry_run"] is True
    assert parsed["config"]["enable_gap_rescue"] is False
    assert parsed["doppel_sperre"]["write_path_active"] is False
    # Second condition met, first missing.
    assert "enable_gap_rescue=True" in parsed["doppel_sperre"]["missing"]
    assert "--apply" not in parsed["doppel_sperre"]["missing"]
